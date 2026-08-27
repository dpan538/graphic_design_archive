#!/usr/bin/env python3
"""Capture standardized Crossref metadata searches for every Round 16A pair.

Capture mode writes one resumable, process-locked shard JSONL chosen explicitly
by the caller and preserves the exact Crossref response plus a receipt in a
per-pair cache.  It never appends to the shared final query log.  Merge-only
mode independently validates complete shards against their frozen cache,
orders all 465 rows by the pair universe, substitutes the frozen response
timestamp, and atomically replaces the final query log.

Crossref metadata, abstracts, and snippets are discovery aids only.  Every
returned work is marked ``NOT_ACCEPTED_METADATA_ONLY_PENDING_TEXT_REVIEW``;
this script cannot accept association evidence or introduce vocabulary.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import tempfile
import time
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_RELATIVE_DIR = Path(
    "docs/audits/v49-exploration-full-space-closure-round1/raw"
)
DEFAULT_PAIR_UNIVERSE = RAW_RELATIVE_DIR / "pair-universe-v2.json"
DEFAULT_CACHE_DIR = RAW_RELATIVE_DIR / "association-query-cache-v2"
DEFAULT_MERGE_OUTPUT = RAW_RELATIVE_DIR / "association-query-log-v2.jsonl"

CROSSREF_ENDPOINT = "https://api.crossref.org/works"
CHANNEL = "CROSSREF_REST_WORKS_PUBLIC_POOL"
ROWS = 5
SELECT_FIELDS = (
    "DOI",
    "title",
    "author",
    "issued",
    "published",
    "container-title",
    "URL",
    "type",
    "abstract",
    "subject",
    "link",
    "references-count",
    "is-referenced-by-count",
    "score",
)
SELECT = ",".join(SELECT_FIELDS)
MIN_PUBLIC_POOL_INTERVAL_SECONDS = 1.05
EXPECTED_PAIR_COUNT = 465
EXPECTED_ACTIVE_VOCABULARY_COUNT = 31
QUERY_ID_PREFIX = "R16A-CROSSREF-QUERY"
PAIR_ID_PREFIX = "R16A-PAIR"
RESULT_REVIEW_STATUS = "NOT_ACCEPTED_METADATA_ONLY_PENDING_TEXT_REVIEW"
REJECTION_REASON = "METADATA_OR_SNIPPET_ONLY_FULL_TEXT_NOT_REVIEWED"
DEFAULT_USER_AGENT = (
    "TRACE-Round16A-Association-Census/2.0 "
    "(public scholarly-metadata capture; no automated evidence acceptance)"
)
RETRYABLE_HTTP_STATUSES = {408, 425, 429, 500, 502, 503, 504}
CAPTURE_RECEIPT_FORMAT = "trace-crossref-response-capture-v2"
QUERY_LOG_FORMAT = "trace-association-query-outcome-v2"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_PAIR_UNIVERSE_FIELDS = {
    "pairs",
    "pair_count",
    "expected_pair_count",
    "active_vocabulary_count",
    "pair_universe_hash",
    "self_pair_exclusion_count",
}
REQUIRED_PAIR_FIELDS = {
    "ordinal",
    "pair_id",
    "vocabulary_id_a",
    "vocabulary_id_b",
    "label_a",
    "label_b",
    "canonical_pair_key",
    "structurally_excluded",
}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def require_nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a non-empty string")
    return value.strip()


def require_sha256(value: Any, location: str) -> str:
    candidate = require_nonempty_string(value, location).lower()
    if not SHA256_RE.fullmatch(candidate):
        raise ValueError(f"{location} must be a lowercase SHA-256 digest")
    return candidate


def resolve_from_repo(repo: Path, value: Path | None, default: Path) -> Path:
    if value is None:
        return (repo / default).resolve()
    return value.resolve() if value.is_absolute() else (repo / value).resolve()


def display_path(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)


def canonical_pair_key(vocabulary_id_a: str, vocabulary_id_b: str) -> str:
    first, second = sorted((vocabulary_id_a, vocabulary_id_b))
    return f"{first}|{second}"


def expected_pair_id(pair_key: str) -> str:
    return f"{PAIR_ID_PREFIX}:{hashlib.sha256(pair_key.encode('utf-8')).hexdigest()}"


def read_pair_universe(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing pair universe: {path}")
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a top-level object")
    missing_top = sorted(REQUIRED_PAIR_UNIVERSE_FIELDS - set(document))
    if missing_top:
        raise ValueError(f"{path} is missing fields: {', '.join(missing_top)}")
    observed_universe_hash = require_sha256(
        document["pair_universe_hash"], f"{path}:pair_universe_hash"
    )
    hash_material = {
        key: value
        for key, value in document.items()
        if key != "pair_universe_hash"
    }
    expected_universe_hash = canonical_hash(hash_material)
    if observed_universe_hash != expected_universe_hash:
        raise ValueError(
            f"{path}:pair_universe_hash mismatch: expected "
            f"{expected_universe_hash}, received {observed_universe_hash}"
        )

    pairs = document["pairs"]
    if not isinstance(pairs, list):
        raise ValueError(f"{path}:pairs must be an array")
    for field, expected in (
        ("active_vocabulary_count", EXPECTED_ACTIVE_VOCABULARY_COUNT),
        ("expected_pair_count", EXPECTED_PAIR_COUNT),
        ("pair_count", EXPECTED_PAIR_COUNT),
        ("self_pair_exclusion_count", EXPECTED_ACTIVE_VOCABULARY_COUNT),
    ):
        value = document[field]
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise ValueError(f"{path}:{field} must equal {expected}, received {value!r}")
    if len(pairs) != EXPECTED_PAIR_COUNT:
        raise ValueError(f"{path}:pairs has {len(pairs)} rows, expected {EXPECTED_PAIR_COUNT}")

    validated: list[dict[str, Any]] = []
    pair_ids: set[str] = set()
    pair_keys: set[str] = set()
    ordinals: set[int] = set()
    for index, row in enumerate(pairs):
        location = f"{path}:pairs[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{location} must be an object")
        missing = sorted(REQUIRED_PAIR_FIELDS - set(row))
        if missing:
            raise ValueError(f"{location} is missing fields: {', '.join(missing)}")
        ordinal = row["ordinal"]
        if isinstance(ordinal, bool) or not isinstance(ordinal, int):
            raise ValueError(f"{location}.ordinal must be an integer")
        if ordinal in ordinals:
            raise ValueError(f"Duplicate pair ordinal: {ordinal}")
        ordinals.add(ordinal)
        pair_id = require_nonempty_string(row["pair_id"], f"{location}.pair_id")
        vocabulary_id_a = require_nonempty_string(
            row["vocabulary_id_a"], f"{location}.vocabulary_id_a"
        )
        vocabulary_id_b = require_nonempty_string(
            row["vocabulary_id_b"], f"{location}.vocabulary_id_b"
        )
        label_a = require_nonempty_string(row["label_a"], f"{location}.label_a")
        label_b = require_nonempty_string(row["label_b"], f"{location}.label_b")
        if vocabulary_id_a == vocabulary_id_b:
            raise ValueError(f"{location} is a forbidden self-pair")
        if "|" in vocabulary_id_a or "|" in vocabulary_id_b:
            raise ValueError(f"{location} vocabulary IDs cannot contain '|'")
        if row["structurally_excluded"] is not False:
            raise ValueError(f"{location}.structurally_excluded must be false")
        pair_key = canonical_pair_key(vocabulary_id_a, vocabulary_id_b)
        if row["canonical_pair_key"] != pair_key:
            raise ValueError(f"{location}.canonical_pair_key is not canonical")
        if vocabulary_id_a > vocabulary_id_b:
            raise ValueError(f"{location} vocabulary IDs are not in canonical order")
        if pair_id != expected_pair_id(pair_key):
            raise ValueError(f"{location}.pair_id does not match canonical pair key")
        if pair_id in pair_ids:
            raise ValueError(f"Duplicate pair_id: {pair_id}")
        if pair_key in pair_keys:
            raise ValueError(f"Duplicate canonical_pair_key: {pair_key}")
        pair_ids.add(pair_id)
        pair_keys.add(pair_key)
        validated.append({
            **row,
            "ordinal": ordinal,
            "pair_id": pair_id,
            "vocabulary_id_a": vocabulary_id_a,
            "vocabulary_id_b": vocabulary_id_b,
            "label_a": label_a,
            "label_b": label_b,
            "canonical_pair_key": pair_key,
        })

    expected_ordinals = set(range(1, EXPECTED_PAIR_COUNT + 1))
    if ordinals != expected_ordinals:
        missing = sorted(expected_ordinals - ordinals)
        unexpected = sorted(ordinals - expected_ordinals)
        raise ValueError(
            f"Non-contiguous pair ordinals: missing={missing}, unexpected={unexpected}"
        )
    validated.sort(key=lambda row: row["ordinal"])
    return document, validated


def quote_query_phrase(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def query_for_pair(pair: dict[str, Any]) -> str:
    return (
        f"{quote_query_phrase(pair['label_a'])} "
        f"{quote_query_phrase(pair['label_b'])} "
        '"graphic design" "design history"'
    )


def query_parameters(query: str) -> dict[str, str]:
    return {
        "query.bibliographic": query,
        "rows": str(ROWS),
        "select": SELECT,
        "sort": "score",
        "order": "desc",
    }


def request_url(query: str) -> str:
    return f"{CROSSREF_ENDPOINT}?{urlencode(query_parameters(query))}"


def query_id_for(pair: dict[str, Any], query: str) -> str:
    identity = {
        "pair_id": pair["pair_id"],
        "channel": CHANNEL,
        "request_parameters": query_parameters(query),
    }
    digest = hashlib.sha256((canonical_json(identity) + "\n").encode("utf-8")).hexdigest()
    return f"{QUERY_ID_PREFIX}:{digest}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def http_date_as_utc(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        parsed = http_date_as_utc(value)
        if parsed is None:
            return None
        then = datetime.fromisoformat(parsed.replace("Z", "+00:00"))
        return max(0.0, (then - datetime.now(timezone.utc)).total_seconds())


class PublicPoolRateLimiter:
    def __init__(self, minimum_interval_seconds: float, state_path: Path) -> None:
        if minimum_interval_seconds < MIN_PUBLIC_POOL_INTERVAL_SECONDS:
            raise ValueError(
                "Public-pool interval cannot be lower than "
                f"{MIN_PUBLIC_POOL_INTERVAL_SECONDS:.2f}s"
            )
        self.minimum_interval_seconds = minimum_interval_seconds
        self.state_path = state_path

    def wait_before_request(self) -> None:
        with exclusive_lock(self.state_path):
            last_request_started: float | None = None
            if self.state_path.exists():
                try:
                    state = json.loads(self.state_path.read_text(encoding="utf-8"))
                    last_request_started = float(state["last_request_started_unix"])
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                    raise ValueError(
                        f"Invalid public-pool rate state: {self.state_path}"
                    ) from error
                if not math.isfinite(last_request_started):
                    raise ValueError(
                        f"Non-finite public-pool rate state: {self.state_path}"
                    )
            now = time.time()
            if last_request_started is not None and last_request_started > now + 60.0:
                raise ValueError(
                    f"Public-pool rate state is implausibly in the future: {self.state_path}"
                )
            remaining = 0.0
            if last_request_started is not None:
                remaining = self.minimum_interval_seconds - (
                    now - last_request_started
                )
            if remaining > 0:
                time.sleep(remaining)
            started = time.time()
            atomic_write(
                self.state_path,
                (canonical_json({
                    "format": "trace-crossref-public-pool-rate-state-v1",
                    "last_request_started_unix": started,
                    "minimum_interval_seconds": self.minimum_interval_seconds,
                }) + "\n").encode("utf-8"),
            )


def selected_response_headers(headers: Any) -> dict[str, str]:
    selected_names = (
        "date",
        "content-type",
        "content-length",
        "x-api-pool",
        "x-rate-limit-limit",
        "x-rate-limit-interval",
        "x-rate-limit-type",
        "x-concurrency-limit",
    )
    output: dict[str, str] = {}
    for name in selected_names:
        value = headers.get(name)
        if value is not None:
            output[name] = str(value)
    return output


def decode_crossref_payload(content: bytes, location: str) -> dict[str, Any]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid Crossref JSON at {location}: {error}") from error
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise ValueError(f"Crossref response at {location} does not have status=ok")
    message = payload.get("message")
    if not isinstance(message, dict):
        raise ValueError(f"Crossref response at {location} has no message object")
    items = message.get("items")
    if not isinstance(items, list):
        raise ValueError(f"Crossref response at {location} has no items array")
    if len(items) > ROWS:
        raise ValueError(
            f"Crossref response at {location} returned {len(items)} rows; maximum is {ROWS}"
        )
    if any(not isinstance(item, dict) for item in items):
        raise ValueError(f"Crossref response at {location} contains a non-object item")
    total_results = message.get("total-results")
    if isinstance(total_results, bool) or not isinstance(total_results, int):
        raise ValueError(f"Crossref response at {location} has invalid total-results")
    return payload


def capture_crossref_response(
    *,
    pair: dict[str, Any],
    query: str,
    query_id: str,
    limiter: PublicPoolRateLimiter,
    timeout_seconds: float,
    max_attempts: int,
    backoff_base_seconds: float,
    user_agent: str,
) -> tuple[bytes, dict[str, Any]]:
    url = request_url(query)
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        limiter.wait_before_request()
        request_started = utc_now()
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": user_agent,
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                content = response.read()
                response_received = utc_now()
                status = int(response.status)
                headers = selected_response_headers(response.headers)
            if status != 200:
                raise RuntimeError(f"Unexpected Crossref HTTP status {status}")
            decode_crossref_payload(content, url)
            api_pool = headers.get("x-api-pool")
            # Crossref currently labels the list-style public pool
            # ``public-array``; older responses used ``public``. Both expose
            # the same public 1 request/second, concurrency-1 headers. No
            # polite-pool identity is accepted without an explicit mailto.
            if api_pool is not None and api_pool.casefold() not in {"public", "public-array"}:
                raise ValueError(
                    f"Crossref response used {api_pool!r} pool; public pool is required"
                )
            frozen_timestamp = (
                http_date_as_utc(headers.get("date")) or response_received
            )
            receipt = {
                "format": CAPTURE_RECEIPT_FORMAT,
                "version": "2",
                "query_id": query_id,
                "pair_id": pair["pair_id"],
                "query": query,
                "channel": CHANNEL,
                "endpoint": CROSSREF_ENDPOINT,
                "request_url": url,
                "request_parameters": query_parameters(query),
                "request_started_utc": request_started,
                "response_received_utc": response_received,
                "frozen_response_timestamp_utc": frozen_timestamp,
                "timestamp_freeze_source": (
                    "HTTP_DATE_HEADER" if headers.get("date") else "CAPTURE_COMPLETION"
                ),
                "http_status": status,
                "response_headers": headers,
                "response_sha256": sha256_bytes(content),
                "response_bytes": len(content),
                "attempt_count": attempt,
                "user_agent": user_agent,
                "rows": ROWS,
                "select_fields": list(SELECT_FIELDS),
                "public_pool_minimum_interval_seconds": (
                    limiter.minimum_interval_seconds
                ),
            }
            return content, receipt
        except HTTPError as error:
            last_error = error
            retryable = error.code in RETRYABLE_HTTP_STATUSES
            retry_after = retry_after_seconds(
                error.headers.get("Retry-After") if error.headers is not None else None
            )
        except (URLError, TimeoutError, socket.timeout, ConnectionError) as error:
            last_error = error
            retryable = True
            retry_after = None
        except ValueError as error:
            last_error = error
            retryable = True
            retry_after = None
        if not retryable or attempt >= max_attempts:
            break
        exponential = backoff_base_seconds * (2 ** (attempt - 1))
        delay = max(exponential, retry_after or 0.0)
        time.sleep(min(delay, 60.0))
    raise RuntimeError(
        f"Crossref query failed closed after {attempt} attempt(s) for "
        f"{pair['pair_id']}: {last_error}"
    ) from last_error


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def cache_paths(
    cache_dir: Path,
    pair: dict[str, Any],
    query_id: str,
) -> tuple[Path, Path]:
    pair_digest = pair["pair_id"].split(":", maxsplit=1)[-1]
    query_digest = query_id.split(":", maxsplit=1)[-1]
    pair_dir = cache_dir / f"{pair['ordinal']:04d}-{pair_digest[:16]}"
    return (
        pair_dir / f"{query_digest}.response.json",
        pair_dir / f"{query_digest}.capture.json",
    )


def write_cache(
    *,
    cache_dir: Path,
    response_path: Path,
    receipt_path: Path,
    response_content: bytes,
    receipt: dict[str, Any],
) -> None:
    if response_path.exists() or receipt_path.exists():
        raise FileExistsError(
            "Refusing to overwrite a partial or concurrent Crossref cache entry: "
            f"{response_path}, {receipt_path}"
        )
    receipt = {
        **receipt,
        "raw_response_ref": response_path.relative_to(cache_dir).as_posix(),
        "capture_receipt_ref": receipt_path.relative_to(cache_dir).as_posix(),
    }
    atomic_write(response_path, response_content)
    atomic_write(
        receipt_path,
        (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    )


def load_cache(
    *,
    cache_dir: Path,
    response_path: Path,
    receipt_path: Path,
    pair: dict[str, Any],
    query: str,
    query_id: str,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    response_exists = response_path.exists()
    receipt_exists = receipt_path.exists()
    if not response_exists and not receipt_exists:
        return None
    if response_exists != receipt_exists:
        raise ValueError(
            "Incomplete Crossref cache entry; refusing to infer missing capture state: "
            f"{response_path}, {receipt_path}"
        )
    if not response_path.is_file() or not receipt_path.is_file():
        raise ValueError("Crossref cache paths must be regular files")
    response_content = response_path.read_bytes()
    with receipt_path.open("r", encoding="utf-8") as handle:
        receipt = json.load(handle)
    if not isinstance(receipt, dict):
        raise ValueError(f"Invalid Crossref capture receipt: {receipt_path}")
    expected_values = {
        "format": CAPTURE_RECEIPT_FORMAT,
        "version": "2",
        "query_id": query_id,
        "pair_id": pair["pair_id"],
        "query": query,
        "channel": CHANNEL,
        "endpoint": CROSSREF_ENDPOINT,
        "request_url": request_url(query),
        "request_parameters": query_parameters(query),
        "http_status": 200,
        "rows": ROWS,
        "select_fields": list(SELECT_FIELDS),
        "raw_response_ref": response_path.relative_to(cache_dir).as_posix(),
        "capture_receipt_ref": receipt_path.relative_to(cache_dir).as_posix(),
    }
    for key, expected in expected_values.items():
        if receipt.get(key) != expected:
            raise ValueError(
                f"Crossref cache receipt mismatch at {receipt_path}:{key}: "
                f"expected {expected!r}, received {receipt.get(key)!r}"
            )
    if receipt.get("response_sha256") != sha256_bytes(response_content):
        raise ValueError(f"Crossref cache response hash mismatch: {response_path}")
    if receipt.get("response_bytes") != len(response_content):
        raise ValueError(f"Crossref cache response byte-count mismatch: {response_path}")
    require_nonempty_string(
        receipt.get("response_received_utc"),
        f"{receipt_path}:response_received_utc",
    )
    require_nonempty_string(
        receipt.get("frozen_response_timestamp_utc"),
        f"{receipt_path}:frozen_response_timestamp_utc",
    )
    require_nonempty_string(
        receipt.get("user_agent"),
        f"{receipt_path}:user_agent",
    )
    recorded_interval = receipt.get("public_pool_minimum_interval_seconds")
    if (
        isinstance(recorded_interval, bool)
        or not isinstance(recorded_interval, (int, float))
        or not math.isfinite(float(recorded_interval))
        or float(recorded_interval) < MIN_PUBLIC_POOL_INTERVAL_SECONDS
    ):
        raise ValueError(f"Invalid public-pool interval in {receipt_path}")
    headers = receipt.get("response_headers")
    if not isinstance(headers, dict):
        raise ValueError(f"{receipt_path}:response_headers must be an object")
    api_pool = headers.get("x-api-pool")
    if api_pool is not None and str(api_pool).casefold() not in {"public", "public-array"}:
        raise ValueError(f"Non-public Crossref pool recorded at {receipt_path}")
    payload = decode_crossref_payload(response_content, str(response_path))
    return payload, receipt


def first_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return ""


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            output.append(item.strip())
    return output


def author_metadata(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    output: list[dict[str, Any]] = []
    allowed = ("given", "family", "name", "ORCID", "sequence", "authenticated-orcid")
    for author in value:
        if not isinstance(author, dict):
            continue
        selected = {key: author[key] for key in allowed if key in author}
        if selected:
            output.append(selected)
    return output


def candidate_source_id(item: dict[str, Any]) -> str:
    doi = first_text(item.get("DOI")).casefold()
    if doi:
        return f"CROSSREF:DOI:{doi}"
    stable_metadata = {
        field: item.get(field)
        for field in SELECT_FIELDS
        if field in item
    }
    digest = hashlib.sha256(
        (canonical_json(stable_metadata) + "\n").encode("utf-8")
    ).hexdigest()
    return f"CROSSREF:WORK:{digest}"


def candidate_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload["message"]["items"]
    results: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    for rank, item in enumerate(items, start=1):
        source_id = candidate_source_id(item)
        if source_id in source_ids:
            raise ValueError(f"Duplicate candidate source ID in Crossref response: {source_id}")
        source_ids.add(source_id)
        results.append({
            "rank": rank,
            "candidate_source_id": source_id,
            "doi": first_text(item.get("DOI")),
            "title": first_text(item.get("title")),
            "authors": author_metadata(item.get("author")),
            "issued": item.get("issued"),
            "published": item.get("published"),
            "container_title": first_text(item.get("container-title")),
            "url": first_text(item.get("URL")),
            "type": first_text(item.get("type")),
            "abstract": first_text(item.get("abstract")),
            "subjects": string_list(item.get("subject")),
            "links": item.get("link") if isinstance(item.get("link"), list) else [],
            "references_count": item.get(
                "references-count", item.get("reference-count")
            ),
            "is_referenced_by_count": item.get("is-referenced-by-count"),
            "crossref_relevance_score": item.get("score"),
            "review_status": RESULT_REVIEW_STATUS,
            "accepted": False,
            "rejection_reason": REJECTION_REASON,
        })
    return results


def build_outcome(
    *,
    pair: dict[str, Any],
    pair_universe_hash: str,
    query: str,
    query_id: str,
    payload: dict[str, Any],
    receipt: dict[str, Any],
    timestamp_mode: str,
) -> dict[str, Any]:
    if timestamp_mode == "wall":
        timestamp = receipt["response_received_utc"]
        timestamp_source = "CAPTURE_COMPLETION_WALL_CLOCK"
    elif timestamp_mode == "frozen":
        timestamp = receipt["frozen_response_timestamp_utc"]
        timestamp_source = "FROZEN_PER_RESPONSE_TIMESTAMP"
    else:
        raise ValueError(f"Unknown timestamp mode: {timestamp_mode}")
    results = candidate_results(payload)
    candidate_ids = [row["candidate_source_id"] for row in results]
    total_results = payload["message"]["total-results"]
    return {
        "format": QUERY_LOG_FORMAT,
        "version": "2",
        "query_id": query_id,
        "pair_id": pair["pair_id"],
        "pair_ordinal": pair["ordinal"],
        "vocabulary_id_a": pair["vocabulary_id_a"],
        "vocabulary_id_b": pair["vocabulary_id_b"],
        "label_a": pair["label_a"],
        "label_b": pair["label_b"],
        "query": query,
        "channel": CHANNEL,
        "timestamp": timestamp,
        "timestamp_source": timestamp_source,
        "frozen_response_timestamp_utc": receipt[
            "frozen_response_timestamp_utc"
        ],
        "result_count": len(results),
        "crossref_total_result_count": total_results,
        "candidate_source_ids": candidate_ids,
        "accepted_source_ids": [],
        "rejected_source_ids": candidate_ids,
        "rejection_reasons": [
            {
                "candidate_source_id": source_id,
                "reason": REJECTION_REASON,
            }
            for source_id in candidate_ids
        ],
        "result_review_status": RESULT_REVIEW_STATUS,
        "candidate_results": results,
        "raw_response_ref": receipt["raw_response_ref"],
        "capture_receipt_ref": receipt["capture_receipt_ref"],
        "raw_response_sha256": receipt["response_sha256"],
        "pair_universe_hash": pair_universe_hash,
        "query_protocol": {
            "endpoint": CROSSREF_ENDPOINT,
            "rows": ROWS,
            "select_fields": list(SELECT_FIELDS),
            "public_pool_minimum_interval_seconds": receipt[
                "public_pool_minimum_interval_seconds"
            ],
            "metadata_or_snippet_is_evidence": False,
            "new_vocabulary_admitted": False,
        },
    }


def get_or_capture_outcome(
    *,
    pair: dict[str, Any],
    pair_universe_hash: str,
    cache_dir: Path,
    limiter: PublicPoolRateLimiter,
    timeout_seconds: float,
    max_attempts: int,
    backoff_base_seconds: float,
    user_agent: str,
) -> dict[str, Any]:
    query = query_for_pair(pair)
    query_id = query_id_for(pair, query)
    response_path, receipt_path = cache_paths(cache_dir, pair, query_id)
    with exclusive_lock(receipt_path):
        cached = load_cache(
            cache_dir=cache_dir,
            response_path=response_path,
            receipt_path=receipt_path,
            pair=pair,
            query=query,
            query_id=query_id,
        )
        if cached is None:
            response_content, receipt = capture_crossref_response(
                pair=pair,
                query=query,
                query_id=query_id,
                limiter=limiter,
                timeout_seconds=timeout_seconds,
                max_attempts=max_attempts,
                backoff_base_seconds=backoff_base_seconds,
                user_agent=user_agent,
            )
            write_cache(
                cache_dir=cache_dir,
                response_path=response_path,
                receipt_path=receipt_path,
                response_content=response_content,
                receipt=receipt,
            )
            cached = load_cache(
                cache_dir=cache_dir,
                response_path=response_path,
                receipt_path=receipt_path,
                pair=pair,
                query=query,
                query_id=query_id,
            )
            if cached is None:
                raise AssertionError(
                    "Crossref cache write did not produce a readable entry"
                )
    payload, receipt = cached
    return build_outcome(
        pair=pair,
        pair_universe_hash=pair_universe_hash,
        query=query,
        query_id=query_id,
        payload=payload,
        receipt=receipt,
        timestamp_mode="wall",
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing shard JSONL: {path}")
    content = path.read_bytes()
    if content and not content.endswith(b"\n"):
        raise ValueError(f"Shard JSONL is missing its final newline: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            raise ValueError(f"Blank JSONL row at {path}:{line_number}")
        try:
            row = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {error}") from error
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row is not an object at {path}:{line_number}")
        rows.append(row)
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (canonical_json(row) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        offset = 0
        while offset < len(content):
            written = os.write(descriptor, content[offset:])
            if written <= 0:
                raise OSError(
                    f"Partial shard write stopped after {offset} of {len(content)} bytes"
                )
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def exclusive_lock(target: Path) -> Iterator[None]:
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(f".{target.name}.lock")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f"Another process holds the lock for {target}") from error
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def validated_existing_shard(
    *,
    shard_path: Path,
    pair_by_id: dict[str, dict[str, Any]],
    pair_universe_hash: str,
    cache_dir: Path,
) -> dict[str, dict[str, Any]]:
    if not shard_path.exists():
        return {}
    rows = load_jsonl(shard_path)
    by_pair: dict[str, dict[str, Any]] = {}
    query_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=1):
        pair_id = require_nonempty_string(
            row.get("pair_id"), f"{shard_path}:{line_number}.pair_id"
        )
        if pair_id in by_pair:
            raise ValueError(f"Duplicate pair_id in shard {shard_path}: {pair_id}")
        pair = pair_by_id.get(pair_id)
        if pair is None:
            raise ValueError(f"Unknown pair_id in shard {shard_path}: {pair_id}")
        query = query_for_pair(pair)
        query_id = query_id_for(pair, query)
        if row.get("query_id") != query_id:
            raise ValueError(f"Query ID mismatch in shard {shard_path}:{line_number}")
        if query_id in query_ids:
            raise ValueError(f"Duplicate query_id in shard {shard_path}: {query_id}")
        query_ids.add(query_id)
        response_path, receipt_path = cache_paths(cache_dir, pair, query_id)
        cached = load_cache(
            cache_dir=cache_dir,
            response_path=response_path,
            receipt_path=receipt_path,
            pair=pair,
            query=query,
            query_id=query_id,
        )
        if cached is None:
            raise ValueError(f"Shard row has no frozen cache entry: {pair_id}")
        payload, receipt = cached
        expected = build_outcome(
            pair=pair,
            pair_universe_hash=pair_universe_hash,
            query=query,
            query_id=query_id,
            payload=payload,
            receipt=receipt,
            timestamp_mode="wall",
        )
        if canonical_json(row) != canonical_json(expected):
            raise ValueError(f"Shard/cache outcome mismatch for {pair_id}")
        by_pair[pair_id] = row
    return by_pair


def capture_mode(
    *,
    pairs: list[dict[str, Any]],
    pair_universe_hash: str,
    cache_dir: Path,
    shard_output: Path,
    start: int,
    count: int | None,
    minimum_interval_seconds: float,
    timeout_seconds: float,
    max_attempts: int,
    backoff_base_seconds: float,
    user_agent: str,
) -> dict[str, Any]:
    if shard_output.suffix != ".jsonl":
        raise ValueError("--shard-output must use a .jsonl suffix")
    if start < 0 or start >= len(pairs):
        raise ValueError(f"--start must be between 0 and {len(pairs) - 1}")
    if count is not None and count <= 0:
        raise ValueError("--count must be positive")
    stop = len(pairs) if count is None else min(len(pairs), start + count)
    selected = pairs[start:stop]
    pair_by_id = {pair["pair_id"]: pair for pair in pairs}
    limiter = PublicPoolRateLimiter(
        minimum_interval_seconds,
        cache_dir / ".crossref-public-pool-rate-state.json",
    )
    appended = 0
    reused = 0
    with exclusive_lock(shard_output):
        existing = validated_existing_shard(
            shard_path=shard_output,
            pair_by_id=pair_by_id,
            pair_universe_hash=pair_universe_hash,
            cache_dir=cache_dir,
        )
        for pair in selected:
            if pair["pair_id"] in existing:
                reused += 1
                continue
            outcome = get_or_capture_outcome(
                pair=pair,
                pair_universe_hash=pair_universe_hash,
                cache_dir=cache_dir,
                limiter=limiter,
                timeout_seconds=timeout_seconds,
                max_attempts=max_attempts,
                backoff_base_seconds=backoff_base_seconds,
                user_agent=user_agent,
            )
            append_jsonl(shard_output, outcome)
            existing[pair["pair_id"]] = outcome
            appended += 1
    return {
        "status": "CAPTURE_COMPLETE",
        "selected_start": start,
        "selected_count": len(selected),
        "appended_count": appended,
        "reused_count": reused,
        "shard_row_count": len(existing),
    }


def merge_mode(
    *,
    pairs: list[dict[str, Any]],
    pair_universe_hash: str,
    cache_dir: Path,
    shard_inputs: list[Path],
    merge_output: Path,
) -> dict[str, Any]:
    if not shard_inputs:
        raise ValueError("--merge-only requires at least one --shard-input")
    if merge_output.suffix != ".jsonl":
        raise ValueError("--merge-output must use a .jsonl suffix")
    resolved_inputs = [path.resolve() for path in shard_inputs]
    if len(resolved_inputs) != len(set(resolved_inputs)):
        raise ValueError("Duplicate --shard-input path")
    if merge_output.resolve() in set(resolved_inputs):
        raise ValueError("Merge output cannot also be a shard input")
    pair_by_id = {pair["pair_id"]: pair for pair in pairs}
    merged_shard_rows: dict[str, dict[str, Any]] = {}
    merged_query_ids: set[str] = set()
    with ExitStack() as shard_locks:
        for shard_path in sorted(resolved_inputs):
            shard_locks.enter_context(exclusive_lock(shard_path))
        for shard_path in resolved_inputs:
            rows = validated_existing_shard(
                shard_path=shard_path,
                pair_by_id=pair_by_id,
                pair_universe_hash=pair_universe_hash,
                cache_dir=cache_dir,
            )
            for pair_id, row in rows.items():
                if pair_id in merged_shard_rows:
                    raise ValueError(f"Pair appears in multiple shards: {pair_id}")
                query_id = row["query_id"]
                if query_id in merged_query_ids:
                    raise ValueError(f"Query appears in multiple shards: {query_id}")
                merged_query_ids.add(query_id)
                merged_shard_rows[pair_id] = row

    expected_pair_ids = {pair["pair_id"] for pair in pairs}
    observed_pair_ids = set(merged_shard_rows)
    missing = sorted(expected_pair_ids - observed_pair_ids)
    unexpected = sorted(observed_pair_ids - expected_pair_ids)
    if missing or unexpected or len(merged_shard_rows) != EXPECTED_PAIR_COUNT:
        raise ValueError(
            "Incomplete shard merge: "
            f"rows={len(merged_shard_rows)}, missing={len(missing)}, "
            f"unexpected={len(unexpected)}"
        )

    final_rows: list[dict[str, Any]] = []
    for pair in pairs:
        query = query_for_pair(pair)
        query_id = query_id_for(pair, query)
        response_path, receipt_path = cache_paths(cache_dir, pair, query_id)
        cached = load_cache(
            cache_dir=cache_dir,
            response_path=response_path,
            receipt_path=receipt_path,
            pair=pair,
            query=query,
            query_id=query_id,
        )
        if cached is None:
            raise ValueError(f"Missing cache during merge for {pair['pair_id']}")
        payload, receipt = cached
        final_rows.append(build_outcome(
            pair=pair,
            pair_universe_hash=pair_universe_hash,
            query=query,
            query_id=query_id,
            payload=payload,
            receipt=receipt,
            timestamp_mode="frozen",
        ))
    if len({row["pair_id"] for row in final_rows}) != EXPECTED_PAIR_COUNT:
        raise AssertionError("Final query log pair IDs are not unique")
    if len({row["query_id"] for row in final_rows}) != EXPECTED_PAIR_COUNT:
        raise AssertionError("Final query log query IDs are not unique")
    content = "".join(canonical_json(row) + "\n" for row in final_rows).encode("utf-8")
    with exclusive_lock(merge_output):
        atomic_write(merge_output, content)
    return {
        "status": "MERGE_COMPLETE",
        "merged_shard_count": len(resolved_inputs),
        "merged_row_count": len(final_rows),
        "output_sha256": sha256_bytes(content),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--pair-universe", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int)
    parser.add_argument("--shard-output", type=Path)
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--shard-input", type=Path, action="append", default=[])
    parser.add_argument("--merge-output", type=Path)
    parser.add_argument(
        "--minimum-interval-seconds",
        type=float,
        default=MIN_PUBLIC_POOL_INTERVAL_SECONDS,
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--backoff-base-seconds", type=float, default=2.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    pair_universe_path = resolve_from_repo(
        repo, args.pair_universe, DEFAULT_PAIR_UNIVERSE
    )
    cache_dir = resolve_from_repo(repo, args.cache_dir, DEFAULT_CACHE_DIR)
    merge_output = resolve_from_repo(repo, args.merge_output, DEFAULT_MERGE_OUTPUT)
    document, pairs = read_pair_universe(pair_universe_path)
    pair_universe_hash = document["pair_universe_hash"]

    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive")
    if args.max_attempts <= 0:
        raise ValueError("--max-attempts must be positive")
    if (
        not math.isfinite(args.backoff_base_seconds)
        or args.backoff_base_seconds <= 0
    ):
        raise ValueError("--backoff-base-seconds must be positive")
    if (
        not math.isfinite(args.minimum_interval_seconds)
        or args.minimum_interval_seconds < MIN_PUBLIC_POOL_INTERVAL_SECONDS
    ):
        raise ValueError(
            "--minimum-interval-seconds must be finite and at least "
            f"{MIN_PUBLIC_POOL_INTERVAL_SECONDS:.2f}"
        )
    require_nonempty_string(args.user_agent, "--user-agent")

    if args.merge_only:
        if args.shard_output is not None:
            raise ValueError("--shard-output is invalid with --merge-only")
        shard_inputs = [
            resolve_from_repo(repo, path, Path("unused"))
            for path in args.shard_input
        ]
        summary = merge_mode(
            pairs=pairs,
            pair_universe_hash=pair_universe_hash,
            cache_dir=cache_dir,
            shard_inputs=shard_inputs,
            merge_output=merge_output,
        )
        summary["output"] = display_path(merge_output, repo)
    else:
        if args.shard_input:
            raise ValueError("--shard-input is valid only with --merge-only")
        if args.shard_output is None:
            raise ValueError("Capture mode requires an explicit --shard-output path")
        shard_output = resolve_from_repo(repo, args.shard_output, Path("unused"))
        default_final_output = (repo / DEFAULT_MERGE_OUTPUT).resolve()
        if shard_output in {merge_output, default_final_output}:
            raise ValueError(
                "Capture mode cannot append to association-query-log-v2.jsonl; "
                "choose a dedicated shard path"
            )
        summary = capture_mode(
            pairs=pairs,
            pair_universe_hash=pair_universe_hash,
            cache_dir=cache_dir,
            shard_output=shard_output,
            start=args.start,
            count=args.count,
            minimum_interval_seconds=args.minimum_interval_seconds,
            timeout_seconds=args.timeout_seconds,
            max_attempts=args.max_attempts,
            backoff_base_seconds=args.backoff_base_seconds,
            user_agent=args.user_agent,
        )
        summary["shard_output"] = display_path(shard_output, repo)
    summary.update({
        "pair_universe": display_path(pair_universe_path, repo),
        "pair_universe_hash": pair_universe_hash,
        "cache_dir": display_path(cache_dir, repo),
        "accepted_source_count": 0,
        "result_review_status": RESULT_REVIEW_STATUS,
    })
    print(canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
