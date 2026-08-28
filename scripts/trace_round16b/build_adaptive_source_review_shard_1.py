#!/usr/bin/env python3
"""Build deterministic Round 16B adaptive-source-review shard 1.

This builder freezes nine completed source audits and the forty exact search
queries that led to them.  Search results remain discovery records rather than
association evidence.  Source-level evidence dispositions are separated from
governed association activation: the Sweden-in-Sydney four-node structure and
the Hutton article-method structure reference tranche C's two canonical
INQUIRY_ONLY identities, while every activation, product, and projection count
remains zero.

No copyrighted source payload is retained by this builder.
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
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
RESEARCH = REPO / "docs/research/trace-v49-exploration-higher-order-association-closure-round16b"

AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORIZED_SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
EVIDENCE_AUTHORITY_BASE_SHA = "f97d20b37b58a509d04cdf3bc3385486fc8d173c"
SHARD_ID = "R16B-ADAPTIVE-SOURCE-SHARD-001"
BUILDER_VERSION = "trace-round16b-adaptive-source-review-shard-1-v1"
UNCAPTURED_TIMESTAMP = "TIMESTAMP_NOT_CAPTURED_ROOT_WEB_TOOL"
TRANCHE_C_IDENTITY_AUTHORITY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-higher-order-review-queue-tranche-c-v1.tsv"
CANONICAL_INQUIRY_IDENTITIES = {
    "COMP-SRC-025": {
        "scope_key": "SWEDEN_IN_SYDNEY_1954",
        "queue_ref": "TCQ-003",
        "association_id": "R16B-ASSOC:4dcabb459b575457929aa565dc7579f43c0e78167fe466f0d0bd777835c19742",
        "revision_id": "R16B-ASSOC-REV:d22c9c9aae73bfcf3609e48a226c054aaad13dea9e477a3388224851beb35689",
    },
    "COMP-SRC-020": {
        "scope_key": "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013",
        "queue_ref": "TCQ-006",
        "association_id": "R16B-ASSOC:b2d7f71d946768a35ee4de75b912d325fbf778f950c9679ef32696596794933a",
        "revision_id": "R16B-ASSOC-REV:f6104d746a20cfb56943be568b578f3efc1add4dcd54647d3b3021f30381c46a",
    },
}

COMPOSITION_SOURCE_PATH = "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv"
COMPOSITION_EVIDENCE_PATH = "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv"
VOCAB_GAP_EVIDENCE_PATH = "docs/research/trace-v49-exploration-composition-review-round1/06_VOCABULARY_GAP_EVIDENCE.tsv"
ROUND16_SOURCE_PATH = "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv"
GRAMMAR_SOURCE_PATH = "docs/research/trace-v49-design-history-relation-grammar-round1/03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv"
GRAMMAR_ATTESTATION_PATH = "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv"
CROSSWALK_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/concept-sense-crosswalk-v1.tsv"
TRANCHE_B_FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-b-v1.tsv"
TRANCHE_B_QUEUE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/conditional-scoped-child-reroute-queue-tranche-b-v1.tsv"
TRANCHE_B_RECEIPT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-b-v1.json"
LOCAL_FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-family-ledger-v2.tsv"
RIGHTS_POLICY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scholarly-source-rights-policy.json"

PINNED_INPUT_SHA256 = {
    COMPOSITION_SOURCE_PATH: "1f54c0956ca12dfaad472a6644c6102ee13b2e9a46f6c1794e21e1a2d7097dca",
    COMPOSITION_EVIDENCE_PATH: "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    VOCAB_GAP_EVIDENCE_PATH: "a38600ead90276d12b97a394443a93cefab1009ea7b391c36aa8d141fcee1051",
    ROUND16_SOURCE_PATH: "473eb44a3b43d3f63261076b13c05e09a1e8b2abb10de8cf73765b0aea597752",
    GRAMMAR_SOURCE_PATH: "9db7d8eaf85b1e104b40cc9412dca274a20b0c5b5715941ec6f234f46c21bd3d",
    GRAMMAR_ATTESTATION_PATH: "62b56052829d23cd2cf820a232479f74cbf663d64465cdc242900e71220df2a8",
    CROSSWALK_PATH: "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    TRANCHE_B_FAMILY_PATH: "1f6547e799963d14c45335569aaa9a5facf9eb1715afe6c462605acdae16a090",
    TRANCHE_B_QUEUE_PATH: "302394dab22ebc85800ac1555db633e3282f83c552026deacec32665ea16389d",
    TRANCHE_B_RECEIPT_PATH: "143266126e7ec3e06158b56647e91c416ed896fb6ebb067656f88db74d7c952f",
    LOCAL_FAMILY_PATH: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    RIGHTS_POLICY_PATH: "b68037dff860421a4f413767a38ca07998cc9f215c75780f1e0019f32bf396ba",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(relative: str) -> str:
    return sha256_bytes((REPO / relative).read_bytes())


def finalize_row(row: dict[str, Any]) -> dict[str, str]:
    scalar = {key: "" if value is None else str(value) for key, value in row.items()}
    scalar["record_sha256"] = sha256_text(canonical_json(scalar))
    return scalar


def tsv_bytes(fields: list[str], rows: Iterable[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def normalize_query(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}:{sha256_text(canonical_json(payload))}"


SOURCE_SPECS: list[dict[str, Any]] = [
    {
        "source_id": "COMP-SRC-001",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "21(1)",
        "pages": "1–18",
        "online_publication_date_or_year": "",
        "record_urls": [
            "https://academic.oup.com/jdh/article/21/1/1/361205",
            "https://uhra.herts.ac.uk/id/eprint/2629/",
        ],
        "text_urls": ["https://uhra.herts.ac.uk/id/eprint/2629/1/905698.pdf"],
        "access_status": "PUBLIC_ACCEPTED_MANUSCRIPT_REVIEWED",
        "text_status": "ACCEPTED_MANUSCRIPT_MULTI_LOCUS_REVIEWED",
        "rights_status": "ALL_RIGHTS_RESERVED_LINK_AND_BOUNDED_NOTES_ONLY",
        "license": "© Author 2008 / Oxford University Press / Design History Society; all rights reserved",
        "license_url": "",
        "third_party": "NOT_APPLICABLE",
        "locators": ["accepted manuscript p.9", "accepted manuscript pp.3, 9, 14, 17"],
        "paraphrase": "Within Western interior design from 1870–1970, professionalization is discussed through formal education, associations, accreditation, and occupational trust or reputation mechanisms.",
        "support_boundary": "A documented multi-locus synthesis can support an inactive scoped interior-design hypothesis joining professionalization, institutional structures, and formal design education.",
        "support_mode": "COHERENT_SINGLE_SOURCE_MULTI_LOCUS_SYNTHESIS",
        "scope": "Western interior design, 1870–1970; named education, association, accreditation, and occupational-trust mechanisms",
        "conflicts": ["professional standing is contested", "accreditation and gatekeeping may exclude", "informal education must remain visible"],
        "nonclaims": ["not generic or all-period", "education is not asserted as a cause", "no direction, chronology, hierarchy, or pair relation is manufactured"],
        "parent_key": "15f5757830dfe043fb27e73c28ff3bfd902aaa9c938ab254fda8682d359a7249",
        "parent_disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "child_action": "REVIEW_INACTIVE_SCOPED_INTERIOR_DESIGN_HYPEREDGE",
        "evidence_disposition": "COHERENT_COMPOSITE_SUPPORT_SCOPE_BOUNDED_HUMAN_REVIEW_OPEN",
    },
    {
        "source_id": "COMP-SRC-013",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "25(3)",
        "pages": "",
        "online_publication_date_or_year": "2021",
        "record_urls": [
            "https://www.tandfonline.com/doi/full/10.1080/13264826.2021.1939745",
            "https://www.research-collection.ethz.ch/entities/publication/18f5155c-0387-40c7-8b6f-eeefe48e4bf0",
        ],
        "text_urls": ["https://www.research-collection.ethz.ch/server/api/core/bitstreams/010acf32-6fdb-45ea-8684-48e1dfec95da/content"],
        "access_status": "PUBLIC_PUBLISHED_FULL_TEXT_REVIEWED",
        "text_status": "PUBLISHED_TEXT_LOCATOR_REVIEWED",
        "rights_status": "CC_BY_NC_ND_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY-NC-ND 4.0",
        "license_url": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
        "third_party": "LICENSE_APPLIES_SUBJECT_TO_SOURCE_MARKINGS",
        "locators": ["printed p.354, Contact Zone section"],
        "paraphrase": "The architectural-contact-zone concept joins situated negotiation, selective borrowing or adaptation, and rejection under unequal participation conditions.",
        "support_boundary": "Direct conceptual support exists for an inactive adaptation/contact-zone-negotiation/rejection child only after a new source-specific negotiation sense is governed.",
        "support_mode": "DIRECT_HIGHER_ORDER_SUPPORT_NEW_SENSE_REQUIRED",
        "scope": "architectural contact zones; specific encounters, actors, and unequal power relations",
        "conflicts": ["the current cultural-negotiation sense is Keraton-bounded", "power asymmetry blocks a voluntary or equal-participation reading"],
        "nonclaims": ["alternatives are not successive stages", "no general topology, direction, or pair projection", "does not support the canonical Keraton-bounded sense"],
        "parent_key": "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e",
        "parent_disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "child_action": "CREATE_AND_GOVERN_CONTACT_ZONE_NEGOTIATION_SENSE_BEFORE_CHILD_REVIEW",
        "evidence_disposition": "DIRECT_HIGHER_ORDER_SUPPORT_NEW_SENSE_AND_HUMAN_REVIEW_OPEN",
    },
    {
        "source_id": "COMP-SRC-014",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "12(1)",
        "pages": "",
        "online_publication_date_or_year": "2025",
        "record_urls": ["https://doi.org/10.1080/23311983.2025.2482456"],
        "text_urls": [
            "https://www.tandfonline.com/doi/full/10.1080/23311983.2025.2482456",
            "https://www.tandfonline.com/doi/pdf/10.1080/23311983.2025.2482456",
        ],
        "access_status": "OPEN_ACCESS_PUBLISHED_FULL_TEXT_REVIEWED",
        "text_status": "PUBLISHED_TEXT_MULTI_SECTION_REVIEWED",
        "rights_status": "CC_BY_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY 4.0; © authors",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "third_party": "LICENSE_APPLIES_SUBJECT_TO_SOURCE_MARKINGS",
        "locators": ["abstract", "Cultural hybridity section", "Aesthetic adaptation section", "conclusion"],
        "paraphrase": "The Keraton Surakarta case binds selective adaptation and cultural negotiation with symbolic or cultural resistance under colonial power asymmetry.",
        "support_boundary": "The reviewed source supports the bounded Keraton adaptation/cultural-negotiation pair and resistance as case context; it does not supply rejection as a participant.",
        "support_mode": "DIRECT_SCOPED_PAIR_SUPPORT_CONTEXT_QUALIFIED",
        "scope": "Keraton Surakarta; Javanese patrons and design actors; colonial institutions and unequal power",
        "conflicts": ["collaboration, coercion, and ambivalence coexist", "the contact-zone rejection participant is absent"],
        "nonclaims": ["no generalization beyond the Keraton case", "no direction or pair projection from a larger group", "resistance is not converted into a new governed vocabulary node here"],
        "parent_key": "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e",
        "parent_disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "child_action": "REROUTE_TO_BOUNDED_KERATON_ADAPTATION_CULTURAL_NEGOTIATION_PAIR",
        "evidence_disposition": "DIRECT_SCOPED_PAIR_SUPPORT_NO_REJECTION_PARTICIPANT",
    },
    {
        "source_id": "COMP-SRC-023",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "9(2)",
        "pages": "123–145",
        "citation_title": "Cold War Cultural Transactions: Designing the USSR for the West at Brussels Expo ’58",
        "online_publication_date_or_year": "2017",
        "record_urls": [
            "https://www.tandfonline.com/doi/full/10.1080/17547075.2017.1333388",
            "https://durham-repository.worktribe.com/output/1310178/cold-war-cultural-transactions-designing-the-ussr-for-the-west-at-brussels-expo-58",
        ],
        "text_urls": [],
        "access_status": "PUBLIC_ABSTRACT_REVIEWED_FULL_TEXT_NOT_ESTABLISHED",
        "text_status": "PUBLISHER_ABSTRACT_AND_PRINTED_PAGE_REFERENCE_REVIEWED_FULL_TEXT_OPEN",
        "rights_status": "LICENSE_UNVERIFIED_REDISTRIBUTION_NOT_AUTHORIZED",
        "license": "LICENSE_NOT_VERIFIED",
        "license_url": "",
        "third_party": "UNKNOWN",
        "locators": ["publisher abstract", "printed p.123 reference"],
        "paraphrase": "The Brussels Expo 1958 source frames the designed modern-USSR image through design diplomacy, persuasion, negotiation, compromise, and transculturation.",
        "support_boundary": "The review supports a Brussels-specific exhibition/design-diplomacy pair and context; it does not establish the exact exhibition/propaganda/design-diplomacy triad.",
        "support_mode": "ABSTRACT_BEARING_SCOPED_PAIR_SUPPORT_FULL_TEXT_GROUP_GAP",
        "scope": "Brussels Expo 1958; Soviet exhibition organizers, designers, and Western audiences",
        "conflicts": ["propaganda participation remains unresolved", "full-text lawful review is not established", "audience reception and effect are not proved"],
        "nonclaims": ["design diplomacy is not equivalent to propaganda", "do not mix Brussels, Turin, and Sweden cases", "no triad or reception claim"],
        "parent_key": "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1",
        "parent_disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "child_action": "REROUTE_TO_BRUSSELS_PAIR_AND_QUEUE_FULL_TEXT_PROPAGANDA_REVIEW",
        "evidence_disposition": "PAIR_SUPPORT_ONLY_EXACT_TRIAD_NOT_SUPPORTED",
    },
    {
        "source_id": "COMP-SRC-024",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "33(1)",
        "pages": "173–191",
        "online_publication_date_or_year": "2022",
        "record_urls": ["https://www.cambridge.org/core/journals/contemporary-european-history/article/socialist-humanist-and-welldesigned-the-polish-welfare-state-at-the-international-labour-exhibition-in-turin-1961/94D125A40C5B3B013872B9A949430909"],
        "text_urls": ["https://www.cambridge.org/core/services/aop-cambridge-core/content/view/94D125A40C5B3B013872B9A949430909/S0960777322000029a.pdf/socialist_humanist_and_welldesigned_the_polish_welfare_state_at_the_international_labour_exhibition_in_turin_1961.pdf"],
        "access_status": "OPEN_ACCESS_PUBLISHED_PDF_REVIEWED",
        "text_status": "PUBLISHED_TEXT_MULTI_LOCUS_REVIEWED",
        "rights_status": "CC_BY_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "third_party": "LICENSE_APPLIES_SUBJECT_TO_SOURCE_MARKINGS",
        "locators": ["pp.173–175, abstract/introduction/Design Diplomacy", "p.190"],
        "paraphrase": "The Turin 1961 International Labour Exhibition presents Polish welfare-state design through exhibition, propaganda, and design diplomacy in one bounded case.",
        "support_boundary": "The exact Turin exhibition/propaganda/design-diplomacy triad has direct same-case source support as an inactive hypothesis.",
        "support_mode": "DIRECT_HIGHER_ORDER_SUPPORT_SAME_CASE",
        "scope": "International Labour Exhibition, Turin, 1961; Polish welfare-state display and diplomatic narrative",
        "conflicts": ["archival evidence is scarce", "the presentation was inaccessible to many working-class visitors", "the official narrative concealed ambivalence"],
        "nonclaims": ["no cross-case or general equivalence", "no audience success or reception outcome", "no pair projection"],
        "parent_key": "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1",
        "parent_disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "child_action": "REVIEW_INACTIVE_TURIN_1961_DIRECT_TRIAD",
        "evidence_disposition": "DIRECT_HIGHER_ORDER_SUPPORT_HUMAN_REVIEW_OPEN",
    },
    {
        "source_id": "R16-SRC-005",
        "registry_path": ROUND16_SOURCE_PATH,
        "source_family": "ROUND16_VOCABULARY_SOURCE",
        "volume_issue": "33",
        "pages": "261–279",
        "citation_title": "Insights from Bauhaus innovation for education and workplaces in a post-pandemic world",
        "online_publication_date_or_year": "2022",
        "record_urls": ["https://doi.org/10.1007/s10798-022-09729-2"],
        "text_urls": ["https://link.springer.com/article/10.1007/s10798-022-09729-2"],
        "access_status": "OPEN_ACCESS_PUBLISHED_FULL_TEXT_REVIEWED",
        "text_status": "PUBLISHED_TEXT_MULTI_SECTION_REVIEWED",
        "rights_status": "CC_BY_4_0_WITH_THIRD_PARTY_EXCEPTIONS",
        "license": "CC BY 4.0 with third-party material exceptions",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "third_party": "THIRD_PARTY_MATERIAL_REQUIRES_ITEM_LEVEL_CHECK",
        "locators": ["abstract", "Dimensions of innovation", "Learning in authentic workplace settings", "Bauhaus influence"],
        "paraphrase": "The article supports a bounded craft and Bauhaus design-education configuration through arts-crafts integration and authentic workplace learning.",
        "support_boundary": "Craft and design education may be reviewed as a bounded child, but education and design education are nested labels here rather than proved distinct roles in a triad.",
        "support_mode": "DIRECT_SCOPED_PAIR_SUPPORT_IDENTITY_RECONCILIATION_REQUIRED",
        "scope": "Bauhaus arts-crafts integration, design education, and post-pandemic workplace-learning comparison",
        "conflicts": ["education and design education may be duplicate or specialization senses", "third-party content exceptions require item-level rights review"],
        "nonclaims": ["not a harmonious or universal Bauhaus model", "no equivalence or causal sequence", "no three-role group, product path, or pair projection"],
        "parent_key": "7696ac77a3bd8ac70e8e0181b3ae969502426a44200925dffb65ef88312e954a",
        "parent_disposition": "COOCCURRENCE_ONLY",
        "child_action": "REVIEW_CRAFT_DESIGN_EDUCATION_PAIR_AND_RESOLVE_EDUCATION_IDENTITY",
        "evidence_disposition": "DIRECT_SCOPED_PAIR_SUPPORT_TRIAD_IDENTITY_CONFLICT",
    },
    {
        "source_id": "GRAM-SRC-025",
        "registry_path": GRAMMAR_SOURCE_PATH,
        "source_family": "GRAMMAR_ATTESTATION_SOURCE",
        "volume_issue": "41(6)",
        "pages": "735–741",
        "citation_title": "Advancing a ‘new professionalism’: professionalization, practice and institutionalization",
        "online_publication_date_or_year": "2013",
        "record_urls": [
            "https://www.tandfonline.com/doi/full/10.1080/09613218.2013.843269",
            "https://research.manchester.ac.uk/en/publications/advancing-a-new-professionalism-professionalisation-practice-and-/",
        ],
        "text_urls": ["https://www.tandfonline.com/doi/pdf/10.1080/09613218.2013.843269"],
        "access_status": "PUBLISHER_FREE_ACCESS_FULL_TEXT_REVIEWED",
        "text_status": "PUBLISHED_TEXT_LOCATOR_REVIEWED",
        "rights_status": "FREE_ACCESS_NO_CC_REDISTRIBUTION_NOT_AUTHORIZED",
        "license": "Publisher Free Access; no Creative Commons license identified",
        "license_url": "",
        "third_party": "UNKNOWN",
        "locators": ["p.737", "end of Changing the system section before A neo-institutional perspective?"],
        "paraphrase": "In built-environment professionalism, the source links professionalization with institutionalization across professional work, education, and training while emphasizing fluidity and contested practice.",
        "support_boundary": "A built-environment child can be reviewed only with a new professional-education/training sense; the canonical Bauhaus education sense cannot be substituted.",
        "support_mode": "DIRECT_LOCAL_HIGHER_ORDER_ATTESTATION_NEW_SENSE_REQUIRED",
        "scope": "built-environment professional work, education, and training; source-scoped interweaving",
        "conflicts": ["professionalization is fluid and contested", "unintended consequences remain possible", "the source is not sufficient design-history authority for a generic active relation"],
        "nonclaims": ["not the canonical Bauhaus education sense", "no universal sequence, chronology, or direction", "no pair projection"],
        "parent_key": "d6dfcd4e355294899be8838eb8ec71439d8911ea19f8aa92401d1a52becf76c0",
        "parent_disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "child_action": "CREATE_PROFESSIONAL_EDUCATION_TRAINING_SENSE_BEFORE_CHILD_REVIEW",
        "evidence_disposition": "DIRECT_LOCAL_ATTESTATION_NEW_SENSE_AND_HUMAN_REVIEW_OPEN",
    },
    {
        "source_id": "COMP-SRC-025",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "33(2)",
        "pages": "279–305",
        "citation_title": "A Fleeting Glimpse? ‘Sweden’s Shop Window in Sydney’ — the Sweden at David Jones’ Exposition of 1954",
        "online_publication_date_or_year": "2023-12-08",
        "record_urls": [
            "https://doi.org/10.1080/10331867.2023.2282294",
            "https://www.tandfonline.com/doi/abs/10.1080/10331867.2023.2282294",
        ],
        "text_urls": ["https://www.tandfonline.com/doi/pdf/10.1080/10331867.2023.2282294"],
        "access_status": "OPEN_ACCESS_PUBLISHED_PDF_REVIEWED",
        "text_status": "PUBLISHED_TEXT_EXACT_GROUP_LOCATOR_REVIEWED",
        "rights_status": "CC_BY_4_0_LINK_AND_BOUNDED_NOTES",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "third_party": "LICENSE_APPLIES_SUBJECT_TO_SOURCE_MARKINGS",
        "locators": ["p.282"],
        "paraphrase": "The 1954 Sweden-at-David-Jones exposition is analyzed through cultural and design diplomacy, cultural transfer through trade, propaganda and goodwill, and its origin as a trade fair seeking Swedish goods and goodwill.",
        "support_boundary": "The exact current bounded senses exhibition, trade, propaganda, and design diplomacy are directly supported together in the same Sweden-in-Sydney case.",
        "support_mode": "DIRECT_HIGHER_ORDER_SUPPORT_SAME_CASE_EXACT_ARITY4",
        "scope": "Sweden at David Jones, Sydney, 1954; retail exposition, state and exhibition intermediaries, Australian publics and commercial counterparts",
        "conflicts": ["propaganda and diplomacy remain distinct concepts", "goodwill and intended representation do not establish reception or diplomatic effect"],
        "nonclaims": ["no audience acceptance, diplomatic outcome, or general law", "no internal pair or subset projection", "the identity remains inquiry-only pending external human review"],
        "parent_key": "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a",
        "parent_disposition": "INQUIRY_ONLY_OR_UNRESOLVED_AT_CHECKPOINT004",
        "child_action": "CREATE_GOVERNED_INQUIRY_ONLY_EXACT_ARITY4_IDENTITY_NO_PROJECTION",
        "evidence_disposition": "DIRECT_HIGHER_ORDER_SUPPORT_EXACT_CURRENT_SENSES",
    },
    {
        "source_id": "COMP-SRC-020",
        "registry_path": COMPOSITION_SOURCE_PATH,
        "source_family": "COMPOSITION_REVIEW_SOURCE",
        "volume_issue": "8(1)",
        "pages": "40–47",
        "citation_title": "Reciprocal landscapes: material portraits in New York City and elsewhere",
        "online_publication_date_or_year": "2013-05-24",
        "record_urls": ["https://www.tandfonline.com/doi/abs/10.1080/18626033.2013.798922"],
        "text_urls": ["https://thelandscapedotorg.files.wordpress.com/2021/05/2013_hutton_reciprocal_landscapes_jola.pdf"],
        "access_status": "PUBLIC_AUTHOR_PDF_LAWFUL_READ_OBSERVED",
        "text_status": "AUTHOR_PDF_ARTICLE_METHOD_AND_CASE_STRUCTURE_REVIEWED",
        "rights_status": "READ_ACCESS_OBSERVED_REDISTRIBUTION_LICENSE_UNKNOWN_NOT_AUTHORIZED",
        "license": "Redistribution license unknown",
        "license_url": "",
        "third_party": "UNKNOWN",
        "locators": ["p.40 abstract", "p.41"],
        "paraphrase": "The article relates sites and people of material production, landscapes of production and consumption, material displacement, commodity chains, production sites, multiple actors, and three named material-movement cases.",
        "support_boundary": "The article offers an article-method-level sparse-association hypothesis, but the exact five-member current-sense group is blocked by production/consumption sense conflicts and by three separate cases rather than one case.",
        "support_mode": "ARTICLE_METHOD_LEVEL_SPARSE_HYPEREDGE_EXACT_ARITY5_BLOCKED",
        "scope": "article-method level across three distinct material-movement cases; any case child must be separately bounded",
        "conflicts": ["current production and consumption senses are mediation-focused rather than generic material production/consumption", "three cases cannot be silently merged", "the exact family has four of ten active pairs and disconnected pair components"],
        "nonclaims": ["not one exact five-member single-case association", "no unrelated pair-source synthesis", "no pair projection, product activation, or redistribution of the PDF"],
        "parent_key": "d936154cb902968e2e5e0404e3dffaa3b61b47480b69f600b766b96351b66148",
        "parent_disposition": "INQUIRY_ONLY_OR_UNRESOLVED_AT_CHECKPOINT004",
        "child_action": "KEEP_EXACT_ARITY5_INQUIRY_ONLY_REVIEW_NEW_SENSES_OR_CASE_CHILDREN",
        "evidence_disposition": "METHOD_LEVEL_RESEARCH_VALUE_EXACT_CURRENT_SENSE_GROUP_CONFLICT",
    },
]


QUERY_BATCHES: list[dict[str, Any]] = [
    {"timestamp": "2026-08-28T08:05:01Z", "purpose": "SOURCE_TEXT_DISCOVERY", "queries": [
        ("\"Introduction: Professionalization as a Focus in Interior Design History\" accepted manuscript PDF Grace Lees-Maffei", "COMP-SRC-001"),
        ("\"Architectural Contact Zones\" Avermaete Nuijsink PDF", "COMP-SRC-013"),
        ("\"Symbolic and Aesthetic Fusion in Keraton Surakarta\" PDF", "COMP-SRC-014"),
        ("\"Cold War Cultural Transactions\" Susan E. Reid PDF", "COMP-SRC-023"),
    ]},
    {"timestamp": "2026-08-28T08:05:11Z", "purpose": "SOURCE_TEXT_DISCOVERY", "queries": [
        ("\"Socialist, Humanist and Well-Designed\" Turin 1961 PDF Jeżowska", "COMP-SRC-024"),
        ("\"Insights from Bauhaus innovation for education and workplaces\" PDF", "R16-SRC-005"),
        ("\"Advancing a new professionalism\" Bresnen PDF institutional repository", "GRAM-SRC-025"),
        ("\"Cold War Cultural Transactions\" \"Brussels Expo\" Reid repository PDF", "COMP-SRC-023"),
    ]},
    {"timestamp": "2026-08-28T08:06:20Z", "purpose": "EXACT_CONCEPT_AND_LOCATOR_FOLLOWUP", "queries": [
        ("\"Architectural Contact Zones\" \"adaptation\" \"rejection\"", "COMP-SRC-013"),
        ("\"Architectural Contact Zones\" \"selective borrowing\"", "COMP-SRC-013"),
        ("\"Architectural Contact Zones\" negotiation adaptation rejection p. 354", "COMP-SRC-013"),
        ("site:research-collection.ethz.ch/server/api/core/bitstreams \"rejection\" \"contact zones\"", "COMP-SRC-013"),
    ]},
    {"timestamp": "2026-08-28T08:06:32Z", "purpose": "GROUP_COHERENCE_AND_BOUNDARY", "queries": [
        ("\"Cold War Cultural Transactions\" \"design diplomacy\" propaganda exhibition", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"counter-propaganda\"", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"negotiation\" \"compromise\" p. 123", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"Soviet Pavilion\" Brussels Expo 58 PDF", "COMP-SRC-023"),
    ]},
    {"timestamp": "2026-08-28T08:06:46Z", "purpose": "PROPAGANDA_FALSIFICATION", "queries": [
        ("\"10.1080/17547075.2017.1333388\" propaganda", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" propaganda USSR pavilion", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" \"mass exhibitions\" propaganda", "COMP-SRC-023"),
        ("\"Cold War Cultural Transactions\" persuasion propaganda \"Expo 58\"", "COMP-SRC-023"),
    ]},
    {"timestamp": "2026-08-28T08:07:25Z", "purpose": "PROFESSIONAL_EDUCATION_MECHANISM", "queries": [
        ("\"Advancing a new professionalism\" \"education and training\" institutionalization", "GRAM-SRC-025"),
        ("\"Advancing a ‘new professionalism’\" professionalization institutionalization education training", "GRAM-SRC-025"),
        ("\"Advancing a new professionalism\" \"institutional work\" education", "GRAM-SRC-025"),
        ("\"10.1080/09613218.2013.843269\" \"education\"", "GRAM-SRC-025"),
    ]},
    {"timestamp": "2026-08-28T08:07:40Z", "purpose": "RIGHTS_AND_LICENSE", "queries": [
        ("\"Advancing a new professionalism\" \"© 2013\" Bresnen", "GRAM-SRC-025"),
        ("\"10.1080/09613218.2013.843269\" license", "GRAM-SRC-025"),
        ("site:tandfonline.com/doi/full/10.1080/09613218.2013.843269 \"Copyright\"", "GRAM-SRC-025"),
        ("site:tandfonline.com/doi/full/10.1080/17547075.2017.1333388 \"Copyright\"", "COMP-SRC-023"),
    ]},
    {"timestamp": "2026-08-28T08:09:45Z", "purpose": "COUNTEREVIDENCE_AND_LIMITATION", "queries": [
        ("\"Introduction: Professionalization as a Focus in Interior Design History\" education institutionalization limitations", "COMP-SRC-001"),
        ("\"Architectural Contact Zones\" asymmetry adaptation rejection limitations", "COMP-SRC-013"),
        ("\"Keraton Surakarta\" adaptation negotiation resistance collaboration Dutch colonial rejection", "COMP-SRC-014"),
        ("\"Cold War Cultural Transactions\" propaganda reception compromise limitations", "COMP-SRC-023"),
    ]},
    {"timestamp": "2026-08-28T08:10:00Z", "purpose": "COUNTEREVIDENCE_AND_LIMITATION", "queries": [
        ("\"Socialist, Humanist and Well-Designed\" propaganda design diplomacy archival scarce reception", "COMP-SRC-024"),
        ("\"Insights from Bauhaus innovation\" craft industrial focus challenged identities", "R16-SRC-005"),
        ("\"Advancing a new professionalism\" unintended consequences education training institutionalization", "GRAM-SRC-025"),
        ("\"Bauhaus innovation\" design education craft limitations workplace learning", "R16-SRC-005"),
    ]},
    {"timestamp": UNCAPTURED_TIMESTAMP, "purpose": "ROOT_SOURCE_CENTERED_DISCOVERY", "queries": [
        ("site:tandfonline.com/doi/full/10.1080/10331867.2023.2282294 Sweden David Jones exposition trade propaganda design diplomacy", "COMP-SRC-025"),
        ("site:tandfonline.com/doi/abs/10.1080/18626033.2013.798922 reciprocal landscapes material portraits production consumption commodity chains", "COMP-SRC-020"),
        ("site:cambridge.org design diplomacy Turin 1961 international labour exhibition propaganda", "COMP-SRC-024"),
        ("site:tandfonline.com 10.1080/13264826.2021.1939745 contact zone adaptation rejection architecture", "COMP-SRC-013"),
    ]},
]


HYPOTHESIS_SPECS = [
    ("COMP-SRC-001", "FORMAL_DESIGN_EDUCATION_1870_1970", ["institutionalization", "design education", "professionalization"], "INCIDENCE_HYPEREDGE_REVIEW", "COHERENT_COMPOSITE_SUPPORT", "CURRENT_SENSE_SCOPE_REVIEW_OPEN"),
    ("COMP-SRC-013", "ARCHITECTURAL_CONTACT_ZONE", ["adaptation", "contact-zone negotiation NEW", "rejection"], "INCIDENCE_HYPEREDGE_REVIEW", "DIRECT_HIGHER_ORDER_SUPPORT", "NEW_NEGOTIATION_SENSE_REQUIRED"),
    ("COMP-SRC-014", "KERATON_SURAKARTA", ["adaptation", "cultural negotiation"], "PAIR_SCOPE_REROUTE", "DIRECT_SCOPED_PAIR_SUPPORT", "CURRENT_SENSES_BOUNDED"),
    ("COMP-SRC-023", "BRUSSELS_EXPO_1958", ["exhibition", "design diplomacy"], "PAIR_SCOPE_REROUTE", "ABSTRACT_BEARING_SCOPED_PAIR_SUPPORT", "PROPAGANDA_PARTICIPANT_UNRESOLVED"),
    ("COMP-SRC-024", "TURIN_INTERNATIONAL_LABOUR_EXHIBITION_1961", ["exhibition", "propaganda", "design diplomacy"], "INCIDENCE_HYPEREDGE_REVIEW", "DIRECT_HIGHER_ORDER_SUPPORT", "CURRENT_SENSES_BOUNDED"),
    ("R16-SRC-005", "BAUHAUS_CRAFT_DESIGN_EDUCATION", ["craft", "design education"], "PAIR_SCOPE_AND_IDENTITY_REVIEW", "DIRECT_SCOPED_PAIR_SUPPORT", "EDUCATION_DESIGN_EDUCATION_IDENTITY_OPEN"),
    ("GRAM-SRC-025", "PROFESSIONAL_EDUCATION_TRAINING_SENSE", ["institutionalization", "professional education or training NEW", "professionalization"], "INCIDENCE_HYPEREDGE_REVIEW", "DIRECT_LOCAL_ATTESTATION", "NEW_PROFESSIONAL_EDUCATION_SENSE_REQUIRED"),
    ("COMP-SRC-025", "SWEDEN_IN_SYDNEY_1954", ["exhibition", "trade", "propaganda", "design diplomacy"], "GOVERNED_INQUIRY_HYPEREDGE", "DIRECT_HIGHER_ORDER_SUPPORT", "CURRENT_SENSES_BOUNDED"),
    ("COMP-SRC-020", "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013", ["consumption", "production site", "production", "material displacement", "supply chain"], "SPARSE_HYPEREDGE_OR_CASE_SPLIT_REVIEW", "METHOD_LEVEL_RESEARCH_VALUE_EXACT_GROUP_BLOCKED", "PRODUCTION_CONSUMPTION_SENSE_AND_CASE_CONFLICT"),
]


SOURCE_REVIEW_FIELDS = [
    "evidence_authority_base_sha", "shard_id", "source_review_id", "source_id", "source_family",
    "authors", "year", "title", "local_registry_title", "publication", "volume_issue", "pages",
    "online_publication_date_or_year", "publisher", "doi",
    "bibliographic_record_urls_json", "reviewed_text_urls_json", "exact_query_ids_json",
    "query_timestamp_status", "access_status", "source_text_review_status", "rights_status",
    "license_expression", "license_url", "third_party_exception_status", "retained_payload_status",
    "retained_payload_sha256", "locators_json", "bounded_paraphrase", "direct_support_boundary",
    "support_mode", "bounded_scope", "conflicts_or_counterevidence_json", "nonclaims_json",
    "linked_parent_candidate_id", "parent_disposition_preserved", "child_or_reroute_action",
    "identity_status", "evidence_disposition", "human_review_status", "product_eligibility",
    "pair_projection_count", "association_activation", "active_fact_created", "record_sha256",
]

QUERY_FIELDS = [
    "evidence_authority_base_sha", "shard_id", "batch_id", "batch_timestamp_utc",
    "timestamp_capture_status", "query_ordinal", "query_id", "service", "purpose",
    "exact_query_text", "normalized_query_text", "parameters_json", "target_source_id",
    "result_identity_json", "stable_locators_json", "access_condition", "query_decision",
    "evidence_use", "rejection_reason", "record_sha256",
]

RIGHTS_FIELDS = [
    "evidence_authority_base_sha", "shard_id", "rights_record_id", "source_id", "doi",
    "record_urls_json", "text_urls_json", "access_status", "source_text_review_status",
    "rights_status", "license_expression", "license_url", "third_party_exception_status",
    "payload_retained", "payload_sha256", "retention_decision", "redistribution_authorized",
    "committed_material", "record_sha256",
]

HYPOTHESIS_FIELDS = [
    "evidence_authority_base_sha", "shard_id", "hypothesis_id", "governed_association_id",
    "governed_association_revision_id", "canonical_identity_authority_path", "canonical_identity_queue_ref",
    "source_ids_json", "linked_parent_candidate_id", "parent_disposition_preserved", "scope_key",
    "scope_note", "participant_labels_json", "participant_sense_ids_json", "arity",
    "participant_order_meaningful", "relation_roles_asserted", "relation_form", "support_mode",
    "exact_group_support_status", "global_coherence_status", "sense_scope_status",
    "evidence_disposition", "governed_identity_status", "external_human_review_status",
    "association_activation_status", "active_fact_created", "product_eligibility",
    "pair_projection_count", "subset_projection_count", "nonclaims_json", "record_sha256",
]

GAP_FIELDS = [
    "evidence_authority_base_sha", "shard_id", "gap_id", "gap_class", "severity", "status",
    "affected_source_ids_json", "gap", "evidence", "required_next_action", "closure_effect",
    "record_sha256",
]


def registry_identity_map() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for path in (COMPOSITION_SOURCE_PATH, ROUND16_SOURCE_PATH, GRAMMAR_SOURCE_PATH):
        for row in read_tsv(path):
            source_id = row["source_id"]
            if source_id not in {spec["source_id"] for spec in SOURCE_SPECS}:
                continue
            if path == GRAMMAR_SOURCE_PATH:
                publication = row["publication"]
                doi = row["doi_isbn"]
                stable_url = row["stable_publisher_url"]
            else:
                publication = row["venue"]
                doi = row["doi_or_identifier"]
                stable_url = row["stable_url"]
            result[source_id] = {
                "authors": row["authors"],
                "year": row["year"],
                "title": row["title"],
                "publication": publication,
                "publisher": row["publisher"],
                "doi": doi,
                "registry_stable_url": stable_url,
                "registry_path": path,
            }
    expected = {spec["source_id"] for spec in SOURCE_SPECS}
    if set(result) != expected:
        raise ValueError(f"source registry coverage mismatch: expected={sorted(expected)} actual={sorted(result)}")
    return result


def sense_map() -> dict[str, str]:
    rows = read_tsv(CROSSWALK_PATH)
    by_label: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_label[row["canonical_label"]].append(row["participant_sense_id"])
    result: dict[str, str] = {}
    used_current_labels = {
        label
        for _, _, labels, _, _, _ in HYPOTHESIS_SPECS
        for label in labels
        if not label.endswith(" NEW")
    }
    for label in sorted(used_current_labels):
        ids = sorted(set(by_label[label]))
        if len(ids) != 1:
            raise ValueError(f"canonical sense resolution is not unique for {label!r}: {ids}")
        result[label] = ids[0]
    return result


def build_query_rows(source_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    rows: list[dict[str, str]] = []
    source_query_ids: dict[str, list[str]] = defaultdict(list)
    ordinal = 0
    for batch_ordinal, batch in enumerate(QUERY_BATCHES, 1):
        batch_id = f"R16B-ADAPTIVE-QUERY-BATCH-{batch_ordinal:03d}"
        timestamp = batch["timestamp"]
        for within_batch, (query_text, target_source_id) in enumerate(batch["queries"], 1):
            ordinal += 1
            query_id = stable_id("R16B-ADAPTIVE-QUERY", {
                "timestamp": timestamp,
                "query": query_text,
                "target_source_id": target_source_id,
                "purpose": batch["purpose"],
            })
            source_query_ids[target_source_id].append(query_id)
            source = source_by_id[target_source_id]
            query_decision = {
                "SOURCE_TEXT_DISCOVERY": "LEAD_TO_REVIEWED_RECORD_OR_TEXT_LOCATOR",
                "EXACT_CONCEPT_AND_LOCATOR_FOLLOWUP": "BOUNDARY_AND_LOCATOR_REVIEW_COMPLETED",
                "GROUP_COHERENCE_AND_BOUNDARY": "GROUP_BOUNDARY_REVIEW_COMPLETED_FAIL_CLOSED",
                "PROPAGANDA_FALSIFICATION": "PROPAGANDA_PARTICIPANT_NOT_ESTABLISHED_FOR_BRUSSELS_TRIAD",
                "PROFESSIONAL_EDUCATION_MECHANISM": "NEW_SENSE_REQUIREMENT_IDENTIFIED",
                "RIGHTS_AND_LICENSE": "RIGHTS_CONDITION_RECORDED_FAIL_CLOSED",
                "COUNTEREVIDENCE_AND_LIMITATION": "QUALIFICATIONS_AND_NONCLAIMS_RECORDED",
                "ROOT_SOURCE_CENTERED_DISCOVERY": "SOURCE_CENTERED_REVIEW_COMPLETED_TIMESTAMP_UNCAPTURED",
            }[batch["purpose"]]
            row = finalize_row({
                "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
                "shard_id": SHARD_ID,
                "batch_id": batch_id,
                "batch_timestamp_utc": timestamp,
                "timestamp_capture_status": "NOT_CAPTURED_DO_NOT_INFER" if timestamp == UNCAPTURED_TIMESTAMP else "EXACT_CAPTURED_UTC",
                "query_ordinal": ordinal,
                "query_id": query_id,
                "service": "ROOT_WEB_SEARCH_TOOL",
                "purpose": batch["purpose"],
                "exact_query_text": query_text,
                "normalized_query_text": normalize_query(query_text),
                "parameters_json": canonical_json({"query_text_exact": query_text}),
                "target_source_id": target_source_id,
                "result_identity_json": canonical_json({"source_id": target_source_id, "doi": source["doi"]}),
                "stable_locators_json": canonical_json(sorted(set(source["record_urls"] + source["text_urls"]))),
                "access_condition": source["access_status"],
                "query_decision": query_decision,
                "evidence_use": "DISCOVERY_AND_FALSIFICATION_TRAIL_ONLY_NOT_ASSOCIATION_EVIDENCE",
                "rejection_reason": "Search ranking, snippets, metadata, and query co-occurrence are not association evidence; the separate locator-bearing source review controls the evidence disposition.",
            })
            rows.append(row)
    if len(rows) != 40 or ordinal != 40:
        raise ValueError(f"expected 40 exact queries, got {len(rows)}")
    return rows, source_query_ids


def build_artifacts() -> dict[str, bytes]:
    for relative, expected in PINNED_INPUT_SHA256.items():
        actual = sha256_file(relative)
        if actual != expected:
            raise ValueError(f"pinned input mismatch: {relative}: expected={expected} actual={actual}")

    # Tranche C is a co-produced checkpoint-007 identity authority, not part of
    # the pre-checkpoint evidence-authority base.  Bind its exact bytes and rows
    # so the source shard can never mint a competing source-local identity.
    canonical_identity_authority_sha256 = sha256_file(TRANCHE_C_IDENTITY_AUTHORITY_PATH)
    tranche_c_identity_rows = {
        row["source_ids_json"]: row
        for row in read_tsv(TRANCHE_C_IDENTITY_AUTHORITY_PATH)
        if row["queue_record_kind"] == "SCOPED_INQUIRY_IDENTITY"
    }
    for source_id, canonical in CANONICAL_INQUIRY_IDENTITIES.items():
        key = canonical_json([source_id])
        row = tranche_c_identity_rows.get(key)
        if row is None:
            raise ValueError(f"tranche-C canonical identity missing for {source_id}")
        expected_values = {
            "queue_ref": canonical["queue_ref"],
            "scope_key": canonical["scope_key"],
            "association_id": canonical["association_id"],
            "association_revision_id": canonical["revision_id"],
            "association_identity_created": "true",
            "association_activation_status": "INQUIRY_ONLY",
            "pair_projection_created": "false",
            "subset_projection_created": "false",
            "product_path_created": "false",
            "product_eligibility": "INELIGIBLE",
        }
        for field, expected in expected_values.items():
            if row[field] != expected:
                raise ValueError(
                    f"tranche-C canonical identity mismatch for {source_id} field={field}: "
                    f"expected={expected} actual={row[field]}"
                )

    registry = registry_identity_map()
    senses = sense_map()
    source_by_id: dict[str, dict[str, Any]] = {}
    for spec in SOURCE_SPECS:
        identity = registry[spec["source_id"]]
        if identity["registry_path"] != spec["registry_path"]:
            raise ValueError(f"registry-path mismatch for {spec['source_id']}")
        record_urls = sorted(set(spec["record_urls"] + [identity["registry_stable_url"]]))
        source_by_id[spec["source_id"]] = {
            **spec,
            **identity,
            "local_registry_title": identity["title"],
            "title": spec.get("citation_title", identity["title"]),
            "record_urls": record_urls,
        }

    query_rows, query_ids_by_source = build_query_rows(source_by_id)

    source_rows: list[dict[str, str]] = []
    rights_rows: list[dict[str, str]] = []
    for source_id in sorted(source_by_id):
        spec = source_by_id[source_id]
        review_id = stable_id("R16B-SOURCE-REVIEW", {"source_id": source_id, "shard": SHARD_ID})
        query_ids = sorted(query_ids_by_source[source_id])
        if not query_ids:
            raise ValueError(f"source has no exact query trail: {source_id}")
        source_rows.append(finalize_row({
            "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "source_review_id": review_id,
            "source_id": source_id,
            "source_family": spec["source_family"],
            "authors": spec["authors"],
            "year": spec["year"],
            "title": spec["title"],
            "local_registry_title": spec["local_registry_title"],
            "publication": spec["publication"],
            "volume_issue": spec["volume_issue"],
            "pages": spec["pages"],
            "online_publication_date_or_year": spec["online_publication_date_or_year"],
            "publisher": spec["publisher"],
            "doi": spec["doi"],
            "bibliographic_record_urls_json": canonical_json(spec["record_urls"]),
            "reviewed_text_urls_json": canonical_json(spec["text_urls"]),
            "exact_query_ids_json": canonical_json(query_ids),
            "query_timestamp_status": (
                "EXPLICIT_UNCAPTURED_ONLY_DO_NOT_INFER"
                if all(
                    row["batch_timestamp_utc"] == UNCAPTURED_TIMESTAMP
                    for row in query_rows if row["target_source_id"] == source_id
                )
                else "MIXED_CAPTURED_AND_EXPLICIT_UNCAPTURED"
                if any(
                    row["batch_timestamp_utc"] == UNCAPTURED_TIMESTAMP
                    for row in query_rows if row["target_source_id"] == source_id
                )
                else "ALL_REPORTED_QUERY_TIMESTAMPS_EXACT_CAPTURED_UTC"
            ),
            "access_status": spec["access_status"],
            "source_text_review_status": spec["text_status"],
            "rights_status": spec["rights_status"],
            "license_expression": spec["license"],
            "license_url": spec["license_url"],
            "third_party_exception_status": spec["third_party"],
            "retained_payload_status": "NO_REMOTE_SOURCE_PAYLOAD_RETAINED",
            "retained_payload_sha256": "",
            "locators_json": canonical_json(spec["locators"]),
            "bounded_paraphrase": spec["paraphrase"],
            "direct_support_boundary": spec["support_boundary"],
            "support_mode": spec["support_mode"],
            "bounded_scope": spec["scope"],
            "conflicts_or_counterevidence_json": canonical_json(spec["conflicts"]),
            "nonclaims_json": canonical_json(spec["nonclaims"]),
            "linked_parent_candidate_id": f"R16B-LOCAL-FAMILY:{spec['parent_key']}",
            "parent_disposition_preserved": spec["parent_disposition"],
            "child_or_reroute_action": spec["child_action"],
            "identity_status": "INQUIRY_ONLY_GOVERNED_IDENTITY" if source_id in CANONICAL_INQUIRY_IDENTITIES else "SOURCE_REVIEW_NOT_ACTIVE_ASSOCIATION_IDENTITY",
            "evidence_disposition": spec["evidence_disposition"],
            "human_review_status": "PENDING_EXTERNAL_DESIGN_HISTORY_REVIEW",
            "product_eligibility": "INELIGIBLE_INQUIRY_ONLY_OR_REVIEW_ACTION",
            "pair_projection_count": 0,
            "association_activation": "INACTIVE",
            "active_fact_created": "false",
        }))
        redistribution = spec["license"].startswith("CC BY 4.0") or spec["license"] == "CC BY-NC-ND 4.0"
        rights_rows.append(finalize_row({
            "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "rights_record_id": stable_id("R16B-SOURCE-RIGHTS", {"source_id": source_id, "shard": SHARD_ID}),
            "source_id": source_id,
            "doi": spec["doi"],
            "record_urls_json": canonical_json(spec["record_urls"]),
            "text_urls_json": canonical_json(spec["text_urls"]),
            "access_status": spec["access_status"],
            "source_text_review_status": spec["text_status"],
            "rights_status": spec["rights_status"],
            "license_expression": spec["license"],
            "license_url": spec["license_url"],
            "third_party_exception_status": spec["third_party"],
            "payload_retained": "false",
            "payload_sha256": "",
            "retention_decision": "RETAIN_BIBLIOGRAPHIC_IDENTITY_URLS_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY",
            "redistribution_authorized": "true_with_license_conditions" if redistribution else "false_or_not_established",
            "committed_material": "NO_REMOTE_FULL_TEXT; NO_COPYRIGHTED_PAYLOAD; NO_EXTENDED_EXTRACT",
        }))

    hypothesis_rows: list[dict[str, str]] = []
    for source_id, scope_key, labels, relation_form, support_mode, sense_status in HYPOTHESIS_SPECS:
        spec = source_by_id[source_id]
        participant_sense_ids = [
            stable_id("R16B-PROPOSED-SENSE", {"label": label, "scope_key": scope_key})
            if label.endswith(" NEW") else senses[label]
            for label in labels
        ]
        hypothesis_payload = {
            "source_id": source_id,
            "scope_key": scope_key,
            "participant_sense_ids": participant_sense_ids,
            "relation_form": relation_form,
        }
        hypothesis_id = stable_id("R16B-SCOPED-HYPOTHESIS", hypothesis_payload)
        governed_association_id = ""
        governed_association_revision_id = ""
        canonical_identity_authority_path = ""
        canonical_identity_queue_ref = ""
        governed_identity_status = "SCOPED_HYPOTHESIS_NOT_GOVERNED_ASSOCIATION"
        if source_id in CANONICAL_INQUIRY_IDENTITIES:
            canonical = CANONICAL_INQUIRY_IDENTITIES[source_id]
            if canonical["scope_key"] != scope_key:
                raise ValueError(f"canonical inquiry scope mismatch for {source_id}")
            governed_association_id = canonical["association_id"]
            governed_association_revision_id = canonical["revision_id"]
            canonical_identity_authority_path = TRANCHE_C_IDENTITY_AUTHORITY_PATH
            canonical_identity_queue_ref = canonical["queue_ref"]
            governed_identity_status = "INQUIRY_ONLY"
        exact_group_status = {
            "COMP-SRC-025": "DIRECT_EXACT_GROUP_SUPPORT_CURRENT_SENSES_SAME_CASE",
            "COMP-SRC-024": "DIRECT_EXACT_GROUP_SUPPORT_CURRENT_SENSES_SAME_CASE",
            "COMP-SRC-013": "DIRECT_GROUP_SUPPORT_NEW_SENSE_REQUIRED",
            "COMP-SRC-001": "COHERENT_MULTI_LOCUS_SOURCE_SYNTHESIS_SCOPE_REVIEW_OPEN",
            "GRAM-SRC-025": "DIRECT_LOCAL_ATTESTATION_NEW_SENSE_REQUIRED",
            "COMP-SRC-020": "EXACT_CURRENT_SENSE_GROUP_NOT_SUPPORTED_METHOD_LEVEL_VALUE_ONLY",
        }.get(source_id, "PAIR_OR_IDENTITY_ACTION_NOT_HIGHER_ORDER_GROUP_SUPPORT")
        global_coherence = {
            "COMP-SRC-025": "PASS_SOURCE_LEVEL_SAME_CASE_HUMAN_REVIEW_OPEN",
            "COMP-SRC-024": "PASS_SOURCE_LEVEL_SAME_CASE_HUMAN_REVIEW_OPEN",
            "COMP-SRC-013": "CONDITIONAL_NEW_SENSE_AND_HUMAN_REVIEW",
            "COMP-SRC-001": "CONDITIONAL_MULTI_LOCUS_SCOPE_AND_HUMAN_REVIEW",
            "GRAM-SRC-025": "CONDITIONAL_NEW_SENSE_DESIGN_HISTORY_ALIGNMENT_AND_HUMAN_REVIEW",
            "COMP-SRC-020": "FAIL_EXACT_ARITY5_CASE_AND_SENSE_CONFLICT",
        }.get(source_id, "NOT_APPLICABLE_PAIR_OR_IDENTITY_ACTION")
        hypothesis_rows.append(finalize_row({
            "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
            "shard_id": SHARD_ID,
            "hypothesis_id": hypothesis_id,
            "governed_association_id": governed_association_id,
            "governed_association_revision_id": governed_association_revision_id,
            "canonical_identity_authority_path": canonical_identity_authority_path,
            "canonical_identity_queue_ref": canonical_identity_queue_ref,
            "source_ids_json": canonical_json([source_id]),
            "linked_parent_candidate_id": f"R16B-LOCAL-FAMILY:{spec['parent_key']}",
            "parent_disposition_preserved": spec["parent_disposition"],
            "scope_key": scope_key,
            "scope_note": spec["scope"],
            "participant_labels_json": canonical_json(labels),
            "participant_sense_ids_json": canonical_json(participant_sense_ids),
            "arity": len(labels),
            "participant_order_meaningful": "false",
            "relation_roles_asserted": "false",
            "relation_form": relation_form,
            "support_mode": support_mode,
            "exact_group_support_status": exact_group_status,
            "global_coherence_status": global_coherence,
            "sense_scope_status": sense_status,
            "evidence_disposition": spec["evidence_disposition"],
            "governed_identity_status": governed_identity_status,
            "external_human_review_status": "OPEN",
            "association_activation_status": "INACTIVE",
            "active_fact_created": "false",
            "product_eligibility": "INELIGIBLE_INQUIRY_ONLY_OR_REVIEW_ACTION",
            "pair_projection_count": 0,
            "subset_projection_count": 0,
            "nonclaims_json": canonical_json(spec["nonclaims"]),
        }))

    if len(source_rows) != 9 or len(rights_rows) != 9 or len(hypothesis_rows) != 9:
        raise ValueError("shard cardinality mismatch")
    if sum(row["governed_identity_status"] == "INQUIRY_ONLY" for row in hypothesis_rows) != 2:
        raise ValueError("expected exactly two governed inquiry-only association identities")
    for row in source_rows + hypothesis_rows:
        if row.get("active_fact_created") != "false" or row.get("pair_projection_count") != "0":
            raise ValueError("fail-closed activation/projection invariant violated")

    gap_specs = [
        ("EXTERNAL_HUMAN_REVIEW", "HIGH", [spec["source_id"] for spec in SOURCE_SPECS], "All scoped support decisions remain pending independent design-history review.", "Nine source audits are complete, but every hypothesis records external human review OPEN.", "Obtain and record independent domain review before any activation.", "BLOCKS_ASSOCIATION_AND_FUNCTION3_CLOSURE"),
        ("FULL_TEXT_ACCESS", "HIGH", ["COMP-SRC-023"], "A lawful reviewable full text for the Brussels article was not established.", "Only the public publisher abstract, repository record, and printed-page reference were reviewed.", "Resolve lawful full-text access and falsify the propaganda participant before any Brussels triad review.", "BLOCKS_BRUSSELS_GROUP_SUPPORT"),
        ("NEW_SENSE_GOVERNANCE", "HIGH", ["COMP-SRC-013"], "The contact-zone negotiation concept cannot use the current Keraton-bounded cultural-negotiation sense.", "The source directly supports an architectural-contact-zone configuration under unequal participation.", "Create and independently review a source-specific contact-zone negotiation sense.", "BLOCKS_CONTACT_ZONE_CHILD_IDENTITY"),
        ("VOCABULARY_IDENTITY", "HIGH", ["R16-SRC-005"], "Education and design education are nested in the Bauhaus source and are not proved distinct roles.", "The full-text review supports craft plus design education, not a three-role structure.", "Resolve duplicate, specialization, or sense-split identity before any higher-order use.", "BLOCKS_BAUHAUS_TRIAD"),
        ("NEW_SENSE_AND_AUTHORITY", "HIGH", ["GRAM-SRC-025"], "Professional education or training requires a new sense and design-history authority alignment.", "The built-environment source does not authorize substitution of the canonical Bauhaus education sense.", "Govern the new sense and obtain domain review before creating a child association identity.", "BLOCKS_PROFESSIONAL_EDUCATION_CHILD"),
        ("METHOD_VERSUS_CASE_SCOPE", "HIGH", ["COMP-SRC-020"], "The Hutton article contains three material-movement cases rather than one exact five-member case.", "The article-method-level configuration is coherent as research value, but the current production and consumption senses also conflict.", "Decide method-level association class versus separately reviewed case children and govern any new senses.", "BLOCKS_EXACT_ARITY5_ACTIVATION"),
        ("PAYLOAD_HASH", "MEDIUM", [spec["source_id"] for spec in SOURCE_SPECS], "No remote source payload was retained or hashed in the completed review handoff.", "The shard retains source identity, exact URLs, access and rights decisions, locators, bounded paraphrase, and deterministic row hashes only.", "If a future lawful reproducibility protocol captures bytes, store only permitted hashes and never commit unauthorized full text.", "DOES_NOT_INVALIDATE_REVIEW_BUT_LIMITS_BYTE_LEVEL_REPRODUCTION"),
        ("PRODUCT_REPRESENTATION", "HIGH", ["COMP-SRC-025", "COMP-SRC-024", "COMP-SRC-013", "COMP-SRC-001", "GRAM-SRC-025"], "No higher-order source hypothesis has an active product path.", "Product eligibility, activation, and all pair/subset projections are zero by construction.", "Complete human review, model audit, representation tests, and product-governance decision before product activation.", "BLOCKS_PRODUCT_AND_FUNCTION3_CLOSURE"),
    ]
    gap_rows = [finalize_row({
        "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "gap_id": stable_id("R16B-ADAPTIVE-SOURCE-GAP", {"gap_class": gap_class, "sources": sorted(sources)}),
        "gap_class": gap_class,
        "severity": severity,
        "status": "OPEN",
        "affected_source_ids_json": canonical_json(sorted(sources)),
        "gap": gap,
        "evidence": evidence,
        "required_next_action": action,
        "closure_effect": effect,
    }) for gap_class, severity, sources, gap, evidence, action, effect in gap_specs]

    license_counts = dict(sorted(Counter(row["license_expression"] for row in rights_rows).items()))
    support_counts = dict(sorted(Counter(row["support_mode"] for row in hypothesis_rows).items()))
    query_purpose_counts = dict(sorted(Counter(row["purpose"] for row in query_rows).items()))
    census = {
        "format": "trace-round16b-adaptive-source-review-census-shard-1-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "source_review_count": len(source_rows),
        "rights_record_count": len(rights_rows),
        "query_batch_count": len(QUERY_BATCHES),
        "query_count": len(query_rows),
        "query_with_exact_captured_timestamp_count": sum(row["timestamp_capture_status"] == "EXACT_CAPTURED_UTC" for row in query_rows),
        "query_with_explicit_uncaptured_timestamp_count": sum(row["timestamp_capture_status"] == "NOT_CAPTURED_DO_NOT_INFER" for row in query_rows),
        "query_purpose_counts": query_purpose_counts,
        "license_expression_counts": license_counts,
        "remote_payload_retained_count": 0,
        "remote_payload_sha256_count": 0,
        "scoped_hypothesis_count": len(hypothesis_rows),
        "hypothesis_arity_distribution": dict(sorted(Counter(row["arity"] for row in hypothesis_rows).items())),
        "hypothesis_support_mode_counts": support_counts,
        "exact_current_sense_same_case_direct_higher_order_support_count": 2,
        "governed_inquiry_only_association_identity_count": 2,
        "canonical_identity_authority_path": TRANCHE_C_IDENTITY_AUTHORITY_PATH,
        "canonical_identity_authority_sha256": canonical_identity_authority_sha256,
        "association_activation_count": 0,
        "active_fact_created_count": 0,
        "product_eligible_count": 0,
        "pair_projection_count": 0,
        "subset_projection_count": 0,
        "active_pending_review_count": 0,
        "open_gap_count": len(gap_rows),
        "closure": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
        "semantic_boundary": "A source-level direct-support disposition is not association activation. COMP-SRC-025 and COMP-SRC-020 reference the two canonical tranche-C governed INQUIRY_ONLY identities; Hutton's exact active current-sense arity-five group remains blocked. All active facts, product eligibility, and pair/subset projections remain zero. Search results are discovery records only.",
    }

    note = f"""# Adaptive source review shard 1

## Authority and boundary

This deterministic shard is bound to evidence-authority base `{EVIDENCE_AUTHORITY_BASE_SHA}`, authorized Round 16A source `{AUTHORIZED_SOURCE_SHA}`, and source tree `{AUTHORIZED_SOURCE_TREE}`. It freezes nine completed locator-bearing source audits and forty exact adaptive-search queries. Thirty-six queries retain exact captured UTC timestamps; four root web-tool queries explicitly retain `{UNCAPTURED_TIMESTAMP}` rather than an invented time.

Search ranking, snippets, metadata, and query co-occurrence remain discovery-only. No remote full text is committed. The shard retains bibliographic identity, exact record and text URLs, access and rights conditions, license decisions, locators, bounded paraphrases, source-level decisions, qualifications, non-claims, and deterministic record hashes.

## Source-level results

- `COMP-SRC-001` supports an inactive, scoped Western-interior-design multi-locus hypothesis; the unsplit arity-three parent remains pairwise-supported without global coherence.
- `COMP-SRC-013` directly supports an architectural-contact-zone adaptation/negotiation/rejection configuration, but a new contact-zone negotiation sense and human review are required.
- `COMP-SRC-014` supports only the bounded Keraton adaptation/cultural-negotiation pair; rejection is absent.
- `COMP-SRC-023` supports a Brussels exhibition/design-diplomacy pair from a public abstract and page reference, not the proposed propaganda triad; lawful full-text review remains open.
- `COMP-SRC-024` directly supports the exact Turin 1961 exhibition/propaganda/design-diplomacy triad as an inactive same-case hypothesis.
- `R16-SRC-005` supports craft with Bauhaus design education, while education/design-education identity remains unresolved and no three-role association is created.
- `GRAM-SRC-025` supports a source-local professionalization/institutionalization/professional-education configuration only after a new professional-education sense and design-history review.
- `COMP-SRC-025` directly supports the exact Sweden-in-Sydney 1954 `[exhibition, trade, propaganda, design diplomacy]` arity-four structure. It receives one governed `INQUIRY_ONLY` association identity; it is product-inactive, human-review-open, and creates no pair or subset projection.
- `COMP-SRC-020` supplies article-method-level sparse-hyperedge research value and references the second canonical tranche-C `INQUIRY_ONLY` identity, but its three separate cases and the current production/consumption sense mismatch block the exact active arity-five structure.

## Rights and reproducibility

Open-license conditions are recorded for the ETH contact-zone text (CC BY-NC-ND 4.0), the Keraton, Turin, Sweden, and Bauhaus texts (CC BY 4.0, with source-specific or third-party conditions where noted). The Lees-Maffei accepted manuscript remains all-rights-reserved; the Brussels license is unverified; Bresnen is publisher Free Access without an identified CC license; and Hutton has lawful public read access but unknown redistribution rights. Only links and bounded research records are committed.

No downloaded source payload was retained in the completed handoff, so the remote-payload hash count is truthfully zero. This is recorded as an open byte-level reproducibility gap, not concealed by hashing URLs or paraphrases as if they were source bytes.

## Fail-closed result

The shard creates zero active facts, zero active-pending-review facts, zero product-eligible associations, zero pair projections, and zero subset projections. Pair, higher-order, global-coherence, product-reachability, computational-space, and Function 3 closure remain false.
""".encode("utf-8")

    source_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-shard-1-v1.tsv"
    query_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-search-query-log-shard-1-v1.tsv"
    rights_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/source-rights-ledger-shard-1-v1.tsv"
    hypothesis_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv"
    census_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-census-shard-1-v1.json"
    gaps_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/recursive-gap-ledger-adaptive-source-shard-1-v1.tsv"
    note_output = "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/13_ADAPTIVE_SOURCE_REVIEW_SHARD_1.md"
    artifacts: dict[str, bytes] = {
        source_output: tsv_bytes(SOURCE_REVIEW_FIELDS, source_rows),
        query_output: tsv_bytes(QUERY_FIELDS, query_rows),
        rights_output: tsv_bytes(RIGHTS_FIELDS, rights_rows),
        hypothesis_output: tsv_bytes(HYPOTHESIS_FIELDS, hypothesis_rows),
        census_output: json_bytes(census),
        gaps_output: tsv_bytes(GAP_FIELDS, gap_rows),
        note_output: note,
    }
    output_hashes = {
        path: {"bytes": len(payload), "sha256": sha256_bytes(payload)}
        for path, payload in sorted(artifacts.items())
    }
    receipt = {
        "format": "trace-round16b-adaptive-source-review-build-receipt-shard-1-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "evidence_authority_base_sha": EVIDENCE_AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "pinned_input_hashes": dict(sorted(PINNED_INPUT_SHA256.items())),
        "source_review_count": len(source_rows),
        "query_batch_count": len(QUERY_BATCHES),
        "query_count": len(query_rows),
        "query_exact_timestamp_count": 36,
        "query_explicit_uncaptured_timestamp_count": 4,
        "rights_record_count": len(rights_rows),
        "scoped_hypothesis_count": len(hypothesis_rows),
        "governed_inquiry_only_association_identity_count": 2,
        "canonical_identity_authority_path": TRANCHE_C_IDENTITY_AUTHORITY_PATH,
        "canonical_identity_authority_sha256": canonical_identity_authority_sha256,
        "remote_payload_retained_count": 0,
        "remote_payload_sha256_count": 0,
        "association_activation_count": 0,
        "active_fact_created_count": 0,
        "active_pending_review_count": 0,
        "product_eligible_count": 0,
        "pair_projection_count": 0,
        "subset_projection_count": 0,
        "closure_flags_true_count": 0,
        "open_gap_count": len(gap_rows),
        "output_count_excluding_receipt": len(artifacts),
        "output_hashes": output_hashes,
        "aggregate_output_sha256": sha256_text(canonical_json(output_hashes)),
        "status": "PASS_FAIL_CLOSED_ADAPTIVE_SOURCE_SHARD_1",
    }
    artifacts["docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-build-receipt-shard-1-v1.json"] = json_bytes(receipt)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare generated bytes with existing artifacts")
    args = parser.parse_args()
    artifacts = build_artifacts()
    if args.check:
        mismatches = [
            relative for relative, expected in artifacts.items()
            if not (REPO / relative).exists() or (REPO / relative).read_bytes() != expected
        ]
        if mismatches:
            raise SystemExit("deterministic artifact mismatch: " + ";".join(mismatches))
        print(canonical_json({"artifact_count": len(artifacts), "mode": "CHECK", "status": "PASS"}))
        return
    for relative, payload in artifacts.items():
        path = REPO / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    receipt_path = RAW / "adaptive-source-review-build-receipt-shard-1-v1.json"
    print(receipt_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
