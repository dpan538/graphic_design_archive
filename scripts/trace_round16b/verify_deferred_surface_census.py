#!/usr/bin/env python3
"""Independent verifier for the Round 16B deferred-surface census."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


CHECKPOINT_003_SHA = "df8aa185910d501daf5a4a5dded8674fdc8a0d87"
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
METHOD_SURFACES = RAW_REL / "evidence-surface-inventory.tsv"
PRIOR_SURFACE_LEDGER = RAW_REL / "local-surface-disposition-ledger-v1.tsv"
PRIOR_OCCURRENCES = RAW_REL / "candidate-trigger-occurrence-ledger-v1.tsv"
PRIOR_FAMILIES = RAW_REL / "local-candidate-family-ledger-v1.tsv"
PRIOR_CROSSWALK = RAW_REL / "concept-sense-crosswalk-v1.tsv"
V2_OCCURRENCES = RAW_REL / "candidate-trigger-occurrence-ledger-v2.tsv"
V2_FAMILIES = RAW_REL / "local-candidate-family-ledger-v2.tsv"
V2_SURFACE_LEDGER = RAW_REL / "local-surface-disposition-ledger-v2.tsv"
V2_CENSUS = RAW_REL / "local-candidate-census-v2.json"
V2_RECEIPT = RAW_REL / "deferred-surface-build-receipt-v2.json"
RESEARCH_NOTE = Path(
    "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/"
    "07_DEFERRED_SURFACE_AND_DATABASE_CENSUS.md"
)
VOCABULARY = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/vocabulary-census-v2.json")
R9_SOURCES = Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/03_SCHOLARLY_SOURCE_REGISTRY.tsv")
R9_CONTROLS = Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/12_REJECTED_AND_DEFERRED_TERMS.tsv")
R10_SOURCES = Path("docs/research/trace-v49-design-history-relation-grammar-round1/03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv")
R10_PAIR_MATRIX = Path("docs/research/trace-v49-design-history-relation-grammar-round1/08_ORDERED_PAIR_COMPATIBILITY_MATRIX.tsv")
R10_GAPS = Path("docs/research/trace-v49-design-history-relation-grammar-round1/20_VOCABULARY_GAP_REGISTER.tsv")
R11_CONSTRAINTS = Path("docs/research/trace-v49-exploration-constraint-kernel-round1/04_CONSTRAINT_REGISTRY.tsv")
R11_FIXTURES = Path("docs/research/trace-v49-exploration-constraint-kernel-round1/08_SYNTHETIC_FIXTURE_REGISTRY.tsv")
R11_ADVERSARIAL = Path("docs/research/trace-v49-exploration-constraint-kernel-round1/15_ADVERSARIAL_TEST_MATRIX.tsv")
R12_CANDIDATES = Path("docs/research/trace-v49-exploration-inquiry-flow-round1/02_RESEARCH_CANDIDATE_FREEZE.json")
R12_PAIR_QUESTIONS = Path("docs/research/trace-v49-exploration-inquiry-flow-round1/05_PAIR_QUESTION_EVIDENCE_COVERAGE.tsv")
R12_SEEDS = Path("docs/research/trace-v49-exploration-inquiry-flow-round1/08_INQUIRY_SEED_REGISTRY.tsv")
R12_INSTANCES = Path("docs/research/trace-v49-exploration-inquiry-flow-round1/11_RESEARCH_INSTANCE_REGISTRY.tsv")
R13_SOURCES = Path("docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv")
R13_PAIRS = Path("docs/research/trace-v49-exploration-composition-review-round1/05_PAIR_DECISION_REGISTRY.tsv")
R13_ACTIVATION = Path("docs/research/trace-v49-exploration-composition-review-round1/14_ACTIVATION_CANDIDATE_PACKAGE.json")
R13_HUMAN_REVIEW = Path("docs/research/trace-v49-exploration-composition-review-round1/16_EXTERNAL_DOMAIN_REVIEW_REGISTRY.tsv")
R14_NARY_RESULTS = Path("docs/audits/v49-exploration-association-calibration-round1/raw/nary-validation.tsv")
R16A_EVIDENCE = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/association-evidence-ledger-v2.tsv")
R16A_PARAMETERS = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/exploration-parameter-universe-v2.json")
R16A_QUERIES = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/association-query-log-v2.jsonl")
DATABASE = Path("data/prefreeze_candidate_v48.sqlite")
DATABASE_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
SELECTOR_VERSION = "trace-round16b-deferred-surface-selector-v2"
NORMALIZATION_VERSION = "trace-round16b-nfkc-casefold-nonalnum-space-longest-first-v1"
DATABASE_SQL_VERSION = "trace-round16b-database-discovery-sql-v1"

EXPECTED_DATABASE_CAPTURE_IDS = {
    "DGITRACE2026R0395",
    "HISTORICALAICTRACE2026V1R0161",
    "HISTORICALAICTRACE2026V1R0206",
    "LOCTRACE2026I3172E16AA089B6",
}
EXPECTED_DATABASE_CAPTURE_CONTROL_IDS = {
    "CHWCONTEMP2026V1R0009",
    "WHMZTRACE2026R0009",
}
EXPECTED_DATABASE_TRACE_SURFACE_IDS = {
    "SURF-VAM20K-00867",
    "SURF-VAM20K-03010",
    "SURF-VAM20K-03052",
    "SURF-VAM20K-03127",
    "SURF-VAM20K-03163",
    "SURF-VAM20K-03165",
    "SURF-VAM20K-03166",
}

OUTPUT_HEADERS = {
    "deferred-surface-execution-ledger-v2.tsv": [
        "surface_id", "round", "source_path", "source_sha256", "record_selector",
        "input_record_count", "selector_rule", "selector_version", "control_record_count",
        "alias_record_count", "metadata_lead_count", "new_trigger_occurrence_count",
        "new_candidate_family_count", "execution_disposition", "authority_dependency",
        "required_next_action", "record_sha256",
    ],
    "deferred-zero-emission-control-ledger-v2.tsv": [
        "control_record_id", "surface_id", "source_path", "source_record_ref",
        "source_record_locator", "selector_rule", "record_class", "emission_decision",
        "net_trigger_occurrence_count", "alias_or_blocker_ref", "authority_dependency",
        "notes", "source_record_sha256", "record_sha256",
    ],
    "source-identity-membership-ledger-v2.tsv": [
        "membership_id", "surface_id", "round", "source_path", "source_record_id",
        "canonical_source_id", "canonical_identity_kind", "canonical_identity_value",
        "membership_role", "representative_source_record_id", "authors", "year", "title",
        "venue", "doi_isbn_or_identifier", "stable_url", "rights_review_status",
        "evidence_use_status", "source_record_sha256", "record_sha256",
    ],
    "source-canonical-rights-queue-v2.tsv": [
        "canonical_source_id", "canonical_identity_kind", "canonical_identity_value",
        "representative_surface_id", "representative_source_path", "representative_source_record_id",
        "member_count", "member_ids_json", "authors", "year", "title", "venue",
        "doi_isbn_or_identifier", "stable_url", "rights_review_status", "text_access_status",
        "locator_review_status", "association_evidence_status", "required_next_action", "record_sha256",
    ],
    "round16a-evidence-alias-ledger-v2.tsv": [
        "alias_id", "round16a_ledger_id", "round14_evidence_id", "pair_id", "source_id",
        "common_field_count", "common_fields_json", "exact_match", "derivative_rule",
        "net_new_evidence_object_count", "record_sha256",
    ],
    "round16a-query-result-alias-ledger-v2.tsv": [
        "alias_id", "query_id", "pair_id", "candidate_source_id", "rank",
        "round16a_ledger_id", "doi", "title", "stable_url", "exact_match",
        "derivative_rule", "net_new_evidence_object_count", "record_sha256",
    ],
    "metadata-search-lead-ledger-v2.tsv": [
        "metadata_lead_id", "canonical_doi", "candidate_source_ids_json", "title",
        "stable_url", "query_occurrence_count", "query_ids_json", "pair_ids_json",
        "rank_distribution_json", "abstract_bearing_occurrence_count", "has_link",
        "review_status", "support_status", "rights_and_access_status",
        "required_next_action", "record_sha256",
    ],
    "parameter-reconciliation-ledger-v2.tsv": [
        "parameter_name", "parameter_class", "authority", "legal_values_json",
        "changes_semantic_identity", "changes_presentation_identity",
        "higher_order_semantic_obligation", "round16a_assumption_status",
        "required_next_action", "source_record_sha256", "record_sha256",
    ],
    "database-discovery-occurrence-ledger-v2.tsv": [
        "database_occurrence_id", "database_family_id", "selector_branch", "stable_row_locator",
        "source_record_url", "matched_fields_json", "matched_node_edge_loci_json",
        "raw_participant_labels_json", "participant_sense_ids_json",
        "excluded_rejected_matches_json", "arity", "metadata_status", "support_status",
        "rights_status", "selector_version", "database_sha256", "record_sha256",
    ],
    "database-discovery-family-ledger-v2.tsv": [
        "database_family_id", "candidate_id", "participant_set_key", "participant_sense_ids_json",
        "canonical_labels_json", "arity", "database_occurrence_count",
        "database_occurrence_ids_json", "selector_branches_json", "metadata_status",
        "evidence_review_status", "global_coherence_status", "product_eligibility",
        "association_identity_frozen", "record_sha256",
    ],
    "database-search-document-rejection-ledger-v2.tsv": [
        "rejection_id", "stable_row_locator", "search_doc_id", "document_type",
        "object_or_capture_id", "matched_labels_json", "arity", "rejection_reason",
        "net_trigger_occurrence_count", "database_sha256", "record_sha256",
    ],
    "database-capture-locus-control-ledger-v2.tsv": [
        "control_id", "stable_row_locator", "capture_id", "source_record_url",
        "eligible_matches_json", "excluded_rejected_matches_json", "matched_fields_json",
        "control_class", "exclusion_reason", "net_trigger_occurrence_count",
        "support_status", "database_sha256", "record_sha256",
    ],
    "checkpoint003-receipt-import-failure-disposition-v2.tsv": [
        "failure_id", "failed_import_path", "canonical_import_path", "failed_import_sha256",
        "canonical_import_sha256", "byte_identical", "manifest_status", "preservation_status",
        "failure_cause", "corrective_action", "record_sha256",
    ],
    "recursive-gap-ledger-checkpoint004-v2.tsv": [
        "gap_id", "last_reviewed_checkpoint", "gap", "severity", "status",
        "checkpoint004_evidence", "authority_dependency", "required_next_action",
    ],
}

DEFERRED_SURFACE_IDS = {
    "SURF-R09-001", "SURF-R09-005", "SURF-R10-001", "SURF-R10-004", "SURF-R10-007",
    "SURF-R11-001", "SURF-R11-002", "SURF-R11-003", "SURF-R12-001", "SURF-R12-002",
    "SURF-R12-003", "SURF-R12-004", "SURF-R13-001", "SURF-R13-003", "SURF-R13-005",
    "SURF-R13-006", "SURF-R14-004", "SURF-R16A-003", "SURF-R16A-005", "SURF-R16A-010",
    "SURF-DB-001",
}
EXPECTED_CLOSURE_KEYS = {
    "PAIR_ASSOCIATION_CLOSURE",
    "HIGHER_ORDER_ASSOCIATION_CLOSURE",
    "GLOBAL_COMPOSITION_COHERENCE_CLOSURE",
    "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE",
    "COMPUTATIONAL_SPACE_CLOSURE",
    "FUNCTION3_CLOSURE",
}

DEFERRED_CONTROL_CONTRACTS: dict[str, tuple[Path, str, str, str, str]] = {
    "SURF-R09-001": (R9_SOURCES, "source_id", "CANONICALIZE_DOI_THEN_ISBN_THEN_STABLE_URL_THEN_AUTHOR_YEAR_TITLE", "BIBLIOGRAPHIC_IDENTITY", "ZERO_EMISSION_RIGHTS_AND_TEXT_REVIEW_BLOCKED"),
    "SURF-R09-005": (R9_CONTROLS, "candidate_id", "FINAL_DECISION_AND_ADVERSARIAL_STATUS_EXACT", "REJECTED_OR_DEFERRED_SENSE_CONTROL", "ZERO_EMISSION_CONTROL_ONLY"),
    "SURF-R10-001": (R10_SOURCES, "source_id", "CANONICALIZE_DOI_THEN_ISBN_THEN_STABLE_URL_THEN_AUTHOR_YEAR_TITLE", "BIBLIOGRAPHIC_IDENTITY", "ZERO_EMISSION_RIGHTS_AND_TEXT_REVIEW_BLOCKED"),
    "SURF-R10-004": (R10_PAIR_MATRIX, "ordered_pair_key", "EXACT_ORDERED_PAIR_DECISION_WITHOUT_GROUP_LIFT", "PAIR_PROJECTION_CONTROL", "ZERO_EMISSION_PAIR_CONTROL_ONLY"),
    "SURF-R10-007": (R10_GAPS, "gap_id", "NO_PUBLIC_LABEL_AND_FUTURE_GATE_EXACT", "OPEN_VOCABULARY_GAP_CONTROL", "ZERO_EMISSION_OPEN_GAP"),
    "SURF-R11-001": (R11_CONSTRAINTS, "constraint_id", "STATUS_MUST_EQUAL_PASS", "SOFTWARE_MODEL_CONSTRAINT_CONTROL", "ZERO_EMISSION_NON_HISTORICAL_CONTROL"),
    "SURF-R11-002": (R11_FIXTURES, "fixture_id", "SYNTHETIC_TRUE_AND_PRODUCTION_EXPORTABLE_FALSE", "SYNTHETIC_FIXTURE_CONTROL", "ZERO_EMISSION_SYNTHETIC_CONTROL"),
    "SURF-R11-003": (R11_ADVERSARIAL, "case_id", "EXPECTED_EQUALS_ACTUAL_AND_STATUS_PASS", "ADVERSARIAL_EXPECTATION_CONTROL", "ZERO_EMISSION_TEST_CONTROL"),
    "SURF-R12-001": (R12_CANDIDATES, "candidateId", "PACKAGE_AND_CANDIDATE_ACTIVE_FALSE", "INACTIVE_UNARY_RESEARCH_CANDIDATE", "ZERO_EMISSION_UNARY_INQUIRY_CONTROL"),
    "SURF-R12-002": (R12_PAIR_QUESTIONS, "pair_question_id", "PAIR_DECISION_CANNOT_EMIT_GROUP", "PAIR_INQUIRY_CONTROL", "ZERO_EMISSION_PAIR_CONTROL_ONLY"),
    "SURF-R12-003": (R12_SEEDS, "seed_id", "HISTORICAL_CLAIM_FALSE_AND_PUBLIC_EXPORTABLE_FALSE", "RESEARCH_ONLY_SEED_CONTROL", "ZERO_EMISSION_RENDERABILITY_NON_SUPPORTING"),
    "SURF-R12-004": (R12_INSTANCES, "instance_id", "RESEARCH_PREVIEW_ONLY_TRUE", "RESEARCH_PREVIEW_INSTANCE_CONTROL", "ZERO_EMISSION_RENDERABILITY_NON_SUPPORTING"),
    "SURF-R13-001": (R13_SOURCES, "source_id", "CANONICALIZE_DOI_THEN_ISBN_THEN_STABLE_URL_THEN_AUTHOR_YEAR_TITLE", "BIBLIOGRAPHIC_IDENTITY", "ZERO_EMISSION_RIGHTS_AND_TEXT_REVIEW_BLOCKED"),
    "SURF-R13-003": (R13_PAIRS, "pair_id", "ACTIVATION_CANDIDATE_FALSE_AND_NO_GROUP_LIFT", "GOVERNED_PAIR_DECISION_CONTROL", "ZERO_EMISSION_PAIR_CONTROL_ONLY"),
    "SURF-R13-005": (R13_ACTIVATION, "candidateId", "PACKAGE_ACTIVE_FALSE_REQUIRES_HUMAN_AND_SEPARATE_DECISION", "INACTIVE_ACTIVATION_PACKAGE_CONTROL", "ZERO_EMISSION_INACTIVE_PACKAGE"),
    "SURF-R13-006": (R13_HUMAN_REVIEW, "review_unit_id", "REVIEWER_ANSWER_STATUS_EXACT_NOT_COMPLETED", "PENDING_EXTERNAL_HUMAN_REVIEW_BLOCKER", "ZERO_EMISSION_HUMAN_AUTHORITY_BLOCKED"),
    "SURF-R14-004": (R14_NARY_RESULTS, "fixture_id", "EXACT_FIXTURE_ALIAS_EXPECTED_EQUALS_ACTUAL_PASS_PRODUCTION_FALSE", "SYNTHETIC_NARY_RESULT_ALIAS_CONTROL", "ZERO_EMISSION_SYNTHETIC_RESULT_ALIAS"),
    "SURF-R16A-003": (R16A_EVIDENCE, "ledger_id", "R14_EXACT_ALIAS_OR_QUERY_RESULT_EXACT_ALIAS", "ROUND16A_PAIR_EVIDENCE_DERIVATIVE", "ZERO_NET_EMISSION_ALL_ROWS_ALIASED"),
    "SURF-R16A-005": (R16A_PARAMETERS, "parameter_name", "SEMANTIC_IDENTITY_FLAG_DETERMINES_HIGHER_ORDER_OBLIGATION", "ROUND16A_PARAMETER_RECONCILIATION", "ZERO_EMISSION_PARAMETER_CONTROL"),
    "SURF-R16A-010": (R16A_QUERIES, "query_id", "FIVE_RESULTS_PER_QUERY_EXACT_ALIAS_AND_ZERO_ACCEPTED", "METADATA_QUERY_CONTROL", "ZERO_EMISSION_METADATA_ONLY"),
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}:{sha256_text(canonical_json(value))}"


def read_tsv(path: Path) -> list[dict[str, str]]:
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[Any]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def normalized_identifier(value: str) -> str:
    result = value.strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if result.startswith(prefix):
            result = result[len(prefix):]
    return result


def normalized_title(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    return " ".join(re.findall(r"[\w]+", decomposed))


def normalized_text(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value or "").casefold()
    return " ".join("".join(character if character.isalnum() else " " for character in folded).split())


def normalized_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc.casefold(), path, parsed.query, ""))


def canonical_source_identity(identifier: str, stable_url: str) -> tuple[str, str]:
    normalized = normalized_identifier(identifier)
    if normalized.startswith("10."):
        return "DOI", normalized
    compact = "".join(character for character in normalized.upper() if character.isdigit() or character == "X")
    if compact and len(compact) in {10, 13}:
        return "ISBN", compact
    return "STABLE_URL", normalized_url(stable_url)


def match_lexicon_fields(
    fields: dict[str, str],
    entries: list[tuple[str, str, str]],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Return longest-first non-overlapping label hits and their resolved senses."""
    matched_fields: dict[str, set[str]] = defaultdict(set)
    senses: dict[str, str] = {}
    for field, raw_value in fields.items():
        text = normalized_text(raw_value)
        occupied: list[tuple[int, int]] = []
        for phrase, label, sense in entries:
            start = 0
            while True:
                location = text.find(phrase, start)
                if location < 0:
                    break
                end = location + len(phrase)
                bounded = (
                    (location == 0 or text[location - 1] == " ")
                    and (end == len(text) or text[end] == " ")
                )
                overlaps = any(location < occupied_end and occupied_start < end for occupied_start, occupied_end in occupied)
                if bounded and not overlaps:
                    occupied.append((location, end))
                    matched_fields[label].add(field)
                    senses[label] = sense
                    break
                start = location + 1
    return (
        {label: sorted(values) for label, values in sorted(matched_fields.items())},
        dict(sorted(senses.items())),
    )


def selector_count(path: Path, selector: str) -> int:
    if selector == "tsv_rows":
        return len(read_tsv(path))
    if selector == "jsonl_rows":
        return len(read_jsonl(path))
    if selector in {"file", "json:file"}:
        return 1
    if selector.startswith("json:"):
        return len(read_json(path)[selector.split(":", 1)[1]])
    raise ValueError(f"unsupported selector: {selector}")


def row_hash_exact(row: dict[str, str], hash_field: str = "record_sha256") -> bool:
    material = {key: value for key, value in row.items() if key != hash_field}
    return row.get(hash_field) == sha256_text(canonical_json(material))


def tsv_header(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle, dialect="excel-tab"))


def id_set_hash(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def is_https(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme.casefold() == "https" and bool(parsed.netloc)


def typed_record_hash_exact(row: dict[str, str], integer_fields: set[str]) -> bool:
    """Validate a full-row record hash after restoring TSV-erased integer types."""
    material: dict[str, Any] = {}
    for key, value in row.items():
        if key == "record_sha256":
            continue
        material[key] = int(value) if key in integer_fields else value
    return row.get("record_sha256") == sha256_text(canonical_json(material))


def canonical_json_fields_exact(rows: Iterable[dict[str, str]]) -> bool:
    for row in rows:
        for key, value in row.items():
            if key.endswith("_json"):
                try:
                    if value != canonical_json(json.loads(value)):
                        return False
                except (TypeError, ValueError, json.JSONDecodeError):
                    return False
    return True


def source_records_for_control(
    repo: Path,
    surface_id: str,
    path: Path,
    ref_field: str,
) -> list[tuple[str, str, dict[str, Any]]]:
    """Independently enumerate one governed source surface's record identities."""
    relative = str(path)
    if surface_id == "SURF-R12-001":
        payload = read_json(repo / path)
        return [
            (row[ref_field], f"{relative}#candidates/{row[ref_field]}", row)
            for row in payload["candidates"]
        ]
    if surface_id == "SURF-R13-005":
        payload = read_json(repo / path)
        rows: list[tuple[str, str, dict[str, Any]]] = []
        for section in (
            "nodeActivationCandidates", "pairCompositionCandidates",
            "inquiryGrammarCandidates", "structuralAnnotationCandidates",
        ):
            for source in payload[section]:
                material = {"package_section": section, **source}
                rows.append((source[ref_field], f"{relative}#{section}/{source[ref_field]}", material))
        return rows
    if surface_id == "SURF-R16A-005":
        return [
            (row[ref_field], f"{relative}#parameters/{row[ref_field]}", row)
            for row in read_json(repo / path)["parameters"]
        ]
    if surface_id == "SURF-R16A-010":
        return [
            (row[ref_field], f"{relative}#query_id={row[ref_field]}", row)
            for row in read_jsonl(repo / path)
        ]
    return [
        (row[ref_field], f"{relative}#{ref_field}={row[ref_field]}", row)
        for row in read_tsv(repo / path)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = repo / RAW_REL
    checks: dict[str, dict[str, Any]] = {}
    failures: list[str] = []

    def require(code: str, condition: bool, detail: Any = None) -> None:
        checks[code] = {"pass": bool(condition), "detail": detail}
        if not condition:
            failures.append(code)

    method_surfaces = read_tsv(repo / METHOD_SURFACES)
    prior_surface_rows = read_tsv(repo / PRIOR_SURFACE_LEDGER)
    prior_occurrences = read_tsv(repo / PRIOR_OCCURRENCES)
    prior_families = read_tsv(repo / PRIOR_FAMILIES)
    crosswalk = read_tsv(repo / PRIOR_CROSSWALK)
    method_by_id = {row["surface_id"]: row for row in method_surfaces}
    prior_surface_by_id = {row["surface_id"]: row for row in prior_surface_rows}
    deferred_rows = [row for row in prior_surface_rows if row["disposition"].startswith("DEFERRED_")]

    require(
        "ORIGINAL_METHOD_SURFACE_PARTITION_EXACT",
        len(method_surfaces) == len(method_by_id) == len(prior_surface_rows) == len(prior_surface_by_id) == 44
        and len(deferred_rows) == len(DEFERRED_SURFACE_IDS) == 21
        and {row["surface_id"] for row in deferred_rows} == DEFERRED_SURFACE_IDS,
    )
    deferred_binding_failures: list[str] = []
    for row in deferred_rows:
        inventory = method_by_id[row["surface_id"]]
        source_path = repo / row["path"]
        exact = (
            row["path"] == inventory["path"]
            and row["record_selector"] == inventory["record_selector"]
            and row["sha256"] == inventory["sha256"] == sha256_file(source_path)
            and int(row["bytes"]) == int(inventory["bytes"]) == source_path.stat().st_size
            and int(row["record_count"])
            == int(inventory["record_count"])
            == selector_count(source_path, row["record_selector"])
            and row["candidate_universe_closure_effect"] == "OPEN"
        )
        if not exact:
            deferred_binding_failures.append(row["surface_id"])
    require(
        "ORIGINAL_21_DEFERRED_SOURCE_BINDINGS_EXACT",
        not deferred_binding_failures,
        deferred_binding_failures,
    )
    require(
        "CHECKPOINT003_BASELINE_COUNTS_EXACT",
        len(prior_occurrences) == 348 and len(prior_families) == 31,
    )

    # Reconstruct the three bibliography surfaces without accepting metadata
    # identity as evidence or deciding redistribution rights.
    bibliography_specs = [
        ("SURF-R09-001", "ROUND9", R9_SOURCES, "doi_isbn", "stable_publisher_url", "publication"),
        ("SURF-R10-001", "ROUND10", R10_SOURCES, "doi_isbn", "stable_publisher_url", "publication"),
        ("SURF-R13-001", "ROUND13", R13_SOURCES, "doi_or_identifier", "stable_url", "venue"),
    ]
    bibliography_records: list[dict[str, Any]] = []
    bibliography_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for surface_id, round_name, relative_path, identifier_field, url_field, venue_field in bibliography_specs:
        for source_row in read_tsv(repo / relative_path):
            identity = canonical_source_identity(source_row[identifier_field], source_row[url_field])
            standardized = {
                "surface_id": surface_id,
                "round": round_name,
                "source_path": str(relative_path),
                "source_record_id": source_row["source_id"],
                "authors": source_row["authors"],
                "year": source_row["year"],
                "title": source_row["title"],
                "venue": source_row[venue_field],
                "identifier": source_row[identifier_field],
                "stable_url": source_row[url_field],
                "identity_kind": identity[0],
                "identity_value": identity[1],
                "source_record_sha256": sha256_text(canonical_json(source_row)),
            }
            bibliography_records.append(standardized)
            bibliography_groups[identity].append(standardized)
    duplicate_member_count = sum(len(rows) - 1 for rows in bibliography_groups.values())
    require(
        "BIBLIOGRAPHY_108_TO_94_IDENTITIES_14_ALIASES",
        len(bibliography_records) == 108
        and len(bibliography_groups) == 94
        and duplicate_member_count == 14,
    )
    require(
        "BIBLIOGRAPHY_MEANINGFUL_IDENTITY_PRECEDENCE",
        Counter(kind for kind, _ in bibliography_groups) == {"DOI": 88, "ISBN": 3, "STABLE_URL": 3},
        Counter(kind for kind, _ in bibliography_groups),
    )

    # Independently prove every non-database local surface is a bounded
    # zero-emission control or an alias/queue surface.
    r9_controls = read_tsv(repo / R9_CONTROLS)
    r10_pairs = read_tsv(repo / R10_PAIR_MATRIX)
    r10_gaps = read_tsv(repo / R10_GAPS)
    r11_constraints = read_tsv(repo / R11_CONSTRAINTS)
    r11_fixtures = read_tsv(repo / R11_FIXTURES)
    r11_adversarial = read_tsv(repo / R11_ADVERSARIAL)
    r12_candidates = read_json(repo / R12_CANDIDATES)
    r12_pairs = read_tsv(repo / R12_PAIR_QUESTIONS)
    r12_seeds = read_tsv(repo / R12_SEEDS)
    r12_instances = read_tsv(repo / R12_INSTANCES)
    r13_pairs = read_tsv(repo / R13_PAIRS)
    r13_activation = read_json(repo / R13_ACTIVATION)
    r13_human = read_tsv(repo / R13_HUMAN_REVIEW)
    r14_nary_results = read_tsv(repo / R14_NARY_RESULTS)
    require(
        "R09_REJECTED_DEFERRED_ROWS_BLOCK_EMISSION",
        len(r9_controls) == 17
        and all(row["adversarial_result"] == "BLOCK" for row in r9_controls)
        and all(row["final_decision"].startswith(("DEFER_", "REJECT_")) for row in r9_controls),
    )
    require(
        "R10_ORDERED_PAIR_MATRIX_HAS_NO_ACTIVE_RULE",
        len(r10_pairs) == 256
        and Counter(row["decision"] for row in r10_pairs)
        == {"REJECT_SELF_RELATION": 16, "UNSUPPORTED_DEFAULT_DENY": 237, "DEFER_DIRECTIONALITY": 2, "DEFER_SINGLE_ATTESTATION": 1}
        and all(row["directionality"] in {"not_authorized", "UNRESOLVED_DEFER"} for row in r10_pairs),
    )
    require(
        "R10_GAPS_CREATE_NO_PUBLIC_LABEL",
        len(r10_gaps) == 6 and all(row["new_public_label_created"] == "false" for row in r10_gaps),
    )
    require(
        "R11_CONSTRAINT_FIXTURE_ADVERSARIAL_CONTROLS_EXACT",
        len(r11_constraints) == 37
        and all(row["status"] == "PASS" for row in r11_constraints)
        and len(r11_fixtures) == 10
        and all(row["synthetic_test_only"] == "true" and row["production_exportable"] == "false" for row in r11_fixtures)
        and len(r11_adversarial) == 20
        and all(row["status"] == "PASS" and row["expected_outcome"] == row["actual_outcome"] for row in r11_adversarial),
    )
    require(
        "R12_INQUIRY_SURFACES_MAX_ARITY_TWO_AND_INACTIVE",
        r12_candidates["active"] is False
        and len(r12_candidates["candidates"]) == 16
        and all(candidate["active"] is False for candidate in r12_candidates["candidates"])
        and len(r12_pairs) == 3
        and all(row["directionality_status"] == "UNRESOLVED_DEFER" for row in r12_pairs)
        and len(r12_seeds) == 5
        and all(len(row["candidate_sense_ids"].split(";")) <= 2 for row in r12_seeds)
        and all(row["historical_claim"] == "false" and row["public_exportable"] == "false" for row in r12_seeds)
        and len(r12_instances) == 5
        and all(int(row["node_count"]) <= 2 and row["activation_state"] == "RESEARCH_CANDIDATE_ONLY" and row["research_preview_only"] == "true" for row in r12_instances),
    )
    activation_children = (
        r13_activation["nodeActivationCandidates"]
        + r13_activation["pairCompositionCandidates"]
        + r13_activation["inquiryGrammarCandidates"]
        + r13_activation["structuralAnnotationCandidates"]
    )
    require(
        "R13_PAIR_ACTIVATION_AND_HUMAN_REVIEW_BLOCKERS_EXACT",
        len(r13_pairs) == 3
        and all(row["activation_candidate"] == "false" for row in r13_pairs)
        and r13_activation["active"] is False
        and r13_activation["requiresExternalHumanReview"] is True
        and r13_activation["requiresSeparateActivationDecision"] is True
        and r13_activation["feedsRealImageCompiler"] is False
        and len(r13_activation["pairCompositionCandidates"]) == 0
        and len(activation_children) == 14
        and all(candidate["active"] is False for candidate in activation_children)
        and len(r13_human) == 36
        and all(row["reviewer_answer_status"] == "NOT_COMPLETED" for row in r13_human),
    )
    require(
        "R14_NARY_RESULTS_SYNTHETIC_NOT_NEW_EMISSIONS",
        len(r14_nary_results) == 6
        and all(row["status"] == "PASS" and row["production_eligible"] == "false" for row in r14_nary_results)
        and Counter(row["actual_result"] for row in r14_nary_results) == {"PASS": 4, "SPLIT": 1, "PRUNED": 1},
    )

    # Round 16A evidence/query rows are aliases of frozen upstream records,
    # never additional evidence objects or association support.
    r14_provenance = {
        row["evidence_id"]: row
        for row in read_tsv(repo / Path("docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv"))
    }
    r16a_evidence = read_tsv(repo / R16A_EVIDENCE)
    accepted_evidence = [row for row in r16a_evidence if row["review_disposition"] == "ACCEPTED_GOVERNED_EVIDENCE"]
    metadata_evidence = [row for row in r16a_evidence if row["review_disposition"] == "REJECTED_METADATA_ONLY_NOT_EVIDENCE"]
    evidence_common_fields = [
        "evidence_channel", "source_id", "source_kind", "creator", "year", "title", "locator",
        "stable_url", "doi", "domain_alignment", "association_context", "source_metadata_verified",
        "evidence_verified",
    ]
    evidence_alias_failures: list[str] = []
    for row in accepted_evidence:
        evidence_id = row["ledger_id"].removeprefix("R16A-")
        source = r14_provenance.get(evidence_id)
        if source is None or any(row[field] != source[field] for field in evidence_common_fields):
            evidence_alias_failures.append(row["ledger_id"])
    require(
        "ROUND16A_61_EVIDENCE_ALIASES_EXACT",
        len(accepted_evidence) == 61 and not evidence_alias_failures,
        evidence_alias_failures[:20],
    )
    require(
        "ROUND16A_2325_METADATA_ROWS_NOT_EVIDENCE",
        len(metadata_evidence) == 2325
        and all(row["evidence_verified"] == "false" and row["supports_active_edge"] == "false" for row in metadata_evidence),
    )
    r16a_queries = read_jsonl(repo / R16A_QUERIES)
    query_results = [
        (query, result)
        for query in r16a_queries
        for result in query["candidate_results"]
    ]
    metadata_by_pair_source = {(row["pair_id"], row["source_id"]): row for row in metadata_evidence}
    query_alias_failures: list[str] = []
    for query, result in query_results:
        ledger = metadata_by_pair_source.get((query["pair_id"], result["candidate_source_id"]))
        exact = (
            ledger is not None
            and ledger["doi"] == result["doi"]
            and ledger["title"] == result["title"]
            and ledger["stable_url"] == result["url"]
            and ledger["review_disposition"] == "REJECTED_METADATA_ONLY_NOT_EVIDENCE"
        )
        if not exact:
            query_alias_failures.append(f"{query['query_id']}:{result['rank']}")
    require(
        "ROUND16A_QUERY_LOG_465_BY_5_ALIASES_EXACT",
        len(r16a_queries) == 465
        and all(query["result_count"] == 5 and not query["accepted_source_ids"] for query in r16a_queries)
        and len(query_results) == 2325
        and not query_alias_failures,
        query_alias_failures[:20],
    )
    metadata_lead_groups: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for query, result in query_results:
        metadata_lead_groups[normalized_identifier(result["doi"])].append((query, result))
    require(
        "METADATA_RESULTS_COLLAPSE_TO_101_NON_SUPPORT_LEADS",
        len(metadata_lead_groups) == 101
        and all(key and key.startswith("10.") for key in metadata_lead_groups)
        and all(result["accepted"] is False for _, result in query_results),
    )

    parameters = read_json(repo / R16A_PARAMETERS)["parameters"]
    require(
        "ROUND16A_18_PARAMETER_CONTROLS_9_SEMANTIC_9_NONSEMANTIC",
        len(parameters) == 18
        and len({row["parameter_name"] for row in parameters}) == 18
        and Counter(row["changes_semantic_identity"] for row in parameters) == {True: 9, False: 9}
        and all(row["changes_presentation_identity"] is True for row in parameters),
    )

    # Reconstruct the frozen-database selector from SQL and the independently
    # derived 53 eligible-label / 52 resolved-sense lexicon.
    eligible_crosswalk = [
        row for row in crosswalk
        if row["disposition"] in {"ACTIVE", "RESEARCH_ONLY", "MERGED_SUPERSEDED"}
        and row["crosswalk_status"] in {"RESOLVED_CANONICAL", "RESOLVED_MERGED_ALIAS"}
    ]
    rejected_crosswalk = [row for row in crosswalk if row["disposition"] == "REJECTED"]
    eligible_lexicon = sorted(
        [
            (normalized_text(row["canonical_label"]), row["canonical_label"], row["canonical_resolution_sense_id"])
            for row in eligible_crosswalk
        ],
        key=lambda value: (-len(value[0]), value[0]),
    )
    rejected_lexicon = sorted(
        [
            (normalized_text(row["canonical_label"]), row["canonical_label"], row["participant_sense_id"])
            for row in rejected_crosswalk
        ],
        key=lambda value: (-len(value[0]), value[0]),
    )
    require(
        "DATABASE_LEXICON_53_LABELS_52_RESOLVED_SENSES",
        len(eligible_lexicon) == 53
        and len({sense for _, _, sense in eligible_lexicon}) == 52
        and next(sense for _, label, sense in eligible_lexicon if label == "cultural adaptation")
        == next(sense for _, label, sense in eligible_lexicon if label == "adaptation"),
    )
    require("FROZEN_DATABASE_HASH_EXACT", sha256_file(repo / DATABASE) == DATABASE_SHA256)

    database = sqlite3.connect(f"file:{repo / DATABASE}?mode=ro", uri=True)
    database.row_factory = sqlite3.Row
    capture_fields = [
        "source_record_url", "source_title", "source_description", "source_notes", "source_subjects"
    ]
    capture_candidates: dict[str, dict[str, Any]] = {}
    for source in database.execute(
        "SELECT capture_id, active_surface_id, capture_status, quality_route, quality_reason, "
        "source_record_url, source_title, source_description, source_notes, source_subjects "
        "FROM capture_records ORDER BY capture_id"
    ):
        fields = {field: source[field] or "" for field in capture_fields}
        matched_fields, label_senses = match_lexicon_fields(fields, eligible_lexicon)
        rejected_fields, _ = match_lexicon_fields(fields, rejected_lexicon)
        resolved_senses = sorted(set(label_senses.values()))
        if len(resolved_senses) >= 3:
            capture_candidates[source["capture_id"]] = {
                "source_record_url": source["source_record_url"],
                "matched_fields": matched_fields,
                "label_senses": label_senses,
                "participant_sense_ids": resolved_senses,
                "rejected_matches": sorted(rejected_fields),
                "governance": {
                    "active_surface_id": source["active_surface_id"],
                    "capture_status": source["capture_status"],
                    "quality_route": source["quality_route"],
                    "quality_reason": source["quality_reason"],
                },
            }
    require(
        "DATABASE_CAPTURE_SIX_LOCUS_CANDIDATES_EXACT",
        set(capture_candidates) == EXPECTED_DATABASE_CAPTURE_IDS | EXPECTED_DATABASE_CAPTURE_CONTROL_IDS,
        sorted(capture_candidates),
    )
    require(
        "DATABASE_CAPTURE_LOCATORS_AND_UNICODE_BOUNDARIES_EXACT",
        all(value["source_record_url"].startswith("https://") for value in capture_candidates.values())
        and normalized_text("μετάφραση — Translation") == "μετάφραση translation"
        and all(
            all(field in capture_fields for fields in value["matched_fields"].values() for field in fields)
            for value in capture_candidates.values()
        ),
    )
    require(
        "DATABASE_CHW_TRANSLATION_AND_WHMZ_CROSS_SECTION_CONTROLS",
        set(capture_candidates) - EXPECTED_DATABASE_CAPTURE_IDS == EXPECTED_DATABASE_CAPTURE_CONTROL_IDS
        and "translation" in capture_candidates["CHWCONTEMP2026V1R0009"]["label_senses"]
        and set(capture_candidates["WHMZTRACE2026R0009"]["label_senses"])
        == {"education", "exhibition", "production"},
    )
    require(
        "DATABASE_AIC_REJECTED_BAUHAUS_MATCH_EXCLUDED",
        all(
            "Bauhaus" in capture_candidates[capture_id]["rejected_matches"]
            for capture_id in {"HISTORICALAICTRACE2026V1R0161", "HISTORICALAICTRACE2026V1R0206"}
        ),
        {capture_id: capture_candidates[capture_id]["rejected_matches"] for capture_id in {"HISTORICALAICTRACE2026V1R0161", "HISTORICALAICTRACE2026V1R0206"}},
    )

    trace_sql = """
        SELECT o.surface_id, o.source_url, o.trace_object_node_id,
               e.edge_id, e.subject_node_id, e.object_node_id, e.edge_label,
               e.review_state, e.prohibited_inference_check,
               e.evidence_url AS edge_evidence_url,
               e.evidence_text AS edge_evidence_text,
               n.node_id, n.node_type, n.label, n.canonical_key,
               n.source_url AS node_source_url, n.evidence AS node_evidence,
               n.evidence_status
          FROM objects AS o
          JOIN object_trace_edges AS ote
            ON ote.surface_id = o.surface_id
          JOIN trace_edges AS e
            ON e.edge_id = ote.edge_id
          JOIN trace_nodes AS n
            ON n.node_id = CASE
                 WHEN e.subject_node_id = o.trace_object_node_id THEN e.object_node_id
                 ELSE e.subject_node_id
               END
         WHERE o.trace_object_node_id IS NOT NULL
           AND o.trace_object_node_id <> ''
           AND o.count_eligible = 1
           AND o.trace_state = 'accepted'
           AND e.review_state = 'accepted'
           AND e.prohibited_inference_check = 'pass'
           AND (e.subject_node_id = o.trace_object_node_id
                OR e.object_node_id = o.trace_object_node_id)
           AND e.evidence_url <> ''
           AND e.evidence_text <> ''
           AND n.source_url <> ''
           AND n.evidence <> ''
         ORDER BY o.surface_id, e.edge_id
    """
    eligible_by_exact_label = {
        normalized_text(label): (label, sense)
        for _, label, sense in eligible_lexicon
    }
    trace_candidates: dict[str, dict[str, Any]] = defaultdict(lambda: {"source_record_url": "", "labels": {}, "loci": []})
    for row in database.execute(trace_sql):
        label_match = eligible_by_exact_label.get(normalized_text(row["label"]))
        if label_match is None:
            continue
        canonical_label, sense = label_match
        record = trace_candidates[row["surface_id"]]
        record["source_record_url"] = row["source_url"]
        record["labels"][canonical_label] = sense
        record["loci"].append({
            "edge_id": row["edge_id"],
            "edge_evidence_url": row["edge_evidence_url"],
            "edge_evidence_text": row["edge_evidence_text"],
            "edge_subject_node_id": row["subject_node_id"],
            "edge_object_node_id": row["object_node_id"],
            "object_node_id": row["trace_object_node_id"],
            "opposite_node_id": row["node_id"],
            "node_type": row["node_type"],
            "node_label": row["label"],
            "node_source_url": row["node_source_url"],
            "node_evidence": row["node_evidence"],
            "node_evidence_status": row["evidence_status"],
        })
    trace_candidates = {
        surface_id: value
        for surface_id, value in trace_candidates.items()
        if len(set(value["labels"].values())) >= 3
    }
    require(
        "DATABASE_TRACE_DIRECT_OPPOSITE_NODE_LOCUS_SET_EXACT",
        set(trace_candidates) == EXPECTED_DATABASE_TRACE_SURFACE_IDS
        and all(len(value["loci"]) == 3 for value in trace_candidates.values())
        and all(set(value["labels"]) == {"advertising", "photography", "typography"} for value in trace_candidates.values())
        and all(value["source_record_url"].startswith("https://") for value in trace_candidates.values())
        and all(
            locus["edge_evidence_url"].startswith("https://")
            and bool(locus["edge_evidence_text"])
            and ((locus["edge_subject_node_id"] == locus["object_node_id"])
                 != (locus["edge_object_node_id"] == locus["object_node_id"]))
            and locus["opposite_node_id"]
            == (
                locus["edge_object_node_id"]
                if locus["edge_subject_node_id"] == locus["object_node_id"]
                else locus["edge_subject_node_id"]
            )
            and locus["node_source_url"].startswith("https://")
            and bool(locus["node_evidence"])
            and locus["node_evidence_status"].startswith(("explicit_", "stable_", "source_verified"))
            for value in trace_candidates.values()
            for locus in value["loci"]
        ),
        sorted(trace_candidates),
    )

    retained_capture_candidates = {
        capture_id: value
        for capture_id, value in capture_candidates.items()
        if capture_id in EXPECTED_DATABASE_CAPTURE_IDS
    }
    database_family_sense_sets = {
        tuple(value["participant_sense_ids"])
        for value in retained_capture_candidates.values()
    } | {
        tuple(sorted(set(value["labels"].values())))
        for value in trace_candidates.values()
    }
    prior_family_sense_sets = {
        tuple(json.loads(row["participant_sense_ids_json"]))
        for row in prior_families
    }
    require(
        "DATABASE_11_OCCURRENCES_4_NEW_FAMILIES_EXACT",
        len(retained_capture_candidates) + len(trace_candidates) == 11
        and len(database_family_sense_sets) == 4
        and database_family_sense_sets.isdisjoint(prior_family_sense_sets),
        {"occurrences": len(retained_capture_candidates) + len(trace_candidates), "families": len(database_family_sense_sets)},
    )

    search_rejection_candidates: dict[str, dict[str, Any]] = {}
    for row in database.execute(
        "SELECT search_doc_id, document_type, object_or_capture_id, title, body "
        "FROM search_documents ORDER BY search_doc_id"
    ):
        matched_fields, label_senses = match_lexicon_fields(
            {"title": row["title"] or "", "body": row["body"] or ""},
            eligible_lexicon,
        )
        resolved_senses = sorted(set(label_senses.values()))
        if len(resolved_senses) >= 3:
            search_rejection_candidates[row["search_doc_id"]] = {
                "document_type": row["document_type"],
                "object_or_capture_id": row["object_or_capture_id"],
                "matched_labels": [
                    next(
                        label for label in sorted(label_senses)
                        if label_senses[label] == sense
                    )
                    for sense in resolved_senses
                ],
                "participant_senses": resolved_senses,
                "arity": len(resolved_senses),
            }
    require(
        "DATABASE_SEARCH_DOCUMENTS_ARE_REJECTION_ONLY",
        len(search_rejection_candidates) == 120
        and all(value["arity"] >= 3 for value in search_rejection_candidates.values()),
        len(search_rejection_candidates),
    )
    database.close()

    # Load every checkpoint-004 artifact only after reconstructing its governed
    # source universe.  The output itself is never used to choose candidates.
    OUTPUT_HEADERS["candidate-trigger-occurrence-ledger-v2.tsv"] = tsv_header(repo / PRIOR_OCCURRENCES)
    OUTPUT_HEADERS["local-candidate-family-ledger-v2.tsv"] = tsv_header(repo / PRIOR_FAMILIES)
    OUTPUT_HEADERS["local-surface-disposition-ledger-v2.tsv"] = tsv_header(repo / PRIOR_SURFACE_LEDGER)
    artifact_rows = {name: read_tsv(raw / name) for name in OUTPUT_HEADERS}
    expected_row_counts = {
        "deferred-surface-execution-ledger-v2.tsv": 21,
        "deferred-zero-emission-control-ledger-v2.tsv": 3411,
        "source-identity-membership-ledger-v2.tsv": 108,
        "source-canonical-rights-queue-v2.tsv": 94,
        "round16a-evidence-alias-ledger-v2.tsv": 61,
        "round16a-query-result-alias-ledger-v2.tsv": 2325,
        "metadata-search-lead-ledger-v2.tsv": 101,
        "parameter-reconciliation-ledger-v2.tsv": 18,
        "database-discovery-occurrence-ledger-v2.tsv": 11,
        "database-discovery-family-ledger-v2.tsv": 4,
        "database-search-document-rejection-ledger-v2.tsv": 120,
        "database-capture-locus-control-ledger-v2.tsv": 2,
        "candidate-trigger-occurrence-ledger-v2.tsv": 359,
        "local-candidate-family-ledger-v2.tsv": 35,
        "local-surface-disposition-ledger-v2.tsv": 44,
        "checkpoint003-receipt-import-failure-disposition-v2.tsv": 1,
        "recursive-gap-ledger-checkpoint004-v2.tsv": 9,
    }
    require(
        "OUTPUT_TSV_HEADERS_AND_ROW_COUNTS_EXACT",
        set(artifact_rows) == set(expected_row_counts)
        and all(tsv_header(raw / name) == OUTPUT_HEADERS[name] for name in artifact_rows)
        and all(len(artifact_rows[name]) == count for name, count in expected_row_counts.items()),
        {name: len(rows) for name, rows in artifact_rows.items()},
    )
    require(
        "OUTPUT_JSON_FIELDS_CANONICAL",
        all(canonical_json_fields_exact(rows) for rows in artifact_rows.values()),
    )

    integer_hash_fields = {
        "deferred-zero-emission-control-ledger-v2.tsv": {"net_trigger_occurrence_count"},
        "source-canonical-rights-queue-v2.tsv": {"member_count"},
        "round16a-evidence-alias-ledger-v2.tsv": {"common_field_count", "net_new_evidence_object_count"},
        "round16a-query-result-alias-ledger-v2.tsv": {"rank", "net_new_evidence_object_count"},
        "metadata-search-lead-ledger-v2.tsv": {"query_occurrence_count", "abstract_bearing_occurrence_count"},
        "database-discovery-occurrence-ledger-v2.tsv": {"arity"},
        "database-discovery-family-ledger-v2.tsv": {"arity", "database_occurrence_count"},
        "database-search-document-rejection-ledger-v2.tsv": {"arity", "net_trigger_occurrence_count"},
        "database-capture-locus-control-ledger-v2.tsv": {"net_trigger_occurrence_count"},
    }
    row_hash_failures: list[str] = []
    for name, int_fields in integer_hash_fields.items():
        for index, row in enumerate(artifact_rows[name]):
            if not typed_record_hash_exact(row, int_fields):
                row_hash_failures.append(f"{name}:{index + 1}")
    for name in (
        "source-identity-membership-ledger-v2.tsv",
        "parameter-reconciliation-ledger-v2.tsv",
        "checkpoint003-receipt-import-failure-disposition-v2.tsv",
    ):
        for index, row in enumerate(artifact_rows[name]):
            if not typed_record_hash_exact(row, set()):
                row_hash_failures.append(f"{name}:{index + 1}")
    for index, row in enumerate(artifact_rows["deferred-surface-execution-ledger-v2.tsv"]):
        execution_material = {
            "surface_id": row["surface_id"],
            "source_sha256": row["source_sha256"],
            "selector_rule": row["selector_rule"],
            "selector_version": row["selector_version"],
            "control_record_count": int(row["control_record_count"]),
            "new_trigger_occurrence_count": int(row["new_trigger_occurrence_count"]),
        }
        if row["record_sha256"] != sha256_text(canonical_json(execution_material)):
            row_hash_failures.append(f"deferred-surface-execution-ledger-v2.tsv:{index + 1}")
    require("OUTPUT_RECORD_HASHES_EXACT", not row_hash_failures, row_hash_failures[:25])

    control_rows = artifact_rows["deferred-zero-emission-control-ledger-v2.tsv"]
    controls_by_key = {(row["surface_id"], row["source_record_ref"]): row for row in control_rows}
    expected_control_records: dict[tuple[str, str], tuple[str, dict[str, Any], tuple[Path, str, str, str, str]]] = {}
    for surface_id, contract in DEFERRED_CONTROL_CONTRACTS.items():
        path, ref_field, _, _, _ = contract
        for source_ref, locator, source_row in source_records_for_control(repo, surface_id, path, ref_field):
            expected_control_records[(surface_id, source_ref)] = (locator, source_row, contract)
    control_binding_failures: list[str] = []
    for key, expected in expected_control_records.items():
        locator, source_row, contract = expected
        path, _, rule, record_class, decision = contract
        row = controls_by_key.get(key)
        expected_id = stable_id(
            "R16B-DEFERRED-CONTROL",
            {"surface_id": key[0], "source_record_ref": key[1], "selector_version": SELECTOR_VERSION},
        )
        if row is None or not (
            row["control_record_id"] == expected_id
            and row["source_path"] == str(path)
            and row["source_record_locator"] == locator
            and row["selector_rule"] == rule
            and row["record_class"] == record_class
            and row["emission_decision"] == decision
            and row["net_trigger_occurrence_count"] == "0"
            and row["source_record_sha256"] == sha256_text(canonical_json(source_row))
            and bool(row["alias_or_blocker_ref"])
            and bool(row["authority_dependency"])
            and bool(row["notes"])
        ):
            control_binding_failures.append(f"{key[0]}:{key[1]}")
    require(
        "ZERO_EMISSION_CONTROL_UNIVERSE_ROW_EXACT",
        len(expected_control_records) == 3411
        and len(controls_by_key) == len(control_rows) == 3411
        and set(controls_by_key) == set(expected_control_records)
        and not control_binding_failures,
        control_binding_failures[:25],
    )

    membership_rows = artifact_rows["source-identity-membership-ledger-v2.tsv"]
    membership_by_source = {
        (row["surface_id"], row["source_record_id"]): row for row in membership_rows
    }
    evidence_alias_rows = artifact_rows["round16a-evidence-alias-ledger-v2.tsv"]
    evidence_alias_by_ledger = {row["round16a_ledger_id"]: row for row in evidence_alias_rows}
    query_alias_rows = artifact_rows["round16a-query-result-alias-ledger-v2.tsv"]
    query_alias_by_ledger = {row["round16a_ledger_id"]: row for row in query_alias_rows}
    query_aliases_by_query: dict[str, list[str]] = defaultdict(list)
    for row in query_alias_rows:
        query_aliases_by_query[row["query_id"]].append(row["alias_id"])
    alias_control_failures: list[str] = []
    for key, row in controls_by_key.items():
        surface_id, source_ref = key
        if surface_id in {"SURF-R09-001", "SURF-R10-001", "SURF-R13-001"}:
            membership = membership_by_source.get(key)
            if membership is None or row["alias_or_blocker_ref"] != membership["canonical_source_id"]:
                alias_control_failures.append(f"{surface_id}:{source_ref}")
        elif surface_id == "SURF-R16A-003":
            expected_alias = (
                evidence_alias_by_ledger.get(source_ref) or query_alias_by_ledger.get(source_ref)
            )
            if expected_alias is None or row["alias_or_blocker_ref"] != expected_alias["alias_id"]:
                alias_control_failures.append(f"{surface_id}:{source_ref}")
        elif surface_id == "SURF-R16A-010":
            expected_ids = sorted(query_aliases_by_query[source_ref])
            try:
                actual_ids = json.loads(row["alias_or_blocker_ref"])
            except json.JSONDecodeError:
                actual_ids = []
            if actual_ids != expected_ids or len(actual_ids) != 5:
                alias_control_failures.append(f"{surface_id}:{source_ref}")
    require(
        "ZERO_EMISSION_ALIAS_AND_BLOCKER_LINKS_EXACT",
        not alias_control_failures,
        alias_control_failures[:25],
    )

    execution_rows = artifact_rows["deferred-surface-execution-ledger-v2.tsv"]
    execution_by_id = {row["surface_id"]: row for row in execution_rows}
    output_controls_by_surface = Counter(row["surface_id"] for row in control_rows)
    alias_members_by_surface = Counter(
        row["surface_id"] for row in membership_rows if row["membership_role"] == "CROSS_ROUND_ALIAS"
    )
    execution_binding_failures: list[str] = []
    for surface_id in DEFERRED_SURFACE_IDS:
        row = execution_by_id.get(surface_id)
        inventory = method_by_id[surface_id]
        if row is None:
            execution_binding_failures.append(surface_id)
            continue
        expected_control_count = (
            122 if surface_id == "SURF-DB-001" else output_controls_by_surface[surface_id]
        )
        expected_alias_count = alias_members_by_surface[surface_id]
        if surface_id == "SURF-R14-004":
            expected_alias_count = 6
        elif surface_id == "SURF-R16A-003":
            expected_alias_count = 2386
        elif surface_id == "SURF-R16A-010":
            expected_alias_count = 2325
        expected_leads = 11 if surface_id == "SURF-DB-001" else (101 if surface_id == "SURF-R16A-010" else 0)
        expected_occurrences = 11 if surface_id == "SURF-DB-001" else 0
        expected_families = 4 if surface_id == "SURF-DB-001" else 0
        exact = (
            row["round"] == inventory["round"]
            and row["source_path"] == inventory["path"]
            and row["source_sha256"] == inventory["sha256"]
            and row["record_selector"] == inventory["record_selector"]
            and int(row["input_record_count"]) == int(inventory["record_count"])
            and row["selector_version"] == SELECTOR_VERSION
            and int(row["control_record_count"]) == expected_control_count
            and int(row["alias_record_count"]) == expected_alias_count
            and int(row["metadata_lead_count"]) == expected_leads
            and int(row["new_trigger_occurrence_count"]) == expected_occurrences
            and int(row["new_candidate_family_count"]) == expected_families
            and row["execution_disposition"].startswith("SELECTOR_ACCOUNTED_")
            and bool(row["authority_dependency"])
            and bool(row["required_next_action"])
        )
        if surface_id != "SURF-DB-001":
            exact = exact and row["selector_rule"] == DEFERRED_CONTROL_CONTRACTS[surface_id][2]
        else:
            exact = exact and row["selector_rule"] == f"{DATABASE_SQL_VERSION};{NORMALIZATION_VERSION}"
        if not exact:
            execution_binding_failures.append(surface_id)
    require(
        "DEFERRED_SURFACE_EXECUTION_21_ROW_EXACT",
        len(execution_by_id) == 21
        and set(execution_by_id) == DEFERRED_SURFACE_IDS
        and not execution_binding_failures,
        execution_binding_failures,
    )

    v2_surface_rows = artifact_rows["local-surface-disposition-ledger-v2.tsv"]
    v2_surface_by_id = {row["surface_id"]: row for row in v2_surface_rows}
    db_output_occurrences = artifact_rows["database-discovery-occurrence-ledger-v2.tsv"]
    v2_surface_failures: list[str] = []
    for surface_id, row in v2_surface_by_id.items():
        inventory = method_by_id.get(surface_id)
        if inventory is None or any(
            row[field] != inventory[field]
            for field in ("round", "path", "record_selector", "record_count", "bytes", "sha256")
        ):
            v2_surface_failures.append(surface_id)
            continue
        if row["disposition"].startswith("DEFERRED_") or "OPEN" not in row["candidate_universe_closure_effect"]:
            v2_surface_failures.append(surface_id)
            continue
        if surface_id in DEFERRED_CONTROL_CONTRACTS:
            expected_ids = {
                control["control_record_id"] for control in control_rows if control["surface_id"] == surface_id
            }
            if set(json.loads(row["matched_input_ids_json"])) != expected_ids:
                v2_surface_failures.append(surface_id)
        elif surface_id == "SURF-DB-001":
            expected_ids = {item["database_occurrence_id"] for item in db_output_occurrences}
            if set(json.loads(row["matched_input_ids_json"])) != expected_ids or row["trigger_occurrence_count"] != "11":
                v2_surface_failures.append(surface_id)
    require(
        "ALL_44_METHOD_SURFACES_SELECTOR_ACCOUNTED_WITH_BLOCKERS_OPEN",
        len(v2_surface_by_id) == 44
        and set(v2_surface_by_id) == set(method_by_id)
        and not v2_surface_failures
        and Counter(row["disposition"] for row in v2_surface_rows) == {
            "SELECTOR_ACCOUNTED_CHECKPOINT003_INPUT": 22,
            "SELECTOR_ACCOUNTED_DATABASE_DISCOVERY_ONLY": 1,
            "SELECTOR_ACCOUNTED_HUMAN_REVIEW_BLOCKED": 1,
            "SELECTOR_ACCOUNTED_METADATA_SEARCH_BLOCKED": 1,
            "SELECTOR_ACCOUNTED_RIGHTS_BLOCKED": 3,
            "SELECTOR_ACCOUNTED_ZERO_HIGHER_ORDER_EMISSION": 16,
        },
        v2_surface_failures,
    )

    bibliography_by_source = {
        (row["surface_id"], row["source_record_id"]): row for row in bibliography_records
    }
    bibliography_membership_failures: list[str] = []
    canonical_members: dict[str, list[dict[str, str]]] = defaultdict(list)
    for key, source in bibliography_by_source.items():
        row = membership_by_source.get(key)
        if row is None:
            bibliography_membership_failures.append(f"{key[0]}:{key[1]}")
            continue
        expected_kind = source["identity_kind"]
        if expected_kind == "STABLE_URL":
            parsed = urlsplit(source["stable_url"])
            expected_value = (parsed.hostname or "").casefold() + re.sub(r"/+", "/", parsed.path).rstrip("/")
        else:
            expected_value = source["identity_value"]
        expected_canonical_id = stable_id("R16B-SOURCE", f"{expected_kind}:{expected_value}")
        expected_membership_id = stable_id(
            "R16B-SOURCE-MEMBERSHIP",
            {"surface_id": key[0], "source_record_id": key[1]},
        )
        exact = (
            row["membership_id"] == expected_membership_id
            and row["round"] == source["round"]
            and row["source_path"] == source["source_path"]
            and row["canonical_source_id"] == expected_canonical_id
            and row["canonical_identity_kind"] == expected_kind
            and row["canonical_identity_value"] == expected_value
            and row["authors"] == source["authors"]
            and row["year"] == source["year"]
            and row["title"] == source["title"]
            and row["venue"] == source["venue"]
            and row["doi_isbn_or_identifier"] == source["identifier"]
            and row["stable_url"] == source["stable_url"]
            and row["source_record_sha256"] == source["source_record_sha256"]
            and row["rights_review_status"] == "PENDING_RIGHTS_AND_ACCESS_REVIEW"
            and row["evidence_use_status"] == "BIBLIOGRAPHIC_IDENTITY_ONLY_NOT_ASSOCIATION_EVIDENCE"
        )
        if not exact:
            bibliography_membership_failures.append(f"{key[0]}:{key[1]}")
        canonical_members[row["canonical_source_id"]].append(row)
    rights_rows = artifact_rows["source-canonical-rights-queue-v2.tsv"]
    rights_by_id = {row["canonical_source_id"]: row for row in rights_rows}
    rights_failures: list[str] = []
    for canonical_id, members in canonical_members.items():
        row = rights_by_id.get(canonical_id)
        ordered = sorted(members, key=lambda item: (item["round"], item["source_path"], item["source_record_id"]))
        representative = ordered[0]
        expected_member_ids = [f"{item['surface_id']}:{item['source_record_id']}" for item in ordered]
        roles_exact = all(
            member["membership_role"] == ("CANONICAL_REPRESENTATIVE" if index == 0 else "CROSS_ROUND_ALIAS")
            and member["representative_source_record_id"] == representative["source_record_id"]
            for index, member in enumerate(ordered)
        )
        if row is None or not (
            int(row["member_count"]) == len(ordered)
            and json.loads(row["member_ids_json"]) == expected_member_ids
            and row["representative_surface_id"] == representative["surface_id"]
            and row["representative_source_path"] == representative["source_path"]
            and row["representative_source_record_id"] == representative["source_record_id"]
            and row["rights_review_status"] == "PENDING"
            and row["text_access_status"] == "NOT_REVIEWED"
            and row["locator_review_status"] == "NOT_REVIEWED"
            and row["association_evidence_status"] == "NOT_EVIDENCE_METADATA_IDENTITY_ONLY"
            and bool(row["required_next_action"])
            and roles_exact
        ):
            rights_failures.append(canonical_id)
    require(
        "BIBLIOGRAPHY_MEMBERSHIP_AND_RIGHTS_QUEUE_ROW_EXACT",
        len(bibliography_by_source) == len(membership_by_source) == 108
        and not bibliography_membership_failures
        and len(canonical_members) == len(rights_by_id) == 94
        and set(canonical_members) == set(rights_by_id)
        and not rights_failures
        and Counter(row["membership_role"] for row in membership_rows)
        == {"CANONICAL_REPRESENTATIVE": 94, "CROSS_ROUND_ALIAS": 14},
        {"membership": bibliography_membership_failures[:20], "rights": rights_failures[:20]},
    )

    evidence_alias_failures = []
    accepted_by_ledger = {row["ledger_id"]: row for row in accepted_evidence}
    for ledger_id, source in accepted_by_ledger.items():
        row = evidence_alias_by_ledger.get(ledger_id)
        if row is None or not (
            row["alias_id"] == stable_id("R16B-R16A-EVIDENCE-ALIAS", ledger_id)
            and row["round14_evidence_id"] == ledger_id.removeprefix("R16A-")
            and row["pair_id"] == source["pair_id"]
            and row["source_id"] == source["source_id"]
            and int(row["common_field_count"]) == len(evidence_common_fields) == 13
            and json.loads(row["common_fields_json"]) == evidence_common_fields
            and row["exact_match"] == "true"
            and row["net_new_evidence_object_count"] == "0"
        ):
            evidence_alias_failures.append(ledger_id)
    require(
        "ROUND16A_EVIDENCE_ALIAS_OUTPUT_61_ROW_EXACT",
        len(evidence_alias_by_ledger) == 61
        and set(evidence_alias_by_ledger) == set(accepted_by_ledger)
        and not evidence_alias_failures,
        evidence_alias_failures[:20],
    )

    query_alias_by_key = {(row["query_id"], int(row["rank"])): row for row in query_alias_rows}
    query_output_failures: list[str] = []
    for query, result in query_results:
        key = (query["query_id"], int(result["rank"]))
        row = query_alias_by_key.get(key)
        ledger = metadata_by_pair_source[(query["pair_id"], result["candidate_source_id"])]
        expected_alias_id = stable_id(
            "R16B-R16A-QUERY-ALIAS",
            {"query_id": query["query_id"], "candidate_source_id": result["candidate_source_id"]},
        )
        if row is None or not (
            row["alias_id"] == expected_alias_id
            and row["pair_id"] == query["pair_id"]
            and row["candidate_source_id"] == result["candidate_source_id"]
            and row["round16a_ledger_id"] == ledger["ledger_id"]
            and row["doi"] == result["doi"]
            and row["title"] == result["title"]
            and row["stable_url"] == result["url"]
            and row["exact_match"] == "true"
            and row["net_new_evidence_object_count"] == "0"
        ):
            query_output_failures.append(f"{key[0]}:{key[1]}")
    require(
        "ROUND16A_QUERY_ALIAS_OUTPUT_2325_ROW_EXACT",
        len(query_alias_by_key) == 2325
        and len({row["alias_id"] for row in query_alias_rows}) == 2325
        and not query_output_failures,
        query_output_failures[:20],
    )

    metadata_output_rows = artifact_rows["metadata-search-lead-ledger-v2.tsv"]
    metadata_output_by_doi = {row["canonical_doi"]: row for row in metadata_output_rows}
    metadata_output_failures: list[str] = []
    for doi, occurrences_for_doi in metadata_lead_groups.items():
        row = metadata_output_by_doi.get(doi)
        representative = min(
            occurrences_for_doi,
            key=lambda item: (int(item[1]["rank"]), item[0]["query_id"]),
        )[1]
        expected_ranks = dict(sorted(Counter(str(item[1]["rank"]) for item in occurrences_for_doi).items()))
        if row is None or not (
            row["metadata_lead_id"] == stable_id("R16B-METADATA-LEAD", f"DOI:{doi}")
            and json.loads(row["candidate_source_ids_json"])
            == sorted({item[1]["candidate_source_id"] for item in occurrences_for_doi})
            and row["title"] == representative["title"]
            and row["stable_url"] == representative["url"]
            and int(row["query_occurrence_count"]) == len(occurrences_for_doi)
            and json.loads(row["query_ids_json"]) == sorted({item[0]["query_id"] for item in occurrences_for_doi})
            and json.loads(row["pair_ids_json"]) == sorted({item[0]["pair_id"] for item in occurrences_for_doi})
            and json.loads(row["rank_distribution_json"]) == expected_ranks
            and int(row["abstract_bearing_occurrence_count"])
            == sum(bool(item[1].get("abstract")) for item in occurrences_for_doi)
            and row["has_link"] == ("true" if any(item[1].get("links") for item in occurrences_for_doi) else "false")
            and row["review_status"] == "METADATA_ONLY_TEXT_NOT_REVIEWED"
            and row["support_status"] == "NOT_ASSOCIATION_EVIDENCE"
            and row["rights_and_access_status"] == "PENDING_LAWFUL_ACCESS_AND_RIGHTS_REVIEW"
        ):
            metadata_output_failures.append(doi)
    require(
        "METADATA_101_LEADS_OUTPUT_ROW_EXACT",
        set(metadata_output_by_doi) == set(metadata_lead_groups)
        and not metadata_output_failures
        and sum(int(row["abstract_bearing_occurrence_count"]) for row in metadata_output_rows) == 139
        and sum(row["has_link"] == "true" for row in metadata_output_rows) == 42,
        metadata_output_failures[:20],
    )

    parameter_output_rows = artifact_rows["parameter-reconciliation-ledger-v2.tsv"]
    parameter_output_by_name = {row["parameter_name"]: row for row in parameter_output_rows}
    parameter_output_failures: list[str] = []
    for parameter in parameters:
        row = parameter_output_by_name.get(parameter["parameter_name"])
        semantic = bool(parameter["changes_semantic_identity"])
        if row is None or not (
            row["parameter_class"] == parameter["class"]
            and row["authority"] == parameter["authority"]
            and json.loads(row["legal_values_json"]) == parameter["legal_values"]
            and row["changes_semantic_identity"] == ("true" if semantic else "false")
            and row["changes_presentation_identity"] == "true"
            and row["higher_order_semantic_obligation"] == ("true" if semantic else "false")
            and row["source_record_sha256"] == sha256_text(canonical_json(parameter))
            and bool(row["required_next_action"])
        ):
            parameter_output_failures.append(parameter["parameter_name"])
    require(
        "PARAMETER_18_ROWS_9_OBLIGATIONS_OUTPUT_EXACT",
        set(parameter_output_by_name) == {row["parameter_name"] for row in parameters}
        and not parameter_output_failures
        and Counter(row["higher_order_semantic_obligation"] for row in parameter_output_rows)
        == {"true": 9, "false": 9},
        parameter_output_failures,
    )

    def labels_in_sense_order(label_senses: dict[str, str], senses: list[str]) -> list[str]:
        by_sense: dict[str, str] = {}
        for label in sorted(label_senses):
            by_sense.setdefault(label_senses[label], label)
        return [by_sense[sense] for sense in senses]

    expected_database_loci: dict[str, dict[str, Any]] = {}
    for capture_id, value in retained_capture_candidates.items():
        senses = value["participant_sense_ids"]
        fields_by_name: dict[str, list[str]] = defaultdict(list)
        for label, fields in value["matched_fields"].items():
            for field in fields:
                fields_by_name[field].append(label)
        matched_fields_output: dict[str, Any] = {
            field: sorted(labels) for field, labels in sorted(fields_by_name.items())
        }
        matched_fields_output["_capture_governance"] = value["governance"]
        locator = f"sqlite:capture_records:capture_id={capture_id}"
        expected_database_loci[locator] = {
            "selector_branch": "CAPTURE_RECORD_BOUNDED_FIELD_LEXICAL_DISCOVERY",
            "source_record_url": value["source_record_url"],
            "matched_fields": matched_fields_output,
            "loci": [],
            "labels": labels_in_sense_order(value["label_senses"], senses),
            "senses": senses,
            "excluded": value["rejected_matches"],
        }
    for surface_id, value in trace_candidates.items():
        senses = sorted(set(value["labels"].values()))
        visible_loci = sorted(
            [
                {
                    "edge_evidence_url": locus["edge_evidence_url"],
                    "edge_id": locus["edge_id"],
                    "node_evidence_status": locus["node_evidence_status"],
                    "node_label": locus["node_label"],
                    "node_source_url": locus["node_source_url"],
                    "opposite_node_id": locus["opposite_node_id"],
                }
                for locus in value["loci"]
            ],
            key=lambda item: (item["edge_id"], item["opposite_node_id"]),
        )
        locator = f"sqlite:objects+object_trace_edges:surface_id={surface_id}"
        expected_database_loci[locator] = {
            "selector_branch": "DIRECT_OPPOSITE_OBJECT_ACCEPTED_TRACE_ENDPOINT_DISCOVERY",
            "source_record_url": value["source_record_url"],
            "matched_fields": {},
            "loci": visible_loci,
            "labels": labels_in_sense_order(value["labels"], senses),
            "senses": senses,
            "excluded": [],
        }

    db_occurrences_by_locator = {row["stable_row_locator"]: row for row in db_output_occurrences}
    db_occurrence_failures: list[str] = []
    for locator, expected in expected_database_loci.items():
        row = db_occurrences_by_locator.get(locator)
        senses = expected["senses"]
        set_key = sha256_text(canonical_json(senses))
        occurrence_material = {
            "selector_branch": expected["selector_branch"],
            "stable_row_locator": locator,
            "participant_sense_ids": senses,
            "selector_version": SELECTOR_VERSION,
            "database_sha256": DATABASE_SHA256,
        }
        if row is None or not (
            row["database_occurrence_id"] == stable_id("R16B-DB-OCC", occurrence_material)
            and row["database_family_id"] == f"R16B-DB-FAMILY:{set_key}"
            and row["selector_branch"] == expected["selector_branch"]
            and row["source_record_url"] == expected["source_record_url"]
            and is_https(row["source_record_url"])
            and json.loads(row["matched_fields_json"]) == expected["matched_fields"]
            and json.loads(row["matched_node_edge_loci_json"]) == expected["loci"]
            and json.loads(row["raw_participant_labels_json"]) == expected["labels"]
            and json.loads(row["participant_sense_ids_json"]) == senses
            and json.loads(row["excluded_rejected_matches_json"]) == expected["excluded"]
            and int(row["arity"]) == len(senses)
            and row["metadata_status"] == "METADATA_OR_LEXICAL_DISCOVERY_ONLY_PENDING_BOUNDED_SENSE_REVIEW"
            and row["support_status"] == "NOT_ASSOCIATION_EVIDENCE"
            and row["rights_status"] == "PENDING_SOURCE_TEXT_RIGHTS_AND_ACCESS_REVIEW"
            and row["selector_version"] == SELECTOR_VERSION
            and row["database_sha256"] == DATABASE_SHA256
        ):
            db_occurrence_failures.append(locator)
    require(
        "DATABASE_DISCOVERY_11_OCCURRENCE_OUTPUT_ROW_EXACT",
        len(expected_database_loci) == len(db_occurrences_by_locator) == 11
        and set(expected_database_loci) == set(db_occurrences_by_locator)
        and not db_occurrence_failures,
        db_occurrence_failures,
    )
    require(
        "DATABASE_OUTPUT_RETAINS_AIC_REJECTED_MATCH_WITHOUT_PARTICIPANT_PROJECTION",
        all(
            json.loads(db_occurrences_by_locator[f"sqlite:capture_records:capture_id={capture_id}"]["excluded_rejected_matches_json"])
            == ["Bauhaus"]
            and all(
                sense not in json.loads(db_occurrences_by_locator[f"sqlite:capture_records:capture_id={capture_id}"]["participant_sense_ids_json"])
                for sense in [row["participant_sense_id"] for row in rejected_crosswalk if row["canonical_label"] == "Bauhaus"]
            )
            for capture_id in {"HISTORICALAICTRACE2026V1R0161", "HISTORICALAICTRACE2026V1R0206"}
        ),
    )

    db_family_rows = artifact_rows["database-discovery-family-ledger-v2.tsv"]
    db_family_by_senses = {
        tuple(json.loads(row["participant_sense_ids_json"])): row for row in db_family_rows
    }
    expected_db_by_senses: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in db_output_occurrences:
        expected_db_by_senses[tuple(json.loads(row["participant_sense_ids_json"]))].append(row)
    db_family_failures: list[str] = []
    for senses, occurrences_for_family in expected_db_by_senses.items():
        row = db_family_by_senses.get(senses)
        set_key = sha256_text(canonical_json(list(senses)))
        occurrence_ids = sorted(item["database_occurrence_id"] for item in occurrences_for_family)
        branches = sorted({item["selector_branch"] for item in occurrences_for_family})
        label_variants = {item["raw_participant_labels_json"] for item in occurrences_for_family}
        if row is None or not (
            row["participant_set_key"] == set_key
            and row["database_family_id"] == f"R16B-DB-FAMILY:{set_key}"
            and row["candidate_id"] == f"R16B-LOCAL-FAMILY:{set_key}"
            and int(row["arity"]) == len(senses)
            and int(row["database_occurrence_count"]) == len(occurrences_for_family)
            and json.loads(row["database_occurrence_ids_json"]) == occurrence_ids
            and json.loads(row["selector_branches_json"]) == branches
            and len(label_variants) == 1
            and row["canonical_labels_json"] in label_variants
            and row["evidence_review_status"] == "NOT_STARTED"
            and row["global_coherence_status"] == "NOT_REVIEWED"
            and row["product_eligibility"] == "INELIGIBLE_PENDING_GOVERNED_REVIEW"
            and row["association_identity_frozen"] == "false"
        ):
            db_family_failures.append(set_key)
    require(
        "DATABASE_DISCOVERY_4_FAMILY_OUTPUT_ROW_EXACT",
        len(db_family_by_senses) == len(expected_db_by_senses) == 4
        and set(db_family_by_senses) == set(expected_db_by_senses)
        and not db_family_failures,
        db_family_failures,
    )

    capture_control_rows = artifact_rows["database-capture-locus-control-ledger-v2.tsv"]
    capture_control_by_id = {row["capture_id"]: row for row in capture_control_rows}
    capture_control_failures: list[str] = []
    for capture_id in EXPECTED_DATABASE_CAPTURE_CONTROL_IDS:
        source = capture_candidates[capture_id]
        row = capture_control_by_id.get(capture_id)
        senses = source["participant_sense_ids"]
        fields_by_name: dict[str, list[str]] = defaultdict(list)
        for label, fields in source["matched_fields"].items():
            for field in fields:
                fields_by_name[field].append(label)
        expected_fields: dict[str, Any] = {
            field: sorted(labels) for field, labels in sorted(fields_by_name.items())
        }
        expected_fields["_capture_governance"] = source["governance"]
        expected_class = (
            "LEXICAL_AMBIGUITY_CONTROL" if capture_id == "CHWCONTEMP2026V1R0009"
            else "CROSS_SECTION_LOCUS_CONFLICT_CONTROL"
        )
        required_reason_tokens = (
            {"translation", "unresolved"} if capture_id == "CHWCONTEMP2026V1R0009"
            else {"unrelated", "sections", "bounded locus"}
        )
        if row is None or not (
            row["control_id"] == stable_id("R16B-DB-CAPTURE-CONTROL", capture_id)
            and row["stable_row_locator"] == f"sqlite:capture_records:capture_id={capture_id}"
            and row["source_record_url"] == source["source_record_url"]
            and is_https(row["source_record_url"])
            and json.loads(row["eligible_matches_json"]) == labels_in_sense_order(source["label_senses"], senses)
            and json.loads(row["excluded_rejected_matches_json"]) == source["rejected_matches"]
            and json.loads(row["matched_fields_json"]) == expected_fields
            and row["control_class"] == expected_class
            and all(token in row["exclusion_reason"] for token in required_reason_tokens)
            and row["net_trigger_occurrence_count"] == "0"
            and row["support_status"] == "NOT_ASSOCIATION_EVIDENCE"
            and row["database_sha256"] == DATABASE_SHA256
        ):
            capture_control_failures.append(capture_id)
    require(
        "DATABASE_CHW_WHMZ_CONTROL_OUTPUT_ROW_EXACT",
        set(capture_control_by_id) == EXPECTED_DATABASE_CAPTURE_CONTROL_IDS
        and not capture_control_failures,
        capture_control_failures,
    )

    search_output_rows = artifact_rows["database-search-document-rejection-ledger-v2.tsv"]
    search_output_by_id = {row["search_doc_id"]: row for row in search_output_rows}
    search_output_failures: list[str] = []
    for search_id, expected in search_rejection_candidates.items():
        row = search_output_by_id.get(search_id)
        if row is None or not (
            row["rejection_id"] == stable_id("R16B-DB-SEARCH-CONTROL", search_id)
            and row["stable_row_locator"] == f"sqlite:search_documents:search_doc_id={search_id}"
            and row["document_type"] == expected["document_type"]
            and row["object_or_capture_id"] == expected["object_or_capture_id"]
            and json.loads(row["matched_labels_json"]) == expected["matched_labels"]
            and int(row["arity"]) == expected["arity"]
            and row["rejection_reason"]
            == "SEARCH_DOCUMENT_BODY_IS_PROJECT_GENERATED_MIXED_TEXT_AND_CANNOT_SUPPLY_SOURCE_BOUNDED_ASSOCIATION_DISCOVERY"
            and row["net_trigger_occurrence_count"] == "0"
            and row["database_sha256"] == DATABASE_SHA256
        ):
            search_output_failures.append(search_id)
    require(
        "DATABASE_SEARCH_DOCUMENT_120_REJECTION_OUTPUT_ROW_EXACT",
        set(search_output_by_id) == set(search_rejection_candidates)
        and not search_output_failures,
        search_output_failures[:20],
    )

    v2_occurrence_rows = artifact_rows["candidate-trigger-occurrence-ledger-v2.tsv"]
    prior_occurrence_by_id = {row["trigger_occurrence_id"]: row for row in prior_occurrences}
    v2_occurrence_by_id = {row["trigger_occurrence_id"]: row for row in v2_occurrence_rows}
    prior_occurrence_loss = [
        occurrence_id for occurrence_id, row in prior_occurrence_by_id.items()
        if v2_occurrence_by_id.get(occurrence_id) != row
    ]
    new_occurrence_rows = [
        row for row in v2_occurrence_rows if row["trigger_occurrence_id"] not in prior_occurrence_by_id
    ]
    require(
        "MERGED_OCCURRENCE_LEDGER_PRESERVES_348_AND_ADDS_11",
        len(prior_occurrence_by_id) == 348
        and len(v2_occurrence_by_id) == len(v2_occurrence_rows) == 359
        and len(new_occurrence_rows) == 11
        and not prior_occurrence_loss,
        prior_occurrence_loss[:20],
    )
    db_by_record_hash = {row["record_sha256"]: row for row in db_output_occurrences}
    new_occurrence_failures: list[str] = []
    for row in new_occurrence_rows:
        try:
            content_hashes = json.loads(row["content_hashes_json"])
            record_refs = json.loads(row["input_record_refs_json"])
            senses = json.loads(row["participant_sense_ids_json"])
            raw_senses = json.loads(row["raw_participant_sense_ids_json"])
        except json.JSONDecodeError:
            new_occurrence_failures.append(row["trigger_occurrence_id"])
            continue
        database_row = db_by_record_hash.get(content_hashes[0]) if len(content_hashes) == 1 else None
        scope_material = {
            "source_path": str(DATABASE),
            "record_refs": record_refs,
            "locator": row["locator"],
            "content_hashes": content_hashes,
        }
        identity_material = {
            "trigger_class": row["trigger_class"],
            "source_path": str(DATABASE),
            "record_refs": record_refs,
            "locator": row["locator"],
            "content_hashes": content_hashes,
            "raw_participant_sense_ids": raw_senses,
            "selector_version": SELECTOR_VERSION,
        }
        occurrence_material = {key: value for key, value in row.items() if key != "occurrence_sha256"}
        exact = database_row is not None and (
            row["trigger_occurrence_id"] == stable_id("R16B-TRIGGER-OCC", identity_material)
            and row["trigger_id"] == "TRG-009"
            and row["trigger_class"] == database_row["selector_branch"]
            and row["input_surface_id"] == "SURF-DB-001"
            and row["source_path"] == str(DATABASE)
            and record_refs == [database_row["stable_row_locator"]]
            and row["locator"] == database_row["source_record_url"]
            and json.loads(row["raw_participant_labels_json"])
            == json.loads(database_row["raw_participant_labels_json"])
            and raw_senses == senses == json.loads(database_row["participant_sense_ids_json"])
            and row["participant_set_key"] == sha256_text(canonical_json(senses))
            and row["scope_hypothesis_id"] == stable_id("R16B-SCOPE-HYP", scope_material)
            and row["polarity"] == "METADATA_LEXICAL_DISCOVERY_ONLY"
            and row["emission_kind"] == "DATABASE_DISCOVERY_REVIEW_FAMILY"
            and row["candidate_id"] == f"R16B-LOCAL-FAMILY:{row['participant_set_key']}"
            and row["incidental_or_excluded_labels_json"] == database_row["excluded_rejected_matches_json"]
            and row["selector_version"] == SELECTOR_VERSION
            and row["occurrence_sha256"] == sha256_text(canonical_json(occurrence_material))
        )
        if not exact:
            new_occurrence_failures.append(row["trigger_occurrence_id"])
    require(
        "DATABASE_TO_MERGED_OCCURRENCE_RECONCILIATION_EXACT",
        not new_occurrence_failures
        and {row["content_hashes_json"] for row in new_occurrence_rows}
        == {canonical_json([row["record_sha256"]]) for row in db_output_occurrences},
        new_occurrence_failures,
    )

    v2_family_rows = artifact_rows["local-candidate-family-ledger-v2.tsv"]
    prior_family_by_id = {row["candidate_id"]: row for row in prior_families}
    v2_family_by_id = {row["candidate_id"]: row for row in v2_family_rows}
    prior_family_loss = [
        candidate_id for candidate_id, row in prior_family_by_id.items()
        if v2_family_by_id.get(candidate_id) != row
    ]
    new_family_rows = [row for row in v2_family_rows if row["candidate_id"] not in prior_family_by_id]
    require(
        "MERGED_FAMILY_LEDGER_PRESERVES_31_AND_ADDS_4",
        len(prior_family_by_id) == 31
        and len(v2_family_by_id) == len(v2_family_rows) == 35
        and len(new_family_rows) == 4
        and not prior_family_loss,
        prior_family_loss,
    )
    canonical_crosswalk_by_sense = {
        row["canonical_resolution_sense_id"]: row
        for row in crosswalk
        if row["participant_sense_id"] == row["canonical_resolution_sense_id"]
    }
    new_family_failures: list[str] = []
    new_occurrences_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in new_occurrence_rows:
        new_occurrences_by_candidate[row["candidate_id"]].append(row)
    for row in new_family_rows:
        senses = json.loads(row["participant_sense_ids_json"])
        occurrences_for_family = new_occurrences_by_candidate[row["candidate_id"]]
        occurrence_ids = sorted(item["trigger_occurrence_id"] for item in occurrences_for_family)
        dispositions = Counter(canonical_crosswalk_by_sense[sense]["disposition"] for sense in senses)
        content_material = {
            "candidate_id": row["candidate_id"],
            "participant_sense_ids": senses,
            "scope_resolution_status": "UNRESOLVED_MAY_SPLIT_BY_CASE",
            "occurrence_ids": occurrence_ids,
        }
        exact = (
            row["candidate_object_kind"] == "LOCAL_PARTICIPANT_SET_REVIEW_FAMILY_NOT_ASSOCIATION"
            and row["participant_set_key"] == sha256_text(canonical_json(senses))
            and row["candidate_id"] == f"R16B-LOCAL-FAMILY:{row['participant_set_key']}"
            and int(row["arity"]) == len(senses)
            and int(row["occurrence_count"]) == len(occurrences_for_family)
            and json.loads(row["trigger_occurrence_ids_json"]) == occurrence_ids
            and json.loads(row["trigger_ids_json"]) == ["TRG-009"]
            and json.loads(row["emission_kinds_json"]) == ["DATABASE_DISCOVERY_REVIEW_FAMILY"]
            and int(row["active_participant_count"]) == dispositions["ACTIVE"]
            and int(row["research_only_participant_count"]) == dispositions["RESEARCH_ONLY"]
            and int(row["rejected_participant_count"]) == 0 == dispositions["REJECTED"]
            and row["scope_resolution_status"] == "UNRESOLVED_MAY_SPLIT_BY_CASE"
            and row["case_resolution_status"] == "UNRESOLVED"
            and row["participant_eligibility"] == "REVIEW_ELIGIBLE_NOT_VALIDATED"
            and row["lifecycle_state"] == "DISCOVERED"
            and row["proposed_disposition"] == "PENDING_GOVERNED_REVIEW"
            and row["evidence_review_status"] == "NOT_STARTED"
            and row["global_coherence_status"] == "NOT_REVIEWED"
            and row["product_eligibility"] == "INELIGIBLE_PENDING_GOVERNED_REVIEW"
            and row["association_identity_frozen"] == "False"
            and row["family_content_sha256"] == sha256_text(canonical_json(content_material))
        )
        if not exact:
            new_family_failures.append(row["candidate_id"])
    require(
        "DATABASE_TO_MERGED_FAMILY_RECONCILIATION_EXACT_NO_REJECTED_PARTICIPANTS",
        set(new_occurrences_by_candidate) == {row["candidate_id"] for row in new_family_rows}
        and not new_family_failures,
        new_family_failures,
    )
    require(
        "ZERO_ACTIVE_ASSOCIATIONS_OR_PREMATURE_FROZEN_IDENTITIES",
        all(row["candidate_object_kind"] != "ASSOCIATION" for row in v2_family_rows)
        and all(row["association_identity_frozen"].casefold() == "false" for row in v2_family_rows)
        and all(row["evidence_review_status"] == "NOT_STARTED" for row in v2_family_rows)
        and all(row["global_coherence_status"] == "NOT_REVIEWED" for row in v2_family_rows),
    )

    receipt_failure_row = artifact_rows["checkpoint003-receipt-import-failure-disposition-v2.tsv"][0]
    failed_receipt_path = repo / receipt_failure_row["failed_import_path"]
    canonical_receipt_path = repo / receipt_failure_row["canonical_import_path"]
    require(
        "CHECKPOINT003_FAILED_IMPORT_PRESERVED_AND_HASH_BOUND",
        receipt_failure_row["failure_id"] == "CHECKPOINT004-FAILED-IMPORT-001"
        and failed_receipt_path.exists()
        and canonical_receipt_path.exists()
        and sha256_file(failed_receipt_path) == receipt_failure_row["failed_import_sha256"]
        and sha256_file(canonical_receipt_path) == receipt_failure_row["canonical_import_sha256"]
        and receipt_failure_row["failed_import_sha256"] == receipt_failure_row["canonical_import_sha256"]
        and receipt_failure_row["byte_identical"] == "true"
        and "PRESERVED" in receipt_failure_row["preservation_status"]
        and "UNMANIFESTED" in receipt_failure_row["manifest_status"],
    )
    gap_rows = artifact_rows["recursive-gap-ledger-checkpoint004-v2.tsv"]
    require(
        "RECURSIVE_GAP_LEDGER_RETAINS_ALL_CLOSURE_BLOCKERS",
        [row["gap_id"] for row in gap_rows] == [f"GAP-{index:03d}" for index in range(1, 10)]
        and all(row["last_reviewed_checkpoint"] == "CHECKPOINT-004" for row in gap_rows)
        and Counter(row["severity"] for row in gap_rows) == {"CLOSURE_BLOCKING": 8, "AUDIT": 1}
        and sum(row["status"].startswith("OPEN") for row in gap_rows) >= 6
        and all(bool(row["authority_dependency"]) and bool(row["required_next_action"]) for row in gap_rows),
    )

    census = read_json(repo / V2_CENSUS)
    v1_census = read_json(repo / (RAW_REL / "local-candidate-census-v1.json"))
    expected_candidate_rows = [
        {
            "candidate_id": row["candidate_id"],
            "candidate_object_kind": row["candidate_object_kind"],
            "participant_set_key": row["participant_set_key"],
            "participant_sense_ids": json.loads(row["participant_sense_ids_json"]),
            "canonical_labels": json.loads(row["canonical_labels_json"]),
            "arity": int(row["arity"]),
            "occurrence_count": int(row["occurrence_count"]),
            "trigger_occurrence_ids": json.loads(row["trigger_occurrence_ids_json"]),
            "trigger_ids": json.loads(row["trigger_ids_json"]),
            "order_semantics": row["order_semantics"],
            "role_semantics": row["role_semantics"],
            "scope_resolution_status": row["scope_resolution_status"],
            "case_resolution_status": row["case_resolution_status"],
            "participant_eligibility": row["participant_eligibility"],
            "lifecycle_state": row["lifecycle_state"],
            "proposed_disposition": row["proposed_disposition"],
            "evidence_review_status": row["evidence_review_status"],
            "global_coherence_status": row["global_coherence_status"],
            "product_eligibility": row["product_eligibility"],
            "association_identity_frozen": row["association_identity_frozen"].casefold() == "true",
            "family_content_sha256": row["family_content_sha256"],
        }
        for row in v2_family_rows
    ]
    expected_trigger_distribution = dict(sorted(Counter(row["trigger_class"] for row in v2_occurrence_rows).items()))
    expected_arity_distribution = dict(
        sorted(Counter(row["arity"] for row in v2_family_rows).items(), key=lambda item: int(item[0]))
    )
    expected_surface_distribution = dict(sorted(Counter(row["disposition"] for row in v2_surface_rows).items()))
    require(
        "CENSUS_FULL_LEDGER_RECONCILIATION_EXACT",
        census["format"] == "trace-round16b-local-candidate-census-v2"
        and census["source_sha"] == "5419770959bdb8998b693fb2275b47e29b92367c"
        and census["parent_checkpoint_sha"] == CHECKPOINT_003_SHA
        and census["selector_version"] == SELECTOR_VERSION
        and census["normalization_version"] == NORMALIZATION_VERSION
        and census["database_selector_sql_version"] == DATABASE_SQL_VERSION
        and census["database_sha256"] == DATABASE_SHA256
        and census["method_surface_count"] == census["selector_accounted_method_surface_count"] == 44
        and census["deferred_method_surface_count"] == 0
        and census["deferred_surface_execution_count"] == 21
        and census["zero_emission_control_record_count"] == 3411
        and census["source_bibliography_row_count"] == 108
        and census["canonical_source_identity_count"] == 94
        and census["cross_round_source_alias_count"] == 14
        and census["round16a_evidence_alias_count"] == 61
        and census["round16a_query_result_alias_count"] == 2325
        and census["metadata_search_lead_count"] == 101
        and census["parameter_reconciliation_count"] == 18
        and census["semantic_parameter_obligation_count"] == 9
        and census["database_discovery_occurrence_count"] == 11
        and census["database_discovery_family_count"] == 4
        and census["database_capture_locus_control_count"] == 2
        and census["database_search_document_rejection_count"] == 120
        and census["trigger_occurrence_count"] == 359
        and census["local_candidate_family_count"] == 35
        and census["trigger_occurrence_distribution"] == expected_trigger_distribution
        and census["candidate_arity_distribution"] == expected_arity_distribution
        and census["method_surface_disposition_distribution"] == expected_surface_distribution
        and census["candidates"] == expected_candidate_rows,
    )
    require(
        "CENSUS_SEMANTIC_BOUNDARY_AND_BLOCKERS_REMAIN_OPEN",
        "not governed associations" in census["semantic_boundary"]
        and "UNCLOSED" in census["candidate_universe_status"]
        and "OPEN" in census["open_blockers"]["prior_global_coherence_and_product_reconciliation"]
        and census["open_blockers"]["canonical_source_rights_and_text_review_count"] == 94
        and census["open_blockers"]["metadata_search_lead_count"] == 101
        and census["open_blockers"]["database_discovery_locus_count"] == 11
        and census["open_blockers"]["external_human_review_unit_count"] == 36
        and census["open_blockers"]["semantic_parameter_obligation_count"] == 9
        and census["open_blockers"]["unresolved_candidate_family_count"] == 35
        and census["active_candidate_family_count"] == 0
        and census["active_pending_review_count"] == 0
        and census["evidence_review_complete_candidate_count"] == 0
        and census["global_coherence_pass_candidate_count"] == 0
        and census["open_participant_resolution_queue_count"] == v1_census["open_participant_resolution_queue_count"] == 10
        and census["isolated_active_vocabulary_count"] == v1_census["isolated_active_vocabulary_count"] == 5
        and census["prior_row_exact_reconciliation_object_count"] == v1_census["prior_row_exact_reconciliation_object_count"] == 32135,
    )
    require(
        "ALL_CLOSURE_FLAGS_EXACTLY_FALSE",
        set(census["closure"]) == EXPECTED_CLOSURE_KEYS
        and all(value is False for value in census["closure"].values()),
        census["closure"],
    )

    receipt = read_json(repo / V2_RECEIPT)
    expected_receipt_counts = {
        "active_facts_added": 0,
        "bibliography_memberships": 108,
        "canonical_source_identities": 94,
        "database_capture_controls": 2,
        "database_discovery_families": 4,
        "database_discovery_occurrences": 11,
        "database_search_document_controls": 120,
        "deferred_surface_execution": 21,
        "merged_candidate_families": 35,
        "merged_trigger_occurrences": 359,
        "metadata_search_leads": 101,
        "method_surface_deferred": 0,
        "method_surface_selector_accounted": 44,
        "parameter_rows": 18,
        "round16a_evidence_aliases": 61,
        "round16a_query_result_aliases": 2325,
        "semantic_parameter_obligations": 9,
        "source_aliases": 14,
        "zero_emission_controls": 3411,
    }
    require(
        "BUILD_RECEIPT_AUTHORITY_COUNTS_AND_NON_MUTATION_EXACT",
        receipt["format"] == "trace-round16b-deferred-surface-build-receipt-v2"
        and receipt["authorized_source_sha"] == "5419770959bdb8998b693fb2275b47e29b92367c"
        and receipt["parent_checkpoint_sha"] == CHECKPOINT_003_SHA
        and receipt["selector_version"] == SELECTOR_VERSION
        and receipt["normalization_version"] == NORMALIZATION_VERSION
        and receipt["database_selector_sql_version"] == DATABASE_SQL_VERSION
        and receipt["counts"] == expected_receipt_counts
        and receipt["closure"] == census["closure"]
        and receipt["history_rewritten"] is False
        and receipt["force_push_used"] is False
        and receipt["activation_performed"] is False
        and receipt["closure_claimed"] is False,
    )
    selector_contract = receipt["selector_contract"]
    require(
        "RECEIPT_DATABASE_SELECTOR_CONTRACT_HASHES_AND_SAFETY_EXACT",
        selector_contract["eligible_lexical_label_count"] == 53
        and selector_contract["eligible_resolved_participant_sense_count"] == 52
        and selector_contract["capture_selector_sql_sha256"] == sha256_text(selector_contract["capture_selector_sql"])
        and selector_contract["trace_selector_sql_sha256"] == sha256_text(selector_contract["trace_selector_sql"])
        and selector_contract["search_document_control_sql_sha256"] == sha256_text(selector_contract["search_document_control_sql"])
        and "source_record_url" in selector_contract["capture_selector_sql"]
        and "object_trace_edges" in selector_contract["trace_selector_sql"]
        and "e.subject_node_id = o.trace_object_node_id" in selector_contract["trace_selector_sql"]
        and "e.evidence_url" in selector_contract["trace_selector_sql"]
        and "e.evidence_text" in selector_contract["trace_selector_sql"]
        and "n.evidence" in selector_contract["trace_selector_sql"]
        and "n.source_url" in selector_contract["trace_selector_sql"]
        and "n.evidence_status LIKE" in selector_contract["trace_selector_sql"]
        and "non-overlapping Unicode token boundaries" in selector_contract["normalization"],
    )
    expected_surface_hashes = {surface_id: method_by_id[surface_id]["sha256"] for surface_id in DEFERRED_SURFACE_IDS}
    immutable_paths = [PRIOR_OCCURRENCES, PRIOR_FAMILIES, PRIOR_SURFACE_LEDGER, RAW_REL / "local-candidate-census-v1.json", PRIOR_CROSSWALK]
    expected_immutable_hashes = {str(path): sha256_file(repo / path) for path in immutable_paths}
    require(
        "RECEIPT_INPUT_MANIFEST_EXACT",
        receipt["input_manifest"]["executed_surface_sha256"] == expected_surface_hashes
        and receipt["input_manifest"]["immutable_checkpoint003_artifact_sha256"] == expected_immutable_hashes
        and receipt["input_manifest"]["failed_checkpoint003_receipt_import_sha256"] == sha256_file(failed_receipt_path)
        and receipt["input_manifest"]["canonical_checkpoint003_receipt_sha256"] == sha256_file(canonical_receipt_path)
        and receipt["frozen_sqlite"] == {
            "path": str(DATABASE), "bytes": (repo / DATABASE).stat().st_size, "sha256": DATABASE_SHA256
        },
    )
    expected_output_paths = {name: raw / name for name in OUTPUT_HEADERS}
    expected_output_paths["local-candidate-census-v2.json"] = repo / V2_CENSUS
    expected_output_paths[str(RESEARCH_NOTE)] = repo / RESEARCH_NOTE
    expected_output_hashes = {name: sha256_file(path) for name, path in expected_output_paths.items()}
    require(
        "RECEIPT_19_OUTPUT_KEY_SET_AND_FILE_HASHES_EXACT",
        len(expected_output_hashes) == 19
        and receipt["output_sha256"] == dict(sorted(expected_output_hashes.items())),
        {"expected": sorted(expected_output_hashes), "actual": sorted(receipt["output_sha256"])},
    )
    note_text = (repo / RESEARCH_NOTE).read_text(encoding="utf-8")
    require(
        "RESEARCH_NOTE_REPORTS_NON_SUPPORT_AND_NON_CLOSURE",
        "Active facts added: 0" in note_text
        and "Evidence-complete families: 0" in note_text
        and "Global-coherence passes: 0" in note_text
        and "All six closure flags remain false" in note_text,
    )

    allowlist = read_json(repo / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json")
    verifier_relative = "scripts/trace_round16b/verify_deferred_surface_census.py"
    require(
        "VERIFIER_ACTIVE_ALLOWLIST_REGISTRATION_EXACT",
        allowlist["scriptCount"] == len(allowlist["scripts"])
        and sum(row["path"] == verifier_relative for row in allowlist["scripts"]) == 1
        and next(row for row in allowlist["scripts"] if row["path"] == verifier_relative)["decision"] == "KEEP_ACTIVE",
    )

    verifier_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(verifier_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(verifier_tree)
        if isinstance(node, ast.ImportFrom)
    }
    require(
        "VERIFIER_DOES_NOT_IMPORT_GENERATOR",
        "build_deferred_surface_census" not in imports
        and "scripts.trace_round16b.build_deferred_surface_census" not in imports,
    )

    result = {
        "format": "trace-round16b-deferred-surface-independent-verification-v1",
        "verifier_path": "scripts/trace_round16b/verify_deferred_surface_census.py",
        "verifier_sha256": sha256_file(Path(__file__)),
        "generator_imported": False,
        "authorized_source_sha": "5419770959bdb8998b693fb2275b47e29b92367c",
        "parent_checkpoint_sha": CHECKPOINT_003_SHA,
        "verified_build_receipt_path": str(V2_RECEIPT),
        "verified_build_receipt_sha256": sha256_file(repo / V2_RECEIPT),
        "verified_census_sha256": sha256_file(repo / V2_CENSUS),
        "verified_output_sha256": dict(sorted(expected_output_hashes.items())),
        "verified_counts": expected_receipt_counts,
        "closure": census["closure"],
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "failure_count": len(failures),
        "failure_codes": failures,
        "checks": checks,
    }
    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "check_count", "failure_count", "failure_codes")}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
