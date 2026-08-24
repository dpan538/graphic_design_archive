#!/usr/bin/env python3
"""Pinned, fail-closed model registry for TRACE v49 NLP research.

This module is metadata only.  It never contacts a model hub, installs a
package, or loads model code.  Executable callers must resolve an exact local
snapshot and verify every declared artifact before importing Transformers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SCHEMA_VERSION = "trace-nlp-model-registry/v1"
IMPLEMENTATION_VERSION = "trace-nlp-model-registry-2026-08-24"
SOURCE_SHA = "580587a74f400d8a04d995937f4efb31e6621dd8"

PRODUCTION_ELIGIBLE = "PRODUCTION_ELIGIBLE"
RESEARCH_ONLY = "RESEARCH_ONLY"
REJECT = "REJECT"

EXECUTION_READY = "READY_FROM_VERIFIED_LOCAL_SNAPSHOT"
EXECUTION_CONDITIONAL = "CONDITIONAL_REVIEW_REQUIRED"
EXECUTION_BLOCKED = "BLOCKED"

DENSE_CANDIDATE_IDS = ("NLP-D1", "NLP-D2", "NLP-D3", "NLP-D4")
SPARSE_CANDIDATE_IDS = ("NLP-S1",)
LANGUAGE_ID_CANDIDATE_IDS = ("NLP-LID1",)
FULL_CORPUS_EXECUTION_SHORTLIST = ("NLP-D1", "NLP-D3")

# Exact versions imported and confirmed in the executed research environment,
# `/private/tmp/trace-nlp-v1-venv` (Python 3.13.5, system-site packages).
RUNTIME_PINS: dict[str, str] = {
    "python": "3.13.5",
    "torch": "2.12.0",
    "transformers": "5.12.0",
    "tokenizers": "0.22.2",
    "numpy": "2.4.4",
    "scipy": "1.17.1",
    "huggingface-hub": "1.19.0",
    "safetensors": "0.8.0",
    "accelerate": "1.14.0",
    "psutil": "7.0.0",
}

# A future clean-room rebuild may prefer Python 3.11.15.  This profile is a
# recommendation only and must never be reported as the runtime used in Round 1.
FUTURE_RECOMMENDED_RUNTIME_PINS: dict[str, str] = {
    **RUNTIME_PINS,
    "python": "3.11.15",
}

OFFICIAL_ARCHIVE_RETRIEVAL_TASK = (
    "Given a web search query, retrieve relevant passages that answer the query"
)

_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = _SHA1


class ModelRegistryError(ValueError):
    """Raised when registry metadata or a local snapshot violates the contract."""


@dataclass(frozen=True)
class ArtifactSpec:
    relative_path: str
    byte_count: int
    digest_algorithm: str
    digest: str
    role: str
    serialization: str
    required_for_execution: bool = True

    def validate(self) -> None:
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts or not path.name:
            raise ModelRegistryError(f"unsafe artifact path: {self.relative_path!r}")
        if self.byte_count <= 0:
            raise ModelRegistryError(f"artifact size must be positive: {self.relative_path}")
        if self.digest_algorithm == "sha256":
            valid = bool(_SHA256.fullmatch(self.digest))
        elif self.digest_algorithm == "git-blob-sha1":
            valid = bool(_SHA1.fullmatch(self.digest))
        else:
            raise ModelRegistryError(f"unsupported digest algorithm: {self.digest_algorithm}")
        if not valid:
            raise ModelRegistryError(f"invalid digest for {self.relative_path}")


@dataclass(frozen=True)
class ModelSpec:
    candidate_id: str
    channel: str
    model_id: str
    official_owner: str
    official_repository_url: str
    revision: str
    tokenizer_revision: str
    license_spdx: str
    eligibility: str
    production_eligible: bool
    execution_state: str
    execution_blockers: tuple[str, ...]
    trust_remote_code_required: bool
    custom_code_repository: str | None
    custom_code_revision: str | None
    custom_code_reviewed: bool
    custom_code_sha256: str | None
    parameter_count_label: str
    embedding_dimension: int | None
    maximum_input_tokens: int
    pooling: str
    normalization: str
    weight_dtype: str
    execution_dtype_cpu: str
    quantization_state: str
    query_template: str | None
    document_template: str | None
    symmetric_mode: str | None
    language_coverage: str
    minimum_length_policy: str | None
    transformers_compatibility: str
    loader_family: str
    pickle_weight_present: bool
    minimal_snapshot_bytes: int
    full_repository_bytes_approx: int
    excluded_download_globs: tuple[str, ...]
    artifacts: tuple[ArtifactSpec, ...]

    def validate(self) -> None:
        if self.candidate_id not in {
            *DENSE_CANDIDATE_IDS,
            *SPARSE_CANDIDATE_IDS,
            *LANGUAGE_ID_CANDIDATE_IDS,
        }:
            raise ModelRegistryError(f"unexpected candidate ID: {self.candidate_id}")
        if not _REVISION.fullmatch(self.revision):
            raise ModelRegistryError(f"model revision is not immutable: {self.candidate_id}")
        if not _REVISION.fullmatch(self.tokenizer_revision):
            raise ModelRegistryError(f"tokenizer revision is not immutable: {self.candidate_id}")
        if self.eligibility not in {PRODUCTION_ELIGIBLE, RESEARCH_ONLY, REJECT}:
            raise ModelRegistryError(f"invalid eligibility: {self.candidate_id}")
        if self.production_eligible != (self.eligibility == PRODUCTION_ELIGIBLE):
            raise ModelRegistryError(f"production eligibility conflict: {self.candidate_id}")
        if self.execution_state not in {
            EXECUTION_READY,
            EXECUTION_CONDITIONAL,
            EXECUTION_BLOCKED,
        }:
            raise ModelRegistryError(f"invalid execution state: {self.candidate_id}")
        if self.execution_state != EXECUTION_READY and not self.execution_blockers:
            raise ModelRegistryError(f"conditional/blocked candidate lacks blockers: {self.candidate_id}")
        if self.trust_remote_code_required and self.execution_state == EXECUTION_READY:
            if not self.custom_code_reviewed or not self.custom_code_sha256:
                raise ModelRegistryError("unreviewed remote code cannot be execution-ready")
        if self.custom_code_revision is not None and not _REVISION.fullmatch(
            self.custom_code_revision
        ):
            raise ModelRegistryError(f"custom code revision is not immutable: {self.candidate_id}")
        if self.custom_code_sha256 is not None and not _SHA256.fullmatch(
            self.custom_code_sha256
        ):
            raise ModelRegistryError(f"invalid custom code hash: {self.candidate_id}")
        if self.maximum_input_tokens <= 0:
            raise ModelRegistryError(f"invalid maximum input length: {self.candidate_id}")
        if not self.language_coverage.strip():
            raise ModelRegistryError(f"language coverage is missing: {self.candidate_id}")
        if self.channel == "LANGUAGE_ID" and not self.minimum_length_policy:
            raise ModelRegistryError("language-ID candidate lacks a minimum-length policy")
        if self.channel != "LANGUAGE_ID" and (
            self.embedding_dimension is None or self.embedding_dimension <= 0
        ):
            raise ModelRegistryError(f"embedding dimension is required: {self.candidate_id}")
        paths = [artifact.relative_path for artifact in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ModelRegistryError(f"duplicate artifact paths: {self.candidate_id}")
        for artifact in self.artifacts:
            artifact.validate()
        required_bytes = sum(
            artifact.byte_count
            for artifact in self.artifacts
            if artifact.required_for_execution
        )
        if required_bytes != self.minimal_snapshot_bytes:
            raise ModelRegistryError(
                f"snapshot byte receipt differs from artifact sum: {self.candidate_id}"
            )
        if self.channel != "LANGUAGE_ID":
            config = [a for a in self.artifacts if a.relative_path == "config.json"]
            if len(config) != 1:
                raise ModelRegistryError(f"configuration hash is missing: {self.candidate_id}")
        weights = [a for a in self.artifacts if a.role in {"WEIGHTS", "LID_WEIGHTS"}]
        if not weights:
            raise ModelRegistryError(f"weight hash is missing: {self.candidate_id}")

    @property
    def artifact_paths(self) -> tuple[str, ...]:
        return tuple(artifact.relative_path for artifact in self.artifacts)


def _a(
    path: str,
    size: int,
    digest: str,
    role: str,
    serialization: str,
    *,
    algorithm: str = "sha256",
) -> ArtifactSpec:
    return ArtifactSpec(path, size, algorithm, digest, role, serialization)


_QWEN_ARTIFACTS = (
    _a("model.safetensors", 1_191_586_416, "0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd", "WEIGHTS", "safetensors"),
    _a("config.json", 727, "b5bf1f51fc45be473a54718cef92448d90a1be001bf9b9a44b8c7f10a19feaa9", "CONFIGURATION", "json"),
    _a("tokenizer.json", 11_423_705, "def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a", "TOKENIZER", "tokenizers-json"),
    _a("tokenizer_config.json", 9_706, "253153d0738ceb4c668d2eff957714dd2bea0b56de772a9fdccd96cbf517e6a0", "TOKENIZER_CONFIG", "json"),
    _a("1_Pooling/config.json", 313, "37bf193fa101f19101bfad9c31d3eb0f786e247b7b1e5cb7f007d730eed1ddbd", "POOLING_CONFIG", "json"),
    _a("config_sentence_transformers.json", 215, "10667c72ddb772627bf1780cb7f86af8e2ae0032b8c243c731172064105c6961", "SENTENCE_TRANSFORMERS_CONFIG", "json"),
    _a("modules.json", 349, "84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf", "MODULE_CONFIG", "json"),
    _a("README.md", 17_237, "c34d9b7e5a267ad3fdd13227a253686bc90844ff4744a2a6a86c7c905e3d06f3", "MODEL_CARD", "markdown"),
)

_E5_ARTIFACTS = (
    _a("model.safetensors", 1_119_825_680, "dd6b6e4f52db0a7aff83a13d10e6c5342ef9f6ab799bad3221f4b35ef390fa85", "WEIGHTS", "safetensors"),
    _a("config.json", 690, "d185df634c872f06fc6dcb3bad4375d3c447234baea8a6e548103f653b595a35", "CONFIGURATION", "json"),
    _a("tokenizer.json", 17_082_756, "f59925fcb90c92b894cb93e51bb9b4a6105c5c249fe54ce1c704420ac39b81af", "TOKENIZER", "tokenizers-json"),
    _a("tokenizer_config.json", 1_182, "49f06d15a18f81855c338f8ab6241ca2e502a65b62968be69b74f094489f8175", "TOKENIZER_CONFIG", "json"),
    _a("special_tokens_map.json", 964, "8c785abebea9ae3257b61681b4e6fd8365ceafde980c21970d001e834cf10835", "SPECIAL_TOKENS", "json"),
    _a("1_Pooling/config.json", 271, "aa629215c1d83e73d9c51184e566f2c53456bc742f936984355a2990c8c8d046", "POOLING_CONFIG", "json"),
    _a("modules.json", 349, "84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf", "MODULE_CONFIG", "json"),
    _a("README.md", 140_205, "41676700d80691ac2f4397ee2b546ef58f9e3236af2f3d0770ab0fa61940ce51", "MODEL_CARD", "markdown"),
)

_BGE_ARTIFACTS = (
    _a("pytorch_model.bin", 2_271_145_830, "b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38", "WEIGHTS", "pytorch-pickle"),
    _a("sparse_linear.pt", 3_516, "45c93804d2142b8f6d7ec6914ae23a1eee9c6a1d27d83d908a20d2afb3595ad9", "SPARSE_HEAD", "pytorch-pickle"),
    _a("colbert_linear.pt", 2_100_674, "19bfbae397c2b7524158c919d0e9b19393c5639d098f0a66932c91ed8f5f9abb", "COLBERT_HEAD", "pytorch-pickle"),
    _a("config.json", 687, "e6eda1c72da8f9dc30fdd9b69c73d35af3b7a7ad", "CONFIGURATION", "json", algorithm="git-blob-sha1"),
    _a("tokenizer.json", 17_098_108, "21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08", "TOKENIZER", "tokenizers-json"),
    _a("tokenizer_config.json", 444, "dc69ac559dcba2694012009aaa108c614541789a", "TOKENIZER_CONFIG", "json", algorithm="git-blob-sha1"),
    _a("sentencepiece.bpe.model", 5_069_051, "cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865", "TOKENIZER_MODEL", "sentencepiece"),
)

_JINA_ARTIFACTS = (
    _a("model.safetensors", 1_144_685_320, "17ca06efd886a065d0081912b04c9e27ef5086a9dd09659cce32aa9c84587f23", "WEIGHTS", "safetensors"),
    _a("config.json", 1_799, "f18804ccf37932b05a75e55c915cf9731b9f77f8", "CONFIGURATION", "json", algorithm="git-blob-sha1"),
    _a("tokenizer.json", 17_082_756, "f59925fcb90c92b894cb93e51bb9b4a6105c5c249fe54ce1c704420ac39b81af", "TOKENIZER", "tokenizers-json"),
    _a("tokenizer_config.json", 1_148, "8cc4b5371966caaa004a24ee183bc6dbda9dbd4d", "TOKENIZER_CONFIG", "json", algorithm="git-blob-sha1"),
)

_LID_ARTIFACTS = (
    _a("model.ftz", 149_855_754, "ace2b2cbcb87068546b1bd5961c0e7f18dd4916e8573d1cf66ade9d074cad922", "LID_WEIGHTS", "fasttext-ftz"),
)


def _snapshot_bytes(artifacts: Iterable[ArtifactSpec]) -> int:
    return sum(a.byte_count for a in artifacts if a.required_for_execution)


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "NLP-D1": ModelSpec(
        candidate_id="NLP-D1",
        channel="DENSE",
        model_id="Qwen/Qwen3-Embedding-0.6B",
        official_owner="Qwen",
        official_repository_url="https://huggingface.co/Qwen/Qwen3-Embedding-0.6B",
        revision="97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        tokenizer_revision="97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        license_spdx="Apache-2.0",
        eligibility=PRODUCTION_ELIGIBLE,
        production_eligible=True,
        execution_state=EXECUTION_READY,
        execution_blockers=(),
        trust_remote_code_required=False,
        custom_code_repository=None,
        custom_code_revision=None,
        custom_code_reviewed=False,
        custom_code_sha256=None,
        parameter_count_label="0.6B",
        embedding_dimension=1_024,
        maximum_input_tokens=32_768,
        pooling="last non-padding token",
        normalization="L2",
        weight_dtype="bfloat16",
        execution_dtype_cpu="float32",
        quantization_state="unquantized",
        query_template="Instruct: {task_description}\nQuery:{query}",
        document_template="{document}",
        symmetric_mode="plain-document/plain-document diagnostic; not an official symmetric adapter",
        language_coverage="100+ languages (official model-card claim)",
        minimum_length_policy=None,
        transformers_compatibility="native qwen3; Transformers >=4.51.0; executed pin 5.12.0",
        loader_family="transformers-auto-model-qwen3-last-token",
        pickle_weight_present=False,
        minimal_snapshot_bytes=_snapshot_bytes(_QWEN_ARTIFACTS),
        full_repository_bytes_approx=1_210_000_000,
        excluded_download_globs=("onnx/**", "*.bin"),
        artifacts=_QWEN_ARTIFACTS,
    ),
    "NLP-D2": ModelSpec(
        candidate_id="NLP-D2",
        channel="DENSE",
        model_id="BAAI/bge-m3",
        official_owner="BAAI / FlagOpen",
        official_repository_url="https://huggingface.co/BAAI/bge-m3",
        revision="5617a9f61b028005a4858fdac845db406aefb181",
        tokenizer_revision="5617a9f61b028005a4858fdac845db406aefb181",
        license_spdx="MIT",
        eligibility=PRODUCTION_ELIGIBLE,
        production_eligible=True,
        execution_state=EXECUTION_CONDITIONAL,
        execution_blockers=("pickle-formatted weights require explicit review/authorization",),
        trust_remote_code_required=False,
        custom_code_repository=None,
        custom_code_revision=None,
        custom_code_reviewed=False,
        custom_code_sha256=None,
        parameter_count_label="569M",
        embedding_dimension=1_024,
        maximum_input_tokens=8_192,
        pooling="CLS token",
        normalization="L2",
        weight_dtype="float32",
        execution_dtype_cpu="float32",
        quantization_state="unquantized",
        query_template="{query}",
        document_template="{document}",
        symmetric_mode="plain/plain; model card requires no query instruction",
        language_coverage="100+ working languages; training data spans 170+ languages",
        minimum_length_policy=None,
        transformers_compatibility="native XLM-R dense path; sparse path uses FlagEmbedding v1.4.0",
        loader_family="transformers-auto-model-xlm-roberta-cls",
        pickle_weight_present=True,
        minimal_snapshot_bytes=_snapshot_bytes(_BGE_ARTIFACTS),
        full_repository_bytes_approx=4_590_000_000,
        excluded_download_globs=("onnx/**",),
        artifacts=_BGE_ARTIFACTS,
    ),
    "NLP-S1": ModelSpec(
        candidate_id="NLP-S1",
        channel="SPARSE",
        model_id="BAAI/bge-m3",
        official_owner="BAAI / FlagOpen",
        official_repository_url="https://huggingface.co/BAAI/bge-m3",
        revision="5617a9f61b028005a4858fdac845db406aefb181",
        tokenizer_revision="5617a9f61b028005a4858fdac845db406aefb181",
        license_spdx="MIT",
        eligibility=PRODUCTION_ELIGIBLE,
        production_eligible=True,
        execution_state=EXECUTION_CONDITIONAL,
        execution_blockers=(
            "FlagEmbedding source and pickle weights require review/authorization",
        ),
        trust_remote_code_required=False,
        custom_code_repository="https://github.com/FlagOpen/FlagEmbedding",
        custom_code_revision="7ed43d67ec03fbe5c31c0992dbfa941fb1860549",
        custom_code_reviewed=False,
        custom_code_sha256=None,
        parameter_count_label="569M plus sparse head",
        embedding_dimension=1_024,
        maximum_input_tokens=8_192,
        pooling="learned lexical sparse weights",
        normalization="model-defined sparse scoring",
        weight_dtype="float32",
        execution_dtype_cpu="float32",
        quantization_state="unquantized",
        query_template="{query}",
        document_template="{document}",
        symmetric_mode="plain/plain; model card requires no query instruction",
        language_coverage="100+ working languages; training data spans 170+ languages",
        minimum_length_policy=None,
        transformers_compatibility="FlagEmbedding v1.4.0 (Transformers v5 compatibility release)",
        loader_family="flagembedding-m3-sparse",
        pickle_weight_present=True,
        minimal_snapshot_bytes=_snapshot_bytes(_BGE_ARTIFACTS),
        full_repository_bytes_approx=4_590_000_000,
        excluded_download_globs=("onnx/**",),
        artifacts=_BGE_ARTIFACTS,
    ),
    "NLP-D3": ModelSpec(
        candidate_id="NLP-D3",
        channel="DENSE",
        model_id="intfloat/multilingual-e5-large-instruct",
        official_owner="intfloat",
        official_repository_url="https://huggingface.co/intfloat/multilingual-e5-large-instruct",
        revision="274baa43b0e13e37fafa6428dbc7938e62e5c439",
        tokenizer_revision="274baa43b0e13e37fafa6428dbc7938e62e5c439",
        license_spdx="MIT",
        eligibility=PRODUCTION_ELIGIBLE,
        production_eligible=True,
        execution_state=EXECUTION_READY,
        execution_blockers=(),
        trust_remote_code_required=False,
        custom_code_repository=None,
        custom_code_revision=None,
        custom_code_reviewed=False,
        custom_code_sha256=None,
        parameter_count_label="0.6B",
        embedding_dimension=1_024,
        maximum_input_tokens=512,
        pooling="attention-mask-weighted mean",
        normalization="L2",
        weight_dtype="float16",
        execution_dtype_cpu="float32",
        quantization_state="unquantized",
        query_template="Instruct: {task_description}\nQuery: {query}",
        document_template="{document}",
        symmetric_mode="plain-document/plain-document diagnostic; not an official symmetric adapter",
        language_coverage="100 languages through the XLM-R training coverage claim",
        minimum_length_policy=None,
        transformers_compatibility="native XLM-R; no remote code; executed pin 5.12.0",
        loader_family="transformers-auto-model-xlm-roberta-mean",
        pickle_weight_present=False,
        minimal_snapshot_bytes=_snapshot_bytes(_E5_ARTIFACTS),
        full_repository_bytes_approx=3_400_000_000,
        excluded_download_globs=("onnx/**", "pytorch_model.bin"),
        artifacts=_E5_ARTIFACTS,
    ),
    "NLP-D4": ModelSpec(
        candidate_id="NLP-D4",
        channel="DENSE",
        model_id="jinaai/jina-embeddings-v3",
        official_owner="jinaai",
        official_repository_url="https://huggingface.co/jinaai/jina-embeddings-v3",
        revision="ab036b023d30b4d1138c4c3bfa9f0c445ab455d6",
        tokenizer_revision="ab036b023d30b4d1138c4c3bfa9f0c445ab455d6",
        license_spdx="CC-BY-NC-4.0",
        eligibility=RESEARCH_ONLY,
        production_eligible=False,
        execution_state=EXECUTION_BLOCKED,
        execution_blockers=(
            "non-commercial license",
            "trust_remote_code is required and custom code is not reviewed/hashed",
        ),
        trust_remote_code_required=True,
        custom_code_repository="https://huggingface.co/jinaai/xlm-roberta-flash-implementation",
        custom_code_revision="bd55a5ec8e6c0fb1d6c26efb4b6a4a74ce8a88d3",
        custom_code_reviewed=False,
        custom_code_sha256=None,
        parameter_count_label="0.6B",
        embedding_dimension=1_024,
        maximum_input_tokens=8_192,
        pooling="mean",
        normalization="L2 after optional Matryoshka truncation",
        weight_dtype="bfloat16",
        execution_dtype_cpu="float32",
        quantization_state="unquantized",
        query_template="task adapter retrieval.query",
        document_template="task adapter retrieval.passage",
        symmetric_mode="vendor text-matching task adapter",
        language_coverage="89 languages (official model-card claim)",
        minimum_length_policy=None,
        transformers_compatibility="custom XLM-R implementation; remote code required",
        loader_family="blocked-unreviewed-remote-code",
        pickle_weight_present=False,
        minimal_snapshot_bytes=_snapshot_bytes(_JINA_ARTIFACTS),
        full_repository_bytes_approx=5_750_000_000,
        excluded_download_globs=("onnx/**", "pytorch_model.bin", "*.py"),
        artifacts=_JINA_ARTIFACTS,
    ),
    "NLP-LID1": ModelSpec(
        candidate_id="NLP-LID1",
        channel="LANGUAGE_ID",
        model_id="facebook/fasttext-language-identification",
        official_owner="Meta / facebook",
        official_repository_url="https://huggingface.co/facebook/fasttext-language-identification",
        revision="9f1c466f5d3c80b0e1cc3985dbccf89859cf67b2",
        tokenizer_revision="9f1c466f5d3c80b0e1cc3985dbccf89859cf67b2",
        license_spdx="CC-BY-NC-4.0",
        eligibility=RESEARCH_ONLY,
        production_eligible=False,
        execution_state=EXECUTION_CONDITIONAL,
        execution_blockers=("non-commercial model artifact; analysis-only",),
        trust_remote_code_required=False,
        custom_code_repository="https://github.com/facebookresearch/fastText",
        custom_code_revision="5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe",
        custom_code_reviewed=False,
        custom_code_sha256=None,
        parameter_count_label="quantized fastText LID classifier",
        embedding_dimension=None,
        maximum_input_tokens=1,
        pooling="N/A",
        normalization="N/A",
        weight_dtype="fastText quantized",
        execution_dtype_cpu="native CPU",
        quantization_state="quantized .ftz",
        query_template=None,
        document_template=None,
        symmetric_mode=None,
        language_coverage="217 language/script labels (NLLB lid218e artifact)",
        minimum_length_policy=(
            "fewer than 20 Unicode letters => UNDETERMINED; otherwise accept top-1 only "
            "at p>=0.80 and top1-top2 margin>=0.20 with script compatibility; "
            "predeclared 10/20/40-letter sensitivity"
        ),
        transformers_compatibility="not a Transformers model; official fastText v0.9.2",
        loader_family="fasttext-native",
        pickle_weight_present=False,
        minimal_snapshot_bytes=_snapshot_bytes(_LID_ARTIFACTS),
        full_repository_bytes_approx=149_900_000,
        excluded_download_globs=("model.bin",),
        artifacts=_LID_ARTIFACTS,
    ),
}


def get_model(candidate_id: str) -> ModelSpec:
    try:
        return MODEL_REGISTRY[candidate_id]
    except KeyError as exc:
        raise ModelRegistryError(f"unknown model candidate: {candidate_id}") from exc


def _digest_file(path: Path, algorithm: str) -> str:
    if algorithm == "sha256":
        digest = hashlib.sha256()
        prefix = b""
    elif algorithm == "git-blob-sha1":
        digest = hashlib.sha1()
        prefix = f"blob {path.stat().st_size}\0".encode("ascii")
    else:
        raise ModelRegistryError(f"unsupported digest algorithm: {algorithm}")
    digest.update(prefix)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_local_snapshot(
    candidate_id: str,
    snapshot_path: str | Path,
    *,
    reject_unregistered_runtime_files: bool = True,
) -> dict[str, Any]:
    """Verify a local, already-downloaded snapshot without network access."""

    spec = get_model(candidate_id)
    root = Path(snapshot_path).expanduser().resolve()
    if not root.is_dir():
        raise ModelRegistryError(f"snapshot directory does not exist: {root}")
    rows: list[dict[str, Any]] = []
    for artifact in spec.artifacts:
        if not artifact.required_for_execution:
            continue
        target = root / artifact.relative_path
        if not target.is_file() or target.is_symlink():
            raise ModelRegistryError(
                f"required artifact missing or symlinked: {artifact.relative_path}"
            )
        actual_bytes = target.stat().st_size
        if actual_bytes != artifact.byte_count:
            raise ModelRegistryError(f"artifact byte mismatch: {artifact.relative_path}")
        actual_digest = _digest_file(target, artifact.digest_algorithm)
        if actual_digest != artifact.digest:
            raise ModelRegistryError(f"artifact digest mismatch: {artifact.relative_path}")
        rows.append(
            {
                "relativePath": artifact.relative_path,
                "byteCount": actual_bytes,
                "digestAlgorithm": artifact.digest_algorithm,
                "digest": actual_digest,
                "role": artifact.role,
            }
        )
    if reject_unregistered_runtime_files:
        declared = set(spec.artifact_paths)
        dangerous_suffixes = {".py", ".pyc", ".so", ".dylib", ".dll", ".bin", ".pt", ".pth", ".safetensors", ".onnx"}
        unexpected = []
        for path in root.rglob("*"):
            if not path.is_file() or ".cache" in path.relative_to(root).parts:
                continue
            relative = path.relative_to(root).as_posix()
            if path.suffix.casefold() in dangerous_suffixes and relative not in declared:
                unexpected.append(relative)
        if unexpected:
            raise ModelRegistryError(
                "snapshot contains unregistered executable/weight files: "
                + ", ".join(sorted(unexpected))
            )
    receipt_material = {
        "schemaVersion": "trace-nlp-model-artifact-verification/v1",
        "candidateId": candidate_id,
        "modelId": spec.model_id,
        "revision": spec.revision,
        "tokenizerRevision": spec.tokenizer_revision,
        "artifactCount": len(rows),
        "verifiedBytes": sum(row["byteCount"] for row in rows),
        "artifacts": sorted(rows, key=lambda row: row["relativePath"]),
        "offlineOnly": True,
        "trustRemoteCode": False,
    }
    canonical = json.dumps(
        receipt_material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        **receipt_material,
        "verificationSha256": hashlib.sha256(canonical).hexdigest(),
    }


def registry_receipt() -> dict[str, Any]:
    rows = []
    for candidate_id in sorted(MODEL_REGISTRY):
        spec = MODEL_REGISTRY[candidate_id]
        spec.validate()
        rows.append(asdict(spec))
    material = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "sourceSha": SOURCE_SHA,
        "executedRuntime": {
            "environmentPath": "/private/tmp/trace-nlp-v1-venv",
            "systemSitePackages": True,
            "versionEvidence": "distribution version plus successful import in executed environment",
            "importsConfirmed": sorted(
                package for package in RUNTIME_PINS if package != "python"
            ),
            "pins": dict(sorted(RUNTIME_PINS.items())),
        },
        "futureRecommendedRuntimePins": dict(
            sorted(FUTURE_RECOMMENDED_RUNTIME_PINS.items())
        ),
        "fullCorpusExecutionShortlist": list(FULL_CORPUS_EXECUTION_SHORTLIST),
        "models": rows,
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {**material, "registrySha256": hashlib.sha256(encoded).hexdigest()}


def run_self_tests() -> dict[str, Any]:
    receipt = registry_receipt()
    if set(MODEL_REGISTRY) != {
        *DENSE_CANDIDATE_IDS,
        *SPARSE_CANDIDATE_IDS,
        *LANGUAGE_ID_CANDIDATE_IDS,
    }:
        raise AssertionError("registry candidate set changed")
    if tuple(
        candidate_id
        for candidate_id in sorted(MODEL_REGISTRY)
        if MODEL_REGISTRY[candidate_id].execution_state == EXECUTION_READY
    ) != FULL_CORPUS_EXECUTION_SHORTLIST:
        raise AssertionError("execution-ready shortlist changed")
    jina = get_model("NLP-D4")
    if (
        jina.eligibility != RESEARCH_ONLY
        or jina.production_eligible
        or not jina.trust_remote_code_required
        or jina.custom_code_reviewed
    ):
        raise AssertionError("Jina remote-code/license gate weakened")
    lid = get_model("NLP-LID1")
    if lid.eligibility != RESEARCH_ONLY or lid.production_eligible:
        raise AssertionError("LID license gate weakened")
    for candidate_id in FULL_CORPUS_EXECUTION_SHORTLIST:
        spec = get_model(candidate_id)
        if spec.trust_remote_code_required or spec.pickle_weight_present:
            raise AssertionError("shortlist admits remote code or pickle weights")
    return {
        "schemaVersion": "trace-nlp-model-registry-self-test/v1",
        "status": "PASS",
        "candidateCount": len(MODEL_REGISTRY),
        "fullCorpusExecutionShortlist": list(FULL_CORPUS_EXECUTION_SHORTLIST),
        "registrySha256": receipt["registrySha256"],
        "networkCalls": 0,
        "modelLoads": 0,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the full registry")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-candidate")
    parser.add_argument("--snapshot")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return 0
    if args.verify_candidate or args.snapshot:
        if not args.verify_candidate or not args.snapshot:
            raise SystemExit("--verify-candidate and --snapshot must be supplied together")
        print(
            json.dumps(
                verify_local_snapshot(args.verify_candidate, args.snapshot),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    receipt = registry_receipt()
    if args.json:
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(
            json.dumps(
                {
                    "schemaVersion": receipt["schemaVersion"],
                    "candidateCount": len(receipt["models"]),
                    "fullCorpusExecutionShortlist": receipt[
                        "fullCorpusExecutionShortlist"
                    ],
                    "registrySha256": receipt["registrySha256"],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
