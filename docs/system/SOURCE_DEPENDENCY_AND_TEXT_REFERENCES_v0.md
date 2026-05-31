# Source Dependency and Text References v0

Date: 2026-05-31

This document defines what the current public archive surfaces depend on.
It is generated from `generated/public_surfaces_v1.json` and the current
source-policy mappings in `scripts/generate_source_dependency_reference.py`.

The purpose is to keep About-page claims, source descriptions, and public
text enrichment tied to inspectable source families rather than free-form
interpretation.

## Current Source Dependency Ledger

| Source | Surfaces | IMG00 | IMG01 | IMG02 | IMG03 | IMG04 | Dependency |
|---|---:|---:|---:|---:|---:|---:|---|
| Gallica / BnF APIs | 239 | 0 | 0 | 15 | 224 | 0 | National-library SRU/IIIF source for French posters, advertising, typography, printing, periodicals, and public-domain visual documents. |
| Cooper Hewitt Collection GraphQL API | 137 | 0 | 0 | 137 | 0 | 0 | Requires manual review. |
| Wikimedia Commons | 111 | 0 | 0 | 0 | 111 | 0 | Open-license image supplement and discovery layer for poster/design-adjacent records; not treated as the original holding archive. |
| Wellcome Collection Catalogue API | 89 | 3 | 0 | 81 | 5 | 0 | Public-health, exhibition, poster, print, and design-adjacent catalogue records with strong rights fields. |
| Georgia State University Library Digital Collections / CONTENTdm | 85 | 0 | 0 | 85 | 0 | 0 | Local/university CONTENTdm source for labor, civil-rights, theatre, newspaper, urban, and public print-culture records. |
| Library of Congress loc.gov API | 50 | 0 | 37 | 0 | 0 | 13 | Prints, posters, WPA/FSA material, trade cards, pamphlets, catalog records, and rights advisories. |
| Art Institute of Chicago API | 45 | 35 | 0 | 0 | 9 | 1 | Museum object records for posters, prints, publications, dates, artist metadata, and IIIF image identifiers. |
| V&A Collections API | 44 | 0 | 0 | 25 | 0 | 19 | Design-object and collection metadata for posters, prints, ephemera, makers, object types, and collection context. |
| Princeton University Library Digital Collections / Figgy | 41 | 0 | 0 | 41 | 0 | 0 | University-library Figgy/IIIF source for posters, broadsides, banners, advertising print, scanned visual resources, and ephemera. |
| Te Papa Collections Online | 32 | 0 | 0 | 32 | 0 | 0 | Aotearoa/New Zealand museum source for posters, protest graphics, music-publicity print, and public visual communication outside the dominant European/North American canon. |
| Internet Archive / text and periodical collections | 30 | 29 | 0 | 0 | 1 | 0 | Scanned books, manuals, periodicals, OCR, item metadata, and bibliography/context evidence. |
| NAIDOC Poster Gallery | 26 | 0 | 0 | 26 | 0 | 0 | Official Indigenous Australian poster-gallery source for annual NAIDOC poster item records. |
| DigitalNZ | 21 | 0 | 0 | 0 | 21 | 0 | Aotearoa New Zealand aggregator for periodical, advertising, newspaper, and public visual communication records. |
| The Met Open Access | 15 | 0 | 0 | 0 | 0 | 15 | Museum object records and public-domain/open-access comparison layer. |
| Cleveland Museum Open Access API | 12 | 0 | 0 | 0 | 12 | 0 | Open-access museum object records with lower-risk image examples and object metadata. |
| Biblioteca Nacional Digital de Chile / Memoria Chilena | 3 | 0 | 0 | 3 | 0 | 0 | National-library and memory-archive source for Chilean political poster, mural, and movement print culture. |
| Getty Research Portal | 3 | 0 | 0 | 0 | 0 | 3 | Bibliographic and digitized design-history support records. |
| South African History Archive | 3 | 0 | 0 | 3 | 0 | 0 | Community/political archive source for anti-apartheid, Medu, labor, and resistance poster histories. |
| NAIDOC / AIATSIS | 2 | 0 | 0 | 0 | 0 | 2 | Indigenous Australian authority/context source for NAIDOC poster history and collection-level poster routes. |
| Roots.sg / National Heritage Board Singapore | 2 | 0 | 0 | 2 | 0 | 0 | Singapore national heritage source for multilingual signs, commercial objects, and everyday public graphic systems. |
| Chinese Posters | 1 | 1 | 0 | 0 | 0 | 0 | Specialist poster-history source for Chinese political and campaign graphics. |

## Text Dependency Rule

Public text may use these layers only:

1. Object/source record fields: title, creator, date, medium, collection, description, subject, rights, source URL.
2. Raw capture metadata: API response path, source identifier, access date, parser status, image-state decision.
3. Authority/context fields: controlled folder assignment, classification rationale, uncertainty note.
4. Bibliographic/context sources: books, catalogues, exhibition texts, institutional pages, OCR snippets, or deep-research references, each with citation basis.

No sentence should present influence, causality, movement membership, or historical significance as fact unless it is grounded in a source record, cited context, or explicitly marked as project inference.

## About-Page Contract

The About page should disclose:

- current source families and counts;
- the fields each family contributes;
- rights/image dependencies;
- text-enrichment boundaries;
- open-source capture stack references;
- that Commons and aggregator sources are discovery/display layers, not ownership claims.

CSV ledger: `data/source_dependency_ledger.csv`
