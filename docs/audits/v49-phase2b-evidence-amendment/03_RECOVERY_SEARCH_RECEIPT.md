# Original P1 byte recovery search receipt

```text
SEARCH_MODE=READ_ONLY_BOUNDED
SOURCE_SHA=11e7b82d27b2774273d2f0d68904632246dabd37
EXPECTED_ARTIFACT_COUNT=11
EXACT_BYTE_RECOVERY_COUNT=0
HISTORICAL_ARTIFACTS_RECOVERED=false
```

The search used each missing manifest basename and never accepted a name,
timestamp, or text-only match. A candidate would have required both the
manifest byte length and its SHA-256 to match exactly.

| Location or object source | Result |
|---|---|
| Registered Git worktrees and known local project clones | No expected P1 path present. |
| `/private/tmp` recovery/performance worktrees | No expected P1 path present. |
| Bounded project locations in Desktop, Documents and Downloads | No expected P1 path present. |
| `~/Library/Caches/gda_v49_phase2b`, `~/Library/Application Support/graphic_design_archive`, and Trash | No expected P1 path present. |
| All reachable refs, remote refs and tags | No commit tree contained an expected P1 path. |
| Stashes | No stash entries. |
| Reflog commit trees | 159 reflog commits inspected; no expected P1 path. |
| Unreachable object scan | Read-only `git fsck --full --unreachable --no-reflogs --no-progress` was stopped at the mandatory 60-minute cap. It emitted no candidate object before the cap. This incomplete final scan is not treated as proof of byte recovery. |
| Time Machine | No machine directory was available to this session. |

The original P1 bytes are therefore unavailable to this task. This result does
not authorize synthesizing matching SHA-256 bytes or adding new output at the
old paths. The package instead uses the separately named, additive
`reproduced/` artifacts.
