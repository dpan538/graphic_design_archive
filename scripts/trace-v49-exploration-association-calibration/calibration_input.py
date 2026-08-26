"""Bounded, researcher-coded Round 14 calibration corpus and provenance bindings."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from model import CalibrationCase


ARCHIVE_SOURCES: dict[str, dict[str, str]] = {
    "R14-ARC-001": {
        "creator": "Bauhaus-Archiv / Museum für Gestaltung",
        "year": "1919; current institutional description",
        "title": "Manifest und Programm des Staatlichen Bauhauses / Das Bauhaus",
        "source_kind": "INSTITUTIONAL_ARCHIVE_PRIMARY_SOURCE_CONTEXT",
        "stable_url": "https://www.bauhaus.de/de/das_bauhaus/",
        "doi": "",
        "source_family": "BAUHAUS_ARCHIVE",
        "domain_alignment": "DESIGN_HISTORY_ARCHIVE",
        "locator": "Program section and 1919 chronology",
        "association_context": "The archive presents the founding manifesto and its educational vision joining art, craft, workshops, and a new school program.",
    },
    "R14-ARC-002": {
        "creator": "The Museum of Modern Art",
        "year": "1991",
        "title": "The Graphic Designs of Herbert Matter",
        "source_kind": "INSTITUTIONAL_EXHIBITION_ARCHIVE",
        "stable_url": "https://www.moma.org/calendar/exhibitions/340",
        "doi": "",
        "source_family": "MOMA_EXHIBITION_ARCHIVE",
        "domain_alignment": "GRAPHIC_DESIGN_MUSEUM_ARCHIVE",
        "locator": "Exhibition description",
        "association_context": "The institutional exhibition record explicitly describes Matter's synthesis of photography and typography and his use of photomontage.",
    },
    "R14-ARC-003": {
        "creator": "Ken Garland",
        "year": "2012",
        "title": "Last things last",
        "source_kind": "PRIMARY_DESIGNER_TESTIMONY",
        "stable_url": "https://eyemagazine.com/feature/article/last-things-last",
        "doi": "",
        "source_family": "EYE_PRIMARY_DESIGNER_ACCOUNT",
        "domain_alignment": "GRAPHIC_DESIGN_PRIMARY_SOURCE",
        "locator": "Author's retrospective account of First Things First",
        "association_context": "Garland's own account qualifies the manifesto's critique of commercial design and discusses clients, commerce, and visual-communication practice.",
    },
    "R14-ARC-004": {
        "creator": "Ken Garland",
        "year": "1994",
        "title": "First things last",
        "source_kind": "PRIMARY_DESIGNER_LETTER",
        "stable_url": "https://eyemagazine.com/opinion/article/letter-first-things-last",
        "doi": "",
        "source_family": "EYE_PRIMARY_DESIGNER_ACCOUNT",
        "domain_alignment": "GRAPHIC_DESIGN_PRIMARY_SOURCE",
        "locator": "Letter to the editor",
        "association_context": "Garland clarifies that the 1964 manifesto concerned spending priorities and the social context and purposes of graphic-design work.",
    },
}


def _row(**values: Any) -> dict[str, Any]:
    return values


CASE_SPECS: list[dict[str, Any]] = [
    _row(id="001", a="professionalization", b="institutionalization", stratum="CLEAR_POSITIVE", hard=False, period="1870–2021", family="interior-design history;graphic-design professions", domain="professional history", primary="INSTITUTIONAL_PROFESSIONAL", secondary=None, historical="Western interior design 1870–1970 and university visual-identity practice", context="Named education, association, accreditation, occupational-trust, and university mechanisms", dims=(2,2,1,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-001","COMP-EVID-002"), expected=True, qualification="Association is non-directional and scope-bounded; no universal professional sequence is claimed.", reason="Two independent domain-aligned studies explicitly discuss the concepts together through named institutions."),
    _row(id="002", a="production", b="mediation", stratum="CLEAR_POSITIVE", hard=False, period="modern and digital design history", family="production-consumption mediation", domain="design historiography", primary="PRACTICE_PRODUCTION", secondary="CULTURAL_DISCURSIVE", historical="Design-history accounts of production-consumption mediation", context="Designed channels and devices between production and consumption", dims=(2,2,1,2,1,2,2), co=False, qual=False, evidence=("COMP-EVID-008","COMP-EVID-009","COMP-EVID-010"), expected=True, qualification="Mediation is contextual, not a causal arrow from production.", reason="Independent design-history sources explicitly place mediating channels or devices in production contexts."),
    _row(id="003", a="mediation", b="consumption", stratum="CLEAR_POSITIVE", hard=False, period="modern and digital design history", family="production-consumption mediation", domain="design historiography", primary="PRACTICE_PRODUCTION", secondary="ECONOMIC_COMMERCIAL", historical="Design-history accounts of production-consumption mediation", context="Meaning inscription and data relations involving consumption", dims=(2,2,1,2,1,2,2), co=False, qual=False, evidence=("COMP-EVID-008","COMP-EVID-009","COMP-EVID-011"), expected=True, qualification="The association does not make consumers passive endpoints.", reason="Independent sources explicitly locate designed mediation within consumption and reception."),
    _row(id="004", a="production", b="consumption", stratum="CLEAR_POSITIVE", hard=False, period="modern and digital design history", family="production-consumption mediation", domain="design historiography", primary="PRACTICE_PRODUCTION", secondary="ECONOMIC_COMMERCIAL", historical="Production-consumption mediation in design history", context="The PCM model and digital extension explicitly retain both poles", dims=(2,2,1,2,1,2,2), co=False, qual=False, evidence=("COMP-EVID-008","COMP-EVID-010","COMP-EVID-011"), expected=True, qualification="Spatial association does not assert a single linear market mechanism.", reason="The sources explicitly frame designed channels and devices between production and consumption."),
    _row(id="005", a="exhibition", b="design diplomacy", stratum="CLEAR_POSITIVE", hard=False, period="1930–1979", family="international exhibitions", domain="design diplomacy", primary="CIRCULATION_EXCHANGE", secondary="CULTURAL_DISCURSIVE", historical="Swedish, Polish, Soviet, and US-linked exposition histories", context="Designed exhibition media used in international negotiation and representation", dims=(2,2,2,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-024","COMP-EVID-025","COMP-EVID-026"), expected=True, qualification="Diplomatic intention does not guarantee audience reception or political effect.", reason="Three independent histories directly analyze exhibitions as sites of design diplomacy."),
    _row(id="006", a="design diplomacy", b="propaganda", stratum="CLEAR_POSITIVE", hard=False, period="1930–1979", family="international exhibitions", domain="design diplomacy", primary="CULTURAL_DISCURSIVE", secondary="CIRCULATION_EXCHANGE", historical="State-sponsored international display", context="Persuasion, propaganda, negotiation, and goodwill in exposition practice", dims=(2,2,2,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-024","COMP-EVID-025","COMP-EVID-026"), expected=True, qualification="The sources distinguish diplomacy from propaganda rather than equating them.", reason="The exhibition studies explicitly compare or combine diplomatic and propagandistic functions."),
    _row(id="007", a="propaganda", b="trade", stratum="CLEAR_POSITIVE", hard=False, period="1930s", family="Swedish exposition history", domain="exhibition history", primary="ECONOMIC_COMMERCIAL", secondary="CULTURAL_DISCURSIVE", historical="Swedish national representation at an international exposition", context="Designed display combining propaganda, goodwill, and trade", dims=(2,1,0,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-026",), expected=True, qualification="One bounded exposition case; no general identity between propaganda and trade.", reason="One domain-aligned historical study explicitly treats propaganda and trade within the same designed display program."),
    _row(id="008", a="exhibition", b="propaganda", stratum="CLEAR_POSITIVE", hard=False, period="1930–1979", family="international exhibitions", domain="exhibition history", primary="CULTURAL_DISCURSIVE", secondary="CIRCULATION_EXCHANGE", historical="State-sponsored international exhibitions", context="Designed exposition used for persuasion, national representation, and propaganda", dims=(2,2,1,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-025","COMP-EVID-026"), expected=True, qualification="The assessment remains case-bounded and does not classify every exhibition as propaganda.", reason="Independent exposition histories directly discuss propagandistic functions of designed exhibitions."),
    _row(id="009", a="design diplomacy", b="trade", stratum="CLEAR_POSITIVE", hard=False, period="1930s", family="Swedish exposition history", domain="design diplomacy", primary="ECONOMIC_COMMERCIAL", secondary="CIRCULATION_EXCHANGE", historical="Swedish international exposition practice", context="Diplomatic representation, goodwill, and trade through designed display", dims=(2,1,0,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-026",), expected=True, qualification="Single-case source support; diplomatic outcome is not asserted.", reason="A design-history exposition case directly joins diplomatic representation and trade."),
    _row(id="010", a="material displacement", b="supply chain", stratum="CLEAR_POSITIVE", hard=False, period="modern design and landscape history", family="material histories", domain="material design history", primary="MATERIAL_TECHNOLOGICAL", secondary="CIRCULATION_EXCHANGE", historical="Movement of designed materials between production and receiving sites", context="Material chains with labor and ecological consequences", dims=(2,2,1,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-020","COMP-EVID-021"), expected=True, qualification="The association does not reduce all material movement to one supply-chain model.", reason="Two design-history sources explicitly treat material movement through sites and chains."),
    _row(id="011", a="supply chain", b="production site", stratum="BORDERLINE", hard=False, period="modern landscape-material history", family="material chains", domain="material design history", primary="MATERIAL_TECHNOLOGICAL", secondary="PRACTICE_PRODUCTION", historical="Landscape material chains", context="Named production sites, destinations, labor, and ecological effects", dims=(2,1,0,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-021",), expected=True, qualification="One bounded study and source family; confidence is moderate.", reason="The study explicitly describes production sites as part of the material chain."),
    _row(id="012", a="material displacement", b="production site", stratum="BORDERLINE", hard=False, period="modern landscape-material history", family="material chains", domain="material design history", primary="MATERIAL_TECHNOLOGICAL", secondary="PRACTICE_PRODUCTION", historical="Movement of landscape materials", context="Production site and designed destination linked by a material chain", dims=(1,1,0,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-021",), expected=True, qualification="Association is inferred within the source's explicit chain, not elevated to a universal relation.", reason="The bounded source-level account supplies a contextual bridge between displacement and production site."),
    _row(id="013", a="cultural negotiation", b="adaptation", stratum="BORDERLINE", hard=False, period="colonial and postcolonial architectural contexts", family="contact zones;Javanese adaptation", domain="architectural design history", primary="CULTURAL_DISCURSIVE", secondary="CIRCULATION_EXCHANGE", historical="Architectural contact zones and Javanese design", context="Selective borrowing, adaptation, rejection, and symbolic resistance", dims=(2,2,1,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-014","COMP-EVID-015"), expected=True, qualification="Adaptation is situated agency, not passive transfer.", reason="Two studies explicitly place adaptation within negotiated contact and resistance."),
    _row(id="014", a="adaptation", b="rejection", stratum="BORDERLINE", hard=False, period="colonial and postcolonial architectural contexts", family="contact zones;Javanese adaptation", domain="architectural design history", primary="CULTURAL_DISCURSIVE", secondary=None, historical="Architectural contact zones", context="Selective borrowing, adaptation, or rejection", dims=(2,1,0,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-014",), expected=True, qualification="Alternatives within one contact-zone model, not successive stages.", reason="A domain-aligned study explicitly presents adaptation and rejection as situated responses."),
    _row(id="015", a="cultural negotiation", b="rejection", stratum="BORDERLINE", hard=False, period="colonial and postcolonial architectural contexts", family="contact zones", domain="architectural design history", primary="CULTURAL_DISCURSIVE", secondary=None, historical="Architectural contact zones", context="Negotiation through borrowing, adaptation, or rejection", dims=(1,1,0,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-014",), expected=True, qualification="One conceptual source; no claim that rejection always constitutes negotiation.", reason="The source explicitly situates rejection within a negotiated contact-zone repertoire."),
    _row(id="016", a="gendering", b="commodification", stratum="BORDERLINE", hard=False, period="1867; qualified contemporary extension", family="Brazilian exposition;second-hand markets", domain="design and consumption history", primary="SOCIAL_IDENTITY", secondary="ECONOMIC_COMMERCIAL", historical="Paris 1867 Brazilian display with a qualified consumption-history comparison", context="Parallel classification of tropical nature/raw material and gendered consumer/trader positions", dims=(2,2,1,2,2,1,2), co=False, qual=False, evidence=("COMP-EVID-003","COMP-EVID-004"), expected=True, qualification="The generic association is case-bounded; it does not assert that either process causes the other.", reason="A design-history article explicitly treats both processes in one exposition; the second source broadens but does not universalize the association."),
    _row(id="017", a="imitation", b="piracy", stratum="BORDERLINE", hard=False, period="twentieth- and twenty-first-century fashion/design regimes", family="fashion business;IP law;consumer research", domain="design and legal history", primary="PRACTICE_PRODUCTION", secondary="ECONOMIC_COMMERCIAL", historical="Fashion and product-design copying regimes", context="Source-bounded classifications distinguish accommodated imitation from piracy", dims=(2,2,2,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-005","COMP-EVID-006","COMP-EVID-007"), expected=True, qualification="Authorization and rights regimes condition the classification; imitation is not automatically piracy.", reason="Three independent sources explicitly analyze the concepts together while preserving their distinction."),
    _row(id="018", a="photography", b="typography", stratum="BORDERLINE", hard=False, period="1930s modern graphic design", family="MoMA exhibition archive", domain="graphic design museum history", primary="MATERIAL_TECHNOLOGICAL", secondary="PRACTICE_PRODUCTION", historical="Herbert Matter's modern graphic-design practice", context="Institutional record of photographic/typographic synthesis", dims=(2,1,0,2,2,1,1), co=False, qual=False, evidence=("R14-ARC-002",), expected=True, qualification="Supported by archive/source evidence. Independent scholarly validation pending.", reason="The museum exhibition record explicitly describes a synthesis of photography and typography."),
    _row(id="019", a="advertising", b="consumer culture", stratum="BORDERLINE", hard=False, period="1964 and retrospective accounts", family="Eye primary designer account", domain="graphic design primary sources", primary="ECONOMIC_COMMERCIAL", secondary="SOCIAL_IDENTITY", historical="Ken Garland's First Things First intervention", context="Commercial priorities, consumer selling, and social-purpose alternatives", dims=(2,1,0,2,2,1,1), co=False, qual=False, evidence=("R14-ARC-003","R14-ARC-004"), expected=True, qualification="Supported by archive/source evidence. Independent scholarly validation pending.", reason="The designer's own published accounts explicitly connect advertising priorities with consumer selling and social context."),
    _row(id="020", a="craft", b="education", stratum="BORDERLINE", hard=False, period="1919 Bauhaus foundation", family="Bauhaus archive", domain="design education primary source", primary="INSTITUTIONAL_PROFESSIONAL", secondary="PRACTICE_PRODUCTION", historical="Staatliches Bauhaus founding program", context="Workshop education and the joining of art and craft", dims=(2,1,0,2,2,1,1), co=False, qual=False, evidence=("R14-ARC-001",), expected=True, qualification="Supported by archive/source evidence. Independent scholarly validation pending.", reason="The institutional archive presents the primary program's explicit educational and workshop context."),
    _row(id="021", a="design education", b="institutionalization", stratum="BORDERLINE", hard=False, period="1870–2021", family="interior-design history;graphic-design professions", domain="professional history", primary="INSTITUTIONAL_PROFESSIONAL", secondary=None, historical="Formal design education and university visual-identity practice", context="Education, accreditation, universities, associations, and professional logic", dims=(1,2,1,2,2,2,2), co=False, qual=False, evidence=("COMP-EVID-001","COMP-EVID-002"), expected=True, qualification="The association is institutional and contextual, not a universal path to professional status.", reason="Independent studies repeatedly place formal education and universities within institutionalization contexts."),
    _row(id="022", a="cultural transfer", b="cultural negotiation", stratum="BORDERLINE", hard=False, period="colonial and Cold War design circulation", family="transfer studies;contact zones", domain="design and architectural history", primary="CIRCULATION_EXCHANGE", secondary="CULTURAL_DISCURSIVE", historical="Print, exhibition, and architectural contact settings", context="Receiving agency and negotiated borrowing are compatible but not directly joined across the bounded sources", dims=(1,2,1,2,1,1,2), co=False, qual=True, evidence=("COMP-EVID-012","COMP-EVID-013","COMP-EVID-014"), expected=False, qualification="The bridge is cross-source and conceptually plausible, but direct historical contextual support remains incomplete.", reason="Evidence exists for both concepts and receiving agency, but the V1 proximity gate excludes this qualified bridge."),
    _row(id="023", a="cultural transformation", b="piracy", stratum="NEGATIVE", hard=True, period="mixed", family="architectural transformation;fashion piracy", domain="cross-domain control", primary="CULTURAL_DISCURSIVE", secondary="ECONOMIC_COMMERCIAL", historical="No shared bounded historical case", context="Near-neighbour language about change does not establish association", dims=(0,1,1,1,0,0,0), co=False, qual=False, evidence=("COMP-EVID-018","COMP-EVID-005"), expected=False, qualification="Separate source families attest each concept only.", reason="No source-level contextual bridge supports meaningful proximity."),
    _row(id="024", a="design education", b="commodification", stratum="NEGATIVE", hard=True, period="mixed", family="professionalization;exposition commodification", domain="cross-domain control", primary="INSTITUTIONAL_PROFESSIONAL", secondary="ECONOMIC_COMMERCIAL", historical="No shared bounded historical case", context="Broad design-history membership only", dims=(0,1,1,2,0,0,0), co=True, qual=False, evidence=("COMP-EVID-001","COMP-EVID-003"), expected=False, qualification="Corpus co-membership is not contextual evidence.", reason="The sources support separate histories, not this association."),
    _row(id="025", a="gendering", b="mobile object", stratum="NEGATIVE", hard=True, period="mixed", family="exposition gendering;object mobility", domain="cross-domain control", primary="SOCIAL_IDENTITY", secondary="CIRCULATION_EXCHANGE", historical="No shared bounded historical case", context="Possible visual-culture overlap without direct evidence", dims=(0,1,1,2,0,0,0), co=False, qual=False, evidence=("COMP-EVID-003","COMP-EVID-022"), expected=False, qualification="A future case-specific study could change the result; none is present here.", reason="The evidence rows attest different concepts in unrelated cases."),
    _row(id="026", a="professionalization", b="material displacement", stratum="NEGATIVE", hard=True, period="mixed", family="professional history;material history", domain="cross-domain control", primary="INSTITUTIONAL_PROFESSIONAL", secondary="MATERIAL_TECHNOLOGICAL", historical="No shared bounded historical case", context="Both are design-history topics but not a supported local association", dims=(0,1,1,2,0,0,0), co=True, qual=False, evidence=("COMP-EVID-001","COMP-EVID-020"), expected=False, qualification="Domain alignment alone cannot activate proximity.", reason="This hard negative tests broad disciplinary similarity without contextual support."),
    _row(id="027", a="photography", b="institutionalization", stratum="NEGATIVE", hard=True, period="mixed", family="MoMA exhibition;professional history", domain="cross-domain control", primary="INSTITUTIONAL_PROFESSIONAL", secondary="MATERIAL_TECHNOLOGICAL", historical="No shared bounded historical case", context="Modern design prominence without a source-level bridge", dims=(0,1,1,2,0,0,0), co=False, qual=False, evidence=("R14-ARC-002","COMP-EVID-001"), expected=False, qualification="Prominence in design history is not association evidence.", reason="Separate records do not justify close placement."),
    _row(id="028", a="craft", b="design diplomacy", stratum="NEGATIVE", hard=True, period="mixed", family="Bauhaus archive;exhibition diplomacy", domain="cross-domain control", primary="CIRCULATION_EXCHANGE", secondary="PRACTICE_PRODUCTION", historical="No shared bounded historical case", context="Institutional design contexts remain unrelated at the assessed scope", dims=(0,1,1,2,0,0,0), co=False, qual=False, evidence=("R14-ARC-001","COMP-EVID-024"), expected=False, qualification="A specific diplomatic craft exhibition could support a future assessment; none is bound here.", reason="The evidence does not contextualize the concepts together."),
    _row(id="029", a="Bauhaus", b="desktop publishing", stratum="NEGATIVE", hard=False, period="1919 versus late twentieth century", family="Bauhaus archive;digital design history", domain="obvious temporal control", primary="TEMPORAL_HISTORICAL_CONTEXT", secondary="MATERIAL_TECHNOLOGICAL", historical="Non-overlapping source cases", context="Famous design topics with no bounded bridge in the evidence", dims=(0,1,1,2,1,0,0), co=True, qual=False, evidence=("R14-ARC-001","COMP-EVID-009"), expected=False, qualification="Chronological difference alone is not proof of disassociation, but the supplied evidence cannot justify proximity.", reason="This obvious negative verifies that corpus fame does not substitute for evidence."),
    _row(id="030", a="Arts and Crafts", b="digital interface", stratum="NEGATIVE", hard=False, period="nineteenth century versus digital era", family="design education archive;digital design history", domain="obvious temporal control", primary="TEMPORAL_HISTORICAL_CONTEXT", secondary="MATERIAL_TECHNOLOGICAL", historical="No shared bounded case", context="Chronological bookends without documented circulation or reception", dims=(0,1,1,1,1,0,0), co=True, qual=False, evidence=("R14-ARC-001","COMP-EVID-011"), expected=False, qualification="A documented reception history could change the assessment.", reason="Temporal contrast and broad design classification do not establish association."),
    _row(id="031", a="Swiss typography", b="Brazilian exposition", stratum="NEGATIVE", hard=False, period="1930s modernism versus 1867 exposition", family="MoMA exhibition;Brazilian exposition", domain="obvious case control", primary="TEMPORAL_HISTORICAL_CONTEXT", secondary="CULTURAL_DISCURSIVE", historical="Distinct cases and geographies", context="No source-level discussion of reception or exchange", dims=(0,1,1,2,1,0,0), co=False, qual=False, evidence=("R14-ARC-002","COMP-EVID-003"), expected=False, qualification="Shared graphic-design historiography is insufficient.", reason="The evidence provides no contextual bridge."),
    _row(id="032", a="photomontage", b="professionalization", stratum="NEGATIVE", hard=True, period="mixed", family="MoMA exhibition;professional history", domain="hard near-neighbour control", primary="PRACTICE_PRODUCTION", secondary="INSTITUTIONAL_PROFESSIONAL", historical="No shared bounded historical case", context="A practice and a professional process that may coexist but are not linked here", dims=(0,1,1,2,0,0,0), co=False, qual=False, evidence=("R14-ARC-002","COMP-EVID-002"), expected=False, qualification="Plausible coexistence is not evidence-grounded association.", reason="The sources independently attest practice and professionalization without a shared context."),
    _row(id="033", a="gendering", b="design education", stratum="NEGATIVE", hard=True, period="mixed", family="Brazilian exposition;professional education", domain="hard local-coherence control", primary="SOCIAL_IDENTITY", secondary="INSTITUTIONAL_PROFESSIONAL", historical="No shared bounded historical case in the supplied evidence", context="Both topics may intersect in future research, but these sources do not join them", dims=(0,1,1,2,0,0,0), co=False, qual=False, evidence=("COMP-EVID-003","COMP-EVID-001"), expected=False, qualification="Potential general relevance is not case-level support.", reason="Separate evidence units cannot justify skip-one proximity."),
    _row(id="034", a="commodification", b="institutionalization", stratum="NEGATIVE", hard=True, period="mixed", family="exposition commodification;professional institutions", domain="hard local-coherence control", primary="ECONOMIC_COMMERCIAL", secondary="INSTITUTIONAL_PROFESSIONAL", historical="No shared bounded historical case in the supplied evidence", context="Broad institutional/economic overlap only", dims=(0,1,1,2,0,0,0), co=True, qual=False, evidence=("COMP-EVID-003","COMP-EVID-002"), expected=False, qualification="Co-membership in design-history scholarship is insufficient.", reason="No contextual evidence binds the concepts in the assessed scope."),
    _row(id="035", a="imitation", b="cultural transformation", stratum="NEGATIVE", hard=True, period="mixed", family="fashion imitation;architectural transformation", domain="hard local-coherence control", primary="CULTURAL_DISCURSIVE", secondary="PRACTICE_PRODUCTION", historical="No shared bounded historical case in the supplied evidence", context="Generic change language without shared actors, place, or source discussion", dims=(0,1,1,1,0,0,0), co=False, qual=False, evidence=("COMP-EVID-005","COMP-EVID-018"), expected=False, qualification="Separate studies attest the terms only.", reason="The skip-one control has no evidence-grounded contextual bridge."),
]


def _load_round13(repo: Path) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    root = repo / "docs/research/trace-v49-exploration-composition-review-round1"
    with (root / "03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv").open(encoding="utf-8", newline="") as handle:
        sources = {row["source_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    with (root / "04_COMPOSITION_EVIDENCE_REGISTRY.tsv").open(encoding="utf-8", newline="") as handle:
        evidence = {row["evidence_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    return sources, evidence


def build_inputs(repo: Path) -> tuple[list[CalibrationCase], list[dict[str, Any]]]:
    sources, round13_evidence = _load_round13(repo)
    cases: list[CalibrationCase] = []
    provenance: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        assessment_id = f"R14-ASSOC-{spec['id']}"
        bound_ids: list[str] = []
        support_role = "ASSOCIATION_SUPPORT" if spec["expected"] or spec["qual"] else "CONCEPT_ONLY_NOT_ASSOCIATION"
        for index, reference in enumerate(spec["evidence"], start=1):
            evidence_id = f"R14-EVID-{spec['id']}-{index:02d}"
            bound_ids.append(evidence_id)
            if reference.startswith("COMP-EVID-"):
                original = round13_evidence[reference]
                source = sources[original["source_id"]]
                provenance.append({
                    "evidence_id": evidence_id,
                    "assessment_id": assessment_id,
                    "evidence_channel": "EXTERNAL_SCHOLARSHIP",
                    "source_id": source["source_id"],
                    "source_kind": source["source_type"],
                    "creator": source["authors"],
                    "year": source["year"],
                    "title": source["title"],
                    "locator": original["locator"],
                    "stable_url": source["stable_url"],
                    "doi": source["doi_or_identifier"] if source["doi_or_identifier"].startswith("10.") else "",
                    "source_family": source["source_cluster"],
                    "domain_alignment": "DESIGN_HISTORY" if source["design_history_usage"] == "true" else "ADJACENT_DISCIPLINE",
                    "support_role": support_role,
                    "association_context": original["bounded_context"],
                    "source_metadata_verified": source["source_metadata_verified"],
                    "evidence_verified": original["evidence_verified"],
                    "upstream_evidence_ref": reference,
                })
            else:
                source = ARCHIVE_SOURCES[reference]
                provenance.append({
                    "evidence_id": evidence_id,
                    "assessment_id": assessment_id,
                    "evidence_channel": "ARCHIVE_SOURCE",
                    "source_id": reference,
                    "source_kind": source["source_kind"],
                    "creator": source["creator"],
                    "year": source["year"],
                    "title": source["title"],
                    "locator": source["locator"],
                    "stable_url": source["stable_url"],
                    "doi": source["doi"],
                    "source_family": source["source_family"],
                    "domain_alignment": source["domain_alignment"],
                    "support_role": support_role,
                    "association_context": source["association_context"],
                    "source_metadata_verified": "true",
                    "evidence_verified": "true",
                    "upstream_evidence_ref": reference,
                })
        d = {f"D{index}": value for index, value in enumerate(spec["dims"], start=1)}
        cases.append(CalibrationCase(
            assessment_id=assessment_id,
            node_a=spec["a"],
            node_b=spec["b"],
            calibration_stratum=spec["stratum"],
            hard_negative=spec["hard"],
            period_band=spec["period"],
            source_family=spec["family"],
            design_history_domain=spec["domain"],
            primary_generic_type=spec["primary"],
            secondary_generic_type=spec["secondary"],
            historical_scope=spec["historical"],
            context_scope=spec["context"],
            rubric_dimensions=d,
            cooccurrence_only=spec["co"],
            qualification_required=spec["qual"],
            evidence_refs=tuple(bound_ids),
            expected_direct_pass=spec["expected"],
            expected_skip_one_pass=spec["expected"],
            qualification=spec["qualification"],
            decision_reason=spec["reason"],
        ))
    return cases, provenance
