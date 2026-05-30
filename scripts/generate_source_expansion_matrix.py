#!/usr/bin/env python3
"""Generate a source expansion matrix for archive production planning.

This is not an ingest crawler. It normalizes the already researched source
universe into a decision table so future crawls can be chosen by coverage,
rights, reading value, and automation feasibility.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


OUTPUT_MATRIX = DATA / "source_expansion_matrix.csv"
OUTPUT_PRIORITY = DATA / "source_expansion_priority_1930_1970.csv"
OUTPUT_REVIEW = ROOT / "SOURCE_EXPANSION_MATRIX_v0.md"


CURRENT_CAPTURE_SOURCES = {
    "Art Institute of Chicago API",
    "V&A Collections API",
    "Library of Congress loc.gov API",
    "The Met Open Access",
}


REPORT_P1_SOURCES = {
    "Chinese Posters",
    "South Asia Open Archives",
    "Palestinian Museum Digital Archive",
    "Digital Library of the Caribbean",
    "Hemeroteca Digital Brasileira",
    "Hemeroteca Nacional Digital de Mexico",
    "M68 Ciudadanias en Movimiento",
    "Getty Research Portal",
    "Getty Vocabularies",
    "Europeana",
    "NDL Digital Collections",
}


ADDITIONAL_SOURCES = [
    {
        "source_expansion_id": "GSE085",
        "source_name": "National Library of India",
        "region": "South Asia",
        "source_type": "National library portal",
        "url": "https://www.nationallibrary.gov.in/",
        "access_method": "Web",
        "api_iiif_oai_data": "catalogue and digital-resource routes require verification",
        "likely_record_types": "books, periodicals, bibliography, institutional records",
        "graphic_design_relevance": "Indian publishing, multilingual typography, public communication context",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG00",
        "recommended_use": "deep research",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE086",
        "source_name": "National Digital Library of India",
        "region": "South Asia",
        "source_type": "National aggregator",
        "url": "https://ndl.iitkgp.ac.in/",
        "access_method": "Web + search",
        "api_iiif_oai_data": "access model requires verification",
        "likely_record_types": "books, reports, theses, institutional documents",
        "graphic_design_relevance": "design education, NID-related texts, public communication references",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG04",
        "recommended_use": "deep research",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE087",
        "source_name": "NID Archives and institutional publications",
        "region": "South Asia",
        "source_type": "Design school archive",
        "url": "https://www.nid.edu/",
        "access_method": "Web + manual PDF",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "institution pages, reports, curriculum/history texts, project pages",
        "graphic_design_relevance": "postcolonial design education and development communication",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG04",
        "recommended_use": "launch",
        "evidence": "existing FIT032-FIT033 targets",
    },
    {
        "source_expansion_id": "GSE088",
        "source_name": "Eames India Report",
        "region": "South Asia",
        "source_type": "Design text",
        "url": "https://www.nid.edu/",
        "access_method": "PDF/manual source",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "book/report/text source",
        "graphic_design_relevance": "foundational text node for Indian design infrastructure",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG04",
        "recommended_use": "launch",
        "evidence": "existing FIT033 target",
    },
    {
        "source_expansion_id": "GSE089",
        "source_name": "Design in India / India Design Council references",
        "region": "South Asia",
        "source_type": "Institutional/design policy source",
        "url": "https://www.indiadesigncouncil.org/",
        "access_method": "Web",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "institutional pages, reports, policy documents",
        "graphic_design_relevance": "design policy and professionalization context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG04",
        "recommended_use": "backup",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE090",
        "source_name": "Qatar Digital Library",
        "region": "Middle East and North Africa",
        "source_type": "Digital library",
        "url": "https://www.qdl.qa/",
        "access_method": "Web + IIIF-like viewer",
        "api_iiif_oai_data": "viewer and metadata; API needs verification",
        "likely_record_types": "archives, maps, books, photographs, printed matter",
        "graphic_design_relevance": "Arabic/Persian/colonial print and public visual culture context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "backup",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE091",
        "source_name": "Bibliotheca Alexandrina Digital Assets Repository",
        "region": "Middle East and North Africa",
        "source_type": "Digital library",
        "url": "https://dar.bibalex.org/",
        "access_method": "Web",
        "api_iiif_oai_data": "requires verification",
        "likely_record_types": "books, periodicals, visual documents",
        "graphic_design_relevance": "Arabic publishing and periodical design context",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG00",
        "recommended_use": "deep research",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE092",
        "source_name": "National Library of Israel",
        "region": "Middle East and North Africa",
        "source_type": "National library portal",
        "url": "https://www.nli.org.il/",
        "access_method": "Web + API routes to verify",
        "api_iiif_oai_data": "metadata and digital collection routes require verification",
        "likely_record_types": "posters, books, periodicals, ephemera, authority records",
        "graphic_design_relevance": "Hebrew/Arabic publishing, posters, institutional graphics",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "backup",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE093",
        "source_name": "Encyclopaedia Iranica / Iranian poster contextual records",
        "region": "Middle East and North Africa",
        "source_type": "Reference text",
        "url": "https://iranicaonline.org/",
        "access_method": "Web",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "reference text, person/movement authority context",
        "graphic_design_relevance": "Iranian poster and typography context when object records are thin",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG04",
        "recommended_use": "backup",
        "evidence": "existing Iranian poster gap",
    },
    {
        "source_expansion_id": "GSE094",
        "source_name": "Poster House Iranian design pages",
        "region": "Middle East and North Africa",
        "source_type": "Museum/exhibition text",
        "url": "https://posterhouse.org/",
        "access_method": "Web",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "exhibition pages, collection/context texts",
        "graphic_design_relevance": "text-rich entry into Iranian poster design and typography",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG04",
        "recommended_use": "backup",
        "evidence": "recommended FIT C11 set",
    },
    {
        "source_expansion_id": "GSE095",
        "source_name": "South African History Archive",
        "region": "Africa",
        "source_type": "Community/political archive",
        "url": "https://www.saha.org.za/",
        "access_method": "Web",
        "api_iiif_oai_data": "manual/catalogue pages",
        "likely_record_types": "posters, collection pages, political graphics, finding aids",
        "graphic_design_relevance": "anti-apartheid graphics, Medu posters, counterpublic design",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG00",
        "recommended_use": "launch",
        "evidence": "existing FIT037-FIT039 targets",
    },
    {
        "source_expansion_id": "GSE096",
        "source_name": "South African History Online",
        "region": "Africa",
        "source_type": "Historical/context archive",
        "url": "https://www.sahistory.org.za/",
        "access_method": "Web",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "articles, archive records, event texts",
        "graphic_design_relevance": "text-rich context for anti-apartheid visual communication",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG04",
        "recommended_use": "launch",
        "evidence": "existing FIT039-FIT040 targets",
    },
    {
        "source_expansion_id": "GSE097",
        "source_name": "Wits Historical Papers / Medu Art Ensemble resources",
        "region": "Africa",
        "source_type": "University archive",
        "url": "https://www.wits.ac.za/",
        "access_method": "Web + finding aids",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "finding aids, posters, archive descriptions, event records",
        "graphic_design_relevance": "Medu and anti-apartheid design context",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG00",
        "recommended_use": "backup",
        "evidence": "recommended C12 set",
    },
    {
        "source_expansion_id": "GSE098",
        "source_name": "Digital Innovation South Africa",
        "region": "Africa",
        "source_type": "Digital archive",
        "url": "https://disa.ukzn.ac.za/",
        "access_method": "Web",
        "api_iiif_oai_data": "requires verification",
        "likely_record_types": "periodicals, political texts, public materials",
        "graphic_design_relevance": "anti-apartheid periodical and campaign context",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG04",
        "recommended_use": "deep research",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE099",
        "source_name": "Trove",
        "region": "Oceania and Pacific",
        "source_type": "National aggregator",
        "url": "https://trove.nla.gov.au/",
        "access_method": "API + web",
        "api_iiif_oai_data": "API and newspaper text routes",
        "likely_record_types": "newspapers, magazines, books, images, web archive records",
        "graphic_design_relevance": "Australian print, advertising, public information and web culture",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "High",
        "default_image_zone": "IMG00",
        "recommended_use": "launch",
        "evidence": "existing source registry SRC010",
    },
    {
        "source_expansion_id": "GSE100",
        "source_name": "DigitalNZ",
        "region": "Oceania and Pacific",
        "source_type": "National aggregator",
        "url": "https://digitalnz.org/",
        "access_method": "API",
        "api_iiif_oai_data": "DigitalNZ API",
        "likely_record_types": "metadata records, partner links, thumbnails",
        "graphic_design_relevance": "Aotearoa/New Zealand distributed print, poster and visual culture",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "High",
        "default_image_zone": "IMG00",
        "recommended_use": "launch",
        "evidence": "existing source registry SRC011",
    },
    {
        "source_expansion_id": "GSE101",
        "source_name": "AIATSIS NAIDOC poster collection",
        "region": "Oceania and Pacific",
        "source_type": "Indigenous/community collection",
        "url": "https://aiatsis.gov.au/",
        "access_method": "Web + manual protocol review",
        "api_iiif_oai_data": "manual",
        "likely_record_types": "poster records, collection pages, protocol notes",
        "graphic_design_relevance": "Indigenous poster and public communication history",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low",
        "default_image_zone": "IMG03",
        "recommended_use": "launch",
        "evidence": "existing FIT041-FIT043 targets",
    },
    {
        "source_expansion_id": "GSE102",
        "source_name": "PANDORA / Australian Web Archive",
        "region": "Oceania and Pacific",
        "source_type": "Web archive",
        "url": "https://pandora.nla.gov.au/",
        "access_method": "Web",
        "api_iiif_oai_data": "search interface; web archive rules",
        "likely_record_types": "archived websites, online publications",
        "graphic_design_relevance": "born-digital Australian design and public communication",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG00",
        "recommended_use": "backup",
        "evidence": "existing source registry SRC019",
    },
    {
        "source_expansion_id": "GSE103",
        "source_name": "Internet Archive / text and periodical collections",
        "region": "Global / web / transnational",
        "source_type": "Repository",
        "url": "https://archive.org/",
        "access_method": "API + web",
        "api_iiif_oai_data": "metadata API; file lists; web viewer",
        "likely_record_types": "books, magazines, manuals, periodicals, scans",
        "graphic_design_relevance": "high-value text and periodical reservoir across all periods",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "High",
        "default_image_zone": "IMG00",
        "recommended_use": "launch",
        "evidence": "existing IA use in China/Hong Kong test",
    },
    {
        "source_expansion_id": "GSE104",
        "source_name": "HathiTrust Digital Library",
        "region": "Global / web / transnational",
        "source_type": "Digital library",
        "url": "https://www.hathitrust.org/",
        "access_method": "Metadata API + web",
        "api_iiif_oai_data": "metadata and bibliographic APIs; access varies",
        "likely_record_types": "books, trade catalogs, journals, bibliographic records",
        "graphic_design_relevance": "text-rich publication and bibliography layer",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med-High",
        "default_image_zone": "IMG04",
        "recommended_use": "backup",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE105",
        "source_name": "WorldCat / library authority discovery",
        "region": "Global / web / transnational",
        "source_type": "Bibliographic discovery",
        "url": "https://www.worldcat.org/",
        "access_method": "Web/API availability varies",
        "api_iiif_oai_data": "authority and bibliographic discovery only",
        "likely_record_types": "bibliographic records, holdings leads",
        "graphic_design_relevance": "source-finding layer for books, catalogues, manuals, periodicals",
        "rights_clarity": "High for citation, not image",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG04",
        "recommended_use": "authority only",
        "evidence": "project gap fill",
    },
    {
        "source_expansion_id": "GSE106",
        "source_name": "Chinese Posters",
        "region": "Mainland China",
        "source_type": "Poster-specific archive",
        "url": "https://chineseposters.net/",
        "access_method": "Public search + web item pages",
        "api_iiif_oai_data": "no public API/IIIF verified; stable item/theme pages",
        "likely_record_types": "posters, artists, publishers, campaigns, thematic collections, contextual text",
        "graphic_design_relevance": "high-yield mainland Chinese poster and campaign graphics connector",
        "rights_clarity": "Low-Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG00",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE107",
        "source_name": "South Asia Open Archives",
        "region": "South Asia",
        "source_type": "Periodical/text repository",
        "url": "https://www.jstor.org/site/saoa/",
        "access_method": "Public search + stable JSTOR item pages",
        "api_iiif_oai_data": "viewer/PDF-like access; API not assumed",
        "likely_record_types": "newspapers, periodicals, books, reports, political tracts, text sources",
        "graphic_design_relevance": "text-rich South Asian print, political, and publication context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG04",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE108",
        "source_name": "Palestinian Museum Digital Archive",
        "region": "Middle East and North Africa",
        "source_type": "Community/archive portal",
        "url": "https://palarchive.org/",
        "access_method": "Public search + web item pages",
        "api_iiif_oai_data": "source-hosted item pages; API not assumed",
        "likely_record_types": "posters, documents, newsletters, community archive items, authority/context text",
        "graphic_design_relevance": "Palestinian and transnational solidarity poster/documentary graphics",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE109",
        "source_name": "Digital Library of the Caribbean",
        "region": "Latin America and the Caribbean",
        "source_type": "Regional digital library",
        "url": "https://dloc.com/",
        "access_method": "Public search + downloads + web item pages",
        "api_iiif_oai_data": "stable item pages; file/download behavior varies by partner",
        "likely_record_types": "newspapers, periodicals, books, community records, tourism/labor/political texts",
        "graphic_design_relevance": "Caribbean periodicals, tourism graphics, labor/counterpublic print context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE110",
        "source_name": "Hemeroteca Digital Brasileira",
        "region": "Latin America and the Caribbean",
        "source_type": "Newspaper/periodical portal",
        "url": "https://bndigital.bn.gov.br/hemeroteca-digital/",
        "access_method": "Public search + viewer",
        "api_iiif_oai_data": "viewer/OCR behavior; automation friction expected",
        "likely_record_types": "newspapers, magazines, OCR text, issue/page records",
        "graphic_design_relevance": "Brazilian periodical design, advertising, architecture/design magazines, public campaigns",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG02",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE111",
        "source_name": "Hemeroteca Nacional Digital de Mexico",
        "region": "Latin America and the Caribbean",
        "source_type": "Newspaper/periodical portal",
        "url": "https://hndm.iib.unam.mx/",
        "access_method": "Public search + viewer",
        "api_iiif_oai_data": "viewer/page access; API not assumed",
        "likely_record_types": "newspapers, periodicals, advertisements, OCR/page records",
        "graphic_design_relevance": "Mexican periodicals, advertising, student movement and print culture context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE112",
        "source_name": "M68 Ciudadanias en Movimiento",
        "region": "Latin America and the Caribbean",
        "source_type": "Movement/community archive",
        "url": "https://m68.mx/",
        "access_method": "Public search + web item pages",
        "api_iiif_oai_data": "repository behavior; item granularity requires probe",
        "likely_record_types": "posters, documents, exhibition records, movement records, text/context sources",
        "graphic_design_relevance": "Mexican 1968 student movement graphics and political visual culture",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE113",
        "source_name": "Tasveer Ghar",
        "region": "South Asia",
        "source_type": "Visual culture archive/essay source",
        "url": "https://www.tasveerghar.net/",
        "access_method": "Public search + web pages",
        "api_iiif_oai_data": "manual/web-only",
        "likely_record_types": "calendar art, film posters, bazaar prints, labels, visual essays, authority/context text",
        "graphic_design_relevance": "South Asian popular visual culture and commercial print context",
        "rights_clarity": "Low",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG00",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE114",
        "source_name": "Endangered Archives Programme",
        "region": "Global / web / transnational",
        "source_type": "Project-based digital archive",
        "url": "https://eap.bl.uk/",
        "access_method": "Public search + IIIF/source viewer",
        "api_iiif_oai_data": "Universal Viewer/IIIF on sampled files",
        "likely_record_types": "periodicals, newspapers, books, community records, scanned files, text sources",
        "graphic_design_relevance": "regional print cultures and underdocumented periodical/newspaper materials",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE115",
        "source_name": "African Activist Archive",
        "region": "Africa",
        "source_type": "Community/political archive",
        "url": "https://africanactivist.msu.edu/",
        "access_method": "Public search + web item pages",
        "api_iiif_oai_data": "manual/web-only",
        "likely_record_types": "posters, newsletters, photographs, organization records, solidarity texts",
        "graphic_design_relevance": "anti-apartheid and liberation solidarity graphics, newsletters, campaign materials",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE116",
        "source_name": "National Repository of Nigeria",
        "region": "Africa",
        "source_type": "National repository",
        "url": "https://nigeriareposit.nln.gov.ng/",
        "access_method": "Public search + downloads",
        "api_iiif_oai_data": "Handle/URI and PDF behavior; API not assumed",
        "likely_record_types": "newspapers, periodicals, books, ministry publications, text sources",
        "graphic_design_relevance": "Nigeria Magazine, public communication, ministry print, post-independence visual culture",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG04",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE117",
        "source_name": "African Online Digital Library",
        "region": "Africa",
        "source_type": "Project/community portal",
        "url": "https://aodl.org/",
        "access_method": "Public web",
        "api_iiif_oai_data": "project-specific web pages",
        "likely_record_types": "community records, text/context pages, media items, web-like project resources",
        "graphic_design_relevance": "contextual African heritage and community archive support source",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Low-Med",
        "default_image_zone": "IMG04",
        "recommended_use": "context only",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE118",
        "source_name": "Taiwan Memory",
        "region": "East Asia",
        "source_type": "National memory portal",
        "url": "https://tm.ncl.edu.tw/",
        "access_method": "Public search + web item pages",
        "api_iiif_oai_data": "citation export and item pages; restricted items present",
        "likely_record_types": "books, photographs, local history, ephemera, authority/context text",
        "graphic_design_relevance": "Taiwanese print, commercial art, advertising, and local visual culture context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE119",
        "source_name": "Shibusawa Shashi Database",
        "region": "East Asia",
        "source_type": "Corporate history/bibliographic database",
        "url": "https://shashi.shibusawa.or.jp/",
        "access_method": "Public search + web pages",
        "api_iiif_oai_data": "manual/web-only",
        "likely_record_types": "company histories, chronologies, bibliographic records, authority/context text",
        "graphic_design_relevance": "Japanese corporate identity, packaging, advertising, and company-history context",
        "rights_clarity": "Med",
        "stable_identifier_quality": "Med",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG04",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE120",
        "source_name": "National Archives of Singapore Poster Collections",
        "region": "Southeast Asia",
        "source_type": "National archive/poster collection",
        "url": "https://www.nas.gov.sg/archivesonline/",
        "access_method": "Public search + web item pages + permissions workflow",
        "api_iiif_oai_data": "viewer/item pages; reuse permissions vary",
        "likely_record_types": "posters, public campaign materials, photographs, government records, text/context",
        "graphic_design_relevance": "Singapore multilingual public-information and civic campaign graphics",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE121",
        "source_name": "Papers Past",
        "region": "Oceania and Pacific",
        "source_type": "Newspaper/periodical portal",
        "url": "https://paperspast.natlib.govt.nz/",
        "access_method": "Public search + OCR + open-data subset",
        "api_iiif_oai_data": "METS/ALTO metadata for older newspapers; viewer",
        "likely_record_types": "newspapers, periodicals, OCR text, page images, advertisements",
        "graphic_design_relevance": "Aotearoa/New Zealand advertising, public notices, typography and periodical layout",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE122",
        "source_name": "Te Papa Collections Online",
        "region": "Oceania and Pacific",
        "source_type": "Museum collection",
        "url": "https://collections.tepapa.govt.nz/",
        "access_method": "Public web item pages",
        "api_iiif_oai_data": "item-level image and rights behavior; API not assumed",
        "likely_record_types": "posters, design objects, public campaign materials, photographs, text/context",
        "graphic_design_relevance": "New Zealand posters, design objects, protest/campaign graphics, exhibition records",
        "rights_clarity": "Med-High",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG03",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE123",
        "source_name": "Hungaricana",
        "region": "Eastern Europe",
        "source_type": "National/regional aggregator",
        "url": "https://hungaricana.hu/",
        "access_method": "Public search + web item pages",
        "api_iiif_oai_data": "searchable text/images; API not assumed",
        "likely_record_types": "books, periodicals, objects, photographs, text sources",
        "graphic_design_relevance": "Hungarian socialist/post-socialist periodicals, posters, local collections",
        "rights_clarity": "Med",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG02",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE124",
        "source_name": "Getty Research Portal",
        "region": "Global / web / transnational",
        "source_type": "Bibliographic/full-text portal",
        "url": "https://portal.getty.edu/",
        "access_method": "Public search",
        "api_iiif_oai_data": "full-text digitized publications and source links",
        "likely_record_types": "books, catalogues, exhibition texts, bibliographic records, text sources",
        "graphic_design_relevance": "design histories, exhibition catalogues, movement anthologies, regional monographs",
        "rights_clarity": "High",
        "stable_identifier_quality": "High",
        "automation_feasibility": "High",
        "default_image_zone": "IMG04",
        "recommended_use": "launch",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE125",
        "source_name": "Getty Vocabularies",
        "region": "Global / web / transnational",
        "source_type": "Authority/vocabulary service",
        "url": "https://www.getty.edu/research/tools/vocabularies/",
        "access_method": "API + LOD + downloadable data",
        "api_iiif_oai_data": "AAT/ULAN/TGN linked open data",
        "likely_record_types": "authority records, medium terms, person/studio/place identifiers, multilingual labels",
        "graphic_design_relevance": "normalization layer for medium, movement, place, and maker names",
        "rights_clarity": "High",
        "stable_identifier_quality": "High",
        "automation_feasibility": "High",
        "default_image_zone": "IMG04",
        "recommended_use": "authority only",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE126",
        "source_name": "VIAF",
        "region": "Global / web / transnational",
        "source_type": "Authority service",
        "url": "https://viaf.org/",
        "access_method": "Public service/API ecosystem",
        "api_iiif_oai_data": "authority clusters",
        "likely_record_types": "personal names, corporate names, multilingual aliases, authority records",
        "graphic_design_relevance": "designer, studio, institution, and variant-name reconciliation",
        "rights_clarity": "High",
        "stable_identifier_quality": "High",
        "automation_feasibility": "High",
        "default_image_zone": "IMG04",
        "recommended_use": "authority only",
        "evidence": "2026-05-30 source expansion report",
    },
    {
        "source_expansion_id": "GSE127",
        "source_name": "State Library of NSW Collection",
        "region": "Oceania and Pacific",
        "source_type": "State library collection",
        "url": "https://collection.sl.nsw.gov.au/",
        "access_method": "Public web item pages",
        "api_iiif_oai_data": "item pages with copyright status and image behavior",
        "likely_record_types": "posters, photographs, printed ephemera, books, public campaign materials",
        "graphic_design_relevance": "Australian poster, exhibition, cinema, festival, and public campaign graphics",
        "rights_clarity": "Med-High",
        "stable_identifier_quality": "High",
        "automation_feasibility": "Med",
        "default_image_zone": "IMG03",
        "recommended_use": "source probe",
        "evidence": "2026-05-30 image strategy report",
    },
]


PERIODS = ["1830-1930", "1931-1970", "1971-2000", "2001-2026"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def source_key(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def classify_record_family(text: str) -> str:
    text_l = text.lower()
    families: list[str] = []
    rules = [
        ("periodical_newspaper", ["newspaper", "magazine", "periodical", "journal"]),
        ("poster_print_object", ["poster", "print", "ephemera", "object", "photograph", "image"]),
        ("book_catalogue_text", ["book", "catalogue", "manual", "report", "pdf", "text"]),
        ("authority_context", ["authority", "people", "organization", "institution", "entity"]),
        ("web_born_digital", ["web", "website", "interface", "born-digital"]),
        ("archive_finding_aid", ["finding aid", "archive", "archival", "collection"]),
    ]
    for label, needles in rules:
        if any(needle in text_l for needle in needles):
            families.append(label)
    return ";".join(families or ["mixed_discovery"])


def text_value(row: dict[str, str]) -> str:
    record_text = " ".join(
        [
            row.get("likely_record_types", ""),
            row.get("graphic_design_relevance", ""),
            row.get("source_type", ""),
        ]
    ).lower()
    if any(x in record_text for x in ["newspaper", "periodical", "magazine", "book", "report", "catalogue", "article", "text"]):
        return "High"
    if any(x in record_text for x in ["archive", "finding aid", "institutional", "authority"]):
        return "Med"
    return "Low-Med"


def image_value(row: dict[str, str]) -> str:
    zone = row.get("default_image_zone", "")
    record_text = row.get("likely_record_types", "").lower()
    if zone == "IMG03":
        return "High-open"
    if zone == "IMG02":
        return "High-viewer"
    if any(x in record_text for x in ["poster", "print", "image", "photograph", "object", "ephemera"]):
        return "High-restricted"
    if zone == "IMG04":
        return "Low-none"
    return "Med"


def crawl_difficulty(row: dict[str, str]) -> str:
    access = row.get("access_method", "").lower()
    auto = row.get("automation_feasibility", "").lower()
    recommended = row.get("recommended_use", "").lower()
    if "avoid" in recommended:
        return "blocked"
    if "api" in access or "dataset" in access or "oai" in access:
        return "low"
    if "high" in auto:
        return "low"
    if "low" in auto:
        return "high"
    return "medium"


def period_fit(row: dict[str, str]) -> dict[str, str]:
    text = " ".join(
        [
            row.get("source_name", ""),
            row.get("source_type", ""),
            row.get("likely_record_types", ""),
            row.get("graphic_design_relevance", ""),
        ]
    ).lower()

    fit = {period: "secondary" for period in PERIODS}

    if any(x in text for x in ["rare", "type specimen", "historical newspapers", "lithograph", "chromolithograph"]):
        fit["1830-1930"] = "strong"
    if any(x in text for x in ["poster", "public communication", "propaganda", "corporate", "institution", "postwar", "design education", "periodical", "magazine", "newspaper", "manual"]):
        fit["1931-1970"] = "strong"
    if any(x in text for x in ["counterpublic", "political", "poster", "zine", "digital", "web", "identity", "community"]):
        fit["1971-2000"] = "strong"
    if any(x in text for x in ["web", "born-digital", "platform", "contemporary", "open data"]):
        fit["2001-2026"] = "strong"

    return fit


def needs_deep_research(row: dict[str, str], family: str, difficulty: str) -> str:
    region = row.get("region", "")
    recommended = row.get("recommended_use", "").lower()
    rights = row.get("rights_clarity", "").lower()
    access = row.get("access_method", "").lower()
    if "deep research" in recommended:
        return "yes"
    if region in {"South Asia", "Middle East and North Africa", "Africa"} and difficulty != "low":
        return "yes"
    if "low" in rights and "api" not in access:
        return "yes"
    if family == "mixed_discovery" and difficulty == "high":
        return "yes"
    return "no"


def priority_1930_1970(row: dict[str, str], fit: dict[str, str], family: str, difficulty: str) -> str:
    name = row.get("source_name", "")
    recommended = row.get("recommended_use", "").lower()
    if name in CURRENT_CAPTURE_SOURCES:
        return "P3 already sampled; use for targeted gap fill only"
    if fit["1931-1970"] != "strong":
        return "P4 later period support"
    if "avoid" in recommended or difficulty == "blocked":
        return "P5 do not crawl now"
    if name in REPORT_P1_SOURCES:
        if "authority" in family:
            return "P1 authority/context crawl"
        if "periodical_newspaper" in family or "book_catalogue_text" in family:
            return "P1 text-rich crawl"
        return "P1 object/image crawl"
    if "authority only" in recommended:
        return "P3 authority enrichment"
    if difficulty == "low" and ("periodical_newspaper" in family or "book_catalogue_text" in family):
        return "P1 text-rich crawl"
    if difficulty == "low" and "poster_print_object" in family:
        return "P1 object/image crawl"
    if row.get("region") in {"South Asia", "Middle East and North Africa", "Africa", "Oceania and Pacific"}:
        return "P2 global-balance manual or semi-manual"
    if difficulty == "medium":
        return "P2 source probe"
    return "P3 manual/link-only"


def normalize_rows() -> list[dict[str, str]]:
    candidates = read_csv(DATA / "global_source_expansion_candidates.csv") + ADDITIONAL_SOURCES

    rows: list[dict[str, str]] = []
    for idx, source in enumerate(candidates, start=1):
        family = classify_record_family(
            " ".join(
                [
                    source.get("source_type", ""),
                    source.get("likely_record_types", ""),
                    source.get("graphic_design_relevance", ""),
                ]
            )
        )
        fit = period_fit(source)
        difficulty = crawl_difficulty(source)
        deep = needs_deep_research(source, family, difficulty)
        status = "sampled_in_active_preview" if source.get("source_name") in CURRENT_CAPTURE_SOURCES else "candidate"
        if source.get("recommended_use", "").lower() == "avoid":
            status = "hold_avoid"
        elif source.get("recommended_use", "").lower() in {"authority only", "context only"}:
            status = "context_or_authority"

        rows.append(
            {
                "matrix_id": f"SEM{idx:03d}",
                "source_expansion_id": source.get("source_expansion_id", ""),
                "source_name": source.get("source_name", ""),
                "region": source.get("region", ""),
                "source_type": source.get("source_type", ""),
                "url": source.get("url", ""),
                "access_method": source.get("access_method", ""),
                "api_iiif_oai_data": source.get("api_iiif_oai_data", ""),
                "record_family": family,
                "period_1830_1930": fit["1830-1930"],
                "period_1931_1970": fit["1931-1970"],
                "period_1971_2000": fit["1971-2000"],
                "period_2001_2026": fit["2001-2026"],
                "image_value": image_value(source),
                "text_value": text_value(source),
                "rights_clarity": source.get("rights_clarity", ""),
                "stable_identifier_quality": source.get("stable_identifier_quality", ""),
                "automation_feasibility": source.get("automation_feasibility", ""),
                "crawl_difficulty": difficulty,
                "default_image_zone": source.get("default_image_zone", ""),
                "recommended_use": source.get("recommended_use", ""),
                "priority_1930_1970": priority_1930_1970(source, fit, family, difficulty),
                "source_status": status,
                "deep_research_needed": deep,
                "use_notes": source.get("graphic_design_relevance", ""),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_review(rows: list[dict[str, str]], priority_rows: list[dict[str, str]]) -> str:
    by_region = Counter(row["region"] for row in rows)
    by_priority = Counter(row["priority_1930_1970"].split(" ", 1)[0] for row in rows)
    by_deep = Counter(row["deep_research_needed"] for row in rows)

    p1 = [row for row in priority_rows if row["priority_1930_1970"].startswith("P1")]
    p2 = [row for row in priority_rows if row["priority_1930_1970"].startswith("P2")]

    def table(items: list[dict[str, str]], limit: int = 20) -> str:
        lines = [
            "| Source | Region | Access | Record family | Image | Text | Why next |",
            "|---|---|---|---|---|---|---|",
        ]
        for row in items[:limit]:
            lines.append(
                "| {source_name} | {region} | {access_method} | {record_family} | {image_value} | {text_value} | {priority_1930_1970} |".format(
                    **row
                )
            )
        return "\n".join(lines)

    region_lines = "\n".join(f"- {region}: {count}" for region, count in sorted(by_region.items()))

    return f"""# Source Expansion Matrix v0

Date: 2026-05-30

This file turns the researched source universe into an execution matrix. It is
not a claim of full coverage. It is a control surface for deciding which source
families to crawl next, which sources remain link-only, and which gaps still
need Deep Research.

## Generated Files

- `data/source_expansion_matrix.csv`
- `data/source_expansion_priority_1930_1970.csv`

## Scope

- Total source rows: {len(rows)}
- 1931-1970 priority rows: {len(priority_rows)}
- P1 rows: {by_priority.get("P1", 0)}
- P2 rows: {by_priority.get("P2", 0)}
- Sources requiring targeted Deep Research: {by_deep.get("yes", 0)}

## Region Counts

{region_lines}

## Interpretation

The current live preview is structurally useful but source-poor. It uses AIC,
V&A, Library of Congress, and Met records heavily, so it proves the sheet system
can run but does not yet prove historical coverage. The next crawl should not
simply ask the same APIs for more records. It should deliberately rebalance
toward:

- text-rich periodical, newspaper, catalogue, and institutional sources;
- open or viewer-based image sources that can reduce `IMG00` table-only pages;
- non-Western and underrepresented regional sources;
- authority/context pages that can become real `IMG04` reading pages rather
  than failed-image placeholders.

## P1 1931-1970 Sources

{table(p1, 24)}

## P2 1931-1970 Sources

{table(p2, 28)}

## Deep Research Need

No broad Deep Research pass is needed before the next mechanical step. We now
have enough source candidates to expand the 1931-1970 crawl intelligently.

Deep Research should be used only for targeted holes where access, rights, or
local source names are still weak:

- South Asia beyond NID and the Eames India Report;
- MENA and Iranian/Arabic/Persian/Hebrew typography/poster sources;
- Africa beyond South Africa/Medu;
- Korea and Mainland China source APIs and rights;
- Latin America machine access for Brazil, Mexico, Argentina, Cuba, and
  Caribbean materials;
- Oceania/Pacific and Indigenous protocol handling beyond AIATSIS/Trove.

## Next Production Recommendation

For the next 1931-1970 expansion run, choose a mixed set:

1. one open/viewer image source,
2. one text-rich periodical/newspaper source,
3. one non-Western regional source,
4. one authority/context text source,
5. one existing API source only for targeted gap repair.

This should increase reading pages and image-bearing sheets without making the
archive dependent on copying images locally.
"""


def main() -> None:
    rows = normalize_rows()
    priority_rows = [
        row
        for row in rows
        if row["period_1931_1970"] == "strong"
        and not row["priority_1930_1970"].startswith(("P4", "P5"))
    ]
    priority_rows.sort(
        key=lambda row: (
            row["priority_1930_1970"],
            row["region"],
            row["source_name"],
        )
    )

    write_csv(OUTPUT_MATRIX, rows)
    write_csv(OUTPUT_PRIORITY, priority_rows)
    OUTPUT_REVIEW.write_text(build_review(rows, priority_rows), encoding="utf-8")

    print(f"Wrote {OUTPUT_MATRIX.relative_to(ROOT)} ({len(rows)} rows)")
    print(f"Wrote {OUTPUT_PRIORITY.relative_to(ROOT)} ({len(priority_rows)} rows)")
    print(f"Wrote {OUTPUT_REVIEW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
