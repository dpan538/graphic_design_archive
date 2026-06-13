# Image Rights Repair Preflight Batches v1

This preflight splits the image-rights repair queue into source-family execution batches. It does not fetch records, download images, mutate surfaces, or upgrade IMG01/IMG03.

## Safety Contract

- `automatic_upgrade_allowed=false` for every batch.
- Any future IMG03 repair requires item-level open-license or public-domain evidence from the source record.
- Source discovery and probe output should store metadata, source text, rights evidence, and source links only.
- Raw payloads, if produced in a later execution run, must be redacted and audited before commit.

## Batch Summary

- total source-family batches: 802
- P0 batches: 7
- P1 batches: 5
- P2 batches: 790
- estimated P0 weighted-gap points: 278.25
- estimated P0+P1 weighted-gap points: 382.45

## Repair Families

- img02_open_rights_review: 628
- img04_text_state_review: 168
- img00_source_visible_repair: 5
- img01_item_image_and_rights_review: 1

## P0 Execution Order

- `IMG-RIGHTS-BATCH-0001` Cooper Hewitt Collection GraphQL API: 137 candidates; 61.65 weighted points; img02_open_rights_review
- `IMG-RIGHTS-BATCH-0002` Wellcome Collection Catalogue API: 84 candidates; 39.45 weighted points; img02_open_rights_review
- `IMG-RIGHTS-BATCH-0003` Library of Congress loc.gov API: 50 candidates; 38.90 weighted points; img01_item_image_and_rights_review
- `IMG-RIGHTS-BATCH-0004` Georgia State University Library Digital Collections / CONTENTdm: 85 candidates; 38.25 weighted points; img02_open_rights_review
- `IMG-RIGHTS-BATCH-0005` Art Institute of Chicago API: 36 candidates; 36.00 weighted points; img00_source_visible_repair
- `IMG-RIGHTS-BATCH-0006` Internet Archive / text and periodical collections: 75 candidates; 33.75 weighted points; img02_open_rights_review
- `IMG-RIGHTS-BATCH-0007` V&A Collections API: 44 candidates; 30.25 weighted points; img02_open_rights_review

## Output File

- `data/image_rights_repair_preflight_batches_v1.csv`
