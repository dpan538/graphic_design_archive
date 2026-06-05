#!/usr/bin/env python3
"""Probe edge source candidates without ingesting item records or images.

This source-level pass is deliberately conservative:
- it fetches only source pages/API endpoints as text evidence;
- it never downloads or stores image binaries;
- it never upgrades image status to IMG01/IMG03 from heuristic signals;
- social/platform/portfolio sources are discovery-only until item-level source
  and rights review is available.
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

DEFAULT_INPUT = DATA / "global_edge_discovery_candidates_v1.csv"
DEFAULT_OUTPUT = DATA / "global_edge_discovery_probe_v1.csv"
DEFAULT_METRICS = DATA / "global_edge_discovery_probe_metrics_v1.csv"
DEFAULT_REPORT = DOCS / "GLOBAL_EDGE_DISCOVERY_PROBE_v1.md"
DEFAULT_RAW_DIR = DATA / "global_edge_discovery_probe_v1_raw"

ACCESS_DATE = "2026-06-05"
USER_AGENT = "ModernGDHistory/0.1 rights-safe-source-probe"

FIELDNAMES = [
    "candidate_id",
    "source_name",
    "macro_region",
    "subregion",
    "country_or_region",
    "source_class",
    "institutional_level",
    "protocol_family",
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
    "recommended_image_policy_next",
    "recommended_text_policy_next",
    "rights_risk",
    "capture_priority_next",
    "probe_status",
    "failure_reason",
    "raw_probe_path",
    "access_date",
    "notes",
]

METRIC_FIELDNAMES = ["metric", "value", "count"]

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|token|bearer|password|secret|session|cookie|private)\s*[:=]\s*['\"]?[^'\"\s<>&]{8,}"),
    re.compile(r"ghp_[0-9A-Za-z]{20,}"),
    re.compile(r"github_pat_[0-9A-Za-z_]{20,}"),
    re.compile(r"sk-[0-9A-Za-z]{20,}"),
]

DISCOVERY_ONLY_MARKERS = {
    "instagram",
    "pinterest",
    "behance",
    "tumblr",
    "reddit",
    "facebook",
    "twitter",
    "x.com",
    "are.na",
    "cargo",
    "social",
    "platform",
    "portfolio",
    "independent web",
}


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "meta":
            key = (attrs_d.get("name") or attrs_d.get("property") or "").lower()
            value = attrs_d.get("content", "")
            if key and value:
                self.meta[key] = html.unescape(value)
        elif tag.lower() == "link":
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


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET_SIGNAL]", redacted)
    return redacted


def workspace_path(path: Path) -> Path:
    """Resolve CLI paths relative to the repository root for repeatable reports."""
    return path if path.is_absolute() else ROOT / path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def fetch(url: str, timeout: int) -> tuple[int, str, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return (
            int(response.status),
            response.geturl(),
            response.headers.get("content-type", ""),
            response.read(180_000),
        )


def detect_protocols(blob: bytes, url: str, claimed: str, links: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    text = blob.decode("utf-8", errors="ignore")
    lower = text.lower()
    claimed_l = claimed.lower()
    url_l = url.lower()
    link_text = " ".join([f"{rel} {href}" for rel, href in links]).lower()
    haystack = " ".join([lower, claimed_l, url_l, link_text])

    checks = [
        ("IIIF", ["iiif", "manifest.json", "presentation/2", "presentation/3", 'rel="manifest"', "rel=manifest"]),
        ("OAI-PMH", ["oai-pmh", "verb=identify", "oai_dc", "listrecords", "metadataPrefix"]),
        ("CONTENTdm", ["contentdm", "/digital/api/", "dmwebservices", "cdm/ref/collection"]),
        ("Omeka", ["omeka", "o:resource_class", "/api/items", "omeka-s"]),
        ("DSpace", ["dspace", "/server/api/", "handle.net", "bitstream"]),
        ("Kramerius", ["kramerius", "api/client/v7.0", "api/client/v5.0"]),
        ("ArchiveSpace/EAD", ["ead2002", "ead3", "encoded archival description", "archivesspace", "finding aid"]),
        ("RSS/Atom", ["application/rss+xml", "application/atom+xml", "<rss", "<feed", "rel=\"alternate\""]),
        ("JSON-LD", ["application/ld+json", "schema.org"]),
        ("WordPress REST", ["wp-json", "wp-content", "wordpress"]),
        ("GraphQL", ["graphql", "__typename", "apollo-state"]),
        ("Static JS App", ["_next/static", "__next_data__", "window.__", "vite", "webpack"]),
        ("PDF", [".pdf", "application/pdf"]),
    ]

    protocols: list[str] = []
    evidence: list[str] = []
    for label, needles in checks:
        hit = next((needle for needle in needles if needle.lower() in haystack), "")
        if hit:
            protocols.append(label)
            evidence.append(f"{label}:{hit}")
    return list(dict.fromkeys(protocols)), evidence


def is_discovery_only(row: dict[str, str]) -> bool:
    fields = " ".join(
        [
            row.get("source_name", ""),
            row.get("source_class", ""),
            row.get("protocol_family", ""),
            row.get("url", ""),
            row.get("recommended_adapter", ""),
            row.get("notes", ""),
        ]
    ).lower()
    return any(marker in fields for marker in DISCOVERY_ONLY_MARKERS)


def adapter_hint(row: dict[str, str], protocols: list[str]) -> str:
    if is_discovery_only(row):
        return "discovery_signal_only_no_item_image_ingest"
    ordered = [
        ("CONTENTdm", "contentdm_source_adapter"),
        ("DSpace", "dspace_oai_or_rest_adapter"),
        ("Kramerius", "kramerius_adapter"),
        ("IIIF", "iiif_manifest_adapter"),
        ("OAI-PMH", "oai_pmh_adapter"),
        ("Omeka", "omeka_api_adapter"),
        ("WordPress REST", "wordpress_rest_or_html_adapter"),
        ("GraphQL", "graphql_schema_probe_then_adapter"),
        ("JSON-LD", "html_jsonld_adapter"),
        ("RSS/Atom", "rss_atom_source_adapter"),
        ("Static JS App", "headless_metadata_probe_only"),
        ("PDF", "pdf_text_or_link_adapter"),
    ]
    for protocol, hint in ordered:
        if protocol in protocols:
            return hint
    recommended = row.get("recommended_adapter", "")
    if recommended:
        return recommended
    if "text" in row.get("text_enrichment_path", "").lower():
        return "html_text_source_adapter"
    return "html_source_probe_then_manual_rules"


def image_policy(row: dict[str, str], protocols: list[str]) -> str:
    if is_discovery_only(row):
        return "IMG00 discovery-only; resolve original source before public image display"
    recommended = row.get("recommended_image_policy", "")
    if "IMG04" in recommended:
        return "IMG04 text/source registry; no image frame unless item-level visual record is found"
    if "IMG03" in recommended:
        return "IMG03 only if authoritative item license confirms; otherwise IMG02/IMG00"
    if any(protocol in protocols for protocol in ("IIIF", "CONTENTdm", "Kramerius")):
        return "IMG02 source-hosted viewer candidate; IMG03 only with record-level open license"
    if "WordPress REST" in protocols or "RSS/Atom" in protocols:
        return "IMG00/IMG02 after item rights review; no automatic thumbnail upgrade"
    return "IMG00 until item rights and source terms are reviewed; IMG02 if source viewer exists"


def text_policy(row: dict[str, str], protocols: list[str]) -> str:
    claimed = row.get("text_enrichment_path", "")
    if claimed:
        return claimed
    if "PDF" in protocols:
        return "extract bibliographic/source text only; no PDF image possession"
    if any(protocol in protocols for protocol in ("RSS/Atom", "WordPress REST", "JSON-LD")):
        return "extract title/summary/tags/citations with field provenance"
    return "metadata + source context note; no unsupported interpretation"


def rights_risk(row: dict[str, str], protocols: list[str]) -> str:
    fields = " ".join(
        [row.get("source_class", ""), row.get("rights_posture", ""), row.get("risk_notes", ""), row.get("url", "")]
    ).lower()
    flags: list[str] = []
    if is_discovery_only(row):
        flags.append("discovery_only_platform")
    if "community" in fields or "indigenous" in fields or "activist" in fields:
        flags.append("community_or_cultural_review")
    if "access" in fields or "subscription" in fields or "onsite" in fields:
        flags.append("access_or_terms_review")
    if "unknown" in fields or "manual" in fields:
        flags.append("manual_rights_review")
    if "IIIF" in protocols:
        flags.append("iiif_is_viewer_not_reuse")
    return ";".join(flags) if flags else "standard_rights_review"


def priority_next(row: dict[str, str], status: int | None, protocols: list[str], title: str) -> str:
    if status is None or not (200 <= status < 400):
        return "P2 retry/manual verification"
    if is_discovery_only(row):
        return "P2 discovery lead queue"
    if row.get("priority", "").startswith("P1") and protocols:
        return "P1 adapter build"
    if any(protocol in protocols for protocol in ("IIIF", "OAI-PMH", "CONTENTdm", "Omeka", "DSpace", "Kramerius")):
        return "P1 adapter build"
    if title or "JSON-LD" in protocols or "WordPress REST" in protocols:
        return "P1 text/source enrichment"
    return "P2 manual source review"


def safe_filename(candidate_id: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", candidate_id)[:80]


def write_raw(raw_dir: Path, candidate_id: str, blob: bytes) -> str:
    raw_dir = workspace_path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    text = blob.decode("utf-8", errors="replace")
    text = redact_secrets(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "  ")
    path = raw_dir / f"{safe_filename(candidate_id)}.html.txt"
    path.write_text(text[:180_000], encoding="utf-8")
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def probe_one(row: dict[str, str], timeout: int, raw_dir: Path) -> dict[str, str]:
    base = {
        "candidate_id": row.get("candidate_id", ""),
        "source_name": row.get("source_name", ""),
        "macro_region": row.get("macro_region", ""),
        "subregion": row.get("subregion", ""),
        "country_or_region": row.get("country_or_region", ""),
        "source_class": row.get("source_class", ""),
        "institutional_level": row.get("institutional_level", ""),
        "protocol_family": row.get("protocol_family", ""),
        "url": row.get("url", ""),
        "access_date": ACCESS_DATE,
        "notes": clean(row.get("notes", ""), max_chars=260),
    }
    try:
        status, final_url, content_type, blob = fetch(row.get("url", ""), timeout)
        parser = HeadParser()
        parser.feed(blob[:100_000].decode("utf-8", errors="ignore"))
        protocols, evidence = detect_protocols(blob, final_url, row.get("protocol_family", ""), parser.links)
        raw_path = write_raw(raw_dir, row.get("candidate_id", "candidate"), blob)
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
            "adapter_hint": adapter_hint(row, protocols),
            "recommended_image_policy_next": image_policy(row, protocols),
            "recommended_text_policy_next": text_policy(row, protocols),
            "rights_risk": rights_risk(row, protocols),
            "capture_priority_next": priority_next(row, status, protocols, parser.title),
            "probe_status": "ok",
            "failure_reason": "",
            "raw_probe_path": raw_path,
        }
    except urllib.error.HTTPError as exc:
        return {
            **base,
            "http_status": str(exc.code),
            "final_url": exc.geturl() if hasattr(exc, "geturl") else row.get("url", ""),
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "response_bytes": "",
            "page_title": "",
            "meta_description": "",
            "detected_protocols": "",
            "protocol_evidence": "",
            "adapter_hint": "manual_review_or_alternate_endpoint",
            "recommended_image_policy_next": "IMG00 until source endpoint and item rights are verified",
            "recommended_text_policy_next": "manual context only",
            "rights_risk": rights_risk(row, []),
            "capture_priority_next": priority_next(row, exc.code, [], ""),
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
            "recommended_image_policy_next": "IMG00 until source endpoint and item rights are verified",
            "recommended_text_policy_next": "manual context only",
            "rights_risk": rights_risk(row, []),
            "capture_priority_next": "P2 retry/manual verification",
            "probe_status": "failed",
            "failure_reason": clean(f"{type(exc).__name__}: {exc}", max_chars=220),
            "raw_probe_path": "",
        }


def metric_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    metrics: list[dict[str, str]] = []

    def add_counter(metric: str, counter: Counter[str]) -> None:
        for value, count in counter.most_common():
            metrics.append({"metric": metric, "value": value or "(blank)", "count": str(count)})

    metrics.append({"metric": "total", "value": "rows", "count": str(len(rows))})
    add_counter("probe_status", Counter(row["probe_status"] for row in rows))
    add_counter("macro_region", Counter(row["macro_region"] for row in rows))
    add_counter("subregion", Counter(row["subregion"] for row in rows))
    add_counter("adapter_hint", Counter(row["adapter_hint"] for row in rows))
    add_counter("capture_priority_next", Counter(row["capture_priority_next"] for row in rows))
    add_counter("recommended_image_policy_next", Counter(row["recommended_image_policy_next"] for row in rows))
    protocol_counter: Counter[str] = Counter()
    for row in rows:
        for protocol in row["detected_protocols"].split(";"):
            if protocol:
                protocol_counter[protocol] += 1
    add_counter("detected_protocol", protocol_counter)
    return metrics


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict[str, str]], metrics: list[dict[str, str]], title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = Counter(row["probe_status"] for row in rows)
    priority = Counter(row["capture_priority_next"] for row in rows)
    regions = Counter(row["macro_region"] for row in rows)
    adapters = Counter(row["adapter_hint"] for row in rows)
    protocols: Counter[str] = Counter()
    for row in rows:
        for protocol in row["detected_protocols"].split(";"):
            if protocol:
                protocols[protocol] += 1

    p1 = [row for row in rows if row["capture_priority_next"].startswith("P1")]
    failures = [row for row in rows if row["probe_status"] != "ok"]
    lines = [
        f"# {title}",
        "",
        "Rights-safe source-level probe. This report records reachability, protocol signals, adapter hints, and next capture priority. It does not create public archive surfaces and does not download or possess source images.",
        "",
        f"- Access date: {ACCESS_DATE}",
        f"- Probe rows: {len(rows)}",
        f"- Metrics rows: {len(metrics)}",
        "",
        "## Safety Constraints",
        "",
        "- IMG01 and IMG03 are never assigned from heuristic, visual, social, or LLM signals.",
        "- IIIF/CONTENTdm/Kramerius evidence can recommend IMG02 only as source-hosted viewing, not reuse.",
        "- Platform and social sources are discovery leads until original sources and rights are reviewed.",
        "- Impact or priority signals are internal triage only, not public authority or inclusion claims.",
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
    lines.extend(["", "## Detected Protocols", ""])
    for key, count in protocols.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Adapter Hints", ""])
    for key, count in adapters.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## P1 Candidates", ""])
    for row in p1[:35]:
        lines.append(
            f"- {row['candidate_id']} | {row['source_name']} | {row['macro_region']} / "
            f"{row['subregion']} | {row['detected_protocols'] or row['protocol_family']} | "
            f"{row['adapter_hint']}"
        )
    lines.extend(["", "## Failed Or Manual Retry", ""])
    for row in failures[:35]:
        lines.append(
            f"- {row['candidate_id']} | {row['source_name']} | {row['probe_status']} | "
            f"{row['failure_reason'] or row['http_status']}"
        )
    lines.extend(
        [
            "",
            "## Next Rule",
            "",
            "Promote reachable protocol-family rows into source-family adapters first. Discovery-only rows should become source-registry or edge-source leads, not public image records, until a stable original source and rights basis are available.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--report-title", default="Global Edge Discovery Probe v1")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    input_path = workspace_path(args.input)
    output_csv = workspace_path(args.output_csv)
    metrics_path = workspace_path(args.metrics)
    report_path = workspace_path(args.report)
    raw_dir = workspace_path(args.raw_dir)

    rows_in = [row for row in read_rows(input_path) if row.get("url", "").startswith("http")]
    if args.limit > 0:
        rows_in = rows_in[: args.limit]

    rows: list[dict[str, str]] = []
    for index, row in enumerate(rows_in, start=1):
        result = probe_one(row, args.timeout, raw_dir)
        rows.append(result)
        print(
            f"{index:03d}/{len(rows_in)} {result['candidate_id']} "
            f"{result['probe_status']} {result['capture_priority_next']} {result['source_name']}"
        )
        time.sleep(args.sleep)

    metrics = metric_rows(rows)
    write_csv(output_csv, FIELDNAMES, rows)
    write_csv(metrics_path, METRIC_FIELDNAMES, metrics)
    write_report(report_path, rows, metrics, args.report_title)
    print(f"Wrote {output_csv.relative_to(ROOT)}")
    print(f"Wrote {metrics_path.relative_to(ROOT)}")
    print(f"Wrote {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
