#!/usr/bin/env python3
"""Harden region/geography auto-apply suggestions before any archive mutation.

This audit reads the existing region geo auto-apply queue and separates it into
records that can be sampled for later batch application and records that must
stay in manual quarantine. It does not rewrite archive data.
"""

from __future__ import annotations

import re
from collections import Counter

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, read_payload, write_csv


READY = DATA / "region_geo_ready_for_auto_apply_v1.csv"
OUTPUT_HARDENED = DATA / "region_geo_auto_apply_hardened_v1.csv"
OUTPUT_QUARANTINE = DATA / "region_geo_auto_apply_quarantine_v1.csv"
OUTPUT_SUMMARY = DATA / "region_geo_auto_apply_hardening_summary_v1.csv"
OUTPUT_REPORT = DOCS / "REGION_GEO_AUTO_APPLY_HARDENING_v1.md"

HARDENED_FIELDS = [
    "hardening_id",
    "suggestion_id",
    "surface_id",
    "source_record_id",
    "current_label",
    "suggested_label",
    "suggested_region_id",
    "suggested_geo_id",
    "action_status",
    "sample_required_before_mutation",
    "automatic_archive_mutation",
    "blocking_flags",
    "advisory_flags",
    "primary_country_labels",
    "secondary_country_labels",
    "suggested_in_primary_evidence",
    "suggested_in_secondary_evidence",
    "current_in_primary_evidence",
    "years_found",
    "source_family",
    "source_family_cluster_size",
    "title",
    "source_name",
    "place_text",
    "source_subjects",
    "evidence",
]

SUMMARY_FIELDS = ["metric", "value"]

DISPUTED_PERIODS = [
    (1846, 1848, {"Mexico", "United States"}),
    (1910, 1920, {"Mexico"}),
    (1931, 1945, {"China", "Japan", "Korea", "Taiwan", "Russia", "Germany", "France", "Italy"}),
    (1939, 1945, {"France", "Germany", "Italy", "Japan", "Poland", "Austria"}),
    (1947, 1991, {"Germany", "Russia", "Ukraine", "Georgia", "Armenia", "Azerbaijan"}),
    (1949, 1990, {"Germany"}),
]

MANUAL_ALIASES = {
    "Argentina": {"argentina", "argentine", "buenos aires"},
    "Brazil": {"brazil", "brazilian", "rio de janeiro", "sao paulo", "sao jose"},
    "Chile": {"chile", "chilean", "santiago"},
    "Egypt": {"egypt", "egyptian", "cairo"},
    "France": {"france", "french", "paris"},
    "Germany": {"germany", "german", "deutschland", "munich", "munchen", "muenchen", "berlin"},
    "India": {"india", "indian", "mumbai", "bombay", "delhi"},
    "Italy": {"italy", "italian", "rome", "roma", "milan", "milano", "turin", "tuscany"},
    "Japan": {"japan", "japanese", "tokyo"},
    "Mexico": {"mexico", "mexican", "matamoros", "tamaulipas", "ciudad de mexico"},
    "Russia": {"russia", "russian", "soviet", "ussr", "moscow", "minsk"},
    "South Africa": {"south africa", "south african", "cape town", "johannesburg"},
    "Turkey": {"turkey", "turkish", "istanbul", "constantinople"},
    "United Kingdom": {
        "united kingdom",
        "uk",
        "u k",
        "britain",
        "british",
        "england",
        "english",
        "london",
        "scotland",
        "wales",
    },
    "United States": {
        "united states",
        "u s",
        "u s a",
        "usa",
        "american",
        "new york",
        "chicago",
        "california",
        "philadelphia",
    },
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def surface_index() -> dict[str, dict]:
    return {clean(surface.get("surfaceId")): surface for surface in read_payload().get("surfaces", [])}


def country_labels() -> set[str]:
    labels = set()
    for row in read_csv(DATA / "geographies.csv"):
        geo_type = clean(row.get("geo_type"))
        if "country" in geo_type or "territory" in geo_type:
            name = clean(row.get("name"))
            if name and "/" not in name:
                labels.add(name)
    labels.update(MANUAL_ALIASES)
    return labels


def alias_map(labels: set[str]) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    for label in labels:
        aliases[label] = {norm(label)}
        aliases[label].update(MANUAL_ALIASES.get(label, set()))
        aliases[label] = {norm(value) for value in aliases[label] if value}
    return aliases


def labels_in_text(value: str, aliases: dict[str, set[str]]) -> set[str]:
    text = f" {norm(value)} "
    found = set()
    for label, terms in aliases.items():
        for term in terms:
            if term and f" {term} " in text:
                found.add(label)
                break
    return found


def parse_years(value: object) -> list[int]:
    years = []
    for year in re.findall(r"\b(1[7-9]\d{2}|20[0-2]\d)\b", clean(value)):
        try:
            years.append(int(year))
        except ValueError:
            continue
    return years


def disputed_year_for_label(years: list[int], label: str) -> bool:
    for year in years:
        for start, end, labels in DISPUTED_PERIODS:
            if start <= year <= end and label in labels:
                return True
    return False


def stamp_issuer_conflicts_with_suggested(primary_text: str, suggested: str, aliases: dict[str, set[str]]) -> bool:
    text = clean(primary_text).lower()
    suggested_terms = aliases.get(suggested, {norm(suggested)})
    for match in re.finditer(r"\bstamp of\s+([^-/,:;().0-9]+)", text):
        issuer = norm(match.group(1))
        if issuer and not any(term and f" {term} " in f" {issuer} " for term in suggested_terms):
            return True
    return False


def source_family(surface: dict, row: dict[str, str]) -> str:
    text = norm(clean(surface.get("sourceName")) or row.get("source_file", ""))
    if "wikimedia commons" in text:
        return "wikimedia_commons"
    if "cooper hewitt" in text:
        return "cooper_hewitt"
    if "gallica" in text or "bnf" in text:
        return "gallica_bnf"
    if "library of congress" in text:
        return "library_of_congress"
    if "internet archive" in text:
        return "internet_archive"
    if "museum" in text:
        return "museum_or_collection"
    if not text:
        return "unknown_source_family"
    return text[:48].replace(" ", "_")


def flag_row(row: dict[str, str], surface: dict, aliases: dict[str, set[str]]) -> tuple[list[str], list[str], set[str], set[str], dict[str, bool]]:
    current = clean(row.get("current_label"))
    suggested = clean(row.get("suggested_label"))
    title = clean(surface.get("title")) or clean(row.get("title"))
    source_name = clean(surface.get("sourceName"))
    source_url = clean(surface.get("sourceUrl"))
    place_text = clean(surface.get("placeText"))
    subjects = clean(surface.get("sourceSubjects"))
    evidence = clean(row.get("evidence"))

    primary_text = " ".join([title, source_name, source_url])
    secondary_text = " ".join([place_text, subjects, evidence])
    primary_labels = labels_in_text(primary_text, aliases)
    secondary_labels = labels_in_text(secondary_text, aliases)

    suggested_in_primary = suggested in primary_labels
    suggested_in_secondary = suggested in secondary_labels
    current_in_primary = current in primary_labels if current != suggested else False
    other_primary = sorted(label for label in primary_labels if label not in {suggested, current})

    years = parse_years(row.get("years_found")) or parse_years(" ".join([title, place_text, subjects, evidence]))

    blocking = []
    advisory = []
    if row.get("auto_apply_eligible") != "true":
        blocking.append("not_marked_auto_apply_eligible")
    if row.get("confidence_level") != "high":
        blocking.append("not_high_confidence")
    if row.get("requires_date_check") == "true":
        blocking.append("requires_date_check")
    if row.get("external_validation_status") == "contradicted":
        blocking.append("external_validation_contradicted")
    if clean(row.get("suggested_action")) not in {"apply_directly", ""}:
        blocking.append("suggested_action_not_direct_apply")
    if not suggested_in_primary:
        blocking.append("suggested_absent_from_title_source_url")
    if not suggested_in_secondary:
        blocking.append("suggested_absent_from_place_subjects_evidence")
    if current_in_primary:
        blocking.append("current_label_present_in_title_source_url")
    if other_primary:
        blocking.append("other_country_present_in_title_source_url:" + "|".join(other_primary[:5]))
    if suggested == "Mexico" and " new mexico " in f" {norm(primary_text)} ":
        blocking.append("new_mexico_subnational_ambiguity")
    if stamp_issuer_conflicts_with_suggested(primary_text, suggested, aliases):
        blocking.append("stamp_issuer_conflicts_with_suggested_label")
    if disputed_year_for_label(years, suggested):
        blocking.append("historical_dispute_period_for_suggested_label")
    if not years:
        advisory.append("missing_year")
    elif max(years) < 1992:
        advisory.append("pre_1992_sample_required")
    if source_family(surface, row) == "wikimedia_commons":
        advisory.append("commons_metadata_sample_required")
    if len(primary_labels | secondary_labels) > 2:
        advisory.append("multi_country_context")

    bools = {
        "suggested_in_primary": suggested_in_primary,
        "suggested_in_secondary": suggested_in_secondary,
        "current_in_primary": current_in_primary,
    }
    return blocking, advisory, primary_labels, secondary_labels, bools


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    ready = read_csv(READY)
    surfaces = surface_index()
    labels = country_labels()
    aliases = alias_map(labels)
    family_counts = Counter(source_family(surfaces.get(clean(row.get("surface_id")), {}), row) for row in ready)

    hardened = []
    quarantine = []
    all_rows = []
    for idx, row in enumerate(ready, start=1):
        surface = surfaces.get(clean(row.get("surface_id")), {})
        blocking, advisory, primary_labels, secondary_labels, bools = flag_row(row, surface, aliases)
        family = source_family(surface, row)
        status = "hardened_ready_after_sample" if not blocking else "quarantine_manual_review"
        out = {
            "hardening_id": f"RG-HARDEN-{idx:04d}",
            "suggestion_id": row.get("suggestion_id", ""),
            "surface_id": row.get("surface_id", ""),
            "source_record_id": row.get("source_record_id", ""),
            "current_label": row.get("current_label", ""),
            "suggested_label": row.get("suggested_label", ""),
            "suggested_region_id": row.get("suggested_region_id", ""),
            "suggested_geo_id": row.get("suggested_geo_id", ""),
            "action_status": status,
            "sample_required_before_mutation": "true",
            "automatic_archive_mutation": "false",
            "blocking_flags": "; ".join(blocking),
            "advisory_flags": "; ".join(advisory),
            "primary_country_labels": "; ".join(sorted(primary_labels)),
            "secondary_country_labels": "; ".join(sorted(secondary_labels)),
            "suggested_in_primary_evidence": str(bools["suggested_in_primary"]).lower(),
            "suggested_in_secondary_evidence": str(bools["suggested_in_secondary"]).lower(),
            "current_in_primary_evidence": str(bools["current_in_primary"]).lower(),
            "years_found": row.get("years_found", ""),
            "source_family": family,
            "source_family_cluster_size": str(family_counts[family]),
            "title": clean(surface.get("title")) or row.get("title", ""),
            "source_name": clean(surface.get("sourceName")),
            "place_text": clean(surface.get("placeText")),
            "source_subjects": clean(surface.get("sourceSubjects")),
            "evidence": row.get("evidence", ""),
        }
        all_rows.append(out)
        if blocking:
            quarantine.append(out)
        else:
            hardened.append(out)
    return hardened, quarantine, all_rows


def write_report(hardened: list[dict[str, str]], quarantine: list[dict[str, str]], all_rows: list[dict[str, str]]) -> None:
    status_counts = Counter(row["action_status"] for row in all_rows)
    label_counts = Counter(row["suggested_label"] for row in all_rows)
    hardened_labels = Counter(row["suggested_label"] for row in hardened)
    quarantine_labels = Counter(row["suggested_label"] for row in quarantine)
    blocking_counts = Counter()
    advisory_counts = Counter()
    for row in all_rows:
        for flag in row["blocking_flags"].split("; "):
            if flag:
                blocking_counts[flag.split(":")[0]] += 1
        for flag in row["advisory_flags"].split("; "):
            if flag:
                advisory_counts[flag] += 1

    summary_rows = [
        {"metric": "input_ready_rows", "value": str(len(all_rows))},
        {"metric": "hardened_ready_after_sample", "value": str(len(hardened))},
        {"metric": "quarantine_manual_review", "value": str(len(quarantine))},
    ]
    for key, value in status_counts.most_common():
        summary_rows.append({"metric": f"status_{key}", "value": str(value)})
    for key, value in blocking_counts.most_common():
        summary_rows.append({"metric": f"blocking_{key}", "value": str(value)})
    for key, value in advisory_counts.most_common():
        summary_rows.append({"metric": f"advisory_{key}", "value": str(value)})

    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Region/Geography Auto-Apply Hardening v1",
        "",
        "This audit tightens the existing region/geography auto-apply queue before any archive mutation.",
        "It is advisory and dry-run only: `automatic_archive_mutation=false` for every row.",
        "",
        "## Result",
        "",
        f"- input ready rows: {len(all_rows)}",
        f"- hardened rows requiring sample before mutation: {len(hardened)}",
        f"- quarantine/manual rows: {len(quarantine)}",
        "",
        "## Blocking Flags",
        "",
    ]
    if blocking_counts:
        for key, value in blocking_counts.most_common():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Advisory Flags", ""])
    if advisory_counts:
        for key, value in advisory_counts.most_common():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Suggested Labels", ""])
    for key, value in label_counts.most_common():
        lines.append(f"- {key}: {value} total; {hardened_labels[key]} hardened; {quarantine_labels[key]} quarantined")

    lines.extend(
        [
            "",
            "## Method Notes",
            "",
            "- The previous ready queue is not treated as enough evidence by itself.",
            "- A row remains batch-candidate only when the suggested country appears in title/source/source URL evidence and in place/subject/evidence fields.",
            "- Rows are quarantined when another country or the current label is visible in title/source evidence.",
            "- Historical dispute periods and external contradictions block automated use.",
            "- All surviving rows still require sampling before any future mutation.",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_HARDENED.relative_to(ROOT)}`",
            f"- `{OUTPUT_QUARANTINE.relative_to(ROOT)}`",
            f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    hardened, quarantine, all_rows = build_rows()
    write_csv(OUTPUT_HARDENED, hardened, HARDENED_FIELDS)
    write_csv(OUTPUT_QUARANTINE, quarantine, HARDENED_FIELDS)
    write_report(hardened, quarantine, all_rows)
    print(f"input_ready_rows={len(all_rows)}")
    print(f"hardened_ready_after_sample={len(hardened)}")
    print(f"quarantine_manual_review={len(quarantine)}")
    print(f"wrote {OUTPUT_HARDENED.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_QUARANTINE.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
