from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ensure_fields(fields: list[str], additions: list[str]) -> list[str]:
    out = list(fields)
    for field in additions:
        if field not in out:
            out.append(field)
    return out


def upsert(path: Path, key: str, additions: list[str], new_rows: list[dict[str, str]]) -> None:
    fields, rows = read_csv(path)
    fields = ensure_fields(fields, additions)
    existing = {row[key]: row for row in rows}
    ordered_keys = [row[key] for row in rows]
    for row in new_rows:
        row = {field: row.get(field, "") for field in fields}
        row_key = row[key]
        if row_key not in existing:
            ordered_keys.append(row_key)
        existing[row_key] = {**existing.get(row_key, {}), **row}
    write_csv(path, fields, [{field: existing[row_key].get(field, "") for field in fields} for row_key in ordered_keys])


def apply_experimental_scope() -> None:
    additions = [
        "scope_cell_id",
        "scope_role",
        "primary_region",
        "secondary_region",
        "hn_ids",
        "movement_ids",
        "event_ids",
        "source_family_id",
        "record_family",
        "default_image_zone",
        "rights_review_level",
        "protocol_sensitive",
        "manual_review_required",
        "query_profile_id",
        "target_record_count",
        "required_fields",
        "expected_surface_type",
    ]
    rows = [
        ("EIC025", "C01", "Bauhaus / 1919 founding first-ingest cell", "SRC001", "The Met Open Access + authority cluster", "Western/Central Europe", "Met object/API records and authority records", "Canonical modernist normalization test with school/person/publication/object relations.", "mixed; OA only per record", "IMG00", "manual_review_required", "source_link_only", "source id; object id; title raw/normalized; maker raw/normalized; date; HN; movement; rights evidence", "Open-museum false positives; over-canonical bias.", "first_ingest_scope", "Selective IMG03 only when record-level OA/CC0 is explicit.", "REG001", "", "HN008; HN014", "RM075", "REN049", "MET_OA_AUTHORITY", "object; authority", "IMG00", "record_level", "false", "true", "bauhaus", "4", "source id; object id; title; maker; date; rights evidence", "SOURCE sheet + NORMALIZED card"),
        ("EIC026", "C02", "Polish Poster School first-ingest cell", "SRC036", "Poster Museum / V&A / Culture.pl + authority", "Eastern Europe", "poster records and institutional/context records", "Poster-specific socialist-context link-only test.", "unclear item image rights", "IMG00", "link_only", "source_link_only", "poster title; designer; event/client; date; place; source note; rights note", "Poster authorship and image rights often inconsistent.", "first_ingest_scope", "Keep link-only unless item-level permission exists.", "REG002", "", "HN009; HN010; HN013", "RM076", "REN050", "POSTER_MUSEUM_AUTHORITY", "poster; authority", "IMG00", "manual", "false", "true", "polish_poster", "2", "poster title; designer; event/client; date; rights note", "loose-leaf poster sheet"),
        ("EIC027", "C03", "IBM corporate design first-ingest cell", "SRC037", "IBM History + Cooper Hewitt + authority", "North America", "corporate archive pages; design object records; authority records", "Institution-designer-manual-object relation test.", "corporate copyright", "IMG00", "metadata_only", "source_link_only", "institution; designer; manual/object distinction; date range; role labels; rights note", "Corporate manuals and archives remain copyright-sensitive.", "first_ingest_scope", "No local image display by default.", "REG003", "", "HN011; HN010", "RM077", "REN051", "IBM_CH_AUTHORITY", "corporate archive; object; authority", "IMG00", "manual", "false", "true", "ibm_design", "4", "institution; designer; manual/object distinction; date range; role labels", "registration card + appendix"),
        ("EIC028", "C04", "Taller de Grafica Popular first-ingest cell", "SRC001", "The Met + Internet Archive + authority", "Latin America", "museum objects; periodicals/books; authority records", "Collective printshop, political print, and publication/object separation test.", "mixed museum and publication rights", "IMG00", "manual_review_required", "source_link_only", "collective name; member names; printer/publisher roles; publication/object distinction; rights evidence", "Collective vs individual creator ambiguity.", "first_ingest_scope", "Selective IMG03 only for explicit OA/public-domain records.", "REG004", "", "HN009; HN012; HN013", "RM078", "REN052", "MET_IA_AUTHORITY", "print; publication; authority", "IMG00", "record_level", "false", "true", "tgp", "4", "collective; printer; publisher; object/publication distinction; rights evidence", "SOURCE sheet + RELATIONS appendix"),
        ("EIC029", "C05", "Brigadas Ramona Parra first-ingest cell", "SRC051", "Memoria Chilena + authority", "Latin America and Caribbean", "thematic dossier; item citation; authority records", "Counterpublic collective-authorship and unstable mural/source boundary test.", "protected work", "IMG00", "link_only", "source_link_only", "collective; date; event relation; publication source; language; citation", "Murals often survive through reproductions; object/source boundary unstable.", "first_ingest_scope", "Link-only required.", "REG004", "", "HN009; HN012; HN013", "RM079", "REN053", "MEMORIA_AUTHORITY", "event; dossier; source sheet", "IMG00", "manual", "false", "true", "brp", "3", "collective; date; event relation; citation", "event card + source sheet"),
        ("EIC030", "C06", "World Design Conference 1960 / NDC first-ingest cell", "SRC038", "M+ / NDC / NDL", "Japan / East Asia transnational", "archive ephemera; institutional pages; bibliographic records", "Japanese-language event/person/institution/work relation test.", "restricted archival ephemera", "IMG00", "metadata_only", "source_link_only", "event name; event dates; participant names; ephemera type; source language; transliteration", "Transliteration variance and restricted archival images.", "first_ingest_scope", "Metadata and source links only.", "REG005", "REG007", "HN010; HN011; HN014", "RM080", "REN054", "MPLUS_NDC_NDL", "event ephemera; institution; bibliography", "IMG00", "manual", "false", "true", "wodeco", "4", "event date; participant names; ephemera type; source language", "event registration card"),
        ("EIC031", "C07", "Shanghai Sketch / yuefenpai first-ingest cell", "SRC025", "Internet Archive + British Museum + authority", "Mainland China", "periodical issue/page records and object records", "Chinese-language issue/page hierarchy plus commercial/vernacular overlap test.", "mixed periodical scan and museum rights", "IMG00", "metadata_only", "source_link_only", "issue title; issue date; page no.; script; translation; advertisement/editorial flag", "OCR/transliteration noise; issue/page duplication.", "first_ingest_scope", "Periodical scans default link-only.", "REG008", "", "HN005; HN007; HN013", "RM081", "REN055", "IA_BRITISH_MUSEUM_AUTHORITY", "periodical issue; page; object", "IMG00", "record_level", "false", "true", "shanghai_manhua", "4", "issue title; issue date; page; script; ad/editorial flag", "periodical issue sheet + page sheet"),
        ("EIC032", "C08", "Minjung / Kwangju poster first-ingest cell", "SRC006", "Library of Congress + authority", "Korea", "poster records; guides; authority records", "Korean-script event-linked protest poster test.", "sensitive political material; sparse image rights", "IMG00", "metadata_only", "source_link_only", "title; creator if known; event relation; political keyword; Korean script; rights advisory", "Sensitive context and advisory-not-warranty rights.", "first_ingest_scope", "Keep LOC records link-only unless reviewed.", "REG006", "", "HN009; HN012; HN014", "RM082", "REN056", "LOC_AUTHORITY", "poster; guide; authority", "IMG00", "manual", "false", "true", "minjung", "3", "title; creator; event relation; Korean script; rights advisory", "poster sheet + event appendix"),
        ("EIC033", "C09", "Singapore multilingual poster/logotype first-ingest cell", "SRC041", "NLB Singapore OneSearch / BiblioAsia", "Southeast Asia", "catalogue records and collection essays", "Four-language public campaign and source/object distinction test.", "catalogue rights; depositor rights", "IMG00", "metadata_only", "source_link_only", "campaign title; agency/institution; languages present; object type; source institution", "Catalogue presence may be mistaken for image permission.", "first_ingest_scope", "IMG01 only after dataset thumbnail review.", "REG011", "", "HN009; HN010; HN011", "RM083", "REN057", "NLB_SG", "catalogue; article", "IMG00", "manual", "false", "true", "sg_posters", "3", "campaign title; agency; languages; object type", "SOURCE sheet"),
        ("EIC034", "C10", "NID development communication first-ingest cell", "SRC053", "NID + Internet Archive + authority", "South Asia", "institutional pages; publications; authority records", "State-building, pedagogy, design education, and multilingual India test.", "institutional/archive image uncertainty", "IMG00", "metadata_only", "source_link_only", "institution; founders/related figures; programme/publication title; date; place", "Archival dispersion and weak object-level rights.", "first_ingest_scope", "Metadata-first.", "REG012", "", "HN010; HN011; HN014", "RM084", "REN058", "NID_IA_AUTHORITY", "institution; publication; authority", "IMG00", "manual", "false", "true", "nid", "3", "institution; founders; programme/publication; date; place", "registration card"),
        ("EIC035", "C11", "Iranian modern poster design first-ingest cell", "SRC042", "Encyclopaedia Iranica + authority", "MENA", "reference records; publication records; authority records", "Persian-script and transliteration test for regional modern graphic design.", "limited verified image licensing", "IMG00", "metadata_only", "source_link_only", "designer name variants; Persian script; date; event/publication relation; citation", "Author-name transliteration variance.", "first_ingest_scope", "Citation-first.", "REG013", "", "HN010; HN011; HN014", "RM085", "REN059", "IRANICA_AUTHORITY", "authority; source sheet", "IMG00", "manual", "false", "true", "iran_poster", "2", "designer variants; Persian script; date; citation", "authority card + source sheet"),
        ("EIC036", "C12", "Medu / Culture and Resistance first-ingest cell", "SRC052", "SAHA + SAHO", "Africa", "poster records; collection inventories; essays", "Collective authorship, exile, anti-apartheid, and call-number metadata test.", "politically sensitive; copyright fragmented", "IMG00", "link_only", "source_link_only", "poster title; call no.; origination; place; date; collective member; source link", "Community archive and movement sensitivity.", "first_ingest_scope", "No local image.", "REG014", "", "HN009; HN012", "RM086", "REN060", "SAHA_SAHO", "poster; inventory; essay", "IMG00", "manual", "false", "true", "medu", "4", "poster title; call no.; origination; date; collective member", "loose-leaf poster sheet + appendix"),
        ("EIC037", "C13", "NAIDOC / land-rights posters first-ingest cell", "SRC045", "AIATSIS + Trove + NAIDOC", "Oceania / Indigenous", "protocol-sensitive records and poster-gallery records", "ICIP/protocol-sensitive metadata test.", "ICIP and cultural sensitivity", "IMG00", "manual_review_required", "source_link_only", "title; year; artist/community; ICIP flag; sensitivity flag; source link", "Access does not imply reuse or display permission.", "first_ingest_scope", "Suppress thumbnails when sensitivity is flagged.", "REG015", "", "HN012; HN013; HN015", "RM087", "REN061", "AIATSIS_TROVE_NAIDOC", "registration; protocol appendix", "IMG00", "protocol_review", "true", "true", "naidoc_land_rights", "3", "title; year; artist/community; ICIP flag; sensitivity flag", "registration card + protocol appendix"),
        ("EIC038", "C14", "Gran Fury / ACT UP first-ingest cell", "SRC046", "ACT UP archive + MoMA + NLM", "North America / transnational", "archive records; museum records; medical/public-health records", "Collective authorship, campaign relation, and queer counterpublic graphics test.", "copyright and community sensitivity", "IMG00", "link_only", "source_link_only", "collective; campaign; date; place; source archive; rights note", "Historically central but rights-sensitive.", "first_ingest_scope", "Link-only.", "REG003", "GEO001", "HN012; HN013", "RM088", "REN062", "ACTUP_MOMA_NLM", "protest graphic; archive; essay", "IMG00", "manual", "false", "true", "gran_fury_actup", "3", "collective; campaign; date; source archive; rights note", "protest-graphics card"),
        ("EIC039", "C15", "Early web / CSS / GeoCities first-ingest cell", "SRC048", "CERN + W3C + Wayback + Internet Archive", "Global digital", "web standards pages and archived captures", "Born-digital source/capture timestamp and archived-rights test.", "archived pages remain copyrighted", "IMG00", "link_only", "source_link_only", "original URL; capture timestamp; page title; standard/version; source type; rights note", "Unstable captures and screenshot-vs-HTML rights confusion.", "first_ingest_scope", "Store source snapshot records; no local screenshots.", "REG007", "GEO001", "HN015; HN014", "RM089", "REN063", "CERN_W3C_WAYBACK_IA", "web source; snapshot; standard", "IMG00", "manual", "false", "true", "early_web_css_geocities", "2", "original URL; capture timestamp; title; standard/version", "web-source sheet"),
    ]
    keys = [
        "experimental_candidate_id", "scope_cell_id", "candidate_name", "source_id", "source_name", "region", "record_type",
        "test_purpose", "expected_rights_state", "expected_image_zone", "expected_record_policy", "expected_display_policy",
        "likely_fields", "risks", "scope_role", "notes", "primary_region", "secondary_region", "hn_ids", "movement_ids",
        "event_ids", "source_family_id", "record_family", "default_image_zone", "rights_review_level", "protocol_sensitive",
        "manual_review_required", "query_profile_id", "target_record_count", "required_fields", "expected_surface_type",
    ]
    scoped_rows = []
    for row in rows:
        item = dict(zip(keys, row))
        item["shortlist_status"] = "pending"
        scoped_rows.append(item)
    upsert(DATA / "experimental_ingest_shortlist.csv", "experimental_candidate_id", additions, scoped_rows)


def apply_movement_scope() -> None:
    additions = [
        "movement_mode",
        "script_flags",
        "collective_authorship",
        "periodical_relevance",
        "protocol_sensitive",
        "source_priority_class",
    ]
    seed = [
        ("RM075", "Bauhaus / New Typography first-ingest network", "Bauhaus; Die Neue Typographie", "REG001", "GEO006", "1919", "1933", "1919-1933", "school/typographic network", "HN008; HN014", "MV011; MV012", "books; teaching material; stationery; posters", "Met; Smithsonian/Cooper Hewitt; Internet Archive; authority cluster", "medium", "first_ingest_scope", "Scope cell for canonical modernist normalization and rights false-positive testing.", "multiple", "Latin", "no", "medium", "false", "A"),
        ("RM076", "Polish Poster School first-ingest scope", "Polska szkola plakatu", "REG002", "GEO018", "1950", "1989", "c.1950s-1980s", "poster/socialist cultural formation", "HN009; HN010; HN013", "RM010", "film posters; theatre posters; cultural posters", "Poster Museum; Culture.pl; V&A; PGDA; authority cluster", "high", "first_ingest_scope", "Scope cell for socialist-context poster indexing in link-only mode.", "single", "Latin", "mixed", "low", "false", "A"),
        ("RM077", "IBM corporate design systems formation", "IBM design program", "REG003", "GEO025", "1956", "1987", "1956-1987", "corporate/systems formation", "HN010; HN011", "MV016", "identity manuals; signage; manuals; object records", "IBM history; Cooper Hewitt; PGDA; Letterform Archive; authority cluster", "high", "first_ingest_scope", "Tests institution-designer-manual-object relations.", "multiple", "Latin", "no", "low", "false", "A"),
        ("RM078", "Taller de Grafica Popular first-ingest scope", "TGP", "REG004", "GEO027", "1937", "1965", "1937-1965", "workshop/political print formation", "HN009; HN012; HN013", "RM068; MV021", "prints; broadsheets; portfolios; books", "Met; MoMA; Internet Archive; authority cluster", "medium-high", "first_ingest_scope", "Collective printshop and publication/object separation test.", "multiple", "Latin", "yes", "medium", "false", "A"),
        ("RM079", "Brigadas Ramona Parra first-ingest scope", "BRP", "REG004", "GEO032", "1969", "1988", "c.1969-1980s", "counterpublic mural/propaganda formation", "HN009; HN012; HN013", "MV021; RM022", "murals; posters; periodical reproductions; propaganda", "Memoria Chilena; Chilean archive authorities; authority cluster", "high", "first_ingest_scope", "Collective authorship and unstable mural/source boundaries.", "multiple", "Latin", "yes", "medium", "false", "A"),
        ("RM080", "Japanese postwar design institution network", "WoDeCo; NDC", "REG005", "GEO036", "1959", "1975", "1959-1970s", "institution/event network", "HN010; HN011; HN014", "RM023; RM024", "event ephemera; posters; programmes; institutional records", "M+; NDC; NDL Search; Internet Archive", "high", "first_ingest_scope", "Tests Japanese-language event and institution relations.", "multiple", "Kanji; Hiragana; Katakana; Latin", "mixed", "medium", "false", "A"),
        ("RM081", "Shanghai Manhua and yuefenpai commercial print", "Shanghai Sketch; 上海漫畫; 上海漫画; 月份牌", "REG008", "GEO040", "1928", "1939", "1928-1930s", "commercial/periodical formation", "HN005; HN007; HN013", "RM028; MV030", "pictorial magazines; advertisements; calendar posters; packaging", "Internet Archive; British Museum; authority cluster", "high", "first_ingest_scope", "Tests Chinese issue/page records and movement NONE/overlap.", "multiple", "Traditional Chinese; Simplified Chinese; Latin", "mixed", "high", "false", "A"),
        ("RM082", "Minjung and democratization poster culture", "민중미술; democratization posters", "REG006", "GEO038", "1980", "1988", "1980s", "counterpublic/political poster formation", "HN009; HN012; HN014", "MV021", "posters; rare books; guides; political ephemera", "Library of Congress; authority cluster; Korean museum sources", "high", "first_ingest_scope", "Tests Korean script and event-linked protest graphics.", "multiple", "Hangul; Hanja; Latin", "mixed", "medium", "false", "A"),
        ("RM083", "Singapore multilingual poster and logotype systems", "Singapore campaign poster regime", "REG011", "GEO095", "1965", "1985", "c.1965-1985", "multilingual public-information formation", "HN009; HN010; HN011", "RM063; MV018", "campaign posters; logos; public information; catalogue records", "NLB Singapore OneSearch; BiblioAsia; authority cluster", "high", "first_ingest_scope", "Tests four-language metadata and catalogue/object distinctions.", "multiple", "Latin; Han; Tamil; Jawi historical", "no", "medium", "false", "A"),
        ("RM084", "NID development-communication and modern design formation", "National Institute of Design Ahmedabad", "REG012", "GEO051", "1961", "1985", "1961-1980s", "design education/development communication formation", "HN010; HN011; HN014", "RM041; RM043", "institutional publications; pedagogy; design education records", "NID; Internet Archive; authority cluster", "high", "first_ingest_scope", "Tests state-building, pedagogy, and multilingual India.", "multiple", "Indic scripts; Latin", "mixed", "medium", "false", "A"),
        ("RM085", "Iranian modern poster and graphic-design formation", "Morteza Momayyez context; Iranian graphic arts", "REG013", "GEO083", "1964", "1989", "1964-1980s", "professional/poster/script formation", "HN010; HN011; HN014", "RM057; RM058", "posters; books; magazines; exhibition references", "Encyclopaedia Iranica; Internet Archive; authority cluster", "high", "first_ingest_scope", "Tests Persian script, RTL metadata, and transliteration.", "multiple", "Arabic-derived Persian; Latin", "mixed", "medium", "false", "A"),
        ("RM086", "Medu Art Ensemble and anti-apartheid poster movement", "Medu; Culture and Resistance", "REG014", "GEO102", "1978", "1985", "1978-1985", "workshop/solidarity formation", "HN009; HN012", "RM071; MV021", "posters; newsletters; workshop records; essays", "SAHA; SAHO; authority cluster", "high", "first_ingest_scope", "Tests collective authorship and community archive call numbers.", "multiple", "Latin", "yes", "low", "false", "A"),
        ("RM087", "Aboriginal land-rights and NAIDOC poster cultures", "NAIDOC posters; Aboriginal land rights graphics", "REG015", "GEO104", "1972", "", "1972-present", "Indigenous/counterpublic poster formation", "HN012; HN013; HN015", "RM073; MV025", "posters; campaign graphics; community records", "AIATSIS; Trove/NLA; NAIDOC", "high", "first_ingest_scope", "Tests ICIP-aware and protocol-sensitive ingest.", "multiple", "Latin; Indigenous orthographies", "mixed", "medium", "true", "A"),
        ("RM088", "Gran Fury and ACT UP activist graphics", "AIDS activist graphics", "REG003", "GEO025", "1987", "1995", "1987/1988-1995", "queer counterpublic campaign formation", "HN012; HN013", "MV023", "posters; campaigns; archive records; public-health graphics", "ACT UP archives; MoMA; NLM; authority cluster", "high", "first_ingest_scope", "Tests collective authorship and campaign relations.", "multiple", "Latin", "yes", "low", "false", "A"),
        ("RM089", "Early web, CSS, and homepage/interface formation", "info.cern.ch; CSS1; GeoCities", "REG007", "GEO001", "1991", "2009", "1991-2009", "born-digital/platform formation", "HN014; HN015", "MV034; MV035; MV036", "web pages; standards; captures; homepages", "CERN; W3C; Wayback Machine; Internet Archive", "very high", "first_ingest_scope", "Tests capture timestamps, source volatility, and link-only web records.", "none_ok", "Latin; multiple", "mixed", "low", "false", "A"),
    ]
    keys = [
        "regional_movement_id", "name", "alternate_names", "region_id", "geo_id", "date_start", "date_end", "date_text",
        "formation_type", "related_node_ids", "related_movement_ids", "key_media", "source_needs", "rights_risk",
        "status", "notes", "movement_mode", "script_flags", "collective_authorship", "periodical_relevance",
        "protocol_sensitive", "source_priority_class",
    ]
    upsert(DATA / "regional_movements.csv", "regional_movement_id", additions, [dict(zip(keys, row)) for row in seed])


def apply_event_scope() -> None:
    additions = [
        "event_date_start",
        "event_date_end",
        "date_precision",
        "anchor_strength",
        "source_record_required",
        "browse_priority",
        "web_archive_relevant",
    ]
    seed = [
        ("REN049", "Bauhaus founding in Weimar", "school founding", "REG001", "GEO006", "1919", "1919", "1919", "HN008", "RM075", "Met; Bauhaus institutional histories; Internet Archive", "medium", "first_ingest_scope", "Clean anchor for institution, manifesto, teachers, workshops, and diaspora relations.", "1919", "1919", "year", "high", "yes", "A", "false"),
        ("REN050", "Poster Museum at Wilanow opens", "institutional poster node", "REG002", "GEO018", "1968", "1968", "1968", "HN009; HN010; HN013", "RM076", "Poster Museum; Culture.pl", "medium-high", "first_ingest_scope", "Stable institutional node for the Polish Poster School.", "1968", "1968", "year", "high", "yes", "A", "false"),
        ("REN051", "IBM corporate design program begins", "corporate design program", "REG003", "GEO025", "1956", "1956", "1956", "HN010; HN011", "RM077", "IBM history; Cooper Hewitt", "high", "first_ingest_scope", "Anchors manuals, systems, logos, signage, and institution-wide design governance.", "1956", "1956", "year", "high", "yes", "A", "false"),
        ("REN052", "Taller de Grafica Popular founded", "workshop founding", "REG004", "GEO027", "1937", "1937", "1937", "HN009; HN012; HN013", "RM078", "Met; MoMA; Internet Archive", "medium-high", "first_ingest_scope", "Dateable anchor for collective authorship and popular-print networks.", "1937", "1937", "year", "high", "yes", "A", "false"),
        ("REN053", "Brigadas Ramona Parra propaganda cycle", "counterpublic mural/propaganda node", "REG004", "GEO032", "1969", "1988", "c.1969-1980s", "HN009; HN012; HN013", "RM079", "Memoria Chilena; Chilean archive authorities", "high", "first_ingest_scope", "Anchors Chilean collective mural and propaganda graphics.", "1969", "1988", "range", "medium", "yes", "A", "false"),
        ("REN054", "World Design Conference in Tokyo", "design conference", "REG005", "GEO036", "1960", "1960", "11-16 May 1960", "HN010; HN011; HN014", "RM080", "M+; NDC; NDL", "high", "first_ingest_scope", "Dateable multilingual event and East Asia network anchor.", "1960", "1960", "exact_date", "high", "yes", "A", "false"),
        ("REN055", "Launch of Shanghai Sketch", "periodical launch", "REG008", "GEO040", "1928", "1928", "1928", "HN005; HN007; HN013", "RM081", "Internet Archive; British Museum; authority cluster", "high", "first_ingest_scope", "Issue-based anchor for Chinese-language periodical hierarchy.", "1928", "1928", "year", "high", "yes", "A", "false"),
        ("REN056", "Kwangju Uprising as Minjung poster anchor", "political event", "REG006", "GEO038", "1980", "1980", "May 1980", "HN009; HN012; HN014", "RM082", "Library of Congress Korean collection", "high", "first_ingest_scope", "Event-linked poster production and later democratization references.", "1980", "1980", "month", "high", "yes", "A", "false"),
        ("REN057", "Singapore multilingual public campaign poster phase", "public information phase", "REG011", "GEO095", "1965", "1985", "c.1965-1985", "HN009; HN010; HN011", "RM083", "NLB Singapore; BiblioAsia", "high", "first_ingest_scope", "Multilingual state-campaign and catalogue-record anchor.", "1965", "1985", "range", "medium", "yes", "A", "false"),
        ("REN058", "National Institute of Design established", "design education founding", "REG012", "GEO051", "1961", "1961", "1961", "HN010; HN011; HN014", "RM084", "NID; Internet Archive; authority cluster", "medium-high", "first_ingest_scope", "Anchors pedagogy, state-building, and design education records.", "1961", "1961", "year", "high", "yes", "A", "false"),
        ("REN059", "Tehran graphic-design exhibition context", "professionalization/exhibition node", "REG013", "GEO083", "1964", "1964", "1964", "HN010; HN011; HN014", "RM085", "Encyclopaedia Iranica; authority cluster", "high", "first_ingest_scope", "Anchor for Iranian modern poster and graphic-design professionalization.", "1964", "1964", "year", "medium", "yes", "A", "false"),
        ("REN060", "Culture and Resistance festival", "workshop/solidarity event", "REG014", "GEO102", "1982", "1982", "5-9 July 1982", "HN009; HN012", "RM086", "SAHA; SAHO", "high", "first_ingest_scope", "African event node linking posters, symposium material, and diaspora activism.", "1982", "1982", "exact_date", "high", "yes", "A", "false"),
        ("REN061", "NAIDOC poster series and Aboriginal land-rights poster culture", "Indigenous/protocol-sensitive poster node", "REG015", "GEO104", "1972", "", "1972-present", "HN012; HN013; HN015", "RM087", "AIATSIS; Trove/NLA; NAIDOC", "high", "first_ingest_scope", "Protocol-sensitive Indigenous poster anchor.", "1972", "", "open_range", "high", "yes", "A", "false"),
        ("REN062", "ACT UP founded", "queer counterpublic organization founding", "REG003", "GEO025", "1987", "1987", "March 1987", "HN012; HN013", "RM088", "ACT UP archives; MoMA; NLM", "high", "first_ingest_scope", "Clean event anchor for Gran Fury and AIDS activist graphics.", "1987", "1987", "month", "high", "yes", "A", "false"),
        ("REN063", "First website, CSS1, and GeoCities archival transition", "born-digital/web standards node", "REG007", "GEO001", "1991", "2009", "1991-2009", "HN014; HN015", "RM089", "CERN; W3C; Wayback Machine; Internet Archive", "very high", "first_ingest_scope", "Born-digital source-chain and platform-loss anchor.", "1991", "2009", "range", "high", "yes", "A", "true"),
    ]
    keys = [
        "event_node_id", "event_name", "event_type", "region_id", "geo_id", "date_start", "date_end", "date_text",
        "related_node_ids", "related_regional_movement_ids", "source_need", "rights_risk", "status", "notes",
        "event_date_start", "event_date_end", "date_precision", "anchor_strength", "source_record_required",
        "browse_priority", "web_archive_relevant",
    ]
    upsert(DATA / "regional_event_nodes.csv", "event_node_id", additions, [dict(zip(keys, row)) for row in seed])


def apply_sources() -> None:
    additions = [
        "automation_status",
        "rights_basis",
        "record_level_rights_required",
        "default_image_zone",
        "preview_allowed",
        "thumbnail_allowed",
        "iiif_capable",
        "api_key_required",
        "protocol_sensitive",
    ]
    rows = [
        ("SRC036", "Poster Museum at Wilanow", "https://www.postermuseum.pl/", "poster museum", "search interface", "https://www.postermuseum.pl/", "unknown", "unknown", "unknown", "Poland", "postwar-present", "very high for Polish poster history", "poster records; exhibition records", "Rights vary; link-only safest.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "First-ingest source for Polish Poster School.", "2026-05-30", "manual_review", "item_or_site_terms_required", "yes", "IMG00", "no", "no", "unknown", "false", "false"),
        ("SRC037", "IBM History Design Program", "https://www.ibm.com/history/design-program", "corporate history archive", "website", "https://www.ibm.com/history/design-program", "no", "no", "no", "United States; global corporate", "1956-present context", "high for corporate design systems", "institutional history; image/text page", "Corporate content; link-only unless permission.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Anchor for IBM corporate design program.", "2026-05-30", "manual_review", "corporate_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC038", "M+ Collections and Archives", "https://www.mplus.org.hk/en/collection/archives/", "museum/archive", "search interface", "https://www.mplus.org.hk/en/collection/archives/", "unknown", "unknown", "unknown", "Hong Kong; Asia; global", "modern-contemporary", "high for Asian design and visual culture archives", "archive records; ephemera; collection pages", "Item-level copyright and access restrictions; link-only first.", "partial", "High", "yes", "No", "Yes", "Launch", "WoDeCo and East Asia design network source.", "2026-05-30", "manual_review", "item_level_copyright", "yes", "IMG00", "no", "no", "unknown", "false", "false"),
        ("SRC039", "Nippon Design Center", "https://www.ndc.co.jp/en/about/", "design institution archive", "website", "https://www.ndc.co.jp/en/about/", "no", "no", "no", "Japan", "1959-present", "high for Japanese postwar design institution context", "institutional history; designer/studio context", "Copyrighted corporate/institutional content; link-only.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Anchor for Japanese postwar design institution network.", "2026-05-30", "manual_review", "institutional_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC040", "British Museum Collection", "https://www.britishmuseum.org/collection", "museum collection", "search interface", "https://www.britishmuseum.org/collection", "unknown", "unknown", "unknown", "UK; global", "broad", "moderate-high for prints, posters, and Chinese visual culture", "object records; images; collection data", "Rights vary; use item-level terms.", "partial", "High", "yes", "Partial", "Yes", "Launch", "Useful comparator for yuefenpai object records.", "2026-05-30", "manual_review", "item_level_terms", "yes", "IMG00", "unknown", "unknown", "unknown", "false", "false"),
        ("SRC041", "NLB Singapore OneSearch and BiblioAsia", "https://reference.nlb.gov.sg/getting-started/onesearch/", "national library/catalogue", "search interface + articles", "https://reference.nlb.gov.sg/getting-started/onesearch/", "unknown", "unknown", "partial", "Singapore", "modern-contemporary", "very high for multilingual public campaign and poster records", "catalogue records; articles; collection notes", "Catalogue presence does not imply image reuse permission.", "unknown", "High", "yes", "Partial", "Yes", "Launch", "First-ingest source for Singapore multilingual poster/logotype records.", "2026-05-30", "manual_review", "catalogue_rights_item_level", "yes", "IMG00", "no", "review", "unknown", "false", "false"),
        ("SRC042", "Encyclopaedia Iranica", "https://www.iranicaonline.org/", "reference source", "website", "https://www.iranicaonline.org/", "no", "no", "no", "Iran; Persianate contexts", "broad historical", "high for Iranian graphic arts anchoring", "reference articles; bibliographic context", "Citation/source-link use; no image reuse assumption.", "unknown", "High", "yes", "No", "Yes", "Launch", "Anchor for Iranian modern poster and graphic design context.", "2026-05-30", "manual_review", "reference_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC043", "South African History Online", "https://www.sahistory.org.za/", "public history archive", "website", "https://www.sahistory.org.za/", "unknown", "unknown", "unknown", "South Africa; Southern Africa", "modern-contemporary", "high for Medu and anti-apartheid context", "articles; archive context; images", "Rights vary; link-only first.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Context source for Medu/Culture and Resistance.", "2026-05-30", "manual_review", "site_and_item_rights", "yes", "IMG00", "no", "no", "unknown", "false", "false"),
        ("SRC044", "NAIDOC Poster Gallery", "https://www.naidoc.org.au/posters/poster-gallery", "community/government cultural poster gallery", "website", "https://www.naidoc.org.au/posters/poster-gallery", "no", "no", "no", "Aboriginal and Torres Strait Islander Australia", "1972-present", "very high for Indigenous poster history", "poster records; artist/year entries", "Copyright and ICIP/protocol considerations; link-only first.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Protocol-sensitive source for NAIDOC poster cell.", "2026-05-30", "manual_review", "copyright_plus_icip", "yes", "IMG00", "no", "no", "no", "false", "true"),
        ("SRC045", "AIATSIS", "https://aiatsis.gov.au/", "Indigenous research/archive institution", "search interface + guidance", "https://aiatsis.gov.au/", "unknown", "unknown", "unknown", "Aboriginal and Torres Strait Islander Australia", "broad", "high for protocol-aware Indigenous visual culture records", "catalogue records; guidance; collection context", "ICIP and cultural protocols may exceed copyright.", "unknown", "High", "yes", "No", "Yes", "Launch", "Use for protocol-sensitive metadata and review rules.", "2026-05-30", "manual_review", "icip_protocol_required", "yes", "IMG00", "no", "no", "unknown", "false", "true"),
        ("SRC046", "ACT UP Oral History Project", "https://www.actuporalhistory.org/", "community oral-history/archive project", "website", "https://www.actuporalhistory.org/", "no", "no", "no", "United States; transnational queer activism", "1987-present context", "high for ACT UP/Gran Fury context", "oral histories; campaign context; source links", "Community and copyright sensitivity; link-only first.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Anchor for ACT UP/Gran Fury event and collective context.", "2026-05-30", "manual_review", "community_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC047", "National Library of Medicine Digital Collections", "https://collections.nlm.nih.gov/", "national library digital collection", "search interface", "https://collections.nlm.nih.gov/", "unknown", "unknown", "unknown", "United States; public health", "modern-contemporary", "high for AIDS/public-health graphics context", "posters; public-health records; metadata", "Rights vary by item; link-only unless explicit.", "mixed", "High", "yes", "Partial", "Yes", "Launch", "Complementary source for Gran Fury/AIDS graphics.", "2026-05-30", "manual_review", "item_level_rights", "yes", "IMG00", "unknown", "unknown", "unknown", "false", "false"),
        ("SRC048", "CERN first website", "https://info.cern.ch/", "web history source", "website", "https://info.cern.ch/", "no", "no", "no", "Global web", "1991-present context", "high for early web source-chain anchoring", "web page; historical reconstruction; source link", "Link/citation first; avoid local screenshots by default.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Anchor for first website event.", "2026-05-30", "manual_review", "web_page_rights", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC049", "W3C CSS Archive", "https://www.w3.org/Style/CSS20/", "web standards archive", "website", "https://www.w3.org/Style/CSS20/", "no", "no", "no", "Global web", "1996-present context", "high for interface/web standards history", "standards pages; versioned recommendations", "Link/citation first; standards terms apply.", "unknown", "High", "yes", "No", "Yes", "Launch", "Anchor for CSS1 / standards event.", "2026-05-30", "manual_review", "standards_site_terms", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC050", "Culture.pl", "https://culture.pl/en", "cultural-history publication", "website", "https://culture.pl/en", "no", "no", "no", "Poland", "modern-contemporary", "high for Polish poster context", "essays; source context; maker names", "Citation/link source; no image reuse assumption.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Context source for Polish Poster School and Wilanow.", "2026-05-30", "manual_review", "site_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC051", "Memoria Chilena", "https://www.memoriachilena.gob.cl/", "national library digital portal", "search interface", "https://www.memoriachilena.gob.cl/", "unknown", "unknown", "unknown", "Chile", "modern", "high for Chilean posters, periodicals, and BRP context", "thematic dossiers; digitized items; citations", "Free access does not imply open image licensing.", "unknown", "High", "yes", "Partial", "Yes", "Launch", "First-ingest source for BRP and Chilean graphics.", "2026-05-30", "manual_review", "item_level_permission_required", "yes", "IMG00", "no", "no", "unknown", "false", "false"),
        ("SRC052", "South African History Archive", "https://www.saha.org.za/", "community/archive poster collection", "search interface", "https://www.saha.org.za/", "unknown", "unknown", "unknown", "South Africa; Southern Africa", "anti-apartheid and struggle history", "very high for poster and movement media records", "poster records; call numbers; collection inventories", "Copyright often retained by archive/rights holders.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "First-ingest source for Medu and anti-apartheid poster records.", "2026-05-30", "manual_review", "community_archive_copyright", "yes", "IMG00", "no", "no", "unknown", "false", "false"),
        ("SRC053", "National Institute of Design", "https://www.nid.edu/about/history-of-nid", "design education institution", "website", "https://www.nid.edu/about/history-of-nid", "no", "no", "no", "India", "1961-present", "high for South Asian design education and development communication", "institutional history; publications context", "Institutional copyright; link-only first.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Anchor for NID formation cell.", "2026-05-30", "manual_review", "institutional_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
        ("SRC054", "Computer History Museum Timeline", "https://www.computerhistory.org/timeline/1984/", "technology history source", "website", "https://www.computerhistory.org/timeline/1984/", "no", "no", "no", "United States; global computing", "1984 context", "moderate for GUI/DTP transition anchoring", "timeline record; reference page", "Citation/link source; no image reuse assumption.", "unknown", "Medium", "yes", "No", "Yes", "Launch", "Anchor for Macintosh near-digital event.", "2026-05-30", "manual_review", "site_copyright", "yes", "IMG00", "no", "no", "no", "false", "false"),
    ]
    keys = [
        "source_id", "name", "url", "source_type", "access_method", "api_base_or_endpoint", "iiif_support",
        "oai_pmh_support", "dataset_support", "geo_coverage", "historical_coverage", "graphic_design_relevance",
        "likely_record_types", "rights_summary", "rights_uri_support", "metadata_quality_estimate", "stable_identifiers",
        "automated_ingestion", "link_only_safer", "priority", "notes", "last_verified_date", "automation_status",
        "rights_basis", "record_level_rights_required", "default_image_zone", "preview_allowed", "thumbnail_allowed",
        "iiif_capable", "api_key_required", "protocol_sensitive",
    ]
    upsert(DATA / "source_registry.csv", "source_id", additions, [dict(zip(keys, row)) for row in rows])


def apply_search_terms() -> None:
    additions = [
        "query_profile_id",
        "script",
        "term_type",
        "preferred",
        "transliteration_of",
        "false_positive_note",
    ]
    terms = [
        ("SV164", "Bauhaus", "bauhaus", "movement", "de", "", "modernism", "", "Neue Typographie; Herbert Bayer", "yes", "first_ingest: bauhaus", "LC; Getty", "", "First ingest query profile.", "bauhaus", "Latin", "movement", "yes", "", "architecture-only hits"),
        ("SV165", "Neue Typographie", "neue typographie", "movement", "de", "New Typography", "Bauhaus", "", "Jan Tschichold", "yes", "first_ingest: bauhaus", "LC; Getty", "", "German term for New Typography.", "bauhaus", "Latin", "movement", "yes", "", "later retrospectives"),
        ("SV166", "Polska szkola plakatu", "polska szkola plakatu", "movement", "pl", "Polish Poster School", "poster", "", "Wilanow", "yes", "first_ingest: polish_poster", "editorial", "", "Polish Poster School query term.", "polish_poster", "Latin", "movement", "yes", "", "poster shops and reproductions"),
        ("SV167", "Polish Poster School", "polish poster school", "movement", "en", "Polish poster", "poster", "", "Poster Museum", "yes", "first_ingest: polish_poster", "editorial", "", "English query term.", "polish_poster", "Latin", "movement", "yes", "", "general poster histories"),
        ("SV168", "IBM design program", "ibm design program", "institutional formation", "en", "IBM corporate design", "corporate identity", "", "Eliot Noyes; Paul Rand", "yes", "first_ingest: ibm_design", "corporate history", "", "IBM design systems query.", "ibm_design", "Latin", "institution", "yes", "", "contemporary IBM design system material"),
        ("SV169", "Taller de Grafica Popular", "taller de grafica popular", "movement", "es", "TGP", "political print", "", "Hoja Popular Ilustrada", "yes", "first_ingest: tgp", "editorial", "", "Spanish movement query.", "tgp", "Latin", "movement", "yes", "", "modern exhibition pages"),
        ("SV170", "grafica popular", "grafica popular", "movement", "es", "gráfica popular", "political print", "", "TGP", "yes", "first_ingest: tgp", "editorial", "", "Accent-flexible query term.", "tgp", "Latin", "theme", "no", "", "generic popular graphics"),
        ("SV171", "World Design Conference 1960", "world design conference 1960", "event", "en", "WoDeCo", "design conference", "", "Tokyo", "yes", "first_ingest: wodeco", "editorial", "", "WoDeCo query.", "wodeco", "Latin", "event", "yes", "", "later commemorations"),
        ("SV172", "世界デザイン会議", "世界デザイン会議", "event", "ja", "東京世界デザイン会議", "design conference", "", "WoDeCo", "yes", "first_ingest: wodeco", "editorial", "", "Japanese WoDeCo query.", "wodeco", "Kanji; Katakana", "event", "yes", "World Design Conference", "commemorative essays"),
        ("SV173", "National Institute of Design", "national institute of design", "institution", "en", "NID Ahmedabad", "design education", "", "India", "yes", "first_ingest: nid", "institutional", "", "NID query.", "nid", "Latin", "institution", "yes", "", "admissions/news pages"),
        ("SV174", "राष्ट्रीय डिजाइन संस्थान", "राष्ट्रीय डिजाइन संस्थान", "institution", "hi", "National Institute of Design", "design education", "", "NID", "yes", "first_ingest: nid", "editorial", "", "Hindi NID variant.", "nid", "Devanagari", "institution", "no", "National Institute of Design", "general education results"),
        ("SV175", "上海漫畫", "上海漫畫", "periodical", "zh-Hant", "Shanghai Manhua; Shanghai Sketch", "pictorial magazine", "", "月份牌", "yes", "first_ingest: shanghai_manhua", "editorial", "", "Traditional Chinese Shanghai Manhua query.", "shanghai_manhua", "Traditional Chinese", "periodical", "yes", "Shanghai Sketch", "modern scholarship"),
        ("SV176", "上海漫画", "上海漫画", "periodical", "zh-Hans", "Shanghai Manhua; Shanghai Sketch", "pictorial magazine", "", "月份牌", "yes", "first_ingest: shanghai_manhua", "editorial", "", "Simplified Chinese Shanghai Manhua query.", "shanghai_manhua", "Simplified Chinese", "periodical", "yes", "Shanghai Sketch", "modern scholarship"),
        ("SV177", "月份牌", "月份牌", "object type", "zh", "yuefenpai; calendar poster", "commercial print", "", "Shanghai advertising", "yes", "first_ingest: shanghai_manhua", "editorial", "", "Calendar-poster query.", "shanghai_manhua", "Chinese", "object_type", "yes", "yuefenpai", "calendar results not design-specific"),
        ("SV178", "민중미술", "민중미술", "movement", "ko", "Minjung art", "protest graphics", "", "광주", "yes", "first_ingest: minjung", "editorial", "", "Korean Minjung query.", "minjung", "Hangul", "movement", "yes", "Minjung art", "scholarly pages without records"),
        ("SV179", "민주화운동 포스터", "민주화운동 포스터", "object/theme", "ko", "democratization movement poster", "protest poster", "", "광주", "yes", "first_ingest: minjung", "editorial", "", "Korean democratization poster query.", "minjung", "Hangul", "object_type", "yes", "democratization poster", "news pages"),
        ("SV180", "광주", "광주", "event/place", "ko", "Kwangju; Gwangju", "political event", "", "Minjung posters", "yes", "first_ingest: minjung", "editorial", "", "Kwangju/Gwangju query.", "minjung", "Hangul", "event", "no", "Gwangju", "place-only results"),
        ("SV181", "Singapore campaign posters", "singapore campaign posters", "object/theme", "en", "poster collection Singapore", "public information", "", "NLB", "yes", "first_ingest: sg_posters", "editorial", "", "Singapore poster query.", "sg_posters", "Latin", "object_type", "yes", "", "general heritage essays"),
        ("SV182", "public campaign Singapore poster", "public campaign singapore poster", "object/theme", "en", "campaign posters Singapore", "public information", "", "NLB", "yes", "first_ingest: sg_posters", "editorial", "", "Singapore campaign query.", "sg_posters", "Latin", "theme", "yes", "", "government pages without item records"),
        ("SV183", "مرتضی ممیز", "مرتضی ممیز", "person", "fa", "Morteza Momayyez", "Iranian graphic design", "", "پوستر", "yes", "first_ingest: iran_poster", "authority", "", "Persian designer query.", "iran_poster", "Arabic-derived Persian", "person", "yes", "Morteza Momayyez", "name variants"),
        ("SV184", "گرافیک ایران", "گرافیک ایران", "theme", "fa", "graphic arts Iran", "graphic design", "", "پوستر", "yes", "first_ingest: iran_poster", "editorial", "", "Persian graphic design query.", "iran_poster", "Arabic-derived Persian", "theme", "yes", "Iranian graphic arts", "contemporary studio pages"),
        ("SV185", "پوستر", "پوستر", "object type", "fa", "poster", "poster", "", "Iran", "yes", "first_ingest: iran_poster", "editorial", "", "Persian poster query.", "iran_poster", "Arabic-derived Persian", "object_type", "no", "poster", "too broad without Iran filters"),
        ("SV186", "Medu Art Ensemble", "medu art ensemble", "collective", "en", "Medu", "anti-apartheid graphics", "", "Culture and Resistance", "yes", "first_ingest: medu", "editorial", "", "Medu query.", "medu", "Latin", "collective", "yes", "", "recent exhibitions"),
        ("SV187", "Culture and Resistance", "culture and resistance", "event", "en", "Gaborone 1982", "anti-apartheid graphics", "", "Medu", "yes", "first_ingest: medu", "editorial", "", "Culture and Resistance query.", "medu", "Latin", "event", "yes", "", "generic culture/resistance phrasing"),
        ("SV188", "NAIDOC poster", "naidoc poster", "object/theme", "en", "NAIDOC posters", "Indigenous graphics", "", "Aboriginal land rights", "yes", "first_ingest: naidoc_land_rights", "editorial", "", "NAIDOC poster query.", "naidoc_land_rights", "Latin", "object_type", "yes", "", "recent publicity"),
        ("SV189", "Aboriginal land rights poster", "aboriginal land rights poster", "object/theme", "en", "First Nations posters", "Indigenous graphics", "", "NAIDOC", "yes", "first_ingest: naidoc_land_rights", "editorial", "", "Land-rights poster query.", "naidoc_land_rights", "Latin", "theme", "yes", "", "rights discussions not item records"),
        ("SV190", "First Nations posters", "first nations posters", "object/theme", "en", "Indigenous posters", "Indigenous graphics", "", "NAIDOC", "yes", "first_ingest: naidoc_land_rights", "editorial", "", "First Nations poster query.", "naidoc_land_rights", "Latin", "theme", "no", "", "Canada/Australia ambiguity"),
        ("SV191", "Brigadas Ramona Parra", "brigadas ramona parra", "collective", "es", "BRP", "Chilean graphics", "", "muralismo", "yes", "first_ingest: brp", "editorial", "", "BRP query.", "brp", "Latin", "collective", "yes", "", "contemporary social pages"),
        ("SV192", "muralismo", "muralismo", "theme", "es", "muralism", "public graphics", "", "propaganda politica", "yes", "first_ingest: brp", "editorial", "", "Muralism query.", "brp", "Latin", "theme", "no", "", "too broad without BRP/Chile filters"),
        ("SV193", "propaganda politica", "propaganda politica", "theme", "es", "propaganda política", "political graphics", "", "Chile", "yes", "first_ingest: brp", "editorial", "", "Spanish political propaganda query.", "brp", "Latin", "theme", "no", "", "broad political material"),
        ("SV194", "Gran Fury", "gran fury", "collective", "en", "ACT UP graphics", "queer graphics", "", "AIDS activist graphics", "yes", "first_ingest: gran_fury_actup", "authority", "", "Gran Fury query.", "gran_fury_actup", "Latin", "collective", "yes", "", "exhibition-only pages"),
        ("SV195", "ACT UP graphics", "act up graphics", "theme", "en", "AIDS posters", "queer graphics", "", "Gran Fury", "yes", "first_ingest: gran_fury_actup", "editorial", "", "ACT UP graphics query.", "gran_fury_actup", "Latin", "theme", "yes", "", "organizational pages without graphics"),
        ("SV196", "Silence=Death", "silence death", "campaign", "en", "Silence Equals Death", "AIDS activist graphics", "", "ACT UP", "yes", "first_ingest: gran_fury_actup", "editorial", "", "Campaign-specific query.", "gran_fury_actup", "Latin", "campaign", "no", "", "symbol/campaign attribution ambiguity"),
        ("SV197", "info.cern.ch", "info cern ch", "web source", "en", "first website", "web design", "", "CERN", "yes", "first_ingest: early_web_css_geocities", "URL", "", "First website source query.", "early_web_css_geocities", "Latin", "url", "yes", "", "retrospective pages"),
        ("SV198", "CSS1 Recommendation", "css1 recommendation", "web standard", "en", "Cascading Style Sheets level 1", "web standards", "", "W3C", "yes", "first_ingest: early_web_css_geocities", "W3C", "", "CSS standards query.", "early_web_css_geocities", "Latin", "standard", "yes", "", "CSS tutorials"),
        ("SV199", "GeoCities", "geocities", "platform", "en", "GeoCities preserved", "web archive", "", "Wayback", "yes", "first_ingest: early_web_css_geocities", "editorial", "", "GeoCities archive query.", "early_web_css_geocities", "Latin", "platform", "yes", "", "nostalgia pages without captures"),
        ("SV200", "Wayback Machine capture", "wayback machine capture", "web archive", "en", "archived URL", "web archive", "", "capture timestamp", "yes", "first_ingest: early_web_css_geocities", "Internet Archive", "", "Web capture query.", "early_web_css_geocities", "Latin", "source_type", "no", "", "not design-specific"),
    ]
    keys = [
        "term_id", "term", "normalized_term", "term_class", "language", "alternate_forms", "broader_term", "narrower_term",
        "related_terms", "preferred_for_query", "query_context", "authority_scheme", "authority_id", "notes",
        "query_profile_id", "script", "term_type", "preferred", "transliteration_of", "false_positive_note",
    ]
    upsert(DATA / "search_vocabulary.csv", "term_id", additions, [dict(zip(keys, row)) for row in terms])


def main() -> None:
    apply_experimental_scope()
    apply_movement_scope()
    apply_event_scope()
    apply_sources()
    apply_search_terms()


if __name__ == "__main__":
    main()
