#!/usr/bin/env python3
"""Build a pre-freeze data cleaning audit across captures and public surfaces.

This pass is intentionally non-mutating. It consolidates existing release,
temporal, recent-quality, region, and capture-record signals into a practical
cleaning queue before any large rebuild or final capture push.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"

SUMMARY = DATA / "prefreeze_data_cleaning_summary_v1.csv"
QUEUE = DATA / "prefreeze_data_cleaning_priority_queue_v1.csv"
CONCENTRATION = DATA / "prefreeze_source_authority_concentration_v1.csv"
REGION_PERIOD = DATA / "prefreeze_region_period_gap_matrix_v1.csv"
REPORT = DOCS / "PREFREEZE_DATA_CLEANING_AUDIT_v1.md"

SUMMARY_FIELDS = ["area", "metric", "value", "severity", "recommendation"]
QUEUE_FIELDS = [
    "priority",
    "action_type",
    "risk_flags",
    "item_type",
    "item_id",
    "source_file",
    "year",
    "region",
    "image_state",
    "title",
    "source_name",
    "source_url",
    "recommendation",
]
CONCENTRATION_FIELDS = [
    "concentration_type",
    "key",
    "record_count",
    "img03_count",
    "img04_count",
    "post_2010_stamp_or_event_count",
    "sample_titles",
    "recommendation",
]
REGION_PERIOD_FIELDS = [
    "region_group",
    "period_band",
    "surface_count",
    "main_sheet_count",
    "source_visible_count",
    "verified_open_count",
    "img04_count",
    "quality_main_count",
    "status",
]

STAMP_TERMS = re.compile(
    r"\b(postage|postal|stamp|stamps|philatel|first\s+day\s+cover|souvenir\s+sheet|commemorative\s+issue)\b",
    re.IGNORECASE,
)
EVENT_MEMORY_TERMS = re.compile(
    r"\b(poster\s+session|conference|symposium|seminar|workshop|ceremony|"
    r"opening\s+(ceremony|reception|event)|exhibition\s+opening|"
    r"(book|product|campaign|event)\s+launch|launch\s+event|"
    r"group\s+photo|photo\s+of|memorial|remembrance|tribute|commemorat|"
    r"anniversary|jubilee|demonstration|rally)\b",
    re.IGNORECASE,
)
CONTEXT_IMAGE_TERMS = re.compile(
    r"\b(source\s+profile|source\s+page|hero\s+image|collection\s+image|poster\s+cutout|"
    r"posters\s+in|row\s+of\s+posters|department\s+store|last\s+address|schiftzug|schriftzug)\b",
    re.IGNORECASE,
)
WEAK_PLATFORM_TERMS = re.compile(r"\b(flickr|instagram|facebook|own\s+work|self-published|self-photographed)\b", re.IGNORECASE)
OPEN_RIGHTS_TERMS = re.compile(r"\b(public\s+domain|cc0|cc[- ]by|cc[- ]by[- ]sa|creative\s+commons|pd[- ]|open[- ]license|license)\b", re.IGNORECASE)


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
        writer.writerows(rows)


def pct(numerator: int | float, denominator: int | float) -> str:
    if denominator <= 0:
        return "0.00"
    return f"{(float(numerator) / float(denominator)) * 100:.2f}"


def capture_files() -> list[Path]:
    return sorted(path for path in DATA.glob("capture_batch_*_records.csv") if "cell_assignments" not in path.name)


def capture_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in capture_files():
        for row in read_csv(path):
            row = dict(row)
            row["_source_file"] = path.name
            rows.append(row)
    return rows


def safe_year(value: object) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        year = int(float(text))
    except ValueError:
        return None
    if 1830 <= year <= 2026:
        return year
    return None


def row_year(row: dict[str, str]) -> int | None:
    return safe_year(row.get("date_end")) or safe_year(row.get("date_start"))


def row_blob(row: dict[str, str]) -> str:
    fields = [
        "source_name",
        "source_title",
        "source_creator",
        "source_object_type",
        "source_medium",
        "source_collection",
        "source_description",
        "source_notes",
        "source_subjects",
        "rights_basis",
        "source_rights_text",
    ]
    return " ".join(clean(row.get(field)) for field in fields)


def norm_url(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    parsed = urlparse(value)
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"


def domain(value: str) -> str:
    parsed = urlparse(clean(value))
    return parsed.netloc.lower().replace("www.", "")


def work_key(row: dict[str, str]) -> str:
    title = clean(row.get("source_title")).lower()
    title = re.sub(r"\.(jpg|jpeg|png|tif|tiff|webp|svg)$", "", title)
    title = re.sub(r"\([^)]*(cropped|crop|file|version|v[0-9]+|black and white|color|colour)[^)]*\)", " ", title)
    title = re.sub(r"\b(cropped|crop|file|version|black and white|black white|b w|bw|colour|color|monochrome)\b", " ", title)
    title = re.sub(r"\b(v|version)\s*[0-9]+\b", " ", title)
    title = re.sub(r"[^a-z0-9]+", " ", title).strip()
    return "|".join([clean(row.get("source_place_text")).lower(), str(row_year(row) or ""), title])


def image_state(row: dict[str, str]) -> str:
    return clean(row.get("image_presence_code")) or "IMG00"


def surface_image_state(surface: dict) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def surface_region(surface: dict) -> str:
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    for folder in folders:
        if isinstance(folder, dict) and folder.get("type") == "region":
            return clean(folder.get("title")) or "Unresolved region"
    return "Unresolved region"


def period_band(year: int | None) -> str:
    if year is None:
        return "undated_or_unparsed"
    if year <= 1930:
        return "pre_1930"
    if year <= 1970:
        return "1930_1970"
    if year <= 2000:
        return "1970_2000"
    if year <= 2026:
        return "2000_2026"
    return "post_2026_or_error"


def surface_year(surface: dict) -> int | None:
    return safe_year(surface.get("dateEnd")) or safe_year(surface.get("dateStart"))


def release_metrics() -> dict[str, str]:
    return {row["metric"]: row["value"] for row in read_csv(DATA / "release_snapshot_v1.csv")}


def source_coverage_metrics() -> dict[str, str]:
    return {row["metric"]: row["value"] for row in read_csv(DATA / "source_coverage_rate_v2.csv")}


def append_queue(
    rows: list[dict[str, object]],
    *,
    priority: str,
    action_type: str,
    flags: list[str],
    item_type: str,
    item_id: str,
    source_file: str,
    year: str,
    region: str,
    image: str,
    title: str,
    source_name: str,
    source_url: str,
    recommendation: str,
) -> None:
    rows.append(
        {
            "priority": priority,
            "action_type": action_type,
            "risk_flags": "; ".join(flags),
            "item_type": item_type,
            "item_id": item_id,
            "source_file": source_file,
            "year": year,
            "region": region,
            "image_state": image,
            "title": title[:260],
            "source_name": source_name[:260],
            "source_url": source_url,
            "recommendation": recommendation,
        }
    )


def build_capture_queue(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    queue: list[dict[str, object]] = []
    by_url: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    by_work: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        url = norm_url(row.get("source_record_url", ""))
        if url:
            by_url[url].append(row)
        key = work_key(row)
        if key and len(key) > 3:
            by_work[key].append(row)

    duplicate_ids: set[tuple[str, str]] = set()
    for group in list(by_url.values()) + list(by_work.values()):
        if len(group) < 2:
            continue
        for row in group[1:]:
            duplicate_ids.add((row.get("_source_file", ""), row.get("capture_id", "")))

    domain_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    domain_risk_counts: Counter[str] = Counter()
    source_risk_counts: Counter[str] = Counter()
    domain_titles: defaultdict[str, list[str]] = defaultdict(list)
    source_titles: defaultdict[str, list[str]] = defaultdict(list)

    for row in rows:
        blob = row_blob(row)
        year = row_year(row)
        state = image_state(row)
        source_url = clean(row.get("source_record_url"))
        source_domain = domain(source_url)
        source_name = clean(row.get("source_name"))
        title = clean(row.get("source_title"))
        source_file = clean(row.get("_source_file"))
        item_id = clean(row.get("capture_id")) or clean(row.get("source_identifier"))
        region = clean(row.get("source_place_text"))
        flags: list[str] = []

        if source_domain:
            domain_counts[source_domain] += 1
            if len(domain_titles[source_domain]) < 5:
                domain_titles[source_domain].append(title)
        if source_name:
            source_counts[source_name] += 1
            if len(source_titles[source_name]) < 5:
                source_titles[source_name].append(title)

        if year and year >= 2010 and STAMP_TERMS.search(blob):
            flags.append("post_2010_stamp_or_philatelic")
        if EVENT_MEMORY_TERMS.search(blob):
            flags.append("event_photo_memory_or_commemoration")
        if CONTEXT_IMAGE_TERMS.search(blob):
            flags.append("context_image_or_environmental_poster")
        if WEAK_PLATFORM_TERMS.search(blob):
            flags.append("weak_platform_or_self_published")
        if year in {2025, 2026}:
            flags.append("recent_year_manual_review")
        if state == "IMG04":
            flags.append("img04_text_or_no_visual_review")
        if state == "IMG03" and not OPEN_RIGHTS_TERMS.search(" ".join([row.get("rights_basis", ""), row.get("source_rights_text", ""), row.get("rights_uri", "")])):
            flags.append("img03_rights_basis_weak_text")
        if region.lower() in {"", "_infer", "unresolved region", "final gap review"}:
            flags.append("unresolved_or_inferred_region")
        if (source_file, row.get("capture_id", "")) in duplicate_ids:
            flags.append("duplicate_source_or_work_variant")

        risk_for_concentration = bool({"post_2010_stamp_or_philatelic", "event_photo_memory_or_commemoration", "context_image_or_environmental_poster"} & set(flags))
        if risk_for_concentration:
            if source_domain:
                domain_risk_counts[source_domain] += 1
            if source_name:
                source_risk_counts[source_name] += 1

        if not flags:
            continue
        if "post_2010_stamp_or_philatelic" in flags or "event_photo_memory_or_commemoration" in flags or "context_image_or_environmental_poster" in flags:
            priority = "P0"
            action = "card_or_appendix_reclass_review"
            recommendation = "Do not keep as primary design object unless an item-level design-work rationale survives manual review."
        elif "duplicate_source_or_work_variant" in flags:
            priority = "P1"
            action = "deduplicate_or_merge_review"
            recommendation = "Collapse repeated source/object variants before object-level release metrics."
        elif "recent_year_manual_review" in flags or "img03_rights_basis_weak_text" in flags:
            priority = "P1"
            action = "manual_rights_or_date_review"
            recommendation = "Verify object year and item-level rights before retaining release metrics."
        else:
            priority = "P2"
            action = "metadata_cleanup_review"
            recommendation = "Clean region/image/text metadata during the pre-freeze pass."

        append_queue(
            queue,
            priority=priority,
            action_type=action,
            flags=flags,
            item_type="capture_record",
            item_id=item_id,
            source_file=source_file,
            year=str(year or ""),
            region=region,
            image=state,
            title=title,
            source_name=source_name,
            source_url=source_url,
            recommendation=recommendation,
        )

    concentration_rows: list[dict[str, object]] = []
    for typ, counts, risk_counts, samples in [
        ("source_domain", domain_counts, domain_risk_counts, domain_titles),
        ("source_name", source_counts, source_risk_counts, source_titles),
    ]:
        for key, count in counts.most_common():
            if count < 25 and risk_counts[key] < 10:
                continue
            concentration_rows.append(
                {
                    "concentration_type": typ,
                    "key": key,
                    "record_count": count,
                    "img03_count": sum(1 for row in rows if (domain(row.get("source_record_url", "")) if typ == "source_domain" else clean(row.get("source_name"))) == key and image_state(row) == "IMG03"),
                    "img04_count": sum(1 for row in rows if (domain(row.get("source_record_url", "")) if typ == "source_domain" else clean(row.get("source_name"))) == key and image_state(row) == "IMG04"),
                    "post_2010_stamp_or_event_count": risk_counts[key],
                    "sample_titles": " | ".join(samples[key][:5]),
                    "recommendation": "Cap or sample this source family before further capture; audit risky rows before surface rebuild.",
                }
            )
    return queue, concentration_rows


def add_existing_review_queues(queue: list[dict[str, object]]) -> None:
    for row in read_csv(DATA / "temporal_recent_anomaly_review_v1.csv")[:1200]:
        append_queue(
            queue,
            priority="P0" if "access_year" in row.get("review_reason", "") or "source_page" in row.get("review_reason", "") else "P1",
            action_type="date_or_span_reclass_review",
            flags=[row.get("review_reason", "")],
            item_type="temporal_anomaly",
            item_id=row.get("capture_id", ""),
            source_file=row.get("capture_file", ""),
            year=row.get("recent_year", ""),
            region=row.get("source_place_text", ""),
            image=row.get("image_presence_code", ""),
            title=row.get("source_title", ""),
            source_name=row.get("source_name", ""),
            source_url=row.get("source_record_url", ""),
            recommendation="Remove access-year/span/profile rows from object-year coverage until item-level year is verified.",
        )
    for row in read_csv(DATA / "recent_stamp_event_reclassification_queue_v1.csv")[:1800]:
        append_queue(
            queue,
            priority="P0",
            action_type="recent_stamp_event_reclassification",
            flags=[row.get("review_flags", "")],
            item_type="recent_quality_queue",
            item_id=row.get("capture_id", ""),
            source_file=row.get("capture_file", ""),
            year=row.get("object_year", ""),
            region=row.get("source_place_text", ""),
            image=row.get("image_presence_code", ""),
            title=row.get("source_title", ""),
            source_name=row.get("source_name", ""),
            source_url=row.get("source_record_url", ""),
            recommendation=row.get("classification_note", "Review for card/support status before final metrics."),
        )


def build_region_period_matrix(surfaces: list[dict], quality_main_ids: set[str]) -> list[dict[str, object]]:
    stats: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for surface in surfaces:
        region = surface_region(surface)
        period = period_band(surface_year(surface))
        state = surface_image_state(surface)
        key = (region, period)
        stats[key]["surface_count"] += 1
        if clean(surface.get("publicationRole")) == "main_sheet":
            stats[key]["main_sheet_count"] += 1
        if state in {"IMG01", "IMG02", "IMG03"}:
            stats[key]["source_visible_count"] += 1
        if state == "IMG03" and (surface.get("reviewGates") or {}).get("rightsReviewed") is True:
            stats[key]["verified_open_count"] += 1
        if state == "IMG04":
            stats[key]["img04_count"] += 1
        if clean(surface.get("surfaceId")) in quality_main_ids:
            stats[key]["quality_main_count"] += 1

    rows: list[dict[str, object]] = []
    for (region, period), counter in sorted(stats.items(), key=lambda item: (item[0][0], item[0][1])):
        surface_count = counter["surface_count"]
        quality_share = counter["quality_main_count"] / surface_count if surface_count else 0
        visible_share = counter["source_visible_count"] / surface_count if surface_count else 0
        if region == "Unresolved region" or quality_share < 0.05 or visible_share < 0.9:
            status = "review"
        elif surface_count < 20:
            status = "thin"
        else:
            status = "ok"
        rows.append(
            {
                "region_group": region,
                "period_band": period,
                "surface_count": surface_count,
                "main_sheet_count": counter["main_sheet_count"],
                "source_visible_count": counter["source_visible_count"],
                "verified_open_count": counter["verified_open_count"],
                "img04_count": counter["img04_count"],
                "quality_main_count": counter["quality_main_count"],
                "status": status,
            }
        )
    return rows


def main() -> None:
    captures = capture_rows()
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8")) if PAYLOAD.exists() else {"surfaces": []}
    surfaces = payload.get("surfaces", [])
    release = release_metrics()
    coverage = source_coverage_metrics()
    quality_main_ids = {
        row.get("surface_id", "")
        for row in read_csv(DATA / "main_sheet_research_value_audit_v1.csv")
        if row.get("recommended_action") in {"keep_main", "keep_main_add_editorial_text"} and int(row.get("research_value_score") or 0) >= 60
    }

    queue, concentration_rows = build_capture_queue(captures)
    add_existing_review_queues(queue)
    region_period_rows = build_region_period_matrix(surfaces, quality_main_ids)

    # De-duplicate queue entries by item/action/flags while preserving priority.
    seen: set[tuple[str, str, str, str]] = set()
    deduped_queue: list[dict[str, object]] = []
    priority_rank = {"P0": 0, "P1": 1, "P2": 2}
    for row in sorted(queue, key=lambda item: (priority_rank.get(str(item["priority"]), 9), str(item["action_type"]), str(item["item_id"]))):
        key = (str(row["item_type"]), str(row["item_id"]), str(row["source_file"]), str(row["action_type"]))
        if key in seen:
            continue
        seen.add(key)
        deduped_queue.append(row)

    p_counts = Counter(str(row["priority"]) for row in deduped_queue)
    action_counts = Counter(str(row["action_type"]) for row in deduped_queue)
    capture_state = Counter(image_state(row) for row in captures)
    capture_years = Counter(row_year(row) for row in captures if row_year(row) is not None)
    unresolved_region_count = sum(1 for row in captures if clean(row.get("source_place_text")).lower() in {"", "_infer", "unresolved region", "final gap review"})
    recent_anomaly_count = len(read_csv(DATA / "temporal_recent_anomaly_review_v1.csv"))
    recent_reclass_count = len(read_csv(DATA / "recent_stamp_event_reclassification_queue_v1.csv"))

    summary_rows = [
        {"area": "release", "metric": "public_surfaces", "value": release.get("public_surfaces", "0"), "severity": "info", "recommendation": "Snapshot only; no frontend rebuild was run."},
        {"area": "release", "metric": "archive_active_public_sources", "value": release.get("archive_active_public_sources", "0"), "severity": "fail", "recommendation": "Treat source count as capacity context, not the defining quality metric."},
        {"area": "release", "metric": "object_source_visible_rate", "value": release.get("object_source_visible_rate", "0"), "severity": "near_gate", "recommendation": "Raise toward 99% through targeted source-visible repair, not broad capture."},
        {"area": "release", "metric": "object_verified_open_rate", "value": release.get("object_verified_open_rate", "0"), "severity": "fail", "recommendation": "Needs item-level rights repair to approach 95%."},
        {"area": "release", "metric": "object_img04_rate", "value": release.get("object_img04_rate", "0"), "severity": "pass", "recommendation": "Keep IMG04 low, but audit true text-only status."},
        {"area": "coverage", "metric": "strict_distribution_adjusted_source_coverage_rate", "value": coverage.get("strict_distribution_adjusted_source_coverage_rate", "0"), "severity": "critical", "recommendation": "Main distribution blocker; prioritize region normalization and low-coverage quality capture."},
        {"area": "coverage", "metric": "research_quality_adjusted_source_coverage_rate_v2", "value": coverage.get("research_quality_adjusted_source_coverage_rate_v2", "0"), "severity": "critical", "recommendation": "Shows main-sheet/text/relation quality, not raw source volume, is the release bottleneck."},
        {"area": "capture_pool", "metric": "capture_records_scanned", "value": str(len(captures)), "severity": "info", "recommendation": "All capture_batch_*_records.csv rows scanned."},
        {"area": "capture_pool", "metric": "capture_img03_count", "value": str(capture_state.get("IMG03", 0)), "severity": "info", "recommendation": "IMG03 count before final clean/rebuild."},
        {"area": "capture_pool", "metric": "capture_img04_count", "value": str(capture_state.get("IMG04", 0)), "severity": "review", "recommendation": "Confirm IMG04 rows are true text/source context, not parser misses."},
        {"area": "capture_pool", "metric": "unresolved_or_inferred_region_records", "value": str(unresolved_region_count), "severity": "review", "recommendation": "Apply region normalization decisions before final surface rebuild."},
        {"area": "temporal", "metric": "temporal_recent_anomaly_review_rows", "value": str(recent_anomaly_count), "severity": "critical", "recommendation": "Remove access-year/span/profile rows from object-year metrics."},
        {"area": "recent_quality", "metric": "recent_stamp_event_reclassification_rows", "value": str(recent_reclass_count), "severity": "critical", "recommendation": "Downgrade post-2010 stamps/event memory material to card/support unless manually justified."},
        {"area": "queue", "metric": "P0_cleaning_queue_rows", "value": str(p_counts.get("P0", 0)), "severity": "critical", "recommendation": "Run before any new broad capture or rebuild."},
        {"area": "queue", "metric": "P1_cleaning_queue_rows", "value": str(p_counts.get("P1", 0)), "severity": "high", "recommendation": "Run after P0, especially rights/date/duplicate review."},
        {"area": "queue", "metric": "P2_cleaning_queue_rows", "value": str(p_counts.get("P2", 0)), "severity": "medium", "recommendation": "Metadata cleanup and triage."},
    ]
    for action, count in action_counts.most_common():
        summary_rows.append({"area": "queue_action", "metric": action, "value": str(count), "severity": "info", "recommendation": "See priority queue CSV."})
    for year, count in capture_years.most_common(12):
        summary_rows.append({"area": "capture_year_top", "metric": str(year), "value": str(count), "severity": "diagnostic", "recommendation": "Top capture-record years before clean/rebuild."})

    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(QUEUE, deduped_queue, QUEUE_FIELDS)
    write_csv(CONCENTRATION, concentration_rows, CONCENTRATION_FIELDS)
    write_csv(REGION_PERIOD, region_period_rows, REGION_PERIOD_FIELDS)

    p0_examples = [row for row in deduped_queue if row["priority"] == "P0"][:12]
    lines = [
        "# Pre-freeze Data Cleaning Audit v1",
        "",
        "Scope: consolidated, non-mutating audit across capture records, generated public surfaces, release snapshot, temporal anomaly review, recent-object quality review, and source coverage diagnostics.",
        "",
        "## Headline",
        "",
        f"- Capture records scanned: {len(captures)}",
        f"- Public surfaces: {release.get('public_surfaces', '0')}",
        f"- Active public sources: {release.get('archive_active_public_sources', '0')}",
        f"- Object source-visible: {release.get('object_source_visible_rate', '0')}%",
        f"- Object verified-open: {release.get('object_verified_open_rate', '0')}%",
        f"- Object IMG04: {release.get('object_img04_rate', '0')}%",
        f"- Strict distribution adjusted coverage: {coverage.get('strict_distribution_adjusted_source_coverage_rate', '0')}%",
        f"- Research-quality adjusted source coverage: {coverage.get('research_quality_adjusted_source_coverage_rate_v2', '0')}%",
        "",
        "## Cleaning Queue",
        "",
        f"- P0: {p_counts.get('P0', 0)}",
        f"- P1: {p_counts.get('P1', 0)}",
        f"- P2: {p_counts.get('P2', 0)}",
        "",
        "P0 means the row can materially distort release metrics if kept as a primary object: access-year/span records, post-2010 stamp drift, event/memory material, context images, or source-page/profile rows.",
        "",
        "## Action Counts",
        "",
    ]
    for action, count in action_counts.most_common():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## P0 Examples", ""])
    for row in p0_examples:
        lines.append(f"- {row['item_id']} · {row['year']} · {row['region']} · {row['title']} · {row['risk_flags']}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Source count is now a capacity indicator, not the defining release-quality metric.",
            "- The largest blockers are distribution, research-quality main-sheet structure, rights verification, and recent-object contamination.",
            "- Broad Commons search should stay paused except for manually verified collection gaps; institution APIs and known collections are better next capture targets.",
            "- A larger cleaning pass is needed before any full surface rebuild, otherwise noisy rows will be promoted into main sheets and distort release gates.",
            "",
            "## Output Files",
            "",
            f"- `{SUMMARY.relative_to(ROOT)}`",
            f"- `{QUEUE.relative_to(ROOT)}`",
            f"- `{CONCENTRATION.relative_to(ROOT)}`",
            f"- `{REGION_PERIOD.relative_to(ROOT)}`",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"captures={len(captures)}")
    print(f"p0={p_counts.get('P0', 0)} p1={p_counts.get('P1', 0)} p2={p_counts.get('P2', 0)}")
    print(f"recent_anomaly={recent_anomaly_count} recent_reclass={recent_reclass_count}")
    print(f"wrote {SUMMARY}")
    print(f"wrote {QUEUE}")
    print(f"wrote {CONCENTRATION}")
    print(f"wrote {REGION_PERIOD}")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
