# SQLite reconciliation

The completed reconciliation report is preserved as evidence. SQLite was used only in its locked read-only reconciliation mode; it created no canonical rows or backfilled fields. This recovery checkpoint does not rerun it.

```text
SQLITE_CANONICAL_WRITES=0
SQLITE_BACKFILLED_ROWS=0
SQLITE_BACKFILLED_FIELDS=0
```
