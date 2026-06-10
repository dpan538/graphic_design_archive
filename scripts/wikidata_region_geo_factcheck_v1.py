#!/usr/bin/env python3
"""Fact-check medium-confidence region/geography suggestions with Wikidata.

This script is dry-run and proposal-only. It never modifies archive records,
taxonomy files, or public surfaces. By default it performs zero network
requests; pass ``--max-queries`` with a positive integer to query Wikidata.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lib.archive_audit import DATA, ROOT, clean, read_csv, write_csv


INPUT = DATA / "region_geo_enrichment_with_confidence_v1.csv"
OUTPUT = DATA / "region_geo_wikidata_validation_v1.csv"
CACHE = DATA / "wikidata_region_geo_factcheck_cache_v1.json"

USER_AGENT = "modern-GD-history-region-normalization/1.0 (proposal-only local audit)"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
ENTITY_DATA = "https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"

FIELDS = [
    "suggestion_id",
    "surface_id",
    "suggestion_type",
    "suggested_label",
    "wikidata_country_found",
    "wikidata_country_qid",
    "external_validation_status",
    "search_term_used",
    "query_status",
]


def load_cache() -> dict[str, dict[str, str]]:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_cache(cache: dict[str, dict[str, str]]) -> None:
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def entity_label(entity: dict, language: str = "en") -> str:
    labels = entity.get("labels") if isinstance(entity.get("labels"), dict) else {}
    return clean(labels.get(language, {}).get("value"))


def entity_country_claim(entity_id: str) -> tuple[str, str]:
    detail = fetch_json(ENTITY_DATA.format(entity_id=entity_id))
    entity = detail.get("entities", {}).get(entity_id, {})
    claims = entity.get("claims") if isinstance(entity.get("claims"), dict) else {}
    countries: dict[str, str] = {}
    for claim in claims.get("P17", []):
        mainsnak = claim.get("mainsnak") if isinstance(claim.get("mainsnak"), dict) else {}
        datavalue = mainsnak.get("datavalue") if isinstance(mainsnak.get("datavalue"), dict) else {}
        value = datavalue.get("value") if isinstance(datavalue.get("value"), dict) else {}
        country_id = clean(value.get("id"))
        if not country_id:
            continue
        country_detail = fetch_json(ENTITY_DATA.format(entity_id=country_id))
        country_entity = country_detail.get("entities", {}).get(country_id, {})
        label = entity_label(country_entity)
        if label:
            countries[country_id] = label
    if len(countries) == 1:
        qid, label = next(iter(countries.items()))
        return label, qid
    return "", ""


def query_wikidata_country(search_term: str, cache: dict[str, dict[str, str]]) -> dict[str, str]:
    if search_term in cache:
        return cache[search_term]

    params = urlencode(
        {
            "action": "wbsearchentities",
            "search": search_term,
            "language": "en",
            "format": "json",
            "limit": "3",
        }
    )
    data = fetch_json(f"{WIKIDATA_API}?{params}")
    countries: dict[str, str] = {}
    for result in data.get("search", []):
        entity_id = clean(result.get("id"))
        if not entity_id:
            continue
        label, qid = entity_country_claim(entity_id)
        if label and qid:
            countries[qid] = label

    if len(countries) == 1:
        qid, label = next(iter(countries.items()))
        payload = {"country_label": label, "country_qid": qid, "query_status": "ok"}
    elif countries:
        payload = {"country_label": "", "country_qid": "", "query_status": "ambiguous_country_claim"}
    else:
        payload = {"country_label": "", "country_qid": "", "query_status": "no_country_claim"}

    cache[search_term] = payload
    save_cache(cache)
    return payload


def search_term_for(row: dict[str, str]) -> str:
    title = clean(row.get("title"))
    evidence = clean(row.get("evidence"))
    suggested = clean(row.get("suggested_label"))
    if title:
        return title[:180]
    if evidence:
        return evidence[:180]
    return suggested


def validation_status(suggested: str, found: str) -> str:
    if not found:
        return "unconfirmed"
    if clean(suggested).lower() == clean(found).lower():
        return "confirmed"
    return "contradicted"


def candidate_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(INPUT):
        if row.get("confidence_level") != "medium":
            continue
        if row.get("suggestion_type") == "historical_split":
            continue
        if row.get("auto_apply_eligible") == "true":
            continue
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-queries", type=int, default=0, help="Maximum Wikidata searches to perform.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds between Wikidata searches.")
    args = parser.parse_args()

    cache = load_cache()
    rows = candidate_rows()
    results: list[dict[str, str]] = []
    queried = 0

    for row in rows:
        term = search_term_for(row)
        found = {"country_label": "", "country_qid": "", "query_status": "not_queried"}
        if args.max_queries > 0 and queried < args.max_queries and term:
            try:
                found = query_wikidata_country(term, cache)
            except Exception as exc:  # noqa: BLE001 - audit script must keep going.
                found = {"country_label": "", "country_qid": "", "query_status": f"error:{type(exc).__name__}"}
            queried += 1
            time.sleep(max(args.sleep, 0))

        country = clean(found.get("country_label"))
        results.append(
            {
                "suggestion_id": row.get("suggestion_id", ""),
                "surface_id": row.get("surface_id", ""),
                "suggestion_type": row.get("suggestion_type", ""),
                "suggested_label": row.get("suggested_label", ""),
                "wikidata_country_found": country,
                "wikidata_country_qid": found.get("country_qid", ""),
                "external_validation_status": validation_status(row.get("suggested_label", ""), country)
                if found.get("query_status") != "not_queried"
                else "unchecked",
                "search_term_used": term,
                "query_status": found.get("query_status", "not_queried"),
            }
        )

    write_csv(OUTPUT, results, FIELDS)
    print(f"medium_review_candidates={len(rows)}")
    print(f"wikidata_queries_performed={queried}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
