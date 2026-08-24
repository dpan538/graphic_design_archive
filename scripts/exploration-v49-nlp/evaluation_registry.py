#!/usr/bin/env python3
"""Mechanically verified NLP evaluation and leakage-control pair registry."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit, urlunsplit

from common import (
    EXPECTED_SHA256,
    LEDGER_PATH,
    ROOT,
    SQLITE_PATH,
    ensure_public_object_id,
    sha256_json,
    sha256_text,
)
from language_script_audit import classify_unicode
from source_inventory import _datasets


REGISTRY_VERSION = "trace-nlp-evaluation-pairs-v1"
MAX_CONTROLS_PER_TYPE = 64
WORD_PATTERN = re.compile(r"\w+", re.UNICODE)
KNOWN_REPRESENTATION_CONTROL_TYPE = "SAME_SOURCE_ITEM_DUPLICATE_IMPORT_IDENTITY"
KNOWN_REPRESENTATION_PAIR_CLASS = "KNOWN_REPRESENTATION_POSITIVE"
KNOWN_REPRESENTATION_TASK = "NLP_TASK_A_KNOWN_REPRESENTATION_RETRIEVAL"

EVALUATION_ROW_FIELDS = (
    "pair_id",
    "public_object_id_a",
    "public_object_id_b",
    "task",
    "pair_class",
    "control_type",
    "verification_source",
    "verification_strength",
    "verification_artifact_path",
    "verification_artifact_sha256",
    "eligibility_artifact_path",
    "eligibility_artifact_sha256",
    "verification_locator_sha256",
    "field_aspects_available",
    "language_script",
    "source_identity",
    "source_item_identity",
    "representation_qualifier",
    "archive_native_variant_evidence",
    "reason",
    "prohibited_interpretation",
)

# The endpoints are public ledger identities.  The institutional item keys and
# canonical URLs are verified again against the immutable SQLite artifact.
EXPECTED_KNOWN_REPRESENTATION_PAIRS = (
    {
        "object_a": "SURF-AICTRACEV47R0002",
        "object_b": "SURF-HISTORICALAICTRACE2026V1R0021",
        "source_item_identity": "AIC:183283",
        "normalized_source_item_key": "183283",
        "canonical_source_url": "https://www.artic.edu/artworks/183283",
    },
    {
        "object_a": "SURF-CGS2026R0383",
        "object_b": "SURF-LOCTRACE2026ICC0337ACE0D517",
        "source_item_identity": "LOC:96523423",
        "normalized_source_item_key": "96523423",
        "canonical_source_url": "https://www.loc.gov/item/96523423",
    },
    {
        "object_a": "SURF-CGS2026R0740",
        "object_b": "SURF-LOCTRACE2026R02046",
        "source_item_identity": "LOC:2016648591",
        "normalized_source_item_key": "2016648591",
        "canonical_source_url": "https://www.loc.gov/item/2016648591",
    },
)

VERIFICATION_ARTIFACTS = {
    "context": (
        "frontend/generated/trace-context-v1/records.json",
        EXPECTED_SHA256["contextRecords"],
    ),
    "canonical": (
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        EXPECTED_SHA256["canonical"],
    ),
    "spacetime": (
        "frontend/generated/trace-spacetime-v1/record-index.json",
        EXPECTED_SHA256["spacetimeRecords"],
    ),
    "sqlite": (str(SQLITE_PATH.relative_to(ROOT)), EXPECTED_SHA256["sqlite"]),
}


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", " ".join(text.split()))


def _pair_id(control_type: str, object_a: str, object_b: str) -> str:
    first, second = sorted((object_a, object_b))
    return "NLP-PAIR-" + sha256_text(
        "\0".join((REGISTRY_VERSION, control_type, first, second))
    )[:20].upper()


def _aspects_for(object_id: str, data: Mapping[str, Any]) -> str:
    surface = data["surfaces"][object_id]
    values = ["NLP_TITLE"]
    if str(surface.get("sourceSubjects") or "").strip():
        values.append("NLP_SUBJECT")
    if str(surface.get("sourceDescription") or "").strip():
        values.append("NLP_SOURCE_NARRATIVE")
    return ",".join(values)


def _row(
    *,
    control_type: str,
    object_a: str,
    object_b: str,
    verification_source: str,
    verification_strength: str,
    verification_artifact: str,
    reason: str,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    first, second = sorted((ensure_public_object_id(object_a), ensure_public_object_id(object_b)))
    if first == second:
        raise ValueError("evaluation pair endpoints must differ")
    title_a = str(data["context"][first]["selectedRecord"]["title"])
    title_b = str(data["context"][second]["selectedRecord"]["title"])
    scripts = sorted(
        {
            classify_unicode(title_a).primary_state,
            classify_unicode(title_b).primary_state,
        }
    )
    same_source = data["sourceNames"][first] == data["sourceNames"][second]
    artifact_path, artifact_sha256 = VERIFICATION_ARTIFACTS[verification_artifact]
    return {
        "pair_id": _pair_id(control_type, first, second),
        "public_object_id_a": first,
        "public_object_id_b": second,
        "task": "NLP_TASK_E_SOURCE_LEAKAGE",
        "pair_class": "DIAGNOSTIC_NEGATIVE_CONTROL",
        "control_type": control_type,
        "verification_source": verification_source,
        "verification_strength": verification_strength,
        "verification_artifact_path": artifact_path,
        "verification_artifact_sha256": artifact_sha256,
        "eligibility_artifact_path": str(LEDGER_PATH.relative_to(ROOT)),
        "eligibility_artifact_sha256": EXPECTED_SHA256["ledger"],
        "verification_locator_sha256": sha256_json(
            {
                "artifactSha256": artifact_sha256,
                "controlType": control_type,
                "publicObjectIds": [first, second],
                "verificationSource": verification_source,
            }
        ),
        "field_aspects_available": f"{_aspects_for(first, data)}|{_aspects_for(second, data)}",
        "language_script": ",".join(scripts),
        "source_identity": "SAME" if same_source else "DIFFERENT",
        "source_item_identity": "",
        "representation_qualifier": "DIAGNOSTIC_NEGATIVE_CONTROL",
        "archive_native_variant_evidence": False,
        "reason": reason,
        "prohibited_interpretation": (
            "Diagnostic control only; it is not a historical non-relation, semantic non-relation, "
            "probability, or evidence of influence."
        ),
    }


def _canonical_item_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    scheme = "https" if parsed.scheme in {"http", "https"} else parsed.scheme
    host = parsed.netloc.casefold()
    path = re.sub(r"/+$", "", parsed.path)
    if host == "www.loc.gov":
        path = re.sub(r"^/pictures/item/", "/item/", path)
    return urlunsplit((scheme, host, path, parsed.query, parsed.fragment))


def _normalized_source_item_key(value: str) -> str:
    normalized = value.strip()
    numeric = re.search(r"(\d{5,})$", normalized)
    return numeric.group(1) if numeric else normalized.casefold()


def _known_representation_rows(data: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    expected_ids = {
        ensure_public_object_id(object_id)
        for expectation in EXPECTED_KNOWN_REPRESENTATION_PAIRS
        for object_id in (expectation["object_a"], expectation["object_b"])
    }
    placeholders = ",".join("?" for _value in sorted(expected_ids))
    connection = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        source_rows = {
            str(row["surface_id"]): dict(row)
            for row in connection.execute(
                "SELECT surface_id,source_record_id,source_object_key,source_document_id,"
                "source_name,source_url FROM objects WHERE surface_id IN ("
                + placeholders
                + ") ORDER BY surface_id",
                tuple(sorted(expected_ids)),
            )
        }
    finally:
        connection.close()
    if set(source_rows) != expected_ids:
        raise RuntimeError("known-representation endpoints changed in the frozen source")

    artifact_path, artifact_sha256 = VERIFICATION_ARTIFACTS["sqlite"]
    rows: list[dict[str, Any]] = []
    for expectation in EXPECTED_KNOWN_REPRESENTATION_PAIRS:
        first, second = sorted(
            (
                ensure_public_object_id(expectation["object_a"]),
                ensure_public_object_id(expectation["object_b"]),
            )
        )
        left = source_rows[first]
        right = source_rows[second]
        source_keys = {
            _normalized_source_item_key(str(left["source_object_key"])),
            _normalized_source_item_key(str(right["source_object_key"])),
        }
        canonical_urls = {
            _canonical_item_url(str(left["source_url"])),
            _canonical_item_url(str(right["source_url"])),
        }
        if source_keys != {expectation["normalized_source_item_key"]}:
            raise RuntimeError("known-representation source item key changed")
        if canonical_urls != {expectation["canonical_source_url"]}:
            raise RuntimeError("known-representation institutional item URL changed")
        if left["source_record_id"] == right["source_record_id"]:
            raise RuntimeError("known-representation endpoints no longer have distinct record IDs")
        if left["source_document_id"] == right["source_document_id"]:
            raise RuntimeError("known-representation endpoints no longer have distinct import documents")

        title_a = str(data["context"][first]["selectedRecord"]["title"])
        title_b = str(data["context"][second]["selectedRecord"]["title"])
        scripts = sorted(
            {
                classify_unicode(title_a).primary_state,
                classify_unicode(title_b).primary_state,
            }
        )
        locator_material = {
            "artifactSha256": artifact_sha256,
            "canonicalInstitutionalItemUrl": expectation["canonical_source_url"],
            "normalizedSourceItemKey": expectation["normalized_source_item_key"],
            "publicObjectIds": [first, second],
            "sourceDocumentIdHashes": sorted(
                sha256_text(str(row["source_document_id"])) for row in (left, right)
            ),
            "sourceRecordIdHashes": sorted(
                sha256_text(str(row["source_record_id"])) for row in (left, right)
            ),
        }
        rows.append(
            {
                "pair_id": _pair_id(KNOWN_REPRESENTATION_CONTROL_TYPE, first, second),
                "public_object_id_a": first,
                "public_object_id_b": second,
                "task": KNOWN_REPRESENTATION_TASK,
                "pair_class": KNOWN_REPRESENTATION_PAIR_CLASS,
                "control_type": KNOWN_REPRESENTATION_CONTROL_TYPE,
                "verification_source": expectation["canonical_source_url"],
                "verification_strength": (
                    "IMMUTABLE_FROZEN_EXACT_INSTITUTIONAL_SOURCE_ITEM_IDENTITY"
                ),
                "verification_artifact_path": artifact_path,
                "verification_artifact_sha256": artifact_sha256,
                "eligibility_artifact_path": str(LEDGER_PATH.relative_to(ROOT)),
                "eligibility_artifact_sha256": EXPECTED_SHA256["ledger"],
                "verification_locator_sha256": sha256_json(locator_material),
                "field_aspects_available": (
                    f"{_aspects_for(first, data)}|{_aspects_for(second, data)}"
                ),
                "language_script": ",".join(scripts),
                "source_identity": "SAME_INSTITUTION_DISTINCT_IMPORT_PIPELINES",
                "source_item_identity": expectation["source_item_identity"],
                "representation_qualifier": KNOWN_REPRESENTATION_CONTROL_TYPE,
                "archive_native_variant_evidence": False,
                "reason": (
                    "Distinct public import representations resolve to one exact institutional "
                    "source item in immutable frozen evidence."
                ),
                "prohibited_interpretation": (
                    "Importer-representation consistency only; no object-semantic, historical, "
                    "influence, archive-native alternate-title/translation, multilingual, or "
                    "cross-language inference."
                ),
            }
        )
    return tuple(rows)


def _first_pairs(groups: Iterable[Iterable[str]], *, limit: int) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for identifiers in groups:
        values = sorted(set(identifiers))
        if len(values) < 2:
            continue
        pair = (values[0], values[1])
        if pair not in seen:
            pairs.append(pair)
            seen.add(pair)
        if len(pairs) >= limit:
            break
    return pairs


def _same_title_controls(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for object_id in sorted(data["publicIds"]):
        title = _normalize(str(data["context"][object_id]["selectedRecord"]["title"]))
        groups[title].append(object_id)
    known_identity_pairs = {
        frozenset((expectation["object_a"], expectation["object_b"]))
        for expectation in EXPECTED_KNOWN_REPRESENTATION_PAIRS
    }
    candidates: list[tuple[str, str]] = []
    for title in sorted(groups):
        identifiers = sorted(set(groups[title]))
        if len(identifiers) < 2:
            continue
        selected = next(
            (
                pair
                for pair in combinations(identifiers, 2)
                if frozenset(pair) not in known_identity_pairs
            ),
            None,
        )
        if selected is not None:
            candidates.append(selected)
    # Known duplicate-import identities cannot also be negative same-title controls.
    return candidates[:512]


def _same_source_only_controls(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    by_source: dict[str, list[str]] = defaultdict(list)
    for object_id in sorted(data["publicIds"]):
        by_source[data["sourceNames"][object_id]].append(object_id)
    result: list[tuple[str, str]] = []
    for source in sorted(by_source):
        identifiers = by_source[source]
        found: tuple[str, str] | None = None
        for first, second in combinations(identifiers, 2):
            title_a = _normalize(str(data["context"][first]["selectedRecord"]["title"]))
            title_b = _normalize(str(data["context"][second]["selectedRecord"]["title"]))
            labels_a = set(data["structuredLabels"][first])
            labels_b = set(data["structuredLabels"][second])
            if title_a != title_b and labels_a.isdisjoint(labels_b):
                found = (first, second)
                break
        if found:
            result.append(found)
    return result[:MAX_CONTROLS_PER_TYPE]


def _same_notes_controls(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for object_id in sorted(data["publicIds"]):
        note = _normalize(str(data["surfaces"][object_id].get("sourceNotes") or ""))
        if note:
            groups[sha256_text(note)].append(object_id)
    candidates: list[list[str]] = []
    for key in sorted(groups):
        identifiers = groups[key]
        if len(identifiers) < 2:
            continue
        distinct_title_ids: list[str] = []
        seen_titles: set[str] = set()
        for object_id in identifiers:
            title = _normalize(str(data["context"][object_id]["selectedRecord"]["title"]))
            if title not in seen_titles:
                distinct_title_ids.append(object_id)
                seen_titles.add(title)
            if len(distinct_title_ids) == 2:
                break
        if len(distinct_title_ids) == 2:
            candidates.append(distinct_title_ids)
    return _first_pairs(candidates, limit=MAX_CONTROLS_PER_TYPE)


def _date_only_controls(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for object_id in sorted(data["publicIds"]):
        display = _normalize(
            str(data["spacetime"][object_id].get("time", {}).get("sourceDisplay") or "")
        )
        if display:
            groups[display].append(object_id)
    candidates: list[list[str]] = []
    for display in sorted(groups):
        identifiers = groups[display]
        selected: list[str] = []
        sources: set[str] = set()
        titles: set[str] = set()
        for object_id in identifiers:
            source = data["sourceNames"][object_id]
            title = _normalize(str(data["context"][object_id]["selectedRecord"]["title"]))
            if source not in sources and title not in titles:
                selected.append(object_id)
                sources.add(source)
                titles.add(title)
            if len(selected) == 2:
                break
        if len(selected) == 2:
            candidates.append(selected)
    return _first_pairs(candidates, limit=MAX_CONTROLS_PER_TYPE)


def _same_language_controls(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    by_script: dict[str, list[str]] = defaultdict(list)
    for object_id in sorted(data["publicIds"]):
        title = str(data["context"][object_id]["selectedRecord"]["title"])
        by_script[classify_unicode(title).primary_state].append(object_id)
    candidates: list[list[str]] = []
    for script in sorted(by_script):
        identifiers = by_script[script]
        selected: list[str] = []
        sources: set[str] = set()
        for object_id in identifiers:
            source = data["sourceNames"][object_id]
            if source not in sources:
                selected.append(object_id)
                sources.add(source)
            if len(selected) == 2:
                break
        if len(selected) == 2:
            candidates.append(selected)
    return _first_pairs(candidates, limit=MAX_CONTROLS_PER_TYPE)


def _common_word_controls(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    tokens_by_id: dict[str, set[str]] = {}
    document_frequency: Counter[str] = Counter()
    for object_id in sorted(data["publicIds"]):
        title = str(data["context"][object_id]["selectedRecord"]["title"])
        tokens = {token.casefold() for token in WORD_PATTERN.findall(title) if len(token) >= 4}
        tokens_by_id[object_id] = tokens
        document_frequency.update(tokens)
    common = sorted(token for token, count in document_frequency.items() if count >= 50)
    result: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for token in common:
        identifiers = [object_id for object_id in sorted(data["publicIds"]) if token in tokens_by_id[object_id]]
        for first, second in combinations(identifiers, 2):
            pair = (first, second)
            if data["sourceNames"][first] == data["sourceNames"][second]:
                continue
            if tokens_by_id[first] & tokens_by_id[second] != {token}:
                continue
            if pair not in seen:
                result.append(pair)
                seen.add(pair)
                break
        if len(result) >= MAX_CONTROLS_PER_TYPE:
            break
    return result


def build_evaluation_registry() -> tuple[dict[str, Any], ...]:
    data = _datasets()
    specifications = (
        (
            "SAME_TITLE_DIFFERENT_ID",
            _same_title_controls(data),
            "governed Context title exact-normalized equality plus distinct ledger identities",
            "MECHANICAL_EXACT_TEXT_AND_IDENTITY",
            "context",
            "Exact same title across distinct public objects tests identity collapse.",
        ),
        (
            "SAME_SOURCE_ONLY",
            _same_source_only_controls(data),
            "governed Context source identity with different title and disjoint structured labels",
            "MECHANICAL_METADATA_CONTROL",
            "context",
            "Shared provider alone tests source-style leakage.",
        ),
        (
            "RIGHTS_PROVENANCE_TEXT_SIMILARITY",
            _same_notes_controls(data),
            "frozen canonical sourceNotes exact hash with different governed titles",
            "MECHANICAL_EXACT_HASH_CONTROL",
            "canonical",
            "Repeated notes test rights, provenance, and provider-template leakage.",
        ),
        (
            "DATE_ONLY_MATCH",
            _date_only_controls(data),
            "governed Spacetime sourceDisplay equality with different source and title",
            "MECHANICAL_METADATA_CONTROL",
            "spacetime",
            "Matching recorded date alone must not become semantic affinity.",
        ),
        (
            "SAME_SCRIPT_ONLY",
            _same_language_controls(data),
            "deterministic Unicode script census with different source identity",
            "MECHANICAL_SCRIPT_CONTROL",
            "context",
            "Shared script alone tests language/script dominance.",
        ),
        (
            "SAME_COMMON_WORD_ONLY",
            _common_word_controls(data),
            "deterministic title token document-frequency census",
            "MECHANICAL_LEXICAL_CONTROL",
            "context",
            "One common title token tests generic lexical attraction.",
        ),
    )
    rows: list[dict[str, Any]] = list(_known_representation_rows(data))
    seen_pairs: set[tuple[str, str, str]] = set()
    for row in rows:
        seen_pairs.add(
            (
                row["control_type"],
                *sorted((row["public_object_id_a"], row["public_object_id_b"])),
            )
        )
    for control_type, pairs, source, strength, artifact, reason in specifications:
        for first, second in pairs:
            key = (control_type, *sorted((first, second)))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            rows.append(
                _row(
                    control_type=control_type,
                    object_a=first,
                    object_b=second,
                    verification_source=source,
                    verification_strength=strength,
                    verification_artifact=artifact,
                    reason=reason,
                    data=data,
                )
            )
    rows.sort(key=lambda row: row["pair_id"])
    if len({row["pair_id"] for row in rows}) != len(rows):
        raise RuntimeError("evaluation pair IDs are not unique")
    expected_fields = set(EVALUATION_ROW_FIELDS)
    if any(set(row) != expected_fields for row in rows):
        raise RuntimeError("evaluation registry row schema changed")
    return tuple(rows)


def evaluation_registry_sha256() -> str:
    return sha256_json({"version": REGISTRY_VERSION, "rows": build_evaluation_registry()})


def evaluation_summary() -> dict[str, Any]:
    rows = build_evaluation_registry()
    positives = [row for row in rows if row["pair_class"] == KNOWN_REPRESENTATION_PAIR_CLASS]
    negatives = [row for row in rows if row["pair_class"] == "DIAGNOSTIC_NEGATIVE_CONTROL"]
    controls = Counter(row["control_type"] for row in negatives)
    return {
        "schemaVersion": "trace-nlp-evaluation-registry-summary/v1",
        "registryVersion": REGISTRY_VERSION,
        "pairCount": len(rows),
        "knownRepresentationPositivePairCount": len(positives),
        "sameSourceItemDuplicateImportIdentityPairCount": sum(
            row["control_type"] == KNOWN_REPRESENTATION_CONTROL_TYPE for row in positives
        ),
        "verifiedCrossLanguagePositivePairCount": 0,
        "taskAPositivePairCount": len(positives),
        "taskBPositivePairCount": 0,
        "negativeControlPairCount": len(negatives),
        "controlTypeCounts": dict(sorted(controls.items())),
        "alternateRepresentationSourceRowCount": 1,
        "alternateRepresentationPositivePairCount": 0,
        "positivePairGenerationByModel": False,
        "registrySha256": evaluation_registry_sha256(),
    }


def self_test() -> dict[str, Any]:
    first = build_evaluation_registry()
    second = build_evaluation_registry()
    if first != second:
        raise AssertionError("evaluation registry is not deterministic")
    expected_positive_pairs = {
        frozenset((row["object_a"], row["object_b"]))
        for row in EXPECTED_KNOWN_REPRESENTATION_PAIRS
    }
    observed_positive_pairs: set[frozenset[str]] = set()
    for row in first:
        ensure_public_object_id(row["public_object_id_a"])
        ensure_public_object_id(row["public_object_id_b"])
        if row["public_object_id_a"] == row["public_object_id_b"]:
            raise AssertionError("self-pair entered evaluation registry")
        if set(row) != set(EVALUATION_ROW_FIELDS):
            raise AssertionError("evaluation row schema changed")
        if row["pair_class"] == KNOWN_REPRESENTATION_PAIR_CLASS:
            if row["task"] != KNOWN_REPRESENTATION_TASK:
                raise AssertionError("known-representation positive entered a non-Task-A lane")
            if row["control_type"] != KNOWN_REPRESENTATION_CONTROL_TYPE:
                raise AssertionError("duplicate-import identity qualifier is missing")
            if row["representation_qualifier"] != KNOWN_REPRESENTATION_CONTROL_TYPE:
                raise AssertionError("duplicate-import representation qualifier is missing")
            if row["archive_native_variant_evidence"] is not False:
                raise AssertionError("duplicate import was mislabeled as archive-native variant evidence")
            if row["verification_artifact_sha256"] != EXPECTED_SHA256["sqlite"]:
                raise AssertionError("positive verification artifact is not the immutable SQLite pin")
            if row["eligibility_artifact_sha256"] != EXPECTED_SHA256["ledger"]:
                raise AssertionError("positive public eligibility does not use the immutable ledger pin")
            observed_positive_pairs.add(
                frozenset((row["public_object_id_a"], row["public_object_id_b"]))
            )
        elif row["pair_class"] != "DIAGNOSTIC_NEGATIVE_CONTROL":
            raise AssertionError("unknown evaluation pair class entered the registry")
    if observed_positive_pairs != expected_positive_pairs:
        raise AssertionError("known-representation positive endpoint set changed")
    negative_pair_keys = {
        frozenset((row["public_object_id_a"], row["public_object_id_b"]))
        for row in first
        if row["pair_class"] == "DIAGNOSTIC_NEGATIVE_CONTROL"
    }
    if expected_positive_pairs & negative_pair_keys:
        raise AssertionError("known identity pair also entered the negative-control registry")
    summary = evaluation_summary()
    if summary["knownRepresentationPositivePairCount"] != 3:
        raise AssertionError("verified duplicate-import identity pair count changed")
    if summary["taskBPositivePairCount"] != 0:
        raise AssertionError("unverified Task B positive was created")
    return {"status": "PASS", **summary}


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
