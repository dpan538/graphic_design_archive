#!/usr/bin/env python3
"""Generate a conservative global edge-source discovery registry.

This script converts recent research notes into a source-discovery planning
layer. It does not crawl sources, store images, or grant image-use permission.
The output is meant to guide the next capture passes and to keep high-risk
ideas, such as proxy bypass or LLM rights interpretation, outside production
image-state decisions.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

OUTPUT = DATA / "global_edge_discovery_candidates_v1.csv"
METRICS = DATA / "global_edge_discovery_metrics_v1.csv"
REPORT = DOCS / "GLOBAL_EDGE_DISCOVERY_STRATEGY_v1.md"

FIELDNAMES = [
    "candidate_id",
    "source_name",
    "macro_region",
    "subregion",
    "country_or_region",
    "source_class",
    "institutional_level",
    "protocol_family",
    "url",
    "period_start",
    "period_end",
    "period_bands",
    "expected_record_types",
    "capture_route",
    "recommended_adapter",
    "recommended_image_policy",
    "text_enrichment_path",
    "rights_posture",
    "risk_notes",
    "priority",
    "inclusion_status",
    "notes",
]

METRIC_FIELDS = ["metric", "value", "notes"]


def row(
    source_name: str,
    macro_region: str,
    subregion: str,
    country_or_region: str,
    source_class: str,
    institutional_level: str,
    protocol_family: str,
    url: str,
    period_start: int | str,
    period_end: int | str,
    expected_record_types: str,
    capture_route: str,
    recommended_adapter: str,
    recommended_image_policy: str,
    text_enrichment_path: str,
    rights_posture: str,
    risk_notes: str,
    priority: str,
    inclusion_status: str = "candidate",
    notes: str = "",
) -> dict[str, str]:
    return {
        "source_name": source_name,
        "macro_region": macro_region,
        "subregion": subregion,
        "country_or_region": country_or_region,
        "source_class": source_class,
        "institutional_level": institutional_level,
        "protocol_family": protocol_family,
        "url": url,
        "period_start": str(period_start),
        "period_end": str(period_end),
        "period_bands": period_bands(period_start, period_end),
        "expected_record_types": expected_record_types,
        "capture_route": capture_route,
        "recommended_adapter": recommended_adapter,
        "recommended_image_policy": recommended_image_policy,
        "text_enrichment_path": text_enrichment_path,
        "rights_posture": rights_posture,
        "risk_notes": risk_notes,
        "priority": priority,
        "inclusion_status": inclusion_status,
        "notes": notes,
    }


def parse_year(value: int | str, default: int) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text in {"present", "current", "ongoing"}:
        return 2026
    if text.startswith("pre-"):
        return int(text.replace("pre-", ""))
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 4:
        return int(digits[:4])
    return default


def period_bands(start: int | str, end: int | str) -> str:
    s = parse_year(start, 1830)
    e = parse_year(end, 2026)
    bands = []
    if s <= 1930 and e >= 1830:
        bands.append("1830-1930")
    if s <= 1970 and e >= 1931:
        bands.append("1931-1970")
    if s <= 2000 and e >= 1971:
        bands.append("1971-2000")
    if s <= 2026 and e >= 2001:
        bands.append("2001-2026")
    return "; ".join(bands)


def build_candidates() -> list[dict[str, str]]:
    candidates = [
        # Global routers and scholarly discovery layers.
        row("World Digital Library", "Global", "global aggregator", "Global", "cultural heritage aggregator", "international", "API/HTML", "https://www.wdl.org/", 1830, 1930, "books; maps; manuscripts; photographs; print culture", "metadata-first discovery", "global_router_adapter", "IMG00 until item rights verified; IMG02 if source viewer exists", "source description; catalog metadata", "link-only default", "closed WDL legacy pages may require source-return links", "P1"),
        row("Getty Research Portal", "Global", "global art history", "Global", "research portal", "institutional", "API/HTML", "https://portal.getty.edu/", 1830, 2026, "books; catalogues; design texts", "metadata and bibliography mining", "bibliography_adapter", "IMG04 for text-led records", "catalog text; bibliography; OCR where available", "text-first", "book scans may have mixed rights", "P2"),
        row("HathiTrust Digital Library", "Global", "global books", "Global", "digital library", "consortium", "OAI/API/HTML", "https://www.hathitrust.org/", 1830, 1930, "books; catalogues; periodicals", "bibliographic source discovery", "oai_or_bibliographic_adapter", "IMG04 or IMG02 depending on record type", "MARC; catalog notes; OCR snippets", "text-first", "full-text access varies by location and rights", "P2"),
        row("Internet Archive", "Global", "global books and web", "Global", "digital library", "nonprofit", "API/IIIF/metadata", "https://archive.org/", 1830, 2026, "books; magazines; posters; web snapshots", "metadata and source-return discovery", "internet_archive_adapter", "IMG02 for viewer; IMG03 only if explicit license", "metadata; OCR; item descriptions", "viewer-first", "archive metadata is evidence but not blanket rights clearance", "P1"),
        row("OpenAlex", "Global", "scholarly graph", "Global", "scholarly metadata graph", "nonprofit", "API", "https://openalex.org/", 1900, 2026, "articles; dissertations; citation leads", "academic citation mining", "academic_graph_adapter", "IMG04", "abstracts; citations; institution names", "text-only", "citation mentions are leads, not object evidence", "P1"),
        row("BASE Search", "Global", "open repositories", "Global", "scholarly repository aggregator", "institutional", "API/OAI-PMH", "https://www.base-search.net/", 1900, 2026, "theses; articles; repository records", "repository discovery", "oai_router_adapter", "IMG04 by default", "abstracts; repository metadata", "text-only", "repository licensing varies", "P2"),
        row("ISIDORE", "Global", "francophone humanities", "France; North Africa; Middle East", "humanities discovery platform", "institutional", "API/RDF", "https://isidore.science/", 1900, 2026, "articles; archives; humanities metadata", "francophone source discovery", "rdf_api_adapter", "IMG04", "abstracts; keywords; source links", "text-only", "good for leads, not direct object display", "P2"),
        row("WorldCat and ArchiveGrid", "Global", "collection finding aids", "Global", "library and archive discovery", "consortium", "API/HTML", "https://researchworks.oclc.org/archivegrid/", 1830, 2026, "finding aids; collection-level records", "source and collection discovery", "finding_aid_adapter", "IMG04 or IMG00 for collection leads", "finding aid text; holding institution", "collection-level", "often collection-level only; may not expose item records", "P1"),
        row("Zotero Public Group Libraries", "Global", "scholarly bibliography", "Global", "public bibliography network", "community", "API/HTML", "https://www.zotero.org/groups", 1900, 2026, "bibliographies; source URLs; research leads", "research bibliography mining", "bibliography_adapter", "IMG04", "bibliographic notes; tags; source links", "text-only", "public group quality varies", "P3"),
        # East Asia and China.
        row("China International Design Museum", "Asia", "East Asia", "China", "design museum archive", "museum", "HTML/manual", "https://cdm.caa.edu.cn/#/archive/consult", 1830, 2026, "design books; special collections; Soviet avant-garde; ephemera", "source registry and manual request", "manual_source_adapter", "IMG00 unless source grants viewer/open license", "collection descriptions; consultation notes", "manual-review", "many holdings require onsite consultation", "P1"),
        row("CADAL", "Asia", "East Asia", "China", "university digital library", "consortium", "HTML/SSO/OAI possible", "https://www.cadal.edu.cn/", 1830, 1949, "periodicals; books; Republican-era print culture", "institutional-access metadata discovery", "manual_or_oai_adapter", "IMG00/IMG04 until terms reviewed", "catalog metadata; OCR if accessible", "access-restricted", "institution login required; no credential storage", "P1"),
        row("National Library of China", "Asia", "East Asia", "China", "national library", "national", "HTML/catalog", "https://www.nlc.cn/", 1830, 2026, "books; newspapers; periodicals; posters", "catalog and newspaper index discovery", "bibliographic_adapter", "IMG04 or IMG00 until item review", "catalog records; subject headings", "link-only default", "digital access varies", "P2"),
        row("National Newspaper and Periodical Index", "Asia", "East Asia", "China", "newspaper and periodical database", "institutional", "database/manual", "https://www.cnbksy.com/", 1830, 1949, "newspaper advertising; periodical layouts; print culture", "manual or institutional-access discovery", "manual_database_adapter", "IMG04 metadata-only unless source terms permit", "article metadata; OCR text if licensed", "access-restricted", "subscription access; no scraping behind auth", "P2"),
        row("M+ Collections", "Asia", "East Asia", "Hong Kong", "visual culture museum", "museum", "API/HTML", "https://www.mplus.org.hk/en/collection/", 1950, 2026, "graphic design; posters; visual culture records", "API/HTML metadata capture", "museum_api_adapter", "IMG02/IMG00 until rights reviewed", "object description; exhibition text", "source-hosted review", "image terms vary per object", "P1"),
        row("National Diet Library Digital Collections", "Asia", "East Asia", "Japan", "national library", "national", "API/HTML/IIIF", "https://dl.ndl.go.jp/", 1830, 2026, "books; magazines; posters; bibliographic records", "catalog and viewer-source capture", "ndl_adapter", "IMG02 if viewer; IMG04 for bibliographic records", "catalog metadata; OCR where exposed", "source-hosted review", "many items are viewer-only or bibliographic", "P1"),
        row("DNP Graphic Design Archives", "Asia", "East Asia", "Japan", "design archive", "private/institutional", "HTML", "https://www.dnpfcp.jp/gallery/ddd/", 1910, 2026, "graphic design records; exhibitions", "source registry and exhibition discovery", "html_metadata_adapter", "IMG00/IMG02 until terms reviewed", "exhibition text; designer metadata", "rights-sensitive", "specialized archive with source-return requirement", "P1"),
        row("Waseda University Library", "Asia", "East Asia", "Japan", "university library", "university", "IIIF/HTML/catalog", "https://www.waseda.jp/library/", 1890, 2026, "magazines; theatre ephemera; print culture", "university catalog discovery", "iiif_or_catalog_adapter", "IMG02 if IIIF; IMG03 only explicit open", "catalog metadata; OCR where available", "source-hosted review", "mixed collections and rights", "P2"),
        row("Tokyo ADC", "Asia", "East Asia", "Japan", "professional design association", "professional body", "HTML", "https://www.tokyoadc.com/", 1952, 2026, "award records; designer network; annuals", "source registry and context capture", "source_registry_context_adapter", "IMG04 unless record image terms are clear", "institutional overview; award metadata", "context-source", "association pages are source evidence, not object-level holdings", "P1"),
        row("Tokyo TDC", "Asia", "East Asia", "Japan", "professional typography association", "professional body", "HTML", "https://tokyotypedirectorsclub.org/", 1987, 2026, "typography awards; exhibition records", "source registry and context capture", "source_registry_context_adapter", "IMG04 unless source terms permit images", "event text; award metadata", "context-source", "avoid treating awards as source image permission", "P1"),
        row("JAGDA", "Asia", "East Asia", "Japan", "professional design association", "professional body", "HTML", "https://www.jagda.or.jp/", 1978, 2026, "designer network; events; publications", "source registry and context capture", "source_registry_context_adapter", "IMG04 source context", "institution text; events; publications", "context-source", "not an object archive by default", "P2"),
        row("Ginza Graphic Gallery", "Asia", "East Asia", "Japan", "design gallery", "gallery", "HTML", "https://www.dnpfcp.jp/gallery/ggg/", 1986, 2026, "exhibition records; designers; catalogues", "exhibition metadata capture", "html_metadata_adapter", "IMG00/IMG04 unless image rights clear", "exhibition notes; designer metadata", "rights-sensitive", "gallery images need source-term review", "P1"),
        row("National Central Library Taiwan", "Asia", "East Asia", "Taiwan", "national library", "national", "catalog/HTML", "https://www.ncl.edu.tw/", 1895, 2026, "Japanese colonial print; periodicals; books", "catalog discovery", "bibliographic_adapter", "IMG04/IMG02 depending on digital viewer", "catalog metadata; subject headings", "source-hosted review", "viewer access varies", "P2"),
        row("Korean Design Archive", "Asia", "East Asia", "Korea", "design archive", "institutional", "HTML", "https://www.kidp.or.kr/", 1950, 2026, "design records; institutions; awards", "source registry and metadata discovery", "html_metadata_adapter", "IMG00/IMG04 until terms reviewed", "institutional text; object metadata where exposed", "rights-sensitive", "requires Korean-language review", "P2"),
        # South and Southeast Asia.
        row("CIViC Archive", "Asia", "South Asia", "India", "visual culture archive", "community/research", "HTML", "https://civicarchives.org/", 1850, 2026, "popular visual culture; calendars; advertisements", "metadata and collection discovery", "html_metadata_adapter", "IMG00/IMG02 until explicit terms", "item descriptions; collection text", "rights-sensitive", "fragile print culture; confirm permissions carefully", "P1"),
        row("Priya Paul Collection", "Asia", "South Asia", "India", "popular art collection", "private/research", "Google Arts/HTML", "https://artsandculture.google.com/", 1880, 2026, "posters; calendar art; advertisements", "collection discovery via source pages", "source_hosted_adapter", "IMG02/source-viewer unless open evidence", "collection notes; object metadata", "source-hosted review", "platform images are not local reuse permission", "P1"),
        row("Tasveer Ghar", "Asia", "South Asia", "South Asia", "visual culture research network", "research/community", "HTML", "https://tasveerghar.net/", 1850, 2026, "essays; popular images; calendars; print culture", "essay and source discovery", "text_enrichment_adapter", "IMG04/IMG00 unless source page rights clear", "scholarly essays; bibliographies", "text-rich review", "excellent for context, not always object-level rights", "P1"),
        row("Design Dashtahjaat", "Asia", "South Asia", "Pakistan", "design archive", "independent/community", "HTML", "https://designdashtahjaat.com/", 1947, 2026, "Urdu typography; posters; design history", "source registry and metadata discovery", "html_metadata_adapter", "IMG00 until source terms clear", "local-language descriptions; source pages", "rights-sensitive", "community archive; preserve source return", "P1"),
        row("SADAA", "Asia", "South Asia diaspora", "South Asia diaspora", "diaspora arts archive", "nonprofit", "HTML", "https://www.sadaa.org/", 1950, 2026, "artists; ephemera; diaspora records", "source registry and context capture", "html_metadata_adapter", "IMG00/IMG04 until item rights clear", "artist bios; item notes", "community-review", "diaspora context source, not automatic image source", "P2"),
        row("ASEAN Digital Library", "Asia", "Southeast Asia", "ASEAN", "national library aggregator", "consortium", "API/HTML", "https://www.aseanlibrary.org/", 1830, 2026, "books; manuscripts; posters; newspapers; cultural records", "regional aggregator discovery", "regional_library_adapter", "IMG02/IMG04 until item terms reviewed", "catalog metadata; national library links", "source-hosted review", "country-level source return required", "P1"),
        row("National Library Board Singapore", "Asia", "Southeast Asia", "Singapore", "national library", "national", "API/HTML", "https://www.nlb.gov.sg/", 1830, 2026, "newspapers; ephemera; design publications", "catalog and newspaper discovery", "library_api_adapter", "IMG02/IMG04 depending on viewer", "catalog metadata; newspaper OCR", "source-hosted review", "terms vary by collection", "P1"),
        row("Malaysian Design Archive", "Asia", "Southeast Asia", "Malaysia", "design archive", "independent/research", "HTML", "https://www.malaysiadesignarchive.org/", 1957, 2026, "Malaysian graphic design; social design; print culture", "metadata and context capture", "html_metadata_adapter", "IMG00 until source terms reviewed", "archive essays; item descriptions", "community-review", "anti-colonial context source; avoid flattening interpretation", "P1"),
        row("Indonesia Design Archive", "Asia", "Southeast Asia", "Indonesia", "design archive", "independent/community", "HTML", "https://www.indonesiadesignarchive.com/", 1945, 2026, "Indonesian graphic design; posters; identity", "source discovery and metadata capture", "html_metadata_adapter", "IMG00 until source terms reviewed", "descriptions; event notes", "community-review", "site structure may be fragile", "P1"),
        row("Vietnam National Library", "Asia", "Southeast Asia", "Vietnam", "national library", "national", "catalog/HTML", "https://nlv.gov.vn/", 1900, 2026, "periodicals; books; print culture", "catalog discovery", "bibliographic_adapter", "IMG04/IMG02 if viewer available", "catalog metadata; subject headings", "source-hosted review", "Vietnamese-language metadata", "P2"),
        row("Thai Graphic Design Century", "Asia", "Southeast Asia", "Thailand", "research publication/source index", "research/community", "book/HTML", "https://readthecloud.co/thaigraphicdesign/", 1850, 1970, "Thai print culture; posters; commercial graphics", "source-bibliography discovery", "manual_bibliography_adapter", "IMG04/IMG00 unless linked item rights clear", "publication text; source references", "text-rich review", "publication-led source, not an object API", "P1"),
        row("Perpusnas Indonesia", "Asia", "Southeast Asia", "Indonesia", "national library", "national", "catalog/HTML", "https://www.perpusnas.go.id/", 1900, 2026, "periodicals; books; newspapers", "catalog discovery", "bibliographic_adapter", "IMG04/IMG02 if viewer available", "catalog metadata; OCR where exposed", "source-hosted review", "Indonesian-language review needed", "P2"),
        # Latin America and Caribbean.
        row("Fundacion IDA", "Latin America", "Southern Cone", "Argentina", "design archive", "nonprofit", "CollectiveAccess/HTML", "https://www.fundacionida.org/", 1920, 2026, "industrial and graphic design; designers; objects", "CollectiveAccess-style metadata capture", "collectiveaccess_adapter", "IMG00/IMG02 until terms reviewed", "object metadata; collection essays", "rights-sensitive", "strong regional source; item rights vary", "P1"),
        row("Diseno Nacional", "Latin America", "Southern Cone", "Chile", "graphic archive", "independent/research", "HTML", "https://www.disenonacional.cl/", 1840, 2000, "posters; publications; ads; brands; symbols; illustration", "HTML metadata capture", "html_metadata_adapter", "IMG00/IMG02 until terms reviewed", "item descriptions; tags", "rights-sensitive", "high-value Chilean source; verify image terms", "P1"),
        row("Grafica Latina", "Latin America", "regional", "Latin America", "poster archive", "community/research", "HTML", "https://www.graficalatina.com/", 1950, 2026, "posters; Latin American and Latinx graphics", "metadata and source-return discovery", "html_metadata_adapter", "IMG00 until source terms clear", "poster descriptions; designer names", "community-review", "poster images often rights-sensitive", "P1"),
        row("Archivo de Ilustracion Argentina", "Latin America", "Southern Cone", "Argentina", "illustration archive", "independent/research", "HTML", "https://ilustracion.fadu.uba.ar/", 1830, 2026, "illustration; books; magazines; posters; advertising", "metadata and essay capture", "html_metadata_adapter", "IMG00 until rights verified", "archive essays; item metadata", "rights-sensitive", "good for pre-1930 and modern transitions", "P1"),
        row("ICAA Documents Project", "Latin America", "regional", "Latin America", "art documents archive", "research institution", "HTML/API", "https://icaa.mfah.org/", 1900, 2026, "documents; essays; artist writings", "document and context capture", "text_enrichment_adapter", "IMG04", "primary texts; documents; citations", "text-first", "art context, not always graphic design objects", "P2"),
        row("Princeton Latin American and Caribbean Ephemera", "Latin America", "Caribbean and Latin America", "Latin America/Caribbean", "special collection", "university", "Figgy/IIIF/HTML", "https://dpul.princeton.edu/lae", 1900, 2026, "ephemera; flyers; posters; political print", "IIIF/source viewer capture", "figgy_iiif_adapter", "IMG02; IMG03 only explicit open", "collection metadata; OCR where available", "source-hosted review", "copyright and cultural sensitivity vary", "P1"),
        row("La Patria Uruguay", "Latin America", "Southern Cone", "Uruguay", "graphic archive", "independent", "HTML", "https://lapatria.uy/", 1900, 2026, "posters; logos; print; graphic design", "metadata and source discovery", "html_metadata_adapter", "IMG00 until rights terms reviewed", "item text; tags; essays", "rights-sensitive", "edge regional archive", "P1"),
        row("Arquivo ESDI", "Latin America", "Brazil", "Brazil", "school archive", "university", "HTML/manual", "https://www.esdi.uerj.br/", 1960, 2026, "design school history; course material; print", "manual source registry", "manual_source_adapter", "IMG00/IMG04 until digitization terms clear", "institutional history; collection notes", "manual-review", "digitization status incomplete", "P2"),
        row("Hemeroteca Digital Brasileira", "Latin America", "Brazil", "Brazil", "newspaper and periodical portal", "national", "OCR/HTML", "https://bndigital.bn.gov.br/hemeroteca-digital/", 1830, 2026, "newspapers; ads; magazine layouts", "OCR and source-link discovery", "newspaper_ocr_adapter", "IMG02/IMG04 until viewer terms reviewed", "OCR snippets; bibliographic metadata", "source-hosted review", "page images require rights/source review", "P1"),
        row("Hemeroteca Nacional Digital de Mexico", "Latin America", "Mexico", "Mexico", "newspaper portal", "national", "OCR/HTML", "https://www.hndm.unam.mx/", 1830, 2026, "newspapers; ads; magazine layouts", "OCR and source-link discovery", "newspaper_ocr_adapter", "IMG02/IMG04 until viewer terms reviewed", "OCR snippets; bibliographic metadata", "source-hosted review", "important for early commercial print", "P1"),
        # Middle East, North Africa, and West Asia.
        row("Arabic Design Archive", "Middle East and North Africa", "Arab world", "Arab world", "design archive", "independent/community", "HTML", "https://arabicdesignarchive.com/", 1900, 2026, "Arab graphic design; typography; posters; identities", "metadata and source-return discovery", "html_metadata_adapter", "IMG00 until source terms reviewed", "item text; designer names; essays", "community-review", "community archive; do not flatten regional context", "P1"),
        row("Syrian Design Archive", "Middle East and North Africa", "Levant", "Syria", "design archive", "independent/community", "HTML", "https://syriandesignarchive.com/", 1900, 2026, "Syrian print and graphic design", "metadata and context capture", "html_metadata_adapter", "IMG00 until rights reviewed", "item descriptions; archive statements", "community-review", "conflict and cultural sensitivity review required", "P1"),
        row("Archival Alliance", "Middle East and North Africa", "Arab world", "Arab world", "archive network", "network/community", "manual/network", "https://arabicdesignarchive.com/archival-alliance/", 1900, 2026, "partner archive leads; regional source registry", "cooperative source discovery", "manual_network_adapter", "IMG04 source registry only", "source descriptions; contacts; scope notes", "manual-cooperation", "contact-based; no automated extraction without agreement", "P2"),
        row("Qatar Digital Library", "Middle East and North Africa", "Gulf", "Qatar/Middle East", "digital library", "national/institutional", "IIIF/HTML", "https://www.qdl.qa/", 1830, 2026, "maps; manuscripts; photographs; print culture", "source-viewer metadata capture", "iiif_or_html_adapter", "IMG02/IMG04 until item rights verified", "metadata; essays; item descriptions", "source-hosted review", "not graphic-design-specific but strong regional context", "P2"),
        row("SALT Research", "Middle East and North Africa", "Anatolia", "Turkey", "research archive", "institutional", "HTML", "https://archives.saltresearch.org/", 1900, 2026, "architecture; design; exhibition; print culture", "archive metadata capture", "html_metadata_adapter", "IMG00/IMG02 until terms reviewed", "finding aids; object metadata", "rights-sensitive", "strong for Turkey and regional modernisms", "P1"),
        row("Dar al-Kutub", "Middle East and North Africa", "North Africa", "Egypt", "national library", "national", "catalog/manual", "https://www.darelkotob.gov.eg/", 1830, 2026, "books; periodicals; manuscripts; print culture", "catalog and manual source discovery", "manual_bibliographic_adapter", "IMG04/IMG00 until source terms verified", "catalog metadata; collection notes", "manual-review", "limited digital access; Arabic-language review needed", "P3"),
        row("Palestinian Museum Digital Archive", "Middle East and North Africa", "Levant", "Palestine", "community and museum archive", "museum/community", "HTML/API possible", "https://palarchive.org/", 1900, 2026, "posters; photographs; documents; ephemera", "metadata and protocol-sensitive source capture", "html_metadata_adapter", "IMG00/IMG02 until terms reviewed", "item metadata; collection context", "protocol-sensitive", "cultural sensitivity and source-return required", "P1"),
        row("Arab Image Foundation", "Middle East and North Africa", "Levant", "Arab world", "photography archive", "nonprofit", "HTML", "https://arabimagefoundation.org/", 1900, 2026, "photography; visual culture; printed ephemera leads", "context and visual culture discovery", "html_metadata_adapter", "IMG00 until terms reviewed", "collection text; photographer metadata", "rights-sensitive", "not graphic-design-specific; useful for visual culture context", "P2"),
        # Africa.
        row("ArchiveAfrica", "Africa", "Pan-African", "Africa", "visual archive", "community/nonprofit", "social+repository/manual", "https://www.instagram.com/archiveafrica_/", 1800, 2026, "visual culture; photographs; documents; ephemera", "cooperative source discovery", "manual_social_source_adapter", "IMG00 unless formal source terms supplied", "account descriptions; partner notes; repository metadata if available", "community-review", "social platform is discovery lead, not image permission", "P1"),
        row("Africa Commons", "Africa", "Pan-African", "Africa", "digital archive platform", "commercial/institutional", "database", "https://www.coherentdigital.net/africacommons", 1800, 2026, "documents; images; archives; periodicals", "subscription-source assessment", "manual_database_adapter", "IMG04/IMG00 unless licensed access permits", "collection descriptions; metadata exports if licensed", "access-restricted", "institutional subscription needed; no credential capture", "P2"),
        row("Frobenius Institute Digital Collections", "Africa", "Pan-African", "Africa/Oceania", "ethnographic archive", "research institute", "HTML/database", "https://sammlungen.frobenius-institut.de/", 1850, 1950, "drawings; photographs; architectural drawings; visual records", "metadata and source-viewer discovery", "html_metadata_adapter", "IMG02/IMG00 until rights reviewed", "object metadata; collection notes", "source-hosted review", "contextual sensitivity review required", "P2"),
        row("Ross Archive of African Images", "Africa", "Pan-African", "Africa", "image research archive", "university", "HTML", "https://raai.library.yale.edu/", 1590, 1920, "published images; African art in print", "metadata and bibliography discovery", "html_metadata_adapter", "IMG04/IMG02 depending on page", "bibliographic metadata; source publication", "text/source-hosted", "image reuse depends on original publication status", "P2"),
        row("CORAA African Archive Network", "Africa", "Pan-African", "Africa", "archive map/network", "network/community", "HTML/map", "https://coraa.org/", 1900, 2026, "archive network leads; institutions", "source registry discovery", "network_map_adapter", "IMG04 source registry", "institution names; scope notes; map metadata", "discovery-only", "map records are leads, not object evidence", "P2"),
        row("African Activist Archive", "Africa", "Southern Africa and diaspora", "Africa/United States", "activist archive", "university/community", "HTML", "https://africanactivist.msu.edu/", 1950, 2000, "posters; leaflets; campaign graphics; documents", "metadata and source-viewer capture", "html_metadata_adapter", "IMG02/IMG00 until terms reviewed", "item metadata; movement context", "rights-sensitive", "political and cultural sensitivity review required", "P1"),
        row("SAHA", "Africa", "Southern Africa", "South Africa", "history archive", "nonprofit", "HTML", "https://www.saha.org.za/", 1950, 2026, "posters; activist print; documents", "metadata and finding aid capture", "html_metadata_adapter", "IMG00/IMG02 until terms reviewed", "finding aids; item descriptions", "rights-sensitive", "activist archive; source-return required", "P2"),
        row("Nelson Mandela Foundation Archive", "Africa", "Southern Africa", "South Africa", "foundation archive", "foundation", "HTML", "https://www.nelsonmandela.org/", 1950, 2026, "campaign materials; public communication; archival documents", "source registry and context capture", "html_metadata_adapter", "IMG04/IMG00 until object rights reviewed", "archive context; institutional notes", "rights-sensitive", "mostly contextual for graphic communication", "P3"),
        # Europe beyond dominant Western museum frame.
        row("Graphic Front", "Europe", "Eastern Europe", "Romania", "graphic design archive", "independent/community", "HTML", "https://www.graphicfront.ro/", 1900, 2026, "advertising; posters; stamps; logos; print", "HTML metadata capture", "html_metadata_adapter", "IMG00 until rights reviewed", "item text; tags; source notes", "rights-sensitive", "important Eastern European source", "P1"),
        row("SCOMUS", "Europe", "Eastern Europe", "Bulgaria", "socialist graphic archive", "independent/community", "HTML", "https://scomus.com/", 1944, 1989, "socialist graphic design; posters; packaging; symbols", "metadata and source capture", "html_metadata_adapter", "IMG00 until rights reviewed", "item descriptions; period context", "rights-sensitive", "non-western Europe socialist context", "P1"),
        row("Kramerius Czech Digital Library", "Europe", "Central/Eastern Europe", "Czech Republic/Slovakia", "digital library protocol family", "national/university", "Kramerius/API/IIIF/OAI", "https://www.digitalniknihovna.cz/", 1830, 2026, "newspapers; periodicals; posters; books; OCR", "protocol-family adapter", "kramerius_adapter", "IMG02 if viewer; IMG04 for OCR/catalog", "OCR; bibliographic records; IIIF manifests", "source-hosted review", "adapter family can cover many local repositories", "P1"),
        row("POLONA", "Europe", "Central/Eastern Europe", "Poland", "national digital library", "national", "API/IIIF/HTML", "https://polona.pl/", 1830, 2026, "posters; magazines; books; print culture", "API/IIIF source capture", "polona_adapter", "IMG02/IMG03 only if explicit open", "metadata; OCR; source links", "source-hosted review", "rich image source but rights vary", "P1"),
        row("e-rara", "Europe", "Central Europe", "Switzerland", "rare books portal", "consortium", "IIIF/HTML", "https://www.e-rara.ch/", 1830, 1930, "books; type specimens; printed material", "IIIF/bibliographic capture", "iiif_or_bibliographic_adapter", "IMG02/IMG03 only with item rights", "metadata; scans; OCR", "source-hosted review", "good for pre-modern and early print context", "P2"),
        # Oceania and Indigenous contexts.
        row("AIATSIS Collections", "Oceania", "Australia/Indigenous", "Australia", "Indigenous collections archive", "national/research", "catalog/HTML", "https://aiatsis.gov.au/collection", 1900, 2026, "posters; community print; documents; photographs", "protocol-sensitive catalog capture", "catalog_adapter", "IMG00/IMG04 until cultural and rights review", "catalog metadata; cultural notices", "protocol-sensitive", "Indigenous cultural protocol review required", "P1"),
        row("Trove", "Oceania", "Australia", "Australia", "national library aggregator", "national", "API/OCR/HTML", "https://trove.nla.gov.au/", 1830, 2026, "newspapers; posters; books; ephemera", "API and OCR source discovery", "trove_adapter", "IMG02/IMG04 until rights reviewed", "OCR; catalog metadata; source links", "source-hosted review", "good for print culture and ads", "P1"),
        row("DigitalNZ", "Oceania", "New Zealand", "New Zealand", "cultural aggregator", "national", "API/HTML", "https://digitalnz.org/", 1830, 2026, "posters; photographs; ephemera; books", "API metadata capture", "digitalnz_adapter", "IMG02/IMG03 only if item rights explicit", "metadata; partner source links", "source-hosted review", "partner-level rights vary", "P1"),
        row("NAIDOC Poster Collections", "Oceania", "Australia/Indigenous", "Australia", "poster and cultural collection", "government/community", "HTML/manual", "https://www.naidoc.org.au/", 1970, 2026, "posters; campaign graphics; public communication", "source registry and protocol review", "manual_source_adapter", "IMG00 until cultural and rights review", "event context; poster metadata", "protocol-sensitive", "rights and cultural protocol review required", "P1"),
        # Contemporary independent and platform discovery.
        row("Another Graphic", "Global", "contemporary independent", "Global", "independent design archive/publication", "independent", "HTML", "https://anothergraphic.org/", 1990, 2026, "contemporary graphic design; projects; essays", "metadata and source-return capture", "html_metadata_adapter", "IMG00/IMG02 until terms reviewed", "project text; designer metadata", "rights-sensitive", "good contemporary edge source; do not copy project images by default", "P1"),
        row("Design Reviewed", "Global", "independent archive", "Global", "independent design archive", "independent", "WordPress/API/HTML", "https://designreviewed.com/", 1900, 2026, "graphic design history; posters; identities; ephemera", "WordPress metadata capture", "wordpress_adapter", "IMG00/IMG02 until terms reviewed", "post text; tags; source notes", "rights-sensitive", "existing source family; image duplicates need dedupe", "P1"),
        row("Letterform Archive", "North America", "typography archive", "United States/global", "typography archive", "nonprofit", "WordPress/API/HTML", "https://letterformarchive.org/", 1800, 2026, "typography; posters; specimens; essays", "WordPress metadata and essay capture", "wordpress_adapter", "IMG00/IMG02 until terms reviewed", "essay text; metadata; tags", "rights-sensitive", "strong text enrichment source", "P1"),
        row("Fonts In Use", "Global", "typography database", "Global", "typography database", "independent", "HTML", "https://fontsinuse.com/", 1900, 2026, "typographic examples; credits; tags", "metadata and relation discovery", "html_metadata_adapter", "IMG00 until source terms reviewed", "credits; typeface metadata; usage notes", "rights-sensitive", "excellent relation source, image rights vary", "P2"),
        row("Are.na", "Global", "social research boards", "Global", "social bookmarking platform", "platform/community", "API/HTML", "https://www.are.na/", 1990, 2026, "research boards; links; image leads", "discovery-only board mining", "social_discovery_adapter", "IMG00 discovery only", "channel descriptions; source URLs", "discovery-only", "platform aggregation is not source evidence", "P3"),
        row("Pinterest", "Global", "social image discovery", "Global", "social platform", "platform", "API/HTML", "https://www.pinterest.com/", 1990, 2026, "pins; source links; boards", "discovery-only source lead extraction", "social_discovery_adapter", "IMG00 discovery only", "pin title; outbound source URL; board context", "discovery-only", "do not store images or treat pins as rights evidence", "P3"),
        row("Behance", "Global", "portfolio platform", "Global", "portfolio platform", "platform", "API/HTML", "https://www.behance.net/", 2005, 2026, "portfolio projects; designers; process text", "metadata-only project discovery", "platform_metadata_adapter", "IMG00 unless creator/source terms explicitly reviewed", "project text; creator metadata; tags", "rights-sensitive", "portfolio images remain creator-controlled", "P3"),
        row("Cargo Sites", "Global", "independent websites", "Global", "website platform", "platform", "HTML", "https://cargo.site/", 1990, 2026, "portfolio projects; independent archives", "seeded site discovery only", "html_metadata_adapter", "IMG00 unless site-level terms reviewed", "page text; project metadata", "rights-sensitive", "site-specific structure; no broad crawler without seeds", "P3"),
        row("Tumblr", "Global", "legacy social web", "Global", "blog platform", "platform", "API/HTML", "https://www.tumblr.com/", 2007, 2026, "blogs; repost networks; image leads", "discovery-only source lead extraction", "social_discovery_adapter", "IMG00 discovery only", "post captions; tags; outbound links", "discovery-only", "repost provenance is weak; use only as lead", "P3"),
        row("Instagram public accounts", "Global", "social archive leads", "Global", "social platform", "platform/community", "manual/API if approved", "https://www.instagram.com/", 2010, 2026, "community archives; collector leads; event posts", "manual discovery and contact leads", "manual_social_source_adapter", "IMG00 discovery only", "profile bios; public captions; source leads", "discovery-only", "platform access and image rights are high risk", "P3"),
        row("Reddit design communities", "Global", "community discussion", "Global", "discussion platform", "community", "JSON/HTML", "https://www.reddit.com/", 2005, 2026, "archive mentions; source recommendations", "discovery-only link mining", "social_discovery_adapter", "IMG04/IMG00 discovery only", "discussion text; outbound links", "discovery-only", "community comments are leads, not evidence", "P4"),
    ]

    for idx, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = f"GED{idx:04d}"
    return candidates


def metric_rows(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    total = len(candidates)
    macro = Counter(c["macro_region"] for c in candidates)
    protocols = Counter()
    bands = Counter()
    priorities = Counter(c["priority"] for c in candidates)
    policies = Counter(c["recommended_image_policy"] for c in candidates)
    risk = Counter(c["rights_posture"] for c in candidates)
    adapters = Counter(c["recommended_adapter"] for c in candidates)
    status = Counter(c["inclusion_status"] for c in candidates)
    for candidate in candidates:
        for part in candidate["protocol_family"].split("/"):
            protocols[part.strip()] += 1
        for band in candidate["period_bands"].split("; "):
            if band:
                bands[band] += 1

    non_us_western_europe = sum(
        1
        for c in candidates
        if c["macro_region"] not in {"North America", "Europe"}
        or c["subregion"] in {"Eastern Europe", "Central/Eastern Europe"}
    )
    discovery_only = sum(1 for c in candidates if "discovery-only" in c["rights_posture"])
    manual_or_access = sum(
        1
        for c in candidates
        if any(
            token in f"{c['capture_route']} {c['recommended_adapter']} {c['rights_posture']}".lower()
            for token in ["manual", "access-restricted", "cooperative"]
        )
    )

    rows = [
        {"metric": "total_candidates", "value": str(total), "notes": "Global edge-source candidates generated in this pass."},
        {
            "metric": "non_us_western_europe_candidates",
            "value": f"{non_us_western_europe}/{total} ({non_us_western_europe / total:.1%})",
            "notes": "Counts candidates outside North America and dominant Western/Central Europe; Eastern/Central Europe is counted as edge coverage.",
        },
        {
            "metric": "manual_or_access_restricted_candidates",
            "value": f"{manual_or_access}/{total} ({manual_or_access / total:.1%})",
            "notes": "Requires source contact, institutional access, protocol review, or manual handling.",
        },
        {
            "metric": "discovery_only_candidates",
            "value": f"{discovery_only}/{total} ({discovery_only / total:.1%})",
            "notes": "Can generate leads but not object-level evidence or image permission.",
        },
    ]

    def extend_counter(prefix: str, counter: Counter[str], note: str) -> None:
        for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
            rows.append({"metric": f"{prefix}:{key}", "value": str(value), "notes": note})

    extend_counter("macro_region", macro, "Candidate distribution by macro-region.")
    extend_counter("protocol_family", protocols, "Protocol/discovery families that can become adapter queues.")
    extend_counter("period_band", bands, "Candidates that can support each chronological capture band.")
    extend_counter("priority", priorities, "Capture planning priority.")
    extend_counter("image_policy", policies, "Recommended initial image policy before item-level rights review.")
    extend_counter("rights_posture", risk, "Rights and review posture.")
    extend_counter("adapter", adapters, "Suggested adapter family.")
    extend_counter("status", status, "Inclusion state.")
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def report_text(candidates: list[dict[str, str]], metrics: list[dict[str, str]]) -> str:
    macro = Counter(c["macro_region"] for c in candidates)
    priority = Counter(c["priority"] for c in candidates)
    adapters = Counter(c["recommended_adapter"] for c in candidates)
    p1 = [c for c in candidates if c["priority"] == "P1"]
    discovery_only = [c for c in candidates if "discovery-only" in c["rights_posture"]]

    lines = [
        "# Global Edge Discovery Strategy v1",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "This registry turns broad research notes into a conservative source-discovery layer.",
        "It is not an object ingest, not a rights clearance list, and not permission to",
        "download or republish source images. Every candidate still needs source review,",
        "rights review, field provenance, and citation review before publication use.",
        "",
        "## Safety boundary",
        "",
        "- No module may automatically upgrade image state to IMG01 or IMG03 from LLM,",
        "  visual analysis, ToS parsing, social-platform metadata, or similar-image search.",
        "- IIIF discovery can support IMG02 because it is a source-hosted display route,",
        "  not a local reuse claim.",
        "- Social platforms, Pinterest boards, portfolio platforms, and repost networks",
        "  are discovery leads only unless the original source is reviewed.",
        "- Proxy/geobypass and authenticated database scraping are excluded from production",
        "  automation. Those sources must remain manual or institutionally authorized.",
        "- Impact scores may rank review priority, but cannot decide historical inclusion",
        "  or image rights.",
        "",
        "## Test calculation",
        "",
    ]
    for metric in metrics[:4]:
        lines.append(f"- {metric['metric']}: {metric['value']} — {metric['notes']}")
    lines.extend(["", "### Macro-region coverage", ""])
    for key, value in sorted(macro.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "### Priority queue", ""])
    for key, value in sorted(priority.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "### Adapter families", ""])
    for key, value in adapters.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## P1 source directions", ""])
    by_region: dict[str, list[str]] = defaultdict(list)
    for candidate in p1:
        by_region[candidate["macro_region"]].append(candidate["source_name"])
    for region, names in sorted(by_region.items()):
        sample = "; ".join(names[:12])
        suffix = "" if len(names) <= 12 else f"; +{len(names) - 12} more"
        lines.append(f"- {region}: {sample}{suffix}")
    lines.extend(["", "## Discovery-only modules held behind review", ""])
    for candidate in discovery_only:
        lines.append(
            f"- {candidate['source_name']}: {candidate['risk_notes']} "
            f"Initial policy: {candidate['recommended_image_policy']}."
        )
    lines.extend(
        [
            "",
            "## Next implementation route",
            "",
            "1. Convert P1 protocol families into bounded adapter queues: IIIF/source viewer,",
            "   OAI/catalog, WordPress/HTML metadata, CollectiveAccess, newspaper/OCR, and",
            "   manual source-registry records.",
            "2. Use this registry to expand `source_prospect_registry_v2` after source checks,",
            "   not before.",
            "3. Run capture only against sources whose robots/terms and access route have been",
            "   reviewed. Store source links, metadata, citations, and rights evidence first.",
            "4. Treat platform crawlers as outbound-source discovery. They should not write",
            "   images, infer open licenses, or mint final object sheets on their own.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    candidates = build_candidates()
    metrics = metric_rows(candidates)
    write_csv(OUTPUT, candidates, FIELDNAMES)
    write_csv(METRICS, metrics, METRIC_FIELDS)
    DOCS.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(candidates, metrics), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(candidates)} candidates)")
    print(f"Wrote {METRICS.relative_to(ROOT)} ({len(metrics)} metric rows)")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
