#!/usr/bin/env python3
"""Audit candidate main-sheet strictness for packet/text archival planning.

This is a non-mutating review queue. It does not demote surfaces, rebuild
payloads, download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

OUT_REVIEW = DATA / "prefreeze_main_anchor_strictness_review_v1.csv"
OUT_CLUSTERS = DATA / "prefreeze_main_anchor_cluster_review_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_anchor_strictness_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_MAIN_ANCHOR_STRICTNESS_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
REVIEW_FIELDS = [
    "surface_id",
    "capture_id",
    "year",
    "period",
    "region",
    "theme",
    "medium",
    "image_state",
    "source_name",
    "title",
    "research_packet_anchor_marker",
    "main_anchor_lane",
    "main_anchor_reason",
    "source_reading_text_length",
    "reading_text_length",
    "compound_children",
    "dossier_subsheet_pages",
    "dossier_text_pages",
    "cluster_key",
    "cluster_size",
]
CLUSTER_FIELDS = [
    "cluster_key",
    "cluster_size",
    "region",
    "theme",
    "source_name",
    "decade",
    "dominant_lane",
    "sample_titles",
]

PERIODS = [
    ("pre_1850", None, 1849),
    ("1850_1899", 1850, 1899),
    ("1900_1913", 1900, 1913),
    ("1914_1945", 1914, 1945),
    ("1946_1969", 1946, 1969),
    ("1970_1989", 1970, 1989),
    ("1990_1999", 1990, 1999),
    ("2000_2009", 2000, 2009),
    ("2010_2019", 2010, 2019),
    ("2020_2026", 2020, 2026),
    ("undated", None, None),
]

RISK_TERMS = (
    "stamp",
    "postage",
    "commemorative",
    "coin",
    "banknote",
    "event photo",
    "session",
    "conference",
    "inauguration",
    "anniversary",
    "ceremony",
    "portrait",
    "profile",
    "street view",
    "tourist",
    "wildlife",
    "natural history",
    "geology",
    "geological",
    "limestone",
    "ordovician",
    "bivalve",
    "boring",
    "borings",
    "fossil",
    "mineral",
    "specimen",
)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def as_int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_payload() -> dict:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def year_of(surface: dict) -> int | None:
    for key in ("dateEnd", "dateStart"):
        value = surface.get(key)
        if isinstance(value, int):
            return value
        text = clean(value)
        if text.isdigit():
            return int(text)
    return None


def decade_of(year: int | None) -> str:
    if year is None:
        return "undated"
    return f"{year // 10 * 10}s"


def period_of(year: int | None) -> str:
    if year is None:
        return "undated"
    for label, start, end in PERIODS:
        if label == "undated":
            continue
        if (start is None or year >= start) and (end is None or year <= end):
            return label
    return "undated"


def folder_title(surface: dict, folder_type: str) -> str:
    for folder in surface.get("folders", []):
        if isinstance(folder, dict) and folder.get("type") == folder_type:
            return clean(folder.get("title"))
    return ""


def image_state(surface: dict) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def page_counts(dossier: dict | None) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not dossier:
        return counts
    for page in dossier.get("pageSequence", []):
        counts[clean(page.get("pageType"))] += 1
    return counts


def dossier_by_anchor(payload: dict) -> dict[str, dict]:
    return {
        clean(dossier.get("anchorSurfaceId")): dossier
        for dossier in payload.get("researchDossiers", [])
        if clean(dossier.get("anchorSurfaceId"))
    }


def text_contains_risk(surface: dict) -> bool:
    text = " ".join(
        clean(surface.get(key))
        for key in ("title", "sourceName", "medium", "objectType", "sourceDescription", "sourceSubjects")
    ).casefold()
    for term in RISK_TERMS:
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            return True
    return False


def cluster_key(surface: dict) -> str:
    year = year_of(surface)
    return "|".join(
        [
            folder_title(surface, "region") or "Unresolved region",
            folder_title(surface, "theme") or "Unresolved theme",
            clean(surface.get("sourceName")) or "Unresolved source",
            decade_of(year),
        ]
    )


def anchor_marker(lane: str) -> str:
    if lane == "keep_main_anchor_candidate":
        return "strong_soft_anchor"
    if lane == "main_anchor_manual_review":
        return "soft_anchor_review"
    if lane == "needs_editorial_text":
        return "anchor_if_editorial_text_added"
    if lane == "needs_packet_subsheet_assignment":
        return "packet_anchor_or_member_review"
    return "support_or_card_review"


def classify_main(surface: dict, dossier: dict | None, cluster_size: int) -> tuple[str, str]:
    source_len = as_int(surface.get("sourceReadingTextLength"))
    read_len = as_int(surface.get("readingTextLength")) or len(clean(surface.get("descriptionSummary")))
    children = len(surface.get("compoundChildren") or [])
    pcounts = page_counts(dossier)
    subsheets = pcounts.get("subsheet", 0)
    text_pages = pcounts.get("text_page", 0)
    img = image_state(surface)
    region = folder_title(surface, "region")
    source_name = clean(surface.get("sourceName")).casefold()
    risky = text_contains_risk(surface)

    if not region or region.casefold().startswith("unresolved") or "transnational" in region.casefold():
        return "support_or_card_review", "unstable region binding requires manual main review"
    if risky and source_len < 160:
        return "support_or_card_review", "risk term plus thin source text"
    if risky:
        return "support_or_card_review", "risk term requires manual main review"
    if source_name.startswith(("wikimedia commons", "colnect")) and not children:
        if source_len < 250:
            return "support_or_card_review", "file-source style main with thin source text"
        return "main_anchor_manual_review", "Commons/Colnect main requires source-family sample review"
    if children > 2 or subsheets > 1:
        return "keep_main_anchor_candidate", "has explicit child/subsheet relation"
    if source_len >= 250 and read_len >= 900 and img in {"IMG01", "IMG02", "IMG03"}:
        return "keep_main_anchor_candidate", "enough source/editorial text for standalone anchor"
    if cluster_size >= 3 and source_len < 250:
        return "needs_packet_subsheet_assignment", "clustered main with insufficient source depth"
    if source_len < 80 or read_len < 600 or text_pages <= 1:
        return "needs_editorial_text", "main lacks enough text support"
    return "main_anchor_manual_review", "moderate signal; needs editorial judgement"


def main() -> None:
    payload = load_payload()
    surfaces = payload.get("surfaces", [])
    dossiers = dossier_by_anchor(payload)
    main_surfaces = [surface for surface in surfaces if surface.get("publicationRole") == "main_sheet"]

    cluster_counts = Counter(cluster_key(surface) for surface in main_surfaces)
    rows: list[dict[str, object]] = []
    by_cluster: dict[str, list[dict[str, object]]] = defaultdict(list)

    for surface in main_surfaces:
        sid = clean(surface.get("surfaceId"))
        dossier = dossiers.get(sid)
        pcounts = page_counts(dossier)
        year = year_of(surface)
        ckey = cluster_key(surface)
        lane, reason = classify_main(surface, dossier, cluster_counts[ckey])
        row = {
            "surface_id": sid,
            "capture_id": clean(surface.get("sourceRecordId")),
            "year": year or "",
            "period": period_of(year),
            "region": folder_title(surface, "region"),
            "theme": folder_title(surface, "theme"),
            "medium": clean(surface.get("medium")),
            "image_state": image_state(surface),
            "source_name": clean(surface.get("sourceName"))[:220],
            "title": clean(surface.get("title"))[:240],
            "research_packet_anchor_marker": anchor_marker(lane),
            "main_anchor_lane": lane,
            "main_anchor_reason": reason,
            "source_reading_text_length": as_int(surface.get("sourceReadingTextLength")),
            "reading_text_length": as_int(surface.get("readingTextLength")),
            "compound_children": len(surface.get("compoundChildren") or []),
            "dossier_subsheet_pages": pcounts.get("subsheet", 0),
            "dossier_text_pages": pcounts.get("text_page", 0),
            "cluster_key": ckey,
            "cluster_size": cluster_counts[ckey],
        }
        rows.append(row)
        by_cluster[ckey].append(row)

    rows.sort(key=lambda row: (row["main_anchor_lane"], -int(row["cluster_size"]), row["period"], row["source_name"], row["title"]))

    cluster_rows: list[dict[str, object]] = []
    for ckey, values in by_cluster.items():
        if len(values) < 3:
            continue
        lane_counts = Counter(clean(row["main_anchor_lane"]) for row in values)
        region, theme, source_name, decade = ckey.split("|", 3)
        cluster_rows.append(
            {
                "cluster_key": ckey,
                "cluster_size": len(values),
                "region": region,
                "theme": theme,
                "source_name": source_name[:220],
                "decade": decade,
                "dominant_lane": lane_counts.most_common(1)[0][0],
                "sample_titles": " | ".join(clean(row["title"]) for row in values[:5])[:700],
            }
        )
    cluster_rows.sort(key=lambda row: (-int(row["cluster_size"]), row["dominant_lane"], row["cluster_key"]))

    lane_counts = Counter(clean(row["main_anchor_lane"]) for row in rows)
    period_lane_counts = Counter((clean(row["period"]), clean(row["main_anchor_lane"])) for row in rows)
    summary_rows: list[dict[str, object]] = [
        {"metric": "main_sheets_scanned", "value": len(rows), "notes": "Candidate main_sheet surfaces scanned."},
        {"metric": "cluster_review_rows", "value": len(cluster_rows), "notes": "Region/theme/source/decade main clusters with at least three records."},
    ]
    for lane, count in lane_counts.most_common():
        summary_rows.append({"metric": f"lane:{lane}", "value": count, "notes": "Main anchor review lane distribution."})
    for (period, lane), count in sorted(period_lane_counts.items()):
        summary_rows.append({"metric": f"period_lane:{period}:{lane}", "value": count, "notes": "Main anchor lane by period."})

    write_csv(OUT_REVIEW, rows, REVIEW_FIELDS)
    write_csv(OUT_CLUSTERS, cluster_rows, CLUSTER_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Prefreeze Main Anchor Strictness v1",
        "",
        "Scope: non-mutating review queue for stricter main/sub/text archival planning.",
        "",
        "This pass does not demote surfaces, rebuild the official payload, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows[:24]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `keep_main_anchor_candidate` is not a final approval; it marks records with enough text or explicit relations to sample first.",
            "- These lanes are soft archival markers, not release gates or automatic demotion instructions.",
            "- `needs_packet_subsheet_assignment` is the main归档 backlog: these records may be packet anchors or members, but need relation design before application.",
            "- `needs_editorial_text` means the surface can remain a main anchor if later editorial text justifies it.",
            "- `support_or_card_review` is a high-priority manual review lane for weak visual/context records; some may still become packet anchors after source review.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"main_sheets_scanned={len(rows)}")
    print(f"cluster_review_rows={len(cluster_rows)}")
    for lane, count in lane_counts.most_common():
        print(f"{lane}={count}")
    print(f"wrote {OUT_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_CLUSTERS.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
