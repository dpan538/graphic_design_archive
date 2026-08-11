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

GDA_PSQL=${GDA_PSQL:-psql}
GDA_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

for GDA_TEST in \
  database/tests/001_constraints.sql \
  database/tests/002_release_seal_cas.sql \
  database/tests/003_roles.sql \
  database/tests/004_serializable_seal.sql
do
  "$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" \
    -f "$GDA_REPO_ROOT/$GDA_TEST"
done

"$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
  -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" <<'SQL'
DO $fixture_residue$
DECLARE
  v_table record;
  v_count bigint;
BEGIN
  FOR v_table IN
    SELECT schemaname, tablename
    FROM pg_catalog.pg_tables
    WHERE schemaname = ANY (ARRAY[
      'raw','core','provenance','research','rights',
      'workflow','release','audit'
    ])
  LOOP
    EXECUTE pg_catalog.format(
      'SELECT count(*) FROM %I.%I', v_table.schemaname, v_table.tablename
    ) INTO v_count;
    IF v_count <> 0 THEN
      RAISE EXCEPTION 'TEST_FIXTURE_RESIDUE: %.% has % rows',
        v_table.schemaname, v_table.tablename, v_count;
    END IF;
  END LOOP;
END
$fixture_residue$;
SQL

printf '%s\n' 'CONSTRAINT_TESTS=PASS ROLE_TESTS=PASS RELEASE_TESTS=PASS TEST_FIXTURE_RESIDUE=0'
