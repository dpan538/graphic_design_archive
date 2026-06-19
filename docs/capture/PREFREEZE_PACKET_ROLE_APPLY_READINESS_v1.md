# Prefreeze Packet Role Apply Readiness v1

Scope: source-file join, confidence filtering, and sample queue for packet-role draft overrides.

This pass does not mutate capture records, does not rebuild the public payload, does not download images, and does not change rights or image states.

## Summary

- draft_rows_scanned: 2452 (Packet role draft rows scanned.)
- apply_ready_rows: 200 (Rows technically ready for a later applied override file.)
- hold_review_rows: 2091 (Rows held for sample/manual review.)
- reference_only_rows: 161 (Main-anchor keep references; no override needed.)
- sample_review_rows: 2270 (Deterministic sample queue for review.)
- status:hold_review: 2091 (Readiness status distribution.)
- status:apply_ready: 200 (Readiness status distribution.)
- status:reference_only: 161 (Readiness status distribution.)
- source_join:unique_capture_id: 2446 (Source-file join status distribution.)
- source_join:resolved_duplicate_capture_id: 3 (Source-file join status distribution.)
- source_join:ambiguous_capture_id: 2 (Source-file join status distribution.)
- source_join:missing_capture_id: 1 (Source-file join status distribution.)
- apply_ready_role:support_packet_appendix_text: 200 (Apply-ready role distribution.)
- reason:source family requires sample review before packet role application: 1253 (Top readiness reasons.)
- reason:region not stable enough for automatic packet role application: 675 (Top readiness reasons.)
- reason:unique source join and high-confidence packet-member subsheet demotion: 200 (Top readiness reasons.)
- reason:main-anchor keep reference; no demotion override needed: 161 (Top readiness reasons.)
- reason:card-related decisions require visual/editorial sample review: 149 (Top readiness reasons.)
- reason:historical/geography review period: 1939: 4 (Top readiness reasons.)
- reason:historical/geography review period: 1945: 4 (Top readiness reasons.)
- reason:source join not unique: ambiguous_capture_id: 2 (Top readiness reasons.)
- reason:historical/geography review period: 1940: 1 (Top readiness reasons.)
- reason:historical/geography review period: 1941: 1 (Top readiness reasons.)
- reason:source join not unique: missing_capture_id: 1 (Top readiness reasons.)
- reason:stamp/event/photo/context term requires review before packet role application: 1 (Top readiness reasons.)
- apply_ready_source:Gallica / BnF APIs: 106 (Top apply-ready source families/names.)
- apply_ready_source:DigitalNZ: 36 (Top apply-ready source families/names.)
- apply_ready_source:Princeton University Library Digital Collections / Figgy: 29 (Top apply-ready source families/names.)
- apply_ready_source:Wellcome Collection Catalogue API: 11 (Top apply-ready source families/names.)
- apply_ready_source:Georgia State University Library Digital Collections / CONTENTdm: 9 (Top apply-ready source families/names.)
- apply_ready_source:V&A Collections API: 5 (Top apply-ready source families/names.)
- apply_ready_source:Cleveland Museum Open Access API: 3 (Top apply-ready source families/names.)
- apply_ready_source:Art Institute of Chicago API: 1 (Top apply-ready source families/names.)

## Interpretation

- `apply_ready` rows are source-file-backed, high-confidence, and pass the stricter risk gate; they are still a small rebuild-test queue, not a final applied layer.
- `hold_review` rows remain useful for editorial planning but should not be applied automatically.
- Main-anchor keep rows are reference-only; they document packet anchors but do not need an override.
- Commons/Colnect file-page clusters, unstable regions, historical review periods, and stamp/event/photo/context terms are held for sample review.

## Next Use

- Review the sample queue by source family, region, and period.
- If sample review passes, create a separate applied override file from `apply_ready` rows only.
- Rebuild the candidate payload in chunks after applying a small tested override layer.
