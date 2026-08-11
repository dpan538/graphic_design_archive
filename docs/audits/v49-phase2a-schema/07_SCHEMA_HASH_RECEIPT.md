# v49 Phase 2A — Deterministic schema hash receipt

| Evidence | final1 | final2 |
|---|---|---|
| Raw schema dump bytes | 946,983 | 946,983 |
| Raw dump SHA-256 | `24cb8faf12dc9f1db535f25c5f9860263052b885b5c2465ad345596ee8639499` | `b2c7247aff01ad0529de15d89594dee4a9842a608ab963437c227de84156c348` |
| Normalized bytes | 738,816 | 738,816 |
| Normalized SHA-256 | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` |

Raw dumps differ only in dump-session noise. The normalizer removes permitted
session/non-semantic differences, preserves all schema definitions, sorts the
stable representation and emits a terminal LF. The two normalized byte
streams are byte-identical.

The Stable5 SQL/test set contains 37 files and has checksum-list SHA-256
`23d2e588c78de7a6756d5fe57117bb972dde453ba44c7b9eb3b4a9373d6f4473`.
The ordered list and every member digest are copied into
`database/schema-manifest.json`.

`SCHEMA_HASH_DETERMINISTIC=true`
