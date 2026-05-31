from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATHS = [
    ROOT / "generated" / "public_surfaces_v1.json",
    ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json",
    ROOT / "frontend" / "public" / "data" / "public_surface_mock_v0.json",
]


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def year_range(items: list[dict[str, Any]]) -> tuple[int | None, int | None, str]:
    years: list[int] = []
    for item in items:
        for key in ("dateStart", "dateEnd"):
            value = item.get(key)
            if isinstance(value, int):
                years.append(value)
    if not years:
        return None, None, "undated"
    start, end = min(years), max(years)
    return start, end, str(start) if start == end else f"{start}-{end}"


def source_host(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url or "")
    return match.group(1).replace("www.", "") if match else ""


def compound_child(surface: dict[str, Any]) -> dict[str, str]:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return {
        "title": surface.get("title", ""),
        "dateText": surface.get("dateText", ""),
        "sourceName": surface.get("sourceName", ""),
        "sourceUrl": surface.get("sourceUrl", ""),
        "imageState": image.get("state", "IMG00"),
        "note": surface.get("descriptionSummary")
        or surface.get("sourceDescription")
        or surface.get("sourceNotes")
        or "Grouped with related source records from the same archive/source.",
    }


def representative_image(items: list[dict[str, Any]]) -> dict[str, Any]:
    priority = {"IMG03": 0, "IMG02": 1, "IMG01": 2, "IMG00": 3, "IMG04": 4}
    candidates = sorted(
        (
            item.get("image", {})
            for item in items
            if isinstance(item.get("image"), dict)
        ),
        key=lambda image: priority.get(image.get("state", "IMG00"), 9),
    )
    for image in candidates:
        if image.get("state") in {"IMG01", "IMG02", "IMG03"} and image.get("url"):
            return {
                "state": image.get("state"),
                "hasImageFrame": True,
                "url": image.get("url"),
                "credit": image.get("credit"),
                "licenseLabel": (
                    image.get("licenseLabel")
                    or "Representative image selected from grouped source records."
                ),
            }
    return {
        "state": "IMG00",
        "hasImageFrame": True,
        "url": None,
        "credit": None,
        "licenseLabel": "Grouped source links; image display withheld until item-level review.",
    }


def make_group_surface(items: list[dict[str, Any]], group_index: int) -> dict[str, Any]:
    first = deepcopy(items[0])
    start, end, span = year_range(items)
    host = source_host(first.get("sourceUrl", ""))
    source_name = first.get("sourceName") or host or "Source group"
    title = first.get("title", "")
    generic_title = norm(title) in {norm(source_name), norm(host), "chineseposters.net"}
    group_title = (
        f"{source_name} grouped records, {span}"
        if generic_title
        else f"{title} grouped records, {span}"
    )

    group_id = f"{first.get('surfaceId', 'SURF-GROUP')}-GROUP"
    first.update(
        {
            "surfaceId": group_id,
            "sourceRecordId": f"{first.get('sourceRecordId', group_id)}-GROUP",
            "surfaceType": "sheet",
            "templateId": "sheet.compound.v0",
            "layoutHint": "compound",
            "title": group_title,
            "dateStart": start,
            "dateEnd": end,
            "dateText": span,
            "descriptionSummary": (
                f"{len(items)} related records from {source_name} were grouped "
                "because they share a repeated or source-generic title. The "
                "group is preserved as one intellectual unit while each original "
                "source link remains available below."
            ),
            "sourceDescription": (
                "Grouped duplicate/source-generic records. This prevents repeated "
                "archive labels from reading as separate designed sheets."
            ),
            "completenessScore": max(item.get("completenessScore", 0) for item in items),
            "compoundChildren": [compound_child(item) for item in items],
        }
    )

    first["image"] = representative_image(items)

    first["tables"] = [
        {
            "kind": "SOURCE",
            "rows": [
                ["source", source_name],
                ["grouped records", str(len(items))],
                ["group reason", "Repeated or source-generic title"],
                ["first source", first.get("sourceUrl", "")],
            ],
        },
        {
            "kind": "NORMALIZED",
            "rows": [
                ["surface type", "compound sheet"],
                ["date span", span],
                ["record group", f"duplicate-title-group-{group_index:03d}"],
            ],
        },
        {
            "kind": "RIGHTS",
            "rows": [
                ["image state", first["image"]["state"]],
                ["member image states", "; ".join(f"{k}: {v}" for k, v in sorted(Counter((item.get("image") or {}).get("state", "IMG00") for item in items).items()))],
                ["policy", "representative image from grouped records when rights state permits"],
            ],
        },
        {
            "kind": "CITATIONS",
            "rows": [["source links", "; ".join(item.get("sourceUrl", "") for item in items[:6])]],
        },
    ]
    return first


def should_group(items: list[dict[str, Any]]) -> bool:
    if len(items) < 3:
        return False
    title = norm(items[0].get("title", ""))
    source = norm(items[0].get("sourceName", ""))
    host = norm(source_host(items[0].get("sourceUrl", "")))
    return title in {source, host, "chineseposters.net"} or len(set(item.get("title", "") for item in items)) == 1


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    surfaces = payload.get("surfaces", [])
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        key = (norm(surface.get("sourceName", "")), norm(surface.get("title", "")))
        groups[key].append(surface)

    replacement: dict[str, dict[str, Any]] = {}
    group_members: dict[str, list[str]] = {}
    remove_ids: set[str] = set()
    group_index = 1
    for items in groups.values():
        if not should_group(items):
            continue
        group_surface = make_group_surface(items, group_index)
        group_index += 1
        replacement[items[0]["surfaceId"]] = group_surface
        group_members[group_surface["surfaceId"]] = [item["surfaceId"] for item in items]
        remove_ids.update(item["surfaceId"] for item in items[1:])

    if not replacement:
        return payload

    next_surfaces: list[dict[str, Any]] = []
    for surface in surfaces:
        sid = surface["surfaceId"]
        if sid in remove_ids:
            continue
        next_surfaces.append(replacement.get(sid, surface))
    payload["surfaces"] = next_surfaces

    first_id_to_group = {old_id: group["surfaceId"] for old_id, group in replacement.items()}
    all_removed_to_group: dict[str, str] = {}
    for old_id, group in replacement.items():
        for member_id in group_members.get(group["surfaceId"], []):
            all_removed_to_group[member_id] = group["surfaceId"]
        all_removed_to_group[old_id] = group["surfaceId"]

    valid_ids = {surface["surfaceId"] for surface in next_surfaces}
    for folder in payload.get("folders", []):
        rewritten: list[str] = []
        seen: set[str] = set()
        for sid in folder.get("surfaceIds", []):
            target = all_removed_to_group.get(sid, first_id_to_group.get(sid, sid))
            if target in valid_ids and target not in seen:
                rewritten.append(target)
                seen.add(target)
        folder["surfaceIds"] = rewritten

    meta = payload.setdefault("meta", {})
    meta["normalization"] = {
        "duplicateGroupsApplied": group_index - 1,
        "rule": "same source + repeated/source-generic title, count >= 3",
    }
    return payload


def main() -> None:
    canonical = PAYLOAD_PATHS[0]
    payload = json.loads(canonical.read_text(encoding="utf-8"))
    payload = normalize_payload(payload)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in PAYLOAD_PATHS:
        path.write_text(text, encoding="utf-8")
    print(f"surfaces={len(payload.get('surfaces', []))}")
    print(f"folders={len(payload.get('folders', []))}")
    print(f"duplicate_groups={payload.get('meta', {}).get('normalization', {}).get('duplicateGroupsApplied', 0)}")


if __name__ == "__main__":
    main()
