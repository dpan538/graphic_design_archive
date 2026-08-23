# Texture experiment

## Decision

`TEXTURE_JS_DECISION=TEXTURE_JS_REJECT_NATIVE_PATTERN`

Textures.js 1.2.3 was benchmarked from an isolated package artifact and was not added to `package.json` or the lockfile. The selected functional foundation keeps a small deterministic native SVG-pattern helper.

## Benchmark

The benchmark generated 100 definitions across several count-tier variants.

| Measure | Native helper | Textures.js 1.2.3 ESM |
| --- | ---: | ---: |
| Source raw bytes | 5,456 | 12,760 |
| Source gzip bytes | 1,605 | 2,394 |
| Generation P50 | 0.251 ms | 0.299 ms |
| Generation P95 | 0.350 ms | 0.676 ms |
| Generation P99 | 0.723 ms | 1.256 ms |
| Serialized bytes / 100 defs | 23,417 | 25,980 |
| Deterministic IDs by default | Yes | No |
| React-declarative | Yes | No; imperative selection API |
| Default random ID behavior | None | Uses `Math.random` |

Textures.js offers no material v1 benefit that outweighs a runtime dependency, imperative D3-selection integration, and default non-deterministic IDs. Its measured source gzip size is not presented as a production bundle delta; final bundle attribution belongs to the integrated build gate.

## Native contract

The helper accepts a namespace, family (`dots`, horizontal lines, diagonal lines), explicitly encoded variable, legend value, spacing, and weight. It derives a deterministic ID and a serializable pattern definition.

V1 texture mode encodes `record_count_tier`; it is not decorative. The accessible table retains exact counts and denominators, so pattern is never the sole carrier of information.

The pure `trace-native-count-tier-v1` policy is fixed and inclusive:

| Record count | Spacing | Weight |
| ---: | ---: | ---: |
| 1–4 | 12 px | 1 px |
| 5–24 | 9 px | 1.1 px |
| 25–99 | 7 px | 1.2 px |
| 100+ | 5 px | 1.2 px |

The functional route renders the same four tiers in a visible legend. Texture fills are applied with an inline SVG style, preventing stylesheet precedence from hiding the governed encoding.

## Compatibility boundary

Native definitions are plain data rendered through React `<pattern>` primitives and work in server/client SVG markup without an imperative selection object. They require no DOM at generation time and can be serialized for export. No hydration warning or external texture runtime is expected from the helper itself; integrated build/runtime evidence remains part of the final gate.
