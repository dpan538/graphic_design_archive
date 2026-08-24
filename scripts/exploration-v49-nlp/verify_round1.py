#!/usr/bin/env python3
"""Fail-closed verifier for TRACE v49 NLP Semantic Corpus Audit Round 1.

Normal verification is read-only.  It validates the exact research and audit
inventories, TSV schemas, raw receipts, integrity ledgers, frozen inputs,
public/held boundary, protected changed-file scope, and all 26 NLP invariants.
``--self-test`` creates and mutates only a temporary fixture.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import generate_round1 as contract


DEFAULT_RESEARCH_DIR = contract.DEFAULT_RESEARCH_DIR
DEFAULT_AUDIT_DIR = contract.DEFAULT_AUDIT_RAW_DIR.parent
VERIFICATION_SCHEMA_VERSION = "trace-nlp-round1-verification/v1"
MANIFEST_COLUMNS = ("path", "bytes", "sha256", "role")
RAW_COMPONENTS = {
    "nlp-round1-analysis-summary.json": "central",
    "corpus-governance-summary.json": "corpus-governance",
    "language-tokenization-summary.json": "language-tokenization",
    "duplication-boilerplate-summary.json": "duplication-boilerplate",
    "model-artifact-summary.json": "model-artifacts",
    "evaluation-registry-summary.json": "evaluation-registry",
    "lexical-baseline-summary.json": "lexical",
    "dense-cross-language-summary.json": "dense-cross-language",
    "metadata-leakage-summary.json": "metadata-leakage",
    "hubness-robustness-summary.json": "hubness-robustness",
    "aspect-structured-hybrid-summary.json": "aspect-structured-hybrid",
    "review-architecture-summary.json": "review-architecture",
    "run-performance-security-summary.json": "runs-performance-security",
}
FROZEN_INPUTS = {
    "data/prefreeze_candidate_v48.sqlite": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
    "docs/audits/v49-exploration-similarity-round1/SHA256SUMS.txt": "5774163988796716aa80be90268f1fa7e428ae3fd85a88424db54f6aaa3bc110",
    "docs/audits/v49-exploration-similarity-round1/raw/human-review-summary.json": "2178df8e22d367cf9ce391d3dfab9f579d7371d4a1aefa1d0b389eb9132d044f",
    "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv": "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
    "frontend/generated/trace-context-v1/manifest.json": "ff8ebc15eeb95407b6b6b274dd2fc69ce4c3c183bb2f6a7e7f261c028b96f92c",
    "frontend/generated/trace-context-v1/records.json": "c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7",
    "frontend/generated/trace-spacetime-v1/manifest.json": "93e88157865d987376ec8997e94a4101353038cf792e665d35e4c50b1c4384ec",
    "frontend/generated/trace-spacetime-v1/record-index.json": "0f4720672f1e906301e3966dc3970737e3a1e459b27317b47018a2e6445c3dec",
    "generated/public_surfaces_prefreeze_candidate_v48.json": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
}

PUBLIC_ID_TOKEN_RE = re.compile(r"(?<![A-Z0-9-])SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*(?![A-Z0-9-])")
FORBIDDEN_MODEL_SUFFIXES = frozenset(
    {".safetensors", ".bin", ".pt", ".pth", ".onnx", ".gguf", ".ftz", ".npy", ".npz", ".faiss"}
)
ALLOWED_ROLES = frozenset(
    {
        "OBJECT_TITLE", "OBJECT_ALTERNATE_TITLE", "OBJECT_DESCRIPTION",
        "OBJECT_SUBJECT_TERMS", "OBJECT_CAPTION", "CREATOR_ATTRIBUTION",
        "OBJECT_TYPE_LABEL", "SOURCE_RECORD_TITLE", "SOURCE_NARRATIVE",
        "SOURCE_COLLECTION_DESCRIPTION", "CURATORIAL_NOTE", "READING_NOTE",
        "DOSSIER_TEXT", "REGISTRATION_TEXT", "PROVENANCE_TEXT", "RIGHTS_TEXT",
        "BOILERPLATE", "INTERNAL_CONTROL_TEXT", "UNCLASSIFIED_UNSAFE",
    }
)
ALLOWED_GOVERNANCE_DECISIONS = frozenset(
    {
        "INCLUDE_TITLE_CHANNEL", "INCLUDE_SUBJECT_CHANNEL",
        "INCLUDE_OBJECT_DESCRIPTION_CHANNEL", "INCLUDE_SOURCE_NARRATIVE_DIAGNOSTIC",
        "INCLUDE_CREATOR_METADATA_ONLY", "INCLUDE_OBJECT_TYPE_METADATA_ONLY",
        "EXPLANATION_ONLY", "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY", "HOLD", "EXCLUDE",
    }
)
ALLOWED_BOILERPLATE_DECISIONS = frozenset(
    {"REMOVE_FOR_NLP_INPUT", "MASK_SOURCE_IDENTITY", "KEEP_SEMANTIC", "KEEP_DIAGNOSTIC", "HOLD"}
)


class VerificationError(RuntimeError):
    """Raised when any Round 7 verification gate fails."""


@dataclass(frozen=True)
class Table:
    name: str
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    payload: bytes


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise VerificationError(f"{label} must be a JSON object")
    return {str(key): item for key, item in value.items()}


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise VerificationError(f"{label} is not an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise VerificationError(f"{label} is not an integer") from error
    if isinstance(value, float) and value != result:
        raise VerificationError(f"{label} is not an integer")
    return result


def _number(value: Any, label: str) -> float:
    if value in (None, "", "N/A", "NOT_RUN", "NOT_SELECTED"):
        raise VerificationError(f"{label} is unavailable")
    if isinstance(value, bool):
        raise VerificationError(f"{label} is not numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise VerificationError(f"{label} is not numeric") from error
    if not math.isfinite(result):
        raise VerificationError(f"{label} is not finite")
    return result


def _bool(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    text = str(value).strip().casefold()
    if text in {"true", "yes", "1", "pass"}:
        return True
    if text in {"false", "no", "0", "fail"}:
        return False
    raise VerificationError(f"{label} is not boolean: {value!r}")


def _json_string_set(value: Any, label: str) -> set[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as error:
            raise VerificationError(f"{label} is not a JSON string array") from error
    else:
        decoded = value
    if isinstance(decoded, (str, bytes, bytearray)) or not isinstance(decoded, Sequence):
        raise VerificationError(f"{label} is not a JSON string array")
    result = [str(item) for item in decoded]
    if any(not item for item in result) or len(result) != len(set(result)):
        raise VerificationError(f"{label} has blank or duplicate values")
    return set(result)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"raw evidence is not a regular file: {path.name}")
    payload = path.read_bytes()
    if len(payload) > contract.MAX_RAW_FILE_BYTES:
        raise VerificationError(f"raw evidence exceeds size bound: {path.name}")
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or b"\r" in payload:
        raise VerificationError(f"raw evidence has non-canonical line framing: {path.name}")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"raw evidence is not strict UTF-8 JSON: {path.name}") from error
    if contract.canonical_json_bytes(value, pretty=True) != payload:
        raise VerificationError(f"raw evidence is not canonical JSON: {path.name}")
    return _mapping(value, path.name)


def _direct_names(path: Path) -> set[str]:
    if not path.is_dir() or path.is_symlink():
        raise VerificationError(f"required directory is missing or is a symlink: {path}")
    return {entry.name for entry in path.iterdir()}


def _validate_exact_inventory(research_dir: Path, audit_dir: Path) -> None:
    research_names = _direct_names(research_dir)
    if research_names != set(contract.RESEARCH_FILES):
        raise VerificationError(
            f"research inventory differs: missing={sorted(set(contract.RESEARCH_FILES)-research_names)} "
            f"extra={sorted(research_names-set(contract.RESEARCH_FILES))}"
        )
    for name in contract.RESEARCH_FILES:
        path = research_dir / name
        if not path.is_file() or path.is_symlink():
            raise VerificationError(f"research entry is not one regular file: {name}")

    expected_audit = {*contract.AUDIT_DOCUMENT_FILES, "MANIFEST.tsv", "SHA256SUMS.txt", "raw"}
    audit_names = _direct_names(audit_dir)
    if audit_names != expected_audit:
        raise VerificationError(
            f"audit inventory differs: missing={sorted(expected_audit-audit_names)} "
            f"extra={sorted(audit_names-expected_audit)}"
        )
    for name in (*contract.AUDIT_DOCUMENT_FILES, "MANIFEST.tsv", "SHA256SUMS.txt"):
        path = audit_dir / name
        if not path.is_file() or path.is_symlink():
            raise VerificationError(f"audit entry is not one regular file: {name}")
    raw_dir = audit_dir / "raw"
    raw_names = _direct_names(raw_dir)
    if raw_names != set(contract.RAW_FILES):
        raise VerificationError(
            f"raw inventory differs: missing={sorted(set(contract.RAW_FILES)-raw_names)} "
            f"extra={sorted(raw_names-set(contract.RAW_FILES))}"
        )
    for name in contract.RAW_FILES:
        path = raw_dir / name
        if not path.is_file() or path.is_symlink():
            raise VerificationError(f"raw entry is not one regular file: {name}")


def _parse_tsv(path: Path) -> Table:
    payload = path.read_bytes()
    if len(payload) > contract.MAX_TSV_FILE_BYTES:
        raise VerificationError(f"TSV exceeds size bound: {path.name}")
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or b"\r" in payload:
        raise VerificationError(f"TSV has non-canonical line framing: {path.name}")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationError(f"TSV is not UTF-8: {path.name}") from error
    reader = csv.reader(io.StringIO(text, newline=""), delimiter="\t")
    values = list(reader)
    if not values:
        raise VerificationError(f"TSV is empty: {path.name}")
    headers = tuple(values[0])
    expected = contract.TABLE_SCHEMAS[path.name]
    if headers != expected:
        raise VerificationError(f"TSV header differs from exact schema: {path.name}")
    if len(headers) != len(set(headers)) or any(not header for header in headers):
        raise VerificationError(f"TSV header is blank or duplicated: {path.name}")
    rows: list[dict[str, str]] = []
    for ordinal, cells in enumerate(values[1:], start=2):
        if len(cells) != len(headers):
            raise VerificationError(f"TSV row {ordinal} is not rectangular: {path.name}")
        if any(contract.CONTROL_RE.search(cell) for cell in cells):
            raise VerificationError(f"TSV row {ordinal} contains a control character: {path.name}")
        rows.append(dict(zip(headers, cells)))
    if not rows:
        raise VerificationError(f"TSV lacks an explicit result/N/A row: {path.name}")
    canonical = contract.tsv_bytes(path.name, rows)
    if canonical != payload:
        raise VerificationError(f"TSV is not in canonical deterministic order/encoding: {path.name}")
    return Table(path.name, headers, tuple(rows), payload)


def _load_tables(research_dir: Path) -> dict[str, Table]:
    tables = {name: _parse_tsv(research_dir / name) for name in contract.RESEARCH_TSV_FILES}
    try:
        contract._validate_table_semantics({name: table.rows for name, table in tables.items()})
    except contract.GenerationError as error:
        raise VerificationError(f"shared table semantics failed: {error}") from error
    return tables


def _load_raw(audit_dir: Path) -> dict[str, dict[str, Any]]:
    raw_dir = audit_dir / "raw"
    raw = {name: _read_json(raw_dir / name) for name in contract.RAW_FILES}
    total = sum((raw_dir / name).stat().st_size for name in contract.RAW_FILES)
    if total > contract.MAX_RAW_TOTAL_BYTES:
        raise VerificationError("aggregate raw evidence exceeds the total size bound")
    numeric_cells = contract._numeric_sequence_cell_count(raw)
    if numeric_cells > contract.MAX_TOTAL_NUMERIC_ARRAY_CELLS:
        raise VerificationError(
            "raw evidence exceeds the recursive numeric-array cell budget: "
            f"{numeric_cells}>{contract.MAX_TOTAL_NUMERIC_ARRAY_CELLS}"
        )
    analysis_hashes: set[str] = set()
    table_receipt_hashes: set[str] = set()
    for name, wrapper in raw.items():
        if wrapper.get("schemaVersion") != contract.RAW_SCHEMA_VERSION:
            raise VerificationError(f"raw schema version differs: {name}")
        if wrapper.get("component") != RAW_COMPONENTS[name]:
            raise VerificationError(f"raw component identity differs: {name}")
        analysis_hash = str(wrapper.get("analysisSummarySha256", ""))
        if not contract.SHA256_RE.fullmatch(analysis_hash):
            raise VerificationError(f"raw analysis hash is invalid: {name}")
        analysis_hashes.add(analysis_hash)
        payload = wrapper.get("payload")
        if not isinstance(payload, Mapping):
            raise VerificationError(f"raw payload is not an object: {name}")
        if wrapper.get("payloadSha256") != contract.sha256_json(payload):
            raise VerificationError(f"raw payload hash differs: {name}")
        receipts = wrapper.get("tableReceipts")
        if not isinstance(receipts, Mapping):
            raise VerificationError(f"raw wrapper lacks table receipts: {name}")
        table_receipt_hashes.add(contract.sha256_json(receipts))
        _validate_raw_bounded(payload, path=f"raw/{name}")
    if len(analysis_hashes) != 1 or len(table_receipt_hashes) != 1:
        raise VerificationError("raw files do not bind one analysis/table receipt set")
    return raw


def _validate_raw_bounded(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = contract._normalize_key(str(key))
            if normalized in {
                "rankings", "rankingsbyquery", "fullrankingrows", "embeddingvectors",
                "embeddings", "vectors", "corpusdocuments", "documentsbyid", "rawtextdump",
                "pairmatrix", "scorematrix", "allpairs", "neighborsbyquery",
            } and child not in (None, False, 0, "", [], {}):
                raise VerificationError(f"unbounded raw payload key: {path}.{key}")
            if (
                isinstance(child, Sequence)
                and not isinstance(child, (str, bytes, bytearray))
                and child
                and any(
                    token in normalized
                    for token in ("embedding", "vector", "matrix", "densevalue", "fullranking", "neighborsbyquery")
                )
            ):
                raise VerificationError(f"forbidden model/ranking array: {path}.{key}")
            _validate_raw_bounded(child, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > contract.MAX_TABLE_ROWS:
            raise VerificationError(f"raw array exceeds bound: {path}")
        scalar = all(
            not isinstance(child, (Mapping, Sequence))
            or isinstance(child, (str, bytes, bytearray))
            for child in value
        )
        numeric = scalar and all(
            isinstance(child, (int, float)) and not isinstance(child, bool)
            for child in value
        )
        numeric_matrix = any(
            isinstance(child, Sequence)
            and not isinstance(child, (str, bytes, bytearray))
            and child
            and all(
                isinstance(cell, (int, float)) and not isinstance(cell, bool)
                for cell in child
            )
            for child in value
        )
        if numeric_matrix:
            raise VerificationError(f"numeric matrix payload is forbidden: {path}")
        if numeric and len(value) > contract.MAX_RAW_NUMERIC_ARRAY_ITEMS:
            raise VerificationError(f"numeric vector payload exceeds the aggregate bound: {path}")
        if scalar and len(value) > contract.MAX_RAW_SCALAR_ARRAY_ITEMS:
            raise VerificationError(f"scalar raw array exceeds the aggregate bound: {path}")
        for index, child in enumerate(value):
            _validate_raw_bounded(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        if contract.UUID_RE.search(value) or contract.PRIVATE_ID_RE.search(value) or contract.URL_RE.search(value):
            raise VerificationError(f"unsafe string in raw evidence: {path}")
    elif isinstance(value, float) and not math.isfinite(value):
        raise VerificationError(f"non-finite raw value: {path}")


def _validate_table_receipts(tables: Mapping[str, Table], raw: Mapping[str, Mapping[str, Any]]) -> None:
    receipts = _mapping(raw["nlp-round1-analysis-summary.json"]["tableReceipts"], "tableReceipts")
    if set(receipts) != set(contract.RESEARCH_TSV_FILES):
        raise VerificationError("raw table receipts do not cover the exact TSV inventory")
    for name, table in tables.items():
        receipt = _mapping(receipts[name], f"tableReceipts.{name}")
        rows = list(table.rows)
        expected = {
            "bytes": len(table.payload),
            "columns": list(table.headers),
            "columnCount": len(table.headers),
            "rowCount": len(rows),
            "rowsSha256": contract.sha256_json(rows),
            "sha256": _sha256(table.payload),
        }
        if receipt != expected:
            raise VerificationError(f"TSV receipt differs: {name}")


def _validate_audit_ledgers(audit_dir: Path) -> None:
    manifest_path = audit_dir / "MANIFEST.tsv"
    manifest = _parse_simple_manifest(manifest_path)
    expected_paths = [*contract.AUDIT_DOCUMENT_FILES, *(f"raw/{name}" for name in contract.RAW_FILES)]
    if [row["path"] for row in manifest] != expected_paths:
        raise VerificationError("MANIFEST.tsv paths/order differ from the exact audit inventory")
    expected_roles = {
        **{name: "AUDIT_NARRATIVE" for name in contract.AUDIT_DOCUMENT_FILES},
        **{f"raw/{name}": "BOUNDED_RAW_EVIDENCE" for name in contract.RAW_FILES},
    }
    manifest_hashes: dict[str, str] = {}
    for row in manifest:
        relative = row["path"]
        path = audit_dir / relative
        if not path.is_file() or path.is_symlink():
            raise VerificationError(f"manifest entry is not a regular file: {relative}")
        payload = path.read_bytes()
        digest = _sha256(payload)
        if _integer(row["bytes"], f"manifest {relative} bytes") != len(payload):
            raise VerificationError(f"manifest byte count differs: {relative}")
        if row["sha256"] != digest or not contract.SHA256_RE.fullmatch(row["sha256"]):
            raise VerificationError(f"manifest SHA-256 differs: {relative}")
        if row["role"] != expected_roles[relative]:
            raise VerificationError(f"manifest role differs: {relative}")
        manifest_hashes[relative] = digest

    sums_path = audit_dir / "SHA256SUMS.txt"
    payload = sums_path.read_bytes()
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or b"\r" in payload:
        raise VerificationError("SHA256SUMS.txt has non-canonical framing")
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise VerificationError("SHA256SUMS.txt is not UTF-8") from error
    expected_sums = [
        *(f"{manifest_hashes[path]}  {path}" for path in expected_paths),
        f"{_sha256(manifest_path.read_bytes())}  MANIFEST.tsv",
    ]
    if lines != expected_sums:
        raise VerificationError("SHA256SUMS.txt does not exactly seal MANIFEST.tsv and its entries")


def _parse_simple_manifest(path: Path) -> list[dict[str, str]]:
    payload = path.read_bytes()
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or b"\r" in payload:
        raise VerificationError("MANIFEST.tsv has non-canonical framing")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""), delimiter="\t")
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise VerificationError("MANIFEST.tsv header differs")
        rows = [dict(row) for row in reader]
    except UnicodeDecodeError as error:
        raise VerificationError("MANIFEST.tsv is not UTF-8") from error
    if len(rows) != len(contract.AUDIT_DOCUMENT_FILES) + len(contract.RAW_FILES):
        raise VerificationError("MANIFEST.tsv row count differs")
    return rows


def _validate_research_receipts(
    research_dir: Path,
    raw: Mapping[str, Mapping[str, Any]],
) -> None:
    central = _mapping(raw["nlp-round1-analysis-summary.json"]["payload"], "central payload")
    if central.get("researchReceiptsComplete") is not True:
        raise VerificationError("central raw receipt is not bound to the final research package")
    receipts = _mapping(central.get("researchFileReceipts"), "researchFileReceipts")
    if set(receipts) != set(contract.RESEARCH_FILES):
        raise VerificationError("research receipts do not cover the exact 28-file inventory")
    for name in contract.RESEARCH_FILES:
        payload = (research_dir / name).read_bytes()
        receipt = _mapping(receipts[name], f"research receipt {name}")
        if receipt != {"bytes": len(payload), "sha256": _sha256(payload)}:
            raise VerificationError(f"research receipt differs: {name}")


def _validate_package_text(research_dir: Path, audit_dir: Path) -> None:
    markdown_paths = [research_dir / name for name in contract.RESEARCH_FILES if name.endswith(".md")]
    markdown_paths += [audit_dir / name for name in contract.AUDIT_DOCUMENT_FILES]
    markdown_total = 0
    for path in markdown_paths:
        payload = path.read_bytes()
        if len(payload) > contract.MAX_MARKDOWN_FILE_BYTES:
            raise VerificationError(f"Markdown exceeds bounded file size: {path.name}")
        markdown_total += len(payload)
        text = path.read_text(encoding="utf-8")
        if "{{PENDING:" in text or "DRAFT_AWAITING_FINAL" in text:
            raise VerificationError(f"unresolved draft token remains: {path.name}")
    if markdown_total > contract.MAX_MARKDOWN_TOTAL_BYTES:
        raise VerificationError("Markdown exceeds the bounded aggregate size")
    decision_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            research_dir / "00_EXECUTIVE_DECISION.md",
            research_dir / "27_ROUND_DECISION.md",
            audit_dir / "00_EXECUTIVE_RECEIPT.md",
        )
    )
    for receipt in (
        "PHASE_STATUS=STOPPED_RECOVERABLE_CHECKPOINT",
        "NLP_MODEL_DECISION=NLP_CORPUS_AUDIT_ONLY",
        "DENSE_MODEL_SHORTLIST_COUNT=0",
        "DENSE_MODEL_SHORTLIST_IDS=NONE",
        "PUBLIC_NLP_MODEL_SELECTED=false",
        "STRUCTURED_NLP_FUSION_SELECTED=false",
    ):
        if receipt not in decision_text:
            raise VerificationError(f"decision narratives lack coherent checkpoint receipt: {receipt}")


def _central_components(raw: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    central = _mapping(raw["nlp-round1-analysis-summary.json"]["payload"], "central")
    required = (
        "source", "governance", "boundary", "evaluationRegistry", "models",
        "review", "performance", "security", "decision", "invariants",
    )
    components = {name: _mapping(central.get(name), f"central.{name}") for name in required}
    try:
        contract._validate_pins(components)
        contract._validate_decisions(components, require_review_rows=False)
    except contract.GenerationError as error:
        raise VerificationError(f"central contract validation failed: {error}") from error
    return components


def _validate_frozen_inputs(
    repo_root: Path,
    components: Mapping[str, Mapping[str, Any]],
    *,
    fixture: bool,
) -> None:
    if fixture:
        return
    declared = _mapping(components["source"].get("frozenInputs"), "source.frozenInputs")
    if declared != FROZEN_INPUTS:
        raise VerificationError("central frozen-input mapping differs from the authoritative contract")
    for relative, expected in FROZEN_INPUTS.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or _sha256_path(path) != expected:
            raise VerificationError(f"frozen input changed: {relative}")
    context_manifest = json.loads((repo_root / "frontend/generated/trace-context-v1/manifest.json").read_text(encoding="utf-8"))
    if context_manifest.get("projectionSha256") != contract.CONTEXT_PROJECTION_SHA256:
        raise VerificationError("Context projection SHA changed")
    spacetime_manifest = json.loads((repo_root / "frontend/generated/trace-spacetime-v1/manifest.json").read_text(encoding="utf-8"))
    if spacetime_manifest.get("projectionSha256") != contract.SPACETIME_PROJECTION_SHA256:
        raise VerificationError("Spacetime projection SHA changed")


def _load_public_held_ids(repo_root: Path) -> tuple[set[str], set[str]]:
    path = repo_root / "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"
    public: set[str] = set()
    held: set[str] = set()
    unclassified = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            object_id = str(row.get("surface_id_exact", ""))
            if not contract.PUBLIC_ID_RE.fullmatch(object_id):
                raise VerificationError("eligibility ledger contains an invalid surface ID")
            disposition = row.get("research_disposition")
            if disposition == "eligible":
                public.add(object_id)
            elif disposition == "held":
                held.add(object_id)
            else:
                unclassified += 1
    if (
        len(public) != contract.PUBLIC_OBJECT_COUNT
        or len(held) != contract.HELD_OBJECT_COUNT
        or public & held
        or unclassified
        or len(public | held) != contract.CANONICAL_OBJECT_COUNT
    ):
        raise VerificationError("eligibility ledger does not reconcile")
    return public, held


def _validate_output_safety(
    research_dir: Path,
    audit_dir: Path,
    *,
    public_ids: set[str],
    held_ids: set[str],
) -> None:
    artifact_paths = [research_dir / name for name in contract.RESEARCH_FILES]
    artifact_paths += [audit_dir / name for name in contract.AUDIT_DOCUMENT_FILES]
    artifact_paths += [audit_dir / "raw" / name for name in contract.RAW_FILES]
    for path in artifact_paths:
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VerificationError(f"scoped artifact is not UTF-8: {path.name}") from error
        if contract.UUID_RE.search(text) or contract.PRIVATE_ID_RE.search(text):
            raise VerificationError(f"private identifier appears in scoped artifact: {path.name}")
        discovered = set(PUBLIC_ID_TOKEN_RE.findall(text))
        if discovered & held_ids:
            raise VerificationError(f"held identity appears in scoped artifact: {path.name}")
        if discovered - public_ids:
            raise VerificationError(f"unknown SURF identity appears in scoped artifact: {path.name}")
        if path.suffix in {".tsv", ".json"}:
            try:
                contract.validate_output_urls(path.name, text)
            except contract.GenerationError as error:
                raise VerificationError(
                    f"ungoverned URL appears in sanitized TSV/raw evidence: {path.name}"
                ) from error


def _false_columns(tables: Mapping[str, Table]) -> bool:
    checked = 0
    for name in (
        "12_LEXICAL_BASELINE_RESULTS.tsv", "13_DENSE_MODEL_RESULTS.tsv",
        "14_CROSS_LANGUAGE_RESULTS.tsv", "15_METADATA_HOLDOUT_RESULTS.tsv",
        "16_SOURCE_LANGUAGE_LEAKAGE.tsv", "18_ROBUSTNESS_AND_ABLATION.tsv",
        "19_ASPECT_DISAGREEMENT.tsv", "20_STRUCTURED_NLP_DISAGREEMENT.tsv",
        "21_HYBRID_EXPERIMENTS.tsv", "22_NLP_REVIEW_PACKET.tsv",
    ):
        for row in tables[name].rows:
            for column in ("historical_relation", "semantic_relation", "probability"):
                checked += 1
                if _bool(row[column], f"{name}.{column}"):
                    return False
    return checked > 0


def _bounded_review_title(value: str) -> str:
    text = " ".join(str(value).split())
    if len(text) <= 180:
        return text
    prefix = text[:177].rsplit(" ", 1)[0]
    if not prefix:
        prefix = text[:177]
    return prefix.rstrip() + "..."


def _load_governed_review_titles(repo_root: Path) -> dict[str, str]:
    relative = "frontend/generated/trace-context-v1/records.json"
    path = repo_root / relative
    if (
        not path.is_file()
        or path.is_symlink()
        or _sha256_path(path) != FROZEN_INPUTS[relative]
    ):
        raise VerificationError("governed Context records differ from the frozen source")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationError("governed Context records are not strict UTF-8 JSON") from error
    payload = _mapping(value, "governed Context records")
    records = payload.get("records")
    if isinstance(records, (str, bytes, bytearray)) or not isinstance(records, Sequence):
        raise VerificationError("governed Context records are absent")
    titles: dict[str, str] = {}
    for index, record in enumerate(records):
        selected = _mapping(_mapping(record, f"Context record {index}").get("selectedRecord"), f"Context selected record {index}")
        object_id = str(selected.get("surfaceId", ""))
        title = selected.get("title")
        if (
            not contract.PUBLIC_ID_RE.fullmatch(object_id)
            or not isinstance(title, str)
            or not title.strip()
            or object_id in titles
        ):
            raise VerificationError("governed Context title map is malformed")
        titles[object_id] = _bounded_review_title(title)
    if len(titles) != contract.PUBLIC_OBJECT_COUNT:
        raise VerificationError("governed Context title map differs from the public cohort")
    return titles


def _validate_detailed_tables(
    tables: Mapping[str, Table],
    *,
    governed_review_titles: Mapping[str, str],
    declared_review_anchor_count: int,
) -> dict[str, Any]:
    fields = tables["03_NLP_TEXT_FIELD_REGISTRY.tsv"].rows
    field_ids = {row["field_id"] for row in fields}
    if len(field_ids) != len(fields):
        raise VerificationError("text field IDs are duplicated")
    for row in fields:
        if row["primary_role"] not in ALLOWED_ROLES or row["primary_role"] == "UNCLASSIFIED_UNSAFE":
            raise VerificationError("text field registry has an invalid/unclassified role")
        if row["governance_decision"] not in ALLOWED_GOVERNANCE_DECISIONS:
            raise VerificationError("text field registry has an invalid decision")
        _bool(row["public_safe"], "field public_safe")
        if row["rights_safe"].upper() not in {"TRUE", "FALSE", "REVIEW_REQUIRED"}:
            raise VerificationError("text field registry has an invalid rights-safe state")
        if row["primary_role"] in {"RIGHTS_TEXT", "PROVENANCE_TEXT", "BOILERPLATE"} and row["governance_decision"] in {
            "INCLUDE_TITLE_CHANNEL", "INCLUDE_SUBJECT_CHANNEL", "INCLUDE_OBJECT_DESCRIPTION_CHANNEL"
        }:
            raise VerificationError("rights/provenance/boilerplate entered object-semantic affinity")

    language = tables["05_LANGUAGE_AND_SCRIPT_CENSUS.tsv"].rows
    if any(_integer(row["object_count"], "script object count") > contract.PUBLIC_OBJECT_COUNT for row in language):
        raise VerificationError("script census exceeds public cohort")
    if any(_integer(row["generated_translation_count"], "generated translations") != 0 for row in language):
        raise VerificationError("generated translation entered script/language census")

    lengths = tables["06_TEXT_LENGTH_AND_TOKENIZATION.tsv"].rows
    for row in lengths:
        if _bool(row["corpus_text_overwritten"], "corpus text overwritten"):
            raise VerificationError("tokenization overwrote governed corpus text")
        if not _bool(row["full_normalized_hashes_preserved"], "normalized hashes preserved"):
            raise VerificationError("tokenization did not preserve full normalized hashes")
        if row["aspect_id"] in contract.MODEL_INPUT_TOKEN_CAPS:
            if _integer(row["governed_token_cap"], "governed token cap") != contract.MODEL_INPUT_TOKEN_CAPS[row["aspect_id"]]:
                raise VerificationError("token-length row has a stale governed cap")
        if row["truncation_direction"] not in {"HEAD", "N/A"}:
            raise VerificationError("token truncation direction is not declared HEAD")

    boilerplate = tables["08_NLP_BOILERPLATE_REGISTRY.tsv"].rows
    for row in boilerplate:
        if row["decision"] not in ALLOWED_BOILERPLATE_DECISIONS:
            raise VerificationError("boilerplate registry contains an invalid decision")
        if _integer(row["support"], "boilerplate support") > _integer(row["denominator"], "boilerplate denominator"):
            raise VerificationError("boilerplate support exceeds denominator")
        if not (row["phrase_or_hash"].startswith("sha256:") or row["decision"] == "KEEP_SEMANTIC"):
            raise VerificationError("committed boilerplate rule exposes an unhashed removable phrase")

    models = tables["10_MODEL_ARTIFACT_REGISTER.tsv"].rows
    if {row["candidate_id"] for row in models} != {"NLP-D1", "NLP-D2", "NLP-D3", "NLP-D4", "NLP-S1", "NLP-LID1"}:
        raise VerificationError("model artifact register candidate set changed")
    model_by_id = {row["candidate_id"]: row for row in models}
    for row in models:
        if not contract.REVISION_RE.fullmatch(row["revision"]) or not contract.REVISION_RE.fullmatch(row["tokenizer_revision"]):
            raise VerificationError("model/tokenizer revision is not immutable")
        if not row["license_spdx"] or row["eligibility"] not in {"PRODUCTION_ELIGIBLE", "RESEARCH_ONLY", "REJECT"}:
            raise VerificationError("model lacks a license/eligibility decision")
        if _bool(row["trust_remote_code_required"], "trust remote code") and not _bool(row["custom_code_reviewed"], "custom code reviewed") and "READY" in row["execution_state"]:
            raise VerificationError("unreviewed remote code is execution-ready")

    lexical = tables["12_LEXICAL_BASELINE_RESULTS.tsv"].rows
    completed_title_families = {
        row["method_family"]
        for row in lexical
        if row["aspect_id"] == "NLP_TITLE"
        and row["status"].upper() in {"PASS", "COMPLETED"}
    }
    if completed_title_families != {"BM25F", "CHAR_NGRAM", "WORD_NGRAM", "LEXICAL_HYBRID"}:
        raise VerificationError("all four lexical families require a completed full-title baseline")
    for row in lexical:
        if _integer(row["candidate_object_count"], "lexical candidates") != contract.PUBLIC_OBJECT_COUNT:
            raise VerificationError("lexical candidate corpus is not the full public cohort")
        query = _integer(row["query_count"], "lexical queries")
        available = _integer(row["aspect_available_query_count"], "lexical aspect queries")
        unavailable = _integer(row["aspect_unavailable_query_count"], "lexical unavailable")
        if query != available or available + unavailable != contract.PUBLIC_OBJECT_COUNT:
            raise VerificationError("lexical aspect-available query accounting differs")
        if _integer(row["top_k"], "lexical top-k") > 50:
            raise VerificationError("lexical top-k exceeds 50")
        if row["status"].upper() in {"PASS", "COMPLETED"} and (
            _bool(row["full_public_cohort"], "lexical full public cohort")
            != (available == contract.PUBLIC_OBJECT_COUNT)
            or not _bool(row["full_aspect_cohort"], "lexical full aspect cohort")
        ):
            raise VerificationError("completed lexical baseline does not cover its full governed cohort")

    dense = tables["13_DENSE_MODEL_RESULTS.tsv"].rows
    for row in dense:
        if row["model_id"] not in model_by_id:
            raise VerificationError("dense result references an unregistered model")
        model = model_by_id[row["model_id"]]
        if row["model_revision"] != model["revision"] or row["tokenizer_revision"] != model["tokenizer_revision"]:
            raise VerificationError("dense result revision differs from model registry")
        if _integer(row["candidate_object_count"], "dense candidates") != contract.PUBLIC_OBJECT_COUNT:
            raise VerificationError("dense candidate corpus is not the full public cohort")
        if row["status"] in {"PASS", "COMPLETED"}:
            query = _integer(row["query_count"], "dense queries")
            available = _integer(row["aspect_available_query_count"], "dense available")
            unavailable = _integer(row["aspect_unavailable_query_count"], "dense unavailable")
            if query != available or available + unavailable != contract.PUBLIC_OBJECT_COUNT:
                raise VerificationError("dense aspect-available query accounting differs")
            if (
                _bool(row["full_public_cohort"], "dense full public cohort")
                != (available == contract.PUBLIC_OBJECT_COUNT)
                or not _bool(row["full_aspect_cohort"], "dense full aspect cohort")
            ):
                raise VerificationError("completed dense result does not cover its full governed cohort")
        for column in (
            "trust_remote_code_executed", "model_weights_committed", "full_embedding_matrix_committed",
            "pair_matrix_materialized", "full_rankings_saved", "randomness_affects_embedding",
            "randomness_affects_neighbor_order",
        ):
            if _bool(row[column], f"dense {column}"):
                raise VerificationError(f"dense result violates boundary: {column}")

    cross = tables["14_CROSS_LANGUAGE_RESULTS.tsv"].rows
    for row in cross:
        if _integer(row["verified_pair_count"], "cross-language positives") != 0:
            raise VerificationError("Task B positive count changed without registry evidence")
        if _integer(row["model_created_positive_pair_count"], "model-created positives") != 0:
            raise VerificationError("model output created a positive pair")
        if _integer(row["generated_translation_count"], "generated translations") != 0:
            raise VerificationError("generated translation entered cross-language evaluation")
        if row["status"].upper() != "NOT_RUN":
            raise VerificationError("zero-positive Task B evaluation must remain NOT_RUN")

    metadata = tables["15_METADATA_HOLDOUT_RESULTS.tsv"].rows
    for row in metadata:
        if not _bool(row["proxy_only"], "metadata proxy-only"):
            raise VerificationError("metadata holdout was presented as ground truth")
        if row["mask_variant"] == "ORIGINAL_APPROVED_TEXT":
            if row["target_literal_count_before"] not in {"", "N/A", "NOT_RUN"} or row[
                "target_literal_count_after"
            ] not in {"", "N/A", "NOT_RUN"}:
                raise VerificationError("unmasked metadata control reports mask literal counts")
            if _bool(row["target_labels_masked"], "unmasked target mask") or _bool(
                row["context_labels_masked"], "unmasked context mask"
            ):
                raise VerificationError("unmasked metadata control claims label masking")
        else:
            if not _bool(row["target_labels_masked"], "metadata target mask"):
                raise VerificationError("metadata masked variant retained target labels")
            after = row["target_literal_count_after"]
            if _integer(row["target_literal_count_before"], "target literals before") < 0:
                raise VerificationError("metadata target literals before is negative")
            if _integer(after, "target literals after") != 0:
                raise VerificationError("target literals remain after masking")

    leakage = tables["16_SOURCE_LANGUAGE_LEAKAGE.tsv"].rows
    if {row["leakage_dimension"] for row in leakage} < {"SOURCE", "LANGUAGE"}:
        raise VerificationError("source/language leakage report is incomplete")
    if any(_bool(row["language_identity_used_as_positive_affinity"], "language positive affinity") for row in leakage):
        raise VerificationError("language identity became positive semantic affinity")
    for row in leakage:
        if row["status"].upper() in {"PASS", "COMPLETED"}:
            _number(row["metric_value"], "completed leakage metric_value")

    hubness = tables["17_HUBNESS_AND_ANISOTROPY.tsv"].rows
    completed_dense_groups = {
        (row["model_id"], row["input_variant"], row["aspect_id"])
        for row in dense
        if row["status"].upper() in {"PASS", "COMPLETED"}
    }
    completed_dense = {group[0] for group in completed_dense_groups}
    for group in completed_dense_groups:
        model_rows = [
            row for row in hubness
            if (row["model_id"], row["input_variant"], row["aspect_id"]) == group
        ]
        hub_ks = {row["k"] for row in model_rows if row["diagnostic_type"] == "HUBNESS"}
        if hub_ks != {"10", "20", "50"}:
            raise VerificationError(f"hubness k=10/20/50 incomplete for {group}")
        if sum(row["diagnostic_type"] == "ANISOTROPY" for row in model_rows) != 1:
            raise VerificationError(f"anisotropy report omitted/duplicated for {group}")
        overall_statuses = {row["overall_diagnostic_status"] for row in model_rows}
        association_receipts = {row["association_inputs_sha256"] for row in model_rows}
        missing_sets = {
            tuple(sorted(_json_string_set(row["missing_required_diagnostics"], "missing diagnostics")))
            for row in model_rows
        }
        if len(overall_statuses) != 1 or len(association_receipts) != 1 or len(missing_sets) != 1:
            raise VerificationError(f"hubness/anisotropy group receipts disagree: {group}")
        overall_status = next(iter(overall_statuses)).upper()
        missing = set(next(iter(missing_sets)))
        if overall_status == "PASS" and missing:
            raise VerificationError("completed hubness/anisotropy group declares missing diagnostics")
        if overall_status == "NOT_RUN" and not missing:
            raise VerificationError("NOT_RUN hubness/anisotropy group lacks missing diagnostics")
        if overall_status not in {"PASS", "NOT_RUN"}:
            raise VerificationError(f"unsupported overall hubness/anisotropy status: {overall_status}")
        for dimension in contract.REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS:
            association_rows = [
                row for row in model_rows
                if row["diagnostic_type"] == f"HUBNESS_ASSOCIATION_{dimension}"
            ]
            if {row["k"] for row in association_rows} != {"10", "20", "50"}:
                raise VerificationError(
                    f"hubness association {dimension} k=10/20/50 incomplete for {group}"
                )
        for row in model_rows:
            if row["diagnostic_type"] == "HUBNESS" and _integer(row["total_occurrence_count"], "hubness total") != _integer(row["expected_occurrence_count"], "hubness expected"):
                raise VerificationError("hubness occurrence accounting differs")
            if _bool(row["correction_selected"], "hubness correction selected"):
                raise VerificationError("hubness correction was selected")
            diagnostic_type = row["diagnostic_type"]
            status = row["status"].upper()
            if diagnostic_type == "ANISOTROPY":
                pre_norm_missing = row["pre_normalization_norm_p50"] in {"", "N/A", "NOT_RUN"} or row[
                    "pre_normalization_norm_p95"
                ] in {"", "N/A", "NOT_RUN"}
                if pre_norm_missing and status in {"PASS", "COMPLETED"}:
                    raise VerificationError("anisotropy passed without pre-normalization norm diagnostics")
            if diagnostic_type.startswith("HUBNESS_ASSOCIATION_"):
                dimension = diagnostic_type.removeprefix("HUBNESS_ASSOCIATION_")
                if dimension not in contract.REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS:
                    raise VerificationError(f"undeclared hubness association dimension: {dimension}")
                if row["association_dimension"] != dimension:
                    raise VerificationError("hubness association dimension field disagrees with its diagnostic type")
                if not contract.SHA256_RE.fullmatch(row["association_inputs_sha256"]):
                    raise VerificationError("hubness association input receipt is invalid")
                if status in {"PASS", "COMPLETED"}:
                    if row["association_type"] in {"", "N/A", "NOT_RUN"}:
                        raise VerificationError("completed hubness association lacks a method")
                    _number(row["association_value"], "hubness association value")
                    if not contract.SHA256_RE.fullmatch(row["association_observation_sha256"]):
                        raise VerificationError("hubness association observation receipt is invalid")
                elif status == "NOT_RUN":
                    if row["association_type"] != "NOT_RUN" or row["association_value"] not in {
                        "",
                        "N/A",
                        "NOT_RUN",
                    }:
                        raise VerificationError("NOT_RUN hubness association contains computed evidence")
                    if not row["limitation"] or row["limitation"] in {"N/A", "NOT_RUN"}:
                        raise VerificationError("NOT_RUN hubness association lacks a reason")
                else:
                    raise VerificationError(f"unsupported hubness association status: {status}")
            if status not in {"PASS", "COMPLETED"}:
                continue
            if diagnostic_type == "HUBNESS":
                for column in (
                    "mean_k_occurrence", "variance_k_occurrence", "skewness", "gini",
                    "top_1_percent_occurrence_share", "maximum_occurrence",
                    "zero_occurrence_object_count", "total_occurrence_count",
                    "expected_occurrence_count",
                ):
                    _number(row[column], f"completed hubness {column}")
            elif diagnostic_type == "ANISOTROPY":
                for column in (
                    "mean_sampled_cosine", "cosine_variance", "pair_observation_count",
                    "first_pc_variance_share", "norm_p50", "norm_p95",
                    "pre_normalization_norm_p50", "pre_normalization_norm_p95",
                    "nearest_neighbor_cosine_distance_p50",
                    "nearest_neighbor_cosine_distance_p95",
                    "exact_mean_off_diagonal_cosine",
                ):
                    _number(row[column], f"completed anisotropy {column}")

    robustness = tables["18_ROBUSTNESS_AND_ABLATION.tsv"].rows
    declared_ablation_ids = set(contract.DECLARED_ROBUSTNESS_ABLATION_IDS)
    grouped_robustness: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in robustness:
        grouped_robustness[(row["model_id"], row["reference_method_id"])].append(row)
    for group, rows in grouped_robustness.items():
        if {row["ablation_id"] for row in rows} != declared_ablation_ids:
            raise VerificationError(f"robustness ablation registry is incomplete for {group}")
    for row in robustness:
        for column in ("weights_selected", "prompt_optimized", "aspects_fused"):
            if _bool(row[column], f"robustness {column}"):
                raise VerificationError(f"robustness selected prohibited {column}")
        if row["robustness_suite_status"] != "STOPPED_RECOVERABLE_CHECKPOINT":
            raise VerificationError("robustness suite lost its stopped-checkpoint status")
        if row["reference_corpus_sha256"] != contract.CORPUS_SHA256:
            raise VerificationError("robustness row uses a stale ranking corpus")
        if _integer(row["declared_ablation_count"], "declared ablation count") != len(
            contract.DECLARED_ROBUSTNESS_ABLATION_IDS
        ):
            raise VerificationError("robustness row does not bind 17 declared ablations")
        for column in ("reference_index_sha256", "reference_ranking_ids_sha256", "suite_sha256"):
            if not contract.SHA256_RE.fullmatch(row[column]):
                raise VerificationError(f"robustness {column} is invalid")
        executed = _json_string_set(row["executed_ablation_ids"], "executed ablation IDs")
        not_run = _json_string_set(row["not_run_ablation_ids"], "not-run ablation IDs")
        if executed & not_run or executed | not_run != declared_ablation_ids:
            raise VerificationError("robustness executed/not-run partition is incomplete")
        status = row["status"].upper()
        if status in {"PASS", "COMPLETED"}:
            if row["ablation_id"] not in executed:
                raise VerificationError("completed robustness row is not in the executed partition")
            for column in (
                "mean_top_k_overlap", "median_top_k_overlap", "p05_top_k_overlap",
                "mean_rank_correlation", "median_rank_correlation",
                "p05_rank_correlation", "same_source_rate_change",
                "hubness_gini_change",
            ):
                _number(row[column], f"completed robustness {column}")
        elif status == "NOT_RUN":
            if row["ablation_id"] not in not_run:
                raise VerificationError("NOT_RUN robustness row is not in the not-run partition")
        else:
            raise VerificationError(f"unsupported robustness status: {status}")

    aspects = tables["19_ASPECT_DISAGREEMENT.tsv"].rows
    if any(_bool(row["affinity_fused"], "aspect affinity fused") or _bool(row["aspect_fusion_selected"], "aspect fusion") for row in aspects):
        raise VerificationError("aspect disagreement selected aspect fusion")
    for row in aspects:
        if row["status"].upper() in {"PASS", "COMPLETED"}:
            _number(row["language_neighbor_rate_a"], "completed aspect language rate A")
            _number(row["language_neighbor_rate_b"], "completed aspect language rate B")

    structured = tables["20_STRUCTURED_NLP_DISAGREEMENT.tsv"].rows
    for row in structured:
        if row["candidate_index_sha256"] != contract.ROUND6_CANDIDATE_INDEX_SHA256:
            raise VerificationError("structured disagreement uses a stale Round 6 candidate index")
        if _bool(row["structured_nlp_fusion_selected"], "structured fusion") or _bool(row["structured_nlp_fusion_weights_selected"], "structured fusion weights"):
            raise VerificationError("structured/NLP fusion was selected")
        if row["status"].upper() in {"PASS", "COMPLETED"}:
            raise VerificationError(
                "structured/NLP comparison cannot claim completion without reliable-language diagnostics"
            )

    hybrid = tables["21_HYBRID_EXPERIMENTS.tsv"].rows
    for row in hybrid:
        for column in ("weights_selected", "production_selected", "hybrid_selected", "fusion_weights_selected"):
            if _bool(row[column], f"hybrid {column}"):
                raise VerificationError("hybrid experiment selected production/fusion weights")

    review = tables["22_NLP_REVIEW_PACKET.tsv"].rows
    if len(review) > contract.MAX_REVIEW_ROWS:
        raise VerificationError("review packet exceeds row bound")
    distinct_review_anchors = {row["anchor_public_object_id"] for row in review}
    if declared_review_anchor_count != len(distinct_review_anchors):
        raise VerificationError(
            "review anchorCount differs from the distinct committed anchors"
        )
    if not 24 <= declared_review_anchor_count <= 36:
        raise VerificationError("review packet must contain 24..36 distinct anchors")
    for row in review:
        if row["anchor_public_object_id"] == row["candidate_public_object_id"]:
            raise VerificationError("review packet contains a self-neighbor")
        if row["expert_judgment"] != "PENDING_LATER_REVIEW":
            raise VerificationError("Round 1 review packet synthesizes expert judgment")
        for id_column, title_column in (
            ("anchor_public_object_id", "anchor_title"),
            ("candidate_public_object_id", "candidate_title"),
        ):
            object_id = row[id_column]
            expected_title = governed_review_titles.get(object_id)
            if expected_title is None or row[title_column] != expected_title:
                raise VerificationError(
                    f"review title is not bound to the governed public corpus: {object_id}"
                )

    if not _false_columns(tables):
        raise VerificationError("a result row asserts relation/probability")
    return {
        "fieldIds": field_ids,
        "modelById": model_by_id,
        "completedDenseModels": completed_dense,
        "reviewRowCount": len(review),
    }


def _validate_runs(raw: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    payload = _mapping(raw["run-performance-security-summary.json"]["payload"], "run payload")
    runs = _mapping(payload.get("runs"), "runs")
    rows = runs.get("rows")
    if isinstance(rows, (str, bytes, bytearray)) or not isinstance(rows, Sequence) or not rows:
        raise VerificationError("run register is absent or empty")
    if len(rows) > contract.MAX_RUN_ROWS:
        raise VerificationError("run register exceeds bounded receipt count")
    result = tuple(_mapping(row, "run row") for row in rows)
    ids: set[str] = set()
    for row in result:
        run_id = str(row.get("runId", ""))
        if not run_id or run_id in ids:
            raise VerificationError("run IDs are blank or duplicated")
        ids.add(run_id)
        if row.get("sourceCommit") != contract.SOURCE_COMMIT:
            raise VerificationError("run receipt uses a stale source commit")
        if row.get("corpusPolicySha256") != contract.CORPUS_POLICY_SHA256:
            raise VerificationError("run receipt uses a stale corpus policy")
        if row.get("fieldRegistrySha256") != contract.FIELD_REGISTRY_SHA256:
            raise VerificationError("run receipt uses a stale field registry")
        expected_corpus_identity = {
            "encodedDocumentReceiptSha256": contract.DOCUMENT_RECEIPT_SHA256,
            "rankingCorpusSha256": contract.CORPUS_SHA256,
            "tokenCountReceiptSha256": contract.TOKEN_COUNT_RECEIPT_SHA256,
            "tokenCountMethod": contract.TOKEN_COUNT_METHOD,
        }
        for key, expected in expected_corpus_identity.items():
            if row.get(key) != expected:
                raise VerificationError(f"run receipt uses a stale corpus identity: {key}")
        if _bool(
            row.get("corpusIdentityContractsConflated"),
            f"run {run_id} corpusIdentityContractsConflated",
        ):
            raise VerificationError("run receipt conflates document/ranking/token-count identities")
        for key in (
            "randomnessAffectsCorpus", "randomnessAffectsEmbedding",
            "randomnessAffectsNeighborOrder", "randomnessAffectsScore",
            "modelWeightsCommitted", "fullEmbeddingMatrixCommitted", "fullRankingsCommitted",
        ):
            value = row.get(key)
            if value is not None and _bool(value, f"run {run_id} {key}"):
                raise VerificationError(f"run receipt violates {key}")
    return result


def _validate_performance(components: Mapping[str, Mapping[str, Any]]) -> None:
    performance = components["performance"]
    required = (
        "lexicalIndexBuildMs", "denseCorpusEncodingMs", "denseDocumentsPerSecond",
        "denseIndexBytes", "denseExactQueryP50Ms", "denseExactQueryP95Ms",
        "nlpPeakRamBytes", "nlpPeakVramBytes",
    )
    for key in required:
        value = performance.get(key)
        if value in (None, "", "N/A", "NOT_RUN"):
            if key == "lexicalIndexBuildMs" or key == "nlpPeakRamBytes":
                raise VerificationError(f"required performance receipt absent: {key}")
            continue
        if _number(value, f"performance.{key}") < 0:
            raise VerificationError(f"performance receipt is negative: {key}")


def _invariant_checks(
    tables: Mapping[str, Table],
    components: Mapping[str, Mapping[str, Any]],
    runs: Sequence[Mapping[str, Any]],
    *,
    no_private_or_held: bool,
    protected_scope: bool,
) -> dict[str, tuple[bool, str]]:
    boundary = components["boundary"]
    governance = components["governance"]
    security = components["security"]
    decision = components["decision"]
    fields = tables["03_NLP_TEXT_FIELD_REGISTRY.tsv"].rows
    pairs = tables["11_EVALUATION_PAIR_REGISTRY.tsv"].rows
    positives = [row for row in pairs if row["pair_class"] == "KNOWN_REPRESENTATION_POSITIVE"]
    metadata = tables["15_METADATA_HOLDOUT_RESULTS.tsv"].rows
    leakage = tables["16_SOURCE_LANGUAGE_LEAKAGE.tsv"].rows
    models = tables["10_MODEL_ARTIFACT_REGISTER.tsv"].rows
    dense = tables["13_DENSE_MODEL_RESULTS.tsv"].rows
    aspects = tables["19_ASPECT_DISAGREEMENT.tsv"].rows
    structured = tables["20_STRUCTURED_NLP_DISAGREEMENT.tsv"].rows
    review = tables["22_NLP_REVIEW_PACKET.tsv"].rows
    rights_safe = all(
        row["primary_role"] not in {"RIGHTS_TEXT", "PROVENANCE_TEXT", "BOILERPLATE"}
        or row["governance_decision"] not in {"INCLUDE_TITLE_CHANNEL", "INCLUDE_SUBJECT_CHANNEL", "INCLUDE_OBJECT_DESCRIPTION_CHANNEL"}
        for row in fields
    )
    checks = {
        "NLP-INV-001": (
            _integer(boundary["publicObjectCount"], "public count") == contract.PUBLIC_OBJECT_COUNT
            and all(_integer(row["candidate_object_count"], "candidate count") == contract.PUBLIC_OBJECT_COUNT for row in (*tables["12_LEXICAL_BASELINE_RESULTS.tsv"].rows, *dense)),
            "boundary and every retrieval candidate corpus reconcile to 7,995 public objects",
        ),
        "NLP-INV-002": (
            _integer(boundary["nlpHeldObjectsIncluded"], "held included") == 0 and no_private_or_held,
            "central boundary and artifact scan report zero held objects/text",
        ),
        "NLP-INV-003": (
            all(row["primary_role"] in ALLOWED_ROLES and row["governance_decision"] in ALLOWED_GOVERNANCE_DECISIONS for row in fields),
            "every field row has one governed role and decision",
        ),
        "NLP-INV-004": (
            not _bool(governance["sourceNarrativeMergedWithObjectSemantic"], "source narrative merge")
            and list(governance["objectSemanticCompositeSourceRoles"]) == ["OBJECT_TITLE"],
            "source narrative is isolated and the v1 composite remains title-only",
        ),
        "NLP-INV-005": (rights_safe, "rights/provenance/boilerplate fields are excluded from object-semantic affinity"),
        "NLP-INV-006": (
            not _bool(governance["originalSourceTextOverwritten"], "source overwrite")
            and all(not _bool(row["corpus_text_overwritten"], "tokenization overwrite") for row in tables["06_TEXT_LENGTH_AND_TOKENIZATION.tsv"].rows),
            "source and normalized corpus text remain immutable",
        ),
        "NLP-INV-007": (
            not _bool(governance["machineTranslationUsed"], "machine translation")
            and not _bool(governance["generatedSummaryUsed"], "generated summary")
            and all(_integer(row["generated_translation_count"], "translations") == 0 for row in tables["14_CROSS_LANGUAGE_RESULTS.tsv"].rows),
            "no generated translation or summary enters the corpus/evaluation",
        ),
        "NLP-INV-008": (
            any(row["control_type"] == "SAME_TITLE_DIFFERENT_ID" and row["pair_class"] == "DIAGNOSTIC_NEGATIVE_CONTROL" for row in pairs),
            "same-title distinct identities remain negative leakage controls",
        ),
        "NLP-INV-009": (
            len(positives) == 3 and all(row["verification_source"] and contract.SHA256_RE.fullmatch(row["verification_artifact_sha256"]) for row in positives),
            "all three Task A importer-representation positives are externally SHA-pinned",
        ),
        "NLP-INV-010": (
            all(_bool(row["target_labels_masked"], "target labels masked") for row in metadata if row["mask_variant"] != "ORIGINAL_APPROVED_TEXT"),
            "every masked metadata-proxy variant declares target-label masking",
        ),
        "NLP-INV-011": (any(row["leakage_dimension"] == "SOURCE" for row in leakage), "source identity has an explicit leakage diagnostic"),
        "NLP-INV-012": (
            any(row["leakage_dimension"] == "LANGUAGE" for row in leakage)
            and all(not _bool(row["language_identity_used_as_positive_affinity"], "language affinity") for row in leakage),
            "language is measured but never used as semantic truth",
        ),
        "NLP-INV-013": (
            all(contract.REVISION_RE.fullmatch(row["revision"]) and contract.REVISION_RE.fullmatch(row["tokenizer_revision"]) for row in models if row["channel"] in {"DENSE", "SPARSE"}),
            "dense/sparse model and tokenizer revisions are immutable pins",
        ),
        "NLP-INV-014": (
            all(row["license_spdx"] and row["eligibility"] in {"PRODUCTION_ELIGIBLE", "RESEARCH_ONLY", "REJECT"} for row in models),
            "every model row records license and eligibility",
        ),
        "NLP-INV-015": (
            not _bool(security["unreviewedRemoteCodeExecuted"], "remote code")
            and all(not _bool(row["trust_remote_code_required"], "remote required") or _bool(row["custom_code_reviewed"], "custom reviewed") or "READY" not in row["execution_state"] for row in models),
            "no unreviewed remote code is executable/executed",
        ),
        "NLP-INV-016": (
            _integer(security["modelWeightFilesCommitted"], "weights committed") == 0
            and all(not _bool(row["model_weights_committed"], "dense weights") for row in dense),
            "no model weight enters committed scope",
        ),
        "NLP-INV-017": (
            not _bool(security["fullEmbeddingMatrixCommitted"], "embedding matrix")
            and all(not _bool(row["full_embedding_matrix_committed"], "dense matrix") for row in dense),
            "no full embedding matrix enters committed scope",
        ),
        "NLP-INV-018": (
            not any(_bool(row["aspect_fusion_selected"], "aspect fusion") for row in aspects)
            and bool({row["aspect_a"] for row in aspects} | {row["aspect_b"] for row in aspects}),
            "aspects remain separately named/evaluable and unfused",
        ),
        "NLP-INV-019": (_false_columns(tables), "all result/review rows set historical_relation=false"),
        "NLP-INV-020": (_false_columns(tables), "all result/review rows set probability=false"),
        "NLP-INV-021": (not _bool(security["cgCur4Changed"], "CG-CUR-4 changed") and protected_scope, "CG-CUR-4 remains outside changed scope"),
        "NLP-INV-022": (
            all(not _bool(security[key], key) for key in ("m2SpecificationChanged", "m5SpecificationChanged", "m7SpecificationChanged")) and protected_scope,
            "M2/M5/M7 specifications remain outside changed scope",
        ),
        "NLP-INV-023": (
            not _bool(decision["structuredNlpFusionSelected"], "fusion")
            and not _bool(decision["structuredNlpFusionWeightsSelected"], "fusion weights")
            and all(not _bool(row["structured_nlp_fusion_selected"], "structured row fusion") for row in structured),
            "structured and NLP evidence remain independent channels",
        ),
        "NLP-INV-024": (
            all(not _bool(security[key], key) for key in ("randomnessAffectsCorpus", "randomnessAffectsEmbedding", "randomnessAffectsNeighborOrder", "randomnessAffectsScore"))
            and all(not any(_bool(row.get(key, False), f"run {key}") for key in ("randomnessAffectsCorpus", "randomnessAffectsEmbedding", "randomnessAffectsNeighborOrder", "randomnessAffectsScore")) for row in runs),
            "security and run receipts declare seedless deterministic corpus/embedding/neighbors/scores",
        ),
        "NLP-INV-025": (
            bool(review) and all(contract.PUBLIC_ID_RE.fullmatch(row["anchor_public_object_id"]) and contract.PUBLIC_ID_RE.fullmatch(row["candidate_public_object_id"]) and len(row["anchor_title"]) <= 180 and len(row["candidate_title"]) <= 180 for row in review) and no_private_or_held,
            "bounded review rows contain only public IDs and sanitized title snippets",
        ),
        "NLP-INV-026": (
            bool(tables["16_SOURCE_LANGUAGE_LEAKAGE.tsv"].rows)
            and bool(tables["17_HUBNESS_AND_ANISOTROPY.tsv"].rows)
            and _bool(decision["sourceLeakageAndHubnessConsidered"], "decision diagnostics"),
            "shortlist decision explicitly consumes nonempty leakage and hubness reports",
        ),
    }
    return checks


def _git_lines(repo_root: Path, args: Sequence[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=repo_root, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise VerificationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line]


def _validate_changed_scope(repo_root: Path, *, fixture: bool) -> tuple[str, ...]:
    if fixture:
        return ()
    _git_lines(repo_root, ["cat-file", "-e", f"{contract.SOURCE_COMMIT}^{{commit}}"])
    changed = set(_git_lines(repo_root, ["diff", "--name-only", contract.SOURCE_COMMIT, "--"]))
    changed.update(_git_lines(repo_root, ["ls-files", "--others", "--exclude-standard"]))
    allowed_research = f"docs/research/trace-v49-exploration-nlp-round1/"
    allowed_audit = f"docs/audits/v49-exploration-nlp-round1/"
    allowed_scripts = "scripts/exploration-v49-nlp/"
    invalid = []
    for relative in sorted(changed):
        path = Path(relative)
        allowed = (
            relative == "PROJECT_LOG.md"
            or (relative.startswith(allowed_research) and path.name in contract.RESEARCH_FILES)
            or (
                relative.startswith(allowed_audit)
                and (
                    path.name in {*contract.AUDIT_DOCUMENT_FILES, "MANIFEST.tsv", "SHA256SUMS.txt", *contract.RAW_FILES}
                )
            )
            or (relative.startswith(allowed_scripts) and path.parent.as_posix() == allowed_scripts.rstrip("/") and path.suffix == ".py")
        )
        if not allowed:
            invalid.append(relative)
        if path.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES or "__pycache__" in path.parts:
            invalid.append(relative)
    if invalid:
        raise VerificationError(f"changed-file boundary violation: {sorted(set(invalid))}")
    if "PROJECT_LOG.md" not in changed:
        raise VerificationError("Round 7 did not update PROJECT_LOG.md")
    project_log = (repo_root / "PROJECT_LOG.md").read_text(encoding="utf-8")
    expected_receipts = {
        "CONTEXT_STATUS": "FROZEN",
        "SPACETIME_STATUS": "FROZEN",
        "EXPLORATION_STRUCTURED_CANDIDATE_RETRIEVAL": "CG-CUR-4",
        "EXPLORATION_STRUCTURED_MODEL_SHORTLIST": "M2,M5,M7",
        "EXPLORATION_NLP_CORPUS_AUDIT": "COMPLETE",
        "EXPLORATION_NLP_BASELINES": "COMPLETE_WITH_LIMITATIONS",
        "EXPLORATION_NLP_MODEL_DECISION": "NLP_CORPUS_AUDIT_ONLY",
        "EXPLORATION_NLP_REGRESSION": "PASS",
        "EXPLORATION_STRUCTURED_NLP_FUSION": "NOT_SELECTED",
        "EXPLORATION_PUBLIC_MODEL": "NOT_SELECTED",
        "EXPLORATION_RENDERER": "NOT_IMPLEMENTED",
        "PROJECT_LOG_UPDATED": "true",
    }
    observed_receipts: dict[str, list[str]] = defaultdict(list)
    for line in project_log.splitlines():
        match = re.fullmatch(r"([A-Z][A-Z0-9_]*)=([^\s=]+)", line)
        if match and match.group(1) in expected_receipts:
            observed_receipts[match.group(1)].append(match.group(2))
    for key, expected in expected_receipts.items():
        values = observed_receipts.get(key, [])
        if values != [expected]:
            raise VerificationError(
                f"PROJECT_LOG.md requires exactly one {key}={expected}; observed {values}"
            )
    diff_check = subprocess.run(
        ["git", "diff", "--check", contract.SOURCE_COMMIT, "--"], cwd=repo_root,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if diff_check.returncode:
        raise VerificationError(f"git diff --check failed: {diff_check.stdout.strip()}")
    return tuple(sorted(changed))


def verify(
    *,
    research_dir: Path,
    audit_dir: Path,
    repo_root: Path = ROOT,
    fixture: bool = False,
    public_ids: set[str] | None = None,
    held_ids: set[str] | None = None,
) -> dict[str, Any]:
    if research_dir.is_symlink() or audit_dir.is_symlink() or repo_root.is_symlink():
        raise VerificationError("verification roots cannot be symlinks")
    research_dir = research_dir.resolve()
    audit_dir = audit_dir.resolve()
    repo_root = repo_root.resolve()
    _validate_exact_inventory(research_dir, audit_dir)
    raw = _load_raw(audit_dir)
    tables = _load_tables(research_dir)
    _validate_table_receipts(tables, raw)
    _validate_audit_ledgers(audit_dir)
    _validate_research_receipts(research_dir, raw)
    _validate_package_text(research_dir, audit_dir)
    components = _central_components(raw)
    _validate_frozen_inputs(repo_root, components, fixture=fixture)
    if fixture:
        governed_review_titles = {
            row[column.replace("title", "public_object_id")]: row[column]
            for row in tables["22_NLP_REVIEW_PACKET.tsv"].rows
            for column in ("anchor_title", "candidate_title")
        }
    else:
        governed_review_titles = _load_governed_review_titles(repo_root)
    table_context = _validate_detailed_tables(
        tables,
        governed_review_titles=governed_review_titles,
        declared_review_anchor_count=_integer(
            _mapping(components["review"], "review").get("anchorCount"),
            "review.anchorCount",
        ),
    )
    runs = _validate_runs(raw)
    _validate_performance(components)
    if public_ids is None or held_ids is None:
        public_ids, held_ids = _load_public_held_ids(repo_root)
    _validate_output_safety(
        research_dir, audit_dir, public_ids=public_ids, held_ids=held_ids
    )
    changed = _validate_changed_scope(repo_root, fixture=fixture)
    checks = _invariant_checks(
        tables,
        components,
        runs,
        no_private_or_held=True,
        protected_scope=True,
    )
    if set(checks) != set(contract.INVARIANT_TEXT):
        raise VerificationError("independent invariant inventory differs from NLP-INV-001..026")
    failures = [identifier for identifier, (passed, _evidence) in checks.items() if not passed]
    if failures:
        raise VerificationError(f"required NLP invariants failed: {failures}")
    declared = components["invariants"]
    for identifier in sorted(contract.INVARIANT_TEXT):
        receipt = _mapping(declared[identifier], f"declared {identifier}")
        if str(receipt.get("status", "")).upper() != "PASS":
            raise VerificationError(f"central summary does not declare PASS for {identifier}")
    invariant_rows = [
        {
            "invariantId": identifier,
            "requirement": contract.INVARIANT_TEXT[identifier],
            "status": "PASS",
            "evidence": checks[identifier][1],
        }
        for identifier in sorted(contract.INVARIANT_TEXT)
    ]
    evidence_material = {
        "research": {name: _sha256((research_dir / name).read_bytes()) for name in contract.RESEARCH_FILES},
        "audit": {
            **{name: _sha256((audit_dir / name).read_bytes()) for name in (*contract.AUDIT_DOCUMENT_FILES, "MANIFEST.tsv", "SHA256SUMS.txt")},
            **{f"raw/{name}": _sha256((audit_dir / "raw" / name).read_bytes()) for name in contract.RAW_FILES},
        },
        "invariants": [row["invariantId"] for row in invariant_rows],
    }
    return {
        "schemaVersion": VERIFICATION_SCHEMA_VERSION,
        "status": "PASS",
        "checkCount": 13,
        "checks": [
            "EXACT_RESEARCH_AUDIT_INVENTORIES", "CANONICAL_TSV_SCHEMAS",
            "BOUNDED_RAW_JSON", "AUDIT_MANIFEST_AND_SHA256SUMS",
            "RESEARCH_FILE_RECEIPTS", "FROZEN_INPUTS_AND_GOVERNANCE_PINS",
            "PUBLIC_HELD_SAFETY", "MODEL_LICENSE_AND_REMOTE_CODE",
            "BOUNDED_TOP_K_AND_NO_MODEL_ARTIFACTS", "RUN_AND_PERFORMANCE_RECEIPTS",
            "PROTECTED_CHANGED_FILE_SCOPE", "PROJECT_LOG_ROUND7_RECEIPT",
            "NLP_INVARIANTS",
        ],
        "invariantCount": len(invariant_rows),
        "invariants": invariant_rows,
        "researchFileCount": len(contract.RESEARCH_FILES),
        "researchTsvCount": len(contract.RESEARCH_TSV_FILES),
        "auditDocumentCount": len(contract.AUDIT_DOCUMENT_FILES),
        "auditRawFileCount": len(contract.RAW_FILES),
        "publicObjectCount": contract.PUBLIC_OBJECT_COUNT,
        "heldObjectsIncluded": 0,
        "completedDenseModelIds": sorted(table_context["completedDenseModels"]),
        "reviewRowCount": table_context["reviewRowCount"],
        "changedFileCount": len(changed),
        "verificationEvidenceSha256": contract.sha256_json(evidence_material),
    }


def _write_ledgers(audit_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for name in contract.AUDIT_DOCUMENT_FILES:
        payload = (audit_dir / name).read_bytes()
        rows.append({"path": name, "bytes": len(payload), "sha256": _sha256(payload), "role": "AUDIT_NARRATIVE"})
    for name in contract.RAW_FILES:
        payload = (audit_dir / "raw" / name).read_bytes()
        rows.append({"path": f"raw/{name}", "bytes": len(payload), "sha256": _sha256(payload), "role": "BOUNDED_RAW_EVIDENCE"})
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=MANIFEST_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest = output.getvalue().encode("utf-8")
    (audit_dir / "MANIFEST.tsv").write_bytes(manifest)
    lines = [*(f"{row['sha256']}  {row['path']}" for row in rows), f"{_sha256(manifest)}  MANIFEST.tsv"]
    (audit_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _fixture_public_ids(tables: Mapping[str, Sequence[Mapping[str, Any]]]) -> tuple[set[str], set[str]]:
    public: set[str] = set()
    for rows in tables.values():
        for row in rows:
            for value in row.values():
                if isinstance(value, str) and contract.PUBLIC_ID_RE.fullmatch(value):
                    public.add(value)
    index = 0
    while len(public) < contract.PUBLIC_OBJECT_COUNT:
        public.add(f"SURF-FIXTURE-PUBLIC-{index:05d}")
        index += 1
    held = {f"SURF-FIXTURE-HELD-{index:05d}" for index in range(contract.HELD_OBJECT_COUNT)}
    return public, held


def self_test() -> dict[str, Any]:
    shared_contract_receipt = contract.self_test()
    if (
        shared_contract_receipt.get("status") != "PASS"
        or shared_contract_receipt.get("adversaryCount") != 37
    ):
        raise AssertionError("shared generator/verification semantics self-test drifted")
    summary = contract._fixture_summary()
    with tempfile.TemporaryDirectory(prefix="trace-nlp-round1-verifier-") as directory:
        root = Path(directory)
        research = root / "docs/research/trace-v49-exploration-nlp-round1"
        audit = root / "docs/audits/v49-exploration-nlp-round1"
        raw_dir = audit / "raw"
        research.mkdir(parents=True)
        raw_dir.mkdir(parents=True)
        for name in contract.RESEARCH_FILES:
            if name.endswith(".md"):
                decision_receipt = ""
                if name in {"00_EXECUTIVE_DECISION.md", "27_ROUND_DECISION.md"}:
                    decision_receipt = "\nPHASE_STATUS=STOPPED_RECOVERABLE_CHECKPOINT\nNLP_MODEL_DECISION=NLP_CORPUS_AUDIT_ONLY\nDENSE_MODEL_SHORTLIST_COUNT=0\nDENSE_MODEL_SHORTLIST_IDS=NONE\nPUBLIC_NLP_MODEL_SELECTED=false\nSTRUCTURED_NLP_FUSION_SELECTED=false\n"
                (research / name).write_text(f"# {name}\n\nResearch-only NLP evidence.\n{decision_receipt}", encoding="utf-8", newline="\n")
        for name in contract.AUDIT_DOCUMENT_FILES:
            invariant_text = "\n".join(f"{identifier}=PASS" for identifier in contract.INVARIANT_TEXT) if name == "00_EXECUTIVE_RECEIPT.md" else ""
            decision_receipt = ""
            if name == "00_EXECUTIVE_RECEIPT.md":
                decision_receipt = "\nPHASE_STATUS=STOPPED_RECOVERABLE_CHECKPOINT\nNLP_MODEL_DECISION=NLP_CORPUS_AUDIT_ONLY\nDENSE_MODEL_SHORTLIST_COUNT=0\nDENSE_MODEL_SHORTLIST_IDS=NONE\nPUBLIC_NLP_MODEL_SELECTED=false\nSTRUCTURED_NLP_FUSION_SELECTED=false\n"
            (audit / name).write_text(f"# {name}\n\n{invariant_text}\n{decision_receipt}", encoding="utf-8", newline="\n")
        research_payloads, raw_payloads, _receipt = contract.build_output_files(
            summary, research_dir_for_receipts=research
        )
        contract.write_outputs(research, raw_dir, research_payloads, raw_payloads)
        _write_ledgers(audit)
        derived = contract.derive_tables(summary)
        public_ids, held_ids = _fixture_public_ids(derived)
        first = verify(
            research_dir=research,
            audit_dir=audit,
            repo_root=root,
            fixture=True,
            public_ids=public_ids,
            held_ids=held_ids,
        )
        second = verify(
            research_dir=research,
            audit_dir=audit,
            repo_root=root,
            fixture=True,
            public_ids=public_ids,
            held_ids=held_ids,
        )
        if first != second:
            raise AssertionError("verifier replay was not deterministic")

        raw_target_name = "dense-cross-language-summary.json"
        raw_target = raw_dir / raw_target_name
        raw_wrapper = json.loads(raw_target.read_text(encoding="utf-8"))
        raw_wrapper["payload"]["data"] = [
            {"values": [0.1] * 64} for _ in range(6)
        ]
        raw_wrapper["payloadSha256"] = contract.sha256_json(raw_wrapper["payload"])
        raw_target.write_bytes(contract.canonical_json_bytes(raw_wrapper, pretty=True))
        _write_ledgers(audit)
        numeric_alias_rejected = False
        try:
            verify(
                research_dir=research,
                audit_dir=audit,
                repo_root=root,
                fixture=True,
                public_ids=public_ids,
                held_ids=held_ids,
            )
        except VerificationError:
            numeric_alias_rejected = True
        if not numeric_alias_rejected:
            raise AssertionError("chunked numeric embedding alias was accepted")
        raw_target.write_bytes(raw_payloads[raw_target_name])
        _write_ledgers(audit)

        target = research / "12_LEXICAL_BASELINE_RESULTS.tsv"
        target.write_bytes(target.read_bytes().replace(b"NLP-L0", b"NLP-X0", 1))
        rejected = False
        try:
            verify(
                research_dir=research,
                audit_dir=audit,
                repo_root=root,
                fixture=True,
                public_ids=public_ids,
                held_ids=held_ids,
            )
        except VerificationError:
            rejected = True
        if not rejected:
            raise AssertionError("mutated TSV was accepted")
    return {
        "schemaVersion": "trace-nlp-round1-verification-self-test/v1",
        "status": "PASS",
        "checkCount": 13,
        "adversaryCount": 39,
        "sharedContractAdversaryCount": 37,
        "verifierAdversaryCount": 2,
        "invariantCount": len(contract.INVARIANT_TEXT),
        "researchFileCount": len(contract.RESEARCH_FILES),
        "researchTsvCount": len(contract.RESEARCH_TSV_FILES),
        "auditDocumentCount": len(contract.AUDIT_DOCUMENT_FILES),
        "auditRawFileCount": len(contract.RAW_FILES),
        "deterministicReplay": True,
        "mutationRejected": True,
        "numericAliasRejected": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", type=Path, default=DEFAULT_RESEARCH_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = self_test() if args.self_test else verify(
        research_dir=args.research_dir,
        audit_dir=args.audit_dir,
        repo_root=args.repo_root,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
