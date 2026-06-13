#!/usr/bin/env python3
"""Shard the public surface payload without changing the legacy JSON contract.

The current public archive payload is intentionally source-rich, but the single
JSON file is now large enough to make frontend builds and audits fragile. This
script writes deterministic sidecar shards plus a manifest. It does not remove
or rewrite the monolithic payload; existing scripts can keep reading it until
the frontend data layer is migrated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

DEFAULT_PAYLOAD = GENERATED / "public_surfaces_v1.json"
DEFAULT_GENERATED_SHARDS = GENERATED / "public_surfaces_v1_shards"
DEFAULT_PUBLIC_SHARDS = ROOT / "frontend" / "public" / "data" / "public_surface_shards_v1"
DEFAULT_METRICS = DATA / "public_surface_payload_sharding_v1.csv"
DEFAULT_REPORT = DOCS / "PUBLIC_SURFACE_PAYLOAD_SHARDING_v1.md"

DEFAULT_CHUNK_SIZES = {
    "surfaces": 500,
    "researchDossiers": 500,
    "registrationCards": 25,
    "appendices": 1000,
    "readingNotes": 500,
    "folders": 250,
    "folderTypes": 250,
    "bookmarks": 500,
}


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any, base: Path | None = None) -> dict[str, Any]:
    data = json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "path": relative(path) if base is None else path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def safe_refresh_dir(path: Path) -> None:
    """Refresh only known shard roots under this repository."""
    resolved = path.resolve()
    allowed_roots = [
        GENERATED.resolve(),
        (ROOT / "frontend" / "public" / "data").resolve(),
        DATA.resolve(),
        Path("/private/tmp").resolve(),
    ]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        raise ValueError(f"Refusing to refresh unsafe shard path: {path}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def chunked(values: list[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [values[index : index + size] for index in range(0, len(values), size)]


def id_for(item: Any, fields: tuple[str, ...]) -> str:
    if not isinstance(item, dict):
        return ""
    for field in fields:
        value = item.get(field)
        if value:
            return str(value)
    return ""


def build_surface_index(shards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for shard in shards:
        shard_path = shard["path"]
        for offset, surface in enumerate(shard["items"]):
            surface_id = id_for(surface, ("surfaceId", "id"))
            if surface_id:
                index[surface_id] = {"path": shard_path, "offset": offset}
    return index


def build_dossier_index(shards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for shard in shards:
        shard_path = shard["path"]
        for offset, dossier in enumerate(shard["items"]):
            dossier_id = id_for(dossier, ("dossierId", "surfaceId", "anchorSurfaceId", "id"))
            if dossier_id:
                index[dossier_id] = {"path": shard_path, "offset": offset}
            anchor_id = id_for(dossier, ("anchorSurfaceId",))
            if anchor_id and anchor_id not in index:
                index[anchor_id] = {"path": shard_path, "offset": offset}
    return index


def build_folder_index(folders: list[Any], section_path: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for offset, folder in enumerate(folders):
        folder_id = id_for(folder, ("id", "folderId", "slug"))
        if folder_id:
            index[folder_id] = {"path": section_path, "offset": offset}
    return index


def write_list_section(root: Path, key: str, values: list[Any], chunk_size: int) -> dict[str, Any]:
    if len(values) <= chunk_size:
        path = root / "sections" / f"{key}.json"
        written = write_json(path, values, base=root)
        written.update({"count": len(values), "chunked": False})
        return written

    shards: list[dict[str, Any]] = []
    for shard_index, items in enumerate(chunked(values, chunk_size)):
        path = root / "sections" / key / f"{key}_{shard_index:04d}.json"
        written = write_json(path, items, base=root)
        first_id = id_for(items[0], ("surfaceId", "dossierId", "anchorSurfaceId", "id", "folderId", "slug")) if items else ""
        last_id = id_for(items[-1], ("surfaceId", "dossierId", "anchorSurfaceId", "id", "folderId", "slug")) if items else ""
        shards.append(
            {
                "path": written["path"],
                "bytes": written["bytes"],
                "sha256": written["sha256"],
                "count": len(items),
                "firstId": first_id,
                "lastId": last_id,
                "items": items,
            }
        )

    manifest_shards = [{key_: value for key_, value in shard.items() if key_ != "items"} for shard in shards]
    return {
        "count": len(values),
        "chunked": True,
        "chunkSize": chunk_size,
        "shardCount": len(shards),
        "shards": manifest_shards,
        "_rawShards": shards,
    }


def clean_manifest_sections(sections: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, section in sections.items():
        if isinstance(section, dict):
            cleaned[key] = {field: value for field, value in section.items() if field != "_rawShards"}
        else:
            cleaned[key] = section
    return cleaned


def write_sharded_payload(
    payload: dict[str, Any],
    output_roots: list[Path] | None = None,
    source_payload: Path = DEFAULT_PAYLOAD,
    chunk_sizes: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Write deterministic shards and return one manifest summary per root."""
    roots = output_roots or [DEFAULT_GENERATED_SHARDS, DEFAULT_PUBLIC_SHARDS]
    sizes = dict(DEFAULT_CHUNK_SIZES)
    sizes.update(chunk_sizes or {})

    source_bytes = source_payload.stat().st_size if source_payload.exists() else len(json_bytes(payload))
    summaries: list[dict[str, Any]] = []

    for root in roots:
        safe_refresh_dir(root)
        sections: dict[str, Any] = {}
        indexes: dict[str, Any] = {}

        for key, value in payload.items():
            if isinstance(value, list):
                sections[key] = write_list_section(root, key, value, sizes.get(key, 500))
            else:
                written = write_json(root / "sections" / f"{key}.json", value, base=root)
                written.update({"count": 1, "chunked": False})
                sections[key] = written

        surface_shards = sections.get("surfaces", {}).get("_rawShards", [])
        if surface_shards:
            surface_index = build_surface_index(surface_shards)
            indexes["surfacesById"] = write_json(root / "indexes" / "surfaces_by_id.json", surface_index, base=root)
            indexes["surfacesById"]["count"] = len(surface_index)
        else:
            surfaces_section = sections.get("surfaces", {})
            surface_index = build_surface_index(
                [{"path": surfaces_section.get("path", ""), "items": payload.get("surfaces", [])}]
            )
            indexes["surfacesById"] = write_json(root / "indexes" / "surfaces_by_id.json", surface_index, base=root)
            indexes["surfacesById"]["count"] = len(surface_index)

        dossier_shards = sections.get("researchDossiers", {}).get("_rawShards", [])
        if dossier_shards:
            dossier_index = build_dossier_index(dossier_shards)
            indexes["researchDossiersByAnchor"] = write_json(
                root / "indexes" / "research_dossiers_by_anchor.json", dossier_index, base=root
            )
            indexes["researchDossiersByAnchor"]["count"] = len(dossier_index)

        folders = payload.get("folders", [])
        if isinstance(folders, list):
            folders_section = sections.get("folders", {})
            section_path = folders_section.get("path") or (
                folders_section.get("shards", [{}])[0].get("path") if folders_section.get("shards") else ""
            )
            folder_index = build_folder_index(folders, section_path)
            indexes["foldersById"] = write_json(root / "indexes" / "folders_by_id.json", folder_index, base=root)
            indexes["foldersById"]["count"] = len(folder_index)

        manifest = {
            "schema": "public_surface_shards_v1",
            "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "sourcePayload": relative(source_payload),
            "sourcePayloadBytes": source_bytes,
            "manifestPath": "manifest.json",
            "counts": {
                key: len(value) if isinstance(value, list) else 1
                for key, value in payload.items()
            },
            "sections": clean_manifest_sections(sections),
            "indexes": indexes,
        }
        manifest_info = write_json(root / "manifest.json", manifest, base=root)
        manifest["manifest"] = manifest_info
        manifest["outputRoot"] = relative(root)
        summaries.append(manifest)

    return summaries


def section_metric_rows(manifest: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_root = str(manifest.get("outputRoot", ""))
    for key, section in manifest.get("sections", {}).items():
        if section.get("chunked"):
            shard_bytes = [int(shard.get("bytes", 0)) for shard in section.get("shards", [])]
            rows.append(
                {
                    "output_root": output_root,
                    "section": key,
                    "count": str(section.get("count", 0)),
                    "chunked": "true",
                    "shard_count": str(section.get("shardCount", 0)),
                    "max_shard_bytes": str(max(shard_bytes) if shard_bytes else 0),
                    "total_section_bytes": str(sum(shard_bytes)),
                }
            )
        else:
            rows.append(
                {
                    "output_root": output_root,
                    "section": key,
                    "count": str(section.get("count", 0)),
                    "chunked": "false",
                    "shard_count": "1",
                    "max_shard_bytes": str(section.get("bytes", 0)),
                    "total_section_bytes": str(section.get("bytes", 0)),
                }
            )
    return rows


def write_metrics(path: Path, manifests: list[dict[str, Any]]) -> None:
    fields = [
        "output_root",
        "section",
        "count",
        "chunked",
        "shard_count",
        "max_shard_bytes",
        "total_section_bytes",
    ]
    rows: list[dict[str, str]] = []
    for manifest in manifests:
        rows.extend(section_metric_rows(manifest))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def mib(value: int | float) -> float:
    return round(float(value) / 1024 / 1024, 2)


def write_report(path: Path, manifests: list[dict[str, Any]], metrics_path: Path) -> None:
    manifest = manifests[0]
    rows = section_metric_rows(manifest)
    max_shard = max((int(row["max_shard_bytes"]) for row in rows), default=0)
    surface_row = next((row for row in rows if row["section"] == "surfaces"), None)
    dossier_row = next((row for row in rows if row["section"] == "researchDossiers"), None)
    output_roots = ", ".join(f"`{item.get('outputRoot')}`" for item in manifests)

    lines = [
        "# Public Surface Payload Sharding v1",
        "",
        "## Purpose",
        "",
        (
            "The generated public surface payload has crossed the point where a single static JSON file is a safe "
            "build primitive. This pass creates deterministic sidecar shards while keeping the legacy monolithic "
            "payload in place for existing audits and frontend routes."
        ),
        "",
        "## Current Payload",
        "",
        f"- Source payload: `{manifest.get('sourcePayload')}`",
        f"- Source payload size: {mib(int(manifest.get('sourcePayloadBytes', 0)))} MiB",
        f"- Output roots: {output_roots}",
        f"- Metrics CSV: `{relative(metrics_path)}`",
        "",
        "## Shard Result",
        "",
        f"- Maximum section/shard size: {mib(max_shard)} MiB",
    ]
    if surface_row:
        lines.append(
            f"- `surfaces`: {surface_row['count']} rows across {surface_row['shard_count']} shards; "
            f"largest shard {mib(int(surface_row['max_shard_bytes']))} MiB"
        )
    if dossier_row:
        lines.append(
            f"- `researchDossiers`: {dossier_row['count']} rows across {dossier_row['shard_count']} shards; "
            f"largest shard {mib(int(dossier_row['max_shard_bytes']))} MiB"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- This is a sidecar export. It does not change `frontend/src/data/public_surface_mock_v0.json` or the current frontend import path.",
            "- `manifest.json` records section counts, shard files, byte sizes, and SHA-256 hashes.",
            "- `indexes/surfaces_by_id.json` maps each `surfaceId` to its shard path and offset.",
            "- `indexes/research_dossiers_by_anchor.json` maps dossier/anchor ids for later lazy loading.",
            "- The shard directories are generated artifacts and are ignored in git until the frontend data layer is migrated to consume them directly.",
            "- Local image files, thumbnails, screenshots, cookies, sessions, and raw third-party payloads are not created.",
            "",
            "## Next Use",
            "",
            (
                "The next frontend optimization can replace the static import with manifest-driven loading, "
                "starting from folder/index views before migrating surface detail pages. Until that migration is "
                "complete, release audits should continue treating the monolithic payload as canonical."
            ),
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write public surface payload sidecar shards.")
    parser.add_argument("--payload", default=str(DEFAULT_PAYLOAD), help="Source public payload JSON.")
    parser.add_argument("--generated-root", default=str(DEFAULT_GENERATED_SHARDS), help="Generated shard output root.")
    parser.add_argument("--public-root", default=str(DEFAULT_PUBLIC_SHARDS), help="Frontend public shard output root.")
    parser.add_argument("--generated-only", action="store_true", help="Only write generated/ shards, not frontend/public.")
    parser.add_argument("--surfaces-per-shard", type=int, default=DEFAULT_CHUNK_SIZES["surfaces"])
    parser.add_argument("--dossiers-per-shard", type=int, default=DEFAULT_CHUNK_SIZES["researchDossiers"])
    parser.add_argument("--registration-cards-per-shard", type=int, default=DEFAULT_CHUNK_SIZES["registrationCards"])
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS), help="CSV summary output path.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload_path = Path(args.payload)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    roots = [Path(args.generated_root)]
    if not args.generated_only:
        roots.append(Path(args.public_root))
    chunk_sizes = {
        "surfaces": args.surfaces_per_shard,
        "researchDossiers": args.dossiers_per_shard,
        "registrationCards": args.registration_cards_per_shard,
    }
    manifests = write_sharded_payload(payload, output_roots=roots, source_payload=payload_path, chunk_sizes=chunk_sizes)
    metrics_path = Path(args.metrics)
    report_path = Path(args.report)
    write_metrics(metrics_path, manifests)
    write_report(report_path, manifests, metrics_path)

    first = manifests[0]
    rows = section_metric_rows(first)
    max_shard = max((int(row["max_shard_bytes"]) for row in rows), default=0)
    print(f"source_payload={relative(payload_path)}")
    print(f"source_payload_mib={mib(first.get('sourcePayloadBytes', 0))}")
    print(f"output_roots={','.join(str(manifest.get('outputRoot')) for manifest in manifests)}")
    print(f"max_shard_mib={mib(max_shard)}")
    print(f"metrics={relative(metrics_path)}")
    print(f"report={relative(report_path)}")


if __name__ == "__main__":
    main()
