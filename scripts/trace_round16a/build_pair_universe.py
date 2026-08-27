#!/usr/bin/env python3
"""Build the complete frozen Round 16A unordered active-vocabulary pair universe.

The input contract is intentionally exact: ``active-vocabulary-v2.json`` must
contain an ``active_vocabulary`` array and the frozen identity fields produced
by the Round 16A vocabulary census.  This builder never admits terms, searches
for terms, or assigns association outcomes.  It only enumerates every distinct
unordered pair and records self-pairs as structural exclusions in metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from itertools import combinations
from pathlib import Path
import re
import tempfile
import unicodedata
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_RELATIVE_DIR = Path(
    "docs/audits/v49-exploration-full-space-closure-round1/raw"
)
DEFAULT_INPUT = RAW_RELATIVE_DIR / "active-vocabulary-v2.json"
DEFAULT_OUTPUT_JSON = RAW_RELATIVE_DIR / "pair-universe-v2.json"
DEFAULT_OUTPUT_TSV = RAW_RELATIVE_DIR / "pair-universe-v2.tsv"
DEFAULT_FUTURE_REGISTRY = RAW_RELATIVE_DIR / "future-vocabulary-candidates.tsv"

FORMAT = "trace-exploration-pair-universe-v2"
VERSION = "2"
EXPECTED_ACTIVE_VOCABULARY_COUNT = 31
EXPECTED_PAIR_COUNT = 465
PAIR_ID_PREFIX = "R16A-PAIR"
SELF_PAIR_EXCLUSION_ID_PREFIX = "R16A-SELF-PAIR-EXCLUSION"
NORMALIZATION_POLICY = "UNICODE_NFKC_WHITESPACE_CASEFOLD_V1"
PAIR_KEY_POLICY = "LEXICOGRAPHIC_VOCABULARY_ID_A_PIPE_VOCABULARY_ID_B_V1"
PAIR_ID_POLICY = f"{PAIR_ID_PREFIX}:sha256(canonical_pair_key)"
HASH_POLICY = "SHA256_UTF8_SORTED_KEY_COMPACT_JSON_PLUS_LF_EXCLUDING_SELF_V1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_TOP_LEVEL_FIELDS = {
    "active_vocabulary",
    "active_vocabulary_count",
    "universe_hash",
    "active_vocabulary_hash",
    "database_snapshot",
}
REQUIRED_VOCABULARY_FIELDS = {
    "vocabulary_id",
    "canonical_label",
    "normalized_label",
    "category_ids",
    "bounded_sense",
    "source_attestations",
    "academic_support",
}
FUTURE_REGISTRY_FIELDS = [
    "vocabulary_candidate_id",
    "canonical_label",
    "normalized_label",
    "status",
    "governed_reason",
    "research_gate",
    "decision_refs_json",
    "provenance_rounds_json",
    "universe_hash",
]


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def normalize_label(value: Any) -> str:
    label = clean_label(value)
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", label)).casefold().strip()


def require_nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a non-empty string")
    return value.strip()


def require_sha256(value: Any, location: str) -> str:
    candidate = require_nonempty_string(value, location).lower()
    if not SHA256_RE.fullmatch(candidate):
        raise ValueError(f"{location} must be a lowercase SHA-256 digest")
    return candidate


def require_nonempty_unique_string_list(value: Any, location: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{location} must be a non-empty array")
    output: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        cleaned = require_nonempty_string(item, f"{location}[{index}]")
        if cleaned in seen:
            raise ValueError(f"Duplicate value in {location}: {cleaned}")
        seen.add(cleaned)
        output.append(cleaned)
    return output


def require_nonempty_array(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{location} must be a non-empty array")
    if any(item is None for item in value):
        raise ValueError(f"{location} cannot contain null entries")
    return value


def read_active_vocabulary(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing active-vocabulary input: {path}")
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a top-level object")
    missing_top = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(document))
    if missing_top:
        raise ValueError(f"{path} is missing required fields: {', '.join(missing_top)}")

    rows = document["active_vocabulary"]
    if not isinstance(rows, list):
        raise ValueError(f"{path}:active_vocabulary must be an array")
    declared_count = document["active_vocabulary_count"]
    if isinstance(declared_count, bool) or not isinstance(declared_count, int):
        raise ValueError(f"{path}:active_vocabulary_count must be an integer")
    if declared_count != len(rows):
        raise ValueError(
            f"{path}:active_vocabulary_count={declared_count} but rows={len(rows)}"
        )
    if declared_count != EXPECTED_ACTIVE_VOCABULARY_COUNT:
        raise ValueError(
            "Round 16A active-vocabulary freeze mismatch: "
            f"expected {EXPECTED_ACTIVE_VOCABULARY_COUNT}, received {declared_count}"
        )

    require_sha256(document["universe_hash"], f"{path}:universe_hash")
    require_sha256(
        document["active_vocabulary_hash"],
        f"{path}:active_vocabulary_hash",
    )
    database_snapshot = document["database_snapshot"]
    if not (
        (isinstance(database_snapshot, str) and database_snapshot.strip())
        or (isinstance(database_snapshot, dict) and database_snapshot)
    ):
        raise ValueError(
            f"{path}:database_snapshot must be a non-empty string or object"
        )

    validated: list[dict[str, Any]] = []
    vocabulary_ids: set[str] = set()
    normalized_labels: set[str] = set()
    for index, row in enumerate(rows):
        location = f"{path}:active_vocabulary[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{location} must be an object")
        missing = sorted(REQUIRED_VOCABULARY_FIELDS - set(row))
        if missing:
            raise ValueError(f"{location} is missing fields: {', '.join(missing)}")

        vocabulary_id = require_nonempty_string(
            row["vocabulary_id"], f"{location}.vocabulary_id"
        )
        if "|" in vocabulary_id:
            raise ValueError(f"{location}.vocabulary_id cannot contain '|'")
        canonical_label = clean_label(row["canonical_label"])
        if not canonical_label:
            raise ValueError(f"{location}.canonical_label must be a non-empty string")
        normalized = require_nonempty_string(
            row["normalized_label"], f"{location}.normalized_label"
        )
        expected_normalized = normalize_label(canonical_label)
        if normalized != expected_normalized:
            raise ValueError(
                f"{location}.normalized_label mismatch: expected "
                f"{expected_normalized!r}, received {normalized!r}"
            )
        if vocabulary_id in vocabulary_ids:
            raise ValueError(f"Duplicate vocabulary_id: {vocabulary_id}")
        if normalized in normalized_labels:
            raise ValueError(f"Duplicate normalized_label: {normalized}")
        vocabulary_ids.add(vocabulary_id)
        normalized_labels.add(normalized)

        category_ids = require_nonempty_unique_string_list(
            row["category_ids"], f"{location}.category_ids"
        )
        bounded_sense = require_nonempty_string(
            row["bounded_sense"], f"{location}.bounded_sense"
        )
        require_nonempty_array(
            row["source_attestations"], f"{location}.source_attestations"
        )
        require_nonempty_array(
            row["academic_support"], f"{location}.academic_support"
        )
        validated.append({
            "vocabulary_id": vocabulary_id,
            "canonical_label": canonical_label,
            "normalized_label": normalized,
            "category_ids": sorted(category_ids),
            "bounded_sense": bounded_sense,
        })

    validated.sort(key=lambda row: row["vocabulary_id"])
    return document, validated


def canonical_pair_key(vocabulary_id_a: str, vocabulary_id_b: str) -> str:
    first, second = sorted((vocabulary_id_a, vocabulary_id_b))
    return f"{first}|{second}"


def pair_id_for(pair_key: str) -> str:
    digest = hashlib.sha256(pair_key.encode("utf-8")).hexdigest()
    return f"{PAIR_ID_PREFIX}:{digest}"


def build_pair_universe(
    *,
    repo: Path,
    input_path: Path,
    document: dict[str, Any],
    vocabulary: list[dict[str, Any]],
) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for ordinal, (left, right) in enumerate(combinations(vocabulary, 2), start=1):
        pair_key = canonical_pair_key(left["vocabulary_id"], right["vocabulary_id"])
        expected_left_id, expected_right_id = pair_key.split("|", maxsplit=1)
        if (
            left["vocabulary_id"] != expected_left_id
            or right["vocabulary_id"] != expected_right_id
        ):
            raise AssertionError("Vocabulary sort order violated canonical pair ordering")
        pairs.append({
            "ordinal": ordinal,
            "pair_id": pair_id_for(pair_key),
            "vocabulary_id_a": left["vocabulary_id"],
            "vocabulary_id_b": right["vocabulary_id"],
            "label_a": left["canonical_label"],
            "label_b": right["canonical_label"],
            "normalized_label_a": left["normalized_label"],
            "normalized_label_b": right["normalized_label"],
            "canonical_pair_key": pair_key,
            "structurally_excluded": False,
        })

    expected_keys = {
        canonical_pair_key(left["vocabulary_id"], right["vocabulary_id"])
        for left, right in combinations(vocabulary, 2)
    }
    actual_keys = [row["canonical_pair_key"] for row in pairs]
    actual_pair_ids = [row["pair_id"] for row in pairs]
    duplicate_pair_count = len(actual_keys) - len(set(actual_keys))
    duplicate_pair_id_count = len(actual_pair_ids) - len(set(actual_pair_ids))
    missing_keys = sorted(expected_keys - set(actual_keys))
    unexpected_keys = sorted(set(actual_keys) - expected_keys)
    expected_pair_count = len(vocabulary) * (len(vocabulary) - 1) // 2
    if expected_pair_count != EXPECTED_PAIR_COUNT:
        raise AssertionError(
            f"Expected-count invariant failed: {expected_pair_count} != {EXPECTED_PAIR_COUNT}"
        )
    if len(pairs) != EXPECTED_PAIR_COUNT:
        raise AssertionError(f"Generated {len(pairs)} pairs, expected {EXPECTED_PAIR_COUNT}")
    if duplicate_pair_count or duplicate_pair_id_count or missing_keys or unexpected_keys:
        raise AssertionError(
            "Pair-universe completeness failure: "
            f"duplicate_keys={duplicate_pair_count}, "
            f"duplicate_ids={duplicate_pair_id_count}, "
            f"missing={len(missing_keys)}, unexpected={len(unexpected_keys)}"
        )
    if any(row["vocabulary_id_a"] == row["vocabulary_id_b"] for row in pairs):
        raise AssertionError("Generated pair universe contains a self-pair")

    self_pair_exclusions = []
    for row in vocabulary:
        self_key = f"{row['vocabulary_id']}|{row['vocabulary_id']}"
        exclusion_digest = hashlib.sha256(self_key.encode("utf-8")).hexdigest()
        self_pair_exclusions.append({
            "self_pair_exclusion_id": (
                f"{SELF_PAIR_EXCLUSION_ID_PREFIX}:{exclusion_digest}"
            ),
            "vocabulary_id": row["vocabulary_id"],
            "canonical_label": row["canonical_label"],
            "canonical_self_pair_key": self_key,
            "reason": "SELF_PAIR_STRUCTURALLY_EXCLUDED",
        })

    canonical_material = {
        "format": FORMAT,
        "version": VERSION,
        "frozen": True,
        "normalization_policy": NORMALIZATION_POLICY,
        "pair_key_policy": PAIR_KEY_POLICY,
        "pair_id_policy": PAIR_ID_POLICY,
        "pair_universe_hash_policy": HASH_POLICY,
        "source_input": {
            "path": display_path(input_path, repo),
            "sha256": sha256_file(input_path),
            "bytes": input_path.stat().st_size,
            "universe_hash": document["universe_hash"],
            "active_vocabulary_hash": document["active_vocabulary_hash"],
            "database_snapshot": document["database_snapshot"],
        },
        "active_vocabulary_count": len(vocabulary),
        "expected_pair_count": expected_pair_count,
        "pair_count": len(pairs),
        "duplicate_pair_count": duplicate_pair_count,
        "duplicate_pair_id_count": duplicate_pair_id_count,
        "missing_pair_count": len(missing_keys),
        "unexpected_pair_count": len(unexpected_keys),
        "self_pair_exclusion_count": len(self_pair_exclusions),
        "self_pair_exclusions": self_pair_exclusions,
        "pairs": pairs,
    }
    return {
        **canonical_material,
        "pair_universe_hash": canonical_hash(canonical_material),
    }


def json_bytes(universe: dict[str, Any]) -> bytes:
    return (
        json.dumps(universe, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def tsv_bytes(universe: dict[str, Any]) -> bytes:
    fieldnames = [
        "ordinal",
        "pair_id",
        "vocabulary_id_a",
        "vocabulary_id_b",
        "label_a",
        "label_b",
        "normalized_label_a",
        "normalized_label_b",
        "canonical_pair_key",
        "structurally_excluded",
        "pair_universe_hash",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for pair in universe["pairs"]:
        writer.writerow({
            **pair,
            "structurally_excluded": "false",
            "pair_universe_hash": universe["pair_universe_hash"],
        })
    return buffer.getvalue().encode("utf-8")


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


def expected_future_registry_header() -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(FUTURE_REGISTRY_FIELDS)
    return buffer.getvalue().encode("utf-8")


def ensure_future_registry(path: Path, *, check: bool) -> bool:
    expected_header = expected_future_registry_header()
    if path.exists():
        if not path.is_file():
            raise ValueError(f"Future-vocabulary registry is not a file: {path}")
        return False
    if check:
        raise FileNotFoundError(f"Missing future-vocabulary registry: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return ensure_future_registry(path, check=True)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(expected_header)
        handle.flush()
        os.fsync(handle.fileno())
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    parser.add_argument("--future-registry", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare deterministic artifacts without writing.",
    )
    return parser.parse_args()


def resolve_from_repo(repo: Path, value: Path | None, default: Path) -> Path:
    if value is None:
        return repo / default
    return value.resolve() if value.is_absolute() else (repo / value).resolve()


def display_path(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    input_path = resolve_from_repo(repo, args.input, DEFAULT_INPUT)
    output_json = resolve_from_repo(repo, args.output_json, DEFAULT_OUTPUT_JSON)
    output_tsv = resolve_from_repo(repo, args.output_tsv, DEFAULT_OUTPUT_TSV)
    future_registry = resolve_from_repo(
        repo, args.future_registry, DEFAULT_FUTURE_REGISTRY
    )

    document, vocabulary = read_active_vocabulary(input_path)
    universe = build_pair_universe(
        repo=repo,
        input_path=input_path,
        document=document,
        vocabulary=vocabulary,
    )
    outputs = {
        output_json: json_bytes(universe),
        output_tsv: tsv_bytes(universe),
    }
    future_registry_created = False
    if args.check:
        mismatches = [
            str(path)
            for path, expected in outputs.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        ensure_future_registry(future_registry, check=True)
        if mismatches:
            raise SystemExit("Deterministic output mismatch: " + ", ".join(mismatches))
    else:
        future_registry_created = ensure_future_registry(future_registry, check=False)
        for path, content in outputs.items():
            atomic_write(path, content)

    print(canonical_json({
        "status": "PASS" if args.check else "GENERATED",
        "active_vocabulary_count": universe["active_vocabulary_count"],
        "pair_count": universe["pair_count"],
        "self_pair_exclusion_count": universe["self_pair_exclusion_count"],
        "duplicate_pair_count": universe["duplicate_pair_count"],
        "missing_pair_count": universe["missing_pair_count"],
        "pair_universe_hash": universe["pair_universe_hash"],
        "future_registry": display_path(future_registry, repo),
        "future_registry_created": future_registry_created,
        "outputs": [display_path(path, repo) for path in outputs],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
