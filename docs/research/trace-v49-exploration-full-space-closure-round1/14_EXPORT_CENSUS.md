# Export Census

Every reachable state has one `portrait_card` manifest under each frozen theme-token set. The exhaustive ledger therefore covers state × preset × theme. The counts below state whether every variant was rendered, decoded, validated, and rendered again for deterministic replay; unequal counts block closure.

| Metric | Value |
| --- | --- |
| Export variants | 11520 |
| Export manifests validated | 11520 |
| SVGs rendered | 11520 |
| SVGs validated | 11520 |
| SVG failures | 0 |
| SVG replay mismatches | 0 |
| PNGs rendered | 11520 |
| PNGs validated | 11520 |
| PNG failures | 0 |
| PNG replay mismatches | 0 |
| Map/tree state mismatches | 0 |
| Width | 1080 px |
| Height | 1620 px |

## Theme distribution

| Theme-token set | Count |
| --- | --- |
| neutral-contrast-v1 | 5760 |
| neutral-v1 | 5760 |

Export variants per state range from `2` to `2`. SVG and PNG binaries are temporary when large; the committed ledger preserves every identity, validation result, and replay hash. Each row covers manifest replay, SVG render/replay, PNG render/decode/replay, SVG-to-PNG equivalence, dimensions, map/tree zones, labels, visible associations, provenance non-claims, and zero forbidden exposure. Public/archive-object, held-data, Context, and Spacetime references must all remain zero.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv` and `docs/audits/v49-exploration-full-space-closure-round1/raw/png-validation-v2.tsv`.
