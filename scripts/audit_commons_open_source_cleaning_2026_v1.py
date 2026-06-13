#!/usr/bin/env python3
"""Audit recent Commons open-source expansion batches for release readiness.

This is a cleaning/review pass, not a destructive rewrite. It reads recent
Commons open capture CSVs, scores authority and release-readiness, flags weak or
duplicate records, and writes review queues. It does not download images, query
external services, or create a cleaned `*_records.csv` that could be
accidentally double-counted by the public-surface rebuild.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

INPUT_FILES = [
    DATA / "capture_batch_commons_open_category_tree_image_2026_v1_records.csv",
    DATA / "capture_batch_commons_open_region_balance_image_2026_v3_records.csv",
    DATA / "capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv",
    DATA / "capture_batch_commons_open_controlled_expansion_2026_v1_records.csv",
    DATA / "capture_batch_commons_open_publication_category_tree_2026_v1_records.csv",
]

AUDIT_CSV = DATA / "commons_open_source_cleaning_audit_2026_v1.csv"
SUMMARY_CSV = DATA / "commons_open_source_cleaning_summary_2026_v1.csv"
REPORT = DOCS / "COMMONS_OPEN_SOURCE_CLEANING_AUDIT_2026_v1.md"

REQUIRED_FIELDS = [
    "source_identifier",
    "source_record_url",
    "source_title",
    "date_start",
    "date_end",
    "source_place_text",
    "source_object_type",
    "source_rights_text",
    "rights_basis",
    "image_presence_code",
    "image_url_detected",
    "access_date",
    "citation_basis",
]

WEAK_GRAPHIC_TERMS = (
    "poster session",
    "conference poster",
    "scientific poster",
    "poster presentation",
    "at the poster",
    "with poster",
    "standing next to poster",
    "calendar page",
    "copyright status unknown",
    "rights status is unknown",
    "unknown copyright status",
    "flag of ",
    "coat of arms",
    "locator map",
    "blank map",
    "commons-logo",
)

OBJECT_FAMILY_TERMS = [
    ("political_poster", ("political poster", "propaganda poster", "campaign poster")),
    ("film_poster", ("film poster", "movie poster", "cinema poster")),
    ("travel_poster", ("travel poster", "railway poster", "tourism poster")),
    ("poster", ("poster", "placard", "plakat", "affiche")),
    ("postage_stamp", ("postage stamp", "stamp", "meter stamp")),
    ("book_cover", ("book cover", "cover of", "dust jacket")),
    ("magazine_cover", ("magazine cover", "journal cover")),
    ("advertising", ("advertisement", "advertising", "publicity", "trade card")),
    ("label_packaging", ("label", "packaging", "package", "matchbox")),
    ("brochure_pamphlet", ("brochure", "pamphlet", "leaflet", "flyer")),
    ("typography_identity", ("typography", "type specimen", "letterhead", "logo", "identity")),
]

INSTITUTION_HINTS = (
    "museum",
    "library",
    "archive",
    "archives",
    "university",
    "college",
    "school",
    "academy",
    "institute",
    "gallery",
    "gov",
    "national",
)

STRUCTURED_CATALOG_DOMAINS = (
    "colnect.com",
    "loc.gov",
    "si.edu",
    "smithsonian",
    "bnf.fr",
    "gallica.bnf.fr",
    "europeana.eu",
    "digitalnz.org",
    "collection.cooperhewitt.org",
    "metmuseum.org",
    "vam.ac.uk",
    "getty.edu",
    "archive.org",
    "dpla",
    "worldcat",
)

AUDIT_FIELDS = [
    "batch_file",
    "capture_id",
    "source_identifier",
    "source_title",
    "source_record_url",
    "image_url_detected",
    "source_place_text",
    "date_start",
    "date_end",
    "object_family",
    "authority_level",
    "authority_score",
    "release_cleaning_status",
    "review_reasons",
    "source_collection",
    "source_rights_text",
    "rights_basis",
]


def clean(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(
        r"(?i)(#|[?&])(?:id_token|access_token|refresh_token|auth_token|token|session|cookie|password|secret)=[^\s\"'<>;,]*",
        "",
        text,
    )


def lower(value: object) -> str:
    return clean(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    for row in rows:
        row["_batch_file"] = path.name
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def period_band(row: dict[str, str]) -> str:
    year = safe_year(row.get("date_end")) or safe_year(row.get("date_start"))
    if year is None:
        return "undated_or_invalid"
    if year < 1940:
        return "pre_1940"
    if year <= 1970:
        return "1940_1970"
    if year <= 2000:
        return "1970_2000"
    return "2000_2026"


def object_family(row: dict[str, str]) -> str:
    blob = lower(" ".join([row.get("source_object_type", ""), row.get("source_title", ""), row.get("source_subjects", "")]))
    for family, terms in OBJECT_FAMILY_TERMS:
        if any(term in blob for term in terms):
            return family
    return "other_graphic_candidate"


def domain(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    if not re.match(r"^https?://|^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/|$)", text):
        return ""
    try:
        parsed = urlparse(text if re.match(r"^https?://", text) else "https://" + text)
    except ValueError:
        return ""
    return parsed.netloc.lower().removeprefix("www.")


def authority_level(row: dict[str, str]) -> str:
    collection = lower(row.get("source_collection"))
    notes = lower(" ".join([row.get("source_notes", ""), row.get("source_subjects", ""), row.get("citation_basis", "")]))
    collection_domain = domain(row.get("source_collection"))
    record_domain = domain(row.get("source_record_url"))
    if any(hint in collection for hint in INSTITUTION_HINTS) or any(hint in notes for hint in INSTITUTION_HINTS):
        return "institutional_or_education_context"
    if any(known in collection_domain for known in STRUCTURED_CATALOG_DOMAINS):
        return "structured_catalog_source_link"
    if any(known in notes for known in STRUCTURED_CATALOG_DOMAINS):
        return "structured_catalog_source_link"
    if "commons.wikimedia.org" in record_domain:
        if collection and collection not in {"wikimedia commons", "commons"}:
            return "commons_open_file_with_extra_source"
        return "commons_platform_only"
    return "source_platform_unclear"


def duplicate_keys(rows: list[dict[str, str]]) -> tuple[set[str], set[str], set[str], set[str]]:
    ids = Counter(clean(row.get("source_identifier")) for row in rows if clean(row.get("source_identifier")))
    urls = Counter(clean(row.get("source_record_url")).lower() for row in rows if clean(row.get("source_record_url")))
    images = Counter(clean(row.get("image_url_detected")).lower() for row in rows if clean(row.get("image_url_detected")))
    new_files = {path.name for path in INPUT_FILES if path.exists()}
    corpus_ids: set[str] = set()
    corpus_images: set[str] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if path.name in new_files or "cell_assignments" in path.name:
            continue
        for row in read_csv(path):
            if clean(row.get("source_identifier")):
                corpus_ids.add(clean(row.get("source_identifier")))
            if clean(row.get("source_record_url")):
                corpus_ids.add(clean(row.get("source_record_url")).lower())
            if clean(row.get("image_url_detected")):
                corpus_images.add(clean(row.get("image_url_detected")).lower())
    return (
        {key for key, count in ids.items() if count > 1} | {key for key, count in urls.items() if count > 1},
        {key for key, count in images.items() if count > 1},
        corpus_ids,
        corpus_images,
    )


def has_open_rights(row: dict[str, str]) -> bool:
    if clean(row.get("image_presence_code")) != "IMG03":
        return False
    blob = lower(" ".join([row.get("source_rights_text", ""), row.get("rights_basis", ""), row.get("image_presence_basis", "")]))
    return any(term in blob for term in ("public domain", "cc0", "creative commons", "cc by", "cc-by", "open-license"))


def weak_graphic(row: dict[str, str]) -> bool:
    blob = lower(" ".join([row.get("source_title", ""), row.get("source_description", ""), row.get("source_notes", ""), row.get("source_subjects", "")]))
    if "poster session" in blob and "poster" in blob:
        return True
    return any(term in blob for term in WEAK_GRAPHIC_TERMS)


def authority_score(
    row: dict[str, str],
    repeated_ids: set[str],
    repeated_images: set[str],
    corpus_ids: set[str],
    corpus_images: set[str],
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    source_id = clean(row.get("source_identifier"))
    source_url = clean(row.get("source_record_url")).lower()
    image_url = clean(row.get("image_url_detected")).lower()
    text_blob = clean(" ".join([row.get("source_description", ""), row.get("source_notes", ""), row.get("source_subjects", ""), row.get("ocr_or_excerpt", "")]))
    family = object_family(row)
    level = authority_level(row)

    missing = [field for field in REQUIRED_FIELDS if not clean(row.get(field))]
    if missing:
        reasons.append("missing_required:" + "|".join(missing[:5]))
    else:
        score += 10

    if source_url.startswith("https://commons.wikimedia.org/wiki/file:"):
        score += 12
    else:
        reasons.append("nonstandard_commons_source_url")
    if image_url.startswith("https://upload.wikimedia.org/"):
        score += 10
    else:
        reasons.append("missing_or_noncommons_image_url")
    if has_open_rights(row):
        score += 22
    else:
        reasons.append("open_rights_evidence_missing")
    if safe_year(row.get("date_start")) and safe_year(row.get("date_end")):
        score += 10
    else:
        reasons.append("date_invalid_or_missing")
    if family != "other_graphic_candidate":
        score += 10
    else:
        reasons.append("object_family_unclear")
    if len(text_blob) >= 120:
        score += 8
    elif len(text_blob) >= 50:
        score += 4
    else:
        reasons.append("thin_source_text")
    if level == "institutional_or_education_context":
        score += 12
    elif level == "structured_catalog_source_link":
        score += 10
    elif level == "commons_open_file_with_extra_source":
        score += 7
    elif level == "commons_platform_only":
        score += 3
        reasons.append("platform_only_authority")
    else:
        reasons.append("authority_unclear")

    if weak_graphic(row):
        score -= 30
        reasons.append("weak_graphic_or_event_photo_signal")
    if source_id in repeated_ids or source_url in repeated_ids or source_id in corpus_ids or source_url in corpus_ids:
        score -= 35
        reasons.append("duplicate_source_identifier_or_url")
    if image_url in repeated_images or image_url in corpus_images:
        score -= 35
        reasons.append("duplicate_image_url")

    return max(0, min(100, score)), reasons


def release_status(score: int, reasons: list[str]) -> str:
    reason_text = ";".join(reasons)
    if "duplicate_" in reason_text:
        return "quarantine_duplicate_review"
    if "weak_graphic_or_event_photo_signal" in reason_text:
        return "review_weak_graphic_evidence"
    if "missing_required:" in reason_text or "open_rights_evidence_missing" in reason_text:
        return "review_release_contract"
    if score >= 72:
        return "release_ready"
    if score >= 58:
        return "authority_review"
    return "manual_review"


def main() -> None:
    rows: list[dict[str, str]] = []
    for path in INPUT_FILES:
        rows.extend(read_csv(path))
    repeated_ids, repeated_images, corpus_ids, corpus_images = duplicate_keys(rows)

    audit_rows: list[dict[str, object]] = []
    for row in rows:
        score, reasons = authority_score(row, repeated_ids, repeated_images, corpus_ids, corpus_images)
        audit_rows.append(
            {
                "batch_file": row.get("_batch_file", ""),
                "capture_id": row.get("capture_id", ""),
                "source_identifier": row.get("source_identifier", ""),
                "source_title": row.get("source_title", ""),
                "source_record_url": row.get("source_record_url", ""),
                "image_url_detected": row.get("image_url_detected", ""),
                "source_place_text": row.get("source_place_text", ""),
                "date_start": row.get("date_start", ""),
                "date_end": row.get("date_end", ""),
                "object_family": object_family(row),
                "authority_level": authority_level(row),
                "authority_score": score,
                "release_cleaning_status": release_status(score, reasons),
                "review_reasons": "; ".join(reasons),
                "source_collection": row.get("source_collection", ""),
                "source_rights_text": row.get("source_rights_text", ""),
                "rights_basis": row.get("rights_basis", ""),
            }
        )

    status_counts = Counter(str(row["release_cleaning_status"]) for row in audit_rows)
    family_counts = Counter(str(row["object_family"]) for row in audit_rows)
    authority_counts = Counter(str(row["authority_level"]) for row in audit_rows)
    period_counts = Counter(period_band(row) for row in rows)
    macro_counts = Counter(clean(row.get("source_place_text")).split(" / ")[0] or "unmapped" for row in rows)
    batch_counts = Counter(str(row["batch_file"]) for row in audit_rows)
    review_reasons = Counter()
    for row in audit_rows:
        for reason in str(row["review_reasons"]).split("; "):
            if reason:
                review_reasons[reason.split(":")[0]] += 1

    summary_rows: list[dict[str, object]] = []
    for metric, counter in [
        ("status", status_counts),
        ("object_family", family_counts),
        ("authority_level", authority_counts),
        ("period", period_counts),
        ("macro_region", macro_counts),
        ("batch_file", batch_counts),
        ("review_reason", review_reasons),
    ]:
        for value, count in counter.most_common():
            summary_rows.append({"metric": metric, "value": value, "count": count})

    write_csv(AUDIT_CSV, audit_rows, AUDIT_FIELDS)
    write_csv(SUMMARY_CSV, summary_rows, ["metric", "value", "count"])

    total = len(audit_rows)
    ready = status_counts.get("release_ready", 0)
    lines = [
        "# Commons Open Source Cleaning Audit 2026 v1",
        "",
        "Scope: recent Commons open-source expansion batches only. This audit generates review queues and does not modify source records.",
        "",
        "## Summary",
        "",
        f"- Records audited: {total}",
        f"- Release-ready records: {ready} ({(ready / total * 100):.2f}% if total else 0)",
        f"- Duplicate/review records: {total - ready}",
        f"- Duplicate source keys inside new batches: {len(repeated_ids)}",
        f"- Duplicate image URLs inside new batches: {len(repeated_images)}",
        "",
        "## Status Distribution",
        "",
    ]
    for key, count in status_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Authority Distribution", ""])
    for key, count in authority_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Object Family Distribution", ""])
    for key, count in family_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Period Distribution", ""])
    for key, count in period_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Top Review Reasons", ""])
    for key, count in review_reasons.most_common(20):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This audit does not download images or raw API payloads.",
            "- It does not create a cleaned `*_records.csv`; this avoids accidental double-counting by rebuild scripts.",
            "- `release_ready` means the row passes automated metadata, rights, duplicate, object-family, and authority-shape checks. It is still a source-linked Commons record and remains reviewable.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"records_audited={total}")
    print(f"release_ready={ready}")
    print(f"status_counts={dict(status_counts)}")
    print(f"authority_counts={dict(authority_counts)}")
    print(f"object_family_counts={dict(family_counts)}")


if __name__ == "__main__":
    main()
