#!/usr/bin/env python3
"""Probe South Asian source prospects before item-level capture.

The project currently has no active South Asia source coverage. This probe
checks the launch-scope prospect registry for reachable P1/P2 South Asian
sources and stores redacted raw HTML for source-registry promotion.
"""

from __future__ import annotations

import csv
import html
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REGISTRY = DATA / "source_prospect_registry_v2.csv"
RAW_DIR = DATA / "source_probe_south_asia_v1_raw"
OUT_CSV = DATA / "source_probe_south_asia_v1.csv"
REPORT = ROOT / "docs" / "capture" / "SOUTH_ASIA_SOURCE_PROBE_v1.md"

ACCESS_DATE = "2026-06-02"
USER_AGENT = "ModernGDHistory/0.1 south-asia-source-probe"

SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"(?i)(key=)[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key[\"'\s:=]+)[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)

FIELDNAMES = [
    "candidate_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "source_class",
    "period_intent",
    "url",
    "http_status",
    "final_url",
    "content_type",
    "response_bytes",
    "page_title",
    "meta_description",
    "detected_protocols",
    "protocol_evidence",
    "capture_priority",
    "capture_intent",
    "recommended_image_policy",
    "recommended_text_policy",
    "rights_risk",
    "probe_status",
    "failure_reason",
    "raw_probe_path",
    "access_date",
    "notes",
]


def clean(value: object, max_chars: int = 600) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def redact(value: str) -> str:
    out = value
    for pattern in SECRET_PATTERNS:
        out = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED_SECRET]", out)
    return out


def fetch(url: str) -> tuple[int, str, str, bytes]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json,application/xml,*/*"},
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=28, context=context) as response:
        return response.status, response.geturl(), response.headers.get("content-type", ""), response.read(180_000)


def write_raw(candidate_id: str, body: bytes, suffix: str = "html") -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{candidate_id}.{suffix}.txt"
    path.write_text(redact(body.decode("utf-8", errors="replace")), encoding="utf-8")
    return str(path.relative_to(ROOT))


def title_and_description(body: str) -> tuple[str, str]:
    title = ""
    description = ""
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
    if match:
        title = clean(re.sub(r"<[^>]+>", " ", match.group(1)), 240)
    for key in ("description", "og:description", "twitter:description"):
        pattern = re.compile(
            r"<meta[^>]+(?:name|property)=[\"']"
            + re.escape(key)
            + r"[\"'][^>]+content=[\"'](.*?)[\"']",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(body)
        if match:
            description = clean(match.group(1), 500)
            break
    return title, description


def detect_protocols(body: str, content_type: str, url: str) -> tuple[str, str]:
    low = (body + " " + content_type + " " + url).lower()
    checks = (
        ("WordPress REST/RSS", ("wp-json", "wp-content", "application/rss+xml", "/feed/")),
        ("IIIF", ("iiif", "manifest.json", "presentation/")),
        ("DSpace", ("dspace", "/server/api", "oai/request")),
        ("OAI-PMH", ("oai/request", "verb=identify", "oai-pmh")),
        ("JSON-LD", ("application/ld+json", "schema.org")),
        ("Next/static JS", ("__next_data__", "/_next/static")),
        ("PDF", (".pdf", "application/pdf")),
    )
    protocols: list[str] = []
    evidence: list[str] = []
    for label, needles in checks:
        hit = next((needle for needle in needles if needle in low), "")
        if hit:
            protocols.append(label)
            evidence.append(f"{label}:{hit}")
    return ";".join(protocols), ";".join(evidence)


def prospects() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(REGISTRY):
        if row.get("region_group") != "South Asia":
            continue
        priority = row.get("capture_priority", "")
        if not (priority.startswith("P1") or priority.startswith("P2")):
            continue
        rows.append(row)
    return rows


def recommended_image_policy(row: dict[str, str]) -> str:
    expected = row.get("expected_image_path", "")
    if "no_image" in expected:
        return "IMG04_text_or_source_dossier"
    if "viewer" in expected or "iiif" in expected:
        return "IMG02_source_hosted_or_viewer_review_required"
    return "IMG00_or_IMG02_after_source_terms"


def main() -> None:
    out_rows: list[dict[str, str]] = []
    for row in prospects():
        source_id = row.get("source_prospect_id", "")
        url = row.get("source_url", "")
        result = {
            "candidate_id": source_id,
            "source_name": row.get("source_name", ""),
            "macro_region": row.get("region_group", ""),
            "country_or_region": row.get("country_or_territory", ""),
            "source_class": row.get("source_family", ""),
            "period_intent": "pre-WWII-present" if row.get("period_1830_1930") else "modern-present",
            "url": url,
            "http_status": "",
            "final_url": "",
            "content_type": "",
            "response_bytes": "",
            "page_title": "",
            "meta_description": "",
            "detected_protocols": "",
            "protocol_evidence": "",
            "capture_priority": row.get("capture_priority", ""),
            "capture_intent": row.get("notes") or row.get("source_role", ""),
            "recommended_image_policy": recommended_image_policy(row),
            "recommended_text_policy": "extract_source_text_or_context; no AI-generated evidence",
            "rights_risk": "high" if "high" in row.get("rights_posture", "") else "medium",
            "probe_status": "",
            "failure_reason": "",
            "raw_probe_path": "",
            "access_date": ACCESS_DATE,
            "notes": row.get("known_limitations") or row.get("recommended_adapter") or row.get("notes", ""),
        }
        try:
            status, final_url, content_type, body = fetch(url)
            raw_path = write_raw(source_id, body)
            title, description = title_and_description(body.decode("utf-8", errors="replace"))
            protocols, evidence = detect_protocols(body.decode("utf-8", errors="replace"), content_type, final_url)
            result.update(
                {
                    "http_status": str(status),
                    "final_url": final_url,
                    "content_type": content_type,
                    "response_bytes": str(len(body)),
                    "page_title": title,
                    "meta_description": description,
                    "detected_protocols": protocols,
                    "protocol_evidence": evidence,
                    "probe_status": "ok",
                    "raw_probe_path": raw_path,
                }
            )
        except urllib.error.HTTPError as exc:
            result.update({"http_status": str(exc.code), "probe_status": "http_error", "failure_reason": str(exc)[:220]})
        except Exception as exc:
            result.update({"probe_status": "failed", "failure_reason": f"{type(exc).__name__}: {exc}"[:220]})
        out_rows.append(result)
    write_csv(OUT_CSV, out_rows)
    ok_count = sum(1 for row in out_rows if row.get("probe_status") == "ok")
    lines = [
        "# South Asia Source Probe v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        f"- Candidate sources probed: {len(out_rows)}",
        f"- Reachable sources: {ok_count}",
        "",
        "## Results",
        "",
    ]
    for row in out_rows:
        lines.append(f"- {row['source_name']}: {row['probe_status']} {row['http_status']} {row['final_url'] or row['url']}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUT_CSV.relative_to(ROOT)}: {len(out_rows)} rows, ok={ok_count}")
    print(f"{REPORT.relative_to(ROOT)}: report written")


if __name__ == "__main__":
    main()
