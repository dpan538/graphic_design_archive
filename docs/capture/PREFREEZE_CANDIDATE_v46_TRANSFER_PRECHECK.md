# v46 transfer precheck — HOLD

This is a supervised-transfer planning artifact, not authorization to stage,
commit, push, or publish the candidate.

## Candidate state

- Active objects: 15,921 / 20,000 minimum target
- Chronology: no missing years from 1800 through 2029
- Active unresolved geography: 0
- Active uncertain authority: 0
- Accepted TRACE: 15,921 / 15,921
- Explicit TRACE tier: 10,964
- Object-geography review hold: 74
- Duplicate-representation review hold: 1
- Remaining distance to count target: 4,079

v46 closes the last two annual holes using five original Gallica OAI records
with exact date, explicit publisher city, qualifying carrier and IIIF route. It
also merges two Commons representations that resolve to the same direct LOC
object. The noncanonical representation remains reviewable but count-isolated.

## Still blocking transfer

1. The active-count target is not met.
2. The v46 search/TRACE synchronization gate has passed, but the final
   clean-checkout rebuild receipt must be regenerated against the exact
   transfer manifest before a release transfer begins.
3. The geography and duplicate review layers must remain count-isolated and
   explicitly included or excluded in the eventual release manifest.
4. Source-chain reattachment continues independently of accepted TRACE; a
   direct root should never be fabricated simply to improve a tier metric.

## Future transfer procedure

Use a clean worktree and an immutable version manifest. Transfer only the
selected candidate JSON, its review payloads, source trace nodes/edges,
decision logs, validation reports, TRACE-atlas aggregates, and reproducible
builders. Do not bulk add raw captures, obsolete candidates, generated previews
or disposable SQLite caches. Hash every transferred file; use LFS only for
manifest-listed large artifacts; validate a clean remote retrieval and local
rebuild before release.

## Supervised large-transfer batches

The transfer must not be one bulk commit. Create the versioned draft manifest
first, then stop if any hash, file classification, or release gate differs.

1. **Batch A — reproducibility and contract.** Transfer scripts, versioned
   documentation, the validation receipts, and the immutable manifest only.
   Verify that the main repository can read the manifest before any object
   payload is added.
2. **Batch B — active candidate payload.** Transfer the one manifest-listed
   public candidate JSON through LFS (the v46 payload is approximately 181 MB).
   Fetch it back by object ID and verify its SHA-256 before proceeding.
3. **Batch C — frozen search database.** Transfer the exact LFS SQLite search
   snapshot separately. It is a read-only query snapshot of the candidate,
   retained because a byte-identical rebuild depends on historical TRACE batch
   evidence. Verify SQLite integrity, schema version, active count, and
   SHA-256 after remote retrieval; it never replaces the candidate JSON as the
   canonical data payload.
4. **Batch D — review and visual-query layer.** Transfer the two isolated
   review payloads, TRACE topology audit, 200-object audit, and the small
   geography-time/source-geography atlas aggregates. Verify that review records
   cannot enter active counts or atlas totals.
5. **Batch E — clean retrieval receipt.** In a fresh checkout, retrieve both
   LFS payloads, verify their hashes, run SQLite integrity and the saved
   search/TRACE/topology/200-object receipts, and compare active count,
   accepted TRACE count, review counts, and atlas manifest hashes. Only then
   may the release-freeze decision be recorded.

The 400 MB SQLite file is transferred as a frozen, read-only query snapshot,
not as a canonical source package. Raw captures and older candidate versions
remain excluded.
