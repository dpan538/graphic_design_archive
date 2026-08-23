# Search Index Specification

## Identity

| Property | Value |
|---|---|
| Format | `gda-search-documents-v1` |
| Algorithm | `v49-lexical-fuzzy-1` |
| Release ID | `v49-api-contract-fresh-c` |
| Release manifest SHA-256 | `4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a` |
| Source SHA | `c0ca9a1d4745cfd1054b924c648e57887830960d` |
| Source tree | `f8ecd0046a4b8e3c1be657b2a31ac0b863f08ad0` |
| Documents | 7,995 |
| Held/excluded | 7,928 |
| Raw bytes | 1,435,371 |
| Gzip bytes | 256,941 |
| Document SHA-256 | `35a6b7e1f8b749fca0ebfda9cf84f265de58d69fe6ef2bac0a4a2a9d263b1522` |

## Source and field policy

The generator verifies `database/FREEZE_V49.json` and the SHA-256 of `generated/public_surfaces_prefreeze_candidate_v48.json`. It selects only `trace.tier === "source_verified"`, the frozen source of the v49 eligible membership, then asserts exactly 7,995 eligible and 7,928 held rows.

Only `surfaceId` and `title` cross into the artifact. The eligibility field is used only as a build gate and is not serialized. Creator, date, place, type, medium, source, descriptions, tables, folders, rights, images, and TRACE data are explicitly excluded and included in the source-field-policy hash.

Each document is a fixed tuple:

```text
[stableId, displayTitle, primary, compatibility, latinFolded]
```

Documents are sorted by stable ID. JSON serialization is one deterministic line with a trailing newline.

## Artifacts

```text
frontend/generated/search-v49/
├── documents.json
├── manifest.json
└── CHECKSUMS.sha256
```

The files are non-authoritative, release-pinned, regenerable, read-only at runtime, and outside `public/`. A static server-only import lets Next include them in the API function without exposing them in the `/search` client bundle. The production build reports `/search` at 113 kB first-load JavaScript, not a corpus-sized bundle.

## Manifest and runtime gates

The manifest records release/projection/canonical digests, source SHA/tree, field-policy hash, normalization/Unicode versions, algorithm/format versions, counts, timestamp, byte lengths, checksum, ordering, public fields, and fixed work bounds.

Lazy initialization recomputes the document SHA and byte length from parsed JSON, validates every identity/count/version/bound, hydrates once, and checks stable-ID uniqueness. Provider open also requires the exact release ID + research manifest SHA. Any mismatch yields `INTEGRITY_FAILURE` or `RELEASE_NOT_FOUND`; it never degrades to empty search.

## Rebuild

```bash
npm run generate:search-v49
npm run verify:search-v49-index
```

The benchmark executes two consecutive builds and requires identical checksum files. Final result: `INDEX_REBUILD_DETERMINISTIC=true`.

`generated_at` is the audited release timestamp rather than wall-clock build time, so rebuilding does not change content.

## Cursor contract

The base64url cursor binds cursor version, release ID, research manifest SHA, algorithm version, index format, index SHA, normalized-query SHA-256, scope, terminal score, terminal normalized title, and terminal stable ID. The terminal tuple must exist in the recomputed ordered results. Query, scope, release, index, or algorithm drift invalidates the cursor.
