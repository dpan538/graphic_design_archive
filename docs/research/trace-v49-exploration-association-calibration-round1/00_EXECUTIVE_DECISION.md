# Executive decision

`ROUND14_DECISION=COMPLETE_WITH_LIMITATIONS`

Round 14 replaces the Round 13 precise-pair activation question with an evidence-grounded generic-association standard for local spatial coherence. The Python reference engine calibrates 35 cases across clear-positive, borderline, negative, source-channel, and hard-negative strata. It selects the same ordinal operating gate for direct and skip-one neighbourhoods:

```text
DIRECT_NEIGHBOUR_THRESHOLD=MIN_STRENGTH=MODERATE;MIN_CONFIDENCE=MODERATE;STATUS_IN={EXTERNALLY_SUPPORTED,SOURCE_SUPPORTED};HARD_GATES=D1>=1,D5>=1,D7>=1,CO_OCCURRENCE_ONLY=false
SKIP_ONE_THRESHOLD=MIN_STRENGTH=MODERATE;MIN_CONFIDENCE=MODERATE;STATUS_IN={EXTERNALLY_SUPPORTED,SOURCE_SUPPORTED};HARD_GATES=D1>=1,D5>=1,D7>=1,CO_OCCURRENCE_ONLY=false
```

The selected gate retains 21 associations and rejects 14, including every co-occurrence-only control. It does not assert a typed, causal, directional, statistical, or all-to-all historical relation. External human review is not complete, so the result remains limited; Round 15 internal engine research is safe to begin only with this package frozen and with no public renderer or public activation.
