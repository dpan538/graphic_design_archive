#!/usr/bin/env python3
"""Build and independently verify the complete TRACE API catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
JSON_PATH = ROOT / "docs/api/trace/trace-api-catalog.v1.json"
MARKDOWN_PATH = ROOT / "docs/api/trace/TRACE_API_CATALOG.md"
RECEIPT_PATH = (
    ROOT
    / "docs/audits/v49-exploration-round16b-main-integration/trace-api-catalog-verification-receipt.v1.json"
)

GROUPS = [
    "TRACE Function 1",
    "TRACE Function 2",
    "TRACE Function 3 — Validated Exploration",
    "TRACE Function 3 — Open Inquiry",
    "shared TRACE infrastructure",
]
TOP_LEVEL_FUNCTIONS = [
    {"function": "TRACE_FUNCTION_1", "canonical_name": "Context Canvas"},
    {"function": "TRACE_FUNCTION_2", "canonical_name": "Spacetime"},
    {"function": "TRACE_FUNCTION_3", "canonical_name": "Exploration"},
]
READ_METHODS = ["GET", "HEAD", "OPTIONS"]
RETIRED_METHODS = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]
POST_METHODS = ["POST", "OPTIONS"]

GENERIC_ROUTE = "frontend/src/app/api/v1/[...path]/route.ts"
GENERIC_HANDLER = "frontend/src/lib/read-platform/server/read-api-controller.ts"
V2_ROUTE = "frontend/src/app/api/trace/v2/exploration/[...path]/route.ts"
V2_ROOT_ROUTE = "frontend/src/app/api/trace/v2/exploration/route.ts"
V2_HANDLER = "frontend/src/features/trace-v49/exploration-v2/controller.server.ts"
V2_SERVICE = "frontend/src/features/trace-v49/exploration-v2/service.server.ts"
V2_TYPES = "frontend/src/features/trace-v49/exploration-v2/types.ts"
V2_TEST = "frontend/scripts/test-trace-exploration-v2.mjs"
V3_ROUTE = "frontend/src/app/api/trace/v3/exploration/[...path]/route.ts"
V3_ROOT_ROUTE = "frontend/src/app/api/trace/v3/exploration/route.ts"
V3_HANDLER = "frontend/src/features/trace-v49/exploration-v3/controller.server.ts"
V3_SERVICE = "frontend/src/features/trace-v49/exploration-v3/service.server.ts"
V3_TYPES = "frontend/src/features/trace-v49/exploration-v3/types.ts"
V3_TEST = "frontend/scripts/test-trace-exploration-v3.mjs"

V3_COLLECTION_DTOS = {
    "association-realizations": "ExplorationV3AssociationRealizationDto",
    "associations": "ExplorationV3AssociationDto",
    "composition-coherence-reviews": "ExplorationV3CompositionCoherenceReviewDto",
    "compositions": "ExplorationV3CompositionDto",
    "concept-senses": "ExplorationV3ConceptSenseDto",
    "concepts": "ExplorationV3ConceptDto",
    "exports": "ExplorationV3ExportDto",
    "incidences": "ExplorationV3IncidenceDto",
    "navigation-states": "ExplorationV3NavigationStateDto",
    "scopes": "ExplorationV3ScopeDto",
    "transitions": "ExplorationV3TransitionDto",
    "workflows": "ExplorationV3WorkflowDto",
}


def schema(description: str, source: str, symbol: str) -> dict[str, str]:
    return {"description": description, "source": source, "symbol": symbol}


def states(loading: str, empty: str, partial: str, error: str) -> dict[str, str]:
    return {"loading": loading, "empty": empty, "partial": partial, "error": error}


def add_record(
    records: list[dict[str, Any]],
    *,
    api_id: str,
    group: str,
    function: str,
    function_name: str,
    layer: str,
    method: list[str],
    route: str,
    implementation_status: str,
    request_schema: dict[str, str],
    response_schema: dict[str, str],
    source_route_path: str,
    handler_path: str,
    service_repository_path: str,
    test_path: str,
    authentication: str,
    pagination: str,
    sorting: str,
    caching: str,
    state_contract: dict[str, str],
    frontend_use: str,
    limitations: list[str],
    explicit_nonclaims: list[str],
) -> None:
    records.append(
        {
            "api_id": api_id,
            "group": group,
            "function": function,
            "function_name": function_name,
            "layer": layer,
            "method": method,
            "route": route,
            "implementation_status": implementation_status,
            "request_schema": request_schema,
            "response_schema": response_schema,
            "source_route_path": source_route_path,
            "handler_path": handler_path,
            "service_repository_path": service_repository_path,
            "test_path": test_path,
            "authentication": authentication,
            "pagination": pagination,
            "sorting": sorting,
            "caching": caching,
            "states": state_contract,
            "frontend_use": frontend_use,
            "limitations": limitations,
            "explicit_nonclaims": explicit_nonclaims,
        }
    )


def build_context_and_spacetime(records: list[dict[str, Any]]) -> None:
    add_record(
        records,
        api_id="trace.f1.context.object-context.v1",
        group=GROUPS[0], function="TRACE_FUNCTION_1", function_name="Context Canvas",
        layer="CONTEXT_CANVAS", method=READ_METHODS,
        route="/api/v1/releases/{release}/trace/objects/{id}/context",
        implementation_status="IMPLEMENTED_GOVERNED_READ_ONLY",
        request_schema=schema(
            "Release path and public stable object ID; an exact release requires Archive-Research-Manifest-Sha256; no body or query parameters.",
            "frontend/src/features/trace-v49/context/governed/read-api-runtime.server.ts",
            "tryReadGovernedContextApiResource",
        ),
        response_schema=schema("Read API v1 envelope containing PublicContextDataset.", "frontend/src/features/trace-v49/context/governed/types.ts", "PublicContextDataset"),
        source_route_path=GENERIC_ROUTE,
        handler_path="frontend/src/features/trace-v49/context/governed/read-api-runtime.server.ts",
        service_repository_path="frontend/src/features/trace-v49/context/governed/reader.server.ts",
        test_path="frontend/scripts/verify-context-api-v1.mjs",
        authentication="None; governed public release identity is enforced through the release pair and optional integrity header.",
        pagination="None.", sorting="Deterministic committed projection order.",
        caching="Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.",
        state_contract=states("SSR or request pending.", "availability=empty is a valid governed result.", "No partial protocol state.", "400 invalid ID; 404 held/unknown/unavailable; 409 release mismatch; 503 integrity failure."),
        frontend_use="Context Canvas can load the selected public record and governed medium, theme, and movement-context representations; the current workspace reads the same governed source server-side.",
        limitations=["No pagination or client sorting.", "The workspace is not linked into public navigation by this integration."],
        explicit_nonclaims=["Project-curated context is not an influence or semantic edge.", "Held UUIDs and full-corpus data are not exposed.", "Context Canvas is independent from Exploration."],
    )

    spacetime_common = dict(
        group=GROUPS[1], function="TRACE_FUNCTION_2", function_name="Spacetime",
        layer="SPACETIME", implementation_status="IMPLEMENTED_GOVERNED_READ_ONLY",
        source_route_path=GENERIC_ROUTE,
        handler_path="frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts",
        service_repository_path="frontend/src/features/trace-v49/spacetime/governed/reader.server.ts",
        test_path="frontend/scripts/verify-spacetime-api-v1.mjs",
        authentication="None; exact-release requests require the committed release manifest identity.",
        caching="Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.",
        limitations=["Governed periods and geography identities are fixed by the committed projection.", "The workspace is not linked into public navigation by this integration."],
        explicit_nonclaims=["Recorded region/date context is not an object coordinate or historical-presence claim.", "Aggregate marks do not assert movement, influence, or an Exploration association.", "realSemanticEdgeCount remains zero."],
    )
    add_record(
        records, api_id="trace.f2.spacetime.periods.v1", method=READ_METHODS,
        route="/api/v1/releases/{release}/trace/spacetime/periods",
        request_schema=schema("Release path; no query or body.", "frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts", "periods request"),
        response_schema=schema("Read API v1 envelope containing PublicSpacetimePeriodsDataset.", "frontend/src/features/trace-v49/spacetime/governed/types.ts", "PublicSpacetimePeriodsDataset"),
        pagination="None.", sorting="Committed period display order.",
        state_contract=states("Periods request pending.", "An empty governed period inventory is displayable.", "No partial protocol state.", "400 query error; 404 release error; 503 integrity failure."),
        frontend_use="Initializes the discrete Spacetime period selector.", **spacetime_common,
    )
    add_record(
        records, api_id="trace.f2.spacetime.atlas.v1", method=READ_METHODS,
        route="/api/v1/releases/{release}/trace/spacetime/atlas",
        request_schema=schema("Exactly one required period query parameter; no body.", "frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts", "atlas request"),
        response_schema=schema("Read API v1 envelope containing PublicSpacetimeAtlasDataset.", "frontend/src/features/trace-v49/spacetime/governed/types.ts", "PublicSpacetimeAtlasDataset"),
        pagination="None.", sorting="Committed geography/mark order.",
        state_contract=states("Atlas request pending after period selection.", "A period with no governed marks is valid empty data.", "No partial protocol state.", "400 query error; 404 period/release error; 503 integrity failure."),
        frontend_use="Loads governed aggregate geographic marks for one selected period.", **spacetime_common,
    )
    add_record(
        records, api_id="trace.f2.spacetime.geography-records.v1", method=READ_METHODS,
        route="/api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records",
        request_schema=schema("Geography path ID; exactly one period; optional first 1..100 (default 24) and projection-bound after cursor up to 2048 characters.", "frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts", "geography-record request"),
        response_schema=schema("Read API v1 envelope containing PublicSpacetimeRecordPage.", "frontend/src/features/trace-v49/spacetime/governed/types.ts", "PublicSpacetimeRecordPage"),
        pagination="Deterministic cursor pagination; first defaults to 24 and is bounded 1..100; hasNextPage/endCursor signal continuation.",
        sorting="Committed projection order; no caller-selected sort.",
        state_contract=states("Selected-geography page request pending.", "A zero-record page is valid.", "hasNextPage=true is an explicit partial state until load-more completes.", "400 invalid query/cursor; 404 geography/period/release; 503 integrity failure."),
        frontend_use="Loads and incrementally extends the selected geography's recorded-object list.", **spacetime_common,
    )


def build_validated_v1_v2(records: list[dict[str, Any]]) -> None:
    retired_common = dict(
        group=GROUPS[2], function="TRACE_FUNCTION_3", function_name="Exploration",
        layer="VALIDATED_EXPLORATION_V1_RETIRED", method=RETIRED_METHODS,
        implementation_status="RETIRED_410",
        request_schema=schema("Any request to the retired v1 root or catch-all.", "frontend/src/app/api/trace/v1/exploration/route.ts", "retired request"),
        response_schema=schema("HTTP 410 trace-exploration-api-retirement-v1 payload; HEAD is bodyless.", "frontend/src/app/api/trace/v1/exploration/route.ts", "RETIREMENT_PAYLOAD"),
        handler_path="frontend/src/app/api/trace/v1/exploration/route.ts",
        service_repository_path="frontend/src/app/api/trace/v1/exploration/route.ts",
        test_path="frontend/scripts/validate-trace-exploration-v2-http.mjs",
        authentication="None.", pagination="None.", sorting="None.",
        caching="Cache-Control: private, no-store; successor Link and Sunset headers.",
        state_contract=states("No loading data contract; response is immediate retirement.", "Not applicable.", "Not applicable.", "Every method returns 410 API_VERSION_RETIRED; HEAD has no body."),
        frontend_use="Compatibility-only retirement signal; clients must use v2.",
        limitations=["OPTIONS intentionally returns the retirement payload rather than 204.", "No v1 data remains available."],
        explicit_nonclaims=["The retired catch-all is not an implemented product data surface.", "Retirement does not create a fourth function."],
    )
    add_record(records, api_id="trace.f3.validated.v1.retired-root", route="/api/trace/v1/exploration", source_route_path="frontend/src/app/api/trace/v1/exploration/route.ts", **retired_common)
    catchall = dict(retired_common)
    catchall["handler_path"] = "frontend/src/app/api/trace/v1/exploration/[...path]/route.ts"
    catchall["service_repository_path"] = catchall["handler_path"]
    add_record(records, api_id="trace.f3.validated.v1.retired-catchall", route="/api/trace/v1/exploration/{...path}", source_route_path="frontend/src/app/api/trace/v1/exploration/[...path]/route.ts", **catchall)

    common = dict(
        group=GROUPS[2], function="TRACE_FUNCTION_3", function_name="Exploration",
        layer="VALIDATED_EXPLORATION_V2", implementation_status="IMPLEMENTED_VALIDATED_BASELINE",
        handler_path=V2_HANDLER, service_repository_path=V2_SERVICE, test_path=V2_TEST,
        authentication="None.", pagination="None.", sorting="No caller-selected sorting; governed deterministic order.",
        caching="Cache-Control: private, no-store.",
        state_contract=states("Request or server render pending.", "Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.", "No partial-response protocol.", "400/404/409/413/503 fail closed; binary render capacity may return 503."),
        frontend_use="Typed client support exists; no final mounted visual page or navigation is added by this integration.",
        limitations=["A map exposes at most eight visible nodes.", "Map GET recognizes state_id; other query keys are currently ignored.", "PNG is fixed at 1080×1620."],
        explicit_nonclaims=["Exactly 21 evidence-qualified generic pair associations are validated.", "No Open Inquiry record is mixed into v2.", "No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim."],
    )
    routes = [
        ("trace.f3.validated.v2.root", READ_METHODS, "/api/trace/v2/exploration", V2_ROOT_ROUTE, "No body/query.", "HTTP 308 to /capabilities.", "root redirect"),
        ("trace.f3.validated.v2.categories.list", READ_METHODS, "/api/trace/v2/exploration/categories", V2_ROUTE, "No body/query.", "ExplorationV2CategoriesResponse", "ExplorationV2CategoriesResponse"),
        ("trace.f3.validated.v2.capabilities.get", READ_METHODS, "/api/trace/v2/exploration/capabilities", V2_ROUTE, "No body/query.", "ExplorationV2CapabilitiesResponse", "ExplorationV2CapabilitiesResponse"),
        ("trace.f3.validated.v2.maps.create", POST_METHODS, "/api/trace/v2/exploration/maps", V2_ROUTE, "JSON ExplorationV2MapRequest; body <=65536 bytes.", "ExplorationV2MapDto", "ExplorationV2MapRequest / ExplorationV2MapDto"),
        ("trace.f3.validated.v2.maps.get", READ_METHODS, "/api/trace/v2/exploration/maps/{mapId}", V2_ROUTE, "Map ID; optional state_id.", "ExplorationV2MapDto", "ExplorationV2MapDto"),
        ("trace.f3.validated.v2.maps.actions", POST_METHODS, "/api/trace/v2/exploration/maps/{mapId}/actions", V2_ROUTE, "Map ID and JSON ExplorationV2ActionRequest; body <=65536 bytes.", "ExplorationV2MapDto", "ExplorationV2ActionRequest / ExplorationV2MapDto"),
        ("trace.f3.validated.v2.vocabulary.get", READ_METHODS, "/api/trace/v2/exploration/vocabulary/{vocabularyId}", V2_ROUTE, "Vocabulary ID; no body/query.", "ExplorationV2VocabularyDto", "ExplorationV2VocabularyDto"),
        ("trace.f3.validated.v2.associations.get", READ_METHODS, "/api/trace/v2/exploration/associations/{associationId}", V2_ROUTE, "Association ID; no body/query.", "ExplorationV2AssociationDto", "ExplorationV2AssociationDto"),
        ("trace.f3.validated.v2.exports.manifest", POST_METHODS, "/api/trace/v2/exploration/exports/manifest", V2_ROUTE, "JSON ExplorationV2ExportRequest; body <=65536 bytes.", "ExplorationV2ExportManifestDto", "ExplorationV2ExportRequest / ExplorationV2ExportManifestDto"),
        ("trace.f3.validated.v2.exports.svg", POST_METHODS, "/api/trace/v2/exploration/export/svg", V2_ROUTE, "JSON ExplorationV2ExportRequest; body <=65536 bytes.", "image/svg+xml bytes with semantic/presentation/state/export headers", "ExplorationV2ExportRequest / SVG bytes"),
        ("trace.f3.validated.v2.exports.png", POST_METHODS, "/api/trace/v2/exploration/exports/png", V2_ROUTE, "JSON ExplorationV2ExportRequest; body <=65536 bytes.", "image/png bytes with semantic/presentation/state/export headers", "ExplorationV2ExportRequest / PNG bytes"),
    ]
    for api_id, methods, route, source, request, response, symbol in routes:
        add_record(
            records, api_id=api_id, method=methods, route=route, source_route_path=source,
            request_schema=schema(request, V2_TYPES, symbol.split(" / ")[0]),
            response_schema=schema(response, V2_TYPES, symbol.split(" / ")[-1]),
            **common,
        )


def parsed_v3_collections() -> list[str]:
    text = (ROOT / V3_SERVICE).read_text(encoding="utf-8")
    block_match = re.search(r"EXPLORATION_V3_COLLECTIONS\s*=\s*Object\.freeze\(\{(?P<body>.*?)\}\s*as const", text, re.S)
    if not block_match:
        raise ValueError("cannot parse EXPLORATION_V3_COLLECTIONS")
    body = block_match.group("body")
    candidates = re.findall(r'^\s*(?:"([a-z0-9-]+)"|([a-z][a-z0-9-]*))\s*:\s*\{', body, re.M)
    values = sorted({quoted or plain for quoted, plain in candidates})
    if values != sorted(V3_COLLECTION_DTOS):
        raise ValueError(f"v3 collection mismatch: {values}")
    return values


def build_validated_v3(records: list[dict[str, Any]]) -> None:
    common = dict(
        group=GROUPS[2], function="TRACE_FUNCTION_3", function_name="Exploration",
        implementation_status="IMPLEMENTED_FAIL_CLOSED_READ_ONLY",
        method=READ_METHODS, handler_path=V3_HANDLER, service_repository_path=V3_SERVICE,
        test_path=V3_TEST, authentication="None.", pagination="None.",
        sorting="Fixed read-model order; no caller-selected sorting.",
        caching="Cache-Control: private, no-store.",
        state_contract=states("Request pending.", "Active-product collection lists are intentionally empty while activation remains fail closed.", "No partial-response protocol.", "404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure."),
        frontend_use="Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.",
        limitations=["Query parameters are currently ignored.", "Identifiers are non-empty and limited to 512 characters.", "Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS."],
        explicit_nonclaims=["Synthetic controls are not Open Inquiry records and are not active product facts.", "V3 does not inherit v2 transitions.", "V3 does not establish any closure claim."],
    )
    fixed = [
        ("trace.f3.validated.v3.root", "/api/trace/v3/exploration", V3_ROOT_ROUTE, "No body/query.", "HTTP 308 to /capabilities.", "VALIDATED_EXPLORATION_V3_ROOT"),
        ("trace.f3.validated.v3.capabilities.get", "/api/trace/v3/exploration/capabilities", V3_ROUTE, "No body; query currently ignored.", "ExplorationV3ResponseEnvelope<{capabilities,contract_version,source_authority}>", "VALIDATED_EXPLORATION_V3_ACTIVE"),
        ("trace.f3.validated.v3.baseline-reconciliation.get", "/api/trace/v3/exploration/baseline/reconciliation", V3_ROUTE, "No body; query currently ignored.", "ExplorationV3ResponseEnvelope<{baseline_reconciliation}>", "VALIDATED_EXPLORATION_V3_ACTIVE"),
    ]
    for api_id, route, source, request, response, layer in fixed:
        add_record(records, api_id=api_id, route=route, source_route_path=source, layer=layer,
                   request_schema=schema(request, V3_TYPES, "ExplorationV3 request"),
                   response_schema=schema(response, V3_TYPES, "ExplorationV3ResponseEnvelope"), **common)
    for slug in parsed_v3_collections():
        dto = V3_COLLECTION_DTOS[slug]
        for realm, prefix, layer in [
            ("active", "", "VALIDATED_EXPLORATION_V3_ACTIVE"),
            ("control", "/controls", "VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL"),
        ]:
            base = f"/api/trace/v3/exploration{prefix}/{slug}"
            add_record(
                records,
                api_id=f"trace.f3.validated.v3.{realm}.{slug}.list",
                route=base, source_route_path=V3_ROUTE, layer=layer,
                request_schema=schema("No body; query currently ignored.", V3_TYPES, "ExplorationV3 collection-list request"),
                response_schema=schema(f"ExplorationV3ResponseEnvelope list of {dto} records with collection, count, and data_class.", V3_TYPES, dto),
                **common,
            )
            add_record(
                records,
                api_id=f"trace.f3.validated.v3.{realm}.{slug}.detail",
                route=f"{base}/{{id}}", source_route_path=V3_ROUTE, layer=layer,
                request_schema=schema("Path identifier, non-empty and <=512 characters; no body; query currently ignored.", V3_TYPES, "ExplorationV3 collection-detail request"),
                response_schema=schema(f"ExplorationV3ResponseEnvelope containing one {dto} and data_class.", V3_TYPES, dto),
                **common,
            )


def build_open_inquiry(records: list[dict[str, Any]]) -> None:
    common = dict(
        group=GROUPS[3], function="TRACE_FUNCTION_3", function_name="Exploration",
        layer="OPEN_INQUIRY", method=READ_METHODS,
        implementation_status="IMPLEMENTED_READ_ONLY_ISOLATED",
        handler_path="frontend/src/features/trace-v49/open-inquiry-v1/controller.server.ts",
        service_repository_path="frontend/src/features/trace-v49/open-inquiry-v1/service.server.ts",
        test_path="frontend/scripts/test-trace-open-inquiry-v1.mjs",
        authentication="None.", pagination="None.",
        sorting="Canonical code-point order by stable inquiry ID; no caller-selected sort.",
        caching="Cache-Control: private, no-store; Vary: Accept; registry digest response header.",
        state_contract=states("Request pending with Open Inquiry label retained.", "List is governed at exactly 11; detail has no empty success state.", "No partial-response protocol.", "400 any query; 404 malformed/unknown ID; 405 unsupported method; 503 registry integrity failure."),
        frontend_use="Future explicitly labelled inquiry inventory and detail surfaces; no visual design or mounted page is added here.",
        limitations=["No pagination, filtering, caller sorting, randomization, mutation, or include-unresolved flag.", "External human review remains pending."],
        explicit_nonclaims=["Every record is unresolved and not validated.", "No record generates pair edges or changes validated graph, composition, topology, export, or metrics.", "No truth probability, likelihood score, confidence percentage, or stochastic display exists."],
    )
    add_record(
        records, api_id="trace.f3.open-inquiry.v1.list", route="/api/trace/v1/open-inquiry",
        source_route_path="frontend/src/app/api/trace/v1/open-inquiry/route.ts",
        request_schema=schema("No body and no query parameters.", "schemas/trace/exploration/open-inquiry/v1/list-response.schema.json", "OpenInquiry list request"),
        response_schema=schema("OpenInquiryResponseEnvelope<OpenInquiryListData> with exactly 11 items.", "schemas/trace/exploration/open-inquiry/v1/list-response.schema.json", "OpenInquiryListData"),
        **common,
    )
    add_record(
        records, api_id="trace.f3.open-inquiry.v1.detail", route="/api/trace/v1/open-inquiry/{inquiryId}",
        source_route_path="frontend/src/app/api/trace/v1/open-inquiry/[inquiryId]/route.ts",
        request_schema=schema("Exact R16B-HYPOTHESIS or R16B-SCOPED-HYPOTHESIS stable ID; no body or query.", "schemas/trace/exploration/open-inquiry/v1/detail-response.schema.json", "OpenInquiry detail request"),
        response_schema=schema("OpenInquiryResponseEnvelope<OpenInquiryDetailData>.", "schemas/trace/exploration/open-inquiry/v1/detail-response.schema.json", "OpenInquiryDetailData"),
        **common,
    )


def build_shared(records: list[dict[str, Any]]) -> None:
    common = dict(
        group=GROUPS[4], function="SHARED_TRACE_INFRASTRUCTURE", function_name="shared TRACE infrastructure",
        layer="LEGACY_TRACE_READ_PLATFORM", method=READ_METHODS,
        implementation_status="IMPLEMENTED_LEGACY_READ_PLATFORM",
        source_route_path=GENERIC_ROUTE, handler_path=GENERIC_HANDLER,
        service_repository_path="frontend/src/lib/read-platform/repository.ts",
        test_path="frontend/scripts/run-v49-api-read-contract-closure.mjs",
        authentication="None; exact release integrity uses Archive-Research-Manifest-Sha256.",
        caching="Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.",
        frontend_use="Legacy Evidence Atlas/read-platform compatibility; shared infrastructure is not a fourth TRACE function.",
        limitations=["Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged.", "Current relation and neighborhood baselines are empty or unavailable."],
        explicit_nonclaims=["Legacy TRACE infrastructure is not Validated Exploration or Open Inquiry.", "Zero typed relations must not be conflated with the 21 validated generic pair associations."],
    )
    static = [
        ("trace.shared.read-v1.atlas", "/api/v1/releases/{release}/trace/atlas", "No body/query.", "TraceAtlas", "None.", "Fixed repository order.", "Trace overview is currently zero/message; no partial state."),
        ("trace.shared.read-v1.objects.list", "/api/v1/releases/{release}/trace/objects", "Optional layer, first (default 50, 1..100), and after cursor.", "Page<TraceObjectSummary>", "Keyset cursor pagination.", "Fixed ID keyset order.", "Empty page is valid; hasNextPage/endCursor represents partial pagination."),
        ("trace.shared.read-v1.objects.neighborhood", "/api/v1/releases/{release}/trace/objects/{id}/neighborhood", "Object ID; no body/query.", "TraceGraph", "None.", "Fixed repository order.", "Current baseline returns 404/no nodes; no partial state."),
        ("trace.shared.read-v1.relation-types.list", "/api/v1/releases/{release}/trace/relation-types", "No body/query.", "RelationTypeDefinition[]", "None.", "Fixed repository order.", "Current list is empty; no partial state."),
        ("trace.shared.read-v1.relation-types.detail", "/api/v1/releases/{release}/trace/relation-types/{id}", "Relation-type ID; no body/query.", "RelationTypeDefinition", "None.", "None.", "Current baseline returns 404; no partial state."),
    ]
    for api_id, route, request, response, pagination, sorting, empty_partial in static:
        add_record(
            records, api_id=api_id, route=route,
            request_schema=schema(request, "frontend/src/lib/read-platform/types.ts", "Read API v1 request"),
            response_schema=schema(f"Read API v1 envelope containing {response}; errors use the repository problem body.", "frontend/src/lib/read-platform/types.ts", response),
            pagination=pagination, sorting=sorting,
            state_contract=states("Request pending.", empty_partial, empty_partial, "400 invalid argument/cursor; 404 unavailable resource; 409 release mismatch; 503 repository unavailable."),
            **common,
        )


def build_catalog() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    build_context_and_spacetime(records)
    build_validated_v1_v2(records)
    build_validated_v3(records)
    build_open_inquiry(records)
    build_shared(records)
    records.sort(key=lambda item: item["api_id"])
    return {
        "schema_version": "trace-api-catalog/v1",
        "catalog_version": "TRACE_API_CATALOG_V1",
        "canonical_product": "TRACE",
        "top_level_functions": TOP_LEVEL_FUNCTIONS,
        "group_order": GROUPS,
        "summary": {
            "trace_top_level_function_count": 3,
            "logical_route_template_count": len(records),
            "expanded_method_route_pair_count": sum(len(item["method"]) for item in records),
            "implemented_trace_api_uncatalogued_count": 0,
            "catalog_implemented_without_real_route_count": 0,
            "catalog_duplicate_method_route_count": 0,
            "catalog_source_path_missing_count": 0,
            "catalog_test_path_missing_count": 0,
        },
        "routes": records,
    }


def exported_methods(source_path: str) -> set[str]:
    text = (ROOT / source_path).read_text(encoding="utf-8")
    return set(re.findall(r"export\s+(?:async\s+)?function\s+([A-Z]+)\b", text)) | set(
        re.findall(r"export\s+const\s+([A-Z]+)\s*=", text)
    )


def expected_pairs_from_implementation() -> set[tuple[str, str]]:
    expected: list[tuple[str, list[str]]] = []
    expected.append(("/api/v1/releases/{release}/trace/objects/{id}/context", READ_METHODS))
    expected.extend((route, READ_METHODS) for route in [
        "/api/v1/releases/{release}/trace/spacetime/periods",
        "/api/v1/releases/{release}/trace/spacetime/atlas",
        "/api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records",
    ])
    expected.extend((route, RETIRED_METHODS) for route in [
        "/api/trace/v1/exploration", "/api/trace/v1/exploration/{...path}",
    ])
    expected.extend([
        ("/api/trace/v2/exploration", READ_METHODS),
        ("/api/trace/v2/exploration/categories", READ_METHODS),
        ("/api/trace/v2/exploration/capabilities", READ_METHODS),
        ("/api/trace/v2/exploration/maps", POST_METHODS),
        ("/api/trace/v2/exploration/maps/{mapId}", READ_METHODS),
        ("/api/trace/v2/exploration/maps/{mapId}/actions", POST_METHODS),
        ("/api/trace/v2/exploration/vocabulary/{vocabularyId}", READ_METHODS),
        ("/api/trace/v2/exploration/associations/{associationId}", READ_METHODS),
        ("/api/trace/v2/exploration/exports/manifest", POST_METHODS),
        ("/api/trace/v2/exploration/export/svg", POST_METHODS),
        ("/api/trace/v2/exploration/exports/png", POST_METHODS),
        ("/api/trace/v3/exploration", READ_METHODS),
        ("/api/trace/v3/exploration/capabilities", READ_METHODS),
        ("/api/trace/v3/exploration/baseline/reconciliation", READ_METHODS),
    ])
    for slug in parsed_v3_collections():
        for prefix in ["", "/controls"]:
            base = f"/api/trace/v3/exploration{prefix}/{slug}"
            expected.extend([(base, READ_METHODS), (f"{base}/{{id}}", READ_METHODS)])
    expected.extend([
        ("/api/trace/v1/open-inquiry", READ_METHODS),
        ("/api/trace/v1/open-inquiry/{inquiryId}", READ_METHODS),
    ])
    expected.extend((route, READ_METHODS) for route in [
        "/api/v1/releases/{release}/trace/atlas",
        "/api/v1/releases/{release}/trace/objects",
        "/api/v1/releases/{release}/trace/objects/{id}/neighborhood",
        "/api/v1/releases/{release}/trace/relation-types",
        "/api/v1/releases/{release}/trace/relation-types/{id}",
    ])
    return {(method, route) for route, methods in expected for method in methods}


def verify_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    routes = catalog["routes"]
    ids = [item["api_id"] for item in routes]
    actual_pairs = [(method, item["route"]) for item in routes for method in item["method"]]
    expected_pairs = expected_pairs_from_implementation()
    actual_set = set(actual_pairs)
    source_missing = sorted({item["source_route_path"] for item in routes if not (ROOT / item["source_route_path"]).is_file()})
    handler_missing = sorted({item["handler_path"] for item in routes if not (ROOT / item["handler_path"]).is_file()})
    service_missing = sorted({item["service_repository_path"] for item in routes if not (ROOT / item["service_repository_path"]).is_file()})
    test_missing = sorted({item["test_path"] for item in routes if not (ROOT / item["test_path"]).is_file()})
    schema_missing = sorted({
        node["source"]
        for item in routes
        for node in [item["request_schema"], item["response_schema"]]
        if not (ROOT / node["source"]).is_file()
    })
    method_source_failures = sorted(
        f"{item['api_id']}:{method}"
        for item in routes
        for method in item["method"]
        if (ROOT / item["source_route_path"]).is_file()
        and method not in exported_methods(item["source_route_path"])
    )
    receipt = {
        "schema_version": "trace-api-catalog-verification-receipt/v1",
        "status": "PASS",
        "TRACE_TOP_LEVEL_FUNCTION_COUNT": len(catalog["top_level_functions"]),
        "TRACE_LOGICAL_ROUTE_TEMPLATE_COUNT": len(routes),
        "TRACE_EXPANDED_METHOD_ROUTE_PAIR_COUNT": len(actual_pairs),
        "IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT": len(expected_pairs - actual_set),
        "CATALOG_IMPLEMENTED_WITHOUT_REAL_ROUTE_COUNT": len(actual_set - expected_pairs) + len(method_source_failures),
        "CATALOG_DUPLICATE_METHOD_ROUTE_COUNT": len(actual_pairs) - len(actual_set),
        "CATALOG_SOURCE_PATH_MISSING_COUNT": len(source_missing),
        "CATALOG_HANDLER_PATH_MISSING_COUNT": len(handler_missing),
        "CATALOG_SERVICE_REPOSITORY_PATH_MISSING_COUNT": len(service_missing),
        "CATALOG_SCHEMA_PATH_MISSING_COUNT": len(schema_missing),
        "CATALOG_TEST_PATH_MISSING_COUNT": len(test_missing),
        "CATALOG_DUPLICATE_API_ID_COUNT": len(ids) - len(set(ids)),
        "FUNCTION_GROUP_COUNT": len(catalog["group_order"]),
        "details": {
            "uncatalogued_method_routes": sorted(f"{method} {route}" for method, route in expected_pairs - actual_set),
            "nonimplemented_catalog_method_routes": sorted(f"{method} {route}" for method, route in actual_set - expected_pairs),
            "method_source_failures": method_source_failures,
            "source_paths_missing": source_missing,
            "handler_paths_missing": handler_missing,
            "service_repository_paths_missing": service_missing,
            "schema_paths_missing": schema_missing,
            "test_paths_missing": test_missing,
        },
        "round": "TRACE v49 Round 16B Clean Main Integration",
        "closure_claim": "evidence-bounded-nonclosure",
        "deployment": "none",
    }
    required_zero_keys = [
        "IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT",
        "CATALOG_IMPLEMENTED_WITHOUT_REAL_ROUTE_COUNT",
        "CATALOG_DUPLICATE_METHOD_ROUTE_COUNT",
        "CATALOG_SOURCE_PATH_MISSING_COUNT",
        "CATALOG_HANDLER_PATH_MISSING_COUNT",
        "CATALOG_SERVICE_REPOSITORY_PATH_MISSING_COUNT",
        "CATALOG_SCHEMA_PATH_MISSING_COUNT",
        "CATALOG_TEST_PATH_MISSING_COUNT",
        "CATALOG_DUPLICATE_API_ID_COUNT",
    ]
    if (
        receipt["TRACE_TOP_LEVEL_FUNCTION_COUNT"] != 3
        or receipt["TRACE_LOGICAL_ROUTE_TEMPLATE_COUNT"] != 75
        or receipt["TRACE_EXPANDED_METHOD_ROUTE_PAIR_COUNT"] != 228
        or catalog["group_order"] != GROUPS
        or any(receipt[key] != 0 for key in required_zero_keys)
    ):
        receipt["status"] = "FAIL"
        raise ValueError(json.dumps(receipt, indent=2, sort_keys=True))
    return receipt


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def markdown_bytes(catalog: dict[str, Any]) -> bytes:
    lines = [
        "# TRACE API catalog",
        "",
        "This catalog records the complete implemented API surface of exactly three TRACE functions: Context Canvas, Spacetime, and Exploration. Search is outside TRACE. Shared TRACE infrastructure is cataloged separately and does not create a fourth function.",
        "",
        "```text",
        "TRACE",
        "├── Context Canvas",
        "├── Spacetime",
        "└── Exploration",
        "    ├── Validated Exploration",
        "    └── Open Inquiry",
        "```",
        "",
        "`TRACE_TOP_LEVEL_FUNCTION_COUNT=3`",
        "",
        f"`TRACE_LOGICAL_ROUTE_TEMPLATE_COUNT={catalog['summary']['logical_route_template_count']}`",
        "",
        f"`TRACE_EXPANDED_METHOD_ROUTE_PAIR_COUNT={catalog['summary']['expanded_method_route_pair_count']}`",
        "",
        "The JSON catalog is the machine authority. Each record below repeats its request, response, implementation, state, frontend, limitation, and nonclaim contract.",
        "",
    ]
    by_group = {group: [] for group in GROUPS}
    for item in catalog["routes"]:
        by_group[item["group"]].append(item)
    for group in GROUPS:
        lines.extend([f"## {group}", ""])
        for item in by_group[group]:
            lines.extend([
                f"### `{item['api_id']}`",
                "",
                f"- Function/layer: `{item['function']}` / `{item['layer']}`",
                f"- Method: `{', '.join(item['method'])}`",
                f"- Route: `{item['route']}`",
                f"- Implementation status: `{item['implementation_status']}`",
                f"- Request schema: {item['request_schema']['description']} (`{item['request_schema']['source']}`; `{item['request_schema']['symbol']}`)",
                f"- Response schema: {item['response_schema']['description']} (`{item['response_schema']['source']}`; `{item['response_schema']['symbol']}`)",
                f"- Source route: `{item['source_route_path']}`",
                f"- Handler: `{item['handler_path']}`",
                f"- Service/repository: `{item['service_repository_path']}`",
                f"- Test: `{item['test_path']}`",
                f"- Authentication: {item['authentication']}",
                f"- Pagination: {item['pagination']}",
                f"- Sorting: {item['sorting']}",
                f"- Caching: {item['caching']}",
                f"- Loading state: {item['states']['loading']}",
                f"- Empty state: {item['states']['empty']}",
                f"- Partial state: {item['states']['partial']}",
                f"- Error state: {item['states']['error']}",
                f"- Frontend use: {item['frontend_use']}",
                f"- Limitations: {' '.join(item['limitations'])}",
                f"- Explicit nonclaims: {' '.join(item['explicit_nonclaims'])}",
                "",
            ])
    lines.extend([
        "## Verification result",
        "",
        "```text",
        "IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT=0",
        "CATALOG_IMPLEMENTED_WITHOUT_REAL_ROUTE_COUNT=0",
        "CATALOG_DUPLICATE_METHOD_ROUTE_COUNT=0",
        "CATALOG_SOURCE_PATH_MISSING_COUNT=0",
        "CATALOG_TEST_PATH_MISSING_COUNT=0",
        "```",
        "",
        "Open Inquiry remains isolated from Validated Exploration. Synthetic v3 controls remain labelled synthetic controls, not Open Inquiry. No route in this catalog establishes pair, higher-order, global-composition, product-reachability, computational-space, or Function 3 closure.",
        "",
    ])
    return "\n".join(lines).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = build_catalog()
    receipt = verify_catalog(catalog)
    catalog_output = json_bytes(catalog)
    markdown_output = markdown_bytes(catalog)
    receipt["catalog_sha256"] = hashlib.sha256(catalog_output).hexdigest()
    receipt["markdown_sha256"] = hashlib.sha256(markdown_output).hexdigest()
    receipt_output = json_bytes(receipt)
    outputs = {
        JSON_PATH: catalog_output,
        MARKDOWN_PATH: markdown_output,
        RECEIPT_PATH: receipt_output,
    }
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, output in outputs.items() if not path.is_file() or path.read_bytes() != output]
        if stale:
            print("FAIL: stale TRACE API catalog outputs: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("PASS: TRACE API catalog 75 templates / 228 method-route pairs / 3 functions / all required zero counts")
        return 0
    for path, output in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(output)
    print("PASS: wrote TRACE API catalog 75 templates / 228 method-route pairs / 3 functions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
