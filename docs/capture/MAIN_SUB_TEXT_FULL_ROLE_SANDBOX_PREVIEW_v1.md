# Main/Sub/Text Full Role Sandbox Preview v1

Scope: candidate-only sandbox preview of calibrated full-role card/sub/text candidates.

This pass does not write a generated payload JSON, mutate the official payload, download images, or change rights/image states.

## Override Summary

- base_override_rows: 2445 (Full-role sandbox preview statistic.)
- candidate_input_rows: 135 (Full-role sandbox preview statistic.)
- merged_override_rows: 2579 (Full-role sandbox preview statistic.)
- preview_applied: 134 (Full-role sandbox preview statistic.)
- preview_disposition:card: 126 (Full-role sandbox preview statistic.)
- preview_disposition:support_packet_appendix_text: 8 (Full-role sandbox preview statistic.)
- preview_role:card_context: 126 (Full-role sandbox preview statistic.)
- preview_role:sub_under_packet: 8 (Full-role sandbox preview statistic.)
- rejected_examples: 1 (Full-role sandbox preview statistic.)
- rejected_existing_override_collision: 1 (Full-role sandbox preview statistic.)
- rejected_rows: 1 (Full-role sandbox preview statistic.)
- sandbox_preview_overrides: 134 (Full-role sandbox preview statistic.)

## Delta Status

- `preview_disposition_applied`: 134

## Key Metric Deltas

- surfaces: 16175 -> 16175 (delta 0)
- active public sources: 14997 -> 14997 (delta 0)
- main sheets: 13537 -> 13403 (delta -134)
- cards: 1944 -> 2070 (delta 126)
- support packets: 692 -> 700 (delta 8)
- text templates: 94 -> 94 (delta 0)
- object source-visible rate: 98.92 -> 98.92 (delta 0.00)
- object verified-open rate: 95.29 -> 95.29 (delta 0.00)
- object weighted publication-grade rate: 97.26 -> 97.26 (delta 0.00)
- object IMG04 rate: 0.82 -> 0.82 (delta 0.00)

## Interpretation

- This preview tests structure only; it is not an archive-wide demotion.
- Source, object, rights, and image-state rates should remain stable because the same objects are retained with different roles.
- Card-heavy movement is expected because the calibrated candidates are mostly stamp/philatelic Commons records.

## Safety Notes

- No image files were downloaded.
- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, platform, or source-priority signals.
- The official payload and frontend mirrors were not edited.
