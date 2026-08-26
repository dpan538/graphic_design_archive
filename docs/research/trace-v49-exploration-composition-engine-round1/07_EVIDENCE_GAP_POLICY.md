# Evidence-gap policy

An evidence gap is an explicit inquiry state supplied by a research fixture or future reviewed input. It is never inferred from missing co-occurrence, graph distance, a failed association, or an empty search result.

V1 serializes gap node identity, `EVIDENCE_GAP`, `EXPLICIT_UNRESOLVED_EVIDENCE`, and a presentation hint. The internal renderer uses equal node size and a dashed outline plus the text “unresolved evidence.” It does not draw a failed edge, red cross, zero score, or negative label.

Evidence gaps affect the semantic-core hash because adding or removing one changes the research claim about what remains unresolved. Cosmetic gap placement affects only the presentation hash.
