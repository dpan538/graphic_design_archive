-- Modern Graphic Design History Archive Index
-- Ingest contract and first-target skeleton.
-- Purpose: implement the structural requirements confirmed by the 2026-05-30
-- source/access, field-mapping, and first-48 target reports before crawling.

do $$
begin
  if not exists (select 1 from pg_type where typname = 'digital_representation_type') then
    create type digital_representation_type as enum (
      'image',
      'thumbnail',
      'iiif_manifest',
      'iiif_canvas',
      'embed',
      'web_capture',
      'text_pdf',
      'audio_video',
      'structured_text',
      'none'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'target_record_status') then
    create type target_record_status as enum (
      'exact_record',
      'search_path_only',
      'needs_source_terms_review',
      'needs_manual_rights_review',
      'ready_for_manual_ingest',
      'blocked'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'fallback_stub_status') then
    create type fallback_stub_status as enum (
      'search_path_only',
      'exact_link_unconfirmed',
      'browser_recheck_required',
      'page_level_recheck_required',
      'replacement_recommended',
      'blocked_by_terms_or_access',
      'not_ingested'
    );
  end if;
end
$$;

insert into schema_versions (version_id, version_label, description, migration_file)
values
  ('schema_011', 'Ingest contract and first-target skeleton', 'Field provenance, digital representations, source-record relations, first-target registry, and validation profiles.', 'db/011_ingest_contract_targets_skeleton.sql')
on conflict (version_id) do nothing;

alter table source_terms_reviews
  add column if not exists access_mode text,
  add column if not exists api_available boolean default false,
  add column if not exists api_key_required boolean default false,
  add column if not exists automation_level text,
  add column if not exists forbidden_behavior text,
  add column if not exists default_image_zone image_zone_code default 'IMG00',
  add column if not exists evidence_urls text,
  add column if not exists terms_checked_date date;

alter table source_records
  add column if not exists raw_fields_json jsonb,
  add column if not exists original_url text,
  add column if not exists capture_url text,
  add column if not exists capture_provider text,
  add column if not exists content_hash text,
  add column if not exists null_reason text,
  add column if not exists normalization_status review_status default 'pending';

alter table citations
  add column if not exists source_type text,
  add column if not exists locator text,
  add column if not exists memento_uri text,
  add column if not exists source_language text,
  add column if not exists source_script text,
  add column if not exists citation_note text;

alter table publication_surface_pages
  add column if not exists image_zone image_zone_code default 'IMG00',
  add column if not exists has_image_frame boolean default true,
  add column if not exists image_layout_profile text;

create table if not exists source_record_relations (
  source_record_relation_id text primary key,
  subject_source_record_id text not null references source_records(source_record_id) on delete cascade,
  predicate text not null,
  object_source_record_id text references source_records(source_record_id) on delete cascade,
  object_url text,
  relation_order int,
  locator text,
  basis text not null,
  confidence confidence_level default 'unknown',
  citation_id text references citations(citation_id),
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint source_record_relations_object_check check (
    object_source_record_id is not null or object_url is not null
  )
);

create table if not exists digital_representations (
  representation_id text primary key,
  source_record_id text references source_records(source_record_id) on delete cascade,
  entity_id text references entities(entity_id),
  image_asset_id text references image_assets(image_asset_id),
  representation_type digital_representation_type not null,
  representation_url text,
  source_item_url text,
  original_url text,
  capture_url text,
  capture_datetime timestamptz,
  iiif_manifest_url text,
  iiif_canvas_id text,
  thumbnail_url text,
  embed_url text,
  mime_type text,
  width_px int,
  height_px int,
  source_rights_text text,
  source_rights_uri text,
  source_terms_review_id text references source_terms_reviews(source_terms_review_id),
  rights_review_id text references rights_reviews(rights_review_id),
  img_state image_zone_code default 'IMG00',
  display_permitted boolean default false,
  local_copy_permitted boolean default false,
  required_credit text,
  review_status review_status default 'pending',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint digital_representations_target_check check (
    source_record_id is not null or entity_id is not null
  )
);

create table if not exists field_provenance (
  field_provenance_id text primary key,
  target_table text not null,
  target_id text not null,
  target_path text not null,
  source_record_id text references source_records(source_record_id),
  source_field_path text,
  source_literal text,
  normalized_value text,
  assertion_basis text not null,
  evidence_bundle_id text references evidence_bundles(evidence_bundle_id),
  citation_id text references citations(citation_id),
  confidence confidence_level default 'unknown',
  review_status review_status default 'pending',
  reviewed_by text,
  reviewed_at timestamptz,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists record_family_profiles (
  record_family text primary key,
  family_label text not null,
  required_source_fields text,
  required_normalized_fields text,
  required_rights_fields text,
  required_classification_fields text,
  required_relation_fields text,
  required_citation_fields text,
  default_surface_type publication_surface_type default 'card',
  default_image_zone image_zone_code default 'IMG00',
  missing_data_strategy text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists ingest_validation_rules (
  validation_rule_id text primary key,
  validation_target text not null,
  required_fields text not null,
  blocking_failure text not null,
  warning_only text,
  suggested_workflow_status workflow_status default 'draft',
  applies_to_record_family text references record_family_profiles(record_family),
  applies_to_image_zone image_zone_code,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists first_ingest_record_targets (
  first_target_id text primary key,
  target_number int not null unique,
  scope_cell_id text not null,
  target_label text not null,
  source_name text not null,
  source_url_or_search_path text not null,
  record_family text,
  region text,
  date_text text,
  creator_or_institution text,
  why_selected text,
  expected_image_zone image_zone_code default 'IMG00',
  rights_risk text,
  target_status target_record_status default 'needs_manual_rights_review',
  manual_rights_review_required boolean default true,
  source_terms_review_required boolean default false,
  required_citation text,
  fallback_target text,
  ingest_order int,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists first_ingest_target_verifications (
  verification_id text primary key,
  first_target_id text not null references first_ingest_record_targets(first_target_id) on delete cascade,
  verification_decision text not null,
  verified_at date not null,
  verified_by text,
  confirmed_image_zone image_zone_code default 'IMG00',
  canonical_url text,
  replacement_url text,
  evidence_summary text,
  required_action text,
  blocking_reason text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists fallback_source_stubs (
  fallback_stub_id text primary key,
  first_target_id text references first_ingest_record_targets(first_target_id) on delete set null,
  scope_cell_id text,
  target_label text not null,
  source_name text,
  source_url_or_search_path text,
  canonical_url text,
  replacement_url text,
  fallback_status fallback_stub_status not null default 'not_ingested',
  public_stub_policy text not null default 'show_link_only_stub',
  expected_image_zone image_zone_code default 'IMG00',
  display_area_policy text not null default 'preserve_area_with_empty_frame',
  not_ingested_reason text not null,
  user_action_label text not null default 'View at source',
  user_action_url text,
  verification_decision text,
  verified_at date,
  verified_by text,
  evidence_summary text,
  required_action text,
  blocking_reason text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists source_record_relations_subject_idx
  on source_record_relations(subject_source_record_id, predicate, relation_order);

create index if not exists source_record_relations_object_idx
  on source_record_relations(object_source_record_id);

create index if not exists digital_representations_record_idx
  on digital_representations(source_record_id, representation_type, img_state);

create index if not exists field_provenance_target_idx
  on field_provenance(target_table, target_id, target_path);

create index if not exists field_provenance_source_idx
  on field_provenance(source_record_id);

create index if not exists first_ingest_record_targets_cell_idx
  on first_ingest_record_targets(scope_cell_id, target_number);

create index if not exists first_ingest_record_targets_status_idx
  on first_ingest_record_targets(target_status, expected_image_zone);

create index if not exists first_ingest_target_verifications_target_idx
  on first_ingest_target_verifications(first_target_id, verification_decision, confirmed_image_zone);

create index if not exists fallback_source_stubs_scope_idx
  on fallback_source_stubs(scope_cell_id, fallback_status, expected_image_zone);

create index if not exists fallback_source_stubs_target_idx
  on fallback_source_stubs(first_target_id);
