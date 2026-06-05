#!/usr/bin/env python3
"""Deterministic IIIF manifest discovery helpers.

These helpers find source-hosted display routes for crawlers. A discovered IIIF
manifest can support IMG02, but it is not a reuse license and cannot upgrade an
item to IMG03.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any


USER_AGENT = "ModernGDHistoryArchive/0.1 rights-first metadata crawler"
IIIF_CONTEXT_MARKERS = ("iiif.io/api/presentation", "iiif.io/api/image")
IIIF_PATHS = (
    "iiif/manifest",
    "iiif/presentation",
    "manifest",
    "manifest.json",
)


class ManifestLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.jsonld_blocks: list[str] = []
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            if href and ("manifest" in rel or "iiif" in rel):
                self.links.append(href)
        if tag.lower() == "script" and attrs_dict.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._jsonld_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_jsonld:
            self.jsonld_blocks.append("".join(self._jsonld_parts))
            self._in_jsonld = False


def fetch_text(url: str, timeout: int = 15) -> tuple[str, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        headers = {k.lower(): v for k, v in response.headers.items()}
        return response.read().decode("utf-8", errors="replace"), headers


def fetch_json(url: str, timeout: int = 15) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def is_iiif_manifest(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    context = data.get("@context")
    context_text = json.dumps(context).lower()
    if any(marker in context_text for marker in IIIF_CONTEXT_MARKERS):
        return data.get("type") in {"Manifest", "Collection"} or data.get("@type") in {
            "sc:Manifest",
            "sc:Collection",
        }
    return False


def manifest_candidates_from_html(page_url: str, html: str, headers: dict[str, str]) -> list[str]:
    candidates: list[str] = []
    for link_header in headers.get("link", "").split(","):
        if "manifest" in link_header.lower() or "iiif" in link_header.lower():
            match = re.search(r"<([^>]+)>", link_header)
            if match:
                candidates.append(urllib.parse.urljoin(page_url, match.group(1)))

    parser = ManifestLinkParser()
    parser.feed(html)
    candidates.extend(urllib.parse.urljoin(page_url, href) for href in parser.links)

    for block in parser.jsonld_blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        queue = [data]
        while queue:
            item = queue.pop()
            if isinstance(item, dict):
                for key in ("iiif_manifest", "manifest", "associatedMedia"):
                    value = item.get(key)
                    if isinstance(value, str) and "iiif" in value.lower():
                        candidates.append(urllib.parse.urljoin(page_url, value))
                    elif isinstance(value, dict):
                        queue.append(value)
                queue.extend(value for value in item.values() if isinstance(value, (dict, list)))
            elif isinstance(item, list):
                queue.extend(value for value in item if isinstance(value, (dict, list)))
    return list(dict.fromkeys(candidates))


def guessed_manifest_candidates(page_url: str) -> list[str]:
    parsed = urllib.parse.urlparse(page_url)
    base = f"{parsed.scheme}://{parsed.netloc}/"
    page_dir = page_url.rsplit("/", 1)[0] + "/"
    guesses = []
    for root in (base, page_dir):
        for path in IIIF_PATHS:
            guesses.append(urllib.parse.urljoin(root, path))
    return list(dict.fromkeys(guesses))


def discover_iiif_manifest(page_url: str) -> str | None:
    """Return the first validated IIIF manifest URL, if any."""

    try:
        html, headers = fetch_text(page_url)
    except (urllib.error.URLError, TimeoutError, ValueError):
        html, headers = "", {}

    candidates = manifest_candidates_from_html(page_url, html, headers)
    candidates.extend(guessed_manifest_candidates(page_url))
    for candidate in dict.fromkeys(candidates):
        try:
            data = fetch_json(candidate)
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            continue
        if is_iiif_manifest(data):
            return candidate
    return None


if __name__ == "__main__":
    import sys

    for arg in sys.argv[1:]:
        print(f"{arg}\t{discover_iiif_manifest(arg) or ''}")
