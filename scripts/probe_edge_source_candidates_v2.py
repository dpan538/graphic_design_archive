#!/usr/bin/env python3
"""Probe a broader edge-source candidate set for archive expansion.

The v2 probe widens beyond the first independent Asia list into local
libraries, community archives, design associations, university repositories,
film/poster archives, and post-1990 independent design-history sources. It
records source feasibility only; it does not promote public surfaces.
"""

from __future__ import annotations

import csv
import html
import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "source_probe_edge_v2_raw"
OUT_CSV = DATA / "source_probe_edge_v2.csv"
REPORT = ROOT / "docs" / "capture" / "EDGE_SOURCE_PROBE_v2.md"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 edge-source-probe-v2"
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
    capture_intent: str
    notes: str


CANDIDATES: tuple[Candidate, ...] = (
    Candidate("ESV201", "M+ Collections", "East Asia", "Hong Kong", "museum/archive", "postwar-present", "https://www.mplus.org.hk/en/collection/", "Hong Kong and Asian design/object/archive records", "Corrected collection URL after previous archive URL returned 404."),
    Candidate("ESV202", "Hong Kong Film Archive", "East Asia", "Hong Kong", "government film archive", "pre-WWII-present", "https://www.filmarchive.gov.hk/", "poster, publicity, film-title graphic evidence", "Useful for film poster and publicity design."),
    Candidate("ESV203", "Hong Kong Heritage Project", "East Asia", "Hong Kong", "community/history archive", "modern-present", "https://www.hongkongheritage.org/", "Hong Kong social and corporate visual culture context", "Context source; image use requires review."),
    Candidate("ESV204", "Taiwan Cultural Memory Bank", "East Asia", "Taiwan", "government/community memory archive", "pre-WWII-present", "https://tcmb.culture.tw/", "Taiwan visual culture, posters, ephemera, publication records", "Alternate endpoint for memory.culture.tw."),
    Candidate("ESV205", "Taiwan Design Research Institute", "East Asia", "Taiwan", "government/design institution", "post-1990-present", "https://www.tdri.org.tw/", "Taiwan design institution and exhibition context", "Institutional context; not open-image by default."),
    Candidate("ESV206", "Taiwan Film and Audiovisual Institute", "East Asia", "Taiwan", "government film archive", "pre-WWII-present", "https://www.tfai.org.tw/", "Taiwan film poster and publicity design records", "Good poster pathway if collections expose records."),
    Candidate("ESV207", "National Taiwan Museum of Fine Arts", "East Asia", "Taiwan", "museum", "modern-present", "https://www.ntmofa.gov.tw/", "Taiwan modern art/design exhibition and poster context", "Museum source; item rights vary."),
    Candidate("ESV208", "Ginza Graphic Gallery", "East Asia", "Japan", "design gallery/institution", "1986-present", "https://www.dnpfcp.jp/gallery/ggg/", "Japanese graphic design exhibitions and designer context", "Corrected URL; link-first."),
    Candidate("ESV209", "Kyoto ddd gallery", "East Asia", "Japan", "design gallery/institution", "1991-present", "https://www.dnpfcp.jp/gallery/ddd/", "Japanese/Kansai graphic design exhibition context", "Corrected URL; link-first."),
    Candidate("ESV210", "Center for Contemporary Graphic Art", "East Asia", "Japan", "design gallery/archive", "modern-present", "https://www.dnpfcp.jp/gallery/ccga/", "Japanese graphic art/poster exhibition context", "DNP family; image rights restricted."),
    Candidate("ESV211", "Printing Museum Tokyo", "East Asia", "Japan", "museum/library", "pre-modern-present", "https://www.printing-museum.org/", "printing, typography, book, poster history context", "Important for printing-history bridge."),
    Candidate("ESV212", "Tokyo TDC", "East Asia", "Japan", "professional design organization", "1987-present", "https://tokyotypedirectorsclub.org/", "typography and type-direction source context", "Professional/award source; image rights restricted."),
    Candidate("ESV213", "Tokyo ADC", "East Asia", "Japan", "professional design organization", "1952-present", "https://www.tokyoadc.com/", "Japanese advertising and graphic award context", "Professional organization; link-first."),
    Candidate("ESV214", "Nippon Design Center", "East Asia", "Japan", "design institution/studio", "1959-present", "https://www.ndc.co.jp/", "Japanese postwar corporate/design institution context", "Corporate source; link-first."),
    Candidate("ESV215", "Seoul Design Foundation", "East Asia", "Korea", "municipal design institution", "post-2000-present", "https://www.seouldesign.or.kr/", "Seoul design archive and public-design context", "May route to DDP/Seoul design archive."),
    Candidate("ESV216", "DDP Seoul", "East Asia", "Korea", "design museum/institution", "post-2000-present", "https://www.ddp.or.kr/", "Korean contemporary design exhibition context", "Institutional source; image review required."),
    Candidate("ESV217", "Design Korea", "East Asia", "Korea", "government/professional design portal", "post-2000-present", "https://dkfestival.or.kr/", "Korean design festival and award context", "Event/source context."),
    Candidate("ESV218", "MMCA Korea", "East Asia", "Korea", "national museum", "modern-present", "https://www.mmca.go.kr/", "Korean modern visual culture and exhibition context", "Museum source; item rights vary."),
    Candidate("ESV219", "Seoul Museum of History", "East Asia", "Korea", "municipal museum/archive", "modern-present", "https://museum.seoul.go.kr/", "Seoul public culture, posters, urban graphic evidence", "Previously had SSL issue; retry in v2."),
    Candidate("ESV220", "National Library of Korea", "East Asia", "Korea", "national library", "pre-WWII-present", "https://www.nl.go.kr/", "Korean publication, poster, advertising bibliography", "Bibliographic/context source."),
    Candidate("ESV221", "DesignSingapore Council", "Southeast Asia", "Singapore", "government design institution", "2003-present", "https://designsingapore.org/", "Singapore design policy, awards, exhibition context", "Institutional source; link-first."),
    Candidate("ESV222", "BiblioAsia", "Southeast Asia", "Singapore", "national library publication", "pre-WWII-present", "https://biblioasia.nlb.gov.sg/", "Singapore design/print history essays and bibliographic context", "Good text enrichment source."),
    Candidate("ESV223", "Roots.sg", "Southeast Asia", "Singapore", "government cultural portal", "pre-WWII-present", "https://www.roots.gov.sg/", "Singapore heritage collection and public visual culture", "Already useful; v2 checks source breadth."),
    Candidate("ESV224", "National Gallery Singapore Collection", "Southeast Asia", "Singapore", "museum collection", "modern-present", "https://www.nationalgallery.sg/", "Singapore and Southeast Asian modern visual culture context", "Museum source; rights vary."),
    Candidate("ESV225", "Asian Film Archive", "Southeast Asia", "Singapore / regional", "community/institutional archive", "postwar-present", "https://asianfilmarchive.org/", "film poster, title, publicity graphic source context", "Regional film-publicity source."),
    Candidate("ESV226", "VietGD", "Southeast Asia", "Vietnam", "independent design-history archive", "post-1990-present", "https://vietgd.com/", "Vietnamese graphic design history context", "Repeat source as P1 adapter candidate."),
    Candidate("ESV227", "Dogma Collection", "Southeast Asia", "Vietnam", "private poster collection", "1945-present", "https://www.dogmacollection.com/", "Vietnamese propaganda poster source context", "Private collection; link-first."),
    Candidate("ESV228", "Vietnam National Museum of History", "Southeast Asia", "Vietnam", "national museum", "pre-WWII-present", "https://baotanglichsu.vn/", "Vietnamese print, poster, visual culture context", "Museum/context source."),
    Candidate("ESV229", "Bophana Audiovisual Resource Center", "Southeast Asia", "Cambodia", "community archive", "postwar-present", "https://bophana.org/", "Cambodia audiovisual/poster/publicity context", "Underrepresented regional archive."),
    Candidate("ESV230", "Cambodia National Library", "Southeast Asia", "Cambodia", "national library", "pre-WWII-present", "https://www.nationallibraryofcambodia.org/", "Cambodian print and publication context", "May be sparse; source registry first."),
    Candidate("ESV231", "Lao National Library", "Southeast Asia", "Laos", "national library", "pre-WWII-present", "https://www.nationallibrary.gov.la/", "Lao print and publication context", "Underrepresented; likely manual/source registry."),
    Candidate("ESV232", "Thai Film Archive", "Southeast Asia", "Thailand", "government film archive", "postwar-present", "https://www.fapot.or.th/", "Thai poster/publicity graphic records", "Film poster route."),
    Candidate("ESV233", "Museum Siam", "Southeast Asia", "Thailand", "museum", "modern-present", "https://www.museumsiam.org/", "Thai exhibition, public visual culture, typography context", "Museum/context source."),
    Candidate("ESV234", "Fine Arts Department Thailand", "Southeast Asia", "Thailand", "government cultural agency", "pre-WWII-present", "https://www.finearts.go.th/", "Thai cultural/print-history context", "Government source; link-first."),
    Candidate("ESV235", "Design Center Philippines", "Southeast Asia", "Philippines", "government design institution", "1973-present", "https://designcenter.gov.ph/", "Philippine design institution and contemporary design context", "Institutional source."),
    Candidate("ESV236", "Cultural Center of the Philippines", "Southeast Asia", "Philippines", "government cultural institution", "1969-present", "https://culturalcenter.gov.ph/", "Philippine poster, publication, exhibition context", "Event/publication source."),
    Candidate("ESV237", "Lopez Museum and Library", "Southeast Asia", "Philippines", "private museum/library", "pre-WWII-present", "https://www.lopezmuseum.org.ph/", "Philippine print and visual culture context", "Private museum; rights review required."),
    Candidate("ESV238", "Grafis Nusantara", "Southeast Asia", "Indonesia", "community graphic archive", "1970s-1990s", "https://grafisnusantara.com/", "Indonesian labels, stickers, packaging, print ephemera", "Repeat source as high-priority adapter candidate."),
    Candidate("ESV239", "Desain Grafis Indonesia", "Southeast Asia", "Indonesia", "independent design-history publication", "post-1990-present", "https://dgi.or.id/", "Indonesian design-history text and source context", "Text enrichment/source registry."),
    Candidate("ESV240", "Indonesian Visual Art Archive", "Southeast Asia", "Indonesia", "community visual archive", "postwar-present", "https://archive.ivaa-online.org/", "Indonesian visual archive item/context records", "Alternative IVAA endpoint."),
    Candidate("ESV241", "National Library of Indonesia", "Southeast Asia", "Indonesia", "national library", "pre-WWII-present", "https://www.perpusnas.go.id/", "Indonesian publication and print context", "Government library; source registry."),
    Candidate("ESV242", "Malaysia Design Archive", "Southeast Asia", "Malaysia", "community design archive", "pre-WWII-present", "https://search.malaysiadesignarchive.org/", "Malaysian design item records", "Already captured; keep as adapter source."),
    Candidate("ESV243", "Pusat Dokumentasi Seni Malaysia", "Southeast Asia", "Malaysia", "arts documentation archive", "modern-present", "https://myartsarchive.org/", "Malaysian arts/design documentation context", "Community/archive source."),
    Candidate("ESV244", "Another Graphic", "Global", "post-1990 international", "independent curated design archive", "1990-2026", "https://anothergraphic.org/", "post-1990 independent design link layer", "Repeat source for contemporary independent context."),
    Candidate("ESV245", "Fonts In Use", "Global", "global", "typography database", "historical-present", "https://fontsinuse.com/", "type-in-use relation source", "High relevance but rights-sensitive."),
    Candidate("ESV246", "People's Graphic Design Archive", "Global", "global/community", "community design archive", "historical-present", "https://peoplesgdarchive.org/", "community-uploaded design source records", "Noncanonical source; rights review required."),
    Candidate("ESV247", "Letterform Archive", "North America", "United States / global", "specialist typography archive", "modern-present", "https://letterformarchive.org/", "typography/design archive context", "Authority/source context."),
    Candidate("ESV248", "Design Reviewed", "Europe", "United Kingdom / global", "independent design archive", "modern-present", "https://www.designreviewed.com/", "independent design archive context", "Rights-sensitive independent source."),
    Candidate("ESV249", "Digital Archive of Graphic Design", "Europe", "United Kingdom / global", "design-history archive", "modern-present", "https://digitalarchiveofgraphicdesign.org/", "graphic design archive records/context", "Probe route; may be educational/source registry."),
    Candidate("ESV250", "AIGA Design Archives", "North America", "United States", "professional design archive", "modern-present", "https://designarchives.aiga.org/", "professional design award/source records", "High relevance; rights sensitive."),
    Candidate("ESV251", "Mexican Design Archive", "Latin America", "Mexico", "independent/community archive", "modern-present", "https://www.archivomexicanodediseno.com/", "Mexican design archive/source context", "Underrepresented regional source if reachable."),
    Candidate("ESV252", "Archivo de la Grafica Chilena", "Latin America", "Chile", "community graphic archive", "modern-present", "https://www.instagram.com/archivograficachilena/", "Chilean graphic archive discovery source", "Social platform only discovery; original linked sources needed."),
    Candidate("ESV253", "Memoria Chilena", "Latin America", "Chile", "national library portal", "pre-WWII-present", "https://www.memoriachilena.gob.cl/", "Chilean posters, periodicals, political print context", "High-value source; item rights vary."),
    Candidate("ESV254", "Fundacion IDA", "Latin America", "Argentina", "design research/archive foundation", "modern-present", "https://www.fundacionida.org/", "Argentine design archive/context", "Already probed; high-value regional source."),
    Candidate("ESV255", "Arquivo Nacional Brasil", "Latin America", "Brazil", "national archive", "pre-WWII-present", "https://www.gov.br/arquivonacional/", "Brazilian public records and print context", "Government source; link-first."),
    Candidate("ESV256", "Biblioteca Nacional Digital Brasil", "Latin America", "Brazil", "national library digital portal", "pre-WWII-present", "https://bndigital.bn.gov.br/", "Brazilian periodical, poster, advertising print context", "High-value source."),
    Candidate("ESV257", "African Activist Archive", "Africa", "Pan-African / United States", "community archive", "modern-present", "https://africanactivist.msu.edu/", "anti-apartheid and liberation movement graphics", "Community source; rights review."),
    Candidate("ESV258", "South African History Archive", "Africa", "South Africa", "community archive", "modern-present", "https://www.saha.org.za/", "anti-apartheid posters and movement ephemera", "High-value non-mainstream source."),
    Candidate("ESV259", "UWC Robben Island Mayibuye Archives", "Africa", "South Africa", "university archive", "modern-present", "https://mayibuyearchives.org/", "South African resistance graphic/context records", "Alternate endpoint for Mayibuye."),
    Candidate("ESV260", "Arab Image Foundation", "Middle East", "Lebanon / regional", "community archive", "modern-present", "https://arabimagefoundation.org/", "Arab visual culture and print context", "Community image archive; rights review."),
    Candidate("ESV261", "Palestinian Museum Digital Archive", "Middle East", "Palestine", "community/museum archive", "modern-present", "https://palarchive.org/", "Palestinian posters, ephemera, visual culture", "High-value but rate/protocol sensitive."),
    Candidate("ESV262", "National Library and Archives of Iran", "Middle East", "Iran", "national library/archive", "pre-WWII-present", "https://www.nlai.ir/", "Iranian print, poster, publication context", "Government source."),
    Candidate("ESV263", "Ukrainian Liberation Movement Archive", "Eastern Europe", "Ukraine", "community archive", "modern-present", "https://avr.org.ua/", "Ukrainian political print and underground graphic records", "Community source; rights review."),
    Candidate("ESV264", "Kramerius Registry", "Eastern Europe", "Czechia / Slovakia", "protocol family registry", "pre-WWII-present", "https://registr.digitalniknihovna.cz/", "Kramerius source-family discovery", "Protocol-family expansion target."),
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
    with urllib.request.urlopen(req, timeout=24, context=context) as response:
        return response.status, response.geturl(), response.headers.get("content-type", ""), response.read(180_000)


def write_raw(candidate_id: str, body: bytes, suffix: str = "html") -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{candidate_id}.{suffix}.txt"
    path.write_text(redact_secrets(body.decode("utf-8", errors="replace")), encoding="utf-8")
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
    if not description:
        m = re.search(r'(?is)<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', body)
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
        ("ArchiveSpace/EAD", ("archivesspace", "<ead", "eadid", "finding aid")),
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
    if "Instagram" in candidate.url or "instagram.com" in candidate.url:
        return "IMG00_discovery_only_no_platform_image", "high"
    if "independent" in candidate.source_class or "community" in candidate.source_class or "private" in candidate.source_class:
        return "IMG02_source_hosted_or_IMG00_until_item_rights", "high"
    if "IIIF" in protocols or "CONTENTdm" in protocols:
        return "IMG02_source_viewer_or_IIIF_after_record_review", "medium"
    return "IMG00_or_IMG02_after_source_terms", "medium"


def capture_priority(candidate: Candidate, protocols: str, status: str) -> str:
    if status != "ok":
        return "P4_hold_or_manual"
    underrepresented = {"Vietnam", "Laos", "Cambodia", "Thailand", "Indonesia", "Malaysia", "Philippines", "Singapore", "Korea", "Taiwan", "Hong Kong", "Chile", "Brazil", "South Africa", "Palestine", "Iran"}
    if candidate.country_or_region in underrepresented or any(place in candidate.country_or_region for place in underrepresented):
        return "P1_underrepresented_region"
    if any(proto in protocols for proto in ("WordPress", "IIIF", "CONTENTdm", "Omeka", "DSpace", "preloaded-state", "Next/static JS")):
        return "P1_adapter_candidate"
    return "P2_source_registry_then_adapter"


def probe(candidate: Candidate) -> dict[str, str]:
    try:
        status, final_url, content_type, body = fetch(candidate.url)
        raw_path = write_raw(candidate.candidate_id, body)
        decoded = body.decode("utf-8", errors="replace")
        decoded = redact_secrets(decoded)
        title, description = title_and_description(decoded)
        protocols, evidence = detect_protocols(decoded, content_type, final_url)
        recommended_image_policy, rights_risk = image_policy(candidate, protocols)
        probe_status = "ok"
        failure_reason = ""
    except urllib.error.HTTPError as exc:
        status = exc.code
        final_url = candidate.url
        content_type = ""
        body = b""
        raw_path = ""
        title = ""
        description = ""
        protocols = ""
        evidence = ""
        recommended_image_policy, rights_risk = "IMG00_until_endpoint_verified", "high"
        probe_status = "http_error"
        failure_reason = f"HTTP {exc.code}: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 - probe report must preserve failures.
        status = 0
        final_url = ""
        content_type = ""
        body = b""
        raw_path = ""
        title = ""
        description = ""
        protocols = ""
        evidence = ""
        recommended_image_policy, rights_risk = "IMG00_until_endpoint_verified", "high"
        probe_status = "failed"
        failure_reason = f"{type(exc).__name__}: {exc}"
    return {
        "candidate_id": candidate.candidate_id,
        "source_name": candidate.source_name,
        "macro_region": candidate.macro_region,
        "country_or_region": candidate.country_or_region,
        "source_class": candidate.source_class,
        "period_intent": candidate.period_intent,
        "url": candidate.url,
        "http_status": str(status) if status else "",
        "final_url": final_url,
        "content_type": content_type,
        "response_bytes": str(len(body)) if body else "",
        "page_title": title,
        "meta_description": description,
        "detected_protocols": protocols,
        "protocol_evidence": evidence,
        "capture_priority": capture_priority(candidate, protocols, probe_status),
        "capture_intent": candidate.capture_intent,
        "recommended_image_policy": recommended_image_policy,
        "recommended_text_policy": "extract_source_text_or_context; no AI-generated evidence",
        "rights_risk": rights_risk,
        "probe_status": probe_status,
        "failure_reason": failure_reason,
        "raw_probe_path": raw_path,
        "access_date": ACCESS_DATE,
        "notes": candidate.notes,
    }


def write_csv(rows: Iterable[dict[str, str]]) -> None:
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def write_report(rows: list[dict[str, str]]) -> None:
    ok = [row for row in rows if row["probe_status"] == "ok"]
    p1 = [row for row in ok if row["capture_priority"].startswith("P1")]
    regions: dict[str, int] = {}
    protocols: dict[str, int] = {}
    for row in ok:
        regions[row["macro_region"]] = regions.get(row["macro_region"], 0) + 1
        for proto in row["detected_protocols"].split(";"):
            if proto:
                protocols[proto] = protocols.get(proto, 0) + 1
    lines = [
        "# Edge Source Probe v2",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This probe expands the candidate source pool beyond large museum APIs, prioritising local, community, university, professional, and government sources. It does not promote records into the public archive.",
        "",
        "## Guardrails",
        "",
        "- Raw payloads are secret-redacted before writing.",
        "- Social platforms are discovery-only and default to `IMG00`; they are not evidence sources.",
        "- Independent/community/private sources default to source-hosted or link-only image states.",
        "- P1 means adapter/source-registry priority, not automatic publication.",
        "",
        "## Summary",
        "",
        f"- Candidates: {len(rows)}",
        f"- Reachable: {len(ok)}",
        f"- P1 candidates: {len(p1)}",
        f"- Macro-region counts: {', '.join(f'{k}={v}' for k, v in sorted(regions.items()))}",
        f"- Protocol hints: {', '.join(f'{k}={v}' for k, v in sorted(protocols.items())) or 'none'}",
        "",
        "## P1 Candidates",
        "",
        "| ID | Source | Region | Country | Protocols | Image policy |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in p1:
        lines.append(
            f"| {row['candidate_id']} | {row['source_name']} | {row['macro_region']} | "
            f"{row['country_or_region']} | {row['detected_protocols'] or 'HTML'} | "
            f"{row['recommended_image_policy']} |"
        )
    failed = [row for row in rows if row["probe_status"] != "ok"]
    lines.extend(["", "## Failed / Manual Follow-Up", ""])
    for row in failed:
        lines.append(f"- {row['candidate_id']} {row['source_name']}: {row['failure_reason']}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
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
