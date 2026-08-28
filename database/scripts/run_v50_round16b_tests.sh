#!/bin/sh
set -eu

: "${PGHOST:?PGHOST must name the dedicated Unix socket directory}"
: "${PGPORT:?PGPORT must name the dedicated non-default port}"
: "${PGDATABASE:?PGDATABASE must name a gda_v50_round16b database}"
if [ "${PGPORT}" = "5432" ]; then exit 64; fi
case "${PGHOST}" in /*) ;; *) exit 64 ;; esac
case "${PGDATABASE}" in gda_v50_round16b_*) ;; *) exit 64 ;; esac

GDA_PSQL=${GDA_PSQL:-psql}
GDA_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
gda_psql() {
  "$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" "$@"
}

gda_psql \
  -f "$GDA_REPO_ROOT/database/tests/014_exploration_v3_higher_order_associations.sql"

# Catalog estimates are not evidence.  Count every governed table exactly.
gda_psql -c "DO \$exact_residue\$
DECLARE v_table record; v_count bigint;
BEGIN
  FOR v_table IN
    SELECT tablename FROM pg_catalog.pg_tables
    WHERE schemaname='exploration_v3' ORDER BY tablename COLLATE \"C\"
  LOOP
    EXECUTE format('SELECT count(*) FROM exploration_v3.%I',v_table.tablename)
      INTO v_count;
    IF v_count <> 0 THEN
      RAISE EXCEPTION 'EXPLORATION_V3_FIXTURE_RESIDUE: table=% count=%',
        v_table.tablename,v_count;
    END IF;
  END LOOP;
END
\$exact_residue\$;"

# Real seal-vs-child schedules run in a disposable clone so committed barrier
# fixtures cannot contaminate either governed replay database.  A FIFO holds
# the owner transaction open; advisory-lock observation is the deterministic
# barrier (wall-clock sleep is not the ordering proof).
GDA_PG_BINDIR=$(CDPATH= cd -- "$(dirname -- "$GDA_PSQL")" && pwd)
GDA_CREATEDB=${GDA_CREATEDB:-$GDA_PG_BINDIR/createdb}
GDA_DROPDB=${GDA_DROPDB:-$GDA_PG_BINDIR/dropdb}
GDA_RACE_DATABASE="${PGDATABASE}_race_$$"
case "$GDA_RACE_DATABASE" in
  gda_v50_round16b_*_race_[0-9]*) ;;
  *) exit 64 ;;
esac
GDA_RACE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/gda-v50-seal-race.XXXXXX")
GDA_RACE_EVIDENCE_ROOT="$GDA_REPO_ROOT/docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/v50-round16b-seal-race"
GDA_RACE_EVIDENCE_DIR=${GDA_RACE_EVIDENCE_DIR:-$GDA_RACE_EVIDENCE_ROOT/$PGDATABASE}
case "$GDA_RACE_EVIDENCE_DIR" in
  "$GDA_RACE_EVIDENCE_ROOT"/gda_v50_round16b_*) ;;
  *) exit 64 ;;
esac
gda_drop_race_database() {
  if [ -n "${GDA_RACE_DATABASE:-}" ]; then
    "$GDA_DROPDB" -h "$PGHOST" -p "$PGPORT" --if-exists --force \
      "$GDA_RACE_DATABASE" >/dev/null 2>&1 || true
  fi
}
trap gda_drop_race_database 0 1 2 3 15
"$GDA_CREATEDB" -h "$PGHOST" -p "$PGPORT" \
  --template="$PGDATABASE" "$GDA_RACE_DATABASE" \
  >"$GDA_RACE_DIR/createdb.log" 2>&1

gda_psql_race() {
  "$GDA_PSQL" -X -q -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -d "$GDA_RACE_DATABASE" "$@"
}
gda_wait_for_membership_lock() {
  GDA_WAIT_ID=$1
  GDA_WAIT_COUNT=0
  while :; do
    GDA_LOCKED=$(gda_psql_race -At -c \
      "SELECT NOT pg_try_advisory_lock(hashtextextended('exploration_v3:EVIDENCE_REFERENCE:$GDA_WAIT_ID',0));")
    if [ "$GDA_LOCKED" = "t" ]; then return 0; fi
    GDA_WAIT_COUNT=$((GDA_WAIT_COUNT + 1))
    if [ "$GDA_WAIT_COUNT" -ge 200 ]; then
      printf '%s\n' "membership-lock barrier timeout: $GDA_WAIT_ID" >&2
      return 1
    fi
    sleep 0.05
  done
}
gda_expect_sqlstate() {
  GDA_EXPECTED_STATE=$1
  GDA_EXPECTED_MESSAGE=$2
  GDA_EXPECTED_LOG=$3
  GDA_EXPECTED_SQL=$4
  if printf '%s\n' '\set VERBOSITY verbose' "$GDA_EXPECTED_SQL" | \
      gda_psql_race >"$GDA_EXPECTED_LOG" 2>&1; then
    printf '%s\n' "expected SQL failure was accepted: $GDA_EXPECTED_MESSAGE" >&2
    return 1
  fi
  rg -q "$GDA_EXPECTED_STATE:.*$GDA_EXPECTED_MESSAGE" "$GDA_EXPECTED_LOG"
}
gda_start_owner() {
  GDA_OWNER_FIFO=$1
  GDA_OWNER_LOG=$2
  GDA_OWNER_SQL=$3
  mkfifo "$GDA_OWNER_FIFO"
  gda_psql_race <"$GDA_OWNER_FIFO" >"$GDA_OWNER_LOG" 2>&1 &
  GDA_OWNER_PID=$!
  exec 9>"$GDA_OWNER_FIFO"
  printf '%s\n' 'BEGIN;' "$GDA_OWNER_SQL" >&9
}
gda_finish_owner() {
  printf '%s\n' 'COMMIT;' '\q' >&9
  exec 9>&-
  wait "$GDA_OWNER_PID"
}

gda_psql_race -At -c "DO \$owner\$ BEGIN
  IF current_user <> (SELECT pg_get_userbyid(datdba) FROM pg_catalog.pg_database
      WHERE datname=current_database()) THEN
    RAISE EXCEPTION 'RACE_DATABASE_OWNER_MISMATCH';
  END IF;
END \$owner\$;
INSERT INTO exploration_v3.evidence_reference VALUES
  ('evidence:race:child-first','SYNTHETIC_CONTROL',NULL,NULL,NULL,repeat('a',64),
   'Real child-first concurrency fixture.',false,true,'SYNTHETIC_ONLY'),
  ('evidence:race:seal-first','SYNTHETIC_CONTROL',NULL,NULL,NULL,repeat('b',64),
   'Real seal-first concurrency fixture.',false,true,'SYNTHETIC_ONLY'),
  ('evidence:race:repeatable-read','SYNTHETIC_CONTROL',NULL,NULL,NULL,repeat('c',64),
   'Repeatable-read isolation fixture.',false,true,'SYNTHETIC_ONLY'),
  ('evidence:race:serializable','SYNTHETIC_CONTROL',NULL,NULL,NULL,repeat('d',64),
   'Serializable isolation fixture.',false,true,'SYNTHETIC_ONLY');
SELECT 'RACE_DATABASE_OWNER='||current_user||' FIXTURE_PARENTS=4';" \
  >"$GDA_RACE_DIR/setup-owner.log" 2>&1

# Child owns membership first: concurrent seal fails 40001; after the child
# commits, a fresh seal hashes and includes that exact locator.
gda_start_owner "$GDA_RACE_DIR/child-first.fifo" \
  "$GDA_RACE_DIR/child-first.owner.log" \
  "INSERT INTO exploration_v3.evidence_locator VALUES
   ('locator:race:child-first','evidence:race:child-first','synthetic://race/child-first',
    repeat('1',64),'SYNTHETIC_ONLY');"
gda_wait_for_membership_lock 'evidence:race:child-first'
gda_expect_sqlstate 40001 AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY \
  "$GDA_RACE_DIR/child-first.contender.log" \
  "INSERT INTO exploration_v3.aggregate_seal VALUES
   ('EVIDENCE_REFERENCE','evidence:race:child-first',
    exploration_v3.aggregate_content_sha('EVIDENCE_REFERENCE','evidence:race:child-first'),
    '2026-08-28T00:00:00Z');"
gda_finish_owner
gda_psql_race -At -c "INSERT INTO exploration_v3.aggregate_seal VALUES
  ('EVIDENCE_REFERENCE','evidence:race:child-first',
   exploration_v3.aggregate_content_sha('EVIDENCE_REFERENCE','evidence:race:child-first'),
   '2026-08-28T00:00:00Z');
  DO \$verify\$ BEGIN
    IF (SELECT count(*) FROM exploration_v3.evidence_locator
        WHERE evidence_reference_id='evidence:race:child-first') <> 1
      OR (SELECT aggregate_content_sha256 FROM exploration_v3.aggregate_seal
          WHERE aggregate_kind='EVIDENCE_REFERENCE'
            AND aggregate_id='evidence:race:child-first') <>
        exploration_v3.aggregate_content_sha(
          'EVIDENCE_REFERENCE','evidence:race:child-first') THEN
      RAISE EXCEPTION 'CHILD_FIRST_POST_RACE_INVARIANT_FAILED';
    END IF;
  END \$verify\$;
  SELECT 'CHILD_FIRST_RETRY_SEAL_AND_CONTENT=PASS CHILD_INCLUDED=1';" \
  >"$GDA_RACE_DIR/child-first.retry-and-invariant.log" 2>&1

# Seal owns membership first: concurrent child fails 40001; once sealed, a
# fresh child attempt reaches the visible seal and fails exact 55000.
gda_start_owner "$GDA_RACE_DIR/seal-first.fifo" \
  "$GDA_RACE_DIR/seal-first.owner.log" \
  "INSERT INTO exploration_v3.aggregate_seal VALUES
   ('EVIDENCE_REFERENCE','evidence:race:seal-first',
    exploration_v3.aggregate_content_sha('EVIDENCE_REFERENCE','evidence:race:seal-first'),
    '2026-08-28T00:00:00Z');"
gda_wait_for_membership_lock 'evidence:race:seal-first'
gda_expect_sqlstate 40001 AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY \
  "$GDA_RACE_DIR/seal-first.contender.log" \
  "INSERT INTO exploration_v3.evidence_locator VALUES
   ('locator:race:seal-first:contender','evidence:race:seal-first',
    'synthetic://race/seal-first/contender',repeat('2',64),'SYNTHETIC_ONLY');"
gda_finish_owner
gda_expect_sqlstate 55000 SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN \
  "$GDA_RACE_DIR/seal-first.retry.log" \
  "INSERT INTO exploration_v3.evidence_locator VALUES
   ('locator:race:seal-first:retry','evidence:race:seal-first',
    'synthetic://race/seal-first/retry',repeat('3',64),'SYNTHETIC_ONLY');"
gda_psql_race -At -c "DO \$verify\$ BEGIN
  IF (SELECT count(*) FROM exploration_v3.evidence_locator
      WHERE evidence_reference_id='evidence:race:seal-first') <> 0
    OR (SELECT aggregate_content_sha256 FROM exploration_v3.aggregate_seal
        WHERE aggregate_kind='EVIDENCE_REFERENCE'
          AND aggregate_id='evidence:race:seal-first') <>
      exploration_v3.aggregate_content_sha(
        'EVIDENCE_REFERENCE','evidence:race:seal-first') THEN
    RAISE EXCEPTION 'SEAL_FIRST_POST_RACE_INVARIANT_FAILED';
  END IF;
END \$verify\$;
SELECT 'SEAL_FIRST_POST_RACE_INVARIANT=PASS CHILD_COUNT=0';" \
  >"$GDA_RACE_DIR/seal-first.invariant.log" 2>&1

gda_expect_sqlstate 25000 AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED \
  "$GDA_RACE_DIR/repeatable-read.log" \
  "BEGIN ISOLATION LEVEL REPEATABLE READ;
   INSERT INTO exploration_v3.evidence_locator VALUES
   ('locator:race:repeatable-read','evidence:race:repeatable-read',
    'synthetic://race/repeatable-read',repeat('4',64),'SYNTHETIC_ONLY'); COMMIT;"
gda_expect_sqlstate 25000 AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED \
  "$GDA_RACE_DIR/serializable.log" \
  "BEGIN ISOLATION LEVEL SERIALIZABLE;
   INSERT INTO exploration_v3.aggregate_seal VALUES
   ('EVIDENCE_REFERENCE','evidence:race:serializable',
    exploration_v3.aggregate_content_sha('EVIDENCE_REFERENCE','evidence:race:serializable'),
    '2026-08-28T00:00:00Z'); COMMIT;"

"$GDA_DROPDB" -h "$PGHOST" -p "$PGPORT" --force "$GDA_RACE_DATABASE" \
  >"$GDA_RACE_DIR/dropdb.log" 2>&1
GDA_RACE_DATABASE=
trap - 0 1 2 3 15
mkdir -p "$GDA_RACE_EVIDENCE_DIR"
for GDA_RACE_LOG in \
  createdb.log setup-owner.log \
  child-first.owner.log child-first.contender.log \
  child-first.retry-and-invariant.log \
  seal-first.owner.log seal-first.contender.log seal-first.retry.log \
  seal-first.invariant.log repeatable-read.log serializable.log dropdb.log; do
  cp "$GDA_RACE_DIR/$GDA_RACE_LOG" "$GDA_RACE_EVIDENCE_DIR/$GDA_RACE_LOG"
done
(
  cd "$GDA_RACE_EVIDENCE_DIR"
  for GDA_RACE_LOG in \
    child-first.contender.log child-first.owner.log \
    child-first.retry-and-invariant.log createdb.log dropdb.log \
    repeatable-read.log seal-first.contender.log seal-first.invariant.log \
    seal-first.owner.log seal-first.retry.log serializable.log setup-owner.log; do
    shasum -a 256 "$GDA_RACE_LOG"
  done
) >"$GDA_RACE_EVIDENCE_DIR/CHECKSUMS.sha256"
GDA_RACE_CHECKSUMS_SHA256=$(shasum -a 256 \
  "$GDA_RACE_EVIDENCE_DIR/CHECKSUMS.sha256" | awk '{print $1}')
printf '%s\n' \
  'V50_SEAL_RACE_CHILD_FIRST=PASS LOSER_SQLSTATE=40001 RETRY_SEAL=PASS CHILD_INCLUDED=1' \
  'V50_SEAL_RACE_SEAL_FIRST=PASS LOSER_SQLSTATE=40001 RETRY_CHILD_SQLSTATE=55000 CHILD_COUNT=0' \
  'V50_SEAL_ISOLATION_GUARDS=PASS REPEATABLE_READ_SQLSTATE=25000 SERIALIZABLE_SQLSTATE=25000' \
  'V50_RACE_DATABASE_DISPOSED=PASS' \
  "V50_SEAL_RACE_EVIDENCE_DIR=$GDA_RACE_EVIDENCE_DIR CHECKSUMS_SHA256=$GDA_RACE_CHECKSUMS_SHA256" \
  'V50_ROUND16B_CONTRACT_TESTS=PASS SEAL_RACE_MATRIX=PASS ISOLATION_GUARDS=PASS FIXTURE_RESIDUE=0'
