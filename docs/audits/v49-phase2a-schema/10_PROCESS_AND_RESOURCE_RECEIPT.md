# v49 Phase 2A — Process and resource receipt

## Task-owned PostgreSQL

- PostgreSQL `16.13`
- cluster root: `/private/tmp/gda_v49_phase2a.bCIwb6`
- socket: `/private/tmp/gda_v49_phase2a.bCIwb6/socket`
- port: `58649`
- primary postmaster PID while testing: `34057`
- start time: `2026-08-11 16:32:07.281866+10`
- external TCP listening: disabled

At 19:09, a guard-rejected duplicate launch was accidentally attempted against
the same data directory. PostgreSQL immediately refused it because postmaster
PID 34057 already owned the cluster. No second postmaster or cluster existed,
and the command was not retried.

All replay, dump, exporter and artifact-tool child processes completed. C1–C5
started no PostgreSQL process; C6 used bounded read-only psql sessions and
left no session or process. After C6 PASS, the controller ran
`pg_ctl ... -m fast -w stop`; PostgreSQL reported `server stopped`, and a
second status check reported `no server running`. PID 34057 and its socket
were absent before cleanup.

The controller then deleted only these verified task-owned disposable paths:

```text
/private/tmp/gda_v49_phase2a.bCIwb6
/private/tmp/v49_phase2a_sheet
/private/tmp/v49_phase2a_full_read.py
```

The first two were temporary directories; the third was a temporary complete-
read helper. They were not user data and are not recoverable by design.

## Resource boundaries

- no port 5432 connection
- no sudo, Docker, package installation, Node server, Next, TypeScript,
  browser automation or data generator
- no v48 JSON/SQLite/TRACE import
- no production media or third-party HTTP request
- one PostgreSQL cluster and at most one local long-running validation process

```text
TASK_OWNED_POSTGRESQL_PROCESS=0
TASK_OWNED_PSQL_SESSION=0
TASK_OWNED_NODE_NEXT_TSC_BROWSER_DOCKER_GENERATOR_PROCESS=0
DISPOSABLE_CLUSTER_STOPPED=true
DISPOSABLE_CLUSTER_PATH_REMOVED=true
```
