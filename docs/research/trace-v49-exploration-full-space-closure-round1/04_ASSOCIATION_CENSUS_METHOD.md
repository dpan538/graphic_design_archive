# Association-census method

Let `N` be the frozen active-vocabulary count. The generator emits each canonical unordered distinct pair once, using the sorted stable vocabulary IDs as identity. It emits `N` self-pair exclusions separately and proves `N × (N - 1) / 2` pair rows with no duplicate or missing key.

Every pair ends in exactly one final status:

- `ACTIVE_EXTERNALLY_SUPPORTED`
- `ACTIVE_SOURCE_SUPPORTED`
- `INACTIVE_INSUFFICIENT_EVIDENCE`
- `INACTIVE_CONFLICTING_SCOPE`
- `INACTIVE_COOCCURRENCE_ONLY`
- `INACTIVE_HARD_NEGATIVE`

The Round 14 V1 threshold is unchanged: at least moderate strength, at least moderate confidence, evidence status externally supported or formally accepted source supported, and D1, D5, and D7 each at least one. Co-occurrence cannot pass. Evidence rows never encode a typed relation, and an inactive result states only that the documented protocol found no qualifying generic-association evidence.

For each pair the census checks, in order:

1. the complete Round 9–16 local source/evidence registries;
2. source texts and stored locators available in the repository;
3. the standardized external scholarly-discovery protocol when the local record is insufficient;
4. accepted/rejected source decisions and reasons;
5. D1–D7, strength, confidence, evidence status, threshold, qualification, and explicit non-claims.

The three Round 14 source-supported cases are re-examined. Each is either promoted with qualifying scholarly evidence, retained under the explicit final source-supported policy, or made inactive; no pending-validation phrase is permitted in an active final row.

All 35 Round 14 cases receive a reconciliation row. A case whose endpoint is not active is marked outside the active-pair universe but still records whether the historical decision, evidence, or method changed. No legacy decision changes silently.

