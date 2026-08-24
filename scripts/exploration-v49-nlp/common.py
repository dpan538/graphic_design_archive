#!/usr/bin/env python3
"""Immutable inputs and fail-closed helpers for TRACE v49 NLP research.

This module is intentionally independent of the frontend runtime.  Eligibility
comes only from the audited migration ledger.  Canonical text is streamed from
the frozen JSON payload and discarded before normalization whenever its object
is not public.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]

SOURCE_COMMIT = "580587a74f400d8a04d995937f4efb31e6621dd8"
CANONICAL_OBJECT_COUNT = 15_923
PUBLIC_OBJECT_COUNT = 7_995
HELD_OBJECT_COUNT = 7_928

REGISTRY_VERSION = "trace-nlp-text-field-registry-v1"
CORPUS_POLICY_VERSION = "trace-nlp-corpus-v1"
NORMALIZATION_VERSION = "trace-nlp-normalization-v1"
ASPECT_DOCUMENT_VERSION = "trace-nlp-aspect-document-v1"
BOILERPLATE_REGISTRY_VERSION = "trace-nlp-boilerplate-v1"

LEDGER_PATH = ROOT / "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"
SQLITE_PATH = ROOT / "data/prefreeze_candidate_v48.sqlite"
CANONICAL_PATH = ROOT / "generated/public_surfaces_prefreeze_candidate_v48.json"
CONTEXT_RECORDS_PATH = ROOT / "frontend/generated/trace-context-v1/records.json"
CONTEXT_MANIFEST_PATH = ROOT / "frontend/generated/trace-context-v1/manifest.json"
SPACETIME_RECORDS_PATH = ROOT / "frontend/generated/trace-spacetime-v1/record-index.json"
SPACETIME_MANIFEST_PATH = ROOT / "frontend/generated/trace-spacetime-v1/manifest.json"
ROUND6_REVIEW_PATH = (
    ROOT
    / "docs/audits/v49-exploration-similarity-round1/raw/human-review-summary.json"
)
ROUND6_LEDGER_PATH = (
    ROOT / "docs/audits/v49-exploration-similarity-round1/SHA256SUMS.txt"
)

EXPECTED_SHA256 = {
    "ledger": "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
    "sqlite": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
    "canonical": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
    "contextRecords": "c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7",
    "contextManifest": "ff8ebc15eeb95407b6b6b274dd2fc69ce4c3c183bb2f6a7e7f261c028b96f92c",
    "spacetimeRecords": "0f4720672f1e906301e3966dc3970737e3a1e459b27317b47018a2e6445c3dec",
    "spacetimeManifest": "93e88157865d987376ec8997e94a4101353038cf792e665d35e4c50b1c4384ec",
    "round6Review": "2178df8e22d367cf9ce391d3dfab9f579d7371d4a1aefa1d0b389eb9132d044f",
    "round6Ledger": "5774163988796716aa80be90268f1fa7e428ae3fd85a88424db54f6aaa3bc110",
}
EXPECTED_CONTEXT_PROJECTION_SHA256 = (
    "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
)
EXPECTED_SPACETIME_PROJECTION_SHA256 = (
    "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
)

PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PRIVATE_TOKEN_PATTERN = re.compile(
    r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH|\bTRB\d|file://)",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s<>]+", re.IGNORECASE)


class NlpBoundaryError(RuntimeError):
    """Raised when a frozen input or public/held boundary is violated."""


@dataclass(frozen=True)
class BoundaryReceipt:
    source_commit: str
    canonical_object_count: int
    public_object_count: int
    held_object_count: int
    overlap_count: int
    unclassified_count: int
    ledger_sha256: str

    def as_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceValue:
    """A public-cohort source value held only in memory or local artifacts."""

    public_object_id: str
    field_id: str
    role: str
    original_text: str
    original_text_hash: str
    source_artifact_hash: str
    source_name: str = ""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def verify_frozen_inputs() -> dict[str, str]:
    paths = {
        "ledger": LEDGER_PATH,
        "sqlite": SQLITE_PATH,
        "canonical": CANONICAL_PATH,
        "contextRecords": CONTEXT_RECORDS_PATH,
        "contextManifest": CONTEXT_MANIFEST_PATH,
        "spacetimeRecords": SPACETIME_RECORDS_PATH,
        "spacetimeManifest": SPACETIME_MANIFEST_PATH,
        "round6Review": ROUND6_REVIEW_PATH,
        "round6Ledger": ROUND6_LEDGER_PATH,
    }
    actual = {name: sha256_path(path) for name, path in paths.items()}
    if actual != EXPECTED_SHA256:
        changed = sorted(name for name in actual if actual[name] != EXPECTED_SHA256[name])
        raise NlpBoundaryError(f"frozen NLP source inputs changed: {changed}")

    context_manifest = load_json(CONTEXT_MANIFEST_PATH)
    if context_manifest.get("projectionSha256") != EXPECTED_CONTEXT_PROJECTION_SHA256:
        raise NlpBoundaryError("governed Context projection changed")
    if context_manifest.get("recordsSha256") != actual["contextRecords"]:
        raise NlpBoundaryError("governed Context records do not match their manifest")

    spacetime_manifest = load_json(SPACETIME_MANIFEST_PATH)
    if spacetime_manifest.get("projectionSha256") != EXPECTED_SPACETIME_PROJECTION_SHA256:
        raise NlpBoundaryError("governed Spacetime projection changed")
    if (
        not isinstance(spacetime_manifest.get("payloadSha256"), Mapping)
        or spacetime_manifest["payloadSha256"].get("record-index.json")
        != actual["spacetimeRecords"]
    ):
        raise NlpBoundaryError("governed Spacetime records do not match their manifest")
    return actual


@lru_cache(maxsize=1)
def _eligibility_sets() -> tuple[frozenset[str], frozenset[str]]:
    verify_frozen_inputs()
    public: set[str] = set()
    held: set[str] = set()
    unclassified = 0
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            object_id = row.get("surface_id_exact", "")
            if not PUBLIC_ID_PATTERN.fullmatch(object_id):
                raise NlpBoundaryError("eligibility ledger contains an invalid surface ID")
            disposition = row.get("research_disposition")
            if disposition == "eligible":
                public.add(object_id)
            elif disposition == "held":
                held.add(object_id)
            else:
                unclassified += 1
    if (
        len(public) != PUBLIC_OBJECT_COUNT
        or len(held) != HELD_OBJECT_COUNT
        or public & held
        or unclassified
        or len(public | held) != CANONICAL_OBJECT_COUNT
    ):
        raise NlpBoundaryError("authoritative public/held ledger does not reconcile")
    return frozenset(public), frozenset(held)


def load_public_boundary() -> BoundaryReceipt:
    public, held = _eligibility_sets()
    return BoundaryReceipt(
        source_commit=SOURCE_COMMIT,
        canonical_object_count=CANONICAL_OBJECT_COUNT,
        public_object_count=len(public),
        held_object_count=len(held),
        overlap_count=len(public & held),
        unclassified_count=CANONICAL_OBJECT_COUNT - len(public | held),
        ledger_sha256=EXPECTED_SHA256["ledger"],
    )


def load_public_ids() -> tuple[str, ...]:
    public, _held = _eligibility_sets()
    return tuple(sorted(public))


def ensure_public_object_id(object_id: Any) -> str:
    """Validate without revealing whether a rejected identifier is held or unknown."""

    public, _held = _eligibility_sets()
    if (
        not isinstance(object_id, str)
        or not PUBLIC_ID_PATTERN.fullmatch(object_id)
        or object_id not in public
    ):
        raise NlpBoundaryError("object is not available in the public NLP cohort")
    return object_id


def contains_private_token(text: str) -> bool:
    return bool(UUID_PATTERN.search(text) or PRIVATE_TOKEN_PATTERN.search(text))


@lru_cache(maxsize=1)
def load_context_records() -> tuple[dict[str, Any], ...]:
    verify_frozen_inputs()
    public = set(load_public_ids())
    document = load_json(CONTEXT_RECORDS_PATH)
    rows: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for record in document.get("records", []):
        selected = record.get("selectedRecord", {})
        object_id = ensure_public_object_id(selected.get("surfaceId"))
        if object_id in identifiers:
            raise NlpBoundaryError("governed Context projection repeats a public object")
        title = selected.get("title")
        if not isinstance(title, str) or not title.strip():
            raise NlpBoundaryError("governed Context title is missing")
        if contains_private_token(title) or URL_PATTERN.search(title):
            raise NlpBoundaryError("governed Context title contains a prohibited token")
        identifiers.add(object_id)
        rows.append(record)
    if identifiers != public or len(rows) != PUBLIC_OBJECT_COUNT:
        raise NlpBoundaryError("governed Context cohort differs from the public ledger")
    return tuple(rows)


def load_context_titles() -> dict[str, str]:
    return {
        record["selectedRecord"]["surfaceId"]: record["selectedRecord"]["title"].strip()
        for record in load_context_records()
    }


@lru_cache(maxsize=4)
def _top_level_array_offsets(path: Path) -> dict[str, int]:
    """Return byte offsets after every top-level array opener.

    A structure-aware scan is necessary because names such as ``folders`` also
    occur inside surface records.  Structural JSON bytes are ASCII, so scanning
    bytes preserves exact UTF-8 offsets without decoding held text values.
    """

    offsets: dict[str, int] = {}
    depth = 0
    in_string = False
    escaped = False
    string_bytes = bytearray()
    pending_key: str | None = None
    pending_colon = False
    absolute = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            for index, byte in enumerate(chunk):
                if in_string:
                    if escaped:
                        escaped = False
                        string_bytes.append(byte)
                    elif byte == 0x5C:  # backslash
                        escaped = True
                        string_bytes.append(byte)
                    elif byte == 0x22:  # quote
                        in_string = False
                        if depth == 1:
                            try:
                                pending_key = json.loads(
                                    b'"' + bytes(string_bytes) + b'"'
                                )
                            except Exception:
                                pending_key = None
                            pending_colon = False
                        string_bytes.clear()
                    else:
                        string_bytes.append(byte)
                    continue

                if byte == 0x22:  # quote
                    in_string = True
                    string_bytes.clear()
                    continue
                if byte in b" \t\r\n":
                    continue
                if depth == 1 and pending_key is not None:
                    if byte == 0x3A and not pending_colon:  # colon
                        pending_colon = True
                        continue
                    if byte == 0x5B and pending_colon:  # array opener
                        offsets[pending_key] = absolute + index + 1
                        pending_key = None
                        pending_colon = False
                        depth += 1
                        continue
                    pending_key = None
                    pending_colon = False
                if byte in (0x7B, 0x5B):  # { [
                    depth += 1
                elif byte in (0x7D, 0x5D):  # } ]
                    depth -= 1
                    if depth < 0:
                        raise NlpBoundaryError("canonical JSON has invalid structural depth")
            absolute += len(chunk)
    if in_string or depth != 0:
        raise NlpBoundaryError("canonical JSON structural scan did not close cleanly")
    return offsets


def _iter_json_array(path: Path, marker: str, *, chunk_size: int = 1024 * 1024) -> Iterator[Any]:
    """Stream one named top-level array using the standard-library decoder."""

    match = re.fullmatch(r'"([^"\\]+)":\[', marker)
    if not match:
        raise NlpBoundaryError(f"invalid top-level JSON array marker: {marker}")
    name = match.group(1)
    offset = _top_level_array_offsets(path).get(name)
    if offset is None:
        raise NlpBoundaryError(f"top-level JSON array not found: {name}")

    decoder = json.JSONDecoder()
    binary_handle = path.open("rb")
    binary_handle.seek(offset)
    with io.TextIOWrapper(binary_handle, encoding="utf-8") as handle:
        buffer = ""
        position = 0
        while True:
            while True:
                while position < len(buffer) and buffer[position] in " \t\r\n,":
                    position += 1
                if position < len(buffer):
                    break
                buffer = handle.read(chunk_size)
                position = 0
                if not buffer:
                    raise NlpBoundaryError("JSON array ended unexpectedly")
            if buffer[position] == "]":
                return
            try:
                value, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                remainder = buffer[position:]
                chunk = handle.read(chunk_size)
                if not chunk:
                    raise NlpBoundaryError("JSON array element is malformed")
                buffer = remainder + chunk
                position = 0
                continue
            yield value
            position = end
            if position > chunk_size:
                buffer = buffer[position:]
                position = 0


def iter_public_canonical_surfaces() -> Iterator[dict[str, Any]]:
    """Yield only public surfaces; held records are discarded before text processing."""

    verify_frozen_inputs()
    public, held = _eligibility_sets()
    seen: set[str] = set()
    canonical_seen = 0
    for value in _iter_json_array(CANONICAL_PATH, '"surfaces":['):
        if not isinstance(value, dict):
            raise NlpBoundaryError("canonical surface is not an object")
        object_id = value.get("surfaceId")
        if not isinstance(object_id, str) or not PUBLIC_ID_PATTERN.fullmatch(object_id):
            raise NlpBoundaryError("canonical payload contains an invalid surface ID")
        canonical_seen += 1
        if object_id in held:
            continue
        if object_id not in public:
            raise NlpBoundaryError("canonical payload contains an unclassified surface")
        if object_id in seen:
            raise NlpBoundaryError("canonical payload repeats a public surface")
        seen.add(object_id)
        yield value
    if canonical_seen != CANONICAL_OBJECT_COUNT or seen != set(public):
        raise NlpBoundaryError("canonical payload does not reconcile to the public ledger")


@lru_cache(maxsize=1)
def load_public_canonical_surfaces() -> tuple[dict[str, Any], ...]:
    return tuple(iter_public_canonical_surfaces())


def self_test() -> dict[str, Any]:
    boundary = load_public_boundary()
    titles = load_context_titles()
    if len(titles) != PUBLIC_OBJECT_COUNT:
        raise AssertionError("public title coverage changed")
    rejected = 0
    for value in ("SURF-UNKNOWN-ROUND7", "not-a-public-id"):
        try:
            ensure_public_object_id(value)
        except NlpBoundaryError as exc:
            if str(exc) != "object is not available in the public NLP cohort":
                raise AssertionError("held and unknown failures must be indistinguishable")
            rejected += 1
    if rejected != 2:
        raise AssertionError("negative public-boundary controls did not fail")
    return {
        "status": "PASS",
        "boundary": boundary.as_mapping(),
        "contextTitleCount": len(titles),
        "frozenInputSha256": dict(EXPECTED_SHA256),
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
