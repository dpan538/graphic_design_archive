#!/bin/sh
set -eu

# Current frozen v49 contract: v5 publishing, not the superseded phase2c API.
# All resources belong to this run: PostgreSQL 16, Unix socket only, no DSN.
GDA_PG_BIN=${GDA_PG_BIN:-/opt/homebrew/opt/postgresql@16/bin}
GDA_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
case "$("$GDA_PG_BIN/postgres" --version)" in
  *' 16.'*) ;;
  *) echo 'PostgreSQL 16 is required' >&2; exit 64 ;;
esac
GDA_TMP=$(mktemp -d "${TMPDIR:-/tmp}/mgda-current-db.XXXXXX")
GDA_DATA="$GDA_TMP/data"
GDA_SOCKET="$GDA_TMP/socket"
GDA_PORT=55457
cleanup() {
  "$GDA_PG_BIN/pg_ctl" -D "$GDA_DATA" -m fast -w stop >/dev/null 2>&1 || true
  rm -rf "$GDA_TMP"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
mkdir -p "$GDA_SOCKET"
"$GDA_PG_BIN/initdb" -D "$GDA_DATA" --no-locale --encoding=UTF8 >/dev/null
"$GDA_PG_BIN/pg_ctl" -D "$GDA_DATA" -o "-k $GDA_SOCKET -p $GDA_PORT -c listen_addresses=''" -w start >/dev/null
sql() {
  "$GDA_PG_BIN/psql" -X -q -v ON_ERROR_STOP=1 -h "$GDA_SOCKET" -p "$GDA_PORT" "$@"
}
sql -d postgres -f "$GDA_ROOT/database/roles/001_cluster_roles.sql"
sql -d postgres -c 'GRANT gda_v49_phase2a_schema_owner TO CURRENT_USER'
replay() {
  "$GDA_PG_BIN/createdb" -h "$GDA_SOCKET" -p "$GDA_PORT" -O gda_v49_phase2a_schema_owner "$1"
  GDA_PSQL="$GDA_PG_BIN/psql" PGHOST="$GDA_SOCKET" PGPORT="$GDA_PORT" PGDATABASE="$1" \
    sh "$GDA_ROOT/database/scripts/replay.sh"
}
GDA_DB=gda_v49_phase2a_current_ci
replay "$GDA_DB"
sql -d "$GDA_DB" -f "$GDA_ROOT/scripts/ci/current-db-entrypoints.sql"
for GDA_TEST in \
  010_release_projection_snapshot_db_closure.sql \
  011_release_projection_missingness_matrix.sql \
  012_release_projection_dml_permission_matrix.sql \
  013_release_projection_fault_matrix.sql
do
  sql -d "$GDA_DB" -f "$GDA_ROOT/database/tests/$GDA_TEST"
done
# The concurrency fixture commits, so it receives a second fresh database.
GDA_CONCURRENT_DB=gda_v49_phase2a_current_ci_concurrency
replay "$GDA_CONCURRENT_DB"
python3 "$GDA_ROOT/database/scripts/run_v49_db_closure_concurrency.py" \
  --psql "$GDA_PG_BIN/psql" --host "$GDA_SOCKET" --port "$GDA_PORT" \
  --database "$GDA_CONCURRENT_DB" --repo "$GDA_ROOT" --output "$GDA_TMP/concurrency.json"
printf '%s\n' 'CURRENT_V49_DB_INTEGRATION=PASS POSTGRESQL_VERSION=16'
