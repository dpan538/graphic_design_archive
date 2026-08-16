\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Phase 2C-S is deliberately additive.  The v3 tables are a distinct,
-- release-owned read model; historical 001--009 structures and their
-- piecemeal builders remain intact for auditability but are not a v3 path.

CREATE TABLE research.folder_type_registry (
  folder_type_code text PRIMARY KEY
    CHECK (folder_type_code ~ '^[a-z][a-z0-9_]*$'),
  type_label text NOT NULL CHECK (btrim(type_label) <> ''),
  type_sort_ordinal integer NOT NULL CHECK (type_sort_ordinal >= 0),
  UNIQUE (type_sort_ordinal)
);

CREATE TABLE research.folder_publication_metadata (
  folder_id uuid PRIMARY KEY
    REFERENCES research.folder(folder_id) ON DELETE RESTRICT,
  folder_type_code text NOT NULL
    REFERENCES research.folder_type_registry(folder_type_code) ON DELETE RESTRICT,
  slug text NOT NULL CHECK (
    slug = lower(slug) AND slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'
  ),
  scope_note text NOT NULL CHECK (btrim(scope_note) <> ''),
  folder_sort_ordinal integer NOT NULL CHECK (folder_sort_ordinal >= 0),
  UNIQUE (folder_type_code, slug),
  UNIQUE (folder_type_code, folder_sort_ordinal)
);

-- These hashes are working-policy identity, not caller-provided assertions.
-- A builder receives this immutable policy row by id and copies its values.
CREATE TABLE research.launch_snapshot_policy_v3 (
  launch_snapshot_policy_id uuid PRIMARY KEY,
  policy_token core.release_token NOT NULL UNIQUE,
  public_corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  projection_query_pack_sha256 core.sha256_hex NOT NULL,
  selection_policy_sha256 core.sha256_hex NOT NULL,
  registry_corpus_policy_sha256 core.sha256_hex NOT NULL,
  created_at timestamptz NOT NULL
);

-- Only an explicit working allowlist can turn a source asset into a public
-- citation.  Builders never expose raw locators, raw records, or ad-hoc text.
CREATE TABLE research.public_source_citation_allowlist_v3 (
  source_asset_id uuid PRIMARY KEY
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  citation_label text NOT NULL CHECK (btrim(citation_label) <> ''),
  created_at timestamptz NOT NULL
);

CREATE TABLE release.research_folder_type_projection_v3 (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  folder_type_code text NOT NULL,
  type_label text NOT NULL CHECK (btrim(type_label) <> ''),
  sort_ordinal integer NOT NULL CHECK (sort_ordinal >= 0),
  PRIMARY KEY (research_release_id, folder_type_code),
  UNIQUE (research_release_id, sort_ordinal)
);

CREATE TABLE release.research_folder_projection_v3 (
  research_release_id uuid NOT NULL,
  folder_id uuid NOT NULL,
  folder_token core.release_token NOT NULL,
  folder_type_code text NOT NULL,
  slug text NOT NULL CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  label text NOT NULL CHECK (btrim(label) <> ''),
  scope_note text NOT NULL CHECK (btrim(scope_note) <> ''),
  sort_ordinal integer NOT NULL CHECK (sort_ordinal >= 0),
  PRIMARY KEY (research_release_id, folder_id),
  UNIQUE (research_release_id, folder_type_code, slug),
  UNIQUE (research_release_id, folder_type_code, sort_ordinal, folder_id),
  FOREIGN KEY (research_release_id, folder_type_code)
    REFERENCES release.research_folder_type_projection_v3
      (research_release_id, folder_type_code) ON DELETE RESTRICT
);

CREATE TABLE release.research_surface_presentation_projection_v3 (
  research_release_id uuid NOT NULL,
  archive_object_id uuid NOT NULL,
  public_surface_id text NOT NULL CHECK (btrim(public_surface_id) <> ''),
  title text,
  title_missingness text NOT NULL CHECK (title_missingness IN ('present','missing')),
  display_date text,
  display_date_missingness text NOT NULL CHECK (display_date_missingness IN ('present','missing')),
  normalized_year integer,
  normalized_year_missingness text NOT NULL CHECK (normalized_year_missingness IN ('present','missing')),
  place_label text,
  place_missingness text NOT NULL CHECK (place_missingness IN ('present','missing')),
  medium_label text,
  medium_missingness text NOT NULL CHECK (medium_missingness IN ('present','missing')),
  type_label text,
  type_missingness text NOT NULL CHECK (type_missingness IN ('present','missing')),
  source_label text NOT NULL CHECK (btrim(source_label) <> ''),
  description text,
  description_missingness text NOT NULL CHECK (description_missingness IN ('present','missing')),
  public_citation_label text NOT NULL CHECK (btrim(public_citation_label) <> ''),
  public_source_route text NOT NULL CHECK (public_source_route ~ '^/sources/[0-9a-f]{64}$'),
  publication_layer release.publication_layer NOT NULL,
  PRIMARY KEY (research_release_id, archive_object_id),
  UNIQUE (research_release_id, public_surface_id),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_release_object
      (research_release_id, archive_object_id) ON DELETE RESTRICT,
  CHECK ((title IS NULL) = (title_missingness = 'missing')),
  CHECK ((display_date IS NULL) = (display_date_missingness = 'missing')),
  CHECK ((normalized_year IS NULL) = (normalized_year_missingness = 'missing')),
  CHECK ((place_label IS NULL) = (place_missingness = 'missing')),
  CHECK ((medium_label IS NULL) = (medium_missingness = 'missing')),
  CHECK ((type_label IS NULL) = (type_missingness = 'missing')),
  CHECK ((description IS NULL) = (description_missingness = 'missing'))
);

CREATE TABLE release.research_surface_credit_projection_v3 (
  research_release_id uuid NOT NULL,
  archive_object_id uuid NOT NULL,
  credit_ordinal integer NOT NULL CHECK (credit_ordinal >= 0),
  credited_label text NOT NULL CHECK (btrim(credited_label) <> ''),
  credit_role text NOT NULL CHECK (credit_role ~ '^[a-z][a-z0-9_]*$'),
  PRIMARY KEY (research_release_id, archive_object_id, credit_ordinal),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_surface_presentation_projection_v3
      (research_release_id, archive_object_id) ON DELETE RESTRICT
);

CREATE TABLE release.research_surface_citation_projection_v3 (
  research_release_id uuid NOT NULL,
  archive_object_id uuid NOT NULL,
  citation_ordinal integer NOT NULL CHECK (citation_ordinal >= 0),
  citation_label text NOT NULL CHECK (btrim(citation_label) <> ''),
  public_source_route text NOT NULL CHECK (public_source_route ~ '^/sources/[0-9a-f]{64}$'),
  PRIMARY KEY (research_release_id, archive_object_id, citation_ordinal),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_surface_presentation_projection_v3
      (research_release_id, archive_object_id) ON DELETE RESTRICT
);

CREATE TABLE release.research_folder_membership_projection_v3 (
  research_release_id uuid NOT NULL,
  folder_id uuid NOT NULL,
  archive_object_id uuid NOT NULL,
  source_assignment_id uuid NOT NULL,
  membership_role text NOT NULL CHECK (membership_role ~ '^[a-z][a-z0-9_]*$'),
  member_ordinal integer NOT NULL CHECK (member_ordinal >= 0),
  source_assignment_status provenance.assertion_status NOT NULL CHECK (source_assignment_status = 'accepted'),
  source_assignment_snapshot_sha256 core.sha256_hex NOT NULL,
  effective_decision_id uuid NOT NULL,
  effective_decision_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (research_release_id, folder_id, archive_object_id, membership_role),
  UNIQUE (research_release_id, folder_id, membership_role, member_ordinal),
  FOREIGN KEY (research_release_id, folder_id)
    REFERENCES release.research_folder_projection_v3
      (research_release_id, folder_id) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_release_object
      (research_release_id, archive_object_id) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_surface_presentation_projection_v3
      (research_release_id, archive_object_id) ON DELETE RESTRICT
);

CREATE INDEX research_folder_membership_v3_folder_idx
  ON release.research_folder_membership_projection_v3
  (research_release_id, folder_id, membership_role, member_ordinal, archive_object_id);
CREATE INDEX research_folder_membership_v3_object_idx
  ON release.research_folder_membership_projection_v3
  (research_release_id, archive_object_id, folder_id, membership_role);
CREATE INDEX research_folder_projection_v3_type_slug_idx
  ON release.research_folder_projection_v3
  (research_release_id, folder_type_code, slug);
CREATE INDEX research_folder_projection_v3_type_sort_idx
  ON release.research_folder_projection_v3
  (research_release_id, folder_type_code, sort_ordinal, folder_id);

CREATE TABLE release.research_search_document_projection_v3 (
  research_release_id uuid NOT NULL,
  archive_object_id uuid NOT NULL,
  public_surface_id text NOT NULL,
  title text,
  search_document text NOT NULL CHECK (btrim(search_document) <> ''),
  sort_key text NOT NULL CHECK (btrim(sort_key) <> ''),
  PRIMARY KEY (research_release_id, archive_object_id),
  UNIQUE (research_release_id, public_surface_id),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_surface_presentation_projection_v3
      (research_release_id, archive_object_id) ON DELETE RESTRICT
);

CREATE TABLE release.research_corpus_summary_projection_v3 (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL,
  corpus_token core.release_token NOT NULL,
  corpus_version_token core.release_token NOT NULL,
  corpus_label text NOT NULL CHECK (btrim(corpus_label) <> ''),
  eligible_object_count bigint NOT NULL CHECK (eligible_object_count >= 0),
  held_object_count bigint NOT NULL CHECK (held_object_count >= 0),
  PRIMARY KEY (research_release_id, corpus_version_id)
);

CREATE TABLE release.research_trace_availability_projection_v3 (
  research_release_id uuid PRIMARY KEY,
  trace_eligible_object_count bigint NOT NULL CHECK (trace_eligible_object_count >= 0),
  trace_relation_count bigint NOT NULL CHECK (trace_relation_count >= 0),
  availability_reason text NOT NULL CHECK (btrim(availability_reason) <> '')
);

CREATE TABLE release.research_launch_component_manifest_v3 (
  research_release_id uuid NOT NULL,
  component_code text NOT NULL CHECK (component_code IN (
    'releaseObjects','surfacePresentation','surfaceCredits','surfaceCitations',
    'folderTypes','folders','folderMemberships','searchDocuments',
    'corpusSummary','traceAvailability'
  )),
  row_count bigint NOT NULL CHECK (row_count >= 0),
  content_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (research_release_id, component_code)
);

CREATE TABLE release.research_launch_build_receipt_v3 (
  research_release_id uuid PRIMARY KEY,
  builder_version core.release_token NOT NULL,
  migration_batch_id uuid NOT NULL REFERENCES raw.migration_batch(migration_batch_id) ON DELETE RESTRICT,
  public_corpus_version_id uuid NOT NULL REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  candidate_asset_id uuid NOT NULL REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  candidate_asset_sha256 core.sha256_hex NOT NULL,
  mapping_specification_sha256 core.sha256_hex NOT NULL,
  projection_query_pack_sha256 core.sha256_hex NOT NULL,
  selection_policy_sha256 core.sha256_hex NOT NULL,
  registry_corpus_policy_sha256 core.sha256_hex NOT NULL,
  source_snapshot_sha256 core.sha256_hex NOT NULL,
  projection_component_manifest_sha256 core.sha256_hex NOT NULL,
  projection_content_sha256 core.sha256_hex NOT NULL,
  build_receipt_sha256 core.sha256_hex NOT NULL,
  candidate_fingerprint core.sha256_hex NOT NULL,
  built_at timestamptz NOT NULL
);

-- This is a release-owned, named accounting of the source rows that were
-- deliberately not copied into a public projection.  It makes held,
-- excluded, proposed, rejected, and superseded source states auditable
-- without promoting any of them into the public read model.
CREATE TABLE release.research_launch_source_disposition_count_v3 (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  source_component text NOT NULL CHECK (source_component IN ('corpusMemberships','folderAssignments')),
  source_disposition text NOT NULL CHECK (source_disposition IN (
    'eligible','held','rejected','excluded','proposed','accepted','superseded'
  )),
  row_count bigint NOT NULL CHECK (row_count >= 0),
  PRIMARY KEY (research_release_id, source_component, source_disposition)
);

CREATE TABLE release.research_launch_validation_v3 (
  research_release_id uuid PRIMARY KEY,
  candidate_fingerprint core.sha256_hex NOT NULL,
  validation_receipt_sha256 core.sha256_hex NOT NULL,
  validated_at timestamptz NOT NULL
);

CREATE TABLE release.research_launch_manifest_v3 (
  research_release_id uuid PRIMARY KEY,
  manifest_bytes bytea NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL UNIQUE,
  created_at timestamptz NOT NULL,
  CHECK (encode(sha256(manifest_bytes), 'hex') = manifest_sha256)
);

RESET ROLE;
