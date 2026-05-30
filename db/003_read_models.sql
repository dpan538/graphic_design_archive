-- Modern Graphic Design History Archive Index
-- Read models for future frontend/API handoff.
-- These are read-only contracts over the skeleton tables.

create or replace view api_historical_nodes as
select
  node_id as id,
  node_name as title,
  date_start,
  date_end,
  date_text,
  geo_centers,
  transnational_routes,
  associated_formations,
  key_media_technologies,
  key_object_types,
  search_keywords,
  rights_risk_level,
  underdocumented_notes,
  editorial_note
from historical_nodes;

create or replace view api_source_registry as
select
  source_id as "sourceId",
  name,
  url,
  source_type as "sourceType",
  access_method as "accessMethod",
  priority,
  automated_ingestion as "automatedIngestion",
  link_only_safer as "linkOnlySafer",
  rights_summary as "rightsSummary",
  rights_uri_support as "rightsUriSupport",
  metadata_quality_estimate as "metadataQualityEstimate",
  stable_identifiers as "stableIdentifiers",
  default_image_zone::text as "defaultImageZone",
  default_record_policy::text as "defaultRecordPolicy",
  default_display_policy::text as "defaultDisplayPolicy",
  automation_status as "automationStatus",
  rights_basis as "rightsBasis",
  record_level_rights_required as "recordLevelRightsRequired",
  preview_allowed as "previewAllowed",
  thumbnail_allowed as "thumbnailAllowed",
  iiif_capable as "iiifCapable",
  api_key_required as "apiKeyRequired",
  protocol_sensitive as "protocolSensitive",
  last_verified_date as "lastVerifiedDate",
  notes
from sources;

create or replace view api_search_documents as
select
  search_doc_id as id,
  document_type as "documentType",
  title,
  body,
  seed_table as "seedTable",
  seed_id as "seedId",
  facets,
  entity_id as "entityId",
  source_record_id as "sourceRecordId",
  created_at as "createdAt",
  updated_at as "updatedAt"
from searchable_documents;

create or replace view api_entity_detail_base as
select
  e.entity_id as "entityId",
  e.entity_type::text as "entityType",
  e.preferred_label as "preferredLabel",
  e.alternate_labels as "alternateLabels",
  e.description,
  e.date_start as "dateStart",
  e.date_end as "dateEnd",
  e.date_text as "dateText",
  e.authority_scheme as "authorityScheme",
  e.authority_id as "authorityId",
  e.authority_status as "authorityStatus"
from entities e;

create or replace view api_source_record_detail_base as
select
  sr.source_record_id as "sourceRecordId",
  sr.source_id as "sourceId",
  s.name as "sourceName",
  s.url as "sourceUrl",
  sr.source_identifier as "sourceIdentifier",
  sr.source_record_url as "sourceRecordUrl",
  sr.source_title as title,
  sr.source_creator as creator,
  sr.source_date_text as "dateText",
  sr.source_rights_text as "sourceRightsText",
  sr.source_rights_uri as "sourceRightsUri",
  sr.capture_method as "captureMethod",
  sr.access_date as "accessDate",
  sr.normalized_entity_id as "normalizedEntityId",
  c.citation_text as "citationText",
  c.url as "citationUrl"
from source_records sr
join sources s on s.source_id = sr.source_id
left join citations c on c.source_record_id = sr.source_record_id;

create or replace view api_rights_review_summary as
select
  rr.rights_review_id as "rightsReviewId",
  rr.source_id as "sourceId",
  rr.source_record_id as "sourceRecordId",
  rr.image_asset_id as "imageAssetId",
  rr.rights_state::text as "rightsState",
  rr.rights_uri as "rightsUri",
  rr.rights_label as "rightsLabel",
  rr.review_status::text as "reviewStatus",
  rr.display_policy as "displayPolicy",
  rr.ingest_policy as "ingestPolicy",
  rr.basis,
  rr.notes
from rights_reviews rr;

create or replace view api_relation_assertions as
select
  a.assertion_id as "assertionId",
  a.subject_entity_id as "subjectEntityId",
  a.predicate,
  a.object_entity_id as "objectEntityId",
  a.assertion_type as "assertionType",
  a.confidence,
  a.note,
  a.source_record_id as "sourceRecordId",
  a.citation_id as "citationId",
  ar.assertion_status::text as "assertionStatus",
  ar.reviewed_at as "reviewedAt"
from assertions a
left join assertion_reviews ar on ar.assertion_id = a.assertion_id;

create or replace view api_regions as
select
  region_id as "regionId",
  region_name as "regionName",
  parent_region_id as "parentRegionId",
  region_type as "regionType",
  priority,
  coverage_reason as "coverageReason",
  known_bias_risk as "knownBiasRisk",
  language_scope as "languageScope",
  script_scope as "scriptScope",
  source_strategy as "sourceStrategy",
  notes
from regions;

create or replace view api_coverage_matrix as
select
  cm.coverage_id as "coverageId",
  cm.node_id as "nodeId",
  hn.node_name as "nodeName",
  cm.region_id as "regionId",
  r.region_name as "regionName",
  cm.coverage_status as "coverageStatus",
  cm.priority,
  cm.known_entry_points as "knownEntryPoints",
  cm.source_needs as "sourceNeeds",
  cm.rights_risk as "rightsRisk",
  cm.research_note as "researchNote"
from coverage_matrix cm
join historical_nodes hn on hn.node_id = cm.node_id
join regions r on r.region_id = cm.region_id;

create or replace view api_classification_axes as
select
  axis_id as "axisId",
  axis_name as "axisName",
  axis_type as "axisType",
  required_for_launch as "requiredForLaunch",
  required_for_record as "requiredForRecord",
  supports_multiple as "supportsMultiple",
  api_filter as "apiFilter",
  controlled_source as "controlledSource",
  notes
from classification_axes;

create or replace view api_geographies as
select
  g.geo_id as "geoId",
  g.name,
  g.parent_geo_id as "parentGeoId",
  p.name as "parentName",
  g.region_id as "regionId",
  r.region_name as "regionName",
  g.geo_type as "geoType",
  g.iso_code as "isoCode",
  g.language_scope as "languageScope",
  g.script_scope as "scriptScope",
  g.date_scope as "dateScope",
  g.notes
from geographies g
left join geographies p on p.geo_id = g.parent_geo_id
left join regions r on r.region_id = g.region_id;

create or replace view api_regional_movements as
select
  rm.regional_movement_id as "regionalMovementId",
  rm.name,
  rm.alternate_names as "alternateNames",
  rm.region_id as "regionId",
  r.region_name as "regionName",
  rm.geo_id as "geoId",
  g.name as "geoName",
  rm.date_start as "dateStart",
  rm.date_end as "dateEnd",
  rm.date_text as "dateText",
  rm.formation_type as "formationType",
  rm.related_node_ids as "relatedNodeIds",
  rm.related_movement_ids as "relatedMovementIds",
  rm.key_media as "keyMedia",
  rm.source_needs as "sourceNeeds",
  rm.rights_risk as "rightsRisk",
  rm.status,
  rm.movement_mode as "movementMode",
  rm.script_flags as "scriptFlags",
  rm.collective_authorship as "collectiveAuthorship",
  rm.periodical_relevance as "periodicalRelevance",
  rm.protocol_sensitive as "protocolSensitive",
  rm.source_priority_class as "sourcePriorityClass",
  rm.notes
from regional_movements rm
join regions r on r.region_id = rm.region_id
left join geographies g on g.geo_id = rm.geo_id;

create or replace view api_regional_event_nodes as
select
  ren.event_node_id as "eventNodeId",
  ren.event_name as "eventName",
  ren.event_type as "eventType",
  ren.region_id as "regionId",
  r.region_name as "regionName",
  ren.geo_id as "geoId",
  g.name as "geoName",
  ren.date_start as "dateStart",
  ren.date_end as "dateEnd",
  ren.date_text as "dateText",
  ren.related_node_ids as "relatedNodeIds",
  ren.related_regional_movement_ids as "relatedRegionalMovementIds",
  ren.source_need as "sourceNeed",
  ren.rights_risk as "rightsRisk",
  ren.status,
  ren.event_date_start as "eventDateStart",
  ren.event_date_end as "eventDateEnd",
  ren.date_precision as "datePrecision",
  ren.anchor_strength as "anchorStrength",
  ren.source_record_required as "sourceRecordRequired",
  ren.browse_priority as "browsePriority",
  ren.web_archive_relevant as "webArchiveRelevant",
  ren.notes
from regional_event_nodes ren
join regions r on r.region_id = ren.region_id
left join geographies g on g.geo_id = ren.geo_id;

create or replace view api_publication_surfaces as
select
  ps.publication_surface_id as "publicationSurfaceId",
  ps.seq_int as "seq",
  ps.seq_label as "seqLabel",
  ps.surface_type::text as "surfaceType",
  ps.target_type as "targetType",
  ps.target_id as "targetId",
  ps.entity_id as "entityId",
  ps.source_record_id as "sourceRecordId",
  ps.primary_historical_node_id as "historicalNodeId",
  hn.node_name as "historicalNodeName",
  ps.primary_movement_id as "movementId",
  m.name as "movementName",
  ps.primary_regional_movement_id as "regionalMovementId",
  rm.name as "regionalMovementName",
  ps.era_text as "era",
  ps.movement_display as "movementDisplay",
  ps.tier::text as "tier",
  ps.layout_id as "layoutId",
  ps.image_zone::text as "imageZone",
  ps.display_number as "displayNumber",
  ps.display_profile as "displayProfile",
  ps.workflow_status::text as "workflowStatus",
  ps.last_verified_at as "lastVerifiedAt",
  ps.published_at as "publishedAt"
from publication_surfaces ps
left join historical_nodes hn on hn.node_id = ps.primary_historical_node_id
left join movements m on m.movement_id = ps.primary_movement_id
left join regional_movements rm on rm.regional_movement_id = ps.primary_regional_movement_id;

create or replace view api_publication_surface_pages as
select
  psp.publication_page_id as "publicationPageId",
  psp.publication_surface_id as "publicationSurfaceId",
  ps.seq_int as "seq",
  psp.page_number as "pageNumber",
  psp.page_label as "pageLabel",
  psp.tier::text as "tier",
  psp.layout_id as "layoutId",
  psp.template_id as "templateId",
  psp.display_number as "displayNumber",
  psp.is_primary_page as "isPrimaryPage",
  psp.overflow_from_table::text as "overflowFromTable",
  psp.image_zone::text as "imageZone",
  psp.has_image_frame as "hasImageFrame",
  psp.image_layout_profile as "imageLayoutProfile",
  psp.page_profile as "pageProfile"
from publication_surface_pages psp
join publication_surfaces ps on ps.publication_surface_id = psp.publication_surface_id;

create or replace view api_surface_table_rows as
select
  str.surface_table_row_id as "surfaceTableRowId",
  str.publication_page_id as "publicationPageId",
  psp.publication_surface_id as "publicationSurfaceId",
  ps.seq_int as "seq",
  str.table_kind::text as "tableKind",
  str.row_order as "rowOrder",
  str.source_record_id as "sourceRecordId",
  str.citation_id as "citationId",
  str.assertion_id as "assertionId",
  str.classification_id as "classificationId",
  str.rights_review_id as "rightsReviewId",
  str.field_key as "fieldKey",
  str.source_label as "sourceLabel",
  str.source_value as "sourceValue",
  str.normalized_label as "normalizedLabel",
  str.normalized_value as "normalizedValue",
  str.confidence::text as "confidence",
  str.warning_code as "warningCode",
  str.display_json as "display"
from surface_table_rows str
join publication_surface_pages psp on psp.publication_page_id = str.publication_page_id
join publication_surfaces ps on ps.publication_surface_id = psp.publication_surface_id;

create or replace view api_folder_views as
select
  fv.folder_view_id as "folderViewId",
  fv.folder_type::text as "folderType",
  fv.folder_value as "folderValue",
  fv.title,
  fv.subtitle,
  fv.nameplate_text as "nameplateText",
  fv.tab_text as "tabText",
  fv.primary_historical_node_id as "historicalNodeId",
  fv.movement_id as "movementId",
  fv.regional_movement_id as "regionalMovementId",
  fv.medium_id as "mediumId",
  fv.region_id as "regionId",
  fv.geo_id as "geoId",
  fv.source_id as "sourceId",
  fv.sort_rule as "sortRule",
  fv.coverage_note as "coverageNote",
  fv.rights_overview as "rightsOverview"
from folder_views fv;

create or replace view api_folder_memberships as
select
  fm.folder_membership_id as "folderMembershipId",
  fm.folder_view_id as "folderViewId",
  fv.folder_type::text as "folderType",
  fv.folder_value as "folderValue",
  fm.publication_surface_id as "publicationSurfaceId",
  ps.seq_int as "seq",
  ps.display_number as "displayNumber",
  fm.membership_basis as "membershipBasis",
  fm.classification_id as "classificationId",
  fm.confidence::text as "confidence",
  fm.sort_seq as "sortSeq"
from folder_memberships fm
join folder_views fv on fv.folder_view_id = fm.folder_view_id
join publication_surfaces ps on ps.publication_surface_id = fm.publication_surface_id;

create or replace view api_filing_registry_cards as
select
  frc.registry_card_id as "registryCardId",
  frc.classification_type as "classificationType",
  frc.classification_value as "classificationValue",
  frc.folder_view_id as "folderViewId",
  frc.classified_at as "classifiedAt",
  frc.modified_at as "modifiedAt",
  frc.registrar,
  frc.registry_note as "registryNote"
from filing_registry_cards frc;

create or replace view api_filing_registry_members as
select
  frm.registry_member_id as "registryMemberId",
  frm.registry_card_id as "registryCardId",
  frm.publication_surface_id as "publicationSurfaceId",
  frm.seq_int as "seq",
  frm.display_number as "displayNumber",
  frm.historical_node_id as "historicalNodeId",
  frm.movement_display as "movementDisplay",
  frm.member_note as "memberNote"
from filing_registry_members frm;

create or replace view api_sparse_cards as
select
  sc.sparse_card_id as "sparseCardId",
  sc.card_type as "cardType",
  sc.title,
  sc.target_type as "targetType",
  sc.target_id as "targetId",
  sc.parent_publication_surface_id as "parentPublicationSurfaceId",
  sc.parent_sparse_card_id as "parentSparseCardId",
  sc.promotion_status::text as "promotionStatus",
  sc.promotion_checklist_json as "promotionChecklist",
  sc.notes
from sparse_cards sc;

create or replace view api_archive_bookmarks as
select
  ab.bookmark_id as "bookmarkId",
  ab.title,
  ab.bookmark_type as "bookmarkType",
  ab.target_type as "targetType",
  ab.target_id as "targetId",
  ab.folder_view_id as "folderViewId",
  ab.stable_slug as "stableSlug",
  ab.body_md as "bodyMd",
  ab.status::text as "status"
from archive_bookmarks ab;

create or replace view api_evidence_bundles as
select
  eb.evidence_bundle_id as "evidenceBundleId",
  eb.title,
  eb.evidence_mode::text as "evidenceMode",
  eb.confidence::text as "confidence",
  eb.review_status::text as "reviewStatus",
  eb.summary,
  eb.notes
from evidence_bundles eb;

create or replace view api_evidence_bundle_items as
select
  ebi.evidence_bundle_item_id as "evidenceBundleItemId",
  ebi.evidence_bundle_id as "evidenceBundleId",
  ebi.item_order as "itemOrder",
  ebi.source_record_id as "sourceRecordId",
  ebi.citation_id as "citationId",
  ebi.authority_source_id as "authoritySourceId",
  ebi.external_identifier_id as "externalIdentifierId",
  ebi.evidence_role as "evidenceRole",
  ebi.evidence_quote as "evidenceQuote",
  ebi.evidence_note as "evidenceNote"
from evidence_bundle_items ebi;

create or replace view api_external_identifier_status as
select
  ei.external_identifier_id as "externalIdentifierId",
  ei.entity_id as "entityId",
  ei.seed_table as "seedTable",
  ei.seed_id as "seedId",
  ei.authority_source_id as "authoritySourceId",
  aus.name as "authoritySourceName",
  ei.authority_scheme as "authorityScheme",
  ei.authority_id as "authorityId",
  ei.authority_url as "authorityUrl",
  ei.confidence::text as "confidence",
  ei.review_status::text as "reviewStatus",
  ei.match_status::text as "matchStatus",
  ei.match_method as "matchMethod",
  ei.reviewed_by as "reviewedBy",
  ei.reviewed_at as "reviewedAt",
  ei.evidence_bundle_id as "evidenceBundleId",
  ei.replacement_identifier_id as "replacementIdentifierId",
  ei.is_preferred_for_entity_class as "isPreferredForEntityClass",
  ei.deprecated_at as "deprecatedAt",
  ei.deprecation_reason as "deprecationReason",
  ei.source_note as "sourceNote"
from external_identifiers ei
left join authority_sources aus on aus.authority_source_id = ei.authority_source_id;

create or replace view api_authority_resolution_events as
select
  are.authority_resolution_event_id as "authorityResolutionEventId",
  are.target_type as "targetType",
  are.target_id as "targetId",
  are.external_identifier_id as "externalIdentifierId",
  are.authority_source_id as "authoritySourceId",
  are.authority_scheme as "authorityScheme",
  are.authority_id as "authorityId",
  are.authority_url as "authorityUrl",
  are.previous_status::text as "previousStatus",
  are.new_status::text as "newStatus",
  are.match_method as "matchMethod",
  are.confidence::text as "confidence",
  are.evidence_bundle_id as "evidenceBundleId",
  are.proposed_by as "proposedBy",
  are.reviewed_by as "reviewedBy",
  are.event_note as "eventNote",
  are.created_at as "createdAt"
from authority_resolution_events are;

create or replace view api_entity_appellations as
select
  ea.appellation_id as "appellationId",
  ea.entity_id as "entityId",
  e.preferred_label as "entityPreferredLabel",
  ea.label_text as "labelText",
  ea.label_type::text as "labelType",
  ea.language_code as "languageCode",
  ea.script_code as "scriptCode",
  ea.romanization_system as "romanizationSystem",
  ea.source_id as "sourceId",
  ea.source_record_id as "sourceRecordId",
  ea.authority_source_id as "authoritySourceId",
  ea.valid_from as "validFrom",
  ea.valid_to as "validTo",
  ea.is_source_label as "isSourceLabel",
  ea.is_preferred_for_display as "isPreferredForDisplay",
  ea.display_priority as "displayPriority",
  ea.confidence::text as "confidence",
  ea.notes
from entity_appellations ea
join entities e on e.entity_id = ea.entity_id;

create or replace view api_geography_appellations as
select
  ga.geography_appellation_id as "geographyAppellationId",
  ga.geo_id as "geoId",
  g.name as "geoName",
  ga.label_text as "labelText",
  ga.label_type::text as "labelType",
  ga.language_code as "languageCode",
  ga.script_code as "scriptCode",
  ga.romanization_system as "romanizationSystem",
  ga.source_id as "sourceId",
  ga.authority_source_id as "authoritySourceId",
  ga.valid_from as "validFrom",
  ga.valid_to as "validTo",
  ga.is_source_label as "isSourceLabel",
  ga.is_preferred_for_display as "isPreferredForDisplay",
  ga.display_priority as "displayPriority",
  ga.confidence::text as "confidence",
  ga.notes
from geography_appellations ga
join geographies g on g.geo_id = ga.geo_id;

create or replace view api_relation_predicate_rules as
select
  rp.predicate_id as "predicateId",
  rp.predicate,
  rp.label,
  rp.inverse_predicate as "inversePredicate",
  rp.description,
  rp.evidence_required as "evidenceRequired",
  rp.default_confidence::text as "defaultConfidence",
  rp.allows_uncited_use as "allowsUncitedUse",
  rp.domain_class as "domainClass",
  rp.range_class as "rangeClass",
  rp.requires_citation as "requiresCitation",
  rp.allows_visual_only as "allowsVisualOnly",
  rp.ui_visibility_default as "uiVisibilityDefault",
  rp.standard_mapping as "standardMapping",
  rp.public_warning as "publicWarning"
from relation_predicates rp;

create or replace view api_protocol_rights_reviews as
select
  rr.rights_review_id as "rightsReviewId",
  rr.source_id as "sourceId",
  rr.source_record_id as "sourceRecordId",
  rr.image_asset_id as "imageAssetId",
  rr.rights_state::text as "rightsState",
  rr.display_policy as "displayPolicy",
  rr.ingest_policy as "ingestPolicy",
  rr.display_zone_max::text as "displayZoneMax",
  rr.protocol_notice as "protocolNotice",
  rr.tk_label as "tkLabel",
  rr.community_access_flag as "communityAccessFlag",
  rr.sensitivity_flag as "sensitivityFlag",
  rr.deceased_name_warning as "deceasedNameWarning",
  rr.rights_basis as "rightsBasis",
  rr.required_statement as "requiredStatement",
  rr.review_status::text as "reviewStatus",
  rr.reviewed_by as "reviewedBy",
  rr.reviewed_at as "reviewedAt",
  rr.notes
from rights_reviews rr;

create or replace view api_source_policy_summary as
select
  s.source_id as "sourceId",
  s.name,
  s.url,
  s.home_url as "homeUrl",
  s.source_type as "sourceType",
  s.access_method as "accessMethod",
  s.geo_coverage as "geoCoverage",
  s.country,
  s.coverage_scope as "coverageScope",
  s.api_base as "apiBase",
  s.iiif_base as "iiifBase",
  s.oai_base as "oaiBase",
  s.stable_identifier_pattern as "stableIdentifierPattern",
  s.default_record_policy::text as "defaultRecordPolicy",
  s.default_display_policy::text as "defaultDisplayPolicy",
  s.default_image_zone::text as "defaultImageZone",
  s.metadata_license as "metadataLicense",
  s.image_license_model as "imageLicenseModel",
  s.terms_url as "termsUrl",
  s.api_terms_url as "apiTermsUrl",
  s.robots_url as "robotsUrl",
  s.rate_limit as "rateLimit",
  s.requires_api_key as "requiresApiKey",
  s.supports_non_latin as "supportsNonLatin",
  s.supports_rights_uri as "supportsRightsUri",
  s.supports_item_level_rights as "supportsItemLevelRights",
  s.supports_thumbnail_rights as "supportsThumbnailRights",
  s.cultural_protocol_risk as "culturalProtocolRisk",
  s.privacy_risk as "privacyRisk",
  s.last_terms_reviewed_at as "lastTermsReviewedAt",
  s.terms_review_status::text as "termsReviewStatus",
  s.policy_notes as "policyNotes"
from sources s;

create or replace view api_source_terms_review_policy as
select
  str.source_terms_review_id as "sourceTermsReviewId",
  str.source_id as "sourceId",
  s.name as "sourceName",
  str.review_status::text as "reviewStatus",
  str.reviewed_by as "reviewedBy",
  str.reviewed_at as "reviewedAt",
  str.terms_url as "termsUrl",
  str.api_terms_url as "apiTermsUrl",
  str.robots_url as "robotsUrl",
  str.terms_snapshot_url as "termsSnapshotUrl",
  str.api_terms_snapshot_url as "apiTermsSnapshotUrl",
  str.robots_snapshot as "robotsSnapshot",
  str.metadata_policy::text as "metadataPolicy",
  str.image_policy::text as "imagePolicy",
  str.scraping_policy::text as "scrapingPolicy",
  str.automated_ingestion_allowed as "automatedIngestionAllowed",
  str.key_clauses as "keyClauses",
  str.image_reuse_summary as "imageReuseSummary",
  str.thumbnail_reuse_summary as "thumbnailReuseSummary",
  str.iiif_summary as "iiifSummary",
  str.prohibited_uses as "prohibitedUses",
  str.rate_limit_summary as "rateLimitSummary",
  str.commercial_use_summary as "commercialUseSummary",
  str.takedown_contact as "takedownContact",
  str.decision::text as "decision",
  str.access_mode as "accessMode",
  str.api_available as "apiAvailable",
  str.api_key_required as "apiKeyRequired",
  str.automation_level as "automationLevel",
  str.forbidden_behavior as "forbiddenBehavior",
  str.default_image_zone::text as "defaultImageZone",
  str.evidence_urls as "evidenceUrls",
  str.terms_checked_date as "termsCheckedDate",
  str.supersedes_review_id as "supersedesReviewId",
  str.notes
from source_terms_reviews str
join sources s on s.source_id = str.source_id;

create or replace view api_experimental_ingest_candidates as
select
  eic.experimental_candidate_id as "experimentalCandidateId",
  eic.candidate_name as "candidateName",
  eic.source_id as "sourceId",
  eic.source_name as "sourceName",
  eic.region,
  eic.record_type as "recordType",
  eic.test_purpose as "testPurpose",
  eic.expected_rights_state as "expectedRightsState",
  eic.expected_image_zone::text as "expectedImageZone",
  eic.expected_record_policy::text as "expectedRecordPolicy",
  eic.expected_display_policy::text as "expectedDisplayPolicy",
  eic.likely_fields as "likelyFields",
  eic.risks,
  eic.scope_cell_id as "scopeCellId",
  eic.scope_role as "scopeRole",
  eic.primary_region as "primaryRegion",
  eic.secondary_region as "secondaryRegion",
  eic.hn_ids as "historicalNodeIds",
  eic.movement_ids as "movementIds",
  eic.event_ids as "eventIds",
  eic.source_family_id as "sourceFamilyId",
  eic.record_family as "recordFamily",
  eic.default_image_zone::text as "defaultImageZone",
  eic.rights_review_level as "rightsReviewLevel",
  eic.protocol_sensitive as "protocolSensitive",
  eic.manual_review_required as "manualReviewRequired",
  eic.query_profile_id as "queryProfileId",
  eic.target_record_count as "targetRecordCount",
  eic.required_fields as "requiredFields",
  eic.expected_surface_type as "expectedSurfaceType",
  eic.shortlist_status::text as "shortlistStatus",
  eic.notes
from experimental_ingest_candidates eic;

create or replace view api_source_record_relations as
select
  srr.source_record_relation_id as "sourceRecordRelationId",
  srr.subject_source_record_id as "subjectSourceRecordId",
  srr.predicate,
  srr.object_source_record_id as "objectSourceRecordId",
  srr.object_url as "objectUrl",
  srr.relation_order as "relationOrder",
  srr.locator,
  srr.basis,
  srr.confidence::text as "confidence",
  srr.citation_id as "citationId",
  srr.notes
from source_record_relations srr;

create or replace view api_digital_representations as
select
  dr.representation_id as "representationId",
  dr.source_record_id as "sourceRecordId",
  dr.entity_id as "entityId",
  dr.image_asset_id as "imageAssetId",
  dr.representation_type::text as "representationType",
  dr.representation_url as "representationUrl",
  dr.source_item_url as "sourceItemUrl",
  dr.original_url as "originalUrl",
  dr.capture_url as "captureUrl",
  dr.capture_datetime as "captureDatetime",
  dr.iiif_manifest_url as "iiifManifestUrl",
  dr.iiif_canvas_id as "iiifCanvasId",
  dr.thumbnail_url as "thumbnailUrl",
  dr.embed_url as "embedUrl",
  dr.mime_type as "mimeType",
  dr.width_px as "widthPx",
  dr.height_px as "heightPx",
  dr.source_rights_text as "sourceRightsText",
  dr.source_rights_uri as "sourceRightsUri",
  dr.source_terms_review_id as "sourceTermsReviewId",
  dr.rights_review_id as "rightsReviewId",
  dr.img_state::text as "imgState",
  dr.display_permitted as "displayPermitted",
  dr.local_copy_permitted as "localCopyPermitted",
  dr.required_credit as "requiredCredit",
  dr.review_status::text as "reviewStatus",
  dr.notes
from digital_representations dr;

create or replace view api_field_provenance as
select
  fp.field_provenance_id as "fieldProvenanceId",
  fp.target_table as "targetTable",
  fp.target_id as "targetId",
  fp.target_path as "targetPath",
  fp.source_record_id as "sourceRecordId",
  fp.source_field_path as "sourceFieldPath",
  fp.source_literal as "sourceLiteral",
  fp.normalized_value as "normalizedValue",
  fp.assertion_basis as "assertionBasis",
  fp.evidence_bundle_id as "evidenceBundleId",
  fp.citation_id as "citationId",
  fp.confidence::text as "confidence",
  fp.review_status::text as "reviewStatus",
  fp.reviewed_by as "reviewedBy",
  fp.reviewed_at as "reviewedAt",
  fp.notes
from field_provenance fp;

create or replace view api_record_family_profiles as
select
  rfp.record_family as "recordFamily",
  rfp.family_label as "familyLabel",
  rfp.required_source_fields as "requiredSourceFields",
  rfp.required_normalized_fields as "requiredNormalizedFields",
  rfp.required_rights_fields as "requiredRightsFields",
  rfp.required_classification_fields as "requiredClassificationFields",
  rfp.required_relation_fields as "requiredRelationFields",
  rfp.required_citation_fields as "requiredCitationFields",
  rfp.default_surface_type::text as "defaultSurfaceType",
  rfp.default_image_zone::text as "defaultImageZone",
  rfp.missing_data_strategy as "missingDataStrategy",
  rfp.notes
from record_family_profiles rfp;

create or replace view api_ingest_validation_rules as
select
  ivr.validation_rule_id as "validationRuleId",
  ivr.validation_target as "validationTarget",
  ivr.required_fields as "requiredFields",
  ivr.blocking_failure as "blockingFailure",
  ivr.warning_only as "warningOnly",
  ivr.suggested_workflow_status::text as "suggestedWorkflowStatus",
  ivr.applies_to_record_family as "appliesToRecordFamily",
  ivr.applies_to_image_zone::text as "appliesToImageZone",
  ivr.notes
from ingest_validation_rules ivr;

create or replace view api_first_ingest_record_targets as
select
  firt.first_target_id as "firstTargetId",
  firt.target_number as "targetNumber",
  firt.scope_cell_id as "scopeCellId",
  firt.target_label as "targetLabel",
  firt.source_name as "sourceName",
  firt.source_url_or_search_path as "sourceUrlOrSearchPath",
  firt.record_family as "recordFamily",
  firt.region,
  firt.date_text as "dateText",
  firt.creator_or_institution as "creatorOrInstitution",
  firt.why_selected as "whySelected",
  firt.expected_image_zone::text as "expectedImageZone",
  firt.rights_risk as "rightsRisk",
  firt.target_status::text as "targetStatus",
  firt.manual_rights_review_required as "manualRightsReviewRequired",
  firt.source_terms_review_required as "sourceTermsReviewRequired",
  firt.required_citation as "requiredCitation",
  firt.fallback_target as "fallbackTarget",
  firt.ingest_order as "ingestOrder",
  firt.notes
from first_ingest_record_targets firt;

create or replace view api_first_ingest_target_verifications as
select
  fitv.verification_id as "verificationId",
  fitv.first_target_id as "firstTargetId",
  firt.target_number as "targetNumber",
  firt.scope_cell_id as "scopeCellId",
  firt.target_label as "targetLabel",
  fitv.verification_decision as "verificationDecision",
  fitv.verified_at as "verifiedAt",
  fitv.verified_by as "verifiedBy",
  fitv.confirmed_image_zone::text as "confirmedImageZone",
  fitv.canonical_url as "canonicalUrl",
  fitv.replacement_url as "replacementUrl",
  fitv.evidence_summary as "evidenceSummary",
  fitv.required_action as "requiredAction",
  fitv.blocking_reason as "blockingReason"
from first_ingest_target_verifications fitv
join first_ingest_record_targets firt on firt.first_target_id = fitv.first_target_id;

create or replace view api_fallback_source_stubs as
select
  fss.fallback_stub_id as "fallbackStubId",
  fss.first_target_id as "firstTargetId",
  fss.scope_cell_id as "scopeCellId",
  fss.target_label as "targetLabel",
  fss.source_name as "sourceName",
  fss.source_url_or_search_path as "sourceUrlOrSearchPath",
  fss.canonical_url as "canonicalUrl",
  fss.replacement_url as "replacementUrl",
  fss.fallback_status::text as "fallbackStatus",
  fss.public_stub_policy as "publicStubPolicy",
  fss.expected_image_zone::text as "expectedImageZone",
  fss.display_area_policy as "displayAreaPolicy",
  fss.not_ingested_reason as "notIngestedReason",
  fss.user_action_label as "userActionLabel",
  fss.user_action_url as "userActionUrl",
  fss.verification_decision as "verificationDecision",
  fss.verified_at as "verifiedAt",
  fss.verified_by as "verifiedBy",
  fss.evidence_summary as "evidenceSummary",
  fss.required_action as "requiredAction",
  fss.blocking_reason as "blockingReason"
from fallback_source_stubs fss;

create or replace view api_source_redundancy_candidates as
select
  src.redundancy_candidate_id as "redundancyCandidateId",
  src.scope_cell_id as "scopeCellId",
  src.candidate_label as "candidateLabel",
  src.candidate_class as "candidateClass",
  src.creator_or_institution as "creatorOrInstitution",
  src.date_text as "dateText",
  src.source_name as "sourceName",
  src.url_or_search_path as "urlOrSearchPath",
  src.record_family as "recordFamily",
  src.expected_image_zone::text as "expectedImageZone",
  src.rights_risk as "rightsRisk",
  src.automation_feasibility as "automationFeasibility",
  src.replace_failed_target as "replaceFailedTarget"
from source_redundancy_candidates src;

create or replace view api_source_redundancy_triage as
select
  srt.triage_id as "triageId",
  srt.probable_failed_target as "probableFailedTarget",
  srt.likely_failure_mode as "likelyFailureMode",
  srt.recommended_action as "recommendedAction",
  srt.best_replacement_or_next_move as "bestReplacementOrNextMove"
from source_redundancy_triage srt;

create or replace view api_recommended_six_target_ingest_sets as
select
  rset.recommended_set_id as "recommendedSetId",
  rset.scope_cell_id as "scopeCellId",
  rset.recommended_six_target_ingest_set as "recommendedSixTargetIngestSet"
from recommended_six_target_ingest_sets rset;

create or replace view api_fallback_remediation_recommendations as
select
  frr.remediation_id as "remediationId",
  frr.failed_target_or_cell as "failedTargetOrCell",
  frr.original_target_label as "originalTargetLabel",
  frr.original_source as "originalSource",
  frr.failure_type as "failureType",
  frr.confirmed_exact_url as "confirmedExactUrl",
  frr.replacement_url as "replacementUrl",
  frr.source_title as "sourceTitle",
  frr.creator_or_institution as "creatorOrInstitution",
  frr.date_text as "dateText",
  frr.record_family as "recordFamily",
  frr.rights_note as "rightsNote",
  frr.recommended_image_zone::text as "recommendedImageZone",
  frr.recommended_status as "recommendedStatus",
  frr.reason
from fallback_remediation_recommendations frr;

create or replace view api_fallback_remediation_projection as
select
  frp.projection_id as "projectionId",
  frp.fallback_stub_id as "fallbackStubId",
  frp.first_target_id as "firstTargetId",
  frp.scope_cell_id as "scopeCellId",
  frp.target_label as "targetLabel",
  frp.current_fallback_status as "currentFallbackStatus",
  frp.current_user_action_url as "currentUserActionUrl",
  frp.remediation_recommended_status as "remediationRecommendedStatus",
  frp.projected_status as "projectedStatus",
  frp.projected_url as "projectedUrl",
  frp.projected_image_zone::text as "projectedImageZone",
  frp.source_title as "sourceTitle",
  frp.rights_note as "rightsNote",
  frp.rationale
from fallback_remediation_projection frp;

create or replace view api_global_source_expansion_candidates as
select
  gsec.source_expansion_id as "sourceExpansionId",
  gsec.source_name as "sourceName",
  gsec.region,
  gsec.source_type as "sourceType",
  gsec.url,
  gsec.access_method as "accessMethod",
  gsec.api_iiif_oai_data as "apiIiifOaiData",
  gsec.likely_record_types as "likelyRecordTypes",
  gsec.graphic_design_relevance as "graphicDesignRelevance",
  gsec.rights_clarity as "rightsClarity",
  gsec.stable_identifier_quality as "stableIdentifierQuality",
  gsec.automation_feasibility as "automationFeasibility",
  gsec.default_image_zone::text as "defaultImageZone",
  gsec.recommended_use as "recommendedUse",
  gsec.evidence
from global_source_expansion_candidates gsec;

create or replace view api_first_production_low_friction_sources as
select
  fplfs.low_friction_id as "lowFrictionId",
  fplfs.source_name as "sourceName",
  fplfs.why_production_ingest as "whyProductionIngest",
  fplfs.evidence
from first_production_low_friction_sources fplfs;

create or replace view api_high_value_fragile_sources as
select
  hvfs.fragile_source_id as "fragileSourceId",
  hvfs.source_name as "sourceName",
  hvfs.why_valuable as "whyValuable",
  hvfs.why_fragile as "whyFragile",
  hvfs.recommended_treatment as "recommendedTreatment",
  hvfs.evidence
from high_value_fragile_sources hvfs;

create or replace view api_remediation_source_verifications as
select
  rsv.remediation_verification_id as "remediationVerificationId",
  rsv.projection_ids as "projectionIds",
  rsv.affected_first_target_ids as "affectedFirstTargetIds",
  rsv.scope_cell_id as "scopeCellId",
  rsv.verification_decision as "verificationDecision",
  rsv.verified_url as "verifiedUrl",
  rsv.source_name as "sourceName",
  rsv.source_title as "sourceTitle",
  rsv.record_family as "recordFamily",
  rsv.date_text as "dateText",
  rsv.confirmed_image_zone::text as "confirmedImageZone",
  rsv.promotion_action as "promotionAction",
  rsv.rights_summary as "rightsSummary",
  rsv.evidence_summary as "evidenceSummary",
  rsv.remaining_blocker as "remainingBlocker"
from remediation_source_verifications rsv;

create or replace view api_capture_batch_records as
select
  ecr.capture_id as "captureId",
  ecr.direction_id as "directionId",
  ecr.direction_name as "directionName",
  ecr.source_id as "sourceId",
  ecr.source_name as "sourceName",
  ecr.source_api_url as "sourceApiUrl",
  ecr.capture_status as "captureStatus",
  ecr.source_identifier as "sourceIdentifier",
  ecr.source_record_url as "sourceRecordUrl",
  ecr.source_title as "sourceTitle",
  ecr.source_creator as "sourceCreator",
  ecr.source_date_text as "sourceDateText",
  ecr.date_start as "dateStart",
  ecr.date_end as "dateEnd",
  ecr.source_place_text as "sourcePlaceText",
  ecr.source_object_type as "sourceObjectType",
  ecr.source_medium as "sourceMedium",
  ecr.source_collection as "sourceCollection",
  ecr.source_rights_text as "sourceRightsText",
  ecr.rights_uri as "rightsUri",
  ecr.rights_basis as "rightsBasis",
  ecr.image_presence_code::text as "imagePresenceCode",
  ecr.image_presence_basis as "imagePresenceBasis",
  ecr.image_state_evaluation as "imageStateEvaluation",
  ecr.image_state_confidence as "imageStateConfidence",
  ecr.rights_review_required as "rightsReviewRequired",
  ecr.image_state_review_note as "imageStateReviewNote",
  ecr.image_frame_behavior as "imageFrameBehavior",
  ecr.image_url_detected as "imageUrlDetected",
  ecr.local_copy_permitted as "localCopyPermitted",
  ecr.iiif_or_viewer_available as "iiifOrViewerAvailable",
  ecr.fallback_required as "fallbackRequired",
  ecr.fallback_reason as "fallbackReason",
  ecr.raw_json_path as "rawJsonPath",
  ecr.access_date as "accessDate"
from capture_batch_records ecr;

create or replace view api_capture_batch_summary as
select
  ecr.direction_id as "directionId",
  ecr.direction_name as "directionName",
  ecr.source_id as "sourceId",
  ecr.source_name as "sourceName",
  count(*)::int as "capturedCount",
  count(*) filter (where ecr.capture_status <> 'captured')::int as "nonCapturedCount",
  count(*) filter (where ecr.image_presence_code = 'IMG00')::int as "img00Count",
  count(*) filter (where ecr.image_presence_code = 'IMG01')::int as "img01Count",
  count(*) filter (where ecr.image_presence_code = 'IMG02')::int as "img02Count",
  count(*) filter (where ecr.image_presence_code = 'IMG03')::int as "img03Count",
  count(*) filter (where ecr.image_presence_code = 'IMG04')::int as "img04Count"
from capture_batch_records ecr
group by ecr.direction_id, ecr.direction_name, ecr.source_id, ecr.source_name;

create or replace view api_capture_batch_cell_assignments as
select
  cbca.capture_id as "captureId",
  cbca.source_id as "sourceId",
  cbca.source_name as "sourceName",
  cbca.source_title as "sourceTitle",
  cbca.image_presence_code::text as "imagePresenceCode",
  cbca.assigned_cell_id as "assignedCellId",
  cbca.assigned_cell_name as "assignedCellName",
  cbca.assignment_type as "assignmentType",
  cbca.assignment_confidence as "assignmentConfidence",
  cbca.assignment_basis as "assignmentBasis",
  cbca.matched_terms as "matchedTerms",
  cbca.recommended_next_step as "recommendedNextStep"
from capture_batch_cell_assignments cbca;

create or replace view api_capture_batch_cell_summary as
select
  cbcs.cell_id as "cellId",
  cbcs.cell_name as "cellName",
  cbcs.cell_type as "cellType",
  cbcs.assigned_count as "assignedCount",
  cbcs.img00_count as "img00Count",
  cbcs.img01_count as "img01Count",
  cbcs.img02_count as "img02Count",
  cbcs.img03_count as "img03Count",
  cbcs.img04_count as "img04Count",
  cbcs.source_names as "sourceNames",
  cbcs.sample_capture_ids as "sampleCaptureIds",
  cbcs.cell_status as "cellStatus",
  cbcs.next_generation_action as "nextGenerationAction"
from capture_batch_cell_summary cbcs;

create or replace view api_capture_batch_next_generation_queue as
select
  cbngq.queue_id as "queueId",
  cbngq.cell_id as "cellId",
  cbngq.cell_name as "cellName",
  cbngq.cell_type as "cellType",
  cbngq.priority,
  cbngq.reason,
  cbngq.recommended_query as "recommendedQuery",
  cbngq.recommended_sources as "recommendedSources",
  cbngq.required_img_states as "requiredImgStates",
  cbngq.minimum_next_capture_count as "minimumNextCaptureCount"
from capture_batch_next_generation_queue cbngq;
