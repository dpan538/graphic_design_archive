#!/usr/bin/env python3
"""Audit appendix generation rules before rebuilding public payloads.

The current frontend can render AX01-AX06, but the data layer must decide when
an appendix is warranted. This audit proposes appendix packets from real surface
evidence, suppresses repeated AX01 placeholders, and groups appendix evidence at
the research-unit level when linkage data says records belong together.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
DOCS = ROOT / "docs" / "capture"

PAYLOAD = GENERATED / "public_surfaces_v1.json"
GATE_AUDIT = DATA / "surface_assignment_gate_audit_v1.csv"
OUT = DATA / "appendix_generation_rule_audit_v1.csv"
REPORT = DOCS / "APPENDIX_GENERATION_RULE_AUDIT_v1.md"

FIELDS = [
    "research_unit_id",
    "surface_id",
    "source_record_id",
    "title",
    "image_state",
    "layout_id",
    "appendix_role",
    "materiality",
    "evidence_signature",
    "dedupe_status",
    "inherits_from_surface_id",
    "reason",
    "source_name",
    "source_url",
    "display_policy",
    "rights_reviewed",
    "table_rows",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def lower(value: object) -> str:
    return clean(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table_rows(surface: dict) -> int:
    return sum(len(table.get("rows", [])) for table in surface.get("tables", []) if isinstance(table, dict))


def domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def gate_map() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in read_csv(GATE_AUDIT):
        capture_id = row.get("capture_id", "")
        if capture_id:
            out[capture_id] = row
    return out


def source_urls(surface: dict) -> list[str]:
    urls: list[str] = []
    source_url = clean(surface.get("sourceUrl"))
    if source_url:
        urls.append(source_url)
    for table in surface.get("tables", []):
        if table.get("kind") not in {"SOURCE", "CITATIONS"}:
            continue
        for _, value in table.get("rows", []):
            text = clean(value)
            if text.startswith("http://") or text.startswith("https://"):
                urls.append(text)
    seen: list[str] = []
    for url in urls:
        if url not in seen:
            seen.append(url)
    return seen


def text_len(surface: dict) -> int:
    return int(surface.get("sourceReadingTextLength") or surface.get("readingTextLength") or 0)


def display_policy(surface: dict) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    rights = surface.get("rights") if isinstance(surface.get("rights"), dict) else {}
    return clean(image.get("frameBehavior") or rights.get("displayPolicy") or rights.get("display_policy"))


def rights_label(surface: dict) -> str:
    rights = surface.get("rights") if isinstance(surface.get("rights"), dict) else {}
    return clean(rights.get("label") or rights.get("basis") or rights.get("state"))


def review_gates(surface: dict) -> dict:
    return surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}


def research_unit_id(surface: dict, gate: dict[str, str] | None) -> str:
    if gate and gate.get("primary_group_id") and gate.get("requires_group_review") == "true":
        return gate["primary_group_id"]
    return clean(surface.get("surfaceId"))


def make_candidate(surface: dict, gate: dict[str, str] | None, layout_id: str, reason: str, role: str, materiality: str) -> dict[str, str]:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    unit = research_unit_id(surface, gate)
    urls = source_urls(surface)
    signature_parts = [
        layout_id,
        unit,
        clean(surface.get("sourceName")),
        domain(urls[0]) if urls else "",
        image.get("state", ""),
        display_policy(surface),
        rights_label(surface)[:80],
        gate.get("primary_relation_label", "") if gate else "",
    ]
    return {
        "research_unit_id": unit,
        "surface_id": clean(surface.get("surfaceId")),
        "source_record_id": clean(surface.get("sourceRecordId")),
        "title": clean(surface.get("title")),
        "image_state": clean(image.get("state") or "IMG00"),
        "layout_id": layout_id,
        "appendix_role": role,
        "materiality": materiality,
        "evidence_signature": "|".join(signature_parts),
        "dedupe_status": "candidate",
        "inherits_from_surface_id": "",
        "reason": reason,
        "source_name": clean(surface.get("sourceName")),
        "source_url": urls[0] if urls else "",
        "display_policy": display_policy(surface),
        "rights_reviewed": str(bool(review_gates(surface).get("rightsReviewed"))).lower(),
        "table_rows": str(table_rows(surface)),
    }


def candidates_for(surface: dict, gate: dict[str, str] | None) -> list[dict[str, str]]:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    image_state = clean(image.get("state") or "IMG00")
    urls = source_urls(surface)
    policy = display_policy(surface)
    rights = rights_label(surface)
    gate_disp = gate.get("recommended_disposition", "") if gate else ""
    relation = gate.get("primary_relation_label", "") if gate else ""
    primary_action = gate.get("primary_group_action", "") if gate else ""
    protocol_text = " ".join(
        clean(surface.get(key))
        for key in ("historicalContextNote", "classificationRationale", "uncertaintyNote", "citationBasis")
    ).lower()
    rows: list[dict[str, str]] = []

    rights_material = bool(rights or policy or image_state in {"IMG00", "IMG01", "IMG02", "IMG03"})
    rights_needs_appendix = (
        image_state == "IMG00"
        or policy in {"empty_rights_frame", "rights_empty_frame"}
        or gate_disp in {"img00_rights_sheet_candidate", "duplicate_image_review_packet"}
        or (
            image_state in {"IMG01", "IMG02", "IMG03"}
            and review_gates(surface).get("rightsReviewed") is not True
            and any(term in protocol_text for term in ("manual review", "protocol-sensitive", "source-only", "source only", "suppress", "sensitive", "indigenous", "diaspora"))
        )
    )
    if rights_material and rights_needs_appendix:
        rows.append(
            make_candidate(
                surface,
                gate,
                "AX01.rights",
                "rights/image display evidence",
                "rights_evidence",
                "material" if rights else "minimal",
            )
        )

    if len(urls) >= 2 or primary_action == "deduplicate_or_merge_source_records" or relation == "same_entity_confirmed":
        rows.append(
            make_candidate(
                surface,
                gate,
                "AX02.citation",
                "source/citation register or dedupe source ledger",
                "source_register",
                "material",
            )
        )

    folder_count = len(surface.get("folders") or [])
    if gate and gate.get("requires_group_review") == "true" and relation in {"same_work_series_or_campaign", "possibly_same_as", "related_but_not_same", "same_entity_confirmed"}:
        rows.append(
            make_candidate(
                surface,
                gate,
                "AX03.relations",
                "relations/classification evidence",
                "relation_classification",
                "material",
            )
        )

    if any(term in protocol_text for term in ("manual review", "protocol-sensitive", "source-only", "source only", "suppress", "sensitive", "indigenous", "diaspora")):
        rows.append(
            make_candidate(
                surface,
                gate,
                "AX04.context",
                "protocol/context packet",
                "protocol_context",
                "material",
            )
        )

    if text_len(surface) >= 1200 or gate_disp in {"text_or_appendix_review_packet", "support_packet_appendix_text"}:
        rows.append(
            make_candidate(
                surface,
                gate,
                "AX05.statement",
                "source verification and reading statement",
                "source_statement",
                "material" if text_len(surface) >= 160 else "minimal",
            )
        )

    if primary_action in {"canonical_main_with_child_text_appendix", "support_packet_or_compound_sheet_candidate"}:
        rows.append(
            make_candidate(
                surface,
                gate,
                "AX06.typed-index",
                "group/compound index packet",
                "typed_group_index",
                "material",
            )
        )

    return rows


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    gates = gate_map()
    raw_candidates: list[dict[str, str]] = []
    for surface in payload.get("surfaces", []):
        gate = gates.get(clean(surface.get("sourceRecordId")))
        raw_candidates.extend(candidates_for(surface, gate))

    by_unit_layout_signature: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in raw_candidates:
        key = (row["research_unit_id"], row["layout_id"])
        by_unit_layout_signature[key].append(row)

    final_rows: list[dict[str, str]] = []
    suppressed = 0
    inherited = 0
    for items in by_unit_layout_signature.values():
        anchor = max(items, key=lambda row: (row["materiality"] == "material", int(row["table_rows"] or 0), row["surface_id"]))
        anchor = dict(anchor)
        if anchor["materiality"] == "minimal" and anchor["layout_id"] != "AX01.rights":
            suppressed += len(items)
            continue
        anchor["dedupe_status"] = "emit"
        final_rows.append(anchor)
        for item in items:
            if item is anchor or item["surface_id"] == anchor["surface_id"]:
                continue
            inherited_row = dict(item)
            inherited_row["dedupe_status"] = "inherit"
            inherited_row["inherits_from_surface_id"] = anchor["surface_id"]
            final_rows.append(inherited_row)
            inherited += 1

    final_rows.sort(key=lambda row: (row["research_unit_id"], row["layout_id"], row["dedupe_status"], row["surface_id"]))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(final_rows)

    emitted = [row for row in final_rows if row["dedupe_status"] == "emit"]
    layout_counts = Counter(row["layout_id"] for row in emitted)
    status_counts = Counter(row["dedupe_status"] for row in final_rows)
    unit_counts = Counter(row["research_unit_id"] for row in emitted)
    repeat_units = sum(1 for count in unit_counts.values() if count > 3)
    placeholder_like = sum(1 for row in emitted if row["materiality"] == "minimal")

    lines = [
        "# Appendix Generation Rule Audit v1",
        "",
        "Date: 2026-06-01",
        "",
        "Scope: generated public surfaces plus the stricter surface gate audit. This proposes AX01-AX06 packets from real evidence and suppresses repeated placeholders before any rebuild.",
        "",
        "## Summary",
        "",
        f"- Raw appendix candidates: {len(raw_candidates)}",
        f"- Rows written including inherited references: {len(final_rows)}",
        f"- Emitted appendix packets: {len(emitted)}",
        f"- Inherited/suppressed duplicate references: {inherited}",
        f"- Suppressed minimal non-rights placeholders: {suppressed}",
        f"- Emitted minimal AX01 packets: {placeholder_like}",
        f"- Research units with more than three appendix packets: {repeat_units}",
        "",
        "## Emitted Layouts",
        "",
    ]
    lines += [f"- `{key}`: {value}" for key, value in layout_counts.most_common()]
    lines += ["", "## Dedupe Status", ""]
    lines += [f"- `{key}`: {value}" for key, value in status_counts.most_common()]
    lines += ["", "## Rules", ""]
    lines += [
        "- AX01 can support IMG00/IMG01/IMG02/IMG03 when rights/display evidence is material.",
        "- Identical AX01 evidence within the same research unit is emitted once; child rows inherit it.",
        "- AX02 is reserved for source/citation registers, multi-source rows, and dedupe ledgers.",
        "- AX03 is for relation/classification evidence, not visual similarity as causality.",
        "- AX04 is for protocol/context/sensitive/source-only cases.",
        "- AX05 is for source-reading or verification statements.",
        "- AX06 is for group/compound typed indexes.",
    ]
    lines += ["", "## First Emitted Packets", ""]
    for row in emitted[:25]:
        lines.append(
            f"- {row['layout_id']} | {row['research_unit_id']} | {row['surface_id']} | {row['reason']} | {row['title'][:90]}"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(final_rows)} rows)")
    print(f"Wrote {REPORT}")
    print(f"emitted={len(emitted)} layouts={dict(layout_counts)}")
    print(f"inherited={inherited} suppressed={suppressed} placeholder_like={placeholder_like}")


if __name__ == "__main__":
    main()
