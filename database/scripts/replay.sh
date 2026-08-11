#!/bin/sh
set -eu

: "${PGHOST:?PGHOST must name the dedicated Unix socket directory}"
: "${PGPORT:?PGPORT must name the dedicated non-default port}"
: "${PGDATABASE:?PGDATABASE must name a fresh gda_v49_phase2a database}"

if [ "${PGPORT}" = "5432" ]; then
  echo "refusing default PostgreSQL port 5432" >&2
  exit 64
fi

case "${PGHOST}" in
  /*) ;;
  *) echo "PGHOST must be an absolute Unix socket directory" >&2; exit 64 ;;
esac

case "${PGDATABASE}" in
  gda_v49_phase2a_*) ;;
  *) echo "PGDATABASE must use the gda_v49_phase2a_ prefix" >&2; exit 64 ;;
esac

GDA_PSQL=${GDA_PSQL:-psql}
GDA_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

GDA_EXISTING=$(
  "$GDA_PSQL" -X -Atq -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -c "SELECT count(*) FROM pg_catalog.pg_namespace
        WHERE nspname = ANY (ARRAY[
          'raw','core','provenance','research','rights',
          'workflow','release','audit','api_v1'
        ]);"
)
if [ "$GDA_EXISTING" != "0" ]; then
  echo "refusing non-fresh database: project schemas already exist" >&2
  exit 65
fi

for GDA_SQL in \
  database/migrations/001_foundation.sql \
  database/migrations/002_raw_core_provenance.sql \
  database/migrations/003_research_rights.sql \
  database/migrations/004_release_audit.sql \
  database/migrations/005_normative_closure.sql \
  database/migrations/006_epistemic_trace_closure.sql \
  database/migrations/007_release_copy_integrity.sql \
  database/migrations/008_final_integrity_closure.sql \
  database/functions/001_deferred_constraints.sql \
  database/functions/002_mutation_guards.sql \
  database/functions/003_release_and_cas.sql \
  database/functions/004_controlled_writes.sql \
  database/functions/005_projection_builders.sql \
  database/functions/006_normative_closure.sql \
  database/functions/007_release_protocol_closure.sql \
  database/functions/008_projection_builders_v2.sql \
  database/functions/009_projection_inventory_builders.sql \
  database/functions/010_visual_inventory_builders.sql \
  database/functions/011_rights_hash_closure.sql \
  database/functions/012_controlled_write_closure.sql \
  database/functions/013_review_case_closure.sql \
  database/functions/014_release_copy_guards.sql \
  database/functions/015_final_integrity_closure.sql \
  database/views/001_api_v1.sql \
  database/views/002_role_workspaces.sql
do
  "$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -f "$GDA_REPO_ROOT/$GDA_SQL"
done

"$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
  -v database_name="$PGDATABASE" \
  -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
  -f "$GDA_REPO_ROOT/database/roles/002_database_grants.sql"

GDA_SCHEMA_COUNT=$(
  "$GDA_PSQL" -X -Atq -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -c "SELECT count(*) FROM pg_catalog.pg_namespace
        WHERE nspname = ANY (ARRAY[
          'raw','core','provenance','research','rights',
          'workflow','release','audit','api_v1'
        ]);"
)
test "$GDA_SCHEMA_COUNT" = "9"
printf '%s\n' "REPLAY_OK database=$PGDATABASE schemas=$GDA_SCHEMA_COUNT"
