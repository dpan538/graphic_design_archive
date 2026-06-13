#!/usr/bin/env python3
"""Top off the authority-weighted Commons open metadata batch.

This is a narrow continuation script for the late long-run capture. It uses
only source-page metadata from Wikimedia Commons, stores source links and
source-hosted image URLs, and does not download image binaries, thumbnails,
screenshots, browser sessions, cookies, or raw API payloads.

The topoff plan is intentionally query-whitelisted. It exists because the
general authority queue becomes very sparse near the 5,000-record target while
some explicit object/country searches still produce clean open metadata.
"""

from __future__ import annotations

import os
import time
from collections import Counter

import run_commons_open_global_south_image_capture_2026_v1 as base
import run_commons_open_authority_weighted_expansion_2026_v1 as auth


TARGET_ROWS = int(os.environ.get("AUTHORITY_TOPOFF_TARGET_ROWS", str(auth.TARGET_ROWS)))
QUERY_LIMIT = int(os.environ.get("AUTHORITY_TOPOFF_QUERY_LIMIT", "50"))
MAX_PAGES_PER_QUERY = int(os.environ.get("AUTHORITY_TOPOFF_MAX_PAGES", "12"))
REQUEST_DELAY_SECONDS = float(os.environ.get("AUTHORITY_TOPOFF_REQUEST_DELAY", "0.55"))
CHECKPOINT_EVERY_ROWS = 25

COUNTRY_TOPOFF_CAP = 240

PLAN: list[tuple[str, str, str, str, int]] = [
    ("South Asia", "India", "matchbox label", '"India" "matchbox label"', 220),
    ("South Asia", "India", "matchbox label", '"Indian" "matchbox label"', 80),
    ("South Asia", "India", "film poster", '"India" "film poster"', 45),
    ("Southeast Asia", "Indonesia", "postage stamp", '"Indonesia" "postage stamp"', 60),
    ("Southeast Asia", "Indonesia", "matchbox label", '"Indonesia" "matchbox label"', 35),
    ("Middle East and North Africa", "Turkey", "postage stamp", '"Turkey" "postage stamp"', 70),
    ("Africa", "South Africa", "book cover", '"South Africa" "book cover"', 70),
    ("Africa", "South Africa", "stamp", '"South Africa" "stamp"', 60),
    ("Latin America / Caribbean", "Mexico", "postage stamp", '"Mexico" "postage stamp"', 80),
    ("Latin America / Caribbean", "Mexico", "stamp", '"Mexico" "stamp"', 45),
    ("Latin America / Caribbean", "Chile", "stamp", '"Chile" "stamp"', 60),
    ("Latin America / Caribbean", "Chile", "label", '"Chile" "label"', 40),
    ("Middle East and North Africa", "Egypt", "film poster", '"Egypt" "film poster"', 45),
    ("Middle East and North Africa", "Egypt", "book cover", '"Egypt" "book cover"', 35),
    ("Africa", "Nigeria", "film poster", '"Nigeria" "film poster"', 30),
    ("Africa", "Kenya", "stamp", '"Kenya" "stamp"', 35),
    ("Africa", "Ghana", "stamp", '"Ghana" "stamp"', 35),
    ("Eastern Europe / Caucasus", "Poland", "label", '"Poland" "label"', 35),
    ("East Asia", "Japan", "matchbox label", '"Japan" "matchbox label"', 45),
    ("East Asia", "Japan", "stamp", '"Japan" "stamp"', 35),
]


def country_added_counter(rows_before: list[dict[str, str]], rows_now: list[dict[str, str]]) -> Counter[str]:
    before = Counter(row.get("source_place_text", "") for row in rows_before)
    now = Counter(row.get("source_place_text", "") for row in rows_now)
    return Counter({key: max(0, now[key] - before.get(key, 0)) for key in now})


def topoff_direction(country: str, object_term: str) -> str:
    safe_country = base.clean(country).lower().replace(" ", "_").replace("/", "_")
    safe_object = base.clean(object_term).lower().replace(" ", "_").replace("/", "_")
    return f"topoff_{safe_country}_{safe_object}"


def main() -> None:
    base.REGION_SEEDS = auth.expanded_region_seeds()
    base.INFER_FALLBACK_REGION = None
    auth.DATA.mkdir(parents=True, exist_ok=True)
    auth.DOCS.mkdir(parents=True, exist_ok=True)
    rows = auth.read_csv(auth.RECORDS_CSV)
    baseline_rows = [dict(row) for row in rows]
    seen_ids, seen_images = auth.existing_keys(rows)
    macro_counts, country_counts, period_counts, object_counts, year_counts = auth.reseed_counters(rows)
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    completed = auth.completed_queries(len(rows))

    print(
        f"topoff_resume_rows={len(rows)} target={TARGET_ROWS} completed_queries={len(completed)}",
        flush=True,
    )
    for index, (macro, country, object_term, query, query_cap) in enumerate(PLAN, 1):
        if len(rows) >= TARGET_ROWS:
            break
        if query in completed:
            continue
        before = len(rows)
        added_this_query = 0
        status = "empty"
        offset: int | str = 0
        pages_seen = 0
        while pages_seen < MAX_PAGES_PER_QUERY and len(rows) < TARGET_ROWS and added_this_query < query_cap:
            added_by_country = country_added_counter(baseline_rows, rows)
            if added_by_country[f"{macro} / {country}"] >= COUNTRY_TOPOFF_CAP:
                rejects["topoff_country_cap"] += 1
                break
            url = base.search_url(query, offset=offset, limit=QUERY_LIMIT)
            try:
                payload = base.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"query": query, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=180)})
                status = "failed"
                time.sleep(REQUEST_DELAY_SECONDS * 4)
                break
            time.sleep(REQUEST_DELAY_SECONDS)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            status = "completed"
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(
                    page,
                    macro,
                    country,
                    topoff_direction(country, object_term),
                    object_term,
                    url,
                )
                if not row:
                    rejects["base_filter"] += 1
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    rejects["duplicate"] += 1
                    continue
                quality_ok, quality_reason = auth.quality_gate(row, object_term)
                if not quality_ok:
                    rejects[quality_reason] += 1
                    continue
                distribution_ok, distribution_reason = auth.distribution_gate(
                    row,
                    object_term,
                    macro_counts,
                    country_counts,
                    period_counts,
                    object_counts,
                    year_counts,
                )
                if not distribution_ok:
                    rejects[distribution_reason] += 1
                    continue
                row["direction_id"] = "CAWTOP2026"
                row["source_id"] = "SRC-COMMONS-AUTHORITY-TOPOFF-2026-V1"
                row["source_object_type"] = (
                    f"authority topoff Commons open image record; {object_term}; "
                    f"{auth.object_family(row, object_term)}"
                )
                row["classification_rationale"] = base.clean(
                    "Selected by authority topoff query: explicit country/object search, Commons open-license extmetadata, object-year evidence, duplicate exclusion, and distribution gate review.",
                    max_chars=700,
                )
                row["uncertainty_note"] = (
                    "Commons metadata can be user-maintained; verify object date, original creator, source credit, place relation, and object-family relevance before final scholarly use."
                )
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                added_this_query += 1
                macro_counts[auth.macro_key(row)] += 1
                country_counts[row.get("source_place_text", "")] += 1
                period_counts[auth.period_band(row)] += 1
                object_counts[auth.object_family(row, object_term)] += 1
                year_counts[auth.row_year(row)] += 1
                if len(rows) % CHECKPOINT_EVERY_ROWS == 0:
                    auth.write_outputs(rows, failures, rejects)
                    print(
                        f"topoff_checkpoint rows={len(rows)} query={index}/{len(PLAN)} added_query={added_this_query}",
                        flush=True,
                    )
                if len(rows) >= TARGET_ROWS or added_this_query >= query_cap:
                    break
            if "continue" not in payload:
                break
            offset = int((payload.get("continue") or {}).get("gsroffset", int(offset or 0) + QUERY_LIMIT))
            pages_seen += 1
        auth.append_state(
            {
                "query_index": f"topoff-{index}",
                "macro": macro,
                "country": country,
                "object_term": object_term,
                "query": query,
                "status": status,
                "added": str(len(rows) - before),
                "rows_after": str(len(rows)),
                "rejects_delta": str(sum(rejects.values())),
                "failures_delta": str(len(failures)),
                "elapsed_seconds": "topoff",
            }
        )
        if len(rows) > before:
            auth.write_outputs(rows, failures, rejects)
        print(
            f"topoff_query_progress={index}/{len(PLAN)} rows={len(rows)} added={len(rows)-before} failures={len(failures)} rejects={sum(rejects.values())}",
            flush=True,
        )

    auth.write_outputs(rows, failures, rejects)
    print(f"records={len(rows)}")
    print(f"target_met={len(rows) >= TARGET_ROWS}")
    print(f"topoff_added={len(rows) - len(baseline_rows)}")
    print(f"failures={len(failures)}")
    print(f"rejects={dict(rejects.most_common())}")


if __name__ == "__main__":
    main()
