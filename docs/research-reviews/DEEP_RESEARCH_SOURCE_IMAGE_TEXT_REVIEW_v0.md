# Deep Research Source/Image/Text Review v0

Date: 2026-05-30

Source reports reviewed:

- `Rights-Aware Source Expansion Plan for Modern Graphic Design History.docx`
- `Rights-Aware Image Strategy for a Modern Graphic Design Archive Index.docx`
- `Text Enrichment Methodology for a Rights-Aware Archive Index of Modern Graphic Design History.docx`

## Main Finding

The three reports support the next production step. They do not require another
broad Deep Research pass before action.

The archive's weakness is not only record count. The current system is still
too dependent on museum-object APIs and therefore produces too many table-like
surfaces. The reports recommend three concrete corrections:

1. expand source connectors beyond API-first museums;
2. treat image display as rights classification, not scraping;
3. add grounded prose layers before the six evidence tables.

## Source Expansion Implication

The project should use a mixed connector model:

- API;
- OAI-PMH;
- IIIF;
- public search plus stable item pages;
- HTML item-page harvesting;
- manual or semi-manual link-only records;
- authority and vocabulary connectors.

This is a structural change in crawl planning, not a change in the public
interface. Region, Theme, Medium, and Movement remain the public folder axes.

Newly incorporated sources include:

- Chinese Posters;
- South Asia Open Archives;
- Palestinian Museum Digital Archive;
- Digital Library of the Caribbean;
- Hemeroteca Digital Brasileira;
- Hemeroteca Nacional Digital de Mexico;
- M68 Ciudadanias en Movimiento;
- Tasveer Ghar;
- Endangered Archives Programme;
- African Activist Archive;
- National Repository of Nigeria;
- Taiwan Memory;
- Shibusawa Shashi Database;
- National Archives of Singapore poster records;
- Papers Past;
- Te Papa Collections Online;
- Hungaricana;
- Getty Research Portal;
- Getty Vocabularies;
- VIAF;
- State Library of NSW.

The regenerated matrix now contains:

- 127 source rows;
- 85 source rows useful for 1931-1970;
- 35 P1 rows;
- 39 P2 rows.

## Image Strategy Implication

The project should use a rights-first image ladder:

1. `IMG03`: explicit open/reusable image evidence exists.
2. `IMG02`: source-hosted viewer, IIIF, or stable source image interface exists.
3. `IMG01`: controlled thumbnail display is plausible under source constraints.
4. `IMG00`: image likely exists, but local display is not permitted or not
   confirmed.
5. `IMG04`: no image frame should exist because the surface is text,
   authority, bibliography, appendix, or context-led.

`IMG04` must not be used for parser failure.

Parser status and public image state must be separated:

- public state: `IMG00` through `IMG04`;
- internal diagnostic state: `image_expectation`, `parser_status`,
  `rights_basis`, `display_mode`, and `rights_snapshot_date`.

If a visual source exists but cannot be displayed, the public page should show
an empty archival image frame with a rights/source explanation and a prominent
source link.

## Text Strategy Implication

The report confirms that the six evidence tables are not enough. They should
remain the audit layer, but every full main sheet needs a readable research note
before or beside those tables.

Text must be separated into four layers:

1. source text: raw catalog/finding-aid/exhibition/OCR/bibliographic text;
2. normalized summary: neutral paraphrase of source evidence;
3. editorial context note: why the record matters, grounded in cited sources;
4. interpretive claim: significance, influence, circulation, reception, or
   movement placement, only when cited or explicitly marked as inference.

The default prose target should be:

- object/work sheets: 100-250 words;
- thin-but-eligible sheets: 60-120 words, visibly flagged;
- folder introductions: 150-350 words;
- cards/stubs: shorter, not padded into fake completeness.

## Self-Supplied Content Boundary

If images cannot be displayed, the project may add:

- empty-frame image notes;
- editorial summaries;
- historical context notes;
- classification rationales;
- uncertainty notes;
- folder intros;
- bibliography and authority links.

The project should not create replacement images or illustrative reconstructions
for archive records. Generated or self-made visuals would not be source
evidence and would blur the difference between archive indexing and design
interpretation.

## Action Taken

Updated:

- `scripts/generate_source_expansion_matrix.py`
- `data/source_expansion_matrix.csv`
- `data/source_expansion_priority_1930_1970.csv`
- `SOURCE_EXPANSION_MATRIX_v0.md`

Added:

- `IMAGE_AND_TEXT_ENRICHMENT_RULES_v0.md`
- `NEXT_1931_1970_EXPANSION_PLAN_v0.md`

