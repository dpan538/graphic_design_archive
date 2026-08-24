#!/usr/bin/env python3
"""Bounded exact-cosine index for in-memory TRACE NLP embeddings.

The index never materializes an all-pairs matrix or writes by default.  Query
and candidate identities remain in canonical public-ID order; score ties break
by public ID.  Optional ranking persistence is restricted to an explicit OS
temporary path and contains public IDs plus bounded top-k observations only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import re
import statistics
import tempfile
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import common as governance_common
import corpus_builder


SCHEMA_VERSION = "trace-nlp-dense-exact-index/v1"
IMPLEMENTATION_VERSION = "trace-nlp-dense-exact-index-2026-08-24"
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
MAX_OBJECTS = 7_995
MAX_TOP_K = 50
MAX_TEMP_TOPK_BYTES = 96 * 1024**2
APPROVED_ASPECT_IDS = frozenset(
    {"NLP_TITLE", "NLP_SUBJECT", "NLP_SOURCE_NARRATIVE", "NLP_OBJECT_SEMANTIC_COMPOSITE"}
)


class EmbeddingIndexError(ValueError):
    """Raised when an embedding/index request violates the bounded contract."""


@lru_cache(maxsize=1)
def _authoritative_base_corpus_sha256() -> str:
    bundle = corpus_builder.build_corpus_bundle(include_text=False)
    value = str(bundle.get("corpusSha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise EmbeddingIndexError("governed corpus builder lacks an authoritative corpus identity")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _quantile_r7(values: Sequence[int | float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


@dataclass(frozen=True)
class RankingObservation:
    rank: int
    candidate_public_id: str
    score: float

    def as_mapping(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "candidatePublicId": self.candidate_public_id,
            "score": self.score,
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
        }


class ExactCosineIndex:
    """Normalized float32 vectors with streamed exact cosine queries."""

    def __init__(
        self,
        public_object_ids: Sequence[str],
        embeddings: Any,
        *,
        corpus_sha256: str,
        pilot_diagnostic: bool = False,
        availability_mask: Any | None = None,
        embedding_observation_sha256: str | None = None,
    ) -> None:
        np = importlib.import_module("numpy")
        ids = tuple(str(value) for value in public_object_ids)
        if not ids or len(ids) > MAX_OBJECTS:
            raise EmbeddingIndexError("index object count is outside the public boundary")
        if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
            raise EmbeddingIndexError("index IDs must be sorted and unique")
        if any(not PUBLIC_ID_PATTERN.fullmatch(value) for value in ids):
            raise EmbeddingIndexError("index contains a non-public identity")
        authoritative_ids = governance_common.load_public_ids()
        authoritative_set = set(authoritative_ids)
        if any(value not in authoritative_set for value in ids):
            raise EmbeddingIndexError("index identity is outside the authoritative public cohort")
        if len(ids) == MAX_OBJECTS and ids != authoritative_ids:
            raise EmbeddingIndexError("full-size index identities differ from the public ledger")
        if str(corpus_sha256) != _authoritative_base_corpus_sha256():
            raise EmbeddingIndexError("index corpusSha256 differs from the governed base-corpus receipt")
        if (len(ids) < MAX_OBJECTS) != bool(pilot_diagnostic):
            raise EmbeddingIndexError("subset indexing requires an explicit pilot diagnostic declaration")
        vectors = np.asarray(embeddings, dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] != len(ids) or vectors.shape[1] <= 0:
            raise EmbeddingIndexError("embedding shape does not match canonical IDs")
        if not np.isfinite(vectors).all():
            raise EmbeddingIndexError("index contains non-finite embeddings")
        if availability_mask is None:
            available = np.ones(len(ids), dtype=np.bool_)
        else:
            available = np.asarray(availability_mask, dtype=np.bool_)
            if available.shape != (len(ids),) or not bool(available.any()):
                raise EmbeddingIndexError("availability mask is empty or shape-invalid")
        norms = np.linalg.norm(vectors[available], axis=1)
        if not np.allclose(norms, 1.0, rtol=0.0, atol=2e-4):
            raise EmbeddingIndexError("available exact-cosine rows must be L2-normalized")
        if np.any(vectors[~available] != 0.0):
            raise EmbeddingIndexError("unavailable aspect rows must be exact zeros")
        observed_hash = hashlib.sha256(
            vectors.astype("<f4", copy=False).tobytes(order="C")
        ).hexdigest()
        if embedding_observation_sha256 is not None and observed_hash != embedding_observation_sha256:
            raise EmbeddingIndexError("embedding observation hash changed")
        self.object_ids = ids
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        self.availability_mask = np.ascontiguousarray(available, dtype=np.bool_)
        self.available_object_ids = tuple(
            object_id for object_id, is_available in zip(ids, available) if is_available
        )
        self.embedding_observation_sha256 = observed_hash
        self.corpus_sha256 = str(corpus_sha256)
        self.pilot_diagnostic = bool(pilot_diagnostic)
        self._ordinal = {value: index for index, value in enumerate(ids)}
        self.index_sha256 = _sha256_json(
            {
                "schemaVersion": SCHEMA_VERSION,
                "corpusSha256": self.corpus_sha256,
                "pilotDiagnostic": self.pilot_diagnostic,
                "publicObjectIds": ids,
                "shape": list(self.vectors.shape),
                "dtype": "float32-little-endian-observation",
                "embeddingObservationSha256": observed_hash,
                "availabilityMaskSha256": hashlib.sha256(
                    self.availability_mask.tobytes(order="C")
                ).hexdigest(),
            }
        )

    @property
    def serialized_bytes(self) -> int:
        return int(self.vectors.nbytes)

    def _scores(self, query_vector: Any) -> Any:
        np = importlib.import_module("numpy")
        query = np.asarray(query_vector, dtype=np.float32)
        if query.shape != (self.vectors.shape[1],) or not np.isfinite(query).all():
            raise EmbeddingIndexError("query vector has an invalid shape/value")
        norm = float(np.linalg.norm(query))
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=2e-4):
            raise EmbeddingIndexError("query vector must be L2-normalized")
        return self.vectors @ query

    def _top_ordinals(
        self,
        scores: Any,
        *,
        top_k: int,
        excluded_ordinal: int | None,
    ) -> tuple[int, ...]:
        np = importlib.import_module("numpy")
        available_count = int(self.availability_mask.sum()) - int(
            excluded_ordinal is not None
        )
        if top_k <= 0 or top_k > MAX_TOP_K or top_k > available_count:
            raise EmbeddingIndexError("top-k is outside the bounded candidate count")
        work = np.asarray(scores, dtype=np.float32).copy()
        work[~self.availability_mask] = -np.inf
        if excluded_ordinal is not None:
            work[excluded_ordinal] = -np.inf
        # Argpartition locates the boundary efficiently.  All exact ties at the
        # boundary are then included before score-desc/public-ID sorting.
        partition = np.argpartition(-work, top_k - 1)[:top_k]
        threshold = float(work[partition].min())
        eligible = np.flatnonzero(work >= threshold)
        order = np.lexsort((eligible, -work[eligible]))
        return tuple(int(value) for value in eligible[order][:top_k])

    def query_vector(
        self,
        query_vector: Any,
        *,
        top_k: int,
        exclude_public_object_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        excluded = None
        if exclude_public_object_id is not None:
            try:
                excluded = self._ordinal[exclude_public_object_id]
            except KeyError as exc:
                raise EmbeddingIndexError("excluded query ID is not in the index") from exc
        scores = self._scores(query_vector)
        ordinals = self._top_ordinals(
            scores, top_k=top_k, excluded_ordinal=excluded
        )
        return tuple(
            RankingObservation(rank, self.object_ids[ordinal], float(scores[ordinal])).as_mapping()
            for rank, ordinal in enumerate(ordinals, start=1)
        )

    def query_id(self, public_object_id: str, *, top_k: int) -> tuple[dict[str, Any], ...]:
        try:
            ordinal = self._ordinal[public_object_id]
        except KeyError as exc:
            raise EmbeddingIndexError("query ID is not in the index") from exc
        if not bool(self.availability_mask[ordinal]):
            raise EmbeddingIndexError("query ID has no available aspect vector")
        return self.query_vector(
            self.vectors[ordinal],
            top_k=top_k,
            exclude_public_object_id=public_object_id,
        )

    def rank_target(self, query_id: str, target_id: str) -> dict[str, Any]:
        if query_id == target_id:
            raise EmbeddingIndexError("self cannot be a target")
        try:
            query_ordinal = self._ordinal[query_id]
            target_ordinal = self._ordinal[target_id]
        except KeyError as exc:
            raise EmbeddingIndexError("rank target identities must be indexed") from exc
        if not self.availability_mask[query_ordinal] or not self.availability_mask[target_ordinal]:
            raise EmbeddingIndexError("rank target requires two available aspect vectors")
        np = importlib.import_module("numpy")
        scores = self._scores(self.vectors[query_ordinal])
        target_score = float(scores[target_ordinal])
        eligible = self.availability_mask & (np.arange(len(self.object_ids)) != query_ordinal)
        strictly_greater = int(np.count_nonzero(eligible & (scores > target_score)))
        equal_before = int(
            np.count_nonzero(
                eligible
                & (scores == target_score)
                & (np.arange(len(self.object_ids)) < target_ordinal)
            )
        )
        return {
            "queryPublicId": query_id,
            "targetPublicId": target_id,
            "rank": 1 + strictly_greater + equal_before,
            "score": target_score,
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
        }

    def rank_all(
        self,
        *,
        method_id: str,
        corpus_sha256: str,
        input_variant: str,
        aspect_ids: Sequence[str],
        full_corpus: bool,
        top_k: int = 50,
        query_ids: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        queries = tuple(sorted(set(query_ids or self.available_object_ids)))
        if not queries or any(
            value not in self._ordinal
            or not bool(self.availability_mask[self._ordinal[value]])
            for value in queries
        ):
            raise EmbeddingIndexError("ranking query cohort is empty or outside the index")
        if corpus_sha256 != self.corpus_sha256:
            raise EmbeddingIndexError("ranking corpusSha256 differs from the indexed corpus")
        actual_full_corpus = self.object_ids == governance_common.load_public_ids()
        if bool(full_corpus) != actual_full_corpus:
            raise EmbeddingIndexError("full-corpus declaration differs from the indexed public cohort")
        if not str(method_id).strip() or not str(input_variant).strip():
            raise EmbeddingIndexError("ranking method/input variant is absent")
        if not aspect_ids or len(set(aspect_ids)) != len(aspect_ids) or set(aspect_ids) - APPROVED_ASPECT_IDS:
            raise EmbeddingIndexError("ranking aspects are absent, duplicated, or ungoverned")
        started = time.perf_counter()
        latencies_ms: list[float] = []
        rankings: dict[str, tuple[dict[str, Any], ...]] = {}
        for query_id in queries:
            query_started = time.perf_counter()
            rankings[query_id] = self.query_id(query_id, top_k=top_k)
            latencies_ms.append((time.perf_counter() - query_started) * 1000.0)
        elapsed = time.perf_counter() - started
        ranking_ids_material = {
            query_id: [row["candidatePublicId"] for row in rankings[query_id]]
            for query_id in queries
        }
        score_material = {
            query_id: [row["score"] for row in rankings[query_id]]
            for query_id in queries
        }
        return {
            "schemaVersion": SCHEMA_VERSION,
            "methodId": method_id,
            "implementationVersion": IMPLEMENTATION_VERSION,
            "corpusSha256": corpus_sha256,
            "inputVariant": input_variant,
            "aspectIds": list(aspect_ids),
            "fullCorpus": bool(full_corpus),
            "topK": top_k,
            "objectCount": len(self.object_ids),
            "fullPublicCohort": actual_full_corpus,
            "aspectAvailableObjectCount": len(self.available_object_ids),
            "aspectUnavailableObjectCount": len(self.object_ids)
            - len(self.available_object_ids),
            "missingAspectRowsZero": True,
            "queryCount": len(queries),
            "indexSha256": self.index_sha256,
            "embeddingObservationSha256": self.embedding_observation_sha256,
            "rankingIdsSha256": _sha256_json(ranking_ids_material),
            "scoreObservationSha256": _sha256_json(score_material),
            "performance": {
                "denseIndexBytes": self.serialized_bytes,
                "denseExactQueryP50Ms": _quantile_r7(latencies_ms, 0.50),
                "denseExactQueryP95Ms": _quantile_r7(latencies_ms, 0.95),
                "rankingElapsedMs": round(elapsed * 1000.0, 3),
            },
            "rankings": rankings,
            "pairMatrixMaterialized": False,
            "vectorDatabaseAdded": False,
            "seedUsed": False,
            "historicalRelationProduced": False,
            "probabilityProduced": False,
        }


def bounded_result_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    """Strip in-memory rankings before any committed audit/research output."""

    if "rankings" not in result:
        raise EmbeddingIndexError("ranking result lacks in-memory rankings")
    summary = {key: value for key, value in result.items() if key != "rankings"}
    summary["rankingRowsRetained"] = 0
    summary["fullRankingsCommitted"] = False
    return summary


def _approved_temp_path(path: str | Path) -> Path:
    raw = Path(path).expanduser()
    if not raw.is_absolute():
        raise EmbeddingIndexError("top-k temp path must be explicit and absolute")
    target = raw.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if target != temp_root and temp_root not in target.parents:
        raise EmbeddingIndexError("top-k rows may be written only below the OS temp root")
    if target.suffix != ".jsonl":
        raise EmbeddingIndexError("top-k temp output must use .jsonl")
    if target.exists():
        raise EmbeddingIndexError("top-k temp output exists; refusing overwrite")
    return target


def write_topk_temp(result: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    rankings = result.get("rankings")
    if not isinstance(rankings, Mapping):
        raise EmbeddingIndexError("result lacks in-memory rankings")
    target = _approved_temp_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    byte_count = 0
    row_count = 0
    with target.open("xb") as handle:
        for query_id in sorted(rankings):
            payload = _canonical_json_bytes(
                {"queryPublicId": query_id, "neighbors": rankings[query_id]}
            ) + b"\n"
            byte_count += len(payload)
            if byte_count > MAX_TEMP_TOPK_BYTES:
                raise EmbeddingIndexError("bounded top-k temp output limit exceeded")
            handle.write(payload)
            digest.update(payload)
            row_count += len(rankings[query_id])
    return {
        "schemaVersion": "trace-nlp-temp-topk-receipt/v1",
        "path": str(target),
        "byteCount": byte_count,
        "sha256": digest.hexdigest(),
        "queryCount": len(rankings),
        "neighborRowCount": row_count,
        "temporary": True,
        "committable": False,
    }


def run_self_tests() -> dict[str, Any]:
    np = importlib.import_module("numpy")
    ids = governance_common.load_public_ids()[:4]
    root2 = math.sqrt(0.5)
    vectors = np.asarray(
        [[1.0, 0.0], [root2, root2], [root2, root2], [0.0, 1.0]],
        dtype=np.float32,
    )
    corpus_sha = _authoritative_base_corpus_sha256()
    index = ExactCosineIndex(ids, vectors, corpus_sha256=corpus_sha, pilot_diagnostic=True)
    ranking = index.query_id(ids[0], top_k=3)
    if [row["candidatePublicId"] for row in ranking] != [ids[1], ids[2], ids[3]]:
        raise AssertionError("score/public-ID tie ordering changed")
    if index.rank_target(ids[0], ids[2])["rank"] != 2:
        raise AssertionError("target rank tie handling changed")
    result = index.rank_all(
        method_id="NLP-TEST",
        corpus_sha256=corpus_sha,
        input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
        aspect_ids=("NLP_TITLE",),
        full_corpus=False,
        top_k=2,
    )
    summary = bounded_result_summary(result)
    if "rankings" in summary or summary["fullRankingsCommitted"]:
        raise AssertionError("bounded summary retained full rankings")
    masked_vectors = vectors.copy()
    masked_vectors[2] = 0.0
    masked = ExactCosineIndex(
        ids,
        masked_vectors,
        corpus_sha256=corpus_sha,
        pilot_diagnostic=True,
        availability_mask=np.asarray([True, True, False, True]),
    )
    masked_ranking = masked.query_id(ids[0], top_k=2)
    if ids[2] in {row["candidatePublicId"] for row in masked_ranking}:
        raise AssertionError("unavailable zero row entered an aspect ranking")
    masked_result = masked.rank_all(
        method_id="NLP-TEST-MASKED",
        corpus_sha256=corpus_sha,
        input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
        aspect_ids=("NLP_SUBJECT",),
        full_corpus=False,
        top_k=2,
    )
    if masked_result["queryCount"] != 3 or masked_result["aspectUnavailableObjectCount"] != 1:
        raise AssertionError("aspect availability query boundary changed")
    try:
        ExactCosineIndex(
            ("SURF-NOTINLEDGER",),
            np.asarray([[1.0]], dtype=np.float32),
            corpus_sha256=corpus_sha,
            pilot_diagnostic=True,
        )
    except EmbeddingIndexError:
        pass
    else:
        raise AssertionError("non-ledger identity entered the dense index")
    try:
        index.rank_all(
            method_id="NLP-TEST",
            corpus_sha256=corpus_sha,
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            aspect_ids=("NLP_TITLE",),
            full_corpus=True,
            top_k=2,
        )
    except EmbeddingIndexError:
        pass
    else:
        raise AssertionError("pilot index accepted a full-corpus declaration")
    try:
        ExactCosineIndex(ids, vectors, corpus_sha256="f" * 64, pilot_diagnostic=True)
    except EmbeddingIndexError:
        pass
    else:
        raise AssertionError("arbitrary corpus SHA entered the dense index")
    return {
        "schemaVersion": "trace-nlp-dense-exact-index-self-test/v1",
        "status": "PASS",
        "objectCount": len(ids),
        "topK": 2,
        "tieBreak": "score-desc/public-ID-asc",
        "pairMatrixMaterialized": False,
        "missingAspectRowsExcludedFromQueriesAndCandidates": True,
        "networkCalls": 0,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return 0
    raise SystemExit("index construction requires explicit in-memory embeddings")


if __name__ == "__main__":
    raise SystemExit(main())
