# Prefreeze Candidate Promotion Blockers v1

Scope: non-mutating promotion blocker audit over the pre-freeze candidate payload. The script does not edit capture records, official payloads, frontend files, rights states, or image files.

## Summary

- candidate_surfaces_scanned: 16175 (Candidate surfaces scanned for promotion blockers.)
- promotion_blocker_rows: 7285 (Total blocker rows; a surface may have more than one blocker.)
- geo_repair_rows: 4938 (Unresolved-region rows requiring geography repair.)
- exclusion_delta_rows: 0 (New P0 source_file + capture_id suggestions not already in current exclusion table.)

## By Severity

- P1: 7283
- P0: 2

## By Blocker Type

- unresolved_region: 4938
- event_photo_or_context_image: 2166
- source_visible_gap: 181

## Top Unresolved Geography Sources

- Internet Archive / text and periodical collections: 61
- Wellcome Collection Catalogue API: 54
- Library of Congress loc.gov API: 38
- Wikimedia Commons: 38
- Georgia State University Library Digital Collections / CONTENTdm: 37
- Another Graphic: 14
- The Met Open Access: 14
- V&A Collections API: 8
- Art Institute of Chicago API: 6
- Smithsonian Open Access: 5
- African Digital Heritage: 3
- Barjeel Art Foundation: 3
- Getty Research Portal: 3
- National Repository of Nigeria: 2
- Cleveland Museum Open Access API: 1

## Exclusion Delta

- none

## Next Cleaning Order

1. Apply or review duplicate exact image URL deltas first; they are the smallest high-confidence loss.
2. Repair unresolved geography before using region coverage as a promotion metric.
3. Reclassify event/photo/context-image rows manually; they are not included in the automatic exclusion delta because false positives can include designed affiches/posters.
4. Review IMG00/IMG04 source-visible gaps; do not upgrade rights states without source evidence.

## Safety

- No image files were downloaded.
- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, platform, or source-priority signals.
- Candidate exclusion rows are recommendations only until a future gate merge is explicitly run.
