from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from validate_manual_source_record import validate


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

READY_TARGETS = DATA / "ready_manual_ingest_targets.csv"
ALL_TARGETS = DATA / "first_ingest_record_targets.csv"
VERIFICATIONS = DATA / "first_ingest_target_verifications.csv"
SOURCE_REGISTRY = DATA / "source_registry.csv"
SCOPE_CELLS = DATA / "experimental_ingest_shortlist.csv"
OUTPUT_DIR = DATA / "manual_source_records"
INDEX_PATH = DATA / "manual_source_records_index.csv"

ACCESS_DATE = "2026-05-30"
ENTERED_BY = "Codex"

SOURCE_ALIASES = {
    "Harvard Art Museums": "Harvard Art Museums API",
    "Library of Congress": "Library of Congress loc.gov API",
    "IBM": "IBM History Design Program",
    "MoMA": "MoMA Collection",
    "Internet Archive": "Internet Archive",
    "National Institute of Design": "National Institute of Design",
    "South African History Archive": "South African History Archive",
    "South African History Online": "South African History Online",
    "AIATSIS": "AIATSIS",
    "W3C": "W3C CSS Archive",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def index_by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def normalize_source_name(name: str) -> str:
    return SOURCE_ALIASES.get(name, name)


def source_identifier(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("objectNumber", "id", "subjectid", "subid"):
        if key in query and query[key]:
            return f"{key}:{query[key][0]}"

    parts = [part for part in parsed.path.split("/") if part]
    if parts:
        return parts[-1]
    return parsed.netloc


def parse_years(date_text: str) -> tuple[int | None, int | None]:
    years = [int(match) for match in re.findall(r"\b(1[5-9]\d{2}|20\d{2})\b", date_text)]
    if not years:
        return None, None
    return min(years), max(years)


def split_semicolon(value: str, prefix: str | None = None) -> list[str]:
    items = [item.strip() for item in value.split(";") if item.strip()]
    if prefix:
        return [item for item in items if item.startswith(prefix)]
    return items


def rights_for_image_zone(image_zone: str, rights_risk: str, required_action: str) -> dict[str, object]:
    basis = (
        f"Image presence {image_zone}. {required_action}. "
        "Default policy follows the project rule that image display must be justified by item-level evidence."
    )
    risk = rights_risk.lower()
    review_required = rights_risk in {"High", "Medium"} or image_zone in {"IMG00", "IMG02", "IMG03"}

    if image_zone == "IMG03":
        return {
            "rightsState": "image_open",
            "imageUsePolicy": "full_image_allowed",
            "metadataPolicy": "source metadata may be indexed with citation",
            "thumbnailPolicy": "allowed only with source credit and protocol review where applicable",
            "fullImagePolicy": "allowed only when source record and protocol review confirm reuse",
            "localCopyPermitted": False,
            "rightsBasis": basis,
            "rightsReviewRequired": review_required,
            "rightsReviewer": "",
            "rightsReviewDate": "",
            "rightsNotes": "IMG03 marks open/reusable image evidence, but local copying still remains disabled in draft records.",
        }

    if image_zone == "IMG02":
        return {
            "rightsState": "image_embed_only",
            "imageUsePolicy": "source_viewer_only",
            "metadataPolicy": "source metadata may be indexed with citation",
            "thumbnailPolicy": "not locally copied",
            "fullImagePolicy": "source-hosted viewer only; no local image file",
            "iiifEmbedPolicy": "source viewer or IIIF only if source terms permit",
            "localCopyPermitted": False,
            "rightsBasis": basis,
            "rightsReviewRequired": review_required,
            "rightsReviewer": "",
            "rightsReviewDate": "",
            "rightsNotes": "IMG02 is a source-hosted display state, not permission to copy or enlarge images locally.",
        }

    if image_zone == "IMG04":
        return {
            "rightsState": "metadata_limited" if risk in {"medium", "high"} else "metadata_open",
            "imageUsePolicy": "metadata_only",
            "metadataPolicy": "text/authority/event metadata may be indexed with citation",
            "thumbnailPolicy": "not applicable",
            "fullImagePolicy": "not applicable",
            "localCopyPermitted": False,
            "rightsBasis": basis,
            "rightsReviewRequired": rights_risk in {"High", "Medium"},
            "rightsReviewer": "",
            "rightsReviewDate": "",
            "rightsNotes": "IMG04 means the publication page has no image frame; it is not a copyright clearance tier.",
        }

    if image_zone == "IMG01":
        return {
            "rightsState": "thumbnail_only",
            "imageUsePolicy": "thumbnail_only",
            "metadataPolicy": "source metadata may be indexed with citation",
            "thumbnailPolicy": "thumbnail only when source terms permit",
            "fullImagePolicy": "not permitted",
            "localCopyPermitted": False,
            "rightsBasis": basis,
            "rightsReviewRequired": review_required,
            "rightsReviewer": "",
            "rightsReviewDate": "",
            "rightsNotes": "IMG01 permits only the controlled thumbnail region.",
        }

    return {
        "rightsState": "link_only",
        "imageUsePolicy": "do_not_display",
        "metadataPolicy": "source metadata may be indexed with citation",
        "thumbnailPolicy": "not displayed",
        "fullImagePolicy": "not displayed",
        "localCopyPermitted": False,
        "rightsBasis": basis,
        "rightsReviewRequired": review_required,
        "rightsReviewer": "",
        "rightsReviewDate": "",
        "rightsNotes": "IMG00 requires an empty image frame with rights/status text and a source link.",
    }


def display_for_image_zone(image_zone: str, decision: str, evidence: str) -> dict[str, str]:
    behavior = {
        "IMG00": "empty_rights_frame",
        "IMG01": "thumbnail_frame",
        "IMG02": "source_viewer_frame",
        "IMG03": "open_image_frame",
        "IMG04": "no_image_frame",
    }[image_zone]
    size_policy = "not_applicable" if image_zone == "IMG04" else "template_defined"
    return {
        "imagePresenceCode": image_zone,
        "imagePresenceBasis": f"{decision}: {evidence}",
        "imageFrameBehavior": behavior,
        "imageSizePolicy": size_policy,
        "layoutNote": "Image size is selected by the publication template; IMG code only controls image presence and display permission state.",
    }


def classification_rows(
    target: dict[str, str],
    verification: dict[str, str],
    scope: dict[str, str],
) -> list[dict[str, str]]:
    rows = [
        {
            "classificationType": "first_ingest_scope_cell",
            "classificationValue": target["scope_cell_id"],
            "source": "controlled_vocabulary",
            "confidence": "high",
            "reviewer": ENTERED_BY,
            "note": scope.get("candidate_name", ""),
        },
        {
            "classificationType": "record_family",
            "classificationValue": target["record_family"],
            "source": "controlled_vocabulary",
            "confidence": "medium",
            "reviewer": ENTERED_BY,
            "note": "Inherited from first-ingest target selection.",
        },
        {
            "classificationType": "image_presence_code",
            "classificationValue": verification["confirmed_image_zone"],
            "source": "editorial_judgment",
            "confidence": "medium",
            "reviewer": ENTERED_BY,
            "note": verification["required_action"],
        },
    ]

    for hn_id in split_semicolon(scope.get("hn_ids", ""), "HN"):
        rows.append(
            {
                "classificationType": "historical_node",
                "classificationValue": hn_id,
                "source": "controlled_vocabulary",
                "confidence": "medium",
                "reviewer": ENTERED_BY,
                "note": "Inherited from first-ingest scope cell; requires record-level confirmation.",
            }
        )

    for movement_id in split_semicolon(scope.get("movement_ids", "")):
        rows.append(
            {
                "classificationType": "movement_or_regional_formation",
                "classificationValue": movement_id,
                "source": "controlled_vocabulary",
                "confidence": "medium",
                "reviewer": ENTERED_BY,
                "note": "Inherited from scope cell; may be regional movement rather than canonical MV term.",
            }
        )

    for event_id in split_semicolon(scope.get("event_ids", ""), "REN"):
        rows.append(
            {
                "classificationType": "regional_event_node",
                "classificationValue": event_id,
                "source": "controlled_vocabulary",
                "confidence": "medium",
                "reviewer": ENTERED_BY,
                "note": "Inherited from first-ingest scope cell.",
            }
        )

    return rows


def uncertainty_rows(target: dict[str, str], verification: dict[str, str]) -> list[dict[str, str]]:
    notes = [
        {
            "field": "rights",
            "issue": "manual_review_required",
            "displayNote": "Rights state is a conservative draft and must be verified against the source record before publication.",
            "internalNote": verification["required_action"],
        },
        {
            "field": "classification",
            "issue": "scope_cell_inherited",
            "displayNote": "Historical classifications are inherited from the first-ingest scope cell until source-level metadata is reviewed.",
            "internalNote": target["why_selected"],
        },
    ]
    if verification.get("blocking_reason"):
        notes.append(
            {
                "field": "source",
                "issue": "verification_blocking_reason",
                "displayNote": "This target had a verification note during the first pass.",
                "internalNote": verification["blocking_reason"],
            }
        )
    return notes


def build_record(
    ready: dict[str, str],
    target: dict[str, str],
    verification: dict[str, str],
    source: dict[str, str],
    scope: dict[str, str],
) -> dict[str, object]:
    canonical_url = ready["canonical_url"] or ready["source_url_or_search_path"]
    date_start, date_end = parse_years(target["date_text"])
    image_zone = verification["confirmed_image_zone"]

    record: dict[str, object] = {
        "recordStatus": "candidate",
        "captureMethod": "manual",
        "enteredBy": ENTERED_BY,
        "enteredDate": ACCESS_DATE,
        "source": {
            "sourceId": source["source_id"],
            "sourceName": ready["source_name"],
            "sourceRecordUrl": canonical_url,
            "sourceIdentifier": source_identifier(canonical_url),
            "accessDate": verification.get("verified_at") or ACCESS_DATE,
        },
        "sourceMetadata": {
            "sourceTitle": target["target_label"],
            "sourceCreator": target["creator_or_institution"],
            "sourceCreatorRole": "creator_or_institution_from_target",
            "sourceDateText": target["date_text"],
            "sourcePlaceText": target["region"],
            "sourceObjectType": target["record_family"],
            "sourceHoldingInstitution": ready["source_name"],
            "sourceCollection": "",
            "sourceDescription": target["why_selected"],
            "sourceRightsText": target["required_citation"],
            "sourceRightsUri": "",
            "sourceCreditLine": "",
        },
        "normalizedMetadata": {
            "normalizedTitle": target["target_label"],
            "normalizedDateStart": date_start,
            "normalizedDateEnd": date_end,
            "normalizedPlace": target["region"],
            "historicalNodeIds": split_semicolon(scope.get("hn_ids", ""), "HN"),
            "movementIds": [],
            "themeTerms": split_semicolon(scope.get("query_profile_id", "")),
            "language": "",
        },
        "rights": rights_for_image_zone(image_zone, target["rights_risk"], verification["required_action"]),
        "citation": {
            "citationText": f"{ready['source_name']}. \"{target['target_label']}.\" Accessed {verification.get('verified_at') or ACCESS_DATE}. {canonical_url}",
            "citationStyle": "project_draft",
            "citationUrl": canonical_url,
            "accessDate": verification.get("verified_at") or ACCESS_DATE,
        },
        "publicationDisplay": display_for_image_zone(
            image_zone,
            verification["verification_decision"],
            verification["evidence_summary"],
        ),
        "classifications": classification_rows(target, verification, scope),
        "relations": [],
        "uncertaintyNotes": uncertainty_rows(target, verification),
    }

    if image_zone in {"IMG01", "IMG02", "IMG03"}:
        record["image"] = {
            "sourceImageUrl": canonical_url,
            "imageRightsUri": "",
            "imageRightsLabel": image_zone,
            "creditLine": ready["source_name"],
            "localCopyPermitted": False,
        }

    return record


def main() -> None:
    ready_targets = read_csv(READY_TARGETS)
    targets = index_by(read_csv(ALL_TARGETS), "first_target_id")
    verifications = index_by(read_csv(VERIFICATIONS), "first_target_id")
    scope_cells = index_by(read_csv(SCOPE_CELLS), "scope_cell_id")
    sources_by_name = {row["name"]: row for row in read_csv(SOURCE_REGISTRY)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict[str, str]] = []

    for ready in ready_targets:
        target = targets[ready["first_target_id"]]
        verification = verifications[ready["first_target_id"]]
        source_name = normalize_source_name(ready["source_name"])
        if source_name not in sources_by_name:
            raise SystemExit(f"missing source registry entry for {ready['source_name']} ({source_name})")

        record = build_record(
            ready=ready,
            target=target,
            verification=verification,
            source=sources_by_name[source_name],
            scope=scope_cells[target["scope_cell_id"]],
        )
        errors = validate(record)
        output_path = OUTPUT_DIR / f"{ready['first_target_id']}_manual_source_record.json"
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index_rows.append(
            {
                "first_target_id": ready["first_target_id"],
                "source_record_draft_path": str(output_path.relative_to(ROOT)),
                "source_id": record["source"]["sourceId"],  # type: ignore[index]
                "source_name": ready["source_name"],
                "canonical_url": record["source"]["sourceRecordUrl"],  # type: ignore[index]
                "image_presence_code": record["publicationDisplay"]["imagePresenceCode"],  # type: ignore[index]
                "validation_status": "valid" if not errors else "invalid",
                "validation_errors": "; ".join(errors),
            }
        )

    with INDEX_PATH.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "first_target_id",
            "source_record_draft_path",
            "source_id",
            "source_name",
            "canonical_url",
            "image_presence_code",
            "validation_status",
            "validation_errors",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(index_rows)

    invalid = [row for row in index_rows if row["validation_status"] != "valid"]
    print(f"{OUTPUT_DIR.relative_to(ROOT)}: {len(index_rows)} draft records")
    print(f"{INDEX_PATH.relative_to(ROOT)}: index written")
    if invalid:
        for row in invalid:
            print(f"{row['first_target_id']}: {row['validation_errors']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
