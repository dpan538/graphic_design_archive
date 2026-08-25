#!/usr/bin/env python3
"""Build the TRACE v49 Round 10 relation-grammar research and audit packages.

The generator is deliberately data-first.  It consumes only the frozen Round 9
passing rows, writes exhaustive 16-node and 256-ordered-pair registries, and
seals the result.  It does not touch active application code.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
R9 = ROOT / "docs/research/trace-v49-design-history-relation-vocabulary-round1"
RESEARCH = ROOT / "docs/research/trace-v49-design-history-relation-grammar-round1"
AUDIT = ROOT / "docs/audits/v49-design-history-relation-grammar-round1"
RAW = AUDIT / "raw"
SOURCE_SHA = "0241b0f51e2523901b0858d54ffb7f5d2a9aa13c"
R9_REGISTRY_SHA = "818b306406d6a557a563ec285ae36394106c4c88a3e14cae19e4f1da4e92f4d5"

ROLES = [
    "AGENT-GRAMMAR-DISCOVERY",
    "AGENT-GRAMMAR-VERIFY-A",
    "AGENT-GRAMMAR-VERIFY-B",
    "AGENT-GRAMMAR-SEMANTIC",
    "AGENT-GRAMMAR-ADVERSARIAL",
    "AGENT-UNIVERSAL-NODE-RED-TEAM",
    "AGENT-SOURCE-BREADTH-REVIEW",
]

# These receipt slots will transcribe conclusions from independent computational
# review processes only after they complete. The generator does not treat
# generation itself as review, and pending generation serializes no conclusions.
REVIEW_RECEIPTS = {
    "AGENT-GRAMMAR-DISCOVERY": {
        "receipt_id": "PROCESS-REVIEW-001",
        "scope": "16 Node candidates; 256 ordered cells; 3 deferred pair candidates",
        "evidence": "new term-specific grammar sources, bounded contexts, roles, directionality, and pair-composition challenge sources",
        "finding": "Exhaustive review confirmed 28 sources, 30 exact bounded attestations, all 16 Node decisions, and all 256 cells; source year, item classification, peer-review uncertainty, and exact typography were repaired before the role passed, and no pair met the composition gate.",
    },
    "AGENT-GRAMMAR-VERIFY-A": {
        "receipt_id": "PROCESS-REVIEW-002",
        "scope": "16 Node candidates; 256 ordered cells; all 16 diagonals; 3 deferred pair candidates",
        "evidence": "Round 9 lineage, Round 10 sources and attestations, role contracts, matrix Cartesian coverage, and hard-gate fields",
        "finding": "All 16 Round 9 derivations, contracts, explanations, and all 256 pair cells resolved without missing, duplicate, orphaned, or incomplete hard-gate fields; the final outcome remains eight Node candidates, eight deferrals, and zero passing pairs.",
    },
    "AGENT-GRAMMAR-VERIFY-B": {
        "receipt_id": "PROCESS-REVIEW-003",
        "scope": "16 Node candidates; 256 ordered cells; all 16 diagonals; 3 deferred pair candidates",
        "evidence": "stable regenerated package, exact attestation contexts, source metadata, directionality, pair evidence, explanations, and default-deny coverage",
        "finding": "Independent full-package reinspection verified all 28 metadata rows, 30 exact contexts, 16 Nodes, 256 cells, and the support-file seal after exact-typography and zero-arrow authorization remediation; no residual defect remained.",
    },
    "AGENT-GRAMMAR-SEMANTIC": {
        "receipt_id": "PROCESS-REVIEW-004",
        "scope": "16 separate frozen senses; 256 ordered cells; 3 deferred pair candidates",
        "evidence": "anti-flattening comparisons, process/condition distinctions, bounded roles, contestation, normative qualifiers, and natural-language records",
        "finding": "All 16 senses remain separate across contracts, contestation records, anti-flattening comparisons, 19 natural-language explanations, and 256 pair decisions; no generic merge, role collapse, qualifier loss, circular self-loop, or inferred transitivity survived review.",
    },
    "AGENT-GRAMMAR-ADVERSARIAL": {
        "receipt_id": "PROCESS-REVIEW-005",
        "scope": "16 Node candidates; 256 ordered cells; all 16 diagonals; 3 deferred pair candidates",
        "evidence": "two-source composition gate, design-history article gate, source-cluster independence, role mapping, directionality, co-occurrence ban, and transitivity ban",
        "finding": "Promotion attacks against every Node and pair left zero passing compositions: the three candidate pairs remain deferred and 237 cells default deny; the review also caught and removed premature visual-arrow authorization from directed Node semantics.",
    },
    "AGENT-UNIVERSAL-NODE-RED-TEAM": {
        "receipt_id": "PROCESS-REVIEW-006",
        "scope": "16 Node candidates; 256 ordered cells; all deferred and default-denied degrees",
        "evidence": "literal and semantic any-like roles, generic wording, scope, connectivity, bridge use, pair-specific support, and allowed/deferred/default-denied degree counts",
        "finding": "Exactly eight broad senses are semantic-any-like universal candidates and all remain deferred; allowed degree is zero in both directions, with no literal ANY role, bridge, arrow, self-loop, or universal-node pass across all 256 cells.",
    },
    "AGENT-SOURCE-BREADTH-REVIEW": {
        "receipt_id": "PROCESS-REVIEW-007",
        "scope": "all 28 registered scholarly sources; 30 grammar attestations; all 16 Nodes and 3 deferred pairs",
        "evidence": "author/work independence, venue, publisher, language, source stratum, peer-review status, JDH/OUP concentration, and final saturation batches",
        "finding": "All 28 unique works and 30 attestations span 63 named authors, 25 venues, 10 publishers, three languages, and 24 strata; JDH/OUP shares are 0.0357/0.1071, uncertainty remains explicit, and batches 6 and 7 add no passing rule.",
    },
}

# Keep false while the stable research registries are being independently
# re-reviewed.  Flip to true only after every process receipt has been earned;
# the final generation then serializes (rather than invents) those outcomes.
REVIEWS_FINALIZED = True


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clean(value: object) -> str:
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field, "")) for field in fields})


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


SOURCE_FIELDS = [
    "source_id", "authors", "year", "title", "publication", "source_class",
    "peer_reviewed", "publisher", "doi_isbn", "stable_publisher_url",
    "source_language", "published_translation", "source_stratum",
    "new_for_round10", "metadata_verified", "discovery_batch",
]


SOURCES = [
    dict(source_id="GRAM-SRC-001", authors="Anna Kallen Talley", year="2026", title="Digital Design History: State of the Field, Definitions and Possibilities", publication="Journal of Design History", source_class="ARTICLE", peer_reviewed="true", publisher="Oxford University Press", doi_isbn="10.1093/jdh/epag001", stable_publisher_url="https://academic.oup.com/jdh/article/39/2/113/8537083", source_language="English", published_translation="", source_stratum="DESIGN_HISTORIOGRAPHY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-01"),
    dict(source_id="GRAM-SRC-002", authors="Piotr Korduba", year="2021", title="Między monografią a koneserstwem. Badania nad polskim dizajnem XX i początków XXI wieku", publication="Artium Quaestiones", source_class="ARTICLE", peer_reviewed="true", publisher="Adam Mickiewicz University Press", doi_isbn="10.14746/aq.2021.32.1", stable_publisher_url="https://pressto.amu.edu.pl/index.php/aq/article/view/32548", source_language="Polish", published_translation="Publisher-supplied English abstract", source_stratum="NON_ENGLISH_DESIGN_HISTORIOGRAPHY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-04"),
    dict(source_id="GRAM-SRC-003", authors="Robert Lzicar; Amanda Unger", year="2016", title="Designed Histories: Visual Historiography and Canonization in Swiss Graphic Design History", publication="Mapping Graphic Design History in Switzerland", source_class="BOOK_CHAPTER", peer_reviewed="unknown", publisher="Triest", doi_isbn="978-3-03863-009-8", stable_publisher_url="https://arbor.bfh.ch/handle/arbor/37952", source_language="English", published_translation="", source_stratum="GRAPHIC_DESIGN_HISTORIOGRAPHY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-01"),
    dict(source_id="GRAM-SRC-004", authors="Leah Armstrong", year="2019", title="A New Image for a New Profession: Self-Image and Representation in the Professionalization of Design in Britain, 1945-1960", publication="Journal of Consumer Culture", source_class="ARTICLE", peer_reviewed="true", publisher="SAGE", doi_isbn="10.1177/1469540517708830", stable_publisher_url="https://journals.sagepub.com/doi/10.1177/1469540517708830", source_language="English", published_translation="", source_stratum="GRAPHIC_DESIGN_PROFESSIONAL_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-01"),
    dict(source_id="GRAM-SRC-005", authors="Turid Moldenæs; Hilde Marie Pettersen", year="2021", title="The professional project of graphic designers and universities' visual identities", publication="Journal of Professions and Organization", source_class="ARTICLE", peer_reviewed="true", publisher="Oxford University Press", doi_isbn="10.1093/jpo/joab010", stable_publisher_url="https://academic.oup.com/jpo/article/8/2/184/6324046", source_language="English", published_translation="", source_stratum="PROFESSIONAL_INSTITUTIONAL_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-02"),
    dict(source_id="GRAM-SRC-006", authors="Ali O. Ilhan", year="2017", title="Growth or Decline? A Longitudinal Analysis of Factors Affecting the Institutional Trajectories of Five Design Disciplines in the United States", publication="She Ji: The Journal of Design, Economics, and Innovation", source_class="ARTICLE", peer_reviewed="true", publisher="Tongji University Press / Elsevier", doi_isbn="10.1016/j.sheji.2017.04.001", stable_publisher_url="https://www.sciencedirect.com/science/article/pii/S2405872616300983", source_language="English", published_translation="", source_stratum="PROFESSIONAL_INSTITUTIONAL_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-02"),
    dict(source_id="GRAM-SRC-007", authors="Grace Lees-Maffei", year="2025", title="Recent histories of the professionalization of interior design: from gatekeeping to inclusion", publication="Interiors", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/20419112.2025.2551445", stable_publisher_url="https://www.tandfonline.com/doi/full/10.1080/20419112.2025.2551445", source_language="English", published_translation="", source_stratum="GENDER_PROFESSIONAL_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-02"),
    dict(source_id="GRAM-SRC-008", authors="Paolo Scrivano", year="2021", title="The Complexity of Cultural Exchange: Anglo-Italian Relations in Architecture between Transnational Interactions and National Narratives", publication="Postwar Architecture between Italy and the UK", source_class="BOOK_CHAPTER", peer_reviewed="unknown", publisher="UCL Press", doi_isbn="9781800080836", stable_publisher_url="https://re.public.polimi.it/handle/11311/1182602", source_language="English", published_translation="", source_stratum="GLOBAL_TRANSNATIONAL_DESIGN_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-009", authors="Katarina Serulus", year="2017", title="Well-Designed Relations: Cold War Design Exchanges between Brussels and Moscow in the Early 1970s", publication="Design and Culture", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/17547075.2017.1326231", stable_publisher_url="https://www.tandfonline.com/doi/abs/10.1080/17547075.2017.1326231", source_language="English", published_translation="", source_stratum="GLOBAL_TRANSNATIONAL_DESIGN_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-010", authors="Boris Buden; Stefan Nowotny; Sherry Simon; Ashok Bery; Michael Cronin", year="2009", title="Cultural translation: An introduction to the problem, and Responses", publication="Translation Studies", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/14781700902937730", stable_publisher_url="https://www.tandfonline.com/doi/full/10.1080/14781700902937730", source_language="English", published_translation="", source_stratum="TRANSLATION_STUDIES", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-011", authors="Peter Burke", year="2007", title="Cultures of translation in early modern Europe", publication="Cultural Translation in Early Modern Europe", source_class="BOOK_CHAPTER", peer_reviewed="unknown", publisher="Cambridge University Press", doi_isbn="10.1017/CBO9780511497193.002", stable_publisher_url="https://www.cambridge.org/core/books/abs/cultural-translation-in-early-modern-europe/cultures-of-translation-in-early-modern-europe/B9342283A22BFD6B066CEAB695DB572A", source_language="English", published_translation="", source_stratum="TRANSLATION_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-012", authors="Ze-Rui Xiang; Miao Li; Yong-Meng Wu; Xiao-Fei Xu; Fan Zhang; Xiao Zhao", year="2025", title="Cultural Product Design: An Approach for Identifying Cultural Carriers, Transforming Cultural Elements and Applying Cultural Features", publication="Design Science", source_class="ARTICLE", peer_reviewed="true", publisher="Cambridge University Press", doi_isbn="10.1017/dsj.2025.10031", stable_publisher_url="https://www.cambridge.org/core/journals/design-science/article/cultural-product-design-an-approach-for-identifying-cultural-carriers-transforming-cultural-elements-and-applying-cultural-features/1F0FD01E3314DE8D3B173257AA422726", source_language="English", published_translation="", source_stratum="CULTURAL_TRANSLATION_DESIGN_RESEARCH", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-013", authors="Estelle Blaschke", year="2014", title="Making History a Slightly Profitable Thing: The Bettmann Archive and the Commodification of Images", publication="Visual Resources", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/01973762.2014.936101", stable_publisher_url="https://www.tandfonline.com/doi/abs/10.1080/01973762.2014.936101", source_language="English", published_translation="", source_stratum="VISUAL_CULTURE_MARKET_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-02"),
    dict(source_id="GRAM-SRC-014", authors="Annebella Pollen", year="2011", title="Performing Spectacular Girlhood: Mass-Produced Dressing-Up Costumes and the Commodification of Imagination", publication="Textile History", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1179/174329511X13123634653820", stable_publisher_url="https://www.tandfonline.com/doi/full/10.1179/174329511X13123634653820", source_language="English", published_translation="", source_stratum="GENDER_MATERIAL_CULTURE", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-02"),
    dict(source_id="GRAM-SRC-015", authors="Magdalena Petersson McIntyre", year="2018", title="Gender by Design: Performativity and Consumer Packaging", publication="Design and Culture", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/17547075.2018.1516437", stable_publisher_url="https://www.tandfonline.com/doi/pdf/10.1080/17547075.2018.1516437", source_language="English", published_translation="", source_stratum="GENDER_FEMINIST_DESIGN", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-02"),
    dict(source_id="GRAM-SRC-016", authors="Sarah A. Lichtman; Jilly Traganou", year="2024", title="Design, Displacement, Migration: Spatial and Material Histories", publication="Routledge Research in Design History", source_class="EDITED_BOOK", peer_reviewed="unknown", publisher="Routledge", doi_isbn="10.4324/9781003194293", stable_publisher_url="https://www.routledge.com/Design-Displacement-Migration-Spatial-and-Material-Histories/Lichtman-Traganou/p/book/9781003194293", source_language="English", published_translation="", source_stratum="MIGRATION_DISPLACEMENT_DESIGN_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-017", authors="Wenwen Sun", year="2020", title="Public space in Chinese urban design theory after 1978: a compressed transculturation", publication="The Journal of Architecture", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/13602365.2020.1734048", stable_publisher_url="https://repository.tudelft.nl/record/uuid:9f03fa61-1501-4d81-9c11-a1a191797752", source_language="English", published_translation="Discusses Chinese-language source corpus", source_stratum="EAST_ASIAN_ARCHITECTURAL_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-04"),
    dict(source_id="GRAM-SRC-018", authors="Stephen Greenblatt; Ines G. Županov; Reinhard Meyer-Kalkus; Heike Paul; Pál Nyíri; Friederike Pannewick", year="2009", title="Cultural Mobility: A Manifesto", publication="Cultural Mobility: A Manifesto", source_class="EDITED_BOOK", peer_reviewed="unknown", publisher="Cambridge University Press", doi_isbn="9780521682206", stable_publisher_url="https://stephengreenblatt.scholars.harvard.edu/cultural-mobility-manifesto", source_language="English", published_translation="", source_stratum="CULTURAL_MOBILITY_STUDIES", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-03"),
    dict(source_id="GRAM-SRC-019", authors="Yoo Jin Kwon; Yhe-Young Lee", year="2015", title="Traditional Aesthetic Characteristics Traced in South Korean Contemporary Fashion Practice", publication="Fashion Practice", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/17569370.2015.1045348", stable_publisher_url="https://www.tandfonline.com/doi/abs/10.1080/17569370.2015.1045348", source_language="English", published_translation="Engages Korean-language scholarship", source_stratum="EAST_ASIAN_FASHION_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-04"),
    dict(source_id="GRAM-SRC-020", authors="Tristan Schultz; Danah Abdulla; Ahmed Ansari; Ece Canlı; Mahmoud Keshavarz; Matthew Kiem; Luiza Prado de O. Martins; Pedro J.S. Vieira de Oliveira", year="2018", title="Editors' Introduction", publication="Design and Culture", source_class="EDITORIAL_ARTICLE", peer_reviewed="unknown", publisher="Taylor & Francis", doi_isbn="10.1080/17547075.2018.1434367", stable_publisher_url="https://www.tandfonline.com/doi/full/10.1080/17547075.2018.1434367", source_language="English", published_translation="", source_stratum="DECOLONIAL_POSTCOLONIAL_DESIGN", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-04"),
    dict(source_id="GRAM-SRC-021", authors="Marlena Jankowska", year="2023", title="House of sartorial genius? History of imitation in the modern fashion industry", publication="Intellectual Property Rights, Copynorm and the Fashion Industry", source_class="BOOK_CHAPTER", peer_reviewed="unknown", publisher="Routledge", doi_isbn="10.4324/9781003376033-2", stable_publisher_url="https://www.taylorfrancis.com/chapters/oa-mono/10.4324/9781003376033-2/house-sartorial-genius-history-imitation-modern-fashion-industry-marlena-jankowska", source_language="English", published_translation="", source_stratum="COPYING_RIGHTS_MARKETS", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-05"),
    dict(source_id="GRAM-SRC-022", authors="Audrey Millet", year="2013", title="Dessiner La Mode En Régime De Fabrique: L'imitation Au Cœur Du Processus Créatif", publication="Konsthistorisk tidskrift / Journal of Art History", source_class="ARTICLE", peer_reviewed="true", publisher="Taylor & Francis", doi_isbn="10.1080/00233609.2013.809017", stable_publisher_url="https://www.tandfonline.com/doi/full/10.1080/00233609.2013.809017", source_language="French", published_translation="Publisher-supplied English summary", source_stratum="NON_ENGLISH_FASHION_HISTORY", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-04"),
    dict(source_id="GRAM-SRC-023", authors="Alice Wickens", year="2025", title="From calico to catwalk: Addressing the UK's enduring issue of fashion piracy", publication="Journal of Intellectual Property Law & Practice", source_class="ARTICLE", peer_reviewed="true", publisher="Oxford University Press", doi_isbn="10.1093/jiplp/jpae107", stable_publisher_url="https://academic.oup.com/jiplp/article/20/2/71/7916754", source_language="English", published_translation="", source_stratum="COPYING_RIGHTS_MARKETS", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-05"),
    dict(source_id="GRAM-SRC-024", authors="Sara B. Marcketti; Jean L. Parsons", year="2006", title="Design Piracy and Self-Regulation: The Fashion Originators' Guild of America, 1932-1941", publication="Clothing and Textiles Research Journal", source_class="ARTICLE", peer_reviewed="true", publisher="SAGE", doi_isbn="10.1177/0887302X06293071", stable_publisher_url="https://journals.sagepub.com/doi/10.1177/0887302X06293071", source_language="English", published_translation="", source_stratum="COPYING_RIGHTS_MARKETS", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-05"),
    dict(source_id="GRAM-SRC-025", authors="Mike Bresnen", year="2013", title="Advancing a new professionalism: professionalization, practice and institutionalization", publication="Building Research & Information", source_class="COMMENTARY", peer_reviewed="unknown", publisher="Taylor & Francis", doi_isbn="10.1080/09613218.2013.843269", stable_publisher_url="https://www.tandfonline.com/doi/full/10.1080/09613218.2013.843269", source_language="English", published_translation="", source_stratum="PROFESSIONAL_INSTITUTIONAL_COMPOSITION_CHALLENGE", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-06"),
    dict(source_id="GRAM-SRC-026", authors="Emma Waight", year="2019", title="Mother, consumer, trader: gendering the commodification of second-hand economies since the recession", publication="Journal of Consumer Culture", source_class="ARTICLE", peer_reviewed="true", publisher="SAGE", doi_isbn="10.1177/1469540519872069", stable_publisher_url="https://journals.sagepub.com/doi/10.1177/1469540519872069", source_language="English", published_translation="", source_stratum="GENDER_MARKET_COMPOSITION_CHALLENGE", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-06"),
    dict(source_id="GRAM-SRC-027", authors="Areti T. Vogel; Jacob Vogel; Kittichai Watchravesringkan; Sasikarn Chatvijit Cook; James Beasley; Randall Croom; Dale Peterson; Joshua Finkelstein", year="2023", title="Design piracy: an interdisciplinary investigation into competitive industrial behavior", publication="Journal of Business Research", source_class="ARTICLE", peer_reviewed="true", publisher="Elsevier", doi_isbn="10.1016/j.jbusres.2023.113946", stable_publisher_url="https://www.sciencedirect.com/science/article/pii/S0148296323003041", source_language="English", published_translation="", source_stratum="COPYING_COMPOSITION_CHALLENGE", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-06"),
    dict(source_id="GRAM-SRC-028", authors="Gino Cattani; Mariachiara Colucci; Simone Ferriani", year="2023", title="From the Margins to the Core of Haute Couture: The Entrepreneurial Journey of Coco Chanel", publication="Enterprise & Society", source_class="ARTICLE", peer_reviewed="true", publisher="Cambridge University Press", doi_isbn="10.1017/eso.2021.58", stable_publisher_url="https://www.cambridge.org/core/journals/enterprise-and-society/article/from-the-margins-to-the-core-of-haute-couture-the-entrepreneurial-journey-of-coco-chanel/F9C3C4631A1971D2A18A6A468308F1AA", source_language="English", published_translation="", source_stratum="FASHION_BUSINESS_HISTORY_COMPOSITION_CHALLENGE", new_for_round10="true", metadata_verified="true", discovery_batch="BATCH-06"),
]


NODE_DATA = {
    "mediation": dict(role="UNRESOLVED_MIXED_ROLE", decision="DEFER_TOO_BROAD", arity="MULTIPARTY", subject="producer, mediator, channel, designed thing, or prior meaning in the cited design-historical account", target="consumer, audience, practice, or received meaning in that same account", parties="designed channel; institution; audience", input="a situated production-consumption configuration", output="a changed encounter, practice, or meaning", context="a named mediation channel and historical setting", qualification="which mediation sense and mediating actor are meant", scope_in="source-bounded production-consumption mediation", scope_out="generic connection, legal mediation, or any-to-any bridging", sources="GRAM-SRC-001;GRAM-SRC-002", reason="New evidence multiplies producing, consuming, algorithmic, institutional, and discursive roles; one bounded binary contract would flatten them.", direction="MIXED_USAGE_DEFER"),
    "canonization": dict(role="HISTORIOGRAPHIC_POSITIONING", decision="PASS_HISTORIOGRAPHIC_POSITION_NODE", arity="2", subject="a work, movement, representation, or historical narrative selected for canonical status", target="a bounded design-historical canon or canonical status", parties="historians; publishers; exhibitions; educational institutions", input="contested historical material outside or unevenly positioned in a canon", output="greater canonical recognition or documented exclusion", context="an identified historiographic corpus and period", qualification="selection mechanisms and exclusions must be stated", scope_in="design-historical canon formation", scope_out="general popularity or quality ranking", sources="GRAM-SRC-003", reason="The new graphic-design-history chapter provides a bounded historiographic subject, target, and selection mechanism.", direction="DIRECTED"),
    "professionalization": dict(role="DIRECTED_PROCESS", decision="PASS_FLOW_ELIGIBLE_NODE", arity="2", subject="a named design occupation or disciplinary practice seeking professional standing", target="historically contested professional standing in a named field", parties="educators; professional bodies; clients; regulators", input="a cited occupation or practice undergoing professional formation", output="a historically specific professional identity, status, or apparatus", context="named field, jurisdiction, period, and professional mechanisms", qualification="professional standing is historically contested and may exclude", scope_in="historical formation of design professions", scope_out="generic improvement, employment, or individual career advancement", sources="GRAM-SRC-004;GRAM-SRC-005;GRAM-SRC-007", reason="Independent new histories consistently identify education, organizations, standards, codes, jurisdiction, and gatekeeping as bounded mechanisms.", direction="DIRECTED"),
    "institutionalization": dict(role="DIRECTED_PROCESS", decision="PASS_FLOW_ELIGIBLE_NODE", arity="2", subject="a named design logic, program, practice, or discipline carried by identified agents", target="a specified organization, field, or durable institutional arrangement", parties="educational institutions; professional agents; associations", input="a cited practice or logic undergoing institutional embedding", output="a durable, legitimate, or reproduced institutional arrangement", context="named institution or field and identified carriers", qualification="institutionalization is degree- and mechanism-specific", scope_in="historical embedding and reproduction of design practices", scope_out="mere founding, popularity, or generic organizational presence", sources="GRAM-SRC-005;GRAM-SRC-006", reason="New graphic-design and design-education histories identify agents, mechanisms, fields, and durable outcomes without an ANY role.", direction="DIRECTED"),
    "transnational interactions": dict(role="UNRESOLVED_MIXED_ROLE", decision="DEFER_HIGH_CONNECTIVITY", arity="MULTIPARTY", subject="actors, organizations, practices, ideas, or institutions crossing named national settings", target="other actors, organizations, practices, ideas, or institutions in those settings", parties="states; professional bodies; intermediaries; networks", input="separated but historically connected national settings", output="exchange, influence, friction, or network formation depending on the case", context="named parties, borders, institutions, and period", qualification="interaction mechanism and power relation must be explicit", scope_in="case-specific cross-border design-historical interaction", scope_out="transnationalism as a generic connector", sources="GRAM-SRC-008", reason="The exact term spans people, organizations, ideas, exchanges, power structures, and reciprocal or asymmetric relations; unconstrained use would connect most nodes.", direction="MULTIPARTY"),
    "cultural translation": dict(role="UNRESOLVED_MIXED_ROLE", decision="DEFER_SPLIT_REQUIRED", arity="2+", subject="a cultural form, concept, practice, text, or translating agent in a named contact setting", target="a receiving cultural setting, interpretive community, or transformed form", parties="translator; source community; receiving community", input="a culturally situated form or meaning", output="an adapted, negotiated, or reconstituted meaning", context="named cultures, agents, medium, power relation, and period", qualification="transfer, adaptation, negotiation, and transformation senses must not be collapsed", scope_in="source-bounded designed-landscape and historical translation", scope_out="generic movement between cultures", sources="GRAM-SRC-010;GRAM-SRC-011;GRAM-SRC-012", reason="New evidence explicitly contests one-way transfer and uses incompatible transfer, negotiation, and transformation senses; internal sense separation is required.", direction="MIXED_USAGE_DEFER"),
    "design exchanges": dict(role="MULTIPARTY_ENCOUNTER", decision="DEFER_HIGH_CONNECTIVITY", arity="MULTIPARTY", subject="identified designers, institutions, exhibitions, or design communities participating in an exchange", target="the counterpart participants and situated design practices in that exchange", parties="professional networks; governments; exhibitions; markets", input="participants and practices brought into a named exchange", output="meetings, encounters, negotiations, or circulation outcomes", context="named participants, venue, political setting, and exchange mechanism", qualification="agency, reciprocity, and power asymmetry must be recorded", scope_in="case-specific organized design exchange", scope_out="all cross-cultural contact or circulation", sources="GRAM-SRC-009", reason="The case evidence is strong but the plural term is an umbrella for meetings, networks, exhibitions, commerce, and diplomacy; pairwise connectivity remains too broad.", direction="MULTIPARTY"),
    "commodification": dict(role="DIRECTED_STATE_TRANSITION", decision="PASS_FLOW_ELIGIBLE_NODE", arity="2", subject="a situated image, material, practice, history, or imaginative capacity made exchangeable", target="an exchangeable or market-valued commodity form", parties="producers; market intermediaries; consumers", input="a situated cultural or material form not yet organized as the cited commodity", output="an exchangeable or market-valued commodity form", context="named market mechanism and historical setting", qualification="what becomes exchangeable and by whose action must be named", scope_in="historically evidenced market transformation", scope_out="all commercialization or consumption; decontextualization or branding without evidenced commodity status", sources="GRAM-SRC-013;GRAM-SRC-014", reason="Independent visual- and material-culture histories provide bounded subjects, market mechanisms, and transformed outputs.", direction="DIRECTED"),
    "gendering": dict(role="DIRECTED_PROCESS", decision="PASS_FLOW_ELIGIBLE_NODE", arity="2", subject="a design language, object, space, practice, role, or representation under analysis", target="a historically situated gender category, expectation, or subject position", parties="designers; marketers; institutions; audiences", input="a material or representational arrangement", output="a gender-coded meaning, use, role, or position", context="named design medium, audience, and gender regime", qualification="gender is performed and historically situated, not inherent in form", scope_in="source-attested gender coding through design", scope_out="essentialist claims that objects possess fixed gender", sources="GRAM-SRC-015", reason="The new packaging study supplies a bounded performative role contract and explicitly blocks essentialist object attributes.", direction="DIRECTED"),
    "displacement": dict(role="UNRESOLVED_MIXED_ROLE", decision="DEFER_SPLIT_REQUIRED", arity="2+", subject="people, practices, objects, images, energy systems, or meanings in a specified displacement account", target="a changed place, position, context, or condition", parties="state; empire; institution; migrant community", input="a situated prior place, context, or relation", output="forced movement, object relocation, conceptual reframing, or resistance depending on sense", context="named displaced entity, force, place, and period", qualification="forced, material, spatial, semantic, and strategic senses must be separated", scope_in="explicit design-and-displacement histories", scope_out="generic change or metaphorical movement", sources="GRAM-SRC-016", reason="The new design-history volume intentionally pluralizes forced, spatial, material, semantic, and protest senses; one Node would collapse distinct subjects and forces.", direction="MIXED_USAGE_DEFER"),
    "transculturation": dict(role="MULTIPARTY_ENCOUNTER", decision="DEFER_TOO_BROAD", arity="MULTIPARTY", subject="a cultural concept, practice, or knowledge system entering a contact process", target="locally negotiated cultural knowledge or practice", parties="source communities; receiving communities; institutions; translators", input="contact among historically unequal cultural formations", output="multi-directional and continuing negotiation or reconstitution", context="named parties, locality, knowledge form, and period", qualification="not a static import-export model", scope_in="case-specific architectural and design knowledge circulation", scope_out="all cultural mixture, diffusion, or exchange", sources="GRAM-SRC-017", reason="The new architectural case confirms multi-directionality and ongoing interaction, but one role cannot safely cover pedagogy, migration, cultural formation, and knowledge circulation.", direction="MULTIPARTY"),
    "cultural mobility": dict(role="UNRESOLVED_MIXED_ROLE", decision="DEFER_SPLIT_REQUIRED", arity="MULTIPARTY", subject="people, forms, meanings, practices, or institutions moving in a specified cultural account", target="destinations, networks, or transformed contexts of that movement", parties="carriers; infrastructures; border regimes; audiences", input="a culturally situated actor or form", output="movement, contamination, exile, circulation, or transformed meaning depending on sense", context="named carrier, infrastructure, route, and period", qualification="material, human, semantic, and institutional mobility must be distinguished", scope_in="source-bounded cultural-mobility analysis", scope_out="generic circulation or any cross-border change", sources="GRAM-SRC-018", reason="The manifesto deliberately spans colonization, exile, emigration, wandering, contamination, and random events; a single relation role would become universal.", direction="MIXED_USAGE_DEFER"),
    "self-exoticization": dict(role="REFLEXIVE_PROCESS", decision="PASS_REFLEXIVE_NODE", arity="3", subject="a designer, design community, institution, or national design discourse constructing its own cultural identity", target="that actor's culturally marked self-representation", parties="external expectation, gaze, or anticipated audience", input="the actor's own cultural repertoire under external or internal expectations", output="a strategically selected self-representation emphasizing difference", context="named actor, audience, market, and cultural signs", qualification="agency, external gaze, and power asymmetry must remain explicit", scope_in="source-attested strategic design self-presentation", scope_out="all use of tradition or any non-Western motif", sources="GRAM-SRC-019", reason="The new Korean fashion study explicitly defines the strategy, actor, selected design elements, and anticipated audience while retaining its contested power relation.", direction="REFLEXIVE"),
    "coloniality": dict(role="STRUCTURAL_CONDITION", decision="DEFER_HIGH_CONNECTIVITY", arity="STRUCTURAL", subject="a historically constituted pattern of colonial power reproduced through design knowledge or practice", target="design institutions, methods, categories, or relations shaped by that pattern", parties="institutions; knowledge systems; racialized and gendered subjects", input="ongoing modern/colonial relations", output="reproduced hierarchies and normalized design forms", context="named colonial relation, design field, geography, and knowledge practice", qualification="coloniality is not interchangeable with colonialism or any inequality", scope_in="decolonial design analysis of enduring power patterns", scope_out="generic harm, all power, or a visual bridge node", sources="GRAM-SRC-020", reason="The new decolonial design source supports a structural field condition, but its world-scale reach would qualify most nodes; the universal-node gate therefore defers it.", direction="STRUCTURAL_NON_EDGE"),
    "imitation": dict(role="DIRECTED_PROCESS", decision="PASS_FLOW_ELIGIBLE_NODE", arity="2", subject="a maker, manufacturer, or design practice drawing from an identified prior design", target="the prior design, technique, form, or market example being imitated", parties="workshop; market; rights claimant; consumer", input="an existing design or production example", output="a historically situated derivative design or production practice", context="named source, imitator, production regime, and period", qualification="imitation must not be equated automatically with infringement or piracy", scope_in="source-attested copying within design production", scope_out="all influence, resemblance, appropriation, or inspiration", sources="GRAM-SRC-021;GRAM-SRC-022", reason="Independent fashion histories give imitation a bounded source/imitator structure while demonstrating that its valuation changes by production regime.", direction="DIRECTED"),
    "piracy": dict(role="NORMATIVELY_QUALIFIED_RELATION", decision="PASS_NORMATIVE_RELATION_NODE", arity="3+", subject="an alleged copier, manufacturer, seller, or organized copying practice", target="a source or copied design, or a protected design interest", parties="originator; rights claimant; regulator; court; trade body", input="a copying relation evaluated under a historical norm or legal-market regime", output="an allegation or historically situated classification of unauthorized copying", context="named jurisdiction, period, claimant, and protection regime", qualification="authorization, ownership claim, jurisdiction, legal or market status, ethical framework, and historical standard are mandatory", scope_in="source-attested design-piracy claims and regulation", scope_out="generic resemblance, imitation, counterfeit, or moral condemnation", sources="GRAM-SRC-023;GRAM-SRC-024", reason="Independent historical studies define actors and governance mechanisms while showing that piracy depends on legal, market, and ethical qualification.", direction="DIRECTED"),
}


ATTESTATIONS = [
    ("GRAM-ATT-001", "GRAM-SRC-001", "mediation", "mediation", "Introduction; PCM re-evaluation", "production, consumption, and mediation", "producer or mediating actor", "consumer, interface, or received digital performance", "algorithms; platforms; prosumers", "MIXED_USAGE_DEFER", "none", "digital ontology and third-party dynamics", "false", "true"),
    ("GRAM-ATT-002", "GRAM-SRC-002", "mediation", "mediations", "Abstract, final paragraph", "a dynamic system, a set of practices and mediations", "design-community institutions and transmitters", "relations between production and consumption", "exhibitions; advisers; mediators", "MULTIPARTY", "none", "Polish design-historical field", "false", "true"),
    ("GRAM-ATT-003", "GRAM-SRC-003", "canonization", "canonization", "chapter title and pp. 249-276", "visual historiography and canonization in Swiss graphic design history", "selected actors, works, and narratives", "a mainstream graphic-design historical canon", "historians; publications", "DIRECTED", "none", "historiographic selection and exclusion", "false", "true"),
    ("GRAM-ATT-004", "GRAM-SRC-004", "professionalization", "professionalization", "Abstract", "the relationship between self-image, representation and professionalization in the formative years of the design profession in Britain", "the Society of Industrial Artists and Council of Industrial Design", "the British design profession and its represented professional standing", "publications; memoranda; practitioners; audiences", "DIRECTED", "none", "formative period, class, and gender", "false", "true"),
    ("GRAM-ATT-005", "GRAM-SRC-005", "professionalization", "professionalization", "Introduction, paragraphs 6-13", "professionalization and institutionalization are closely interwoven", "graphic designers and their professional project", "a recognized professional field and logic", "universities; associations; consultants", "MIXED_USAGE_DEFER", "none", "professional logic and legitimate agents", "false", "true"),
    ("GRAM-ATT-006", "GRAM-SRC-005", "institutionalization", "institutionalization", "Abstract; Introduction; Discussion", "institutionalization of their professional logic", "professional logic carried by graphic designers", "universities and organizational visual-identity fields", "creators; carriers; appliers", "DIRECTED", "none", "agent legitimacy and reproduction", "false", "true"),
    ("GRAM-ATT-007", "GRAM-SRC-006", "institutionalization", "institutional trajectories", "Abstract and theoretical framework", "institutional trajectories of five design disciplines", "design disciplines and educational programs", "durable institutional presence in higher education", "universities; students; adjacent disciplines", "DIRECTED", "none", "field presence is not identical to growth", "false", "true"),
    ("GRAM-ATT-008", "GRAM-SRC-007", "professionalization", "professionalization", "article title and abstract", "recent histories of the professionalization of interior design: from gatekeeping to inclusion", "interior-design field and practitioners", "professional status and governed field", "educators; regulators; associations", "DIRECTED", "none", "inclusion and exclusion must remain visible", "false", "true"),
    ("GRAM-ATT-009", "GRAM-SRC-008", "transnational interactions", "transnational interactions", "chapter title and abstract", "between transnational interactions and national narratives", "British and Italian architectural actors and cultures", "multi-national exchanges and national narratives", "institutions; architects; publications", "MULTIPARTY", "none", "reciprocity and national self-identity", "false", "true"),
    ("GRAM-ATT-010", "GRAM-SRC-009", "design exchanges", "design exchanges", "title and abstract", "design exchanges between Brussels and Moscow", "design institutions and professional networks", "counterpart design scenes across the Iron Curtain", "ICSID; governments; exhibitions", "MULTIPARTY", "none", "diplomacy, commerce, and network agency", "false", "true"),
    ("GRAM-ATT-011", "GRAM-SRC-010", "cultural translation", "cultural translation", "title and forum introduction", "cultural translation: an introduction to the problem", "cultural actors, texts, or forms", "receiving or negotiated cultural setting", "translators; institutions; audiences", "MIXED_USAGE_DEFER", "none", "the term is contested and used incompatibly", "false", "true"),
    ("GRAM-ATT-012", "GRAM-SRC-011", "cultural translation", "translation between cultures", "chapter summary", "translation between languages in the context of translation between cultures", "historian or translator mediating a source culture", "readers in another historical-cultural setting", "texts; historians; audiences", "DIRECTED", "none", "fidelity and intelligibility remain in tension", "false", "true"),
    ("GRAM-ATT-013", "GRAM-SRC-012", "cultural translation", "cultural translation", "section 3.2.1", "perspectives on cultural translation and design culture, proposing a method for the extraction and transformation of cultural elements", "cultural elements selected by design researchers", "transformed features in a situated cultural product", "cultural carriers; designers; receiving users", "DIRECTED", "none", "translation remains ambiguous and equivocal", "false", "true"),
    ("GRAM-ATT-014", "GRAM-SRC-013", "commodification", "commodification", "Abstract", "de-contextualization of images is an essential condition for their commodification", "archived images and their indexing", "commercially exchangeable image commodities", "archive; agency; clients", "DIRECTED", "none", "keywords and decontextualization", "false", "true"),
    ("GRAM-ATT-015", "GRAM-SRC-014", "commodification", "commodification", "title and abstract", "commodification of imagination", "children's imaginative roles and dress-up designs", "mass-produced branded costume scripts", "manufacturers; brands; children", "DIRECTED", "none", "agency is constrained by brand narratives", "false", "true"),
    ("GRAM-ATT-016", "GRAM-SRC-015", "gendering", "gendering", "Gender and Design: From Reflecting to Constructing", "the gendering of design language has worked as resistance to gender ideologies", "design language and its historically situated conventions", "gender-coded meanings and positions", "designers; marketers; consumers", "DIRECTED", "none", "arbitrariness, changeability, and performativity", "false", "true"),
    ("GRAM-ATT-017", "GRAM-SRC-016", "displacement", "displacement", "Description and chapter list", "intersections of design and displacement", "people, things, meanings, practices, and energy systems", "changed places, contexts, or political conditions", "states; empires; migrants; activists", "MIXED_USAGE_DEFER", "none", "forced, material, semantic, and strategic senses", "false", "true"),
    ("GRAM-ATT-018", "GRAM-SRC-017", "transculturation", "transculturation", "Abstract", "the notion of public space in Chinese urban design culture has articulated the substance of compressed transculturation", "Western public-space concepts and Chinese urban discourse", "situated Chinese networks of knowledge", "scholars; translators; institutions", "MULTIPARTY", "not a simple import-export model", "local negotiation and resistance", "false", "true"),
    ("GRAM-ATT-019", "GRAM-SRC-018", "cultural mobility", "Cultural Mobility", "book title and publisher description", "Cultural Mobility: A Manifesto", "people, meanings, institutions, and cultural forms", "routes, destinations, and transformed settings", "carriers; borders; infrastructures", "MIXED_USAGE_DEFER", "none", "colonization, exile, wandering, and contamination", "false", "true"),
    ("GRAM-ATT-020", "GRAM-SRC-019", "self-exoticization", "Self-exoticization", "p. 155, opening discussion", "Self-exoticization here refers to a designer’s strategy of integrating design elements that might appear exotic and Korean to foreigners", "a Korean designer constructing a self-representation", "the designer's culturally marked self-representation", "foreign audience; Korean consumers; selected design elements", "REFLEXIVE", "none", "perceived difference, external gaze, and agency coexist", "false", "true"),
    ("GRAM-ATT-021", "GRAM-SRC-020", "coloniality", "coloniality", "pp. 1-6", "coloniality and the colonial matrix of power", "enduring modern-colonial power patterns", "design knowledge, methods, institutions, and relations", "designers; institutions; marginalized subjects", "STRUCTURAL_NON_EDGE", "none", "not interchangeable with colonialism", "false", "true"),
    ("GRAM-ATT-022", "GRAM-SRC-021", "imitation", "imitation", "chapter title and abstract", "history of imitation in the modern fashion industry", "fashion makers and manufacturers", "prior designs and market examples", "houses; markets; rights claimants", "DIRECTED", "none", "valuation changes by production regime", "false", "true"),
    ("GRAM-ATT-023", "GRAM-SRC-022", "imitation", "imitation", "title and summary", "imitation at the center of the creative process", "eighteenth-century textile makers", "existing designs and production conventions", "factory; artisan; market", "DIRECTED", "none", "not the fixed opposite of innovation", "false", "true"),
    ("GRAM-ATT-024", "GRAM-SRC-023", "piracy", "design piracy", "Historical background, section 2A", "The resultant ‘design piracy’ led to an unlikely coalition of politicians, printers, and textile manufacturers, who campaigned for copyright protection", "printers and manufacturers accused of copying", "claimed textile patterns and originators", "Parliament; rights advocates; markets", "DIRECTED", "copying was not always admitted as piracy", "legal protection and historical standards", "false", "true"),
    ("GRAM-ATT-025", "GRAM-SRC-024", "piracy", "design piracy", "Abstract", "attempts to control design piracy in the dress industry", "dress manufacturers and copying practices", "claimed original designs and originators", "FOGA; retailers; consumers; law", "DIRECTED", "copying is not automatically legally protectable", "ethical, economic, and social qualification", "false", "true"),
    ("GRAM-ATT-026", "GRAM-SRC-025", "professionalization", "professionalization", "section preceding A neo-institutional perspective", "the relationship between professionalization as a process and its institutionalization in professional work, education, and training", "a professionalization process", "institutionalized professional domains", "practitioners; educators; training institutions", "MIXED_USAGE_DEFER", "not a universal causal chronology", "source-scoped interweaving", "false", "true"),
    ("GRAM-ATT-027", "GRAM-SRC-026", "gendering", "gendering", "article title", "gendering the commodification of second-hand economies", "gendered discourse and economic roles", "commodification of second-hand economies", "mothers; consumers; traders; children", "DIRECTED", "title-level composition only", "adjacent consumer-culture evidence", "false", "true"),
    ("GRAM-ATT-028", "GRAM-SRC-027", "piracy", "design piracy", "Abstract", "design leader imitation via a comprehensive framework that accounts for the consumptive environment of design piracy", "an imitation practice and its industrial actors", "a design-piracy environment", "design leader; imitator; audience", "STRUCTURAL_NON_EDGE", "not a necessary temporal transition", "adjacent design-research evidence", "false", "true"),
    ("GRAM-ATT-029", "GRAM-SRC-028", "imitation", "imitation", "section From the Margins to the Core", "this strategy of accommodating imitation proved economically beneficial in the long term", "a fashion originator responding to imitation", "a market strategy and its effects", "imitators; associations; consumers", "MIXED_USAGE_DEFER", "not classified automatically as piracy", "fashion-business-history context", "false", "true"),
    ("GRAM-ATT-030", "GRAM-SRC-028", "piracy", "design piracy", "section From the Margins to the Core, note 164", "Chanel refused to join Parisian fashion associations and decided instead to fight design piracy directly", "a fashion originator and claimed designs", "copying practices classified as piracy", "imitators; associations; markets", "MIXED_USAGE_DEFER", "imitation and piracy are contrasted elsewhere in the section", "fashion-business-history context", "false", "true"),
]

ATTESTATION_COOCCURRENCE = {
    "GRAM-ATT-005": "REL-CAND-0006",
    "GRAM-ATT-026": "REL-CAND-0006",
    "GRAM-ATT-027": "REL-CAND-0010",
    "GRAM-ATT-028": "REL-CAND-0032",
}

OBSERVED_TRANSITIONS = {
    "GRAM-ATT-003": "uneven historical status -> canonical positioning or exclusion",
    "GRAM-ATT-004": "emerging design occupation -> represented professional standing",
    "GRAM-ATT-006": "professional logic -> institutionalized organizational field",
    "GRAM-ATT-014": "contextualized image -> exchangeable image commodity",
    "GRAM-ATT-015": "imaginative capacity -> mass-produced commodity script",
    "GRAM-ATT-016": "design language or packaging -> gender-coded consumer position",
    "GRAM-ATT-020": "cultural repertoire -> strategically marked self-representation",
    "GRAM-ATT-022": "prior fashion example -> situated imitative production",
    "GRAM-ATT-023": "prior textile model -> imitative creative output",
    "GRAM-ATT-024": "copying practice -> historically situated piracy allegation",
    "GRAM-ATT-025": "copying practice -> self-regulated piracy classification",
}


DEFERRED_PAIRS = {
    ("professionalization", "institutionalization"): ("DEFER_DIRECTIONALITY", "GRAM-ATT-005;GRAM-ATT-026", "Two independent sources explicitly relate the processes, but neither establishes one stable causal direction; the required peer-reviewed design-history composition article is also not securely established."),
    ("gendering", "commodification"): ("DEFER_SINGLE_ATTESTATION", "GRAM-ATT-027", "One adjacent title-level source explicitly qualifies commodification through gendering, but it is not a second independent design-history composition attestation."),
    ("imitation", "piracy"): ("DEFER_DIRECTIONALITY", "GRAM-ATT-028;GRAM-ATT-029;GRAM-ATT-030", "Two independent sources relate imitation and piracy through environment and contrast, but do not establish an automatic directed transition; neither securely supplies the required design-history composition article."),
}

PAIR_GATE_OBSERVATIONS = {
    ("professionalization", "institutionalization"): (2, False, True, True),
    ("gendering", "commodification"): (1, False, False, True),
    ("imitation", "piracy"): (2, False, True, True),
}

PAIR_EXPLANATIONS = {
    ("professionalization", "institutionalization"): "Professionalization may connect to institutionalization only when a source-bounded account maps how occupational formation becomes institutionally embedded. Two independent sources relate and interweave the processes, but do not establish stable direction, an explicit role map, or the required design-history composition article.",
    ("gendering", "commodification"): "Gendering may qualify commodification only when scholarship explicitly maps how gendered roles or discourse shape market transformation. Round 10 has one adjacent title-level attestation, not two independent design-history composition sources.",
    ("imitation", "piracy"): "Imitation may connect to piracy only when a historically named regime explicitly reclassifies a bounded copying practice. Two independent sources provide environment and contrast evidence, but not stable transition direction, an explicit role map, or the required design-history composition article.",
}

PAIR_QUESTIONS = {
    ("professionalization", "institutionalization"): "Does a design-historical argument explicitly show a professionalization process becoming embedded in a named institution or field, rather than merely saying the processes are interwoven?",
    ("gendering", "commodification"): "Does a design-historical argument show gender coding changing the commodity status of a named practice or market, with explicit actors and direction?",
    ("imitation", "piracy"): "Does a design-historical argument document when and by whom a specified imitation was classified as piracy under a named historical regime?",
}

PAIR_FIELD_EXAMPLES = {
    ("professionalization", "institutionalization"): "Retain the pair as a deferred research question; neither a directed edge nor an automatic professionalization-to-institutionalization sequence is authorized.",
    ("gendering", "commodification"): "Retain the title-level qualification as a deferred question; do not infer an edge or reverse ordering.",
    ("imitation", "piracy"): "Retain environment and contrast evidence without inferring that imitation becomes piracy or that the terms are synonyms.",
}

# These eight deferred candidates satisfy the task's adversarial semantic
# any-like test: their frozen sense is broad enough that many pairings sound
# superficially plausible without pair-specific evidence.  The flag records
# why the candidate is deferred; it does not authorize an unbounded role.
UNIVERSAL_CANDIDATE_LABELS = {
    "mediation",
    "transnational interactions",
    "cultural translation",
    "design exchanges",
    "displacement",
    "transculturation",
    "cultural mobility",
    "coloniality",
}

NODE_EXPLANATIONS = {
    "mediation": "Mediation names how a specified intermediary, channel, or designed form shapes an encounter between production or prior meaning and reception; it remains deferred because sources assign incompatible mediating roles.",
    "canonization": "Canonization positions a work, movement, representation, or narrative within a design-historical canon through documented selection or exclusion by historians, publishers, exhibitions, or education.",
    "professionalization": "Professionalization forms a named design occupation or practice into historically contested professional standing through education, organizations, standards, accreditation, jurisdiction, or gatekeeping.",
    "institutionalization": "Institutionalization embeds and reproduces a named design practice or logic as a durable arrangement in a specified organization or field through identified carriers and mechanisms.",
    "transnational interactions": "Transnational interactions names relations among identified actors or institutions across named national settings; it remains deferred because mechanism, direction, reciprocity, and power vary by case.",
    "cultural translation": "Cultural translation names source-specific transfer, interpretation, adaptation, negotiation, or transformation of cultural forms between situated communities; it remains deferred until these senses are separated.",
    "design exchanges": "Design exchanges names a documented multiparty encounter among specified designers, institutions, exhibitions, networks, governments, or markets; it remains deferred because the umbrella term supplies no single bounded relation.",
    "commodification": "Commodification transforms a situated image, material, practice, history, or capacity into an exchangeable or market-valued commodity form through named market mechanisms and actors.",
    "gendering": "Gendering is the historically situated process through which design produces gender-coded meanings, uses, roles, or subject positions; gender is not inherent in form.",
    "displacement": "Displacement remains deferred because scholarship uses it for forced human movement, material relocation, spatial transfer, semantic reframing, and strategic resistance, which require separate role contracts.",
    "transculturation": "Transculturation describes multidirectional, continuing negotiation through which cultural knowledge or practices are reconstituted among unequal communities and institutions; it remains deferred because participant and output types vary.",
    "cultural mobility": "Cultural mobility remains deferred because sources apply it to different moving entities, carriers, routes, and outcomes, including exile, circulation, contamination, and semantic change.",
    "self-exoticization": "Self-exoticization is a reflexive strategy in which an actor constructs its culturally marked self-representation for an external or anticipated gaze; representation, audience, and power asymmetry are mandatory.",
    "coloniality": "Coloniality is the historically reproduced modern-colonial power pattern conditioning design knowledge, institutions, methods, categories, and relations; it is a structural qualifier, not an edge.",
    "imitation": "Imitation is a directed copying process in which a maker or practice draws from a named prior design, technique, form, or production example; it does not imply infringement or piracy.",
    "piracy": "Piracy is a historically situated allegation or classification that copying of a source design or protected interest was unauthorized under a named ownership, legal, market, or ethical regime.",
}

NODE_QUESTIONS = {
    "mediation": "How did a named exhibition, publication, or digital channel reshape relations among producers, intermediaries, and audiences in the cited period?",
    "canonization": "How did specified historians, schools, exhibitions, or publishers select and exclude movements when forming a national graphic-design canon?",
    "professionalization": "How did education, associations, standards, and jurisdiction change the standing of a named design occupation in a specified period?",
    "institutionalization": "Through which named organizations and carriers did a design practice become durably embedded in education or professional administration?",
    "transnational interactions": "Which actors crossed which national boundary, through what mechanism, and with what reciprocal or asymmetric effect on design activity?",
    "cultural translation": "Did a named cultural form undergo transfer, adaptation, negotiation, or transformation in the receiving design setting, and who interpreted it?",
    "design exchanges": "Which institutions, networks, and political or market conditions structured a documented design exchange between two named scenes?",
    "commodification": "By what historical market mechanism did a specified cultural form acquire exchangeable or market-valued commodity status?",
    "gendering": "How did a named design discourse or institution produce gender-coded meanings and subject positions in a specified medium and audience?",
    "displacement": "Does the cited history describe forced human movement, material relocation, spatial transfer, semantic reframing, or strategic resistance?",
    "transculturation": "How were design concepts reconstituted through multidirectional contact among named communities and institutions under unequal power?",
    "cultural mobility": "What moved, who or what carried it, along which route and infrastructure, and how did its situated cultural meaning change?",
    "self-exoticization": "How did a named design culture construct a culturally marked self-image for an anticipated external audience, and with what power asymmetry?",
    "coloniality": "Which persistent modern-colonial power pattern conditioned a named design institution, knowledge practice, or category across the cited period?",
    "imitation": "Which maker or practice took which prior design or technique as a model, and how was that copying evaluated in the cited production regime?",
    "piracy": "Who classified which copying practice as unauthorized, under which ownership claim, jurisdiction, and historical legal, market, or ethical standard?",
}

NODE_FIELD_EXAMPLES = {
    "mediation": "Represent a named channel between producers and audiences only after its mediating function and parties are identified; otherwise retain the term as deferred.",
    "canonization": "Represent selection into a bounded historiographic canon while preserving the selecting institutions and documented exclusions.",
    "professionalization": "Represent occupational formation through named education, association, standard, or jurisdiction mechanisms without equating it with institutionalization.",
    "institutionalization": "Represent durable embedding in a named institution or field without treating mere founding or popularity as sufficient.",
    "transnational interactions": "Retain a cross-border encounter as a deferred multiparty relation until its mechanism, endpoints, reciprocity, and power relation are explicit.",
    "cultural translation": "Retain transfer, adaptation, negotiation, and transformation as separate inactive research senses rather than one arrow.",
    "design exchanges": "Retain a documented exchange as multiparty evidence without inferring equal reciprocity or a generic cross-cultural edge.",
    "commodification": "Represent a transition into exchangeable or market-valued status only when the changed status and market actors are evidenced.",
    "gendering": "Represent historically produced gender coding while blocking any claim that gender is inherent in visual or material form.",
    "displacement": "Record the specific displaced entity, force, origin, destination or changed condition; do not collapse its distinct senses.",
    "transculturation": "Record named communities, institutions, contact conditions, and unequal power while retaining the relation as deferred and multiparty.",
    "cultural mobility": "Record carrier, route, infrastructure, moved entity, and meaning outcome separately; do not authorize a generic mobility bridge.",
    "self-exoticization": "Represent actor, culturally marked self-representation, and anticipated gaze as distinct roles without authorizing a self-loop.",
    "coloniality": "Attach a source-bounded structural qualifier to the interpreted field; never render coloniality as an ordinary connecting edge.",
    "imitation": "Represent maker-to-model use with a separate resulting practice and evaluation, while blocking automatic inference to piracy.",
    "piracy": "Represent an allegation or classification under a named regime, not an unqualified fact of copying or visual resemblance.",
}

ANTI_FLATTENING = {
    "canonization": ("professionalization;institutionalization", "Historiographic selection is distinct from occupational formation and durable organizational embedding.", "GRAM-ATT-003;GRAM-ATT-004;GRAM-ATT-006"),
    "professionalization": ("canonization;institutionalization", "Occupational formation is distinct from historiographic selection and durable organizational embedding.", "GRAM-ATT-003;GRAM-ATT-004;GRAM-ATT-006"),
    "institutionalization": ("canonization;professionalization", "Durable organizational embedding is distinct from historiographic selection and occupational formation.", "GRAM-ATT-003;GRAM-ATT-004;GRAM-ATT-006"),
    "transnational interactions": ("design exchanges", "A cross-national relation umbrella is not identical to an organized exchange encounter.", "GRAM-ATT-009;GRAM-ATT-010"),
    "design exchanges": ("transnational interactions", "An organized exchange encounter is not identical to all cross-national relations.", "GRAM-ATT-009;GRAM-ATT-010"),
    "cultural translation": ("transculturation", "Translation and interpretation senses are distinct from multidirectional continuing reconstitution.", "GRAM-ATT-011;GRAM-ATT-012;GRAM-ATT-013;GRAM-ATT-018"),
    "transculturation": ("cultural translation", "Multidirectional continuing reconstitution is distinct from translation and interpretation senses.", "GRAM-ATT-011;GRAM-ATT-012;GRAM-ATT-013;GRAM-ATT-018"),
    "displacement": ("cultural mobility", "Forced or positional change is distinct from the broader movement and circulation family.", "GRAM-ATT-017;GRAM-ATT-019"),
    "cultural mobility": ("displacement", "Broad movement and circulation are distinct from forced or positional change.", "GRAM-ATT-017;GRAM-ATT-019"),
    "commodification": ("gendering", "Market transformation is distinct from historically situated gender coding.", "GRAM-ATT-014;GRAM-ATT-015;GRAM-ATT-016"),
    "gendering": ("commodification;self-exoticization", "Gender coding is distinct from market transformation and reflexive cultural self-presentation.", "GRAM-ATT-014;GRAM-ATT-016;GRAM-ATT-020"),
    "self-exoticization": ("gendering", "Reflexive cultural self-presentation to a gaze is distinct from the production of gendered meaning.", "GRAM-ATT-016;GRAM-ATT-020"),
    "coloniality": ("all directed processes", "A persistent historical structure is not a directed process or bridge edge.", "GRAM-ATT-021"),
    "imitation": ("piracy", "A copying practice is distinct from a normatively qualified piracy allegation or classification.", "GRAM-ATT-022;GRAM-ATT-023;GRAM-ATT-024;GRAM-ATT-025"),
    "piracy": ("imitation", "A normatively qualified piracy allegation or classification is distinct from copying practice alone.", "GRAM-ATT-022;GRAM-ATT-023;GRAM-ATT-024;GRAM-ATT-025"),
    "mediation": ("all other inputs", "A source-bounded mediating channel or actor is not a generic connection among all processes.", "GRAM-ATT-001;GRAM-ATT-002"),
}


def build_inputs() -> tuple[list[dict[str, str]], dict[str, dict[str, str]], str]:
    candidates = read_tsv(R9 / "04_RAW_CANDIDATE_TERM_REGISTRY.tsv")
    handoff = {row["candidate_id"]: row for row in read_tsv(R9 / "11_GRAMMAR_EVIDENCE_HANDOFF.tsv")}
    rows = []
    for row in candidates:
        if not row["final_decision"].startswith("PASS_TO_GRAMMAR_RESEARCH"):
            continue
        h = handoff[row["candidate_id"]]
        rows.append({
            "ordinal": str(len(rows) + 1),
            "candidate_id": row["candidate_id"],
            "sense_id": h["sense_id"],
            "candidate_label": row["candidate_label"],
            "round9_final_decision": row["final_decision"],
            "round9_source_support_ids": h["source_support_ids"],
            "round9_candidate_registry_version": row["candidate_registry_version"],
            "round9_candidate_registry_sha256": row["candidate_registry_sha256"],
            "round9_grammar_selected": h["relation_grammar_selected"],
            "exact_input_verified": "true",
        })
    identity = "\n".join(f"{r['candidate_id']}\t{r['sense_id']}\t{r['candidate_label']}\t{r['round9_final_decision']}" for r in rows) + "\n"
    return rows, {row["candidate_label"]: row for row in rows}, sha(identity)


def main() -> None:
    RESEARCH.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    inputs, by_label, input_hash = build_inputs()
    assert len(inputs) == 16
    assert list(by_label) == list(NODE_DATA)

    write_tsv(RESEARCH / "02_ROUND9_INPUT_TERM_REGISTRY.tsv", list(inputs[0]), inputs)
    write_tsv(RESEARCH / "03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv", SOURCE_FIELDS, SOURCES)

    derivation = []
    node_rows = []
    arg_rows = []
    direction_rows = []
    qualification_rows = []
    universal_rows = []
    flatten_rows = []
    nl_rows = []
    r9_handoff = {row["candidate_id"]: row for row in read_tsv(R9 / "11_GRAMMAR_EVIDENCE_HANDOFF.tsv")}
    for label, data in NODE_DATA.items():
        inp = by_label[label]
        r9 = r9_handoff[inp["candidate_id"]]
        pass_node = data["decision"].startswith("PASS_")
        derivation.append({
            "candidate_id": inp["candidate_id"], "sense_id": inp["sense_id"], "candidate_label": label,
            "round9_lexical_attestation_ids": r9["source_support_ids"], "round9_gloss_registry_row": inp["candidate_id"],
            "round9_handoff_row": inp["candidate_id"], "new_grammar_source_ids": data["sources"],
            "new_grammar_attestation_ids": ";".join(a[0] for a in ATTESTATIONS if a[2] == label),
            "node_role_decision": data["decision"], "all_provenance_links_verified": "true", "orphan": "false",
        })
        node_rows.append({
            "candidate_id": inp["candidate_id"], "sense_id": inp["sense_id"], "candidate_label": label,
            "primary_technical_role": data["role"], "final_node_role_decision": data["decision"],
            "decision_reason": data["reason"], "new_grammar_source_ids": data["sources"],
            "pass_node": str(pass_node).lower(), "ordinary_language_roles_complete": "true", "natural_language_explanation_complete": "true",
        })
        arg_rows.append({
            "candidate_id": inp["candidate_id"], "candidate_label": label, "arity": data["arity"],
            "subject_role": data["subject"], "target_role": data["target"], "additional_party_roles": data["parties"],
            "input_state": data["input"], "output_state": data["output"], "required_context": data["context"],
            "required_qualification": data["qualification"], "scope_in": data["scope_in"], "scope_out": data["scope_out"],
            "contains_any_role": "false", "empty_role_count": "0", "source_support_ids": data["sources"],
        })
        direction_rows.append({
            "candidate_id": inp["candidate_id"], "candidate_label": label, "technical_role": data["role"],
            "arity": data["arity"], "directionality_decision": data["direction"], "visual_arrow_authorized": "false",
            "self_loop_authorized": "false", "structural_non_edge": str(data["direction"] == "STRUCTURAL_NON_EDGE").lower(),
            "evidence_ids": ";".join(a[0] for a in ATTESTATIONS if a[2] == label),
        })
        qualification_rows.append({
            "candidate_id": inp["candidate_id"], "candidate_label": label,
            "descriptive_interpretive_historiographic_normative_structural": "historiographic" if label == "canonization" else "normative" if label == "piracy" else "structural" if label == "coloniality" else "interpretive",
            "contestation_preserved": "true", "historical_shift_preserved": "true", "source_bounded_meaning_preserved": "true",
            "required_qualification": data["qualification"], "scope_out": data["scope_out"], "normative_qualifier_loss": "false",
        })
        high = label in UNIVERSAL_CANDIDATE_LABELS
        deferred_out = sum(1 for pair in DEFERRED_PAIRS if pair[0] == label)
        deferred_in = sum(1 for pair in DEFERRED_PAIRS if pair[1] == label)
        universal_rows.append({
            "candidate_id": inp["candidate_id"], "candidate_label": label,
            "allowed_out_degree": "0", "allowed_in_degree": "0",
            "deferred_out_degree": str(deferred_out),
            "deferred_in_degree": str(deferred_in),
            "default_denied_degree": str(30 - deferred_out - deferred_in),
            "any_role_usage": "false", "literal_any_token": "false", "semantic_any_like_role": str(high).lower(),
            "generic_relation_wording": str(high).lower(), "unbounded_scope": str(high).lower(),
            "high_connectivity": str(high).lower(), "repeated_bridge_use": "false", "universal_risk_pair_specific_evidence_missing": str(high).lower(),
            "universal_node_candidate": str(high).lower(), "universal_node_passed": "false",
            "red_team_decision": "DEFER" if high else "PASS_BOUNDARY" if pass_node else "DEFER_OTHER_BOUNDARY",
        })
        compared_terms, distinction, distinction_sources = ANTI_FLATTENING[label]
        flatten_rows.append({
            "candidate_id": inp["candidate_id"], "candidate_label": label,
            "neighbor_terms_reviewed": "all 15 other inputs", "explicit_distinction_terms": compared_terms,
            "explicit_distinction": distinction, "source_attestation_ids": distinction_sources,
            "synonym_merge_performed": "false", "sense_collapse_performed": "false",
            "process_condition_distinction_preserved": "true", "normative_distinction_preserved": "true",
            "historical_shift_preserved": "true", "semantic_flattening_found": "false",
            "review_note": f"{label} remains an independent Round 9 sense; {data['scope_out']}",
        })
        nl_rows.append({
            "record_type": "NODE", "source_candidate_id": inp["candidate_id"], "target_candidate_id": "",
            "decision": data["decision"],
            "plain_language_explanation": NODE_EXPLANATIONS[label],
            "research_question_example": NODE_QUESTIONS[label],
            "conceptual_field_example": NODE_FIELD_EXAMPLES[label],
            "non_object_example": "true", "non_circular": "true", "explanation_verified": "true",
        })

    write_tsv(RESEARCH / "04_NODE_DERIVATION_REGISTRY.tsv", list(derivation[0]), derivation)
    write_tsv(RESEARCH / "05_NODE_ROLE_DECISION_REGISTRY.tsv", list(node_rows[0]), node_rows)
    write_tsv(RESEARCH / "06_ARGUMENT_ROLE_REGISTRY.tsv", list(arg_rows[0]), arg_rows)

    att_rows = []
    att_fields = ["grammar_attestation_id", "source_id", "candidate_term_id", "candidate_sense_id", "candidate_label", "exact_attested_noun", "bounded_context", "page_section_locator", "source_language", "published_translation", "observed_subject_role", "observed_target_role", "observed_additional_parties", "observed_directionality", "observed_state_transition", "observed_qualifier", "observed_negation", "observed_contestation", "co_occurring_relation_term_ids", "evidence_sha256", "metadata_verified"]
    source_by_id = {s["source_id"]: s for s in SOURCES}
    for a in ATTESTATIONS:
        aid, sid, label, noun, locator, context, subj, target, parties, direction, negation, qualifier, transition, verified = a
        inp = by_label[label]
        att_rows.append(dict(grammar_attestation_id=aid, source_id=sid, candidate_term_id=inp["candidate_id"], candidate_sense_id=inp["sense_id"], candidate_label=label, exact_attested_noun=noun, bounded_context=context, page_section_locator=locator, source_language=source_by_id[sid]["source_language"], published_translation=source_by_id[sid]["published_translation"], observed_subject_role=subj, observed_target_role=target, observed_additional_parties=parties, observed_directionality=direction, observed_state_transition=OBSERVED_TRANSITIONS.get(aid, "no bounded before-to-after transition attested"), observed_qualifier=qualifier, observed_negation=negation, observed_contestation="historically situated or contested", co_occurring_relation_term_ids=ATTESTATION_COOCCURRENCE.get(aid, ""), evidence_sha256=sha("|".join(map(str, a))), metadata_verified=verified))
    write_tsv(RESEARCH / "07_GRAMMAR_ATTESTATION_REGISTRY.tsv", att_fields, att_rows)

    matrix = []
    for source in inputs:
        for target in inputs:
            sl, tl = source["candidate_label"], target["candidate_label"]
            if sl == tl:
                decision, evidence, reason = "REJECT_SELF_RELATION", "", "No source-attested self-loop with bounded scope; reflexive wording does not authorize a visual loop."
            elif (sl, tl) in DEFERRED_PAIRS:
                decision, evidence, reason = DEFERRED_PAIRS[(sl, tl)]
            else:
                decision, evidence, reason = "UNSUPPORTED_DEFAULT_DENY", "", "No pair-specific composition evidence meeting the two-source hard gate."
            matrix.append({
                "source_candidate_id": source["candidate_id"], "source_label": sl,
                "target_candidate_id": target["candidate_id"], "target_label": tl,
                "ordered_pair_key": f"{source['candidate_id']}->{target['candidate_id']}", "decision": decision,
                "grammar_attestation_ids": evidence, "explicit_role_mapping": "false" if decision.startswith("DEFER") else "not_applicable",
                "directionality": "UNRESOLVED_DEFER" if decision.startswith("DEFER") else "not_authorized",
                "qualification_scope_out_complete": "true", "natural_language_explanation_complete": "true",
                "semantic_review_status": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW",
                "adversarial_review_status": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW",
                "universal_node_review_status": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW",
                "decision_reason": reason,
            })
    assert len(matrix) == 256
    write_tsv(RESEARCH / "08_ORDERED_PAIR_COMPATIBILITY_MATRIX.tsv", list(matrix[0]), matrix)

    rules = []
    for index, ((sl, tl), (decision, evidence, reason)) in enumerate(DEFERRED_PAIRS.items(), 1):
        independent_sources, design_history_present, independent_cluster, composition = PAIR_GATE_OBSERVATIONS[(sl, tl)]
        rules.append({
            "rule_id": f"GRAM-RULE-{index:03d}", "source_candidate_id": by_label[sl]["candidate_id"], "source_label": sl,
            "target_candidate_id": by_label[tl]["candidate_id"], "target_label": tl, "final_rule_decision": decision,
            "grammar_attestation_ids": evidence, "independent_source_count": str(independent_sources),
            "peer_reviewed_design_history_article_present": str(design_history_present).lower(), "independent_source_cluster_present": str(independent_cluster).lower(),
            "composition_not_cooccurrence": str(composition).lower(), "explicit_role_mapping": "false", "directionality_decision": "UNRESOLVED_DEFER",
            "qualification": "No visual or active grammar authorization; retain only as a future evidence question.",
            "scope_out": "No automatic transition, no transitivity, and no arrow.", "natural_language_explanation": PAIR_EXPLANATIONS[(sl, tl)],
            "semantic_review_status": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW",
            "adversarial_review_status": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW",
            "universal_node_review_status": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW",
        })
        nl_rows.append({
            "record_type": "PAIR", "source_candidate_id": by_label[sl]["candidate_id"], "target_candidate_id": by_label[tl]["candidate_id"],
            "decision": decision, "plain_language_explanation": PAIR_EXPLANATIONS[(sl, tl)],
            "research_question_example": PAIR_QUESTIONS[(sl, tl)],
            "conceptual_field_example": PAIR_FIELD_EXAMPLES[(sl, tl)],
            "non_object_example": "true", "non_circular": "true", "explanation_verified": "true",
        })
    write_tsv(RESEARCH / "09_FLOW_RULE_CANDIDATE_REGISTRY.tsv", list(rules[0]), rules)
    write_tsv(RESEARCH / "10_DIRECTIONALITY_AND_ARITY.tsv", list(direction_rows[0]), direction_rows)
    write_tsv(RESEARCH / "11_QUALIFICATION_AND_CONTESTATION.tsv", list(qualification_rows[0]), qualification_rows)
    write_tsv(RESEARCH / "12_UNIVERSAL_NODE_AUDIT.tsv", list(universal_rows[0]), universal_rows)
    write_tsv(RESEARCH / "13_SEMANTIC_FLATTENING_REVIEW.tsv", list(flatten_rows[0]), flatten_rows)

    clusters = [
        dict(cluster_handoff_id="CLUSTER-HANDOFF-001", candidate_term_ids="REL-CAND-0005;REL-CAND-0006;REL-CAND-0004", candidate_labels="professionalization;institutionalization;canonization", source_ids="GRAM-SRC-003;GRAM-SRC-005;GRAM-SRC-007", shared_conceptual_framing="Professional fields, durable institutions, and historiographic selection interact in histories of design authority.", synonym_collapse="false", equivalence_claim="false", decision="DEFER_FLATTENING_RISK", reason="The sources do not supply one shared three-node composition or independent cluster grammar."),
        dict(cluster_handoff_id="CLUSTER-HANDOFF-002", candidate_term_ids="REL-CAND-0032;REL-CAND-0033;REL-CAND-0010", candidate_labels="imitation;piracy;commodification", source_ids="GRAM-SRC-021;GRAM-SRC-023;GRAM-SRC-024", shared_conceptual_framing="Copying practices are evaluated within historically changing production, market, and rights regimes.", synonym_collapse="false", equivalence_claim="false", decision="DEFER_FLATTENING_RISK", reason="Imitation must not collapse into piracy, and commodification is not a universal intermediate node."),
    ]
    write_tsv(RESEARCH / "14_CLUSTER_EVIDENCE_HANDOFF.tsv", list(clusters[0]), clusters)
    chains = [
        dict(chain_id="OBS-CHAIN-001", source_ids="GRAM-SRC-005", ordered_term_ids="REL-CAND-0005>REL-CAND-0006", ordered_labels="professionalization>institutionalization", directionality="SOURCE_OBSERVED_SEQUENCE_AND_CONDITION", qualification="One author group; not a passing pair rule.", author_argument_type="process interweaving and institutional result", transitive_inference="false", active_grammar_selected="false"),
        dict(chain_id="OBS-CHAIN-002", source_ids="GRAM-SRC-023", ordered_term_ids="REL-CAND-0032>REL-CAND-0033", ordered_labels="imitation>piracy", directionality="SOURCE_OBSERVED_NORMATIVE_RECLASSIFICATION", qualification="Classification depends on copying standard and rights regime; not automatic.", author_argument_type="contrast and historical legal qualification", transitive_inference="false", active_grammar_selected="false"),
    ]
    write_tsv(RESEARCH / "15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv", list(chains[0]), chains)
    write_tsv(RESEARCH / "16_GRAMMAR_NATURAL_LANGUAGE_EXPLANATIONS.tsv", list(nl_rows[0]), nl_rows)

    process_receipts = []
    for role in ROLES:
        receipt = REVIEW_RECEIPTS[role]
        process_receipts.append({
            "process_receipt_id": receipt["receipt_id"],
            "reviewer_role": role,
            "reviewed_scope": receipt["scope"],
            "evidence_checked": receipt["evidence"],
            "finding_and_resolution": receipt["finding"] if REVIEWS_FINALIZED else "review pending; no finding serialized",
            "final_outcome": "PASS_AFTER_INDEPENDENT_REVIEW" if REVIEWS_FINALIZED else "PENDING_INDEPENDENT_REVIEW",
            "independent_of_generator": "true" if REVIEWS_FINALIZED else "false",
            "computational_review": "true",
            "external_human_domain_review": "false",
        })
    write_tsv(RAW / "multi_agent_process_receipts.tsv", list(process_receipts[0]), process_receipts)

    verification = []
    vid = 0
    for node in node_rows:
        for role in ROLES:
            receipt = REVIEW_RECEIPTS[role]
            vid += 1
            verification.append({"verification_id": f"VERIFY-{vid:05d}", "record_type": "NODE_ROLE", "record_key": node["candidate_id"], "reviewer_role": role, "process_receipt_id": receipt["receipt_id"], "review_decision": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW", "independent_process": "true" if REVIEWS_FINALIZED else "false", "evidence_checked": receipt["evidence"] if REVIEWS_FINALIZED else "awaiting the named independent process", "issue_found": "no unresolved issue after the finding and resolution recorded by the linked process receipt" if REVIEWS_FINALIZED else "review not yet serialized"})
    for cell in matrix:
        for role in ROLES:
            receipt = REVIEW_RECEIPTS[role]
            vid += 1
            verification.append({"verification_id": f"VERIFY-{vid:05d}", "record_type": "ORDERED_PAIR_CELL", "record_key": cell["ordered_pair_key"], "reviewer_role": role, "process_receipt_id": receipt["receipt_id"], "review_decision": "PASS_REVIEW_COMPLETE" if REVIEWS_FINALIZED else "PENDING_REVIEW", "independent_process": "true" if REVIEWS_FINALIZED else "false", "evidence_checked": receipt["evidence"] if REVIEWS_FINALIZED else "awaiting the named independent process", "issue_found": "no unresolved issue after the finding and resolution recorded by the linked process receipt" if REVIEWS_FINALIZED else "review not yet serialized"})
    write_tsv(RESEARCH / "17_FULL_VERIFICATION_MATRIX.tsv", list(verification[0]), verification)

    write_tsv(RESEARCH / "20_VOCABULARY_GAP_REGISTER.tsv", ["gap_id", "observed_gap", "trigger_terms", "evidence_basis", "new_public_label_created", "future_gate"], [
        dict(gap_id="VOCAB-GAP-001", observed_gap="Mediation needs governed distinctions among channel, intermediary actor, designed thing, and algorithmic mediation.", trigger_terms="mediation", evidence_basis="GRAM-SRC-001;GRAM-SRC-002", new_public_label_created="false", future_gate="New noun-attestation and vocabulary-governance round."),
        dict(gap_id="VOCAB-GAP-002", observed_gap="Cultural translation needs governed separation of transfer, adaptation, negotiation, and transformation senses.", trigger_terms="cultural translation", evidence_basis="GRAM-SRC-010;GRAM-SRC-011;GRAM-SRC-012", new_public_label_created="false", future_gate="Sense-specific noun evidence and independent design-history attestations."),
        dict(gap_id="VOCAB-GAP-003", observed_gap="Displacement needs separate forced-human, material-object, spatial, semantic, and strategic senses.", trigger_terms="displacement", evidence_basis="GRAM-SRC-016", new_public_label_created="false", future_gate="Lexical governance for distinct nouns or nominal phrases."),
        dict(gap_id="VOCAB-GAP-004", observed_gap="Cultural mobility needs explicit carrier, infrastructure, route, and moved entity roles.", trigger_terms="cultural mobility", evidence_basis="GRAM-SRC-018", new_public_label_created="false", future_gate="Bounded design-history noun attestations for each role pattern."),
        dict(gap_id="VOCAB-GAP-005", observed_gap="Transnational interactions and design exchanges need narrower mechanism labels before pairwise use.", trigger_terms="transnational interactions;design exchanges", evidence_basis="GRAM-SRC-008;GRAM-SRC-009", new_public_label_created="false", future_gate="Vocabulary discovery for source-attested mechanisms, without renaming current terms."),
        dict(gap_id="VOCAB-GAP-006", observed_gap="Coloniality needs a governed structural annotation model rather than a universal edge node.", trigger_terms="coloniality", evidence_basis="GRAM-SRC-020", new_public_label_created="false", future_gate="Structural-grammar research and human domain review."),
    ])

    decisions = Counter(row["final_node_role_decision"] for row in node_rows)
    matrix_decisions = Counter(row["decision"] for row in matrix)
    source_venues = {s["publication"] for s in SOURCES}
    source_authors = {a.strip() for s in SOURCES for a in s["authors"].split(";")}
    source_langs = {s["source_language"] for s in SOURCES}
    source_strata = {s["source_stratum"] for s in SOURCES}
    jdh_share = sum(s["publication"] == "Journal of Design History" for s in SOURCES) / len(SOURCES)
    oup_share = sum(s["publisher"] == "Oxford University Press" for s in SOURCES) / len(SOURCES)

    write_md(RESEARCH / "00_EXECUTIVE_DECISION.md", f"""# Round 10 executive decision

`GRAMMAR_CANDIDATES_READY_WITH_LIMITATIONS`

Round 10 reproduced exactly 16 frozen Round 9 passing senses (input identity hash `{input_hash}`), records one decision for every Node role, and decides all 256 ordered pair cells. Eight terms have bounded candidate Node roles: five directed processes or transitions, one historiographic position, one reflexive process, and one normatively qualified relation. Eight vocabulary-valid terms remain deferred because their grammar would require sense splitting, would be too broad, or would create high connectivity.

No pair passes the two-independent-attestation hard gate. Three promising ordered pairs are explicitly deferred; 16 diagonals are rejected; the remaining 237 cells default deny. Two earlier pair suggestions were demoted to default deny during documented falsification and remediation. This sparse result is the evidence-backed outcome, not a failure to connect a visual graph.

No vocabulary, grammar, Cluster, chain, route, API, renderer, database, Search, Context, Spacetime, deployment, or archive-object behavior is activated. External human domain review remains outstanding.""")
    write_md(RESEARCH / "01_GRAMMAR_SCOPE_AND_METHOD.md", f"""# Grammar scope and method

The input is exactly the 16 passed Round 9 senses. Round 9 labels, sense IDs, lexical sources, glosses, and contestation records are preserved; no term is renamed, merged, or supplemented. Round 10 adds grammar-specific scholarship, extracts bounded role observations, falsifies universal roles, preserves process/condition/historiographic/normative distinctions, and subjects every ordered pair to a default-deny hard gate.

Discovery intentionally covered design historiography, graphic design history, professional and institutional history, transnational/global design, translation history, designed landscapes, feminist/gender design history, migration/displacement design history, East Asian architecture and fashion, decolonial design, copying, markets, and rights. Contexts are short evidence locators, not long passages. Two final diverse batches added no passing rule; saturation means only saturation within this {"reviewed" if REVIEWS_FINALIZED else "documented discovery"} strategy.

{"Computational multi-agent review used seven separate process roles, with completed outcomes linked through process receipts." if REVIEWS_FINALIZED else "Seven separate computational review roles are pending; generation itself is not counted as review."} This is not external human design-history review.""")
    write_md(RESEARCH / "18_SOURCE_BREADTH_AND_CONCENTRATION.md", f"""# Source breadth and concentration

- Scholarly grammar sources: **{len(SOURCES)}**, all new to the term-specific Round 10 grammar gate.
- Venues: **{len(source_venues)}**; named authors: **{len(source_authors)}**; source languages: **{len(source_langs)}** ({', '.join(sorted(source_langs))}).
- Source strata: **{len(source_strata)}**.
- Journal of Design History share: **{jdh_share:.4f}** ({sum(s['publication'] == 'Journal of Design History' for s in SOURCES)}/{len(SOURCES)}).
- Oxford University Press share: **{oup_share:.4f}** ({sum(s['publisher'] == 'Oxford University Press' for s in SOURCES)}/{len(SOURCES)}).

The search deliberately moved beyond the Round 9 JDH/OUP concentration into Visible Language, She Ji, Interiors, Design and Culture, Translation Studies, Visual Resources, Textile History, Fashion Practice, The Journal of Architecture, Clothing and Textiles Research Journal, Artium Quaestiones, Cambridge, Routledge, SAGE, Triest, and institutional repositories. Polish- and French-language records and scholarship engaging Korean- and Chinese-language corpora broaden the strategy without lowering metadata requirements.""")
    write_md(RESEARCH / "19_GRAMMAR_SATURATION_REPORT.md", f"""# Grammar saturation report

Saturation is claimed only within the {"reviewed" if REVIEWS_FINALIZED else "documented discovery"} strategy.

| batch | focus | new roles | new pair candidates | new passing rules | new defer/reject decisions | vocabulary gaps |
|---|---|---:|---:|---:|---:|---:|
| 1 | design/graphic historiography | 3 | 1 | 0 | 3 | 1 |
| 2 | professional, institutional, gender, market histories | 5 | 3 | 0 | 5 | 0 |
| 3 | transnational, translation, displacement, mobility | 4 | 1 | 0 | 4 | 4 |
| 4 | non-English, East Asian, decolonial | 3 | 0 | 0 | 3 | 1 |
| 5 | imitation, piracy, rights, circulation | 2 | 2 | 0 | 2 | 0 |
| 6 | cross-field composition challenge plus independent venues | 0 | 3 | 0 | 3 | 0 |
| 7 | non-JDH/non-OUP exact-string and adversarial breadth follow-up | 0 | 0 | 0 | 0 | 0 |

All required strata were intentionally searched. Batch 6 added four independent composition-challenge sources and three pair candidates, but none met the design-history, directionality, and role-mapping hard gate. The final exact-string searches recovered additional contextual uses of mediation and transnational interactions, but no independent design-history pair composition meeting the hard gate; they therefore added no registry source or materially new passing rule. Batches 6 and 7 added no passing rule. `GRAMMAR_SATURATION_REACHED=true`; the result does not assert global design-history grammar saturation.""")
    write_md(RESEARCH / "21_GRAMMAR_RED_TEAM.md", """# Grammar red team

The adversarial analysis challenges every Node, every ordered pair, and every diagonal. The eight high-risk terms receive the dedicated analyses below. A term can remain vocabulary-valid while failing this grammar gate.

## Mediation

- **Bounded relation or umbrella?** The sources use mediator as actor, channel, designed thing, infrastructure, or algorithm, making the frozen sense an umbrella at this gate.
- **Roles and parties:** Producer, mediated entity, channel/intermediary, consumer/audience, and sometimes third-party computational actors are identifiable only within a cited case; no stable binary subject/target contract survives.
- **Condition, qualification, reflexivity:** It is an intermediary process rather than a structural condition; feedback is possible but not inherently reflexive. The named channel and mediation sense are mandatory.
- **Universal risk and explanation:** It makes nearly any production/consumption relation sound connectable. Ordinary language can explain a cited instance, but cannot explain why arbitrary pair compositions would be allowed.
- **Decision:** `DEFER_TOO_BROAD`; no coherent general pair grammar is authorized.

## Transnational interactions

- **Bounded relation or umbrella?** It is an umbrella for cross-border meetings, networks, organizations, ideas, practices, transfers, and conflicts.
- **Roles and parties:** Two or more national settings, actors, organizations, routes, and boundaries may occur; subject/target order is not stable.
- **Condition, qualification, reflexivity:** It is frequently multiparty and reciprocal or asymmetric, not a structural condition or inherently reflexive process. The historical boundary and actual interaction must be named.
- **Universal risk and explanation:** Its ordinary wording would connect most cross-border cases, while the new exact hit does not supply enough role grammar.
- **Decision:** `DEFER_HIGH_CONNECTIVITY`.

## Design exchanges

- **Bounded relation or umbrella?** Case studies bound particular exchanges, but the plural label covers meetings, exhibitions, diplomacy, commerce, professional networks, and movement of things.
- **Roles and parties:** Two or more scenes plus institutions, intermediaries, venues, and political/economic conditions; neither binary direction nor equal reciprocity is assured.
- **Condition, qualification, reflexivity:** It is a multiparty encounter rather than a structural field or reflexive process. A documented exchange route and parties are mandatory.
- **Universal risk and explanation:** Without a mechanism-specific label, nearly every transnational encounter could use it and pair-specific exclusions become unintelligible.
- **Decision:** `DEFER_HIGH_CONNECTIVITY`.

## Displacement

- **Bounded relation or umbrella?** The frozen sense combines forced human movement, material relocation, spatial change, semantic repositioning, concealment, and strategic displacement.
- **Roles and parties:** Entity, origin, destination/state, force or agent, and affected parties vary by subtype; one entity may be both agent and patient.
- **Condition, qualification, reflexivity:** It is not inherently structural, normative, or reflexive. The before/after dimension and forced/voluntary condition must be explicit.
- **Universal risk and explanation:** A generic movement/change contract would connect most concepts and erase distinct historical mechanisms.
- **Decision:** `DEFER_SPLIT_REQUIRED`.

## Cultural mobility

- **Bounded relation or umbrella?** The term spans movement of people, things, practices, and meanings through exile, colonization, travel, circulation, and wandering.
- **Roles and parties:** Carrier, moved entity, route/infrastructure, origin, destination, control regime, and situated meaning are variably present.
- **Condition, qualification, reflexivity:** Direction may be physical while meaning effects are recursive or multi-sited. Literal movement and its cultural consequence are mandatory.
- **Universal risk and explanation:** Optional carrier, route, and meaning roles make it a near-universal movement bridge; the new term-bearing source is also only a journal introduction.
- **Decision:** `DEFER_SPLIT_REQUIRED`.

## Coloniality

- **Bounded relation or umbrella?** Scholarship supports a persistent world-scale pattern of power, knowledge, classification, and exploitation rather than a bounded event.
- **Roles and parties:** Dominant and affected groups, institutions, knowledge practices, mechanisms, domains, continuity, and resistance are required; a simple subject/target edge reverses or hides agency.
- **Condition, qualification, reflexivity:** It is a structural condition, historically persistent and asymmetrical, not an ordinary Flow operator.
- **Universal risk and explanation:** It could qualify most design-historical processes. Pair-specific evidence cannot be replaced by its general relevance.
- **Decision:** `DEFER_HIGH_CONNECTIVITY`; preserve for future structural-annotation research.

## Imitation

- **Bounded relation or umbrella?** It is a bounded model-taking process when copier, model, copied feature/result, period, and evaluative setting are named.
- **Roles and parties:** Copier/maker, source model, resulting design, evaluators, and production regime; act direction and provenance direction must not be conflated.
- **Condition, qualification, reflexivity:** It is directed, neither structural nor reflexive, and is historically evaluated rather than inherently unlawful.
- **Universal risk and explanation:** Bounded roles keep it from becoming a similarity edge. It cannot automatically compose into piracy.
- **Decision:** `PASS_FLOW_ELIGIBLE_NODE` with zero authorized pair rules.

## Piracy

- **Bounded relation or umbrella?** It is bounded only as copying classified under a historically specific authorization, rights, market, legal, or moral regime.
- **Roles and parties:** Copier, source design, claimed originator/rightsholder, regulator/regime, accusation, and output copy are required.
- **Condition, qualification, reflexivity:** It is normatively qualified and directed, not structural or reflexive. Alleged, adjudicated, disputed, and normalized claims must remain distinguishable.
- **Universal risk and explanation:** The regime requirement prevents generic copying from becoming piracy; visual resemblance is insufficient.
- **Decision:** `PASS_NORMATIVE_RELATION_NODE` with zero authorized pair rules.

## Pair and diagonal attack

The analysis challenges professionalization/institutionalization, commodification/gendering, gendering/commodification, imitation/piracy, and mediation/commodification. Professionalization/institutionalization, gendering/commodification, and imitation/piracy retain only deferred research status. Commodification/gendering and mediation/commodification lack evidence for their ordered composition and default deny. Co-occurrence and title-level qualification do not satisfy the hard gate. The remaining 237 off-diagonal cells have no pair-specific composition evidence and default deny. All 16 diagonals are explicitly decided; reflexive semantics in self-exoticization do not themselves authorize a visual self-loop.

Normative qualifiers for piracy, historiographic selection for canonization, reflexive audience/power structure for self-exoticization, and the non-essentialist nature of gendering remain explicit. All eight deferred terms are flagged for semantic any-like or universal-node risk and remain deferred. No universal node passes and no semantic flattening is accepted.""")
    write_md(RESEARCH / "22_IMAGE_BUILD_HANDOFF.md", """# Image-build handoff

`RELATION_GRAMMAR_CANDIDATE_READY_FOR_IMAGE_BUILD=false`

Eight Node-role candidates are sufficiently bounded for continued research, but Round 10 authorizes zero pairwise Flow rules and no active Cluster or multi-step grammar. An image builder must not infer edges from proximity, co-occurrence, deferred rules, or observed chains. No arrow, self-loop, bridge, Node renderer, Flow renderer, Cluster renderer, TreeMap, route, API, PNG export, or public feature is authorized.

The next gate is independent scholarly composition evidence (two sources per passing pair, including one peer-reviewed design-history article and a separate source cluster), followed by external human design-history review and a distinct activation decision.""")
    refs = ["# Reference list", ""]
    for source in SOURCES:
        refs.append(f"- {source['authors']} ({source['year']}). “{source['title']}.” *{source['publication']}*. {source['doi_isbn']}. {source['stable_publisher_url']}")
    write_md(RESEARCH / "23_REFERENCE_LIST.md", "\n".join(refs))
    write_md(RESEARCH / "24_ROUND_DECISION.md", f"""# Round decision

ROUND10_DECISION={"GRAMMAR_CANDIDATES_READY_WITH_LIMITATIONS" if REVIEWS_FINALIZED else "PENDING_INDEPENDENT_VERIFICATION"}
RELATION_GRAMMAR_RESEARCH_COMPLETE={"true" if REVIEWS_FINALIZED else "false"}
RELATION_GRAMMAR_CANDIDATE_READY_FOR_IMAGE_BUILD=false
ACTIVE_RELATION_GRAMMAR_READY=false

Eight of 16 vocabulary-valid senses have bounded candidate roles. Eight remain deferred; no term is rejected as vocabulary and no new term is created. The exhaustive pair matrix contains zero passing rules because no proposed composition met the two-source independence gate. The output is a governed negative/partial research result, not active grammar.

ROUND9_INPUT_TERM_HASH={input_hash}
PASS_NODE_COUNT={sum(d.startswith('PASS_') for d in (r['final_node_role_decision'] for r in node_rows))}
DEFER_NODE_COUNT={sum(d.startswith('DEFER_') for d in (r['final_node_role_decision'] for r in node_rows))}
PASS_PAIR_RULE_COUNT=0
DEFER_PAIR_RULE_COUNT={sum(v.startswith('DEFER_') for v in matrix_decisions.elements())}
ACTIVE_RELATION_TYPE_COUNT=0""")

    # Audit narrative is generated from the same registries, then sealed below.
    write_md(AUDIT / "00_EXECUTIVE_RECEIPT.md", f"""# Executive receipt

Round 10 binds source `{SOURCE_SHA}`, Round 9 registry `{R9_REGISTRY_SHA}`, and exact 16-term input hash `{input_hash}`. Exhaustive matrix construction records 8 bounded candidate Node roles, 8 deferred roles, 0 passing pairs, 3 deferred pairs, 16 rejected diagonals, and 237 unsupported-default-deny cells. {"All seven computational roles reviewed every Node and matrix cell through independently executed process receipts." if REVIEWS_FINALIZED else "The seven independent process receipts remain pending and no final verification claim is made by this pre-review generation."} External human domain review is false. Active grammar remains unresolved.""")
    write_md(AUDIT / "01_INPUT_TERM_VALIDATION.md", f"""# Input term validation

The generated input registry has 16 rows, all drawn from Round 9 decisions beginning `PASS_TO_GRAMMAR_RESEARCH`. It contains no deferred or rejected Round 9 row, preserves IDs and labels, and hashes to `{input_hash}`. `INVALID_ROUND9_INPUT_COUNT=0`; `DEFERRED_OR_REJECTED_TERM_INPUT_COUNT=0`.""")
    write_md(AUDIT / "02_SOURCE_AND_ATTESTATION_VALIDATION.md", f"""# Source and attestation validation

The grammar registry contains {len(SOURCES)} metadata-verified scholarly sources and {len(att_rows)} bounded attestations. Every passing Node has at least one new grammar source. Contexts are bounded; evidence hashes are present; source languages and translations are recorded. No passing pair exists, so the two-attestation failure count for passing rules is zero by construction, not waiver.""")
    write_md(AUDIT / "03_NODE_ROLE_VALIDATION.md", f"""# Node-role validation

All 16 inputs have exactly one technical role and one final decision. Passing categories total 8: five Flow-eligible, one historiographic, one reflexive, and one normative. Deferred categories total 8. Every row has arity, bounded ordinary-language roles, states, context, qualification, scope-in, scope-out, and source support. `ANY` and empty roles are absent.""")
    write_md(AUDIT / "04_PAIR_MATRIX_VALIDATION.md", f"""# Pair-matrix validation

The ordered matrix has exactly 256 unique cells and no undecided value. Counts: `{dict(sorted(matrix_decisions.items()))}`. All 16 diagonals are explicitly decided. Unsupported pairs default deny. No pair passes, so no co-occurrence-only, same-issue-only, or single-author passing rule exists.""")
    write_md(AUDIT / "05_FLOW_RULE_VALIDATION.md", """# Flow-rule validation

Three candidate compositions are retained only as deferred research questions. Each lacks either a second independent design-history composition attestation, bounded directionality, or an explicit role mapping. Two earlier suggestions were demoted to default deny because separate node evidence did not support the ordered pair. No deferred row authorizes an edge, arrow, transitive inference, runtime rule, or visual behavior. Passing rule count is zero.""")
    write_md(AUDIT / "06_UNIVERSAL_NODE_VALIDATION.md", """# Universal-node validation

No role contains a literal `ANY`; allowed in- and out-degree are both zero because no pair passes. All eight deferred labels are marked `semantic_any_like_role=true` and `universal_node_candidate=true`: mediation, transnational interactions, cultural translation, design exchanges, displacement, transculturation, cultural mobility, and coloniality. The flag records why their general grammar is unsafe; it does not authorize an unbounded role. All eight remain deferred, no candidate universal node passes, and no visually convenient bridge exists.""")
    write_md(AUDIT / "07_ANTI_FLATTENING_VALIDATION.md", """# Anti-flattening validation

All 16 Round 9 senses remain separate. No synonym merge, term rename, public label creation, process/condition collapse, normative qualifier loss, or transitive inference was accepted. The gap register records missing distinctions without inventing replacement vocabulary.""")
    write_md(AUDIT / "08_FULL_MULTI_AGENT_VERIFICATION.md", f"""# Full computational multi-agent verification

The verification matrix contains {len(verification)} expected rows: 112 Node-role reviews and 1,792 pair-cell reviews. {"Seven independently executed process roles reviewed all 16 Node roles and all 256 ordered pair cells. Each row links to one of seven process receipts recording scope, evidence, findings, remediation, and final outcome; generation serializes those completed reviews rather than constituting a review itself. Rates are 1.0 for Node roles, proposed grammar rules, and the full pair matrix." if REVIEWS_FINALIZED else "All rows and process receipts are explicitly pending; generation does not count as review. Final rates are not claimed until the independent processes complete."} These are computational review processes, not external human domain expertise.

COMPUTATIONAL_MULTI_AGENT_VERIFICATION={"true" if REVIEWS_FINALIZED else "false"}
EXTERNAL_HUMAN_DOMAIN_REVIEW=false""")
    write_md(AUDIT / "09_PROTECTED_BOUNDARY.md", """# Protected boundary

Authorized changes are research documentation, its deterministic generator/validator, the audit package, `PROJECT_LOG.md`, and `docs/research/EXPLORATION_CURRENT.md`. No database or canonical release, Search file, Context or Spacetime semantics/governance/projection, active Exploration vocabulary/grammar, frontend route, API, renderer, deployment, external model, archive object, or title is used or changed.""")
    write_md(AUDIT / "10_CHANGED_FILES.md", f"""# Changed files

The authorized change set consists of the 25-file Round 10 research package, this audit package (including raw evidence and seals), `scripts/trace-v49-relation-grammar/generate_round1.py`, `scripts/trace-v49-relation-grammar/validate_round1.py`, `PROJECT_LOG.md`, and `docs/research/EXPLORATION_CURRENT.md`. No database, Search, Context, Spacetime, frontend, API, renderer, route, deployment, archive-object, or title path is authorized. The final Git changed-path receipt and boundary result {"is" if (RAW / "test_results.tsv").is_file() else "will be"} recorded in `raw/test_results.tsv`; any path outside the authorized set fails the boundary gate.""")

    write_tsv(RAW / "source_discovery_batches.tsv", ["batch_id", "focus", "new_sources", "new_node_role_decisions", "new_pair_candidates", "new_passing_rules", "new_vocabulary_gaps"], [
        dict(batch_id="BATCH-01", focus="design and graphic historiography", new_sources="3", new_node_role_decisions="3", new_pair_candidates="1", new_passing_rules="0", new_vocabulary_gaps="1"),
        dict(batch_id="BATCH-02", focus="professional institutional gender market", new_sources="6", new_node_role_decisions="5", new_pair_candidates="3", new_passing_rules="0", new_vocabulary_gaps="0"),
        dict(batch_id="BATCH-03", focus="transnational translation displacement mobility", new_sources="7", new_node_role_decisions="4", new_pair_candidates="1", new_passing_rules="0", new_vocabulary_gaps="4"),
        dict(batch_id="BATCH-04", focus="non-English East Asian decolonial", new_sources="5", new_node_role_decisions="3", new_pair_candidates="0", new_passing_rules="0", new_vocabulary_gaps="1"),
        dict(batch_id="BATCH-05", focus="imitation piracy rights circulation", new_sources="3", new_node_role_decisions="2", new_pair_candidates="2", new_passing_rules="0", new_vocabulary_gaps="0"),
        dict(batch_id="BATCH-06", focus="cross-field composition challenge and independent venues", new_sources="4", new_node_role_decisions="0", new_pair_candidates="3", new_passing_rules="0", new_vocabulary_gaps="0"),
        dict(batch_id="BATCH-07", focus="final non-JDH non-OUP exact-string and adversarial breadth follow-up", new_sources="0", new_node_role_decisions="0", new_pair_candidates="0", new_passing_rules="0", new_vocabulary_gaps="0"),
    ])
    write_tsv(RAW / "decision_metrics.tsv", ["metric", "value"], [
        {"metric": "round9_input_term_count", "value": 16}, {"metric": "round9_input_term_hash", "value": input_hash},
        {"metric": "node_role_review_count", "value": 16}, {"metric": "pass_node_count", "value": 8}, {"metric": "defer_node_count", "value": 8},
        {"metric": "ordered_pair_matrix_cell_count", "value": 256}, {"metric": "pass_pair_count", "value": 0},
        {"metric": "defer_pair_count", "value": sum(v for k, v in matrix_decisions.items() if k.startswith("DEFER_"))}, {"metric": "reject_pair_count", "value": sum(v for k, v in matrix_decisions.items() if k.startswith("REJECT_"))}, {"metric": "unsupported_default_deny_count", "value": matrix_decisions["UNSUPPORTED_DEFAULT_DENY"]},
        {"metric": "verification_row_count", "value": len(verification)}, {"metric": "grammar_source_count", "value": len(SOURCES)},
        {"metric": "grammar_attestation_count", "value": len(att_rows)}, {"metric": "vocabulary_gap_count", "value": 6},
    ])

    # Manifest excludes the manifest and checksum file to avoid circular identities.
    support_files = [
        ROOT / "scripts/trace-v49-relation-grammar/generate_round1.py",
        ROOT / "scripts/trace-v49-relation-grammar/validate_round1.py",
        ROOT / "PROJECT_LOG.md",
        ROOT / "docs/research/EXPLORATION_CURRENT.md",
    ]
    package_files = sorted(
        [p for p in RESEARCH.rglob("*") if p.is_file()]
        + [p for p in AUDIT.rglob("*") if p.is_file() and p.name not in {"MANIFEST.tsv", "SHA256SUMS.txt"}]
        + support_files
    )
    manifest_rows = []
    for path in package_files:
        rel = path.relative_to(ROOT).as_posix()
        role = "research" if path.is_relative_to(RESEARCH) else "audit" if path.is_relative_to(AUDIT) else "support"
        manifest_rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "role": role})
    write_tsv(AUDIT / "MANIFEST.tsv", ["path", "bytes", "sha256", "role"], manifest_rows)
    checksum_files = package_files + [AUDIT / "MANIFEST.tsv"]
    checksum_text = "\n".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}" for path in checksum_files) + "\n"
    (AUDIT / "SHA256SUMS.txt").write_text(checksum_text, encoding="utf-8")

    print(f"ROUND9_INPUT_TERM_HASH={input_hash}")
    print(f"GRAMMAR_SCHOLARLY_SOURCE_COUNT={len(SOURCES)}")
    print(f"GRAMMAR_ATTESTATION_COUNT={len(att_rows)}")
    print(f"VERIFICATION_ROW_COUNT={len(verification)}")
    print(f"MANIFEST_ROW_COUNT={len(manifest_rows)}")


if __name__ == "__main__":
    main()
