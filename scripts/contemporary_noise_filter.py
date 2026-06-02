#!/usr/bin/env python3
"""Shared contemporary-capture noise filter.

The filter is intentionally conservative. It does not decide scholarly value;
it separates candidate graphic-design archive records from event listings,
commerce pages, job posts, social reposts, and other pages that should remain
discovery leads rather than public archive surfaces.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Mapping


STRONG_GRAPHIC_TERMS = {
    "poster",
    "posters",
    "affiche",
    "placard",
    "flyer",
    "flier",
    "zine",
    "pamphlet",
    "broadsheet",
    "broadside",
    "leaflet",
    "booklet",
    "magazine",
    "periodical",
    "newspaper",
    "cover",
    "advertisement",
    "advertising",
    "typography",
    "typeface",
    "font",
    "specimen",
    "logo",
    "logotype",
    "identity",
    "branding",
    "signage",
    "wayfinding",
    "infographic",
    "diagram",
    "layout",
    "graphic design",
    "communication design",
    "visual communication",
    "print design",
    "web design",
    "interface design",
    "ui",
    "icon",
    "screenshot",
    "manual",
    "style guide",
}

PUBLIC_CONTEXT_TERMS = {
    "campaign",
    "activist",
    "protest",
    "solidarity",
    "public health",
    "election",
    "political",
    "trade union",
    "liberation",
    "anti-apartheid",
    "aids",
    "act up",
    "environment",
    "climate",
    "nuclear",
    "festival",
    "exhibition",
    "music",
    "punk",
    "club",
    "community",
    "indigenous",
    "feminist",
    "queer",
    "palestine",
    "palestinian",
}

ARCHIVE_CONTEXT_TERMS = {
    "archive",
    "archives",
    "collection",
    "collections",
    "record",
    "object",
    "item",
    "metadata",
    "catalogue",
    "catalog",
    "repository",
    "digital library",
    "library",
    "museum",
    "special collections",
    "finding aid",
    "iiif",
    "omeka",
    "contentdm",
    "dspace",
}

NEGATIVE_PAGE_TERMS = {
    "job",
    "jobs",
    "career",
    "careers",
    "internship",
    "vacancy",
    "hiring",
    "apply now",
    "ticket",
    "tickets",
    "registration",
    "register now",
    "rsvp",
    "eventbrite",
    "call for entries",
    "submission guidelines",
    "submit your work",
    "award entry",
    "shop",
    "cart",
    "checkout",
    "buy now",
    "membership",
    "donate",
    "newsletter",
    "subscribe",
    "privacy policy",
    "cookie policy",
    "terms of use",
    "terms and conditions",
    "press release",
    "press kit",
    "sponsor",
    "sponsorship",
    "rfp",
    "tender",
}

DISCOVERY_ONLY_DOMAINS = {
    "pinterest.com",
    "www.pinterest.com",
    "instagram.com",
    "www.instagram.com",
    "tumblr.com",
    "www.tumblr.com",
    "are.na",
    "www.are.na",
    "behance.net",
    "www.behance.net",
    "dribbble.com",
    "www.dribbble.com",
    "designspiration.com",
    "www.designspiration.com",
}

SOURCE_FAMILY_HINTS = {
    "wordpress": ("wp-json", "wp-content"),
    "omeka": ("omeka", "/api/items", "/items/show/"),
    "contentdm": ("digital/api", "contentdm", "/digital/"),
    "dspace": ("dspace", "/handle/", "oai/request"),
    "iiif": ("iiif", "manifest"),
    "institutional_api": ("api", "collection", "object", "catalogue", "catalog"),
}


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def count_terms(text: str, terms: set[str]) -> tuple[int, list[str]]:
    hits: list[str] = []
    padded = f" {text} "
    for term in sorted(terms):
        term_l = term.lower()
        if " " in term_l:
            if term_l in text:
                hits.append(term)
        elif re.search(rf"(?<![a-z0-9]){re.escape(term_l)}(?![a-z0-9])", padded):
            hits.append(term)
    return len(hits), hits


def domain_for(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def source_family_for(row: Mapping[str, str]) -> str:
    blob = normalize_text(
        " ".join(
            [
                row.get("source_name", ""),
                row.get("source_api_url", ""),
                row.get("source_record_url", ""),
                row.get("raw_capture_path", ""),
            ]
        )
    )
    for family, hints in SOURCE_FAMILY_HINTS.items():
        if any(hint in blob for hint in hints):
            return family
    return "other"


@dataclass(frozen=True)
class NoiseDecision:
    decision: str
    score: int
    design_score: int
    provenance_score: int
    risk_score: int
    source_family: str
    positive_signals: str
    negative_signals: str
    reason: str


def safe_text(value: object) -> str:
    return "" if value is None else str(value)


def evaluate_record(row: Mapping[str, str]) -> NoiseDecision:
    title = safe_text(row.get("source_title", ""))
    source = safe_text(row.get("source_name", ""))
    url = safe_text(row.get("source_record_url", "")) or safe_text(row.get("source_api_url", ""))
    text = normalize_text(
        " ".join(
            [
                title,
                safe_text(row.get("source_creator", "")),
                safe_text(row.get("source_object_type", "")),
                safe_text(row.get("source_medium", "")),
                safe_text(row.get("source_collection", "")),
                safe_text(row.get("source_description", "")),
                safe_text(row.get("source_notes", "")),
                safe_text(row.get("source_subjects", "")),
                safe_text(row.get("direction_name", "")),
                source,
                url,
            ]
        )
    )
    domain = domain_for(url)
    source_family = source_family_for(row)

    strong_n, strong_hits = count_terms(text, STRONG_GRAPHIC_TERMS)
    context_n, context_hits = count_terms(text, PUBLIC_CONTEXT_TERMS)
    archive_n, archive_hits = count_terms(text, ARCHIVE_CONTEXT_TERMS)
    negative_n, negative_hits = count_terms(text, NEGATIVE_PAGE_TERMS)

    design_score = min(9, strong_n * 3 + min(context_n, 4))
    provenance_score = min(6, archive_n + (2 if row.get("source_identifier") else 0) + (1 if url else 0))
    risk_score = min(8, negative_n * 2)

    if domain in DISCOVERY_ONLY_DOMAINS:
        decision = "discovery_only"
        reason = "social/repost platform should not be a standalone evidence source"
    elif negative_n >= 2 and strong_n == 0:
        decision = "exclude_noise"
        reason = "page looks like service, event, commerce, jobs, policy, or administrative noise"
    elif strong_n == 0 and context_n <= 1 and archive_n <= 1:
        decision = "review_lead"
        reason = "not enough graphic-design or archive-specific evidence in metadata"
    elif strong_n >= 1 and provenance_score >= 4 and design_score + provenance_score - risk_score >= 8:
        decision = "include_candidate"
        reason = "has graphic-design object language and sufficient source/provenance signal"
    elif strong_n >= 1 and provenance_score >= 2:
        decision = "downgrade_candidate"
        reason = "usable as subsheet/card/text candidate, but not strong enough for main sheet without grouping or enrichment"
    else:
        decision = "review_lead"
        reason = "partial signal; keep as capture lead until corroborated"

    return NoiseDecision(
        decision=decision,
        score=design_score + provenance_score - risk_score,
        design_score=design_score,
        provenance_score=provenance_score,
        risk_score=risk_score,
        source_family=source_family,
        positive_signals="; ".join((strong_hits + context_hits + archive_hits)[:16]),
        negative_signals="; ".join(negative_hits[:12]),
        reason=reason,
    )
