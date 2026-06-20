#!/usr/bin/env python3
"""Build a non-mutating main/sub/text methodology validation packet.

This script samples the prefreeze main-anchor strictness audit so the packet
role method can be reviewed before any rebuild, override, demotion, or surface
generation. It does not download images or change rights/image states.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_REVIEW = DATA / "prefreeze_main_anchor_strictness_review_v1.csv"

OUT_PACKET = DATA / "prefreeze_main_sub_text_method_validation_packet_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_method_validation_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_MAIN_SUB_TEXT_METHOD_VALIDATION_PACKET_v1.md"
OUT_DECISION_TEMPLATE = DOCS / "PREFREEZE_MAIN_SUB_TEXT_METHOD_DECISION_LOG_TEMPLATE_v1.md"

TARGETS = {
    "strong_soft_anchor": 40,
    "soft_anchor_review": 80,
    "anchor_if_editorial_text_added": 40,
    "packet_anchor_or_member_review": None,
    "support_or_card_review": 120,
}

PACKET_FIELDS = [
    "validation_sample_id",
    "sample_target_marker",
    "surface_id",
    "capture_id",
    "year",
    "period",
    "region",
    "theme",
    "medium",
    "image_state",
    "source_name",
    "source_family",
    "title",
    "research_packet_anchor_marker",
    "main_anchor_lane",
    "main_anchor_reason",
    "source_reading_text_length",
    "reading_text_length",
    "source_text_bucket",
    "compound_children",
    "dossier_subsheet_pages",
    "dossier_text_pages",
    "cluster_key",
    "cluster_size",
    "cluster_bucket",
    "method_risk_flags",
    "review_question_1_anchor_scope",
    "review_question_2_source_depth",
    "review_question_3_relation_need",
    "review_question_4_text_need",
    "review_question_5_recommended_role",
    "review_status",
    "reviewer_notes",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def as_int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(*parts: object) -> str:
    text = "||".join(clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def source_family(source_name: object) -> str:
    text = clean(source_name)
    folded = text.casefold()
    rules = [
        ("wikimedia commons", "Wikimedia Commons"),
        ("gallica", "Gallica / BnF APIs"),
        ("bnf", "Gallica / BnF APIs"),
        ("digitalnz", "DigitalNZ"),
        ("te papa", "Te Papa"),
        ("internet archive", "Internet Archive"),
        ("library of congress", "Library of Congress"),
        ("georgia state", "Georgia State CONTENTdm"),
        ("princeton", "Princeton Figgy"),
        ("wellcome", "Wellcome Collection"),
        ("cooper hewitt", "Cooper Hewitt"),
        ("europeana", "Europeana"),
        ("rijksmuseum", "Rijksmuseum"),
        ("metropolitan museum", "Metropolitan Museum of Art"),
        ("victoria and albert", "Victoria and Albert Museum"),
    ]
    for needle, label in rules:
        if needle in folded:
            return label
    return text[:80] or "Unresolved source family"


def source_text_bucket(length: object) -> str:
    value = as_int(length)
    if value < 80:
        return "lt80"
    if value < 250:
        return "80_249"
    if value < 600:
        return "250_599"
    return "600_plus"


def cluster_bucket(size: object) -> str:
    value = as_int(size)
    if value <= 1:
        return "single"
    if value <= 4:
        return "2_4"
    if value <= 9:
        return "5_9"
    return "10_plus"


def risk_flags(row: dict[str, str]) -> str:
    text = " ".join(
        clean(row.get(key))
        for key in ("title", "region", "theme", "medium", "source_name", "main_anchor_reason", "cluster_key")
    ).casefold()
    flags: list[str] = []
    if "wikimedia commons" in text:
        flags.append("commons_file_source")
    if "unresolved" in text:
        flags.append("unresolved_region_or_theme")
    if any(term in text for term in ("global", "international", "transnational", "world", "diaspora")):
        flags.append("transnational_region")
    if re.search(r"(?<![a-z0-9])(stamp|postage|philatelic|commemorative)(?![a-z0-9])", text):
        flags.append("stamp_or_philatelic")
    if re.search(r"(?<![a-z0-9])(event photo|conference|session|ceremony|anniversary|inauguration)(?![a-z0-9])", text):
        flags.append("event_photo_context")
    if re.search(r"(?<![a-z0-9])(natural history|geology|geological|fossil|mineral|specimen)(?![a-z0-9])", text):
        flags.append("natural_history_geology")
    if as_int(row.get("cluster_size")) >= 5:
        flags.append("large_cluster")
    if as_int(row.get("source_reading_text_length")) < 80:
        flags.append("thin_source_text")
    if as_int(row.get("dossier_subsheet_pages")) == 0:
        flags.append("no_subsheet_relation")
    return "; ".join(dict.fromkeys(flags))


def review_questions(marker: str) -> dict[str, str]:
    if marker == "strong_soft_anchor":
        role_hint = "Can stay main if it has source depth, relation density, or packet value."
    elif marker == "soft_anchor_review":
        role_hint = "Decide whether this is a main anchor, sub sheet, card, or appendix support item."
    elif marker == "anchor_if_editorial_text_added":
        role_hint = "Main status depends on whether editorial text can create research value."
    elif marker == "packet_anchor_or_member_review":
        role_hint = "Determine whether this starts a packet or belongs under a nearby packet anchor."
    else:
        role_hint = "Likely support/card unless the review finds exceptional anchor value."
    return {
        "review_question_1_anchor_scope": "Does this surface define a research packet, or only support another packet?",
        "review_question_2_source_depth": "Does source evidence support more than an object listing?",
        "review_question_3_relation_need": "Which nearby main/sub/card/appendix records should it connect to?",
        "review_question_4_text_need": "Would editorial text materially improve research use, or only pad the page?",
        "review_question_5_recommended_role": role_hint,
    }


def enriched_row(row: dict[str, str], sample_id: int) -> dict[str, object]:
    marker = clean(row.get("research_packet_anchor_marker")) or "unmarked"
    family = source_family(row.get("source_name"))
    out = dict(row)
    out.update(
        {
            "validation_sample_id": f"MSTV{sample_id:04d}",
            "sample_target_marker": marker,
            "source_family": family,
            "source_text_bucket": source_text_bucket(row.get("source_reading_text_length")),
            "cluster_bucket": cluster_bucket(row.get("cluster_size")),
            "method_risk_flags": risk_flags(row),
            "review_status": "pending",
            "reviewer_notes": "",
        }
    )
    out.update(review_questions(marker))
    return out


def stratified_pick(rows: list[dict[str, str]], target: int | None) -> list[dict[str, str]]:
    if target is None or len(rows) <= target:
        return sorted(rows, key=lambda row: stable_hash(row.get("surface_id"), row.get("capture_id"), row.get("title")))

    grouped: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            clean(row.get("period")) or "undated",
            source_family(row.get("source_name")),
            clean(row.get("image_state")) or "IMG00",
            source_text_bucket(row.get("source_reading_text_length")),
            cluster_bucket(row.get("cluster_size")),
        )
        grouped[key].append(row)

    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: stable_hash(row.get("surface_id"), row.get("capture_id"), row.get("title")))

    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    keys = sorted(grouped, key=lambda key: (len(grouped[key]), key))
    while len(selected) < target and keys:
        advanced = False
        for key in keys:
            group_rows = grouped[key]
            while group_rows:
                candidate = group_rows.pop(0)
                surface_id = clean(candidate.get("surface_id"))
                if surface_id not in seen:
                    selected.append(candidate)
                    seen.add(surface_id)
                    advanced = True
                    break
            if len(selected) >= target:
                break
        keys = [key for key in keys if grouped[key]]
        if not advanced:
            break

    if len(selected) < target:
        remaining = [
            row
            for row in rows
            if clean(row.get("surface_id")) not in seen
        ]
        remaining.sort(key=lambda row: stable_hash(row.get("surface_id"), row.get("capture_id"), row.get("title")))
        selected.extend(remaining[: target - len(selected)])

    return selected


def build_packet(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_marker: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_marker[clean(row.get("research_packet_anchor_marker"))].append(row)

    selected: list[dict[str, str]] = []
    for marker, target in TARGETS.items():
        selected.extend(stratified_pick(by_marker.get(marker, []), target))

    selected.sort(
        key=lambda row: (
            clean(row.get("research_packet_anchor_marker")),
            clean(row.get("period")),
            source_family(row.get("source_name")),
            clean(row.get("region")),
            stable_hash(row.get("surface_id"), row.get("capture_id")),
        )
    )
    return [enriched_row(row, index + 1) for index, row in enumerate(selected)]


def summary_rows(packet: list[dict[str, object]], source_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {"metric": "methodology_scope", "value": "non_mutating_validation", "notes": "No rebuild, no role override, no image download, no rights/image-state change."},
        {"metric": "source_review_rows", "value": len(source_rows), "notes": "Rows available from prefreeze main-anchor strictness audit."},
        {"metric": "validation_packet_rows", "value": len(packet), "notes": "Rows sampled for methodology validation."},
    ]
    for marker, count in Counter(clean(row.get("sample_target_marker")) for row in packet).most_common():
        rows.append({"metric": f"sample_marker:{marker}", "value": count, "notes": "Validation sample distribution by soft anchor marker."})
    for period, count in Counter(clean(row.get("period")) for row in packet).most_common():
        rows.append({"metric": f"sample_period:{period}", "value": count, "notes": "Validation sample distribution by period."})
    for family, count in Counter(clean(row.get("source_family")) for row in packet).most_common():
        rows.append({"metric": f"sample_source_family:{family}", "value": count, "notes": "Validation sample distribution by source family."})
    for bucket, count in Counter(clean(row.get("source_text_bucket")) for row in packet).most_common():
        rows.append({"metric": f"sample_source_text_bucket:{bucket}", "value": count, "notes": "Validation sample distribution by source text length."})
    for bucket, count in Counter(clean(row.get("cluster_bucket")) for row in packet).most_common():
        rows.append({"metric": f"sample_cluster_bucket:{bucket}", "value": count, "notes": "Validation sample distribution by cluster size."})

    flag_counter: Counter[str] = Counter()
    for row in packet:
        for flag in clean(row.get("method_risk_flags")).split("; "):
            if flag:
                flag_counter[flag] += 1
    for flag, count in flag_counter.most_common():
        rows.append({"metric": f"sample_risk_flag:{flag}", "value": count, "notes": "Risk flag to inspect during method validation."})
    return rows


def write_report(packet: list[dict[str, object]], summary: list[dict[str, object]]) -> None:
    marker_counts = Counter(clean(row.get("sample_target_marker")) for row in packet)
    period_counts = Counter(clean(row.get("period")) for row in packet)
    family_counts = Counter(clean(row.get("source_family")) for row in packet)
    lines = [
        "# Prefreeze Main/Sub/Text Method Validation Packet v1",
        "",
        "Scope: non-mutating review packet for validating the main/sub/text method before any rebuild or role application.",
        "",
        "This pass does not rebuild surfaces, does not apply overrides, does not download images, and does not change rights or image states.",
        "",
        "## Why This Exists",
        "",
        "The current archive has many surfaces that are technically main sheets but have not yet proven that they can act as durable research-packet anchors. This packet creates a reviewable sample so the method can be accepted, revised, or rejected before any structural mutation.",
        "",
        "## Sample Size",
        "",
        f"- Total validation rows: {len(packet)}.",
    ]
    for marker, count in marker_counts.most_common():
        lines.append(f"- {marker}: {count}.")
    lines.extend(
        [
            "",
            "## Period Spread",
            "",
        ]
    )
    for period, count in period_counts.most_common():
        lines.append(f"- {period}: {count}.")
    lines.extend(
        [
            "",
            "## Source-Family Spread",
            "",
        ]
    )
    for family, count in family_counts.most_common(20):
        lines.append(f"- {family}: {count}.")
    lines.extend(
        [
            "",
            "## Validation Rule",
            "",
            "- A main sheet may remain a provisional research-packet anchor when it has impact, source depth, relation density, period/region scarcity, or clear editorial need.",
            "- A sub sheet is not a demotion of historical importance; it is a structural assignment under a stronger packet anchor.",
            "- A text sheet is valid only when it adds interpretive, contextual, or methodological value beyond metadata repetition.",
            "- Cards and appendix pages should preserve evidence, provenance, index, and lightweight context without overclaiming research anchor status.",
            "",
            "## Advantages",
            "",
            "- Keeps the archive from making premature structural changes on weak evidence.",
            "- Lets main sheets carry provisional anchor intent without pretending every main already has a full dossier.",
            "- Makes edge cases reviewable by period, region, source family, image state, source depth, and cluster size.",
            "- Creates an audit trail that can be revisited after the next large data-cleaning cycle.",
            "",
            "## Disadvantages",
            "",
            "- It adds a review layer before visible structure improves.",
            "- Some genuinely important isolated works may stay in review longer than ideal.",
            "- Source-family imbalance can still affect the sample because the underlying archive is uneven.",
            "- The method cannot prove final packet quality until reviewed rows are later tested in a small rebuild.",
            "",
            "## Pass / Fail Meaning",
            "",
            "- Pass: reviewers agree that the marker classes predict plausible main/sub/text/card/appendix roles often enough to justify a small applied override test.",
            "- Revise: reviewers find a recurring failure pattern, such as Commons event photos, stamps, transnational region drift, or thin source text receiving too much anchor weight.",
            "- Fail: reviewers conclude that object-level rows cannot be packetized until more source text or relation data is available.",
            "",
            "## Next Permitted Action",
            "",
            "Review this packet and fill the decision log template. Do not apply a new override layer until the decision log states which marker classes are accepted and which require new rules.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision_template() -> None:
    lines = [
        "# Prefreeze Main/Sub/Text Method Decision Log Template v1",
        "",
        "Use this after reviewing `data/prefreeze_main_sub_text_method_validation_packet_v1.csv`.",
        "",
        "## 1. Review Scope",
        "",
        "- Review date:",
        "- Reviewer:",
        "- Sample rows reviewed:",
        "- Marker classes reviewed:",
        "",
        "## 2. Main As Provisional Research-Packet Anchor",
        "",
        "- Accepted / revised / rejected:",
        "- Reason:",
        "- Boundary conditions:",
        "",
        "## 3. Accepted Criteria",
        "",
        "- Impact:",
        "- Source depth:",
        "- Relation density:",
        "- Period span:",
        "- Region scarcity:",
        "- Rights state:",
        "- Editorial need:",
        "",
        "## 4. Rejected Or Risky Criteria",
        "",
        "- Event/photo context:",
        "- Stamp or commemorative issue:",
        "- Natural-history/geology drift:",
        "- Transnational geography drift:",
        "- Thin source text:",
        "- Duplicate/variant clusters:",
        "",
        "## 5. Role Transition Principles",
        "",
        "- Main to sub:",
        "- Main to card:",
        "- Main to appendix:",
        "- Main retained with text requirement:",
        "",
        "## 6. Minimum Text Principles",
        "",
        "- When one text page is enough:",
        "- When multiple text pages are needed:",
        "- When text would be filler and should not be created:",
        "",
        "## 7. Source-Family Notes",
        "",
        "- Commons:",
        "- Museum APIs:",
        "- National libraries:",
        "- Design institutions:",
        "- Smaller regional sources:",
        "",
        "## 8. Known Failure Cases",
        "",
        "-",
        "",
        "## 9. Next Permissible Action",
        "",
        "- No action / revise rules / create small override test / request deeper research:",
    ]
    OUT_DECISION_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DECISION_TEMPLATE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    source_rows = read_csv(IN_REVIEW)
    packet = build_packet(source_rows)
    summary = summary_rows(packet, source_rows)

    write_csv(OUT_PACKET, packet, PACKET_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_report(packet, summary)
    write_decision_template()

    print(f"validation_packet_rows={len(packet)}")
    print(f"wrote {OUT_PACKET.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")
    print(f"wrote {OUT_DECISION_TEMPLATE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
