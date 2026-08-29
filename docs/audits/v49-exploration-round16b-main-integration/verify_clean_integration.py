#!/usr/bin/env python3
"""Fail-closed TRACE Round 16B clean-integration and isolation verifier.

The verifier is intentionally read-only. It derives the required integration
metrics from the canonical Open Inquiry registry, Validated Exploration v2
read model, v3 fail-closed read model, API catalog, function tree, and bounded
handoff source manifest. It writes no receipt or generated repository file.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import runpy
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[3]

REGISTRY_PATH = (
    ROOT / "frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json"
)
VALIDATED_V2_PATH = (
    ROOT / "frontend/generated/trace-exploration-v2/production-read-model.json"
)
VALIDATED_V2_EXAMPLES_PATH = ROOT / "docs/api/trace-exploration-v2-examples.json"
V3_READ_MODEL_PATH = ROOT / "frontend/generated/trace-exploration-v3/read-model.json"
CATALOG_PATH = ROOT / "docs/api/trace/trace-api-catalog.v1.json"
CATALOG_BUILDER_PATH = (
    ROOT
    / "docs/audits/v49-exploration-round16b-main-integration/build_trace_api_catalog.py"
)
FUNCTION_TREE_PATH = (
    ROOT / "docs/frontend/trace-v49-handoff/trace-function-tree.v1.json"
)
SOURCE_MANIFEST_PATH = ROOT / "docs/frontend/trace-v49-handoff/SOURCE_MANIFEST.json"

EXPECTED_VALIDATED_V2_SHA256 = (
    "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9"
)
EXPECTED_REGISTRY_FILE_SHA256 = (
    "46d03365a3405e8475fccdce0c2e8f42884a4e0a6a9088f7043ac3a022183b77"
)
EXPECTED_REGISTRY_RECORDS_SHA256 = (
    "4a8109c9f4b4296522aead0227331ee5e117fa26a40a9782605192adccdcb44e"
)
EXPECTED_CATALOG_SHA256 = (
    "6373e77a6a6670383e0a952c7b78a8036fc9b11954212ebb2a92dc10df87fcd7"
)
EXPECTED_FUNCTION_TREE_SHA256 = (
    "eac8776c6aa79a1c9a81b69f835da5cc54188f3a93074dcaa665f96b02611ba3"
)

EXPECTED_SOURCE_BINDINGS = (
    {
        "path": (
            "docs/audits/v49-exploration-higher-order-association-closure-round16b/"
            "raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv"
        ),
        "sha256": "f16deeca67663b05262640cba1512bb46acb0a36ffe8dcae006fd45dc475bed3",
        "bytes": 13_131,
        "record_count": 9,
    },
    {
        "path": (
            "docs/audits/v49-exploration-higher-order-association-closure-round16b/"
            "raw/scoped-association-hypothesis-ledger-shard-2-v1.tsv"
        ),
        "sha256": "5b7e04bde8fc0c91f7d141f0ecdccf23579394dafba21e33e91ad512f9ab5a4d",
        "bytes": 4_544,
        "record_count": 2,
    },
)

CLOSURE_FLAGS = {
    "PAIR_ASSOCIATION_CLOSURE": False,
    "HIGHER_ORDER_ASSOCIATION_CLOSURE": False,
    "GLOBAL_COMPOSITION_COHERENCE_CLOSURE": False,
    "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE": False,
    "COMPUTATIONAL_SPACE_CLOSURE": False,
    "FUNCTION3_CLOSURE": False,
}

REQUIRED_RECORD_BOUNDARY = {
    "epistemic_status": "UNRESOLVED_OPEN_INQUIRY",
    "validated_relation": False,
    "counts_as_validated": False,
    "eligible_for_validated_graph": False,
    "eligible_for_validated_composition": False,
    "may_generate_pair_edges": False,
    "may_modify_validated_topology": False,
    "display_eligible": True,
    "display_layer": "OPEN_INQUIRY",
    "default_in_validated_results": False,
    "active": False,
    "external_human_review_status": "PENDING",
    "product_eligible": False,
    "product_path": None,
    "participant_order_meaningful": False,
    "relation_roles_asserted": False,
    "pair_projection_policy": "NONE",
    "implicit_pair_projection_count": 0,
}

DISALLOWED_PROBABILITY_FIELDS = {
    "truth_probability",
    "probability_true",
    "likelihood_score",
    "confidence_percentage",
}

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
INQUIRY_ID_PATTERN = re.compile(r"^R16B-(?:SCOPED-)?HYPOTHESIS:[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    """One deterministic integration invariant failed."""


def fail(message: str) -> NoReturn:
    raise VerificationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def reject_json_constant(value: str) -> NoReturn:
    fail(f"non-finite JSON constant is forbidden: {value}")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    require(path.is_file(), f"required JSON file missing: {path.relative_to(ROOT)}")
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"required JSON is not UTF-8: {path.relative_to(ROOT)}: {error}")
    try:
        return json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_json_constant,
        )
    except (json.JSONDecodeError, VerificationError) as error:
        fail(f"invalid JSON: {path.relative_to(ROOT)}: {error}")


def as_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def as_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{label} must be an array")
    return value


def as_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    return value


def require_sha256(value: Any, label: str) -> str:
    text = as_string(value, label)
    require(bool(SHA256_PATTERN.fullmatch(text)), f"{label} is not lowercase SHA-256")
    return text


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    require(path.is_file(), f"required file missing: {path.relative_to(ROOT)}")
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)
    elif isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from iter_strings(child)


def count_disallowed_fields(value: Any) -> int:
    if isinstance(value, list):
        return sum(count_disallowed_fields(child) for child in value)
    if not isinstance(value, dict):
        return 0
    return sum(
        (1 if key in DISALLOWED_PROBABILITY_FIELDS else 0)
        + count_disallowed_fields(child)
        for key, child in value.items()
    )


def repository_path(relative: Any, label: str) -> Path:
    text = as_string(relative, label)
    candidate = Path(text)
    require(not candidate.is_absolute(), f"{label} must be repository-relative")
    require(".." not in candidate.parts, f"{label} may not traverse outside repository")
    path = (ROOT / candidate).resolve()
    require(path.is_relative_to(ROOT.resolve()), f"{label} escaped repository")
    return path


def validate_registry() -> tuple[dict[str, Any], set[str], dict[str, int]]:
    require(
        file_sha256(REGISTRY_PATH) == EXPECTED_REGISTRY_FILE_SHA256,
        "canonical Open Inquiry registry file SHA-256 changed",
    )
    registry = as_object(load_json(REGISTRY_PATH), "Open Inquiry registry")
    require(
        set(registry) == {
            "api_version",
            "canonical_serialization",
            "closure_flags",
            "counts",
            "input_bindings",
            "records",
            "records_sha256",
            "registry_version",
        },
        "Open Inquiry registry keys differ",
    )
    require(registry["api_version"] == "trace-open-inquiry/v1", "registry API version differs")
    require(
        registry["registry_version"] == "trace-open-inquiry-registry/v1",
        "registry version differs",
    )
    require(
        registry["canonical_serialization"]
        == "UTF8_SORTED_KEYS_COMPACT_JSON_RECORD_DIGEST",
        "registry canonical serialization differs",
    )
    require(registry["closure_flags"] == CLOSURE_FLAGS, "registry closure flags differ")
    require(
        registry["input_bindings"] == list(EXPECTED_SOURCE_BINDINGS),
        "registry input bindings differ from canonical Round 16B sources",
    )

    for index, binding in enumerate(EXPECTED_SOURCE_BINDINGS):
        path = repository_path(binding["path"], f"input_bindings[{index}].path")
        data = path.read_bytes()
        require(data.endswith(b"\n"), f"source ledger lacks final LF: {binding['path']}")
        require(b"\r" not in data, f"source ledger contains CR bytes: {binding['path']}")
        require(len(data) == binding["bytes"], f"source ledger byte count differs: {binding['path']}")
        require(sha256_bytes(data) == binding["sha256"], f"source ledger hash differs: {binding['path']}")
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8")), delimiter="\t"))
        require(len(rows) == binding["record_count"], f"source ledger row count differs: {binding['path']}")
        require(rows and "record_sha256" in rows[0], f"source ledger digest header missing: {binding['path']}")
        for row_number, source_row in enumerate(rows, start=2):
            source_digest = source_row.get("record_sha256", "")
            scalar_material = {
                key: value for key, value in source_row.items() if key != "record_sha256"
            }
            require(
                canonical_sha256(scalar_material) == source_digest,
                f"source row digest mismatch: {binding['path']}:{row_number}",
            )

    records = as_list(registry["records"], "registry.records")
    require(len(records) == 11, "Open Inquiry registry must contain exactly 11 records")
    record_ids: list[str] = []
    inquiry_fingerprints: set[str] = {
        "OPEN_INQUIRY",
        "UNRESOLVED_OPEN_INQUIRY",
    }
    arity_counts = {2: 0, 3: 0, 4: 0, 5: 0}
    projection_total = 0
    boundary_violation_count = 0

    for index, candidate in enumerate(records):
        record = as_object(candidate, f"registry.records[{index}]")
        inquiry_id = as_string(record.get("inquiry_id"), f"records[{index}].inquiry_id")
        require(
            bool(INQUIRY_ID_PATTERN.fullmatch(inquiry_id)),
            f"records[{index}].inquiry_id differs from stable-ID policy",
        )
        record_ids.append(inquiry_id)
        inquiry_fingerprints.add(inquiry_id)
        inquiry_fingerprints.add(as_string(record.get("inquiry_key"), f"records[{index}].inquiry_key"))

        arity = record.get("arity")
        require(arity in arity_counts, f"records[{index}].arity is outside 2..5")
        participants = as_list(record.get("participants"), f"records[{index}].participants")
        require(len(participants) == arity, f"records[{index}] participant count differs from arity")
        arity_counts[arity] += 1

        for key, expected in REQUIRED_RECORD_BOUNDARY.items():
            if record.get(key) != expected:
                boundary_violation_count += 1
        projection_value = record.get("implicit_pair_projection_count")
        require(isinstance(projection_value, int), f"records[{index}] projection count is not an integer")
        projection_total += projection_value

        identity = record.get("inquiry_only_association_identity")
        if identity is not None:
            identity_object = as_object(identity, f"records[{index}].inquiry_only_association_identity")
            inquiry_fingerprints.add(
                as_string(identity_object.get("association_id"), f"records[{index}].association_id")
            )
            inquiry_fingerprints.add(
                as_string(
                    identity_object.get("association_revision_id"),
                    f"records[{index}].association_revision_id",
                )
            )

        record_digest = require_sha256(record.get("record_sha256"), f"records[{index}].record_sha256")
        inquiry_fingerprints.add(record_digest)
        material = {key: value for key, value in record.items() if key != "record_sha256"}
        require(
            canonical_sha256(material) == record_digest,
            f"records[{index}].record_sha256 mismatch",
        )

    require(len(set(record_ids)) == 11, "Open Inquiry stable IDs are not unique")
    require(record_ids == sorted(record_ids), "Open Inquiry records are not in deterministic ID order")
    records_digest = require_sha256(registry["records_sha256"], "registry.records_sha256")
    require(records_digest == EXPECTED_REGISTRY_RECORDS_SHA256, "registry records digest differs")
    require(canonical_sha256(records) == records_digest, "registry records digest mismatch")

    counts = as_object(registry["counts"], "registry.counts")
    expected_counts = {
        "scoped_higher_order_hypothesis_count": 11,
        "arity_2_count": 3,
        "arity_3_count": 6,
        "arity_4_count": 1,
        "arity_5_count": 1,
        "governed_inquiry_only_association_identity_count": 4,
        "ungoverned_hypothesis_count": 7,
        "active_pending_review_count": 0,
        "implicit_pair_projection_count": 0,
    }
    require(counts == expected_counts, "registry declared counts differ")
    require(arity_counts == {2: 3, 3: 6, 4: 1, 5: 1}, "registry computed arity counts differ")
    require(projection_total == 0, "registry computed implicit pair projection count differs")

    metrics = {
        "OPEN_INQUIRY_REGISTRY_COUNT": len(records),
        "OPEN_INQUIRY_IMPLICIT_PAIR_PROJECTION_COUNT": projection_total,
        "OPEN_INQUIRY_BOUNDARY_VIOLATION_COUNT": boundary_violation_count,
        "OPEN_INQUIRY_FORBIDDEN_PROBABILITY_FIELD_COUNT": count_disallowed_fields(registry),
    }
    return registry, inquiry_fingerprints, metrics


def contains_inquiry_material(value: Any, fingerprints: set[str]) -> bool:
    for text in iter_strings(value):
        if text in fingerprints:
            return True
        if "R16B-HYPOTHESIS:" in text or "R16B-SCOPED-HYPOTHESIS:" in text:
            return True
    return False


def invalid_references(values: Any, allowed: set[str], label: str) -> list[str]:
    items = as_list(values, label)
    result: list[str] = []
    for index, value in enumerate(items):
        text = as_string(value, f"{label}[{index}]")
        if text not in allowed:
            result.append(text)
    return result


def validate_validated_layers(
    inquiry_fingerprints: set[str],
) -> tuple[dict[str, Any], dict[str, int]]:
    require(
        file_sha256(VALIDATED_V2_PATH) == EXPECTED_VALIDATED_V2_SHA256,
        "canonical Validated Exploration v2 read-model SHA-256 changed",
    )
    model = as_object(load_json(VALIDATED_V2_PATH), "Validated Exploration v2 model")
    vocabulary = as_list(model.get("vocabulary"), "v2.vocabulary")
    vocabulary_ids = {
        as_string(as_object(item, "v2 vocabulary record").get("vocabulary_id"), "vocabulary_id")
        for item in vocabulary
    }
    require(len(vocabulary_ids) == len(vocabulary), "v2 vocabulary IDs are not unique")

    associations = as_list(model.get("associations"), "v2.associations")
    association_ids: set[str] = set()
    association_leak_count = 0
    topology_mutation_count = 0
    for index, candidate in enumerate(associations):
        association = as_object(candidate, f"v2.associations[{index}]")
        association_id = as_string(association.get("association_id"), f"v2.associations[{index}].association_id")
        require(association_id not in association_ids, f"duplicate v2 association ID: {association_id}")
        association_ids.add(association_id)
        endpoints = as_list(
            association.get("endpoint_vocabulary_ids"),
            f"v2.associations[{index}].endpoint_vocabulary_ids",
        )
        if len(endpoints) != 2 or len(set(endpoints)) != 2:
            topology_mutation_count += 1
        topology_mutation_count += len(
            [endpoint for endpoint in endpoints if endpoint not in vocabulary_ids]
        )
        if association.get("generic_association_only") is not True:
            topology_mutation_count += 1
        if contains_inquiry_material(association, inquiry_fingerprints):
            association_leak_count += 1

    capabilities = as_object(model.get("capabilities"), "v2.capabilities")
    metric_contamination_count = int(capabilities.get("association_count") != len(associations))
    metric_contamination_count += int(capabilities.get("association_count") != 21)
    metric_contamination_count += int(contains_inquiry_material(capabilities, inquiry_fingerprints))

    compositions = as_object(model.get("compositions"), "v2.compositions")
    composition_leak_count = 0
    for composition_id, candidate in compositions.items():
        composition = as_object(candidate, f"v2.compositions[{composition_id}]")
        bad_associations = invalid_references(
            composition.get("association_ids"),
            association_ids,
            f"v2.compositions[{composition_id}].association_ids",
        )
        bad_nodes = invalid_references(
            composition.get("node_ids"),
            vocabulary_ids,
            f"v2.compositions[{composition_id}].node_ids",
        )
        if bad_associations or contains_inquiry_material(composition, inquiry_fingerprints):
            composition_leak_count += 1
        topology_mutation_count += len(bad_nodes)

    states = as_object(model.get("states"), "v2.states")
    for state_id, candidate in states.items():
        state = as_object(candidate, f"v2.states[{state_id}]")
        composition_id = as_string(
            state.get("composition_id"), f"v2.states[{state_id}].composition_id"
        )
        if composition_id not in compositions:
            topology_mutation_count += 1
            continue
        composition = as_object(compositions[composition_id], f"v2.compositions[{composition_id}]")
        composition_associations = set(
            as_list(composition.get("association_ids"), f"composition[{composition_id}].association_ids")
        )
        composition_nodes = set(
            as_list(composition.get("node_ids"), f"composition[{composition_id}].node_ids")
        )
        visible_associations = as_list(
            state.get("visible_association_ids"),
            f"v2.states[{state_id}].visible_association_ids",
        )
        visible_nodes = as_list(state.get("visible_node_ids"), f"v2.states[{state_id}].visible_node_ids")
        topology_mutation_count += len(
            [item for item in visible_associations if item not in association_ids or item not in composition_associations]
        )
        topology_mutation_count += len(
            [item for item in visible_nodes if item not in vocabulary_ids or item not in composition_nodes]
        )
        if contains_inquiry_material(state, inquiry_fingerprints):
            topology_mutation_count += 1

    v3 = as_object(load_json(V3_READ_MODEL_PATH), "Exploration v3 model")
    active_product = as_object(v3.get("active_product"), "v3.active_product")
    active_associations = as_list(active_product.get("associations"), "v3.active_product.associations")
    active_compositions = as_list(active_product.get("compositions"), "v3.active_product.compositions")
    association_leak_count += sum(
        contains_inquiry_material(item, inquiry_fingerprints) for item in active_associations
    )
    composition_leak_count += sum(
        contains_inquiry_material(item, inquiry_fingerprints) for item in active_compositions
    )

    examples = as_object(load_json(VALIDATED_V2_EXAMPLES_PATH), "Validated Exploration v2 examples")
    example_capabilities = as_object(examples.get("capabilities_response"), "examples.capabilities_response")
    metric_contamination_count += int(example_capabilities.get("association_count") != 21)
    metric_contamination_count += int(
        contains_inquiry_material(example_capabilities, inquiry_fingerprints)
    )

    manifest = as_object(examples.get("export_manifest"), "examples.export_manifest")
    export_leak_count = int(contains_inquiry_material(manifest, inquiry_fingerprints))
    manifest_associations = as_list(manifest.get("associations"), "examples.export_manifest.associations")
    manifest_association_ids = [
        as_string(as_object(item, "example export association").get("association_id"), "export association ID")
        for item in manifest_associations
    ]
    require(
        len(manifest_association_ids) == len(set(manifest_association_ids)),
        "example export association IDs are not unique",
    )
    manifest_association_id_set = set(manifest_association_ids)
    export_leak_count += int(manifest.get("association_count") != len(manifest_associations))
    provenance_summary = as_object(
        manifest.get("provenance_summary"), "examples.export_manifest.provenance_summary"
    )
    export_leak_count += int(
        provenance_summary.get("association_count") != len(manifest_associations)
    )
    export_leak_count += int(provenance_summary.get("generic_association_only") is not True)
    tree = as_object(manifest.get("plain_text_tree"), "examples.export_manifest.plain_text_tree")
    for key in ("tree_association_ids", "visible_association_ids"):
        export_leak_count += len(
            invalid_references(
                tree.get(key),
                manifest_association_id_set,
                f"examples.export_manifest.{key}",
            )
        )

    active_exports = as_list(active_product.get("exports"), "v3.active_product.exports")
    export_leak_count += sum(
        contains_inquiry_material(item, inquiry_fingerprints) for item in active_exports
    )

    v2_source_paths = sorted(
        (ROOT / "frontend/src/features/trace-v49/exploration-v2").glob("*.ts")
    ) + sorted((ROOT / "frontend/src/app/api/trace/v2/exploration").rglob("*.ts"))
    forbidden_import_fragments = (
        "open-inquiry",
        "open_inquiry",
        "openInquiry",
        "/api/trace/v1/open-inquiry",
    )
    for source_path in v2_source_paths:
        text = source_path.read_text(encoding="utf-8")
        if any(fragment in text for fragment in forbidden_import_fragments):
            export_leak_count += 1

    metrics = {
        "OPEN_INQUIRY_LEAK_INTO_VALIDATED_ASSOCIATION_COUNT": association_leak_count,
        "OPEN_INQUIRY_LEAK_INTO_VALIDATED_COMPOSITION_COUNT": composition_leak_count,
        "OPEN_INQUIRY_VALIDATED_TOPOLOGY_MUTATION_COUNT": topology_mutation_count,
        "OPEN_INQUIRY_VALIDATED_EXPORT_LEAK_COUNT": export_leak_count,
        "OPEN_INQUIRY_VALIDATED_METRIC_CONTAMINATION_COUNT": metric_contamination_count,
        "VALIDATED_PAIR_ASSOCIATION_COUNT": len(associations),
    }
    return model, metrics


def load_catalog_builder() -> Mapping[str, Any]:
    require(CATALOG_BUILDER_PATH.is_file(), "TRACE API catalog builder is missing")
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        return runpy.run_path(
            str(CATALOG_BUILDER_PATH),
            run_name="trace_api_catalog_builder_for_clean_integration_verification",
        )
    finally:
        sys.dont_write_bytecode = previous


def validate_catalog_and_tree() -> tuple[dict[str, Any], dict[str, int]]:
    require(file_sha256(CATALOG_PATH) == EXPECTED_CATALOG_SHA256, "canonical API catalog SHA-256 changed")
    catalog = as_object(load_json(CATALOG_PATH), "TRACE API catalog")
    builder = load_catalog_builder()
    build_catalog = builder.get("build_catalog")
    verify_catalog = builder.get("verify_catalog")
    require(callable(build_catalog) and callable(verify_catalog), "catalog builder API is unavailable")
    rebuilt = build_catalog()
    require(catalog == rebuilt, "TRACE API catalog is stale against its deterministic builder")
    receipt = as_object(verify_catalog(catalog), "catalog verification result")

    tree = as_object(load_json(FUNCTION_TREE_PATH), "TRACE function tree")
    require(
        file_sha256(FUNCTION_TREE_PATH) == EXPECTED_FUNCTION_TREE_SHA256,
        "canonical function-tree SHA-256 changed",
    )
    functions = as_list(tree.get("functions"), "function_tree.functions")
    expected_functions = [
        ("TRACE_FUNCTION_1", "Context Canvas"),
        ("TRACE_FUNCTION_2", "Spacetime"),
        ("TRACE_FUNCTION_3", "Exploration"),
    ]
    actual_functions = [
        (
            as_string(as_object(item, "function tree item").get("function"), "function ID"),
            as_string(as_object(item, "function tree item").get("name"), "function name"),
        )
        for item in functions
    ]
    require(actual_functions == expected_functions, "canonical TRACE top-level function tree differs")
    require(tree.get("trace_top_level_function_count") == 3, "function-tree declared count differs")
    require(tree.get("closure_flags") == CLOSURE_FLAGS, "function-tree closure flags differ")
    require(tree.get("frontend_visual_design_implemented") is False, "function tree claims visual design")
    require(tree.get("deployment_performed") is False, "function tree claims deployment")

    catalog_api_ids = {
        as_string(as_object(item, "catalog route").get("api_id"), "catalog api_id")
        for item in as_list(catalog.get("routes"), "catalog.routes")
    }
    references: list[str] = []

    def collect_references(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                collect_references(child)
            return
        if not isinstance(value, dict):
            return
        if "api_references" in value:
            for index, reference in enumerate(as_list(value["api_references"], "api_references")):
                references.append(as_string(reference, f"api_references[{index}]"))
        for child in value.values():
            collect_references(child)

    collect_references(tree)
    dangling = sorted(set(references) - catalog_api_ids)
    require(len(references) == len(set(references)), "function tree contains duplicate API references")

    metrics = {
        "TRACE_TOP_LEVEL_FUNCTION_COUNT": len(functions),
        "IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT": int(
            receipt.get("IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT", -1)
        ),
        "FUNCTION_TREE_DANGLING_API_REFERENCE_COUNT": len(dangling),
        "API_CATALOG_STALE_COUNT": 0,
        "FUNCTION_TREE_STALE_COUNT": 0,
    }
    return catalog, metrics


def digest_manifest_rows(rows: Sequence[Any], label: str) -> str:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, candidate in enumerate(rows):
        row = as_object(candidate, f"{label}[{index}]")
        require(
            set(row) == {"bytes", "path", "required", "role", "sha256"},
            f"{label}[{index}] keys differ",
        )
        relative = as_string(row.get("path"), f"{label}[{index}].path")
        repository_path(relative, f"{label}[{index}].path")
        require(relative not in seen, f"duplicate manifest path in {label}: {relative}")
        seen.add(relative)
        require(row.get("required") is True, f"{label}[{index}] is not required")
        require(
            isinstance(row.get("bytes"), int) and row["bytes"] >= 0,
            f"{label}[{index}].bytes is invalid",
        )
        require_sha256(row.get("sha256"), f"{label}[{index}].sha256")
        as_string(row.get("role"), f"{label}[{index}].role")
        normalized.append(row)
    return canonical_sha256(normalized)


def verify_bound_rows(rows: Sequence[Any], label: str) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    mismatches: list[str] = []
    for index, candidate in enumerate(rows):
        row = as_object(candidate, f"{label}[{index}]")
        relative = as_string(row.get("path"), f"{label}[{index}].path")
        path = repository_path(relative, f"{label}[{index}].path")
        if not path.is_file():
            missing.append(relative)
            continue
        data = path.read_bytes()
        if len(data) != row.get("bytes") or sha256_bytes(data) != row.get("sha256"):
            mismatches.append(relative)
    return sorted(missing), sorted(mismatches)


def validate_source_manifest(catalog: dict[str, Any]) -> dict[str, int]:
    manifest = as_object(load_json(SOURCE_MANIFEST_PATH), "frontend handoff source manifest")
    require(
        manifest.get("schema_version") == "trace-frontend-handoff-source-manifest/v1",
        "handoff source-manifest schema differs",
    )
    require(manifest.get("trace_top_level_function_count") == 3, "source-manifest function count differs")
    require(manifest.get("closure_flags") == CLOSURE_FLAGS, "source-manifest closure flags differ")
    require(manifest.get("external_human_review_status") == "PENDING", "source-manifest review status differs")
    require(manifest.get("frontend_visual_design_implemented") is False, "source manifest claims visual design")
    require(manifest.get("deployment_performed") is False, "source manifest claims deployment")

    sources = as_list(manifest.get("sources"), "source_manifest.sources")
    handoff_files = as_list(manifest.get("handoff_files"), "source_manifest.handoff_files")
    require(
        manifest.get("required_source_count") == len(sources),
        "source-manifest required source count differs",
    )
    require(
        manifest.get("required_handoff_source_file_count") == len(handoff_files),
        "source-manifest handoff file count differs",
    )
    require(
        digest_manifest_rows(sources, "source_manifest.sources") == manifest.get("sources_sha256"),
        "source-manifest aggregate source digest differs",
    )
    require(
        digest_manifest_rows(handoff_files, "source_manifest.handoff_files")
        == manifest.get("handoff_files_sha256"),
        "source-manifest aggregate handoff digest differs",
    )

    source_missing, source_mismatches = verify_bound_rows(sources, "source_manifest.sources")
    handoff_missing, handoff_mismatches = verify_bound_rows(
        handoff_files, "source_manifest.handoff_files"
    )

    catalog_binding = as_object(manifest.get("catalog_binding"), "source_manifest.catalog_binding")
    require(catalog_binding.get("path") == str(CATALOG_PATH.relative_to(ROOT)), "catalog binding path differs")
    require(catalog_binding.get("sha256") == file_sha256(CATALOG_PATH), "catalog binding hash differs")
    catalog_summary = as_object(catalog.get("summary"), "catalog.summary")
    require(
        catalog_binding.get("logical_route_template_count")
        == catalog_summary.get("logical_route_template_count"),
        "catalog binding logical-route count differs",
    )
    require(
        catalog_binding.get("expanded_method_route_pair_count")
        == catalog_summary.get("expanded_method_route_pair_count"),
        "catalog binding expanded-route count differs",
    )

    return {
        "HANDOFF_REQUIRED_SOURCE_MISSING_COUNT": len(source_missing),
        "HANDOFF_SOURCE_HASH_MISMATCH_COUNT": len(source_mismatches),
        "HANDOFF_BOUND_HANDOFF_FILE_MISSING_COUNT": len(handoff_missing),
        "HANDOFF_BOUND_HANDOFF_FILE_HASH_MISMATCH_COUNT": len(handoff_mismatches),
    }


REQUIRED_METRICS = {
    "OPEN_INQUIRY_REGISTRY_COUNT": 11,
    "OPEN_INQUIRY_IMPLICIT_PAIR_PROJECTION_COUNT": 0,
    "OPEN_INQUIRY_LEAK_INTO_VALIDATED_ASSOCIATION_COUNT": 0,
    "OPEN_INQUIRY_LEAK_INTO_VALIDATED_COMPOSITION_COUNT": 0,
    "OPEN_INQUIRY_VALIDATED_TOPOLOGY_MUTATION_COUNT": 0,
    "OPEN_INQUIRY_VALIDATED_EXPORT_LEAK_COUNT": 0,
    "OPEN_INQUIRY_VALIDATED_METRIC_CONTAMINATION_COUNT": 0,
    "VALIDATED_PAIR_ASSOCIATION_COUNT": 21,
    "TRACE_TOP_LEVEL_FUNCTION_COUNT": 3,
    "IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT": 0,
    "FUNCTION_TREE_DANGLING_API_REFERENCE_COUNT": 0,
    "HANDOFF_REQUIRED_SOURCE_MISSING_COUNT": 0,
    "HANDOFF_SOURCE_HASH_MISMATCH_COUNT": 0,
}

AUXILIARY_ZERO_METRICS = (
    "OPEN_INQUIRY_BOUNDARY_VIOLATION_COUNT",
    "OPEN_INQUIRY_FORBIDDEN_PROBABILITY_FIELD_COUNT",
    "API_CATALOG_STALE_COUNT",
    "FUNCTION_TREE_STALE_COUNT",
    "HANDOFF_BOUND_HANDOFF_FILE_MISSING_COUNT",
    "HANDOFF_BOUND_HANDOFF_FILE_HASH_MISMATCH_COUNT",
)


def verify() -> dict[str, int]:
    _registry, inquiry_fingerprints, registry_metrics = validate_registry()
    _validated_model, isolation_metrics = validate_validated_layers(inquiry_fingerprints)
    catalog, catalog_metrics = validate_catalog_and_tree()
    handoff_metrics = validate_source_manifest(catalog)
    metrics = {
        **registry_metrics,
        **isolation_metrics,
        **catalog_metrics,
        **handoff_metrics,
    }

    for key, expected in REQUIRED_METRICS.items():
        require(key in metrics, f"required metric was not computed: {key}")
        require(metrics[key] == expected, f"{key}={metrics[key]} expected {expected}")
    for key in AUXILIARY_ZERO_METRICS:
        require(metrics.get(key) == 0, f"{key}={metrics.get(key)} expected 0")
    return metrics


def main() -> int:
    try:
        metrics = verify()
    except (OSError, UnicodeError, ValueError, TypeError, VerificationError) as error:
        print("CLEAN_INTEGRATION_VERIFICATION_STATUS=FAIL", file=sys.stderr)
        print(f"FAIL_REASON={error}", file=sys.stderr)
        return 1

    print("CLEAN_INTEGRATION_VERIFICATION_STATUS=PASS")
    for key in REQUIRED_METRICS:
        print(f"{key}={metrics[key]}")
    for key in AUXILIARY_ZERO_METRICS:
        print(f"{key}={metrics[key]}")
    print(f"OPEN_INQUIRY_REGISTRY_FILE_SHA256={file_sha256(REGISTRY_PATH)}")
    print(f"VALIDATED_EXPLORATION_V2_READ_MODEL_SHA256={file_sha256(VALIDATED_V2_PATH)}")
    print(f"TRACE_API_CATALOG_SHA256={file_sha256(CATALOG_PATH)}")
    print(f"TRACE_FUNCTION_TREE_SHA256={file_sha256(FUNCTION_TREE_PATH)}")
    print(f"HANDOFF_SOURCE_MANIFEST_SHA256={file_sha256(SOURCE_MANIFEST_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
