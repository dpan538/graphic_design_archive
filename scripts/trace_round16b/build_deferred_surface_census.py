#!/usr/bin/env python3
"""Build the deterministic Round 16B checkpoint-004 deferred-surface census.

The builder is deliberately additive: checkpoint-003 v1 artifacts are immutable
inputs.  It executes the twenty deferred local-surface zero-emission selectors,
the frozen SQLite metadata-discovery selector, and writes v2 review-family
ledgers.  Nothing produced here is a governed association or an active fact.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
RESEARCH = REPO / "docs/research/trace-v49-exploration-higher-order-association-closure-round16b"

AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORIZED_SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_CHECKPOINT_SHA = "df8aa185910d501daf5a4a5dded8674fdc8a0d87"
SQLITE_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
SELECTOR_VERSION = "trace-round16b-deferred-surface-selector-v2"
NORMALIZATION_VERSION = "trace-round16b-nfkc-casefold-nonalnum-space-longest-first-v1"
DATABASE_SELECTOR_SQL_VERSION = "trace-round16b-database-discovery-sql-v1"

INVENTORY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-surface-inventory.tsv"
CROSSWALK_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/concept-sense-crosswalk-v1.tsv"
V1_OCCURRENCE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/candidate-trigger-occurrence-ledger-v1.tsv"
V1_FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-family-ledger-v1.tsv"
V1_SURFACE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-surface-disposition-ledger-v1.tsv"
V1_CENSUS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-census-v1.json"
SQLITE_PATH = "data/prefreeze_candidate_v48.sqlite"

R09_BIB = "docs/research/trace-v49-design-history-relation-vocabulary-round1/03_SCHOLARLY_SOURCE_REGISTRY.tsv"
R09_REJECTED = "docs/research/trace-v49-design-history-relation-vocabulary-round1/12_REJECTED_AND_DEFERRED_TERMS.tsv"
R10_BIB = "docs/research/trace-v49-design-history-relation-grammar-round1/03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv"
R10_PAIRS = "docs/research/trace-v49-design-history-relation-grammar-round1/08_ORDERED_PAIR_COMPATIBILITY_MATRIX.tsv"
R10_GAPS = "docs/research/trace-v49-design-history-relation-grammar-round1/20_VOCABULARY_GAP_REGISTER.tsv"
R11_CONSTRAINTS = "docs/research/trace-v49-exploration-constraint-kernel-round1/04_CONSTRAINT_REGISTRY.tsv"
R11_FIXTURES = "docs/research/trace-v49-exploration-constraint-kernel-round1/08_SYNTHETIC_FIXTURE_REGISTRY.tsv"
R11_ADVERSARIAL = "docs/research/trace-v49-exploration-constraint-kernel-round1/15_ADVERSARIAL_TEST_MATRIX.tsv"
R12_FREEZE = "docs/research/trace-v49-exploration-inquiry-flow-round1/02_RESEARCH_CANDIDATE_FREEZE.json"
R12_PAIRS = "docs/research/trace-v49-exploration-inquiry-flow-round1/05_PAIR_QUESTION_EVIDENCE_COVERAGE.tsv"
R12_SEEDS = "docs/research/trace-v49-exploration-inquiry-flow-round1/08_INQUIRY_SEED_REGISTRY.tsv"
R12_INSTANCES = "docs/research/trace-v49-exploration-inquiry-flow-round1/11_RESEARCH_INSTANCE_REGISTRY.tsv"
R13_BIB = "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv"
R13_PAIRS = "docs/research/trace-v49-exploration-composition-review-round1/05_PAIR_DECISION_REGISTRY.tsv"
R13_ACTIVATION = "docs/research/trace-v49-exploration-composition-review-round1/14_ACTIVATION_CANDIDATE_PACKAGE.json"
R13_HUMAN = "docs/research/trace-v49-exploration-composition-review-round1/16_EXTERNAL_DOMAIN_REVIEW_REGISTRY.tsv"
R14_NARY_RESULT = "docs/audits/v49-exploration-association-calibration-round1/raw/nary-validation.tsv"
R14_NARY_FIXTURE = "scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json"
R14_PROVENANCE = "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv"
R16A_EVIDENCE = "docs/audits/v49-exploration-full-space-closure-round1/raw/association-evidence-ledger-v2.tsv"
R16A_PARAMETERS = "docs/audits/v49-exploration-full-space-closure-round1/raw/exploration-parameter-universe-v2.json"
R16A_QUERY_LOG = "docs/audits/v49-exploration-full-space-closure-round1/raw/association-query-log-v2.jsonl"

OUTPUT_SCHEMAS: dict[str, list[str]] = {
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
        "excluded_rejected_matches_json", "arity",
        "metadata_status", "support_status", "rights_status", "selector_version",
        "database_sha256", "record_sha256",
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
    "candidate-trigger-occurrence-ledger-v2.tsv": [],
    "local-candidate-family-ledger-v2.tsv": [],
    "local-surface-disposition-ledger-v2.tsv": [],
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


def row_hash(value: Any) -> str:
    return sha256_text(canonical_json(value))


def stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}:{row_hash(value)}"


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(relative: str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def read_jsonl(relative: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (REPO / relative).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    path.write_text(buffer.getvalue(), encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value or "").casefold()
    return " ".join("".join(character if character.isalnum() else " " for character in folded).split())


def finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["record_sha256"] = row_hash(output)
    return output


def normalize_doi(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold().strip()
    normalized = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", normalized)
    normalized = "".join(normalized.split()).rstrip(".,;)")
    return normalized if normalized.startswith("10.") else ""


def normalize_isbn(value: str) -> str:
    normalized = re.sub(r"[^0-9xX]", "", value or "").upper()
    return normalized if len(normalized) in {10, 13} else ""


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    host = (parsed.hostname or "").casefold()
    path = re.sub(r"/+", "/", parsed.path).rstrip("/")
    return f"{host}{path}"


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def build_source_identity_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str], str]]:
    specifications = [
        ("SURF-R09-001", "ROUND9", R09_BIB, "doi_isbn", "stable_publisher_url", "publication"),
        ("SURF-R10-001", "ROUND10", R10_BIB, "doi_isbn", "stable_publisher_url", "publication"),
        ("SURF-R13-001", "ROUND13", R13_BIB, "doi_or_identifier", "stable_url", "venue"),
    ]
    inputs: list[dict[str, Any]] = []
    for surface_id, round_name, path, identifier_field, url_field, venue_field in specifications:
        for source_row in read_tsv(path):
            identifier = source_row[identifier_field]
            doi = normalize_doi(identifier)
            isbn = normalize_isbn(identifier)
            stable_url = source_row[url_field]
            normalized_stable_url = normalize_url(stable_url)
            if doi:
                identity_kind, identity_value = "DOI", doi
            elif isbn:
                identity_kind, identity_value = "ISBN", isbn
            elif normalized_stable_url:
                identity_kind, identity_value = "STABLE_URL", normalized_stable_url
            else:
                identity_kind = "AUTHOR_YEAR_TITLE"
                identity_value = "|".join(
                    normalize_text(source_row[field]) for field in ("authors", "year", "title")
                )
            identity_key = f"{identity_kind}:{identity_value}"
            inputs.append({
                "surface_id": surface_id,
                "round": round_name,
                "source_path": path,
                "source_record_id": source_row["source_id"],
                "canonical_source_id": stable_id("R16B-SOURCE", identity_key),
                "canonical_identity_kind": identity_kind,
                "canonical_identity_value": identity_value,
                "authors": source_row["authors"],
                "year": source_row["year"],
                "title": source_row["title"],
                "venue": source_row[venue_field],
                "doi_isbn_or_identifier": identifier,
                "stable_url": stable_url,
                "source_record_sha256": row_hash(source_row),
            })
    if len(inputs) != 108:
        raise ValueError(f"bibliographic row count changed: {len(inputs)} != 108")

    by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inputs:
        by_identity[row["canonical_source_id"]].append(row)
    if len(by_identity) != 94:
        raise ValueError(f"canonical source count changed: {len(by_identity)} != 94")
    alias_count = sum(len(rows) - 1 for rows in by_identity.values())
    if alias_count != 14:
        raise ValueError(f"bibliographic alias count changed: {alias_count} != 14")

    membership_rows: list[dict[str, Any]] = []
    rights_rows: list[dict[str, Any]] = []
    canonical_by_member: dict[tuple[str, str], str] = {}
    for canonical_source_id, members in sorted(by_identity.items()):
        ordered = sorted(members, key=lambda item: (item["round"], item["source_path"], item["source_record_id"]))
        representative = ordered[0]
        member_ids = [f"{item['surface_id']}:{item['source_record_id']}" for item in ordered]
        for index, item in enumerate(ordered):
            canonical_by_member[(item["surface_id"], item["source_record_id"])] = canonical_source_id
            membership_rows.append(finalize_row({
                **item,
                "membership_id": stable_id("R16B-SOURCE-MEMBERSHIP", {
                    "surface_id": item["surface_id"], "source_record_id": item["source_record_id"]
                }),
                "membership_role": "CANONICAL_REPRESENTATIVE" if index == 0 else "CROSS_ROUND_ALIAS",
                "representative_source_record_id": representative["source_record_id"],
                "rights_review_status": "PENDING_RIGHTS_AND_ACCESS_REVIEW",
                "evidence_use_status": "BIBLIOGRAPHIC_IDENTITY_ONLY_NOT_ASSOCIATION_EVIDENCE",
            }))
        rights_rows.append(finalize_row({
            "canonical_source_id": canonical_source_id,
            "canonical_identity_kind": representative["canonical_identity_kind"],
            "canonical_identity_value": representative["canonical_identity_value"],
            "representative_surface_id": representative["surface_id"],
            "representative_source_path": representative["source_path"],
            "representative_source_record_id": representative["source_record_id"],
            "member_count": len(ordered),
            "member_ids_json": canonical_json(member_ids),
            "authors": representative["authors"],
            "year": representative["year"],
            "title": representative["title"],
            "venue": representative["venue"],
            "doi_isbn_or_identifier": representative["doi_isbn_or_identifier"],
            "stable_url": representative["stable_url"],
            "rights_review_status": "PENDING",
            "text_access_status": "NOT_REVIEWED",
            "locator_review_status": "NOT_REVIEWED",
            "association_evidence_status": "NOT_EVIDENCE_METADATA_IDENTITY_ONLY",
            "required_next_action": (
                "Resolve lawful text access and reuse rights, inspect source text at a stable locator, "
                "and perform bounded-sense group review before any evidence use."
            ),
        }))
    return (
        sorted(membership_rows, key=lambda row: (row["canonical_source_id"], row["membership_id"])),
        sorted(rights_rows, key=lambda row: row["canonical_source_id"]),
        canonical_by_member,
    )


def build_round16a_alias_ledgers() -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]],
    dict[str, str], dict[str, list[str]],
]:
    evidence_rows = read_tsv(R16A_EVIDENCE)
    provenance_by_id = {row["evidence_id"]: row for row in read_tsv(R14_PROVENANCE)}
    common_fields = [
        "evidence_channel", "source_id", "source_kind", "creator", "year", "title",
        "locator", "stable_url", "doi", "domain_alignment", "association_context",
        "source_metadata_verified", "evidence_verified",
    ]
    evidence_aliases: list[dict[str, Any]] = []
    evidence_alias_id_by_ledger: dict[str, str] = {}
    for row in evidence_rows:
        if row["evidence_verified"] != "true":
            continue
        if not row["ledger_id"].startswith("R16A-R14-"):
            raise ValueError(f"verified Round16A evidence is not an R14 derivative: {row['ledger_id']}")
        round14_id = row["ledger_id"][len("R16A-"):]
        upstream = provenance_by_id.get(round14_id)
        if upstream is None:
            raise ValueError(f"missing Round14 provenance alias target: {round14_id}")
        differing = [field for field in common_fields if row[field] != upstream[field]]
        if differing:
            raise ValueError(f"Round16A evidence derivative differs at {round14_id}: {differing}")
        alias_id = stable_id("R16B-R16A-EVIDENCE-ALIAS", row["ledger_id"])
        evidence_alias_id_by_ledger[row["ledger_id"]] = alias_id
        evidence_aliases.append(finalize_row({
            "alias_id": alias_id,
            "round16a_ledger_id": row["ledger_id"],
            "round14_evidence_id": round14_id,
            "pair_id": row["pair_id"],
            "source_id": row["source_id"],
            "common_field_count": len(common_fields),
            "common_fields_json": canonical_json(common_fields),
            "exact_match": "true",
            "derivative_rule": "STRIP_R16A_PREFIX_AND_COMPARE_13_COMMON_FIELDS",
            "net_new_evidence_object_count": 0,
        }))
    if len(evidence_aliases) != 61:
        raise ValueError(f"Round16A verified evidence alias count changed: {len(evidence_aliases)} != 61")

    query_rows = read_jsonl(R16A_QUERY_LOG)
    metadata_evidence = {
        (row["pair_id"], row["source_id"]): row
        for row in evidence_rows if row["evidence_channel"] == "CROSSREF_DISCOVERY_METADATA"
    }
    if len(metadata_evidence) != 2325:
        raise ValueError(f"Round16A metadata evidence count changed: {len(metadata_evidence)} != 2325")
    query_aliases: list[dict[str, Any]] = []
    query_alias_ids_by_query: dict[str, list[str]] = defaultdict(list)
    lead_occurrences: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()
    for query in query_rows:
        if query["accepted_source_ids"] or query["result_review_status"] == "ACCEPTED":
            raise ValueError(f"query unexpectedly contains accepted metadata: {query['query_id']}")
        for result in query["candidate_results"]:
            key = (query["pair_id"], result["candidate_source_id"])
            ledger = metadata_evidence.get(key)
            if ledger is None or key in seen_pairs:
                raise ValueError(f"metadata query/evidence alias is not exact and unique: {key}")
            seen_pairs.add(key)
            comparisons = {
                "source_id": result["candidate_source_id"],
                "title": result["title"],
                "stable_url": result["url"],
                "doi": result["doi"],
                "source_kind": result["type"],
            }
            if any(ledger[field] != value for field, value in comparisons.items()):
                raise ValueError(f"metadata query/evidence derivative differs: {key}")
            alias_id = stable_id("R16B-R16A-QUERY-ALIAS", {
                "query_id": query["query_id"], "candidate_source_id": result["candidate_source_id"]
            })
            query_alias_ids_by_query[query["query_id"]].append(alias_id)
            query_aliases.append(finalize_row({
                "alias_id": alias_id,
                "query_id": query["query_id"],
                "pair_id": query["pair_id"],
                "candidate_source_id": result["candidate_source_id"],
                "rank": result["rank"],
                "round16a_ledger_id": ledger["ledger_id"],
                "doi": result["doi"],
                "title": result["title"],
                "stable_url": result["url"],
                "exact_match": "true",
                "derivative_rule": "EXACT_PAIR_ID_AND_SOURCE_ID_PLUS_FIVE_COMMON_METADATA_FIELDS",
                "net_new_evidence_object_count": 0,
            }))
            lead_occurrences[normalize_doi(result["doi"])].append((query, result))
    if len(query_aliases) != 2325 or seen_pairs != set(metadata_evidence):
        raise ValueError("Round16A query-result alias coverage is not exactly 2,325 one-to-one rows")
    if len(lead_occurrences) != 101 or "" in lead_occurrences:
        raise ValueError(f"metadata lead DOI count changed: {len(lead_occurrences)} != 101")

    metadata_leads: list[dict[str, Any]] = []
    for doi, occurrences in sorted(lead_occurrences.items()):
        representative = min(occurrences, key=lambda item: (item[1]["rank"], item[0]["query_id"]))[1]
        metadata_leads.append(finalize_row({
            "metadata_lead_id": stable_id("R16B-METADATA-LEAD", f"DOI:{doi}"),
            "canonical_doi": doi,
            "candidate_source_ids_json": canonical_json(sorted({item[1]["candidate_source_id"] for item in occurrences})),
            "title": representative["title"],
            "stable_url": representative["url"],
            "query_occurrence_count": len(occurrences),
            "query_ids_json": canonical_json(sorted({item[0]["query_id"] for item in occurrences})),
            "pair_ids_json": canonical_json(sorted({item[0]["pair_id"] for item in occurrences})),
            "rank_distribution_json": canonical_json(dict(sorted(Counter(str(item[1]["rank"]) for item in occurrences).items()))),
            "abstract_bearing_occurrence_count": sum(bool(item[1].get("abstract")) for item in occurrences),
            "has_link": bool_text(any(item[1].get("links") for item in occurrences)),
            "review_status": "METADATA_ONLY_TEXT_NOT_REVIEWED",
            "support_status": "NOT_ASSOCIATION_EVIDENCE",
            "rights_and_access_status": "PENDING_LAWFUL_ACCESS_AND_RIGHTS_REVIEW",
            "required_next_action": (
                "Use adaptive source-centred discovery, resolve lawful access, and review locator-bearing text; "
                "metadata, snippets, abstracts, and links remain non-supporting."
            ),
        }))
    if sum(int(row["abstract_bearing_occurrence_count"]) for row in metadata_leads) != 139:
        raise ValueError("metadata abstract-bearing occurrence count changed")
    if sum(row["has_link"] == "true" for row in metadata_leads) != 42:
        raise ValueError("metadata link-bearing lead count changed")
    return (
        sorted(evidence_aliases, key=lambda row: row["alias_id"]),
        sorted(query_aliases, key=lambda row: row["alias_id"]),
        metadata_leads,
        evidence_alias_id_by_ledger,
        query_alias_ids_by_query,
    )


def build_parameter_reconciliation() -> list[dict[str, Any]]:
    payload = read_json(R16A_PARAMETERS)
    rows: list[dict[str, Any]] = []
    obligation_names = {
        "node_set", "association_set", "topology", "qualification_gate",
        "evidence_gap_node_ids", "degree_bound", "maximum_node_count", "pruning", "split",
    }
    for parameter in payload["parameters"]:
        obligation = parameter["parameter_name"] in obligation_names
        if obligation != bool(parameter["changes_semantic_identity"]):
            raise ValueError(f"semantic obligation classification drifted: {parameter['parameter_name']}")
        rows.append(finalize_row({
            "parameter_name": parameter["parameter_name"],
            "parameter_class": parameter["class"],
            "authority": parameter["authority"],
            "legal_values_json": canonical_json(parameter["legal_values"]),
            "changes_semantic_identity": bool_text(parameter["changes_semantic_identity"]),
            "changes_presentation_identity": bool_text(parameter["changes_presentation_identity"]),
            "higher_order_semantic_obligation": bool_text(obligation),
            "round16a_assumption_status": (
                "REQUIRES_HIGHER_ORDER_REJUSTIFICATION" if obligation
                else "BASELINE_MEASUREMENT_OR_PRESENTATION_CONTROL_ONLY"
            ),
            "required_next_action": (
                "Rejustify or replace this semantic bound against first-class higher-order associations; "
                "do not inherit the pair-derived domain." if obligation else
                "Retain only as a Round16A baseline parameter until the v3 reachable product space is regenerated."
            ),
            "source_record_sha256": row_hash(parameter),
        }))
    if len(rows) != 18 or sum(row["higher_order_semantic_obligation"] == "true" for row in rows) != 9:
        raise ValueError("parameter reconciliation must contain 18 rows and nine semantic obligations")
    return sorted(rows, key=lambda row: row["parameter_name"])


CAPTURE_SELECTOR_SQL = """SELECT capture_id, active_surface_id, capture_status, quality_route,
       quality_reason, source_id, source_record_url, source_title,
       source_description, source_notes, source_subjects
FROM capture_records
ORDER BY capture_id"""

TRACE_SELECTOR_SQL = """SELECT o.surface_id, o.trace_object_node_id,
       o.source_url AS object_source_url,
       e.edge_id, e.evidence_url,
       CASE WHEN e.subject_node_id = o.trace_object_node_id
            THEN e.object_node_id ELSE e.subject_node_id END AS opposite_node_id,
       n.label, n.source_url AS node_source_url, n.evidence, n.evidence_status
FROM objects AS o
JOIN object_trace_edges AS ote ON ote.surface_id = o.surface_id
JOIN trace_edges AS e ON e.edge_id = ote.edge_id
JOIN trace_nodes AS n
  ON n.node_id = CASE WHEN e.subject_node_id = o.trace_object_node_id
                      THEN e.object_node_id ELSE e.subject_node_id END
WHERE o.trace_object_node_id IS NOT NULL
  AND e.review_state = 'accepted'
  AND (e.subject_node_id = o.trace_object_node_id
       OR e.object_node_id = o.trace_object_node_id)
  AND COALESCE(e.evidence_url, '') <> ''
  AND COALESCE(e.evidence_text, '') <> ''
  AND COALESCE(n.evidence, '') <> ''
  AND COALESCE(n.source_url, '') <> ''
  AND (n.evidence_status LIKE 'explicit_%'
       OR n.evidence_status LIKE 'stable_%'
       OR n.evidence_status LIKE 'source_verified%')
ORDER BY o.surface_id, e.edge_id, n.node_id"""

SEARCH_DOCUMENT_CONTROL_SQL = """SELECT search_doc_id, document_type, object_or_capture_id, title, body
FROM search_documents
ORDER BY search_doc_id"""


def longest_nonoverlap_matches(
    value: str, label_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    normalized = normalize_text(value)
    if not normalized:
        return []
    occupied: list[tuple[int, int]] = []
    matched: list[dict[str, str]] = []
    alternatives = sorted(
        label_rows,
        key=lambda row: (-len(normalize_text(row["canonical_label"])), normalize_text(row["canonical_label"])),
    )
    for row in alternatives:
        label = normalize_text(row["canonical_label"])
        pattern = re.compile(rf"(?<!\w){re.escape(label)}(?!\w)", re.UNICODE)
        accepted = False
        for match in pattern.finditer(normalized):
            span = match.span()
            if any(not (span[1] <= prior[0] or span[0] >= prior[1]) for prior in occupied):
                continue
            occupied.append(span)
            accepted = True
        if accepted:
            matched.append(row)
    return sorted(matched, key=lambda row: row["canonical_label"])


def build_database_discovery() -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]],
    list[dict[str, Any]], list[dict[str, Any]],
]:
    database_path = REPO / SQLITE_PATH
    actual_database_sha = sha256_file(database_path)
    if actual_database_sha != SQLITE_SHA256:
        raise ValueError(f"frozen SQLite SHA changed: {actual_database_sha} != {SQLITE_SHA256}")

    crosswalk = read_tsv(CROSSWALK_PATH)
    eligible_label_rows = [
        row for row in crosswalk
        if row["disposition"] in {"ACTIVE", "RESEARCH_ONLY", "MERGED_SUPERSEDED"}
        and row["crosswalk_status"] in {"RESOLVED_CANONICAL", "RESOLVED_MERGED_ALIAS"}
    ]
    rejected_label_rows = [row for row in crosswalk if row["disposition"] == "REJECTED"]
    if len(eligible_label_rows) != 53:
        raise ValueError(f"eligible lexical label count changed: {len(eligible_label_rows)} != 53")
    if len({row["canonical_resolution_sense_id"] for row in eligible_label_rows}) != 52:
        raise ValueError("53 eligible lexical labels must resolve to exactly 52 participant senses")
    eligible_by_normalized = {normalize_text(row["canonical_label"]): row for row in eligible_label_rows}

    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    capture_candidates: list[dict[str, Any]] = []
    capture_controls: list[dict[str, Any]] = []
    capture_fields = [
        "source_record_url", "source_title", "source_description", "source_notes", "source_subjects"
    ]
    for sqlite_row in connection.execute(CAPTURE_SELECTOR_SQL):
        row = dict(sqlite_row)
        matched_by_field: dict[str, list[str]] = {}
        rejected_by_field: dict[str, list[str]] = {}
        matched_rows: list[dict[str, str]] = []
        rejected_rows: list[dict[str, str]] = []
        for field in capture_fields:
            field_matches = longest_nonoverlap_matches(row[field] or "", eligible_label_rows)
            field_rejected = longest_nonoverlap_matches(row[field] or "", rejected_label_rows)
            if field_matches:
                matched_by_field[field] = [item["canonical_label"] for item in field_matches]
                matched_rows.extend(field_matches)
            if field_rejected:
                rejected_by_field[field] = [item["canonical_label"] for item in field_rejected]
                rejected_rows.extend(field_rejected)
        resolved_senses = sorted({item["canonical_resolution_sense_id"] for item in matched_rows})
        if len(resolved_senses) < 3:
            continue
        labels_by_sense: dict[str, str] = {}
        for item in sorted(matched_rows, key=lambda value: value["canonical_label"]):
            labels_by_sense.setdefault(item["canonical_resolution_sense_id"], item["canonical_label"])
        stable_locator = f"sqlite:capture_records:capture_id={row['capture_id']}"
        candidate = {
            "selector_branch": "CAPTURE_RECORD_BOUNDED_FIELD_LEXICAL_DISCOVERY",
            "stable_row_locator": stable_locator,
            "source_record_url": row["source_record_url"],
            "matched_fields": {
                **matched_by_field,
                "_capture_governance": {
                    "active_surface_id": row["active_surface_id"],
                    "capture_status": row["capture_status"],
                    "quality_route": row["quality_route"],
                    "quality_reason": row["quality_reason"],
                },
            },
            "matched_node_edge_loci": [],
            "labels": [labels_by_sense[sense] for sense in resolved_senses],
            "senses": resolved_senses,
            "excluded_rejected_matches": sorted({item["canonical_label"] for item in rejected_rows}),
            "source_material": row,
        }
        if row["capture_id"] == "CHWCONTEMP2026V1R0009":
            capture_controls.append(finalize_row({
                "control_id": stable_id("R16B-DB-CAPTURE-CONTROL", row["capture_id"]),
                "stable_row_locator": stable_locator,
                "capture_id": row["capture_id"],
                "source_record_url": row["source_record_url"],
                "eligible_matches_json": canonical_json(candidate["labels"]),
                "excluded_rejected_matches_json": canonical_json(candidate["excluded_rejected_matches"]),
                "matched_fields_json": canonical_json(candidate["matched_fields"]),
                "control_class": "LEXICAL_AMBIGUITY_CONTROL",
                "exclusion_reason": (
                    "translation occurs only in the transcription '[Greek translation below]'; the governed "
                    "translation sense is unresolved here, so the lexical triple cannot emit a participant-set occurrence."
                ),
                "net_trigger_occurrence_count": 0,
                "support_status": "NOT_ASSOCIATION_EVIDENCE",
                "database_sha256": actual_database_sha,
            }))
        elif row["capture_id"] == "WHMZTRACE2026R0009":
            capture_controls.append(finalize_row({
                "control_id": stable_id("R16B-DB-CAPTURE-CONTROL", row["capture_id"]),
                "stable_row_locator": stable_locator,
                "capture_id": row["capture_id"],
                "source_record_url": row["source_record_url"],
                "eligible_matches_json": canonical_json(candidate["labels"]),
                "excluded_rejected_matches_json": canonical_json(candidate["excluded_rejected_matches"]),
                "matched_fields_json": canonical_json(candidate["matched_fields"]),
                "control_class": "CROSS_SECTION_LOCUS_CONFLICT_CONTROL",
                "exclusion_reason": (
                    "The capture concatenates unrelated page sections: production belongs to a residency account "
                    "while education belongs to a later symposium description; there is no single bounded locus."
                ),
                "net_trigger_occurrence_count": 0,
                "support_status": "NOT_ASSOCIATION_EVIDENCE",
                "database_sha256": actual_database_sha,
            }))
        else:
            capture_candidates.append(candidate)

    capture_ids = {item["source_material"]["capture_id"] for item in capture_candidates}
    expected_capture_ids = {
        "DGITRACE2026R0395", "HISTORICALAICTRACE2026V1R0161",
        "HISTORICALAICTRACE2026V1R0206", "LOCTRACE2026I3172E16AA089B6",
    }
    if capture_ids != expected_capture_ids or len(capture_controls) != 2:
        raise ValueError(f"capture locus selector drifted: candidates={sorted(capture_ids)} controls={len(capture_controls)}")
    for candidate in capture_candidates:
        capture_id = candidate["source_material"]["capture_id"]
        if not candidate["source_record_url"].startswith("https://"):
            raise ValueError(f"retained capture locus lacks HTTPS source URL: {capture_id}")
        if capture_id.startswith("HISTORICALAIC") and "Bauhaus" not in candidate["excluded_rejected_matches"]:
            raise ValueError(f"AIC locus did not retain rejected Bauhaus control: {capture_id}")
    dgi = next(item for item in capture_candidates if item["source_material"]["capture_id"] == "DGITRACE2026R0395")
    if dgi["source_material"]["active_surface_id"] is not None or not dgi["source_material"]["capture_status"].startswith("hold_"):
        raise ValueError("DGI lexical lead governance caveat changed")

    trace_by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sqlite_row in connection.execute(TRACE_SELECTOR_SQL):
        row = dict(sqlite_row)
        label_row = eligible_by_normalized.get(normalize_text(row["label"]))
        if label_row is not None:
            trace_by_surface[row["surface_id"]].append({**row, "label_row": label_row})
    trace_candidates: list[dict[str, Any]] = []
    for surface_id, loci in sorted(trace_by_surface.items()):
        resolved_senses = sorted({item["label_row"]["canonical_resolution_sense_id"] for item in loci})
        if len(resolved_senses) < 3:
            continue
        labels_by_sense: dict[str, str] = {}
        for item in sorted(loci, key=lambda value: value["label_row"]["canonical_label"]):
            labels_by_sense.setdefault(
                item["label_row"]["canonical_resolution_sense_id"], item["label_row"]["canonical_label"]
            )
        trace_candidates.append({
            "selector_branch": "DIRECT_OPPOSITE_OBJECT_ACCEPTED_TRACE_ENDPOINT_DISCOVERY",
            "stable_row_locator": f"sqlite:objects+object_trace_edges:surface_id={surface_id}",
            "source_record_url": loci[0]["object_source_url"],
            "matched_fields": {},
            "matched_node_edge_loci": sorted([{
                "edge_id": item["edge_id"],
                "edge_evidence_url": item["evidence_url"],
                "opposite_node_id": item["opposite_node_id"],
                "node_label": item["label"],
                "node_source_url": item["node_source_url"],
                "node_evidence_status": item["evidence_status"],
            } for item in loci], key=lambda value: (value["edge_id"], value["opposite_node_id"])),
            "labels": [labels_by_sense[sense] for sense in resolved_senses],
            "senses": resolved_senses,
            "excluded_rejected_matches": [],
            "source_material": {"surface_id": surface_id, "loci": [
                {key: value for key, value in item.items() if key != "label_row"} for item in loci
            ]},
        })
    expected_trace_surfaces = {
        "SURF-VAM20K-00867", "SURF-VAM20K-03010", "SURF-VAM20K-03052",
        "SURF-VAM20K-03127", "SURF-VAM20K-03163", "SURF-VAM20K-03165",
        "SURF-VAM20K-03166",
    }
    if {item["source_material"]["surface_id"] for item in trace_candidates} != expected_trace_surfaces:
        raise ValueError("direct-opposite-object TRACE selector changed")
    for candidate in trace_candidates:
        if not candidate["source_record_url"].startswith("https://"):
            raise ValueError(f"retained TRACE locus lacks HTTPS source URL: {candidate['stable_row_locator']}")

    candidates = capture_candidates + trace_candidates
    database_occurrences: list[dict[str, Any]] = []
    family_members: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        senses = tuple(candidate["senses"])
        participant_set_key = sha256_text(canonical_json(list(senses)))
        database_family_id = f"R16B-DB-FAMILY:{participant_set_key}"
        occurrence_material = {
            "selector_branch": candidate["selector_branch"],
            "stable_row_locator": candidate["stable_row_locator"],
            "participant_sense_ids": list(senses),
            "selector_version": SELECTOR_VERSION,
            "database_sha256": actual_database_sha,
        }
        occurrence_id = stable_id("R16B-DB-OCC", occurrence_material)
        output = finalize_row({
            "database_occurrence_id": occurrence_id,
            "database_family_id": database_family_id,
            "selector_branch": candidate["selector_branch"],
            "stable_row_locator": candidate["stable_row_locator"],
            "source_record_url": candidate["source_record_url"],
            "matched_fields_json": canonical_json(candidate["matched_fields"]),
            "matched_node_edge_loci_json": canonical_json(candidate["matched_node_edge_loci"]),
            "raw_participant_labels_json": canonical_json(candidate["labels"]),
            "participant_sense_ids_json": canonical_json(list(senses)),
            "excluded_rejected_matches_json": canonical_json(candidate["excluded_rejected_matches"]),
            "arity": len(senses),
            "metadata_status": "METADATA_OR_LEXICAL_DISCOVERY_ONLY_PENDING_BOUNDED_SENSE_REVIEW",
            "support_status": "NOT_ASSOCIATION_EVIDENCE",
            "rights_status": "PENDING_SOURCE_TEXT_RIGHTS_AND_ACCESS_REVIEW",
            "selector_version": SELECTOR_VERSION,
            "database_sha256": actual_database_sha,
        })
        database_occurrences.append(output)
        family_members[senses].append({"database": output, "candidate": candidate})
    if len(database_occurrences) != 11 or len(family_members) != 4:
        raise ValueError(
            f"revised database discovery count changed: {len(database_occurrences)}/"
            f"{len(family_members)} != 11/4"
        )

    database_families: list[dict[str, Any]] = []
    merged_occurrences: list[dict[str, Any]] = []
    for senses, members in sorted(family_members.items()):
        participant_set_key = sha256_text(canonical_json(list(senses)))
        candidate_id = f"R16B-LOCAL-FAMILY:{participant_set_key}"
        labels_by_sense: dict[str, str] = {}
        for member in members:
            for sense, label in zip(member["candidate"]["senses"], member["candidate"]["labels"]):
                labels_by_sense.setdefault(sense, label)
        labels = [labels_by_sense[sense] for sense in senses]
        occurrence_ids = sorted(member["database"]["database_occurrence_id"] for member in members)
        database_family_id = f"R16B-DB-FAMILY:{participant_set_key}"
        database_families.append(finalize_row({
            "database_family_id": database_family_id,
            "candidate_id": candidate_id,
            "participant_set_key": participant_set_key,
            "participant_sense_ids_json": canonical_json(list(senses)),
            "canonical_labels_json": canonical_json(labels),
            "arity": len(senses),
            "database_occurrence_count": len(members),
            "database_occurrence_ids_json": canonical_json(occurrence_ids),
            "selector_branches_json": canonical_json(sorted({member["candidate"]["selector_branch"] for member in members})),
            "metadata_status": "METADATA_OR_LEXICAL_DISCOVERY_ONLY_PENDING_BOUNDED_SENSE_REVIEW",
            "evidence_review_status": "NOT_STARTED",
            "global_coherence_status": "NOT_REVIEWED",
            "product_eligibility": "INELIGIBLE_PENDING_GOVERNED_REVIEW",
            "association_identity_frozen": "false",
        }))
        for member in members:
            candidate = member["candidate"]
            database = member["database"]
            scope_material = {
                "source_path": SQLITE_PATH,
                "record_refs": [database["stable_row_locator"]],
                "locator": database["source_record_url"],
                "content_hashes": [database["record_sha256"]],
            }
            identity_material = {
                "trigger_class": candidate["selector_branch"],
                "source_path": SQLITE_PATH,
                "record_refs": [database["stable_row_locator"]],
                "locator": database["source_record_url"],
                "content_hashes": [database["record_sha256"]],
                "raw_participant_sense_ids": list(senses),
                "selector_version": SELECTOR_VERSION,
            }
            occurrence = {
                "trigger_occurrence_id": stable_id("R16B-TRIGGER-OCC", identity_material),
                "trigger_id": "TRG-009",
                "trigger_class": candidate["selector_branch"],
                "input_surface_id": "SURF-DB-001",
                "source_path": SQLITE_PATH,
                "input_record_refs_json": canonical_json([database["stable_row_locator"]]),
                "locator": database["source_record_url"],
                "content_hashes_json": canonical_json([database["record_sha256"]]),
                "raw_participant_labels_json": canonical_json(labels),
                "raw_participant_sense_ids_json": canonical_json(list(senses)),
                "participant_sense_ids_json": canonical_json(list(senses)),
                "participant_set_key": participant_set_key,
                "scope_hypothesis_id": stable_id("R16B-SCOPE-HYP", scope_material),
                "polarity": "METADATA_LEXICAL_DISCOVERY_ONLY",
                "emission_kind": "DATABASE_DISCOVERY_REVIEW_FAMILY",
                "candidate_id": candidate_id,
                "incidental_or_excluded_labels_json": database["excluded_rejected_matches_json"],
                "notes": (
                    "Database locus is a non-supporting discovery trigger pending exact bounded-sense, "
                    "source-text, rights, and global-coherence review."
                ),
                "selector_version": SELECTOR_VERSION,
            }
            occurrence["occurrence_sha256"] = row_hash(occurrence)
            merged_occurrences.append(occurrence)

    search_rejections: list[dict[str, Any]] = []
    for sqlite_row in connection.execute(SEARCH_DOCUMENT_CONTROL_SQL):
        row = dict(sqlite_row)
        matches = longest_nonoverlap_matches(f"{row['title']}\n{row['body']}", eligible_label_rows)
        resolved = sorted({item["canonical_resolution_sense_id"] for item in matches})
        if len(resolved) < 3:
            continue
        labels_by_sense: dict[str, str] = {}
        for item in matches:
            labels_by_sense.setdefault(item["canonical_resolution_sense_id"], item["canonical_label"])
        labels = [labels_by_sense[sense] for sense in resolved]
        locator = f"sqlite:search_documents:search_doc_id={row['search_doc_id']}"
        search_rejections.append(finalize_row({
            "rejection_id": stable_id("R16B-DB-SEARCH-CONTROL", row["search_doc_id"]),
            "stable_row_locator": locator,
            "search_doc_id": row["search_doc_id"],
            "document_type": row["document_type"],
            "object_or_capture_id": row["object_or_capture_id"],
            "matched_labels_json": canonical_json(labels),
            "arity": len(resolved),
            "rejection_reason": (
                "SEARCH_DOCUMENT_BODY_IS_PROJECT_GENERATED_MIXED_TEXT_AND_CANNOT_SUPPLY_"
                "SOURCE_BOUNDED_ASSOCIATION_DISCOVERY"
            ),
            "net_trigger_occurrence_count": 0,
            "database_sha256": actual_database_sha,
        }))
    connection.close()
    if len(search_rejections) != 120:
        raise ValueError(f"search-document rejection control count changed: {len(search_rejections)} != 120")
    return (
        sorted(database_occurrences, key=lambda row: row["database_occurrence_id"]),
        sorted(database_families, key=lambda row: row["database_family_id"]),
        sorted(merged_occurrences, key=lambda row: row["trigger_occurrence_id"]),
        sorted(search_rejections, key=lambda row: row["rejection_id"]),
        sorted(capture_controls, key=lambda row: row["control_id"]),
    )


DEFERRED_SURFACE_SPECS: dict[str, dict[str, str]] = {
    "SURF-R09-001": {"round": "ROUND9", "path": R09_BIB, "ref": "source_id", "class": "BIBLIOGRAPHIC_IDENTITY", "rule": "CANONICALIZE_DOI_THEN_ISBN_THEN_STABLE_URL_THEN_AUTHOR_YEAR_TITLE", "decision": "ZERO_EMISSION_RIGHTS_AND_TEXT_REVIEW_BLOCKED"},
    "SURF-R09-005": {"round": "ROUND9", "path": R09_REJECTED, "ref": "candidate_id", "class": "REJECTED_OR_DEFERRED_SENSE_CONTROL", "rule": "FINAL_DECISION_AND_ADVERSARIAL_STATUS_EXACT", "decision": "ZERO_EMISSION_CONTROL_ONLY"},
    "SURF-R10-001": {"round": "ROUND10", "path": R10_BIB, "ref": "source_id", "class": "BIBLIOGRAPHIC_IDENTITY", "rule": "CANONICALIZE_DOI_THEN_ISBN_THEN_STABLE_URL_THEN_AUTHOR_YEAR_TITLE", "decision": "ZERO_EMISSION_RIGHTS_AND_TEXT_REVIEW_BLOCKED"},
    "SURF-R10-004": {"round": "ROUND10", "path": R10_PAIRS, "ref": "ordered_pair_key", "class": "PAIR_PROJECTION_CONTROL", "rule": "EXACT_ORDERED_PAIR_DECISION_WITHOUT_GROUP_LIFT", "decision": "ZERO_EMISSION_PAIR_CONTROL_ONLY"},
    "SURF-R10-007": {"round": "ROUND10", "path": R10_GAPS, "ref": "gap_id", "class": "OPEN_VOCABULARY_GAP_CONTROL", "rule": "NO_PUBLIC_LABEL_AND_FUTURE_GATE_EXACT", "decision": "ZERO_EMISSION_OPEN_GAP"},
    "SURF-R11-001": {"round": "ROUND11", "path": R11_CONSTRAINTS, "ref": "constraint_id", "class": "SOFTWARE_MODEL_CONSTRAINT_CONTROL", "rule": "STATUS_MUST_EQUAL_PASS", "decision": "ZERO_EMISSION_NON_HISTORICAL_CONTROL"},
    "SURF-R11-002": {"round": "ROUND11", "path": R11_FIXTURES, "ref": "fixture_id", "class": "SYNTHETIC_FIXTURE_CONTROL", "rule": "SYNTHETIC_TRUE_AND_PRODUCTION_EXPORTABLE_FALSE", "decision": "ZERO_EMISSION_SYNTHETIC_CONTROL"},
    "SURF-R11-003": {"round": "ROUND11", "path": R11_ADVERSARIAL, "ref": "case_id", "class": "ADVERSARIAL_EXPECTATION_CONTROL", "rule": "EXPECTED_EQUALS_ACTUAL_AND_STATUS_PASS", "decision": "ZERO_EMISSION_TEST_CONTROL"},
    "SURF-R12-001": {"round": "ROUND12", "path": R12_FREEZE, "ref": "candidateId", "class": "INACTIVE_UNARY_RESEARCH_CANDIDATE", "rule": "PACKAGE_AND_CANDIDATE_ACTIVE_FALSE", "decision": "ZERO_EMISSION_UNARY_INQUIRY_CONTROL"},
    "SURF-R12-002": {"round": "ROUND12", "path": R12_PAIRS, "ref": "pair_question_id", "class": "PAIR_INQUIRY_CONTROL", "rule": "PAIR_DECISION_CANNOT_EMIT_GROUP", "decision": "ZERO_EMISSION_PAIR_CONTROL_ONLY"},
    "SURF-R12-003": {"round": "ROUND12", "path": R12_SEEDS, "ref": "seed_id", "class": "RESEARCH_ONLY_SEED_CONTROL", "rule": "HISTORICAL_CLAIM_FALSE_AND_PUBLIC_EXPORTABLE_FALSE", "decision": "ZERO_EMISSION_RENDERABILITY_NON_SUPPORTING"},
    "SURF-R12-004": {"round": "ROUND12", "path": R12_INSTANCES, "ref": "instance_id", "class": "RESEARCH_PREVIEW_INSTANCE_CONTROL", "rule": "RESEARCH_PREVIEW_ONLY_TRUE", "decision": "ZERO_EMISSION_RENDERABILITY_NON_SUPPORTING"},
    "SURF-R13-001": {"round": "ROUND13", "path": R13_BIB, "ref": "source_id", "class": "BIBLIOGRAPHIC_IDENTITY", "rule": "CANONICALIZE_DOI_THEN_ISBN_THEN_STABLE_URL_THEN_AUTHOR_YEAR_TITLE", "decision": "ZERO_EMISSION_RIGHTS_AND_TEXT_REVIEW_BLOCKED"},
    "SURF-R13-003": {"round": "ROUND13", "path": R13_PAIRS, "ref": "pair_id", "class": "GOVERNED_PAIR_DECISION_CONTROL", "rule": "ACTIVATION_CANDIDATE_FALSE_AND_NO_GROUP_LIFT", "decision": "ZERO_EMISSION_PAIR_CONTROL_ONLY"},
    "SURF-R13-005": {"round": "ROUND13", "path": R13_ACTIVATION, "ref": "candidateId", "class": "INACTIVE_ACTIVATION_PACKAGE_CONTROL", "rule": "PACKAGE_ACTIVE_FALSE_REQUIRES_HUMAN_AND_SEPARATE_DECISION", "decision": "ZERO_EMISSION_INACTIVE_PACKAGE"},
    "SURF-R13-006": {"round": "ROUND13", "path": R13_HUMAN, "ref": "review_unit_id", "class": "PENDING_EXTERNAL_HUMAN_REVIEW_BLOCKER", "rule": "REVIEWER_ANSWER_STATUS_EXACT_NOT_COMPLETED", "decision": "ZERO_EMISSION_HUMAN_AUTHORITY_BLOCKED"},
    "SURF-R14-004": {"round": "ROUND14", "path": R14_NARY_RESULT, "ref": "fixture_id", "class": "SYNTHETIC_NARY_RESULT_ALIAS_CONTROL", "rule": "EXACT_FIXTURE_ALIAS_EXPECTED_EQUALS_ACTUAL_PASS_PRODUCTION_FALSE", "decision": "ZERO_EMISSION_SYNTHETIC_RESULT_ALIAS"},
    "SURF-R16A-003": {"round": "ROUND16A", "path": R16A_EVIDENCE, "ref": "ledger_id", "class": "ROUND16A_PAIR_EVIDENCE_DERIVATIVE", "rule": "R14_EXACT_ALIAS_OR_QUERY_RESULT_EXACT_ALIAS", "decision": "ZERO_NET_EMISSION_ALL_ROWS_ALIASED"},
    "SURF-R16A-005": {"round": "ROUND16A", "path": R16A_PARAMETERS, "ref": "parameter_name", "class": "ROUND16A_PARAMETER_RECONCILIATION", "rule": "SEMANTIC_IDENTITY_FLAG_DETERMINES_HIGHER_ORDER_OBLIGATION", "decision": "ZERO_EMISSION_PARAMETER_CONTROL"},
    "SURF-R16A-010": {"round": "ROUND16A", "path": R16A_QUERY_LOG, "ref": "query_id", "class": "METADATA_QUERY_CONTROL", "rule": "FIVE_RESULTS_PER_QUERY_EXACT_ALIAS_AND_ZERO_ACCEPTED", "decision": "ZERO_EMISSION_METADATA_ONLY"},
}


def surface_records(spec: dict[str, str]) -> list[tuple[str, str, dict[str, Any]]]:
    path = spec["path"]
    if path == R12_FREEZE:
        payload = read_json(path)
        if payload["active"] is not False:
            raise ValueError("Round12 research candidate package unexpectedly active")
        return [(row["candidateId"], f"{path}#candidates/{row['candidateId']}", row) for row in payload["candidates"]]
    if path == R13_ACTIVATION:
        payload = read_json(path)
        if payload["active"] is not False or payload["requiresExternalHumanReview"] is not True or payload["requiresSeparateActivationDecision"] is not True:
            raise ValueError("Round13 activation package authority boundary changed")
        rows: list[tuple[str, str, dict[str, Any]]] = []
        for key in ("nodeActivationCandidates", "pairCompositionCandidates", "inquiryGrammarCandidates", "structuralAnnotationCandidates"):
            for row in payload[key]:
                rows.append((row["candidateId"], f"{path}#{key}/{row['candidateId']}", {"package_section": key, **row}))
        return rows
    if path == R16A_PARAMETERS:
        return [(row["parameter_name"], f"{path}#parameters/{row['parameter_name']}", row) for row in read_json(path)["parameters"]]
    if path == R16A_QUERY_LOG:
        return [(row["query_id"], f"{path}#query_id={row['query_id']}", row) for row in read_jsonl(path)]
    rows = read_tsv(path)
    return [(row[spec["ref"]], f"{path}#{spec['ref']}={row[spec['ref']]}", row) for row in rows]


def validate_zero_emission_source(path: str, row: dict[str, Any]) -> tuple[str, str, str]:
    """Return record-specific alias/blocker, dependency, and note after exact checks."""
    if path == R09_REJECTED:
        if not (row["final_decision"].startswith("DEFER_") or row["final_decision"].startswith("REJECT_")):
            raise ValueError(f"Round9 negative/deferred decision became permissive: {row['candidate_id']}")
        return row["final_decision"], "GOVERNED_VOCABULARY_AUTHORITY", row["decision_reason"]
    if path == R10_PAIRS:
        return row["decision"], "PAIR_PROJECTION_POLICY", row["decision_reason"]
    if path == R10_GAPS:
        if row["new_public_label_created"] != "false":
            raise ValueError(f"Round10 gap created a public label: {row['gap_id']}")
        number = int(row["gap_id"].rsplit("-", 1)[1])
        return f"{row['gap_id']}->GAP-{number:03d}", "VOCABULARY_GOVERNANCE", row["future_gate"]
    if path == R11_CONSTRAINTS:
        if row["status"] != "PASS":
            raise ValueError(f"Round11 constraint failed: {row['constraint_id']}")
        return row["constraint_id"], "SOFTWARE_CONTROL_ONLY", row["requirement"]
    if path == R11_FIXTURES:
        if row["synthetic_test_only"] != "true" or row["production_exportable"] != "false":
            raise ValueError(f"Round11 fixture boundary changed: {row['fixture_id']}")
        return row["fixture_id"], "SYNTHETIC_CONTROL_ONLY", row["purpose"]
    if path == R11_ADVERSARIAL:
        if row["status"] != "PASS" or row["expected_outcome"] != row["actual_outcome"]:
            raise ValueError(f"Round11 adversarial expectation failed: {row['case_id']}")
        return row["case_id"], "SOFTWARE_CONTROL_ONLY", row["attack"]
    if path == R12_FREEZE:
        if row["active"] is not False:
            raise ValueError(f"Round12 candidate unexpectedly active: {row['candidateId']}")
        return row["researchStatus"], "FRESH_GOVERNED_REVIEW_REQUIRED", row["label"]
    if path == R12_PAIRS:
        return row["decision"], "PAIR_ONLY_INQUIRY_AUTHORITY", row["defer_reason"]
    if path == R12_SEEDS:
        if row["historical_claim"] != "false" or row["public_exportable"] != "false":
            raise ValueError(f"Round12 inquiry seed became claim/exportable: {row['seed_id']}")
        return row["research_status"], "RESEARCH_INQUIRY_ONLY", row["plain_language_research_question"]
    if path == R12_INSTANCES:
        if row["research_preview_only"] != "true":
            raise ValueError(f"Round12 instance left preview boundary: {row['instance_id']}")
        return row["activation_state"], "RESEARCH_PREVIEW_ONLY", f"node_count={row['node_count']}"
    if path == R13_PAIRS:
        if row["activation_candidate"] != "false":
            raise ValueError(f"Round13 pair became activation candidate: {row['pair_id']}")
        return row["final_status"], "PAIR_DECISION_ONLY", row["qualification"]
    if path == R13_ACTIVATION:
        if row.get("active") is not False:
            raise ValueError(f"Round13 package child became active: {row['candidateId']}")
        return row["package_section"], "EXTERNAL_HUMAN_AND_SEPARATE_ACTIVATION_AUTHORITY", "Inactive package child; no association fact is authorized."
    if path == R13_HUMAN:
        if row["reviewer_answer_status"] != "NOT_COMPLETED":
            raise ValueError(f"Round13 human review state changed: {row['review_unit_id']}")
        return row["review_unit_type"], "EXTERNAL_DOMAIN_REVIEWER_REQUIRED", row["current_system_decision"]
    if path == R14_NARY_RESULT:
        if row["status"] != "PASS" or row["expected_result"] != row["actual_result"] or row["production_eligible"] != "false":
            raise ValueError(f"Round14 nary result boundary changed: {row['fixture_id']}")
        return f"{R14_NARY_FIXTURE}#fixtures/{row['fixture_id']}", "SYNTHETIC_CONTROL_ONLY", f"strategy={row['strategy']}"
    if path == R16A_PARAMETERS:
        obligation = bool(row["changes_semantic_identity"])
        return ("SEMANTIC_REJUSTIFICATION_OBLIGATION" if obligation else "BASELINE_ONLY_PARAMETER"), "HIGHER_ORDER_METHOD_AUTHORITY", row["authority"]
    return "", "", ""


def build_zero_emission_controls(
    canonical_by_member: dict[tuple[str, str], str],
    evidence_alias_id_by_ledger: dict[str, str],
    query_aliases: list[dict[str, Any]],
    query_alias_ids_by_query: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    query_alias_by_ledger = {row["round16a_ledger_id"]: row["alias_id"] for row in query_aliases}
    control_rows: list[dict[str, Any]] = []
    controls_by_surface: dict[str, list[str]] = defaultdict(list)
    for surface_id, spec in DEFERRED_SURFACE_SPECS.items():
        records = surface_records(spec)
        for source_ref, locator, source_row in records:
            alias_ref, dependency, notes = validate_zero_emission_source(spec["path"], source_row)
            if spec["path"] in {R09_BIB, R10_BIB, R13_BIB}:
                alias_ref = canonical_by_member[(surface_id, source_ref)]
                dependency = "RIGHTS_TEXT_ACCESS_LOCATOR_AND_BOUNDED_GROUP_REVIEW"
                notes = "Bibliographic identity is discovery metadata, not association evidence."
            elif spec["path"] == R16A_EVIDENCE:
                if source_row["ledger_id"] in evidence_alias_id_by_ledger:
                    alias_ref = evidence_alias_id_by_ledger[source_row["ledger_id"]]
                else:
                    alias_ref = query_alias_by_ledger[source_row["ledger_id"]]
                dependency = "UPSTREAM_ALIAS_ONLY_NO_GROUP_LIFT"
                notes = (
                    "Exact Round14 evidence derivative bounded to a pair." if source_row["evidence_verified"] == "true"
                    else "Exact query-result metadata derivative; rejected as evidence."
                )
            elif spec["path"] == R16A_QUERY_LOG:
                if source_row["accepted_source_ids"] or len(source_row["candidate_results"]) != 5:
                    raise ValueError(f"Round16A query boundary changed: {source_row['query_id']}")
                alias_ref = canonical_json(sorted(query_alias_ids_by_query[source_row["query_id"]]))
                dependency = "LAWFUL_SOURCE_TEXT_AND_LOCATOR_REVIEW"
                notes = "Five Crossref results are exact aliases to metadata-only evidence rows; no result was accepted."
            control_id = stable_id("R16B-DEFERRED-CONTROL", {
                "surface_id": surface_id, "source_record_ref": source_ref,
                "selector_version": SELECTOR_VERSION,
            })
            control = finalize_row({
                "control_record_id": control_id,
                "surface_id": surface_id,
                "source_path": spec["path"],
                "source_record_ref": source_ref,
                "source_record_locator": locator,
                "selector_rule": spec["rule"],
                "record_class": spec["class"],
                "emission_decision": spec["decision"],
                "net_trigger_occurrence_count": 0,
                "alias_or_blocker_ref": alias_ref,
                "authority_dependency": dependency,
                "notes": notes,
                "source_record_sha256": row_hash(source_row),
            })
            control_rows.append(control)
            controls_by_surface[surface_id].append(control_id)
    if len(control_rows) != 3411:
        raise ValueError(f"zero-emission control row count changed: {len(control_rows)} != 3411")
    if len(controls_by_surface) != 20:
        raise ValueError("zero-emission controls must cover exactly twenty non-database deferred surfaces")
    return sorted(control_rows, key=lambda row: row["control_record_id"]), controls_by_surface


def tsv_fields(relative: str) -> list[str]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        fields = csv.DictReader(handle, dialect="excel-tab").fieldnames
    if fields is None:
        raise ValueError(f"missing TSV header: {relative}")
    return fields


def build_merged_candidate_ledgers(
    database_occurrences: list[dict[str, Any]],
    database_families: list[dict[str, Any]],
    new_occurrences: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    occurrences = read_tsv(V1_OCCURRENCE_PATH) + new_occurrences
    if len(occurrences) != 359 or len({row["trigger_occurrence_id"] for row in occurrences}) != 359:
        raise ValueError("merged trigger occurrence ledger must contain 359 unique rows")
    v1_families = read_tsv(V1_FAMILY_PATH)
    existing_ids = {row["candidate_id"] for row in v1_families}
    crosswalk = read_tsv(CROSSWALK_PATH)
    canonical_by_sense = {
        row["canonical_resolution_sense_id"]: row
        for row in crosswalk if row["participant_sense_id"] == row["canonical_resolution_sense_id"]
    }
    occurrence_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for occurrence in new_occurrences:
        occurrence_by_candidate[occurrence["candidate_id"]].append(occurrence)
    new_family_rows: list[dict[str, Any]] = []
    for database_family in database_families:
        candidate_id = database_family["candidate_id"]
        if candidate_id in existing_ids:
            raise ValueError(f"database family unexpectedly overlaps checkpoint003 family: {candidate_id}")
        senses = json.loads(database_family["participant_sense_ids_json"])
        labels = [canonical_by_sense[sense]["canonical_label"] for sense in senses]
        dispositions = Counter(canonical_by_sense[sense]["disposition"] for sense in senses)
        family_occurrences = occurrence_by_candidate[candidate_id]
        occurrence_ids = sorted(row["trigger_occurrence_id"] for row in family_occurrences)
        family_material = {
            "candidate_id": candidate_id,
            "participant_sense_ids": senses,
            "scope_resolution_status": "UNRESOLVED_MAY_SPLIT_BY_CASE",
            "occurrence_ids": occurrence_ids,
        }
        new_family_rows.append({
            "candidate_id": candidate_id,
            "candidate_object_kind": "LOCAL_PARTICIPANT_SET_REVIEW_FAMILY_NOT_ASSOCIATION",
            "participant_set_key": database_family["participant_set_key"],
            "participant_sense_ids_json": canonical_json(senses),
            "canonical_labels_json": canonical_json(labels),
            "arity": len(senses),
            "occurrence_count": len(family_occurrences),
            "trigger_occurrence_ids_json": canonical_json(occurrence_ids),
            "trigger_ids_json": canonical_json(["TRG-009"]),
            "emission_kinds_json": canonical_json(["DATABASE_DISCOVERY_REVIEW_FAMILY"]),
            "active_participant_count": dispositions["ACTIVE"],
            "research_only_participant_count": dispositions["RESEARCH_ONLY"],
            "rejected_participant_count": dispositions["REJECTED"],
            "order_semantics": "UNRESOLVED",
            "role_semantics": "UNRESOLVED",
            "scope_resolution_status": "UNRESOLVED_MAY_SPLIT_BY_CASE",
            "case_resolution_status": "UNRESOLVED",
            "participant_eligibility": "REVIEW_ELIGIBLE_NOT_VALIDATED",
            "lifecycle_state": "DISCOVERED",
            "proposed_disposition": "PENDING_GOVERNED_REVIEW",
            "evidence_review_status": "NOT_STARTED",
            "global_coherence_status": "NOT_REVIEWED",
            "product_eligibility": "INELIGIBLE_PENDING_GOVERNED_REVIEW",
            "association_identity_frozen": "False",
            "family_content_sha256": row_hash(family_material),
        })
    families = v1_families + new_family_rows
    if len(families) != 35 or len({row["candidate_id"] for row in families}) != 35:
        raise ValueError("merged local candidate family ledger must contain 35 unique rows")
    if len(database_occurrences) != sum(len(rows) for rows in occurrence_by_candidate.values()):
        raise ValueError("database discovery/merged occurrence reconciliation failed")
    return (
        sorted(occurrences, key=lambda row: row["trigger_occurrence_id"]),
        sorted(families, key=lambda row: (int(row["arity"]), row["candidate_id"])),
    )


def build_execution_and_surface_ledgers(
    controls_by_surface: dict[str, list[str]],
    source_membership_rows: list[dict[str, Any]],
    database_occurrences: list[dict[str, Any]],
    database_families: list[dict[str, Any]],
    database_search_controls: list[dict[str, Any]],
    database_capture_controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory = read_tsv(INVENTORY_PATH)
    inventory_by_id = {row["surface_id"]: row for row in inventory}
    deferred_ids = list(DEFERRED_SURFACE_SPECS) + ["SURF-DB-001"]
    if len(inventory) != 44 or len(deferred_ids) != 21:
        raise ValueError("method inventory or checkpoint004 execution surface count changed")
    for surface_id in deferred_ids:
        row = inventory_by_id[surface_id]
        source_path = REPO / row["path"]
        if sha256_file(source_path) != row["sha256"] or source_path.stat().st_size != int(row["bytes"]):
            raise ValueError(f"frozen surface bytes/hash changed: {surface_id}")

    alias_members_by_surface = Counter(
        row["surface_id"] for row in source_membership_rows if row["membership_role"] == "CROSS_ROUND_ALIAS"
    )
    execution_rows: list[dict[str, Any]] = []
    for surface_id in deferred_ids:
        inventory_row = inventory_by_id[surface_id]
        if surface_id == "SURF-DB-001":
            spec = {
                "rule": f"{DATABASE_SELECTOR_SQL_VERSION};{NORMALIZATION_VERSION}",
            }
            control_count = len(database_search_controls) + len(database_capture_controls)
            alias_count = 0
            lead_count = len(database_occurrences)
            occurrence_count = len(database_occurrences)
            family_count = len(database_families)
            disposition = "SELECTOR_ACCOUNTED_DATABASE_DISCOVERY_ONLY"
            dependency = "BOUNDED_SOURCE_TEXT_SENSE_RIGHTS_AND_GLOBAL_COHERENCE_REVIEW"
            action = (
                "Review the eleven metadata/lexical loci as sources; preserve the two capture-locus exclusions "
                "and 120 project-generated search-document controls; do not activate database co-occurrence."
            )
        else:
            spec = DEFERRED_SURFACE_SPECS[surface_id]
            control_count = len(controls_by_surface[surface_id])
            alias_count = 0
            lead_count = 0
            occurrence_count = 0
            family_count = 0
            if surface_id in {"SURF-R09-001", "SURF-R10-001", "SURF-R13-001"}:
                alias_count = alias_members_by_surface[surface_id]
                disposition = "SELECTOR_ACCOUNTED_RIGHTS_BLOCKED"
                dependency = "RIGHTS_TEXT_ACCESS_LOCATOR_AND_BOUNDED_GROUP_REVIEW"
                action = "Resolve the canonical rights queue and review lawful locator-bearing source text."
            elif surface_id == "SURF-R13-006":
                disposition = "SELECTOR_ACCOUNTED_HUMAN_REVIEW_BLOCKED"
                dependency = "EXTERNAL_DOMAIN_REVIEWER_AUTHORITY"
                action = "Complete all 36 external domain-review units before any activation decision."
            elif surface_id == "SURF-R16A-010":
                alias_count = 2325
                lead_count = 101
                disposition = "SELECTOR_ACCOUNTED_METADATA_SEARCH_BLOCKED"
                dependency = "LAWFUL_SOURCE_TEXT_AND_LOCATOR_REVIEW"
                action = "Review the 101 deduplicated DOI leads adaptively; metadata remains non-supporting."
            else:
                if surface_id == "SURF-R14-004":
                    alias_count = 6
                elif surface_id == "SURF-R16A-003":
                    alias_count = 2386
                disposition = "SELECTOR_ACCOUNTED_ZERO_HIGHER_ORDER_EMISSION"
                dependency = "GOVERNED_EVIDENCE_AND_METHOD_AUTHORITY_REMAINS_OPEN"
                action = "Retain the exact control/alias proof; continue evidence and recursive-gap review."
        material = {
            "surface_id": surface_id,
            "source_sha256": inventory_row["sha256"],
            "selector_rule": spec["rule"],
            "selector_version": SELECTOR_VERSION,
            "control_record_count": control_count,
            "new_trigger_occurrence_count": occurrence_count,
        }
        execution_rows.append({
            "surface_id": surface_id,
            "round": inventory_row["round"],
            "source_path": inventory_row["path"],
            "source_sha256": inventory_row["sha256"],
            "record_selector": inventory_row["record_selector"],
            "input_record_count": inventory_row["record_count"],
            "selector_rule": spec["rule"],
            "selector_version": SELECTOR_VERSION,
            "control_record_count": control_count,
            "alias_record_count": alias_count,
            "metadata_lead_count": lead_count,
            "new_trigger_occurrence_count": occurrence_count,
            "new_candidate_family_count": family_count,
            "execution_disposition": disposition,
            "authority_dependency": dependency,
            "required_next_action": action,
            "record_sha256": row_hash(material),
        })

    v1_rows = read_tsv(V1_SURFACE_PATH)
    db_occurrence_ids = [row["database_occurrence_id"] for row in database_occurrences]
    surface_rows: list[dict[str, Any]] = []
    execution_by_id = {row["surface_id"]: row for row in execution_rows}
    for old_row in v1_rows:
        row = {key: value for key, value in old_row.items() if key != "record_sha256"}
        surface_id = row["surface_id"]
        if surface_id in execution_by_id:
            execution = execution_by_id[surface_id]
            row["matched_input_ids_json"] = canonical_json(
                db_occurrence_ids if surface_id == "SURF-DB-001" else controls_by_surface[surface_id]
            )
            row["trigger_occurrence_count"] = execution["new_trigger_occurrence_count"]
            row["disposition"] = execution["execution_disposition"]
            row["zero_emission_proof"] = (
                "NOT_ZERO:ELEVEN_NON_SUPPORTING_DATABASE_DISCOVERY_OCCURRENCES" if surface_id == "SURF-DB-001"
                else f"ROW_EXACT_CONTROLS={execution['control_record_count']};ALIASES={execution['alias_record_count']};NET_OCCURRENCES=0"
            )
            row["candidate_universe_closure_effect"] = "SELECTOR_ACCOUNTED_RESEARCH_AND_AUTHORITY_BLOCKERS_OPEN"
            row["required_next_action"] = execution["required_next_action"]
        elif row["disposition"] == "SELECTED_EXECUTION_INPUT":
            row["disposition"] = "SELECTOR_ACCOUNTED_CHECKPOINT003_INPUT"
            row["candidate_universe_closure_effect"] = "SELECTOR_ACCOUNTED_EVIDENCE_AND_COHERENCE_REVIEW_OPEN"
        elif row["disposition"] == "INSPECTED_ZERO_HIGHER_ORDER_EMISSION":
            row["disposition"] = "SELECTOR_ACCOUNTED_ZERO_HIGHER_ORDER_EMISSION"
            row["candidate_universe_closure_effect"] = "SELECTOR_ACCOUNTED_EVIDENCE_AND_COHERENCE_REVIEW_OPEN"
        else:
            raise ValueError(f"unhandled surface disposition: {surface_id}:{row['disposition']}")
        row["record_sha256"] = row_hash({key: value for key, value in row.items() if key != "record_sha256"})
        surface_rows.append(row)
    if len(execution_rows) != 21 or len(surface_rows) != 44:
        raise ValueError("execution/surface ledger coverage mismatch")
    if any(row["disposition"].startswith("DEFERRED_") for row in surface_rows):
        raise ValueError("checkpoint004 must leave zero selector-deferred method surfaces")
    return sorted(execution_rows, key=lambda row: row["surface_id"]), sorted(surface_rows, key=lambda row: row["surface_id"])


def build_receipt_import_failure_disposition() -> list[dict[str, Any]]:
    failed_relative = (
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
        "publication-receipts/001-1787895386177547000-checkpoint-003.json"
    )
    canonical_relative = (
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
        "publication-receipts/007-1787895386177547000-checkpoint-003.json"
    )
    failed_path = REPO / failed_relative
    canonical_path = REPO / canonical_relative
    if not failed_path.exists() or not canonical_path.exists():
        raise ValueError("checkpoint003 failed-import duplicate and canonical receipt must both be preserved")
    failed_hash = sha256_file(failed_path)
    canonical_hash = sha256_file(canonical_path)
    if failed_hash != canonical_hash:
        raise ValueError("checkpoint003 failed-import artifact is not byte-identical to canonical receipt")
    manifest = read_tsv(
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
        "checkpoint-publication-manifest.tsv"
    )
    manifest_paths = {row["copied_path"] for row in manifest}
    if canonical_path.name not in manifest_paths or failed_path.name in manifest_paths:
        raise ValueError("checkpoint003 receipt manifest/copy disposition changed")
    return [finalize_row({
        "failure_id": "CHECKPOINT004-FAILED-IMPORT-001",
        "failed_import_path": failed_relative,
        "canonical_import_path": canonical_relative,
        "failed_import_sha256": failed_hash,
        "canonical_import_sha256": canonical_hash,
        "byte_identical": "true",
        "manifest_status": "FAILED_COPY_UNMANIFESTED;CANONICAL_COPY_MANIFESTED_AS_ORDINAL_007",
        "preservation_status": "PRESERVED_AND_HASH_BOUND_NO_DELETION",
        "failure_cause": (
            "The first single-receipt chain import copied the checkpoint003 receipt into ordinal 001; "
            "the authoritative full-chain retry assigned the same bytes to ordinal 007."
        ),
        "corrective_action": (
            "Retain both files, treat ordinal 007 as the canonical manifest member, bind both hashes here, "
            "and never silently delete the failed-import artifact."
        ),
    })]


def build_recursive_gap_rows() -> list[dict[str, Any]]:
    rows = [
        ("GAP-001", "Previously deferred method surfaces", "CLOSURE_BLOCKING", "SELECTOR_ACCOUNTED_EVIDENCE_OPEN", "All 44 inventory surfaces now have deterministic selectors or exact zero-emission/control proofs.", "EVIDENCE_REVIEW", "Keep trigger discovery extensible and rerun after every new evidence class."),
        ("GAP-002", "Lawful source-text access and reuse rights", "CLOSURE_BLOCKING", "OPEN_94_CANONICAL_IDENTITIES", "108 bibliography rows resolve to 94 identities and 14 aliases without emitting association facts.", "RIGHTS_OR_HUMAN_AUTHORITY", "Resolve rights/access and inspect locator-bearing text."),
        ("GAP-003", "Round16A metadata discovery is not evidence", "CLOSURE_BLOCKING", "OPEN_101_METADATA_LEADS", "2,325 query-result aliases deduplicate to 101 DOI leads; none is accepted evidence.", "SOURCE_TEXT_REVIEW", "Run adaptive source-centred and falsification review."),
        ("GAP-004", "Database lexical/provenance discovery lacks bounded senses", "CLOSURE_BLOCKING", "OPEN_11_LOCI_4_FAMILIES", "Seven direct TRACE loci and four capture loci emit non-supporting review families; CHW and WHMZ are excluded controls.", "SOURCE_TEXT_AND_SENSE_REVIEW", "Review each exact locus; retain DGI hold and AIC rejected-Bauhaus caveats."),
        ("GAP-005", "Round13 external review authority remains absent", "CLOSURE_BLOCKING", "OPEN_36_HUMAN_REVIEW_UNITS", "All 36 review rows remain NOT_COMPLETED.", "EXTERNAL_HUMAN_AUTHORITY", "Complete and record external domain review before activation."),
        ("GAP-006", "Pair-derived semantic parameter bounds are unjustified for hyperedges", "CLOSURE_BLOCKING", "OPEN_9_SEMANTIC_OBLIGATIONS", "Nine of 18 parameters change semantic identity and require higher-order rejustification.", "METHOD_AUTHORITY", "Reconcile arity, topology, pruning, split, degree, and node bounds before enumeration."),
        ("GAP-007", "Candidate participant sets are not associations", "CLOSURE_BLOCKING", "OPEN_35_REVIEW_FAMILIES", "359 occurrences form 35 review families; evidence, scope, case, order, roles, and global coherence are unresolved.", "GOVERNED_ASSOCIATION_REVIEW", "Split/merge/dispose candidates append-only; do not freeze association identity early."),
        ("GAP-008", "Prior compositions and descendants lack group-level reconciliation", "CLOSURE_BLOCKING", "OPEN", "Checkpoint003 prior-object census remains the exact baseline; no v2 object is silently promoted.", "GLOBAL_COHERENCE_AND_PRODUCT_AUTHORITY", "Reconcile all prior compositions before v3 regeneration."),
        ("GAP-009", "Checkpoint003 failed receipt import left an unmanifested duplicate", "AUDIT", "DOCUMENTED_PRESERVED", "Ordinal 001 and canonical ordinal 007 are byte-identical and separately hash-bound.", "AUDIT_TRAIL", "Preserve both; use ordinal 007 as canonical manifest member."),
    ]
    return [{
        "gap_id": gap_id,
        "last_reviewed_checkpoint": "CHECKPOINT-004",
        "gap": gap,
        "severity": severity,
        "status": status,
        "checkpoint004_evidence": evidence,
        "authority_dependency": authority,
        "required_next_action": action,
    } for gap_id, gap, severity, status, evidence, authority, action in rows]


def candidate_json_rows(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
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
    } for row in families]


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    source_membership, source_rights, canonical_by_member = build_source_identity_ledgers()
    evidence_aliases, query_aliases, metadata_leads, evidence_alias_map, query_aliases_by_query = (
        build_round16a_alias_ledgers()
    )
    parameter_rows = build_parameter_reconciliation()
    (
        database_occurrences,
        database_families,
        database_trigger_occurrences,
        database_search_controls,
        database_capture_controls,
    ) = build_database_discovery()
    zero_controls, controls_by_surface = build_zero_emission_controls(
        canonical_by_member, evidence_alias_map, query_aliases, query_aliases_by_query
    )
    occurrences, families = build_merged_candidate_ledgers(
        database_occurrences, database_families, database_trigger_occurrences
    )
    execution_rows, surface_rows = build_execution_and_surface_ledgers(
        controls_by_surface, source_membership, database_occurrences, database_families,
        database_search_controls, database_capture_controls,
    )
    receipt_failure_rows = build_receipt_import_failure_disposition()
    gap_rows = build_recursive_gap_rows()

    OUTPUT_SCHEMAS["candidate-trigger-occurrence-ledger-v2.tsv"] = tsv_fields(V1_OCCURRENCE_PATH)
    OUTPUT_SCHEMAS["local-candidate-family-ledger-v2.tsv"] = tsv_fields(V1_FAMILY_PATH)
    OUTPUT_SCHEMAS["local-surface-disposition-ledger-v2.tsv"] = tsv_fields(V1_SURFACE_PATH)
    output_rows: dict[str, list[dict[str, Any]]] = {
        "deferred-surface-execution-ledger-v2.tsv": execution_rows,
        "deferred-zero-emission-control-ledger-v2.tsv": zero_controls,
        "source-identity-membership-ledger-v2.tsv": source_membership,
        "source-canonical-rights-queue-v2.tsv": source_rights,
        "round16a-evidence-alias-ledger-v2.tsv": evidence_aliases,
        "round16a-query-result-alias-ledger-v2.tsv": query_aliases,
        "metadata-search-lead-ledger-v2.tsv": metadata_leads,
        "parameter-reconciliation-ledger-v2.tsv": parameter_rows,
        "database-discovery-occurrence-ledger-v2.tsv": database_occurrences,
        "database-discovery-family-ledger-v2.tsv": database_families,
        "database-search-document-rejection-ledger-v2.tsv": database_search_controls,
        "database-capture-locus-control-ledger-v2.tsv": database_capture_controls,
        "candidate-trigger-occurrence-ledger-v2.tsv": occurrences,
        "local-candidate-family-ledger-v2.tsv": families,
        "local-surface-disposition-ledger-v2.tsv": surface_rows,
        "checkpoint003-receipt-import-failure-disposition-v2.tsv": receipt_failure_rows,
        "recursive-gap-ledger-checkpoint004-v2.tsv": gap_rows,
    }
    for name, rows in output_rows.items():
        write_tsv(RAW / name, OUTPUT_SCHEMAS[name], rows)

    family_arity = Counter(str(row["arity"]) for row in families)
    surface_dispositions = Counter(row["disposition"] for row in surface_rows)
    trigger_classes = Counter(row["trigger_class"] for row in occurrences)
    v1_census = read_json(V1_CENSUS_PATH)
    candidates = candidate_json_rows(families)
    closure = {
        "PAIR_ASSOCIATION_CLOSURE": False,
        "HIGHER_ORDER_ASSOCIATION_CLOSURE": False,
        "GLOBAL_COMPOSITION_COHERENCE_CLOSURE": False,
        "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE": False,
        "COMPUTATIONAL_SPACE_CLOSURE": False,
        "FUNCTION3_CLOSURE": False,
    }
    census = {
        "format": "trace-round16b-local-candidate-census-v2",
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "selector_version": SELECTOR_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "database_selector_sql_version": DATABASE_SELECTOR_SQL_VERSION,
        "database_sha256": SQLITE_SHA256,
        "status": "PASS_WITH_OPEN_RESEARCH_HUMAN_RIGHTS_AND_AUTHORITY_BLOCKERS",
        "semantic_boundary": (
            "The 359 trigger occurrences and 35 participant-set review families are discovery/control objects, "
            "not governed associations, evidence dispositions, globally coherent compositions, or active facts."
        ),
        "candidate_universe_status": "ALL_44_LOCAL_METHOD_SURFACES_SELECTOR_ACCOUNTED_EVIDENCE_UNCLOSED",
        "eligible_lexical_label_count": 53,
        "eligible_resolved_participant_sense_count": 52,
        "method_surface_count": 44,
        "selector_accounted_method_surface_count": 44,
        "deferred_method_surface_count": 0,
        "method_surface_disposition_distribution": dict(sorted(surface_dispositions.items())),
        "deferred_surface_execution_count": 21,
        "zero_emission_control_record_count": len(zero_controls),
        "source_bibliography_row_count": len(source_membership),
        "canonical_source_identity_count": len(source_rights),
        "cross_round_source_alias_count": sum(row["membership_role"] == "CROSS_ROUND_ALIAS" for row in source_membership),
        "round16a_evidence_alias_count": len(evidence_aliases),
        "round16a_query_result_alias_count": len(query_aliases),
        "metadata_search_lead_count": len(metadata_leads),
        "parameter_reconciliation_count": len(parameter_rows),
        "semantic_parameter_obligation_count": sum(row["higher_order_semantic_obligation"] == "true" for row in parameter_rows),
        "database_discovery_occurrence_count": len(database_occurrences),
        "database_discovery_family_count": len(database_families),
        "database_capture_locus_control_count": len(database_capture_controls),
        "database_search_document_rejection_count": len(database_search_controls),
        "trigger_occurrence_count": len(occurrences),
        "trigger_occurrence_distribution": dict(sorted(trigger_classes.items())),
        "local_candidate_family_count": len(families),
        "candidate_arity_distribution": dict(sorted(family_arity.items(), key=lambda item: int(item[0]))),
        "control_only_candidate_family_count": sum(row["participant_eligibility"] == "CONTROL_ONLY_REJECTED_PARTICIPANT" for row in families),
        "active_candidate_family_count": 0,
        "active_pending_review_count": 0,
        "evidence_review_complete_candidate_count": 0,
        "global_coherence_pass_candidate_count": 0,
        "open_participant_resolution_queue_count": v1_census["open_participant_resolution_queue_count"],
        "isolated_active_vocabulary_count": v1_census["isolated_active_vocabulary_count"],
        "isolated_active_vocabulary_proven_composable_count": 0,
        "prior_row_exact_reconciliation_object_count": v1_census["prior_row_exact_reconciliation_object_count"],
        "prior_transition_set_count": v1_census["prior_transition_set_count"],
        "prior_transition_set_sha256": v1_census["prior_transition_set_sha256"],
        "candidates": candidates,
        "closure": closure,
        "open_blockers": {
            "canonical_source_rights_and_text_review_count": len(source_rights),
            "metadata_search_lead_count": len(metadata_leads),
            "database_discovery_locus_count": len(database_occurrences),
            "external_human_review_unit_count": 36,
            "semantic_parameter_obligation_count": 9,
            "open_participant_resolution_queue_count": v1_census["open_participant_resolution_queue_count"],
            "isolated_active_vocabulary_count": v1_census["isolated_active_vocabulary_count"],
            "unresolved_candidate_family_count": len(families),
            "prior_global_coherence_and_product_reconciliation": "OPEN",
        },
    }
    write_json(RAW / "local-candidate-census-v2.json", census)

    note = f"""# Checkpoint 004 — Deferred-surface and database census

Checkpoint 004 executes all 21 selectors deferred at checkpoint 003. All 44 governed local method surfaces are now selector-accounted, but the candidate universe and every substantive closure remain open.

The three bibliographies contain 108 memberships resolving to 94 canonical source identities and 14 cross-round aliases. They populate a rights/text-access queue and emit no association facts. Round 16A contributes 61 exact Round 14 evidence derivatives, 2,325 exact query-result aliases, and 101 DOI metadata leads; none may be lifted from pair or metadata scope into group support.

The frozen SQLite selector binds SHA-256 `{SQLITE_SHA256}` and requires NFKC/casefold exact-token normalization. It recognizes 53 governed labels resolving to 52 participant senses, including the superseded `cultural adaptation` label resolving to `adaptation`. Seven direct-opposite-object accepted TRACE loci and four capture loci emit 11 metadata/lexical discovery occurrences across four review families. The Cooper Hewitt row is excluded because “translation” is only an unresolved umbrella transcription phrase. The WHM Zambia page is excluded because production and education occur in unrelated concatenated sections. Both AIC loci retain rejected `Bauhaus` as an excluded match. The DGI locus retains its null-active-surface and hold-status caveat. None of these loci is evidence.

Merged totals are 359 trigger occurrences and 35 participant-set review families. Active facts added: 0. Evidence-complete families: 0. Global-coherence passes: 0. All six closure flags remain false.
"""
    note_path = RESEARCH / "07_DEFERRED_SURFACE_AND_DATABASE_CENSUS.md"
    note_path.write_text(note, encoding="utf-8")

    inventory_by_id = {row["surface_id"]: row for row in read_tsv(INVENTORY_PATH)}
    executed_ids = list(DEFERRED_SURFACE_SPECS) + ["SURF-DB-001"]
    failed_receipt = receipt_failure_rows[0]
    output_hashes = {name: sha256_file(RAW / name) for name in output_rows}
    output_hashes["local-candidate-census-v2.json"] = sha256_file(RAW / "local-candidate-census-v2.json")
    output_hashes[str(note_path.relative_to(REPO))] = sha256_file(note_path)
    receipt = {
        "format": "trace-round16b-deferred-surface-build-receipt-v2",
        "authorized_source_sha": AUTHORIZED_SOURCE_SHA,
        "authorized_source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "selector_version": SELECTOR_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "database_selector_sql_version": DATABASE_SELECTOR_SQL_VERSION,
        "status": "PASS_WITH_OPEN_RESEARCH_HUMAN_RIGHTS_AND_AUTHORITY_BLOCKERS",
        "frozen_sqlite": {
            "path": SQLITE_PATH,
            "bytes": (REPO / SQLITE_PATH).stat().st_size,
            "sha256": SQLITE_SHA256,
        },
        "selector_contract": {
            "normalization": "Unicode NFKC, casefold, non-alphanumeric to spaces, longest alternative first, non-overlapping Unicode token boundaries",
            "eligible_lexical_label_count": 53,
            "eligible_resolved_participant_sense_count": 52,
            "capture_selector_sql": CAPTURE_SELECTOR_SQL,
            "capture_selector_sql_sha256": sha256_text(CAPTURE_SELECTOR_SQL),
            "trace_selector_sql": TRACE_SELECTOR_SQL,
            "trace_selector_sql_sha256": sha256_text(TRACE_SELECTOR_SQL),
            "search_document_control_sql": SEARCH_DOCUMENT_CONTROL_SQL,
            "search_document_control_sql_sha256": sha256_text(SEARCH_DOCUMENT_CONTROL_SQL),
        },
        "input_manifest": {
            "executed_surface_sha256": {surface_id: inventory_by_id[surface_id]["sha256"] for surface_id in executed_ids},
            "immutable_checkpoint003_artifact_sha256": {
                path: sha256_file(REPO / path) for path in (
                    V1_OCCURRENCE_PATH, V1_FAMILY_PATH, V1_SURFACE_PATH, V1_CENSUS_PATH, CROSSWALK_PATH
                )
            },
            "failed_checkpoint003_receipt_import_sha256": failed_receipt["failed_import_sha256"],
            "canonical_checkpoint003_receipt_sha256": failed_receipt["canonical_import_sha256"],
        },
        "counts": {
            "deferred_surface_execution": len(execution_rows),
            "method_surface_selector_accounted": len(surface_rows),
            "method_surface_deferred": 0,
            "zero_emission_controls": len(zero_controls),
            "bibliography_memberships": len(source_membership),
            "canonical_source_identities": len(source_rights),
            "source_aliases": sum(row["membership_role"] == "CROSS_ROUND_ALIAS" for row in source_membership),
            "round16a_evidence_aliases": len(evidence_aliases),
            "round16a_query_result_aliases": len(query_aliases),
            "metadata_search_leads": len(metadata_leads),
            "parameter_rows": len(parameter_rows),
            "semantic_parameter_obligations": 9,
            "database_discovery_occurrences": len(database_occurrences),
            "database_discovery_families": len(database_families),
            "database_capture_controls": len(database_capture_controls),
            "database_search_document_controls": len(database_search_controls),
            "merged_trigger_occurrences": len(occurrences),
            "merged_candidate_families": len(families),
            "active_facts_added": 0,
        },
        "closure": closure,
        "output_sha256": dict(sorted(output_hashes.items())),
        "history_rewritten": False,
        "force_push_used": False,
        "activation_performed": False,
        "closure_claimed": False,
    }
    write_json(RAW / "deferred-surface-build-receipt-v2.json", receipt)
    print(canonical_json(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
