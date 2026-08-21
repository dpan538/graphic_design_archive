# Database and API-visible statistics

`scripts/v49_read_api_statistics.mjs` is the reproducible, versioned statistics generator. It rejects mutation/DDL keywords, forces `default_transaction_read_only=on`, begins explicit read-only transactions, and uses `gda_v49_phase2a_api_reader` for public projections. The existing auditor role intentionally cannot read raw/core tables; the isolated internal audit query therefore used the task-local admin session under database-enforced read-only mode without granting or changing any privilege.

```text
DATABASE_STATISTICS=PASS
DATABASE_STATISTICS_REPRODUCIBLE=true
API_VISIBLE_STATISTICS=PASS
SEARCH_READINESS_STATISTICS=PASS
CANONICAL_OBJECT_COUNT=15923
API_VISIBLE_OBJECT_COUNT=7995
ELIGIBLE_COUNT=7995
HELD_COUNT=7928
QUARANTINED_COUNT=7928
RELATIONSHIP_ASSIGNMENT_COUNT=47982
API_VISIBLE_RELATIONSHIP_COUNT=0
SEARCHABLE_RECORD_COUNT=7995
UNIQUE_SEARCH_KEY_COUNT=7995
DUPLICATE_SEARCH_KEY_COUNT=0
MISSING_SEARCH_KEY_COUNT=0
```

Missing field (4,957 governed `trace.tier` absences), explicit JSON null (676), empty string (11,136), empty array (38,991), absent accepted relationship (15,923 objects), and quarantined/held delta (7,928) remain separate metrics. Complete type/source/geography/year/folder, rights, lifecycle, quality, search, and per-endpoint distributions are in `docs/statistics/v49-release-data-profile.{md,json,csv}`.
