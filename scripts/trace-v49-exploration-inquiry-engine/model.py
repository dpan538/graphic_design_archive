"""Language-neutral model vocabulary for the TRACE v49 inquiry reference engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CandidateResearchStatus(str, Enum):
    BOUNDED = "BOUNDED_NODE_ROLE_CANDIDATE"
    DEFERRED = "DEFERRED_NODE_ROLE_CANDIDATE"


class InquirySeedKind(str, Enum):
    PAIR = "PAIR_RESEARCH_QUESTION"
    SINGLE = "SINGLE_NODE_INQUIRY"


class InquiryTreeStrategy(str, Enum):
    LINEAR_PATH = "LINEAR_PATH"
    BINARY_FORK = "BINARY_FORK"
    BINARY_CONVERGENCE = "BINARY_CONVERGENCE"
    QUALIFIED_PATH = "QUALIFIED_PATH"
    REFLEXIVE_RETURN = "REFLEXIVE_RETURN"
    EVIDENCE_GAP_TREE = "EVIDENCE_GAP_TREE"


class InquiryLinkKind(str, Enum):
    OPEN_QUESTION = "OPEN_QUESTION"
    CONTRAST_QUESTION = "CONTRAST_QUESTION"
    CONDITION_QUESTION = "CONDITION_QUESTION"
    QUALIFICATION_QUESTION = "QUALIFICATION_QUESTION"
    REFLEXIVE_QUESTION = "REFLEXIVE_QUESTION"
    EVIDENCE_GAP_QUESTION = "EVIDENCE_GAP_QUESTION"


class TreeItemKind(str, Enum):
    SEMANTIC_NODE_REFERENCE = "SEMANTIC_NODE_REFERENCE"
    INQUIRY_OPERATION = "INQUIRY_OPERATION"
    EVIDENCE_NOTE = "EVIDENCE_NOTE"
    QUALIFICATION_NOTE = "QUALIFICATION_NOTE"
    CONTESTATION_NOTE = "CONTESTATION_NOTE"
    EVIDENCE_GAP_NOTE = "EVIDENCE_GAP_NOTE"


MAX_SEMANTIC_NODE_COUNT = 2
MAX_SIBLING_COUNT = 2
MAX_TREE_DEPTH = 4
MAX_TOTAL_TREE_ITEM_COUNT = 7


@dataclass(frozen=True)
class InquirySeed:
    seed_id: str
    seed_kind: InquirySeedKind
    candidate_sense_ids: tuple[str, ...]
    research_status: str
    pair_decision: str
    evidence_refs: tuple[str, ...]
    grammar_attestation_refs: tuple[str, ...]
    unresolved_gap_refs: tuple[str, ...]
    allowed_tree_strategies: tuple[InquiryTreeStrategy, ...]
    canonical_tree_strategy: InquiryTreeStrategy
    plain_language_research_question: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "seedId": self.seed_id,
            "seedKind": self.seed_kind.value,
            "candidateSenseIds": list(self.candidate_sense_ids),
            "researchStatus": self.research_status,
            "pairDecision": self.pair_decision,
            "evidenceRefs": list(self.evidence_refs),
            "grammarAttestationRefs": list(self.grammar_attestation_refs),
            "unresolvedGapRefs": list(self.unresolved_gap_refs),
            "allowedTreeStrategies": [value.value for value in self.allowed_tree_strategies],
            "canonicalTreeStrategy": self.canonical_tree_strategy.value,
            "plainLanguageResearchQuestion": self.plain_language_research_question,
            "historicalClaim": False,
            "publicExportable": False,
            "allowedOrigins": ["RESEARCH_INQUIRY"],
        }


def split_refs(value: str, separator: str = ";") -> list[str]:
    return sorted({item.strip() for item in value.split(separator) if item.strip()})
