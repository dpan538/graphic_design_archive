# API fix

The minimal fix adds a named generic `pageByKey` wrapper over the existing `keysetPage` contract and makes PostgreSQL search use the complete release-pinned result set with the existing keyset cursor. The search query is parameterized, literal-substring based (`%` and `_` do not widen it), trimmed, length/scope validated, and ordered by stable title + surface ID keys.

Related closure fixes preserve semantics: current release selection reads `api_v1.current_version_status`; missing unpublished relation/claim/corpus/folder singletons return deterministic 404 rather than infrastructure 503; empty paged collections validate cursors/page size; HTTP provider preserves API error codes; and the testable dispatcher moved to a server-only controller so Next.js route exports remain valid.

```text
PAGE_BY_KEY_RUNTIME_TYPE_AFTER=function
PAGE_BY_KEY_MODULE_CONTRACT_TEST=PASS
SEARCH_ROUTE_INTEGRATION_TEST=PASS
DATABASE_SCHEMA_CHANGED=false
DATABASE_PERMISSION_CHANGED=false
HELD_FALLBACK_ADDED=false
RIGHTS_WIDENING_COUNT=0
```
