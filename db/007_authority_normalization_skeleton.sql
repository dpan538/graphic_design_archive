-- Modern Graphic Design History Archive Index
-- Authority, vocabulary, appellation, and evidence normalization skeleton.
-- Purpose: make multilingual authority control and uncertainty-preserving
-- normalization explicit before experimental ingest and design-system freeze.

do $$
begin
  if not exists (select 1 from pg_type where typname = 'authority_match_status') then
    create type authority_match_status as enum (
      'needs_resolution',
      'candidate_match',
      'reviewed_match',
      'multiple_possible_matches',
      'no_external_authority',
      'local_authority',
      'rejected_match',
      'deprecated'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'appellation_type') then
    create type appellation_type as enum (
      'preferred',
      'alternate',
      'source_label',
      'transliteration',
      'translation',
      'community_preferred',
      'deprecated',
      'hidden_search'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'mapping_relation') then
    create type mapping_relation as enum (
      'exact',
      'broad',
      'narrow',
      'related',
      'candidate',
      'none'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'evidence_mode') then
    create type evidence_mode as enum (
      'source_metadata',
      'documentary_source',
      'scholarly_citation',
      'authority_record',
      'visual_comparison',
      'editorial_inference',
      'system_provenance'
    );
  end if;
end
$$;

create table if not exists evidence_bundles (
  evidence_bundle_id text primary key,
  title text,
  evidence_mode evidence_mode not null,
  confidence confidence_level default 'unknown',
  review_status review_status default 'pending',
  summary text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists evidence_bundle_items (
  evidence_bundle_item_id text primary key,
  evidence_bundle_id text not null references evidence_bundles(evidence_bundle_id) on delete cascade,
  item_order int not null default 1,
  source_record_id text references source_records(source_record_id),
  citation_id text references citations(citation_id),
  authority_source_id text references authority_sources(authority_source_id),
  external_identifier_id text references external_identifiers(external_identifier_id),
  evidence_role text,
  evidence_quote text,
  evidence_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (evidence_bundle_id, item_order)
);

alter table authority_sources
  add column if not exists source_type text,
  add column if not exists jurisdiction_scope text,
  add column if not exists entity_classes_supported text,
  add column if not exists license text,
  add column if not exists api_type text,
  add column if not exists update_frequency text,
  add column if not exists coverage_note text,
  add column if not exists preferred_rank_by_entity_class jsonb default '{}'::jsonb;

alter table external_identifiers
  add column if not exists match_status authority_match_status default 'needs_resolution',
  add column if not exists match_method text,
  add column if not exists asserted_by text,
  add column if not exists reviewed_by text,
  add column if not exists reviewed_at timestamptz,
  add column if not exists evidence_bundle_id text references evidence_bundles(evidence_bundle_id),
  add column if not exists replacement_identifier_id text references external_identifiers(external_identifier_id),
  add column if not exists is_preferred_for_entity_class boolean default false,
  add column if not exists deprecated_at timestamptz,
  add column if not exists deprecation_reason text;

create table if not exists authority_resolution_events (
  authority_resolution_event_id text primary key,
  target_type text not null,
  target_id text not null,
  external_identifier_id text references external_identifiers(external_identifier_id),
  authority_source_id text references authority_sources(authority_source_id),
  authority_scheme text,
  authority_id text,
  authority_url text,
  previous_status authority_match_status,
  new_status authority_match_status not null,
  match_method text,
  confidence confidence_level default 'unknown',
  evidence_bundle_id text references evidence_bundles(evidence_bundle_id),
  proposed_by text,
  reviewed_by text,
  event_note text,
  created_at timestamptz default now()
);

create table if not exists entity_appellations (
  appellation_id text primary key,
  entity_id text not null references entities(entity_id) on delete cascade,
  label_text text not null,
  label_type appellation_type not null,
  language_code text,
  script_code text,
  romanization_system text,
  source_id text references sources(source_id),
  source_record_id text references source_records(source_record_id),
  authority_source_id text references authority_sources(authority_source_id),
  valid_from int,
  valid_to int,
  is_source_label boolean default false,
  is_preferred_for_display boolean default false,
  display_priority int default 100,
  confidence confidence_level default 'unknown',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists geography_appellations (
  geography_appellation_id text primary key,
  geo_id text not null references geographies(geo_id) on delete cascade,
  label_text text not null,
  label_type appellation_type not null,
  language_code text,
  script_code text,
  romanization_system text,
  source_id text references sources(source_id),
  authority_source_id text references authority_sources(authority_source_id),
  valid_from int,
  valid_to int,
  is_source_label boolean default false,
  is_preferred_for_display boolean default false,
  display_priority int default 100,
  confidence confidence_level default 'unknown',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table entities
  add column if not exists language_tag_bcp47 text,
  add column if not exists script_code_iso15924 text,
  add column if not exists preferred_label_language text,
  add column if not exists preferred_label_script text,
  add column if not exists local_authority_scope_note text;

alter table source_records
  add column if not exists title_original text,
  add column if not exists title_transliterated text,
  add column if not exists title_translated_en text,
  add column if not exists title_sort_key text,
  add column if not exists language_tag_bcp47 text,
  add column if not exists script_code_iso15924 text,
  add column if not exists transliteration_scheme text;

alter table geographies
  add column if not exists current_name text,
  add column if not exists historical_name text,
  add column if not exists place_type text,
  add column if not exists valid_from int,
  add column if not exists valid_to int,
  add column if not exists current_country_code text,
  add column if not exists contested_status text,
  add column if not exists tgn_id text,
  add column if not exists geonames_id text,
  add column if not exists community_protocol_note text;

alter table classifications
  add column if not exists mapping_relation mapping_relation default 'none',
  add column if not exists local_scope_note text,
  add column if not exists review_status review_status default 'pending',
  add column if not exists source_attestation text,
  add column if not exists evidence_bundle_id text references evidence_bundles(evidence_bundle_id);

alter table relation_predicates
  add column if not exists domain_class text,
  add column if not exists range_class text,
  add column if not exists requires_citation boolean default true,
  add column if not exists allows_visual_only boolean default false,
  add column if not exists ui_visibility_default text default 'visible_with_context',
  add column if not exists standard_mapping text,
  add column if not exists public_warning text;

alter table assertions
  add column if not exists evidence_mode evidence_mode,
  add column if not exists assertion_origin text,
  add column if not exists review_status review_status default 'pending',
  add column if not exists public_note text,
  add column if not exists evidence_bundle_id text references evidence_bundles(evidence_bundle_id);

alter table normalized_dates
  add column if not exists date_earliest int,
  add column if not exists date_latest int,
  add column if not exists certainty confidence_level default 'unknown',
  add column if not exists circa boolean default false,
  add column if not exists source_id text references sources(source_id);

alter table entity_geographies
  add column if not exists role text,
  add column if not exists source_label text,
  add column if not exists language_code text,
  add column if not exists script_code text,
  add column if not exists evidence_bundle_id text references evidence_bundles(evidence_bundle_id);

alter table source_record_geographies
  add column if not exists language_code text,
  add column if not exists script_code text,
  add column if not exists normalized_geo_id text references geographies(geo_id);

alter table rights_reviews
  add column if not exists protocol_notice text,
  add column if not exists tk_label text,
  add column if not exists community_access_flag boolean default false,
  add column if not exists sensitivity_flag boolean default false,
  add column if not exists deceased_name_warning boolean default false,
  add column if not exists display_zone_max image_zone_code,
  add column if not exists rights_basis text,
  add column if not exists required_statement text;

create index if not exists evidence_bundle_items_bundle_idx
  on evidence_bundle_items(evidence_bundle_id, item_order);

create index if not exists authority_resolution_events_target_idx
  on authority_resolution_events(target_type, target_id);

create index if not exists authority_resolution_events_external_identifier_idx
  on authority_resolution_events(external_identifier_id);

create index if not exists entity_appellations_entity_idx
  on entity_appellations(entity_id, display_priority);

create index if not exists entity_appellations_label_trgm_idx
  on entity_appellations using gin (label_text gin_trgm_ops);

create index if not exists geography_appellations_geo_idx
  on geography_appellations(geo_id, display_priority);

create index if not exists geography_appellations_label_trgm_idx
  on geography_appellations using gin (label_text gin_trgm_ops);
