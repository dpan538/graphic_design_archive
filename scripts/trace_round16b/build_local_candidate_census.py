#!/usr/bin/env python3
"""Build the deterministic Round 16B local higher-order candidate census.

This checkpoint creates review families, not governed associations.  It preserves
the method checkpoint's empty, hash-bound templates and writes versioned ledgers.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
CHECKPOINT_002_SHA = "af056edadb43c1eb9e219217c42fd58b74ac5efd"
SELECTOR_VERSION = "trace-round16b-local-candidate-selector-v1"

VOCAB_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/vocabulary-census-v2.json"
R9_CANDIDATE_PATH = "docs/research/trace-v49-design-history-relation-vocabulary-round1/04_RAW_CANDIDATE_TERM_REGISTRY.tsv"
R9_ATTESTATION_PATH = "docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv"
R9_GLOSS_PATH = "docs/research/trace-v49-design-history-relation-vocabulary-round1/07_SEMANTIC_GLOSS_REGISTRY.tsv"
R10_ROLE_PATH = "docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv"
R10_ATTESTATION_PATH = "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv"
R10_CLUSTER_PATH = "docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv"
R10_CHAIN_PATH = "docs/research/trace-v49-design-history-relation-grammar-round1/15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv"
R13_EVIDENCE_PATH = "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv"
R13_GAP_PATH = "docs/research/trace-v49-exploration-composition-review-round1/07_VOCABULARY_GAP_DECISIONS.tsv"
R14_ASSESSMENT_PATH = "scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json"
R14_PROVENANCE_PATH = "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv"
R14_NARY_PATH = "scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json"
R15_FIXTURE_PATH = "scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json"
R15_DECISION_PATH = "docs/audits/v49-exploration-composition-engine-round1/raw/composition-decision-audit.json"
R15_RESULT_PATH = "docs/audits/v49-exploration-composition-engine-round1/raw/composition-fixture-results.tsv"
R16_COMPOSITION_PATH = "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json"
R16_SOURCE_PATH = "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv"
R16_READ_MODEL_PATH = "frontend/generated/trace-exploration-v1/read-model.json"
R16A_PAIR_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/association-census-v2.tsv"
R16A_GRAPH_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json"
R16A_REGISTRY_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json"
R16A_ENUMERATION_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/composition-enumeration-v2.tsv"
R16A_REJECTION_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/composition-rejection-ledger-v2.tsv"
R16A_READ_MODEL_PATH = "frontend/generated/trace-exploration-v2/production-read-model.json"
R16A_STATE_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/state-census-v2.tsv"
R16A_TRANSITION_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv"
R16A_WORKFLOW_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/workflow-census-v2.tsv"
R16A_EXPORT_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv"
METHOD_SURFACE_INVENTORY_PATH = (
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/"
    "raw/evidence-surface-inventory.tsv"
)

# File-level no-loss scope for the complete Round 15, Round 16, and Round 16A
# research, audit, generator, schema, read-model, and API namespaces.  The
# manifest binds the authorized source tree, not the mutable worktree.
PRIOR_ARTIFACT_NAMESPACES = (
    ("ROUND15_AUDIT", "docs/audits/v49-exploration-composition-engine-round1"),
    ("ROUND15_RESEARCH", "docs/research/trace-v49-exploration-composition-engine-round1"),
    ("ROUND15_GENERATOR", "scripts/trace-v49-exploration-composition-engine"),
    ("ROUND16_AUDIT", "docs/audits/v49-exploration-real-database-round1"),
    ("ROUND16_RESEARCH", "docs/research/trace-v49-exploration-real-database-round1"),
    ("ROUND16_GENERATOR", "scripts/trace-v49-exploration-real-database"),
    ("ROUND16A_AUDIT", "docs/audits/v49-exploration-full-space-closure-round1"),
    ("ROUND16A_RESEARCH", "docs/research/trace-v49-exploration-full-space-closure-round1"),
    ("ROUND16A_GENERATOR", "scripts/trace_round16a"),
    ("ROUND16_READ_MODEL", "frontend/generated/trace-exploration-v1"),
    ("ROUND16A_READ_MODEL", "frontend/generated/trace-exploration-v2"),
    ("ROUND16_RUNTIME", "frontend/src/features/trace-v49/exploration"),
    ("ROUND16A_RUNTIME", "frontend/src/features/trace-v49/exploration-v2"),
    ("ROUND16_API", "frontend/src/app/api/trace/v1/exploration"),
    ("ROUND16A_API", "frontend/src/app/api/trace/v2/exploration"),
    ("ROUND15_16_16A_SCHEMA", "schemas/trace/exploration"),
)


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


def read_json(relative: str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for raw_row in rows:
        writer.writerow({key: raw_row.get(key, "") for key in fieldnames})
    path.write_text(buffer.getvalue(), encoding="utf-8")


def stable_sense_id(vocabulary_candidate_id: str) -> str:
    material = f"round16a-vocabulary-candidate:{vocabulary_candidate_id}"
    return f"R16B-SENSE:{sha256_text(material)}"


def stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}:{sha256_text(canonical_json(value))}"


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def row_hash(row: dict[str, Any]) -> str:
    return sha256_text(canonical_json(row))


def id_set_hash(values: Iterable[str]) -> str:
    return sha256_text("".join(f"{value}\n" for value in sorted(values)))


def input_manifest_record_count(path: str, selector: str) -> int:
    if selector == "tsv_rows":
        with (REPO / path).open(encoding="utf-8", newline="") as handle:
            return max(0, sum(1 for _ in handle) - 1)
    if selector == "jsonl_rows":
        with (REPO / path).open(encoding="utf-8") as handle:
            return sum(bool(line.strip()) for line in handle)
    if selector == "file":
        return 1
    payload = read_json(path)
    if selector == "json:file":
        return 1
    key = selector.split(":", 1)[1]
    value = payload[key]
    return len(value)


def scan_sorted_tsv_ids(path: str, id_field: str) -> tuple[int, str]:
    """Hash a strictly sorted unique TSV identity column without retaining rows."""
    digest = hashlib.sha256()
    count = 0
    previous = ""
    with (REPO / path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, dialect="excel-tab"):
            value = row[id_field]
            if not value or (previous and value <= previous):
                raise ValueError(f"{path}:{id_field} is not strictly sorted and unique at {value}")
            digest.update(value.encode("utf-8"))
            digest.update(b"\n")
            previous = value
            count += 1
    return count, digest.hexdigest()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    vocabulary_payload = read_json(VOCAB_PATH)
    vocabulary = vocabulary_payload["candidates"]
    by_label = {row["canonical_label"]: row for row in vocabulary}
    by_vocabulary_id = {row["vocabulary_id"]: row for row in vocabulary if row["vocabulary_id"]}
    sense_by_label = {label: stable_sense_id(row["vocabulary_candidate_id"]) for label, row in by_label.items()}

    # Stable cross-round sense crosswalk.  Source labels are display evidence;
    # Round 16A vocabulary-candidate identity is the frozen identity seed.
    r9_candidates = read_tsv(R9_CANDIDATE_PATH)
    r9_candidate_by_label = {row["candidate_label"]: row for row in r9_candidates}
    r9_glosses = read_tsv(R9_GLOSS_PATH)
    r9_senses_by_candidate: dict[str, list[str]] = defaultdict(list)
    for row in r9_glosses:
        r9_senses_by_candidate[row["candidate_id"]].append(row["sense_id"])
    r9_attestations = read_tsv(R9_ATTESTATION_PATH)
    for row in r9_attestations:
        if row["sense_id_if_applicable"]:
            r9_senses_by_candidate[row["candidate_id"]].append(row["sense_id_if_applicable"])

    r13_gap_rows = read_tsv(R13_GAP_PATH)
    r13_sense_by_label: dict[str, list[str]] = defaultdict(list)
    for row in r13_gap_rows:
        ids = split_semicolon(row["candidate_ids"])
        labels = split_semicolon(row["attested_terms"])
        if len(ids) == len(labels):
            for label, sense_id in zip(labels, ids):
                r13_sense_by_label[label].append(sense_id)
    r13_sense_by_label["coloniality"].append("R13-ANNOT-001")

    assessments = read_json(R14_ASSESSMENT_PATH)["assessments"]
    r14_refs_by_label: dict[str, list[str]] = defaultdict(list)
    for assessment in assessments:
        r14_refs_by_label[assessment["nodeA"]].append(assessment["assessmentId"])
        r14_refs_by_label[assessment["nodeB"]].append(assessment["assessmentId"])

    r16_sources = read_tsv(R16_SOURCE_PATH)
    r16_refs_by_label: dict[str, list[str]] = defaultdict(list)
    for row in r16_sources:
        for label in split_semicolon(row["supported_terms"]):
            r16_refs_by_label[label].append(row["source_id"])

    crosswalk_rows: list[dict[str, Any]] = []
    for row in vocabulary:
        label = row["canonical_label"]
        r9 = r9_candidate_by_label.get(label)
        source_concept_ids = [r9["candidate_id"]] if r9 else []
        source_sense_ids = sorted(set(r9_senses_by_candidate.get(r9["candidate_id"], []) if r9 else []))
        source_sense_ids.extend(value for value in sorted(set(r13_sense_by_label.get(label, []))) if value not in source_sense_ids)
        upstream_refs = sorted(set(
            list(row["decision_refs"])
            + list(row["source_attestations"])
            + r14_refs_by_label.get(label, [])
            + r16_refs_by_label.get(label, [])
        ))
        resolution_label = row["merge_target_label"] or label
        resolution_sense_id = sense_by_label[resolution_label]
        if row["disposition"] == "MERGED_SUPERSEDED":
            crosswalk_status = "RESOLVED_MERGED_ALIAS"
            reason = "The superseded label keeps its own audit identity and resolves to the governed active target for association participation."
        elif row["disposition"] == "REJECTED":
            crosswalk_status = "RESOLVED_CONTROL_ONLY"
            reason = "The rejected vocabulary candidate has a stable sense identity only for exclusion and adversarial reconciliation."
        else:
            crosswalk_status = "RESOLVED_CANONICAL"
            reason = "The stable sense identity is derived only from the frozen Round 16A vocabulary-candidate identity."
        material = {
            "participant_sense_id": sense_by_label[label],
            "vocabulary_candidate_id": row["vocabulary_candidate_id"],
            "vocabulary_id": row["vocabulary_id"],
            "canonical_label": label,
            "normalized_label": row["normalized_label"],
            "canonical_resolution_sense_id": resolution_sense_id,
            "disposition": row["disposition"],
            "status": row["status"],
        }
        crosswalk_rows.append({
            **material,
            "bounded_sense": row["bounded_sense"],
            "scope_note": row["scope_note"],
            "merge_target_vocabulary_id": row["merge_target_vocabulary_id"],
            "source_system": "ROUND16A_VOCABULARY_CENSUS_V2",
            "source_concept_ids_json": canonical_json(sorted(set(source_concept_ids))),
            "source_sense_ids_json": canonical_json(source_sense_ids),
            "upstream_authority_refs_json": canonical_json(upstream_refs),
            "authority_path": VOCAB_PATH,
            "authority_record_id": row["vocabulary_candidate_id"],
            "source_sha": SOURCE_SHA,
            "crosswalk_status": crosswalk_status,
            "crosswalk_reason": reason,
            "record_sha256": sha256_text(canonical_json(material)),
        })

    crosswalk_fields = [
        "participant_sense_id", "vocabulary_candidate_id", "vocabulary_id", "canonical_label",
        "normalized_label", "bounded_sense", "scope_note", "disposition", "status",
        "merge_target_vocabulary_id", "canonical_resolution_sense_id", "source_system",
        "source_concept_ids_json", "source_sense_ids_json", "upstream_authority_refs_json",
        "authority_path", "authority_record_id", "source_sha", "crosswalk_status",
        "crosswalk_reason", "record_sha256",
    ]

    occurrences: list[dict[str, Any]] = []
    families: dict[tuple[str, ...], dict[str, Any]] = {}

    def add_occurrence(
        *, trigger_id: str, trigger_class: str, input_surface_id: str, source_path: str,
        record_refs: list[str], labels: list[str], locator: str = "",
        content_hashes: list[str] | None = None, polarity: str = "REVIEW_REQUIRED",
        emission_kind: str = "ASSOCIATION_REVIEW_FAMILY", notes: str = "",
        incidental_or_excluded_labels: list[str] | None = None,
    ) -> None:
        unknown = sorted(set(labels) - set(by_label))
        if unknown:
            raise ValueError(f"unknown governed labels: {unknown}")
        raw_senses = [sense_by_label[label] for label in labels]
        resolved_senses = sorted(set(
            next(row["canonical_resolution_sense_id"] for row in crosswalk_rows if row["participant_sense_id"] == sense_id)
            for sense_id in raw_senses
        ))
        if len(resolved_senses) < 3:
            raise ValueError(f"higher-order occurrence has fewer than three resolved senses: {record_refs}")
        participant_set_key = sha256_text(canonical_json(resolved_senses))
        candidate_id = f"R16B-LOCAL-FAMILY:{participant_set_key}"
        scope_material = {
            "source_path": source_path,
            "record_refs": sorted(record_refs),
            "locator": locator,
            "content_hashes": sorted(content_hashes or []),
        }
        scope_hypothesis_id = stable_id("R16B-SCOPE-HYP", scope_material)
        identity_material = {
            "trigger_class": trigger_class,
            "source_path": source_path,
            "record_refs": sorted(record_refs),
            "locator": locator,
            "content_hashes": sorted(content_hashes or []),
            "raw_participant_sense_ids": raw_senses,
            "selector_version": SELECTOR_VERSION,
        }
        trigger_occurrence_id = stable_id("R16B-TRIGGER-OCC", identity_material)
        occurrence = {
            "trigger_occurrence_id": trigger_occurrence_id,
            "trigger_id": trigger_id,
            "trigger_class": trigger_class,
            "input_surface_id": input_surface_id,
            "source_path": source_path,
            "input_record_refs_json": canonical_json(sorted(record_refs)),
            "locator": locator,
            "content_hashes_json": canonical_json(sorted(content_hashes or [])),
            "raw_participant_labels_json": canonical_json(labels),
            "raw_participant_sense_ids_json": canonical_json(raw_senses),
            "participant_sense_ids_json": canonical_json(resolved_senses),
            "participant_set_key": participant_set_key,
            "scope_hypothesis_id": scope_hypothesis_id,
            "polarity": polarity,
            "emission_kind": emission_kind,
            "candidate_id": candidate_id,
            "incidental_or_excluded_labels_json": canonical_json(sorted(incidental_or_excluded_labels or [])),
            "notes": notes,
            "selector_version": SELECTOR_VERSION,
        }
        occurrence["occurrence_sha256"] = sha256_text(canonical_json(occurrence))
        occurrences.append(occurrence)
        family = families.setdefault(tuple(resolved_senses), {
            "candidate_id": candidate_id,
            "participant_set_key": participant_set_key,
            "participant_sense_ids": resolved_senses,
            "occurrences": [],
        })
        family["occurrences"].append(occurrence)

    # Explicit Round 10 cluster near misses.
    for row in read_tsv(R10_CLUSTER_PATH):
        add_occurrence(
            trigger_id="TRG-007", trigger_class="EXPLICIT_CLUSTER_NEAR_MISS",
            input_surface_id="R16B-LOCAL-SURF-R10-CLUSTERS", source_path=R10_CLUSTER_PATH,
            record_refs=[row["cluster_handoff_id"]], labels=split_semicolon(row["candidate_labels"]),
            content_hashes=[row_hash(row)], polarity="NEAR_MISS_CONTROL",
            emission_kind="CONTROL_AND_REVIEW_FAMILY",
            notes=f"{row['decision']}: {row['reason']}",
        )

    # Round 14 synthetic n-ary local-coherence controls.
    for row in read_json(R14_NARY_PATH)["fixtures"]:
        add_occurrence(
            trigger_id="TRG-007", trigger_class="ROUND14_NARY_FIXTURE",
            input_surface_id="R16B-LOCAL-SURF-R14-NARY", source_path=R14_NARY_PATH,
            record_refs=[row["fixtureId"]], labels=row["nodes"], content_hashes=[row_hash(row)],
            polarity="SYNTHETIC_CONTROL", emission_kind="CONTROL_AND_REVIEW_FAMILY",
            notes=f"Synthetic pair-binding fixture; expectedResult={row['expectedResult']}; not group evidence.",
        )

    # Round 15 fixtures, including split/pruned and hard-negative controls.
    for row in read_json(R15_FIXTURE_PATH)["fixtures"]:
        if len(row["nodeIds"]) >= 3:
            add_occurrence(
                trigger_id="TRG-004", trigger_class="ROUND15_COMPOSITION_FIXTURE",
                input_surface_id="R16B-LOCAL-SURF-R15-FIXTURES", source_path=R15_FIXTURE_PATH,
                record_refs=[row["fixtureId"]], labels=row["nodeIds"], content_hashes=[row_hash(row)],
                polarity="PRIOR_COMPOSITION_RECONCILIATION", emission_kind="PRIOR_STRUCTURE_REVIEW_FAMILY",
                notes="Researcher-authored composition fixture; renderability and fixture admission are not group support.",
            )

    # Round 16 legacy compositions.
    for row in read_json(R16_COMPOSITION_PATH)["compositions"]:
        if len(row["nodeIds"]) >= 3:
            add_occurrence(
                trigger_id="TRG-004", trigger_class="ROUND16_LEGACY_COMPOSITION",
                input_surface_id="R16B-LOCAL-SURF-R16-COMPOSITIONS", source_path=R16_COMPOSITION_PATH,
                record_refs=[row["compositionId"]], labels=row["nodeIds"], content_hashes=[row_hash(row)],
                polarity="PRIOR_COMPOSITION_RECONCILIATION", emission_kind="PRIOR_STRUCTURE_REVIEW_FAMILY",
                notes="Legacy product composition requires independent global-coherence review.",
            )

    registry = read_json(R16A_REGISTRY_PATH)
    for row in registry["association_subgraphs"]:
        if row["node_count"] >= 3:
            add_occurrence(
                trigger_id="TRG-004", trigger_class="ROUND16A_CONNECTED_SUBGRAPH",
                input_surface_id="R16B-LOCAL-SURF-R16A-SUBGRAPHS", source_path=R16A_REGISTRY_PATH,
                record_refs=[row["association_subgraph_id"]],
                labels=[by_vocabulary_id[value]["canonical_label"] for value in row["node_ids"]],
                content_hashes=[row["association_subgraph_hash"]],
                polarity="PAIR_CONNECTIVITY_ONLY", emission_kind="PRIOR_STRUCTURE_REVIEW_FAMILY",
                notes="Connected pair graph is a trigger only; it is not group-level evidence.",
            )
    for row in registry["topology_compositions"]:
        if row["node_count"] >= 3:
            add_occurrence(
                trigger_id="TRG-004", trigger_class="ROUND16A_TOPOLOGY_COMPOSITION",
                input_surface_id="R16B-LOCAL-SURF-R16A-TOPOLOGIES", source_path=R16A_REGISTRY_PATH,
                record_refs=[row["composition_id"]],
                labels=[by_vocabulary_id[value]["canonical_label"] for value in row["node_ids"]],
                content_hashes=[row["topology_composition_hash"]],
                polarity="PAIR_DERIVED_TOPOLOGY_ONLY", emission_kind="PRIOR_STRUCTURE_REVIEW_FAMILY",
                notes=f"Presentation topology {row['topology_family']} is not historical group semantics.",
            )

    read_model = read_json(R16A_READ_MODEL_PATH)
    for composition_id, row in read_model["compositions"].items():
        if len(row["node_ids"]) >= 3:
            add_occurrence(
                trigger_id="TRG-004", trigger_class="ROUND16A_PRODUCTION_COMPOSITION",
                input_surface_id="R16B-LOCAL-SURF-R16A-PRODUCTION", source_path=R16A_READ_MODEL_PATH,
                record_refs=[composition_id],
                labels=[by_vocabulary_id[value]["canonical_label"] for value in row["node_ids"]],
                content_hashes=[row["semantic_hash"]],
                polarity="PRODUCT_RECONCILIATION_REQUIRED", emission_kind="PRIOR_STRUCTURE_REVIEW_FAMILY",
                notes="Product-visible v2 composition requires group-level evidence and global-coherence reconciliation.",
            )

    # Active Round 14 pair assessments sharing an exact source and locator.
    assessment_by_id = {row["assessmentId"]: row for row in assessments}
    active_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_tsv(R14_PROVENANCE_PATH):
        assessment = assessment_by_id[row["assessment_id"]]
        if row["support_role"] == "ASSOCIATION_SUPPORT" and assessment["activeForProximity"]:
            active_groups[(row["source_id"], row["locator"])].append(row)
    active_bundle_count = 0
    for (source_id, locator), rows in sorted(active_groups.items()):
        labels = sorted({
            label for row in rows
            for label in (assessment_by_id[row["assessment_id"]]["nodeA"], assessment_by_id[row["assessment_id"]]["nodeB"])
        })
        if len(labels) >= 3:
            active_bundle_count += 1
            add_occurrence(
                trigger_id="TRG-003", trigger_class="ROUND14_ACTIVE_PAIR_SHARED_LOCUS_BUNDLE",
                input_surface_id="R16B-LOCAL-SURF-R14-PROVENANCE", source_path=R14_PROVENANCE_PATH,
                record_refs=[row["evidence_id"] for row in rows], labels=labels, locator=locator,
                content_hashes=[row_hash(row) for row in rows], polarity="PAIR_SUPPORT_WITHOUT_GROUP_REVIEW",
                emission_kind="SOURCE_BUNDLE_REVIEW_FAMILY",
                notes=f"{source_id}; active pair claims share one exact locator, but group coherence remains unreviewed.",
            )
    if active_bundle_count != 10:
        raise ValueError(f"expected 10 active shared-locus bundles, found {active_bundle_count}")

    r10_attestations = {row["grammar_attestation_id"]: row for row in read_tsv(R10_ATTESTATION_PATH)}
    r10_direct = {
        "GRAM-ATT-001": ["production", "mediation", "consumption"],
        "GRAM-ATT-002": ["production", "mediation", "consumption"],
        "GRAM-ATT-026": ["education", "institutionalization", "professionalization"],
    }
    for record_id, labels in r10_direct.items():
        row = r10_attestations[record_id]
        add_occurrence(
            trigger_id="TRG-002", trigger_class="ROUND10_DIRECT_PASSAGE",
            input_surface_id="R16B-LOCAL-SURF-R10-ATTESTATIONS", source_path=R10_ATTESTATION_PATH,
            record_refs=[record_id], labels=labels, locator=row["page_section_locator"],
            content_hashes=[row["evidence_sha256"]], polarity="LOCATOR_BEARING_REVIEW_REQUIRED",
            emission_kind="DIRECT_PASSAGE_REVIEW_FAMILY",
            notes="Participants are bounded to exact concept terms in the passage or observed governed roles; no support disposition is inherited.",
        )

    r13_evidence = {row["evidence_id"]: row for row in read_tsv(R13_EVIDENCE_PATH)}
    r13_direct = {
        "COMP-EVID-008": ["production", "mediating channels", "consumption"],
        "COMP-EVID-010": ["production", "mediating devices", "consumption"],
        "COMP-EVID-011": ["production", "mediating devices", "consumption"],
        "COMP-EVID-014": ["cultural negotiation", "adaptation", "rejection"],
        "COMP-EVID-021": ["material displacement", "production site", "supply chain", "production", "consumption"],
        "COMP-EVID-026": ["design diplomacy", "exhibition", "propaganda", "trade"],
    }
    for record_id, labels in r13_direct.items():
        row = r13_evidence[record_id]
        add_occurrence(
            trigger_id="TRG-002", trigger_class="ROUND13_DIRECT_POSITIVE_FIELD_PASSAGE",
            input_surface_id="R16B-LOCAL-SURF-R13-EVIDENCE", source_path=R13_EVIDENCE_PATH,
            record_refs=[record_id], labels=labels, locator=row["locator"],
            content_hashes=[row_hash(row)], polarity="LOCATOR_BEARING_REVIEW_REQUIRED",
            emission_kind="DIRECT_PASSAGE_REVIEW_FAMILY",
            notes="Exact positive participant fields trigger whole-group review; the prior row did not decide higher-order support.",
        )

    # The exposition label in COMP-EVID-003 names the bounded case rather than
    # an admitted product concept. Preserve it as an explicit rejected-sense
    # control so that the locator-bearing three-sense configuration cannot
    # disappear from the candidate/exclusion audit.
    row = r13_evidence["COMP-EVID-003"]
    add_occurrence(
        trigger_id="TRG-002", trigger_class="ROUND13_INCIDENTAL_CASE_LABEL_CONTROL",
        input_surface_id="R16B-LOCAL-SURF-R13-EVIDENCE", source_path=R13_EVIDENCE_PATH,
        record_refs=["COMP-EVID-003"], labels=["commodification", "gendering", "Brazilian exposition"],
        locator=row["locator"], content_hashes=[row_hash(row)], polarity="INCIDENTAL_CASE_LABEL_CONTROL",
        emission_kind="CONTROL_AND_REVIEW_FAMILY",
        incidental_or_excluded_labels=["Brazilian exposition"],
        notes="Brazilian exposition is a bounded case label and rejected vocabulary sense, not an active product concept; the configuration remains reviewable as a control.",
    )

    # One qualification-context lead; consumer culture is an annotation, not an
    # automatically admitted participant.
    row = r13_evidence["COMP-EVID-004"]
    grammar_context_row = r10_attestations["GRAM-ATT-027"]
    add_occurrence(
        trigger_id="TRG-002", trigger_class="ROUND13_QUALIFICATION_CONTEXT_EXTENSION",
        input_surface_id="R16B-LOCAL-SURF-R13-EVIDENCE", source_path=R13_EVIDENCE_PATH,
        record_refs=["COMP-EVID-004", f"{R10_ATTESTATION_PATH}#GRAM-ATT-027"],
        labels=["commodification", "consumer culture", "gendering"],
        locator=row["locator"], content_hashes=[row_hash(row), grammar_context_row["evidence_sha256"]], polarity="DISCOVERY_ONLY",
        emission_kind="CONTEXT_EXTENSION_REVIEW_FAMILY",
        notes="Consumer culture occurs in qualification; GRAM-ATT-027 is title-level adjacent corroborating context. Neither admits it as group evidence.",
    )

    # The inactive cultural-transfer/cultural-negotiation assessment reuses the
    # contact-zone locus.  Preserve this as a qualified overlap lead, not support.
    provenance = read_tsv(R14_PROVENANCE_PATH)
    contact_rows = [row for row in provenance if row["source_id"] == "COMP-SRC-013" and row["locator"] == "p.354; Contact Zone section" and row["assessment_id"] in {"R14-ASSOC-013", "R14-ASSOC-014", "R14-ASSOC-015", "R14-ASSOC-022"}]
    add_occurrence(
        trigger_id="TRG-008", trigger_class="ROUND14_QUALIFIED_SHARED_LOCUS_OVERLAP",
        input_surface_id="R16B-LOCAL-SURF-R14-PROVENANCE", source_path=R14_PROVENANCE_PATH,
        record_refs=[row["evidence_id"] for row in contact_rows],
        labels=["adaptation", "cultural negotiation", "cultural transfer", "rejection"],
        locator="p.354; Contact Zone section", content_hashes=[row_hash(row) for row in contact_rows],
        polarity="QUALIFIED_BRIDGE_REVIEW_REQUIRED", emission_kind="OVERLAP_RECONCILIATION_FAMILY",
        notes="Cultural transfer enters only through an inactive qualified cross-source bridge; the quartet is a falsification target, not support.",
    )

    # A hard-negative gendering/mobile-object pair assessment contains a
    # separate concept-only passage that binds cultural mobility, a mobile
    # object, and mediation. Pair disposition must not suppress this sparse
    # higher-order inquiry lead or manufacture any projected pair.
    mobility_row = next(row for row in provenance if row["evidence_id"] == "R14-EVID-025-02")
    mobility_upstream = r13_evidence["COMP-EVID-022"]
    add_occurrence(
        trigger_id="TRG-002", trigger_class="ROUND14_CONCEPT_ONLY_HIGHER_ORDER_LEAD",
        input_surface_id="R16B-LOCAL-SURF-R14-PROVENANCE", source_path=R14_PROVENANCE_PATH,
        record_refs=["R14-EVID-025-02", f"{R13_EVIDENCE_PATH}#COMP-EVID-022"],
        labels=["cultural mobility", "mobile object", "mediation"],
        locator=mobility_row["locator"], content_hashes=[row_hash(mobility_row), row_hash(mobility_upstream)],
        polarity="INQUIRY_ONLY_HIGHER_ORDER_LEAD", emission_kind="DIRECT_PASSAGE_INQUIRY_FAMILY",
        notes="Concept-only source language triggers group review independently of the enclosing hard-negative gendering/mobile-object pair; no pair projection or support disposition is inherited.",
    )

    # Exact repeated archive context: retain exhibition as contextual discovery,
    # photography/typography as participant terms, and photomontage as a rejected
    # incidental/control label.
    archive_rows = [row for row in provenance if row["source_id"] == "R14-ARC-002" and row["locator"] == "Exhibition description"]
    if len(archive_rows) != 4 or len({row["association_context"] for row in archive_rows}) != 1:
        raise ValueError("Round 14 archive duplicate invariant changed")
    for row in archive_rows:
        add_occurrence(
            trigger_id="TRG-002", trigger_class="ROUND14_ARCHIVE_EXACT_CONTEXT_DUPLICATE",
            input_surface_id="R16B-LOCAL-SURF-R14-PROVENANCE", source_path=R14_PROVENANCE_PATH,
            record_refs=[row["evidence_id"]], labels=["exhibition", "photography", "typography"],
            locator=row["locator"], content_hashes=[row_hash(row)], polarity="DISCOVERY_ONLY",
            emission_kind="ARCHIVE_CONTEXT_REVIEW_FAMILY",
            notes="Institutional exhibition context is a discovery lead; the archive row does not itself decide a three-concept association.",
            incidental_or_excluded_labels=["photomontage"],
        )

    # Vocabulary-only source deliberately cannot activate a group.
    r16_source_rows = {row["source_id"]: row for row in r16_sources}
    row = r16_source_rows["R16-SRC-005"]
    add_occurrence(
        trigger_id="TRG-006", trigger_class="ROUND16_VOCABULARY_ONLY_MULTI_TERM",
        input_surface_id="R16B-LOCAL-SURF-R16-SOURCES", source_path=R16_SOURCE_PATH,
        record_refs=["R16-SRC-005"], labels=["craft", "education", "design education"],
        content_hashes=[row_hash(row)], polarity="VOCABULARY_SUPPORT_ONLY",
        emission_kind="VOCABULARY_ONLY_REVIEW_FAMILY",
        notes=row["scope_note"],
    )

    # Same source+locator but two different passage hashes: a deliberate collision
    # review, not a same-passage assertion.
    collision_rows = [row for row in r9_attestations if row["source_id"] == "SRC-0005" and row["page_or_section_locator"] == "title/p.35"]
    if {row["attestation_id"] for row in collision_rows} != {"ATT-0005", "ATT-0018", "ATT-0029"} or len({row["context_sha256"] for row in collision_rows}) != 2:
        raise ValueError("Round 9 collision invariant changed")
    add_occurrence(
        trigger_id="TRG-002", trigger_class="ROUND9_SOURCE_LOCATOR_CONTEXT_COLLISION",
        input_surface_id="R16B-LOCAL-SURF-R09-ATTESTATIONS", source_path=R9_ATTESTATION_PATH,
        record_refs=[row["attestation_id"] for row in collision_rows],
        labels=["appropriation", "creative appropriation", "design exchanges"],
        locator="title/p.35", content_hashes=[row["context_sha256"] for row in collision_rows],
        polarity="CONTEXT_COLLISION_REVIEW_REQUIRED", emission_kind="COLLISION_REVIEW_FAMILY",
        notes="The common source and locator contain two context hashes; no common-passage or group-support claim is made.",
    )

    occurrence_ids = [row["trigger_occurrence_id"] for row in occurrences]
    if len(occurrence_ids) != len(set(occurrence_ids)):
        raise ValueError("duplicate trigger occurrence identity")

    label_by_resolved_sense: dict[str, str] = {}
    disposition_by_resolved_sense: dict[str, str] = {}
    for row in crosswalk_rows:
        resolved = row["canonical_resolution_sense_id"]
        if row["participant_sense_id"] == resolved:
            label_by_resolved_sense[resolved] = row["canonical_label"]
            disposition_by_resolved_sense[resolved] = row["disposition"]

    family_rows: list[dict[str, Any]] = []
    candidate_objects: list[dict[str, Any]] = []
    for sense_key, family in sorted(families.items(), key=lambda item: (len(item[0]), item[0])):
        family_occurrences = family["occurrences"]
        labels = [label_by_resolved_sense[value] for value in sense_key]
        dispositions = [disposition_by_resolved_sense[value] for value in sense_key]
        counts = Counter(dispositions)
        eligibility = "CONTROL_ONLY_REJECTED_PARTICIPANT" if counts["REJECTED"] else "REVIEW_ELIGIBLE_NOT_VALIDATED"
        family_material = {
            "candidate_id": family["candidate_id"],
            "participant_sense_ids": list(sense_key),
            "scope_resolution_status": "UNRESOLVED_MAY_SPLIT_BY_CASE",
            "occurrence_ids": sorted(row["trigger_occurrence_id"] for row in family_occurrences),
        }
        candidate_object = {
            "candidate_id": family["candidate_id"],
            "candidate_object_kind": "LOCAL_PARTICIPANT_SET_REVIEW_FAMILY_NOT_ASSOCIATION",
            "participant_set_key": family["participant_set_key"],
            "participant_sense_ids": list(sense_key),
            "canonical_labels": labels,
            "arity": len(sense_key),
            "order_semantics": "UNRESOLVED",
            "role_semantics": "UNRESOLVED",
            "scope_resolution_status": "UNRESOLVED_MAY_SPLIT_BY_CASE",
            "case_resolution_status": "UNRESOLVED",
            "trigger_occurrence_ids": sorted(row["trigger_occurrence_id"] for row in family_occurrences),
            "trigger_ids": sorted({row["trigger_id"] for row in family_occurrences}),
            "participant_eligibility": eligibility,
            "lifecycle_state": "DISCOVERED",
            "proposed_disposition": "PENDING_GOVERNED_REVIEW",
            "evidence_review_status": "NOT_STARTED",
            "global_coherence_status": "NOT_REVIEWED",
            "product_eligibility": "INELIGIBLE_PENDING_GOVERNED_REVIEW",
            "association_identity_frozen": False,
            "family_content_sha256": sha256_text(canonical_json(family_material)),
        }
        candidate_objects.append(candidate_object)
        family_rows.append({
            **{key: value for key, value in candidate_object.items() if key not in {"participant_sense_ids", "canonical_labels", "trigger_occurrence_ids", "trigger_ids"}},
            "participant_sense_ids_json": canonical_json(candidate_object["participant_sense_ids"]),
            "canonical_labels_json": canonical_json(candidate_object["canonical_labels"]),
            "occurrence_count": len(family_occurrences),
            "trigger_occurrence_ids_json": canonical_json(candidate_object["trigger_occurrence_ids"]),
            "trigger_ids_json": canonical_json(candidate_object["trigger_ids"]),
            "emission_kinds_json": canonical_json(sorted({row["emission_kind"] for row in family_occurrences})),
            "active_participant_count": counts["ACTIVE"],
            "research_only_participant_count": counts["RESEARCH_ONLY"],
            "rejected_participant_count": counts["REJECTED"],
        })

    # Open n-ary grammar templates stay outside the closed participant-set count.
    open_arities = {"MULTIPARTY", "2+", "3", "3+", "STRUCTURAL"}
    role_rows = [row for row in read_tsv(R10_ROLE_PATH) if row["arity"] in open_arities]
    open_role_rows: list[dict[str, Any]] = []
    for row in role_rows:
        label = row["candidate_label"]
        relation_sense_id = sense_by_label[label]
        material = {
            "candidate_id": row["candidate_id"], "arity": row["arity"],
            "roles": [row["subject_role"], row["target_role"], row["additional_party_roles"]],
            "source_support_ids": split_semicolon(row["source_support_ids"]),
        }
        open_role_rows.append({
            "participant_resolution_queue_id": stable_id("R16B-PARTICIPANT-QUEUE", material),
            "source_path": R10_ROLE_PATH,
            "source_candidate_id": row["candidate_id"],
            "relation_label": label,
            "relation_participant_sense_id": relation_sense_id,
            "declared_argument_arity": row["arity"],
            "subject_role": row["subject_role"],
            "target_role": row["target_role"],
            "additional_party_roles": row["additional_party_roles"],
            "required_context": row["required_context"],
            "required_qualification": row["required_qualification"],
            "source_support_ids_json": canonical_json(split_semicolon(row["source_support_ids"])),
            "participant_resolution_status": "OPEN",
            "candidate_emitted": "false",
            "reason": "Round 10 arity describes argument roles, not a closed governed concept participant set; role nouns are not promoted to vocabulary concepts.",
            "record_sha256": row_hash(material),
        })

    # Active pair-graph isolates receive explicit product-accessibility audits.
    graph = read_json(R16A_GRAPH_PATH)
    isolated_nodes = [row for row in graph["nodes"] if row["isolated"]]
    isolated_rows: list[dict[str, Any]] = []
    for node in sorted(isolated_nodes, key=lambda row: row["canonical_label"]):
        sense_id = sense_by_label[node["canonical_label"]]
        related = sorted(row["candidate_id"] for row in candidate_objects if sense_id in row["participant_sense_ids"])
        isolated_rows.append({
            "isolation_audit_id": stable_id("R16B-ISOLATED-AUDIT", {"vocabulary_id": node["vocabulary_id"]}),
            "vocabulary_id": node["vocabulary_id"],
            "participant_sense_id": sense_id,
            "canonical_label": node["canonical_label"],
            "round16a_pair_degree": node["degree"],
            "local_candidate_family_ids_json": canonical_json(related),
            "higher_order_composability_proven": "false",
            "product_accessibility_disposition": "OPEN",
            "required_next_action": "Review exact group evidence and either validate a product path, keep inquiry-only, reclassify vocabulary, or record an explicit non-product policy.",
        })

    # Selected row-addressable prior-object universe where duplication is reasonable.
    # The 749,944-transition LFS ledger is covered cryptographically in the set
    # manifest rather than copied into a second giant file.
    prior_rows: list[dict[str, Any]] = []
    candidate_by_sense_set = {tuple(row["participant_sense_ids"]): row["candidate_id"] for row in candidate_objects}

    def candidate_for_senses(senses: list[str]) -> str:
        return candidate_by_sense_set.get(tuple(sorted(set(senses))), "")

    def senses_for_labels(labels: list[str]) -> list[str]:
        return sorted(set(
            next(row["canonical_resolution_sense_id"] for row in crosswalk_rows if row["canonical_label"] == label)
            for label in labels
        ))

    def senses_for_vocabulary_ids(ids: list[str]) -> list[str]:
        return senses_for_labels([by_vocabulary_id[value]["canonical_label"] for value in ids])

    def add_prior(
        object_type: str, prior_id: str, source_path: str, source_record_ref: str,
        senses: list[str] | None = None, parent_ids: list[str] | None = None,
        association_ids: list[str] | None = None, topology: str = "", prior_status: str = "",
        coverage_mode: str = "ROW_EXACT", extra: dict[str, Any] | None = None,
    ) -> None:
        senses = sorted(set(senses or []))
        candidate_id = candidate_for_senses(senses) if len(senses) >= 3 else ""
        if len(senses) >= 3 and candidate_id:
            status = "HIGHER_ORDER_FAMILY_REVIEW_PENDING"
        elif len(senses) == 2:
            status = "PAIRWISE_BASELINE_RECONCILIATION_PENDING"
        else:
            status = "OBJECT_POLICY_RECONCILIATION_PENDING"
        material = {
            "prior_object_type": object_type, "prior_id": prior_id,
            "source_path": source_path, "source_record_ref": source_record_ref,
            "participant_sense_ids": senses, "parent_ids": sorted(parent_ids or []),
            "association_ids": sorted(association_ids or []), "topology": topology,
            "prior_status": prior_status, "candidate_id": candidate_id,
            "extra": extra or {},
        }
        prior_rows.append({
            "prior_object_type": object_type,
            "prior_id": prior_id,
            "source_path": source_path,
            "source_record_ref": source_record_ref,
            "participant_set_key": sha256_text(canonical_json(senses)) if senses else "",
            "participant_sense_ids_json": canonical_json(senses),
            "prior_parent_ids_json": canonical_json(sorted(parent_ids or [])),
            "prior_association_ids_json": canonical_json(sorted(association_ids or [])),
            "prior_topology": topology,
            "prior_status": prior_status,
            "round16b_candidate_ids_json": canonical_json([candidate_id] if candidate_id else []),
            "reconciliation_status": status,
            "required_next_action": "Assign an evidence and global-coherence disposition, then regenerate or retire downstream product objects without silently carrying v2 semantics.",
            "coverage_mode": coverage_mode,
            "record_sha256": row_hash(material),
        })

    r15_fixtures = read_json(R15_FIXTURE_PATH)["fixtures"]
    r15_fixture_by_id = {row["fixtureId"]: row for row in r15_fixtures}
    for row in r15_fixtures:
        add_prior("ROUND15_FIXTURE", row["fixtureId"], R15_FIXTURE_PATH, row["fixtureId"],
                  senses_for_labels(row["nodeIds"]), association_ids=row["associationIds"],
                  topology=row["topologyRequest"], prior_status=row["fixtureFamily"])
    r15_decisions = read_json(R15_DECISION_PATH)["images"]
    for row in r15_decisions:
        semantic = row["semantic_core"]
        fixture_id = row["audit"]["fixture_id"]
        add_prior("ROUND15_SEMANTIC_IMAGE", semantic["semantic_image_id"], R15_DECISION_PATH,
                  semantic["semantic_image_id"], senses_for_labels(semantic["node_ids"]),
                  parent_ids=[fixture_id], association_ids=semantic["qualified_association_ids"],
                  topology=semantic["topology_type"], prior_status="ROUND15_ENGINE_OUTPUT")
    r15_results = read_tsv(R15_RESULT_PATH)
    for row in r15_results:
        fixture = r15_fixture_by_id[row["fixture_id"]]
        add_prior("ROUND15_FIXTURE_RESULT", row["fixture_id"], R15_RESULT_PATH, row["fixture_id"],
                  senses_for_labels(fixture["nodeIds"]), parent_ids=[row["fixture_id"]],
                  association_ids=fixture["associationIds"], topology=row["topology_type"],
                  prior_status=row["status"])
    r16_compositions = read_json(R16_COMPOSITION_PATH)["compositions"]
    r16_composition_senses: dict[str, list[str]] = {}
    for row in r16_compositions:
        r16_composition_senses[row["compositionId"]] = senses_for_labels(row["nodeIds"])
        add_prior("ROUND16_LEGACY_COMPOSITION", row["compositionId"], R16_COMPOSITION_PATH, row["compositionId"],
                  senses_for_labels(row["nodeIds"]), association_ids=row["associationIds"],
                  topology=row["topologyRequest"], prior_status="LEGACY_PRODUCT_COMPOSITION")
    r16_read_model = read_json(R16_READ_MODEL_PATH)
    for composition_id, row in r16_read_model["compositions"].items():
        semantic = row["round15_semantic_image"]["semantic_core"]
        add_prior("ROUND16_EMBEDDED_SEMANTIC_IMAGE", semantic["semantic_image_id"], R16_READ_MODEL_PATH,
                  f"compositions/{composition_id}/round15_semantic_image", r16_composition_senses[composition_id],
                  parent_ids=[composition_id], association_ids=semantic["qualified_association_ids"],
                  topology=semantic["topology_type"], prior_status="ROUND16_EMBEDDED_ROUND15_OUTPUT")
    for map_id, row in r16_read_model["maps"].items():
        senses = sorted(set(value for composition_id in row["composition_ids"] for value in r16_composition_senses[composition_id]))
        add_prior("ROUND16_MAP", map_id, R16_READ_MODEL_PATH, f"maps/{map_id}", senses,
                  parent_ids=row["composition_ids"], association_ids=row["association_ids"],
                  prior_status=f"CATEGORY_MAP:{row['category_id']}")
    for tree_key, row in r16_read_model["trees"].items():
        composition_id = tree_key.split("|", 1)[0]
        add_prior("ROUND16_TREE", tree_key, R16_READ_MODEL_PATH, f"trees/{tree_key}",
                  r16_composition_senses[composition_id], parent_ids=[composition_id],
                  association_ids=row["tree_association_ids"], prior_status="PLAIN_TEXT_TREE_V1")
    r16_state_composition: dict[str, str] = {}
    for state_id, row in r16_read_model["states"].items():
        composition_id = row["selected_composition_id"]
        r16_state_composition[state_id] = composition_id
        add_prior("ROUND16_STATE", state_id, R16_READ_MODEL_PATH, f"states/{state_id}",
                  r16_composition_senses[composition_id], parent_ids=[composition_id, row["map_id"]],
                  association_ids=row["visible_association_ids"], prior_status="REACHABLE_V1_STATE")
    for transition_key, next_state_id in r16_read_model["transitions"].items():
        state_hash = transition_key.split("|", 1)[0]
        current_state_id = r16_read_model["states_by_hash"][state_hash]
        composition_id = r16_state_composition[current_state_id]
        add_prior("ROUND16_TRANSITION", transition_key, R16_READ_MODEL_PATH, f"transitions/{transition_key}",
                  r16_composition_senses[composition_id], parent_ids=[current_state_id, next_state_id, composition_id],
                  prior_status="DERIVED_V1_TRANSITION")
    for row in r16_read_model["workflows"]:
        composition_id = row["composition_id"]
        add_prior("ROUND16_WORKFLOW", row["workflow_id"], R16_READ_MODEL_PATH,
                  f"workflows/{row['workflow_id']}", r16_composition_senses[composition_id],
                  parent_ids=[composition_id, row["map_id"], row["state_id"]], prior_status="V1_WORKFLOW")
    for manifest_key, row in r16_read_model["export_manifests"].items():
        composition_id = row["selected_composition_id"]
        add_prior("ROUND16_EXPORT", row["export_id"], R16_READ_MODEL_PATH,
                  f"export_manifests/{manifest_key}", r16_composition_senses[composition_id],
                  parent_ids=[composition_id, row["map_id"], manifest_key],
                  association_ids=row["association_ids"], prior_status=f"V1_EXPORT:{row['export_preset']}")
    for row in r16_read_model["vocabulary"]:
        add_prior("ROUND16_VOCABULARY_REPRESENTATION", row["vocabulary_id"], R16_READ_MODEL_PATH,
                  f"vocabulary/{row['vocabulary_id']}", senses_for_vocabulary_ids([row["vocabulary_id"]]),
                  prior_status=row["activation_status"])
    for row in r16_read_model["associations"]:
        add_prior("ROUND16_ASSOCIATION_REPRESENTATION", row["association_id"], R16_READ_MODEL_PATH,
                  f"associations/{row['association_id']}", senses_for_vocabulary_ids(row["endpoint_vocabulary_ids"]),
                  association_ids=[row["association_id"]], prior_status=row["support_status"])
    for row in r16_read_model["categories"]:
        add_prior("ROUND16_CATEGORY_REPRESENTATION", row["category_id"], R16_READ_MODEL_PATH,
                  f"categories/{row['category_id']}", parent_ids=[row["map_id"]],
                  prior_status="V1_CATEGORY_REPRESENTATION")
    for key, value in r16_read_model["source_inventory"].items():
        add_prior("ROUND16_SOURCE_INVENTORY_ENTRY", key, R16_READ_MODEL_PATH,
                  f"source_inventory/{key}", prior_status=f"PATH:{value}")
    for row in r16_read_model["failed_associations_audit_only"]:
        add_prior("ROUND16_FAILED_ASSOCIATION_AUDIT", row["association_id"], R16_READ_MODEL_PATH,
                  f"failed_associations_audit_only/{row['association_id']}",
                  senses_for_labels(row["endpoint_labels"]), association_ids=[row["association_id"]],
                  prior_status=f"{row['support_status']}:HARD_NEGATIVE={str(row['hard_negative']).lower()}")
    for state_hash, state_id in r16_read_model["states_by_hash"].items():
        composition_id = r16_state_composition[state_id]
        add_prior("ROUND16_STATE_HASH_INDEX", state_hash, R16_READ_MODEL_PATH,
                  f"states_by_hash/{state_hash}", r16_composition_senses[composition_id],
                  parent_ids=[state_id, composition_id], prior_status="V1_STATE_HASH_INDEX")
    for key, value in r16_read_model["capabilities"].items():
        add_prior("ROUND16_CAPABILITY_FIELD", key, R16_READ_MODEL_PATH,
                  f"capabilities/{key}", prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}")
    for key, value in r16_read_model["database"].items():
        add_prior("ROUND16_DATABASE_AUTHORITY_FIELD", key, R16_READ_MODEL_PATH,
                  f"database/{key}", prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}")
    for row in vocabulary:
        add_prior("ROUND16A_VOCABULARY_CANDIDATE", row["vocabulary_candidate_id"], VOCAB_PATH,
                  row["vocabulary_candidate_id"], [sense_by_label[row["canonical_label"]]],
                  prior_status=row["disposition"])
    pair_rows = read_tsv(R16A_PAIR_PATH)
    for row in pair_rows:
        add_prior("ROUND16A_PAIR_CENSUS", row["pair_id"], R16A_PAIR_PATH, row["pair_id"],
                  senses_for_vocabulary_ids([row["vocabulary_id_a"], row["vocabulary_id_b"]]),
                  association_ids=[row["pair_id"]], prior_status=row["final_status"])
    for row in graph["edges"]:
        add_prior("ROUND16A_ACTIVE_PAIR_ASSOCIATION", row["association_id"], R16A_GRAPH_PATH,
                  row["association_id"], senses_for_vocabulary_ids([row["vocabulary_id_a"], row["vocabulary_id_b"]]),
                  association_ids=[row["association_id"]], prior_status=row["support_status"])
    for row in registry["association_subgraphs"]:
        add_prior("ROUND16A_ASSOCIATION_SUBGRAPH", row["association_subgraph_id"], R16A_REGISTRY_PATH,
                  row["association_subgraph_id"], senses_for_vocabulary_ids(row["node_ids"]),
                  association_ids=row["association_ids"], prior_status="PAIR_DERIVED_CONNECTED_SUBGRAPH")
    for row in registry["round16_legacy_reconciliation"]:
        add_prior("ROUND16A_LEGACY_RECONCILIATION", row["legacy_composition_id"], R16A_REGISTRY_PATH,
                  row["legacy_composition_id"], r16_composition_senses[row["legacy_composition_id"]],
                  parent_ids=[row["round16a_composition_id"]] if row["round16a_composition_id"] else [],
                  prior_status=f"{row['disposition']}:{row['reason']}")
    for row in registry["topology_compositions"]:
        add_prior("ROUND16A_TOPOLOGY_COMPOSITION", row["composition_id"], R16A_REGISTRY_PATH,
                  row["composition_id"], senses_for_vocabulary_ids(row["node_ids"]),
                  parent_ids=[row["association_subgraph_id"]], association_ids=row["association_ids"],
                  topology=row["topology_family"], prior_status="VALID_PAIR_DERIVED_TOPOLOGY")
    for row in registry["round15_adapter_records"]:
        subgraph = next(item for item in registry["association_subgraphs"] if item["association_subgraph_id"] == row["association_subgraph_id"])
        add_prior("ROUND16A_ROUND15_ADAPTER_RECORD", row["fixture_id"], R16A_REGISTRY_PATH,
                  row["fixture_id"], senses_for_vocabulary_ids(subgraph["node_ids"]),
                  parent_ids=[row["association_subgraph_id"]],
                  association_ids=row["admitted_round14_association_ids"],
                  topology=row["frozen_round15_topology_type"], prior_status="ROUND15_ADAPTER_OUTPUT")
    for row in registry["category_entries"]:
        add_prior("ROUND16A_CATEGORY_ENTRY", row["category_entry_id"], R16A_REGISTRY_PATH,
                  row["category_entry_id"], senses_for_vocabulary_ids(row["node_ids"]),
                  parent_ids=[row["composition_id"]] + row["production_composition_ids"],
                  association_ids=row["association_ids"], prior_status=row["category_id"])
    for topology in registry["topology_compositions"]:
        for seed in topology["seed_variants"]:
            add_prior("ROUND16A_SEED_VARIANT", seed["seed_id"], R16A_REGISTRY_PATH,
                      seed["seed_id"], senses_for_vocabulary_ids(topology["node_ids"]),
                      parent_ids=[topology["composition_id"]], association_ids=topology["association_ids"],
                      topology=topology["topology_family"], prior_status="SEED_PRESENTATION_VARIANT")

    production_senses: dict[str, list[str]] = {}
    for composition_id, row in read_model["compositions"].items():
        senses = senses_for_vocabulary_ids(row["node_ids"])
        production_senses[composition_id] = senses
        add_prior("ROUND16A_PRODUCTION_COMPOSITION", composition_id, R16A_READ_MODEL_PATH, composition_id,
                  senses, parent_ids=[row["category_entry_id"], row["seed_id"]],
                  association_ids=row["association_ids"], topology=row["topology_family"],
                  prior_status="PRODUCT_VISIBLE_V2")

    for row in read_model["vocabulary"]:
        add_prior("ROUND16A_VOCABULARY_REPRESENTATION", row["vocabulary_id"], R16A_READ_MODEL_PATH,
                  f"vocabulary/{row['vocabulary_id']}", senses_for_vocabulary_ids([row["vocabulary_id"]]),
                  prior_status=row["activation_status"])
    for row in read_model["associations"]:
        add_prior("ROUND16A_ASSOCIATION_REPRESENTATION", row["association_id"], R16A_READ_MODEL_PATH,
                  f"associations/{row['association_id']}", senses_for_vocabulary_ids(row["endpoint_vocabulary_ids"]),
                  association_ids=[row["association_id"]], prior_status=row["support_status"])
    registry_categories_by_id = {row["category_entry_id"]: row for row in registry["category_entries"]}
    for row in read_model["categories"]:
        authority = registry_categories_by_id[row["category_entry_id"]]
        add_prior("ROUND16A_CATEGORY_REPRESENTATION", row["category_entry_id"], R16A_READ_MODEL_PATH,
                  f"categories/{row['category_entry_id']}", senses_for_vocabulary_ids(authority["node_ids"]),
                  parent_ids=row["composition_ids"] + [row["initial_state_id"]],
                  association_ids=authority["association_ids"], prior_status=row["category_id"])
    for state_hash, state_id in read_model["states_by_hash"].items():
        composition_id = read_model["states"][state_id]["composition_id"]
        add_prior("ROUND16A_STATE_HASH_INDEX", state_hash, R16A_READ_MODEL_PATH,
                  f"states_by_hash/{state_hash}", production_senses[composition_id],
                  parent_ids=[state_id, composition_id], prior_status="V2_STATE_HASH_INDEX")
    for key, value in read_model["transitions"].items():
        add_prior("ROUND16A_TRANSITION_DESCRIPTOR_FIELD", key, R16A_READ_MODEL_PATH,
                  f"transitions/{key}", prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}")
    for key, value in read_model["capabilities"].items():
        add_prior("ROUND16A_CAPABILITY_FIELD", key, R16A_READ_MODEL_PATH,
                  f"capabilities/{key}", prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}")
    for key, value in read_model["database"].items():
        add_prior("ROUND16A_DATABASE_AUTHORITY_FIELD", key, R16A_READ_MODEL_PATH,
                  f"database/{key}", prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}")

    state_rows = read_tsv(R16A_STATE_PATH)
    for row in state_rows:
        add_prior("ROUND16A_STATE", row["state_id"], R16A_STATE_PATH, row["state_id"],
                  production_senses[row["composition_id"]],
                  parent_ids=[row["composition_id"], row["category_entry_id"], row["seed_id"]],
                  association_ids=json.loads(row["visible_association_ids"]), prior_status="REACHABLE_V2_STATE")
    workflow_rows = read_tsv(R16A_WORKFLOW_PATH)
    for row in workflow_rows:
        add_prior("ROUND16A_WORKFLOW", row["workflow_id"], R16A_WORKFLOW_PATH, row["workflow_id"],
                  production_senses[row["composition_id"]],
                  parent_ids=[row["composition_id"], row["category_entry_id"], row["seed_id"], row["start_state_id"], row["target_state_id"]],
                  prior_status="REPLAYED_V2_WORKFLOW")
    export_rows = read_tsv(R16A_EXPORT_PATH)
    for row in export_rows:
        add_prior("ROUND16A_EXPORT", row["export_variant_id"], R16A_EXPORT_PATH, row["export_variant_id"],
                  production_senses[row["composition_id"]],
                  parent_ids=[row["composition_id"], row["category_entry_id"], row["seed_id"], row["state_id"]],
                  prior_status=f"V2_EXPORT:{row['export_preset']}")
    enumeration_rows = read_tsv(R16A_ENUMERATION_PATH)
    for index, row in enumerate(enumeration_rows, 1):
        prior_id = f"{row['association_subgraph_id']}|{row['topology_family']}"
        add_prior("ROUND16A_TOPOLOGY_ENUMERATION_RESULT", prior_id, R16A_ENUMERATION_PATH, str(index),
                  senses_for_vocabulary_ids(json.loads(row["node_ids"])),
                  parent_ids=[row["association_subgraph_id"]], association_ids=json.loads(row["association_ids"]),
                  topology=row["topology_family"], prior_status=row["decision"])
    rejection_rows = read_tsv(R16A_REJECTION_PATH)
    for row in rejection_rows:
        subgraph = next(item for item in registry["association_subgraphs"] if item["association_subgraph_id"] == row["association_subgraph_id"])
        add_prior("ROUND16A_TOPOLOGY_REJECTION", row["rejection_id"], R16A_REJECTION_PATH, row["rejection_id"],
                  senses_for_vocabulary_ids(subgraph["node_ids"]), parent_ids=[row["association_subgraph_id"]],
                  association_ids=subgraph["association_ids"], topology=row["topology_family"], prior_status=row["reason_code"])

    # Exact set manifest, including the large transition set without duplication.
    transition_count, transition_id_hash = scan_sorted_tsv_ids(R16A_TRANSITION_PATH, "transition_id")
    r16_export_ids = [row["export_id"] for row in r16_read_model["export_manifests"].values()]
    r16_seed_ids = [seed["seed_id"] for row in registry["topology_compositions"] for seed in row["seed_variants"]]
    set_specs = [
        ("ROUND15_FIXTURE", R15_FIXTURE_PATH, "json:fixtures", [row["fixtureId"] for row in r15_fixtures], True),
        ("ROUND15_SEMANTIC_IMAGE", R15_DECISION_PATH, "json:images", [row["semantic_core"]["semantic_image_id"] for row in r15_decisions], True),
        ("ROUND15_FIXTURE_RESULT", R15_RESULT_PATH, "tsv_rows", [row["fixture_id"] for row in r15_results], True),
        ("ROUND16_LEGACY_COMPOSITION", R16_COMPOSITION_PATH, "json:compositions", [row["compositionId"] for row in r16_compositions], True),
        ("ROUND16_VOCABULARY_REPRESENTATION", R16_READ_MODEL_PATH, "json:vocabulary", [row["vocabulary_id"] for row in r16_read_model["vocabulary"]], True),
        ("ROUND16_ASSOCIATION_REPRESENTATION", R16_READ_MODEL_PATH, "json:associations", [row["association_id"] for row in r16_read_model["associations"]], True),
        ("ROUND16_CATEGORY_REPRESENTATION", R16_READ_MODEL_PATH, "json:categories", [row["category_id"] for row in r16_read_model["categories"]], True),
        ("ROUND16_SOURCE_INVENTORY_ENTRY", R16_READ_MODEL_PATH, "json:source_inventory", list(r16_read_model["source_inventory"]), True),
        ("ROUND16_FAILED_ASSOCIATION_AUDIT", R16_READ_MODEL_PATH, "json:failed_associations_audit_only", [row["association_id"] for row in r16_read_model["failed_associations_audit_only"]], True),
        ("ROUND16_STATE_HASH_INDEX", R16_READ_MODEL_PATH, "json:states_by_hash", list(r16_read_model["states_by_hash"]), True),
        ("ROUND16_CAPABILITY_FIELD", R16_READ_MODEL_PATH, "json:capabilities", list(r16_read_model["capabilities"]), True),
        ("ROUND16_DATABASE_AUTHORITY_FIELD", R16_READ_MODEL_PATH, "json:database", list(r16_read_model["database"]), True),
        ("ROUND16_EMBEDDED_SEMANTIC_IMAGE", R16_READ_MODEL_PATH, "json:compositions", [row["round15_semantic_image"]["semantic_core"]["semantic_image_id"] for row in r16_read_model["compositions"].values()], True),
        ("ROUND16_MAP", R16_READ_MODEL_PATH, "json:maps", list(r16_read_model["maps"]), True),
        ("ROUND16_TREE", R16_READ_MODEL_PATH, "json:trees", list(r16_read_model["trees"]), True),
        ("ROUND16_STATE", R16_READ_MODEL_PATH, "json:states", list(r16_read_model["states"]), True),
        ("ROUND16_TRANSITION", R16_READ_MODEL_PATH, "json:transitions", list(r16_read_model["transitions"]), True),
        ("ROUND16_WORKFLOW", R16_READ_MODEL_PATH, "json:workflows", [row["workflow_id"] for row in r16_read_model["workflows"]], True),
        ("ROUND16_EXPORT_MANIFEST_KEY", R16_READ_MODEL_PATH, "json:export_manifests", list(r16_read_model["export_manifests"]), False),
        ("ROUND16_EXPORT", R16_READ_MODEL_PATH, "json:export_manifests", r16_export_ids, True),
        ("ROUND16A_VOCABULARY_CANDIDATE", VOCAB_PATH, "json:candidates", [row["vocabulary_candidate_id"] for row in vocabulary], True),
        ("ROUND16A_PAIR_CENSUS", R16A_PAIR_PATH, "tsv_rows", [row["pair_id"] for row in pair_rows], True),
        ("ROUND16A_ACTIVE_PAIR_ASSOCIATION", R16A_GRAPH_PATH, "json:edges", [row["association_id"] for row in graph["edges"]], True),
        ("ROUND16A_ASSOCIATION_SUBGRAPH", R16A_REGISTRY_PATH, "json:association_subgraphs", [row["association_subgraph_id"] for row in registry["association_subgraphs"]], True),
        ("ROUND16A_LEGACY_RECONCILIATION", R16A_REGISTRY_PATH, "json:round16_legacy_reconciliation", [row["legacy_composition_id"] for row in registry["round16_legacy_reconciliation"]], True),
        ("ROUND16A_ROUND15_ADAPTER_RECORD", R16A_REGISTRY_PATH, "json:round15_adapter_records", [row["fixture_id"] for row in registry["round15_adapter_records"]], True),
        ("ROUND16A_TOPOLOGY_COMPOSITION", R16A_REGISTRY_PATH, "json:topology_compositions", [row["composition_id"] for row in registry["topology_compositions"]], True),
        ("ROUND16A_CATEGORY_ENTRY", R16A_REGISTRY_PATH, "json:category_entries", [row["category_entry_id"] for row in registry["category_entries"]], True),
        ("ROUND16A_SEED_VARIANT", R16A_REGISTRY_PATH, "json:topology_compositions", r16_seed_ids, True),
        ("ROUND16A_PRODUCTION_COMPOSITION", R16A_READ_MODEL_PATH, "json:compositions", list(read_model["compositions"]), True),
        ("ROUND16A_VOCABULARY_REPRESENTATION", R16A_READ_MODEL_PATH, "json:vocabulary", [row["vocabulary_id"] for row in read_model["vocabulary"]], True),
        ("ROUND16A_ASSOCIATION_REPRESENTATION", R16A_READ_MODEL_PATH, "json:associations", [row["association_id"] for row in read_model["associations"]], True),
        ("ROUND16A_CATEGORY_REPRESENTATION", R16A_READ_MODEL_PATH, "json:categories", [row["category_entry_id"] for row in read_model["categories"]], True),
        ("ROUND16A_STATE_HASH_INDEX", R16A_READ_MODEL_PATH, "json:states_by_hash", list(read_model["states_by_hash"]), True),
        ("ROUND16A_TRANSITION_DESCRIPTOR_FIELD", R16A_READ_MODEL_PATH, "json:transitions", list(read_model["transitions"]), True),
        ("ROUND16A_CAPABILITY_FIELD", R16A_READ_MODEL_PATH, "json:capabilities", list(read_model["capabilities"]), True),
        ("ROUND16A_DATABASE_AUTHORITY_FIELD", R16A_READ_MODEL_PATH, "json:database", list(read_model["database"]), True),
        ("ROUND16A_STATE", R16A_STATE_PATH, "tsv_rows", [row["state_id"] for row in state_rows], True),
        ("ROUND16A_WORKFLOW", R16A_WORKFLOW_PATH, "tsv_rows", [row["workflow_id"] for row in workflow_rows], True),
        ("ROUND16A_EXPORT", R16A_EXPORT_PATH, "tsv_rows", [row["export_variant_id"] for row in export_rows], True),
        ("ROUND16A_TOPOLOGY_ENUMERATION_RESULT", R16A_ENUMERATION_PATH, "tsv_rows", [f"{row['association_subgraph_id']}|{row['topology_family']}" for row in enumeration_rows], True),
        ("ROUND16A_TOPOLOGY_REJECTION", R16A_REJECTION_PATH, "tsv_rows", [row["rejection_id"] for row in rejection_rows], True),
    ]
    set_manifest_rows = []
    for object_type, path, selector, ids, row_exact in set_specs:
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate prior IDs for {object_type}")
        set_manifest_rows.append({
            "prior_object_type": object_type,
            "source_path": path,
            "record_selector": selector,
            "record_count": len(ids),
            "unique_id_count": len(set(ids)),
            "sorted_id_set_sha256": id_set_hash(ids),
            "source_bytes": (REPO / path).stat().st_size,
            "source_sha256": sha256_file(REPO / path),
            "row_exact_reconciliation_ledger": str(row_exact).lower(),
            "coverage_status": "COMPLETE_SOURCE_SET_BOUND",
            "next_action": "Final disposition and v3 regeneration remain pending; no v2 object is silently accepted as higher-order-valid.",
        })
    set_manifest_rows.append({
        "prior_object_type": "ROUND16A_TRANSITION",
        "source_path": R16A_TRANSITION_PATH,
        "record_selector": "tsv_rows:transition_id",
        "record_count": transition_count,
        "unique_id_count": transition_count,
        "sorted_id_set_sha256": transition_id_hash,
        "source_bytes": (REPO / R16A_TRANSITION_PATH).stat().st_size,
        "source_sha256": sha256_file(REPO / R16A_TRANSITION_PATH),
        "row_exact_reconciliation_ledger": "false",
        "coverage_status": "COMPLETE_SOURCE_SET_BOUND_WITHOUT_DUPLICATING_LFS_LEDGER",
        "next_action": "Partitioned descendant commitments bind every transition ID; v3 transitions must be regenerated after semantic decisions.",
    })

    # Bind every tracked file in the complete prior Round 15/16/16A artifact
    # namespaces to its Git blob in the authorized source tree.  Row-level
    # semantic commitments below remain the stronger binding where practical;
    # every other file remains explicitly pending object-policy reconciliation.
    object_types_by_path: dict[str, list[str]] = defaultdict(list)
    for row in set_manifest_rows:
        object_types_by_path[row["source_path"]].append(row["prior_object_type"])
    prior_artifact_file_rows: list[dict[str, Any]] = []
    prior_artifact_paths: set[str] = set()
    for namespace_id, namespace_prefix in PRIOR_ARTIFACT_NAMESPACES:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "-l", SOURCE_SHA, "--", namespace_prefix],
            cwd=REPO,
            check=True,
            text=True,
            capture_output=True,
        )
        namespace_count = 0
        for line in result.stdout.splitlines():
            metadata, path = line.split("\t", 1)
            mode, object_type, object_sha, object_bytes = metadata.split()
            if object_type != "blob" or object_bytes == "-":
                raise ValueError(f"unexpected prior artifact object: {line}")
            if path in prior_artifact_paths:
                raise ValueError(f"prior artifact namespace overlap: {path}")
            prior_artifact_paths.add(path)
            namespace_count += 1
            covered_types = sorted(object_types_by_path.get(path, []))
            coverage_mode = (
                "ROW_EXACT_PLUS_FILE_BOUND"
                if covered_types
                else "FILE_BOUND_OBJECT_POLICY_RECONCILIATION_PENDING"
            )
            material = {
                "source_sha": SOURCE_SHA,
                "source_tree": SOURCE_TREE,
                "namespace_id": namespace_id,
                "namespace_prefix": namespace_prefix,
                "path": path,
                "git_mode": mode,
                "git_object_type": object_type,
                "git_blob_sha": object_sha,
                "git_blob_bytes": int(object_bytes),
                "object_set_coverage": covered_types,
                "coverage_mode": coverage_mode,
                "reconciliation_status": "PENDING",
            }
            prior_artifact_file_rows.append({
                "prior_artifact_file_id": stable_id("R16B-PRIOR-FILE", {"path": path}),
                "source_sha": SOURCE_SHA,
                "source_tree": SOURCE_TREE,
                "namespace_id": namespace_id,
                "namespace_prefix": namespace_prefix,
                "path": path,
                "git_mode": mode,
                "git_object_type": object_type,
                "git_blob_sha": object_sha,
                "git_blob_bytes": int(object_bytes),
                "object_set_coverage_json": canonical_json(covered_types),
                "coverage_mode": coverage_mode,
                "reconciliation_status": "PENDING",
                "required_next_action": "Preserve or explicitly supersede this source-tree artifact; where no row-level commitment exists, complete object-policy and semantic reconciliation before final closure.",
                "record_sha256": row_hash(material),
            })
        if namespace_count == 0:
            raise ValueError(f"empty prior artifact namespace: {namespace_prefix}")

    # Per-production descendant partitions prove that every state, transition,
    # workflow, and export remains attached to a specific v2 composition.  The
    # partitions are commitments only; they do not carry v2 semantics into v3.
    descendant_ids: dict[str, dict[str, list[str]]] = {
        composition_id: {"state": [], "workflow": [], "export": []}
        for composition_id in production_senses
    }
    state_to_production: dict[str, str] = {}
    for row in state_rows:
        descendant_ids[row["composition_id"]]["state"].append(row["state_id"])
        state_to_production[row["state_id"]] = row["composition_id"]
    for row in workflow_rows:
        descendant_ids[row["composition_id"]]["workflow"].append(row["workflow_id"])
    for row in export_rows:
        descendant_ids[row["composition_id"]]["export"].append(row["export_variant_id"])
    transition_counts: Counter[str] = Counter()
    transition_digests = {composition_id: hashlib.sha256() for composition_id in production_senses}
    with (REPO / R16A_TRANSITION_PATH).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, dialect="excel-tab"):
            composition_id = state_to_production[row["current_state_id"]]
            transition_counts[composition_id] += 1
            transition_digests[composition_id].update(row["transition_id"].encode("utf-8"))
            transition_digests[composition_id].update(b"\n")
    descendant_rows: list[dict[str, Any]] = []
    for composition_id in sorted(production_senses):
        arity = len(production_senses[composition_id])
        ids = descendant_ids[composition_id]
        expected_state_count = arity * (2 ** arity)
        if len(ids["state"]) != expected_state_count or len(ids["workflow"]) != expected_state_count or len(ids["export"]) != 2 * expected_state_count:
            raise ValueError(f"v2 descendant cardinality mismatch for {composition_id}")
        descendant_rows.append({
            "production_composition_id": composition_id,
            "participant_arity": arity,
            "round16b_candidate_ids_json": canonical_json([candidate_for_senses(production_senses[composition_id])] if candidate_for_senses(production_senses[composition_id]) else []),
            "state_count": len(ids["state"]),
            "state_id_set_sha256": id_set_hash(ids["state"]),
            "transition_count_by_current_state": transition_counts[composition_id],
            "transition_id_set_sha256": transition_digests[composition_id].hexdigest(),
            "workflow_count": len(ids["workflow"]),
            "workflow_id_set_sha256": id_set_hash(ids["workflow"]),
            "export_count": len(ids["export"]),
            "export_id_set_sha256": id_set_hash(ids["export"]),
            "partition_status": "COMPLETE_PENDING_ROUND16B_REGENERATION",
            "semantic_carry_forward_authorized": "false",
        })
    if sum(row["transition_count_by_current_state"] for row in descendant_rows) != transition_count:
        raise ValueError("transition descendant partitions do not cover the global transition set")

    # Bind every input, including the production read model omitted from the
    # method checkpoint's evidence-surface inventory.
    input_specs = [
        ("R16B-LOCAL-SURF-R16A-VOCABULARY", VOCAB_PATH, "json:candidates"),
        ("R16B-LOCAL-SURF-R09-CANDIDATES", R9_CANDIDATE_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R09-ATTESTATIONS", R9_ATTESTATION_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R09-GLOSSES", R9_GLOSS_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R10-ROLES", R10_ROLE_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R10-ATTESTATIONS", R10_ATTESTATION_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R10-CLUSTERS", R10_CLUSTER_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R10-CHAINS", R10_CHAIN_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R13-EVIDENCE", R13_EVIDENCE_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R13-GAP-DECISIONS", R13_GAP_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R14-ASSESSMENTS", R14_ASSESSMENT_PATH, "json:assessments"),
        ("R16B-LOCAL-SURF-R14-PROVENANCE", R14_PROVENANCE_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R14-NARY", R14_NARY_PATH, "json:fixtures"),
        ("R16B-LOCAL-SURF-R15-FIXTURES", R15_FIXTURE_PATH, "json:fixtures"),
        ("R16B-LOCAL-SURF-R15-DECISIONS", R15_DECISION_PATH, "json:images"),
        ("R16B-LOCAL-SURF-R15-RESULTS", R15_RESULT_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16-COMPOSITIONS", R16_COMPOSITION_PATH, "json:compositions"),
        ("R16B-LOCAL-SURF-R16-SOURCES", R16_SOURCE_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16-READ-MODEL", R16_READ_MODEL_PATH, "json:file"),
        ("R16B-LOCAL-SURF-R16A-PAIR-CENSUS", R16A_PAIR_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16A-GRAPH-NODES", R16A_GRAPH_PATH, "json:nodes"),
        ("R16B-LOCAL-SURF-R16A-GRAPH-EDGES", R16A_GRAPH_PATH, "json:edges"),
        ("R16B-LOCAL-SURF-R16A-SUBGRAPHS", R16A_REGISTRY_PATH, "json:association_subgraphs"),
        ("R16B-LOCAL-SURF-R16A-TOPOLOGIES", R16A_REGISTRY_PATH, "json:topology_compositions"),
        ("R16B-LOCAL-SURF-R16A-CATEGORIES", R16A_REGISTRY_PATH, "json:category_entries"),
        ("R16B-LOCAL-SURF-R16A-ADAPTERS", R16A_REGISTRY_PATH, "json:round15_adapter_records"),
        ("R16B-LOCAL-SURF-R16A-ENUMERATION", R16A_ENUMERATION_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16A-REJECTIONS", R16A_REJECTION_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16A-PRODUCTION", R16A_READ_MODEL_PATH, "json:compositions"),
        ("R16B-LOCAL-SURF-R16A-STATES", R16A_STATE_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16A-TRANSITIONS", R16A_TRANSITION_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16A-WORKFLOWS", R16A_WORKFLOW_PATH, "tsv_rows"),
        ("R16B-LOCAL-SURF-R16A-EXPORTS", R16A_EXPORT_PATH, "tsv_rows"),
        ("R16B-LOCAL-METHOD-SURFACE-INVENTORY", METHOD_SURFACE_INVENTORY_PATH, "tsv_rows"),
    ]
    input_manifest_rows = [{
        "input_id": f"R16B-LOCAL-INPUT-{index:03d}", "input_surface_id": surface_id,
        "path": path, "record_selector": selector,
        "record_count": input_manifest_record_count(path, selector),
        "bytes": (REPO / path).stat().st_size, "sha256": sha256_file(REPO / path),
        "use_boundary": "CANDIDATE_DISCOVERY_OR_PRIOR_RECONCILIATION_ONLY; NO SUPPORT DISPOSITION INHERITED",
    } for index, (surface_id, path, selector) in enumerate(input_specs, 1)]

    # Account for every method-checkpoint evidence surface, including surfaces
    # deferred from this finite local selector tranche.  A deferred surface is
    # an explicit closure blocker, never an implicit zero-emission exclusion.
    input_by_key = {
        (row["path"], row["record_selector"]): row
        for row in input_manifest_rows
    }
    occurrence_count_by_input = Counter(row["input_surface_id"] for row in occurrences)
    chain_rows = read_tsv(R10_CHAIN_PATH)
    if len(chain_rows) != 2 or any(
        len(row["ordered_labels"].split(">")) != 2
        or row["transitive_inference"] != "false"
        or row["active_grammar_selected"] != "false"
        for row in chain_rows
    ):
        raise ValueError("Round 10 observed-chain zero-higher-order-emission proof failed")
    chain_proof = canonical_json({
        "row_count": len(chain_rows),
        "chain_ids": sorted(row["chain_id"] for row in chain_rows),
        "ordered_labels": sorted(row["ordered_labels"] for row in chain_rows),
        "participant_count_each": [2 for _ in chain_rows],
        "transitive_inference_values": sorted(set(row["transitive_inference"] for row in chain_rows)),
        "active_grammar_selected_values": sorted(set(row["active_grammar_selected"] for row in chain_rows)),
        "higher_order_occurrence_count": 0,
    })
    method_surface_rows = read_tsv(METHOD_SURFACE_INVENTORY_PATH)
    surface_disposition_rows: list[dict[str, Any]] = []
    for surface in method_surface_rows:
        path = surface["path"]
        selector = surface["record_selector"]
        current_count = input_manifest_record_count(path, selector)
        current_bytes = (REPO / path).stat().st_size
        current_sha = sha256_file(REPO / path)
        if (
            current_count != int(surface["record_count"])
            or current_bytes != int(surface["bytes"])
            or current_sha != surface["sha256"]
        ):
            raise ValueError(f"method surface drift: {surface['surface_id']}")
        input_row = input_by_key.get((path, selector))
        if surface["surface_id"] == "SURF-R10-006":
            if not input_row or occurrence_count_by_input[input_row["input_surface_id"]] != 0:
                raise ValueError("observed-chain surface must be selected with zero higher-order emissions")
            disposition = "INSPECTED_ZERO_HIGHER_ORDER_EMISSION"
            zero_emission_proof = chain_proof
            next_action = "Retain as a bounded two-term chain control; do not infer transitivity, direction, pair activation, or a higher-order association."
        elif input_row:
            disposition = "SELECTED_EXECUTION_INPUT"
            zero_emission_proof = "NOT_APPLICABLE"
            next_action = "Carry the exact input and every emitted or reconciliation record into evidence and global-coherence review."
        elif surface["evidence_authority"] == "BIBLIOGRAPHIC_IDENTITY":
            disposition = "DEFERRED_SOURCE_RIGHTS_AND_EVIDENCE_REVIEW"
            zero_emission_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Review source identity, access, rights, locators, and bounded evidence before activating any trigger."
        elif surface["surface_id"] == "SURF-DB-001":
            disposition = "DEFERRED_TRG009_DATABASE_DISCOVERY"
            zero_emission_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Run governed database discovery; treat co-occurrence as a lead only and require scholarly follow-up."
        elif surface["evidence_authority"] == "PENDING_HUMAN_REVIEW":
            disposition = "DEFERRED_HUMAN_REVIEW_PENDING"
            zero_emission_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Keep affected claims inactive until independent human review is completed and recorded."
        elif surface["evidence_authority"] == "METADATA_DISCOVERY_ONLY":
            disposition = "DEFERRED_METADATA_QUERY_LOG_REVIEW"
            zero_emission_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Reconcile metadata-only results during adaptive source discovery; metadata cannot support an association."
        else:
            disposition = "DEFERRED_LOCAL_SELECTOR_REVIEW"
            zero_emission_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Implement and independently verify a bounded selector or a record-exact non-emission proof in a later tranche."
        occurrence_count = (
            occurrence_count_by_input[input_row["input_surface_id"]]
            if input_row
            else 0
        )
        material = {
            "surface_id": surface["surface_id"],
            "path": path,
            "record_selector": selector,
            "record_count": current_count,
            "bytes": current_bytes,
            "sha256": current_sha,
            "matched_input_id": input_row["input_id"] if input_row else "",
            "trigger_occurrence_count": occurrence_count,
            "disposition": disposition,
            "zero_emission_proof": zero_emission_proof,
        }
        surface_disposition_rows.append({
            "surface_id": surface["surface_id"],
            "round": surface["round"],
            "path": path,
            "record_selector": selector,
            "record_count": current_count,
            "bytes": current_bytes,
            "sha256": current_sha,
            "evidence_authority": surface["evidence_authority"],
            "candidate_trigger_ids": surface["candidate_trigger_ids"],
            "matched_input_ids_json": canonical_json([input_row["input_id"]] if input_row else []),
            "trigger_occurrence_count": occurrence_count,
            "disposition": disposition,
            "zero_emission_proof": zero_emission_proof,
            "candidate_universe_closure_effect": "OPEN" if disposition.startswith("DEFERRED_") else "ACCOUNTED_IN_CHECKPOINT003_LOCAL_TRANCHE",
            "required_next_action": next_action,
            "record_sha256": row_hash(material),
        })
    surface_disposition_counts = Counter(row["disposition"] for row in surface_disposition_rows)
    selected_method_surface_count = sum(not row["disposition"].startswith("DEFERRED_") for row in surface_disposition_rows)
    deferred_method_surface_count = sum(row["disposition"].startswith("DEFERRED_") for row in surface_disposition_rows)
    if len(surface_disposition_rows) != 44 or selected_method_surface_count != 23 or deferred_method_surface_count != 21:
        raise ValueError("method surface disposition coverage mismatch")

    occurrence_fields = [
        "trigger_occurrence_id", "trigger_id", "trigger_class", "input_surface_id", "source_path",
        "input_record_refs_json", "locator", "content_hashes_json", "raw_participant_labels_json",
        "raw_participant_sense_ids_json", "participant_sense_ids_json", "participant_set_key",
        "scope_hypothesis_id", "polarity", "emission_kind", "candidate_id",
        "incidental_or_excluded_labels_json", "notes", "selector_version", "occurrence_sha256",
    ]
    family_fields = [
        "candidate_id", "candidate_object_kind", "participant_set_key", "participant_sense_ids_json",
        "canonical_labels_json", "arity", "occurrence_count", "trigger_occurrence_ids_json",
        "trigger_ids_json", "emission_kinds_json", "active_participant_count",
        "research_only_participant_count", "rejected_participant_count", "order_semantics",
        "role_semantics", "scope_resolution_status", "case_resolution_status", "participant_eligibility",
        "lifecycle_state", "proposed_disposition", "evidence_review_status", "global_coherence_status",
        "product_eligibility", "association_identity_frozen", "family_content_sha256",
    ]
    open_role_fields = list(open_role_rows[0])
    isolated_fields = list(isolated_rows[0])
    prior_fields = list(prior_rows[0])
    set_manifest_fields = list(set_manifest_rows[0])
    prior_artifact_file_fields = list(prior_artifact_file_rows[0])
    descendant_fields = list(descendant_rows[0])
    input_manifest_fields = list(input_manifest_rows[0])
    surface_disposition_fields = list(surface_disposition_rows[0])

    prior_core_rows = [
        row for row in prior_rows
        if row["prior_object_type"] not in {
            "ROUND16A_STATE", "ROUND16A_STATE_HASH_INDEX", "ROUND16A_WORKFLOW", "ROUND16A_EXPORT"
        }
    ]
    prior_state_rows = [row for row in prior_rows if row["prior_object_type"] in {"ROUND16A_STATE", "ROUND16A_STATE_HASH_INDEX"}]
    prior_workflow_rows = [row for row in prior_rows if row["prior_object_type"] == "ROUND16A_WORKFLOW"]
    prior_export_rows = [row for row in prior_rows if row["prior_object_type"] == "ROUND16A_EXPORT"]
    outputs = {
        "concept-sense-crosswalk-v1.tsv": (crosswalk_fields, crosswalk_rows),
        "candidate-trigger-occurrence-ledger-v1.tsv": (occurrence_fields, sorted(occurrences, key=lambda row: row["trigger_occurrence_id"])),
        "local-candidate-family-ledger-v1.tsv": (family_fields, family_rows),
        "open-participant-resolution-ledger-v1.tsv": (open_role_fields, open_role_rows),
        "isolated-active-term-audit-ledger-v1.tsv": (isolated_fields, isolated_rows),
        "prior-object-reconciliation-universe-v1-core.tsv": (prior_fields, sorted(prior_core_rows, key=lambda row: (row["prior_object_type"], row["prior_id"]))),
        "prior-object-reconciliation-universe-v1-states.tsv": (prior_fields, sorted(prior_state_rows, key=lambda row: row["prior_id"])),
        "prior-object-reconciliation-universe-v1-workflows.tsv": (prior_fields, sorted(prior_workflow_rows, key=lambda row: row["prior_id"])),
        "prior-object-reconciliation-universe-v1-exports.tsv": (prior_fields, sorted(prior_export_rows, key=lambda row: row["prior_id"])),
        "prior-object-set-manifest-v1.tsv": (set_manifest_fields, set_manifest_rows),
        "prior-artifact-file-manifest-v1.tsv": (
            prior_artifact_file_fields,
            sorted(prior_artifact_file_rows, key=lambda row: row["path"]),
        ),
        "prior-production-descendant-manifest-v1.tsv": (descendant_fields, descendant_rows),
        "local-candidate-input-manifest-v1.tsv": (input_manifest_fields, input_manifest_rows),
        "local-surface-disposition-ledger-v1.tsv": (
            surface_disposition_fields,
            surface_disposition_rows,
        ),
    }
    for name, (fields, rows) in outputs.items():
        write_tsv(RAW / name, fields, rows)

    trigger_counts = Counter(row["trigger_class"] for row in occurrences)
    arity_distribution = Counter(str(row["arity"]) for row in candidate_objects)
    prior_counts = Counter(row["prior_object_type"] for row in prior_rows)
    census = {
        "format": "trace-round16b-local-candidate-census-v1",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": CHECKPOINT_002_SHA,
        "selector_version": SELECTOR_VERSION,
        "status": "PASS_WITH_OPEN_RESEARCH_BLOCKERS",
        "semantic_boundary": "These are participant-set review families emitted by the implemented local selectors, not a complete trigger universe, governed associations, evidence dispositions, or product-active facts.",
        "candidate_universe_status": "INITIAL_LOCAL_LOWER_BOUND_NOT_CLOSED",
        "crosswalk_record_count": len(crosswalk_rows),
        "crosswalk_disposition_distribution": dict(sorted(Counter(row["disposition"] for row in crosswalk_rows).items())),
        "trigger_occurrence_count": len(occurrences),
        "trigger_occurrence_distribution": dict(sorted(trigger_counts.items())),
        "local_candidate_family_count": len(candidate_objects),
        "candidate_arity_distribution": dict(sorted(arity_distribution.items(), key=lambda item: int(item[0]))),
        "control_only_candidate_family_count": sum(row["participant_eligibility"] == "CONTROL_ONLY_REJECTED_PARTICIPANT" for row in candidate_objects),
        "active_candidate_family_count": 0,
        "evidence_review_complete_candidate_count": 0,
        "global_coherence_pass_candidate_count": 0,
        "open_participant_resolution_queue_count": len(open_role_rows),
        "isolated_active_vocabulary_count": len(isolated_rows),
        "isolated_active_vocabulary_proven_composable_count": 0,
        "prior_row_exact_reconciliation_object_count": len(prior_rows),
        "prior_row_exact_reconciliation_distribution": dict(sorted(prior_counts.items())),
        "prior_transition_set_count": transition_count,
        "prior_transition_set_sha256": transition_id_hash,
        "prior_artifact_file_count": len(prior_artifact_file_rows),
        "prior_artifact_namespace_count": len(PRIOR_ARTIFACT_NAMESPACES),
        "input_surface_count": len(input_manifest_rows),
        "method_surface_count": len(surface_disposition_rows),
        "selected_method_surface_count": selected_method_surface_count,
        "deferred_method_surface_count": deferred_method_surface_count,
        "method_surface_disposition_distribution": dict(sorted(surface_disposition_counts.items())),
        "candidates": candidate_objects,
        "closure": {
            "PAIR_ASSOCIATION_CLOSURE": False,
            "HIGHER_ORDER_ASSOCIATION_CLOSURE": False,
            "GLOBAL_COMPOSITION_COHERENCE_CLOSURE": False,
            "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE": False,
            "COMPUTATIONAL_SPACE_CLOSURE": False,
            "FUNCTION3_CLOSURE": False,
        },
        "open_blockers": [
            "Candidate scopes and cases may split participant-set review families into multiple semantic association candidates.",
            "Twenty-one method-inventory surfaces are hash-accounted but remain explicitly deferred from executable selector review, so local trigger completeness is open.",
            "Local evidence, rights, negative evidence, and source-bundle synthesis have not yet received final dispositions.",
            "Database discovery and adaptive external scholarly searches have not yet been completed.",
            "Ten n-ary role templates lack closed governed participant sets.",
            "Five pair-isolated active terms lack final product-accessibility dispositions.",
            "Every prior composition and downstream v2 object remains pending global-coherence and v3 regeneration review.",
        ],
    }
    write_json(RAW / "local-candidate-census-v1.json", census)

    output_names = list(outputs) + ["local-candidate-census-v1.json"]
    receipt = {
        "format": "trace-round16b-local-candidate-build-receipt-v1",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": CHECKPOINT_002_SHA,
        "selector_version": SELECTOR_VERSION,
        "status": "PASS_WITH_OPEN_RESEARCH_BLOCKERS",
        "crosswalk_record_count": len(crosswalk_rows),
        "trigger_occurrence_count": len(occurrences),
        "local_candidate_family_count": len(candidate_objects),
        "open_participant_resolution_queue_count": len(open_role_rows),
        "isolated_active_vocabulary_count": len(isolated_rows),
        "prior_row_exact_reconciliation_object_count": len(prior_rows),
        "prior_transition_set_count": transition_count,
        "prior_artifact_file_count": len(prior_artifact_file_rows),
        "prior_artifact_namespace_count": len(PRIOR_ARTIFACT_NAMESPACES),
        "input_manifest_record_count": len(input_manifest_rows),
        "method_surface_count": len(surface_disposition_rows),
        "selected_method_surface_count": selected_method_surface_count,
        "deferred_method_surface_count": deferred_method_surface_count,
        "method_surface_disposition_distribution": dict(sorted(surface_disposition_counts.items())),
        "input_sha256": {row["path"]: row["sha256"] for row in input_manifest_rows},
        "output_sha256": {name: sha256_file(RAW / name) for name in output_names},
        "history_rewritten": False,
        "force_push_used": False,
        "closure_claimed": False,
    }
    write_json(RAW / "local-candidate-build-receipt.json", receipt)
    print(canonical_json(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
