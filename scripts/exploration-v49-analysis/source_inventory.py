#!/usr/bin/env python3
"""Inventory canonical v49 structures without publishing their internal identities.

The canonical candidate JSON is large and intentionally internal.  This module
loads it once for an offline aggregate census, verifies the repeated folder
membership views against one another, and returns only counts, distributions,
and hashes.  It never writes object rows, folder tokens, URLs, or held IDs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


EXPECTED_TOP_LEVEL_KEYS = (
    "appendices",
    "bookmarks",
    "folderTypes",
    "folders",
    "meta",
    "readingNotes",
    "registrationCards",
    "researchDossiers",
    "surfaces",
)
EXPECTED_PAIR_SHA256 = "b2ddbe94f4d569f6b9970246855b535374b7c1a9b8ac047de58899c860bd4573"
EXPECTED_OBJECT_COUNT = 15_923
EXPECTED_PUBLIC_COUNT = 7_995
EXPECTED_HELD_COUNT = 7_928
EXPECTED_FOLDER_COUNT = 185
EXPECTED_MEMBERSHIP_COUNT = 47_982


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pair_digest(pairs: Iterable[tuple[str, str]]) -> tuple[int, str]:
    ordered = sorted(pairs)
    payload = "".join(f"{container_id}\t{object_id}\n" for container_id, object_id in ordered).encode("utf-8")
    return len(ordered), hashlib.sha256(payload).hexdigest()


def load_eligibility(ledger_path: Path) -> tuple[set[str], set[str]]:
    public_ids: set[str] = set()
    held_ids: set[str] = set()
    with ledger_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "surface_id_exact" not in reader.fieldnames or "research_disposition" not in reader.fieldnames:
            raise ValueError("eligibility ledger schema is invalid")
        for row in reader:
            object_id = row["surface_id_exact"]
            disposition = row["research_disposition"]
            if disposition == "eligible":
                public_ids.add(object_id)
            elif disposition == "held":
                held_ids.add(object_id)
            else:
                raise ValueError("eligibility ledger contains an unclassified record")
    if len(public_ids) != EXPECTED_PUBLIC_COUNT or len(held_ids) != EXPECTED_HELD_COUNT or public_ids & held_ids:
        raise ValueError("eligibility ledger does not reconcile")
    return public_ids, held_ids


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


class _TopLevelJsonStream:
    """Incrementally decode one minified top-level JSON object.

    The canonical candidate file contains large arrays.  ``json.load`` expands
    the 190 MB payload to more than 2 GB of Python objects, while this reader
    retains only the current array item and the bounded aggregate indexes.
    """

    def __init__(self, path: Path, *, chunk_size: int = 1024 * 1024) -> None:
        self._handle = path.open("r", encoding="utf-8")
        self._chunk_size = chunk_size
        self._buffer = ""
        self._position = 0
        self._eof = False
        self._decoder = json.JSONDecoder()

    def close(self) -> None:
        self._handle.close()

    def _compact(self) -> None:
        if self._position > self._chunk_size:
            self._buffer = self._buffer[self._position:]
            self._position = 0

    def _fill(self) -> bool:
        if self._eof:
            return False
        chunk = self._handle.read(self._chunk_size)
        if not chunk:
            self._eof = True
            return False
        self._buffer += chunk
        return True

    def _skip_space(self) -> None:
        while True:
            while self._position < len(self._buffer) and self._buffer[self._position].isspace():
                self._position += 1
            if self._position < len(self._buffer) or not self._fill():
                self._compact()
                return

    def _peek(self) -> str:
        self._skip_space()
        while self._position >= len(self._buffer):
            if not self._fill():
                raise ValueError("candidate JSON ended unexpectedly")
            self._skip_space()
        return self._buffer[self._position]

    def _take(self, expected: str) -> None:
        actual = self._peek()
        if actual != expected:
            raise ValueError(f"candidate JSON expected {expected!r}, found {actual!r}")
        self._position += 1
        self._compact()

    def _decode(self) -> Any:
        self._skip_space()
        while True:
            try:
                value, end = self._decoder.raw_decode(self._buffer, self._position)
            except json.JSONDecodeError:
                if not self._fill():
                    raise ValueError("candidate JSON contains an incomplete or invalid value")
                continue
            self._position = end
            self._compact()
            return value

    def _array_items(self) -> Iterable[Any]:
        self._take("[")
        if self._peek() == "]":
            self._take("]")
            return
        while True:
            yield self._decode()
            delimiter = self._peek()
            if delimiter == ",":
                self._take(",")
                continue
            if delimiter == "]":
                self._take("]")
                return
            raise ValueError("candidate JSON array has an invalid delimiter")

    def entries(self) -> Iterable[tuple[str, bool, Any]]:
        self._take("{")
        if self._peek() == "}":
            self._take("}")
            return
        while True:
            key = self._decode()
            if not isinstance(key, str):
                raise ValueError("candidate JSON top-level key is not text")
            self._take(":")
            if self._peek() == "[":
                yield key, True, self._array_items()
            else:
                yield key, False, self._decode()
            delimiter = self._peek()
            if delimiter == ",":
                self._take(",")
                continue
            if delimiter == "}":
                self._take("}")
                self._skip_space()
                if self._position < len(self._buffer) or self._fill():
                    self._skip_space()
                    if self._position < len(self._buffer):
                        raise ValueError("candidate JSON has trailing content")
                return
            raise ValueError("candidate JSON object has an invalid delimiter")


def analyze(
    *,
    candidate_path: Path,
    ledger_path: Path,
) -> dict[str, Any]:
    """Return the aggregate inventory using bounded-memory streaming decode."""

    public_ids, held_ids = load_eligibility(ledger_path)
    seen_keys: set[str] = set()
    top_counts: Counter[str] = Counter()
    surface_ids: set[str] = set()
    folder_ids: set[str] = set()
    folder_pairs: list[tuple[str, str]] = []
    surface_pairs: list[tuple[str, str]] = []
    card_pairs: list[tuple[str, str]] = []
    dossier_pairs: list[tuple[str, str]] = []
    folder_type_counts: Counter[str] = Counter()
    related_directed: set[tuple[str, str]] = set()
    related_self = 0
    dossier_page_types: Counter[str] = Counter()
    dossier_page_count = 0
    dossier_multi_page_count = 0
    dossier_cross_anchor_pages = 0
    trace_tree_counts: Counter[str] = Counter()
    trace_branch_ids: set[str] = set()
    trace_branch_memberships = 0
    public_trace_tree_memberships = 0
    held_trace_tree_memberships = 0
    public_trace_branch_memberships = 0
    held_trace_branch_memberships = 0
    compound_child_refs = 0

    stream = _TopLevelJsonStream(candidate_path)
    try:
        for key, is_array, value in stream.entries():
            if key in seen_keys:
                raise ValueError("candidate JSON repeats a top-level key")
            seen_keys.add(key)
            if key == "meta":
                if is_array or not isinstance(value, dict):
                    raise ValueError("candidate meta must be an object")
                continue
            if not is_array:
                raise ValueError(f"candidate top-level structure {key!r} must be an array")
            for raw_item in value:
                top_counts[key] += 1
                item = _require_mapping(raw_item, key)
                if key == "folders":
                    folder_id = str(item.get("folderId", ""))
                    folder_ids.add(folder_id)
                    folder_type_counts[str(item.get("type", ""))] += 1
                    for object_id in _require_list(item.get("surfaceIds"), "folder surface IDs"):
                        folder_pairs.append((folder_id, str(object_id)))
                    for related_value in _require_list(item.get("relatedFolderIds"), "related folder IDs"):
                        related_id = str(related_value)
                        related_self += int(related_id == folder_id)
                        related_directed.add((folder_id, related_id))
                elif key == "surfaces":
                    object_id = str(item.get("surfaceId", ""))
                    surface_ids.add(object_id)
                    for reference_value in _require_list(item.get("folders"), "surface folders"):
                        reference = _require_mapping(reference_value, "surface folder reference")
                        surface_pairs.append((str(reference.get("folderId", "")), object_id))
                    trace = _require_mapping(item.get("trace"), "surface trace")
                    tree_id = str(trace.get("treeId", ""))
                    if tree_id:
                        trace_tree_counts[tree_id] += 1
                        if object_id in public_ids:
                            public_trace_tree_memberships += 1
                        elif object_id in held_ids:
                            held_trace_tree_memberships += 1
                    branches = [str(entry) for entry in _require_list(trace.get("branchIds"), "trace branch IDs")]
                    trace_branch_ids.update(branches)
                    trace_branch_memberships += len(branches)
                    if object_id in public_ids:
                        public_trace_branch_memberships += len(branches)
                    elif object_id in held_ids:
                        held_trace_branch_memberships += len(branches)
                    children = item.get("compoundChildren", [])
                    if children is not None:
                        compound_child_refs += len(_require_list(children, "compound children"))
                elif key == "registrationCards":
                    folder_id = str(item.get("folderId", ""))
                    for page_value in _require_list(item.get("memberPages"), "registration card member pages"):
                        page = _require_mapping(page_value, "registration card member page")
                        card_pairs.append((folder_id, str(page.get("surfaceId", ""))))
                elif key == "researchDossiers":
                    object_id = str(item.get("anchorSurfaceId", ""))
                    for folder_id in _require_list(item.get("folderIds"), "dossier folder IDs"):
                        dossier_pairs.append((str(folder_id), object_id))
                    pages = _require_list(item.get("pageSequence"), "dossier page sequence")
                    dossier_page_count += len(pages)
                    dossier_multi_page_count += int(len(pages) > 1)
                    for page_value in pages:
                        page = _require_mapping(page_value, "dossier page")
                        dossier_page_types[str(page.get("pageType", ""))] += 1
                        page_object_id = str(page.get("surfaceId", ""))
                        dossier_cross_anchor_pages += int(bool(page_object_id) and page_object_id != object_id)
                elif key not in {"folderTypes", "readingNotes", "appendices", "bookmarks"}:
                    raise ValueError(f"unexpected candidate top-level structure: {key}")
    finally:
        stream.close()

    if tuple(sorted(seen_keys)) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("candidate payload top-level structures changed")
    if len(surface_ids) != EXPECTED_OBJECT_COUNT or surface_ids != public_ids | held_ids:
        raise ValueError("candidate surfaces and authoritative eligibility ledger differ")
    if len(folder_ids) != EXPECTED_FOLDER_COUNT or "" in folder_ids:
        raise ValueError("candidate folder identities are invalid")

    representation_receipts: dict[str, dict[str, Any]] = {}
    for name, pairs in (
        ("folder.surfaceIds", folder_pairs),
        ("surface.folders", surface_pairs),
        ("registrationCard.memberPages", card_pairs),
        ("researchDossier.folderIds", dossier_pairs),
    ):
        count, digest = pair_digest(pairs)
        if count != EXPECTED_MEMBERSHIP_COUNT or digest != EXPECTED_PAIR_SHA256:
            raise ValueError(f"candidate membership representation differs: {name}")
        representation_receipts[name] = {"membershipCount": count, "pairSha256": digest}

    related_dangling = sum(right not in folder_ids for _, right in related_directed)
    reciprocal_missing = sum((right, left) not in related_directed for left, right in related_directed)
    return {
        "schemaVersion": "trace-exploration-source-inventory/v1",
        "candidatePayloadSha256": sha256_path(candidate_path),
        "eligibilityLedgerSha256": sha256_path(ledger_path),
        "population": {
            "allObjects": len(surface_ids),
            "publicObjects": len(public_ids),
            "heldObjects": len(held_ids),
        },
        "topLevelStructures": {
            "appendices": top_counts["appendices"],
            "bookmarks": top_counts["bookmarks"],
            "folderTypes": top_counts["folderTypes"],
            "folders": top_counts["folders"],
            "readingNotes": top_counts["readingNotes"],
            "registrationCards": top_counts["registrationCards"],
            "researchDossiers": top_counts["researchDossiers"],
            "surfaces": top_counts["surfaces"],
        },
        "folderStructures": {
            "folderTypeContainerCounts": dict(sorted(folder_type_counts.items())),
            "membershipCount": len(folder_pairs),
            "membershipPairSha256": EXPECTED_PAIR_SHA256,
            "duplicateRepresentationIntegrity": representation_receipts,
            "relatedFolderDirectedReferences": len(related_directed),
            "relatedFolderUndirectedEdges": len(related_directed) // 2,
            "relatedFolderSelfReferences": related_self,
            "relatedFolderDanglingReferences": related_dangling,
            "relatedFolderMissingReciprocals": reciprocal_missing,
        },
        "dossierStructures": {
            "pageCount": dossier_page_count,
            "multiPageDossierCount": dossier_multi_page_count,
            "crossAnchorPageReferenceCount": dossier_cross_anchor_pages,
            "pageTypeCounts": dict(sorted(dossier_page_types.items())),
        },
        "legacyTraceStructures": {
            "treeCount": len(trace_tree_counts),
            "treeMembershipCount": sum(trace_tree_counts.values()),
            "publicTreeMembershipCount": public_trace_tree_memberships,
            "heldTreeMembershipCount": held_trace_tree_memberships,
            "branchCount": len(trace_branch_ids),
            "branchMembershipCount": trace_branch_memberships,
            "publicBranchMembershipCount": public_trace_branch_memberships,
            "heldBranchMembershipCount": held_trace_branch_memberships,
        },
        "compoundChildReferenceCount": compound_child_refs,
        "safety": {
            "rawObjectRowsEmitted": 0,
            "rawFolderIdsEmitted": 0,
            "heldObjectIdsEmitted": 0,
            "urlsEmitted": 0,
        },
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=root / "generated/public_surfaces_prefreeze_candidate_v48.json")
    parser.add_argument("--ledger", type=Path, default=root / "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv")
    parser.add_argument("--output", type=str, default="-")
    args = parser.parse_args()
    result = analyze(candidate_path=args.candidate.resolve(), ledger_path=args.ledger.resolve())
    payload = canonical_json_bytes(result)
    if args.output == "-":
        print(payload.decode("utf-8"), end="")
    else:
        Path(args.output).write_bytes(payload)


if __name__ == "__main__":
    main()
