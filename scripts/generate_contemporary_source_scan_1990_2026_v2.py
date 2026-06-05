#!/usr/bin/env python3
"""Generate a broader candidate source scan for 1990-2026 coverage.

This is a source-discovery list, not a publication-ready source registry.
Rows are intended for rights-safe source probing: index metadata and source
links first, never image possession unless authoritative IMG03 evidence exists.
"""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from generate_contemporary_source_scan_1990_2026_v1 import FIELDNAMES, build_rows, row


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "contemporary_source_scan_candidates_1990_2026_v2.csv"

DISCOVERY_NOTE = (
    "candidate source only; internal triage; not source partnership, rights "
    "clearance, or publication-ready authority"
)


def candidate(
    *,
    source_name: str,
    macro_region: str,
    subregion: str,
    country_or_scope: str,
    source_url: str,
    source_class: str,
    source_level: str,
    likely_protocol_family: str,
    priority: str = "P1",
    period_start: str = "1990",
    period_end: str = "2026",
    expected_record_types: str = "design objects; posters; publications; institutional records",
    expected_text_depth: str = "unknown",
    expected_image_policy: str = "IMG00_default_until_source_policy_review",
    discovery_route: str = "candidate_source_expansion_v2",
    adapter_hint: str = "html_source_probe_then_manual_rules",
    rights_risk: str = "unknown",
    language_scope: str = "mixed",
    notes: str = "",
):
    note = f"{DISCOVERY_NOTE}; {notes}".strip("; ")
    return row(
        source_name=source_name,
        macro_region=macro_region,
        subregion=subregion,
        country_or_region=country_or_scope,
        period_start=period_start,
        period_end=period_end,
        period_bands=f"{period_start}-{period_end}",
        url=source_url,
        source_class=source_class,
        institutional_level=source_level,
        protocol_family=likely_protocol_family,
        expected_record_types=expected_record_types,
        capture_route=discovery_route,
        recommended_adapter=adapter_hint,
        recommended_image_policy=expected_image_policy,
        text_enrichment_path=expected_text_depth,
        rights_posture="source_policy_unreviewed",
        risk_notes=f"{rights_risk}; language_scope={language_scope}",
        priority=priority,
        inclusion_status="candidate_probe_v2",
        notes=note,
    )


def canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def extra_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    global_sources = [
        ("World Digital Library / Library of Congress", "https://www.loc.gov/collections/world-digital-library/", "institutional aggregator", "JSON-LD / API"),
        ("Getty Research Portal", "https://portal.getty.edu/", "research portal", "Static JS App"),
        ("HathiTrust Digital Library", "https://www.hathitrust.org/", "library aggregator", "OAI-PMH / Metadata API"),
        ("Internet Archive Texts", "https://archive.org/details/texts", "library aggregator", "Metadata API"),
        ("OpenAlex", "https://openalex.org/", "scholarly metadata", "JSON API"),
        ("OpenBibArt", "https://openbibart.fr/", "scholarly bibliography", "Search interface"),
        ("DPLA", "https://dp.la/", "cultural heritage aggregator", "Metadata API"),
        ("ArchiveGrid", "https://researchworks.oclc.org/archivegrid/", "archive finding aid aggregator", "Search interface"),
        ("Zotero Public Groups", "https://www.zotero.org/groups/", "bibliographic community index", "HTML / RSS"),
    ]
    for name, url, source_class, protocol in global_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Global",
            subregion="Transregional",
            country_or_scope="Global",
            source_url=url,
            source_class=source_class,
            source_level="aggregator",
            likely_protocol_family=protocol,
            priority="P1",
            period_start="1830",
            period_end="2026",
            expected_record_types="books; ephemera; catalog records; bibliographic references",
            expected_text_depth="medium",
            adapter_hint="aggregator_probe_then_source_return",
            notes="broad source discovery for references and non-Western collection leads",
        ))

    independent_sources = [
        ("UnderConsideration Brand New", "https://www.underconsideration.com/brandnew/", "design media archive"),
        ("Design Observer", "https://designobserver.com/", "design criticism archive"),
        ("Walker Art Center Design", "https://walkerart.org/magazine/categories/design", "institutional design writing"),
        ("Typographica", "https://typographica.org/", "typography review archive"),
        ("Typewolf", "https://www.typewolf.com/", "typography reference"),
        ("Revue Faire", "https://www.revue-faire.eu/", "design criticism publication"),
        ("Alliance Graphique Internationale", "https://a-g-i.org/", "designer organization"),
        ("Graphic Design Festival Scotland", "https://graphicdesignfestivalscotland.com/", "festival archive"),
        ("Creative Review", "https://www.creativereview.co.uk/", "design media archive"),
        ("Eye Magazine", "https://www.eyemagazine.com/", "design magazine archive"),
        ("Design Week", "https://www.designweek.co.uk/", "design media archive"),
    ]
    for name, url, source_class in independent_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Global",
            subregion="Independent / media",
            country_or_scope="Transregional",
            source_url=url,
            source_class=source_class,
            source_level="independent_or_media",
            likely_protocol_family="RSS/Atom / HTML",
            priority="P2",
            expected_record_types="articles; projects; designer mentions; source leads",
            expected_text_depth="medium",
            expected_image_policy="IMG00_or_source_return_until_terms_review",
            rights_risk="medium",
            notes="post-1990 independent source discovery; use as source lead, not image mirror",
        ))

    china_sources = [
        ("China Design Museum", "https://cdm.caa.edu.cn/", "China", "institutional archive", "Static JS App", "P0"),
        ("National Library of China", "https://www.nlc.cn/", "China", "national library", "Search interface", "P1"),
        ("Shanghai Library", "https://www.library.sh.cn/", "China", "public library", "Search interface", "P1"),
        ("CADAL", "https://www.cadal.edu.cn/", "China", "university digital library", "Search interface", "P0"),
        ("CAFA Art Museum", "https://www.cafamuseum.org/", "China", "museum", "HTML", "P1"),
        ("National Central Library Taiwan", "https://www.ncl.edu.tw/", "Taiwan", "national library", "Search interface", "P1"),
        ("Academia Sinica Digital Resources", "https://digitalarchives.sinica.edu.tw/", "Taiwan", "research archive aggregator", "Search interface", "P1"),
    ]
    for name, url, country, cls, protocol, priority in china_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="East Asia",
            subregion="China / Taiwan / Hong Kong",
            country_or_scope=country,
            period_start="1830",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional",
            likely_protocol_family=protocol,
            priority=priority,
            expected_record_types="design records; books; periodicals; posters; exhibition records",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_IMG02_if_source_viewer",
            language_scope="zh / en",
            notes="priority East Asia source gap; source-return and bibliographic metadata first",
        ))

    japan_korea_sources = [
        ("NDL Search", "https://ndlsearch.ndl.go.jp/", "Japan", "national library search", "Search interface", "P0"),
        ("NDL Digital Collections", "https://dl.ndl.go.jp/", "Japan", "national digital library", "IIIF / Search interface", "P0"),
        ("National Museum of Modern Art Tokyo", "https://www.momat.go.jp/en/", "Japan", "museum", "HTML", "P1"),
        ("Musashino Art University Museum and Library", "https://mauml.musabi.ac.jp/", "Japan", "university museum/library", "Search interface", "P1"),
        ("Tama Art University Library", "https://www.tamabi.ac.jp/library/", "Japan", "university library", "Search interface", "P1"),
        ("National Archives of Korea", "https://www.archives.go.kr/", "Korea", "national archive", "Search interface", "P1"),
        ("MMCA Korea", "https://www.mmca.go.kr/", "Korea", "museum", "Search interface", "P1"),
        ("Seoul Museum of Art", "https://sema.seoul.go.kr/", "Korea", "museum", "Static JS App", "P1"),
    ]
    for name, url, country, cls, protocol, priority in japan_korea_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="East Asia",
            subregion="Japan / Korea",
            country_or_scope=country,
            period_start="1900",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional",
            likely_protocol_family=protocol,
            priority=priority,
            expected_record_types="posters; books; graphic design; exhibition records; periodicals",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_IMG02_if_source_viewer",
            language_scope="ja / ko / en",
            notes="priority East Asia source gap and authority/source-registry expansion",
        ))

    southeast_asia_sources = [
        ("National Library of Vietnam", "https://nlv.gov.vn/", "Vietnam", "national library"),
        ("Vietnam National Archives", "https://archives.gov.vn/", "Vietnam", "national archive"),
        ("National Library of Indonesia", "https://www.perpusnas.go.id/", "Indonesia", "national library"),
        ("National Library of the Philippines", "https://web.nlp.gov.ph/", "Philippines", "national library"),
        ("Singapore National Library Board", "https://www.nlb.gov.sg/", "Singapore", "national library"),
        ("National Archives of Singapore", "https://www.nas.gov.sg/archivesonline/", "Singapore", "national archive"),
        ("National Library of Thailand", "https://www.nlt.go.th/", "Thailand", "national library"),
    ]
    for name, url, country, cls in southeast_asia_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Southeast Asia",
            subregion="National library / archive",
            country_or_scope=country,
            period_start="1830",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional",
            likely_protocol_family="Search interface / HTML",
            priority="P0" if country in {"Vietnam", "Indonesia", "Philippines", "Thailand"} else "P1",
            expected_record_types="periodicals; posters; books; public information print; ephemera",
            expected_text_depth="low_to_medium",
            expected_image_policy="IMG00_default_or_IMG02_source_viewer",
            language_scope="local language / en",
            notes="Southeast Asia coverage gap; prioritize source links and bibliographic records",
        ))

    south_asia_sources = [
        ("Osianama", "https://osianama.com/", "India", "popular visual culture archive"),
        ("MAP Academy", "https://mapacademy.io/", "South Asia", "scholarly encyclopedia"),
        ("DAG", "https://dagworld.com/", "India", "gallery/research archive"),
        ("Alkazi Foundation", "https://alkazifoundation.org/", "South Asia", "photography archive"),
        ("Indian Memory Project", "https://www.indianmemoryproject.com/", "India", "community visual archive"),
        ("National Digital Library of India", "https://ndl.iitkgp.ac.in/", "India", "digital library"),
    ]
    for name, url, country, cls in south_asia_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="South Asia",
            subregion="India / South Asia",
            country_or_scope=country,
            period_start="1850",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional_or_community",
            likely_protocol_family="HTML / Search interface",
            priority="P0",
            expected_record_types="popular print; film publicity; posters; photographs; essays",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_source_policy_review",
            rights_risk="medium",
            language_scope="en / local languages",
            notes="major non-Western visual culture gap; treat images conservatively",
        ))

    mena_sources = [
        ("Khatt Foundation", "https://www.khtt.net/", "MENA", "typography/design archive"),
        ("29LT", "https://www.29lt.com/", "MENA", "typography foundry/archive"),
        ("Barjeel Art Foundation", "https://barjeelartfoundation.org/", "MENA", "art foundation archive"),
        ("Qatar Digital Library", "https://www.qdl.qa/", "MENA", "digital library"),
        ("Akkasah", "https://akkasah.org/", "MENA", "photography archive"),
        ("Egyptian National Library and Archives", "https://www.darelkotob.gov.eg/", "Egypt", "national library"),
        ("Arab Center for Architecture", "https://arab-architecture.org/", "Lebanon / MENA", "architecture/design archive"),
    ]
    for name, url, country, cls in mena_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="MENA",
            subregion="Arab world / Middle East",
            country_or_scope=country,
            period_start="1900",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional_or_independent",
            likely_protocol_family="HTML / Search interface",
            priority="P0",
            expected_record_types="Arabic typography; posters; periodicals; catalog records; essays",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_source_return",
            rights_risk="medium",
            language_scope="ar / en / fr",
            notes="edge-source priority; do not infer rights from visible image availability",
        ))

    africa_sources = [
        ("GALA Queer Archive", "https://gala.co.za/", "South Africa", "community archive"),
        ("Wits Historical Papers", "https://historicalpapers-atom.wits.ac.za/", "South Africa", "university archive"),
        ("UCT Digital Collections", "https://digitalcollections.lib.uct.ac.za/", "South Africa", "university digital collections"),
        ("African Digital Heritage", "https://www.africandigitalheritage.org/", "Africa", "digital heritage organization"),
        ("South African History Online", "https://www.sahistory.org.za/", "South Africa", "history archive"),
        ("University of Pretoria Repository", "https://repository.up.ac.za/", "South Africa", "institutional repository"),
        ("Herskovits Library", "https://www.library.northwestern.edu/libraries-collections/herskovits-library/", "Africa / diaspora", "research library"),
    ]
    for name, url, country, cls in africa_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Africa",
            subregion="Africa / diaspora",
            country_or_scope=country,
            period_start="1850",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="community_or_institutional",
            likely_protocol_family="HTML / ArchiveSpace/EAD / repository",
            priority="P0",
            expected_record_types="posters; activist graphics; publications; visual culture records",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_source_return",
            rights_risk="medium_high",
            language_scope="en / fr / local languages",
            notes="main coverage gap; source relationship and cultural sensitivity review required",
        ))

    latin_america_sources = [
        ("Biblioteca Nacional Argentina", "https://www.bn.gov.ar/", "Argentina", "national library"),
        ("Biblioteca Nacional de Mexico", "https://bnm.iib.unam.mx/", "Mexico", "national library"),
        ("Hemeroteca Nacional Digital de Mexico", "https://hndm.iib.unam.mx/", "Mexico", "newspaper/periodical archive"),
        ("Brasiliana Fotografica", "https://brasilianafotografica.bn.gov.br/", "Brazil", "photo archive"),
        ("Biblioteca Nacional Digital de Chile", "https://www.bibliotecanacionaldigital.gob.cl/", "Chile", "national digital library"),
        ("ICAA Documents", "https://icaa.mfah.org/", "Latin America", "documents archive"),
        ("Princeton Latin American Ephemera", "https://lae.princeton.edu/", "Latin America / Caribbean", "ephemera archive"),
        ("Caribbean Memory Project", "https://www.caribbeanmemoryproject.com/", "Caribbean", "community archive"),
        ("Biblioteca Nacional de Uruguay", "https://www.bibna.gub.uy/", "Uruguay", "national library"),
    ]
    for name, url, country, cls in latin_america_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Latin America / Caribbean",
            subregion="National / community archives",
            country_or_scope=country,
            period_start="1830",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional_or_community",
            likely_protocol_family="HTML / Search interface / IIIF",
            priority="P0",
            expected_record_types="posters; newspapers; ephemera; advertising; political graphics",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_IMG02_if_viewer",
            language_scope="es / pt / en",
            notes="strong region for non-US design history expansion and source triangulation",
        ))

    eastern_europe_sources = [
        ("Czech Digital Library", "https://www.digitalniknihovna.cz/", "Czech Republic", "Kramerius digital library", "Kramerius / IIIF", "P0"),
        ("POLONA", "https://polona.pl/", "Poland", "national digital library", "IIIF / Search interface", "P0"),
        ("e-rara", "https://www.e-rara.ch/", "Switzerland / Europe", "rare books portal", "IIIF / OAI-PMH", "P1"),
        ("Russian State Library", "https://www.rsl.ru/", "Russia", "national library", "Search interface", "P1"),
        ("National Library of Kazakhstan", "https://nabrk.kz/", "Kazakhstan", "national library", "Search interface", "P0"),
        ("Soviet Posters", "https://www.sovietposters.com/", "Russia / Soviet", "poster archive", "HTML", "P1"),
    ]
    for name, url, country, cls, protocol, priority in eastern_europe_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Eastern Europe / Central Asia",
            subregion="Libraries / poster archives",
            country_or_scope=country,
            period_start="1850",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional_or_independent",
            likely_protocol_family=protocol,
            priority=priority,
            expected_record_types="periodicals; posters; books; constructivist/socialist graphic records",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_IMG02_if_IIIF",
            language_scope="local language / en",
            notes="under-covered Eastern Europe/Central Asia source discovery",
        ))

    oceania_sources = [
        ("National Archives of Australia", "https://www.naa.gov.au/", "Australia", "national archive"),
        ("State Library Victoria", "https://www.slv.vic.gov.au/", "Australia", "state library"),
        ("State Library NSW", "https://www.sl.nsw.gov.au/", "Australia", "state library"),
        ("National Library of New Zealand", "https://natlib.govt.nz/", "Aotearoa New Zealand", "national library"),
        ("Te Papa Collections", "https://collections.tepapa.govt.nz/", "Aotearoa New Zealand", "museum collections"),
        ("Auckland Libraries Heritage Collections", "https://kura.aucklandlibraries.govt.nz/", "Aotearoa New Zealand", "library heritage collections"),
    ]
    for name, url, country, cls in oceania_sources:
        rows.append(candidate(
            source_name=name,
            macro_region="Oceania / Indigenous",
            subregion="Australia / Aotearoa",
            country_or_scope=country,
            period_start="1850",
            period_end="2026",
            source_url=url,
            source_class=cls,
            source_level="institutional",
            likely_protocol_family="Search interface / API",
            priority="P1",
            expected_record_types="posters; public information print; Indigenous design; ephemera",
            expected_text_depth="medium",
            expected_image_policy="IMG00_default_or_source_policy_review",
            language_scope="en / Indigenous languages",
            notes="regional and Indigenous source discovery; cultural sensitivity review required",
        ))

    return rows


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for item in rows:
        key = canonical_url(item["url"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    for index, item in enumerate(deduped, start=1):
        item["candidate_id"] = f"CSS{index:04d}"
    return deduped


def main() -> None:
    rows = dedupe_rows([*build_rows(), *extra_rows()])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} candidates to {OUTPUT}")


if __name__ == "__main__":
    main()
