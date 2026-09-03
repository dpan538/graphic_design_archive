#!/bin/sh
set -eu

# One private PostgreSQL 16 cluster for the compact synthetic fixture. No
# TCP listener, production DSN, staging path, or host PostgreSQL is used.
GDA_PG_BIN=${GDA_PG_BIN:-/opt/homebrew/opt/postgresql@16/bin}
GDA_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
GDA_TMP=$(mktemp -d "${TMPDIR:-/tmp}/gda-v49-phase2c-pg.XXXXXX")
GDA_DATA="$GDA_TMP/data"
GDA_SOCKET="$GDA_TMP/socket"
GDA_PORT=${GDA_PHASE2C_PGPORT:-55457}

cleanup() {
  "$GDA_PG_BIN/pg_ctl" -D "$GDA_DATA" -m fast -w stop >/dev/null 2>&1 || true
  rm -rf "$GDA_TMP"
}
trap cleanup EXIT HUP INT TERM
test "$GDA_PORT" != 5432
mkdir -p "$GDA_SOCKET"
"$GDA_PG_BIN/initdb" -D "$GDA_DATA" --no-locale --encoding=UTF8 >/dev/null
"$GDA_PG_BIN/pg_ctl" -D "$GDA_DATA" -o "-k $GDA_SOCKET -p $GDA_PORT -c listen_addresses=''" -w start >/dev/null
"$GDA_PG_BIN/psql" -X -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" \
  -d postgres -f "$GDA_ROOT/database/roles/001_cluster_roles.sql" >/dev/null
# The disposable cluster's bootstrap account is granted only SET ROLE for
# schema replay and test impersonation; this exists solely inside this temp
# cluster and is removed with it.
"$GDA_PG_BIN/psql" -X -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" \
  -d postgres -c "GRANT gda_v49_phase2a_schema_owner TO CURRENT_USER" >/dev/null
"$GDA_PG_BIN/createdb" -h "$GDA_SOCKET" -p "$GDA_PORT" \
  -O gda_v49_phase2a_schema_owner gda_v49_phase2a_phase2c
PGHOST="$GDA_SOCKET" PGPORT="$GDA_PORT" PGDATABASE=gda_v49_phase2a_phase2c \
  "$GDA_ROOT/database/scripts/replay.sh"
"$GDA_PG_BIN/psql" -X -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" \
  -d gda_v49_phase2a_phase2c -f "$GDA_ROOT/database/tests/002_release_seal_cas.sql" >/dev/null
printf '%s\n' 'PHASE2C_SMALL_DB_INTEGRATION=PASS POSTGRESQL_VERSION=16'
