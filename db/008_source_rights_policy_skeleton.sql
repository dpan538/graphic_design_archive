-- Modern Graphic Design History Archive Index
-- Source and rights policy skeleton.
-- Purpose: prevent accidental escalation from metadata indexing to image reuse
-- before experimental ingest begins.

do $$
begin
  if not exists (select 1 from pg_type where typname = 'source_record_policy') then
    create type source_record_policy as enum (
      'metadata_only',
      'metadata_plus_thumbnail',
      'iiif_embed_only',
      'open_image_allowed',
      'link_only',
      'manual_review_required',
      'do_not_ingest'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'public_display_policy') then
    create type public_display_policy as enum (
      'source_link_only',
      'metadata_only',
      'thumbnail_with_attribution',
      'iiif_embed_with_credit',
      'open_image_with_license',
      'blocked'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'asset_origin') then
    create type asset_origin as enum (
      'remote',
      'cached_thumbnail',
      'licensed_local',
      'derivative_generated',
      'none'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'terms_review_decision') then
    create type terms_review_decision as enum (
      'approved_metadata_only',
      'approved_thumbnail_only',
      'approved_iiif_embed_only',
      'approved_open_image',
      'link_only',
      'manual_review_required',
      'blocked'
    );
  end if;
end
$$;

alter table sources
  add column if not exists home_url text,
  add column if not exists country text,
  add column if not exists coverage_scope text,
  add column if not exists api_base text,
  add column if not exists iiif_base text,
  add column if not exists oai_base text,
  add column if not exists stable_identifier_pattern text,
  add column if not exists default_record_policy source_record_policy default 'manual_review_required',
  add column if not exists default_display_policy public_display_policy default 'source_link_only',
  add column if not exists default_image_zone image_zone_code default 'IMG00',
  add column if not exists metadata_license text,
  add column if not exists image_license_model text,
  add column if not exists terms_url text,
  add column if not exists api_terms_url text,
  add column if not exists robots_url text,
  add column if not exists rate_limit text,
  add column if not exists requires_api_key boolean default false,
  add column if not exists supports_non_latin boolean default false,
  add column if not exists supports_rights_uri boolean default false,
  add column if not exists supports_item_level_rights boolean default false,
  add column if not exists supports_thumbnail_rights boolean default false,
  add column if not exists cultural_protocol_risk boolean default false,
  add column if not exists privacy_risk boolean default false,
  add column if not exists last_terms_reviewed_at timestamptz,
  add column if not exists terms_review_status review_status default 'pending',
  add column if not exists policy_notes text;

alter table source_terms_reviews
  add column if not exists terms_snapshot_url text,
  add column if not exists api_terms_snapshot_url text,
  add column if not exists robots_snapshot text,
  add column if not exists key_clauses text,
  add column if not exists image_reuse_summary text,
  add column if not exists thumbnail_reuse_summary text,
  add column if not exists iiif_summary text,
  add column if not exists prohibited_uses text,
  add column if not exists rate_limit_summary text,
  add column if not exists commercial_use_summary text,
  add column if not exists takedown_contact text,
  add column if not exists decision terms_review_decision default 'manual_review_required',
  add column if not exists supersedes_review_id text references source_terms_reviews(source_terms_review_id);

alter table rights_reviews
  add column if not exists rights_basis_type text,
  add column if not exists rights_text text,
  add column if not exists evidence_url text,
  add column if not exists evidence_date date,
  add column if not exists attribution_text text,
  add column if not exists display_ok_thumbnail boolean default false,
  add column if not exists display_ok_embed boolean default false,
  add column if not exists display_ok_open boolean default false,
  add column if not exists copy_ok_local boolean default false,
  add column if not exists expiry_or_recheck_date date,
  add column if not exists requires_manual_review boolean default true,
  add column if not exists normalized_image_zone image_zone_code default 'IMG00',
  add column if not exists normalized_display_policy public_display_policy default 'source_link_only';

alter table image_assets
  add column if not exists asset_origin asset_origin default 'none',
  add column if not exists asset_rights_status rights_state default 'unknown',
  add column if not exists license_uri text,
  add column if not exists source_item_url text,
  add column if not exists iiif_info_json_url text,
  add column if not exists manifest_url text,
  add column if not exists thumbnail_policy text,
  add column if not exists attribution_required boolean default true,
  add column if not exists checksum_sha256 text,
  add column if not exists original_mime_type text,
  add column if not exists suppression_flag boolean default false,
  add column if not exists no_local_copy_reason text;

alter table ingestion_runs
  add column if not exists harvest_scope text,
  add column if not exists api_version text,
  add column if not exists query_or_set text,
  add column if not exists records_blocked_rights int default 0,
  add column if not exists records_blocked_terms int default 0,
  add column if not exists records_needing_review int default 0,
  add column if not exists thumbnail_downloaded_count int default 0,
  add column if not exists iiif_manifest_stored_count int default 0,
  add column if not exists policy_snapshot_id text references source_terms_reviews(source_terms_review_id);

create table if not exists experimental_ingest_candidates (
  experimental_candidate_id text primary key,
  candidate_name text not null,
  source_id text references sources(source_id),
  source_name text not null,
  region text,
  record_type text,
  test_purpose text not null,
  expected_rights_state text,
  expected_image_zone image_zone_code default 'IMG00',
  expected_record_policy source_record_policy default 'manual_review_required',
  expected_display_policy public_display_policy default 'source_link_only',
  likely_fields text,
  risks text,
  shortlist_status review_status default 'pending',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists sources_policy_idx
  on sources(default_record_policy, default_display_policy, default_image_zone);

create index if not exists source_terms_reviews_decision_idx
  on source_terms_reviews(source_id, decision, reviewed_at);

create index if not exists rights_reviews_zone_idx
  on rights_reviews(source_record_id, normalized_image_zone, normalized_display_policy);

create index if not exists image_assets_origin_idx
  on image_assets(asset_origin, asset_rights_status);

create index if not exists experimental_ingest_candidates_status_idx
  on experimental_ingest_candidates(shortlist_status, expected_image_zone);
