# Fallback and Ingest Status Policy v0

Date: 2026-05-30  
Status: Implemented in skeleton and seed workflow

## Core Rule

If a source cannot be fetched, confirmed, rights-cleared, or safely captured, the historical area should remain present.

The system should not:

- silently remove the target;
- pretend it has been ingested;
- copy images or screenshots as a workaround;
- collapse the source into a vague bibliography note.

Instead, it creates a fallback source stub.

## What a Fallback Stub Is

A fallback source stub is a structured placeholder for a historically relevant target that cannot yet become a source record.

It can expose:

- source name;
- source URL or deterministic search path;
- replacement URL if a better source is found;
- verification decision;
- blocking reason;
- next action;
- expected `IMG` state;
- public link/search action.

It is not a source record and should not receive a `SEQ` as a published sheet unless later promoted through capture, citation, rights review, and provenance.

## Public Rendering

| State | Public behavior |
|---|---|
| `search_path_only` | Show target label, source name, search path note, and `Search at source`. |
| `browser_recheck_required` | Show target label, source link, and status that automated capture failed or was blocked. |
| `page_level_recheck_required` | Show parent source link plus page/locator note; do not create a child record yet. |
| `replacement_recommended` | Show original source issue and replacement link; do not silently overwrite the original target. |
| `blocked_by_terms_or_access` | Show source link and reason; no local metadata beyond target/context fields. |

`IMG00` fallback stubs preserve the image area as an empty archive frame with linework, status text, and source action.

`IMG04` fallback stubs render without an image frame.

## Status Recording

Capture attempts should be logged in two layers:

1. `ingestion_runs` and `ingestion_events` record each batch/run attempt, event type, URL, status, message, and payload.
2. `fallback_source_stubs` record persistent unresolved targets that should remain searchable or visible in the historical framework.

The first layer is operational logging. The second layer is archive-facing research state.

## Promotion Rule

A fallback stub can be promoted only when all required evidence exists:

1. exact source URL or stable locator;
2. source-level metadata capture;
3. citation and access date;
4. rights/source terms review;
5. field provenance;
6. classification review;
7. publication surface assignment if it becomes publishable.

Until then, it remains a stub.

## Current Implementation

Implemented files:

- `db/011_ingest_contract_targets_skeleton.sql`
- `db/003_read_models.sql`
- `scripts/generate_fallback_source_stubs.py`
- `data/fallback_source_stubs.csv`
- `DATA_DICTIONARY.md`
- `FRONTEND_HANDOFF_CONTRACT.md`
- `AUTOMATED_ARCHIVE_WORKFLOW_v0.md`

Current generated result:

- 18 fallback source stubs from the first 48 target verification pass.
- 30 ready targets remain candidate manual source record drafts.

This means all 48 first targets now have a structured state:

- ready manual candidate record, or
- fallback source stub.
