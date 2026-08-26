# Direct-neighbour threshold

Selected V1 gate: `MIN_STRENGTH=MODERATE;MIN_CONFIDENCE=MODERATE;STATUS_IN={EXTERNALLY_SUPPORTED,SOURCE_SUPPORTED};HARD_GATES=D1>=1,D5>=1,D7>=1,CO_OCCURRENCE_ONLY=false`.

The sweep compares five ordinal policies. Strong-only policies produce no extra false-positive safety but omit moderate, source-supported, and bounded local transitions. Allowing `QUALIFIED` creates the first unsupported activation. The selected configuration therefore occupies the conservative usable boundary: 21/21 expected positives retained and 14/14 expected negatives rejected in this bounded set.

A failing direct edge is never silently retained. A terminal leaf is pruned; a failing branch is pruned; an internal failure splits the composition.
