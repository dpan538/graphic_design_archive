# Performance fix

Forward-only function 019 replaces the v5 internal builder without changing its output contract. The parity join now includes:

```sql
AND r.member_ordinal=e.member_ordinal
```

This matches the complete membership tuple and the existing folder/role/ordinal uniqueness boundary. The optimized diagnostic 2k plan removes zero rows, scans 6,107 inner rows, and completes the parity query in 4.511 ms. A transaction-scoped global builder advisory mutex also prevents unrelated releases from forming an SSI pivot through shared projection indexes while preserving per-release locks and the one-builder resource model.

No gate, timeout, fixture count, constraint, trigger, digest, reconciliation, or resource limit was weakened.
