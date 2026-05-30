# Next 1931-1970 Expansion Plan v0

Date: 2026-05-30

This plan follows the source expansion, image strategy, and text enrichment
reports. It is designed to reduce table-only sheets and rebalance the archive
away from the current AIC/V&A/LOC/Met-heavy preview.

## Purpose

The next crawl should not maximize record count. It should maximize usable
archive surfaces:

- richer readable text;
- clearer image-state routing;
- more global coverage;
- more source families;
- fewer thin standalone sheets.

## Mixed Source Set

Use five source groups in one expansion run.

| Role | Source group | Why |
|---|---|---|
| Open/viewer image source | NDL Digital Collections / NDL Search | Strong Japanese print and periodical source with persistent IDs, IIIF on many records, and item-level access/rights signals. |
| Text-rich periodical source | Hemeroteca Digital Brasileira or HNDM | Adds Brazilian or Mexican periodical/OCR context for advertising, magazines, public graphics, and print culture. |
| Non-Western regional source | Chinese Posters | High-yield, design-specific mainland Chinese poster and campaign connector. |
| Authority/context source | Getty Research Portal + Getty Vocabularies | Adds readable catalogues/books and stabilizes terms, people, media, and movement labels. |
| Targeted gap repair source | Europeana | Repairs Eastern Europe/socialist/post-socialist gaps with rights-aware metadata and provider links. |

Secondary alternates:

- Palestinian Museum Digital Archive for MENA and solidarity graphics;
- M68 Ciudadanias en Movimiento for Mexican 1968 political graphics;
- South Asia Open Archives for South Asian periodicals and texts;
- African Activist Archive for liberation/anti-apartheid solidarity graphics;
- Te Papa or State Library of NSW for rights-clear Oceania image tests.

## Expected Output

Target a smaller but higher-quality batch:

- 80-120 captured candidate rows;
- at least 30 text-rich records;
- at least 20 records with `IMG02` or `IMG03` potential;
- at least 20 non-Western regional records;
- at least 10 authority/context records;
- no table-only main sheets under the Reading Gate.

## Capture Rules

Every captured row must include:

- `source_name`;
- `provider`;
- `stable_item_url`;
- `access_method`;
- `record_family`;
- `title`;
- `date_start`, `date_end`, and `date_text`;
- `place`;
- `language` and `script` when available;
- `rights_statement_or_note`;
- `image_presence_code`;
- `image_expectation`;
- `parser_status`;
- `image_behavior_code`;
- `thumbnail_or_image_or_manifest`;
- `ocr_or_excerpt`;
- `source_description_raw`;
- `editorial_summary` candidate or summary seed;
- `person_or_institution_authority_links`;
- Region/Theme/Medium/Movement tags;
- citation seed;
- access date.

## Publication Rules

Main sheet:

- must pass the Reading Gate;
- must include readable prose before the evidence tables;
- must expose source and rights visibly;
- must not promote `IMG04` merely because image parsing failed.

Card:

- use when record identity and source are useful but the text/image evidence is
  too thin for a full sheet.

Compound page:

- use when a set, periodical issue, campaign, exhibition, or collection is more
  meaningful than isolated child sheets.

Fallback stub:

- use when historical relevance is clear but source capture is blocked or
  legally unsafe.

## Recommended Order

1. Probe NDL Digital Collections for `1931-1970` records using Japanese and
   English search terms.
2. Probe Chinese Posters for item-page structure and rights/display behavior.
3. Probe one Latin American periodical source, preferably Hemeroteca Digital
   Brasileira if automation is tolerable, otherwise HNDM.
4. Use Getty Research Portal for text-rich support records and Getty
   Vocabularies for normalization.
5. Use Europeana as a broad gap-repair connector, not as an image source by
   default.

## Success Criteria

The expansion succeeds if:

- the source mix is visibly broader than the current preview;
- table-only surfaces decrease;
- `IMG00` pages include meaningful empty-frame explanations;
- `IMG04` pages are genuinely text-led;
- every main sheet has at least one grounded reading note;
- source provenance and rights are still auditable.

