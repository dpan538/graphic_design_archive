# Prefreeze candidate v46 — supervised transfer completion

## Scope and freeze status

This receipt records the transfer of the **v46 design-validation baseline**
to `origin/main`. It is frozen for interface, search and TRACE validation; it
is **not** the final public-release database. The candidate has 15,921 active
objects and remains 4,079 objects below the 20,000-object release target.

The complete selected package is defined by
`generated/prefreeze_candidate_v46_transfer_manifest_draft.json`:

- 30 files; 613,972,721 bytes; two Git LFS payloads.
- Manifest SHA-256: `4e36dba9239cc90775944f1a1d53bb92fab494c80ed53103f65107d7f6c0bed4`.
- Canonical candidate JSON: 190,039,480 bytes;
  `42515bce22514532a1651b5236100f6660a9f9ff12e9f3b2f889eb85d4ac182b`.
- Frozen search SQLite: 419,688,448 bytes;
  `9975ee1c7ae13d1845428115707e3ad8c8d1d7421a18c5af533385b758ca9731`.

Raw capture caches, prior candidates and unrelated working-tree changes are
outside this transfer.

## Ordered transfer

| Batch | Commit before this receipt | Contents |
| --- | --- | --- |
| A | `f48cc93` | freeze contract, audit/build scripts, documentation and new-design handoff |
| B | `fce7535` | canonical v46 candidate JSON through Git LFS |
| C | `8f0f318` | frozen v46 search SQLite through Git LFS |
| D | `c460333` | review holds, search/TRACE audits and TRACE-atlas query artifacts |
| E | this commit | missing reproducibility script and this completion receipt |

The E script is
`scripts/build_prefreeze_candidate_v46_loc_duplicate_resolution.py`. It was
already declared in the A manifest but was detected as absent by the first
independent remote readback. It is included here rather than silently removing
it from the reproducibility contract.

## Independent verification before E

An isolated shallow clone of remote commit `c460333` confirmed both LFS
payload hashes and the following frozen functional checks:

- SQLite `PRAGMA integrity_check`: `ok`.
- Active objects: 15,921; accepted TRACE objects: 15,921.
- Unlinked TRACE holds: 0; uncertain-authority active objects: 0.
- Search-gate failures: 0.
- 200-object audit failures: 0.
- TRACE topology: 15,921 pass; 0 fail.

The same clone exposed exactly one manifest failure: the missing E script
above. E is therefore a bounded correction to make all 30 declared files
available remotely. After E is pushed, the same isolated clone is refreshed
and all manifest hashes must match before this transfer is considered complete.

## Design handoff

The next design-only chat must use
[`DESIGN_REFINEMENT_PROMPT_v1.md`](../handoff/DESIGN_REFINEMENT_PROMPT_v1.md).
It treats the v46 data as read-only and keeps the design task separate from
release-count expansion or data reclassification.
