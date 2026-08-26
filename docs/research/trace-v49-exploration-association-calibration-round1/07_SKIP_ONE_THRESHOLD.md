# Skip-one threshold

Selected V1 gate: `MIN_STRENGTH=MODERATE;MIN_CONFIDENCE=MODERATE;STATUS_IN={EXTERNALLY_SUPPORTED,SOURCE_SUPPORTED};HARD_GATES=D1>=1,D5>=1,D7>=1,CO_OCCURRENCE_ONLY=false`.

The same gate is retained for graph distance two. The sweep did not justify weakening it: accepting `QUALIFIED` adds a false positive, while the visually encoded near-neighbour implication still requires inspectable evidence. Equality does not mean identical layout distance; it means the same minimum evidentiary eligibility. A failing skip-one check triggers restructuring or split after direct-edge repair.
