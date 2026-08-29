#!/usr/bin/env python3
"""Independently verify Checkpoint 012's evidence-bounded non-closure audit.

This stdlib-only implementation does not import, invoke, or reuse the primary
builder's enumeration.  It reconstructs the governed source universe directly
from committed Round 16B inputs, checks every primary row and byte seal, runs
fail-closed corruption probes, and owns the independent receipt and report.
"""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW_REL = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
RESEARCH_REL = "docs/research/trace-v49-exploration-higher-order-association-closure-round16b"

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
AUTHORITY_BASE_SHA = "11412d23e309a647a3a2fb0b3db4369dcdd15993"
AUTHORITY_BASE_TREE = "9117d6fc189b8c8a986f6ba26e6879184d58eb12"
EXPECTED_ORIGIN_MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
WORK_BRANCH = "codex/trace-v49-exploration-higher-order-association-closure-round16b"
VERIFIER_VERSION = "trace-round16b-recursive-gap-closure-audit-independent-verifier-v2"

PRIMARY_BUILDER_PATH = "scripts/trace_round16b/build_recursive_gap_closure_audit.py"
INPUT_MANIFEST_PATH = f"{RAW_REL}/recursive-gap-input-manifest-checkpoint012-v1.tsv"
SUPERSESSION_PATH = f"{RAW_REL}/recursive-gap-supersession-ledger-checkpoint012-v1.tsv"
OBLIGATION_PATH = f"{RAW_REL}/recursive-gap-current-obligation-ledger-checkpoint012-v1.tsv"
METRICS_PATH = f"{RAW_REL}/recursive-gap-closure-metrics-checkpoint012-v1.json"
BUILD_RECEIPT_PATH = f"{RAW_REL}/recursive-gap-closure-build-receipt-checkpoint012-v1.json"
INDEPENDENT_RECEIPT_PATH = f"{RAW_REL}/recursive-gap-closure-independent-verification-checkpoint012-v1.json"
REPORT_PATH = f"{RESEARCH_REL}/23_RECURSIVE_GAP_AUDIT_AND_CLOSURE_DECISION.md"

GAP_PATHS = (
    f"{RAW_REL}/recursive-gap-ledger.tsv",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint003-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint004-v2.tsv",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint005-tranche-a-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint006-tranche-b-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint007-tranche-c-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint008-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-adaptive-source-shard-1-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-adaptive-source-shard-2-v1.tsv",
    f"{RAW_REL}/recursive-gap-ledger-round16a-global-reconciliation-v1.tsv",
)
ASSOCIATION_QUEUE_PATHS = (
    f"{RAW_REL}/conditional-scoped-child-reroute-queue-tranche-a-v1.tsv",
    f"{RAW_REL}/conditional-scoped-child-reroute-queue-tranche-b-v1.tsv",
    f"{RAW_REL}/scoped-higher-order-review-queue-tranche-c-v1.tsv",
)
RIGHTS_QUEUE_PATH = f"{RAW_REL}/source-canonical-rights-queue-v2.tsv"
PARTICIPANT_PATH = f"{RAW_REL}/open-participant-resolution-ledger-v1.tsv"
PARAMETER_PATH = f"{RAW_REL}/parameter-reconciliation-ledger-v2.tsv"
METADATA_PATH = f"{RAW_REL}/metadata-search-lead-ledger-v2.tsv"
EXTERNAL_REVIEW_PATH = (
    "docs/research/trace-v49-exploration-composition-review-round1/"
    "16_EXTERNAL_DOMAIN_REVIEW_REGISTRY.tsv"
)
CROSSWALK_PATH = f"{RAW_REL}/concept-sense-crosswalk-v1.tsv"
TRIGGER_PATH = f"{RAW_REL}/candidate-trigger-occurrence-ledger-v2.tsv"
EXCLUSION_PATH = f"{RAW_REL}/candidate-exclusion-ledger.tsv"
ASSOCIATION_EVIDENCE_PATH = f"{RAW_REL}/association-evidence-ledger.tsv"
HYPOTHESIS_PATHS = (
    f"{RAW_REL}/scoped-association-hypothesis-ledger-shard-1-v1.tsv",
    f"{RAW_REL}/scoped-association-hypothesis-ledger-shard-2-v1.tsv",
)
RIGHTS_REVIEW_PATHS = (
    f"{RAW_REL}/source-rights-ledger-shard-1-v1.tsv",
    f"{RAW_REL}/source-rights-ledger-shard-2-v2.tsv",
)
ISOLATED_PATH = f"{RAW_REL}/isolated-active-term-audit-ledger-v1.tsv"
VOCAB_IMPACT_PATH = f"{RAW_REL}/active-vocabulary-evidence-impact-ledger-shard-2-v1.tsv"
LOCAL_FAMILY_PATH = f"{RAW_REL}/local-candidate-family-ledger-v2.tsv"
R16A_SUBGRAPH_PATH = f"{RAW_REL}/round16a-global-reconciliation-subgraphs-v1.tsv"
R16A_CENSUS_PATH = f"{RAW_REL}/round16a-global-reconciliation-census-v1.json"
V3_CENSUS_PATH = f"{RAW_REL}/v3-semantic-contract-census-v1.json"
V3_RUNTIME_PATH = f"{RAW_REL}/v3-runtime-independent-verification-v1.json"
V50_REPLAY_PATH = f"{RAW_REL}/v50-round16b-replay-receipt-checkpoint011.json"
CP11_RECEIPT_PATH = f"{RAW_REL}/v50-v3-runtime-checkpoint011-receipt.json"
DB_MANIFEST_PATH = "database/schema-manifest-v50-round16b.json"

EXPECTED_INPUT_PATHS = frozenset((
    *GAP_PATHS,
    *ASSOCIATION_QUEUE_PATHS,
    RIGHTS_QUEUE_PATH,
    PARTICIPANT_PATH,
    PARAMETER_PATH,
    METADATA_PATH,
    EXTERNAL_REVIEW_PATH,
    CROSSWALK_PATH,
    TRIGGER_PATH,
    EXCLUSION_PATH,
    ASSOCIATION_EVIDENCE_PATH,
    *HYPOTHESIS_PATHS,
    *RIGHTS_REVIEW_PATHS,
    ISOLATED_PATH,
    VOCAB_IMPACT_PATH,
    LOCAL_FAMILY_PATH,
    R16A_SUBGRAPH_PATH,
    R16A_CENSUS_PATH,
    V3_CENSUS_PATH,
    V3_RUNTIME_PATH,
    V50_REPLAY_PATH,
    CP11_RECEIPT_PATH,
    DB_MANIFEST_PATH,
))

# Recomputed from the committed Checkpoint 011 bytes before this verifier was
# written.  These remain Checkpoint 011 capability inputs, not mutable working
# directory claims.
PINNED_CP11_SHA256 = {
    V3_CENSUS_PATH: "7df89f2248d169c1f4e6358425a7f01afbcdb27c02d1d0e3f583f35c67322c6e",
    V50_REPLAY_PATH: "7034cf1474d1baeec36d09033f28e35ae2d58f754009ebe194f5a9102725b83b",
    CP11_RECEIPT_PATH: "b7b2e0560823071129cb4c3cc6afa71275f76df7c189962ab36265ef3fc9861b",
}
PINNED_CHECKPOINT012_CORRECTED_SHA256 = {
    R16A_CENSUS_PATH: "f2196eef23c560e24fd373956af6e711687440203edc4e0c96ab5de90c8c4537",
    V3_RUNTIME_PATH: "4839c5bf5492762478e1562c203db0dffc4b62886e1689f6eb7d37e3af2c0c38",
}
PINNED_CHECKPOINT015_CORRECTED_SHA256 = {
    DB_MANIFEST_PATH: "5f11af95c21417846cd6a71b92173c2d265d5389365fcce08d8c1b7d5b456433",
}

CLOSURE_KEYS = (
    "pair_association_closure",
    "higher_order_association_closure",
    "global_composition_coherence_closure",
    "product_association_reachability_closure",
    "computational_space_closure",
    "function3_closure",
)

OBLIGATION_IDS = {
    "candidate": "R16B-CURRENT-OBLIGATION:CANDIDATE_UNIVERSE_AND_EXCLUSION_PROOF",
    "nary": "R16B-CURRENT-OBLIGATION:NARY_PARTICIPANT_RESOLUTION",
    "rights": "R16B-CURRENT-OBLIGATION:RIGHTS_AND_LAWFUL_TEXT",
    "metadata": "R16B-CURRENT-OBLIGATION:METADATA_TO_TEXT_REVIEW",
    "human": "R16B-CURRENT-OBLIGATION:EXTERNAL_HUMAN_AUTHORITY",
    "scope": "R16B-CURRENT-OBLIGATION:SCOPE_SENSE_AND_IDENTITY",
    "group": "R16B-CURRENT-OBLIGATION:GLOBAL_GROUP_COHERENCE",
    "cultural": "R16B-CURRENT-OBLIGATION:CULTURAL_TRANSFORMATION_REAUDIT",
    "vocab": "R16B-CURRENT-OBLIGATION:ACTIVE_VOCABULARY_REACHABILITY",
    "bound": "R16B-CURRENT-OBLIGATION:SEMANTIC_AND_PRODUCT_ARITY_BOUND",
    "r16a": "R16B-CURRENT-OBLIGATION:ROUND16A_SEMANTIC_RECONCILIATION",
    "product": "R16B-CURRENT-OBLIGATION:PRODUCTION_POPULATION_AND_REACHABILITY",
    "pair": "R16B-CURRENT-OBLIGATION:PAIR_ASSOCIATION_REAUDIT",
    "payload": "R16B-CURRENT-OBLIGATION:SOURCE_BYTE_REPRODUCIBILITY",
    "repro": "R16B-CURRENT-OBLIGATION:FINAL_CLEAN_REPRODUCTION_GATE",
    "queue": "R16B-CURRENT-OBLIGATION:OPEN_ASSOCIATION_REVIEW_QUEUE",
}

EXPECTED_SET_HASHES = {
    "supersession": "3324de09faab9a1362e2eac97293298a2b9e8d06808f6741df76815f66882497",
    "hypotheses": "4dde1a4d5ae3cc5facc407bfaafc1813581b14d5f3c9382a119de93584360118",
    "ungoverned": "99437d954b3e02621ba1846f50b828373cbfd195d0c6386a45d095ed8010f9d4",
    "governed": "c61d2dda5b1237cfdb5748d34361d9631a2c79b23c98a1261222b86a4ab6f007",
    "governed_hypotheses": "53308df373dfe229f34f82a80fdc5d9ba2fbe1c1bdcfcb04abf4bfae9a1a21e7",
    "nary": "027745b18d40dfe7f186d9d3774b3d20cf6bde72fcdbdecfe3aceaa900474077",
    "uncovered_research": "d1b846638f45b1fbf4587c60ad71a6e9ecd285d1fa0d498c6615783bf86b4fb4",
    "vocab": "4f150b6d2e551e305d7810321bd260096ff52bab29bd8c93d148d114481073c2",
    "parameters": "73b91c15b7aa08ebfea18fd2b06a5130c09d77713c9e679aeee354684f121eb9",
    "rights_open": "dd257baf10240263b03216da4729752458c854585e11344ad965af9aac909e45",
    "metadata_open": "a0a6fa675ead9c98e56c52f387a2468876960b25fe65885f6ceaaf284309a0bd",
    "human": "303ab3c6bd4e17a27c697d62211d2dce6b01a0acd4ea1fa1eb8a4f8da1be5357",
    "queue_all": "46ae8c3ba4395d99d04e9bd3a9d9118e0cbdfd9cadbf3786bb684b99d0278d54",
    "queue_terminal": "fc5c97257691144de308f695e595248ab80dfdd941c83b7320112a9290968b11",
    "queue_derivative": "d0cba564ad24365cdbba049f205aa87f5ee624faa8da3c6c3739d2c29472eb86",
    "queue_open": "fc1497ae93a4da880c0d919b4c174bc15bb7aebb3fc22f364a7a41174a67c1dd",
}

EXPECTED_PRIOR_KIND_DISTRIBUTION = {
    "ASSOCIATION_REVIEW_QUEUE": 59,
    "EXTERNAL_HUMAN_REVIEW_OBLIGATION": 36,
    "GAP": 105,
    "METADATA_LEAD_OBLIGATION": 101,
    "NARY_PARTICIPANT_OBLIGATION": 10,
    "SEMANTIC_PARAMETER_OBLIGATION": 9,
    "SOURCE_RIGHTS_QUEUE": 94,
}
EXPECTED_DISPOSITION_DISTRIBUTION = {
    "PARTIALLY_RECONCILED_REMAINDER_OPEN": 44,
    "PRESERVED_HISTORICAL_LIMITATION": 2,
    "PRESERVED_TERMINAL_CONTROL": 25,
    "RESOLVED_BY_COMMITTED_ARTIFACT": 22,
    "SUPERSEDED_BY_OPEN_OBLIGATION": 321,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(relative: str | Path) -> str:
    path = relative if isinstance(relative, Path) else REPO / relative
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_set_hash(values: Iterable[str]) -> str:
    return sha256_bytes("".join(f"{value}\n" for value in sorted(set(values))).encode("utf-8"))


def normalize_identifier(value: str) -> str:
    normalized = value.strip().casefold()
    for prefix in (
        "https://doi.org/", "http://doi.org/",
        "https://dx.doi.org/", "http://dx.doi.org/", "doi:",
    ):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    return normalized.strip()


def row_hash(row: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(row).encode("utf-8"))


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect="excel-tab")
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"missing or duplicate TSV fields: {relative}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"malformed TSV row: {relative}")
    return rows


def read_json(relative: str) -> Any:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key in {relative}: {key}")
            result[key] = value
        return result

    return json.loads((REPO / relative).read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def parse_string_array(value: str, context: str) -> list[str]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(f"not a string-array JSON value: {context}")
    return parsed


def require(actual: Any, expected: Any, name: str) -> None:
    if actual != expected:
        raise ValueError(f"{name}: observed={actual!r}; expected={expected!r}")


def source_record_hash(row: dict[str, str]) -> str:
    existing = row.get("record_sha256", "")
    if len(existing) == 64 and all(character in "0123456789abcdef" for character in existing):
        return existing
    return row_hash(row)


def independent_status_projection(row: dict[str, str]) -> str:
    statuses = {
        name: value for name, value in sorted(row.items())
        if (name == "status" or name.endswith("_status")) and value
    }
    if not statuses:
        statuses = {"status": "UNSPECIFIED"}
    return canonical_json(statuses)


def verify_implementation_separation() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")
    banned = {
        "build_recursive_gap_closure_audit", "importlib", "runpy", "subprocess",
    }
    if any(module.split(".")[-1] in banned for module in imported_modules):
        raise ValueError("independent verifier imports a builder/invocation facility")
    return {
        "primary_builder_path": PRIMARY_BUILDER_PATH,
        "independent_verifier_path": str(Path(__file__).resolve().relative_to(REPO)),
        "primary_builder_sha256": sha256_file(PRIMARY_BUILDER_PATH),
        "independent_verifier_sha256": sha256_file(Path(__file__)),
        "imports_primary_builder": False,
        "invokes_primary_builder": False,
        "reuses_primary_enumeration_module": False,
        "stdlib_only": True,
    }


def record_count(relative: str) -> int:
    return len(read_tsv(relative)) if relative.endswith(".tsv") else 1


def expected_manifest_authority(relative: str) -> str:
    if relative == R16A_CENSUS_PATH:
        return "CHECKPOINT012_CORRECTED_ROUND16A_RECONCILIATION_BYTES"
    if relative == V3_RUNTIME_PATH:
        return "CHECKPOINT012_REFRESHED_RUNTIME_VERIFICATION_BYTES"
    if relative == DB_MANIFEST_PATH:
        return "CHECKPOINT015_V50_MANIFEST_PORTABILITY_CORRECTION_BYTES"
    if relative in PINNED_CP11_SHA256:
        return "COMMITTED_CHECKPOINT011_BYTES"
    return "COMMITTED_ROUND16B_PRE_CHECKPOINT011_BYTES"


def validate_manifest_authorities(rows: list[dict[str, str]]) -> None:
    require(len(rows), 36, "manifest authority specimen row count")
    for row in rows:
        require(
            row["authority_boundary"], expected_manifest_authority(row["path"]),
            f"manifest authority boundary {row['path']}",
        )


def verify_input_manifest() -> dict[str, Any]:
    rows = read_tsv(INPUT_MANIFEST_PATH)
    require(len(EXPECTED_INPUT_PATHS), 36, "verifier expected-input path count")
    require(len(rows), 36, "primary input-manifest row count")
    require({row["path"] for row in rows}, EXPECTED_INPUT_PATHS, "primary input-manifest path set")
    require([row["path"] for row in rows], sorted(EXPECTED_INPUT_PATHS), "input-manifest sort order")
    require([int(row["ordinal"]) for row in rows], list(range(1, 37)), "input-manifest ordinals")
    validate_manifest_authorities(rows)
    for row in rows:
        relative = row["path"]
        path = REPO / relative
        require(path.is_file(), True, f"manifest input exists {relative}")
        require(int(row["bytes"]), path.stat().st_size, f"manifest byte count {relative}")
        require(int(row["record_count"]), record_count(relative), f"manifest record count {relative}")
        require(row["sha256"], sha256_file(relative), f"manifest SHA-256 {relative}")
        selector = "ALL_TSV_ROWS" if relative.endswith(".tsv") else "WHOLE_JSON_DOCUMENT"
        require(row["selector"], selector, f"manifest selector {relative}")
    for relative, expected in PINNED_CP11_SHA256.items():
        require(sha256_file(relative), expected, f"committed Checkpoint 011 trust anchor {relative}")
    for relative, expected in PINNED_CHECKPOINT012_CORRECTED_SHA256.items():
        require(sha256_file(relative), expected, f"Checkpoint 012 corrected trust anchor {relative}")
    for relative, expected in PINNED_CHECKPOINT015_CORRECTED_SHA256.items():
        require(sha256_file(relative), expected, f"Checkpoint 015 corrected trust anchor {relative}")
    return {
        "record_count": len(rows),
        "path_set_sha256": id_set_hash(EXPECTED_INPUT_PATHS),
        "manifest_sha256": sha256_file(INPUT_MANIFEST_PATH),
        "checkpoint011_pinned_artifact_count": len(PINNED_CP11_SHA256),
        "checkpoint011_pinned_artifact_sha256": dict(sorted(PINNED_CP11_SHA256.items())),
        "checkpoint012_corrected_artifact_count": len(PINNED_CHECKPOINT012_CORRECTED_SHA256),
        "checkpoint012_corrected_artifact_sha256": dict(
            sorted(PINNED_CHECKPOINT012_CORRECTED_SHA256.items())
        ),
        "checkpoint015_corrected_artifact_count": len(PINNED_CHECKPOINT015_CORRECTED_SHA256),
        "checkpoint015_corrected_artifact_sha256": dict(
            sorted(PINNED_CHECKPOINT015_CORRECTED_SHA256.items())
        ),
    }


def collect_hypotheses() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in HYPOTHESIS_PATHS:
        for row in read_tsv(relative):
            product_eligible = row.get("product_eligible")
            if product_eligible is None:
                product_eligible = (
                    "true" if row.get("product_eligibility", "").startswith("ELIGIBLE")
                    else "false"
                )
            records.append({
                "source_path": relative,
                "hypothesis_id": row["hypothesis_id"],
                "association_id": row.get("governed_association_id") or row.get("association_id", ""),
                "association_revision_id": (
                    row.get("governed_association_revision_id")
                    or row.get("association_revision_id", "")
                ),
                "arity": int(row["arity"]),
                "participants": parse_string_array(
                    row["participant_sense_ids_json"], f"{relative}:{row['hypothesis_id']}",
                ),
                "activation": row.get("association_activation_status") or row["activation_status"],
                "human_review": row["external_human_review_status"],
                "active_fact_created": row.get("active_fact_created", "false"),
                "product_eligible": product_eligible,
                "pair_projection_count": int(
                    row.get("pair_projection_count") or row["implicit_pair_projection_count"]
                ),
            })
    ids = [row["hypothesis_id"] for row in records]
    require(len(records), 11, "current scoped hypothesis count")
    require(len(set(ids)), 11, "current scoped hypothesis identity uniqueness")
    if any(bool(row["association_id"]) != bool(row["association_revision_id"]) for row in records):
        raise ValueError("a hypothesis has an association identity without its revision, or vice versa")
    if any(
        len(row["participants"]) != row["arity"]
        or len(set(row["participants"])) != row["arity"]
        for row in records
    ):
        raise ValueError("a hypothesis participant array violates declared arity or uniqueness")
    if any(row["activation"] not in {"INACTIVE", "INQUIRY_ONLY"} for row in records):
        raise ValueError("a current hypothesis is active")
    if any(row["human_review"] not in {"OPEN", "PENDING_NOT_ACTIVE"} for row in records):
        raise ValueError("a current hypothesis lacks an open human-review boundary")
    if any(row["active_fact_created"] != "false" for row in records):
        raise ValueError("a current hypothesis created an active fact")
    if any(row["product_eligible"] != "false" for row in records):
        raise ValueError("a current hypothesis is product eligible")
    if any(row["pair_projection_count"] != 0 for row in records):
        raise ValueError("a current hypothesis projects an implicit pair")
    return records


def independent_rights_text_completion(row: dict[str, str], relative: str) -> bool:
    """Independent conservative oracle for a rights/text completion record."""
    access = row.get("access_status", "")
    status_values = [
        value for key, value in row.items()
        if (key == "status" or key.endswith("_status")) and value
    ]
    status_text = "|".join(status_values)
    forbidden = (
        "ABSTRACT_ONLY", "ABSTRACT_REVIEWED", "FULL_TEXT_OPEN",
        "FULL_TEXT_NOT_ESTABLISHED", "NOT_REVIEWED",
    )
    if any(marker in status_text for marker in forbidden):
        return False

    if relative == RIGHTS_REVIEW_PATHS[0]:
        access_to_review_statuses = {
            "PUBLIC_ACCEPTED_MANUSCRIPT_REVIEWED": {
                "ACCEPTED_MANUSCRIPT_MULTI_LOCUS_REVIEWED",
            },
            "PUBLIC_PUBLISHED_FULL_TEXT_REVIEWED": {
                "PUBLISHED_TEXT_LOCATOR_REVIEWED",
            },
            "OPEN_ACCESS_PUBLISHED_FULL_TEXT_REVIEWED": {
                "PUBLISHED_TEXT_MULTI_SECTION_REVIEWED",
            },
            "PUBLIC_AUTHOR_PDF_LAWFUL_READ_OBSERVED": {
                "AUTHOR_PDF_ARTICLE_METHOD_AND_CASE_STRUCTURE_REVIEWED",
            },
            "OPEN_ACCESS_PUBLISHED_PDF_REVIEWED": {
                "PUBLISHED_TEXT_MULTI_LOCUS_REVIEWED",
                "PUBLISHED_TEXT_EXACT_GROUP_LOCATOR_REVIEWED",
            },
            "PUBLISHER_FREE_ACCESS_FULL_TEXT_REVIEWED": {
                "PUBLISHED_TEXT_LOCATOR_REVIEWED",
            },
        }
        if row.get("source_text_review_status") not in access_to_review_statuses.get(access, set()):
            return False
        record_locators = parse_string_array(
            row.get("record_urls_json", "[]"), f"{relative}:{row.get('source_id')}:records",
        )
        text_locators = parse_string_array(
            row.get("text_urls_json", "[]"), f"{relative}:{row.get('source_id')}:texts",
        )
        locators = [*record_locators, *text_locators]
        return bool(
            record_locators
            and text_locators
            and all(value.startswith(("https://", "http://")) and " " not in value for value in locators)
            and row.get("rights_record_id")
            and row.get("rights_status")
            and row.get("payload_retained") == "false"
            and row.get("retention_decision")
            == "RETAIN_BIBLIOGRAPHIC_IDENTITY_URLS_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY"
            and row.get("redistribution_authorized")
            in {"false_or_not_established", "true_with_license_conditions"}
            and row.get("committed_material")
            == "NO_REMOTE_FULL_TEXT; NO_COPYRIGHTED_PAYLOAD; NO_EXTENDED_EXTRACT"
        )

    if relative == RIGHTS_REVIEW_PATHS[1]:
        locator = row.get("retained_path_or_locator", "")
        locator_lower = locator.lower()
        return bool(
            access in {
                "PUBLIC_PUBLISHER_FULL_TEXT_REVIEWED",
                "OPEN_ACCESS_PUBLISHER_FULL_TEXT_REVIEWED",
            }
            and row.get("review_status") == "COMPLETE_FAIL_CLOSED"
            and row.get("stable_url", "").startswith(("https://", "http://"))
            and locator
            and any(marker in locator_lower for marker in ("pdf", "html"))
            and "abstract only" not in locator_lower
            and row.get("access_condition")
            and row.get("license_identifier")
            and row.get("copyright_or_rights_holder")
            and row.get("retained_material_type")
            == "BIBLIOGRAPHIC_IDENTITY_STABLE_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY"
            and row.get("retained_sha256") == "NOT_APPLICABLE_NO_SOURCE_PAYLOAD_RETAINED"
            and row.get("extract_word_count") == "0"
            and row.get("redistribution_authorized")
            in {"false", "true_with_attribution_conditions"}
            and row.get("rights_record_id")
        )

    raise ValueError(f"unknown source-review schema: {relative}")


def collect_source_reviews() -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for relative in RIGHTS_REVIEW_PATHS:
        for row in read_tsv(relative):
            reviews.append({
                "source_path": relative,
                "source_id": row["source_id"],
                "rights_record_id": row["rights_record_id"],
                "identifier": normalize_identifier(
                    row.get("doi") or row.get("doi_or_identifier") or ""
                ),
                "access_status": row.get("access_status", ""),
                "text_review_status": (
                    row.get("source_text_review_status")
                    or row.get("review_status", "")
                ),
                "rights_text_completion_eligible": independent_rights_text_completion(
                    row, relative,
                ),
                "raw": row,
            })
    require(len(reviews), 12, "source-review record count")
    require(len({row["source_id"] for row in reviews}), 12, "source-review source uniqueness")
    eligible = sorted(
        row["source_id"] for row in reviews if row["rights_text_completion_eligible"]
    )
    require(len(eligible), 10, "locator-bearing rights/text completion record count")
    require(
        sorted(row["source_id"] for row in reviews if not row["rights_text_completion_eligible"]),
        ["COMP-SRC-017", "COMP-SRC-023"],
        "noncompletion review records",
    )
    return reviews


def reconcile_rights(
    queue: list[dict[str, str]], reviews: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    canonical_ids = [row["canonical_source_id"] for row in queue]
    require(len(queue), 94, "rights baseline canonical identity count")
    require(len(set(canonical_ids)), 94, "rights baseline canonical identity uniqueness")
    matched: dict[str, dict[str, Any]] = {}
    baseline_review_ids: set[str] = set()
    noncompletion_baseline_ids: set[str] = set()
    review_to_canonical: dict[str, list[str]] = {}
    for baseline in queue:
        baseline_id = baseline["canonical_source_id"]
        members = parse_string_array(baseline["member_ids_json"], f"{RIGHTS_QUEUE_PATH}:{baseline_id}")
        representative = baseline["representative_source_record_id"]
        identifier = normalize_identifier(baseline["doi_isbn_or_identifier"])
        hits = []
        for review in reviews:
            source_match = review["source_id"] == representative or any(
                member.endswith(f":{review['source_id']}") for member in members
            )
            review_identifier = normalize_identifier(review["identifier"])
            identifier_match = bool(review_identifier and review_identifier == identifier)
            if source_match or identifier_match:
                hits.append(review)
        if len(hits) > 1:
            raise ValueError(f"ambiguous rights supersession for {baseline_id}")
        if hits:
            baseline_review_ids.add(hits[0]["source_id"])
            review_to_canonical.setdefault(hits[0]["source_id"], []).append(baseline_id)
            if hits[0]["rights_text_completion_eligible"]:
                matched[baseline_id] = hits[0]
            else:
                noncompletion_baseline_ids.add(hits[0]["source_id"])
    ambiguous = {
        source_id: identities for source_id, identities in review_to_canonical.items()
        if len(identities) != 1
    }
    if ambiguous:
        raise ValueError(f"one source review maps to multiple canonical rights identities: {ambiguous}")
    outside = sorted(
        row["source_id"] for row in reviews
        if row["rights_text_completion_eligible"]
        and row["source_id"] not in baseline_review_ids
    )
    noncompletion = sorted(noncompletion_baseline_ids)
    require(len(review_to_canonical), 11, "rights baseline identities with a review record")
    require(len(matched), 9, "rights baseline identities superseded by locator-bearing text review")
    require(noncompletion, ["COMP-SRC-017", "COMP-SRC-023"], "baseline review records still open")
    require(outside, ["R16-SRC-005"], "text review outside rights baseline")
    return matched, outside, noncompletion


def reconcile_metadata(
    leads: list[dict[str, str]], reviews: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    lead_ids = [row["metadata_lead_id"] for row in leads]
    require(len(leads), 101, "metadata baseline lead count")
    require(len(set(lead_ids)), 101, "metadata baseline lead identity uniqueness")
    matched: dict[str, dict[str, Any]] = {}
    for lead in leads:
        doi = normalize_identifier(lead["canonical_doi"])
        hits = [
            review for review in reviews
            if review["rights_text_completion_eligible"]
            and
            normalize_identifier(review["identifier"])
            and normalize_identifier(review["identifier"]) == doi
        ]
        if len(hits) > 1:
            raise ValueError(f"ambiguous metadata supersession for {lead['metadata_lead_id']}")
        if hits:
            matched[lead["metadata_lead_id"]] = hits[0]
    require(len(matched), 1, "metadata leads superseded by locator-bearing source-text review")
    return matched


def reconstruct_model() -> dict[str, Any]:
    hypotheses = collect_hypotheses()
    hypothesis_ids = sorted(row["hypothesis_id"] for row in hypotheses)
    governed = sorted(row["association_id"] for row in hypotheses if row["association_id"])
    ungoverned = sorted(row["hypothesis_id"] for row in hypotheses if not row["association_id"])
    require(len(governed), 4, "governed association identity count")
    require(len(set(governed)), 4, "governed association identity uniqueness")
    require(len(ungoverned), 7, "ungoverned hypothesis count")

    queue_parts: dict[str, list[dict[str, str]]] = {
        "terminal": [], "derivative": [], "open": [],
    }
    for relative in ASSOCIATION_QUEUE_PATHS:
        for row in read_tsv(relative):
            enriched = {**row, "_source_path": relative}
            if "CLOSED_PARENT" in row["queue_status"]:
                queue_parts["terminal"].append(enriched)
            elif row.get("queue_record_kind") == "DERIVATIVE_RECONCILIATION":
                queue_parts["derivative"].append(enriched)
            else:
                queue_parts["open"].append(enriched)
    queue_ids = [row["queue_id"] for rows in queue_parts.values() for row in rows]
    require(len(queue_ids), 59, "association review queue row count")
    require(len(set(queue_ids)), 59, "association review queue identity uniqueness")
    require({key: len(value) for key, value in queue_parts.items()}, {
        "terminal": 13, "derivative": 7, "open": 39,
    }, "association review queue partition")

    reviews = collect_source_reviews()
    rights_queue = read_tsv(RIGHTS_QUEUE_PATH)
    rights_matched, rights_outside, rights_incomplete_baseline = reconcile_rights(
        rights_queue, reviews,
    )
    rights_open = sorted(
        row["canonical_source_id"] for row in rights_queue
        if row["canonical_source_id"] not in rights_matched
    )
    metadata = read_tsv(METADATA_PATH)
    metadata_matched = reconcile_metadata(metadata, reviews)
    metadata_open = sorted(
        row["metadata_lead_id"] for row in metadata
        if row["metadata_lead_id"] not in metadata_matched
    )

    participant_rows = read_tsv(PARTICIPANT_PATH)
    if any(
        row["participant_resolution_status"] != "OPEN" or row["candidate_emitted"] != "false"
        for row in participant_rows
    ):
        raise ValueError("n-ary participant queue contains a closed or emitted row")
    require(len(participant_rows), 10, "open n-ary participant resolution count")
    parameter_rows = [
        row for row in read_tsv(PARAMETER_PATH)
        if row["higher_order_semantic_obligation"] == "true"
    ]
    require(len(parameter_rows), 9, "higher-order semantic parameter count")

    crosswalk = read_tsv(CROSSWALK_PATH)
    crosswalk_ids = {row["participant_sense_id"] for row in crosswalk}
    research_senses = {
        row["participant_sense_id"]: row["canonical_label"]
        for row in crosswalk if row["disposition"] == "RESEARCH_ONLY"
    }
    require(len(research_senses), 21, "research-only sense count")
    covered_senses: set[str] = set()
    local_families = read_tsv(LOCAL_FAMILY_PATH)
    for row in local_families:
        covered_senses.update(parse_string_array(
            row["participant_sense_ids_json"], f"{LOCAL_FAMILY_PATH}:{row['candidate_id']}",
        ))
    for row in hypotheses:
        covered_senses.update(row["participants"])
    covered_senses.update(row["relation_participant_sense_id"] for row in participant_rows)
    exclusion_rows = read_tsv(EXCLUSION_PATH)
    for row in exclusion_rows:
        covered_senses.update(parse_string_array(
            row["participant_sense_ids_json"], f"{EXCLUSION_PATH}:{row['exclusion_id']}",
        ))
    uncovered_research = sorted(set(research_senses) - covered_senses)
    require(len(exclusion_rows), 0, "candidate exclusion proof row count")
    require(len(uncovered_research), 9, "known uncovered research-only sense count")
    require({research_senses[value] for value in uncovered_research}, {
        "access", "circulation", "collective production", "cultural diplomacy",
        "cultural transferral", "decolonization", "erasure", "translation",
        "work migrations",
    }, "uncovered research-only labels")
    proposed_senses = sorted({
        participant for row in hypotheses for participant in row["participants"]
        if participant.startswith("R16B-PROPOSED-SENSE:")
    })
    require(len(proposed_senses), 2, "proposed-sense participant count")
    require(set(proposed_senses) & crosswalk_ids, set(), "proposed senses absent from governed crosswalk")

    legacy_human = [
        row for row in read_tsv(EXTERNAL_REVIEW_PATH)
        if row["reviewer_answer_status"] == "NOT_COMPLETED"
    ]
    require(len(legacy_human), 36, "legacy incomplete external-review count")
    human_members = sorted(
        [f"LEGACY:{row['review_unit_id']}" for row in legacy_human]
        + [f"R16B:{value}" for value in hypothesis_ids]
    )
    require(len(human_members), 47, "current namespaced human-authority blocker count")

    vocab_rows = [
        row for row in read_tsv(VOCAB_IMPACT_PATH)
        if row["active_product_path_count"] == "0"
        and row["active_association_count"] == "0"
        and row["higher_order_composability_proven"] == "false"
    ]
    isolated_rows = read_tsv(ISOLATED_PATH)
    require(len(vocab_rows), 5, "active noncomposable vocabulary count")
    if any(
        row["round16a_pair_degree"] != "0"
        or row["higher_order_composability_proven"] != "false"
        for row in isolated_rows
    ):
        raise ValueError("isolated active vocabulary escaped the noncomposable boundary")
    require(
        {row["vocabulary_id"] for row in vocab_rows},
        {row["vocabulary_id"] for row in isolated_rows},
        "active noncomposable vocabulary agrees with isolated audit",
    )

    subgraphs = read_tsv(R16A_SUBGRAPH_PATH)
    require(len(subgraphs), 58, "Round 16A association-subgraph reconciliation count")
    if any(
        row["semantic_carry_forward_authorized"] != "false"
        or row["active_fact_created"] != "false"
        or row["product_eligible"] != "false"
        for row in subgraphs
    ):
        raise ValueError("Round 16A semantic carry-forward or product activation escaped quarantine")
    family_arity = Counter(int(row["arity"]) for row in local_families)
    require(family_arity, Counter({3: 25, 4: 4, 6: 4, 5: 1, 8: 1}), "local candidate-family arity distribution")
    require(read_tsv(ASSOCIATION_EVIDENCE_PATH), [], "canonical Round 16B association-evidence ledger")

    r16a = read_json(R16A_CENSUS_PATH)
    v3 = read_json(V3_CENSUS_PATH)
    runtime = read_json(V3_RUNTIME_PATH)
    replay = read_json(V50_REPLAY_PATH)
    cp11 = read_json(CP11_RECEIPT_PATH)
    database = read_json(DB_MANIFEST_PATH)
    require(r16a["closure"], {key: False for key in CLOSURE_KEYS}, "Round 16A reconciliation closure boundary")
    require(v3["production_activation_count"], 0, "v3 production activation count")
    require(v3["production_active_pending_review_count"], 0, "v3 production active-pending count")
    require(runtime["status"], "PASS", "v3 runtime independent verification")
    require(runtime["production_boundary"]["production_activation_count"], 0, "runtime production activation")
    require(replay["status"], "PASS", "v50 replay status")
    require(replay["normalizedSchemasIdentical"], True, "v50 normalized-schema identity")
    require(cp11["status"], "PASS_RESEARCH_CAPABILITY_CLOSURE_WITHHELD", "Checkpoint 011 status")
    require(cp11["closure_flags"], {key: False for key in CLOSURE_KEYS}, "Checkpoint 011 closure flags")
    require(database["productionDataImported"], False, "database production import boundary")
    require(database["productionActivationPerformed"], False, "database activation boundary")
    require(database["deploymentPerformed"], False, "database deployment boundary")

    model = {
        "hypotheses": hypotheses,
        "hypothesis_ids": hypothesis_ids,
        "governed": governed,
        "governed_hypothesis_ids": sorted(
            row["hypothesis_id"] for row in hypotheses if row["association_id"]
        ),
        "ungoverned": ungoverned,
        "hypothesis_arity": Counter(row["arity"] for row in hypotheses),
        "queue_parts": queue_parts,
        "reviews": reviews,
        "rights_queue": rights_queue,
        "rights_matched": rights_matched,
        "rights_outside": rights_outside,
        "rights_incomplete_baseline": rights_incomplete_baseline,
        "rights_open": rights_open,
        "metadata": metadata,
        "metadata_matched": metadata_matched,
        "metadata_open": metadata_open,
        "participant_rows": participant_rows,
        "parameter_rows": parameter_rows,
        "research_senses": research_senses,
        "crosswalk_ids": sorted(crosswalk_ids),
        "proposed_senses": proposed_senses,
        "uncovered_research": uncovered_research,
        "legacy_human": legacy_human,
        "human_members": human_members,
        "vocab_rows": vocab_rows,
        "subgraphs": subgraphs,
        "family_arity": family_arity,
        "r16a": r16a,
        "v3": v3,
        "runtime": runtime,
        "replay": replay,
        "cp11": cp11,
        "database": database,
    }
    observed_hashes = {
        "hypotheses": id_set_hash(hypothesis_ids),
        "ungoverned": id_set_hash(ungoverned),
        "governed": id_set_hash(governed),
        "governed_hypotheses": id_set_hash(
            row["hypothesis_id"] for row in hypotheses if row["association_id"]
        ),
        "nary": id_set_hash(row["participant_resolution_queue_id"] for row in participant_rows),
        "uncovered_research": id_set_hash(uncovered_research),
        "vocab": id_set_hash(row["vocabulary_id"] for row in vocab_rows),
        "parameters": id_set_hash(row["parameter_name"] for row in parameter_rows),
        "rights_open": id_set_hash(rights_open),
        "metadata_open": id_set_hash(metadata_open),
        "human": id_set_hash(human_members),
        "queue_all": id_set_hash(queue_ids),
        "queue_terminal": id_set_hash(row["queue_id"] for row in queue_parts["terminal"]),
        "queue_derivative": id_set_hash(row["queue_id"] for row in queue_parts["derivative"]),
        "queue_open": id_set_hash(row["queue_id"] for row in queue_parts["open"]),
    }
    require(observed_hashes, {key: value for key, value in EXPECTED_SET_HASHES.items() if key != "supersession"}, "independent source-set hashes")
    model["set_hashes"] = observed_hashes
    return model


def enumerate_prior_source_rows() -> dict[tuple[str, str, str], tuple[int, dict[str, str]]]:
    """Enumerate the prior universe directly, independently of primary output."""
    result: dict[tuple[str, str, str], tuple[int, dict[str, str]]] = {}

    def append(kind: str, relative: str, identity_field: str, predicate: Callable[[dict[str, str]], bool] | None = None) -> None:
        for row_number, row in enumerate(read_tsv(relative), 2):
            if predicate is not None and not predicate(row):
                continue
            identity = row[identity_field]
            key = (kind, relative, identity)
            if key in result:
                raise ValueError(f"duplicate independent prior identity: {key}")
            result[key] = (row_number, row)

    for relative in GAP_PATHS:
        append("GAP", relative, "gap_id")
    for relative in ASSOCIATION_QUEUE_PATHS:
        append("ASSOCIATION_REVIEW_QUEUE", relative, "queue_id")
    append("SOURCE_RIGHTS_QUEUE", RIGHTS_QUEUE_PATH, "canonical_source_id")
    append("NARY_PARTICIPANT_OBLIGATION", PARTICIPANT_PATH, "participant_resolution_queue_id")
    append(
        "SEMANTIC_PARAMETER_OBLIGATION", PARAMETER_PATH, "parameter_name",
        lambda row: row["higher_order_semantic_obligation"] == "true",
    )
    append("METADATA_LEAD_OBLIGATION", METADATA_PATH, "metadata_lead_id")
    append("EXTERNAL_HUMAN_REVIEW_OBLIGATION", EXTERNAL_REVIEW_PATH, "review_unit_id")
    require(len(result), 414, "independent prior-record universe count")
    distribution = dict(sorted(Counter(key[0] for key in result).items()))
    require(distribution, EXPECTED_PRIOR_KIND_DISTRIBUTION, "independent prior-kind distribution")
    membership = ["\t".join(key) for key in result]
    require(id_set_hash(membership), EXPECTED_SET_HASHES["supersession"], "independent supersession membership SHA-256")
    return result


def independent_gap_route_oracle() -> dict[tuple[str, str], tuple[str, list[str]]]:
    """Independently maintained semantic route for every physical GAP row."""
    oracle: dict[tuple[str, str], tuple[str, list[str]]] = {}
    obligation = OBLIGATION_IDS

    def route(relative: str, identities: str, disposition: str, successor_keys: list[str]) -> None:
        successors = sorted(obligation[key] for key in successor_keys)
        for identity in identities.split():
            key = (relative, identity)
            if key in oracle:
                raise ValueError(f"duplicate independent GAP semantic route: {key}")
            oracle[key] = (disposition, successors)

    root = GAP_PATHS[0]
    route(root, "GAP-001", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["candidate", "nary"])
    route(root, "GAP-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["product"])
    route(root, "GAP-003", "SUPERSEDED_BY_OPEN_OBLIGATION", ["group", "r16a"])
    route(root, "GAP-004", "SUPERSEDED_BY_OPEN_OBLIGATION", ["vocab"])
    route(root, "GAP-005", "SUPERSEDED_BY_OPEN_OBLIGATION", ["human"])
    route(root, "GAP-006", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["rights"])
    route(root, "GAP-007", "SUPERSEDED_BY_OPEN_OBLIGATION", ["bound"])
    route(root, "GAP-008", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["pair", "group"])
    route(root, "GAP-009", "SUPERSEDED_BY_OPEN_OBLIGATION", ["metadata", "candidate"])
    route(root, "GAP-010", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["r16a", "product"])
    route(root, "GAP-011", "PRESERVED_TERMINAL_CONTROL", [])
    route(root, "GAP-012", "SUPERSEDED_BY_OPEN_OBLIGATION", ["candidate"])
    route(root, "GAP-013", "RESOLVED_BY_COMMITTED_ARTIFACT", [])
    route(root, "GAP-014", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["candidate"])

    cp3 = GAP_PATHS[1]
    route(cp3, "GAP-001 GAP-014 GAP-019 GAP-031", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["candidate"])
    route(cp3, "GAP-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["product"])
    route(cp3, "GAP-003", "SUPERSEDED_BY_OPEN_OBLIGATION", ["group", "r16a"])
    route(cp3, "GAP-004 GAP-024", "SUPERSEDED_BY_OPEN_OBLIGATION", ["vocab"])
    route(cp3, "GAP-005", "SUPERSEDED_BY_OPEN_OBLIGATION", ["human"])
    route(cp3, "GAP-006 GAP-018", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["rights"])
    route(cp3, "GAP-007", "SUPERSEDED_BY_OPEN_OBLIGATION", ["bound"])
    route(cp3, "GAP-008", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["pair", "group"])
    route(cp3, "GAP-009 GAP-020", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["metadata", "candidate"])
    route(cp3, "GAP-010 GAP-023 GAP-032", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["r16a", "product"])
    route(cp3, "GAP-011", "PRESERVED_TERMINAL_CONTROL", [])
    route(cp3, "GAP-012 GAP-022", "SUPERSEDED_BY_OPEN_OBLIGATION", ["candidate"])
    route(cp3, "GAP-013 GAP-015 GAP-025 GAP-026 GAP-028 GAP-029 GAP-030 GAP-033 GAP-034", "RESOLVED_BY_COMMITTED_ARTIFACT", [])
    route(cp3, "GAP-016", "SUPERSEDED_BY_OPEN_OBLIGATION", ["scope", "group", "queue"])
    route(cp3, "GAP-017", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["rights", "human", "group"])
    route(cp3, "GAP-021", "SUPERSEDED_BY_OPEN_OBLIGATION", ["nary"])
    route(cp3, "GAP-027", "PRESERVED_HISTORICAL_LIMITATION", [])

    cp4 = GAP_PATHS[2]
    route(cp4, "GAP-001 GAP-004", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["candidate", "scope"])
    route(cp4, "GAP-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["rights"])
    route(cp4, "GAP-003", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["metadata"])
    route(cp4, "GAP-005", "SUPERSEDED_BY_OPEN_OBLIGATION", ["human"])
    route(cp4, "GAP-006", "SUPERSEDED_BY_OPEN_OBLIGATION", ["bound"])
    route(cp4, "GAP-007", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["queue", "group", "scope"])
    route(cp4, "GAP-008", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["r16a", "product"])
    route(cp4, "GAP-009", "PRESERVED_HISTORICAL_LIMITATION", [])

    cp5 = GAP_PATHS[3]
    route(cp5, "GAP-010", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["queue", "group"])
    route(cp5, "GAP-011 GAP-014 GAP-015", "PRESERVED_TERMINAL_CONTROL", [])
    route(cp5, "GAP-012", "SUPERSEDED_BY_OPEN_OBLIGATION", ["queue", "scope"])
    route(cp5, "GAP-013", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["group", "human"])
    route(cp5, "GAP-016", "SUPERSEDED_BY_OPEN_OBLIGATION", ["product"])

    cp6 = GAP_PATHS[4]
    route(cp6, "GAP-017", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["queue", "group"])
    route(cp6, "GAP-018 GAP-020 GAP-021", "PRESERVED_TERMINAL_CONTROL", [])
    route(cp6, "GAP-019", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["queue"])
    route(cp6, "GAP-022", "SUPERSEDED_BY_OPEN_OBLIGATION", ["group", "scope", "human"])
    route(cp6, "GAP-023", "SUPERSEDED_BY_OPEN_OBLIGATION", ["product", "r16a"])
    route(cp6, "GAP-024", "SUPERSEDED_BY_OPEN_OBLIGATION", ["rights", "human", "group"])

    cp7 = GAP_PATHS[5]
    route(cp7, "GAP-025", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["candidate"])
    route(cp7, "GAP-026 GAP-027", "SUPERSEDED_BY_OPEN_OBLIGATION", ["group", "scope", "human"])
    route(cp7, "GAP-028 GAP-029 GAP-030 GAP-032", "PRESERVED_TERMINAL_CONTROL", [])
    route(cp7, "GAP-031", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["r16a", "product"])

    cp8 = GAP_PATHS[6]
    route(cp8, "GAP-R16B-008-001", "SUPERSEDED_BY_OPEN_OBLIGATION", ["human", "product"])
    route(cp8, "GAP-R16B-008-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["r16a", "group", "product"])
    route(cp8, "GAP-R16B-008-003 GAP-R16B-008-005", "RESOLVED_BY_COMMITTED_ARTIFACT", [])
    route(cp8, "GAP-R16B-008-004", "SUPERSEDED_BY_OPEN_OBLIGATION", ["bound"])

    shard1 = GAP_PATHS[7]
    shard1_successors = {
        "0afc59ec3c1298bc3ffbe9f912511da277e44682decc4b914bf04e5de0710823": ["human"],
        "8d7da37424b678e4a943fe109e5d93c6dfae74684eed17ebe2ddcc88e2d87f7f": ["rights"],
        "77315c825f65f9e6a4e193ec22bbd8537c8837020de4440eb0818728d19fea8b": ["scope"],
        "e49d03f04994a3c1de47c3e08ebf63c09a6929f9fd14ba511a226a4650a953bf": ["scope"],
        "711715ff0a111db59ec0e2536b6ebcc85ab31e41e1327e325865121e92bd2f73": ["scope", "human"],
        "ad757abca4717e8fa253c0e44971730a7ae8fc55ac2b9253d94da008707bdb79": ["scope", "group"],
        "17a6758a9f19605c957407617309802e0ea990701be9efd46ff4d54c3d77dd88": ["payload"],
        "374f75ee7c228223417b215b6157270adba2aea14e62716b8249bc80b06e046f": ["product"],
    }
    for suffix, successor_keys in shard1_successors.items():
        route(shard1, f"R16B-ADAPTIVE-SOURCE-GAP:{suffix}", "SUPERSEDED_BY_OPEN_OBLIGATION", successor_keys)

    shard2 = GAP_PATHS[8]
    route(shard2, "R16B-GAP-S2-001", "SUPERSEDED_BY_OPEN_OBLIGATION", ["human", "group"])
    route(shard2, "R16B-GAP-S2-002", "SUPERSEDED_BY_OPEN_OBLIGATION", ["cultural"])
    route(shard2, "R16B-GAP-S2-003", "SUPERSEDED_BY_OPEN_OBLIGATION", ["vocab", "product"])
    route(shard2, "R16B-GAP-S2-004", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["rights"])
    route(shard2, "R16B-GAP-S2-005", "SUPERSEDED_BY_OPEN_OBLIGATION", ["candidate"])
    route(shard2, "R16B-GAP-S2-006", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["r16a", "product"])

    global_reconciliation = GAP_PATHS[9]
    route(global_reconciliation, "R16B-GLOBAL-GAP-001 R16B-GLOBAL-GAP-002 R16B-GLOBAL-GAP-003", "SUPERSEDED_BY_OPEN_OBLIGATION", ["group", "r16a"])
    route(global_reconciliation, "R16B-GLOBAL-GAP-004", "SUPERSEDED_BY_OPEN_OBLIGATION", ["cultural"])
    route(global_reconciliation, "R16B-GLOBAL-GAP-005", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["product"])
    route(global_reconciliation, "R16B-GLOBAL-GAP-006", "PARTIALLY_RECONCILED_REMAINDER_OPEN", ["repro"])

    source_keys = {
        (relative, row["gap_id"])
        for relative in GAP_PATHS for row in read_tsv(relative)
    }
    require(len(oracle), 105, "independent GAP route oracle count")
    require(set(oracle), source_keys, "independent GAP route oracle completeness")
    return oracle


def validate_gap_route_projection(rows: list[dict[str, str]]) -> str:
    oracle = independent_gap_route_oracle()
    gap_rows = [row for row in rows if row["prior_kind"] == "GAP"]
    require(len(gap_rows), 105, "GAP semantic projection row count")
    observed_keys = {(row["source_path"], row["prior_id"]) for row in gap_rows}
    require(observed_keys, set(oracle), "GAP semantic projection key set")
    framed: list[str] = []
    for row in gap_rows:
        key = (row["source_path"], row["prior_id"])
        disposition, successors = oracle[key]
        observed_successors = parse_string_array(
            row["successor_obligation_ids_json"], f"GAP semantic route {key}",
        )
        require(row["current_disposition"], disposition, f"GAP semantic disposition {key}")
        require(observed_successors, successors, f"GAP semantic successors {key}")
        framed.append(
            "\t".join((key[0], key[1], disposition, canonical_json(successors)))
        )
    return id_set_hash(framed)


def validate_prior_status_projection(rows: list[dict[str, str]]) -> None:
    source_universe = enumerate_prior_source_rows()
    require(len(rows), 414, "prior-status specimen row count")
    for row in rows:
        key = (row["prior_kind"], row["source_path"], row["prior_id"])
        require(key in source_universe, True, f"prior-status specimen source key {key}")
        require(
            row["prior_status"], independent_status_projection(source_universe[key][1]),
            f"prior-status specimen exact projection {key}",
        )


def expected_obligation_members(model: dict[str, Any]) -> dict[str, list[str]]:
    return {
        OBLIGATION_IDS["candidate"]: sorted(model["uncovered_research"]),
        OBLIGATION_IDS["nary"]: sorted(row["participant_resolution_queue_id"] for row in model["participant_rows"]),
        OBLIGATION_IDS["rights"]: sorted(model["rights_open"]),
        OBLIGATION_IDS["metadata"]: sorted(model["metadata_open"]),
        OBLIGATION_IDS["human"]: sorted(model["human_members"]),
        OBLIGATION_IDS["scope"]: sorted(model["ungoverned"]),
        OBLIGATION_IDS["group"]: sorted(model["hypothesis_ids"]),
        OBLIGATION_IDS["cultural"]: ["COMP-EVID-018"],
        OBLIGATION_IDS["vocab"]: sorted(row["vocabulary_id"] for row in model["vocab_rows"]),
        OBLIGATION_IDS["bound"]: sorted(row["parameter_name"] for row in model["parameter_rows"]),
        OBLIGATION_IDS["r16a"]: sorted(row["prior_id"] for row in model["subgraphs"]),
        OBLIGATION_IDS["product"]: ["V3_PRODUCTION_ACTIVATION_COUNT:0"],
        OBLIGATION_IDS["pair"]: ["ROUND16A_PAIR_BASELINE_ONLY"],
        OBLIGATION_IDS["payload"]: sorted(row["source_id"] for row in model["reviews"]),
        OBLIGATION_IDS["repro"]: ["CHECKPOINT013_CLEAN_WORKTREE_REPRODUCTION_PENDING"],
        OBLIGATION_IDS["queue"]: sorted(row["queue_id"] for row in model["queue_parts"]["open"]),
    }


def independent_obligation_semantic_contract() -> dict[str, dict[str, Any]]:
    all_closures = sorted(CLOSURE_KEYS)

    def contract(
        key: str, obligation_class: str, count_semantics: str,
        evidence: list[str], action: str, blockers: list[str],
    ) -> tuple[str, dict[str, Any]]:
        return OBLIGATION_IDS[key], {
            "obligation_class": obligation_class,
            "count_semantics": count_semantics,
            "member_kind": obligation_class,
            "evidence_paths": sorted(evidence),
            "required_action": action,
            "blocks_closures": sorted(blockers),
        }

    return dict((
        contract(
            "candidate", "CANDIDATE_UNIVERSE_AND_EXCLUSION_PROOF",
            "KNOWN_MINIMUM_NOT_UNIVERSE_WIDE_TOTAL",
            [CROSSWALK_PATH, TRIGGER_PATH, EXCLUSION_PATH],
            "Add governed triggers or explicit exclusions for every uncovered sense, audit omitted structural classes, and prove the rule-level candidate complement.",
            all_closures,
        ),
        contract(
            "nary", "NARY_PARTICIPANT_RESOLUTION", "EXACT_OPEN_QUEUE",
            [PARTICIPANT_PATH],
            "Resolve the exact participant sets, scopes, roles, and qualifications without manufacturing pair edges.",
            all_closures,
        ),
        contract(
            "rights", "RIGHTS_AND_LAWFUL_TEXT", "CURRENT_AFTER_SUPERSESSION",
            [RIGHTS_QUEUE_PATH, *RIGHTS_REVIEW_PATHS],
            "Complete lawful access, rights, locator, and bounded source-text review for every unresolved canonical source identity.",
            all_closures,
        ),
        contract(
            "metadata", "METADATA_TO_TEXT_REVIEW", "CURRENT_AFTER_SUPERSESSION",
            [METADATA_PATH, *RIGHTS_REVIEW_PATHS],
            "Resolve each metadata lead to reviewable source text or record a final rejection; metadata remains non-evidence.",
            all_closures,
        ),
        contract(
            "human", "EXTERNAL_HUMAN_AUTHORITY", "DISJOINT_NAMESPACED_RECORDS",
            [EXTERNAL_REVIEW_PATH, *HYPOTHESIS_PATHS],
            "Obtain independent design-history review of bounded senses, synthesis, topology, and nonclaims before activation.",
            all_closures,
        ),
        contract(
            "scope", "SCOPE_SENSE_AND_IDENTITY", "UNGOVERNED_HYPOTHESES",
            list(HYPOTHESIS_PATHS),
            "Resolve proposed senses, case boundaries, participant distinctions, and governed association identity.",
            ["higher_order_association_closure", "global_composition_coherence_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        contract(
            "group", "GLOBAL_GROUP_COHERENCE", "CURRENT_SCOPED_HYPOTHESES",
            list(HYPOTHESIS_PATHS),
            "Complete independent exact-group evidence, scope, conflict, counterevidence, and global-coherence review.",
            ["higher_order_association_closure", "global_composition_coherence_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        contract(
            "cultural", "CULTURAL_TRANSFORMATION_REAUDIT", "EXACT_QUARANTINED_CLAIM",
            [GAP_PATHS[8], GAP_PATHS[9]],
            "Re-audit the inherited cultural-transformation claim against the conflicting official abstract and lawful text.",
            all_closures,
        ),
        contract(
            "vocab", "ACTIVE_VOCABULARY_REACHABILITY",
            "INHERITED_ACTIVE_ZERO_PAIR_DEGREE_AND_ZERO_ACTIVE_V3_PATH",
            [ISOLATED_PATH, VOCAB_IMPACT_PATH],
            "Validate an active product path, retain inquiry-only status, reclassify vocabulary, or govern an explicit non-product policy.",
            ["higher_order_association_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        contract(
            "bound", "SEMANTIC_AND_PRODUCT_ARITY_BOUND", "EXACT_SEMANTIC_PARAMETERS",
            [PARAMETER_PATH, LOCAL_FAMILY_PATH, CP11_RECEIPT_PATH],
            "Rejustify semantic bounds and derive a governed product maximum from evidence, accessibility, representation, and tested performance.",
            ["higher_order_association_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        contract(
            "r16a", "ROUND16A_SEMANTIC_RECONCILIATION", "NO_SEMANTIC_CARRY_FORWARD",
            [R16A_SUBGRAPH_PATH, R16A_CENSUS_PATH],
            "Resolve corrected, inquiry, rejected, and pair-baseline-only structures before any historical semantic carry-forward.",
            all_closures,
        ),
        contract(
            "product", "PRODUCTION_POPULATION_AND_REACHABILITY",
            "ZERO_HISTORICAL_PRODUCTION_ACTIVATIONS",
            [V3_CENSUS_PATH, V3_RUNTIME_PATH, CP11_RECEIPT_PATH, DB_MANIFEST_PATH],
            "Populate only externally authorized historical associations, regenerate reachable objects, and prove every active association and composition path.",
            ["product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        contract(
            "pair", "PAIR_ASSOCIATION_REAUDIT", "INHERITED_PAIR_BASELINE_NOT_CURRENT_CLOSURE",
            [ASSOCIATION_EVIDENCE_PATH, R16A_SUBGRAPH_PATH],
            "Reconcile inherited pair evidence under the current evidence and scope rules; an empty Round16B association-evidence ledger cannot prove pair closure.",
            ["pair_association_closure", "computational_space_closure", "function3_closure"],
        ),
        contract(
            "payload", "SOURCE_BYTE_REPRODUCIBILITY",
            "REVIEWED_SOURCES_WITH_NO_COMMITTED_SOURCE_PAYLOAD",
            list(RIGHTS_REVIEW_PATHS),
            "Preserve lawful source-byte hashes when permitted or retain the explicit locator-only reproducibility limitation.",
            ["computational_space_closure", "function3_closure"],
        ),
        contract(
            "repro", "FINAL_CLEAN_REPRODUCTION_GATE", "NEXT_CHECKPOINT_GATE",
            [CP11_RECEIPT_PATH],
            "Run final clean-worktree deterministic reproduction and the complete repository, build, API, database, LFS, and audit-seal gates.",
            ["computational_space_closure", "function3_closure"],
        ),
        contract(
            "queue", "OPEN_ASSOCIATION_REVIEW_QUEUE", "CURRENT_NONASSOCIATION_REVIEW_ROWS",
            list(ASSOCIATION_QUEUE_PATHS),
            "Resolve every conditional review row without treating queue membership as an association identity or support decision.",
            all_closures,
        ),
    ))


def validate_obligation_semantic_projection(rows: list[dict[str, str]]) -> None:
    semantic = independent_obligation_semantic_contract()
    require({row["obligation_id"] for row in rows}, set(semantic), "obligation semantic ID set")
    for row in rows:
        identity = row["obligation_id"]
        expected = semantic[identity]
        require(row["obligation_class"], expected["obligation_class"], f"obligation class {identity}")
        require(row["count_semantics"], expected["count_semantics"], f"obligation count semantics {identity}")
        require(row["member_kind"], expected["member_kind"], f"obligation member kind {identity}")
        require(
            parse_string_array(row["evidence_paths_json"], f"obligation evidence {identity}"),
            expected["evidence_paths"], f"obligation evidence paths {identity}",
        )
        require(row["required_action"], expected["required_action"], f"obligation action {identity}")
        require(
            parse_string_array(row["blocks_closures_json"], f"obligation blockers {identity}"),
            expected["blocks_closures"], f"obligation closure blockers {identity}",
        )


def verify_obligation_ledger(model: dict[str, Any]) -> dict[str, Any]:
    rows = read_tsv(OBLIGATION_PATH)
    expected_members = expected_obligation_members(model)
    require(len(rows), 16, "current obligation row count")
    require(len({row["obligation_id"] for row in rows}), 16, "current obligation ID uniqueness")
    require({row["obligation_id"] for row in rows}, set(expected_members), "current obligation ID set")
    validate_obligation_semantic_projection(rows)
    closure_blockers: Counter[str] = Counter()
    for row in rows:
        identity = row["obligation_id"]
        require(row["status"], "OPEN_CLOSURE_BLOCKING", f"obligation status {identity}")
        require(row["severity"], "CLOSURE_BLOCKING", f"obligation severity {identity}")
        members = parse_string_array(row["member_ids_json"], f"{OBLIGATION_PATH}:{identity}:members")
        require(members, sorted(set(members)), f"obligation member canonicalization {identity}")
        require(members, expected_members[identity], f"obligation members {identity}")
        require(int(row["member_count"]), len(members), f"obligation member count {identity}")
        require(row["member_ids_sha256"], id_set_hash(members), f"obligation member hash {identity}")
        evidence = parse_string_array(row["evidence_paths_json"], f"{OBLIGATION_PATH}:{identity}:evidence")
        if not evidence or any(not item for item in evidence):
            raise ValueError(f"obligation lacks evidence path: {identity}")
        blockers = parse_string_array(row["blocks_closures_json"], f"{OBLIGATION_PATH}:{identity}:blocks")
        if not blockers or not set(blockers) <= set(CLOSURE_KEYS):
            raise ValueError(f"obligation has invalid closure blocker set: {identity}")
        closure_blockers.update(blockers)
        material = {key: value for key, value in row.items() if key != "record_sha256"}
        require(row["record_sha256"], row_hash(material), f"obligation record hash {identity}")
    if any(closure_blockers[key] == 0 for key in CLOSURE_KEYS):
        raise ValueError("at least one closure lacks a current open blocker")
    return {
        "record_count": len(rows),
        "obligation_id_set_sha256": id_set_hash(expected_members),
        "open_closure_blocker_count_by_closure": dict(sorted(closure_blockers.items())),
        "ledger_sha256": sha256_file(OBLIGATION_PATH),
    }


def verify_supersession_ledger(model: dict[str, Any]) -> dict[str, Any]:
    independent = enumerate_prior_source_rows()
    rows = read_tsv(SUPERSESSION_PATH)
    require(len(rows), 414, "supersession ledger record count")
    observed_keys = [(row["prior_kind"], row["source_path"], row["prior_id"]) for row in rows]
    require(len(set(observed_keys)), 414, "supersession physical-key uniqueness")
    require(set(observed_keys), set(independent), "supersession physical-key completeness")
    expected_effects = {
        "RESOLVED_BY_COMMITTED_ARTIFACT": "TECHNICAL_OR_METHOD_GAP_RESOLVED_NO_CLOSURE_INFERENCE",
        "SUPERSEDED_BY_OPEN_OBLIGATION": "CURRENT_SUCCESSOR_BLOCKS_AT_LEAST_ONE_CLOSURE",
        "PARTIALLY_RECONCILED_REMAINDER_OPEN": "COMPLETED_WORK_PRESERVED_CURRENT_REMAINDER_BLOCKS_CLOSURE",
        "PRESERVED_TERMINAL_CONTROL": "TERMINAL_CONTROL_PRESERVED_NO_POSITIVE_CLOSURE_INFERENCE",
        "PRESERVED_HISTORICAL_LIMITATION": "HISTORICAL_LIMITATION_PRESERVED_NO_CLOSURE_INFERENCE",
    }
    terminal_ids = {row["queue_id"] for row in model["queue_parts"]["terminal"]}
    derivative_ids = {row["queue_id"] for row in model["queue_parts"]["derivative"]}
    current_ids = {row["queue_id"] for row in model["queue_parts"]["open"]}
    gap_route_sha256 = validate_gap_route_projection(rows)
    for row in rows:
        key = (row["prior_kind"], row["source_path"], row["prior_id"])
        source_row_number, source = independent[key]
        require(int(row["source_row_number"]), source_row_number, f"supersession source row {key}")
        require(row["prior_record_sha256"], source_record_hash(source), f"supersession source record hash {key}")
        require(row["prior_status"], independent_status_projection(source), f"supersession prior-status projection {key}")
        key_material = "\t".join(key)
        require(
            row["prior_record_key"], f"R16B-PRIOR-RECORD:{sha256_bytes(key_material.encode('utf-8'))}",
            f"supersession stable key {key}",
        )
        disposition = row["current_disposition"]
        require(disposition in expected_effects, True, f"supersession disposition vocabulary {key}")
        require(row["closure_effect"], expected_effects[disposition], f"supersession closure effect {key}")
        successors = parse_string_array(
            row["successor_obligation_ids_json"], f"{SUPERSESSION_PATH}:{key}:successors",
        )
        references = parse_string_array(
            row["successor_artifact_refs_json"], f"{SUPERSESSION_PATH}:{key}:refs",
        )
        if disposition in {"SUPERSEDED_BY_OPEN_OBLIGATION", "PARTIALLY_RECONCILED_REMAINDER_OPEN"}:
            if not successors:
                raise ValueError(f"open supersession lacks successor obligation: {key}")
        elif successors:
            raise ValueError(f"terminal supersession incorrectly has open successor: {key}")
        if not set(successors) <= set(OBLIGATION_IDS.values()):
            raise ValueError(f"supersession references unknown current obligation: {key}")
        if not references:
            raise ValueError(f"supersession lacks artifact reference: {key}")

        if row["prior_kind"] == "ASSOCIATION_REVIEW_QUEUE":
            if row["prior_id"] in terminal_ids:
                require(disposition, "PRESERVED_TERMINAL_CONTROL", f"terminal queue supersession {key}")
            elif row["prior_id"] in derivative_ids:
                require(disposition, "PARTIALLY_RECONCILED_REMAINDER_OPEN", f"derivative queue supersession {key}")
            elif row["prior_id"] in current_ids:
                require(disposition, "SUPERSEDED_BY_OPEN_OBLIGATION", f"open queue supersession {key}")
        elif row["prior_kind"] == "SOURCE_RIGHTS_QUEUE":
            expected = "RESOLVED_BY_COMMITTED_ARTIFACT" if row["prior_id"] in model["rights_matched"] else "SUPERSEDED_BY_OPEN_OBLIGATION"
            require(disposition, expected, f"rights supersession {key}")
        elif row["prior_kind"] == "METADATA_LEAD_OBLIGATION":
            expected = "RESOLVED_BY_COMMITTED_ARTIFACT" if row["prior_id"] in model["metadata_matched"] else "SUPERSEDED_BY_OPEN_OBLIGATION"
            require(disposition, expected, f"metadata supersession {key}")
        elif row["prior_kind"] in {
            "NARY_PARTICIPANT_OBLIGATION", "SEMANTIC_PARAMETER_OBLIGATION",
            "EXTERNAL_HUMAN_REVIEW_OBLIGATION",
        }:
            require(disposition, "SUPERSEDED_BY_OPEN_OBLIGATION", f"open obligation supersession {key}")
        material = {field: value for field, value in row.items() if field != "record_sha256"}
        require(row["record_sha256"], row_hash(material), f"supersession record hash {key}")

    membership = ["\t".join(key) for key in observed_keys]
    require(id_set_hash(membership), EXPECTED_SET_HASHES["supersession"], "supersession membership set hash")
    disposition_distribution = dict(sorted(Counter(row["current_disposition"] for row in rows).items()))
    kind_distribution = dict(sorted(Counter(row["prior_kind"] for row in rows).items()))
    require(kind_distribution, EXPECTED_PRIOR_KIND_DISTRIBUTION, "supersession prior-kind distribution")
    require(disposition_distribution, EXPECTED_DISPOSITION_DISTRIBUTION, "supersession disposition distribution")
    require(len({row["prior_record_key"] for row in rows}), 414, "supersession stable-key uniqueness")
    return {
        "prior_record_count": len(rows),
        "membership_id_set_sha256": id_set_hash(membership),
        "prior_kind_distribution": kind_distribution,
        "current_disposition_distribution": disposition_distribution,
        "gap_semantic_route_count": 105,
        "gap_semantic_route_id_set_sha256": gap_route_sha256,
        "ledger_sha256": sha256_file(SUPERSESSION_PATH),
    }


def assert_fail_closed_view(view: dict[str, Any]) -> None:
    require(view["unresolved_association_count"], 11, "headline unresolved association count")
    require(view["rights_current_unresolved"], 85, "current unresolved rights count")
    require(view["metadata_current_unreviewed"], 100, "current metadata-only count")
    require(view["human_current_blockers"], 47, "current namespaced human blocker count")
    require(view["known_unexplained_exclusions"], 9, "known scoped exclusion-proof gap count")
    require(view["universe_wide_unexplained_exclusions"], "INDETERMINATE", "universe-wide unexplained exclusion count")
    require(view["active_pending_review_count"], 0, "active pending-review count")
    require(view["active_association_count"], 0, "active association count")
    require(view["product_eligible_association_count"], 0, "product-eligible association count")
    require(view["implicit_pair_projection_count"], 0, "implicit pair projection count")
    require(view["uncovered_research_count"], 9, "uncovered research-only sense count")
    require(view["proposed_sense_governed_coverage_count"], 0, "proposed-sense governed coverage count")
    require(view["active_noncomposable_vocabulary_count"], 5, "active noncomposable vocabulary count")
    require(
        view["governed_association_id_set_sha256"], EXPECTED_SET_HASHES["governed"],
        "governed association-ID set hash",
    )
    require(
        view["governed_hypothesis_id_set_sha256"], EXPECTED_SET_HASHES["governed_hypotheses"],
        "governed hypothesis-ID set hash",
    )
    if view["governed_association_id_set_sha256"] == view["governed_hypothesis_id_set_sha256"]:
        raise ValueError("governed association and hypothesis identity domains were collapsed")
    require(view["candidate_universe_closure"], False, "candidate-universe closure")
    require(view["closure"], {key: False for key in CLOSURE_KEYS}, "closure flags")
    if any(value not in {"INACTIVE", "INQUIRY_ONLY"} for value in view["hypothesis_activation_statuses"]):
        raise ValueError("an activation-status corruption escaped fail-closed validation")


def headline_view(model: dict[str, Any]) -> dict[str, Any]:
    return {
        "unresolved_association_count": len(model["hypotheses"]),
        "rights_current_unresolved": len(model["rights_open"]),
        "metadata_current_unreviewed": len(model["metadata_open"]),
        "human_current_blockers": len(model["human_members"]),
        "known_unexplained_exclusions": len(model["uncovered_research"]),
        "universe_wide_unexplained_exclusions": "INDETERMINATE",
        "active_pending_review_count": 0,
        "active_association_count": 0,
        "product_eligible_association_count": 0,
        "implicit_pair_projection_count": 0,
        "uncovered_research_count": len(model["uncovered_research"]),
        "proposed_sense_governed_coverage_count": len(
            set(model["proposed_senses"]) & set(model["crosswalk_ids"])
        ),
        "active_noncomposable_vocabulary_count": len(model["vocab_rows"]),
        "governed_association_id_set_sha256": model["set_hashes"]["governed"],
        "governed_hypothesis_id_set_sha256": model["set_hashes"]["governed_hypotheses"],
        "candidate_universe_closure": False,
        "closure": {key: False for key in CLOSURE_KEYS},
        "hypothesis_activation_statuses": [row["activation"] for row in model["hypotheses"]],
    }


def expect_rejection(name: str, mutation: Callable[[dict[str, Any]], None], baseline: dict[str, Any]) -> dict[str, str]:
    specimen = copy.deepcopy(baseline)
    mutation(specimen)
    try:
        assert_fail_closed_view(specimen)
    except ValueError:
        return {"probe": name, "status": "PASS_REJECTED"}
    raise ValueError(f"adversarial probe was accepted: {name}")


def expect_operation_rejection(name: str, operation: Callable[[], None]) -> dict[str, str]:
    try:
        operation()
    except ValueError:
        return {"probe": name, "status": "PASS_REJECTED"}
    raise ValueError(f"adversarial probe was accepted: {name}")


def validate_membership_specimen(
    keys: list[tuple[str, str, str]], canonical: set[tuple[str, str, str]],
) -> None:
    require(len(keys), 414, "membership specimen row count")
    require(len(set(keys)), 414, "membership specimen uniqueness")
    for kind, relative, identity in keys:
        if kind not in EXPECTED_PRIOR_KIND_DISTRIBUTION:
            raise ValueError("membership specimen has a noncanonical kind")
        if Path(relative).is_absolute() or relative.startswith("./") or not identity:
            raise ValueError("membership specimen has a noncanonical path or empty identity")
    require(set(keys), canonical, "membership specimen physical key set")
    framed = "".join("\t".join(key) + "\n" for key in sorted(keys)).encode("utf-8")
    require(sha256_bytes(framed), EXPECTED_SET_HASHES["supersession"], "membership specimen final-LF hash")


def validate_queue_partition(
    terminal: list[str], derivative: list[str], current: list[str],
) -> None:
    require(len(terminal), 13, "queue terminal partition count")
    require(len(derivative), 7, "queue derivative partition count")
    require(len(current), 39, "queue current-open partition count")
    require(len(set([*terminal, *derivative, *current])), 59, "queue partition disjoint union")
    require(id_set_hash(terminal), EXPECTED_SET_HASHES["queue_terminal"], "queue terminal partition hash")
    require(id_set_hash(derivative), EXPECTED_SET_HASHES["queue_derivative"], "queue derivative partition hash")
    require(id_set_hash(current), EXPECTED_SET_HASHES["queue_open"], "queue current-open partition hash")


def validate_hypothesis_specimen(records: list[dict[str, Any]]) -> None:
    require(len(records), 11, "hypothesis specimen count")
    require(len({row["hypothesis_id"] for row in records}), 11, "hypothesis specimen ID uniqueness")
    for row in records:
        require(
            bool(row["association_id"]), bool(row["association_revision_id"]),
            f"hypothesis governance parity {row['hypothesis_id']}",
        )
        require(len(row["participants"]), row["arity"], f"hypothesis arity {row['hypothesis_id']}")
        require(len(set(row["participants"])), row["arity"], f"hypothesis participant uniqueness {row['hypothesis_id']}")
        if row["activation"] not in {"INACTIVE", "INQUIRY_ONLY"}:
            raise ValueError("hypothesis specimen activates a pending record")
        require(row["pair_projection_count"], 0, f"hypothesis pair projection {row['hypothesis_id']}")


def run_adversarial_probes(model: dict[str, Any]) -> list[dict[str, str]]:
    baseline = headline_view(model)
    assert_fail_closed_view(baseline)
    probes = [
        expect_rejection("STALE_RIGHTS_BASELINE_94_AS_CURRENT", lambda value: value.update(rights_current_unresolved=94), baseline),
        expect_rejection("STALE_METADATA_BASELINE_101_AS_CURRENT", lambda value: value.update(metadata_current_unreviewed=101), baseline),
        expect_rejection("STALE_LEGACY_HUMAN_36_AS_CURRENT", lambda value: value.update(human_current_blockers=36), baseline),
        expect_rejection("UNRESOLVED_ASSOCIATIONS_REDUCED_TO_GOVERNED_IDENTITIES_4", lambda value: value.update(unresolved_association_count=4), baseline),
        expect_rejection("UNIVERSE_WIDE_EXCLUSION_COUNT_FALSELY_NUMERIC", lambda value: value.update(universe_wide_unexplained_exclusions=9), baseline),
        expect_rejection("KNOWN_UNCOVERED_RESEARCH_SENSE_REMOVED", lambda value: value.update(uncovered_research_count=8), baseline),
        expect_rejection("PROPOSED_SENSE_TREATED_AS_GOVERNED_COVERAGE", lambda value: value.update(proposed_sense_governed_coverage_count=1), baseline),
        expect_rejection("ACTIVE_NONCOMPOSABLE_VOCABULARY_ROW_DROPPED", lambda value: value.update(active_noncomposable_vocabulary_count=4), baseline),
        expect_rejection(
            "GOVERNED_ASSOCIATION_IDS_REPLACED_WITH_HYPOTHESIS_IDS",
            lambda value: value.update(
                governed_association_id_set_sha256=value["governed_hypothesis_id_set_sha256"],
            ), baseline,
        ),
        expect_rejection("ACTIVE_PENDING_REVIEW_ONE", lambda value: value.update(active_pending_review_count=1), baseline),
        expect_rejection("ACTIVE_HYPOTHESIS", lambda value: value["hypothesis_activation_statuses"].__setitem__(0, "ACTIVE"), baseline),
        expect_rejection("PRODUCT_ELIGIBLE_HYPOTHESIS", lambda value: value.update(product_eligible_association_count=1), baseline),
        expect_rejection("IMPLICIT_HYPEREDGE_PAIR_PROJECTION", lambda value: value.update(implicit_pair_projection_count=1), baseline),
        expect_rejection("CANDIDATE_UNIVERSE_FALSELY_CLOSED", lambda value: value.update(candidate_universe_closure=True), baseline),
        expect_rejection("FUNCTION3_FALSELY_CLOSED", lambda value: value["closure"].update(function3_closure=True), baseline),
    ]

    universe = list(enumerate_prior_source_rows())
    canonical_universe = set(universe)
    wrong_kind = copy.deepcopy(universe)
    wrong_kind[0] = ("GAPS", wrong_kind[0][1], wrong_kind[0][2])
    absolute_path = copy.deepcopy(universe)
    absolute_path[0] = (absolute_path[0][0], f"/{absolute_path[0][1]}", absolute_path[0][2])
    dotted_path = copy.deepcopy(universe)
    dotted_path[0] = (dotted_path[0][0], f"./{dotted_path[0][1]}", dotted_path[0][2])
    wrong_native_id = copy.deepcopy(universe)
    wrong_native_id[0] = (wrong_native_id[0][0], wrong_native_id[0][1], "WRONG-NATIVE-ID")
    gap_deduplicated = list({(kind, identity): key for key in universe for kind, _, identity in [key]}.values())
    for name, corrupt in (
        ("SUPERSESSION_MEMBER_MISSING", universe[:-1]),
        ("SUPERSESSION_MEMBER_EXTRA", [*universe, ("GAP", GAP_PATHS[0], "EXTRA-GAP")]),
        ("SUPERSESSION_MEMBER_DUPLICATED", [*universe, universe[0]]),
        ("SUPERSESSION_KIND_MISSPELLED", wrong_kind),
        ("SUPERSESSION_ABSOLUTE_PATH", absolute_path),
        ("SUPERSESSION_DOT_RELATIVE_PATH", dotted_path),
        ("SUPERSESSION_WRONG_NATIVE_ID", wrong_native_id),
        ("SUPERSESSION_GAP_IDS_DEDUPLICATED_ACROSS_PHYSICAL_FILES", gap_deduplicated),
    ):
        probes.append(expect_operation_rejection(
            name, lambda corrupt=corrupt: validate_membership_specimen(corrupt, canonical_universe),
        ))
    missing_final_lf = "\n".join("\t".join(key) for key in sorted(universe)).encode("utf-8")
    probes.append(expect_operation_rejection(
        "SUPERSESSION_MEMBERSHIP_FINAL_LF_MISSING",
        lambda: require(
            sha256_bytes(missing_final_lf), EXPECTED_SET_HASHES["supersession"],
            "membership hash without final LF",
        ),
    ))

    terminal_ids = [row["queue_id"] for row in model["queue_parts"]["terminal"]]
    derivative_ids = [row["queue_id"] for row in model["queue_parts"]["derivative"]]
    open_ids = [row["queue_id"] for row in model["queue_parts"]["open"]]
    validate_queue_partition(terminal_ids, derivative_ids, open_ids)
    tcq004 = next(
        row["queue_id"] for row in model["queue_parts"]["derivative"]
        if row["queue_action"] == "RECONCILE_PRIOR_STRUCTURAL_DESCENDANTS"
    )
    tcq007 = next(
        row["queue_id"] for row in model["queue_parts"]["open"]
        if row["queue_action"] == "AUDIT_METHOD_LEVEL_AND_THREE_CASE_SPECIFIC_IDENTITIES"
    )
    probes.append(expect_operation_rejection(
        "TCQ004_DERIVATIVE_MISCLASSIFIED_OPEN",
        lambda: validate_queue_partition(
            terminal_ids, [value for value in derivative_ids if value != tcq004], [*open_ids, tcq004],
        ),
    ))
    probes.append(expect_operation_rejection(
        "TCQ007_OPEN_MISCLASSIFIED_BY_RECONCILIATION_SUBSTRING",
        lambda: validate_queue_partition(
            terminal_ids, [*derivative_ids, tcq007], [value for value in open_ids if value != tcq007],
        ),
    ))

    semantic_class_ids = sorted(
        row["parameter_name"] for row in read_tsv(PARAMETER_PATH)
        if row["parameter_class"] == "semantic"
    )
    obligation_parameter_ids = sorted(row["parameter_name"] for row in model["parameter_rows"])
    probes.append(expect_operation_rejection(
        "SEMANTIC_CLASS_11_USED_INSTEAD_OF_EXPLICIT_OBLIGATION_9",
        lambda: require(semantic_class_ids, obligation_parameter_ids, "semantic parameter selector"),
    ))

    doi_only_review_ids = {
        normalize_identifier(row["identifier"]) for row in model["reviews"] if row["identifier"]
    }
    doi_only_matches = {
        row["canonical_source_id"] for row in model["rights_queue"]
        if normalize_identifier(row["doi_isbn_or_identifier"]) in doi_only_review_ids
    }
    require(len(doi_only_matches), 10, "DOI-only rights diagnostic match count")
    probes.append(expect_operation_rejection(
        "RIGHTS_DOI_ONLY_JOIN_LOSES_STABLE_URL_IDENTITY",
        lambda: require(len(doi_only_matches), 11, "DOI-only rights join"),
    ))
    probes.append(expect_operation_rejection(
        "RIGHTS_ALL_12_REVIEWS_BLINDLY_SUBTRACTED",
        lambda: require(94 - len(model["reviews"]), 85, "blind rights subtraction"),
    ))

    duplicate_rights_queue = [*copy.deepcopy(model["rights_queue"]), copy.deepcopy(model["rights_queue"][0])]
    probes.append(expect_operation_rejection(
        "RIGHTS_DUPLICATE_CANONICAL_IDENTITY",
        lambda: reconcile_rights(duplicate_rights_queue, model["reviews"]),
    ))
    two_reviews_for_one = copy.deepcopy(model["reviews"])
    cloned_review = copy.deepcopy(next(row for row in two_reviews_for_one if row["identifier"]))
    cloned_review["source_id"] = "AMBIGUOUS-SECOND-REVIEW"
    two_reviews_for_one.append(cloned_review)
    probes.append(expect_operation_rejection(
        "RIGHTS_TWO_REVIEWS_MATCH_ONE_CANONICAL_IDENTITY",
        lambda: reconcile_rights(model["rights_queue"], two_reviews_for_one),
    ))
    one_review_two_identities = copy.deepcopy(model["reviews"])
    ambiguous_target = next(
        row for row in one_review_two_identities
        if row["source_id"] != "R16-SRC-005" and row["identifier"]
    )
    original_matches = [
        row for row in model["rights_queue"]
        if row["canonical_source_id"] in model["rights_matched"]
        and model["rights_matched"][row["canonical_source_id"]]["source_id"] == ambiguous_target["source_id"]
    ]
    require(len(original_matches), 1, "ambiguous-review control original match")
    other_queue = next(
        row for row in model["rights_queue"]
        if row["canonical_source_id"] not in {original_matches[0]["canonical_source_id"]}
        and normalize_identifier(row["doi_isbn_or_identifier"])
    )
    ambiguous_target["identifier"] = other_queue["doi_isbn_or_identifier"]
    probes.append(expect_operation_rejection(
        "RIGHTS_ONE_REVIEW_MAPS_TWO_CANONICAL_IDENTITIES",
        lambda: reconcile_rights(model["rights_queue"], one_review_two_identities),
    ))

    duplicate_metadata = [*copy.deepcopy(model["metadata"]), copy.deepcopy(model["metadata"][0])]
    probes.append(expect_operation_rejection(
        "METADATA_DUPLICATE_LEAD_IDENTITY",
        lambda: reconcile_metadata(duplicate_metadata, model["reviews"]),
    ))

    hypothesis_arity_control = copy.deepcopy(model["hypotheses"])
    hypothesis_arity_control[0]["participants"] = hypothesis_arity_control[0]["participants"][:-1]
    probes.append(expect_operation_rejection(
        "HYPOTHESIS_PARTICIPANT_LENGTH_DIFFERS_FROM_ARITY",
        lambda: validate_hypothesis_specimen(hypothesis_arity_control),
    ))
    hypothesis_duplicate_control = copy.deepcopy(model["hypotheses"])
    hypothesis_duplicate_control[0]["participants"][0] = hypothesis_duplicate_control[0]["participants"][1]
    probes.append(expect_operation_rejection(
        "HYPOTHESIS_DUPLICATE_PARTICIPANT",
        lambda: validate_hypothesis_specimen(hypothesis_duplicate_control),
    ))
    hypothesis_revision_control = copy.deepcopy(model["hypotheses"])
    governed_control = next(row for row in hypothesis_revision_control if row["association_id"])
    governed_control["association_revision_id"] = ""
    probes.append(expect_operation_rejection(
        "HYPOTHESIS_ASSOCIATION_REVISION_PARITY_BROKEN",
        lambda: validate_hypothesis_specimen(hypothesis_revision_control),
    ))

    wrong_input_paths = set(EXPECTED_INPUT_PATHS)
    wrong_input_paths.remove(LOCAL_FAMILY_PATH)
    wrong_input_paths.add(f"{RAW_REL}/local-candidate-family-ledger-v1.tsv")
    probes.append(expect_operation_rejection(
        "STALE_LOCAL_CANDIDATE_FAMILY_V1_SELECTED",
        lambda: require(frozenset(wrong_input_paths), EXPECTED_INPUT_PATHS, "input path authority"),
    ))
    wrong_crosswalk_paths = set(EXPECTED_INPUT_PATHS)
    wrong_crosswalk_paths.remove(CROSSWALK_PATH)
    wrong_crosswalk_paths.add(f"{RAW_REL}/concept-sense-crosswalk.tsv")
    probes.append(expect_operation_rejection(
        "HEADER_ONLY_CROSSWALK_PLACEHOLDER_SELECTED",
        lambda: require(frozenset(wrong_crosswalk_paths), EXPECTED_INPUT_PATHS, "crosswalk path authority"),
    ))

    manifest_authority_control = copy.deepcopy(read_tsv(INPUT_MANIFEST_PATH))
    next(
        row for row in manifest_authority_control if row["path"] == R16A_CENSUS_PATH
    )["authority_boundary"] = "COMMITTED_ROUND16B_PRE_CHECKPOINT011_BYTES"
    probes.append(expect_operation_rejection(
        "INPUT_MANIFEST_AUTHORITY_BOUNDARY_DOWNGRADED",
        lambda: validate_manifest_authorities(manifest_authority_control),
    ))

    supersession_control = copy.deepcopy(read_tsv(SUPERSESSION_PATH))
    gap_swap_candidates = [
        row for row in supersession_control
        if row["prior_kind"] == "GAP"
        and row["current_disposition"] == "SUPERSEDED_BY_OPEN_OBLIGATION"
    ]
    gap_left = next(
        row for row in gap_swap_candidates
        if parse_string_array(row["successor_obligation_ids_json"], "gap-swap-left")
        == [OBLIGATION_IDS["human"]]
    )
    gap_right = next(
        row for row in gap_swap_candidates
        if parse_string_array(row["successor_obligation_ids_json"], "gap-swap-right")
        == [OBLIGATION_IDS["bound"]]
    )
    gap_left["successor_obligation_ids_json"], gap_right["successor_obligation_ids_json"] = (
        gap_right["successor_obligation_ids_json"], gap_left["successor_obligation_ids_json"]
    )
    probes.append(expect_operation_rejection(
        "GAP_SUCCESSOR_ROUTES_SWAPPED_WITH_AGGREGATES_PRESERVED",
        lambda: validate_gap_route_projection(supersession_control),
    ))

    prior_status_control = copy.deepcopy(read_tsv(SUPERSESSION_PATH))
    next(
        row for row in prior_status_control if row["prior_kind"] == "SOURCE_RIGHTS_QUEUE"
    )["prior_status"] = canonical_json({"status": "UNSPECIFIED"})
    probes.append(expect_operation_rejection(
        "RIGHTS_PRIOR_STATUS_PROJECTION_ERASED",
        lambda: validate_prior_status_projection(prior_status_control),
    ))

    obligation_action_control = copy.deepcopy(read_tsv(OBLIGATION_PATH))
    next(
        row for row in obligation_action_control
        if row["obligation_id"] == OBLIGATION_IDS["rights"]
    )["required_action"] = "Treat a matching DOI as completion."
    probes.append(expect_operation_rejection(
        "OBLIGATION_REQUIRED_ACTION_CORRUPTED",
        lambda: validate_obligation_semantic_projection(obligation_action_control),
    ))

    obligation_blocker_control = copy.deepcopy(read_tsv(OBLIGATION_PATH))
    next(
        row for row in obligation_blocker_control
        if row["obligation_id"] == OBLIGATION_IDS["metadata"]
    )["blocks_closures_json"] = canonical_json(["function3_closure"])
    probes.append(expect_operation_rejection(
        "OBLIGATION_EXACT_CLOSURE_BLOCKERS_CORRUPTED",
        lambda: validate_obligation_semantic_projection(obligation_blocker_control),
    ))

    missing_locator_review = copy.deepcopy(
        next(row for row in model["reviews"] if row["source_id"] == "COMP-SRC-001")["raw"]
    )
    missing_locator_review["text_urls_json"] = "[]"
    probes.append(expect_operation_rejection(
        "RIGHTS_FULL_TEXT_STATUS_WITHOUT_TEXT_LOCATOR",
        lambda: require(
            independent_rights_text_completion(missing_locator_review, RIGHTS_REVIEW_PATHS[0]),
            True, "full-text status without text locator",
        ),
    ))

    abstract_only_review = copy.deepcopy(
        next(row for row in model["reviews"] if row["source_id"] == "COMP-SRC-017")["raw"]
    )
    abstract_only_review["access_status"] = "OPEN_ACCESS_PUBLISHER_FULL_TEXT_REVIEWED"
    probes.append(expect_operation_rejection(
        "RIGHTS_ABSTRACT_LOCATOR_NOT_PROMOTED_BY_ACCESS_LABEL",
        lambda: require(
            independent_rights_text_completion(abstract_only_review, RIGHTS_REVIEW_PATHS[1]),
            True, "abstract-only locator with promoted access label",
        ),
    ))

    metadata_abstract_promotion = copy.deepcopy(model["reviews"])
    next(
        row for row in metadata_abstract_promotion if row["source_id"] == "COMP-SRC-017"
    )["rights_text_completion_eligible"] = True
    probes.append(expect_operation_rejection(
        "METADATA_ABSTRACT_ONLY_DOI_FALSELY_SUPERSEDED",
        lambda: reconcile_metadata(model["metadata"], metadata_abstract_promotion),
    ))

    rights_prefix_control = copy.deepcopy(model["reviews"])
    rights_target = next(
        row for row in rights_prefix_control
        if row["identifier"] and row["source_id"] != "R16-SRC-005"
    )
    rights_target["source_id"] = "DOI-PREFIX-CONTROL-NONMEMBER"
    rights_target["identifier"] = f"HTTPS://DOI.ORG/{rights_target['identifier'].upper()}"
    matched, outside, incomplete = reconcile_rights(model["rights_queue"], rights_prefix_control)
    require(len(matched), 9, "DOI resolver-prefix rights text-completion match count")
    require(outside, ["R16-SRC-005"], "DOI resolver-prefix rights outside-baseline set")
    require(incomplete, ["COMP-SRC-017", "COMP-SRC-023"], "DOI resolver-prefix noncompletion set")
    probes.append({"probe": "RIGHTS_DOI_RESOLVER_PREFIX_NORMALIZED", "status": "PASS_NORMALIZED"})

    metadata_prefix_control = copy.deepcopy(model["reviews"])
    for row in metadata_prefix_control:
        if row["identifier"]:
            row["identifier"] = f"http://dx.doi.org/{row['identifier'].upper()}"
    require(
        len(reconcile_metadata(model["metadata"], metadata_prefix_control)), 1,
        "DOI resolver-prefix metadata match count",
    )
    probes.append({"probe": "METADATA_DOI_RESOLVER_PREFIX_NORMALIZED", "status": "PASS_NORMALIZED"})

    require(len(probes), 48, "adversarial probe count")
    return probes


def verify_metrics(model: dict[str, Any], supersession: dict[str, Any]) -> dict[str, Any]:
    metrics = read_json(METRICS_PATH)
    require(metrics["format"], "trace-round16b-recursive-gap-closure-metrics-checkpoint012-v2", "primary metrics format")
    require(metrics["builder_version"], "trace-round16b-recursive-gap-closure-audit-builder-v2", "primary metrics builder version")
    require(metrics["status"], "PASS_EVIDENCE_BOUNDED_NONCLOSURE", "primary metrics status")
    require(metrics["authority"], {
        "checkpoint011_sha": AUTHORITY_BASE_SHA,
        "checkpoint011_tree": AUTHORITY_BASE_TREE,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
    }, "primary metrics authority")
    require(metrics["supersession"]["prior_record_count"], 414, "metrics supersession count")
    require(metrics["supersession"]["prior_record_key_unique_count"], 414, "metrics supersession key uniqueness")
    require(metrics["supersession"]["membership_id_set_sha256"], supersession["membership_id_set_sha256"], "metrics supersession hash")
    require(metrics["supersession"]["prior_kind_distribution"], EXPECTED_PRIOR_KIND_DISTRIBUTION, "metrics prior-kind distribution")
    require(metrics["supersession"]["current_disposition_distribution"], EXPECTED_DISPOSITION_DISTRIBUTION, "metrics disposition distribution")

    hypotheses = metrics["hypotheses"]
    require(hypotheses["unresolved_association_count"], 11, "metrics unresolved association count")
    require(hypotheses["unresolved_association_count_scope"], "CURRENT_SCOPED_ASSOCIATION_HYPOTHESES", "metrics unresolved association scope")
    require(hypotheses["arity_distribution"], {"2": 3, "3": 6, "4": 1, "5": 1}, "metrics hypothesis arity distribution")
    require(hypotheses["governed_association_identity_count"], 4, "metrics governed association identities")
    require(hypotheses["ungoverned_hypothesis_count"], 7, "metrics ungoverned hypotheses")
    require(hypotheses["active_association_count"], 0, "metrics active association count")
    require(hypotheses["active_pending_review_count"], 0, "metrics active pending-review count")
    require(hypotheses["product_eligible_association_count"], 0, "metrics product-eligible association count")
    require(hypotheses["implicit_pair_projection_count"], 0, "metrics implicit pair projections")
    require(hypotheses["hypothesis_id_set_sha256"], model["set_hashes"]["hypotheses"], "metrics hypothesis hash")
    require(hypotheses["governed_association_id_set_sha256"], model["set_hashes"]["governed"], "metrics governed identity hash")
    require(hypotheses["ungoverned_hypothesis_id_set_sha256"], model["set_hashes"]["ungoverned"], "metrics ungoverned hypothesis hash")

    queue = metrics["association_review_queue"]
    require(queue["baseline_record_count"], 59, "metrics association queue baseline")
    require(queue["terminal_control_count"], 13, "metrics association queue terminal")
    require(queue["derivative_reconciled_successor_open_count"], 7, "metrics association queue derivative")
    require(queue["current_open_review_count"], 39, "metrics association queue current open")
    require(queue["current_open_review_id_set_sha256"], model["set_hashes"]["queue_open"], "metrics association queue open hash")
    require(queue["queue_rows_are_associations"], False, "metrics queue/association distinction")

    candidate = metrics["candidate_universe"]
    require(candidate["research_only_sense_count"], 21, "metrics research-only sense count")
    require(candidate["covered_research_only_sense_count"], 12, "metrics covered research-only sense count")
    require(candidate["known_unexplained_exclusion_count"], 9, "metrics known exclusion-proof gaps")
    require(candidate["universe_wide_unexplained_exclusion_count"], "INDETERMINATE", "metrics universe-wide unexplained exclusions")
    require(candidate["candidate_exclusion_ledger_record_count"], 0, "metrics exclusion proof rows")
    require(candidate["open_nary_participant_obligation_count"], 10, "metrics n-ary participant obligations")
    require(candidate["governed_product_maximum_arity"], None, "metrics governed product maximum arity")
    require(candidate["candidate_universe_closure"], False, "metrics candidate-universe closure")
    require(candidate["uncovered_research_only_sense_id_set_sha256"], model["set_hashes"]["uncovered_research"], "metrics uncovered research sense hash")
    require(candidate["open_nary_participant_obligation_id_set_sha256"], model["set_hashes"]["nary"], "metrics n-ary obligation hash")

    rights = metrics["source_rights"]
    require(rights["baseline_canonical_identity_count"], 94, "metrics rights baseline")
    require(rights["baseline_identities_superseded_by_locator_bearing_text_review_count"], 9, "metrics rights superseded")
    require(rights["locator_bearing_text_review_outside_baseline_queue_count"], 1, "metrics rights outside baseline")
    require(rights["locator_bearing_text_review_outside_baseline_source_ids"], ["R16-SRC-005"], "metrics rights outside-baseline identity")
    require(rights["baseline_review_records_not_text_completion_count"], 2, "metrics baseline noncompletion review count")
    require(rights["baseline_review_records_not_text_completion_source_ids"], ["COMP-SRC-017", "COMP-SRC-023"], "metrics baseline noncompletion source IDs")
    require(rights["known_canonical_identity_union_count"], 95, "metrics rights identity union")
    require(rights["review_record_count"], 12, "metrics source review record count")
    require(rights["rights_text_completion_count"], 10, "metrics rights text completion count")
    require(rights["incomplete_review_record_count"], 2, "metrics incomplete review record count")
    require(rights["current_unresolved_canonical_identity_count"], 85, "metrics current unresolved rights count")
    require(rights["current_unresolved_canonical_identity_id_set_sha256"], model["set_hashes"]["rights_open"], "metrics unresolved rights hash")

    metadata = metrics["metadata"]
    require(metadata["baseline_lead_count"], 101, "metrics metadata baseline")
    require(metadata["superseded_by_text_review_count"], 1, "metrics metadata superseded")
    require(metadata["current_metadata_only_unreviewed_count"], 100, "metrics current metadata-only count")
    require(metadata["current_metadata_only_unreviewed_id_set_sha256"], model["set_hashes"]["metadata_open"], "metrics unresolved metadata hash")

    human = metrics["human_authority"]
    require(human["legacy_not_completed_count"], 36, "metrics legacy human blockers")
    require(human["round16b_hypothesis_external_review_open_count"], 11, "metrics Round 16B human blockers")
    require(human["current_record_level_blocker_count"], 47, "metrics current human blockers")
    require(human["namespaced_member_format"], "LEGACY:<review_unit_id>|R16B:<hypothesis_id>", "metrics human namespace")
    require(human["current_record_level_blocker_id_set_sha256"], model["set_hashes"]["human"], "metrics human blocker hash")

    require(metrics["semantic_bounds"]["higher_order_semantic_obligation_count"], 9, "metrics semantic parameter count")
    require(metrics["semantic_bounds"]["parameter_name_set_sha256"], model["set_hashes"]["parameters"], "metrics semantic parameter hash")
    require(metrics["semantic_bounds"]["product_maximum_arity_audited"], False, "metrics product maximum audit")
    vocab = metrics["vocabulary_reachability"]
    require(vocab["active_noncomposable_vocabulary_count"], 5, "metrics active noncomposable vocabulary")
    require(vocab["vocabulary_id_set_sha256"], model["set_hashes"]["vocab"], "metrics active noncomposable vocabulary hash")
    require(vocab["higher_order_composability_proven_count"], 0, "metrics higher-order composability proven count")
    require(vocab["active_product_path_count"], 0, "metrics active product path count")

    boundary = metrics["checkpoint011_capability_boundary"]
    require(boundary["database_replay_status"], "PASS", "metrics Checkpoint 011 replay")
    require(boundary["normalized_database_schemas_identical"], True, "metrics Checkpoint 011 schema identity")
    require(boundary["runtime_independent_status"], "PASS", "metrics Checkpoint 011 runtime")
    require(boundary["production_activation_count"], 0, "metrics Checkpoint 011 production activation")
    require(boundary["active_pending_review_count"], 0, "metrics Checkpoint 011 active pending review")
    require(boundary["active_product_record_count"], 0, "metrics Checkpoint 011 active product records")
    require(boundary["production_data_imported"], False, "metrics Checkpoint 011 production import")
    require(boundary["production_activation_performed"], False, "metrics Checkpoint 011 activation")
    require(boundary["deployment_performed"], False, "metrics Checkpoint 011 deployment")
    require(boundary["research_capability_is_historical_closure"], False, "metrics capability/closure distinction")

    projection = metrics["headline_receipt_projection"]
    require(projection, {
        "unresolved_association_count": 11,
        "active_pending_review_count": 0,
        "unexplained_exclusion_count": 9,
        "unexplained_exclusion_count_scope": "KNOWN_RESEARCH_ONLY_SENSE_COVERAGE_GAPS_ONLY",
        "universe_wide_unexplained_exclusion_count": "INDETERMINATE",
        "active_noncomposable_vocabulary_count": 5,
    }, "metrics headline projection")
    require(metrics["closure"], {key: False for key in CLOSURE_KEYS}, "metrics closure flags")
    require(metrics["closure_true_count"], 0, "metrics true closure count")
    require(metrics["independent_verification_status"], "PENDING_SEPARATE_IMPLEMENTATION", "primary/independent ownership boundary")
    assert_fail_closed_view(headline_view(model))
    return {
        "metrics_sha256": sha256_file(METRICS_PATH),
        "status": metrics["status"],
        "closure_true_count": metrics["closure_true_count"],
    }


def verify_primary_build_receipt() -> dict[str, Any]:
    receipt = read_json(BUILD_RECEIPT_PATH)
    primary_without_receipt = (
        INPUT_MANIFEST_PATH, SUPERSESSION_PATH, OBLIGATION_PATH, METRICS_PATH,
    )
    hashes = {relative: sha256_file(relative) for relative in sorted(primary_without_receipt)}
    require(receipt["format"], "trace-round16b-recursive-gap-closure-build-receipt-checkpoint012-v2", "primary receipt format")
    require(receipt["builder_version"], "trace-round16b-recursive-gap-closure-audit-builder-v2", "primary receipt builder version")
    require(receipt["authority_base_sha"], AUTHORITY_BASE_SHA, "primary receipt authority SHA")
    require(receipt["authority_base_tree"], AUTHORITY_BASE_TREE, "primary receipt authority tree")
    require(receipt["source_sha"], SOURCE_SHA, "primary receipt source SHA")
    require(receipt["source_tree"], SOURCE_TREE, "primary receipt source tree")
    require(receipt["builder_sha256"], sha256_file(PRIMARY_BUILDER_PATH), "primary builder SHA-256")
    require(receipt["status"], "PASS_EVIDENCE_BOUNDED_NONCLOSURE", "primary build receipt status")
    require(receipt["input_count"], 36, "primary receipt input count")
    require(receipt["primary_output_count_excluding_receipt"], 4, "primary receipt output count")
    require(receipt["primary_output_sha256"], hashes, "primary receipt output hashes")
    require(receipt["primary_output_aggregate_sha256"], sha256_bytes(canonical_json(hashes).encode("utf-8")), "primary output aggregate hash")
    require(receipt["supersession_prior_record_count"], 414, "primary receipt supersession count")
    require(receipt["supersession_membership_id_set_sha256"], EXPECTED_SET_HASHES["supersession"], "primary receipt supersession hash")
    require(receipt["current_obligation_class_count"], 16, "primary receipt obligation class count")
    require(receipt["unresolved_association_count"], 11, "primary receipt unresolved associations")
    require(receipt["active_pending_review_count"], 0, "primary receipt active pending review")
    require(receipt["rights_baseline_text_completed_count"], 9, "primary receipt baseline rights text completion")
    require(receipt["rights_current_unresolved_count"], 85, "primary receipt unresolved rights")
    require(receipt["metadata_text_superseded_count"], 1, "primary receipt metadata text supersession")
    require(receipt["metadata_current_unreviewed_count"], 100, "primary receipt unreviewed metadata")
    require(receipt["known_unexplained_exclusion_count"], 9, "primary receipt known exclusion gaps")
    require(receipt["universe_wide_unexplained_exclusion_count"], "INDETERMINATE", "primary receipt universe exclusion total")
    require(receipt["active_noncomposable_vocabulary_count"], 5, "primary receipt active noncomposable vocabulary")
    require(receipt["closure_flags_true_count"], 0, "primary receipt closure flags")
    for key in (
        "history_rewritten", "force_push_used", "origin_main_rewritten",
        "rollback_tag_pushed", "deployment_performed",
    ):
        require(receipt[key], False, f"primary receipt {key}")
    return {
        "receipt_sha256": sha256_file(BUILD_RECEIPT_PATH),
        "primary_artifact_sha256": {
            **hashes,
            BUILD_RECEIPT_PATH: sha256_file(BUILD_RECEIPT_PATH),
        },
        "primary_output_aggregate_sha256": receipt["primary_output_aggregate_sha256"],
    }


def independent_metrics(model: dict[str, Any]) -> dict[str, Any]:
    return {
        "unresolved_association_count": 11,
        "unresolved_association_count_scope": "CURRENT_SCOPED_ASSOCIATION_HYPOTHESES",
        "hypothesis_arity_distribution": {str(key): value for key, value in sorted(model["hypothesis_arity"].items())},
        "governed_association_identity_count": 4,
        "ungoverned_hypothesis_count": 7,
        "active_association_count": 0,
        "active_pending_review_count": 0,
        "product_eligible_association_count": 0,
        "implicit_pair_projection_count": 0,
        "association_review_queue_baseline_count": 59,
        "association_review_queue_terminal_control_count": 13,
        "association_review_queue_derivative_reconciled_successor_open_count": 7,
        "association_review_queue_current_open_count": 39,
        "rights_baseline_canonical_identity_count": 94,
        "rights_locator_bearing_text_review_matched_to_baseline_count": 9,
        "rights_locator_bearing_text_review_outside_baseline_count": 1,
        "rights_review_record_count": 12,
        "rights_text_completion_count": 10,
        "rights_incomplete_review_record_count": 2,
        "rights_known_canonical_identity_union_count": 95,
        "rights_current_unresolved_canonical_identity_count": 85,
        "metadata_baseline_lead_count": 101,
        "metadata_superseded_by_text_review_count": 1,
        "metadata_current_unreviewed_count": 100,
        "legacy_human_review_blocker_count": 36,
        "round16b_hypothesis_human_review_blocker_count": 11,
        "current_namespaced_human_review_blocker_count": 47,
        "open_nary_participant_resolution_count": 10,
        "semantic_parameter_obligation_count": 9,
        "research_only_sense_count": 21,
        "covered_research_only_sense_count": 12,
        "known_unexplained_exclusion_count": 9,
        "known_unexplained_exclusion_count_scope": "RESEARCH_ONLY_SENSES_WITHOUT_TRIGGER_HYPOTHESIS_PARTICIPANT_OBLIGATION_OR_EXCLUSION",
        "universe_wide_unexplained_exclusion_count": "INDETERMINATE",
        "candidate_exclusion_proof_record_count": 0,
        "active_noncomposable_vocabulary_count": 5,
        "governed_product_maximum_arity": None,
        "round16a_association_subgraph_count": 58,
        "round16a_semantic_carry_forward_authorized_count": 0,
        "production_activation_count": 0,
        "closure": {key: False for key in CLOSURE_KEYS},
    }


def build_independent_receipt() -> tuple[dict[str, Any], dict[str, Any]]:
    separation = verify_implementation_separation()
    manifest = verify_input_manifest()
    model = reconstruct_model()
    obligations = verify_obligation_ledger(model)
    supersession = verify_supersession_ledger(model)
    metrics = verify_metrics(model, supersession)
    primary = verify_primary_build_receipt()
    probes = run_adversarial_probes(model)
    checks = {
        "implementation_separation": "PASS",
        "input_manifest_and_committed_trust_anchors": "PASS",
        "input_manifest_authority_boundaries": "PASS",
        "current_hypothesis_reconstruction": "PASS",
        "association_arity_reconstruction": "PASS",
        "governed_ungoverned_identity_partition": "PASS",
        "association_review_queue_partition": "PASS",
        "rights_baseline_current_supersession": "PASS",
        "rights_locator_bearing_text_completion_predicate": "PASS",
        "metadata_baseline_current_supersession": "PASS",
        "human_authority_namespaced_union": "PASS",
        "research_only_sense_coverage": "PASS",
        "exclusion_proof_boundary": "PASS",
        "active_vocabulary_reachability": "PASS",
        "semantic_bound_obligations": "PASS",
        "round16a_semantic_quarantine": "PASS",
        "checkpoint011_capability_nonclosure_boundary": "PASS",
        "complete_prior_record_supersession": "PASS",
        "every_gap_semantic_disposition_and_successor_route": "PASS",
        "every_prior_status_structured_projection": "PASS",
        "current_obligation_membership": "PASS",
        "current_obligation_exact_semantic_contract": "PASS",
        "primary_metrics_reconciliation": "PASS",
        "primary_output_byte_seals": "PASS",
        "fail_closed_adversarial_probes": "PASS",
    }
    receipt = {
        "format": "trace-round16b-recursive-gap-closure-independent-verification-checkpoint012-v2",
        "verifier_version": VERIFIER_VERSION,
        "authority": {
            "checkpoint011_sha": AUTHORITY_BASE_SHA,
            "checkpoint011_tree": AUTHORITY_BASE_TREE,
            "source_sha": SOURCE_SHA,
            "source_tree": SOURCE_TREE,
            "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
            "work_branch": WORK_BRANCH,
        },
        "status": "PASS_FOR_EVIDENCE_BOUNDED_NONCLOSURE_DECISION",
        "implementation_independence": separation,
        "input_verification": manifest,
        "primary_artifact_verification": primary,
        "supersession_verification": supersession,
        "current_obligation_verification": obligations,
        "primary_metrics_verification": metrics,
        "independent_metrics": independent_metrics(model),
        "independent_set_hashes": {
            **dict(sorted(model["set_hashes"].items())),
            "supersession": supersession["membership_id_set_sha256"],
        },
        "checks": checks,
        "check_count": len(checks),
        "adversarial_probes": probes,
        "adversarial_probe_count": len(probes),
        "closure": {key: False for key in CLOSURE_KEYS},
        "closure_true_count": 0,
        "reproducibility_status": "PASS_PINNED_COMMITTED_INPUT_AND_GENERATED_BYTE_REPRODUCTION_FINAL_CLEAN_WORKTREE_GATE_PENDING",
        "limitations": [
            "This verifier proves the scoped census and evidence-bounded non-closure decision; it does not prove universe-wide candidate completeness.",
            "The universe-wide unexplained-exclusion count remains INDETERMINATE because no complete complement proof exists.",
            "No external design historian supplied activation authority.",
            "No new scholarly search or source-text review was performed in this computational checkpoint.",
            "Reviewed remote source payloads were not committed, leaving source-byte reproduction open.",
            "Final clean-worktree reproduction and full repository gates remain Checkpoint 013 work.",
            "Branch-tip, clean-worktree, commit, and publication fields cannot be finalized before the Checkpoint 012 commit and ordinary push.",
        ],
        "history_rewritten": False,
        "force_push_used": False,
        "origin_main_rewritten": False,
        "rollback_tag_pushed": False,
        "deployment_performed": False,
    }
    return receipt, model


def render_report(receipt: dict[str, Any], receipt_sha256: str, model: dict[str, Any]) -> bytes:
    metrics = receipt["independent_metrics"]
    supersession = receipt["supersession_verification"]
    obligation = receipt["current_obligation_verification"]
    primary_hashes = receipt["primary_artifact_verification"]["primary_artifact_sha256"]
    primary_table = "\n".join(
        f"| `{path}` | `{digest}` |" for path, digest in sorted(primary_hashes.items())
    )
    kind_table = "\n".join(
        f"| {kind} | {count} |" for kind, count in supersession["prior_kind_distribution"].items()
    )
    disposition_table = "\n".join(
        f"| {kind} | {count} |" for kind, count in supersession["current_disposition_distribution"].items()
    )
    closure_lines = "\n".join(
        f"{key.upper()}=false" for key in CLOSURE_KEYS
    )
    text = f"""# Checkpoint 012: recursive gap audit and evidence-bounded non-closure decision

Authority base: `{AUTHORITY_BASE_SHA}` (`{AUTHORITY_BASE_TREE}`). Authorized Round 16A source: `{SOURCE_SHA}` (`{SOURCE_TREE}`). Work branch: `{WORK_BRANCH}`. Expected unchanged `origin/main`: `{EXPECTED_ORIGIN_MAIN_SHA}`.

## Decision

Function 3 is **not closed**. The complete governed prior-record census is superseded into explicit current obligations, but current evidence does not establish candidate-universe completeness, higher-order group closure, global composition coherence, product reachability, or computational closure. Checkpoint 011's database and runtime capability remains a zero-production-activation capability result, not a historical closure result.

The primary build and a separate stdlib-only verifier agree byte-for-byte and by independently reconstructed source sets. The verifier does not import, invoke, or reuse the primary builder's enumeration. It passes {receipt['check_count']} named checks and all {receipt['adversarial_probe_count']} adversarial and normalization controls. Independent receipt SHA-256: `{receipt_sha256}`.

## Current evidence-bounded census

| Measure | Current result | Boundary |
|---|---:|---|
| Current scoped association hypotheses | {metrics['unresolved_association_count']} | 3 arity-2, 6 arity-3, 1 arity-4, 1 arity-5 |
| Governed association identities | {metrics['governed_association_identity_count']} | Identity exists; none is active or product eligible |
| Ungoverned hypotheses | {metrics['ungoverned_hypothesis_count']} | Exact association identity remains unresolved |
| Active associations | {metrics['active_association_count']} | Zero |
| Active pending review | {metrics['active_pending_review_count']} | Zero; any nonzero value blocks verification |
| Implicit hyperedge pair projections | {metrics['implicit_pair_projection_count']} | Zero |
| Open association-review rows | {metrics['association_review_queue_current_open_count']} | Queue rows are not association identities |
| Open n-ary participant resolutions | {metrics['open_nary_participant_resolution_count']} | Exact participant sets remain unresolved |
| Semantic/product-bound parameters | {metrics['semantic_parameter_obligation_count']} | No governed product maximum arity exists |
| Active noncomposable vocabulary | {metrics['active_noncomposable_vocabulary_count']} | Inherited active, zero pair degree, zero active v3 product path |

The eleven hypotheses are the current scoped unresolved-association count. They must not be collapsed to the four records that already carry governed association IDs: identity governance does not resolve evidence, global coherence, human authority, activation, or product eligibility.

## Candidate-universe and exclusion-proof boundary

There are {metrics['research_only_sense_count']} governed research-only senses. Twelve appear in at least one governed trigger, scoped hypothesis, n-ary participant obligation, or explicit exclusion. Nine do not. Their exact ID-set SHA-256 is `{receipt['independent_set_hashes']['uncovered_research']}`. The exclusion ledger contains zero proof rows.

`KNOWN_UNEXPLAINED_EXCLUSION_COUNT=9` is therefore a scoped lower bound, not a universe-wide total. `UNIVERSE_WIDE_UNEXPLAINED_EXCLUSION_COUNT=INDETERMINATE` remains mandatory until trigger completeness and the candidate-complement proof are established. This checkpoint cannot truthfully set candidate-universe closure.

## Rights, metadata, and human authority

- Rights: 94 baseline canonical identities, 9 superseded by committed locator-bearing full-text, accepted-manuscript, or author-PDF review, and 85 currently unresolved baseline identities. Of 12 committed review records, 10 satisfy the rights/text completion predicate; `R16-SRC-005` is the one qualifying review outside the baseline. `COMP-SRC-023` and `COMP-SRC-017` remain open because their records are abstract-only or explicitly leave full-text review open.
- Metadata: 101 baseline leads, 1 superseded by locator-bearing source-text review, and 100 still metadata-only and unreviewed. `COMP-SRC-017` remains open; DOI and abstract-row presence is not source-text review. Metadata is not association evidence.
- Human authority: 36 incomplete legacy review units plus 11 current Round 16B hypothesis reviews produce 47 disjoint namespaced blockers. The hash uses `LEGACY:<review_unit_id>` and `R16B:<hypothesis_id>` records and is `{receipt['independent_set_hashes']['human']}`.

The corrected current counts are 85, 100, and 47. The stale baseline-only counts 94, 101, and 36 are retained as provenance but rejected as current blocker totals.

## Complete supersession census

Every one of the 414 physical prior rows has exactly one stable key using `kind<TAB>repo_relative_path<TAB>prior_id`, one source-row locator, one source-record hash, and one current disposition. Membership SHA-256: `{supersession['membership_id_set_sha256']}`.

Every source status field is retained as a canonical JSON projection rather than collapsed to the first generic status. In particular, all 94 rights rows preserve `rights_review_status`, `text_access_status`, `locator_review_status`, and `association_evidence_status`; none is `UNSPECIFIED`. The independent verifier checks the exact projection for every prior row. It also checks the exact semantic disposition and successor-obligation set for each of the 105 physical GAP rows; their independent route-set SHA-256 is `{supersession['gap_semantic_route_id_set_sha256']}`. Aggregate-preserving successor swaps are rejected.

| Prior kind | Rows |
|---|---:|
{kind_table}

| Current disposition | Rows |
|---|---:|
{disposition_table}

All open or partially reconciled rows name at least one of the {obligation['record_count']} open current obligation classes. For every class, the verifier independently checks its exact class, count semantics, member kind, evidence paths, required action, and closure-blocker set in addition to its members and hashes. Terminal, resolved-technical, and preserved-historical rows carry no positive closure inference. Every closure flag has at least one explicit current blocker.

## Deterministic artifacts

| Primary artifact | SHA-256 |
|---|---|
{primary_table}

The input manifest contains 36 exact governed inputs. Three unchanged Checkpoint 011 capability artifacts are pinned to hashes recomputed from the committed `{AUTHORITY_BASE_SHA}` bytes. The corrected Round 16A census and refreshed v3 runtime independent receipt are separately pinned as Checkpoint 012 prerequisite corrections. The database manifest is pinned as the Checkpoint 015 checkout-portability correction; that correction changes verifier path validation only and does not change SQL, the normalized schema hash, or any closure result. Primary check mode and independent check mode must reproduce these exact files without rewriting them.

## Closure receipt

```text
SOURCE_SHA={SOURCE_SHA}
WORK_BRANCH={WORK_BRANCH}
CHECKPOINT012_AUTHORITY_BASE_SHA={AUTHORITY_BASE_SHA}
CHECKPOINT012_FINAL_LOCAL_SHA=PENDING_CHECKPOINT_COMMIT
CHECKPOINT012_FINAL_REMOTE_SHA=PENDING_ORDINARY_PUBLICATION
REMOTE_MAIN_SHA_EXPECTED={EXPECTED_ORIGIN_MAIN_SHA}
WORKTREE_CLEAN=PENDING_POST_COMMIT_VERIFICATION

{closure_lines}

UNRESOLVED_ASSOCIATION_COUNT=11
UNRESOLVED_ASSOCIATION_COUNT_SCOPE=CURRENT_SCOPED_ASSOCIATION_HYPOTHESES
ACTIVE_PENDING_REVIEW_COUNT=0
KNOWN_UNEXPLAINED_EXCLUSION_COUNT=9
KNOWN_UNEXPLAINED_EXCLUSION_COUNT_SCOPE=RESEARCH_ONLY_SENSE_COVERAGE_GAPS_ONLY
UNEXPLAINED_EXCLUSION_COUNT=9
UNEXPLAINED_EXCLUSION_COUNT_SCOPE=KNOWN_RESEARCH_ONLY_SENSE_COVERAGE_GAPS
UNIVERSE_WIDE_UNEXPLAINED_EXCLUSION_COUNT=INDETERMINATE
ACTIVE_NONCOMPOSABLE_VOCABULARY_COUNT=5
INDEPENDENT_VERIFICATION_STATUS=PASS_FOR_EVIDENCE_BOUNDED_NONCLOSURE_DECISION
REPRODUCIBILITY_STATUS=PASS_PINNED_COMMITTED_INPUT_AND_GENERATED_BYTE_REPRODUCTION_FINAL_CLEAN_WORKTREE_GATE_PENDING

FORCE_PUSH_USED=false
HISTORY_REWRITTEN=false
ORIGIN_MAIN_REWRITTEN=false
ROLLBACK_TAG_PUSHED=false
DEPLOYMENT_PERFORMED=false
```

## Checkpoint limitation and next boundary

This is a deterministic evidence census and non-closure decision. It performs no new scholarly search, source-text review, human design-history adjudication, production population, deployment, history rewrite, force push, main update, or tag publication. Reviewed remote payload bytes remain outside the repository. The universe-wide exclusion total is indeterminate. Final clean-worktree reproduction, full repository/build/API/database/LFS/audit-seal gates, checkpoint commit, ordinary push, and post-publication branch-tip verification remain later controlled steps; the pending receipt fields above must not be replaced until those events occur.
"""
    return text.encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    receipt, model = build_independent_receipt()
    receipt_payload = json_bytes(receipt)
    report_payload = render_report(receipt, sha256_bytes(receipt_payload), model)
    return {
        INDEPENDENT_RECEIPT_PATH: receipt_payload,
        REPORT_PATH: report_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="compare verifier-owned output bytes without rewriting them",
    )
    args = parser.parse_args()
    outputs = build_outputs()
    mismatches = []
    for relative, payload in sorted(outputs.items()):
        path = REPO / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != payload:
                mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    result = {
        "status": "PASS" if not mismatches else "FAIL",
        "mode": "CHECK" if args.check else "WRITE",
        "verifier_version": VERIFIER_VERSION,
        "verifier_owned_artifact_count": len(outputs),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }
    print(canonical_json(result))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
