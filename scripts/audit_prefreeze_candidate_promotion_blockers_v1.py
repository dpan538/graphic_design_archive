#!/usr/bin/env python3
"""Find candidate-payload rows that should not be blindly promoted.

The script is intentionally non-mutating. It reads the sandbox candidate payload
and capture records, then writes auditable blocker, geography repair, and
optional exclusion-delta CSVs. It does not edit capture data, public payloads,
frontend files, rights states, or image files.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"
CURRENT_EXCLUSION = DATA / "prefreeze_public_rebuild_exclusion_v1.csv"

BLOCKERS = DATA / "prefreeze_candidate_promotion_blockers_v1.csv"
GEO_REPAIR = DATA / "prefreeze_candidate_geo_repair_queue_v1.csv"
EXCLUSION_DELTA = DATA / "prefreeze_candidate_exclusion_delta_v1.csv"
SUMMARY = DATA / "prefreeze_candidate_promotion_blockers_summary_v1.csv"
REPORT = DOCS / "PREFREEZE_CANDIDATE_PROMOTION_BLOCKERS_v1.md"

BLOCKER_FIELDS = [
    "blocker_type",
    "severity",
    "source_file",
    "capture_id",
    "surface_id",
    "year",
    "region",
    "image_state",
    "source_name",
    "title",
    "source_url",
    "image_url",
    "recommendation",
]

GEO_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "year",
    "current_region",
    "place_text",
    "source_subjects",
    "source_name",
    "title",
    "source_url",
    "repair_hint",
]

EXCLUSION_FIELDS = [
    "source_file",
    "capture_id",
    "priority",
    "action_type",
    "risk_flags",
    "year",
    "region",
    "image_state",
    "title",
    "source_name",
    "recommendation",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

STAMP_TERMS = re.compile(r"\b(postage|postal|stamp|stamps|philatel|first day cover|souvenir sheet|commemorative issue)\b", re.I)
EVENT_TERMS = re.compile(
    r"\b(event photo|group photo|photo of|photograph of|opening reception|conference|symposium|seminar|workshop|poster session)\b",
    re.I,
)
WEAK_CONTEXT_TERMS = re.compile(r"\b(hero image|source profile|profile page|designer portrait|self[- ]?photographed|own work)\b", re.I)
DESIGN_TERMS = re.compile(r"\b(poster|typograph\w*|graphic design|identity|logo|publication|book cover|magazine|exhibition|advertis\w*|visual communication|zine)\b", re.I)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: clean(value) if isinstance(value, str) else value for key, value in row.items()})


def capture_files() -> list[Path]:
    return sorted(DATA.glob("capture_batch_*_records.csv"))


def capture_lookup() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for path in capture_files():
        for row in read_csv(path):
            capture_id = clean(row.get("capture_id"))
            if not capture_id:
                continue
            row = dict(row)
            row["_source_file"] = path.name
            lookup.setdefault(capture_id, row)
    return lookup


def current_exclusion_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in read_csv(CURRENT_EXCLUSION):
        source_file = clean(row.get("source_file"))
        capture_id = clean(row.get("capture_id"))
        if source_file and capture_id:
            keys.add((source_file, capture_id))
    return keys


def surface_image(surface: dict[str, Any]) -> dict[str, Any]:
    image = surface.get("image")
    return image if isinstance(image, dict) else {}


def image_state(surface: dict[str, Any]) -> str:
    return clean(surface_image(surface).get("state")) or "IMG00"


def parse_image_url(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    if text.startswith("{") and '"url"' in text:
        try:
            data = json.loads(text)
            return clean(data.get("url"))
        except json.JSONDecodeError:
            return text
    return text


def normalize_url(value: str) -> str:
    value = parse_image_url(value)
    if not value:
        return ""
    parsed = urlsplit(value)
    path = parsed.path.rstrip("/") or parsed.path
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def surface_image_url(surface: dict[str, Any]) -> str:
    return normalize_url(clean(surface_image(surface).get("url")))


def year(surface: dict[str, Any], row: dict[str, str] | None = None) -> str:
    for value in (
        surface.get("dateEnd"),
        surface.get("dateStart"),
        row.get("date_end") if row else "",
        row.get("date_start") if row else "",
    ):
        text = clean(value)
        if re.fullmatch(r"\d{4}", text):
            return text
    return ""


def region(surface: dict[str, Any], row: dict[str, str] | None = None) -> str:
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    for folder in folders:
        if isinstance(folder, dict) and folder.get("type") == "region":
            return clean(folder.get("title")) or "Unresolved region"
    return clean(row.get("source_place_text")) if row else "Unresolved region"


def row_blob(surface: dict[str, Any], row: dict[str, str] | None) -> str:
    surface_parts = [
        surface.get("title"),
        surface.get("sourceName"),
        surface.get("sourceDescription"),
        surface.get("sourceSubjects"),
        surface.get("sourceNotes"),
        surface.get("classificationRationale"),
    ]
    row_parts = []
    if row:
        row_parts = [
            row.get("source_title"),
            row.get("source_name"),
            row.get("source_description"),
            row.get("source_notes"),
            row.get("source_subjects"),
            row.get("source_object_type"),
            row.get("source_medium"),
            row.get("rights_basis"),
        ]
    return " ".join(clean(part) for part in [*surface_parts, *row_parts] if clean(part))


def blocker_row(
    blocker_type: str,
    severity: str,
    surface: dict[str, Any],
    row: dict[str, str] | None,
    recommendation: str,
) -> dict[str, str]:
    capture_id = clean(surface.get("sourceRecordId"))
    return {
        "blocker_type": blocker_type,
        "severity": severity,
        "source_file": clean(row.get("_source_file")) if row else "",
        "capture_id": capture_id,
        "surface_id": clean(surface.get("surfaceId")),
        "year": year(surface, row),
        "region": region(surface, row),
        "image_state": image_state(surface),
        "source_name": clean(surface.get("sourceName"))[:260],
        "title": clean(surface.get("title"))[:260],
        "source_url": clean(surface.get("sourceUrl")),
        "image_url": surface_image_url(surface),
        "recommendation": recommendation,
    }


def exclusion_row(blocker: dict[str, str], action_type: str, risk_flags: str) -> dict[str, str]:
    return {
        "source_file": blocker["source_file"],
        "capture_id": blocker["capture_id"],
        "priority": "P0",
        "action_type": action_type,
        "risk_flags": risk_flags,
        "year": blocker["year"],
        "region": blocker["region"],
        "image_state": blocker["image_state"],
        "title": blocker["title"],
        "source_name": blocker["source_name"],
        "recommendation": blocker["recommendation"],
    }


def geo_repair_row(surface: dict[str, Any], row: dict[str, str] | None) -> dict[str, str]:
    blob = row_blob(surface, row)
    hint = ""
    if row:
        place = clean(row.get("source_place_text"))
        subjects = clean(row.get("source_subjects"))
        if place and not place.lower().startswith("global"):
            hint = f"review placeText: {place[:160]}"
        elif subjects:
            hint = f"review subjects: {subjects[:160]}"
    if not hint:
        hint = "manual geography review; unresolved candidate lacks controlled mapping"
    return {
        "source_file": clean(row.get("_source_file")) if row else "",
        "capture_id": clean(surface.get("sourceRecordId")),
        "surface_id": clean(surface.get("surfaceId")),
        "year": year(surface, row),
        "current_region": region(surface, row),
        "place_text": clean(row.get("source_place_text"))[:260] if row else "",
        "source_subjects": clean(row.get("source_subjects"))[:260] if row else clean(surface.get("sourceSubjects"))[:260],
        "source_name": clean(surface.get("sourceName"))[:260],
        "title": clean(surface.get("title"))[:260],
        "source_url": clean(surface.get("sourceUrl")),
        "repair_hint": hint,
    }


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    captures = capture_lookup()
    existing_exclusions = current_exclusion_keys()

    by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        url = surface_image_url(surface)
        if url:
            by_url[url].append(surface)

    keep_duplicate_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for url, members in by_url.items():
        if len(members) < 2:
            continue
        ranked = sorted(
            members,
            key=lambda surface: (
                image_state(surface) != "IMG03",
                int(clean(surface.get("dateEnd")) or 9999),
                clean(surface.get("surfaceId")),
            ),
        )
        keep_duplicate_ids.add(clean(ranked[0].get("surfaceId")))
        duplicate_ids.update(clean(surface.get("surfaceId")) for surface in ranked[1:])

    blockers: list[dict[str, str]] = []
    geo_rows: list[dict[str, str]] = []
    exclusion_delta: list[dict[str, str]] = []
    seen_exclusion: set[tuple[str, str, str]] = set()

    for surface in surfaces:
        capture_id = clean(surface.get("sourceRecordId"))
        row = captures.get(capture_id)
        blob = row_blob(surface, row)
        current_region = region(surface, row)
        state = image_state(surface)
        y = int(year(surface, row) or 0)

        if clean(surface.get("surfaceId")) in duplicate_ids:
            blocker = blocker_row(
                "duplicate_exact_image_url",
                "P0",
                surface,
                row,
                "Exclude duplicate visual variant before public promotion; keep one representative source-return row.",
            )
            blockers.append(blocker)
            key = (blocker["source_file"], blocker["capture_id"], blocker["blocker_type"])
            if blocker["source_file"] and blocker["capture_id"] and (blocker["source_file"], blocker["capture_id"]) not in existing_exclusions and key not in seen_exclusion:
                exclusion_delta.append(exclusion_row(blocker, "duplicate_visual_variant_review", "exact_image_url_duplicate"))
                seen_exclusion.add(key)

        if current_region == "Unresolved region":
            blockers.append(
                blocker_row(
                    "unresolved_region",
                    "P1",
                    surface,
                    row,
                    "Repair controlled geography before final promotion; do not count unresolved rows as region coverage.",
                )
            )
            geo_rows.append(geo_repair_row(surface, row))

        if state in {"IMG00", "IMG04"}:
            blockers.append(
                blocker_row(
                    "source_visible_gap",
                    "P1",
                    surface,
                    row,
                    "Review source-visible status; unresolved IMG00/IMG04 rows are the remaining object source-visible gap.",
                )
            )

        is_recent_stamp = y >= 2010 and STAMP_TERMS.search(blob)
        if is_recent_stamp:
            blocker = blocker_row(
                "post_2010_stamp_like",
                "P1",
                surface,
                row,
                "Review as card/support unless the stamp has a strong graphic-design rationale and source depth.",
            )
            blockers.append(blocker)

        is_event = EVENT_TERMS.search(blob) is not None
        weak_context = WEAK_CONTEXT_TERMS.search(blob) is not None
        if is_event or weak_context:
            has_design_claim = DESIGN_TERMS.search(blob) is not None
            severity = "P1" if has_design_claim else "P0"
            blocker = blocker_row(
                "event_photo_or_context_image",
                severity,
                surface,
                row,
                "Reclassify as card/support material unless it is an item-level designed surface with source evidence.",
            )
            blockers.append(blocker)

    by_type = Counter(row["blocker_type"] for row in blockers)
    by_severity = Counter(row["severity"] for row in blockers)
    by_geo_source = Counter(row["source_name"] for row in geo_rows)
    summary_rows: list[dict[str, str]] = [
        {"metric": "candidate_surfaces_scanned", "value": str(len(surfaces)), "notes": "Candidate surfaces scanned for promotion blockers."},
        {"metric": "promotion_blocker_rows", "value": str(len(blockers)), "notes": "Total blocker rows; a surface may have more than one blocker."},
        {"metric": "geo_repair_rows", "value": str(len(geo_rows)), "notes": "Unresolved-region rows requiring geography repair."},
        {"metric": "exclusion_delta_rows", "value": str(len(exclusion_delta)), "notes": "New P0 source_file + capture_id suggestions not already in current exclusion table."},
    ]
    for severity, count in by_severity.most_common():
        summary_rows.append({"metric": f"severity:{severity}", "value": str(count), "notes": "Promotion blocker severity."})
    for blocker_type, count in by_type.most_common():
        summary_rows.append({"metric": f"blocker:{blocker_type}", "value": str(count), "notes": "Promotion blocker type."})
    for source_name, count in by_geo_source.most_common(20):
        summary_rows.append({"metric": f"geo_source:{source_name[:80]}", "value": str(count), "notes": "Top unresolved-region source names."})

    blockers.sort(key=lambda row: (row["severity"], row["blocker_type"], row["source_file"], row["capture_id"]))
    geo_rows.sort(key=lambda row: (row["source_name"], row["year"], row["title"]))
    exclusion_delta.sort(key=lambda row: (row["source_file"], row["capture_id"]))
    return blockers, geo_rows, exclusion_delta, summary_rows


def write_report(
    blockers: list[dict[str, str]],
    geo_rows: list[dict[str, str]],
    exclusion_delta: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> None:
    by_type = Counter(row["blocker_type"] for row in blockers)
    by_severity = Counter(row["severity"] for row in blockers)
    by_geo_source = Counter(row["source_name"] for row in geo_rows)
    lines = [
        "# Prefreeze Candidate Promotion Blockers v1",
        "",
        "Scope: non-mutating promotion blocker audit over the pre-freeze candidate payload. The script does not edit capture records, official payloads, frontend files, rights states, or image files.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows[:4]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## By Severity", ""])
    for severity, count in by_severity.most_common():
        lines.append(f"- {severity}: {count}")
    lines.extend(["", "## By Blocker Type", ""])
    for blocker_type, count in by_type.most_common():
        lines.append(f"- {blocker_type}: {count}")
    lines.extend(["", "## Top Unresolved Geography Sources", ""])
    for source_name, count in by_geo_source.most_common(15):
        lines.append(f"- {source_name}: {count}")
    lines.extend(["", "## Exclusion Delta", ""])
    if exclusion_delta:
        lines.append(
            f"- {len(exclusion_delta)} source_file + capture_id rows are proposed as a future P0 exclusion delta."
        )
        lines.append("- This delta is not automatically merged into `prefreeze_public_rebuild_exclusion_v1.csv`.")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Cleaning Order",
            "",
            "1. Apply or review duplicate exact image URL deltas first; they are the smallest high-confidence loss.",
            "2. Repair unresolved geography before using region coverage as a promotion metric.",
            "3. Reclassify event/photo/context-image rows manually; they are not included in the automatic exclusion delta because false positives can include designed affiches/posters.",
            "4. Review IMG00/IMG04 source-visible gaps; do not upgrade rights states without source evidence.",
            "",
            "## Safety",
            "",
            "- No image files were downloaded.",
            "- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, platform, or source-priority signals.",
            "- Candidate exclusion rows are recommendations only until a future gate merge is explicitly run.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    blockers, geo_rows, exclusion_delta, summary_rows = build_rows()
    write_csv(BLOCKERS, blockers, BLOCKER_FIELDS)
    write_csv(GEO_REPAIR, geo_rows, GEO_FIELDS)
    write_csv(EXCLUSION_DELTA, exclusion_delta, EXCLUSION_FIELDS)
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(blockers, geo_rows, exclusion_delta, summary_rows)
    print(f"promotion_blocker_rows={len(blockers)}")
    print(f"geo_repair_rows={len(geo_rows)}")
    print(f"exclusion_delta_rows={len(exclusion_delta)}")
    print(f"wrote {BLOCKERS.relative_to(ROOT)}")
    print(f"wrote {GEO_REPAIR.relative_to(ROOT)}")
    print(f"wrote {EXCLUSION_DELTA.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
