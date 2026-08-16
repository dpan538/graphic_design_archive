#!/bin/sh
set -eu

# Phase 2C-S is intentionally isolated: one PostgreSQL 16 cluster, Unix
# socket only, two fresh schema replays, and the v3 focused test.  It never
# calls the legacy full Seal/CAS test suite or any frontend command.
GDA_PG_BIN=${GDA_PG_BIN:-/opt/homebrew/opt/postgresql@16/bin}
GDA_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
GDA_TMP=$(mktemp -d "${TMPDIR:-/private/tmp}/gda-v49-phase2s.XXXXXX")
GDA_DATA="$GDA_TMP/data"
GDA_SOCKET="$GDA_TMP/socket"
GDA_PORT=${GDA_PHASE2S_PGPORT:-55681}
cleanup() {
  "$GDA_PG_BIN/pg_ctl" -D "$GDA_DATA" -m fast -w stop >/dev/null 2>&1 || true
  rm -rf "$GDA_TMP"
}
trap cleanup EXIT HUP INT TERM
test "$GDA_PORT" != 5432
mkdir -p "$GDA_SOCKET"
"$GDA_PG_BIN/initdb" -D "$GDA_DATA" --no-locale --encoding=UTF8 >/dev/null
"$GDA_PG_BIN/pg_ctl" -D "$GDA_DATA" -o "-k $GDA_SOCKET -p $GDA_PORT -c listen_addresses=''" -w start >/dev/null
"$GDA_PG_BIN/psql" -X -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" -d postgres -f "$GDA_ROOT/database/roles/001_cluster_roles.sql" >/dev/null
"$GDA_PG_BIN/psql" -X -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" -d postgres -c "GRANT gda_v49_phase2a_schema_owner TO CURRENT_USER" >/dev/null
for GDA_DB in gda_v49_phase2a_phase2s_a gda_v49_phase2a_phase2s_b; do
  "$GDA_PG_BIN/createdb" -h "$GDA_SOCKET" -p "$GDA_PORT" -O gda_v49_phase2a_schema_owner "$GDA_DB"
  PGHOST="$GDA_SOCKET" PGPORT="$GDA_PORT" PGDATABASE="$GDA_DB" "$GDA_ROOT/database/scripts/replay.sh"
  TMPDIR="$GDA_TMP" PGHOST="$GDA_SOCKET" PGPORT="$GDA_PORT" PGDATABASE="$GDA_DB" sh "$GDA_ROOT/database/scripts/schema_hash.sh" >> "$GDA_TMP/schema-hashes.txt"
done
test "$(sed -n '1p' "$GDA_TMP/schema-hashes.txt")" = "$(sed -n '2p' "$GDA_TMP/schema-hashes.txt")"
"$GDA_PG_BIN/psql" -X -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" -d gda_v49_phase2a_phase2s_a -f "$GDA_ROOT/database/tests/005_release_projection_snapshot.sql"
printf '%s\n' "PHASE2S_SNAPSHOT=PASS SCHEMA_SHA256=$(sed -n '1p' "$GDA_TMP/schema-hashes.txt")"
