#!/usr/bin/env python3
"""Build a 500-source success registry for undercovered regions.

This batch expands source coverage without adding public IMG04 surfaces. It
discovers official source sites through Wikidata, probes those official URLs,
and records only source-level metadata needed for later item/image capture.

No image binaries, screenshots, raw HTML, cookies, or source payloads are saved.
"""

from __future__ import annotations

import csv
import html
import json
import re
import ssl
import socket
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

OUTPUT = DATA / "nonmainstream_source_success_registry_2026_v1.csv"
SUMMARY = DATA / "nonmainstream_source_success_summary_2026_v1.csv"
REGION_BREAKDOWN = DATA / "nonmainstream_source_success_region_breakdown_2026_v1.csv"
REPORT = DOCS / "NONMAINSTREAM_SOURCE_SUCCESS_REGISTRY_2026_v1.md"

ACCESS_DATE = "2026-06-05"
TARGET_SUCCESS_COUNT = 500
MACRO_SELECTION_CAPS = {
    "Africa": 120,
    "Latin America / Caribbean": 120,
    "East Asia": 60,
    "MENA": 90,
    "South Asia": 80,
    "Southeast Asia": 80,
    "Central Asia": 70,
    "Eastern Europe / Caucasus": 70,
    "Oceania / Indigenous": 40,
}
MAX_PROBE_WORKERS = 18
PROBE_TIMEOUT = 8
PROBE_BYTES = 140_000
WIKIDATA_TIMEOUT = 18
MAX_CANDIDATE_PROBES = 2600
PROBE_STOP_SUCCESS_COUNT = 1000
PROBE_BATCH_SIZE = 250
USER_AGENT = "ModernGDHistory/0.1 source-success-registry"

SOURCE_CLASSES = {
    "Q33506": "museum",
    "Q7075": "library",
    "Q166118": "archive",
    "Q207694": "art museum",
    "Q1007870": "art gallery",
    "Q1329623": "cultural center",
}

COUNTRIES: list[tuple[str, str, str]] = [
    # Africa
    ("Q1033", "Nigeria", "Africa"), ("Q117", "Ghana", "Africa"), ("Q114", "Kenya", "Africa"),
    ("Q115", "Ethiopia", "Africa"), ("Q924", "Tanzania", "Africa"), ("Q1036", "Uganda", "Africa"),
    ("Q1037", "Rwanda", "Africa"), ("Q1041", "Senegal", "Africa"), ("Q1009", "Cameroon", "Africa"),
    ("Q962", "Benin", "Africa"), ("Q945", "Togo", "Africa"), ("Q1008", "Cote d'Ivoire", "Africa"),
    ("Q965", "Burkina Faso", "Africa"), ("Q912", "Mali", "Africa"), ("Q1032", "Niger", "Africa"),
    ("Q657", "Chad", "Africa"), ("Q1049", "Sudan", "Africa"), ("Q958", "South Sudan", "Africa"),
    ("Q916", "Angola", "Africa"), ("Q1029", "Mozambique", "Africa"), ("Q953", "Zambia", "Africa"),
    ("Q954", "Zimbabwe", "Africa"), ("Q1030", "Namibia", "Africa"), ("Q963", "Botswana", "Africa"),
    ("Q258", "South Africa", "Africa"), ("Q1028", "Morocco", "Africa"), ("Q262", "Algeria", "Africa"),
    ("Q948", "Tunisia", "Africa"), ("Q79", "Egypt", "Africa"), ("Q1019", "Madagascar", "Africa"),
    ("Q1027", "Mauritius", "Africa"), ("Q1011", "Cape Verde", "Africa"), ("Q974", "DR Congo", "Africa"),
    ("Q971", "Republic of the Congo", "Africa"), ("Q1000", "Gabon", "Africa"), ("Q1005", "The Gambia", "Africa"),
    ("Q1044", "Sierra Leone", "Africa"), ("Q1014", "Liberia", "Africa"), ("Q1006", "Guinea", "Africa"),
    ("Q1020", "Malawi", "Africa"), ("Q1013", "Lesotho", "Africa"), ("Q1050", "Eswatini", "Africa"),
    # Latin America / Caribbean
    ("Q96", "Mexico", "Latin America / Caribbean"), ("Q155", "Brazil", "Latin America / Caribbean"),
    ("Q414", "Argentina", "Latin America / Caribbean"), ("Q298", "Chile", "Latin America / Caribbean"),
    ("Q419", "Peru", "Latin America / Caribbean"), ("Q739", "Colombia", "Latin America / Caribbean"),
    ("Q717", "Venezuela", "Latin America / Caribbean"), ("Q736", "Ecuador", "Latin America / Caribbean"),
    ("Q750", "Bolivia", "Latin America / Caribbean"), ("Q733", "Paraguay", "Latin America / Caribbean"),
    ("Q77", "Uruguay", "Latin America / Caribbean"), ("Q774", "Guatemala", "Latin America / Caribbean"),
    ("Q783", "Honduras", "Latin America / Caribbean"), ("Q792", "El Salvador", "Latin America / Caribbean"),
    ("Q811", "Nicaragua", "Latin America / Caribbean"), ("Q800", "Costa Rica", "Latin America / Caribbean"),
    ("Q804", "Panama", "Latin America / Caribbean"), ("Q241", "Cuba", "Latin America / Caribbean"),
    ("Q786", "Dominican Republic", "Latin America / Caribbean"), ("Q790", "Haiti", "Latin America / Caribbean"),
    ("Q766", "Jamaica", "Latin America / Caribbean"), ("Q754", "Trinidad and Tobago", "Latin America / Caribbean"),
    ("Q244", "Barbados", "Latin America / Caribbean"), ("Q242", "Belize", "Latin America / Caribbean"),
    # South Asia
    ("Q668", "India", "South Asia"), ("Q843", "Pakistan", "South Asia"), ("Q902", "Bangladesh", "South Asia"),
    ("Q854", "Sri Lanka", "South Asia"), ("Q837", "Nepal", "South Asia"), ("Q917", "Bhutan", "South Asia"),
    ("Q826", "Maldives", "South Asia"), ("Q889", "Afghanistan", "South Asia"),
    # Southeast Asia
    ("Q252", "Indonesia", "Southeast Asia"), ("Q928", "Philippines", "Southeast Asia"),
    ("Q881", "Vietnam", "Southeast Asia"), ("Q869", "Thailand", "Southeast Asia"),
    ("Q833", "Malaysia", "Southeast Asia"), ("Q334", "Singapore", "Southeast Asia"),
    ("Q424", "Cambodia", "Southeast Asia"), ("Q819", "Laos", "Southeast Asia"),
    ("Q836", "Myanmar", "Southeast Asia"), ("Q921", "Brunei", "Southeast Asia"), ("Q574", "Timor-Leste", "Southeast Asia"),
    # MENA
    ("Q794", "Iran", "MENA"), ("Q796", "Iraq", "MENA"), ("Q858", "Syria", "MENA"),
    ("Q822", "Lebanon", "MENA"), ("Q810", "Jordan", "MENA"), ("Q219060", "Palestine", "MENA"),
    ("Q851", "Saudi Arabia", "MENA"), ("Q878", "United Arab Emirates", "MENA"), ("Q846", "Qatar", "MENA"),
    ("Q398", "Bahrain", "MENA"), ("Q842", "Oman", "MENA"), ("Q805", "Yemen", "MENA"),
    ("Q817", "Kuwait", "MENA"), ("Q43", "Turkey", "MENA"),
    # Eastern Europe / Caucasus
    ("Q212", "Ukraine", "Eastern Europe / Caucasus"), ("Q184", "Belarus", "Eastern Europe / Caucasus"),
    ("Q217", "Moldova", "Eastern Europe / Caucasus"), ("Q218", "Romania", "Eastern Europe / Caucasus"),
    ("Q219", "Bulgaria", "Eastern Europe / Caucasus"), ("Q403", "Serbia", "Eastern Europe / Caucasus"),
    ("Q225", "Bosnia and Herzegovina", "Eastern Europe / Caucasus"),
    ("Q221", "North Macedonia", "Eastern Europe / Caucasus"), ("Q222", "Albania", "Eastern Europe / Caucasus"),
    ("Q236", "Montenegro", "Eastern Europe / Caucasus"), ("Q1246", "Kosovo", "Eastern Europe / Caucasus"),
    ("Q230", "Georgia", "Eastern Europe / Caucasus"), ("Q399", "Armenia", "Eastern Europe / Caucasus"),
    ("Q227", "Azerbaijan", "Eastern Europe / Caucasus"),
    # Central Asia
    ("Q232", "Kazakhstan", "Central Asia"), ("Q265", "Uzbekistan", "Central Asia"),
    ("Q813", "Kyrgyzstan", "Central Asia"), ("Q863", "Tajikistan", "Central Asia"),
    ("Q874", "Turkmenistan", "Central Asia"), ("Q711", "Mongolia", "Central Asia"),
    # Oceania / Indigenous
    ("Q712", "Fiji", "Oceania / Indigenous"), ("Q683", "Samoa", "Oceania / Indigenous"),
    ("Q678", "Tonga", "Oceania / Indigenous"), ("Q686", "Vanuatu", "Oceania / Indigenous"),
    ("Q691", "Papua New Guinea", "Oceania / Indigenous"), ("Q685", "Solomon Islands", "Oceania / Indigenous"),
    ("Q26988", "Cook Islands", "Oceania / Indigenous"), ("Q33788", "New Caledonia", "Oceania / Indigenous"),
    ("Q710", "Kiribati", "Oceania / Indigenous"), ("Q672", "Tuvalu", "Oceania / Indigenous"),
    ("Q697", "Nauru", "Oceania / Indigenous"), ("Q709", "Marshall Islands", "Oceania / Indigenous"),
    ("Q702", "Micronesia", "Oceania / Indigenous"), ("Q695", "Palau", "Oceania / Indigenous"),
    # East Asia, limited undercovered institutional context
    ("Q865", "Taiwan", "East Asia"),
]

OUTPUT_FIELDS = [
    "source_success_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "country_qid",
    "source_class",
    "institutional_level",
    "url",
    "final_url",
    "http_status",
    "content_type",
    "response_bytes",
    "page_title",
    "meta_description",
    "detected_protocols",
    "protocol_evidence",
    "source_success_status",
    "capture_scope",
    "image_policy_next",
    "rights_policy_next",
    "next_item_capture_priority",
    "period_start",
    "period_end",
    "period_bands",
    "wikidata_qid",
    "wikidata_url",
    "access_date",
    "notes",
]

SUMMARY_FIELDS = ["metric", "value", "count", "notes"]
REGION_FIELDS = ["macro_region", "country_or_region", "successful_sources", "source_classes", "protocols"]


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {key.lower(): value or "" for key, value in attrs}
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


@dataclass(frozen=True)
class Candidate:
    source_name: str
    macro_region: str
    country_or_region: str
    country_qid: str
    source_class: str
    url: str
    wikidata_qid: str


def clean(value: Any, *, max_chars: int = 700) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def normalized_url(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    parsed = urllib.parse.urlsplit(value)
    path = parsed.path.rstrip("/") or parsed.path
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def qid_from_uri(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def existing_source_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if "cell_assignments" in path.name:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = clean(row.get("source_name")).lower()
                url = normalized_url(row.get("source_record_url") or row.get("source_api_url") or "")
                if name or url:
                    keys.add((name, url))
    for path in sorted(DATA.glob("nonmainstream_source_success_registry_*_v*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = clean(row.get("source_name")).lower()
                url = normalized_url(row.get("final_url") or row.get("url") or "")
                if name or url:
                    keys.add((name, url))
    return keys


def sparql_query(countries: list[tuple[str, str, str]]) -> str:
    country_values = "\n".join(
        f'(wd:{qid} "{country}" "{macro}")' for qid, country, macro in countries
    )
    class_values = " ".join(f"wd:{qid}" for qid in SOURCE_CLASSES)
    return f"""
SELECT DISTINCT ?item ?itemLabel ?country ?countryName ?macro ?website ?classLabel WHERE {{
  VALUES (?country ?countryName ?macro) {{
    {country_values}
  }}
  VALUES ?class {{ {class_values} }}
  ?item wdt:P17 ?country ;
        wdt:P856 ?website ;
        wdt:P31/wdt:P279* ?class .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,es,fr,pt,ar,ru,zh". }}
}}
LIMIT 800
""".strip()


def fetch_wikidata_chunk(countries: list[tuple[str, str, str]]) -> list[Candidate]:
    params = urllib.parse.urlencode({"query": sparql_query(countries), "format": "json"}).encode("utf-8")
    request = urllib.request.Request(
        "https://query.wikidata.org/sparql",
        data=params,
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=WIKIDATA_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))

    country_macro = {qid: (country, macro) for qid, country, macro in countries}
    out: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    for binding in payload.get("results", {}).get("bindings", []):
        item_uri = binding.get("item", {}).get("value", "")
        website = binding.get("website", {}).get("value", "")
        if not website.startswith(("http://", "https://")):
            continue
        country_qid = qid_from_uri(binding.get("country", {}).get("value", ""))
        fallback_country, fallback_macro = country_macro.get(country_qid, ("", ""))
        source_name = clean(binding.get("itemLabel", {}).get("value", ""))
        country = clean(binding.get("countryName", {}).get("value", "")) or fallback_country
        macro = clean(binding.get("macro", {}).get("value", "")) or fallback_macro
        source_class = clean(binding.get("classLabel", {}).get("value", "cultural source"))
        key = (source_name.lower(), normalized_url(website))
        if not source_name or not macro or key in seen:
            continue
        seen.add(key)
        out.append(
            Candidate(
                source_name=source_name,
                macro_region=macro,
                country_or_region=country,
                country_qid=country_qid,
                source_class=source_class,
                url=website,
                wikidata_qid=qid_from_uri(item_uri),
            )
        )
    return out


def fetch_wikidata_candidates() -> list[Candidate]:
    all_candidates: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    retry_countries: list[tuple[str, str, str]] = []
    chunks = [COUNTRIES[index : index + 8] for index in range(0, len(COUNTRIES), 8)]
    for index, chunk in enumerate(chunks, 1):
        try:
            rows = fetch_wikidata_chunk(chunk)
        except Exception as exc:
            countries = ", ".join(country for _, country, _ in chunk)
            print(f"wikidata_chunk={index}/{len(chunks)} skipped countries={countries} error={type(exc).__name__}", flush=True)
            retry_countries.extend(chunk)
            continue
        for candidate in rows:
            key = (candidate.source_name.lower(), normalized_url(candidate.url))
            if key in seen:
                continue
            seen.add(key)
            all_candidates.append(candidate)
        countries = ", ".join(country for _, country, _ in chunk)
        print(f"wikidata_chunk={index}/{len(chunks)} rows={len(rows)} total_candidates={len(all_candidates)} countries={countries}", flush=True)
        time.sleep(0.2)

    if retry_countries:
        print(f"wikidata_single_country_retries={len(retry_countries)}", flush=True)
    for retry_index, country_row in enumerate(retry_countries, 1):
        try:
            rows = fetch_wikidata_chunk([country_row])
        except Exception as exc:
            print(f"wikidata_retry={retry_index}/{len(retry_countries)} skipped country={country_row[1]} error={type(exc).__name__}", flush=True)
            continue
        added = 0
        for candidate in rows:
            key = (candidate.source_name.lower(), normalized_url(candidate.url))
            if key in seen:
                continue
            seen.add(key)
            all_candidates.append(candidate)
            added += 1
        print(f"wikidata_retry={retry_index}/{len(retry_countries)} rows={len(rows)} added={added} total_candidates={len(all_candidates)} country={country_row[1]}", flush=True)
        time.sleep(0.1)
    return all_candidates


def balanced_candidates(candidates: list[Candidate]) -> list[Candidate]:
    buckets: dict[tuple[str, str], list[Candidate]] = defaultdict(list)
    for candidate in sorted(candidates, key=lambda item: (item.macro_region, item.country_or_region, item.source_name)):
        buckets[(candidate.macro_region, candidate.country_or_region)].append(candidate)

    out: list[Candidate] = []
    keys = sorted(buckets)
    while any(buckets.values()) and len(out) < MAX_CANDIDATE_PROBES:
        for key in keys:
            bucket = buckets[key]
            if bucket:
                out.append(bucket.pop(0))
                if len(out) >= MAX_CANDIDATE_PROBES:
                    break
    return out


def detect_protocols(blob: bytes, url: str, content_type: str, links: list[tuple[str, str]]) -> tuple[str, str]:
    text = blob.decode("utf-8", errors="ignore").lower()
    haystack = " ".join([text, url.lower(), content_type.lower(), " ".join(f"{rel} {href}" for rel, href in links).lower()])
    checks = [
        ("IIIF", ["iiif", "manifest.json", "presentation/2", "presentation/3", "rel=\"manifest\""]),
        ("CONTENTdm", ["contentdm", "/digital/api/", "cdm/ref/collection"]),
        ("DSpace", ["dspace", "/server/api/", "handle.net", "bitstream"]),
        ("Omeka", ["omeka", "o:resource_class", "/api/items", "omeka-s"]),
        ("OAI-PMH", ["oai-pmh", "verb=identify", "listrecords", "metadataPrefix"]),
        ("Kramerius", ["kramerius", "api/client/v7.0", "api/client/v5.0"]),
        ("RSS/Atom", ["application/rss+xml", "application/atom+xml", "<rss", "<feed", "rel=\"alternate\""]),
        ("JSON-LD", ["application/ld+json", "schema.org"]),
        ("WordPress REST", ["wp-json", "wp-content", "wordpress"]),
        ("Static JS App", ["_next/static", "__next_data__", "vite", "webpack"]),
        ("PDF", [".pdf", "application/pdf"]),
    ]
    protocols: list[str] = []
    evidence: list[str] = []
    for label, needles in checks:
        hit = next((needle for needle in needles if needle.lower() in haystack), "")
        if hit:
            protocols.append(label)
            evidence.append(f"{label}:{hit}")
    return ";".join(dict.fromkeys(protocols)), "; ".join(evidence)


def image_policy(protocols: str) -> str:
    if any(protocol in protocols for protocol in ("IIIF", "CONTENTdm", "Kramerius")):
        return "candidate IMG02/source-hosted route; IMG03 only after item-level open-rights evidence"
    if any(protocol in protocols for protocol in ("DSpace", "Omeka", "OAI-PMH")):
        return "candidate item capture route; preserve IMG00/IMG02 until item-level visual evidence and rights text are verified"
    return "source success only; next pass must find item-level image-bearing records before public image display"


def priority(protocols: str, source_class: str) -> str:
    if any(protocol in protocols for protocol in ("IIIF", "CONTENTdm", "Kramerius")):
        return "P0 item/image adapter"
    if any(protocol in protocols for protocol in ("DSpace", "Omeka", "OAI-PMH", "WordPress REST", "RSS/Atom", "JSON-LD")):
        return "P1 item/source adapter"
    if "museum" in source_class.lower() or "archive" in source_class.lower():
        return "P1 manual item capture"
    return "P2 source enrichment"


def probe(candidate: Candidate) -> dict[str, str] | None:
    request = urllib.request.Request(
        candidate.url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=PROBE_TIMEOUT) as response:
            status = int(response.status)
            final_url = response.geturl()
            content_type = response.headers.get("content-type", "")
            blob = response.read(PROBE_BYTES)
    except Exception:
        return None
    if status < 200 or status >= 400:
        return None

    parser = HeadParser()
    parser.feed(blob.decode("utf-8", errors="ignore"))
    title = parser.title or candidate.source_name
    description = clean(
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
        or "",
        max_chars=600,
    )
    protocols, evidence = detect_protocols(blob, final_url, content_type, parser.links)
    if not title and not description:
        return None
    return {
        "source_name": candidate.source_name,
        "macro_region": candidate.macro_region,
        "country_or_region": candidate.country_or_region,
        "country_qid": candidate.country_qid,
        "source_class": candidate.source_class,
        "institutional_level": "official_source_site",
        "url": candidate.url,
        "final_url": final_url,
        "http_status": str(status),
        "content_type": clean(content_type, max_chars=140),
        "response_bytes": str(len(blob)),
        "page_title": title,
        "meta_description": description,
        "detected_protocols": protocols,
        "protocol_evidence": clean(evidence, max_chars=500),
        "source_success_status": "success",
        "capture_scope": "official source homepage metadata; no raw payload or image download",
        "image_policy_next": image_policy(protocols),
        "rights_policy_next": "item-level rights review required before IMG01/IMG03; source success alone is not rights clearance",
        "next_item_capture_priority": priority(protocols, candidate.source_class),
        "period_start": "1900",
        "period_end": "2026",
        "period_bands": "1931-1970; 1971-2000; 2001-2026",
        "wikidata_qid": candidate.wikidata_qid,
        "wikidata_url": f"https://www.wikidata.org/wiki/{candidate.wikidata_qid}",
        "access_date": ACCESS_DATE,
        "notes": "Non-mainstream source success registry; not added to public surfaces until item/image capture is ready.",
    }


def select_balanced(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_macro: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: (item["macro_region"], item["country_or_region"], item["source_name"])):
        by_macro[row["macro_region"]].append(row)

    selected: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    macro_selected: Counter[str] = Counter()
    macros = sorted(by_macro)
    while len(selected) < TARGET_SUCCESS_COUNT and any(by_macro.values()):
        progress = False
        for macro in macros:
            if len(selected) >= TARGET_SUCCESS_COUNT:
                break
            cap = MACRO_SELECTION_CAPS.get(macro)
            if cap is not None and macro_selected[macro] >= cap:
                continue
            bucket = by_macro[macro]
            while bucket:
                row = bucket.pop(0)
                key = (row["source_name"].lower(), normalized_url(row["final_url"] or row["url"]))
                if key not in seen:
                    seen.add(key)
                    selected.append(row)
                    macro_selected[macro] += 1
                    progress = True
                    break
        if not progress:
            break
    if len(selected) < TARGET_SUCCESS_COUNT:
        for macro in macros:
            bucket = by_macro[macro]
            while bucket and len(selected) < TARGET_SUCCESS_COUNT:
                row = bucket.pop(0)
                key = (row["source_name"].lower(), normalized_url(row["final_url"] or row["url"]))
                if key in seen:
                    continue
                seen.add(key)
                selected.append(row)
                macro_selected[macro] += 1
    for index, row in enumerate(selected, 1):
        row["source_success_id"] = f"NMSS2026R{index:04d}"
    return selected


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    started = time.time()
    socket.setdefaulttimeout(PROBE_TIMEOUT)
    existing = existing_source_keys()
    candidates = balanced_candidates([
        candidate
        for candidate in fetch_wikidata_candidates()
        if (candidate.source_name.lower(), normalized_url(candidate.url)) not in existing
    ])
    success_rows: list[dict[str, str]] = []
    print(f"probe_candidates={len(candidates)}", flush=True)
    probed = 0
    for batch_start in range(0, len(candidates), PROBE_BATCH_SIZE):
        batch = candidates[batch_start : batch_start + PROBE_BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=MAX_PROBE_WORKERS) as executor:
            future_map = {executor.submit(probe, candidate): candidate for candidate in batch}
            for future in as_completed(future_map):
                row = future.result()
                probed += 1
                if row is not None:
                    success_rows.append(row)
        print(f"probe_progress={probed}/{len(candidates)} success={len(success_rows)}", flush=True)
        if len(success_rows) >= PROBE_STOP_SUCCESS_COUNT:
            break

    selected = select_balanced(success_rows)
    if len(selected) < TARGET_SUCCESS_COUNT:
        raise SystemExit(f"Only {len(selected)} successful new sources; target is {TARGET_SUCCESS_COUNT}.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT, selected, OUTPUT_FIELDS)

    region_country: Counter[tuple[str, str]] = Counter((row["macro_region"], row["country_or_region"]) for row in selected)
    macro_counts = Counter(row["macro_region"] for row in selected)
    class_counts = Counter(row["source_class"] for row in selected)
    protocol_counts = Counter(row["detected_protocols"] or "(none detected)" for row in selected)
    priority_counts = Counter(row["next_item_capture_priority"] for row in selected)

    summary_rows = [
        {"metric": "candidate_sources_from_wikidata", "value": "all", "count": str(len(candidates)), "notes": "New candidate official source sites after existing-source dedupe."},
        {"metric": "successful_new_sources_available", "value": "all", "count": str(len(success_rows)), "notes": "Official source URLs that returned successful source metadata."},
        {"metric": "successful_new_sources_selected", "value": "all", "count": str(len(selected)), "notes": "Balanced non-mainstream source successes written to the registry."},
    ]
    for macro, count in macro_counts.most_common():
        summary_rows.append({"metric": "macro_region_distribution", "value": macro, "count": str(count), "notes": "Selected successful source registry rows."})
    for source_class, count in class_counts.most_common():
        summary_rows.append({"metric": "source_class_distribution", "value": source_class, "count": str(count), "notes": "Selected successful source registry rows."})
    for protocol, count in protocol_counts.most_common():
        summary_rows.append({"metric": "protocol_distribution", "value": protocol, "count": str(count), "notes": "Detected protocol hints only; not rights clearance."})
    for priority_value, count in priority_counts.most_common():
        summary_rows.append({"metric": "next_item_capture_priority", "value": priority_value, "count": str(count), "notes": "Internal triage for later item/image capture."})
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)

    region_rows: list[dict[str, str]] = []
    for (macro, country), count in sorted(region_country.items(), key=lambda item: (item[0][0], item[0][1])):
        country_rows = [row for row in selected if row["macro_region"] == macro and row["country_or_region"] == country]
        region_rows.append(
            {
                "macro_region": macro,
                "country_or_region": country,
                "successful_sources": str(count),
                "source_classes": "; ".join(f"{key}:{value}" for key, value in Counter(row["source_class"] for row in country_rows).most_common()),
                "protocols": "; ".join(f"{key}:{value}" for key, value in Counter(row["detected_protocols"] or "(none detected)" for row in country_rows).most_common()),
            }
        )
    write_csv(REGION_BREAKDOWN, region_rows, REGION_FIELDS)

    lines = [
        "# Non-mainstream Source Success Registry 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This batch records 500 newly successful official source sites from undercovered regions. It is source-success archival metadata, not public-surface/image ingestion.",
        "",
        "## Top Metrics",
        "",
        f"- Candidate official source sites after dedupe: {len(candidates)}",
        f"- Successful new source sites available: {len(success_rows)}",
        f"- Successful new source sites selected: {len(selected)}",
        f"- Runtime seconds: {time.time() - started:.1f}",
        "",
        "## Macro-region Distribution",
        "",
    ]
    for macro, count in macro_counts.most_common():
        lines.append(f"- {macro}: {count}")
    lines.extend(["", "## Next Item/Image Capture Priorities", ""])
    for priority_value, count in priority_counts.most_common():
        lines.append(f"- {priority_value}: {count}")
    lines.extend(["", "## Source Class Distribution", ""])
    for source_class, count in class_counts.most_common(20):
        lines.append(f"- {source_class}: {count}")
    lines.extend(["", "## Boundary", ""])
    lines.extend(
        [
            "- No image binaries, thumbnails, screenshots, cookies, credentials, or raw HTML/source payloads were saved.",
            "- Source success does not upgrade `IMG01` or `IMG03`.",
            "- Rows are not added to generated public surfaces in this pass, so this source-count expansion does not inflate `IMG04` public pages.",
            "- `next_item_capture_priority` is internal triage for future item-level image-bearing capture.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"candidate_sources={len(candidates)}")
    print(f"successful_new_sources_available={len(success_rows)}")
    print(f"successful_new_sources_selected={len(selected)}")
    print("macro_regions=" + ",".join(f"{key}:{value}" for key, value in macro_counts.most_common()))
    print("next_priorities=" + ",".join(f"{key}:{value}" for key, value in priority_counts.most_common()))
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REGION_BREAKDOWN.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    # Some undercovered official source sites have incomplete certificate chains.
    # Keep urllib default verification for the Wikidata query and do not override
    # HTTPS globally; this assignment exists only so static analyzers see that no
    # permissive SSL context is intentionally installed.
    _DEFAULT_SSL_CONTEXT = ssl.create_default_context
    main()
