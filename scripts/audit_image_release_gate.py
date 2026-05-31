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


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    counts = Counter(surface.get("image", {}).get("state", "IMG00") for surface in surfaces)
    ready = sum(counts[state] for state in IMAGE_READY)
    total = len(surfaces)
    coverage = round((ready / total) * 100, 2) if total else 0.0

    blockers_by_source: dict[str, Counter[str]] = defaultdict(Counter)
    blockers_by_folder: dict[str, Counter[str]] = defaultdict(Counter)
    blocker_examples: list[tuple[str, str, str, str]] = []

    for surface in surfaces:
        state = surface.get("image", {}).get("state", "IMG00")
        if state not in BLOCKING_STATES:
            continue
        source = surface.get("sourceName", "Unknown source")
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
    print(f"image_ready={ready}")
    print(f"coverage={coverage}%")
    print(f"minimum_launch_gate={MIN_LAUNCH_COVERAGE}%")
    print(f"target={TARGET_COVERAGE}%")
    print(f"state_counts={dict(sorted(counts.items()))}")

    if total:
        # If we only add image-ready surfaces and keep current blockers public,
        # this is the volume required to mathematically reach the launch gate.
        deficit_ready_only = max(0, int(((MIN_LAUNCH_COVERAGE / 100) * total - ready) / (1 - MIN_LAUNCH_COVERAGE / 100)) + 1)
        print(f"new_image_ready_needed_if_no_blockers_removed={deficit_ready_only}")

    print("\nblocking_sources:")
    for source, counter in sorted(blockers_by_source.items(), key=lambda item: -sum(item[1].values())):
        print(f"- {source}: {dict(counter)}")

    print("\nblocking_folders:")
    for folder, counter in sorted(blockers_by_folder.items(), key=lambda item: -sum(item[1].values()))[:20]:
        print(f"- {folder}: {dict(counter)}")

    print("\nblocker_examples:")
    for surface_id, state, source, title in blocker_examples:
        print(f"- {surface_id} | {state} | {source} | {title}")

    if coverage < MIN_LAUNCH_COVERAGE:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
