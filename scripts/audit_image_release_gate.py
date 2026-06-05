from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
SOURCE_SUCCESS_REGISTRY = DATA / "nonmainstream_source_success_registry_2026_v1.csv"
IMAGE_READY = {"IMG01", "IMG02", "IMG03"}
BLOCKING_STATES = {"IMG00", "IMG04"}
MIN_SOURCE_VISIBLE_COVERAGE = 95
MIN_VERIFIED_OPEN_COVERAGE = 85
MIN_WEIGHTED_PUBLICATION_COVERAGE = 95
MIN_RELEASE_SOURCE_COVERAGE = 80
RELEASE_SOURCE_TARGET = 2000
MAX_IMG04_COVERAGE: float | None = None
TARGET_COVERAGE = 100

# Renderability is not the same as publication-grade image coverage.
# IMG02 is intentionally source-hosted and rights-sensitive; it proves that an
# image/viewer exists, but it cannot be counted as equivalent to an open,
# reviewed image in launch reporting.
PUBLICATION_WEIGHTS = {
    "IMG03": 0.9,
    "IMG02": 0.55,
    "IMG01": 0.3,
    "IMG00": 0.0,
    "IMG04": 0.0,
}


def clean(value: object) -> str:
    return str(value or "").strip()


def normalize_url(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    parsed = urlsplit(value)
    path = parsed.path.rstrip("/") or parsed.path
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def object_key(surface: dict) -> str:
    """Group repeated photos/views of one source object as one gate unit."""
    source_url = normalize_url(surface.get("sourceUrl", ""))
    if source_url:
        return f"url:{source_url}"
    record_id = clean(surface.get("sourceRecordId"))
    if record_id:
        return f"record:{record_id}"
    parts = [
        clean(surface.get("sourceName")),
        clean(surface.get("title")).lower(),
        clean(surface.get("dateText")),
    ]
    return "fallback:" + "|".join(parts)


def capture_source_count() -> int:
    sources: set[str] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if "cell_assignments" in path.name:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                source_name = clean(row.get("source_name"))
                if source_name:
                    sources.add(source_name)
    if SOURCE_SUCCESS_REGISTRY.exists():
        with SOURCE_SUCCESS_REGISTRY.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if clean(row.get("source_success_status")) != "success":
                    continue
                source_name = clean(row.get("source_name"))
                if source_name:
                    sources.add(source_name)
    return len(sources)


def pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def state_weight(surface: dict) -> float:
    return PUBLICATION_WEIGHTS.get(surface.get("image", {}).get("state", "IMG00"), 0.0)


def is_verified_open(surface: dict) -> bool:
    return (
        surface.get("image", {}).get("state") == "IMG03"
        and surface.get("reviewGates", {}).get("rightsReviewed") is True
    )


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    counts = Counter(surface.get("image", {}).get("state", "IMG00") for surface in surfaces)
    ready = sum(counts[state] for state in IMAGE_READY)
    verified_open = sum(1 for surface in surfaces if is_verified_open(surface))
    weighted_ready = sum(state_weight(surface) for surface in surfaces)
    total = len(surfaces)
    source_visible_coverage = pct(ready, total)
    verified_open_coverage = pct(verified_open, total)
    weighted_publication_coverage = pct(weighted_ready, total)

    object_groups: dict[str, list[dict]] = defaultdict(list)
    for surface in surfaces:
        object_groups[object_key(surface)].append(surface)
    object_total = len(object_groups)
    object_ready = sum(
        1
        for group in object_groups.values()
        if any(surface.get("image", {}).get("state") in IMAGE_READY for surface in group)
    )
    object_verified_open = sum(
        1
        for group in object_groups.values()
        if any(is_verified_open(surface) for surface in group)
    )
    object_weighted_ready = sum(max(state_weight(surface) for surface in group) for group in object_groups.values())
    object_counts = Counter(
        max(
            (surface.get("image", {}).get("state", "IMG00") for surface in group),
            key=lambda state: PUBLICATION_WEIGHTS.get(state, 0.0),
        )
        for group in object_groups.values()
    )
    object_source_visible_coverage = pct(object_ready, object_total)
    object_verified_open_coverage = pct(object_verified_open, object_total)
    object_weighted_publication_coverage = pct(object_weighted_ready, object_total)
    surface_img04_count = counts.get("IMG04", 0)
    surface_img04_coverage = pct(surface_img04_count, total)
    object_img04_count = object_counts.get("IMG04", 0)
    object_img04_coverage = pct(object_img04_count, object_total)

    active_source_count = capture_source_count()
    release_source_coverage = pct(active_source_count, RELEASE_SOURCE_TARGET)
    sources_needed_for_target = max(0, RELEASE_SOURCE_TARGET - active_source_count)
    sources_needed_for_minimum = max(
        0,
        int((MIN_RELEASE_SOURCE_COVERAGE / 100) * RELEASE_SOURCE_TARGET) - active_source_count,
    )

    blockers_by_source: dict[str, Counter[str]] = defaultdict(Counter)
    blockers_by_folder: dict[str, Counter[str]] = defaultdict(Counter)
    weighted_gap_by_source: dict[str, float] = defaultdict(float)
    unverified_visible_by_source: dict[str, Counter[str]] = defaultdict(Counter)
    blocker_examples: list[tuple[str, str, str, str]] = []

    for surface in surfaces:
        state = surface.get("image", {}).get("state", "IMG00")
        source = surface.get("sourceName", "Unknown source")
        weighted_gap_by_source[source] += 1.0 - PUBLICATION_WEIGHTS.get(state, 0.0)
        if state in {"IMG01", "IMG02"}:
            unverified_visible_by_source[source][state] += 1
        if state not in BLOCKING_STATES:
            continue
        blockers_by_source[source][state] += 1
        for folder in surface.get("folders", []):
            blockers_by_folder[f"{folder.get('type')} · {folder.get('title')}"][state] += 1
        if len(blocker_examples) < 25:
            blocker_examples.append(
                (
                    surface.get("surfaceId", ""),
                    state,
                    source,
                    surface.get("title", "")[:120],
                )
            )

    print(f"surfaces={total}")
    print(f"source_visible_image_ready={ready}")
    print(f"source_visible_coverage={source_visible_coverage}%")
    print(f"verified_open_images={verified_open}")
    print(f"verified_open_coverage={verified_open_coverage}%")
    print(f"weighted_publication_image_score={round(weighted_ready, 2)}")
    print(f"weighted_publication_coverage={weighted_publication_coverage}%")
    print(f"objects={object_total}")
    print(f"object_source_visible_image_ready={object_ready}")
    print(f"object_source_visible_coverage={object_source_visible_coverage}%")
    print(f"object_verified_open_images={object_verified_open}")
    print(f"object_verified_open_coverage={object_verified_open_coverage}%")
    print(f"object_weighted_publication_image_score={round(object_weighted_ready, 2)}")
    print(f"object_weighted_publication_coverage={object_weighted_publication_coverage}%")
    print(f"surface_img04_count={surface_img04_count}")
    print(f"surface_img04_coverage={surface_img04_coverage}%")
    print(f"object_img04_count={object_img04_count}")
    print(f"object_img04_coverage={object_img04_coverage}%")
    print(f"minimum_source_visible_gate={MIN_SOURCE_VISIBLE_COVERAGE}% object-level")
    print(f"minimum_verified_open_gate={MIN_VERIFIED_OPEN_COVERAGE}% object-level")
    print(f"minimum_weighted_publication_gate={MIN_WEIGHTED_PUBLICATION_COVERAGE}% object-level")
    print(f"maximum_img04_gate={'pending' if MAX_IMG04_COVERAGE is None else str(MAX_IMG04_COVERAGE) + '% object-level'}")
    print(f"release_source_target={RELEASE_SOURCE_TARGET}")
    print(f"release_active_source_count={active_source_count}")
    print(f"release_source_coverage={release_source_coverage}%")
    print(f"minimum_release_source_coverage={MIN_RELEASE_SOURCE_COVERAGE}%")
    print(f"release_sources_needed_for_80pct={sources_needed_for_minimum}")
    print(f"release_sources_needed_for_target={sources_needed_for_target}")
    print(f"target={TARGET_COVERAGE}%")
    print(f"surface_state_counts={dict(sorted(counts.items()))}")
    print(f"object_state_counts={dict(sorted(object_counts.items()))}")
    print(f"weights={PUBLICATION_WEIGHTS}")
    gates = {
        "source_visible_object_gate": object_source_visible_coverage >= MIN_SOURCE_VISIBLE_COVERAGE,
        "verified_open_object_gate": object_verified_open_coverage >= MIN_VERIFIED_OPEN_COVERAGE,
        "weighted_publication_object_gate": object_weighted_publication_coverage >= MIN_WEIGHTED_PUBLICATION_COVERAGE,
        "release_source_coverage_gate": release_source_coverage >= MIN_RELEASE_SOURCE_COVERAGE,
    }
    if MAX_IMG04_COVERAGE is not None:
        gates["img04_object_gate"] = object_img04_coverage <= MAX_IMG04_COVERAGE
    print(f"release_gates={gates}")

    if total:
        # If we only add image-ready surfaces and keep current blockers public,
        # this is the volume required to mathematically reach the launch gate.
        deficit_ready_only = max(0, int(((MIN_SOURCE_VISIBLE_COVERAGE / 100) * total - ready) / (1 - MIN_SOURCE_VISIBLE_COVERAGE / 100)) + 1)
        weighted_deficit = max(0.0, (MIN_WEIGHTED_PUBLICATION_COVERAGE / 100) * object_total - object_weighted_ready)
        print(f"new_source_visible_needed_if_no_blockers_removed={deficit_ready_only}")
        print(f"object_weighted_publication_points_needed={round(weighted_deficit, 2)}")

    print("\nblocking_sources:")
    for source, counter in sorted(blockers_by_source.items(), key=lambda item: -sum(item[1].values())):
        print(f"- {source}: {dict(counter)}")

    print("\nunverified_visible_sources:")
    for source, counter in sorted(unverified_visible_by_source.items(), key=lambda item: -sum(item[1].values()))[:20]:
        print(f"- {source}: {dict(counter)}")

    print("\nweighted_gap_sources:")
    for source, gap in sorted(weighted_gap_by_source.items(), key=lambda item: -item[1])[:20]:
        print(f"- {source}: {round(gap, 2)} points")

    print("\nblocking_folders:")
    for folder, counter in sorted(blockers_by_folder.items(), key=lambda item: -sum(item[1].values()))[:20]:
        print(f"- {folder}: {dict(counter)}")

    print("\nblocker_examples:")
    for surface_id, state, source, title in blocker_examples:
        print(f"- {surface_id} | {state} | {source} | {title}")

    if not all(gates.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
