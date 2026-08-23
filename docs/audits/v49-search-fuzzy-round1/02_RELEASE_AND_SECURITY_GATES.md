# Release and Security Gates

## Frozen-data boundary

| Gate | Expected | Result |
|---|---:|---|
| canonical objects | 15,923 | verified from freeze receipt |
| public/searchable documents | 7,995 | PASS |
| held/excluded documents | 7,928 | PASS |
| duplicate public stable IDs | 0 | PASS |
| indexed public fields | stable ID, title | PASS |
| files changed under `database/**` | 0 | PASS |
| frozen canonical input changed | false | PASS |
| release manifest changed | false | PASS |

The generator validates the canonical input checksum before extraction and the runtime validates the derived document checksum after import. Count or identity drift is fatal.

## Abuse bounds

| Bound | Value |
|---|---:|
| query code points | 160 |
| query tokens | 24 |
| page size | 100 |
| cursor bytes | 2,048 |
| document count | 7,995 |
| title code points | 1,024 |
| title tokens | 128 |
| title-token code points | 64 |
| edit distance | 2 |

User regex, arbitrary fields, wildcards, SQL fragments, and external services are absent. The scorer never evaluates arbitrary document payloads. Tokens containing digits and tokens below four code points do not receive typo edits.

## Dependency and network gates

```text
SEARCH_V1_AI_ENABLED=false
SEARCH_V1_LLM_ENABLED=false
SEARCH_V1_SLM_ENABLED=false
SEARCH_V1_EMBEDDINGS_ENABLED=false
SEARCH_V1_VECTOR_DB_ENABLED=false
AI_DEPENDENCY_ADDED=false
VECTOR_DEPENDENCY_ADDED=false
NEW_EXTERNAL_SEARCH_SERVICE=false
```

No runtime model/network request exists. Search uses only the same-origin Read API and the server-bundled derived artifact. No database credentials or corpus artifact enter the browser.

## Legacy removal

Deleted:

- `frontend/public/data/archive-search-v1.json` (22,695,973 bytes; 8,636 stale mock rows);
- `frontend/scripts/generate-archive-search-index.mjs`;
- `frontend/src/lib/archive-search-client.ts`;
- legacy unused SearchWorkspace component and stylesheet.

The deletion is recoverable from Git history. The replacement artifact is not public and contains exactly 7,995 safe records.

## Cursor integrity

Cursor validation rejects malformed/oversized payloads and any mismatch in release, research manifest, algorithm, index format, index checksum, normalized query hash, scope, or terminal result tuple. It cannot silently reuse an old alphabetical cursor against the relevance order.
