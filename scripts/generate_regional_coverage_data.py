from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


regions_fields = [
    "region_id",
    "region_name",
    "parent_region_id",
    "region_type",
    "priority",
    "coverage_reason",
    "known_bias_risk",
    "language_scope",
    "script_scope",
    "source_strategy",
    "notes",
]

regions = [
    {
        "region_id": "REG001",
        "region_name": "Western and Central Europe",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Many canonical modern graphic design movements and institutions are indexed here, but the region must be decomposed rather than treated as Europe-as-default.",
        "known_bias_risk": "Overrepresented in existing canon; risk of becoming the implicit center.",
        "language_scope": "English; German; French; Dutch; Italian; Spanish; others",
        "script_scope": "Latin",
        "source_strategy": "Museum APIs; national libraries; poster archives; design school archives; periodicals; exhibition catalogues.",
        "notes": "Must include both canonical and non-canonical production, not only Bauhaus/Swiss/modernism.",
    },
    {
        "region_id": "REG002",
        "region_name": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Important for constructivism, socialist visual communication, poster cultures, state design, publishing, and post-socialist design histories.",
        "known_bias_risk": "Often compressed into Russian/Soviet references or omitted from Western survey narratives.",
        "language_scope": "Polish; Czech; Slovak; Hungarian; Romanian; Bulgarian; Serbian; Croatian; Ukrainian; Russian; others",
        "script_scope": "Latin; Cyrillic",
        "source_strategy": "National libraries; poster museums; Europeana; university archives; state archives; periodical repositories.",
        "notes": "Needs separate tracking for USSR, non-Russian Soviet republics, and socialist/non-aligned countries.",
    },
    {
        "region_id": "REG003",
        "region_name": "North America",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Important for advertising, corporate identity, editorial design, design education, community graphics, digital media, and counterpublic archives.",
        "known_bias_risk": "High digitization may overstate centrality; U.S. sources can dominate Canada, Mexico, and Indigenous histories.",
        "language_scope": "English; French; Spanish; Indigenous languages",
        "script_scope": "Latin; Indigenous scripts where applicable",
        "source_strategy": "Museum APIs; Library of Congress; DPLA; university special collections; community archives; web archives.",
        "notes": "Do not collapse North America into U.S. modernism.",
    },
    {
        "region_id": "REG004",
        "region_name": "Latin America and the Caribbean",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Essential for poster cultures, political graphics, publishing, modernisms, national identity systems, and anti-colonial/decolonial visual communication.",
        "known_bias_risk": "Often appears only as revolution/poster imagery or isolated modernist cases.",
        "language_scope": "Spanish; Portuguese; French; English; Indigenous languages; Caribbean creoles",
        "script_scope": "Latin",
        "source_strategy": "National libraries; poster archives; university archives; museum collections; periodicals; political graphics archives.",
        "notes": "Needs country-level and transnational routes, including Cuba, Mexico, Brazil, Argentina, Chile, and Caribbean contexts.",
    },
    {
        "region_id": "REG005",
        "region_name": "Japan",
        "parent_region_id": "REG007",
        "region_type": "country_context",
        "priority": "Launch",
        "coverage_reason": "Essential for modern poster design, typography, magazine culture, postwar design, corporate identity, packaging, and interface/game/platform visual cultures.",
        "known_bias_risk": "Frequently represented through a small canon of poster designers while everyday publishing, advertising, and digital design are under-indexed.",
        "language_scope": "Japanese; English",
        "script_scope": "Kanji; Hiragana; Katakana; Latin",
        "source_strategy": "National Diet Library; museum collections; design museum archives; magazine/advertising archives; poster collections; web archives.",
        "notes": "Requires multilingual search terms and Japanese script support from the start.",
    },
    {
        "region_id": "REG006",
        "region_name": "Korea",
        "parent_region_id": "REG007",
        "region_type": "country_context",
        "priority": "Launch",
        "coverage_reason": "Essential for Hangul typography, print modernization, postwar visual culture, corporate identity, political graphics, publishing, and contemporary digital/platform design.",
        "known_bias_risk": "Often missing from English-language design history frameworks or folded into generic East Asia.",
        "language_scope": "Korean; English",
        "script_scope": "Hangul; Hanja; Latin",
        "source_strategy": "National libraries; museum collections; design archives; university repositories; poster and magazine archives; web archives.",
        "notes": "Needs Korean-language search vocabulary and authority strategy.",
    },
    {
        "region_id": "REG007",
        "region_name": "East Asia",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Necessary as a transnational frame for China, Japan, Korea, Taiwan, Hong Kong, and regional visual circulation.",
        "known_bias_risk": "Risk of flattening distinct histories into a single regional label.",
        "language_scope": "Chinese; Japanese; Korean; English; others",
        "script_scope": "Han characters; Kana; Hangul; Latin",
        "source_strategy": "National libraries; museum collections; regional archives; periodicals; web archives; bilingual source registry.",
        "notes": "Use as parent region only; most records should also have more specific country/city context.",
    },
    {
        "region_id": "REG008",
        "region_name": "Mainland China",
        "parent_region_id": "REG007",
        "region_type": "country_context",
        "priority": "Launch",
        "coverage_reason": "Essential for modern print culture, typography, propaganda, book and magazine design, commercial graphics, socialist visual communication, reform-era design, branding, web/interface culture, and platform-native visual communication.",
        "known_bias_risk": "Often reduced to propaganda posters or absent from global graphic design surveys.",
        "language_scope": "Chinese; English",
        "script_scope": "Simplified Chinese; Traditional Chinese in historical contexts; Latin",
        "source_strategy": "National and university libraries; poster collections; museum collections; periodical archives; book databases; web archives; bilingual/manual indexing.",
        "notes": "Needs careful periodization: late Qing print, Republican Shanghai, socialist state design, reform-era commercial design, contemporary digital platforms.",
    },
    {
        "region_id": "REG009",
        "region_name": "Hong Kong",
        "parent_region_id": "REG007",
        "region_type": "city/territory_context",
        "priority": "Launch",
        "coverage_reason": "Important for bilingual typography, film and entertainment graphics, publishing, advertising, identity, protest graphics, and regional circulation.",
        "known_bias_risk": "Often folded into either British colonial or Chinese frameworks without local media specificity.",
        "language_scope": "Chinese; Cantonese; English",
        "script_scope": "Traditional Chinese; Latin",
        "source_strategy": "University archives; museum collections; film/poster archives; periodicals; web archives; community archives.",
        "notes": "Needs distinct treatment because of bilingual, colonial, commercial, and activist visual cultures.",
    },
    {
        "region_id": "REG010",
        "region_name": "Taiwan",
        "parent_region_id": "REG007",
        "region_type": "country/territory_context",
        "priority": "Launch",
        "coverage_reason": "Important for print modernization, political graphics, publishing, typography, identity, advertising, and contemporary digital culture.",
        "known_bias_risk": "Often absent from English-language frameworks or merged into broader Chinese design history.",
        "language_scope": "Chinese; Taiwanese Hokkien; Japanese historical materials; English",
        "script_scope": "Traditional Chinese; Kana in historical contexts; Latin",
        "source_strategy": "National libraries; museum archives; university repositories; periodicals; poster archives; web archives.",
        "notes": "Needs separate tracking of Japanese colonial, postwar, democratization, and contemporary periods.",
    },
    {
        "region_id": "REG011",
        "region_name": "Southeast Asia",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Important for colonial print, multilingual typography, advertising, political graphics, tourism, publishing, and contemporary platform design.",
        "known_bias_risk": "Often nearly invisible in graphic design history surveys.",
        "language_scope": "Indonesian; Malay; Thai; Vietnamese; Filipino languages; Khmer; Burmese; English; French; Dutch; Chinese; others",
        "script_scope": "Latin; Thai; Khmer; Burmese; Han; Arabic-derived scripts; others",
        "source_strategy": "National libraries; colonial archives; university repositories; newspaper archives; museum collections; community archives.",
        "notes": "Needs country-by-country decomposition.",
    },
    {
        "region_id": "REG012",
        "region_name": "South Asia",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Essential for multilingual typography, publishing, film graphics, political posters, state information design, advertising, and digital design.",
        "known_bias_risk": "Often reduced to craft, film posters, or postcolonial case studies.",
        "language_scope": "Hindi; Bengali; Urdu; Tamil; Telugu; Malayalam; Marathi; Sinhala; Nepali; English; others",
        "script_scope": "Devanagari; Bengali; Perso-Arabic; Tamil; Telugu; Malayalam; Latin; others",
        "source_strategy": "National libraries; film poster archives; university archives; newspaper archives; design schools; public information archives.",
        "notes": "Must model multilingual script and typography as primary, not peripheral.",
    },
    {
        "region_id": "REG013",
        "region_name": "Middle East and North Africa",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Important for Arabic/Persian/Hebrew typography, publishing, political graphics, posters, advertising, and modernist/postcolonial visual cultures.",
        "known_bias_risk": "Often omitted or treated only through political poster material.",
        "language_scope": "Arabic; Persian; Hebrew; Turkish; French; English; others",
        "script_scope": "Arabic; Hebrew; Latin",
        "source_strategy": "National libraries; poster archives; university collections; museum collections; periodicals; community archives.",
        "notes": "Requires script-aware search and right-to-left interface considerations later.",
    },
    {
        "region_id": "REG014",
        "region_name": "Africa",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Essential for decolonial graphics, print cultures, political posters, publishing, advertising, vernacular commercial graphics, and contemporary digital design.",
        "known_bias_risk": "High risk of underrepresentation due to digitization and archive access gaps.",
        "language_scope": "Arabic; English; French; Portuguese; Swahili; Amharic; Yoruba; Hausa; Zulu; Xhosa; others",
        "script_scope": "Latin; Arabic; Ethiopic; others",
        "source_strategy": "National libraries; university archives; poster/political collections; newspaper archives; community archives; oral histories.",
        "notes": "Should be decomposed regionally and nationally; avoid continent-as-single-category treatment.",
    },
    {
        "region_id": "REG015",
        "region_name": "Oceania and Pacific",
        "parent_region_id": "",
        "region_type": "macro_region",
        "priority": "Launch",
        "coverage_reason": "Important for Australian, Aotearoa New Zealand, Pacific, Indigenous, migrant, public information, and web/archive contexts.",
        "known_bias_risk": "Australian/New Zealand institutional data can overshadow Pacific and Indigenous visual communication.",
        "language_scope": "English; Maori; Indigenous Australian languages; Pacific languages; others",
        "script_scope": "Latin; Indigenous scripts/orthographies where applicable",
        "source_strategy": "Trove; DigitalNZ; PANDORA; national libraries; Indigenous/community archives; museum collections.",
        "notes": "Needs community protocols and culturally sensitive metadata handling.",
    },
]


coverage_matrix_fields = [
    "coverage_id",
    "node_id",
    "region_id",
    "coverage_status",
    "priority",
    "known_entry_points",
    "source_needs",
    "rights_risk",
    "research_note",
]

coverage_matrix = []
coverage_id = 1
for region in regions:
    for node_id in [f"HN{i:03d}" for i in range(1, 16)]:
        priority = region["priority"]
        status = "planned"
        note = "Coverage must be validated with region-specific sources before claims are made."
        if region["region_id"] in {"REG001", "REG003"}:
            status = "seeded"
        if region["region_id"] in {"REG005", "REG006", "REG008", "REG009", "REG010"}:
            status = "launch_research_required"
        coverage_matrix.append(
            {
                "coverage_id": f"COV{coverage_id:04d}",
                "node_id": node_id,
                "region_id": region["region_id"],
                "coverage_status": status,
                "priority": priority,
                "known_entry_points": "",
                "source_needs": "Regional archives; national libraries; periodicals; museum collections; design texts; community archives",
                "rights_risk": "unknown",
                "research_note": note,
            }
        )
        coverage_id += 1


regional_source_priority_fields = [
    "priority_id",
    "region_id",
    "source_need_type",
    "priority",
    "examples_to_research",
    "reason",
    "status",
]

regional_source_priorities = []
priority_id = 1
for region in regions:
    for source_need_type, reason in [
        ("national_library", "Needed for books, periodicals, newspapers, bibliographic records, and public-domain material."),
        ("museum_collection", "Needed for posters, prints, design objects, exhibition histories, and institutional metadata."),
        ("design_archive", "Needed for designers, studios, schools, ephemera, and professional histories."),
        ("periodical_newspaper_archive", "Needed for advertising, editorial design, typography, and commercial print ecology."),
        ("community_archive", "Needed for protest graphics, underdocumented histories, zines, and counterpublics."),
        ("web_archive", "Needed for born-digital, interface, platform, and contemporary visual communication."),
    ]:
        regional_source_priorities.append(
            {
                "priority_id": f"RSP{priority_id:04d}",
                "region_id": region["region_id"],
                "source_need_type": source_need_type,
                "priority": region["priority"],
                "examples_to_research": "",
                "reason": reason,
                "status": "needs_research",
            }
        )
        priority_id += 1


def main() -> None:
    write_csv(DATA / "regions.csv", regions_fields, regions)
    write_csv(DATA / "coverage_matrix.csv", coverage_matrix_fields, coverage_matrix)
    write_csv(DATA / "regional_source_priorities.csv", regional_source_priority_fields, regional_source_priorities)


if __name__ == "__main__":
    main()
