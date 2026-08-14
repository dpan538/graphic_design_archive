#!/usr/bin/env python3
"""Read-only parity and deterministic-content verifier for Phase 2B."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
OWNER_ROLE = "gda_v49_phase2a_schema_owner"
API_ROLE = "gda_v49_phase2a_api_reader"


class VerifyError(RuntimeError):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def run(command: list[str], env: dict[str, str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    if result.returncode:
        raise VerifyError("COMMAND_FAILED:\n" + result.stdout[-2000:] + result.stderr[-4000:])
    return result.stdout


def environment(args: argparse.Namespace, user: str) -> dict[str, str]:
    result = os.environ.copy()
    result.update({"PGHOST": args.pg_host, "PGPORT": str(args.pg_port), "PGDATABASE": args.database, "PGUSER": user})
    return result


def query(args: argparse.Namespace, sql: str, *, user: str | None = None) -> str:
    return run(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], environment(args, user or args.admin_user)).strip()


def stream_sql_hash(args: argparse.Namespace, sql: str) -> tuple[str, int]:
    """Hash deterministic ordered SQL rows without materialising them in RAM.

    The replay includes a durable raw-literal row for every scalar occurrence,
    so a Python list of all row texts would make verification memory-sensitive.
    ``COPY ... TO STDOUT`` emits the ordered textual rows directly to a SHA-256
    stream. The query itself fixes UTC where timestamps participate, and JSONB
    rendering is deterministic within the pinned PostgreSQL major version.
    """
    process = subprocess.Popen(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment(args, args.admin_user),
    )
    assert process.stdout is not None
    digest = hashlib.sha256()
    rows = 0
    while True:
        chunk = process.stdout.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        rows += chunk.count(b"\n")
    return_code = process.wait()
    assert process.stderr is not None
    stderr = process.stderr.read().decode("utf-8", "replace")
    if return_code:
        raise VerifyError("ORDERED_HASH_QUERY_FAILED:\n" + stderr[-4000:])
    return digest.hexdigest(), rows


def schema_hash(args: argparse.Namespace) -> str:
    return run([str(ROOT / "database/scripts/schema_hash.sh")], environment(args, args.admin_user)).strip()


def count_vector(args: argparse.Namespace) -> dict[str, int]:
    tables = [
        ("raw.source_asset", "raw_source_asset"), ("raw.mapping_version", "raw_mapping_version"),
        ("raw.migration_batch", "raw_migration_batch"), ("raw.source_record", "raw_source_record"),
        ("raw.field_literal", "raw_field_literal"),
        ("raw.legacy_surface_ledger", "raw_legacy_surface_ledger"), ("raw.fail_closed_delta", "raw_fail_closed_delta"),
        ("core.entity", "core_entity"), ("core.archive_object", "core_archive_object"),
        ("core.legacy_identity", "core_legacy_identity"), ("core.legacy_identity_resolution", "core_legacy_identity_resolution"),
        ("provenance.object_source_record", "provenance_object_source_record"),
        ("provenance.canonical_assignment", "provenance_canonical_assignment"),
        ("provenance.assignment_folder_membership", "provenance_assignment_folder_membership"),
        ("research.corpus", "research_corpus"), ("research.corpus_version", "research_corpus_version"),
        ("research.corpus_membership", "research_corpus_membership"), ("research.trace_node", "research_trace_node"),
        ("research.folder", "research_folder"),
        ("research.object_trace_node", "research_object_trace_node"), ("research.semantic_relation", "research_semantic_relation"),
        ("rights.external_visual_reference", "rights_external_visual_reference"),
        ("rights.object_visual_reference", "rights_object_visual_reference"),
        ("rights.visual_locator", "rights_visual_locator"),
        ("rights.rights_assessment", "rights_rights_assessment"), ("rights.delivery_assessment", "rights_delivery_assessment"),
        ("rights.legacy_visual_surface_disposition", "rights_legacy_visual_surface_disposition"),
        ("rights.legacy_visual_surface_classification", "rights_legacy_visual_surface_classification"),
        ("release.research_release", "release_research_release"), ("release.visual_registry_release", "release_visual_registry_release"),
        ("release.research_current_pointer", "release_research_current_pointer"), ("release.visual_current_pointer", "release_visual_current_pointer"),
        ("release.trace_projection_edge", "release_trace_projection_edge"),
    ]
    unions = " UNION ALL ".join(
        f"SELECT '{label}' AS k, count(*)::bigint AS v FROM {table}" for table, label in tables
    )
    payload = query(args, f"SET ROLE {OWNER_ROLE}; SELECT jsonb_object_agg(k, v ORDER BY k)::text FROM ({unions}) q;")
    return {key: int(value) for key, value in json.loads(payload).items()}


def metric_query(args: argparse.Namespace) -> dict[str, int]:
    sql = f"""
SET ROLE {OWNER_ROLE};
SELECT jsonb_build_object(
  'legacyInputSurfaces', (SELECT count(*) FROM raw.legacy_surface_ledger),
  'operationalObjects', (SELECT count(*) FROM core.archive_object),
  'rawSourceRecords', (SELECT count(*) FROM raw.source_record),
  'objectSourceSeedLinks', (SELECT count(*) FROM provenance.object_source_record WHERE source_role='seed_description'),
  'rawFieldLiterals', (SELECT count(*) FROM raw.field_literal),
  'folders', (SELECT count(*) FROM research.folder),
  'folderMembershipAssignments', (SELECT count(*) FROM provenance.assignment_folder_membership),
  'sourceVerified', (SELECT count(*) FROM raw.legacy_surface_ledger WHERE reason_code='EXPLICIT_SOURCE_VERIFIED_TIER'),
  'metadataSupportedHeld', (SELECT count(*) FROM raw.legacy_surface_ledger WHERE reason_code='METADATA_SUPPORTED_BELOW_STRICT_EVIDENCE_THRESHOLD'),
  'missingTraceTierHeld', (SELECT count(*) FROM raw.legacy_surface_ledger WHERE reason_code='MISSING_EXPLICIT_EVIDENCE_TIER'),
  'researchEligibleObjects', (SELECT count(*) FROM research.corpus_membership WHERE disposition='eligible'),
  'heldObjects', (SELECT count(*) FROM raw.fail_closed_delta WHERE disposition='held'),
  'rejectedObjects', (SELECT count(*) FROM raw.legacy_surface_ledger WHERE import_disposition='rejected'),
  'acceptedTraceRelations', (SELECT count(*) FROM research.semantic_relation WHERE status='accepted'),
  'semanticRelationRows', (SELECT count(*) FROM research.semantic_relation),
  'legacyProjectionFactRows', (SELECT count(*) FROM research.legacy_projection_fact),
  'traceEligibleObjects', (SELECT count(*) FROM research.object_relation_membership),
  'traceWorkingTreeRows', (SELECT count(*) FROM research.trace_tree),
  'traceWorkingBranchRows', (SELECT count(*) FROM research.trace_branch),
  'traceWorkingNodePlacementRows', (SELECT count(*) FROM research.trace_node_tree_membership),
  'traceWorkingAssignmentRows', (SELECT count(*) FROM provenance.assignment_object_tree_membership),
  'traceRootNodes', (SELECT count(*) FROM research.trace_node),
  'visualBundles', (SELECT count(*) FROM rights.legacy_visual_surface_disposition),
  'bundlesWithReference', (SELECT count(*) FROM rights.legacy_visual_surface_disposition WHERE visual_reference_count > 0),
  'bundlesWithoutReference', (SELECT count(*) FROM rights.legacy_visual_surface_disposition WHERE visual_reference_count = 0),
  'locatorOccurrences', (SELECT count(*) FROM rights.visual_locator),
  'unclassifiedVisualReference', (SELECT count(*) FROM rights.legacy_visual_surface_disposition d WHERE NOT EXISTS (SELECT 1 FROM rights.legacy_visual_surface_classification c WHERE c.legacy_surface_ledger_id=d.legacy_surface_ledger_id)),
  'positiveRights', (SELECT count(*) FROM rights.rights_assessment WHERE assessed_state='permitted'),
  'remoteImageDecisions', (SELECT count(*) FROM rights.delivery_assessment WHERE delivery_mode='remote_image'),
  'rightsObservations', (SELECT count(*) FROM rights.rights_observation),
  'rightsAssessments', (SELECT count(*) FROM rights.rights_assessment),
  'policyEvaluations', (SELECT count(*) FROM rights.provider_policy_evaluation),
  'citationOnlyDecisions', (SELECT count(*) FROM rights.delivery_assessment WHERE delivery_mode='citation_only'),
  'publicPixelLocators', (SELECT count(*) FROM rights.visual_locator WHERE visibility='public_candidate'),
  'acceptedSemanticRelations', (SELECT count(*) FROM research.semantic_relation WHERE status='accepted'),
  'traceProjectionEdges', (SELECT count(*) FROM release.trace_projection_edge),
  'traceProjectionNodes', (SELECT count(*) FROM release.trace_projection_node),
  'traceProjectionTrees', (SELECT count(*) FROM release.trace_tree_projection),
  'traceProjectionBranches', (SELECT count(*) FROM release.trace_branch_projection),
  'traceProjectionNodePlacements', (SELECT count(*) FROM release.trace_node_tree_placement),
  'traceProjectionEdgePlacements', (SELECT count(*) FROM release.trace_edge_tree_placement),
  'currentPointers', (SELECT count(*) FROM release.research_current_pointer) + (SELECT count(*) FROM release.visual_current_pointer),
  'sealedReleases', (SELECT count(*) FROM release.research_release WHERE release_state='sealed') + (SELECT count(*) FROM release.visual_registry_release WHERE release_state='sealed')
)::text;
"""
    return {key: int(value) for key, value in json.loads(query(args, sql)).items()}


def stable_key_hash(args: argparse.Namespace) -> tuple[str, int]:
    sql = f"""
SET ROLE {OWNER_ROLE};
COPY (
SELECT row_text FROM (
  SELECT 'source_asset|' || source_asset_id::text AS row_text FROM raw.source_asset
  UNION ALL
  SELECT 'object|' || archive_object_id::text AS row_text FROM core.archive_object
  UNION ALL SELECT 'source|' || source_record_id::text AS row_text FROM raw.source_record
  UNION ALL SELECT 'field_literal|' || field_literal_id::text AS row_text FROM raw.field_literal
  UNION ALL SELECT 'ledger|' || legacy_surface_ledger_id::text AS row_text FROM raw.legacy_surface_ledger
  UNION ALL SELECT 'membership|' || corpus_version_id::text || '|' || archive_object_id::text FROM research.corpus_membership
  UNION ALL SELECT 'held|' || fail_closed_delta_id::text FROM raw.fail_closed_delta
  UNION ALL SELECT 'folder|' || folder_id::text AS row_text FROM research.folder
  UNION ALL SELECT 'folder_membership|' || canonical_assignment_id::text AS row_text FROM provenance.assignment_folder_membership
  UNION ALL SELECT 'trace_root|' || archive_object_id::text || '|' || trace_node_id::text || '|' || node_role FROM research.object_trace_node
  UNION ALL SELECT 'visual_ref|' || external_visual_reference_id::text AS row_text FROM rights.external_visual_reference
  UNION ALL SELECT 'visual_locator|' || visual_locator_id::text AS row_text FROM rights.visual_locator
  UNION ALL SELECT 'delivery|' || delivery_assessment_id::text AS row_text FROM rights.delivery_assessment
) stable ORDER BY row_text
) TO STDOUT;
"""
    return stream_sql_hash(args, sql)


def semantic_content_hash(args: argparse.Namespace) -> tuple[str, int]:
    """All Phase 2B population semantics in a stable, timezone-normalized form."""
    sql = f"""
SET TIME ZONE 'UTC';
SET ROLE {OWNER_ROLE};
COPY (
SELECT row_text FROM (
  SELECT 'asset|' || jsonb_build_object('id',source_asset_id,'authority',authority,'logicalName',logical_name,'sha256',sha256,'bytes',byte_length,'mediaType',media_type)::text AS row_text FROM raw.source_asset
  UNION ALL SELECT 'mapping|' || jsonb_build_object('id',mapping_version_id,'token',version_token,'specificationSha256',specification_sha256,'parserVersion',parser_version,'delimiterPolicy',delimiter_policy)::text FROM raw.mapping_version
  UNION ALL SELECT 'batch|' || jsonb_build_object('id',migration_batch_id,'token',batch_token,'inputAsset',canonical_input_asset_id,'mappingVersion',mapping_version_id,'inputSha256',input_sha256)::text FROM raw.migration_batch
  UNION ALL SELECT 'source|' || jsonb_build_object('id',source_record_id,'asset',source_asset_id,'ordinal',record_ordinal,'legacyId',legacy_source_record_id,'rawFingerprint',raw_fingerprint,'projection',parsed_projection,'parseError',parse_error_code)::text FROM raw.source_record
  UNION ALL SELECT 'entity|' || jsonb_build_object('id',entity_id,'kind',entity_kind,'state',lifecycle_state)::text FROM core.entity
  UNION ALL SELECT 'object|' || jsonb_build_object('id',archive_object_id,'urn',object_urn,'semanticsVersion',operational_semantics_version,'label',preferred_label,'ledger',created_from_surface_ledger_id)::text FROM core.archive_object
  UNION ALL SELECT 'ledger|' || jsonb_build_object('id',legacy_surface_ledger_id,'batch',migration_batch_id,'source',source_record_id,'asset',canonical_input_asset_id,'ordinal',input_ordinal,'surfaceId',surface_id,'legacySourceId',legacy_source_record_id,'fingerprint',source_fingerprint,'disposition',import_disposition,'object',archive_object_id,'reason',reason_code)::text FROM raw.legacy_surface_ledger
  UNION ALL SELECT 'sourceLink|' || jsonb_build_object('object',archive_object_id,'source',source_record_id,'role',source_role)::text FROM provenance.object_source_record
  UNION ALL SELECT 'fieldLiteral|' || jsonb_build_object('id',field_literal_id,'source',source_record_id,'pointer',json_pointer,'ordinal',occurrence_ordinal,'rawBytesSha256',encode(sha256(raw_bytes),'hex'),'rawText',raw_text)::text FROM raw.field_literal
  UNION ALL SELECT 'legacyIdentity|' || jsonb_build_object('id',legacy_identity_id,'kind',identity_kind,'namespace',namespace,'legacyId',legacy_id)::text FROM core.legacy_identity
  UNION ALL SELECT 'traceNode|' || jsonb_build_object('id',trace_node_id,'key',canonical_key,'label',label,'entity',entity_id,'type',node_type,'evidence',evidence_item_id)::text FROM research.trace_node
  UNION ALL SELECT 'objectTrace|' || jsonb_build_object('object',archive_object_id,'node',trace_node_id,'role',node_role)::text FROM research.object_trace_node
  UNION ALL SELECT 'corpus|' || jsonb_build_object('id',corpus_id,'token',corpus_token,'label',label)::text FROM research.corpus
  UNION ALL SELECT 'corpusVersion|' || jsonb_build_object('id',corpus_version_id,'corpus',corpus_id,'token',version_token,'policyVersion',policy_version,'policySha256',policy_sha256,'frame',population_frame)::text FROM research.corpus_version
  UNION ALL SELECT 'folder|' || jsonb_build_object('id',folder_id,'token',folder_token,'label',label)::text FROM research.folder
  UNION ALL SELECT 'folderMembership|' || jsonb_build_object('assignment',canonical_assignment_id,'folder',folder_id,'object',archive_object_id,'role',membership_role,'ordinal',member_ordinal)::text FROM provenance.assignment_folder_membership
  UNION ALL SELECT 'membership|' || jsonb_build_object('corpusVersion',corpus_version_id,'object',archive_object_id,'disposition',disposition,'reason',reason_code,'evidence',evidence_item_id,'decidedBy',decided_by,'decidedAtUs',(extract(epoch FROM decided_at)*1000000)::bigint)::text FROM research.corpus_membership
  UNION ALL SELECT 'held|' || jsonb_build_object('id',fail_closed_delta_id,'batch',migration_batch_id,'source',source_record_id,'expected',expected_classification,'actual',actual_literal,'reason',reason_code,'disposition',disposition)::text FROM raw.fail_closed_delta
  UNION ALL SELECT 'visualReference|' || jsonb_build_object('id',external_visual_reference_id,'asset',source_asset_id,'source',source_record_id,'pointer',source_field_or_json_pointer,'ordinal',source_occurrence_ordinal,'providerObject',provider_object_id,'fingerprint',reference_fingerprint)::text FROM rights.external_visual_reference
  UNION ALL SELECT 'visualBridge|' || jsonb_build_object('id',object_visual_reference_id,'object',archive_object_id,'reference',external_visual_reference_id,'role',reference_role,'ordinal',ordinal,'acceptance',acceptance_state,'evidence',evidence_item_id)::text FROM rights.object_visual_reference
  UNION ALL SELECT 'locator|' || jsonb_build_object('id',visual_locator_id,'reference',external_visual_reference_id,'role',locator_role,'asset',source_asset_id,'source',source_record_id,'pointer',source_field_or_json_pointer,'ordinal',occurrence_ordinal,'visibility',visibility,'rawLocator',raw_locator,'fingerprint',locator_fingerprint,'evidence',source_evidence_item_id)::text FROM rights.visual_locator
  UNION ALL SELECT 'rightsObservation|' || jsonb_build_object('id',rights_observation_id,'subjectKind',subject_kind,'state',evidence_state,'evidence',evidence_item_id,'wording',observed_wording,'subject',(SELECT external_visual_reference_id FROM rights.rights_observation_visual_reference x WHERE x.rights_observation_id=o.rights_observation_id))::text FROM rights.rights_observation o
  UNION ALL SELECT 'rightsAssessment|' || jsonb_build_object('id',rights_assessment_id,'subjectKind',subject_kind,'state',assessed_state,'reviewer',reviewer_actor,'rationale',rationale,'assessedAtUs',(extract(epoch FROM assessed_at)*1000000)::bigint,'subject',(SELECT external_visual_reference_id FROM rights.rights_assessment_visual_reference x WHERE x.rights_assessment_id=a.rights_assessment_id))::text FROM rights.rights_assessment a
  UNION ALL SELECT 'assessmentObservation|' || jsonb_build_object('assessment',rights_assessment_id,'observation',rights_observation_id,'role',evidence_role)::text FROM rights.rights_assessment_observation
  UNION ALL SELECT 'policyEvaluation|' || jsonb_build_object('id',provider_policy_evaluation_id,'bridge',object_visual_reference_id,'state',evaluated_state,'evaluator',evaluator_actor,'evaluatedAtUs',(extract(epoch FROM evaluated_at)*1000000)::bigint)::text FROM rights.provider_policy_evaluation
  UNION ALL SELECT 'delivery|' || jsonb_build_object('id',delivery_assessment_id,'bridge',object_visual_reference_id,'attribution',attribution_bundle_id,'mode',delivery_mode,'rule',reason_code,'machineReason',machine_reason_code,'assessor',assessor_actor,'assessedAtUs',(extract(epoch FROM assessed_at)*1000000)::bigint)::text FROM rights.delivery_assessment
  UNION ALL SELECT 'deliveryRights|' || jsonb_build_object('delivery',delivery_assessment_id,'assessment',rights_assessment_id,'role',evidence_role)::text FROM rights.delivery_rights_assessment
  UNION ALL SELECT 'deliveryPolicy|' || jsonb_build_object('delivery',delivery_assessment_id,'evaluation',provider_policy_evaluation_id)::text FROM rights.delivery_policy_evaluation
  UNION ALL SELECT 'visualDisposition|' || jsonb_build_object('ledger',legacy_surface_ledger_id,'fingerprint',source_fingerprint,'referenceCount',visual_reference_count,'locatorCount',locator_occurrence_count,'setSha256',disposition_set_sha256)::text FROM rights.legacy_visual_surface_disposition
  UNION ALL SELECT 'visualClass|' || jsonb_build_object('ledger',legacy_surface_ledger_id,'disposition',disposition,'evidence',evidence_item_id)::text FROM rights.legacy_visual_surface_classification
) content ORDER BY row_text
) TO STDOUT;
"""
    return stream_sql_hash(args, sql)


def command_exit(args: argparse.Namespace, sql: str, *, user: str) -> int:
    """Run one bounded role-level probe and return its psql exit status.

    Denial probes are deliberately actual SQL attempts rather than catalog-only
    privilege inspection.  The write probe is wrapped in a transaction and has
    an always-false predicate, so even an accidental grant cannot persist data.
    """
    result = subprocess.run(
        ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True,
        capture_output=True,
        env=environment(args, user),
        check=False,
    )
    return result.returncode


def public_boundary(args: argparse.Namespace) -> dict[str, int]:
    api_current = int(query(args, "SELECT count(*) FROM api_v1.current_object;", user=API_ROLE) or "0")
    api_pixels = int(query(args, "SELECT count(*) FROM api_v1.current_object WHERE remote_image_url IS NOT NULL;", user=API_ROLE) or "0")
    # Each of these must be denied.  The third statement has no matching row
    # and is protected by rollback even if a bad grant ever regresses.
    raw_locator_denied = int(command_exit(args, "SELECT 1 FROM rights.visual_locator LIMIT 1;", user=API_ROLE) != 0)
    raw_source_denied = int(command_exit(args, "SELECT 1 FROM raw.source_record LIMIT 1;", user=API_ROLE) != 0)
    write_denied = int(command_exit(args, "BEGIN; DELETE FROM core.archive_object WHERE false; ROLLBACK;", user=API_ROLE) != 0)
    return {
        "apiCurrentRows": api_current,
        "apiPixelRows": api_pixels,
        "rawLocatorSelectDenied": raw_locator_denied,
        "rawSourceSelectDenied": raw_source_denied,
        "archiveWriteDenied": write_denied,
    }


def integrity_invariants(args: argparse.Namespace) -> dict[str, int]:
    """Return zero-only invariant failures, including the tier partition."""
    sql = f"""
SET ROLE {OWNER_ROLE};
WITH
  ledger AS (SELECT * FROM raw.legacy_surface_ledger),
  eligible AS (
    SELECT DISTINCT archive_object_id
    FROM research.corpus_membership WHERE disposition='eligible'
  ),
  held AS (
    SELECT DISTINCT l.archive_object_id
    FROM raw.fail_closed_delta d
    JOIN ledger l ON l.source_record_id=d.source_record_id
    WHERE d.disposition='held'
  )
SELECT jsonb_build_object(
  'distinctLedgerMismatch', abs((SELECT count(*) FROM ledger) - (SELECT count(DISTINCT legacy_surface_ledger_id) FROM ledger)),
  'distinctObjectMismatch', abs((SELECT count(*) FROM core.archive_object) - (SELECT count(DISTINCT archive_object_id) FROM core.archive_object)),
  'distinctRawRecordMismatch', abs((SELECT count(*) FROM raw.source_record) - (SELECT count(DISTINCT source_record_id) FROM raw.source_record)),
  'distinctSeedLinkMismatch', abs((SELECT count(*) FROM provenance.object_source_record WHERE source_role='seed_description') - (SELECT count(DISTINCT archive_object_id) FROM provenance.object_source_record WHERE source_role='seed_description')),
  'fieldLiteralOrphan', (SELECT count(*) FROM raw.field_literal f LEFT JOIN raw.source_record r ON r.source_record_id=f.source_record_id WHERE r.source_record_id IS NULL),
  'fieldLiteralDuplicate', (SELECT count(*) FROM (SELECT source_record_id,json_pointer,occurrence_ordinal FROM raw.field_literal GROUP BY source_record_id,json_pointer,occurrence_ordinal HAVING count(*) <> 1) q),
  'folderMembershipMismatch', abs((SELECT count(*) FROM provenance.assignment_folder_membership)-47982),
  'folderAssignmentStatusMismatch', (SELECT count(*) FROM provenance.canonical_assignment WHERE assignment_kind='folder_membership' AND status <> 'proposed'),
  'folderAssignmentSubtypeMismatch', (SELECT count(*) FROM provenance.canonical_assignment a LEFT JOIN provenance.assignment_folder_membership f ON f.canonical_assignment_id=a.canonical_assignment_id WHERE a.assignment_kind='folder_membership' AND f.canonical_assignment_id IS NULL),
  'ledgerObjectOrphan', (SELECT count(*) FROM ledger l LEFT JOIN core.archive_object o ON o.archive_object_id=l.archive_object_id WHERE o.archive_object_id IS NULL),
  'ledgerRecordOrphan', (SELECT count(*) FROM ledger l LEFT JOIN raw.source_record r ON r.source_record_id=l.source_record_id WHERE r.source_record_id IS NULL),
  'recordAssetMismatch', (SELECT count(*) FROM ledger l JOIN raw.source_record r ON r.source_record_id=l.source_record_id WHERE r.source_asset_id IS DISTINCT FROM l.canonical_input_asset_id),
  'eligibleCountMismatch', abs((SELECT count(*) FROM eligible)-7995),
  'heldCountMismatch', abs((SELECT count(*) FROM held)-7928),
  'tierOverlap', (SELECT count(*) FROM eligible e JOIN held h USING (archive_object_id)),
  'tierCoverageMismatch', abs((SELECT count(*) FROM (SELECT archive_object_id FROM eligible UNION SELECT archive_object_id FROM held) q)-15923),
  'ledgerWithoutVisualDisposition', (SELECT count(*) FROM ledger l LEFT JOIN rights.legacy_visual_surface_disposition d ON d.legacy_surface_ledger_id=l.legacy_surface_ledger_id WHERE d.legacy_surface_ledger_id IS NULL),
  'visualDispositionDuplicate', (SELECT count(*) FROM (SELECT legacy_surface_ledger_id FROM rights.legacy_visual_surface_disposition GROUP BY legacy_surface_ledger_id HAVING count(*) <> 1) q),
  'ledgerWithoutVisualClassification', (SELECT count(*) FROM ledger l LEFT JOIN rights.legacy_visual_surface_classification c ON c.legacy_surface_ledger_id=l.legacy_surface_ledger_id WHERE c.legacy_surface_ledger_id IS NULL),
  'sourceLinkMismatch', (SELECT count(*) FROM ledger l LEFT JOIN provenance.object_source_record s ON s.archive_object_id=l.archive_object_id AND s.source_record_id=l.source_record_id AND s.source_role='seed_description' WHERE s.archive_object_id IS NULL),
  'visualBridgeReferenceOrphan', (SELECT count(*) FROM rights.object_visual_reference b LEFT JOIN rights.external_visual_reference r ON r.external_visual_reference_id=b.external_visual_reference_id WHERE r.external_visual_reference_id IS NULL)
)::text;
"""
    return {key: int(value) for key, value in json.loads(query(args, sql)).items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--expected-schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise VerifyError("DISPOSABLE_CONNECTION_POLICY_VIOLATION")
    before = schema_hash(args)
    if before != args.expected_schema:
        raise VerifyError("SCHEMA_SHA_BEFORE_MISMATCH:" + before)
    counts = count_vector(args)
    metrics = metric_query(args)
    stable_key_set_sha256, stable_row_count = stable_key_hash(args)
    normalized_content_sha256, semantic_content_row_count = semantic_content_hash(args)
    invariants = integrity_invariants(args)
    public = public_boundary(args)
    after = schema_hash(args)
    if after != args.expected_schema:
        raise VerifyError("SCHEMA_SHA_AFTER_MISMATCH:" + after)
    expected = {
        "legacyInputSurfaces": 15923, "operationalObjects": 15923, "rawSourceRecords": 15923,
        "objectSourceSeedLinks": 15923, "folders": 185,
        "folderMembershipAssignments": 47982, "sourceVerified": 7995, "metadataSupportedHeld": 2971,
        "missingTraceTierHeld": 4957, "researchEligibleObjects": 7995, "heldObjects": 7928,
        "rejectedObjects": 0, "acceptedTraceRelations": 0, "traceEligibleObjects": 0,
        "semanticRelationRows": 0, "legacyProjectionFactRows": 0,
        "traceWorkingTreeRows": 0, "traceWorkingBranchRows": 0,
        "traceWorkingNodePlacementRows": 0, "traceWorkingAssignmentRows": 0,
        "traceRootNodes": 15923,
        "visualBundles": 15923, "bundlesWithReference": 15788, "bundlesWithoutReference": 135,
        "locatorOccurrences": 15790, "unclassifiedVisualReference": 0, "positiveRights": 0,
        "remoteImageDecisions": 0, "publicPixelLocators": 0, "acceptedSemanticRelations": 0,
        "traceProjectionEdges": 0, "traceProjectionNodes": 0,
        "traceProjectionTrees": 0, "traceProjectionBranches": 0,
        "traceProjectionNodePlacements": 0, "traceProjectionEdgePlacements": 0,
        "currentPointers": 0, "sealedReleases": 0,
        "rightsObservations": 15788, "rightsAssessments": 15788,
        "policyEvaluations": 15788, "citationOnlyDecisions": 15788,
    }
    failed = {key: [metrics.get(key), wanted] for key, wanted in expected.items() if metrics.get(key) != wanted}
    if any(value != 0 for value in invariants.values()):
        failed["integrityInvariants"] = invariants
    expected_public = {
        "apiCurrentRows": 0, "apiPixelRows": 0,
        "rawLocatorSelectDenied": 1, "rawSourceSelectDenied": 1,
        "archiveWriteDenied": 1,
    }
    if public != expected_public:
        failed["publicBoundary"] = [public, expected_public]
    report = {
        "status": "PASS" if not failed else "FAIL",
        "schemaShaBefore": before, "schemaShaAfter": after,
        "schemaDrift": 0 if before == after else 1,
        "metrics": metrics, "countVector": counts,
        "countVectorSha256": sha256(canonical_json(counts)),
        "stableKeySetSha256": stable_key_set_sha256,
        "normalizedContentSha256": normalized_content_sha256,
        "stableRowCount": stable_row_count,
        "semanticContentRowCount": semantic_content_row_count,
        "integrityInvariants": invariants, "publicBoundary": public, "failures": failed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "schemaDrift", "countVectorSha256", "stableKeySetSha256", "normalizedContentSha256")}, sort_keys=True))
    return 0 if not failed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerifyError, subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
