# P0 Rights Repair Preflight Rollup v1

This rollup combines the seven P0 image-rights repair preflights. It is advisory only and does not mutate records or upgrade IMG01/IMG03.

## P0 Totals

- source families: 7
- candidate rows: 511
- weighted gap points represented: 278.25
- automatic upgrades allowed: 0

## Recommendation Totals

- no_upgrade: 434 rows / 215.10 weighted points
- item_rights_capture_required: 37 rows / 25.90 weighted points
- source_visible_repair_needed: 35 rows / 35.00 weighted points
- review_only_no_automatic_upgrade: 4 rows / 1.80 weighted points
- review_rebuild_alignment_no_automatic_upgrade: 1 rows / 0.45 weighted points

## Source Summary

- Cooper Hewitt Collection GraphQL API: 137 rows / 61.65 pts; auto=0; Not a quick verified-open repair family; mostly copyright/restriction or credit-only local metadata.
- Wellcome Collection Catalogue API: 84 rows / 39.45 pts; auto=0; Not a quick verified-open repair family; includes legacy CC-BY-NC/ND placeholder risks.
- Library of Congress loc.gov API: 50 rows / 38.90 pts; auto=0; Best P0 deep-probe target; missing item image/rights capture is the main blocker.
- Georgia State University Library Digital Collections / CONTENTdm: 85 rows / 38.25 pts; auto=0; Mostly blocked by raw copyright/permission rights; one CC0 row needs manual rebuild review.
- Art Institute of Chicago API: 36 rows / 36.00 pts; auto=0; No current repair gain; raw search data mostly says is_public_domain=false.
- Internet Archive / text and periodical collections: 75 rows / 33.75 pts; auto=0; Reading/source support source; current repair queue lacks explicit open item licenses.
- V&A Collections API: 44 rows / 30.25 pts; auto=0; Useful for source-visible triage; object metadata does not provide bulk verified-open evidence.

## Next Actions

- Treat the P0 preflight as a negative rights-upgrade result: source-family reputation and source-hosted images are not enough to move IMG01/IMG03.
- Run a targeted LOC deep item/image-rights probe first because it has the clearest missing-evidence repair path.
- Patch GSU capture logic so local rights statements and image-display basis are preserved separately before any future GSU rebuild.
- Keep Wellcome, AIC, Internet Archive, V&A, and Cooper Hewitt as source-visible/context sources unless explicit item-level open evidence is captured.
- Shift the next 5,000-source capture tranche toward sources with explicit public-domain/open-license item fields and lower region coverage, instead of trying to mine verified-open gains from these P0 families.

## Output Files

- `data/p0_rights_repair_preflight_rollup_v1.csv`
- `data/p0_rights_repair_preflight_recommendations_v1.csv`
