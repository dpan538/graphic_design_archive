#!/usr/bin/env python3
"""Audit public surface payload integrity for archive-box releases.

This is intentionally local/offline by default. It checks the public JSON for
issues that a visual archive cannot hide behind a simple IMG coverage count:
duplicate image URLs, known placeholders, missing text-continuation candidates,
card/sheet balance, and absent structural surface families.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path
from typing import Any


TEXT_FIELDS = (
    "descriptionSummary",
    "sourceDescription",
    "sourceNotes",
    "sourceSubjects",
    "historicalContextNote",
    "classificationRationale",
    "uncertaintyNote",
    "citationBasis",
)

PLACEHOLDER_PATTERNS = (
    "placeholder",
    "spacer.gif",
    "no-image",
    "no_image",
    "missing-image",
)


def words(surface: dict[str, Any]) -> list[str]:
    text = " ".join(str(surface.get(k) or "") for k in TEXT_FIELDS)
    return re.findall(r"[\w'-]+", text)


def image_url(surface: dict[str, Any]) -> str:
    image = surface.get("image") or {}
    return str(image.get("url") or "")


def image_state(surface: dict[str, Any]) -> str:
    image = surface.get("image") or {}
    return str(image.get("state") or "")


def display_no(surface: dict[str, Any]) -> str:
    return str(
        surface.get("displayNumber")
        or surface.get("provisionalDisplayNumber")
        or surface.get("surfaceId")
        or ""
    )


def title(surface: dict[str, Any]) -> str:
    return str(surface.get("title") or "").replace("\n", " ")


def audit(path: Path) -> tuple[list[str], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    surfaces = data.get("surfaces") or []
    warnings: list[str] = []
    lines: list[str] = []

    type_counts = collections.Counter(s.get("surfaceType") for s in surfaces)
    image_counts = collections.Counter(image_state(s) for s in surfaces)
    source_counts = collections.Counter(s.get("sourceName") for s in surfaces)

    urls: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for surface in surfaces:
        url = image_url(surface)
        if url:
            urls[url].append(surface)

    repeated_urls = {u: ss for u, ss in urls.items() if len(ss) > 1}
    placeholder_surfaces = [
        s
        for s in surfaces
        if any(pattern in image_url(s).lower() for pattern in PLACEHOLDER_PATTERNS)
    ]
    renderable = [
        s
        for s in surfaces
        if image_state(s) in {"IMG01", "IMG02", "IMG03"} and image_url(s)
    ]
    sheets = [s for s in surfaces if s.get("surfaceType") == "sheet"]
    cards = [s for s in surfaces if s.get("surfaceType") == "card"]
    short_text = [s for s in sheets if len(words(s)) < 60]
    no_source_url = [s for s in surfaces if not s.get("sourceUrl")]

    if placeholder_surfaces:
        warnings.append(f"{len(placeholder_surfaces)} renderable image URLs look like placeholders.")
    if repeated_urls:
        warnings.append(
            f"{sum(len(v) for v in repeated_urls.values())} surfaces share {len(repeated_urls)} exact image URLs."
        )
    if short_text:
        warnings.append(f"{len(short_text)} sheet surfaces have fewer than 60 text words.")
    if no_source_url:
        warnings.append(f"{len(no_source_url)} surfaces are missing sourceUrl.")
    reading_notes = data.get("readingNotes") or []
    bookmarks = data.get("bookmarks") or []
    folders = data.get("folders") or []
    folder_note_count = sum(1 for note in reading_notes if note.get("noteScope") == "folder")
    surface_note_count = sum(1 for note in reading_notes if note.get("noteScope") == "surface")
    if len(reading_notes) <= len(folders):
        warnings.append(
            f"Reading-note coverage is folder-only or below folder count; found {len(reading_notes)} readingNotes for {len(folders)} folders."
        )
    if folder_note_count != len(folders):
        warnings.append(
            f"Folder reading-note count should match folder count; found {folder_note_count} folder readingNotes for {len(folders)} folders."
        )
    if folders and len(bookmarks) >= len(folders):
        warnings.append(
            f"Bookmark count is suspiciously folder-like; found {len(bookmarks)} bookmarks for {len(folders)} folders."
        )
    if not data.get("appendices"):
        warnings.append("No top-level appendices collection is present in the payload.")

    lines.append(f"payload: {path}")
    lines.append(f"surfaces: {len(surfaces)}")
    lines.append(f"surface_type_counts: {dict(type_counts)}")
    lines.append(f"image_state_counts: {dict(image_counts)}")
    lines.append(f"renderable_image_surfaces: {len(renderable)} / {len(surfaces)}")
    lines.append(f"cards: {len(cards)}")
    lines.append(f"sheets: {len(sheets)}")
    lines.append(f"reading_notes: {len(reading_notes)}")
    lines.append(f"folder_reading_notes: {folder_note_count}")
    lines.append(f"surface_reading_notes: {surface_note_count}")
    lines.append(f"bookmarks: {len(bookmarks)}")
    lines.append(f"short_text_sheets_lt60_words: {len(short_text)}")
    lines.append(f"exact_repeated_image_urls: {len(repeated_urls)}")
    lines.append(f"placeholder_image_urls: {len(placeholder_surfaces)}")
    lines.append("top_sources:")
    for source, count in source_counts.most_common(15):
      lines.append(f"  {count:4d}  {source}")

    if repeated_urls:
        lines.append("repeated_url_examples:")
        for url, ss in sorted(repeated_urls.items(), key=lambda item: -len(item[1]))[:20]:
            lines.append(f"  {len(ss)}x {url}")
            for s in ss[:6]:
                lines.append(f"    - {display_no(s)} | {image_state(s)} | {title(s)[:100]}")

    if placeholder_surfaces:
        lines.append("placeholder_examples:")
        for s in placeholder_surfaces[:20]:
            lines.append(f"  - {display_no(s)} | {image_state(s)} | {title(s)[:100]} | {image_url(s)}")

    if short_text:
        lines.append("short_text_examples:")
        for s in short_text[:20]:
            lines.append(f"  - {display_no(s)} | {len(words(s))} words | {title(s)[:100]}")

    return warnings, lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "payload",
        nargs="?",
        default="generated/public_surfaces_v1.json",
        help="Path to public surface payload JSON.",
    )
    args = parser.parse_args()
    warnings, lines = audit(Path(args.payload))
    print("\n".join(lines))
    if warnings:
        print("\nwarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
