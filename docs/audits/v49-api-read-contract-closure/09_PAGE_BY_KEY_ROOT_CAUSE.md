# `pageByKey` root cause

```text
PAGE_BY_KEY_ROOT_CAUSE=PROVEN:ABSENT_NAMED_EXPORT_WITH_NAMED_PRODUCTION_IMPORT
PAGE_BY_KEY_DEFINITION_FILE=frontend/src/lib/read-platform/pagination.ts
PAGE_BY_KEY_EXPORT_FORM_BEFORE=ABSENT_NAMED_EXPORT
PAGE_BY_KEY_IMPORT_FILE=frontend/src/lib/read-platform/server/postgres-repository.ts
PAGE_BY_KEY_IMPORT_FORM=NAMED_IMPORT
PAGE_BY_KEY_RUNTIME_TYPE_BEFORE=undefined
PAGE_BY_KEY_EXPECTED_TYPE=function
```

This was not ESM/CJS interop, a stale generated file, mock drift, a planner/database failure, or a circular dependency. The resolved module exported `decodeCursor`, `encodeCursor`, `keysetPage`, `requireFirst`, and `resultError`, but not the symbol that production search imported and called.
