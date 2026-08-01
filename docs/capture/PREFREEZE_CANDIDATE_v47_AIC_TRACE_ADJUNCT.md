# Prefreeze candidate v47: AIC geographic balance and TRACE adjuncts

This is an isolated successor to the frozen v46 candidate. It does not modify
v46 or the official release layer.

## Active candidate addition

- Two active graphic carriers pass exact single-year, explicit `place_of_origin`,
  bounded carrier, source-page, authority, collection-evidence and TRACE gates.
- The new objects are a 1946 portfolio cover from Mexico City and an 1899 poster
  design from the Netherlands.
- Active total: 15,923. Remaining to the minimum 20,000-object target: 4,077.

## Photography and printmaking as TRACE media branches

- Eleven AIC records with explicit photography or printmaking media are stored
  in `generated/prefreeze_candidate_v47_aic_trace_adjuncts.json`.
- They are `countEligible=false`, have zero TRACE promotions, and contain no
  `influenced_by` edges. Their documented date, place, medium, source and image
  metadata remain searchable as auxiliary branches (`TRTREE048 / TRB166`).
- This records graphic practice as an expanded field without misclassifying
  artistic photography or printmaking as main archive objects. Future planar
  animation can enter the same layer only with equivalent source evidence.

## Image route decision

- Live HEAD checks on 2026-08-01 reached both AIC object URLs (301 to their
  canonical item pages) but received Cloudflare 403 responses from both direct
  IIIF image URLs.
- All v47 AIC records are therefore `IMG02` and source-viewer only. The direct
  IIIF URL remains evidence metadata; it is not treated as a reliable display
  frame and no image is downloaded locally.

## Validation

- `data/prefreeze_candidate_v47_search_gate.csv`: 9/9 PASS.
- `data/prefreeze_candidate_v47_sample_200_audit.csv`: 200 rows, including the
  two new active objects; all `audit_status=pass`.
- `data/prefreeze_candidate_v47.sqlite`: integrity check `ok`; 15,923 active
  objects and 11 non-active TRACE adjunct search documents.
