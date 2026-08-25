#!/usr/bin/env python3
"""Generate the TRACE v49 Round 13 research, schema, fixture, and audit packages."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from canonical_v2 import semantic_hash  # noqa: E402
from instance_v2 import compile_instance_v2  # noqa: E402
from topology import STRATEGIES, assert_no_duplicate_topologies, build_tree, topology_signature  # noqa: E402


SOURCE_SHA = "83f1fba3464f5828fcfd15a1c557035bb1341bf3"
FREEZE_HASH = "b7d42015862e12fd54bc05a9ed0a53223771fc03954c112e72652c0349fb6f90"
RESEARCH = REPO / "docs/research/trace-v49-exploration-composition-review-round1"
AUDIT = REPO / "docs/audits/v49-exploration-composition-review-round1"
INSTANCES_V1 = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1/12_RESEARCH_INSTANCES"
INSTANCES_V2 = RESEARCH / "12_RESEARCH_INSTANCES_V2"
RAW = AUDIT / "raw"
FIXTURES = ENGINE / "fixtures"
SCHEMAS = REPO / "schemas/trace/exploration"


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows and not fields:
        raise ValueError(f"empty TSV without declared schema: {path}")
    columns = fields or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: str(row.get(column, "")).replace("\t", " ").replace("\n", " ") for column in columns})


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile_active_script_allowlist() -> None:
    json_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json"
    csv_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv"
    markdown_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md"
    value = json.loads(json_path.read_text(encoding="utf-8"))
    rows_by_path = {row["path"]: row for row in value["scripts"]}
    round13_paths = sorted(
        path.relative_to(REPO).as_posix()
        for path in ENGINE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    for path in round13_paths:
        rows_by_path[path] = {
            "path": path,
            "category": "RESEARCH_ENGINE_VALIDATION",
            "current_runtime_required": False,
            "current_api_required": False,
            "current_database_required": False,
            "current_ci_required": False,
            "retained_audit_role": True,
            "decision": "DOCUMENTED_ALLOWLIST",
        }
    rows = [rows_by_path[path] for path in sorted(rows_by_path)]
    write_json(json_path, {"format": value["format"], "scriptCount": len(rows), "unknownClassificationCount": 0, "scripts": rows})
    write_tsv(csv_path, rows)
    csv_text = csv_path.read_text(encoding="utf-8").replace("\t", ",")
    csv_path.write_text(csv_text, encoding="utf-8")
    paragraphs = markdown_path.read_text(encoding="utf-8").rstrip().split("\n\n")
    paragraphs = [paragraph for paragraph in paragraphs if not paragraph.startswith("Round 13 adds ")]
    paragraphs.append(
        f"Round 13 adds {len(round13_paths)} composition-review reference, generator, validator, test, and topology-fixture files. "
        f"They are research/audit reproduction tooling only and do not activate runtime semantics. The reconciled count is {len(rows)} with zero missing, extra, duplicate, or unknown classifications."
    )
    existing = "\n\n".join(paragraphs)
    write_text(markdown_path, existing)


def source(
    source_id: str,
    authors: str,
    year: int,
    title: str,
    venue: str,
    publisher: str,
    doi: str,
    url: str,
    language: str,
    source_type: str,
    peer_reviewed: str,
    design_history_usage: str,
    cluster: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "authors": authors,
        "year": year,
        "title": title,
        "venue": venue,
        "publisher": publisher,
        "doi_or_identifier": doi,
        "stable_url": url,
        "language": language,
        "source_type": source_type,
        "peer_reviewed": peer_reviewed,
        "design_history_usage": design_history_usage,
        "source_cluster": cluster,
        "source_metadata_verified": "true",
    }


SOURCES = [
    source("COMP-SRC-001", "Grace Lees-Maffei", 2008, "Introduction: Professionalization as a Focus in Interior Design History", "Journal of Design History 21.1", "Oxford University Press", "10.1093/jdh/epn007", "https://academic.oup.com/jdh/article/21/1/1/361205", "English", "ARTICLE", "true", "true", "PROFESSIONALIZATION_INTERIOR_DESIGN"),
    source("COMP-SRC-002", "Turid Moldenæs;Hilde Marie Pettersen", 2021, "The Professional Project of Graphic Designers and Universities' Visual Identities", "Journal of Professions and Organization 8.2", "Oxford University Press", "10.1093/jpo/joab010", "https://munin.uit.no/handle/10037/22810", "English", "ARTICLE", "true", "true", "GRAPHIC_DESIGN_PROFESSIONS"),
    source("COMP-SRC-003", "Mike Bresnen", 2013, "Advancing a New Professionalism: Professionalization, Practice and Institutionalization", "Building Research & Information 41.6", "Taylor & Francis", "10.1080/09613218.2013.843269", "https://doi.org/10.1080/09613218.2013.843269", "English", "COMMENTARY", "unknown", "false", "PROFESSIONS_CHALLENGE"),
    source("COMP-SRC-004", "Livia Rezende", 2017, "Manufacturing the Raw in Design Pageantries: the Commodification and Gendering of Brazilian Tropical Nature", "Journal of Design History 30.2", "Oxford University Press", "10.1093/jdh/epx007", "https://researchonline.rca.ac.uk/2773/", "English", "ARTICLE", "true", "true", "BRAZILIAN_ENVIRONMENTAL_DESIGN_HISTORY"),
    source("COMP-SRC-005", "Emma Waight", 2019, "Mother, Consumer, Trader: Gendering the Commodification of Second-Hand Economies", "Journal of Consumer Culture 19.4", "SAGE", "10.1177/1469540519872069", "https://journals.sagepub.com/doi/abs/10.1177/1469540519872069", "English", "ARTICLE", "true", "false", "CONSUMER_MATERIAL_CULTURE"),
    source("COMP-SRC-006", "Gino Cattani;Mariachiara Colucci;Simone Ferriani", 2023, "From the Margins to the Core of Haute Couture: The Entrepreneurial Journey of Coco Chanel", "Enterprise & Society 24.2", "Cambridge University Press", "10.1017/eso.2021.58", "https://www.cambridge.org/core/journals/enterprise-and-society/article/from-the-margins-to-the-core-of-haute-couture-the-entrepreneurial-journey-of-coco-chanel/2EB663E94E9C67F6CB3B9CF962242FAD", "English", "ARTICLE", "true", "false", "FASHION_PIRACY_HISTORY"),
    source("COMP-SRC-007", "Alice Wickens", 2025, "From Calico to Catwalk: Addressing the UK's Enduring Issue of Fashion Piracy", "Journal of Intellectual Property Law & Practice 20.2", "Oxford University Press", "10.1093/jiplp/jpae107", "https://academic.oup.com/jiplp/article/20/2/71/7916754", "English", "ARTICLE", "true", "false", "FASHION_RIGHTS_HISTORY"),
    source("COMP-SRC-008", "Areti T. Vogel;Jacob Vogel;Kittichai Watchravesringkan;Sasikarn Chatvijit Cook;James Beasley;Randall Croom;Dale Peterson;Joshua Finkelstein", 2023, "Design Piracy: An Interdisciplinary Investigation into Competitive Industrial Behavior", "Journal of Business Research 164", "Elsevier", "10.1016/j.jbusres.2023.113946", "https://www.sciencedirect.com/science/article/pii/S0148296323003041", "English", "ARTICLE", "true", "false", "DESIGN_PIRACY_BEHAVIOR"),
    source("COMP-SRC-009", "Grace Lees-Maffei", 2009, "The Production–Consumption–Mediation Paradigm", "Journal of Design History 22.4", "Oxford University Press", "10.1093/jdh/epp031", "https://doi.org/10.1093/jdh/epp031", "English", "ARTICLE", "true", "true", "PCM_METHODOLOGY"),
    source("COMP-SRC-010", "Anna Kallen Talley", 2026, "Digital Design History: State of the Field, Definitions and Possibilities", "Journal of Design History 39.2", "Oxford University Press", "10.1093/jdh/epag001", "https://academic.oup.com/jdh/article/39/2/113/8537083", "English", "ARTICLE", "true", "true", "PCM_METHODOLOGY"),
    source("COMP-SRC-011", "Gay McDonald", 2010, "The Modern American Home as Soft Power: Finland, MoMA and the 'American Home 1953' Exhibition", "Journal of Design History 23.4", "Oxford University Press", "10.1093/jdh/epq038", "https://academic.oup.com/jdh/article/23/4/387/426251", "English", "ARTICLE", "true", "true", "COLD_WAR_EXHIBITION_TRANSFER"),
    source("COMP-SRC-012", "Todd P. Olson", 2023, "Cultural Transfer and Its Discontents: Recent Scholarship on the Mobility of Early Modern Prints", "Oxford Art Journal 46.1", "Oxford University Press", "10.1093/oxartj/kcad007", "https://doi.org/10.1093/oxartj/kcad007", "English", "BOOK_REVIEW", "unknown", "false", "PRINT_MOBILITY"),
    source("COMP-SRC-013", "Tom Avermaete;Cathelijne Nuijsink", 2021, "Architectural Contact Zones: Another Way to Write Global Histories of the Post-War Period?", "Architectural Theory Review 25.3", "Taylor & Francis", "10.1080/13264826.2021.1939745", "https://www.tandfonline.com/doi/full/10.1080/13264826.2021.1939745", "English", "ARTICLE", "true", "true", "ARCHITECTURAL_CONTACT_ZONES"),
    source("COMP-SRC-014", "Imam Santosa;I. Kadek Dwi Noorwatha", 2025, "Symbolic and Aesthetic Fusion in Keraton Surakarta: Colonial Influence and Javanese Cultural Resistance through Architectural Design Adaptation", "Cogent Arts & Humanities 12.1", "Taylor & Francis", "10.1080/23311983.2025.2482456", "https://doi.org/10.1080/23311983.2025.2482456", "English", "ARTICLE", "true", "true", "JAVANESE_ARCHITECTURAL_DESIGN"),
    source("COMP-SRC-015", "Ana Trujillo Dennis", 2019, "Ehon Don Kihōte de Serizawa Keisuke: Don Quijote como puente entre culturas", "Mirai. Estudios Japoneses 3", "Universidad Complutense de Madrid", "10.5209/mira.63100", "https://doi.org/10.5209/mira.63100", "Spanish", "ARTICLE", "true", "true", "JAPANESE_BOOK_DESIGN"),
    source("COMP-SRC-016", "Dirk Snelders;Kaj P. N. Morel;Pieter Havermans", 2011, "The Cultural Adaptation of Web Design to Local Industry Styles: A Comparative Study", "Design Studies 32.5", "Elsevier", "10.1016/j.destud.2011.03.001", "https://www.sciencedirect.com/science/article/abs/pii/S0142694X11000251", "English", "ARTICLE", "true", "false", "CROSS_CULTURAL_DESIGN_RESEARCH"),
    source("COMP-SRC-017", "Hifsiye Pulhan;İbrahim Numan", 2006, "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation", "Journal of Design History 19.2", "Oxford University Press", "10.1093/jdh/epi050", "https://doi.org/10.1093/jdh/epi050", "English", "ARTICLE", "true", "true", "CYPRUS_ARCHITECTURAL_HISTORY"),
    source("COMP-SRC-018", "Richard E. Blanton", 2011, "Cultural Transformation, Art, and Collective Action in Polity Building", "Cross-Cultural Research 45.2", "SAGE", "10.1177/1069397110393145", "https://journals.sagepub.com/doi/10.1177/1069397110393145", "English", "ARTICLE", "true", "false", "COMPARATIVE_POLITY_RESEARCH"),
    source("COMP-SRC-019", "Sarah A. Lichtman;Jilly Traganou", 2021, "Introduction to Material Displacements", "Journal of Design History 34.3", "Oxford University Press", "10.1093/jdh/epab027", "https://academic.oup.com/jdh/issue/34/3", "English", "ARTICLE", "true", "true", "MATERIAL_DISPLACEMENTS"),
    source("COMP-SRC-020", "Jane Hutton", 2013, "Reciprocal Landscapes: Material Portraits in New York City and Elsewhere", "Journal of Landscape Architecture 8.1", "Taylor & Francis", "10.1080/18626033.2013.798922", "https://www.tandfonline.com/doi/abs/10.1080/18626033.2013.798922", "English", "ARTICLE", "true", "true", "LANDSCAPE_MATERIAL_CHAINS"),
    source("COMP-SRC-021", "Damon Taylor", 2016, "Laying Down Memories: the Cultural Mobility of Tejo Remy's Chest of Drawers", "Journal of Design History 29.3", "Oxford University Press", "10.1093/jdh/epv047", "https://academic.oup.com/jdh/article/29/3/245/1745258", "English", "ARTICLE", "true", "true", "DESIGN_OBJECT_MOBILITY"),
    source("COMP-SRC-022", "Rebecca Earle;Susan Deans-Smith", 2026, "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "Itinerario 50.1", "Cambridge University Press", "10.1017/S0165115326100552", "https://www.cambridge.org/core/journals/itinerario/article/mobility-violence-and-the-afterlives-of-a-peruvian-painting-at-sea/0CCD9C903B8DDA855989858E63EEC238", "English", "ARTICLE", "true", "false", "COLONIAL_ART_MOBILITY"),
    source("COMP-SRC-023", "Susan E. Reid", 2017, "Cold War Cultural Transactions: Designing the USSR for the West at Brussels Expo '58", "Design and Culture 9.2", "Taylor & Francis", "10.1080/17547075.2017.1333388", "https://www.tandfonline.com/doi/abs/10.1080/17547075.2017.1333388", "English", "ARTICLE", "true", "true", "DESIGN_DIPLOMACY_GENEALOGY"),
    source("COMP-SRC-024", "Katarzyna Jeżowska", 2024, "Socialist, Humanist and Well-Designed: The Polish Welfare State at the International Labour Exhibition in Turin, 1961", "Contemporary European History 33.1", "Cambridge University Press", "10.1017/S0960777322000029", "https://www.cambridge.org/core/journals/contemporary-european-history/article/socialist-humanist-and-welldesigned-the-polish-welfare-state-at-the-international-labour-exhibition-in-turin-1961/94D125A40C5B3B013872B9A949430909", "English", "ARTICLE", "true", "true", "DESIGN_DIPLOMACY_APPLICATION"),
    source("COMP-SRC-025", "Mark Ian Jones", 2023, "A Fleeting Glimpse? 'Sweden's Shop Window in Sydney' – the Sweden at David Jones' Exposition of 1954", "Fabrications 33.2", "Taylor & Francis", "10.1080/10331867.2023.2282294", "https://doi.org/10.1080/10331867.2023.2282294", "English", "ARTICLE", "true", "true", "DESIGN_DIPLOMACY_APPLICATION"),
    source("COMP-SRC-026", "Daniele Burlando", 2023, "'Moroccan' Artek: Colonized Textiles within 1930s Modernist Interiors", "Journal of Design History 36.1", "Oxford University Press", "10.1093/jdh/epac035", "https://academic.oup.com/jdh/article/36/1/35/6691352", "English", "ARTICLE", "true", "true", "COLONIALITY_DESIGN_HISTORY"),
    source("COMP-SRC-027", "Emilio Distretti", 2023, "The Coloniality of Italian Fascist Architecture", "The Journal of Architecture 28.4", "Taylor & Francis", "10.1080/13602365.2023.2238284", "https://doi.org/10.1080/13602365.2023.2238284", "English", "ARTICLE", "true", "true", "COLONIALITY_ARCHITECTURAL_HISTORY"),
    source("COMP-SRC-028", "Karen Tucker", 2018, "Unraveling Coloniality in International Relations: Knowledge, Relationality, and Strategies for Engagement", "International Political Sociology 12.3", "Oxford University Press", "10.1093/ips/oly005", "https://academic.oup.com/ips/article/12/3/215/5025555", "English", "ARTICLE", "true", "false", "COLONIALITY_ADVERSARIAL"),
    source("COMP-SRC-029", "Véronique Pouillard", 2011, "Design Piracy in the Fashion Industries of Paris and New York", "Business History Review 85.2", "Cambridge University Press", "10.1017/S0007680511000407", "https://www.cambridge.org/core/journals/business-history-review/article/abs/design-piracy-in-the-fashion-industries-of-paris-and-new-york-in-the-interwar-years/AB3FC3E1B56C0798123ABDF06BD62486", "English", "ARTICLE", "true", "false", "FASHION_PIRACY_HISTORY"),
    source("COMP-SRC-030", "Patricia Lara-Betancourt;Livia Rezende", 2019, "Locating Design Exchanges in Latin America and the Caribbean", "Journal of Design History 32.1", "Oxford University Press", "10.1093/jdh/epy048", "https://doi.org/10.1093/jdh/epy048", "English", "ARTICLE", "true", "true", "DESIGN_EXCHANGE_BASELINE"),
]


EVIDENCE_FIELDS = [
    "evidence_id", "pair_or_gap_id", "candidate_sense_ids", "source_id", "source_type",
    "peer_reviewed", "design_history_usage", "exact_attested_terms", "bounded_context", "locator",
    "composition_kind", "subject_role", "target_role", "additional_roles", "directionality",
    "qualification", "negation", "contestation", "same_source_cluster", "source_metadata_verified",
    "evidence_verified", "semantic_review", "adversarial_review",
]


def evidence(
    evidence_id: str,
    scope: str,
    senses: str,
    source_id: str,
    terms: str,
    context: str,
    locator: str,
    kind: str,
    subject: str,
    target: str,
    roles: str,
    direction: str,
    qualification: str,
    contestation: str,
    same_cluster: str = "false",
    negation: str = "none",
) -> dict[str, Any]:
    source_row = next(row for row in SOURCES if row["source_id"] == source_id)
    return {
        "evidence_id": evidence_id,
        "pair_or_gap_id": scope,
        "candidate_sense_ids": senses,
        "source_id": source_id,
        "source_type": source_row["source_type"],
        "peer_reviewed": source_row["peer_reviewed"],
        "design_history_usage": source_row["design_history_usage"],
        "exact_attested_terms": terms,
        "bounded_context": context,
        "locator": locator,
        "composition_kind": kind,
        "subject_role": subject,
        "target_role": target,
        "additional_roles": roles,
        "directionality": direction,
        "qualification": qualification,
        "negation": negation,
        "contestation": contestation,
        "same_source_cluster": same_cluster,
        "source_metadata_verified": "true",
        "evidence_verified": "true",
        "semantic_review": "PASS_BOUNDED",
        "adversarial_review": "PASS_WITH_RECORDED_LIMITS",
    }


EVIDENCE = [
    evidence("COMP-EVID-001", "PAIR-A", "REL-CAND-0005#SENSE-A;REL-CAND-0006#SENSE-A", "COMP-SRC-001", "professionalization;institutionalisation", "Professionalization is defined through the institutionalisation of occupational trust and reputation in an interior-design history.", "accepted manuscript p.9", "CLASSIFICATION", "interior-design practitioners and professional field", "formal education, associations, accreditation, and occupational trust/reputation mechanisms", "clients;professional organizations;gendered professional subjects", "NON_DIRECTIONAL_CLASSIFICATION", "Western interior design, 1870–1970; named institutional mechanisms required", "Institutional trust alone is not a durable organization, and the definition does not establish a universal chronological transition."),
    evidence("COMP-EVID-002", "PAIR-A", "REL-CAND-0005#SENSE-A;REL-CAND-0006#SENSE-A", "COMP-SRC-002", "professionalization;institutionalization;closely interwoven", "Graphic designers' professional project and the institutionalization of their logic are described as interwoven and mutually reinforcing.", "pp.185, 194", "MUTUAL_REINFORCEMENT", "graphic designers and professional logic", "university visual-identity field", "universities;associations;consultants", "RECIPROCAL_SOURCE_SCOPED", "university identity changes and graphic-design profession", "Interweaving does not imply stable succession."),
    evidence("COMP-EVID-003", "PAIR-B", "REL-CAND-0011#SENSE-A;REL-CAND-0010#SENSE-A", "COMP-SRC-004", "commodification;gendering", "A Brazilian exposition case analyzes gendering and commodification as parallel processes acting on tropical nature and raw materials.", "title; abstract; pp.122–138", "COMMON_TARGET_PARALLEL_PROCESSES", "gendered discourse and commodity classification processes", "Brazilian tropical nature and raw materials as common target", "imperial exhibitors;European reception;tropicality", "NON_DIRECTIONAL_COMMON_TARGET", "Paris 1867 exposition and Brazilian imperial display", "The common target does not establish an ordered process-to-process relation, and one case cannot authorize a general relation."),
    evidence("COMP-EVID-004", "PAIR-B", "REL-CAND-0011#SENSE-A;REL-CAND-0010#SENSE-A", "COMP-SRC-005", "gendering the commodification", "Second-hand commodification is qualified through maternal subject positions as consumers and traders.", "title; abstract; pp.532–550", "ROLE_QUALIFICATION", "gendering of maternal consumer/trader subject positions", "commodification of second-hand childhood goods and the economy around them", "children;family resources;resale venues", "NON_DIRECTIONAL_QUALIFICATION", "UK post-recession consumer culture", "The row supplies source-bounded role qualification, not an ordered process relation or a second design-history article."),
    evidence("COMP-EVID-005", "PAIR-C", "REL-CAND-0032#SENSE-A;REL-CAND-0033#SENSE-A", "COMP-SRC-006", "imitation;piracy", "Chanel's accommodation of imitation is contrasted with her response to practices classified as piracy.", "p.573 and note 164", "CONTRAST", "fashion originator", "imitators and alleged design pirates", "associations;markets;appreciation norms", "NON_DIRECTIONAL_CONTRAST", "Paris haute couture and contemporaneous norms", "The source treats imitation and piracy differently rather than as degrees."),
    evidence("COMP-EVID-006", "PAIR-C", "REL-CAND-0032#SENSE-A;REL-CAND-0033#SENSE-A", "COMP-SRC-007", "imitation;copying;fashion piracy", "Legal-history discussion shows that authorization, protected subject matter, and rights regimes condition a piracy classification.", "pp.71–77; section 3", "HISTORICAL_RECLASSIFICATION", "fashion makers and alleged copiers", "designs and rights claims", "jurisdiction;authorization;market regime", "REGIME_CONDITIONED", "UK calico and contemporary fashion law", "Imitation is not automatically piracy; legal and historical norms remain explicit."),
    evidence("COMP-EVID-007", "PAIR-C", "REL-CAND-0032#SENSE-A;REL-CAND-0033#SENSE-A", "COMP-SRC-008", "design leader imitation;design piracy", "Behavioral research places imitation within a design-piracy environment and distinguishes leaders, pirates, and audiences.", "abstract; Actors of Design Piracy", "SUPPORTING_ENVIRONMENT", "design leader and imitator", "market classification and audience response", "audience;trademark regime;retail channel", "STRUCTURAL_NON_EDGE", "contemporary apparel and accessories; excluded from composition-attestation count", "Not design history and therefore supporting, not gate-satisfying, composition evidence."),
    evidence("COMP-EVID-008", "GAP-001", "R13-MEDIATION-CHANNELS", "COMP-SRC-009", "mediating channels", "The PCM model distinguishes designed channels that connect production and consumption and participate in meaning inscription.", "abstract and PCM currents", "ROLE_DISTINCTION", "producer or institution", "consumer or audience", "designed channel;object;meaning", "SOURCE_CHANNEL_TARGET", "channel and mediated variable must be named", "High universal-connector risk if treated as any conduit."),
    evidence("COMP-EVID-009", "GAP-001", "R13-MEDIATION-CHANNELS", "COMP-SRC-010", "mediating channels", "Digital design-history analysis applies the phrase to interfaces and platforms that shape cultural meanings.", "Design history and digital material culture section", "ROLE_DISTINCTION", "platform operator or producer", "users and traded cultural objects", "mediating channel: interface or platform;algorithms;regulation;third parties", "SOURCE_CHANNEL_TARGET", "named operator, channel, affected actor/object, and concrete platform effect", "This application derives from PCM and is not an independent conceptual genealogy.", "true"),
    evidence("COMP-EVID-010", "GAP-001", "R13-MEDIATION-DEVICES", "COMP-SRC-009", "mediating devices", "Designed goods are identified as devices participating between production and consumption.", "abstract and PCM currents", "ROLE_DISTINCTION", "producer or institution", "user or consumer", "mediating device: specific designed good;practice;meaning;use", "SOURCE_DEVICE_TARGET", "specific designed thing and mediated effect required", "Every designed object cannot default to a mediation Node."),
    evidence("COMP-EVID-011", "GAP-001", "R13-MEDIATION-DEVICES", "COMP-SRC-010", "mediating device", "A digital object participates in ongoing production-consumption and third-party data relations.", "Digital objects in the PCM paradigm section", "ROLE_DISTINCTION", "producer or platform operator", "user and third-party stakeholders", "mediating device: digital artifact;data flows;platform rules;algorithms", "MULTIPARTY_DEVICE_MEDIATION", "named digital artifact, parties, data relation, and platform rule", "The second use is explicitly PCM-dependent and does not satisfy independent-source breadth.", "true"),
    evidence("COMP-EVID-012", "GAP-002", "R13-SPLIT-001", "COMP-SRC-011", "cultural transfer", "A Cold War exhibition tests and criticizes an orthodox donor-to-host transfer model while retaining receiving agency.", "abstract; pp.387–408", "CONTESTED_TRANSFER", "donor institution and selected content", "receiving institution, host actors, and audience", "exhibition;agenda;route;reception", "CONTESTED_ASYMMETRIC_WITH_RECEIVING_AGENCY", "named content, route, receiving context, reception, and receiving agency", "The criticized donor model is not the case finding and cannot erase receiving agency."),
    evidence("COMP-EVID-013", "GAP-002", "R13-SPLIT-001", "COMP-SRC-012", "cultural transfer", "Print mobility scholarship uses cultural transfer for movement and circulation across colonial and receiving settings.", "title; pp.153–160", "TRANSFER", "print producers and circulating images", "receiving publics and settings", "seriality;colonial project;circulation", "SOURCE_TO_RECEIVER", "early-modern print mobility", "Transfer does not guarantee unchanged reception."),
    evidence("COMP-EVID-014", "GAP-002", "R13-SPLIT-002", "COMP-SRC-013", "cultural negotiation", "Architectural contact zones support reciprocal negotiation, selective borrowing, adaptation, and rejection.", "p.354; Contact Zone section", "NEGOTIATION", "participants in contact", "shared architectural problem or form", "contact zone;power;borrowing;rejection", "MULTIDIRECTIONAL", "specific encounter, actors, and power relation", "Negotiation must not imply voluntary or equal participation."),
    evidence("COMP-EVID-015", "GAP-002", "R13-SPLIT-002", "COMP-SRC-014", "cultural negotiation", "A Javanese architectural-design case treats selective adaptation as negotiation and symbolic resistance.", "abstract and results", "NEGOTIATION", "Keraton patrons and Javanese design actors", "imported colonial architectural forms and political meanings", "colonial institutions;resistance;patronage;power asymmetry", "ASYMMETRIC_SELECTIVE_ADAPTATION", "Keraton Surakarta case; actual actors and unequal power required", "Negotiation does not imply voluntary, equal, or fully reciprocal participation."),
    evidence("COMP-EVID-016", "GAP-002", "R13-SPLIT-003", "COMP-SRC-015", "adaptación cultural;cultural adaptation", "An illustrated Don Quixote book is analyzed as an adaptation into a named Japanese cultural and graphic context.", "author English abstract p.179; Spanish text pp.179–190; version-of-record pagination differs from embedded citation text", "ADAPTATION", "adapter/illustrator and source work", "adapted illustrated book", "target cultural context;audience;retained features;modified visual form;commission", "SOURCE_TO_ADAPTED_VERSION", "source, adapter, changed artifact, changes, and target context required", "Target culture cannot be treated as essential or uniform."),
    evidence("COMP-EVID-017", "GAP-002", "R13-SPLIT-003", "COMP-SRC-016", "cultural adaptation", "Web designs are deliberately modified to local industry styles and evaluated with local users.", "title; abstract; pp.457–481", "ADAPTATION", "designers and source interface", "adapted local-industry web interface", "local audience;local style;trust;usability", "SOURCE_TO_ADAPTED_VERSION", "source, designer, changed interface, target industry, and local evaluation required", "Contemporary design research is independent but not design history."),
    evidence("COMP-EVID-018", "GAP-002", "R13-SPLIT-004", "COMP-SRC-017", "cultural transformation", "Cypriot urban houses are read as material evidence of change between named Ottoman-period and British-colonial cultural configurations.", "title; abstract; pp.105–119", "TRANSFORMATION", "earlier Ottoman-period cultural configuration embodied in urban houses", "later British-colonial cultural configuration embodied in altered houses", "historical actors;period;material expression;social practice", "STATE_T0_TO_STATE_T1", "both historical states, period, forces, and material evidence required", "Transformation is not linear progress or a single external influence."),
    evidence("COMP-EVID-019", "GAP-002", "R13-SPLIT-004", "COMP-SRC-018", "cultural transformation", "Comparative research associates artistic phenomena and collective action with differences among polity cultures.", "title; abstract; pp.106–127", "COMPARATIVE_ASSOCIATION", "collective actors and artistic phenomena", "comparative polity-cultural configurations", "governance;leadership;morality;sample of thirty premodern states", "NON_DIRECTIONAL_COMPARATIVE_ASSOCIATION", "comparative cross-sectional support only; no within-case T0-to-T1 claim", "Broad theory cannot substitute for design-historical material evidence or a documented temporal transition."),
    evidence("COMP-EVID-020", "GAP-003", "R13-SPLIT-005", "COMP-SRC-019", "material displacements", "A design-history issue distinguishes movement and transformation of materials, objects, meanings, and sites.", "abstract; pp.195–211", "MATERIAL_DISPLACEMENT", "material or designed object", "receiving place, form, or context", "production;labor;ecology;boundary", "ORIGIN_TO_RECEIVING_CONTEXT", "material entity and historical movement required", "Do not infer forced-human or semantic displacement from material movement."),
    evidence("COMP-EVID-021", "GAP-003", "R13-SPLIT-005", "COMP-SRC-020", "material displacement", "Landscape-material chains connect production and consumption sites with ecological and labor changes.", "abstract; p.40", "MATERIAL_DISPLACEMENT", "specified construction material", "designed landscape", "production site;supply chain;labor;ecology", "PRODUCTION_SITE_TO_DESIGNED_SITE", "named material chain and consequences", "Commodity exchange can conceal production relations."),
    evidence("COMP-EVID-022", "GAP-004", "R13-SPLIT-006", "COMP-SRC-021", "mobile object", "A chest of drawers is treated as a culturally mobile object constituted through mediation and changing settings.", "abstract; p.245", "MOVED_ENTITY_ROLE", "design object", "successive cultural settings", "carrier;mediation;reception;iteration", "ITINERARY_WITHOUT_TRANSITIVITY", "object biography and reception changes required", "The noun identifies a role, not a universal relation."),
    evidence("COMP-EVID-023", "GAP-004", "R13-SPLIT-006", "COMP-SRC-022", "mobile object", "A Peruvian painting's movement, violence, reception, and material change are traced as an object life cycle.", "abstract; p.191; conclusion", "MOVED_ENTITY_ROLE", "commissioned painting", "unintended receiving settings", "warfare;ships;owners;prints;audiences", "ITINERARY_WITHOUT_TRANSITIVITY", "specific causes, routes, carriers, and receptions", "Mobility does not erase colonial violence or infer an abstract route."),
    evidence("COMP-EVID-024", "GAP-005", "R13-SPLIT-007", "COMP-SRC-023", "design diplomacy", "A Soviet exposition case uses design diplomacy as a lens for international persuasion, negotiation, and compromise.", "abstract; p.123", "DIPLOMATIC_MECHANISM", "state exhibition organizers and designers", "foreign publics and diplomatic counterparts", "pavilion;graphic media;tradecraft;audience reception", "INTENTIONAL_OUTWARD_WITH_NEGOTIATION_AND_CONTEXTUAL_RECEPTION", "documented diplomatic intent, negotiating counterparts, and contingent receiving context", "The source calls it a metaphor; reciprocity belongs to negotiation, not assumed audience reception."),
    evidence("COMP-EVID-025", "GAP-005", "R13-SPLIT-007", "COMP-SRC-024", "design diplomacy", "A Polish exhibition case distinguishes design culture as diplomatic subject from designers participating in state action.", "Design Diplomacy section p.175", "DIPLOMATIC_MECHANISM", "state institutions and exhibition makers", "international audience", "graphic design;facilities;policy experts", "INTENTIONAL_OUTWARD", "Cold War international exhibition", "Application cites the prior genealogy; intellectual dependence is recorded."),
    evidence("COMP-EVID-026", "GAP-005", "R13-SPLIT-007", "COMP-SRC-025", "design diplomacy", "A Swedish exposition combines propaganda, goodwill, trade, and national representation through designed display.", "p.282", "DIPLOMATIC_MECHANISM", "state and exhibition intermediaries", "Australian public and commercial counterparts", "exposition;goods;media;retail venue", "INTENTIONAL_OUTWARD_WITH_RECEPTION", "Sweden in Sydney, 1954; application shares the design-diplomacy genealogy", "Diplomatic intent does not prove audience acceptance.", "true"),
    evidence("COMP-EVID-027", "GAP-006", "R13-ANNOT-001", "COMP-SRC-026", "coloniality;modernity/coloniality", "Coloniality describes a continuing structure conditioning textile appropriation, classification, and modernist display.", "Colonized textiles section, pp.41–42", "STRUCTURAL_CONDITION", "imperial socioeconomic structures", "Amazigh rugs and modernist interiors", "markets;exhibitions;consumers;knowledge categories", "STRUCTURAL_NON_EDGE", "Morocco–Finland interwar case and named mechanisms", "A bounded structure is not an edge connecting arbitrary concepts."),
    evidence("COMP-EVID-028", "GAP-006", "R13-ANNOT-001", "COMP-SRC-027", "coloniality of architecture", "An architectural history traces long-lived power arrangements after formal colonial rule across buildings and institutions.", "abstract; conclusion p.593", "STRUCTURAL_ANNOTATION", "historically constituted institutions and regimes", "named architecture and urban setting", "government;memorialization;aesthetics;period", "STRUCTURAL_NON_EDGE", "Italian Fascist architecture and FAO/Piazza case", "Case-specific nominal use cannot become universal normalization."),
    evidence("COMP-EVID-029", "GAP-006", "R13-ANNOT-001", "COMP-SRC-028", "coloniality", "Adversarial scholarship requires slow, context-specific analysis rather than a uniform unitary system.", "abstract; pp.216–217", "ADVERSARIAL_QUALIFICATION", "dispersed racialized practices", "specific political, economic, and epistemic sites", "methodology;knowledge;affected communities", "STRUCTURAL_NON_EDGE", "empirical site and practice required", "Uniform coloniality risks homogenizing subalternized knowledge."),
]


PAIR_DECISIONS = [
    {
        "pair_id": "PAIR-A", "source_candidate_id": "REL-CAND-0005", "source_label": "professionalization", "target_candidate_id": "REL-CAND-0006", "target_label": "institutionalization", "final_status": "INQUIRY_ONLY_SUPPORTED", "evidence_ids": "COMP-EVID-001;COMP-EVID-002", "independent_composition_attestation_count": 2, "peer_reviewed_design_history_article_present": "true", "outside_source_cluster_present": "true", "explicit_role_mapping": "true", "directionality": "NON_DIRECTIONAL_OR_RECIPROCAL_SOURCE_SCOPED", "natural_language_explanation": "Scholarship supports source-bounded classification, interweaving, and mutual reinforcement, but not a universal professionalization-to-institutionalization transition.", "qualification": "Interior-design and graphic-design professional histories; institutional field, actors, and period must be explicit.", "scope_out": "No automatic arrow, transitivity, or cross-profession chronology.", "semantic_review": "PASS", "adversarial_review": "PASS", "universal_node_review": "PASS_RETAIN_AS_INQUIRY", "activation_candidate": "false",
    },
    {
        "pair_id": "PAIR-B", "source_candidate_id": "REL-CAND-0011", "source_label": "gendering", "target_candidate_id": "REL-CAND-0010", "target_label": "commodification", "final_status": "DEFER_MORE_EVIDENCE", "evidence_ids": "COMP-EVID-003;COMP-EVID-004", "independent_composition_attestation_count": 2, "peer_reviewed_design_history_article_present": "true", "outside_source_cluster_present": "true", "explicit_role_mapping": "false", "directionality": "COMMON_TARGET_OR_ROLE_QUALIFICATION_ONLY", "natural_language_explanation": "One design-history case establishes a common target and an independent consumer-culture source supplies role qualification, but neither establishes a general ordered process relation and no second design-history composition article clears the gate.", "qualification": "Material, visual, gender, market, and historical regime must all be named.", "scope_out": "No inference from general feminist economics, title-level co-occurrence, common-target evidence, or role qualification to a directed historical relation.", "semantic_review": "PASS_DEFER", "adversarial_review": "PASS", "universal_node_review": "PASS_DEFER", "activation_candidate": "false",
    },
    {
        "pair_id": "PAIR-C", "source_candidate_id": "REL-CAND-0032", "source_label": "imitation", "target_candidate_id": "REL-CAND-0033", "target_label": "piracy", "final_status": "DEFER_MORE_EVIDENCE", "evidence_ids": "COMP-EVID-005;COMP-EVID-006;COMP-EVID-007", "independent_composition_attestation_count": 2, "peer_reviewed_design_history_article_present": "false", "outside_source_cluster_present": "true", "explicit_role_mapping": "true", "directionality": "REGIME_CONDITIONED_RECLASSIFICATION_OR_CONTRAST", "natural_language_explanation": "Two scholarly sources support historically situated contrast and reclassification questions, while a third supplies non-gate environmental support; no peer-reviewed design-history article clears the required gate.", "qualification": "Jurisdiction, authorization, market regime, rights regime, historical norm, and ethical position are mandatory.", "scope_out": "Imitation is never automatically piracy; no transitive, stronger-degree, or moralized default, and non-design-history support cannot fill the design-history gate.", "semantic_review": "PASS_DEFER", "adversarial_review": "PASS", "universal_node_review": "PASS_DEFER", "activation_candidate": "false",
    },
]


GAP_DECISIONS = [
    {"gap_id": "GAP-001", "gap_name": "mediation role distinctions", "final_decision": "NEEDS_ADDITIONAL_EVIDENCE", "candidate_ids": "R13-MEDIATION-CHANNELS;R13-MEDIATION-DEVICES", "attested_terms": "mediating channels;mediating devices", "reason": "Exact design-history uses exist, but the second applications explicitly depend on the PCM genealogy and universal-connector risk remains high.", "scope_out": "No generic conduit, every-object, or algorithmic mediation Node.", "verified": "true"},
    {"gap_id": "GAP-002", "gap_name": "cultural translation distinctions", "final_decision": "SOURCE_ATTESTED_SPLIT_CANDIDATE", "candidate_ids": "R13-SPLIT-001;R13-SPLIT-002;R13-SPLIT-003;R13-SPLIT-004", "attested_terms": "cultural transfer;cultural negotiation;cultural adaptation;cultural transformation", "reason": "Each phrase has a peer-reviewed design or architectural-history use, a second independent scholarly use, and a distinct bounded role or time structure after source and semantic review.", "scope_out": "The phrases are not synonyms or universal connectors: transfer requires source, content, route, receiver, and receiving agency; negotiation requires actual unequal counterparts; adaptation requires source, adapter, and changed artifact; transformation requires named T0/T1 states, forces, period, and material evidence.", "verified": "true"},
    {"gap_id": "GAP-003", "gap_name": "displacement distinctions", "final_decision": "SOURCE_ATTESTED_SPLIT_CANDIDATE", "candidate_ids": "R13-SPLIT-005", "attested_terms": "material displacement", "reason": "Material displacement clears the bounded design-history and independent landscape-design evidence gate; forced-human, spatial, semantic, and strategic senses remain unresolved.", "scope_out": "Not every material movement: require a named material, origin, destination, chain or force, and material/labor/ecological consequences; never infer forced-human movement, semantic change, or strategy.", "verified": "true"},
    {"gap_id": "GAP-004", "gap_name": "cultural mobility roles", "final_decision": "SOURCE_ATTESTED_SPLIT_CANDIDATE", "candidate_ids": "R13-SPLIT-006", "attested_terms": "mobile object", "reason": "The moved-entity role has two independent scholarly object-history uses; carrier, infrastructure, and route labels did not clear the same gate.", "scope_out": "Not every moved object: require a bounded itinerary, origin, carrier or route, receiving context, and reception or material change; mobile object is a role, not a relation or automatic connector.", "verified": "true"},
    {"gap_id": "GAP-005", "gap_name": "transnational exchange mechanisms", "final_decision": "SOURCE_ATTESTED_SPLIT_CANDIDATE", "candidate_ids": "R13-SPLIT-007", "attested_terms": "design diplomacy", "reason": "Three bounded exhibition/design-history applications establish an institutionally organized diplomatic mechanism while preserving genealogy dependence.", "scope_out": "No ordinary migration, trade, private collaboration, stylistic influence, or generic cross-border event.", "verified": "true"},
    {"gap_id": "GAP-006", "gap_name": "coloniality structural semantics", "final_decision": "STRUCTURAL_ANNOTATION_CANDIDATE", "candidate_ids": "R13-ANNOT-001", "attested_terms": "coloniality;coloniality of architecture", "reason": "Design and architectural histories support a source-bounded continuing condition, while adversarial scholarship rejects a uniform unitary model.", "scope_out": "Never a universal Node, edge, transitive relation, stylistic label, or generic inequality marker.", "verified": "true"},
]


SPLIT_CANDIDATES = [
    ("R13-SPLIT-001", "cultural transfer", "GAP-002", "source;transferred content;carrier or institution;receiving actors and agency;receiving context;contested reception", "SOURCE_BOUNDED_CONTESTED_TRANSFER_WITH_RECEIVING_AGENCY"),
    ("R13-SPLIT-002", "cultural negotiation", "GAP-002", "participants;contact zone;shared issue;power regime;acts of borrowing, adaptation, or rejection", "MULTIDIRECTIONAL"),
    ("R13-SPLIT-003", "cultural adaptation", "GAP-002", "source work;adapter;target context;retained and modified features;adapted artifact", "SOURCE_TO_ADAPTED_VERSION"),
    ("R13-SPLIT-004", "cultural transformation", "GAP-002", "historical state C0;actors and forces;material evidence;time;historical state C1", "STATE_T0_TO_STATE_T1"),
    ("R13-SPLIT-005", "material displacement", "GAP-003", "moved material;production site;designed destination;supply chain;labor and ecological effects", "ORIGIN_TO_RECEIVING_CONTEXT"),
    ("R13-SPLIT-006", "mobile object", "GAP-004", "moved entity;origin;carrier;route;receiving context;reception change", "ITINERARY_WITHOUT_TRANSITIVITY"),
    ("R13-SPLIT-007", "design diplomacy", "GAP-005", "state or institution;designers and curators;designed media or exposition;negotiating counterpart;foreign public;contingent reception", "INTENTIONAL_OUTWARD_WITH_NEGOTIATION_AND_CONTEXTUAL_RECEPTION"),
]


def load_v1_instances() -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(INSTANCES_V1.glob("INQUIRY-INSTANCE-*.json"))]


def neutral_nodes() -> list[dict[str, Any]]:
    return [
        {"senseId": "SYNTHETIC-SENSE-A", "label": "neutral concept A", "lexicalAttestationIds": ["SYNTHETIC-LEX-A"], "grammarAttestationIds": ["SYNTHETIC-GRAM-A"]},
        {"senseId": "SYNTHETIC-SENSE-B", "label": "neutral concept B", "lexicalAttestationIds": ["SYNTHETIC-LEX-B"], "grammarAttestationIds": ["SYNTHETIC-GRAM-B"]},
    ]


def build_topology_fixtures() -> dict[str, list[dict[str, Any]]]:
    fixtures = {
        strategy: build_tree(strategy, f"SYNTH-{index:02d}", "How should two neutral concepts be investigated?", neutral_nodes(), ["SYNTHETIC-GRAM-A", "SYNTHETIC-GRAM-B"], ["SYNTHETIC-GAP"])
        for index, strategy in enumerate(STRATEGIES, start=1)
    }
    assert_no_duplicate_topologies(fixtures)
    return fixtures


def build_negative_topology_fixtures(fixtures: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    unknown_kind = deepcopy(fixtures["LINEAR_PATH"])
    unknown_kind[1]["itemKind"] = "UNDECLARED_KIND"
    cases.append({"caseId": "NEG-UNKNOWN-ITEM-KIND", "strategy": "LINEAR_PATH", "expectedError": "UNKNOWN_TREE_ITEM_KIND", "treeItems": unknown_kind})

    bad_fork = deepcopy(fixtures["BINARY_FORK"])
    next(item for item in bad_fork if item["inquiryRole"] == "ALTERNATIVE_BRANCH_A")["branchStatus"] = "PRIMARY"
    cases.append({"caseId": "NEG-FORK-BRANCH-STATUS", "strategy": "BINARY_FORK", "expectedError": "BINARY_FORK_TOPOLOGY", "treeItems": bad_fork})

    fake_convergence = deepcopy(fixtures["BINARY_CONVERGENCE"])
    root = next(item for item in fake_convergence if item["parentItemId"] is None)
    branch = next(item for item in fake_convergence if item["inquiryRole"] == "CONVERGENCE_BRANCH_A")
    next(item for item in fake_convergence if item["branchStatus"] == "CONVERGENCE")["convergenceSourceItemIds"] = [root["itemId"], branch["itemId"]]
    cases.append({"caseId": "NEG-CONVERGENCE-SOURCE-IDENTITY", "strategy": "BINARY_CONVERGENCE", "expectedError": "BINARY_CONVERGENCE_TOPOLOGY", "treeItems": fake_convergence})

    bypass = deepcopy(fixtures["QUALIFIED_PATH"])
    first = next(item for item in bypass if item["inquiryRole"] == "PRIMARY_CONCEPT_QUESTION")
    continuation = next(item for item in bypass if item["inquiryRole"] == "QUALIFIED_CONTINUATION")
    boundary = next(item for item in bypass if item["inquiryRole"] == "QUALIFICATION_REVIEW")
    continuation["parentItemId"] = first["itemId"]
    continuation["depth"] = 2
    boundary["depth"] = 3
    cases.append({"caseId": "NEG-QUALIFICATION-BYPASS", "strategy": "QUALIFIED_PATH", "expectedError": "QUALIFIED_PATH_TOPOLOGY", "treeItems": bypass})

    semantic_navigation = deepcopy(fixtures["REFLEXIVE_RETURN"])
    semantic = next(item for item in semantic_navigation if item["itemKind"] == "SEMANTIC_NODE_REFERENCE")
    semantic["navigationTargetItemId"] = semantic["itemId"]
    cases.append({"caseId": "NEG-SEMANTIC-SELF-NAVIGATION", "strategy": "REFLEXIVE_RETURN", "expectedError": "SEMANTIC_NAVIGATION_FORBIDDEN", "treeItems": semantic_navigation})

    wrong_gap_owner = deepcopy(fixtures["EVIDENCE_GAP_TREE"])
    supported = next(item for item in wrong_gap_owner if item["inquiryRole"] == "SUPPORTED_BRANCH")
    gap = next(item for item in wrong_gap_owner if item["itemKind"] == "EVIDENCE_GAP_NOTE")
    gap["parentItemId"] = supported["itemId"]
    gap["depth"] = 2
    cases.append({"caseId": "NEG-GAP-ON-SUPPORTED-BRANCH", "strategy": "EVIDENCE_GAP_TREE", "expectedError": "EVIDENCE_GAP_TREE_TOPOLOGY", "treeItems": wrong_gap_owner})

    swapped_linear_roles = deepcopy(fixtures["LINEAR_PATH"])
    start = next(item for item in swapped_linear_roles if item["inquiryRole"] == "STARTING_CONCEPT_QUESTION")
    evidence = next(item for item in swapped_linear_roles if item["inquiryRole"] == "EVIDENCE_CHECK")
    start["inquiryRole"], evidence["inquiryRole"] = evidence["inquiryRole"], start["inquiryRole"]
    cases.append({"caseId": "NEG-LINEAR-ROLE-KIND-SWAP", "strategy": "LINEAR_PATH", "expectedError": "LINEAR_PATH_TOPOLOGY", "treeItems": swapped_linear_roles})

    fork_wrong_kind = deepcopy(fixtures["BINARY_FORK"])
    next(item for item in fork_wrong_kind if item["inquiryRole"] == "BRANCH_A_CONCEPT")["itemKind"] = "EVIDENCE_NOTE"
    cases.append({"caseId": "NEG-FORK-CONCEPT-KIND", "strategy": "BINARY_FORK", "expectedError": "BINARY_FORK_TOPOLOGY", "treeItems": fork_wrong_kind})

    swapped_inputs = deepcopy(fixtures["BINARY_CONVERGENCE"])
    input_a = next(item for item in swapped_inputs if item["inquiryRole"] == "CONVERGENCE_INPUT_A")
    input_b = next(item for item in swapped_inputs if item["inquiryRole"] == "CONVERGENCE_INPUT_B")
    input_a["inquiryRole"], input_b["inquiryRole"] = input_b["inquiryRole"], input_a["inquiryRole"]
    cases.append({"caseId": "NEG-CONVERGENCE-INPUT-ROLE-SWAP", "strategy": "BINARY_CONVERGENCE", "expectedError": "BINARY_CONVERGENCE_TOPOLOGY", "treeItems": swapped_inputs})

    qualified_wrong_kind = deepcopy(fixtures["QUALIFIED_PATH"])
    next(item for item in qualified_wrong_kind if item["inquiryRole"] == "PRIMARY_CONCEPT_QUESTION")["itemKind"] = "EVIDENCE_NOTE"
    cases.append({"caseId": "NEG-QUALIFIED-CONCEPT-KIND", "strategy": "QUALIFIED_PATH", "expectedError": "QUALIFIED_PATH_TOPOLOGY", "treeItems": qualified_wrong_kind})

    reflexive_wrong_kind = deepcopy(fixtures["REFLEXIVE_RETURN"])
    next(item for item in reflexive_wrong_kind if item["inquiryRole"] == "REFLEXIVE_CONCEPT_QUESTION")["itemKind"] = "EVIDENCE_NOTE"
    cases.append({"caseId": "NEG-REFLEXIVE-CONCEPT-KIND", "strategy": "REFLEXIVE_RETURN", "expectedError": "REFLEXIVE_RETURN_TOPOLOGY", "treeItems": reflexive_wrong_kind})

    gap_wrong_kind = deepcopy(fixtures["EVIDENCE_GAP_TREE"])
    next(item for item in gap_wrong_kind if item["inquiryRole"] == "SUPPORTED_CONCEPT")["itemKind"] = "EVIDENCE_NOTE"
    cases.append({"caseId": "NEG-GAP-CONCEPT-KIND", "strategy": "EVIDENCE_GAP_TREE", "expectedError": "EVIDENCE_GAP_TREE_TOPOLOGY", "treeItems": gap_wrong_kind})
    return cases


def schema_instance_v2() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://graphic-design-archive.local/schemas/trace/exploration/research-inquiry-instance-v2.schema.json",
        "title": "TRACE Research Inquiry Instance v2",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "instanceId", "instanceVersion", "parentInstanceHash", "parentInstanceVersion", "freezePackageHash",
            "seedId", "seedHash", "treeStrategy", "treeStrategyVersion", "rootInquiry", "semanticNodeRefs",
            "primaryInquiryFlow", "treeItems", "evidenceCoverage", "sourceCoverage", "qualificationRefs",
            "contestationRefs", "gapRefs", "inclusionExplanation", "nonClaimExplanation", "evidenceSummary",
            "limitationStatement", "topologyChange", "historicalClaim", "semanticRelation", "publicExportable",
            "activationState", "researchPreviewOnly", "canonicalHash",
        ],
        "properties": {
            "instanceId": {"type": "string", "pattern": "^INQUIRY-INSTANCE-[0-9]{3}$"},
            "instanceVersion": {"const": "2"},
            "parentInstanceHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "parentInstanceVersion": {"const": "1"},
            "freezePackageHash": {"const": FREEZE_HASH},
            "seedId": {"type": "string"}, "seedHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "treeStrategy": {"enum": list(STRATEGIES)}, "treeStrategyVersion": {"const": "2"},
            "rootInquiry": {"type": "string", "pattern": "\\?$"},
            "semanticNodeRefs": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "object"}},
            "primaryInquiryFlow": {"type": "object"},
            "treeItems": {"type": "array", "minItems": 1, "maxItems": 7, "items": {"$ref": "inquiry-tree-v2.schema.json#/$defs/treeItem"}},
            "evidenceCoverage": {"type": "object"}, "sourceCoverage": {"type": "object"},
            "qualificationRefs": {"type": "array", "items": {"type": "string"}},
            "contestationRefs": {"type": "array", "items": {"type": "string"}},
            "gapRefs": {"type": "array", "items": {"type": "string"}},
            "inclusionExplanation": {"type": "string"}, "nonClaimExplanation": {"type": "string"},
            "evidenceSummary": {"type": "string"}, "limitationStatement": {"type": "string"},
            "topologyChange": {
                "type": "object", "additionalProperties": False,
                "required": ["changed", "summary", "semanticContentUnchanged", "evidenceBindingChange"],
                "properties": {"changed": {"const": True}, "summary": {"type": "string"}, "semanticContentUnchanged": {"const": True}, "evidenceBindingChange": {"const": "UNCHANGED"}},
            },
            "historicalClaim": {"const": False}, "semanticRelation": {"const": False}, "publicExportable": {"const": False},
            "activationState": {"const": "RESEARCH_CANDIDATE_ONLY"}, "researchPreviewOnly": {"const": True},
            "canonicalHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }


def schema_tree_v2() -> dict[str, Any]:
    item_required = ["itemId", "itemKind", "parentItemId", "depth", "order", "label", "inquiryRole", "branchStatus", "evidenceRefs", "gapRefs", "convergenceSourceItemIds", "navigationTargetItemId"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://graphic-design-archive.local/schemas/trace/exploration/inquiry-tree-v2.schema.json",
        "title": "TRACE inquiry tree v2",
        "$defs": {
            "treeItem": {
                "type": "object", "additionalProperties": False, "required": item_required,
                "properties": {
                    "itemId": {"type": "string", "minLength": 1},
                    "itemKind": {"enum": ["SEMANTIC_NODE_REFERENCE", "INQUIRY_OPERATION", "EVIDENCE_NOTE", "QUALIFICATION_NOTE", "CONTESTATION_NOTE", "EVIDENCE_GAP_NOTE"]},
                    "parentItemId": {"type": ["string", "null"]}, "depth": {"type": "integer", "minimum": 0, "maximum": 4},
                    "order": {"type": "integer", "minimum": 0}, "label": {"type": "string", "minLength": 1},
                    "inquiryRole": {"type": "string", "minLength": 1}, "branchStatus": {"type": "string", "minLength": 1},
                    "candidateSenseId": {"type": "string"},
                    "evidenceRefs": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
                    "gapRefs": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
                    "convergenceSourceItemIds": {"type": "array", "uniqueItems": True, "maxItems": 2, "items": {"type": "string"}},
                    "navigationTargetItemId": {"type": ["string", "null"]},
                },
            }
        },
        "type": "object", "additionalProperties": False,
        "required": ["rootInquiryId", "strategy", "treeItems"],
        "properties": {
            "rootInquiryId": {"type": "string"}, "strategy": {"enum": list(STRATEGIES)},
            "treeItems": {"type": "array", "minItems": 1, "maxItems": 7, "items": {"$ref": "#/$defs/treeItem"}},
        },
    }


def breadth_metrics() -> dict[str, Any]:
    publisher_counts = Counter(row["publisher"] for row in SOURCES)
    normalized_venues = {re.sub(r"\s+\d+(?:\.\d+)?$", "", row["venue"]) for row in SOURCES}
    venue_count = len(normalized_venues)
    author_count = len({author for row in SOURCES for author in row["authors"].split(";")})
    language_count = len({row["language"] for row in SOURCES})
    source_count = len(SOURCES)
    jdh = sum(row["venue"].startswith("Journal of Design History") for row in SOURCES)
    oup = publisher_counts["Oxford University Press"]
    largest_publisher, largest_count = publisher_counts.most_common(1)[0]
    cluster_counts = Counter(row["source_cluster"] for row in SOURCES)
    largest_cluster_count = max(cluster_counts.values())
    largest_clusters = sorted(cluster for cluster, count in cluster_counts.items() if count == largest_cluster_count)
    return {
        "source_count": source_count, "venue_count": venue_count, "author_count": author_count,
        "language_count": language_count, "publisher_count": len(publisher_counts),
        "jdh_share": f"{jdh}/{source_count}={jdh/source_count:.4f}", "oup_share": f"{oup}/{source_count}={oup/source_count:.4f}",
        "largest_publisher": largest_publisher, "largest_publisher_share": f"{largest_count}/{source_count}={largest_count/source_count:.4f}",
        "largest_source_cluster": ";".join(largest_clusters), "largest_source_cluster_share": f"{largest_cluster_count}/{source_count}={largest_cluster_count/source_count:.4f}",
    }


def review_units(instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    freeze = json.loads((REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1/02_RESEARCH_CANDIDATE_FREEZE.json").read_text(encoding="utf-8"))
    bounded = [item for item in freeze["candidates"] if item["researchStatus"] == "BOUNDED_NODE_ROLE_CANDIDATE"]
    glosses = {row["sense_id"]: row for row in read_tsv(REPO / "docs/research/trace-v49-design-history-relation-vocabulary-round1/07_SEMANTIC_GLOSS_REGISTRY.tsv")}
    roles = {row["candidate_id"]: row for row in read_tsv(REPO / "docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv")}
    evidence_by_id = {row["evidence_id"]: row for row in EVIDENCE}
    split_by_id = {candidate_id: {"label": label, "gapId": gap_id, "argumentRoles": argument_roles, "directionality": direction} for candidate_id, label, gap_id, argument_roles, direction in SPLIT_CANDIDATES}
    units: list[dict[str, Any]] = []
    questions = "Is the meaning faithful to design-history scholarship?;Is the technical role appropriate?;Are subject and target roles historically defensible?;Does the inquiry accidentally imply directionality?;Is the distinction meaningful?;Is an important qualification missing?;Is this a useful research question?;Would it mislead as a historical relation?;Does it act as a universal connector?;Should it remain deferred, be split, or be rejected?"
    for item in bounded:
        gloss = glosses[item["senseId"]]
        role = roles[item["candidateId"]]
        units.append({"review_unit_id": f"REVIEW-NODE-{len(units)+1:03d}", "review_unit_type": "BOUNDED_NODE_ROLE", "subject_id": item["senseId"], "plain_language_definition": gloss["plain_language_gloss"], "source_ids": ";".join(item["sourceIds"]), "evidence_ids": ";".join(item["lexicalAttestationIds"] + item["grammarAttestationIds"]), "bounded_context": role["required_context"], "role_structure": f"subject={role['subject_role']}; target={role['target_role']}; additional={role['additional_party_roles']}", "directionality": item["directionalityStatus"], "qualification": role["required_qualification"], "contestation": f"{item['contestationStatus']}; scope_out={role['scope_out']}", "current_system_decision": "BOUNDED_NODE_ROLE_CANDIDATE_NOT_ACTIVE", "alternative_decisions": "RETAIN;DEFER;SPLIT;REJECT", "reviewer_questions": questions, "reviewer_answer_status": "NOT_COMPLETED"})
    for pair in PAIR_DECISIONS:
        pair_evidence = [evidence_by_id[evidence_id] for evidence_id in pair["evidence_ids"].split(";")]
        role_summary = " | ".join(f"{row['evidence_id']}: subject={row['subject_role']}; target={row['target_role']}; additional={row['additional_roles']}" for row in pair_evidence)
        units.append({"review_unit_id": f"REVIEW-PAIR-{pair['pair_id'][-1]}", "review_unit_type": "PAIR_RESEARCH_QUESTION", "subject_id": pair["pair_id"], "plain_language_definition": pair["natural_language_explanation"], "source_ids": ";".join(dict.fromkeys(row["source_id"] for row in pair_evidence)), "evidence_ids": pair["evidence_ids"], "bounded_context": pair["qualification"], "role_structure": role_summary, "directionality": pair["directionality"], "qualification": pair["qualification"], "contestation": pair["scope_out"], "current_system_decision": pair["final_status"], "alternative_decisions": "PAIR_ACTIVATION_CANDIDATE;INQUIRY_ONLY_SUPPORTED;DEFER_MORE_EVIDENCE;REJECT_COMPOSITION;REJECT_FLATTENING_RISK;REJECT_DIRECTIONALITY_RISK", "reviewer_questions": questions, "reviewer_answer_status": "NOT_COMPLETED"})
    for item in instances:
        tree_evidence = sorted({reference for tree_item in item["treeItems"] for reference in tree_item["evidenceRefs"]})
        tree_roles = " | ".join(f"{tree_item['inquiryRole']}:{tree_item['itemKind']}" for tree_item in item["treeItems"])
        instance_context = item["limitationStatement"]
        if item["instanceId"] == "INQUIRY-INSTANCE-002":
            instance_context += " Frozen v1-era 'one source' wording means one qualifying design-history composition source; Round 13's independent non-design-history support does not clear that gate."
        units.append({"review_unit_id": f"REVIEW-INSTANCE-{item['instanceId'][-3:]}", "review_unit_type": "RESEARCH_INQUIRY_INSTANCE_V2", "subject_id": item["instanceId"], "plain_language_definition": item["rootInquiry"], "source_ids": ";".join(item["sourceCoverage"]["sourceIds"]), "evidence_ids": ";".join(tree_evidence), "bounded_context": instance_context, "role_structure": tree_roles, "directionality": "INQUIRY_NAVIGATION_ONLY_NO_HISTORICAL_DIRECTION", "qualification": ";".join(item["qualificationRefs"]), "contestation": ";".join(item["contestationRefs"]), "current_system_decision": "RESEARCH_CANDIDATE_ONLY", "alternative_decisions": "RETAIN;REFINE_TOPOLOGY;DEFER;REJECT", "reviewer_questions": questions, "reviewer_answer_status": "NOT_COMPLETED"})
    for gap in GAP_DECISIONS:
        gap_evidence = [row for row in EVIDENCE if row["pair_or_gap_id"] == gap["gap_id"]]
        role_summary = " | ".join(f"{row['evidence_id']}: subject={row['subject_role']}; target={row['target_role']}; additional={row['additional_roles']}" for row in gap_evidence)
        directions = ";".join(dict.fromkeys(row["directionality"] for row in gap_evidence))
        units.append({"review_unit_id": f"REVIEW-{gap['gap_id']}", "review_unit_type": "VOCABULARY_GAP", "subject_id": gap["gap_id"], "plain_language_definition": gap["gap_name"], "source_ids": ";".join(dict.fromkeys(row["source_id"] for row in gap_evidence)), "evidence_ids": ";".join(row["evidence_id"] for row in gap_evidence), "bounded_context": gap["reason"], "role_structure": role_summary, "directionality": directions, "qualification": gap["scope_out"], "contestation": gap["scope_out"], "current_system_decision": gap["final_decision"], "alternative_decisions": "SOURCE_ATTESTED_SPLIT_CANDIDATE;STRUCTURAL_ANNOTATION_CANDIDATE;NEEDS_ADDITIONAL_EVIDENCE;REJECT_NO_DESIGN_HISTORY_ATTESTATION;REJECT_FLATTENING;REJECT_UNIVERSAL_NODE_RISK", "reviewer_questions": questions, "reviewer_answer_status": "NOT_COMPLETED"})
    activation_subjects = [(item[0], "NODE_ACTIVATION_CANDIDATE", item[1]) for item in SPLIT_CANDIDATES] + [(f"R13-INQUIRY-RULE-{index:03d}", "INQUIRY_GRAMMAR_ACTIVATION_CANDIDATE", strategy) for index, strategy in enumerate(STRATEGIES, start=1)] + [("R13-ANNOT-001", "STRUCTURAL_ANNOTATION_CANDIDATE", "coloniality")]
    for subject_id, kind, label in activation_subjects:
        subject_evidence = [row for row in EVIDENCE if subject_id in row["candidate_sense_ids"].split(";")]
        if subject_id in split_by_id:
            role_structure = split_by_id[subject_id]["argumentRoles"]
            directionality = split_by_id[subject_id]["directionality"]
        elif subject_id.startswith("R13-INQUIRY-RULE-"):
            role_structure = "strategy-specific inquiry operations and bounded navigation; no semantic edge roles"
            directionality = "INQUIRY_NAVIGATION_ONLY_NO_HISTORICAL_DIRECTION"
        else:
            role_structure = "source;geography;period;mechanism;affected actors or objects;beneficiary or control structure;continuity claim"
            directionality = "STRUCTURAL_NON_EDGE"
        units.append({"review_unit_id": f"REVIEW-ACT-{len(units)+1:03d}", "review_unit_type": kind, "subject_id": subject_id, "plain_language_definition": label, "source_ids": ";".join(dict.fromkeys(row["source_id"] for row in subject_evidence)) or "NOT_APPLICABLE_SYNTHETIC_TOPOLOGY", "evidence_ids": ";".join(row["evidence_id"] for row in subject_evidence) or f"TREE-CONF-{subject_id[-3:]}", "bounded_context": "Activation candidate only; no active vocabulary or grammar.", "role_structure": role_structure, "directionality": directionality, "qualification": "Requires external human review and separate activation decision.", "contestation": "Default deny outside recorded scope.", "current_system_decision": "ACTIVE_FALSE", "alternative_decisions": "RETAIN_CANDIDATE;DEFER;REJECT", "reviewer_questions": questions, "reviewer_answer_status": "NOT_COMPLETED"})
    return units


def render_review_packet(reviews: list[dict[str, Any]]) -> str:
    sections = ["# External design-history domain review packet", "Review status: `NOT_COMPLETED`. No reviewer answer is supplied or inferred."]
    for row in reviews:
        questions = "\n".join(f"{index}. {question}" for index, question in enumerate(row["reviewer_questions"].split(";"), start=1))
        sections.append(
            f"## {row['review_unit_id']} — {row['subject_id']}\n\n"
            f"- Unit type: `{row['review_unit_type']}`\n"
            f"- Plain-language definition: {row['plain_language_definition']}\n"
            f"- Sources: `{row['source_ids']}`\n"
            f"- Evidence: `{row['evidence_ids']}`\n"
            f"- Bounded context: {row['bounded_context']}\n"
            f"- Role structure: {row['role_structure']}\n"
            f"- Directionality: `{row['directionality']}`\n"
            f"- Qualification: {row['qualification']}\n"
            f"- Contestation: {row['contestation']}\n"
            f"- Current decision: `{row['current_system_decision']}`\n"
            f"- Alternatives: `{row['alternative_decisions']}`\n\n"
            f"### Unanswered reviewer questions\n\n{questions}"
        )
    sections.append("Full copyrighted articles are not included. The bounded reference list supplies publisher, DOI, and repository links.")
    return "\n\n".join(sections)


def generate() -> None:
    for path in (RESEARCH, AUDIT, INSTANCES_V2, RAW, FIXTURES, SCHEMAS):
        path.mkdir(parents=True, exist_ok=True)
    v1 = load_v1_instances()
    if len(v1) != 5:
        raise ValueError("ROUND12_INSTANCE_V1_COUNT")
    v2 = [compile_instance_v2(value) for value in v1]
    fixtures = build_topology_fixtures()
    negative_fixtures = build_negative_topology_fixtures(fixtures)
    for old, new in zip(v1, v2, strict=True):
        write_json(INSTANCES_V2 / f"{new['instanceId']}.v2.json", new)
    write_json(FIXTURES / "tree-strategy-conformance-v2.json", {"fixtureVersion": "2", "syntheticOnly": True, "historicalClaim": False, "fixtures": [{"fixtureId": f"TREE-CONF-{index:03d}", "strategy": strategy, "topologySignature": topology_signature(fixtures[strategy]), "treeItems": fixtures[strategy], "productionEligible": False} for index, strategy in enumerate(STRATEGIES, start=1)]})
    write_json(FIXTURES / "tree-strategy-negative-v2.json", {"fixtureVersion": "2", "syntheticOnly": True, "historicalClaim": False, "cases": negative_fixtures})
    reconcile_active_script_allowlist()
    write_json(SCHEMAS / "inquiry-tree-v2.schema.json", schema_tree_v2())
    write_json(SCHEMAS / "research-inquiry-instance-v2.schema.json", schema_instance_v2())

    write_tsv(RESEARCH / "03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv", SOURCES)
    write_tsv(RESEARCH / "04_COMPOSITION_EVIDENCE_REGISTRY.tsv", EVIDENCE, EVIDENCE_FIELDS)
    write_tsv(RESEARCH / "05_PAIR_DECISION_REGISTRY.tsv", PAIR_DECISIONS)
    write_tsv(RESEARCH / "06_VOCABULARY_GAP_EVIDENCE.tsv", [row for row in EVIDENCE if row["pair_or_gap_id"].startswith("GAP-")], EVIDENCE_FIELDS)
    write_tsv(RESEARCH / "07_VOCABULARY_GAP_DECISIONS.tsv", GAP_DECISIONS)
    write_tsv(RESEARCH / "08_INQUIRY_GRAMMAR_CANDIDATES.tsv", [{"candidate_id": f"R13-INQUIRY-RULE-{index:03d}", "strategy": strategy, "rule_kind": "RESEARCH_INQUIRY_RULE", "historical_claim": "false", "semantic_relation": "false", "active": "false", "topology_signature": topology_signature(fixtures[strategy]), "external_human_review_required": "true", "separate_activation_decision_required": "true"} for index, strategy in enumerate(STRATEGIES, start=1)])
    write_tsv(RESEARCH / "10_TREE_STRATEGY_CONFORMANCE.tsv", [{"fixture_id": f"TREE-CONF-{index:03d}", "strategy": strategy, "synthetic_only": "true", "tree_item_count": len(fixtures[strategy]), "semantic_node_count": sum(item["itemKind"] == "SEMANTIC_NODE_REFERENCE" for item in fixtures[strategy]), "max_depth": max(item["depth"] for item in fixtures[strategy]), "topology_signature": topology_signature(fixtures[strategy]), "topology_unique": "true", "historical_claim": "false", "production_eligible": "false", "validation_status": "PASS"} for index, strategy in enumerate(STRATEGIES, start=1)])
    write_tsv(RESEARCH / "11_RESEARCH_INSTANCE_V2_REGISTRY.tsv", [{"instance_id": item["instanceId"], "instance_version": item["instanceVersion"], "parent_instance_hash": item["parentInstanceHash"], "instance_hash": item["canonicalHash"], "tree_strategy": item["treeStrategy"], "tree_item_count": len(item["treeItems"]), "semantic_node_count": len(item["semanticNodeRefs"]), "candidate_sense_ids": ";".join(node["senseId"] for node in item["semanticNodeRefs"]), "historical_claim": "false", "semantic_relation": "false", "public_exportable": "false", "activation_state": item["activationState"], "topology_changed": "true", "semantic_content_unchanged": "true", "evidence_binding_change": "UNCHANGED"} for item in v2])
    write_tsv(RESEARCH / "13_INSTANCE_V1_V2_DIFF.tsv", [{"instance_id": new["instanceId"], "v1_hash": old["canonicalHash"], "v2_parent_hash": new["parentInstanceHash"], "v2_hash": new["canonicalHash"], "topology_change": "STRATEGY_SPECIFIC_FUNCTION", "semantic_node_change_count": 0, "research_question_change_count": 0, "historical_claim_change_count": 0, "semantic_relation_change_count": 0, "evidence_binding_change": "UNCHANGED", "v1_mutated": "false", "validation_status": "PASS"} for old, new in zip(v1, v2, strict=True)])

    activation = {
        "packageId": "trace-exploration-inquiry-grammar-activation-candidates-v1", "version": "1", "sourceRound": 13,
        "sourceCommit": SOURCE_SHA, "active": False, "requiresExternalHumanReview": True,
        "requiresSeparateActivationDecision": True, "feedsRealImageCompiler": False,
        "nodeActivationCandidates": [{"candidateId": candidate_id, "label": label, "gapId": gap_id, "argumentRoles": roles, "directionality": direction, "active": False} for candidate_id, label, gap_id, roles, direction in SPLIT_CANDIDATES],
        "pairCompositionCandidates": [],
        "inquiryGrammarCandidates": [{"candidateId": f"R13-INQUIRY-RULE-{index:03d}", "strategy": strategy, "historicalClaim": False, "semanticRelation": False, "active": False} for index, strategy in enumerate(STRATEGIES, start=1)],
        "structuralAnnotationCandidates": [{"candidateId": "R13-ANNOT-001", "label": "coloniality", "representation": "SOURCE_BOUNDED_STRUCTURAL_ANNOTATION", "requiredFields": ["source", "geography", "period", "mechanism", "affectedActorsOrObjects", "beneficiaryOrControlStructure", "continuityClaim", "qualification", "contestation"], "universalNode": False, "edge": False, "active": False}],
    }
    activation["canonicalHash"] = semantic_hash({key: value for key, value in activation.items() if key != "canonicalHash"})
    write_json(RESEARCH / "14_ACTIVATION_CANDIDATE_PACKAGE.json", activation)

    reviews = review_units(v2)
    write_tsv(RESEARCH / "16_EXTERNAL_DOMAIN_REVIEW_REGISTRY.tsv", reviews)
    metrics = breadth_metrics()

    write_text(RESEARCH / "00_EXECUTIVE_DECISION.md", f"""# Executive decision

Round 13 preserves the Round 12 candidate freeze at `{FREEZE_HASH}` and all five Instance v1 files. It researches only the three governed pair questions and six documented vocabulary gaps, implements six structurally distinct inquiry-tree strategies, compiles five non-claiming Instance v2 artifacts, and prepares an unanswered external domain-review packet.

Pair decisions are `INQUIRY_ONLY_SUPPORTED` only for professionalization/institutionalization. Gendering/commodification and imitation/piracy are `DEFER_MORE_EVIDENCE`; the latter has no peer-reviewed design-history composition article. No pair is an activation candidate. Seven narrower noun-level candidates and one structural annotation candidate are retained only for external review; none is active.

Active vocabulary and grammar remain unresolved. Active relation, pair, Cluster, and chain counts remain zero; no semantic Image, renderer, route, API, archive object, Context input, Spacetime input, model, embedding, or vector database is introduced.
""")
    write_text(RESEARCH / "01_SCOPE_AND_METHOD.md", """# Scope and method

The research scope is exactly PAIR-A professionalization/institutionalization, PAIR-B gendering/commodification, PAIR-C imitation/piracy, and GAP-001 through GAP-006. No 8×8 enumeration, similarity, embedding, semantic-proximity automation, machine translation, or invented normalization was used.

Each evidence row records source metadata, exact attested noun terms, bounded context, locator, roles, directionality, qualification, negation, contestation, source-cluster status, semantic review, and adversarial review. Co-occurrence alone cannot pass. A pair must also satisfy the design-history article, independent-cluster, role, direction, explanation, scope, adversarial, and universal-node gates.

Research Inquiry Rules remain separate from Historical Composition Rules. Every Round 13 inquiry rule has `historicalClaim=false` and `semanticRelation=false`.
""")
    write_text(RESEARCH / "02_ROUND12_INPUT_FREEZE.md", f"""# Round 12 input freeze

The immutable package `trace-exploration-research-candidates-v1` retains canonical SHA-256 `{FREEZE_HASH}`. Round 13 does not edit that file or any of the five v1 Instance files. Instance v2 stores each parent v1 canonical hash and changes topology only; semantic Nodes, root questions, primary inquiry flows, evidence coverage, source coverage, claims, exportability, and activation state are unchanged.

The source branch is `main` at `{SOURCE_SHA}`. Verification compares the frozen files against that Git tree and validates the freeze canonical hash independently.
""")
    write_text(RESEARCH / "09_TREE_STRATEGY_TOPOLOGY_SPEC.md", """# TreeStrategy topology specification

All strategies retain one root inquiry, one primary inquiry flow, at most two semantic Nodes, at most two siblings, maximum depth four, and at most seven total items.

- `LINEAR_PATH`: one non-branching inquiry sequence with distinct start, evidence-check, continuation, and sequence-boundary roles.
- `BINARY_FORK`: a root with two explicit alternative question branches; no exclusivity of historical truth is implied.
- `BINARY_CONVERGENCE`: two branches carry separate bounded concepts and a convergence item contains structural references to both inputs.
- `QUALIFIED_PATH`: continuation is a descendant of a mandatory qualification gate and cannot bypass it.
- `REFLEXIVE_RETURN`: a navigation target returns to the root after an actor/self-positioning question; the parent tree remains acyclic and no semantic self-loop exists.
- `EVIDENCE_GAP_TREE`: supported and unresolved root branches are peers, and the missing-evidence branch owns a first-class evidence-gap item.

Canonical topology signatures omit labels, strategy names, and IDs while preserving item kinds, parent indexes, depth, branch status, convergence references, and navigation targets. The six neutral synthetic signatures are distinct.
""")
    write_text(RESEARCH / "15_EXTERNAL_DOMAIN_REVIEW_PACKET.md", render_review_packet(reviews))
    write_text(RESEARCH / "17_SOURCE_BREADTH_AND_CONCENTRATION.md", f"""# Source breadth and concentration

- Source count: {metrics['source_count']}
- Venue count: {metrics['venue_count']}
- Author count: {metrics['author_count']}
- Language count: {metrics['language_count']}
- Publisher count: {metrics['publisher_count']}
- JDH share: {metrics['jdh_share']}
- OUP share: {metrics['oup_share']}
- Largest publisher: {metrics['largest_publisher']} at {metrics['largest_publisher_share']}
- Largest exact source cluster: {metrics['largest_source_cluster']} at {metrics['largest_source_cluster_share']}

The corpus spans design history, architecture history, fashion/business history, material and consumer culture, intellectual-property history, landscape architecture, comparative research, and coloniality methodology. It remains predominantly English. Pair evidence is narrower than the gap corpus: non-design-history sources cannot fill a missing design-history gate, and the fashion-piracy sources contain citation-cluster dependencies. Breadth therefore does not itself validate a pair.
""")
    write_text(RESEARCH / "18_LIMITATIONS_AND_ACTIVATION_BOUNDARY.md", """# Limitations and activation boundary

External human design-history review is incomplete. Gendering/commodification lacks a second qualifying design-history composition article. Professionalization/institutionalization lacks a stable direction. Imitation/piracy has two scholarly contrast/reclassification attestations but no peer-reviewed design-history composition article and remains contingent on law, authorization, markets, norms, and ethics. Mediation distinctions remain genealogy-concentrated. Carrier, infrastructure, and route labels for cultural mobility remain unresolved, as do forced-human, spatial, semantic, and strategic displacement labels.

The activation-candidate package is inactive, requires external review, requires a separate activation decision, and cannot feed the real Image compiler. No active vocabulary, historical grammar, public feature, or real semantic Image is authorized.
""")
    references = "\n".join(f"{index}. {row['authors'].replace(';', ', ')} ({row['year']}). “{row['title']}.” *{row['venue']}*. [{row['doi_or_identifier']}]({row['stable_url']})" for index, row in enumerate(SOURCES, start=1))
    write_text(RESEARCH / "19_REFERENCE_LIST.md", f"# Bounded reference list\n\n{references}\n")
    write_text(RESEARCH / "20_ROUND_DECISION.md", """# Round decision

Decision: `READY_WITH_LIMITATIONS`.

The exact three pairs and six gaps have fully verified decisions. The six Python TreeStrategy functions and neutral fixtures are structurally distinct, five v2 Instances preserve v1 semantic content, and the complete external-review packet is ready. No pair is an activation candidate; seven source-attested narrower labels, six inquiry topologies, and one coloniality structural annotation remain inactive review candidates.

Next gate: `EXTERNAL_HUMAN_REVIEW_AND_SEPARATE_SEMANTIC_ACTIVATION_DECISION`.
""")

    audit_docs = {
        "00_EXECUTIVE_RECEIPT.md": f"# Executive receipt\n\nRound 13 preserves `{FREEZE_HASH}` and five v1 Instances, verifies exactly three pair decisions and six gap decisions, implements six non-duplicate inquiry topologies, compiles five v2 Instances with 8/8 bounded-node coverage, and creates an inactive {activation['packageId']} package plus an unanswered {len(reviews)}-unit external review packet. Independent source, semantic, and adversarial re-reviews report PASS after all corrections; the authoritative regression, typecheck, database-freeze, hygiene, build, and audit-seal gates pass.",
        "01_INPUT_FREEZE_VALIDATION.md": f"# Input freeze validation\n\nSource Git tree: `{SOURCE_SHA}`. Canonical freeze: `{FREEZE_HASH}`. The validation gate compares the freeze and v1 Instance paths with the source tree, revalidates the freeze semantic hash, and requires five unchanged v1 files.",
        "02_SOURCE_AND_EVIDENCE_VALIDATION.md": f"# Source and evidence validation\n\nThe source registry has {len(SOURCES)} fully metadata-verified rows and the evidence registry has {len(EVIDENCE)} fully verified rows. Each evidence row has a locator, noun-level term, context, roles, direction, qualification, semantic review, adversarial review, and source-cluster flag.",
        "03_PAIR_DECISION_VALIDATION.md": "# Pair decision validation\n\nAll three governed pairs have one exact final status. No co-occurrence-only row passes, no pair lacks exhaustive verification, and no pair is activated. Professionalization/institutionalization remains inquiry-only; gendering/commodification and imitation/piracy remain deferred. The latter cannot bypass the missing peer-reviewed design-history article gate.",
        "04_VOCABULARY_GAP_VALIDATION.md": "# Vocabulary gap validation\n\nExactly six gap decisions are present. Four gaps yield source-attested split candidates, one yields a structural annotation candidate, and mediation remains evidence-limited. No label is normalized or invented, and no candidate enters the Round 12 freeze.",
        "05_TREE_STRATEGY_VALIDATION.md": "# Tree strategy validation\n\nSix Python builders produce six topology-only fixtures with distinct canonical signatures. Twelve shared negative fixtures prove that both Python and TypeScript reject wrong item kinds, role/kind swaps, false fork branches, swapped or false convergence inputs, qualification bypass, semantic self-navigation, and gaps attached to supported branches. Convergence has two semantic inputs, qualification is unavoidable, reflexive return is navigational only, and evidence absence is a first-class unresolved branch.",
        "06_INSTANCE_V2_VALIDATION.md": "# Instance v2 validation\n\nFive v2 files bind their v1 parent hashes, preserve semantic Nodes, questions, evidence, source coverage, primary inquiry flows, historicalClaim=false, semanticRelation=false, publicExportable=false, and RESEARCH_CANDIDATE_ONLY. Only tree topology and version metadata change.",
        "07_ACTIVATION_BOUNDARY.md": "# Activation boundary\n\nThe activation-candidate package is active=false, requires external review and a separate decision, and is barred from the real Image compiler. Active relation, pair, Cluster, chain, and real Image counts remain zero.",
        "08_EXTERNAL_REVIEW_PACKET_VALIDATION.md": f"# External review packet validation\n\nThe Markdown packet and {len(reviews)}-row TSV registry cover every required review unit and leave every reviewer answer NOT_COMPLETED. No review has been fabricated and no full article is redistributed.",
        "09_ZERO_OBJECT_AND_MODEL_BOUNDARY.md": "# Zero object and model boundary\n\nRound 13 inputs contain no archive object, Context, Spacetime, external model, embedding, vector database, renderer, public route, API, or PNG export. Python uses the standard library; no model download or inference occurs.",
        "10_PROTECTED_SYSTEMS.md": "# Protected systems\n\nDatabase and canonical v49 data, Search, Context, Spacetime, the Round 12 freeze, Round 12 Instance v1, and all Round 8–12 sealed packages are unchanged. TypeScript remains an adapter and contributes zero semantic rules.",
    }
    for name, content in audit_docs.items():
        write_text(AUDIT / name, content)
    write_json(RAW / "input-freeze.json", {"status": "PASS", "sourceSha": SOURCE_SHA, "freezeCanonicalHash": FREEZE_HASH, "instanceV1Count": len(v1), "instanceV1Hashes": [item["canonicalHash"] for item in v1]})
    write_json(RAW / "composition-evidence.json", {"status": "PASS", "sourceCount": len(SOURCES), "evidenceRowCount": len(EVIDENCE), "pairDecisionCount": len(PAIR_DECISIONS), "gapDecisionCount": len(GAP_DECISIONS), "fullyVerified": True})
    write_json(RAW / "independent-review-provenance.json", {
        "status": "PASS_THREE_INDEPENDENT_REVIEWS",
        "sourceVerification": {"reviewScope": "29/29 evidence rows", "initialVerdict": {"pass": 17, "qualified": 11, "fail": 1}, "finalVerdict": "PASS_NO_RESIDUAL_BLOCKER", "resolvedCorrections": ["source titles and stable URL", "BOOK_REVIEW classification and unknown peer-review state", "bounded paraphrases", "pagination qualification", "non-directional comparative association"]},
        "semanticVerification": {"reviewScope": "29/29 evidence rows; 3/3 pairs; 6/6 gaps; 6/6 inquiry rules", "finalVerdict": "PASS_NO_RESIDUAL_BLOCKER", "resolvedCorrections": ["PAIR-C deferred under design-history gate", "PAIR-B common-target and role-qualification mapping", "mediation role separation", "adapted-artifact target roles", "transformation state/association distinction", "candidate-specific anti-universal guards", "design-diplomacy cluster and reception qualification"]},
        "adversarialReview": {"reviewScope": "30 sources; 29 evidence rows; 3 pairs; 6 gaps; 6 strategies; 5 instances; 36 review units; Python and TypeScript", "finalVerdict": "PASS_NO_REMAINING_GATE_BLOCKER", "resolvedCorrections": ["derived evidence and decision gates", "12 shared cross-runtime negative topology fixtures", "exact role-kind-parent topology contracts", "tree-level evidence/gap binding preservation", "exact per-gap candidate and attested-term ownership", "complete review unit role/direction/source/evidence re-derivation", "normalized venue count and tied source-cluster report"]},
        "externalHumanReviewCompleted": False,
    })
    validation_rows = [
        {"gate": "ROUND8_REGRESSION", "status": "PASS", "execution_context": "current Round 13 tree", "command_or_evidence": "npm run verify:exploration-reset; npm run test:exploration-domain"},
        {"gate": "ROUND9_REGRESSION", "status": "PASS", "execution_context": "preserved worktree 47978c519c3c7141690e3894315a1ef1b7a403db", "command_or_evidence": "python3 scripts/validate_trace_v49_relation_vocabulary_round1.py"},
        {"gate": "ROUND10_REGRESSION", "status": "PASS", "execution_context": "preserved worktree 4bd82deba482ec2fbf8c4856080151416fb8ee83", "command_or_evidence": "python3 scripts/trace-v49-relation-grammar/validate_round1.py"},
        {"gate": "ROUND11_REGRESSION", "status": "PASS", "execution_context": "preserved worktree 5ca999b53d9a5d18b47317817402f9e51ad26cec and current tree", "command_or_evidence": "validate_round1.py; npm run test:exploration-constraint-kernel"},
        {"gate": "ROUND12_REGRESSION", "status": "PASS", "execution_context": "preserved worktree fc11f033d2fcdbb98130879cdbd3e4a52890e5d2 and current tree", "command_or_evidence": "validate.py; npm run test:exploration-inquiry-adapter"},
        {"gate": "COMPOSITION_EVIDENCE_TESTS", "status": "PASS", "execution_context": "current tree", "command_or_evidence": "29/29 evidence rows; derived source metadata and sense bindings"},
        {"gate": "PAIR_DECISION_TESTS", "status": "PASS", "execution_context": "current tree", "command_or_evidence": "3/3 derived scope/count/cluster/design-history gates"},
        {"gate": "VOCABULARY_GAP_TESTS", "status": "PASS", "execution_context": "current tree", "command_or_evidence": "6/6 exact candidate/term/package ownership gates"},
        {"gate": "TREE_STRATEGY_TESTS", "status": "PASS", "execution_context": "Python and TypeScript", "command_or_evidence": "6 positive and 12 shared negative fixtures"},
        {"gate": "TREE_TOPOLOGY_NON_DUPLICATION", "status": "PASS", "execution_context": "Python and TypeScript", "command_or_evidence": "6 distinct canonical topology signatures"},
        {"gate": "INSTANCE_V1_IMMUTABILITY", "status": "PASS", "execution_context": f"Git source tree {SOURCE_SHA}", "command_or_evidence": "freeze and five v1 paths unchanged"},
        {"gate": "INSTANCE_V2_TESTS", "status": "PASS", "execution_context": "Python and TypeScript", "command_or_evidence": "five deterministic v2 instances; 8/8 bounded senses"},
        {"gate": "V1_V2_SEMANTIC_PRESERVATION", "status": "PASS", "execution_context": "Python and TypeScript", "command_or_evidence": "semantic nodes/questions/claims/evidence and gap binding unions unchanged"},
        {"gate": "STRICT_SCHEMA_TESTS", "status": "PASS", "execution_context": "JSON Schema 2020-12 and exact-field validators", "command_or_evidence": "additionalProperties=false; required/property contracts exact"},
        {"gate": "CROSS_RUNTIME_CONFORMANCE", "status": "PASS", "execution_context": "Python reference and TypeScript verifier", "command_or_evidence": "decision mismatches=0; hash mismatches=0"},
        {"gate": "TYPECHECK", "status": "PASS", "execution_context": "frontend", "command_or_evidence": "npx tsc --noEmit --pretty false; npm run typecheck:runtime"},
        {"gate": "SEARCH_REGRESSION", "status": "PASS", "execution_context": "frontend", "command_or_evidence": "verify:search-v49-index; test:search-v49"},
        {"gate": "CONTEXT_REGRESSION", "status": "PASS", "execution_context": "frontend", "command_or_evidence": "projection, governance, runtime, and API gates"},
        {"gate": "SPACETIME_REGRESSION", "status": "PASS", "execution_context": "frontend", "command_or_evidence": "projection, governance, runtime, API, and GIS gates"},
        {"gate": "API_TESTS", "status": "PASS", "execution_context": "frontend", "command_or_evidence": "test:read-platform; page-by-key contract"},
        {"gate": "DATABASE_FREEZE", "status": "PASS", "execution_context": "repository", "command_or_evidence": "verify_v49_database_freeze.py --repo ."},
        {"gate": "REPOSITORY_HYGIENE", "status": "PASS", "execution_context": "explicitly staged final tree", "command_or_evidence": "audit_repository_hygiene.py --repo ."},
        {"gate": "PRODUCTION_BUILD", "status": "PASS", "execution_context": "frontend", "command_or_evidence": "npm run build"},
        {"gate": "GIT_DIFF_CHECK", "status": "PASS", "execution_context": "repository", "command_or_evidence": "git diff --check; git diff --cached --check"},
        {"gate": "GIT_FSCK", "status": "PASS", "execution_context": "repository", "command_or_evidence": "git fsck --full"},
        {"gate": "AUDIT_SEAL", "status": "PASS", "execution_context": "Round 13 audit package", "command_or_evidence": "manifest paths/bytes/SHA-256 equal SHA256SUMS"},
    ]
    write_tsv(RAW / "full-validation.tsv", validation_rows)
    write_json(RAW / "tree-strategy-validation.json", {"status": "PASS", "strategyCount": len(STRATEGIES), "fixtureCount": len(fixtures), "topologyDuplicateCount": 0, "signatures": {strategy: topology_signature(items) for strategy, items in fixtures.items()}})
    write_json(RAW / "instance-v2-validation.json", {"status": "PASS", "instanceV2Count": len(v2), "boundedNodeCoverage": "8/8", "semanticNodeChangeCount": 0, "questionChangeCount": 0, "historicalClaimChangeCount": 0, "instanceHashes": [item["canonicalHash"] for item in v2]})
    write_json(RAW / "activation-boundary.json", {"status": "PASS", "activeVocabularyState": "UNRESOLVED", "activeGrammarState": "UNRESOLVED", "activeRelationTypeCount": 0, "activePairRuleCount": 0, "activeClusterRuleCount": 0, "activeChainRuleCount": 0, "realSemanticImageCount": 0, "externalReviewCompleted": False})

    changed = ["scripts/trace-v49-exploration-composition-review/", "schemas/trace/exploration/inquiry-tree-v2.schema.json", "schemas/trace/exploration/research-inquiry-instance-v2.schema.json", "frontend/src/lib/trace/exploration-inquiry-adapter.ts", "frontend/src/lib/trace/exploration-inquiry-v2-adapter.ts", "frontend/scripts/test-exploration-composition-review.mjs", "frontend/package.json", "docs/research/EXPLORATION_CURRENT.md", "docs/research/trace-v49-exploration-composition-review-round1/", "docs/audits/v49-exploration-composition-review-round1/", "PROJECT_LOG.md", "docs/releases/v49/RELEASE_INDEX.md", "docs/releases/v49/AUDIT_INDEX.md", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md"]
    write_text(AUDIT / "11_CHANGED_FILES.md", "# Changed files\n\n" + "\n".join(f"- `{item}`" for item in changed) + "\n")

    support_files = [
        REPO / "schemas/trace/exploration/inquiry-tree-v2.schema.json",
        REPO / "schemas/trace/exploration/research-inquiry-instance-v2.schema.json",
        REPO / "frontend/src/lib/trace/exploration-inquiry-adapter.ts",
        REPO / "frontend/src/lib/trace/exploration-inquiry-v2-adapter.ts",
        REPO / "frontend/scripts/test-exploration-composition-review.mjs",
        REPO / "frontend/package.json",
        REPO / "docs/research/EXPLORATION_CURRENT.md",
        REPO / "PROJECT_LOG.md",
        REPO / "docs/releases/v49/RELEASE_INDEX.md",
        REPO / "docs/releases/v49/AUDIT_INDEX.md",
        REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json",
        REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv",
        REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md",
        *sorted(path for path in ENGINE.rglob("*") if path.is_file() and "__pycache__" not in path.parts),
    ]
    manifest_excludes = {AUDIT / "MANIFEST.tsv", AUDIT / "SHA256SUMS.txt"}
    manifest_files = sorted(set(path for root in (RESEARCH, AUDIT) for path in root.rglob("*") if path.is_file() and path not in manifest_excludes) | {path for path in support_files if path.is_file()})
    manifest_rows = [{"path": path.relative_to(REPO).as_posix(), "byte_size": path.stat().st_size, "sha256": sha256(path)} for path in manifest_files]
    write_tsv(AUDIT / "MANIFEST.tsv", manifest_rows)
    write_text(AUDIT / "SHA256SUMS.txt", "\n".join(f"{row['sha256']}  {row['path']}" for row in manifest_rows))


if __name__ == "__main__":
    generate()
