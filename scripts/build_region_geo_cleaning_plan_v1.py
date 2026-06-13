#!/usr/bin/env python3
"""Build a region/geography cleaning plan from scored enrichment queues.

This is a planning artifact only. It does not rewrite surfaces, records,
regions, geographies, or capture data.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, read_payload, write_csv


READY = DATA / "region_geo_ready_for_auto_apply_v1.csv"
HARDENED_READY = DATA / "region_geo_auto_apply_hardened_v1.csv"
MANUAL = DATA / "region_geo_priority_manual_review_v1.csv"
HISTORICAL = DATA / "region_geo_requires_historical_split_review_v1.csv"

OUTPUT_ACTIONS = DATA / "region_geo_cleaning_action_plan_v1.csv"
OUTPUT_CLUSTERS = DATA / "region_geo_manual_review_clusters_v1.csv"
OUTPUT_REPORT = DOCS / "REGION_GEO_CLEANING_PLAN_v1.md"

ACTION_FIELDS = [
    "plan_id",
    "surface_id",
    "source_record_id",
    "current_label",
    "suggested_label",
    "suggested_region_id",
    "suggested_geo_id",
    "action_status",
    "action_type",
    "pre_apply_check",
    "source_family",
    "source_family_cluster_size",
    "same_title_cluster_size",
    "years_found",
    "risk_flags",
    "place_text",
    "source_subjects",
    "source_name",
    "title",
    "evidence",
]

CLUSTER_FIELDS = [
    "cluster_id",
    "review_priority",
    "suggestion_type",
    "suggested_label",
    "risk_flags",
    "row_count",
    "source_family_count",
    "sample_surface_ids",
    "sample_titles",
    "recommended_review_action",
]


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def surface_index() -> dict[str, dict]:
    return {clean(surface.get("surfaceId")): surface for surface in read_payload().get("surfaces", [])}


def country_labels() -> set[str]:
    labels = set()
    for row in read_csv(DATA / "geographies.csv"):
        if clean(row.get("geo_type")) in {"country_context", "country/territory_context", "city/territory_context"}:
            labels.add(clean(row.get("name")))
    labels.update({"United States", "Mexico", "Russia", "Brazil", "Argentina", "Egypt", "Chile"})
    return {label for label in labels if label}


def labels_in_text(value: str, labels: set[str]) -> set[str]:
    text = f" {norm(value)} "
    return {label for label in labels if f" {norm(label)} " in text}


def source_family(value: str) -> str:
    text = norm(value)
    if not text:
        return "unknown_source_family"
    families = [
        ("wikimedia_commons", "wikimedia commons"),
        ("cooper_hewitt", "cooper hewitt"),
        ("gallica_bnf", "gallica bnf"),
        ("library_of_congress", "library of congress"),
        ("dpla", "dpla"),
        ("europeana", "europeana"),
        ("internet_archive", "internet archive"),
        ("museum_api", "museum"),
    ]
    for family, marker in families:
        if marker in text:
            return family
    return text[:48].replace(" ", "_")


def action_queue_path() -> tuple:
    if HARDENED_READY.exists():
        return HARDENED_READY, "hardened auto-apply queue"
    return READY, "original auto-apply queue"


def high_signal_contains(surface: dict, label: str) -> bool:
    label_norm = norm(label)
    if not label_norm:
        return False
    fields = [surface.get("placeText"), surface.get("sourceSubjects")]
    return any(f" {label_norm} " in f" {norm(value)} " for value in fields)


def build_action_rows() -> list[dict[str, str]]:
    queue_path, _ = action_queue_path()
    ready = read_csv(queue_path)
    surfaces = surface_index()
    countries = country_labels()
    family_counts: Counter[str] = Counter()
    title_counts: Counter[str] = Counter()
    for row in ready:
        surface = surfaces.get(clean(row.get("surface_id")), {})
        family_counts[source_family(clean(surface.get("sourceName")) or row.get("source_file", ""))] += 1
        title_counts[norm(row.get("title"))] += 1

    rows: list[dict[str, str]] = []
    for idx, row in enumerate(ready, start=1):
        surface = surfaces.get(clean(row.get("surface_id")), {})
        family = source_family(clean(surface.get("sourceName")) or row.get("source_file", ""))
        checks = []
        title_labels = labels_in_text(row.get("title", ""), countries)
        other_title_labels = sorted(label for label in title_labels if label != clean(row.get("suggested_label")))
        if clean(row.get("current_label")) == clean(row.get("suggested_label")):
            checks.append("already_matches_target")
        if clean(row.get("current_label")) in title_labels and clean(row.get("current_label")) != clean(row.get("suggested_label")):
            checks.append("current_label_appears_in_title")
        if other_title_labels:
            checks.append("other_country_label_appears_in_title:" + "|".join(other_title_labels[:4]))
        if not high_signal_contains(surface, row.get("suggested_label", "")):
            checks.append("target_not_in_high_signal_surface_fields")
        if row.get("external_validation_status") == "contradicted":
            checks.append("external_contradiction")
        if not clean(row.get("years_found")):
            checks.append("missing_year")

        if checks:
            status = "spot_check_before_apply"
        else:
            status = "ready_for_batch_apply_after_sample_audit"

        rows.append(
            {
                "plan_id": f"RG-CLEAN-ACT-{idx:04d}",
                "surface_id": row.get("surface_id", ""),
                "source_record_id": row.get("source_record_id", ""),
                "current_label": row.get("current_label", ""),
                "suggested_label": row.get("suggested_label", ""),
                "suggested_region_id": row.get("suggested_region_id", ""),
                "suggested_geo_id": row.get("suggested_geo_id", ""),
                "action_status": status,
                "action_type": "region_geo_relabel_dry_run",
                "pre_apply_check": "; ".join(checks) if checks else "sample_audit_required",
                "source_family": family,
                "source_family_cluster_size": str(family_counts[family]),
                "same_title_cluster_size": str(title_counts[norm(row.get("title"))]),
                "years_found": row.get("years_found", ""),
                "risk_flags": row.get("risk_flags", ""),
                "place_text": clean(surface.get("placeText")),
                "source_subjects": clean(surface.get("sourceSubjects")),
                "source_name": clean(surface.get("sourceName")),
                "title": row.get("title", ""),
                "evidence": row.get("evidence", ""),
            }
        )
    return rows


def recommended_cluster_action(row: dict[str, str]) -> str:
    priority = row.get("review_priority")
    suggestion_type = row.get("suggestion_type")
    risk = row.get("risk_flags", "")
    label = row.get("suggested_label", "")
    if priority == "P1_date_sensitive_medium":
        return "sample_dates_then_decide_split_or_modern_country_mapping"
    if suggestion_type == "pending_text_resurface" and label in {"Indonesia", "Caucasus", "Azerbaijan", "Georgia"}:
        return "audit_as_large_cluster_before_mapping_topic_vs_source_geography"
    if "low_signal_field" in risk:
        return "use_only_as_capture_or_review_hint"
    if priority == "P1_medium_review":
        return "sample_5_to_10_then_promote_rules_if_consistent"
    return "manual_review_only"


def build_cluster_rows() -> list[dict[str, str]]:
    manual_rows = read_csv(MANUAL)
    surfaces = surface_index()
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in manual_rows:
        key = (
            row.get("review_priority", ""),
            row.get("suggestion_type", ""),
            row.get("suggested_label", ""),
            row.get("risk_flags", ""),
        )
        groups[key].append(row)

    clusters = []
    sorted_groups = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    for idx, ((priority, suggestion_type, label, risk), rows) in enumerate(sorted_groups, start=1):
        families = Counter(
            source_family(clean(surfaces.get(clean(row.get("surface_id")), {}).get("sourceName")) or row.get("source_file", ""))
            for row in rows
        )
        sample = rows[:5]
        clusters.append(
            {
                "cluster_id": f"RG-CLEAN-CLUSTER-{idx:04d}",
                "review_priority": priority,
                "suggestion_type": suggestion_type,
                "suggested_label": label,
                "risk_flags": risk,
                "row_count": str(len(rows)),
                "source_family_count": str(len(families)),
                "sample_surface_ids": "; ".join(row.get("surface_id", "") for row in sample),
                "sample_titles": " | ".join(clean(row.get("title"))[:120] for row in sample),
                "recommended_review_action": recommended_cluster_action(rows[0]),
            }
        )
    return clusters


def write_report(actions: list[dict[str, str]], clusters: list[dict[str, str]]) -> None:
    queue_path, queue_label = action_queue_path()
    historical = read_csv(HISTORICAL)
    action_status = Counter(row["action_status"] for row in actions)
    action_labels = Counter(row["suggested_label"] for row in actions)
    cluster_labels = Counter()
    cluster_rows_by_priority = Counter()
    for row in clusters:
        cluster_labels[row["suggested_label"]] += int(row["row_count"])
        cluster_rows_by_priority[row["review_priority"]] += int(row["row_count"])
    historical_labels = Counter(row.get("suggested_label") for row in historical)

    lines = [
        "# Region/Geography Cleaning Plan v1",
        "",
        "This plan is dry-run only. It prepares review and application queues without mutating archive data.",
        f"Action queue source: `{queue_path.relative_to(ROOT)}` ({queue_label}).",
        "",
        "## Batch Action Queue",
        "",
        f"- action rows: {len(actions)}",
    ]
    for key, value in action_status.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "### Auto-Candidate Labels", ""])
    for key, value in action_labels.most_common():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Manual Review Compression", "", f"- compressed clusters: {len(clusters)}"])
    for key, value in cluster_rows_by_priority.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "### Largest Manual Labels", ""])
    for key, value in cluster_labels.most_common(15):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Historical Split Queue", "", f"- historical split rows: {len(historical)}"])
    for key, value in historical_labels.most_common(10):
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Recommended Next Cleaning Order",
            "",
            f"1. Spot-check the {len(actions)} action rows by label/source family before applying any mapping.",
            "2. Review the 220 Mexico / United States military occupation rows as a historical-context policy decision, not a simple country relabel.",
            "3. Audit the large pending-text clusters for Indonesia, Caucasus, Azerbaijan, Georgia, and Singapore to separate source geography from topic geography.",
            "4. Convert confirmed cluster rules into a second, narrower auto-map pass only after review evidence is consistent.",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_ACTIONS.relative_to(ROOT)}`",
            f"- `{OUTPUT_CLUSTERS.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    actions = build_action_rows()
    clusters = build_cluster_rows()
    write_csv(OUTPUT_ACTIONS, actions, ACTION_FIELDS)
    write_csv(OUTPUT_CLUSTERS, clusters, CLUSTER_FIELDS)
    write_report(actions, clusters)
    print(f"cleaning_action_rows={len(actions)}")
    print(f"manual_review_clusters={len(clusters)}")
    print(f"wrote {OUTPUT_ACTIONS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_CLUSTERS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
