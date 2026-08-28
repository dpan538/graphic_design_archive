#!/usr/bin/env python3
"""Independently verify Round 16B adaptive-source-review shard 1.

This verifier intentionally does not import or execute the shard builder.  It
reconstructs expected source, query, rights, hypothesis, identity, and receipt
invariants from frozen constants and committed governed artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"

AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORIZED_SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
EVIDENCE_AUTHORITY_BASE_SHA = "f97d20b37b58a509d04cdf3bc3385486fc8d173c"
SHARD_ID = "R16B-ADAPTIVE-SOURCE-SHARD-001"
VERIFIER_VERSION = "trace-round16b-adaptive-source-review-independent-verifier-shard-1-v1"
UNCAPTURED_TIMESTAMP = "TIMESTAMP_NOT_CAPTURED_ROOT_WEB_TOOL"
EXPECTED_AGGREGATE_OUTPUT_SHA256 = "9718b8c5a11e8bc32b79048f210ebf3b2258d6eda9383c1f3e6a42320efc3b9b"

SOURCE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-shard-1-v1.tsv"
QUERY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-search-query-log-shard-1-v1.tsv"
RIGHTS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/source-rights-ledger-shard-1-v1.tsv"
HYPOTHESIS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv"
CENSUS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-census-shard-1-v1.json"
GAP_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/recursive-gap-ledger-adaptive-source-shard-1-v1.tsv"
NOTE_PATH = "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/13_ADAPTIVE_SOURCE_REVIEW_SHARD_1.md"
BUILD_RECEIPT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-build-receipt-shard-1-v1.json"
TRANCHE_C_IDENTITY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-higher-order-review-queue-tranche-c-v1.tsv"
VERIFICATION_RECEIPT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-independent-verification-shard-1-v1.json"

PINNED_INPUT_SHA256 = {
    "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv": "1f54c0956ca12dfaad472a6644c6102ee13b2e9a46f6c1794e21e1a2d7097dca",
    "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv": "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    "docs/research/trace-v49-exploration-composition-review-round1/06_VOCABULARY_GAP_EVIDENCE.tsv": "a38600ead90276d12b97a394443a93cefab1009ea7b391c36aa8d141fcee1051",
    "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv": "473eb44a3b43d3f63261076b13c05e09a1e8b2abb10de8cf73765b0aea597752",
    "docs/research/trace-v49-design-history-relation-grammar-round1/03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv": "9db7d8eaf85b1e104b40cc9412dca274a20b0c5b5715941ec6f234f46c21bd3d",
    "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv": "62b56052829d23cd2cf820a232479f74cbf663d64465cdc242900e71220df2a8",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/concept-sense-crosswalk-v1.tsv": "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-b-v1.tsv": "1f6547e799963d14c45335569aaa9a5facf9eb1715afe6c462605acdae16a090",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/conditional-scoped-child-reroute-queue-tranche-b-v1.tsv": "302394dab22ebc85800ac1555db633e3282f83c552026deacec32665ea16389d",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-b-v1.json": "143266126e7ec3e06158b56647e91c416ed896fb6ebb067656f88db74d7c952f",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-family-ledger-v2.tsv": "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scholarly-source-rights-policy.json": "b68037dff860421a4f413767a38ca07998cc9f215c75780f1e0019f32bf396ba",
    TRANCHE_C_IDENTITY_PATH: "d7ff7c13d75ad0ba14c1f84490b021956a23137d6e926f655057f2ea2009e22e",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(relative: str) -> str:
    return sha256_bytes((REPO / relative).read_bytes())


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def normalize_query(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}:{sha256_text(canonical_json(payload))}"


EXPECTED_SOURCES: dict[str, dict[str, Any]] = {
    "COMP-SRC-001": {
        "authors": "Grace Lees-Maffei", "year": "2008",
        "title": "Introduction: Professionalization as a Focus in Interior Design History",
        "doi": "10.1093/jdh/epn007", "access": "PUBLIC_ACCEPTED_MANUSCRIPT_REVIEWED",
        "text": "ACCEPTED_MANUSCRIPT_MULTI_LOCUS_REVIEWED",
        "rights": "ALL_RIGHTS_RESERVED_LINK_AND_BOUNDED_NOTES_ONLY",
        "license": "© Author 2008 / Oxford University Press / Design History Society; all rights reserved",
        "locators": ["accepted manuscript p.9", "accepted manuscript pp.3, 9, 14, 17"],
        "support": "COHERENT_SINGLE_SOURCE_MULTI_LOCUS_SYNTHESIS",
        "parent": "15f5757830dfe043fb27e73c28ff3bfd902aaa9c938ab254fda8682d359a7249",
        "parent_disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "nonclaims": ["not generic or all-period", "education is not asserted as a cause", "no direction, chronology, hierarchy, or pair relation is manufactured"],
    },
    "COMP-SRC-013": {
        "authors": "Tom Avermaete;Cathelijne Nuijsink", "year": "2021",
        "title": "Architectural Contact Zones: Another Way to Write Global Histories of the Post-War Period?",
        "doi": "10.1080/13264826.2021.1939745", "access": "PUBLIC_PUBLISHED_FULL_TEXT_REVIEWED",
        "text": "PUBLISHED_TEXT_LOCATOR_REVIEWED", "rights": "CC_BY_NC_ND_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY-NC-ND 4.0", "locators": ["printed p.354, Contact Zone section"],
        "support": "DIRECT_HIGHER_ORDER_SUPPORT_NEW_SENSE_REQUIRED",
        "parent": "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e",
        "parent_disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "nonclaims": ["alternatives are not successive stages", "no general topology, direction, or pair projection", "does not support the canonical Keraton-bounded sense"],
    },
    "COMP-SRC-014": {
        "authors": "Imam Santosa;I. Kadek Dwi Noorwatha", "year": "2025",
        "title": "Symbolic and Aesthetic Fusion in Keraton Surakarta: Colonial Influence and Javanese Cultural Resistance through Architectural Design Adaptation",
        "doi": "10.1080/23311983.2025.2482456", "access": "OPEN_ACCESS_PUBLISHED_FULL_TEXT_REVIEWED",
        "text": "PUBLISHED_TEXT_MULTI_SECTION_REVIEWED", "rights": "CC_BY_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY 4.0; © authors",
        "locators": ["abstract", "Cultural hybridity section", "Aesthetic adaptation section", "conclusion"],
        "support": "DIRECT_SCOPED_PAIR_SUPPORT_CONTEXT_QUALIFIED",
        "parent": "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e",
        "parent_disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "nonclaims": ["no generalization beyond the Keraton case", "no direction or pair projection from a larger group", "resistance is not converted into a new governed vocabulary node here"],
    },
    "COMP-SRC-020": {
        "authors": "Jane Hutton", "year": "2013",
        "title": "Reciprocal landscapes: material portraits in New York City and elsewhere",
        "doi": "10.1080/18626033.2013.798922", "access": "PUBLIC_AUTHOR_PDF_LAWFUL_READ_OBSERVED",
        "text": "AUTHOR_PDF_ARTICLE_METHOD_AND_CASE_STRUCTURE_REVIEWED",
        "rights": "READ_ACCESS_OBSERVED_REDISTRIBUTION_LICENSE_UNKNOWN_NOT_AUTHORIZED",
        "license": "Redistribution license unknown", "locators": ["p.40 abstract", "p.41"],
        "support": "ARTICLE_METHOD_LEVEL_SPARSE_HYPEREDGE_EXACT_ARITY5_BLOCKED",
        "parent": "d936154cb902968e2e5e0404e3dffaa3b61b47480b69f600b766b96351b66148",
        "parent_disposition": "INQUIRY_ONLY_OR_UNRESOLVED_AT_CHECKPOINT004",
        "nonclaims": ["not one exact five-member single-case association", "no unrelated pair-source synthesis", "no pair projection, product activation, or redistribution of the PDF"],
    },
    "COMP-SRC-023": {
        "authors": "Susan E. Reid", "year": "2017",
        "title": "Cold War Cultural Transactions: Designing the USSR for the West at Brussels Expo ’58",
        "doi": "10.1080/17547075.2017.1333388", "access": "PUBLIC_ABSTRACT_REVIEWED_FULL_TEXT_NOT_ESTABLISHED",
        "text": "PUBLISHER_ABSTRACT_AND_PRINTED_PAGE_REFERENCE_REVIEWED_FULL_TEXT_OPEN",
        "rights": "LICENSE_UNVERIFIED_REDISTRIBUTION_NOT_AUTHORIZED", "license": "LICENSE_NOT_VERIFIED",
        "locators": ["publisher abstract", "printed p.123 reference"],
        "support": "ABSTRACT_BEARING_SCOPED_PAIR_SUPPORT_FULL_TEXT_GROUP_GAP",
        "parent": "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1",
        "parent_disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "nonclaims": ["design diplomacy is not equivalent to propaganda", "do not mix Brussels, Turin, and Sweden cases", "no triad or reception claim"],
    },
    "COMP-SRC-024": {
        "authors": "Katarzyna Jeżowska", "year": "2024",
        "title": "Socialist, Humanist and Well-Designed: The Polish Welfare State at the International Labour Exhibition in Turin, 1961",
        "doi": "10.1017/S0960777322000029", "access": "OPEN_ACCESS_PUBLISHED_PDF_REVIEWED",
        "text": "PUBLISHED_TEXT_MULTI_LOCUS_REVIEWED", "rights": "CC_BY_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY 4.0", "locators": ["pp.173–175, abstract/introduction/Design Diplomacy", "p.190"],
        "support": "DIRECT_HIGHER_ORDER_SUPPORT_SAME_CASE",
        "parent": "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1",
        "parent_disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "nonclaims": ["no cross-case or general equivalence", "no audience success or reception outcome", "no pair projection"],
    },
    "COMP-SRC-025": {
        "authors": "Mark Ian Jones", "year": "2023",
        "title": "A Fleeting Glimpse? ‘Sweden’s Shop Window in Sydney’ — the Sweden at David Jones’ Exposition of 1954",
        "doi": "10.1080/10331867.2023.2282294", "access": "OPEN_ACCESS_PUBLISHED_PDF_REVIEWED",
        "text": "PUBLISHED_TEXT_EXACT_GROUP_LOCATOR_REVIEWED", "rights": "CC_BY_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY 4.0", "locators": ["p.282"],
        "support": "DIRECT_HIGHER_ORDER_SUPPORT_SAME_CASE_EXACT_ARITY4",
        "parent": "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a",
        "parent_disposition": "INQUIRY_ONLY_OR_UNRESOLVED_AT_CHECKPOINT004",
        "nonclaims": ["no audience acceptance, diplomatic outcome, or general law", "no internal pair or subset projection", "the identity remains inquiry-only pending external human review"],
    },
    "GRAM-SRC-025": {
        "authors": "Mike Bresnen", "year": "2013",
        "title": "Advancing a ‘new professionalism’: professionalization, practice and institutionalization",
        "doi": "10.1080/09613218.2013.843269", "access": "PUBLISHER_FREE_ACCESS_FULL_TEXT_REVIEWED",
        "text": "PUBLISHED_TEXT_LOCATOR_REVIEWED", "rights": "FREE_ACCESS_NO_CC_REDISTRIBUTION_NOT_AUTHORIZED",
        "license": "Publisher Free Access; no Creative Commons license identified",
        "locators": ["p.737", "end of Changing the system section before A neo-institutional perspective?"],
        "support": "DIRECT_LOCAL_HIGHER_ORDER_ATTESTATION_NEW_SENSE_REQUIRED",
        "parent": "d6dfcd4e355294899be8838eb8ec71439d8911ea19f8aa92401d1a52becf76c0",
        "parent_disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "nonclaims": ["not the canonical Bauhaus education sense", "no universal sequence, chronology, or direction", "no pair projection"],
    },
    "R16-SRC-005": {
        "authors": "Lorraine White-Hancock", "year": "2023",
        "title": "Insights from Bauhaus innovation for education and workplaces in a post-pandemic world",
        "doi": "10.1007/s10798-022-09729-2", "access": "OPEN_ACCESS_PUBLISHED_FULL_TEXT_REVIEWED",
        "text": "PUBLISHED_TEXT_MULTI_SECTION_REVIEWED", "rights": "CC_BY_4_0_WITH_THIRD_PARTY_EXCEPTIONS",
        "license": "CC BY 4.0 with third-party material exceptions",
        "locators": ["abstract", "Dimensions of innovation", "Learning in authentic workplace settings", "Bauhaus influence"],
        "support": "DIRECT_SCOPED_PAIR_SUPPORT_IDENTITY_RECONCILIATION_REQUIRED",
        "parent": "7696ac77a3bd8ac70e8e0181b3ae969502426a44200925dffb65ef88312e954a",
        "parent_disposition": "COOCCURRENCE_ONLY",
        "nonclaims": ["not a harmonious or universal Bauhaus model", "no equivalence or causal sequence", "no three-role group, product path, or pair projection"],
    },
}


EXPECTED_QUERY_BATCHES: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("2026-08-28T08:05:01Z", "SOURCE_TEXT_DISCOVERY", [
        ("\"Introduction: Professionalization as a Focus in Interior Design History\" accepted manuscript PDF Grace Lees-Maffei", "COMP-SRC-001"),
        ("\"Architectural Contact Zones\" Avermaete Nuijsink PDF", "COMP-SRC-013"),
        ("\"Symbolic and Aesthetic Fusion in Keraton Surakarta\" PDF", "COMP-SRC-014"),
        ("\"Cold War Cultural Transactions\" Susan E. Reid PDF", "COMP-SRC-023"),
    ]),
    ("2026-08-28T08:05:11Z", "SOURCE_TEXT_DISCOVERY", [
        ("\"Socialist, Humanist and Well-Designed\" Turin 1961 PDF Jeżowska", "COMP-SRC-024"),
        ("\"Insights from Bauhaus innovation for education and workplaces\" PDF", "R16-SRC-005"),
        ("\"Advancing a new professionalism\" Bresnen PDF institutional repository", "GRAM-SRC-025"),
        ("\"Cold War Cultural Transactions\" \"Brussels Expo\" Reid repository PDF", "COMP-SRC-023"),
    ]),
    ("2026-08-28T08:06:20Z", "EXACT_CONCEPT_AND_LOCATOR_FOLLOWUP", [
        ("\"Architectural Contact Zones\" \"adaptation\" \"rejection\"", "COMP-SRC-013"),
        ("\"Architectural Contact Zones\" \"selective borrowing\"", "COMP-SRC-013"),
        ("\"Architectural Contact Zones\" negotiation adaptation rejection p. 354", "COMP-SRC-013"),
        ("site:research-collection.ethz.ch/server/api/core/bitstreams \"rejection\" \"contact zones\"", "COMP-SRC-013"),
    ]),
    ("2026-08-28T08:06:32Z", "GROUP_COHERENCE_AND_BOUNDARY", [
        ("\"Cold War Cultural Transactions\" \"design diplomacy\" propaganda exhibition", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"counter-propaganda\"", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"negotiation\" \"compromise\" p. 123", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"Soviet Pavilion\" Brussels Expo 58 PDF", "COMP-SRC-023"),
    ]),
    ("2026-08-28T08:06:46Z", "PROPAGANDA_FALSIFICATION", [
        ("\"10.1080/17547075.2017.1333388\" propaganda", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" propaganda USSR pavilion", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"mass exhibitions\" propaganda", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" persuasion propaganda \"Expo 58\"", "COMP-SRC-023"),
    ]),
    ("2026-08-28T08:07:25Z", "PROFESSIONAL_EDUCATION_MECHANISM", [
        ("\"Advancing a new professionalism\" \"education and training\" institutionalization", "GRAM-SRC-025"),
        ("\"Advancing a ‘new professionalism’\" professionalization institutionalization education training", "GRAM-SRC-025"),
        ("\"Advancing a new professionalism\" \"institutional work\" education", "GRAM-SRC-025"),
        ("\"10.1080/09613218.2013.843269\" \"education\"", "GRAM-SRC-025"),
    ]),
    ("2026-08-28T08:07:40Z", "RIGHTS_AND_LICENSE", [
        ("\"Advancing a new professionalism\" \"© 2013\" Bresnen", "GRAM-SRC-025"),
        ("\"10.1080/09613218.2013.843269\" license", "GRAM-SRC-025"),
        ("site:tandfonline.com/doi/full/10.1080/09613218.2013.843269 \"Copyright\"", "GRAM-SRC-025"),
        ("site:tandfonline.com/doi/full/10.1080/17547075.2017.1333388 \"Copyright\"", "COMP-SRC-023"),
    ]),
    ("2026-08-28T08:09:45Z", "COUNTEREVIDENCE_AND_LIMITATION", [
        ("\"Introduction: Professionalization as a Focus in Interior Design History\" education institutionalization limitations", "COMP-SRC-001"),
        ("\"Architectural Contact Zones\" asymmetry adaptation rejection limitations", "COMP-SRC-013"),
        ("\"Keraton Surakarta\" adaptation negotiation resistance collaboration Dutch colonial rejection", "COMP-SRC-014"),
        ("\"Cold War Cultural Transactions\" propaganda reception compromise limitations", "COMP-SRC-023"),
    ]),
    ("2026-08-28T08:10:00Z", "COUNTEREVIDENCE_AND_LIMITATION", [
        ("\"Socialist, Humanist and Well-Designed\" propaganda design diplomacy archival scarce reception", "COMP-SRC-024"),
        ("\"Insights from Bauhaus innovation\" craft industrial focus challenged identities", "R16-SRC-005"),
        ("\"Advancing a new professionalism\" unintended consequences education training institutionalization", "GRAM-SRC-025"),
        ("\"Bauhaus innovation\" design education craft limitations workplace learning", "R16-SRC-005"),
    ]),
    (UNCAPTURED_TIMESTAMP, "ROOT_SOURCE_CENTERED_DISCOVERY", [
        ("site:tandfonline.com/doi/full/10.1080/10331867.2023.2282294 Sweden David Jones exposition trade propaganda design diplomacy", "COMP-SRC-025"),
        ("site:tandfonline.com/doi/abs/10.1080/18626033.2013.798922 reciprocal landscapes material portraits production consumption commodity chains", "COMP-SRC-020"),
        ("site:cambridge.org design diplomacy Turin 1961 international labour exhibition propaganda", "COMP-SRC-024"),
        ("site:tandfonline.com 10.1080/13264826.2021.1939745 contact zone adaptation rejection architecture", "COMP-SRC-013"),
    ]),
]


EXPECTED_HYPOTHESES = {
    "FORMAL_DESIGN_EDUCATION_1870_1970": ("COMP-SRC-001", ["institutionalization", "design education", "professionalization"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "ARCHITECTURAL_CONTACT_ZONE": ("COMP-SRC-013", ["adaptation", "contact-zone negotiation NEW", "rejection"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "KERATON_SURAKARTA": ("COMP-SRC-014", ["adaptation", "cultural negotiation"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "BRUSSELS_EXPO_1958": ("COMP-SRC-023", ["exhibition", "design diplomacy"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "TURIN_INTERNATIONAL_LABOUR_EXHIBITION_1961": ("COMP-SRC-024", ["exhibition", "propaganda", "design diplomacy"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "BAUHAUS_CRAFT_DESIGN_EDUCATION": ("R16-SRC-005", ["craft", "design education"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "PROFESSIONAL_EDUCATION_TRAINING_SENSE": ("GRAM-SRC-025", ["institutionalization", "professional education or training NEW", "professionalization"], "", "", "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"),
    "SWEDEN_IN_SYDNEY_1954": (
        "COMP-SRC-025", ["exhibition", "trade", "propaganda", "design diplomacy"],
        "R16B-ASSOC:4dcabb459b575457929aa565dc7579f43c0e78167fe466f0d0bd777835c19742",
        "R16B-ASSOC-REV:d22c9c9aae73bfcf3609e48a226c054aaad13dea9e477a3388224851beb35689",
        "INQUIRY_ONLY",
    ),
    "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013": (
        "COMP-SRC-020", ["consumption", "production site", "production", "material displacement", "supply chain"],
        "R16B-ASSOC:b2d7f71d946768a35ee4de75b912d325fbf778f950c9679ef32696596794933a",
        "R16B-ASSOC-REV:f6104d746a20cfb56943be568b578f3efc1add4dcd54647d3b3021f30381c46a",
        "INQUIRY_ONLY",
    ),
}


class Verification:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []
        self.failures: list[str] = []

    def require(self, name: str, condition: bool, detail: Any = None) -> None:
        passed = bool(condition)
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            self.failures.append(name)


def verify_record_hash(v: Verification, path: str, row: dict[str, str], row_ref: str) -> None:
    stored = row.get("record_sha256", "")
    unhashed = {key: value for key, value in row.items() if key != "record_sha256"}
    expected = sha256_text(canonical_json(unhashed))
    v.require(f"record_hash:{path}:{row_ref}", stored == expected, {"stored": stored, "expected": expected})


def association_identity(participant_sense_ids: list[str], scope_key: str) -> str:
    return stable_id("R16B-ASSOC", {
        "association_class": "HIGHER_ORDER",
        "participant_sense_ids": participant_sense_ids,
        "order_semantics": "UNORDERED",
        "role_semantics": "NONE_UNTIL_EXTERNAL_REVIEW",
        "scope_key": scope_key,
    })


def association_revision(association_id: str) -> str:
    return stable_id("R16B-ASSOC-REV", {
        "association_id": association_id,
        "activation_status": "INQUIRY_ONLY",
        "final_disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "pair_projection_policy": "NONE",
        "parent_checkpoint_sha": EVIDENCE_AUTHORITY_BASE_SHA,
        "product_eligibility": "INELIGIBLE",
        "review_tranche": "CHECKPOINT-007-EVIDENCE-TRANCHE-C",
    })


def build_verification_receipt() -> dict[str, Any]:
    v = Verification()

    for path, expected_hash in sorted(PINNED_INPUT_SHA256.items()):
        actual_hash = sha256_file(path)
        v.require(f"pinned_input:{path}", actual_hash == expected_hash, {"expected": expected_hash, "actual": actual_hash})

    source_rows = read_tsv(SOURCE_PATH)
    query_rows = read_tsv(QUERY_PATH)
    rights_rows = read_tsv(RIGHTS_PATH)
    hypothesis_rows = read_tsv(HYPOTHESIS_PATH)
    gap_rows = read_tsv(GAP_PATH)
    census = json.loads((REPO / CENSUS_PATH).read_text(encoding="utf-8"))
    build_receipt = json.loads((REPO / BUILD_RECEIPT_PATH).read_text(encoding="utf-8"))
    tranche_c_rows = read_tsv(TRANCHE_C_IDENTITY_PATH)

    v.require("source_count", len(source_rows) == 9, len(source_rows))
    v.require("rights_count", len(rights_rows) == 9, len(rights_rows))
    v.require("query_count", len(query_rows) == 40, len(query_rows))
    v.require("hypothesis_count", len(hypothesis_rows) == 9, len(hypothesis_rows))
    v.require("gap_count", len(gap_rows) == 8, len(gap_rows))

    source_by_id = {row["source_id"]: row for row in source_rows}
    rights_by_id = {row["source_id"]: row for row in rights_rows}
    v.require("source_identity_set", set(source_by_id) == set(EXPECTED_SOURCES), sorted(source_by_id))
    v.require("rights_identity_set", set(rights_by_id) == set(EXPECTED_SOURCES), sorted(rights_by_id))
    for source_id, expected in sorted(EXPECTED_SOURCES.items()):
        row = source_by_id[source_id]
        verify_record_hash(v, SOURCE_PATH, row, source_id)
        for field, wanted in (
            ("authors", expected["authors"]), ("year", expected["year"]), ("title", expected["title"]),
            ("doi", expected["doi"]), ("access_status", expected["access"]),
            ("source_text_review_status", expected["text"]), ("rights_status", expected["rights"]),
            ("license_expression", expected["license"]), ("support_mode", expected["support"]),
            ("linked_parent_candidate_id", f"R16B-LOCAL-FAMILY:{expected['parent']}"),
            ("parent_disposition_preserved", expected["parent_disposition"]),
        ):
            v.require(f"source:{source_id}:{field}", row[field] == wanted, {"expected": wanted, "actual": row[field]})
        v.require(f"source:{source_id}:locators", json.loads(row["locators_json"]) == expected["locators"], json.loads(row["locators_json"]))
        v.require(f"source:{source_id}:nonclaims", json.loads(row["nonclaims_json"]) == expected["nonclaims"], json.loads(row["nonclaims_json"]))
        v.require(f"source:{source_id}:conflicts_nonempty", len(json.loads(row["conflicts_or_counterevidence_json"])) > 0)
        v.require(f"source:{source_id}:bounded_paraphrase", len(row["bounded_paraphrase"]) >= 60)
        v.require(f"source:{source_id}:support_boundary", len(row["direct_support_boundary"]) >= 60)
        v.require(f"source:{source_id}:no_retained_payload", row["retained_payload_status"] == "NO_REMOTE_SOURCE_PAYLOAD_RETAINED" and row["retained_payload_sha256"] == "")
        v.require(f"source:{source_id}:inactive", row["active_fact_created"] == "false" and row["association_activation"] == "INACTIVE")
        v.require(f"source:{source_id}:no_product_or_projection", row["product_eligibility"].startswith("INELIGIBLE") and row["pair_projection_count"] == "0")
        v.require(f"source:{source_id}:human_open", row["human_review_status"] == "PENDING_EXTERNAL_DESIGN_HISTORY_REVIEW")

        rights = rights_by_id[source_id]
        verify_record_hash(v, RIGHTS_PATH, rights, source_id)
        for field, wanted in (
            ("doi", expected["doi"]), ("access_status", expected["access"]),
            ("source_text_review_status", expected["text"]), ("rights_status", expected["rights"]),
            ("license_expression", expected["license"]),
        ):
            v.require(f"rights:{source_id}:{field}", rights[field] == wanted, {"expected": wanted, "actual": rights[field]})
        v.require(f"rights:{source_id}:payload_absent", rights["payload_retained"] == "false" and rights["payload_sha256"] == "")
        v.require(f"rights:{source_id}:bounded_commit", rights["committed_material"] == "NO_REMOTE_FULL_TEXT; NO_COPYRIGHTED_PAYLOAD; NO_EXTENDED_EXTRACT")
        v.require(f"rights:{source_id}:record_url", len(json.loads(rights["record_urls_json"])) >= 1)
        if source_id == "COMP-SRC-023":
            v.require("rights:COMP-SRC-023:no_full_text_url", json.loads(rights["text_urls_json"]) == [])
        else:
            v.require(f"rights:{source_id}:text_url", len(json.loads(rights["text_urls_json"])) >= 1)

    expected_query_rows: list[dict[str, str]] = []
    ordinal = 0
    for batch_ordinal, (timestamp, purpose, query_specs) in enumerate(EXPECTED_QUERY_BATCHES, 1):
        for query_text, target_source_id in query_specs:
            ordinal += 1
            expected_query_rows.append({
                "batch_id": f"R16B-ADAPTIVE-QUERY-BATCH-{batch_ordinal:03d}",
                "batch_timestamp_utc": timestamp,
                "timestamp_capture_status": "NOT_CAPTURED_DO_NOT_INFER" if timestamp == UNCAPTURED_TIMESTAMP else "EXACT_CAPTURED_UTC",
                "query_ordinal": str(ordinal),
                "query_id": stable_id("R16B-ADAPTIVE-QUERY", {
                    "timestamp": timestamp, "query": query_text,
                    "target_source_id": target_source_id, "purpose": purpose,
                }),
                "purpose": purpose,
                "exact_query_text": query_text,
                "normalized_query_text": normalize_query(query_text),
                "target_source_id": target_source_id,
            })
    v.require("expected_query_cardinality", len(expected_query_rows) == 40)
    queries_by_id = {row["query_id"]: row for row in query_rows}
    v.require("query_id_unique", len(queries_by_id) == len(query_rows))
    v.require("query_exact_id_set", set(queries_by_id) == {row["query_id"] for row in expected_query_rows})
    expected_ids_by_source: dict[str, list[str]] = defaultdict(list)
    for expected in expected_query_rows:
        row = queries_by_id[expected["query_id"]]
        expected_ids_by_source[expected["target_source_id"]].append(expected["query_id"])
        verify_record_hash(v, QUERY_PATH, row, expected["query_id"])
        for field, wanted in expected.items():
            v.require(f"query:{expected['query_ordinal']}:{field}", row[field] == wanted, {"expected": wanted, "actual": row[field]})
        v.require(f"query:{expected['query_ordinal']}:authority", row["evidence_authority_base_sha"] == EVIDENCE_AUTHORITY_BASE_SHA and row["shard_id"] == SHARD_ID)
        v.require(f"query:{expected['query_ordinal']}:service", row["service"] == "ROOT_WEB_SEARCH_TOOL")
        v.require(f"query:{expected['query_ordinal']}:discovery_only", row["evidence_use"] == "DISCOVERY_AND_FALSIFICATION_TRAIL_ONLY_NOT_ASSOCIATION_EVIDENCE")
        v.require(f"query:{expected['query_ordinal']}:rejection_boundary", "not association evidence" in row["rejection_reason"])
        v.require(f"query:{expected['query_ordinal']}:result_identity", json.loads(row["result_identity_json"]) == {"source_id": expected["target_source_id"], "doi": EXPECTED_SOURCES[expected["target_source_id"]]["doi"]})
        v.require(f"query:{expected['query_ordinal']}:stable_locator", len(json.loads(row["stable_locators_json"])) >= 1)
    v.require("query_exact_timestamp_count", sum(row["timestamp_capture_status"] == "EXACT_CAPTURED_UTC" for row in query_rows) == 36)
    v.require("query_literal_uncaptured_count", sum(row["batch_timestamp_utc"] == UNCAPTURED_TIMESTAMP and row["timestamp_capture_status"] == "NOT_CAPTURED_DO_NOT_INFER" for row in query_rows) == 4)
    for source_id, row in source_by_id.items():
        v.require(f"source:{source_id}:exact_query_refs", json.loads(row["exact_query_ids_json"]) == sorted(expected_ids_by_source[source_id]))
        has_uncaptured = any(queries_by_id[qid]["batch_timestamp_utc"] == UNCAPTURED_TIMESTAMP for qid in expected_ids_by_source[source_id])
        has_captured = any(queries_by_id[qid]["batch_timestamp_utc"] != UNCAPTURED_TIMESTAMP for qid in expected_ids_by_source[source_id])
        wanted = "MIXED_CAPTURED_AND_EXPLICIT_UNCAPTURED" if has_uncaptured and has_captured else "EXPLICIT_UNCAPTURED_ONLY_DO_NOT_INFER" if has_uncaptured else "ALL_REPORTED_QUERY_TIMESTAMPS_EXACT_CAPTURED_UTC"
        v.require(f"source:{source_id}:query_timestamp_status", row["query_timestamp_status"] == wanted, {"expected": wanted, "actual": row["query_timestamp_status"]})

    hypothesis_by_scope = {row["scope_key"]: row for row in hypothesis_rows}
    v.require("hypothesis_scope_set", set(hypothesis_by_scope) == set(EXPECTED_HYPOTHESES), sorted(hypothesis_by_scope))
    for scope_key, (source_id, labels, assoc_id, revision_id, identity_status) in EXPECTED_HYPOTHESES.items():
        row = hypothesis_by_scope[scope_key]
        verify_record_hash(v, HYPOTHESIS_PATH, row, scope_key)
        v.require(f"hypothesis:{scope_key}:source", json.loads(row["source_ids_json"]) == [source_id])
        v.require(f"hypothesis:{scope_key}:labels", json.loads(row["participant_labels_json"]) == labels)
        v.require(f"hypothesis:{scope_key}:arity", row["arity"] == str(len(labels)))
        v.require(f"hypothesis:{scope_key}:association_id", row["governed_association_id"] == assoc_id)
        v.require(f"hypothesis:{scope_key}:revision_id", row["governed_association_revision_id"] == revision_id)
        v.require(f"hypothesis:{scope_key}:identity_status", row["governed_identity_status"] == identity_status)
        v.require(f"hypothesis:{scope_key}:inactive", row["association_activation_status"] == "INACTIVE" and row["active_fact_created"] == "false")
        v.require(f"hypothesis:{scope_key}:no_product_projection", row["product_eligibility"].startswith("INELIGIBLE") and row["pair_projection_count"] == "0" and row["subset_projection_count"] == "0")
        v.require(f"hypothesis:{scope_key}:human_open", row["external_human_review_status"] == "OPEN")
        v.require(f"hypothesis:{scope_key}:unordered_no_roles", row["participant_order_meaningful"] == "false" and row["relation_roles_asserted"] == "false")
        if assoc_id:
            participant_sense_ids = json.loads(row["participant_sense_ids_json"])
            v.require(f"hypothesis:{scope_key}:identity_formula", association_identity(participant_sense_ids, scope_key) == assoc_id)
            v.require(f"hypothesis:{scope_key}:revision_formula", association_revision(assoc_id) == revision_id)
            v.require(f"hypothesis:{scope_key}:tranche_c_authority", row["canonical_identity_authority_path"] == TRANCHE_C_IDENTITY_PATH)
        else:
            v.require(f"hypothesis:{scope_key}:no_identity_authority", row["canonical_identity_authority_path"] == "" and row["canonical_identity_queue_ref"] == "")

    hutton = hypothesis_by_scope["HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013"]
    v.require("hutton_exact_active_group_blocked", hutton["exact_group_support_status"] == "EXACT_CURRENT_SENSE_GROUP_NOT_SUPPORTED_METHOD_LEVEL_VALUE_ONLY" and hutton["global_coherence_status"] == "FAIL_EXACT_ARITY5_CASE_AND_SENSE_CONFLICT")
    sweden = hypothesis_by_scope["SWEDEN_IN_SYDNEY_1954"]
    v.require("sweden_exact_group_source_support", sweden["exact_group_support_status"] == "DIRECT_EXACT_GROUP_SUPPORT_CURRENT_SENSES_SAME_CASE" and sweden["global_coherence_status"] == "PASS_SOURCE_LEVEL_SAME_CASE_HUMAN_REVIEW_OPEN")

    c_identities = {row["scope_key"]: row for row in tranche_c_rows if row["queue_record_kind"] == "SCOPED_INQUIRY_IDENTITY"}
    for scope_key in ("SWEDEN_IN_SYDNEY_1954", "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013"):
        source_row = hypothesis_by_scope[scope_key]
        c_row = c_identities[scope_key]
        verify_record_hash(v, TRANCHE_C_IDENTITY_PATH, c_row, scope_key)
        v.require(f"cross_artifact:{scope_key}:association", source_row["governed_association_id"] == c_row["association_id"])
        v.require(f"cross_artifact:{scope_key}:revision", source_row["governed_association_revision_id"] == c_row["association_revision_id"])
        v.require(f"cross_artifact:{scope_key}:participants", source_row["participant_sense_ids_json"] == c_row["participant_sense_ids_json"])
        v.require(f"cross_artifact:{scope_key}:queue_ref", source_row["canonical_identity_queue_ref"] == c_row["queue_ref"])
        v.require(f"cross_artifact:{scope_key}:fail_closed", c_row["association_activation_status"] == "INQUIRY_ONLY" and c_row["pair_projection_policy"] == "NONE" and c_row["pair_projection_created"] == "false" and c_row["subset_projection_created"] == "false" and c_row["product_path_created"] == "false" and c_row["product_eligibility"] == "INELIGIBLE")

    for row in gap_rows:
        verify_record_hash(v, GAP_PATH, row, row["gap_class"])
        v.require(f"gap:{row['gap_class']}:open", row["status"] == "OPEN")
        v.require(f"gap:{row['gap_class']}:closure_effect", row["closure_effect"] != "")

    expected_census_scalars = {
        "source_sha": AUTHORIZED_SOURCE_SHA, "source_tree": AUTHORIZED_SOURCE_TREE,
        "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA, "shard_id": SHARD_ID,
        "source_review_count": 9, "rights_record_count": 9, "query_batch_count": 10,
        "query_count": 40, "query_with_exact_captured_timestamp_count": 36,
        "query_with_explicit_uncaptured_timestamp_count": 4, "remote_payload_retained_count": 0,
        "remote_payload_sha256_count": 0, "scoped_hypothesis_count": 9,
        "exact_current_sense_same_case_direct_higher_order_support_count": 2,
        "governed_inquiry_only_association_identity_count": 2, "association_activation_count": 0,
        "active_fact_created_count": 0, "product_eligible_count": 0, "pair_projection_count": 0,
        "subset_projection_count": 0, "active_pending_review_count": 0, "open_gap_count": 8,
        "canonical_identity_authority_path": TRANCHE_C_IDENTITY_PATH,
        "canonical_identity_authority_sha256": PINNED_INPUT_SHA256[TRANCHE_C_IDENTITY_PATH],
    }
    for field, wanted in expected_census_scalars.items():
        v.require(f"census:{field}", census[field] == wanted, {"expected": wanted, "actual": census[field]})
    v.require("census:closure_all_false", set(census["closure"].values()) == {False} and len(census["closure"]) == 6)
    v.require("census:arity_distribution", census["hypothesis_arity_distribution"] == {"2": 3, "3": 4, "4": 1, "5": 1}, census["hypothesis_arity_distribution"])

    expected_receipt_scalars = {
        "source_sha": AUTHORIZED_SOURCE_SHA, "source_tree": AUTHORIZED_SOURCE_TREE,
        "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA, "shard_id": SHARD_ID,
        "source_review_count": 9, "rights_record_count": 9, "query_batch_count": 10,
        "query_count": 40, "query_exact_timestamp_count": 36,
        "query_explicit_uncaptured_timestamp_count": 4, "scoped_hypothesis_count": 9,
        "governed_inquiry_only_association_identity_count": 2, "remote_payload_retained_count": 0,
        "remote_payload_sha256_count": 0, "association_activation_count": 0,
        "active_fact_created_count": 0, "active_pending_review_count": 0,
        "product_eligible_count": 0, "pair_projection_count": 0, "subset_projection_count": 0,
        "closure_flags_true_count": 0, "open_gap_count": 8,
        "canonical_identity_authority_path": TRANCHE_C_IDENTITY_PATH,
        "canonical_identity_authority_sha256": PINNED_INPUT_SHA256[TRANCHE_C_IDENTITY_PATH],
        "aggregate_output_sha256": EXPECTED_AGGREGATE_OUTPUT_SHA256,
        "status": "PASS_FAIL_CLOSED_ADAPTIVE_SOURCE_SHARD_1",
    }
    for field, wanted in expected_receipt_scalars.items():
        v.require(f"build_receipt:{field}", build_receipt[field] == wanted, {"expected": wanted, "actual": build_receipt[field]})
    v.require("build_receipt:pinned_inputs", build_receipt["pinned_input_hashes"] == {k: v for k, v in PINNED_INPUT_SHA256.items() if k != TRANCHE_C_IDENTITY_PATH})
    verified_output_hashes: dict[str, dict[str, Any]] = {}
    for path, metadata in sorted(build_receipt["output_hashes"].items()):
        payload = (REPO / path).read_bytes()
        actual = {"bytes": len(payload), "sha256": sha256_bytes(payload)}
        verified_output_hashes[path] = actual
        v.require(f"output_hash:{path}", actual == metadata, {"receipt": metadata, "actual": actual})
    aggregate = sha256_text(canonical_json(verified_output_hashes))
    v.require("output_hash_aggregate", aggregate == EXPECTED_AGGREGATE_OUTPUT_SHA256, aggregate)
    v.require("output_hash_path_set", set(verified_output_hashes) == {SOURCE_PATH, QUERY_PATH, RIGHTS_PATH, HYPOTHESIS_PATH, CENSUS_PATH, GAP_PATH, NOTE_PATH})

    authority_counts = Counter(row["evidence_authority_base_sha"] for rows in (source_rows, query_rows, rights_rows, hypothesis_rows, gap_rows) for row in rows)
    v.require("all_rows_bind_evidence_authority", authority_counts == {EVIDENCE_AUTHORITY_BASE_SHA: 75}, dict(authority_counts))
    v.require("all_source_nonclaims_present", all(len(json.loads(row["nonclaims_json"])) >= 3 for row in source_rows))
    v.require("zero_activation_all_ledgers", all(row["active_fact_created"] == "false" for row in source_rows + hypothesis_rows))
    v.require("zero_product_all_hypotheses", all(row["product_eligibility"].startswith("INELIGIBLE") for row in hypothesis_rows))
    v.require("zero_projection_all_hypotheses", all(row["pair_projection_count"] == "0" and row["subset_projection_count"] == "0" for row in hypothesis_rows))

    status = "PASS" if not v.failures else "FAIL"
    receipt = {
        "format": "trace-round16b-adaptive-source-review-independent-verification-shard-1-v1",
        "verifier_version": VERIFIER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "independent_from_builder_implementation": True,
        "builder_imported_or_called": False,
        "pinned_input_hashes": dict(sorted(PINNED_INPUT_SHA256.items())),
        "expected_aggregate_output_sha256": EXPECTED_AGGREGATE_OUTPUT_SHA256,
        "verified_output_hashes": verified_output_hashes,
        "source_review_count": len(source_rows),
        "rights_record_count": len(rights_rows),
        "query_count": len(query_rows),
        "hypothesis_count": len(hypothesis_rows),
        "canonical_inquiry_identity_count": 2,
        "active_fact_count": 0,
        "product_eligible_count": 0,
        "pair_projection_count": 0,
        "subset_projection_count": 0,
        "closure_flags_true_count": 0,
        "check_count": len(v.checks),
        "pass_count": sum(check["passed"] for check in v.checks),
        "failure_count": len(v.failures),
        "failures": v.failures,
        "checks": v.checks,
        "status": status,
    }
    return receipt


def receipt_bytes(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare verification bytes with existing receipt")
    args = parser.parse_args()
    receipt = build_verification_receipt()
    payload = receipt_bytes(receipt)
    path = REPO / VERIFICATION_RECEIPT_PATH
    if args.check:
        if not path.exists() or path.read_bytes() != payload:
            raise SystemExit("independent verification receipt mismatch")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(canonical_json({
        "status": receipt["status"], "check_count": receipt["check_count"],
        "pass_count": receipt["pass_count"], "failure_count": receipt["failure_count"],
        "receipt_sha256": sha256_bytes(payload),
    }))
    if receipt["status"] != "PASS":
        raise SystemExit("independent verification failed: " + ";".join(receipt["failures"]))


if __name__ == "__main__":
    main()
