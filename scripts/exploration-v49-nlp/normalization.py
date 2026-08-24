#!/usr/bin/env python3
"""Deterministic, non-generative text views for TRACE NLP research."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from typing import Any

from common import NORMALIZATION_VERSION, URL_PATTERN, sha256_text


MARKUP_PATTERN = re.compile(r"<[A-Za-z!/][^>]*>")
ENTITY_PATTERN = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]+|#\d+|#x[0-9A-Fa-f]+);")
WHITESPACE_PATTERN = re.compile(r"\s+", re.UNICODE)


class NormalizationError(ValueError):
    """Raised when a text value cannot safely enter an NLP view."""


class DisallowedControlError(NormalizationError):
    """Raised for C0/C1 controls outside tab/newline/carriage return."""


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif tag.casefold() in {"br", "p", "div", "li", "tr", "td", "th"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
        elif tag.casefold() in {"p", "div", "li", "tr", "td", "th"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)

    def visible_text(self) -> str:
        return "".join(self.parts)


@dataclass(frozen=True)
class NormalizationResult:
    normalization_version: str
    display_original: str
    original_text_hash: str
    semantic_normalized: str
    semantic_normalized_hash: str
    lexical_casefolded: str
    lexical_casefolded_hash: str
    lexical_compatibility_fallback: str
    lexical_compatibility_fallback_hash: str
    markup_removed: bool
    html_entity_decoded: bool
    url_removed_count: int
    nonbreaking_space_replaced: bool
    repeated_whitespace_collapsed: bool
    compatibility_changed: bool

    def as_mapping(self, *, include_text: bool = True) -> dict[str, Any]:
        value = asdict(self)
        if not include_text:
            for key in (
                "display_original",
                "semantic_normalized",
                "lexical_casefolded",
                "lexical_compatibility_fallback",
            ):
                value.pop(key, None)
        return value


def disallowed_controls(text: str) -> tuple[str, ...]:
    values = {
        f"U+{ord(character):04X}"
        for character in text
        if unicodedata.category(character) == "Cc" and character not in "\t\n\r"
    }
    return tuple(sorted(values))


def _parse_markup(text: str) -> str:
    parser = _VisibleTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # HTMLParser errors are rare; fail closed if one occurs.
        raise NormalizationError("markup parser rejected the text value") from exc
    return parser.visible_text()


def _diacritic_folded_compatibility(text: str) -> str:
    compatibility = unicodedata.normalize("NFKC", text).casefold()
    decomposed = unicodedata.normalize("NFD", compatibility)
    without_marks = "".join(
        character for character in decomposed if not unicodedata.category(character).startswith("M")
    )
    return unicodedata.normalize("NFC", without_marks)


def normalize_text(
    text: str,
    *,
    remove_urls: bool = True,
    reject_controls: bool = True,
) -> NormalizationResult:
    if not isinstance(text, str):
        raise NormalizationError("NLP text must be a string")
    original = text
    controls = disallowed_controls(original)
    if controls and reject_controls:
        raise DisallowedControlError(f"disallowed controls present: {','.join(controls)}")

    line_normalized = original.replace("\r\n", "\n").replace("\r", "\n")
    nonbreaking = "\u00a0" in line_normalized
    line_normalized = line_normalized.replace("\u00a0", " ")

    entity_present = bool(ENTITY_PATTERN.search(line_normalized))
    decoded = html.unescape(line_normalized)
    decoded_controls = disallowed_controls(decoded)
    if decoded_controls and reject_controls:
        raise DisallowedControlError(
            f"disallowed controls present after HTML decoding: {','.join(decoded_controls)}"
        )
    markup_present = bool(MARKUP_PATTERN.search(decoded))
    visible = _parse_markup(decoded) if markup_present else decoded

    url_count = len(URL_PATTERN.findall(visible)) if remove_urls else 0
    if remove_urls:
        visible = URL_PATTERN.sub(" ", visible)

    before_whitespace = visible
    visible = WHITESPACE_PATTERN.sub(" ", visible).strip()
    repeated = visible != before_whitespace.strip()
    semantic = unicodedata.normalize("NFC", visible)
    if not semantic:
        raise NormalizationError("normalization produced empty model input")
    final_controls = disallowed_controls(semantic)
    if final_controls and reject_controls:
        raise DisallowedControlError(
            f"disallowed controls present after normalization: {','.join(final_controls)}"
        )

    casefolded = semantic.casefold()
    compatibility = _diacritic_folded_compatibility(semantic)
    return NormalizationResult(
        normalization_version=NORMALIZATION_VERSION,
        display_original=original,
        original_text_hash=sha256_text(original),
        semantic_normalized=semantic,
        semantic_normalized_hash=sha256_text(semantic),
        lexical_casefolded=casefolded,
        lexical_casefolded_hash=sha256_text(casefolded),
        lexical_compatibility_fallback=compatibility,
        lexical_compatibility_fallback_hash=sha256_text(compatibility),
        markup_removed=markup_present,
        html_entity_decoded=entity_present,
        url_removed_count=url_count,
        nonbreaking_space_replaced=nonbreaking,
        repeated_whitespace_collapsed=repeated,
        compatibility_changed=compatibility != casefolded,
    )


def semantic_normalize(text: str, *, remove_urls: bool = True) -> str:
    return normalize_text(text, remove_urls=remove_urls).semantic_normalized


def lexical_casefolded(text: str, *, remove_urls: bool = True) -> str:
    return normalize_text(text, remove_urls=remove_urls).lexical_casefolded


def self_test() -> dict[str, Any]:
    first = normalize_text("  Caf\u00e9\u00a0&amp; <b>Design</b>\r\nhttps://example.test/x  ")
    second = normalize_text("  Caf\u00e9\u00a0&amp; <b>Design</b>\r\nhttps://example.test/x  ")
    if first != second:
        raise AssertionError("normalization is not deterministic")
    if first.semantic_normalized != "Caf\u00e9 & Design":
        raise AssertionError("semantic normalization contract changed")
    if unicodedata.normalize("NFC", first.semantic_normalized) != first.semantic_normalized:
        raise AssertionError("semantic normalized view is not NFC")
    if first.lexical_compatibility_fallback != "cafe & design":
        raise AssertionError("compatibility fallback contract changed")
    try:
        normalize_text("unsafe\u0096control")
    except DisallowedControlError:
        pass
    else:
        raise AssertionError("disallowed control was not rejected")
    try:
        normalize_text("entity-encoded control: &#x81;")
    except DisallowedControlError:
        pass
    else:
        raise AssertionError("entity-decoded control was not rejected")
    if normalize_text("co-operate; l'art", remove_urls=False).semantic_normalized != "co-operate; l'art":
        raise AssertionError("primary semantic view removed punctuation")
    return {
        "status": "PASS",
        "normalizationVersion": NORMALIZATION_VERSION,
        "exampleSemanticSha256": first.semantic_normalized_hash,
        "urlRemovedCount": first.url_removed_count,
        "markupRemoved": first.markup_removed,
        "htmlEntityDecoded": first.html_entity_decoded,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
