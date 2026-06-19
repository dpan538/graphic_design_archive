# Pre-freeze Chunked Rebuild v1

Scope: sandbox chunked rebuild validator. It processes capture rows in chunks and writes metrics only; it does not overwrite generated public payloads or frontend files.

## Summary

- scope: all-capture (Record-file selection mode.)
- chunk_size: 2000 (Maximum rows per chunk.)
- record_files: 44 (Capture CSV inputs scanned.)
- raw_input_rows: 19886 (Rows before P0 exclusion and dedupe.)
- prefreeze_excluded_rows: 3549 (Rows skipped by pre-freeze exclusion table.)
- deduped_candidate_rows: 16294 (Rows after exclusion and dedupe.)
- chunks_total: 9 (Chunks executed.)
- chunks_ok: 9 (Chunks built successfully.)
- chunks_error: 0 (Chunks with exceptions.)
- chunk_surface_sum: 16185 (Sum of surfaces built per chunk; not a finalized public payload count.)
- chunk_distinct_source_sum: 15079 (Per-chunk source counts summed; cross-chunk duplicates are not collapsed here.)
- chunk_source_visible_surface_sum: 16004 (Per-chunk source-visible surface sum.)
- chunk_verified_open_surface_sum: 15406 (Per-chunk verified-open surface sum.)

## Chunk Results

- chunk_0001: rows=2000, surfaces=1968, sources=1794, states=IMG00:1;IMG01:6;IMG02:14;IMG03:1940;IMG04:7, status=ok
- chunk_0002: rows=2000, surfaces=1950, sources=1828, states=IMG00:7;IMG02:37;IMG03:1904;IMG04:2, status=ok
- chunk_0003: rows=2000, surfaces=2000, sources=1815, states=IMG00:6;IMG01:9;IMG02:47;IMG03:1929;IMG04:9, status=ok
- chunk_0004: rows=2000, surfaces=1992, sources=1853, states=IMG00:21;IMG02:82;IMG03:1880;IMG04:9, status=ok
- chunk_0005: rows=2000, surfaces=2000, sources=1888, states=IMG00:3;IMG02:79;IMG03:1893;IMG04:25, status=ok
- chunk_0006: rows=2000, surfaces=1997, sources=1884, states=IMG00:1;IMG02:83;IMG03:1910;IMG04:3, status=ok
- chunk_0007: rows=2000, surfaces=1995, sources=1911, states=IMG00:1;IMG02:62;IMG03:1911;IMG04:21, status=ok
- chunk_0008: rows=2000, surfaces=1989, sources=1863, states=IMG02:116;IMG03:1853;IMG04:20, status=ok
- chunk_0009: rows=294, surfaces=294, sources=243, states=IMG00:1;IMG01:4;IMG02:59;IMG03:186;IMG04:44, status=ok

## Interpretation

- This pass validates that candidate rows can be rebuilt in batches of 2,000 or fewer.
- The summed chunk source count is diagnostic only; a final official payload must still perform global grouping, folder aggregation, and object-level release audits.
- P0 rows remain available in capture CSVs but are skipped from this candidate rebuild through the exclusion table.
