# Main/Sub/Text Calibration Second Pass v1

Scope: Codex second-pass calibration over the 80-row queue, enriched with candidate payload context.

This pass does not apply overrides, rebuild surfaces, download images, or change rights/image states.

## Gate

- Agreement rate: 98.75%.
- Fail rate: 0.00%.
- Confirmed candidate preview rows: 7.
- Sandbox gate status: `codex_calibrated_preview_only`.

The gate remains preview-only. A future override still needs an explicit sandbox apply step.

## Second-Pass Role Distribution

- `card_context`: 27.
- `sub_under_packet`: 17.
- `manual_hold`: 15.
- `main_needs_text`: 14.
- `keep_main`: 7.

## Decision Distribution

- `accept_initial`: 79.
- `revise_initial`: 1.

## Fail / Revision Patterns

- `none`: 52.
- `parent_needs_named_anchor`: 17.
- `stamp_or_commemorative_context`: 10.
- `natural_history_topic_design_object_context`: 1.

## Interpretation

- The second pass uses richer payload context to catch overbroad card/appendix/sub/main decisions.
- Stamp, commemorative, geography, false-positive, and parent-selection issues remain manual-first.
- Confirmed candidate rows are preview-only and should not be applied until the project explicitly creates a sandbox override layer.
