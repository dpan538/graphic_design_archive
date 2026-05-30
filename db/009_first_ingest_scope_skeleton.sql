-- Modern Graphic Design History Archive Index
-- First experimental ingest scope skeleton.
-- Purpose: make the first controlled ingest scope explicit before crawling.

alter table regional_movements
  add column if not exists movement_mode text,
  add column if not exists script_flags text,
  add column if not exists collective_authorship text,
  add column if not exists periodical_relevance text,
  add column if not exists protocol_sensitive boolean default false,
  add column if not exists source_priority_class text;

alter table regional_event_nodes
  add column if not exists event_date_start int,
  add column if not exists event_date_end int,
  add column if not exists date_precision text,
  add column if not exists anchor_strength text,
  add column if not exists source_record_required boolean default false,
  add column if not exists browse_priority text,
  add column if not exists web_archive_relevant boolean default false;

alter table sources
  add column if not exists automation_status text,
  add column if not exists rights_basis text,
  add column if not exists record_level_rights_required boolean default true,
  add column if not exists preview_allowed text,
  add column if not exists thumbnail_allowed text,
  add column if not exists iiif_capable text,
  add column if not exists api_key_required boolean default false,
  add column if not exists protocol_sensitive boolean default false;

alter table search_vocabulary
  add column if not exists query_profile_id text,
  add column if not exists script text,
  add column if not exists term_type text,
  add column if not exists preferred text,
  add column if not exists transliteration_of text,
  add column if not exists false_positive_note text;

alter table experimental_ingest_candidates
  add column if not exists scope_cell_id text,
  add column if not exists scope_role text,
  add column if not exists primary_region text,
  add column if not exists secondary_region text,
  add column if not exists hn_ids text,
  add column if not exists movement_ids text,
  add column if not exists event_ids text,
  add column if not exists source_family_id text,
  add column if not exists record_family text,
  add column if not exists default_image_zone image_zone_code default 'IMG00',
  add column if not exists rights_review_level text,
  add column if not exists protocol_sensitive boolean default false,
  add column if not exists manual_review_required boolean default true,
  add column if not exists query_profile_id text,
  add column if not exists target_record_count int,
  add column if not exists required_fields text,
  add column if not exists expected_surface_type text;

alter table source_records
  add column if not exists parent_record_id text references source_records(source_record_id),
  add column if not exists source_language text,
  add column if not exists source_script text,
  add column if not exists title_translated text,
  add column if not exists capture_datetime timestamptz,
  add column if not exists issue_identifier text,
  add column if not exists page_number text,
  add column if not exists record_family text,
  add column if not exists protocol_sensitive boolean default false,
  add column if not exists icip_flag boolean default false;

alter table rights_reviews
  add column if not exists rights_evidence_url text,
  add column if not exists rights_evidence_note text,
  add column if not exists image_zone image_zone_code default 'IMG00';

alter table classifications
  add column if not exists movement_assignment_mode text,
  add column if not exists authority_confidence confidence_level default 'unknown',
  add column if not exists relation_confidence confidence_level default 'unknown',
  add column if not exists protocol_sensitive boolean default false;

create index if not exists experimental_ingest_candidates_scope_idx
  on experimental_ingest_candidates(scope_role, scope_cell_id);

create index if not exists source_records_parent_idx
  on source_records(parent_record_id);

create index if not exists source_records_issue_page_idx
  on source_records(issue_identifier, page_number);
