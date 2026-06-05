#!/usr/bin/env python3
"""Audit IMG00-IMG04 payload consistency.

This checks data-layer contradictions only. A page may still render badly in the
frontend even when this audit passes; in that case the bug is in the template or
CSS, not the generated image-state payload.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"


def image(surface: dict[str, Any]) -> dict[str, Any]:
    value = surface.get("image")
    return value if isinstance(value, dict) else {}


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    counts: Counter[str] = Counter()
    findings: list[str] = []

    for surface in surfaces:
        img = image(surface)
        state = img.get("state") or "IMG00"
        counts[state] += 1
        sid = surface.get("surfaceId", "unknown")
        title = surface.get("title", "Untitled")
        has_frame = img.get("hasImageFrame")
        url = img.get("url")
        display_mode = img.get("displayMode") or img.get("frameBehavior")
        expectation = img.get("expectation")

        if state == "IMG04":
            if has_frame is True:
                findings.append(f"{sid}: IMG04 must have hasImageFrame=false ({title})")
            if url:
                findings.append(f"{sid}: IMG04 must not carry image.url ({title})")
            if display_mode and display_mode not in {"no_image_frame"}:
                findings.append(f"{sid}: IMG04 display mode must be no_image_frame ({display_mode})")
            if expectation and expectation != "not_expected":
                findings.append(f"{sid}: IMG04 expectation must be not_expected ({expectation})")
        elif state in {"IMG00", "IMG01", "IMG02", "IMG03"}:
            if has_frame is False:
                findings.append(f"{sid}: {state} should keep an image frame contract ({title})")

        if state == "IMG00" and url:
            findings.append(f"{sid}: IMG00 should not carry displayable image.url ({title})")

        if state == "IMG03" and not url:
            findings.append(f"{sid}: IMG03 requires image.url evidence ({title})")

    print(f"surfaces={len(surfaces)}")
    print(f"image_state_counts={dict(sorted(counts.items()))}")
    if findings:
        print("img state contract findings:")
        for line in findings[:100]:
            print(f"- {line}")
        if len(findings) > 100:
            print(f"- ... {len(findings) - 100} more")
        return 1
    print("img state contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
