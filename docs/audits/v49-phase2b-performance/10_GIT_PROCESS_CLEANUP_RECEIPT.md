# Git, process and cleanup receipt

```text
SOURCE_RECOVERY_REF=origin/recovery/v49-phase2b-performance-checkpoint-20260814
SOURCE_RECOVERY_SHA=6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320
WORK_BRANCH=refactor/v49-phase2b-performance
IMPLEMENTATION_COMMIT=302ddb9
INITIAL_REMOTE_DIVERGENCE=0/0
STABLE_BRANCH_TOUCHED=false
PROTECTED_MAIN_TOUCHED=false
PROTECTED_MAIN_UNCHANGED=true
PROTECTED_MAIN_CONTROLLER_WRITES=0
PRODUCTION_DATABASE_TOUCHED=false
TASK_OWNED_RESIDUAL_PROCESS_COUNT=0
STAGING_PRESERVED=true
EXTRACTOR_RERUN=false
SIGKILL_USED=false
```

Fresh A, Fresh B and the diagnostic database were normally dropped. The
single PostgreSQL 16.13 cluster received a normal `pg_ctl ... stop -m fast
-t 120`; the socket disappeared before deletion. The exact task root
`/private/tmp/gda_v49_phase2b_perf_60423` was then deleted. Its pre-delete
size was 3,019,388 KiB, including 2,170,380 KiB PGDATA. The stable staging
cache remains present. Four pre-existing legacy-named temporary paths were
not treated as task-owned and were not swept.

The protected main end fingerprint exactly equals its start fingerprint:
HEAD `7ef26d66b6ad671fdcc5e11bfa831699a39426bc`, tracked 59 /
`022f7387...9c82`, staged 0 / empty SHA, and untracked 10,937 /
`c1c1c009...4730`. The stable worktree remains clean at recovery SHA
`6b918dd` on its pre-existing recovery branch.

Evidence: `evidence/P6_PROCESS_CLEANUP.json`,
`P0_PROTECTED_MAIN_START.json`, and `P6_PROTECTED_MAIN_END.json`. The exact
final local/remote branch head is reported by the controller after the audit
commit, because a commit cannot contain its own SHA.
