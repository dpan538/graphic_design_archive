# File Naming and Archival Storage v0

Date: 2026-05-30

Source report:

- `File Naming and Archival Storage Rulebook for a Rights-Aware Graphic Design History Archive Index.docx`

## Purpose

This document defines how project files, identifiers, generated outputs, and archival production layers should be organized.

The filesystem should help humans review work, but it must not be the true identity system. Stable IDs live in data fields. Filenames are review aids and build artifacts.

## Storage Layers

| Layer | Role | Human edited? | Typical formats |
|---|---|---|---|
| raw | Original source responses, request metadata, headers, and source payloads. | No | JSON, HTML, TXT, PDF, WARC |
| normalized | Script-derived rows parsed from raw captures. | No | CSV, JSONL |
| canonical | Human-reviewed source records, entity records, rights records, authority lists. | Yes | YAML, Markdown |
| derived | Assignments, summaries, relation tables, publication inputs, databases. | No | CSV, JSON, SQLite |
| builds | Rendered outputs from a build run. | No | HTML, JSON, PDF |
| releases | Frozen public/citable exports. | No | HTML, JSON, CSV, checksums |

## ID Strategy

| Form | Object | Scope | User-facing? | Rule |
|---|---|---|---|---|
| `CB001` | Capture batch | Project-wide | Usually no | Never reuse |
| `R0001` | Row ordinal within a batch | Batch-local | No | Never reuse within batch |
| `CB001-R0001` | Full capture row ID | Project-wide | No | Preferred capture row key |
| `ECAP001` | Legacy capture alias | Project-wide alias | No | Keep only as alias if already minted |
| `SRC001` | Source registry/source record ID | Project-wide | Sometimes | Never reuse |
| `ENT000001` | Normalized entity ID | Project-wide | Later optional | Never reuse |
| `C01` | Ratified historical/folder cell | Controlled vocabulary | Yes | Never reuse |
| `PC01` | Proposed cell | Proposal namespace | Usually visible as proposed | Never reuse, even if rejected |
| `SEQ000001` | Global publication sequence | Project-wide | Yes | Never reuse once minted |
| `GD/...` | Display number | Derived public label | Yes | Do not use as primary key |
| `BUILD-YYYYMMDDThhmmssZ` | Build run | Project-wide | No | Immutable |
| `REL-YYYY-MM-DD` | Public release | Project-wide | Sometimes | Immutable |
| `SNAP-YYYYMMDDThhmmssZ` | Data snapshot | Project-wide | Internal/citable | Immutable |

## Current Naming Decision

The current `ECAP001` style should be treated as a legacy alias for capture batch 001. Before the next larger batch, capture rows should move to:

```text
CB001-R0001
CB001-R0002
...
```

The current data can retain `ECAP001` in an alias field during migration to avoid breaking existing references.

## Recommended Directory Tree

This is the target structure. It should be adopted gradually so existing scripts do not break.

```text
project-root/
  docs/
    rulebooks/
    decisions/
    methods/
    reports/
  prompts/
    deep_research/
    codex/
    cursor/
  schemas/
    jsonschema/
    csv/
    examples/
  authority/
    eras.yaml
    cells.yaml
    proposed_cells.yaml
    folder_types.yaml
    relation_types.yaml
    rights_statements.yaml
    publication_tiers.yaml
  data/
    source_registry/
      source_registry__v1.csv
    capture_batches/
      CB001/
        manifest.json
        source_summary.csv
        records.csv
        cell_assignments.csv
        cell_summary.csv
        next_generation_queue.csv
        raw/
          CB001-R0001/
            request.json
            response_body.json
            headers.json
            capture_meta.json
    source_records/
      drafts/
        SRC001/
          record.yaml
          rights.yaml
      canonical/
        SRC001/
          record.yaml
          rights.yaml
          provenance.yaml
      tombstones/
    entities/
      drafts/
      canonical/
    publication_surfaces/
      sheets/
      cards/
      stubs/
      folders/
      appendices/
    derived/
      sqlite/
      search/
      assignments/
    snapshots/
    releases/
  db/
  scripts/
    ingest/
    normalize/
    validate/
    publish/
  frontend_handoff/
```

## Current Project Compatibility

The project currently uses flat root files and flat `data/*.csv` outputs. Do not reorganize everything at once. The safe migration is:

1. Keep current root docs stable for now.
2. Add new target folders when the next batch begins.
3. Mirror `capture_batch_001_*` into `data/capture_batches/CB001/` after scripts are updated.
4. Keep generated flat CSVs until Cursor/frontend integration is stable.
5. Move rulebooks into `docs/rulebooks/` only when imports and links are updated.

## Filename Grammar

Inside an ID folder:

```text
<role>[__<qualifier>][__<version-or-timestamp>].<ext>
```

Examples:

```text
record.yaml
record.stub.yaml
rights.yaml
provenance.yaml
capture_meta.yaml
response_body.json
sheet__tier-m__p001.html
```

Flat exports:

```text
<dataset>__<scope-or-release>__<version>.ext
```

Examples:

```text
source_registry__v1.csv
capture_rows__CB001__v1.csv
publication_index__REL-2026-05-30__v1.json
display_aliases__v1.csv
```

## Extension Policy

| Extension | Use | Editing rule |
|---|---|---|
| `.yaml` | Canonical human-reviewed records and authority/config files. | Human-edited, schema-validated |
| `.json` | Manifests, raw payloads, frontend payloads. | Generated unless explicitly in canonical config |
| `.jsonl` | Large machine-readable exports. | Generated |
| `.csv` | Batch rows, summaries, exchange tables. | Generated or script-owned |
| `.md` | Rulebooks, decisions, logs, authored reports. | Human/Codex-authored |
| `.html` / `.pdf` | Rendered publication surfaces. | Generated |
| `.log` | Automation logs. | Generated |
| `.txt` | Fixity manifests, notes, BagIt tags. | Generated or review notes |
| `.warc.gz` | Optional raw web capture package. | Generated |

## Display Numbers

The public display number should not encode historical-node or movement membership. Historical nodes and folder memberships are metadata, not display-number segments.

```text
GD / {ERA} / {SEQ} / {TIER}-p{PAGE}
```

But it must not be used as a database key or folder path. Store:

- `display_number`: exact human-readable label;
- `display_slug`: filesystem-safe derived label;
- `seq_id`: stable global publication sequence;
- `surface_page`: page number.

Example:

```text
display_number: GD/1890/SEQ000231/M-p001
display_slug: gd-1890-seq000231-m-p001
seq_id: SEQ000231
```

Historical-node IDs (`HN*`) and movement IDs (`MV*`, `RM*`) remain available in classification metadata and folder memberships. They should not be required in the public display number because a surface can appear in many public folders.

## Raw Capture Rules

Every capture row should preserve:

- batch ID;
- row ID;
- source ID;
- request URL;
- query parameters;
- access datetime;
- HTTP status;
- headers when available;
- response body or payload;
- parser version;
- checksum;
- raw payload path.

Raw files must not be edited manually.

## Generated vs Authored Files

Generated files:

- capture batch records;
- source summaries;
- cell assignments;
- cell summaries;
- next-generation queues;
- seed SQL;
- SQLite snapshots;
- publication surfaces.

Authored or reviewed files:

- rulebooks;
- decisions;
- source record canonical YAML;
- rights review YAML;
- proposed cell review notes;
- project log.

Generated files may be regenerated. Authored files should be changed deliberately and logged.

## Rights-Sensitive Storage

Rules:

- Do not store local image files by default.
- Store image URLs, IIIF manifests, viewer URLs, and rights evidence as metadata.
- `IMG03` does not automatically permit local copying.
- `local_copy_permitted` must remain false unless a record-level rights review explicitly permits it.
- Never infer rights from file extension, image availability, age, or visual accessibility alone.
- Store takedown/review notes separately from public rights summary when needed.

## Publication Surface Storage

Generated surfaces should eventually live under:

```text
data/publication_surfaces/
  sheets/SEQ000231/
    sheet__tier-m__p001.html
    sheet__tier-m__p002.html
    surface.json
  cards/
  stubs/
  folders/
  appendices/
```

Each surface must link back to:

- source record ID;
- entity ID when present;
- folder memberships;
- display number;
- raw/canonical provenance chain;
- generation build ID.

## Collaboration Rules

- Codex may generate and update scripts, derived CSVs, rulebooks, and validation docs.
- Cursor should use API contracts, read models, and frontend handoff files, not infer from raw CSVs alone.
- Human review is required for proposed cell acceptance, rights promotion, contested classifications, and publication release.
- Do not manually edit generated CSVs after a script owns them.
- Do not move large folder structures until scripts are updated together.

## Anti-Patterns

- Using filenames as primary keys.
- Using `GD/...` display numbers as database keys.
- Editing raw payloads.
- Mixing raw, canonical, derived, and published files in one directory.
- Treating `.csv` as canonical when the record needs review history.
- Storing images locally because a URL exists.
- Deleting rejected proposals instead of keeping tombstones.
