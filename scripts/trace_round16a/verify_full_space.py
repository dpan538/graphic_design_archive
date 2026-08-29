#!/usr/bin/env python3
"""Independent, fail-closed verification of the Round 16A finite space.

This program intentionally imports no Round 16A generator, enumerator, frozen
Round 15 model, or frontend runtime. It reads committed artifacts, independently
derives their finite identities, executes the published transition relation,
and writes deterministic verification receipts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-full-space-closure-round1/raw")
RAW = REPO / RAW_REL
MODEL_REL = Path("frontend/generated/trace-exploration-v2/production-read-model.json")
MODEL = REPO / MODEL_REL

EXPECTED_DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
EXPECTED_CANDIDATES = 65
EXPECTED_ACTIVE_VOCABULARY = 31
EXPECTED_PAIRS = 465
EXPECTED_ACTIVE_ASSOCIATIONS = 21
EXPECTED_EXTERNALLY_SUPPORTED = 18
EXPECTED_SOURCE_SUPPORTED = 3
EXPECTED_SUBGRAPHS = 58
EXPECTED_TOPOLOGY_EVALUATIONS = 348
EXPECTED_TOPOLOGY_COMPOSITIONS = 81
EXPECTED_SEEDS = 228
EXPECTED_PRODUCTION_COMPOSITIONS = 228
EXPECTED_STATES = 5760
EXPECTED_TRANSITIONS = 749944
EXPECTED_WORKFLOWS = 5760
EXPECTED_EXPORTS = 11520
EXPECTED_PRODUCTION_MODEL_SHA256 = "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9"
EXPECTED_CATEGORIES = ("region", "theme", "medium", "movement")
TOPOLOGIES = ("LINEAR_PATH", "BINARY_FORK", "BINARY_CONVERGENCE", "QUALIFIED_PATH", "REFLEXIVE_RETURN", "EVIDENCE_GAP_TREE")
ACTIONS = ("SELECT_CATEGORY", "FOCUS_NODE", "EXPAND_NODE", "COLLAPSE_NODE", "MOVE_FOCUS", "SELECT_COMPOSITION", "RESET_CATEGORY", "EXPORT_CURRENT_STATE")
THEMES = ("neutral-v1", "neutral-contrast-v1")
EXPORT_PRESETS = ("portrait_card",)
ADAPTER_VERSION = "trace-round15-full-space-adapter-v2"

ACTIVE_ASSOCIATION_STATUSES = {"ACTIVE_EXTERNALLY_SUPPORTED", "ACTIVE_SOURCE_SUPPORTED"}
ALL_ASSOCIATION_STATUSES = ACTIVE_ASSOCIATION_STATUSES | {"INACTIVE_INSUFFICIENT_EVIDENCE", "INACTIVE_CONFLICTING_SCOPE", "INACTIVE_COOCCURRENCE_ONLY", "INACTIVE_HARD_NEGATIVE"}
VOCABULARY_DISPOSITIONS = {"ACTIVE": 31, "MERGED_SUPERSEDED": 1, "REJECTED": 12, "RESEARCH_ONLY": 21}

PNG_REQUIRED_COLUMNS = {
    "export_variant_id", "state_id", "theme_token_set", "export_preset", "manifest_validated",
    "manifest_schema_valid", "state_hash_match", "semantic_hash_match", "presentation_hash_match",
    "png_rendered", "png_decoded", "width", "height", "dimensions_valid", "upper_map_zone_valid",
    "lower_tree_zone_valid", "all_labels_valid", "all_visible_associations_valid",
    "provenance_summary_valid", "zero_archive_object_exposure", "png_sha256", "replay_png_sha256",
    "replay_match", "map_tree_state_match", "http_status", "elapsed_ms", "error_code",
}
API_TOP_LEVEL_FIELDS = {
    "schema_version", "status", "api_version", "base_url", "actual_production_http_tested", "case_count",
    "pass_count", "fail_count", "unexpected_5xx_count", "stale_state_accepted_count",
    "invalid_target_accepted_count", "held_data_leak_count", "public_archive_object_id_count",
    "public_archive_object_title_count", "public_record_link_count", "public_context_reference_count",
    "public_spacetime_reference_count", "cases",
}

SEMANTIC_ARTIFACTS = (
    "vocabulary-candidate-universe-v2.json", "vocabulary-candidate-universe-v2.tsv",
    "vocabulary-census-v2.json", "vocabulary-census-v2.tsv", "active-vocabulary-v2.json",
    "category-authority-v2.tsv", "database-identity-v2.json", "pair-universe-v2.json", "pair-universe-v2.tsv",
    "association-query-log-v2.jsonl", "association-census-v2.json", "association-census-v2.tsv",
    "association-evidence-ledger-v2.tsv", "validated-association-graph-v2.json", "graph-statistics-v2.json",
    "exploration-parameter-universe-v2.json", "composition-enumeration-v2.tsv",
    "composition-rejection-ledger-v2.tsv", "canonical-composition-registry-v2.json",
    "composition-statistics-v2.json", "category-entry-census-v2.tsv", "state-census-v2.tsv",
    "transition-census-v2.tsv", "workflow-census-v2.tsv", "export-census-v2.tsv",
    "production-read-model-metadata-v2.json", "space-generation-summary-v2.json",
    "api-functional-validation-v2.json", "png-validation-v2.tsv",
)
API_SOURCE_RELS = (
    Path("frontend/src/features/trace-v49/exploration-v2/client.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/controller.server.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/derive.server.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/read-model.server.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/renderer.server.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/service.server.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/theme-tokens.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/transition.server.ts"),
    Path("frontend/src/features/trace-v49/exploration-v2/types.ts"),
    Path("frontend/src/app/api/trace/v1/exploration/route.ts"),
    Path("frontend/src/app/api/trace/v1/exploration/[...path]/route.ts"),
    Path("frontend/src/app/api/trace/v2/exploration/route.ts"),
    Path("frontend/src/app/api/trace/v2/exploration/[...path]/route.ts"),
)
API_CONTRACT_RELS = (
    Path("schemas/trace/exploration/v2/action-request.schema.json"),
    Path("schemas/trace/exploration/v2/association-response.schema.json"),
    Path("schemas/trace/exploration/v2/capabilities-response.schema.json"),
    Path("schemas/trace/exploration/v2/category-response.schema.json"),
    Path("schemas/trace/exploration/v2/common.schema.json"),
    Path("schemas/trace/exploration/v2/error.schema.json"),
    Path("schemas/trace/exploration/v2/export-manifest.schema.json"),
    Path("schemas/trace/exploration/v2/export-request.schema.json"),
    Path("schemas/trace/exploration/v2/map-request.schema.json"),
    Path("schemas/trace/exploration/v2/map-response.schema.json"),
    Path("schemas/trace/exploration/v2/production-read-model.schema.json"),
    Path("schemas/trace/exploration/v2/vocabulary-response.schema.json"),
    Path("docs/api/trace-exploration-v2-error-catalog.md"),
    Path("docs/api/trace-exploration-v2-examples.json"),
    Path("docs/api/trace-exploration-v2-openapi.yaml"),
)
GENERATOR_SOURCE_RELS = (
    Path("scripts/trace_round16a/apply_authority_clarification.py"),
    Path("scripts/trace_round16a/capture_database_identity.py"),
    Path("scripts/trace_round16a/build_vocabulary_universe.py"),
    Path("scripts/trace_round16a/build_vocabulary_census.py"),
    Path("scripts/trace_round16a/build_pair_universe.py"),
    Path("scripts/trace_round16a/search_association_pairs.py"),
    Path("scripts/trace_round16a/build_association_census.py"),
    Path("scripts/trace_round16a/build_exploration_space.py"),
    Path("scripts/trace_round16a/build_final_gate_evidence.py"),
    Path("scripts/trace_round16a/build_operational_gate_receipts.py"),
    Path("scripts/trace_round16a/build_research_reports.py"),
    Path("scripts/trace_round16a/capture_final_integration_evidence.py"),
    Path("scripts/trace_round16a/run_logged.py"),
    Path("scripts/trace_round16a/seal_audit_package.py"),
    Path("scripts/trace_round16a/start_production_server.py"),
    Path("scripts/trace_round16a/summarize_runtime_results.py"),
    Path("scripts/trace_round16a/verify_authorized_lfs_migration.py"),
    Path("scripts/trace_round16a/verify_execution_log.py"),
    Path("scripts/trace_round16a/verify_full_space.py"),
    Path("scripts/trace_round16a/verify_repository_boundary.py"),
    Path("scripts/trace_round16a/verify_reproducibility.py"),
)
RUNTIME_HARNESS_SOURCE_RELS = (
    Path("scripts/trace_round16a/node_runtime_probe.cjs"),
    Path("frontend/scripts/benchmark-trace-exploration-v2-http.mjs"),
    Path("frontend/scripts/measure-trace-exploration-v2-model.mjs"),
    Path("frontend/scripts/test-trace-exploration-v2.mjs"),
    Path("frontend/scripts/validate-trace-exploration-v2-http.mjs"),
)
BUILD_CONFIG_RELS = (
    Path(".gitattributes"),
    Path("frontend/next.config.ts"),
    Path("frontend/package.json"),
    Path("frontend/package-lock.json"),
    Path("frontend/postcss.config.mjs"),
    Path("frontend/tailwind.config.ts"),
    Path("frontend/tsconfig.json"),
    Path("frontend/tsconfig.runtime-acceptance.json"),
)
ALL_SOURCE_RELS = (
    *API_SOURCE_RELS,
    *API_CONTRACT_RELS,
    *GENERATOR_SOURCE_RELS,
    *RUNTIME_HARNESS_SOURCE_RELS,
    *BUILD_CONFIG_RELS,
)
GATED_ARTIFACTS = {"api-functional-validation-v2.json", "png-validation-v2.tsv"}


def discovered_round16a_source_rels() -> set[Path]:
    """Discover governed source surfaces so new unsealed helpers fail closed."""
    discovered: set[Path] = set()
    for directory in (
        REPO / "frontend/src/app/api/trace/v1/exploration",
        REPO / "frontend/src/app/api/trace/v2/exploration",
        REPO / "frontend/src/features/trace-v49/exploration-v2",
        REPO / "schemas/trace/exploration/v2",
        REPO / "scripts/trace_round16a",
    ):
        if directory.is_dir():
            discovered.update(
                path.relative_to(REPO)
                for path in directory.rglob("*")
                if path.is_file() and path.suffix in {".ts", ".json", ".py", ".cjs"}
            )
    api_docs = REPO / "docs/api"
    if api_docs.is_dir():
        discovered.update(
            path.relative_to(REPO)
            for path in api_docs.glob("trace-exploration-v2-*")
            if path.is_file()
        )
    frontend_scripts = REPO / "frontend/scripts"
    if frontend_scripts.is_dir():
        discovered.update(
            path.relative_to(REPO)
            for path in frontend_scripts.glob("*trace-exploration-v2*")
            if path.is_file()
        )
    return discovered


def uninventoried_round16a_source_rels() -> list[Path]:
    return sorted(
        discovered_round16a_source_rels() - set(ALL_SOURCE_RELS),
        key=lambda path: path.as_posix(),
    )


def compact(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_hash(value: Any, *, newline: bool = False) -> str:
    return hashlib.sha256(compact(value) + (b"\n" if newline else b"")).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_label(value: str) -> str:
    clean = re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", clean)).casefold()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().casefold()
    if text in {"true", "1", "yes", "pass", "passed"}:
        return True
    if text in {"false", "0", "no", "fail", "failed", ""}:
        return False
    raise ValueError(f"not a Boolean value: {value!r}")


def as_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Boolean is not an integer: {value!r}")
    return int(value)


def json_cell(value: Any, expected: type = list) -> Any:
    if isinstance(value, expected):
        return value
    parsed = json.loads(str(value))
    if not isinstance(parsed, expected):
        raise ValueError(f"expected {expected.__name__} JSON cell")
    return parsed


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{number} is not an object")
                rows.append(row)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compact(value) + b"\n")


def json_safe(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        return [json_safe(item) for item in sorted(value, key=lambda item: str(item))]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(child) for key, child in value.items()}
    return value


class Audit:
    def __init__(self) -> None:
        self.cases: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {}

    def check(self, case_id: str, condition: bool, *, domain: str, expected: Any, actual: Any,
              sources: Sequence[str] = (), detail: str = "", skipped: bool = False) -> bool:
        self.cases.append({"case_id": case_id, "domain": domain,
                           "status": "SKIP" if skipped else ("PASS" if condition else "FAIL"),
                           "expected": json_safe(expected), "actual": json_safe(actual),
                           "sources": list(sources), "detail": detail})
        return condition or skipped

    def equal(self, case_id: str, actual: Any, expected: Any, *, domain: str,
              sources: Sequence[str] = (), detail: str = "") -> bool:
        return self.check(case_id, actual == expected, domain=domain, expected=expected, actual=actual,
                          sources=sources, detail=detail)

    @property
    def failures(self) -> list[dict[str, Any]]:
        return [row for row in self.cases if row["status"] == "FAIL"]


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def require_inputs(audit: Audit, allow_incomplete_gates: bool) -> bool:
    missing: list[str] = []
    for name in SEMANTIC_ARTIFACTS:
        path = RAW / name
        if path.is_file():
            continue
        if allow_incomplete_gates and name in GATED_ARTIFACTS:
            audit.check(f"INPUT.GATE.{name}", True, domain="inputs", expected="present at final gate",
                        actual="not yet present", sources=[rel(path)], skipped=True,
                        detail="Development-only deferral; normal final verification fails this absence.")
        else:
            missing.append(rel(path))
    if not MODEL.is_file():
        missing.append(rel(MODEL))
    for path_rel in ALL_SOURCE_RELS:
        if not (REPO / path_rel).is_file():
            missing.append(path_rel.as_posix())
    missing.extend(
        f"UNINVENTORIED_ROUND16A_SOURCE:{path.as_posix()}"
        for path in uninventoried_round16a_source_rels()
    )
    return audit.equal("INPUT.REQUIRED_ARTIFACTS", missing, [], domain="inputs",
                       sources=[RAW_REL.as_posix(), MODEL_REL.as_posix()])


def evidence_reference_universe() -> tuple[set[str], set[str], list[str]]:
    """Resolve only IDs found in governed evidence/source registry columns."""
    paths = [
        Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/03_SCHOLARLY_SOURCE_REGISTRY.tsv"),
        Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv"),
        Path("docs/research/trace-v49-design-history-relation-grammar-round1/03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv"),
        Path("docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv"),
        Path("docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv"),
        Path("docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv"),
        Path("docs/research/trace-v49-exploration-composition-review-round1/06_VOCABULARY_GAP_EVIDENCE.tsv"),
        Path("docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv"),
        Path("scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv"),
    ]
    source_ids: set[str] = set()
    evidence_ids: set[str] = set()
    used: list[str] = []
    for path_rel in paths:
        path = REPO / path_rel
        if not path.is_file():
            continue
        used.append(path_rel.as_posix())
        for row in read_tsv(path):
            for key, value in row.items():
                value = (value or "").strip()
                if not value:
                    continue
                folded = key.casefold()
                if folded == "source_id" or folded.endswith("_source_id"):
                    source_ids.add(value)
                if "attestation_id" in folded or folded == "evidence_id" or folded.endswith("_evidence_id"):
                    evidence_ids.add(value)
    return source_ids, evidence_ids, used


def verify_vocabulary(audit: Audit) -> dict[str, Any]:
    universe_path = RAW / "vocabulary-candidate-universe-v2.json"
    census_path = RAW / "vocabulary-census-v2.json"
    active_path = RAW / "active-vocabulary-v2.json"
    universe = read_json(universe_path)
    census = read_json(census_path)
    active_doc = read_json(active_path)
    universe_tsv = read_tsv(RAW / "vocabulary-candidate-universe-v2.tsv")
    census_tsv = read_tsv(RAW / "vocabulary-census-v2.tsv")
    category_rows = read_tsv(RAW / "category-authority-v2.tsv")

    candidates = universe.get("candidates", [])
    census_rows = census.get("candidates", [])
    active = active_doc.get("active_vocabulary", [])
    audit.equal("VOCAB.CANDIDATE_COUNT", len(candidates), EXPECTED_CANDIDATES,
                domain="vocabulary", sources=[rel(universe_path)])
    audit.equal("VOCAB.CANDIDATE_TSV_COUNT", len(universe_tsv), EXPECTED_CANDIDATES,
                domain="vocabulary", sources=[rel(RAW / "vocabulary-candidate-universe-v2.tsv")])
    audit.equal("VOCAB.CENSUS_COUNT", len(census_rows), EXPECTED_CANDIDATES,
                domain="vocabulary", sources=[rel(census_path)])
    audit.equal("VOCAB.CENSUS_TSV_COUNT", len(census_tsv), EXPECTED_CANDIDATES,
                domain="vocabulary", sources=[rel(RAW / "vocabulary-census-v2.tsv")])
    universe_material = {key: value for key, value in universe.items() if key != "universe_canonical_hash"}
    audit.equal("VOCAB.UNIVERSE_HASH", canonical_hash(universe_material, newline=True),
                universe.get("universe_canonical_hash"), domain="vocabulary", sources=[rel(universe_path)])
    normalized = [normalize_label(str(row.get("canonical_label", ""))) for row in candidates]
    audit.equal("VOCAB.NORMALIZED_LABEL_UNIQUENESS", len(set(normalized)), EXPECTED_CANDIDATES,
                domain="vocabulary", sources=[rel(universe_path)])
    audit.equal("VOCAB.CANDIDATE_ID_COVERAGE",
                {row.get("vocabulary_candidate_id") for row in candidates},
                {row.get("vocabulary_candidate_id") for row in census_rows},
                domain="vocabulary", sources=[rel(universe_path), rel(census_path)])
    dispositions = Counter(str(row.get("disposition")) for row in census_rows)
    audit.equal("VOCAB.DISPOSITION_COUNTS", dict(dispositions), VOCABULARY_DISPOSITIONS,
                domain="vocabulary", sources=[rel(census_path)])
    audit.equal("VOCAB.DECLARED_DISPOSITION_COUNTS", census.get("disposition_counts"), VOCABULARY_DISPOSITIONS,
                domain="vocabulary", sources=[rel(census_path)])
    audit.equal("VOCAB.CENSUS_HASH", canonical_hash(census_rows, newline=True), census.get("vocabulary_census_hash"),
                domain="vocabulary", sources=[rel(census_path)])

    active_top_fields = {"active_vocabulary", "active_vocabulary_count", "universe_hash",
                         "active_vocabulary_hash", "database_snapshot"}
    active_row_fields = {"vocabulary_id", "canonical_label", "normalized_label", "category_ids",
                         "bounded_sense", "scope_note", "ambiguity_note", "source_attestations",
                         "academic_support"}
    audit.equal("VOCAB.ACTIVE_TOP_LEVEL_CONTRACT", set(active_doc), active_top_fields,
                domain="vocabulary", sources=[rel(active_path)])
    audit.equal("VOCAB.ACTIVE_COUNT", len(active), EXPECTED_ACTIVE_VOCABULARY,
                domain="vocabulary", sources=[rel(active_path)])
    audit.equal("VOCAB.ACTIVE_DECLARED_COUNT", active_doc.get("active_vocabulary_count"), EXPECTED_ACTIVE_VOCABULARY,
                domain="vocabulary", sources=[rel(active_path)])
    malformed = [row.get("vocabulary_id", "<missing>") for row in active if set(row) != active_row_fields]
    audit.equal("VOCAB.ACTIVE_ROW_CONTRACT", malformed, [], domain="vocabulary", sources=[rel(active_path)])
    ids = [str(row.get("vocabulary_id", "")) for row in active]
    normalized_active = [str(row.get("normalized_label", "")) for row in active]
    audit.equal("VOCAB.ACTIVE_ID_UNIQUENESS", len(set(ids)), EXPECTED_ACTIVE_VOCABULARY,
                domain="vocabulary", sources=[rel(active_path)])
    audit.equal("VOCAB.ACTIVE_NORMALIZED_UNIQUENESS", len(set(normalized_active)), EXPECTED_ACTIVE_VOCABULARY,
                domain="vocabulary", sources=[rel(active_path)])
    normalization_errors = [row.get("vocabulary_id") for row in active
                            if normalize_label(str(row.get("canonical_label", ""))) != row.get("normalized_label")]
    audit.equal("VOCAB.ACTIVE_NORMALIZATION", normalization_errors, [], domain="vocabulary", sources=[rel(active_path)])
    active_from_census = [{key: row[key] for key in active_row_fields}
                          for row in census_rows if row.get("disposition") == "ACTIVE"]
    audit.equal("VOCAB.ACTIVE_CENSUS_PROJECTION", active, active_from_census,
                domain="vocabulary", sources=[rel(active_path), rel(census_path)])
    audit.equal("VOCAB.ACTIVE_HASH", canonical_hash(active, newline=True), active_doc.get("active_vocabulary_hash"),
                domain="vocabulary", sources=[rel(active_path)])
    audit.equal("VOCAB.UNIVERSE_HASH_CHAIN", active_doc.get("universe_hash"), universe.get("universe_canonical_hash"),
                domain="vocabulary", sources=[rel(active_path), rel(universe_path)])
    audit.equal("VOCAB.DATABASE_SNAPSHOT", active_doc.get("database_snapshot"), EXPECTED_DATABASE_SNAPSHOT,
                domain="vocabulary", sources=[rel(active_path)])

    source_ids, evidence_ids, registry_sources = evidence_reference_universe()
    unresolved_attestations: list[str] = []
    unresolved_sources: list[str] = []
    content_errors: list[str] = []
    categories = set(EXPECTED_CATEGORIES)
    for row in active:
        row_id = str(row.get("vocabulary_id"))
        for field in ("canonical_label", "normalized_label", "bounded_sense", "scope_note", "ambiguity_note"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                content_errors.append(f"{row_id}:{field}")
        for field in ("category_ids", "source_attestations", "academic_support"):
            if not isinstance(row.get(field), list) or not row[field]:
                content_errors.append(f"{row_id}:{field}")
        if not set(row.get("category_ids", [])) <= categories:
            content_errors.append(f"{row_id}:category_ids")
        for ref in row.get("source_attestations", []):
            parent_source = str(ref).split(":attestation:", 1)[0]
            if ref not in evidence_ids and parent_source not in source_ids:
                unresolved_attestations.append(str(ref))
        for ref in row.get("academic_support", []):
            if ref not in source_ids:
                unresolved_sources.append(str(ref))
    audit.equal("VOCAB.ACTIVE_EVIDENCE_GATES", content_errors, [], domain="vocabulary", sources=[rel(active_path)])
    audit.equal("VOCAB.ATTESTATION_RESOLUTION", sorted(set(unresolved_attestations)), [],
                domain="vocabulary", sources=registry_sources)
    audit.equal("VOCAB.ACADEMIC_SOURCE_RESOLUTION", sorted(set(unresolved_sources)), [],
                domain="vocabulary", sources=registry_sources)

    category_by_id = {row.get("category_id"): row for row in category_rows}
    audit.equal("VOCAB.CATEGORY_AUTHORITY_IDS", set(category_by_id), categories,
                domain="vocabulary", sources=[rel(RAW / "category-authority-v2.tsv")])
    invalid_category_rows: list[str] = []
    for category_id, row in category_by_id.items():
        try:
            valid = (row.get("status") == "PASS" and as_bool(row.get("database_authority_validated"))
                     and as_int(row.get("eligible_binding_row_count")) > 0
                     and as_int(row.get("eligible_folder_count")) > 0
                     and as_int(row.get("eligible_surface_count")) > 0
                     and as_int(row.get("real_folder_count")) > 0)
        except (TypeError, ValueError):
            valid = False
        if not valid:
            invalid_category_rows.append(str(category_id))
    audit.equal("VOCAB.CATEGORY_AUTHORITY_GATES", invalid_category_rows, [],
                domain="vocabulary", sources=[rel(RAW / "category-authority-v2.tsv")])
    database_identity_path = RAW / "database-identity-v2.json"
    database_identity = read_json(database_identity_path)
    category_identity = database_identity.get("category_authority", {})
    audit.equal("VOCAB.DATABASE_IDENTITY_SNAPSHOT", database_identity.get("database_snapshot_id"),
                EXPECTED_DATABASE_SNAPSHOT, domain="vocabulary", sources=[rel(database_identity_path)])
    audit.equal("VOCAB.DATABASE_IDENTITY_STATUS", database_identity.get("status"), "PASS",
                domain="vocabulary", sources=[rel(database_identity_path)])
    audit.equal("VOCAB.CATEGORY_AUTHORITY_FILE_HASH", database_identity.get("category_authority_sha256"),
                sha256_path(RAW / "category-authority-v2.tsv"), domain="vocabulary",
                sources=[rel(database_identity_path), rel(RAW / "category-authority-v2.tsv")])
    audit.equal("VOCAB.DATABASE_IDENTITY_CATEGORY_COUNT", category_identity.get("governed_folder_type_count"),
                len(EXPECTED_CATEGORIES), domain="vocabulary", sources=[rel(database_identity_path)])
    audit.equal("VOCAB.DATABASE_IDENTITY_CATEGORY_SET",
                set(category_identity.get("observed_governed_folder_types", [])), categories,
                domain="vocabulary", sources=[rel(database_identity_path)])
    audit.equal("VOCAB.DATABASE_IDENTITY_CATEGORY_ZERO_GAPS",
                (category_identity.get("category_without_eligible_binding_count"),
                 category_identity.get("category_without_real_folder_count")), (0, 0),
                domain="vocabulary", sources=[rel(database_identity_path)])
    audit.equal("VOCAB.DATABASE_IDENTITY_CATEGORY_PASS",
                database_identity.get("validation", {}).get("four_category_authority"), "PASS",
                domain="vocabulary", sources=[rel(database_identity_path)])
    category_counts = Counter(category for row in active for category in row.get("category_ids", []))
    audit.equal("VOCAB.ACTIVE_CATEGORY_COVERAGE", set(category_counts), categories,
                domain="vocabulary", sources=[rel(active_path)])
    audit.metrics.update({"VOCABULARY_CANDIDATE_COUNT": len(candidates), "ACTIVE_VOCABULARY_COUNT": len(active),
                          "VOCABULARY_CANDIDATE_UNIVERSE_COUNT": len(candidates),
                          "VOCABULARY_CANDIDATE_UNIVERSE_FROZEN": universe.get("frozen") is True,
                          "UNATTESTED_ACTIVE_VOCABULARY_COUNT": len(set(unresolved_attestations)),
                          "ACADEMICALLY_UNSUPPORTED_ACTIVE_VOCABULARY_COUNT": len(set(unresolved_sources)),
                          "INVENTED_ACTIVE_VOCABULARY_COUNT": len(content_errors),
                          "VOCABULARY_DISPOSITION_COUNTS": dict(sorted(dispositions.items())),
                          "ACTIVE_VOCABULARY_CATEGORY_COUNTS": dict(sorted(category_counts.items()))})
    return {"active_document": active_doc, "active": active,
            "active_by_id": {row["vocabulary_id"]: row for row in active}, "census": census}


def expected_pair_rows(active: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ordered = sorted(active, key=lambda row: row["vocabulary_id"])
    for ordinal, (left, right) in enumerate(itertools.combinations(ordered, 2), 1):
        key = f"{left['vocabulary_id']}|{right['vocabulary_id']}"
        rows.append({"ordinal": ordinal,
                     "pair_id": f"R16A-PAIR:{hashlib.sha256(key.encode('utf-8')).hexdigest()}",
                     "vocabulary_id_a": left["vocabulary_id"], "vocabulary_id_b": right["vocabulary_id"],
                     "label_a": left["canonical_label"], "label_b": right["canonical_label"],
                     "normalized_label_a": left["normalized_label"], "normalized_label_b": right["normalized_label"],
                     "canonical_pair_key": key, "structurally_excluded": False})
    return rows


def normalized_pair_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {"ordinal": as_int(row["ordinal"]), "pair_id": row["pair_id"],
            "vocabulary_id_a": row["vocabulary_id_a"], "vocabulary_id_b": row["vocabulary_id_b"],
            "label_a": row["label_a"], "label_b": row["label_b"],
            "normalized_label_a": row["normalized_label_a"], "normalized_label_b": row["normalized_label_b"],
            "canonical_pair_key": row["canonical_pair_key"],
            "structurally_excluded": as_bool(row["structurally_excluded"])}


def expected_crossref_query(label_a: str, label_b: str) -> str:
    def quoted(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return f'{quoted(label_a)} {quoted(label_b)} "graphic design" "design history"'


def graph_components(nodes: Sequence[str], edges: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    adjacency = {node: set() for node in nodes}
    for edge in edges:
        a, b = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen = set(nodes)
    parts: list[list[str]] = []
    while unseen:
        root = min(unseen)
        seen = {root}
        queue = [root]
        while queue:
            current = queue.pop()
            for neighbour in adjacency[current] - seen:
                seen.add(neighbour)
                queue.append(neighbour)
        unseen -= seen
        parts.append(sorted(seen))
    return sorted(parts, key=lambda part: (len(part), part))


def articulation_and_bridges(nodes: Sequence[str], edges: Sequence[Mapping[str, Any]]) -> tuple[list[str], list[str]]:
    adjacency = {node: set() for node in nodes}
    edge_ids: dict[frozenset[str], str] = {}
    for edge in edges:
        a, b = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
        adjacency[a].add(b)
        adjacency[b].add(a)
        edge_ids[frozenset((a, b))] = str(edge["association_id"])
    discovered: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    cuts: set[str] = set()
    bridges: set[str] = set()
    clock = 0

    def visit(node: str) -> None:
        nonlocal clock
        clock += 1
        discovered[node] = low[node] = clock
        children = 0
        for neighbour in sorted(adjacency[node]):
            if neighbour not in discovered:
                parent[neighbour] = node
                children += 1
                visit(neighbour)
                low[node] = min(low[node], low[neighbour])
                if parent[node] is None and children > 1:
                    cuts.add(node)
                if parent[node] is not None and low[neighbour] >= discovered[node]:
                    cuts.add(node)
                if low[neighbour] > discovered[node]:
                    bridges.add(edge_ids[frozenset((node, neighbour))])
            elif neighbour != parent[node]:
                low[node] = min(low[node], discovered[neighbour])

    for node in sorted(nodes):
        if node not in discovered:
            parent[node] = None
            visit(node)
    return sorted(cuts), sorted(bridges)


def independent_round14_status(row: Mapping[str, Any]) -> str:
    strength = {"NONE": 0, "WEAK": 1, "MODERATE": 2, "STRONG": 3}.get(str(row.get("association_strength")), -1)
    confidence = {"NONE": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3}.get(str(row.get("evidence_confidence")), -1)
    try:
        dimensions = all(as_int(row.get(key)) >= 1 for key in ("d1", "d5", "d7"))
        cooccurrence = as_bool(row.get("cooccurrence_only"))
        hard_negative = as_bool(row.get("hard_negative"))
    except ValueError:
        return "MALFORMED_ROUND14_ROW"
    evidence_status = str(row.get("evidence_status"))
    active = (strength >= 2 and confidence >= 2 and dimensions
              and evidence_status in {"EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED"}
              and not cooccurrence and not hard_negative)
    if active:
        return "ACTIVE_EXTERNALLY_SUPPORTED" if evidence_status == "EXTERNALLY_SUPPORTED" else "ACTIVE_SOURCE_SUPPORTED"
    if hard_negative:
        return "INACTIVE_HARD_NEGATIVE"
    if cooccurrence:
        return "INACTIVE_COOCCURRENCE_ONLY"
    if row.get("assessment_id") == "R14-ASSOC-022":
        return "INACTIVE_CONFLICTING_SCOPE"
    return "INACTIVE_INSUFFICIENT_EVIDENCE"


def verify_pairs_and_graph(audit: Audit, vocabulary: dict[str, Any]) -> dict[str, Any]:
    pair_json_path = RAW / "pair-universe-v2.json"
    pair_tsv_path = RAW / "pair-universe-v2.tsv"
    pair_doc = read_json(pair_json_path)
    pair_tsv = read_tsv(pair_tsv_path)
    expected = expected_pair_rows(vocabulary["active"])
    observed_json = [normalized_pair_row(row) for row in pair_doc.get("pairs", [])]
    observed_tsv = [normalized_pair_row(row) for row in pair_tsv]
    audit.equal("PAIR.EQUATION_31_CHOOSE_2", EXPECTED_ACTIVE_VOCABULARY * 30 // 2, EXPECTED_PAIRS,
                domain="pairs", sources=[rel(pair_json_path)])
    audit.equal("PAIR.JSON_EXACT_UNIVERSE", observed_json, expected, domain="pairs", sources=[rel(pair_json_path)])
    audit.equal("PAIR.TSV_EXACT_UNIVERSE", observed_tsv, expected, domain="pairs", sources=[rel(pair_tsv_path)])
    pair_material = {key: value for key, value in pair_doc.items() if key != "pair_universe_hash"}
    audit.equal("PAIR.UNIVERSE_HASH", canonical_hash(pair_material, newline=True), pair_doc.get("pair_universe_hash"),
                domain="pairs", sources=[rel(pair_json_path)])
    self_rows = pair_doc.get("self_pair_exclusions", [])
    audit.equal("PAIR.SELF_EXCLUSION_COUNT", len(self_rows), EXPECTED_ACTIVE_VOCABULARY,
                domain="pairs", sources=[rel(pair_json_path)])
    audit.equal("PAIR.SELF_EXCLUSION_COVERAGE", {row.get("vocabulary_id") for row in self_rows},
                set(vocabulary["active_by_id"]), domain="pairs", sources=[rel(pair_json_path)])
    self_errors: list[str] = []
    for row in self_rows:
        vocabulary_id = str(row.get("vocabulary_id", ""))
        key = f"{vocabulary_id}|{vocabulary_id}"
        expected_id = f"R16A-SELF-PAIR-EXCLUSION:{hashlib.sha256(key.encode('utf-8')).hexdigest()}"
        active_row = vocabulary["active_by_id"].get(vocabulary_id, {})
        if (row.get("canonical_self_pair_key") != key or row.get("self_pair_exclusion_id") != expected_id
                or row.get("canonical_label") != active_row.get("canonical_label")
                or row.get("reason") != "SELF_PAIR_STRUCTURALLY_EXCLUDED"):
            self_errors.append(vocabulary_id)
    audit.equal("PAIR.SELF_EXCLUSION_IDENTITIES", self_errors, [], domain="pairs", sources=[rel(pair_json_path)])

    query_path = RAW / "association-query-log-v2.jsonl"
    queries = read_jsonl(query_path)
    query_by_pair = {row.get("pair_id"): row for row in queries}
    audit.equal("PAIR.QUERY_ROW_COUNT", len(queries), EXPECTED_PAIRS,
                domain="pairs", sources=[rel(query_path)])
    audit.equal("PAIR.QUERY_UNIQUE_COUNT", len(query_by_pair), EXPECTED_PAIRS,
                domain="pairs", sources=[rel(query_path)])
    audit.equal("PAIR.QUERY_EXACT_COVERAGE", set(query_by_pair), {row["pair_id"] for row in expected},
                domain="pairs", sources=[rel(query_path)])
    query_errors: list[str] = []
    expected_pair_by_id = {row["pair_id"]: row for row in expected}
    for pair_id, row in query_by_pair.items():
        candidates = row.get("candidate_results", [])
        pair = expected_pair_by_id.get(pair_id, {})
        expected_query = expected_crossref_query(str(pair.get("label_a", "")), str(pair.get("label_b", "")))
        if row.get("query") != expected_query or row.get("channel") != "CROSSREF_REST_WORKS_PUBLIC_POOL":
            query_errors.append(f"{pair_id}:query_or_channel")
        if row.get("timestamp_source") != "FROZEN_PER_RESPONSE_TIMESTAMP" or row.get("timestamp") != row.get("frozen_response_timestamp_utc"):
            query_errors.append(f"{pair_id}:frozen_timestamp")
        if row.get("accepted_source_ids") != []:
            query_errors.append(f"{pair_id}:accepted_source_ids")
        if row.get("result_review_status") != "NOT_ACCEPTED_METADATA_ONLY_PENDING_TEXT_REVIEW":
            query_errors.append(f"{pair_id}:result_review_status")
        if row.get("candidate_source_ids") != [item.get("candidate_source_id") for item in candidates]:
            query_errors.append(f"{pair_id}:candidate_source_ids")
        if row.get("rejected_source_ids") != row.get("candidate_source_ids"):
            query_errors.append(f"{pair_id}:rejected_source_ids")
        if any(item.get("review_status") != "NOT_ACCEPTED_METADATA_ONLY_PENDING_TEXT_REVIEW"
               or item.get("accepted") is not False for item in candidates):
            query_errors.append(f"{pair_id}:candidate_review")
        protocol = row.get("query_protocol", {})
        if protocol.get("metadata_or_snippet_is_evidence") is not False or protocol.get("new_vocabulary_admitted") is not False:
            query_errors.append(f"{pair_id}:query_protocol")
    audit.equal("PAIR.QUERY_METADATA_NOT_EVIDENCE", sorted(query_errors), [], domain="pairs", sources=[rel(query_path)])

    census_path = RAW / "association-census-v2.json"
    census_doc = read_json(census_path)
    census_rows = census_doc.get("pairs", [])
    census_tsv = read_tsv(RAW / "association-census-v2.tsv")
    census_by_pair = {row.get("pair_id"): row for row in census_rows}
    statuses = Counter(str(row.get("final_status")) for row in census_rows)
    active_rows = [row for row in census_rows if row.get("final_status") in ACTIVE_ASSOCIATION_STATUSES]
    audit.equal("ASSOCIATION.CENSUS_COUNT", len(census_rows), EXPECTED_PAIRS,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.CENSUS_TSV_COUNT", len(census_tsv), EXPECTED_PAIRS,
                domain="associations", sources=[rel(RAW / "association-census-v2.tsv")])
    audit.equal("ASSOCIATION.PAIR_STATUS_COVERAGE", set(census_by_pair), {row["pair_id"] for row in expected},
                domain="associations", sources=[rel(census_path), rel(pair_json_path)])
    audit.equal("ASSOCIATION.STATUS_VOCABULARY", set(statuses) <= ALL_ASSOCIATION_STATUSES, True,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.STATUS_SUM", sum(statuses.values()), EXPECTED_PAIRS,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.DECLARED_STATUS_COUNTS", census_doc.get("status_counts"), dict(sorted(statuses.items())),
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.EXTERNALLY_SUPPORTED", statuses["ACTIVE_EXTERNALLY_SUPPORTED"], EXPECTED_EXTERNALLY_SUPPORTED,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.SOURCE_SUPPORTED", statuses["ACTIVE_SOURCE_SUPPORTED"], EXPECTED_SOURCE_SUPPORTED,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.ACTIVE_EQUATION", len(active_rows), EXPECTED_EXTERNALLY_SUPPORTED + EXPECTED_SOURCE_SUPPORTED,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.UNRESOLVED", census_doc.get("unresolved_pair_count"), 0,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.PENDING_ACTIVE_VALIDATION", census_doc.get("active_association_with_pending_validation_count"), 0,
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.CENSUS_HASH", canonical_hash(census_rows), census_doc.get("census_hash"),
                domain="associations", sources=[rel(census_path)])

    round14_path = REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/association-calibration.tsv"
    round14_rows = read_tsv(round14_path)
    active_by_label = {row["canonical_label"].casefold(): row for row in vocabulary["active"]}
    governed_status_by_pair: dict[str, tuple[str, str]] = {}
    outside_active = 0
    for row in round14_rows:
        left = active_by_label.get(str(row.get("node_a", "")).casefold())
        right = active_by_label.get(str(row.get("node_b", "")).casefold())
        if not left or not right:
            outside_active += 1
            continue
        pair_key = "|".join(sorted((left["vocabulary_id"], right["vocabulary_id"])))
        pair_id = next(expected_row["pair_id"] for expected_row in expected
                       if expected_row["canonical_pair_key"] == pair_key)
        governed_status_by_pair[pair_id] = (independent_round14_status(row), str(row.get("assessment_id")))
    expected_status_by_pair = {row["pair_id"]: "INACTIVE_INSUFFICIENT_EVIDENCE" for row in expected}
    expected_status_by_pair.update({pair_id: status for pair_id, (status, _) in governed_status_by_pair.items()})
    status_reconciliation_errors: list[str] = []
    for pair_id, expected_status in expected_status_by_pair.items():
        observed = census_by_pair.get(pair_id, {})
        if observed.get("final_status") != expected_status:
            status_reconciliation_errors.append(f"{pair_id}:status")
        governed = governed_status_by_pair.get(pair_id)
        expected_assessment = governed[1] if governed else ""
        if observed.get("round14_assessment_id", "") != expected_assessment:
            status_reconciliation_errors.append(f"{pair_id}:round14_assessment_id")
    audit.equal("ASSOCIATION.ROUND14_ROW_COUNT", len(round14_rows), 35,
                domain="associations", sources=[rel(round14_path)])
    audit.equal("ASSOCIATION.ROUND14_ACTIVE_ENDPOINT_PAIR_COUNT", len(governed_status_by_pair), 31,
                domain="associations", sources=[rel(round14_path)])
    audit.equal("ASSOCIATION.ROUND14_OUTSIDE_ACTIVE_ENDPOINT_COUNT", outside_active, 4,
                domain="associations", sources=[rel(round14_path)])
    reconciliation_rows = census_doc.get("round14_reconciliation", [])
    reconciliation_errors = [row.get("assessment_id") for row in reconciliation_rows
                             if row.get("decision_reconciliation") != "PRESERVED"
                             or row.get("new_evidence_changed_decision") is not False
                             or row.get("method_changed_decision") is not False]
    audit.equal("ASSOCIATION.ROUND14_RECONCILIATION_COUNT", len(reconciliation_rows), len(round14_rows),
                domain="associations", sources=[rel(census_path), rel(round14_path)])
    audit.equal("ASSOCIATION.ROUND14_RECONCILIATION_GATES", reconciliation_errors, [],
                domain="associations", sources=[rel(census_path)])
    audit.equal("ASSOCIATION.INDEPENDENT_STATUS_RECONCILIATION", status_reconciliation_errors, [],
                domain="associations", sources=[rel(round14_path), rel(census_path)])

    evidence_path = RAW / "association-evidence-ledger-v2.tsv"
    evidence_rows = read_tsv(evidence_path)
    evidence_by_pair: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_pair[row.get("pair_id", "")].append(row)
    evidence_errors: list[str] = []
    for row in census_rows:
        pair_id = str(row.get("pair_id"))
        ledgers = evidence_by_pair.get(pair_id, [])
        if row.get("final_status") in ACTIVE_ASSOCIATION_STATUSES:
            accepted_refs = set(row.get("accepted_evidence_refs", []))
            supported = {ledger.get("ledger_id", "").removeprefix("R16A-") for ledger in ledgers
                         if as_bool(ledger.get("supports_active_edge")) and as_bool(ledger.get("evidence_verified"))}
            if not accepted_refs or not accepted_refs <= supported:
                evidence_errors.append(f"{pair_id}:active_evidence")
        for ledger in ledgers:
            if ledger.get("evidence_channel") == "CROSSREF_DISCOVERY_METADATA" and as_bool(ledger.get("supports_active_edge")):
                evidence_errors.append(f"{pair_id}:crossref_promoted")
    audit.equal("ASSOCIATION.EVIDENCE_LEDGER_GATES", evidence_errors, [],
                domain="associations", sources=[rel(evidence_path), rel(census_path)])
    nonclaim_errors: list[str] = []
    for row in census_rows:
        if bool(row.get("active")) != (row.get("final_status") in ACTIVE_ASSOCIATION_STATUSES):
            nonclaim_errors.append(f"{row.get('pair_id')}:active")
        for field in ("typed_relation_emitted", "causal_relation_emitted", "directional_relation_emitted",
                      "database_text_cooccurrence_used", "database_metadata_relation_inferred"):
            if bool(row.get(field)):
                nonclaim_errors.append(f"{row.get('pair_id')}:{field}")
    audit.equal("ASSOCIATION.BOUNDED_NONCLAIM_GATES", nonclaim_errors, [],
                domain="associations", sources=[rel(census_path)])

    graph_path = RAW / "validated-association-graph-v2.json"
    stats_path = RAW / "graph-statistics-v2.json"
    graph = read_json(graph_path)
    recorded_stats = read_json(stats_path)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = sorted(row["vocabulary_id"] for row in nodes)
    degree: Counter[str] = Counter({node: 0 for node in node_ids})
    for edge in edges:
        degree[edge["vocabulary_id_a"]] += 1
        degree[edge["vocabulary_id_b"]] += 1
    components = graph_components(node_ids, edges)
    cuts, bridges = articulation_and_bridges(node_ids, edges)
    degree_values = sorted(degree.values())
    recomputed = {
        "graph_node_count": len(node_ids), "graph_edge_count": len(edges),
        "graph_density": 2 * len(edges) / (len(node_ids) * (len(node_ids) - 1)),
        "degree_min": min(degree_values), "degree_max": max(degree_values),
        "degree_mean": statistics.fmean(degree_values), "degree_median": statistics.median(degree_values),
        "degree_distribution": dict(sorted(Counter(map(str, degree_values)).items(), key=lambda item: int(item[0]))),
        "connected_component_count": len(components),
        "connected_component_size_distribution": dict(sorted(Counter(str(len(part)) for part in components).items(), key=lambda item: int(item[0]))),
        "components": components, "isolated_active_node_count": sum(value == 0 for value in degree_values),
        "within_category_edge_count": sum(bool(edge.get("shared_category_ids")) for edge in edges),
        "cross_category_edge_count": sum(not edge.get("shared_category_ids") for edge in edges),
        "externally_supported_edge_count": statuses["ACTIVE_EXTERNALLY_SUPPORTED"],
        "source_supported_edge_count": statuses["ACTIVE_SOURCE_SUPPORTED"],
        "strength_distribution": dict(sorted(Counter(edge.get("strength") for edge in edges).items())),
        "confidence_distribution": dict(sorted(Counter(edge.get("confidence") for edge in edges).items())),
        "articulation_point_ids": cuts, "bridge_association_ids": bridges,
    }
    audit.equal("GRAPH.NODE_COUNT", len(nodes), EXPECTED_ACTIVE_VOCABULARY, domain="graph", sources=[rel(graph_path)])
    audit.equal("GRAPH.NODE_COVERAGE", set(node_ids), set(vocabulary["active_by_id"]),
                domain="graph", sources=[rel(graph_path), rel(RAW / "active-vocabulary-v2.json")])
    audit.equal("GRAPH.EDGE_COUNT", len(edges), EXPECTED_ACTIVE_ASSOCIATIONS, domain="graph", sources=[rel(graph_path)])
    audit.equal("GRAPH.EDGE_COVERAGE", {row["association_id"] for row in edges}, {row["pair_id"] for row in active_rows},
                domain="graph", sources=[rel(graph_path), rel(census_path)])
    graph_row_errors: list[str] = []
    for node in nodes:
        vocabulary_row = vocabulary["active_by_id"].get(node.get("vocabulary_id"), {})
        node_id = str(node.get("vocabulary_id"))
        if (node.get("canonical_label") != vocabulary_row.get("canonical_label")
                or node.get("category_ids") != vocabulary_row.get("category_ids")
                or node.get("degree") != degree[node_id]
                or node.get("isolated") != (degree[node_id] == 0)):
            graph_row_errors.append(f"{node_id}:node")
    for edge in edges:
        association_id = str(edge.get("association_id"))
        census_row = census_by_pair.get(association_id, {})
        left = vocabulary["active_by_id"].get(edge.get("vocabulary_id_a"), {})
        right = vocabulary["active_by_id"].get(edge.get("vocabulary_id_b"), {})
        shared = sorted(set(left.get("category_ids", [])) & set(right.get("category_ids", [])))
        if (edge.get("support_status") != census_row.get("final_status")
                or edge.get("strength") != census_row.get("association_strength")
                or edge.get("confidence") != census_row.get("evidence_confidence")
                or edge.get("shared_category_ids") != shared):
            graph_row_errors.append(f"{association_id}:edge")
    audit.equal("GRAPH.NODE_EDGE_PROJECTIONS", graph_row_errors, [], domain="graph",
                sources=[rel(graph_path), rel(census_path), rel(RAW / "active-vocabulary-v2.json")])
    graph_material = {key: graph[key] for key in ("schema_version", "source_sha", "database_snapshot",
                                                   "method_version", "frozen", "nodes", "edges")}
    audit.equal("GRAPH.CANONICAL_HASH", canonical_hash(graph_material), graph.get("graph_hash"),
                domain="graph", sources=[rel(graph_path)])
    for key, value in recomputed.items():
        audit.equal(f"GRAPH.STAT.{key}", recorded_stats.get(key), value,
                    domain="graph", sources=[rel(stats_path), rel(graph_path)])
    audit.metrics.update({"PAIR_UNIVERSE_COUNT": len(expected),
                          "PAIR_CANDIDATE_COUNT": len(expected),
                          "ALL_UNORDERED_PAIRS_ENUMERATED": observed_json == expected and observed_tsv == expected,
                          "ASSOCIATION_STATUS_COUNTS": dict(sorted(statuses.items())),
                          "ACTIVE_ASSOCIATION_COUNT": len(edges), "GRAPH_NODE_COUNT": len(nodes),
                          "GRAPH_EDGE_COUNT": len(edges), "GRAPH_DENSITY": recomputed["graph_density"],
                          "GRAPH_COMPONENT_COUNT": len(components),
                          "GRAPH_ISOLATED_NODE_COUNT": recomputed["isolated_active_node_count"],
                          "VALIDATED_ASSOCIATION_GRAPH_FROZEN": graph.get("frozen") is True})
    return {"pair_document": pair_doc, "pairs": expected, "census": census_doc,
            "census_by_pair": census_by_pair, "graph": graph, "edges": edges,
            "edge_by_id": {edge["association_id"]: edge for edge in edges}}


def connected(node_ids: Iterable[str], edge_pairs: Iterable[tuple[str, str]]) -> bool:
    nodes = set(node_ids)
    if not nodes:
        return False
    adjacency = {node: set() for node in nodes}
    for left, right in edge_pairs:
        if left in adjacency and right in adjacency:
            adjacency[left].add(right)
            adjacency[right].add(left)
    seen = {min(nodes)}
    queue = list(seen)
    while queue:
        node = queue.pop()
        for neighbour in adjacency[node] - seen:
            seen.add(neighbour)
            queue.append(neighbour)
    return seen == nodes


def enumerate_connected_edge_subgraphs(edges: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Directly inspect every non-empty bit mask in the frozen 21-edge set."""
    ordered = sorted(edges, key=lambda row: row["association_id"])
    if len(ordered) != EXPECTED_ACTIVE_ASSOCIATIONS:
        raise ValueError(f"direct enumeration requires 21 edges, got {len(ordered)}")
    valid: list[dict[str, Any]] = []
    over_bound = 0
    for mask in range(1, 1 << len(ordered)):
        chosen: list[Mapping[str, Any]] = []
        nodes: set[str] = set()
        probe = mask
        index = 0
        while probe:
            if probe & 1:
                edge = ordered[index]
                chosen.append(edge)
                nodes.add(str(edge["vocabulary_id_a"]))
                nodes.add(str(edge["vocabulary_id_b"]))
            index += 1
            probe >>= 1
        pairs = [(str(row["vocabulary_id_a"]), str(row["vocabulary_id_b"])) for row in chosen]
        if not connected(nodes, pairs):
            continue
        # The bounded candidate universe is defined over connected subgraphs.
        # A global edge mask spanning several disconnected components is a
        # disconnected rejection, not a node-bound rejection. Count the bound
        # only after connectivity has independently been established.
        if len(nodes) > 8:
            over_bound += 1
            continue
        node_ids = sorted(nodes)
        association_ids = sorted(str(row["association_id"]) for row in chosen)
        identity = {"node_ids": node_ids, "association_ids": association_ids}
        subgraph_hash = canonical_hash(identity)
        induced_count = sum(
            str(edge["vocabulary_id_a"]) in nodes and str(edge["vocabulary_id_b"]) in nodes
            for edge in ordered
        )
        valid.append({
            "association_subgraph_id": f"R16A-SUBGRAPH-{subgraph_hash[:20].upper()}",
            "association_subgraph_hash": subgraph_hash,
            "node_ids": node_ids,
            "association_ids": association_ids,
            "round14_assessment_ids": sorted(str(row["round14_assessment_id"]) for row in chosen),
            "node_count": len(node_ids),
            "edge_count": len(association_ids),
            "maximal_induced_for_node_set": len(chosen) == induced_count,
        })
    valid.sort(key=lambda row: row["association_subgraph_hash"])
    unique_node_sets = {tuple(row["node_ids"]) for row in valid}
    raw_edge_subgraphs = 0
    for nodes_tuple in unique_node_sets:
        node_set = set(nodes_tuple)
        induced = sum(str(edge["vocabulary_id_a"]) in node_set and str(edge["vocabulary_id_b"]) in node_set
                      for edge in ordered)
        raw_edge_subgraphs += (1 << induced) - 1
    metrics = {
        "raw_node_subset_count": sum(math.comb(EXPECTED_ACTIVE_VOCABULARY, size) for size in range(2, 9)),
        "connected_node_subset_count": len(unique_node_sets),
        "raw_edge_subgraph_count": raw_edge_subgraphs,
        "canonical_association_subgraph_count": len(valid),
        "disconnected_rejection_count": raw_edge_subgraphs - len(valid),
        "node_bound_rejection_count": over_bound,
        "duplicate_canonicalisation_count": len(valid) - len({row["association_subgraph_hash"] for row in valid}),
    }
    return valid, metrics


def topology_decisions(subgraph: Mapping[str, Any], edge_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, tuple[bool, str]]:
    nodes = list(subgraph["node_ids"])
    pairs = [(str(edge_by_id[association_id]["vocabulary_id_a"]),
              str(edge_by_id[association_id]["vocabulary_id_b"]))
             for association_id in subgraph["association_ids"]]
    degree = Counter({node: 0 for node in nodes})
    for left, right in pairs:
        degree[left] += 1
        degree[right] += 1
    is_tree = connected(nodes, pairs) and len(pairs) == len(nodes) - 1
    linear = is_tree and max(degree.values(), default=0) <= 2
    binary = len(nodes) == 3 and len(pairs) == 2 and sorted(degree.values()) == [1, 1, 2]
    return {
        "LINEAR_PATH": (linear, "CONNECTED_TREE_MAX_DEGREE_TWO" if linear else "NOT_A_CONNECTED_LINEAR_TREE"),
        "BINARY_FORK": (binary, "EXACT_THREE_NODE_TWO_EDGE_BINARY_SHAPE" if binary else "BINARY_REQUIRES_EXACTLY_THREE_NODES_TWO_EDGES"),
        "BINARY_CONVERGENCE": (binary, "EXACT_THREE_NODE_TWO_EDGE_BINARY_SHAPE" if binary else "BINARY_REQUIRES_EXACTLY_THREE_NODES_TWO_EDGES"),
        "QUALIFIED_PATH": (False, "NO_EXPLICIT_GOVERNED_QUALIFICATION_GATE"),
        "REFLEXIVE_RETURN": (False, "NO_EXPLICIT_GOVERNED_NAVIGATION_RETURN"),
        "EVIDENCE_GAP_TREE": (False, "NO_EXPLICIT_GOVERNED_EVIDENCE_GAP_NODE"),
    }


def topology_hash(subgraph_hash: str, family: str) -> str:
    return canonical_hash({"association_subgraph_hash": subgraph_hash, "topology_family": family,
                           "qualification_gate": False, "navigation_return": False,
                           "evidence_gap_node_ids": [], "adapter_version": ADAPTER_VERSION})


def verify_composition_space(audit: Audit, vocabulary: dict[str, Any], association: dict[str, Any]) -> dict[str, Any]:
    enumeration_path = RAW / "composition-enumeration-v2.tsv"
    registry_path = RAW / "canonical-composition-registry-v2.json"
    stats_path = RAW / "composition-statistics-v2.json"
    enumeration = read_tsv(enumeration_path)
    registry = read_json(registry_path)
    recorded_stats = read_json(stats_path)
    subgraphs, enum_metrics = enumerate_connected_edge_subgraphs(association["edges"])
    edge_by_id = association["edge_by_id"]
    audit.equal("COMPOSITION.DIRECT_SUBGRAPH_COUNT", len(subgraphs), EXPECTED_SUBGRAPHS,
                domain="composition", sources=[rel(RAW / "validated-association-graph-v2.json")])
    audit.equal("COMPOSITION.SUBGRAPH_HASH_UNIQUENESS", len({row["association_subgraph_hash"] for row in subgraphs}),
                len(subgraphs), domain="composition", sources=[rel(registry_path)])
    for key, value in enum_metrics.items():
        audit.equal(f"COMPOSITION.STAT.{key}", recorded_stats.get(key), value,
                    domain="composition", sources=[rel(stats_path), rel(registry_path)])

    registry_subgraphs = registry.get("association_subgraphs", [])
    audit.equal("COMPOSITION.REGISTRY_SUBGRAPH_COUNT", len(registry_subgraphs), len(subgraphs),
                domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.REGISTRY_SUBGRAPH_HASH_COVERAGE",
                {row.get("association_subgraph_hash") for row in registry_subgraphs},
                {row["association_subgraph_hash"] for row in subgraphs},
                domain="composition", sources=[rel(registry_path)])
    projected_registry_subgraphs = [{key: row.get(key) for key in subgraph} for row in registry_subgraphs
                                    for subgraph in subgraphs if row.get("association_subgraph_hash") == subgraph["association_subgraph_hash"]]
    audit.equal("COMPOSITION.REGISTRY_SUBGRAPHS", projected_registry_subgraphs, subgraphs,
                domain="composition", sources=[rel(registry_path)])

    enum_by_key = {(row.get("association_subgraph_id"), row.get("topology_family")): row for row in enumeration}
    audit.equal("COMPOSITION.TOPOLOGY_CANDIDATE_COUNT", len(enumeration), EXPECTED_TOPOLOGY_EVALUATIONS,
                domain="composition", sources=[rel(enumeration_path)])
    audit.equal("COMPOSITION.TOPOLOGY_KEY_UNIQUENESS", len(enum_by_key), len(enumeration),
                domain="composition", sources=[rel(enumeration_path)])
    expected_topologies: list[dict[str, Any]] = []
    topology_errors: list[str] = []
    for subgraph in subgraphs:
        decisions = topology_decisions(subgraph, edge_by_id)
        for family in TOPOLOGIES:
            valid, reason = decisions[family]
            expected_hash = topology_hash(subgraph["association_subgraph_hash"], family) if valid else ""
            row = enum_by_key.get((subgraph["association_subgraph_id"], family))
            if row is None:
                topology_errors.append(f"{subgraph['association_subgraph_id']}:{family}:missing")
                continue
            try:
                row_nodes = json_cell(row.get("node_ids", "[]"))
                row_edges = json_cell(row.get("association_ids", "[]"))
                row_valid = row.get("decision") == "VALID"
                ok = (row.get("association_subgraph_hash") == subgraph["association_subgraph_hash"]
                      and row_nodes == subgraph["node_ids"] and row_edges == subgraph["association_ids"]
                      and as_int(row.get("node_count")) == subgraph["node_count"]
                      and as_int(row.get("edge_count")) == subgraph["edge_count"]
                      and row_valid == valid and row.get("reason_code") == reason
                      and row.get("topology_composition_hash", "") == expected_hash
                      and not as_bool(row.get("adapter_unresolved")))
            except (ValueError, TypeError, KeyError):
                ok = False
            if not ok:
                topology_errors.append(f"{subgraph['association_subgraph_id']}:{family}:mismatch")
            if valid:
                categories = sorted(set.intersection(*(
                    set(vocabulary["active_by_id"][node]["category_ids"]) for node in subgraph["node_ids"]
                )), key=EXPECTED_CATEGORIES.index)
                expected_topologies.append({
                    "composition_id": f"R16A-TOPO-{expected_hash[:20].upper()}",
                    "association_subgraph_id": subgraph["association_subgraph_id"],
                    "association_subgraph_hash": subgraph["association_subgraph_hash"],
                    "topology_composition_hash": expected_hash,
                    "topology_family": family,
                    "node_ids": subgraph["node_ids"], "association_ids": subgraph["association_ids"],
                    "category_ids": categories, "node_count": subgraph["node_count"],
                    "edge_count": subgraph["edge_count"],
                })
    expected_topologies.sort(key=lambda row: row["topology_composition_hash"])
    audit.equal("COMPOSITION.STRICT_TOPOLOGY_ROWS", topology_errors, [],
                domain="composition", sources=[rel(enumeration_path), rel(registry_path)])
    audit.equal("COMPOSITION.VALID_TOPOLOGY_COUNT", len(expected_topologies), EXPECTED_TOPOLOGY_COMPOSITIONS,
                domain="composition", sources=[rel(enumeration_path)])
    audit.equal("COMPOSITION.VALID_INVALID_EQUATION", len(expected_topologies) + (len(enumeration) - len(expected_topologies)),
                EXPECTED_SUBGRAPHS * len(TOPOLOGIES), domain="composition", sources=[rel(enumeration_path)])
    valid_distribution = dict(sorted(Counter(row["topology_family"] for row in expected_topologies).items()))
    audit.equal("COMPOSITION.TOPOLOGY_DISTRIBUTION", recorded_stats.get("topology_distribution"), valid_distribution,
                domain="composition", sources=[rel(stats_path)])
    candidate_distribution = dict(sorted(Counter(row.get("topology_family") for row in enumeration).items()))
    invalid_distribution = dict(sorted(Counter(row.get("topology_family") for row in enumeration
                                               if row.get("decision") == "INVALID").items()))
    size_distribution = dict(sorted(Counter(str(row["node_count"]) for row in expected_topologies).items(),
                                    key=lambda item: int(item[0])))
    edge_distribution = dict(sorted(Counter(str(row["edge_count"]) for row in expected_topologies).items(),
                                    key=lambda item: int(item[0])))
    for case_id, field, expected_value in (
        ("COMPOSITION.CANDIDATE_DISTRIBUTION", "topology_candidate_distribution", candidate_distribution),
        ("COMPOSITION.INVALID_DISTRIBUTION", "topology_invalid_distribution", invalid_distribution),
        ("COMPOSITION.SIZE_DISTRIBUTION", "composition_size_distribution", size_distribution),
        ("COMPOSITION.EDGE_DISTRIBUTION", "edge_count_distribution", edge_distribution),
        ("COMPOSITION.INVALID_COUNT", "invalid_composition_count", len(enumeration) - len(expected_topologies)),
    ):
        audit.equal(case_id, recorded_stats.get(field), expected_value,
                    domain="composition", sources=[rel(stats_path), rel(enumeration_path)])

    registry_topologies = registry.get("topology_compositions", [])
    audit.equal("COMPOSITION.REGISTRY_TOPOLOGY_COUNT", len(registry_topologies), len(expected_topologies),
                domain="composition", sources=[rel(registry_path)])
    registry_by_hash = {row.get("topology_composition_hash"): row for row in registry_topologies}
    registry_projection = [{key: registry_by_hash.get(row["topology_composition_hash"], {}).get(key)
                            for key in row} for row in expected_topologies]
    audit.equal("COMPOSITION.REGISTRY_TOPOLOGIES", registry_projection, expected_topologies,
                domain="composition", sources=[rel(registry_path)])

    expected_entries: list[dict[str, Any]] = []
    expected_production: dict[str, dict[str, Any]] = {}
    expected_seed_rows: list[dict[str, Any]] = []
    for topology in expected_topologies:
        seeds: list[dict[str, Any]] = []
        for node_id in topology["node_ids"]:
            seed_hash = canonical_hash({"topology_composition_hash": topology["topology_composition_hash"],
                                        "seed_node_id": node_id})
            seed = {"seed_id": f"R16A-SEED-{seed_hash[:20].upper()}", "seed_node_id": node_id,
                    "seed_variant_hash": seed_hash}
            seeds.append(seed)
            expected_seed_rows.append({"composition_id": topology["composition_id"], **seed})
        registry_row = registry_by_hash.get(topology["topology_composition_hash"], {})
        audit.equal(f"COMPOSITION.SEEDS.{topology['composition_id']}", registry_row.get("seed_variants"), seeds,
                    domain="composition", sources=[rel(registry_path)])
        for category_id in topology["category_ids"]:
            entry_hash = canonical_hash({"topology_composition_hash": topology["topology_composition_hash"],
                                         "category_id": category_id})
            entry_id = f"R16A-ENTRY-{entry_hash[:20].upper()}"
            production_ids: list[str] = []
            for seed in seeds:
                production_hash = canonical_hash({"category_entry_hash": entry_hash,
                                                  "seed_variant_hash": seed["seed_variant_hash"]})
                production_id = f"R16A-PCOMP-{production_hash[:20].upper()}"
                production_ids.append(production_id)
                expected_production[production_id] = {
                    "composition_id": production_id, "category_entry_id": entry_id,
                    "seed_id": seed["seed_id"], "seed_node_id": seed["seed_node_id"],
                    "node_ids": topology["node_ids"], "association_ids": topology["association_ids"],
                    "topology_family": topology["topology_family"],
                    "semantic_hash": topology["topology_composition_hash"],
                }
            expected_entries.append({
                "category_entry_id": entry_id, "category_entry_hash": entry_hash,
                "category_id": category_id, "composition_id": topology["composition_id"],
                "topology_composition_hash": topology["topology_composition_hash"],
                "node_ids": topology["node_ids"], "association_ids": topology["association_ids"],
                "seed_variant_ids": [seed["seed_id"] for seed in seeds],
                "production_composition_ids": production_ids,
            })
    expected_entries.sort(key=lambda row: (EXPECTED_CATEGORIES.index(row["category_id"]), row["category_entry_id"]))
    category_distribution = dict(sorted(Counter(row["category_id"] for row in expected_entries).items()))
    audit.equal("COMPOSITION.CATEGORY_ENTRY_DISTRIBUTION", recorded_stats.get("category_entry_distribution"),
                category_distribution, domain="composition", sources=[rel(stats_path)])
    audit.equal("COMPOSITION.MULTI_CATEGORY_COUNT", recorded_stats.get("multi_category_composition_count"),
                sum(len(row["category_ids"]) > 1 for row in expected_topologies),
                domain="composition", sources=[rel(stats_path)])
    category_tsv = read_tsv(RAW / "category-entry-census-v2.tsv")
    category_tsv_by_id = {row.get("category_entry_id"): row for row in category_tsv}
    category_registry_by_id = {row.get("category_entry_id"): row for row in registry.get("category_entries", [])}
    audit.equal("COMPOSITION.CATEGORY_ENTRY_TSV_COVERAGE", set(category_tsv_by_id),
                {row["category_entry_id"] for row in expected_entries}, domain="composition",
                sources=[rel(RAW / "category-entry-census-v2.tsv")])
    audit.equal("COMPOSITION.CATEGORY_ENTRY_REGISTRY_COVERAGE", set(category_registry_by_id),
                {row["category_entry_id"] for row in expected_entries}, domain="composition",
                sources=[rel(registry_path)])
    entry_errors: list[str] = []
    for expected_entry in expected_entries:
        for origin, row in (("tsv", category_tsv_by_id.get(expected_entry["category_entry_id"])),
                            ("registry", category_registry_by_id.get(expected_entry["category_entry_id"]))):
            if row is None:
                entry_errors.append(f"{expected_entry['category_entry_id']}:{origin}:missing")
                continue
            for key, expected_value in expected_entry.items():
                actual: Any = row.get(key)
                if key in {"node_ids", "association_ids", "seed_variant_ids", "production_composition_ids"}:
                    actual = json_cell(actual) if isinstance(actual, str) else actual
                if actual != expected_value:
                    entry_errors.append(f"{expected_entry['category_entry_id']}:{origin}:{key}")
    audit.equal("COMPOSITION.CATEGORY_ENTRY_IDENTITIES", entry_errors, [],
                domain="composition", sources=[rel(registry_path), rel(RAW / "category-entry-census-v2.tsv")])
    audit.equal("COMPOSITION.SEED_COUNT", len(expected_seed_rows), EXPECTED_SEEDS,
                domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.SEED_SUM_EQUATION", sum(row["node_count"] for row in expected_topologies),
                len(expected_seed_rows), domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.CATEGORY_ENTRY_SUM_EQUATION", sum(len(row["category_ids"]) for row in expected_topologies),
                len(expected_entries), domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.PRODUCTION_SUM_EQUATION",
                sum(len(row["seed_variant_ids"]) for row in expected_entries), len(expected_production),
                domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.PRODUCTION_COMPOSITION_HEADLINE", len(expected_production),
                EXPECTED_PRODUCTION_COMPOSITIONS, domain="composition", sources=[rel(registry_path)])
    registry_material_keys = ("schema_version", "source_sha", "database_snapshot", "round15_adapter_version", "frozen",
                              "association_subgraphs", "topology_compositions", "category_entries",
                              "round15_adapter_records", "round16_legacy_reconciliation")
    audit.equal("COMPOSITION.REGISTRY_HASH", canonical_hash({key: registry[key] for key in registry_material_keys}),
                registry.get("registry_hash"), domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.UNRESOLVED_COUNT", recorded_stats.get("unresolved_composition_count"), 0,
                domain="composition", sources=[rel(stats_path)])
    rejection_path = RAW / "composition-rejection-ledger-v2.tsv"
    rejection_rows = read_tsv(rejection_path)
    topology_rejections = {(row.get("association_subgraph_id"), row.get("topology_family")): row
                           for row in rejection_rows if row.get("topology_family") in TOPOLOGIES}
    rejection_errors: list[str] = []
    for row in enumeration:
        key = (row.get("association_subgraph_id"), row.get("topology_family"))
        rejection = topology_rejections.get(key)
        if row.get("decision") == "INVALID":
            if (not rejection or rejection.get("decision") != "INVALID"
                    or rejection.get("reason_code") != row.get("reason_code")
                    or rejection.get("round15_adapter_version") != ADAPTER_VERSION):
                rejection_errors.append(f"{key[0]}:{key[1]}:missing_or_mismatch")
        elif rejection is not None:
            rejection_errors.append(f"{key[0]}:{key[1]}:valid_has_rejection")
    audit.equal("COMPOSITION.REJECTION_LEDGER_RECONCILIATION", rejection_errors, [],
                domain="composition", sources=[rel(rejection_path), rel(enumeration_path)])
    adapter_records = registry.get("round15_adapter_records", [])
    audit.equal("COMPOSITION.ADAPTER_RECORD_COUNT", len(adapter_records), len(subgraphs),
                domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.ADAPTER_FINAL_UNRESOLVED",
                sum(as_int(row.get("adapter_final_unresolved_count", -1)) for row in adapter_records), 0,
                domain="composition", sources=[rel(registry_path)])
    legacy_rows = registry.get("round16_legacy_reconciliation", [])
    legacy_errors = [row.get("legacy_composition_id") for row in legacy_rows
                     if row.get("disposition") not in {"PRESERVED_CANONICAL", "REJECTED_WITH_REASON"}
                     or not row.get("reason")
                     or row.get("context_or_spacetime_dependency_removed") is not True]
    audit.equal("COMPOSITION.LEGACY_RECONCILIATION_COUNT", len(legacy_rows), 11,
                domain="composition", sources=[rel(registry_path)])
    audit.equal("COMPOSITION.LEGACY_RECONCILIATION_GATES", legacy_errors, [],
                domain="composition", sources=[rel(registry_path)])
    audit.metrics.update({"CANONICAL_ASSOCIATION_SUBGRAPH_COUNT": len(subgraphs),
                          "TOPOLOGY_CANDIDATE_COUNT": len(enumeration),
                          "VALID_TOPOLOGY_COMPOSITION_COUNT": len(expected_topologies),
                          "INVALID_TOPOLOGY_CANDIDATE_COUNT": len(enumeration) - len(expected_topologies),
                          "TOPOLOGY_DISTRIBUTION": valid_distribution,
                          "SEED_VARIANT_COUNT": len(expected_seed_rows),
                          "CATEGORY_ENTRY_COUNT": len(expected_entries),
                          "PRODUCTION_COMPOSITION_COUNT": len(expected_production),
                          "ALL_LEGAL_SUBGRAPHS_ENUMERATED": len(subgraphs) == EXPECTED_SUBGRAPHS,
                          "ALL_LEGAL_TOPOLOGIES_EVALUATED": len(enumeration) == EXPECTED_TOPOLOGY_EVALUATIONS,
                          "CANONICAL_COMPOSITION_COUNT_INDEPENDENTLY_VERIFIED": len(expected_topologies) == EXPECTED_TOPOLOGY_COMPOSITIONS,
                          "ROUND16_LEGACY_COMPOSITION_RECONCILED_COUNT": len(legacy_rows) - len(legacy_errors)})
    return {"registry": registry, "subgraphs": subgraphs, "topologies": expected_topologies,
            "category_entries": expected_entries, "category_registry_by_id": category_registry_by_id,
            "category_tsv_by_id": category_tsv_by_id,
            "production_compositions": expected_production}


def normalize_state(row: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for key in ("expanded_node_ids", "visible_node_ids", "visible_association_ids", "available_actions"):
        output[key] = json_cell(output[key]) if isinstance(output.get(key), str) else output.get(key)
    return output


def composition_adjacency(composition: Mapping[str, Any], edge_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, set[str]]:
    adjacency = {node: set() for node in composition["node_ids"]}
    for association_id in composition["association_ids"]:
        edge = edge_by_id[association_id]
        left, right = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
        adjacency[left].add(right)
        adjacency[right].add(left)
    return adjacency


def visible_projection(composition: Mapping[str, Any], focused: str, expanded: set[str],
                       edge_by_id: Mapping[str, Mapping[str, Any]], adjacency: Mapping[str, set[str]]) -> tuple[list[str], list[str]]:
    visible = {focused} | set(adjacency[focused]) | expanded
    for node in expanded:
        visible |= set(adjacency[node])
    visible_nodes = sorted(visible)
    visible_associations = sorted(
        association_id for association_id in composition["association_ids"]
        if {edge_by_id[association_id]["vocabulary_id_a"], edge_by_id[association_id]["vocabulary_id_b"]} <= visible
    )
    return visible_nodes, visible_associations


def verify_model_and_states(audit: Audit, composition_space: dict[str, Any],
                            association: dict[str, Any], vocabulary: dict[str, Any]) -> dict[str, Any]:
    model = read_json(MODEL)
    state_path = RAW / "state-census-v2.tsv"
    state_tsv = [normalize_state(row) for row in read_tsv(state_path)]
    state_by_id = {row.get("state_id"): row for row in state_tsv}
    model_states = model.get("states", {})
    model_compositions = model.get("compositions", {})
    expected_production = composition_space["production_compositions"]
    edge_by_id = association["edge_by_id"]
    audit.equal("MODEL.TOP_LEVEL_ALLOWLIST", set(model),
                {"associations", "capabilities", "categories", "compositions", "database", "states",
                 "states_by_hash", "transitions", "vocabulary"},
                domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.DATABASE_SNAPSHOT", model.get("database", {}).get("database_snapshot_id"),
                EXPECTED_DATABASE_SNAPSHOT, domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.VOCABULARY_COUNT", len(model.get("vocabulary", [])), EXPECTED_ACTIVE_VOCABULARY,
                domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.VOCABULARY_COVERAGE", {row.get("vocabulary_id") for row in model.get("vocabulary", [])},
                set(vocabulary["active_by_id"]), domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.ASSOCIATION_COUNT", len(model.get("associations", [])), EXPECTED_ACTIVE_ASSOCIATIONS,
                domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.ASSOCIATION_COVERAGE", {row.get("association_id") for row in model.get("associations", [])},
                set(edge_by_id), domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.PRODUCTION_COMPOSITION_COVERAGE", set(model_compositions), set(expected_production),
                domain="model", sources=[rel(MODEL), rel(RAW / "canonical-composition-registry-v2.json")])
    composition_errors: list[str] = []
    for production_id, expected in expected_production.items():
        observed = model_compositions.get(production_id, {})
        for key, expected_value in expected.items():
            if observed.get(key) != expected_value:
                composition_errors.append(f"{production_id}:{key}")
    audit.equal("MODEL.PRODUCTION_COMPOSITION_IDENTITIES", composition_errors, [],
                domain="model", sources=[rel(MODEL)])

    expected_entries = composition_space["category_entries"]
    expected_entry_ids = {row["category_entry_id"] for row in expected_entries}
    model_categories = model.get("categories", [])
    category_model_by_entry = {row.get("category_entry_id"): row for row in model_categories}
    audit.equal("MODEL.CATEGORY_ENTRY_COVERAGE", set(category_model_by_entry), expected_entry_ids,
                domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.CATEGORY_TYPES", {row.get("category_id") for row in model_categories}, set(EXPECTED_CATEGORIES),
                domain="model", sources=[rel(MODEL)])
    category_for_entry = {row["category_entry_id"]: row["category_id"] for row in expected_entries}
    prod_by_category: dict[str, list[str]] = defaultdict(list)
    prod_by_entry: dict[str, list[str]] = defaultdict(list)
    for production_id, record in expected_production.items():
        prod_by_entry[record["category_entry_id"]].append(production_id)
        prod_by_category[category_for_entry[record["category_entry_id"]]].append(production_id)
    for values in itertools.chain(prod_by_entry.values(), prod_by_category.values()):
        values.sort()

    state_key_map: dict[tuple[str, str, str, tuple[str, ...]], dict[str, Any]] = {}
    state_errors: list[str] = []
    adjacency_by_production: dict[str, dict[str, set[str]]] = {}
    expected_state_total = 0
    for production_id, production in sorted(expected_production.items()):
        nodes = list(production["node_ids"])
        expected_state_total += len(nodes) * (1 << len(nodes))
        adjacency = composition_adjacency(production, edge_by_id)
        adjacency_by_production[production_id] = adjacency
    audit.equal("STATE.COUNT_FORMULA", len(state_tsv), expected_state_total,
                domain="state", sources=[rel(state_path), rel(RAW / "canonical-composition-registry-v2.json")])
    audit.equal("STATE.HEADLINE_COUNT", len(state_tsv), EXPECTED_STATES,
                domain="state", sources=[rel(state_path)])
    audit.equal("STATE.ID_UNIQUENESS", len(state_by_id), len(state_tsv), domain="state", sources=[rel(state_path)])
    audit.equal("STATE.MODEL_ID_COVERAGE", set(model_states), set(state_by_id),
                domain="state", sources=[rel(MODEL), rel(state_path)])

    for row in state_tsv:
        state_id = str(row.get("state_id"))
        production_id = str(row.get("composition_id"))
        production = expected_production.get(production_id)
        if production is None:
            state_errors.append(f"{state_id}:unknown_composition")
            continue
        nodes = list(production["node_ids"])
        node_set = set(nodes)
        focused = str(row.get("focused_node_id"))
        expanded = set(row.get("expanded_node_ids") or [])
        if focused not in node_set or not expanded <= node_set:
            state_errors.append(f"{state_id}:focus_or_expansion_domain")
            continue
        adjacency = adjacency_by_production[production_id]
        visible_nodes, visible_associations = visible_projection(production, focused, expanded, edge_by_id, adjacency)
        local_targets = {
            "FOCUS_NODE": nodes,
            "MOVE_FOCUS": sorted(adjacency[focused]),
            "EXPAND_NODE": sorted(set(visible_nodes) - expanded),
            "COLLAPSE_NODE": sorted(expanded),
        }
        available = [action for action in ACTIONS if action not in local_targets or bool(local_targets[action])]
        presentation_identity = {
            "category_entry_id": production["category_entry_id"], "production_composition_id": production_id,
            "seed_id": production["seed_id"], "focused_node_id": focused,
            "expanded_node_ids": sorted(expanded), "visible_node_ids": visible_nodes,
            "visible_association_ids": visible_associations, "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
        }
        presentation_hash = canonical_hash(presentation_identity)
        state_identity = {**presentation_identity, "semantic_hash": production["semantic_hash"],
                          "presentation_hash": presentation_hash}
        state_hash = canonical_hash(state_identity)
        expected_fields = {
            "state_id": f"R16A-STATE-{state_hash[:24].upper()}", "state_hash": state_hash,
            "category_entry_id": production["category_entry_id"], "composition_id": production_id,
            "seed_id": production["seed_id"], "focused_node_id": focused,
            "expanded_node_ids": sorted(expanded), "visible_node_ids": visible_nodes,
            "visible_association_ids": visible_associations, "available_actions": available,
            "semantic_hash": production["semantic_hash"], "presentation_hash": presentation_hash,
            "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
        }
        for key, expected_value in expected_fields.items():
            if row.get(key) != expected_value:
                state_errors.append(f"{state_id}:{key}")
        model_row = model_states.get(state_id)
        if model_row != expected_fields:
            state_errors.append(f"{state_id}:model_projection")
        visible_pairs = [(edge_by_id[association_id]["vocabulary_id_a"],
                          edge_by_id[association_id]["vocabulary_id_b"])
                         for association_id in visible_associations]
        if not connected(visible_nodes, visible_pairs):
            state_errors.append(f"{state_id}:visible_disconnected")
        key = (production_id, production["seed_id"], focused, tuple(sorted(expanded)))
        if key in state_key_map:
            state_errors.append(f"{state_id}:duplicate_state_key")
        state_key_map[key] = row
    audit.equal("STATE.IDENTITY_VISIBILITY_ACTION_GATES", state_errors, [],
                domain="state", sources=[rel(state_path), rel(MODEL)])
    audit.equal("STATE.HASH_UNIQUENESS", len({row.get("state_hash") for row in state_tsv}), len(state_tsv),
                domain="state", sources=[rel(state_path)])
    audit.equal("STATE.STATES_BY_HASH", model.get("states_by_hash"),
                {row["state_hash"]: row["state_id"] for row in state_tsv},
                domain="state", sources=[rel(MODEL), rel(state_path)])

    root_by_production: dict[str, dict[str, Any]] = {}
    for production_id, production in expected_production.items():
        key = (production_id, production["seed_id"], production["seed_node_id"], ())
        if key in state_key_map:
            root_by_production[production_id] = state_key_map[key]
        else:
            state_errors.append(f"{production_id}:root_missing")
    entry_by_id = {row["category_entry_id"]: row for row in expected_entries}
    entry_initial: dict[str, str] = {}
    entry_errors: list[str] = []
    for entry_id, entry in entry_by_id.items():
        canonical_production = min(entry["production_composition_ids"])
        expected_initial = root_by_production[canonical_production]["state_id"]
        entry_initial[entry_id] = expected_initial
        registry_entry = composition_space["category_registry_by_id"].get(entry_id, {})
        tsv_entry = composition_space["category_tsv_by_id"].get(entry_id, {})
        model_entry = category_model_by_entry.get(entry_id, {})
        if registry_entry.get("initial_state_id") != expected_initial:
            entry_errors.append(f"{entry_id}:registry_initial")
        if tsv_entry.get("initial_state_id") != expected_initial:
            entry_errors.append(f"{entry_id}:tsv_initial")
        if model_entry.get("initial_state_id") != expected_initial:
            entry_errors.append(f"{entry_id}:model_initial")
        if model_entry.get("composition_ids") != entry["production_composition_ids"]:
            entry_errors.append(f"{entry_id}:model_compositions")
    audit.equal("STATE.CATEGORY_INITIAL_IDENTITIES", entry_errors, [], domain="state",
                sources=[rel(MODEL), rel(RAW / "category-entry-census-v2.tsv")])

    local_unreachable: dict[str, int] = {}
    local_distances: dict[str, dict[str, int]] = {}
    canonical_steps_by_target: dict[str, list[dict[str, str]]] = {}
    action_rank = {action: index for index, action in enumerate(ACTIONS)}
    for production_id, production in expected_production.items():
        root = root_by_production[production_id]
        adjacency = adjacency_by_production[production_id]
        distances = {root["state_id"]: 0}
        predecessor: dict[str, tuple[str, str, str] | None] = {root["state_id"]: None}
        queue = deque([root])
        while queue:
            current = queue.popleft()
            expanded = set(current["expanded_node_ids"])
            targets: list[tuple[str, str, dict[str, Any]]] = []
            for node in production["node_ids"]:
                targets.append(("FOCUS_NODE", node, state_key_map[(
                    production_id, production["seed_id"], node, tuple(sorted(expanded)))]))
            for node in sorted(adjacency[current["focused_node_id"]]):
                targets.append(("MOVE_FOCUS", node, state_key_map[(
                    production_id, production["seed_id"], node, tuple(sorted(expanded)))]))
            for node in sorted(set(current["visible_node_ids"]) - expanded):
                targets.append(("EXPAND_NODE", node, state_key_map[(
                    production_id, production["seed_id"], current["focused_node_id"],
                    tuple(sorted(expanded | {node})))]))
            for node in sorted(expanded):
                targets.append(("COLLAPSE_NODE", node, state_key_map[(
                    production_id, production["seed_id"], current["focused_node_id"],
                    tuple(sorted(expanded - {node})))]))
            targets.append(("EXPORT_CURRENT_STATE", "", current))
            targets.sort(key=lambda item: (action_rank[item[0]], item[1], item[2]["state_id"]))
            for action, target, nxt in targets:
                if nxt["state_id"] not in distances:
                    distances[nxt["state_id"]] = distances[current["state_id"]] + 1
                    predecessor[nxt["state_id"]] = (current["state_id"], action, target)
                    queue.append(nxt)
        expected_ids = {row["state_id"] for row in state_tsv if row["composition_id"] == production_id}
        missing = expected_ids - set(distances)
        if missing:
            local_unreachable[production_id] = len(missing)
        local_distances[production_id] = distances
        for target_id in expected_ids:
            reverse_steps: list[dict[str, str]] = []
            cursor = target_id
            while predecessor.get(cursor) is not None:
                previous, action, target = predecessor[cursor]  # type: ignore[misc]
                reverse_steps.append({"action": action, "target_id": target})
                cursor = previous
            canonical_steps_by_target[target_id] = list(reversed(reverse_steps))
    audit.equal("STATE.LOCAL_REACHABILITY", local_unreachable, {}, domain="state", sources=[rel(state_path)])
    audit.metrics["STATE_COUNT"] = len(state_tsv)
    audit.metrics["UNREACHABLE_PRODUCTION_STATE_COUNT"] = sum(local_unreachable.values())
    audit.metrics["ALL_REACHABLE_STATES_ENUMERATED"] = not local_unreachable and len(state_tsv) == expected_state_total
    return {"model": model, "states": state_tsv, "state_by_id": state_by_id,
            "state_key_map": state_key_map, "root_by_production": root_by_production,
            "entry_initial": entry_initial, "category_for_entry": category_for_entry,
            "prod_by_category": prod_by_category, "prod_by_entry": prod_by_entry,
            "adjacency_by_production": adjacency_by_production, "local_distances": local_distances,
            "canonical_steps_by_target": canonical_steps_by_target,
            "expected_production": expected_production}


def expected_transitions_for_state(runtime: dict[str, Any], current: Mapping[str, Any]) -> dict[tuple[str, str], str]:
    production_id = str(current["composition_id"])
    production = runtime["expected_production"][production_id]
    expanded = set(current["expanded_node_ids"])
    visible = set(current["visible_node_ids"])
    adjacency = runtime["adjacency_by_production"][production_id]
    state_key = runtime["state_key_map"]
    expected: dict[tuple[str, str], str] = {}
    top_entry_by_category: dict[str, str] = {}
    for category_id in EXPECTED_CATEGORIES:
        top_entry_by_category[category_id] = min(
            entry_id for entry_id, category in runtime["category_for_entry"].items() if category == category_id
        )
    for category_id, entry_id in top_entry_by_category.items():
        expected[("SELECT_CATEGORY", category_id)] = runtime["entry_initial"][entry_id]
    for target in production["node_ids"]:
        expected[("FOCUS_NODE", target)] = state_key[(production_id, production["seed_id"], target,
                                                       tuple(sorted(expanded)))]["state_id"]
    for target in sorted(adjacency[current["focused_node_id"]]):
        expected[("MOVE_FOCUS", target)] = state_key[(production_id, production["seed_id"], target,
                                                       tuple(sorted(expanded)))]["state_id"]
    for target in sorted(visible - expanded):
        expected[("EXPAND_NODE", target)] = state_key[(production_id, production["seed_id"],
                                                        current["focused_node_id"],
                                                        tuple(sorted(expanded | {target})))]["state_id"]
    for target in sorted(expanded):
        expected[("COLLAPSE_NODE", target)] = state_key[(production_id, production["seed_id"],
                                                          current["focused_node_id"],
                                                          tuple(sorted(expanded - {target})))]["state_id"]
    category_id = runtime["category_for_entry"][current["category_entry_id"]]
    for target_production in runtime["prod_by_category"][category_id]:
        expected[("SELECT_COMPOSITION", target_production)] = runtime["root_by_production"][target_production]["state_id"]
    top_entry = top_entry_by_category[category_id]
    expected[("RESET_CATEGORY", "")] = runtime["entry_initial"][top_entry]
    expected[("EXPORT_CURRENT_STATE", "")] = str(current["state_id"])
    return expected


def verify_transitions(audit: Audit, runtime: dict[str, Any]) -> dict[str, Any]:
    path = RAW / "transition-census-v2.tsv"
    rows = read_tsv(path)
    transition_descriptor = runtime["model"].get("transitions", {})
    state_by_id = runtime["state_by_id"]
    observed_by_state: dict[str, dict[tuple[str, str], str]] = defaultdict(dict)
    expected_model_keys: set[str] = set()
    observed_model_keys: set[str] = set()
    derived_model_transitions: dict[str, str] = {}
    transition_errors: list[str] = []
    outgoing: dict[str, set[str]] = defaultdict(set)
    seen_ids: set[str] = set()
    differing_next_state_count = 0
    for row in rows:
        transition_id = str(row.get("transition_id"))
        current_id = str(row.get("current_state_id"))
        next_id = str(row.get("next_state_id"))
        current = state_by_id.get(current_id)
        nxt = state_by_id.get(next_id)
        action = str(row.get("action"))
        target = str(row.get("target_id", ""))
        if transition_id in seen_ids:
            transition_errors.append(f"{transition_id}:duplicate_id")
        seen_ids.add(transition_id)
        if current is None or nxt is None:
            transition_errors.append(f"{transition_id}:unknown_state")
            continue
        if next_id != current_id:
            differing_next_state_count += 1
        key_tuple = (action, target)
        if key_tuple in observed_by_state[current_id]:
            transition_errors.append(f"{transition_id}:duplicate_current_action_target")
        observed_by_state[current_id][key_tuple] = next_id
        model_key = f"{current['state_hash']}|{action}|{target}"
        observed_model_keys.add(model_key)
        expected_id = f"R16A-TRANSITION-{canonical_hash({'key': model_key, 'next': next_id})[:24].upper()}"
        if row.get("current_state_hash") != current["state_hash"]:
            transition_errors.append(f"{transition_id}:current_hash")
        if row.get("next_state_hash") != nxt["state_hash"]:
            transition_errors.append(f"{transition_id}:next_hash")
        if transition_id != expected_id:
            transition_errors.append(f"{transition_id}:identity")
        try:
            flags_ok = (as_bool(row.get("executed")) and as_bool(row.get("passed"))
                        and not as_bool(row.get("state_mutated")))
        except ValueError:
            flags_ok = False
        if not flags_ok:
            transition_errors.append(f"{transition_id}:execution_flags")
        if row.get("database_snapshot") != EXPECTED_DATABASE_SNAPSHOT:
            transition_errors.append(f"{transition_id}:database_snapshot")
        outgoing[current_id].add(next_id)

    expected_count = 0
    for current in runtime["states"]:
        expected = expected_transitions_for_state(runtime, current)
        expected_count += len(expected)
        observed = observed_by_state.get(current["state_id"], {})
        if observed != expected:
            missing = len(set(expected) - set(observed))
            extra = len(set(observed) - set(expected))
            wrong = sum(key in observed and observed[key] != value for key, value in expected.items())
            transition_errors.append(f"{current['state_id']}:relation:missing={missing}:extra={extra}:wrong={wrong}")
        for (action, target), next_id in expected.items():
            model_key = f"{current['state_hash']}|{action}|{target}"
            expected_model_keys.add(model_key)
            derived_model_transitions[model_key] = next_id
    audit.equal("TRANSITION.ENUMERATED_COUNT", len(rows), expected_count,
                domain="transition", sources=[rel(path), rel(MODEL)])
    audit.equal("TRANSITION.HEADLINE_COUNT", len(rows), EXPECTED_TRANSITIONS,
                domain="transition", sources=[rel(path)])
    audit.equal("TRANSITION.EXECUTE_EVERY_ROW", transition_errors, [],
                domain="transition", sources=[rel(path), rel(MODEL)])
    audit.equal("TRANSITION.PRODUCTION_DERIVATION_DESCRIPTOR", transition_descriptor, {
        "derivation_version": "trace-exploration-derived-transitions-v2",
        "key_format": "state_hash|action|target",
        "transition_count": expected_count,
    }, domain="transition", sources=[rel(MODEL), rel(path)])
    audit.equal("TRANSITION.DERIVED_EXACT_KEY_COVERAGE", observed_model_keys, expected_model_keys,
                domain="transition", sources=[rel(MODEL), rel(path)])

    top_entries = [min(entry_id for entry_id, category in runtime["category_for_entry"].items()
                       if category == category_id) for category_id in EXPECTED_CATEGORIES]
    start = runtime["entry_initial"][top_entries[0]]
    reachable = {start}
    queue = deque([start])
    while queue:
        current_id = queue.popleft()
        for next_id in outgoing.get(current_id, set()) - reachable:
            reachable.add(next_id)
            queue.append(next_id)
    audit.equal("TRANSITION.GLOBAL_STATE_REACHABILITY", len(reachable), len(runtime["states"]),
                domain="transition", sources=[rel(path)])
    audit.metrics["TRANSITION_COUNT"] = len(rows)
    audit.metrics["TRANSITION_FAILURE_COUNT"] = len(transition_errors)
    audit.metrics["TRANSITION_FAIL_COUNT"] = len(transition_errors)
    audit.metrics["STATE_MUTATION_COUNT"] = sum(as_bool(row.get("state_mutated")) for row in rows)
    audit.metrics["TRANSITION_DIFFERENT_NEXT_STATE_COUNT"] = differing_next_state_count
    return {"rows": rows, "observed_by_state": observed_by_state,
            "model_transitions": derived_model_transitions,
            "transition_descriptor": transition_descriptor}


def verify_workflows(audit: Audit, runtime: dict[str, Any], transitions: dict[str, Any]) -> dict[str, Any]:
    path = RAW / "workflow-census-v2.tsv"
    rows = read_tsv(path)
    state_by_id = runtime["state_by_id"]
    model_transitions = transitions["model_transitions"]
    errors: list[str] = []
    targets: list[str] = []
    workflow_ids: set[str] = set()
    lengths: list[int] = []
    for row in rows:
        workflow_id = str(row.get("workflow_id"))
        production_id = str(row.get("composition_id"))
        start_id = str(row.get("start_state_id"))
        target_id = str(row.get("target_state_id"))
        targets.append(target_id)
        if workflow_id in workflow_ids:
            errors.append(f"{workflow_id}:duplicate_id")
        workflow_ids.add(workflow_id)
        target = state_by_id.get(target_id)
        root = runtime["root_by_production"].get(production_id)
        try:
            steps = json_cell(row.get("steps", "[]"))
            length = as_int(row.get("workflow_length"))
        except (ValueError, TypeError):
            errors.append(f"{workflow_id}:malformed_steps")
            continue
        lengths.append(length)
        if target is None or root is None:
            errors.append(f"{workflow_id}:unknown_endpoint")
            continue
        if start_id != root["state_id"] or length != len(steps):
            errors.append(f"{workflow_id}:start_or_length")
        if steps != runtime["canonical_steps_by_target"].get(target_id):
            errors.append(f"{workflow_id}:canonical_tie_break")
        expected_hash = canonical_hash({"start_state_id": start_id, "target_state_id": target_id, "steps": steps})
        if workflow_id != f"R16A-WORKFLOW-{expected_hash[:24].upper()}":
            errors.append(f"{workflow_id}:identity")
        for replay_index in range(2):
            current = root
            for step in steps:
                key = f"{current['state_hash']}|{step.get('action')}|{step.get('target_id', '')}"
                next_id = model_transitions.get(key)
                if next_id not in state_by_id:
                    errors.append(f"{workflow_id}:replay{replay_index}:missing_transition")
                    break
                current = state_by_id[next_id]
            if current["state_id"] != target_id:
                errors.append(f"{workflow_id}:replay{replay_index}:state")
            if current["semantic_hash"] != target["semantic_hash"]:
                errors.append(f"{workflow_id}:replay{replay_index}:semantic")
        expected_distance = runtime["local_distances"].get(production_id, {}).get(target_id)
        if expected_distance != length:
            errors.append(f"{workflow_id}:not_shortest")
        try:
            counters_ok = (as_int(row.get("replay_count")) == 2 and as_int(row.get("replay_pass_count")) == 2
                           and as_int(row.get("state_replay_mismatch_count")) == 0
                           and as_int(row.get("semantic_replay_mismatch_count")) == 0)
        except ValueError:
            counters_ok = False
        if not counters_ok:
            errors.append(f"{workflow_id}:receipt_counts")
        for field, expected_value in (("category_entry_id", target["category_entry_id"]),
                                      ("seed_id", target["seed_id"]),
                                      ("target_state_hash", target["state_hash"]),
                                      ("target_semantic_hash", target["semantic_hash"])):
            if row.get(field) != expected_value:
                errors.append(f"{workflow_id}:{field}")
    audit.equal("WORKFLOW.STATE_COUNT_EQUATION", len(rows), len(runtime["states"]),
                domain="workflow", sources=[rel(path), rel(RAW / "state-census-v2.tsv")])
    audit.equal("WORKFLOW.HEADLINE_COUNT", len(rows), EXPECTED_WORKFLOWS,
                domain="workflow", sources=[rel(path)])
    audit.equal("WORKFLOW.TARGET_BIJECTION", set(targets), set(state_by_id),
                domain="workflow", sources=[rel(path)])
    audit.equal("WORKFLOW.UNIQUE_TARGET_COUNT", len(targets), len(set(targets)),
                domain="workflow", sources=[rel(path)])
    audit.equal("WORKFLOW.DOUBLE_REPLAY_AND_SHORTEST_PATH", errors, [],
                domain="workflow", sources=[rel(path), rel(MODEL)])
    audit.metrics.update({"WORKFLOW_COUNT": len(rows), "WORKFLOW_REPLAY_COUNT": len(rows) * 2,
                          "WORKFLOW_REPLAY_FAILURE_COUNT": len(errors),
                          "WORKFLOW_LENGTH_MIN": min(lengths, default=0),
                          "WORKFLOW_LENGTH_MAX": max(lengths, default=0),
                          "WORKFLOW_LENGTH_MEAN": statistics.fmean(lengths) if lengths else 0.0,
                          "WORKFLOW_LENGTH_MEDIAN": float(statistics.median(lengths)) if lengths else 0.0,
                          "WORKFLOW_LENGTH_DISTRIBUTION": dict(sorted(Counter(map(str, lengths)).items(),
                                                                  key=lambda item: int(item[0])))})
    return {"rows": rows}


def verify_exports(audit: Audit, runtime: dict[str, Any], composition_space: dict[str, Any]) -> dict[str, Any]:
    path = RAW / "export-census-v2.tsv"
    rows = read_tsv(path)
    by_id = {row.get("export_variant_id"): row for row in rows}
    errors: list[str] = []
    expected_ids: set[str] = set()
    for state in runtime["states"]:
        for preset in EXPORT_PRESETS:
            for theme in THEMES:
                identity = {
                    "api_version": "trace-exploration/v2",
                    "render_version": "trace-exploration-portrait-png-v2",
                    "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
                    "state_hash": state["state_hash"],
                    "state_presentation_hash": state["presentation_hash"],
                    "composition_id": state["composition_id"],
                    "export_preset": preset,
                    "theme_token_set": theme,
                }
                export_hash = canonical_hash(identity)
                export_id = f"TEV2-{export_hash[:24]}"
                expected_ids.add(export_id)
                row = by_id.get(export_id)
                if row is None:
                    errors.append(f"{export_id}:missing")
                    continue
                expected_fields = {
                    "state_id": state["state_id"], "state_hash": state["state_hash"],
                    "category_entry_id": state["category_entry_id"], "composition_id": state["composition_id"],
                    "seed_id": state["seed_id"], "export_preset": preset, "theme_token_set": theme,
                    "width": "1080", "height": "1620", "semantic_hash": state["semantic_hash"],
                    "state_presentation_hash": state["presentation_hash"],
                    "export_presentation_hash": export_hash,
                }
                for key, expected_value in expected_fields.items():
                    if str(row.get(key)) != expected_value:
                        errors.append(f"{export_id}:{key}")
    audit.equal("EXPORT.EXACT_ID_COVERAGE", set(by_id), expected_ids,
                domain="export", sources=[rel(path), rel(RAW / "state-census-v2.tsv")])
    audit.equal("EXPORT.IDENTITY_AND_DIMENSIONS", errors, [], domain="export", sources=[rel(path)])
    audit.equal("EXPORT.COUNT_EQUATION", len(rows), len(runtime["states"]) * len(THEMES) * len(EXPORT_PRESETS),
                domain="export", sources=[rel(path)])
    audit.equal("EXPORT.HEADLINE_COUNT", len(rows), EXPECTED_EXPORTS,
                domain="export", sources=[rel(path)])

    model = runtime["model"]
    capabilities = model.get("capabilities", {})
    expected_capabilities = {
        "category_count": 4,
        "category_entry_count": len(composition_space["category_entries"]),
        "vocabulary_count": EXPECTED_ACTIVE_VOCABULARY,
        "association_count": EXPECTED_ACTIVE_ASSOCIATIONS,
        "topology_composition_count": len(composition_space["topologies"]),
        "production_composition_count": len(composition_space["production_compositions"]),
        "state_count": len(runtime["states"]),
        "transition_count": audit.metrics.get("TRANSITION_COUNT"),
        "workflow_count": audit.metrics.get("WORKFLOW_COUNT"),
        "export_variant_count": len(rows),
        "actions": list(ACTIONS), "themes": list(THEMES), "export_presets": list(EXPORT_PRESETS),
        "maximum_node_count": 8, "generic_association_only": True,
    }
    capability_errors = {key: {"expected": value, "actual": capabilities.get(key)}
                         for key, value in expected_capabilities.items() if capabilities.get(key) != value}
    audit.equal("MODEL.CAPABILITY_HEADLINES", capability_errors, {}, domain="model", sources=[rel(MODEL)])
    audit.equal("MODEL.API_VERSION", capabilities.get("api_version"), "trace-exploration/v2",
                domain="model", sources=[rel(MODEL)])

    metadata_path = RAW / "production-read-model-metadata-v2.json"
    metadata = read_json(metadata_path)
    model_sha = sha256_path(MODEL)
    model_bytes = MODEL.stat().st_size
    metadata_expected = {
        "production_read_model_path": MODEL_REL.as_posix(),
        "production_read_model_sha256": model_sha,
        "production_read_model_bytes": model_bytes,
        "audit_state_count": len(runtime["states"]),
        "audit_transition_count": audit.metrics.get("TRANSITION_COUNT"),
        "audit_workflow_count": audit.metrics.get("WORKFLOW_COUNT"),
        "audit_export_variant_count": len(rows),
        "audit_to_production_equivalence_mismatch_count": 0,
    }
    audit.equal("MODEL.METADATA_IDENTITY", metadata, metadata_expected,
                domain="model", sources=[rel(metadata_path), rel(MODEL)])
    audit.equal("MODEL.FROZEN_PRODUCTION_SHA256", model_sha, EXPECTED_PRODUCTION_MODEL_SHA256,
                domain="model", sources=[rel(MODEL)])
    used_associations = {association_id for row in composition_space["topologies"] for association_id in row["association_ids"]}
    visible_associations = {association_id for row in runtime["states"] for association_id in row["visible_association_ids"]}
    exported_state_ids = {row["state_id"] for row in rows}
    exported_associations = {association_id for state_id in exported_state_ids
                             for association_id in runtime["state_by_id"][state_id]["visible_association_ids"]}
    audit.equal("METRIC.ALL_ACTIVE_ASSOCIATIONS_ADMITTED", len(used_associations), EXPECTED_ACTIVE_ASSOCIATIONS,
                domain="metrics", sources=[rel(path), rel(RAW / "canonical-composition-registry-v2.json")])
    audit.equal("METRIC.ALL_ACTIVE_ASSOCIATIONS_VISIBLE", len(visible_associations), EXPECTED_ACTIVE_ASSOCIATIONS,
                domain="metrics", sources=[rel(RAW / "state-census-v2.tsv")])
    audit.equal("METRIC.ALL_ACTIVE_ASSOCIATIONS_EXPORTED", len(exported_associations), EXPECTED_ACTIVE_ASSOCIATIONS,
                domain="metrics", sources=[rel(path)])
    audit.metrics.update({
        "EXPORT_VARIANT_COUNT": len(rows), "PRODUCTION_READ_MODEL_BYTES": model_bytes,
        "PRODUCTION_READ_MODEL_SHA256": model_sha,
        "ASSOCIATION_USED_BY_ANY_COMPOSITION_COUNT": len(used_associations),
        "ASSOCIATION_ADMITTED_BY_ANY_COMPOSITION_COUNT": len(used_associations),
        "ASSOCIATION_VISIBLE_IN_ANY_STATE_COUNT": len(visible_associations),
        "ASSOCIATION_EXPORTED_IN_ANY_CARD_COUNT": len(exported_associations),
    })
    return {"rows": rows, "by_id": by_id, "expected_ids": expected_ids}


def verify_png_gate(audit: Audit, exports: dict[str, Any], allow_incomplete: bool) -> list[dict[str, str]]:
    path = RAW / "png-validation-v2.tsv"
    if not path.is_file():
        audit.check("PNG.FINAL_GATE_PRESENT", allow_incomplete, domain="png", expected="present",
                    actual="missing", sources=[rel(path)], skipped=allow_incomplete)
        return []
    rows = read_tsv(path)
    headers = set(rows[0]) if rows else set()
    audit.equal("PNG.MINIMUM_SCHEMA", PNG_REQUIRED_COLUMNS - headers, set(), domain="png", sources=[rel(path)])
    by_id = {row.get("export_variant_id"): row for row in rows}
    audit.equal("PNG.EXACT_EXPORT_COVERAGE", set(by_id), exports["expected_ids"],
                domain="png", sources=[rel(path), rel(RAW / "export-census-v2.tsv")])
    boolean_fields = (
        "manifest_validated", "manifest_schema_valid", "state_hash_match", "semantic_hash_match",
        "presentation_hash_match", "png_rendered", "png_decoded", "dimensions_valid",
        "upper_map_zone_valid", "lower_tree_zone_valid", "all_labels_valid",
        "all_visible_associations_valid", "provenance_summary_valid", "zero_archive_object_exposure",
        "replay_match", "map_tree_state_match",
    )
    errors: list[str] = []
    for export_id, row in by_id.items():
        export = exports["by_id"].get(export_id)
        if export is None:
            errors.append(f"{export_id}:unknown_export")
            continue
        for field in boolean_fields:
            try:
                if not as_bool(row.get(field)):
                    errors.append(f"{export_id}:{field}")
            except ValueError:
                errors.append(f"{export_id}:{field}:malformed")
        for field, expected in (("state_id", export["state_id"]), ("theme_token_set", export["theme_token_set"]),
                                ("export_preset", export["export_preset"]), ("width", "1080"), ("height", "1620"),
                                ("error_code", "")):
            if str(row.get(field, "")) != expected:
                errors.append(f"{export_id}:{field}")
        status_parts = str(row.get("http_status", "")).split(";")
        if not status_parts or any(part != "200" for part in status_parts):
            errors.append(f"{export_id}:http_status")
        png_hash = str(row.get("png_sha256", ""))
        replay_hash = str(row.get("replay_png_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", png_hash) or replay_hash != png_hash:
            errors.append(f"{export_id}:png_replay_hash")
        try:
            if float(row.get("elapsed_ms", "-1")) < 0:
                errors.append(f"{export_id}:elapsed_ms")
        except ValueError:
            errors.append(f"{export_id}:elapsed_ms")
    audit.equal("PNG.EVERY_VARIANT_VALIDATED_AND_REPLAYED", errors, [], domain="png", sources=[rel(path)])
    audit.equal("PNG.MANIFEST_RENDER_VALIDATION_EQUATION", len(rows), len(exports["rows"]),
                domain="png", sources=[rel(path)])
    def valid_flag(row: Mapping[str, Any], field: str) -> bool:
        try:
            return as_bool(row.get(field))
        except ValueError:
            return False
    audit.metrics.update({"PNG_MANIFEST_VALIDATED_COUNT": sum(valid_flag(row, "manifest_validated") for row in rows),
                          "PNG_RENDERED_COUNT": sum(valid_flag(row, "png_rendered") for row in rows),
                          "PNG_VALIDATED_COUNT": sum(all(valid_flag(row, field) for field in boolean_fields) for row in rows),
                          "PNG_REPLAY_MATCH_COUNT": sum(valid_flag(row, "replay_match") for row in rows),
                          "PNG_VALIDATION_FAILURE_COUNT": len({e.split(":", 1)[0] for e in errors}),
                          "PNG_FAILURE_COUNT": len({e.split(":", 1)[0] for e in errors})})
    return rows


def api_case_passed(row: Mapping[str, Any]) -> bool:
    if row.get("pass") is True or row.get("passed") is True:
        return True
    return str(row.get("status", row.get("result", ""))).upper() in {"PASS", "PASSED"}


def verify_api_gate(audit: Audit, allow_incomplete: bool) -> dict[str, Any]:
    path = RAW / "api-functional-validation-v2.json"
    if not path.is_file():
        audit.check("API.FINAL_GATE_PRESENT", allow_incomplete, domain="api", expected="present",
                    actual="missing", sources=[rel(path)], skipped=allow_incomplete)
        return {}
    document = read_json(path)
    audit.equal("API.EXACT_TOP_LEVEL_CONTRACT", set(document), API_TOP_LEVEL_FIELDS,
                domain="api", sources=[rel(path)])
    cases = document.get("cases", [])
    passed = sum(api_case_passed(row) for row in cases)
    audit.equal("API.CASE_COUNT", document.get("case_count"), len(cases), domain="api", sources=[rel(path)])
    audit.equal("API.PASS_COUNT", document.get("pass_count"), passed, domain="api", sources=[rel(path)])
    audit.equal("API.FAIL_COUNT", document.get("fail_count"), len(cases) - passed, domain="api", sources=[rel(path)])
    zero_fields = ("fail_count", "unexpected_5xx_count", "stale_state_accepted_count",
                   "invalid_target_accepted_count", "held_data_leak_count", "public_archive_object_id_count",
                   "public_archive_object_title_count", "public_record_link_count",
                   "public_context_reference_count", "public_spacetime_reference_count")
    errors = [field for field in zero_fields if document.get(field) != 0]
    if not isinstance(document.get("schema_version"), str) or not document.get("schema_version"):
        errors.append("schema_version")
    if not isinstance(document.get("base_url"), str) or not re.match(r"^https?://", document.get("base_url", "")):
        errors.append("base_url")
    if document.get("status") != "PASS":
        errors.append("status")
    if document.get("api_version") != "trace-exploration/v2":
        errors.append("api_version")
    if document.get("actual_production_http_tested") is not True:
        errors.append("actual_production_http_tested")
    if passed != len(cases):
        errors.append("case_failures")
    case_ids = [row.get("case_id") for row in cases]
    if any(not case_id for case_id in case_ids) or len(case_ids) != len(set(case_ids)):
        errors.append("case_id_coverage")
    audit.equal("API.PRODUCTION_FUNCTIONAL_GATES", errors, [], domain="api", sources=[rel(path)])
    audit.metrics.update({"API_CASE_COUNT": len(cases), "API_PASS_COUNT": passed,
                          "API_FAILURE_COUNT": len(cases) - passed, "API_UNEXPECTED_5XX_COUNT": document.get("unexpected_5xx_count")})
    return document


AUDIT_COUNTER_KEYS = {
    "public_archive_object_id_count", "public_archive_object_title_count", "public_record_link_count",
    "public_context_reference_count", "public_spacetime_reference_count", "zero_archive_object_exposure",
}
FORBIDDEN_PUBLIC_KEYS = {
    "archiveobject", "archiveobjectid", "archiveobjecttitle", "recordid", "recordtitle", "recordlink",
    "thumbnail", "thumbnailurl", "relatedrecord", "relatedrecordid", "context", "contextid",
    "spacetime", "spacetimeid", "search", "searchresult", "searchresults", "searchmanifest",
}
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"(?:^|/)(?:api/)?search(?:/|$)", re.I),
    re.compile(r"search[-_]?manifest|trace[-_]?search", re.I),
    re.compile(r"/(?:record|archive-object)s?/", re.I),
    re.compile(r"\b(?:OBJ|REC|ARCHIVE|CONTEXT|SPACETIME)[-:][A-Z0-9]", re.I),
    re.compile(r"trace[-_]?(?:context|spacetime)", re.I),
)


def scan_public_payload(value: Any, location: str = "$") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if key not in AUDIT_COUNTER_KEYS and normalized_key in FORBIDDEN_PUBLIC_KEYS:
                violations.append(f"{child_location}:forbidden_key")
            violations.extend(scan_public_payload(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(scan_public_payload(child, f"{location}[{index}]") )
    elif isinstance(value, str):
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                violations.append(f"{location}:forbidden_value:{pattern.pattern}")
    return violations


def verify_public_boundary(audit: Audit, runtime: dict[str, Any], exports: dict[str, Any],
                           api_document: dict[str, Any], png_rows: list[dict[str, str]]) -> None:
    payloads: list[tuple[str, Any]] = [
        (rel(MODEL), runtime["model"]),
        (rel(RAW / "export-census-v2.tsv"), exports["rows"]),
    ]
    # API response bodies are not copied into the functional ledger. Its exact
    # zero-leak counters are verified separately above; scanning request routes
    # would misclassify deliberate hostile test inputs as public responses.
    if png_rows:
        payloads.append((rel(RAW / "png-validation-v2.tsv"), png_rows))
    violations: list[str] = []
    for source, payload in payloads:
        violations.extend(f"{source}:{item}" for item in scan_public_payload(payload))
    audit.equal("BOUNDARY.PUBLIC_PAYLOAD_ZERO_FORBIDDEN_REFS", violations, [], domain="boundary",
                sources=[source for source, _ in payloads])

    source_patterns = (
        re.compile(r"search[-_]?manifest|trace[-_]?search|/api/search", re.I),
        re.compile(r"\bSearch(?:Result|DTO|Index|Manifest)\b"),
        re.compile(r"archive[_A-Z]?object(?:[_A-Z]?(?:id|title))?|archiveObject(?:Id|Title)", re.I),
        re.compile(r"record[_A-Z]?(?:id|title|link)|relatedRecord|thumbnail", re.I),
        re.compile(r"ContextCanvas|trace[-_]?context|context[_A-Z]?id", re.I),
        re.compile(r"Spacetime|trace[-_]?spacetime|spacetime[_A-Z]?id", re.I),
    )
    source_violations: list[str] = []
    for path_rel in API_SOURCE_RELS:
        text = (REPO / path_rel).read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            for pattern in source_patterns:
                if pattern.search(line):
                    source_violations.append(f"{path_rel.as_posix()}:{number}:{pattern.pattern}")
    audit.equal("BOUNDARY.API_SOURCE_ZERO_FORBIDDEN_DEPENDENCIES", source_violations, [], domain="boundary",
                sources=[path.as_posix() for path in API_SOURCE_RELS])
    audit.metrics.update({"PUBLIC_ARCHIVE_OBJECT_REFERENCE_COUNT": 0 if not violations else len(violations),
                          "PUBLIC_SEARCH_DEPENDENCY_COUNT": sum("search" in row.casefold() for row in source_violations),
                          "PUBLIC_CONTEXT_SPACETIME_REFERENCE_COUNT": sum(
                              "context" in row.casefold() or "spacetime" in row.casefold() for row in source_violations)})


def verify_summaries_and_equations(audit: Audit, composition_space: dict[str, Any], runtime: dict[str, Any],
                                   exports: dict[str, Any], png_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    parameter_path = RAW / "exploration-parameter-universe-v2.json"
    parameter_doc = read_json(parameter_path)
    parameters = parameter_doc.get("parameters", [])
    audit.equal("PARAMETER.FROZEN", parameter_doc.get("frozen"), True, domain="parameters", sources=[rel(parameter_path)])
    audit.equal("PARAMETER.DATABASE_SNAPSHOT", parameter_doc.get("database_snapshot"), EXPECTED_DATABASE_SNAPSHOT,
                domain="parameters", sources=[rel(parameter_path)])
    audit.equal("PARAMETER.COUNT", parameter_doc.get("parameter_count"), len(parameters),
                domain="parameters", sources=[rel(parameter_path)])
    audit.equal("PARAMETER.HASH", parameter_doc.get("parameter_universe_hash"), canonical_hash(parameters),
                domain="parameters", sources=[rel(parameter_path)])
    audit.metrics["PARAMETER_UNIVERSE_FROZEN"] = parameter_doc.get("frozen") is True
    parameter_by_name = {row.get("parameter_name"): row for row in parameters}
    parameter_expectations = {
        "topology": list(TOPOLOGIES), "qualification_gate": [False], "navigation_return": [False],
        "evidence_gap_node_ids": [[]], "degree_bound": [2], "maximum_node_count": [8],
        "theme_token": list(THEMES), "export_preset": list(EXPORT_PRESETS),
    }
    parameter_errors = {key: parameter_by_name.get(key, {}).get("legal_values")
                        for key, expected in parameter_expectations.items()
                        if parameter_by_name.get(key, {}).get("legal_values") != expected}
    audit.equal("PARAMETER.STRICT_DOMAINS", parameter_errors, {}, domain="parameters", sources=[rel(parameter_path)])

    summary_path = RAW / "space-generation-summary-v2.json"
    summary = read_json(summary_path)
    summary_expectations = {
        "canonical_association_subgraph_count": audit.metrics["CANONICAL_ASSOCIATION_SUBGRAPH_COUNT"],
        "topology_instantiated_composition_count": audit.metrics["VALID_TOPOLOGY_COMPOSITION_COUNT"],
        "seed_variant_count": audit.metrics["SEED_VARIANT_COUNT"],
        "category_entry_variant_count": audit.metrics["CATEGORY_ENTRY_COUNT"],
        "production_composition_count": audit.metrics["PRODUCTION_COMPOSITION_COUNT"],
        "state_enumerated_count": audit.metrics["STATE_COUNT"],
        "state_validated_count": audit.metrics["STATE_COUNT"],
        "unreachable_production_state_count": 0,
        "duplicate_state_hash_count": 0,
        "transition_enumerated_count": audit.metrics["TRANSITION_COUNT"],
        "transition_executed_count": audit.metrics["TRANSITION_COUNT"],
        "transition_pass_count": audit.metrics["TRANSITION_COUNT"],
        "transition_fail_count": 0,
        "canonical_workflow_count": audit.metrics["WORKFLOW_COUNT"],
        "workflow_replayed_count": audit.metrics["WORKFLOW_COUNT"],
        "workflow_replay_failure_count": 0,
        "workflow_length_min": audit.metrics["WORKFLOW_LENGTH_MIN"],
        "workflow_length_max": audit.metrics["WORKFLOW_LENGTH_MAX"],
        "workflow_length_mean": audit.metrics["WORKFLOW_LENGTH_MEAN"],
        "workflow_length_median": audit.metrics["WORKFLOW_LENGTH_MEDIAN"],
        "workflow_length_distribution": audit.metrics["WORKFLOW_LENGTH_DISTRIBUTION"],
        "state_replay_mismatch_count": 0,
        "semantic_replay_mismatch_count": 0,
        "export_variant_count": audit.metrics["EXPORT_VARIANT_COUNT"],
        "production_read_model_bytes": audit.metrics["PRODUCTION_READ_MODEL_BYTES"],
        "production_read_model_sha256": audit.metrics["PRODUCTION_READ_MODEL_SHA256"],
        "registry_hash": composition_space["registry"].get("registry_hash"),
    }
    summary_errors = {key: {"expected": expected, "actual": summary.get(key)}
                      for key, expected in summary_expectations.items() if summary.get(key) != expected}
    audit.equal("SUMMARY.RECOMPUTED_HEADLINES", summary_errors, {}, domain="summary", sources=[rel(summary_path)])

    equations = [
        {"equation_id": "EQ-VOCABULARY-DISPOSITIONS", "expression": "31+1+12+21=65",
         "lhs": sum(VOCABULARY_DISPOSITIONS.values()), "rhs": EXPECTED_CANDIDATES},
        {"equation_id": "EQ-PAIR-UNIVERSE", "expression": "31*30/2=465",
         "lhs": EXPECTED_ACTIVE_VOCABULARY * (EXPECTED_ACTIVE_VOCABULARY - 1) // 2, "rhs": EXPECTED_PAIRS},
        {"equation_id": "EQ-ACTIVE-ASSOCIATIONS", "expression": "18+3=21",
         "lhs": EXPECTED_EXTERNALLY_SUPPORTED + EXPECTED_SOURCE_SUPPORTED, "rhs": audit.metrics["GRAPH_EDGE_COUNT"]},
        {"equation_id": "EQ-GRAPH-ASSOCIATIONS", "expression": "graph edges=active associations",
         "lhs": audit.metrics["GRAPH_EDGE_COUNT"], "rhs": audit.metrics["ACTIVE_ASSOCIATION_COUNT"]},
        {"equation_id": "EQ-TOPOLOGY-CANDIDATES", "expression": "valid+invalid=58*6",
         "lhs": audit.metrics["VALID_TOPOLOGY_COMPOSITION_COUNT"] + audit.metrics["INVALID_TOPOLOGY_CANDIDATE_COUNT"],
         "rhs": EXPECTED_SUBGRAPHS * len(TOPOLOGIES)},
        {"equation_id": "EQ-SEEDS", "expression": "seeds=sum topology node counts",
         "lhs": audit.metrics["SEED_VARIANT_COUNT"],
         "rhs": sum(row["node_count"] for row in composition_space["topologies"])},
        {"equation_id": "EQ-CATEGORY-ENTRIES", "expression": "entries=sum shared-category counts",
         "lhs": audit.metrics["CATEGORY_ENTRY_COUNT"],
         "rhs": sum(len(row["category_ids"]) for row in composition_space["topologies"])},
        {"equation_id": "EQ-PRODUCTION-COMPOSITIONS", "expression": "production=sum(entry seed variants)",
         "lhs": audit.metrics["PRODUCTION_COMPOSITION_COUNT"],
         "rhs": sum(len(row["seed_variant_ids"]) for row in composition_space["category_entries"])},
        {"equation_id": "EQ-STATES", "expression": "states=sum(n*2^n)",
         "lhs": audit.metrics["STATE_COUNT"],
         "rhs": sum(len(row["node_ids"]) * (1 << len(row["node_ids"]))
                    for row in composition_space["production_compositions"].values())},
        {"equation_id": "EQ-TRANSITIONS", "expression": "transitions=sum legal action-target counts over states",
         "lhs": audit.metrics["TRANSITION_COUNT"],
         "rhs": sum(len(expected_transitions_for_state(runtime, row)) for row in runtime["states"])},
        {"equation_id": "EQ-STATE-IMMUTABILITY", "expression": "forbidden in-place state mutations=0",
         "lhs": audit.metrics["STATE_MUTATION_COUNT"], "rhs": 0},
        {"equation_id": "EQ-WORKFLOWS", "expression": "workflows=states",
         "lhs": audit.metrics["WORKFLOW_COUNT"], "rhs": audit.metrics["STATE_COUNT"]},
        {"equation_id": "EQ-EXPORTS", "expression": "exports=states*2 themes*1 preset",
         "lhs": audit.metrics["EXPORT_VARIANT_COUNT"],
         "rhs": audit.metrics["STATE_COUNT"] * len(THEMES) * len(EXPORT_PRESETS)},
    ]
    if png_rows:
        equations.extend([
            {"equation_id": "EQ-PNG-MANIFEST", "expression": "manifest validated=exports",
             "lhs": audit.metrics.get("PNG_MANIFEST_VALIDATED_COUNT"), "rhs": audit.metrics["EXPORT_VARIANT_COUNT"]},
            {"equation_id": "EQ-PNG-RENDER", "expression": "png rendered=exports",
             "lhs": audit.metrics.get("PNG_RENDERED_COUNT"), "rhs": audit.metrics["EXPORT_VARIANT_COUNT"]},
            {"equation_id": "EQ-PNG-VALIDATE", "expression": "png validated=exports",
             "lhs": audit.metrics.get("PNG_VALIDATED_COUNT"), "rhs": audit.metrics["EXPORT_VARIANT_COUNT"]},
            {"equation_id": "EQ-PNG-REPLAY", "expression": "png replay matches=exports",
             "lhs": audit.metrics.get("PNG_REPLAY_MATCH_COUNT"), "rhs": audit.metrics["EXPORT_VARIANT_COUNT"]},
        ])
    for equation in equations:
        equation["status"] = "PASS" if equation["lhs"] == equation["rhs"] else "FAIL"
        audit.equal(equation["equation_id"], equation["lhs"], equation["rhs"], domain="equations",
                    sources=[rel(summary_path)])
    return equations


def current_artifact_entries(*, allow_incomplete_gates: bool) -> list[dict[str, Any]]:
    uninventoried = uninventoried_round16a_source_rels()
    if uninventoried:
        raise FileNotFoundError(
            "uninventoried Round 16A source paths: "
            + ", ".join(path.as_posix() for path in uninventoried)
        )
    paths: set[Path] = {RAW / name for name in SEMANTIC_ARTIFACTS}
    paths.add(MODEL)
    paths.update(REPO / path for path in ALL_SOURCE_RELS)
    # Reproduction also freezes the governed upstream inputs named by the
    # vocabulary universe plus the independent association/composition inputs.
    universe_path = RAW / "vocabulary-candidate-universe-v2.json"
    if universe_path.is_file():
        universe = read_json(universe_path)
        for row in universe.get("source_inputs", []):
            if isinstance(row, dict) and isinstance(row.get("path"), str):
                paths.add(REPO / row["path"])
    paths.update({
        REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/association-calibration.tsv",
        REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv",
        REPO / "scripts/trace-v49-exploration-composition-engine/model.py",
        REPO / "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json",
    })
    missing: list[str] = []
    entries: list[dict[str, Any]] = []
    for path in sorted(paths, key=rel):
        if not path.is_file():
            if allow_incomplete_gates and path.name in GATED_ARTIFACTS:
                continue
            missing.append(rel(path))
            continue
        entries.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_path(path)})
    if missing:
        raise FileNotFoundError("hash manifest inputs missing: " + ", ".join(missing))
    return entries


def write_hash_manifest(path: Path, *, allow_incomplete_gates: bool) -> None:
    entries = current_artifact_entries(allow_incomplete_gates=allow_incomplete_gates)
    material = {
        "schema_version": "trace-exploration-round16a-artifact-sha-manifest-v2",
        "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
        "hash_algorithm": "SHA-256",
        "canonicalization": "UTF8_SORTED_KEY_COMPACT_JSON_NO_TIMESTAMP",
        "file_count": len(entries),
        "files": entries,
    }
    document = {**material, "manifest_hash": canonical_hash(material)}
    write_json(path, document)


def write_case_tsv(path: Path, cases: Sequence[Mapping[str, Any]]) -> None:
    fields = ("case_id", "domain", "status", "expected", "actual", "sources", "detail")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for case in sorted(cases, key=lambda row: str(row["case_id"])):
            writer.writerow({
                "case_id": case["case_id"], "domain": case["domain"], "status": case["status"],
                "expected": compact(case["expected"]).decode("utf-8"),
                "actual": compact(case["actual"]).decode("utf-8"),
                "sources": compact(case["sources"]).decode("utf-8"),
                "detail": case["detail"] or "NONE",
            })


METRIC_DEFINITIONS: dict[str, tuple[str, str, str, str]] = {
    "VOCABULARY_CANDIDATE_COUNT": ("Number of normalized, casefold-deduplicated governed vocabulary candidates.",
                                   "candidate", "vocabulary-candidate-universe-v2.json", "build_vocabulary_universe.py"),
    "ACTIVE_VOCABULARY_COUNT": ("Number of candidate rows with final ACTIVE disposition and complete evidence/category gates.",
                                "term", "active-vocabulary-v2.json", "build_vocabulary_census.py"),
    "PAIR_UNIVERSE_COUNT": ("Cardinality of the unordered two-element subsets of the active vocabulary.",
                            "pair", "pair-universe-v2.json", "build_pair_universe.py"),
    "ACTIVE_ASSOCIATION_COUNT": ("Pairs whose final association status is an active evidence-qualified status.",
                                 "association", "association-census-v2.json", "build_association_census.py"),
    "GRAPH_NODE_COUNT": ("Active vocabulary vertices represented by the validated association graph.",
                         "node", "validated-association-graph-v2.json", "build_association_census.py"),
    "GRAPH_EDGE_COUNT": ("Evidence-qualified active pair edges represented by the validated association graph.",
                         "edge", "validated-association-graph-v2.json", "build_association_census.py"),
    "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT": ("Connected non-empty active-edge subsets spanning at most eight endpoint nodes.",
                                             "subgraph", "canonical-composition-registry-v2.json", "build_exploration_space.py"),
    "VALID_TOPOLOGY_COMPOSITION_COUNT": ("Subgraph/topology candidates satisfying the strict Round 16A topology predicates.",
                                         "composition", "composition-enumeration-v2.tsv", "build_exploration_space.py"),
    "SEED_VARIANT_COUNT": ("Sum of legal seed nodes over every valid topology composition.",
                           "seed variant", "canonical-composition-registry-v2.json", "build_exploration_space.py"),
    "CATEGORY_ENTRY_COUNT": ("Sum of non-empty shared governed-category intersections over valid topology compositions.",
                             "category entry", "category-entry-census-v2.tsv", "build_exploration_space.py"),
    "PRODUCTION_COMPOSITION_COUNT": ("Cartesian product of each category entry and its topology seed variants.",
                                     "production composition", "production-read-model.json", "build_exploration_space.py"),
    "STATE_COUNT": ("Sum over production compositions of node_count multiplied by two to the node_count.",
                    "state", "state-census-v2.tsv", "build_exploration_space.py"),
    "TRANSITION_COUNT": ("Complete legal action-target transition rows over every enumerated state.",
                         "transition", "transition-census-v2.tsv", "build_exploration_space.py"),
    "WORKFLOW_COUNT": ("One canonical shortest, twice-replayed local workflow for every state.",
                       "workflow", "workflow-census-v2.tsv", "build_exploration_space.py"),
    "EXPORT_VARIANT_COUNT": ("Every state crossed with two themes and one portrait export preset.",
                             "export variant", "export-census-v2.tsv", "build_exploration_space.py"),
    "ASSOCIATION_USED_BY_ANY_COMPOSITION_COUNT": ("Distinct graph edges occurring in at least one strict topology composition.",
                                                  "association", "canonical-composition-registry-v2.json", "build_exploration_space.py"),
    "ASSOCIATION_ADMITTED_BY_ANY_COMPOSITION_COUNT": ("Distinct graph edges admitted by at least one production composition.",
                                                      "association", "production-read-model.json", "build_exploration_space.py"),
    "ASSOCIATION_VISIBLE_IN_ANY_STATE_COUNT": ("Distinct graph edges in at least one state visible-association projection.",
                                               "association", "state-census-v2.tsv", "build_exploration_space.py"),
    "ASSOCIATION_EXPORTED_IN_ANY_CARD_COUNT": ("Distinct visible graph edges carried by at least one export variant state.",
                                               "association", "export-census-v2.tsv", "build_exploration_space.py"),
}


def metric_dictionary(audit: Audit, status: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    public_safe_status = "FAIL" if any(
        row["status"] == "FAIL" and row["domain"] in {"boundary", "api", "png"}
        for row in audit.cases
    ) else "PASS"
    for name, value in sorted(audit.metrics.items()):
        definition, unit, source, generator = METRIC_DEFINITIONS.get(
            name, (f"Independently recomputed Round 16A metric {name}.", "value",
                   "independent-verification.json", "multiple governed generators")
        )
        rows.append({
            "metric_name": name, "formal_definition": definition, "unit": unit,
            "numerator": value if isinstance(value, (int, float)) and not isinstance(value, bool) else None,
            "denominator": None, "source_artifact": source, "generation_script": generator,
            "verification_script": "scripts/trace_round16a/verify_full_space.py",
            "database_snapshot": EXPECTED_DATABASE_SNAPSHOT, "value": value,
            "independent_verification_status": status, "public_safe_status": public_safe_status,
            "caveat": "Counts describe the governed evidence-qualified finite model; they are not claims of historical importance, causation, or completeness beyond the frozen scope.",
            "required_caveat": "Counts describe the governed evidence-qualified finite model; they are not claims of historical importance, causation, or completeness beyond the frozen scope.",
        })
    return {"schema_version": "trace-exploration-metric-dictionary-v2", "status": status,
            "database_snapshot": EXPECTED_DATABASE_SNAPSHOT, "metric_count": len(rows), "metrics": rows}


def headline_document(audit: Audit, equations: Sequence[Mapping[str, Any]], status: str) -> dict[str, Any]:
    headline_keys = (
        "VOCABULARY_CANDIDATE_COUNT", "ACTIVE_VOCABULARY_COUNT", "PAIR_UNIVERSE_COUNT",
        "ACTIVE_ASSOCIATION_COUNT", "GRAPH_NODE_COUNT", "GRAPH_EDGE_COUNT",
        "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT", "VALID_TOPOLOGY_COMPOSITION_COUNT",
        "SEED_VARIANT_COUNT", "CATEGORY_ENTRY_COUNT", "PRODUCTION_COMPOSITION_COUNT",
        "STATE_COUNT", "TRANSITION_COUNT", "WORKFLOW_COUNT", "EXPORT_VARIANT_COUNT",
        "STATE_MUTATION_COUNT", "TRANSITION_DIFFERENT_NEXT_STATE_COUNT",
        "ASSOCIATION_USED_BY_ANY_COMPOSITION_COUNT", "ASSOCIATION_ADMITTED_BY_ANY_COMPOSITION_COUNT",
        "ASSOCIATION_VISIBLE_IN_ANY_STATE_COUNT", "ASSOCIATION_EXPORTED_IN_ANY_CARD_COUNT",
    )
    return {"schema_version": "trace-exploration-headline-numbers-v2", "status": status,
            "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
            "headlines": {key: audit.metrics.get(key) for key in headline_keys},
            "equations": list(equations)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hash-only-manifest", type=Path,
                        help="Write only a deterministic artifact SHA manifest to this path.")
    parser.add_argument("--allow-incomplete-gates", action="store_true",
                        help="Development-only: permit missing API/PNG final-gate artifacts.")
    parser.add_argument("--case-tsv", type=Path,
                        default=RAW / "independent-verification-cases.tsv")
    return parser.parse_args()


def resolve_output(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (REPO / path).resolve()


def main() -> int:
    args = parse_args()
    if args.hash_only_manifest is not None:
        write_hash_manifest(resolve_output(args.hash_only_manifest),
                            allow_incomplete_gates=True)
        return 0

    audit = Audit()
    equations: list[dict[str, Any]] = []
    required_ok = require_inputs(audit, args.allow_incomplete_gates)
    core_names = [name for name in SEMANTIC_ARTIFACTS if name not in GATED_ARTIFACTS]
    core_ready = all((RAW / name).is_file() for name in core_names) and MODEL.is_file() and all(
        (REPO / path).is_file() for path in ALL_SOURCE_RELS
    )
    if core_ready:
        try:
            vocabulary = verify_vocabulary(audit)
            association = verify_pairs_and_graph(audit, vocabulary)
            composition_space = verify_composition_space(audit, vocabulary, association)
            runtime = verify_model_and_states(audit, composition_space, association, vocabulary)
            transitions = verify_transitions(audit, runtime)
            verify_workflows(audit, runtime, transitions)
            exports = verify_exports(audit, runtime, composition_space)
            png_rows = verify_png_gate(audit, exports, args.allow_incomplete_gates)
            api_document = verify_api_gate(audit, args.allow_incomplete_gates)
            verify_public_boundary(audit, runtime, exports, api_document, png_rows)
            equations = verify_summaries_and_equations(audit, composition_space, runtime, exports, png_rows)
        except Exception as error:  # deterministic fail-closed receipt for malformed artifacts
            audit.check("INDEPENDENT_VERIFIER.UNCAUGHT_ARTIFACT_ERROR", False, domain="verifier",
                        expected="all artifacts parse and reconcile", actual=f"{type(error).__name__}:{error}",
                        sources=["scripts/trace_round16a/verify_full_space.py"])
    elif required_ok:
        audit.check("INDEPENDENT_VERIFIER.CORE_READY", False, domain="inputs", expected=True, actual=False)

    audit.metrics["INDEPENDENT_COUNT_MISMATCH_COUNT"] = sum(
        row["status"] == "FAIL" and ("COUNT" in row["case_id"] or row["domain"] == "equations")
        for row in audit.cases
    )
    audit.metrics["INDEPENDENT_HASH_MISMATCH_COUNT"] = sum(
        row["status"] == "FAIL" and ("HASH" in row["case_id"] or "SHA" in row["case_id"])
        for row in audit.cases
    )
    status = "PASS" if not audit.failures else "FAIL"
    pass_count = sum(row["status"] == "PASS" for row in audit.cases)
    skip_count = sum(row["status"] == "SKIP" for row in audit.cases)
    artifact_entries: list[dict[str, Any]] = []
    try:
        artifact_entries = current_artifact_entries(allow_incomplete_gates=args.allow_incomplete_gates)
    except FileNotFoundError:
        pass
    independent = {
        "schema_version": "trace-exploration-independent-verification-v2",
        "status": status, "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
        "verification_script": "scripts/trace_round16a/verify_full_space.py",
        "generator_import_count": 0, "direct_edge_mask_enumeration": True,
        "case_count": len(audit.cases), "pass_count": pass_count,
        "fail_count": len(audit.failures), "skip_count": skip_count,
        "failure_case_ids": [row["case_id"] for row in audit.failures],
        "metrics": dict(sorted(audit.metrics.items())), "equations": equations,
        "verified_artifact_count": len(artifact_entries),
        "verified_artifact_manifest_hash": canonical_hash(artifact_entries),
        "cases": sorted(audit.cases, key=lambda row: row["case_id"]),
    }
    quantitative = {
        "schema_version": "trace-exploration-quantitative-audit-v2", "status": status,
        "database_snapshot": EXPECTED_DATABASE_SNAPSHOT,
        "metric_count": len(audit.metrics), "metrics": dict(sorted(audit.metrics.items())),
        "equation_count": len(equations), "equations": equations,
        "independent_case_count": len(audit.cases), "independent_failure_count": len(audit.failures),
    }
    write_json(RAW / "independent-verification.json", independent)
    write_json(RAW / "quantitative-audit.json", quantitative)
    write_json(RAW / "headline-numbers.json", headline_document(audit, equations, status))
    write_json(RAW / "metric-dictionary.json", metric_dictionary(audit, status))
    write_case_tsv(resolve_output(args.case_tsv), audit.cases)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
