# Texture benchmark

## Decision

`TEXTURE_JS_VERSION_TESTED=1.2.3`

`TEXTURE_JS_DECISION=TEXTURE_JS_REJECT_NATIVE_PATTERN`

Textures.js was evaluated from an isolated package artifact and is not a production dependency.

| Measure | Native SVG helper | Textures.js 1.2.3 |
| --- | ---: | ---: |
| Source raw bytes | 5,456 | 12,760 |
| Source gzip bytes | 1,605 | 2,394 |
| 100-def generation P50 | 0.251 ms | 0.299 ms |
| 100-def generation P95 | 0.350 ms | 0.676 ms |
| 100-def generation P99 | 0.723 ms | 1.256 ms |
| Serialized bytes | 23,417 | 25,980 |
| Deterministic IDs by default | true | false |
| Uses `Math.random` by default | false | true |
| React-declarative | true | false |

The native helper provides deterministic IDs, explicit encoded-variable/legend metadata, simple serializable definitions, and direct React SVG primitives. Textures.js provides no material v1 advantage and would introduce an unused imperative runtime dependency.

`trace-native-count-tier-v1` is a pure inclusive policy: 1–4 records use 12 px spacing / 1 px weight; 5–24 use 9 px / 1.1 px; 25–99 use 7 px / 1.2 px; and 100+ use 5 px / 1.2 px. The functional route visibly renders this tier legend and applies each pattern fill as an inline SVG style, so CSS cannot suppress the encoding. Policy-boundary adversaries and deterministic output pass.

Reported source/gzip measurements are not mislabelled as production client bundle deltas. Exact native helper bundle attribution remains part of the integrated build gate.

Sanitized evidence: `raw/spacetime-gis-benchmark-summary.json`.
