#!/usr/bin/env python3
"""Generate source_prospect_registry_v2.

This registry is the durable source-planning layer requested by the Deep
Research remediation plan. It merges existing seed matrices, probe results, and
capture-source summaries into one conservative prospect table. A row here is not
permission to publish a main sheet; it is a classified source candidate with a
known role, protocol hint, rights posture, and capture priority.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

INPUTS = {
    "candidate_v1": DATA / "source_candidate_registry_v1.csv",
    "candidate_probe_v1": DATA / "source_candidate_probe_v1.csv",
    "edge_probe_v2": DATA / "source_probe_edge_v2.csv",
    "independent_asia_probe_v1": DATA / "source_probe_independent_asia_v1.csv",
    "dependency_ledger": DATA / "source_dependency_ledger.csv",
}

OUTPUT = DATA / "source_prospect_registry_v2.csv"
REPORT = DOCS / "SOURCE_PROSPECT_REGISTRY_v2.md"

FIELDNAMES = [
    "source_prospect_id",
    "source_name",
    "source_url",
    "region_group",
    "subregion",
    "country_or_territory",
    "language_scripts",
    "source_family",
    "source_role",
    "protocol_hints",
    "rights_posture",
    "expected_image_path",
    "expected_text_path",
    "credibility_tier",
    "capture_priority",
    "known_limitations",
    "recommended_adapter",
    "seed_query_or_discovery_route",
    "last_checked",
    "source_status",
    "capture_record_count",
    "img00_count",
    "img01_count",
    "img02_count",
    "img03_count",
    "img04_count",
    "discovered_from",
    "notes",
]


def clean(value: str | None) -> str:
    return (value or "").strip()


def norm_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", clean(value))


def norm_name(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def host(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    return (parsed.netloc or "").lower().replace("www.", "")


def key_for(name: str, url: str) -> str:
    h = host(url)
    if h:
        return h
    return norm_name(name)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split_protocols(value: str) -> list[str]:
    text = clean(value)
    if not text:
        return []
    parts = re.split(r"[;+/,|]", text)
    return [p.strip() for p in parts if p.strip()]


def join_unique(*values: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        for part in split_protocols(value):
            low = part.lower()
            if low not in seen:
                seen.add(low)
                out.append(part)
    return "; ".join(out)


def nonempty(*values: str) -> str:
    for value in values:
        value = clean(value)
        if value:
            return value
    return ""


def infer_language_scripts(region: str, country: str, name: str) -> str:
    text = f"{region} {country} {name}".lower()
    if "japan" in text:
        return "Japanese; English possible"
    if "korea" in text:
        return "Korean; English possible"
    if "china" in text or "hong kong" in text or "taiwan" in text:
        return "Chinese; English possible"
    if any(x in text for x in ["argentina", "mexico", "chile", "peru", "colombia", "spain", "uruguay", "bolivia"]):
        return "Spanish"
    if "brazil" in text or "portugal" in text:
        return "Portuguese"
    if any(x in text for x in ["france", "belgium", "quebec", "morocco", "tunisia"]):
        return "French; local languages possible"
    if any(x in text for x in ["iran", "persian"]):
        return "Persian; English possible"
    if any(x in text for x in ["arab", "egypt", "palestin", "qatar", "lebanon"]):
        return "Arabic; English/French possible"
    if any(x in text for x in ["india", "bangladesh", "nepal", "sri lanka", "south asia"]):
        return "English; local scripts required"
    if any(x in text for x in ["indonesia", "malaysia", "singapore", "vietnam", "thailand", "cambodia", "philippines"]):
        return "English; local languages required"
    if any(x in text for x in ["russia", "ukraine", "serbia", "bulgaria"]):
        return "Cyrillic/local language; English possible"
    return "English or local language"


def infer_source_family(kind: str, source_class: str, name: str) -> str:
    text = f"{kind} {source_class} {name}".lower()
    if "newspaper" in text or "hemeroteca" in text or "periodical" in text or "magazine" in text:
        return "newspaper_magazine_ocr_portal"
    if "university" in text or "repository" in text or "special collection" in text:
        return "university_repository_or_special_collection"
    if "national library" in text or "library" in text:
        return "library_or_national_library"
    if "municipal" in text or "city" in text or "state library" in text:
        return "municipal_or_state_archive"
    if "government" in text or "national archive" in text or "public memory" in text:
        return "government_or_public_cultural_database"
    if "community" in text or "activist" in text or "diaspora" in text or "movement" in text or "zine" in text:
        return "community_activist_diaspora_archive"
    if "film" in text or "poster" in text or "festival" in text:
        return "poster_film_festival_design_archive"
    if "aggregator" in text or "metadata" in text or "search api" in text:
        return "aggregator_or_discovery_router"
    if "wordpress" in text or "independent" in text or "blog" in text:
        return "independent_design_archive_or_publication"
    if "social" in text or "pinterest" in text or "instagram" in text or "arena" in text:
        return "social_or_repost_discovery_only"
    return "general_archive_or_collection"


def infer_source_role(family: str, status: str, kind: str, notes: str) -> str:
    text = f"{family} {status} {kind} {notes}".lower()
    if "social_or_repost" in family or "discovery-only" in text or "lead" in text:
        return "discovery_lead"
    if "aggregator" in family or "router" in family:
        return "aggregator_router"
    if "text_only" in text or "context" in text:
        return "context_source"
    if "active_in_public_payload" in text or "captured" in text:
        return "source_record_candidate"
    return "source_of_record_candidate"


def infer_rights_posture(value: str, image: str, family: str) -> str:
    text = f"{value} {image} {family}".lower()
    if "high" in text or "rights-sensitive" in text or "community" in text:
        return "high_review_required"
    if "open" in text or "prefer_open_image" in text or "img03" in text:
        return "open_candidate_review_required"
    if "source" in text or "iiif" in text or "viewer" in text or "img02" in text:
        return "source_hosted_or_viewer_review_required"
    if "thumbnail" in text or "img01" in text:
        return "thumbnail_or_preview_review_required"
    if "text_only" in text or "img04" in text:
        return "text_only_no_image_expected"
    return "link_only_until_rights_verified"


def infer_expected_image_path(image_strategy: str, protocol: str, rights: str) -> str:
    text = f"{image_strategy} {protocol} {rights}".lower()
    if "prefer_open" in text or "open_candidate" in text:
        return "open_download_or_open_api"
    if "iiif" in text:
        return "iiif_or_source_viewer"
    if "source" in text or "viewer" in text:
        return "source_hosted_viewer_or_thumbnail"
    if "thumbnail" in text:
        return "thumbnail_plus_source_return"
    if "text_only" in text:
        return "no_image_expected_text_page"
    return "source_return_or_img00"


def infer_expected_text_path(text_strategy: str, family: str, protocols: str) -> str:
    text = f"{text_strategy} {family} {protocols}".lower()
    if "ocr" in text or "newspaper" in text or "periodical" in text:
        return "ocr_or_periodical_text"
    if "text-rich" in text or "publication" in text:
        return "source_context_text"
    if "api" in text or "json" in text:
        return "structured_metadata"
    return "metadata_plus_source_return"


def infer_credibility_tier(family: str, cls: str, status: str, rights: str) -> str:
    text = f"{family} {cls} {status} {rights}".lower()
    if "social_or_repost" in text:
        return "D_discovery_only"
    if "active" in text or "captured" in text:
        return "A_verified_or_captured"
    if any(x in text for x in ["government", "national", "university", "municipal", "library"]):
        return "A_custodial_or_public_institution"
    if any(x in text for x in ["community", "activist", "diaspora", "independent"]):
        return "B_contextual_or_community_custody"
    if "aggregator" in text:
        return "B_discovery_router"
    return "C_needs_verification"


def infer_priority(value: str, status: str, family: str) -> str:
    text = f"{value} {status} {family}".lower()
    if "p0" in text or "active" in text:
        return "P0_active_or_already_captured"
    if "p1" in text or "underrepresented" in text:
        return "P1_next_adapter_or_probe"
    if "p2" in text:
        return "P2_source_family_followup"
    if "p3" in text:
        return "P3_gap_filler"
    if "p4" in text or "hold" in text:
        return "P4_manual_or_later"
    return "P2_source_family_followup"


def blank_row() -> dict[str, str]:
    return {name: "" for name in FIELDNAMES}


def row_from_candidate_v1(src: dict[str, str]) -> dict[str, str]:
    row = blank_row()
    family = infer_source_family(clean(src.get("source_kind")), clean(src.get("institution_class")), clean(src.get("source_name")))
    rights = infer_rights_posture(clean(src.get("rights_risk")), clean(src.get("image_strategy")), family)
    protocols = clean(src.get("access_family"))
    row.update(
        {
            "source_name": clean(src.get("source_name")),
            "source_url": clean(src.get("url")),
            "region_group": clean(src.get("macro_region")),
            "subregion": "",
            "country_or_territory": clean(src.get("country_or_region")),
            "language_scripts": infer_language_scripts(clean(src.get("macro_region")), clean(src.get("country_or_region")), clean(src.get("source_name"))),
            "source_family": family,
            "source_role": infer_source_role(family, clean(src.get("current_ingest_status")), clean(src.get("source_kind")), clean(src.get("notes"))),
            "protocol_hints": protocols,
            "rights_posture": rights,
            "expected_image_path": infer_expected_image_path(clean(src.get("image_strategy")), protocols, rights),
            "expected_text_path": infer_expected_text_path(clean(src.get("text_strategy")), family, protocols),
            "credibility_tier": infer_credibility_tier(family, clean(src.get("institution_class")), clean(src.get("current_ingest_status")), rights),
            "capture_priority": infer_priority(clean(src.get("automation_priority")), clean(src.get("current_ingest_status")), family),
            "known_limitations": "",
            "recommended_adapter": clean(src.get("access_family")).lower().replace("+", "_or_") or "manual_or_html_adapter",
            "seed_query_or_discovery_route": "source_candidate_registry_v1",
            "last_checked": "",
            "source_status": clean(src.get("current_ingest_status")) or "candidate",
            "discovered_from": "source_candidate_registry_v1",
            "notes": clean(src.get("notes")),
        }
    )
    return row


def row_from_probe(src: dict[str, str], discovered_from: str) -> dict[str, str]:
    row = blank_row()
    name = clean(src.get("source_name"))
    region = nonempty(src.get("macro_region"), src.get("region_group"))
    country = nonempty(src.get("country_or_region"), src.get("country_or_territory"))
    cls = nonempty(src.get("source_class"), src.get("institution_class"), src.get("institution_class_claimed"))
    kind = nonempty(src.get("source_class"), src.get("institution_class"), src.get("source_kind"))
    protocols = nonempty(src.get("detected_protocols"), src.get("access_family_claimed"))
    family = infer_source_family(kind, cls, name)
    image_policy = nonempty(src.get("recommended_image_policy"), src.get("recommended_image_policy"))
    rights = infer_rights_posture(nonempty(src.get("rights_risk")), image_policy, family)
    status = clean(src.get("probe_status"))
    failure = clean(src.get("failure_reason"))
    row.update(
        {
            "source_name": name,
            "source_url": nonempty(src.get("final_url"), src.get("url")),
            "region_group": region,
            "subregion": "",
            "country_or_territory": country,
            "language_scripts": infer_language_scripts(region, country, name),
            "source_family": family,
            "source_role": infer_source_role(family, status, kind, clean(src.get("notes"))),
            "protocol_hints": protocols,
            "rights_posture": rights,
            "expected_image_path": infer_expected_image_path(image_policy, protocols, rights),
            "expected_text_path": infer_expected_text_path(nonempty(src.get("recommended_text_policy")), family, protocols),
            "credibility_tier": infer_credibility_tier(family, cls, status, rights),
            "capture_priority": infer_priority(nonempty(src.get("capture_priority"), src.get("capture_priority_next")), status, family),
            "known_limitations": failure,
            "recommended_adapter": nonempty(src.get("adapter_hint"), protocols.lower().replace("; ", "_or_")) or "manual_or_html_adapter",
            "seed_query_or_discovery_route": nonempty(src.get("discovery_channel"), src.get("capture_intent"), src.get("capture_intent")),
            "last_checked": clean(src.get("access_date")),
            "source_status": f"probe_{status}" if status else "probe_candidate",
            "discovered_from": discovered_from,
            "notes": clean(src.get("notes")),
        }
    )
    return row


def row_from_dependency(src: dict[str, str]) -> dict[str, str]:
    row = blank_row()
    name = clean(src.get("source_name"))
    family = infer_source_family(clean(src.get("dependency_role")), "", name)
    protocols = clean(src.get("capture_scripts"))
    rights = infer_rights_posture(clean(src.get("rights_dependency")), "", family)
    row.update(
        {
            "source_name": name,
            "source_url": "",
            "region_group": "active dependency / needs mapping",
            "subregion": "",
            "country_or_territory": "",
            "language_scripts": infer_language_scripts("", "", name),
            "source_family": family,
            "source_role": "source_record_candidate",
            "protocol_hints": protocols,
            "rights_posture": rights,
            "expected_image_path": infer_expected_image_path("", protocols, rights),
            "expected_text_path": infer_expected_text_path(clean(src.get("text_dependency")), family, protocols),
            "credibility_tier": "A_verified_or_captured",
            "capture_priority": "P0_active_or_already_captured",
            "known_limitations": "",
            "recommended_adapter": clean(src.get("capture_scripts")),
            "seed_query_or_discovery_route": "source_dependency_ledger",
            "last_checked": "",
            "source_status": "active_dependency",
            "capture_record_count": clean(src.get("surface_count")),
            "img00_count": clean(src.get("img00")),
            "img01_count": clean(src.get("img01")),
            "img02_count": clean(src.get("img02")),
            "img03_count": clean(src.get("img03")),
            "img04_count": clean(src.get("img04")),
            "discovered_from": "source_dependency_ledger",
            "notes": clean(src.get("dependency_role")),
        }
    )
    return row


def source_summary_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(DATA.glob("capture_batch_*_source_summary.csv")):
        for src in read_csv(path):
            name = clean(src.get("source_name"))
            if not name:
                continue
            row = blank_row()
            family = infer_source_family(clean(src.get("adapter_hint")), "", name)
            image_states = clean(src.get("image_states"))
            row.update(
                {
                    "source_name": name,
                    "source_url": "",
                    "region_group": clean(src.get("macro_region")) or "captured source / needs mapping",
                    "subregion": "",
                    "country_or_territory": clean(src.get("country_or_region")),
                    "language_scripts": infer_language_scripts(clean(src.get("macro_region")), clean(src.get("country_or_region")), name),
                    "source_family": family,
                    "source_role": "source_record_candidate",
                    "protocol_hints": clean(src.get("adapter_hint")),
                    "rights_posture": infer_rights_posture(clean(src.get("notes")), image_states, family),
                    "expected_image_path": infer_expected_image_path(image_states, clean(src.get("adapter_hint")), clean(src.get("notes"))),
                    "expected_text_path": "captured_record_metadata_or_source_context",
                    "credibility_tier": "A_verified_or_captured",
                    "capture_priority": "P0_active_or_already_captured",
                    "known_limitations": clean(src.get("notes")),
                    "recommended_adapter": clean(src.get("adapter_hint")),
                    "seed_query_or_discovery_route": path.name,
                    "last_checked": "",
                    "source_status": clean(src.get("status")) or "captured_source_summary",
                    "capture_record_count": nonempty(src.get("captured_count"), src.get("captured_records")),
                    "img00_count": clean(src.get("img00_count")),
                    "img01_count": clean(src.get("img01_count")),
                    "img02_count": clean(src.get("img02_count")),
                    "img03_count": clean(src.get("img03_count")),
                    "img04_count": clean(src.get("img04_count")),
                    "discovered_from": path.name,
                    "notes": clean(src.get("notes")),
                }
            )
            rows.append(row)
    return rows


def merge_rows(base: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    for field in FIELDNAMES:
        current = clean(merged.get(field))
        new = clean(incoming.get(field))
        if field == "protocol_hints":
            merged[field] = join_unique(current, new)
        elif field == "discovered_from":
            merged[field] = "; ".join(
                dict.fromkeys(part for part in [*current.split("; "), *new.split("; ")] if part)
            )
        elif field == "capture_record_count":
            try:
                total = int(current or 0) + int(new or 0)
                merged[field] = str(total) if total else current or new
            except ValueError:
                merged[field] = current or new
        elif field in {"img00_count", "img01_count", "img02_count", "img03_count", "img04_count"}:
            try:
                total = int(current or 0) + int(new or 0)
                merged[field] = str(total) if total else current or new
            except ValueError:
                merged[field] = current or new
        elif not current and new:
            merged[field] = new
        elif field in {"last_checked"} and new > current:
            merged[field] = new
        elif field == "source_status" and "captured" in new and "captured" not in current:
            merged[field] = new
        elif field == "capture_priority" and current.startswith(("P2", "P3", "P4")) and new.startswith(("P0", "P1")):
            merged[field] = new
    return merged


def build_rows() -> list[dict[str, str]]:
    staged: dict[str, dict[str, str]] = {}
    name_index: dict[str, str] = {}

    input_rows: list[dict[str, str]] = []
    input_rows += [row_from_candidate_v1(row) for row in read_csv(INPUTS["candidate_v1"])]
    input_rows += [row_from_probe(row, "source_candidate_probe_v1") for row in read_csv(INPUTS["candidate_probe_v1"])]
    input_rows += [row_from_probe(row, "source_probe_edge_v2") for row in read_csv(INPUTS["edge_probe_v2"])]
    input_rows += [row_from_probe(row, "source_probe_independent_asia_v1") for row in read_csv(INPUTS["independent_asia_probe_v1"])]
    input_rows += [row_from_dependency(row) for row in read_csv(INPUTS["dependency_ledger"])]
    input_rows += source_summary_rows()

    for row in input_rows:
        name = clean(row.get("source_name"))
        if not name:
            continue
        name_key = norm_name(name)
        key = name_index.get(name_key) or key_for(name, clean(row.get("source_url")))
        if key in staged:
            staged[key] = merge_rows(staged[key], row)
        else:
            staged[key] = row
        name_index[name_key] = key

    rows = list(staged.values())
    rows.sort(
        key=lambda row: (
            row.get("capture_priority", "P9"),
            row.get("region_group", ""),
            row.get("source_family", ""),
            row.get("source_name", "").lower(),
        )
    )
    for idx, row in enumerate(rows, start=1):
        row["source_prospect_id"] = f"SPV2-{idx:04d}"
    return rows


def counter_report(rows: list[dict[str, str]], field: str) -> list[str]:
    counts = Counter(row.get(field, "") or "unmapped" for row in rows)
    return [f"- {key}: {count}" for key, count in counts.most_common()]


def write_report(rows: list[dict[str, str]]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    captured = sum(1 for row in rows if row["capture_priority"].startswith("P0"))
    p1 = sum(1 for row in rows if row["capture_priority"].startswith("P1"))
    non_western = sum(
        1
        for row in rows
        if row["region_group"]
        and not any(x in row["region_group"].lower() for x in ["western", "north america", "active dependency"])
    )
    discovery_only = sum(1 for row in rows if row["source_role"] == "discovery_lead")
    localish = sum(
        1
        for row in rows
        if any(
            token in f"{row['source_family']} {row['source_role']} {row['credibility_tier']}".lower()
            for token in ["community", "university", "government", "municipal", "diaspora", "activist"]
        )
    )
    protocol_counts = Counter()
    for row in rows:
        for protocol in split_protocols(row["protocol_hints"]):
            protocol_counts[protocol] += 1

    lines = [
        "# Source Prospect Registry v2",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "This registry is the source-planning layer for the rights-aware modern graphic design history archive. A row is a classified source prospect, not a public-surface approval.",
        "",
        "## Summary",
        "",
        f"- Total source prospects: {len(rows)}",
        f"- Already captured / active dependency: {captured}",
        f"- P1 next adapter or probe candidates: {p1}",
        f"- Non-Western or transregional candidates: {non_western}",
        f"- Local/community/university/government/municipal candidates: {localish}",
        f"- Discovery-only lead sources: {discovery_only}",
        "",
        "## Source Families",
        "",
        *counter_report(rows, "source_family"),
        "",
        "## Region Groups",
        "",
        *counter_report(rows, "region_group"),
        "",
        "## Credibility Tiers",
        "",
        *counter_report(rows, "credibility_tier"),
        "",
        "## Source Roles",
        "",
        *counter_report(rows, "source_role"),
        "",
        "## Protocol Hints",
        "",
    ]
    for key, count in protocol_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Execution Notes",
            "",
            "- Use this registry before new capture batches.",
            "- Select candidates by source family, region, language/script, and rights posture.",
            "- Discovery-only rows cannot publish main sheets without corroboration.",
            "- Captured rows still need linkage/grouping and surface assignment before public payload rebuild.",
            "- This registry intentionally separates source prospecting from public-surface publishing.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_report(rows)
    print(f"Wrote {OUTPUT} ({len(rows)} rows)")
    print(f"Wrote {REPORT}")
    print("source_family", dict(Counter(row["source_family"] for row in rows).most_common(12)))
    print("region_group", dict(Counter(row["region_group"] for row in rows).most_common(12)))
    print("priority", dict(Counter(row["capture_priority"] for row in rows).most_common()))


if __name__ == "__main__":
    main()
