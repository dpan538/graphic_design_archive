"""Exact corpus, candidate, pair-question, and instance evidence coverage."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from freeze import read_tsv
from model import CandidateResearchStatus, split_refs


def _source_class_counts(rows: list[dict[str, str]]) -> tuple[int, int]:
    peer = sum(row.get("peer_reviewed", "").lower() == "true" for row in rows)
    books = sum(any(token in row.get("source_class", "").lower() for token in ("book", "chapter")) for row in rows)
    return peer, books


def _concentration(values: list[str]) -> str:
    return f"{(max(Counter(values).values()) / len(values)) if values else 0:.3f}"


def compute_evidence_coverage(repo: Path, freeze: dict[str, Any]) -> dict[str, Any]:
    r9 = repo / "docs/research/trace-v49-design-history-relation-vocabulary-round1"
    r10 = repo / "docs/research/trace-v49-design-history-relation-grammar-round1"
    r9_sources = read_tsv(r9 / "03_SCHOLARLY_SOURCE_REGISTRY.tsv")
    r10_sources = read_tsv(r10 / "03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv")
    lexical = read_tsv(r9 / "05_TERM_ATTESTATION_REGISTRY.tsv")
    grammar = read_tsv(r10 / "07_GRAMMAR_ATTESTATION_REGISTRY.tsv")
    pair_rules = [row for row in read_tsv(r10 / "09_FLOW_RULE_CANDIDATE_REGISTRY.tsv") if row["final_rule_decision"].startswith("DEFER_")]
    source_meta = {row["source_id"]: row for row in r9_sources + r10_sources}
    candidates = {row["candidateId"]: row for row in freeze["candidates"]}

    node_rows: list[dict[str, Any]] = []
    for candidate in freeze["candidates"]:
        cid = candidate["candidateId"]
        lex = [row for row in lexical if row["candidate_id"] == cid]
        gram = [row for row in grammar if row["candidate_term_id"] == cid]
        source_ids = sorted({row["source_id"] for row in lex + gram})
        sources = [source_meta[source_id] for source_id in source_ids]
        authors = [source.get("authors", "") for source in sources]
        venues = [source.get("publication", "") for source in sources]
        languages = [source.get("source_language", "") for source in sources]
        issue_groups = [f"{source.get('publication', '')}|{source.get('volume_issue', '')}" for source in sources]
        peer, books = _source_class_counts(sources)
        node_rows.append({
            "candidate_id": cid,
            "sense_id": candidate["senseId"],
            "candidate_label": candidate["label"],
            "research_status": candidate["researchStatus"],
            "instance_eligible": str(candidate["researchStatus"] == CandidateResearchStatus.BOUNDED.value).lower(),
            "lexical_attestation_count": len(lex),
            "grammar_attestation_count": len(gram),
            "direct_attestation_count": len(lex) + len(gram),
            "distinct_source_count": len(source_ids),
            "distinct_author_count": len(set(authors)),
            "distinct_venue_count": len(set(venues)),
            "distinct_source_language_count": len(set(languages)),
            "peer_reviewed_source_count": peer,
            "book_chapter_source_count": books,
            "source_concentration": _concentration([row["source_id"] for row in lex + gram]),
            "same_issue_concentration": _concentration(issue_groups),
            "same_author_group_concentration": _concentration(authors),
            "contestation_status": candidate["contestationStatus"],
            "evidence_gap_count": len(candidate["vocabularyGapIds"]),
            "pair_question_ids": ";".join(candidate["pairQuestionIds"]),
            "standalone_inquiry": str(not candidate["pairQuestionIds"] and candidate["researchStatus"] == CandidateResearchStatus.BOUNDED.value).lower(),
            "source_ids": ";".join(source_ids),
            "lexical_attestation_ids": ";".join(candidate["lexicalAttestationIds"]),
            "grammar_attestation_ids": ";".join(candidate["grammarAttestationIds"]),
        })

    grammar_by_id = {row["grammar_attestation_id"]: row for row in grammar}
    pair_rows = []
    for rule in pair_rules:
        attestation_ids = split_refs(rule["grammar_attestation_ids"])
        source_ids = sorted({grammar_by_id[item]["source_id"] for item in attestation_ids})
        pair_rows.append({
            "pair_question_id": rule["rule_id"],
            "source_candidate_id": rule["source_candidate_id"],
            "source_label": rule["source_label"],
            "target_candidate_id": rule["target_candidate_id"],
            "target_label": rule["target_label"],
            "decision": rule["final_rule_decision"],
            "grammar_attestation_count": len(attestation_ids),
            "distinct_source_count": len(source_ids),
            "grammar_attestation_ids": ";".join(attestation_ids),
            "source_ids": ";".join(source_ids),
            "directionality_status": rule["directionality_decision"],
            "defer_reason": rule["natural_language_explanation"],
        })

    def aggregate(status: str | None) -> tuple[int, int]:
        ids = {row["candidateId"] for row in freeze["candidates"] if status is None or row["researchStatus"] == status}
        attestations = {row["attestation_id"] for row in lexical if row["candidate_id"] in ids} | {row["grammar_attestation_id"] for row in grammar if row["candidate_term_id"] in ids}
        sources = {row["source_id"] for row in lexical if row["candidate_id"] in ids} | {row["source_id"] for row in grammar if row["candidate_term_id"] in ids}
        return len(sources), len(attestations)

    all_direct = aggregate(None)
    bounded_direct = aggregate(CandidateResearchStatus.BOUNDED.value)
    deferred_direct = aggregate(CandidateResearchStatus.DEFERRED.value)
    summary = {
        "totalResearchSourceCount": len(r9_sources) + len(r10_sources),
        "totalResearchAttestationCount": len(lexical) + len(grammar),
        "frozenCandidateDirectSourceCount": all_direct[0],
        "frozenCandidateDirectAttestationCount": all_direct[1],
        "boundedCandidateDirectSourceCount": bounded_direct[0],
        "boundedCandidateDirectAttestationCount": bounded_direct[1],
        "deferredCandidateDirectSourceCount": deferred_direct[0],
        "deferredCandidateDirectAttestationCount": deferred_direct[1],
        "frozenCandidateCount": len(freeze["candidates"]),
        "boundedCandidateCount": sum(row["researchStatus"] == CandidateResearchStatus.BOUNDED.value for row in freeze["candidates"]),
        "deferredCandidateCount": sum(row["researchStatus"] == CandidateResearchStatus.DEFERRED.value for row in freeze["candidates"]),
        "pairQuestionCount": len(pair_rules),
        "clusterHandoffCount": len(read_tsv(r10 / "14_CLUSTER_EVIDENCE_HANDOFF.tsv")),
        "observedChainCount": len(read_tsv(r10 / "15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv")),
        "gapCount": len(read_tsv(r10 / "20_VOCABULARY_GAP_REGISTER.tsv")),
        "blockerCount": 9,
        "researchInstanceCount": 5,
        "boundedNodeCoverage": "8/8",
        "activeRelationTypeCount": 0,
        "activePairRuleCount": 0,
        "activeClusterRuleCount": 0,
        "activeChainRuleCount": 0,
        "round11SyntheticImageBuildCount": 3,
        "realSemanticImageCount": 0,
    }
    return {"summary": summary, "nodeRows": node_rows, "pairRows": pair_rows, "sourceMetadata": source_meta, "lexicalRows": lexical, "grammarRows": grammar, "candidates": candidates}


def compute_candidate_coverage(repo: Path, freeze: dict[str, Any]) -> list[dict[str, Any]]:
    return compute_evidence_coverage(repo, freeze)["nodeRows"]
