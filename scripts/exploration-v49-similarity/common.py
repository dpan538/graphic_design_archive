#!/usr/bin/env python3
"""Shared immutable inputs and canonical helpers for Round 6 similarity research.

This module deliberately delegates public-record normalization to the sealed
Round 5 loader.  It verifies the Round 5 audit ledger and signal registry before
returning any data, and it never exposes held identifiers to downstream model
code.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
ROUND5_SCRIPT = ROOT / "scripts/exploration-v49-analysis/common.py"
ROUND5_RESEARCH_DIR = ROOT / "docs/research/trace-v49-exploration-discovery-round1"
ROUND5_AUDIT_DIR = ROOT / "docs/audits/v49-spacetime-closure-exploration-discovery"
ROUND5_SIGNAL_REGISTRY = ROUND5_RESEARCH_DIR / "13_EXPLORATION_SIGNAL_REGISTRY.tsv"
ROUND5_SIGNAL_SUMMARY = ROUND5_AUDIT_DIR / "raw/exploration-signal-registry-summary.json"
ROUND5_GENERATION_SUMMARY = ROUND5_AUDIT_DIR / "raw/exploration-generation-summary.json"
CONTEXT_RECORDS_PATH = ROOT / "frontend/generated/trace-context-v1/records.json"
CONTEXT_MANIFEST_PATH = ROOT / "frontend/generated/trace-context-v1/manifest.json"
SPACETIME_MANIFEST_PATH = ROOT / "frontend/generated/trace-spacetime-v1/manifest.json"

SOURCE_SHA = "0e311f0b88b4adc3cbfe2080ac98d622013cc6d3"
RESEARCH_RELEASE_ID = "v49-api-contract-fresh-c"
RESEARCH_MANIFEST_SHA256 = "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a"
CONTEXT_PROJECTION_ID = "trace-context-v1"
ROUND5_BUNDLE_SHA256 = "bdb7f5f8350dde9e8264d254654d691ecc68e4fd279aa61ec2188bf2d65c8285"
ROUND5_SIGNAL_TSV_SHA256 = "0c5ad4a0d39190eaf63998b54d3b65d99cb160f3ad2653ebb4517f89a9dc9eab"
ROUND5_SIGNAL_RECEIPT_SHA256 = "224aaea1123ad9d5730006aa5e779c17b4673fdfc9ee87988f3f96ac8ce26424"
CONTEXT_PROJECTION_SHA256 = "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
SPACETIME_PROJECTION_ID = "trace-spacetime-v1"
SPACETIME_PROJECTION_SHA256 = "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
PUBLIC_OBJECT_COUNT = 7_995
HELD_OBJECT_COUNT = 7_928
EXHAUSTIVE_PAIR_COUNT = PUBLIC_OBJECT_COUNT * (PUBLIC_OBJECT_COUNT - 1) // 2

PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PRIVATE_VALUE_PATTERN = re.compile(
    r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH|https?://|file://)",
    re.IGNORECASE,
)


class SimilarityInputError(RuntimeError):
    """Raised when a frozen or public-safety input contract is violated."""


def canonical_json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    separators = None if pretty else (",", ":")
    indent = 2 if pretty else None
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=separators,
            indent=indent,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def tsv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    lines = ["\t".join(headers)]
    for row in rows:
        lines.append("\t".join(clean_cell(row.get(header)) for header in headers))
    return ("\n".join(lines) + "\n").encode("utf-8")


def quantile_r7(values: Iterable[int | float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _load_round5_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("trace_v49_round5_common", ROUND5_SCRIPT)
    if spec is None or spec.loader is None:
        raise SimilarityInputError("Round 5 normalized loader could not be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_round5_audit_ledger() -> dict[str, str]:
    ledger = ROUND5_AUDIT_DIR / "SHA256SUMS.txt"
    verified: dict[str, str] = {}
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        target = ROUND5_AUDIT_DIR / relative
        actual = sha256_path(target)
        if actual != digest:
            raise SimilarityInputError(f"Round 5 audit payload changed: {relative}")
        verified[relative] = actual
    if len(verified) != 21:
        raise SimilarityInputError("Round 5 audit ledger does not contain 21 bound payloads")
    return verified


def load_signal_registry() -> dict[str, Any]:
    ledger_receipts = verify_round5_audit_ledger()
    if sha256_path(ROUND5_SIGNAL_REGISTRY) != ROUND5_SIGNAL_TSV_SHA256:
        raise SimilarityInputError("Round 5 signal registry TSV changed")
    rows = load_tsv(ROUND5_SIGNAL_REGISTRY)
    if len(rows) != 64 or len({row.get("signal_id") for row in rows}) != 64:
        raise SimilarityInputError("Round 5 signal registry must contain 64 unique signals")
    summary = load_json(ROUND5_SIGNAL_SUMMARY)
    if summary.get("deterministicReceipt", {}).get("sha256") != ROUND5_SIGNAL_RECEIPT_SHA256:
        raise SimilarityInputError("Round 5 signal registry receipt changed")
    generation = load_json(ROUND5_GENERATION_SUMMARY)
    if generation.get("deterministicBundleSha256") != ROUND5_BUNDLE_SHA256:
        raise SimilarityInputError("Round 5 deterministic bundle changed")
    return {
        "rows": rows,
        "rowsSha256": sha256_path(ROUND5_SIGNAL_REGISTRY),
        "deterministicReceiptSha256": ROUND5_SIGNAL_RECEIPT_SHA256,
        "bundleSha256": ROUND5_BUNDLE_SHA256,
        "auditLedgerReceipts": ledger_receipts,
    }


def load_normalized_public_records() -> dict[str, Any]:
    round5 = _load_round5_module()
    loaded = round5.load_normalized_public_records()
    records = loaded.get("records")
    if not isinstance(records, list) or len(records) != PUBLIC_OBJECT_COUNT:
        raise SimilarityInputError("normalized public cohort does not contain 7,995 records")
    identifiers = [record.get("objectId") for record in records]
    if identifiers != sorted(identifiers) or len(set(identifiers)) != PUBLIC_OBJECT_COUNT:
        raise SimilarityInputError("normalized public object identities are not sorted and unique")
    if any(not isinstance(identifier, str) or not PUBLIC_ID_PATTERN.fullmatch(identifier) for identifier in identifiers):
        raise SimilarityInputError("normalized cohort contains an invalid public object ID")
    text = json.dumps(records, ensure_ascii=False, sort_keys=True)
    if UUID_PATTERN.search(text) or PRIVATE_VALUE_PATTERN.search(text):
        raise SimilarityInputError("normalized public cohort contains a private identifier or URL")
    if loaded.get("heldObjectCount") != HELD_OBJECT_COUNT:
        raise SimilarityInputError("held cohort count changed")
    return loaded


def load_public_titles() -> dict[str, str]:
    """Return safe governed titles for the bounded human-review packet only."""

    loaded = load_normalized_public_records()
    public_ids = {record["objectId"] for record in loaded["records"]}
    document = load_json(CONTEXT_RECORDS_PATH)
    titles: dict[str, str] = {}
    for record in document.get("records", []):
        selected = record.get("selectedRecord", {})
        object_id = selected.get("surfaceId")
        title = selected.get("title")
        if object_id not in public_ids or not isinstance(title, str) or not title.strip():
            raise SimilarityInputError("governed Context title packet does not match the public cohort")
        titles[object_id] = title.strip()
    if set(titles) != public_ids:
        raise SimilarityInputError("governed Context title packet is incomplete")
    text = json.dumps(titles, ensure_ascii=False, sort_keys=True)
    if UUID_PATTERN.search(text) or PRIVATE_VALUE_PATTERN.search(text):
        raise SimilarityInputError("governed public title packet contains a private identifier or URL")
    return titles


def source_receipt() -> dict[str, Any]:
    signal = load_signal_registry()
    normalized = load_normalized_public_records()
    context_manifest = load_json(CONTEXT_MANIFEST_PATH)
    spacetime_manifest = load_json(SPACETIME_MANIFEST_PATH)
    if (
        context_manifest.get("projectionId") != CONTEXT_PROJECTION_ID
        or context_manifest.get("projectionSha256") != CONTEXT_PROJECTION_SHA256
        or context_manifest.get("sourceRelease", {}).get("id") != RESEARCH_RELEASE_ID
        or context_manifest.get("sourceRelease", {}).get("manifestSha256")
        != RESEARCH_MANIFEST_SHA256
    ):
        raise SimilarityInputError("governed Context projection/release binding changed")
    if (
        spacetime_manifest.get("projectionId") != SPACETIME_PROJECTION_ID
        or spacetime_manifest.get("projectionSha256") != SPACETIME_PROJECTION_SHA256
        or spacetime_manifest.get("sourceRelease", {}).get("researchReleaseId")
        != RESEARCH_RELEASE_ID
        or spacetime_manifest.get("sourceRelease", {}).get("researchManifestSha256")
        != RESEARCH_MANIFEST_SHA256
    ):
        raise SimilarityInputError("governed Spacetime projection/release binding changed")
    return {
        "sourceCommit": SOURCE_SHA,
        "researchReleaseId": RESEARCH_RELEASE_ID,
        "researchManifestSha256": RESEARCH_MANIFEST_SHA256,
        "contextProjectionId": CONTEXT_PROJECTION_ID,
        "contextProjectionSha256": CONTEXT_PROJECTION_SHA256,
        "spacetimeProjectionId": SPACETIME_PROJECTION_ID,
        "spacetimeProjectionSha256": SPACETIME_PROJECTION_SHA256,
        "contextManifestSha256": sha256_path(CONTEXT_MANIFEST_PATH),
        "spacetimeManifestSha256": sha256_path(SPACETIME_MANIFEST_PATH),
        "explorationSignalRegistrySha256": signal["deterministicReceiptSha256"],
        "explorationRound5BundleSha256": signal["bundleSha256"],
        "publicObjectCount": len(normalized["records"]),
        "heldObjectCount": normalized["heldObjectCount"],
        "exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT,
    }
