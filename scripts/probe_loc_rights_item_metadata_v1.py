#!/usr/bin/env python3
"""Probe LOC item metadata for rights/image repair candidates.

The probe is source-only: it fetches loc.gov JSON metadata, extracts item-level
rights/advisory text and source-hosted image URL signals, and writes review
queues. It does not download images, save raw JSON, mutate records, rebuild
surfaces, or upgrade IMG01/IMG03.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


INPUT = DATA / "loc_rights_repair_preflight_v1.csv"
OUTPUT_ROWS = DATA / "loc_rights_item_probe_v1.csv"
OUTPUT_SUMMARY = DATA / "loc_rights_item_probe_summary_v1.csv"
OUTPUT_REPORT = DOCS / "LOC_RIGHTS_ITEM_PROBE_v1.md"

USER_AGENT = "ModernGDHistory/0.1 LOC-rights-item-probe source-only"
REQUEST_SLEEP_SECONDS = 1.1
MAX_ROWS = 50

ROW_FIELDS = [
    "surface_id",
    "source_record_id",
    "source_record_url",
    "item_json_url",
    "title",
    "repair_family",
    "weighted_gap_points",
    "local_image_state",
    "fetch_status",
    "http_status",
    "rights_signal",
    "rights_text_excerpt",
    "image_url_count",
    "first_image_url_excerpt",
    "recommendation",
    "automatic_upgrade_allowed",
    "notes",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

OPEN_RIGHTS_MARKERS = (
    "no known restrictions",
    "public domain",
    "no known copyright",
    "out of copyright",
    "rights status is in the public domain",
)

RESTRICTIVE_RIGHTS_MARKERS = (
    "may be restricted",
    "rights status not evaluated",
    "copyright",
    "permission",
    "restricted",
    "rights assessment is your responsibility",
)


def item_json_url(record_url: str, source_record_id: str) -> str:
    url = clean(record_url)
    if url:
        return url.rstrip("/") + "/?fo=json"
    if source_record_id:
        return f"https://www.loc.gov/pictures/item/{source_record_id}/?fo=json"
    return ""


def fetch_json(url: str) -> tuple[str, str, dict[str, Any] | None]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            status = str(getattr(response, "status", ""))
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
            return "ok", status, payload
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return "rate_limited", "429", None
        return "http_error", str(exc.code), None
    except Exception as exc:  # noqa: BLE001
        return f"error:{type(exc).__name__}", "", None


def walk(value: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.append((str(key), child))
            found.extend(walk(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(walk(child))
    return found


def stringify(value: Any) -> str:
    if isinstance(value, str):
        return clean(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return clean("; ".join(stringify(item) for item in value if stringify(item)), max_chars=1200)
    if isinstance(value, dict):
        preferred = []
        for key in ("title", "label", "text", "value", "name"):
            if key in value:
                preferred.append(stringify(value[key]))
        if preferred:
            return clean("; ".join(preferred), max_chars=1200)
        return clean(json.dumps(value, ensure_ascii=False, sort_keys=True), max_chars=1200)
    return ""


def excerpt(value: str, limit: int) -> str:
    text = clean(value)
    return text[: limit - 3].rstrip() + "..." if len(text) > limit else text


def rights_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key, value in walk(payload):
        low = key.lower()
        if "rights" in low or "restriction" in low:
            text = stringify(value)
            if text:
                chunks.append(text)
    return excerpt("; ".join(dict.fromkeys(chunks)), 1200)


def image_urls(payload: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for _key, value in walk(payload):
        if isinstance(value, str):
            text = clean(value)
            if not text:
                continue
            low = text.lower()
            if "notdigitized" in low or "not_digitized" in low:
                continue
            image_host = any(host in low for host in ("tile.loc.gov", "cdn.loc.gov", "/service/pnp/"))
            image_ext = any(ext in low for ext in (".jpg", ".jpeg", ".png", ".gif", ".tif", ".jp2"))
            if image_host and image_ext:
                urls.append(text)
    return list(dict.fromkeys(urls))


def rights_signal(text: str) -> str:
    low = text.lower()
    if any(marker in low for marker in RESTRICTIVE_RIGHTS_MARKERS):
        return "restrictive_or_unclear_rights_text"
    if any(marker in low for marker in OPEN_RIGHTS_MARKERS):
        return "item_level_open_rights_text"
    if text:
        return "item_rights_text_unclassified"
    return "no_item_rights_text"


def recommendation(fetch_status: str, signal: str, urls: list[str]) -> str:
    if fetch_status == "rate_limited":
        return "retry_later_rate_limited"
    if fetch_status != "ok":
        return "retry_item_probe"
    if signal == "item_level_open_rights_text" and urls:
        return "manual_img03_candidate_item_rights_visible"
    if urls:
        return "source_visible_img02_rebuild_candidate"
    return "keep_img04_or_text_until_visual_source_found"


def build_rows() -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    cached_ok = {
        row.get("surface_id", ""): row
        for row in read_csv(OUTPUT_ROWS)
        if row.get("fetch_status") == "ok"
    }
    for index, row in enumerate(read_csv(INPUT), start=1):
        if index > MAX_ROWS:
            break
        surface_id = row.get("surface_id", "")
        if surface_id in cached_ok:
            output.append(cached_ok[surface_id])
            continue
        json_url = item_json_url(row.get("source_record_url", ""), row.get("source_record_id", ""))
        if not json_url:
            status, http_status, payload = "error:missing_url", "", None
        else:
            status, http_status, payload = fetch_json(json_url)
        rights = rights_text(payload) if payload else ""
        signal = rights_signal(rights)
        urls = image_urls(payload) if payload else []
        output.append(
            {
                "surface_id": row.get("surface_id", ""),
                "source_record_id": row.get("source_record_id", ""),
                "source_record_url": row.get("source_record_url", ""),
                "item_json_url": json_url,
                "title": row.get("title", ""),
                "repair_family": row.get("repair_family", ""),
                "weighted_gap_points": row.get("weighted_gap_points", ""),
                "local_image_state": row.get("local_image_state", ""),
                "fetch_status": status,
                "http_status": http_status,
                "rights_signal": signal,
                "rights_text_excerpt": excerpt(rights, 520),
                "image_url_count": str(len(urls)),
                "first_image_url_excerpt": excerpt(urls[0] if urls else "", 320),
                "recommendation": recommendation(status, signal, urls),
                "automatic_upgrade_allowed": "false",
                "notes": "Source-only LOC item metadata probe; no images downloaded and no image-state mutation.",
            }
        )
        time.sleep(REQUEST_SLEEP_SECONDS)
    return output


def write_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    fetch_counts = Counter(row["fetch_status"] for row in rows)
    signal_counts = Counter(row["rights_signal"] for row in rows)
    recommendation_counts = Counter(row["recommendation"] for row in rows)
    rows_with_image = sum(1 for row in rows if int(row["image_url_count"] or "0") > 0)
    manual_candidate_points = sum(
        float(row.get("weighted_gap_points") or 0)
        for row in rows
        if row["recommendation"] == "manual_img03_candidate_item_rights_visible"
    )
    summary = [
        {"metric": "candidate_rows", "value": str(len(rows)), "notes": "Rows read from LOC P0 rights repair preflight."},
        {"metric": "rows_with_source_image_url", "value": str(rows_with_image), "notes": "Source-hosted LOC image URLs detected in JSON metadata; no image download."},
        {"metric": "manual_img03_candidate_weighted_gap_points", "value": f"{manual_candidate_points:.2f}", "notes": "Weighted points represented by manual candidates; no automatic upgrade."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "Probe is advisory only."},
    ]
    for key, value in fetch_counts.most_common():
        summary.append({"metric": f"fetch_status_{key}", "value": str(value), "notes": "LOC item JSON probe status."})
    for key, value in signal_counts.most_common():
        summary.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Item-level rights/advisory text signal."})
    for key, value in recommendation_counts.most_common():
        summary.append({"metric": f"recommendation_{key}", "value": str(value), "notes": "Review recommendation only; not an automatic state change."})
    write_csv(OUTPUT_SUMMARY, summary, SUMMARY_FIELDS)
    return summary


def write_report(rows: list[dict[str, str]], summary: list[dict[str, str]]) -> None:
    metrics = {row["metric"]: row["value"] for row in summary}
    lines = [
        "# LOC Rights Item Probe v1",
        "",
        "This source-only probe checks P0 Library of Congress repair candidates against loc.gov item JSON metadata. It does not download images, save raw JSON, mutate records, rebuild surfaces, or upgrade IMG01/IMG03.",
        "",
        "## Summary",
        "",
        f"- candidate rows probed: {metrics.get('candidate_rows', '0')}",
        f"- rows with source-hosted image URL: {metrics.get('rows_with_source_image_url', '0')}",
        f"- manual IMG03 candidate weighted gap points: {metrics.get('manual_img03_candidate_weighted_gap_points', '0.00')}",
        f"- automatic upgrades allowed: {metrics.get('automatic_upgrade_allowed_rows', '0')}",
        "",
        "## Recommendation Counts",
        "",
    ]
    for row in summary:
        if row["metric"].startswith("recommendation_"):
            lines.append(f"- {row['metric'].removeprefix('recommendation_')}: {row['value']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- `manual_img03_candidate_item_rights_visible` means LOC item metadata exposes both an image URL and open-rights text, but a human/rebuild pass must still decide whether to promote.",
            "- `source_visible_img02_rebuild_candidate` can improve source-visible coverage but is not verified-open.",
        "- `automatic_upgrade_allowed` is false for every row.",
        "- LOC HTTP 429 responses are kept as `retry_later_rate_limited` rather than blocking the run with long in-process backoff.",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_ROWS.relative_to(ROOT)}`",
            f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_ROWS, rows, ROW_FIELDS)
    summary = write_summary(rows)
    write_report(rows, summary)
    print(f"candidate_rows={len(rows)}")
    print(f"rows_with_source_image_url={sum(1 for row in rows if int(row['image_url_count'] or '0') > 0)}")
    print("automatic_upgrade_allowed_rows=0")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
