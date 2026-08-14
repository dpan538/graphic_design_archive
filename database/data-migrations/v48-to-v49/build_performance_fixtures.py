#!/usr/bin/env python3
"""Build nested, stratified, closure-complete Phase 2B performance fixtures.

The frozen staging directory is opened read-only.  No Candidate extraction or
semantic reinterpretation occurs: rows are selected and copied by the exact
deterministic IDs already present in staging.
"""

from __future__ import annotations

import argparse
import base64
import bisect
import csv
import hashlib
import json
import os
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


SCALES = (50, 250, 1000, 4000, 8000)
CANDIDATE_SHA = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
BASE_SCHEMA_SHA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
STAGING_MANIFEST_SHA = "01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322"
ATTESTATION_SHA = "11742e9afc577d976ea097540326c2697937290635735ad9d4466efce1758bcc"
IMPLEMENTATION_BASE = "86ba95cae9ecf12e58fcabb8170c9020e151b386"

IMPORT_FILES = (
    "source-assets.tsv", "mapping-versions.tsv", "migration-batches.tsv",
    "source-records.tsv", "field-literals.tsv", "entities.tsv",
    "archive-objects.tsv", "surface-ledgers.tsv", "object-source-links.tsv",
    "legacy-identities.tsv", "folders.tsv", "folder-assignments.tsv",
    "legacy-resolutions.tsv", "trace-nodes.tsv", "object-trace-nodes.tsv",
    "corpora.tsv", "corpus-versions.tsv", "corpus-memberships.tsv",
    "held-deltas.tsv", "visual-references.tsv", "visual-bridges.tsv",
    "visual-locators.tsv", "visual-dispositions.tsv",
    "visual-classifications.tsv", "rights-observations.tsv",
    "rights-assessments.tsv", "policy-evaluations.tsv",
    "delivery-assessments.tsv",
)


class FixtureError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def b64_text(value: str) -> str:
    decoded = json.loads(base64.b64decode(value, validate=True).decode("utf-8"))
    if not isinstance(decoded, str):
        raise FixtureError("BASE64_JSON_NOT_TEXT")
    return decoded


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if any(None in row for row in rows):
        raise FixtureError(f"RAGGED_TSV:{path.name}")
    return rows


def stable_key(profile: dict[str, Any]) -> str:
    return hashlib.sha256(
        (CANDIDATE_SHA + "|" + profile["archive_object_id"]).encode("utf-8")
    ).hexdigest()


def quantile_cuts(values: list[int]) -> list[int]:
    ordered = sorted(values)
    return [ordered[min(len(ordered) - 1, len(ordered) * n // 5)] for n in range(1, 5)]


def choose_nested(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    literal_cuts = quantile_cuts([p["literal_count"] for p in profiles])
    folder_cuts = quantile_cuts([p["folder_count"] for p in profiles])
    for profile in profiles:
        profile["literal_quantile"] = bisect.bisect_right(literal_cuts, profile["literal_count"])
        profile["folder_quantile"] = bisect.bisect_right(folder_cuts, profile["folder_count"])
        profile["source_bucket"] = int(profile["source_sha256"][:4], 16) % 8
        profile["priority"] = stable_key(profile)

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add(profile: dict[str, Any]) -> None:
        if profile["archive_object_id"] not in selected_ids:
            selected.append(profile)
            selected_ids.add(profile["archive_object_id"])

    # Guarantee all required marginal classes before round-robin expansion.
    for feature in (
        "research_disposition", "tier_class", "visual_present",
        "folder_quantile", "literal_quantile", "rights_state",
        "source_bucket",
    ):
        grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for profile in profiles:
            grouped[profile[feature]].append(profile)
        for value in sorted(grouped, key=lambda item: str(item)):
            add(min(grouped[value], key=lambda item: item["priority"]))

    for profile in sorted(
        profiles, key=lambda item: (-item["literal_count"], item["priority"]),
    )[:8]:
        add(profile)
    for profile in sorted(
        profiles, key=lambda item: (-item["folder_count"], item["priority"]),
    )[:8]:
        add(profile)

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for profile in profiles:
        if profile["archive_object_id"] in selected_ids:
            continue
        bucket = (
            profile["research_disposition"], profile["tier_class"],
            profile["visual_present"], profile["folder_quantile"],
            profile["literal_quantile"], profile["rights_state"],
            profile["source_bucket"],
        )
        buckets[bucket].append(profile)
    for rows in buckets.values():
        rows.sort(key=lambda item: item["priority"])
    keys = sorted(buckets, key=lambda item: tuple(str(value) for value in item))
    offset = 0
    while len(selected) < max(SCALES):
        progressed = False
        for key in keys:
            rows = buckets[key]
            if offset < len(rows):
                add(rows[offset])
                progressed = True
                if len(selected) == max(SCALES):
                    break
        if not progressed:
            break
        offset += 1
    if len(selected) != max(SCALES):
        raise FixtureError(f"SELECTION_UNDERFLOW:{len(selected)}")
    return selected


def descriptor(path: Path, rows: int) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "rows": rows, "sha256": sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--audit-manifest-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    stage = args.stage_dir.resolve()
    output_root = args.output_root.resolve()
    audit_dir = args.audit_manifest_dir.resolve()
    started = time.monotonic()
    if output_root.exists() and any(output_root.iterdir()):
        raise FixtureError("OUTPUT_ROOT_NOT_EMPTY")
    output_root.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = stage / "staging-manifest.json"
    if sha256_file(manifest_path) != STAGING_MANIFEST_SHA:
        raise FixtureError("STAGING_MANIFEST_DRIFT")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    surface_rows = read_tsv(stage / "surface-row-ledger.tsv")
    if len(surface_rows) != 15923:
        raise FixtureError("SURFACE_PROFILE_COUNT")
    profiles: list[dict[str, Any]] = []
    by_source: dict[str, dict[str, Any]] = {}
    by_object: dict[str, dict[str, Any]] = {}
    for row in surface_rows:
        profile = {
            "source_ordinal": int(row["source_ordinal"]),
            "surface_id_exact": row["surface_id_exact"],
            "source_record_id_exact": row["source_record_id_exact"],
            "archive_object_id": row["archive_object_uuid"],
            "source_record_id": row["raw_record_uuid"],
            "trace_root_legacy_id": row["trace_root_legacy_id"],
            "research_disposition": row["research_disposition"],
            "tier_class": "missing" if row["tier_presence"] == "MISSING" else row["tier_exact_value"],
            "literal_count": 0,
            "folder_count": 0,
            "visual_present": False,
            "source_sha256": hashlib.sha256(b"missing-source").hexdigest(),
            "rights_state": "missing",
        }
        profiles.append(profile)
        by_source[profile["source_record_id"]] = profile
        by_object[profile["archive_object_id"]] = profile

    for row in read_tsv(stage / "folder-assignments.tsv"):
        profile = by_object.get(row["archive_object_id"])
        if profile is not None:
            profile["folder_count"] += 1
    for row in read_tsv(stage / "visual-references.tsv"):
        profile = by_source.get(row["source_record_id"])
        if profile is not None:
            profile["visual_present"] = True

    with (stage / "field-literals.tsv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            profile = by_source.get(row["source_record_id"])
            if profile is not None:
                profile["literal_count"] += 1

    with (stage / "source-records.tsv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            profile = by_source.get(row["source_record_id"])
            if profile is None:
                continue
            try:
                payload = json.loads(base64.b64decode(row["raw_value_b64"], validate=True))
            except (ValueError, json.JSONDecodeError) as error:
                raise FixtureError("SOURCE_PROFILE_JSON_INVALID") from error
            source_name = payload.get("sourceName")
            if not isinstance(source_name, str):
                source_name = "missing-source"
            rights = payload.get("rights")
            rights_state = rights.get("state") if isinstance(rights, dict) else None
            profile["source_sha256"] = hashlib.sha256(source_name.encode("utf-8")).hexdigest()
            profile["rights_state"] = rights_state if isinstance(rights_state, str) else "missing"

    selected = choose_nested(profiles)
    object_rank = {p["archive_object_id"]: index for index, p in enumerate(selected, 1)}
    source_rank = {p["source_record_id"]: index for index, p in enumerate(selected, 1)}
    ledger_rank: dict[str, int] = {}
    for row in read_tsv(stage / "surface-ledgers.tsv"):
        rank = object_rank.get(row["archive_object_id"])
        if rank is not None:
            ledger_rank[row["legacy_surface_ledger_id"]] = rank

    folder_rank: dict[str, int] = {}
    for row in read_tsv(stage / "folder-assignments.tsv"):
        rank = object_rank.get(row["archive_object_id"])
        if rank is not None:
            folder_rank[row["folder_id"]] = min(rank, folder_rank.get(row["folder_id"], rank))
    trace_rank: dict[str, int] = {}
    for row in read_tsv(stage / "object-trace-nodes.tsv"):
        rank = object_rank.get(row["archive_object_id"])
        if rank is not None:
            trace_rank[row["trace_node_id"]] = rank
    reference_rank: dict[str, int] = {}
    for row in read_tsv(stage / "visual-references.tsv"):
        rank = source_rank.get(row["source_record_id"])
        if rank is not None:
            reference_rank[row["external_visual_reference_id"]] = rank
    bridge_rank: dict[str, int] = {}
    for row in read_tsv(stage / "visual-bridges.tsv"):
        rank = object_rank.get(row["archive_object_id"])
        if rank is not None:
            bridge_rank[row["object_visual_reference_id"]] = rank

    scale_dirs = {scale: output_root / f"scale-{scale:05d}" for scale in SCALES}
    for directory in scale_dirs.values():
        directory.mkdir()

    selected_headers = [
        "selection_rank", "source_ordinal", "archive_object_id", "source_record_id",
        "research_disposition", "tier_class", "visual_present", "folder_count",
        "folder_quantile", "literal_count", "literal_quantile", "rights_state",
        "source_sha256", "source_bucket", "selection_priority_sha256",
    ]
    for scale, directory in scale_dirs.items():
        with (directory / "selected-objects.tsv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(selected_headers)
            for rank, profile in enumerate(selected[:scale], 1):
                writer.writerow([
                    rank, profile["source_ordinal"], profile["archive_object_id"],
                    profile["source_record_id"], profile["research_disposition"],
                    profile["tier_class"], str(profile["visual_present"]).lower(),
                    profile["folder_count"], profile["folder_quantile"],
                    profile["literal_count"], profile["literal_quantile"],
                    profile["rights_state"], profile["source_sha256"],
                    profile["source_bucket"], profile["priority"],
                ])
        shutil.copyfile(
            directory / "selected-objects.tsv",
            audit_dir / f"scale-{scale:05d}-objects.tsv",
        )

    file_rows: dict[int, dict[str, int]] = {scale: {} for scale in SCALES}

    def fanout(
        filename: str, rank_for: Callable[[dict[str, str]], int | None],
    ) -> None:
        handles = {
            scale: (directory / filename).open("w", encoding="utf-8", newline="")
            for scale, directory in scale_dirs.items()
        }
        counts = {scale: 0 for scale in SCALES}
        try:
            with (stage / filename).open("r", encoding="utf-8", newline="") as source:
                reader = csv.DictReader(source, delimiter="\t")
                if reader.fieldnames is None:
                    raise FixtureError(f"MISSING_HEADER:{filename}")
                writers = {
                    scale: csv.DictWriter(
                        handle, fieldnames=reader.fieldnames, delimiter="\t",
                        lineterminator="\n", extrasaction="raise",
                    ) for scale, handle in handles.items()
                }
                for writer in writers.values():
                    writer.writeheader()
                for row in reader:
                    rank = rank_for(row)
                    if rank is None:
                        continue
                    for scale, writer in writers.items():
                        if rank <= scale:
                            writer.writerow(row)
                            counts[scale] += 1
        finally:
            for handle in handles.values():
                handle.close()
        for scale in SCALES:
            file_rows[scale][filename] = counts[scale]

    # Shared immutable singleton payload.  Symlinking avoids five 253 MB copies;
    # import.py resolves and reads it but never opens it for writing.
    for scale, directory in scale_dirs.items():
        os.symlink(stage / "source-assets.tsv", directory / "source-assets.tsv")
        file_rows[scale]["source-assets.tsv"] = 1
        for filename in (
            "mapping-versions.tsv", "migration-batches.tsv", "corpora.tsv",
            "corpus-versions.tsv", "legacy-resolutions.tsv",
        ):
            shutil.copyfile(stage / filename, directory / filename)
            file_rows[scale][filename] = max(0, sum(1 for _ in (directory / filename).open("rb")) - 1)

    fanout("source-records.tsv", lambda row: source_rank.get(row["source_record_id"]))
    fanout("field-literals.tsv", lambda row: source_rank.get(row["source_record_id"]))
    fanout("entities.tsv", lambda row: object_rank.get(row["entity_id"]))
    fanout("archive-objects.tsv", lambda row: object_rank.get(row["archive_object_id"]))
    fanout("surface-ledgers.tsv", lambda row: object_rank.get(row["archive_object_id"]))
    fanout("object-source-links.tsv", lambda row: object_rank.get(row["archive_object_id"]))

    identity_rank: dict[str, int] = {}
    for rank, profile in enumerate(selected, 1):
        for value in (
            profile["surface_id_exact"], profile["source_record_id_exact"],
            profile["trace_root_legacy_id"],
        ):
            identity_rank[value] = min(rank, identity_rank.get(value, rank))
    fanout(
        "legacy-identities.tsv",
        lambda row: identity_rank.get(b64_text(row["legacy_id_json_b64"])),
    )
    fanout("folders.tsv", lambda row: folder_rank.get(row["folder_id"]))
    fanout("folder-assignments.tsv", lambda row: object_rank.get(row["archive_object_id"]))
    fanout("trace-nodes.tsv", lambda row: trace_rank.get(row["trace_node_id"]))
    fanout("object-trace-nodes.tsv", lambda row: object_rank.get(row["archive_object_id"]))
    fanout("corpus-memberships.tsv", lambda row: object_rank.get(row["archive_object_id"]))
    fanout("held-deltas.tsv", lambda row: source_rank.get(row["source_record_id"]))
    fanout("visual-references.tsv", lambda row: source_rank.get(row["source_record_id"]))
    fanout("visual-bridges.tsv", lambda row: object_rank.get(row["archive_object_id"]))
    fanout("visual-locators.tsv", lambda row: source_rank.get(row["source_record_id"]))
    fanout("visual-dispositions.tsv", lambda row: ledger_rank.get(row["legacy_surface_ledger_id"]))
    fanout("visual-classifications.tsv", lambda row: ledger_rank.get(row["legacy_surface_ledger_id"]))
    fanout("rights-observations.tsv", lambda row: reference_rank.get(row["external_visual_reference_id"]))
    fanout("rights-assessments.tsv", lambda row: reference_rank.get(row["external_visual_reference_id"]))
    fanout("policy-evaluations.tsv", lambda row: bridge_rank.get(row["object_visual_reference_id"]))
    fanout("delivery-assessments.tsv", lambda row: bridge_rank.get(row["object_visual_reference_id"]))
    fanout("surface-row-ledger.tsv", lambda row: object_rank.get(row["archive_object_uuid"]))

    occurrence_sample: dict[str, bytes] = {}
    marker = b'"sourceRecordUuid":"'
    selected_sources = set(source_rank)
    with (stage / "field-occurrence-ledger.jsonl").open("rb") as handle:
        for line in handle:
            start = line.find(marker)
            if start < 0:
                continue
            start += len(marker)
            record_id = line[start:start + 36].decode("ascii", errors="ignore")
            if record_id in selected_sources and record_id not in occurrence_sample:
                occurrence_sample[record_id] = line
                if len(occurrence_sample) == max(SCALES):
                    break
    if len(occurrence_sample) != max(SCALES):
        raise FixtureError(f"FIELD_OCCURRENCE_SAMPLE_UNDERFLOW:{len(occurrence_sample)}")
    for scale, directory in scale_dirs.items():
        with (directory / "field-occurrence-sample.jsonl").open("wb") as handle:
            for profile in selected[:scale]:
                handle.write(occurrence_sample[profile["source_record_id"]])
        file_rows[scale]["field-occurrence-sample.jsonl"] = scale
        file_rows[scale]["selected-objects.tsv"] = scale

    receipts: dict[str, Any] = {}
    for scale, directory in scale_dirs.items():
        expected = {
            "surfaces": scale,
            "eligible": sum(p["research_disposition"] == "eligible" for p in selected[:scale]),
            "held": sum(p["research_disposition"] == "held" for p in selected[:scale]),
            "visual": file_rows[scale]["visual-references.tsv"],
            "locators": file_rows[scale]["visual-locators.tsv"],
            "fieldLiterals": file_rows[scale]["field-literals.tsv"],
            "folders": file_rows[scale]["folders.tsv"],
            "folderAssignments": file_rows[scale]["folder-assignments.tsv"],
        }
        files = {
            name: descriptor(directory / name, file_rows[scale][name])
            for name in set(IMPORT_FILES) | {
                "surface-row-ledger.tsv", "selected-objects.tsv",
                "field-occurrence-sample.jsonl",
            }
        }
        coverage = {
            "researchDisposition": sorted({p["research_disposition"] for p in selected[:scale]}),
            "tierClass": sorted({p["tier_class"] for p in selected[:scale]}),
            "visualPresent": sorted({p["visual_present"] for p in selected[:scale]}),
            "folderQuantiles": sorted({p["folder_quantile"] for p in selected[:scale]}),
            "literalQuantiles": sorted({p["literal_quantile"] for p in selected[:scale]}),
            "rightsState": sorted({p["rights_state"] for p in selected[:scale]}),
            "sourceSha256Distinct": len({p["source_sha256"] for p in selected[:scale]}),
            "maxFieldLiteralsPerObject": max(p["literal_count"] for p in selected[:scale]),
            "maxFolderMembershipsPerObject": max(p["folder_count"] for p in selected[:scale]),
        }
        fixture_manifest = {
            "schema": "gda-v49-phase2b-performance-fixture/v1",
            "scale": scale,
            "source": {
                "stagingAttestationSha256": ATTESTATION_SHA,
                "stagingManifestSha256": STAGING_MANIFEST_SHA,
                "candidateSha256": CANDIDATE_SHA,
                "baseSchemaSha256": BASE_SCHEMA_SHA,
                "implementationBaseCommit": IMPLEMENTATION_BASE,
            },
            "candidate": manifest["candidate"],
            "extractor": manifest["extractor"],
            "mapping": manifest["mapping"],
            "bundleBinding": manifest["bundleBinding"],
            "ids": manifest["ids"],
            "selection": {
                "algorithm": "nested-marginal-seed-composite-stratum-round-robin-v1",
                "sha256": files["selected-objects.tsv"]["sha256"],
            },
            "coverage": coverage,
            "expected": expected,
            "files": files,
        }
        fixture_path = directory / "performance-fixture-manifest.json"
        fixture_path.write_text(
            json.dumps(fixture_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        receipts[str(scale)] = {
            "directory": str(directory),
            "fixtureManifestSha256": sha256_file(fixture_path),
            "selectionSha256": files["selected-objects.tsv"]["sha256"],
            "expected": expected,
            "coverage": coverage,
            "inputBytes": sum(files[name]["bytes"] for name in IMPORT_FILES),
        }

    receipt = {
        "status": "PASS",
        "schema": "gda-v49-phase2b-performance-fixture-build/v1",
        "wallSeconds": round(time.monotonic() - started, 6),
        "stagingReused": True,
        "extractorRerun": False,
        "scales": receipts,
    }
    args.receipt.resolve().write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FixtureError, OSError, UnicodeError, csv.Error, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
