#!/bin/sh
set -eu

: "${PGHOST:?PGHOST must name the dedicated Unix socket directory}"
: "${PGPORT:?PGPORT must name the dedicated non-default port}"
: "${PGDATABASE:?PGDATABASE must name a gda_v49_phase2a database}"

if [ "${PGPORT}" = "5432" ]; then
  echo "refusing default PostgreSQL port 5432" >&2
  exit 64
fi
case "${PGHOST}" in /*) ;; *) exit 64 ;; esac
case "${PGDATABASE}" in gda_v49_phase2a_*) ;; *) exit 64 ;; esac

GDA_PG_DUMP=${GDA_PG_DUMP:-pg_dump}
GDA_PYTHON=${GDA_PYTHON:-python3}
GDA_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
GDA_DUMP=$(mktemp "${TMPDIR:-/tmp}/gda_v49_phase2a_schema.XXXXXX.sql")
trap 'rm -f -- "$GDA_DUMP"' EXIT HUP INT TERM

"$GDA_PG_DUMP" --schema-only --no-owner --no-privileges \
  -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" > "$GDA_DUMP"
GDA_HASH=$(
  "$GDA_PYTHON" "$GDA_REPO_ROOT/database/scripts/schema_hash.py" "$GDA_DUMP"
)
printf '%s\n' "$GDA_HASH"
