# Composition policy

The candidate record keeps five decisions separate: semantic eligibility, composition eligibility, neighbourhood role, topology role, and presentation role. A failed Round 14 association enters only as `NOT_QUALIFIED / INELIGIBLE / INELIGIBLE_CONTROL`; no later rule can convert it to `ADMITTED`.

## Strategy comparison

| Family | Determinism | Auditability | Caution | Degree control | Topology fit | Main risk | V1 result |
|---|---|---|---|---|---|---|---|
| ordinal lexicographic | high | high | medium | high | high | a final identifier tie-break becomes pseudo-ranking | component only |
| Pareto-style | high | high | high | medium | high | a large non-dominated frontier | selected foundation |
| diversity-aware | medium | medium | medium | high | medium | generic types become latent historical categories | deferred |
| minimal sufficient | high | high | high | high | high | may omit useful qualified alternatives | selected constraint |

`PARETO_MINIMAL_SUFFICIENT_V1` groups candidates by the existing Round 14 ordinal vector: strength, confidence, and D1/D5/D7 followed by the remaining rubric dimensions. It never converts these dimensions into a scalar, never ranks `EXTERNALLY_SUPPORTED` above `SOURCE_SUPPORTED`, and never ranks generic types. A full evidence group is admitted only if it fits the topology-derived bound. If equally evidenced candidates compete across the cutoff, they remain unresolved; canonical association identity is used only for serialization, never selection.

The degree limit of two comes from the frozen binary topology budget and Round 13 maximum sibling count, not an empirical claim about history. V1 keeps the smallest sufficient topology-bounded structure while preserving every non-admitted qualified candidate and explanation in the audit.
