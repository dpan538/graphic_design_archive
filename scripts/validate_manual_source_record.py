from __future__ import annotations

import json
import re
import sys
from pathlib import Path


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://")

RIGHTS_STATES = {
    "metadata_open",
    "metadata_limited",
    "image_open",
    "image_embed_only",
    "thumbnail_only",
    "link_only",
    "unknown",
    "do_not_ingest",
}

IMAGE_POLICIES = {
    "metadata_only",
    "link_only",
    "thumbnail_only",
    "source_viewer_only",
    "iiif_embed_only",
    "full_image_allowed",
    "do_not_display",
}

CLASSIFICATION_SOURCES = {
    "source_metadata",
    "controlled_vocabulary",
    "editorial_judgment",
}

CONFIDENCE = {"high", "medium", "low", "unknown"}
IMAGE_PRESENCE_CODES = {"IMG00", "IMG01", "IMG02", "IMG03", "IMG04"}
IMAGE_FRAME_BEHAVIORS = {
    "empty_rights_frame",
    "thumbnail_frame",
    "source_viewer_frame",
    "open_image_frame",
    "no_image_frame",
}
IMAGE_SIZE_POLICIES = {"template_defined", "not_applicable"}


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def get(data: dict, path: str):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate(data: dict) -> list[str]:
    errors: list[str] = []

    for path in [
        "recordStatus",
        "captureMethod",
        "source.sourceId",
        "source.sourceName",
        "source.sourceRecordUrl",
        "source.accessDate",
        "sourceMetadata.sourceTitle",
        "rights.rightsState",
        "rights.imageUsePolicy",
        "rights.localCopyPermitted",
        "rights.rightsBasis",
        "citation.citationText",
        "citation.citationUrl",
        "citation.accessDate",
        "classifications",
    ]:
        require(get(data, path) not in (None, ""), errors, f"missing required field: {path}")

    require(get(data, "captureMethod") == "manual", errors, "captureMethod must be manual")
    require(str(get(data, "source.sourceId") or "").startswith("SRC"), errors, "source.sourceId must start with SRC")
    require(bool(URL_RE.match(str(get(data, "source.sourceRecordUrl") or ""))), errors, "source.sourceRecordUrl must be http(s)")
    require(bool(DATE_RE.match(str(get(data, "source.accessDate") or ""))), errors, "source.accessDate must be YYYY-MM-DD")
    require(bool(URL_RE.match(str(get(data, "citation.citationUrl") or ""))), errors, "citation.citationUrl must be http(s)")
    require(bool(DATE_RE.match(str(get(data, "citation.accessDate") or ""))), errors, "citation.accessDate must be YYYY-MM-DD")
    require(get(data, "rights.rightsState") in RIGHTS_STATES, errors, "rights.rightsState is invalid")
    require(get(data, "rights.imageUsePolicy") in IMAGE_POLICIES, errors, "rights.imageUsePolicy is invalid")
    require(isinstance(get(data, "rights.localCopyPermitted"), bool), errors, "rights.localCopyPermitted must be boolean")

    publication_display = get(data, "publicationDisplay")
    if publication_display is not None:
        require(isinstance(publication_display, dict), errors, "publicationDisplay must be an object")
        require(
            get(data, "publicationDisplay.imagePresenceCode") in IMAGE_PRESENCE_CODES,
            errors,
            "publicationDisplay.imagePresenceCode is invalid",
        )
        require(
            get(data, "publicationDisplay.imagePresenceBasis") not in (None, ""),
            errors,
            "publicationDisplay.imagePresenceBasis is required",
        )
        behavior = get(data, "publicationDisplay.imageFrameBehavior")
        if behavior is not None:
            require(behavior in IMAGE_FRAME_BEHAVIORS, errors, "publicationDisplay.imageFrameBehavior is invalid")
        size_policy = get(data, "publicationDisplay.imageSizePolicy")
        if size_policy is not None:
            require(size_policy in IMAGE_SIZE_POLICIES, errors, "publicationDisplay.imageSizePolicy is invalid")

    classifications = get(data, "classifications")
    require(isinstance(classifications, list) and len(classifications) > 0, errors, "classifications must be a non-empty array")
    if isinstance(classifications, list):
        for idx, item in enumerate(classifications):
            require(isinstance(item, dict), errors, f"classifications[{idx}] must be an object")
            if not isinstance(item, dict):
                continue
            for key in ["classificationType", "classificationValue", "source", "confidence"]:
                require(item.get(key) not in (None, ""), errors, f"classifications[{idx}].{key} is required")
            require(item.get("source") in CLASSIFICATION_SOURCES, errors, f"classifications[{idx}].source is invalid")
            require(item.get("confidence") in CONFIDENCE, errors, f"classifications[{idx}].confidence is invalid")

    if get(data, "rights.imageUsePolicy") == "full_image_allowed":
        require(
            get(data, "rights.rightsState") == "image_open",
            errors,
            "full_image_allowed requires rights.rightsState = image_open",
        )

    if get(data, "rights.localCopyPermitted") is True:
        require(
            get(data, "rights.rightsState") == "image_open",
            errors,
            "localCopyPermitted true requires rights.rightsState = image_open",
        )

    image_presence = get(data, "publicationDisplay.imagePresenceCode")
    if image_presence == "IMG04":
        require(
            get(data, "rights.imageUsePolicy") in {"metadata_only", "link_only"},
            errors,
            "IMG04 requires a text/metadata imageUsePolicy",
        )
        require(
            get(data, "publicationDisplay.imageFrameBehavior") == "no_image_frame",
            errors,
            "IMG04 requires imageFrameBehavior = no_image_frame",
        )
    elif image_presence == "IMG00":
        require(
            get(data, "rights.imageUsePolicy") in {"do_not_display", "link_only"},
            errors,
            "IMG00 requires do_not_display or link_only imageUsePolicy",
        )
        require(
            get(data, "publicationDisplay.imageFrameBehavior") == "empty_rights_frame",
            errors,
            "IMG00 requires imageFrameBehavior = empty_rights_frame",
        )
    elif image_presence == "IMG02":
        require(
            get(data, "rights.imageUsePolicy") in {"source_viewer_only", "iiif_embed_only"},
            errors,
            "IMG02 requires source_viewer_only or iiif_embed_only imageUsePolicy",
        )
        require(
            get(data, "publicationDisplay.imageFrameBehavior") == "source_viewer_frame",
            errors,
            "IMG02 requires imageFrameBehavior = source_viewer_frame",
        )

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_manual_source_record.py path/to/record.json [...]")
        raise SystemExit(2)

    failed = False
    for raw_path in sys.argv[1:]:
        path = Path(raw_path)
        paths = sorted(path.glob("*.json")) if path.is_dir() else [path]
        for json_path in paths:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            errors = validate(data)

            if errors:
                print(f"{json_path}: invalid")
                for error in errors:
                    print(f"  - {error}")
                failed = True
            else:
                print(f"{json_path}: valid")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
