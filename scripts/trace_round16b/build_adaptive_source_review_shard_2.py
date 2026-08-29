#!/usr/bin/env python3
"""Build Round 16B adaptive source-review shard 2 and source-scope corrections.

This deterministic builder records two bounded higher-order source hypotheses
and one additive correction to inherited evidence.  It retains bibliographic
identity, stable locators, rights decisions, bounded paraphrases, and review
decisions only.  It does not retain publisher PDFs or copyrighted full text,
activate an association, project a hyperedge into pair edges, create a product
path, or assert closure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RESEARCH_REL = Path("docs/research/trace-v49-exploration-higher-order-association-closure-round16b")

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORITY_BASE_SHA = "5d9ebf6918cf0fd09450608289ebc5a05ed3c8c3"
SHARD_ID = "R16B-ADAPTIVE-SOURCE-SHARD-002"
BUILDER_VERSION = "trace-round16b-adaptive-source-review-shard-2-v1"
RETRIEVED_AT_UTC = "2026-08-28T11:08:18Z"
REVIEWER = "CODEX_ROUND16B_ROOT_RESEARCH_REVIEW"

VOCAB_SOURCE = "docs/research/trace-v49-design-history-relation-vocabulary-round1/03_SCHOLARLY_SOURCE_REGISTRY.tsv"
VOCAB_ATTESTATION = "docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv"
COMPOSITION_SOURCE = "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv"
COMPOSITION_EVIDENCE = "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv"
CROSSWALK = str(RAW_REL / "concept-sense-crosswalk-v1.tsv")
ISOLATED_TERMS = str(RAW_REL / "isolated-active-term-audit-ledger-v1.tsv")
SOURCE_RIGHTS_QUEUE = str(RAW_REL / "source-canonical-rights-queue-v2.tsv")
SHARD1_REVIEW = str(RAW_REL / "adaptive-source-review-shard-1-v1.tsv")
RIGHTS_POLICY = str(RAW_REL / "scholarly-source-rights-policy.json")
LOCAL_FAMILIES = str(RAW_REL / "local-candidate-family-ledger-v2.tsv")
CANDIDATE_TRIGGER_REGISTRY = str(RAW_REL / "candidate-trigger-registry.tsv")

PINNED_INPUT_SHA256 = {
    VOCAB_SOURCE: "8aae0e6d73f30061cc09a3bc7d72c4eb10aea1ca92513a5d0bc16bf29aa4943f",
    VOCAB_ATTESTATION: "f2f8ff68c9263ee360aa84f73bc3adb55e5b18b41f86f03faa18522645193240",
    COMPOSITION_SOURCE: "1f54c0956ca12dfaad472a6644c6102ee13b2e9a46f6c1794e21e1a2d7097dca",
    COMPOSITION_EVIDENCE: "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    CROSSWALK: "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    ISOLATED_TERMS: "67eaf0d1a519163d6c6d54a1c728e9f3fdc502c6bac93b1b59b7593a384803d2",
    SOURCE_RIGHTS_QUEUE: "fd8e8b48b1d0f8da1e4194828d0cc6f273fadb4ecbe147a7f5f9e2319f08b960",
    SHARD1_REVIEW: "0ed85ac002eb27b6130639acb4ecb2c3ebc9fbe0224f67550dc853f098324ecb",
    RIGHTS_POLICY: "b68037dff860421a4f413767a38ca07998cc9f215c75780f1e0019f32bf396ba",
    LOCAL_FAMILIES: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    CANDIDATE_TRIGGER_REGISTRY: "b2c1710f09d8bc6dd7a629b186bbcf10a6e1f1a6ccf10adc3a67a5c7eec8eef1",
}

QUERY_PATH = str(RAW_REL / "adaptive-search-query-log-shard-2-v1.tsv")
REVIEW_PATH = str(RAW_REL / "adaptive-source-review-shard-2-v1.tsv")
RIGHTS_PATH = str(RAW_REL / "source-rights-ledger-shard-2-v2.tsv")
HYPOTHESIS_PATH = str(RAW_REL / "scoped-association-hypothesis-ledger-shard-2-v1.tsv")
CORRECTION_PATH = str(RAW_REL / "source-scope-reconciliation-ledger-shard-2-v1.tsv")
TRIGGER_PATH = str(RAW_REL / "external-candidate-trigger-occurrence-ledger-shard-2-v1.tsv")
TRIGGER_MATRIX_PATH = str(RAW_REL / "external-candidate-trigger-applicability-matrix-shard-2-v1.tsv")
FAMILY_PATH = str(RAW_REL / "external-candidate-family-ledger-shard-2-v1.tsv")
VOCAB_IMPACT_PATH = str(RAW_REL / "active-vocabulary-evidence-impact-ledger-shard-2-v1.tsv")
GAP_PATH = str(RAW_REL / "recursive-gap-ledger-adaptive-source-shard-2-v1.tsv")
CENSUS_PATH = str(RAW_REL / "adaptive-source-review-census-shard-2-v1.json")
MANIFEST_PATH = str(RAW_REL / "adaptive-source-review-output-manifest-shard-2-v1.tsv")
REPORT_PATH = str(RESEARCH_REL / "17_ADAPTIVE_SOURCE_REVIEW_SHARD_002_AND_SOURCE_SCOPE_RECONCILIATION.md")
RECEIPT_PATH = str(RAW_REL / "adaptive-source-review-build-receipt-shard-2-v1.json")

SENSES = {
    "canonization": "R16B-SENSE:94c4f5d3fe61b3ac4c6a1540f918207e423a9abe9823bb4ddb0466ce033cda4d",
    "gendering": "R16B-SENSE:14bd96e324918cf3d87ed84253055004be79647294bf62a305ccf9a65a46b863",
    "exclusion": "R16B-SENSE:51949ccda89c423bfca99e114d57880bdab2a25181a617884774e748bd18ae89",
    "mobile object": "R16B-SENSE:74959afea7f94773eca66c42bbaabe55d3f5ac814d8b2f8efd05921e7e76aa78",
    "mediation": "R16B-SENSE:35489187871bfd7b7be6e2d5268a3a922984d3bdad9e9a8ca61ea6edee84a5a7",
    "commodification": "R16B-SENSE:f1dafc6df9c9a66b0b7c19d34606a2ed638c193dc7047afb8a1f83b3d564ebc1",
    "cultural transformation": "R16B-SENSE:1e7045ac788667d54d6b65cd2d78f8c378eb10d531dd198692143840ff9d766b",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(relative: str) -> str:
    return sha256_bytes((REPO / relative).read_bytes())


def stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json(value).encode('utf-8'))}"


def j(value: Any) -> str:
    return canonical_json(value)


def finalized(row: dict[str, Any]) -> dict[str, str]:
    scalar = {key: ("" if value is None else str(value)) for key, value in row.items()}
    scalar["record_sha256"] = sha256_bytes(canonical_json(scalar).encode("utf-8"))
    return scalar


def tsv_bytes(fieldnames: list[str], rows: Iterable[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def exact_row(relative: str, key: str, value: str) -> dict[str, str]:
    rows = [row for row in read_tsv(relative) if row.get(key) == value]
    if len(rows) != 1:
        raise ValueError(f"expected one {relative}:{key}={value}; found {len(rows)}")
    return rows[0]


def validate_inputs() -> None:
    failures = []
    for path, expected in sorted(PINNED_INPUT_SHA256.items()):
        actual = sha256_file(path)
        if actual != expected:
            failures.append(f"PIN_MISMATCH:{path}:{actual}")
    expected_sources = {
        (VOCAB_SOURCE, "source_id", "SRC-0007"): ("Dori Griffin", "2016", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History"),
        (COMPOSITION_SOURCE, "source_id", "COMP-SRC-022"): ("Rebecca Earle;Susan Deans-Smith", "2026", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea"),
        (COMPOSITION_SOURCE, "source_id", "COMP-SRC-017"): ("Hifsiye Pulhan;İbrahim Numan", "2006", "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation"),
    }
    for (path, key, value), wanted in expected_sources.items():
        row = exact_row(path, key, value)
        actual = (row.get("authors", ""), row.get("year", ""), row.get("title", ""))
        if actual != wanted:
            failures.append(f"SOURCE_DRIFT:{value}:{actual}")
    evidence = exact_row(COMPOSITION_EVIDENCE, "evidence_id", "COMP-EVID-018")
    if evidence.get("exact_attested_terms") != "cultural transformation" or evidence.get("source_id") != "COMP-SRC-017":
        failures.append("COMP_EVID_018_IDENTITY_DRIFT")
    crosswalk = {row["canonical_label"]: row for row in read_tsv(CROSSWALK)}
    for label, sense_id in SENSES.items():
        if crosswalk.get(label, {}).get("participant_sense_id") != sense_id:
            failures.append(f"SENSE_DRIFT:{label}")
    local_sets = {
        tuple(sorted(json.loads(row["canonical_labels_json"])))
        for row in read_tsv(LOCAL_FAMILIES)
    }
    for candidate in (
        tuple(sorted(["canonization", "gendering", "exclusion"])),
        tuple(sorted(["mobile object", "mediation", "commodification"])),
    ):
        if candidate in local_sets:
            failures.append(f"EXTERNAL_CANDIDATE_ALREADY_LOCAL:{candidate}")
    trigger_registry = read_tsv(CANDIDATE_TRIGGER_REGISTRY)
    expected_trigger_names = {
        "TRG-002": "SAME_LOCATOR_MULTI_CONCEPT",
        "TRG-005": "ISOLATED_ACTIVE_VOCABULARY",
        "TRG-006": "RESEARCH_ONLY_BOUNDED_SENSE",
        "TRG-010": "ADAPTIVE_EXTERNAL_SEARCH",
        "TRG-011": "COUNTEREVIDENCE_AND_FALSIFICATION",
    }
    trigger_names = {row["trigger_id"]: row["trigger_name"] for row in trigger_registry}
    if len(trigger_names) != 12:
        failures.append(f"TRIGGER_REGISTRY_COUNT:{len(trigger_names)}")
    for trigger_id, trigger_name in expected_trigger_names.items():
        if trigger_names.get(trigger_id) != trigger_name:
            failures.append(f"TRIGGER_REGISTRY_DRIFT:{trigger_id}")
    if failures:
        raise ValueError(";".join(failures))


def association_identity(labels: list[str], scope_key: str) -> tuple[str, str]:
    participant_sense_ids = sorted(SENSES[label] for label in labels)
    association_id = stable_id("R16B-ASSOC", {
        "association_class": "HIGHER_ORDER",
        "participant_sense_ids": participant_sense_ids,
        "order_semantics": "UNORDERED",
        "role_semantics": "NONE_UNTIL_EXTERNAL_REVIEW",
        "scope_key": scope_key,
    })
    revision_id = stable_id("R16B-ASSOC-REV", {
        "association_id": association_id,
        "activation_status": "INQUIRY_ONLY",
        "final_disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "pair_projection_policy": "NONE",
        "parent_checkpoint_sha": AUTHORITY_BASE_SHA,
        "product_eligibility": "INELIGIBLE",
        "review_tranche": "CHECKPOINT-009-ADAPTIVE-SOURCE-SHARD-002",
    })
    return association_id, revision_id


def build_queries() -> list[dict[str, str]]:
    specs = [
        ("SOURCE_CENTERED_DISCOVERY", "site:journals.uc.edu/index.php/vl/article/view/5932 Dori Griffin canon graphic design history visible language PDF", "SRC-0007", "https://journals.uc.edu/index.php/vl/article/view/5932", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "OFFICIAL_RECORD_AND_PDF_LOCATED", "Followed to official record, abstract, and publisher PDF."),
        ("COMPLETE_GROUP_QUERY", '"The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History" canon exclusion gender', "SRC-0007", "https://journals.uc.edu/index.php/vl/article/view/5932", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "OFFICIAL_RECORD_REVIEWED", "Exact group language reviewed at abstract and bounded PDF loci."),
        ("LOCATOR_FOLLOWUP", "official Visible Language PDF canonization", "SRC-0007", "https://journals.uc.edu/index.php/vl/article/download/5932/4796/7609", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "PUBLIC_PDF_LOCATOR_REVIEWED", "Publisher PDF pp.7,16-17,20 reviewed; payload not retained."),
        ("FALSIFICATION", 'Griffin PDF "male-dominated"', "SRC-0007", "https://journals.uc.edu/index.php/vl/article/download/5932/4796/7609", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "BOUNDED_GENDERED_CANON_LANGUAGE_FOUND", "Male-dominated qualifies the traditional canon; no general gendering rule inferred."),
        ("FALSIFICATION", 'Griffin PDF "inclusions and exclusions"', "SRC-0007", "https://journals.uc.edu/index.php/vl/article/download/5932/4796/7609", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "INCLUSION_EXCLUSION_MECHANISM_FOUND", "Bounded to Visible Language corpus and graphic-design historiography."),
        ("SOURCE_CENTERED_DISCOVERY", 'site:cambridge.org/core/journals/itinerario "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea"', "COMP-SRC-022", "https://www.cambridge.org/core/journals/itinerario/article/mobility-violence-and-the-afterlives-of-a-peruvian-painting-at-sea/0CCD9C903B8DDA855989858E63EEC238", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "OFFICIAL_OPEN_FULL_TEXT_LOCATED", "Official HTML and CC BY PDF reviewed."),
        ("COMPLETE_GROUP_QUERY", '"Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea" mobile object mediation market', "COMP-SRC-022", "https://www.cambridge.org/core/journals/itinerario/article/mobility-violence-and-the-afterlives-of-a-peruvian-painting-at-sea/0CCD9C903B8DDA855989858E63EEC238", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "SAME_OBJECT_MULTI_LOCUS_SUPPORT_FOUND", "Exact bounded configuration reviewed across one object biography."),
        ("LOCATOR_FOLLOWUP", 'Earle Deans-Smith PDF "Losing Its Identity"', "COMP-SRC-022", "https://www.cambridge.org/core/services/aop-cambridge-core/content/view/0CCD9C903B8DDA855989858E63EEC238/S0165115326100552a.pdf/mobility_violence_and_the_afterlives_of_a_peruvian_painting_at_sea.pdf", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "PUBLIC_CC_BY_PDF_LOCATOR_REVIEWED", "PDF pp.9-11 reviewed; payload not retained."),
        ("MECHANISM_SEARCH", 'Earle Deans-Smith PDF "Good business" publishers images', "COMP-SRC-022", "https://www.cambridge.org/core/services/aop-cambridge-core/content/view/0CCD9C903B8DDA855989858E63EEC238/S0165115326100552a.pdf/mobility_violence_and_the_afterlives_of_a_peruvian_painting_at_sea.pdf", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "COMMERCIAL_REUSE_LOCUS_FOUND", "PDF pp.17-18 ties representational reuse to market demand."),
        ("MECHANISM_SEARCH", 'Earle Deans-Smith PDF "investment opportunity" plates', "COMP-SRC-022", "https://www.cambridge.org/core/services/aop-cambridge-core/content/view/0CCD9C903B8DDA855989858E63EEC238/S0165115326100552a.pdf/mobility_violence_and_the_afterlives_of_a_peruvian_painting_at_sea.pdf", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "MARKET_AND_REPRESENTATION_LOCUS_FOUND", "PDF p.18 reviewed with earlier painting-to-print transformation."),
        ("FALSIFICATION", 'Earle Deans-Smith PDF commodification', "COMP-SRC-022", "https://www.cambridge.org/core/journals/itinerario/article/mobility-violence-and-the-afterlives-of-a-peruvian-painting-at-sea/0CCD9C903B8DDA855989858E63EEC238", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "EXACT_LABEL_ABSENT_MECHANISM_PRESENT", "No exact commodification label; group remains inquiry-only pending bounded-sense review."),
        ("SOURCE_CENTERED_DISCOVERY", 'site:academic.oup.com/jdh/article "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation"', "COMP-SRC-017", "https://academic.oup.com/jdh/article-abstract/19/2/105/515938", "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation", "OFFICIAL_ABSTRACT_LOCATED", "Official abstract compared to inherited evidence record."),
        ("LAWFUL_ACCESS_SEARCH", '"10.1093/jdh/epi050" PDF Pulhan Numan', "COMP-SRC-017", "https://academic.oup.com/jdh/article-abstract/19/2/105/515938", "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation", "FULL_TEXT_NOT_LAWFULLY_ESTABLISHED", "Available-for-purchase abstract only; no publisher payload retained."),
        ("SCOPE_FALSIFICATION", 'Hifsiye Pulhan Ibrahim Numan Cyprus urban house British colonial Ottoman', "COMP-SRC-017", "https://academic.oup.com/jdh/article-abstract/19/2/105/515938", "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation", "INHERITED_SCOPE_CONFLICT_FOUND", "Official abstract describes Latin/Venetian-to-Ottoman transformation, not inherited Ottoman-to-British claim."),
        ("RIGHTS_REVIEW", "official source access and redistribution terms for shard 2", "SHARD-002", "https://creativecommons.org/licenses/by/4.0/", "Creative Commons Attribution 4.0 International", "SOURCE_SPECIFIC_RIGHTS_RECORDED", "Only Earle/Deans-Smith is established CC BY; no source payload is committed."),
    ]
    rows = []
    for ordinal, spec in enumerate(specs, 1):
        phase, query, target, url, title, decision, followup = spec
        row = {
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "query_id": stable_id("R16B-QUERY", {"ordinal": ordinal, "query": query, "target": target}),
            "ordinal": ordinal,
            "recorded_at_utc": RETRIEVED_AT_UTC,
            "timestamp_precision": "POST_BATCH_CAPTURE_AFTER_ROOT_WEB_RUN",
            "query_phase": phase,
            "query_text": query,
            "target_source_id": target,
            "result_url": url,
            "result_title": title,
            "result_identity": stable_id("R16B-RESULT", {"url": url, "title": title}),
            "decision": decision,
            "result_is_association_evidence": "false",
            "locator_followup": followup,
            "rights_gate": "SOURCE_SPECIFIC_REVIEW_REQUIRED_OR_RECORDED",
        }
        rows.append(finalized(row))
    return rows


def build_triggers() -> list[dict[str, str]]:
    trigger_names = {
        row["trigger_id"]: row["trigger_name"]
        for row in read_tsv(CANDIDATE_TRIGGER_REGISTRY)
    }
    specs = [
        ("EXT-S2-001", "SRC-0007", "TRG-002", ["canonization", "gendering", "exclusion"], "The official abstract and bounded publisher-PDF loci identify canon construction, inclusion/exclusion, and the male-dominated qualification within one bounded historiographic argument."),
        ("EXT-S2-001", "SRC-0007", "TRG-005", ["canonization", "gendering", "exclusion"], "Canonization has pair degree zero in Round 16A, so its source-centred group context requires explicit review outside the pair graph."),
        ("EXT-S2-001", "SRC-0007", "TRG-006", ["canonization", "gendering", "exclusion"], "Exclusion is a governed research-only bounded sense with a source locus suggesting multi-concept participation; it remains inquiry-only."),
        ("EXT-S2-001", "SRC-0007", "TRG-010", ["canonization", "gendering", "exclusion"], "Adaptive source-centred, complete-group, locator, and falsification searches were required because local evidence did not establish an active higher-order association."),
        ("EXT-S2-002", "COMP-SRC-022", "TRG-002", ["mobile object", "mediation", "commodification"], "One locator-bearing article argument identifies the same painting's mobility, representational mediation, and market-conditioned reuse across bounded linked loci."),
        ("EXT-S2-002", "COMP-SRC-022", "TRG-005", ["mobile object", "mediation", "commodification"], "Mobile object has pair degree zero in Round 16A, so same-object higher-order evidence must be reviewed without pair projection."),
        ("EXT-S2-002", "COMP-SRC-022", "TRG-010", ["mobile object", "mediation", "commodification"], "Adaptive complete-group, mechanism, locator, and falsification searches were required because local pair-derived evidence could not expose this same-object configuration."),
    ]
    rows = []
    for ordinal, (candidate_key, source_id, trigger_id, labels, rationale) in enumerate(specs, 1):
        rows.append(finalized({
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "trigger_occurrence_id": stable_id("R16B-EXTERNAL-TRIGGER", {"candidate_key": candidate_key, "trigger_id": trigger_id, "source_id": source_id}),
            "ordinal": ordinal,
            "candidate_key": candidate_key,
            "trigger_id": trigger_id,
            "trigger_class": trigger_names[trigger_id],
            "source_id": source_id,
            "participant_labels_json": j(sorted(labels)),
            "participant_sense_ids_json": j(sorted(SENSES[label] for label in labels)),
            "rationale": rationale,
            "pair_graph_derivation": "false",
            "review_required": "true",
            "activation_created": "false",
            "product_path_created": "false",
            "pair_projection_created": "false",
        }))
    return rows


def build_trigger_matrix(triggers: list[dict[str, str]]) -> list[dict[str, str]]:
    trigger_registry = read_tsv(CANDIDATE_TRIGGER_REGISTRY)
    trigger_names = {row["trigger_id"]: row["trigger_name"] for row in trigger_registry}
    occurrences = {
        (row["candidate_key"], row["trigger_id"]): row["trigger_occurrence_id"]
        for row in triggers
    }
    applicable = {
        "EXT-S2-001": {"TRG-002", "TRG-005", "TRG-006", "TRG-010"},
        "EXT-S2-002": {"TRG-002", "TRG-005", "TRG-010"},
    }
    non_applicable_reasons = {
        "TRG-001": "No governed n-ary grammar record declares this exact participant set.",
        "TRG-003": "The hypothesis is one bounded source argument, not a synthesis of two or more separately governed evidence records sharing a case.",
        "TRG-004": "No prior Round 12-16A product or composition contains this exact semantic participant set.",
        "TRG-007": "No prior governed negative or near-miss control identifies this exact candidate; counterevidence is recorded within the inquiry review.",
        "TRG-008": "The two external candidates neither overlap nor nest and have no prior-product mapping conflict at this checkpoint.",
        "TRG-009": "No database or archive-provenance co-case query generated this candidate.",
        "TRG-011": "The candidate is inactive and product-ineligible; falsification searches were still performed, while the separate COMP-EVID-018 correction records the canonical counterevidence behavior.",
        "TRG-012": "The candidate uses already governed arity and source-pattern classes; recursive gap review remains open at the tranche level rather than generating this identity.",
    }
    candidate_labels = {
        "EXT-S2-001": ["canonization", "exclusion", "gendering"],
        "EXT-S2-002": ["commodification", "mediation", "mobile object"],
    }
    applicable_reasons = {
        ("EXT-S2-001", "TRG-002"): "The source's bounded historiographic argument joins the three proposed senses.",
        ("EXT-S2-001", "TRG-005"): "Canonization is active and isolated in the Round 16A pair graph.",
        ("EXT-S2-001", "TRG-006"): "Exclusion is governed research-only and appears in the bounded multi-concept locus.",
        ("EXT-S2-001", "TRG-010"): "Adaptive external discovery and falsification queries produced the reviewable source path.",
        ("EXT-S2-002", "TRG-002"): "One source argument follows one painting through mobility, mediation, and market-conditioned reuse.",
        ("EXT-S2-002", "TRG-005"): "Mobile object is active and isolated in the Round 16A pair graph.",
        ("EXT-S2-002", "TRG-010"): "Adaptive external source, mechanism, locator, and falsification queries were necessary.",
    }
    rows = []
    ordinal = 0
    for candidate_key in sorted(applicable):
        for trigger_id in sorted(trigger_names):
            ordinal += 1
            is_applicable = trigger_id in applicable[candidate_key]
            occurrence_id = occurrences.get((candidate_key, trigger_id), "")
            rationale = (
                applicable_reasons[(candidate_key, trigger_id)]
                if is_applicable
                else (
                    "All participant senses are governed active senses; no research-only bounded participant triggers this class."
                    if trigger_id == "TRG-006"
                    else non_applicable_reasons[trigger_id]
                )
            )
            rows.append(finalized({
                "authority_base_sha": AUTHORITY_BASE_SHA,
                "shard_id": SHARD_ID,
                "applicability_record_id": stable_id("R16B-EXTERNAL-TRIGGER-APPLICABILITY", {
                    "candidate_key": candidate_key,
                    "trigger_id": trigger_id,
                }),
                "ordinal": ordinal,
                "candidate_key": candidate_key,
                "participant_labels_json": j(candidate_labels[candidate_key]),
                "trigger_id": trigger_id,
                "trigger_name": trigger_names[trigger_id],
                "applicability": "APPLICABLE" if is_applicable else "NOT_APPLICABLE",
                "trigger_occurrence_id": occurrence_id,
                "occurrence_emitted": "true" if is_applicable else "false",
                "rationale": rationale,
                "activation_created": "false",
                "product_path_created": "false",
                "pair_projection_created": "false",
            }))
    if set(occurrences) != {
        (candidate_key, trigger_id)
        for candidate_key, trigger_ids in applicable.items()
        for trigger_id in trigger_ids
    }:
        raise ValueError("TRIGGER_APPLICABILITY_OCCURRENCE_MISMATCH")
    return rows


def build_families(triggers: list[dict[str, str]], hypotheses: list[dict[str, str]]) -> list[dict[str, str]]:
    trigger_by_key: dict[str, list[str]] = {}
    for row in triggers:
        trigger_by_key.setdefault(row["candidate_key"], []).append(row["trigger_occurrence_id"])
    specs = {
        "EXT-S2-001": "VISIBLE_LANGUAGE_CANON_CRITIQUE_1967_2015",
        "EXT-S2-002": "MEZA_PAINTING_MOBILITY_MEDIATION_MARKET_1790_1836",
    }
    hypotheses_by_key = {row["hypothesis_key"]: row for row in hypotheses}
    rows = []
    for candidate_key, hypothesis_key in specs.items():
        hypothesis = hypotheses_by_key[hypothesis_key]
        rows.append(finalized({
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "external_candidate_family_id": stable_id("R16B-EXTERNAL-FAMILY", {"candidate_key": candidate_key, "association_id": hypothesis["association_id"]}),
            "candidate_key": candidate_key,
            "hypothesis_id": hypothesis["hypothesis_id"],
            "association_id": hypothesis["association_id"],
            "association_revision_id": hypothesis["association_revision_id"],
            "participant_labels_json": hypothesis["participant_labels_json"],
            "participant_sense_ids_json": hypothesis["participant_sense_ids_json"],
            "arity": hypothesis["arity"],
            "trigger_occurrence_ids_json": j(sorted(trigger_by_key[candidate_key])),
            "candidate_origin": "EXTERNAL_ADAPTIVE_SOURCE_DISCOVERY_NOT_DERIVED_FROM_ROUND16A_PAIR_GRAPH",
            "local_family_match_count": "0",
            "final_source_level_disposition": hypothesis["source_level_disposition"],
            "activation_status": "INQUIRY_ONLY",
            "product_eligible": "false",
            "pair_projection_policy": "NONE",
            "external_human_review_status": "PENDING_NOT_ACTIVE",
        }))
    return rows


def build_vocab_impacts(hypotheses: list[dict[str, str]], corrections: list[dict[str, str]]) -> list[dict[str, str]]:
    hypothesis_by_label = {}
    for hypothesis in hypotheses:
        for label in json.loads(hypothesis["participant_labels_json"]):
            hypothesis_by_label.setdefault(label, []).append(hypothesis["association_id"])
    source_rows = {row["canonical_label"]: row for row in read_tsv(ISOLATED_TERMS)}
    decisions = {
        "canonization": ("INQUIRY_ONLY_HIGHER_ORDER_PATH_FOUND", "External human review and product-policy decision remain open."),
        "cultural transfer": ("NO_NEW_SHARD2_GROUP_EVIDENCE", "Continue adaptive discovery or define an explicit non-product/reclassification policy."),
        "cultural transformation": ("PRIOR_SUPPORT_QUARANTINED_ACTIVE_STATUS_REAUDIT_REQUIRED", corrections[0]["required_action"]),
        "mobile object": ("INQUIRY_ONLY_HIGHER_ORDER_PATH_FOUND", "External human review and product-policy decision remain open."),
        "self-exoticization": ("NO_NEW_SHARD2_GROUP_EVIDENCE", "Continue adaptive discovery or define an explicit non-product/reclassification policy."),
    }
    rows = []
    for label in sorted(decisions):
        source = source_rows[label]
        disposition, action = decisions[label]
        rows.append(finalized({
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "vocabulary_id": source["vocabulary_id"],
            "participant_sense_id": source["participant_sense_id"],
            "canonical_label": label,
            "round16a_pair_degree": source["round16a_pair_degree"],
            "shard2_association_ids_json": j(sorted(hypothesis_by_label.get(label, []))),
            "shard2_evidence_impact": disposition,
            "active_association_count": "0",
            "active_product_path_count": "0",
            "higher_order_composability_proven": "false",
            "product_accessibility_disposition": "OPEN_BLOCKING",
            "required_next_action": action,
            "closure_effect": "ACTIVE_NONCOMPOSABLE_VOCABULARY_REMAINS_UNRESOLVED",
        }))
    return rows


def build_rights() -> list[dict[str, str]]:
    common = {
        "retrieved_at_utc": RETRIEVED_AT_UTC,
        "retained_material_type": "BIBLIOGRAPHIC_IDENTITY_STABLE_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY",
        "retained_sha256": "NOT_APPLICABLE_NO_SOURCE_PAYLOAD_RETAINED",
        "extract_word_count": "0",
        "reviewer": REVIEWER,
        "review_status": "COMPLETE_FAIL_CLOSED",
    }
    specs = [
        {
            "source_id": "SRC-0007",
            "bibliographic_identity": "Dori Griffin (2016), The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History, Visible Language 50(3), 7-27",
            "stable_url": "https://journals.uc.edu/index.php/vl/article/view/5932",
            "doi_or_identifier": "VISIBLE-LANGUAGE-5932",
            "access_status": "PUBLIC_PUBLISHER_FULL_TEXT_REVIEWED",
            "access_condition": "Official record and publisher PDF accessible without authentication at review time",
            "license_identifier": "LICENSE_NOT_IDENTIFIED",
            "copyright_or_rights_holder": "Author and/or Visible Language; exact redistribution authority not established",
            "redistribution_authorized": "false",
            "retained_path_or_locator": "official record abstract; publisher PDF pp.7,16-17,20; no local payload",
            "notes": "Public access is not treated as redistribution permission; only bounded notes and locators are committed.",
        },
        {
            "source_id": "COMP-SRC-022",
            "bibliographic_identity": "Rebecca Earle and Susan Deans-Smith (2026), Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea, Itinerario 50(1), 191-212",
            "stable_url": "https://www.cambridge.org/core/journals/itinerario/article/mobility-violence-and-the-afterlives-of-a-peruvian-painting-at-sea/0CCD9C903B8DDA855989858E63EEC238",
            "doi_or_identifier": "10.1017/S0165115326100552",
            "access_status": "OPEN_ACCESS_PUBLISHER_FULL_TEXT_REVIEWED",
            "access_condition": "Official Cambridge HTML and PDF accessible without authentication",
            "license_identifier": "CC-BY-4.0",
            "copyright_or_rights_holder": "The Authors, 2026; Cambridge University Press on behalf of The Leiden Institute for History",
            "redistribution_authorized": "true_with_attribution_conditions",
            "retained_path_or_locator": "official HTML abstract/introduction and PDF pp.9-11,17-18; no local payload",
            "notes": "CC BY terms were visible on the official record; this repository still retains no publisher payload.",
        },
        {
            "source_id": "COMP-SRC-017",
            "bibliographic_identity": "H. Pulhan and I. Numan (2006), The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation, Journal of Design History 19(2), 105-119",
            "stable_url": "https://academic.oup.com/jdh/article-abstract/19/2/105/515938",
            "doi_or_identifier": "10.1093/jdh/epi050",
            "access_status": "PUBLIC_ABSTRACT_ONLY_FULL_TEXT_AVAILABLE_FOR_PURCHASE",
            "access_condition": "Official OUP abstract accessible; full-text lawful review not reproduced from committed provenance",
            "license_identifier": "ALL_RIGHTS_RESERVED",
            "copyright_or_rights_holder": "The Author(s), 2006; Oxford University Press on behalf of The Design History Society",
            "redistribution_authorized": "false",
            "retained_path_or_locator": "official OUP abstract only; no local payload",
            "notes": "The abstract materially conflicts with the inherited COMP-EVID-018 T0/T1 statement; evidence is quarantined.",
        },
    ]
    rows = []
    for spec in specs:
        row = dict(common)
        row.update(spec)
        row["rights_record_id"] = stable_id("R16B-SOURCE-RIGHTS", {"source_id": spec["source_id"], "retrieved_at": RETRIEVED_AT_UTC})
        row["authority_base_sha"] = AUTHORITY_BASE_SHA
        row["shard_id"] = SHARD_ID
        rows.append(finalized(row))
    return rows


def build_hypotheses(rights_by_source: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    specs = [
        {
            "hypothesis_key": "VISIBLE_LANGUAGE_CANON_CRITIQUE_1967_2015",
            "source_id": "SRC-0007",
            "labels": ["canonization", "gendering", "exclusion"],
            "scope": "Visible Language volumes 1-49 and the graphic/visual-communication historiographic canon reviewed by Griffin; no general canon law",
            "support_mode": "DIRECT_HIGHER_ORDER_SUPPORT_BOUNDED_CORPUS",
            "disposition": "DIRECT_GROUP_SUPPORT_INQUIRY_ONLY_BOUNDED_SENSE_AND_HUMAN_REVIEW_OPEN",
            "locators": ["official abstract", "publisher PDF p.7", "publisher PDF pp.16-17", "publisher PDF p.20"],
            "synthesis": ["canon construction through selection", "inclusion and exclusion establish corpus boundaries", "male-dominated qualification supplies gendered normative positioning"],
            "counterevidence": ["the journal also critiques and extends canonical boundaries", "gendering is a governed interpretation rather than the source's exact relation label"],
            "qualifications": ["exclusion is research-only vocabulary", "external design-history review remains pending", "not every omission is intentional exclusion"],
            "nonclaims": ["no causal or universal canonization rule", "no direction or role semantics activated", "no internal pair support manufactured"],
        },
        {
            "hypothesis_key": "MEZA_PAINTING_MOBILITY_MEDIATION_MARKET_1790_1836",
            "source_id": "COMP-SRC-022",
            "labels": ["mobile object", "mediation", "commodification"],
            "scope": "Meza's commissioned Peruvian painting and its seizure, sale, painting-to-print disassembly, republication, auction history, and market-conditioned reinterpretation, 1790-1836",
            "support_mode": "COHERENT_SINGLE_SOURCE_MULTI_LOCUS_SYNTHESIS",
            "disposition": "COHERENT_GROUP_SUPPORT_INQUIRY_ONLY_EXACT_COMMODIFICATION_LABEL_AND_HUMAN_REVIEW_OPEN",
            "locators": ["official abstract and introduction", "publisher PDF pp.9-11", "publisher PDF pp.17-18", "publisher PDF conclusion"],
            "synthesis": ["one object's bounded itinerary supplies mobile-object identity", "painting-to-print and publisher reuse shape reception and meaning", "purchase, auction, investment framing, commercial demand, and market forces supply the bounded market-value mechanism"],
            "counterevidence": ["violence and warfare, not markets alone, caused key movements", "the exact word commodification is absent"],
            "qualifications": ["same object and linked afterlives only", "commodification remains a bounded interpretive mapping", "external design-history review remains pending"],
            "nonclaims": ["not every mobile object is mediated or commodified", "no direction or causal topology activated", "no pair projection from the group"],
        },
    ]
    rows = []
    for spec in specs:
        labels = sorted(spec["labels"])
        association_id, revision_id = association_identity(labels, spec["hypothesis_key"])
        row = {
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "hypothesis_id": stable_id("R16B-HYPOTHESIS", {"source_id": spec["source_id"], "scope": spec["hypothesis_key"], "labels": labels}),
            "hypothesis_key": spec["hypothesis_key"],
            "association_id": association_id,
            "association_revision_id": revision_id,
            "association_class": "HIGHER_ORDER",
            "arity": len(labels),
            "participant_labels_json": j(labels),
            "participant_sense_ids_json": j(sorted(SENSES[label] for label in labels)),
            "order_semantics": "UNORDERED",
            "role_semantics": "NONE_UNTIL_EXTERNAL_REVIEW",
            "source_id": spec["source_id"],
            "rights_record_id": rights_by_source[spec["source_id"]]["rights_record_id"],
            "bounded_scope": spec["scope"],
            "locators_json": j(spec["locators"]),
            "support_mode": spec["support_mode"],
            "synthesis_steps_json": j(spec["synthesis"]),
            "counterevidence_json": j(spec["counterevidence"]),
            "qualifications_json": j(spec["qualifications"]),
            "source_level_disposition": spec["disposition"],
            "external_human_review_status": "PENDING_NOT_ACTIVE",
            "activation_status": "INQUIRY_ONLY",
            "product_eligible": "false",
            "product_path": "",
            "pair_projection_policy": "NONE",
            "implicit_pair_projection_count": "0",
            "nonclaims_json": j(spec["nonclaims"]),
            "closure_effect": "BLOCKS_HIGHER_ORDER_AND_PRODUCT_ASSOCIATION_CLOSURE_UNTIL_REVIEW",
        }
        rows.append(finalized(row))
    return rows


def build_reviews(hypotheses: list[dict[str, str]], rights: list[dict[str, str]]) -> list[dict[str, str]]:
    rights_by_source = {row["source_id"]: row for row in rights}
    hypotheses_by_source = {row["source_id"]: row for row in hypotheses}
    specs = [
        ("SRC-0007", "Dori Griffin", "2016", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "VISIBLE-LANGUAGE-5932", "PUBLIC_PUBLISHER_FULL_TEXT_REVIEWED", "LOCATOR_BEARING_FULL_TEXT_REVIEW", "DIRECT_GROUP_SUPPORT_INQUIRY_ONLY", "The bounded journal corpus links canon construction, inclusion/exclusion, and a male-dominated traditional canon while also documenting critique and expansion."),
        ("COMP-SRC-022", "Rebecca Earle;Susan Deans-Smith", "2026", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "10.1017/S0165115326100552", "OPEN_ACCESS_PUBLISHER_FULL_TEXT_REVIEWED", "LOCATOR_BEARING_FULL_TEXT_REVIEW", "COHERENT_SINGLE_SOURCE_MULTI_LOCUS_GROUP_SUPPORT_INQUIRY_ONLY", "One painting's itinerary, representational repurposing, commercial reuse, and market-conditioned meaning form a coherent bounded configuration."),
        ("COMP-SRC-017", "Hifsiye Pulhan;İbrahim Numan", "2006", "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation", "10.1093/jdh/epi050", "PUBLIC_ABSTRACT_ONLY_FULL_TEXT_AVAILABLE_FOR_PURCHASE", "OFFICIAL_ABSTRACT_SCOPE_RECONCILIATION", "INHERITED_EVIDENCE_SCOPE_CONFLICT_QUARANTINED", "The official abstract describes Latin/Venetian occidental to Ottoman Turkish oriental transformations; it does not establish the inherited Ottoman-to-British T0/T1 claim."),
    ]
    rows = []
    for source_id, authors, year, title, doi, access, surface, disposition, paraphrase in specs:
        hypothesis = hypotheses_by_source.get(source_id)
        row = {
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "source_review_id": stable_id("R16B-SOURCE-REVIEW", {"source_id": source_id, "retrieved_at": RETRIEVED_AT_UTC}),
            "source_id": source_id,
            "authors": authors,
            "year": year,
            "title": title,
            "doi_or_identifier": doi,
            "retrieved_at_utc": RETRIEVED_AT_UTC,
            "review_surface": surface,
            "access_status": access,
            "rights_record_id": rights_by_source[source_id]["rights_record_id"],
            "bounded_paraphrase": paraphrase,
            "source_level_disposition": disposition,
            "association_id": hypothesis["association_id"] if hypothesis else "",
            "association_revision_id": hypothesis["association_revision_id"] if hypothesis else "",
            "activation_created": "false",
            "product_path_created": "false",
            "pair_projection_created": "false",
            "copyrighted_payload_retained": "false",
            "human_review_status": "PENDING_FOR_ASSOCIATION_ACTIVATION" if hypothesis else "NOT_APPLICABLE_QUARANTINE",
            "closure_effect": "BLOCKING_OPEN_REVIEW_OR_SOURCE_RECONCILIATION",
        }
        rows.append(finalized(row))
    return rows


def inherited_evidence_line_sha256() -> str:
    path = REPO / COMPOSITION_EVIDENCE
    with path.open("rb") as handle:
        header = handle.readline()
        del header
        for line in handle:
            if line.startswith(b"COMP-EVID-018\t"):
                return sha256_bytes(line)
    raise ValueError("COMP-EVID-018 raw line missing")


def build_corrections(rights_by_source: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    row = {
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "reconciliation_id": stable_id("R16B-SOURCE-SCOPE-CORRECTION", {"evidence_id": "COMP-EVID-018", "official_locator": "OUP_ABSTRACT_2026-08-28"}),
        "legacy_evidence_id": "COMP-EVID-018",
        "legacy_source_id": "COMP-SRC-017",
        "legacy_row_sha256": inherited_evidence_line_sha256(),
        "legacy_claim": "Cypriot urban houses evidence change from Ottoman-period to British-colonial cultural configurations.",
        "legacy_locators": "title; abstract; pp.105-119",
        "official_review_url": "https://academic.oup.com/jdh/article-abstract/19/2/105/515938",
        "official_review_locator": "official OUP abstract",
        "method_trigger_id": "TRG-011",
        "method_trigger_name": "COUNTEREVIDENCE_AND_FALSIFICATION",
        "candidate_family_created": "false",
        "retrieved_at_utc": RETRIEVED_AT_UTC,
        "official_abstract_scope": "Nicosia houses and transformations from Latin/Frankish/Venetian occidental configurations into Ottoman Turkish oriental intrusions from the late sixteenth century.",
        "conflict_type": "TIME_PERIOD_DIRECTION_AND_HISTORICAL_STATE_MISMATCH",
        "reproducible_full_text_review": "false",
        "rights_record_id": rights_by_source["COMP-SRC-017"]["rights_record_id"],
        "additive_disposition": "SOURCE_SCOPE_CONFLICT_QUARANTINE",
        "legacy_pass_superseded": "true_for_round16b_use_only",
        "legacy_artifact_mutated": "false",
        "evidence_activation_eligible": "false",
        "product_eligible": "false",
        "pair_projection_eligible": "false",
        "cultural_transformation_vocabulary_effect": "ACTIVE_STATUS_REQUIRES_REAUDIT_OF_REMAINING_INDEPENDENT_SUPPORT_NO_AUTOMATIC_RECLASSIFICATION",
        "required_action": "Obtain lawful locator-bearing full text or correct the claim; independently re-audit remaining cultural-transformation support before activation, product use, or closure.",
        "closure_effect": "BLOCKS_CANDIDATE_UNIVERSE_HIGHER_ORDER_GLOBAL_COHERENCE_AND_FUNCTION3_CLOSURE",
        "nonclaims_json": j(["the abstract does not prove the full article omits British-period material", "metadata or title is not evidence", "the frozen legacy row is preserved for audit"]),
    }
    return [finalized(row)]


def build_gaps() -> list[dict[str, str]]:
    specs = [
        ("R16B-GAP-S2-001", "EXTERNAL_HUMAN_REVIEW", "Both shard-2 group hypotheses remain inquiry-only; source review is not activation authority.", "Obtain independent design-history review of bounded senses, synthesis, topology, and nonclaims."),
        ("R16B-GAP-S2-002", "CULTURAL_TRANSFORMATION_SUPPORT_REAUDIT", "COMP-EVID-018 is quarantined because the official abstract conflicts with the inherited T0/T1 claim.", "Re-audit remaining independent sources and lawful full text before preserving active/product eligibility."),
        ("R16B-GAP-S2-003", "ISOLATED_ACTIVE_TERMS", "Mobile object gains an inquiry-only higher-order path, not an active product path; cultural transfer, cultural transformation, canonization, and self-exoticization remain unresolved for product reachability.", "Resolve each active isolated term through active evidence, explicit inquiry-only policy, or reclassification."),
        ("R16B-GAP-S2-004", "RIGHTS_SCHEMA_RECONCILIATION", "Shard 1's rights ledger predates and omits several fields required by the committed rights policy.", "Create an additive full-policy shard-1 rights reconciliation before any shard-1 evidence activation."),
        ("R16B-GAP-S2-005", "CANDIDATE_TRIGGER_RECURSION", "Two adaptive source hypotheses do not prove external discovery or association-class completeness.", "Continue source-family, counterexample, citation-chain, and isolated-term search with resumable shards."),
        ("R16B-GAP-S2-006", "ROUND16A_GLOBAL_RECONCILIATION", "No prior Round 16A subgraph, composition, state, transition, workflow, or export is reconciled by this source shard.", "Run the independent global-coherence reconciliation before any product or computational closure claim."),
    ]
    rows = []
    for gap_id, gap_class, finding, action in specs:
        rows.append(finalized({
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "gap_id": gap_id,
            "gap_class": gap_class,
            "finding": finding,
            "required_action": action,
            "status": "OPEN_BLOCKING",
            "association_activation_allowed": "false",
            "product_activation_allowed": "false",
            "closure_allowed": "false",
        }))
    return rows


def build_report(census: dict[str, Any], hypotheses: list[dict[str, str]], correction: dict[str, str]) -> bytes:
    lines = [
        "# Adaptive Source Review Shard 002 and Source-Scope Reconciliation",
        "",
        f"Authority base: `{AUTHORITY_BASE_SHA}`. Retrieval record: `{RETRIEVED_AT_UTC}`.",
        "",
        "This shard records two bounded source-level higher-order hypotheses and one fail-closed source-scope correction. It retains no source payload, creates no active association or product path, projects no pair edge, and asserts no closure.",
        "",
        "## Source-level higher-order hypotheses",
        "",
    ]
    for row in hypotheses:
        labels = ", ".join(json.loads(row["participant_labels_json"]))
        lines.extend([
            f"- `{row['hypothesis_key']}` ({labels}): `{row['source_level_disposition']}`. Association `{row['association_id']}` remains inquiry-only, product-ineligible, and projection-free.",
        ])
    lines.extend([
        "",
        "## Additive correction",
        "",
        f"`{correction['legacy_evidence_id']}` is `{correction['additive_disposition']}` for Round 16B. The official OUP abstract concerns Latin/Frankish/Venetian-to-Ottoman transformations, while the inherited row asserts Ottoman-to-British states. The frozen legacy artifact is not edited; the correction supersedes its eligibility for Round 16B activation pending lawful full-text and independent support review.",
        "",
        "## Boundary",
        "",
        f"- source reviews: {census['source_review_count']}",
        f"- external trigger occurrences: {census['candidate_trigger_occurrence_count']}",
        f"- trigger applicability decisions: {census['candidate_trigger_applicability_row_count']}",
        f"- external candidate families: {census['candidate_family_count']}",
        f"- hypotheses: {census['higher_order_hypothesis_count']}",
        f"- source-scope corrections: {census['source_scope_correction_count']}",
        f"- isolated-active vocabulary impact rows: {census['active_vocabulary_impact_count']}",
        "- active associations: 0",
        "- product paths: 0",
        "- implicit pair projections: 0",
        "- closure flags: all false",
        "",
    ])
    return ("\n".join(lines)).encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    validate_inputs()
    queries = build_queries()
    triggers = build_triggers()
    trigger_matrix = build_trigger_matrix(triggers)
    rights = build_rights()
    rights_by_source = {row["source_id"]: row for row in rights}
    hypotheses = build_hypotheses(rights_by_source)
    families = build_families(triggers, hypotheses)
    reviews = build_reviews(hypotheses, rights)
    corrections = build_corrections(rights_by_source)
    vocab_impacts = build_vocab_impacts(hypotheses, corrections)
    gaps = build_gaps()

    census = {
        "schema_version": "trace-round16b-adaptive-source-review-shard-2-census/v1",
        "source_sha": SOURCE_SHA,
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "retrieved_at_utc": RETRIEVED_AT_UTC,
        "query_count": len(queries),
        "candidate_trigger_occurrence_count": len(triggers),
        "candidate_trigger_applicability_row_count": len(trigger_matrix),
        "candidate_family_count": len(families),
        "source_review_count": len(reviews),
        "rights_review_count": len(rights),
        "higher_order_hypothesis_count": len(hypotheses),
        "source_scope_correction_count": len(corrections),
        "active_vocabulary_impact_count": len(vocab_impacts),
        "open_gap_count": len(gaps),
        "association_arity_distribution": {"3": 2},
        "inquiry_only_association_identity_count": 2,
        "active_association_count": 0,
        "active_pending_review_count": 0,
        "product_eligible_association_count": 0,
        "implicit_pair_projection_count": 0,
        "copyrighted_payload_retained_count": 0,
        "quarantined_legacy_evidence_count": 1,
        "closure": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "candidate_universe_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
    }

    output: dict[str, bytes] = {
        QUERY_PATH: tsv_bytes(list(queries[0]), queries),
        TRIGGER_PATH: tsv_bytes(list(triggers[0]), triggers),
        TRIGGER_MATRIX_PATH: tsv_bytes(list(trigger_matrix[0]), trigger_matrix),
        FAMILY_PATH: tsv_bytes(list(families[0]), families),
        REVIEW_PATH: tsv_bytes(list(reviews[0]), reviews),
        RIGHTS_PATH: tsv_bytes(list(rights[0]), rights),
        HYPOTHESIS_PATH: tsv_bytes(list(hypotheses[0]), hypotheses),
        CORRECTION_PATH: tsv_bytes(list(corrections[0]), corrections),
        VOCAB_IMPACT_PATH: tsv_bytes(list(vocab_impacts[0]), vocab_impacts),
        GAP_PATH: tsv_bytes(list(gaps[0]), gaps),
        CENSUS_PATH: json_bytes(census),
    }
    output[REPORT_PATH] = build_report(census, hypotheses, corrections[0])
    manifest_rows = []
    for ordinal, (path, payload) in enumerate(sorted(output.items()), 1):
        manifest_rows.append({
            "ordinal": str(ordinal),
            "path": path,
            "sha256": sha256_bytes(payload),
            "size_bytes": str(len(payload)),
            "lfs_required": "false",
        })
    output[MANIFEST_PATH] = tsv_bytes(list(manifest_rows[0]), manifest_rows)
    aggregate_material = [{"path": path, "sha256": sha256_bytes(payload)} for path, payload in sorted(output.items())]
    receipt = {
        "schema_version": "trace-round16b-adaptive-source-review-shard-2-build/v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": SOURCE_SHA,
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "status": "PASS",
        "pinned_inputs": PINNED_INPUT_SHA256,
        "output_count_excluding_receipt": len(output),
        "output_hashes_excluding_receipt": {path: sha256_bytes(payload) for path, payload in sorted(output.items())},
        "aggregate_sha256_excluding_receipt": sha256_bytes(canonical_json(aggregate_material).encode("utf-8")),
        "counts": {key: value for key, value in census.items() if key.endswith("_count") or key == "query_count"},
        "non_authorizations": {
            "association_activation": False,
            "product_activation": False,
            "pair_projection": False,
            "history_rewrite": False,
            "force_push": False,
            "rollback_tag": False,
            "main_update": False,
            "deployment": False,
            "closure": False,
        },
    }
    output[RECEIPT_PATH] = json_bytes(receipt)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = build_outputs()
    failures = []
    for relative, payload in sorted(output.items()):
        path = REPO / relative
        if args.check:
            actual = path.read_bytes() if path.exists() else b""
            if actual != payload:
                failures.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    result = {
        "status": "PASS" if not failures else "FAIL",
        "mode": "CHECK" if args.check else "WRITE",
        "output_count": len(output),
        "mismatch_count": len(failures),
        "mismatches": failures,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
