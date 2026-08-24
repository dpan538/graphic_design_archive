#!/usr/bin/env python3
"""Fail-closed verifier for TRACE v49 Exploration affinity research Round 1.

Normal verification is read-only.  It validates the sealed research and audit
packages, cross-checks their aggregate evidence, and independently enforces the
24 EXP-SIM invariants.  ``--self-test`` writes only to a temporary directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import statistics
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
DEFAULT_RESEARCH_DIR = ROOT / "docs/research/trace-v49-exploration-similarity-round1"
DEFAULT_AUDIT_RAW_DIR = ROOT / "docs/audits/v49-exploration-similarity-round1/raw"

SOURCE_SHA = "0e311f0b88b4adc3cbfe2080ac98d622013cc6d3"
RESEARCH_RELEASE_ID = "v49-api-contract-fresh-c"
RESEARCH_RELEASE_SHA256 = "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a"
CONTEXT_PROJECTION_ID = "trace-context-v1"
CONTEXT_PROJECTION_SHA256 = "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
SPACETIME_PROJECTION_ID = "trace-spacetime-v1"
SPACETIME_PROJECTION_SHA256 = "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
EXPLORATION_SIGNAL_REGISTRY_SHA256 = "224aaea1123ad9d5730006aa5e779c17b4673fdfc9ee87988f3f96ac8ce26424"
PUBLIC_OBJECT_COUNT = 7_995
OTHER_PUBLIC_OBJECT_COUNT = 7_994
EXHAUSTIVE_PAIR_COUNT = 31_956_015
SIGNAL_COUNT = 64
HUMAN_REVIEW_ANCHOR_COUNT = 72

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_ID_RE = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
PUBLIC_ID_TOKEN_RE = re.compile(
    r"(?<![A-Z0-9-])SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*(?![A-Z0-9-])"
)
MODEL_ID_TOKEN_RE = re.compile(r"(?<![A-Z0-9])M[0-8](?![A-Z0-9])")
INTERACTION_ID_RE = re.compile(r"^EXP:INTERACTION:[0-9a-f]{64}$")
UUID_RE = re.compile(
    r"(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])",
    re.IGNORECASE,
)
PRIVATE_ID_RE = re.compile(
    r"(?:\bFOL-[A-Z0-9_-]+|\bTRN-OBJ-[A-Z0-9_-]+|\bTRTREE[A-Z0-9_-]*|"
    r"\bTRBRANCH[A-Z0-9_-]*)",
    re.IGNORECASE,
)
EXPLANATION_PRIVATE_RE = re.compile(
    r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH|https?://|file://)",
    re.IGNORECASE,
)

MODEL_BASELINE_SCHEMA_VERSION = "trace-exploration-model-baselines/v1"
COMPILED_CONTEXT_SCHEMA_VERSION = "trace-exploration-compiled-feature-context/v1"
EXPLANATION_SCHEMA_VERSION = "trace-exploration-candidate-explanation/v1"
MODEL_CONTEXT_DIGEST_FIELDS = (
    "scoringRecordsSha256",
    "modelContextSha256",
    "compiledFeatureContextSha256",
)
RESIDUAL_INTERACTION_METHODS = frozenset(
    {
        "NO_INTERACTION_CONTRIBUTION",
        "CAPPED_INTERACTION_BONUS",
        "INFORMATION_RESIDUAL_CONTRIBUTION",
        "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
    }
)

RESEARCH_FILES = (
    "00_EXECUTIVE_DECISION.md",
    "01_EXPLORATION_TASK_DEFINITIONS.md",
    "02_SIMILARITY_LITERATURE_AND_APPLICABILITY.md",
    "03_SIGNAL_LINEAGE_REGISTRY.tsv",
    "04_INDEPENDENT_SIGNAL_BASIS.md",
    "05_EVALUATION_PROTOCOL.md",
    "06_CANDIDATE_GENERATION_ARCHITECTURE.md",
    "07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv",
    "08_MISSINGNESS_AND_COMPARABILITY.md",
    "09_MODEL_SPECIFICATIONS.md",
    "10_MODEL_BENCHMARK_RESULTS.tsv",
    "11_CANDIDATE_RECALL_RESULTS.tsv",
    "12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv",
    "13_HUBNESS_ANALYSIS.tsv",
    "14_ABLATION_AND_STABILITY.tsv",
    "15_INTERACTION_STATISTICS_REVIEW.tsv",
    "16_MECHANICAL_EXPECTATION_CASES.tsv",
    "17_HUMAN_REVIEW_PACKET.tsv",
    "18_EXPLANATION_CONTRACT.md",
    "19_ANALYSIS_RUN_REGISTER.tsv",
    "20_PERFORMANCE_AND_ARCHITECTURE.md",
    "21_RED_TEAM.md",
    "22_MODEL_SHORTLIST_DECISION.md",
    "23_ROUND_DECISION.md",
)

RESEARCH_TSV_FILES = tuple(name for name in RESEARCH_FILES if name.endswith(".tsv"))

AUDIT_DOCUMENT_FILES = (
    "00_EXECUTIVE_RECEIPT.md",
    "01_SIGNAL_LINEAGE_VALIDATION.md",
    "02_CANDIDATE_INDEX_VALIDATION.md",
    "03_MODEL_BENCHMARK_VALIDATION.md",
    "04_MISSINGNESS_VALIDATION.md",
    "05_HUBNESS_AND_BIAS_VALIDATION.md",
    "06_PERFORMANCE.md",
    "07_SECURITY_BOUNDARY.md",
    "08_CHANGED_FILES.md",
)

RAW_FILES = (
    "exploration-similarity-evaluation-summary.json",
    "signal-lineage-summary.json",
    "independent-basis-summary.json",
    "candidate-index-summary.json",
    "model-benchmark-summary.json",
    "missingness-summary.json",
    "interaction-summary.json",
    "hubness-summary.json",
    "ablation-summary.json",
    "human-review-summary.json",
    "performance-summary.json",
    "analysis-run-summary.json",
    "security-summary.json",
)

LINEAGE_COLUMNS = (
    "signal_id",
    "source_artifact",
    "source_row_family",
    "direct_parent_signals",
    "derived_from_signals",
    "same_source_fact_group",
    "epistemic_level",
    "scoring_disposition",
    "independent_information_candidate",
    "duplicate_for_scoring",
    "interaction_only",
    "diagnostic_only",
    "candidate_generation_allowed",
    "scoring_allowed",
    "explanation_allowed",
    "reason",
)

SCORING_DISPOSITIONS = frozenset(
    {
        "INDEPENDENT_BASE_SIGNAL",
        "DEPENDENT_INTERACTION_SIGNAL",
        "CANDIDATE_GENERATION_ONLY",
        "COMPARABILITY_ONLY",
        "EXPLANATION_ONLY",
        "DIAGNOSTIC_ONLY",
        "REJECT",
    }
)
CANDIDATE_VARIANTS = frozenset(f"CG-CUR-{index}" for index in range(1, 7))
MODEL_IDS = frozenset(f"M{index}" for index in range(9))
SCALAR_MODEL_IDS = frozenset(f"M{index}" for index in range(8))
CURATORIAL_POLICIES = frozenset(f"CUR-W{index}" for index in range(1, 7))
MISSINGNESS_VARIANTS = frozenset(f"MISSING-{value}" for value in "ABCD")
INTERACTION_METHODS = frozenset(
    {
        "RAW_SUPPORT",
        "CONDITIONAL_SUPPORT",
        "LIFT",
        "PMI",
        "NORMALIZED_PMI",
        "LOG_LIKELIHOOD_RATIO",
        "SMOOTHED_LIFT",
        "SHRUNK_NORMALIZED_PMI",
    }
)
SUPPORT_THRESHOLDS = frozenset({2, 3, 5, 10, 20})
HUBNESS_K_VALUES = frozenset({10, 20, 50})
AXIOM_IDS = frozenset(f"AX-{index:03d}" for index in range(1, 16))
ABLATION_FAMILIES = frozenset(
    {
        "LEAVE_CONTEXT_OUT",
        "LEAVE_TIME_OUT",
        "LEAVE_GEOGRAPHY_OUT",
        "LEAVE_SOURCE_OUT",
        "LEAVE_CURATION_OUT",
        "LEAVE_MISSINGNESS_DIAGNOSTICS_OUT",
        "LEAVE_INTERACTIONS_OUT",
        "REMOVE_LARGEST_CURATED_CONTAINER",
        "REMOVE_DOMINANT_SOURCE",
        "CHANGE_BROAD_CONTAINER_THRESHOLD",
        "CHANGE_RARE_SUPPORT_THRESHOLD",
        "CHANGE_TEMPORAL_DECAY",
        "CHANGE_FAMILY_NORMALIZATION",
    }
)
MODEL_DECISIONS = frozenset(
    {
        "NO_MODEL_SELECTED",
        "MODEL_FAMILY_SHORTLISTED",
        "PROVISIONAL_INTERNAL_AFFINITY_PROFILE_SELECTED",
    }
)

INVARIANT_TEXT = {
    "EXP-SIM-INV-001": "Raw curated Jaccard cannot be imported by a production/public scorer.",
    "EXP-SIM-INV-002": "Every scored signal resolves to one lineage record.",
    "EXP-SIM-INV-003": "The same source fact contributes at most once to base affinity.",
    "EXP-SIM-INV-004": "Derived interaction terms are separated from parent contributions.",
    "EXP-SIM-INV-005": "Shared missing/unknown state adds zero default affinity.",
    "EXP-SIM-INV-006": "Every score exposes comparability.",
    "EXP-SIM-INV-007": "Every contribution exposes a denominator or source identity.",
    "EXP-SIM-INV-008": "Curatorial overlap never becomes historical relation.",
    "EXP-SIM-INV-009": "Rare never becomes important by definition.",
    "EXP-SIM-INV-010": "Map-coordinate distance contributes zero.",
    "EXP-SIM-INV-011": "Same source is not automatically positive affinity.",
    "EXP-SIM-INV-012": "Every model is deterministic.",
    "EXP-SIM-INV-013": "Every run is release/projection/signal-registry pinned.",
    "EXP-SIM-INV-014": "Held objects never enter research outputs.",
    "EXP-SIM-INV-015": "No internal UUID enters committed artifacts.",
    "EXP-SIM-INV-016": "No full pair matrix is committed.",
    "EXP-SIM-INV-017": "No probability claim is emitted.",
    "EXP-SIM-INV-018": "No public similarity model is selected.",
    "EXP-SIM-INV-019": "No clustering model is selected.",
    "EXP-SIM-INV-020": "Seeded randomness affects neither score nor candidate set.",
    "EXP-SIM-INV-021": "Symmetry is tested for symmetric models.",
    "EXP-SIM-INV-022": "Asymmetry is declared for query-conditioned models.",
    "EXP-SIM-INV-023": "Every shortlist model passes the mechanical suite.",
    "EXP-SIM-INV-024": "Every candidate result has an explanation path.",
}


class VerificationError(RuntimeError):
    """Raised when a Round 6 verification gate fails."""


@dataclass(frozen=True)
class Table:
    name: str
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
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


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _bool(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    normalized = str(value).strip().casefold()
    if normalized in {"true", "yes", "1", "pass"}:
        return True
    if normalized in {"false", "no", "0", "fail"}:
        return False
    raise VerificationError(f"{label} is not a boolean: {value!r}")


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise VerificationError(f"{label} is not numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise VerificationError(f"{label} is not numeric: {value!r}") from error
    if not math.isfinite(result):
        raise VerificationError(f"{label} is not finite")
    return result


def _integer(value: Any, label: str) -> int:
    result = _number(value, label)
    if not result.is_integer():
        raise VerificationError(f"{label} is not an integer: {value!r}")
    return int(result)


def _close(actual: Any, expected: Any, label: str) -> None:
    left = _number(actual, label)
    right = _number(expected, label)
    if not math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-12):
        raise VerificationError(f"{label} differs: {left} != {right}")


def _unique_json_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"JSON object contains duplicate key: {key}")
        result[key] = value
    return result


def _json_cell(value: str, label: str) -> Any:
    try:
        return json.loads(value, object_pairs_hook=_unique_json_object)
    except json.JSONDecodeError as error:
        raise VerificationError(f"{label} is not JSON") from error


def _split_ids(value: Any) -> tuple[str, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value or "").strip()
    if not text or text.upper() in {"NONE", "N/A", "NOT_APPLICABLE"}:
        return ()
    return tuple(item.strip() for item in re.split(r"[;,|]", text) if item.strip())


def _parse_tsv(path: Path) -> Table:
    payload = path.read_bytes()
    if not payload or b"\x00" in payload or b"\r" in payload:
        raise VerificationError(f"{path.name} is empty or contains CR/NUL bytes")
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise VerificationError(f"{path.name} must have exactly one final LF")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationError(f"{path.name} is not UTF-8") from error
    try:
        raw_rows = list(csv.reader(io.StringIO(text), delimiter="\t", strict=True))
    except csv.Error as error:
        raise VerificationError(f"{path.name} is not valid TSV") from error
    if len(raw_rows) < 2:
        raise VerificationError(f"{path.name} has no data rows")
    headers = tuple(raw_rows[0])
    if not all(headers) or len(headers) != len(set(headers)):
        raise VerificationError(f"{path.name} has blank or duplicate headers")
    if any(len(row) != len(headers) for row in raw_rows):
        raise VerificationError(f"{path.name} is not rectangular")
    rows = tuple(dict(zip(headers, row, strict=True)) for row in raw_rows[1:])
    return Table(path.name, headers, rows)


def _header(table: Table, *aliases: str) -> str:
    by_normalized = {_normalize_key(value): value for value in table.headers}
    for alias in aliases:
        value = by_normalized.get(_normalize_key(alias))
        if value is not None:
            return value
    raise VerificationError(f"{table.name} lacks required column {aliases[0]}")


def _optional_header(table: Table, *aliases: str) -> str | None:
    by_normalized = {_normalize_key(value): value for value in table.headers}
    for alias in aliases:
        value = by_normalized.get(_normalize_key(alias))
        if value is not None:
            return value
    return None


def _values(table: Table, *aliases: str) -> list[str]:
    key = _header(table, *aliases)
    return [row[key] for row in table.rows]


def _assert_set(actual: Iterable[Any], expected: set[Any] | frozenset[Any], label: str) -> None:
    observed = set(actual)
    if observed != set(expected):
        missing = sorted(set(expected) - observed, key=str)
        extra = sorted(observed - set(expected), key=str)
        raise VerificationError(f"{label} differs; missing={missing}, extra={extra}")


def _walk(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _all_key_values(value: Any, aliases: Sequence[str]) -> list[Any]:
    targets = {_normalize_key(alias) for alias in aliases}
    return [item for key, item in _walk(value) if _normalize_key(key) in targets]


def _evidence(
    documents: Sequence[Mapping[str, Any]],
    aliases: Sequence[str],
    label: str,
    *,
    required: bool = True,
) -> Any:
    values: list[Any] = []
    for document in documents:
        values.extend(_all_key_values(document, aliases))
    if not values:
        if required:
            raise VerificationError(f"aggregate evidence lacks {label}")
        return None
    canonical = {
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for value in values
    }
    if len(canonical) != 1:
        raise VerificationError(f"aggregate evidence conflicts for {label}: {values!r}")
    return values[0]


def _require_false(documents: Sequence[Mapping[str, Any]], aliases: Sequence[str], label: str) -> None:
    if _bool(_evidence(documents, aliases, label), label):
        raise VerificationError(f"{label} must be false")


def _require_zero(documents: Sequence[Mapping[str, Any]], aliases: Sequence[str], label: str) -> None:
    if _integer(_evidence(documents, aliases, label), label) != 0:
        raise VerificationError(f"{label} must be zero")


def _validate_exact_paths(research_dir: Path, audit_raw_dir: Path) -> None:
    if not research_dir.is_dir():
        raise VerificationError(f"research directory is absent: {research_dir}")
    actual_research = {path.name for path in research_dir.iterdir() if path.is_file()}
    _assert_set(actual_research, set(RESEARCH_FILES), "research file paths")
    if any(path.is_dir() for path in research_dir.iterdir()):
        raise VerificationError("research directory contains an unexpected subdirectory")
    if any(path.is_symlink() for path in research_dir.iterdir()):
        raise VerificationError("research package cannot contain symlinks")
    if not audit_raw_dir.is_dir():
        raise VerificationError(f"audit raw directory is absent: {audit_raw_dir}")
    actual_raw = {path.name for path in audit_raw_dir.iterdir() if path.is_file()}
    _assert_set(actual_raw, set(RAW_FILES), "audit raw file paths")
    if any(path.is_dir() for path in audit_raw_dir.iterdir()):
        raise VerificationError("audit raw directory contains an unexpected subdirectory")
    if any(path.is_symlink() for path in audit_raw_dir.iterdir()):
        raise VerificationError("audit raw package cannot contain symlinks")
    audit_dir = audit_raw_dir.parent
    actual_audit_files = {path.name for path in audit_dir.iterdir() if path.is_file()}
    _assert_set(
        actual_audit_files,
        set(AUDIT_DOCUMENT_FILES) | {"MANIFEST.tsv", "SHA256SUMS.txt"},
        "audit file paths",
    )
    actual_audit_dirs = {path.name for path in audit_dir.iterdir() if path.is_dir()}
    _assert_set(actual_audit_dirs, {"raw"}, "audit directory paths")
    if any(path.is_symlink() for path in audit_dir.iterdir()):
        raise VerificationError("audit package cannot contain symlinks")


def _load_json_receipts(audit_raw_dir: Path) -> dict[str, Mapping[str, Any]]:
    receipts: dict[str, Mapping[str, Any]] = {}
    total_bytes = 0
    for filename in RAW_FILES:
        path = audit_raw_dir / filename
        payload = path.read_bytes()
        total_bytes += len(payload)
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            raise VerificationError(f"{filename} must have exactly one final LF")
        if len(payload) > 16 * 1024 * 1024:
            raise VerificationError(f"{filename} is not bounded aggregate evidence")
        try:
            value = json.loads(payload, object_pairs_hook=_unique_json_object)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise VerificationError(f"{filename} is not valid UTF-8 JSON") from error
        if not isinstance(value, Mapping):
            raise VerificationError(f"{filename} must contain a JSON object")
        receipts[filename] = value
    if total_bytes > 64 * 1024 * 1024:
        raise VerificationError("audit raw evidence package is not bounded")
    return receipts


def _validate_audit_ledgers(audit_raw_dir: Path) -> None:
    audit_dir = audit_raw_dir.parent
    manifest = _parse_tsv(audit_dir / "MANIFEST.tsv")
    if manifest.headers != ("path", "bytes", "sha256", "role"):
        raise VerificationError("MANIFEST.tsv header differs from the audit ledger schema")
    expected_paths = set(AUDIT_DOCUMENT_FILES) | {f"raw/{name}" for name in RAW_FILES}
    manifest_paths = [row["path"] for row in manifest.rows]
    _assert_set(manifest_paths, expected_paths, "audit MANIFEST paths")
    if len(manifest_paths) != len(set(manifest_paths)):
        raise VerificationError("MANIFEST.tsv contains duplicate paths")
    manifest_hashes: dict[str, str] = {}
    for row in manifest.rows:
        relative = row["path"]
        path = audit_dir / relative
        payload = path.read_bytes()
        if _integer(row["bytes"], f"MANIFEST {relative} bytes") != len(payload):
            raise VerificationError(f"MANIFEST byte count differs: {relative}")
        digest = _sha256(payload)
        if row["sha256"] != digest or not row["role"].strip():
            raise VerificationError(f"MANIFEST digest/role differs: {relative}")
        manifest_hashes[relative] = digest

    sums_path = audit_dir / "SHA256SUMS.txt"
    lines = sums_path.read_text(encoding="utf-8").splitlines()
    if not lines or any(not re.fullmatch(r"[0-9a-f]{64}  [^\n]+", line) for line in lines):
        raise VerificationError("SHA256SUMS.txt has an invalid line")
    sums: dict[str, str] = {}
    for line in lines:
        digest, relative = line.split("  ", 1)
        if relative in sums:
            raise VerificationError("SHA256SUMS.txt contains a duplicate path")
        sums[relative] = digest
    expected_sums = {**manifest_hashes, "MANIFEST.tsv": _sha256((audit_dir / "MANIFEST.tsv").read_bytes())}
    if sums != expected_sums:
        raise VerificationError("SHA256SUMS.txt does not exactly seal MANIFEST.tsv and its entries")


def _research_receipt_mapping(summary: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    candidates = _all_key_values(summary, ("researchOutputReceipts", "researchFileReceipts"))
    if len(candidates) != 1 or not isinstance(candidates[0], Mapping):
        raise VerificationError("central summary lacks one research output receipt mapping")
    mapping = candidates[0]
    if set(map(str, mapping)) != set(RESEARCH_FILES):
        raise VerificationError("research output receipts do not cover the exact 24 files")
    return {str(key): value for key, value in mapping.items() if isinstance(value, Mapping)}


def _validate_research_receipts(research_dir: Path, summary: Mapping[str, Any]) -> None:
    receipts = _research_receipt_mapping(summary)
    if len(receipts) != len(RESEARCH_FILES):
        raise VerificationError("a research output receipt is malformed")
    for filename in RESEARCH_FILES:
        payload = (research_dir / filename).read_bytes()
        receipt = receipts[filename]
        digest = str(receipt.get("sha256", receipt.get("sha256Digest", "")))
        byte_count = receipt.get("bytes", receipt.get("byteCount"))
        if digest != _sha256(payload) or _integer(byte_count, f"{filename} receipt bytes") != len(payload):
            raise VerificationError(f"research output receipt differs: {filename}")


def _validate_lineage(table: Table) -> dict[str, Any]:
    if table.headers != LINEAGE_COLUMNS:
        raise VerificationError("03_SIGNAL_LINEAGE_REGISTRY.tsv header differs from its exact schema")
    if len(table.rows) != SIGNAL_COUNT:
        raise VerificationError("signal lineage registry must contain exactly 64 rows")
    identifiers = [row["signal_id"] for row in table.rows]
    if len(set(identifiers)) != SIGNAL_COUNT or any(not value for value in identifiers):
        raise VerificationError("signal lineage IDs are blank or duplicated")
    dispositions = Counter(row["scoring_disposition"] for row in table.rows)
    if set(dispositions) - SCORING_DISPOSITIONS:
        raise VerificationError("signal lineage contains an unknown scoring disposition")
    for row in table.rows:
        if not row["source_artifact"] or not row["source_row_family"] or not row["reason"]:
            raise VerificationError("signal lineage row lacks source/reason")
        for field in (
            "independent_information_candidate",
            "duplicate_for_scoring",
            "interaction_only",
            "diagnostic_only",
            "candidate_generation_allowed",
            "scoring_allowed",
            "explanation_allowed",
        ):
            _bool(row[field], f"lineage {row['signal_id']} {field}")
    base_groups: defaultdict[str, list[str]] = defaultdict(list)
    for row in table.rows:
        if row["scoring_disposition"] == "INDEPENDENT_BASE_SIGNAL" and _bool(
            row["scoring_allowed"], f"lineage {row['signal_id']} scoring_allowed"
        ):
            base_groups[row["same_source_fact_group"]].append(row["signal_id"])
    duplicates = {key: value for key, value in base_groups.items() if key and len(value) > 1}
    if duplicates:
        raise VerificationError(f"same source fact receives duplicate base credit: {duplicates}")
    return {
        "signalIds": set(identifiers),
        "scoredSignalIds": {
            row["signal_id"] for row in table.rows if _bool(row["scoring_allowed"], "scoring_allowed")
        },
        "dispositions": dispositions,
        "sameSourceFactGroups": {row["same_source_fact_group"] for row in table.rows if row["same_source_fact_group"]},
    }


def _validate_lineage_and_basis_raw(
    table: Table,
    lineage: Mapping[str, Any],
    lineage_summary: Mapping[str, Any],
    basis_summary: Mapping[str, Any],
) -> None:
    raw_signals = lineage_summary.get("signals")
    if not isinstance(raw_signals, list) or len(raw_signals) != SIGNAL_COUNT:
        raise VerificationError("signal-lineage raw summary lacks the 64 classified signals")
    raw_by_id = {
        str(row.get("signal_id", row.get("signalId", ""))): row
        for row in raw_signals
        if isinstance(row, Mapping)
    }
    if set(raw_by_id) != lineage["signalIds"]:
        raise VerificationError("signal-lineage raw identities differ from the TSV")
    for row in table.rows:
        native = raw_by_id[row["signal_id"]]
        if native.get("scoring_disposition", native.get("scoringDisposition")) != row["scoring_disposition"]:
            raise VerificationError("signal-lineage raw disposition differs from the TSV")
        if native.get("same_source_fact_group", native.get("sameSourceFactGroup")) != row["same_source_fact_group"]:
            raise VerificationError("signal-lineage raw source-fact group differs from the TSV")
    independent_ids = set(
        map(
            str,
            basis_summary.get("independentBaseSignalIds", ()),
        )
    )
    interaction_ids = set(
        map(
            str,
            basis_summary.get("dependentInteractionSignalIds", ()),
        )
    )
    expected_independent = {
        row["signal_id"]
        for row in table.rows
        if row["scoring_disposition"] == "INDEPENDENT_BASE_SIGNAL"
    }
    expected_interactions = {
        row["signal_id"]
        for row in table.rows
        if row["scoring_disposition"] == "DEPENDENT_INTERACTION_SIGNAL"
    }
    if independent_ids != expected_independent or interaction_ids != expected_interactions:
        raise VerificationError("independent basis IDs do not reconcile to lineage dispositions")
    candidate_keys = (
        "directCandidatePostingSignalIds",
        "highInformationCandidatePostingSignalIds",
    )
    candidate_ids = {
        str(value)
        for key in candidate_keys
        for value in basis_summary.get(key, ())
    }
    if not candidate_ids.issubset(lineage["signalIds"]):
        raise VerificationError("candidate basis references an unclassified signal")


_DIGEST_FIELD_FAMILIES: dict[str, str] = {
    "medium": "context",
    "theme": "context",
    "movement_context": "context",
    "decade": "temporal",
    "geography": "geography",
    "source": "source",
    "object_type": "descriptive",
    "creator": "descriptive",
}
_DIGEST_PROFILE_FAMILIES = (
    "context",
    "temporal",
    "geography",
    "source",
    "descriptive",
    "curatorialResidual",
)
_DIGEST_UNKNOWN_LABELS = frozenset(
    {
        "",
        "unknown",
        "not governed",
        "not_governed",
        "no published movement context",
        "no_published_movement_context",
    }
)


def _digest_member(value: Any, field: str) -> tuple[str, str]:
    if isinstance(value, str):
        identifier = value.strip()
        label = identifier
    elif isinstance(value, Mapping):
        identifier = str(value.get("id", "")).strip()
        label = str(value.get("label", identifier)).strip()
    else:
        raise VerificationError(f"frozen record {field} contains an invalid member")
    if not identifier:
        raise VerificationError(f"frozen record {field} contains a blank identifier")
    return identifier, label


def _digest_members(record: Mapping[str, Any], field: str) -> tuple[tuple[str, str], ...]:
    raw = record.get(field)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise VerificationError(f"frozen record {field} is not an array")
    return tuple(sorted({_digest_member(value, field) for value in raw}))


def _digest_observed(identifier: str, label: str) -> bool:
    del identifier
    normalized = label.strip().casefold().replace("-", "_")
    return normalized not in _DIGEST_UNKNOWN_LABELS and not normalized.startswith("unknown;")


def _digest_token(family: str, field: str, identifier: str) -> str:
    return f"{family}\x1f{field}\x1f{identifier}"


def _normalize_scoring_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Independently reproduce the sealed, model-visible record material.

    This intentionally does not import ``candidate_index`` or the benchmark.
    A self-consistent receipt therefore cannot conceal a different public
    cohort or a changed normalization boundary.
    """

    object_id = str(record.get("objectId", "")).strip()
    if not PUBLIC_ID_RE.fullmatch(object_id):
        raise VerificationError("frozen scoring record has an invalid public ID")
    if (
        record.get("held") is True
        or record.get("isHeld") is True
        or str(record.get("researchDisposition", "")).casefold() == "held"
    ):
        raise VerificationError("held data entered the model-visible record material")

    field_values: dict[str, tuple[str, ...]] = {}
    labels: dict[str, str] = {}
    for field in ("medium", "theme", "movement_context", "decade", "geography"):
        values = tuple(
            (identifier, label)
            for identifier, label in _digest_members(record, field)
            if _digest_observed(identifier, label)
        )
        field_values[field] = tuple(identifier for identifier, _ in values)
        labels.update({identifier: label for identifier, label in values})
    for field in ("source", "object_type", "creator"):
        if field not in record:
            raise VerificationError(f"frozen scoring record lacks {field}")
        identifier, label = _digest_member(record[field], field)
        labels[identifier] = label
        field_values[field] = (identifier,) if _digest_observed(identifier, label) else ()

    curated = _digest_members(record, "curated_container")
    curated_ids = tuple(identifier for identifier, _ in curated)
    labels.update({identifier: label for identifier, label in curated})
    family_tokens: defaultdict[str, list[str]] = defaultdict(list)
    for field, family in _DIGEST_FIELD_FAMILIES.items():
        for identifier in field_values[field]:
            family_tokens[family].append(_digest_token(family, field, identifier))

    start_year = record.get("startYear")
    end_year = record.get("endYear")
    if isinstance(start_year, bool) or not isinstance(start_year, int):
        raise VerificationError("frozen scoring record startYear is not an integer")
    if isinstance(end_year, bool) or not isinstance(end_year, int) or end_year < start_year:
        raise VerificationError("frozen scoring record endYear is invalid")
    precision = str(record.get("temporalPrecision", "")).strip()
    if not precision:
        raise VerificationError("frozen scoring record temporalPrecision is blank")

    raw_states = record.get("geographyMappingStates", record.get("geography_mapping_state", ()))
    raw_classes = record.get("geographyClasses", record.get("geography_class", ()))
    if not isinstance(raw_states, Sequence) or isinstance(raw_states, (str, bytes, bytearray)):
        raise VerificationError("frozen scoring record geography states are invalid")
    if not isinstance(raw_classes, Sequence) or isinstance(raw_classes, (str, bytes, bytearray)):
        raise VerificationError("frozen scoring record geography classes are invalid")
    states = tuple(sorted({_digest_member(value, "geographyMappingStates")[0] for value in raw_states}))
    classes = tuple(sorted({_digest_member(value, "geographyClasses")[0] for value in raw_classes}))
    multi_region = record.get("multiRegion")
    if not isinstance(multi_region, bool) or multi_region != (len(field_values["geography"]) > 1):
        raise VerificationError("frozen scoring record multiRegion does not reconcile")

    return {
        "objectId": object_id,
        "fieldValues": {key: tuple(value) for key, value in sorted(field_values.items())},
        "familyTokens": {
            key: tuple(sorted(set(value))) for key, value in sorted(family_tokens.items())
        },
        "candidateOnlyTokens": tuple(
            _digest_token("candidateOnly", "geography_class", value)
            for value in classes
        ),
        "curatedTokens": curated_ids,
        "residualCuratedTokens": (),
        "labels": dict(sorted(labels.items())),
        "startYear": start_year,
        "endYear": end_year,
        "temporalPrecision": precision,
        "geographyMappingStates": states,
        "geographyClasses": classes,
        "geographyQualified": bool(record.get("geographyQualified", False)),
        "multiRegion": multi_region,
    }


def _derive_model_context_receipts(
    records: Sequence[Mapping[str, Any]],
    candidate_index_sha256: str,
    *,
    expected_record_count: int = PUBLIC_OBJECT_COUNT,
) -> dict[str, str]:
    if not SHA256_RE.fullmatch(candidate_index_sha256):
        raise VerificationError("candidate-index digest is invalid")
    normalized = sorted(
        (_normalize_scoring_record(record) for record in records),
        key=lambda row: str(row["objectId"]),
    )
    object_ids = [str(row["objectId"]) for row in normalized]
    if len(object_ids) != expected_record_count or len(object_ids) != len(set(object_ids)):
        raise VerificationError(
            f"model-visible record cohort does not contain {expected_record_count:,} unique objects"
        )
    scoring_sha256 = _sha256(_canonical_json_bytes(normalized))

    family_documents: defaultdict[str, set[str]] = defaultdict(set)
    family_lengths: defaultdict[str, list[int]] = defaultdict(list)
    field_lengths: defaultdict[str, list[int]] = defaultdict(list)
    token_document_frequency: Counter[str] = Counter()
    token_family: dict[str, str] = {}
    for row in normalized:
        object_id = str(row["objectId"])
        family_tokens = row["familyTokens"]
        for family in _DIGEST_PROFILE_FAMILIES:
            tokens = tuple(family_tokens.get(family, ()))
            if tokens:
                family_documents[family].add(object_id)
            family_lengths[family].append(len(tokens))
            for token in tokens:
                token_document_frequency[token] += 1
                token_family[token] = family
        for field in _DIGEST_FIELD_FAMILIES:
            field_lengths[field].append(len(row["fieldValues"].get(field, ())))
        field_lengths["residual_curated_container"].append(
            len(row["residualCuratedTokens"])
        )

    goodall: dict[str, float] = {}
    by_family_df: defaultdict[str, list[tuple[str, int]]] = defaultdict(list)
    for token, frequency in token_document_frequency.items():
        family = token_family.get(token)
        if family in _DIGEST_PROFILE_FAMILIES:
            by_family_df[family].append((token, frequency))
    for family, token_rows in by_family_df.items():
        denominator = max(1, len(family_documents.get(family, ())))
        squared_by_frequency: defaultdict[int, float] = defaultdict(float)
        for _, frequency in token_rows:
            squared_by_frequency[frequency] += (frequency / denominator) ** 2
        cumulative = 0.0
        cumulative_by_frequency: dict[int, float] = {}
        for frequency in sorted(squared_by_frequency):
            cumulative += squared_by_frequency[frequency]
            cumulative_by_frequency[frequency] = cumulative
        for token, frequency in token_rows:
            goodall[token] = max(0.0, min(1.0, 1.0 - cumulative_by_frequency[frequency]))

    model_context_material = {
        "schemaVersion": MODEL_BASELINE_SCHEMA_VERSION,
        "candidateIndexSha256": candidate_index_sha256,
        "scoringRecordsSha256": scoring_sha256,
        "familyDocumentCounts": {
            family: len(values) for family, values in sorted(family_documents.items())
        },
        "averageFamilyLengths": {
            family: statistics.fmean(values) if values else 0.0
            for family, values in sorted(family_lengths.items())
        },
        "averageFieldLengths": {
            field: statistics.fmean(values) if values else 0.0
            for field, values in sorted(field_lengths.items())
        },
        "goodallWeightSha256": _sha256(
            json.dumps(goodall, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ),
    }
    model_context_sha256 = _sha256(_canonical_json_bytes(model_context_material))

    multi_fields = (
        "medium",
        "theme",
        "movement_context",
        "decade",
        "geography",
        "residual_curated_container",
    )
    field_vocabulary_counts: dict[str, int] = {}
    for field in multi_fields:
        vocabulary = {
            value
            for row in normalized
            for value in (
                row["residualCuratedTokens"]
                if field == "residual_curated_container"
                else row["fieldValues"].get(field, ())
            )
        }
        field_vocabulary_counts[field] = len(vocabulary)
    scalar_vocabulary_counts = {
        field: len(
            {
                value
                for row in normalized
                for value in row["fieldValues"].get(field, ())
            }
        )
        for field in ("source", "object_type", "creator")
    }
    compiled_material = {
        "schemaVersion": COMPILED_CONTEXT_SCHEMA_VERSION,
        "modelContextSha256": model_context_sha256,
        "scoringRecordsSha256": scoring_sha256,
        "objectCount": len(normalized),
        "fieldVocabularyCounts": field_vocabulary_counts,
        "scalarVocabularyCounts": scalar_vocabulary_counts,
        "randomnessUsed": False,
        "pairRowsMaterialized": False,
    }
    return {
        "scoringRecordsSha256": scoring_sha256,
        "modelContextSha256": model_context_sha256,
        "compiledFeatureContextSha256": _sha256(_canonical_json_bytes(compiled_material)),
    }


def _direct_digest(document: Mapping[str, Any], aliases: Sequence[str], label: str) -> str:
    targets = {_normalize_key(alias) for alias in aliases}
    values = [value for key, value in document.items() if _normalize_key(str(key)) in targets]
    if len(values) != 1 or not SHA256_RE.fullmatch(str(values[0])):
        raise VerificationError(f"{label} is absent, duplicated, or not a lowercase SHA-256")
    return str(values[0])


def _validate_model_context_receipts(
    raw: Mapping[str, Mapping[str, Any]],
    runs: Sequence[Mapping[str, Any]],
    normalized_records: Sequence[Mapping[str, Any]] | None,
) -> dict[str, str]:
    central = raw["exploration-similarity-evaluation-summary.json"]
    candidate = raw["candidate-index-summary.json"]
    models = raw["model-benchmark-summary.json"]
    candidate_index_sha256 = _direct_digest(
        central, ("candidateIndexSha256", "indexSha256"), "central candidate-index digest"
    )
    if _direct_digest(
        candidate, ("candidateIndexSha256", "indexSha256"), "candidate raw candidate-index digest"
    ) != candidate_index_sha256:
        raise VerificationError("candidate-index digest differs between central and candidate raw evidence")

    reconciled: dict[str, str] = {}
    for field in MODEL_CONTEXT_DIGEST_FIELDS:
        values = {
            _direct_digest(central, (field,), f"central {field}"),
            _direct_digest(candidate, (field,), f"candidate raw {field}"),
            _direct_digest(models, (field,), f"model raw {field}"),
        }
        if len(values) != 1:
            raise VerificationError(f"{field} differs across central/candidate/model raw evidence")
        reconciled[field] = values.pop()
    for receipt in runs:
        if str(receipt.get("candidateIndexSha256", "")) != candidate_index_sha256:
            raise VerificationError("analysis run candidate-index digest differs from semantic receipt")
        parameters = receipt.get("parameterSet")
        if not isinstance(parameters, Mapping):
            raise VerificationError("analysis run parameterSet is not a mapping")
        for field, expected in reconciled.items():
            if parameters.get(field) != expected:
                raise VerificationError(f"analysis run parameterSet does not pin {field}")
    if normalized_records is not None:
        derived = _derive_model_context_receipts(normalized_records, candidate_index_sha256)
        if derived != reconciled:
            raise VerificationError(
                "model/scoring/compiled context digests do not derive from the frozen public cohort"
            )
    return {"candidateIndexSha256": candidate_index_sha256, **reconciled}


def _validate_curatorial(table: Table) -> None:
    policy = _header(table, "policy_id", "policyId")
    _assert_set((row[policy] for row in table.rows), CURATORIAL_POLICIES, "curatorial policies")
    if len(table.rows) != 9:
        raise VerificationError("curatorial attenuation table must contain nine sensitivity rows")
    broad_stop = _header(table, "broad_stop_ratio", "broadStopRatio")
    w3_ratios = {
        _number(row[broad_stop], "CUR-W3 broad-stop ratio")
        for row in table.rows
        if row[policy] == "CUR-W3"
    }
    if w3_ratios != {0.25, 0.50, 0.75, 0.90}:
        raise VerificationError("CUR-W3 broad-container sensitivity grid differs")
    for aliases in (
        ("raw_membership_scoring_allowed", "rawMembershipScoringAllowed"),
        ("randomness_affects_candidate_set", "randomnessAffectsCandidateSet"),
        ("historical_relation", "historicalRelation"),
        ("semantic_relation", "semanticRelation"),
        ("probability",),
    ):
        key = _header(table, *aliases)
        if any(_bool(row[key], f"curatorial {aliases[0]}") for row in table.rows):
            raise VerificationError(f"curatorial {aliases[0]} must remain false")
    for aliases in (
        ("same_source_parent_duplication_failures", "sameSourceParentDuplicationFailures"),
        ("broad_dominance_failures", "broadDominanceFailures"),
    ):
        key = _header(table, *aliases)
        if any(_integer(row[key], f"curatorial {aliases[0]}") != 0 for row in table.rows):
            raise VerificationError(f"curatorial {aliases[0]} is nonzero")


def _validate_models(
    table: Table,
    shortlist: set[str],
    raw_summary: Mapping[str, Any],
) -> dict[str, Any]:
    model = _header(table, "model_id", "modelId")
    _assert_set((row[model] for row in table.rows), MODEL_IDS, "model IDs")
    if "M0" in shortlist:
        raise VerificationError("M0 negative control cannot be shortlisted")
    by_model: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in table.rows:
        by_model[row[model]].append(row)
    for aliases in (
        ("deterministic",),
        ("comparability_exposed", "comparabilityExposed", "comparabilityChannel"),
        ("explanation_path", "explanationPath", "explanationReady"),
    ):
        key = _header(table, *aliases)
        if any(not _bool(row[key], f"model {aliases[0]}") for row in table.rows):
            raise VerificationError(f"every model row must set {aliases[0]} true")
    for aliases in (("historical_relation", "historicalRelation"), ("semantic_relation", "semanticRelation"), ("probability",)):
        key = _header(table, *aliases)
        if any(_bool(row[key], f"model {aliases[0]}") for row in table.rows):
            raise VerificationError(f"model result crossed {aliases[0]} boundary")
    symmetry = _header(table, "symmetry_test", "symmetryTest", "symmetryStatus")
    asymmetry = _header(table, "asymmetry_declared", "asymmetryDeclared")
    symmetric_declared = _header(table, "symmetric", "isSymmetric")
    for model_id in shortlist:
        rows = by_model[model_id]
        if any(_bool(row[symmetric_declared], f"{model_id} symmetric") for row in rows):
            if not any(str(row[symmetry]).strip().upper() == "PASS" for row in rows):
                raise VerificationError(f"shortlisted symmetric model lacks a passing symmetry test: {model_id}")
        else:
            if not all(_bool(row[asymmetry], f"{model_id} asymmetry declared") for row in rows):
                raise VerificationError(f"query-conditioned shortlist model lacks declared asymmetry: {model_id}")
    shortlist_col = _optional_header(table, "shortlisted", "isShortlisted")
    if shortlist_col:
        row_shortlist = {row[model] for row in table.rows if _bool(row[shortlist_col], "shortlisted")}
        if row_shortlist != shortlist:
            raise VerificationError("model benchmark shortlist flags disagree with the decision")
    raw_rows = raw_summary.get("modelRows", raw_summary.get("rows"))
    if not isinstance(raw_rows, list) or not all(isinstance(row, Mapping) for row in raw_rows):
        raise VerificationError("model benchmark raw summary lacks native model rows")
    variant = _header(table, "variant_id", "variantId")
    table_keys = [(row[model], row[variant]) for row in table.rows]
    raw_keys = [(str(row.get("modelId", "")), str(row.get("variantId", ""))) for row in raw_rows]
    if len(table_keys) != len(set(table_keys)) or set(table_keys) != set(raw_keys):
        raise VerificationError("model benchmark TSV does not reconcile to native raw model rows")
    raw_by_key = {
        (str(row["modelId"]), str(row["variantId"])): row for row in raw_rows
    }
    family = _header(table, "model_family", "modelFamily")
    for row in table.rows:
        native = raw_by_key[(row[model], row[variant])]
        if row[family] != str(native.get("modelFamily", "")):
            raise VerificationError("model benchmark family differs from native raw evidence")
        if _bool(row[symmetric_declared], "TSV symmetric") != _bool(native.get("symmetric"), "raw symmetric"):
            raise VerificationError("model benchmark symmetry differs from native raw evidence")
        if shortlist_col and _bool(row[shortlist_col], "TSV shortlisted") != _bool(
            native.get("shortlistEligible", False), "raw shortlist eligible"
        ):
            raise VerificationError("model benchmark shortlist differs from native raw evidence")
    return {"rowsByModel": by_model}


def _validate_candidates(
    table: Table,
    shortlist: set[str],
    raw_summary: Mapping[str, Any],
) -> None:
    variant = _header(table, "candidate_variant_id", "candidateVariantId", "variant_id", "variant")
    _assert_set((row[variant] for row in table.rows), CANDIDATE_VARIANTS, "candidate variants")
    model = _header(table, "model_id", "modelId", "reference_model_id", "referenceModelId")
    if shortlist and {row[model] for row in table.rows} != shortlist:
        raise VerificationError("candidate recall reference-model set differs from the shortlist")
    for aliases in (
        ("candidate_pool_p50", "candidatePoolP50"),
        ("candidate_pool_p95", "candidatePoolP95"),
        ("candidate_pool_p99", "candidatePoolP99"),
        ("candidate_pool_max", "candidatePoolMax"),
        ("zero_candidate_object_count", "zeroCandidateObjectCount"),
        ("near_full_candidate_object_count", "nearFullCandidateObjectCount"),
    ):
        key = _header(table, *aliases)
        for row in table.rows:
            value = _number(row[key], f"candidate {aliases[0]}")
            if not 0 <= value <= (OTHER_PUBLIC_OBJECT_COUNT if "pool" in aliases[0] else PUBLIC_OBJECT_COUNT):
                raise VerificationError(f"candidate {aliases[0]} escapes its population")
    for aliases in (("recall_at_10", "recallAt10"), ("recall_at_20", "recallAt20"), ("recall_at_50", "recallAt50")):
        key = _header(table, *aliases)
        for row in table.rows:
            value = _number(row[key], f"candidate {aliases[0]}")
            if not 0 <= value <= 1:
                raise VerificationError(f"candidate {aliases[0]} escapes [0,1]")
    pair_rows = _header(table, "pair_rows_materialized", "pairRowsMaterialized")
    randomness = _header(table, "randomness_affects_candidate_set", "randomnessAffectsCandidateSet")
    if any(_integer(row[pair_rows], "pair rows materialized") != 0 for row in table.rows):
        raise VerificationError("candidate evaluation materialized pair rows")
    if any(_bool(row[randomness], "candidate randomness") for row in table.rows):
        raise VerificationError("candidate generation depends on randomness")
    reference_variant = _header(
        table,
        "reference_variant_id",
        "referenceVariantId",
        "model_variant_id",
        "modelVariantId",
    )
    table_keys = [(row[variant], row[reference_variant]) for row in table.rows]
    if len(table_keys) != len(set(table_keys)):
        raise VerificationError("candidate recall TSV duplicates a candidate/reference variant row")
    reference_variants = {row[reference_variant] for row in table.rows}
    if set(table_keys) != {
        (candidate_variant, reference)
        for candidate_variant in CANDIDATE_VARIANTS
        for reference in reference_variants
    }:
        raise VerificationError("candidate recall does not cover every candidate/reference cross-product")
    raw_rows = raw_summary.get("rows")
    if not isinstance(raw_rows, list) or not all(isinstance(row, Mapping) for row in raw_rows):
        raise VerificationError("candidate-index raw summary lacks native long-form rows")
    grouped: defaultdict[tuple[str, str], dict[int, Mapping[str, Any]]] = defaultdict(dict)
    for row in raw_rows:
        key = (str(row.get("candidateVariant", "")), str(row.get("referenceVariantId", "")))
        k = _integer(row.get("k"), "raw candidate recall k")
        if k in grouped[key]:
            raise VerificationError("native candidate recall rows duplicate k")
        grouped[key][k] = row
    if set(table_keys) != set(grouped):
        raise VerificationError("candidate recall TSV does not reconcile to native raw keys")
    recall_headers = {
        10: _header(table, "recall_at_10", "recallAt10"),
        20: _header(table, "recall_at_20", "recallAt20"),
        50: _header(table, "recall_at_50", "recallAt50"),
    }
    pool_headers = {
        "candidatePoolP50": _header(table, "candidate_pool_p50", "candidatePoolP50"),
        "candidatePoolP95": _header(table, "candidate_pool_p95", "candidatePoolP95"),
        "candidatePoolP99": _header(table, "candidate_pool_p99", "candidatePoolP99"),
        "candidatePoolMax": _header(table, "candidate_pool_max", "candidatePoolMax"),
        "zeroCandidateObjectCount": _header(table, "zero_candidate_object_count", "zeroCandidateObjectCount"),
        "nearFullCorpusCandidateObjectCount": _header(
            table,
            "near_full_candidate_object_count",
            "nearFullCandidateObjectCount",
            "nearFullCorpusCandidateObjectCount",
        ),
    }
    for row in table.rows:
        native_by_k = grouped[(row[variant], row[reference_variant])]
        if set(native_by_k) != HUBNESS_K_VALUES:
            raise VerificationError("native candidate recall k grid is incomplete")
        if {
            str(native.get("referenceModelId", "")) for native in native_by_k.values()
        } != {row[model]}:
            raise VerificationError("candidate recall reference model differs from native raw evidence")
        for k, field in recall_headers.items():
            _close(row[field], native_by_k[k].get("recall"), f"candidate recall@{k}")
        for raw_field, tsv_field in pool_headers.items():
            values = {str(native.get(raw_field)) for native in native_by_k.values()}
            if len(values) != 1:
                raise VerificationError(f"native candidate {raw_field} conflicts across k")
            _close(row[tsv_field], next(iter(values)), f"candidate {raw_field}")


def _validate_bias(table: Table, shortlist: set[str]) -> None:
    model = _header(table, "model_id", "modelId")
    if shortlist and not shortlist.issubset({row[model] for row in table.rows}):
        raise VerificationError("bias analysis lacks a shortlisted model")
    for aliases in (
        ("result_top1_source_share", "resultTop1SourceShare"),
        ("result_hhi", "resultHhi"),
        ("cross_source_rate", "crossSourceRate"),
        ("source_dominated_query_rate", "sourceDominatedQueryRate"),
        ("curation_dominated_query_rate", "curationDominatedQueryRate"),
        ("maximum_family_contribution_p95", "p95MaximumFamilyShare", "maxFamilyContributionP95"),
    ):
        key = _header(table, *aliases)
        if any(not 0 <= _number(row[key], f"bias {aliases[0]}") <= 1 for row in table.rows):
            raise VerificationError(f"bias {aliases[0]} escapes [0,1]")


def _validate_hubness(table: Table, shortlist: set[str]) -> None:
    model = _header(table, "model_id", "modelId")
    k_field = _header(table, "k")
    by_model: defaultdict[str, set[int]] = defaultdict(set)
    for row in table.rows:
        by_model[row[model]].add(_integer(row[k_field], "hubness k"))
    required_models = SCALAR_MODEL_IDS | shortlist
    if not required_models.issubset(by_model):
        raise VerificationError("hubness analysis does not cover every scalar/shortlist model")
    for model_id in required_models:
        if by_model[model_id] != HUBNESS_K_VALUES:
            raise VerificationError(f"hubness k grid differs for {model_id}")
    for aliases in (
        ("mean",),
        ("variance",),
        ("maximum_occurrence", "maximumOccurrence"),
        ("zero_occurrence_object_count", "zeroOccurrenceObjectCount"),
    ):
        key = _header(table, *aliases)
        if any(_number(row[key], f"hubness {aliases[0]}") < 0 for row in table.rows):
            raise VerificationError(f"hubness {aliases[0]} is negative")
    skewness = _header(table, "skewness")
    for row in table.rows:
        _number(row[skewness], "hubness skewness")
    for aliases in (
        ("gini",),
        ("top1_percent_occurrence_share", "top1PercentOccurrenceShare"),
    ):
        key = _header(table, *aliases)
        if any(not 0 <= _number(row[key], f"hubness {aliases[0]}") <= 1 for row in table.rows):
            raise VerificationError(f"hubness {aliases[0]} escapes [0,1]")


def _validate_ablations(table: Table) -> None:
    model = _header(table, "model_id", "modelId")
    ablation_id = _header(table, "ablation_id", "ablationId")
    family = _header(table, "ablation_family", "ablationFamily")
    k_field = _header(table, "k")
    by_model: defaultdict[str, set[str]] = defaultdict(set)
    by_variant: defaultdict[tuple[str, str], set[int]] = defaultdict(set)
    for row in table.rows:
        by_model[row[model]].add(row[family])
        key = (row[model], row[ablation_id])
        k = _integer(row[k_field], "ablation k")
        if k in by_variant[key]:
            raise VerificationError("ablation table duplicates a model/variant/k row")
        by_variant[key].add(k)
    for model_id in MODEL_IDS - {"M0"}:
        if by_model[model_id] != ABLATION_FAMILIES:
            raise VerificationError(f"ablation family coverage differs for {model_id}")
        if sum(model == model_id for model, _ in by_variant) != 27:
            raise VerificationError(f"ablation variant count differs for {model_id}")
    if set(by_model) != MODEL_IDS - {"M0"} or len(by_variant) != 216 or len(table.rows) != 648:
        raise VerificationError("ablation table is not the exact 8 x 27 x 3 sensitivity grid")
    if any(k_values != HUBNESS_K_VALUES for k_values in by_variant.values()):
        raise VerificationError("ablation table does not contain k=10,20,50 for every variant")
    learned = _header(table, "learned_weights_used", "learnedWeightsUsed")
    labels = _header(table, "historical_labels_used", "historicalLabelsUsed")
    if any(_bool(row[learned], "ablation learned weights") or _bool(row[labels], "ablation labels") for row in table.rows):
        raise VerificationError("ablation analysis uses learned weights or historical labels")


def _validate_interactions(
    table: Table,
    raw_summary: Mapping[str, Any],
    candidate_summary: Mapping[str, Any],
) -> None:
    method = _header(table, "method_id", "methodId", "method")
    threshold = _header(table, "support_threshold", "supportThreshold")
    combinations = {(row[method], _integer(row[threshold], "interaction threshold")) for row in table.rows}
    expected = {(method_id, value) for method_id in INTERACTION_METHODS for value in SUPPORT_THRESHOLDS}
    if combinations != expected or len(table.rows) != len(expected):
        raise VerificationError("interaction method/support sensitivity grid is not exact")
    parent = _header(table, "parent_contribution_repeated", "parentContributionRepeated")
    importance = _header(
        table,
        "importance_inference",
        "importanceInference",
        "rare_means_important",
        "rareMeansImportant",
    )
    if any(_bool(row[parent], "interaction parent repeated") for row in table.rows):
        raise VerificationError("interaction repeats a parent contribution")
    for row in table.rows:
        value = str(row[importance]).strip()
        if value.upper() != "PROHIBITED" and _bool(value, "rare means important"):
            raise VerificationError("interaction table equates rarity with importance")

    if raw_summary.get("jointObservableDenominatorPolicy") != "ALL_DIMENSIONS_OBSERVED":
        raise VerificationError("interaction denominators are not restricted to jointly observable records")
    for field in (
        "invalidDenominatorCount",
        "supportExceedsDenominatorCount",
        "nonPositiveExcessResidualCount",
        "gridReconciliationFailureCount",
        "scorerCapReconciliationFailureCount",
        "interactionParentDoubleCountFailures",
        "lowSupportInflationFailureCount",
    ):
        if _integer(raw_summary.get(field), f"interaction {field}") != 0:
            raise VerificationError(f"interaction semantic guard reports {field}")
    if not _bool(
        raw_summary.get("positiveExcessAssociationRequired"),
        "interaction positive-excess requirement",
    ):
        raise VerificationError("interaction residuals do not require positive excess association")

    pair_count = _integer(raw_summary.get("observedPairCellCount"), "observed pair-cell count")
    triple_count = _integer(raw_summary.get("observedTripleCellCount"), "observed triple-cell count")
    registry_cell_count = _integer(raw_summary.get("registryCellCount"), "interaction registry-cell count")
    if pair_count < 0 or triple_count < 0 or registry_cell_count <= 0 or pair_count + triple_count != registry_cell_count:
        raise VerificationError("interaction registry cell counts do not reconcile")

    raw_rows = raw_summary.get("rows")
    if not isinstance(raw_rows, list) or not all(isinstance(row, Mapping) for row in raw_rows):
        raise VerificationError("interaction raw summary lacks its method grid rows")
    raw_keys = [
        (str(row.get("method", row.get("methodId", ""))), _integer(row.get("supportThreshold"), "raw interaction threshold"))
        for row in raw_rows
    ]
    if len(raw_keys) != len(set(raw_keys)) or set(raw_keys) != expected:
        raise VerificationError("interaction raw method grid does not reconcile")
    if (
        _integer(raw_summary.get("expectedMethodGridRowCount"), "expected interaction grid rows") != len(expected)
        or _integer(raw_summary.get("observedMethodGridRowCount"), "observed interaction grid rows") != len(raw_rows)
    ):
        raise VerificationError("interaction method-grid reconciliation counts differ")
    raw_by_key = {key: row for key, row in zip(raw_keys, raw_rows, strict=True)}
    table_by_key = {
        (row[method], _integer(row[threshold], "interaction threshold")): row for row in table.rows
    }
    for key, row in raw_by_key.items():
        eligible = _integer(row.get("eligibleObservedCellCount"), "eligible observed interaction cells")
        excluded = _integer(row.get("lowSupportCellsExcluded"), "excluded low-support interaction cells")
        if eligible < 0 or excluded < 0 or eligible + excluded != registry_cell_count:
            raise VerificationError("interaction support grid does not partition observed registry cells")
        if _bool(row.get("parentContributionRepeated"), "raw interaction parent repeated"):
            raise VerificationError("interaction raw method grid repeats a parent contribution")
        if _bool(row.get("rareMeansImportant"), "raw interaction rare-means-important"):
            raise VerificationError("interaction raw method grid equates rarity with importance")
        table_row = table_by_key[key]
        for aliases, raw_key in (
            (("eligible_observed_cell_count", "eligibleObservedCellCount"), "eligibleObservedCellCount"),
            (("low_support_cells_excluded", "lowSupportCellsExcluded"), "lowSupportCellsExcluded"),
            (("statistic_p50", "statisticP50"), "statisticP50"),
            (("statistic_p95", "statisticP95"), "statisticP95"),
            (("statistic_max", "statisticMax"), "statisticMax"),
        ):
            column = _optional_header(table, *aliases)
            if column is not None:
                _close(table_row[column], row.get(raw_key), f"interaction TSV/raw {raw_key}")

    residual_rows = raw_summary.get("residualRows")
    if not isinstance(residual_rows, list) or not all(isinstance(row, Mapping) for row in residual_rows):
        raise VerificationError("interaction raw summary lacks residual sensitivity rows")
    expected_residual = {
        (method_id, value)
        for method_id in RESIDUAL_INTERACTION_METHODS
        for value in SUPPORT_THRESHOLDS
    }
    residual_keys = [
        (str(row.get("method", "")), _integer(row.get("supportThreshold"), "residual threshold"))
        for row in residual_rows
    ]
    if len(residual_keys) != len(set(residual_keys)) or set(residual_keys) != expected_residual:
        raise VerificationError("interaction residual method/support grid is not exact")
    if (
        _integer(raw_summary.get("expectedResidualGridRowCount"), "expected residual grid rows")
        != len(expected_residual)
        or _integer(raw_summary.get("observedResidualGridRowCount"), "observed residual grid rows")
        != len(residual_rows)
    ):
        raise VerificationError("interaction residual-grid reconciliation counts differ")
    for row in residual_rows:
        cell_count = _integer(row.get("cellCount"), "residual cell count")
        if cell_count != registry_cell_count:
            raise VerificationError("interaction residual row does not cover the observed registry")
        cap = _number(row.get("cap"), "interaction residual cap")
        p50 = _number(row.get("residualP50"), "interaction residual p50")
        p95 = _number(row.get("residualP95"), "interaction residual p95")
        maximum = _number(row.get("residualMax"), "interaction residual max")
        if not 0 < cap <= 1 or not 0 <= p50 <= p95 <= maximum <= cap + 1e-12:
            raise VerificationError("interaction residual distribution escapes its declared cap")
        if not _bool(
            row.get("positiveExcessAssociationRequired"),
            "residual positive-excess requirement",
        ):
            raise VerificationError("a residual grid row does not require positive excess")
        eligible = _integer(
            row.get("positiveExcessEligibleCellCount"),
            "positive-excess eligible interaction cells",
        )
        positive = _integer(row.get("positiveResidualCellCount"), "positive residual cells")
        nonpositive = _integer(
            row.get("nonPositiveExcessResidualCount"),
            "non-positive-excess residual cells",
        )
        if not 0 <= positive <= eligible <= cell_count or nonpositive != 0:
            raise VerificationError("interaction residual positive-excess counts do not reconcile")
        if row.get("method") == "NO_INTERACTION_CONTRIBUTION" and (
            positive != 0 or any(abs(value) > 1e-12 for value in (p50, p95, maximum))
        ):
            raise VerificationError("no-interaction control emits a residual contribution")

    registry_sha256 = str(raw_summary.get("registrySha256", ""))
    context_sha256 = str(raw_summary.get("trustedInteractionContextSha256", ""))
    if not SHA256_RE.fullmatch(registry_sha256) or not SHA256_RE.fullmatch(context_sha256):
        raise VerificationError("interaction registry/trusted-context digest is invalid")
    candidate_registry_sha256 = str(
        _evidence(
            [candidate_summary],
            ("interactionRegistrySha256", "registrySha256"),
            "candidate interaction-registry digest",
        )
    )
    candidate_context_sha256 = str(
        _evidence(
            [candidate_summary],
            (
                "trustedInteractionContextSha256",
                "interactionContextSha256",
                "contextSha256",
            ),
            "candidate trusted-interaction-context digest",
        )
    )
    if (
        candidate_registry_sha256 != registry_sha256
        or candidate_context_sha256 != context_sha256
    ):
        raise VerificationError("candidate index is not bound to the audited interaction context")

    scorer_rows = raw_summary.get("scorerExperimentRows")
    if not isinstance(scorer_rows, list) or not all(isinstance(row, Mapping) for row in scorer_rows):
        raise VerificationError("interaction raw evidence lacks direct scorer experiment rows")
    policies = [str(row.get("interactionPolicy", "")) for row in scorer_rows]
    if len(policies) != len(set(policies)) or set(policies) != RESIDUAL_INTERACTION_METHODS:
        raise VerificationError("interaction direct-scorer experiment does not cover exactly four policies")
    anchor_counts = {
        _integer(row.get("anchorCount"), "interaction scorer anchor count") for row in scorer_rows
    }
    pair_counts = {
        _integer(row.get("evaluatedPairCount"), "interaction scorer pair count")
        for row in scorer_rows
    }
    declared_pair_count = _integer(
        raw_summary.get("scorerExperimentPairCount"), "interaction scorer declared pair count"
    )
    if (
        len(anchor_counts) != 1
        or next(iter(anchor_counts)) <= 0
        or len(pair_counts) != 1
        or next(iter(pair_counts)) <= 0
        or pair_counts != {declared_pair_count}
    ):
        raise VerificationError("interaction direct-scorer anchor/pair populations do not reconcile")
    for row in scorer_rows:
        overlap = _number(row.get("meanTop20Overlap"), "interaction scorer top-20 overlap")
        correlation = _number(
            row.get("meanTop20RankCorrelation"), "interaction scorer rank correlation"
        )
        delta_p50 = _number(row.get("scoreDeltaP50"), "interaction scorer delta p50")
        delta_p95 = _number(row.get("scoreDeltaP95"), "interaction scorer delta p95")
        if (
            not 0 <= overlap <= 1
            or not -1 <= correlation <= 1
            or not 0 <= delta_p50 <= delta_p95
            or row.get("directScorerSensitivity") is not True
        ):
            raise VerificationError("interaction direct-scorer metric or sensitivity flag is invalid")
        if row.get("interactionPolicy") == "NO_INTERACTION_CONTRIBUTION" and not (
            overlap == 1
            and correlation == 1
            and delta_p50 == 0
            and delta_p95 == 0
        ):
            raise VerificationError("interaction no-contribution scorer control is not an identity")


def _validate_mechanical(table: Table, shortlist: set[str]) -> None:
    axiom = _header(table, "axiom_id", "axiomId")
    _assert_set((row[axiom] for row in table.rows), AXIOM_IDS, "mechanical axioms")
    if len(table.rows) != 15:
        raise VerificationError("mechanical expectation table must contain exactly 15 rows")
    status = _header(table, "status")
    failures = _header(table, "failure_count", "failureCount")
    tested = _header(table, "tested_model_ids", "testedModelIds")
    if any(row[status].strip().upper() != "PASS" or _integer(row[failures], "axiom failures") != 0 for row in table.rows):
        raise VerificationError("a mechanical expectation failed")
    tested_models = {model for row in table.rows for model in _split_ids(row[tested])}
    if not shortlist.issubset(tested_models):
        raise VerificationError("a shortlisted model is absent from the mechanical suite")
    for aliases in (("historical_relation", "historicalRelation"), ("semantic_relation", "semanticRelation"), ("probability",)):
        key = _header(table, *aliases)
        if any(_bool(row[key], f"mechanical {aliases[0]}") for row in table.rows):
            raise VerificationError("mechanical evidence crosses a semantic boundary")


def _validate_human_review(table: Table, public_ids: set[str], held_ids: set[str]) -> None:
    anchor = _header(table, "anchor_public_id", "anchorPublicId")
    candidate = _header(table, "candidate_public_id", "candidatePublicId")
    blind = _header(table, "blind_profile_slot", "blindProfileSlot")
    ordinal = _header(table, "candidate_ordinal", "candidateOrdinal")
    retrieval = _header(table, "retrieval_reasons", "retrievalReasons")
    shared = _header(table, "shared_independent_signals", "sharedIndependentSignals")
    comparability = _header(table, "comparability_ratio", "comparabilityRatio")
    source_composition = _header(table, "source_composition", "sourceComposition")
    anchors = {row[anchor] for row in table.rows}
    if len(anchors) != HUMAN_REVIEW_ANCHOR_COUNT:
        raise VerificationError("human review packet must contain exactly 72 anchors")
    if public_ids and any(value not in public_ids for value in anchors):
        raise VerificationError("human review contains a non-public anchor")
    groups: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    for row in table.rows:
        anchor_id = row[anchor]
        candidate_id = row[candidate]
        if anchor_id == candidate_id or not PUBLIC_ID_RE.fullmatch(anchor_id) or not PUBLIC_ID_RE.fullmatch(candidate_id):
            raise VerificationError("human review contains an invalid/self candidate")
        if held_ids and (anchor_id in held_ids or candidate_id in held_ids):
            raise VerificationError("held object entered the human review packet")
        if public_ids and candidate_id not in public_ids:
            raise VerificationError("human review contains a non-public candidate")
        if not row[retrieval].strip() or not row[shared].strip():
            raise VerificationError("human review candidate lacks retrieval/shared-independent evidence")
        ratio = _number(row[comparability], "human review comparability")
        if not 0 <= ratio <= 1:
            raise VerificationError("human review comparability escapes [0,1]")
        if row[source_composition] not in {
            "SAME_GOVERNED_SOURCE_NAME",
            "CROSS_GOVERNED_SOURCE_NAME",
        }:
            raise VerificationError("human review source composition is absent or invalid")
        groups[(anchor_id, row[blind])].append(_integer(row[ordinal], "candidate ordinal"))
    for key, ordinals in groups.items():
        if not 3 <= len(ordinals) <= 5 or sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise VerificationError(f"human review bounded candidate group differs: {key}")
    for aliases in (
        ("useful_for_further_exploration", "usefulForFurtherExploration"),
        ("explanation_intelligible", "explanationIntelligible"),
        ("merely_broad_category", "merelyBroadCategory"),
        ("new_defensible_research_direction", "newDefensibleResearchDirection"),
        ("accidental_relation_suggestion", "accidentalRelationSuggestion"),
        ("reviewer_notes", "reviewerNotes"),
    ):
        key = _header(table, *aliases)
        if any(row[key].strip() for row in table.rows):
            raise VerificationError("human judgments were fabricated or prefilled")
    completed = _header(table, "human_review_completed", "humanReviewCompleted")
    if any(_bool(row[completed], "human review completed") for row in table.rows):
        raise VerificationError("human review was marked complete")
    for aliases in (("historical_relation", "historicalRelation"), ("semantic_relation", "semanticRelation"), ("probability",)):
        key = _header(table, *aliases)
        if any(_bool(row[key], f"human review {aliases[0]}") for row in table.rows):
            raise VerificationError("human review crosses a semantic boundary")
    forbidden_score_headers = {
        "score",
        "diagnosticscore",
        "affinityscore",
        "finalscore",
        "modelid",
        "modelname",
    }
    if {_normalize_key(value) for value in table.headers} & forbidden_score_headers:
        raise VerificationError("human review packet exposes a score or unblinded model identity")
    for row in table.rows:
        for key, value in row.items():
            if key not in {anchor, candidate} and MODEL_ID_TOKEN_RE.search(value):
                raise VerificationError("human review packet exposes an unblinded model ID")


def _explanation_array(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise VerificationError(f"explanation {label} is not an array")
    if nonempty and not value:
        raise VerificationError(f"explanation {label} is empty")
    return value


def _safe_explanation_text(value: Any, label: str, *, allow_blank: bool = False) -> str:
    text = str(value if value is not None else "").strip()
    if not text and not allow_blank:
        raise VerificationError(f"explanation {label} is blank")
    if UUID_RE.search(text) or EXPLANATION_PRIVATE_RE.search(text):
        raise VerificationError(f"explanation {label} contains private identity or a URL")
    return text


def _validate_explanation_contribution(row: Any, *, kind: str) -> None:
    if not isinstance(row, Mapping):
        raise VerificationError(f"explanation {kind} contribution is not an object")
    _safe_explanation_text(row.get("family"), f"{kind}.family")
    has_ratio = "numerator" in row and "denominator" in row
    has_source = bool(str(row.get("sourceIdentity", "")).strip())
    if not has_ratio and not has_source:
        raise VerificationError(
            f"explanation {kind} contribution lacks numerator/denominator or source identity"
        )
    if has_ratio:
        numerator = _number(row.get("numerator"), f"explanation {kind} numerator")
        denominator = _number(row.get("denominator"), f"explanation {kind} denominator")
        if numerator < 0 or denominator <= 0:
            raise VerificationError(f"explanation {kind} contribution has an invalid ratio")
    if has_source:
        _safe_explanation_text(row.get("sourceIdentity"), f"{kind}.sourceIdentity")
    if kind == "affinity":
        _safe_explanation_text(row.get("sameSourceFactGroup"), "affinity.sameSourceFactGroup")
        _safe_explanation_text(row.get("signalId"), "affinity.signalId")
    for field in ("historicalRelation", "semanticRelation"):
        if field not in row or _bool(row[field], f"explanation {kind} {field}"):
            raise VerificationError(f"explanation {kind} contribution crossed {field}")


def _validate_m7_explanation_formula(row: Mapping[str, Any], field: str) -> None:
    """Independently recompute the five declared BM25F-like relationships."""

    if row.get("basis") != "BM25F_LIKE_FIELDED_RETRIEVAL" or row.get(
        "formula"
    ) != "BM25F_LIKE_FIELD_SATURATION":
        raise VerificationError(f"{field} lacks the declared M7 BM25F-like formula")
    terms = row.get("queryTermStatistics")
    if not isinstance(terms, list) or not terms or not all(
        isinstance(term, Mapping) for term in terms
    ):
        raise VerificationError(f"{field} lacks query-term statistics")
    matched_count = 0
    query_weight = 0.0
    matched_weight = 0.0
    for ordinal, term in enumerate(terms):
        _safe_explanation_text(
            term.get("featureId"), f"{field}.queryTermStatistics[{ordinal}].featureId"
        )
        frequency = term.get("documentFrequency")
        if isinstance(frequency, bool) or not isinstance(frequency, int) or frequency <= 0:
            raise VerificationError(f"{field} has an invalid document frequency")
        idf = _number(term.get("idf"), f"{field} query-term IDF")
        matched = term.get("matched")
        if idf < 0 or not isinstance(matched, bool):
            raise VerificationError(f"{field} has invalid IDF/match metadata")
        query_weight += idf
        if matched:
            matched_count += 1
            matched_weight += idf
    if _integer(row.get("matchedQueryTermCount"), f"{field} matched term count") != matched_count:
        raise VerificationError(f"{field} matched query-term count does not reconcile")
    document_length = row.get("documentFieldLength")
    if isinstance(document_length, bool) or not isinstance(document_length, int) or document_length <= 0:
        raise VerificationError(f"{field} document field length is invalid")
    average_length = _number(
        row.get("averageDocumentFieldLength"), f"{field} average document length"
    )
    k1 = _number(row.get("k1"), f"{field} k1")
    b = _number(row.get("b"), f"{field} b")
    declared_weight = _number(
        row.get("declaredFamilyWeight"), f"{field} declared family weight"
    )
    if average_length <= 0 or k1 <= 0 or not 0 <= b <= 1 or declared_weight <= 0:
        raise VerificationError(f"{field} BM25F-like parameters are invalid")

    expected_length = 1.0 - b + b * document_length / average_length
    expected_saturation = (k1 + 1.0) / (1.0 + k1 * expected_length)
    expected_numerator = matched_weight * expected_saturation
    expected_denominator = query_weight
    expected_contribution = min(
        1.0,
        expected_numerator / expected_denominator if expected_denominator else 0.0,
    )
    relationships = (
        (row.get("lengthNormalization"), expected_length, "lengthNormalization"),
        (row.get("saturation"), expected_saturation, "saturation"),
        (row.get("numerator"), expected_numerator, "numerator"),
        (row.get("denominator"), expected_denominator, "denominator"),
        (row.get("contribution"), expected_contribution, "contribution"),
    )
    for observed, expected, label in relationships:
        if not math.isclose(
            _number(observed, f"{field} {label}"),
            expected,
            rel_tol=0.0,
            abs_tol=2e-12,
        ):
            raise VerificationError(f"{field} {label} does not reconcile to its formula")


def _validate_standalone_explanation(
    payload: Mapping[str, Any],
    *,
    public_ids: set[str],
    held_ids: set[str],
    run_receipts_by_id: Mapping[str, Mapping[str, Any]],
    shortlist: set[str],
    shortlist_variant_by_model: Mapping[str, str],
    candidate_index_sha256: str,
    interaction_registry_sha256: str,
    interaction_context_sha256: str,
    fixture: bool,
) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "queryId",
        "candidateId",
        "candidateTitle",
        "retrievalReasons",
        "affinityContributions",
        "distinctiveFeatures",
        "ignoredDuplicateSignals",
        "unavailableFamilies",
        "comparability",
        "familyContributionUnits",
        "familyContributionShares",
        "broadContainerAttenuation",
        "sourceBiasNotes",
        "interactionEvidence",
        "interactionRegistrySha256",
        "interactionContextSha256",
        "methodId",
        "sourceTreatment",
        "methodVersion",
        "analysisRunId",
        "researchReleaseId",
        "researchReleaseSha256",
        "contextProjectionSha256",
        "spacetimeProjectionSha256",
        "candidateIndexSha256",
        "diagnosticScore",
        "scoreOnlyResult",
        "probability",
        "historicalRelation",
        "semanticRelation",
        "explanationSha256",
    }
    if required - set(payload):
        raise VerificationError(
            f"standalone explanation lacks fields: {sorted(required - set(payload))}"
        )
    if payload.get("schemaVersion") != EXPLANATION_SCHEMA_VERSION:
        raise VerificationError("standalone explanation schema differs")
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if UUID_RE.search(serialized) or EXPLANATION_PRIVATE_RE.search(serialized):
        raise VerificationError("standalone explanation contains private identity or a URL")
    query_id = str(payload.get("queryId", ""))
    candidate_id = str(payload.get("candidateId", ""))
    if (
        query_id == candidate_id
        or not PUBLIC_ID_RE.fullmatch(query_id)
        or not PUBLIC_ID_RE.fullmatch(candidate_id)
        or query_id not in public_ids
        or candidate_id not in public_ids
        or query_id in held_ids
        or candidate_id in held_ids
    ):
        raise VerificationError("standalone explanation is not bound to a distinct public pair")
    _safe_explanation_text(payload.get("candidateTitle"), "candidateTitle")

    retrieval = _explanation_array(payload.get("retrievalReasons"), "retrievalReasons", nonempty=True)
    affinity = _explanation_array(
        payload.get("affinityContributions"), "affinityContributions", nonempty=True
    )
    for row in retrieval:
        _validate_explanation_contribution(row, kind="retrieval")
    for row in affinity:
        _validate_explanation_contribution(row, kind="affinity")
        if str(payload.get("methodId", "")) == "M7":
            _validate_m7_explanation_formula(row, "M7 affinity contribution")
    source_groups = [str(row.get("sameSourceFactGroup", "")) for row in affinity]
    if len(source_groups) != len(set(source_groups)):
        raise VerificationError("standalone explanation repeats a same-source fact group")

    for field in ("distinctiveFeatures", "ignoredDuplicateSignals", "unavailableFamilies", "sourceBiasNotes"):
        values = _explanation_array(payload.get(field), field)
        if field in {"ignoredDuplicateSignals", "unavailableFamilies", "sourceBiasNotes"}:
            for value in values:
                _safe_explanation_text(value, field)
    comparability = payload.get("comparability")
    if not isinstance(comparability, Mapping):
        raise VerificationError("standalone explanation lacks a comparability object")
    observed = _integer(comparability.get("observedFamilyCount"), "explanation observed families")
    eligible = _integer(comparability.get("eligibleFamilyCount"), "explanation eligible families")
    ratio = _number(comparability.get("ratio"), "explanation comparability ratio")
    if observed < 0 or eligible <= 0 or observed > eligible or not math.isclose(
        ratio, observed / eligible, rel_tol=1e-12, abs_tol=1e-12
    ):
        raise VerificationError("standalone explanation comparability does not reconcile")
    unavailable = payload.get("unavailableFamilies")
    if (
        not isinstance(unavailable, list)
        or len(unavailable) != len(set(map(str, unavailable)))
        or len(unavailable) != eligible - observed
    ):
        raise VerificationError("standalone explanation unavailable families do not reconcile")

    raw_units = payload.get("familyContributionUnits")
    raw_shares = payload.get("familyContributionShares")
    if not isinstance(raw_units, Mapping) or not isinstance(raw_shares, Mapping):
        raise VerificationError("standalone explanation lacks family contribution units/shares")
    units = {
        _safe_explanation_text(family, "family contribution unit family"): _number(
            value, f"family contribution unit {family}"
        )
        for family, value in raw_units.items()
    }
    shares = {
        _safe_explanation_text(family, "family contribution share family"): _number(
            value, f"family contribution share {family}"
        )
        for family, value in raw_shares.items()
    }
    if not units or set(units) != set(shares):
        raise VerificationError("family contribution units/shares use different families")
    if any(not 0 <= value <= 1 for value in (*units.values(), *shares.values())):
        raise VerificationError("family contribution unit/share escapes [0,1]")
    diagnostic_score = _number(payload.get("diagnosticScore"), "explanation diagnostic score")
    unit_total = sum(units.values())
    share_total = sum(shares.values())
    if not 0 <= diagnostic_score <= 1 or not math.isclose(
        unit_total, diagnostic_score, rel_tol=0.0, abs_tol=2e-12
    ):
        raise VerificationError("family contribution units do not reconcile to diagnostic score")
    if unit_total > 0:
        if not math.isclose(share_total, 1.0, rel_tol=0.0, abs_tol=2e-12) or any(
            not math.isclose(
                shares[family],
                value / unit_total,
                rel_tol=0.0,
                abs_tol=2e-12,
            )
            for family, value in units.items()
        ):
            raise VerificationError("family contribution shares do not truly derive from units")
    elif share_total != 0:
        raise VerificationError("zero family contribution units have nonzero shares")

    attenuation = payload.get("broadContainerAttenuation")
    if not isinstance(attenuation, Mapping):
        raise VerificationError("standalone explanation lacks broad-container attenuation")
    if attenuation.get("curatorialUse") != "RECALL_SUBSTRATE_ONLY" or attenuation.get(
        "rawCuratedJaccardScoringAllowed"
    ) is not False:
        raise VerificationError("standalone explanation turns raw curation into affinity")
    source_treatment = _safe_explanation_text(payload.get("sourceTreatment"), "sourceTreatment")
    if source_treatment not in {f"SOURCE-{index}" for index in range(5)}:
        raise VerificationError("standalone explanation has an unknown source treatment")
    if source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"} and any(
        str(row.get("family")) == "source" and _number(
            row.get("contribution", 0), "source contribution"
        ) > 0
        for row in affinity
    ):
        raise VerificationError("source-excluded explanation contains positive source affinity")

    interactions = _explanation_array(payload.get("interactionEvidence"), "interactionEvidence")
    top_registry_sha256 = payload.get("interactionRegistrySha256")
    top_context_sha256 = payload.get("interactionContextSha256")
    if interactions:
        if (
            top_registry_sha256 != interaction_registry_sha256
            or top_context_sha256 != interaction_context_sha256
        ):
            raise VerificationError(
                "standalone explanation interaction hashes do not bind the audited context"
            )
    elif top_registry_sha256 is not None or top_context_sha256 is not None:
        raise VerificationError("standalone explanation has interaction hashes without evidence")
    interaction_residuals: list[float] = []
    interaction_aggregate_bonuses: list[float] = []
    interaction_context_hashes: set[str] = set()
    interaction_ids: list[str] = []
    for interaction in interactions:
        if not isinstance(interaction, Mapping):
            raise VerificationError("explanation interaction evidence is not an object")
        interaction_id = str(interaction.get("interactionId", ""))
        if not INTERACTION_ID_RE.fullmatch(interaction_id):
            raise VerificationError("explanation interaction ID is not registry-derived")
        interaction_ids.append(interaction_id)
        if interaction.get("method") not in RESIDUAL_INTERACTION_METHODS:
            raise VerificationError("explanation interaction method is unsupported")
        support = _integer(interaction.get("support"), "explanation interaction support")
        threshold = _integer(
            interaction.get("supportThreshold"), "explanation interaction threshold"
        )
        denominator = _integer(
            interaction.get("denominator"), "explanation interaction denominator"
        )
        if (
            support <= 0
            or threshold not in SUPPORT_THRESHOLDS
            or denominator <= 0
            or support > denominator
        ):
            raise VerificationError("explanation interaction support/denominator is invalid")
        if interaction.get("separateFromParentContributions") is not True or interaction.get(
            "parentContributionRepeated"
        ) is not False:
            raise VerificationError("explanation interaction repeats or obscures parent evidence")
        if interaction.get("positiveExcessAssociationRequired") is not True:
            raise VerificationError("explanation interaction does not require positive excess")
        observed_excess = _bool(
            interaction.get("positiveExcessAssociationObserved"),
            "explanation interaction positive excess",
        )
        residual = _number(interaction.get("residualScore"), "explanation interaction residual")
        raw_residual = _number(
            interaction.get("rawResidualScore"), "explanation raw interaction residual"
        )
        cap = _number(interaction.get("cap"), "explanation interaction cap")
        aggregate_bonus = _number(
            interaction.get("aggregateBonus"), "explanation interaction aggregate bonus"
        )
        if (
            not 0 < cap <= 1
            or not 0 <= residual <= cap + 1e-12
            or not 0 <= raw_residual <= cap + 1e-12
            or not 0 <= aggregate_bonus <= cap + 1e-12
            or ((residual > 0 or raw_residual > 0) and not observed_excess)
            or interaction.get("aggregateResidualNormalized") is not True
        ):
            raise VerificationError("explanation interaction violates positive-excess/cap gating")
        object_ids = interaction.get("objectIds")
        if (
            not isinstance(object_ids, Sequence)
            or isinstance(object_ids, (str, bytes, bytearray))
            or tuple(map(str, object_ids)) != (query_id, candidate_id)
        ):
            raise VerificationError("explanation interaction is not bound to its public pair")
        if interaction.get("registrySha256") != top_registry_sha256:
            raise VerificationError("explanation interaction registry digest conflicts with its payload")
        context_sha256 = str(interaction.get("interactionContextSha256", ""))
        if context_sha256 != top_context_sha256:
            raise VerificationError("explanation interaction-context digest conflicts with its payload")
        parents = interaction.get("parentSignalIds")
        if (
            not isinstance(parents, list)
            or not parents
            or len(parents) != len(set(map(str, parents)))
            or any(not str(value).startswith("SIG-") for value in parents)
        ):
            raise VerificationError("explanation interaction parent lineage is invalid")
        if source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"} and any(
            str(value).startswith("SIG-SOURCE-") for value in parents
        ):
            raise VerificationError("explanation interaction violates its source treatment")
        interaction_context_hashes.add(context_sha256)
        interaction_residuals.append(residual)
        interaction_aggregate_bonuses.append(aggregate_bonus)
        if interaction.get("rareMeansImportant") is not False:
            raise VerificationError("explanation interaction equates rarity with importance")
        for field in ("historicalRelation", "semanticRelation", "probability"):
            if field in interaction and _bool(interaction[field], f"interaction {field}"):
                raise VerificationError("explanation interaction crossed an interpretation boundary")
    if len(interaction_ids) != len(set(interaction_ids)):
        raise VerificationError("standalone explanation repeats an interaction registry row")
    if interactions:
        if len(interaction_context_hashes) != 1:
            raise VerificationError("one explanation mixes trusted interaction contexts")
        aggregate_values = set(interaction_aggregate_bonuses)
        if len(aggregate_values) != 1 or not math.isclose(
            sum(interaction_residuals),
            next(iter(aggregate_values)),
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise VerificationError("explanation interaction residuals do not sum to one aggregate bonus")
        aggregate_bonus = next(iter(aggregate_values))
        if not math.isclose(
            units.get("interactionResidual", 0.0),
            aggregate_bonus,
            rel_tol=0.0,
            abs_tol=2e-12,
        ):
            raise VerificationError("interaction contribution unit does not equal aggregate bonus")
    elif "interactionResidual" in units:
        raise VerificationError("interaction contribution unit exists without interaction evidence")

    method_id = _safe_explanation_text(payload.get("methodId"), "methodId")
    if method_id not in shortlist:
        raise VerificationError("standalone explanation is not tied to a shortlisted method")
    method_version = _safe_explanation_text(payload.get("methodVersion"), "methodVersion")
    analysis_run_id = _safe_explanation_text(payload.get("analysisRunId"), "analysisRunId")
    run_receipt = run_receipts_by_id.get(analysis_run_id)
    if not isinstance(run_receipt, Mapping):
        raise VerificationError("standalone explanation references an unknown analysis run")
    if (
        run_receipt.get("modelId") != method_id
        or run_receipt.get("implementationVersion") != method_version
    ):
        raise VerificationError("standalone explanation method/version differs from its run receipt")
    parameters = run_receipt.get("parameterSet")
    if not isinstance(parameters, Mapping):
        raise VerificationError("standalone explanation run lacks a parameter set")
    if "sourceTreatment" in parameters and parameters.get("sourceTreatment") != source_treatment:
        raise VerificationError("standalone explanation source treatment differs from its run")
    expected_variant = shortlist_variant_by_model.get(method_id)
    if not expected_variant or parameters.get("benchmarkVariantId") != expected_variant:
        raise VerificationError("standalone explanation is not bound to its shortlisted variant")
    release_id = _safe_explanation_text(payload.get("researchReleaseId"), "researchReleaseId")
    if not fixture and release_id != RESEARCH_RELEASE_ID:
        raise VerificationError("standalone explanation changed the frozen research release")
    exact_hashes = {
        "researchReleaseSha256": None if fixture else RESEARCH_RELEASE_SHA256,
        "contextProjectionSha256": None if fixture else CONTEXT_PROJECTION_SHA256,
        "spacetimeProjectionSha256": None if fixture else SPACETIME_PROJECTION_SHA256,
        "candidateIndexSha256": candidate_index_sha256,
    }
    for field, exact in exact_hashes.items():
        value = str(payload.get(field, ""))
        if not SHA256_RE.fullmatch(value) or (exact is not None and value != exact):
            raise VerificationError(f"standalone explanation has an invalid/unpinned {field}")
    receipt_bindings = {
        "researchReleaseId": "researchReleaseId",
        "researchReleaseSha256": "researchReleaseSha256",
        "contextProjectionSha256": "contextProjectionSha256",
        "spacetimeProjectionSha256": "spacetimeProjectionSha256",
        "candidateIndexSha256": "candidateIndexSha256",
    }
    if any(
        payload.get(payload_field) != run_receipt.get(receipt_field)
        for payload_field, receipt_field in receipt_bindings.items()
    ):
        raise VerificationError("standalone explanation provenance differs from its run receipt")
    for field in ("scoreOnlyResult", "probability", "historicalRelation", "semanticRelation"):
        if payload.get(field) is not False:
            raise VerificationError(f"standalone explanation crossed {field}")

    without_hash = dict(payload)
    digest = str(without_hash.pop("explanationSha256"))
    if not SHA256_RE.fullmatch(digest) or digest != _sha256(_canonical_json_bytes(without_hash)):
        raise VerificationError("standalone explanation hash does not bind its payload")
    return {
        "schemaVersion": "trace-exploration-explanation-validation/v1",
        "explanationSha256": digest,
        "retrievalReasonCount": len(retrieval),
        "affinityContributionCount": len(affinity),
        "sameSourceFactGroupCount": len(source_groups),
        "familyContributionShareCount": len(shares),
        "familyContributionSharesReconciled": True,
        "interactionEvidenceCount": len(interactions),
        "comparabilityReconciled": True,
        "sourceTreatmentBoundaryPass": True,
        "rawCuratedScoringBoundaryPass": True,
        "interactionPairBindingPass": True,
        "semanticValidationPass": True,
    }


def _validate_explanation_evidence(
    raw: Mapping[str, Mapping[str, Any]],
    human_table: Table,
    *,
    public_ids: set[str],
    held_ids: set[str],
    runs: Sequence[Mapping[str, Any]],
    shortlist: set[str],
    candidate_index_sha256: str,
    fixture: bool,
    normalized_records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    model_raw = raw["model-benchmark-summary.json"]
    human_raw = raw["human-review-summary.json"]
    model_rows = model_raw.get("explanationRows")
    human_rows = human_raw.get("explanationRows")
    if (
        not isinstance(model_rows, list)
        or not all(isinstance(row, Mapping) for row in model_rows)
        or _canonical_json_bytes(model_rows) != _canonical_json_bytes(human_rows)
    ):
        raise VerificationError("model/human raw evidence lacks one identical bounded explanation set")
    run_receipts_by_id = {str(row["analysisRunId"]): row for row in runs}
    native_model_rows = model_raw.get("modelRows")
    if not isinstance(native_model_rows, list):
        raise VerificationError("model raw evidence lacks native model rows")
    shortlist_native = [
        row
        for row in native_model_rows
        if isinstance(row, Mapping) and row.get("shortlistEligible") is True
    ]
    shortlist_variant_by_model: dict[str, str] = {}
    for row in shortlist_native:
        model_id = str(row.get("modelId", ""))
        if model_id in shortlist_variant_by_model:
            raise VerificationError("model raw evidence selects multiple shortlist variants per model")
        shortlist_variant_by_model[model_id] = str(row.get("variantId", ""))
    if set(shortlist_variant_by_model) != shortlist or any(
        not value for value in shortlist_variant_by_model.values()
    ):
        raise VerificationError("model raw shortlist variants do not reconcile")
    interaction_raw = raw["interaction-summary.json"]
    interaction_registry_sha256 = str(interaction_raw.get("registrySha256", ""))
    interaction_context_sha256 = str(
        interaction_raw.get("trustedInteractionContextSha256", "")
    )
    validation_rows: list[dict[str, Any]] = []
    for row in model_rows:
        validation_rows.append(
            _validate_standalone_explanation(
                row,
                public_ids=public_ids,
                held_ids=held_ids,
                run_receipts_by_id=run_receipts_by_id,
                shortlist=shortlist,
                shortlist_variant_by_model=shortlist_variant_by_model,
                candidate_index_sha256=candidate_index_sha256,
                interaction_registry_sha256=interaction_registry_sha256,
                interaction_context_sha256=interaction_context_sha256,
                fixture=fixture,
            )
        )

    anchor = _header(human_table, "anchor_public_id", "anchorPublicId")
    candidate = _header(human_table, "candidate_public_id", "candidatePublicId")
    packet_pairs = Counter((row[anchor], row[candidate]) for row in human_table.rows)
    explanation_pairs = Counter(
        (str(row["queryId"]), str(row["candidateId"])) for row in model_rows
    )
    if explanation_pairs != packet_pairs:
        raise VerificationError("standalone explanation pairs do not reconcile to the blinded packet")
    if normalized_records is not None:
        source_by_id: dict[str, str] = {}
        for record in normalized_records:
            object_id = str(record.get("objectId", ""))
            source = record.get("source")
            if isinstance(source, Mapping):
                source_id = str(source.get("id", "")).strip()
            else:
                source_id = str(source or "").strip()
            if not object_id or not source_id:
                raise VerificationError("frozen record lacks governed source identity")
            source_by_id[object_id] = source_id
        composition = _header(human_table, "source_composition", "sourceComposition")
        for row in human_table.rows:
            same_source = source_by_id[row[anchor]] == source_by_id[row[candidate]]
            expected = (
                "SAME_GOVERNED_SOURCE_NAME"
                if same_source
                else "CROSS_GOVERNED_SOURCE_NAME"
            )
            if row[composition] != expected:
                raise VerificationError(
                    "human review source composition does not derive from governed records"
                )

    model_validation = model_raw.get("explanationValidation")
    human_validation = human_raw.get("explanationValidation")
    if (
        not isinstance(model_validation, Mapping)
        or _canonical_json_bytes(model_validation) != _canonical_json_bytes(human_validation)
    ):
        raise VerificationError("model/human explanation-validation receipts differ")
    count = len(model_rows)
    expected_counts = {
        "explanationCount": count,
        "retrievalPathCount": count,
        "affinityEvidencePathCount": count,
        "comparabilityValidCount": count,
        "provenancePinnedCount": count,
        "invalidExplanationCount": 0,
        "scoreOnlyResultCount": 0,
        "historicalRelationCount": 0,
        "semanticRelationCount": 0,
        "probabilityCount": 0,
    }
    for field, expected in expected_counts.items():
        if _integer(model_validation.get(field), f"explanation validation {field}") != expected:
            raise VerificationError(f"explanation validation count differs: {field}")
    for field in (
        "explanationContractReady",
        "standaloneSemanticValidationPassed",
        "contributionSchemaValid",
    ):
        if not _bool(model_validation.get(field), f"explanation validation {field}"):
            raise VerificationError(f"explanation validation did not pass {field}")
    explanation_rows_sha256 = str(model_validation.get("explanationRowsSha256", ""))
    if explanation_rows_sha256 != _sha256(_canonical_json_bytes(model_rows)):
        raise VerificationError("explanation validation digest does not bind the standalone rows")
    validation_rows_sha256 = str(
        model_validation.get("explanationValidationRowsSha256", "")
    )
    if validation_rows_sha256 != _sha256(_canonical_json_bytes(validation_rows)):
        raise VerificationError(
            "explanation validation-row digest does not bind independent semantic receipts"
        )
    return {"explanationCount": count, "explanationRowsSha256": explanation_rows_sha256}


RUN_FIELDS = (
    "schemaVersion",
    "modelId",
    "modelFamily",
    "implementationVersion",
    "parameterSet",
    "sourceCommit",
    "researchReleaseId",
    "researchReleaseSha256",
    "researchManifestSha256",
    "contextProjectionId",
    "contextProjectionSha256",
    "spacetimeProjectionId",
    "spacetimeProjectionSha256",
    "explorationSignalRegistrySha256",
    "candidateIndexSha256",
    "inputCohortCount",
    "executionSeed",
    "outputSummarySha256",
    "topKArtifactSha256",
    "randomnessAffectsAffinity",
    "randomnessAffectsCandidateSet",
    "fullPairMatrixMaterialized",
    "historicalRelation",
    "semanticRelation",
    "probability",
    "generatedAt",
    "timestampExcludedFromDeterministicHash",
    "analysisRunId",
    "receiptSha256",
)


def _run_receipt_from_row(table: Table, row: Mapping[str, str]) -> dict[str, Any]:
    receipt_column = _optional_header(table, "receipt_json", "receiptJson")
    if receipt_column:
        value = _json_cell(row[receipt_column], "analysis run receipt_json")
        if not isinstance(value, Mapping):
            raise VerificationError("analysis run receipt_json is not an object")
        return dict(value)
    result: dict[str, Any] = {}
    for field in RUN_FIELDS:
        key = _header(table, field)
        value: Any = row[key]
        if field == "parameterSet":
            value = _json_cell(value, "analysis run parameterSet")
        elif field in {
            "randomnessAffectsAffinity",
            "randomnessAffectsCandidateSet",
            "fullPairMatrixMaterialized",
            "historicalRelation",
            "semanticRelation",
            "probability",
            "timestampExcludedFromDeterministicHash",
        }:
            value = _bool(value, f"analysis run {field}")
        elif field == "inputCohortCount":
            value = _integer(value, "analysis run input cohort")
        elif field == "executionSeed":
            value = None if not str(value).strip() or str(value).strip().lower() == "null" else _integer(value, "execution seed")
        result[field] = value
    return result


def _validate_run_receipt(receipt: Mapping[str, Any], *, fixture: bool) -> None:
    if set(RUN_FIELDS) - set(receipt):
        raise VerificationError("analysis run receipt lacks required fields")
    if receipt["sourceCommit"] != SOURCE_SHA or _integer(receipt["inputCohortCount"], "run input cohort") != PUBLIC_OBJECT_COUNT:
        raise VerificationError("analysis run is not source/cohort pinned")
    for field in (
        "researchReleaseSha256",
        "researchManifestSha256",
        "contextProjectionSha256",
        "spacetimeProjectionSha256",
        "explorationSignalRegistrySha256",
        "candidateIndexSha256",
        "outputSummarySha256",
        "topKArtifactSha256",
        "receiptSha256",
    ):
        if not SHA256_RE.fullmatch(str(receipt[field])):
            raise VerificationError(f"analysis run has an invalid {field}")
    if not fixture:
        exact_pins = {
            "researchReleaseId": RESEARCH_RELEASE_ID,
            "researchReleaseSha256": RESEARCH_RELEASE_SHA256,
            "researchManifestSha256": RESEARCH_RELEASE_SHA256,
            "contextProjectionId": CONTEXT_PROJECTION_ID,
            "contextProjectionSha256": CONTEXT_PROJECTION_SHA256,
            "spacetimeProjectionId": SPACETIME_PROJECTION_ID,
            "spacetimeProjectionSha256": SPACETIME_PROJECTION_SHA256,
            "explorationSignalRegistrySha256": EXPLORATION_SIGNAL_REGISTRY_SHA256,
        }
        changed = {
            field: (receipt.get(field), expected)
            for field, expected in exact_pins.items()
            if receipt.get(field) != expected
        }
        if changed:
            raise VerificationError(f"analysis run changed a frozen release/projection/signal pin: {changed}")
    for field in (
        "randomnessAffectsAffinity",
        "randomnessAffectsCandidateSet",
        "fullPairMatrixMaterialized",
        "historicalRelation",
        "semanticRelation",
        "probability",
    ):
        if _bool(receipt[field], f"run {field}"):
            raise VerificationError(f"analysis run crossed {field} boundary")
    if not _bool(receipt["timestampExcludedFromDeterministicHash"], "timestamp exclusion"):
        raise VerificationError("analysis timestamp is not excluded from deterministic material")
    excluded = {"generatedAt", "timestampExcludedFromDeterministicHash", "receiptSha256", "analysisRunId"}
    material = {key: value for key, value in receipt.items() if key not in excluded}
    expected = _sha256(_canonical_json_bytes(material))
    if receipt["receiptSha256"] != expected or receipt["analysisRunId"] != f"EXP-RUN:{expected}":
        raise VerificationError("analysis run deterministic hash binding differs")


def _validate_runs(
    table: Table,
    raw_summary: Mapping[str, Any],
    *,
    fixture: bool,
) -> list[dict[str, Any]]:
    receipts = [_run_receipt_from_row(table, row) for row in table.rows]
    if not receipts:
        raise VerificationError("analysis run register is empty")
    for receipt in receipts:
        _validate_run_receipt(receipt, fixture=fixture)
    run_model_ids = {str(row["modelId"]) for row in receipts}
    if not MODEL_IDS.issubset(run_model_ids) or any(not value.strip() for value in run_model_ids):
        raise VerificationError("analysis run register lacks one or more M0..M8 benchmark families")
    for receipt in receipts:
        run_id = str(receipt["modelId"])
        if run_id in MODEL_IDS:
            continue
        if not run_id.startswith("EVAL-") or receipt.get("modelFamily") != "ANALYSIS_SUBEXPERIMENT":
            raise VerificationError(
                "non-model analysis run must use EVAL-* and modelFamily=ANALYSIS_SUBEXPERIMENT"
            )
    ids = [str(row["analysisRunId"]) for row in receipts]
    if len(ids) != len(set(ids)):
        raise VerificationError("analysis run IDs are duplicated")
    raw_rows = raw_summary.get("rows", raw_summary.get("receipts"))
    if not isinstance(raw_rows, list) or len(raw_rows) != len(receipts):
        raise VerificationError("analysis-run raw summary does not reconcile with the TSV")
    raw_by_id = {str(row.get("analysisRunId")): row for row in raw_rows if isinstance(row, Mapping)}
    for receipt in receipts:
        if raw_by_id.get(str(receipt["analysisRunId"])) != receipt:
            raise VerificationError("analysis-run raw receipt differs from the TSV")
    if _integer(raw_summary.get("analysisRunCount"), "raw analysis run count") != len(receipts):
        raise VerificationError("analysis-run raw count differs from its rows")
    if _integer(raw_summary.get("receiptFailureCount"), "raw receipt failure count") != 0:
        raise VerificationError("analysis-run raw summary reports a receipt failure")
    register_digest = raw_summary.get("registerSha256")
    expected_register = _sha256(
        _canonical_json_bytes(
            {
                "schemaVersion": raw_summary.get("schemaVersion"),
                "receiptSha256": [str(row["receiptSha256"]) for row in raw_rows],
            }
        )
    )
    if register_digest != expected_register:
        raise VerificationError("analysis-run register SHA-256 binding differs")
    return receipts


def _validate_tsv_shapes(
    research_dir: Path,
    documents: Sequence[Mapping[str, Any]],
    raw: Mapping[str, Mapping[str, Any]],
    public_ids: set[str],
    held_ids: set[str],
    *,
    fixture: bool,
) -> tuple[dict[str, Table], dict[str, Any]]:
    tables = {name: _parse_tsv(research_dir / name) for name in RESEARCH_TSV_FILES}
    if len(tables) != 11:
        raise VerificationError("research package must contain exactly 11 TSVs")
    lineage = _validate_lineage(tables["03_SIGNAL_LINEAGE_REGISTRY.tsv"])
    _validate_lineage_and_basis_raw(
        tables["03_SIGNAL_LINEAGE_REGISTRY.tsv"],
        lineage,
        raw["signal-lineage-summary.json"],
        raw["independent-basis-summary.json"],
    )
    shortlist = set(_split_ids(_evidence(documents, ("shortlistModelIds", "modelShortlistIds"), "shortlist model IDs")))
    if len(shortlist) > 3 or not shortlist.issubset(MODEL_IDS - {"M0"}):
        raise VerificationError("model shortlist is invalid or exceeds three models")
    _validate_curatorial(tables["07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv"])
    models = _validate_models(
        tables["10_MODEL_BENCHMARK_RESULTS.tsv"],
        shortlist,
        raw["model-benchmark-summary.json"],
    )
    _validate_candidates(
        tables["11_CANDIDATE_RECALL_RESULTS.tsv"],
        shortlist,
        raw["candidate-index-summary.json"],
    )
    _validate_bias(tables["12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv"], shortlist)
    _validate_hubness(tables["13_HUBNESS_ANALYSIS.tsv"], shortlist)
    _validate_ablations(tables["14_ABLATION_AND_STABILITY.tsv"])
    _validate_interactions(
        tables["15_INTERACTION_STATISTICS_REVIEW.tsv"],
        raw["interaction-summary.json"],
        raw["candidate-index-summary.json"],
    )
    _validate_mechanical(tables["16_MECHANICAL_EXPECTATION_CASES.tsv"], shortlist)
    _validate_human_review(tables["17_HUMAN_REVIEW_PACKET.tsv"], public_ids, held_ids)
    runs = _validate_runs(
        tables["19_ANALYSIS_RUN_REGISTER.tsv"],
        raw["analysis-run-summary.json"],
        fixture=fixture,
    )
    return tables, {"lineage": lineage, "shortlist": shortlist, "models": models, "runs": runs}


def _load_eligibility(
    repo_root: Path,
) -> tuple[set[str], set[str], tuple[Mapping[str, Any], ...]]:
    import importlib.util

    module_path = repo_root / "scripts/exploration-v49-analysis/common.py"
    spec = importlib.util.spec_from_file_location("_trace_round5_common_for_similarity_verifier", module_path)
    if spec is None or spec.loader is None:
        raise VerificationError("cannot load the frozen Round 5 input verifier")
    round5_common = importlib.util.module_from_spec(spec)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(round5_common)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    frozen_receipts = round5_common.verify_frozen_inputs()
    public_ids, held_ids = round5_common.load_eligibility()
    normalized = round5_common.load_normalized_public_records()
    records = normalized.get("records")
    if len(public_ids) != PUBLIC_OBJECT_COUNT or len(held_ids) != 7_928 or public_ids & held_ids:
        raise VerificationError("frozen eligibility ledger does not reconcile")
    if not isinstance(frozen_receipts, Mapping) or len(frozen_receipts) < 8:
        raise VerificationError("frozen source/projection receipts are incomplete")
    if (
        not isinstance(records, list)
        or len(records) != PUBLIC_OBJECT_COUNT
        or {str(row.get("objectId", "")) for row in records if isinstance(row, Mapping)}
        != set(public_ids)
    ):
        raise VerificationError("frozen normalized public cohort does not reconcile to eligibility")
    return set(public_ids), set(held_ids), tuple(records)


def _scan_bytes_for_private_values(paths: Iterable[Path], held_ids: set[str]) -> None:
    for path in paths:
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VerificationError(f"committed artifact is not UTF-8: {path}") from error
        if UUID_RE.search(text):
            raise VerificationError(f"internal UUID appears in committed artifact: {path.name}")
        if PRIVATE_ID_RE.search(text):
            raise VerificationError(f"raw private identifier appears in committed artifact: {path.name}")
        if held_ids and (set(PUBLIC_ID_TOKEN_RE.findall(text)) & held_ids):
            raise VerificationError(f"held identifier appears in committed artifact: {path.name}")


def _static_assignment(path: Path, name: str) -> Any:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return ast.literal_eval(node.value)
    raise VerificationError(f"{path.name} lacks static assignment {name}")


def _python_negative_control_references(path: Path) -> list[str]:
    """Return AST-proven negative-control imports/references in one Python file."""

    import ast

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    findings: list[str] = []

    def negative_module(value: str | None) -> bool:
        if not value:
            return False
        normalized = value.casefold().replace("-", "_")
        return normalized == "negative_control" or normalized.endswith(".negative_control")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if negative_module(alias.name):
                    findings.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if negative_module(node.module) or any(negative_module(alias.name) for alias in node.names):
                findings.append(f"line {node.lineno}: from-import negative_control")
        elif isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
            function_name = ""
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            if function_name in {"__import__", "import_module"} and isinstance(node.args[0].value, str):
                if negative_module(node.args[0].value):
                    findings.append(f"line {node.lineno}: dynamic import {node.args[0].value}")
        elif isinstance(node, ast.Name) and _normalize_key(node.id) == "rawcuratedjaccard":
            findings.append(f"line {node.lineno}: raw curated Jaccard reference")
        elif isinstance(node, ast.Attribute) and _normalize_key(node.attr) == "rawcuratedjaccard":
            findings.append(f"line {node.lineno}: raw curated Jaccard attribute")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and negative_module(node.value):
            findings.append(f"line {node.lineno}: negative-control module literal")
    return sorted(set(findings))


def _javascript_negative_control_references(path: Path) -> list[str]:
    """Return literal ESM/CommonJS/dynamic-import violations in JS/TS source."""

    source = path.read_text(encoding="utf-8")
    specifier_pattern = re.compile(
        r"(?:\bimport\s*(?:[^;\n]*?\sfrom\s*)?|\bexport\s+[^;\n]*?\sfrom\s*|"
        r"\brequire\s*\(|\bimport\s*\()\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    findings: list[str] = []
    for match in specifier_pattern.finditer(source):
        specifier = match.group(1).casefold().replace("-", "_")
        stem = re.sub(r"\.(?:[cm]?[jt]sx?|py)$", "", specifier)
        if stem == "negative_control" or stem.endswith("/negative_control") or stem.endswith(".negative_control"):
            line = source.count("\n", 0, match.start()) + 1
            findings.append(f"line {line}: import {match.group(1)}")
    # Also catch literal specifiers passed through a local alias of require or
    # import helpers.  This is deliberately conservative in production roots:
    # a negative-control module literal has no legitimate runtime purpose.
    module_literal_pattern = re.compile(
        r"(?P<quote>['\"`])(?P<value>[^'\"`\r\n]*negative[_-]control(?:\.[^'\"`\r\n]*)?)(?P=quote)",
        re.IGNORECASE,
    )
    for match in module_literal_pattern.finditer(source):
        line = source.count("\n", 0, match.start()) + 1
        findings.append(f"line {line}: negative-control module literal")
    raw_pattern = re.compile(r"\braw[_-]?curated[_-]?jaccard\b", re.IGNORECASE)
    for match in raw_pattern.finditer(source):
        line = source.count("\n", 0, match.start()) + 1
        findings.append(f"line {line}: raw curated Jaccard reference")
    return sorted(set(findings))


def _validate_negative_control_import_boundary(repo_root: Path) -> None:
    negative = repo_root / "scripts/exploration-v49-similarity/negative_control.py"
    if not negative.is_file():
        raise VerificationError("isolated negative_control.py is absent")
    expected = {
        "MODEL_ID": "M0",
        "ANALYSIS_ONLY": True,
        "SCORING_ALLOWED": False,
        "SHORTLIST_ELIGIBLE": False,
        "PRODUCTION_IMPORT_ALLOWED": False,
    }
    for name, value in expected.items():
        if _static_assignment(negative, name) != value:
            raise VerificationError(f"negative control boundary differs: {name}")
    scorer_paths = (
        repo_root / "scripts/exploration-v49-similarity/model_baselines.py",
        repo_root / "scripts/exploration-v49-similarity/candidate_index.py",
        repo_root / "scripts/exploration-v49-similarity/explanation.py",
    )
    for path in scorer_paths:
        findings = _python_negative_control_references(path)
        if findings:
            raise VerificationError(
                f"analysis scorer imports/references the M0 negative control: {path.name}: {findings}"
            )
    production_roots = (
        repo_root / "frontend/src",
        repo_root / "frontend/scripts",
        repo_root / "database/functions",
        repo_root / "generated",
    )
    suffixes = {".py", ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
    for root in production_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            findings = (
                _python_negative_control_references(path)
                if path.suffix == ".py"
                else _javascript_negative_control_references(path)
            )
            if findings:
                raise VerificationError(
                    "production/frontend code imports/references the M0 negative control: "
                    f"{path.relative_to(repo_root)}: {findings}"
                )


def _git_changed_paths(repo_root: Path) -> set[str]:
    excluded_lfs = ":(exclude)generated/public_surfaces_prefreeze_candidate_v48.json"
    command = [
        "git",
        "diff",
        "--name-only",
        SOURCE_SHA,
        "--",
        ".",
        excluded_lfs,
    ]
    result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise VerificationError(f"cannot inspect changed-file boundary: {result.stderr.strip()}")
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if untracked.returncode != 0:
        raise VerificationError(f"cannot inspect untracked-file boundary: {untracked.stderr.strip()}")
    return {line.strip() for line in (result.stdout + "\n" + untracked.stdout).splitlines() if line.strip()}


def _validate_changed_file_boundary(repo_root: Path, *, fixture: bool) -> set[str]:
    if fixture:
        return set()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_SHA, "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if ancestry.returncode != 0:
        raise VerificationError("required Round 5 source commit is not an ancestor of HEAD")
    changed = _git_changed_paths(repo_root)
    research_prefix = "docs/research/trace-v49-exploration-similarity-round1/"
    audit_prefix = "docs/audits/v49-exploration-similarity-round1/"
    script_prefix = "scripts/exploration-v49-similarity/"
    allowed = {
        path
        for path in changed
        if path == "PROJECT_LOG.md"
        or path.startswith(research_prefix)
        or path.startswith(audit_prefix)
        or path.startswith(script_prefix)
    }
    unexpected = changed - allowed
    if unexpected:
        raise VerificationError(f"protected project files changed: {sorted(unexpected)}")
    if any("__pycache__" in path or path.endswith((".pyc", ".pyo")) for path in changed):
        raise VerificationError("compiled Python cache entered the changed-file set")
    for prefix in ("frontend/", "database/", "generated/", "docs/api/"):
        if any(path.startswith(prefix) for path in changed):
            raise VerificationError(f"protected {prefix} boundary changed")
    return changed


def _validate_no_pair_matrix(paths: Iterable[Path], raw: Mapping[str, Mapping[str, Any]]) -> None:
    forbidden_name = re.compile(r"(?:full[-_]?pair|pair[-_]?matrix|all[-_]?pairs|pair[-_]?rows?\.(?:csv|tsv|json|parquet))", re.IGNORECASE)
    for path in paths:
        if forbidden_name.search(path.name) or path.suffix.casefold() in {".parquet", ".feather", ".sqlite", ".db"}:
            raise VerificationError(f"unbounded pair artifact is committed: {path.name}")
    for filename, document in raw.items():
        for key, value in _walk(document):
            normalized = _normalize_key(key)
            pair_row_storage_key = normalized in {
                "pairrows",
                "pairrowsmaterialized",
                "pairrowsretained",
                "pairrowsemitted",
                "pairrowsstored",
                "pairrowscommitted",
            }
            matrix_key = "pairmatrix" in normalized or normalized in {"allpairs", "allpairrows"}
            if pair_row_storage_key or matrix_key:
                if isinstance(value, list) and value:
                    raise VerificationError(f"{filename} materializes pair rows")
                if pair_row_storage_key and _integer(value, f"{filename}.{key}") != 0:
                    raise VerificationError(f"{filename} reports materialized pair rows")
                if matrix_key and _bool(value, f"{filename}.{key}"):
                    raise VerificationError(f"{filename} reports a full pair matrix")


def _validate_aggregate_contract(
    documents: Sequence[Mapping[str, Any]],
    table_context: Mapping[str, Any],
    tables: Mapping[str, Table],
) -> dict[str, Any]:
    if str(_evidence(documents, ("sourceCommit", "sourceSha"), "source commit")) != SOURCE_SHA:
        raise VerificationError("aggregate source commit differs")
    if _integer(_evidence(documents, ("publicObjectCount",), "public object count"), "public object count") != PUBLIC_OBJECT_COUNT:
        raise VerificationError("public object count differs")
    if _integer(
        _evidence(documents, ("heldExplorationObjectCount", "heldObjectsInEvaluation", "heldObjectsIncluded"), "held Exploration count"),
        "held Exploration count",
    ) != 0:
        raise VerificationError("held objects entered Exploration evaluation")
    if _integer(_evidence(documents, ("exhaustivePairCount",), "exhaustive pair count"), "exhaustive pair count") != EXHAUSTIVE_PAIR_COUNT:
        raise VerificationError("exhaustive pair count differs")
    if _integer(_evidence(documents, ("signalInputCount", "explorationSignalInputCount"), "signal input count"), "signal input count") != SIGNAL_COUNT:
        raise VerificationError("signal input count differs")
    if _integer(_evidence(documents, ("signalLineageClassifiedCount", "classifiedCount"), "classified signal count"), "classified signal count") != SIGNAL_COUNT:
        raise VerificationError("classified signal count differs")
    _require_zero(documents, ("signalLineageUnclassifiedCount", "unclassifiedCount"), "unclassified signal count")
    disposition_fields = {
        "INDEPENDENT_BASE_SIGNAL": ("independentBaseSignalCount",),
        "DEPENDENT_INTERACTION_SIGNAL": ("dependentInteractionSignalCount",),
        "CANDIDATE_GENERATION_ONLY": ("candidateGenerationOnlySignalCount",),
        "COMPARABILITY_ONLY": ("comparabilityOnlySignalCount",),
        "EXPLANATION_ONLY": ("explanationOnlySignalCount",),
        "DIAGNOSTIC_ONLY": ("diagnosticOnlySignalCount",),
        "REJECT": ("rejectedScoringSignalCount",),
    }
    for disposition, aliases in disposition_fields.items():
        actual = _integer(
            _evidence(documents, aliases, f"{disposition} count"),
            f"{disposition} count",
        )
        expected = table_context["lineage"]["dispositions"].get(disposition, 0)
        if actual != expected:
            raise VerificationError(f"lineage disposition count differs for {disposition}")
    if _integer(
        _evidence(documents, ("sameSourceFactGroupCount",), "same-source fact group count"),
        "same-source fact group count",
    ) != len(table_context["lineage"]["sameSourceFactGroups"]):
        raise VerificationError("same-source fact group count differs")
    if _integer(_evidence(documents, ("candidateGeneratorVariantCount", "candidateVariantCount"), "candidate variant count"), "candidate variant count") != 6:
        raise VerificationError("candidate variant count differs")
    candidate_selected = _bool(
        _evidence(documents, ("candidateArchitectureSelected",), "candidate architecture selected"),
        "candidate architecture selected",
    )
    selected_variant = str(
        _evidence(
            documents,
            ("selectedCandidateVariant", "candidateArchitectureVariant", "candidateArchitectureId"),
            "selected candidate variant",
        )
    )
    if candidate_selected and selected_variant not in CANDIDATE_VARIANTS:
        raise VerificationError("selected candidate architecture is not CG-CUR-1..6")
    if not candidate_selected and selected_variant not in {"", "NONE", "N/A", "NOT_SELECTED"}:
        raise VerificationError("unselected candidate architecture names a selected variant")
    pool_values = [
        _number(
            _evidence(documents, aliases, label),
            label,
        )
        for aliases, label in (
            (("selectedCandidatePoolP50", "candidatePoolP50"), "selected candidate pool p50"),
            (("selectedCandidatePoolP95", "candidatePoolP95"), "selected candidate pool p95"),
            (("selectedCandidatePoolP99", "candidatePoolP99"), "selected candidate pool p99"),
            (("selectedCandidatePoolMax", "candidatePoolMax"), "selected candidate pool max"),
        )
    ]
    if pool_values != sorted(pool_values) or not 0 <= pool_values[0] <= pool_values[-1] <= OTHER_PUBLIC_OBJECT_COUNT:
        raise VerificationError("selected candidate pool distribution is invalid")
    for aliases, label in (
        (("selectedCandidateRecallAt10", "candidateRecallAt10"), "candidate recall@10"),
        (("selectedCandidateRecallAt20", "candidateRecallAt20"), "candidate recall@20"),
        (("selectedCandidateRecallAt50", "candidateRecallAt50"), "candidate recall@50"),
    ):
        value = _number(_evidence(documents, aliases, label), label)
        if not 0 <= value <= 1:
            raise VerificationError(f"{label} escapes [0,1]")
    for aliases, label in (
        (("zeroCandidateObjectCount",), "zero-candidate object count"),
        (("nearFullCorpusCandidateObjectCount", "nearFullCandidateObjectCount"), "near-full candidate object count"),
    ):
        value = _integer(_evidence(documents, aliases, label), label)
        if not 0 <= value <= PUBLIC_OBJECT_COUNT:
            raise VerificationError(f"{label} escapes the public cohort")
    model_ids = set(_split_ids(_evidence(documents, ("modelIds", "benchmarkModelIds"), "model IDs")))
    if model_ids != MODEL_IDS:
        raise VerificationError("aggregate model ID registry differs")
    decision = str(_evidence(documents, ("modelDecision",), "model decision"))
    if decision not in MODEL_DECISIONS:
        raise VerificationError("model decision is outside the Round 6 gate")
    shortlist = table_context["shortlist"]
    if decision == "NO_MODEL_SELECTED" and shortlist:
        raise VerificationError("NO_MODEL_SELECTED conflicts with a nonempty shortlist")
    if decision != "NO_MODEL_SELECTED" and not shortlist:
        raise VerificationError("selected/shortlisted decision lacks a shortlist")
    if _integer(_evidence(documents, ("modelShortlistCount", "shortlistModelCount"), "shortlist count"), "shortlist count") != len(shortlist):
        raise VerificationError("shortlist count does not reconcile")
    model_table = tables["10_MODEL_BENCHMARK_RESULTS.tsv"]
    variant_header = _header(model_table, "variant_id", "variantId")
    model_variant_count = len({row[variant_header] for row in model_table.rows})
    if _integer(_evidence(documents, ("modelVariantCount",), "model variant count"), "model variant count") != model_variant_count:
        raise VerificationError("model variant count does not reconcile")
    if _integer(_evidence(documents, ("curatorialAttenuationVariantCount", "curatorialVariantCount"), "curatorial variant count"), "curatorial variant count") != 6:
        raise VerificationError("curatorial attenuation variant count differs")
    residual_count = _integer(
        _evidence(documents, ("curatorialResidualSignalCount", "residualSignalCount"), "curatorial residual signal count"),
        "curatorial residual signal count",
    )
    if residual_count < 0:
        raise VerificationError("curatorial residual signal count is negative")
    if residual_count == 0 and _bool(
        _evidence(documents, ("curatorialAsIndependentScore",), "curatorial independent score"),
        "curatorial independent score",
    ):
        raise VerificationError("zero residual curation became an independent score")
    _bool(_evidence(documents, ("curatorialAsRecallIndex",), "curatorial recall index"), "curatorial recall index")
    if _integer(_evidence(documents, ("missingnessVariantCount",), "missingness variant count"), "missingness variant count") != 4:
        raise VerificationError("missingness variant count differs")
    if set(_split_ids(_evidence(documents, ("missingnessVariantIds",), "missingness variant IDs"))) != MISSINGNESS_VARIANTS:
        raise VerificationError("missingness variant registry differs")
    comparability_p50 = _number(
        _evidence(documents, ("comparabilityP50",), "comparability p50"),
        "comparability p50",
    )
    comparability_p95 = _number(
        _evidence(documents, ("comparabilityP95",), "comparability p95"),
        "comparability p95",
    )
    if not 0 <= comparability_p50 <= comparability_p95 <= 1:
        raise VerificationError("comparability distribution is invalid")
    if _integer(_evidence(documents, ("interactionMethodCount",), "interaction method count"), "interaction method count") != len(INTERACTION_METHODS):
        raise VerificationError("interaction method count differs")
    if _integer(_evidence(documents, ("interactionSupportThresholdCount", "supportThresholdCount"), "interaction support threshold count"), "interaction support threshold count") != len(SUPPORT_THRESHOLDS):
        raise VerificationError("interaction support threshold count differs")
    if set(_integer(value, "hubness k") for value in _evidence(documents, ("hubnessKValues", "kValues"), "hubness k values")) != HUBNESS_K_VALUES:
        raise VerificationError("hubness k registry differs")
    _bool(_evidence(documents, ("hubnessCorrectionTested",), "hubness correction tested"), "hubness correction tested")
    correction_selected = _bool(
        _evidence(documents, ("hubnessCorrectionSelected",), "hubness correction selected"),
        "hubness correction selected",
    )
    correction_tested = _bool(
        _evidence(documents, ("hubnessCorrectionTested",), "hubness correction tested"),
        "hubness correction tested",
    )
    if correction_selected and not correction_tested:
        raise VerificationError("hubness correction was selected without being tested")
    if _integer(_evidence(documents, ("mechanicalAxiomCount", "axiomCount"), "mechanical axiom count"), "mechanical axiom count") != 15:
        raise VerificationError("mechanical axiom count differs")
    _require_zero(documents, ("mechanicalAxiomFailureCount", "axiomFailureCount"), "mechanical axiom failures")
    ablation_table = tables["14_ABLATION_AND_STABILITY.tsv"]
    ablation_model = _header(ablation_table, "model_id", "modelId")
    ablation_id = _header(ablation_table, "ablation_id", "ablationId")
    observed_ablation_variants = len({(row[ablation_model], row[ablation_id]) for row in ablation_table.rows})
    if _integer(_evidence(documents, ("ablationVariantCount",), "ablation variant count"), "ablation variant count") != observed_ablation_variants:
        raise VerificationError("ablation variant count does not reconcile")
    if _integer(_evidence(documents, ("pathologicalAnchorCount", "pathologicalCaseCount"), "pathological anchor count"), "pathological anchor count") != 15:
        raise VerificationError("pathological anchor count differs")
    if _integer(_evidence(documents, ("humanReviewPacketAnchorCount", "humanReviewAnchorCount", "anchorCount"), "human review anchor count"), "human review anchor count") != HUMAN_REVIEW_ANCHOR_COUNT:
        raise VerificationError("human review anchor count differs")
    if not _bool(_evidence(documents, ("humanReviewPacketReady",), "human review readiness"), "human review readiness"):
        raise VerificationError("human review packet is not ready")
    _require_false(documents, ("humanReviewCompleted",), "human review completed")
    if _integer(_evidence(documents, ("analysisRunCount",), "analysis run count"), "analysis run count") != len(table_context["runs"]):
        raise VerificationError("analysis run count does not reconcile")
    _require_zero(documents, ("analysisRunReceiptFailureCount", "receiptFailureCount"), "analysis receipt failures")
    candidate_index_hash = str(_evidence(documents, ("candidateIndexSha256",), "candidate index SHA-256"))
    if not SHA256_RE.fullmatch(candidate_index_hash) or {
        str(receipt["candidateIndexSha256"]) for receipt in table_context["runs"]
    } != {candidate_index_hash}:
        raise VerificationError("analysis runs do not reconcile to one candidate-index hash")
    for aliases, label in (
        (("candidateIndexBuildMs",), "candidate index build ms"),
        (("candidateIndexBytes",), "candidate index bytes"),
        (("candidateIndexHeapBytes",), "candidate index heap bytes"),
        (("exhaustiveModelBenchmarkMs",), "exhaustive model benchmark ms"),
        (("objectLocalQueryP50Ms",), "object-local query p50 ms"),
        (("objectLocalQueryP95Ms",), "object-local query p95 ms"),
        (("peakHeapBytes",), "peak heap bytes"),
        (("peakRssBytes",), "peak RSS bytes"),
    ):
        if _number(_evidence(documents, aliases, label), label) < 0:
            raise VerificationError(f"{label} is negative")
    for aliases, label in (
        (("sameSourceFactDoubleScoreCount",), "same-source double score count"),
        (("curatorialParentDuplicationFailureCount", "sameSourceParentDuplicationFailures"), "curatorial parent duplication failures"),
        (("sharedUnknownPositiveCreditCount",), "shared unknown positive credit"),
        (("notApplicableAsMissingCount",), "not-applicable-as-missing count"),
        (("lowSupportInflationFailureCount", "lowSupportInflationFailures"), "low-support inflation failures"),
        (("interactionParentDoubleCountFailures",), "interaction parent double-count failures"),
        (("unexplainedShortlistResultCount",), "unexplained shortlist results"),
        (("scoreOnlyResultCount",), "score-only explanation results"),
        (("historicalRelationCount",), "historical-relation explanation results"),
        (("semanticRelationCount",), "semantic-relation explanation results"),
        (("probabilityCount",), "probability explanation results"),
        (("internalUuidExposureCount", "internalUuidCount"), "internal UUID exposure"),
        (("databaseFilesChanged",), "database files changed"),
        (("searchFilesChanged",), "search files changed"),
    ):
        _require_zero(documents, aliases, label)
    for aliases, label in (
        (("publicSimilarityModelSelected",), "public similarity model selected"),
        (("publicSimilarityWeightsSelected", "publicWeightsSelected"), "public similarity weights selected"),
        (("probabilityModelSelected",), "probability model selected"),
        (("clusteringModelSelected",), "clustering model selected"),
        (("randomnessAffectsAffinity",), "randomness affects affinity"),
        (("randomnessAffectsCandidateSet",), "randomness affects candidate set"),
        (("fullPairMatrixCommitted",), "full pair matrix committed"),
        (("fullPairMatrixInClient",), "full pair matrix in client"),
        (("canonicalReleaseChanged",), "canonical release changed"),
        (("contextSemanticsChanged",), "Context semantics changed"),
        (("contextGovernanceChanged",), "Context governance changed"),
        (("contextPublicProjectionChanged",), "Context public projection changed"),
        (("spacetimeGovernanceChanged",), "Spacetime governance changed"),
        (("spacetimePublicProjectionChanged",), "Spacetime public projection changed"),
        (("publicExplorationApiAdded",), "public Exploration API added"),
        (("publicExplorationRouteAdded",), "public Exploration route added"),
        (("explorationRendererImplemented",), "Exploration renderer implemented"),
        (("explorationTemplateRegistryFrozen",), "Exploration template registry frozen"),
    ):
        _require_false(documents, aliases, label)
    _require_false(
        documents,
        ("rawCuratedJaccardProductionEligible", "rawCuratedJaccardIsProductionEligible"),
        "raw curated Jaccard production eligibility",
    )
    if str(_evidence(documents, ("rawCuratedJaccardImportBoundary",), "raw-curation import boundary")).upper() != "PASS":
        raise VerificationError("raw-curation import boundary is not PASS")
    if not _bool(_evidence(documents, ("comparabilityChannelImplemented",), "comparability channel"), "comparability channel"):
        raise VerificationError("comparability channel is not implemented")
    if not _bool(_evidence(documents, ("explanationContractReady",), "explanation contract"), "explanation contract"):
        raise VerificationError("explanation contract is not ready")
    if _integer(
        _evidence(documents, ("explanationCount",), "explanation count"),
        "explanation count",
    ) != table_context["explanationReceipt"]["explanationCount"]:
        raise VerificationError("central explanation count differs from standalone evidence")
    if str(
        _evidence(documents, ("explanationRowsSha256",), "explanation rows digest")
    ) != table_context["explanationReceipt"]["explanationRowsSha256"]:
        raise VerificationError("central explanation digest differs from standalone evidence")
    return {"modelDecision": decision, "shortlist": shortlist}


def _invariant_checks(
    documents: Sequence[Mapping[str, Any]],
    tables: Mapping[str, Table],
    context: Mapping[str, Any],
    *,
    import_boundary_passed: bool,
    no_private_values: bool,
    no_pair_matrix: bool,
) -> dict[str, tuple[bool, str]]:
    models = tables["10_MODEL_BENCHMARK_RESULTS.tsv"]
    interactions = tables["15_INTERACTION_STATISTICS_REVIEW.tsv"]
    human = tables["17_HUMAN_REVIEW_PACKET.tsv"]
    model_deterministic = _header(models, "deterministic")
    model_comparability = _header(models, "comparability_exposed", "comparabilityExposed", "comparabilityChannel")
    model_explanation = _header(models, "explanation_path", "explanationPath", "explanationReady")
    symmetric = _header(models, "symmetric", "isSymmetric")
    symmetry_status = _header(models, "symmetry_test", "symmetryTest", "symmetryStatus")
    asymmetry = _header(models, "asymmetry_declared", "asymmetryDeclared")
    interaction_parent = _header(interactions, "parent_contribution_repeated", "parentContributionRepeated")
    interaction_importance = _header(
        interactions,
        "importance_inference",
        "importanceInference",
        "rare_means_important",
        "rareMeansImportant",
    )
    retrieval_column = _header(human, "retrieval_reasons", "retrievalReasons")
    shared_column = _header(human, "shared_independent_signals", "sharedIndependentSignals")
    shortlist = context["shortlist"]
    model_id = _header(models, "model_id", "modelId")
    shortlist_rows = [row for row in models.rows if row[model_id] in shortlist]
    checks = {
        "EXP-SIM-INV-001": (import_boundary_passed, "M0 is isolated and absent from production/scorer imports"),
        "EXP-SIM-INV-002": (
            set(context["lineage"]["scoredSignalIds"]).issubset(context["lineage"]["signalIds"]),
            "all scoring-eligible signal IDs are classified in the 64-row lineage registry",
        ),
        "EXP-SIM-INV-003": (
            _integer(_evidence(documents, ("sameSourceFactDoubleScoreCount",), "same-source double score count"), "same-source double score count") == 0,
            "lineage and aggregate evidence report zero duplicate base credit",
        ),
        "EXP-SIM-INV-004": (
            all(not _bool(row[interaction_parent], "interaction parent repeated") for row in interactions.rows),
            "interaction contributions are separated from their parents",
        ),
        "EXP-SIM-INV-005": (
            _integer(_evidence(documents, ("sharedUnknownPositiveCreditCount",), "shared unknown credit"), "shared unknown credit") == 0,
            "shared unknown state receives zero default affinity",
        ),
        "EXP-SIM-INV-006": (
            all(_bool(row[model_comparability], "model comparability") for row in models.rows),
            "every model result exposes a separate comparability channel",
        ),
        "EXP-SIM-INV-007": (
            _bool(_evidence(documents, ("contributionSchemaValid", "contributionNumeratorDenominatorOrSourceValid"), "contribution schema"), "contribution schema"),
            "contribution schema validates numerator/denominator or source identity",
        ),
        "EXP-SIM-INV-008": (
            _integer(_evidence(documents, ("curatorialHistoricalRelationCount",), "curatorial historical relation count"), "curatorial relation count") == 0,
            "curatorial evidence emits no historical relation",
        ),
        "EXP-SIM-INV-009": (
            all(
                row[interaction_importance].strip().upper() == "PROHIBITED"
                or not _bool(row[interaction_importance], "rare means important")
                for row in interactions.rows
            ),
            "rare interactions are diagnostics, never importance by definition",
        ),
        "EXP-SIM-INV-010": (
            _integer(_evidence(documents, ("geographicLayoutDistanceScoreCount", "mapCoordinateDistanceScoreCount"), "map-distance score count"), "map-distance score count") == 0,
            "map-coordinate distance contributes zero",
        ),
        "EXP-SIM-INV-011": (
            not _bool(_evidence(documents, ("sameSourcePositiveAffinityDefault",), "same-source positive default"), "same-source positive default"),
            "same-source is not positive affinity by default",
        ),
        "EXP-SIM-INV-012": (
            all(_bool(row[model_deterministic], "model deterministic") for row in models.rows),
            "all nine model families are deterministic",
        ),
        "EXP-SIM-INV-013": (
            all(str(row["sourceCommit"]) == SOURCE_SHA for row in context["runs"]),
            "all analysis receipts are source/release/projection/registry/index pinned",
        ),
        "EXP-SIM-INV-014": (
            _integer(_evidence(documents, ("heldExplorationObjectCount", "heldObjectsIncluded"), "held count"), "held count") == 0,
            "held objects are absent from indexes, evaluations, and review packet",
        ),
        "EXP-SIM-INV-015": (no_private_values, "no UUID or raw-private identifier appears in scoped artifacts"),
        "EXP-SIM-INV-016": (no_pair_matrix, "only bounded aggregates/top-k hashes are committed"),
        "EXP-SIM-INV-017": (
            not _bool(_evidence(documents, ("probabilityModelSelected",), "probability model"), "probability model"),
            "candidate/model/receipt outputs all set probability=false",
        ),
        "EXP-SIM-INV-018": (
            not _bool(_evidence(documents, ("publicSimilarityModelSelected",), "public model"), "public model"),
            "model decision remains internal/shortlist only",
        ),
        "EXP-SIM-INV-019": (
            not _bool(_evidence(documents, ("clusteringModelSelected",), "clustering model"), "clustering model"),
            "no clustering model is selected",
        ),
        "EXP-SIM-INV-020": (
            not _bool(_evidence(documents, ("randomnessAffectsAffinity",), "affinity randomness"), "affinity randomness")
            and not _bool(_evidence(documents, ("randomnessAffectsCandidateSet",), "candidate randomness"), "candidate randomness"),
            "randomness affects neither affinity nor candidates",
        ),
        "EXP-SIM-INV-021": (
            all(
                (not _bool(row[symmetric], "model symmetric")) or row[symmetry_status].strip().upper() == "PASS"
                for row in shortlist_rows
            ),
            "every shortlisted symmetric model has a passing symmetry test",
        ),
        "EXP-SIM-INV-022": (
            all(_bool(row[symmetric], "model symmetric") or _bool(row[asymmetry], "model asymmetry") for row in shortlist_rows),
            "every shortlisted query-conditioned model declares asymmetry",
        ),
        "EXP-SIM-INV-023": (
            _integer(_evidence(documents, ("mechanicalAxiomFailureCount", "axiomFailureCount"), "axiom failures"), "axiom failures") == 0,
            "every shortlisted model passes all applicable mechanical expectations",
        ),
        "EXP-SIM-INV-024": (
            all(_bool(row[model_explanation], "model explanation path") for row in shortlist_rows)
            and all(row[retrieval_column].strip() and row[shared_column].strip() for row in human.rows),
            "shortlist results and blinded review candidates retain explanation paths",
        ),
    }
    return checks


def verify(
    *,
    research_dir: Path,
    audit_raw_dir: Path,
    repo_root: Path = ROOT,
    fixture: bool = False,
    public_ids: set[str] | None = None,
    held_ids: set[str] | None = None,
    normalized_records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if research_dir.is_symlink() or audit_raw_dir.is_symlink() or repo_root.is_symlink():
        raise VerificationError("verification roots cannot be symlinks")
    research_dir = research_dir.resolve()
    audit_raw_dir = audit_raw_dir.resolve()
    repo_root = repo_root.resolve()
    _validate_exact_paths(research_dir, audit_raw_dir)
    raw = _load_json_receipts(audit_raw_dir)
    central = raw["exploration-similarity-evaluation-summary.json"]
    # High-level receipt keys are read from the central summary only.  Component
    # receipts may legitimately reuse a key with a richer representation (for
    # example the import-boundary object versus central ``PASS``), so merging
    # recursive namespaces would create false reconciliation conflicts.
    documents = [central]
    _validate_audit_ledgers(audit_raw_dir)
    _validate_research_receipts(research_dir, central)
    if public_ids is None or held_ids is None:
        public_ids, held_ids, normalized_records = _load_eligibility(repo_root)
    tables, table_context = _validate_tsv_shapes(
        research_dir,
        documents,
        raw,
        public_ids,
        held_ids,
        fixture=fixture,
    )
    semantic_receipts = _validate_model_context_receipts(
        raw,
        table_context["runs"],
        normalized_records,
    )
    explanation_receipt = _validate_explanation_evidence(
        raw,
        tables["17_HUMAN_REVIEW_PACKET.tsv"],
        public_ids=public_ids,
        held_ids=held_ids,
        runs=table_context["runs"],
        shortlist=table_context["shortlist"],
        candidate_index_sha256=semantic_receipts["candidateIndexSha256"],
        fixture=fixture,
        normalized_records=normalized_records,
    )
    table_context["semanticReceipts"] = semantic_receipts
    table_context["explanationReceipt"] = explanation_receipt
    aggregate = _validate_aggregate_contract(documents, table_context, tables)
    changed = _validate_changed_file_boundary(repo_root, fixture=fixture)
    scoped_paths = [research_dir / name for name in RESEARCH_FILES]
    scoped_paths += [audit_raw_dir / name for name in RAW_FILES]
    scoped_paths += [audit_raw_dir.parent / name for name in AUDIT_DOCUMENT_FILES]
    scoped_paths += sorted((repo_root / "scripts/exploration-v49-similarity").glob("*.py"))
    _scan_bytes_for_private_values(scoped_paths, held_ids)
    _validate_no_pair_matrix(scoped_paths, raw)
    _validate_negative_control_import_boundary(repo_root)

    checks = _invariant_checks(
        documents,
        tables,
        table_context,
        import_boundary_passed=True,
        no_private_values=True,
        no_pair_matrix=True,
    )
    failures = [identifier for identifier, (passed, _) in checks.items() if not passed]
    if failures:
        raise VerificationError(f"required invariants failed: {failures}")
    invariant_rows = [
        {
            "invariantId": identifier,
            "requirement": INVARIANT_TEXT[identifier],
            "status": "PASS",
            "evidence": checks[identifier][1],
        }
        for identifier in sorted(INVARIANT_TEXT)
    ]
    result = {
        "schemaVersion": "trace-exploration-similarity-round1-verification/v1",
        "status": "PASS",
        "checkCount": 11,
        "checks": [
            "EXACT_PATHS",
            "AUDIT_LEDGERS",
            "RESEARCH_RECEIPTS",
            "TSV_SHAPES",
            "AGGREGATE_RECONCILIATION",
            "PRIVATE_IDENTIFIER_BOUNDARY",
            "PAIR_MATRIX_BOUNDARY",
            "NEGATIVE_CONTROL_IMPORT_BOUNDARY",
            "PROTECTED_CHANGED_FILES",
            "ANALYSIS_RUN_RECEIPTS",
            "SEMANTIC_TRUST_RECEIPTS",
        ],
        "invariantCount": len(invariant_rows),
        "invariants": invariant_rows,
        "researchFileCount": len(RESEARCH_FILES),
        "researchTsvCount": len(RESEARCH_TSV_FILES),
        "auditDocumentCount": len(AUDIT_DOCUMENT_FILES),
        "auditRawFileCount": len(RAW_FILES),
        "publicObjectCount": PUBLIC_OBJECT_COUNT,
        "heldExplorationObjectCount": 0,
        "exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT,
        "modelDecision": aggregate["modelDecision"],
        "shortlistModelIds": sorted(table_context["shortlist"]),
        "changedFileCount": len(changed),
        "verificationEvidenceSha256": _sha256(
            _canonical_json_bytes(
                {
                    "research": {
                        name: _sha256((research_dir / name).read_bytes()) for name in RESEARCH_FILES
                    },
                    "auditRaw": {
                        name: _sha256((audit_raw_dir / name).read_bytes()) for name in RAW_FILES
                    },
                    "invariants": [row["invariantId"] for row in invariant_rows],
                }
            )
        ),
    }
    return result


def _tsv_bytes(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        cells = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, bool):
                value = "true" if value else "false"
            elif isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            elif value is None:
                value = ""
            cells.append(value)
        writer.writerow(cells)
    return output.getvalue().encode("utf-8")


def _fixture_run(
    model_id: str,
    ordinal: int,
    semantic_receipts: Mapping[str, str],
) -> dict[str, Any]:
    digest = hashlib.sha256(f"fixture-{ordinal}".encode()).hexdigest()
    candidate_index_digest = semantic_receipts["candidateIndexSha256"]
    receipt: dict[str, Any] = {
        "schemaVersion": "trace-exploration-analysis-run-receipt/v1",
        "modelId": model_id,
        "modelFamily": f"FIXTURE_{model_id}",
        "implementationVersion": "fixture-v1",
        "parameterSet": {
            "ordinal": ordinal,
            "benchmarkVariantId": f"{model_id}-FIXTURE",
            "sourceTreatment": "SOURCE-0",
            **{field: semantic_receipts[field] for field in MODEL_CONTEXT_DIGEST_FIELDS},
        },
        "sourceCommit": SOURCE_SHA,
        "researchReleaseId": "fixture-release",
        "researchReleaseSha256": digest,
        "researchManifestSha256": digest,
        "contextProjectionId": "trace-context-v1",
        "contextProjectionSha256": digest,
        "spacetimeProjectionId": "trace-spacetime-v1",
        "spacetimeProjectionSha256": digest,
        "explorationSignalRegistrySha256": digest,
        "candidateIndexSha256": candidate_index_digest,
        "inputCohortCount": PUBLIC_OBJECT_COUNT,
        "executionSeed": None,
        "outputSummarySha256": digest,
        "topKArtifactSha256": digest,
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
        "fullPairMatrixMaterialized": False,
        "historicalRelation": False,
        "semanticRelation": False,
        "probability": False,
        "generatedAt": "2026-08-24T00:00:00Z",
        "timestampExcludedFromDeterministicHash": True,
    }
    excluded = {"generatedAt", "timestampExcludedFromDeterministicHash", "receiptSha256", "analysisRunId"}
    bound = _sha256(_canonical_json_bytes({key: value for key, value in receipt.items() if key not in excluded}))
    receipt["analysisRunId"] = f"EXP-RUN:{bound}"
    receipt["receiptSha256"] = bound
    return receipt


def _write_fixture(root: Path) -> tuple[Path, Path, set[str], set[str]]:
    research = root / "docs/research/trace-v49-exploration-similarity-round1"
    audit = root / "docs/audits/v49-exploration-similarity-round1"
    raw_dir = audit / "raw"
    research.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    semantic_receipts = {
        "candidateIndexSha256": _sha256(b"fixture-candidate-index"),
        "scoringRecordsSha256": _sha256(b"fixture-scoring-records"),
        "modelContextSha256": _sha256(b"fixture-model-context"),
        "compiledFeatureContextSha256": _sha256(b"fixture-compiled-context"),
        "interactionRegistrySha256": _sha256(b"fixture-interaction-registry"),
        "trustedInteractionContextSha256": _sha256(b"fixture-interaction-context"),
    }
    for filename in RESEARCH_FILES:
        if filename.endswith(".md"):
            text = (
                f"# {filename}\n\n"
                "Research-only archive affinity evidence. probability: false; historicalRelation: false; "
                "semanticRelation: false.\n"
            )
            if filename in {"00_EXECUTIVE_DECISION.md", "22_MODEL_SHORTLIST_DECISION.md", "23_ROUND_DECISION.md"}:
                text += "\nMODEL_DECISION=MODEL_FAMILY_SHORTLISTED\nPUBLIC_SIMILARITY_MODEL_SELECTED=false\n"
            if filename == "18_EXPLANATION_CONTRACT.md":
                text += "\nretrievalReasons affinityContributions distinctiveFeatures unavailableFamilies comparability methodVersion analysisRunId\n"
            (research / filename).write_text(text, encoding="utf-8", newline="\n")

    lineage_rows = []
    dispositions = list(SCORING_DISPOSITIONS)
    for index in range(SIGNAL_COUNT):
        disposition = "INDEPENDENT_BASE_SIGNAL" if index < 8 else dispositions[index % len(dispositions)]
        lineage_rows.append(
            {
                "signal_id": f"SIG-FIXTURE-{index:03d}",
                "source_artifact": "fixture",
                "source_row_family": "FIXTURE",
                "direct_parent_signals": "",
                "derived_from_signals": "",
                "same_source_fact_group": f"FACT-{index:03d}",
                "epistemic_level": "ANALYSIS_DIAGNOSTIC",
                "scoring_disposition": disposition,
                "independent_information_candidate": disposition == "INDEPENDENT_BASE_SIGNAL",
                "duplicate_for_scoring": False,
                "interaction_only": disposition == "DEPENDENT_INTERACTION_SIGNAL",
                "diagnostic_only": disposition == "DIAGNOSTIC_ONLY",
                "candidate_generation_allowed": disposition in {"INDEPENDENT_BASE_SIGNAL", "CANDIDATE_GENERATION_ONLY"},
                "scoring_allowed": disposition == "INDEPENDENT_BASE_SIGNAL",
                "explanation_allowed": disposition != "REJECT",
                "reason": "synthetic verifier fixture",
            }
        )
    (research / "03_SIGNAL_LINEAGE_REGISTRY.tsv").write_bytes(_tsv_bytes(LINEAGE_COLUMNS, lineage_rows))

    cur_headers = (
        "policy_id", "sensitivity_id", "broad_stop_ratio", "raw_membership_scoring_allowed",
        "same_source_parent_duplication_failures", "broad_dominance_failures",
        "randomness_affects_candidate_set", "historical_relation", "semantic_relation", "probability",
    )
    cur_policy_rows = [
        ("CUR-W1", "N/A"),
        ("CUR-W2", "N/A"),
        *(("CUR-W3", ratio) for ratio in (0.25, 0.50, 0.75, 0.90)),
        ("CUR-W4", "N/A"),
        ("CUR-W5", "N/A"),
        ("CUR-W6", "N/A"),
    ]
    cur_rows = [
        {
            "policy_id": policy,
            "sensitivity_id": f"{policy}-{ratio}",
            "broad_stop_ratio": ratio,
            "raw_membership_scoring_allowed": False,
            "same_source_parent_duplication_failures": 0,
            "broad_dominance_failures": 0,
            "randomness_affects_candidate_set": False,
            "historical_relation": False,
            "semantic_relation": False,
            "probability": False,
        }
        for policy, ratio in cur_policy_rows
    ]
    (research / "07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv").write_bytes(_tsv_bytes(cur_headers, cur_rows))

    shortlist = {"M2", "M5", "M7"}
    model_headers = (
        "model_id", "variant_id", "model_family", "symmetric", "symmetry_test", "asymmetry_declared",
        "deterministic", "comparability_exposed", "explanation_path", "shortlisted",
        "historical_relation", "semantic_relation", "probability",
    )
    model_rows = [
        {
            "model_id": model,
            "variant_id": f"{model}-FIXTURE",
            "model_family": f"FIXTURE_{model}",
            "symmetric": model != "M7",
            "symmetry_test": "PASS" if model != "M7" else "NOT_APPLICABLE",
            "asymmetry_declared": model == "M7",
            "deterministic": True,
            "comparability_exposed": True,
            "explanation_path": True,
            "shortlisted": model in shortlist,
            "historical_relation": False,
            "semantic_relation": False,
            "probability": False,
        }
        for model in sorted(MODEL_IDS)
    ]
    (research / "10_MODEL_BENCHMARK_RESULTS.tsv").write_bytes(_tsv_bytes(model_headers, model_rows))

    candidate_headers = (
        "candidate_variant_id", "model_id", "reference_variant_id", "candidate_pool_p50", "candidate_pool_p95",
        "candidate_pool_p99", "candidate_pool_max", "recall_at_10", "recall_at_20", "recall_at_50",
        "zero_candidate_object_count", "near_full_candidate_object_count", "pair_rows_materialized",
        "randomness_affects_candidate_set",
    )
    candidate_rows = []
    for variant in sorted(CANDIDATE_VARIANTS):
        for model in sorted(shortlist):
            candidate_rows.append(
                {
                    "candidate_variant_id": variant,
                    "model_id": model,
                    "reference_variant_id": f"{model}-FIXTURE",
                    "candidate_pool_p50": 100,
                    "candidate_pool_p95": 200,
                    "candidate_pool_p99": 250,
                    "candidate_pool_max": 300,
                    "recall_at_10": 1,
                    "recall_at_20": 1,
                    "recall_at_50": 1,
                    "zero_candidate_object_count": 0,
                    "near_full_candidate_object_count": 0,
                    "pair_rows_materialized": 0,
                    "randomness_affects_candidate_set": False,
                }
            )
    (research / "11_CANDIDATE_RECALL_RESULTS.tsv").write_bytes(_tsv_bytes(candidate_headers, candidate_rows))

    bias_headers = (
        "model_id", "result_top1_source_share", "result_hhi", "cross_source_rate",
        "source_dominated_query_rate", "curation_dominated_query_rate", "maximum_family_contribution_p95",
    )
    bias_rows = [
        {
            "model_id": model,
            "result_top1_source_share": 0.2,
            "result_hhi": 0.1,
            "cross_source_rate": 0.8,
            "source_dominated_query_rate": 0,
            "curation_dominated_query_rate": 0,
            "maximum_family_contribution_p95": 0.5,
        }
        for model in sorted(shortlist)
    ]
    (research / "12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv").write_bytes(_tsv_bytes(bias_headers, bias_rows))

    hub_headers = (
        "model_id", "k", "mean", "variance", "skewness", "gini",
        "top1_percent_occurrence_share", "maximum_occurrence", "zero_occurrence_object_count",
    )
    hub_rows = [
        {
            "model_id": model,
            "k": k,
            "mean": k,
            "variance": 1,
            "skewness": 0.1,
            "gini": 0.1,
            "top1_percent_occurrence_share": 0.02,
            "maximum_occurrence": k + 1,
            "zero_occurrence_object_count": 0,
        }
        for model in sorted(SCALAR_MODEL_IDS)
        for k in sorted(HUBNESS_K_VALUES)
    ]
    (research / "13_HUBNESS_ANALYSIS.tsv").write_bytes(_tsv_bytes(hub_headers, hub_rows))

    ablation_headers = (
        "model_id",
        "ablation_id",
        "ablation_family",
        "k",
        "learned_weights_used",
        "historical_labels_used",
    )
    fixture_ablation_variants = [
        (family, family) for family in sorted(ABLATION_FAMILIES)
    ] + [
        (f"{family}-SENSITIVITY-{ordinal:02d}", family)
        for ordinal, family in enumerate(
            (sorted(ABLATION_FAMILIES) * 2)[:14],
            start=1,
        )
    ]
    ablation_rows = [
        {
            "model_id": model,
            "ablation_id": ablation_id,
            "ablation_family": family,
            "k": k,
            "learned_weights_used": False,
            "historical_labels_used": False,
        }
        for model in sorted(MODEL_IDS - {"M0"})
        for ablation_id, family in fixture_ablation_variants
        for k in sorted(HUBNESS_K_VALUES)
    ]
    (research / "14_ABLATION_AND_STABILITY.tsv").write_bytes(_tsv_bytes(ablation_headers, ablation_rows))

    interaction_headers = (
        "method_id", "support_threshold", "parent_contribution_repeated", "importance_inference",
    )
    interaction_rows = [
        {
            "method_id": method,
            "support_threshold": threshold,
            "parent_contribution_repeated": False,
            "importance_inference": "PROHIBITED",
        }
        for method in sorted(INTERACTION_METHODS)
        for threshold in sorted(SUPPORT_THRESHOLDS)
    ]
    (research / "15_INTERACTION_STATISTICS_REVIEW.tsv").write_bytes(_tsv_bytes(interaction_headers, interaction_rows))

    mechanical_headers = (
        "axiom_id", "status", "failure_count", "tested_model_ids", "historical_relation", "semantic_relation", "probability",
    )
    mechanical_rows = [
        {
            "axiom_id": axiom,
            "status": "PASS",
            "failure_count": 0,
            "tested_model_ids": ",".join(sorted(shortlist)),
            "historical_relation": False,
            "semantic_relation": False,
            "probability": False,
        }
        for axiom in sorted(AXIOM_IDS)
    ]
    (research / "16_MECHANICAL_EXPECTATION_CASES.tsv").write_bytes(_tsv_bytes(mechanical_headers, mechanical_rows))

    public_ids = {f"SURF-TEST-{index:03d}" for index in range(100)}
    human_headers = (
        "anchor_public_id", "candidate_public_id", "blind_profile_slot", "candidate_ordinal",
        "retrieval_reasons", "shared_independent_signals", "distinctive_signals", "comparability_ratio",
        "source_composition",
        "useful_for_further_exploration", "explanation_intelligible", "merely_broad_category",
        "new_defensible_research_direction", "accidental_relation_suggestion", "reviewer_notes",
        "human_review_completed", "historical_relation", "semantic_relation", "probability",
    )
    human_rows = []
    ordered_public = sorted(public_ids)
    for anchor_index, anchor in enumerate(ordered_public[:HUMAN_REVIEW_ANCHOR_COUNT]):
        for profile in ("PROFILE-1", "PROFILE-2", "PROFILE-3"):
            for ordinal in range(1, 4):
                candidate = ordered_public[(anchor_index + ordinal) % len(ordered_public)]
                human_rows.append(
                    {
                        "anchor_public_id": anchor,
                        "candidate_public_id": candidate,
                        "blind_profile_slot": profile,
                        "candidate_ordinal": ordinal,
                        "retrieval_reasons": "context:fixture",
                        "shared_independent_signals": "context:fixture",
                        "distinctive_signals": "source:fixture",
                        "comparability_ratio": 1,
                        "source_composition": "CROSS_GOVERNED_SOURCE_NAME",
                        "useful_for_further_exploration": "",
                        "explanation_intelligible": "",
                        "merely_broad_category": "",
                        "new_defensible_research_direction": "",
                        "accidental_relation_suggestion": "",
                        "reviewer_notes": "",
                        "human_review_completed": False,
                        "historical_relation": False,
                        "semantic_relation": False,
                        "probability": False,
                    }
                )
    (research / "17_HUMAN_REVIEW_PACKET.tsv").write_bytes(_tsv_bytes(human_headers, human_rows))

    runs = [
        _fixture_run(f"M{index}", index, semantic_receipts) for index in range(9)
    ]
    run_headers = ("receipt_json",)
    (research / "19_ANALYSIS_RUN_REGISTER.tsv").write_bytes(
        _tsv_bytes(run_headers, [{"receipt_json": receipt} for receipt in runs])
    )

    model_by_profile = {"PROFILE-1": "M2", "PROFILE-2": "M5", "PROFILE-3": "M7"}
    run_by_model = {str(receipt["modelId"]): receipt for receipt in runs}
    explanation_rows: list[dict[str, Any]] = []
    for row in human_rows:
        model_id = model_by_profile[str(row["blind_profile_slot"])]
        run = run_by_model[model_id]
        affinity_contribution: dict[str, Any] = {
            "family": "context",
            "signalId": "SIG-FIXTURE-000",
            "sameSourceFactGroup": "FACT-000",
            "numerator": 1,
            "denominator": 1,
            "contribution": 1,
            "historicalRelation": False,
            "semanticRelation": False,
        }
        if model_id == "M7":
            affinity_contribution.update(
                {
                    "basis": "BM25F_LIKE_FIELDED_RETRIEVAL",
                    "formula": "BM25F_LIKE_FIELD_SATURATION",
                    "queryTermStatistics": [
                        {
                            "featureId": "MEDIUM-FIXTURE",
                            "documentFrequency": 2,
                            "idf": 1,
                            "matched": True,
                        }
                    ],
                    "matchedQueryTermCount": 1,
                    "documentFieldLength": 1,
                    "averageDocumentFieldLength": 1,
                    "k1": 1.2,
                    "b": 0.75,
                    "lengthNormalization": 1,
                    "saturation": 1,
                    "declaredFamilyWeight": 1,
                }
            )
        explanation: dict[str, Any] = {
            "schemaVersion": EXPLANATION_SCHEMA_VERSION,
            "queryId": row["anchor_public_id"],
            "candidateId": row["candidate_public_id"],
            "candidateTitle": f"Fixture candidate {row['candidate_public_id']}",
            "retrievalReasons": [
                {
                    "reasonType": "DIRECT_APPROVED_POSTING",
                    "family": "context",
                    "numerator": 1,
                    "denominator": PUBLIC_OBJECT_COUNT,
                    "historicalRelation": False,
                    "semanticRelation": False,
                }
            ],
            "affinityContributions": [affinity_contribution],
            "distinctiveFeatures": [],
            "ignoredDuplicateSignals": ["SIG-FIXTURE-DUPLICATE"],
            "unavailableFamilies": [],
            "comparability": {
                "observedFamilyCount": 4,
                "eligibleFamilyCount": 4,
                "ratio": 1,
            },
            "familyContributionUnits": {"context": 1},
            "familyContributionShares": {"context": 1},
            "broadContainerAttenuation": {
                "curatorialUse": "RECALL_SUBSTRATE_ONLY",
                "rawCuratedJaccardScoringAllowed": False,
            },
            "sourceBiasNotes": ["CROSS_GOVERNED_SOURCE_REPORTED"],
            "interactionEvidence": [],
            "interactionRegistrySha256": None,
            "interactionContextSha256": None,
            "methodId": model_id,
            "sourceTreatment": "SOURCE-0",
            "methodVersion": run["implementationVersion"],
            "analysisRunId": run["analysisRunId"],
            "researchReleaseId": run["researchReleaseId"],
            "researchReleaseSha256": run["researchReleaseSha256"],
            "contextProjectionSha256": run["contextProjectionSha256"],
            "spacetimeProjectionSha256": run["spacetimeProjectionSha256"],
            "candidateIndexSha256": semantic_receipts["candidateIndexSha256"],
            "diagnosticScore": 1,
            "scoreOnlyResult": False,
            "probability": False,
            "historicalRelation": False,
            "semanticRelation": False,
        }
        explanation["explanationSha256"] = _sha256(_canonical_json_bytes(explanation))
        explanation_rows.append(explanation)
    fixture_explanation_validation_rows = [
        {
            "schemaVersion": "trace-exploration-explanation-validation/v1",
            "explanationSha256": row["explanationSha256"],
            "retrievalReasonCount": 1,
            "affinityContributionCount": 1,
            "sameSourceFactGroupCount": 1,
            "familyContributionShareCount": 1,
            "familyContributionSharesReconciled": True,
            "interactionEvidenceCount": 0,
            "comparabilityReconciled": True,
            "sourceTreatmentBoundaryPass": True,
            "rawCuratedScoringBoundaryPass": True,
            "interactionPairBindingPass": True,
            "semanticValidationPass": True,
        }
        for row in explanation_rows
    ]
    explanation_validation = {
        "explanationContractReady": True,
        "standaloneSemanticValidationPassed": True,
        "contributionSchemaValid": True,
        "explanationCount": len(explanation_rows),
        "retrievalPathCount": len(explanation_rows),
        "affinityEvidencePathCount": len(explanation_rows),
        "comparabilityValidCount": len(explanation_rows),
        "provenancePinnedCount": len(explanation_rows),
        "invalidExplanationCount": 0,
        "scoreOnlyResultCount": 0,
        "historicalRelationCount": 0,
        "semanticRelationCount": 0,
        "probabilityCount": 0,
        "explanationRowsSha256": _sha256(_canonical_json_bytes(explanation_rows)),
        "explanationValidationRowsSha256": _sha256(
            _canonical_json_bytes(fixture_explanation_validation_rows)
        ),
    }

    research_receipts = {
        filename: {
            "bytes": (research / filename).stat().st_size,
            "sha256": _sha256((research / filename).read_bytes()),
        }
        for filename in RESEARCH_FILES
    }
    central: dict[str, Any] = {
        "sourceCommit": SOURCE_SHA,
        "publicObjectCount": PUBLIC_OBJECT_COUNT,
        "heldExplorationObjectCount": 0,
        "exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT,
        "explorationSignalInputCount": SIGNAL_COUNT,
        "signalLineageClassifiedCount": SIGNAL_COUNT,
        "signalLineageUnclassifiedCount": 0,
        **{
            {
                "INDEPENDENT_BASE_SIGNAL": "independentBaseSignalCount",
                "DEPENDENT_INTERACTION_SIGNAL": "dependentInteractionSignalCount",
                "CANDIDATE_GENERATION_ONLY": "candidateGenerationOnlySignalCount",
                "COMPARABILITY_ONLY": "comparabilityOnlySignalCount",
                "EXPLANATION_ONLY": "explanationOnlySignalCount",
                "DIAGNOSTIC_ONLY": "diagnosticOnlySignalCount",
                "REJECT": "rejectedScoringSignalCount",
            }[disposition]: count
            for disposition, count in Counter(
                row["scoring_disposition"] for row in lineage_rows
            ).items()
        },
        "sameSourceFactGroupCount": SIGNAL_COUNT,
        "sameSourceFactDoubleScoreCount": 0,
        "rawCuratedJaccardImportBoundary": "PASS",
        "rawCuratedJaccardProductionEligible": False,
        "candidateGeneratorVariantCount": 6,
        "candidateArchitectureSelected": True,
        "selectedCandidateVariant": "CG-CUR-4",
        "selectedCandidatePoolP50": 100,
        "selectedCandidatePoolP95": 200,
        "selectedCandidatePoolP99": 250,
        "selectedCandidatePoolMax": 300,
        "selectedCandidateRecallAt10": 1,
        "selectedCandidateRecallAt20": 1,
        "selectedCandidateRecallAt50": 1,
        "zeroCandidateObjectCount": 0,
        "nearFullCorpusCandidateObjectCount": 0,
        "modelIds": sorted(MODEL_IDS),
        "modelVariantCount": len(MODEL_IDS),
        "modelDecision": "MODEL_FAMILY_SHORTLISTED",
        "shortlistModelIds": sorted(shortlist),
        "modelShortlistCount": len(shortlist),
        "curatorialAttenuationVariantCount": 6,
        "curatorialResidualSignalCount": 0,
        "curatorialAsRecallIndex": True,
        "curatorialAsIndependentScore": False,
        "curatorialParentDuplicationFailureCount": 0,
        "missingnessVariantCount": 4,
        "missingnessVariantIds": sorted(MISSINGNESS_VARIANTS),
        "comparabilityP50": 1,
        "comparabilityP95": 1,
        "interactionMethodCount": len(INTERACTION_METHODS),
        "interactionSupportThresholdCount": len(SUPPORT_THRESHOLDS),
        "hubnessKValues": sorted(HUBNESS_K_VALUES),
        "hubnessCorrectionTested": False,
        "hubnessCorrectionSelected": False,
        "mechanicalAxiomCount": 15,
        "mechanicalAxiomFailureCount": 0,
        "ablationVariantCount": len(MODEL_IDS - {"M0"}) * 27,
        "pathologicalAnchorCount": 15,
        "humanReviewPacketAnchorCount": HUMAN_REVIEW_ANCHOR_COUNT,
        "humanReviewPacketReady": True,
        "humanReviewCompleted": False,
        "analysisRunCount": len(runs),
        "analysisRunReceiptFailureCount": 0,
        **semantic_receipts,
        "candidateIndexBuildMs": 1,
        "candidateIndexBytes": 1,
        "candidateIndexHeapBytes": 1,
        "exhaustiveModelBenchmarkMs": 1,
        "objectLocalQueryP50Ms": 1,
        "objectLocalQueryP95Ms": 1,
        "peakHeapBytes": 1,
        "peakRssBytes": 1,
        "sharedUnknownPositiveCreditCount": 0,
        "notApplicableAsMissingCount": 0,
        "lowSupportInflationFailureCount": 0,
        "interactionParentDoubleCountFailures": 0,
        "unexplainedShortlistResultCount": 0,
        "explanationCount": len(explanation_rows),
        "explanationRowsSha256": explanation_validation["explanationRowsSha256"],
        "scoreOnlyResultCount": 0,
        "historicalRelationCount": 0,
        "semanticRelationCount": 0,
        "probabilityCount": 0,
        "internalUuidExposureCount": 0,
        "databaseFilesChanged": 0,
        "searchFilesChanged": 0,
        "publicSimilarityModelSelected": False,
        "publicSimilarityWeightsSelected": False,
        "probabilityModelSelected": False,
        "clusteringModelSelected": False,
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
        "fullPairMatrixCommitted": False,
        "fullPairMatrixInClient": False,
        "canonicalReleaseChanged": False,
        "contextSemanticsChanged": False,
        "contextGovernanceChanged": False,
        "contextPublicProjectionChanged": False,
        "spacetimeGovernanceChanged": False,
        "spacetimePublicProjectionChanged": False,
        "publicExplorationApiAdded": False,
        "publicExplorationRouteAdded": False,
        "explorationRendererImplemented": False,
        "explorationTemplateRegistryFrozen": False,
        "comparabilityChannelImplemented": True,
        "explanationContractReady": True,
        "contributionSchemaValid": True,
        "curatorialHistoricalRelationCount": 0,
        "geographicLayoutDistanceScoreCount": 0,
        "sameSourcePositiveAffinityDefault": False,
        "researchOutputReceipts": research_receipts,
    }
    run_summary: dict[str, Any] = {
        "schemaVersion": "trace-exploration-analysis-run-register/v1",
        "analysisRunCount": len(runs),
        "receiptFailureCount": 0,
        "rows": runs,
    }
    run_summary["registerSha256"] = _sha256(
        _canonical_json_bytes(
            {
                "schemaVersion": run_summary["schemaVersion"],
                "receiptSha256": [row["receiptSha256"] for row in runs],
            }
        )
    )
    raw_documents: dict[str, Any] = {
        "exploration-similarity-evaluation-summary.json": central,
        "signal-lineage-summary.json": {
            "signalLineageClassifiedCount": SIGNAL_COUNT,
            "signalLineageUnclassifiedCount": 0,
            "signals": lineage_rows,
        },
        "independent-basis-summary.json": {
            "sameSourceFactDoubleScoreCount": 0,
            "independentBaseSignalIds": [
                row["signal_id"]
                for row in lineage_rows
                if row["scoring_disposition"] == "INDEPENDENT_BASE_SIGNAL"
            ],
            "dependentInteractionSignalIds": [
                row["signal_id"]
                for row in lineage_rows
                if row["scoring_disposition"] == "DEPENDENT_INTERACTION_SIGNAL"
            ],
            "directCandidatePostingSignalIds": [
                row["signal_id"] for row in lineage_rows if row["candidate_generation_allowed"]
            ],
            "highInformationCandidatePostingSignalIds": [],
        },
        "candidate-index-summary.json": {
            **semantic_receipts,
            "candidateGeneratorVariantCount": 6,
            "randomnessAffectsCandidateSet": False,
            "rows": [
                {
                    "candidateVariant": row["candidate_variant_id"],
                    "referenceModelId": row["model_id"],
                    "referenceVariantId": row["reference_variant_id"],
                    "k": k,
                    "recall": row[f"recall_at_{k}"],
                    "candidatePoolP50": row["candidate_pool_p50"],
                    "candidatePoolP95": row["candidate_pool_p95"],
                    "candidatePoolP99": row["candidate_pool_p99"],
                    "candidatePoolMax": row["candidate_pool_max"],
                    "zeroCandidateObjectCount": row["zero_candidate_object_count"],
                    "nearFullCorpusCandidateObjectCount": row["near_full_candidate_object_count"],
                }
                for row in candidate_rows
                for k in (10, 20, 50)
            ],
        },
        "model-benchmark-summary.json": {
            **{field: semantic_receipts[field] for field in MODEL_CONTEXT_DIGEST_FIELDS},
            "modelIds": sorted(MODEL_IDS),
            "modelRows": [
                {
                    "modelId": row["model_id"],
                    "variantId": row["variant_id"],
                    "modelFamily": f"FIXTURE_{row['model_id']}",
                    "symmetric": row["symmetric"],
                    "shortlistEligible": row["shortlisted"],
                }
                for row in model_rows
            ],
            "explanationRows": explanation_rows,
            "explanationValidation": explanation_validation,
        },
        "missingness-summary.json": {"missingnessVariantCount": 4, "sharedUnknownPositiveCreditCount": 0},
        "interaction-summary.json": {
            "interactionMethodCount": len(INTERACTION_METHODS),
            "interactionParentDoubleCountFailures": 0,
            "observedPairCellCount": 8,
            "observedTripleCellCount": 4,
            "registryCellCount": 12,
            "registrySha256": semantic_receipts["interactionRegistrySha256"],
            "trustedInteractionContextSha256": semantic_receipts[
                "trustedInteractionContextSha256"
            ],
            "jointObservableDenominatorPolicy": "ALL_DIMENSIONS_OBSERVED",
            "invalidDenominatorCount": 0,
            "supportExceedsDenominatorCount": 0,
            "positiveExcessAssociationRequired": True,
            "nonPositiveExcessResidualCount": 0,
            "expectedMethodGridRowCount": len(INTERACTION_METHODS) * len(SUPPORT_THRESHOLDS),
            "observedMethodGridRowCount": len(INTERACTION_METHODS) * len(SUPPORT_THRESHOLDS),
            "expectedResidualGridRowCount": len(RESIDUAL_INTERACTION_METHODS) * len(SUPPORT_THRESHOLDS),
            "observedResidualGridRowCount": len(RESIDUAL_INTERACTION_METHODS) * len(SUPPORT_THRESHOLDS),
            "gridReconciliationFailureCount": 0,
            "scorerCapReconciliationFailureCount": 0,
            "lowSupportInflationFailureCount": 0,
            "rows": [
                {
                    "method": method,
                    "supportThreshold": threshold,
                    "eligibleObservedCellCount": max(0, 14 - threshold),
                    "lowSupportCellsExcluded": 12 - max(0, 14 - threshold),
                    "statisticP50": 0.1,
                    "statisticP95": 0.2,
                    "statisticMax": 0.3,
                    "rareMeansImportant": False,
                    "parentContributionRepeated": False,
                }
                for method in sorted(INTERACTION_METHODS)
                for threshold in sorted(SUPPORT_THRESHOLDS)
            ],
            "residualRows": [
                {
                    "method": method,
                    "supportThreshold": threshold,
                    "cellCount": 12,
                    "residualP50": 0 if method == "NO_INTERACTION_CONTRIBUTION" else 0.01,
                    "residualP95": 0 if method == "NO_INTERACTION_CONTRIBUTION" else 0.03,
                    "residualMax": 0 if method == "NO_INTERACTION_CONTRIBUTION" else 0.05,
                    "cap": 0.10,
                    "positiveExcessAssociationRequired": True,
                    "positiveExcessEligibleCellCount": 4,
                    "positiveResidualCellCount": 0 if method == "NO_INTERACTION_CONTRIBUTION" else 3,
                    "nonPositiveExcessResidualCount": 0,
                }
                for method in sorted(RESIDUAL_INTERACTION_METHODS)
                for threshold in sorted(SUPPORT_THRESHOLDS)
            ],
            "scorerExperimentRows": [
                {
                    "interactionPolicy": policy,
                    "anchorCount": HUMAN_REVIEW_ANCHOR_COUNT,
                    "evaluatedPairCount": 500,
                    "meanTop20Overlap": (
                        1 if policy == "NO_INTERACTION_CONTRIBUTION" else 0.9
                    ),
                    "meanTop20RankCorrelation": (
                        1 if policy == "NO_INTERACTION_CONTRIBUTION" else 0.8
                    ),
                    "scoreDeltaP50": (
                        0 if policy == "NO_INTERACTION_CONTRIBUTION" else 0.01
                    ),
                    "scoreDeltaP95": (
                        0 if policy == "NO_INTERACTION_CONTRIBUTION" else 0.03
                    ),
                    "directScorerSensitivity": True,
                }
                for policy in sorted(RESIDUAL_INTERACTION_METHODS)
            ],
            "scorerExperimentPairCount": 500,
        },
        "hubness-summary.json": {"hubnessKValues": sorted(HUBNESS_K_VALUES)},
        "ablation-summary.json": {"historicalLabelsUsed": False},
        "human-review-summary.json": {
            "humanReviewPacketAnchorCount": HUMAN_REVIEW_ANCHOR_COUNT,
            "humanReviewCompleted": False,
            "explanationRows": explanation_rows,
            "explanationValidation": explanation_validation,
        },
        "performance-summary.json": {"exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT, "fullPairMatrixCommitted": False},
        "analysis-run-summary.json": run_summary,
        "security-summary.json": {"internalUuidExposureCount": 0, "heldExplorationObjectCount": 0},
    }
    for filename, value in raw_documents.items():
        (raw_dir / filename).write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")

    for filename in AUDIT_DOCUMENT_FILES:
        (audit / filename).write_text(f"# {filename}\n\nBounded verification evidence.\n", encoding="utf-8", newline="\n")
    manifest_rows = []
    for relative in sorted(set(AUDIT_DOCUMENT_FILES) | {f"raw/{name}" for name in RAW_FILES}):
        payload = (audit / relative).read_bytes()
        manifest_rows.append({"path": relative, "bytes": len(payload), "sha256": _sha256(payload), "role": "synthetic self-test evidence"})
    (audit / "MANIFEST.tsv").write_bytes(_tsv_bytes(("path", "bytes", "sha256", "role"), manifest_rows))
    sums = {
        row["path"]: row["sha256"] for row in manifest_rows
    }
    sums["MANIFEST.tsv"] = _sha256((audit / "MANIFEST.tsv").read_bytes())
    (audit / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {relative}\n" for relative, digest in sorted(sums.items())),
        encoding="utf-8",
        newline="\n",
    )
    return research, raw_dir, public_ids, set()


def self_test(repo_root: Path = ROOT) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="trace-v49-similarity-verifier-") as temporary:
        research, raw_dir, public_ids, held_ids = _write_fixture(Path(temporary))
        boundary_root = Path(temporary) / "boundary"
        boundary_scripts = boundary_root / "scripts/exploration-v49-similarity"
        boundary_frontend = boundary_root / "frontend/src"
        boundary_scripts.mkdir(parents=True)
        boundary_frontend.mkdir(parents=True)
        (boundary_scripts / "negative_control.py").write_text(
            "MODEL_ID='M0'\nANALYSIS_ONLY=True\nSCORING_ALLOWED=False\n"
            "SHORTLIST_ELIGIBLE=False\nPRODUCTION_IMPORT_ALLOWED=False\n",
            encoding="utf-8",
        )
        for filename in ("model_baselines.py", "candidate_index.py", "explanation.py"):
            (boundary_scripts / filename).write_text("VALUE = 1\n", encoding="utf-8")
        result = verify(
            research_dir=research,
            audit_raw_dir=raw_dir,
            repo_root=boundary_root,
            fixture=True,
            public_ids=public_ids,
            held_ids=held_ids,
        )
        loaded_raw = _load_json_receipts(raw_dir)
        interaction_table = _parse_tsv(research / "15_INTERACTION_STATISTICS_REVIEW.tsv")

        bad_denominator_raw = json.loads(
            json.dumps(loaded_raw["interaction-summary.json"])
        )
        bad_denominator_raw["rows"][0]["eligibleObservedCellCount"] += 1
        denominator_rejected = False
        try:
            _validate_interactions(
                interaction_table,
                bad_denominator_raw,
                loaded_raw["candidate-index-summary.json"],
            )
        except VerificationError:
            denominator_rejected = True
        if not denominator_rejected:
            raise AssertionError("self-test invalid joint-observable denominator was not rejected")

        bad_excess_raw = json.loads(json.dumps(loaded_raw["interaction-summary.json"]))
        bad_excess_raw["residualRows"][0]["nonPositiveExcessResidualCount"] = 1
        positive_excess_rejected = False
        try:
            _validate_interactions(
                interaction_table,
                bad_excess_raw,
                loaded_raw["candidate-index-summary.json"],
            )
        except VerificationError:
            positive_excess_rejected = True
        if not positive_excess_rejected:
            raise AssertionError("self-test non-positive-excess residual was not rejected")

        bad_scorer_raw = json.loads(json.dumps(loaded_raw["interaction-summary.json"]))
        bad_scorer_raw["scorerExperimentRows"].pop()
        scorer_experiment_rejected = False
        try:
            _validate_interactions(
                interaction_table,
                bad_scorer_raw,
                loaded_raw["candidate-index-summary.json"],
            )
        except VerificationError:
            scorer_experiment_rejected = True
        if not scorer_experiment_rejected:
            raise AssertionError("self-test incomplete direct-scorer experiment was not rejected")

        bad_digest_raw = json.loads(json.dumps(loaded_raw))
        bad_digest_raw["candidate-index-summary.json"]["scoringRecordsSha256"] = "f" * 64
        digest_rejected = False
        try:
            _validate_model_context_receipts(
                bad_digest_raw,
                bad_digest_raw["analysis-run-summary.json"]["rows"],
                None,
            )
        except VerificationError:
            digest_rejected = True
        if not digest_rejected:
            raise AssertionError("self-test inconsistent model-context record digest was not rejected")

        def digest_record(object_id: str, theme_id: str) -> dict[str, Any]:
            token = lambda value: {"id": value, "label": value}
            return {
                "objectId": object_id,
                "medium": [token("MEDIUM-1")],
                "theme": [token(theme_id)],
                "movement_context": [],
                "decade": [token("DECADE-1900")],
                "geography": [token("GEO-1")],
                "curated_container": [token("CUR-1")],
                "source": token("SOURCE-1"),
                "object_type": token("TYPE-1"),
                "creator": token(f"CREATOR-{object_id[-1]}"),
                "startYear": 1900,
                "endYear": 1900,
                "temporalPrecision": "year",
                "geographyMappingStates": ["mapped"],
                "geographyClasses": ["country"],
                "geographyQualified": False,
                "multiRegion": False,
            }

        tiny_records = [
            digest_record("SURF-DIGEST-1", "THEME-1"),
            digest_record("SURF-DIGEST-2", "THEME-1"),
        ]
        tiny_index_sha256 = _sha256(b"tiny-candidate-index")
        tiny_receipts = _derive_model_context_receipts(
            tiny_records,
            tiny_index_sha256,
            expected_record_count=2,
        )
        if tiny_receipts != _derive_model_context_receipts(
            list(reversed(tiny_records)),
            tiny_index_sha256,
            expected_record_count=2,
        ):
            raise AssertionError("self-test model-context digest depends on input ordering")
        mutated_records = json.loads(json.dumps(tiny_records))
        mutated_records[1]["theme"] = [{"id": "THEME-2", "label": "THEME-2"}]
        mutated_receipts = _derive_model_context_receipts(
            mutated_records,
            tiny_index_sha256,
            expected_record_count=2,
        )
        if any(
            tiny_receipts[field] == mutated_receipts[field]
            for field in MODEL_CONTEXT_DIGEST_FIELDS
        ):
            raise AssertionError("self-test model-context digest did not bind a record mutation")

        candidate_only_records = json.loads(json.dumps(tiny_records))
        candidate_only_records[1]["geographyClasses"] = ["region"]
        original_normalized = _normalize_scoring_record(tiny_records[1])
        candidate_only_normalized = _normalize_scoring_record(candidate_only_records[1])
        expected_candidate_only = (
            _digest_token("candidateOnly", "geography_class", "country"),
        )
        if original_normalized.get("candidateOnlyTokens") != expected_candidate_only:
            raise AssertionError(
                "self-test scoring material lacks geography-class candidate-only tokens"
            )
        if (
            original_normalized["familyTokens"]
            != candidate_only_normalized["familyTokens"]
            or original_normalized["fieldValues"]
            != candidate_only_normalized["fieldValues"]
        ):
            raise AssertionError(
                "self-test candidate-only tokens leaked into model family/field statistics"
            )
        candidate_only_receipts = _derive_model_context_receipts(
            candidate_only_records,
            tiny_index_sha256,
            expected_record_count=2,
        )
        if tiny_receipts["scoringRecordsSha256"] == candidate_only_receipts[
            "scoringRecordsSha256"
        ]:
            raise AssertionError(
                "self-test scoring-record digest did not bind candidate-only tokens"
            )

        def mutated_explanation_package(
            mutate: Callable[[list[dict[str, Any]]], None]
        ) -> dict[str, Any]:
            """Return a fully self-hashed, model/human-mirrored adversarial package."""

            package = json.loads(json.dumps(loaded_raw))
            rows = package["model-benchmark-summary.json"]["explanationRows"]
            mutate(rows)
            for row in rows:
                unhashed = dict(row)
                unhashed.pop("explanationSha256", None)
                row["explanationSha256"] = _sha256(_canonical_json_bytes(unhashed))
            validation = package["model-benchmark-summary.json"][
                "explanationValidation"
            ]
            validation["explanationRowsSha256"] = _sha256(
                _canonical_json_bytes(rows)
            )
            package["human-review-summary.json"]["explanationRows"] = json.loads(
                json.dumps(rows)
            )
            package["human-review-summary.json"][
                "explanationValidation"
            ] = json.loads(json.dumps(validation))
            return package

        human_packet = _parse_tsv(research / "17_HUMAN_REVIEW_PACKET.tsv")

        def explanation_package_rejected(package: Mapping[str, Mapping[str, Any]]) -> bool:
            try:
                _validate_explanation_evidence(
                    package,
                    human_packet,
                    public_ids=public_ids,
                    held_ids=held_ids,
                    runs=package["analysis-run-summary.json"]["rows"],
                    shortlist={"M2", "M5", "M7"},
                    candidate_index_sha256=package[
                        "exploration-similarity-evaluation-summary.json"
                    ]["candidateIndexSha256"],
                    fixture=True,
                )
            except VerificationError:
                return True
            return False

        bad_explanation_raw = mutated_explanation_package(
            lambda rows: rows[0].__setitem__("retrievalReasons", [])
        )
        explanation_rejected = explanation_package_rejected(bad_explanation_raw)
        if not explanation_rejected:
            raise AssertionError(
                "self-test semantically empty standalone explanation was not rejected"
            )

        def remove_contribution_units(rows: list[dict[str, Any]]) -> None:
            rows[0].pop("familyContributionUnits")

        units_removal_rejected = explanation_package_rejected(
            mutated_explanation_package(remove_contribution_units)
        )
        if not units_removal_rejected:
            raise AssertionError(
                "self-test explanation without contribution units was not rejected"
            )

        def forge_contribution_share(rows: list[dict[str, Any]]) -> None:
            rows[0]["familyContributionShares"]["context"] = 0.5

        share_mutation_rejected = explanation_package_rejected(
            mutated_explanation_package(forge_contribution_share)
        )
        if not share_mutation_rejected:
            raise AssertionError(
                "self-test forged explanation contribution share was not rejected"
            )

        def forge_m7_formula(rows: list[dict[str, Any]]) -> None:
            m7_row = next(row for row in rows if row.get("methodId") == "M7")
            m7_row["affinityContributions"][0]["saturation"] = 0.5

        formula_mutation_rejected = explanation_package_rejected(
            mutated_explanation_package(forge_m7_formula)
        )
        if not formula_mutation_rejected:
            raise AssertionError(
                "self-test forged M7 explanation formula was not rejected"
            )

        def swap_analysis_run(rows: list[dict[str, Any]]) -> None:
            m2_row = next(row for row in rows if row.get("methodId") == "M2")
            m5_row = next(row for row in rows if row.get("methodId") == "M5")
            m2_row["analysisRunId"] = m5_row["analysisRunId"]

        run_binding_rejected = explanation_package_rejected(
            mutated_explanation_package(swap_analysis_run)
        )
        if not run_binding_rejected:
            raise AssertionError(
                "self-test swapped explanation analysis run was not rejected"
            )

        fixture_sources = [
            {"objectId": object_id, "source": {"id": f"SOURCE-{ordinal}"}}
            for ordinal, object_id in enumerate(sorted(public_ids))
        ]
        human_table = _parse_tsv(research / "17_HUMAN_REVIEW_PACKET.tsv")
        bad_human_rows = [dict(row) for row in human_table.rows]
        source_composition_column = _header(
            human_table, "source_composition", "sourceComposition"
        )
        bad_human_rows[0][source_composition_column] = "SAME_GOVERNED_SOURCE_NAME"
        source_composition_rejected = False
        try:
            _validate_explanation_evidence(
                loaded_raw,
                Table(human_table.name, human_table.headers, tuple(bad_human_rows)),
                public_ids=public_ids,
                held_ids=held_ids,
                runs=loaded_raw["analysis-run-summary.json"]["rows"],
                shortlist={"M2", "M5", "M7"},
                candidate_index_sha256=loaded_raw[
                    "exploration-similarity-evaluation-summary.json"
                ]["candidateIndexSha256"],
                fixture=True,
                normalized_records=fixture_sources,
            )
        except VerificationError:
            source_composition_rejected = True
        if not source_composition_rejected:
            raise AssertionError("self-test false governed-source composition was not rejected")

        target = research / "17_HUMAN_REVIEW_PACKET.tsv"
        original = target.read_bytes()
        target.write_bytes(original.replace(b"\tfalse\tfalse\tfalse\n", b"\tfalse\tfalse\ttrue\n", 1))
        rejected = False
        try:
            _validate_human_review(_parse_tsv(target), public_ids, held_ids)
        except VerificationError:
            rejected = True
        if not rejected:
            raise AssertionError("self-test negative fixture was not rejected")
        (boundary_frontend / "forbidden.py").write_text(
            "from . import negative_control\n",
            encoding="utf-8",
        )
        import_rejected = False
        try:
            _validate_negative_control_import_boundary(boundary_root)
        except VerificationError:
            import_rejected = True
        if not import_rejected:
            raise AssertionError("self-test forbidden negative-control import was not rejected")
        (boundary_frontend / "forbidden.py").unlink()
        (boundary_frontend / "forbidden.ts").write_text(
            "const loader = require; loader('./negative_control');\n",
            encoding="utf-8",
        )
        javascript_import_rejected = False
        try:
            _validate_negative_control_import_boundary(boundary_root)
        except VerificationError:
            javascript_import_rejected = True
        if not javascript_import_rejected:
            raise AssertionError("self-test aliased JavaScript negative-control import was not rejected")
        return {
            "status": result["status"],
            "negativeFixtureRejected": True,
            "forbiddenImportRejected": True,
            "javascriptImportRejected": True,
            "jointDenominatorRejected": True,
            "positiveExcessRejected": True,
            "scorerExperimentRejected": True,
            "contextDigestRejected": True,
            "cohortMutationRejected": True,
            "candidateOnlyDigestBound": True,
            "standaloneExplanationRejected": True,
            "contributionUnitsRemovalRejected": True,
            "contributionShareMutationRejected": True,
            "m7FormulaMutationRejected": True,
            "explanationRunBindingRejected": True,
            "sourceCompositionRejected": True,
            "invariantCount": result["invariantCount"],
        }


def _print_result(result: Mapping[str, Any], *, prefix: str = "VERIFY_ROUND1") -> None:
    for check in result.get("checks", ()):
        print(f"CHECK {check} PASS")
    for row in result.get("invariants", ()):
        print(f"INVARIANT {row['invariantId']} {row['status']}")
    print(
        f"{prefix} PASS checks={result.get('checkCount', 11)} "
        f"invariants={result['invariantCount']} research_files={result.get('researchFileCount', 24)} "
        f"research_tsvs={result.get('researchTsvCount', 11)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", type=Path, default=DEFAULT_RESEARCH_DIR)
    parser.add_argument("--audit-raw-dir", type=Path, default=DEFAULT_AUDIT_RAW_DIR)
    parser.add_argument("--repo-root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            result = self_test(args.repo_root)
            print(
                f"VERIFY_ROUND1_SELF_TEST PASS invariants={result['invariantCount']} "
                "negative_fixture_rejected=true forbidden_import_rejected=true "
                "javascript_import_rejected=true "
                "joint_denominator_rejected=true positive_excess_rejected=true "
                "scorer_experiment_rejected=true "
                "context_digest_rejected=true cohort_mutation_rejected=true "
                "candidate_only_digest_bound=true "
                "standalone_explanation_rejected=true contribution_units_removal_rejected=true "
                "contribution_share_mutation_rejected=true m7_formula_mutation_rejected=true "
                "explanation_run_binding_rejected=true source_composition_rejected=true"
            )
        else:
            result = verify(
                research_dir=args.research_dir,
                audit_raw_dir=args.audit_raw_dir,
                repo_root=args.repo_root,
            )
            _print_result(result)
    except (OSError, ValueError, VerificationError, json.JSONDecodeError) as error:
        print(f"VERIFY_ROUND1 FAIL {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
