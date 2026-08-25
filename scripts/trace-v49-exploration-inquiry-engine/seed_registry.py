"""The exact five canonical research-inquiry seeds."""

from __future__ import annotations

from typing import Any

from model import InquirySeed, InquirySeedKind, InquiryTreeStrategy
from strict_parse import validate_inquiry_seed


SEED_SPECS = [
    ("INQUIRY-SEED-001", ("professionalization", "institutionalization"), InquirySeedKind.PAIR, "DEFERRED_PAIR_RESEARCH_QUESTION", "GRAM-RULE-001", InquiryTreeStrategy.BINARY_CONVERGENCE, "How might professionalization be examined alongside institutionalization when occupational formation and durable institutional embedding are not assumed to have one historical direction?"),
    ("INQUIRY-SEED-002", ("gendering", "commodification"), InquirySeedKind.PAIR, "DEFERRED_PAIR_RESEARCH_QUESTION", "GRAM-RULE-002", InquiryTreeStrategy.QUALIFIED_PATH, "How might gendering be examined alongside commodification when the available composition evidence comes from only one source and the market and gender regimes must remain explicit?"),
    ("INQUIRY-SEED-003", ("imitation", "piracy"), InquirySeedKind.PAIR, "DEFERRED_PAIR_RESEARCH_QUESTION", "GRAM-RULE-003", InquiryTreeStrategy.BINARY_FORK, "How might imitation be examined alongside piracy when legal, market, normative, and historical regimes determine whether the concepts remain distinct?"),
    ("INQUIRY-SEED-004", ("canonization",), InquirySeedKind.SINGLE, "SINGLE_NODE_INQUIRY", "NOT_APPLICABLE_SINGLE_NODE", InquiryTreeStrategy.BINARY_FORK, "How might canonization be investigated through bounded questions about selection and exclusion without inventing a second semantic concept?"),
    ("INQUIRY-SEED-005", ("self-exoticization",), InquirySeedKind.SINGLE, "SINGLE_NODE_INQUIRY", "NOT_APPLICABLE_SINGLE_NODE", InquiryTreeStrategy.REFLEXIVE_RETURN, "How might self-exoticization be investigated as a bounded reflexive research question while keeping agency, audience, external gaze, and power asymmetry explicit?"),
]


def build_seed_registry(freeze: dict[str, Any], pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_label = {candidate["label"]: candidate for candidate in freeze["candidates"]}
    pair_by_id = {row["pair_question_id"]: row for row in pair_rows}
    seeds = []
    for seed_id, labels, kind, status, pair_id, strategy, question in SEED_SPECS:
        candidates = [candidates_by_label[label] for label in labels]
        pair = pair_by_id.get(pair_id)
        grammar_refs = sorted({item for candidate in candidates for item in candidate["grammarAttestationIds"]})
        evidence_refs = sorted({item for candidate in candidates for item in candidate["sourceIds"]})
        gaps = sorted({item for candidate in candidates for item in candidate["vocabularyGapIds"]})
        if pair:
            grammar_refs = sorted(set(grammar_refs) | set(pair["grammar_attestation_ids"].split(";")))
            evidence_refs = sorted(set(evidence_refs) | set(pair["source_ids"].split(";")))
            gaps.append(f"PAIR-EVIDENCE-GAP:{pair_id}")
        gaps.append("REVIEW-GAP:EXTERNAL-DOMAIN-REVIEW")
        seed = InquirySeed(
            seed_id=seed_id,
            seed_kind=kind,
            candidate_sense_ids=tuple(candidate["senseId"] for candidate in candidates),
            research_status=status,
            pair_decision=pair["decision"] if pair else pair_id,
            evidence_refs=tuple(sorted(set(evidence_refs))),
            grammar_attestation_refs=tuple(sorted(set(grammar_refs))),
            unresolved_gap_refs=tuple(sorted(set(gaps))),
            allowed_tree_strategies=(strategy,),
            canonical_tree_strategy=strategy,
            plain_language_research_question=question,
        ).as_dict()
        seeds.append(validate_inquiry_seed(seed, freeze))
    if len(seeds) != 5 or len({sense for seed in seeds for sense in seed["candidateSenseIds"]}) != 8:
        raise ValueError("canonical seed registry does not cover exactly 8 bounded senses")
    return seeds


def load_inquiry_seed_registry(values: list[dict[str, Any]], freeze: dict[str, Any]) -> list[dict[str, Any]]:
    seeds = [validate_inquiry_seed(value, freeze) for value in values]
    if len(seeds) != 5 or len({seed["seedId"] for seed in seeds}) != 5:
        raise ValueError("seed registry identity/count mismatch")
    return seeds
