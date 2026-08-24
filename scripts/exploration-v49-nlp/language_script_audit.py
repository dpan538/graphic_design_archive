#!/usr/bin/env python3
"""Unicode-property script census with no language inference from metadata."""

from __future__ import annotations

import json
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


SCRIPT_ORDER = (
    "Latin",
    "Cyrillic",
    "Greek",
    "Han",
    "Hiragana",
    "Katakana",
    "Hangul",
    "Arabic",
    "Hebrew",
    "Devanagari",
    "mixed",
    "other",
    "undetermined",
)


def character_script(character: str) -> str | None:
    codepoint = ord(character)
    name = unicodedata.name(character, "")
    if "LATIN" in name:
        return "Latin"
    if "CYRILLIC" in name:
        return "Cyrillic"
    if "GREEK" in name:
        return "Greek"
    if 0x3040 <= codepoint <= 0x309F:
        return "Hiragana"
    if (
        0x30A0 <= codepoint <= 0x30FF
        or 0x31F0 <= codepoint <= 0x31FF
        or 0xFF65 <= codepoint <= 0xFF9F
    ):
        return "Katakana"
    if (
        0x4E00 <= codepoint <= 0x9FFF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x20000 <= codepoint <= 0x3134F
        or "CJK" in name
        or "IDEOGRAPH" in name
    ):
        return "Han"
    if (
        0xAC00 <= codepoint <= 0xD7AF
        or 0x1100 <= codepoint <= 0x11FF
        or 0x3130 <= codepoint <= 0x318F
    ):
        return "Hangul"
    if (
        0x0600 <= codepoint <= 0x06FF
        or 0x0750 <= codepoint <= 0x077F
        or 0x08A0 <= codepoint <= 0x08FF
        or 0xFB50 <= codepoint <= 0xFDFF
        or 0xFE70 <= codepoint <= 0xFEFF
    ):
        return "Arabic"
    if 0x0590 <= codepoint <= 0x05FF or 0xFB1D <= codepoint <= 0xFB4F:
        return "Hebrew"
    if 0x0900 <= codepoint <= 0x097F:
        return "Devanagari"
    if character.isalpha():
        return "other"
    return None


@dataclass(frozen=True)
class ScriptState:
    primary_state: str
    scripts: tuple[str, ...]
    script_character_counts: tuple[tuple[str, int], ...]
    alphabetic_character_count: int
    codepoint_count: int

    def as_mapping(self) -> dict[str, Any]:
        value = asdict(self)
        value["script_character_counts"] = dict(self.script_character_counts)
        return value


def classify_unicode(text: str) -> ScriptState:
    counts: Counter[str] = Counter()
    for character in text:
        script = character_script(character)
        if script:
            counts[script] += 1
    scripts = tuple(sorted(counts))
    if not scripts:
        primary = "undetermined"
    elif len(scripts) == 1:
        primary = scripts[0]
    else:
        primary = "mixed"
    return ScriptState(
        primary_state=primary,
        scripts=scripts,
        script_character_counts=tuple(sorted(counts.items())),
        alphabetic_character_count=sum(counts.values()),
        codepoint_count=len(text),
    )


def audit_aspect_documents(documents: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    by_aspect: dict[str, Counter[str]] = defaultdict(Counter)
    object_states: dict[str, set[str]] = defaultdict(set)
    document_count = 0
    for document in documents:
        object_id = str(document.get("publicObjectId", ""))
        for aspect_id, aspect in sorted(dict(document.get("aspects", {})).items()):
            text = aspect.get("semanticNormalized")
            state_name = aspect.get("languageScriptState")
            if isinstance(text, str):
                actual = classify_unicode(text).primary_state
                if state_name is not None and state_name != actual:
                    raise ValueError("document script state differs from deterministic census")
                state_name = actual
            if not isinstance(state_name, str) or state_name not in SCRIPT_ORDER:
                raise ValueError("aspect document has an invalid script state")
            by_aspect[aspect_id][state_name] += 1
            object_states[object_id].add(state_name)
        document_count += 1
    return {
        "documentCount": document_count,
        "aspectScriptCounts": {
            aspect: {state: counts[state] for state in SCRIPT_ORDER if counts[state]}
            for aspect, counts in sorted(by_aspect.items())
        },
        "mixedAspectStateObjectCount": sum(1 for states in object_states.values() if len(states) > 1),
        "languageIdModel": "NOT_SELECTED",
        "languageIdModelCommitted": False,
    }


def self_test() -> dict[str, Any]:
    cases = {
        "Latin": "Design",
        "Cyrillic": "\u0414\u0438\u0437\u0430\u0439\u043d",
        "Greek": "\u03a3\u03c7\u03ad\u03b4\u03b9\u03bf",
        "Han": "\u8a2d\u8a08",
        "Hiragana": "\u3067\u3056\u3044\u3093",
        "Katakana": "\u30c7\u30b6\u30a4\u30f3",
        "Hangul": "\ub514\uc790\uc778",
        "Arabic": "\u062a\u0635\u0645\u064a\u0645",
        "Hebrew": "\u05e2\u05d9\u05e6\u05d5\u05d1",
        "Devanagari": "\u0921\u093f\u091c\u093c\u093e\u0907\u0928",
        "mixed": "Design \u8a2d\u8a08",
        "undetermined": "1945 -- 1950",
    }
    actual = {key: classify_unicode(value).primary_state for key, value in cases.items()}
    if actual != {key: key for key in cases}:
        raise AssertionError(f"script classifier self-test failed: {actual}")
    return {"status": "PASS", "scriptClassCount": len(SCRIPT_ORDER), "cases": actual}


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
