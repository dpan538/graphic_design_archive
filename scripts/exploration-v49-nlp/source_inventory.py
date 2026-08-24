#!/usr/bin/env python3
"""Public-only census of frozen and governed TRACE text seams."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Iterator, Mapping

from common import (
    CANONICAL_PATH,
    CONTEXT_RECORDS_PATH,
    EXPECTED_SHA256,
    PUBLIC_OBJECT_COUNT,
    ROUND6_REVIEW_PATH,
    SPACETIME_RECORDS_PATH,
    SQLITE_PATH,
    SourceValue,
    URL_PATTERN,
    _iter_json_array,
    ensure_public_object_id,
    load_context_records,
    load_json,
    load_public_boundary,
    load_public_canonical_surfaces,
    load_public_ids,
    sha256_text,
)
from field_governance import FIELDS, FieldDecision, registry_sha256
from language_script_audit import SCRIPT_ORDER, classify_unicode


MARKUP_PATTERN = re.compile(
    r"<[A-Za-z!/][^>]*>|&(?:[A-Za-z][A-Za-z0-9]+|#\d+|#x[0-9A-Fa-f]+);"
)
RIGHTS_PROVENANCE_PATTERN = re.compile(
    r"\b(?:copyright|rights? reserved|licen[cs]e|public domain|fair use|permission|"
    r"reproduction|terms of use|usage rights|rights statement|provenance|credit line|"
    r"accession|catalog(?:ue|ing)|digitization)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Observation:
    object_id: str
    text: str
    source_name: str = ""


def _metric_normalize(text: str) -> str:
    return unicodedata.normalize("NFC", " ".join(text.split()))


def _quantile_r7(values: Iterable[int], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _printable(value: float) -> int | float:
    return int(value) if float(value).is_integer() else round(value, 6)


def _open_sqlite() -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
        connection.close()
        raise RuntimeError("SQLite source is not query-only")
    return connection


@lru_cache(maxsize=1)
def _datasets() -> dict[str, Any]:
    public_ids = set(load_public_ids())
    surfaces = {value["surfaceId"]: value for value in load_public_canonical_surfaces()}
    context = {
        value["selectedRecord"]["surfaceId"]: value for value in load_context_records()
    }
    spacetime_document = load_json(SPACETIME_RECORDS_PATH)
    spacetime = {value["objectId"]: value for value in spacetime_document.get("records", [])}
    if set(surfaces) != public_ids or set(context) != public_ids or set(spacetime) != public_ids:
        raise RuntimeError("public source datasets do not share one cohort")
    source_names = {
        object_id: str(record["selectedRecord"]["rootMetadata"]["sourceName"]).strip()
        for object_id, record in context.items()
    }
    structured_labels: dict[str, tuple[str, ...]] = {}
    folder_members: dict[str, set[str]] = defaultdict(set)
    for object_id, surface in surfaces.items():
        labels = {
            str(surface.get("medium") or "").strip(),
            str(surface.get("objectType") or "").strip(),
        }
        for folder in surface.get("folders", []):
            title = str(folder.get("title") or "").strip()
            folder_id = str(folder.get("folderId") or "")
            if title:
                labels.add(title)
            if folder_id:
                folder_members[folder_id].add(object_id)
        structured_labels[object_id] = tuple(sorted(value for value in labels if value))
    return {
        "publicIds": public_ids,
        "surfaces": surfaces,
        "context": context,
        "spacetime": spacetime,
        "sourceNames": source_names,
        "structuredLabels": structured_labels,
        "folderMembers": folder_members,
    }


def iter_public_sources() -> Iterator[SourceValue]:
    """Yield only the three authoritative, governed aspect seams."""

    data = _datasets()
    for object_id in sorted(data["publicIds"]):
        source_name = data["sourceNames"][object_id]
        title = str(data["context"][object_id]["selectedRecord"]["title"]).strip()
        yield SourceValue(
            public_object_id=object_id,
            field_id="NLP-FIELD-001",
            role="OBJECT_TITLE",
            original_text=title,
            original_text_hash=sha256_text(title),
            source_artifact_hash=EXPECTED_SHA256["contextRecords"],
            source_name=source_name,
        )
        surface = data["surfaces"][object_id]
        for field_id, field_name, role in (
            ("NLP-FIELD-003", "sourceSubjects", "OBJECT_SUBJECT_TERMS"),
            ("NLP-FIELD-004", "sourceDescription", "SOURCE_NARRATIVE"),
        ):
            text = str(surface.get(field_name) or "").strip()
            if text:
                yield SourceValue(
                    public_object_id=object_id,
                    field_id=field_id,
                    role=role,
                    original_text=text,
                    original_text_hash=sha256_text(text),
                    source_artifact_hash=EXPECTED_SHA256["canonical"],
                    source_name=source_name,
                )


def _surface_observations(field_name: str) -> Iterator[Observation]:
    data = _datasets()
    for object_id in sorted(data["publicIds"]):
        yield Observation(
            object_id,
            str(data["surfaces"][object_id].get(field_name) or ""),
            data["sourceNames"][object_id],
        )


def _context_observations(field_name: str) -> Iterator[Observation]:
    data = _datasets()
    for object_id in sorted(data["publicIds"]):
        selected = data["context"][object_id]["selectedRecord"]
        value: Any
        if field_name == "title":
            value = selected.get("title")
        else:
            value = selected.get("rootMetadata", {}).get(field_name)
        yield Observation(object_id, str(value or ""), data["sourceNames"][object_id])


def _iter_global_array(name: str) -> Iterator[dict[str, Any]]:
    for value in _iter_json_array(CANONICAL_PATH, f'"{name}":['):
        if not isinstance(value, dict):
            raise RuntimeError(f"canonical {name} entry is not an object")
        yield value


def _iter_sqlite_observations(field_id: str) -> Iterator[Observation]:
    data = _datasets()
    public_ids = data["publicIds"]
    connection = _open_sqlite()
    try:
        if field_id == "NLP-FIELD-028":
            query = (
                "SELECT surface_id,value FROM object_metadata_rows "
                "WHERE table_kind='CITATIONS' AND label='Alternate representation' "
                "ORDER BY surface_id,row_order"
            )
            for row in connection.execute(query):
                if row["surface_id"] in public_ids:
                    yield Observation(
                        row["surface_id"], str(row["value"] or ""), data["sourceNames"][row["surface_id"]]
                    )
        elif field_id == "NLP-FIELD-029":
            capture_to_public = {
                row["capture_id"]: row["active_surface_id"]
                for row in connection.execute("SELECT capture_id,active_surface_id FROM capture_records")
                if row["active_surface_id"] in public_ids
            }
            for row in connection.execute(
                "SELECT object_or_capture_id,body FROM search_documents ORDER BY search_doc_id"
            ):
                reference = row["object_or_capture_id"]
                object_id = reference if reference in public_ids else capture_to_public.get(reference)
                if object_id:
                    yield Observation(
                        object_id, str(row["body"] or ""), data["sourceNames"][object_id]
                    )
        else:
            capture_field = {
                "NLP-FIELD-034": "source_title",
                "NLP-FIELD-035": "source_description",
                "NLP-FIELD-036": "source_notes",
                "NLP-FIELD-037": "source_subjects",
            }[field_id]
            for row in connection.execute(
                f"SELECT active_surface_id,{capture_field} FROM capture_records ORDER BY capture_id"
            ):
                object_id = row["active_surface_id"]
                if object_id in public_ids:
                    yield Observation(
                        object_id,
                        str(row[capture_field] or ""),
                        data["sourceNames"][object_id],
                    )
    finally:
        connection.close()


def _iter_observations(field_id: str) -> Iterator[Observation]:
    data = _datasets()
    if field_id == "NLP-FIELD-001":
        yield from _context_observations("title")
    elif field_id == "NLP-FIELD-002":
        yield from _surface_observations("title")
    elif field_id == "NLP-FIELD-003":
        yield from _surface_observations("sourceSubjects")
    elif field_id == "NLP-FIELD-004":
        yield from _surface_observations("sourceDescription")
    elif field_id == "NLP-FIELD-005":
        yield from _surface_observations("descriptionSummary")
    elif field_id == "NLP-FIELD-006":
        yield from _surface_observations("sourceNotes")
    elif field_id == "NLP-FIELD-007":
        yield from _context_observations("creatorAttribution")
    elif field_id == "NLP-FIELD-008":
        yield from _context_observations("objectType")
    elif field_id == "NLP-FIELD-009":
        yield from _surface_observations("medium")
    elif field_id == "NLP-FIELD-010":
        for object_id in sorted(data["publicIds"]):
            yield Observation(
                object_id,
                str(data["spacetime"][object_id].get("rawRegionDisplay") or ""),
                data["sourceNames"][object_id],
            )
    elif field_id == "NLP-FIELD-011":
        yield from _context_observations("sourceName")
    elif field_id in {"NLP-FIELD-012", "NLP-FIELD-013", "NLP-FIELD-014", "NLP-FIELD-015"}:
        name = {
            "NLP-FIELD-012": "historicalContextNote",
            "NLP-FIELD-013": "classificationRationale",
            "NLP-FIELD-014": "citationBasis",
            "NLP-FIELD-015": "uncertaintyNote",
        }[field_id]
        yield from _surface_observations(name)
    elif field_id in {"NLP-FIELD-016", "NLP-FIELD-017"}:
        name = "title" if field_id == "NLP-FIELD-016" else "note"
        for object_id in sorted(data["publicIds"]):
            for child in data["surfaces"][object_id].get("compoundChildren", []):
                yield Observation(
                    object_id, str(child.get(name) or ""), data["sourceNames"][object_id]
                )
    elif field_id == "NLP-FIELD-018":
        for object_id in sorted(data["publicIds"]):
            for folder in data["surfaces"][object_id].get("folders", []):
                yield Observation(
                    object_id, str(folder.get("title") or ""), data["sourceNames"][object_id]
                )
    elif field_id == "NLP-FIELD-019":
        for folder in _iter_global_array("folders"):
            members = data["folderMembers"].get(str(folder.get("folderId") or ""), set())
            if members:
                object_id = min(members)
                yield Observation(object_id, str(folder.get("scopeNote") or ""))
    elif field_id == "NLP-FIELD-020":
        for note in _iter_global_array("readingNotes"):
            members = data["folderMembers"].get(str(note.get("folderId") or ""), set())
            if members:
                yield Observation(min(members), str(note.get("scopeNote") or ""))
    elif field_id == "NLP-FIELD-021":
        for card in _iter_global_array("registrationCards"):
            for member in card.get("memberPages", []):
                object_id = member.get("surfaceId")
                if object_id in data["publicIds"]:
                    yield Observation(
                        object_id,
                        str(member.get("title") or ""),
                        data["sourceNames"][object_id],
                    )
    elif field_id == "NLP-FIELD-022":
        for dossier in _iter_global_array("researchDossiers"):
            if dossier.get("anchorSurfaceId") not in data["publicIds"]:
                continue
            for page in dossier.get("pageSequence", []):
                object_id = page.get("surfaceId")
                if object_id in data["publicIds"]:
                    yield Observation(
                        object_id, str(page.get("title") or ""), data["sourceNames"][object_id]
                    )
    elif field_id == "NLP-FIELD-023":
        for appendix in _iter_global_array("appendices"):
            object_id = appendix.get("surfaceId")
            if object_id in data["publicIds"]:
                yield Observation(
                    object_id,
                    str(appendix.get("title") or ""),
                    data["sourceNames"][object_id],
                )
    elif field_id == "NLP-FIELD-024":
        for object_id in sorted(data["publicIds"]):
            for representation in data["context"][object_id].get("representations", []):
                yield Observation(
                    object_id,
                    str(representation.get("label") or ""),
                    data["sourceNames"][object_id],
                )
    elif field_id == "NLP-FIELD-025":
        for object_id in sorted(data["publicIds"]):
            for value in data["spacetime"][object_id].get("recordedRegionDisplays", []):
                yield Observation(object_id, str(value or ""), data["sourceNames"][object_id])
    elif field_id == "NLP-FIELD-026":
        for object_id in sorted(data["publicIds"]):
            yield Observation(
                object_id,
                str(data["spacetime"][object_id].get("time", {}).get("sourceDisplay") or ""),
                data["sourceNames"][object_id],
            )
    elif field_id == "NLP-FIELD-027":
        review = load_json(ROUND6_REVIEW_PATH)
        for row in review.get("rows", []):
            for id_key, title_key in (
                ("anchorPublicId", "anchorTitle"),
                ("candidatePublicId", "candidateTitle"),
            ):
                object_id = ensure_public_object_id(row.get(id_key))
                yield Observation(
                    object_id, str(row.get(title_key) or ""), data["sourceNames"][object_id]
                )
    elif field_id in {"NLP-FIELD-028", "NLP-FIELD-029", "NLP-FIELD-034", "NLP-FIELD-035", "NLP-FIELD-036", "NLP-FIELD-037"}:
        yield from _iter_sqlite_observations(field_id)
    elif field_id == "NLP-FIELD-030":
        for object_id in sorted(data["publicIds"]):
            for table in data["surfaces"][object_id].get("tables", []):
                for row in table.get("rows", []):
                    for value in row:
                        yield Observation(object_id, str(value or ""), data["sourceNames"][object_id])
    elif field_id == "NLP-FIELD-031":
        for object_id in sorted(data["publicIds"]):
            evidence = data["surfaces"][object_id].get("collectionEvidence") or {}
            for name in ("label", "boundary"):
                yield Observation(
                    object_id, str(evidence.get(name) or ""), data["sourceNames"][object_id]
                )
    elif field_id == "NLP-FIELD-032":
        for object_id in sorted(data["publicIds"]):
            surface = data["surfaces"][object_id]
            for value in (
                (surface.get("rights") or {}).get("label"),
                (surface.get("image") or {}).get("licenseLabel"),
            ):
                yield Observation(object_id, str(value or ""), data["sourceNames"][object_id])
    elif field_id == "NLP-FIELD-033":
        names = (
            "boundary",
            "descriptiveSourceName",
            "descriptiveSourceRole",
            "imageHost",
            "narrativeEvidencePolicy",
            "recordHost",
        )
        for object_id in sorted(data["publicIds"]):
            provenance = data["surfaces"][object_id].get("sourceProvenance") or {}
            for name in names:
                if name in provenance:
                    yield Observation(
                        object_id, str(provenance.get(name) or ""), data["sourceNames"][object_id]
                    )
    else:
        raise KeyError(f"no source inventory extractor for {field_id}")


def _metrics(decision: FieldDecision) -> dict[str, Any]:
    data = _datasets()
    nonempty = 0
    object_ids: set[str] = set()
    value_counts: Counter[bytes] = Counter()
    source_value_counts: dict[str, Counter[bytes]] = defaultdict(Counter)
    source_totals: Counter[str] = Counter()
    lengths: list[int] = []
    scripts: Counter[str] = Counter()
    contains_source_identity = 0
    contains_structured_label = 0
    contains_url = 0
    contains_markup = 0
    contains_rights = 0
    for observation in _iter_observations(decision.field_id):
        object_id = ensure_public_object_id(observation.object_id)
        text = observation.text.strip()
        if not text:
            continue
        normalized = _metric_normalize(text)
        digest = hashlib.sha256(normalized.encode("utf-8")).digest()
        nonempty += 1
        object_ids.add(object_id)
        value_counts[digest] += 1
        source = observation.source_name or data["sourceNames"].get(object_id, "")
        source_value_counts[source][digest] += 1
        source_totals[source] += 1
        lengths.append(len(text))
        scripts[classify_unicode(text).primary_state] += 1
        lowered = normalized.casefold()
        source_label = data["sourceNames"].get(object_id, "").casefold()
        if len(source_label) >= 4 and source_label in lowered:
            contains_source_identity += 1
        labels = data["structuredLabels"].get(object_id, ())
        if any(len(label) >= 3 and label.casefold() in lowered for label in labels):
            contains_structured_label += 1
        contains_url += bool(URL_PATTERN.search(text))
        contains_markup += bool(MARKUP_PATTERN.search(text))
        contains_rights += bool(RIGHTS_PROVENANCE_PATTERN.search(text))

    boilerplate_affected = 0
    for source, counts in source_value_counts.items():
        denominator = source_totals[source]
        for count in counts.values():
            if count >= 3 and count / denominator >= 0.05:
                boilerplate_affected += count
    duplicate_groups = sum(1 for count in value_counts.values() if count > 1)
    return {
        "field_id": decision.field_id,
        "source_artifact": decision.source_artifact,
        "source_structure": decision.source_structure,
        "source_field": decision.source_field,
        "primary_role": decision.primary_role,
        "public_object_coverage": len(object_ids),
        "nonempty_count": nonempty,
        "distinct_value_count": len(value_counts),
        "character_length_p50": _printable(_quantile_r7(lengths, 0.50)),
        "character_length_p95": _printable(_quantile_r7(lengths, 0.95)),
        "character_length_p99": _printable(_quantile_r7(lengths, 0.99)),
        "character_length_max": max(lengths, default=0),
        "language_or_script_state": ";".join(
            f"{state}:{scripts[state]}" for state in SCRIPT_ORDER if scripts[state]
        ),
        "duplicate_rate": 0.0 if not nonempty else round((nonempty - len(value_counts)) / nonempty, 9),
        "duplicate_group_count": duplicate_groups,
        "boilerplate_rate": 0.0 if not nonempty else round(boilerplate_affected / nonempty, 9),
        "boilerplate_candidate_count": boilerplate_affected,
        "contains_source_identity": contains_source_identity > 0,
        "source_identity_literal_count": contains_source_identity,
        "contains_structured_label_leakage": contains_structured_label > 0,
        "structured_label_leakage_count": contains_structured_label,
        "contains_url": contains_url > 0,
        "url_count": contains_url,
        "contains_markup": contains_markup > 0,
        "markup_count": contains_markup,
        "contains_rights_or_provenance": contains_rights > 0,
        "rights_or_provenance_count": contains_rights,
        "public_safe": decision.public_safe,
        "rights_safe": decision.rights_safe,
        "governance_decision": decision.governance_decision,
        "reason": decision.reason,
        "prohibited_use": decision.prohibited_use,
    }


@lru_cache(maxsize=1)
def build_inventory_rows() -> tuple[dict[str, Any], ...]:
    rows = tuple(_metrics(decision) for decision in FIELDS)
    if len(rows) != len(FIELDS) or len({row["field_id"] for row in rows}) != len(FIELDS):
        raise RuntimeError("text field inventory does not reconcile to the registry")
    if any(row["primary_role"] == "UNCLASSIFIED_UNSAFE" for row in rows):
        raise RuntimeError("unclassified text field remains")
    return rows


def inventory_summary() -> dict[str, Any]:
    rows = build_inventory_rows()
    return {
        "schemaVersion": "trace-nlp-source-inventory/v1",
        "boundary": load_public_boundary().as_mapping(),
        "publicObjectsAudited": PUBLIC_OBJECT_COUNT,
        "heldObjectsIncluded": 0,
        "textSourceFieldCount": len(rows),
        "textSourceFieldClassifiedCount": len(rows),
        "unclassifiedTextFieldCount": 0,
        "fieldRegistrySha256": registry_sha256(),
        "rows": list(rows),
    }


def self_test() -> dict[str, Any]:
    summary = inventory_summary()
    by_id = {row["field_id"]: row for row in summary["rows"]}
    expected = {
        "NLP-FIELD-001": (7_995, 7_995, 7_630, 23, 109, 163, 806),
        "NLP-FIELD-003": (7_838, 7_838, 2_602, 60, 156, 220, 828),
        "NLP-FIELD-004": (7_432, 7_432, 4_933, 50, 200.45, 394.69, 5_000),
        "NLP-FIELD-005": (7_995, 7_995, 5_078, 155, 901, 980.12, 5_000),
    }
    for field_id, values in expected.items():
        row = by_id[field_id]
        actual = (
            row["public_object_coverage"],
            row["nonempty_count"],
            row["distinct_value_count"],
            row["character_length_p50"],
            row["character_length_p95"],
            row["character_length_p99"],
            row["character_length_max"],
        )
        if actual != values:
            raise AssertionError(f"source inventory metric changed for {field_id}: {actual}")
    return {
        "status": "PASS",
        "publicObjectsAudited": summary["publicObjectsAudited"],
        "heldObjectsIncluded": summary["heldObjectsIncluded"],
        "textSourceFieldCount": summary["textSourceFieldCount"],
        "unclassifiedTextFieldCount": summary["unclassifiedTextFieldCount"],
        "fieldRegistrySha256": summary["fieldRegistrySha256"],
        "authoritativeFieldMetrics": {field_id: by_id[field_id] for field_id in expected},
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
