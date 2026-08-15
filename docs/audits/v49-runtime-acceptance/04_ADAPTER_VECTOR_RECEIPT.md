# Adapter runtime vector receipt

The runner `frontend/scripts/run-runtime-acceptance-vectors.mjs` uses the real API route dispatcher and a minimal injected fetch seam. It never opens TCP and does not duplicate API serialization. It defines the required query-vector categories: current/exact descriptors, overview, folder types/list/detail, two keyset pages, surface/not-found, deterministic search, empty TRACE atlas/objects, ineligible neighborhood, relation registry, invalid/cross-release cursors, release mismatch, cancellation, and unsupported method.

Execution 1 (exit 1) stopped at `current-descriptor semantic mismatch`. Root cause: the runner incorrectly compared repository instances instead of descriptors. The runner was corrected to compare only the version descriptor.

Execution 2 (exit 1) stopped at `folder-detail semantic mismatch`. Root cause: `HttpArchiveRepository.getFolder({type, slug})` encoded `region/africa` as one documented folder-id segment. The adapter was repaired to obtain the matching bounded folder id before fetching folder detail. A second narrow TypeScript check passed after that repair.

The command was not run a third time: the task permits only one retry of the same failing command after a diagnosed minimal repair. Independent R2 review additionally identified an unexecuted remaining semantic discrepancy: fixture exact-pair mismatch returns `RELEASE_NOT_FOUND`, while `HttpArchiveRepositoryProvider.open()` reduces a non-OK descriptor response to `UNAVAILABLE`.

Consequently no adapter-runtime pass is asserted:

```text
FIXTURE_ADAPTER_RUNTIME_PASS=false
HTTP_ADAPTER_RUNTIME_PASS=false
POSTGRES_ADAPTER_RUNTIME_PASS=false
ADAPTER_CONTRACT_DIGEST_MATCH=false
QUERY_VECTOR_COUNT=0
```

`UNKNOWN_RELATION_FAIL_CLOSED=UNVERIFIED`, `HELD_LOCATOR_API_LEAK_COUNT=UNVERIFIED`, and `RAW_PAYLOAD_API_LEAK_COUNT=UNVERIFIED`: the complete vector did not finish.
