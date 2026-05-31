from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
CSV_OUT = ROOT / "data" / "source_dependency_ledger.csv"
MD_OUT = ROOT / "docs" / "system" / "SOURCE_DEPENDENCY_AND_TEXT_REFERENCES_v0.md"


SOURCE_META = {
    "Gallica / BnF APIs": {
        "source_id": "SRC023",
        "role": "National-library SRU/IIIF source for French posters, advertising, typography, printing, periodicals, and public-domain visual documents.",
        "reference_fields": "SRU Dublin Core title, creator, date, description, format, relation, publisher, rights, ark identifier; IIIF image URL/manifest.",
        "rights_dependency": "SRU dc:rights and Gallica/BnF item page; public-domain signals promote to IMG03, otherwise IIIF/source-hosted IMG02.",
        "text_dependency": "source_description, source_notes, OCR/description fields, format and relation notes; no uncited interpretation.",
        "scripts": "run_gallica_image_ready_1830_1970.py; run_gallica_secondary_image_ready_1830_1970.py",
    },
    "Wikimedia Commons": {
        "source_id": "SRC012",
        "role": "Open-license image supplement and discovery layer for poster/design-adjacent records; not treated as the original holding archive.",
        "reference_fields": "Commons page id, file description URL, imageinfo URL, extmetadata ObjectName, ImageDescription, Artist, Credit, Categories, LicenseShortName, LicenseUrl.",
        "rights_dependency": "Commons extmetadata license fields; only open-license records are admitted as IMG03 candidates.",
        "text_dependency": "file description, object name, categories, credit and artist metadata, with uncertainty because metadata may be user supplied.",
        "scripts": "run_wikimedia_commons_image_ready_1830_1970.py",
    },
    "Wellcome Collection Catalogue API": {
        "source_id": "SRC016",
        "role": "Public-health, exhibition, poster, print, and design-adjacent catalogue records with strong rights fields.",
        "reference_fields": "Catalogue work id, title, contributors, production date, description, subjects, thumbnail/IIIF/media links, rights/license fields.",
        "rights_dependency": "Wellcome item license/access fields; IMG02/IMG03 depends on explicit media evidence.",
        "text_dependency": "catalogue description, subjects, notes, collection context and rights statement.",
        "scripts": "run_image_ready_expansion_1931_1970.py",
    },
    "Library of Congress loc.gov API": {
        "source_id": "SRC006",
        "role": "Prints, posters, WPA/FSA material, trade cards, pamphlets, catalog records, and rights advisories.",
        "reference_fields": "loc.gov/PPOC id, title, contributor, date, notes, medium, repository, rights advisory, image/thumbnail fields, item URL.",
        "rights_dependency": "LoC item-level rights advisory; no universal public-domain assumption.",
        "text_dependency": "title, notes, summary, repository, subject, medium, and rights advisory.",
        "scripts": "run_early_region_capture_1830_1930.py; run_midcentury_capture_1930_1970.py",
    },
    "V&A Collections API": {
        "source_id": "SRC005",
        "role": "Design-object and collection metadata for posters, prints, ephemera, makers, object types, and collection context.",
        "reference_fields": "V&A system number, title, artist/maker, date, object type, materials/techniques, collection, image fields, item URL, rights/credit.",
        "rights_dependency": "V&A item rights and image permission statements; image presence does not imply reuse.",
        "text_dependency": "object metadata, physical description, collection context, maker/date fields.",
        "scripts": "run_early_region_capture_1830_1930.py; run_midcentury_capture_1930_1970.py",
    },
    "Art Institute of Chicago API": {
        "source_id": "SRC020",
        "role": "Museum object records for posters, prints, publications, dates, artist metadata, and IIIF image identifiers.",
        "reference_fields": "AIC artwork id, title, artist_display, date_display, place_of_origin, medium_display, classification_titles, image_id, is_public_domain.",
        "rights_dependency": "AIC is_public_domain and item page; IIIF URL alone is not enough for display promotion.",
        "text_dependency": "object metadata, classification, medium, artist/date/place fields.",
        "scripts": "run_early_region_capture_1830_1930.py; run_midcentury_capture_1930_1970.py",
    },
    "Internet Archive / text and periodical collections": {
        "source_id": "SRC025",
        "role": "Scanned books, manuals, periodicals, OCR, item metadata, and bibliography/context evidence.",
        "reference_fields": "identifier, title, creator, date, metadata API file list, item URL, collection, description, OCR/text availability.",
        "rights_dependency": "Item-level archive metadata and uploader/source terms; many records remain IMG00 or source-linked.",
        "text_dependency": "metadata description, OCR/excerpt, file list and item page; OCR requires verification before strong claims.",
        "scripts": "run_midcentury_expansion_capture_1931_1970.py",
    },
    "DigitalNZ": {
        "source_id": "SRC011",
        "role": "Aotearoa New Zealand aggregator for periodical, advertising, newspaper, and public visual communication records.",
        "reference_fields": "record id, title, display_date/date, description, subject, collection/content partner, rights, usage, landing URL, thumbnail URL.",
        "rights_dependency": "DigitalNZ rights and usage fields plus partner landing page; admitted IMG03 only when open-enough signals are present.",
        "text_dependency": "description, additional_description, subjects, collection, content partner and citation fields.",
        "scripts": "run_digitalnz_image_ready_1830_1970.py",
    },
    "The Met Open Access": {
        "source_id": "SRC001",
        "role": "Museum object records and public-domain/open-access comparison layer.",
        "reference_fields": "object id, title, artist, object date, medium, classification, department, culture, object URL, open-access/public-domain flags.",
        "rights_dependency": "Met Open Access/public-domain fields; current blockers remain IMG04 where image basis is insufficient.",
        "text_dependency": "object metadata, classification, medium, date, culture and collection fields.",
        "scripts": "run_midcentury_capture_1930_1970.py",
    },
    "Cleveland Museum Open Access API": {
        "source_id": "SRC022",
        "role": "Open-access museum object records with lower-risk image examples and object metadata.",
        "reference_fields": "accession/object id, title, creators, date, culture, type, technique, image URL, share/license fields.",
        "rights_dependency": "Cleveland open-access/license fields at item level.",
        "text_dependency": "object description, creators, technique, culture, type, department and rights fields.",
        "scripts": "run_early_region_capture_1830_1930.py",
    },
    "Getty Research Portal": {
        "source_id": "SRC000",
        "role": "Bibliographic and digitized design-history support records.",
        "reference_fields": "portal title, URL, source institution, bibliographic metadata and access link.",
        "rights_dependency": "Portal/provider terms; used as bibliography/context before image display.",
        "text_dependency": "bibliographic title, subject, source, notes and URL.",
        "scripts": "run_midcentury_expansion_capture_1931_1970.py",
    },
    "Chinese Posters": {
        "source_id": "SRC106",
        "role": "Specialist poster-history source for Chinese political and campaign graphics.",
        "reference_fields": "stable item or theme URL, title, date, creator/publisher if present, theme/category metadata, rights/source note.",
        "rights_dependency": "Specialist archive terms; link-only unless item display permission is explicit.",
        "text_dependency": "item description, theme context and specialist metadata.",
        "scripts": "run_midcentury_expansion_capture_1931_1970.py",
    },
    "Princeton University Library Digital Collections / Figgy": {
        "source_id": "SRC130",
        "role": "University-library Figgy/IIIF source for posters, broadsides, banners, advertising print, scanned visual resources, and ephemera.",
        "reference_fields": "Figgy catalog id, manifest label, metadata labels/values, date, extent/type, abstract/contents, manifest license, IIIF service/image URL.",
        "rights_dependency": "Manifest license field and Princeton source page; explicit public-domain/CC0 signals promote to IMG03, otherwise source-hosted IIIF remains IMG02.",
        "text_dependency": "manifest description, abstract, contents, extent/type, identifier and source metadata.",
        "scripts": "run_princeton_figgy_image_ready_1830_1970.py",
    },
    "Georgia State University Library Digital Collections / CONTENTdm": {
        "source_id": "SRC131",
        "role": "Local/university CONTENTdm source for labor, civil-rights, theatre, newspaper, urban, and public print-culture records.",
        "reference_fields": "CONTENTdm collection alias/item id, singleitem fields, title, date, creator, description, subject, location, format/type, local rights statement, IIIF imageUri.",
        "rights_dependency": "Item-level local rights statement; imageUri/IIIF availability is treated as source-hosted IMG02, not an open reuse grant.",
        "text_dependency": "CONTENTdm description, publication/collection fields, subjects, curatorial area, and source format fields.",
        "scripts": "run_gsu_contentdm_image_ready_1830_1970.py",
    },
}


def image_counts(surface_rows: list[dict]) -> Counter:
    return Counter((surface.get("image") or {}).get("state", "IMG00") for surface in surface_rows)


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    by_source: dict[str, list[dict]] = defaultdict(list)
    for surface in surfaces:
        by_source[surface.get("sourceName", "Unknown source")].append(surface)

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_name",
        "source_id",
        "surface_count",
        "img00",
        "img01",
        "img02",
        "img03",
        "img04",
        "dependency_role",
        "reference_fields",
        "rights_dependency",
        "text_dependency",
        "capture_scripts",
    ]
    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for source, items in sorted(by_source.items(), key=lambda item: (-len(item[1]), item[0])):
            counts = image_counts(items)
            meta = SOURCE_META.get(source, {})
            writer.writerow(
                {
                    "source_name": source,
                    "source_id": meta.get("source_id", ""),
                    "surface_count": len(items),
                    "img00": counts.get("IMG00", 0),
                    "img01": counts.get("IMG01", 0),
                    "img02": counts.get("IMG02", 0),
                    "img03": counts.get("IMG03", 0),
                    "img04": counts.get("IMG04", 0),
                    "dependency_role": meta.get("role", "Source role requires manual review."),
                    "reference_fields": meta.get("reference_fields", "Record-level fields require manual review."),
                    "rights_dependency": meta.get("rights_dependency", "Rights dependency requires manual review."),
                    "text_dependency": meta.get("text_dependency", "Text dependency requires manual review."),
                    "capture_scripts": meta.get("scripts", ""),
                }
            )

    lines = [
        "# Source Dependency and Text References v0",
        "",
        "Date: 2026-05-31",
        "",
        "This document defines what the current public archive surfaces depend on.",
        "It is generated from `generated/public_surfaces_v1.json` and the current",
        "source-policy mappings in `scripts/generate_source_dependency_reference.py`.",
        "",
        "The purpose is to keep About-page claims, source descriptions, and public",
        "text enrichment tied to inspectable source families rather than free-form",
        "interpretation.",
        "",
        "## Current Source Dependency Ledger",
        "",
        "| Source | Surfaces | IMG00 | IMG01 | IMG02 | IMG03 | IMG04 | Dependency |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for source, items in sorted(by_source.items(), key=lambda item: (-len(item[1]), item[0])):
        counts = image_counts(items)
        meta = SOURCE_META.get(source, {})
        lines.append(
            "| "
            + " | ".join(
                [
                    source,
                    str(len(items)),
                    str(counts.get("IMG00", 0)),
                    str(counts.get("IMG01", 0)),
                    str(counts.get("IMG02", 0)),
                    str(counts.get("IMG03", 0)),
                    str(counts.get("IMG04", 0)),
                    meta.get("role", "Requires manual review.").replace("|", "/"),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Text Dependency Rule",
            "",
            "Public text may use these layers only:",
            "",
            "1. Object/source record fields: title, creator, date, medium, collection, description, subject, rights, source URL.",
            "2. Raw capture metadata: API response path, source identifier, access date, parser status, image-state decision.",
            "3. Authority/context fields: controlled folder assignment, classification rationale, uncertainty note.",
            "4. Bibliographic/context sources: books, catalogues, exhibition texts, institutional pages, OCR snippets, or deep-research references, each with citation basis.",
            "",
            "No sentence should present influence, causality, movement membership, or historical significance as fact unless it is grounded in a source record, cited context, or explicitly marked as project inference.",
            "",
            "## About-Page Contract",
            "",
            "The About page should disclose:",
            "",
            "- current source families and counts;",
            "- the fields each family contributes;",
            "- rights/image dependencies;",
            "- text-enrichment boundaries;",
            "- open-source capture stack references;",
            "- that Commons and aggregator sources are discovery/display layers, not ownership claims.",
            "",
            f"CSV ledger: `{CSV_OUT.relative_to(ROOT)}`",
        ]
    )
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {CSV_OUT.relative_to(ROOT)}")
    print(f"wrote {MD_OUT.relative_to(ROOT)}")
    print(f"sources={len(by_source)} surfaces={len(surfaces)}")


if __name__ == "__main__":
    main()
