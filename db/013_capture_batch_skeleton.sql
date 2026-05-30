create table if not exists capture_batch_records (
  capture_id text primary key,
  direction_id text not null,
  direction_name text not null,
  source_id text references sources(source_id),
  source_name text not null,
  source_api_url text not null,
  capture_status text not null,
  source_identifier text,
  source_record_url text,
  source_title text not null,
  source_creator text,
  source_date_text text,
  date_start integer,
  date_end integer,
  source_place_text text,
  source_object_type text,
  source_medium text,
  source_collection text,
  source_rights_text text,
  rights_uri text,
  rights_basis text,
  image_presence_code image_zone_code default 'IMG00',
  image_presence_basis text,
  image_state_evaluation text,
  image_state_confidence text,
  rights_review_required boolean default true,
  image_state_review_note text,
  image_frame_behavior text,
  image_url_detected text,
  local_copy_permitted boolean default false,
  iiif_or_viewer_available text,
  fallback_required boolean default false,
  fallback_reason text,
  raw_json_path text,
  access_date date not null
);

create index if not exists capture_batch_records_source_idx
  on capture_batch_records(source_id, image_presence_code, capture_status);

create index if not exists capture_batch_records_direction_idx
  on capture_batch_records(direction_id, source_id);

create table if not exists capture_batch_cell_assignments (
  capture_id text primary key references capture_batch_records(capture_id),
  source_id text,
  source_name text,
  source_title text,
  image_presence_code image_zone_code default 'IMG00',
  assigned_cell_id text not null,
  assigned_cell_name text not null,
  assignment_type text not null,
  assignment_confidence text,
  assignment_basis text,
  matched_terms text,
  recommended_next_step text
);

create index if not exists capture_batch_cell_assignments_cell_idx
  on capture_batch_cell_assignments(assigned_cell_id, assignment_type, image_presence_code);

create table if not exists capture_batch_cell_summary (
  cell_id text primary key,
  cell_name text not null,
  cell_type text not null,
  assigned_count integer default 0,
  img00_count integer default 0,
  img01_count integer default 0,
  img02_count integer default 0,
  img03_count integer default 0,
  img04_count integer default 0,
  source_names text,
  sample_capture_ids text,
  cell_status text,
  next_generation_action text
);

create table if not exists capture_batch_next_generation_queue (
  queue_id text primary key,
  cell_id text not null,
  cell_name text not null,
  cell_type text not null,
  priority text,
  reason text,
  recommended_query text,
  recommended_sources text,
  required_img_states text,
  minimum_next_capture_count integer default 0
);
