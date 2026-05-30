-- Modern Graphic Design History Archive Index
-- Operational database skeleton
-- Status: pre-ingestion. This file adds governance, review, provenance,
-- versioning, and handoff tables. It intentionally does not fetch data.

do $$
begin
  if not exists (select 1 from pg_type where typname = 'workflow_status') then
    create type workflow_status as enum (
      'draft',
      'candidate',
      'source_reviewed',
      'rights_reviewed',
      'ingested',
      'normalized',
      'classified',
      'relation_reviewed',
      'published',
      'deprecated',
      'blocked'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'review_status') then
    create type review_status as enum (
      'not_started',
      'pending',
      'approved',
      'needs_revision',
      'rejected',
      'blocked'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'rights_state') then
    create type rights_state as enum (
      'metadata_open',
      'metadata_limited',
      'image_open',
      'image_embed_only',
      'thumbnail_only',
      'link_only',
      'unknown',
      'do_not_ingest'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'confidence_level') then
    create type confidence_level as enum (
      'high',
      'medium',
      'low',
      'unknown'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'ingestion_status') then
    create type ingestion_status as enum (
      'planned',
      'running',
      'completed',
      'completed_with_warnings',
      'failed',
      'cancelled',
      'blocked'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'assertion_status') then
    create type assertion_status as enum (
      'draft',
      'reviewed',
      'published',
      'deprecated',
      'disputed'
    );
  end if;
end
$$;

create table if not exists schema_versions (
  version_id text primary key,
  version_label text not null,
  applied_at timestamptz default now(),
  description text,
  migration_file text not null
);

insert into schema_versions (version_id, version_label, description, migration_file)
values
  ('schema_001', 'Initial schema', 'Seed tables, core entities, source records, citations, assertions, image assets, searchable documents.', 'db/001_initial_schema.sql'),
  ('schema_002', 'Operational skeleton', 'Governance, review, provenance, ingestion logs, release snapshots, and handoff contracts.', 'db/002_operational_skeleton.sql')
on conflict (version_id) do nothing;

create table if not exists project_releases (
  release_id text primary key,
  release_label text not null,
  release_type text not null,
  status review_status default 'pending',
  description text,
  created_at timestamptz default now(),
  published_at timestamptz,
  citation_text text,
  doi text,
  notes text
);

create table if not exists release_files (
  release_file_id text primary key,
  release_id text not null references project_releases(release_id),
  file_path text not null,
  file_type text,
  checksum_sha256 text,
  created_at timestamptz default now(),
  notes text
);

create table if not exists authority_sources (
  authority_source_id text primary key,
  name text not null,
  url text,
  authority_type text,
  description text,
  preferred_for text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists external_identifiers (
  external_identifier_id text primary key,
  entity_id text references entities(entity_id),
  seed_table text,
  seed_id text,
  authority_source_id text references authority_sources(authority_source_id),
  authority_scheme text not null,
  authority_id text not null,
  authority_url text,
  confidence confidence_level default 'unknown',
  review_status review_status default 'pending',
  source_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint external_identifier_target_check check (
    entity_id is not null or (seed_table is not null and seed_id is not null)
  )
);

create table if not exists entity_aliases (
  alias_id text primary key,
  entity_id text not null references entities(entity_id),
  alias text not null,
  language text default 'und',
  alias_type text,
  source_record_id text references source_records(source_record_id),
  confidence confidence_level default 'unknown',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists relation_predicates (
  predicate_id text primary key,
  predicate text not null unique,
  label text not null,
  inverse_predicate text,
  description text,
  evidence_required text,
  default_confidence confidence_level default 'unknown',
  allows_uncited_use boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists classification_schemes (
  scheme_id text primary key,
  scheme_name text not null,
  scheme_type text,
  description text,
  authority_source_id text references authority_sources(authority_source_id),
  local_only boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists source_terms_reviews (
  source_terms_review_id text primary key,
  source_id text not null references sources(source_id),
  review_status review_status default 'pending',
  reviewed_by text,
  reviewed_at timestamptz,
  terms_url text,
  robots_url text,
  api_terms_url text,
  metadata_policy rights_state default 'unknown',
  image_policy rights_state default 'unknown',
  scraping_policy rights_state default 'unknown',
  automated_ingestion_allowed boolean default false,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists rights_reviews (
  rights_review_id text primary key,
  source_id text references sources(source_id),
  source_record_id text references source_records(source_record_id),
  image_asset_id text references image_assets(image_asset_id),
  rights_state rights_state not null,
  rights_uri text,
  rights_label text,
  review_status review_status default 'pending',
  reviewed_by text,
  reviewed_at timestamptz,
  basis text not null,
  display_policy text,
  ingest_policy text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint rights_review_target_check check (
    source_id is not null or source_record_id is not null or image_asset_id is not null
  )
);

create table if not exists ingestion_runs (
  ingestion_run_id text primary key,
  source_id text not null references sources(source_id),
  run_label text,
  status ingestion_status default 'planned',
  ingestion_mode text not null,
  initiated_by text,
  started_at timestamptz,
  completed_at timestamptz,
  source_terms_review_id text references source_terms_reviews(source_terms_review_id),
  config_json jsonb,
  records_seen int default 0,
  records_created int default 0,
  records_updated int default 0,
  records_skipped int default 0,
  records_failed int default 0,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists ingestion_events (
  ingestion_event_id text primary key,
  ingestion_run_id text not null references ingestion_runs(ingestion_run_id),
  event_level text not null,
  event_type text not null,
  source_identifier text,
  source_record_url text,
  message text not null,
  payload_json jsonb,
  created_at timestamptz default now()
);

create table if not exists source_record_snapshots (
  snapshot_id text primary key,
  source_record_id text not null references source_records(source_record_id),
  ingestion_run_id text references ingestion_runs(ingestion_run_id),
  snapshot_type text not null,
  captured_at timestamptz default now(),
  content_hash_sha256 text,
  raw_json jsonb,
  raw_text text,
  notes text
);

create table if not exists editorial_reviews (
  editorial_review_id text primary key,
  review_target_type text not null,
  review_target_id text not null,
  review_status review_status default 'pending',
  reviewer text,
  reviewed_at timestamptz,
  checklist_json jsonb,
  decision_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists workflow_events (
  workflow_event_id text primary key,
  target_type text not null,
  target_id text not null,
  from_status workflow_status,
  to_status workflow_status not null,
  changed_by text,
  changed_at timestamptz default now(),
  reason text,
  evidence_json jsonb
);

create table if not exists assertion_reviews (
  assertion_review_id text primary key,
  assertion_id text not null references assertions(assertion_id),
  assertion_status assertion_status default 'draft',
  reviewer text,
  reviewed_at timestamptz,
  evidence_note text,
  dispute_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists search_index_queue (
  queue_id text primary key,
  target_type text not null,
  target_id text not null,
  action text not null,
  status ingestion_status default 'planned',
  queued_at timestamptz default now(),
  processed_at timestamptz,
  error_message text
);

create table if not exists export_jobs (
  export_job_id text primary key,
  release_id text references project_releases(release_id),
  status ingestion_status default 'planned',
  export_type text not null,
  requested_by text,
  started_at timestamptz,
  completed_at timestamptz,
  output_path text,
  checksum_sha256 text,
  row_counts_json jsonb,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists audit_log (
  audit_id text primary key,
  actor text,
  action text not null,
  target_type text not null,
  target_id text not null,
  before_json jsonb,
  after_json jsonb,
  reason text,
  created_at timestamptz default now()
);

create index if not exists external_identifiers_entity_idx
  on external_identifiers(entity_id);

create index if not exists external_identifiers_seed_idx
  on external_identifiers(seed_table, seed_id);

create index if not exists source_terms_reviews_source_idx
  on source_terms_reviews(source_id);

create index if not exists rights_reviews_source_record_idx
  on rights_reviews(source_record_id);

create index if not exists ingestion_runs_source_idx
  on ingestion_runs(source_id);

create index if not exists ingestion_events_run_idx
  on ingestion_events(ingestion_run_id);

create index if not exists source_record_snapshots_record_idx
  on source_record_snapshots(source_record_id);

create index if not exists workflow_events_target_idx
  on workflow_events(target_type, target_id);

create index if not exists search_index_queue_status_idx
  on search_index_queue(status, queued_at);

create index if not exists audit_log_target_idx
  on audit_log(target_type, target_id);
