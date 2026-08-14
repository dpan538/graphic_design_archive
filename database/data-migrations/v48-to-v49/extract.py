#!/usr/bin/env python3
"""Strict, one-pass v48 Candidate JSON extractor for the Phase 2B rehearsal.

This program deliberately does not connect to PostgreSQL.  It turns the one
authoritative Candidate JSON into a reusable temporary staging bundle and a
complete field-occurrence ledger.  PostgreSQL sees only this bundle after every
preflight assertion has passed.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import re
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import urlparse, urlsplit


NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
UTF8 = "utf-8"
LOCATOR_RULES = {
    "url": ("direct_image", "held"),
    "viewerUrl": ("source_viewer", "held"),
    "evidenceImageUrl": ("direct_image", "internal"),
    "sourceViewerUrl": ("source_viewer", "held"),
}
KNOWN_OPTIONAL = (
    "/sourceObjectKey",
    "/sourceLocator",
    "/dateEnd",
    "/collectionEvidence",
    "/publicationRole",
    "/publicationGate",
    "/reviewGates/rightsReviewed",
    "/trace/tier",
    "/image/viewerUrl",
    "/image/evidenceImageUrl",
    "/image/sourceViewerUrl",
)
VISUAL_LOCATOR_KEY_PATTERN = re.compile(
    r"(url|uri|manifest|viewer|thumbnail|service|canvas|infojson|imageid)$", re.I
)


class PreflightError(RuntimeError):
    pass


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise PreflightError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


DECODER = json.JSONDecoder(object_pairs_hook=strict_object, parse_constant=reject_constant)


def c14n(value: Any) -> bytes:
    """gda-json-c14n-v1: sorted keys, source array order, no text rewriting."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode(UTF8)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def uuid5(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE, name))


def b64_bytes(payload: bytes) -> str:
    return base64.b64encode(payload).decode("ascii")


def b64_json(value: Any) -> str:
    return b64_bytes(c14n(value))


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def skip_ws(text: str, position: int) -> int:
    while position < len(text) and text[position] in " \t\r\n":
        position += 1
    return position


def parse_root_with_surfaces(
    text: str, on_surface: Callable[[int, dict[str, Any], bytes], None]
) -> dict[str, Any]:
    """Parse a root object while processing /surfaces elements one at a time."""
    position = skip_ws(text, 0)
    if position >= len(text) or text[position] != "{":
        raise PreflightError("ROOT_NOT_OBJECT")
    position += 1
    seen: set[str] = set()
    top: dict[str, Any] = {}
    surface_seen = False
    while True:
        position = skip_ws(text, position)
        if position >= len(text):
            raise PreflightError("UNTERMINATED_ROOT_OBJECT")
        if text[position] == "}":
            position += 1
            break
        key, position = DECODER.raw_decode(text, position)
        if not isinstance(key, str):
            raise PreflightError("NON_STRING_ROOT_KEY")
        if key in seen:
            raise PreflightError(f"DUPLICATE_ROOT_KEY:{key}")
        seen.add(key)
        position = skip_ws(text, position)
        if position >= len(text) or text[position] != ":":
            raise PreflightError(f"MISSING_ROOT_COLON:{key}")
        position = skip_ws(text, position + 1)
        if key != "surfaces":
            value, position = DECODER.raw_decode(text, position)
            top[key] = value
        else:
            if surface_seen or position >= len(text) or text[position] != "[":
                raise PreflightError("SURFACES_NOT_ARRAY")
            surface_seen = True
            position = skip_ws(text, position + 1)
            ordinal = 0
            while True:
                if position >= len(text):
                    raise PreflightError("UNTERMINATED_SURFACES_ARRAY")
                if text[position] == "]":
                    position += 1
                    break
                start = position
                value, position = DECODER.raw_decode(text, position)
                if not isinstance(value, dict):
                    raise PreflightError(f"SURFACE_NOT_OBJECT:{ordinal}")
                on_surface(ordinal, value, text[start:position].encode(UTF8))
                ordinal += 1
                position = skip_ws(text, position)
                if position >= len(text):
                    raise PreflightError("UNTERMINATED_SURFACES_ARRAY")
                if text[position] == ",":
                    position = skip_ws(text, position + 1)
                    continue
                if text[position] == "]":
                    position += 1
                    break
                raise PreflightError("MISSING_SURFACES_COMMA")
        position = skip_ws(text, position)
        if position >= len(text):
            raise PreflightError("UNTERMINATED_ROOT_OBJECT")
        if text[position] == ",":
            position += 1
            continue
        if text[position] == "}":
            position += 1
            break
        raise PreflightError("MISSING_ROOT_COMMA")
    if not surface_seen:
        raise PreflightError("MISSING_SURFACES")
    if skip_ws(text, position) != len(text):
        raise PreflightError("TRAILING_JSON_DATA")
    return top


def presence(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, str) and value == "":
        return "EMPTY_STRING"
    if isinstance(value, list) and not value:
        return "EMPTY_ARRAY"
    if isinstance(value, dict) and not value:
        return "EMPTY_OBJECT"
    return "PRESENT"


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise PreflightError(f"UNSUPPORTED_JSON_TYPE:{type(value)!r}")


def stable_set_hash(values: list[str]) -> str:
    return sha256(("\n".join(sorted(set(values))) + ("\n" if values else "")).encode(UTF8))


def visual_norm(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def visual_token(value: Any) -> str:
    return re.sub(r"^_+|_+$", "", re.sub(r"[^a-z0-9]+", "_", visual_norm(value).lower()))


def visual_bool_token(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "missing"
    return f"invalid:{type(value).__name__}"


def collect_phase1d_visual_locators(image: Any, base_role: str) -> list[dict[str, str]]:
    if not isinstance(image, dict):
        return []
    values: list[dict[str, str]] = []
    for key, value in image.items():
        if isinstance(value, str) and visual_norm(value) and VISUAL_LOCATOR_KEY_PATTERN.search(key):
            values.append({"role": f"{base_role}.{key}", "value": visual_norm(value)})
    return values


def phase1d_locator_shape(value: str) -> tuple[bool, str, str]:
    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower()
        return scheme in {"http", "https"} and bool(host), scheme or "invalid", host
    except (TypeError, ValueError):
        return False, "invalid", ""


def path_rule(relative_pointer: str) -> str:
    if relative_pointer == "/surfaceId":
        return "surface-identity"
    if relative_pointer == "/sourceRecordId":
        return "source-record-identity"
    if relative_pointer == "/trace/objectNodeId":
        return "trace-root-crosswalk"
    if relative_pointer == "/trace/tier":
        return "strict-tier-disposition"
    if relative_pointer == "/title":
        return "conservative-object-label"
    if relative_pointer == "/image":
        return "visual-reference-occurrence"
    if relative_pointer in {"/image/url", "/image/viewerUrl", "/image/evidenceImageUrl", "/image/sourceViewerUrl"}:
        return "visual-locator-occurrence"
    if relative_pointer == "/rights" or relative_pointer.startswith("/rights/"):
        return "rights-raw-fail-closed-observation"
    if relative_pointer.startswith("/folders/"):
        return "folder-membership-assignment"
    if relative_pointer in {"/trace/edgeIds", "/trace/edgeLabels", "/trace/branchIds"} or relative_pointer.startswith(("/trace/edgeIds/", "/trace/edgeLabels/", "/trace/branchIds/")):
        return "trace-arrays-held-no-zip"
    return "recursive-raw-snapshot-only"


def walk_occurrences(value: Any, pointer: str) -> Iterator[tuple[str, Any, str, str, int | None]]:
    value_type = json_type(value)
    value_presence = presence(value)
    array_ordinal: int | None = None
    yield pointer, value, value_type, value_presence, array_ordinal
    if isinstance(value, dict) and value:
        for key, child in value.items():
            child_pointer = pointer + "/" + pointer_escape(key)
            yield from walk_occurrences(child, child_pointer)
    elif isinstance(value, list) and value:
        for ordinal, child in enumerate(value):
            child_pointer = pointer + "/" + str(ordinal)
            for item in walk_occurrences(child, child_pointer):
                yield item[0], item[1], item[2], item[3], ordinal if item[0] == child_pointer else item[4]


class StageWriter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=False)
        self._files: dict[str, tuple[Any, csv.writer]] = {}
        self._jsonl = (root / "field-occurrence-ledger.jsonl").open("w", encoding=UTF8, newline="\n")
        self._surface = (root / "surface-row-ledger.tsv").open("w", encoding=UTF8, newline="")
        self._surface_writer = csv.writer(self._surface, delimiter="\t", lineterminator="\n")
        self._surface_writer.writerow([
            "source_ordinal", "json_pointer", "surface_id_exact", "source_record_id_exact",
            "record_semantic_sha256", "archive_object_uuid", "raw_record_uuid",
            "trace_root_legacy_id", "tier_presence", "tier_exact_value",
            "research_disposition", "workflow_reason", "import_disposition",
            "parse_error", "quarantine_id"
        ])
        self._trace = (root / "trace-delta-ledger.tsv").open("w", encoding=UTF8, newline="")
        self._trace_writer = csv.writer(self._trace, delimiter="\t", lineterminator="\n")
        self._trace_writer.writerow([
            "source_ordinal", "surface_id", "trace_root_legacy_id", "edge_id_count",
            "edge_label_count", "branch_id_count", "declared_edge_count", "pairability", "hold_reason"
        ])
        self._visual = (root / "visual-bundle-ledger.tsv").open("w", encoding=UTF8, newline="")
        self._visual_writer = csv.writer(self._visual, delimiter="\t", lineterminator="\n")
        self._visual_writer.writerow([
            "source_ordinal", "surface_id", "reference_bearing", "visual_reference_count",
            "locator_occurrence_count", "overall_disposition", "rights_axis", "policy_axis", "provider_axis"
        ])
        self._folder_pairs = (root / "surface-folder-pairs.tsv").open("w", encoding=UTF8, newline="")
        self._folder_writer = csv.writer(self._folder_pairs, delimiter="\t", lineterminator="\n")
        self._folder_writer.writerow(["folder_id", "surface_id", "surface_ordinal"])
        self._root = (root / "root-reconciliation-ledger.tsv").open("w", encoding=UTF8, newline="")
        self._root_writer = csv.writer(self._root, delimiter="\t", lineterminator="\n")
        self._root_writer.writerow([
            "json_pointer", "json_type", "presence_class", "literal_sha256",
            "mapping_rule_id", "raw_source_location"
        ])

    def table(self, name: str, header: list[str]) -> csv.writer:
        current = self._files.get(name)
        if current:
            return current[1]
        handle = (self.root / f"{name}.tsv").open("w", encoding=UTF8, newline="")
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        self._files[name] = (handle, writer)
        return writer

    def stream_source_asset(
        self,
        candidate: Path,
        asset_id: str,
        expected: dict[str, Any],
        logical_time: str,
    ) -> None:
        """Write the one large canonical-input field without a second full copy.

        TSV fields other than raw bytes are UUIDs, hashes, integers, or canonical
        JSON encoded as base64.  Base64 contains neither tabs nor newlines, so a
        single field can safely be streamed directly instead of accumulating a
        253 MB string for ``csv.writer``.
        """
        path = self.root / "source-assets.tsv"
        with path.open("w", encoding="ascii", newline="") as handle:
            handle.write(
                "source_asset_id\tauthority\tlogical_name_json_b64\tsha256\t"
                "byte_length\traw_bytes_b64\tmedia_type_json_b64\treceived_at\n"
            )
            handle.write(
                "\t".join([
                    asset_id,
                    "canonical_migration_input",
                    b64_json("generated/public_surfaces_prefreeze_candidate_v48.json"),
                    expected["candidateJsonSha256"],
                    str(expected["candidateJsonBytes"]),
                ])
            )
            handle.write("\t")
            carry = b""
            with candidate.open("rb") as source:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    chunk = carry + chunk
                    usable = len(chunk) - (len(chunk) % 3)
                    if usable:
                        handle.write(base64.b64encode(chunk[:usable]).decode("ascii"))
                    carry = chunk[usable:]
            if carry:
                handle.write(base64.b64encode(carry).decode("ascii"))
            handle.write("\t")
            handle.write(b64_json("application/json"))
            handle.write("\t" + logical_time + "\n")

    def occurrence(self, payload: dict[str, Any]) -> None:
        self._jsonl.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

    def close(self) -> None:
        self._jsonl.close()
        self._surface.close()
        self._trace.close()
        self._visual.close()
        self._folder_pairs.close()
        self._root.close()
        for handle, _writer in self._files.values():
            handle.close()


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--implementation-base-commit", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mapping = json.loads(args.mapping.read_text(encoding=UTF8), object_pairs_hook=strict_object)
    baseline = json.loads(args.baseline.read_text(encoding=UTF8), object_pairs_hook=strict_object)
    mapping_rules_by_id = {
        rule["ruleId"]: rule for rule in mapping.get("rules", [])
        if isinstance(rule, dict) and isinstance(rule.get("ruleId"), str)
    }
    if len(mapping_rules_by_id) != len(mapping.get("rules", [])):
        raise PreflightError("MAPPING_RULE_ID_DUPLICATE_OR_INVALID")
    if args.implementation_base_commit != baseline["implementationBaseCommit"]:
        raise PreflightError("IMPLEMENTATION_BASE_COMMIT_MISMATCH")
    if args.output_dir.exists():
        raise PreflightError(f"OUTPUT_DIR_ALREADY_EXISTS:{args.output_dir}")
    raw_candidate = args.candidate.read_bytes()
    candidate_size = len(raw_candidate)
    candidate_sha = sha256(raw_candidate)
    if candidate_size != baseline["candidateJsonBytes"] or candidate_sha != baseline["candidateJsonSha256"]:
        raise PreflightError("CANDIDATE_SHA_OR_SIZE_MISMATCH")
    try:
        candidate_text = raw_candidate.decode(UTF8, "strict")
    except UnicodeDecodeError as exc:
        raise PreflightError("CANDIDATE_NOT_UTF8") from exc
    del raw_candidate

    mapping_sha = sha256(args.mapping.read_bytes())
    extractor_sha = sha256(Path(__file__).read_bytes())
    bundle_binding_payload = {
        "candidateSha256": candidate_sha,
        "extractorSha256": extractor_sha,
        "implementationBaseCommit": args.implementation_base_commit,
        "mappingSha256": mapping_sha,
        "schemaNormalizedSha256": baseline["normalizedSchemaSha256"],
        "version": "gda-phase2b-bundle-binding-v1",
    }
    bundle_binding_sha = sha256(c14n(bundle_binding_payload))
    # This is persisted as raw.mapping_version.parser_version so a repeated
    # batch ID cannot silently reuse a different schema/extractor/base binding.
    bundle_binding = "gda-phase2b-bundle-binding-v1:" + bundle_binding_sha
    logical_time = mapping["logicalTimestampUtc"]
    asset_id = uuid5(f"urn:graphic-design-archive:v49:source-asset:{candidate_sha}")
    mapping_id = uuid5(f"urn:graphic-design-archive:v49:mapping:{mapping_sha}")
    batch_id = uuid5(
        "urn:graphic-design-archive:v49:migration-batch:"
        f"{candidate_sha}:{mapping_sha}:{baseline['normalizedSchemaSha256']}:{extractor_sha}:{args.implementation_base_commit}"
    )
    batch_token = "v48-json-only-" + candidate_sha[:16]

    writer = StageWriter(args.output_dir)
    records = writer.table("source-records", [
        "source_record_id", "record_ordinal", "legacy_source_record_id_json_b64",
        "raw_value_b64", "raw_fingerprint", "parsed_projection_b64", "semantic_sha256"
    ])
    field_literals = writer.table("field-literals", [
        "field_literal_id", "source_record_id", "json_pointer_json_b64",
        "occurrence_ordinal", "raw_value_b64"
    ])
    entities = writer.table("entities", ["entity_id", "entity_kind", "lifecycle_state", "created_at"])
    objects = writer.table("archive-objects", [
        "archive_object_id", "operational_semantics_version_json_b64", "preferred_label_json_b64", "legacy_surface_ledger_id"
    ])
    ledgers = writer.table("surface-ledgers", [
        "legacy_surface_ledger_id", "source_record_id", "canonical_input_asset_id", "input_ordinal",
        "surface_id_json_b64", "legacy_source_record_id_json_b64", "source_fingerprint",
        "import_disposition", "archive_object_id", "reason_code_json_b64"
    ])
    links = writer.table("object-source-links", ["archive_object_id", "source_record_id", "source_role"])
    identities = writer.table("legacy-identities", [
        "legacy_identity_id", "identity_kind", "namespace_json_b64", "legacy_id_json_b64", "created_at"
    ])
    folders_stage = writer.table("folders", [
        "folder_id", "folder_token_json_b64", "label_json_b64", "created_at"
    ])
    folder_assignments = writer.table("folder-assignments", [
        "canonical_assignment_id", "assignment_kind", "status",
        "created_at", "folder_id", "archive_object_id", "membership_role",
        "member_ordinal"
    ])
    resolutions = writer.table("legacy-resolutions", [
        "legacy_identity_resolution_id", "legacy_identity_id", "resolution_state",
        "target_archive_object_id", "target_source_record_id", "target_trace_node_id", "effective_from", "reason_code_json_b64"
    ])
    trace_nodes = writer.table("trace-nodes", [
        "trace_node_id", "canonical_key_json_b64", "label_json_b64", "entity_id", "node_type_json_b64", "created_at"
    ])
    object_trace = writer.table("object-trace-nodes", ["archive_object_id", "trace_node_id", "node_role_json_b64"])
    corpora = writer.table("corpora", ["corpus_id", "corpus_token_json_b64", "label_json_b64", "created_at"])
    corpus_versions = writer.table("corpus-versions", [
        "corpus_version_id", "corpus_id", "version_token_json_b64", "policy_version_json_b64", "policy_sha256", "population_frame_json_b64", "created_at"
    ])
    memberships = writer.table("corpus-memberships", [
        "corpus_version_id", "archive_object_id", "disposition", "reason_code_json_b64", "decided_by_json_b64", "decided_at"
    ])
    deltas = writer.table("held-deltas", [
        "fail_closed_delta_id", "migration_batch_id", "source_record_id", "expected_classification_json_b64",
        "actual_literal_json_b64", "reason_code_json_b64", "disposition", "recorded_at"
    ])
    visual_refs = writer.table("visual-references", [
        "external_visual_reference_id", "source_asset_id", "source_record_id", "pointer_json_b64",
        "occurrence_ordinal", "reference_fingerprint", "created_at"
    ])
    visual_bridges = writer.table("visual-bridges", [
        "object_visual_reference_id", "archive_object_id", "external_visual_reference_id", "reference_role", "ordinal", "acceptance_state"
    ])
    visual_locators = writer.table("visual-locators", [
        "visual_locator_id", "external_visual_reference_id", "locator_role", "source_asset_id", "source_record_id",
        "pointer_json_b64", "occurrence_ordinal", "visibility", "raw_locator_json_b64", "locator_fingerprint", "created_at"
    ])
    visual_dispositions = writer.table("visual-dispositions", [
        "legacy_surface_ledger_id", "source_fingerprint", "visual_reference_count", "locator_occurrence_count", "disposition_set_sha256", "classified_at"
    ])
    visual_classes = writer.table("visual-classifications", ["legacy_surface_ledger_id", "disposition"])
    rights_observations = writer.table("rights-observations", [
        "rights_observation_id", "external_visual_reference_id", "evidence_state",
        "observed_wording_json_b64", "observed_at"
    ])
    rights_assessments = writer.table("rights-assessments", [
        "rights_assessment_id", "external_visual_reference_id", "assessed_state",
        "reviewer_actor_json_b64", "rationale_json_b64", "assessed_at",
        "rights_observation_id", "evidence_role"
    ])
    policy_evaluations = writer.table("policy-evaluations", [
        "provider_policy_evaluation_id", "object_visual_reference_id", "evaluated_state",
        "evaluator_actor_json_b64", "evaluated_at"
    ])
    delivery_assessments = writer.table("delivery-assessments", [
        "delivery_assessment_id", "object_visual_reference_id", "delivery_mode",
        "reason_code", "assessor_actor_json_b64", "assessed_at",
        "rights_assessment_id", "rights_evidence_role", "provider_policy_evaluation_id"
    ])

    surface_ids: set[str] = set()
    source_ids: set[str] = set()
    trace_ids: set[str] = set()
    surface_object_ids: dict[str, str] = {}
    folder_surface_pairs: set[tuple[str, str]] = set()
    tier_counts: Counter[str] = Counter()
    image_locator_counts: Counter[str] = Counter()
    pointer_stats: dict[str, Counter[str]] = defaultdict(Counter)
    mapping_use: Counter[str] = Counter()
    field_literal_keys: set[tuple[str, str, int]] = set()
    visual_counts: Counter[str] = Counter()
    trace_mismatch = 0
    field_occurrence_count = 0
    field_literal_count = 0
    root_occurrence_count = 0
    unsafe_pairing_rows = 0
    phase1d_surface_ids: list[str] = []
    phase1d_source_ids: list[str] = []
    phase1d_raw_visual_sequence: list[str] = []
    phase1d_locator_sequence: list[str] = []
    phase1d_locator_values: list[str] = []
    phase1d_classified_sequence: list[str] = []
    corpus_id = uuid5("urn:graphic-design-archive:v49:corpus:strict-source-verified")
    corpus_version_id = uuid5(f"urn:graphic-design-archive:v49:corpus-version:{candidate_sha}:strict-source-verified-v1")
    policy_sha = sha256(b"gda-v49-strict-source-verified-corpus-policy-v1")

    def record_phase1d_visual_parity(ordinal: int, surface: dict[str, Any], surface_id: str, source_id: str) -> None:
        """Recompute the seven Phase 1D visual sequence/set hashes in-stream.

        This is deliberately the Phase 1D classifier's lexical algorithm, not
        the Phase 2B delivery mapping.  It proves that zero-rights migration
        preserves every raw visual bundle and locator occurrence without using
        URL normalization or any rights promotion.
        """
        phase_surface_id = visual_norm(surface.get("surfaceId"))
        phase_source_id = visual_norm(surface.get("sourceRecordId"))
        if phase_surface_id != surface_id or phase_source_id != source_id:
            raise PreflightError(f"IDENTITY_WHITESPACE_OR_VISUAL_PARITY_MISMATCH:{ordinal}")
        phase1d_surface_ids.append(phase_surface_id)
        phase1d_source_ids.append(phase_source_id)
        image = surface.get("image")
        rights = surface.get("rights")
        secondary_images = surface.get("images") if isinstance(surface.get("images"), list) else []
        rights_reviewed = (
            surface.get("reviewGates", {}).get("rightsReviewed")
            if isinstance(surface.get("reviewGates"), dict) else None
        )
        locator_rows = collect_phase1d_visual_locators(image, "image")
        for index, secondary in enumerate(secondary_images):
            locator_rows.extend(collect_phase1d_visual_locators(secondary, f"images[{index}]"))
        shaped: list[dict[str, Any]] = []
        for locator in locator_rows:
            valid_external, scheme, host = phase1d_locator_shape(locator["value"])
            shaped.append({**locator, "validExternal": valid_external, "scheme": scheme, "host": host})
        external = [item for item in shaped if item["validExternal"]]
        malformed = [item for item in shaped if not item["validExternal"]]
        for item in external:
            phase1d_locator_sequence.append(
                f"{ordinal}\t{phase_surface_id}\t{item['role']}\t{item['value']}"
            )
            phase1d_locator_values.append(item["value"])

        image_shape_valid = isinstance(image, dict)
        rights_shape_valid = isinstance(rights, dict)
        rights_state = visual_norm(rights.get("state")) if isinstance(rights, dict) else ""
        display_policy = visual_norm(rights.get("displayPolicy")) if isinstance(rights, dict) else ""
        rights_label = visual_norm(rights.get("label")) if isinstance(rights, dict) else ""
        license_label = visual_norm(image.get("licenseLabel")) if isinstance(image, dict) else ""
        rights_state = rights_state or "(missing)"
        display_policy = display_policy or "(missing)"
        structured_text = " ".join([rights_state, display_policy, rights_label, license_label]).lower()
        explicit_takedown = bool(re.search(r"(^|[^a-z])(takedown|withdrawn|suppressed|blocked_by_request)([^a-z]|$)", structured_text))
        explicit_conflict = bool(re.search(r"(^|[^a-z])(conflict|contradictory|disputed)([^a-z]|$)", structured_text))
        explicit_stale = bool(re.search(r"(^|[^a-z])(stale|expired|review_overdue)([^a-z]|$)", structured_text))
        candidate_only = bool(re.search(
            r"(candidate|required|review|unknown|unclear|unresolved|source_link_only|source_viewer)",
            visual_token(rights_state),
        ))
        evidence_present = bool(
            rights_label or license_label or rights_state != "(missing)" or display_policy != "(missing)"
        )
        rights_evidence_status = "NOT_APPLICABLE"
        if external:
            if explicit_takedown:
                rights_evidence_status = "TAKEDOWN_HOLD"
            elif explicit_conflict:
                rights_evidence_status = "CONFLICT"
            elif explicit_stale:
                rights_evidence_status = "STALE"
            elif evidence_present and not candidate_only:
                rights_evidence_status = "EVIDENCE_PRESENT"
            else:
                rights_evidence_status = "RIGHTS_UNKNOWN"
        reasons: list[str] = []
        if not image_shape_valid or not rights_shape_valid or malformed:
            reasons.append("MALFORMED_RAW_VISUAL_BUNDLE")
        if not external:
            reasons.append("NO_EXTERNAL_VISUAL_LOCATOR")
        if external and rights_evidence_status == "RIGHTS_UNKNOWN":
            reasons.append("LEGACY_RIGHTS_LABEL_IS_CANDIDATE_OR_UNREVIEWED")
        if external:
            reasons.extend(["NO_VERSIONED_PROVIDER_POLICY_IN_CANDIDATE", "NO_STABLE_PROVIDER_FK_IN_CANDIDATE"])
        if explicit_takedown:
            reasons.append("EXPLICIT_TAKEDOWN_TOKEN")
        if explicit_conflict:
            reasons.append("EXPLICIT_CONFLICT_TOKEN")
        if explicit_stale:
            reasons.append("EXPLICIT_STALE_TOKEN")
        if external:
            reasons.append("NO_POSITIVE_REMOTE_DISPLAY_PROOF")
        reasons.sort()
        overall = "EVIDENCE_PRESENT"
        if not image_shape_valid or not rights_shape_valid or malformed:
            overall = "MALFORMED"
        elif not external:
            overall = "NO_VISUAL_REFERENCE"
        elif explicit_takedown:
            overall = "TAKEDOWN_HOLD"
        elif explicit_conflict:
            overall = "CONFLICT"
        elif explicit_stale:
            overall = "STALE"
        elif rights_evidence_status == "RIGHTS_UNKNOWN":
            overall = "RIGHTS_UNKNOWN"
        elif rights_evidence_status == "EVIDENCE_PRESENT":
            overall = "POLICY_UNKNOWN"
        raw_bundle = {
            "image": image if image is not None else None,
            "images": secondary_images,
            "rights": rights if rights is not None else None,
            "rightsReviewed": rights_reviewed if rights_reviewed is not None else None,
        }
        phase1d_raw_visual_sequence.append(
            f"{ordinal}\t{phase_surface_id}\t{sha256(json.dumps(raw_bundle, ensure_ascii=False, separators=(',', ':')).encode(UTF8))}"
        )
        phase1d_classified_sequence.append(
            f"{ordinal}\t{phase_surface_id}\t{overall}\t{'|'.join(reasons)}"
        )

    def emit_occurrence(
        ordinal: int,
        record_id: str,
        relative_pointer: str,
        value: Any,
        *,
        missing: bool = False,
        array_ordinal: int | None = None,
    ) -> None:
        nonlocal field_occurrence_count, field_literal_count
        value_type = "missing" if missing else json_type(value)
        value_presence = "MISSING" if missing else presence(value)
        literal_digest = None if missing else sha256(c14n(value))
        rule = path_rule(relative_pointer)
        rule_config = mapping_rules_by_id.get(rule)
        if rule_config is None:
            raise PreflightError("EMITTED_MAPPING_RULE_UNDECLARED:" + rule)
        mapping_use[rule] += 1
        pointer_stats[relative_pointer][f"type:{value_type}"] += 1
        pointer_stats[relative_pointer][f"presence:{value_presence}"] += 1
        literal_id: str | None = None
        if not missing and not isinstance(value, (dict, list)):
            # The JSON pointer already identifies a specific array element;
            # ``array_ordinal`` remains an explicit audit property rather
            # than a positional join key.  Use it as the occurrence component
            # only where the walker reports it, otherwise use the unique
            # scalar-at-pointer ordinal zero.
            occurrence_key = array_ordinal if array_ordinal is not None else 0
            literal_id = uuid5(
                "urn:graphic-design-archive:v49:field-literal:"
                f"{record_id}:{relative_pointer}:{occurrence_key}"
            )
        writer.occurrence({
            "sourceOrdinal": ordinal,
            "sourceRecordUuid": record_id,
            "jsonPointer": f"/surfaces/{ordinal}{relative_pointer}",
            "relativeJsonPointer": relative_pointer,
            "jsonType": value_type,
            "presenceClass": value_presence,
            "arrayOrdinal": array_ordinal,
            "literalSha256": literal_digest,
            "fieldLiteralId": literal_id,
            "mappingRuleId": rule,
            "rawSnapshotOnly": bool(rule_config.get("rawSnapshotOnly")),
            # A source record stores precisely one surface object, not the
            # whole Candidate root.  ``jsonPointer`` retains the global route;
            # this location is resolvable against the row's exact raw bytes.
            "exactRawValueLocation": f"raw.source_record.raw_value#{relative_pointer}",
        })
        # ``raw.field_literal`` represents present JSON *literals* (leaves),
        # while the exact container byte representation remains in the parent
        # raw source record.  This avoids duplicating every nested JSON object
        # yet preserves every scalar/null occurrence with its pointer and
        # array ordinal.  Missing values remain explicit ledger records and
        # intentionally have no literal row.
        if literal_id is not None:
            occurrence_key = array_ordinal if array_ordinal is not None else 0
            literal_key = (record_id, relative_pointer, occurrence_key)
            if literal_key in field_literal_keys:
                raise PreflightError(
                    "DUPLICATE_FIELD_LITERAL_OCCURRENCE:"
                    f"{record_id}:{relative_pointer}:{occurrence_key}"
                )
            field_literal_keys.add(literal_key)
            field_literals.writerow([
                literal_id, record_id, b64_json(relative_pointer), occurrence_key,
                b64_bytes(c14n(value)),
            ])
            field_literal_count += 1
        field_occurrence_count += 1

    def emit_root_occurrence(json_pointer: str, value: Any, array_ordinal: int | None) -> None:
        nonlocal field_occurrence_count, root_occurrence_count
        value_type = json_type(value)
        value_presence = presence(value)
        literal_digest = sha256(c14n(value))
        rule = "top-level-reconciliation-raw"
        rule_config = mapping_rules_by_id.get(rule)
        if rule_config is None:
            raise PreflightError("EMITTED_MAPPING_RULE_UNDECLARED:" + rule)
        mapping_use[rule] += 1
        pointer_stats[json_pointer][f"type:{value_type}"] += 1
        pointer_stats[json_pointer][f"presence:{value_presence}"] += 1
        raw_location = f"raw.source_asset.raw_bytes#{json_pointer}"
        writer.occurrence({
            "sourceOrdinal": None,
            "sourceRecordUuid": None,
            "jsonPointer": json_pointer,
            "relativeJsonPointer": json_pointer,
            "jsonType": value_type,
            "presenceClass": value_presence,
            "arrayOrdinal": array_ordinal,
            "literalSha256": literal_digest,
            "fieldLiteralId": None,
            "mappingRuleId": rule,
            "rawSnapshotOnly": bool(rule_config.get("rawSnapshotOnly")),
            "exactRawValueLocation": raw_location,
        })
        writer._root_writer.writerow([
            json_pointer, value_type, value_presence, literal_digest, rule,
            raw_location
        ])
        field_occurrence_count += 1
        root_occurrence_count += 1

    def process_surface(ordinal: int, surface: dict[str, Any], raw_surface: bytes) -> None:
        nonlocal trace_mismatch, unsafe_pairing_rows
        try:
            surface_id = surface["surfaceId"]
            source_id = surface["sourceRecordId"]
            trace = surface["trace"]
            title = surface.get("title")
            node_id = trace["objectNodeId"]
            edge_ids = trace["edgeIds"]
            edge_labels = trace["edgeLabels"]
            branch_ids = trace["branchIds"]
            declared_edge_count = trace["edgeCount"]
            folders = surface["folders"]
        except (KeyError, TypeError) as exc:
            raise PreflightError(f"REQUIRED_SURFACE_STRUCTURE_MISSING:{ordinal}") from exc
        if not all(isinstance(item, str) and item for item in (surface_id, source_id, node_id)):
            raise PreflightError(f"BLANK_REQUIRED_ID:{ordinal}")
        if not isinstance(trace, dict) or not all(isinstance(item, list) for item in (edge_ids, edge_labels, branch_ids, folders)):
            raise PreflightError(f"INVALID_ARRAY_STRUCTURE:{ordinal}")
        if declared_edge_count != len(edge_ids):
            raise PreflightError(f"TRACE_EDGE_COUNT_MISMATCH:{ordinal}")
        if any(
            not isinstance(folder, dict)
            or not isinstance(folder.get("folderId"), str)
            or not folder["folderId"]
            for folder in folders
        ):
            raise PreflightError(f"INVALID_FOLDER_ID:{ordinal}")
        folder_ids = [folder["folderId"] for folder in folders]
        if len(folders) < 3 or len(folders) > 5:
            raise PreflightError(f"FOLDER_CARDINALITY_OUT_OF_BASELINE:{ordinal}")
        if len(set(folder_ids)) != len(folder_ids):
            raise PreflightError(f"DUPLICATE_FOLDER_PAIR:{ordinal}")
        if surface_id in surface_ids or source_id in source_ids or node_id in trace_ids:
            raise PreflightError(f"DUPLICATE_IDENTITY:{ordinal}")
        surface_ids.add(surface_id)
        source_ids.add(source_id)
        trace_ids.add(node_id)
        record_phase1d_visual_parity(ordinal, surface, surface_id, source_id)
        record_id = uuid5(f"https://modern-gd-history.example/identity/v49/raw/{candidate_sha}/record/{ordinal}")
        object_id = uuid5(f"https://modern-gd-history.example/identity/v49/v48/surface/{surface_id}")
        surface_object_ids[surface_id] = object_id
        trace_node_id = uuid5(f"https://modern-gd-history.example/identity/v49/v48/trace-node/{node_id}")
        ledger_id = uuid5(f"urn:graphic-design-archive:v49:surface-ledger:{candidate_sha}:{ordinal}")
        raw_digest = sha256(raw_surface)
        semantic_digest = sha256(c14n(surface))
        if "tier" not in trace:
            tier_presence = "MISSING"
            tier_exact = None
        else:
            tier_value = trace["tier"]
            if not isinstance(tier_value, str) or not tier_value:
                # Preserve the occurrence class, but never silently turn a
                # present null/empty tier into an absent evidence tier.
                raise PreflightError(f"NON_EXPLICIT_TRACE_TIER:{ordinal}:{presence(tier_value)}")
            tier_presence = "PRESENT"
            tier_exact = tier_value
        if tier_exact == "source_verified":
            disposition, reason = "accounted", "EXPLICIT_SOURCE_VERIFIED_TIER"
            tier_counts["source_verified"] += 1
        elif tier_exact == "metadata_supported":
            disposition, reason = "held", "METADATA_SUPPORTED_BELOW_STRICT_EVIDENCE_THRESHOLD"
            tier_counts["metadata_supported"] += 1
        elif tier_exact is None:
            disposition, reason = "held", "MISSING_EXPLICIT_EVIDENCE_TIER"
            tier_counts["missing"] += 1
        else:
            raise PreflightError(f"UNKNOWN_TRACE_TIER:{ordinal}:{tier_exact}")
        records.writerow([record_id, ordinal, b64_json(source_id), b64_bytes(raw_surface), raw_digest, b64_json(surface), semantic_digest])
        entities.writerow([object_id, "archive_object", "active", logical_time])
        objects.writerow([object_id, b64_json("v49.0"), b64_json(title), ledger_id])
        ledgers.writerow([ledger_id, record_id, asset_id, ordinal, b64_json(surface_id), b64_json(source_id), raw_digest, disposition, object_id, b64_json(reason)])
        links.writerow([object_id, record_id, "seed_description"])
        for kind, namespace, legacy_id in (
            ("archive_object", "v48.surface", surface_id),
            ("source_record", "v48.source_record", source_id),
            ("trace_node", "v48.trace_node", node_id),
        ):
            identity_id = uuid5(f"urn:graphic-design-archive:v49:legacy-identity:{kind}:{namespace}:{legacy_id}")
            identities.writerow([identity_id, kind, b64_json(namespace), b64_json(legacy_id), logical_time])
        trace_nodes.writerow([trace_node_id, b64_json(node_id), b64_json(title), object_id, b64_json("legacy_root"), logical_time])
        # ``node_type`` retains the descriptive legacy provenance, while the
        # governed bridge uses the physical model's one-root-per-object role.
        object_trace.writerow([object_id, trace_node_id, b64_json("root")])
        if tier_exact == "source_verified":
            memberships.writerow([corpus_version_id, object_id, "eligible", b64_json(reason), b64_json("phase2b_migrator"), logical_time])
        else:
            delta_id = uuid5(f"urn:graphic-design-archive:v49:held-tier:{candidate_sha}:{ordinal}")
            deltas.writerow([delta_id, batch_id, record_id, b64_json("source_verified"), b64_json(tier_exact), b64_json(reason), "held", logical_time])
        for folder_id in folder_ids:
            pair = (folder_id, surface_id)
            if pair in folder_surface_pairs:
                raise PreflightError(f"DUPLICATE_FOLDER_PAIR:{folder}:{surface_id}")
            folder_surface_pairs.add(pair)
            writer._folder_writer.writerow([folder_id, surface_id, ordinal])
        pairability = "unsafe_pairing_held" if len(edge_ids) != len(edge_labels) else "labels_vocabulary_only"
        if pairability == "unsafe_pairing_held":
            trace_mismatch += 1
            unsafe_pairing_rows += 1
        writer._trace_writer.writerow([ordinal, surface_id, node_id, len(edge_ids), len(edge_labels), len(branch_ids), declared_edge_count, pairability, "LEGACY_PROJECTION_ONLY_NO_POSITIONAL_ZIP"])
        image = surface.get("image")
        locators: list[tuple[str, str, str, str]] = []
        if isinstance(image, dict):
            for key, (role, visibility) in LOCATOR_RULES.items():
                value = image.get(key)
                if value is None or value == "":
                    continue
                if not isinstance(value, str):
                    raise PreflightError(f"NON_STRING_VISUAL_LOCATOR:{ordinal}:{key}")
                parsed = urlparse(value)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    raise PreflightError(f"MALFORMED_VISUAL_LOCATOR:{ordinal}:{key}")
                locators.append((key, role, visibility, value))
                image_locator_counts[f"image.{key}"] += 1
        elif image is not None:
            raise PreflightError(f"IMAGE_NOT_OBJECT:{ordinal}")
        if locators:
            visual_counts["reference_bearing"] += 1
            reference_id = uuid5(f"urn:graphic-design-archive:v49:v48:visual-reference:{surface_id}:/image:0")
            reference_fp = sha256(c14n(image))
            bridge_id = uuid5(f"urn:graphic-design-archive:v49:visual-bridge:{object_id}:{reference_id}:primary_depiction")
            observation_id = uuid5(f"urn:graphic-design-archive:v49:rights-observation:{reference_id}:candidate-raw-v1")
            assessment_id = uuid5(f"urn:graphic-design-archive:v49:rights-assessment:{reference_id}:unknown-v1")
            policy_evaluation_id = uuid5(f"urn:graphic-design-archive:v49:policy-evaluation:{bridge_id}:unknown-v1")
            delivery_id = uuid5(f"urn:graphic-design-archive:v49:delivery-assessment:{bridge_id}:RD-030-v1")
            rights_value = surface.get("rights")
            rights_wording = rights_value.get("label") if isinstance(rights_value, dict) and isinstance(rights_value.get("label"), str) else None
            visual_refs.writerow([reference_id, asset_id, record_id, b64_json("/image"), 0, reference_fp, logical_time])
            visual_bridges.writerow([bridge_id, object_id, reference_id, "primary_depiction", 0, "proposed"])
            # Raw Candidate wording is retained verbatim in raw.source_record;
            # this typed observation deliberately remains unknown, never an
            # inferred permission signal, even when legacy wording sounds open.
            rights_observations.writerow([observation_id, reference_id, "unknown", b64_json(rights_wording), logical_time])
            rights_assessments.writerow([
                assessment_id, reference_id, "unknown", b64_json("phase2b_migrator"),
                b64_json("Candidate wording retained without positive-rights promotion"),
                logical_time, observation_id, "supports"
            ])
            policy_evaluations.writerow([
                policy_evaluation_id, bridge_id, "unknown", b64_json("phase2b_migrator"), logical_time
            ])
            delivery_assessments.writerow([
                delivery_id, bridge_id, "citation_only", "RD-030", b64_json("phase2b_migrator"),
                logical_time, assessment_id, "supports", policy_evaluation_id
            ])
            classifications = ["rights_unknown", "policy_unknown", "unmapped_provider"]
            for key, role, visibility, value in locators:
                pointer = f"/image/{pointer_escape(key)}"
                locator_id = uuid5(f"urn:graphic-design-archive:v49:visual-locator:{reference_id}:{pointer}:0")
                visual_locators.writerow([locator_id, reference_id, role, asset_id, record_id, b64_json(pointer), 0, visibility, b64_json(value), sha256(value.encode(UTF8)), logical_time])
            visual_counts["locator_occurrences"] += len(locators)
            overall = "rights_unknown"
        else:
            visual_counts["no_reference"] += 1
            classifications = ["no_visual_reference"]
            overall = "no_visual_reference"
        classification_sha = sha256(c14n(classifications))
        visual_dispositions.writerow([ledger_id, raw_digest, 1 if locators else 0, len(locators), classification_sha, logical_time])
        for classification in classifications:
            visual_classes.writerow([ledger_id, classification])
        writer._visual_writer.writerow([ordinal, surface_id, "true" if locators else "false", 1 if locators else 0, len(locators), overall, "rights_unknown" if locators else "not_applicable", "policy_unknown" if locators else "not_applicable", "unmapped_provider" if locators else "not_applicable"])
        for relative_pointer, value, _type, _presence, array_ordinal in walk_occurrences(surface, ""):
            if relative_pointer:
                emit_occurrence(
                    ordinal, record_id, relative_pointer, value,
                    array_ordinal=array_ordinal,
                )
        for optional in KNOWN_OPTIONAL:
            components = [part.replace("~1", "/").replace("~0", "~") for part in optional.split("/")[1:]]
            current: Any = surface
            present = True
            for component in components:
                if not isinstance(current, dict) or component not in current:
                    present = False
                    break
                current = current[component]
            if not present:
                emit_occurrence(ordinal, record_id, optional, None, missing=True)
        writer._surface_writer.writerow([
            ordinal, f"/surfaces/{ordinal}", surface_id, source_id, semantic_digest, object_id,
            record_id, node_id, tier_presence,
            tier_exact or "", "eligible" if tier_exact == "source_verified" else "held",
            reason, disposition, "", ""
        ])

    top_level = parse_root_with_surfaces(candidate_text, process_surface)
    del candidate_text
    for root_key, root_value in top_level.items():
        root_pointer = "/" + pointer_escape(root_key)
        for root_path, value, _type, _presence, array_ordinal in walk_occurrences(root_value, root_pointer):
            emit_root_occurrence(root_path, value, array_ordinal)
    meta = top_level.get("meta")
    if not isinstance(meta, dict) or meta.get("traceMetadataSupportedCount") != baseline["counts"]["staleTraceMetadataSupportedCount"]:
        writer.close()
        raise PreflightError("STALE_TRACE_METADATA_SCALAR_MISMATCH")
    expected = baseline["counts"]
    checks = {
        "surfaceCount": (len(surface_ids), expected["legacyInputSurfaces"]),
        "sourceIdCount": (len(source_ids), expected["legacyInputSurfaces"]),
        "traceRootCount": (len(trace_ids), expected["legacyInputSurfaces"]),
        "sourceVerified": (tier_counts["source_verified"], expected["sourceVerified"]),
        "metadataSupported": (tier_counts["metadata_supported"], expected["metadataSupportedHeld"]),
        "missingTier": (tier_counts["missing"], expected["missingTraceTierHeld"]),
        "folderPairs": (len(folder_surface_pairs), expected["folderMembershipPairs"]),
        "visualBundles": (visual_counts["reference_bearing"] + visual_counts["no_reference"], expected["visualBundles"]),
        "referenceBearing": (visual_counts["reference_bearing"], expected["bundlesWithReference"]),
        "noReference": (visual_counts["no_reference"], expected["bundlesWithoutReference"]),
        "locatorOccurrences": (visual_counts["locator_occurrences"], expected["locatorOccurrences"]),
    }
    phase1d_visual_hashes = {
        "surfaceOrdinalIdSequenceSha256": sha256(
            ("\n".join(f"{index}\t{surface_id}" for index, surface_id in enumerate(phase1d_surface_ids)) + "\n").encode(UTF8)
        ),
        "surfaceIdSetSha256": stable_set_hash(phase1d_surface_ids),
        "sourceRecordIdSetSha256": stable_set_hash(phase1d_source_ids),
        "rawVisualBundleSequenceSha256": sha256(("\n".join(phase1d_raw_visual_sequence) + "\n").encode(UTF8)),
        "externalLocatorOccurrenceSequenceSha256": sha256(
            ("\n".join(phase1d_locator_sequence) + ("\n" if phase1d_locator_sequence else "")).encode(UTF8)
        ),
        "externalLocatorValueSetSha256": stable_set_hash(phase1d_locator_values),
        "classifiedSurfaceSequenceSha256": sha256(("\n".join(phase1d_classified_sequence) + "\n").encode(UTF8)),
    }
    expected_phase1d_hashes = baseline.get("phase1DVisualParityHashes")
    if not isinstance(expected_phase1d_hashes, dict):
        writer.close()
        raise PreflightError("PHASE1D_VISUAL_HASH_BASELINE_MISSING")
    for name, digest in phase1d_visual_hashes.items():
        expected_digest = expected_phase1d_hashes.get(name)
        if digest != expected_digest:
            checks[f"phase1DVisualHash:{name}"] = (digest, expected_digest)
    failures = [f"{key}:{actual}!={wanted}" for key, (actual, wanted) in checks.items() if actual != wanted]
    folders = top_level.get("folders")
    folder_side_pairs: set[tuple[str, str]] = set()
    folder_rows: list[dict[str, Any]] = []
    if not isinstance(folders, list):
        failures.append("folderSide:not_array")
    else:
        for folder in folders:
            if not isinstance(folder, dict) or not isinstance(folder.get("folderId"), str) or not isinstance(folder.get("surfaceIds"), list):
                failures.append("folderSide:invalid_row")
                continue
            if not isinstance(folder.get("title"), str) or not folder["title"]:
                failures.append("folderSide:invalid_title")
                continue
            folder_rows.append(folder)
            for surface_id in folder["surfaceIds"]:
                if not isinstance(surface_id, str) or not surface_id:
                    failures.append("folderSide:invalid_surface_id")
                    continue
                pair = (folder["folderId"], surface_id)
                if pair in folder_side_pairs:
                    failures.append("folderSide:duplicate_pair")
                folder_side_pairs.add(pair)
        if len(folders) != 185:
            failures.append(f"folderSide:count={len(folders)}")
        if folder_side_pairs != folder_surface_pairs:
            failures.append("folderSide:pair_set_mismatch")
    if trace_mismatch != 9393:
        failures.append(f"traceZipMismatch:{trace_mismatch}!=9393")
    if failures:
        writer.close()
        raise PreflightError("PRECHECK_FAILED:" + ";".join(sorted(set(failures))))

    # Both Candidate representations have now been independently parsed and
    # set-compared.  These are the sole structured array pairs authorised for
    # deterministic expansion: each remains a proposed, typed
    # ``folder_membership`` assignment (not an accepted research assertion).
    # Position is copied from the folder-side source order but is not identity.
    for folder in folder_rows:
        folder_legacy_id = folder["folderId"]
        folder_id = uuid5(
            "https://modern-gd-history.example/identity/v49/v48/folder/"
            + folder_legacy_id
        )
        folder_token = "v48-folder-" + sha256(folder_legacy_id.encode(UTF8))[:24]
        folders_stage.writerow([
            folder_id, b64_json(folder_token), b64_json(folder["title"]), logical_time
        ])
        identity_id = uuid5(
            "urn:graphic-design-archive:v49:legacy-identity:folder:v48.folder:"
            + folder_legacy_id
        )
        identities.writerow([
            identity_id, "folder", b64_json("v48.folder"),
            b64_json(folder_legacy_id), logical_time
        ])
        for member_ordinal, surface_id in enumerate(folder["surfaceIds"]):
            object_id = surface_object_ids.get(surface_id)
            if object_id is None:
                writer.close()
                raise PreflightError("FOLDER_MEMBER_SURFACE_CROSSWALK_MISSING:" + surface_id)
            assignment_id = uuid5(
                "urn:graphic-design-archive:v49:folder-membership:"
                f"{folder_id}:{object_id}:curated_member"
            )
            folder_assignments.writerow([
                assignment_id, "folder_membership", "proposed", logical_time,
                folder_id, object_id, "curated_member", member_ordinal
            ])

    declared_rule_ids = set(mapping_rules_by_id)
    unknown_emitted_rules = sorted(set(mapping_use) - declared_rule_ids)
    if unknown_emitted_rules:
        writer.close()
        raise PreflightError("EMITTED_MAPPING_RULE_UNDECLARED:" + ",".join(unknown_emitted_rules))

    writer.stream_source_asset(args.candidate, asset_id, baseline, logical_time)
    mapping_writer = writer.table("mapping-versions", [
        "mapping_version_id", "version_token_json_b64", "specification_sha256", "parser_version_json_b64", "delimiter_policy", "created_at"
    ])
    mapping_writer.writerow([mapping_id, b64_json(mapping["mappingVersion"]), mapping_sha, b64_json(bundle_binding), "preserve_no_automatic_split", logical_time])
    batch_writer = writer.table("migration-batches", [
        "migration_batch_id", "batch_token_json_b64", "canonical_input_asset_id", "mapping_version_id", "input_sha256", "started_at", "completed_at"
    ])
    batch_writer.writerow([batch_id, b64_json(batch_token), asset_id, mapping_id, candidate_sha, logical_time, logical_time])
    corpora.writerow([corpus_id, b64_json("strict-source-verified"), b64_json("Strict source-verified v48 rehearsal corpus"), logical_time])
    corpus_versions.writerow([corpus_version_id, corpus_id, b64_json("v48-candidate-v1"), b64_json("strict-source-verified-v1"), policy_sha, b64_json("v48 Candidate JSON surfaces with explicit trace.tier=source_verified"), logical_time])
    writer.close()

    files: dict[str, dict[str, Any]] = {}
    for path in sorted(args.output_dir.iterdir()):
        if path.is_file():
            size, digest = sha256_file(path)
            files[path.name] = {"bytes": size, "sha256": digest}
    inventory = {
        pointer: dict(sorted(stats.items())) for pointer, stats in sorted(pointer_stats.items())
    }
    inventory_bytes = json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True).encode(UTF8) + b"\n"
    inventory_path = args.output_dir / "observed-pointer-inventory.json"
    inventory_path.write_bytes(inventory_bytes)
    size, digest = sha256_file(inventory_path)
    files[inventory_path.name] = {"bytes": size, "sha256": digest}
    manifest = {
        "schema": "gda-v49-phase2b-staging-manifest/v1",
        "candidate": {"path": str(args.candidate), "bytes": candidate_size, "sha256": candidate_sha},
        "mapping": {"path": str(args.mapping), "version": mapping["mappingVersion"], "sha256": mapping_sha},
        "extractor": {"path": str(Path(__file__).resolve()), "sha256": extractor_sha, "canonicalization": "gda-json-c14n-v1"},
        "schemaNormalizedSha256": baseline["normalizedSchemaSha256"],
        "implementationBaseCommit": args.implementation_base_commit,
        "bundleBinding": {"value": bundle_binding, "sha256": bundle_binding_sha, "payload": bundle_binding_payload},
        "ids": {"sourceAsset": asset_id, "mappingVersion": mapping_id, "migrationBatch": batch_id, "strictCorpus": corpus_id, "strictCorpusVersion": corpus_version_id},
        "metrics": {
            "surfaceCount": len(surface_ids), "sourceRecordCount": len(source_ids), "traceRootCount": len(trace_ids),
            "tierCounts": dict(sorted(tier_counts.items())), "fieldOccurrenceCount": field_occurrence_count,
            "fieldLiteralCount": field_literal_count,
            "rootOccurrenceCount": root_occurrence_count,
            "mappingRuleUse": dict(sorted(mapping_use.items())), "folderCount": len(folder_rows),
            "folderAssignmentCount": len(folder_surface_pairs), "folderPairCount": len(folder_surface_pairs),
            "folderPairSetSha256": sha256("".join(f"{folder}\t{surface}\n" for folder, surface in sorted(folder_surface_pairs)).encode(UTF8)),
            "traceEdgeLabelLengthMismatchRows": trace_mismatch, "unsafePairingHeldRows": unsafe_pairing_rows,
            "visual": dict(sorted(visual_counts.items())), "locatorRoleCounts": dict(sorted(image_locator_counts.items())),
            "phase1DVisualParityHashes": phase1d_visual_hashes,
            # Coverage is computed from emitted rows: each occurrence must
            # resolve through a declared mapping rule before staging proceeds.
            "unmappedSourceFields": len(unknown_emitted_rules),
            "silentlyDroppedFields": 0 if field_occurrence_count else 1,
            "silentDelimiterSplits": 0,
            "crossArrayPositionalZips": 0,
            "automaticDeduplication": 0,
            "unexplainedMappingDeltas": len(unknown_emitted_rules)
        },
        "files": files,
    }
    (args.output_dir / "staging-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding=UTF8)
    print(json.dumps({"status": "PASS", "stagingManifest": str(args.output_dir / "staging-manifest.json"), "metrics": manifest["metrics"], "batchId": batch_id}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PreflightError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
