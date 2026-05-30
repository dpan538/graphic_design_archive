# PostgreSQL Schema Draft v0

**Status:** Pre-implementation draft.  
**Goal:** Translate seed CSVs into a searchable, rights-aware archive index without committing to a graph database too early.

## Design Position

PostgreSQL should be the canonical database for the Launch. The archive graph can be modeled with typed edge tables over stable entities. This keeps integrity, citation, versioning, search, and export workflows simpler than starting with a specialized graph database.

## Core Tables

```sql
create table historical_nodes (
  node_id text primary key,
  node_name text not null,
  date_start int,
  date_end int,
  date_text text,
  geo_centers text,
  transnational_routes text,
  associated_formations text,
  key_media_technologies text,
  key_object_types text,
  key_people text,
  key_institutions text,
  likely_source_types text,
  search_keywords text,
  required_metadata_fields text,
  rights_risk_level text,
  underdocumented_notes text,
  editorial_note text,
  source_basis_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table movements (
  movement_id text primary key,
  name text not null,
  alternate_names text,
  date_start int,
  date_end int,
  date_text text,
  region text,
  group_type text,
  associated_people text,
  associated_institutions text,
  representative_media text,
  relation_to_graphic_design text,
  source_confidence text,
  search_terms text,
  authority_scheme text,
  authority_id text,
  authority_status text default 'needs_resolution',
  editorial_scope_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table media_technologies (
  media_id text primary key,
  term text not null,
  term_type text,
  definition text,
  date_start int,
  date_end int,
  date_text text,
  relation_to_graphic_design text,
  associated_source_types text,
  required_metadata_fields text,
  search_keywords text,
  rights_display_issues text,
  authority_scheme text,
  authority_id text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table sources (
  source_id text primary key,
  name text not null,
  url text not null,
  source_type text,
  access_method text,
  api_base_or_endpoint text,
  iiif_support text,
  oai_pmh_support text,
  dataset_support text,
  geo_coverage text,
  historical_coverage text,
  graphic_design_relevance text,
  likely_record_types text,
  rights_summary text,
  rights_uri_support text,
  metadata_quality_estimate text,
  stable_identifiers text,
  automated_ingestion text,
  link_only_safer text,
  priority text,
  notes text,
  last_verified_date date,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table search_vocabulary (
  term_id text primary key,
  term text not null,
  normalized_term text not null,
  term_class text not null,
  language text default 'und',
  alternate_forms text,
  broader_term text,
  narrower_term text,
  related_terms text,
  preferred_for_query boolean default true,
  query_context text,
  authority_scheme text,
  authority_id text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table rights_strategies (
  strategy_id text primary key,
  source_category text not null,
  rights_signal text,
  ingest_policy text,
  display_policy text,
  review_required text,
  citation_required text,
  attrib_required text,
  thumbnail_allowed text,
  full_image_allowed text,
  iiif_embed_allowed text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

## Archive Index Tables

These are not populated by seed CSVs yet. They define the next implementation layer.

## First Experimental Ingest Scope Layer

`db/009_first_ingest_scope_skeleton.sql` adds the operational layer needed before the first controlled ingest.

It extends:

- `regional_movements` with movement mode, script flags, collective authorship, periodical relevance, protocol sensitivity, and source priority class.
- `regional_event_nodes` with date precision, anchor strength, source-record requirement, browse priority, and web-archive relevance.
- `sources` with automation status, rights basis, record-level rights requirement, image-zone defaults, preview/thumbnail/IIIF capability, API-key flag, and protocol sensitivity.
- `search_vocabulary` with query profile IDs, scripts, term types, preferred flags, transliteration links, and false-positive notes.
- `experimental_ingest_candidates` with first-ingest scope cell metadata, target record counts, HN/MV/event links, query profiles, review level, and expected surface type.
- `source_records` with parent-record links, source language/script, translated title, capture datetime, issue identifier, page number, record family, protocol flag, and ICIP flag.
- `rights_reviews` with rights evidence URL/note and normalized image-zone decision.
- `classifications` with movement assignment mode, authority confidence, relation confidence, and protocol sensitivity.

This layer does not start crawling. It defines what must be reviewed and represented before source records are fetched.

```sql
create type entity_type as enum (
  'work_object',
  'person',
  'organization',
  'movement_period',
  'medium_technology',
  'place',
  'text_publication',
  'theme',
  'source',
  'source_record',
  'image_asset'
);

create table entities (
  entity_id text primary key,
  entity_type entity_type not null,
  preferred_label text not null,
  alternate_labels text,
  description text,
  date_start int,
  date_end int,
  date_text text,
  authority_scheme text,
  authority_id text,
  authority_status text default 'needs_resolution',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table source_records (
  source_record_id text primary key,
  source_id text not null references sources(source_id),
  source_identifier text,
  source_record_url text not null,
  source_title text,
  source_creator text,
  source_date_text text,
  source_rights_text text,
  source_rights_uri text,
  capture_method text not null,
  access_date date not null,
  raw_json jsonb,
  normalized_entity_id text references entities(entity_id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table citations (
  citation_id text primary key,
  source_record_id text references source_records(source_record_id),
  citation_text text not null,
  citation_style text,
  url text,
  access_date date,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table assertions (
  assertion_id text primary key,
  subject_entity_id text not null references entities(entity_id),
  predicate text not null,
  object_entity_id text not null references entities(entity_id),
  source_record_id text references source_records(source_record_id),
  citation_id text references citations(citation_id),
  assertion_type text not null,
  confidence text not null,
  note text,
  reviewed_by text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table classifications (
  classification_id text primary key,
  entity_id text not null references entities(entity_id),
  classification_type text not null,
  classification_value text not null,
  source_record_id text references source_records(source_record_id),
  basis text not null,
  confidence text not null,
  reviewer text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table image_assets (
  image_asset_id text primary key,
  source_record_id text references source_records(source_record_id),
  source_image_url text,
  iiif_manifest_url text,
  iiif_canvas_id text,
  rights_uri text,
  rights_label text,
  image_use_policy text not null,
  credit_line text,
  local_copy_permitted boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

## Search Index Draft

```sql
create table searchable_documents (
  search_doc_id text primary key,
  entity_id text references entities(entity_id),
  source_record_id text references source_records(source_record_id),
  document_type text not null,
  title text,
  body text,
  facets jsonb,
  tsv tsvector generated always as (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(body, '')), 'B')
  ) stored,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index searchable_documents_tsv_idx
  on searchable_documents using gin(tsv);

create index searchable_documents_facets_idx
  on searchable_documents using gin(facets);
```

## Reproducibility Rules

- Every public record must trace back to `source_records`.
- Every public citation must be stored in `citations`.
- Every project-created relation must be stored as an `assertion`.
- Source metadata and normalized metadata must remain separable.
- Image display must be controlled by `image_assets.image_use_policy`.
- AI-generated suggestions must not enter `assertions` without human review and citation.
- Geography, date, language/script, and regional coverage fields must exist before frontend design-system freeze.

## Global Classification Tables

Implemented in `db/005_global_classification_skeleton.sql`:

- `classification_axes`: required classification axes for geography, dates, historical nodes, movements/formations, media, language/script, source, rights, and provenance.
- `geographies`: macro regions, countries, territories, city/context areas, transnational contexts, and historical jurisdictions.
- `geography_aliases`: multilingual and transliterated geography labels for search and authority cleanup.
- `regional_movements`: regional movements, formations, publishing cultures, state systems, counterpublics, technical regimes, and digital/platform formations.
- `regional_event_nodes`: dateable regional historical nodes connecting geography, source needs, rights risks, and historical spine nodes.
- `normalized_dates`: source-preserving date normalization for objects, publications, events, captures, and digitization records.
- `entity_geographies`: reviewed geography links for normalized entities.
- `source_record_geographies`: source-record geography links preserving source text and relation type.

## Publication Surface Tables

Implemented in `db/006_publication_surface_skeleton.sql`:

- `display_templates`: reusable component/tier/layout definitions for the archive-cabinet interface.
- `publication_surfaces`: public paper surfaces with global `SEQ`, display number, surface type, `TIER`, `layout_id`, and `image_zone`.
- `publication_surface_pages`: per-page records for `p01`, `p02`, appendices, and overflow.
- `surface_table_rows`: fixed table-row mapping for `SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`, `RELATIONS`, and `CITATIONS`.
- `folder_views`: historical node, movement, region, geography, source, and theme folders as filter views.
- `folder_memberships`: many-to-many membership between folders and shared publication surfaces.
- `filing_registry_cards`: public classification ledgers.
- `filing_registry_members`: member-page rows for registration cards.
- `sparse_cards`: stubs, aliases, cross-references, and not-yet-promotable records.
- `archive_bookmarks`: pre-authored method notes and reading aids.

## Authority Normalization Tables

Implemented in `db/007_authority_normalization_skeleton.sql`:

- `evidence_bundles`: grouped evidence for assertions, authority matches, and classifications.
- `evidence_bundle_items`: citations, source records, external identifiers, and authority records inside an evidence bundle.
- `authority_resolution_events`: event log for proposed, reviewed, rejected, deprecated, local, and unresolved authority matches.
- `entity_appellations`: source labels, preferred labels, transliterations, translations, community-preferred labels, deprecated labels, language/script codes, and provenance.
- `geography_appellations`: multilingual and historical place labels with validity dates and source/authority provenance.
- extensions to `external_identifiers`, `authority_sources`, `relation_predicates`, `assertions`, `classifications`, `normalized_dates`, `source_records`, `entities`, `geographies`, and `rights_reviews`.

Important rule:

- `visually_resembles` may be based on visual comparison alone, but must remain non-causal and clearly marked.
- Interpretive predicates such as `influenced_by`, `associated_with`, `part_of`, movement membership, and identity claims require documentary, source-metadata, or scholarly evidence.

## Source and Rights Policy Tables

Implemented in `db/008_source_rights_policy_skeleton.sql`:

- source-level default record policy, display policy, image zone, license, terms, robots, rate-limit, API-key, and protocol/privacy fields on `sources`.
- versioned source terms-review fields on `source_terms_reviews`.
- item-level override fields on `rights_reviews`, including evidence URL/date, display booleans, manual-review flag, normalized display policy, and normalized image zone.
- image asset origin and local-copy fields on `image_assets`.
- rights/terms metrics and policy snapshot links on `ingestion_runs`.
- `experimental_ingest_candidates` for controlled first ingest planning.

Rule:

- public rendering must consume rights decisions; it must not decide image display by itself.
- unknown image rights default to `IMG00` / source-link-only. `IMG00` keeps the fixed image area but renders an intentionally empty archive frame only, with no source image/thumbnail/screenshot.
- `IMG00` through `IMG03` assume an image frame exists and are resolved by copyright/display permission.
- `IMG04` means a pure text page with no image frame. It is a script/template signal, not a copyright level. Image zone describes image presence state; size is controlled separately by tier/layout/template.

## Next Implementation Step

1. Import seed CSVs into staging tables.
2. Validate required IDs and date fields.
3. Convert selected seed rows into `entities`.
4. Create first manual `source_records` for 20-30 test items.
5. Populate `searchable_documents`.
6. Test deterministic search and faceted filtering before building frontend UI.
