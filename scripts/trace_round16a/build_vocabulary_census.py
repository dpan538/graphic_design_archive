#!/usr/bin/env python3
"""Compile the frozen Round 16A vocabulary census and active contract.

The compiler is deliberately vocabulary-only.  It reads the frozen candidate
universe and governed vocabulary/association/composition artifacts from prior
rounds; it never reads archive object, Context, Search, or Spacetime records.
Association calibration controls are not promoted into vocabulary evidence.

The default invocation writes exactly the four raw artifacts and two research
notes declared in ``OUTPUT_PATHS``.  ``--check`` compares deterministic bytes
without writing.  No existing Round 9--16 artifact or execution log is changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]

RAW_ROOT = Path(
    "docs/audits/v49-exploration-full-space-closure-round1/raw"
)
RESEARCH_ROOT = Path(
    "docs/research/trace-v49-exploration-full-space-closure-round1"
)

CANDIDATE_UNIVERSE = RAW_ROOT / "vocabulary-candidate-universe-v2.json"
DATABASE_IDENTITY = RAW_ROOT / "database-identity-v2.json"

ROUND9_RAW = Path(
    "docs/research/trace-v49-design-history-relation-vocabulary-round1/"
    "04_RAW_CANDIDATE_TERM_REGISTRY.tsv"
)
ROUND9_ATTESTATIONS = Path(
    "docs/research/trace-v49-design-history-relation-vocabulary-round1/"
    "05_TERM_ATTESTATION_REGISTRY.tsv"
)
ROUND9_GLOSSES = Path(
    "docs/research/trace-v49-design-history-relation-vocabulary-round1/"
    "07_SEMANTIC_GLOSS_REGISTRY.tsv"
)
ROUND10_DECISIONS = Path(
    "docs/research/trace-v49-design-history-relation-grammar-round1/"
    "05_NODE_ROLE_DECISION_REGISTRY.tsv"
)
ROUND13_EVIDENCE = Path(
    "docs/research/trace-v49-exploration-composition-review-round1/"
    "06_VOCABULARY_GAP_EVIDENCE.tsv"
)
ROUND13_DECISIONS = Path(
    "docs/research/trace-v49-exploration-composition-review-round1/"
    "07_VOCABULARY_GAP_DECISIONS.tsv"
)
ROUND14_ASSESSMENTS = Path(
    "scripts/trace-v49-exploration-association-calibration/fixtures/"
    "association-assessments-v1.json"
)
ROUND16_ADDITIONS = Path(
    "scripts/trace-v49-exploration-real-database/"
    "scholarly-source-additions-v1.tsv"
)
ROUND16_ACTIVE = Path(
    "docs/audits/v49-exploration-real-database-round1/raw/"
    "active-vocabulary-audit.tsv"
)
ROUND16_PROVENANCE = Path(
    "docs/audits/v49-exploration-real-database-round1/raw/"
    "vocabulary-provenance-audit.tsv"
)
ROUND16_COMPOSITIONS = Path(
    "scripts/trace-v49-exploration-real-database/"
    "real-composition-registry-v1.json"
)

OUTPUT_PATHS = {
    "census_tsv": RAW_ROOT / "vocabulary-census-v2.tsv",
    "census_json": RAW_ROOT / "vocabulary-census-v2.json",
    "future_tsv": RAW_ROOT / "future-vocabulary-candidates.tsv",
    "active_json": RAW_ROOT / "active-vocabulary-v2.json",
    "census_note": RESEARCH_ROOT / "06_VOCABULARY_CENSUS.md",
    "reconciliation_note": (
        RESEARCH_ROOT / "07_VOCABULARY_DISPOSITION_RECONCILIATION.md"
    ),
}

FORMAT = "trace-exploration-vocabulary-census-v2"
VERSION = "2"
EXPECTED_CANDIDATE_COUNT = 65
EXPECTED_BASELINE_ACTIVE_COUNT = 26
EXPECTED_ACTIVE_COUNT = 31
EXPECTED_CATEGORY_IDS = ("region", "theme", "medium", "movement")
ACTIVE_ID_PREFIX = "TRV"

EXPECTED_BASELINE_ACTIVE_LABELS = {
    "adaptation",
    "advertising",
    "commodification",
    "consumer culture",
    "consumption",
    "craft",
    "cultural negotiation",
    "design diplomacy",
    "design education",
    "education",
    "exhibition",
    "gendering",
    "imitation",
    "institutionalization",
    "material displacement",
    "mediation",
    "photography",
    "piracy",
    "production",
    "production site",
    "professionalization",
    "propaganda",
    "rejection",
    "supply chain",
    "trade",
    "typography",
}

ADDED_ACTIVE_LABELS = {
    "canonization",
    "self-exoticization",
    "cultural transfer",
    "cultural transformation",
    "mobile object",
}

MERGED_LABEL_TO_TARGET = {"cultural adaptation": "adaptation"}

ROUND14_FAILED_ONLY_CONTROLS = {
    "arts and crafts",
    "bauhaus",
    "brazilian exposition",
    "desktop publishing",
    "digital interface",
    "photomontage",
    "swiss typography",
}

ROUND9_REJECTED_LABELS = {
    "collective process",
    "oblikovanje",
    "power relations",
    "relational infrastructure",
    "transnationalism",
}

# Freeze the exact candidate population so a changed upstream universe cannot
# silently acquire a disposition under the default policy.
EXPECTED_UNIVERSE_LABELS = {
    "access",
    "adaptation",
    "advertising",
    "appropriation",
    "arts and crafts",
    "bauhaus",
    "brazilian exposition",
    "canonization",
    "circulation",
    "collective process",
    "collective production",
    "coloniality",
    "commodification",
    "consumer culture",
    "consumption",
    "craft",
    "creative appropriation",
    "cultural adaptation",
    "cultural diplomacy",
    "cultural mobility",
    "cultural negotiation",
    "cultural transfer",
    "cultural transferral",
    "cultural transformation",
    "cultural translation",
    "decolonization",
    "design diplomacy",
    "design education",
    "design exchanges",
    "desktop publishing",
    "digital interface",
    "displacement",
    "education",
    "erasure",
    "exclusion",
    "exhibition",
    "gendering",
    "imitation",
    "institutionalization",
    "material displacement",
    "mediating channels",
    "mediating devices",
    "mediation",
    "mobile object",
    "oblikovanje",
    "photography",
    "photomontage",
    "piracy",
    "power relations",
    "production",
    "production site",
    "professionalization",
    "propaganda",
    "rejection",
    "relational infrastructure",
    "self-exoticization",
    "supply chain",
    "swiss typography",
    "trade",
    "transculturation",
    "translation",
    "transnational interactions",
    "transnationalism",
    "typography",
    "work migrations",
}

# The first 26 labels derive category bindings from governed Round 16
# compositions.  These five additions have more than one category because the
# cited governed senses explicitly span the listed entry dimensions.  The
# evidence references document each binding without copying an object record.
ADDED_CATEGORY_BINDINGS: dict[str, dict[str, tuple[str, ...]]] = {
    "canonization": {
        "medium": ("ATT-0008",),
        "movement": ("ATT-0007",),
    },
    "self-exoticization": {
        "region": ("ATT-0040", "ATT-0041"),
        "theme": ("REL-CAND-0025#SENSE-A",),
    },
    "cultural transfer": {
        "region": ("COMP-EVID-012", "COMP-EVID-013"),
        "theme": ("COMP-EVID-012",),
        "medium": ("COMP-EVID-013",),
    },
    "cultural transformation": {
        "region": ("COMP-EVID-018",),
        "movement": ("COMP-EVID-018", "COMP-EVID-019"),
    },
    "mobile object": {
        "region": ("COMP-EVID-022", "COMP-EVID-023"),
        "medium": ("COMP-EVID-022", "COMP-EVID-023"),
    },
}

DISPOSITION_TO_STATUS = {
    "ACTIVE": "ACTIVE_USER_VISIBLE",
    "MERGED_SUPERSEDED": "SUPERSEDED_BY_ACTIVE_CANONICAL_LABEL",
    "RESEARCH_ONLY": "GOVERNED_RESEARCH_ONLY",
    "REJECTED": "GOVERNED_REJECTED",
}

# Keys or values carrying archive-record identity are forbidden from every
# emitted artifact.  Academic source and bounded evidence identifiers remain
# allowed; archive-source identifiers (R14-ARC-*) do not.
FORBIDDEN_KEY_TOKENS = {
    "archiveobjectref",
    "archiveobjectrefs",
    "archivesourceref",
    "archivesourcerefs",
    "contextref",
    "contextrefs",
    "spacetimeref",
    "spacetimerefs",
    "objectid",
    "objectids",
    "objecttitle",
    "objecttitles",
}
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"(?:^|[^A-Z0-9])R14-ARC-", re.IGNORECASE),
    re.compile(r"(?:^|[^A-Z0-9])CTX:", re.IGNORECASE),
    re.compile(r"(?:^|[^A-Z0-9])SPTGEO:", re.IGNORECASE),
    re.compile(r"(?:^|[^A-Z0-9])SURF-", re.IGNORECASE),
    re.compile(r"(?:^|[^A-Z0-9])OBJ-", re.IGNORECASE),
    re.compile(r"archive[_ -]?object", re.IGNORECASE),
)


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def normalize_label(value: Any) -> str:
    return re.sub(
        r"\s+", " ", unicodedata.normalize("NFKC", clean_text(value))
    ).casefold().strip()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        (canonical_json(value) + "\n").encode("utf-8")
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def unique_sorted(values: Iterable[Any]) -> list[str]:
    cleaned = {clean_text(value) for value in values}
    return sorted(
        (value for value in cleaned if value),
        key=lambda value: (normalize_label(value), value),
    )


def split_semicolon(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return unique_sorted(value.split(";"))


def split_json_or_semicolon(value: Any) -> list[str]:
    if isinstance(value, list):
        return unique_sorted(value)
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return split_semicolon(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON list, received {value!r}")
    return unique_sorted(parsed)


def require_fields(
    rows: Sequence[Mapping[str, Any]],
    fields: Iterable[str],
    source: Path,
) -> None:
    if not rows:
        raise ValueError(f"Governed input has no rows: {source}")
    missing = set(fields) - set(rows[0])
    if missing:
        raise ValueError(
            f"Governed input {source} lacks fields: {sorted(missing)}"
        )


def read_tsv(
    repo: Path,
    relative_path: Path,
    fields: Iterable[str],
) -> list[dict[str, str]]:
    path = repo / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Missing governed input: {relative_path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    require_fields(rows, fields, relative_path)
    return rows


def read_json(repo: Path, relative_path: Path) -> Any:
    path = repo / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Missing governed input: {relative_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def index_rows(
    rows: Iterable[dict[str, str]], field: str
) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        label = normalize_label(row.get(field))
        if label:
            indexed.setdefault(label, []).append(row)
    return indexed


def row_ref(path: Path, value: str) -> str:
    return f"{path.as_posix()}#{clean_text(value)}"


def is_safe_reference(value: Any) -> bool:
    text = clean_text(value)
    return bool(text) and not any(
        pattern.search(text) for pattern in FORBIDDEN_VALUE_PATTERNS
    )


def safe_references(values: Iterable[Any]) -> list[str]:
    return unique_sorted(value for value in values if is_safe_reference(value))


def assert_safe_output(value: Any, location: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized_key in FORBIDDEN_KEY_TOKENS:
                raise ValueError(f"Forbidden output key at {location}: {key}")
            assert_safe_output(child, f"{location}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            assert_safe_output(child, f"{location}[{index}]")
        return
    if isinstance(value, str):
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                raise ValueError(
                    f"Forbidden archive/Context/Spacetime value at {location}: "
                    f"{value!r}"
                )


def verify_universe(repo: Path, universe: dict[str, Any]) -> list[dict[str, Any]]:
    if universe.get("candidate_count") != EXPECTED_CANDIDATE_COUNT:
        raise ValueError(
            f"Candidate universe count must be {EXPECTED_CANDIDATE_COUNT}, "
            f"received {universe.get('candidate_count')!r}"
        )
    candidates = universe.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError("Candidate universe rows do not reconcile to candidate_count")
    expected_hash = clean_text(universe.get("universe_canonical_hash"))
    if not expected_hash:
        raise ValueError("Candidate universe lacks universe_canonical_hash")
    canonical_material = {
        key: value
        for key, value in universe.items()
        if key != "universe_canonical_hash"
    }
    if canonical_hash(canonical_material) != expected_hash:
        raise ValueError("Candidate universe canonical hash mismatch")

    normalized = [normalize_label(row.get("canonical_label")) for row in candidates]
    if any(not label for label in normalized) or len(set(normalized)) != len(normalized):
        raise ValueError("Candidate labels must be nonempty and normalized-unique")
    if set(normalized) != EXPECTED_UNIVERSE_LABELS:
        missing = sorted(EXPECTED_UNIVERSE_LABELS - set(normalized))
        unexpected = sorted(set(normalized) - EXPECTED_UNIVERSE_LABELS)
        raise ValueError(
            f"Frozen 65-label population changed; missing={missing}, "
            f"unexpected={unexpected}"
        )

    source_inputs = universe.get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        raise ValueError("Candidate universe lacks governed source_inputs")
    for item in source_inputs:
        if not isinstance(item, dict):
            raise ValueError("Malformed candidate-universe source input")
        relative = Path(clean_text(item.get("path")))
        expected = clean_text(item.get("sha256"))
        path = repo / relative
        if not relative.as_posix() or not path.is_file() or not expected:
            raise ValueError(f"Incomplete governed source input: {item!r}")
        if sha256_file(path) != expected:
            raise ValueError(f"Governed source hash mismatch: {relative}")
        expected_bytes = item.get("bytes")
        if expected_bytes is not None and path.stat().st_size != int(expected_bytes):
            raise ValueError(f"Governed source byte-size mismatch: {relative}")
    return candidates


def build_input_manifest(
    repo: Path, universe: dict[str, Any]
) -> list[dict[str, Any]]:
    paths: dict[str, str] = {
        CANDIDATE_UNIVERSE.as_posix(): "FROZEN_CANDIDATE_UNIVERSE",
        DATABASE_IDENTITY.as_posix(): "ROUND16A_DATABASE_IDENTITY",
        ROUND9_GLOSSES.as_posix(): "ROUND9_BOUNDED_SEMANTIC_GLOSSES",
        ROUND16_COMPOSITIONS.as_posix(): "ROUND16_CATEGORY_COMPOSITIONS",
    }
    for item in universe["source_inputs"]:
        paths.setdefault(
            clean_text(item["path"]),
            clean_text(item.get("role")) or "GOVERNED_UNIVERSE_SOURCE",
        )
    manifest = []
    for path_text, role in sorted(paths.items()):
        relative = Path(path_text)
        path = repo / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing governed input: {relative}")
        manifest.append({
            "path": relative.as_posix(),
            "role": role,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return manifest


def build_indexes(repo: Path) -> dict[str, Any]:
    round9 = read_tsv(
        repo,
        ROUND9_RAW,
        ("candidate_id", "candidate_label", "final_decision", "decision_reason"),
    )
    attestations = read_tsv(
        repo,
        ROUND9_ATTESTATIONS,
        ("attestation_id", "candidate_id", "source_id", "attestation_verified"),
    )
    glosses = read_tsv(
        repo,
        ROUND9_GLOSSES,
        (
            "candidate_label",
            "plain_language_gloss",
            "scope_in",
            "scope_out",
            "confusable_terms",
            "source_support_ids",
            "explainability_pass",
        ),
    )
    round10 = read_tsv(
        repo,
        ROUND10_DECISIONS,
        (
            "candidate_label",
            "final_node_role_decision",
            "decision_reason",
            "pass_node",
        ),
    )
    gap_evidence = read_tsv(
        repo,
        ROUND13_EVIDENCE,
        (
            "evidence_id",
            "candidate_sense_ids",
            "source_id",
            "exact_attested_terms",
            "bounded_context",
            "composition_kind",
            "qualification",
            "contestation",
            "evidence_verified",
            "semantic_review",
        ),
    )
    gap_decisions = read_tsv(
        repo,
        ROUND13_DECISIONS,
        (
            "gap_id",
            "final_decision",
            "attested_terms",
            "reason",
            "scope_out",
            "verified",
        ),
    )
    additions = read_tsv(
        repo,
        ROUND16_ADDITIONS,
        (
            "source_id",
            "supported_terms",
            "scope_note",
            "metadata_verified",
        ),
    )
    active = read_tsv(
        repo,
        ROUND16_ACTIVE,
        (
            "vocabulary_id",
            "canonical_label",
            "activation_status",
            "status",
        ),
    )
    provenance = read_tsv(
        repo,
        ROUND16_PROVENANCE,
        (
            "vocabulary_id",
            "canonical_label",
            "attestation_refs",
            "academic_support_refs",
            "provenance_chain_complete",
            "status",
        ),
    )

    assessment_document = read_json(repo, ROUND14_ASSESSMENTS)
    assessments = assessment_document.get("assessments")
    if not isinstance(assessments, list) or not assessments:
        raise ValueError("Round 14 assessment fixture has no assessments")
    required_assessment_fields = {
        "assessmentId",
        "nodeA",
        "nodeB",
        "activeForProximity",
        "evidenceStatus",
        "decisionReason",
        "qualification",
    }
    for row in assessments:
        if not isinstance(row, dict) or not required_assessment_fields <= set(row):
            raise ValueError("Malformed Round 14 association assessment")

    evidence_by_label: dict[str, list[dict[str, str]]] = {}
    for row in gap_evidence:
        if row.get("evidence_verified") != "true" or row.get("semantic_review") != "PASS_BOUNDED":
            raise ValueError(
                f"Unverified Round 13 evidence row: {row.get('evidence_id')}"
            )
        for term in split_semicolon(row.get("exact_attested_terms")):
            evidence_by_label.setdefault(normalize_label(term), []).append(row)

    gap_decisions_by_label: dict[str, list[dict[str, str]]] = {}
    for row in gap_decisions:
        if row.get("verified") != "true":
            raise ValueError(f"Unverified Round 13 decision: {row.get('gap_id')}")
        for term in split_semicolon(row.get("attested_terms")):
            gap_decisions_by_label.setdefault(normalize_label(term), []).append(row)

    assessments_by_label: dict[str, list[dict[str, Any]]] = {}
    for row in assessments:
        for field in ("nodeA", "nodeB"):
            label = normalize_label(row[field])
            assessments_by_label.setdefault(label, []).append(row)

    additions_by_label: dict[str, list[dict[str, str]]] = {}
    for row in additions:
        if row.get("metadata_verified") != "true":
            raise ValueError(f"Unverified Round 16 source: {row.get('source_id')}")
        for term in split_semicolon(row.get("supported_terms")):
            additions_by_label.setdefault(normalize_label(term), []).append(row)

    active_by_label = index_rows(active, "canonical_label")
    provenance_by_label = index_rows(provenance, "canonical_label")
    if len(active_by_label) != EXPECTED_BASELINE_ACTIVE_COUNT:
        raise ValueError(
            f"Round 16 baseline must contain {EXPECTED_BASELINE_ACTIVE_COUNT} labels"
        )
    if set(active_by_label) != EXPECTED_BASELINE_ACTIVE_LABELS:
        raise ValueError("The exact governed Round 16 26-label baseline changed")
    if set(active_by_label) != set(provenance_by_label):
        raise ValueError("Round 16 active/provenance label sets differ")
    for label, rows in active_by_label.items():
        if len(rows) != 1 or rows[0]["activation_status"] != "ACTIVE_USER_VISIBLE" or rows[0]["status"] != "PASS":
            raise ValueError(f"Invalid Round 16 active row for {label}")
        provenance_row = provenance_by_label[label]
        if len(provenance_row) != 1:
            raise ValueError(f"Duplicate Round 16 provenance row for {label}")
        prov = provenance_row[0]
        if prov["status"] != "PASS" or prov["provenance_chain_complete"].casefold() != "true":
            raise ValueError(f"Incomplete Round 16 provenance for {label}")
        if rows[0]["vocabulary_id"] != prov["vocabulary_id"]:
            raise ValueError(f"Round 16 vocabulary ID mismatch for {label}")

    rejected_round9 = {
        normalize_label(row["candidate_label"])
        for row in round9
        if row["final_decision"].startswith("REJECT_")
    }
    if rejected_round9 != ROUND9_REJECTED_LABELS:
        raise ValueError(
            "Round 9 governed rejection set changed: "
            f"{sorted(rejected_round9)}"
        )

    for label in ROUND14_FAILED_ONLY_CONTROLS:
        rows = assessments_by_label.get(label, [])
        if not rows or any(row["activeForProximity"] is not False for row in rows):
            raise ValueError(f"Round 14 failed-only control changed: {label}")
        if not all(
            row.get("hardNegative") is True
            or row.get("cooccurrenceOnly") is True
            or row.get("evidenceStatus") == "INSUFFICIENT"
            for row in rows
        ):
            raise ValueError(f"Round 14 control lacks governed failure basis: {label}")

    return {
        "round9": index_rows(round9, "candidate_label"),
        "attestations": attestations,
        "glosses": index_rows(glosses, "candidate_label"),
        "round10": index_rows(round10, "candidate_label"),
        "gap_evidence": evidence_by_label,
        "gap_decisions": gap_decisions_by_label,
        "assessments": assessments_by_label,
        "additions": additions_by_label,
        "active": active_by_label,
        "provenance": provenance_by_label,
    }


def build_category_bindings(
    repo: Path,
    baseline_labels: set[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    document = read_json(repo, ROUND16_COMPOSITIONS)
    if not isinstance(document, dict):
        raise ValueError("Malformed Round 16 composition registry")
    if tuple(document.get("categoryOrder", [])) != EXPECTED_CATEGORY_IDS:
        raise ValueError("Round 16 governed category order changed")
    if set(document.get("categories", {})) != set(EXPECTED_CATEGORY_IDS):
        raise ValueError("Round 16 governed category set must be exactly four")
    compositions = document.get("compositions")
    if not isinstance(compositions, list) or not compositions:
        raise ValueError("Round 16 composition registry has no compositions")

    categories: dict[str, set[str]] = {}
    refs: dict[str, set[str]] = {}
    for row in compositions:
        if not isinstance(row, dict):
            raise ValueError("Malformed Round 16 composition")
        category_id = clean_text(row.get("categoryId"))
        composition_id = clean_text(row.get("compositionId"))
        node_ids = row.get("nodeIds")
        if category_id not in EXPECTED_CATEGORY_IDS or not composition_id:
            raise ValueError("Composition has invalid category or identifier")
        if not isinstance(node_ids, list) or not node_ids:
            raise ValueError(f"Composition {composition_id} has no nodeIds")
        for node in node_ids:
            label = normalize_label(node)
            categories.setdefault(label, set()).add(category_id)
            refs.setdefault(label, set()).add(composition_id)

    if set(categories) != baseline_labels:
        raise ValueError(
            "Round 16 composition nodes do not exactly bind the 26-label baseline"
        )

    order = {category: index for index, category in enumerate(EXPECTED_CATEGORY_IDS)}
    result_categories = {
        label: sorted(values, key=order.__getitem__)
        for label, values in categories.items()
    }
    result_refs = {
        label: unique_sorted(values) for label, values in refs.items()
    }
    for label, bindings in ADDED_CATEGORY_BINDINGS.items():
        result_categories[label] = sorted(bindings, key=order.__getitem__)
        result_refs[label] = safe_references(
            ref for values in bindings.values() for ref in values
        )
    return result_categories, result_refs


def database_snapshot(repo: Path) -> str:
    identity = read_json(repo, DATABASE_IDENTITY)
    if not isinstance(identity, dict) or identity.get("status") != "PASS":
        raise ValueError("Round 16A database identity must have PASS status")
    if identity.get("database_schema_version") != 49:
        raise ValueError("Active vocabulary must bind the frozen v49 database")
    category_authority = identity.get("category_authority")
    if not isinstance(category_authority, dict):
        raise ValueError("Database identity lacks category authority")
    if category_authority.get("governed_folder_type_count") != 4:
        raise ValueError("Database identity does not govern exactly four folder types")
    if set(category_authority.get("observed_governed_folder_types", [])) != set(EXPECTED_CATEGORY_IDS):
        raise ValueError("Database identity governed folder types changed")
    if identity.get("validation", {}).get("four_category_authority") != "PASS":
        raise ValueError("Database category authority is not validated")
    snapshot = clean_text(identity.get("database_snapshot_id"))
    if not snapshot:
        raise ValueError("Database identity lacks database_snapshot_id")
    return snapshot


def round13_rows(indexes: dict[str, Any], label: str) -> list[dict[str, str]]:
    return indexes["gap_evidence"].get(label, [])


def positive_assessments(indexes: dict[str, Any], label: str) -> list[dict[str, Any]]:
    return [
        row
        for row in indexes["assessments"].get(label, [])
        if row.get("activeForProximity") is True
    ]


def bounded_sense(indexes: dict[str, Any], label: str) -> str:
    gloss_rows = indexes["glosses"].get(label, [])
    if gloss_rows:
        if len(gloss_rows) != 1 or gloss_rows[0]["explainability_pass"] != "true":
            raise ValueError(f"Unvalidated or duplicate semantic gloss for {label}")
        value = clean_text(gloss_rows[0]["plain_language_gloss"])
        if value:
            return value

    evidence = round13_rows(indexes, label)
    if evidence:
        kinds = unique_sorted(
            row["composition_kind"].replace("_", " ").casefold()
            for row in evidence
        )
        qualifications = unique_sorted(row["qualification"] for row in evidence)
        return (
            f"In governed design-history evidence, {label} denotes "
            f"{'; '.join(kinds)}. Use requires {('; '.join(qualifications))}."
        )

    additions = indexes["additions"].get(label, [])
    if additions:
        notes = unique_sorted(row["scope_note"] for row in additions)
        return f"In the governed Round 16 sources, {label} is bounded as follows: {'; '.join(notes)}"

    assessments = positive_assessments(indexes, label)
    if assessments:
        bases = unique_sorted(row.get("decisionReason") for row in assessments)
        qualifications = unique_sorted(row.get("qualification") for row in assessments)
        basis_text = "; ".join(bases)
        qualification_text = "; ".join(qualifications)
        return (
            f"In governed Round 14 design-history evidence, {label} is used "
            f"on this bounded basis: {basis_text}. {qualification_text}"
        ).strip()

    raise ValueError(f"No governed bounded sense for active label: {label}")


def scope_note(indexes: dict[str, Any], label: str) -> str:
    gap_rows = indexes["gap_decisions"].get(label, [])
    if gap_rows:
        return " ".join(unique_sorted(row["scope_out"] for row in gap_rows))
    gloss_rows = indexes["glosses"].get(label, [])
    if gloss_rows:
        row = gloss_rows[0]
        return f"In scope: {clean_text(row['scope_in'])}. Out of scope: {clean_text(row['scope_out'])}."
    additions = indexes["additions"].get(label, [])
    if additions:
        return " ".join(unique_sorted(row["scope_note"] for row in additions))
    assessments = positive_assessments(indexes, label)
    if assessments:
        return " ".join(unique_sorted(row.get("qualification") for row in assessments))
    raise ValueError(f"No governed scope note for active label: {label}")


def ambiguity_note(indexes: dict[str, Any], label: str) -> str:
    evidence = round13_rows(indexes, label)
    if evidence:
        notes = unique_sorted(row["contestation"] for row in evidence)
        if notes:
            return " ".join(notes)
    gloss_rows = indexes["glosses"].get(label, [])
    if gloss_rows:
        row = gloss_rows[0]
        confusable = clean_text(row["confusable_terms"])
        return (
            f"Do not expand beyond the governed scope-out. Confusable terms: "
            f"{confusable or 'none recorded'}."
        )
    assessments = positive_assessments(indexes, label)
    if assessments:
        notes = unique_sorted(
            row.get("qualification") or row.get("decisionReason")
            for row in assessments
        )
        if notes:
            return " ".join(notes)
    return (
        "The label alone does not establish association, direction, causality, "
        "or an archive-record classification."
    )


def active_support(
    candidate: dict[str, Any],
    indexes: dict[str, Any],
    label: str,
) -> tuple[list[str], list[str]]:
    if label in indexes["active"]:
        provenance = indexes["provenance"][label][0]
        attestations = safe_references(
            split_json_or_semicolon(provenance["attestation_refs"])
        )
        support = safe_references(
            split_json_or_semicolon(provenance["academic_support_refs"])
        )
    elif label in {"canonization", "self-exoticization"}:
        attestations = safe_references(candidate.get("attestation_refs", []))
        support = safe_references(candidate.get("scholarly_source_refs", []))
    else:
        rows = round13_rows(indexes, label)
        attestations = safe_references(row["evidence_id"] for row in rows)
        support = safe_references(row["source_id"] for row in rows)
    if not attestations or not support:
        raise ValueError(f"Active label lacks safe governed support: {label}")
    return attestations, support


def active_vocabulary_id(indexes: dict[str, Any], label: str) -> str:
    if label in indexes["active"]:
        return indexes["active"][label][0]["vocabulary_id"]
    digest = hashlib.sha256(label.encode("utf-8")).hexdigest()
    return f"{ACTIVE_ID_PREFIX}:{digest}"


def governed_decision(
    indexes: dict[str, Any],
    label: str,
    disposition: str,
) -> tuple[str, list[str], list[str]]:
    if disposition == "ACTIVE":
        if label in indexes["active"]:
            row = indexes["active"][label][0]
            return (
                "Round 16 records the term as ACTIVE_USER_VISIBLE with a complete "
                "academic provenance chain.",
                [row_ref(ROUND16_ACTIVE, row["vocabulary_id"])],
                ["ROUND16"],
            )
        if label in {"canonization", "self-exoticization"}:
            row = indexes["round10"][label][0]
            return (
                f"Round 16A promotes the bounded Round 10 node decision "
                f"{row['final_node_role_decision']}: {clean_text(row['decision_reason'])}",
                [row_ref(ROUND10_DECISIONS, row.get("sense_id") or label)],
                ["ROUND9", "ROUND10", "ROUND16A"],
            )
        gap = indexes["gap_decisions"][label][0]
        return (
            f"Round 16A promotes the verified Round 13 split sense "
            f"{gap['final_decision']}: {clean_text(gap['reason'])}",
            [row_ref(ROUND13_DECISIONS, gap["gap_id"] + ":" + label)],
            ["ROUND13", "ROUND16A"],
        )

    if disposition == "MERGED_SUPERSEDED":
        gap = indexes["gap_decisions"][label][0]
        return (
            "Round 16A reconciles the bounded phrase cultural adaptation into "
            "the already-active canonical label adaptation; its distinct source "
            "evidence remains provenance, not a second user-visible label.",
            [row_ref(ROUND13_DECISIONS, gap["gap_id"] + ":" + label)],
            ["ROUND13", "ROUND16A"],
        )

    if label in ROUND14_FAILED_ONLY_CONTROLS:
        rows = indexes["assessments"][label]
        reasons = unique_sorted(row["decisionReason"] for row in rows)
        refs = [row_ref(ROUND14_ASSESSMENTS, row["assessmentId"]) for row in rows]
        return (
            "Round 14 failed-only calibration control: " + " ".join(reasons),
            refs,
            ["ROUND14"],
        )

    round9_rows = indexes["round9"].get(label, [])
    if disposition == "REJECTED":
        if len(round9_rows) != 1 or not round9_rows[0]["final_decision"].startswith("REJECT_"):
            raise ValueError(f"Rejected term lacks governed rejection: {label}")
        row = round9_rows[0]
        return (
            f"Round 9 {row['final_decision']}: {clean_text(row['decision_reason'])}",
            [row_ref(ROUND9_RAW, row["candidate_id"])],
            ["ROUND9"],
        )

    gap_rows = indexes["gap_decisions"].get(label, [])
    if gap_rows:
        row = gap_rows[0]
        return (
            f"Round 13 {row['final_decision']}: {clean_text(row['reason'])}",
            [row_ref(ROUND13_DECISIONS, row["gap_id"] + ":" + label)],
            ["ROUND13"],
        )
    round10_rows = indexes["round10"].get(label, [])
    if round10_rows:
        row = round10_rows[0]
        return (
            f"Round 10 {row['final_node_role_decision']}: "
            f"{clean_text(row['decision_reason'])}",
            [row_ref(ROUND10_DECISIONS, row.get("sense_id") or label)],
            ["ROUND10"],
        )
    if round9_rows:
        row = round9_rows[0]
        return (
            f"Round 9 {row['final_decision']}: {clean_text(row['decision_reason'])}",
            [row_ref(ROUND9_RAW, row["candidate_id"])],
            ["ROUND9"],
        )
    assessment_rows = indexes["assessments"].get(label, [])
    if assessment_rows:
        return (
            "Round 14 association evidence did not establish product-vocabulary "
            "activation: "
            + " ".join(unique_sorted(row["decisionReason"] for row in assessment_rows)),
            [row_ref(ROUND14_ASSESSMENTS, row["assessmentId"]) for row in assessment_rows],
            ["ROUND14"],
        )
    raise ValueError(f"No governed prior-round disposition basis for {label}")


def research_gate(reason: str) -> str:
    upper = reason.upper()
    if "SINGLE_ATTESTATION" in upper or "ADDITIONAL_EVIDENCE" in upper:
        return "Obtain independent, verified design-history attestation and repeat semantic review."
    if "AMBIGUITY" in upper or "SPLIT_REQUIRED" in upper or "SPLIT" in upper:
        return "Split competing senses and independently attest each bounded sense."
    if "TOO_BROAD" in upper or "HIGH_CONNECTIVITY" in upper:
        return "Demonstrate a bounded non-universal role with explicit scope-out and argument roles."
    if "STRUCTURAL_ANNOTATION" in upper:
        return "Retain as a contested structural annotation unless a non-universal node role is proven."
    if "DEFER_TRANSLATION" in upper:
        return "Verify the original-language noun and an independent published translation chain."
    return "Complete a new governed activation review; prior passage to research is not product activation."


def build_records(
    candidates: list[dict[str, Any]],
    indexes: dict[str, Any],
    categories: dict[str, list[str]],
    category_refs: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline = set(indexes["active"])
    active_labels = baseline | ADDED_ACTIVE_LABELS
    if len(active_labels) != EXPECTED_ACTIVE_COUNT:
        raise ValueError("Round 16 baseline plus additions must total 31 labels")
    if not ADDED_ACTIVE_LABELS.isdisjoint(baseline):
        raise ValueError("Round 16A additions unexpectedly overlap Round 16 baseline")

    records: list[dict[str, Any]] = []
    active_rows: list[dict[str, Any]] = []
    for candidate in sorted(
        candidates,
        key=lambda row: (
            normalize_label(row["canonical_label"]),
            clean_text(row["canonical_label"]),
        ),
    ):
        label = normalize_label(candidate["canonical_label"])
        if label in active_labels:
            disposition = "ACTIVE"
        elif label in MERGED_LABEL_TO_TARGET:
            disposition = "MERGED_SUPERSEDED"
        elif label in ROUND14_FAILED_ONLY_CONTROLS or label in ROUND9_REJECTED_LABELS:
            disposition = "REJECTED"
        else:
            disposition = "RESEARCH_ONLY"

        reason, decision_refs, rounds = governed_decision(
            indexes, label, disposition
        )
        merge_target = MERGED_LABEL_TO_TARGET.get(label, "")
        active_id = active_vocabulary_id(indexes, label) if disposition == "ACTIVE" else ""
        source_attestations: list[str] = []
        academic_support: list[str] = []
        sense = ""
        scope = ""
        ambiguity = ""
        category_ids: list[str] = []
        binding_refs: list[str] = []
        if disposition == "ACTIVE":
            source_attestations, academic_support = active_support(
                candidate, indexes, label
            )
            sense = bounded_sense(indexes, label)
            scope = scope_note(indexes, label)
            ambiguity = ambiguity_note(indexes, label)
            category_ids = categories.get(label, [])
            binding_refs = category_refs.get(label, [])
            if not category_ids or not set(category_ids) <= set(EXPECTED_CATEGORY_IDS):
                raise ValueError(f"Active term lacks governed category binding: {label}")
            active_rows.append({
                "vocabulary_id": active_id,
                "canonical_label": clean_text(candidate["canonical_label"]),
                "normalized_label": label,
                "category_ids": category_ids,
                "bounded_sense": sense,
                "scope_note": scope,
                "ambiguity_note": ambiguity,
                "source_attestations": source_attestations,
                "academic_support": academic_support,
            })

        records.append({
            "vocabulary_candidate_id": candidate["vocabulary_candidate_id"],
            "vocabulary_id": active_id,
            "canonical_label": clean_text(candidate["canonical_label"]),
            "normalized_label": label,
            "disposition": disposition,
            "status": DISPOSITION_TO_STATUS[disposition],
            "merge_target_label": merge_target,
            "merge_target_vocabulary_id": (
                active_vocabulary_id(indexes, merge_target) if merge_target else ""
            ),
            "category_ids": category_ids,
            "category_binding_refs": safe_references(binding_refs),
            "bounded_sense": sense,
            "scope_note": scope,
            "ambiguity_note": ambiguity,
            "source_attestations": source_attestations,
            "academic_support": academic_support,
            "decision_reason": reason,
            "decision_refs": safe_references(decision_refs),
            "provenance_rounds": unique_sorted(rounds),
            "governed_source_paths": unique_sorted(
                candidate.get("contributing_source_paths", [])
            ),
        })

    active_rows.sort(
        key=lambda row: (row["normalized_label"], row["canonical_label"])
    )
    if len(records) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError("Vocabulary census does not contain exactly 65 records")
    if len(active_rows) != EXPECTED_ACTIVE_COUNT:
        raise ValueError("Active vocabulary does not contain exactly 31 records")
    if len({row["normalized_label"] for row in records}) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError("Every candidate must receive exactly one disposition")
    if len({row["vocabulary_id"] for row in active_rows}) != EXPECTED_ACTIVE_COUNT:
        raise ValueError("Active vocabulary IDs are not unique")
    if {
        row["normalized_label"] for row in active_rows
    } != active_labels:
        raise ValueError("Active label set does not match the exact 31-label contract")
    if sum(row["disposition"] == "MERGED_SUPERSEDED" for row in records) != 1:
        raise ValueError("Exactly cultural adaptation must be merged/superseded")
    return records, active_rows


CENSUS_TSV_FIELDS = (
    "vocabulary_candidate_id",
    "vocabulary_id",
    "canonical_label",
    "normalized_label",
    "disposition",
    "status",
    "merge_target_label",
    "merge_target_vocabulary_id",
    "category_ids_json",
    "category_binding_refs_json",
    "bounded_sense",
    "scope_note",
    "ambiguity_note",
    "source_attestations_json",
    "academic_support_json",
    "decision_reason",
    "decision_refs_json",
    "provenance_rounds_json",
    "governed_source_paths_json",
    "universe_hash",
)


def tsv_bytes(
    rows: Sequence[dict[str, Any]],
    fields: Sequence[str],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def census_tsv(records: list[dict[str, Any]], universe_hash: str) -> bytes:
    rows = []
    for record in records:
        rows.append({
            "vocabulary_candidate_id": record["vocabulary_candidate_id"],
            "vocabulary_id": record["vocabulary_id"],
            "canonical_label": record["canonical_label"],
            "normalized_label": record["normalized_label"],
            "disposition": record["disposition"],
            "status": record["status"],
            "merge_target_label": record["merge_target_label"],
            "merge_target_vocabulary_id": record["merge_target_vocabulary_id"],
            "category_ids_json": canonical_json(record["category_ids"]),
            "category_binding_refs_json": canonical_json(record["category_binding_refs"]),
            "bounded_sense": record["bounded_sense"],
            "scope_note": record["scope_note"],
            "ambiguity_note": record["ambiguity_note"],
            "source_attestations_json": canonical_json(record["source_attestations"]),
            "academic_support_json": canonical_json(record["academic_support"]),
            "decision_reason": record["decision_reason"],
            "decision_refs_json": canonical_json(record["decision_refs"]),
            "provenance_rounds_json": canonical_json(record["provenance_rounds"]),
            "governed_source_paths_json": canonical_json(record["governed_source_paths"]),
            "universe_hash": universe_hash,
        })
    return tsv_bytes(rows, CENSUS_TSV_FIELDS)


FUTURE_TSV_FIELDS = (
    "vocabulary_candidate_id",
    "canonical_label",
    "normalized_label",
    "status",
    "governed_reason",
    "research_gate",
    "decision_refs_json",
    "provenance_rounds_json",
    "universe_hash",
)


def future_tsv(records: list[dict[str, Any]], universe_hash: str) -> bytes:
    rows = []
    for record in records:
        if record["disposition"] != "RESEARCH_ONLY":
            continue
        rows.append({
            "vocabulary_candidate_id": record["vocabulary_candidate_id"],
            "canonical_label": record["canonical_label"],
            "normalized_label": record["normalized_label"],
            "status": record["status"],
            "governed_reason": record["decision_reason"],
            "research_gate": research_gate(record["decision_reason"]),
            "decision_refs_json": canonical_json(record["decision_refs"]),
            "provenance_rounds_json": canonical_json(record["provenance_rounds"]),
            "universe_hash": universe_hash,
        })
    return tsv_bytes(rows, FUTURE_TSV_FIELDS)


def markdown_escape(value: Any) -> str:
    return clean_text(value).replace("|", "\\|")


def census_markdown(
    records: list[dict[str, Any]],
    universe_hash: str,
    active_hash: str,
    database_snapshot_value: str,
) -> bytes:
    counts = {
        disposition: sum(row["disposition"] == disposition for row in records)
        for disposition in DISPOSITION_TO_STATUS
    }
    lines = [
        "# Round 16A Vocabulary Census",
        "",
        "This census closes the frozen 65-candidate vocabulary space without "
        "reading record-level, Search, Context, or Spacetime sources.",
        "",
        f"- Universe hash: `{universe_hash}`",
        f"- Active-vocabulary hash: `{active_hash}`",
        f"- Database snapshot: `{database_snapshot_value}`",
        f"- Candidate count: {len(records)}",
        f"- Active: {counts['ACTIVE']}",
        f"- Merged/superseded: {counts['MERGED_SUPERSEDED']}",
        f"- Research-only: {counts['RESEARCH_ONLY']}",
        f"- Rejected: {counts['REJECTED']}",
        "",
        "Every candidate has exactly one disposition. Association failure is not "
        "treated as vocabulary rejection except for the seven governed Round 14 "
        "failed-only controls. Active terms expose only bounded senses and source "
        "identifiers; record identifiers and titles are prohibited.",
        "",
        "| Candidate | Disposition | Status | Categories | Governed reason |",
        "|---|---|---|---|---|",
    ]
    for row in records:
        lines.append(
            "| "
            + " | ".join((
                markdown_escape(row["canonical_label"]),
                row["disposition"],
                row["status"],
                markdown_escape(", ".join(row["category_ids"])),
                markdown_escape(row["decision_reason"]),
            ))
            + " |"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def reconciliation_markdown(
    records: list[dict[str, Any]],
    universe_hash: str,
) -> bytes:
    merged = [row for row in records if row["disposition"] == "MERGED_SUPERSEDED"]
    rejected = [row for row in records if row["disposition"] == "REJECTED"]
    research = [row for row in records if row["disposition"] == "RESEARCH_ONLY"]
    additions = [
        row for row in records if row["normalized_label"] in ADDED_ACTIVE_LABELS
    ]
    lines = [
        "# Round 16A Vocabulary Disposition Reconciliation",
        "",
        f"Frozen universe: `{universe_hash}`.",
        "",
        "## Active additions",
        "",
        "The current 26-label Round 16 active audit is preserved. These five "
        "bounded governed candidates are added, producing exactly 31 active labels.",
        "",
        "| Label | Category bindings | Decision basis |",
        "|---|---|---|",
    ]
    for row in additions:
        lines.append(
            f"| {markdown_escape(row['canonical_label'])} | "
            f"{markdown_escape(', '.join(row['category_ids']))} | "
            f"{markdown_escape(row['decision_reason'])} |"
        )
    lines.extend([
        "",
        "## Merge reconciliation",
        "",
        "| Candidate | Canonical target | Reason |",
        "|---|---|---|",
    ])
    for row in merged:
        lines.append(
            f"| {markdown_escape(row['canonical_label'])} | "
            f"{markdown_escape(row['merge_target_label'])} | "
            f"{markdown_escape(row['decision_reason'])} |"
        )
    lines.extend([
        "",
        "## Governed rejections",
        "",
        "Rejections comprise explicit Round 9 term rejections and Round 14 "
        "failed-only controls. A failed association involving an otherwise "
        "governed term does not reject that term.",
        "",
        "| Candidate | Reason |",
        "|---|---|",
    ])
    for row in rejected:
        lines.append(
            f"| {markdown_escape(row['canonical_label'])} | "
            f"{markdown_escape(row['decision_reason'])} |"
        )
    lines.extend([
        "",
        "## Research-only candidates",
        "",
        "These labels retain prior-round evidence and decisions but are not "
        "user-visible vocabulary. Future work must satisfy the recorded gate.",
        "",
        "| Candidate | Prior decision | Future gate |",
        "|---|---|---|",
    ])
    for row in research:
        lines.append(
            f"| {markdown_escape(row['canonical_label'])} | "
            f"{markdown_escape(row['decision_reason'])} | "
            f"{markdown_escape(research_gate(row['decision_reason']))} |"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo: Path) -> dict[Path, bytes]:
    universe = read_json(repo, CANDIDATE_UNIVERSE)
    if not isinstance(universe, dict):
        raise ValueError("Malformed vocabulary candidate universe")
    candidates = verify_universe(repo, universe)
    indexes = build_indexes(repo)
    baseline_labels = set(indexes["active"])
    categories, category_refs = build_category_bindings(repo, baseline_labels)
    snapshot = database_snapshot(repo)
    records, active_rows = build_records(
        candidates, indexes, categories, category_refs
    )
    universe_hash = universe["universe_canonical_hash"]

    active_hash = canonical_hash(active_rows)
    active_contract = {
        "active_vocabulary": active_rows,
        "active_vocabulary_count": EXPECTED_ACTIVE_COUNT,
        "universe_hash": universe_hash,
        "active_vocabulary_hash": active_hash,
        "database_snapshot": snapshot,
    }
    if set(active_contract) != {
        "active_vocabulary",
        "active_vocabulary_count",
        "universe_hash",
        "active_vocabulary_hash",
        "database_snapshot",
    }:
        raise AssertionError("Active-vocabulary top-level contract changed")
    required_active_fields = {
        "vocabulary_id",
        "canonical_label",
        "normalized_label",
        "category_ids",
        "bounded_sense",
        "scope_note",
        "ambiguity_note",
        "source_attestations",
        "academic_support",
    }
    for row in active_rows:
        if set(row) != required_active_fields:
            raise AssertionError(
                f"Active-vocabulary row contract changed for {row.get('canonical_label')}"
            )
        for field in (
            "vocabulary_id",
            "canonical_label",
            "normalized_label",
            "bounded_sense",
            "scope_note",
            "ambiguity_note",
        ):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(
                    f"Active-vocabulary field {field} is empty for "
                    f"{row.get('canonical_label')}"
                )
        for field in ("category_ids", "source_attestations", "academic_support"):
            if not isinstance(row[field], list) or not row[field]:
                raise ValueError(
                    f"Active-vocabulary list {field} is empty for "
                    f"{row.get('canonical_label')}"
                )

    census_tsv_content = census_tsv(records, universe_hash)
    future_tsv_content = future_tsv(records, universe_hash)
    active_json_content = json_bytes(active_contract)
    census_note_content = census_markdown(
        records, universe_hash, active_hash, snapshot
    )
    reconciliation_note_content = reconciliation_markdown(records, universe_hash)

    disposition_counts = {
        disposition: sum(row["disposition"] == disposition for row in records)
        for disposition in DISPOSITION_TO_STATUS
    }
    input_manifest = build_input_manifest(repo, universe)
    census_document = {
        "format": FORMAT,
        "version": VERSION,
        "frozen": True,
        "candidate_count": len(records),
        "active_vocabulary_count": len(active_rows),
        "future_vocabulary_candidate_count": disposition_counts["RESEARCH_ONLY"],
        "disposition_counts": disposition_counts,
        "universe_hash": universe_hash,
        "vocabulary_census_hash": canonical_hash(records),
        "active_vocabulary_hash": active_hash,
        "database_snapshot": snapshot,
        "input_artifacts": input_manifest,
        "disposition_policy": {
            "active": (
                "Exact Round 16 26-label active audit plus canonization, "
                "self-exoticization, cultural transfer, cultural transformation, "
                "and mobile object."
            ),
            "merged_superseded": "cultural adaptation merges into adaptation.",
            "rejected": (
                "Explicit Round 9 rejections and seven Round 14 failed-only controls."
            ),
            "research_only": (
                "All remaining governed candidates retain their most recent "
                "prior-round decision without product activation."
            ),
        },
        "scope_boundary": {
            "archive_record_dependency_count": 0,
            "search_dependency_count": 0,
            "context_dependency_count": 0,
            "spacetime_dependency_count": 0,
            "association_failure_is_term_rejection": False,
        },
        "output_hashes": {
            OUTPUT_PATHS["census_tsv"].as_posix(): sha256_bytes(census_tsv_content),
            OUTPUT_PATHS["future_tsv"].as_posix(): sha256_bytes(future_tsv_content),
            OUTPUT_PATHS["active_json"].as_posix(): sha256_bytes(active_json_content),
            OUTPUT_PATHS["census_note"].as_posix(): sha256_bytes(census_note_content),
            OUTPUT_PATHS["reconciliation_note"].as_posix(): sha256_bytes(
                reconciliation_note_content
            ),
        },
        "candidates": records,
        "status": "PASS",
    }
    census_json_content = json_bytes(census_document)

    # Validate structured artifacts and their rendered text before returning any
    # bytes to the writer.  This catches prohibited keys, refs, and identifiers.
    assert_safe_output(active_contract)
    assert_safe_output(census_document)
    for name, content in {
        "census_tsv": census_tsv_content,
        "future_tsv": future_tsv_content,
        "census_note": census_note_content,
        "reconciliation_note": reconciliation_note_content,
    }.items():
        assert_safe_output(content.decode("utf-8"), f"$.{name}")

    return {
        OUTPUT_PATHS["census_tsv"]: census_tsv_content,
        OUTPUT_PATHS["census_json"]: census_json_content,
        OUTPUT_PATHS["future_tsv"]: future_tsv_content,
        OUTPUT_PATHS["active_json"]: active_json_content,
        OUTPUT_PATHS["census_note"]: census_note_content,
        OUTPUT_PATHS["reconciliation_note"]: reconciliation_note_content,
    }


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare deterministic bytes with existing artifacts without writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    outputs = build_outputs(repo)
    if args.check:
        mismatches = [
            relative.as_posix()
            for relative, expected in outputs.items()
            if not (repo / relative).is_file()
            or (repo / relative).read_bytes() != expected
        ]
        if mismatches:
            raise SystemExit(
                "Deterministic output mismatch: " + ", ".join(mismatches)
            )
    else:
        for relative, content in outputs.items():
            atomic_write(repo / relative, content)
    print(canonical_json({
        "status": "PASS" if args.check else "GENERATED",
        "candidate_count": EXPECTED_CANDIDATE_COUNT,
        "active_vocabulary_count": EXPECTED_ACTIVE_COUNT,
        "outputs": [
            {
                "path": relative.as_posix(),
                "bytes": len(content),
                "sha256": sha256_bytes(content),
            }
            for relative, content in sorted(
                outputs.items(), key=lambda item: item[0].as_posix()
            )
        ],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
