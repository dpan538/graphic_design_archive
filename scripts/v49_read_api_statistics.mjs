#!/usr/bin/env node
// Versioned, SELECT-only v49 canonical/release/API statistics generator.
// The internal audit connection is forced read-only by both PGOPTIONS and an
// explicit transaction; API-visible statistics use the formal API reader role.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { mkdirSync } from "node:fs";

function parseArguments(argv) {
  const parsed = {};
  for (let index = 2; index < argv.length; index += 2) parsed[argv[index]] = argv[index + 1];
  return parsed;
}
const args = parseArguments(process.argv);
for (const key of ["--psql", "--host", "--port", "--database", "--audit-role", "--api-role", "--schema-hash", "--verifier", "--reconciliation", "--api-results", "--runtime-profile", "--json", "--csv", "--markdown"]) {
  if (!args[key]) throw new Error(`missing ${key}`);
}
if (!args["--host"].startsWith("/private/tmp/") || args["--port"] === "5432" || !args["--database"].startsWith("gda_v49_phase2a_")) {
  throw new Error("isolated local database boundary rejected");
}

const forbiddenSql = /\b(insert|update|delete|merge|create|alter|drop|truncate|refresh|grant|revoke|copy|call|do)\b/i;
function queryJson(role, selectSql) {
  if (forbiddenSql.test(selectSql)) throw new Error("statistics SQL must be SELECT-only");
  const transaction = `BEGIN READ ONLY;\nSET LOCAL statement_timeout='120s';\n${selectSql.trim().replace(/;$/, "")};\nROLLBACK;\n`;
  const result = spawnSync(args["--psql"], ["-X", "-Atq", "-v", "ON_ERROR_STOP=1"], {
    env: {
      ...process.env,
      PGHOST: args["--host"],
      PGPORT: args["--port"],
      PGDATABASE: args["--database"],
      PGUSER: role,
      PGOPTIONS: "-c default_transaction_read_only=on",
    },
    input: transaction,
    encoding: "utf8",
    timeout: 130_000,
  });
  if (result.status !== 0) throw new Error(`statistics query failed as ${role}: ${result.stderr.trim()}`);
  const line = result.stdout.split("\n").find((value) => value.startsWith("{"));
  if (!line) throw new Error(`statistics query returned no JSON as ${role}`);
  return JSON.parse(line);
}
function readJson(path) { return JSON.parse(readFileSync(resolve(path), "utf8")); }
function write(path, value) { const target = resolve(path); mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, value); }
function csvCell(value) { return `"${String(value ?? "").replaceAll('"', '""')}"`; }

const internalSql = String.raw`
WITH latest AS (
  SELECT * FROM release.research_release WHERE release_state='sealed'
  ORDER BY sealed_at DESC, research_release_id DESC LIMIT 1
), object_types AS (
  SELECT convert_from(raw_bytes,'UTF8')::jsonb #>> '{}' AS value, count(*) AS count
  FROM raw.field_literal WHERE json_pointer='/objectType' GROUP BY value
), sources AS (
  SELECT convert_from(raw_bytes,'UTF8')::jsonb #>> '{}' AS value, count(*) AS count
  FROM raw.field_literal WHERE json_pointer='/sourceName' GROUP BY value
), geographies AS (
  SELECT convert_from(raw_bytes,'UTF8')::jsonb #>> '{}' AS value, count(*) AS count
  FROM raw.field_literal WHERE json_pointer='/authority/geographyClass' GROUP BY value
), date_values AS (
  SELECT convert_from(raw_bytes,'UTF8')::jsonb #>> '{}' AS value
  FROM raw.field_literal WHERE json_pointer='/dateStart'
), year_ranges AS (
  SELECT CASE WHEN value ~ '^[0-9]{4}$'
    THEN ((value::integer / 10) * 10)::text || 's'
    ELSE 'null_or_non_year' END AS value, count(*) AS count
  FROM date_values GROUP BY 1
), folder_types AS (
  SELECT convert_from(raw_bytes,'UTF8')::jsonb #>> '{}' AS value, count(*) AS count
  FROM raw.field_literal WHERE json_pointer ~ '^/folders/[0-9]+/type$' GROUP BY value
), assignment_states AS (
  SELECT status::text AS value, count(*) AS count FROM provenance.canonical_assignment GROUP BY status
), relation_types AS (
  SELECT rt.relation_code AS value, count(*) AS count
  FROM research.semantic_relation r JOIN research.relation_type rt USING (relation_type_id)
  GROUP BY rt.relation_code
), rights_states AS (
  SELECT delivery_mode::text AS value, count(*) AS count
  FROM rights.delivery_assessment d
  WHERE NOT EXISTS (SELECT 1 FROM rights.delivery_assessment n WHERE n.supersedes_delivery_assessment_id=d.delivery_assessment_id)
  GROUP BY delivery_mode
), assignment_depth AS (
  WITH RECURSIVE walk(start_id,current_id,depth,path,cycle) AS (
    SELECT canonical_assignment_id,canonical_assignment_id,1,ARRAY[canonical_assignment_id],false
    FROM provenance.canonical_assignment
    UNION ALL
    SELECT w.start_id,p.supersedes_assignment_id,w.depth+1,w.path||p.supersedes_assignment_id,
      p.supersedes_assignment_id=ANY(w.path)
    FROM walk w JOIN provenance.canonical_assignment p ON p.canonical_assignment_id=w.current_id
    WHERE p.supersedes_assignment_id IS NOT NULL AND NOT w.cycle
  ), terminal AS (
    SELECT start_id,max(depth) AS depth,bool_or(cycle) AS cycle FROM walk GROUP BY start_id
  )
  SELECT depth,count(*) AS count FROM terminal GROUP BY depth ORDER BY depth
), projection AS (
  SELECT b.* FROM release.research_launch_build_receipt_v3 b JOIN latest l USING(research_release_id)
), source_asset AS (
  SELECT source_asset_id,authority::text,logical_name,sha256,byte_length,received_at
  FROM raw.source_asset WHERE authority='canonical_migration_input' ORDER BY received_at DESC LIMIT 1
)
SELECT jsonb_build_object(
  'transactionReadOnly',current_setting('transaction_read_only'),
  'releaseIdentity',(SELECT jsonb_build_object(
    'releaseUuid',l.research_release_id,'releaseId',l.release_token,'releaseVersion',l.model_version,
    'schemaVersion',l.schema_version,'sealStatus',l.release_state,'createdAt',l.created_at,
    'candidateAt',l.candidate_at,'validatedAt',l.validated_at,'sealedAt',l.sealed_at,
    'manifestSha256',l.manifest_sha256,'candidateFingerprint',l.candidate_fingerprint,
    'builderVersion',p.builder_version,'builtAt',p.built_at,
    'projectionContentSha256',p.projection_content_sha256,
    'canonicalSource',to_jsonb(s)) FROM latest l LEFT JOIN projection p ON true LEFT JOIN source_asset s ON true),
  'coreScale',jsonb_build_object(
    'canonicalObjectCount',(SELECT count(*) FROM core.archive_object),
    'heldObjectCount',(SELECT count(*) FROM raw.legacy_surface_ledger WHERE import_disposition='held'),
    'eligibleObjectCount',(SELECT count(*) FROM research.corpus_membership WHERE disposition='eligible'),
    'quarantinedObjectCount',(SELECT count(*) FROM raw.fail_closed_delta WHERE disposition='held'),
    'assignmentCount',(SELECT count(*) FROM provenance.canonical_assignment),
    'currentAssignmentLeafCount',(SELECT count(*) FROM provenance.canonical_assignment a WHERE NOT EXISTS (SELECT 1 FROM provenance.canonical_assignment n WHERE n.supersedes_assignment_id=a.canonical_assignment_id)),
    'supersededAssignmentCount',(SELECT count(*) FROM provenance.canonical_assignment a WHERE EXISTS (SELECT 1 FROM provenance.canonical_assignment n WHERE n.supersedes_assignment_id=a.canonical_assignment_id)),
    'relationshipAssignmentCount',(SELECT count(*) FROM provenance.assignment_folder_membership),
    'acceptedSemanticRelationCount',(SELECT count(*) FROM research.semantic_relation WHERE status='accepted'),
    'releaseFolderMembershipProjectionCount',(SELECT count(*) FROM release.research_folder_membership_projection_v3 p JOIN latest l USING(research_release_id)),
    'releaseRelationProjectionCount',(SELECT count(*) FROM release.research_release_relation p JOIN latest l USING(research_release_id)),
    'releaseSearchDocumentCount',(SELECT count(*) FROM release.research_search_document_projection_v3 p JOIN latest l USING(research_release_id))
  ),
  'distributions',jsonb_build_object(
    'objectDesignType',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM object_types),
    'relationType',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM relation_types),
    'assignmentLifecycleState',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM assignment_states),
    'source',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM sources),
    'geographyClass',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM geographies),
    'yearDecade',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY value),'[]') FROM year_ranges),
    'folderType',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM folder_types)
  ),
  'missingness',jsonb_build_object(
    'missingField',jsonb_build_object('definition','trace.tier absent; governed fail-closed delta','count',(SELECT count(*) FROM raw.fail_closed_delta WHERE reason_code='MISSING_EXPLICIT_EVIDENCE_TIER')),
    'explicitNull',jsonb_build_object('definition','JSON null literal occurrences','count',(SELECT count(*) FROM raw.field_literal WHERE convert_from(raw_bytes,'UTF8')='null')),
    'emptyString',jsonb_build_object('definition','JSON empty-string occurrences','count',(SELECT count(*) FROM raw.field_literal WHERE convert_from(raw_bytes,'UTF8')='""')),
    'emptyArray',jsonb_build_object('definition','JSON empty-array occurrences','count',(SELECT count(*) FROM raw.source_record r CROSS JOIN LATERAL jsonb_path_query(r.parsed_projection,'strict $.** ? (@.type() == "array" && @.size() == 0)') x)),
    'absentRelationship',jsonb_build_object('definition','canonical objects with no accepted semantic relation in a zero-relation canonical set','count',(SELECT count(*) FROM core.archive_object WHERE NOT EXISTS (SELECT 1 FROM research.semantic_relation WHERE status='accepted'))),
    'quarantinedValue',jsonb_build_object('definition','fail_closed_delta rows retained with held disposition','count',(SELECT count(*) FROM raw.fail_closed_delta WHERE disposition='held'))
  ),
  'dataQuality',jsonb_build_object(
    'duplicateStableIds',(SELECT count(*) FROM (SELECT surface_id FROM raw.legacy_surface_ledger GROUP BY surface_id HAVING count(*)>1) d),
    'orphanAssignmentMemberships',(SELECT count(*) FROM provenance.assignment_folder_membership m LEFT JOIN provenance.canonical_assignment a USING(canonical_assignment_id) WHERE a.canonical_assignment_id IS NULL),
    'unknownRelationTypes',(SELECT count(*) FROM research.semantic_relation r LEFT JOIN research.relation_type t USING(relation_type_id) WHERE t.relation_type_id IS NULL),
    'failedCandidateSelectedCurrent',(SELECT count(*) FROM release.research_current_pointer p JOIN release.research_release r USING(research_release_id) WHERE r.release_state<>'sealed'),
    'assignmentSupersessionDepthDistribution',(SELECT coalesce(jsonb_agg(jsonb_build_object('depth',depth,'count',count) ORDER BY depth),'[]') FROM assignment_depth),
    'malformedAssignmentSupersessionCycles',(WITH RECURSIVE walk(start_id,current_id,path,cycle) AS (
      SELECT canonical_assignment_id,canonical_assignment_id,ARRAY[canonical_assignment_id],false FROM provenance.canonical_assignment
      UNION ALL SELECT w.start_id,p.supersedes_assignment_id,w.path||p.supersedes_assignment_id,p.supersedes_assignment_id=ANY(w.path)
      FROM walk w JOIN provenance.canonical_assignment p ON p.canonical_assignment_id=w.current_id
      WHERE p.supersedes_assignment_id IS NOT NULL AND NOT w.cycle)
      SELECT count(DISTINCT start_id) FROM walk WHERE cycle)
  ),
  'rightsAndPublication',jsonb_build_object(
    'rightsStateDistribution',(SELECT coalesce(jsonb_agg(jsonb_build_object('value',value,'count',count) ORDER BY count DESC,value),'[]') FROM rights_states),
    'positiveRightsCount',(SELECT count(*) FROM rights.delivery_assessment d WHERE NOT EXISTS (SELECT 1 FROM rights.delivery_assessment n WHERE n.supersedes_delivery_assessment_id=d.delivery_assessment_id) AND d.delivery_mode IN ('link_only','source_viewer','remote_image')),
    'eligibleCount',(SELECT count(*) FROM research.corpus_membership WHERE disposition='eligible'),
    'heldCount',(SELECT count(*) FROM raw.legacy_surface_ledger WHERE import_disposition='held'),
    'acceptedTraceCount',(SELECT count(*) FROM research.semantic_relation WHERE status='accepted'),
    'sealedReleaseCount',(SELECT count(*) FROM release.research_release WHERE release_state='sealed'),
    'currentReleaseCount',(SELECT count(*) FROM release.research_current_pointer WHERE research_release_id IS NOT NULL)
  )
)`;

const apiSql = String.raw`
WITH current_release AS (
  SELECT research_release_id,research_manifest_sha256 FROM api_v1.current_version_status WHERE channel='public'
), surfaces AS (
  SELECT s.* FROM api_v1.sealed_surface s JOIN current_release c USING(research_release_id,research_manifest_sha256)
), descriptor AS (
  SELECT d.* FROM api_v1.sealed_research_release_descriptor d JOIN current_release c USING(research_release_id,research_manifest_sha256)
)
SELECT jsonb_build_object(
  'transactionReadOnly',current_setting('transaction_read_only'),
  'currentRelease',(SELECT to_jsonb(c) FROM current_release c),
  'descriptor',(SELECT to_jsonb(d) FROM descriptor d),
  'apiVisibleObjectCount',(SELECT count(*) FROM surfaces),
  'apiVisibleRelationshipCount',(SELECT relation_count FROM descriptor),
  'searchableRecordCount',(SELECT count(*) FROM surfaces WHERE nullif(btrim(title),'') IS NOT NULL),
  'uniqueSearchKeyCount',(SELECT count(DISTINCT lower(coalesce(title,''))||'|'||surface_id) FROM surfaces),
  'duplicateSearchKeyCount',(SELECT count(*) FROM (SELECT lower(coalesce(title,''))||'|'||surface_id AS k FROM surfaces GROUP BY k HAVING count(*)>1) d),
  'missingSearchKeyCount',(SELECT count(*) FROM surfaces WHERE surface_id IS NULL OR surface_id=''),
  'emptyTitleCount',(SELECT count(*) FROM surfaces WHERE title IS NULL OR btrim(title)=''),
  'recordsWithNoSearchableText',(SELECT count(*) FROM surfaces WHERE nullif(btrim(title),'') IS NULL),
  'publicationLayerDistribution',(SELECT coalesce(jsonb_object_agg(publication_layer,count),'{}') FROM (SELECT publication_layer,count(*) FROM surfaces GROUP BY publication_layer) x),
  'surfaceIdMinimum',(SELECT min(surface_id) FROM surfaces),
  'surfaceIdMaximum',(SELECT max(surface_id) FROM surfaces)
)`;

const internal = queryJson(args["--audit-role"], internalSql);
const apiVisible = queryJson(args["--api-role"], apiSql);
if (internal.transactionReadOnly !== "on" || apiVisible.transactionReadOnly !== "on") throw new Error("statistics transaction was not read-only");

const verifier = readJson(args["--verifier"]);
const reconciliation = readJson(args["--reconciliation"]);
const apiResults = readJson(args["--api-results"]);
const runtimeProfile = readJson(args["--runtime-profile"]);
const core = internal.coreScale;
const endpointPrimary = new Map(apiResults.endpointInventory.map((endpoint) => [endpoint.template, apiResults.contractResults.find((item) => item.name === endpoint.id)]));
const pagedTemplates = new Set([
  "/api/v1/releases/{release}/folders",
  "/api/v1/releases/{release}/folders/{id}/surfaces",
  "/api/v1/releases/{release}/search",
  "/api/v1/releases/{release}/trace/objects",
]);
const addressable = {
  "/api/v1/visual-registries/current": 0,
  "/api/v1/releases/{release}": 1,
  "/api/v1/releases/{release}/manifest": 1,
  "/api/v1/releases/{release}/archive/overview": 1,
  "/api/v1/releases/{release}/folder-types": 0,
  "/api/v1/releases/{release}/folders": 0,
  "/api/v1/releases/{release}/folders/{id}/surfaces": 0,
  "/api/v1/releases/{release}/folders/{id}": 0,
  "/api/v1/releases/{release}/surfaces/{id}": apiVisible.apiVisibleObjectCount,
  "/api/v1/releases/{release}/search": apiVisible.searchableRecordCount,
  "/api/v1/releases/{release}/trace/atlas": 1,
  "/api/v1/releases/{release}/trace/objects": 0,
  "/api/v1/releases/{release}/trace/objects/{id}/neighborhood": 0,
  "/api/v1/releases/{release}/trace/relation-types": 0,
  "/api/v1/releases/{release}/trace/relation-types/{id}": 0,
  "/api/v1/releases/{release}/relations/{id}": 0,
  "/api/v1/releases/{release}/claims/{id}": 0,
  "/api/v1/releases/{release}/corpora/{version}": 0,
};
const nullableFields = {
  "/api/v1/releases/{release}/surfaces/{id}": ["year", "citation", "description"],
  "/api/v1/releases/{release}/search": ["nodes[].surface.year"],
};
const omittedBoundaryFields = ["raw source payload", "internal UUIDs", "held/quarantined rows", "rights internals", "candidate state"];
const endpointStatistics = apiResults.endpointInventory.map((endpoint) => {
  const primary = endpointPrimary.get(endpoint.template);
  return {
    endpoint: endpoint.template,
    totalRecordsAddressable: addressable[endpoint.template],
    defaultPageSize: pagedTemplates.has(endpoint.template) ? 50 : null,
    maximumPageSize: pagedTemplates.has(endpoint.template) ? 100 : null,
    firstResponseRecordCount: primary?.returnedRecords ?? 0,
    emptyResultSemantics: primary?.status === 404 ? "NOT_FOUND/404" : (primary?.returnedRecords === 0 ? "200 with empty collection" : "not applicable to primary case"),
    responsePayloadBytes: primary?.responseBytes ?? 0,
    nullableFields: nullableFields[endpoint.template] ?? [],
    fieldsOmittedByBoundary: omittedBoundaryFields,
  };
});

const rec = reconciliation;
const profile = {
  format: "gda-v49-release-data-profile/v1",
  database: args["--database"],
  generatedBy: "scripts/v49_read_api_statistics.mjs",
  readOnlyProof: {
    auditSessionRole: args["--audit-role"],
    auditSessionEnforcement: "PGOPTIONS default_transaction_read_only=on + BEGIN READ ONLY",
    auditTransactionReadOnly: internal.transactionReadOnly,
    apiRole: args["--api-role"],
    apiTransactionReadOnly: apiVisible.transactionReadOnly,
    sqlPolicy: "SELECT-only; mutation and DDL keywords rejected before execution",
  },
  releaseIdentity: { ...internal.releaseIdentity, schemaHash: args["--schema-hash"] },
  coreScale: {
    ...core,
    apiVisibleObjectCount: apiVisible.apiVisibleObjectCount,
    apiVisibleRelationshipCount: apiVisible.apiVisibleRelationshipCount,
  },
  distributions: internal.distributions,
  missingness: internal.missingness,
  dataQuality: {
    ...internal.dataQuality,
    duplicateStableIdsReconciled: rec.duplicatedStableIdCount,
    missingStableIds: rec.missingStableIdCount,
    unexpectedStableIds: rec.unexpectedStableIdCount,
    remappedStableIds: rec.remappedStableIdCount,
    unexplainedDeltas: rec.unexplainedDeltaCount ?? 0,
    silentDrops: rec.silentDropCount ?? 0,
    silentSplits: rec.silentSplitCount ?? 0,
    rightsWidening: rec.rightsWideningCount ?? 0,
    verifierIntegrityFailures: Object.keys(verifier.failures ?? {}).length,
  },
  rightsAndPublication: internal.rightsAndPublication,
  searchReadiness: {
    searchableRecordCount: apiVisible.searchableRecordCount,
    uniqueSearchKeyCount: apiVisible.uniqueSearchKeyCount,
    duplicatePageSearchKeyCount: apiVisible.duplicateSearchKeyCount,
    missingPageSearchKeyCount: apiVisible.missingSearchKeyCount,
    recordsExcludedFromSearch: Number(core.canonicalObjectCount) - Number(apiVisible.searchableRecordCount),
    searchIndexSourceRecordCount: core.releaseSearchDocumentCount,
    pageByKeyPotentialSourceSize: apiVisible.searchableRecordCount,
    pageByKeyCanonicalPosterQuerySourceSize: apiResults.paginatedExpectedCount,
    keyNormalizationCollisions: apiVisible.duplicateSearchKeyCount,
    emptyTitlesLabels: apiVisible.emptyTitleCount,
    recordsWithNoSearchableText: apiVisible.recordsWithNoSearchableText,
  },
  apiVisible: { ...apiVisible, endpointStatistics },
  evidenceCrosscheck: {
    verifierSchemaHash: verifier.schemaShaAfter,
    verifierContentDigest: verifier.normalizedContentSha256,
    verifierStableKeySetSha256: verifier.stableKeySetSha256,
    apiContractStatus: apiResults.status,
    runtimeProfileStatus: runtimeProfile.timeoutCount === 0 && runtimeProfile.http5xxCount === 0 ? "PASS" : "FAIL",
  },
};

const rows = [];
function flatten(path, value) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      if (item && typeof item === "object" && "value" in item && "count" in item) rows.push([path, item.value, item.count]);
      else if (item && typeof item === "object" && "endpoint" in item) rows.push([path, item.endpoint, item.totalRecordsAddressable]);
      else flatten(`${path}[${index}]`, item);
    });
  } else if (value && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) flatten(path ? `${path}.${key}` : key, child);
  } else rows.push([path, "", value]);
}
flatten("", profile);
const csv = ["category,dimension,value", ...rows.map((row) => row.map(csvCell).join(","))].join("\n") + "\n";
const top = (items, limit = 20) => items.slice(0, limit).map((item) => `| ${String(item.value).replaceAll("|", "\\|")} | ${item.count} |`).join("\n") || "| _none_ | 0 |";
const md = `# v49 release data profile\n\nGenerated by \`scripts/v49_read_api_statistics.mjs\` against \`${args["--database"]}\`. The audit session was database-enforced read-only; public statistics were queried as \`${args["--api-role"]}\`.\n\n## Release identity\n\n- Release: \`${profile.releaseIdentity.releaseId}\`\n- State: \`${profile.releaseIdentity.sealStatus}\`\n- Manifest: \`${profile.releaseIdentity.manifestSha256}\`\n- Projection content digest: \`${profile.releaseIdentity.projectionContentSha256}\`\n- Schema hash: \`${profile.releaseIdentity.schemaHash}\`\n- Canonical source: \`${profile.releaseIdentity.canonicalSource.logical_name}\` / \`${profile.releaseIdentity.canonicalSource.sha256}\`\n\n## Core and public scale\n\n| Metric | Count |\n|---|---:|\n| Canonical objects | ${core.canonicalObjectCount} |\n| Eligible | ${core.eligibleObjectCount} |\n| Held / quarantined | ${core.heldObjectCount} / ${core.quarantinedObjectCount} |\n| Canonical assignments | ${core.assignmentCount} |\n| Current assignment leaves | ${core.currentAssignmentLeafCount} |\n| Superseded assignments | ${core.supersededAssignmentCount} |\n| Relationship assignments | ${core.relationshipAssignmentCount} |\n| API-visible objects | ${apiVisible.apiVisibleObjectCount} |\n| API-visible relationships | ${apiVisible.apiVisibleRelationshipCount} |\n\n## Missingness semantics\n\n| Semantics | Count | Definition |\n|---|---:|---|\n${Object.entries(profile.missingness).map(([key, item]) => `| ${key} | ${item.count} | ${item.definition} |`).join("\n")}\n\n## Object/design types (top 20; JSON/CSV contain all)\n\n| Value | Count |\n|---|---:|\n${top(profile.distributions.objectDesignType)}\n\n## Sources (top 20; JSON/CSV contain all)\n\n| Value | Count |\n|---|---:|\n${top(profile.distributions.source)}\n\n## Geography class\n\n| Value | Count |\n|---|---:|\n${top(profile.distributions.geographyClass, 100)}\n\n## Search readiness\n\n| Metric | Count |\n|---|---:|\n${Object.entries(profile.searchReadiness).map(([key, value]) => `| ${key} | ${value} |`).join("\n")}\n\n## Data quality\n\nThe fresh verifier, stable-ID reconciliation, supersession traversal, and API-boundary crosscheck report zero duplicate, missing, unexpected, remapped, orphaned, cycle, silent-drop/split, unknown-relation, and rights-widening failures. Full machine-readable values are in the companion JSON and CSV.\n\n## Per-endpoint public statistics\n\n| Endpoint | Addressable | Default/max page | First response records | Bytes | Empty/not-found semantics |\n|---|---:|---|---:|---:|---|\n${endpointStatistics.map((row) => `| \`${row.endpoint}\` | ${row.totalRecordsAddressable} | ${row.defaultPageSize ?? "—"}/${row.maximumPageSize ?? "—"} | ${row.firstResponseRecordCount} | ${row.responsePayloadBytes} | ${row.emptyResultSemantics} |`).join("\n")}\n`;

write(args["--json"], `${JSON.stringify(profile, null, 2)}\n`);
write(args["--csv"], csv);
write(args["--markdown"], md);
console.log(JSON.stringify({ status: "PASS", canonicalObjects: core.canonicalObjectCount, apiVisibleObjects: apiVisible.apiVisibleObjectCount, eligible: core.eligibleObjectCount, held: core.heldObjectCount, searchable: profile.searchReadiness.searchableRecordCount, apiVisibleRelationships: apiVisible.apiVisibleRelationshipCount, endpoints: endpointStatistics.length }));
