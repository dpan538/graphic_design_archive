#!/usr/bin/env python3
"""Assess every pre-freeze main sheet for main/sub/text/card role planning.

This is a non-mutating audit. It reads the local pre-freeze candidate payload
and writes review queues only. It does not rebuild official payloads, apply
role overrides, download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import audit_prefreeze_candidate_payload_v1 as release_audit


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

OUT_ASSESSMENT = DATA / "prefreeze_main_sub_text_full_role_assessment_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_full_role_assessment_summary_v1.csv"
OUT_ACTION_PERIOD = DATA / "prefreeze_main_sub_text_full_role_action_by_period_v1.csv"
OUT_ACTION_REGION = DATA / "prefreeze_main_sub_text_full_role_action_by_region_v1.csv"
OUT_SAMPLE = DATA / "prefreeze_main_sub_text_full_role_calibration_sample_v1.csv"
REPORT = DOCS / "MAIN_SUB_TEXT_FULL_ROLE_ASSESSMENT_v1.md"

SAMPLE_TARGET = 500

ASSESSMENT_FIELDS = [
    "surface_id",
    "capture_id",
    "year",
    "period_band",
    "five_year_bucket",
    "region",
    "theme",
    "source_family",
    "source_name",
    "title",
    "image_state",
    "source_text_chars",
    "generated_text_chars",
    "total_text_chars",
    "cluster_key",
    "cluster_size",
    "dossier_text_pages",
    "dossier_support_pages",
    "compound_children",
    "anchor_strength_score",
    "source_depth_score",
    "relation_density_score",
    "text_depth_score",
    "design_object_confidence_score",
    "risk_pressure_score",
    "region_scarcity_score",
    "period_value_score",
    "editorial_need_score",
    "overall_research_anchor_score",
    "risk_flags",
    "positive_flags",
    "recommended_next_action",
    "action_confidence",
    "action_reason",
    "sample_priority",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]
ACTION_FIELDS = [
    "group",
    "main_sheet_count",
    "keep_main_anchor",
    "keep_main_add_text",
    "packet_anchor_review",
    "downgrade_to_sub_candidate",
    "downgrade_to_card_candidate",
    "convert_to_text_or_appendix",
    "exclude_or_deprioritize_review",
    "manual_review",
    "median_anchor_score",
    "median_risk_pressure",
]

SAMPLE_FIELDS = ASSESSMENT_FIELDS + [
    "calibration_question",
    "review_status",
    "reviewer_notes",
]

DESIGN_TERMS = {
    "advertising",
    "advertisement",
    "book cover",
    "brand",
    "campaign",
    "catalogue",
    "commercial art",
    "corporate identity",
    "design",
    "exhibition",
    "film poster",
    "graphic",
    "identity",
    "layout",
    "letterform",
    "logo",
    "magazine",
    "packaging",
    "poster",
    "print",
    "publication",
    "signage",
    "symbol",
    "typography",
    "visual communication",
    "zine",
}

WEAK_CONTEXT_TERMS = {
    "anniversary",
    "ceremony",
    "conference",
    "event photo",
    "festival photo",
    "inauguration",
    "opening reception",
    "poster session",
    "profile",
    "talk",
    "workshop",
}

STAMP_TERMS = {"commemorative", "philatelic", "postage", "stamp", "stamps"}
NON_DESIGN_DRIFT_TERMS = {
    "bivalve",
    "bird",
    "botanical",
    "fossil",
    "geology",
    "geological",
    "limestone",
    "mineral",
    "natural history",
    "ordovician",
    "specimen",
    "tourist photo",
    "wildlife",
}
SOURCE_REGISTER_TERMS = {
    "archive profile",
    "bibliography",
    "catalog record",
    "collection guide",
    "finding aid",
    "inventory",
    "register",
    "source profile",
}
HIGH_AUTHORITY_SOURCE_TERMS = {
    "archive",
    "bnf",
    "collection",
    "cooper hewitt",
    "digitalnz",
    "gallica",
    "library",
    "museum",
    "smithsonian",
    "university",
    "wellcome",
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_payload() -> dict[str, Any]:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def stable_hash(*parts: object) -> str:
    text = "||".join(clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def year_of(surface: dict[str, Any]) -> int | None:
    return release_audit.year(surface)


def period_band(surface: dict[str, Any]) -> str:
    return release_audit.period_band(surface)


def five_year_bucket(surface: dict[str, Any]) -> str:
    return release_audit.five_year_bucket(surface)


def image_state(surface: dict[str, Any]) -> str:
    return release_audit.image_state(surface)


def folder_title(surface: dict[str, Any], folder_type: str) -> str:
    for folder in surface.get("folders", []):
        if isinstance(folder, dict) and folder.get("type") == folder_type:
            return clean(folder.get("title"))
    return ""


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
        ("smithsonian", "Smithsonian"),
    ]
    for needle, label in rules:
        if needle in folded:
            return label
    return text[:80] or "Unresolved source family"


def source_text(surface: dict[str, Any]) -> str:
    return " ".join(
        clean(surface.get(key))
        for key in ("sourceDescription", "sourceNotes", "sourceSubjects", "ocrOrExcerpt", "sourceDescriptionRaw")
        if clean(surface.get(key))
    )


def generated_text(surface: dict[str, Any]) -> str:
    return " ".join(
        clean(surface.get(key))
        for key in (
            "descriptionSummary",
            "historicalContextNote",
            "classificationRationale",
            "uncertaintyNote",
            "citationBasis",
        )
        if clean(surface.get(key))
    )


def dossier_by_anchor(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        clean(dossier.get("anchorSurfaceId")): dossier
        for dossier in payload.get("researchDossiers", [])
        if clean(dossier.get("anchorSurfaceId"))
    }


def dossier_counts(dossier: dict[str, Any] | None) -> tuple[int, int]:
    if not dossier:
        return 0, 0
    text_pages = 0
    support_pages = 0
    for page in dossier.get("pageSequence", []):
        if not isinstance(page, dict):
            continue
        page_type = clean(page.get("pageType"))
        if page_type == "text_page":
            text_pages += 1
        if page_type in {"sub_sheet", "card", "appendix", "child_source_record"}:
            support_pages += 1
    return text_pages, support_pages


def cluster_key(surface: dict[str, Any]) -> str:
    return "|".join(
        [
            folder_title(surface, "region") or "Unresolved region",
            folder_title(surface, "theme") or "Unresolved theme",
            source_family(surface.get("sourceName")),
            five_year_bucket(surface),
        ]
    )


def term_hits(text: str, terms: set[str]) -> list[str]:
    hits: list[str] = []
    for term in sorted(terms):
        pattern = r"(?<![a-z0-9])" + re.escape(term.casefold()) + r"(?![a-z0-9])"
        if re.search(pattern, text.casefold()):
            hits.append(term)
    return hits


def score_text_depth(source_chars: int, generated_chars: int) -> int:
    source_score = min(55, source_chars // 12)
    generated_score = min(35, generated_chars // 45)
    total_bonus = 10 if source_chars + generated_chars >= 1200 else 0
    return min(100, source_score + generated_score + total_bonus)


def score_source_depth(source_chars: int, family: str, source_name: str) -> int:
    score = min(70, source_chars // 10)
    folded = f"{family} {source_name}".casefold()
    if any(term in folded for term in HIGH_AUTHORITY_SOURCE_TERMS):
        score += 15
    if source_chars >= 600:
        score += 10
    if source_chars < 80:
        score -= 20
    return max(0, min(100, score))


def score_relation_density(cluster_size: int, support_pages: int, children: int) -> int:
    score = min(35, max(0, cluster_size - 1) * 5)
    score += min(35, support_pages * 12)
    score += min(30, children * 10)
    return min(100, score)


def score_design_confidence(text: str, image: str) -> tuple[int, list[str]]:
    positives = term_hits(text, DESIGN_TERMS)
    score = min(65, len(positives) * 12)
    if image == "IMG03":
        score += 20
    elif image == "IMG02":
        score += 14
    elif image == "IMG01":
        score += 8
    if "graphic design" in positives or "visual communication" in positives:
        score += 10
    return min(100, score), positives


def score_risk_pressure(text: str, source_name: str) -> tuple[int, list[str]]:
    flags: list[str] = []
    weak_hits = term_hits(text, WEAK_CONTEXT_TERMS)
    stamp_hits = term_hits(text, STAMP_TERMS)
    drift_hits = term_hits(text, NON_DESIGN_DRIFT_TERMS)
    register_hits = term_hits(text, SOURCE_REGISTER_TERMS)
    flags.extend(f"weak_context:{hit}" for hit in weak_hits)
    flags.extend(f"stamp_or_philatelic:{hit}" for hit in stamp_hits)
    flags.extend(f"non_design_drift:{hit}" for hit in drift_hits)
    flags.extend(f"source_register:{hit}" for hit in register_hits)
    if "wikimedia commons" in source_name.casefold():
        flags.append("commons_file_source")
    score = len(weak_hits) * 12 + len(stamp_hits) * 18 + len(drift_hits) * 20 + len(register_hits) * 12
    if "commons_file_source" in flags:
        score += 8
    return min(100, score), list(dict.fromkeys(flags))


def region_scarcity_scores(main_surfaces: list[dict[str, Any]]) -> dict[str, int]:
    lookup = release_audit.macro_region_lookup()
    counts = Counter(release_audit.region(surface, lookup) for surface in main_surfaces)
    scores: dict[str, int] = {}
    for region, count in counts.items():
        target = release_audit.REGION_SURFACE_TARGETS.get(region, 250)
        fill = min(count / target, 1.0) if target else 1.0
        scores[region] = int(round((1.0 - fill) * 100))
    return scores


def period_value_scores(main_surfaces: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(period_band(surface) for surface in main_surfaces)
    scores: dict[str, int] = {}
    for period, count in counts.items():
        target = release_audit.PERIOD_SURFACE_TARGETS.get(period, 250)
        fill = min(count / target, 1.0) if target else 1.0
        base = int(round((1.0 - fill) * 100))
        if period in {"1970_2000", "2000_2026"}:
            base = max(base, 20)
        scores[period] = min(100, base)
    return scores


def action_for(
    anchor: int,
    source_depth: int,
    relation: int,
    text_depth: int,
    design_confidence: int,
    risk: int,
    editorial_need: int,
    source_chars: int,
    image: str,
    risk_flags: list[str],
    positive_flags: list[str],
) -> tuple[str, str, str]:
    risk_text = "; ".join(risk_flags)
    has_design_evidence = bool(positive_flags)
    if risk >= 70 and not has_design_evidence:
        return "exclude_or_deprioritize_review", "medium", "High non-design/context risk with weak design-object evidence."
    if "source_register:" in risk_text and image in {"IMG00", "IMG04"}:
        return "convert_to_text_or_appendix", "medium", "Source/register evidence should become text or appendix rather than object main."
    if "stamp_or_philatelic:" in risk_text:
        if relation >= 50 and source_depth >= 75 and design_confidence >= 75:
            return "downgrade_to_sub_candidate", "medium", "Stamp/philatelic evidence may support a packet but should not carry main-sheet authority by default."
        return "downgrade_to_card_candidate", "medium", "Stamp/philatelic evidence should be card support unless manually justified as a primary design object."
    if risk >= 55:
        return "downgrade_to_card_candidate", "medium", "Context/photo/stamp/source-file risk should be preserved as card support unless reviewed otherwise."
    if source_chars < 100 and design_confidence < 55 and relation < 25:
        return "downgrade_to_card_candidate", "medium", "Thin source text, weak relation density, and modest design-object confidence."
    if relation >= 45 and anchor < 70:
        return "downgrade_to_sub_candidate", "medium", "Cluster/relation value is present, but standalone anchor strength is not yet high."
    if anchor >= 60 and risk < 35 and source_depth >= 40 and design_confidence >= 60:
        return "keep_main_anchor", "medium", "Enough source depth and design-object evidence for provisional main-anchor treatment."
    if anchor >= 55 and risk < 50 and design_confidence >= 60:
        return "keep_main_add_text", "medium", "Promising anchor, but it needs reviewed editorial text before release."
    if relation >= 30 or source_depth >= 50:
        return "packet_anchor_review", "medium", "May be an anchor or packet member; relation design should decide before mutation."
    return "manual_review", "low", "Signals are mixed; keep in review rather than applying a structural rule."


def calibration_question(action: str) -> str:
    questions = {
        "keep_main_anchor": "Does this truly define a durable research packet anchor?",
        "keep_main_add_text": "What editorial text would justify keeping this as main?",
        "packet_anchor_review": "Is this a packet anchor, sub sheet, or sibling under a stronger main?",
        "downgrade_to_sub_candidate": "Which nearby main should own this as a sub sheet?",
        "downgrade_to_card_candidate": "Would moving this to card hide any meaningful research path?",
        "convert_to_text_or_appendix": "Should this evidence become text, appendix, or source register?",
        "exclude_or_deprioritize_review": "Is this outside graphic design object scope, or useful only as background evidence?",
        "manual_review": "Which signal is decisive: impact, source depth, relation density, or risk?",
    }
    return questions.get(action, "Review structural role.")


def sample_priority(row: dict[str, Any]) -> int:
    action = clean(row.get("recommended_next_action"))
    risk = int(row.get("risk_pressure_score") or 0)
    relation = int(row.get("relation_density_score") or 0)
    source_depth = int(row.get("source_depth_score") or 0)
    editorial_need = int(row.get("editorial_need_score") or 0)
    priority = risk + editorial_need
    if action in {"downgrade_to_card_candidate", "downgrade_to_sub_candidate", "convert_to_text_or_appendix"}:
        priority += 35
    if action == "packet_anchor_review":
        priority += 25
    if relation >= 45:
        priority += 15
    if source_depth < 25:
        priority += 10
    return priority


def group_summary(rows: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(group_key)) or "unknown"].append(row)
    out: list[dict[str, Any]] = []
    for group, values in grouped.items():
        actions = Counter(clean(row.get("recommended_next_action")) for row in values)
        out.append(
            {
                "group": group,
                "main_sheet_count": len(values),
                "keep_main_anchor": actions.get("keep_main_anchor", 0),
                "keep_main_add_text": actions.get("keep_main_add_text", 0),
                "packet_anchor_review": actions.get("packet_anchor_review", 0),
                "downgrade_to_sub_candidate": actions.get("downgrade_to_sub_candidate", 0),
                "downgrade_to_card_candidate": actions.get("downgrade_to_card_candidate", 0),
                "convert_to_text_or_appendix": actions.get("convert_to_text_or_appendix", 0),
                "exclude_or_deprioritize_review": actions.get("exclude_or_deprioritize_review", 0),
                "manual_review": actions.get("manual_review", 0),
                "median_anchor_score": int(median([int(row.get("overall_research_anchor_score") or 0) for row in values])),
                "median_risk_pressure": int(median([int(row.get("risk_pressure_score") or 0) for row in values])),
            }
        )
    out.sort(key=lambda row: (-int(row["main_sheet_count"]), row["group"]))
    return out


def stratified_sample(rows: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            clean(row.get("recommended_next_action")),
            clean(row.get("period_band")),
            clean(row.get("region")),
            clean(row.get("source_family")),
        )
        grouped[key].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: (-int(row.get("sample_priority") or 0), stable_hash(row.get("surface_id"))))
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    keys = sorted(grouped, key=lambda key: (key[0], key[1], key[2], key[3]))
    while len(selected) < target and keys:
        advanced = False
        for key in keys:
            values = grouped[key]
            while values:
                candidate = values.pop(0)
                sid = clean(candidate.get("surface_id"))
                if sid and sid not in seen:
                    selected.append(candidate)
                    seen.add(sid)
                    advanced = True
                    break
            if len(selected) >= target:
                break
        keys = [key for key in keys if grouped[key]]
        if not advanced:
            break
    if len(selected) < target:
        remaining = [row for row in rows if clean(row.get("surface_id")) not in seen]
        remaining.sort(key=lambda row: (-int(row.get("sample_priority") or 0), stable_hash(row.get("surface_id"))))
        selected.extend(remaining[: target - len(selected)])
    return selected


def write_report(
    rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    period_rows: list[dict[str, Any]],
    region_rows: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]],
) -> None:
    actions = Counter(clean(row.get("recommended_next_action")) for row in rows)
    risky = sorted(rows, key=lambda row: (-int(row.get("sample_priority") or 0), clean(row.get("surface_id"))))[:20]
    lines = [
        "# Main/Sub/Text Full Role Assessment v1",
        "",
        "Scope: non-mutating assessment of every main sheet in the local pre-freeze candidate payload.",
        "",
        "This audit does not apply role overrides, rebuild the official payload, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Recommended Next Actions", ""])
    for action, count in actions.most_common():
        lines.append(f"- `{action}`: {count}")
    lines.extend(["", "## Period Pressure", ""])
    for row in period_rows:
        lines.append(
            f"- {row['group']}: main={row['main_sheet_count']}; keep={row['keep_main_anchor']}; "
            f"add_text={row['keep_main_add_text']}; packet_review={row['packet_anchor_review']}; "
            f"sub={row['downgrade_to_sub_candidate']}; card={row['downgrade_to_card_candidate']}; "
            f"text_appendix={row['convert_to_text_or_appendix']}; exclude_review={row['exclude_or_deprioritize_review']}"
        )
    lines.extend(["", "## Largest Region Groups", ""])
    for row in region_rows[:16]:
        lines.append(
            f"- {row['group']}: main={row['main_sheet_count']}; keep={row['keep_main_anchor']}; "
            f"add_text={row['keep_main_add_text']}; packet_review={row['packet_anchor_review']}; "
            f"sub={row['downgrade_to_sub_candidate']}; card={row['downgrade_to_card_candidate']}"
        )
    lines.extend(["", "## Highest-Priority Calibration Rows", ""])
    for row in risky:
        lines.append(
            f"- {row['surface_id']}: action={row['recommended_next_action']}; score={row['overall_research_anchor_score']}; "
            f"risk={row['risk_pressure_score']}; region={row['region']}; year={row['year']}; title={row['title']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `keep_main_anchor` is provisional, not final release approval.",
            "- `keep_main_add_text` means the object may remain main, but needs reviewed editorial text rather than metadata padding.",
            "- `packet_anchor_review` is the core relation-design backlog: these rows may become main anchors, sub sheets, or packet members.",
            "- `downgrade_to_sub_candidate` and `downgrade_to_card_candidate` are review candidates only; they are not automatic changes.",
            "- Risk terms such as event/photo, stamp, source-register, and non-design drift lower main-anchor confidence but do not erase useful evidence.",
            "- Region scarcity and period value are triage signals. They do not upgrade rights, image state, authorship, source authority, or design-object certainty.",
            "",
            "## Next Permitted Action",
            "",
            f"Review `data/prefreeze_main_sub_text_full_role_calibration_sample_v1.csv` ({len(sample_rows)} rows) before any broader sandbox override preview.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = load_payload()
    surfaces = payload.get("surfaces", [])
    main_surfaces = [surface for surface in surfaces if clean(surface.get("publicationRole")) == "main_sheet"]
    dossiers = dossier_by_anchor(payload)
    cluster_counts = Counter(cluster_key(surface) for surface in main_surfaces)
    region_scores = region_scarcity_scores(main_surfaces)
    period_scores = period_value_scores(main_surfaces)
    region_lookup = release_audit.macro_region_lookup()

    rows: list[dict[str, Any]] = []
    for surface in main_surfaces:
        sid = clean(surface.get("surfaceId"))
        year = year_of(surface)
        source = source_text(surface)
        generated = generated_text(surface)
        source_chars = len(source)
        generated_chars = len(generated)
        family = source_family(surface.get("sourceName"))
        region = release_audit.region(surface, region_lookup)
        period = period_band(surface)
        image = image_state(surface)
        dossier_text, dossier_support = dossier_counts(dossiers.get(sid))
        children = len(surface.get("compoundChildren") or [])
        ckey = cluster_key(surface)
        cluster_size = cluster_counts[ckey]
        evidence_text = " ".join(
            clean(surface.get(key))
            for key in (
                "title",
                "sourceName",
                "medium",
                "objectType",
                "sourceDescription",
                "sourceNotes",
                "sourceSubjects",
                "descriptionSummary",
                "classificationRationale",
            )
        )

        text_depth = score_text_depth(source_chars, generated_chars)
        source_depth = score_source_depth(source_chars, family, clean(surface.get("sourceName")))
        relation = score_relation_density(cluster_size, dossier_support, children)
        design_confidence, positive_flags = score_design_confidence(evidence_text, image)
        risk, risk_flags = score_risk_pressure(evidence_text, clean(surface.get("sourceName")))
        region_scarcity = region_scores.get(region, 0)
        period_value = period_scores.get(period, 0)
        editorial_need = max(0, 100 - text_depth)
        anchor = round(
            source_depth * 0.24
            + relation * 0.18
            + text_depth * 0.18
            + design_confidence * 0.24
            + region_scarcity * 0.06
            + period_value * 0.05
            - risk * 0.15
        )
        anchor = max(0, min(100, anchor))
        action, confidence, reason = action_for(
            anchor,
            source_depth,
            relation,
            text_depth,
            design_confidence,
            risk,
            editorial_need,
            source_chars,
            image,
            risk_flags,
            positive_flags,
        )
        row = {
            "surface_id": sid,
            "capture_id": clean(surface.get("sourceRecordId")),
            "year": year or "",
            "period_band": period,
            "five_year_bucket": five_year_bucket(surface),
            "region": region,
            "theme": folder_title(surface, "theme") or "Unresolved theme",
            "source_family": family,
            "source_name": clean(surface.get("sourceName"))[:220],
            "title": clean(surface.get("title"))[:260],
            "image_state": image,
            "source_text_chars": source_chars,
            "generated_text_chars": generated_chars,
            "total_text_chars": source_chars + generated_chars,
            "cluster_key": ckey,
            "cluster_size": cluster_size,
            "dossier_text_pages": dossier_text,
            "dossier_support_pages": dossier_support,
            "compound_children": children,
            "anchor_strength_score": anchor,
            "source_depth_score": source_depth,
            "relation_density_score": relation,
            "text_depth_score": text_depth,
            "design_object_confidence_score": design_confidence,
            "risk_pressure_score": risk,
            "region_scarcity_score": region_scarcity,
            "period_value_score": period_value,
            "editorial_need_score": editorial_need,
            "overall_research_anchor_score": anchor,
            "risk_flags": "; ".join(risk_flags),
            "positive_flags": "; ".join(positive_flags),
            "recommended_next_action": action,
            "action_confidence": confidence,
            "action_reason": reason,
        }
        row["sample_priority"] = sample_priority(row)
        rows.append(row)

    rows.sort(
        key=lambda row: (
            clean(row.get("recommended_next_action")),
            -int(row.get("sample_priority") or 0),
            clean(row.get("period_band")),
            clean(row.get("region")),
            clean(row.get("surface_id")),
        )
    )
    sample_rows = stratified_sample(rows, SAMPLE_TARGET)
    sample_out = [
        {
            **row,
            "calibration_question": calibration_question(clean(row.get("recommended_next_action"))),
            "review_status": "pending",
            "reviewer_notes": "",
        }
        for row in sample_rows
    ]
    period_rows = group_summary(rows, "period_band")
    region_rows = group_summary(rows, "region")
    action_counts = Counter(clean(row.get("recommended_next_action")) for row in rows)
    risk_flags = Counter()
    positive_flags = Counter()
    for row in rows:
        for flag in clean(row.get("risk_flags")).split("; "):
            if flag:
                risk_flags[flag] += 1
        for flag in clean(row.get("positive_flags")).split("; "):
            if flag:
                positive_flags[flag] += 1
    summary_rows: list[dict[str, Any]] = [
        {"metric": "scope", "value": "non_mutating_full_main_assessment", "notes": "No rebuild, no role override, no image download, no rights/image-state change."},
        {"metric": "main_sheets_scanned", "value": len(rows), "notes": "All candidate publicationRole=main_sheet surfaces."},
        {"metric": "calibration_sample_rows", "value": len(sample_rows), "notes": "Stratified sample for next method review."},
        {"metric": "median_anchor_score", "value": int(median([int(row["overall_research_anchor_score"]) for row in rows])) if rows else 0, "notes": "Median overall research anchor score."},
        {"metric": "median_risk_pressure", "value": int(median([int(row["risk_pressure_score"]) for row in rows])) if rows else 0, "notes": "Median risk pressure score."},
    ]
    for action, count in action_counts.most_common():
        summary_rows.append({"metric": f"action:{action}", "value": count, "notes": "Recommended next action distribution."})
    for flag, count in risk_flags.most_common(20):
        summary_rows.append({"metric": f"risk_flag:{flag}", "value": count, "notes": "Risk flag distribution across main sheets."})
    for flag, count in positive_flags.most_common(20):
        summary_rows.append({"metric": f"positive_flag:{flag}", "value": count, "notes": "Design-object positive signal distribution across main sheets."})

    write_csv(OUT_ASSESSMENT, rows, ASSESSMENT_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(OUT_ACTION_PERIOD, period_rows, ACTION_FIELDS)
    write_csv(OUT_ACTION_REGION, region_rows, ACTION_FIELDS)
    write_csv(OUT_SAMPLE, sample_out, SAMPLE_FIELDS)
    write_report(rows, summary_rows, period_rows, region_rows, sample_out)

    print(f"main_sheets_scanned={len(rows)}")
    print(f"calibration_sample_rows={len(sample_out)}")
    print(f"actions={dict(action_counts.most_common())}")
    print(f"wrote {OUT_ASSESSMENT.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_SAMPLE.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
