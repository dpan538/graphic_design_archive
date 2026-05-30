-- Modern Graphic Design History Archive Index
-- Global classification skeleton.
-- Purpose: make geography, date, regional movement, and event-node coverage
-- structural before frontend/design-system work begins.

create table if not exists classification_axes (
  axis_id text primary key,
  axis_name text not null unique,
  axis_type text not null,
  required_for_launch text,
  required_for_record text,
  supports_multiple text,
  api_filter text,
  controlled_source text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists geographies (
  geo_id text primary key,
  name text not null,
  parent_geo_id text references geographies(geo_id),
  region_id text references regions(region_id),
  geo_type text not null,
  iso_code text,
  language_scope text,
  script_scope text,
  date_scope text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists geography_aliases (
  alias_id text primary key,
  geo_id text not null references geographies(geo_id),
  alias text not null,
  language text default 'und',
  script text,
  transliteration_scheme text,
  preferred_for_search boolean default true,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists regional_movements (
  regional_movement_id text primary key,
  name text not null,
  alternate_names text,
  region_id text not null references regions(region_id),
  geo_id text references geographies(geo_id),
  date_start int,
  date_end int,
  date_text text,
  formation_type text,
  related_node_ids text,
  related_movement_ids text,
  key_media text,
  source_needs text,
  rights_risk text,
  status text default 'launch_scope',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists regional_event_nodes (
  event_node_id text primary key,
  event_name text not null,
  event_type text not null,
  region_id text not null references regions(region_id),
  geo_id text references geographies(geo_id),
  date_start int,
  date_end int,
  date_text text,
  related_node_ids text,
  related_regional_movement_ids text,
  source_need text,
  rights_risk text,
  status text default 'launch_scope',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists normalized_dates (
  normalized_date_id text primary key,
  target_table text not null,
  target_id text not null,
  date_start int,
  date_end int,
  date_text text not null,
  date_precision text,
  date_basis text not null,
  calendar_system text default 'gregorian',
  source_record_id text references source_records(source_record_id),
  citation_id text references citations(citation_id),
  confidence confidence_level default 'unknown',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists entity_geographies (
  entity_geography_id text primary key,
  entity_id text not null references entities(entity_id),
  geo_id text not null references geographies(geo_id),
  relation_type text not null,
  source_record_id text references source_records(source_record_id),
  citation_id text references citations(citation_id),
  confidence confidence_level default 'unknown',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists source_record_geographies (
  source_record_geography_id text primary key,
  source_record_id text not null references source_records(source_record_id),
  geo_id text not null references geographies(geo_id),
  relation_type text not null,
  source_text text,
  confidence confidence_level default 'unknown',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists geographies_parent_idx
  on geographies(parent_geo_id);

create index if not exists geographies_region_idx
  on geographies(region_id);

create index if not exists regional_movements_region_geo_idx
  on regional_movements(region_id, geo_id);

create index if not exists regional_event_nodes_region_geo_idx
  on regional_event_nodes(region_id, geo_id);

create index if not exists normalized_dates_target_idx
  on normalized_dates(target_table, target_id);

create index if not exists entity_geographies_entity_idx
  on entity_geographies(entity_id);

create index if not exists entity_geographies_geo_idx
  on entity_geographies(geo_id);

create index if not exists source_record_geographies_record_idx
  on source_record_geographies(source_record_id);

create index if not exists source_record_geographies_geo_idx
  on source_record_geographies(geo_id);
