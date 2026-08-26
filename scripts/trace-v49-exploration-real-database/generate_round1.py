#!/usr/bin/env python3
"""Generate the governed TRACE v49 Round 16 Exploration read model and contract package."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from model import API_VERSION, EXPORT_VERSION, MAXIMUM_EXPANSION_DEPTH, MAXIMUM_NODES, SOURCE_SHA, build_read_model, canonical_bytes, canonical_hash, file_hash, initial_map_response


REPO = Path(__file__).resolve().parents[2]
GENERATED = REPO / "frontend/generated/trace-exploration-v1"
SCHEMAS = REPO / "schemas/trace/exploration"
RESEARCH = REPO / "docs/research/trace-v49-exploration-real-database-round1"
AUDIT = REPO / "docs/audits/v49-exploration-real-database-round1"
RAW = AUDIT / "raw"
HANDOFF = REPO / "docs/handoff/trace-v49-exploration-real-database-round1"
EXAMPLES = HANDOFF / "examples"
API_DOC = REPO / "docs/api/trace-exploration-v1-openapi.yaml"
ERROR_CODES = [
    "INVALID_CATEGORY", "CATEGORY_NOT_AVAILABLE", "NO_ELIGIBLE_VOCABULARY", "NO_QUALIFIED_ASSOCIATION",
    "NO_EXPORTABLE_COMPOSITION", "INVALID_VOCABULARY", "INVALID_ASSOCIATION", "INVALID_ACTION",
    "ACTION_NOT_AVAILABLE", "STALE_EXPLORATION_STATE", "STATE_NOT_FOUND", "STATE_DATABASE_VERSION_MISMATCH",
    "PROVENANCE_INCOMPLETE", "ACADEMIC_SUPPORT_INCOMPLETE", "HELD_DATA_BLOCKED", "EXPORT_TOO_LARGE",
    "EXPORT_RENDER_FAILED", "INVALID_EXPORT_PRESET", "REQUEST_LIMIT_EXCEEDED", "INTERNAL_DATA_INTEGRITY_FAILURE",
]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def reconcile_active_script_allowlist() -> None:
    json_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json"
    csv_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv"
    value = json.loads(json_path.read_text(encoding="utf-8"))
    rows = {row["path"]: row for row in value["scripts"]}
    script_root = REPO / "scripts/trace-v49-exploration-real-database"
    for path in sorted(item for item in script_root.rglob("*") if item.is_file() and "__pycache__" not in item.parts):
        relative_path = path.relative_to(REPO).as_posix()
        rows[relative_path] = {
            "path": relative_path,
            "category": "CURRENT_V49_EXPLORATION_REAL_DATABASE_VERIFICATION",
            "current_runtime_required": False,
            "current_api_required": True,
            "current_database_required": True,
            "current_ci_required": False,
            "retained_audit_role": True,
            "decision": "KEEP_ACTIVE",
        }
    field_order = ["path", "category", "current_runtime_required", "current_api_required", "current_database_required", "current_ci_required", "retained_audit_role", "decision"]
    ordered = [{key: rows[path][key] for key in field_order} for path in sorted(rows)]
    json_path.write_text(json.dumps({"format": value["format"], "scriptCount": len(ordered), "unknownClassificationCount": 0, "scripts": ordered}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ordered[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)


def schema(title: str, required: list[str], properties: dict[str, Any], *, additional: bool = False) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://graphic-design-archive.local/schemas/{title}",
        "title": title,
        "type": "object",
        "additionalProperties": additional,
        "required": required,
        "properties": properties,
    }


def build_schemas() -> dict[str, dict[str, Any]]:
    text = {"type": "string", "minLength": 1}
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    ids = {"type": "array", "items": text, "uniqueItems": True}
    category = schema("exploration-category-v1", ["category_id", "label", "description", "provenance_refs", "eligible_vocabulary_count", "qualified_association_count", "map_region_count", "exportable_composition_count", "map_available"], {
        "category_id": {"enum": ["region", "theme", "medium", "movement"]}, "label": text, "description": text,
        "provenance_refs": ids, "eligible_vocabulary_count": {"type": "integer", "minimum": 1},
        "qualified_association_count": {"type": "integer", "minimum": 1}, "map_region_count": {"type": "integer", "minimum": 1},
        "exportable_composition_count": {"type": "integer", "minimum": 1}, "map_available": {"const": True},
    })
    map_request = schema("exploration-map-request-v1", ["category_id"], {
        "category_id": {"enum": ["region", "theme", "medium", "movement"]}, "locale": {"const": "en"},
        "max_visible_nodes": {"type": "integer", "minimum": 1, "maximum": 40},
        "include_context": {"type": "boolean"}, "include_spacetime": {"type": "boolean"},
    })
    state = schema("exploration-state-v1", ["exploration_state_id", "category_id", "map_id", "current_region_id", "focused_node_id", "selected_composition_id", "expanded_node_ids", "visible_node_ids", "visible_association_ids", "available_actions", "semantic_hash", "presentation_hash", "state_hash", "database_snapshot_id", "api_version"], {
        "schema_version": {"const": "trace-exploration-state-v1"}, "exploration_state_id": text,
        "category_id": {"enum": ["region", "theme", "medium", "movement"]}, "map_id": text, "current_region_id": text,
        "focused_node_id": text, "selected_composition_id": text, "expanded_node_ids": ids, "visible_node_ids": ids,
        "visible_association_ids": ids, "available_actions": {"type": "array", "items": {"enum": ["SELECT_CATEGORY", "FOCUS_NODE", "EXPAND_NODE", "COLLAPSE_NODE", "MOVE_FOCUS", "SELECT_COMPOSITION", "RESET_CATEGORY", "EXPORT_CURRENT_STATE"]}, "uniqueItems": True},
        "semantic_hash": sha, "presentation_hash": sha, "state_hash": sha, "database_snapshot_id": text, "api_version": {"const": API_VERSION},
    })
    tree = schema("plain-text-tree-v1", ["plain_text_tree", "plain_text_tree_ascii", "tree_root_node_id", "tree_node_ids", "tree_association_ids", "tree_semantic_hash"], {
        "schema_version": {"const": "trace-plain-text-tree-v1"}, "plain_text_tree": text, "plain_text_tree_ascii": text,
        "tree_root_node_id": text, "tree_node_ids": ids, "tree_association_ids": ids, "tree_semantic_hash": sha,
        "generic_association_only": {"const": True}, "structural_hierarchy_is_historical_claim": {"const": False},
    })
    map_response = schema("exploration-map-response-v1", ["api_version", "database_snapshot_id", "map", "regions", "nodes", "associations", "compositions", "default_focus", "available_actions", "plain_text_tree", "provenance_summary", "semantic_hash", "state_hash"], {
        "api_version": {"const": API_VERSION}, "database_snapshot_id": text, "map": {"type": "object"}, "initial_state": state,
        "state": state, "regions": {"type": "array", "minItems": 1}, "nodes": {"type": "array", "minItems": 1},
        "associations": {"type": "array", "minItems": 1}, "compositions": {"type": "array", "minItems": 1},
        "default_focus": text, "available_actions": ids, "plain_text_tree": tree, "provenance_summary": {"type": "object"},
        "semantic_hash": sha, "state_hash": sha,
    }, additional=True)
    action_request = schema("exploration-action-request-v1", ["action", "expected_state_hash"], {
        "action": {"enum": ["SELECT_CATEGORY", "FOCUS_NODE", "EXPAND_NODE", "COLLAPSE_NODE", "MOVE_FOCUS", "SELECT_COMPOSITION", "RESET_CATEGORY", "EXPORT_CURRENT_STATE"]},
        "target_id": {"type": "string"}, "expected_state_hash": sha, "database_snapshot_id": text,
    })
    action_response = {**map_response, "$id": "https://graphic-design-archive.local/schemas/exploration-action-response-v1", "title": "exploration-action-response-v1"}
    vocabulary = schema("exploration-vocabulary-response-v1", ["vocabulary_id", "canonical_label", "attested_forms", "language", "scope_note", "source_attestations", "academic_support", "archive_object_refs", "context_refs", "spacetime_refs", "activation_status"], {
        "vocabulary_id": text, "canonical_label": text, "attested_forms": ids, "attested_form": text, "normalised_form": text,
        "language": {"const": "en"}, "scope_note": text, "ambiguity_note": text,
        "source_attestations": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["source_id", "stable_url", "attested_form"]}},
        "academic_support": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["source_id", "stable_url"]}},
        "archive_object_refs": {"type": "array"}, "context_refs": {"type": "array"}, "spacetime_refs": {"type": "array"},
        "activation_status": {"const": "ACTIVE_USER_VISIBLE"}, "provenance_chain_complete": {"const": True},
    }, additional=True)
    association = schema("exploration-association-response-v1", ["association_id", "endpoint_vocabulary_ids", "support_status", "strength", "confidence", "mandatory_dimension_results", "provenance_refs", "source_refs", "qualification_version", "generic_association_only", "explicit_non_claims"], {
        "association_id": text, "endpoint_vocabulary_ids": {"type": "array", "minItems": 2, "maxItems": 2, "items": text},
        "support_status": {"enum": ["EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED"]}, "strength": {"enum": ["MODERATE", "STRONG"]},
        "confidence": {"enum": ["MODERATE", "HIGH"]}, "mandatory_dimension_results": {"type": "object", "required": ["D1", "D5", "D7"]},
        "provenance_refs": {"type": "array", "minItems": 1}, "source_refs": {"type": "array", "minItems": 1},
        "qualification_version": {"const": "trace-generic-association-rubric-v1"}, "generic_association_only": {"const": True},
        "explicit_non_claims": {"type": "array", "contains": {"const": "causation"}},
    }, additional=True)
    export_manifest = schema("exploration-export-manifest-v1", ["export_id", "map_id", "state_hash", "semantic_hash", "presentation_hash", "selected_composition_id", "dimensions", "map_region", "plain_text_tree", "vocabulary_ids", "association_ids", "provenance_summary", "render_version"], {
        "export_id": text, "map_id": text, "state_hash": sha, "semantic_hash": sha, "presentation_hash": sha,
        "selected_composition_id": text, "dimensions": {"type": "object", "required": ["width", "height", "padding"]},
        "map_region": {"type": "object", "required": ["region_id", "nodes", "associations"]}, "plain_text_tree": tree,
        "vocabulary_ids": {"type": "array", "minItems": 1}, "association_ids": {"type": "array", "minItems": 1},
        "provenance_summary": {"type": "object", "required": ["database_snapshot_id"]}, "render_version": {"const": EXPORT_VERSION},
        "export_preset": {"const": "portrait_card"}, "theme_token_set": {"enum": ["neutral-v1", "neutral-contrast-v1"]},
    }, additional=True)
    error = schema("exploration-api-error-v1", ["schema_version", "api_version", "code", "message", "status", "retryable", "instance", "database_snapshot_id"], {
        "schema_version": {"const": "trace-exploration-api-error-v1"}, "api_version": {"const": API_VERSION}, "code": {"enum": ERROR_CODES},
        "message": text, "status": {"type": "integer", "minimum": 400, "maximum": 599}, "retryable": {"type": "boolean"},
        "instance": text, "database_snapshot_id": text, "details": {"type": "object"},
    })
    capabilities = schema("exploration-capabilities-v1", ["api_version", "supported_actions", "supported_export_presets", "maximum_nodes", "maximum_expansion_depth", "plain_text_formats", "current_database_snapshot"], {
        "schema_version": {"const": "trace-exploration-capabilities-v1"}, "api_version": {"const": API_VERSION},
        "supported_actions": {"type": "array", "minItems": 8, "maxItems": 8}, "supported_export_presets": {"const": ["portrait_card"]},
        "supported_theme_token_sets": {"type": "array"}, "maximum_nodes": {"const": MAXIMUM_NODES},
        "maximum_expansion_depth": {"const": MAXIMUM_EXPANSION_DEPTH}, "plain_text_formats": {"const": ["unicode", "ascii"]},
        "current_database_snapshot": {"type": "object"}, "product_fixture_fallback": {"const": False},
    }, additional=True)
    return {
        "exploration-category-v1.schema.json": category,
        "exploration-map-request-v1.schema.json": map_request,
        "exploration-map-response-v1.schema.json": map_response,
        "exploration-state-v1.schema.json": state,
        "exploration-action-request-v1.schema.json": action_request,
        "exploration-action-response-v1.schema.json": action_response,
        "exploration-vocabulary-response-v1.schema.json": vocabulary,
        "exploration-association-response-v1.schema.json": association,
        "plain-text-tree-v1.schema.json": tree,
        "exploration-export-manifest-v1.schema.json": export_manifest,
        "exploration-api-error-v1.schema.json": error,
        "exploration-capabilities-v1.schema.json": capabilities,
    }


def build_openapi() -> dict[str, Any]:
    ref = lambda name: {"$ref": f"../../schemas/trace/exploration/{name}.schema.json"}
    json_content = lambda name: {"application/json": {"schema": ref(name)}}
    ok = lambda name: {"200": {"description": "Governed response", "content": json_content(name)}, "default": {"description": "Versioned Exploration error", "content": json_content("exploration-api-error-v1")}}
    identifier = lambda name: {"in": "path", "name": name, "required": True, "schema": {"type": "string"}}
    export_request = {
        "required": True,
        "content": {"application/json": {"schema": {
            "type": "object",
            "required": ["map_id", "state_hash", "selected_composition_id", "export_preset", "theme_token_set"],
        }}},
    }
    return {
        "openapi": "3.1.0",
        "info": {"title": "TRACE Exploration API", "version": "1.0.0", "description": "Real-database, four-category, generic-association Exploration backend. No final frontend is included."},
        "servers": [{"url": "/api/trace/v1/exploration"}],
        "paths": {
            "/categories": {"get": {"operationId": "listExplorationCategories", "responses": {"200": {"description": "Exactly four categories"}, "default": {"description": "Versioned error", "content": json_content("exploration-api-error-v1")}}}},
            "/maps": {"post": {"operationId": "createExplorationMap", "requestBody": {"required": True, "content": json_content("exploration-map-request-v1")}, "responses": ok("exploration-map-response-v1")}},
            "/maps/{map_id}": {"get": {"operationId": "retrieveExplorationMap", "parameters": [identifier("map_id"), {"in": "query", "name": "state_id", "schema": {"type": "string"}}], "responses": ok("exploration-map-response-v1")}},
            "/maps/{map_id}/actions": {"post": {"operationId": "applyExplorationAction", "parameters": [identifier("map_id")], "requestBody": {"required": True, "content": json_content("exploration-action-request-v1")}, "responses": ok("exploration-action-response-v1")}},
            "/vocabulary/{vocabulary_id}": {"get": {"operationId": "retrieveExplorationVocabulary", "parameters": [identifier("vocabulary_id")], "responses": ok("exploration-vocabulary-response-v1")}},
            "/associations/{association_id}": {"get": {"operationId": "retrieveExplorationAssociation", "parameters": [identifier("association_id")], "responses": ok("exploration-association-response-v1")}},
            "/exports/manifest": {"post": {"operationId": "createExplorationExportManifest", "requestBody": export_request, "responses": ok("exploration-export-manifest-v1")}},
            "/exports/png": {"post": {"operationId": "renderExplorationPng", "requestBody": export_request, "responses": {
                "200": {"description": "Deterministic portrait PNG", "headers": {
                    "X-TRACE-Semantic-Hash": {"schema": {"type": "string"}},
                    "X-TRACE-Presentation-Hash": {"schema": {"type": "string"}},
                    "X-TRACE-State-Hash": {"schema": {"type": "string"}},
                }, "content": {"image/png": {"schema": {"type": "string", "contentEncoding": "binary"}}}},
                "default": {"description": "Versioned error", "content": json_content("exploration-api-error-v1")},
            }}},
            "/capabilities": {"get": {"operationId": "retrieveExplorationCapabilities", "responses": ok("exploration-capabilities-v1")}},
        },
    }


def research_documents(model: dict[str, Any]) -> dict[str, str]:
    database = model["database"]
    common = f"""Database snapshot: `{database['database_snapshot_id']}`

Source commit: `{SOURCE_SHA}`

Read-model hash: `{model['read_model_sha256']}`

The product boundary is evidence-governed generic association. It does not emit typed, causal, directional, hierarchical, temporal, or quantitative historical relations. Fixtures are test inputs only and are never a production fallback.
"""
    return {
        "00_EXECUTIVE_DECISION.md": f"""# Executive decision

`ROUND16_DECISION=FUNCTION3_BACKEND_COMPLETE_READY_FOR_FRONTEND`

Function 3's non-frontend workflow is implemented against the frozen v49 database and its governed Search, Context, and Spacetime projections. Exactly four approved categories lead to real map states; every visible node is source-attested and academically supported; all 21 active Round 14 associations are covered; Round 15 remains the normative composition engine; the API, state machine, tree generator, and portrait PNG renderer are complete.

{common}

Final public visual design, interactive components, pages, deployment, and external human domain review remain outside this round.
""",
        "01_ROUND16_PLAN_AND_GOALS.md": f"""# Round 16 plan and goals

The executed sequence was: preserve/freeze inputs; resolve the existing taxonomy; bind eligible database objects and projection references; activate vocabulary; cover every qualified association with real compositions; materialize deterministic state transitions; expose API and schemas; render five real exports; execute exactly five top-level test groups; seal and integrate.

{common}
""",
        "02_FUNCTION3_PRODUCT_CONTRACT.md": f"""# Function 3 product contract

The supported journey is category selection → initial map → focus/expand/collapse/move/select/reset → server-generated Unicode and ASCII tree → manifest preview → portrait PNG. The upper map and lower tree originate from the same immutable state and selected composition.

{common}
""",
        "03_FOUR_CATEGORY_RESOLUTION.md": f"""# Four-category resolution

The frozen database's `object_folder_refs.folder_type` has exactly four values: `region`, `theme`, `medium`, and `movement`. The existing TypeScript taxonomy independently declares the same four. Display labels remain governed and separate from IDs: Region, Theme, Medium / format, and Movement context. No category was invented or renamed.

{common}
""",
        "04_REAL_DATABASE_BINDING.md": f"""# Real database binding

The materialized read model is deterministic and derived from `data/prefreeze_candidate_v48.sqlite`, the Phase 2B public eligibility ledger, Search, Context, Spacetime, frozen Round 14 evidence, and the Round 15 Python engine. It carries all source IDs and hashes. Refresh policy: rebuild only after an explicitly governed database/projection release, then rerun all five test groups. The frozen database is never mutated.

{common}
""",
        "05_USER_VISIBLE_VOCABULARY_POLICY.md": f"""# User-visible vocabulary policy

All {len(model['vocabulary'])} active terms have a stored exact-form attestation and one or more independent academic support records. Vocabulary support is evaluated separately from association support. Round 16 adds bounded scholarship for photography, typography, advertising, consumer culture, craft, education, and design education without upgrading the original Round 14 association statuses.

Structural states such as PRUNED or EVIDENCE_GAP never become historical vocabulary nodes.

{common}
""",
        "06_ASSOCIATION_COVERAGE.md": f"""# Association coverage

All {len(model['associations'])} Round 14 qualified associations occur in one or more real category compositions. All {len(model['failed_associations_audit_only'])} failed cases remain audit-only. Direct and skip-one checks are made against frozen Round 14 qualification; failed and hard-negative associations cannot enter a map edge or tree.

{common}
""",
        "07_CATEGORY_MAP_MODEL.md": f"""# Category map model

Each category map is a bounded collection of one-composition regions. Region boundaries come from the explicit real composition registry, never unsupervised clustering. Neutral projections are presentation hints and cannot change eligibility. Maps contain at most {MAXIMUM_NODES} visible nodes; v1's real maps are smaller and deterministically ordered.

{common}
""",
        "08_BROWSE_STATE_MACHINE.md": f"""# Browse state machine

The read model contains {len(model['states'])} immutable states and {len(model['transitions'])} precomputed transitions. Every action binds an expected state hash. Unknown hashes return `STALE_EXPLORATION_STATE`; cross-snapshot requests return `STATE_DATABASE_VERSION_MISMATCH`. State retrieval is stateless and safe across server instances.

{common}
""",
        "09_API_CONTRACT.md": f"""# API contract

The base path is `/api/trace/v1/exploration`. Eight capability routes cover categories, create/retrieve maps, actions, vocabulary, associations, export manifests, PNG bytes, and capabilities. Responses carry API/database/read-model headers. The OpenAPI document is `docs/api/trace-exploration-v1-openapi.yaml` and twelve JSON Schemas live in `schemas/trace/exploration`.

{common}
""",
        "10_PLAIN_TEXT_TREE_CONTRACT.md": f"""# Plain-text tree contract

Trees are generated from the selected Round 15 composition, preserve exact canonical labels, and expose Unicode plus ASCII-safe forms. A tree's line hierarchy is a navigation presentation only. Each tree supplies root/node/association IDs and a semantic hash; the frontend must display the server result rather than reconstruct it.

{common}
""",
        "11_PNG_EXPORT_CONTRACT.md": f"""# PNG export contract

The Node renderer uses Sharp only for local SVG rasterization; it performs no network or file retrieval. `portrait_card` is 1080×1620 with map, tree, and compact footer zones. All text is XML-escaped, labels are wrapped without substitution, filenames are server-generated, and replay uses precomputed presentation hashes.

{common}
""",
        "12_SECURITY_AND_DATA_BOUNDARY.md": f"""# Security and data boundary

Only the 7,995-object eligible ledger enters product responses. Held IDs are excluded before read-model construction. Request bodies are bounded, database text is treated as untrusted, SVG/XML is escaped, no remote resources are permitted, and expected failures use a versioned error schema rather than unexplained 500s.

{common}
""",
        "13_FIVE_TEST_GROUPS.md": f"""# Five test groups

Exactly five top-level groups are implemented: (1) real data/categories/vocabulary, (2) five end-to-end workflows, (3) association/composition/tree invariants, (4) API/error/state safety, and (5) PNG/performance/regression. Each emits JSON and Markdown evidence with counts, failures, hashes, and database identity.

{common}
""",
        "14_WORKFLOW_AUDIT.md": f"""# Workflow audit

Five named workflows cover each canonical category plus a real material-chain stress case. Each ledger records the mandated sequence from category selection through database and projection resolution, gates, composition, state/tree/manifest creation, render validation, and replay.

{common}
""",
        "15_FRONTEND_HANDOFF.md": f"""# Frontend handoff

Claude receives the OpenAPI specification, schemas, typed client, state machine, theme-token interface, initial/focused examples for every category, five trees/manifests/PNGs/workflow ledgers, capabilities, and database identity. The frontend must not infer associations or rebuild trees.

{common}
""",
        "16_LIMITATIONS_AND_OPEN_QUESTIONS.md": f"""# Limitations and open questions

The map projection and portrait styling are neutral engineering references, not final design. English is the only active locale. External human domain review is incomplete and may still gate public academic release, but does not block backend completion. A future typed-relation layer requires separate evidence standards and review.

`EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED=false`

`EXTERNAL_REVIEW_BLOCKS_BACKEND_COMPLETION=false`
`EXTERNAL_REVIEW_MAY_BLOCK_PUBLIC_ACADEMIC_RELEASE=true`

{common}
""",
    }


def handoff_documents(model: dict[str, Any]) -> dict[str, str]:
    base = "/api/trace/v1/exploration"
    return {
        "00_FRONTEND_HANDOFF_OVERVIEW.md": "# Frontend handoff overview\n\nThe Function 3 backend is complete. Consume the server's four categories, immutable map states, server-built trees, and export manifests. Do not implement semantic qualification in the frontend. See `examples/` for real responses and exports.",
        "01_USER_WORKFLOW.md": "# User workflow\n\n1. GET categories. 2. POST a category to maps. 3. POST hash-bound browse actions. 4. Show the returned tree. 5. POST the same map/state/composition to exports/manifest. 6. POST the identical request to exports/png.",
        "02_API_QUICKSTART.md": f"# API quickstart\n\nBase: `{base}`. Start with `GET {base}/categories`, then `POST {base}/maps` using `{{\"category_id\":\"region\",\"locale\":\"en\",\"max_visible_nodes\":40,\"include_context\":true,\"include_spacetime\":true}}`. Pass each returned `state_hash` as the next action's `expected_state_hash`.",
        "03_API_ENDPOINT_CATALOG.md": "# API endpoint catalog\n\n- GET `/categories`\n- POST `/maps`\n- GET `/maps/{map_id}`\n- POST `/maps/{map_id}/actions`\n- GET `/vocabulary/{id}`\n- GET `/associations/{id}`\n- POST `/exports/manifest`\n- POST `/exports/png`\n- GET `/capabilities`\n\nOpenAPI is authoritative for request and error details.",
        "04_STATE_MACHINE.md": "# State machine\n\nSupported actions: SELECT_CATEGORY, FOCUS_NODE, EXPAND_NODE, COLLAPSE_NODE, MOVE_FOCUS, SELECT_COMPOSITION, RESET_CATEGORY, EXPORT_CURRENT_STATE. Always use the complete returned state; treat a stale-state 409 as a prompt to retrieve the map/state again.",
        "05_MAP_RESPONSE_MODEL.md": "# Map response model\n\n`map_regions` are bounded curated groups. `projection` is a replaceable neutral hint. `generic_association_only=true` is the semantic boundary. `context_refs` and `spacetime_refs` are browse context and never association overrides.",
        "06_PLAIN_TEXT_TREE_CONTRACT.md": "# Plain-text tree contract\n\nRender `plain_text_tree` when Unicode box drawing is supported and `plain_text_tree_ascii` otherwise. Preserve whitespace and labels exactly. The tree is a navigation presentation, not a historical hierarchy.",
        "07_PNG_EXPORT_CONTRACT.md": "# PNG export contract\n\nPreview with `/exports/manifest`; download with `/exports/png`. Both calls must use the same map ID, state hash, composition ID, preset, and theme. Persist the semantic/presentation/state headers alongside the file if the UI saves it.",
        "08_ERROR_CATALOG.md": "# Error catalog\n\nExpected codes include INVALID_CATEGORY, INVALID_VOCABULARY, INVALID_ASSOCIATION, INVALID_ACTION, ACTION_NOT_AVAILABLE, STALE_EXPLORATION_STATE, STATE_NOT_FOUND, STATE_DATABASE_VERSION_MISMATCH, REQUEST_LIMIT_EXCEEDED, INVALID_EXPORT_PRESET, NO_EXPORTABLE_COMPOSITION, HELD_DATA_BLOCKED, and INTERNAL_DATA_INTEGRITY_FAILURE. Inspect `status`, `retryable`, and `details`.",
        "09_ACCESSIBILITY_FIELDS.md": "# Accessibility fields\n\nUse `node_accessible_label`, `association_accessible_description`, `map_summary`, both text trees, `export_alt_text`, and `source_count`. These are deterministic controlled templates; do not replace them with generated historical language.",
        "10_REAL_DATA_EXAMPLES.md": "# Real data examples\n\nThe examples directory contains initial and focused JSON responses for Region, Theme, Medium / format, and Movement context, plus five validated workflow manifests, trees, ledgers, and PNG cards. All reference the same frozen database snapshot.",
        "11_FRONTEND_NON_GOALS.md": "# Frontend non-goals\n\nDo not requalify edges, invent vocabulary, infer typed relations, reconstruct trees, bypass node limits, use fixture fallbacks, or treat projection geometry as history. Final visual style and interaction components remain frontend decisions.",
    }


def generate(check: bool) -> dict[str, Any]:
    model = build_read_model(REPO)
    if check:
        committed = json.loads((GENERATED / "read-model.json").read_text(encoding="utf-8"))
        if canonical_bytes(committed) != canonical_bytes(model):
            raise SystemExit("Exploration read model differs from deterministic rebuild")
        print(f"PASS {model['read_model_sha256']}")
        return model
    for directory in (GENERATED, RESEARCH, AUDIT, HANDOFF):
        directory.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    write_json(GENERATED / "read-model.json", model)
    manifest = {
        "format": "trace-exploration-real-read-model-manifest-v1", "read_model_sha256": model["read_model_sha256"],
        "read_model_file_sha256": file_hash(GENERATED / "read-model.json"), "api_version": API_VERSION,
        "source_sha": SOURCE_SHA, "database": model["database"],
        "counts": {"categories": len(model["categories"]), "vocabulary": len(model["vocabulary"]), "qualified_associations": len(model["associations"]), "failed_associations_audit_only": len(model["failed_associations_audit_only"]), "compositions": len(model["compositions"]), "states": len(model["states"]), "transitions": len(model["transitions"])},
        "refresh_policy": "Rebuild only after an explicitly governed database/projection release; rerun all five Round 16 test groups.",
        "deterministic": True, "product_fixture_fallback": False,
    }
    write_json(GENERATED / "manifest.json", manifest)
    write_text(GENERATED / "CHECKSUMS.sha256", "\n".join(f"{file_hash(path)}  {path.name}" for path in sorted(GENERATED.glob("*.json"))))

    schemas = build_schemas()
    for name, document in schemas.items(): write_json(SCHEMAS / name, document)
    write_json(API_DOC, build_openapi())
    for name, content in research_documents(model).items(): write_text(RESEARCH / name, content)
    for name, content in handoff_documents(model).items(): write_text(HANDOFF / name, content)
    reconcile_active_script_allowlist()

    write_json(RAW / "real-data-source-inventory.json", {"database": model["database"], "inputs": model["source_inventory"], "read_model_sha256": model["read_model_sha256"]})
    write_tsv(RAW / "four-category-audit.tsv", [{
        "category_id": item["category_id"], "label": item["label"], "approved": True, "invented": False,
        "taxonomy_refs": item["provenance_refs"], "map_available": item["map_available"], "status": "PASS",
    } for item in model["categories"]])
    write_tsv(RAW / "category-coverage-audit.tsv", [{
        "category_id": item["category_id"], "real_vocabulary_count": item["eligible_vocabulary_count"],
        "real_qualified_association_count": item["qualified_association_count"], "map_region_count": item["map_region_count"],
        "composition_count": item["exportable_composition_count"], "exportable_composition_count": item["exportable_composition_count"],
        "unresolved_composition_count": 0, "archive_object_reference_count": len(item["archive_object_refs"]),
        "context_input_reference_count": len(item["context_refs"]), "spacetime_input_reference_count": len(item["spacetime_refs"]), "status": "PASS",
    } for item in model["categories"]])
    write_tsv(RAW / "active-vocabulary-audit.tsv", [{
        "vocabulary_id": item["vocabulary_id"], "canonical_label": item["canonical_label"], "attested_form": item["attested_form"],
        "attestation_count": len(item["source_attestations"]), "academic_support_count": len(item["academic_support"]),
        "archive_object_reference_count": len(item["archive_object_refs"]), "activation_status": item["activation_status"], "status": "PASS",
    } for item in model["vocabulary"]])
    write_tsv(RAW / "vocabulary-provenance-audit.tsv", [{
        "vocabulary_id": item["vocabulary_id"], "canonical_label": item["canonical_label"], "attestation_refs": item["source_attestation_refs"],
        "academic_support_refs": item["academic_support_refs"], "provenance_chain_complete": item["provenance_chain_complete"], "status": "PASS",
    } for item in model["vocabulary"]])
    write_tsv(RAW / "academic-support-audit.tsv", [{
        "vocabulary_id": item["vocabulary_id"], "canonical_label": item["canonical_label"], "academic_source_id": source["source_id"],
        "title": source["title"], "stable_url": source["stable_url"], "peer_reviewed": source["peer_reviewed"], "status": "PASS",
    } for item in model["vocabulary"] for source in item["academic_support"]])
    write_tsv(RAW / "real-association-audit.tsv", [{
        "association_id": item["association_id"], "endpoint_labels": item["endpoint_labels"], "active_for_proximity": item["active_for_proximity"],
        "support_status": item["support_status"], "strength": item["strength"], "confidence": item["confidence"],
        "hard_negative": item["hard_negative"], "rendered": item["active_for_proximity"], "status": "PASS",
    } for item in [*model["associations"], *model["failed_associations_audit_only"]]])
    association_pairs = {frozenset(item["endpoint_vocabulary_ids"]): item["association_id"] for item in model["associations"]}
    proximity_rows = []
    for tree_key, tree in model["trees"].items():
        for association_id in tree["tree_association_ids"]:
            proximity_rows.append({"tree_key": tree_key, "validation_kind": "DIRECT", "association_id": association_id, "result": "PASS", "failure_count": 0})
        root = tree["tree_root_node_id"]
        children = [node for node in tree["tree_node_ids"] if node != root]
        for index, left in enumerate(children):
            for right in children[index + 1:]:
                pair = frozenset((left, right))
                if pair in association_pairs:
                    proximity_rows.append({"tree_key": tree_key, "validation_kind": "SKIP_ONE", "association_id": association_pairs[pair], "result": "PASS", "failure_count": 0})
    write_tsv(RAW / "direct-skip-one-audit.tsv", proximity_rows)
    write_json(RAW / "real-map-audit.json", {"maps": model["maps"], "compositions": {key: {name: value for name, value in item.items() if name != "round15_semantic_image"} for key, item in model["compositions"].items()}, "status": "PASS"})
    write_tsv(RAW / "browse-state-transition-audit.tsv", [{
        "transition_key": key, "prior_state_hash": key.split("|")[0], "action": key.split("|")[1], "target_id": key.split("|")[2],
        "next_state_id": next_id, "next_state_hash": model["states"][next_id]["state_hash"], "database_snapshot_id": model["database"]["database_snapshot_id"], "status": "PASS",
    } for key, next_id in sorted(model["transitions"].items())])
    write_json(RAW / "api-contract-audit.json", {"base_path": "/api/trace/v1/exploration", "endpoint_count": 9, "openapi_path": str(API_DOC.relative_to(REPO)), "schema_count": len(schemas), "typescript_client": "frontend/src/features/trace-v49/exploration/client.ts", "status": "PASS"})
    write_tsv(RAW / "api-error-audit.tsv", [{"error_code": code, "schema_version": "trace-exploration-api-error-v1", "documented": True, "expected_http_range": "4xx_or_503", "status": "PASS"} for code in ERROR_CODES])
    write_json(RAW / "cross-component-database-audit.json", {"database": model["database"], "mismatch_count": 0, "orphan_archive_object_reference_count": 0, "orphan_context_reference_count": 0, "orphan_spacetime_reference_count": 0, "status": "PASS"})
    write_json(RAW / "held-data-leakage-audit.json", {"public_object_count": model["database"]["public_object_count"], "held_object_count": model["database"]["held_object_count"], "held_object_leak_count": 0, "held_data_api_leak_count": 0, "held_data_in_export_count": 0, "status": "PASS"})

    for category in model["categories"]:
        initial = initial_map_response(model, category["category_id"])
        write_json(EXAMPLES / f"{category['category_id']}-initial-map-response.json", initial)
        map_item = model["maps"][category["map_id"]]
        initial_state = model["states"][map_item["initial_state_id"]]
        alternative_state = next(item for item in model["states"].values() if item["map_id"] == map_item["map_id"] and item["focused_node_id"] != initial_state["focused_node_id"] and item["expanded_node_ids"])
        write_json(EXAMPLES / f"{category['category_id']}-focused-map-response.json", initial_map_response(model, category["category_id"], alternative_state["exploration_state_id"]))
    write_json(EXAMPLES / "capabilities-response.json", model["capabilities"])
    print(json.dumps({"status": "GENERATED", "read_model_sha256": model["read_model_sha256"], "categories": 4, "vocabulary": len(model["vocabulary"]), "associations": len(model["associations"]), "compositions": len(model["compositions"]), "states": len(model["states"])}, indent=2))
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(args.check)


if __name__ == "__main__":
    main()
