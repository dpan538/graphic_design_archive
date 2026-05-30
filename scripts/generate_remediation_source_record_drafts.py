from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from validate_manual_source_record import validate


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

VERIFICATIONS = DATA / "remediation_source_verifications.csv"
SOURCE_REGISTRY = DATA / "source_registry.csv"
OUTPUT_DIR = DATA / "remediation_source_records"
INDEX_PATH = DATA / "remediation_source_records_index.csv"

ACCESS_DATE = "2026-05-30"
ENTERED_BY = "Codex"

SOURCE_ALIASES = {
    "Biblioteca Nacional Digital de Chile": "Biblioteca Nacional Digital de Chile",
    "NDL Search": "NDL Search",
    "Seoul Museum of Art": "Seoul Museum of Art",
    "National Library Board Singapore": "National Library Board Singapore",
    "National Institute of Design": "National Institute of Design",
    "ICOD": "ICOD",
    "South African History Archive": "South African History Archive",
}

BLOCKING_ACTIONS = {
    "keep_fallback_until_exact_record",
    "keep_fallback_or_replace_with_proceedings_anchor",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_years(date_text: str) -> tuple[int | None, int | None]:
    years = [int(match) for match in re.findall(r"\b(1[5-9]\d{2}|20\d{2})\b", date_text)]
    if not years:
        return None, None
    return min(years), max(years)


def source_identifier(url: str) -> str:
    parsed = urlparse(url)
    if "w3-article-" in parsed.path:
        return parsed.path.rsplit("w3-article-", 1)[-1].split(".", 1)[0]
    if "BND%3A" in url:
        return url.rsplit("BND%3A", 1)[-1]
    if "R100000002-" in parsed.path:
        return parsed.path.rsplit("R100000002-", 1)[-1]
    if "artSeq=" in parsed.query:
        return parsed.query.rsplit("artSeq=", 1)[-1]
    parts = [part for part in parsed.path.split("/") if part]
    return parts[-1] if parts else parsed.netloc


def rights_for_zone(image_zone: str, rights_summary: str) -> dict[str, object]:
    if image_zone == "IMG04":
        return {
            "rightsState": "metadata_limited",
            "imageUsePolicy": "metadata_only",
            "metadataPolicy": "source metadata may be indexed with citation",
            "thumbnailPolicy": "not applicable",
            "fullImagePolicy": "not applicable",
            "localCopyPermitted": False,
            "rightsBasis": rights_summary,
            "rightsReviewRequired": True,
            "rightsReviewer": "",
            "rightsReviewDate": "",
            "rightsNotes": "IMG04 means no image frame; source media is not captured.",
        }

    return {
        "rightsState": "link_only",
        "imageUsePolicy": "do_not_display",
        "metadataPolicy": "source metadata may be indexed with citation",
        "thumbnailPolicy": "not displayed",
        "fullImagePolicy": "not displayed",
        "localCopyPermitted": False,
        "rightsBasis": rights_summary,
        "rightsReviewRequired": True,
        "rightsReviewer": "",
        "rightsReviewDate": "",
        "rightsNotes": "IMG00 requires an empty image frame with rights/status text and a source link.",
    }


def display_for_zone(image_zone: str, evidence: str) -> dict[str, str]:
    if image_zone == "IMG04":
        return {
            "imagePresenceCode": "IMG04",
            "imagePresenceBasis": evidence,
            "imageFrameBehavior": "no_image_frame",
            "imageSizePolicy": "not_applicable",
            "layoutNote": "Text/source page; no image frame.",
        }

    return {
        "imagePresenceCode": image_zone,
        "imagePresenceBasis": evidence,
        "imageFrameBehavior": "empty_rights_frame",
        "imageSizePolicy": "template_defined",
        "layoutNote": "Image state controls display permission only; size remains template-defined.",
    }


def classification_rows(row: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "classificationType": "remediation_verification",
            "classificationValue": row["remediation_verification_id"],
            "source": "editorial_judgment",
            "confidence": "medium",
            "reviewer": ENTERED_BY,
            "note": row["promotion_action"],
        },
        {
            "classificationType": "first_ingest_scope_cell",
            "classificationValue": row["scope_cell_id"],
            "source": "controlled_vocabulary",
            "confidence": "medium",
            "reviewer": ENTERED_BY,
            "note": "Inherited from fallback remediation verification.",
        },
        {
            "classificationType": "record_family",
            "classificationValue": row["record_family"],
            "source": "controlled_vocabulary",
            "confidence": "medium",
            "reviewer": ENTERED_BY,
            "note": "Derived from remediation verification row.",
        },
        {
            "classificationType": "image_presence_code",
            "classificationValue": row["confirmed_image_zone"],
            "source": "editorial_judgment",
            "confidence": "medium",
            "reviewer": ENTERED_BY,
            "note": row["rights_summary"],
        },
    ]


def build_record(row: dict[str, str], source: dict[str, str]) -> dict[str, object]:
    date_start, date_end = parse_years(row["date_text"])
    title = row["source_title"]
    url = row["verified_url"]
    image_zone = row["confirmed_image_zone"]
    return {
        "recordStatus": "candidate",
        "captureMethod": "manual",
        "enteredBy": ENTERED_BY,
        "enteredDate": ACCESS_DATE,
        "source": {
            "sourceId": source["source_id"],
            "sourceName": row["source_name"],
            "sourceRecordUrl": url,
            "sourceIdentifier": source_identifier(url),
            "accessDate": ACCESS_DATE,
        },
        "sourceMetadata": {
            "sourceTitle": title,
            "sourceCreator": "",
            "sourceCreatorRole": "",
            "sourceDateText": row["date_text"],
            "sourcePlaceText": "",
            "sourceObjectType": row["record_family"],
            "sourceHoldingInstitution": row["source_name"],
            "sourceCollection": "",
            "sourceDescription": row["evidence_summary"],
            "sourceRightsText": row["rights_summary"],
            "sourceRightsUri": "",
            "sourceCreditLine": row["source_name"],
        },
        "normalizedMetadata": {
            "normalizedTitle": title,
            "normalizedDateStart": date_start,
            "normalizedDateEnd": date_end,
            "normalizedPlace": "",
            "historicalNodeIds": [],
            "movementIds": [],
            "themeTerms": [row["scope_cell_id"], "remediation"],
            "language": "",
        },
        "rights": rights_for_zone(image_zone, row["rights_summary"]),
        "citation": {
            "citationText": f"{row['source_name']}. \"{title}.\" Accessed {ACCESS_DATE}. {url}",
            "citationStyle": "project_draft",
            "citationUrl": url,
            "accessDate": ACCESS_DATE,
        },
        "publicationDisplay": display_for_zone(image_zone, row["evidence_summary"]),
        "classifications": classification_rows(row),
        "relations": [],
        "uncertaintyNotes": [
            {
                "field": "source",
                "issue": "remediation_candidate",
                "displayNote": "This candidate was created from a remediation verification pass and still requires source-field capture.",
                "internalNote": row["remaining_blocker"],
            },
            {
                "field": "promotion",
                "issue": "not_original_target_when_contextual",
                "displayNote": "Some remediation records are contextual replacements rather than exact replacements for the original target.",
                "internalNote": row["promotion_action"],
            },
        ],
    }


def main() -> None:
    sources_by_name = {row["name"]: row for row in read_csv(SOURCE_REGISTRY)}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict[str, str]] = []

    for row in read_csv(VERIFICATIONS):
        if row["promotion_action"] in BLOCKING_ACTIONS:
            continue
        source_name = SOURCE_ALIASES.get(row["source_name"], row["source_name"])
        if source_name not in sources_by_name:
            raise SystemExit(f"missing source registry entry for {row['source_name']}")
        record = build_record(row, sources_by_name[source_name])
        errors = validate(record)
        output_path = OUTPUT_DIR / f"{row['remediation_verification_id']}_source_record.json"
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index_rows.append(
            {
                "remediation_verification_id": row["remediation_verification_id"],
                "source_record_draft_path": str(output_path.relative_to(ROOT)),
                "source_id": record["source"]["sourceId"],  # type: ignore[index]
                "source_name": row["source_name"],
                "verified_url": row["verified_url"],
                "image_presence_code": row["confirmed_image_zone"],
                "promotion_action": row["promotion_action"],
                "validation_status": "valid" if not errors else "invalid",
                "validation_errors": "; ".join(errors),
            }
        )

    with INDEX_PATH.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "remediation_verification_id",
            "source_record_draft_path",
            "source_id",
            "source_name",
            "verified_url",
            "image_presence_code",
            "promotion_action",
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
            print(f"{row['remediation_verification_id']}: {row['validation_errors']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
