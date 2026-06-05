#!/usr/bin/env python3
"""Rights-first IMG00-IMG04 decision helper.

This module is intentionally conservative. It decides public image state from
structured rights evidence before any crawler stores image pixels. Discovery
signals such as visual logo detection, LLM terms-of-service summaries, pHash
matches, or Wayback/IPFS traces may create review notes, but they must not
upgrade a record to IMG03 by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class IMG(str, Enum):
    IMG00 = "IMG00"  # visual object exists, display is withheld
    IMG01 = "IMG01"  # controlled thumbnail only
    IMG02 = "IMG02"  # source-hosted viewer / IIIF / embed only
    IMG03 = "IMG03"  # explicit open/reusable image evidence
    IMG04 = "IMG04"  # text/authority/appendix page; no image frame


DisplayMode = Literal[
    "empty_rights_frame",
    "thumbnail_frame",
    "source_viewer_frame",
    "open_image_frame",
    "no_image_frame",
]

EvidenceLevel = Literal[
    "item_explicit",
    "source_policy",
    "source_viewer",
    "discovery_signal",
    "none",
]


OPEN_LICENSE_URIS = {
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "http://creativecommons.org/publicdomain/zero/1.0/",
    "https://creativecommons.org/publicdomain/mark/1.0/",
    "http://creativecommons.org/publicdomain/mark/1.0/",
    "https://creativecommons.org/licenses/by/4.0/",
    "http://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by-sa/4.0/",
    "http://creativecommons.org/licenses/by-sa/4.0/",
    "http://rightsstatements.org/vocab/NoC-OKLR/1.0/",
    "https://rightsstatements.org/vocab/NoC-OKLR/1.0/",
}

RESTRICTIVE_RIGHTS_URIS = {
    "http://rightsstatements.org/vocab/InC/1.0/",
    "https://rightsstatements.org/vocab/InC/1.0/",
    "http://rightsstatements.org/vocab/InC-EDU/1.0/",
    "https://rightsstatements.org/vocab/InC-EDU/1.0/",
    "http://rightsstatements.org/vocab/InC-RUU/1.0/",
    "https://rightsstatements.org/vocab/InC-RUU/1.0/",
    "http://rightsstatements.org/vocab/CNE/1.0/",
    "https://rightsstatements.org/vocab/CNE/1.0/",
}

OPEN_TEXT_MARKERS = (
    "cc0",
    "creative commons zero",
    "public domain mark",
    "public domain",
    "no known copyright",
    "out of copyright",
    "open access image",
    "rights (production): pdm",
)

RESTRICTIVE_TEXT_MARKERS = (
    "all rights reserved",
    "copyright",
    "permission required",
    "in copyright",
    "may not be reproduced",
)


@dataclass
class RightsEvidence:
    source_name: str = ""
    source_url: str = ""
    license_uri: str = ""
    rights_uri: str = ""
    rights_text: str = ""
    credit_line: str = ""
    source_terms_allow_thumbnail: bool = False
    source_terms_reviewed: bool = False
    source_policy_id: str = ""
    source_terms_allow_local_copy: bool = False
    has_iiif_manifest: bool = False
    has_source_viewer: bool = False
    has_image_candidate: bool = False
    is_textual_surface: bool = False
    parser_status: str = "ok"
    definite_restrictive_notice: bool = False
    discovery_signals: list[str] = field(default_factory=list)


@dataclass
class ImageDecision:
    img: IMG
    display_mode: DisplayMode
    local_copy_permitted: bool
    rights_review_required: bool
    evidence_level: EvidenceLevel
    reason: str
    warnings: list[str] = field(default_factory=list)

    def capture_fields(self) -> dict[str, str]:
        """Return fields compatible with existing capture CSV rows."""
        return {
            "image_presence_code": self.img.value,
            "image_frame_behavior": self.display_mode,
            "local_copy_permitted": "true" if self.local_copy_permitted else "false",
            "rights_review_required": "true" if self.rights_review_required else "false",
            "image_state_confidence": (
                "high" if self.evidence_level == "item_explicit" else "medium"
            ),
            "image_state_review_note": self.reason,
            "rights_basis": self.reason,
            "image_state_evaluation": f"{self.img.value}: {self.reason}",
        }


def _norm(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _has_open_text(evidence: RightsEvidence) -> bool:
    text = _norm(" ".join([evidence.rights_text, evidence.credit_line]))
    return any(marker in text for marker in OPEN_TEXT_MARKERS)


def _has_restrictive_text(evidence: RightsEvidence) -> bool:
    text = _norm(" ".join([evidence.rights_text, evidence.credit_line]))
    return any(marker in text for marker in RESTRICTIVE_TEXT_MARKERS)


def decide_image_state(evidence: RightsEvidence) -> ImageDecision:
    """Decide IMG state before any crawler writes image bytes to disk."""

    warnings: list[str] = []
    if evidence.discovery_signals:
        warnings.append(
            "Discovery-only rights signals recorded; they cannot upgrade image state."
        )

    if evidence.is_textual_surface:
        return ImageDecision(
            img=IMG.IMG04,
            display_mode="no_image_frame",
            local_copy_permitted=False,
            rights_review_required=False,
            evidence_level="item_explicit",
            reason="Text, authority, bibliography, appendix, or context-led surface; no image frame is expected.",
            warnings=warnings,
        )

    if evidence.license_uri in OPEN_LICENSE_URIS:
        return ImageDecision(
            img=IMG.IMG03,
            display_mode="open_image_frame",
            local_copy_permitted=True,
            rights_review_required=True,
            evidence_level="item_explicit",
            reason=f"Item-level open license URI: {evidence.license_uri}",
            warnings=warnings,
        )

    if evidence.rights_uri in OPEN_LICENSE_URIS:
        return ImageDecision(
            img=IMG.IMG03,
            display_mode="open_image_frame",
            local_copy_permitted=True,
            rights_review_required=True,
            evidence_level="item_explicit",
            reason=f"Item-level open rights URI: {evidence.rights_uri}",
            warnings=warnings,
        )

    if (
        evidence.definite_restrictive_notice
        or evidence.rights_uri in RESTRICTIVE_RIGHTS_URIS
        or _has_restrictive_text(evidence)
    ):
        return ImageDecision(
            img=IMG.IMG00,
            display_mode="empty_rights_frame",
            local_copy_permitted=False,
            rights_review_required=True,
            evidence_level="item_explicit",
            reason="Rights evidence or a high-confidence restrictive notice requires link-only display.",
            warnings=warnings,
        )

    if _has_open_text(evidence) and not _has_restrictive_text(evidence):
        return ImageDecision(
            img=IMG.IMG03,
            display_mode="open_image_frame",
            local_copy_permitted=True,
            rights_review_required=True,
            evidence_level="item_explicit",
            reason="Item/source text explicitly reports public-domain or open-image status.",
            warnings=warnings,
        )

    if evidence.has_iiif_manifest or evidence.has_source_viewer:
        return ImageDecision(
            img=IMG.IMG02,
            display_mode="source_viewer_frame",
            local_copy_permitted=False,
            rights_review_required=True,
            evidence_level="source_viewer",
            reason="Source-hosted viewer or IIIF manifest exists; image remains at source until open rights are explicit.",
            warnings=warnings,
        )

    if evidence.source_terms_allow_thumbnail and evidence.source_terms_reviewed:
        return ImageDecision(
            img=IMG.IMG01,
            display_mode="thumbnail_frame",
            local_copy_permitted=False,
            rights_review_required=True,
            evidence_level="source_policy",
            reason=(
                "Reviewed source policy permits controlled thumbnail display; "
                "no local full-size copy."
            ),
            warnings=warnings,
        )

    if evidence.source_terms_allow_thumbnail and not evidence.source_terms_reviewed:
        warnings.append(
            "Unreviewed thumbnail permission was ignored; source policy must be in the reviewed registry."
        )

    if evidence.has_image_candidate or evidence.parser_status not in {"ok", "not_expected"}:
        return ImageDecision(
            img=IMG.IMG00,
            display_mode="empty_rights_frame",
            local_copy_permitted=False,
            rights_review_required=True,
            evidence_level="none",
            reason="A visual object or image candidate exists, but no display-safe rights basis has been verified.",
            warnings=warnings,
        )

    return ImageDecision(
        img=IMG.IMG00,
        display_mode="empty_rights_frame",
        local_copy_permitted=False,
        rights_review_required=True,
        evidence_level="none",
        reason="Unknown image status defaults to link-only empty rights frame.",
        warnings=warnings,
    )
