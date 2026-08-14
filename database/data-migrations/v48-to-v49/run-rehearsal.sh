#!/bin/sh
# One deterministic Phase 2B population replay.  This runner deliberately
# refuses to create/drop clusters or databases: the controller must provide a
# fresh database in an already-isolated task-owned cluster.
set -eu

: "${PGHOST:?PGHOST must be the isolated Unix socket directory}"
: "${PGPORT:?PGPORT must be the isolated non-default PostgreSQL port}"
: "${PGDATABASE:?PGDATABASE must be a fresh gda_v49_phase2a database}"
: "${GDA_PHASE2B_STAGE:?GDA_PHASE2B_STAGE must name one verified staging bundle}"
: "${GDA_PHASE2B_REPORT:?GDA_PHASE2B_REPORT must name the verifier JSON output}"

case "$PGHOST" in /*) ;; *) echo 'PGHOST must be an absolute Unix socket directory' >&2; exit 64 ;; esac
case "$PGPORT" in 5432) echo 'refusing PostgreSQL port 5432' >&2; exit 64 ;; esac
case "$PGDATABASE" in gda_v49_phase2a_*) ;; *) echo 'database prefix rejected' >&2; exit 64 ;; esac
case "$GDA_PHASE2B_STAGE" in /private/tmp/*|/tmp/*) ;; *) echo 'staging must be a task-local temporary directory' >&2; exit 64 ;; esac

GDA_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
GDA_PYTHON=${GDA_PYTHON:-python3}
GDA_ADMIN_USER=${GDA_ADMIN_USER:-gda_v49_phase2b_admin}

"$GDA_REPO_ROOT/database/scripts/replay.sh"
"$GDA_PYTHON" "$GDA_REPO_ROOT/database/data-migrations/v48-to-v49/import.py" \
  --stage-dir "$GDA_PHASE2B_STAGE" \
  --pg-host "$PGHOST" --pg-port "$PGPORT" --database "$PGDATABASE" \
  --admin-user "$GDA_ADMIN_USER"
"$GDA_PYTHON" "$GDA_REPO_ROOT/database/data-migrations/v48-to-v49/verify.py" \
  --pg-host "$PGHOST" --pg-port "$PGPORT" --database "$PGDATABASE" \
  --admin-user "$GDA_ADMIN_USER" --output "$GDA_PHASE2B_REPORT"

printf '%s\n' 'PHASE2B_REHEARSAL_REPLAY=PASS'
