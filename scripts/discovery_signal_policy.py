#!/usr/bin/env python3
"""Non-upgrading discovery-signal contract for crawler helpers.

Visual classifiers, OCR, LLM Terms-of-Use summaries, Wayback/IPFS traces, and
pHash/CLIP similarity can help a crawler find leads or queue review. They must
not upgrade an item to IMG01 or IMG03.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal


SignalKind = Literal[
    "visual_cc_hint",
    "visual_watermark_hint",
    "definite_restrictive_notice",
    "tos_thumbnail_hint",
    "archive_license_hint",
    "similar_open_candidate",
    "jsonld_image_hint",
    "opengraph_image_hint",
]

SignalAction = Literal["downgrade_to_img00", "manual_review", "source_discovery"]


DOWNGRADE_SIGNALS = {"definite_restrictive_notice"}
REVIEW_SIGNALS = {
    "visual_cc_hint",
    "visual_watermark_hint",
    "tos_thumbnail_hint",
    "archive_license_hint",
    "jsonld_image_hint",
    "opengraph_image_hint",
}
DISCOVERY_SIGNALS = {"similar_open_candidate"}


@dataclass(frozen=True)
class DiscoverySignal:
    kind: SignalKind
    confidence: float
    note: str
    source_url: str = ""
    evidence_url: str = ""

    def action(self) -> SignalAction:
        if self.kind in DOWNGRADE_SIGNALS and self.confidence >= 0.99:
            return "downgrade_to_img00"
        if self.kind in DISCOVERY_SIGNALS:
            return "source_discovery"
        return "manual_review"

    def can_upgrade_image_state(self) -> bool:
        return False

    def to_payload(self) -> dict[str, str | float | bool]:
        payload = asdict(self)
        payload["action"] = self.action()
        payload["can_upgrade_image_state"] = False
        return payload


def normalize_signal(kind: str, confidence: float, note: str, **kwargs: str) -> DiscoverySignal:
    allowed = set(DOWNGRADE_SIGNALS) | set(REVIEW_SIGNALS) | set(DISCOVERY_SIGNALS)
    if kind not in allowed:
        raise ValueError(f"Unsupported discovery signal kind: {kind}")
    bounded_confidence = max(0.0, min(1.0, confidence))
    return DiscoverySignal(
        kind=kind,  # type: ignore[arg-type]
        confidence=bounded_confidence,
        note=note,
        source_url=kwargs.get("source_url", ""),
        evidence_url=kwargs.get("evidence_url", ""),
    )


def summarize_signals(signals: list[DiscoverySignal]) -> dict[str, object]:
    return {
        "count": len(signals),
        "downgrade_to_img00": [
            signal.to_payload() for signal in signals if signal.action() == "downgrade_to_img00"
        ],
        "manual_review": [
            signal.to_payload() for signal in signals if signal.action() == "manual_review"
        ],
        "source_discovery": [
            signal.to_payload() for signal in signals if signal.action() == "source_discovery"
        ],
        "can_upgrade_image_state": False,
    }


if __name__ == "__main__":
    demo = [
        normalize_signal("visual_cc_hint", 0.84, "CC-like mark detected; verify source license."),
        normalize_signal(
            "definite_restrictive_notice",
            0.995,
            "OCR found a high-confidence all-rights-reserved notice.",
        ),
    ]
    print(summarize_signals(demo))
