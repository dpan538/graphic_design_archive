#!/usr/bin/env python3
"""Shared immutable loaders for TRACE v49 Exploration discovery.

Eligibility always comes from the audited migration ledger.  SQLite remains a
read-only reconciliation source; governed Context and Spacetime artifacts are
the authority for public feature values.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
LEDGER_PATH = ROOT / "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"
SQLITE_PATH = ROOT / "data/prefreeze_candidate_v48.sqlite"
FREEZE_PATH = ROOT / "database/FREEZE_V49.json"
CANDIDATE_PATH = ROOT / "generated/public_surfaces_prefreeze_candidate_v48.json"
CONTEXT_MANIFEST_PATH = ROOT / "frontend/generated/trace-context-v1/manifest.json"
CONTEXT_RECORDS_PATH = ROOT / "frontend/generated/trace-context-v1/records.json"
SPACETIME_MANIFEST_PATH = ROOT / "frontend/generated/trace-spacetime-v1/manifest.json"
SPACETIME_RECORDS_PATH = ROOT / "frontend/generated/trace-spacetime-v1/record-index.json"
SPACETIME_GEOGRAPHY_PATH = ROOT / "frontend/generated/trace-spacetime-v1/geography-registry.json"
SPACETIME_PERIODS_PATH = ROOT / "frontend/generated/trace-spacetime-v1/time-buckets.json"

EXPECTED_HASHES = {
    "database/FREEZE_V49.json": "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e",
    "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv": "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
    "data/prefreeze_candidate_v48.sqlite": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
    "generated/public_surfaces_prefreeze_candidate_v48.json": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
}
EXPECTED_CONTEXT_PROJECTION_SHA256 = "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
EXPECTED_SPACETIME_PROJECTION_SHA256 = "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
EXPECTED_GOVERNED_MANIFEST_SHA256 = {
    "frontend/generated/trace-context-v1/manifest.json": "ff8ebc15eeb95407b6b6b274dd2fc69ce4c3c183bb2f6a7e7f261c028b96f92c",
    "frontend/generated/trace-spacetime-v1/manifest.json": "93e88157865d987376ec8997e94a4101353038cf792e665d35e4c50b1c4384ec",
}
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
UUID_PATTERN = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I)
PRIVATE_VALUE_PATTERN = re.compile(r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRB\d|https?://|file://)", re.I)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    if pretty:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def clean_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("\t", " ").replace("\r", " ").replace("\n", " ")


def tsv_bytes(headers: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    ordered_headers = list(headers)
    lines = ["\t".join(ordered_headers)]
    for row in rows:
        lines.append("\t".join(clean_cell(row.get(header, "")) for header in ordered_headers))
    return ("\n".join(lines) + "\n").encode("utf-8")


def quantile_r7(values: Iterable[int | float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def printable_number(value: float, digits: int = 9) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def analysis_id(namespace: str, source_value: str) -> str:
    digest = hashlib.sha256(f"trace-exploration-v1\0{namespace}\0{source_value}".encode("utf-8")).hexdigest()
    prefix = re.sub(r"[^A-Z0-9]+", "_", namespace.upper()).strip("_") or "VALUE"
    return f"EXP:{prefix}:{digest}"


def value_token(namespace: str, label: str, *, public_id: str | None = None) -> dict[str, str]:
    normalized = str(label).strip()
    if not normalized:
        raise ValueError(f"{namespace} label is blank")
    return {"id": public_id or analysis_id(namespace, normalized), "label": normalized}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_eligibility() -> tuple[set[str], set[str]]:
    public_ids: set[str] = set()
    held_ids: set[str] = set()
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            object_id = row["surface_id_exact"]
            if not PUBLIC_ID_PATTERN.fullmatch(object_id):
                raise ValueError("eligibility ledger contains an invalid public surface ID")
            if row["research_disposition"] == "eligible":
                public_ids.add(object_id)
            elif row["research_disposition"] == "held":
                held_ids.add(object_id)
            else:
                raise ValueError("eligibility ledger contains an unclassified surface")
    if len(public_ids) != 7_995 or len(held_ids) != 7_928 or public_ids & held_ids:
        raise ValueError("eligibility ledger does not reconcile")
    return public_ids, held_ids


def open_immutable_sqlite() -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
        connection.close()
        raise ValueError("SQLite reconciliation source is not query-only")
    return connection


def verify_frozen_inputs() -> dict[str, str]:
    paths = {
        "database/FREEZE_V49.json": FREEZE_PATH,
        "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv": LEDGER_PATH,
        "data/prefreeze_candidate_v48.sqlite": SQLITE_PATH,
        "generated/public_surfaces_prefreeze_candidate_v48.json": CANDIDATE_PATH,
    }
    actual = {name: sha256_path(path) for name, path in paths.items()}
    if actual != EXPECTED_HASHES:
        raise ValueError("a frozen Exploration source input changed")
    governed_manifest_hashes = {
        "frontend/generated/trace-context-v1/manifest.json": sha256_path(CONTEXT_MANIFEST_PATH),
        "frontend/generated/trace-spacetime-v1/manifest.json": sha256_path(SPACETIME_MANIFEST_PATH),
    }
    if governed_manifest_hashes != EXPECTED_GOVERNED_MANIFEST_SHA256:
        raise ValueError("a governed projection manifest changed")
    context_manifest = load_json(CONTEXT_MANIFEST_PATH)
    spacetime_manifest = load_json(SPACETIME_MANIFEST_PATH)
    if context_manifest.get("projectionSha256") != EXPECTED_CONTEXT_PROJECTION_SHA256:
        raise ValueError("governed Context projection changed")
    if spacetime_manifest.get("projectionSha256") != EXPECTED_SPACETIME_PROJECTION_SHA256:
        raise ValueError("governed Spacetime projection changed")
    context_records_sha256 = sha256_path(CONTEXT_RECORDS_PATH)
    context_artifact_hashes = context_manifest.get("artifactSha256")
    if (
        not isinstance(context_artifact_hashes, Mapping)
        or context_artifact_hashes.get("records.json") != context_records_sha256
        or context_manifest.get("recordsSha256") != context_records_sha256
    ):
        raise ValueError("governed Context records do not match their manifest")
    spacetime_loaded_artifacts = {
        "record-index.json": SPACETIME_RECORDS_PATH,
        "geography-registry.json": SPACETIME_GEOGRAPHY_PATH,
        "time-buckets.json": SPACETIME_PERIODS_PATH,
    }
    spacetime_payload_hashes = spacetime_manifest.get("payloadSha256")
    if not isinstance(spacetime_payload_hashes, Mapping):
        raise ValueError("governed Spacetime manifest lacks payload hashes")
    verified_spacetime_hashes: dict[str, str] = {}
    for filename, path in spacetime_loaded_artifacts.items():
        payload_sha256 = sha256_path(path)
        if spacetime_payload_hashes.get(filename) != payload_sha256:
            raise ValueError(f"governed Spacetime {filename} does not match its manifest")
        verified_spacetime_hashes[
            f"frontend/generated/trace-spacetime-v1/{filename}"
        ] = payload_sha256
    return {
        **actual,
        **governed_manifest_hashes,
        "frontend/generated/trace-context-v1/records.json": context_records_sha256,
        **verified_spacetime_hashes,
        "frontend/generated/trace-context-v1": EXPECTED_CONTEXT_PROJECTION_SHA256,
        "frontend/generated/trace-spacetime-v1": EXPECTED_SPACETIME_PROJECTION_SHA256,
    }


def _sorted_unique_tokens(values: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    by_id: dict[str, str] = {}
    for value in values:
        value_id = value["id"]
        label = value["label"]
        if value_id in by_id and by_id[value_id] != label:
            raise ValueError("one normalized dimension ID has conflicting labels")
        by_id[value_id] = label
    return [{"id": value_id, "label": by_id[value_id]} for value_id in sorted(by_id)]


def load_normalized_public_records() -> dict[str, Any]:
    receipts = verify_frozen_inputs()
    public_ids, held_ids = load_eligibility()
    context_document = load_json(CONTEXT_RECORDS_PATH)
    spacetime_document = load_json(SPACETIME_RECORDS_PATH)
    geography_document = load_json(SPACETIME_GEOGRAPHY_PATH)
    periods_document = load_json(SPACETIME_PERIODS_PATH)

    context_by_id = {record["selectedRecord"]["surfaceId"]: record for record in context_document["records"]}
    spacetime_by_id = {record["objectId"]: record for record in spacetime_document["records"]}
    if set(context_by_id) != public_ids or set(spacetime_by_id) != public_ids:
        raise ValueError("governed Context/Spacetime public cohorts do not match the eligibility ledger")
    if public_ids & held_ids:
        raise ValueError("held/public overlap entered normalized inputs")

    geography_by_id = {entry["geographyId"]: entry for entry in geography_document["entries"]}
    period_by_id = {entry["periodId"]: entry for entry in periods_document["periods"]}
    folder_entries: dict[str, list[dict[str, str]]] = defaultdict(list)
    source_collection_present: set[str] = set()
    source_diagnostics: dict[str, dict[str, str]] = {}

    connection = open_immutable_sqlite()
    try:
        for row in connection.execute(
            "SELECT surface_id, folder_id, folder_type, title FROM object_folder_refs ORDER BY surface_id, folder_type, folder_id"
        ):
            object_id = row["surface_id"]
            if object_id not in public_ids:
                continue
            folder_type = str(row["folder_type"])
            raw_id = str(row["folder_id"])
            folder_entries[object_id].append({
                "id": analysis_id(f"curated_container_{folder_type}", raw_id),
                "label": str(row["title"]).strip(),
                "type": folder_type,
            })
        for row in connection.execute(
            """SELECT surface_id, value FROM object_metadata_rows
               WHERE table_kind='SOURCE' AND label='Source collection'
               ORDER BY surface_id, row_order"""
        ):
            if row["surface_id"] in public_ids and str(row["value"]).strip():
                source_collection_present.add(row["surface_id"])
        for row in connection.execute(
            """SELECT surface_id, rights_state, image_state, authority_state
               FROM objects ORDER BY surface_id"""
        ):
            if row["surface_id"] in public_ids:
                source_diagnostics[row["surface_id"]] = {
                    "rightsState": str(row["rights_state"]),
                    "imageState": str(row["image_state"]),
                    "authorityState": str(row["authority_state"]),
                }
    finally:
        connection.close()

    if sum(len(values) for values in folder_entries.values()) != 24_102:
        raise ValueError("public curated memberships do not reconcile")
    if len(source_diagnostics) != 7_995:
        raise ValueError("public source diagnostics do not reconcile")

    actual_folder_labels: dict[str, set[str]] = defaultdict(set)
    for entries in folder_entries.values():
        for entry in entries:
            actual_folder_labels[entry["type"]].add(entry["label"])
    expected_context_labels: dict[str, set[str]] = defaultdict(set)
    for context in context_by_id.values():
        for representation in context["representations"]:
            source_kind = "movement" if representation["kind"] == "movement_context" else representation["kind"]
            expected_context_labels[source_kind].add(representation["label"])
    expected_folder_labels = {
        "medium": expected_context_labels["medium"],
        "theme": expected_context_labels["theme"],
        "movement": expected_context_labels["movement"],
        "region": {entry["sourceLabel"] for entry in geography_by_id.values()},
    }
    if {key: actual_folder_labels[key] for key in sorted(actual_folder_labels)} != expected_folder_labels:
        raise ValueError("public curated folder labels differ from governed Context/Spacetime registries")

    normalized: list[dict[str, Any]] = []
    for object_id in sorted(public_ids):
        context = context_by_id[object_id]
        spacetime = spacetime_by_id[object_id]
        metadata = context["selectedRecord"]["rootMetadata"]
        representations: dict[str, list[dict[str, str]]] = defaultdict(list)
        for representation in context["representations"]:
            representations[representation["kind"]].append({
                "id": representation["termId"],
                "label": representation["label"],
            })
        geography_tokens = []
        geography_states: set[str] = set()
        geography_classes: set[str] = set()
        geography_qualified = False
        for geography_id in spacetime["geographyIds"]:
            entry = geography_by_id.get(geography_id)
            if not entry:
                raise ValueError("Spacetime record references an unknown geography")
            geography_tokens.append({"id": geography_id, "label": entry["displayLabel"]})
            geography_states.add(entry["mappingState"])
            geography_classes.add(entry["geographyClass"])
            qualification = entry.get("qualification")
            if qualification is not None and not isinstance(qualification, str):
                raise ValueError("Spacetime geography qualification is not text or null")
            geography_qualified = geography_qualified or bool(qualification and qualification.strip())
        decade_tokens = []
        for period_id in spacetime["periodIds"]:
            period = period_by_id.get(period_id)
            if not period:
                raise ValueError("Spacetime record references an unknown period")
            decade_tokens.append({"id": period_id, "label": period["label"]})
        curated_entries = folder_entries[object_id]
        curated_types = _sorted_unique_tokens(
            value_token("curated_container_type", entry["type"], public_id=f"EXP:CURATED_TYPE:{entry['type'].upper()}")
            for entry in curated_entries
        )
        creator_label = str(metadata["creatorAttribution"]).strip()
        object_type_label = str(metadata["objectType"]).strip()
        source_label = str(metadata["sourceName"]).strip()
        record = {
            "objectId": object_id,
            "medium": _sorted_unique_tokens(representations.get("medium", [])),
            "theme": _sorted_unique_tokens(representations.get("theme", [])),
            "movement_context": _sorted_unique_tokens(representations.get("movement_context", [])),
            "decade": _sorted_unique_tokens(decade_tokens),
            "geography": _sorted_unique_tokens(geography_tokens),
            "geography_class": _sorted_unique_tokens(
                value_token("geography_class", value) for value in geography_classes
            ),
            "geography_mapping_state": _sorted_unique_tokens(
                value_token("geography_mapping_state", value) for value in geography_states
            ),
            "curated_container": _sorted_unique_tokens(
                {"id": entry["id"], "label": entry["label"]} for entry in curated_entries
            ),
            "curated_container_type": curated_types,
            "source": value_token("source", source_label),
            "object_type": value_token("object_type", object_type_label),
            "creator": value_token("creator", creator_label),
            "creatorLabel": creator_label,
            "sourceCollectionPresent": object_id in source_collection_present,
            "temporalPrecision": spacetime["time"]["precision"],
            "startYear": spacetime["time"]["startYearInclusive"],
            "endYear": spacetime["time"]["endYearInclusive"],
            "geographyMappingStates": sorted(geography_states),
            "geographyClasses": sorted(geography_classes),
            "geographyQualified": geography_qualified,
            "multiRegion": len(spacetime["geographyIds"]) > 1,
            "sourceDiagnostics": source_diagnostics[object_id],
        }
        normalized.append(record)

    public_text = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    if UUID_PATTERN.search(public_text):
        raise ValueError("internal UUID entered normalized Exploration records")
    if PRIVATE_VALUE_PATTERN.search(public_text):
        raise ValueError("raw folder/TRACE identity or URL entered normalized Exploration records")
    if any(record["objectId"] in held_ids for record in normalized):
        raise ValueError("held object entered normalized Exploration records")
    return {
        "records": normalized,
        "receipts": receipts,
        "publicObjectCount": len(normalized),
        "heldObjectCount": len(held_ids),
        "publicObjectIds": public_ids,
        "heldObjectIds": held_ids,
    }
