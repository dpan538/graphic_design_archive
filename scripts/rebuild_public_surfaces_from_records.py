from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from normalize_public_surfaces import normalize_payload


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
ACCESS_DATE = "2026-05-31"

RECORD_FILES = [
    DATA / "capture_batch_early_region_1830_1930_records.csv",
    DATA / "capture_batch_midcentury_1930_1970_records.csv",
    DATA / "capture_batch_midcentury_expansion_1931_1970_records.csv",
    DATA / "capture_batch_image_ready_1931_1970_records.csv",
    DATA / "capture_batch_gallica_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gallica_secondary_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_smithsonian_oa_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_digitalnz_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_digitalnz_postwar_image_ready_1945_2026_records.csv",
    DATA / "capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_wikimedia_commons_deep_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_postwar_commons_open_image_1945_2026_records.csv",
    DATA / "capture_batch_princeton_figgy_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gsu_contentdm_image_ready_1971_2026_records.csv",
    DATA / "capture_batch_cooperhewitt_graphql_image_ready_1830_2026_records.csv",
    DATA / "capture_batch_noncanonical_movement_commons_1930_2000_records.csv",
    DATA / "capture_batch_noncanonical_exact_sources_1970_2000_records.csv",
    DATA / "capture_batch_gap_noncanonical_image_text_1930_2000_records.csv",
    DATA / "capture_batch_late_period_coverage_1970_2026_records.csv",
    DATA / "capture_batch_protocol_item_1970_2026_records.csv",
    DATA / "capture_batch_source_breadth_1970_2026_records.csv",
    DATA / "capture_batch_independent_asia_1990_2026_records.csv",
    DATA / "capture_batch_edge_wordpress_1970_2026_records.csv",
    DATA / "capture_batch_edge_rss_html_1970_2026_records.csv",
    DATA / "capture_batch_loc_deep_image_ready_1931_1970_records.csv",
    DATA / "capture_batch_source_coverage_gap_1931_2026_records.csv",
    DATA / "capture_batch_edge_source_registry_context_1931_2026_records.csv",
    DATA / "capture_batch_nonmainstream_region_1990_2026_records.csv",
    DATA / "capture_batch_nonmainstream_source_profiles_1990_2026_records.csv",
    DATA / "capture_batch_nonmainstream_item_image_2026_records.csv",
]

PAYLOAD_PATHS = [
    GENERATED / "public_surfaces_v1.json",
    ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json",
    ROOT / "frontend" / "public" / "data" / "public_surface_mock_v0.json",
    DATA / "public_surface_mock_v0.json",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def fallback_summary(row: dict[str, str]) -> str:
    title = row.get("source_title") or "This record"
    source = row.get("source_name") or "the source"
    evidence = (
        row.get("editorial_summary")
        or row.get("source_description")
        or row.get("source_notes")
        or row.get("source_subjects")
        or row.get("source_object_type")
        or "metadata-only source record"
    )
    return mx.clean(f"{title} is retained as a source-linked record from {source}. {evidence}", max_chars=560)


def fill_enrichment_defaults(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code") or "IMG00"
    title = row.get("source_title") or row.get("source_object_type") or row.get("source_medium") or "Untitled source record"
    if not row.get("source_title"):
        row["source_title"] = title
    row.setdefault("image_expectation", "not_expected" if code == "IMG04" else "expected")
    row.setdefault("parser_status", "ok" if row.get("source_record_url") else "legacy")
    row.setdefault("display_mode", row.get("image_frame_behavior", ""))
    row.setdefault("ocr_or_excerpt", row.get("source_description", ""))
    row.setdefault("source_description_raw", row.get("source_description", ""))
    if not row.get("historical_context_note"):
        row["historical_context_note"] = (
            "Cumulative 1830-1970 archive-box record retained as evidence of "
            "graphic communication, print circulation, advertising, public "
            "information, or visual culture in the period under review."
        )
    if not row.get("classification_rationale"):
        row["classification_rationale"] = (
            "Folder placement is provisional and derived from title, date, "
            "medium, subject terms, source institution, geography, and provider "
            "context. The folder is a filter view rather than an ownership claim."
        )
    row.setdefault("uncertainty_note", "")
    row.setdefault(
        "citation_basis",
        f"{row.get('source_name', '')}. {row.get('source_title', '')}. "
        f"{row.get('source_record_url') or row.get('source_api_url')}. "
        f"Accessed {row.get('access_date') or mc.ACCESS_DATE}.",
    )
    row.setdefault("editorial_summary", fallback_summary(row))
    for field in mx.FIELDNAMES:
        row.setdefault(field, "")
    return row


def public_context_note(value: str) -> str:
    """Remove capture-phase ranges from public reading notes.

    Phase labels such as 1970-2026 describe the capture plan, not the object,
    movement, or source record. They may remain in raw provenance paths and
    internal reports, but not as public historical labels.
    """
    note = value or ""
    note = re.sub(r"\b(?:19|20)\d{2}-20\d{2}\s+protocol capture", "Protocol-source capture", note)
    note = re.sub(r"\b(?:19|20)\d{2}-20\d{2}\s+coverage-first capture", "Coverage-first capture", note)
    note = re.sub(r"\b(?:19|20)\d{2}-20\d{2}\s+capture", "Capture", note)
    return note


def public_visible_text(value: object) -> object:
    """Sanitize public strings while leaving non-string values untouched."""
    if not isinstance(value, str):
        return value
    text = public_context_note(value)
    text = re.sub(
        r"\balready captured\b",
        "previously collected",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\buntil item records are captured\b",
        "until item-level records are reviewed",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bCaptured\s+(?:in|through)\s+the\s+[^.]*?\bpass\s+for\s+(?:18|19|20)\d{2}[-–](?:19|20)\d{2}\.\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bCaptured\s+(?:in|through)\s+[^.]*?(?:1830[-–]1930|1931[-–]1970|1930[-–]1970|1970[-–]2026|1830[-–]2026)[^.]*\.\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bThis record is kept because the source exposes a thumbnail, source-hosted IIIF/viewer image, or open image candidate\.\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b(?:early|midcentury|late[- ]period)?\s*(?:1830[-–]1930|1930[-–]1970|1970[-–]2026)\s+capture rule\b",
        "Item-level source classification rule",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bCB-(?:EARLY|MIDCENTURY|LATE)[-_A-Z0-9]*(?:1830[-_]1930|1930[-_]1970|1970[-_]2026)\b",
        "CB-ITEM-LEVEL-CAPTURE",
        text,
    )
    text = re.sub(r"\s*;\s*;\s*", "; ", text)
    return text


def clean_text(value: object, max_chars: int = 1400) -> str:
    """Clean a text fragment without turning missing source evidence into copy."""
    return mx.clean(str(value or ""), max_chars=max_chars).strip()


def sentence_safe_clean(value: object, max_chars: int = 1400) -> str:
    """Clean and trim at a readable sentence boundary when possible."""
    text = clean_text(value, max_chars=max_chars + 180)
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    boundary = max(cut.rfind(". "), cut.rfind("; "), cut.rfind("。"), cut.rfind("；"))
    if boundary > max_chars * 0.58:
        return cut[: boundary + 1].rstrip()
    return cut.rstrip(" ,;:") + "..."


def clean_evidence_list(value: object, max_chars: int = 280) -> str:
    """Normalize catalogue list fragments for public prose.

    Many providers return list-like fields as semicolon strings with empty
    values, repeated generic labels, or `Unknown`. These are useful in raw
    tables but noisy in reading text.
    """
    text = clean_text(value, max_chars=max_chars)
    if not text:
        return ""
    text = re.sub(r"\{[^{}]*\}", "", text)
    text = re.sub(r"\b(?:None|null|nan)\b", "", text, flags=re.IGNORECASE)
    parts = re.split(r"\s*;\s*", text)
    cleaned: list[str] = []
    seen: set[str] = set()
    generic = {"", "unknown", "images", "image", "image/jpeg", "not stated", "n/a"}
    for part in parts:
        part = re.sub(r"\s+", " ", part).strip(" ,.;:/")
        key = part.lower()
        if key in generic or not part:
            continue
        if key not in seen:
            cleaned.append(part)
            seen.add(key)
    return mx.clean("; ".join(cleaned), max_chars=max_chars).strip()


def clean_evidence_prose(value: object, max_chars: int = 700) -> str:
    """Clean prose-like catalogue evidence while preserving source wording."""
    text = clean_text(value, max_chars=max_chars)
    if not text:
        return ""
    text = re.sub(r"\s*;\s*;\s*", "; ", text)
    text = re.sub(r"\bUnknown\b\s*;?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bImages?,\s*;\s*", "", text, flags=re.IGNORECASE)
    parts = re.split(r"\s*;\s*", text)
    cleaned: list[str] = []
    seen: set[str] = set()
    for part in parts:
        part = re.sub(r"\s+", " ", part).strip(" ,;")
        if not part:
            continue
        key = re.sub(r"\W+", "", part.lower())[:90]
        if key in seen:
            continue
        cleaned.append(part)
        seen.add(key)
    return sentence_safe_clean("; ".join(cleaned), max_chars=max_chars)


def public_form_label(row: dict[str, str], max_chars: int = 170) -> str:
    object_type = clean_evidence_list(row.get("source_object_type"), max_chars=120)
    medium = clean_evidence_list(row.get("source_medium"), max_chars=160)
    parts = []
    for part in (object_type, medium):
        if not part:
            continue
        low = part.lower()
        if "nombre total de vues" in low or "image/jpeg" in low:
            continue
        if part not in parts:
            parts.append(part)
    form = "; ".join(parts)
    low_blob = " ".join(parts).lower()
    if not form:
        return "source-linked graphic-design record"
    if "gallica visual/document record" in low_blob and ("affiche" in low_blob or "poster" in low_blob):
        return "poster or visual-document record"
    if len(form) > max_chars:
        form = form[:max_chars].rsplit(";", 1)[0].strip() or form[:max_chars].rstrip(" ,;") + "..."
    return form


def unique_fragments(*values: object, max_chars: int = 1800) -> str:
    fragments: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_text(value, max_chars=max_chars)
        if not text:
            continue
        key = re.sub(r"\W+", "", text.lower())[:120]
        if key and key not in seen:
            fragments.append(text)
            seen.add(key)
    return mx.clean(" ".join(fragments), max_chars=max_chars).strip()


GENERIC_SOURCE_TEXT = {
    "poster",
    "posters",
    "print",
    "prints",
    "image",
    "images",
    "photograph",
    "photographs",
    "correspondence",
    "old filing list",
    "wellcome work",
    "metadata-only source record",
}


def is_generic_source_text(value: object) -> bool:
    text = clean_text(value, max_chars=220).strip(" .;:/").lower()
    if not text:
        return True
    if text in GENERIC_SOURCE_TEXT:
        return True
    if re.fullmatch(r"(?:poster|posters|print|prints|image|images|correspondence)(?:\s+\d+\s+file)?", text):
        return True
    if len(text) < 32 and not re.search(r"\b(?:design|typograph|advert|lithograph|exhibition|publication|identity|politic|public|health|poster|press|magazine)\b", text):
        return True
    return False


def meaningful_source_text(*values: object, max_chars: int = 900) -> str:
    parts: list[str] = []
    for value in values:
        text = clean_text(value, max_chars=max_chars)
        if is_generic_source_text(text):
            continue
        parts.append(text)
    return unique_fragments(*parts, max_chars=max_chars)


def sentence_join(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def source_fact_sentence(row: dict[str, str]) -> str:
    date = clean_evidence_list(row.get("source_date_text"), max_chars=80)
    creator = clean_evidence_list(row.get("source_creator"), max_chars=160)
    place = clean_evidence_list(row.get("source_place_text") or row.get("source_place"), max_chars=140)
    form = public_form_label(row, max_chars=220)
    facts = []
    if date:
        facts.append(f"date evidence: {date}")
    if creator:
        facts.append(f"creator/attribution: {creator}")
    if place:
        facts.append(f"place evidence: {place}")
    if form and form != "source-linked graphic-design record":
        facts.append(f"form/medium: {form}")
    if not facts:
        return "The source provides limited item-level descriptive metadata; the record remains anchored by its source return and rights state."
    return f"The item metadata gives {('; '.join(facts))}."


def source_evidence_sentence(row: dict[str, str]) -> str:
    raw_text = meaningful_source_text(
        row.get("source_description"),
        row.get("ocr_or_excerpt"),
        row.get("source_notes"),
        row.get("source_subjects"),
        max_chars=640,
    )
    text = clean_evidence_prose(raw_text, max_chars=560)
    if not text:
        return (
            "The source does not provide extended descriptive prose; this support text therefore records the item-level evidence that can be verified."
        )
    if not re.search(r"[.!?。！？]$", text):
        text = f"{text}."
    return f"The source-side description adds this evidence: {text}"


def row_year(row: dict[str, str]) -> int | None:
    for key in ("date_start", "date_end"):
        value = row.get(key)
        if value and value.isdigit():
            return int(value)
    match = re.search(r"\b(18|19|20)\d{2}\b", row.get("source_date_text", ""))
    return int(match.group(0)) if match else None


def period_context(year: int | None) -> str:
    if year is None:
        return (
            "The item is kept in the archive as an undated or weakly dated record; "
            "its placement depends on source metadata, medium terms, and folder evidence rather than a fixed chronology."
        )
    if year < 1914:
        return (
            "Within the pre-1914 record set, this item belongs to the expansion of lithographic, typographic, "
            "periodical, advertising, and administrative print cultures that made modern graphic design legible before the profession was fully named."
        )
    if year < 1945:
        return (
            "Within the interwar record set, this item sits near the overlap of modernist composition, mass printing, "
            "public communication, commercial display, and politically charged visual circulation."
        )
    if year < 1971:
        return (
            "Within the postwar record set, this item supports reading graphic design through public information, advertising, "
            "institutional identity, exhibition culture, popular print, and the spread of offset and photographic reproduction."
        )
    if year < 2001:
        return (
            "Within the late twentieth-century record set, this item helps track phototypesetting, offset production, "
            "corporate identity, postmodern graphic language, cultural-political publishing, and early digital transitions."
        )
    return (
        "Within the contemporary record set, this item is treated as evidence of networked visual communication, "
        "independent publishing, digital identity systems, platform circulation, and the expansion of design archives beyond museum object records."
    )


def source_family_context(source_name: str) -> str:
    low = source_name.lower()
    if "gallica" in low or "bnf" in low:
        return "Gallica / BnF records are treated as bibliographic and visual-document evidence; the source return remains primary because image and rights statements vary by record."
    if "art institute of chicago" in low or low == "aic":
        return "Art Institute of Chicago records are treated as museum object evidence, useful for object metadata, creator attribution, dimensions, medium, and rights review."
    if "v&a" in low or "victoria and albert" in low:
        return "V&A records are treated as museum collection evidence, especially for object type, maker, material, collection context, and source-return verification."
    if "library of congress" in low or "loc" in low:
        return "Library of Congress records are treated as public collection evidence, especially for posters, printed ephemera, publication metadata, and rights statements."
    if "wellcome" in low:
        return "Wellcome records are treated as health, public-information, poster, and collection-context evidence; sparse catalogue prose should not be inflated into a finished design-history narrative."
    if "internet archive" in low:
        return "Internet Archive records are treated as source-return and reading evidence; OCR and scans must be cited back to the hosted item rather than absorbed as local holdings."
    if "chinese posters" in low:
        return "Chinese Posters records are treated as specialist archive evidence; repeated title/source rows must be grouped carefully so the archive does not imply duplicate independent sheets."
    if "wikimedia" in low or "commons" in low:
        return "Wikimedia Commons records are treated as rights-aware image supplements, not as original holding institutions; source and license chains must remain visible."
    if "smithsonian" in low:
        return "Smithsonian records are treated as open collection evidence when rights and media metadata support display."
    if "digitalnz" in low:
        return "DigitalNZ records are treated as regional aggregation evidence; member institutions and original source links remain more important than the aggregator label."
    if "cooper hewitt" in low:
        return "Cooper Hewitt records are treated as design-museum object evidence with strong metadata but record-level image and rights checks."
    if "cleveland" in low:
        return "Cleveland Museum records are treated as open-access museum evidence when object images and metadata can be verified."
    if "princeton" in low or "figgy" in low:
        return "Princeton / Figgy records are treated as library and special-collections evidence, useful for rare books, periodicals, and print culture records."
    if "gsu" in low or "georgia state" in low or "contentdm" in low:
        return "CONTENTdm and university archive records are treated as local-institution evidence; collection context and source-return links must stay visible."
    if "another graphic" in low:
        return "Independent design archive records are treated as contemporary source-context evidence and require careful filtering against portfolio, inspiration, and platform noise."
    return "This source is treated as an external holding or index; the archive records the link, metadata, image state, and citation basis without claiming possession of the material."


def medium_context(row: dict[str, str]) -> str:
    blob = " ".join(
        row.get(key, "")
        for key in ("source_object_type", "source_medium", "source_title", "source_subjects")
    ).lower()
    if "poster" in blob or "affiche" in blob:
        return "As a poster or display record, it is read through public address, scale, reproduction method, and the relation between image, lettering, and circulation site."
    if "periodical" in blob or "magazine" in blob or "journal" in blob or "newspaper" in blob:
        return "As a periodical or serial record, it is read through issue structure, editorial rhythm, advertising space, typographic hierarchy, and recurring publication format."
    if "book" in blob or "cover" in blob or "catalog" in blob or "catalogue" in blob:
        return "As a book, catalogue, or cover record, it is read through format, sequence, cover/interior relation, typography, and publication context."
    if "identity" in blob or "logo" in blob or "brand" in blob or "standard" in blob:
        return "As an identity or standards record, it is read through repeatable rules, system logic, institutional authorship, and the movement from single object to design program."
    if "typograph" in blob or "type" in blob or "font" in blob:
        return "As a typography record, it is read through letterform, setting technology, specimen logic, typographic hierarchy, and distribution."
    if "web" in blob or "interface" in blob or "digital" in blob:
        return "As a digital or interface record, it is read through screen context, platform circulation, updateability, and the relation between graphic form and software environment."
    return "The record is read as graphic communication evidence: a designed surface whose metadata, source link, image state, and classification help connect it to broader design-history structures."


def build_reading_summary(row: dict[str, str]) -> str:
    title = clean_text(row.get("source_title"), max_chars=260) or "Untitled source record"
    source = clean_text(row.get("source_name"), max_chars=120) or "external source"
    form = public_form_label(row)
    variants = (
        f"{title} is filed here as a {form} from {source}.",
        f"This leaf records {title} as a {form} sourced from {source}.",
        f"{title} is presented as a source-linked {form}; the holding evidence remains with {source}.",
        f"The archive keeps {title} as a traceable {form} connected back to {source}.",
    )
    intro = variants[stable_hash(row.get("capture_id") or title) % len(variants)]
    return sentence_safe_clean(
        sentence_join(
            [
                intro,
                source_fact_sentence(row),
                source_evidence_sentence(row),
                "The project keeps this as an index-and-return surface: the page gives enough context to read the record while the source link remains the evidentiary home.",
            ]
        ),
        max_chars=1100,
    )


def build_context_note(row: dict[str, str]) -> str:
    existing = public_visible_text(row.get("historical_context_note", ""))
    if re.search(r"\b(?:capture|captured|expansion pass|record retained as evidence|source exposes a thumbnail)\b", existing, re.IGNORECASE):
        existing = ""
    context = unique_fragments(
        existing,
        period_context(row_year(row)),
        medium_context(row),
        source_family_context(row.get("source_name", "")),
        max_chars=1300,
    )
    return context


def build_classification_note(row: dict[str, str]) -> str:
    existing = clean_text(row.get("classification_rationale"), max_chars=620)
    if re.search(
        r"Folder placement|Provisional folders|Provisional folder|captured|capture",
        existing,
        re.IGNORECASE,
    ):
        existing = ""
    folders = ", ".join(
        part
        for part in (
            row.get("region_folder"),
            row.get("theme_folder"),
            row.get("medium_folder"),
            row.get("movement_folder"),
        )
        if part
    )
    basis = (
        f" Folder evidence currently includes {folders}." if folders else ""
    )
    rule = (
        "Folder membership is a filter assignment, not a claim of ownership or a closed historical interpretation. "
        "It is derived from source title, object type, medium, date, place, subjects, source institution, and review notes."
    )
    return unique_fragments(existing, rule + basis, max_chars=1000)


def usable_editorial_summary(row: dict[str, str]) -> str:
    """Keep only editorial summaries that add more than boilerplate indexing text."""
    text = clean_text(row.get("editorial_summary"), max_chars=760)
    if not text:
        return ""
    low = text.lower()
    boilerplate_markers = (
        " is indexed from ",
        "is retained as a source-linked record from",
        "captured through ",
        "source record is dated",
        "source-provided descriptive text is limited",
        "enters the archive",
    )
    if any(marker in low for marker in boilerplate_markers):
        return ""
    return text


def usable_surface_summary(value: object) -> str:
    text = clean_text(value, max_chars=760)
    if not text:
        return ""
    low = text.lower()
    if any(
        marker in low
        for marker in (
            " is indexed from ",
            "enters the archive",
            "source record is dated",
            "source-provided text notes",
            "source-provided descriptive text is limited",
            "captured in ",
            "captured through ",
        )
    ):
        return ""
    if is_generic_source_text(text):
        return ""
    return text


def build_source_description(row: dict[str, str], fallback: str = "") -> str:
    source_text = clean_evidence_prose(
        meaningful_source_text(
        row.get("source_description"),
        row.get("ocr_or_excerpt"),
        row.get("source_description_raw"),
        fallback,
        max_chars=1050,
        ),
        max_chars=1050,
    )
    if source_text:
        return source_text
    return sentence_safe_clean(
        sentence_join(
            [
                "The source does not provide extended descriptive prose.",
                source_fact_sentence(row),
                "For this reason the archive treats the page primarily as source-linked evidence rather than as a finished narrative entry.",
            ]
        ),
        max_chars=780,
    )


def enrich_orphan_surface(surface: dict) -> None:
    """Give generated group/compound sheets a minimal reading layer.

    A few compound records are created after row-level capture and therefore do
    not have a capture row to enrich from. They should still read as archive
    surfaces rather than empty registers, while clearly staying at the level of
    grouped source context.
    """
    if surface.get("surfaceType") != "sheet":
        return
    if surface.get("readingTextLength"):
        return
    title = clean_text(surface.get("title"), max_chars=220) or "Grouped source record"
    source = clean_text(surface.get("sourceName"), max_chars=120) or "multiple source records"
    children = surface.get("compoundChildren") or []
    child_note = ""
    if children:
        child_titles = ", ".join(
            clean_text(child.get("title"), max_chars=80)
            for child in children[:4]
            if isinstance(child, dict) and child.get("title")
        )
        child_note = f" Child records include {child_titles}." if child_titles else ""
    summary = (
        f"{title} is retained as a grouped archive-box surface derived from {source}. "
        "It is not presented as a single object; it keeps related weak or repeated records together so they can be read as a source cluster."
        f"{child_note}"
    )
    context = (
        "Grouped surfaces are used when several records share a source family, visual form, title pattern, or uncertain item boundary. "
        "The grouping prevents thin duplicate sheets while preserving source-return evidence for later research."
    )
    surface["descriptionSummary"] = unique_fragments(surface.get("descriptionSummary"), summary, max_chars=1000)
    surface["historicalContextNote"] = unique_fragments(surface.get("historicalContextNote"), context, max_chars=900)
    surface["classificationRationale"] = unique_fragments(
        surface.get("classificationRationale"),
        "This page is a group-level filing surface. It should be reviewed before any child record is promoted to an independent main sheet.",
        max_chars=760,
    )
    surface["readingTextLength"] = len(
        " ".join(
            str(surface.get(key) or "")
            for key in ("descriptionSummary", "historicalContextNote", "classificationRationale")
        ).strip()
    )


def normalize_public_surface_visible_text(payload: dict) -> dict:
    """Clean visible sheet fields and table rows generated by older captures."""
    visible_fields = (
        "descriptionSummary",
        "sourceDescription",
        "sourceNotes",
        "sourceSubjects",
        "historicalContextNote",
        "classificationRationale",
        "uncertaintyNote",
        "citationBasis",
    )
    for surface in payload.get("surfaces", []):
        for field in visible_fields:
            if field in surface:
                surface[field] = public_visible_text(surface[field])
        for table in surface.get("tables", []):
            rows = []
            for row in table.get("rows", []):
                if not isinstance(row, list):
                    rows.append(row)
                    continue
                rows.append([public_visible_text(cell) for cell in row])
            table["rows"] = rows
    return payload


def public_folder_scope_note(folder: dict) -> str:
    """Describe folder function without leaking capture-phase ranges.

    Folders are filter views. Their member dates may span decades, especially
    for regions or long-running source families, but that span is not a claim
    about a movement's historical duration.
    """
    title = folder.get("title") or "this folder"
    folder_type = folder.get("type") or "folder"
    if folder_type == "region":
        return f"Geographic and transregional filter view for {title}. Member records are sorted by item-level date when known."
    if folder_type == "theme":
        return f"Theme filter view for {title}. Membership records research relevance; it is not a single historical period."
    if folder_type == "medium":
        return f"Medium filter view for {title}. Member records are filed by material, format, or production context."
    if folder_type == "movement":
        return f"Movement or formation filter for {title}. Dates shown on leaves are item dates, not a movement-duration claim."
    return f"Filter view for {title}. Member records are sorted by item-level date when known."


def normalize_public_folder_metadata(payload: dict) -> dict:
    """Clean public folder metadata after the shared payload builder runs."""
    for folder in payload.get("folders", []):
        folder["scopeNote"] = public_folder_scope_note(folder)
        if folder.get("type") == "movement":
            start = folder.get("dateStart")
            end = folder.get("dateEnd")
            if isinstance(start, int) and isinstance(end, int) and end - start > 35:
                folder["memberDateStart"] = start
                folder["memberDateEnd"] = end
                folder["dateStart"] = None
                folder["dateEnd"] = None
                folder["chronologyStatus"] = "member_date_span_not_movement_duration"
    return payload


def is_phase_or_collection_range(row: dict[str, str]) -> bool:
    start = row.get("date_start")
    end = row.get("date_end")
    if not (start and end and start.isdigit() and end.isdigit()):
        return False
    span = int(end) - int(start)
    date_text = row.get("source_date_text", "").strip()
    if date_text in {"1830-1930", "1930-1970", "1970-2026"}:
        return True
    if span <= 40:
        return False
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_object_type", ""),
            row.get("source_medium", ""),
            row.get("source_collection", ""),
            row.get("source_notes", ""),
            row.get("source_subjects", ""),
        ]
    ).lower()
    collection_terms = (
        "collection-level",
        "poster gallery",
        "gallery",
        "collection",
        "inventory",
        "biographical information",
        "source record",
        "repository text record",
    )
    return int(end) >= 2026 or any(term in blob for term in collection_terms)


def normalize_public_date_fields(row: dict[str, str]) -> dict[str, str]:
    """Prevent broad source/capture scopes from becoming object dates."""
    if not is_phase_or_collection_range(row):
        return row
    original = row.get("source_date_text") or f"{row.get('date_start')}-{row.get('date_end')}"
    row = dict(row)
    row["source_date_text"] = "source collection scope; object date not itemized"
    row["date_start"] = ""
    row["date_end"] = ""
    note = row.get("uncertainty_note", "")
    row["uncertainty_note"] = mx.clean(
        f"{note} Broad source range was treated as collection/source scope, not as the object date.",
        max_chars=520,
    ).strip()
    if not row.get("classification_rationale"):
        row["classification_rationale"] = (
            "This record represents collection/source context. It should resolve to bookmark, source dossier, "
            "or grouped support material unless item-level dates are later captured."
        )
    return row


def row_sort_year(row: dict[str, str]) -> int:
    """Sort long-range records by their terminal year.

    The archive's capture phases treat a record that spans decades as belonging
    to the phase where its end year lands. Keeping the same rule in the static
    payload prevents ranges such as 1965-1990 from being visually filed with
    the 1960s merely because their start year is early.
    """
    year = row.get("date_end") or row.get("date_start")
    return int(year) if year and year.isdigit() else 9999


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[tuple[str, str], dict[str, str]] = {}

    def score(row: dict[str, str]) -> tuple[int, int, int, int]:
        image_rank = {
            "IMG03": 5,
            "IMG02": 4,
            "IMG01": 3,
            "IMG04": 2,
            "IMG00": 1,
        }.get(row.get("image_presence_code") or "IMG00", 0)
        text_rank = max(
            len(row.get("editorial_summary") or ""),
            len(row.get("source_description") or ""),
            len(row.get("ocr_or_excerpt") or ""),
        )
        parsed_rank = 1 if row.get("parser_status") == "ok" else 0
        rights_rank = 1 if row.get("rights_review_required") == "true" else 0
        return image_rank, text_rank, parsed_rank, rights_rank

    for row in rows:
        key = (
            row.get("source_name", ""),
            row.get("source_identifier") or row.get("source_record_url") or row.get("source_title", ""),
        )
        current = best.get(key)
        if current is None or score(row) > score(current):
            best[key] = row
    return list(best.values())


def enhance_payload(payload: dict, rows: list[dict[str, str]]) -> dict:
    by_capture = {row.get("capture_id", ""): row for row in rows}
    payload["meta"] = {
        "generatedAt": ACCESS_DATE,
        "status": "generated",
        "note": "Generated cumulative 1830-1970 archive-box payload. Static export; not final publication data.",
    }
    for surface in payload.get("surfaces", []):
        row = by_capture.get(surface.get("sourceRecordId", ""))
        if not row:
            enrich_orphan_surface(surface)
            continue
        source_reading = build_reading_summary(row)
        context_note = build_context_note(row)
        classification_note = build_classification_note(row)
        source_description = build_source_description(row, surface.get("sourceDescription", ""))
        surface["descriptionSummary"] = unique_fragments(
            usable_editorial_summary(row),
            source_reading,
            usable_surface_summary(surface.get("descriptionSummary")),
            max_chars=1250,
        )
        surface["sourceDescription"] = source_description or source_reading
        surface["historicalContextNote"] = context_note
        surface["classificationRationale"] = classification_note
        surface["uncertaintyNote"] = clean_text(row.get("uncertainty_note"), max_chars=720)
        surface["citationBasis"] = clean_text(row.get("citation_basis"), max_chars=720)
        surface["readingTextLength"] = len(
            " ".join(
                value
                for value in (
                    surface.get("descriptionSummary", ""),
                    surface.get("sourceDescription", ""),
                    surface.get("historicalContextNote", ""),
                    surface.get("classificationRationale", ""),
                    surface.get("uncertaintyNote", ""),
                    surface.get("citationBasis", ""),
                )
                if value
            )
        )
        image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
        if image:
            image["expectation"] = row.get("image_expectation")
            image["parserStatus"] = row.get("parser_status")
            image["displayMode"] = row.get("display_mode") or row.get("image_frame_behavior")
            if row.get("image_presence_code") == "IMG00":
                image["placeholderText"] = (
                    row.get("image_state_review_note")
                    or "Image evidence remains source-linked; this project does not display a local copy."
                )
    return payload


def table_rows(surface: dict, kind: str) -> int:
    for table in surface.get("tables", []):
        if table.get("kind") == kind:
            return len(table.get("rows", []))
    return 0


def table_map(surface: dict) -> dict[str, dict]:
    return {
        table.get("kind", ""): table
        for table in surface.get("tables", [])
        if isinstance(table, dict)
    }


def table_row_value(surface: dict, kind: str, label_terms: tuple[str, ...]) -> str:
    terms = tuple(term.lower() for term in label_terms)
    for label, value in table_map(surface).get(kind, {}).get("rows", []):
        if any(term in str(label).lower() for term in terms):
            return str(value)
    return ""


def reading_length(surface: dict) -> int:
    return len(
        " ".join(
            str(surface.get(key) or "")
            for key in (
                "descriptionSummary",
                "sourceDescription",
                "historicalContextNote",
                "sourceNotes",
                "sourceSubjects",
            )
        ).strip()
    )


def stable_hash(value: str) -> int:
    h = 2166136261
    for char in value:
        h ^= ord(char)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def appendix_rule(surface: dict) -> tuple[str | None, list[str]]:
    """Return the production AX layout and reasons for one appendix packet.

    The rule mirrors `frontend/src/lib/paginate.ts`: a surface gets at most one
    appendix packet, selected by evidence priority rather than generic table
    overflow. Text leaves stay reading/image-only; evidence ledgers move here.
    """
    if surface.get("surfaceType") != "sheet":
        return None, []

    tables = table_map(surface)
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    image_state = image.get("state")
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    child_count = len(surface.get("compoundChildren") or [])
    total_rows = sum(len(table.get("rows", [])) for table in tables.values())
    source_links = table_row_value(surface, "CITATIONS", ("source links", "source urls", "source url"))
    multi_source_list = source_links.count("http://") + source_links.count("https://") >= 2
    protocol_text = " ".join(
        str(surface.get(key) or "")
        for key in (
            "historicalContextNote",
            "classificationRationale",
            "citationBasis",
        )
    )
    rights = surface.get("rights") if isinstance(surface.get("rights"), dict) else {}
    protocol_text = f"{protocol_text} {rights.get('label', '')}"
    surface_hash = stable_hash(surface.get("surfaceId", ""))
    protocol_low = protocol_text.lower()
    explicit_protocol_note = any(
        term in protocol_low
        for term in ("manual review", "protocol-sensitive", "source-only", "source only", "suppress", "sensitive")
    )
    source_policy_context = image_state == "IMG02" and reading_length(surface) >= 1500 and surface_hash % 4 == 0
    display_policy = rights.get("displayPolicy") or rights.get("display_policy") or ""
    review_gates = surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}
    rights_reviewed = bool(review_gates.get("rightsReviewed"))
    non_blank_rights_evidence = (
        image_state in {"IMG01", "IMG02", "IMG03"}
        and (display_policy != "open_image_frame" or not rights_reviewed)
        and reading_length(surface) >= 900
        and surface_hash % 6 == 0
    )

    if image_state == "IMG00":
        return "AX01.rights", ["rights/image evidence continuation"]
    if multi_source_list or child_count >= 3:
        return "AX02.citation", ["source/citation register"]
    if table_rows(surface, "RELATIONS") > 4 or len(folders) >= 4 or child_count > 0:
        return "AX03.relations", ["relations/classification appendix"]
    if non_blank_rights_evidence:
        return "AX01.rights", ["rights/image display evidence continuation"]
    if explicit_protocol_note or source_policy_context:
        return "AX04.context", ["protocol/context packet"]
    if total_rows >= 30 and reading_length(surface) >= 900 and surface_hash % 5 == 0:
        layout = "AX06.typed-index" if surface_hash % 3 == 0 else "AX05.statement"
        return layout, ["source verification dossier"]
    return None, []


def attach_structural_collections(payload: dict) -> dict:
    """Expose non-sheet archive structures in the static payload.

    The frontend can still paginate these virtually, but the data layer should
    explicitly acknowledge reading notes, true bookmark candidates, appendix
    candidates, and filing/register records so the archive does not collapse
    into a flat list of sheets.
    """
    folders = payload.get("folders", [])
    surfaces = payload.get("surfaces", [])
    by_surface = {surface.get("surfaceId"): surface for surface in surfaces}

    folder_reading_notes = [
        {
            "readingNoteId": f"RN-{folder.get('folderId')}",
            "noteScope": "folder",
            "folderId": folder.get("folderId"),
            "type": folder.get("type"),
            "title": folder.get("title"),
            "dateStart": folder.get("dateStart"),
            "dateEnd": folder.get("dateEnd"),
            "surfaceCount": len(folder.get("surfaceIds", [])),
            "scopeNote": folder.get("scopeNote"),
            "displayRule": "one reading-note leaf after folder register",
        }
        for folder in folders
    ]

    long_surface_reading_notes = []
    for surface in surfaces:
        role = surface.get("publicationRole") or surface.get("surfaceDisposition") or ""
        layout_hint = surface.get("layoutHint") or ""
        is_support_packet = role in {
            "support_packet_appendix_text",
            "merge_candidate_support_packet",
            "thin_visual_support_packet",
        } or layout_hint in {"support_packet", "merge_candidate"}
        if surface.get("surfaceType") != "sheet" or is_support_packet:
            continue
        if reading_length(surface) < 3200:
            continue
        image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
        long_surface_reading_notes.append(
            {
                "readingNoteId": f"RN-{surface.get('surfaceId')}",
                "noteScope": "surface",
                "surfaceId": surface.get("surfaceId"),
                "title": surface.get("title"),
                "displayNumber": surface.get("provisionalDisplayNumber"),
                "dateStart": surface.get("dateStart"),
                "dateEnd": surface.get("dateEnd"),
                "sourceName": surface.get("sourceName"),
                "sourceUrl": surface.get("sourceUrl"),
                "imageState": image.get("state"),
                "readingLength": reading_length(surface),
                "scopeNote": "Long main-sheet reading note candidate; use as an interpretive guide before export or dossier reading.",
                "displayRule": "attach to the corresponding main-sheet dossier, not to every folder view",
            }
        )

    payload["readingNotes"] = folder_reading_notes + long_surface_reading_notes
    payload["bookmarks"] = []

    appendix_candidates = []
    for surface in surfaces:
        layout_id, reasons = appendix_rule(surface)
        if reasons:
            total_rows = sum(len(table.get("rows", [])) for table in surface.get("tables", []))
            appendix_candidates.append(
                {
                    "appendixId": f"APP-{surface.get('surfaceId')}",
                    "surfaceId": surface.get("surfaceId"),
                    "title": surface.get("title"),
                    "displayNumber": surface.get("provisionalDisplayNumber"),
                    "layoutId": layout_id,
                    "reasons": reasons,
                    "tableRows": total_rows,
                }
            )
    payload["appendices"] = appendix_candidates

    payload["registrationCards"] = [
        {
            "registrationId": f"REGCARD-{folder.get('folderId')}",
            "folderId": folder.get("folderId"),
            "type": folder.get("type"),
            "title": folder.get("title"),
            "memberPages": [
                {
                    "surfaceId": sid,
                    "displayNumber": (by_surface.get(sid) or {}).get("provisionalDisplayNumber"),
                    "title": (by_surface.get(sid) or {}).get("title"),
                }
                for sid in folder.get("surfaceIds", [])
                if sid in by_surface
            ],
            "displayRule": "folder membership ledger; folder is a filter, not a container",
        }
        for folder in folders
    ]
    return payload


def surface_is_support_packet(surface: dict) -> bool:
    role = surface.get("publicationRole") or surface.get("surfaceDisposition") or ""
    layout_hint = surface.get("layoutHint") or ""
    return role in {
        "support_packet_appendix_text",
        "merge_candidate_support_packet",
        "thin_visual_support_packet",
    } or layout_hint in {"support_packet", "merge_candidate"}


def surface_base_page_type(surface: dict) -> str:
    if surface.get("surfaceType") == "card":
        return "card"
    if surface_is_support_packet(surface):
        return "subsheet"
    return "main_sheet"


def surface_requires_text_page(surface: dict) -> bool:
    """Every sheet-level dossier member needs a readable text layer.

    IMG04 may render as a text-only first page in the current frontend, but the
    research-dossier contract still marks it as text-bearing so export/thumbnail
    tools can distinguish evidence prose from table-led pages.
    """
    return surface.get("surfaceType") == "sheet"


def surface_requires_slip(surface: dict) -> bool:
    if surface.get("surfaceType") != "card":
        return False
    text = " ".join(
        str(surface.get(key) or "")
        for key in ("descriptionSummary", "sourceDescription", "sourceNotes", "citationBasis")
    )
    evidence_rows = 0
    for table in surface.get("tables", []):
        if table.get("kind") in {"SOURCE", "RIGHTS", "CITATIONS"}:
            evidence_rows += len(table.get("rows", []))
    return len(text) >= 320 and evidence_rows <= 10


def dossier_page(surface: dict, page_type: str, index: int, layout_id: str | None = None) -> dict:
    return {
        "pageId": f"{surface.get('surfaceId')}#{page_type}-{index:02d}",
        "pageType": page_type,
        "surfaceId": surface.get("surfaceId"),
        "displayNumber": surface.get("provisionalDisplayNumber"),
        "title": surface.get("title"),
        "imageState": (surface.get("image") or {}).get("state", "IMG00"),
        "layoutId": layout_id,
        "exportable": True,
        "rightsState": (surface.get("rights") or {}).get("state"),
        "sourceName": surface.get("sourceName"),
        "sourceUrl": surface.get("sourceUrl"),
    }


def surface_dossier_pages(surface: dict) -> list[dict]:
    pages: list[dict] = [dossier_page(surface, surface_base_page_type(surface), 1)]
    next_index = 2
    if surface_requires_text_page(surface):
        pages.append(dossier_page(surface, "text_page", next_index))
        next_index += 1
    layout_id, reasons = appendix_rule(surface)
    if layout_id:
        page = dossier_page(surface, "appendix", next_index, layout_id)
        page["appendixReasons"] = reasons
        pages.append(page)
        next_index += 1
    if surface_requires_slip(surface):
        pages.append(dossier_page(surface, "slip", next_index))
    return pages


def dossier_source_scope(surface: dict) -> str:
    if surface.get("compoundChildren"):
        return "compound_or_series_cluster"
    if surface_is_support_packet(surface):
        return "support_packet"
    if surface.get("surfaceType") == "card":
        return "card_record"
    return "single_anchor_record"


def build_research_dossiers(payload: dict) -> dict:
    """Attach exportable research-unit packets to the public payload.

    This is intentionally conservative: it does not merge nearby works merely
    because they share a folder, period, or visual similarity. Broad grouping
    must come from a linkage pass with evidence. Until then, every strong record
    becomes its own dossier anchor, and compound/group sheets expose their child
    evidence as part of the same dossier.
    """
    dossiers: list[dict] = []
    for surface in payload.get("surfaces", []):
        pages = surface_dossier_pages(surface)
        children = surface.get("compoundChildren") or []
        for child_index, child in enumerate(children, start=1):
            pages.append(
                {
                    "pageId": f"{surface.get('surfaceId')}#child-{child_index:02d}",
                    "pageType": "child_source_record",
                    "surfaceId": surface.get("surfaceId"),
                    "displayNumber": surface.get("provisionalDisplayNumber"),
                    "title": child.get("title"),
                    "imageState": child.get("imageState", "IMG00"),
                    "layoutId": "child.source-record",
                    "exportable": True,
                    "rightsState": "member_record_rights",
                    "sourceName": child.get("sourceName"),
                    "sourceUrl": child.get("sourceUrl"),
                }
            )
        dossiers.append(
            {
                "dossierId": f"DOS-{surface.get('surfaceId')}",
                "anchorSurfaceId": surface.get("surfaceId"),
                "anchorType": surface_base_page_type(surface),
                "sourceScope": dossier_source_scope(surface),
                "title": surface.get("title"),
                "dateStart": surface.get("dateStart"),
                "dateEnd": surface.get("dateEnd"),
                "folderIds": [folder.get("folderId") for folder in surface.get("folders", [])],
                "pageCount": len(pages),
                "pageSequence": pages,
                "exportPolicy": {
                    "selectablePages": True,
                    "pdfAllowed": True,
                    "stampEveryPage": True,
                    "includeRightsPage": True,
                    "localImageCopyAllowed": False,
                },
                "groupingBasis": (
                    "single record anchor; no inferred historical grouping"
                    if not children
                    else "compound/group surface created from repeated or source-generic records"
                ),
            }
        )
    payload["researchDossiers"] = dossiers
    return payload


def main() -> None:
    rows: list[dict[str, str]] = []
    for path in RECORD_FILES:
        rows.extend(read_rows(path))
    rows = dedupe_rows([normalize_public_date_fields(fill_enrichment_defaults(row)) for row in rows])
    rows.sort(key=lambda r: (row_sort_year(r), r.get("source_title", "")))

    payload = mc.build_public_payload(rows)
    payload = enhance_payload(payload, rows)
    payload = normalize_payload(payload)
    payload = normalize_public_surface_visible_text(payload)
    payload = normalize_public_folder_metadata(payload)
    payload = attach_structural_collections(payload)
    payload = build_research_dossiers(payload)

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in PAYLOAD_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    image_counter = Counter(surface.get("image", {}).get("state", "IMG00") for surface in payload.get("surfaces", []))
    source_visible = sum(image_counter[state] for state in ("IMG01", "IMG02", "IMG03"))
    publication_weights = {
        "IMG03": 0.9,
        "IMG02": 0.55,
        "IMG01": 0.3,
        "IMG00": 0.0,
        "IMG04": 0.0,
    }
    weighted_ready = sum(
        publication_weights.get(surface.get("image", {}).get("state", "IMG00"), 0.0)
        for surface in payload.get("surfaces", [])
    )
    total = len(payload.get("surfaces", []))
    source_visible_coverage = round(source_visible / total * 100, 2) if total else 0
    weighted_coverage = round(weighted_ready / total * 100, 2) if total else 0
    print(f"rows={len(rows)}")
    print(f"surfaces={total}")
    print(f"folders={len(payload.get('folders', []))}")
    print(f"image_states={dict(sorted(image_counter.items()))}")
    print(f"source_visible_image_ready={source_visible}/{total} ({source_visible_coverage}%)")
    print(f"weighted_publication_image_score={round(weighted_ready, 2)}/{total} ({weighted_coverage}%)")


if __name__ == "__main__":
    main()
