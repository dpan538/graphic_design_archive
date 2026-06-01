#!/usr/bin/env python3
"""Probe independent and Asia/SEA graphic-design source candidates.

This is a source-discovery pass, not a public-record ingest. It records which
sites are reachable, which protocol family they resemble, and how conservatively
their images should be treated. Pinterest/Instagram-style platforms are only
allowed as discovery paths; the promoted source must be the original archive,
studio, library, university, government, or community site.
"""

from __future__ import annotations

import csv
import html
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "source_probe_independent_asia_v1_raw"
OUT_CSV = DATA / "source_probe_independent_asia_v1.csv"
REPORT = ROOT / "docs" / "capture" / "INDEPENDENT_ASIA_SOURCE_PROBE_v1.md"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 independent-asia-source-probe"
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"(?i)(key=)[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key[\"'\s:=]+)[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    source_name: str
    macro_region: str
    country_or_region: str
    source_class: str
    period_intent: str
    url: str
    discovery_channel: str
    capture_intent: str
    notes: str


CANDIDATES: tuple[Candidate, ...] = (
    Candidate("IAS001", "Another Graphic", "Global", "post-1990 international", "independent curated design archive", "1990-2026", "https://anothergraphic.org/", "independent design archive; social-platform-adjacent discovery", "contemporary context and object-link records", "WordPress REST is available; image rights remain with designers/sources."),
    Candidate("IAS002", "East Asian Graphics Archive", "East Asia", "East Asia", "independent curated design archive", "postwar-present", "https://eastasiangraphicsarchive.com/", "independent design archive", "source registry and selected context records", "Framer site; likely JS/static scrape rather than clean API."),
    Candidate("IAS003", "Grafis Nusantara", "Southeast Asia", "Indonesia", "independent/community graphic archive", "pre-WWII-present", "https://grafisnusantara.com/", "regional graphic archive", "Indonesian graphic history source records", "Potential WordPress family; image rights need source-level caution."),
    Candidate("IAS004", "Malaysia Design Archive", "Southeast Asia", "Malaysia", "community design archive", "pre-WWII-present", "https://search.malaysiadesignarchive.org/", "regional design archive", "Malaysian design record source", "Search interface likely custom/WordPress; treat images as source-hosted."),
    Candidate("IAS005", "Singapore Graphic Archives", "Southeast Asia", "Singapore", "independent/community design archive", "pre-WWII-present", "https://graphic.sg/resources/databases-archives", "regional design archive", "Singapore graphic source registry and citation layer", "Founded as Singapore Visual Archive; likely source-guide plus records."),
    Candidate("IAS006", "Thaipography Archive", "Southeast Asia", "Thailand", "independent typography archive", "post-1990-present", "https://thaipography-archive.com/", "regional typography archive", "Thai typography and contemporary design context", "Next/static site with CDN images; no open image assumption."),
    Candidate("IAS007", "Thai Poster Archive", "Southeast Asia", "Thailand", "independent poster archive", "pre-WWII-present", "https://thaiposterarchive.com/", "regional poster archive", "Thai poster source registry", "May use bot protection; link-first if inaccessible."),
    Candidate("IAS008", "TPaddassoc Graphics Archive", "East Asia", "Taiwan", "independent design association archive", "post-1990-present", "https://tpaddassoc.com/graphics-archive", "regional design archive", "Taiwan contemporary graphic source records", "Preloaded state appears in HTML; possible structured scrape."),
    Candidate("IAS009", "VietGD", "Southeast Asia", "Vietnam", "independent design-history archive", "post-1990-present", "https://vietgd.com/", "regional design-history archive", "Vietnamese graphic design source records", "Probe reachability before promotion."),
    Candidate("IAS010", "Design and Culture Lab / DNP Graphic Design Archives", "East Asia", "Japan", "institutional design archive", "postwar-present", "https://www.dnpfcp.jp/gallery/ddd/archives/", "Japanese design archive", "Japanese postwar exhibition/object context", "Institutional source; link-first; image rights likely restricted."),
    Candidate("IAS011", "Ginza Graphic Gallery Archives", "East Asia", "Japan", "institutional design gallery archive", "postwar-present", "https://www.dnpfcp.jp/gallery/ggg/archives/", "Japanese design gallery", "Japanese graphic exhibition and designer context", "High relevance; not open-image by default."),
    Candidate("IAS012", "JAGDA", "East Asia", "Japan", "professional association", "1978-present", "https://www.jagda.or.jp/", "professional design organization", "movement/institution source context", "Useful for authority/event context rather than object images."),
    Candidate("IAS013", "Seoul Design Archive", "East Asia", "Korea", "municipal/institutional design archive", "postwar-present", "https://seouldesignarchive.or.kr/", "regional design archive", "Korean modern/contemporary design records", "Probe for API/JSON endpoints."),
    Candidate("IAS014", "DesignDB / KIDP", "East Asia", "Korea", "government/professional design portal", "postwar-present", "https://www.designdb.com/", "professional design portal", "Korean design context/source registry", "Likely HTML; use as citation layer first."),
    Candidate("IAS015", "Korean Film Archive", "East Asia", "Korea", "government film archive", "pre-WWII-present", "https://www.koreafilm.or.kr/", "government archive", "film poster and publicity records", "Already in broad probe; included here for regional poster priority."),
    Candidate("IAS016", "M+ Collections and Archives", "East Asia", "Hong Kong", "museum/archive", "postwar-present", "https://www.mplus.org.hk/en/collection/archives/", "museum/archive", "Hong Kong and Asian design archive context", "High authority; image reuse restricted."),
    Candidate("IAS017", "Hong Kong Memory", "East Asia", "Hong Kong", "government/community memory archive", "pre-WWII-present", "https://www.hkmemory.hk/", "local memory archive", "Hong Kong print, advertising, public culture", "Metadata and images require item review."),
    Candidate("IAS018", "Shanghai Library", "East Asia", "China", "municipal library", "pre-WWII-present", "https://www.library.sh.cn/", "local library archive", "Shanghai print/commercial design source context", "Already probed generally; needs item-level pathway."),
    Candidate("IAS019", "National Cultural Memory Bank Taiwan", "East Asia", "Taiwan", "government/community memory archive", "pre-WWII-present", "https://memory.culture.tw/", "national memory archive", "Taiwan visual culture and public graphic records", "Good non-museum voice; item rights vary."),
    Candidate("IAS020", "National Archives of Singapore", "Southeast Asia", "Singapore", "government archive", "pre-WWII-present", "https://www.nas.gov.sg/archivesonline/", "government archive", "Singapore public information, posters, campaign graphics", "Viewer and reproduction permissions differ."),
    Candidate("IAS021", "NewspaperSG", "Southeast Asia", "Singapore", "national library newspaper archive", "pre-WWII-present", "https://eresources.nlb.gov.sg/newspapers/", "newspaper archive", "advertising/layout/OCR source", "Search/OCR source; images link-first."),
    Candidate("IAS022", "BookSG / Print Heritage", "Southeast Asia", "Singapore", "national library digital collection", "pre-WWII-present", "https://eresources.nlb.gov.sg/printheritage/", "digital print collection", "Singapore book, ephemera, print culture", "May return 202 challenge; record as source family."),
    Candidate("IAS023", "National Library of Vietnam", "Southeast Asia", "Vietnam", "national library", "pre-WWII-present", "https://nlv.gov.vn/", "government library", "Vietnamese print and publication context", "Likely HTML/catalogue; link-first."),
    Candidate("IAS024", "Vietnam National Archives", "Southeast Asia", "Vietnam", "national archive", "pre-WWII-present", "https://luutru.gov.vn/", "government archive", "Vietnamese posters, notices, periodicals context", "Likely HTML; source registry first."),
    Candidate("IAS025", "Digital Library of Lao Manuscripts", "Southeast Asia", "Laos", "library/cultural heritage", "pre-WWII-present", "https://www.laomanuscripts.net/", "cultural heritage archive", "Lao writing/print precursor and visual culture context", "Not pure graphic design; use sparingly as historical context."),
    Candidate("IAS026", "National Library of the Philippines", "Southeast Asia", "Philippines", "national library", "pre-WWII-present", "https://web.nlp.gov.ph/", "government library", "Philippine print/poster/publication context", "Probe access; likely manual/search source."),
    Candidate("IAS027", "Ateneo Rizal Library Digital Archives", "Southeast Asia", "Philippines", "university archive", "pre-WWII-present", "https://rizal.library.ateneo.edu/", "university archive", "Philippine periodical and print culture source", "Already reachable; good university/local source."),
    Candidate("IAS028", "Khastara Perpusnas Indonesia", "Southeast Asia", "Indonesia", "national library digital collection", "pre-WWII-present", "https://khastara.perpusnas.go.id/", "government library", "Indonesian publications and visual culture", "Likely HTML; source registry and selected records."),
    Candidate("IAS029", "IVAA Indonesian Visual Art Archive", "Southeast Asia", "Indonesia", "community art archive", "postwar-present", "https://ivaa-online.org/", "community visual archive", "Indonesian design/art print context", "Community archive; rights review required."),
    Candidate("IAS030", "ANRI Arsip Nasional Republik Indonesia", "Southeast Asia", "Indonesia", "national archive", "pre-WWII-present", "https://anri.go.id/", "government archive", "Indonesian public visual records", "Already reachable; likely source registry first."),
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
    "discovery_channel",
    "probe_status",
    "failure_reason",
    "raw_probe_path",
    "access_date",
    "notes",
]


def clean(value: object, max_chars: int = 600) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def redact_secrets(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED_SECRET]", redacted)
    return redacted


def fetch(url: str) -> tuple[int, str, str, bytes]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json,application/xml,*/*"},
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=25, context=context) as response:
        return response.status, response.geturl(), response.headers.get("content-type", ""), response.read(180_000)


def write_raw(candidate_id: str, body: bytes, suffix: str = "html") -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{candidate_id}.{suffix}.txt"
    text = body.decode("utf-8", errors="replace")
    path.write_text(redact_secrets(text), encoding="utf-8")
    return str(path.relative_to(ROOT))


def title_and_description(body: str) -> tuple[str, str]:
    title = ""
    description = ""
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
    if m:
        title = clean(re.sub(r"<[^>]+>", " ", m.group(1)), 220)
    m = re.search(r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', body)
    if m:
        description = clean(m.group(1), 360)
    return title, description


def detect_protocols(body: str, content_type: str, url: str) -> tuple[str, str]:
    low = (body + " " + content_type + " " + url).lower()
    protocols: list[str] = []
    evidence: list[str] = []
    checks: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("WordPress REST/RSS", ("wp-json", "wp-content", "application/rss+xml")),
        ("IIIF", ("iiif", "manifest.json", "presentation/")),
        ("CONTENTdm", ("contentdm", "/digital/api/")),
        ("Omeka", ("omeka", "/api/items")),
        ("DSpace", ("dspace", "/server/api", "oai/request")),
        ("JSON-LD", ("application/ld+json", "schema.org")),
        ("Framer/static JS", ("framer.com", "__framer")),
        ("Next/static JS", ("__next_data__", "/_next/static")),
        ("preloaded-state", ("__preloaded_state__", "window.__preloaded_state__")),
        ("PDF", (".pdf", "application/pdf")),
        ("RSS/Atom", ("application/rss+xml", "application/atom+xml", "/feed/")),
    )
    for label, needles in checks:
        hit = next((needle for needle in needles if needle in low), "")
        if hit:
            protocols.append(label)
            evidence.append(f"{label}:{hit}")
    return ";".join(protocols), ";".join(evidence)


def image_policy(candidate: Candidate, protocols: str) -> tuple[str, str]:
    if candidate.source_class.startswith("independent") or "community" in candidate.source_class:
        return "IMG02_source_hosted_or_IMG00_until_item_rights", "high"
    if "IIIF" in protocols or "CONTENTdm" in protocols:
        return "IMG02_source_viewer_or_IIIF_after_record_review", "medium"
    return "IMG00_or_IMG02_after_source_terms", "medium"


def capture_priority(candidate: Candidate, protocols: str, status: str) -> str:
    if status != "ok":
        return "P4_hold_or_manual"
    if candidate.country_or_region in {"Vietnam", "Laos", "Thailand", "Indonesia", "Malaysia", "Philippines", "Singapore", "Korea", "Taiwan"}:
        return "P1_underrepresented_region"
    if "WordPress" in protocols or "preloaded-state" in protocols:
        return "P1_adapter_candidate"
    return "P2_source_registry_then_adapter"


def probe(candidate: Candidate) -> dict[str, str]:
    try:
        status, final_url, content_type, body = fetch(candidate.url)
        raw_path = write_raw(candidate.candidate_id, body)
        decoded = body.decode("utf-8", errors="replace")
        title, description = title_and_description(decoded)
        protocols, evidence = detect_protocols(decoded, content_type, final_url)
        recommended_image_policy, rights_risk = image_policy(candidate, protocols)
        return {
            "candidate_id": candidate.candidate_id,
            "source_name": candidate.source_name,
            "macro_region": candidate.macro_region,
            "country_or_region": candidate.country_or_region,
            "source_class": candidate.source_class,
            "period_intent": candidate.period_intent,
            "url": candidate.url,
            "http_status": str(status),
            "final_url": final_url,
            "content_type": content_type,
            "response_bytes": str(len(body)),
            "page_title": title,
            "meta_description": description,
            "detected_protocols": protocols,
            "protocol_evidence": evidence,
            "capture_priority": capture_priority(candidate, protocols, "ok"),
            "capture_intent": candidate.capture_intent,
            "recommended_image_policy": recommended_image_policy,
            "recommended_text_policy": "extract_about_context_and_item_metadata; no AI-generated evidence",
            "rights_risk": rights_risk,
            "discovery_channel": candidate.discovery_channel,
            "probe_status": "ok",
            "failure_reason": "",
            "raw_probe_path": raw_path,
            "access_date": ACCESS_DATE,
            "notes": candidate.notes,
        }
    except urllib.error.HTTPError as exc:
        return failed_row(candidate, "http_error", f"HTTP {exc.code}: {exc.reason}")
    except Exception as exc:  # noqa: BLE001 - probe report must preserve failures.
        return failed_row(candidate, "failed", f"{type(exc).__name__}: {exc}")


def failed_row(candidate: Candidate, status: str, reason: str) -> dict[str, str]:
    row = {
        "candidate_id": candidate.candidate_id,
        "source_name": candidate.source_name,
        "macro_region": candidate.macro_region,
        "country_or_region": candidate.country_or_region,
        "source_class": candidate.source_class,
        "period_intent": candidate.period_intent,
        "url": candidate.url,
        "http_status": "",
        "final_url": "",
        "content_type": "",
        "response_bytes": "",
        "page_title": "",
        "meta_description": "",
        "detected_protocols": "",
        "protocol_evidence": "",
        "capture_priority": capture_priority(candidate, "", status),
        "capture_intent": candidate.capture_intent,
        "recommended_image_policy": "IMG00_until_endpoint_verified",
        "recommended_text_policy": "manual_context_only",
        "rights_risk": "high",
        "discovery_channel": candidate.discovery_channel,
        "probe_status": status,
        "failure_reason": reason,
        "raw_probe_path": "",
        "access_date": ACCESS_DATE,
        "notes": candidate.notes,
    }
    return row


def write_csv(rows: Iterable[dict[str, str]]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def write_report(rows: list[dict[str, str]]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    ok = [row for row in rows if row["probe_status"] == "ok"]
    priority = [row for row in ok if row["capture_priority"].startswith("P1")]
    region_counts: dict[str, int] = {}
    for row in ok:
        region_counts[row["macro_region"]] = region_counts.get(row["macro_region"], 0) + 1
    lines = [
        "# Independent + Asia Source Probe v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This pass expands source breadth for post-1990 independent design archives and underrepresented East Asia / Southeast Asia sources. It is a source-discovery layer, not a claim that every site can be safely image-ingested.",
        "",
        "## Rules",
        "",
        "- Pinterest, Instagram, Behance, Are.na, and similar platforms may be used only to discover original sources.",
        "- Independent design sites after 1990 default to `IMG02` or `IMG00`; they do not create open-image claims.",
        "- Government, library, university, and community archives remain item-rights dependent.",
        "- Pre-WWII to present coverage is prioritized for China, Japan, Korea, Taiwan, Hong Kong, Singapore, Vietnam, Laos, Thailand, Indonesia, Malaysia, and the Philippines.",
        "",
        "## Probe Summary",
        "",
        f"- Candidates: {len(rows)}",
        f"- Reachable: {len(ok)}",
        f"- P1 next-capture candidates: {len(priority)}",
        f"- Macro-region counts: {', '.join(f'{k}={v}' for k, v in sorted(region_counts.items()))}",
        "",
        "## P1 Candidates",
        "",
        "| ID | Source | Region | Country | Protocols | Image policy |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in priority:
        lines.append(
            f"| {row['candidate_id']} | {row['source_name']} | {row['macro_region']} | "
            f"{row['country_or_region']} | {row['detected_protocols'] or 'HTML'} | "
            f"{row['recommended_image_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Next Capture Direction",
            "",
            "1. Use Another Graphic only for post-1990 contemporary context records and original-source routing.",
            "2. Build adapters for sources with explicit protocol signals: WordPress, preloaded-state, IIIF, CONTENTdm, Omeka, or government/library search endpoints.",
            "3. For China/Japan/Korea and Southeast Asia, prefer local libraries, national archives, university collections, and community archives over global museum aggregators.",
            "4. Do not promote image-heavy records from independent sites to `IMG03` unless item-level open licensing is explicit.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = [probe(candidate) for candidate in CANDIDATES]
    write_csv(rows)
    write_report(rows)
    ok = sum(1 for row in rows if row["probe_status"] == "ok")
    p1 = sum(1 for row in rows if row["capture_priority"].startswith("P1"))
    print(f"probed={len(rows)} reachable={ok} p1={p1}")
    print(f"wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
