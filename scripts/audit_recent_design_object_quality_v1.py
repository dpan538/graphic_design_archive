#!/usr/bin/env python3
"""Audit recent object quality, studio coverage, and concentration risks.

This diagnostic pass is intentionally non-mutating. It helps separate
2005-2025 independent studio/design-object candidates from recent postage
stamps, event photographs, memory material, source-profile spans, and
single-source concentration risks.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

QUALITY_AUDIT = DATA / "recent_design_object_quality_audit_2005_2025_v1.csv"
STUDIO_AUDIT = DATA / "independent_studio_work_audit_2005_2025_v1.csv"
RECLASS_QUEUE = DATA / "recent_stamp_event_reclassification_queue_v1.csv"
CONCENTRATION_REVIEW = DATA / "recent_source_concentration_review_v1.csv"
SUMMARY = DATA / "recent_design_object_quality_summary_2005_2025_v1.csv"
YEAR_SUMMARY = DATA / "recent_design_object_quality_year_summary_2005_2025_v1.csv"
REPORT = DOCS / "RECENT_DESIGN_OBJECT_QUALITY_AUDIT_2005_2025_v1.md"

START_YEAR = 2005
END_YEAR = 2025
RECENT_YEARS = {2025, 2026}

AUDIT_FIELDS = [
    "capture_file",
    "capture_id",
    "source_name",
    "source_title",
    "source_creator",
    "object_year",
    "date_start",
    "date_end",
    "source_place_text",
    "source_object_type",
    "source_medium",
    "source_collection",
    "image_presence_code",
    "rights_basis",
    "source_record_url",
    "source_domain",
    "quality_bucket",
    "studio_confidence",
    "studio_key",
    "source_concentration_count",
    "domain_concentration_count",
    "studio_concentration_count",
    "review_flags",
    "classification_note",
]

CONCENTRATION_FIELDS = [
    "concentration_type",
    "key",
    "record_count",
    "studio_candidate_count",
    "stamp_or_event_count",
    "sample_titles",
    "review_note",
]

SUMMARY_FIELDS = ["metric", "value", "note"]
YEAR_SUMMARY_FIELDS = [
    "year",
    "total_records",
    "primary_design_candidates",
    "studio_high",
    "studio_manual",
    "stamp_review",
    "event_memory_card_only",
    "recent_manual_review",
    "primary_share",
    "stamp_event_share",
]

HIGH_STUDIO_TERMS = re.compile(
    r"\b(design\s+studio|studio\s+[a-z0-9][a-z0-9&.\-\s]{1,40}|[a-z0-9][a-z0-9&.\-\s]{1,40}\s+studio|"
    r"atelier|design\s+bureau|type\s+foundry|graphics?\s+lab|design\s+lab|"
    r"visual\s+communication\s+studio|creative\s+agency|advertising\s+agency)\b",
    re.IGNORECASE,
)
WEAK_STUDIO_TERMS = re.compile(
    r"\b(studio|agency|collective|cooperative|foundry|workshop)\b",
    re.IGNORECASE,
)
STUDIO_FALSE_POSITIVES = re.compile(
    r"\b(studio\s+portrait|film\s+studio|television\s+studio|tv\s+studio|recording\s+studio|"
    r"studio\s+album|studio\s+museum|photo\s+studio|photography\s+studio|dance\s+studio|"
    r"yoga\s+studio|in\s+his\s+studio|in\s+her\s+studio|studio\s+and\s+art\s+gallery|"
    r"artist\s+studio|art\s+gallery|celebrated\s+western\s+artist|"
    r"bureau\s+of\s+land\s+management|workshop\s+in\s+university)\b",
    re.IGNORECASE,
)
DESIGN_OBJECT_TERMS = re.compile(
    r"\b(poster|advertis(e|ing|ement)|identity|branding|logo|mark|campaign|typograph|"
    r"typeface|font|letterform|book\s+cover|cover|magazine|record\s+sleeve|album\s+cover|"
    r"label|packaging|catalogue|catalog|editorial|signage|wayfinding|exhibition\s+graphic|"
    r"visual\s+communication|graphic\s+design|website|web\s+design|interface|layout)\b",
    re.IGNORECASE,
)
STAMP_TERMS = re.compile(
    r"\b(postage|postal|stamp|stamps|philatel|first\s+day\s+cover|souvenir\s+sheet|"
    r"commemorative\s+issue|stamp\s+issue)\b",
    re.IGNORECASE,
)
COMMEMORATIVE_TERMS = re.compile(
    r"\b(commemorat|anniversary|centenary|bicentenary|jubilee|memorial|remembrance|"
    r"remembering|homage|tribute)\b",
    re.IGNORECASE,
)
EVENT_TERMS = re.compile(
    r"\b(event|conference|symposium|seminar|workshop|poster\s+session|session|meeting|"
    r"opening|launch|award|ceremony|lecture|talk|panel|festival|biennial|triennial|"
    r"wikimania|asian\s*games|expo)\b",
    re.IGNORECASE,
)
PHOTO_TERMS = re.compile(r"\b(photo|photograph|snapshot|group\s+photo|portrait|documentation)\b", re.IGNORECASE)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def lower(value: object) -> str:
    return clean(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def capture_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if "cell_assignments" in path.name:
            continue
        for row in read_csv(path):
            row = dict(row)
            row["_capture_file"] = path.name
            rows.append(row)
    return rows


def safe_year(value: object) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        year = int(float(text))
    except ValueError:
        return None
    if 1830 <= year <= 2026:
        return year
    return None


def year_span(row: dict[str, str]) -> tuple[int | None, int | None]:
    return safe_year(row.get("date_start")), safe_year(row.get("date_end"))


def record_year(row: dict[str, str]) -> int | None:
    return safe_year(row.get("date_end")) or safe_year(row.get("date_start"))


def source_date_object_years(row: dict[str, str]) -> list[int]:
    source_date = lower(row.get("source_date_text"))
    if not source_date:
        return []
    if "accessed" in source_date or "coverage target" in source_date:
        return []
    years: list[int] = []
    for match in re.findall(r"\b(1[7-9]\d{2}|20[0-2]\d)\b", source_date):
        year = safe_year(match)
        if year is not None:
            years.append(year)
    return years


def access_year_used_as_object_year(row: dict[str, str]) -> bool:
    start, end = year_span(row)
    source_date = lower(row.get("source_date_text"))
    citation = lower(row.get("citation_basis"))
    if "accessed 2026" in source_date:
        return True
    if end in RECENT_YEARS and "accessed 2026" in citation and not source_date_object_years(row):
        return True
    if start in RECENT_YEARS and end in RECENT_YEARS and "accessed 2026" in citation and not source_date_object_years(row):
        return True
    return False


def span_or_profile_record(row: dict[str, str]) -> bool:
    start, end = year_span(row)
    source_date = lower(row.get("source_date_text"))
    object_type = lower(row.get("source_object_type"))
    notes = lower(" ".join([row.get("source_notes", ""), row.get("classification_rationale", ""), row.get("uncertainty_note", "")]))
    if "coverage target" in source_date:
        return True
    if access_year_used_as_object_year(row):
        return True
    if "source profile" in object_type:
        return True
    if "official source image-bearing record" in object_type:
        return True
    if "source page, logo, hero, or collection image" in notes:
        return True
    if start is not None and end is not None and end - start >= 25:
        return True
    return False


def blob(row: dict[str, str]) -> str:
    fields = [
        "source_name",
        "source_title",
        "source_creator",
        "source_object_type",
        "source_medium",
        "source_collection",
        "source_description",
        "source_notes",
        "source_subjects",
        "editorial_summary",
        "historical_context_note",
        "classification_rationale",
        "uncertainty_note",
    ]
    return " ".join(clean(row.get(field)) for field in fields)


def signal_blob(row: dict[str, str]) -> str:
    """Source/object-side text for classification signals.

    Excludes generated rationale/uncertainty notes so previous audit phrases
    such as "weak event-photo filtering" cannot feed back into this review.
    """
    fields = [
        "source_name",
        "source_title",
        "source_creator",
        "source_object_type",
        "source_medium",
        "source_collection",
        "source_description",
        "source_subjects",
        "ocr_or_excerpt",
        "source_description_raw",
    ]
    return " ".join(clean(row.get(field)) for field in fields)


def source_domain(row: dict[str, str]) -> str:
    url = clean(row.get("source_record_url"))
    if not url:
        return ""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def normalized_key(value: object) -> str:
    text = lower(value)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stamp_review(row: dict[str, str], year: int) -> bool:
    text = signal_blob(row)
    if year < 2010:
        return False
    if not STAMP_TERMS.search(text):
        return False
    return bool(COMMEMORATIVE_TERMS.search(text) or "postage" in lower(text) or "philatel" in lower(text))


def event_or_memory_review(row: dict[str, str]) -> bool:
    text = signal_blob(row)
    title = clean(row.get("source_title"))
    object_type = clean(row.get("source_object_type"))
    if "poster session" in lower(title):
        return True
    if PHOTO_TERMS.search(text) and EVENT_TERMS.search(text):
        return True
    if COMMEMORATIVE_TERMS.search(text) and PHOTO_TERMS.search(text):
        return True
    if "photograph" in lower(object_type) and not DESIGN_OBJECT_TERMS.search(text):
        return True
    return False


def studio_signal(row: dict[str, str]) -> tuple[str, str, str]:
    creator = clean(row.get("source_creator"))
    source_name = clean(row.get("source_name"))
    text = signal_blob(row)
    if STUDIO_FALSE_POSITIVES.search(text):
        return "none", "", "studio false-positive phrase"

    source_name_lower = lower(source_name)
    provenance_source_name = (
        source_name_lower.startswith("wikimedia commons file source")
        or source_name_lower.startswith("commons file source")
        or " / page " in source_name_lower
    )

    for label, value in [("creator", creator), ("source", "" if provenance_source_name else source_name)]:
        if not value:
            continue
        if HIGH_STUDIO_TERMS.search(value):
            return "high", normalized_key(value), f"explicit studio term in {label}"
        if WEAK_STUDIO_TERMS.search(value) and DESIGN_OBJECT_TERMS.search(text):
            key = normalized_key(value)
            return "medium", key, f"weak studio term in {label}"

    if (HIGH_STUDIO_TERMS.search(text) or WEAK_STUDIO_TERMS.search(text)) and DESIGN_OBJECT_TERMS.search(text):
        key_source = creator or source_name or row.get("source_collection") or row.get("source_title")
        return "medium", normalized_key(key_source), "studio/design terms in record text"
    return "none", "", ""


def classify_row(row: dict[str, str], source_counts: Counter[str], domain_counts: Counter[str], studio_counts: Counter[str]) -> dict[str, object] | None:
    year = record_year(row)
    if year is None or not (START_YEAR <= year <= END_YEAR):
        return None

    text = signal_blob(row)
    domain = source_domain(row)
    source_name = clean(row.get("source_name"))
    studio_conf, studio_key, studio_note = studio_signal(row)
    flags: list[str] = []

    if span_or_profile_record(row):
        bucket = "exclude_span_or_profile"
        flags.append("not_object_year_safe")
        note = "Source-profile, source-page, coverage-span, access-year, or long-span record; exclude from object success metrics."
    elif stamp_review(row, year):
        bucket = "card_or_appendix_recent_commemorative_stamp_review"
        flags.append("post_2010_stamp_or_philatelic_material")
        note = "Post-2010 stamp/philatelic or commemorative material should not dominate design-object coverage."
    elif event_or_memory_review(row):
        bucket = "card_only_event_or_memory_material"
        flags.append("event_photo_or_memory_documentation")
        note = "Event photo/documentation/memory material is research support, not a primary design object."
    elif studio_conf == "high" and DESIGN_OBJECT_TERMS.search(text):
        bucket = "independent_studio_work_candidate_high"
        flags.append("studio_work_candidate")
        note = f"High-confidence independent studio/design-object candidate; {studio_note}."
    elif studio_conf in {"high", "medium"}:
        bucket = "independent_studio_manual_review"
        flags.append("studio_signal_needs_object_check")
        note = f"Studio-like signal present, but object type needs review; {studio_note}."
    elif DESIGN_OBJECT_TERMS.search(text):
        bucket = "design_object_no_studio_signal"
        note = "Design-object terms present, but no independent studio signal."
    else:
        bucket = "recent_object_manual_review"
        flags.append("weak_graphic_design_signal")
        note = "Recent object-dated record needs review for graphic-design relevance."

    if source_counts[source_name] > 25:
        flags.append("source_concentration_gt_25")
    if domain and domain_counts[domain] > 25:
        flags.append("domain_concentration_gt_25")
    if studio_key and studio_counts[studio_key] > 10:
        flags.append("studio_concentration_gt_10")

    return {
        "capture_file": row.get("_capture_file", ""),
        "capture_id": row.get("capture_id", ""),
        "source_name": source_name,
        "source_title": clean(row.get("source_title")),
        "source_creator": clean(row.get("source_creator")),
        "object_year": year,
        "date_start": clean(row.get("date_start")),
        "date_end": clean(row.get("date_end")),
        "source_place_text": clean(row.get("source_place_text")),
        "source_object_type": clean(row.get("source_object_type")),
        "source_medium": clean(row.get("source_medium")),
        "source_collection": clean(row.get("source_collection")),
        "image_presence_code": clean(row.get("image_presence_code")),
        "rights_basis": clean(row.get("rights_basis")),
        "source_record_url": clean(row.get("source_record_url")),
        "source_domain": domain,
        "quality_bucket": bucket,
        "studio_confidence": studio_conf,
        "studio_key": studio_key,
        "source_concentration_count": source_counts[source_name],
        "domain_concentration_count": domain_counts[domain] if domain else 0,
        "studio_concentration_count": studio_counts[studio_key] if studio_key else 0,
        "review_flags": "; ".join(flags),
        "classification_note": note,
    }


def sample_titles(rows: list[dict[str, object]]) -> str:
    titles = []
    for row in rows:
        title = clean(row.get("source_title"))
        if title and title not in titles:
            titles.append(title)
        if len(titles) >= 5:
            break
    return " | ".join(titles)


def concentration_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for concentration_type, field, threshold in [
        ("source_name", "source_name", 25),
        ("source_domain", "source_domain", 25),
        ("studio_key", "studio_key", 10),
    ]:
        groups: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            key = clean(row.get(field))
            if not key:
                continue
            groups.setdefault(key, []).append(row)
        for key, group in groups.items():
            if len(group) <= threshold:
                continue
            studio_count = sum(1 for row in group if clean(row.get("quality_bucket")).startswith("independent_studio"))
            reclass_count = sum(1 for row in group if clean(row.get("quality_bucket")) in {"card_or_appendix_recent_commemorative_stamp_review", "card_only_event_or_memory_material"})
            out.append(
                {
                    "concentration_type": concentration_type,
                    "key": key,
                    "record_count": len(group),
                    "studio_candidate_count": studio_count,
                    "stamp_or_event_count": reclass_count,
                    "sample_titles": sample_titles(group),
                    "review_note": "Cap or sample before further capture from this source/studio unless explicitly justified.",
                }
            )
    out.sort(key=lambda row: (-int(row["record_count"]), str(row["concentration_type"]), str(row["key"])))
    return out


def primary_design_candidate(row: dict[str, object]) -> bool:
    return clean(row.get("quality_bucket")) in {
        "design_object_no_studio_signal",
        "independent_studio_work_candidate_high",
        "independent_studio_manual_review",
        "recent_object_manual_review",
    }


def year_summary_rows(audit_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    by_year: dict[int, list[dict[str, object]]] = {}
    for row in audit_rows:
        year_text = clean(row.get("object_year"))
        if not year_text:
            continue
        by_year.setdefault(int(year_text), []).append(row)
    for year in range(START_YEAR, END_YEAR + 1):
        group = by_year.get(year, [])
        total = len(group)
        primary = sum(1 for row in group if primary_design_candidate(row))
        studio_high = sum(1 for row in group if clean(row.get("quality_bucket")) == "independent_studio_work_candidate_high")
        studio_manual = sum(1 for row in group if clean(row.get("quality_bucket")) == "independent_studio_manual_review")
        stamp = sum(1 for row in group if clean(row.get("quality_bucket")) == "card_or_appendix_recent_commemorative_stamp_review")
        event = sum(1 for row in group if clean(row.get("quality_bucket")) == "card_only_event_or_memory_material")
        recent_manual = sum(1 for row in group if clean(row.get("quality_bucket")) == "recent_object_manual_review")
        out.append(
            {
                "year": year,
                "total_records": total,
                "primary_design_candidates": primary,
                "studio_high": studio_high,
                "studio_manual": studio_manual,
                "stamp_review": stamp,
                "event_memory_card_only": event,
                "recent_manual_review": recent_manual,
                "primary_share": f"{(primary / total):.3f}" if total else "0.000",
                "stamp_event_share": f"{((stamp + event) / total):.3f}" if total else "0.000",
            }
        )
    return out


def summary_rows(audit_rows: list[dict[str, object]], concentration: list[dict[str, object]]) -> list[dict[str, object]]:
    bucket_counts = Counter(clean(row.get("quality_bucket")) for row in audit_rows)
    year_counts = Counter(int(row["object_year"]) for row in audit_rows if clean(row.get("object_year")))
    source_counts = Counter(clean(row.get("source_name")) for row in audit_rows)
    domain_counts = Counter(clean(row.get("source_domain")) for row in audit_rows if clean(row.get("source_domain")))
    high_studios = {
        clean(row.get("studio_key"))
        for row in audit_rows
        if clean(row.get("quality_bucket")) == "independent_studio_work_candidate_high" and clean(row.get("studio_key"))
    }
    manual_studios = {
        clean(row.get("studio_key"))
        for row in audit_rows
        if clean(row.get("quality_bucket")) == "independent_studio_manual_review" and clean(row.get("studio_key"))
    }
    rows: list[dict[str, object]] = [
        {"metric": "scope_years", "value": f"{START_YEAR}-{END_YEAR}", "note": "Object-year audit range."},
        {"metric": "records_in_scope", "value": len(audit_rows), "note": "Object-dated and span/profile records with record year in scope."},
        {"metric": "unique_high_confidence_studio_keys", "value": len(high_studios), "note": "Unique studio keys among high-confidence studio work candidates."},
        {"metric": "unique_manual_review_studio_keys", "value": len(manual_studios), "note": "Unique studio keys among manual-review studio candidates."},
    ]
    for bucket, count in bucket_counts.most_common():
        rows.append({"metric": f"bucket:{bucket}", "value": count, "note": "Quality bucket count."})
    for year, count in sorted(year_counts.items()):
        rows.append({"metric": f"year:{year}", "value": count, "note": "Records by object year after current date parsing."})
    for source, count in source_counts.most_common(15):
        rows.append({"metric": f"top_source:{source}", "value": count, "note": "Top source concentration in 2005-2025 scope."})
    for domain, count in domain_counts.most_common(15):
        rows.append({"metric": f"top_domain:{domain}", "value": count, "note": "Top source domain concentration in 2005-2025 scope."})
    rows.append({"metric": "concentration_review_rows", "value": len(concentration), "note": "Sources/domains/studios exceeding review thresholds."})
    return rows


def write_report(
    audit_rows: list[dict[str, object]],
    concentration: list[dict[str, object]],
    summary: list[dict[str, object]],
    years: list[dict[str, object]],
) -> None:
    bucket_counts = Counter(clean(row.get("quality_bucket")) for row in audit_rows)
    year_counts = Counter(int(row["object_year"]) for row in audit_rows if clean(row.get("object_year")))
    high_studio = bucket_counts["independent_studio_work_candidate_high"]
    manual_studio = bucket_counts["independent_studio_manual_review"]
    high_studio_keys = {
        clean(row.get("studio_key"))
        for row in audit_rows
        if clean(row.get("quality_bucket")) == "independent_studio_work_candidate_high" and clean(row.get("studio_key"))
    }
    manual_studio_keys = {
        clean(row.get("studio_key"))
        for row in audit_rows
        if clean(row.get("quality_bucket")) == "independent_studio_manual_review" and clean(row.get("studio_key"))
    }
    stamp = bucket_counts["card_or_appendix_recent_commemorative_stamp_review"]
    event = bucket_counts["card_only_event_or_memory_material"]
    span = bucket_counts["exclude_span_or_profile"]

    lines = [
        "# Recent Design Object Quality Audit v1",
        "",
        "Scope: 2005-2025 capture records. Diagnostic only; no source rows are rewritten.",
        "",
        "## Summary",
        "",
        f"- Records in scope: {len(audit_rows)}",
        f"- Independent studio work candidates, high confidence: {high_studio}",
        f"- Unique high-confidence studio keys: {len(high_studio_keys)}",
        f"- Independent studio manual-review candidates: {manual_studio}",
        f"- Unique manual-review studio keys: {len(manual_studio_keys)}",
        f"- Post-2010 stamp/philatelic or commemorative review rows: {stamp}",
        f"- Event/photo/memory material card-only rows: {event}",
        f"- Span/profile/access-year exclusions in scope: {span}",
        f"- Concentration review rows: {len(concentration)}",
        "",
        "## Recent Year Counts",
        "",
    ]
    for year, count in sorted(year_counts.items()):
        lines.append(f"- {year}: {count}")
    lines.extend(["", "## Quality-Adjusted Recent Years", ""])
    for row in years:
        lines.append(
            f"- {row['year']}: primary={row['primary_design_candidates']}/{row['total_records']} "
            f"(primary_share={row['primary_share']}), stamp/event={row['stamp_event_share']}"
        )
    lines.extend(["", "## Quality Buckets", ""])
    for bucket, count in bucket_counts.most_common():
        lines.append(f"- {bucket}: {count}")
    lines.extend(["", "## Top Concentration Risks", ""])
    for row in concentration[:20]:
        lines.append(
            f"- {row['concentration_type']} `{row['key']}`: {row['record_count']} records; "
            f"studio={row['studio_candidate_count']}; stamp/event={row['stamp_or_event_count']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Post-2010 commemorative stamp records should be sampled or demoted before they inflate contemporary object coverage.",
            "- Event photographs and memory/documentation records should support research packets as cards/appendix material, not primary design objects.",
            "- Independent studio counts should use high-confidence studio candidates first; manual-review candidates need source/object verification before being treated as successful studio coverage.",
            "- Source/studio concentration rows should be capped or explicitly justified before another capture pass from the same source family.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = capture_rows()
    scoped_rows = [row for row in rows if (year := record_year(row)) is not None and START_YEAR <= year <= END_YEAR]
    source_counts = Counter(clean(row.get("source_name")) for row in scoped_rows)
    domain_counts = Counter(source_domain(row) for row in scoped_rows)

    studio_counts: Counter[str] = Counter()
    for row in scoped_rows:
        _, studio_key, _ = studio_signal(row)
        if studio_key:
            studio_counts[studio_key] += 1

    audit_rows: list[dict[str, object]] = []
    for row in scoped_rows:
        classified = classify_row(row, source_counts, domain_counts, studio_counts)
        if classified is not None:
            audit_rows.append(classified)

    studio_rows = [row for row in audit_rows if clean(row.get("quality_bucket")).startswith("independent_studio")]
    reclass_rows = [
        row
        for row in audit_rows
        if clean(row.get("quality_bucket")) in {"card_or_appendix_recent_commemorative_stamp_review", "card_only_event_or_memory_material"}
    ]
    concentration = concentration_rows(audit_rows)
    summary = summary_rows(audit_rows, concentration)
    years = year_summary_rows(audit_rows)

    write_csv(QUALITY_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(STUDIO_AUDIT, studio_rows, AUDIT_FIELDS)
    write_csv(RECLASS_QUEUE, reclass_rows, AUDIT_FIELDS)
    write_csv(CONCENTRATION_REVIEW, concentration, CONCENTRATION_FIELDS)
    write_csv(SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(YEAR_SUMMARY, years, YEAR_SUMMARY_FIELDS)
    write_report(audit_rows, concentration, summary, years)

    bucket_counts = Counter(clean(row.get("quality_bucket")) for row in audit_rows)
    print(f"records_in_scope={len(audit_rows)}")
    print(f"studio_high={bucket_counts['independent_studio_work_candidate_high']}")
    print(f"studio_manual={bucket_counts['independent_studio_manual_review']}")
    print(f"recent_stamp_review={bucket_counts['card_or_appendix_recent_commemorative_stamp_review']}")
    print(f"event_memory_card_only={bucket_counts['card_only_event_or_memory_material']}")
    print(f"span_profile_exclusions={bucket_counts['exclude_span_or_profile']}")
    print(f"concentration_review_rows={len(concentration)}")
    print(f"wrote {QUALITY_AUDIT.relative_to(ROOT)}")
    print(f"wrote {STUDIO_AUDIT.relative_to(ROOT)}")
    print(f"wrote {RECLASS_QUEUE.relative_to(ROOT)}")
    print(f"wrote {CONCENTRATION_REVIEW.relative_to(ROOT)}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {YEAR_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
