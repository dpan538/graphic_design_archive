# `pageByKey` 503 reproduction

The exact canonical failure was reproduced before modification against an isolated 32-object sealed fixture database:

```text
METHOD=GET
URL=http://api-contract.local/api/v1/releases/v49-db-closure-api-v1/search?q=Phase%202S&first=5
HTTP_STATUS=503
ERROR=(0 , _pagination.pageByKey) is not a function
RUNTIME=node v22.21.0 / Jiti server route dispatch
TYPEOF_PAGE_BY_KEY=undefined
FIRST_APPLICATION_FRAME=PostgresArchiveRepository.search postgres-repository.ts:48:44
```

`raw/api/page-by-key-before.json` includes the command, mode, request, headers/body, full stack, module resolution, available exports, import/export form, and runtime types.
