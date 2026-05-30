-- Modern Graphic Design History Archive Index
-- Regional and historical coverage skeleton.
-- Purpose: make broad geographic coverage a database requirement, not an afterthought.

create table if not exists regions (
  region_id text primary key,
  region_name text not null,
  parent_region_id text references regions(region_id),
  region_type text not null,
  priority text,
  coverage_reason text,
  known_bias_risk text,
  language_scope text,
  script_scope text,
  source_strategy text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists coverage_matrix (
  coverage_id text primary key,
  node_id text not null references historical_nodes(node_id),
  region_id text not null references regions(region_id),
  coverage_status text not null,
  priority text,
  known_entry_points text,
  source_needs text,
  rights_risk text,
  research_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (node_id, region_id)
);

create table if not exists regional_source_priorities (
  priority_id text primary key,
  region_id text not null references regions(region_id),
  source_need_type text not null,
  priority text,
  examples_to_research text,
  reason text,
  status text default 'needs_research',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists historical_events (
  event_id text primary key,
  event_name text not null,
  event_type text not null,
  date_start int,
  date_end int,
  date_text text,
  region_id text references regions(region_id),
  place_text text,
  related_node_id text references historical_nodes(node_id),
  source_record_id text references source_records(source_record_id),
  citation_id text references citations(citation_id),
  confidence confidence_level default 'unknown',
  review_status review_status default 'pending',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists coverage_gap_notes (
  gap_id text primary key,
  region_id text references regions(region_id),
  node_id text references historical_nodes(node_id),
  gap_type text not null,
  gap_description text not null,
  priority text,
  proposed_research_action text,
  status text default 'open',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists coverage_matrix_region_idx
  on coverage_matrix(region_id);

create index if not exists coverage_matrix_node_idx
  on coverage_matrix(node_id);

create index if not exists regional_source_priorities_region_idx
  on regional_source_priorities(region_id);

create index if not exists historical_events_region_node_idx
  on historical_events(region_id, related_node_id);

create index if not exists coverage_gap_notes_region_node_idx
  on coverage_gap_notes(region_id, node_id);
