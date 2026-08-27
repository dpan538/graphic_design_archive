#!/usr/bin/env python3
"""Build the frozen Round 16A vocabulary-candidate universe.

This script performs identity reconciliation only.  It deliberately does not
assign Round 16A vocabulary dispositions, infer vocabulary from the archive
database, or change any Round 8--16 artifact.  Every governed row listed below
is retained as provenance for the casefold-deduplicated candidate it
contributes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]

ROUND9_RAW = Path(
    "docs/research/trace-v49-design-history-relation-vocabulary-round1/"
    "04_RAW_CANDIDATE_TERM_REGISTRY.tsv"
)
ROUND9_ATTESTATIONS = Path(
    "docs/research/trace-v49-design-history-relation-vocabulary-round1/"
    "05_TERM_ATTESTATION_REGISTRY.tsv"
)
ROUND10_HANDOFF = Path(
    "docs/research/trace-v49-design-history-relation-grammar-round1/"
    "02_ROUND9_INPUT_TERM_REGISTRY.tsv"
)
ROUND10_DERIVATION = Path(
    "docs/research/trace-v49-design-history-relation-grammar-round1/"
    "04_NODE_DERIVATION_REGISTRY.tsv"
)
ROUND10_NODE_DECISIONS = Path(
    "docs/research/trace-v49-design-history-relation-grammar-round1/"
    "05_NODE_ROLE_DECISION_REGISTRY.tsv"
)
ROUND12_FREEZE = Path(
    "docs/research/trace-v49-exploration-inquiry-flow-round1/"
    "02_RESEARCH_CANDIDATE_FREEZE.json"
)
ROUND13_GAP_EVIDENCE = Path(
    "docs/research/trace-v49-exploration-composition-review-round1/"
    "06_VOCABULARY_GAP_EVIDENCE.tsv"
)
ROUND13_GAP_DECISIONS = Path(
    "docs/research/trace-v49-exploration-composition-review-round1/"
    "07_VOCABULARY_GAP_DECISIONS.tsv"
)
ROUND13_ACTIVATION = Path(
    "docs/research/trace-v49-exploration-composition-review-round1/"
    "14_ACTIVATION_CANDIDATE_PACKAGE.json"
)
ROUND14_ASSESSMENTS = Path(
    "scripts/trace-v49-exploration-association-calibration/fixtures/"
    "association-assessments-v1.json"
)
ROUND14_EVIDENCE = Path(
    "docs/audits/v49-exploration-association-calibration-round1/raw/"
    "evidence-provenance.tsv"
)
ROUND16_ADDITIONS = Path(
    "scripts/trace-v49-exploration-real-database/"
    "scholarly-source-additions-v1.tsv"
)
ROUND16_ACTIVE = Path(
    "docs/audits/v49-exploration-real-database-round1/raw/"
    "active-vocabulary-audit.tsv"
)
ROUND16_PROVENANCE = Path(
    "docs/audits/v49-exploration-real-database-round1/raw/"
    "vocabulary-provenance-audit.tsv"
)

INPUT_PATHS = (
    ROUND9_RAW,
    ROUND9_ATTESTATIONS,
    ROUND10_HANDOFF,
    ROUND10_DERIVATION,
    ROUND10_NODE_DECISIONS,
    ROUND12_FREEZE,
    ROUND13_GAP_EVIDENCE,
    ROUND13_GAP_DECISIONS,
    ROUND13_ACTIVATION,
    ROUND14_ASSESSMENTS,
    ROUND14_EVIDENCE,
    ROUND16_ADDITIONS,
    ROUND16_ACTIVE,
    ROUND16_PROVENANCE,
)
INPUT_ROLES = {
    ROUND9_RAW: ("ROUND9_RAW_CANDIDATE_REGISTRY", True),
    ROUND9_ATTESTATIONS: ("ROUND9_ATTESTATION_REFERENCE_REGISTRY", False),
    ROUND10_HANDOFF: ("ROUND10_HANDOFF_SENSE_REGISTRY", True),
    ROUND10_DERIVATION: ("ROUND10_NODE_DERIVATION_REGISTRY", True),
    ROUND10_NODE_DECISIONS: ("ROUND10_NODE_ROLE_DECISION_REGISTRY", True),
    ROUND12_FREEZE: ("ROUND12_FROZEN_CANDIDATE_PACKAGE", True),
    ROUND13_GAP_EVIDENCE: ("ROUND13_VOCABULARY_GAP_EVIDENCE", True),
    ROUND13_GAP_DECISIONS: ("ROUND13_VOCABULARY_GAP_DECISIONS", True),
    ROUND13_ACTIVATION: ("ROUND13_ACTIVATION_CANDIDATE_PACKAGE", True),
    ROUND14_ASSESSMENTS: ("ROUND14_ASSOCIATION_ENDPOINT_ASSESSMENTS", True),
    ROUND14_EVIDENCE: ("ROUND14_EVIDENCE_REFERENCE_REGISTRY", False),
    ROUND16_ADDITIONS: ("ROUND16_SCHOLARLY_ADDITIONS_SUPPORTED_TERMS", True),
    ROUND16_ACTIVE: ("ROUND16_ACTIVE_VOCABULARY_AUDIT", True),
    ROUND16_PROVENANCE: ("ROUND16_VOCABULARY_PROVENANCE_REFERENCE_AUDIT", False),
}

FORMAT = "trace-exploration-vocabulary-candidate-universe-v2"
VERSION = "2"
NORMALIZATION_POLICY = "UNICODE_NFKC_WHITESPACE_CASEFOLD_V1"
ID_PREFIX = "R16A-VOCAB-CAND"


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


def clean_exact_label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def normalize_label(value: Any) -> str:
    exact = clean_exact_label(value)
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", exact)).casefold().strip()


def split_semicolon(value: Any) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return []
    return [item for raw in value.split(";") if (item := clean_exact_label(raw))]


def split_json_or_semicolon(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean_exact_label(item) for item in value if clean_exact_label(item)]
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return split_semicolon(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected a JSON list, received: {value!r}")
    return [clean_exact_label(item) for item in parsed if clean_exact_label(item)]


def unique_sorted(values: Iterable[Any]) -> list[str]:
    cleaned = {clean_exact_label(value) for value in values}
    return sorted((value for value in cleaned if value), key=lambda value: (normalize_label(value), value))


def read_tsv(repo: Path, relative_path: Path) -> list[dict[str, str]]:
    path = repo / relative_path
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def read_json(repo: Path, relative_path: Path) -> Any:
    with (repo / relative_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_columns(path: Path, rows: list[dict[str, str]], columns: Iterable[str]) -> None:
    if not rows:
        raise ValueError(f"Required input is empty: {path}")
    missing = sorted(set(columns) - set(rows[0]))
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def truth_status(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return clean_exact_label(str(value))


def reference_values(row: dict[str, Any], fields: Iterable[str]) -> list[str]:
    values: list[str] = []
    for field in fields:
        value = row.get(field)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.extend(split_semicolon(value))
    return unique_sorted(values)


def make_contribution(
    *,
    source_path: Path,
    source_kind: str,
    source_index: int,
    source_pointer: str,
    label_field: str,
    canonical_label: str,
    exact_labels: Iterable[str],
    statuses: dict[str, Any],
    candidate_refs: Iterable[str] = (),
    governance_refs: Iterable[str] = (),
    attestation_refs: Iterable[str] = (),
    evidence_refs: Iterable[str] = (),
    scholarly_source_refs: Iterable[str] = (),
    reference_source_paths: Iterable[Path | str] = (),
    source_row: Any,
    canonical_priority: int,
) -> dict[str, Any]:
    canonical = clean_exact_label(canonical_label)
    if not canonical:
        raise ValueError(f"Empty candidate label at {source_path}:{source_pointer}")
    exact = unique_sorted([canonical, *exact_labels])
    return {
        "source_path": source_path.as_posix(),
        "source_format": source_path.suffix.removeprefix(".").upper(),
        "source_kind": source_kind,
        "source_index": source_index,
        "source_pointer": source_pointer,
        "label_field": label_field,
        "canonical_label": canonical,
        "normalized_label": normalize_label(canonical),
        "exact_labels": exact,
        "statuses": {
            key: truth_status(value)
            for key, value in sorted(statuses.items())
            if value is not None and truth_status(value) != ""
        },
        "candidate_refs": unique_sorted(candidate_refs),
        "governance_refs": unique_sorted(governance_refs),
        "attestation_refs": unique_sorted(attestation_refs),
        "evidence_refs": unique_sorted(evidence_refs),
        "scholarly_source_refs": unique_sorted(scholarly_source_refs),
        "reference_source_paths": sorted({
            path.as_posix() if isinstance(path, Path) else Path(path).as_posix()
            for path in reference_source_paths
        }),
        "source_row": source_row,
        "canonical_priority": canonical_priority,
    }


def round9_contributions(repo: Path) -> list[dict[str, Any]]:
    rows = read_tsv(repo, ROUND9_RAW)
    attestations = read_tsv(repo, ROUND9_ATTESTATIONS)
    require_columns(
        ROUND9_RAW,
        rows,
        ("candidate_id", "candidate_label", "final_decision", "discovery_source_id"),
    )
    require_columns(
        ROUND9_ATTESTATIONS,
        attestations,
        ("attestation_id", "candidate_id", "source_id"),
    )
    attestation_by_candidate: dict[str, list[str]] = {}
    source_by_candidate: dict[str, list[str]] = {}
    for row in attestations:
        candidate_id = row["candidate_id"]
        attestation_by_candidate.setdefault(candidate_id, []).append(row["attestation_id"])
        source_by_candidate.setdefault(candidate_id, []).append(row["source_id"])

    contributions = []
    for index, row in enumerate(rows, start=1):
        candidate_id = row["candidate_id"]
        exact_labels = [
            row.get("candidate_label", ""),
            row.get("original_language_label", ""),
            row.get("published_translation_label", ""),
        ]
        contributions.append(make_contribution(
            source_path=ROUND9_RAW,
            source_kind="ROUND9_RAW_CANDIDATE",
            source_index=index,
            source_pointer=f"row:{index + 1}",
            label_field="candidate_label",
            canonical_label=row["candidate_label"],
            exact_labels=exact_labels,
            statuses={
                "final_decision": row.get("final_decision"),
                "noun_attested": row.get("noun_attested"),
                "all_required_checks_complete": row.get("all_required_checks_complete"),
                "contestation_status": row.get("contestation_status"),
                "polysemy_status": row.get("polysemy_status"),
            },
            candidate_refs=[candidate_id],
            attestation_refs=attestation_by_candidate.get(candidate_id, []),
            scholarly_source_refs=[
                row.get("discovery_source_id", ""),
                *source_by_candidate.get(candidate_id, []),
            ],
            reference_source_paths=[ROUND9_ATTESTATIONS],
            source_row=row,
            canonical_priority=10,
        ))
    return contributions


def round10_contributions(repo: Path) -> list[dict[str, Any]]:
    specifications = (
        (
            ROUND10_HANDOFF,
            "ROUND10_HANDOFF_SENSE",
            20,
            (
                "round9_final_decision",
                "round9_grammar_selected",
                "exact_input_verified",
            ),
            ("round9_source_support_ids",),
            (),
        ),
        (
            ROUND10_DERIVATION,
            "ROUND10_NODE_DERIVATION",
            21,
            ("node_role_decision", "all_provenance_links_verified", "orphan"),
            ("round9_lexical_attestation_ids", "new_grammar_attestation_ids"),
            ("new_grammar_source_ids",),
        ),
        (
            ROUND10_NODE_DECISIONS,
            "ROUND10_NODE_ROLE_DECISION",
            22,
            (
                "final_node_role_decision",
                "pass_node",
                "ordinary_language_roles_complete",
                "natural_language_explanation_complete",
            ),
            (),
            ("new_grammar_source_ids",),
        ),
    )
    contributions: list[dict[str, Any]] = []
    for path, kind, priority, status_fields, attestation_fields, source_fields in specifications:
        rows = read_tsv(repo, path)
        require_columns(path, rows, ("candidate_id", "sense_id", "candidate_label"))
        for index, row in enumerate(rows, start=1):
            contributions.append(make_contribution(
                source_path=path,
                source_kind=kind,
                source_index=index,
                source_pointer=f"row:{index + 1}",
                label_field="candidate_label",
                canonical_label=row["candidate_label"],
                exact_labels=[row["candidate_label"]],
                statuses={field: row.get(field) for field in status_fields},
                candidate_refs=[row["candidate_id"], row["sense_id"]],
                attestation_refs=reference_values(row, attestation_fields),
                scholarly_source_refs=reference_values(row, source_fields),
                source_row=row,
                canonical_priority=priority,
            ))
    return contributions


def round12_contributions(repo: Path) -> list[dict[str, Any]]:
    document = read_json(repo, ROUND12_FREEZE)
    candidates = document.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(f"{ROUND12_FREEZE} has no candidates")
    contributions = []
    for index, row in enumerate(candidates, start=1):
        if not isinstance(row, dict) or not row.get("label"):
            raise ValueError(f"Invalid Round 12 candidate at index {index}")
        contributions.append(make_contribution(
            source_path=ROUND12_FREEZE,
            source_kind="ROUND12_FROZEN_RESEARCH_CANDIDATE",
            source_index=index,
            source_pointer=f"/candidates/{index - 1}",
            label_field="label",
            canonical_label=row["label"],
            exact_labels=[row["label"]],
            statuses={
                "researchStatus": row.get("researchStatus"),
                "round9Decision": row.get("round9Decision"),
                "round10NodeRoleDecision": row.get("round10NodeRoleDecision"),
                "active": row.get("active"),
            },
            candidate_refs=[
                row.get("candidateId", ""),
                row.get("senseId", ""),
            ],
            governance_refs=[
                *row.get("vocabularyGapIds", []),
                *row.get("pairQuestionIds", []),
                *row.get("clusterHandoffIds", []),
                *row.get("observedChainIds", []),
            ],
            attestation_refs=[
                *row.get("lexicalAttestationIds", []),
                *row.get("grammarAttestationIds", []),
            ],
            scholarly_source_refs=row.get("sourceIds", []),
            source_row=row,
            canonical_priority=30,
        ))
    return contributions


def round13_contributions(repo: Path) -> list[dict[str, Any]]:
    decisions = read_tsv(repo, ROUND13_GAP_DECISIONS)
    evidence = read_tsv(repo, ROUND13_GAP_EVIDENCE)
    activation = read_json(repo, ROUND13_ACTIVATION)
    require_columns(
        ROUND13_GAP_DECISIONS,
        decisions,
        ("gap_id", "final_decision", "candidate_ids", "attested_terms"),
    )
    require_columns(
        ROUND13_GAP_EVIDENCE,
        evidence,
        ("evidence_id", "candidate_sense_ids", "source_id", "exact_attested_terms"),
    )

    canonical_by_candidate: dict[str, str] = {}
    activation_sections = (
        ("nodeActivationCandidates", "ROUND13_NODE_ACTIVATION_CANDIDATE"),
        (
            "structuralAnnotationCandidates",
            "ROUND13_STRUCTURAL_ANNOTATION_CANDIDATE",
        ),
    )
    for section, _source_kind in activation_sections:
        items = activation.get(section, [])
        if not isinstance(items, list):
            raise ValueError(f"{ROUND13_ACTIVATION}:{section} must be an array")
        for item in items:
            if not isinstance(item, dict) or not item.get("candidateId") or not item.get("label"):
                raise ValueError(f"Invalid activation candidate in {section}")
            candidate_id = clean_exact_label(item["candidateId"])
            canonical_by_candidate[candidate_id] = clean_exact_label(item["label"])

    decision_candidate_forms: dict[int, list[tuple[str, str, list[str]]]] = {}
    for index, row in enumerate(decisions, start=1):
        candidate_ids = split_semicolon(row["candidate_ids"])
        exact_terms = split_semicolon(row["attested_terms"])
        if not candidate_ids:
            raise ValueError(f"No candidate IDs at {ROUND13_GAP_DECISIONS}:row:{index + 1}")
        if len(candidate_ids) == len(exact_terms):
            pairs = [
                (candidate_id, canonical_by_candidate.get(candidate_id, exact), [exact])
                for candidate_id, exact in zip(candidate_ids, exact_terms, strict=True)
            ]
        elif len(candidate_ids) == 1 and exact_terms:
            candidate_id = candidate_ids[0]
            pairs = [(
                candidate_id,
                canonical_by_candidate.get(candidate_id, exact_terms[0]),
                exact_terms,
            )]
        else:
            unresolved = [item for item in candidate_ids if item not in canonical_by_candidate]
            if unresolved:
                raise ValueError(
                    f"Ambiguous candidate/term mapping at {ROUND13_GAP_DECISIONS}:row:{index + 1}: "
                    f"{unresolved}"
                )
            pairs = [
                (candidate_id, canonical_by_candidate[candidate_id], exact_terms)
                for candidate_id in candidate_ids
            ]
        decision_candidate_forms[index] = pairs
        for candidate_id, canonical, exacts in pairs:
            canonical_by_candidate.setdefault(candidate_id, canonical)

    contributions: list[dict[str, Any]] = []
    for section_index, (section, source_kind) in enumerate(
        activation_sections, start=1
    ):
        for index, row in enumerate(activation.get(section, []), start=1):
            candidate_id = clean_exact_label(row["candidateId"])
            contributions.append(make_contribution(
                source_path=ROUND13_ACTIVATION,
                source_kind=source_kind,
                source_index=(section_index * 10_000) + index,
                source_pointer=f"/{section}/{index - 1}",
                label_field="label",
                canonical_label=row["label"],
                exact_labels=[row["label"]],
                statuses={
                    "active": row.get("active"),
                    "representation": row.get("representation"),
                    "universalNode": row.get("universalNode"),
                    "edge": row.get("edge"),
                },
                candidate_refs=[candidate_id],
                governance_refs=[row.get("gapId", "")],
                source_row=row,
                canonical_priority=40,
            ))

    for index, row in enumerate(decisions, start=1):
        for candidate_id, canonical, exacts in decision_candidate_forms[index]:
            contributions.append(make_contribution(
                source_path=ROUND13_GAP_DECISIONS,
                source_kind="ROUND13_VOCABULARY_GAP_DECISION",
                source_index=index,
                source_pointer=f"row:{index + 1}:{candidate_id}",
                label_field="attested_terms",
                canonical_label=canonical,
                exact_labels=exacts,
                statuses={
                    "final_decision": row.get("final_decision"),
                    "verified": row.get("verified"),
                },
                candidate_refs=[candidate_id],
                governance_refs=[row.get("gap_id", "")],
                source_row=row,
                canonical_priority=41,
            ))

    for index, row in enumerate(evidence, start=1):
        candidate_ids = split_semicolon(row["candidate_sense_ids"])
        exact_terms = split_semicolon(row["exact_attested_terms"])
        if not candidate_ids:
            raise ValueError(f"No candidate IDs at {ROUND13_GAP_EVIDENCE}:row:{index + 1}")
        for candidate_position, candidate_id in enumerate(candidate_ids):
            canonical = canonical_by_candidate.get(candidate_id)
            if canonical is None:
                if len(candidate_ids) == len(exact_terms):
                    canonical = exact_terms[candidate_position]
                elif exact_terms:
                    canonical = exact_terms[0]
                else:
                    raise ValueError(
                        f"No canonical label at {ROUND13_GAP_EVIDENCE}:row:{index + 1}"
                    )
                canonical_by_candidate[candidate_id] = canonical
            if len(candidate_ids) == 1:
                contribution_exacts = exact_terms
            elif len(candidate_ids) == len(exact_terms):
                contribution_exacts = [exact_terms[candidate_position]]
            else:
                contribution_exacts = exact_terms
            contributions.append(make_contribution(
                source_path=ROUND13_GAP_EVIDENCE,
                source_kind="ROUND13_VOCABULARY_GAP_EVIDENCE",
                source_index=index,
                source_pointer=f"row:{index + 1}:{candidate_id}",
                label_field="exact_attested_terms",
                canonical_label=canonical,
                exact_labels=contribution_exacts,
                statuses={
                    "peer_reviewed": row.get("peer_reviewed"),
                    "design_history_usage": row.get("design_history_usage"),
                    "source_metadata_verified": row.get("source_metadata_verified"),
                    "evidence_verified": row.get("evidence_verified"),
                    "semantic_review": row.get("semantic_review"),
                    "adversarial_review": row.get("adversarial_review"),
                },
                candidate_refs=[candidate_id],
                governance_refs=[row.get("pair_or_gap_id", "")],
                evidence_refs=[row["evidence_id"]],
                scholarly_source_refs=[row["source_id"]],
                source_row=row,
                canonical_priority=42,
            ))
    return contributions


def round14_contributions(repo: Path) -> list[dict[str, Any]]:
    document = read_json(repo, ROUND14_ASSESSMENTS)
    assessments = document.get("assessments")
    if not isinstance(assessments, list) or not assessments:
        raise ValueError(f"{ROUND14_ASSESSMENTS} has no assessments")
    evidence_rows = read_tsv(repo, ROUND14_EVIDENCE)
    require_columns(
        ROUND14_EVIDENCE,
        evidence_rows,
        ("assessment_id", "evidence_id", "source_id"),
    )
    evidence_by_assessment: dict[str, list[str]] = {}
    sources_by_assessment: dict[str, list[str]] = {}
    for row in evidence_rows:
        assessment_id = row["assessment_id"]
        evidence_by_assessment.setdefault(assessment_id, []).append(row["evidence_id"])
        sources_by_assessment.setdefault(assessment_id, []).append(row["source_id"])

    contributions = []
    for index, row in enumerate(assessments, start=1):
        assessment_id = clean_exact_label(row.get("assessmentId", ""))
        if not assessment_id or not row.get("nodeA") or not row.get("nodeB"):
            raise ValueError(f"Invalid Round 14 assessment at index {index}")
        source_refs = [
            *row.get("externalSourceRefs", []),
            *row.get("archiveSourceRefs", []),
            *sources_by_assessment.get(assessment_id, []),
        ]
        statuses = {
            "activeForProximity": row.get("activeForProximity"),
            "directNeighbourPass": row.get("directNeighbourPass"),
            "skipOnePass": row.get("skipOnePass"),
            "associationStrength": row.get("associationStrength"),
            "evidenceConfidence": row.get("evidenceConfidence"),
            "evidenceStatus": row.get("evidenceStatus"),
            "calibrationStratum": row.get("calibrationStratum"),
            "hardNegative": row.get("hardNegative"),
            "cooccurrenceOnly": row.get("cooccurrenceOnly"),
        }
        for endpoint in ("nodeA", "nodeB"):
            contributions.append(make_contribution(
                source_path=ROUND14_ASSESSMENTS,
                source_kind="ROUND14_ASSOCIATION_ENDPOINT",
                source_index=index,
                source_pointer=f"/assessments/{index - 1}/{endpoint}",
                label_field=endpoint,
                canonical_label=row[endpoint],
                exact_labels=[row[endpoint]],
                statuses=statuses,
                governance_refs=[assessment_id],
                evidence_refs=evidence_by_assessment.get(assessment_id, []),
                scholarly_source_refs=source_refs,
                reference_source_paths=[ROUND14_EVIDENCE],
                source_row=row,
                canonical_priority=50,
            ))
    return contributions


def round16_contributions(repo: Path) -> list[dict[str, Any]]:
    additions = read_tsv(repo, ROUND16_ADDITIONS)
    active = read_tsv(repo, ROUND16_ACTIVE)
    provenance = read_tsv(repo, ROUND16_PROVENANCE)
    require_columns(
        ROUND16_ADDITIONS,
        additions,
        ("source_id", "supported_terms", "metadata_verified"),
    )
    require_columns(
        ROUND16_ACTIVE,
        active,
        ("vocabulary_id", "canonical_label", "activation_status", "status"),
    )
    require_columns(
        ROUND16_PROVENANCE,
        provenance,
        ("vocabulary_id", "canonical_label", "attestation_refs", "academic_support_refs"),
    )
    provenance_by_id: dict[str, dict[str, str]] = {}
    for row in provenance:
        vocabulary_id = row["vocabulary_id"]
        if not vocabulary_id:
            raise ValueError(f"Blank vocabulary_id in {ROUND16_PROVENANCE}")
        if vocabulary_id in provenance_by_id:
            raise ValueError(
                f"Duplicate vocabulary_id in {ROUND16_PROVENANCE}: {vocabulary_id}"
            )
        provenance_by_id[vocabulary_id] = row
    contributions: list[dict[str, Any]] = []
    for index, row in enumerate(additions, start=1):
        terms = split_semicolon(row["supported_terms"])
        if not terms:
            raise ValueError(f"No supported terms at {ROUND16_ADDITIONS}:row:{index + 1}")
        for term_position, term in enumerate(terms, start=1):
            contributions.append(make_contribution(
                source_path=ROUND16_ADDITIONS,
                source_kind="ROUND16_SCHOLARLY_ADDITION_SUPPORTED_TERM",
                source_index=index,
                source_pointer=f"row:{index + 1}:supported_terms:{term_position}",
                label_field="supported_terms",
                canonical_label=term,
                exact_labels=[term],
                statuses={
                    "peer_reviewed": row.get("peer_reviewed"),
                    "design_history_usage": row.get("design_history_usage"),
                    "metadata_verified": row.get("metadata_verified"),
                },
                scholarly_source_refs=[row["source_id"]],
                source_row=row,
                canonical_priority=60,
            ))
    active_ids: set[str] = set()
    for index, row in enumerate(active, start=1):
        vocabulary_id = row["vocabulary_id"]
        if vocabulary_id in active_ids:
            raise ValueError(f"Duplicate vocabulary_id in {ROUND16_ACTIVE}: {vocabulary_id}")
        active_ids.add(vocabulary_id)
        provenance_row = provenance_by_id.get(row["vocabulary_id"])
        if provenance_row is None:
            raise ValueError(f"Missing Round 16 provenance for {row['vocabulary_id']}")
        if normalize_label(provenance_row["canonical_label"]) != normalize_label(
            row["canonical_label"]
        ):
            raise ValueError(
                "Round 16 canonical-label mismatch for "
                f"{row['vocabulary_id']}: active={row['canonical_label']!r}, "
                f"provenance={provenance_row['canonical_label']!r}"
            )
        contributions.append(make_contribution(
            source_path=ROUND16_ACTIVE,
            source_kind="ROUND16_ACTIVE_VOCABULARY_BASELINE",
            source_index=index,
            source_pointer=f"row:{index + 1}",
            label_field="canonical_label",
            canonical_label=row["canonical_label"],
            exact_labels=[row.get("attested_form", ""), row["canonical_label"]],
            statuses={
                "activation_status": row.get("activation_status"),
                "audit_status": row.get("status"),
                "provenance_chain_complete": provenance_row.get("provenance_chain_complete"),
            },
            candidate_refs=[row["vocabulary_id"]],
            attestation_refs=split_json_or_semicolon(provenance_row["attestation_refs"]),
            scholarly_source_refs=split_json_or_semicolon(
                provenance_row["academic_support_refs"]
            ),
            reference_source_paths=[ROUND16_PROVENANCE],
            source_row={
                "active_vocabulary_audit": row,
                "vocabulary_provenance_audit": provenance_row,
            },
            canonical_priority=70,
        ))
    return contributions


def aggregate_candidates(contributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for contribution in contributions:
        normalized = contribution["normalized_label"]
        if not normalized:
            raise ValueError(f"Empty normalized label in {contribution['source_pointer']}")
        grouped.setdefault(normalized, []).append(contribution)

    candidates: list[dict[str, Any]] = []
    for normalized_label, rows in sorted(grouped.items()):
        rows.sort(key=lambda item: (
            item["canonical_priority"],
            item["source_path"],
            item["source_index"],
            item["source_pointer"],
            item["label_field"],
        ))
        canonical_label = rows[0]["canonical_label"]
        digest = hashlib.sha256(normalized_label.encode("utf-8")).hexdigest()
        source_row_keys = {
            (row["source_path"], row["source_index"])
            for row in rows
        }
        statuses = {
            f"{row['source_kind']}:{key}={value}"
            for row in rows
            for key, value in row["statuses"].items()
        }
        candidate = {
            "vocabulary_candidate_id": f"{ID_PREFIX}:{digest}",
            "canonical_label": canonical_label,
            "normalized_label": normalized_label,
            "exact_labels": unique_sorted(
                exact for row in rows for exact in row["exact_labels"]
            ),
            "contributing_source_paths": sorted({row["source_path"] for row in rows}),
            "contributing_source_kinds": sorted({row["source_kind"] for row in rows}),
            "source_statuses": sorted(statuses),
            "candidate_refs": unique_sorted(
                ref for row in rows for ref in row["candidate_refs"]
            ),
            "governance_refs": unique_sorted(
                ref for row in rows for ref in row["governance_refs"]
            ),
            "attestation_refs": unique_sorted(
                ref for row in rows for ref in row["attestation_refs"]
            ),
            "evidence_refs": unique_sorted(
                ref for row in rows for ref in row["evidence_refs"]
            ),
            "scholarly_source_refs": unique_sorted(
                ref for row in rows for ref in row["scholarly_source_refs"]
            ),
            "reference_source_paths": sorted({
                path
                for row in rows
                for path in row["reference_source_paths"]
            }),
            "contributing_source_row_count": len(source_row_keys),
            "source_contribution_count": len(rows),
            "contributing_sources": [
                {key: value for key, value in row.items() if key != "canonical_priority"}
                for row in rows
            ],
        }
        candidates.append(candidate)
    return candidates


def build_universe(repo: Path) -> dict[str, Any]:
    missing = [path.as_posix() for path in INPUT_PATHS if not (repo / path).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing governed input(s): {', '.join(missing)}")

    contributions = [
        *round9_contributions(repo),
        *round10_contributions(repo),
        *round12_contributions(repo),
        *round13_contributions(repo),
        *round14_contributions(repo),
        *round16_contributions(repo),
    ]
    candidates = aggregate_candidates(contributions)
    source_inputs = [
        {
            "path": path.as_posix(),
            "format": path.suffix.removeprefix(".").upper(),
            "role": INPUT_ROLES[path][0],
            "contributes_candidate_labels": INPUT_ROLES[path][1],
            "sha256": sha256_file(repo / path),
            "bytes": (repo / path).stat().st_size,
        }
        for path in INPUT_PATHS
    ]
    canonical_material = {
        "format": FORMAT,
        "version": VERSION,
        "frozen": True,
        "round16a_dispositions_assigned": False,
        "normalization_policy": NORMALIZATION_POLICY,
        "deduplication_policy": "EXACT_NORMALIZED_LABEL_MATCH_V1",
        "canonical_label_selection_policy": (
            "LOWEST_SOURCE_PRIORITY_THEN_PATH_ROW_POINTER_FIELD_V1"
        ),
        "candidate_id_policy": f"{ID_PREFIX}:sha256(normalized_label)",
        "universe_canonical_hash_policy": (
            "SHA256_UTF8_SORTED_KEY_COMPACT_JSON_PLUS_LF_EXCLUDING_SELF_V1"
        ),
        "source_inputs": source_inputs,
        "source_input_count": len(source_inputs),
        "contributing_source_row_count": len({
            (row["source_path"], row["source_index"])
            for row in contributions
        }),
        "source_contribution_count": len(contributions),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    return {
        **canonical_material,
        "universe_canonical_hash": canonical_hash(canonical_material),
    }


def json_bytes(universe: dict[str, Any]) -> bytes:
    return (json.dumps(universe, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def tsv_bytes(universe: dict[str, Any]) -> bytes:
    fieldnames = [
        "vocabulary_candidate_id",
        "canonical_label",
        "normalized_label",
        "exact_labels_json",
        "contributing_source_path_count",
        "contributing_source_row_count",
        "source_contribution_count",
        "contributing_source_paths_json",
        "contributing_source_kinds_json",
        "source_statuses_json",
        "candidate_refs_json",
        "governance_refs_json",
        "attestation_refs_json",
        "evidence_refs_json",
        "scholarly_source_refs_json",
        "reference_source_paths_json",
        "contributing_sources_json",
        "universe_canonical_hash",
    ]
    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for candidate in universe["candidates"]:
        writer.writerow({
            "vocabulary_candidate_id": candidate["vocabulary_candidate_id"],
            "canonical_label": candidate["canonical_label"],
            "normalized_label": candidate["normalized_label"],
            "exact_labels_json": canonical_json(candidate["exact_labels"]),
            "contributing_source_path_count": len(candidate["contributing_source_paths"]),
            "contributing_source_row_count": candidate["contributing_source_row_count"],
            "source_contribution_count": candidate["source_contribution_count"],
            "contributing_source_paths_json": canonical_json(
                candidate["contributing_source_paths"]
            ),
            "contributing_source_kinds_json": canonical_json(
                candidate["contributing_source_kinds"]
            ),
            "source_statuses_json": canonical_json(candidate["source_statuses"]),
            "candidate_refs_json": canonical_json(candidate["candidate_refs"]),
            "governance_refs_json": canonical_json(candidate["governance_refs"]),
            "attestation_refs_json": canonical_json(candidate["attestation_refs"]),
            "evidence_refs_json": canonical_json(candidate["evidence_refs"]),
            "scholarly_source_refs_json": canonical_json(
                candidate["scholarly_source_refs"]
            ),
            "reference_source_paths_json": canonical_json(
                candidate["reference_source_paths"]
            ),
            "contributing_sources_json": canonical_json(candidate["contributing_sources"]),
            "universe_canonical_hash": universe["universe_canonical_hash"],
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare deterministic bytes with existing outputs without writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else repo / "docs/audits/v49-exploration-full-space-closure-round1/raw"
    )
    universe = build_universe(repo)
    outputs = {
        output_dir / "vocabulary-candidate-universe-v2.json": json_bytes(universe),
        output_dir / "vocabulary-candidate-universe-v2.tsv": tsv_bytes(universe),
    }
    if args.check:
        mismatches = [
            str(path)
            for path, expected in outputs.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        if mismatches:
            raise SystemExit("Deterministic output mismatch: " + ", ".join(mismatches))
    else:
        for path, content in outputs.items():
            atomic_write(path, content)
    def display_path(path: Path) -> str:
        try:
            return str(path.relative_to(repo))
        except ValueError:
            return str(path)

    print(canonical_json({
        "status": "PASS" if args.check else "GENERATED",
        "candidate_count": universe["candidate_count"],
        "contributing_source_row_count": universe["contributing_source_row_count"],
        "source_contribution_count": universe["source_contribution_count"],
        "source_input_count": universe["source_input_count"],
        "universe_canonical_hash": universe["universe_canonical_hash"],
        "round16a_dispositions_assigned": False,
        "outputs": [display_path(path) for path in outputs],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
