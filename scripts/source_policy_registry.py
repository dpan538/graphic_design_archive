#!/usr/bin/env python3
"""Reviewed source-policy lookup for rights-first crawlers.

This is deliberately stricter than a normal domain allowlist. A crawler may use
this helper to ask whether a source has a reviewed policy for controlled
thumbnail display or source-hosted viewer display, but the helper never grants
local reuse. Item-level open evidence is still required for IMG03.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY = ROOT / "data" / "source_registry.csv"

YES_VALUES = {"yes", "true", "1"}
NO_VALUES = {"no", "false", "0"}
REVIEW_VALUES = {"reviewed", "policy_reviewed", "manual_policy_reviewed"}


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    name: str
    url: str
    domain: str
    thumbnail_allowed: str
    preview_allowed: str
    default_image_zone: str
    iiif_capable: str
    record_level_rights_required: str
    protocol_sensitive: str
    automation_status: str
    rights_basis: str

    @property
    def reviewed_for_automatic_thumbnail(self) -> bool:
        """Only an explicit reviewed policy can open IMG01.

        `manual_review` in the registry means "needs review", not "approved".
        We therefore require an explicit reviewed status plus a clear yes value,
        and we reject source-level thumbnail use when item-level rights are
        still required.
        """

        return (
            norm(self.automation_status) in REVIEW_VALUES
            and norm(self.thumbnail_allowed) in YES_VALUES
            and norm(self.record_level_rights_required) in NO_VALUES
            and norm(self.protocol_sensitive) not in YES_VALUES
        )

    @property
    def source_viewer_candidate(self) -> bool:
        """A reviewed source-hosted viewer route can support IMG02.

        This is not a reuse permission. It only records that the source may be
        linked or embedded according to the source registry.
        """

        return (
            norm(self.preview_allowed) in YES_VALUES
            or norm(self.iiif_capable) in YES_VALUES
            or norm(self.default_image_zone) == "img02"
        )


def norm(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def host_for(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def host_matches(candidate: str, registered: str) -> bool:
    if not candidate or not registered:
        return False
    candidate = candidate[4:] if candidate.startswith("www.") else candidate
    registered = registered[4:] if registered.startswith("www.") else registered
    return candidate == registered or candidate.endswith("." + registered)


def load_source_policies(path: Path = SOURCE_REGISTRY) -> list[SourcePolicy]:
    policies: list[SourcePolicy] = []
    if not path.exists():
        return policies
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            url = row.get("url", "")
            policies.append(
                SourcePolicy(
                    source_id=row.get("source_id", ""),
                    name=row.get("name", ""),
                    url=url,
                    domain=host_for(url),
                    thumbnail_allowed=row.get("thumbnail_allowed", ""),
                    preview_allowed=row.get("preview_allowed", ""),
                    default_image_zone=row.get("default_image_zone", ""),
                    iiif_capable=row.get("iiif_capable", ""),
                    record_level_rights_required=row.get("record_level_rights_required", ""),
                    protocol_sensitive=row.get("protocol_sensitive", ""),
                    automation_status=row.get("automation_status", ""),
                    rights_basis=row.get("rights_basis", ""),
                )
            )
    return policies


def policy_for_url(source_url: str, source_id: str = "") -> SourcePolicy | None:
    host = host_for(source_url)
    for policy in load_source_policies():
        if source_id and policy.source_id == source_id:
            return policy
        if host_matches(host, policy.domain):
            return policy
    return None


def thumbnail_policy_evidence(source_url: str, source_id: str = "") -> dict[str, str | bool]:
    """Return reviewed IMG01 evidence for the rights decision engine."""

    policy = policy_for_url(source_url, source_id)
    if not policy:
        return {
            "source_terms_allow_thumbnail": False,
            "source_terms_reviewed": False,
            "source_policy_id": "",
            "review_note": "No matching source policy registry entry.",
        }
    allowed = policy.reviewed_for_automatic_thumbnail
    return {
        "source_terms_allow_thumbnail": allowed,
        "source_terms_reviewed": allowed,
        "source_policy_id": policy.source_id,
        "review_note": (
            "Reviewed source policy permits controlled thumbnail display."
            if allowed
            else "Source policy is not reviewed for automatic thumbnail display."
        ),
    }


def main() -> int:
    policies = load_source_policies()
    reviewed_thumb = [p for p in policies if p.reviewed_for_automatic_thumbnail]
    viewer = [p for p in policies if p.source_viewer_candidate]
    print(f"sources={len(policies)}")
    print(f"reviewed_thumbnail_sources={len(reviewed_thumb)}")
    print(f"source_viewer_candidates={len(viewer)}")
    if reviewed_thumb:
        print("reviewed thumbnail policy ids:")
        for policy in reviewed_thumb:
            print(f"- {policy.source_id} {policy.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
