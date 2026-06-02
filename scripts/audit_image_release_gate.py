from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
IMAGE_READY = {"IMG01", "IMG02", "IMG03"}
BLOCKING_STATES = {"IMG00", "IMG04"}
MIN_LAUNCH_COVERAGE = 95
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


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    counts = Counter(surface.get("image", {}).get("state", "IMG00") for surface in surfaces)
    ready = sum(counts[state] for state in IMAGE_READY)
    verified_open = sum(
        1
        for surface in surfaces
        if surface.get("image", {}).get("state") == "IMG03"
        and surface.get("reviewGates", {}).get("rightsReviewed") is True
    )
    weighted_ready = sum(
        PUBLICATION_WEIGHTS.get(surface.get("image", {}).get("state", "IMG00"), 0.0)
        for surface in surfaces
    )
    total = len(surfaces)
    source_visible_coverage = round((ready / total) * 100, 2) if total else 0.0
    verified_open_coverage = round((verified_open / total) * 100, 2) if total else 0.0
    weighted_publication_coverage = round((weighted_ready / total) * 100, 2) if total else 0.0

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
    print(f"minimum_launch_gate={MIN_LAUNCH_COVERAGE}% weighted/publication-grade")
    print(f"target={TARGET_COVERAGE}%")
    print(f"state_counts={dict(sorted(counts.items()))}")
    print(f"weights={PUBLICATION_WEIGHTS}")

    if total:
        # If we only add image-ready surfaces and keep current blockers public,
        # this is the volume required to mathematically reach the launch gate.
        deficit_ready_only = max(0, int(((MIN_LAUNCH_COVERAGE / 100) * total - ready) / (1 - MIN_LAUNCH_COVERAGE / 100)) + 1)
        weighted_deficit = max(0.0, (MIN_LAUNCH_COVERAGE / 100) * total - weighted_ready)
        print(f"new_source_visible_needed_if_no_blockers_removed={deficit_ready_only}")
        print(f"weighted_publication_points_needed={round(weighted_deficit, 2)}")

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

    if weighted_publication_coverage < MIN_LAUNCH_COVERAGE:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
