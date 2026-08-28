#!/bin/sh
set -eu

: "${PGHOST:?PGHOST must name the dedicated Unix socket directory}"
: "${PGPORT:?PGPORT must name the dedicated non-default port}"
: "${PGDATABASE:?PGDATABASE must name a fresh gda_v50_round16b database}"

if [ "${PGPORT}" = "5432" ]; then
  echo "refusing default PostgreSQL port 5432" >&2
  exit 64
fi
case "${PGHOST}" in /*) ;; *) echo "PGHOST must be absolute" >&2; exit 64 ;; esac
case "${PGDATABASE}" in
  gda_v50_round16b_*) ;;
  *) echo "PGDATABASE must use gda_v50_round16b_ prefix" >&2; exit 64 ;;
esac

GDA_PSQL=${GDA_PSQL:-psql}
GDA_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
python3 "$GDA_REPO_ROOT/database/scripts/verify_v50_round16b_manifest.py" --preflight

GDA_EXISTING=$(
  "$GDA_PSQL" -X -Atq -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -c "SELECT count(*) FROM pg_catalog.pg_namespace
        WHERE nspname = ANY (ARRAY[
          'raw','core','provenance','research','rights','workflow','release',
          'audit','api_v1','exploration_v3','api_v3']);"
)
if [ "$GDA_EXISTING" != "0" ]; then
  echo "refusing non-fresh database: project schemas already exist" >&2
  exit 65
fi

GDA_V49_REPLAY_PREFIX=$(python3 \
  "$GDA_REPO_ROOT/database/scripts/verify_v50_round16b_manifest.py" \
  --emit-v49-replay-prefix)
for GDA_SQL in $GDA_V49_REPLAY_PREFIX
do
  "$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
    -v database_name="$PGDATABASE" \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -f "$GDA_REPO_ROOT/$GDA_SQL"
done

# The complete, byte-frozen v49 replay above is an exact prefix.  Only after
# all v49 grants exist may the forward-only v50 research capability be added.
GDA_V50_ADDITIVE_REPLAY=$(python3 \
  "$GDA_REPO_ROOT/database/scripts/verify_v50_round16b_manifest.py" \
  --emit-additive-replay)
for GDA_SQL in $GDA_V50_ADDITIVE_REPLAY
do
  "$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
    -v database_name="$PGDATABASE" \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -f "$GDA_REPO_ROOT/$GDA_SQL"
done

GDA_SCHEMA_COUNT=$(
  "$GDA_PSQL" -X -Atq -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -c "SELECT count(*) FROM pg_catalog.pg_namespace
        WHERE nspname = ANY (ARRAY[
          'raw','core','provenance','research','rights','workflow','release',
          'audit','api_v1','exploration_v3','api_v3']);"
)
test "$GDA_SCHEMA_COUNT" = "11"
GDA_SERVER_VERSION=$(
  "$GDA_PSQL" -X -Atq -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -c "SHOW server_version;"
)
case "$GDA_SERVER_VERSION" in 16.*) ;; *) exit 66 ;; esac
printf '%s\n' \
  "V50_ROUND16B_REPLAY_OK database=$PGDATABASE schemas=$GDA_SCHEMA_COUNT postgresql=$GDA_SERVER_VERSION"
