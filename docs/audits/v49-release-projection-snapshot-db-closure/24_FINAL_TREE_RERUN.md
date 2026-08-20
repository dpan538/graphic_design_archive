# Final tree rerun

Execution SHA: `1a2a2b9a0f9b43a00a5ebd360fac42d48d6aa5dc`.

Execution tree: `f52722a0a455804fe9c9974f965ce5b77f85a5b1`.

All ordered gates must be regenerated after the code/test/document structure is frozen. Raw outputs are written under `raw/final/`; the audit-only receipt commit records them without changing executable SQL or tests. Any post-freeze executable change invalidates the sequence and forces a fresh restart.

All database gates were regenerated from this execution tree. Two earlier frozen runs are retained under `raw/restarted-*` rather than represented as final: one reducer correction and one held-state reconciliation harness correction required new execution commits. The final API gate failed without an executable-tree change. The audit receipt commit adds only evidence/docs; final local/remote SHA, final tree hash, divergence, cleanliness, and checksum counts are reported by the non-self-referential handoff receipt after push.

`MANIFEST.txt` enumerates every formal payload file except the manifest and checksum file themselves. `CHECKSUMS.sha256` covers every payload plus `MANIFEST.txt`; it excludes only itself because a self-checksum cannot be stable. The final handoff reports both counts and the independent `shasum -a 256 -c` result.
