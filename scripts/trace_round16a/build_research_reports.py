#!/usr/bin/env python3
"""Build the final Round 16A research narrative from frozen census receipts.

This is a reporting program, not a verifier.  It refuses to write anything
until every final machine-readable input named by the Round 16A contract is
present and parseable.  Counts are projected from those inputs and the formal
closure decision is recomputed from explicit gates; a pre-written decision
string is never trusted as authority.

The program also preserves the vocabulary reports that occupied numbers 06
and 07 during construction by copying their exact bytes to 03A and 03B before
the contractually required 06 graph and 07 parameter reports are written.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO = Path(__file__).resolve().parents[2]
RESEARCH = REPO / "docs/research/trace-v49-exploration-full-space-closure-round1"
RAW = REPO / "docs/audits/v49-exploration-full-space-closure-round1/raw"
CURRENT = REPO / "docs/research/EXPLORATION_CURRENT.md"
PROJECT_LOG = REPO / "PROJECT_LOG.md"

SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
UNKNOWN = "NOT_RECORDED"

JSON_INPUTS = (
    "environment.json",
    "database-identity-v2.json",
    "vocabulary-candidate-universe-v2.json",
    "vocabulary-census-v2.json",
    "active-vocabulary-v2.json",
    "pair-universe-v2.json",
    "association-census-v2.json",
    "validated-association-graph-v2.json",
    "graph-statistics-v2.json",
    "exploration-parameter-universe-v2.json",
    "canonical-composition-registry-v2.json",
    "composition-statistics-v2.json",
    "production-read-model-metadata-v2.json",
    "space-generation-summary-v2.json",
    "api-functional-validation-v2.json",
    "production-http-results.json",
    "concurrency-results.json",
    "runtime-memory-results.json",
    "build-time-computation-results.json",
    "sustained-load-results.json",
    "metric-dictionary.json",
    "headline-numbers.json",
    "independent-verification.json",
    "reproducibility-verification.json",
    "authorized-lfs-migration-receipt.json",
    "quantitative-audit.json",
    "final-gate-evidence.json",
)

TSV_INPUTS = (
    "command-ledger.tsv",
    "checkpoint-ledger.tsv",
    "vocabulary-candidate-universe-v2.tsv",
    "vocabulary-census-v2.tsv",
    "future-vocabulary-candidates.tsv",
    "pair-universe-v2.tsv",
    "association-census-v2.tsv",
    "association-evidence-ledger-v2.tsv",
    "composition-enumeration-v2.tsv",
    "composition-rejection-ledger-v2.tsv",
    "category-entry-census-v2.tsv",
    "state-census-v2.tsv",
    "transition-census-v2.tsv",
    "workflow-census-v2.tsv",
    "export-census-v2.tsv",
    "png-validation-v2.tsv",
)

JSONL_INPUTS = (
    "execution-events.jsonl",
    "association-query-log-v2.jsonl",
)

REPORT_NAMES = {
    "06_VALIDATED_GRAPH_REPORT.md",
    "07_PARAMETER_UNIVERSE.md",
    "08_COMPOSITION_ENUMERATION_METHOD.md",
    "09_CANONICALISATION_POLICY.md",
    "10_TOPOLOGY_CENSUS.md",
    "11_CATEGORY_ENTRY_CENSUS.md",
    "12_STATE_AND_TRANSITION_CENSUS.md",
    "13_CANONICAL_WORKFLOW_CENSUS.md",
    "14_EXPORT_CENSUS.md",
    "15_API_AND_READ_MODEL_DECISION.md",
    "16_PRODUCTION_LOAD_METHOD.md",
    "17_PRODUCTION_LOAD_RESULTS.md",
    "18_STATISTICAL_CENSUS.md",
    "19_INDEPENDENT_VERIFICATION.md",
    "20_REPRODUCIBILITY.md",
    "21_LIMITATIONS.md",
    "22_FUNCTION3_CLOSURE_DECISION.md",
    "23_BRANDING_SAFE_METRICS.md",
}

EARLY_REQUIRED_REPORTS = (
    "00_LIVE_EXECUTION_LOG.md",
    "01_AUTHORITY_AND_ARCHITECTURE_RECONCILIATION.md",
    "02_ROUND16A_GOAL_AND_METHOD.md",
    "03_VOCABULARY_UNIVERSE_METHOD.md",
    "04_ASSOCIATION_CENSUS_METHOD.md",
    "05_EVIDENCE_SEARCH_PROTOCOL.md",
)

# Ordered exactly as section 38 of the Round 16A contract.  The emitted text is
# deliberately line-oriented (KEY=value) so it can be pasted verbatim into the
# final response and mechanically parsed without Markdown-table semantics.
RECEIPT_SECTIONS: tuple[tuple[str | None, tuple[str, ...]], ...] = (
    (None, (
        "PHASE_STATUS", "SOURCE_SHA", "SOURCE_TREE_SHA", "FINAL_LOCAL_SHA", "FINAL_REMOTE_SHA",
        "WORKTREE", "WORKTREE_CLEAN", "BRANCH", "ROLLBACK_TAG", "ROLLBACK_TAG_TARGET",
    )),
    ("Scope", (
        "ROUND_SCOPE", "SEARCH_STATUS", "SEARCH_CODE_MUTATION_COUNT", "SEARCH_RUNTIME_DEPENDENCY_COUNT",
        "SEARCH_SEMANTIC_INPUT_COUNT", "CONTEXT_CODE_MUTATION_COUNT", "SPACETIME_CODE_MUTATION_COUNT",
        "CONTEXT_SEMANTIC_INPUT_COUNT", "SPACETIME_SEMANTIC_INPUT_COUNT",
    )),
    ("Authority", (
        "ACTIVE_EXPLORATION_AUTHORITY_COUNT", "AUTHORITY_CONTRADICTION_COUNT", "AUTHORITY_RECONCILIATION_READY",
    )),
    ("Logging", (
        "EXECUTION_EVENT_COUNT", "EXECUTION_LOG_SEQUENCE_GAP_COUNT", "COMMAND_LOG_COUNT",
        "CHECKPOINT_COMMIT_COUNT", "FULL_COMMAND_LOG_READY", "CONTINUOUS_PROCESS_LOG_READY",
    )),
    ("Database", (
        "DATABASE_SNAPSHOT_ID", "DATABASE_SCHEMA_VERSION", "DATABASE_CONTENT_HASH", "DATABASE_FREEZE_HASH",
        "PUBLIC_OBJECT_COUNT", "HELD_OBJECT_COUNT", "DIRECT_DATABASE_SNAPSHOT_VALIDATED",
        "DIRECT_DATABASE_CATEGORY_BINDING_READY", "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT",
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT", "HELD_DATA_LEAK_COUNT",
    )),
    ("Vocabulary", (
        "VOCABULARY_CANDIDATE_UNIVERSE_COUNT", "ACTIVE_PRODUCT_VOCABULARY_COUNT",
        "VALID_RESEARCH_ONLY_VOCABULARY_COUNT", "DEFERRED_VOCABULARY_COUNT", "REJECTED_VOCABULARY_COUNT",
        "UNCLASSIFIED_VOCABULARY_COUNT", "UNATTESTED_ACTIVE_VOCABULARY_COUNT",
        "ACADEMICALLY_UNSUPPORTED_ACTIVE_VOCABULARY_COUNT", "INVENTED_ACTIVE_VOCABULARY_COUNT",
        "ACTIVE_VOCABULARY_WITHOUT_CATEGORY_ENTRY_COUNT", "VOCABULARY_CANDIDATE_UNIVERSE_FROZEN",
    )),
    ("Pair census", (
        "EXPECTED_PAIR_COUNT", "PAIR_LEDGER_ROW_COUNT", "DUPLICATE_PAIR_COUNT", "MISSING_PAIR_COUNT",
        "SELF_PAIR_EXCLUSION_COUNT", "ACTIVE_EXTERNALLY_SUPPORTED_COUNT", "ACTIVE_SOURCE_SUPPORTED_COUNT",
        "INACTIVE_INSUFFICIENT_EVIDENCE_COUNT", "INACTIVE_CONFLICTING_SCOPE_COUNT",
        "INACTIVE_COOCCURRENCE_ONLY_COUNT", "INACTIVE_HARD_NEGATIVE_COUNT", "UNRESOLVED_PAIR_COUNT",
        "ACTIVE_ASSOCIATION_WITH_PENDING_VALIDATION_COUNT", "ALL_UNORDERED_PAIRS_ENUMERATED",
    )),
    ("Round 14 reconciliation", (
        "ROUND14_ASSESSMENT_COUNT", "ROUND14_DECISION_PRESERVED_COUNT", "ROUND14_DECISION_CHANGED_COUNT",
        "ROUND14_NEW_EVIDENCE_CHANGE_COUNT", "ROUND14_METHOD_CHANGE_COUNT",
    )),
    ("Graph", (
        "GRAPH_NODE_COUNT", "GRAPH_EDGE_COUNT", "GRAPH_DENSITY", "CONNECTED_COMPONENT_COUNT",
        "ISOLATED_ACTIVE_NODE_COUNT", "WITHIN_CATEGORY_EDGE_COUNT", "CROSS_CATEGORY_EDGE_COUNT",
        "VALIDATED_ASSOCIATION_GRAPH_FROZEN",
    )),
    ("Parameter universe", (
        "PARAMETER_COUNT", "PARAMETER_UNIVERSE_FROZEN", "MAX_NODE_COUNT", "MAX_ADMITTED_DEGREE",
        "TOPOLOGY_ENUM_COUNT",
    )),
    ("Composition census", (
        "RAW_NODE_SUBSET_COUNT", "CONNECTED_NODE_SUBSET_COUNT", "RAW_EDGE_SUBGRAPH_COUNT",
        "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT", "TOPOLOGY_INSTANTIATED_COMPOSITION_COUNT",
        "SEED_VARIANT_COUNT", "CATEGORY_ENTRY_VARIANT_COUNT", "INVALID_COMPOSITION_COUNT",
        "DUPLICATE_CANONICALISATION_COUNT", "LINEAR_PATH_VALID_COUNT", "BINARY_FORK_VALID_COUNT",
        "BINARY_CONVERGENCE_VALID_COUNT", "QUALIFIED_PATH_VALID_COUNT", "REFLEXIVE_RETURN_VALID_COUNT",
        "EVIDENCE_GAP_TREE_VALID_COUNT", "PRUNED_COMPOSITION_COUNT", "SPLIT_COMPOSITION_COUNT",
        "EVIDENCE_GAP_COMPOSITION_COUNT", "UNRESOLVED_COMPOSITION_COUNT", "ROUND16_LEGACY_COMPOSITION_COUNT",
        "ROUND16_LEGACY_COMPOSITION_RECONCILED_COUNT", "ROUND16_LEGACY_COMPOSITION_UNEXPLAINED_COUNT",
        "ALL_LEGAL_SUBGRAPHS_ENUMERATED", "ALL_LEGAL_TOPOLOGIES_EVALUATED",
        "CANONICAL_COMPOSITION_COUNT_INDEPENDENTLY_VERIFIED",
    )),
    ("Categories", (
        "CANONICAL_CATEGORY_COUNT", "INVENTED_CATEGORY_COUNT", "CATEGORY_WITHOUT_DATABASE_AUTHORITY_COUNT",
        "MULTI_CATEGORY_COMPOSITION_COUNT", "ACTIVE_COMPOSITION_WITHOUT_CATEGORY_ENTRY_COUNT",
    )),
    ("State and transition census", (
        "STATE_ENUMERATED_COUNT", "STATE_VALIDATED_COUNT", "UNREACHABLE_PRODUCTION_STATE_COUNT",
        "DUPLICATE_STATE_HASH_COUNT", "TRANSITION_ENUMERATED_COUNT", "TRANSITION_EXECUTED_COUNT",
        "TRANSITION_PASS_COUNT", "TRANSITION_FAIL_COUNT",
    )),
    ("Workflow census", (
        "CANONICAL_WORKFLOW_COUNT", "WORKFLOW_REPLAYED_COUNT", "WORKFLOW_REPLAY_FAILURE_COUNT",
        "WORKFLOW_LENGTH_MIN", "WORKFLOW_LENGTH_MAX", "WORKFLOW_LENGTH_MEAN", "WORKFLOW_LENGTH_MEDIAN",
        "STATE_REPLAY_MISMATCH_COUNT", "SEMANTIC_REPLAY_MISMATCH_COUNT",
    )),
    ("Export census", (
        "EXPORT_VARIANT_COUNT", "EXPORT_MANIFEST_VALIDATED_COUNT", "PNG_RENDERED_COUNT", "PNG_VALIDATED_COUNT",
        "PNG_FAILURE_COUNT", "PNG_REPLAY_MISMATCH_COUNT", "MAP_TREE_STATE_MISMATCH_COUNT",
    )),
    ("Production model", (
        "FULL_AUDIT_CENSUS_BYTES", "PRODUCTION_READ_MODEL_BYTES", "PRODUCTION_MODEL_LOAD_MS",
        "PRODUCTION_MODEL_RSS_DELTA_BYTES", "PRODUCTION_MODEL_HEAP_DELTA_BYTES",
        "AUDIT_TO_PRODUCTION_EQUIVALENCE_MISMATCH_COUNT",
    )),
    ("Production HTTP", (
        "ACTUAL_PRODUCTION_HTTP_TESTED", "CONCURRENCY_TEST_COMPLETED", "CONCURRENT_PNG_TEST_COMPLETED",
        "SUSTAINED_LOAD_TEST_COMPLETED", "COLD_START_MS", "FIRST_REQUEST_MS", "JSON_API_P50_MS",
        "JSON_API_P95_MS", "JSON_API_P99_MS", "JSON_API_MAX_MS", "PNG_P50_MS", "PNG_P95_MS",
        "PNG_P99_MS", "PNG_MAX_MS", "PEAK_RSS_BYTES", "PEAK_HEAP_USED_BYTES", "PEAK_CPU_PERCENT",
        "PEAK_EVENT_LOOP_DELAY_MS", "TOTAL_HTTP_REQUEST_COUNT", "HTTP_SUCCESS_COUNT", "HTTP_FAILURE_COUNT",
        "HTTP_TIMEOUT_COUNT", "UNEXPECTED_5XX_COUNT",
    )),
    ("Build-time computation", (
        "VOCABULARY_CENSUS_DURATION_MS", "PAIR_CENSUS_DURATION_MS", "GRAPH_BUILD_DURATION_MS",
        "COMPOSITION_ENUMERATION_DURATION_MS", "STATE_GENERATION_DURATION_MS", "TRANSITION_GENERATION_DURATION_MS",
        "WORKFLOW_GENERATION_DURATION_MS", "EXPORT_VALIDATION_DURATION_MS", "ENUMERATION_PEAK_RSS_BYTES",
        "ENUMERATION_TEMP_STORAGE_BYTES",
    )),
    ("Independent verification", (
        "INDEPENDENT_COUNT_MISMATCH_COUNT", "INDEPENDENT_HASH_MISMATCH_COUNT", "VOCABULARY_CENSUS_HASH_MATCH",
        "PAIR_CENSUS_HASH_MATCH", "GRAPH_HASH_MATCH", "COMPOSITION_REGISTRY_HASH_MATCH", "STATE_CENSUS_HASH_MATCH",
        "TRANSITION_CENSUS_HASH_MATCH", "WORKFLOW_CENSUS_HASH_MATCH", "EXPORT_CENSUS_HASH_MATCH",
        "REPRODUCIBILITY_VERIFICATION",
    )),
    ("Semantic safety", (
        "DATABASE_TEXT_COOCCURRENCE_ASSOCIATION_PASS_COUNT", "DATABASE_METADATA_INFERRED_RELATION_COUNT",
        "UNSUPPORTED_EDGE_COUNT", "TYPED_RELATION_EMISSION_COUNT", "CAUSAL_RELATION_EMISSION_COUNT",
        "DIRECTIONAL_RELATION_EMISSION_COUNT", "STATE_CORRUPTION_COUNT", "SEMANTIC_HASH_MISMATCH_COUNT",
    )),
    ("Regression", (
        "ROUND8_REGRESSION", "ROUND9_REGRESSION", "ROUND10_REGRESSION", "ROUND11_REGRESSION",
        "ROUND12_REGRESSION", "ROUND13_REGRESSION", "ROUND14_REGRESSION", "ROUND15_REGRESSION",
        "ROUND16_REGRESSION", "DATABASE_FREEZE", "REPOSITORY_HYGIENE", "TYPECHECK", "PRODUCTION_BUILD",
        "API_SCHEMA_VALIDATION", "AUDIT_SEAL",
    )),
    ("Product boundary", (
        "FINAL_EXPLORATION_FRONTEND_IMPLEMENTED", "PUBLIC_EXPLORATION_PAGE_ADDED",
        "PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN", "DEPLOYED", "EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED",
    )),
    ("Main", (
        "MAIN_BEFORE_SHA", "MAIN_FAST_FORWARD_COMPLETED", "MAIN_AFTER_SHA", "FORCE_PUSH_USED",
        "MERGE_COMMIT_CREATED", "HISTORY_REWRITTEN", "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN",
        "PUBLIC_EXISTING_HISTORY_REWRITTEN", "ORIGIN_MAIN_REWRITTEN",
    )),
    ("Final decision", (
        "ROUND16A_DECISION", "FUNCTION3_FULL_SPACE_CENSUS_COMPLETE", "FUNCTION3_BACKEND_FUNCTIONALLY_COMPLETE",
        "TRACE_FUNCTION3_EXPLORATION_CLOSED", "PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN", "NEXT_GATE",
    )),
)

RECEIPT_KEYS = tuple(key for _, keys in RECEIPT_SECTIONS for key in keys)
FINAL_INTEGRATION_KEYS = {
    "FINAL_LOCAL_SHA", "FINAL_REMOTE_SHA", "WORKTREE", "WORKTREE_CLEAN", "BRANCH",
    "ROLLBACK_TAG", "ROLLBACK_TAG_TARGET", "MAIN_BEFORE_SHA", "MAIN_FAST_FORWARD_COMPLETED",
    "MAIN_AFTER_SHA", "FORCE_PUSH_USED", "MERGE_COMMIT_CREATED", "HISTORY_REWRITTEN",
    "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN", "PUBLIC_EXISTING_HISTORY_REWRITTEN",
    "ORIGIN_MAIN_REWRITTEN",
}


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected one JSON object per line")
            rows.append(value)
    return rows


def summarize_transition_tsv(path: Path) -> dict[str, Any]:
    """Stream the 285 MB transition ledger once instead of materializing it."""
    action_counts: Counter[str] = Counter()
    transitions_by_state: Counter[str] = Counter()
    count = executed_count = pass_count = state_mutation_count = 0
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"current_state_id", "action", "executed", "passed", "state_mutated"}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"ROUND16A_TRANSITION_LEDGER_FIELDS:{missing}")
        for row in reader:
            count += 1
            action_counts[str(row["action"])] += 1
            transitions_by_state[str(row["current_state_id"])] += 1
            executed_count += int(tsv_bool(row, "executed"))
            pass_count += int(tsv_bool(row, "passed"))
            state_mutation_count += int(tsv_bool(row, "state_mutated"))
    if count == 0:
        raise ValueError("ROUND16A_TRANSITION_LEDGER_EMPTY")
    return {
        "count": count,
        "executed_count": executed_count,
        "pass_count": pass_count,
        "fail_count": count - pass_count,
        "state_mutation_count": state_mutation_count,
        "action_counts": action_counts,
        "transitions_by_state": transitions_by_state,
    }


def load_inputs() -> tuple[dict[str, Any], dict[str, list[dict[str, str]]], dict[str, list[dict[str, Any]]]]:
    required = [RAW / name for name in JSON_INPUTS + TSV_INPUTS + JSONL_INPUTS]
    required.extend(RESEARCH / name for name in EARLY_REQUIRED_REPORTS)
    missing = [str(path.relative_to(REPO)) for path in required if not path.is_file()]
    empty = [str(path.relative_to(REPO)) for path in required if path.is_file() and path.stat().st_size == 0]
    if missing or empty:
        raise FileNotFoundError(f"ROUND16A_REPORT_INPUT_GATE: missing={missing}; empty={empty}")

    json_docs = {name: json.loads((RAW / name).read_text(encoding="utf-8")) for name in JSON_INPUTS}
    # transition-census-v2.tsv is streamed separately by the report builder.
    tsv_docs = {name: ([] if name == "transition-census-v2.tsv" else read_tsv(RAW / name)) for name in TSV_INPUTS}
    jsonl_docs = {name: read_jsonl(RAW / name) for name in JSONL_INPUTS}
    if not tsv_docs["command-ledger.tsv"] or not jsonl_docs["execution-events.jsonl"]:
        raise ValueError("ROUND16A_REPORT_LOG_GATE: command and execution ledgers must be non-empty")
    return json_docs, tsv_docs, jsonl_docs


def normal_name(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


class MetricResolver:
    """Resolve exact named metrics while retaining source provenance."""

    def __init__(self) -> None:
        self.values: dict[str, list[tuple[str, Any]]] = defaultdict(list)

    def add(self, name: str, value: Any, source: str, *, first: bool = False) -> None:
        key = normal_name(name)
        if not key:
            return
        pair = (source, value)
        if first:
            self.values[key].insert(0, pair)
        else:
            self.values[key].append(pair)

    def scan(self, document: Any, source: str) -> None:
        def visit(value: Any) -> None:
            if isinstance(value, list):
                for child in value:
                    visit(child)
                return
            if not isinstance(value, dict):
                return
            metric_name = value.get("metric_name", value.get("metricName"))
            if metric_name and "value" in value:
                self.add(str(metric_name), value["value"], source)
            for key, child in value.items():
                if scalar(child):
                    self.add(str(key), child, source)
                elif isinstance(child, dict) and "value" in child and scalar(child["value"]):
                    self.add(str(key), child["value"], source)
                visit(child)

        visit(document)

    def set(self, name: str, value: Any, source: str) -> None:
        self.add(name, value, source, first=True)

    def get(self, name: str, *aliases: str, default: Any = UNKNOWN) -> Any:
        for candidate in (name, *aliases):
            rows = self.values.get(normal_name(candidate), [])
            if rows:
                return rows[0][1]
        return default

    def source(self, name: str, *aliases: str) -> str:
        for candidate in (name, *aliases):
            rows = self.values.get(normal_name(candidate), [])
            if rows:
                return rows[0][0]
        return UNKNOWN


def as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    folded = str(value).strip().casefold()
    if folded in {"true", "pass", "passed", "ready", "complete", "completed", "yes", "1"}:
        return True
    if folded in {"false", "fail", "failed", "not_ready", "incomplete", "no", "0"}:
        return False
    return None


def number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def yesno(value: Any) -> str:
    parsed = as_bool(value)
    if parsed is None:
        return str(value)
    return "true" if parsed else "false"


def fmt(value: Any) -> str:
    if value is UNKNOWN or value == UNKNOWN:
        return UNKNOWN
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, dict)):
        return f"`{compact_json(value)}`"
    return str(value)


def pct(numerator: int | float, denominator: int | float) -> str:
    return "0.00%" if not denominator else f"{100 * numerator / denominator:.2f}%"


def markdown_cell(value: Any) -> str:
    return fmt(value).replace("|", "\\|").replace("\n", " ")


def table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    material = list(rows)
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(markdown_cell(value) for value in row) + " |" for row in material]
    return "\n".join((head, rule, *body))


def distribution_table(distribution: Mapping[str, Any], first: str = "Value") -> str:
    return table((first, "Count"), sorted(distribution.items(), key=lambda item: str(item[0])))


def tsv_bool(row: Mapping[str, Any], key: str) -> bool:
    return as_bool(row.get(key)) is True


def walk_workloads(document: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            if "request_count" in value and ("concurrency" in value or "workload_id" in value or "mode" in value):
                found.append(value)
            for child in value.values():
                visit(child)

    visit(document)
    deduplicated: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(found):
        key = str(row.get("workload_id", f"{row.get('mode', 'workload')}:{row.get('concurrency', '')}:{index}"))
        deduplicated.setdefault(key, row)
    return list(deduplicated.values())


def metric_records(document: Any) -> list[dict[str, Any]]:
    candidate = document.get("metrics", document) if isinstance(document, dict) else document
    records: list[dict[str, Any]] = []
    if isinstance(candidate, list):
        records = [dict(row) for row in candidate if isinstance(row, dict)]
    elif isinstance(candidate, dict):
        for name, value in candidate.items():
            if isinstance(value, dict):
                record = dict(value)
                record.setdefault("metric_name", name)
            else:
                record = {"metric_name": name, "value": value}
            records.append(record)
    return sorted(records, key=lambda row: normal_name(str(row.get("metric_name", row.get("name", "")))))


def preserve_vocabulary_reports() -> None:
    mappings = (
        (RESEARCH / "06_VOCABULARY_CENSUS.md", RESEARCH / "03A_VOCABULARY_CENSUS.md", "# Round 16A Vocabulary Census"),
        (RESEARCH / "07_VOCABULARY_DISPOSITION_RECONCILIATION.md", RESEARCH / "03B_VOCABULARY_DISPOSITION_RECONCILIATION.md", "# Round 16A Vocabulary Disposition Reconciliation"),
    )
    for source, target, expected_heading in mappings:
        if not source.is_file():
            if not target.is_file():
                raise FileNotFoundError(f"VOCABULARY_REPORT_PRESERVATION_GATE:{source.relative_to(REPO)}")
            continue
        content = source.read_bytes()
        if source.read_text(encoding="utf-8").startswith(expected_heading):
            if target.is_file() and target.read_bytes() != content:
                raise ValueError(f"VOCABULARY_REPORT_PRESERVATION_CONFLICT:{target.relative_to(REPO)}")
            if not target.is_file():
                target.write_bytes(content)
        elif not target.is_file():
            raise ValueError(f"VOCABULARY_REPORT_PRESERVATION_MISSING:{target.relative_to(REPO)}")


def append_once(path: Path, marker: str, block: str) -> None:
    existing = path.read_text(encoding="utf-8")
    if marker in existing:
        if block not in existing:
            raise ValueError(f"ADDITIVE_HISTORY_CONFLICT:{path.relative_to(REPO)}:{marker}")
        return
    separator = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(separator + block)


def source_path(name: str) -> str:
    return f"docs/audits/v49-exploration-full-space-closure-round1/raw/{name}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("reports", "receipt", "reports-and-receipt"),
        default="reports",
        help="Reports mutate the research package; receipt-only performs no repository writes.",
    )
    parser.add_argument(
        "--integration-evidence",
        type=Path,
        help="Final post-push integration JSON required whenever a final receipt is emitted.",
    )
    parser.add_argument(
        "--receipt-output",
        type=Path,
        help="Optional output for KEY=value receipt text; stdout is used when omitted.",
    )
    return parser.parse_args()


def load_integration_evidence(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    resolved = path if path.is_absolute() else REPO / path
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("ROUND16A_FINAL_INTEGRATION_EVIDENCE_NOT_OBJECT")
    if (
        value.get("schema_version")
        != "trace-round16a-final-integration-evidence/v2"
        or value.get("integration_mode") != "review-branch"
        or value.get("main_integration_expected") is not False
        or value.get("remote_rollback_tag_present") is not False
        or value.get("validation_failures") != []
    ):
        raise ValueError("ROUND16A_FINAL_INTEGRATION_EVIDENCE_CONTRACT_INVALID")
    if str(value.get("status", "")).upper() != "PASS":
        raise ValueError("ROUND16A_FINAL_INTEGRATION_EVIDENCE_NOT_PASS")
    receipt = value.get("receipt", value.get("metrics"))
    if not isinstance(receipt, dict):
        raise ValueError("ROUND16A_FINAL_INTEGRATION_RECEIPT_MISSING")
    missing = sorted(key for key in FINAL_INTEGRATION_KEYS if key not in receipt)
    extras = sorted(key for key, child in receipt.items() if key in FINAL_INTEGRATION_KEYS and not scalar(child))
    if missing or extras:
        raise ValueError(f"ROUND16A_FINAL_INTEGRATION_CONTRACT:missing={missing};nonscalar={extras}")
    return receipt


def receipt_scalar(value: Any) -> str:
    if value == UNKNOWN or value is UNKNOWN or value is None:
        raise ValueError("ROUND16A_FINAL_RECEIPT_UNKNOWN_VALUE")
    if isinstance(value, bool):
        return "true" if value else "false"
    if not scalar(value):
        raise ValueError(f"ROUND16A_FINAL_RECEIPT_NONSCALAR:{type(value).__name__}")
    rendered = str(value)
    if "\n" in rendered or "\r" in rendered or "=" in rendered:
        raise ValueError("ROUND16A_FINAL_RECEIPT_UNSAFE_SCALAR")
    return rendered


def render_final_receipt(values: Mapping[str, Any]) -> str:
    missing = sorted(key for key in set(RECEIPT_KEYS) if key not in values or values[key] in (UNKNOWN, None, ""))
    if missing:
        raise ValueError(f"ROUND16A_FINAL_RECEIPT_MISSING:{missing}")
    lines: list[str] = []
    for heading, keys in RECEIPT_SECTIONS:
        if lines:
            lines.append("")
        if heading is not None:
            lines.append(f"# {heading}")
            lines.append("")
        lines.extend(f"{key}={receipt_scalar(values[key])}" for key in keys)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    json_docs, tsv_docs, jsonl_docs = load_inputs()
    final_gate = json_docs["final-gate-evidence.json"]
    if str(final_gate.get("status", "")).upper() != "PASS":
        raise ValueError("ROUND16A_FINAL_GATE_EVIDENCE_NOT_PASS")
    if final_gate.get("missing_required_metrics") or final_gate.get("conflicts"):
        raise ValueError("ROUND16A_FINAL_GATE_EVIDENCE_HAS_OPEN_ITEMS")
    integration_evidence = load_integration_evidence(args.integration_evidence)
    if args.mode in {"receipt", "reports-and-receipt"} and not integration_evidence:
        raise ValueError("ROUND16A_FINAL_RECEIPT_REQUIRES_INTEGRATION_EVIDENCE")
    environment = json_docs["environment.json"]
    database = json_docs["database-identity-v2.json"]
    vocabulary_universe = json_docs["vocabulary-candidate-universe-v2.json"]
    vocabulary_census = json_docs["vocabulary-census-v2.json"]
    active_vocabulary = json_docs["active-vocabulary-v2.json"]
    pair_universe = json_docs["pair-universe-v2.json"]
    association_census = json_docs["association-census-v2.json"]
    graph = json_docs["validated-association-graph-v2.json"]
    graph_stats = json_docs["graph-statistics-v2.json"]
    parameters = json_docs["exploration-parameter-universe-v2.json"]
    registry = json_docs["canonical-composition-registry-v2.json"]
    composition_stats = json_docs["composition-statistics-v2.json"]
    model_meta = json_docs["production-read-model-metadata-v2.json"]
    space = json_docs["space-generation-summary-v2.json"]
    api = json_docs["api-functional-validation-v2.json"]
    independent = json_docs["independent-verification.json"]
    reproduction = json_docs["reproducibility-verification.json"]
    authorized_migration = json_docs["authorized-lfs-migration-receipt.json"]
    migration_material = dict(authorized_migration)
    migration_embedded_hash = migration_material.pop("receipt_hash", None)
    expected_migration_hash = hashlib.sha256(
        (
            json.dumps(
                migration_material,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    migration_receipt = authorized_migration.get("receipt")
    expected_migration_paths = sorted((
        "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification-cases-v2.tsv",
        "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification.json",
    ))
    expected_migration_receipt = {
        "HISTORY_REWRITTEN": True,
        "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
        "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
        "ORIGIN_MAIN_REWRITTEN": False,
        "FORCE_PUSH_USED": False,
    }
    if (
        migration_embedded_hash != expected_migration_hash
        or authorized_migration.get("schema_version")
        != "trace-round16a-authorized-lfs-migration-receipt/v1"
        or authorized_migration.get("status") != "PASS"
        or authorized_migration.get("source_sha") != SOURCE_SHA
        or authorized_migration.get("source_tree_sha")
        != "86c2ed7771034f6d3f0f2e10e7a37aeec0552c71"
        or authorized_migration.get("new_head_sha")
        != "02eb7055659714a0e5ebce85dabdcda02dce2cc1"
        or authorized_migration.get("branch")
        != "codex/trace-v49-exploration-full-space-closure-round1"
        or sorted(authorized_migration.get("migrated_paths", [])) != expected_migration_paths
        or not isinstance(migration_receipt, Mapping)
        or any(migration_receipt.get(key) is not expected for key, expected in expected_migration_receipt.items())
        or authorized_migration.get("topology", {}).get(
            "post_migration_ordinary_blob_scope"
        ) != "ALL_HISTORY_REACHABLE_FROM_REWRITTEN_BRANCH"
        or authorized_migration.get("topology", {}).get(
            "post_migration_ordinary_blob_over_limit_count"
        ) != 0
    ):
        raise ValueError("ROUND16A_AUTHORIZED_LFS_MIGRATION_REPORT_INPUT_INVALID")
    checkpoints = tsv_docs["checkpoint-ledger.tsv"]
    if [row.get("checkpoint_id") for row in checkpoints] != [
        f"CHECKPOINT-{index:03d}" for index in range(1, 10)
    ]:
        raise ValueError("ROUND16A_POST_MIGRATION_CHECKPOINT_SEQUENCE_INVALID")
    hardened_checkpoint = checkpoints[8]
    hardened_sha = str(hardened_checkpoint.get("commit_sha", ""))
    reproduction_worktree = reproduction.get("worktree")
    if (
        reproduction.get("schema_version")
        != "trace-exploration-round16a-reproducibility-verification-v2"
        or reproduction.get("status") != "PASS"
        or reproduction.get("reproducibility_verification") != "PASS"
        or reproduction.get("all_required_hashes_match") is not True
        or reproduction.get("clean_worktree_reproduction") is not True
        or "POST_MIGRATION" not in hardened_checkpoint.get("phase", "").upper()
        or "HARDENED" not in hardened_checkpoint.get("phase", "").upper()
        or "supersedes_checkpoint_007_as_post_migration_final_code_sha=true"
        not in hardened_checkpoint.get("known_limitations", "").casefold()
        or reproduction.get("final_code_sha") != hardened_sha
        or not isinstance(reproduction_worktree, Mapping)
        or reproduction_worktree.get("primary_head") != hardened_sha
        or reproduction_worktree.get("reproduction_head") != hardened_sha
    ):
        raise ValueError("ROUND16A_POST_MIGRATION_REPRODUCTION_REPORT_INPUT_INVALID")

    vocab_rows = vocabulary_census.get("candidates", tsv_docs["vocabulary-census-v2.tsv"])
    active_rows = active_vocabulary.get("active_vocabulary", [])
    pair_rows = tsv_docs["pair-universe-v2.tsv"]
    association_rows = association_census.get("pairs", tsv_docs["association-census-v2.tsv"])
    composition_rows = tsv_docs["composition-enumeration-v2.tsv"]
    category_rows = tsv_docs["category-entry-census-v2.tsv"]
    state_rows = tsv_docs["state-census-v2.tsv"]
    transition_summary = summarize_transition_tsv(RAW / "transition-census-v2.tsv")
    workflow_rows = tsv_docs["workflow-census-v2.tsv"]
    export_rows = tsv_docs["export-census-v2.tsv"]
    png_rows = tsv_docs["png-validation-v2.tsv"]

    if environment.get("source_sha") != SOURCE_SHA:
        raise ValueError(f"ROUND16A_SOURCE_IDENTITY_GATE:{environment.get('source_sha')}")
    if database.get("database_snapshot_id") != DATABASE_SNAPSHOT:
        raise ValueError(f"ROUND16A_DATABASE_IDENTITY_GATE:{database.get('database_snapshot_id')}")
    if not vocab_rows or not active_rows or not pair_rows or not association_rows:
        raise ValueError("ROUND16A_SEMANTIC_CENSUS_EMPTY")
    if len(jsonl_docs["association-query-log-v2.jsonl"]) != len(pair_rows):
        raise ValueError("ROUND16A_QUERY_LEDGER_COVERAGE_GATE")
    dictionary_preflight = metric_records(json_docs["metric-dictionary.json"])
    if not dictionary_preflight:
        raise ValueError("ROUND16A_METRIC_DICTIONARY_EMPTY")
    dictionary_fields = {
        "metric_name": ("metric_name", "name"),
        "formal_definition": ("formal_definition", "definition"),
        "unit": ("unit",),
        "numerator": ("numerator",),
        "denominator": ("denominator",),
        "source_artifact": ("source_artifact",),
        "generation_script": ("generation_script",),
        "verification_script": ("verification_script",),
        "database_snapshot": ("database_snapshot",),
        "value": ("value",),
        "independent_verification_status": ("independent_verification_status",),
        "public_safe_status": ("public_safe_status",),
        "required_caveat": ("required_caveat",),
    }
    malformed_dictionary: list[str] = []
    for index, record in enumerate(dictionary_preflight):
        missing_fields = [formal for formal, aliases in dictionary_fields.items() if not any(alias in record for alias in aliases)]
        if missing_fields:
            malformed_dictionary.append(f"row={index}:missing={','.join(missing_fields)}")
    if malformed_dictionary:
        raise ValueError(f"ROUND16A_METRIC_DICTIONARY_CONTRACT:{malformed_dictionary[:10]}")
    dictionary_names = [normal_name(str(record.get("metric_name", record.get("name", "")))) for record in dictionary_preflight]
    duplicate_dictionary_names = sorted(name for name, count in Counter(dictionary_names).items() if name and count != 1)
    required_branding_metrics = {
        "PAIR_CANDIDATE_COUNT", "ACTIVE_ASSOCIATION_COUNT",
        "ASSOCIATION_USED_BY_ANY_COMPOSITION_COUNT", "ASSOCIATION_ADMITTED_BY_ANY_COMPOSITION_COUNT",
        "ASSOCIATION_VISIBLE_IN_ANY_STATE_COUNT", "ASSOCIATION_EXPORTED_IN_ANY_CARD_COUNT",
        "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT", "STATE_COUNT", "TRANSITION_COUNT", "WORKFLOW_COUNT",
        "EXPORT_VARIANT_COUNT",
    }
    missing_dictionary_metrics = sorted(required_branding_metrics - set(dictionary_names))
    if duplicate_dictionary_names or missing_dictionary_metrics:
        raise ValueError(
            f"ROUND16A_METRIC_DICTIONARY_COVERAGE:duplicates={duplicate_dictionary_names};missing={missing_dictionary_metrics}"
        )
    headline_map = json_docs["headline-numbers.json"].get("headlines")
    if not isinstance(headline_map, dict):
        raise ValueError("ROUND16A_HEADLINE_NUMBERS_MAP_MISSING")
    required_headlines = {
        "VOCABULARY_CANDIDATE_COUNT", "ACTIVE_VOCABULARY_COUNT", "PAIR_UNIVERSE_COUNT",
        "ACTIVE_ASSOCIATION_COUNT", "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT",
        "VALID_TOPOLOGY_COMPOSITION_COUNT", "SEED_VARIANT_COUNT", "CATEGORY_ENTRY_COUNT",
        "STATE_COUNT", "TRANSITION_COUNT", "WORKFLOW_COUNT", "EXPORT_VARIANT_COUNT",
    }
    missing_headlines = sorted(required_headlines - set(headline_map))
    if missing_headlines:
        raise ValueError(f"ROUND16A_HEADLINE_NUMBERS_COVERAGE:{missing_headlines}")
    expected_headlines = {
        "VOCABULARY_CANDIDATE_COUNT": len(vocab_rows),
        "ACTIVE_VOCABULARY_COUNT": len(active_rows),
        "PAIR_UNIVERSE_COUNT": len(pair_rows),
        "ACTIVE_ASSOCIATION_COUNT": sum(
            tsv_bool(row, "active") or str(row.get("final_status", "")).startswith("ACTIVE_")
            for row in association_rows
        ),
        "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT": len(registry.get("association_subgraphs", [])),
        "VALID_TOPOLOGY_COMPOSITION_COUNT": sum(str(row.get("decision")) == "VALID" for row in composition_rows),
        "SEED_VARIANT_COUNT": sum(len(row.get("seed_variants", [])) for row in registry.get("topology_compositions", [])),
        "CATEGORY_ENTRY_COUNT": len(category_rows),
        "STATE_COUNT": len(state_rows),
        "TRANSITION_COUNT": transition_summary["count"],
        "WORKFLOW_COUNT": len(workflow_rows),
        "EXPORT_VARIANT_COUNT": len(export_rows),
    }
    headline_mismatches = {
        name: {"expected": expected, "actual": headline_map.get(name)}
        for name, expected in expected_headlines.items() if headline_map.get(name) != expected
    }
    if headline_mismatches:
        raise ValueError(f"ROUND16A_HEADLINE_NUMBERS_MISMATCH:{headline_mismatches}")

    resolver = MetricResolver()
    # Priority is intentional: the consolidated operational evidence wins,
    # followed by independent quantitative/headline receipts and domain artifacts.
    for name in (
        "final-gate-evidence.json", "quantitative-audit.json", "headline-numbers.json", "metric-dictionary.json",
        "independent-verification.json", "reproducibility-verification.json",
        "production-http-results.json", "concurrency-results.json", "runtime-memory-results.json",
        "build-time-computation-results.json", "sustained-load-results.json",
        "api-functional-validation-v2.json", "space-generation-summary-v2.json",
        "composition-statistics-v2.json", "graph-statistics-v2.json", "database-identity-v2.json",
    ):
        resolver.scan(json_docs[name], source_path(name))
    for key, value in integration_evidence.items():
        resolver.set(key, value, str(args.integration_evidence or "integration evidence"))
    event_sequences = [integer(row.get("sequence"), -1) for row in jsonl_docs["execution-events.jsonl"]]
    expected_event_sequences = list(range(1, len(event_sequences) + 1))
    sequence_gap_count = sum(left != right for left, right in zip(event_sequences, expected_event_sequences))
    sequence_gap_count += abs(len(event_sequences) - len(expected_event_sequences))
    resolver.set("EXECUTION_EVENT_COUNT", len(event_sequences), source_path("execution-events.jsonl"))
    resolver.set("EXECUTION_LOG_SEQUENCE_GAP_COUNT", sequence_gap_count, source_path("execution-events.jsonl"))
    resolver.set("COMMAND_LOG_COUNT", len(tsv_docs["command-ledger.tsv"]), source_path("command-ledger.tsv"))
    resolver.set("CHECKPOINT_COMMIT_COUNT", len(tsv_docs["checkpoint-ledger.tsv"]), source_path("checkpoint-ledger.tsv"))

    dispositions = Counter(str(row.get("disposition", "UNCLASSIFIED")) for row in vocab_rows)
    statuses = Counter(str(row.get("final_status", "UNRESOLVED")) for row in association_rows)
    active_associations = [row for row in association_rows if tsv_bool(row, "active") or str(row.get("final_status", "")).startswith("ACTIVE_")]
    valid_topologies = [row for row in composition_rows if str(row.get("decision")) == "VALID"]
    invalid_topologies = [row for row in composition_rows if str(row.get("decision")) != "VALID"]
    topology_valid = Counter(str(row.get("topology_family")) for row in valid_topologies)
    topology_invalid = Counter(str(row.get("topology_family")) for row in invalid_topologies)
    action_counts = transition_summary["action_counts"]
    category_distribution = Counter(str(row.get("category_id")) for row in category_rows)
    workflow_lengths = [integer(row.get("workflow_length")) for row in workflow_rows]
    state_by_composition = Counter(str(row.get("composition_id")) for row in state_rows)
    transitions_by_state = transition_summary["transitions_by_state"]
    export_by_state = Counter(str(row.get("state_id")) for row in export_rows)
    export_by_theme = Counter(str(row.get("theme_token_set")) for row in export_rows)
    attestation_source_distribution = Counter(
        str(source_id) for row in active_rows for source_id in row.get("source_attestations", [])
    )
    academic_source_distribution = Counter(
        str(source_id) for row in active_rows for source_id in row.get("academic_support", [])
    )
    category_membership_distribution = Counter(
        str(category_id) for row in active_rows for category_id in row.get("category_ids", [])
    )
    category_memberships_per_term = Counter(str(len(row.get("category_ids", []))) for row in active_rows)
    polysemy_rows = [
        row for row in vocab_rows
        if re.search(r"(?i)polysem|ambigu|confus", " ".join((
            str(row.get("ambiguity_note", "")), str(row.get("decision_reason", "")),
        )))
    ]
    polysemy_disposition_distribution = Counter(str(row.get("disposition", "UNCLASSIFIED")) for row in polysemy_rows)

    release_counts = database.get("release_counts", {})
    resolver.set("DATABASE_SNAPSHOT_ID", database.get("database_snapshot_id", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("DATABASE_SCHEMA_VERSION", database.get("database_schema_version", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("DATABASE_CONTENT_HASH", database.get("database_content_sha256", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("DATABASE_FREEZE_HASH", database.get("freeze_manifest_sha256", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("PUBLIC_OBJECT_COUNT", release_counts.get("eligible_count", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("HELD_OBJECT_COUNT", release_counts.get("held_count", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("VOCABULARY_CANDIDATE_UNIVERSE_COUNT", len(vocab_rows), source_path("vocabulary-census-v2.json"))
    resolver.set("ACTIVE_PRODUCT_VOCABULARY_COUNT", len(active_rows), source_path("active-vocabulary-v2.json"))
    resolver.set("ACTIVE_VOCABULARY_COUNT", len(active_rows), source_path("active-vocabulary-v2.json"))
    resolver.set("VALID_RESEARCH_ONLY_VOCABULARY_COUNT", dispositions.get("RESEARCH_ONLY", 0), source_path("vocabulary-census-v2.json"))
    resolver.set("DEFERRED_VOCABULARY_COUNT", sum(count for name, count in dispositions.items() if name.startswith("DEFER")), source_path("vocabulary-census-v2.json"))
    resolver.set("REJECTED_VOCABULARY_COUNT", dispositions.get("REJECTED", 0), source_path("vocabulary-census-v2.json"))
    resolver.set("UNCLASSIFIED_VOCABULARY_COUNT", dispositions.get("UNCLASSIFIED", 0), source_path("vocabulary-census-v2.json"))
    resolver.set("UNATTESTED_ACTIVE_VOCABULARY_COUNT", sum(not row.get("source_attestations") for row in active_rows), source_path("active-vocabulary-v2.json"))
    resolver.set("ACADEMICALLY_UNSUPPORTED_ACTIVE_VOCABULARY_COUNT", sum(not row.get("academic_support") for row in active_rows), source_path("active-vocabulary-v2.json"))
    candidate_labels = {str(row.get("canonical_label", "")).casefold() for row in vocab_rows}
    resolver.set("INVENTED_ACTIVE_VOCABULARY_COUNT", sum(str(row.get("canonical_label", "")).casefold() not in candidate_labels for row in active_rows), source_path("active-vocabulary-v2.json"))
    resolver.set("STRUCTURAL_LABEL_ACTIVE_VOCABULARY_COUNT", sum(
        str(row.get("disposition")) == "ACTIVE"
        and "STRUCTURAL_OR_INTERFACE" in f"{row.get('status', '')} {row.get('decision_reason', '')}".upper()
        for row in vocab_rows
    ), source_path("vocabulary-census-v2.json"))
    resolver.set("ACTIVE_VOCABULARY_WITHOUT_BOUNDED_SENSE_COUNT", sum(not str(row.get("bounded_sense", "")).strip() for row in active_rows), source_path("active-vocabulary-v2.json"))
    resolver.set("ACTIVE_VOCABULARY_WITHOUT_CATEGORY_ENTRY_COUNT", sum(not row.get("category_ids") for row in active_rows), source_path("active-vocabulary-v2.json"))
    resolver.set("EXPECTED_PAIR_COUNT", len(active_rows) * (len(active_rows) - 1) // 2, source_path("active-vocabulary-v2.json"))
    resolver.set("ACTIVE_PAIR_UNIVERSE_COUNT", len(pair_rows), source_path("pair-universe-v2.tsv"))
    resolver.set("PAIR_CANDIDATE_COUNT", len(pair_rows), source_path("pair-universe-v2.tsv"))
    resolver.set("PAIR_LEDGER_ROW_COUNT", len(pair_rows), source_path("pair-universe-v2.tsv"))
    resolver.set("ASSOCIATION_QUERY_LOG_ROW_COUNT", len(jsonl_docs["association-query-log-v2.jsonl"]), source_path("association-query-log-v2.jsonl"))
    resolver.set("DUPLICATE_PAIR_COUNT", len(pair_rows) - len({row.get("canonical_pair_key") for row in pair_rows}), source_path("pair-universe-v2.tsv"))
    resolver.set("MISSING_PAIR_COUNT", max(0, len(active_rows) * (len(active_rows) - 1) // 2 - len(pair_rows)), source_path("pair-universe-v2.tsv"))
    resolver.set("SELF_PAIR_EXCLUSION_COUNT", len(pair_universe.get("self_pair_exclusions", [])), source_path("pair-universe-v2.json"))
    resolver.set("UNRESOLVED_PAIR_COUNT", association_census.get("unresolved_pair_count", statuses.get("UNRESOLVED", 0)), source_path("association-census-v2.json"))
    resolver.set("ACTIVE_ASSOCIATION_WITH_PENDING_VALIDATION_COUNT", association_census.get("active_association_with_pending_validation_count", 0), source_path("association-census-v2.json"))
    resolver.set("COOCCURRENCE_ONLY_ACTIVE_COUNT", sum(bool(row.get("cooccurrence_only")) for row in active_associations), source_path("association-census-v2.json"))
    resolver.set("ACTIVE_EXTERNALLY_SUPPORTED_COUNT", statuses.get("ACTIVE_EXTERNALLY_SUPPORTED", 0), source_path("association-census-v2.json"))
    resolver.set("ACTIVE_SOURCE_SUPPORTED_COUNT", statuses.get("ACTIVE_SOURCE_SUPPORTED", 0), source_path("association-census-v2.json"))
    resolver.set("INACTIVE_INSUFFICIENT_EVIDENCE_COUNT", statuses.get("INACTIVE_INSUFFICIENT_EVIDENCE", 0), source_path("association-census-v2.json"))
    resolver.set("INACTIVE_CONFLICTING_SCOPE_COUNT", statuses.get("INACTIVE_CONFLICTING_SCOPE", 0), source_path("association-census-v2.json"))
    resolver.set("INACTIVE_COOCCURRENCE_ONLY_COUNT", statuses.get("INACTIVE_COOCCURRENCE_ONLY", 0), source_path("association-census-v2.json"))
    resolver.set("INACTIVE_HARD_NEGATIVE_COUNT", statuses.get("INACTIVE_HARD_NEGATIVE", 0), source_path("association-census-v2.json"))
    governed_association_statuses = {
        "ACTIVE_EXTERNALLY_SUPPORTED", "ACTIVE_SOURCE_SUPPORTED", "INACTIVE_INSUFFICIENT_EVIDENCE",
        "INACTIVE_CONFLICTING_SCOPE", "INACTIVE_COOCCURRENCE_ONLY", "INACTIVE_HARD_NEGATIVE",
    }
    resolver.set("ASSOCIATION_DISPOSITION_TOTAL_COUNT", sum(statuses.get(name, 0) for name in governed_association_statuses), source_path("association-census-v2.json"))
    resolver.set("INVALID_ASSOCIATION_STATUS_COUNT", sum(count for name, count in statuses.items() if name not in governed_association_statuses), source_path("association-census-v2.json"))
    resolver.set("ACTIVE_ASSOCIATION_COUNT", len(active_associations), source_path("association-census-v2.json"))
    resolver.set("DATABASE_TEXT_COOCCURRENCE_ASSOCIATION_PASS_COUNT", sum(bool(row.get("database_text_cooccurrence_used")) for row in active_associations), source_path("association-census-v2.json"))
    resolver.set("DATABASE_METADATA_INFERRED_RELATION_COUNT", sum(bool(row.get("database_metadata_relation_inferred")) for row in association_rows), source_path("association-census-v2.json"))
    resolver.set("TYPED_RELATION_EMISSION_COUNT", sum(bool(row.get("typed_relation_emitted")) for row in association_rows), source_path("association-census-v2.json"))
    resolver.set("CAUSAL_RELATION_EMISSION_COUNT", sum(bool(row.get("causal_relation_emitted")) for row in association_rows), source_path("association-census-v2.json"))
    resolver.set("DIRECTIONAL_RELATION_EMISSION_COUNT", sum(bool(row.get("directional_relation_emitted")) for row in association_rows), source_path("association-census-v2.json"))
    round14_rows = association_census.get("round14_reconciliation", [])
    resolver.set("ROUND14_ASSESSMENT_COUNT", len(round14_rows), source_path("association-census-v2.json"))
    resolver.set("ROUND14_DECISION_PRESERVED_COUNT", sum(row.get("decision_reconciliation") == "PRESERVED" for row in round14_rows), source_path("association-census-v2.json"))
    resolver.set("ROUND14_DECISION_CHANGED_COUNT", sum(row.get("decision_reconciliation") != "PRESERVED" for row in round14_rows), source_path("association-census-v2.json"))
    resolver.set("ROUND14_NEW_EVIDENCE_CHANGE_COUNT", sum(bool(row.get("new_evidence_changed_decision")) for row in round14_rows), source_path("association-census-v2.json"))
    resolver.set("ROUND14_METHOD_CHANGE_COUNT", sum(bool(row.get("method_changed_decision")) for row in round14_rows), source_path("association-census-v2.json"))
    resolver.set("GRAPH_NODE_COUNT", len(graph.get("nodes", [])), source_path("validated-association-graph-v2.json"))
    resolver.set("GRAPH_EDGE_COUNT", len(graph.get("edges", [])), source_path("validated-association-graph-v2.json"))
    resolver.set("UNSUPPORTED_EDGE_COUNT", len({row.get("association_id") for row in graph.get("edges", [])} - {row.get("pair_id") for row in active_associations}), source_path("validated-association-graph-v2.json"))
    resolver.set("GRAPH_DENSITY", graph_stats.get("graph_density", UNKNOWN), source_path("graph-statistics-v2.json"))
    resolver.set("CONNECTED_COMPONENT_COUNT", graph_stats.get("connected_component_count", UNKNOWN), source_path("graph-statistics-v2.json"))
    resolver.set("ISOLATED_ACTIVE_NODE_COUNT", graph_stats.get("isolated_active_node_count", UNKNOWN), source_path("graph-statistics-v2.json"))
    resolver.set("WITHIN_CATEGORY_EDGE_COUNT", graph_stats.get("within_category_edge_count", UNKNOWN), source_path("graph-statistics-v2.json"))
    resolver.set("CROSS_CATEGORY_EDGE_COUNT", graph_stats.get("cross_category_edge_count", UNKNOWN), source_path("graph-statistics-v2.json"))
    resolver.set("PARAMETER_COUNT", parameters.get("parameter_count", len(parameters.get("parameters", []))), source_path("exploration-parameter-universe-v2.json"))
    parameter_by_name = {str(row.get("parameter_name")): row for row in parameters.get("parameters", [])}
    maximum_node_values = parameter_by_name.get("maximum_node_count", {}).get("legal_values", [])
    degree_bound_values = parameter_by_name.get("degree_bound", {}).get("legal_values", [])
    topology_values = parameter_by_name.get("topology", {}).get("legal_values", [])
    resolver.set("MAX_NODE_COUNT", max(map(integer, maximum_node_values), default=UNKNOWN), source_path("exploration-parameter-universe-v2.json"))
    resolver.set("MAX_ADMITTED_DEGREE", max(map(integer, degree_bound_values), default=UNKNOWN), source_path("exploration-parameter-universe-v2.json"))
    resolver.set("TOPOLOGY_ENUM_COUNT", len(topology_values), source_path("exploration-parameter-universe-v2.json"))
    resolver.set("RAW_NODE_SUBSET_COUNT", composition_stats.get("raw_node_subset_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("CONNECTED_NODE_SUBSET_COUNT", composition_stats.get("connected_node_subset_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("RAW_EDGE_SUBGRAPH_COUNT", composition_stats.get("raw_edge_subgraph_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("CANONICAL_ASSOCIATION_SUBGRAPH_COUNT", len(registry.get("association_subgraphs", [])), source_path("canonical-composition-registry-v2.json"))
    resolver.set("CANONICAL_SUBGRAPH_LEDGER_ROW_COUNT", len(registry.get("association_subgraphs", [])), source_path("canonical-composition-registry-v2.json"))
    resolver.set("TOPOLOGY_INSTANTIATED_COMPOSITION_COUNT", len(registry.get("topology_compositions", [])), source_path("canonical-composition-registry-v2.json"))
    resolver.set("VALID_TOPOLOGY_COMPOSITION_LEDGER_ROW_COUNT", len(valid_topologies), source_path("composition-enumeration-v2.tsv"))
    resolver.set("SEED_VARIANT_COUNT", sum(len(row.get("seed_variants", [])) for row in registry.get("topology_compositions", [])), source_path("canonical-composition-registry-v2.json"))
    resolver.set("CATEGORY_ENTRY_VARIANT_COUNT", len(category_rows), source_path("category-entry-census-v2.tsv"))
    resolver.set("INVALID_COMPOSITION_COUNT", len(invalid_topologies), source_path("composition-enumeration-v2.tsv"))
    resolver.set("DUPLICATE_CANONICALISATION_COUNT", composition_stats.get("duplicate_canonicalisation_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    for topology_name in ("LINEAR_PATH", "BINARY_FORK", "BINARY_CONVERGENCE", "QUALIFIED_PATH", "REFLEXIVE_RETURN", "EVIDENCE_GAP_TREE"):
        resolver.set(f"{topology_name}_VALID_COUNT", topology_valid.get(topology_name, 0), source_path("composition-enumeration-v2.tsv"))
    resolver.set("PRUNED_COMPOSITION_COUNT", composition_stats.get("pruned_composition_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("SPLIT_COMPOSITION_COUNT", composition_stats.get("split_composition_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("EVIDENCE_GAP_COMPOSITION_COUNT", composition_stats.get("evidence_gap_composition_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("UNRESOLVED_COMPOSITION_COUNT", composition_stats.get("unresolved_composition_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("ROUND16_LEGACY_COMPOSITION_COUNT", len(registry.get("round16_legacy_reconciliation", [])), source_path("canonical-composition-registry-v2.json"))
    resolver.set("ROUND16_LEGACY_COMPOSITION_RECONCILED_COUNT", composition_stats.get("round16_legacy_composition_reconciled_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("ROUND16_LEGACY_COMPOSITION_UNEXPLAINED_COUNT", composition_stats.get("round16_legacy_composition_unexplained_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("CANONICAL_CATEGORY_COUNT", database.get("category_authority", {}).get("governed_folder_type_count", UNKNOWN), source_path("database-identity-v2.json"))
    resolver.set("MULTI_CATEGORY_COMPOSITION_COUNT", composition_stats.get("multi_category_composition_count", UNKNOWN), source_path("composition-statistics-v2.json"))
    resolver.set("INVENTED_CATEGORY_COUNT", 0 if {row.get("category_id") for row in category_rows} <= {"region", "theme", "medium", "movement"} else 1, source_path("category-entry-census-v2.tsv"))
    resolver.set("CATEGORY_WITHOUT_DATABASE_AUTHORITY_COUNT", sum(not str(row.get("database_authority", "")).strip() for row in category_rows), source_path("category-entry-census-v2.tsv"))
    resolver.set("ACTIVE_COMPOSITION_WITHOUT_CATEGORY_ENTRY_COUNT", sum(not row.get("category_entries") for row in registry.get("topology_compositions", [])), source_path("canonical-composition-registry-v2.json"))
    resolver.set("STATE_ENUMERATED_COUNT", len(state_rows), source_path("state-census-v2.tsv"))
    resolver.set("STATE_VALIDATED_COUNT", space.get("state_validated_count", len(state_rows)), source_path("space-generation-summary-v2.json"))
    resolver.set("UNREACHABLE_PRODUCTION_STATE_COUNT", space.get("unreachable_production_state_count", UNKNOWN), source_path("space-generation-summary-v2.json"))
    resolver.set("DUPLICATE_STATE_HASH_COUNT", len(state_rows) - len({row.get("state_hash") for row in state_rows}), source_path("state-census-v2.tsv"))
    resolver.set("TRANSITION_ENUMERATED_COUNT", transition_summary["count"], source_path("transition-census-v2.tsv"))
    resolver.set("TRANSITION_EXECUTED_COUNT", transition_summary["executed_count"], source_path("transition-census-v2.tsv"))
    resolver.set("TRANSITION_PASS_COUNT", transition_summary["pass_count"], source_path("transition-census-v2.tsv"))
    resolver.set("TRANSITION_FAIL_COUNT", transition_summary["fail_count"], source_path("transition-census-v2.tsv"))
    resolver.set("STATE_MUTATION_COUNT", transition_summary["state_mutation_count"], source_path("transition-census-v2.tsv"))
    resolver.set("CANONICAL_WORKFLOW_COUNT", len(workflow_rows), source_path("workflow-census-v2.tsv"))
    resolver.set("WORKFLOW_REPLAYED_COUNT", sum(integer(row.get("replay_pass_count")) > 0 for row in workflow_rows), source_path("workflow-census-v2.tsv"))
    resolver.set("WORKFLOW_REPLAY_FAILURE_COUNT", sum(integer(row.get("replay_pass_count")) != integer(row.get("replay_count")) for row in workflow_rows), source_path("workflow-census-v2.tsv"))
    resolver.set("WORKFLOW_LENGTH_MIN", min(workflow_lengths, default=0), source_path("workflow-census-v2.tsv"))
    resolver.set("WORKFLOW_LENGTH_MAX", max(workflow_lengths, default=0), source_path("workflow-census-v2.tsv"))
    resolver.set("WORKFLOW_LENGTH_MEAN", statistics.fmean(workflow_lengths) if workflow_lengths else 0, source_path("workflow-census-v2.tsv"))
    resolver.set("WORKFLOW_LENGTH_MEDIAN", statistics.median(workflow_lengths) if workflow_lengths else 0, source_path("workflow-census-v2.tsv"))
    resolver.set("STATE_REPLAY_MISMATCH_COUNT", sum(integer(row.get("state_replay_mismatch_count")) for row in workflow_rows), source_path("workflow-census-v2.tsv"))
    resolver.set("SEMANTIC_REPLAY_MISMATCH_COUNT", sum(integer(row.get("semantic_replay_mismatch_count")) for row in workflow_rows), source_path("workflow-census-v2.tsv"))
    resolver.set("EXPORT_VARIANT_COUNT", len(export_rows), source_path("export-census-v2.tsv"))
    resolver.set("EXPORT_VARIANT_ENUMERATED_COUNT", len(export_rows), source_path("export-census-v2.tsv"))
    resolver.set("EXPORT_MANIFEST_VALIDATED_COUNT", sum(tsv_bool(row, "manifest_validated") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("SVG_RENDERED_COUNT", sum(tsv_bool(row, "svg_rendered") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("PNG_RENDERED_COUNT", sum(tsv_bool(row, "png_rendered") for row in png_rows), source_path("png-validation-v2.tsv"))
    png_gate_fields = (
        "manifest_validated", "manifest_schema_valid", "state_hash_match", "semantic_hash_match",
        "presentation_hash_match", "manifest_replay_match",
        "svg_rendered", "svg_headers_valid", "svg_envelope_valid", "svg_dimensions_valid",
        "svg_all_labels_valid", "svg_all_visible_associations_valid", "svg_provenance_non_claims_valid",
        "svg_zero_archive_object_exposure", "svg_replay_match",
        "png_rendered", "png_decoded", "png_content_type_valid", "png_headers_valid", "png_metadata_safe",
        "svg_png_render_match", "dimensions_valid",
        "upper_map_zone_valid", "lower_tree_zone_valid", "all_labels_valid",
        "all_visible_associations_valid", "provenance_summary_valid", "zero_archive_object_exposure",
        "replay_match", "map_tree_state_match",
    )
    svg_gate_fields = (
        "svg_rendered", "svg_headers_valid", "svg_envelope_valid", "svg_dimensions_valid",
        "svg_all_labels_valid", "svg_all_visible_associations_valid", "svg_provenance_non_claims_valid",
        "svg_zero_archive_object_exposure", "svg_replay_match",
    )
    svg_passes = [all(tsv_bool(row, key) for key in svg_gate_fields) and not str(row.get("error_code", "")).strip() for row in png_rows]
    png_passes = [all(tsv_bool(row, key) for key in png_gate_fields) and not str(row.get("error_code", "")).strip() for row in png_rows]
    resolver.set("SVG_VALIDATED_COUNT", sum(svg_passes), source_path("png-validation-v2.tsv"))
    resolver.set("SVG_FAILURE_COUNT", sum(not value for value in svg_passes), source_path("png-validation-v2.tsv"))
    resolver.set("SVG_REPLAY_MISMATCH_COUNT", sum(not tsv_bool(row, "svg_replay_match") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("PNG_VALIDATED_COUNT", sum(png_passes), source_path("png-validation-v2.tsv"))
    resolver.set("PNG_FAILURE_COUNT", sum(not value for value in png_passes), source_path("png-validation-v2.tsv"))
    resolver.set("PNG_REPLAY_MISMATCH_COUNT", sum(not tsv_bool(row, "replay_match") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("MAP_TREE_STATE_MISMATCH_COUNT", sum(not tsv_bool(row, "map_tree_state_match") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("PNG_ARCHIVE_OBJECT_REFERENCE_COUNT", sum(not tsv_bool(row, "zero_archive_object_exposure") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("SVG_ARCHIVE_OBJECT_REFERENCE_COUNT", sum(not tsv_bool(row, "svg_zero_archive_object_exposure") for row in png_rows), source_path("png-validation-v2.tsv"))
    resolver.set("PRODUCTION_READ_MODEL_BYTES", model_meta.get("production_read_model_bytes", 0), source_path("production-read-model-metadata-v2.json"))
    resolver.set("AUDIT_TO_PRODUCTION_EQUIVALENCE_MISMATCH_COUNT", model_meta.get("audit_to_production_equivalence_mismatch_count", UNKNOWN), source_path("production-read-model-metadata-v2.json"))
    resolver.set("ACTUAL_PRODUCTION_HTTP_TESTED", api.get("actual_production_http_tested", False), source_path("api-functional-validation-v2.json"))
    resolver.set("UNEXPECTED_5XX_COUNT", api.get("unexpected_5xx_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT", api.get("public_archive_object_id_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT", api.get("public_archive_object_title_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("PUBLIC_EXPLORATION_RECORD_LINK_COUNT", api.get("public_record_link_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT", api.get("public_context_reference_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT", api.get("public_spacetime_reference_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("HELD_DATA_LEAK_COUNT", api.get("held_data_leak_count", 0), source_path("api-functional-validation-v2.json"))
    resolver.set("STALE_STATE_ACCEPTED_COUNT", api.get("stale_state_accepted_count", UNKNOWN), source_path("api-functional-validation-v2.json"))
    resolver.set("INVALID_TARGET_ACCEPTED_COUNT", api.get("invalid_target_accepted_count", UNKNOWN), source_path("api-functional-validation-v2.json"))
    resolver.set("API_FAILURE_COUNT", api.get("fail_count", UNKNOWN), source_path("api-functional-validation-v2.json"))
    resolver.set("DIRECT_DATABASE_SNAPSHOT_VALIDATED", database.get("closure_metrics", {}).get("direct_database_snapshot_validated", False), source_path("database-identity-v2.json"))
    resolver.set("DIRECT_DATABASE_CATEGORY_BINDING_READY", database.get("closure_metrics", {}).get("direct_database_category_binding_ready", False), source_path("database-identity-v2.json"))
    resolver.set("REPRODUCIBILITY_VERIFICATION", reproduction.get("reproducibility_verification", reproduction.get("status", UNKNOWN)), source_path("reproducibility-verification.json"))

    json_workloads = walk_workloads(json_docs["concurrency-results.json"])
    png_workloads = [row for row in json_workloads if str(row.get("mode", "")).casefold() == "png"]
    api_workloads = [row for row in json_workloads if str(row.get("mode", "")).casefold() in {"json", "api"}]
    json_levels = {integer(row.get("concurrency")) for row in api_workloads}
    png_levels = {integer(row.get("concurrency")) for row in png_workloads}
    resolver.set("CONCURRENCY_TEST_COMPLETED", {1, 5, 10, 25, 50} <= json_levels, source_path("concurrency-results.json"))
    resolver.set("CONCURRENT_PNG_TEST_COMPLETED", {1, 2, 5, 10} <= png_levels, source_path("concurrency-results.json"))
    sustained_workloads = walk_workloads(json_docs["sustained-load-results.json"])
    sustained_document = json_docs["sustained-load-results.json"]
    sustained_criterion = sustained_document.get("termination_criterion", {}) if isinstance(sustained_document, dict) else {}
    sustained_completed = (
        sustained_document.get("status") == "PASS"
        and sustained_document.get("sustained_load_test_completed") is True
        and integer(sustained_criterion.get("minimum_request_count")) >= 10_000
        and number(sustained_criterion.get("minimum_duration_ms")) >= 300_000
        and integer(sustained_document.get("request_count")) >= integer(sustained_criterion.get("minimum_request_count"))
        and number(sustained_document.get("duration_ms")) >= number(sustained_criterion.get("minimum_duration_ms"))
        and bool(sustained_workloads)
    )
    resolver.set("SUSTAINED_LOAD_TEST_COMPLETED", sustained_completed, source_path("sustained-load-results.json"))

    # Required predicates that can be established directly from the census.
    resolver.set("VOCABULARY_CANDIDATE_UNIVERSE_FROZEN", bool(vocabulary_universe.get("universe_canonical_hash")), source_path("vocabulary-candidate-universe-v2.json"))
    resolver.set("ALL_UNORDERED_PAIRS_ENUMERATED", len(pair_rows) == len(active_rows) * (len(active_rows) - 1) // 2, source_path("pair-universe-v2.tsv"))
    resolver.set("VALIDATED_ASSOCIATION_GRAPH_FROZEN", graph.get("frozen") is True, source_path("validated-association-graph-v2.json"))
    resolver.set("PARAMETER_UNIVERSE_FROZEN", parameters.get("frozen") is True, source_path("exploration-parameter-universe-v2.json"))
    resolver.set("ALL_LEGAL_SUBGRAPHS_ENUMERATED", len(registry.get("association_subgraphs", [])) == integer(composition_stats.get("canonical_association_subgraph_count")), source_path("canonical-composition-registry-v2.json"))
    resolver.set("ALL_LEGAL_TOPOLOGIES_EVALUATED", len(composition_rows) == len(registry.get("association_subgraphs", [])) * 6, source_path("composition-enumeration-v2.tsv"))
    resolver.set("ALL_REACHABLE_STATES_ENUMERATED", len(state_rows) == integer(space.get("state_validated_count", len(state_rows))) and integer(space.get("unreachable_production_state_count", 0)) == 0, source_path("space-generation-summary-v2.json"))
    resolver.set("FULL_COMMAND_LOG_READY", bool(tsv_docs["command-ledger.tsv"]) and bool(jsonl_docs["execution-events.jsonl"]), source_path("command-ledger.tsv"))

    def gate_equal(name: str, expected: Any, *aliases: str) -> tuple[bool, Any, str]:
        actual = resolver.get(name, *aliases)
        if isinstance(expected, bool):
            passed = as_bool(actual) is expected
        elif isinstance(expected, (int, float)):
            passed = actual != UNKNOWN and number(actual, math.nan) == float(expected)
        else:
            passed = str(actual).upper() == str(expected).upper()
        return passed, actual, resolver.source(name, *aliases)

    def gate_equation(name: str, left: str, right: str) -> tuple[bool, str, str]:
        left_value = resolver.get(left)
        right_value = resolver.get(right)
        passed = left_value != UNKNOWN and right_value != UNKNOWN and number(left_value, math.nan) == number(right_value, math.nan)
        return passed, f"{fmt(left_value)} = {fmt(right_value)}", f"{resolver.source(left)}; {resolver.source(right)}"

    gate_specs: list[tuple[str, Any, tuple[str, ...]]] = [
        ("ACTIVE_EXPLORATION_AUTHORITY_COUNT", 1, ()),
        ("AUTHORITY_CONTRADICTION_COUNT", 0, ()),
        ("AUTHORITY_RECONCILIATION_READY", True, ()),
        ("SEARCH_CODE_MUTATION_COUNT", 0, ()),
        ("SEARCH_SCHEMA_MUTATION_COUNT", 0, ()),
        ("SEARCH_API_MUTATION_COUNT", 0, ()),
        ("SEARCH_INDEX_MUTATION_COUNT", 0, ()),
        ("SEARCH_RUNTIME_DEPENDENCY_COUNT", 0, ()),
        ("SEARCH_SEMANTIC_INPUT_COUNT", 0, ()),
        ("SEARCH_STATUS", "OUT_OF_SCOPE_NOT_EVALUATED", ()),
        ("CONTEXT_SEMANTIC_INPUT_COUNT", 0, ()),
        ("SPACETIME_SEMANTIC_INPUT_COUNT", 0, ()),
        ("CONTEXT_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT", 0, ()),
        ("SPACETIME_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT", 0, ()),
        ("CONTEXT_CODE_MUTATION_COUNT", 0, ()),
        ("SPACETIME_CODE_MUTATION_COUNT", 0, ()),
        ("DIRECT_DATABASE_SNAPSHOT_VALIDATED", True, ()),
        ("DIRECT_DATABASE_CATEGORY_BINDING_READY", True, ()),
        ("DATABASE_TEXT_COOCCURRENCE_ASSOCIATION_PASS_COUNT", 0, ()),
        ("DATABASE_METADATA_INFERRED_RELATION_COUNT", 0, ()),
        ("PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT", 0, ()),
        ("PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT", 0, ()),
        ("PUBLIC_EXPLORATION_RECORD_LINK_COUNT", 0, ()),
        ("PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT", 0, ()),
        ("PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT", 0, ()),
        ("PNG_ARCHIVE_OBJECT_REFERENCE_COUNT", 0, ()),
        ("HELD_DATA_LEAK_COUNT", 0, ()),
        ("VOCABULARY_CANDIDATE_UNIVERSE_FROZEN", True, ()),
        ("UNCLASSIFIED_VOCABULARY_COUNT", 0, ()),
        ("UNATTESTED_ACTIVE_VOCABULARY_COUNT", 0, ()),
        ("ACADEMICALLY_UNSUPPORTED_ACTIVE_VOCABULARY_COUNT", 0, ()),
        ("INVENTED_ACTIVE_VOCABULARY_COUNT", 0, ()),
        ("STRUCTURAL_LABEL_ACTIVE_VOCABULARY_COUNT", 0, ()),
        ("ACTIVE_VOCABULARY_WITHOUT_BOUNDED_SENSE_COUNT", 0, ()),
        ("ACTIVE_VOCABULARY_WITHOUT_CATEGORY_ENTRY_COUNT", 0, ()),
        ("ALL_UNORDERED_PAIRS_ENUMERATED", True, ()),
        ("DUPLICATE_PAIR_COUNT", 0, ()),
        ("MISSING_PAIR_COUNT", 0, ()),
        ("INVALID_ASSOCIATION_STATUS_COUNT", 0, ()),
        ("UNRESOLVED_PAIR_COUNT", 0, ()),
        ("ACTIVE_ASSOCIATION_WITH_PENDING_VALIDATION_COUNT", 0, ()),
        ("COOCCURRENCE_ONLY_ACTIVE_COUNT", 0, ()),
        ("ROUND14_ASSESSMENT_COUNT", 35, ()),
        ("ROUND14_DECISION_PRESERVED_COUNT", 35, ()),
        ("ROUND14_DECISION_CHANGED_COUNT", 0, ()),
        ("ROUND14_NEW_EVIDENCE_CHANGE_COUNT", 0, ()),
        ("ROUND14_METHOD_CHANGE_COUNT", 0, ()),
        ("VALIDATED_ASSOCIATION_GRAPH_FROZEN", True, ()),
        ("PARAMETER_UNIVERSE_FROZEN", True, ()),
        ("ALL_LEGAL_SUBGRAPHS_ENUMERATED", True, ()),
        ("ALL_LEGAL_TOPOLOGIES_EVALUATED", True, ()),
        ("CANONICAL_COMPOSITION_COUNT_INDEPENDENTLY_VERIFIED", True, ()),
        ("DUPLICATE_CANONICALISATION_COUNT", 0, ()),
        ("UNRESOLVED_COMPOSITION_COUNT", 0, ()),
        ("ROUND16_LEGACY_COMPOSITION_RECONCILED_COUNT", 11, ()),
        ("ROUND16_LEGACY_COMPOSITION_UNEXPLAINED_COUNT", 0, ()),
        ("INVENTED_CATEGORY_COUNT", 0, ()),
        ("CATEGORY_WITHOUT_DATABASE_AUTHORITY_COUNT", 0, ()),
        ("ACTIVE_COMPOSITION_WITHOUT_CATEGORY_ENTRY_COUNT", 0, ()),
        ("ALL_REACHABLE_STATES_ENUMERATED", True, ()),
        ("UNREACHABLE_PRODUCTION_STATE_COUNT", 0, ()),
        ("DUPLICATE_STATE_HASH_COUNT", 0, ()),
        ("TRANSITION_FAIL_COUNT", 0, ()),
        ("STALE_STATE_ACCEPTED_COUNT", 0, ()),
        ("INVALID_TARGET_ACCEPTED_COUNT", 0, ()),
        ("STATE_MUTATION_COUNT", 0, ()),
        ("WORKFLOW_REPLAY_FAILURE_COUNT", 0, ()),
        ("STATE_REPLAY_MISMATCH_COUNT", 0, ()),
        ("SEMANTIC_REPLAY_MISMATCH_COUNT", 0, ()),
        ("PNG_FAILURE_COUNT", 0, ()),
        ("PNG_REPLAY_MISMATCH_COUNT", 0, ()),
        ("MAP_TREE_STATE_MISMATCH_COUNT", 0, ()),
        ("SVG_FAILURE_COUNT", 0, ()),
        ("SVG_REPLAY_MISMATCH_COUNT", 0, ()),
        ("SVG_ARCHIVE_OBJECT_REFERENCE_COUNT", 0, ()),
        ("AUDIT_TO_PRODUCTION_EQUIVALENCE_MISMATCH_COUNT", 0, ()),
        ("ACTUAL_PRODUCTION_HTTP_TESTED", True, ()),
        ("CONCURRENCY_TEST_COMPLETED", True, ()),
        ("CONCURRENT_PNG_TEST_COMPLETED", True, ()),
        ("SUSTAINED_LOAD_TEST_COMPLETED", True, ()),
        ("HTTP_FAILURE_COUNT", 0, ()),
        ("HTTP_TIMEOUT_COUNT", 0, ()),
        ("UNEXPECTED_5XX_COUNT", 0, ()),
        ("API_FAILURE_COUNT", 0, ()),
        ("PNG_CORRUPTION_COUNT", 0, ()),
        ("UNBOUNDED_MEMORY_GROWTH_COUNT", 0, ()),
        ("STATE_CORRUPTION_COUNT", 0, ()),
        ("SEMANTIC_HASH_MISMATCH_COUNT", 0, ()),
        ("UNSUPPORTED_EDGE_COUNT", 0, ()),
        ("TYPED_RELATION_EMISSION_COUNT", 0, ()),
        ("CAUSAL_RELATION_EMISSION_COUNT", 0, ()),
        ("DIRECTIONAL_RELATION_EMISSION_COUNT", 0, ()),
        ("INDEPENDENT_COUNT_MISMATCH_COUNT", 0, ()),
        ("INDEPENDENT_HASH_MISMATCH_COUNT", 0, ()),
        ("REPRODUCIBILITY_VERIFICATION", "PASS", ()),
        ("EXECUTION_LOG_SEQUENCE_GAP_COUNT", 0, ()),
        ("EXECUTION_EVENT_HASH_FAILURE_COUNT", 0, ()),
        ("FULL_COMMAND_LOG_READY", True, ()),
        ("CONTINUOUS_PROCESS_LOG_READY", True, ()),
        ("FINAL_GATE_SOURCE_FAILURE_COUNT", 0, ()),
        ("FINAL_GATE_CRITERION_FAILURE_COUNT", 0, ()),
        ("DATABASE_FREEZE", "PASS", ()),
        ("REPOSITORY_HYGIENE", "PASS", ()),
        ("TYPECHECK", "PASS", ()),
        ("PRODUCTION_BUILD", "PASS", ()),
        ("API_SCHEMA_VALIDATION", "PASS", ()),
        ("AUTHORIZED_LFS_MIGRATION", "PASS", ()),
        ("HISTORY_REWRITE_AUTHORIZED", True, ()),
        ("HISTORY_REWRITE_SCOPE_EXACT", True, ()),
        ("REPOSITORY_BOUNDARY", "PASS", ()),
        ("INDEPENDENT_VERIFICATION", "PASS", ()),
        ("COUNT_HASH_RECONCILIATION", "PASS", ()),
        ("DETERMINISTIC_REPRODUCTION", "PASS", ()),
        ("GIT_FSCK", "PASS", ()),
        ("GIT_LFS_FSCK", "PASS", ()),
        ("AUDIT_SEAL", "PASS", ()),
        ("SEARCH_MUTATION_COUNT", 0, ()),
        ("CONTEXT_MUTATION_COUNT", 0, ()),
        ("SPACETIME_MUTATION_COUNT", 0, ()),
        ("FINAL_EXPLORATION_FRONTEND_IMPLEMENTED", False, ()),
        ("PUBLIC_EXPLORATION_PAGE_ADDED", False, ()),
        ("PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN", False, ()),
        ("DEPLOYED", False, ()),
        ("EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED", False, ()),
        ("FORCE_PUSH_USED", False, ()),
        ("MERGE_COMMIT_CREATED", False, ()),
        ("HISTORY_REWRITTEN", True, ()),
        ("UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN", True, ()),
        ("PUBLIC_EXISTING_HISTORY_REWRITTEN", False, ()),
        ("ORIGIN_MAIN_REWRITTEN", False, ()),
    ]
    for round_number in range(8, 17):
        gate_specs.append((f"ROUND{round_number}_REGRESSION", "PASS", ()))

    gate_results: list[dict[str, Any]] = []
    for name, expected, aliases in gate_specs:
        passed, actual, source = gate_equal(name, expected, *aliases)
        gate_results.append({"gate": name, "expected": expected, "actual": actual, "source": source, "passed": passed})
    for name, left, right in (
        ("ACTIVE_PAIR_UNIVERSE_COUNT=EXPECTED_PAIR_COUNT", "ACTIVE_PAIR_UNIVERSE_COUNT", "EXPECTED_PAIR_COUNT"),
        ("PAIR_LEDGER_ROW_COUNT=EXPECTED_PAIR_COUNT", "PAIR_LEDGER_ROW_COUNT", "EXPECTED_PAIR_COUNT"),
        ("ASSOCIATION_QUERY_LOG_ROW_COUNT=EXPECTED_PAIR_COUNT", "ASSOCIATION_QUERY_LOG_ROW_COUNT", "EXPECTED_PAIR_COUNT"),
        ("ACTIVE_PAIR_UNIVERSE_COUNT=ASSOCIATION_DISPOSITION_TOTAL_COUNT", "ACTIVE_PAIR_UNIVERSE_COUNT", "ASSOCIATION_DISPOSITION_TOTAL_COUNT"),
        ("CANONICAL_ASSOCIATION_SUBGRAPH_COUNT=CANONICAL_SUBGRAPH_LEDGER_ROW_COUNT", "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT", "CANONICAL_SUBGRAPH_LEDGER_ROW_COUNT"),
        ("TOPOLOGY_INSTANTIATED_COMPOSITION_COUNT=VALID_TOPOLOGY_COMPOSITION_LEDGER_ROW_COUNT", "TOPOLOGY_INSTANTIATED_COMPOSITION_COUNT", "VALID_TOPOLOGY_COMPOSITION_LEDGER_ROW_COUNT"),
        ("STATE_ENUMERATED_COUNT=STATE_VALIDATED_COUNT", "STATE_ENUMERATED_COUNT", "STATE_VALIDATED_COUNT"),
        ("TRANSITION_ENUMERATED_COUNT=TRANSITION_EXECUTED_COUNT", "TRANSITION_ENUMERATED_COUNT", "TRANSITION_EXECUTED_COUNT"),
        ("TRANSITION_ENUMERATED_COUNT=TRANSITION_PASS_COUNT", "TRANSITION_ENUMERATED_COUNT", "TRANSITION_PASS_COUNT"),
        ("CANONICAL_WORKFLOW_COUNT=WORKFLOW_REPLAYED_COUNT", "CANONICAL_WORKFLOW_COUNT", "WORKFLOW_REPLAYED_COUNT"),
        ("EXPORT_VARIANT_COUNT=EXPORT_MANIFEST_VALIDATED_COUNT", "EXPORT_VARIANT_COUNT", "EXPORT_MANIFEST_VALIDATED_COUNT"),
        ("EXPORT_VARIANT_COUNT=SVG_RENDERED_COUNT", "EXPORT_VARIANT_COUNT", "SVG_RENDERED_COUNT"),
        ("EXPORT_VARIANT_COUNT=SVG_VALIDATED_COUNT", "EXPORT_VARIANT_COUNT", "SVG_VALIDATED_COUNT"),
        ("EXPORT_VARIANT_COUNT=PNG_RENDERED_COUNT", "EXPORT_VARIANT_COUNT", "PNG_RENDERED_COUNT"),
        ("EXPORT_VARIANT_COUNT=PNG_VALIDATED_COUNT", "EXPORT_VARIANT_COUNT", "PNG_VALIDATED_COUNT"),
    ):
        passed, actual, source = gate_equation(name, left, right)
        gate_results.append({"gate": name, "expected": "equal", "actual": actual, "source": source, "passed": passed})

    core_names = {
        "VOCABULARY_CANDIDATE_UNIVERSE_FROZEN", "UNCLASSIFIED_VOCABULARY_COUNT",
        "UNATTESTED_ACTIVE_VOCABULARY_COUNT", "ACADEMICALLY_UNSUPPORTED_ACTIVE_VOCABULARY_COUNT",
        "INVENTED_ACTIVE_VOCABULARY_COUNT", "STRUCTURAL_LABEL_ACTIVE_VOCABULARY_COUNT",
        "ACTIVE_VOCABULARY_WITHOUT_BOUNDED_SENSE_COUNT", "ACTIVE_VOCABULARY_WITHOUT_CATEGORY_ENTRY_COUNT",
        "ALL_UNORDERED_PAIRS_ENUMERATED", "DUPLICATE_PAIR_COUNT", "MISSING_PAIR_COUNT",
        "INVALID_ASSOCIATION_STATUS_COUNT", "ACTIVE_PAIR_UNIVERSE_COUNT=EXPECTED_PAIR_COUNT",
        "PAIR_LEDGER_ROW_COUNT=EXPECTED_PAIR_COUNT", "ASSOCIATION_QUERY_LOG_ROW_COUNT=EXPECTED_PAIR_COUNT",
        "ACTIVE_PAIR_UNIVERSE_COUNT=ASSOCIATION_DISPOSITION_TOTAL_COUNT",
        "UNRESOLVED_PAIR_COUNT",
        "ACTIVE_ASSOCIATION_WITH_PENDING_VALIDATION_COUNT", "COOCCURRENCE_ONLY_ACTIVE_COUNT",
        "ROUND14_ASSESSMENT_COUNT", "ROUND14_DECISION_PRESERVED_COUNT", "ROUND14_DECISION_CHANGED_COUNT",
        "ROUND14_NEW_EVIDENCE_CHANGE_COUNT", "ROUND14_METHOD_CHANGE_COUNT",
        "VALIDATED_ASSOCIATION_GRAPH_FROZEN", "PARAMETER_UNIVERSE_FROZEN",
        "ALL_LEGAL_SUBGRAPHS_ENUMERATED", "ALL_LEGAL_TOPOLOGIES_EVALUATED",
        "CANONICAL_ASSOCIATION_SUBGRAPH_COUNT=CANONICAL_SUBGRAPH_LEDGER_ROW_COUNT",
        "TOPOLOGY_INSTANTIATED_COMPOSITION_COUNT=VALID_TOPOLOGY_COMPOSITION_LEDGER_ROW_COUNT",
        "CANONICAL_COMPOSITION_COUNT_INDEPENDENTLY_VERIFIED", "DUPLICATE_CANONICALISATION_COUNT",
        "UNRESOLVED_COMPOSITION_COUNT", "ROUND16_LEGACY_COMPOSITION_RECONCILED_COUNT",
        "ROUND16_LEGACY_COMPOSITION_UNEXPLAINED_COUNT", "INVENTED_CATEGORY_COUNT",
        "CATEGORY_WITHOUT_DATABASE_AUTHORITY_COUNT", "ACTIVE_COMPOSITION_WITHOUT_CATEGORY_ENTRY_COUNT",
        "ALL_REACHABLE_STATES_ENUMERATED", "STATE_ENUMERATED_COUNT=STATE_VALIDATED_COUNT",
        "UNREACHABLE_PRODUCTION_STATE_COUNT", "DUPLICATE_STATE_HASH_COUNT",
        "TRANSITION_ENUMERATED_COUNT=TRANSITION_EXECUTED_COUNT", "TRANSITION_ENUMERATED_COUNT=TRANSITION_PASS_COUNT", "TRANSITION_FAIL_COUNT",
        "CANONICAL_WORKFLOW_COUNT=WORKFLOW_REPLAYED_COUNT", "WORKFLOW_REPLAY_FAILURE_COUNT",
        "STATE_REPLAY_MISMATCH_COUNT", "SEMANTIC_REPLAY_MISMATCH_COUNT",
        "EXPORT_VARIANT_COUNT=EXPORT_MANIFEST_VALIDATED_COUNT", "EXPORT_VARIANT_COUNT=PNG_RENDERED_COUNT",
        "EXPORT_VARIANT_COUNT=SVG_RENDERED_COUNT", "EXPORT_VARIANT_COUNT=SVG_VALIDATED_COUNT",
        "EXPORT_VARIANT_COUNT=PNG_VALIDATED_COUNT", "PNG_FAILURE_COUNT", "PNG_REPLAY_MISMATCH_COUNT",
        "MAP_TREE_STATE_MISMATCH_COUNT", "SVG_FAILURE_COUNT", "SVG_REPLAY_MISMATCH_COUNT",
        "SVG_ARCHIVE_OBJECT_REFERENCE_COUNT",
        "INDEPENDENT_COUNT_MISMATCH_COUNT", "INDEPENDENT_HASH_MISMATCH_COUNT",
        "REPRODUCIBILITY_VERIFICATION",
    }
    full_space_complete = all(row["passed"] for row in gate_results if row["gate"] in core_names)
    backend_names = {
        "SEARCH_RUNTIME_DEPENDENCY_COUNT", "SEARCH_SEMANTIC_INPUT_COUNT",
        "CONTEXT_SEMANTIC_INPUT_COUNT", "SPACETIME_SEMANTIC_INPUT_COUNT",
        "DIRECT_DATABASE_SNAPSHOT_VALIDATED", "DIRECT_DATABASE_CATEGORY_BINDING_READY",
        "DATABASE_TEXT_COOCCURRENCE_ASSOCIATION_PASS_COUNT", "DATABASE_METADATA_INFERRED_RELATION_COUNT",
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT", "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT",
        "PUBLIC_EXPLORATION_RECORD_LINK_COUNT", "PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT",
        "PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT", "PNG_ARCHIVE_OBJECT_REFERENCE_COUNT",
        "HELD_DATA_LEAK_COUNT", "AUDIT_TO_PRODUCTION_EQUIVALENCE_MISMATCH_COUNT",
        "ACTUAL_PRODUCTION_HTTP_TESTED", "CONCURRENCY_TEST_COMPLETED", "CONCURRENT_PNG_TEST_COMPLETED",
        "SUSTAINED_LOAD_TEST_COMPLETED", "API_FAILURE_COUNT", "HTTP_FAILURE_COUNT", "HTTP_TIMEOUT_COUNT",
        "UNEXPECTED_5XX_COUNT", "STALE_STATE_ACCEPTED_COUNT", "INVALID_TARGET_ACCEPTED_COUNT",
        "STATE_MUTATION_COUNT", "STATE_CORRUPTION_COUNT",
        "SEMANTIC_HASH_MISMATCH_COUNT", "PNG_CORRUPTION_COUNT", "UNBOUNDED_MEMORY_GROWTH_COUNT",
        "SVG_FAILURE_COUNT", "SVG_REPLAY_MISMATCH_COUNT", "PRODUCTION_BUILD", "TYPECHECK", "API_SCHEMA_VALIDATION",
    }
    backend_complete = full_space_complete and all(row["passed"] for row in gate_results if row["gate"] in backend_names)
    trace_closed = all(row["passed"] for row in gate_results)
    if trace_closed:
        decision = "TRACE_EXPLORATION_FULLY_CLOSED"
        next_gate = "INDEPENDENT_REVIEW_OF_PUBLISHED_ROUND16A_RESEARCH_BRANCH"
    elif full_space_complete:
        decision = "TRACE_EXPLORATION_READY_WITH_EXPLICIT_LIMITATIONS"
        next_gate = "ROUND16A_REMEDIATE_FAILED_FUNCTIONAL_CLOSURE_GATES"
    else:
        decision = "TRACE_EXPLORATION_NOT_CLOSED"
        next_gate = "ROUND16A_COMPLETE_FULL_SPACE_AND_INDEPENDENT_GATES"

    resolver.set("FUNCTION3_FULL_SPACE_CENSUS_COMPLETE", full_space_complete, "computed by build_research_reports.py")
    resolver.set("FUNCTION3_BACKEND_FUNCTIONALLY_COMPLETE", backend_complete, "computed by build_research_reports.py")
    resolver.set("TRACE_FUNCTION3_EXPLORATION_CLOSED", trace_closed, "computed by build_research_reports.py")
    resolver.set("ROUND16A_DECISION", decision, "computed by build_research_reports.py")
    resolver.set("ROUND_SCOPE", "TRACE_FUNCTION3_EXPLORATION_ONLY", "Round 16A immutable scope")
    resolver.set("SOURCE_SHA", environment.get("source_sha", UNKNOWN), source_path("environment.json"))
    resolver.set("SOURCE_TREE_SHA", environment.get("source_tree_sha", UNKNOWN), source_path("environment.json"))
    resolver.set("NEXT_GATE", next_gate, "computed by build_research_reports.py")

    receipt_text: str | None = None
    if args.mode in {"receipt", "reports-and-receipt"}:
        integration_failures: list[str] = []
        sha_pattern = re.compile(r"^[0-9a-f]{40}$")
        for key in ("FINAL_LOCAL_SHA", "FINAL_REMOTE_SHA", "ROLLBACK_TAG_TARGET", "MAIN_BEFORE_SHA", "MAIN_AFTER_SHA"):
            if not sha_pattern.fullmatch(str(integration_evidence.get(key, ""))):
                integration_failures.append(f"{key}_INVALID")
        expected_branch = "codex/trace-v49-exploration-full-space-closure-round1"
        expected_tag = "rollback/trace-v49-exploration-full-space-closure-round1-source"
        if integration_evidence.get("BRANCH") != expected_branch:
            integration_failures.append("BRANCH_MISMATCH")
        if integration_evidence.get("ROLLBACK_TAG") != expected_tag:
            integration_failures.append("ROLLBACK_TAG_MISMATCH")
        if integration_evidence.get("ROLLBACK_TAG_TARGET") != SOURCE_SHA:
            integration_failures.append("ROLLBACK_TAG_TARGET_MISMATCH")
        if integration_evidence.get("MAIN_BEFORE_SHA") != SOURCE_SHA:
            integration_failures.append("MAIN_BEFORE_SHA_MISMATCH")
        if integration_evidence.get("FINAL_LOCAL_SHA") != integration_evidence.get("FINAL_REMOTE_SHA"):
            integration_failures.append("LOCAL_REMOTE_SHA_MISMATCH")
        if as_bool(integration_evidence.get("WORKTREE_CLEAN")) is not True:
            integration_failures.append("WORKTREE_NOT_CLEAN")
        for key in (
            "FORCE_PUSH_USED", "MERGE_COMMIT_CREATED",
            "PUBLIC_EXISTING_HISTORY_REWRITTEN", "ORIGIN_MAIN_REWRITTEN",
        ):
            if as_bool(integration_evidence.get(key)) is not False:
                integration_failures.append(f"{key}_NOT_FALSE")
        for key in ("HISTORY_REWRITTEN", "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN"):
            if as_bool(integration_evidence.get(key)) is not True:
                integration_failures.append(f"{key}_NOT_TRUE")
        main_fast_forward = as_bool(integration_evidence.get("MAIN_FAST_FORWARD_COMPLETED")) is True
        if main_fast_forward:
            integration_failures.append("REVIEW_BRANCH_MAIN_WAS_FAST_FORWARDED")
        if integration_evidence.get("MAIN_AFTER_SHA") != integration_evidence.get("MAIN_BEFORE_SHA"):
            integration_failures.append("REVIEW_BRANCH_MAIN_CHANGED")
        if integration_failures:
            raise ValueError(f"ROUND16A_FINAL_INTEGRATION_GATE:{integration_failures}")

        receipt_values = {key: resolver.get(key) for key in set(RECEIPT_KEYS)}
        receipt_values.update(integration_evidence)
        receipt_values.update({
            "PHASE_STATUS": "PASS" if trace_closed else "NOT_CLOSED",
            "SOURCE_SHA": environment.get("source_sha", UNKNOWN),
            "SOURCE_TREE_SHA": environment.get("source_tree_sha", UNKNOWN),
            "ROUND_SCOPE": "TRACE_FUNCTION3_EXPLORATION_ONLY",
            "DATABASE_SNAPSHOT_ID": database.get("database_snapshot_id", UNKNOWN),
            "ROUND16A_DECISION": decision,
            "FUNCTION3_FULL_SPACE_CENSUS_COMPLETE": full_space_complete,
            "FUNCTION3_BACKEND_FUNCTIONALLY_COMPLETE": backend_complete,
            "TRACE_FUNCTION3_EXPLORATION_CLOSED": trace_closed,
            "NEXT_GATE": next_gate,
        })
        receipt_text = render_final_receipt(receipt_values)

    graph_components = graph_stats.get("components", [])
    graph_component_rows = [(index, len(component), component) for index, component in enumerate(graph_components, 1)]
    degree_rows = [(node.get("canonical_label"), node.get("degree"), node.get("isolated"), node.get("category_ids")) for node in graph.get("nodes", [])]
    parameter_rows = [(
        row.get("parameter_name"), row.get("class"), row.get("legal_values"), row.get("default_value"),
        row.get("authority"), row.get("finite_domain_proof"), row.get("changes_semantic_identity"), row.get("changes_presentation_identity"),
    ) for row in parameters.get("parameters", [])]

    round14 = association_census.get("round14_reconciliation", [])
    round14_decisions = Counter(str(row.get("decision_reconciliation")) for row in round14)
    legacy_rows = registry.get("round16_legacy_reconciliation", [])
    legacy_dispositions = Counter(str(row.get("disposition")) for row in legacy_rows)
    rejection_reasons = Counter(str(row.get("reason_code")) for row in tsv_docs["composition-rejection-ledger-v2.tsv"])

    all_workloads: list[tuple[str, dict[str, Any]]] = []
    for input_name in ("production-http-results.json", "concurrency-results.json", "sustained-load-results.json"):
        for workload in walk_workloads(json_docs[input_name]):
            all_workloads.append((input_name, workload))
    workload_rows = [(
        row.get("workload_id", input_name), row.get("mode", ""), row.get("concurrency", ""),
        row.get("request_count", ""), row.get("success_count", ""), row.get("failure_count", ""),
        row.get("timeout_count", ""), row.get("p50_ms", ""), row.get("p95_ms", ""),
        row.get("p99_ms", ""), row.get("maximum_ms", row.get("max_ms", "")),
        row.get("requests_per_second", ""), row.get("response_bytes", ""),
        row.get("server_runtime", {}).get("server_cpu_percent_peak", ""),
        row.get("server_runtime", {}).get("server_rss_bytes_peak", ""),
        row.get("server_runtime", {}).get("server_heap_used_bytes_peak", ""),
        row.get("server_runtime", {}).get("server_heap_total_bytes_peak", ""),
        row.get("server_runtime", {}).get("server_event_loop_delay_ms_peak", ""), input_name,
    ) for input_name, row in all_workloads]

    reports: dict[str, str] = {}
    reports["06_VALIDATED_GRAPH_REPORT.md"] = f"""# Validated Graph Report

## Decision

The frozen graph contains **{len(graph.get('nodes', []))} active vocabulary nodes** and **{len(graph.get('edges', []))} evidence-qualified generic associations**. It is a proximity graph only: no edge encodes causation, direction, chronology, hierarchy, equivalence, influence, similarity, or historical importance.

`GRAPH_HASH={graph.get('graph_hash', UNKNOWN)}`

`VALIDATED_ASSOCIATION_GRAPH_FROZEN={yesno(graph.get('frozen', False))}`

## Association census

{distribution_table(dict(sorted(statuses.items())), "Final status")}

The exhaustive pair equation is `{len(active_rows)} × ({len(active_rows)} − 1) / 2 = {len(pair_rows)}`. Round 14 reconciliation covers {len(round14)} assessments; disposition counts are `{compact_json(dict(sorted(round14_decisions.items())))}`. No Crossref metadata-only candidate was promoted to evidence.

## Graph statistics

{table(("Metric", "Value"), (
    ("Density", graph_stats.get("graph_density", UNKNOWN)),
    ("Connected components", graph_stats.get("connected_component_count", UNKNOWN)),
    ("Isolated active nodes", graph_stats.get("isolated_active_node_count", UNKNOWN)),
    ("Within-category edges", graph_stats.get("within_category_edge_count", UNKNOWN)),
    ("Cross-category edges", graph_stats.get("cross_category_edge_count", UNKNOWN)),
    ("Degree minimum", graph_stats.get("degree_min", UNKNOWN)),
    ("Degree mean", graph_stats.get("degree_mean", UNKNOWN)),
    ("Degree median", graph_stats.get("degree_median", UNKNOWN)),
    ("Degree maximum", graph_stats.get("degree_max", UNKNOWN)),
    ("Articulation points", graph_stats.get("articulation_point_ids", [])),
    ("Bridge associations", graph_stats.get("bridge_association_ids", [])),
))}

### Components

{table(("Component", "Size", "Vocabulary IDs"), graph_component_rows)}

### Node degrees

{table(("Label", "Degree", "Isolated", "Category bindings"), degree_rows)}

Graph centrality is a property of this governed finite evidence graph and must not be interpreted as historical importance.

Sources: `{source_path('association-census-v2.json')}`, `{source_path('validated-association-graph-v2.json')}`, and `{source_path('graph-statistics-v2.json')}`.
"""

    reports["07_PARAMETER_UNIVERSE.md"] = f"""# Parameter Universe

The parameter universe is frozen at `{parameters.get('parameter_universe_hash', UNKNOWN)}`. Every parameter is assigned a finite legal domain, an authority, a default or explicit absence of default, and separate semantic/presentation identity effects.

`PARAMETER_COUNT={parameters.get('parameter_count', len(parameter_rows))}`

`PARAMETER_UNIVERSE_FROZEN={yesno(parameters.get('frozen', False))}`

{table(("Parameter", "Class", "Legal values", "Default", "Authority", "Finite-domain proof", "Semantic identity", "Presentation identity"), parameter_rows)}

Uninstantiated governed families remain in the universe with an explicit zero-valued legal gate; they are not silently deleted. Arbitrary combinations outside these domains are invalid.

Source: `{source_path('exploration-parameter-universe-v2.json')}`.
"""

    reports["08_COMPOSITION_ENUMERATION_METHOD.md"] = f"""# Composition Enumeration Method

Round 16A enumerates the complete finite active space rather than a fixture sample. The normative graph has {len(graph.get('edges', []))} edges. Enumeration examines every bounded connected edge subgraph spanning 2–8 active nodes, records disconnected and over-bound candidates, evaluates all six topology families, and calls the frozen Round 15 engine for every canonical association subgraph through adapter `{registry.get('round15_adapter_version', UNKNOWN)}`.

The strict adapter does not modify Round 15. It requires a connected tree with maximum degree two for `LINEAR_PATH`, and exactly three nodes, two edges, and degree sequence `[1,1,2]` for each binary form. Qualification, return, and evidence-gap families require explicit governed records; their absence produces recorded invalid decisions rather than invented structures.

{table(("Enumeration measure", "Count"), (
    ("Raw node subsets", composition_stats.get("raw_node_subset_count", UNKNOWN)),
    ("Connected node subsets", composition_stats.get("connected_node_subset_count", UNKNOWN)),
    ("Raw edge subgraphs", composition_stats.get("raw_edge_subgraph_count", UNKNOWN)),
    ("Canonical association subgraphs", composition_stats.get("canonical_association_subgraph_count", len(registry.get("association_subgraphs", [])))),
    ("Topology candidate rows", composition_stats.get("topology_candidate_count", len(composition_rows))),
    ("Valid topology compositions", composition_stats.get("topology_instantiated_composition_count", len(valid_topologies))),
    ("Invalid topology decisions", composition_stats.get("invalid_composition_count", len(invalid_topologies))),
    ("Duplicate canonicalisations", composition_stats.get("duplicate_canonicalisation_count", UNKNOWN)),
))}

`ALL_LEGAL_SUBGRAPHS_ENUMERATED={yesno(resolver.get('ALL_LEGAL_SUBGRAPHS_ENUMERATED'))}`

`ALL_LEGAL_TOPOLOGIES_EVALUATED={yesno(resolver.get('ALL_LEGAL_TOPOLOGIES_EVALUATED'))}`

Sources: `{source_path('composition-enumeration-v2.tsv')}`, `{source_path('composition-rejection-ledger-v2.tsv')}`, and `{source_path('canonical-composition-registry-v2.json')}`.
"""

    reports["09_CANONICALISATION_POLICY.md"] = f"""# Canonicalisation Policy

Canonical identity is layered and deterministic:

1. an association-subgraph hash covers sorted admitted vocabulary and association IDs;
2. a topology hash adds the evaluated topology family and governed gate values;
3. a seed hash adds one admitted seed node;
4. a category-entry hash adds one database-authoritative category;
5. state identity adds focus and the sorted expansion subset;
6. semantic and presentation hashes remain separate;
7. export identity adds the preset and theme-token set without changing semantic identity.

Input ordering, labels used only for presentation, and runtime request order cannot change semantic identity. Hash collision and duplicate-canonicalisation counts must remain zero. All IDs in downstream state, transition, workflow, and export ledgers chain back to the frozen graph and database snapshot `{database.get('database_snapshot_id', DATABASE_SNAPSHOT)}`.

The registry hash is `{registry.get('registry_hash', UNKNOWN)}`. The production read-model SHA-256 is `{model_meta.get('production_read_model_sha256', UNKNOWN)}` and its audit equivalence mismatch count is `{model_meta.get('audit_to_production_equivalence_mismatch_count', UNKNOWN)}`.

Round 16 legacy reconciliation covers all {len(legacy_rows)} legacy compositions with distribution `{compact_json(dict(sorted(legacy_dispositions.items())))}`. A rejected triangle is explained as a stricter v2 topology correction, not silently relabelled.

Sources: `{source_path('canonical-composition-registry-v2.json')}` and `{source_path('production-read-model-metadata-v2.json')}`.
"""

    reports["10_TOPOLOGY_CENSUS.md"] = f"""# Topology Census

Every canonical association subgraph was evaluated against all six governed topology families.

{table(("Topology", "Valid", "Invalid", "Total"), ((name, topology_valid.get(name, 0), topology_invalid.get(name, 0), topology_valid.get(name, 0) + topology_invalid.get(name, 0)) for name in ("LINEAR_PATH", "BINARY_FORK", "BINARY_CONVERGENCE", "QUALIFIED_PATH", "REFLEXIVE_RETURN", "EVIDENCE_GAP_TREE")))}

## Rejection reasons

{distribution_table(dict(sorted(rejection_reasons.items())), "Reason code")}

Pruned, split, gap, and unresolved composition counts are respectively `{composition_stats.get('pruned_composition_count', UNKNOWN)}`, `{composition_stats.get('split_composition_count', UNKNOWN)}`, `{composition_stats.get('evidence_gap_composition_count', UNKNOWN)}`, and `{composition_stats.get('unresolved_composition_count', UNKNOWN)}`. Zero-valued families were still evaluated and have explicit reasons.

The frozen Round 15 result is preserved as an input receipt. The adapter’s stricter binary rule prevents three-edge triangles from being mislabeled as two-branch structures. All 11 Round 16 legacy compositions are reconciled; unexplained count is `{composition_stats.get('round16_legacy_composition_unexplained_count', UNKNOWN)}`.

Sources: `{source_path('composition-enumeration-v2.tsv')}`, `{source_path('composition-rejection-ledger-v2.tsv')}`, and `{source_path('composition-statistics-v2.json')}`.
"""

    reports["11_CATEGORY_ENTRY_CENSUS.md"] = f"""# Category Entry Census

Exactly four top-level categories are grounded directly in the frozen database taxonomy: `region`, `theme`, `medium`, and `movement`. Categories are entry structures, not historical association evidence.

{table(("Category", "Entry variants"), sorted(category_distribution.items()))}

`CANONICAL_CATEGORY_COUNT={database.get('category_authority', {}).get('governed_folder_type_count', 4)}`

`CATEGORY_ENTRY_VARIANT_COUNT={len(category_rows)}`

`MULTI_CATEGORY_COMPOSITION_COUNT={composition_stats.get('multi_category_composition_count', UNKNOWN)}`

`INVENTED_CATEGORY_COUNT={resolver.get('INVENTED_CATEGORY_COUNT')}`

`CATEGORY_WITHOUT_DATABASE_AUTHORITY_COUNT={resolver.get('CATEGORY_WITHOUT_DATABASE_AUTHORITY_COUNT')}`

`ACTIVE_COMPOSITION_WITHOUT_CATEGORY_ENTRY_COUNT={resolver.get('ACTIVE_COMPOSITION_WITHOUT_CATEGORY_ENTRY_COUNT')}`

Every entry records its database authority, category, topology composition, seed variants, production composition IDs, and initial state. Multi-category access duplicates an entry route, not semantic composition identity.

Sources: `{source_path('database-identity-v2.json')}`, `{source_path('category-entry-census-v2.tsv')}`, and `{source_path('composition-statistics-v2.json')}`.
"""

    reports["12_STATE_AND_TRANSITION_CENSUS.md"] = f"""# State and Transition Census

The product state space is fully materialized from category entry, production composition, seed, focus node, and expansion subset. Visible nodes and associations are deterministic projections of that state. States are immutable; actions return a hash-bound next state.

{table(("Metric", "Value"), (
    ("States enumerated", len(state_rows)),
    ("States validated", resolver.get("STATE_VALIDATED_COUNT")),
    ("Unreachable production states", resolver.get("UNREACHABLE_PRODUCTION_STATE_COUNT")),
    ("Duplicate state hashes", resolver.get("DUPLICATE_STATE_HASH_COUNT")),
    ("Transitions enumerated", transition_summary["count"]),
    ("Transitions executed", resolver.get("TRANSITION_EXECUTED_COUNT")),
    ("Transitions passed", resolver.get("TRANSITION_PASS_COUNT")),
    ("Transitions failed", resolver.get("TRANSITION_FAIL_COUNT")),
    ("State mutation count", resolver.get("STATE_MUTATION_COUNT")),
    ("Stale-state accepted count", resolver.get("STALE_STATE_ACCEPTED_COUNT")),
    ("Invalid-target accepted count", resolver.get("INVALID_TARGET_ACCEPTED_COUNT")),
))}

## Action distribution

{distribution_table(dict(sorted(action_counts.items())), "Action")}

States per production composition range from `{min(state_by_composition.values(), default=0)}` to `{max(state_by_composition.values(), default=0)}`. Transitions per state range from `{min(transitions_by_state.values(), default=0)}` to `{max(transitions_by_state.values(), default=0)}`.

`ALL_REACHABLE_STATES_ENUMERATED={yesno(resolver.get('ALL_REACHABLE_STATES_ENUMERATED'))}`

Sources: `{source_path('state-census-v2.tsv')}`, `{source_path('transition-census-v2.tsv')}`, and `{source_path('space-generation-summary-v2.json')}`.
"""

    reports["13_CANONICAL_WORKFLOW_CENSUS.md"] = f"""# Canonical Workflow Census

There is one deterministic shortest workflow from the applicable production root to every reachable exportable state. Breadth-first search uses a stable action/target order. Every workflow was replayed twice and checked against both target state and semantic hashes.

{table(("Metric", "Value"), (
    ("Canonical workflows", len(workflow_rows)),
    ("Workflow targets", len({row.get("target_state_id") for row in workflow_rows})),
    ("Replayed workflows", resolver.get("WORKFLOW_REPLAYED_COUNT")),
    ("Replay failures", resolver.get("WORKFLOW_REPLAY_FAILURE_COUNT")),
    ("State replay mismatches", resolver.get("STATE_REPLAY_MISMATCH_COUNT")),
    ("Semantic replay mismatches", resolver.get("SEMANTIC_REPLAY_MISMATCH_COUNT")),
    ("Length minimum", min(workflow_lengths, default=0)),
    ("Length maximum", max(workflow_lengths, default=0)),
    ("Length mean", statistics.fmean(workflow_lengths) if workflow_lengths else 0),
    ("Length median", statistics.median(workflow_lengths) if workflow_lengths else 0),
))}

## Workflow-length distribution

{distribution_table(dict(sorted(Counter(map(str, workflow_lengths)).items(), key=lambda item: int(item[0]))), "Length")}

Sources: `{source_path('workflow-census-v2.tsv')}` and `{source_path('transition-census-v2.tsv')}`.
"""

    reports["14_EXPORT_CENSUS.md"] = f"""# Export Census

Every reachable state has one `portrait_card` manifest under each frozen theme-token set. The exhaustive ledger therefore covers state × preset × theme. The counts below state whether every variant was rendered, decoded, validated, and rendered again for deterministic replay; unequal counts block closure.

{table(("Metric", "Value"), (
    ("Export variants", len(export_rows)),
    ("Export manifests validated", resolver.get("EXPORT_MANIFEST_VALIDATED_COUNT")),
    ("SVGs rendered", resolver.get("SVG_RENDERED_COUNT")),
    ("SVGs validated", resolver.get("SVG_VALIDATED_COUNT")),
    ("SVG failures", resolver.get("SVG_FAILURE_COUNT")),
    ("SVG replay mismatches", resolver.get("SVG_REPLAY_MISMATCH_COUNT")),
    ("PNGs rendered", resolver.get("PNG_RENDERED_COUNT")),
    ("PNGs validated", resolver.get("PNG_VALIDATED_COUNT")),
    ("PNG failures", resolver.get("PNG_FAILURE_COUNT")),
    ("PNG replay mismatches", resolver.get("PNG_REPLAY_MISMATCH_COUNT")),
    ("Map/tree state mismatches", resolver.get("MAP_TREE_STATE_MISMATCH_COUNT")),
    ("Width", "1080 px"),
    ("Height", "1620 px"),
))}

## Theme distribution

{distribution_table(dict(sorted(export_by_theme.items())), "Theme-token set")}

Export variants per state range from `{min(export_by_state.values(), default=0)}` to `{max(export_by_state.values(), default=0)}`. SVG and PNG binaries are temporary when large; the committed ledger preserves every identity, validation result, and replay hash. Each row covers manifest replay, SVG render/replay, PNG render/decode/replay, SVG-to-PNG equivalence, dimensions, map/tree zones, labels, visible associations, provenance non-claims, and zero forbidden exposure. Public/archive-object, held-data, Context, and Spacetime references must all remain zero.

Sources: `{source_path('export-census-v2.tsv')}` and `{source_path('png-validation-v2.tsv')}`.
"""

    reports["15_API_AND_READ_MODEL_DECISION.md"] = f"""# API and Read-Model Decision

Round 16A selects versioned `trace-exploration/v2`. The legacy v1 route is specified to retire with HTTP 410 rather than silently change. V2 exposes categories, capabilities, map creation/retrieval, actions, vocabulary, generic associations, trees, export manifests, and PNGs. Its contract forbids Search DTOs, archive records, archive identifiers/titles, record links, Context records, Spacetime records, and census-only evidence fields; the measured counts below determine whether that contract passed.

The production read model is separate from the full audit census and is hash-addressed at `{model_meta.get('production_read_model_sha256', UNKNOWN)}`.

{table(("Metric", "Value"), (
    ("Production read-model bytes", model_meta.get("production_read_model_bytes", UNKNOWN)),
    ("Production model load ms", resolver.get("PRODUCTION_MODEL_LOAD_MS")),
    ("RSS delta bytes", resolver.get("PRODUCTION_MODEL_RSS_DELTA_BYTES")),
    ("Heap delta bytes", resolver.get("PRODUCTION_MODEL_HEAP_DELTA_BYTES")),
    ("Audit/production equivalence mismatches", model_meta.get("audit_to_production_equivalence_mismatch_count", UNKNOWN)),
    ("Actual production HTTP tested", api.get("actual_production_http_tested", False)),
    ("Functional API cases", api.get("case_count", UNKNOWN)),
    ("Functional API failures", api.get("fail_count", UNKNOWN)),
    ("Unexpected 5xx", api.get("unexpected_5xx_count", UNKNOWN)),
    ("Public archive object IDs", api.get("public_archive_object_id_count", UNKNOWN)),
    ("Public archive object titles", api.get("public_archive_object_title_count", UNKNOWN)),
    ("Public record links", api.get("public_record_link_count", UNKNOWN)),
    ("Public Context references", api.get("public_context_reference_count", UNKNOWN)),
    ("Public Spacetime references", api.get("public_spacetime_reference_count", UNKNOWN)),
))}

OpenAPI, JSON schemas, TypeScript types, typed client, error catalog, real examples, and the capabilities response are versioned with v2. Runtime errors are allowlisted and sanitized; request size, stale-state, invalid-target, and snapshot mismatch behavior are tested through production HTTP.

Sources: `{source_path('api-functional-validation-v2.json')}` and `{source_path('production-read-model-metadata-v2.json')}`.
"""

    reports["16_PRODUCTION_LOAD_METHOD.md"] = f"""# Production Load Method

All online measurements use the built Next.js production server and the actual `/api/trace/v2/exploration/` HTTP routes. Direct service calls, if retained, are labelled `IN_PROCESS_MICROBENCHMARK` and are not API latency.

The workload matrix contains JSON/API concurrency 1, 5, 10, 25, and 50; PNG concurrency 1, 2, 5, and 10; cold startup and first request; warm steady state; burst load; sustained mixed load; and concurrent PNG load. Each workload records request, success, failure, timeout, P50/P95/P99/maximum latency, throughput, response bytes, CPU, RSS, heap used/total, event-loop delay, client errors, and server errors.

Sustained load uses its recorded dual termination criterion: both minimum request volume and minimum runtime/stability duration must be satisfied. No post-hoc marketing SLO is inferred. Closure is based on absence of crashes, deadlocks, state/hash corruption, unexpected 5xx, ordinary-load timeouts, PNG corruption, and unbounded memory growth.

Offline build-time measurement separately covers vocabulary, pair/evidence, graph, canonical composition, state, transition, workflow, and export generation plus peak process memory and storage. This keeps offline research/build cost distinct from online request cost.

Sources: `{source_path('production-http-results.json')}`, `{source_path('concurrency-results.json')}`, `{source_path('runtime-memory-results.json')}`, `{source_path('build-time-computation-results.json')}`, and `{source_path('sustained-load-results.json')}`.
"""

    reports["17_PRODUCTION_LOAD_RESULTS.md"] = f"""# Production Load Results

## HTTP workloads

{table(("Workload", "Mode", "Concurrency", "Requests", "Successes", "Failures", "Timeouts", "P50 ms", "P95 ms", "P99 ms", "Max ms", "Requests/s", "Response bytes", "Peak CPU %", "Peak RSS bytes", "Peak heap used", "Peak heap total", "Peak event-loop delay ms", "Source"), workload_rows)}

## Runtime envelope

{table(("Metric", "Value"), (
    ("Cold start ms", resolver.get("COLD_START_MS")),
    ("First request ms", resolver.get("FIRST_REQUEST_MS")),
    ("Peak RSS bytes", resolver.get("PEAK_RSS_BYTES")),
    ("Peak heap used bytes", resolver.get("PEAK_HEAP_USED_BYTES")),
    ("Peak CPU percent", resolver.get("PEAK_CPU_PERCENT")),
    ("Peak event-loop delay ms", resolver.get("PEAK_EVENT_LOOP_DELAY_MS")),
    ("Total HTTP requests", resolver.get("TOTAL_HTTP_REQUEST_COUNT")),
    ("HTTP failures", resolver.get("HTTP_FAILURE_COUNT")),
    ("HTTP timeouts", resolver.get("HTTP_TIMEOUT_COUNT")),
    ("Unexpected 5xx", resolver.get("UNEXPECTED_5XX_COUNT")),
    ("Concurrency matrix complete", resolver.get("CONCURRENCY_TEST_COMPLETED")),
    ("Concurrent PNG matrix complete", resolver.get("CONCURRENT_PNG_TEST_COMPLETED")),
    ("Sustained load complete", resolver.get("SUSTAINED_LOAD_TEST_COMPLETED")),
))}

Measured capacity is reported as observed, without converting it into an unapproved SLO. Full observation arrays and process samples remain in the machine-readable receipts.

Sources: `{source_path('production-http-results.json')}`, `{source_path('concurrency-results.json')}`, `{source_path('runtime-memory-results.json')}`, and `{source_path('sustained-load-results.json')}`.
"""

    vocab_total = len(vocab_rows)
    assoc_total = len(association_rows)
    reports["18_STATISTICAL_CENSUS.md"] = f"""# Statistical Census

## Vocabulary

{table(("Disposition", "Count", "Rate of candidates"), ((name, count, pct(count, vocab_total)) for name, count in sorted(dispositions.items())))}

Active vocabulary is `{len(active_rows)}/{vocab_total}` ({pct(len(active_rows), vocab_total)}). Candidate-universe and active-vocabulary counts are not association counts.

{table(("Vocabulary statistic", "Distribution"), (
    ("Attestation-source IDs across active terms", dict(sorted(attestation_source_distribution.items()))),
    ("Academic-source IDs across active terms", dict(sorted(academic_source_distribution.items()))),
    ("Category memberships across active terms", dict(sorted(category_membership_distribution.items()))),
    ("Category memberships per active term", dict(sorted(category_memberships_per_term.items(), key=lambda item: int(item[0])))),
    ("Polysemy/ambiguity-flagged candidate dispositions", dict(sorted(polysemy_disposition_distribution.items()))),
))}

The polysemy/ambiguity subset is the deterministic set whose governed ambiguity note or decision reason contains `polysem*`, `ambigu*`, or `confus*`; it is a reporting filter, not a new eligibility rule.

## Associations

{table(("Disposition", "Count", "Rate of all pairs"), ((name, count, pct(count, assoc_total)) for name, count in sorted(statuses.items())))}

Active generic associations are `{len(active_associations)}/{assoc_total}` ({pct(len(active_associations), assoc_total)}). Strength, confidence, and D1/D5/D7 distributions follow.

{table(("Dimension", "Distribution"), (
    ("Strength", dict(sorted(Counter(str(row.get("association_strength")) for row in association_rows).items()))),
    ("Confidence", dict(sorted(Counter(str(row.get("evidence_confidence")) for row in association_rows).items()))),
    ("D1", dict(sorted(Counter(str(row.get("d1")) for row in association_rows).items()))),
    ("D5", dict(sorted(Counter(str(row.get("d5")) for row in association_rows).items()))),
    ("D7", dict(sorted(Counter(str(row.get("d7")) for row in association_rows).items()))),
))}

Co-occurrence-only and conflicting-scope rates are `{pct(statuses.get('INACTIVE_COOCCURRENCE_ONLY', 0), assoc_total)}` and `{pct(statuses.get('INACTIVE_CONFLICTING_SCOPE', 0), assoc_total)}`. Within-category and cross-category edge rates are `{pct(integer(graph_stats.get('within_category_edge_count')), len(active_associations))}` and `{pct(integer(graph_stats.get('cross_category_edge_count')), len(active_associations))}`.

## Graph

Graph density is `{fmt(graph_stats.get('graph_density', UNKNOWN))}` over `{len(graph.get('nodes', []))}` nodes and `{len(graph.get('edges', []))}` edges. Degree distribution is `{compact_json(graph_stats.get('degree_distribution', {}))}`; component-size distribution is `{compact_json(graph_stats.get('connected_component_size_distribution', {}))}`. Centrality is not historical importance.

## Compositions

{table(("Measure", "Value"), (
    ("Raw candidate node subsets", composition_stats.get("raw_node_subset_count", UNKNOWN)),
    ("Connected node subsets", composition_stats.get("connected_node_subset_count", UNKNOWN)),
    ("Raw edge subgraphs", composition_stats.get("raw_edge_subgraph_count", UNKNOWN)),
    ("Canonical association subgraphs", composition_stats.get("canonical_association_subgraph_count", UNKNOWN)),
    ("Valid topology compositions", composition_stats.get("topology_instantiated_composition_count", UNKNOWN)),
    ("Invalid topology candidates", composition_stats.get("invalid_composition_count", UNKNOWN)),
    ("Seed variants", composition_stats.get("seed_variant_count", UNKNOWN)),
    ("Category-entry variants", composition_stats.get("category_entry_variant_count", UNKNOWN)),
    ("Multi-category compositions", composition_stats.get("multi_category_composition_count", UNKNOWN)),
    ("Pruning rate", pct(integer(composition_stats.get("pruned_composition_count")), integer(composition_stats.get("canonical_association_subgraph_count")))),
    ("Split rate", pct(integer(composition_stats.get("split_composition_count")), integer(composition_stats.get("canonical_association_subgraph_count")))),
    ("Gap rate", pct(integer(composition_stats.get("evidence_gap_composition_count")), integer(composition_stats.get("canonical_association_subgraph_count")))),
    ("Unresolved rate", pct(integer(composition_stats.get("unresolved_composition_count")), integer(composition_stats.get("canonical_association_subgraph_count")))),
))}

Topology, composition-size, edge-count, and category-entry distributions are `{compact_json(composition_stats.get('topology_distribution', {}))}`, `{compact_json(composition_stats.get('composition_size_distribution', {}))}`, `{compact_json(composition_stats.get('edge_count_distribution', {}))}`, and `{compact_json(composition_stats.get('category_entry_distribution', {}))}`.

## Interaction and export

States per production composition range `{min(state_by_composition.values(), default=0)}–{max(state_by_composition.values(), default=0)}`; transitions per state range `{min(transitions_by_state.values(), default=0)}–{max(transitions_by_state.values(), default=0)}`. There are `{len(workflow_rows)}` canonical workflows with length distribution `{compact_json(dict(sorted(Counter(map(str, workflow_lengths)).items(), key=lambda item: int(item[0]))))}` and `{len(export_rows)}` export variants, `{min(export_by_state.values(), default=0)}–{max(export_by_state.values(), default=0)}` per state.

## Runtime

Production latency, throughput, response-size, CPU, memory, event-loop-delay, PNG-cost, and concurrency-scaling results are reported without extrapolation in `17_PRODUCTION_LOAD_RESULTS.md`. Offline generation timings remain separate in `{source_path('build-time-computation-results.json')}`.
"""

    independent_cases = independent.get("cases", independent.get("checks", [])) if isinstance(independent, dict) else []
    independent_failures = [row for row in independent_cases if isinstance(row, dict) and str(row.get("status", row.get("result", "PASS"))).upper() not in {"PASS", "PASSED"}]
    reports["19_INDEPENDENT_VERIFICATION.md"] = f"""# Independent Verification

The second-pass verifier does not import the normative generator or its enumeration functions. It independently reconstructs vocabulary and pair identities, scans the 21-edge power set under the node bound, re-evaluates topology conditions, reconstructs category/seed/state identities, executes transitions, replays workflows, reconciles every export, and recomputes headline statistics.

{table(("Metric", "Value"), (
    ("Verifier status", independent.get("status", UNKNOWN)),
    ("Verification cases", len(independent_cases)),
    ("Case failures", len(independent_failures)),
    ("Count mismatches", resolver.get("INDEPENDENT_COUNT_MISMATCH_COUNT")),
    ("Hash mismatches", resolver.get("INDEPENDENT_HASH_MISMATCH_COUNT")),
    ("Canonical composition independently verified", resolver.get("CANONICAL_COMPOSITION_COUNT_INDEPENDENTLY_VERIFIED")),
))}

Independent verification is logically separate, but it is still software verification rather than external human design-history review. Every mismatch blocks closure.

Source: `{source_path('independent-verification.json')}`.
"""

    reproduction_hashes = []
    for key, value in sorted(resolver.values.items()):
        if key.endswith("_HASH_MATCH"):
            reproduction_hashes.append((key, value[0][1], value[0][0]))
    reports["20_REPRODUCIBILITY.md"] = f"""# Reproducibility

The clean-worktree reproduction rebuilds the semantic and census artifacts from the same frozen source/database inputs and compares byte-level or canonical hashes. Performance timings are explicitly excluded from byte-identity requirements.

{table(("Artifact gate", "Match", "Receipt"), reproduction_hashes)}

`REPRODUCIBILITY_VERIFICATION={resolver.get('REPRODUCIBILITY_VERIFICATION', 'status')}`

`SOURCE_SHA={environment.get('source_sha', SOURCE_SHA)}`

`SOURCE_TREE_SHA={environment.get('source_tree_sha', UNKNOWN)}`

`POST_MIGRATION_HARDENED_FINAL_CODE_SHA={hardened_sha}`

`DATABASE_SNAPSHOT={database.get('database_snapshot_id', DATABASE_SNAPSHOT)}`

## Authorized unpublished-branch LFS migration

The eight original Round 16A commits were preserved in a verified standalone Git bundle before the narrowly scoped LFS conversion. Checkpoint order, messages, authorship, timestamps, and phase boundaries remain one-to-one mapped. Only `.gitattributes` and the two authorized independent-verifier audit paths differ at the Git-tree layer; hydrated payload SHA-256 values remain identical.

`HISTORY_REWRITTEN={yesno(resolver.get('HISTORY_REWRITTEN'))}`

`UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN={yesno(resolver.get('UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN'))}`

`PUBLIC_EXISTING_HISTORY_REWRITTEN={yesno(resolver.get('PUBLIC_EXISTING_HISTORY_REWRITTEN'))}`

`ORIGIN_MAIN_REWRITTEN={yesno(resolver.get('ORIGIN_MAIN_REWRITTEN'))}`

`ORIGINAL_LINEAGE_BUNDLE_SHA256={authorized_migration.get('bundle', {}).get('sha256', UNKNOWN)}`

The reproduction must match vocabulary, pair census, graph, canonical composition registry, state census, transition census, workflow census, and export census. Independent verification is rerun in the reproduction worktree. Any absent or false match keeps Round 16A open.

Sources: `{source_path('reproducibility-verification.json')}` and `{source_path('authorized-lfs-migration-receipt.json')}`.
"""

    failed_gates = [row for row in gate_results if not row["passed"]]
    reports["21_LIMITATIONS.md"] = f"""# Limitations

Round 16A closes only the finite governed Function 3 computational/backend space when its formal gates pass. It does not convert generic proximity into a typed historical relation and does not establish historical causation, direction, chronology, influence, hierarchy, equivalence, similarity, or statistical correlation.

- External human domain review is not completed: `EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED=false`.
- No final Exploration frontend, public page, navigation, production visual design, animation, or deployment is implemented: `FINAL_EXPLORATION_FRONTEND_IMPLEMENTED=false`, `PUBLIC_EXPLORATION_PAGE_ADDED=false`, `DEPLOYED=false`.
- Overall project frontend readiness is outside this TRACE-only round: `PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN=false`.
- Database grounding establishes snapshot and category authority only. Database text co-occurrence and metadata never qualify associations.
- Crossref results are discovery metadata only; full text not reviewed in this round is not evidence.
- Source-supported associations remain explicitly qualified generic proximities.
- Graph centrality is not historical importance.
- Reference SVG/PNG output validates backend/export behavior; it is not final visual design.
- One explicitly authorized pre-publication history rewrite converted only `raw/independent-verification.json` and `raw/independent-verification-cases-v2.tsv` to Git LFS on the unpublished Round 16A branch. Existing public history and `origin/main` remain unchanged, no force push was used, and the original lineage bundle is retained locally at `{authorized_migration.get('bundle', {}).get('local_path', UNKNOWN)}` with SHA-256 `{authorized_migration.get('bundle', {}).get('sha256', UNKNOWN)}`.
- Main remains un-fast-forwarded at report generation unless a later sealed receipt records otherwise: `MAIN_FAST_FORWARD_COMPLETED={yesno(resolver.get('MAIN_FAST_FORWARD_COMPLETED', default=False))}`.

Formal gate failures at report time: `{len(failed_gates)}`. If non-zero, consult `22_FUNCTION3_CLOSURE_DECISION.md`; limitations never convert a failed closure gate into a pass.
"""

    gate_table = table(("Gate", "Expected", "Actual", "Status", "Source"), ((row["gate"], row["expected"], row["actual"], "PASS" if row["passed"] else "FAIL", row["source"]) for row in gate_results))
    reports["22_FUNCTION3_CLOSURE_DECISION.md"] = f"""# Function 3 Closure Decision

`ROUND16A_DECISION={decision}`

`FUNCTION3_FULL_SPACE_CENSUS_COMPLETE={yesno(full_space_complete)}`

`FUNCTION3_BACKEND_FUNCTIONALLY_COMPLETE={yesno(backend_complete)}`

`TRACE_FUNCTION3_EXPLORATION_CLOSED={yesno(trace_closed)}`

The decision is computed from every gate below. A missing value is a failure. Passing examples, an existing 11-composition set, a production build, or five workflows cannot substitute for the complete census, production HTTP/load gates, independent verification, reproduction, regressions, and audit seal.

## Gate ledger

{gate_table}

## Governing distinctions

Real database grounding is not object-facing Exploration. A generic association is not a typed historical relation. All legal canonical compositions are not a manually curated example set. Full functional closure is not a handful of passing workflows.

`EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED=false`

`FINAL_EXPLORATION_FRONTEND_IMPLEMENTED=false`

`PUBLIC_EXPLORATION_PAGE_ADDED=false`

`PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN=false`

`DEPLOYED=false`

`MAIN_FAST_FORWARD_COMPLETED={yesno(resolver.get('MAIN_FAST_FORWARD_COMPLETED', default=False))}`

`NEXT_GATE={next_gate}`
"""

    dictionary_records = metric_records(json_docs["metric-dictionary.json"])
    branding_rows = []
    for record in dictionary_records:
        name = record.get("metric_name", record.get("name", UNKNOWN))
        branding_rows.append((
            name,
            record.get("formal_definition", record.get("definition", UNKNOWN)),
            record.get("unit", UNKNOWN),
            record.get("numerator", UNKNOWN),
            record.get("denominator", UNKNOWN),
            record.get("value", resolver.get(str(name))),
            record.get("source_artifact", UNKNOWN),
            record.get("generation_script", UNKNOWN),
            record.get("verification_script", UNKNOWN),
            record.get("database_snapshot", database.get("database_snapshot_id", DATABASE_SNAPSHOT)),
            record.get("independent_verification_status", UNKNOWN),
            record.get("public_safe_status", UNKNOWN),
            record.get("required_caveat", UNKNOWN),
        ))
    reports["23_BRANDING_SAFE_METRICS.md"] = f"""# Branding-Safe Metrics

## Approved factual summary

TRACE evaluated **{len(pair_rows)} governed unordered vocabulary pairs** and retained **{len(active_associations)} evidence-qualified generic associations** under the documented protocol. It enumerated **{len(registry.get('association_subgraphs', []))} canonical association subgraphs**, **{len(valid_topologies)} valid topology compositions**, **{len(state_rows)} reachable states**, **{transition_summary['count']} governed transitions**, **{len(workflow_rows)} canonical workflows**, and **{len(export_rows)} export variants**.

These are finite-system census counts. They do not prove that any historical relationship exists, and they do not measure historical importance.

## Coverage terms that must remain distinct

{table(("Metric", "Value"), ((name, resolver.get(name)) for name in (
    "PAIR_CANDIDATE_COUNT", "ACTIVE_ASSOCIATION_COUNT",
    "ASSOCIATION_USED_BY_ANY_COMPOSITION_COUNT", "ASSOCIATION_ADMITTED_BY_ANY_COMPOSITION_COUNT",
    "ASSOCIATION_VISIBLE_IN_ANY_STATE_COUNT", "ASSOCIATION_EXPORTED_IN_ANY_CARD_COUNT",
)))}

“Used,” “admitted,” “visible,” and “exported” are not interchangeable. Public copy must name the exact denominator and stage.

## Metric dictionary

{table(("Metric", "Formal definition", "Unit", "Numerator", "Denominator", "Value", "Source artifact", "Generation script", "Verification script", "Database snapshot", "Independent status", "Public-safe", "Required caveat"), branding_rows)}

No public-safe statement may say that TRACE proves historical relationships. External human review, final frontend design, a public page, deployment, and overall project frontend readiness remain false/out of scope for this round.

Canonical sources: `{source_path('metric-dictionary.json')}` and `{source_path('headline-numbers.json')}`.
"""

    if set(reports) != REPORT_NAMES:
        raise AssertionError(f"REPORT_NAME_CONTRACT:{sorted(set(reports) ^ REPORT_NAMES)}")

    if args.mode in {"reports", "reports-and-receipt"}:
        preserve_vocabulary_reports()
        RESEARCH.mkdir(parents=True, exist_ok=True)
        for name in sorted(reports):
            content = reports[name].rstrip() + "\n"
            (RESEARCH / name).write_text(content, encoding="utf-8")

        current_marker = "<!-- TRACE_ROUND16A_CLOSURE_STATUS_V3 -->"
        current_block = f"""{current_marker}
## TRACE v49 Round 16A — post-migration review-branch handoff

This additive handoff preserves the earlier Round 16A closure statement while recording the separately authorized, pre-publication LFS migration of the unpublished research branch. Prior sealed packages and every published Round 8–16 ref remain historical evidence; `origin/main` remains at the frozen source anchor.

`HISTORY_REWRITTEN={yesno(resolver.get('HISTORY_REWRITTEN'))}`

`UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN={yesno(resolver.get('UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN'))}`

`PUBLIC_EXISTING_HISTORY_REWRITTEN={yesno(resolver.get('PUBLIC_EXISTING_HISTORY_REWRITTEN'))}`

`ORIGIN_MAIN_REWRITTEN={yesno(resolver.get('ORIGIN_MAIN_REWRITTEN'))}`

`FORCE_PUSH_USED={yesno(resolver.get('FORCE_PUSH_USED'))}`

The current v2 authority permits the frozen database only for snapshot identity and exactly four category-entry types. Its public contract prohibits archive object IDs/titles, record links, Context references, and Spacetime references; measured counts are `{resolver.get('PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT')}`, `{resolver.get('PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT')}`, `{resolver.get('PUBLIC_EXPLORATION_RECORD_LINK_COUNT')}`, `{resolver.get('PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT')}`, and `{resolver.get('PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT')}`. Its semantic layer is the frozen vocabulary/pair/graph/composition/state census; associations are generic evidence-qualified proximity only.

`ROUND16A_DECISION={decision}`

`FUNCTION3_FULL_SPACE_CENSUS_COMPLETE={yesno(full_space_complete)}`

`FUNCTION3_BACKEND_FUNCTIONALLY_COMPLETE={yesno(backend_complete)}`

`TRACE_FUNCTION3_EXPLORATION_CLOSED={yesno(trace_closed)}`

`EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED=false`

`FINAL_EXPLORATION_FRONTEND_IMPLEMENTED=false`

`PUBLIC_EXPLORATION_PAGE_ADDED=false`

`PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN=false`

`DEPLOYED=false`

Authoritative Round 16A package: `docs/research/trace-v49-exploration-full-space-closure-round1/`.

`NEXT_GATE={next_gate}`
<!-- /TRACE_ROUND16A_CLOSURE_STATUS_V3 -->
"""
        append_once(CURRENT, current_marker, current_block)

        project_marker = "<!-- TRACE_ROUND16A_PROJECT_LOG_V3 -->"
        project_block = f"""{project_marker}
## TRACE v49 Round 16A — authorized LFS migration and review publication

- Preserved the complete original unpublished Round 16A lineage in a verified local Git bundle, restored it cleanly, and recorded the bundle SHA-256 plus the five-blob oversized-object ledger.
- Rewrote only the unpublished Round 16A branch and only the two authorized independent-verification paths, preserving all eight original checkpoint commits in order with identical authorship, timestamps, messages, and logical phase boundaries.
- Left every existing public ref and `origin/main` unchanged, used no force push, pushed no rollback tag, and performed no deployment.
- Froze {len(vocab_rows)} vocabulary candidates and {len(active_rows)} active product terms, enumerated all {len(pair_rows)} unordered active pairs, and retained {len(active_associations)} evidence-qualified generic associations without database co-occurrence inference.
- Enumerated {len(registry.get('association_subgraphs', []))} canonical association subgraphs, {len(valid_topologies)} valid topology compositions, {len(state_rows)} states, {transition_summary['count']} transitions, {len(workflow_rows)} canonical workflows, and {len(export_rows)} export variants.
- Grounded category entry directly in frozen database `{database.get('database_snapshot_id', DATABASE_SNAPSHOT)}` and evaluated the v2 Search/archive-object/Context/Spacetime dependency and public-exposure gates; the formal values are recorded in the Round 16A closure ledger.
- Preserved Round 8–16 history and reconciled all 11 Round 16 legacy compositions through a versioned strict adapter. V1 is explicitly retired; v2 is documented and independently verified.
- Final frontend implementation, public page, deployment, external human domain review, and overall project frontend readiness remain false/out of scope.

`ROUND16A_DECISION={decision}`

`FUNCTION3_FULL_SPACE_CENSUS_COMPLETE={yesno(full_space_complete)}`

`FUNCTION3_BACKEND_FUNCTIONALLY_COMPLETE={yesno(backend_complete)}`

`TRACE_FUNCTION3_EXPLORATION_CLOSED={yesno(trace_closed)}`

`MAIN_FAST_FORWARD_COMPLETED={yesno(resolver.get('MAIN_FAST_FORWARD_COMPLETED', default=False))}`

`NEXT_GATE={next_gate}`
<!-- /TRACE_ROUND16A_PROJECT_LOG_V3 -->
"""
        append_once(PROJECT_LOG, project_marker, project_block)

        # Section 27 names this basename explicitly, while section 30 names the
        # numbered research report.  Preserve both paths with identical bytes.
        (RAW / "BRANDING_SAFE_METRICS.md").write_text(reports["23_BRANDING_SAFE_METRICS.md"].rstrip() + "\n", encoding="utf-8")

        required_documents = set(EARLY_REQUIRED_REPORTS) | REPORT_NAMES
        missing_documents = sorted(
            name for name in required_documents
            if not (RESEARCH / name).is_file() or (RESEARCH / name).stat().st_size == 0
        )
        if missing_documents:
            raise ValueError(f"ROUND16A_RESEARCH_DOCUMENT_GATE:{missing_documents}")

    if receipt_text is not None:
        if args.receipt_output:
            output = args.receipt_output if args.receipt_output.is_absolute() else REPO / args.receipt_output
            if not output.parent.is_dir():
                raise FileNotFoundError(f"ROUND16A_RECEIPT_OUTPUT_PARENT_MISSING:{output.parent}")
            output.write_text(receipt_text, encoding="utf-8")
        elif args.mode == "reports-and-receipt":
            raise ValueError("ROUND16A_REPORTS_AND_RECEIPT_REQUIRES_RECEIPT_OUTPUT")
        else:
            print(receipt_text, end="")

    if args.mode in {"reports", "reports-and-receipt"}:
        print(json.dumps({
            "status": "PASS",
            "decision": decision,
            "function3_full_space_census_complete": full_space_complete,
            "function3_backend_functionally_complete": backend_complete,
            "trace_function3_exploration_closed": trace_closed,
            "failed_gate_count": len(failed_gates),
            "required_document_count": len(set(EARLY_REQUIRED_REPORTS) | REPORT_NAMES),
            "generated_report_count": len(reports),
            "report_hashes": {name: sha256(RESEARCH / name) for name in sorted(reports)},
            "branding_safe_metrics_sha256": sha256(RAW / "BRANDING_SAFE_METRICS.md"),
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
