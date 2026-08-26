# Association rubric

Each dimension is ordinal: 0 absent/contrary, 1 bounded/partial, 2 direct/strongly evidenced.

| Dimension | Meaning |
|---|---|
| D1 | contextual directness |
| D2 | recurrence within or across evidence units |
| D3 | source-family independence |
| D4 | design-history/domain alignment |
| D5 | historical specificity of period, place, actors, or case |
| D6 | cross-source or within-source consistency, with qualifications preserved |
| D7 | source-level directness: metadata 0, explicit primary/archive or scholarly indirect 1, direct external scholarship 2 |

D1≥1, D5≥1, D7≥1, and `cooccurrence_only=false` are hard gates. Strength is `STRONG` only when contextual directness is explicit, evidence recurs, and consistency is at least bounded; otherwise a gated, consistent case is `MODERATE`. Confidence is `HIGH` only with independent, directly aligned, consistent external evidence; the bounded fallback is `MODERATE`. No weights or normalized evidence score are used.
