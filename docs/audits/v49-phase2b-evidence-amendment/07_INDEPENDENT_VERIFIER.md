# Independent promotion evidence verifier

The independent verifier is
`database/scripts/verify_phase2b_evidence_supersession.py`. It separately
re-hashes the original present checksum entries, bounds the missing set from
the original checksum ledger, verifies that the source tree lacks those paths,
re-checks the new package's hashes/index/ignore state, and reads every new
probe metadata record and raw stdout.

```text
PROMOTION_GATE_RESULT=PASS
PROMOTION_EVIDENCE_BASIS=AUDITED_P1_REPRODUCTION_SUPERSESSION
ORIGINAL_PRESENT_HASH_MATCH=61/61
ORIGINAL_MISSING_SET_BOUND=11/11
MISSING_SET_P1_ONLY=true
HISTORICAL_ARTIFACTS_RECOVERED=false
CORRECTIVE_PROBE_PASS=11/11
CORRECTIVE_PACKAGE_CHECKSUM=233/233
SEMANTIC_EQUIVALENCE_VERIFIED=true
INDEPENDENT_VERIFIER_P0=0
INDEPENDENT_VERIFIER_P1=0
EVIDENTIARY_GAP_CLOSED=true
```

The verifier does not lower the historical checksum gate: the original result
remains `61/72`. It accepts promotion only because the independent additive
supersession package is self-contained and its narrowly scoped reproduction
proves the same P1 roles without contradicting the retained Fresh A/B, digest,
scale-ladder, or public-boundary receipts.
