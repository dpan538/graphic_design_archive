# Non-mainstream item/image capture quality audit v1

Generated: 2026-06-13

## Scope

- Input records: `data/capture_batch_nonmainstream_item_image_2026_records.csv`.
- Input source summary: `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`.
- Offline audit only: no network access, no image download, no source-record mutation, no frontend rebuild.
- All records remain IMG02; this audit does not grant IMG01/IMG03 rights state.

## Results

- Records audited: 587
- manual_review_before_surface: 349
- quarantine_not_counted: 237
- ready_for_item_review: 1

## Macro-region distribution

- Latin America: 292
- Eastern Europe: 94
- Africa: 88
- MENA: 44
- Southeast Asia: 37
- East Asia: 11
- Central Asia: 8
- South Asia: 6
- (blank): 5
- Oceania: 2

## Ready queue by macro-region

- Southeast Asia: 1

## Authority tiers

- museum: 304
- library: 151
- cultural_center: 46
- gallery: 24
- archive: 15
- national_library: 14
- university: 13
- national_museum: 12
- institute: 6
- national_archive: 2

## Main risk flags

- missing_design_signal: 546
- overbroad_country_or_region: 386
- low_surface_signal: 225
- generic_non_design_source: 20
- spam_or_seo_pollution: 12
- missing_country_or_region: 5
- qid_as_source_name: 4

## Design signal terms

- exhibition: 16
- grafico: 7
- logo: 5
- workshop: 5
- festival: 3
- catalog: 2
- grafica: 2
- visual art: 2
- historieta: 1
- humor grafico: 1
- cartel: 1
- comic: 1
- zine: 1
- catalogue: 1

## Ready queue examples

| capture_id | source | region | score | design terms |
| --- | --- | --- | ---: | --- |
| NMIIC2026R0396 | Asian Film Archive | Southeast Asia / Singapore | 11 | catalog; catalogue |

## Quarantine examples

| capture_id | source | reason |
| --- | --- | --- |
| NMIIC2026R0001 | Botswana Craft | generic_non_design_source; missing_design_signal; low_surface_signal |
| NMIIC2026R0003 | Goodman Gallery | missing_design_signal; low_surface_signal |
| NMIIC2026R0004 | Centre For Black And African Arts And Civilization | spam_or_seo_pollution; missing_design_signal |
| NMIIC2026R0013 | Cafesjian Center for the Arts | overbroad_country_or_region; missing_design_signal; low_surface_signal |
| NMIIC2026R0043 | Museum of Religious Art Bishop Fray José Antonio de San Alberto | overbroad_country_or_region; generic_non_design_source; missing_design_signal; low_surface_signal |
| NMIIC2026R0047 | Biblioteca Pública Municipal German Guzmán Campos | overbroad_country_or_region; missing_design_signal; low_surface_signal |
| NMIIC2026R0049 | Biblioteca Pública Municipal Senderos del Saber | missing_design_signal; low_surface_signal |
| NMIIC2026R0050 | Biblioteca Pública Municipal Prado Tolima | overbroad_country_or_region; missing_design_signal; low_surface_signal |
| NMIIC2026R0051 | Biblioteca Pública Municipal de Macanal | missing_design_signal; low_surface_signal |
| NMIIC2026R0052 | Biblioteca Pública Municipal de Pelaya | overbroad_country_or_region; missing_design_signal; low_surface_signal |

## Interpretation

- The batch has useful under-covered-region leads, but it is not safe to count all 587 records as successful active sources.
- `ready_for_item_review` records should enter a small item/surface review pass first; `manual_review_before_surface` records need geography and design-relevance confirmation.
- `quarantine_not_counted` records should not be included in success totals or rebuild inputs without source replacement or manual repair.
- Overbroad geography labels such as Caribbean or Caucasus need normalization before this batch can improve strict source coverage honestly.

## Output files

- `data/nonmainstream_item_image_capture_quality_v1.csv`
- `data/nonmainstream_item_image_capture_quality_summary_v1.csv`
- `data/nonmainstream_item_image_capture_ready_queue_v1.csv`
- `data/nonmainstream_item_image_capture_manual_review_v1.csv`
- `data/nonmainstream_item_image_capture_quarantine_v1.csv`
