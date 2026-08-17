# Phase 2S-P performance checkpoint

`PHASE_STATUS=PARTIAL_PERFORMANCE_CHECKPOINT`

The final code tree is `00241aa` (v5 protocol).  It corrected the proven
assignment current-leaf error and replaced the unbounded component aggregate
with 1,024-row chunk digests.  The final 32-object correctness test passed.

The final scale ladder stopped at 2,000 objects: builder wall time was
86,370.397 ms against the 75,000 ms gate, and the 1,000→2,000 exponent was
1.725873519, above 1.35.  The measured publishable-assignment function also
grew from 3,402.258 ms to 19,125.186 ms.  Per the Phase 2S-P stop rule, this
package records no 4,000, 8,000, full A/B, concurrency, or final matrix PASS.

No timeout was increased, constraint disabled, hash semantics weakened,
production database contacted, or protected branch advanced.
