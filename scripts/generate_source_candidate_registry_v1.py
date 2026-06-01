#!/usr/bin/env python3
"""Build a 200+ source candidate registry for rights-aware capture planning.

The public payload only counts sources that already produced published surfaces.
This registry is broader: it is the explicit source universe we can route future
crawlers through, with community/university/government status visible as data.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

MATRIX = DATA / "source_expansion_matrix.csv"
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
OUTPUT = DATA / "source_candidate_registry_v1.csv"
REPORT = DOCS / "SOURCE_CANDIDATE_REGISTRY_v1.md"


FIELDNAMES = [
    "candidate_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "locality",
    "source_kind",
    "institutional_level",
    "institution_class",
    "access_family",
    "url",
    "expected_record_types",
    "period_strength",
    "image_strategy",
    "text_strategy",
    "rights_risk",
    "automation_priority",
    "verification_status",
    "current_ingest_status",
    "notes",
]


def clean(value: str | None) -> str:
    return (value or "").strip()


def guess_institution_class(source_type: str, name: str) -> str:
    text = f"{source_type} {name}".lower()
    if "community" in text or "movement" in text or "activist" in text:
        return "community"
    if "university" in text or "school" in text or "college" in text:
        return "university"
    if "national" in text or "state" in text or "government" in text or "archives" in text:
        return "government"
    if "municipal" in text or "city" in text:
        return "municipal"
    if "museum" in text:
        return "museum"
    if "aggregator" in text or "metadata" in text:
        return "aggregator"
    if "library" in text:
        return "library"
    return "independent"


def guess_level(source_type: str, name: str) -> str:
    text = f"{source_type} {name}".lower()
    if "global" in text or "world" in text or "international" in text:
        return "transnational"
    if "national" in text:
        return "national"
    if "state" in text or "provincial" in text:
        return "state/provincial"
    if "municipal" in text or "city" in text:
        return "municipal"
    if "university" in text or "college" in text:
        return "university"
    if "community" in text or "movement" in text:
        return "community"
    return "institutional"


def guess_access_family(access_method: str, api_note: str) -> str:
    text = f"{access_method} {api_note}".lower()
    families = []
    for label in ["iiif", "oai", "contentdm", "omeka", "dspace", "kramerius", "api"]:
        if label in text:
            families.append(label.upper() if label != "api" else "API")
    if "web" in text or "html" in text:
        families.append("HTML")
    if "pdf" in text:
        families.append("PDF")
    return "+".join(dict.fromkeys(families)) or "manual"


def image_strategy(default_image_zone: str) -> str:
    zone = clean(default_image_zone) or "IMG00"
    if zone == "IMG03":
        return "prefer_open_image"
    if zone == "IMG02":
        return "source_viewer_or_iiif"
    if zone == "IMG01":
        return "thumbnail_only"
    if zone == "IMG04":
        return "text_only"
    return "link_only_until_rights_verified"


def active_sources() -> set[str]:
    if not PAYLOAD.exists():
        return set()
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    return {
        clean(surface.get("sourceName"))
        for surface in data.get("surfaces", [])
        if clean(surface.get("sourceName"))
    }


def active_payload_rows(existing_names: set[str]) -> list[dict[str, str]]:
    if not PAYLOAD.exists():
        return []
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    by_name: dict[str, dict[str, str]] = {}
    for surface in data.get("surfaces", []):
        name = clean(surface.get("sourceName"))
        if not name or name.lower() in existing_names or name in by_name:
            continue
        by_name[name] = {
            "candidate_id": f"PAY{len(by_name) + 1:03d}",
            "source_name": name,
            "macro_region": "active payload / needs registry mapping",
            "country_or_region": "",
            "locality": "",
            "source_kind": "published capture source",
            "institutional_level": "institutional",
            "institution_class": guess_institution_class("published capture source", name),
            "access_family": "captured adapter",
            "url": clean(surface.get("sourceUrl")),
            "expected_record_types": clean(surface.get("objectType")),
            "period_strength": "has published surfaces",
            "image_strategy": image_strategy(clean((surface.get("image") or {}).get("state"))),
            "text_strategy": "published-surface text varies",
            "rights_risk": clean((surface.get("rights") or {}).get("state")),
            "automation_priority": "P0 already publishing",
            "verification_status": "active_payload_source_needs_registry_backfill",
            "current_ingest_status": "active_in_public_payload",
            "notes": "This source appears in generated/public_surfaces_v1.json but was not matched to source_expansion_matrix.csv by name.",
        }
    return list(by_name.values())


def matrix_rows() -> list[dict[str, str]]:
    active = active_sources()
    rows: list[dict[str, str]] = []
    with MATRIX.open(newline="", encoding="utf-8") as f:
        for src in csv.DictReader(f):
            name = clean(src.get("source_name"))
            source_type = clean(src.get("source_type"))
            rows.append(
                {
                    "candidate_id": clean(src.get("matrix_id")),
                    "source_name": name,
                    "macro_region": clean(src.get("region")),
                    "country_or_region": "",
                    "locality": "",
                    "source_kind": source_type,
                    "institutional_level": guess_level(source_type, name),
                    "institution_class": guess_institution_class(source_type, name),
                    "access_family": guess_access_family(
                        clean(src.get("access_method")), clean(src.get("api_iiif_oai_data"))
                    ),
                    "url": clean(src.get("url")),
                    "expected_record_types": clean(src.get("record_family")),
                    "period_strength": "; ".join(
                        part
                        for part in [
                            f"1830-1930={clean(src.get('period_1830_1930'))}",
                            f"1931-1970={clean(src.get('period_1931_1970'))}",
                            f"1971-2000={clean(src.get('period_1971_2000'))}",
                            f"2001-2026={clean(src.get('period_2001_2026'))}",
                        ]
                        if not part.endswith("=")
                    ),
                    "image_strategy": image_strategy(clean(src.get("default_image_zone"))),
                    "text_strategy": "text-rich" if clean(src.get("text_value")).lower().startswith("high") else "metadata-plus-context",
                    "rights_risk": clean(src.get("rights_clarity")),
                    "automation_priority": clean(src.get("priority_1930_1970")) or clean(src.get("recommended_use")),
                    "verification_status": "deep_research_seed",
                    "current_ingest_status": "active_in_public_payload" if name in active else "candidate_from_matrix",
                    "notes": clean(src.get("use_notes")),
                }
            )
    return rows


def additions() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        name: str,
        macro: str,
        country: str,
        kind: str,
        level: str,
        cls: str,
        access: str,
        url: str,
        records: str,
        periods: str,
        image: str,
        text: str,
        risk: str,
        priority: str,
        notes: str,
        locality: str = "",
    ) -> None:
        rows.append(
            {
                "candidate_id": f"ESC{len(rows) + 1:03d}",
                "source_name": name,
                "macro_region": macro,
                "country_or_region": country,
                "locality": locality,
                "source_kind": kind,
                "institutional_level": level,
                "institution_class": cls,
                "access_family": access,
                "url": url,
                "expected_record_types": records,
                "period_strength": periods,
                "image_strategy": image,
                "text_strategy": text,
                "rights_risk": risk,
                "automation_priority": priority,
                "verification_status": "needs_url_protocol_verification",
                "current_ingest_status": "new_edge_candidate",
                "notes": notes,
            }
        )

    # Latin America and Caribbean: periodicals, universities, political graphics.
    add("AHIRA Archivo Historico de Revistas Argentinas", "Latin America", "Argentina", "periodical archive", "community/university", "university", "HTML+PDF", "https://ahira.com.ar/", "magazines; journals; advertisements; cover design", "1830-1930=secondary;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 edge-periodical", "Strong for magazine design outside museum object logic.")
    add("Fundacion IDA Investigacion en Diseno Argentino", "Latin America", "Argentina", "design archive", "community", "community", "HTML", "https://www.fundacionida.org/", "design archives; posters; identity; ephemera", "1931-1970=secondary;1971-2000=strong;2001-2026=secondary", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 design-archive", "Important non-Anglophone design-history authority.")
    add("Biblioteca Nacional Mariano Moreno Digital", "Latin America", "Argentina", "national library", "national", "government", "HTML+OAI?", "https://www.bn.gov.ar/", "periodicals; books; posters; ephemera", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P2 national-library", "Government source for Argentine print culture.")
    add("Archivo General de la Nacion Argentina", "Latin America", "Argentina", "national archive", "national", "government", "HTML", "https://www.argentina.gob.ar/interior/archivo-general", "posters; public records; photographs", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 government-archive", "Useful for state communication and public campaigns.")
    add("CeDInCI Archivo", "Latin America", "Argentina", "political archive", "community/university", "community", "HTML", "https://cedinci.org/", "political posters; pamphlets; periodicals", "1931-1970=secondary;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 movement-archive", "Important political graphics and print-culture source.")
    add("Biblioteca Brasiliana Guita e Jose Mindlin", "Latin America", "Brazil", "university digital library", "university", "university", "HTML+IIIF?", "https://digital.bbm.usp.br/", "books; periodicals; illustrated print", "1830-1930=strong;1931-1970=secondary", "source_viewer_or_iiif", "text-rich", "Med", "P2 university-library", "USP source for Brazilian print history.")
    add("Arquivo Publico do Estado de Sao Paulo", "Latin America", "Brazil", "state archive", "state/provincial", "government", "HTML", "https://www.arquivoestado.sp.gov.br/", "government posters; public campaigns; printed ephemera", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 state-archive", "State-level public communication source.")
    add("Museu da Pessoa", "Latin America", "Brazil", "community archive", "community", "community", "HTML", "https://museudapessoa.org/", "oral histories; community memory; graphic context", "1971-2000=secondary;2001-2026=strong", "text_only", "text-rich", "Med", "P3 context", "Contextual source for design labor and community narratives.")
    add("Biblioteca Nacional de Colombia Digital", "Latin America", "Colombia", "national library", "national", "government", "HTML", "https://www.bibliotecanacional.gov.co/", "newspapers; periodicals; books; posters", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P2 national-library", "Needed for Colombian print and poster context.")
    add("Banco de la Republica Biblioteca Virtual", "Latin America", "Colombia", "public cultural library", "national", "government", "HTML", "https://www.banrepcultural.org/", "exhibition texts; books; cultural ephemera", "1931-1970=secondary;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P2 public-culture", "Public institutional source with reading value.")
    add("Biblioteca Nacional del Peru Digital", "Latin America", "Peru", "national library", "national", "government", "HTML", "https://www.bnp.gob.pe/", "books; periodicals; newspapers; posters", "1830-1930=secondary;1931-1970=strong", "link_only_until_rights_verified", "text-rich", "Med", "P2 national-library", "Andean print-culture gap filler.")
    add("Biblioteca Nacional de Uruguay Digital", "Latin America", "Uruguay", "national library", "national", "government", "HTML", "https://www.bibna.gub.uy/", "periodicals; books; public documents", "1830-1930=secondary;1931-1970=strong", "link_only_until_rights_verified", "text-rich", "Med", "P3 national-library", "Needed for Southern Cone coverage.")
    add("Biblioteca Nacional de Bolivia", "Latin America", "Bolivia", "national library", "national", "government", "HTML", "https://www.archivoybibliotecanacionales.org.bo/", "periodicals; books; printed ephemera", "1830-1930=secondary;1931-1970=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "Low-represented national print source.")
    add("Archivo General de la Nacion Mexico", "Latin America", "Mexico", "national archive", "national", "government", "HTML", "https://www.gob.mx/agn", "public campaigns; posters; state print", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 government-archive", "Complements Hemeroteca Nacional de Mexico.")
    add("UNAM Repositorio Institucional", "Latin America", "Mexico", "university repository", "university", "university", "DSpace/OAI?", "https://repositorio.unam.mx/", "theses; books; exhibition texts; research papers", "1931-1970=secondary;1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P2 university-text", "Text enrichment for Mexican design and visual culture.")
    add("Archivo Jose Guadalupe Posada / Museo Nacional de la Estampa", "Latin America", "Mexico", "museum/archive", "national", "government", "HTML", "https://munae.inba.gob.mx/", "prints; posters; exhibition texts", "1830-1930=strong;1931-1970=secondary", "link_only_until_rights_verified", "text-rich", "Med", "P2 print-history", "Bridge from popular print to graphic design history.")

    # Africa: political graphics, university repositories, local memory.
    add("University of Cape Town Digital Collections", "Africa", "South Africa", "university digital collection", "university", "university", "HTML", "https://digitalcollections.lib.uct.ac.za/", "posters; pamphlets; anti-apartheid print; photographs", "1931-1970=secondary;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 university-archive", "High value for southern African political print.")
    add("Mayibuye Archives", "Africa", "South Africa", "university archive", "university", "university", "HTML", "https://www.uwc.ac.za/", "anti-apartheid posters; pamphlets; photographs", "1931-1970=secondary;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 movement-archive", "Core source for political visual culture.")
    add("Digital Bleek and Lloyd / UCT Libraries", "Africa", "South Africa", "university archive", "university", "university", "HTML", "https://lloydbleekcollection.cs.uct.ac.za/", "archive material; scripts; colonial print context", "1830-1930=secondary", "text_only", "text-rich", "Med", "P4 context", "Contextual script/colonial knowledge source.")
    add("National Library of South Africa", "Africa", "South Africa", "national library", "national", "government", "HTML", "https://www.nlsa.ac.za/", "periodicals; books; posters", "1830-1930=secondary;1931-1970=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 national-library", "National print-culture source.")
    add("Kenya National Archives", "Africa", "Kenya", "national archive", "national", "government", "HTML", "https://archives.go.ke/", "public posters; tourism graphics; state print", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 government-archive", "East African government visual culture gap.")
    add("University of Nairobi Repository", "Africa", "Kenya", "university repository", "university", "university", "DSpace/OAI", "http://erepository.uonbi.ac.ke/", "theses; reports; communication design texts", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "Text enrichment and regional design studies.")
    add("Makerere University Institutional Repository", "Africa", "Uganda", "university repository", "university", "university", "DSpace/OAI", "http://makir.mak.ac.ug/", "theses; reports; public communication studies", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "East African text source.")
    add("University of Ghana Digital Collections", "Africa", "Ghana", "university repository", "university", "university", "DSpace/OAI?", "https://ugspace.ug.edu.gh/", "theses; reports; posters context", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "West African design/communication scholarship source.")
    add("National Archives of Ghana", "Africa", "Ghana", "national archive", "national", "government", "HTML", "https://praad.gov.gh/", "government records; public communication", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P4 government-archive", "Government source for state communication.")
    add("University of Ibadan Repository", "Africa", "Nigeria", "university repository", "university", "university", "DSpace/OAI?", "https://ir.library.ui.edu.ng/", "theses; journals; communication studies", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "Nigerian scholarship source.")
    add("University of Lagos Institutional Repository", "Africa", "Nigeria", "university repository", "university", "university", "DSpace/OAI?", "http://ir.unilag.edu.ng/", "theses; reports; design/communication texts", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "Lagos-centered academic source.")
    add("Chimurenga Library", "Africa", "Pan-African", "community publishing archive", "community", "community", "HTML", "https://chimurengalibrary.co.za/", "magazines; posters; publishing history; essays", "1971-2000=strong;2001-2026=strong", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 community-publishing", "Vital noncanonical editorial/design source.")
    add("Africa Media Online", "Africa", "South Africa / regional", "commercial/community image archive", "regional", "independent", "HTML", "https://www.africamediaonline.com/", "photographs; posters; visual culture", "1931-1970=secondary;1971-2000=strong", "link_only_until_rights_verified", "metadata-plus-context", "High", "P4 link-only", "Use mainly as source-return index.")

    # Middle East, North Africa, and Turkey.
    add("Arab Image Foundation", "Middle East and North Africa", "Lebanon / regional", "community image archive", "community", "community", "HTML", "https://arabimagefoundation.org/", "photographs; posters; printed visual culture", "1931-1970=strong;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "High", "P1 community-archive", "Important regional visual archive; rights-sensitive.")
    add("Akkasah Center for Photography", "Middle East and North Africa", "United Arab Emirates / regional", "university archive", "university", "university", "HTML", "https://akkasah.org/", "photographs; studio ephemera; printed visual culture", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "text-rich", "High", "P2 university-archive", "NYUAD regional visual culture source.")
    add("SALT Research", "Middle East and North Africa", "Turkey", "research archive", "independent", "independent", "HTML", "https://archives.saltresearch.org/", "posters; graphic ephemera; exhibition texts; periodicals", "1931-1970=secondary;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 design-archive", "High-value Turkish design and visual culture archive.")
    add("Istanbul Research Institute Collections", "Middle East and North Africa", "Turkey", "research archive", "independent", "independent", "HTML", "https://www.iae.org.tr/", "posters; ephemera; photographs; exhibition texts", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P2 local-archive", "Urban print and exhibition context.")
    add("Ataturk Library Digital Archive", "Middle East and North Africa", "Turkey", "municipal library", "municipal", "municipal", "HTML", "https://ataturkkitapligi.ibb.gov.tr/", "periodicals; newspapers; books; printed ephemera", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P2 municipal-library", "Municipal source for Istanbul print culture.")
    add("National Library and Archives of Iran", "Middle East and North Africa", "Iran", "national archive/library", "national", "government", "HTML", "https://www.nlai.ir/", "books; periodicals; posters; public records", "1931-1970=strong;1971-2000=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 national-library", "Needed for Iranian graphic/typographic history.")
    add("University of Tehran Digital Library", "Middle East and North Africa", "Iran", "university library", "university", "university", "HTML", "https://utlib.ut.ac.ir/", "theses; books; design texts", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "Text enrichment for Iranian design research.")
    add("Bibliotheque Nationale du Royaume du Maroc", "Middle East and North Africa", "Morocco", "national library", "national", "government", "HTML", "https://www.bnrm.ma/", "periodicals; books; posters", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "Maghreb print-culture gap.")
    add("Bibliotheque Nationale de Tunisie", "Middle East and North Africa", "Tunisia", "national library", "national", "government", "HTML", "http://www.bibliotheque.nat.tn/", "periodicals; books; printed ephemera", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "North African public print source.")
    add("National Library and Archives of Egypt", "Middle East and North Africa", "Egypt", "national library/archive", "national", "government", "HTML", "https://www.darelkotob.gov.eg/", "books; periodicals; posters; public print", "1830-1930=strong;1931-1970=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 national-library", "Major Arabic print-culture source.")

    # South Asia.
    add("Roja Muthiah Research Library", "South Asia", "India", "research library", "independent", "independent", "HTML", "https://www.rmrl.in/", "Tamil print; posters; periodicals; ephemera", "1830-1930=strong;1931-1970=strong", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 regional-print", "Crucial South Indian print-culture source.")
    add("Panjab Digital Library", "South Asia", "India / Punjab", "community digital library", "community", "community", "HTML", "https://panjabdigilib.org/", "books; posters; newspapers; ephemera", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P2 community-library", "Language/regional print archive.")
    add("Rekhta", "South Asia", "India / Urdu", "literary digital archive", "independent", "independent", "HTML", "https://www.rekhta.org/", "periodicals; book covers; typography context", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "text-rich", "Med", "P4 contextual-text", "Urdu print culture and typography context.")
    add("Bangladesh National Archives", "South Asia", "Bangladesh", "national archive", "national", "government", "HTML", "https://nanl.gov.bd/", "government records; printed public communication", "1931-1970=secondary;1971-2000=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 government-archive", "Postcolonial public communication source.")
    add("BRAC University Institutional Repository", "South Asia", "Bangladesh", "university repository", "university", "university", "DSpace/OAI", "http://dspace.bracu.ac.bd/", "theses; reports; communication/design texts", "1971-2000=strong;2001-2026=strong", "text_only", "text-rich", "Low-Med", "P3 university-text", "Bangladesh design and communication scholarship source.")
    add("National Library of Sri Lanka", "South Asia", "Sri Lanka", "national library", "national", "government", "HTML", "https://www.natlib.lk/", "books; periodicals; public documents", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "Sri Lankan print-history gap.")
    add("National Archives of Sri Lanka", "South Asia", "Sri Lanka", "national archive", "national", "government", "HTML", "https://www.archives.gov.lk/", "government posters; public records", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 government-archive", "State communication source.")
    add("Madan Puraskar Pustakalaya", "South Asia", "Nepal", "community/library archive", "community", "community", "HTML", "https://madanpuraskar.org/", "Nepali books; periodicals; ephemera", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 regional-library", "Nepal language print source.")
    add("Nepal National Library", "South Asia", "Nepal", "national library", "national", "government", "HTML", "https://nnl.gov.np/", "books; periodicals; public print", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P4 national-library", "National gap coverage.")

    # East Asia.
    add("Japan Search", "East Asia", "Japan", "national aggregator", "national", "government", "API+HTML", "https://jpsearch.go.jp/", "museum/library/archive records; posters; books", "1830-1930=strong;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P1 aggregator", "Japanese cross-institution discovery layer.")
    add("National Diet Library Digital Collections", "East Asia", "Japan", "national library", "national", "government", "API+IIIF+HTML", "https://dl.ndl.go.jp/", "books; magazines; posters; typography", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 national-library", "Separate from NDL Search; direct digital object source.")
    add("Tokyo Metropolitan Library Digital Archive", "East Asia", "Japan", "municipal library", "municipal", "municipal", "HTML", "https://archive.library.metro.tokyo.lg.jp/", "posters; maps; magazines; local print", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P2 municipal-library", "Local urban print source.")
    add("Kyoto University Rare Materials Digital Archive", "East Asia", "Japan", "university archive", "university", "university", "IIIF+HTML", "https://rmda.kulib.kyoto-u.ac.jp/", "books; prints; ephemera; typography context", "1830-1930=strong;1931-1970=secondary", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 university-library", "High-quality IIIF source.")
    add("Waseda University Theatre Museum Database", "East Asia", "Japan", "university museum", "university", "university", "HTML", "https://enpaku.w.waseda.jp/", "posters; programs; theatre ephemera", "1830-1930=secondary;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P2 poster-ephemera", "Strong performing-arts poster source.")
    add("National Archives of Japan Digital Archive", "East Asia", "Japan", "national archive", "national", "government", "HTML", "https://www.digital.archives.go.jp/", "government documents; public communication", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Low-Med", "P3 government-archive", "Public information design context.")
    add("National Library of Korea Digital Collection", "East Asia", "Korea", "national library", "national", "government", "HTML", "https://www.nl.go.kr/", "books; periodicals; posters; typography", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 national-library", "Korean print source.")
    add("Seoul Museum of History Digital Archive", "East Asia", "Korea", "municipal museum archive", "municipal", "municipal", "HTML", "https://museum.seoul.go.kr/", "urban posters; ephemera; photographs", "1931-1970=secondary;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P2 municipal-archive", "City-scale visual culture source.")
    add("Korean Film Archive", "East Asia", "Korea", "specialized public archive", "national", "government", "HTML", "https://www.koreafilm.or.kr/", "film posters; lobby cards; graphic ephemera", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P1 poster-source", "Strong poster graphics source outside design museums.")
    add("Hong Kong Memory", "East Asia", "Hong Kong", "public memory archive", "regional", "government", "HTML", "https://www.hkmemory.hk/", "advertising; posters; packaging; street graphics", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 regional-memory", "Important for Hong Kong visual culture.")
    add("HKUL Digital Initiatives", "East Asia", "Hong Kong", "university digital collection", "university", "university", "HTML", "https://digitalrepository.lib.hku.hk/", "newspapers; posters; photographs; books", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P2 university-library", "University source for China/Hong Kong records.")
    add("Academia Sinica Digital Resources", "East Asia", "Taiwan", "research institution archive", "national", "government", "HTML", "https://digitalarchives.sinica.edu.tw/", "periodicals; images; archival records", "1931-1970=strong;1971-2000=secondary", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P2 research-archive", "Taiwan/Chinese-language archive.")
    add("National Central Library Taiwan", "East Asia", "Taiwan", "national library", "national", "government", "HTML", "https://www.ncl.edu.tw/", "books; periodicals; posters; newspapers", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 national-library", "Core Taiwan print source.")
    add("Shanghai Library Digital Collections", "East Asia", "China", "municipal library", "municipal", "municipal", "HTML", "https://www.library.sh.cn/", "periodicals; newspapers; calendar posters; books", "1830-1930=strong;1931-1970=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 municipal-library", "Local source for Shanghai print culture.")

    # Southeast Asia.
    add("BookSG", "Southeast Asia", "Singapore", "national library digital collection", "national", "government", "HTML", "https://eresources.nlb.gov.sg/printheritage/", "books; magazines; public print", "1931-1970=secondary;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-library", "Singapore print heritage source.")
    add("PictureSG", "Southeast Asia", "Singapore", "national image archive", "national", "government", "HTML", "https://eresources.nlb.gov.sg/pictures/", "posters; photographs; street graphics", "1931-1970=secondary;1971-2000=strong", "thumbnail_only", "metadata-plus-context", "Med", "P2 image-archive", "Visual source for Singapore.")
    add("National Archives of Singapore", "Southeast Asia", "Singapore", "national archive", "national", "government", "HTML", "https://www.nas.gov.sg/archivesonline/", "posters; photographs; public campaigns", "1931-1970=secondary;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P1 government-archive", "Government/public communication source.")
    add("Khastara Perpusnas Indonesia", "Southeast Asia", "Indonesia", "national library digital collection", "national", "government", "HTML", "https://khastara.perpusnas.go.id/", "books; periodicals; newspapers; posters", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Med", "P1 national-library", "Indonesian print-culture source.")
    add("ANRI Arsip Nasional Republik Indonesia", "Southeast Asia", "Indonesia", "national archive", "national", "government", "HTML", "https://anri.go.id/", "government print; posters; photographs", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 government-archive", "State communication source.")
    add("National Library of the Philippines Digital Collections", "Southeast Asia", "Philippines", "national library", "national", "government", "HTML", "https://web.nlp.gov.ph/", "books; newspapers; periodicals; posters", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 national-library", "Philippine print source.")
    add("Filipinas Heritage Library", "Southeast Asia", "Philippines", "heritage library", "independent", "independent", "HTML", "https://www.filipinaslibrary.org.ph/", "photographs; ephemera; posters; books", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "text-rich", "Med", "P2 heritage-library", "Non-state Philippine visual source.")
    add("Ateneo Rizal Library Digital Archives", "Southeast Asia", "Philippines", "university archive", "university", "university", "HTML", "https://rizal.library.ateneo.edu/", "periodicals; posters; books; photographs", "1931-1970=strong;1971-2000=secondary", "source_viewer_or_iiif", "text-rich", "Med", "P2 university-archive", "University source for Manila print culture.")
    add("National Archives of Thailand", "Southeast Asia", "Thailand", "national archive", "national", "government", "HTML", "https://www.nat.go.th/", "government posters; public records; photographs", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 government-archive", "Thai public graphics source.")
    add("Thai National Library Digital Collections", "Southeast Asia", "Thailand", "national library", "national", "government", "HTML", "https://www.nlt.go.th/", "books; periodicals; posters", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "Thai print-culture source.")
    add("National Library of Vietnam", "Southeast Asia", "Vietnam", "national library", "national", "government", "HTML", "https://nlv.gov.vn/", "books; periodicals; propaganda/public posters", "1931-1970=strong;1971-2000=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 national-library", "Vietnamese print source.")
    add("Vietnam National Archives", "Southeast Asia", "Vietnam", "national archive", "national", "government", "HTML", "https://luutru.gov.vn/", "public records; posters; printed state material", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P2 government-archive", "Government visual communication source.")

    # Eastern Europe / Caucasus / Central Asia.
    add("Kramerius Registry", "Eastern Europe", "Czech Republic / Slovakia", "protocol registry", "transnational", "aggregator", "KRAMERIUS+API", "https://registr.digitalniknihovna.cz/", "libraries using Kramerius; periodicals; books", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 protocol-family", "Adapter family can unlock many local libraries.")
    add("Czech Digital Library", "Eastern Europe", "Czech Republic", "national aggregator", "national", "government", "KRAMERIUS+API+IIIF", "https://www.digitalniknihovna.cz/", "periodicals; posters; books; advertisements", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 national-aggregator", "High-value non-Anglophone print source.")
    add("Slovak Digital Library", "Eastern Europe", "Slovakia", "national library", "national", "government", "KRAMERIUS+HTML", "https://dikda.snk.sk/", "periodicals; books; posters", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-library", "Slovak print source.")
    add("dLib.si Digital Library of Slovenia", "Eastern Europe", "Slovenia", "national library", "national", "government", "HTML+OAI?", "https://www.dlib.si/", "periodicals; posters; books", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-library", "Slovenian print source.")
    add("Croatian Digital Library", "Eastern Europe", "Croatia", "national library", "national", "government", "HTML", "https://digitalna.nsk.hr/", "periodicals; books; posters", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P3 national-library", "Croatian print source.")
    add("National Library of Serbia Digital Library", "Eastern Europe", "Serbia", "national library", "national", "government", "HTML", "https://digitalna.nb.rs/", "periodicals; posters; books", "1830-1930=secondary;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P3 national-library", "Serbian print source.")
    add("National Library of Bulgaria Digital Library", "Eastern Europe", "Bulgaria", "national library", "national", "government", "HTML", "https://www.nationallibrary.bg/", "periodicals; books; posters", "1830-1930=secondary;1931-1970=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "Bulgarian print source.")
    add("ePaveldas", "Eastern Europe", "Lithuania", "national heritage portal", "national", "government", "HTML+IIIF?", "https://www.epaveldas.lt/", "periodicals; posters; books; photographs", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-portal", "Baltic print source.")
    add("DIGAR Estonian Articles and Digital Archive", "Eastern Europe", "Estonia", "national library", "national", "government", "HTML+API?", "https://www.digar.ee/", "newspapers; periodicals; books; posters", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-library", "Baltic periodical source.")
    add("Latvian National Digital Library", "Eastern Europe", "Latvia", "national library", "national", "government", "HTML", "https://www.lndb.lv/", "periodicals; books; posters", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-library", "Baltic print source.")
    add("Szukaj w Archiwach", "Eastern Europe", "Poland", "national archive aggregator", "national", "government", "HTML+API?", "https://www.szukajwarchiwach.gov.pl/", "posters; public records; photographs", "1830-1930=secondary;1931-1970=strong;1971-2000=secondary", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P2 government-archive", "Polish archive source beyond poster canon.")
    add("NAC Narodowe Archiwum Cyfrowe", "Eastern Europe", "Poland", "national digital archive", "national", "government", "HTML", "https://www.nac.gov.pl/", "photographs; posters; public communication", "1931-1970=strong;1971-2000=secondary", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P2 government-archive", "Government visual archive.")
    add("Ukrainian Liberation Movement Archive", "Eastern Europe", "Ukraine", "community archive", "community", "community", "HTML", "https://avr.org.ua/", "posters; leaflets; underground print", "1931-1970=strong;1971-2000=secondary", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 movement-archive", "Non-state political print source.")
    add("Vernadsky National Library Digital Collections", "Eastern Europe", "Ukraine", "national library", "national", "government", "HTML", "http://www.nbuv.gov.ua/", "books; periodicals; posters; bibliographic records", "1830-1930=secondary;1931-1970=strong", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P3 national-library", "Ukrainian print source.")
    add("National Library of Armenia Digital Collections", "Eastern Europe / Caucasus", "Armenia", "national library", "national", "government", "HTML", "https://www.nla.am/", "books; periodicals; posters", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P4 national-library", "Caucasus gap coverage.")
    add("National Library of Georgia Digital Library", "Eastern Europe / Caucasus", "Georgia", "national library", "national", "government", "HTML", "https://www.nplg.gov.ge/", "books; periodicals; posters", "1931-1970=secondary;1971-2000=secondary", "link_only_until_rights_verified", "metadata-plus-context", "Med", "P4 national-library", "Caucasus gap coverage.")

    # Oceania and Pacific.
    add("State Library Victoria", "Oceania and Pacific", "Australia", "state library", "state/provincial", "government", "HTML+API?", "https://www.slv.vic.gov.au/", "posters; ephemera; newspapers; photographs", "1830-1930=strong;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 state-library", "State-level non-national source.")
    add("State Library of Queensland", "Oceania and Pacific", "Australia", "state library", "state/provincial", "government", "HTML", "https://www.slq.qld.gov.au/", "posters; ephemera; community archives", "1830-1930=secondary;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 state-library", "State and Indigenous visual culture source.")
    add("State Library of Western Australia", "Oceania and Pacific", "Australia", "state library", "state/provincial", "government", "HTML", "https://slwa.wa.gov.au/", "posters; ephemera; photographs; newspapers", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P3 state-library", "Regional Australian source.")
    add("Hocken Collections", "Oceania and Pacific", "Aotearoa New Zealand", "university archive", "university", "university", "HTML", "https://www.otago.ac.nz/library/hocken", "posters; ephemera; music graphics; political print", "1931-1970=secondary;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med", "P2 university-archive", "Strong local ephemera archive.")
    add("Auckland Libraries Heritage Collections", "Oceania and Pacific", "Aotearoa New Zealand", "municipal library", "municipal", "municipal", "HTML", "https://kura.aucklandlibraries.govt.nz/", "posters; photographs; ephemera", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P2 municipal-library", "City-level visual culture source.")
    add("Pacific Manuscripts Bureau", "Oceania and Pacific", "Pacific Islands", "university/regional archive", "regional", "university", "HTML", "https://asiapacific.anu.edu.au/pambu/", "periodicals; community records; printed ephemera", "1931-1970=secondary;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med", "P3 regional-archive", "Pacific regional source.")
    add("University of Hawai'i eVols", "Oceania and Pacific", "Pacific / Hawai'i", "university repository", "university", "university", "DSpace/OAI", "https://evols.library.manoa.hawaii.edu/", "periodicals; books; reports; ephemera", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P3 university-repository", "Pacific print and public communication source.")

    # North America: prioritize community/university/movement over large museums.
    add("Digital Public Library of America", "North America", "United States", "national aggregator", "national", "aggregator", "API", "https://dp.la/", "aggregated local archive records; posters; ephemera", "1830-1930=strong;1931-1970=strong;1971-2000=strong", "thumbnail_only", "metadata-plus-context", "Med", "P1 aggregator", "Useful for routing into local sources rather than replacing them.")
    add("Calisphere", "North America", "United States / California", "regional aggregator", "state/provincial", "university", "API+HTML", "https://calisphere.org/", "posters; ephemera; movement archives; photographs", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 regional-aggregator", "Local/community source discovery.")
    add("UCLA Library Digital Collections", "North America", "United States", "university digital collection", "university", "university", "IIIF+HTML", "https://digital.library.ucla.edu/", "posters; prints; ephemera; photographs", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 university-archive", "Los Angeles/transnational visual culture.")
    add("University of Washington Libraries Digital Collections", "North America", "United States", "university digital collection", "university", "university", "CONTENTDM+IIIF?", "https://digitalcollections.lib.washington.edu/", "posters; ephemera; photographs; labor materials", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P2 university-archive", "Pacific Northwest and Asian American material.")
    add("Portal to Texas History", "North America", "United States / Texas", "university regional portal", "state/provincial", "university", "API+IIIF+HTML", "https://texashistory.unt.edu/", "newspapers; posters; advertisements; ephemera", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 regional-portal", "Newspaper/ad design source.")
    add("Minnesota Digital Library", "North America", "United States / Minnesota", "regional aggregator", "state/provincial", "aggregator", "CONTENTDM+HTML", "https://collection.mndigital.org/", "posters; local print; ephemera", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P3 regional-aggregator", "Local institutional source.")
    add("Duke Digital Collections", "North America", "United States", "university digital collection", "university", "university", "IIIF+HTML", "https://repository.duke.edu/dc", "advertising; posters; trade cards; radical print", "1830-1930=strong;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 university-archive", "Strong advertising and political ephemera.")
    add("Brown Digital Repository", "North America", "United States", "university repository", "university", "university", "API+IIIF?", "https://repository.library.brown.edu/", "posters; political graphics; ephemera", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P2 university-repository", "Movement and political print source.")
    add("NYU Tamiment Library and Robert F. Wagner Labor Archives", "North America", "United States", "university archive", "university", "university", "HTML", "https://specialcollections.library.nyu.edu/", "labor posters; pamphlets; movement graphics", "1931-1970=strong;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med", "P1 movement-archive", "Noncanonical labor/political graphics.")
    add("Interference Archive", "North America", "United States", "community archive", "community", "community", "Omeka/HTML", "https://interferencearchive.org/", "posters; zines; movement graphics; ephemera", "1971-2000=strong;2001-2026=strong", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 community-archive", "Important community archive; rights-sensitive.")
    add("Center for the Study of Political Graphics", "North America", "United States", "community/nonprofit archive", "community", "community", "HTML", "https://politicalgraphics.org/", "political posters; movement graphics", "1931-1970=secondary;1971-2000=strong;2001-2026=strong", "link_only_until_rights_verified", "text-rich", "Med-High", "P1 community-archive", "Dedicated political graphics archive.")
    add("Queer Zine Archive Project", "North America", "United States / transnational", "community archive", "community", "community", "HTML+PDF", "https://www.qzap.org/", "zines; typography; DIY print", "1971-2000=strong;2001-2026=strong", "link_only_until_rights_verified", "text-rich", "High", "P2 community-archive", "Important noninstitutional graphic culture.")
    add("Library and Archives Canada", "North America", "Canada", "national archive/library", "national", "government", "HTML", "https://library-archives.canada.ca/", "posters; public campaigns; periodicals", "1830-1930=strong;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Med", "P2 national-archive", "Canadian public/graphic source.")
    add("Bibliotheque et Archives nationales du Quebec", "North America", "Canada / Quebec", "provincial library/archive", "state/provincial", "government", "HTML+IIIF?", "https://www.banq.qc.ca/", "posters; newspapers; advertisements; books", "1830-1930=strong;1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 provincial-library", "Francophone North American print source.")

    # Europe: regional/municipal/university additions, not the usual design canon.
    add("Wellcome Library IIIF Manifests", "Western/Central Europe", "United Kingdom", "library image infrastructure", "institutional", "library", "IIIF+API", "https://wellcomecollection.org/works", "public health posters; books; campaign graphics", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 adapter-upgrade", "Separate IIIF layer for existing Wellcome source.")
    add("University of Brighton Design Archives", "Western/Central Europe", "United Kingdom", "university design archive", "university", "university", "HTML", "https://blogs.brighton.ac.uk/brightondesignarchives/", "design archives; posters; identity; education texts", "1931-1970=strong;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med", "P1 university-design-archive", "Major design archive outside museum API mode.")
    add("London Transport Museum Collections", "Western/Central Europe", "United Kingdom", "transport museum archive", "municipal/public", "museum", "HTML", "https://www.ltmuseum.co.uk/collections", "posters; maps; signage; identity", "1830-1930=secondary;1931-1970=strong;1971-2000=strong", "link_only_until_rights_verified", "text-rich", "Med", "P1 design-object-source", "Transport graphics canonical source with rich metadata.")
    add("Rijksmuseum API", "Western/Central Europe", "Netherlands", "museum API", "national", "museum", "API+IIIF", "https://data.rijksmuseum.nl/", "posters; prints; advertisements", "1830-1930=strong;1931-1970=secondary", "prefer_open_image", "metadata-plus-context", "Low", "P2 open-api", "High-quality open images for Dutch material.")
    add("Amsterdam City Archives Beeldbank", "Western/Central Europe", "Netherlands", "municipal archive", "municipal", "municipal", "HTML", "https://archief.amsterdam/beeldbank/", "posters; advertisements; urban print", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P2 municipal-archive", "City-scale print and advertising source.")
    add("Belgian Art Links and Tools / KBR BelgicaPress", "Western/Central Europe", "Belgium", "national library/aggregator", "national", "government", "HTML", "https://www.belgicapress.be/", "newspapers; periodicals; advertisements", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P2 national-library", "Belgian periodical advertising source.")
    add("ETH Zurich e-rara", "Western/Central Europe", "Switzerland", "university digital library", "university", "university", "IIIF+OAI", "https://www.e-rara.ch/", "books; specimen books; technical print", "1830-1930=strong;1931-1970=secondary", "source_viewer_or_iiif", "text-rich", "Low", "P2 university-library", "Swiss typography and print culture context.")
    add("Swiss National Library Helveticat / e-Helvetica", "Western/Central Europe", "Switzerland", "national library", "national", "government", "HTML", "https://www.e-helvetica.nb.admin.ch/", "posters; books; periodicals; graphic records", "1931-1970=strong;1971-2000=strong", "source_viewer_or_iiif", "metadata-plus-context", "Low-Med", "P1 national-library", "Swiss graphic design history source.")
    add("Biblioteca Nacional de Espana Biblioteca Digital Hispanica", "Western/Central Europe", "Spain", "national library", "national", "government", "IIIF+HTML", "https://www.bne.es/", "posters; periodicals; advertisements; books", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 national-library", "Spanish-language print source.")
    add("Hemeroteca Digital BNE", "Western/Central Europe", "Spain", "newspaper portal", "national", "government", "HTML", "https://hemerotecadigital.bne.es/", "newspapers; magazines; advertisements", "1830-1930=strong;1931-1970=strong", "source_viewer_or_iiif", "text-rich", "Low-Med", "P1 newspaper-source", "Major text and advertising source.")

    return rows


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    combined: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in matrix_rows():
        key = row["source_name"].lower()
        if key not in seen:
            combined.append(row)
            seen.add(key)
    for row in additions():
        key = row["source_name"].lower()
        if key not in seen:
            combined.append(row)
            seen.add(key)
    for row in active_payload_rows(seen):
        key = row["source_name"].lower()
        if key not in seen:
            combined.append(row)
            seen.add(key)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(combined)

    by_status = Counter(row["current_ingest_status"] for row in combined)
    by_class = Counter(row["institution_class"] for row in combined)
    by_region = Counter(row["macro_region"] for row in combined)
    edge_count = sum(
        1
        for row in combined
        if row["institution_class"] in {"community", "university", "government", "municipal"}
    )
    report = [
        "# Source Candidate Registry v1",
        "",
        "This registry separates the public payload source count from the larger research/capture source universe. A row here is a citable source candidate, not proof that records have already been published.",
        "",
        f"- Total candidate sources: {len(combined)}",
        f"- Active in current public payload: {by_status.get('active_in_public_payload', 0)}",
        f"- Candidate rows inherited from source matrix: {by_status.get('candidate_from_matrix', 0)}",
        f"- New edge/community/local candidates: {by_status.get('new_edge_candidate', 0)}",
        f"- Community/university/government/municipal rows: {edge_count}",
        "",
        "## Institution Class",
        "",
    ]
    for key, count in by_class.most_common():
        report.append(f"- {key}: {count}")
    report.extend(["", "## Region Coverage", ""])
    for key, count in by_region.most_common():
        report.append(f"- {key}: {count}")
    report.extend(
        [
            "",
            "## Capture Rule",
            "",
            "Future crawls should select sources from this registry by protocol family and underrepresented region. The public interface should continue to count only sources that have at least one published surface, while the About/methodology page can cite this registry as the broader source universe under verification.",
            "",
            "Priority now moves to: Kramerius/OAI/IIIF/CONTENTdm/Omeka/DSpace protocol adapters, then region-balanced source batches rather than more broad museum keyword sweeps.",
        ]
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT} ({len(combined)} rows)")
    print(f"Wrote {REPORT}")
    print("status", dict(by_status))
    print("class", dict(by_class.most_common()))
    print("regions", dict(by_region.most_common()))


if __name__ == "__main__":
    main()
