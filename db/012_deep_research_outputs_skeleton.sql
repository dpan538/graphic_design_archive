-- Modern Graphic Design History Archive Index
-- Deep Research output skeleton.
-- Purpose: preserve report-derived candidates, remediation recommendations,
-- and source expansion findings as reviewable data before promotion.

insert into schema_versions (version_id, version_label, description, migration_file)
values
  ('schema_012', 'Deep Research output layer', 'Report-derived redundancy candidates, fallback remediation recommendations, source expansion candidates, and production/fragile source shortlists.', 'db/012_deep_research_outputs_skeleton.sql')
on conflict (version_id) do nothing;

create table if not exists source_redundancy_candidates (
  redundancy_candidate_id text primary key,
  scope_cell_id text not null,
  candidate_label text not null,
  candidate_class text,
  creator_or_institution text,
  date_text text,
  source_name text,
  url_or_search_path text,
  record_family text,
  expected_image_zone image_zone_code default 'IMG00',
  rights_risk text,
  automation_feasibility text,
  replace_failed_target text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists source_redundancy_triage (
  triage_id text primary key,
  probable_failed_target text not null,
  likely_failure_mode text,
  recommended_action text,
  best_replacement_or_next_move text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists recommended_six_target_ingest_sets (
  recommended_set_id text primary key,
  scope_cell_id text not null,
  recommended_six_target_ingest_set text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists fallback_remediation_recommendations (
  remediation_id text primary key,
  failed_target_or_cell text not null,
  original_target_label text,
  original_source text,
  failure_type text,
  confirmed_exact_url text,
  replacement_url text,
  source_title text,
  creator_or_institution text,
  date_text text,
  record_family text,
  rights_note text,
  recommended_image_zone image_zone_code default 'IMG00',
  recommended_status text,
  reason text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists fallback_remediation_projection (
  projection_id text primary key,
  fallback_stub_id text references fallback_source_stubs(fallback_stub_id) on delete set null,
  first_target_id text references first_ingest_record_targets(first_target_id) on delete set null,
  scope_cell_id text,
  target_label text,
  current_fallback_status text,
  current_user_action_url text,
  remediation_recommended_status text,
  projected_status text,
  projected_url text,
  projected_image_zone image_zone_code default 'IMG00',
  source_title text,
  rights_note text,
  rationale text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists global_source_expansion_candidates (
  source_expansion_id text primary key,
  source_name text not null,
  region text,
  source_type text,
  url text,
  access_method text,
  api_iiif_oai_data text,
  likely_record_types text,
  graphic_design_relevance text,
  rights_clarity text,
  stable_identifier_quality text,
  automation_feasibility text,
  default_image_zone image_zone_code default 'IMG00',
  recommended_use text,
  evidence text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists first_production_low_friction_sources (
  low_friction_id text primary key,
  source_name text not null,
  why_production_ingest text,
  evidence text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists high_value_fragile_sources (
  fragile_source_id text primary key,
  source_name text not null,
  why_valuable text,
  why_fragile text,
  recommended_treatment text,
  evidence text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists remediation_source_verifications (
  remediation_verification_id text primary key,
  projection_ids text,
  affected_first_target_ids text,
  scope_cell_id text,
  verification_decision text not null,
  verified_url text,
  source_name text,
  source_title text,
  record_family text,
  date_text text,
  confirmed_image_zone image_zone_code default 'IMG00',
  promotion_action text,
  rights_summary text,
  evidence_summary text,
  remaining_blocker text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists source_redundancy_candidates_scope_idx
  on source_redundancy_candidates(scope_cell_id, candidate_class, expected_image_zone);

create index if not exists fallback_remediation_recommendations_cell_idx
  on fallback_remediation_recommendations(failed_target_or_cell, recommended_status);

create index if not exists fallback_remediation_projection_status_idx
  on fallback_remediation_projection(projected_status, scope_cell_id);

create index if not exists global_source_expansion_candidates_use_idx
  on global_source_expansion_candidates(recommended_use, region, default_image_zone);

create index if not exists remediation_source_verifications_scope_idx
  on remediation_source_verifications(scope_cell_id, verification_decision, confirmed_image_zone);
