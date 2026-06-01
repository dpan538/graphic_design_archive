#!/usr/bin/env python3
"""Probe source candidates before item-level ingestion.

This pass does not create public surfaces. It verifies whether edge/community/
university/government sources are reachable and what protocol family they seem
to expose, so later crawlers can be written by source family rather than by
large museum keyword sweeps.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
REGISTRY = DATA / "source_candidate_registry_v1.csv"
OUTPUT = DATA / "source_candidate_probe_v1.csv"
REPORT = DOCS / "SOURCE_CANDIDATE_PROBE_v1.md"
RAW_DIR = DATA / "source_candidate_probe_v1_raw"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 source-candidate-probe"

FIELDNAMES = [
    "probe_id",
    "candidate_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "institution_class",
    "institutional_level",
    "access_family_claimed",
    "url",
    "http_status",
    "final_url",
    "content_type",
    "response_bytes",
    "page_title",
    "meta_description",
    "detected_protocols",
    "protocol_evidence",
    "adapter_hint",
    "capture_priority_next",
    "recommended_image_policy",
    "recommended_text_policy",
    "probe_status",
    "failure_reason",
    "raw_probe_path",
    "access_date",
]

UNDERREPRESENTED_REGIONS = {
    "Latin America",
    "Latin America and the Caribbean",
    "Latin America / Transregional",
    "Mainland China",
    "East Asia",
    "Southeast Asia",
    "South Asia",
    "Middle East and North Africa",
    "Africa",
    "Eastern Europe",
    "Eastern Europe / Caucasus",
    "Oceania and Pacific",
}

EDGE_CLASSES = {"community", "university", "government", "municipal", "library"}
LOW_PRIORITY_PREFIXES = ("P4", "P5")


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            key = (attrs_d.get("name") or attrs_d.get("property") or "").lower()
            value = attrs_d.get("content", "")
            if key and value:
                self.meta[key] = html.unescape(value)
        if tag.lower() == "link":
            rel = attrs_d.get("rel", "")
            href = attrs_d.get("href", "")
            if href:
                self.links.append((rel, href))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return clean(" ".join(self.title_parts), max_chars=180)


def clean(value: Any, *, max_chars: int = 500) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def read_registry() -> list[dict[str, str]]:
    with REGISTRY.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def priority_score(row: dict[str, str]) -> tuple[int, int, int, int, str]:
    region_bonus = 0 if row["macro_region"] in UNDERREPRESENTED_REGIONS else 1
    class_bonus = 0 if row["institution_class"] in EDGE_CLASSES else 1
    priority = row.get("automation_priority", "")
    p_rank = 0
    if priority.startswith("P0"):
        p_rank = 5
    elif priority.startswith("P1"):
        p_rank = 0
    elif priority.startswith("P2"):
        p_rank = 1
    elif priority.startswith("P3"):
        p_rank = 2
    elif priority.startswith("P4"):
        p_rank = 3
    elif priority.startswith("P5"):
        p_rank = 4
    text_bonus = 0 if row.get("text_strategy") == "text-rich" else 1
    return (region_bonus, class_bonus, p_rank, text_bonus, row["candidate_id"])


def select_rows(limit: int) -> list[dict[str, str]]:
    rows = [
        row
        for row in read_registry()
        if row.get("current_ingest_status") != "active_in_public_payload"
        and row.get("macro_region") in UNDERREPRESENTED_REGIONS
        and row.get("institution_class") in EDGE_CLASSES
        and not row.get("automation_priority", "").startswith(LOW_PRIORITY_PREFIXES)
        and row.get("url", "").startswith("http")
    ]
    rows = sorted(rows, key=priority_score)
    return rows[:limit]


def fetch(url: str, timeout: int) -> tuple[int, str, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.6",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return (
            int(response.status),
            response.geturl(),
            response.headers.get("content-type", ""),
            response.read(180_000),
        )


def detect_protocols(blob: bytes, url: str, claimed: str) -> tuple[list[str], list[str]]:
    text = blob.decode("utf-8", errors="ignore")
    lower = text.lower()
    evidence: list[str] = []
    protocols: list[str] = []

    checks = [
        ("IIIF", ["iiif", "manifest.json", "presentation/2", "presentation/3"]),
        ("OAI-PMH", ["oai-pmh", "verb=identify", "oai_dc", "listrecords"]),
        ("CONTENTdm", ["contentdm", "/digital/api/", "dmwebservices"]),
        ("Omeka", ["omeka", "o:resource_class", "/api/items"]),
        ("DSpace", ["dspace", "/server/api/", "handle.net"]),
        ("Kramerius", ["kramerius", "api/client/v7.0", "api/client/v5.0"]),
        ("ArchiveSpace/EAD", ["ead2002", "ead3", "encoded archival description", "archivesspace", "finding aid"]),
        ("RSS/Atom", ["application/rss+xml", "application/atom+xml", "<rss", "<feed"]),
        ("JSON-LD", ["application/ld+json", "schema.org"]),
        ("PDF", [".pdf", "application/pdf"]),
    ]
    claimed_l = claimed.lower()
    for label, needles in checks:
        if label.lower() in claimed_l or any(needle in lower for needle in needles) or any(
            needle in url.lower() for needle in needles
        ):
            protocols.append(label)
            found = next((needle for needle in needles if needle in lower or needle in url.lower()), "claimed")
            evidence.append(f"{label}:{found}")
    return list(dict.fromkeys(protocols)), evidence


def adapter_hint(protocols: list[str], row: dict[str, str]) -> str:
    if "CONTENTdm" in protocols:
        return "contentdm_source_adapter"
    if "DSpace" in protocols:
        return "dspace_oai_or_rest_adapter"
    if "Kramerius" in protocols:
        return "kramerius_adapter"
    if "IIIF" in protocols:
        return "iiif_manifest_adapter"
    if "OAI-PMH" in protocols:
        return "oai_pmh_adapter"
    if "Omeka" in protocols:
        return "omeka_api_adapter"
    if "JSON-LD" in protocols:
        return "html_jsonld_adapter"
    if "PDF" in protocols:
        return "pdf_text_or_link_adapter"
    if row.get("text_strategy") == "text-rich":
        return "html_text_source_adapter"
    return "html_source_probe_then_manual_rules"


def next_priority(row: dict[str, str], status: int, protocols: list[str], title: str) -> str:
    if not (200 <= status < 400):
        return "hold_unreachable"
    if row["institution_class"] in {"community", "university", "government", "municipal"} and protocols:
        return "P1_adapter_candidate"
    if row["institution_class"] in {"community", "university", "government", "municipal"} and title:
        return "P2_html_source_candidate"
    return "P3_manual_source_candidate"


def image_policy(row: dict[str, str], protocols: list[str]) -> str:
    if row.get("image_strategy") == "text_only":
        return "IMG04_text_only_until_object_images_found"
    if any(proto in protocols for proto in ("IIIF", "CONTENTdm", "Kramerius")):
        return "IMG02_source_viewer_or_iiif_candidate"
    if row.get("image_strategy") == "prefer_open_image":
        return "IMG03_only_after_record_level_rights"
    return "IMG00_or_IMG02_after_record_level_rights"


def normalize_raw_blob(blob: bytes) -> bytes:
    text = blob.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "  ")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_raw(candidate_id: str, blob: bytes) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{candidate_id}.html.txt"
    path.write_bytes(normalize_raw_blob(blob))
    return str(path.relative_to(ROOT))


def probe_one(row: dict[str, str], timeout: int, index: int) -> dict[str, str]:
    base = {
        "probe_id": f"SCP{index:03d}",
        "candidate_id": row["candidate_id"],
        "source_name": row["source_name"],
        "macro_region": row["macro_region"],
        "country_or_region": row["country_or_region"],
        "institution_class": row["institution_class"],
        "institutional_level": row["institutional_level"],
        "access_family_claimed": row["access_family"],
        "url": row["url"],
        "access_date": ACCESS_DATE,
    }
    try:
        status, final_url, content_type, blob = fetch(row["url"], timeout)
        parser = HeadParser()
        parser.feed(blob[:90_000].decode("utf-8", errors="ignore"))
        protocols, evidence = detect_protocols(blob, final_url, row.get("access_family", ""))
        raw_path = write_raw(row["candidate_id"], blob)
        return {
            **base,
            "http_status": str(status),
            "final_url": final_url,
            "content_type": content_type,
            "response_bytes": str(len(blob)),
            "page_title": parser.title,
            "meta_description": clean(
                parser.meta.get("description") or parser.meta.get("og:description") or "",
                max_chars=240,
            ),
            "detected_protocols": ";".join(protocols),
            "protocol_evidence": ";".join(evidence),
            "adapter_hint": adapter_hint(protocols, row),
            "capture_priority_next": next_priority(row, status, protocols, parser.title),
            "recommended_image_policy": image_policy(row, protocols),
            "recommended_text_policy": "extract_source_text_or_context" if row.get("text_strategy") == "text-rich" else "metadata_plus_context",
            "probe_status": "ok",
            "failure_reason": "",
            "raw_probe_path": raw_path,
        }
    except urllib.error.HTTPError as exc:
        blob = exc.read(20_000) if hasattr(exc, "read") else b""
        return {
            **base,
            "http_status": str(exc.code),
            "final_url": exc.geturl() if hasattr(exc, "geturl") else row["url"],
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "response_bytes": str(len(blob)),
            "page_title": "",
            "meta_description": "",
            "detected_protocols": "",
            "protocol_evidence": "",
            "adapter_hint": "manual_review_or_alternate_endpoint",
            "capture_priority_next": "hold_http_error",
            "recommended_image_policy": "IMG00_until_source_endpoint_verified",
            "recommended_text_policy": "manual_context_only",
            "probe_status": "http_error",
            "failure_reason": clean(str(exc), max_chars=220),
            "raw_probe_path": "",
        }
    except Exception as exc:  # noqa: BLE001 - source probing records failures as data.
        return {
            **base,
            "http_status": "",
            "final_url": "",
            "content_type": "",
            "response_bytes": "",
            "page_title": "",
            "meta_description": "",
            "detected_protocols": "",
            "protocol_evidence": "",
            "adapter_hint": "manual_review_or_alternate_endpoint",
            "capture_priority_next": "hold_probe_failed",
            "recommended_image_policy": "IMG00_until_source_endpoint_verified",
            "recommended_text_policy": "manual_context_only",
            "probe_status": "failed",
            "failure_reason": clean(f"{type(exc).__name__}: {exc}", max_chars=220),
            "raw_probe_path": "",
        }


def write_report(rows: list[dict[str, str]], selected: list[dict[str, str]]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    status = Counter(row["probe_status"] for row in rows)
    priority = Counter(row["capture_priority_next"] for row in rows)
    regions = Counter(row["macro_region"] for row in rows)
    adapters = Counter(row["adapter_hint"] for row in rows)
    p1 = [row for row in rows if row["capture_priority_next"] == "P1_adapter_candidate"]
    lines = [
        "# Source Candidate Probe v1",
        "",
        "Source-level probe for edge/community/university/government candidates. This does not create public surfaces; it decides which source families deserve item-level adapters next.",
        "",
        f"- Access date: {ACCESS_DATE}",
        f"- Selected candidates: {len(selected)}",
        f"- Probe rows written: {len(rows)}",
        "",
        "## Probe Status",
        "",
    ]
    for key, count in status.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Next Capture Priority", ""])
    for key, count in priority.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Region Mix", ""])
    for key, count in regions.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Adapter Hints", ""])
    for key, count in adapters.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## P1 Adapter Candidates", ""])
    for row in p1[:25]:
        lines.append(
            f"- {row['candidate_id']} | {row['source_name']} | {row['macro_region']} | "
            f"{row['detected_protocols'] or row['access_family_claimed']} | {row['adapter_hint']}"
        )
    lines.extend(
        [
            "",
            "## Next Rule",
            "",
            "Promote only `P1_adapter_candidate` and selected `P2_html_source_candidate` rows into item-level capture scripts. Failed or HTTP-error rows stay in the registry as link-only or manual-review sources; they should not be removed because the archive index must still acknowledge source territories that are difficult to automate.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--timeout", type=int, default=16)
    parser.add_argument("--sleep", type=float, default=0.25)
    args = parser.parse_args()

    selected = select_rows(args.limit)
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(selected, start=1):
        result = probe_one(row, args.timeout, idx)
        rows.append(result)
        print(
            f"{idx:02d}/{len(selected)} {result['candidate_id']} "
            f"{result['probe_status']} {result['capture_priority_next']} {result['source_name']}"
        )
        time.sleep(args.sleep)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_report(rows, selected)
    print(f"Wrote {OUTPUT}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
