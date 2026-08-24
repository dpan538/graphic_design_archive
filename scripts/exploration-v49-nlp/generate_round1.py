#!/usr/bin/env python3
"""Generate deterministic, bounded TRACE NLP Round 1 evidence.

The generator is intentionally a projection boundary.  It accepts one sealed
analysis summary, derives the exact seventeen research TSVs, and emits thirteen
aggregate-only raw JSON receipts.  It never accepts or writes corpus documents,
embedding vectors, pair matrices, or full rankings.

Normal use is two-pass safe: the Markdown research files may be authored first,
then this script binds their bytes together with the prospective TSV bytes in
``nlp-round1-analysis-summary.json``.  ``--self-test`` writes only beneath a
temporary directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import tempfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
DEFAULT_RESEARCH_DIR = ROOT / "docs/research/trace-v49-exploration-nlp-round1"
DEFAULT_AUDIT_RAW_DIR = ROOT / "docs/audits/v49-exploration-nlp-round1/raw"

INPUT_SCHEMA_VERSION = "trace-nlp-round1-analysis-summary/v1"
GENERATION_SCHEMA_VERSION = "trace-nlp-round1-generation/v1"
RAW_SCHEMA_VERSION = "trace-nlp-round1-bounded-evidence/v1"
SOURCE_COMMIT = "580587a74f400d8a04d995937f4efb31e6621dd8"
CANONICAL_OBJECT_COUNT = 15_923
PUBLIC_OBJECT_COUNT = 7_995
HELD_OBJECT_COUNT = 7_928
EXPECTED_ASPECT_COUNTS = {
    "NLP_OBJECT_DESCRIPTION": 0,
    "NLP_OBJECT_SEMANTIC_COMPOSITE": 7_995,
    "NLP_SOURCE_NARRATIVE": 7_431,
    "NLP_SUBJECT": 7_838,
    "NLP_TITLE": 7_995,
}
CORPUS_POLICY_VERSION = "trace-nlp-corpus-v1"
CORPUS_POLICY_SHA256 = "e20d6de00345fce6f925b4ee1ba5c89be7ee4b859e8bda0432bcd6c964a03f16"
FIELD_REGISTRY_VERSION = "trace-nlp-text-field-registry-v1"
FIELD_REGISTRY_SHA256 = "b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6"
NORMALIZATION_VERSION = "trace-nlp-normalization-v1"
CORPUS_SHA256 = "7cde5cfdcf0a0bfd4762f9e23c3b50287a0b9071cbf0bd21102bca4ae2ee024c"
DOCUMENT_RECEIPT_SHA256 = "69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8"
TOKEN_COUNT_RECEIPT_SHA256 = "511eee824342ded9c6ac4606af3f99dea79844663ebd550cbbca2ac2ba2cecca"
TOKEN_COUNT_METHOD = "TRACE_UNICODE_WORD_TOKENS_V1"
EVALUATION_REGISTRY_VERSION = "trace-nlp-evaluation-pairs-v1"
EVALUATION_REGISTRY_SHA256 = "73c0650cfc10a2db6d5fb61c72a783b086667d2da7e6229f1cdd00475700a785"
MODEL_REGISTRY_SHA256 = "2b77f50cf883714544d16224f84ef15e511d45251bd52e81fc8764d2f64fcd82"
ROUND6_CANDIDATE_INDEX_SHA256 = "abba30fcdded21b8f1ba6f7ec87a47b6bbd83c0d1e40d90670143fb88b83873f"
CONTEXT_PROJECTION_SHA256 = "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
SPACETIME_PROJECTION_SHA256 = "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
MODEL_INPUT_TOKEN_CAPS = {
    "NLP_OBJECT_SEMANTIC_COMPOSITE": 256,
    "NLP_SOURCE_NARRATIVE": 512,
    "NLP_SUBJECT": 256,
    "NLP_TITLE": 256,
}
REQUIRED_LEXICAL_ASPECT_IDS = (
    "NLP_TITLE",
    "NLP_SUBJECT",
    "NLP_SOURCE_NARRATIVE",
)
REQUIRED_LEXICAL_FAMILIES = (
    "BM25F",
    "CHAR_NGRAM",
    "WORD_NGRAM",
    "LEXICAL_HYBRID",
)
REQUIRED_DIAGNOSTIC_K = (10, 20, 50)
REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS = (
    "SOURCE",
    "LANGUAGE",
    "TEXT_LENGTH",
    "BOILERPLATE",
    "GENERIC_TITLE",
    "METADATA_COMPLETENESS",
)
DECLARED_ROBUSTNESS_ABLATION_IDS = (
    "MAX_LENGTH_128",
    "MAX_LENGTH_256",
    "MAX_LENGTH_512",
    "OFFICIAL_ASYMMETRIC_VS_PLAIN_DIAGNOSTIC",
    "TITLE_ONLY",
    "SUBJECT_ONLY",
    "SOURCE_NARRATIVE_ONLY",
    "SOURCE_IDENTITY_MASKED",
    "REGISTERED_BOILERPLATE_REMOVED",
    "MARKUP_CLEANED",
    "CASE_NORMALIZED",
    "PUNCTUATION_VARIANT",
    "HYPHEN_VARIANT",
    "APOSTROPHE_VARIANT",
    "UNICODE_CANONICAL_VARIANT",
    "DIACRITIC_FOLDED_LEXICAL_VIEW",
    "WIDTH_COMPATIBILITY_LEXICAL_VIEW",
)

COMPONENT_KEYS = (
    "source",
    "governance",
    "boundary",
    "evaluationRegistry",
    "models",
    "lexical",
    "dense",
    "metadata",
    "leakage",
    "hubness",
    "robustness",
    "aspects",
    "structured",
    "hybrid",
    "review",
    "runs",
    "performance",
    "security",
    "decision",
    "invariants",
)

RESEARCH_FILES = (
    "00_EXECUTIVE_DECISION.md",
    "01_NLP_DATA_STATEMENT.md",
    "02_TEXT_SOURCE_INVENTORY.md",
    "03_NLP_TEXT_FIELD_REGISTRY.tsv",
    "04_NLP_CORPUS_GOVERNANCE_POLICY.md",
    "05_LANGUAGE_AND_SCRIPT_CENSUS.tsv",
    "06_TEXT_LENGTH_AND_TOKENIZATION.tsv",
    "07_DUPLICATION_AND_BOILERPLATE_AUDIT.md",
    "08_NLP_BOILERPLATE_REGISTRY.tsv",
    "09_ASPECT_DOCUMENT_SPEC.md",
    "10_MODEL_ARTIFACT_REGISTER.tsv",
    "11_EVALUATION_PAIR_REGISTRY.tsv",
    "12_LEXICAL_BASELINE_RESULTS.tsv",
    "13_DENSE_MODEL_RESULTS.tsv",
    "14_CROSS_LANGUAGE_RESULTS.tsv",
    "15_METADATA_HOLDOUT_RESULTS.tsv",
    "16_SOURCE_LANGUAGE_LEAKAGE.tsv",
    "17_HUBNESS_AND_ANISOTROPY.tsv",
    "18_ROBUSTNESS_AND_ABLATION.tsv",
    "19_ASPECT_DISAGREEMENT.tsv",
    "20_STRUCTURED_NLP_DISAGREEMENT.tsv",
    "21_HYBRID_EXPERIMENTS.tsv",
    "22_NLP_REVIEW_PACKET.tsv",
    "23_NLP_CHANNEL_ARCHITECTURE.md",
    "24_LICENSE_AND_PRODUCTION_ELIGIBILITY.md",
    "25_PERFORMANCE_AND_REPRODUCIBILITY.md",
    "26_NLP_RED_TEAM.md",
    "27_ROUND_DECISION.md",
)

AUDIT_DOCUMENT_FILES = (
    "00_EXECUTIVE_RECEIPT.md",
    "01_CORPUS_BOUNDARY_VALIDATION.md",
    "02_TEXT_FIELD_GOVERNANCE.md",
    "03_MODEL_ARTIFACT_VALIDATION.md",
    "04_LEXICAL_BASELINE_VALIDATION.md",
    "05_DENSE_MODEL_VALIDATION.md",
    "06_LEAKAGE_AND_HUBNESS_VALIDATION.md",
    "07_REPRODUCIBILITY.md",
    "08_SECURITY_AND_LICENSE.md",
    "09_CHANGED_FILES.md",
)

RAW_FILES = (
    "nlp-round1-analysis-summary.json",
    "corpus-governance-summary.json",
    "language-tokenization-summary.json",
    "duplication-boilerplate-summary.json",
    "model-artifact-summary.json",
    "evaluation-registry-summary.json",
    "lexical-baseline-summary.json",
    "dense-cross-language-summary.json",
    "metadata-leakage-summary.json",
    "hubness-robustness-summary.json",
    "aspect-structured-hybrid-summary.json",
    "review-architecture-summary.json",
    "run-performance-security-summary.json",
)

TABLE_SCHEMAS: dict[str, tuple[str, ...]] = {
    "03_NLP_TEXT_FIELD_REGISTRY.tsv": (
        "field_id", "source_artifact", "source_structure", "source_field", "primary_role",
        "public_object_coverage", "nonempty_count", "distinct_value_count",
        "character_length_p50", "character_length_p95", "character_length_p99",
        "character_length_max", "language_or_script_state", "duplicate_rate",
        "boilerplate_rate", "contains_source_identity",
        "contains_structured_label_leakage", "contains_url", "contains_markup",
        "contains_rights_or_provenance", "public_safe", "rights_safe",
        "governance_decision", "reason", "prohibited_use",
    ),
    "05_LANGUAGE_AND_SCRIPT_CENSUS.tsv": (
        "aspect_id", "field_role", "source_identity", "script_state",
        "text_length_bucket", "object_count", "document_count", "character_count",
        "object_share", "language_label", "language_label_state",
        "language_id_model_id", "language_id_model_revision",
        "language_id_model_committed", "generated_translation_count", "corpus_sha256",
    ),
    "06_TEXT_LENGTH_AND_TOKENIZATION.tsv": (
        "model_or_tokenizer_id", "tokenizer_revision", "aspect_id", "field_role",
        "measurement_scope", "document_count", "character_length_p50",
        "character_length_p90", "character_length_p95", "character_length_p99",
        "character_length_max", "codepoint_length_p50", "codepoint_length_p90",
        "codepoint_length_p95", "codepoint_length_p99", "codepoint_length_max",
        "lexical_token_count_p50", "lexical_token_count_p90",
        "lexical_token_count_p95", "lexical_token_count_p99",
        "lexical_token_count_max", "dense_token_count_p50", "dense_token_count_p90",
        "dense_token_count_p95", "dense_token_count_p99", "dense_token_count_max",
        "governed_token_cap", "official_model_max_tokens", "effective_token_cap",
        "documents_truncated", "tokens_removed", "document_truncation_rate",
        "token_removal_rate", "truncation_direction", "application_stage",
        "full_normalized_hashes_preserved", "corpus_text_overwritten", "receipt_sha256",
    ),
    "08_NLP_BOILERPLATE_REGISTRY.tsv": (
        "rule_id", "source", "field_role", "phrase_or_hash", "support", "denominator",
        "decision", "reason", "removal_scope", "version", "rule_type", "token_count",
    ),
    "10_MODEL_ARTIFACT_REGISTER.tsv": (
        "candidate_id", "channel", "model_id", "revision", "tokenizer_revision",
        "license_spdx", "eligibility", "production_eligible", "execution_state",
        "execution_blockers", "trust_remote_code_required", "custom_code_reviewed",
        "parameter_count_label", "embedding_dimension", "maximum_input_tokens", "pooling",
        "normalization", "weight_dtype", "execution_dtype_cpu", "quantization_state",
        "query_template", "document_template", "symmetric_mode", "language_coverage",
        "minimum_length_policy", "loader_family", "pickle_weight_present",
        "minimal_snapshot_bytes", "artifact_count", "artifact_manifest_sha256",
        "local_snapshot_verified", "execution_scope", "run_status", "prohibited_use",
    ),
    "11_EVALUATION_PAIR_REGISTRY.tsv": (
        "pair_id", "public_object_id_a", "public_object_id_b", "task", "pair_class",
        "control_type", "verification_source", "verification_strength",
        "verification_artifact_path", "verification_artifact_sha256",
        "eligibility_artifact_path", "eligibility_artifact_sha256",
        "verification_locator_sha256", "field_aspects_available", "language_script",
        "source_identity", "source_item_identity", "representation_qualifier",
        "archive_native_variant_evidence", "reason", "prohibited_interpretation",
    ),
    "12_LEXICAL_BASELINE_RESULTS.tsv": (
        "model_id", "method_family", "implementation_version", "input_variant", "aspect_id",
        "aspect_purpose", "corpus_sha256", "corpus_policy_sha256", "field_registry_sha256",
        "normalization_version", "parameters_sha256", "object_count",
        "candidate_object_count", "aspect_available_query_count",
        "aspect_unavailable_query_count", "query_count", "top_k", "full_public_cohort",
        "full_aspect_cohort", "index_sha256", "index_bytes", "index_build_ms",
        "exact_query_p50_ms", "exact_query_p95_ms", "ranking_ids_sha256",
        "score_observation_sha256", "known_item_positive_pair_count",
        "known_item_recall_at_1", "known_item_recall_at_5", "known_item_recall_at_10",
        "known_item_recall_at_20", "known_item_mrr", "negative_control_pair_count",
        "negative_control_at_10_rate", "same_source_neighbor_rate_at_20",
        "same_language_neighbor_rate_at_20", "metadata_proxy_summary_sha256",
        "ranking_deterministic", "pair_matrix_materialized", "full_rankings_saved",
        "historical_relation", "semantic_relation", "probability", "status", "limitation",
    ),
    "13_DENSE_MODEL_RESULTS.tsv": (
        "model_id", "model_revision", "tokenizer_revision", "license_spdx", "eligibility",
        "execution_scope", "status", "input_variant", "aspect_id", "corpus_sha256",
        "corpus_policy_sha256", "field_registry_sha256", "normalization_version",
        "object_count", "candidate_object_count", "aspect_available_query_count",
        "aspect_unavailable_query_count", "query_count", "top_k", "full_public_cohort",
        "full_aspect_cohort", "embedding_dimension", "maximum_input_tokens", "batch_size",
        "device", "encoding_ms", "documents_per_second", "index_sha256", "index_bytes",
        "exact_query_p50_ms", "exact_query_p95_ms", "ranking_ids_sha256",
        "score_observation_sha256", "known_item_recall_at_1", "known_item_recall_at_5",
        "known_item_recall_at_10", "known_item_recall_at_20", "known_item_mrr",
        "same_source_neighbor_rate_at_20", "same_language_neighbor_rate_at_20",
        "hubness_gini_at_20", "top_1_percent_occurrence_share_at_20",
        "maximum_occurrence_at_20", "mean_sampled_cosine", "first_pc_variance_share",
        "peak_ram_bytes", "peak_vram_bytes", "trust_remote_code_executed",
        "model_weights_committed", "full_embedding_matrix_committed",
        "pair_matrix_materialized", "full_rankings_saved", "randomness_affects_embedding",
        "randomness_affects_neighbor_order", "historical_relation", "semantic_relation",
        "probability", "limitation",
    ),
    "14_CROSS_LANGUAGE_RESULTS.tsv": (
        "model_id", "model_revision", "input_variant", "aspect_id", "status", "reason",
        "corpus_sha256", "evaluation_registry_sha256", "verified_pair_count",
        "directional_query_count", "recall_at_1", "recall_at_5", "recall_at_10",
        "recall_at_20", "mean_reciprocal_rank", "median_rank", "maximum_rank",
        "mean_cosine_observation", "review_row_count", "review_rows_sha256",
        "model_created_positive_pair_count", "generated_translation_count",
        "language_identity_used_as_semantic_truth", "historical_relation",
        "semantic_relation", "probability",
    ),
    "15_METADATA_HOLDOUT_RESULTS.tsv": (
        "model_id", "method_family", "input_variant", "mask_variant", "target", "proxy_only",
        "label_count", "evaluable_query_count", "majority_label_object_share",
        "precision_at_5", "precision_at_10", "precision_at_20", "ndcg_at_5",
        "ndcg_at_10", "ndcg_at_20", "target_literal_count_before",
        "target_literal_count_after", "target_labels_masked", "context_labels_masked",
        "label_contract_sha256", "rows_sha256", "historical_relation",
        "semantic_relation", "probability", "status", "limitation",
    ),
    "16_SOURCE_LANGUAGE_LEAKAGE.tsv": (
        "model_id", "method_family", "input_variant", "aspect_id", "leakage_dimension",
        "probe_or_metric", "k", "query_count", "label_count", "metric_value",
        "majority_baseline", "macro_f1", "cross_validation_folds",
        "source_identity_masked", "boilerplate_removed", "reliable_language_labels_only",
        "language_identity_used_as_positive_affinity", "status", "reason", "receipt_sha256",
        "historical_relation", "semantic_relation", "probability",
    ),
    "17_HUBNESS_AND_ANISOTROPY.tsv": (
        "model_id", "model_revision", "input_variant", "aspect_id", "diagnostic_type", "k",
        "object_count", "query_count", "embedding_dimension", "mean_k_occurrence",
        "variance_k_occurrence", "skewness", "gini", "top_1_percent_occurrence_share",
        "maximum_occurrence", "zero_occurrence_object_count", "total_occurrence_count",
        "expected_occurrence_count", "mean_sampled_cosine", "cosine_variance",
        "pair_observation_count", "first_pc_variance_share", "norm_p50", "norm_p95",
        "pre_normalization_norm_p50", "pre_normalization_norm_p95",
        "nearest_neighbor_cosine_distance_p50", "nearest_neighbor_cosine_distance_p95",
        "exact_mean_off_diagonal_cosine", "overall_diagnostic_status",
        "missing_required_diagnostics", "association_inputs_sha256",
        "association_dimension", "association_type", "association_value",
        "association_group_count", "association_eta_squared",
        "association_pearson_correlation", "association_observation_sha256",
        "correction_id", "correction_tested", "correction_selected", "receipt_sha256",
        "status", "limitation",
    ),
    "18_ROBUSTNESS_AND_ABLATION.tsv": (
        "model_id", "reference_method_id", "variant_method_id", "ablation_id",
        "ablation_family", "input_variant", "aspect_id", "k", "query_count",
        "mean_top_k_overlap", "median_top_k_overlap", "p05_top_k_overlap",
        "mean_rank_correlation", "median_rank_correlation", "p05_rank_correlation",
        "same_source_rate_change", "same_language_rate_change", "hubness_gini_change",
        "known_item_recall_change", "weights_selected", "prompt_optimized", "aspects_fused",
        "robustness_suite_status", "reference_corpus_sha256", "reference_input_variant",
        "reference_aspect_id", "reference_index_sha256", "reference_ranking_ids_sha256",
        "declared_ablation_count", "executed_ablation_ids", "not_run_ablation_ids",
        "suite_sha256",
        "historical_relation", "semantic_relation", "probability", "status", "limitation",
        "receipt_sha256",
    ),
    "19_ASPECT_DISAGREEMENT.tsv": (
        "model_id", "corpus_sha256", "aspect_a", "aspect_b", "k", "joint_query_count",
        "mean_top_k_overlap", "mean_common_rank_correlation", "source_neighbor_rate_a",
        "source_neighbor_rate_b", "language_neighbor_rate_a", "language_neighbor_rate_b",
        "affinity_fused", "aspect_fusion_selected", "historical_relation",
        "semantic_relation", "probability", "status", "limitation",
    ),
    "20_STRUCTURED_NLP_DISAGREEMENT.tsv": (
        "row_type", "structured_model_id", "structured_variant_id", "nlp_method_id",
        "anchor_public_object_id", "candidate_public_object_id", "classification",
        "anchor_count", "candidate_index_sha256", "structured_rank", "nlp_rank",
        "mean_top_20_jaccard", "both_high_case_count",
        "high_structured_low_nlp_case_count", "low_structured_high_nlp_case_count",
        "both_low_case_count", "context_match", "temporal_match", "geography_match",
        "descriptive_match", "text_aspect", "anchor_language_script_state",
        "candidate_language_script_state", "same_source_diagnostic",
        "structured_nlp_fusion_selected", "structured_nlp_fusion_weights_selected",
        "historical_relation", "semantic_relation", "probability", "status", "limitation",
    ),
    "21_HYBRID_EXPERIMENTS.tsv": (
        "hybrid_id", "left_method_id", "right_method_id", "rrf_constant", "evaluation_k",
        "eligible_query_count", "known_item_recall", "ranking_ids_sha256",
        "weights_selected", "production_selected", "hybrid_selected",
        "fusion_weights_selected", "historical_relation", "semantic_relation",
        "probability", "status", "limitation",
    ),
    "22_NLP_REVIEW_PACKET.tsv": (
        "packet_id", "anchor_public_object_id", "anchor_title",
        "candidate_public_object_id", "candidate_title", "blind_model_code", "method_role",
        "rank", "score_observation", "text_aspect", "retrieval_reason", "same_source",
        "same_script_state", "context_match", "temporal_match", "geography_match",
        "descriptive_match", "expert_judgment", "historical_relation", "semantic_relation",
        "probability",
    ),
}

RESEARCH_TSV_FILES = tuple(TABLE_SCHEMAS)

TABLE_SOURCES: dict[str, tuple[str, str]] = {
    "03_NLP_TEXT_FIELD_REGISTRY.tsv": ("governance", "fieldRegistryRows"),
    "05_LANGUAGE_AND_SCRIPT_CENSUS.tsv": ("governance", "languageScriptRows"),
    "06_TEXT_LENGTH_AND_TOKENIZATION.tsv": ("governance", "textLengthRows"),
    "08_NLP_BOILERPLATE_REGISTRY.tsv": ("governance", "boilerplateRows"),
    "10_MODEL_ARTIFACT_REGISTER.tsv": ("models", "artifactRows"),
    "11_EVALUATION_PAIR_REGISTRY.tsv": ("evaluationRegistry", "rows"),
    "12_LEXICAL_BASELINE_RESULTS.tsv": ("lexical", "resultRows"),
    "13_DENSE_MODEL_RESULTS.tsv": ("dense", "resultRows"),
    "14_CROSS_LANGUAGE_RESULTS.tsv": ("dense", "crossLanguageRows"),
    "15_METADATA_HOLDOUT_RESULTS.tsv": ("metadata", "holdoutRows"),
    "16_SOURCE_LANGUAGE_LEAKAGE.tsv": ("leakage", "sourceLanguageRows"),
    "17_HUBNESS_AND_ANISOTROPY.tsv": ("hubness", "rows"),
    "18_ROBUSTNESS_AND_ABLATION.tsv": ("robustness", "rows"),
    "19_ASPECT_DISAGREEMENT.tsv": ("aspects", "rows"),
    "20_STRUCTURED_NLP_DISAGREEMENT.tsv": ("structured", "rows"),
    "21_HYBRID_EXPERIMENTS.tsv": ("hybrid", "rows"),
    "22_NLP_REVIEW_PACKET.tsv": ("review", "rows"),
}

TABLE_ID_COLUMNS: dict[str, tuple[str, ...]] = {
    "03_NLP_TEXT_FIELD_REGISTRY.tsv": ("field_id",),
    "05_LANGUAGE_AND_SCRIPT_CENSUS.tsv": ("aspect_id", "script_state", "source_identity", "text_length_bucket"),
    "06_TEXT_LENGTH_AND_TOKENIZATION.tsv": ("model_or_tokenizer_id", "aspect_id", "measurement_scope"),
    "08_NLP_BOILERPLATE_REGISTRY.tsv": ("rule_id",),
    "10_MODEL_ARTIFACT_REGISTER.tsv": ("candidate_id",),
    "11_EVALUATION_PAIR_REGISTRY.tsv": ("pair_id",),
    "12_LEXICAL_BASELINE_RESULTS.tsv": ("model_id", "input_variant", "aspect_id"),
    "13_DENSE_MODEL_RESULTS.tsv": ("model_id", "execution_scope", "input_variant", "aspect_id"),
    "14_CROSS_LANGUAGE_RESULTS.tsv": ("model_id", "input_variant", "aspect_id"),
    "15_METADATA_HOLDOUT_RESULTS.tsv": ("model_id", "target", "mask_variant"),
    "16_SOURCE_LANGUAGE_LEAKAGE.tsv": ("model_id", "input_variant", "leakage_dimension", "probe_or_metric", "k"),
    "17_HUBNESS_AND_ANISOTROPY.tsv": ("model_id", "input_variant", "aspect_id", "diagnostic_type", "k"),
    "18_ROBUSTNESS_AND_ABLATION.tsv": (
        "model_id", "reference_method_id", "variant_method_id", "ablation_id", "k"
    ),
    "19_ASPECT_DISAGREEMENT.tsv": ("model_id", "aspect_a", "aspect_b", "k"),
    "20_STRUCTURED_NLP_DISAGREEMENT.tsv": ("row_type", "structured_model_id", "anchor_public_object_id", "candidate_public_object_id", "classification"),
    "21_HYBRID_EXPERIMENTS.tsv": ("hybrid_id", "evaluation_k"),
    "22_NLP_REVIEW_PACKET.tsv": ("packet_id", "anchor_public_object_id", "blind_model_code", "rank", "candidate_public_object_id"),
}

INVARIANT_TEXT = {
    "NLP-INV-001": "Only 7,995 public objects may enter the NLP corpus.",
    "NLP-INV-002": "No held object or held text enters any model input.",
    "NLP-INV-003": "Every included text field has a governed role and decision.",
    "NLP-INV-004": "Source narrative is not silently merged with object-semantic text.",
    "NLP-INV-005": "Rights/provenance/boilerplate text adds zero object-semantic affinity.",
    "NLP-INV-006": "Original source text is never overwritten.",
    "NLP-INV-007": "No machine translation or generated summary enters the corpus.",
    "NLP-INV-008": "Same title does not imply same object identity.",
    "NLP-INV-009": "Every evaluation positive pair has an external verification source.",
    "NLP-INV-010": "Metadata-proxy targets are masked in the masked evaluation variant.",
    "NLP-INV-011": "Source identity is measured as leakage and not hidden.",
    "NLP-INV-012": "Language identity is measured and not treated as semantic truth.",
    "NLP-INV-013": "Every dense model uses an exact pinned revision.",
    "NLP-INV-014": "Every model has a license and production-eligibility decision.",
    "NLP-INV-015": "Unreviewed remote code cannot execute.",
    "NLP-INV-016": "No model weight is committed.",
    "NLP-INV-017": "No full embedding matrix is committed.",
    "NLP-INV-018": "Every text aspect remains separately evaluable.",
    "NLP-INV-019": "No NLP score becomes a historical relation.",
    "NLP-INV-020": "No NLP score is described as probability.",
    "NLP-INV-021": "NLP does not modify CG-CUR-4.",
    "NLP-INV-022": "NLP does not modify M2/M5/M7.",
    "NLP-INV-023": "NLP and structured affinity remain separate channels in this round.",
    "NLP-INV-024": "Seeded randomness affects no corpus, embedding, neighbor or score.",
    "NLP-INV-025": "Every committed review row contains public-safe text only.",
    "NLP-INV-026": "Source-leakage and hubness reports cannot be omitted from shortlist decisions.",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40,64}$")
PUBLIC_ID_RE = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
UUID_RE = re.compile(
    r"(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])",
    re.IGNORECASE,
)
PRIVATE_ID_RE = re.compile(
    r"(?:\bFOL-[A-Z0-9_-]+|\bTRN-OBJ-[A-Z0-9_-]+|\bTRTREE[A-Z0-9_-]*|"
    r"\bTRBRANCH[A-Z0-9_-]*|\bDOS-SURF-[A-Z0-9_-]+)",
    re.IGNORECASE,
)
URL_RE = re.compile(r"(?:https?://|file://|www\.)", re.IGNORECASE)
OFFICIAL_VERIFICATION_SOURCE_RE = re.compile(
    r"https://www\.(?:artic\.edu/artworks/[1-9][0-9]*|loc\.gov/item/[1-9][0-9]*)"
)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_RAW_FILE_BYTES = 8 * 1024 * 1024
MAX_RAW_TOTAL_BYTES = 32 * 1024 * 1024
MAX_TSV_FILE_BYTES = 16 * 1024 * 1024
MAX_TABLE_ROWS = 25_000
MAX_REVIEW_ROWS = 2_000
MAX_RUN_ROWS = 100
MAX_RAW_SCALAR_ARRAY_ITEMS = 256
MAX_RAW_NUMERIC_ARRAY_ITEMS = 64
MAX_TOTAL_NUMERIC_ARRAY_CELLS = 64
MAX_MARKDOWN_FILE_BYTES = 64 * 1024
MAX_MARKDOWN_TOTAL_BYTES = 256 * 1024


class GenerationError(RuntimeError):
    """Raised when an analysis summary cannot cross the evidence boundary."""


def canonical_json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise GenerationError(f"{label} must be a JSON object")
    return {str(key): item for key, item in value.items()}


def _rows(value: Any, label: str, *, maximum: int = MAX_TABLE_ROWS) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise GenerationError(f"{label} must be a JSON row array")
    if len(value) > maximum:
        raise GenerationError(f"{label} exceeds the bounded row limit {maximum}")
    result = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise GenerationError(f"{label}[{index}] is not an object")
        result.append({str(key): item for key, item in row.items()})
    return result


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise GenerationError(f"{label} is not an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise GenerationError(f"{label} is not an integer") from error
    if isinstance(value, float) and value != result:
        raise GenerationError(f"{label} is not an integer")
    return result


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise GenerationError(f"{label} is not numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise GenerationError(f"{label} is not numeric") from error
    if not math.isfinite(result):
        raise GenerationError(f"{label} is not finite")
    return result


def _number_in_range(
    value: Any, label: str, *, minimum: float, maximum: float
) -> float:
    result = _number(value, label)
    if result < minimum or result > maximum:
        raise GenerationError(f"{label} is outside [{minimum}, {maximum}]")
    return result


def _nonnegative_number(value: Any, label: str) -> float:
    result = _number(value, label)
    if result < 0:
        raise GenerationError(f"{label} is negative")
    return result


def _positive_integer(value: Any, label: str) -> int:
    result = _integer(value, label)
    if result <= 0:
        raise GenerationError(f"{label} is not positive")
    return result


def _status(value: Any, label: str, allowed: set[str]) -> str:
    result = str(value).upper()
    if result not in allowed:
        raise GenerationError(f"{label} has unsupported status: {result}")
    return result


def _required_text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result or result in {"N/A", "NOT_RUN"}:
        raise GenerationError(f"{label} is absent")
    return result


def _require_unavailable(
    row: Mapping[str, Any], columns: Sequence[str], label: str
) -> None:
    for column in columns:
        value = row[column]
        if value is None:
            continue
        if str(value).strip().upper() not in {"", "N/A", "NOT_RUN"}:
            raise GenerationError(f"{label} carries unavailable evidence: {column}")


def _require_zero_or_unavailable(
    row: Mapping[str, Any], columns: Sequence[str], label: str
) -> None:
    for column in columns:
        value = row[column]
        if value is None or str(value).strip().upper() in {"", "N/A", "NOT_RUN"}:
            continue
        if _integer(value, f"{label} {column}") != 0:
            raise GenerationError(f"{label} carries a nonzero count: {column}")


def _boolean(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    normalized = str(value).strip().casefold()
    if normalized in {"true", "yes", "1", "pass"}:
        return True
    if normalized in {"false", "no", "0", "fail"}:
        return False
    raise GenerationError(f"{label} is not boolean")


def _json_string_set(value: Any, label: str) -> set[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as error:
            raise GenerationError(f"{label} is not a JSON string array") from error
    else:
        decoded = value
    if isinstance(decoded, (str, bytes, bytearray)) or not isinstance(decoded, Sequence):
        raise GenerationError(f"{label} is not a JSON string array")
    result = [str(item) for item in decoded]
    if any(not item for item in result) or len(result) != len(set(result)):
        raise GenerationError(f"{label} has blank or duplicate values")
    return set(result)


def _sha(value: Any, label: str) -> str:
    text = str(value or "")
    if not SHA256_RE.fullmatch(text):
        raise GenerationError(f"{label} is not a lowercase SHA-256")
    return text


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _lookup(mapping: Mapping[str, Any], key: str, *, default: Any = None) -> Any:
    if key in mapping:
        return mapping[key]
    normalized = _normalize_key(key)
    matches = [value for native, value in mapping.items() if _normalize_key(str(native)) == normalized]
    if len(matches) > 1:
        raise GenerationError(f"ambiguous aliases for {key}")
    return matches[0] if matches else default


def _required(mapping: Mapping[str, Any], key: str, label: str) -> Any:
    sentinel = object()
    value = _lookup(mapping, key, default=sentinel)
    if value is sentinel:
        raise GenerationError(f"{label}.{key} is required")
    return value


def _assert_false(mapping: Mapping[str, Any], key: str, label: str) -> None:
    if _boolean(_required(mapping, key, label), f"{label}.{key}"):
        raise GenerationError(f"{label}.{key} must remain false")


def _assert_zero(mapping: Mapping[str, Any], key: str, label: str) -> None:
    if _integer(_required(mapping, key, label), f"{label}.{key}") != 0:
        raise GenerationError(f"{label}.{key} must remain zero")


def _validate_input_shape(summary: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    allowed = {"schemaVersion", "analysisSummarySha256", "tables", *COMPONENT_KEYS}
    if set(summary) - allowed:
        raise GenerationError(f"analysis summary has unexpected top-level keys: {sorted(set(summary) - allowed)}")
    if summary.get("schemaVersion") != INPUT_SCHEMA_VERSION:
        raise GenerationError("analysis summary schema version changed")
    components = {key: _mapping(_required(summary, key, "summary"), key) for key in COMPONENT_KEYS}
    declared = _required(summary, "analysisSummarySha256", "summary")
    material = {key: value for key, value in summary.items() if key != "analysisSummarySha256"}
    if _sha(declared, "analysisSummarySha256") != sha256_json(material):
        raise GenerationError("analysisSummarySha256 does not bind the canonical input")
    return components


def _validate_pins(components: Mapping[str, Mapping[str, Any]]) -> None:
    source = components["source"]
    expected_source = {
        "sourceCommit": SOURCE_COMMIT,
        "round6CandidateIndexSha256": ROUND6_CANDIDATE_INDEX_SHA256,
        "contextProjectionSha256": CONTEXT_PROJECTION_SHA256,
        "spacetimeProjectionSha256": SPACETIME_PROJECTION_SHA256,
    }
    for key, expected in expected_source.items():
        if str(_required(source, key, "source")) != expected:
            raise GenerationError(f"source pin changed: {key}")
    frozen = _mapping(_required(source, "frozenInputs", "source"), "source.frozenInputs")
    if not frozen or any(not PurePosixPath(path).name or PurePosixPath(path).is_absolute() for path in frozen):
        raise GenerationError("frozenInputs must be a non-empty relative-path mapping")
    for path, digest in frozen.items():
        _sha(digest, f"source.frozenInputs[{path}]")
    identity = _mapping(
        _required(source, "corpusIdentityReceipt", "source"),
        "source.corpusIdentityReceipt",
    )
    expected_identity = {
        "documentReceiptSha256": DOCUMENT_RECEIPT_SHA256,
        "lexicalCorpusSha256": CORPUS_SHA256,
        "tokenCountReceiptSha256": TOKEN_COUNT_RECEIPT_SHA256,
        "tokenCountMethod": TOKEN_COUNT_METHOD,
    }
    for key, expected in expected_identity.items():
        if str(_required(identity, key, "source.corpusIdentityReceipt")) != expected:
            raise GenerationError(f"corpus identity contract changed: {key}")
    if not _boolean(
        _required(
            identity,
            "documentAndLexicalCorpusHashesAreDistinctContracts",
            "source.corpusIdentityReceipt",
        ),
        "source.corpusIdentityReceipt.documentAndLexicalCorpusHashesAreDistinctContracts",
    ):
        raise GenerationError("document and lexical corpus identities were conflated")
    _sha(
        _required(identity, "canonicalPublicIdsSha256", "source.corpusIdentityReceipt"),
        "source.corpusIdentityReceipt.canonicalPublicIdsSha256",
    )

    governance = components["governance"]
    expected_governance = {
        "corpusPolicyVersion": CORPUS_POLICY_VERSION,
        "corpusPolicySha256": CORPUS_POLICY_SHA256,
        "fieldRegistryVersion": FIELD_REGISTRY_VERSION,
        "fieldRegistrySha256": FIELD_REGISTRY_SHA256,
        "normalizationVersion": NORMALIZATION_VERSION,
        "corpusSha256": CORPUS_SHA256,
        "documentReceiptSha256": DOCUMENT_RECEIPT_SHA256,
        "tokenCountReceiptSha256": TOKEN_COUNT_RECEIPT_SHA256,
        "tokenCountMethod": TOKEN_COUNT_METHOD,
    }
    for key, expected in expected_governance.items():
        if str(_required(governance, key, "governance")) != expected:
            raise GenerationError(f"governance pin changed: {key}")
    caps = _mapping(_required(governance, "modelInputTokenCaps", "governance"), "modelInputTokenCaps")
    if {key: _integer(value, f"cap {key}") for key, value in caps.items()} != MODEL_INPUT_TOKEN_CAPS:
        raise GenerationError("governed model-input token caps changed")

    boundary = components["boundary"]
    expected_boundary = {
        "canonicalObjectCount": CANONICAL_OBJECT_COUNT,
        "publicObjectCount": PUBLIC_OBJECT_COUNT,
        "heldObjectCount": HELD_OBJECT_COUNT,
        "overlapCount": 0,
        "unclassifiedCount": 0,
        "nlpHeldObjectsIncluded": 0,
        "publicObjectsAudited": PUBLIC_OBJECT_COUNT,
    }
    for key, expected in expected_boundary.items():
        if _integer(_required(boundary, key, "boundary"), f"boundary.{key}") != expected:
            raise GenerationError(f"boundary count changed: {key}")
    aspect_counts = _mapping(_required(boundary, "aspectObjectCounts", "boundary"), "aspectObjectCounts")
    normalized_counts = {str(key): _integer(value, f"aspect count {key}") for key, value in aspect_counts.items()}
    if normalized_counts != EXPECTED_ASPECT_COUNTS:
        raise GenerationError("aspect coverage differs from the frozen corpus contract")

    evaluation = components["evaluationRegistry"]
    expected_evaluation = {
        "registryVersion": EVALUATION_REGISTRY_VERSION,
        "registrySha256": EVALUATION_REGISTRY_SHA256,
    }
    for key, expected in expected_evaluation.items():
        if str(_required(evaluation, key, "evaluationRegistry")) != expected:
            raise GenerationError(f"evaluation registry pin changed: {key}")
    count_contract = {
        "pairCount": 312,
        "knownRepresentationPositivePairCount": 3,
        "negativeControlPairCount": 309,
        "verifiedCrossLanguagePositivePairCount": 0,
        "taskBPositivePairCount": 0,
        "modelCreatedPositivePairCount": 0,
    }
    for key, expected in count_contract.items():
        if _integer(_required(evaluation, key, "evaluationRegistry"), f"evaluationRegistry.{key}") != expected:
            raise GenerationError(f"evaluation registry count changed: {key}")
    same_title = _mapping(
        _required(evaluation, "fullSameTitleStressCensus", "evaluationRegistry"),
        "evaluationRegistry.fullSameTitleStressCensus",
    )
    for key, expected in {
        "duplicateTitleGroupCount": 155,
        "duplicateTitleObjectCount": 520,
        "allUnorderedPairCount": 4_346,
        "excludedKnownIdentityPairCount": 2,
        "stressPairCount": 4_344,
    }.items():
        if _integer(_required(same_title, key, "fullSameTitleStressCensus"), key) != expected:
            raise GenerationError(f"same-title stress census changed: {key}")
    if _boolean(
        _required(same_title, "pairRowsSerialized", "fullSameTitleStressCensus"),
        "same-title pair serialization",
    ):
        raise GenerationError("full same-title stress pairs may not be serialized")
    title_differences = _mapping(
        _required(evaluation, "sourceTitleDifferenceCensus", "evaluationRegistry"),
        "evaluationRegistry.sourceTitleDifferenceCensus",
    )
    if _integer(_required(title_differences, "differenceCount", "sourceTitleDifferenceCensus"), "differenceCount") != 23:
        raise GenerationError("source-title difference census changed")
    difference_types = _mapping(
        _required(title_differences, "differenceTypeCounts", "sourceTitleDifferenceCensus"),
        "sourceTitleDifferenceCensus.differenceTypeCounts",
    )
    if {
        key: _integer(value, f"difference type {key}")
        for key, value in difference_types.items()
    } != {
        "LOC_FILE_SUFFIX_OR_FILENAME_TITLE_REWRITE": 7,
        "V_AND_A_MARKUP_OR_ADJACENT_PUNCTUATION_NORMALIZATION": 16,
    }:
        raise GenerationError("source-title difference category census changed")
    if _integer(_required(title_differences, "taskBPositivePairCount", "sourceTitleDifferenceCensus"), "Task B positives") != 0:
        raise GenerationError("source-title differences were mislabeled as Task B positives")
    if _boolean(_required(title_differences, "rawTitlesSerialized", "sourceTitleDifferenceCensus"), "raw title serialization"):
        raise GenerationError("raw source/title differences may not be serialized")

    models = components["models"]
    if str(_required(models, "registrySha256", "models")) != MODEL_REGISTRY_SHA256:
        raise GenerationError("model registry pin changed")


def _validate_decisions(
    components: Mapping[str, Mapping[str, Any]], *, require_review_rows: bool = True
) -> None:
    governance = components["governance"]
    for key in (
        "originalSourceTextOverwritten",
        "machineTranslationUsed",
        "generatedSummaryUsed",
        "sourceNarrativeMergedWithObjectSemantic",
    ):
        _assert_false(governance, key, "governance")
    roles = _required(governance, "objectSemanticCompositeSourceRoles", "governance")
    if list(roles) != ["OBJECT_TITLE"]:
        raise GenerationError("v1 object-semantic composite must remain title-only")
    if _integer(_required(governance, "unclassifiedTextFieldCount", "governance"), "unclassifiedTextFieldCount") != 0:
        raise GenerationError("an unclassified text field remains")

    decision = components["decision"]
    if str(_required(decision, "phaseStatus", "decision")) != "STOPPED_RECOVERABLE_CHECKPOINT":
        raise GenerationError("source-dominated dense results require a recoverable checkpoint")
    if str(_required(decision, "nlpModelDecision", "decision")) != "NLP_CORPUS_AUDIT_ONLY":
        raise GenerationError("Round 1 may select only NLP_CORPUS_AUDIT_ONLY")
    if _integer(
        _required(decision, "denseModelShortlistCount", "decision"),
        "decision.denseModelShortlistCount",
    ) != 0:
        raise GenerationError("dense model shortlist must remain empty")
    shortlist = _required(decision, "denseModelShortlistIds", "decision")
    if shortlist not in ([], (), "NONE", None):
        raise GenerationError("dense model shortlist IDs must remain NONE")
    for key in (
        "baselineFamiliesShortlisted",
        "provisionalInternalNlpChannelSelected",
        "publicNlpModelSelected",
        "publicNlpWeightsSelected",
        "publicExplorationModelSelected",
        "structuredNlpFusionSelected",
        "structuredNlpFusionWeightsSelected",
        "hubnessCorrectionSelected",
        "domainExpertReviewCompleted",
    ):
        _assert_false(decision, key, "decision")
    if not _boolean(_required(decision, "sourceLeakageAndHubnessConsidered", "decision"), "sourceLeakageAndHubnessConsidered"):
        raise GenerationError("shortlist decision omitted leakage/hubness evidence")

    review = components["review"]
    if _boolean(_required(review, "packetReady", "review"), "review.packetReady"):
        raise GenerationError(
            "review packet cannot be ready when structured/NLP disagreement was unavailable at anchor selection"
        )
    if _boolean(
        _required(review, "domainExpertReviewCompleted", "review"),
        "review.domainExpertReviewCompleted",
    ):
        raise GenerationError("domain-expert review cannot be completed in this round")
    declared_review_anchors = _integer(
        _required(review, "anchorCount", "review"), "review.anchorCount"
    )
    if require_review_rows:
        review_rows = [
            _project_row("22_NLP_REVIEW_PACKET.tsv", row)
            for row in _rows(
                _required(review, "rows", "review"),
                "review.rows",
                maximum=MAX_REVIEW_ROWS,
            )
        ]
        distinct_review_anchors = {
            row["anchor_public_object_id"] for row in review_rows
        }
        if declared_review_anchors != len(distinct_review_anchors):
            raise GenerationError(
                "review.anchorCount differs from the distinct committed anchors"
            )
        if not 24 <= declared_review_anchors <= 36:
            raise GenerationError("review packet must contain 24..36 distinct anchors")

    security = components["security"]
    for key in (
        "modelWeightFilesCommitted",
        "internalUuidExposureCount",
        "heldIdentifierExposureCount",
        "databaseFilesChanged",
        "searchFilesChanged",
        "historicalRelationCount",
        "probabilityCount",
    ):
        _assert_zero(security, key, "security")
    for key in (
        "canonicalReleaseChanged",
        "contextSemanticsChanged",
        "contextGovernanceChanged",
        "spacetimeGovernanceChanged",
        "cgCur4Changed",
        "m2SpecificationChanged",
        "m5SpecificationChanged",
        "m7SpecificationChanged",
        "publicExplorationApiAdded",
        "publicExplorationRouteAdded",
        "vectorDatabaseAdded",
        "explorationRendererImplemented",
        "unreviewedRemoteCodeExecuted",
        "fullEmbeddingMatrixCommitted",
        "fullRankingsCommitted",
        "fullPairMatrixCommitted",
        "randomnessAffectsCorpus",
        "randomnessAffectsEmbedding",
        "randomnessAffectsNeighborOrder",
        "randomnessAffectsScore",
    ):
        _assert_false(security, key, "security")

    invariants = components["invariants"]
    if set(invariants) != set(INVARIANT_TEXT):
        raise GenerationError("analysis summary must declare exactly NLP-INV-001..026")
    for identifier in sorted(INVARIANT_TEXT):
        receipt = _mapping(invariants[identifier], f"invariants.{identifier}")
        if str(_required(receipt, "status", identifier)).upper() != "PASS":
            raise GenerationError(f"analysis did not pass {identifier}")
        refs = _required(receipt, "evidenceRefs", identifier)
        if isinstance(refs, (str, bytes, bytearray)) or not isinstance(refs, Sequence) or not refs:
            raise GenerationError(f"{identifier} lacks evidence references")


def _numeric_sequence_cell_count(value: Any) -> int:
    """Count numeric cells carried by arrays, including mapping-wrapped chunks."""

    if isinstance(value, Mapping):
        return sum(_numeric_sequence_cell_count(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        direct = sum(
            isinstance(child, (int, float)) and not isinstance(child, bool)
            for child in value
        )
        return direct + sum(_numeric_sequence_cell_count(child) for child in value)
    return 0


def _validate_no_forbidden_payload(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = _normalize_key(str(key))
            if normalized in {
                "rankings", "rankingsbyquery", "fullrankingrows", "embeddingvectors",
                "embeddings", "vectors", "corpusdocuments", "documentsbyid", "rawtextdump",
                "pairmatrix", "scorematrix", "allpairs", "neighborsbyquery",
            } and child not in (None, False, 0, "", [], {}):
                raise GenerationError(f"forbidden unbounded payload at {path}.{key}")
            if (
                isinstance(child, Sequence)
                and not isinstance(child, (str, bytes, bytearray))
                and child
                and any(
                    token in normalized
                    for token in ("embedding", "vector", "matrix", "densevalue", "fullranking", "neighborsbyquery")
                )
            ):
                raise GenerationError(f"forbidden model/ranking array at {path}.{key}")
            _validate_no_forbidden_payload(child, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        scalar = all(
            not isinstance(child, (Mapping, Sequence))
            or isinstance(child, (str, bytes, bytearray))
            for child in value
        )
        numeric = scalar and all(
            isinstance(child, (int, float)) and not isinstance(child, bool)
            for child in value
        )
        numeric_matrix = any(
            isinstance(child, Sequence)
            and not isinstance(child, (str, bytes, bytearray))
            and child
            and all(
                isinstance(cell, (int, float)) and not isinstance(cell, bool)
                for cell in child
            )
            for child in value
        )
        if numeric_matrix:
            raise GenerationError(f"numeric matrix payload is forbidden at {path}")
        if numeric and len(value) > MAX_RAW_NUMERIC_ARRAY_ITEMS:
            raise GenerationError(f"numeric vector payload exceeds the bounded aggregate limit at {path}")
        if scalar and len(value) > MAX_RAW_SCALAR_ARRAY_ITEMS:
            raise GenerationError(f"scalar raw array exceeds the bounded aggregate limit at {path}")
        for index, child in enumerate(value):
            _validate_no_forbidden_payload(child, path=f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise GenerationError(f"non-finite value at {path}")


def _compact_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GenerationError("TSV cell is non-finite")
        return format(value, ".15g")
    if isinstance(value, (Mapping, list, tuple)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    else:
        text = str(value)
    text = " ".join(text.replace("\u00a0", " ").split())
    if CONTROL_RE.search(text):
        raise GenerationError("TSV cell contains a disallowed control character")
    return text


def _project_row(filename: str, row: Mapping[str, Any]) -> dict[str, str]:
    normalized: dict[str, tuple[str, Any]] = {}
    for native, value in row.items():
        key = _normalize_key(str(native))
        if key in normalized:
            raise GenerationError(f"{filename} row contains ambiguous aliases for {native}")
        normalized[key] = (str(native), value)
    projected = {}
    for column in TABLE_SCHEMAS[filename]:
        match = normalized.get(_normalize_key(column))
        projected[column] = _compact_cell(match[1] if match else "")
    for column in TABLE_ID_COLUMNS[filename]:
        if not projected[column]:
            raise GenerationError(f"{filename} row lacks identity column {column}")
    return projected


def _component_rows(component: Mapping[str, Any], row_key: str, label: str) -> list[dict[str, Any]]:
    value = _required(component, row_key, label)
    maximum = MAX_REVIEW_ROWS if row_key == "rows" and label == "review" else MAX_TABLE_ROWS
    rows = _rows(value, f"{label}.{row_key}", maximum=maximum)
    receipt_map = _mapping(
        _required(component, "rowReceipts", label), f"{label}.rowReceipts"
    )
    receipt = _mapping(
        _required(receipt_map, row_key, f"{label}.rowReceipts"),
        f"{label}.{row_key} receipt",
    )
    if _integer(_required(receipt, "rowCount", row_key), f"{label}.{row_key}.rowCount") != len(rows):
        raise GenerationError(f"{label}.{row_key} declared row count differs")
    if _sha(_required(receipt, "rowsSha256", row_key), f"{label}.{row_key}.rowsSha256") != sha256_json(rows):
        raise GenerationError(f"{label}.{row_key} declared row hash differs")
    return rows


def derive_tables(summary: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    components = _validate_input_shape(summary)
    numeric_cells = _numeric_sequence_cell_count(summary)
    if numeric_cells > MAX_TOTAL_NUMERIC_ARRAY_CELLS:
        raise GenerationError(
            "analysis summary exceeds the recursive numeric-array cell budget: "
            f"{numeric_cells}>{MAX_TOTAL_NUMERIC_ARRAY_CELLS}"
        )
    _validate_no_forbidden_payload(summary)
    _validate_pins(components)
    _validate_decisions(components)
    receipt_keys: dict[str, set[str]] = defaultdict(set)
    for _filename, (component_name, row_key) in TABLE_SOURCES.items():
        receipt_keys[component_name].add(row_key)
    for component_name, expected in receipt_keys.items():
        receipts = _mapping(
            _required(components[component_name], "rowReceipts", component_name),
            f"{component_name}.rowReceipts",
        )
        if set(receipts) != expected:
            raise GenerationError(
                f"{component_name}.rowReceipts differs: expected {sorted(expected)}"
            )
    projected: dict[str, list[dict[str, str]]] = {}
    for filename in RESEARCH_TSV_FILES:
        component_name, row_key = TABLE_SOURCES[filename]
        native_rows = _component_rows(components[component_name], row_key, component_name)
        rows = [_project_row(filename, row) for row in native_rows]
        rows.sort(key=lambda row: tuple(row[column] for column in TABLE_ID_COLUMNS[filename]))
        identities = [tuple(row[column] for column in TABLE_ID_COLUMNS[filename]) for row in rows]
        if len(identities) != len(set(identities)):
            raise GenerationError(f"{filename} contains duplicate row identities")
        projected[filename] = rows
    _validate_table_semantics(projected)
    preprojected = summary.get("tables")
    if preprojected is not None:
        _reconcile_preprojected(_mapping(preprojected, "tables"), projected)
    return projected


def _validate_table_semantics(tables: Mapping[str, Sequence[Mapping[str, str]]]) -> None:
    for filename, rows in tables.items():
        if not rows:
            raise GenerationError(f"{filename} may not be empty; use an explicit N/A diagnostic row")

    fields = tables["03_NLP_TEXT_FIELD_REGISTRY.tsv"]
    if any(not row["primary_role"] or not row["governance_decision"] for row in fields):
        raise GenerationError("every text field requires a role and governance decision")
    if any(row["primary_role"] == "UNCLASSIFIED_UNSAFE" for row in fields):
        raise GenerationError("unclassified text field entered the registry")

    pairs = tables["11_EVALUATION_PAIR_REGISTRY.tsv"]
    if len(pairs) != 312:
        raise GenerationError("evaluation pair registry must contain exactly 312 rows")
    positives = [row for row in pairs if row["pair_class"] == "KNOWN_REPRESENTATION_POSITIVE"]
    negatives = [row for row in pairs if row["pair_class"] == "DIAGNOSTIC_NEGATIVE_CONTROL"]
    if len(positives) != 3 or len(negatives) != 309:
        raise GenerationError("evaluation pair class counts differ from the frozen registry")
    for row in pairs:
        if not PUBLIC_ID_RE.fullmatch(row["public_object_id_a"]) or not PUBLIC_ID_RE.fullmatch(row["public_object_id_b"]):
            raise GenerationError("evaluation registry contains an invalid public object ID")
        if row["public_object_id_a"] == row["public_object_id_b"]:
            raise GenerationError("evaluation registry contains a self-pair")
    for row in positives:
        if (
            row["task"] != "NLP_TASK_A_KNOWN_REPRESENTATION_RETRIEVAL"
            or row["control_type"] != "SAME_SOURCE_ITEM_DUPLICATE_IMPORT_IDENTITY"
            or row["representation_qualifier"] != "SAME_SOURCE_ITEM_DUPLICATE_IMPORT_IDENTITY"
            or _boolean(row["archive_native_variant_evidence"], "archive_native_variant_evidence")
            or not row["verification_source"]
        ):
            raise GenerationError("Task A importer-identity positive semantics changed")
        for field in (
            "verification_artifact_sha256", "eligibility_artifact_sha256", "verification_locator_sha256"
        ):
            _sha(row[field], f"positive {field}")

    lexical = tables["12_LEXICAL_BASELINE_RESULTS.tsv"]
    required_lexical_groups = {
        (family, aspect)
        for family in REQUIRED_LEXICAL_FAMILIES
        for aspect in REQUIRED_LEXICAL_ASPECT_IDS
    }
    observed_lexical_groups = [
        (row["method_family"], row["aspect_id"]) for row in lexical
    ]
    if (
        set(observed_lexical_groups) != required_lexical_groups
        or len(observed_lexical_groups) != len(required_lexical_groups)
    ):
        raise GenerationError(
            "lexical baselines must be exactly four families across "
            "TITLE/SUBJECT/SOURCE_NARRATIVE"
        )
    for row in lexical:
        _status(row["status"], "lexical", {"PASS", "COMPLETED"})
        if _boolean(row["pair_matrix_materialized"], "lexical pair matrix") or _boolean(row["full_rankings_saved"], "lexical full rankings"):
            raise GenerationError("lexical result crossed the bounded top-k boundary")
        if not _boolean(row["ranking_deterministic"], "lexical determinism"):
            raise GenerationError("completed lexical baseline is not deterministic")
        aspect_id = row["aspect_id"]
        expected_available = EXPECTED_ASPECT_COUNTS[aspect_id]
        if _integer(row["object_count"], "lexical object count") != PUBLIC_OBJECT_COUNT:
            raise GenerationError("lexical object count differs from the public cohort")
        if _integer(row["candidate_object_count"], "lexical candidate count") != PUBLIC_OBJECT_COUNT:
            raise GenerationError("lexical baseline candidate universe is not the public cohort")
        if (
            _integer(row["aspect_available_query_count"], "lexical available queries")
            != expected_available
            or _integer(row["aspect_unavailable_query_count"], "lexical unavailable queries")
            != PUBLIC_OBJECT_COUNT - expected_available
            or _integer(row["query_count"], "lexical query count")
            != expected_available
        ):
            raise GenerationError("lexical default query cohort must equal the aspect-available cohort")
        expected_full_public_cohort = expected_available == PUBLIC_OBJECT_COUNT
        if (
            _boolean(row["full_public_cohort"], "lexical full public cohort")
            != expected_full_public_cohort
            or not _boolean(row["full_aspect_cohort"], "lexical full aspect cohort")
        ):
            raise GenerationError("completed lexical baseline does not cover its full governed cohort")
        if _integer(row["top_k"], "lexical top-k") != 50:
            raise GenerationError("lexical retained top-k differs from the governed bound")
        for column, expected in (
            ("corpus_sha256", CORPUS_SHA256),
            ("corpus_policy_sha256", CORPUS_POLICY_SHA256),
            ("field_registry_sha256", FIELD_REGISTRY_SHA256),
            ("normalization_version", NORMALIZATION_VERSION),
        ):
            if row[column] != expected:
                raise GenerationError(f"lexical result uses a stale {column}")
        for column in (
            "parameters_sha256", "index_sha256", "ranking_ids_sha256",
            "score_observation_sha256", "metadata_proxy_summary_sha256",
        ):
            _sha(row[column], f"completed lexical {column}")
        _positive_integer(row["index_bytes"], "completed lexical index_bytes")
        for column in ("index_build_ms", "exact_query_p50_ms", "exact_query_p95_ms"):
            _nonnegative_number(row[column], f"completed lexical {column}")
        if _integer(row["known_item_positive_pair_count"], "lexical known pairs") != 3:
            raise GenerationError("lexical known-item pair count differs")
        if _integer(row["negative_control_pair_count"], "lexical controls") != 309:
            raise GenerationError("lexical negative-control count differs")
        for column in (
            "known_item_recall_at_1", "known_item_recall_at_5",
            "known_item_recall_at_10", "known_item_recall_at_20",
            "known_item_mrr", "negative_control_at_10_rate",
            "same_source_neighbor_rate_at_20",
        ):
            _number_in_range(row[column], f"completed lexical {column}", minimum=0, maximum=1)

    dense = tables["13_DENSE_MODEL_RESULTS.tsv"]
    for row in dense:
        status = _status(row["status"], "dense", {"PASS", "COMPLETED", "NOT_RUN"})
        if status == "NOT_RUN":
            _required_text(row["limitation"], "NOT_RUN dense limitation")
            _require_zero_or_unavailable(
                row,
                (
                    "object_count", "candidate_object_count",
                    "aspect_available_query_count", "aspect_unavailable_query_count",
                    "query_count", "top_k", "embedding_dimension",
                    "maximum_input_tokens", "batch_size", "index_bytes",
                ),
                "NOT_RUN dense",
            )
            _require_unavailable(
                row,
                (
                    "index_sha256", "ranking_ids_sha256", "score_observation_sha256",
                    "encoding_ms", "documents_per_second", "exact_query_p50_ms",
                    "exact_query_p95_ms", "known_item_recall_at_1",
                    "known_item_recall_at_5", "known_item_recall_at_10",
                    "known_item_recall_at_20", "known_item_mrr",
                    "same_source_neighbor_rate_at_20",
                    "same_language_neighbor_rate_at_20", "hubness_gini_at_20",
                    "top_1_percent_occurrence_share_at_20",
                    "maximum_occurrence_at_20", "mean_sampled_cosine",
                    "first_pc_variance_share", "peak_ram_bytes", "peak_vram_bytes",
                ),
                "NOT_RUN dense",
            )
            continue
        for column, expected in (
            ("corpus_sha256", CORPUS_SHA256),
            ("corpus_policy_sha256", CORPUS_POLICY_SHA256),
            ("field_registry_sha256", FIELD_REGISTRY_SHA256),
            ("normalization_version", NORMALIZATION_VERSION),
        ):
            if row[column] != expected:
                raise GenerationError(f"dense result uses a stale {column}")
        available = _integer(row["aspect_available_query_count"], "dense available")
        unavailable = _integer(row["aspect_unavailable_query_count"], "dense unavailable")
        if (
            _integer(row["object_count"], "dense object count") != PUBLIC_OBJECT_COUNT
            or _integer(row["candidate_object_count"], "dense candidate count") != PUBLIC_OBJECT_COUNT
            or available + unavailable != PUBLIC_OBJECT_COUNT
            or _integer(row["query_count"], "dense query count") != available
            or _boolean(row["full_public_cohort"], "dense full public cohort")
            != (available == PUBLIC_OBJECT_COUNT)
            or not _boolean(row["full_aspect_cohort"], "dense full aspect cohort")
            or _integer(row["top_k"], "dense top-k") != 50
        ):
            raise GenerationError("completed dense result lacks its full governed cohort")
        for column in ("index_sha256", "ranking_ids_sha256", "score_observation_sha256"):
            _sha(row[column], f"completed dense {column}")
        for column in (
            "embedding_dimension", "maximum_input_tokens", "batch_size", "index_bytes",
        ):
            _positive_integer(row[column], f"completed dense {column}")
        _required_text(row["device"], "completed dense device")
        for column in (
            "encoding_ms", "documents_per_second", "exact_query_p50_ms",
            "exact_query_p95_ms", "peak_ram_bytes",
        ):
            _nonnegative_number(row[column], f"completed dense {column}")
        for column in (
            "known_item_recall_at_1", "known_item_recall_at_5",
            "known_item_recall_at_10", "known_item_recall_at_20",
            "known_item_mrr", "same_source_neighbor_rate_at_20", "hubness_gini_at_20",
            "top_1_percent_occurrence_share_at_20", "first_pc_variance_share",
        ):
            _number_in_range(row[column], f"completed dense {column}", minimum=0, maximum=1)
        _number_in_range(
            row["mean_sampled_cosine"], "completed dense mean_sampled_cosine",
            minimum=-1, maximum=1,
        )
        _nonnegative_number(row["maximum_occurrence_at_20"], "completed dense maximum occurrence")
    completed_dense_groups = {
        (row["model_id"], row["input_variant"], row["aspect_id"])
        for row in dense
        if row["status"].upper() in {"PASS", "COMPLETED"}
    }

    metadata = tables["15_METADATA_HOLDOUT_RESULTS.tsv"]
    targets = {row["target"] for row in metadata}
    if targets != {"medium", "theme", "object_type"}:
        raise GenerationError("metadata holdout targets must be exactly medium/theme/object_type")
    required_metadata_variants = {
        "ORIGINAL_APPROVED_TEXT", "TARGET_LABEL_MASKED", "ALL_CONTEXT_LABELS_MASKED"
    }
    for target in targets:
        variants = {row["mask_variant"] for row in metadata if row["target"] == target}
        if not required_metadata_variants.issubset(variants):
            raise GenerationError(f"metadata holdout variants incomplete for {target}")
        for row in metadata:
            if row["target"] == target and row["mask_variant"] != "ORIGINAL_APPROVED_TEXT":
                if not _boolean(row["target_labels_masked"], "target labels masked"):
                    raise GenerationError("masked metadata variant did not mask target labels")
    for row in metadata:
        status = _status(row["status"], "metadata holdout", {"PASS", "COMPLETED", "NOT_RUN"})
        if not _boolean(row["proxy_only"], "metadata proxy-only"):
            raise GenerationError("metadata holdout was presented as ground truth")
        if status == "NOT_RUN":
            _required_text(row["limitation"], "NOT_RUN metadata limitation")
            _require_zero_or_unavailable(
                row,
                (
                    "label_count", "evaluable_query_count",
                    "target_literal_count_before", "target_literal_count_after",
                ),
                "NOT_RUN metadata holdout",
            )
            _require_unavailable(
                row,
                (
                    "majority_label_object_share", "precision_at_5",
                    "precision_at_10", "precision_at_20", "ndcg_at_5",
                    "ndcg_at_10", "ndcg_at_20", "label_contract_sha256",
                    "rows_sha256",
                ),
                "NOT_RUN metadata holdout",
            )
            continue
        for column in ("label_contract_sha256", "rows_sha256"):
            _sha(row[column], f"completed metadata {column}")
        for column in ("label_count", "evaluable_query_count"):
            _positive_integer(row[column], f"completed metadata {column}")
        for column in (
            "majority_label_object_share", "precision_at_5", "precision_at_10",
            "precision_at_20", "ndcg_at_5", "ndcg_at_10", "ndcg_at_20",
        ):
            _number_in_range(row[column], f"completed metadata {column}", minimum=0, maximum=1)
        if row["mask_variant"] == "ORIGINAL_APPROVED_TEXT":
            _require_unavailable(
                row,
                ("target_literal_count_before", "target_literal_count_after"),
                "unmasked metadata control",
            )
            if (
                _boolean(row["target_labels_masked"], "unmasked target-label flag")
                or _boolean(row["context_labels_masked"], "unmasked context-label flag")
            ):
                raise GenerationError("unmasked metadata control claims label masking")
        else:
            for column in ("target_literal_count_before", "target_literal_count_after"):
                if _integer(row[column], f"completed metadata {column}") < 0:
                    raise GenerationError(f"completed metadata {column} is negative")
            if _integer(
                row["target_literal_count_after"], "masked target literals after"
            ) != 0:
                raise GenerationError("metadata label literal remains after masking")

    leakage_rows = tables["16_SOURCE_LANGUAGE_LEAKAGE.tsv"]
    leakage_dimensions = {row["leakage_dimension"] for row in leakage_rows}
    if not {"SOURCE", "LANGUAGE"}.issubset(leakage_dimensions):
        raise GenerationError("source and language leakage diagnostics are both required")
    for row in leakage_rows:
        status = _status(
            row["status"],
            "leakage",
            {"PASS", "COMPLETED", "PASS_SCRIPT_ONLY", "NOT_RUN"},
        )
        if status in {"PASS", "COMPLETED"}:
            _number(row["metric_value"], "completed leakage metric_value")
        elif status == "PASS_SCRIPT_ONLY":
            if (
                row["leakage_dimension"] != "LANGUAGE"
                or row["probe_or_metric"] != "SAME_SCRIPT_NEIGHBOR_RATE_NOT_LANGUAGE"
                or _boolean(
                    row["reliable_language_labels_only"],
                    "script-only reliable-language flag",
                )
                or _integer(row["label_count"], "script-only language label count") != 0
            ):
                raise GenerationError("PASS_SCRIPT_ONLY is not a governed script diagnostic")
            _number_in_range(
                row["metric_value"], "script-only neighborhood rate",
                minimum=0, maximum=1,
            )
            _require_unavailable(
                row,
                ("majority_baseline", "macro_f1", "cross_validation_folds"),
                "PASS_SCRIPT_ONLY leakage",
            )
        else:
            _required_text(row["reason"], "NOT_RUN leakage reason")
            _require_unavailable(
                row,
                ("metric_value", "majority_baseline", "macro_f1"),
                "NOT_RUN leakage",
            )
            _require_zero_or_unavailable(
                row,
                ("label_count", "cross_validation_folds"),
                "NOT_RUN leakage",
            )

    cross_language = tables["14_CROSS_LANGUAGE_RESULTS.tsv"]
    for row in cross_language:
        if (
            _integer(row["verified_pair_count"], "cross-language verified pairs") != 0
            or _integer(row["directional_query_count"], "cross-language directional queries") != 0
            or _integer(row["review_row_count"], "cross-language review rows") != 0
            or _integer(row["model_created_positive_pair_count"], "cross-language model-created pairs") != 0
            or _integer(row["generated_translation_count"], "cross-language generated translations") != 0
            or row["status"].upper() != "NOT_RUN"
        ):
            raise GenerationError("Task B must remain an honest zero-positive NOT_RUN evaluation")
        _required_text(row["reason"], "Task B NOT_RUN reason")
        _require_unavailable(
            row,
            (
                "recall_at_1", "recall_at_5", "recall_at_10", "recall_at_20",
                "mean_reciprocal_rank", "median_rank", "maximum_rank",
                "mean_cosine_observation",
            ),
            "Task B NOT_RUN",
        )
        _sha(row["review_rows_sha256"], "Task B empty review-row receipt")

    hubness_rows = tables["17_HUBNESS_AND_ANISOTROPY.tsv"]
    observed_hubness_groups = {
        (row["model_id"], row["input_variant"], row["aspect_id"])
        for row in hubness_rows
    }
    if observed_hubness_groups != completed_dense_groups:
        raise GenerationError(
            "hubness/anisotropy groups differ from completed dense result groups"
        )
    for row in hubness_rows:
        diagnostic_type = row["diagnostic_type"]
        if diagnostic_type == "HUBNESS":
            _status(row["status"], "hubness", {"PASS", "COMPLETED"})
            if _integer(row["k"], "hubness k") not in REQUIRED_DIAGNOSTIC_K:
                raise GenerationError("hubness row uses an undeclared k")
            for column in (
                "mean_k_occurrence", "variance_k_occurrence", "skewness", "gini",
                "top_1_percent_occurrence_share", "maximum_occurrence",
                "zero_occurrence_object_count", "total_occurrence_count",
                "expected_occurrence_count",
            ):
                _number(row[column], f"completed hubness {column}")
            if _integer(row["total_occurrence_count"], "hubness total") != _integer(
                row["expected_occurrence_count"], "hubness expected"
            ):
                raise GenerationError("hubness occurrence accounting differs")
            continue
        if diagnostic_type == "ANISOTROPY":
            status = _status(
                row["status"], "anisotropy", {"PASS", "COMPLETED", "NOT_RUN"}
            )
            for column in (
                "mean_sampled_cosine", "cosine_variance", "pair_observation_count",
                "first_pc_variance_share", "norm_p50", "norm_p95",
                "nearest_neighbor_cosine_distance_p50",
                "nearest_neighbor_cosine_distance_p95", "exact_mean_off_diagonal_cosine",
            ):
                _number(row[column], f"anisotropy {column}")
            pre_values = (
                row["pre_normalization_norm_p50"], row["pre_normalization_norm_p95"]
            )
            pre_missing = all(value in {"", "N/A", "NOT_RUN"} for value in pre_values)
            if status in {"PASS", "COMPLETED"}:
                for column in (
                    "pre_normalization_norm_p50", "pre_normalization_norm_p95"
                ):
                    _number(row[column], f"completed anisotropy {column}")
            elif not pre_missing:
                raise GenerationError(
                    "NOT_RUN anisotropy must omit both pre-normalization norm diagnostics"
                )
            else:
                _required_text(row["limitation"], "NOT_RUN anisotropy limitation")
            continue
        if diagnostic_type.startswith("HUBNESS_ASSOCIATION_"):
            status = _status(
                row["status"], "hubness association", {"PASS", "COMPLETED", "NOT_RUN"}
            )
            dimension = diagnostic_type.removeprefix("HUBNESS_ASSOCIATION_")
            if dimension not in REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS:
                raise GenerationError(f"undeclared hubness association dimension: {dimension}")
            if row["association_dimension"] != dimension:
                raise GenerationError("hubness association dimension field disagrees with its diagnostic type")
            _sha(row["association_inputs_sha256"], "hubness association input receipt")
            if status in {"PASS", "COMPLETED"}:
                if row["association_type"] in {"", "N/A", "NOT_RUN"}:
                    raise GenerationError("completed hubness association lacks an executed method")
                _number(row["association_value"], "completed hubness association value")
                _sha(
                    row["association_observation_sha256"],
                    "completed hubness association observation",
                )
            elif status == "NOT_RUN":
                if row["association_type"] != "NOT_RUN" or row["association_value"] not in {
                    "",
                    "N/A",
                    "NOT_RUN",
                }:
                    raise GenerationError("NOT_RUN hubness association contains computed evidence")
                if not row["limitation"] or row["limitation"] in {"N/A", "NOT_RUN"}:
                    raise GenerationError("NOT_RUN hubness association lacks a limitation")
            continue
        raise GenerationError(f"undeclared hubness diagnostic type: {diagnostic_type}")

    for group in completed_dense_groups:
        model_rows = [
            row for row in hubness_rows
            if (row["model_id"], row["input_variant"], row["aspect_id"]) == group
        ]
        hub_rows_for_group = [row for row in model_rows if row["diagnostic_type"] == "HUBNESS"]
        if (
            {row["k"] for row in hub_rows_for_group} != {"10", "20", "50"}
            or len(hub_rows_for_group) != 3
        ):
            raise GenerationError(f"completed dense group lacks exact hubness k rows: {group}")
        anisotropy_rows = [row for row in model_rows if row["diagnostic_type"] == "ANISOTROPY"]
        if len(anisotropy_rows) != 1:
            raise GenerationError(f"completed dense group requires exactly one anisotropy row: {group}")
        expected_missing: set[str] = set()
        for dimension in REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS:
            association_rows = [
                row for row in model_rows
                if row["diagnostic_type"] == f"HUBNESS_ASSOCIATION_{dimension}"
            ]
            if (
                {row["k"] for row in association_rows} != {"10", "20", "50"}
                or len(association_rows) != 3
            ):
                raise GenerationError(
                    f"completed dense group lacks exact {dimension} association k rows: {group}"
                )
            statuses = {row["status"].upper() for row in association_rows}
            if statuses == {"NOT_RUN"}:
                expected_missing.add(dimension)
            elif not statuses <= {"PASS", "COMPLETED"}:
                raise GenerationError(
                    f"hubness association status differs across k for {group}/{dimension}"
                )
        if anisotropy_rows[0]["status"].upper() == "NOT_RUN":
            expected_missing.add("PRE_NORMALIZATION_NORMS")
        expected_overall = "NOT_RUN" if expected_missing else "PASS"
        overall_statuses = {row["overall_diagnostic_status"].upper() for row in model_rows}
        association_receipts = {row["association_inputs_sha256"] for row in model_rows}
        missing_sets = {
            frozenset(_json_string_set(row["missing_required_diagnostics"], "missing diagnostics"))
            for row in model_rows
        }
        if overall_statuses != {expected_overall} or missing_sets != {frozenset(expected_missing)}:
            raise GenerationError(
                f"hubness overall/missing diagnostics are not derived from row evidence: {group}"
            )
        if len(association_receipts) != 1:
            raise GenerationError(f"hubness association receipt differs within group: {group}")
        _sha(next(iter(association_receipts)), "hubness association group receipt")

    robustness_rows = tables["18_ROBUSTNESS_AND_ABLATION.tsv"]
    declared_ablation_ids = set(DECLARED_ROBUSTNESS_ABLATION_IDS)
    lexical_family_ids = {
        "BM25F": "NLP-L0",
        "CHAR_NGRAM": "NLP-L1",
        "WORD_NGRAM": "NLP-L2",
        "LEXICAL_HYBRID": "NLP-L3",
    }
    expected_robustness_groups: dict[tuple[str, str], dict[str, str]] = {}
    for row in lexical:
        if row["aspect_id"] != "NLP_TITLE":
            continue
        key = (lexical_family_ids[row["method_family"]], row["model_id"])
        expected_robustness_groups[key] = {
            "inputVariant": "ORIGINAL_APPROVED",
            "aspectId": row["aspect_id"],
            "indexSha256": row["index_sha256"],
        }
    for row in dense:
        if row["status"].upper() not in {"PASS", "COMPLETED"} or row["aspect_id"] != "NLP_TITLE":
            continue
        reference_id = (
            f"{row['model_id']}-TITLE-{row['input_variant']}"
        )
        expected_robustness_groups[(row["model_id"], reference_id)] = {
            "inputVariant": row["input_variant"],
            "aspectId": row["aspect_id"],
            "indexSha256": row["index_sha256"],
        }
    robustness_groups: dict[tuple[str, str], list[Mapping[str, str]]] = defaultdict(list)
    for row in robustness_rows:
        robustness_groups[(row["model_id"], row["reference_method_id"])].append(row)
    if set(robustness_groups) != set(expected_robustness_groups):
        raise GenerationError(
            "robustness model/reference groups differ from governed TITLE baselines"
        )
    for group, rows in robustness_groups.items():
        reference = expected_robustness_groups[group]
        observed = {row["ablation_id"] for row in rows}
        if observed != declared_ablation_ids:
            raise GenerationError(f"robustness ablation registry is incomplete for {group}")
        for row in rows:
            if (
                row["reference_input_variant"] != reference["inputVariant"]
                or row["reference_aspect_id"] != reference["aspectId"]
                or row["reference_index_sha256"] != reference["indexSha256"]
            ):
                raise GenerationError(
                    f"robustness reference receipt differs from its governed baseline: {group}"
                )
        for ablation_id in DECLARED_ROBUSTNESS_ABLATION_IDS:
            ablation_rows = [row for row in rows if row["ablation_id"] == ablation_id]
            statuses = {row["status"].upper() for row in ablation_rows}
            if statuses <= {"PASS", "COMPLETED"}:
                if (
                    len(ablation_rows) != len(REQUIRED_DIAGNOSTIC_K)
                    or {_integer(row["k"], "robustness k") for row in ablation_rows}
                    != set(REQUIRED_DIAGNOSTIC_K)
                ):
                    raise GenerationError(
                        f"executed robustness ablation lacks k=10/20/50: {group}/{ablation_id}"
                    )
            elif statuses == {"NOT_RUN"}:
                if len(ablation_rows) != 1 or _integer(
                    ablation_rows[0]["k"], "NOT_RUN robustness k"
                ) != 0:
                    raise GenerationError(
                        f"NOT_RUN robustness ablation must have one k=0 row: {group}/{ablation_id}"
                    )
            else:
                raise GenerationError(
                    f"robustness ablation mixes executed/NOT_RUN statuses: {group}/{ablation_id}"
                )

    for row in robustness_rows:
        if row["robustness_suite_status"] != "STOPPED_RECOVERABLE_CHECKPOINT":
            raise GenerationError("robustness suite must retain the stopped-checkpoint status")
        if row["reference_corpus_sha256"] != CORPUS_SHA256:
            raise GenerationError("robustness suite uses a stale ranking corpus")
        for column in (
            "reference_index_sha256", "reference_ranking_ids_sha256", "suite_sha256"
        ):
            _sha(row[column], f"robustness {column}")
        if _integer(row["declared_ablation_count"], "declared robustness ablations") != len(
            DECLARED_ROBUSTNESS_ABLATION_IDS
        ):
            raise GenerationError("robustness suite does not bind all 17 declared variants")
        executed = _json_string_set(row["executed_ablation_ids"], "executed ablation IDs")
        not_run = _json_string_set(row["not_run_ablation_ids"], "not-run ablation IDs")
        if executed & not_run or executed | not_run != declared_ablation_ids:
            raise GenerationError("robustness executed/not-run partition is incomplete")
        status = _status(row["status"], "robustness", {"PASS", "COMPLETED", "NOT_RUN"})
        if status in {"PASS", "COMPLETED"}:
            if row["ablation_id"] not in executed:
                raise GenerationError("completed robustness row is not in the executed partition")
            for column in (
                "mean_top_k_overlap", "median_top_k_overlap", "p05_top_k_overlap",
                "mean_rank_correlation", "median_rank_correlation",
                "p05_rank_correlation", "same_source_rate_change",
                "hubness_gini_change",
            ):
                _number(row[column], f"completed robustness {column}")
        elif status == "NOT_RUN":
            if row["ablation_id"] not in not_run:
                raise GenerationError("NOT_RUN robustness row is not in the not-run partition")
            _required_text(row["limitation"], "NOT_RUN robustness limitation")
            if _integer(row["query_count"], "NOT_RUN robustness query count") != 0:
                raise GenerationError("NOT_RUN robustness row has a nonzero query cohort")
            _require_unavailable(
                row,
                (
                    "mean_top_k_overlap", "median_top_k_overlap",
                    "p05_top_k_overlap", "mean_rank_correlation",
                    "median_rank_correlation", "p05_rank_correlation",
                    "same_source_rate_change", "same_language_rate_change",
                    "hubness_gini_change", "known_item_recall_change",
                ),
                "NOT_RUN robustness",
            )

    structured = tables["20_STRUCTURED_NLP_DISAGREEMENT.tsv"]
    summary_models = {
        row["structured_model_id"] for row in structured
        if row["row_type"] == "SUMMARY"
    }
    if summary_models != {"M2", "M5", "M7"}:
        raise GenerationError("structured/NLP summaries must cover M2, M5, and M7")
    for row in structured:
        if _boolean(row["structured_nlp_fusion_selected"], "structured fusion") or _boolean(row["structured_nlp_fusion_weights_selected"], "fusion weights"):
            raise GenerationError("structured/NLP fusion was selected")
        _status(row["status"], "structured/NLP", {"PARTIAL", "NOT_RUN"})
        _required_text(row["limitation"], "structured/NLP limitation")

    for row in tables["19_ASPECT_DISAGREEMENT.tsv"]:
        status = _status(
            row["status"], "aspect disagreement", {"PASS", "COMPLETED", "NOT_RUN"}
        )
        if status in {"PASS", "COMPLETED"}:
            _number(row["language_neighbor_rate_a"], "completed aspect language rate A")
            _number(row["language_neighbor_rate_b"], "completed aspect language rate B")
        else:
            _required_text(row["limitation"], "NOT_RUN aspect-disagreement limitation")
            _require_unavailable(
                row,
                ("language_neighbor_rate_a", "language_neighbor_rate_b"),
                "NOT_RUN aspect disagreement",
            )

    for row in tables["21_HYBRID_EXPERIMENTS.tsv"]:
        status = _status(row["status"], "hybrid", {"PASS", "COMPLETED", "NOT_RUN"})
        if status in {"PASS", "COMPLETED"}:
            _positive_integer(row["eligible_query_count"], "completed hybrid eligible queries")
            _number_in_range(
                row["known_item_recall"], "completed hybrid known-item recall",
                minimum=0, maximum=1,
            )
            _sha(row["ranking_ids_sha256"], "completed hybrid ranking hash")
            _positive_integer(row["rrf_constant"], "completed hybrid RRF constant")
            _positive_integer(row["evaluation_k"], "completed hybrid evaluation k")
        else:
            _required_text(row["limitation"], "NOT_RUN hybrid limitation")
            if _integer(row["eligible_query_count"], "NOT_RUN hybrid eligible queries") != 0:
                raise GenerationError("NOT_RUN hybrid has an eligible query cohort")
            _require_unavailable(
                row, ("known_item_recall",), "NOT_RUN hybrid"
            )
            _sha(row["ranking_ids_sha256"], "NOT_RUN hybrid bounded ranking hash")
            _positive_integer(row["rrf_constant"], "NOT_RUN hybrid RRF constant")
            _positive_integer(row["evaluation_k"], "NOT_RUN hybrid evaluation k")

    review = tables["22_NLP_REVIEW_PACKET.tsv"]
    for row in review:
        for key in ("anchor_public_object_id", "candidate_public_object_id"):
            if not PUBLIC_ID_RE.fullmatch(row[key]):
                raise GenerationError("review packet contains a non-public identity")
        if len(row["anchor_title"]) > 180 or len(row["candidate_title"]) > 180:
            raise GenerationError("review title exceeds the public-safe bound")

    for filename in (
        "12_LEXICAL_BASELINE_RESULTS.tsv", "13_DENSE_MODEL_RESULTS.tsv",
        "14_CROSS_LANGUAGE_RESULTS.tsv", "15_METADATA_HOLDOUT_RESULTS.tsv",
        "16_SOURCE_LANGUAGE_LEAKAGE.tsv", "18_ROBUSTNESS_AND_ABLATION.tsv",
        "19_ASPECT_DISAGREEMENT.tsv", "20_STRUCTURED_NLP_DISAGREEMENT.tsv",
        "21_HYBRID_EXPERIMENTS.tsv", "22_NLP_REVIEW_PACKET.tsv",
    ):
        for row in tables[filename]:
            for column in ("historical_relation", "semantic_relation", "probability"):
                if _boolean(row[column], f"{filename} {column}"):
                    raise GenerationError(f"{filename} asserts prohibited {column}")


def _reconcile_preprojected(
    preprojected: Mapping[str, Any], derived: Mapping[str, Sequence[Mapping[str, str]]]
) -> None:
    if set(preprojected) != set(RESEARCH_TSV_FILES):
        raise GenerationError("preprojected tables do not cover the exact 17-file inventory")
    for filename in RESEARCH_TSV_FILES:
        bundle = _mapping(preprojected[filename], f"tables.{filename}")
        columns = tuple(map(str, _required(bundle, "columns", filename)))
        if columns != TABLE_SCHEMAS[filename]:
            raise GenerationError(f"preprojected columns differ for {filename}")
        rows = [_project_row(filename, row) for row in _rows(_required(bundle, "rows", filename), filename)]
        rows.sort(key=lambda row: tuple(row[column] for column in TABLE_ID_COLUMNS[filename]))
        if rows != list(derived[filename]):
            raise GenerationError(f"preprojected rows differ from component projection: {filename}")
        if _integer(_required(bundle, "rowCount", filename), f"{filename}.rowCount") != len(rows):
            raise GenerationError(f"preprojected row count differs: {filename}")
        if _sha(_required(bundle, "rowsSha256", filename), f"{filename}.rowsSha256") != sha256_json(rows):
            raise GenerationError(f"preprojected row hash differs: {filename}")


def tsv_bytes(filename: str, rows: Sequence[Mapping[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(TABLE_SCHEMAS[filename])
    for row in rows:
        if set(row) != set(TABLE_SCHEMAS[filename]):
            raise GenerationError(f"{filename} projected row schema changed")
        writer.writerow([row[column] for column in TABLE_SCHEMAS[filename]])
    payload = output.getvalue().encode("utf-8")
    if len(payload) > MAX_TSV_FILE_BYTES:
        raise GenerationError(f"{filename} exceeds the bounded TSV size")
    return payload


def validate_output_urls(filename: str, text: str) -> None:
    """Allow only the three governed official-source locators in the pair TSV."""

    if not URL_RE.search(text):
        return
    if filename != "11_EVALUATION_PAIR_REGISTRY.tsv":
        raise GenerationError(f"{filename} contains URL material")
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter="\t")
    if tuple(reader.fieldnames or ()) != TABLE_SCHEMAS[filename]:
        raise GenerationError("evaluation pair registry schema changed during URL validation")
    allowed_count = 0
    for row in reader:
        if None in row:
            raise GenerationError("evaluation pair registry row is malformed")
        for column, value in row.items():
            if not URL_RE.search(value or ""):
                continue
            if (
                column != "verification_source"
                or not OFFICIAL_VERIFICATION_SOURCE_RE.fullmatch(value or "")
            ):
                raise GenerationError("evaluation pair registry contains an ungoverned URL")
            allowed_count += 1
    if allowed_count != 3:
        raise GenerationError("evaluation pair registry official-source locator count differs")


def _row_receipt(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"rowCount": len(rows), "rowsSha256": sha256_json(list(rows))}


_DROP_RAW_KEYS = {
    "officialrepositoryurl", "environmentpath", "localpath", "snapshotpath",
    "downloadurl", "canonicalsourceurl", "displayoriginal", "semanticnormalized",
    "lexicalcasefolded", "rawtext", "text",
}


def _sanitize_raw(value: Any, *, path: str = "$", keep_run_rows: bool = False) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for native, child in sorted(value.items(), key=lambda item: str(item[0])):
            key = str(native)
            normalized = _normalize_key(key)
            if normalized in _DROP_RAW_KEYS:
                continue
            is_row_array = isinstance(child, Sequence) and not isinstance(
                child, (str, bytes, bytearray)
            )
            if is_row_array and normalized in {
                "fieldregistryrows", "languagescriptrows", "textlengthrows", "boilerplaterows",
                "artifactrows", "resultrows", "crosslanguagerows", "holdoutrows",
                "sourcelanguagerows",
            } or (is_row_array and normalized == "rows" and not keep_run_rows):
                rows = _rows(child, f"{path}.{key}", maximum=MAX_TABLE_ROWS)
                result[key + "Receipt"] = _row_receipt(rows)
                continue
            result[key] = _sanitize_raw(
                child,
                path=f"{path}.{key}",
                keep_run_rows=keep_run_rows,
            )
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        maximum = MAX_RUN_ROWS if keep_run_rows else MAX_TABLE_ROWS
        if len(value) > maximum:
            raise GenerationError(f"raw array exceeds bound at {path}")
        scalar = all(
            not isinstance(child, (Mapping, Sequence))
            or isinstance(child, (str, bytes, bytearray))
            for child in value
        )
        numeric = scalar and all(
            isinstance(child, (int, float)) and not isinstance(child, bool)
            for child in value
        )
        numeric_matrix = any(
            isinstance(child, Sequence)
            and not isinstance(child, (str, bytes, bytearray))
            and child
            and all(
                isinstance(cell, (int, float)) and not isinstance(cell, bool)
                for cell in child
            )
            for child in value
        )
        if numeric_matrix:
            raise GenerationError(f"numeric matrix payload is forbidden at {path}")
        if numeric and len(value) > MAX_RAW_NUMERIC_ARRAY_ITEMS:
            raise GenerationError(f"numeric vector payload exceeds the bounded aggregate limit at {path}")
        if scalar and len(value) > MAX_RAW_SCALAR_ARRAY_ITEMS:
            raise GenerationError(f"scalar raw array exceeds the bounded aggregate limit at {path}")
        return [_sanitize_raw(child, path=f"{path}[]", keep_run_rows=False) for child in value]
    if isinstance(value, str):
        text = " ".join(value.replace("\u00a0", " ").split())
        if URL_RE.search(text) or UUID_RE.search(text) or PRIVATE_ID_RE.search(text) or CONTROL_RE.search(text):
            raise GenerationError(f"unsafe raw string at {path}")
        return text
    if isinstance(value, float) and not math.isfinite(value):
        raise GenerationError(f"non-finite raw number at {path}")
    return value


def _research_receipts(
    research_dir: Path | None,
    tsv_payloads: Mapping[str, bytes],
) -> tuple[dict[str, dict[str, Any]], bool]:
    if research_dir is None:
        return {}, False
    if research_dir.is_symlink():
        raise GenerationError("research directory cannot be a symlink")
    receipts: dict[str, dict[str, Any]] = {}
    markdown_total = 0
    for filename in RESEARCH_FILES:
        if filename in tsv_payloads:
            payload = tsv_payloads[filename]
        else:
            path = research_dir / filename
            if not path.is_file() or path.is_symlink():
                raise GenerationError(f"research receipt binding requires {filename}")
            payload = path.read_bytes()
        if filename.endswith(".md"):
            if len(payload) > MAX_MARKDOWN_FILE_BYTES:
                raise GenerationError(f"research Markdown exceeds bounded size: {filename}")
            markdown_total += len(payload)
        receipts[filename] = {"bytes": len(payload), "sha256": sha256_bytes(payload)}
    if markdown_total > MAX_MARKDOWN_TOTAL_BYTES:
        raise GenerationError("research Markdown exceeds the bounded aggregate size")
    return receipts, True


def _raw_wrapper(
    component: str,
    payload: Any,
    *,
    analysis_sha256: str,
    table_receipts: Mapping[str, Any],
) -> dict[str, Any]:
    sanitized = _sanitize_raw(payload, keep_run_rows=component == "runs-performance-security")
    return {
        "schemaVersion": RAW_SCHEMA_VERSION,
        "component": component,
        "analysisSummarySha256": analysis_sha256,
        "tableReceipts": table_receipts,
        "payload": sanitized,
        "payloadSha256": sha256_json(sanitized),
    }


def build_output_files(
    summary: Mapping[str, Any],
    *,
    research_dir_for_receipts: Path | None = None,
) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, Any]]:
    components = _validate_input_shape(summary)
    tables = derive_tables(summary)
    research = {filename: tsv_bytes(filename, tables[filename]) for filename in RESEARCH_TSV_FILES}
    table_receipts = {
        filename: {
            "bytes": len(research[filename]),
            "columns": list(TABLE_SCHEMAS[filename]),
            "columnCount": len(TABLE_SCHEMAS[filename]),
            "rowCount": len(tables[filename]),
            "rowsSha256": sha256_json(tables[filename]),
            "sha256": sha256_bytes(research[filename]),
        }
        for filename in RESEARCH_TSV_FILES
    }
    material = {key: value for key, value in summary.items() if key != "analysisSummarySha256"}
    analysis_sha256 = sha256_json(material)
    research_receipts, bound = _research_receipts(research_dir_for_receipts, research)

    central_payload = {
        "source": components["source"],
        "governance": components["governance"],
        "boundary": components["boundary"],
        "evaluationRegistry": components["evaluationRegistry"],
        "models": components["models"],
        "review": components["review"],
        "performance": components["performance"],
        "security": components["security"],
        "decision": components["decision"],
        "invariants": components["invariants"],
        "researchFileReceipts": research_receipts,
        "researchReceiptsComplete": bound,
    }
    raw_payloads: dict[str, tuple[str, Any]] = {
        "nlp-round1-analysis-summary.json": ("central", central_payload),
        "corpus-governance-summary.json": (
            "corpus-governance", {"source": components["source"], "boundary": components["boundary"], "governance": components["governance"]},
        ),
        "language-tokenization-summary.json": (
            "language-tokenization", {"boundary": components["boundary"], "governance": components["governance"], "leakage": components["leakage"]},
        ),
        "duplication-boilerplate-summary.json": (
            "duplication-boilerplate", {"governance": components["governance"], "evaluationRegistry": components["evaluationRegistry"]},
        ),
        "model-artifact-summary.json": ("model-artifacts", components["models"]),
        "evaluation-registry-summary.json": ("evaluation-registry", components["evaluationRegistry"]),
        "lexical-baseline-summary.json": ("lexical", components["lexical"]),
        "dense-cross-language-summary.json": ("dense-cross-language", components["dense"]),
        "metadata-leakage-summary.json": (
            "metadata-leakage", {"metadata": components["metadata"], "leakage": components["leakage"]},
        ),
        "hubness-robustness-summary.json": (
            "hubness-robustness", {"hubness": components["hubness"], "robustness": components["robustness"]},
        ),
        "aspect-structured-hybrid-summary.json": (
            "aspect-structured-hybrid", {"aspects": components["aspects"], "structured": components["structured"], "hybrid": components["hybrid"]},
        ),
        "review-architecture-summary.json": (
            "review-architecture", {"review": components["review"], "decision": components["decision"]},
        ),
        "run-performance-security-summary.json": (
            "runs-performance-security", {"runs": components["runs"], "performance": components["performance"], "security": components["security"], "decision": components["decision"], "invariants": components["invariants"]},
        ),
    }
    if set(raw_payloads) != set(RAW_FILES):
        raise GenerationError("internal raw inventory drifted")
    raw_objects = {
        filename: _raw_wrapper(
            component,
            payload,
            analysis_sha256=analysis_sha256,
            table_receipts=table_receipts,
        )
        for filename, (component, payload) in raw_payloads.items()
    }
    raw = {filename: canonical_json_bytes(raw_objects[filename], pretty=True) for filename in RAW_FILES}
    _validate_output_safety(research, raw)
    receipt = {
        "schemaVersion": GENERATION_SCHEMA_VERSION,
        "analysisSummarySha256": analysis_sha256,
        "researchTsvCount": len(research),
        "auditRawCount": len(raw),
        "researchReceiptsComplete": bound,
        "tableReceipts": table_receipts,
        "rawReceipts": {
            name: {"bytes": len(payload), "sha256": sha256_bytes(payload)} for name, payload in raw.items()
        },
    }
    return research, raw, receipt


def _validate_output_safety(research: Mapping[str, bytes], raw: Mapping[str, bytes]) -> None:
    if set(research) != set(RESEARCH_TSV_FILES) or set(raw) != set(RAW_FILES):
        raise GenerationError("output inventory differs from the frozen contract")
    raw_total = 0
    for filename, payload in {**research, **raw}.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise GenerationError(f"{filename} is not UTF-8") from error
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or b"\r" in payload:
            raise GenerationError(f"{filename} does not use canonical LF framing")
        if UUID_RE.search(text) or PRIVATE_ID_RE.search(text):
            raise GenerationError(f"{filename} contains private/URL material")
        validate_output_urls(filename, text)
        if filename in raw:
            if len(payload) > MAX_RAW_FILE_BYTES:
                raise GenerationError(f"{filename} exceeds the raw-file bound")
            raw_total += len(payload)
    if raw_total > MAX_RAW_TOTAL_BYTES:
        raise GenerationError("aggregate raw evidence exceeds the total size bound")


def load_analysis_summary(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise GenerationError("analysis summary must be one regular file")
    payload = path.read_bytes()
    if len(payload) > MAX_INPUT_BYTES:
        raise GenerationError("analysis summary exceeds the input size bound")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GenerationError("analysis summary is not strict UTF-8 JSON") from error
    return _mapping(value, "analysis summary")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GenerationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def run_twice(
    analysis_path: Path,
    *,
    research_dir_for_receipts: Path | None = None,
) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, Any]]:
    first_summary = load_analysis_summary(analysis_path)
    second_summary = load_analysis_summary(analysis_path)
    if canonical_json_bytes(first_summary) != canonical_json_bytes(second_summary):
        raise GenerationError("analysis summary changed between deterministic passes")
    first = build_output_files(first_summary, research_dir_for_receipts=research_dir_for_receipts)
    second = build_output_files(second_summary, research_dir_for_receipts=research_dir_for_receipts)
    if first != second:
        raise GenerationError("two evidence projections were not byte-identical")
    return first


def _validate_output_directories(research_dir: Path, audit_raw_dir: Path) -> None:
    for path, label in ((research_dir, "research"), (audit_raw_dir, "audit raw")):
        if path.exists() and (not path.is_dir() or path.is_symlink()):
            raise GenerationError(f"{label} output must be a real directory")
    if research_dir.exists():
        unexpected = {path.name for path in research_dir.iterdir()} - set(RESEARCH_FILES)
        if unexpected:
            raise GenerationError(f"unexpected research entries: {sorted(unexpected)}")
    if audit_raw_dir.exists():
        unexpected = {path.name for path in audit_raw_dir.iterdir()} - set(RAW_FILES)
        if unexpected:
            raise GenerationError(f"unexpected audit raw entries: {sorted(unexpected)}")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise GenerationError(f"refusing to replace symlink: {path}")
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    if temporary.exists():
        raise GenerationError(f"stale temporary output exists: {temporary}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def write_outputs(
    research_dir: Path,
    audit_raw_dir: Path,
    research: Mapping[str, bytes],
    raw: Mapping[str, bytes],
) -> None:
    _validate_output_directories(research_dir, audit_raw_dir)
    _validate_output_safety(research, raw)
    for filename in RESEARCH_TSV_FILES:
        _atomic_write(research_dir / filename, research[filename])
    for filename in RAW_FILES:
        _atomic_write(audit_raw_dir / filename, raw[filename])


def schema_receipt() -> dict[str, Any]:
    return {
        "schemaVersion": GENERATION_SCHEMA_VERSION,
        "inputSchemaVersion": INPUT_SCHEMA_VERSION,
        "componentKeys": list(COMPONENT_KEYS),
        "researchFiles": list(RESEARCH_FILES),
        "tableSources": {
            filename: {"component": TABLE_SOURCES[filename][0], "rowKey": TABLE_SOURCES[filename][1]}
            for filename in RESEARCH_TSV_FILES
        },
        "tableSchemas": {
            filename: {"columns": list(columns), "columnCount": len(columns), "identityColumns": list(TABLE_ID_COLUMNS[filename])}
            for filename, columns in TABLE_SCHEMAS.items()
        },
        "rawFiles": list(RAW_FILES),
        "invariants": INVARIANT_TEXT,
    }


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _fixture_row(filename: str, ordinal: int = 1) -> dict[str, Any]:
    row: dict[str, Any] = {column: "N/A" for column in TABLE_SCHEMAS[filename]}
    for column in TABLE_SCHEMAS[filename]:
        if column.endswith("_count") or column in {
            "k", "rank", "top_k", "object_count", "candidate_object_count", "query_count",
            "document_count", "support", "denominator", "artifact_count", "batch_size",
            "maximum_input_tokens", "minimal_snapshot_bytes", "rrf_constant", "evaluation_k",
        }:
            row[column] = 1
        elif column.endswith("_sha256"):
            row[column] = _digest(f"{filename}:{column}:{ordinal}")
        elif column in {
            "public_safe", "rights_safe", "proxy_only", "ranking_deterministic",
            "full_aspect_cohort", "target_labels_masked", "context_labels_masked",
            "full_normalized_hashes_preserved", "local_snapshot_verified",
        }:
            row[column] = True
        elif column in {
            "contains_source_identity", "contains_structured_label_leakage", "contains_url",
            "contains_markup", "contains_rights_or_provenance", "language_id_model_committed",
            "corpus_text_overwritten", "production_eligible", "trust_remote_code_required",
            "custom_code_reviewed", "pickle_weight_present", "full_public_cohort",
            "pair_matrix_materialized", "full_rankings_saved", "historical_relation",
            "semantic_relation", "probability", "trust_remote_code_executed",
            "model_weights_committed", "full_embedding_matrix_committed",
            "randomness_affects_embedding", "randomness_affects_neighbor_order",
            "model_created_positive_pair_count", "generated_translation_count",
            "language_identity_used_as_semantic_truth", "language_identity_used_as_positive_affinity",
            "source_identity_masked", "boilerplate_removed", "reliable_language_labels_only",
            "correction_tested", "correction_selected", "weights_selected", "prompt_optimized",
            "aspects_fused", "affinity_fused", "aspect_fusion_selected",
            "same_source_diagnostic", "structured_nlp_fusion_selected",
            "structured_nlp_fusion_weights_selected", "production_selected",
            "hybrid_selected", "fusion_weights_selected", "same_source", "same_script_state",
        }:
            row[column] = False
    return row


def _fixture_summary() -> dict[str, Any]:
    table_rows: dict[str, list[dict[str, Any]]] = {}
    field = _fixture_row("03_NLP_TEXT_FIELD_REGISTRY.tsv")
    field.update({"field_id": "NLP-FIELD-SELF", "source_artifact": "generated/self.json", "source_structure": "records[]", "source_field": "title", "primary_role": "OBJECT_TITLE", "governance_decision": "INCLUDE_TITLE_CHANNEL", "reason": "self test", "prohibited_use": "identity inference prohibited", "public_object_coverage": PUBLIC_OBJECT_COUNT, "nonempty_count": PUBLIC_OBJECT_COUNT, "distinct_value_count": 7630})
    table_rows["03_NLP_TEXT_FIELD_REGISTRY.tsv"] = [field]
    language = _fixture_row("05_LANGUAGE_AND_SCRIPT_CENSUS.tsv")
    language.update({"aspect_id": "NLP_TITLE", "field_role": "OBJECT_TITLE", "source_identity": "ALL", "script_state": "Latin", "text_length_bucket": "ALL", "object_count": PUBLIC_OBJECT_COUNT, "document_count": PUBLIC_OBJECT_COUNT, "language_label": "UNDETERMINED", "language_label_state": "ANALYSIS_ONLY", "language_id_model_id": "NOT_SELECTED", "language_id_model_revision": "NOT_SELECTED", "language_id_model_committed": False, "generated_translation_count": 0, "corpus_sha256": CORPUS_SHA256})
    table_rows["05_LANGUAGE_AND_SCRIPT_CENSUS.tsv"] = [language]
    length = _fixture_row("06_TEXT_LENGTH_AND_TOKENIZATION.tsv")
    length.update({"model_or_tokenizer_id": "LEXICAL_WORD", "tokenizer_revision": "trace-tokenizer-self", "aspect_id": "NLP_TITLE", "field_role": "OBJECT_TITLE", "measurement_scope": "FULL_ASPECT_COHORT", "document_count": PUBLIC_OBJECT_COUNT, "governed_token_cap": 256, "effective_token_cap": 256, "truncation_direction": "HEAD", "application_stage": "MODEL_INPUT_ONLY"})
    table_rows["06_TEXT_LENGTH_AND_TOKENIZATION.tsv"] = [length]
    bp = _fixture_row("08_NLP_BOILERPLATE_REGISTRY.tsv")
    bp.update({"rule_id": "NLP-BP-SELF", "source": "SELF SOURCE", "field_role": "SOURCE_IDENTITY", "phrase_or_hash": "sha256:" + _digest("phrase"), "support": 1, "denominator": 1, "decision": "MASK_SOURCE_IDENTITY", "reason": "self test", "removal_scope": "SOURCE_NAME_ONLY", "version": "trace-nlp-boilerplate-v1", "rule_type": "SOURCE_LITERAL", "token_count": 2})
    table_rows["08_NLP_BOILERPLATE_REGISTRY.tsv"] = [bp]
    model_rows = []
    for candidate in ("NLP-D1", "NLP-D2", "NLP-D3", "NLP-D4", "NLP-S1", "NLP-LID1"):
        row = _fixture_row("10_MODEL_ARTIFACT_REGISTER.tsv")
        row.update({"candidate_id": candidate, "channel": "DENSE" if "D" in candidate else "SPARSE", "model_id": f"MODEL-{candidate}", "revision": "a" * 40, "tokenizer_revision": "b" * 40, "license_spdx": "Apache-2.0", "eligibility": "PRODUCTION_ELIGIBLE", "execution_state": "READY_FROM_VERIFIED_LOCAL_SNAPSHOT", "execution_blockers": "", "parameter_count_label": "fixture", "embedding_dimension": 8, "maximum_input_tokens": 512, "pooling": "MEAN", "normalization": "L2", "weight_dtype": "float32", "execution_dtype_cpu": "float32", "quantization_state": "NONE", "language_coverage": "fixture", "loader_family": "fixture", "artifact_count": 1, "minimal_snapshot_bytes": 1, "execution_scope": "SELF_TEST", "run_status": "COMPLETED", "prohibited_use": "public selection"})
        model_rows.append(row)
    table_rows["10_MODEL_ARTIFACT_REGISTER.tsv"] = model_rows
    pairs = []
    positive_ids = (
        ("SURF-AICTRACEV47R0002", "SURF-HISTORICALAICTRACE2026V1R0021"),
        ("SURF-CGS2026R0383", "SURF-LOCTRACE2026ICC0337ACE0D517"),
        ("SURF-CGS2026R0740", "SURF-LOCTRACE2026R02046"),
    )
    for index in range(312):
        row = _fixture_row("11_EVALUATION_PAIR_REGISTRY.tsv", index)
        if index < 3:
            left, right = positive_ids[index]
            pair_class = "KNOWN_REPRESENTATION_POSITIVE"
            control = "SAME_SOURCE_ITEM_DUPLICATE_IMPORT_IDENTITY"
            task = "NLP_TASK_A_KNOWN_REPRESENTATION_RETRIEVAL"
            qualifier = control
        else:
            left, right = f"SURF-SELF-A{index:04d}", f"SURF-SELF-B{index:04d}"
            pair_class = "DIAGNOSTIC_NEGATIVE_CONTROL"
            control = "SAME_TITLE_DIFFERENT_ID"
            task = "NLP_TASK_NEGATIVE_CONTROL"
            qualifier = "NOT_APPLICABLE"
        verification_source = (
            f"https://www.loc.gov/item/{index + 1}"
            if index < 3
            else "frozen artifact"
        )
        row.update({"pair_id": f"NLP-PAIR-SELF-{index:04d}", "public_object_id_a": left, "public_object_id_b": right, "task": task, "pair_class": pair_class, "control_type": control, "verification_source": verification_source, "verification_strength": "MECHANICAL", "verification_artifact_path": "data/prefreeze_candidate_v48.sqlite", "eligibility_artifact_path": "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv", "field_aspects_available": "NLP_TITLE", "language_script": "Latin", "source_identity": "SELF", "source_item_identity": f"SELF:{index}", "representation_qualifier": qualifier, "archive_native_variant_evidence": False, "reason": "self test", "prohibited_interpretation": "not historical relation"})
        pairs.append(row)
    table_rows["11_EVALUATION_PAIR_REGISTRY.tsv"] = pairs
    lexical_rows = []
    lexical_specs = (
        ("NLP-L0", "BM25F", "NLP-L0-BM25F-EQUAL"),
        ("NLP-L1", "CHAR_NGRAM", "NLP-L1-CHAR-3-5"),
        ("NLP-L2", "WORD_NGRAM", "NLP-L2-WORD-1-2"),
        ("NLP-L3", "LEXICAL_HYBRID", "NLP-L3-RRF-L0-L1-K60"),
    )
    ordinal = 0
    for _family_id, family, method_prefix in lexical_specs:
        for aspect_id in REQUIRED_LEXICAL_ASPECT_IDS:
            ordinal += 1
            suffix = aspect_id.removeprefix("NLP_")
            available = EXPECTED_ASPECT_COUNTS[aspect_id]
            row = _fixture_row("12_LEXICAL_BASELINE_RESULTS.tsv", ordinal)
            row.update({
                "model_id": f"{method_prefix}-{suffix}",
                "method_family": family,
                "implementation_version": "self-test",
                "input_variant": "ORIGINAL_APPROVED_TEXT",
                "aspect_id": aspect_id,
                "aspect_purpose": "SELF_TEST_GOVERNED_ASPECT",
                "corpus_sha256": CORPUS_SHA256,
                "corpus_policy_sha256": CORPUS_POLICY_SHA256,
                "field_registry_sha256": FIELD_REGISTRY_SHA256,
                "normalization_version": NORMALIZATION_VERSION,
                "object_count": PUBLIC_OBJECT_COUNT,
                "candidate_object_count": PUBLIC_OBJECT_COUNT,
                "aspect_available_query_count": available,
                "aspect_unavailable_query_count": PUBLIC_OBJECT_COUNT - available,
                "query_count": available,
                "top_k": 50,
                "full_public_cohort": available == PUBLIC_OBJECT_COUNT,
                "full_aspect_cohort": True,
                "index_bytes": 128,
                "index_build_ms": 1.0,
                "exact_query_p50_ms": 0.1,
                "exact_query_p95_ms": 0.2,
                "known_item_positive_pair_count": 3,
                "known_item_recall_at_1": 0.25,
                "known_item_recall_at_5": 0.5,
                "known_item_recall_at_10": 0.5,
                "known_item_recall_at_20": 0.75,
                "known_item_mrr": 0.5,
                "negative_control_pair_count": 309,
                "negative_control_at_10_rate": 0.1,
                "same_source_neighbor_rate_at_20": 0.2,
                "same_language_neighbor_rate_at_20": "N/A",
                "ranking_deterministic": True,
                "status": "PASS",
                "limitation": "self test",
            })
            lexical_rows.append(row)
    table_rows["12_LEXICAL_BASELINE_RESULTS.tsv"] = lexical_rows
    dense = _fixture_row("13_DENSE_MODEL_RESULTS.tsv")
    dense.update({"model_id": "NLP-D1", "model_revision": "a" * 40, "tokenizer_revision": "b" * 40, "license_spdx": "Apache-2.0", "eligibility": "PRODUCTION_ELIGIBLE", "execution_scope": "FULL_CORPUS", "status": "PASS", "input_variant": "APPROVED_ORIGINAL", "aspect_id": "NLP_TITLE", "corpus_sha256": CORPUS_SHA256, "corpus_policy_sha256": CORPUS_POLICY_SHA256, "field_registry_sha256": FIELD_REGISTRY_SHA256, "normalization_version": NORMALIZATION_VERSION, "object_count": PUBLIC_OBJECT_COUNT, "candidate_object_count": PUBLIC_OBJECT_COUNT, "aspect_available_query_count": PUBLIC_OBJECT_COUNT, "aspect_unavailable_query_count": 0, "query_count": PUBLIC_OBJECT_COUNT, "top_k": 50, "full_public_cohort": True, "full_aspect_cohort": True, "embedding_dimension": 8, "maximum_input_tokens": 512, "batch_size": 8, "device": "cpu", "encoding_ms": 10.0, "documents_per_second": 100.0, "index_bytes": 256, "exact_query_p50_ms": 0.1, "exact_query_p95_ms": 0.2, "known_item_recall_at_1": 0.25, "known_item_recall_at_5": 0.5, "known_item_recall_at_10": 0.5, "known_item_recall_at_20": 0.75, "known_item_mrr": 0.5, "same_source_neighbor_rate_at_20": 0.2, "same_language_neighbor_rate_at_20": "N/A", "hubness_gini_at_20": 0.2, "top_1_percent_occurrence_share_at_20": 0.03, "maximum_occurrence_at_20": 30, "mean_sampled_cosine": 0.4, "first_pc_variance_share": 0.1, "peak_ram_bytes": 1024, "peak_vram_bytes": 0, "limitation": "self test"})
    table_rows["13_DENSE_MODEL_RESULTS.tsv"] = [dense]
    cross = _fixture_row("14_CROSS_LANGUAGE_RESULTS.tsv")
    cross.update({"model_id": "NLP-D1", "model_revision": "a" * 40, "input_variant": "APPROVED_ORIGINAL", "aspect_id": "NLP_TITLE", "status": "NOT_RUN", "reason": "NO_MECHANICALLY_VERIFIED_CROSS_LANGUAGE_POSITIVES", "corpus_sha256": CORPUS_SHA256, "evaluation_registry_sha256": EVALUATION_REGISTRY_SHA256, "verified_pair_count": 0, "directional_query_count": 0, "review_row_count": 0, "model_created_positive_pair_count": 0, "generated_translation_count": 0})
    table_rows["14_CROSS_LANGUAGE_RESULTS.tsv"] = [cross]
    metadata_rows = []
    for target in ("medium", "theme", "object_type"):
        for variant in ("ORIGINAL_APPROVED_TEXT", "TARGET_LABEL_MASKED", "ALL_CONTEXT_LABELS_MASKED"):
            row = _fixture_row("15_METADATA_HOLDOUT_RESULTS.tsv")
            row.update({"model_id": "NLP-L0", "method_family": "BM25F", "input_variant": "APPROVED_ORIGINAL", "mask_variant": variant, "target": target, "proxy_only": True, "label_count": 4, "evaluable_query_count": 100, "majority_label_object_share": 0.4, "precision_at_5": 0.5, "precision_at_10": 0.5, "precision_at_20": 0.5, "ndcg_at_5": 0.5, "ndcg_at_10": 0.5, "ndcg_at_20": 0.5, "target_literal_count_before": None if variant == "ORIGINAL_APPROVED_TEXT" else 5, "target_literal_count_after": None if variant == "ORIGINAL_APPROVED_TEXT" else 0, "target_labels_masked": variant != "ORIGINAL_APPROVED_TEXT", "context_labels_masked": variant == "ALL_CONTEXT_LABELS_MASKED", "status": "PASS", "limitation": "proxy only"})
            metadata_rows.append(row)
    table_rows["15_METADATA_HOLDOUT_RESULTS.tsv"] = metadata_rows
    leakage_rows = []
    for dimension in ("SOURCE", "LANGUAGE"):
        row = _fixture_row("16_SOURCE_LANGUAGE_LEAKAGE.tsv")
        row.update({"model_id": "NLP-L0", "method_family": "BM25F", "input_variant": "APPROVED_ORIGINAL", "aspect_id": "NLP_TITLE", "leakage_dimension": dimension, "probe_or_metric": f"SAME_{dimension}_NEIGHBOR_RATE", "k": 20, "query_count": PUBLIC_OBJECT_COUNT, "label_count": 1 if dimension == "SOURCE" else 0, "metric_value": 0.25 if dimension == "SOURCE" else "N/A", "status": "PASS" if dimension == "SOURCE" else "NOT_RUN", "reason": "diagnostic" if dimension == "SOURCE" else "NO_SELECTED_RELIABLE_LANGUAGE_ID_MODEL"})
        leakage_rows.append(row)
    script_only = _fixture_row("16_SOURCE_LANGUAGE_LEAKAGE.tsv", 99)
    script_only.update({"model_id": "NLP-L0", "method_family": "BM25F", "input_variant": "APPROVED_ORIGINAL", "aspect_id": "NLP_TITLE", "leakage_dimension": "LANGUAGE", "probe_or_metric": "SAME_SCRIPT_NEIGHBOR_RATE_NOT_LANGUAGE", "k": 20, "query_count": PUBLIC_OBJECT_COUNT, "label_count": 0, "metric_value": 0.4, "reliable_language_labels_only": False, "status": "PASS_SCRIPT_ONLY", "reason": "SCRIPT_IS_NOT_LANGUAGE"})
    leakage_rows.append(script_only)
    table_rows["16_SOURCE_LANGUAGE_LEAKAGE.tsv"] = leakage_rows
    hub_rows = []
    missing_hubness_diagnostics = ["LANGUAGE", "PRE_NORMALIZATION_NORMS"]
    association_inputs_sha256 = _digest("hubness-association-inputs")
    for k in (10, 20, 50):
        row = _fixture_row("17_HUBNESS_AND_ANISOTROPY.tsv", k)
        row.update({"model_id": "NLP-D1", "model_revision": "a" * 40, "input_variant": "APPROVED_ORIGINAL", "aspect_id": "NLP_TITLE", "diagnostic_type": "HUBNESS", "k": k, "object_count": PUBLIC_OBJECT_COUNT, "query_count": PUBLIC_OBJECT_COUNT, "mean_k_occurrence": k, "variance_k_occurrence": 1.0, "skewness": 0.1, "gini": 0.2, "top_1_percent_occurrence_share": 0.03, "maximum_occurrence": k + 2, "zero_occurrence_object_count": 0, "total_occurrence_count": PUBLIC_OBJECT_COUNT * k, "expected_occurrence_count": PUBLIC_OBJECT_COUNT * k, "overall_diagnostic_status": "NOT_RUN", "missing_required_diagnostics": missing_hubness_diagnostics, "association_inputs_sha256": association_inputs_sha256, "status": "PASS", "limitation": "diagnostic"})
        hub_rows.append(row)
    for dimension in REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS:
        for k in (10, 20, 50):
            row = _fixture_row(
                "17_HUBNESS_AND_ANISOTROPY.tsv",
                100 + REQUIRED_HUBNESS_ASSOCIATION_DIMENSIONS.index(dimension) * 10 + k,
            )
            available = dimension != "LANGUAGE"
            row.update({
                "model_id": "NLP-D1",
                "model_revision": "a" * 40,
                "input_variant": "APPROVED_ORIGINAL",
                "aspect_id": "NLP_TITLE",
                "diagnostic_type": f"HUBNESS_ASSOCIATION_{dimension}",
                "k": k,
                "object_count": PUBLIC_OBJECT_COUNT,
                "query_count": PUBLIC_OBJECT_COUNT,
                "overall_diagnostic_status": "NOT_RUN",
                "missing_required_diagnostics": missing_hubness_diagnostics,
                "association_inputs_sha256": association_inputs_sha256,
                "association_dimension": dimension,
                "association_type": "CATEGORICAL_ETA_SQUARED" if available else "NOT_RUN",
                "association_value": 0.05 if available else "N/A",
                "association_group_count": 4 if available else "N/A",
                "association_eta_squared": 0.05 if available else "N/A",
                "association_pearson_correlation": "N/A",
                "association_observation_sha256": _digest(f"association-{dimension}-{k}") if available else "N/A",
                "status": "PASS" if available else "NOT_RUN",
                "limitation": "diagnostic only" if available else "NO_SELECTED_RELIABLE_LANGUAGE_ID_MODEL",
            })
            hub_rows.append(row)
    anisotropy = _fixture_row("17_HUBNESS_AND_ANISOTROPY.tsv", 99)
    anisotropy.update({"model_id": "NLP-D1", "model_revision": "a" * 40, "input_variant": "APPROVED_ORIGINAL", "aspect_id": "NLP_TITLE", "diagnostic_type": "ANISOTROPY", "k": "N/A", "object_count": PUBLIC_OBJECT_COUNT, "query_count": PUBLIC_OBJECT_COUNT, "embedding_dimension": 8, "mean_sampled_cosine": 0.4, "cosine_variance": 0.02, "pair_observation_count": 100, "first_pc_variance_share": 0.1, "norm_p50": 1.0, "norm_p95": 1.0, "pre_normalization_norm_p50": "N/A", "pre_normalization_norm_p95": "N/A", "nearest_neighbor_cosine_distance_p50": 0.2, "nearest_neighbor_cosine_distance_p95": 0.4, "exact_mean_off_diagonal_cosine": 0.3, "overall_diagnostic_status": "NOT_RUN", "missing_required_diagnostics": missing_hubness_diagnostics, "association_inputs_sha256": association_inputs_sha256, "status": "NOT_RUN", "limitation": "pre-normalization norms unavailable"})
    hub_rows.append(anisotropy)
    table_rows["17_HUBNESS_AND_ANISOTROPY.tsv"] = hub_rows
    robust_rows = []
    executed_ablations = {
        "REGISTERED_BOILERPLATE_REMOVED",
        "SOURCE_IDENTITY_MASKED",
        "MARKUP_CLEANED",
        "UNICODE_CANONICAL_VARIANT",
    }
    declared_ablation_set = set(DECLARED_ROBUSTNESS_ABLATION_IDS)
    title_lexical = [row for row in lexical_rows if row["aspect_id"] == "NLP_TITLE"]
    robustness_references = [
        (
            next(family_id for family_id, family, _prefix in lexical_specs if family == row["method_family"]),
            row["model_id"],
            "ORIGINAL_APPROVED",
            row["index_sha256"],
        )
        for row in title_lexical
    ]
    robustness_references.append(
        (
            "NLP-D1",
            "NLP-D1-TITLE-APPROVED_ORIGINAL",
            "APPROVED_ORIGINAL",
            dense["index_sha256"],
        )
    )
    ordinal = 0
    for model_id, reference_method_id, reference_input_variant, reference_index in robustness_references:
        for ablation in DECLARED_ROBUSTNESS_ABLATION_IDS:
            executed = ablation in executed_ablations
            k_values = REQUIRED_DIAGNOSTIC_K if executed else (0,)
            for k in k_values:
                ordinal += 1
                row = _fixture_row("18_ROBUSTNESS_AND_ABLATION.tsv", ordinal)
                row.update({"model_id": model_id, "reference_method_id": reference_method_id, "variant_method_id": f"{model_id}-{ablation}" if executed else "N/A", "ablation_id": ablation, "ablation_family": "TEXT_ROBUSTNESS", "input_variant": ablation if executed else "NOT_RUN", "aspect_id": "NLP_TITLE" if executed else "N/A", "k": k, "query_count": PUBLIC_OBJECT_COUNT if executed else 0, "mean_top_k_overlap": 0.8 if executed else "N/A", "median_top_k_overlap": 0.8 if executed else "N/A", "p05_top_k_overlap": 0.6 if executed else "N/A", "mean_rank_correlation": 0.7 if executed else "N/A", "median_rank_correlation": 0.7 if executed else "N/A", "p05_rank_correlation": 0.5 if executed else "N/A", "same_source_rate_change": -0.01 if executed else "N/A", "hubness_gini_change": 0.01 if executed else "N/A", "robustness_suite_status": "STOPPED_RECOVERABLE_CHECKPOINT", "reference_corpus_sha256": CORPUS_SHA256, "reference_input_variant": reference_input_variant, "reference_aspect_id": "NLP_TITLE", "reference_index_sha256": reference_index, "reference_ranking_ids_sha256": _digest(f"robust-ranking-{model_id}-{ablation}-{k}"), "declared_ablation_count": len(DECLARED_ROBUSTNESS_ABLATION_IDS), "executed_ablation_ids": [ablation] if executed else [], "not_run_ablation_ids": sorted(declared_ablation_set - {ablation}) if executed else sorted(declared_ablation_set), "suite_sha256": _digest(f"robust-suite-{model_id}-{ablation}-{k}"), "status": "PASS" if executed else "NOT_RUN", "limitation": "diagnostic" if executed else "declared but unavailable at stopped checkpoint"})
                robust_rows.append(row)
    table_rows["18_ROBUSTNESS_AND_ABLATION.tsv"] = robust_rows
    aspect = _fixture_row("19_ASPECT_DISAGREEMENT.tsv")
    aspect.update({"model_id": "NLP-L0", "corpus_sha256": CORPUS_SHA256, "aspect_a": "NLP_TITLE", "aspect_b": "NLP_SUBJECT", "k": 20, "joint_query_count": 7838, "status": "NOT_RUN", "limitation": "overlap computed but reliable-language diagnostic unavailable"})
    table_rows["19_ASPECT_DISAGREEMENT.tsv"] = [aspect]
    structured_rows = []
    for model in ("M2", "M5", "M7"):
        row = _fixture_row("20_STRUCTURED_NLP_DISAGREEMENT.tsv")
        row.update({"row_type": "SUMMARY", "structured_model_id": model, "structured_variant_id": f"{model}-FIXED", "nlp_method_id": "NLP-L0", "anchor_public_object_id": "N/A", "candidate_public_object_id": "N/A", "classification": "AGGREGATE", "anchor_count": 24, "candidate_index_sha256": ROUND6_CANDIDATE_INDEX_SHA256, "status": "PARTIAL", "limitation": "channels remain separate; reliable-language diagnostic unavailable"})
        structured_rows.append(row)
    table_rows["20_STRUCTURED_NLP_DISAGREEMENT.tsv"] = structured_rows
    hybrid = _fixture_row("21_HYBRID_EXPERIMENTS.tsv")
    hybrid.update({"hybrid_id": "RRF-NLP-L0-NLP-D1-K60", "left_method_id": "NLP-L0", "right_method_id": "NLP-D1", "rrf_constant": 60, "evaluation_k": 10, "eligible_query_count": 6, "known_item_recall": 0.5, "status": "PASS", "limitation": "analysis only"})
    table_rows["21_HYBRID_EXPERIMENTS.tsv"] = [hybrid]
    review_rows = []
    for index in range(24):
        review = _fixture_row("22_NLP_REVIEW_PACKET.tsv", index)
        review.update({"packet_id": "NLP-REVIEW-ROUND1", "anchor_public_object_id": f"SURF-SELF-ANCHOR-{index:04d}", "anchor_title": f"Public self-test title {index}", "candidate_public_object_id": f"SURF-SELF-CANDIDATE-{index:04d}", "candidate_title": f"Public candidate title {index}", "blind_model_code": "MODEL-A", "method_role": "LEXICAL", "rank": 1, "text_aspect": "NLP_TITLE", "retrieval_reason": "BOUNDED_TOP_K", "expert_judgment": "PENDING_LATER_REVIEW"})
        review_rows.append(review)
    table_rows["22_NLP_REVIEW_PACKET.tsv"] = review_rows

    components: dict[str, Any] = {
        "source": {"sourceCommit": SOURCE_COMMIT, "round6CandidateIndexSha256": ROUND6_CANDIDATE_INDEX_SHA256, "contextProjectionSha256": CONTEXT_PROJECTION_SHA256, "spacetimeProjectionSha256": SPACETIME_PROJECTION_SHA256, "frozenInputs": {"generated/self.json": _digest("frozen")}, "corpusIdentityReceipt": {"documentReceiptSha256": DOCUMENT_RECEIPT_SHA256, "lexicalCorpusSha256": CORPUS_SHA256, "tokenCountReceiptSha256": TOKEN_COUNT_RECEIPT_SHA256, "tokenCountMethod": TOKEN_COUNT_METHOD, "canonicalPublicIdsSha256": _digest("public-ids"), "documentAndLexicalCorpusHashesAreDistinctContracts": True}},
        "governance": {"corpusPolicyVersion": CORPUS_POLICY_VERSION, "corpusPolicySha256": CORPUS_POLICY_SHA256, "fieldRegistryVersion": FIELD_REGISTRY_VERSION, "fieldRegistrySha256": FIELD_REGISTRY_SHA256, "normalizationVersion": NORMALIZATION_VERSION, "corpusSha256": CORPUS_SHA256, "documentReceiptSha256": DOCUMENT_RECEIPT_SHA256, "tokenCountReceiptSha256": TOKEN_COUNT_RECEIPT_SHA256, "tokenCountMethod": TOKEN_COUNT_METHOD, "modelInputTokenCaps": MODEL_INPUT_TOKEN_CAPS, "originalSourceTextOverwritten": False, "machineTranslationUsed": False, "generatedSummaryUsed": False, "sourceNarrativeMergedWithObjectSemantic": False, "objectSemanticCompositeSourceRoles": ["OBJECT_TITLE"], "unclassifiedTextFieldCount": 0, "textSourceFieldCount": 1, "textSourceFieldClassifiedCount": 1, "fieldRegistryRows": table_rows["03_NLP_TEXT_FIELD_REGISTRY.tsv"], "languageScriptRows": table_rows["05_LANGUAGE_AND_SCRIPT_CENSUS.tsv"], "textLengthRows": table_rows["06_TEXT_LENGTH_AND_TOKENIZATION.tsv"], "boilerplateRows": table_rows["08_NLP_BOILERPLATE_REGISTRY.tsv"]},
        "boundary": {"canonicalObjectCount": CANONICAL_OBJECT_COUNT, "publicObjectCount": PUBLIC_OBJECT_COUNT, "heldObjectCount": HELD_OBJECT_COUNT, "overlapCount": 0, "unclassifiedCount": 0, "nlpHeldObjectsIncluded": 0, "publicObjectsAudited": PUBLIC_OBJECT_COUNT, "publicObjectsWithAnyApprovedText": PUBLIC_OBJECT_COUNT, "aspectObjectCounts": EXPECTED_ASPECT_COUNTS},
        "evaluationRegistry": {"registryVersion": EVALUATION_REGISTRY_VERSION, "registrySha256": EVALUATION_REGISTRY_SHA256, "pairCount": 312, "knownRepresentationPositivePairCount": 3, "negativeControlPairCount": 309, "verifiedCrossLanguagePositivePairCount": 0, "taskBPositivePairCount": 0, "modelCreatedPositivePairCount": 0, "fullSameTitleStressCensus": {"schemaVersion": "trace-nlp-full-same-title-stress-census/v1", "duplicateTitleGroupCount": 155, "duplicateTitleObjectCount": 520, "allUnorderedPairCount": 4346, "excludedKnownIdentityPairCount": 2, "stressPairCount": 4344, "pairEndpointsSha256": _digest("same-title-stress"), "pairRowsSerialized": False, "historicalNonrelation": False}, "sourceTitleDifferenceCensus": {"schemaVersion": "trace-nlp-source-title-difference-census/v1", "sourceTitleObservedObjectCount": 1, "sourceTitleUnavailableObjectCount": 7994, "differenceCount": 23, "differenceTypeCounts": {"LOC_FILE_SUFFIX_OR_FILENAME_TITLE_REWRITE": 7, "V_AND_A_MARKUP_OR_ADJACENT_PUNCTUATION_NORMALIZATION": 16}, "observationHashesSha256": _digest("title-differences"), "archiveNativeLanguageVariantCount": 0, "taskBPositivePairCount": 0, "rawTitlesSerialized": False}, "rows": table_rows["11_EVALUATION_PAIR_REGISTRY.tsv"]},
        "models": {"registrySha256": MODEL_REGISTRY_SHA256, "artifactRows": table_rows["10_MODEL_ARTIFACT_REGISTER.tsv"]},
        "lexical": {"resultRows": table_rows["12_LEXICAL_BASELINE_RESULTS.tsv"]},
        "dense": {"resultRows": table_rows["13_DENSE_MODEL_RESULTS.tsv"], "crossLanguageRows": table_rows["14_CROSS_LANGUAGE_RESULTS.tsv"]},
        "metadata": {"holdoutRows": table_rows["15_METADATA_HOLDOUT_RESULTS.tsv"]},
        "leakage": {"sourceLanguageRows": table_rows["16_SOURCE_LANGUAGE_LEAKAGE.tsv"], "sourceLeakageBlockerCount": 0, "languageLeakageBlockerCount": 0},
        "hubness": {"rows": table_rows["17_HUBNESS_AND_ANISOTROPY.tsv"]},
        "robustness": {"rows": table_rows["18_ROBUSTNESS_AND_ABLATION.tsv"]},
        "aspects": {"rows": table_rows["19_ASPECT_DISAGREEMENT.tsv"], "aspectFusionSelected": False},
        "structured": {"rows": table_rows["20_STRUCTURED_NLP_DISAGREEMENT.tsv"], "structuredNlpFusionSelected": False, "structuredNlpFusionWeightsSelected": False},
        "hybrid": {"rows": table_rows["21_HYBRID_EXPERIMENTS.tsv"], "hybridSelected": False, "fusionWeightsSelected": False},
        "review": {"rows": table_rows["22_NLP_REVIEW_PACKET.tsv"], "anchorCount": 24, "packetReady": False, "domainExpertReviewCompleted": False},
        "runs": {"rows": [{"runId": "NLP-SELF-RUN", "sourceCommit": SOURCE_COMMIT, "corpusPolicySha256": CORPUS_POLICY_SHA256, "fieldRegistrySha256": FIELD_REGISTRY_SHA256, "encodedDocumentReceiptSha256": DOCUMENT_RECEIPT_SHA256, "rankingCorpusSha256": CORPUS_SHA256, "tokenCountReceiptSha256": TOKEN_COUNT_RECEIPT_SHA256, "tokenCountMethod": TOKEN_COUNT_METHOD, "corpusIdentityContractsConflated": False, "randomnessAffectsCorpus": False, "randomnessAffectsEmbedding": False, "randomnessAffectsNeighborOrder": False, "randomnessAffectsScore": False, "modelWeightsCommitted": False, "fullEmbeddingMatrixCommitted": False, "fullRankingsCommitted": False}]},
        "performance": {"lexicalIndexBuildMs": 1, "denseCorpusEncodingMs": 1, "denseDocumentsPerSecond": 1, "denseIndexBytes": 1, "denseExactQueryP50Ms": 1, "denseExactQueryP95Ms": 1, "nlpPeakRamBytes": 1, "nlpPeakVramBytes": 0},
        "security": {"modelWeightFilesCommitted": 0, "internalUuidExposureCount": 0, "heldIdentifierExposureCount": 0, "databaseFilesChanged": 0, "searchFilesChanged": 0, "historicalRelationCount": 0, "probabilityCount": 0, "canonicalReleaseChanged": False, "contextSemanticsChanged": False, "contextGovernanceChanged": False, "spacetimeGovernanceChanged": False, "cgCur4Changed": False, "m2SpecificationChanged": False, "m5SpecificationChanged": False, "m7SpecificationChanged": False, "publicExplorationApiAdded": False, "publicExplorationRouteAdded": False, "vectorDatabaseAdded": False, "explorationRendererImplemented": False, "unreviewedRemoteCodeExecuted": False, "fullEmbeddingMatrixCommitted": False, "fullRankingsCommitted": False, "fullPairMatrixCommitted": False, "randomnessAffectsCorpus": False, "randomnessAffectsEmbedding": False, "randomnessAffectsNeighborOrder": False, "randomnessAffectsScore": False},
        "decision": {"phaseStatus": "STOPPED_RECOVERABLE_CHECKPOINT", "nlpModelDecision": "NLP_CORPUS_AUDIT_ONLY", "denseModelShortlistCount": 0, "denseModelShortlistIds": [], "baselineFamiliesShortlisted": False, "provisionalInternalNlpChannelSelected": False, "publicNlpModelSelected": False, "publicNlpWeightsSelected": False, "publicExplorationModelSelected": False, "structuredNlpFusionSelected": False, "structuredNlpFusionWeightsSelected": False, "hubnessCorrectionSelected": False, "domainExpertReviewCompleted": False, "sourceLeakageAndHubnessConsidered": True},
        "invariants": {identifier: {"status": "PASS", "evidenceRefs": ["self-test"]} for identifier in INVARIANT_TEXT},
    }
    for component_name, component in components.items():
        if not isinstance(component, Mapping):
            continue
        row_receipts = {}
        for _filename, (owner, row_key) in TABLE_SOURCES.items():
            if owner == component_name and row_key in component:
                row_receipts[row_key] = _row_receipt(component[row_key])
        if row_receipts:
            component["rowReceipts"] = row_receipts
    summary = {"schemaVersion": INPUT_SCHEMA_VERSION, **components}
    summary["analysisSummarySha256"] = sha256_json(summary)
    return summary


def _reseal_fixture_summary(summary: dict[str, Any]) -> dict[str, Any]:
    for component_name, component in summary.items():
        if component_name in {"schemaVersion", "analysisSummarySha256"} or not isinstance(
            component, Mapping
        ):
            continue
        receipts = component.get("rowReceipts")
        if not isinstance(receipts, Mapping):
            continue
        component["rowReceipts"] = {
            row_key: _row_receipt(component[row_key]) for row_key in receipts
        }
    summary.pop("analysisSummarySha256", None)
    summary["analysisSummarySha256"] = sha256_json(summary)
    return summary


def _assert_fixture_rejected(summary: dict[str, Any], label: str) -> None:
    try:
        derive_tables(_reseal_fixture_summary(summary))
    except GenerationError:
        return
    raise AssertionError(f"adversarial fixture was accepted: {label}")


def self_test() -> dict[str, Any]:
    summary = _fixture_summary()
    with tempfile.TemporaryDirectory(prefix="trace-nlp-round1-generation-") as directory:
        root = Path(directory)
        research_dir = root / "research"
        raw_dir = root / "audit/raw"
        research_dir.mkdir(parents=True)
        for filename in RESEARCH_FILES:
            if filename.endswith(".md"):
                (research_dir / filename).write_text(f"# {filename}\n", encoding="utf-8", newline="\n")
        analysis_path = root / "analysis.json"
        analysis_path.write_bytes(canonical_json_bytes(summary, pretty=True))
        first = run_twice(analysis_path, research_dir_for_receipts=research_dir)
        second = run_twice(analysis_path, research_dir_for_receipts=research_dir)
        if first != second:
            raise AssertionError("generator replay was not deterministic")
        write_outputs(research_dir, raw_dir, first[0], first[1])
        if {path.name for path in research_dir.iterdir() if path.suffix == ".tsv"} != set(RESEARCH_TSV_FILES):
            raise AssertionError("self-test did not write the exact TSV inventory")
        if {path.name for path in raw_dir.iterdir()} != set(RAW_FILES):
            raise AssertionError("self-test did not write the exact raw inventory")
        unsafe_url_research = dict(first[0])
        unsafe_url_research["11_EVALUATION_PAIR_REGISTRY.tsv"] = unsafe_url_research[
            "11_EVALUATION_PAIR_REGISTRY.tsv"
        ].replace(
            b"https://www.loc.gov/item/1",
            b"https://example.com/item/1",
            1,
        )
        try:
            _validate_output_safety(unsafe_url_research, first[1])
        except GenerationError:
            pass
        else:
            raise AssertionError("ungoverned evaluation source URL was accepted")
        corrupt = deepcopy(summary)
        corrupt["boundary"]["publicObjectCount"] = PUBLIC_OBJECT_COUNT - 1
        corrupt.pop("analysisSummarySha256", None)
        corrupt["analysisSummarySha256"] = sha256_json(corrupt)
        corrupt_path = root / "corrupt.json"
        corrupt_path.write_bytes(canonical_json_bytes(corrupt))
        rejected = False
        try:
            run_twice(corrupt_path)
        except GenerationError:
            rejected = True
        if not rejected:
            raise AssertionError("corrupt public boundary was accepted")
        unbounded = deepcopy(summary)
        unbounded["lexical"]["rankings"] = {
            "SURF-SELF-ANCHOR": ["SURF-SELF-CANDIDATE"]
        }
        unbounded.pop("analysisSummarySha256", None)
        unbounded["analysisSummarySha256"] = sha256_json(unbounded)
        unbounded_path = root / "unbounded.json"
        unbounded_path.write_bytes(canonical_json_bytes(unbounded))
        unbounded_rejected = False
        try:
            run_twice(unbounded_path)
        except GenerationError:
            unbounded_rejected = True
        if not unbounded_rejected:
            raise AssertionError("full ranking payload was accepted")
        conflated = deepcopy(summary)
        conflated["source"]["corpusIdentityReceipt"]["documentReceiptSha256"] = CORPUS_SHA256
        conflated.pop("analysisSummarySha256", None)
        conflated["analysisSummarySha256"] = sha256_json(conflated)
        conflated_path = root / "conflated.json"
        conflated_path.write_bytes(canonical_json_bytes(conflated))
        try:
            run_twice(conflated_path)
        except GenerationError:
            pass
        else:
            raise AssertionError("conflated corpus identity receipts were accepted")
        incomplete = deepcopy(summary)
        completed_robustness = next(
            row
            for row in incomplete["robustness"]["rows"]
            if str(row["status"]).upper() == "PASS"
        )
        completed_robustness["mean_top_k_overlap"] = None
        incomplete["robustness"]["rowReceipts"]["rows"] = _row_receipt(
            incomplete["robustness"]["rows"]
        )
        incomplete.pop("analysisSummarySha256", None)
        incomplete["analysisSummarySha256"] = sha256_json(incomplete)
        incomplete_path = root / "incomplete.json"
        incomplete_path.write_bytes(canonical_json_bytes(incomplete))
        try:
            run_twice(incomplete_path)
        except GenerationError:
            pass
        else:
            raise AssertionError("PASS robustness row with N/A diagnostics was accepted")
        adversaries: list[tuple[str, dict[str, Any]]] = []

        hubness_overall = deepcopy(summary)
        for row in hubness_overall["hubness"]["rows"]:
            row["overall_diagnostic_status"] = "PASS"
            row["missing_required_diagnostics"] = []
        adversaries.append(("HUBNESS_OVERALL_NOT_DERIVED", hubness_overall))

        anisotropy_partial = deepcopy(summary)
        next(
            row for row in anisotropy_partial["hubness"]["rows"]
            if row["diagnostic_type"] == "ANISOTROPY"
        )["status"] = "PARTIAL"
        adversaries.append(("ANISOTROPY_PARTIAL_WITHOUT_PRE_NORMS", anisotropy_partial))

        anisotropy_not_run_with_evidence = deepcopy(summary)
        anisotropy_row = next(
            row for row in anisotropy_not_run_with_evidence["hubness"]["rows"]
            if row["diagnostic_type"] == "ANISOTROPY"
        )
        anisotropy_row["pre_normalization_norm_p50"] = 1.0
        anisotropy_row["pre_normalization_norm_p95"] = 1.1
        adversaries.append(
            ("ANISOTROPY_NOT_RUN_WITH_PRE_NORM_EVIDENCE", anisotropy_not_run_with_evidence)
        )

        hubness_not_run = deepcopy(summary)
        next(
            row for row in hubness_not_run["hubness"]["rows"]
            if row["diagnostic_type"] == "HUBNESS"
        )["status"] = "NOT_RUN"
        adversaries.append(("POPULATED_HUBNESS_NOT_RUN", hubness_not_run))

        fake_robustness = deepcopy(summary)
        for row in fake_robustness["robustness"]["rows"]:
            if row["model_id"] == "NLP-D1":
                row["model_id"] = "FAKE-MODEL"
                row["reference_method_id"] = "FAKE-REFERENCE"
        adversaries.append(("FORGED_ROBUSTNESS_REFERENCE", fake_robustness))

        missing_robustness_k = deepcopy(summary)
        missing_robustness_k["robustness"]["rows"] = [
            row for row in missing_robustness_k["robustness"]["rows"]
            if not (
                row["model_id"] == "NLP-D1"
                and row["ablation_id"] == "SOURCE_IDENTITY_MASKED"
                and row["k"] in {10, 50}
            )
        ]
        adversaries.append(("ROBUSTNESS_K_COVERAGE_INCOMPLETE", missing_robustness_k))

        title_only_lexical = deepcopy(summary)
        title_only_lexical["lexical"]["resultRows"] = [
            row for row in title_only_lexical["lexical"]["resultRows"]
            if row["aspect_id"] != "NLP_SUBJECT"
        ]
        adversaries.append(("LEXICAL_SUBJECT_COVERAGE_OMITTED", title_only_lexical))

        forged_subject_public_cohort = deepcopy(summary)
        next(
            row for row in forged_subject_public_cohort["lexical"]["resultRows"]
            if row["aspect_id"] == "NLP_SUBJECT"
        )["full_public_cohort"] = True
        adversaries.append(("LEXICAL_SUBJECT_PUBLIC_COHORT_FORGED", forged_subject_public_cohort))

        forged_anchor_count = deepcopy(summary)
        forged_anchor_count["review"]["anchorCount"] = 25
        adversaries.append(("REVIEW_ANCHOR_COUNT_FORGED", forged_anchor_count))

        undersized_review = deepcopy(summary)
        undersized_review["review"]["rows"] = undersized_review["review"]["rows"][:1]
        undersized_review["review"]["anchorCount"] = 1
        adversaries.append(("REVIEW_ANCHOR_TARGET_UNDERSIZED", undersized_review))

        lexical_na = deepcopy(summary)
        lexical_na["lexical"]["resultRows"][0]["known_item_recall_at_10"] = "N/A"
        adversaries.append(("LEXICAL_PASS_WITH_NA_METRIC", lexical_na))

        lexical_na_hash = deepcopy(summary)
        lexical_na_hash["lexical"]["resultRows"][0]["ranking_ids_sha256"] = "N/A"
        adversaries.append(("LEXICAL_PASS_WITH_NA_HASH", lexical_na_hash))

        dense_na = deepcopy(summary)
        dense_na["dense"]["resultRows"][0]["embedding_dimension"] = "N/A"
        adversaries.append(("DENSE_PASS_WITH_NA_DIMENSION", dense_na))

        dense_na_hash = deepcopy(summary)
        dense_na_hash["dense"]["resultRows"][0]["ranking_ids_sha256"] = "N/A"
        adversaries.append(("DENSE_PASS_WITH_NA_HASH", dense_na_hash))

        metadata_na = deepcopy(summary)
        metadata_na["metadata"]["holdoutRows"][0]["precision_at_10"] = "N/A"
        adversaries.append(("METADATA_PASS_WITH_NA_METRIC", metadata_na))

        metadata_bad_count = deepcopy(summary)
        metadata_bad_count["metadata"]["holdoutRows"][0]["label_count"] = 0
        adversaries.append(("METADATA_PASS_WITH_ZERO_LABEL_COUNT", metadata_bad_count))

        metadata_unmasked_counts = deepcopy(summary)
        unmasked_metadata_row = next(
            row for row in metadata_unmasked_counts["metadata"]["holdoutRows"]
            if row["mask_variant"] == "ORIGINAL_APPROVED_TEXT"
        )
        unmasked_metadata_row["target_literal_count_before"] = 0
        unmasked_metadata_row["target_literal_count_after"] = 0
        adversaries.append(("METADATA_UNMASKED_LITERAL_COUNTS_FORGED", metadata_unmasked_counts))

        hybrid_na = deepcopy(summary)
        hybrid_na["hybrid"]["rows"][0]["known_item_recall"] = "N/A"
        adversaries.append(("HYBRID_PASS_WITH_NA_METRIC", hybrid_na))

        hybrid_bad_count = deepcopy(summary)
        hybrid_bad_count["hybrid"]["rows"][0]["eligible_query_count"] = 0
        adversaries.append(("HYBRID_PASS_WITH_ZERO_QUERY_COUNT", hybrid_bad_count))

        invalid_status_mutations = (
            ("DENSE", "dense", "resultRows"),
            ("METADATA", "metadata", "holdoutRows"),
            ("LEAKAGE", "leakage", "sourceLanguageRows"),
            ("HYBRID", "hybrid", "rows"),
            ("ASPECT", "aspects", "rows"),
            ("STRUCTURED", "structured", "rows"),
        )
        for label, component, row_key in invalid_status_mutations:
            invalid_status = deepcopy(summary)
            invalid_status[component][row_key][0]["status"] = "GIBBERISH"
            adversaries.append((f"UNDECLARED_{label}_STATUS", invalid_status))

        task_b_not_run_evidence = deepcopy(summary)
        task_b_row = task_b_not_run_evidence["dense"]["crossLanguageRows"][0]
        task_b_row["recall_at_10"] = 0.9
        task_b_row["mean_reciprocal_rank"] = 0.8
        task_b_row["review_row_count"] = 1
        adversaries.append(("TASK_B_NOT_RUN_WITH_RESULT_EVIDENCE", task_b_not_run_evidence))

        language_not_run_evidence = deepcopy(summary)
        language_row = next(
            row for row in language_not_run_evidence["leakage"]["sourceLanguageRows"]
            if row["leakage_dimension"] == "LANGUAGE" and row["status"] == "NOT_RUN"
        )
        language_row["metric_value"] = 0.8
        language_row["macro_f1"] = 0.7
        adversaries.append(("LANGUAGE_NOT_RUN_WITH_METRICS", language_not_run_evidence))

        aspect_not_run_evidence = deepcopy(summary)
        aspect_not_run_evidence["aspects"]["rows"][0]["language_neighbor_rate_a"] = 0.8
        aspect_not_run_evidence["aspects"]["rows"][0]["language_neighbor_rate_b"] = 0.7
        adversaries.append(("ASPECT_NOT_RUN_WITH_LANGUAGE_METRICS", aspect_not_run_evidence))

        metadata_not_run_evidence = deepcopy(summary)
        metadata_row = metadata_not_run_evidence["metadata"]["holdoutRows"][0]
        metadata_row["status"] = "NOT_RUN"
        metadata_row["limitation"] = "self-test non-execution"
        metadata_row["precision_at_10"] = 0.9
        adversaries.append(("METADATA_NOT_RUN_WITH_RESULT_EVIDENCE", metadata_not_run_evidence))

        hybrid_not_run_evidence = deepcopy(summary)
        hybrid_row = hybrid_not_run_evidence["hybrid"]["rows"][0]
        hybrid_row["status"] = "NOT_RUN"
        hybrid_row["eligible_query_count"] = 0
        hybrid_row["known_item_recall"] = 0.9
        adversaries.append(("HYBRID_NOT_RUN_WITH_RESULT_EVIDENCE", hybrid_not_run_evidence))

        robustness_not_run_evidence = deepcopy(summary)
        robustness_row = next(
            row for row in robustness_not_run_evidence["robustness"]["rows"]
            if row["status"] == "NOT_RUN"
        )
        robustness_row["mean_top_k_overlap"] = 0.9
        robustness_row["mean_rank_correlation"] = 0.8
        adversaries.append(("ROBUSTNESS_NOT_RUN_WITH_RESULT_EVIDENCE", robustness_not_run_evidence))

        chunked_embedding = deepcopy(summary)
        chunked_embedding["dense"]["data"] = [
            {"values": [0.1] * 64} for _ in range(6)
        ]
        adversaries.append(("CHUNKED_EMBEDDING_ALIAS", chunked_embedding))

        for label, adversary in adversaries:
            _assert_fixture_rejected(adversary, label)
    return {
        "schemaVersion": "trace-nlp-round1-generation-self-test/v1",
        "status": "PASS",
        "researchTsvCount": len(RESEARCH_TSV_FILES),
        "auditRawCount": len(RAW_FILES),
        "invariantCount": len(INVARIANT_TEXT),
        "deterministicReplay": True,
        "corruptionRejected": True,
        "unboundedPayloadRejected": True,
        "corpusIdentityConflationRejected": True,
        "incompleteCompletedDiagnosticRejected": True,
        "adversaryCount": 37,
        "adversariesRejected": [
            "PUBLIC_BOUNDARY_CORRUPTION",
            "UNBOUNDED_RANKING_PAYLOAD",
            "CORPUS_IDENTITY_CONFLATION",
            "ROBUSTNESS_PASS_WITH_NA_DIAGNOSTIC",
            "UNGOVERNED_EVALUATION_SOURCE_URL",
            *[label for label, _adversary in adversaries],
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-summary", type=Path)
    parser.add_argument("--research-dir", type=Path, default=DEFAULT_RESEARCH_DIR)
    parser.add_argument("--audit-raw-dir", type=Path, default=DEFAULT_AUDIT_RAW_DIR)
    parser.add_argument("--bind-research-receipts", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
        return 0
    if args.print_schema:
        print(json.dumps(schema_receipt(), ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args.analysis_summary is None:
        parser.error("--analysis-summary is required unless --self-test/--print-schema is used")
    research_dir = args.research_dir.resolve()
    audit_raw_dir = args.audit_raw_dir.resolve()
    outputs = run_twice(
        args.analysis_summary.resolve(),
        research_dir_for_receipts=research_dir if args.bind_research_receipts else None,
    )
    if not args.dry_run:
        write_outputs(research_dir, audit_raw_dir, outputs[0], outputs[1])
    print(json.dumps({
        "status": "PASS",
        "dryRun": args.dry_run,
        "researchReceiptsComplete": outputs[2]["researchReceiptsComplete"],
        "analysisSummarySha256": outputs[2]["analysisSummarySha256"],
        "researchTsvCount": len(outputs[0]),
        "auditRawCount": len(outputs[1]),
        "rowCounts": {name: value["rowCount"] for name, value in outputs[2]["tableReceipts"].items()},
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
