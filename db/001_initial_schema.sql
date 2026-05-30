-- Modern Graphic Design History Archive Index
-- Initial PostgreSQL schema draft
-- Status: pre-launch skeleton, generated from Methodology v0 and seed data design.

create extension if not exists pg_trgm;

create table if not exists historical_nodes (
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

create table if not exists movements (
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

create table if not exists media_technologies (
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

create table if not exists sources (
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

create table if not exists search_vocabulary (
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

create table if not exists rights_strategies (
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

do $$
begin
  if not exists (select 1 from pg_type where typname = 'entity_type') then
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
  end if;
end
$$;

create table if not exists entities (
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

create table if not exists source_records (
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

create table if not exists citations (
  citation_id text primary key,
  source_record_id text references source_records(source_record_id),
  citation_text text not null,
  citation_style text,
  url text,
  access_date date,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists assertions (
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

create table if not exists classifications (
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

create table if not exists image_assets (
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

create table if not exists searchable_documents (
  search_doc_id text primary key,
  entity_id text references entities(entity_id),
  source_record_id text references source_records(source_record_id),
  seed_table text,
  seed_id text,
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

create index if not exists historical_nodes_name_trgm_idx
  on historical_nodes using gin (node_name gin_trgm_ops);

create index if not exists movements_name_trgm_idx
  on movements using gin (name gin_trgm_ops);

create index if not exists media_technologies_term_trgm_idx
  on media_technologies using gin (term gin_trgm_ops);

create index if not exists sources_name_trgm_idx
  on sources using gin (name gin_trgm_ops);

create index if not exists searchable_documents_tsv_idx
  on searchable_documents using gin (tsv);

create index if not exists searchable_documents_facets_idx
  on searchable_documents using gin (facets);
