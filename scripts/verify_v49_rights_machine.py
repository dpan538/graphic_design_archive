#!/usr/bin/env python3
"""Read-only deterministic verifier for the v49 Phase 1D rights/machine pack.

The verifier has no network or third-party dependency, writes no file or database,
and parses the frozen candidate JSON exactly once per invocation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/audits/v49-rights-machine"
PROMPT_A_DIR = ROOT / "docs/audits/v49-authority-research-delta"
HASH_CHUNK = 1024 * 1024

FROZEN_ASSETS = {
    "generated/public_surfaces_prefreeze_candidate_v48.json": {
        "bytes": 190_067_852,
        "sha256": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
    },
    "data/prefreeze_candidate_v48.sqlite": {
        "bytes": 421_801_984,
        "sha256": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
    },
    "generated/prefreeze_candidate_v48_transfer_manifest.json": {
        "bytes": 21_752,
        "sha256": "865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b",
    },
    "data/prefreeze_candidate_v48_transfer_manifest.csv": {
        "bytes": 12_861,
        "sha256": "694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18",
    },
    "frontend/public/data/trace-v48/manifest.json": {
        "bytes": 83_900,
        "sha256": "1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23",
    },
}

CORE_RIGHTS_FILES = [
    "01_P0_CROSSWALK.md",
    "02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md",
    "03_VISUAL_ENTITY_CARDINALITY_MATRIX.md",
    "04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv",
    "05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv",
    "06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json",
    "07_DUAL_RELEASE_SEAL_CAS_SPEC.md",
    "08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md",
    "09_STABLE_ID_URI_POLICY.md",
    "10_NEGATIVE_TEST_SPEC.md",
    "agents/B1_RIGHTS_DELIVERY_RECEIPT.md",
    "agents/B2_VISUAL_ENTITY_DUAL_RELEASE_RECEIPT.md",
    "agents/B3_LEGACY_VISUAL_DISPOSITION_RECEIPT.md",
    "agents/B4_MACHINE_CONTRACT_RECEIPT.md",
    "agents/B5_NEGATIVE_ORACLE_RECEIPT.md",
]

FINAL_WRAPPER_FILES = [
    "00_EXECUTIVE_RECEIPT.md",
    "11_RIGHTS_MACHINE_GATE_RECEIPT.md",
    "AGENT_TASK_REGISTER.md",
]

NORMATIVE_FILES = [
    "ARCHITECTURE.md",
    "DATA_MODEL_V49.md",
    "READ_API_V1.md",
    "MIGRATION_V48_TO_V49.md",
    "ACCEPTANCE_GATES.md",
    "docs/architecture/DDL_DECISION_PACK_V49.md",
    "docs/adr/0001-canonical-postgres-and-read-only-release.md",
    "docs/adr/0002-immutable-data-versioning.md",
    "docs/adr/0003-runtime-repository-and-fixture-mode.md",
    "docs/adr/0004-research-claims-corpora-and-visual-registry.md",
]

DELIVERY_MODES = {
    "BLOCKED",
    "CITATION_ONLY",
    "LINK_ONLY",
    "SOURCE_VIEWER",
    "REMOTE_IMAGE",
}

TRUTH_HEADER = [
    "rule_id",
    "precedence",
    "takedown_effective_state",
    "rights_assessment_state",
    "provider_policy_evaluation_state",
    "attribution_bundle_state",
    "endpoint_health_condition",
    "qualified_locator_set",
    "effective_delivery_mode",
    "canonical_record_locator",
    "source_viewer_locator",
    "remote_pixel_locator",
    "thumbnail_locator",
    "image_service_locator",
    "reason_code",
    "rationale",
]

BASELINE_HEADER = [
    "group_id",
    "classification_unit",
    "overall_disposition",
    "rights_evidence_status",
    "provider_policy_status",
    "provider_mapping_status",
    "legacy_image_state",
    "legacy_rights_state",
    "legacy_display_policy",
    "rights_reviewed",
    "has_image_frame",
    "secondary_image_count",
    "locator_roles",
    "locator_hosts",
    "locator_schemes",
    "credit_present",
    "license_label_present",
    "rights_label_present",
    "surface_count",
    "visual_locator_occurrence_count",
    "malformed_locator_occurrence_count",
    "positive_rights_evidence_surface_count",
    "member_surface_id_set_sha256",
    "member_locator_occurrence_hash_set_sha256",
    "representative_surface_ids",
    "reason_codes",
    "candidate_sha256",
    "authority_role",
    "recovery_reference",
]

EXPECTED_PROMPT_A_GATES = {
    "AUDIT_BASELINE_VERIFIED": True,
    "INPUT_PARITY": True,
    "METADATA_SUPPORTED_CONFLICT_RESOLVED": True,
    "PARENT_ASSET_AUTHORITY_BOUNDARY_LOCKED": True,
    "UNCLASSIFIED_GRAPH_FACT": 0,
    "UNCLASSIFIED_RAW_SOURCE": 0,
    "UNKNOWN_RELATION_FAIL_CLOSED": True,
    "RESEARCH_CORPUS_POLICY_VERSIONED": True,
    "MISSINGNESS_BASELINE_VERSIONED": True,
    "AUTHORITY_RESEARCH_DELTA_CLOSED": True,
    "TARGET_20000_IS_ACCEPTANCE_GATE": False,
    "PRE_DDL_READY": False,
    "DATABASE_IMPLEMENTED": False,
    "FREEZE_READY": False,
    "PROMOTION_READY": False,
    "DEPLOYMENT_READY": False,
}

EXPECTED_VISUAL_COUNTS = {
    "candidateSurfaceVisualBundles": 15_923,
    "accountedSurfaceVisualBundles": 15_923,
    "unaccountedSurfaceVisualBundles": 0,
    "referenceBearingSurfaceVisualBundles": 15_788,
    "noReferenceSurfaceVisualBundles": 135,
    "externalVisualLocatorOccurrences": 15_790,
    "distinctExternalVisualLocatorValues": 15_788,
    "compactDispositionGroups": 71,
    "positiveRightsEvidenceSurfaceBundles": 0,
    "unclassifiedVisualReference": 0,
}

EXPECTED_LOCATOR_ROLES = {
    "image.evidenceImageUrl": 2,
    "image.sourceViewerUrl": 2,
    "image.url": 15_621,
    "image.viewerUrl": 165,
}

EXPECTED_VISUAL_HASHES = {
    "surfaceOrdinalIdSequenceSha256": "0ded26112f66e9b269dd6f7ca5978d9454e254e52241ca121f63c56368eab418",
    "surfaceIdSetSha256": "7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46",
    "sourceRecordIdSetSha256": "16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e",
    "rawVisualBundleSequenceSha256": "265cc790ffcc5b4c4dddf5ddbb29a894f35f92e166df474a744dafa0b7e8743e",
    "externalLocatorOccurrenceSequenceSha256": "1bbd68dfaf8661a1976fea56a2d121d807a42b5ed8a735094dda9868dcec5812",
    "externalLocatorValueSetSha256": "434dafb489119676615a6cd604a65286f17e2d8f2f18e48bf5e06943b6439e28",
    "classifiedSurfaceSequenceSha256": "2ba50afc2175e350895f9b7b76615ba72cf2175cf4599b13b49f5ee107242abc",
}


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path, *, strict: bool = True) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        if strict:
            return json.load(handle, object_pairs_hook=strict_object)
        return json.load(handle)


def load_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        header = list(reader.fieldnames or [])
        if not header or len(header) != len(set(header)):
            raise ValueError(f"missing or duplicate TSV header: {path}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"ragged TSV row: {path}")
    return header, rows


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def stable_set_hash(values: Iterable[str]) -> str:
    distinct = sorted(set(values))
    text = "\n".join(distinct) + ("\n" if distinct else "")
    return sha256_text(text)


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(HASH_CHUNK)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def js_json_stringify(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def norm(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def token(value: Any) -> str:
    return re.sub(r"^_+|_+$", "", re.sub(r"[^a-z0-9]+", "_", norm(value).lower()))


def bool_token(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "missing"
    return f"invalid:{type(value).__name__}"


def collect_image_locators(image: Any, base_role: str) -> list[dict[str, str]]:
    if not isinstance(image, dict):
        return []
    pattern = re.compile(r"(url|uri|manifest|viewer|thumbnail|service|canvas|infojson|imageid)$", re.I)
    result: list[dict[str, str]] = []
    for key, value in image.items():
        if isinstance(value, str) and norm(value) and pattern.search(key):
            result.append({"role": f"{base_role}.{key}", "value": norm(value)})
    return result


def locator_shape(value: str) -> tuple[bool, str, str]:
    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower()
        return scheme in {"http", "https"} and bool(host), scheme or "invalid", host
    except (TypeError, ValueError):
        return False, "invalid", ""


class Receipt:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}
        self.metrics: dict[str, Any] = {}
        self.hashes: dict[str, str] = {}
        self.timings: dict[str, float] = {}
        self.errors: list[str] = []
        self.notes: list[str] = []

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if isinstance(value, Path):
            return value.as_posix()
        if isinstance(value, set):
            text_values = {str(item) for item in value}
            return {"count": len(value), "sha256": stable_set_hash(text_values)}
        if isinstance(value, Counter):
            return dict(value)
        if isinstance(value, tuple):
            return [Receipt._jsonable(item) for item in value]
        if isinstance(value, list):
            return [Receipt._jsonable(item) for item in value]
        if isinstance(value, dict):
            return {str(key): Receipt._jsonable(item) for key, item in value.items()}
        return value

    def check(self, name: str, actual: Any, expected: Any, *, detail: str | None = None) -> bool:
        passed = actual == expected
        entry: dict[str, Any] = {
            "actual": self._jsonable(actual),
            "expected": self._jsonable(expected),
            "pass": passed,
        }
        if detail:
            entry["detail"] = detail
        self.checks[name] = entry
        if not passed:
            self.errors.append(f"{name}: expected {expected!r}, got {actual!r}")
        return passed

    def require(self, name: str, passed: bool, *, detail: str) -> bool:
        self.checks[name] = {"pass": bool(passed), "detail": detail}
        if not passed:
            self.errors.append(f"{name}: {detail}")
        return passed


def classify_candidate(receipt: Receipt) -> dict[str, Any]:
    """Read and parse the candidate exactly once, reproducing B3 classifications."""

    started = time.monotonic()
    path = ROOT / "generated/public_surfaces_prefreeze_candidate_v48.json"
    raw_bytes = path.read_bytes()
    candidate_sha = sha256_bytes(raw_bytes)
    candidate_size = len(raw_bytes)
    payload = json.loads(raw_bytes)
    del raw_bytes
    surfaces = payload.get("surfaces") if isinstance(payload, dict) else None
    receipt.require(
        "candidate.surfaces_is_array",
        isinstance(surfaces, list),
        detail="candidate must contain one top-level surfaces array",
    )
    if not isinstance(surfaces, list):
        return {}

    surface_ids: list[str] = []
    source_record_ids: list[str] = []
    raw_visual_sequence: list[str] = []
    classified_sequence: list[str] = []
    locator_occurrence_sequence: list[str] = []
    locator_values: list[str] = []
    locator_roles: Counter[str] = Counter()
    overall_dispositions: Counter[str] = Counter()
    rights_statuses: Counter[str] = Counter()
    policy_statuses: Counter[str] = Counter()
    provider_statuses: Counter[str] = Counter()
    image_states: Counter[str] = Counter()
    rights_states: Counter[str] = Counter()
    display_policies: Counter[str] = Counter()
    rights_reviewed_values: Counter[str] = Counter()
    image_key_counts: Counter[str] = Counter()
    secondary_image_key_counts: Counter[str] = Counter()
    rights_key_counts: Counter[str] = Counter()
    reference_bearing = 0
    no_reference = 0
    positive_rights = 0
    unclassified = 0
    malformed_occurrences = 0
    bad_rows = 0

    for ordinal, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            bad_rows += 1
            continue
        surface_id = norm(surface.get("surfaceId"))
        source_record_id = norm(surface.get("sourceRecordId"))
        if not surface_id or not source_record_id:
            bad_rows += 1
        surface_ids.append(surface_id)
        source_record_ids.append(source_record_id)

        image = surface.get("image")
        rights = surface.get("rights")
        secondary_images = surface.get("images") if isinstance(surface.get("images"), list) else []
        rights_reviewed = (
            surface.get("reviewGates", {}).get("rightsReviewed")
            if isinstance(surface.get("reviewGates"), dict)
            else None
        )

        if isinstance(image, dict):
            image_key_counts.update(image.keys())
        for secondary in secondary_images:
            if isinstance(secondary, dict):
                secondary_image_key_counts.update(secondary.keys())
        if isinstance(rights, dict):
            rights_key_counts.update(rights.keys())

        locator_rows = collect_image_locators(image, "image")
        for index, secondary in enumerate(secondary_images):
            locator_rows.extend(collect_image_locators(secondary, f"images[{index}]"))

        shaped: list[dict[str, Any]] = []
        for locator in locator_rows:
            valid_external, scheme, host = locator_shape(locator["value"])
            shaped.append(
                {
                    **locator,
                    "validExternal": valid_external,
                    "scheme": scheme,
                    "host": host,
                }
            )
        external = [item for item in shaped if item["validExternal"]]
        malformed = [item for item in shaped if not item["validExternal"]]
        malformed_occurrences += len(malformed)
        for item in external:
            locator_occurrence_sequence.append(
                f"{ordinal}\t{surface_id}\t{item['role']}\t{item['value']}"
            )
            locator_values.append(item["value"])
            locator_roles[item["role"]] += 1

        image_shape_valid = isinstance(image, dict)
        rights_shape_valid = isinstance(rights, dict)
        image_state = norm(image.get("state")) if isinstance(image, dict) else ""
        rights_state = norm(rights.get("state")) if isinstance(rights, dict) else ""
        display_policy = norm(rights.get("displayPolicy")) if isinstance(rights, dict) else ""
        rights_label = norm(rights.get("label")) if isinstance(rights, dict) else ""
        credit = norm(image.get("credit")) if isinstance(image, dict) else ""
        license_label = norm(image.get("licenseLabel")) if isinstance(image, dict) else ""
        image_state = image_state or "(missing)"
        rights_state = rights_state or "(missing)"
        display_policy = display_policy or "(missing)"

        structured_text = " ".join(
            [rights_state, display_policy, rights_label, license_label]
        ).lower()
        explicit_takedown = bool(
            re.search(r"(^|[^a-z])(takedown|withdrawn|suppressed|blocked_by_request)([^a-z]|$)", structured_text)
        )
        explicit_conflict = bool(
            re.search(r"(^|[^a-z])(conflict|contradictory|disputed)([^a-z]|$)", structured_text)
        )
        explicit_stale = bool(
            re.search(r"(^|[^a-z])(stale|expired|review_overdue)([^a-z]|$)", structured_text)
        )
        candidate_only = bool(
            re.search(
                r"(candidate|required|review|unknown|unclear|unresolved|source_link_only|source_viewer)",
                token(rights_state),
            )
        )
        evidence_present = bool(
            rights_label
            or license_label
            or rights_state != "(missing)"
            or display_policy != "(missing)"
        )
        positive_rights_evidence = False
        provider_policy_status = "POLICY_UNKNOWN" if external else "NOT_APPLICABLE"
        provider_mapping_status = "UNMAPPED_PROVIDER" if external else "NOT_APPLICABLE"
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
            reasons.extend(
                [
                    "NO_VERSIONED_PROVIDER_POLICY_IN_CANDIDATE",
                    "NO_STABLE_PROVIDER_FK_IN_CANDIDATE",
                ]
            )
        if explicit_takedown:
            reasons.append("EXPLICIT_TAKEDOWN_TOKEN")
        if explicit_conflict:
            reasons.append("EXPLICIT_CONFLICT_TOKEN")
        if explicit_stale:
            reasons.append("EXPLICIT_STALE_TOKEN")
        if external and not positive_rights_evidence:
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
        elif provider_policy_status == "POLICY_UNKNOWN":
            overall = "POLICY_UNKNOWN"
        elif provider_mapping_status == "UNMAPPED_PROVIDER":
            overall = "UNMAPPED_PROVIDER"

        if external:
            reference_bearing += 1
        else:
            no_reference += 1
        if positive_rights_evidence:
            positive_rights += 1
        if not overall:
            unclassified += 1

        overall_dispositions[overall] += 1
        rights_statuses[rights_evidence_status] += 1
        policy_statuses[provider_policy_status] += 1
        provider_statuses[provider_mapping_status] += 1
        image_states[image_state] += 1
        rights_states[rights_state] += 1
        display_policies[display_policy] += 1
        rights_reviewed_values[bool_token(rights_reviewed)] += 1

        raw_bundle = {
            "image": image if image is not None else None,
            "images": secondary_images,
            "rights": rights if rights is not None else None,
            "rightsReviewed": rights_reviewed if rights_reviewed is not None else None,
        }
        raw_bundle_hash = sha256_text(js_json_stringify(raw_bundle))
        raw_visual_sequence.append(f"{ordinal}\t{surface_id}\t{raw_bundle_hash}")
        classified_sequence.append(
            f"{ordinal}\t{surface_id}\t{overall}\t{'|'.join(reasons)}"
        )

    counts = {
        "candidateSurfaceVisualBundles": len(surfaces),
        "accountedSurfaceVisualBundles": len(surface_ids) - bad_rows,
        "unaccountedSurfaceVisualBundles": bad_rows,
        "referenceBearingSurfaceVisualBundles": reference_bearing,
        "noReferenceSurfaceVisualBundles": no_reference,
        "externalVisualLocatorOccurrences": len(locator_occurrence_sequence),
        "distinctExternalVisualLocatorValues": len(set(locator_values)),
        "positiveRightsEvidenceSurfaceBundles": positive_rights,
        "unclassifiedVisualReference": unclassified,
    }
    hashes = {
        "surfaceOrdinalIdSequenceSha256": sha256_text(
            "\n".join(f"{i}\t{surface_id}" for i, surface_id in enumerate(surface_ids)) + "\n"
        ),
        "surfaceIdSetSha256": stable_set_hash(surface_ids),
        "sourceRecordIdSetSha256": stable_set_hash(source_record_ids),
        "rawVisualBundleSequenceSha256": sha256_text("\n".join(raw_visual_sequence) + "\n"),
        "externalLocatorOccurrenceSequenceSha256": sha256_text(
            "\n".join(locator_occurrence_sequence)
            + ("\n" if locator_occurrence_sequence else "")
        ),
        "externalLocatorValueSetSha256": stable_set_hash(locator_values),
        "classifiedSurfaceSequenceSha256": sha256_text("\n".join(classified_sequence) + "\n"),
    }

    receipt.check("candidate.parse_count", 1, 1)
    receipt.check("candidate.bytes", candidate_size, FROZEN_ASSETS[path.relative_to(ROOT).as_posix()]["bytes"])
    receipt.check("candidate.sha256", candidate_sha, FROZEN_ASSETS[path.relative_to(ROOT).as_posix()]["sha256"])
    receipt.check("candidate.bad_rows", bad_rows, 0)
    receipt.check("candidate.unique_surface_ids", len(set(surface_ids)), 15_923)
    receipt.check("candidate.unique_source_record_ids", len(set(source_record_ids)), 15_923)
    for name, expected in EXPECTED_VISUAL_COUNTS.items():
        if name == "compactDispositionGroups":
            continue
        receipt.check(f"candidate.counts.{name}", counts.get(name), expected)
    receipt.check("candidate.locator_roles", dict(sorted(locator_roles.items())), EXPECTED_LOCATOR_ROLES)
    receipt.check(
        "candidate.overall_disposition",
        dict(sorted(overall_dispositions.items())),
        {"NO_VISUAL_REFERENCE": 135, "RIGHTS_UNKNOWN": 15_788},
    )
    receipt.check(
        "candidate.rights_status",
        dict(sorted(rights_statuses.items())),
        {"NOT_APPLICABLE": 135, "RIGHTS_UNKNOWN": 15_788},
    )
    receipt.check(
        "candidate.policy_status",
        dict(sorted(policy_statuses.items())),
        {"NOT_APPLICABLE": 135, "POLICY_UNKNOWN": 15_788},
    )
    receipt.check(
        "candidate.provider_status",
        dict(sorted(provider_statuses.items())),
        {"NOT_APPLICABLE": 135, "UNMAPPED_PROVIDER": 15_788},
    )
    receipt.check("candidate.malformed_locator_occurrences", malformed_occurrences, 0)
    for name, expected in EXPECTED_VISUAL_HASHES.items():
        receipt.check(f"candidate.hashes.{name}", hashes.get(name), expected)

    receipt.metrics.update(
        {
            "CANDIDATE_PARSE_COUNT": 1,
            "LEGACY_INPUT_SURFACES": len(surfaces),
            "ACCOUNTED_INPUT_SURFACES": len(surface_ids) - bad_rows,
            "UNACCOUNTED_INPUT_SURFACES": bad_rows,
            "LEGACY_VISUAL_REFERENCE_BEARING": reference_bearing,
            "LEGACY_NO_VISUAL_REFERENCE": no_reference,
            "LEGACY_VISUAL_LOCATOR_OCCURRENCES": len(locator_occurrence_sequence),
            "LEGACY_POSITIVE_RIGHTS_COVERAGE": 0,
            "UNCLASSIFIED_VISUAL_REFERENCE": unclassified,
        }
    )
    receipt.hashes.update(hashes)
    receipt.timings["candidateParseAndClassificationSeconds"] = round(time.monotonic() - started, 6)
    return {
        "bytes": candidate_size,
        "sha256": candidate_sha,
        "counts": counts,
        "hashes": hashes,
        "distributions": {
            "overallDisposition": dict(sorted(overall_dispositions.items())),
            "rightsEvidenceStatus": dict(sorted(rights_statuses.items())),
            "providerPolicyStatus": dict(sorted(policy_statuses.items())),
            "providerMappingStatus": dict(sorted(provider_statuses.items())),
            "imageState": dict(sorted(image_states.items())),
            "rightsState": dict(sorted(rights_states.items())),
            "displayPolicy": dict(sorted(display_policies.items())),
            "rightsReviewed": dict(sorted(rights_reviewed_values.items())),
            "locatorRoles": dict(sorted(locator_roles.items())),
        },
        "observedSchema": {
            "imageKeys": dict(sorted(image_key_counts.items())),
            "secondaryImageKeys": dict(sorted(secondary_image_key_counts.items())),
            "rightsKeys": dict(sorted(rights_key_counts.items())),
        },
    }


def verify_frozen_assets(receipt: Receipt, candidate: dict[str, Any]) -> None:
    for relative, expected in FROZEN_ASSETS.items():
        path = ROOT / relative
        receipt.require(f"frozen.exists:{relative}", path.is_file(), detail="frozen asset exists")
        if not path.is_file():
            continue
        if relative == "generated/public_surfaces_prefreeze_candidate_v48.json" and candidate:
            size, digest = candidate["bytes"], candidate["sha256"]
        else:
            size, digest = sha256_file(path)
        receipt.check(f"frozen.bytes:{relative}", size, expected["bytes"])
        receipt.check(f"frozen.sha256:{relative}", digest, expected["sha256"])


def verify_prompt_a(receipt: Receipt) -> None:
    manifest_path = PROMPT_A_DIR / "MANIFEST.json"
    gate_path = PROMPT_A_DIR / "13_AUTHORITY_RESEARCH_GATE_RECEIPT.md"
    checksums_path = PROMPT_A_DIR / "CHECKSUMS.sha256"
    for path in (manifest_path, gate_path, checksums_path, ROOT / "scripts/verify_v49_authority_research_delta.py"):
        receipt.require(f"prompt_a.exists:{path.relative_to(ROOT)}", path.is_file(), detail="Prompt A evidence exists")
    if not manifest_path.is_file() or not gate_path.is_file() or not checksums_path.is_file():
        return

    manifest = load_json(manifest_path)
    gates = manifest.get("gates", {})
    for name, expected in EXPECTED_PROMPT_A_GATES.items():
        receipt.check(f"prompt_a.manifest_gate.{name}", gates.get(name), expected)

    receipt_text = gate_path.read_text(encoding="utf-8")
    parsed_receipt: dict[str, Any] = {}
    for name, raw_value in re.findall(r"^([A-Z0-9_]+)=([^\n]+)$", receipt_text, flags=re.M):
        value = raw_value.strip()
        if value == "true":
            parsed_receipt[name] = True
        elif value == "false":
            parsed_receipt[name] = False
        elif re.fullmatch(r"-?\d+", value):
            parsed_receipt[name] = int(value)
        else:
            parsed_receipt[name] = value
    for name, expected in EXPECTED_PROMPT_A_GATES.items():
        receipt.check(f"prompt_a.receipt_gate.{name}", parsed_receipt.get(name), expected)
    receipt.check("prompt_a.receipt.LEGACY_INPUT_SURFACES", parsed_receipt.get("LEGACY_INPUT_SURFACES"), 15_923)
    receipt.check("prompt_a.receipt.ACCOUNTED_INPUT_SURFACES", parsed_receipt.get("ACCOUNTED_INPUT_SURFACES"), 15_923)
    receipt.check("prompt_a.receipt.UNACCOUNTED_INPUT_SURFACES", parsed_receipt.get("UNACCOUNTED_INPUT_SURFACES"), 0)

    manifest_assets = {
        item.get("path"): item for item in manifest.get("frozenAssets", []) if isinstance(item, dict)
    }
    for relative, expected in FROZEN_ASSETS.items():
        item = manifest_assets.get(relative, {})
        receipt.check(f"prompt_a.frozen_bytes:{relative}", item.get("bytes"), expected["bytes"])
        receipt.check(f"prompt_a.frozen_sha256:{relative}", item.get("sha256"), expected["sha256"])

    # Prompt A's package is immutable, but three root normative files were authorized
    # to change in Phase 1D. Verify every package-local checksum and its verifier while
    # explicitly excluding only those cross-phase normative entries.
    failures: list[str] = []
    checked = 0
    excluded = {
        "ACCEPTANCE_GATES.md",
        "DATA_MODEL_V49.md",
        "MIGRATION_V48_TO_V49.md",
    }
    for line_number, raw_line in enumerate(checksums_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line:
            continue
        try:
            expected_digest, relative = raw_line.split("  ", 1)
        except ValueError:
            failures.append(f"line:{line_number}")
            continue
        if relative in excluded:
            continue
        if not (
            relative.startswith("docs/audits/v49-authority-research-delta/")
            or relative == "scripts/verify_v49_authority_research_delta.py"
        ):
            failures.append(f"unexpected-scope:{relative}")
            continue
        target = ROOT / relative
        if not target.is_file():
            failures.append(relative)
            continue
        _, actual_digest = sha256_file(target)
        checked += 1
        if actual_digest != expected_digest:
            failures.append(relative)
    receipt.check("prompt_a.scoped_checksum_failures", failures, [])
    receipt.check("prompt_a.scoped_checksum_entries", checked, 25)
    receipt.notes.append(
        "Prompt A checksum recheck excludes only three authorized Phase 1D normative integration paths; all Prompt A package-local evidence and its verifier remain bound."
    )


def verify_required_rights_files(receipt: Receipt) -> None:
    missing = [relative for relative in CORE_RIGHTS_FILES if not (AUDIT_DIR / relative).is_file()]
    receipt.check("rights.required_core_files_missing", missing, [])
    empty = [
        relative
        for relative in CORE_RIGHTS_FILES
        if (AUDIT_DIR / relative).is_file() and (AUDIT_DIR / relative).stat().st_size == 0
    ]
    receipt.check("rights.required_core_files_empty", empty, [])

    present_wrappers = [relative for relative in FINAL_WRAPPER_FILES if (AUDIT_DIR / relative).is_file()]
    if present_wrappers:
        missing_wrappers = [relative for relative in FINAL_WRAPPER_FILES if not (AUDIT_DIR / relative).is_file()]
        receipt.check("rights.final_wrapper_files_missing", missing_wrappers, [])
    else:
        receipt.notes.append(
            "Final executive/gate/register wrappers were not present during detached B7 verification; they are owned by the primary task and are checked once any one appears."
        )


def verify_truth_table(receipt: Receipt) -> None:
    path = AUDIT_DIR / "04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv"
    header, rows = load_tsv(path)
    receipt.check("truth.header", header, TRUTH_HEADER)
    receipt.check("truth.rows", len(rows), 20)
    rule_ids = [row["rule_id"] for row in rows]
    precedences = [int(row["precedence"]) for row in rows]
    receipt.check("truth.unique_rule_ids", len(set(rule_ids)), 20)
    receipt.check("truth.unique_precedences", len(set(precedences)), 20)
    receipt.check("truth.strict_precedence_order", precedences, sorted(precedences))
    receipt.check("truth.delivery_modes", {row["effective_delivery_mode"] for row in rows}, DELIVERY_MODES)
    remote_rows = [row for row in rows if row["effective_delivery_mode"] == "REMOTE_IMAGE"]
    receipt.check("truth.remote_image_rule_count", len(remote_rows), 1)
    receipt.check("truth.remote_image_rule_id", remote_rows[0]["rule_id"] if remote_rows else None, "RD-080")
    if remote_rows:
        positive = remote_rows[0]
        receipt.check("truth.remote_image_rights", positive["rights_assessment_state"], "REMOTE_DISPLAY_PERMITTED")
        receipt.check("truth.remote_image_policy", positive["provider_policy_evaluation_state"], "REMOTE_DISPLAY_ALLOWED")
        receipt.check("truth.remote_image_attribution", positive["attribution_bundle_state"], "COMPLETE")
        receipt.check("truth.remote_image_health", positive["endpoint_health_condition"], "REMOTE_IMAGE_HEALTHY_FRESH")
        receipt.check("truth.remote_pixel_allow", positive["remote_pixel_locator"], "ALLOWLISTED_ONLY")

    lower_mode_leaks = [
        row["rule_id"]
        for row in rows
        if row["effective_delivery_mode"] != "REMOTE_IMAGE"
        and any(row[field] != "OMIT" for field in ("remote_pixel_locator", "thumbnail_locator", "image_service_locator"))
    ]
    receipt.check("truth.lower_mode_pixel_leaks", lower_mode_leaks, [])
    takedown_rows = rows[:2]
    receipt.check("truth.takedown_rule_ids", [row["rule_id"] for row in takedown_rows], ["RD-001", "RD-002"])
    receipt.check("truth.takedown_precedences", [row["precedence"] for row in takedown_rows], ["1", "2"])
    receipt.check("truth.takedown_modes", [row["effective_delivery_mode"] for row in takedown_rows], ["BLOCKED", "CITATION_ONLY"])
    terminal = rows[-1]
    receipt.check("truth.terminal_rule_id", terminal["rule_id"], "RD-999")
    receipt.check("truth.terminal_precedence", terminal["precedence"], "999")
    receipt.check("truth.terminal_mode", terminal["effective_delivery_mode"], "CITATION_ONLY")
    receipt.check("truth.terminal_reason", terminal["reason_code"], "FAIL_CLOSED_DEFAULT")
    receipt.check(
        "truth.terminal_locator_omission",
        [terminal[field] for field in (
            "canonical_record_locator",
            "source_viewer_locator",
            "remote_pixel_locator",
            "thumbnail_locator",
            "image_service_locator",
        )],
        ["OMIT"] * 5,
    )


def verify_b3_summary_and_tsv(receipt: Receipt, candidate: dict[str, Any]) -> None:
    summary_path = AUDIT_DIR / "06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json"
    tsv_path = AUDIT_DIR / "05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv"
    summary = load_json(summary_path)
    header, rows = load_tsv(tsv_path)
    receipt.check("b3.summary_schema", summary.get("schemaVersion"), "v49-phase1d-legacy-visual-disposition-v1")
    receipt.check("b3.tsv_header", header, BASELINE_HEADER)
    receipt.check("b3.tsv_rows", len(rows), 71)
    receipt.check("b3.tsv_unique_group_ids", len({row["group_id"] for row in rows}), 71)
    receipt.check("b3.tsv_blank_dispositions", sum(not row["overall_disposition"].strip() for row in rows), 0)
    receipt.check("b3.tsv_classification_units", {row["classification_unit"] for row in rows}, {"candidate_surface_visual_bundle"})

    counts = summary.get("counts", {})
    for name, expected in EXPECTED_VISUAL_COUNTS.items():
        receipt.check(f"b3.summary_counts.{name}", counts.get(name), expected)
    for name, actual in candidate.get("counts", {}).items():
        if name in counts:
            receipt.check(f"b3.candidate_summary_count.{name}", counts.get(name), actual)

    percentages = summary.get("percentages", {})
    receipt.check("b3.inventory_percentage", percentages.get("legacyVisualReferenceInventoried"), 100)
    receipt.check("b3.typed_percentage", percentages.get("legacyVisualReferenceTyped"), 100)
    receipt.check("b3.positive_rights_percentage", percentages.get("legacyPositiveRightsCoverage"), 0)
    gates = summary.get("gates", {})
    receipt.check("b3.gate_inventory", gates.get("LEGACY_VISUAL_REFERENCE_INVENTORIED"), "100%")
    receipt.check("b3.gate_typed", gates.get("LEGACY_VISUAL_REFERENCE_TYPED"), "100%")
    receipt.check("b3.gate_positive_rights", gates.get("LEGACY_POSITIVE_RIGHTS_COVERAGE"), "0.0000%")
    receipt.check("b3.gate_unclassified", gates.get("UNCLASSIFIED_VISUAL_REFERENCE"), 0)

    summary_hashes = summary.get("hashes", {})
    for name, expected in EXPECTED_VISUAL_HASHES.items():
        receipt.check(f"b3.summary_hashes.{name}", summary_hashes.get(name), expected)
        receipt.check(f"b3.candidate_summary_hash.{name}", summary_hashes.get(name), candidate.get("hashes", {}).get(name))
    distributions = summary.get("distributions", {})
    for name, actual in candidate.get("distributions", {}).items():
        if name in distributions:
            receipt.check(f"b3.candidate_summary_distribution.{name}", distributions.get(name), actual)
    receipt.check("b3.candidate_summary_observed_schema", summary.get("observedSchema"), candidate.get("observedSchema"))

    surface_sum = sum(int(row["surface_count"]) for row in rows)
    locator_sum = sum(int(row["visual_locator_occurrence_count"]) for row in rows)
    malformed_sum = sum(int(row["malformed_locator_occurrence_count"]) for row in rows)
    positive_sum = sum(int(row["positive_rights_evidence_surface_count"]) for row in rows)
    reference_surface_sum = sum(
        int(row["surface_count"])
        for row in rows
        if int(row["visual_locator_occurrence_count"]) > 0
    )
    no_reference_surface_sum = sum(
        int(row["surface_count"])
        for row in rows
        if int(row["visual_locator_occurrence_count"]) == 0
    )
    receipt.check("b3.tsv_surface_sum", surface_sum, 15_923)
    receipt.check("b3.tsv_locator_sum", locator_sum, 15_790)
    receipt.check("b3.tsv_malformed_sum", malformed_sum, 0)
    receipt.check("b3.tsv_positive_rights_sum", positive_sum, 0)
    receipt.check("b3.tsv_reference_bearing_surface_sum", reference_surface_sum, 15_788)
    receipt.check("b3.tsv_no_reference_surface_sum", no_reference_surface_sum, 135)
    receipt.check(
        "b3.tsv_candidate_hashes",
        {row["candidate_sha256"] for row in rows},
        {FROZEN_ASSETS["generated/public_surfaces_prefreeze_candidate_v48.json"]["sha256"]},
    )
    receipt.check(
        "b3.tsv_authority_roles",
        {row["authority_role"] for row in rows},
        {"canonical_migration_input_lexical_bytes"},
    )
    receipt.check(
        "b3.tsv_recovery_references",
        {row["recovery_reference"] for row in rows},
        {"0404c7f96f9189f576c4c5b1368061e4082e436b"},
    )
    actual_tsv_size, actual_tsv_sha = sha256_file(tsv_path)
    compact = summary.get("compactLedger", {})
    receipt.check("b3.tsv_sha256", actual_tsv_sha, compact.get("sha256"))
    receipt.check("b3.tsv_summary_rows", compact.get("rowsExcludingHeader"), 71)
    receipt.check("b3.tsv_summary_columns", compact.get("columns"), 29)
    receipt.check("b3.tsv_summary_surface_sum", compact.get("sumSurfaceCount"), 15_923)
    receipt.check("b3.tsv_summary_locator_sum", compact.get("sumVisualLocatorOccurrences"), 15_790)
    receipt.check("b3.tsv_summary_positive_sum", compact.get("sumPositiveRightsEvidenceSurfaceCount"), 0)
    receipt.metrics["B3_TSV_BYTES"] = actual_tsv_size
    receipt.hashes["b3CompactLedgerSha256"] = actual_tsv_sha


def verify_negative_oracle(receipt: Receipt) -> None:
    text = (AUDIT_DIR / "10_NEGATIVE_TEST_SPEC.md").read_text(encoding="utf-8")
    ids = re.findall(
        r"^\| `((?:RM-[NP]|MC-N|SC-N|AU-N)-\d{3})` \|",
        text,
        flags=re.M,
    )
    unique_ids = sorted(set(ids))
    expected_prefix_counts = {"RM": 11, "MC": 14, "SC": 9, "AU": 5}
    actual_prefix_counts = Counter(item.split("-")[0] for item in unique_ids)
    receipt.check("oracle.unique_case_count", len(unique_ids), 39)
    receipt.check("oracle.prefix_counts", dict(sorted(actual_prefix_counts.items())), expected_prefix_counts)
    receipt.check("oracle.duplicate_case_definitions", len(ids), 39)
    required = {
        "RM-N-001",
        "RM-N-003",
        "RM-N-004",
        "RM-N-006",
        "RM-N-008",
        "RM-P-001",
        "MC-N-003",
        "MC-N-006",
        "MC-N-014",
        "SC-N-001",
        "SC-N-002",
        "SC-N-003",
        "SC-N-004",
        "SC-N-007",
        "AU-N-001",
        "AU-N-002",
        "AU-N-004",
    }
    receipt.check("oracle.required_case_ids_missing", sorted(required - set(unique_ids)), [])
    receipt.require("oracle.structural_absence_defined", "`ABSENT(path)` means the property does not exist" in text, detail="ABSENT is structural, not null/CSS filtering")
    receipt.require("oracle.derived_anti_write_present", "Search cannot reverse-create canonical rows" in text and "TRACE cannot reverse-create canonical research facts" in text, detail="Search/TRACE anti-write oracles remain present")
    receipt.metrics["NEGATIVE_ORACLE_CASES"] = len(unique_ids)


def verify_normative_contract(receipt: Receipt) -> None:
    missing = [relative for relative in NORMATIVE_FILES if not (ROOT / relative).is_file()]
    receipt.check("normative.files_missing", missing, [])
    if missing:
        return
    texts = {relative: (ROOT / relative).read_text(encoding="utf-8") for relative in NORMATIVE_FILES}
    corpus = "\n".join(texts.values())

    old_terms: list[str] = []
    for relative, text in texts.items():
        for match in re.finditer(r"\b(?:PIXEL_ALLOWED|WITHHELD|registrySha256)\b", text):
            old_terms.append(f"{relative}:{text.count(chr(10), 0, match.start()) + 1}:{match.group(0)}")
    receipt.check("normative.old_public_terms", old_terms, [])

    example_violations: list[str] = []
    for relative, text in texts.items():
        for match in re.finditer(r"https?://[^\s)`>]*\.example[^\s)`>]*", text):
            value = match.group(0)
            if relative != "docs/architecture/DDL_DECISION_PACK_V49.md" or not value.startswith(
                "https://modern-gd-history.example/identity/v49/"
            ):
                example_violations.append(f"{relative}:{value}")
    receipt.check("normative.final_example_uri_violations", example_violations, [])
    ddl_text = texts["docs/architecture/DDL_DECISION_PACK_V49.md"]
    receipt.require(
        "normative.example_seed_only_guard",
        "non-resolvable namespace input only" in ddl_text
        and "must never be emitted or dereferenced as a final public URI" in ddl_text,
        detail="historical .example values are seed names only",
    )

    for kind in ("object", "relation", "claim", "source", "visual-reference"):
        receipt.require(
            f"normative.urn_kind:{kind}",
            f"urn:gdarchive:{kind}:" in corpus,
            detail=f"canonical {kind} URN is present",
        )
    receipt.require(
        "normative.public_visual_sha",
        "visualRegistrySha256" in corpus and "registry_sha256" in corpus,
        detail="public visual digest and internal mapping are explicit",
    )
    receipt.require(
        "normative.atomic_nullable_visual_pair",
        "atomic optional `(visualRegistryVersion,visualRegistrySha256)` pair" in corpus
        or "visual pair is atomically present or absent" in corpus,
        detail="visual version pair is atomic and nullable",
    )
    receipt.require(
        "normative.research_only_registry_absence",
        "research-only" in corpus and "RELEASE_VERSION_MISMATCH" in corpus,
        detail="absence and explicit mismatch are distinct",
    )
    receipt.require(
        "normative.positive_allowlist",
        "positive allowlist" in corpus,
        detail="serializer is built from a positive allowlist",
    )
    receipt.require(
        "normative.field_classes",
        all(f"`{name}`" in corpus for name in ("SAFE", "PUBLIC", "INTERNAL", "HELD")),
        detail="four public-exposure field classes are closed",
    )
    receipt.require(
        "normative.get_only_boundary",
        "GET/HEAD/OPTIONS-only" in corpus or "`GET`, `HEAD`, and `OPTIONS`" in corpus,
        detail="public API boundary is read-only",
    )
    receipt.require(
        "normative.five_modes",
        all(mode in corpus for mode in DELIVERY_MODES),
        detail="five delivery modes are represented",
    )
    receipt.require(
        "normative.dual_seal_cas",
        "draft → candidate → validated → sealed" in corpus
        and "CAS" in corpus
        and "sidecar" in corpus,
        detail="independent immutable seal/CAS protocol remains normative",
    )
    receipt.require(
        "normative.later_implementation_not_ddl_blocker",
        "does not by itself keep physical-schema specification blocked" in corpus
        or "not an empty-schema blocker" in corpus,
        detail="API/schema/CI/deploy absence is a later implementation gate",
    )


def verify_markdown_links(receipt: Receipt) -> None:
    broken: list[str] = []
    markdown_paths = [AUDIT_DIR / relative for relative in CORE_RIGHTS_FILES if relative.endswith(".md")]
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "#", "urn:")):
                continue
            relative_target = target.split("#", 1)[0]
            if not relative_target:
                continue
            resolved = (path.parent / relative_target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                broken.append(f"outside-root:{path.relative_to(ROOT)}->{target}")
                continue
            if not resolved.exists():
                broken.append(f"missing:{path.relative_to(ROOT)}->{target}")
    receipt.check("rights.broken_markdown_links", broken, [])


def verify_optional_rights_manifest(receipt: Receipt) -> None:
    manifest_path = AUDIT_DIR / "MANIFEST.json"
    checksums_path = AUDIT_DIR / "CHECKSUMS.sha256"
    receipt.check(
        "rights.manifest_checksum_presence_atomic",
        manifest_path.is_file(),
        checksums_path.is_file(),
    )
    if not manifest_path.is_file():
        receipt.notes.append("Rights package MANIFEST/CHECKSUMS were not present during detached B7 verification and were therefore not self-verified.")
        return
    manifest = load_json(manifest_path)
    artifacts = manifest.get("artifacts") or manifest.get("files") or []
    failures: list[str] = []
    checked = 0
    for item in artifacts:
        if not isinstance(item, dict):
            failures.append(str(item))
            continue
        relative = item.get("path")
        if not isinstance(relative, str):
            failures.append(str(relative))
            continue
        target = ROOT / relative
        if not target.is_file():
            failures.append(relative)
            continue
        size, digest = sha256_file(target)
        checked += 1
        if item.get("bytes") not in (None, size) or item.get("sha256") != digest:
            failures.append(relative)
    receipt.check("rights.manifest_artifact_failures", failures, [])
    receipt.metrics["RIGHTS_MANIFEST_ARTIFACTS_VERIFIED"] = checked

    checksum_failures: list[str] = []
    checksum_entries = 0
    for line_number, line in enumerate(checksums_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            checksum_failures.append(f"line:{line_number}")
            continue
        target = ROOT / relative
        if not target.is_file():
            checksum_failures.append(relative)
            continue
        _, digest = sha256_file(target)
        checksum_entries += 1
        if digest != expected:
            checksum_failures.append(relative)
    receipt.check("rights.checksum_failures", checksum_failures, [])
    receipt.metrics["RIGHTS_CHECKSUM_ENTRIES_VERIFIED"] = checksum_entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the complete JSON receipt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    receipt = Receipt()
    try:
        verify_required_rights_files(receipt)
        candidate = classify_candidate(receipt)
        if candidate:
            verify_frozen_assets(receipt, candidate)
            verify_b3_summary_and_tsv(receipt, candidate)
        verify_prompt_a(receipt)
        verify_truth_table(receipt)
        verify_negative_oracle(receipt)
        verify_normative_contract(receipt)
        verify_markdown_links(receipt)
        verify_optional_rights_manifest(receipt)
    except Exception as exc:
        receipt.errors.append(f"verifier exception: {type(exc).__name__}: {exc}")

    receipt.timings["totalSeconds"] = round(time.monotonic() - started, 6)
    receipt.metrics["CHECK_COUNT"] = len(receipt.checks)
    receipt.metrics["FAILURE_COUNT"] = len(receipt.errors)
    status = "PASS" if not receipt.errors else "FAIL"
    output = {
        "schema": "v49.rights-machine-verifier-receipt/v1",
        "status": status,
        "process": {
            "pid": os.getpid(),
            "candidateParseCount": receipt.metrics.get("CANDIDATE_PARSE_COUNT", 0),
            "networkAccessed": False,
            "databaseOpened": False,
            "filesWritten": False,
        },
        "checks": dict(sorted(receipt.checks.items())),
        "metrics": dict(sorted(receipt.metrics.items())),
        "hashes": dict(sorted(receipt.hashes.items())),
        "timings": dict(sorted(receipt.timings.items())),
        "notes": receipt.notes,
        "errors": receipt.errors,
    }
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"{status}: {len(receipt.checks)} checks; {len(receipt.errors)} failures")
        for error in receipt.errors:
            print(f"- {error}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
