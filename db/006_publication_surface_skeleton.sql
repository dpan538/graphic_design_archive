-- Modern Graphic Design History Archive Index
-- Publication surface and archive-cabinet design-system skeleton.
-- Purpose: normalize the public "paper" layer without changing source data.

do $$
begin
  if not exists (select 1 from pg_type where typname = 'publication_surface_type') then
    create type publication_surface_type as enum (
      'sheet',
      'card',
      'fallback_stub',
      'folder_cover',
      'registration_card',
      'bookmark',
      'index_appendix',
      'excerpt_strip'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'sheet_tier') then
    create type sheet_tier as enum ('S', 'M', 'L', 'XL', 'XXL');
  end if;

  if not exists (select 1 from pg_type where typname = 'image_zone_code') then
    create type image_zone_code as enum ('IMG00', 'IMG01', 'IMG02', 'IMG03', 'IMG04');
  end if;

  if not exists (select 1 from pg_type where typname = 'surface_table_kind') then
    create type surface_table_kind as enum (
      'SOURCE',
      'NORMALIZED',
      'RIGHTS',
      'CLASSIFICATION',
      'RELATIONS',
      'CITATIONS'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'folder_view_type') then
    create type folder_view_type as enum (
      'region',
      'theme',
      'medium',
      'movement'
    );
  end if;
end
$$;

create table if not exists display_templates (
  template_id text primary key,
  component_type publication_surface_type not null,
  tier sheet_tier,
  layout_id text not null,
  grid_unit text,
  table_kinds surface_table_kind[] default array[]::surface_table_kind[],
  allowed_image_zones image_zone_code[] default array[]::image_zone_code[],
  decorative_whitelist text,
  status review_status default 'pending',
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (component_type, tier, layout_id)
);

create table if not exists publication_surfaces (
  publication_surface_id text primary key,
  seq_int int unique,
  seq_label text unique,
  surface_type publication_surface_type not null default 'sheet',
  target_type text not null,
  target_id text not null,
  entity_id text references entities(entity_id),
  source_record_id text references source_records(source_record_id),
  primary_historical_node_id text references historical_nodes(node_id),
  primary_movement_id text references movements(movement_id),
  primary_regional_movement_id text references regional_movements(regional_movement_id),
  era_text text not null default 'undated',
  movement_display text not null default 'NONE',
  tier sheet_tier not null default 'S',
  layout_id text not null default 'S-001',
  image_zone image_zone_code not null default 'IMG00',
  display_number text unique,
  display_profile jsonb default '{}'::jsonb,
  workflow_status workflow_status default 'draft',
  last_verified_at timestamptz,
  published_at timestamptz,
  deprecated_at timestamptz,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint publication_surfaces_seq_for_sheet_check check (
    surface_type <> 'sheet' or seq_int is not null
  ),
  constraint publication_surfaces_target_check check (target_type <> '' and target_id <> '')
);

create table if not exists publication_surface_pages (
  publication_page_id text primary key,
  publication_surface_id text not null references publication_surfaces(publication_surface_id) on delete cascade,
  page_number int not null default 1,
  page_label text not null default 'p01',
  tier sheet_tier not null,
  layout_id text not null,
  template_id text references display_templates(template_id),
  display_number text unique,
  is_primary_page boolean default false,
  overflow_from_table surface_table_kind,
  page_profile jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (publication_surface_id, page_number)
);

create table if not exists surface_table_rows (
  surface_table_row_id text primary key,
  publication_page_id text not null references publication_surface_pages(publication_page_id) on delete cascade,
  table_kind surface_table_kind not null,
  row_order int not null,
  source_record_id text references source_records(source_record_id),
  citation_id text references citations(citation_id),
  assertion_id text references assertions(assertion_id),
  classification_id text references classifications(classification_id),
  rights_review_id text references rights_reviews(rights_review_id),
  field_key text,
  source_label text,
  source_value text,
  normalized_label text,
  normalized_value text,
  confidence confidence_level default 'unknown',
  warning_code text,
  display_json jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (publication_page_id, table_kind, row_order)
);

create table if not exists folder_views (
  folder_view_id text primary key,
  folder_type folder_view_type not null,
  folder_value text not null,
  title text not null,
  subtitle text,
  nameplate_text text,
  tab_text text,
  primary_historical_node_id text references historical_nodes(node_id),
  movement_id text references movements(movement_id),
  regional_movement_id text references regional_movements(regional_movement_id),
  medium_id text references media_technologies(media_id),
  region_id text references regions(region_id),
  geo_id text references geographies(geo_id),
  source_id text references sources(source_id),
  sort_rule text default 'seq_int',
  coverage_note text,
  rights_overview text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (folder_type, folder_value)
);

create table if not exists folder_memberships (
  folder_membership_id text primary key,
  folder_view_id text not null references folder_views(folder_view_id) on delete cascade,
  publication_surface_id text not null references publication_surfaces(publication_surface_id) on delete cascade,
  membership_basis text not null,
  classification_id text references classifications(classification_id),
  confidence confidence_level default 'unknown',
  sort_seq int,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (folder_view_id, publication_surface_id)
);

create table if not exists filing_registry_cards (
  registry_card_id text primary key,
  classification_type text not null,
  classification_value text not null,
  folder_view_id text references folder_views(folder_view_id),
  classified_at timestamptz default now(),
  modified_at timestamptz default now(),
  registrar text,
  registry_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists filing_registry_members (
  registry_member_id text primary key,
  registry_card_id text not null references filing_registry_cards(registry_card_id) on delete cascade,
  publication_surface_id text not null references publication_surfaces(publication_surface_id) on delete cascade,
  seq_int int,
  display_number text,
  historical_node_id text references historical_nodes(node_id),
  movement_display text not null default 'NONE',
  member_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (registry_card_id, publication_surface_id)
);

create table if not exists sparse_cards (
  sparse_card_id text primary key,
  card_type text not null,
  title text not null,
  target_type text,
  target_id text,
  parent_publication_surface_id text references publication_surfaces(publication_surface_id),
  parent_sparse_card_id text references sparse_cards(sparse_card_id),
  promotion_status review_status default 'pending',
  promotion_checklist_json jsonb default '{}'::jsonb,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint sparse_cards_parent_check check (
    parent_publication_surface_id is not null or parent_sparse_card_id is not null
  )
);

create table if not exists archive_bookmarks (
  bookmark_id text primary key,
  title text not null,
  bookmark_type text not null,
  target_type text,
  target_id text,
  folder_view_id text references folder_views(folder_view_id),
  stable_slug text unique,
  body_md text,
  status review_status default 'pending',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists publication_surfaces_seq_idx
  on publication_surfaces(seq_int);

create index if not exists publication_surfaces_target_idx
  on publication_surfaces(target_type, target_id);

create index if not exists publication_surfaces_classification_idx
  on publication_surfaces(primary_historical_node_id, primary_movement_id, primary_regional_movement_id);

create index if not exists publication_surface_pages_surface_idx
  on publication_surface_pages(publication_surface_id, page_number);

create index if not exists surface_table_rows_page_kind_idx
  on surface_table_rows(publication_page_id, table_kind, row_order);

create index if not exists folder_views_type_value_idx
  on folder_views(folder_type, folder_value);

create index if not exists folder_memberships_folder_idx
  on folder_memberships(folder_view_id, sort_seq);

create index if not exists folder_memberships_surface_idx
  on folder_memberships(publication_surface_id);

create index if not exists filing_registry_members_card_idx
  on filing_registry_members(registry_card_id);

create index if not exists sparse_cards_parent_surface_idx
  on sparse_cards(parent_publication_surface_id);
