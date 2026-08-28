#!/usr/bin/env python3
"""Build the Round 16B recursive-gap audit and fail-closed non-closure census.

The builder consolidates every governed prior gap, queue, and obligation row
without treating old status labels as current facts.  Later rights and source
reviews are joined to their baseline queues, but an unresolved review is never
promoted to an association, pair projection, or product fact.

The independent verifier owns the final report and independent receipt.  This
script writes only the five primary artifacts and supports a read-only
``--check`` mode.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW_REL = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
RAW = REPO / RAW_REL

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
AUTHORITY_BASE_SHA = "11412d23e309a647a3a2fb0b3db4369dcdd15993"
AUTHORITY_BASE_TREE = "9117d6fc189b8c8a986f6ba26e6879184d58eb12"
EXPECTED_ORIGIN_MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
BUILDER_VERSION = "trace-round16b-recursive-gap-closure-audit-builder-v2"

INPUT_MANIFEST_PATH = f"{RAW_REL}/recursive-gap-input-manifest-checkpoint012-v1.tsv"
SUPERSESSION_PATH = f"{RAW_REL}/recursive-gap-supersession-ledger-checkpoint012-v1.tsv"
OBLIGATION_PATH = f"{RAW_REL}/recursive-gap-current-obligation-ledger-checkpoint012-v1.tsv"
METRICS_PATH = f"{RAW_REL}/recursive-gap-closure-metrics-checkpoint012-v1.json"
BUILD_RECEIPT_PATH = f"{RAW_REL}/recursive-gap-closure-build-receipt-checkpoint012-v1.json"

GAP_PATHS = [
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
]
ASSOCIATION_QUEUE_PATHS = [
    f"{RAW_REL}/conditional-scoped-child-reroute-queue-tranche-a-v1.tsv",
    f"{RAW_REL}/conditional-scoped-child-reroute-queue-tranche-b-v1.tsv",
    f"{RAW_REL}/scoped-higher-order-review-queue-tranche-c-v1.tsv",
]
RIGHTS_QUEUE_PATH = f"{RAW_REL}/source-canonical-rights-queue-v2.tsv"
PARTICIPANT_QUEUE_PATH = f"{RAW_REL}/open-participant-resolution-ledger-v1.tsv"
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
HYPOTHESIS_PATHS = [
    f"{RAW_REL}/scoped-association-hypothesis-ledger-shard-1-v1.tsv",
    f"{RAW_REL}/scoped-association-hypothesis-ledger-shard-2-v1.tsv",
]
RIGHTS_REVIEW_PATHS = [
    f"{RAW_REL}/source-rights-ledger-shard-1-v1.tsv",
    f"{RAW_REL}/source-rights-ledger-shard-2-v2.tsv",
]
ISOLATED_PATH = f"{RAW_REL}/isolated-active-term-audit-ledger-v1.tsv"
VOCAB_IMPACT_PATH = f"{RAW_REL}/active-vocabulary-evidence-impact-ledger-shard-2-v1.tsv"
LOCAL_FAMILY_PATH = f"{RAW_REL}/local-candidate-family-ledger-v2.tsv"
R16A_SUBGRAPH_PATH = f"{RAW_REL}/round16a-global-reconciliation-subgraphs-v1.tsv"
R16A_CENSUS_PATH = f"{RAW_REL}/round16a-global-reconciliation-census-v1.json"
V3_CENSUS_PATH = f"{RAW_REL}/v3-semantic-contract-census-v1.json"
V3_RUNTIME_INDEPENDENT_PATH = f"{RAW_REL}/v3-runtime-independent-verification-v1.json"
V50_REPLAY_PATH = f"{RAW_REL}/v50-round16b-replay-receipt-checkpoint011.json"
CP11_RECEIPT_PATH = f"{RAW_REL}/v50-v3-runtime-checkpoint011-receipt.json"
DB_MANIFEST_PATH = "database/schema-manifest-v50-round16b.json"

# Most hashes below were recomputed from ``git show 11412d23:<path>`` after
# checkpoint 011 was committed.  Two prerequisite receipts were then
# deterministically corrected in checkpoint 012: the Round 16A reconciliation
# census and the v3 runtime independent receipt.  Their exact current hashes
# are pinned here explicitly rather than treated as checkpoint-011 bytes.
PINNED_INPUT_SHA256 = {
    f"{RAW_REL}/recursive-gap-ledger-adaptive-source-shard-1-v1.tsv": "dfcf94990753ab8f7bcde4e3438de90f60fb8688b8777cf6f72f731d10ffe180",
    f"{RAW_REL}/recursive-gap-ledger-adaptive-source-shard-2-v1.tsv": "179e7896ad5fe6374303075da2072dc47afc3a2adb799f061d256e05126542fe",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint003-v1.tsv": "46198584dec1d637bb897c84d39e90a9c9b12dba1d4028974abc4c3f57126509",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint004-v2.tsv": "62c7ad95128682aecb8c19547ea926cba486494dbf074ae73b1fc74c60133bc1",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint005-tranche-a-v1.tsv": "d11be30cc6ffb2d62889fe4d5a86c325facaf5d803c29b59a1c8f92875990238",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint006-tranche-b-v1.tsv": "8198d9a7f8d0fea5651f3587da9d89db776640e086500f6e79f9889e07fecc9d",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint007-tranche-c-v1.tsv": "14272d3be247175fab22505dfba9309a122201dcc06e7615fcc4a63c577cbaa8",
    f"{RAW_REL}/recursive-gap-ledger-checkpoint008-v1.tsv": "ef1454bb34eddf58ef4be75d1838eba72de8ccaf3c4d2965b57ecb474637a4a1",
    f"{RAW_REL}/recursive-gap-ledger-round16a-global-reconciliation-v1.tsv": "c3ac9dc5b4509a83cef6842d0869f5afc6d93b99435ceca139e244cf22eba08d",
    f"{RAW_REL}/recursive-gap-ledger.tsv": "cc571fbd38cf196a09af92c1c159843b965e7f4926cfaebcd31759c17e3d0d1b",
    f"{RAW_REL}/conditional-scoped-child-reroute-queue-tranche-a-v1.tsv": "abedad8a6e3df9ac964d3c3c7ee6923e0af610ac0459b6c510cb2873f6403716",
    f"{RAW_REL}/conditional-scoped-child-reroute-queue-tranche-b-v1.tsv": "302394dab22ebc85800ac1555db633e3282f83c552026deacec32665ea16389d",
    f"{RAW_REL}/scoped-higher-order-review-queue-tranche-c-v1.tsv": "d7ff7c13d75ad0ba14c1f84490b021956a23137d6e926f655057f2ea2009e22e",
    RIGHTS_QUEUE_PATH: "fd8e8b48b1d0f8da1e4194828d0cc6f273fadb4ecbe147a7f5f9e2319f08b960",
    PARTICIPANT_QUEUE_PATH: "f680797194ef66b0520a7c3c730a2ad50acc28c1f5de992aeb46b63cec2fed5f",
    PARAMETER_PATH: "da45043f2414c9fd2f77c261507773ac3d768829d616b96a3db261518cb4a717",
    METADATA_PATH: "d566cec6043668fd628353c010a004fda5faf1bf2b6898fd7026323740383380",
    CROSSWALK_PATH: "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    TRIGGER_PATH: "1685e5bfdab735657ce78499b2597e6a20aecd7402d97f515b162a5d16009cd6",
    EXCLUSION_PATH: "e1a2082a85bb8a2c25c8ed3f26ce2fee3df9cd0a5ad834641cea7ca502c73b0d",
    ASSOCIATION_EVIDENCE_PATH: "890a99a18a384a7227713c42ad543915ce42df7194df9039195befae333ec62a",
    HYPOTHESIS_PATHS[0]: "f16deeca67663b05262640cba1512bb46acb0a36ffe8dcae006fd45dc475bed3",
    HYPOTHESIS_PATHS[1]: "5b7e04bde8fc0c91f7d141f0ecdccf23579394dafba21e33e91ad512f9ab5a4d",
    RIGHTS_REVIEW_PATHS[0]: "062b61c2ee532118716b088939fd2758fb8b002adfe5546f6d4c68ba155536ce",
    RIGHTS_REVIEW_PATHS[1]: "453a9b772b8c176eefe1fad5fdfa99c3b3a0316c070aa7a5d803f8fd4993a3eb",
    ISOLATED_PATH: "67eaf0d1a519163d6c6d54a1c728e9f3fdc502c6bac93b1b59b7593a384803d2",
    VOCAB_IMPACT_PATH: "22c9765705c197dd8b5e291d15a088377d71a37ef551fb3d6e73b73f15ad1b69",
    LOCAL_FAMILY_PATH: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    R16A_SUBGRAPH_PATH: "81a9c85fcb3a4bcb764ad9c816fbfe381d8eb84c99733463ca8bcf1f7bf4f81b",
    R16A_CENSUS_PATH: "f2196eef23c560e24fd373956af6e711687440203edc4e0c96ab5de90c8c4537",
    V3_CENSUS_PATH: "7df89f2248d169c1f4e6358425a7f01afbcdb27c02d1d0e3f583f35c67322c6e",
    V3_RUNTIME_INDEPENDENT_PATH: "4839c5bf5492762478e1562c203db0dffc4b62886e1689f6eb7d37e3af2c0c38",
    V50_REPLAY_PATH: "7034cf1474d1baeec36d09033f28e35ae2d58f754009ebe194f5a9102725b83b",
    CP11_RECEIPT_PATH: "b7b2e0560823071129cb4c3cc6afa71275f76df7c189962ab36265ef3fc9861b",
    EXTERNAL_REVIEW_PATH: "903369afab8486b9a7553898ef0cf1bcf858d87bea99bd96887e62aa17a478b6",
    DB_MANIFEST_PATH: "bac907114133ea9b261fdff426434365f020ba92bd0e377b8b2d9629438319c3",
}

OBL_CANDIDATE = "R16B-CURRENT-OBLIGATION:CANDIDATE_UNIVERSE_AND_EXCLUSION_PROOF"
OBL_NARY = "R16B-CURRENT-OBLIGATION:NARY_PARTICIPANT_RESOLUTION"
OBL_RIGHTS = "R16B-CURRENT-OBLIGATION:RIGHTS_AND_LAWFUL_TEXT"
OBL_METADATA = "R16B-CURRENT-OBLIGATION:METADATA_TO_TEXT_REVIEW"
OBL_HUMAN = "R16B-CURRENT-OBLIGATION:EXTERNAL_HUMAN_AUTHORITY"
OBL_SCOPE = "R16B-CURRENT-OBLIGATION:SCOPE_SENSE_AND_IDENTITY"
OBL_GROUP = "R16B-CURRENT-OBLIGATION:GLOBAL_GROUP_COHERENCE"
OBL_CULTURAL = "R16B-CURRENT-OBLIGATION:CULTURAL_TRANSFORMATION_REAUDIT"
OBL_VOCAB = "R16B-CURRENT-OBLIGATION:ACTIVE_VOCABULARY_REACHABILITY"
OBL_BOUND = "R16B-CURRENT-OBLIGATION:SEMANTIC_AND_PRODUCT_ARITY_BOUND"
OBL_R16A = "R16B-CURRENT-OBLIGATION:ROUND16A_SEMANTIC_RECONCILIATION"
OBL_PRODUCT = "R16B-CURRENT-OBLIGATION:PRODUCTION_POPULATION_AND_REACHABILITY"
OBL_PAIR = "R16B-CURRENT-OBLIGATION:PAIR_ASSOCIATION_REAUDIT"
OBL_PAYLOAD = "R16B-CURRENT-OBLIGATION:SOURCE_BYTE_REPRODUCIBILITY"
OBL_REPRO = "R16B-CURRENT-OBLIGATION:FINAL_CLEAN_REPRODUCTION_GATE"
OBL_QUEUE = "R16B-CURRENT-OBLIGATION:OPEN_ASSOCIATION_REVIEW_QUEUE"
ALL_OBLIGATIONS = {
    OBL_CANDIDATE, OBL_NARY, OBL_RIGHTS, OBL_METADATA, OBL_HUMAN, OBL_SCOPE,
    OBL_GROUP, OBL_CULTURAL, OBL_VOCAB, OBL_BOUND, OBL_R16A, OBL_PRODUCT,
    OBL_PAIR, OBL_PAYLOAD, OBL_REPRO, OBL_QUEUE,
}

CLOSURE_KEYS = [
    "pair_association_closure",
    "higher_order_association_closure",
    "global_composition_coherence_closure",
    "product_association_reachability_closure",
    "computational_space_closure",
    "function3_closure",
]

INPUT_FIELDS = [
    "ordinal", "path", "selector", "record_count", "bytes", "sha256",
    "authority_boundary",
]
SUPERSESSION_FIELDS = [
    "prior_record_key", "prior_kind", "source_path", "source_row_number",
    "prior_id", "prior_status", "prior_record_sha256", "current_disposition",
    "successor_obligation_ids_json", "successor_artifact_refs_json",
    "closure_effect", "record_sha256",
]
OBLIGATION_FIELDS = [
    "obligation_id", "obligation_class", "status", "severity", "count_semantics",
    "member_kind", "member_count", "member_ids_sha256", "member_ids_json",
    "evidence_paths_json", "required_action", "blocks_closures_json",
    "record_sha256",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_hash(row: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(row).encode("utf-8"))


def id_set_hash(values: Iterable[str]) -> str:
    unique = sorted(set(values))
    return sha256_bytes(("".join(f"{value}\n" for value in unique)).encode("utf-8"))


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


def tsv_bytes(fields: list[str], rows: Iterable[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect="excel-tab")
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"missing or duplicate TSV fields: {relative}")
        return list(reader)


def read_json(relative: str) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key in {relative}: {key}")
            result[key] = value
        return result

    return json.loads((REPO / relative).read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def parse_json_list(value: str, context: str) -> list[str]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(f"expected string-array JSON: {context}")
    return parsed


def record_count(relative: str) -> int:
    return len(read_tsv(relative)) if relative.endswith(".tsv") else 1


def verify_inputs() -> None:
    if len(PINNED_INPUT_SHA256) != 36:
        raise ValueError("input pin count drift")
    for relative, expected in PINNED_INPUT_SHA256.items():
        observed = sha256_file(REPO / relative)
        if observed != expected:
            raise ValueError(f"pinned input drift: {relative}: {observed} != {expected}")


def input_manifest() -> list[dict[str, str]]:
    rows = []
    for ordinal, relative in enumerate(sorted(PINNED_INPUT_SHA256), 1):
        rows.append({
            "ordinal": str(ordinal),
            "path": relative,
            "selector": "ALL_TSV_ROWS" if relative.endswith(".tsv") else "WHOLE_JSON_DOCUMENT",
            "record_count": str(record_count(relative)),
            "bytes": str((REPO / relative).stat().st_size),
            "sha256": PINNED_INPUT_SHA256[relative],
            "authority_boundary": (
                "CHECKPOINT012_CORRECTED_ROUND16A_RECONCILIATION_BYTES"
                if relative == R16A_CENSUS_PATH else
                "CHECKPOINT012_REFRESHED_RUNTIME_VERIFICATION_BYTES"
                if relative == V3_RUNTIME_INDEPENDENT_PATH else
                "COMMITTED_CHECKPOINT011_BYTES" if relative in {
                    V3_CENSUS_PATH, V50_REPLAY_PATH,
                    CP11_RECEIPT_PATH, DB_MANIFEST_PATH,
                } else "COMMITTED_ROUND16B_PRE_CHECKPOINT011_BYTES"
            ),
        })
    return rows


def hypothesis_records() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative in HYPOTHESIS_PATHS:
        for source in read_tsv(relative):
            hypothesis_id = source["hypothesis_id"]
            association_id = source.get("governed_association_id") or source.get("association_id") or ""
            association_revision_id = (
                source.get("governed_association_revision_id")
                or source.get("association_revision_id") or ""
            )
            activation = source.get("association_activation_status") or source.get("activation_status") or ""
            human = source["external_human_review_status"]
            product = source.get("product_eligible")
            if product is None:
                product = "true" if source.get("product_eligibility", "").startswith("ELIGIBLE") else "false"
            participants = parse_json_list(
                source["participant_sense_ids_json"], f"{relative}:{hypothesis_id}"
            )
            result.append({
                "source_path": relative,
                "hypothesis_id": hypothesis_id,
                "association_id": association_id,
                "association_revision_id": association_revision_id,
                "arity": int(source["arity"]),
                "participant_sense_ids": participants,
                "activation_status": activation,
                "external_human_review_status": human,
                "product_eligible": product,
            })
    ids = [row["hypothesis_id"] for row in result]
    if len(result) != 11 or len(set(ids)) != 11:
        raise ValueError("scoped hypothesis identity regression")
    if any(bool(row["association_id"]) != bool(row["association_revision_id"]) for row in result):
        raise ValueError("association identity/revision governance parity regression")
    if any(
        len(row["participant_sense_ids"]) != row["arity"]
        or len(set(row["participant_sense_ids"])) != row["arity"]
        for row in result
    ):
        raise ValueError("hypothesis participant arity or uniqueness regression")
    if any(row["activation_status"] not in {"INACTIVE", "INQUIRY_ONLY"} for row in result):
        raise ValueError("a scoped hypothesis is unexpectedly active")
    if any(row["external_human_review_status"] not in {"OPEN", "PENDING_NOT_ACTIVE"} for row in result):
        raise ValueError("a scoped hypothesis no longer has an open external review boundary")
    if any(row["product_eligible"] != "false" for row in result):
        raise ValueError("a scoped hypothesis is unexpectedly product eligible")
    return result


def stable_http_locators(values: list[str]) -> bool:
    return bool(values) and all(
        value.startswith(("https://", "http://")) and " " not in value
        for value in values
    )


def rights_text_completion_eligible(source: dict[str, str], relative: str) -> bool:
    """Fail closed unless a committed review proves lawful locator-bearing text review.

    A review-row presence, DOI match, public abstract, or ``FULL_TEXT_OPEN``
    marker is not completion.  The two source-review shards have different
    schemas, so each is checked against its own concrete access, text-review,
    locator, retention, and rights fields.  Abstract-only terminal negatives
    would require an explicit governed terminal-negative status and no further
    source-text action; no current row satisfies that exceptional rule.
    """
    access = source.get("access_status", "")
    status_projection = "\n".join(
        value for key, value in sorted(source.items())
        if (key == "status" or key.endswith("_status")) and value
    )
    if any(token in status_projection for token in (
        "ABSTRACT_ONLY", "ABSTRACT_REVIEWED", "FULL_TEXT_OPEN",
        "FULL_TEXT_NOT_ESTABLISHED", "NOT_REVIEWED",
    )):
        return False

    if relative == RIGHTS_REVIEW_PATHS[0]:
        allowed_access = {
            "PUBLIC_ACCEPTED_MANUSCRIPT_REVIEWED",
            "PUBLIC_PUBLISHED_FULL_TEXT_REVIEWED",
            "OPEN_ACCESS_PUBLISHED_FULL_TEXT_REVIEWED",
            "PUBLIC_AUTHOR_PDF_LAWFUL_READ_OBSERVED",
            "OPEN_ACCESS_PUBLISHED_PDF_REVIEWED",
            "PUBLISHER_FREE_ACCESS_FULL_TEXT_REVIEWED",
        }
        allowed_text_review = {
            "ACCEPTED_MANUSCRIPT_MULTI_LOCUS_REVIEWED",
            "PUBLISHED_TEXT_LOCATOR_REVIEWED",
            "PUBLISHED_TEXT_MULTI_SECTION_REVIEWED",
            "AUTHOR_PDF_ARTICLE_METHOD_AND_CASE_STRUCTURE_REVIEWED",
            "PUBLISHED_TEXT_MULTI_LOCUS_REVIEWED",
            "PUBLISHED_TEXT_EXACT_GROUP_LOCATOR_REVIEWED",
        }
        record_urls = parse_json_list(
            source.get("record_urls_json", "[]"),
            f"{relative}:{source.get('source_id', '')}:record_urls",
        )
        text_urls = parse_json_list(
            source.get("text_urls_json", "[]"),
            f"{relative}:{source.get('source_id', '')}:text_urls",
        )
        return bool(
            access in allowed_access
            and source.get("source_text_review_status") in allowed_text_review
            and stable_http_locators(record_urls)
            and stable_http_locators(text_urls)
            and source.get("rights_status")
            and source.get("rights_record_id")
            and source.get("payload_retained") == "false"
            and source.get("retention_decision")
            == "RETAIN_BIBLIOGRAPHIC_IDENTITY_URLS_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY"
            and source.get("redistribution_authorized")
            in {"false_or_not_established", "true_with_license_conditions"}
            and source.get("committed_material")
            == "NO_REMOTE_FULL_TEXT; NO_COPYRIGHTED_PAYLOAD; NO_EXTENDED_EXTRACT"
        )

    if relative == RIGHTS_REVIEW_PATHS[1]:
        retained_locator = source.get("retained_path_or_locator", "")
        locator_casefold = retained_locator.casefold()
        return bool(
            access in {
                "PUBLIC_PUBLISHER_FULL_TEXT_REVIEWED",
                "OPEN_ACCESS_PUBLISHER_FULL_TEXT_REVIEWED",
            }
            and source.get("review_status") == "COMPLETE_FAIL_CLOSED"
            and stable_http_locators([source.get("stable_url", "")])
            and retained_locator
            and ("pdf" in locator_casefold or "html" in locator_casefold)
            and "abstract only" not in locator_casefold
            and source.get("access_condition")
            and source.get("license_identifier")
            and source.get("copyright_or_rights_holder")
            and source.get("retained_material_type")
            == "BIBLIOGRAPHIC_IDENTITY_STABLE_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY"
            and source.get("retained_sha256") == "NOT_APPLICABLE_NO_SOURCE_PAYLOAD_RETAINED"
            and source.get("extract_word_count") == "0"
            and source.get("redistribution_authorized")
            in {"false", "true_with_attribution_conditions"}
            and source.get("rights_record_id")
        )

    raise ValueError(f"unexpected source-review shard: {relative}")


def reviewed_sources() -> list[dict[str, Any]]:
    result = []
    for relative in RIGHTS_REVIEW_PATHS:
        for source in read_tsv(relative):
            identifier = normalize_identifier(
                source.get("doi") or source.get("doi_or_identifier") or ""
            )
            result.append({
                "source_path": relative,
                "source_id": source["source_id"],
                "identifier": identifier,
                "rights_record_id": source["rights_record_id"],
                "access_status": source.get("access_status", ""),
                "text_review_status": (
                    source.get("source_text_review_status")
                    or source.get("review_status", "")
                ),
                "rights_text_completion_eligible": rights_text_completion_eligible(
                    source, relative,
                ),
            })
    if len(result) != 12 or len({row["source_id"] for row in result}) != 12:
        raise ValueError("reviewed source identity regression")
    eligible_ids = sorted(
        row["source_id"] for row in result
        if row["rights_text_completion_eligible"]
    )
    if len(eligible_ids) != 10 or set(eligible_ids) & {"COMP-SRC-017", "COMP-SRC-023"}:
        raise ValueError("locator-bearing source-text completion regression")
    return result


def rights_supersession(
    queue_rows: list[dict[str, str]], reviews: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]:
    queue_ids = [row["canonical_source_id"] for row in queue_rows]
    if len(queue_rows) != 94 or len(set(queue_ids)) != 94:
        raise ValueError("rights queue canonical identity uniqueness regression")
    matched: dict[str, list[dict[str, Any]]] = {}
    baseline_review_sources: set[str] = set()
    ineligible_baseline_sources: set[str] = set()
    review_to_canonical: dict[str, list[str]] = {}
    for queue in queue_rows:
        members = parse_json_list(
            queue["member_ids_json"], f"{RIGHTS_QUEUE_PATH}:{queue['canonical_source_id']}"
        )
        queue_identifier = normalize_identifier(queue["doi_isbn_or_identifier"])
        queue_source = queue["representative_source_record_id"]
        hits = []
        for review in reviews:
            source_id = review["source_id"]
            by_source = queue_source == source_id or any(member.endswith(f":{source_id}") for member in members)
            by_identifier = bool(review["identifier"] and review["identifier"] == queue_identifier)
            if by_source or by_identifier:
                hits.append(review)
                baseline_review_sources.add(source_id)
        if len(hits) > 1:
            raise ValueError(f"ambiguous rights supersession: {queue['canonical_source_id']}")
        if hits:
            review_to_canonical.setdefault(hits[0]["source_id"], []).append(
                queue["canonical_source_id"]
            )
            if hits[0]["rights_text_completion_eligible"]:
                matched[queue["canonical_source_id"]] = hits
            else:
                ineligible_baseline_sources.add(hits[0]["source_id"])
    ambiguous_reviews = {
        source_id: identities for source_id, identities in review_to_canonical.items()
        if len(identities) != 1
    }
    if ambiguous_reviews:
        raise ValueError(f"review maps to multiple canonical rights identities: {ambiguous_reviews}")
    outside = sorted(
        row["source_id"] for row in reviews
        if row["rights_text_completion_eligible"]
        and row["source_id"] not in baseline_review_sources
    )
    ineligible = sorted(ineligible_baseline_sources)
    if (
        len(queue_rows) != 94
        or len(review_to_canonical) != 11
        or len(matched) != 9
        or ineligible != ["COMP-SRC-017", "COMP-SRC-023"]
        or outside != ["R16-SRC-005"]
    ):
        raise ValueError("rights queue supersession regression")
    return matched, outside, ineligible


def metadata_supersession(
    metadata_rows: list[dict[str, str]], reviews: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    lead_ids = [row["metadata_lead_id"] for row in metadata_rows]
    if len(metadata_rows) != 101 or len(set(lead_ids)) != 101:
        raise ValueError("metadata lead identity uniqueness regression")
    matched: dict[str, list[dict[str, Any]]] = {}
    for lead in metadata_rows:
        doi = normalize_identifier(lead["canonical_doi"])
        hits = [
            row for row in reviews
            if row["rights_text_completion_eligible"]
            and row["identifier"]
            and row["identifier"] == doi
        ]
        if len(hits) > 1:
            raise ValueError(f"ambiguous metadata supersession: {lead['metadata_lead_id']}")
        if hits:
            matched[lead["metadata_lead_id"]] = hits
    if len(metadata_rows) != 101 or len(matched) != 1:
        raise ValueError("metadata supersession regression")
    return matched


def association_queue_partition() -> dict[str, list[dict[str, str]]]:
    partitions: dict[str, list[dict[str, str]]] = {
        "terminal_control": [], "derivative_reconciled": [], "current_open": [],
    }
    for relative in ASSOCIATION_QUEUE_PATHS:
        for row in read_tsv(relative):
            enriched = {**row, "_source_path": relative}
            if "CLOSED_PARENT" in row["queue_status"]:
                partitions["terminal_control"].append(enriched)
            elif row.get("queue_record_kind") == "DERIVATIVE_RECONCILIATION":
                partitions["derivative_reconciled"].append(enriched)
            else:
                partitions["current_open"].append(enriched)
    all_ids = [row["queue_id"] for rows in partitions.values() for row in rows]
    if len(all_ids) != 59 or len(set(all_ids)) != 59:
        raise ValueError("association review queue identity uniqueness regression")
    observed = {key: len(value) for key, value in partitions.items()}
    if observed != {"terminal_control": 13, "derivative_reconciled": 7, "current_open": 39}:
        raise ValueError(f"association review queue partition regression: {observed}")
    return partitions


def research_only_coverage(
    hypotheses: list[dict[str, Any]], participant_rows: list[dict[str, str]],
) -> tuple[dict[str, str], list[str]]:
    crosswalk = read_tsv(CROSSWALK_PATH)
    research = {
        row["participant_sense_id"]: row["canonical_label"]
        for row in crosswalk if row["disposition"] == "RESEARCH_ONLY"
    }
    covered: set[str] = set()
    for row in read_tsv(TRIGGER_PATH):
        covered.update(parse_json_list(
            row["participant_sense_ids_json"], f"{TRIGGER_PATH}:{row['trigger_occurrence_id']}"
        ))
    for row in hypotheses:
        covered.update(row["participant_sense_ids"])
    covered.update(row["relation_participant_sense_id"] for row in participant_rows)
    exclusions = read_tsv(EXCLUSION_PATH)
    for row in exclusions:
        covered.update(parse_json_list(
            row["participant_sense_ids_json"], f"{EXCLUSION_PATH}:{row['exclusion_id']}"
        ))
    missing = sorted(set(research) - covered)
    if len(research) != 21 or len(exclusions) != 0 or len(missing) != 9:
        raise ValueError("research-only sense coverage regression")
    expected_labels = {
        "access", "circulation", "collective production", "cultural diplomacy",
        "cultural transferral", "decolonization", "erasure", "translation",
        "work migrations",
    }
    if {research[sense_id] for sense_id in missing} != expected_labels:
        raise ValueError("unexpected uncovered research-only senses")
    return research, missing


def load_context() -> dict[str, Any]:
    verify_inputs()
    hypotheses = hypothesis_records()
    reviews = reviewed_sources()
    rights_queue = read_tsv(RIGHTS_QUEUE_PATH)
    metadata = read_tsv(METADATA_PATH)
    rights_matched, rights_outside, rights_ineligible_baseline = rights_supersession(
        rights_queue, reviews,
    )
    metadata_matched = metadata_supersession(metadata, reviews)
    queue_partition = association_queue_partition()
    participant_rows = read_tsv(PARTICIPANT_QUEUE_PATH)
    parameters = [
        row for row in read_tsv(PARAMETER_PATH)
        if row["higher_order_semantic_obligation"] == "true"
    ]
    if len(participant_rows) != 10 or any(
        row["participant_resolution_status"] != "OPEN" or row["candidate_emitted"] != "false"
        for row in participant_rows
    ):
        raise ValueError("n-ary participant obligation regression")
    if len(parameters) != 9:
        raise ValueError("semantic parameter obligation regression")
    research, uncovered_research = research_only_coverage(hypotheses, participant_rows)
    legacy_human = [
        row for row in read_tsv(EXTERNAL_REVIEW_PATH)
        if row["reviewer_answer_status"] == "NOT_COMPLETED"
    ]
    if len(legacy_human) != 36:
        raise ValueError("legacy external review count regression")
    vocab = [
        row for row in read_tsv(VOCAB_IMPACT_PATH)
        if row["active_product_path_count"] == "0"
        and row["active_association_count"] == "0"
        and row["higher_order_composability_proven"] == "false"
    ]
    isolated = read_tsv(ISOLATED_PATH)
    if (
        len(vocab) != 5
        or any(row["higher_order_composability_proven"] != "false" for row in isolated)
        or {row["vocabulary_id"] for row in vocab} != {
        row["vocabulary_id"] for row in isolated
        }
    ):
        raise ValueError("active noncomposable vocabulary regression")
    subgraphs = read_tsv(R16A_SUBGRAPH_PATH)
    if len(subgraphs) != 58 or any(
        row["semantic_carry_forward_authorized"] != "false"
        or row["active_fact_created"] != "false"
        or row["product_eligible"] != "false"
        for row in subgraphs
    ):
        raise ValueError("Round16A semantic carry-forward boundary regression")
    local_families = read_tsv(LOCAL_FAMILY_PATH)
    family_arity = Counter(int(row["arity"]) for row in local_families)
    if family_arity != Counter({3: 25, 4: 4, 6: 4, 5: 1, 8: 1}):
        raise ValueError("local candidate arity distribution regression")
    association_evidence = read_tsv(ASSOCIATION_EVIDENCE_PATH)
    if association_evidence:
        raise ValueError("canonical Round16B association-evidence ledger is unexpectedly populated")
    r16a_census = read_json(R16A_CENSUS_PATH)
    v3_census = read_json(V3_CENSUS_PATH)
    runtime = read_json(V3_RUNTIME_INDEPENDENT_PATH)
    replay = read_json(V50_REPLAY_PATH)
    cp11 = read_json(CP11_RECEIPT_PATH)
    database = read_json(DB_MANIFEST_PATH)
    if r16a_census["closure"] != {key: False for key in CLOSURE_KEYS}:
        raise ValueError("Round16A reconciliation closure boundary drift")
    if v3_census["production_activation_count"] != 0 or v3_census["production_active_pending_review_count"] != 0:
        raise ValueError("v3 semantic production boundary drift")
    if runtime["status"] != "PASS" or runtime["production_boundary"]["production_activation_count"] != 0:
        raise ValueError("v3 runtime independent boundary drift")
    if replay["status"] != "PASS" or not replay["normalizedSchemasIdentical"]:
        raise ValueError("v50 replay receipt regression")
    if cp11["status"] != "PASS_RESEARCH_CAPABILITY_CLOSURE_WITHHELD":
        raise ValueError("checkpoint011 capability receipt regression")
    if cp11["closure_flags"] != {key: False for key in CLOSURE_KEYS}:
        raise ValueError("checkpoint011 closure boundary drift")
    if database["productionDataImported"] or database["productionActivationPerformed"] or database["deploymentPerformed"]:
        raise ValueError("database production boundary drift")
    return {
        "hypotheses": hypotheses,
        "reviews": reviews,
        "rights_queue": rights_queue,
        "rights_matched": rights_matched,
        "rights_outside": rights_outside,
        "rights_ineligible_baseline": rights_ineligible_baseline,
        "metadata": metadata,
        "metadata_matched": metadata_matched,
        "queue_partition": queue_partition,
        "participant_rows": participant_rows,
        "parameters": parameters,
        "research": research,
        "uncovered_research": uncovered_research,
        "legacy_human": legacy_human,
        "vocab": vocab,
        "subgraphs": subgraphs,
        "family_arity": family_arity,
        "r16a_census": r16a_census,
        "v3_census": v3_census,
        "runtime": runtime,
        "replay": replay,
        "cp11": cp11,
        "database": database,
    }


def gap_routing() -> dict[tuple[str, str], tuple[str, list[str]]]:
    """Return an exhaustive, explicit current disposition for all 105 gap rows."""
    routes: dict[tuple[str, str], tuple[str, list[str]]] = {}

    def add(relative: str, ids: str, disposition: str, obligations: list[str]) -> None:
        for gap_id in ids.split():
            key = (relative, gap_id)
            if key in routes:
                raise ValueError(f"duplicate gap route: {key}")
            routes[key] = (disposition, sorted(obligations))

    root = f"{RAW_REL}/recursive-gap-ledger.tsv"
    add(root, "GAP-001", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_CANDIDATE, OBL_NARY])
    add(root, "GAP-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_PRODUCT])
    add(root, "GAP-003", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_GROUP, OBL_R16A])
    add(root, "GAP-004", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_VOCAB])
    add(root, "GAP-005", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_HUMAN])
    add(root, "GAP-006", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_RIGHTS])
    add(root, "GAP-007", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_BOUND])
    add(root, "GAP-008", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_PAIR, OBL_GROUP])
    add(root, "GAP-009", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_METADATA, OBL_CANDIDATE])
    add(root, "GAP-010", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_PRODUCT])
    add(root, "GAP-011", "PRESERVED_TERMINAL_CONTROL", [])
    add(root, "GAP-012", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_CANDIDATE])
    add(root, "GAP-013", "RESOLVED_BY_COMMITTED_ARTIFACT", [])
    add(root, "GAP-014", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_CANDIDATE])

    cp3 = f"{RAW_REL}/recursive-gap-ledger-checkpoint003-v1.tsv"
    add(cp3, "GAP-001 GAP-014 GAP-019 GAP-031", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_CANDIDATE])
    add(cp3, "GAP-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_PRODUCT])
    add(cp3, "GAP-003", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_GROUP, OBL_R16A])
    add(cp3, "GAP-004 GAP-024", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_VOCAB])
    add(cp3, "GAP-005", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_HUMAN])
    add(cp3, "GAP-006 GAP-018", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_RIGHTS])
    add(cp3, "GAP-007", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_BOUND])
    add(cp3, "GAP-008", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_PAIR, OBL_GROUP])
    add(cp3, "GAP-009 GAP-020", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_METADATA, OBL_CANDIDATE])
    add(cp3, "GAP-010 GAP-023 GAP-032", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_PRODUCT])
    add(cp3, "GAP-011", "PRESERVED_TERMINAL_CONTROL", [])
    add(cp3, "GAP-012 GAP-022", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_CANDIDATE])
    add(cp3, "GAP-013 GAP-015 GAP-025 GAP-026 GAP-028 GAP-029 GAP-030 GAP-033 GAP-034", "RESOLVED_BY_COMMITTED_ARTIFACT", [])
    add(cp3, "GAP-016", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_SCOPE, OBL_GROUP, OBL_QUEUE])
    add(cp3, "GAP-017", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_RIGHTS, OBL_HUMAN, OBL_GROUP])
    add(cp3, "GAP-021", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_NARY])
    add(cp3, "GAP-027", "PRESERVED_HISTORICAL_LIMITATION", [])

    cp4 = f"{RAW_REL}/recursive-gap-ledger-checkpoint004-v2.tsv"
    add(cp4, "GAP-001 GAP-004", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_CANDIDATE, OBL_SCOPE])
    add(cp4, "GAP-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_RIGHTS])
    add(cp4, "GAP-003", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_METADATA])
    add(cp4, "GAP-005", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_HUMAN])
    add(cp4, "GAP-006", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_BOUND])
    add(cp4, "GAP-007", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_QUEUE, OBL_GROUP, OBL_SCOPE])
    add(cp4, "GAP-008", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_PRODUCT])
    add(cp4, "GAP-009", "PRESERVED_HISTORICAL_LIMITATION", [])

    cp5 = f"{RAW_REL}/recursive-gap-ledger-checkpoint005-tranche-a-v1.tsv"
    add(cp5, "GAP-010", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_QUEUE, OBL_GROUP])
    add(cp5, "GAP-011 GAP-014 GAP-015", "PRESERVED_TERMINAL_CONTROL", [])
    add(cp5, "GAP-012", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_QUEUE, OBL_SCOPE])
    add(cp5, "GAP-013", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_GROUP, OBL_HUMAN])
    add(cp5, "GAP-016", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_PRODUCT])

    cp6 = f"{RAW_REL}/recursive-gap-ledger-checkpoint006-tranche-b-v1.tsv"
    add(cp6, "GAP-017", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_QUEUE, OBL_GROUP])
    add(cp6, "GAP-018 GAP-020 GAP-021", "PRESERVED_TERMINAL_CONTROL", [])
    add(cp6, "GAP-019", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_QUEUE])
    add(cp6, "GAP-022", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_GROUP, OBL_SCOPE, OBL_HUMAN])
    add(cp6, "GAP-023", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_PRODUCT, OBL_R16A])
    add(cp6, "GAP-024", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_RIGHTS, OBL_HUMAN, OBL_GROUP])

    cp7 = f"{RAW_REL}/recursive-gap-ledger-checkpoint007-tranche-c-v1.tsv"
    add(cp7, "GAP-025", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_CANDIDATE])
    add(cp7, "GAP-026 GAP-027", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_GROUP, OBL_SCOPE, OBL_HUMAN])
    add(cp7, "GAP-028 GAP-029 GAP-030 GAP-032", "PRESERVED_TERMINAL_CONTROL", [])
    add(cp7, "GAP-031", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_PRODUCT])

    cp8 = f"{RAW_REL}/recursive-gap-ledger-checkpoint008-v1.tsv"
    add(cp8, "GAP-R16B-008-001", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_HUMAN, OBL_PRODUCT])
    add(cp8, "GAP-R16B-008-002", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_GROUP, OBL_PRODUCT])
    add(cp8, "GAP-R16B-008-003 GAP-R16B-008-005", "RESOLVED_BY_COMMITTED_ARTIFACT", [])
    add(cp8, "GAP-R16B-008-004", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_BOUND])

    shard1 = f"{RAW_REL}/recursive-gap-ledger-adaptive-source-shard-1-v1.tsv"
    ids = {
        "0afc59ec3c1298bc3ffbe9f912511da277e44682decc4b914bf04e5de0710823": [OBL_HUMAN],
        "8d7da37424b678e4a943fe109e5d93c6dfae74684eed17ebe2ddcc88e2d87f7f": [OBL_RIGHTS],
        "77315c825f65f9e6a4e193ec22bbd8537c8837020de4440eb0818728d19fea8b": [OBL_SCOPE],
        "e49d03f04994a3c1de47c3e08ebf63c09a6929f9fd14ba511a226a4650a953bf": [OBL_SCOPE],
        "711715ff0a111db59ec0e2536b6ebcc85ab31e41e1327e325865121e92bd2f73": [OBL_SCOPE, OBL_HUMAN],
        "ad757abca4717e8fa253c0e44971730a7ae8fc55ac2b9253d94da008707bdb79": [OBL_SCOPE, OBL_GROUP],
        "17a6758a9f19605c957407617309802e0ea990701be9efd46ff4d54c3d77dd88": [OBL_PAYLOAD],
        "374f75ee7c228223417b215b6157270adba2aea14e62716b8249bc80b06e046f": [OBL_PRODUCT],
    }
    for suffix, obligations in ids.items():
        add(shard1, f"R16B-ADAPTIVE-SOURCE-GAP:{suffix}", "SUPERSEDED_BY_OPEN_OBLIGATION", obligations)

    shard2 = f"{RAW_REL}/recursive-gap-ledger-adaptive-source-shard-2-v1.tsv"
    add(shard2, "R16B-GAP-S2-001", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_HUMAN, OBL_GROUP])
    add(shard2, "R16B-GAP-S2-002", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_CULTURAL])
    add(shard2, "R16B-GAP-S2-003", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_VOCAB, OBL_PRODUCT])
    add(shard2, "R16B-GAP-S2-004", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_RIGHTS])
    add(shard2, "R16B-GAP-S2-005", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_CANDIDATE])
    add(shard2, "R16B-GAP-S2-006", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_PRODUCT])

    global_path = f"{RAW_REL}/recursive-gap-ledger-round16a-global-reconciliation-v1.tsv"
    add(global_path, "R16B-GLOBAL-GAP-001 R16B-GLOBAL-GAP-002 R16B-GLOBAL-GAP-003", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_GROUP, OBL_R16A])
    add(global_path, "R16B-GLOBAL-GAP-004", "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_CULTURAL])
    add(global_path, "R16B-GLOBAL-GAP-005", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_PRODUCT])
    add(global_path, "R16B-GLOBAL-GAP-006", "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_REPRO])

    observed = {(relative, row["gap_id"]) for relative in GAP_PATHS for row in read_tsv(relative)}
    if len(observed) != 105 or set(routes) != observed:
        missing = sorted(observed - set(routes))
        extra = sorted(set(routes) - observed)
        raise ValueError(f"gap routing is not exhaustive: missing={missing}; extra={extra}")
    return routes


def obligation_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    hypotheses = context["hypotheses"]
    hypothesis_ids = sorted(row["hypothesis_id"] for row in hypotheses)
    ungoverned = sorted(row["hypothesis_id"] for row in hypotheses if not row["association_id"])
    rights_unresolved = sorted(
        row["canonical_source_id"] for row in context["rights_queue"]
        if row["canonical_source_id"] not in context["rights_matched"]
    )
    metadata_unresolved = sorted(
        row["metadata_lead_id"] for row in context["metadata"]
        if row["metadata_lead_id"] not in context["metadata_matched"]
    )
    human = sorted(
        [f"LEGACY:{row['review_unit_id']}" for row in context["legacy_human"]]
        + [f"R16B:{row['hypothesis_id']}" for row in hypotheses]
    )
    open_queue = sorted(
        row["queue_id"] for row in context["queue_partition"]["current_open"]
    )
    definitions: list[tuple[str, str, str, list[str], list[str], str, list[str]]] = [
        (
            OBL_CANDIDATE, "CANDIDATE_UNIVERSE_AND_EXCLUSION_PROOF",
            "KNOWN_MINIMUM_NOT_UNIVERSE_WIDE_TOTAL", context["uncovered_research"],
            [CROSSWALK_PATH, TRIGGER_PATH, EXCLUSION_PATH],
            "Add governed triggers or explicit exclusions for every uncovered sense, audit omitted structural classes, and prove the rule-level candidate complement.",
            CLOSURE_KEYS,
        ),
        (
            OBL_NARY, "NARY_PARTICIPANT_RESOLUTION", "EXACT_OPEN_QUEUE",
            sorted(row["participant_resolution_queue_id"] for row in context["participant_rows"]),
            [PARTICIPANT_QUEUE_PATH],
            "Resolve the exact participant sets, scopes, roles, and qualifications without manufacturing pair edges.",
            CLOSURE_KEYS,
        ),
        (
            OBL_RIGHTS, "RIGHTS_AND_LAWFUL_TEXT", "CURRENT_AFTER_SUPERSESSION",
            rights_unresolved, [RIGHTS_QUEUE_PATH, *RIGHTS_REVIEW_PATHS],
            "Complete lawful access, rights, locator, and bounded source-text review for every unresolved canonical source identity.",
            CLOSURE_KEYS,
        ),
        (
            OBL_METADATA, "METADATA_TO_TEXT_REVIEW", "CURRENT_AFTER_SUPERSESSION",
            metadata_unresolved, [METADATA_PATH, *RIGHTS_REVIEW_PATHS],
            "Resolve each metadata lead to reviewable source text or record a final rejection; metadata remains non-evidence.",
            CLOSURE_KEYS,
        ),
        (
            OBL_HUMAN, "EXTERNAL_HUMAN_AUTHORITY", "DISJOINT_NAMESPACED_RECORDS",
            human, [EXTERNAL_REVIEW_PATH, *HYPOTHESIS_PATHS],
            "Obtain independent design-history review of bounded senses, synthesis, topology, and nonclaims before activation.",
            CLOSURE_KEYS,
        ),
        (
            OBL_SCOPE, "SCOPE_SENSE_AND_IDENTITY", "UNGOVERNED_HYPOTHESES",
            ungoverned, HYPOTHESIS_PATHS,
            "Resolve proposed senses, case boundaries, participant distinctions, and governed association identity.",
            ["higher_order_association_closure", "global_composition_coherence_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_GROUP, "GLOBAL_GROUP_COHERENCE", "CURRENT_SCOPED_HYPOTHESES",
            hypothesis_ids, HYPOTHESIS_PATHS,
            "Complete independent exact-group evidence, scope, conflict, counterevidence, and global-coherence review.",
            ["higher_order_association_closure", "global_composition_coherence_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_CULTURAL, "CULTURAL_TRANSFORMATION_REAUDIT", "EXACT_QUARANTINED_CLAIM",
            ["COMP-EVID-018"], [GAP_PATHS[8], GAP_PATHS[9]],
            "Re-audit the inherited cultural-transformation claim against the conflicting official abstract and lawful text.",
            CLOSURE_KEYS,
        ),
        (
            OBL_VOCAB, "ACTIVE_VOCABULARY_REACHABILITY", "INHERITED_ACTIVE_ZERO_PAIR_DEGREE_AND_ZERO_ACTIVE_V3_PATH",
            sorted(row["vocabulary_id"] for row in context["vocab"]),
            [ISOLATED_PATH, VOCAB_IMPACT_PATH],
            "Validate an active product path, retain inquiry-only status, reclassify vocabulary, or govern an explicit non-product policy.",
            ["higher_order_association_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_BOUND, "SEMANTIC_AND_PRODUCT_ARITY_BOUND", "EXACT_SEMANTIC_PARAMETERS",
            sorted(row["parameter_name"] for row in context["parameters"]),
            [PARAMETER_PATH, LOCAL_FAMILY_PATH, CP11_RECEIPT_PATH],
            "Rejustify semantic bounds and derive a governed product maximum from evidence, accessibility, representation, and tested performance.",
            ["higher_order_association_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_R16A, "ROUND16A_SEMANTIC_RECONCILIATION", "NO_SEMANTIC_CARRY_FORWARD",
            sorted(row["prior_id"] for row in context["subgraphs"]),
            [R16A_SUBGRAPH_PATH, R16A_CENSUS_PATH],
            "Resolve corrected, inquiry, rejected, and pair-baseline-only structures before any historical semantic carry-forward.",
            ["pair_association_closure", "higher_order_association_closure", "global_composition_coherence_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_PRODUCT, "PRODUCTION_POPULATION_AND_REACHABILITY", "ZERO_HISTORICAL_PRODUCTION_ACTIVATIONS",
            ["V3_PRODUCTION_ACTIVATION_COUNT:0"],
            [V3_CENSUS_PATH, V3_RUNTIME_INDEPENDENT_PATH, CP11_RECEIPT_PATH, DB_MANIFEST_PATH],
            "Populate only externally authorized historical associations, regenerate reachable objects, and prove every active association and composition path.",
            ["product_association_reachability_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_PAIR, "PAIR_ASSOCIATION_REAUDIT", "INHERITED_PAIR_BASELINE_NOT_CURRENT_CLOSURE",
            ["ROUND16A_PAIR_BASELINE_ONLY"],
            [ASSOCIATION_EVIDENCE_PATH, R16A_SUBGRAPH_PATH],
            "Reconcile inherited pair evidence under the current evidence and scope rules; an empty Round16B association-evidence ledger cannot prove pair closure.",
            ["pair_association_closure", "computational_space_closure", "function3_closure"],
        ),
        (
            OBL_PAYLOAD, "SOURCE_BYTE_REPRODUCIBILITY", "REVIEWED_SOURCES_WITH_NO_COMMITTED_SOURCE_PAYLOAD",
            sorted(row["source_id"] for row in context["reviews"]),
            RIGHTS_REVIEW_PATHS,
            "Preserve lawful source-byte hashes when permitted or retain the explicit locator-only reproducibility limitation.",
            ["computational_space_closure", "function3_closure"],
        ),
        (
            OBL_REPRO, "FINAL_CLEAN_REPRODUCTION_GATE", "NEXT_CHECKPOINT_GATE",
            ["CHECKPOINT013_CLEAN_WORKTREE_REPRODUCTION_PENDING"],
            [CP11_RECEIPT_PATH],
            "Run final clean-worktree deterministic reproduction and the complete repository, build, API, database, LFS, and audit-seal gates.",
            ["computational_space_closure", "function3_closure"],
        ),
        (
            OBL_QUEUE, "OPEN_ASSOCIATION_REVIEW_QUEUE", "CURRENT_NONASSOCIATION_REVIEW_ROWS",
            open_queue, ASSOCIATION_QUEUE_PATHS,
            "Resolve every conditional review row without treating queue membership as an association identity or support decision.",
            CLOSURE_KEYS,
        ),
    ]
    rows = []
    for obligation_id, obligation_class, count_semantics, members, evidence, action, blocks in definitions:
        if not members:
            raise ValueError(f"current obligation has no governed members: {obligation_id}")
        material = {
            "obligation_id": obligation_id,
            "obligation_class": obligation_class,
            "status": "OPEN_CLOSURE_BLOCKING",
            "severity": "CLOSURE_BLOCKING",
            "count_semantics": count_semantics,
            "member_kind": obligation_class,
            "member_count": str(len(members)),
            "member_ids_sha256": id_set_hash(members),
            "member_ids_json": canonical_json(sorted(members)),
            "evidence_paths_json": canonical_json(sorted(evidence)),
            "required_action": action,
            "blocks_closures_json": canonical_json(sorted(blocks)),
        }
        rows.append({**material, "record_sha256": row_hash(material)})
    rows.sort(key=lambda row: row["obligation_id"])
    if len(rows) != len(ALL_OBLIGATIONS) or {row["obligation_id"] for row in rows} != ALL_OBLIGATIONS:
        raise ValueError("current obligation registry is incomplete")
    return rows


def prior_status(row: dict[str, str]) -> str:
    projection = {
        field: row[field]
        for field in sorted(row)
        if (field == "status" or field.endswith("_status")) and row.get(field)
    }
    if not projection:
        projection = {"status": "UNSPECIFIED"}
    return canonical_json(projection)


def source_record_sha(row: dict[str, str]) -> str:
    existing = row.get("record_sha256", "")
    if len(existing) == 64 and all(char in "0123456789abcdef" for char in existing):
        return existing
    return row_hash(row)


def supersession_row(
    kind: str,
    relative: str,
    row_number: int,
    identity: str,
    source: dict[str, str],
    disposition: str,
    obligations: list[str],
    refs: list[str],
) -> dict[str, str]:
    if not set(obligations) <= ALL_OBLIGATIONS:
        raise ValueError(f"unknown successor obligation for {relative}:{identity}")
    if disposition in {"SUPERSEDED_BY_OPEN_OBLIGATION", "PARTIALLY_RECONCILED_REMAINDER_OPEN"} and not obligations:
        raise ValueError(f"open supersession lacks successor: {relative}:{identity}")
    key_material = f"{kind}\t{relative}\t{identity}"
    closure_effect = {
        "RESOLVED_BY_COMMITTED_ARTIFACT": "TECHNICAL_OR_METHOD_GAP_RESOLVED_NO_CLOSURE_INFERENCE",
        "SUPERSEDED_BY_OPEN_OBLIGATION": "CURRENT_SUCCESSOR_BLOCKS_AT_LEAST_ONE_CLOSURE",
        "PARTIALLY_RECONCILED_REMAINDER_OPEN": "COMPLETED_WORK_PRESERVED_CURRENT_REMAINDER_BLOCKS_CLOSURE",
        "PRESERVED_TERMINAL_CONTROL": "TERMINAL_CONTROL_PRESERVED_NO_POSITIVE_CLOSURE_INFERENCE",
        "PRESERVED_HISTORICAL_LIMITATION": "HISTORICAL_LIMITATION_PRESERVED_NO_CLOSURE_INFERENCE",
    }[disposition]
    material = {
        "prior_record_key": f"R16B-PRIOR-RECORD:{sha256_bytes(key_material.encode('utf-8'))}",
        "prior_kind": kind,
        "source_path": relative,
        "source_row_number": str(row_number),
        "prior_id": identity,
        "prior_status": prior_status(source),
        "prior_record_sha256": source_record_sha(source),
        "current_disposition": disposition,
        "successor_obligation_ids_json": canonical_json(sorted(obligations)),
        "successor_artifact_refs_json": canonical_json(sorted(refs)),
        "closure_effect": closure_effect,
    }
    return {**material, "record_sha256": row_hash(material)}


def supersession_rows(context: dict[str, Any]) -> tuple[list[dict[str, str]], str]:
    rows: list[dict[str, str]] = []
    membership: list[str] = []
    routes = gap_routing()

    def append(
        kind: str, relative: str, row_number: int, identity: str, source: dict[str, str],
        disposition: str, obligations: list[str], refs: list[str],
    ) -> None:
        membership.append(f"{kind}\t{relative}\t{identity}")
        rows.append(supersession_row(
            kind, relative, row_number, identity, source, disposition, obligations, refs,
        ))

    for relative in GAP_PATHS:
        for row_number, source in enumerate(read_tsv(relative), 2):
            identity = source["gap_id"]
            disposition, obligations = routes[(relative, identity)]
            append(
                "GAP", relative, row_number, identity, source, disposition, obligations,
                [OBLIGATION_PATH] if obligations else ["COMMITTED_ROUND16B_ARTIFACTS_THROUGH_CHECKPOINT011"],
            )

    terminal = {row["queue_id"] for row in context["queue_partition"]["terminal_control"]}
    derivative = {row["queue_id"] for row in context["queue_partition"]["derivative_reconciled"]}
    for relative in ASSOCIATION_QUEUE_PATHS:
        for row_number, source in enumerate(read_tsv(relative), 2):
            identity = source["queue_id"]
            if identity in terminal:
                disposition, obligations = "PRESERVED_TERMINAL_CONTROL", []
            elif identity in derivative:
                disposition, obligations = "PARTIALLY_RECONCILED_REMAINDER_OPEN", [OBL_R16A, OBL_PRODUCT]
            else:
                disposition, obligations = "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_QUEUE]
            append(
                "ASSOCIATION_REVIEW_QUEUE", relative, row_number, identity, source,
                disposition, obligations,
                [R16A_CENSUS_PATH, OBLIGATION_PATH] if obligations else [relative],
            )

    for row_number, source in enumerate(context["rights_queue"], 2):
        identity = source["canonical_source_id"]
        hits = context["rights_matched"].get(identity, [])
        if hits:
            disposition = "RESOLVED_BY_COMMITTED_ARTIFACT"
            obligations: list[str] = []
            refs = [f"{row['source_path']}#{row['rights_record_id']}" for row in hits]
        else:
            disposition, obligations, refs = "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_RIGHTS], [OBLIGATION_PATH]
        append("SOURCE_RIGHTS_QUEUE", RIGHTS_QUEUE_PATH, row_number, identity, source, disposition, obligations, refs)

    for row_number, source in enumerate(context["participant_rows"], 2):
        append(
            "NARY_PARTICIPANT_OBLIGATION", PARTICIPANT_QUEUE_PATH, row_number,
            source["participant_resolution_queue_id"], source,
            "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_NARY], [OBLIGATION_PATH],
        )

    semantic_row_number = 1
    for source in read_tsv(PARAMETER_PATH):
        semantic_row_number += 1
        if source["higher_order_semantic_obligation"] != "true":
            continue
        append(
            "SEMANTIC_PARAMETER_OBLIGATION", PARAMETER_PATH, semantic_row_number,
            source["parameter_name"], source, "SUPERSEDED_BY_OPEN_OBLIGATION",
            [OBL_BOUND], [OBLIGATION_PATH],
        )

    for row_number, source in enumerate(context["metadata"], 2):
        identity = source["metadata_lead_id"]
        hits = context["metadata_matched"].get(identity, [])
        if hits:
            disposition = "RESOLVED_BY_COMMITTED_ARTIFACT"
            obligations = []
            refs = [f"{row['source_path']}#{row['rights_record_id']}" for row in hits]
        else:
            disposition, obligations, refs = "SUPERSEDED_BY_OPEN_OBLIGATION", [OBL_METADATA], [OBLIGATION_PATH]
        append("METADATA_LEAD_OBLIGATION", METADATA_PATH, row_number, identity, source, disposition, obligations, refs)

    for row_number, source in enumerate(read_tsv(EXTERNAL_REVIEW_PATH), 2):
        append(
            "EXTERNAL_HUMAN_REVIEW_OBLIGATION", EXTERNAL_REVIEW_PATH, row_number,
            source["review_unit_id"], source, "SUPERSEDED_BY_OPEN_OBLIGATION",
            [OBL_HUMAN], [OBLIGATION_PATH],
        )

    if len(membership) != 414 or len(set(membership)) != 414:
        raise ValueError("supersession universe must contain 414 unique physical prior records")
    universe_hash = id_set_hash(membership)
    if universe_hash != "3324de09faab9a1362e2eac97293298a2b9e8d06808f6741df76815f66882497":
        raise ValueError(f"supersession membership drift: {universe_hash}")
    rows.sort(key=lambda row: (row["prior_kind"], row["source_path"], row["prior_id"]))
    if len({row["prior_record_key"] for row in rows}) != 414:
        raise ValueError("supersession prior-record key collision")
    return rows, universe_hash


def closure_metrics(
    context: dict[str, Any], supersession: list[dict[str, str]], universe_hash: str,
) -> dict[str, Any]:
    hypotheses = context["hypotheses"]
    hypothesis_ids = sorted(row["hypothesis_id"] for row in hypotheses)
    ungoverned_hypotheses = sorted(row["hypothesis_id"] for row in hypotheses if not row["association_id"])
    governed_associations = sorted(row["association_id"] for row in hypotheses if row["association_id"])
    arity = Counter(row["arity"] for row in hypotheses)
    queue = context["queue_partition"]
    terminal_queue_ids = [row["queue_id"] for row in queue["terminal_control"]]
    derivative_queue_ids = [row["queue_id"] for row in queue["derivative_reconciled"]]
    open_queue_ids = [row["queue_id"] for row in queue["current_open"]]
    rights_all = sorted(row["canonical_source_id"] for row in context["rights_queue"])
    rights_reviewed = sorted(context["rights_matched"])
    rights_open = sorted(set(rights_all) - set(rights_reviewed))
    metadata_all = sorted(row["metadata_lead_id"] for row in context["metadata"])
    metadata_reviewed = sorted(context["metadata_matched"])
    metadata_open = sorted(set(metadata_all) - set(metadata_reviewed))
    legacy_human_ids = sorted(row["review_unit_id"] for row in context["legacy_human"])
    human_namespaced = sorted(
        [f"LEGACY:{value}" for value in legacy_human_ids]
        + [f"R16B:{value}" for value in hypothesis_ids]
    )
    participant_ids = sorted(row["participant_resolution_queue_id"] for row in context["participant_rows"])
    parameters = sorted(row["parameter_name"] for row in context["parameters"])
    vocab_ids = sorted(row["vocabulary_id"] for row in context["vocab"])
    vocab_sense_ids = sorted(row["participant_sense_id"] for row in context["vocab"])
    subgraph_distribution = dict(sorted(Counter(
        row["reconciliation_outcome"] for row in context["subgraphs"]
    ).items()))
    disposition_distribution = dict(sorted(Counter(
        row["current_disposition"] for row in supersession
    ).items()))
    kind_distribution = dict(sorted(Counter(row["prior_kind"] for row in supersession).items()))
    closure = {key: False for key in CLOSURE_KEYS}
    metrics = {
        "format": "trace-round16b-recursive-gap-closure-metrics-checkpoint012-v2",
        "builder_version": BUILDER_VERSION,
        "authority": {
            "checkpoint011_sha": AUTHORITY_BASE_SHA,
            "checkpoint011_tree": AUTHORITY_BASE_TREE,
            "source_sha": SOURCE_SHA,
            "source_tree": SOURCE_TREE,
            "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        },
        "status": "PASS_EVIDENCE_BOUNDED_NONCLOSURE",
        "supersession": {
            "prior_record_count": len(supersession),
            "prior_record_key_unique_count": len({row["prior_record_key"] for row in supersession}),
            "membership_key_format": "kind<TAB>repo_relative_path<TAB>prior_id<LF>",
            "membership_id_set_sha256": universe_hash,
            "prior_kind_distribution": kind_distribution,
            "current_disposition_distribution": disposition_distribution,
        },
        "hypotheses": {
            "unresolved_association_count": len(hypotheses),
            "unresolved_association_count_scope": "CURRENT_SCOPED_ASSOCIATION_HYPOTHESES",
            "arity_distribution": {str(key): value for key, value in sorted(arity.items())},
            "hypothesis_id_set_sha256": id_set_hash(hypothesis_ids),
            "governed_association_identity_count": len(governed_associations),
            "governed_association_id_set_sha256": id_set_hash(governed_associations),
            "ungoverned_hypothesis_count": len(ungoverned_hypotheses),
            "ungoverned_hypothesis_id_set_sha256": id_set_hash(ungoverned_hypotheses),
            "active_association_count": 0,
            "active_pending_review_count": 0,
            "product_eligible_association_count": 0,
            "implicit_pair_projection_count": 0,
        },
        "association_review_queue": {
            "baseline_record_count": 59,
            "terminal_control_count": len(terminal_queue_ids),
            "terminal_control_id_set_sha256": id_set_hash(terminal_queue_ids),
            "derivative_reconciled_successor_open_count": len(derivative_queue_ids),
            "derivative_reconciled_id_set_sha256": id_set_hash(derivative_queue_ids),
            "current_open_review_count": len(open_queue_ids),
            "current_open_review_id_set_sha256": id_set_hash(open_queue_ids),
            "queue_rows_are_associations": False,
        },
        "candidate_universe": {
            "research_only_sense_count": len(context["research"]),
            "covered_research_only_sense_count": len(context["research"]) - len(context["uncovered_research"]),
            "known_unexplained_exclusion_count": len(context["uncovered_research"]),
            "known_unexplained_exclusion_count_scope": "RESEARCH_ONLY_SENSES_WITHOUT_TRIGGER_HYPOTHESIS_PARTICIPANT_OBLIGATION_OR_EXCLUSION",
            "universe_wide_unexplained_exclusion_count": "INDETERMINATE",
            "uncovered_research_only_sense_id_set_sha256": id_set_hash(context["uncovered_research"]),
            "candidate_exclusion_ledger_record_count": len(read_tsv(EXCLUSION_PATH)),
            "open_nary_participant_obligation_count": len(participant_ids),
            "open_nary_participant_obligation_id_set_sha256": id_set_hash(participant_ids),
            "local_candidate_family_arity_distribution": {
                str(key): value for key, value in sorted(context["family_arity"].items())
            },
            "governed_product_maximum_arity": None,
            "candidate_universe_closure": False,
        },
        "source_rights": {
            "baseline_canonical_identity_count": len(rights_all),
            "baseline_canonical_identity_id_set_sha256": id_set_hash(rights_all),
            "baseline_identities_superseded_by_locator_bearing_text_review_count": len(rights_reviewed),
            "superseded_identity_id_set_sha256": id_set_hash(rights_reviewed),
            "locator_bearing_text_review_outside_baseline_queue_count": len(context["rights_outside"]),
            "locator_bearing_text_review_outside_baseline_source_ids": context["rights_outside"],
            "baseline_review_records_not_text_completion_count": len(context["rights_ineligible_baseline"]),
            "baseline_review_records_not_text_completion_source_ids": context["rights_ineligible_baseline"],
            "known_canonical_identity_union_count": len(rights_all) + len(context["rights_outside"]),
            "review_record_count": len(context["reviews"]),
            "rights_text_completion_count": sum(
                bool(row["rights_text_completion_eligible"])
                for row in context["reviews"]
            ),
            "incomplete_review_record_count": sum(
                not bool(row["rights_text_completion_eligible"])
                for row in context["reviews"]
            ),
            "current_unresolved_canonical_identity_count": len(rights_open),
            "current_unresolved_canonical_identity_id_set_sha256": id_set_hash(rights_open),
        },
        "metadata": {
            "baseline_lead_count": len(metadata_all),
            "baseline_lead_id_set_sha256": id_set_hash(metadata_all),
            "superseded_by_text_review_count": len(metadata_reviewed),
            "superseded_lead_id_set_sha256": id_set_hash(metadata_reviewed),
            "current_metadata_only_unreviewed_count": len(metadata_open),
            "current_metadata_only_unreviewed_id_set_sha256": id_set_hash(metadata_open),
        },
        "human_authority": {
            "legacy_not_completed_count": len(legacy_human_ids),
            "legacy_review_unit_id_set_sha256": id_set_hash(legacy_human_ids),
            "round16b_hypothesis_external_review_open_count": len(hypothesis_ids),
            "round16b_hypothesis_id_set_sha256": id_set_hash(hypothesis_ids),
            "current_record_level_blocker_count": len(human_namespaced),
            "namespaced_member_format": "LEGACY:<review_unit_id>|R16B:<hypothesis_id>",
            "current_record_level_blocker_id_set_sha256": id_set_hash(human_namespaced),
        },
        "semantic_bounds": {
            "higher_order_semantic_obligation_count": len(parameters),
            "parameter_name_set_sha256": id_set_hash(parameters),
            "product_maximum_arity_audited": False,
        },
        "vocabulary_reachability": {
            "active_noncomposable_vocabulary_count": len(vocab_ids),
            "count_scope": "INHERITED_ROUND16A_ACTIVE_ZERO_PAIR_DEGREE_AND_ZERO_ACTIVE_V3_PATH",
            "vocabulary_id_set_sha256": id_set_hash(vocab_ids),
            "participant_sense_id_set_sha256": id_set_hash(vocab_sense_ids),
            "higher_order_composability_proven_count": 0,
            "active_product_path_count": 0,
        },
        "round16a_reconciliation": {
            "association_subgraph_count": len(context["subgraphs"]),
            "association_subgraph_distribution": subgraph_distribution,
            "semantic_carry_forward_authorized_count": 0,
            "active_fact_created_count": 0,
            "product_activation_count": context["r16a_census"]["product_activation_count"],
            "transition_count": context["r16a_census"]["transition_count"],
            "reconciled_row_count_including_topology_audit_records": context["r16a_census"]["reconciled_row_count_including_topology_audit_records"],
        },
        "checkpoint011_capability_boundary": {
            "database_replay_status": context["replay"]["status"],
            "normalized_database_schemas_identical": context["replay"]["normalizedSchemasIdentical"],
            "runtime_independent_status": context["runtime"]["status"],
            "production_activation_count": context["cp11"]["runtime"]["production_activation_count"],
            "active_pending_review_count": context["cp11"]["runtime"]["active_pending_review_count"],
            "active_product_record_count": context["cp11"]["runtime"]["active_product_record_count"],
            "production_data_imported": context["database"]["productionDataImported"],
            "production_activation_performed": context["database"]["productionActivationPerformed"],
            "deployment_performed": context["database"]["deploymentPerformed"],
            "research_capability_is_historical_closure": False,
        },
        "headline_receipt_projection": {
            "unresolved_association_count": 11,
            "active_pending_review_count": 0,
            "unexplained_exclusion_count": 9,
            "unexplained_exclusion_count_scope": "KNOWN_RESEARCH_ONLY_SENSE_COVERAGE_GAPS_ONLY",
            "universe_wide_unexplained_exclusion_count": "INDETERMINATE",
            "active_noncomposable_vocabulary_count": 5,
        },
        "closure": closure,
        "closure_true_count": sum(bool(value) for value in closure.values()),
        "independent_verification_status": "PENDING_SEPARATE_IMPLEMENTATION",
        "reproducibility_status": "PRIMARY_DETERMINISTIC_BUILD_PASS_FINAL_CLEAN_WORKTREE_GATE_PENDING",
        "limitations": [
            "No external design historian supplied activation authority.",
            "No new scholarly search or source-text review was performed by this computational audit.",
            "The candidate-exclusion ledger is header-only and the universe-wide exclusion count is indeterminate.",
            "Reviewed remote source payloads were not committed, so source-byte reproduction remains open.",
            "Checkpoint011 proves schema and runtime capability with zero historical production activation.",
            "Final clean-worktree reproduction and full repository gates remain a later checkpoint obligation.",
        ],
    }
    expected_hashes = {
        "hypotheses": "4dde1a4d5ae3cc5facc407bfaafc1813581b14d5f3c9382a119de93584360118",
        "ungoverned": "99437d954b3e02621ba1846f50b828373cbfd195d0c6386a45d095ed8010f9d4",
        "governed": "c61d2dda5b1237cfdb5748d34361d9631a2c79b23c98a1261222b86a4ab6f007",
        "nary": "027745b18d40dfe7f186d9d3774b3d20cf6bde72fcdbdecfe3aceaa900474077",
        "research": "d1b846638f45b1fbf4587c60ad71a6e9ecd285d1fa0d498c6615783bf86b4fb4",
        "vocab": "4f150b6d2e551e305d7810321bd260096ff52bab29bd8c93d148d114481073c2",
        "parameters": "73b91c15b7aa08ebfea18fd2b06a5130c09d77713c9e679aeee354684f121eb9",
        "rights_open": "dd257baf10240263b03216da4729752458c854585e11344ad965af9aac909e45",
        "metadata_open": "a0a6fa675ead9c98e56c52f387a2468876960b25fe65885f6ceaaf284309a0bd",
        "human": "303ab3c6bd4e17a27c697d62211d2dce6b01a0acd4ea1fa1eb8a4f8da1be5357",
        "queue_open": "fc1497ae93a4da880c0d919b4c174bc15bb7aebb3fc22f364a7a41174a67c1dd",
    }
    observed_hashes = {
        "hypotheses": metrics["hypotheses"]["hypothesis_id_set_sha256"],
        "ungoverned": metrics["hypotheses"]["ungoverned_hypothesis_id_set_sha256"],
        "governed": metrics["hypotheses"]["governed_association_id_set_sha256"],
        "nary": metrics["candidate_universe"]["open_nary_participant_obligation_id_set_sha256"],
        "research": metrics["candidate_universe"]["uncovered_research_only_sense_id_set_sha256"],
        "vocab": metrics["vocabulary_reachability"]["vocabulary_id_set_sha256"],
        "parameters": metrics["semantic_bounds"]["parameter_name_set_sha256"],
        "rights_open": metrics["source_rights"]["current_unresolved_canonical_identity_id_set_sha256"],
        "metadata_open": metrics["metadata"]["current_metadata_only_unreviewed_id_set_sha256"],
        "human": metrics["human_authority"]["current_record_level_blocker_id_set_sha256"],
        "queue_open": metrics["association_review_queue"]["current_open_review_id_set_sha256"],
    }
    if observed_hashes != expected_hashes:
        raise ValueError(f"headline set-hash regression: {observed_hashes}")
    if metrics["closure_true_count"] != 0:
        raise ValueError("non-closure audit produced a true closure flag")
    return metrics


def build_artifacts() -> dict[str, bytes]:
    context = load_context()
    manifest_rows = input_manifest()
    obligations = obligation_rows(context)
    supersession, universe_hash = supersession_rows(context)
    metrics = closure_metrics(context, supersession, universe_hash)
    artifacts = {
        INPUT_MANIFEST_PATH: tsv_bytes(INPUT_FIELDS, manifest_rows),
        SUPERSESSION_PATH: tsv_bytes(SUPERSESSION_FIELDS, supersession),
        OBLIGATION_PATH: tsv_bytes(OBLIGATION_FIELDS, obligations),
        METRICS_PATH: json_bytes(metrics),
    }
    output_hashes = {
        relative: sha256_bytes(payload) for relative, payload in sorted(artifacts.items())
    }
    receipt = {
        "format": "trace-round16b-recursive-gap-closure-build-receipt-checkpoint012-v2",
        "builder_version": BUILDER_VERSION,
        "builder_sha256": sha256_file(Path(__file__)),
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "authority_base_tree": AUTHORITY_BASE_TREE,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "status": "PASS_EVIDENCE_BOUNDED_NONCLOSURE",
        "input_count": len(manifest_rows),
        "primary_output_count_excluding_receipt": len(artifacts),
        "primary_output_sha256": output_hashes,
        "primary_output_aggregate_sha256": sha256_bytes(canonical_json(output_hashes).encode("utf-8")),
        "supersession_prior_record_count": len(supersession),
        "supersession_membership_id_set_sha256": universe_hash,
        "current_obligation_class_count": len(obligations),
        "unresolved_association_count": metrics["hypotheses"]["unresolved_association_count"],
        "active_pending_review_count": 0,
        "rights_baseline_text_completed_count": metrics["source_rights"]["baseline_identities_superseded_by_locator_bearing_text_review_count"],
        "rights_current_unresolved_count": metrics["source_rights"]["current_unresolved_canonical_identity_count"],
        "metadata_text_superseded_count": metrics["metadata"]["superseded_by_text_review_count"],
        "metadata_current_unreviewed_count": metrics["metadata"]["current_metadata_only_unreviewed_count"],
        "known_unexplained_exclusion_count": 9,
        "universe_wide_unexplained_exclusion_count": "INDETERMINATE",
        "active_noncomposable_vocabulary_count": 5,
        "closure_flags_true_count": 0,
        "history_rewritten": False,
        "force_push_used": False,
        "origin_main_rewritten": False,
        "rollback_tag_pushed": False,
        "deployment_performed": False,
    }
    artifacts[BUILD_RECEIPT_PATH] = json_bytes(receipt)
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="compare all primary artifact bytes without rewriting them",
    )
    args = parser.parse_args()
    artifacts = build_artifacts()
    mismatches = []
    for relative, payload in sorted(artifacts.items()):
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
        "builder_version": BUILDER_VERSION,
        "primary_artifact_count": len(artifacts),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }
    print(canonical_json(result))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
