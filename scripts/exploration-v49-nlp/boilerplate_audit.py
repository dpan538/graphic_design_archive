#!/usr/bin/env python3
"""Deterministic source-conditioned boilerplate discovery and masking."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any, Iterable, Mapping, Sequence

from common import BOILERPLATE_REGISTRY_VERSION, SourceValue, URL_PATTERN, sha256_json, sha256_text
from source_inventory import iter_public_sources


TOKEN_PATTERN = re.compile(r"\w+(?:['\u2019-]\w+)*", re.UNICODE)
ALLOWED_DECISIONS = frozenset(
    {"REMOVE_FOR_NLP_INPUT", "MASK_SOURCE_IDENTITY", "KEEP_SEMANTIC", "KEEP_DIAGNOSTIC", "HOLD"}
)


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", " ".join(text.split()))


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in TOKEN_PATTERN.findall(_normalize(text)))


@dataclass(frozen=True)
class BoilerplateRule:
    rule_id: str
    source: str
    field_role: str
    phrase_or_hash: str
    support: int
    denominator: int
    decision: str
    reason: str
    removal_scope: str
    version: str
    rule_type: str
    token_count: int

    def as_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BoilerplateTransformReceipt:
    text: str
    applied_rule_ids: tuple[str, ...]
    boilerplate_removed: bool
    source_identity_masked: bool


def _rule_id(source: str, role: str, rule_type: str, phrase_hash: str) -> str:
    return "NLP-BP-" + sha256_text(
        "\0".join((BOILERPLATE_REGISTRY_VERSION, source, role, rule_type, phrase_hash))
    )[:20].upper()


def _source_identity_rules(values: Sequence[SourceValue]) -> list[BoilerplateRule]:
    source_objects: dict[str, set[str]] = defaultdict(set)
    for value in values:
        if value.source_name:
            source_objects[value.source_name].add(value.public_object_id)
    rows: list[BoilerplateRule] = []
    for source in sorted(source_objects):
        phrase_hash = sha256_text(_normalize(source).casefold())
        support = len(source_objects[source])
        rows.append(
            BoilerplateRule(
                rule_id=_rule_id(source, "SOURCE_IDENTITY", "SOURCE_LITERAL", phrase_hash),
                source=source,
                field_role="SOURCE_IDENTITY",
                phrase_or_hash=f"sha256:{phrase_hash}",
                support=support,
                denominator=support,
                decision="MASK_SOURCE_IDENTITY",
                reason="Explicit source identity is masked in the source-leakage robustness variant.",
                removal_scope="SOURCE_NAME_AND_URL_VARIANT_ONLY",
                version=BOILERPLATE_REGISTRY_VERSION,
                rule_type="SOURCE_LITERAL",
                token_count=len(_tokens(source)),
            )
        )
    return rows


def _repetition_rules(values: Sequence[SourceValue]) -> tuple[list[BoilerplateRule], set[str]]:
    grouped: dict[tuple[str, str], list[SourceValue]] = defaultdict(list)
    for value in values:
        grouped[(value.source_name, value.role)].append(value)
    rows: list[BoilerplateRule] = []
    affected_objects: set[str] = set()
    for (source, role), group in sorted(grouped.items()):
        denominator = len(group)
        exact: dict[str, list[SourceValue]] = defaultdict(list)
        prefixes: dict[tuple[int, str], list[SourceValue]] = defaultdict(list)
        suffixes: dict[tuple[int, str], list[SourceValue]] = defaultdict(list)
        for value in group:
            normalized = _normalize(value.original_text)
            exact[sha256_text(normalized)].append(value)
            tokens = _tokens(normalized)
            for token_count in (5, 8):
                if len(tokens) >= token_count:
                    prefix = " ".join(tokens[:token_count])
                    suffix = " ".join(tokens[-token_count:])
                    prefixes[(token_count, sha256_text(prefix))].append(value)
                    suffixes[(token_count, sha256_text(suffix))].append(value)

        for phrase_hash, matching in sorted(exact.items()):
            support = len(matching)
            if support < 3 or support / denominator < 0.05:
                continue
            affected_objects.update(value.public_object_id for value in matching)
            decision = "KEEP_SEMANTIC" if role == "OBJECT_TITLE" else "HOLD"
            reason = (
                "Repeated title is retained because title duplication does not prove boilerplate or identity."
                if role == "OBJECT_TITLE"
                else "Exact source-conditioned repetition is a boilerplate candidate requiring explicit review."
            )
            rows.append(
                BoilerplateRule(
                    rule_id=_rule_id(source, role, "EXACT_TEMPLATE", phrase_hash),
                    source=source,
                    field_role=role,
                    phrase_or_hash=f"sha256:{phrase_hash}",
                    support=support,
                    denominator=denominator,
                    decision=decision,
                    reason=reason,
                    removal_scope="SOURCE_AND_ROLE_ONLY",
                    version=BOILERPLATE_REGISTRY_VERSION,
                    rule_type="EXACT_TEMPLATE",
                    token_count=0,
                )
            )

        minimum_phrase_support = max(5, math.ceil(denominator * 0.20))
        for rule_type, candidates in (("PREFIX", prefixes), ("SUFFIX", suffixes)):
            for (token_count, phrase_hash), matching in sorted(candidates.items()):
                # One document contributes at most once to each prefix/suffix key.
                object_support = len({value.public_object_id for value in matching})
                if object_support < minimum_phrase_support:
                    continue
                affected_objects.update(value.public_object_id for value in matching)
                rows.append(
                    BoilerplateRule(
                        rule_id=_rule_id(source, role, rule_type, phrase_hash),
                        source=source,
                        field_role=role,
                        phrase_or_hash=f"sha256:{phrase_hash}",
                        support=object_support,
                        denominator=denominator,
                        decision="HOLD",
                        reason=(
                            "High-support source-conditioned phrase is registered for review; "
                            "frequency alone does not authorize removal."
                        ),
                        removal_scope="SOURCE_AND_ROLE_ONLY",
                        version=BOILERPLATE_REGISTRY_VERSION,
                        rule_type=rule_type,
                        token_count=token_count,
                    )
                )
    return rows, affected_objects


@lru_cache(maxsize=1)
def discover_boilerplate_registry() -> tuple[BoilerplateRule, ...]:
    values = tuple(iter_public_sources())
    source_rules = _source_identity_rules(values)
    repetition_rules, _affected = _repetition_rules(values)
    rows = tuple(sorted((*source_rules, *repetition_rules), key=lambda row: row.rule_id))
    if len({row.rule_id for row in rows}) != len(rows):
        raise RuntimeError("boilerplate registry rule IDs are not unique")
    if any(row.decision not in ALLOWED_DECISIONS for row in rows):
        raise RuntimeError("boilerplate registry contains an invalid decision")
    return rows


def boilerplate_registry_rows() -> tuple[dict[str, Any], ...]:
    return tuple(row.as_mapping() for row in discover_boilerplate_registry())


def boilerplate_registry_sha256() -> str:
    return sha256_json(
        {"version": BOILERPLATE_REGISTRY_VERSION, "rows": boilerplate_registry_rows()}
    )


def mask_source_identity(text: str, source_name: str) -> tuple[str, int]:
    masked, url_count = URL_PATTERN.subn(" <URL> ", text)
    source_count = 0
    source = _normalize(source_name)
    if source:
        masked, source_count = re.subn(re.escape(source), " <SOURCE> ", masked, flags=re.IGNORECASE)
    return _normalize(masked), url_count + source_count


def mask_structured_labels(text: str, labels: Iterable[str]) -> tuple[str, int]:
    masked = text
    replacements = 0
    for label in sorted({_normalize(value) for value in labels if _normalize(value)}, key=lambda x: (-len(x), x)):
        if len(label) < 3:
            continue
        masked, count = re.subn(re.escape(label), " <LABEL> ", masked, flags=re.IGNORECASE)
        replacements += count
    return _normalize(masked), replacements


def apply_registered_rules(
    *,
    source: str,
    field_role: str,
    text: str,
    rules: Iterable[Mapping[str, Any]] | None = None,
) -> BoilerplateTransformReceipt:
    """Apply only explicit registered decisions; HOLD candidates never mutate text."""

    selected = list(rules if rules is not None else boilerplate_registry_rows())
    result = _normalize(text)
    applied: list[str] = []
    removed = False
    masked = False
    for rule in sorted(selected, key=lambda row: str(row.get("rule_id", ""))):
        if rule.get("source") != source:
            continue
        decision = rule.get("decision")
        role = rule.get("field_role")
        if decision == "MASK_SOURCE_IDENTITY" and role == "SOURCE_IDENTITY":
            result, count = mask_source_identity(result, source)
            if count:
                masked = True
                applied.append(str(rule["rule_id"]))
        elif decision == "REMOVE_FOR_NLP_INPUT" and role == field_role:
            expected_hash = str(rule.get("phrase_or_hash", "")).removeprefix("sha256:")
            if rule.get("rule_type") == "EXACT_TEMPLATE" and sha256_text(result) == expected_hash:
                result = ""
                removed = True
                applied.append(str(rule["rule_id"]))
    return BoilerplateTransformReceipt(
        text=result,
        applied_rule_ids=tuple(applied),
        boilerplate_removed=removed,
        source_identity_masked=masked,
    )


def boilerplate_summary() -> dict[str, Any]:
    values = tuple(iter_public_sources())
    _rows, affected = _repetition_rules(values)
    registry = discover_boilerplate_registry()
    counts = Counter(row.decision for row in registry)
    return {
        "schemaVersion": "trace-nlp-boilerplate-summary/v1",
        "registryVersion": BOILERPLATE_REGISTRY_VERSION,
        "ruleCount": len(registry),
        "affectedPublicObjectCount": len(affected),
        "decisionCounts": dict(sorted(counts.items())),
        "registrySha256": boilerplate_registry_sha256(),
        "hiddenPhraseBlacklist": False,
    }


def self_test() -> dict[str, Any]:
    summary = boilerplate_summary()
    first = boilerplate_registry_sha256()
    second = boilerplate_registry_sha256()
    if first != second:
        raise AssertionError("boilerplate registry is not deterministic")
    if summary["decisionCounts"].get("REMOVE_FOR_NLP_INPUT", 0):
        raise AssertionError("unreviewed frequency candidate was authorized for removal")
    masked, count = mask_source_identity(
        "A record from Example Archive at https://example.test/record", "Example Archive"
    )
    if count != 2 or "Example Archive" in masked or "https://" in masked:
        raise AssertionError("source-identity masking failed")
    labels_masked, label_count = mask_structured_labels(
        "Poster design and poster typography", ["Poster", "Typography"]
    )
    if label_count != 3 or "poster" in labels_masked.casefold():
        raise AssertionError("structured-label masking failed")
    return {"status": "PASS", **summary}


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
