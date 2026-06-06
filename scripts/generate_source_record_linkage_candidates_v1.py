#!/usr/bin/env python3
"""Generate provenance-first linkage candidates from capture records.

This pass works below the public-surface layer. It does not merge records and it
does not decide final UI surfaces. It identifies where multiple capture rows may
belong to one research unit: exact source records, duplicate visual evidence,
same-title records, and source-series clusters.
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

GROUPS = DATA / "source_record_linkage_candidates_v1.csv"
MEMBERS = DATA / "source_record_linkage_memberships_v1.csv"
REPORT = DOCS / "SOURCE_RECORD_LINKAGE_CANDIDATES_v1.md"

GROUP_FIELDS = [
    "linkage_group_id",
    "linkage_type",
    "linkage_key",
    "confidence",
    "relation_label",
    "member_count",
    "proposed_anchor_capture_id",
    "proposed_anchor_title",
    "anchor_completeness_proxy",
    "date_span",
    "source_names",
    "image_states",
    "period_bands",
    "recommended_group_action",
    "coverage_gap_flags",
    "evidence_basis",
    "member_capture_uids",
]

MEMBER_FIELDS = [
    "linkage_group_id",
    "capture_uid",
    "capture_id",
    "capture_file",
    "membership_role",
    "relation_label",
    "membership_confidence",
    "source_name",
    "source_identifier",
    "source_title",
    "date_text",
    "period_band",
    "image_state",
    "completeness_proxy",
    "source_record_url",
    "image_url_detected",
]

STOP_STEMS = {
    "untitled",
    "poster",
    "affiche",
    "graphic design",
    "commercial art",
    "source record",
    "image",
    "unknown",
}


def clean(value: str | None) -> str:
    return (value or "").strip()


def lower(value: str | None) -> str:
    return clean(value).lower()


def norm(value: str | None) -> str:
    value = lower(value)
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def safe_int(value: str | None) -> int | None:
    value = clean(value)
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def capture_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_uid: set[str] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if "cell_assignments" in path.name:
            continue
        for row in read_csv(path):
            row = dict(row)
            capture_id = clean(row.get("capture_id")) or "unknown"
            uid = f"{path.name}:{capture_id}"
            if uid in seen_uid:
                continue
            seen_uid.add(uid)
            row["_capture_file"] = path.name
            row["_capture_uid"] = uid
            rows.append(row)
    return rows


def period_band(row: dict[str, str]) -> str:
    year = safe_int(row.get("date_end")) or safe_int(row.get("date_start"))
    if year is None:
        return "undated_or_unparsed"
    if year <= 1930:
        return "pre_1930"
    if year <= 1970:
        return "1930_1970"
    if year <= 2000:
        return "1970_2000"
    if year <= 2026:
        return "2000_2026"
    return "post_2026_or_error"


def image_state(row: dict[str, str]) -> str:
    value = clean(row.get("image_presence_code"))
    if value in {"IMG00", "IMG01", "IMG02", "IMG03", "IMG04"}:
        return value
    text = clean(row.get("image_state_evaluation"))
    for code in ("IMG00", "IMG01", "IMG02", "IMG03", "IMG04"):
        if code in text:
            return code
    return "UNKNOWN"


def series_stem(title: str | None) -> str:
    value = clean(title)
    value = re.sub(r"\b(18|19|20)\d{2}[-/.]\d{1,2}([-/.]\d{1,2})?\b", " ", value)
    value = re.sub(r"\b(18|19|20)\d{2}\b", " ", value)
    value = re.sub(r"\b(volume|vol\.?|number|no\.?|issue|nº|nr\.?|leaf|page|plate)\s*[\w.-]+\b", " ", value, flags=re.I)
    value = re.sub(r"\b\d{1,4}\b", " ", value)
    value = norm(value)
    if len(value) < 8 or value in STOP_STEMS:
        return ""
    return value


def decade(row: dict[str, str]) -> str:
    year = safe_int(row.get("date_end")) or safe_int(row.get("date_start"))
    if year is None:
        return "undated"
    return f"{year // 10 * 10}s"


def url_domain(url: str | None) -> str:
    parsed = urlparse(clean(url))
    return parsed.netloc.lower()


def title(row: dict[str, str]) -> str:
    return clean(row.get("source_title")) or "Untitled / title unavailable"


def date_text(row: dict[str, str]) -> str:
    return clean(row.get("source_date_text")) or clean(row.get("date_end")) or clean(row.get("date_start")) or "undated"


def text_length(row: dict[str, str]) -> int:
    fields = (
        "source_description",
        "source_notes",
        "source_subjects",
        "ocr_or_excerpt",
        "editorial_summary",
        "historical_context_note",
        "classification_rationale",
    )
    return len(" ".join(clean(row.get(field)) for field in fields).strip())


def completeness_proxy(row: dict[str, str]) -> int:
    score = 0
    checks = [
        ("source_title", 12),
        ("source_identifier", 10),
        ("source_record_url", 12),
        ("source_date_text", 8),
        ("source_creator", 6),
        ("source_place_text", 6),
        ("source_object_type", 6),
        ("source_medium", 6),
        ("source_collection", 6),
        ("source_rights_text", 8),
        ("rights_basis", 6),
    ]
    for field, weight in checks:
        if clean(row.get(field)):
            score += weight
    if image_state(row) in {"IMG01", "IMG02", "IMG03"}:
        score += 10
    if text_length(row) >= 180:
        score += 10
    elif text_length(row) >= 80:
        score += 5
    return min(score, 100)


def add(groups: dict[tuple[str, str], list[dict[str, str]]], kind: str, key: str, row: dict[str, str]) -> None:
    if key:
        groups[(kind, key)].append(row)


def build_groups(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        source_name = norm(row.get("source_name"))
        source_id = norm(row.get("source_identifier"))
        source_url = clean(row.get("source_record_url"))
        image_url = clean(row.get("image_url_detected"))
        title_norm = norm(row.get("source_title"))
        stem = series_stem(row.get("source_title"))
        collection = norm(row.get("source_collection"))
        medium = norm(row.get("source_medium"))[:60]
        place = norm(row.get("source_place_text"))[:60]

        add(groups, "same_source_record_url", source_url, row)
        if source_name and source_id:
            add(groups, "same_source_identifier", f"{source_name}|{source_id}", row)
        if image_url:
            add(groups, "same_image_url", image_url, row)
        if source_name and title_norm:
            add(groups, "same_title_within_source", f"{source_name}|{title_norm}|{decade(row)}", row)
        if source_name and collection and stem:
            add(groups, "same_series_stem_collection", f"{source_name}|{collection}|{stem}|{decade(row)}", row)
        if collection and medium and place:
            add(groups, "same_collection_medium_place_decade", f"{collection}|{medium}|{place}|{decade(row)}", row)
    return groups


def relation_label(linkage_type: str, items: list[dict[str, str]]) -> str:
    if linkage_type in {"same_source_record_url", "same_source_identifier"}:
        return "same_entity_confirmed"
    if linkage_type == "same_image_url":
        domains = {url_domain(row.get("image_url_detected")) for row in items}
        url = clean(items[0].get("image_url_detected"))
        if "placeholder" in url or "default" in url and len(items) > 5:
            return "possible_placeholder_or_loader_reuse"
        if len(domains) == 1:
            return "same_visual_item_different_capture"
        return "possibly_same_as"
    if linkage_type == "same_title_within_source":
        return "possibly_same_as"
    if linkage_type == "same_series_stem_collection":
        return "same_work_series_or_campaign"
    return "related_but_not_same"


def confidence(linkage_type: str, relation: str, items: list[dict[str, str]]) -> str:
    if relation == "same_entity_confirmed":
        return "high"
    if relation == "same_visual_item_different_capture" and len(items) <= 8:
        return "medium"
    if linkage_type in {"same_title_within_source", "same_series_stem_collection"}:
        return "medium"
    return "low"


def date_span(items: list[dict[str, str]]) -> str:
    years: list[int] = []
    for row in items:
        for field in ("date_start", "date_end"):
            year = safe_int(row.get(field))
            if year is not None:
                years.append(year)
    if not years:
        return "undated"
    start, end = min(years), max(years)
    return str(start) if start == end else f"{start}-{end}"


def concise(values: list[str], max_items: int = 5) -> str:
    seen: list[str] = []
    for value in values:
        value = clean(value)
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= max_items:
        return "; ".join(seen)
    return "; ".join(seen[:max_items]) + f"; +{len(seen) - max_items} more"


def coverage_gaps(items: list[dict[str, str]]) -> str:
    flags: list[str] = []
    if not any(image_state(row) in {"IMG01", "IMG02", "IMG03"} for row in items):
        flags.append("needs_image")
    if max(text_length(row) for row in items) < 180:
        flags.append("needs_text")
    if any(image_state(row) == "IMG00" for row in items):
        flags.append("needs_rights_evidence")
    if len({period_band(row) for row in items}) > 1:
        flags.append("cross_period_review")
    if len({clean(row.get("source_place_text")) for row in items if clean(row.get("source_place_text"))}) > 1:
        flags.append("multi_place_review")
    return ";".join(flags or ["coverage_ready"])


def recommended_action(relation: str, items: list[dict[str, str]]) -> str:
    anchor_score = max(completeness_proxy(row) for row in items)
    if relation == "same_entity_confirmed":
        return "deduplicate_or_merge_source_records"
    if relation in {"same_visual_item_different_capture", "possible_placeholder_or_loader_reuse"}:
        return "review_duplicate_image_before_public_rebuild"
    if anchor_score >= 75 and len(items) >= 3:
        return "canonical_main_with_child_text_appendix"
    if anchor_score >= 55:
        return "support_packet_or_compound_sheet_candidate"
    if anchor_score >= 40:
        return "attach_to_parent_as_card_or_appendix"
    return "bookmark_or_internal_lead"


def evidence_basis(linkage_type: str) -> str:
    return {
        "same_source_record_url": "Rows share the same source_record_url.",
        "same_source_identifier": "Rows share the same source_name and source_identifier.",
        "same_image_url": "Rows share the same image_url_detected; may be true reuse or a loader/placeholder problem.",
        "same_title_within_source": "Rows share normalized title, source, and decade.",
        "same_series_stem_collection": "Rows share source, collection, title stem, and decade.",
        "same_collection_medium_place_decade": "Rows share collection, medium, place, and decade; weak planning cluster only.",
    }.get(linkage_type, "Generated linkage candidate.")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                field: clean(str(row.get(field, "")))
                for field in fields
            }
            for row in rows
        )


def main() -> None:
    rows = capture_rows()
    raw_groups = build_groups(rows)
    group_rows: list[dict[str, str]] = []
    member_rows: list[dict[str, str]] = []
    gid = 1

    for (linkage_type, linkage_key), items in sorted(raw_groups.items(), key=lambda item: (-len(item[1]), item[0][0], item[0][1])):
        # Keep useful candidates, but avoid giant weak buckets.
        if len(items) < 2 or len(items) > 60:
            continue
        if linkage_type == "same_collection_medium_place_decade" and len(items) < 4:
            continue
        if linkage_type == "same_title_within_source" and len(items) > 20:
            continue

        relation = relation_label(linkage_type, items)
        conf = confidence(linkage_type, relation, items)
        anchor = max(items, key=lambda row: (completeness_proxy(row), text_length(row), image_state(row), title(row)))
        group_id = f"SRLG{gid:04d}"
        gid += 1
        group_rows.append(
            {
                "linkage_group_id": group_id,
                "linkage_type": linkage_type,
                "linkage_key": linkage_key,
                "confidence": conf,
                "relation_label": relation,
                "member_count": str(len(items)),
                "proposed_anchor_capture_id": clean(anchor.get("capture_id")),
                "proposed_anchor_title": title(anchor),
                "anchor_completeness_proxy": str(completeness_proxy(anchor)),
                "date_span": date_span(items),
                "source_names": concise([row.get("source_name", "") for row in items]),
                "image_states": "; ".join(f"{k}: {v}" for k, v in sorted(Counter(image_state(row) for row in items).items())),
                "period_bands": "; ".join(f"{k}: {v}" for k, v in sorted(Counter(period_band(row) for row in items).items())),
                "recommended_group_action": recommended_action(relation, items),
                "coverage_gap_flags": coverage_gaps(items),
                "evidence_basis": evidence_basis(linkage_type),
                "member_capture_uids": ";".join(row["_capture_uid"] for row in items),
            }
        )
        for row in items:
            role = "anchor_candidate" if row is anchor else "linked_member"
            member_rows.append(
                {
                    "linkage_group_id": group_id,
                    "capture_uid": row["_capture_uid"],
                    "capture_id": clean(row.get("capture_id")),
                    "capture_file": row["_capture_file"],
                    "membership_role": role,
                    "relation_label": relation,
                    "membership_confidence": conf,
                    "source_name": clean(row.get("source_name")),
                    "source_identifier": clean(row.get("source_identifier")),
                    "source_title": title(row),
                    "date_text": date_text(row),
                    "period_band": period_band(row),
                    "image_state": image_state(row),
                    "completeness_proxy": str(completeness_proxy(row)),
                    "source_record_url": clean(row.get("source_record_url")),
                    "image_url_detected": clean(row.get("image_url_detected")),
                }
            )

    write_csv(GROUPS, GROUP_FIELDS, group_rows)
    write_csv(MEMBERS, MEMBER_FIELDS, member_rows)

    type_counts = Counter(row["linkage_type"] for row in group_rows)
    action_counts = Counter(row["recommended_group_action"] for row in group_rows)
    relation_counts = Counter(row["relation_label"] for row in group_rows)
    gap_counts: Counter[str] = Counter()
    for row in group_rows:
        for flag in row["coverage_gap_flags"].split(";"):
            gap_counts[flag] += 1

    top_groups = sorted(
        group_rows,
        key=lambda row: (
            "needs_image" in row["coverage_gap_flags"],
            "needs_text" in row["coverage_gap_flags"],
            int(row["member_count"]),
            int(row["anchor_completeness_proxy"]),
        ),
        reverse=True,
    )[:25]

    lines = [
        "# Source Record Linkage Candidates v1",
        "",
        "Date: 2026-06-01",
        "",
        "Scope: capture records before final surface assignment. This file proposes grouping and de-duplication candidates; it does not merge records.",
        "",
        "## Summary",
        "",
        f"- Capture rows scanned: {len(rows)}",
        f"- Linkage groups: {len(group_rows)}",
        f"- Linkage memberships: {len(member_rows)}",
        "",
        "## Linkage Types",
        "",
    ]
    lines += [f"- `{key}`: {value}" for key, value in type_counts.most_common()]
    lines += ["", "## Relation Labels", ""]
    lines += [f"- `{key}`: {value}" for key, value in relation_counts.most_common()]
    lines += ["", "## Recommended Actions", ""]
    lines += [f"- `{key}`: {value}" for key, value in action_counts.most_common()]
    lines += ["", "## Coverage Gaps", ""]
    lines += [f"- `{key}`: {value}" for key, value in gap_counts.most_common()]
    lines += ["", "## High-Value Review Groups", ""]
    for row in top_groups:
        lines.append(
            f"- {row['linkage_group_id']} | {row['linkage_type']} | {row['member_count']} members | "
            f"{row['recommended_group_action']} | {row['coverage_gap_flags']} | {row['proposed_anchor_title']}"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- `same_entity_confirmed` can support deduplication or one main sheet with source/register children.",
        "- `same_visual_item_different_capture` must be checked before rebuild because it may be a true repeated visual item or an accidental repeated thumbnail.",
        "- `same_work_series_or_campaign` is a good target for compound sheets, text pages, cards, and appendix grouping.",
        "- Weak collection/medium/place clusters are planning aids, not evidence that records describe the same work.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {GROUPS} ({len(group_rows)} groups)")
    print(f"Wrote {MEMBERS} ({len(member_rows)} memberships)")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
