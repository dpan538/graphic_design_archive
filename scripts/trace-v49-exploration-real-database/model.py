"""Normative TRACE v49 Round 16 real-database Exploration model.

This module binds the immutable Round 14 association assessments and Round 15
composition engine to the frozen v49 public database boundary.  It performs no
similarity search, clustering, model inference, or database mutation.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import sqlite3
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


SOURCE_SHA = "aca7b9627ca42776d966f96ce4bd03db1f296ae3"
API_VERSION = "trace-exploration/v1"
READ_MODEL_VERSION = "trace-exploration-real-read-model-v1"
STATE_VERSION = "trace-exploration-state-v1"
TREE_VERSION = "trace-plain-text-tree-v1"
EXPORT_VERSION = "trace-exploration-portrait-png-v1"
PROJECTION_VERSION = "trace-exploration-neutral-projection-v1"
MAXIMUM_NODES = 40
MAXIMUM_EXPANSION_DEPTH = 2
DATABASE_PATH = "data/prefreeze_candidate_v48.sqlite"
FREEZE_PATH = "database/FREEZE_V49.json"
ELIGIBILITY_LEDGER_PATH = "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"
CONTEXT_MANIFEST_PATH = "frontend/generated/trace-context-v1/manifest.json"
SPACETIME_MANIFEST_PATH = "frontend/generated/trace-spacetime-v1/manifest.json"
SEARCH_MANIFEST_PATH = "frontend/generated/search-v49/manifest.json"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_round15_module(repo: Path):
    path = repo / "scripts/trace-v49-exploration-composition-engine/model.py"
    spec = importlib.util.spec_from_file_location("trace_round15_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("ROUND15_ENGINE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def database_identity(repo: Path) -> dict[str, Any]:
    freeze = read_json(repo / FREEZE_PATH)
    context = read_json(repo / CONTEXT_MANIFEST_PATH)
    spacetime = read_json(repo / SPACETIME_MANIFEST_PATH)
    search = read_json(repo / SEARCH_MANIFEST_PATH)
    database_sha = file_hash(repo / DATABASE_PATH)
    freeze_sha = file_hash(repo / FREEZE_PATH)
    if database_sha != "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e":
        raise ValueError("DATABASE_CONTENT_HASH_MISMATCH")
    if freeze_sha != "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e":
        raise ValueError("DATABASE_FREEZE_HASH_MISMATCH")
    releases = {
        (search["release_id"], search["release_manifest_sha256"]),
        (context["sourceRelease"]["id"], context["sourceRelease"]["manifestSha256"]),
        (spacetime["sourceRelease"]["researchReleaseId"], spacetime["sourceRelease"]["researchManifestSha256"]),
    }
    if len(releases) != 1:
        raise ValueError("CROSS_COMPONENT_DATABASE_VERSION_MISMATCH")
    release_id, release_manifest = releases.pop()
    public_counts = {
        search["document_count"],
        context["counts"]["publicObjectCount"],
        spacetime["counts"]["publicObjects"],
    }
    held_counts = {
        search["held_document_count"],
        context["counts"]["heldExcluded"]["objectCount"],
        spacetime["counts"]["heldObjects"],
    }
    if len(public_counts) != 1 or len(held_counts) != 1:
        raise ValueError("CROSS_COMPONENT_COUNT_MISMATCH")
    return {
        "database_snapshot_id": f"{release_id}:{database_sha}",
        "database_schema_version": int(freeze["version"]),
        "database_content_sha256": database_sha,
        "database_freeze_sha256": freeze_sha,
        "research_release_id": release_id,
        "research_manifest_sha256": release_manifest,
        "public_object_count": public_counts.pop(),
        "held_object_count": held_counts.pop(),
        "search_projection_sha256": search["index_sha256"],
        "context_projection_id": context["projectionId"],
        "context_projection_sha256": context["projectionSha256"],
        "spacetime_projection_id": spacetime["projectionId"],
        "spacetime_projection_sha256": spacetime["projectionSha256"],
        "source_sha": SOURCE_SHA,
    }


def eligible_ids(repo: Path) -> set[str]:
    rows = read_tsv(repo / ELIGIBILITY_LEDGER_PATH)
    values = {row["surface_id_exact"] for row in rows if row["research_disposition"] == "eligible"}
    if len(values) != 7995:
        raise ValueError("PUBLIC_ELIGIBILITY_COUNT_MISMATCH")
    return values


def _text_match(haystack: Iterable[str], needle: str) -> bool:
    token = re.sub(r"\s+", " ", needle.casefold()).strip()
    return token in re.sub(r"\s+", " ", " ".join(haystack).casefold())


def _source_record(row: dict[str, str], attested_form: str) -> dict[str, Any]:
    return {
        "attestation_ref": row["evidence_id"],
        "source_id": row["source_id"],
        "title": row["title"],
        "creator": row["creator"],
        "year": row["year"],
        "locator": row["locator"],
        "stable_url": row["stable_url"],
        "attested_form": attested_form,
        "evidence_channel": row["evidence_channel"],
    }


def _academic_record(row: dict[str, str]) -> dict[str, Any]:
    return {
        "source_id": row["source_id"],
        "authors": row.get("authors") or row.get("creator", ""),
        "year": row["year"],
        "title": row["title"],
        "venue": row.get("venue", ""),
        "doi_or_identifier": row.get("doi_or_identifier") or row.get("doi", ""),
        "stable_url": row["stable_url"],
        "support_scope": row.get("scope_note") or row.get("association_context", ""),
        "peer_reviewed": row.get("peer_reviewed", "true") == "true",
    }


def _source_year(value: str) -> int:
    match = re.search(r"(?:18|19|20)\d{2}", value)
    return int(match.group()) if match else 9999


def build_vocabulary(
    repo: Path,
    active_assessments: list[dict[str, Any]],
    evidence_rows: list[dict[str, str]],
    eligible: set[str],
    context_by_object: dict[str, dict[str, Any]],
    spacetime_by_object: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    additions = read_tsv(repo / "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv")
    addition_by_id = {row["source_id"]: row for row in additions}
    scholarly_rows = read_tsv(repo / "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv")
    scholarly_by_id = {row["source_id"]: row for row in scholarly_rows}
    gap_rows = read_tsv(repo / "docs/research/trace-v49-exploration-composition-review-round1/06_VOCABULARY_GAP_EVIDENCE.tsv")
    gap_sources = {row["source_id"]: row for row in scholarly_rows}
    assessments_by_term: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assessment in active_assessments:
        assessments_by_term[assessment["nodeA"]].append(assessment)
        assessments_by_term[assessment["nodeB"]].append(assessment)

    addition_term_map: dict[str, list[str]] = defaultdict(list)
    for row in additions:
        for term in row["supported_terms"].split(";"):
            addition_term_map[term].append(row["source_id"])

    attestation_overrides: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for term in ("advertising", "consumer culture", "design education"):
        for source_id in addition_term_map[term]:
            row = addition_by_id[source_id]
            attestation_overrides[term].append({
                "attestation_ref": f"{source_id}:attestation:{term.replace(' ', '-')}",
                "source_id": source_id,
                "title": row["title"],
                "creator": row["authors"],
                "year": row["year"],
                "locator": "title, abstract, or indexed chapter description",
                "stable_url": row["stable_url"],
                "attested_form": term,
                "evidence_channel": "EXTERNAL_SCHOLARSHIP",
            })
    for term, phrase in (
        ("cultural negotiation", "cultural negotiation"),
        ("production site", "production site"),
        ("supply chain", "supply chain"),
    ):
        for row in gap_rows:
            if _text_match((row.get("exact_attested_terms", ""), row.get("bounded_context", ""), row.get("additional_roles", "")), phrase):
                source = gap_sources[row["source_id"]]
                attestation_overrides[term].append({
                    "attestation_ref": row["evidence_id"],
                    "source_id": row["source_id"],
                    "title": source["title"],
                    "creator": source["authors"],
                    "year": source["year"],
                    "locator": row.get("locator", "stored vocabulary-gap evidence"),
                    "stable_url": source["stable_url"],
                    "attested_form": term,
                    "evidence_channel": "EXTERNAL_SCHOLARSHIP",
                })

    db = sqlite3.connect(repo / DATABASE_PATH)
    db.row_factory = sqlite3.Row
    fields = "title,creator,description,source_notes,source_subjects,medium,object_type"
    vocabulary: list[dict[str, Any]] = []
    term_to_id: dict[str, str] = {}
    for term in sorted(assessments_by_term):
        assessment_ids = {item["assessmentId"] for item in assessments_by_term[term]}
        candidate_evidence = [row for row in evidence_rows if row["assessment_id"] in assessment_ids]
        attestations = [
            _source_record(row, term)
            for row in candidate_evidence
            if _text_match((row["title"], row["association_context"], row["locator"]), term)
        ]
        attestations.extend(attestation_overrides[term])
        seen_attestation: set[str] = set()
        attestations = [item for item in attestations if not (item["attestation_ref"] in seen_attestation or seen_attestation.add(item["attestation_ref"]))]

        academic_ids = {
            row["source_id"] for row in candidate_evidence
            if row["source_id"].startswith("COMP-SRC-") and row["source_id"] in scholarly_by_id
        }
        academic_ids.update(addition_term_map[term])
        academic_support = [
            _academic_record(scholarly_by_id[source_id] if source_id in scholarly_by_id else addition_by_id[source_id])
            for source_id in sorted(academic_ids)
        ]
        if not attestations:
            raise ValueError(f"UNATTESTED_USER_VISIBLE_VOCABULARY:{term}")
        if not academic_support:
            raise ValueError(f"ACADEMICALLY_UNSUPPORTED_USER_VISIBLE_VOCABULARY:{term}")

        object_refs: list[dict[str, Any]] = []
        rows = db.execute(
            f"SELECT surface_id,title,{fields} FROM objects ORDER BY surface_id"
        ).fetchall()
        for row in rows:
            surface_id = row["surface_id"]
            if surface_id not in eligible:
                continue
            if not _text_match(tuple(str(row[key] or "") for key in row.keys() if key != "surface_id"), term):
                continue
            object_refs.append({"surface_id": surface_id, "title": row["title"]})
            if len(object_refs) == 5:
                break
        context_refs = sorted({
            representation["id"]
            for item in object_refs
            for representation in context_by_object[item["surface_id"]]["representations"]
        })
        spacetime_refs = sorted({
            geography_id
            for item in object_refs
            for geography_id in spacetime_by_object[item["surface_id"]]["geographyIds"]
        })
        vocabulary_id = stable_id("TRV", term)
        term_to_id[term] = vocabulary_id
        relevant_year = min(
            [_source_year(item["year"]) for item in attestations if _source_year(item["year"]) != 9999],
            default=None,
        )
        vocabulary.append({
            "vocabulary_id": vocabulary_id,
            "canonical_label": term,
            "attested_forms": sorted({item["attested_form"] for item in attestations}),
            "attested_form": term,
            "normalised_form": term.casefold(),
            "language": "en",
            "scope_note": "Evidence-bounded historical or design-historical vocabulary; its visibility does not assert a typed relation.",
            "ambiguity_note": "Interpret within the cited historical scope and source record; no universal definition is implied.",
            "source_attestations": attestations,
            "source_attestation_refs": [item["attestation_ref"] for item in attestations],
            "academic_support": academic_support,
            "academic_support_refs": [item["source_id"] for item in academic_support],
            "first_or_relevant_attested_date": relevant_year,
            "archive_object_refs": object_refs,
            "context_refs": context_refs,
            "spacetime_refs": spacetime_refs,
            "activation_status": "ACTIVE_USER_VISIBLE",
            "provenance_chain_complete": True,
        })
    db.close()
    return vocabulary, term_to_id


def build_associations(
    active_assessments: list[dict[str, Any]],
    failed_assessments: list[dict[str, Any]],
    evidence_rows: list[dict[str, str]],
    term_to_id: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    def record(item: dict[str, Any]) -> dict[str, Any]:
        rows = [row for row in evidence_rows if row["assessment_id"] == item["assessmentId"]]
        return {
            "association_id": item["assessmentId"],
            "endpoint_vocabulary_ids": [term_to_id[item["nodeA"]], term_to_id[item["nodeB"]]] if item["nodeA"] in term_to_id and item["nodeB"] in term_to_id else [],
            "endpoint_labels": [item["nodeA"], item["nodeB"]],
            "support_status": item["evidenceStatus"],
            "strength": item["associationStrength"],
            "confidence": item["evidenceConfidence"],
            "mandatory_dimension_results": {key: item["rubricDimensions"][key] for key in ("D1", "D5", "D7")},
            "provenance_refs": [row["evidence_id"] for row in rows],
            "source_refs": sorted({row["source_id"] for row in rows}),
            "source_urls": sorted({row["stable_url"] for row in rows}),
            "qualification_version": item["methodVersion"],
            "qualification": item["qualification"],
            "active_for_proximity": item["activeForProximity"],
            "hard_negative": item["hardNegative"],
            "generic_association_only": True,
            "association_accessible_description": f"{item['nodeA']} is available to explore with {item['nodeB']} as a qualified generic association.",
            "explicit_non_claims": ["causation", "influence", "chronology", "hierarchy", "direction", "equivalence"],
        }
    return [record(item) for item in active_assessments], [record(item) for item in failed_assessments]


def load_projection_records(repo: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    context_document = read_json(repo / "frontend/generated/trace-context-v1/records.json")
    spacetime_document = read_json(repo / "frontend/generated/trace-spacetime-v1/record-index.json")
    geography_document = read_json(repo / "frontend/generated/trace-spacetime-v1/geography-registry.json")
    terms_document = read_json(repo / "frontend/generated/trace-context-v1/terms.json")
    context_by_object = {row["selectedRecord"]["surfaceId"]: row for row in context_document["records"]}
    spacetime_by_object = {row["objectId"]: row for row in spacetime_document["records"]}
    geography_by_id = {row["geographyId"]: row for row in geography_document["entries"]}
    context_term_by_key = {f"{row['kind']}|{row['label']}": row for row in terms_document["terms"]}
    return context_by_object, spacetime_by_object, geography_by_id, context_term_by_key


def select_category_references(
    repo: Path,
    eligible: set[str],
    category_id: str,
    anchor_titles: list[str],
    context_by_object: dict[str, dict[str, Any]],
    spacetime_by_object: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    db = sqlite3.connect(repo / DATABASE_PATH)
    db.row_factory = sqlite3.Row
    archive: list[dict[str, Any]] = []
    for title in anchor_titles:
        rows = db.execute(
            "SELECT r.surface_id,o.title,r.folder_id,r.title folder_title FROM object_folder_refs r JOIN objects o USING(surface_id) WHERE r.folder_type=? AND r.title=? ORDER BY r.surface_id",
            (category_id, title),
        ).fetchall()
        for row in rows:
            if row["surface_id"] not in eligible:
                continue
            archive.append({
                "surface_id": row["surface_id"],
                "title": row["title"],
                "folder_id": row["folder_id"],
                "folder_title": row["folder_title"],
            })
            if len([item for item in archive if item["folder_title"] == title]) >= 4:
                break
    db.close()
    if not archive:
        raise ValueError(f"CATEGORY_WITHOUT_REAL_ARCHIVE_REFERENCE:{category_id}")
    context_refs = sorted({
        representation["id"]
        for item in archive
        for representation in context_by_object[item["surface_id"]]["representations"]
    })
    spacetime_refs = sorted({
        geography_id
        for item in archive
        for geography_id in spacetime_by_object[item["surface_id"]]["geographyIds"]
    })
    if not context_refs or not spacetime_refs:
        raise ValueError(f"CATEGORY_WITHOUT_SHARED_PROJECTION_REFERENCE:{category_id}")
    return {
        "archive_object_refs": archive,
        "context_refs": context_refs,
        "spacetime_refs": spacetime_refs,
    }


def _round15_input(specification: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixtureId": specification["compositionId"],
        "fixtureFamily": "REAL_DATABASE_CATEGORY_COMPOSITION",
        "seedNodeIds": specification["seedNodeIds"],
        "nodeIds": specification["nodeIds"],
        "associationIds": specification["associationIds"],
        "topologyRequest": specification["topologyRequest"],
        "evidenceGapNodeIds": [],
        "qualificationGate": False,
        "navigationReturn": False,
        "synthetic": False,
        "visualSeed": f"round16|{specification['categoryId']}|{specification['compositionId']}",
        "description": specification["description"],
    }


def build_tree(
    composition: dict[str, Any],
    focus_label: str,
    vocabulary_by_label: dict[str, dict[str, Any]],
    association_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    admitted_ids = composition["round15_semantic_image"]["semantic_core"]["admitted_association_ids"]
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for association_id in admitted_ids:
        a, b = association_by_id[association_id]["endpoint_labels"]
        adjacency[a].append((b, association_id))
        adjacency[b].append((a, association_id))
    root = focus_label if focus_label in adjacency else composition["seed_labels"][0]
    nodes = [root]
    tree_edges: list[tuple[str, str, str, int]] = []
    for child, association_id in sorted(adjacency[root]):
        if child not in nodes:
            nodes.append(child)
            tree_edges.append((root, child, association_id, 1))
    # A second level is admitted only when the skip-one endpoints are themselves
    # qualified by a frozen Round 14 association in this composition.
    qualified_pairs = {
        frozenset(association_by_id[item]["endpoint_labels"]): item
        for item in composition["qualified_association_ids"]
    }
    first_level = [child for _, child, _, depth in tree_edges if depth == 1]
    for parent in first_level:
        for child, association_id in sorted(adjacency[parent]):
            if child in nodes or child == root:
                continue
            if frozenset((root, child)) not in qualified_pairs:
                continue
            nodes.append(child)
            tree_edges.append((parent, child, association_id, 2))
    labels = {label: vocabulary_by_label[label]["canonical_label"] for label in nodes}
    children: dict[str, list[str]] = defaultdict(list)
    for parent, child, _, _ in tree_edges:
        children[parent].append(child)

    def lines_for(node: str, prefix: str, ascii_mode: bool) -> list[str]:
        rows: list[str] = []
        values = sorted(children[node])
        for index, child in enumerate(values):
            last = index == len(values) - 1
            connector = ("`-- " if last else "|-- ") if ascii_mode else ("└── " if last else "├── ")
            rows.append(prefix + connector + labels[child])
            extension = ("    " if last else "|   ") if ascii_mode else ("    " if last else "│   ")
            rows.extend(lines_for(child, prefix + extension, ascii_mode))
        return rows

    unicode_text = "\n".join([labels[root], *lines_for(root, "", False)])
    ascii_text = "\n".join([labels[root], *lines_for(root, "", True)])
    tree_associations = [association_id for _, _, association_id, _ in tree_edges]
    semantic_material = {
        "selected_composition_id": composition["composition_id"],
        "root_vocabulary_id": vocabulary_by_label[root]["vocabulary_id"],
        "tree_node_ids": [vocabulary_by_label[label]["vocabulary_id"] for label in nodes],
        "tree_association_ids": tree_associations,
        "composition_semantic_hash": composition["semantic_hash"],
    }
    return {
        "schema_version": TREE_VERSION,
        "plain_text_tree": unicode_text,
        "plain_text_tree_ascii": ascii_text,
        "tree_root_node_id": semantic_material["root_vocabulary_id"],
        "tree_node_ids": semantic_material["tree_node_ids"],
        "tree_association_ids": tree_associations,
        "tree_semantic_hash": canonical_hash(semantic_material),
        "generic_association_only": True,
        "structural_hierarchy_is_historical_claim": False,
    }


def _state_hash(state: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in state.items() if key != "state_hash"})


def _export_manifest(
    state: dict[str, Any],
    tree: dict[str, Any],
    category: dict[str, Any],
    composition: dict[str, Any],
    theme_token_set: str,
    database_snapshot_id: str,
) -> dict[str, Any]:
    dimensions = {"width": 1080, "height": 1620, "padding": 72}
    material = {
        "state_hash": state["state_hash"],
        "semantic_hash": state["semantic_hash"],
        "composition_id": composition["composition_id"],
        "theme_token_set": theme_token_set,
        "dimensions": dimensions,
        "render_version": EXPORT_VERSION,
        "database_snapshot_id": database_snapshot_id,
    }
    presentation_hash = canonical_hash(material)
    export_id = stable_id("TREX", presentation_hash)
    visible = set(state["visible_node_ids"])
    map_nodes = [node for node in composition["nodes"] if node["vocabulary_id"] in visible]
    map_associations = [
        association for association in composition["associations"]
        if set(association["endpoint_vocabulary_ids"]) <= visible
        and association["association_id"] in composition["admitted_association_ids"]
    ]
    return {
        "schema_version": "trace-exploration-export-manifest-v1",
        "export_id": export_id,
        "map_id": state["map_id"],
        "state_hash": state["state_hash"],
        "semantic_hash": state["semantic_hash"],
        "presentation_hash": presentation_hash,
        "selected_composition_id": composition["composition_id"],
        "dimensions": dimensions,
        "export_preset": "portrait_card",
        "theme_token_set": theme_token_set,
        "map_region": {
            "region_id": state["current_region_id"],
            "nodes": map_nodes,
            "associations": map_associations,
            "projection_version": PROJECTION_VERSION,
        },
        "plain_text_tree": tree,
        "vocabulary_ids": tree["tree_node_ids"],
        "association_ids": [association["association_id"] for association in map_associations],
        "provenance_summary": {
            "source_count": len({ref for item in map_associations for ref in item["source_refs"]}),
            "archive_object_reference_count": len(category["archive_object_refs"]),
            "context_reference_count": len(category["context_refs"]),
            "spacetime_reference_count": len(category["spacetime_refs"]),
            "database_snapshot_id": database_snapshot_id,
        },
        "render_version": EXPORT_VERSION,
        "content_type": "image/png",
        "suggested_filename": f"trace-{category['category_id']}-{export_id.split(':')[1][:12]}.png",
        "export_alt_text": f"{category['label']} exploration card. {tree['plain_text_tree_ascii'].replace(chr(10), '; ')}",
    }


def build_read_model(repo: Path) -> dict[str, Any]:
    identity = database_identity(repo)
    eligible = eligible_ids(repo)
    context_by_object, spacetime_by_object, geography_by_id, context_term_by_key = load_projection_records(repo)
    if set(context_by_object) != eligible or set(spacetime_by_object) != eligible:
        raise ValueError("ORPHAN_SHARED_PROJECTION_REFERENCE")
    round15 = load_round15_module(repo)
    frozen = round15.load_frozen_input(repo)
    all_assessments = list(frozen.assessments.values())
    active_assessments = [item for item in all_assessments if item["activeForProximity"]]
    failed_assessments = [item for item in all_assessments if not item["activeForProximity"]]
    evidence_rows = read_tsv(repo / "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv")
    vocabulary, term_to_id = build_vocabulary(
        repo, active_assessments, evidence_rows, eligible, context_by_object, spacetime_by_object,
    )
    vocabulary_by_label = {item["canonical_label"]: item for item in vocabulary}
    vocabulary_by_id = {item["vocabulary_id"]: item for item in vocabulary}
    associations, failed_association_records = build_associations(active_assessments, failed_assessments, evidence_rows, term_to_id)
    association_by_id = {item["association_id"]: item for item in associations}
    registry = read_json(repo / "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json")
    category_order = registry["categoryOrder"]
    if category_order != ["region", "theme", "medium", "movement"]:
        raise ValueError("FOUR_CATEGORY_ORDER_MISMATCH")
    if set(registry["categories"]) != {"region", "theme", "medium", "movement"}:
        raise ValueError("FOUR_CATEGORY_TAXONOMY_MISMATCH")

    specifications = {item["compositionId"]: item for item in registry["compositions"]}
    compositions: dict[str, dict[str, Any]] = {}
    used_associations: set[str] = set()
    for specification in registry["compositions"]:
        image = round15.compose(_round15_input(specification), frozen)
        admitted_ids = image["semantic_core"]["admitted_association_ids"]
        if not admitted_ids:
            raise ValueError(f"NO_EXPORTABLE_COMPOSITION:{specification['compositionId']}")
        used_associations.update(specification["associationIds"])
        nodes = []
        position_by_label = {row["node_id"]: row for row in image["presentation_hints"]["node_positions"]}
        for label in specification["nodeIds"]:
            position = position_by_label[label]
            nodes.append({
                "vocabulary_id": term_to_id[label],
                "canonical_label": label,
                "node_accessible_label": f"{label}, evidence-supported exploration term",
                "projection": {
                    "projection_version": PROJECTION_VERSION,
                    "normalised_x": round(position["x"] / 720, 6),
                    "normalised_y": round(position["y"] / 540, 6),
                    "group_slot": specification["categoryId"],
                    "branch_slot": position["branch_slot"],
                    "layer_slot": 0,
                    "bounding_hint": {"radius": position["node_radius"] / 720},
                },
            })
        composition_associations = [association_by_id[item] for item in specification["associationIds"]]
        composition = {
            "composition_id": specification["compositionId"],
            "category_id": specification["categoryId"],
            "description": specification["description"],
            "entry_evidence": specification["entryEvidence"].split(";"),
            "seed_labels": specification["seedNodeIds"],
            "seed_node_ids": [term_to_id[item] for item in specification["seedNodeIds"]],
            "nodes": nodes,
            "associations": composition_associations,
            "qualified_association_ids": image["semantic_core"]["qualified_association_ids"],
            "admitted_association_ids": admitted_ids,
            "pruned_association_ids": [
                item["assessment_id"] for item in image["composition_core"]["candidate_decisions"]
                if item["decision_state"] == "PRUNED"
            ],
            "topology_type": image["semantic_core"]["topology_type"],
            "semantic_hash": image["semantic_core_hash"],
            "presentation_hash": image["presentation_hash"],
            "round15_semantic_image": image,
            "exportable": True,
            "generic_association_only": True,
        }
        compositions[composition["composition_id"]] = composition
    if used_associations != {item["assessmentId"] for item in active_assessments}:
        raise ValueError("ROUND14_QUALIFIED_ASSOCIATION_COVERAGE_MISMATCH")

    categories: list[dict[str, Any]] = []
    maps: dict[str, dict[str, Any]] = {}
    states: dict[str, dict[str, Any]] = {}
    states_by_hash: dict[str, str] = {}
    transitions: dict[str, str] = {}
    trees: dict[str, dict[str, Any]] = {}
    export_manifests: dict[str, dict[str, Any]] = {}
    state_variant_index: dict[tuple[str, str, str, bool], str] = {}

    for category_id in category_order:
        category_spec = registry["categories"][category_id]
        refs = select_category_references(
            repo, eligible, category_id, category_spec["anchorFolderTitles"], context_by_object, spacetime_by_object,
        )
        comp_ids = category_spec["compositions"]
        category_compositions = [compositions[item] for item in comp_ids]
        map_id = stable_id("TRMAP", f"{identity['database_snapshot_id']}|{category_id}")
        map_regions = []
        all_node_ids: set[str] = set()
        all_association_ids: set[str] = set()
        for index, composition in enumerate(category_compositions):
            node_ids = [item["vocabulary_id"] for item in composition["nodes"]]
            all_node_ids.update(node_ids)
            all_association_ids.update(composition["qualified_association_ids"])
            map_regions.append({
                "region_id": stable_id("TRREG", composition["composition_id"]),
                "category_id": category_id,
                "node_ids": node_ids,
                "association_ids": composition["qualified_association_ids"],
                "composition_ids": [composition["composition_id"]],
                "entry_node_ids": composition["seed_node_ids"],
                "focusable_node_ids": sorted({
                    endpoint
                    for association_id in composition["admitted_association_ids"]
                    for endpoint in association_by_id[association_id]["endpoint_vocabulary_ids"]
                }),
                "context_refs": refs["context_refs"],
                "spacetime_refs": refs["spacetime_refs"],
                "semantic_hash": composition["semantic_hash"],
                "stable_order": index,
            })
        category = {
            "category_id": category_id,
            "label": category_spec["label"],
            "description": category_spec["description"],
            "provenance_refs": category_spec["approvedTaxonomyRefs"],
            "anchor_folder_titles": category_spec["anchorFolderTitles"],
            "eligible_vocabulary_count": len(all_node_ids),
            "qualified_association_count": len(all_association_ids),
            "map_region_count": len(map_regions),
            "exportable_composition_count": len(category_compositions),
            "map_available": True,
            "map_id": map_id,
            **refs,
        }
        categories.append(category)
        maps[map_id] = {
            "map_id": map_id,
            "category_id": category_id,
            "map_regions": map_regions,
            "node_ids": sorted(all_node_ids),
            "association_ids": sorted(all_association_ids),
            "composition_ids": comp_ids,
            "default_focus": category_compositions[0]["seed_node_ids"][0],
            "default_composition_id": comp_ids[0],
            "context_references": refs["context_refs"],
            "spacetime_references": refs["spacetime_refs"],
            "archive_object_references": refs["archive_object_refs"],
            "map_summary": f"{category_spec['label']} map with {len(map_regions)} evidence-bounded regions and {len(all_node_ids)} active terms.",
            "semantic_hash": canonical_hash({
                "category_id": category_id,
                "composition_semantic_hashes": [item["semantic_hash"] for item in category_compositions],
                "archive_object_ids": [item["surface_id"] for item in refs["archive_object_refs"]],
                "database_snapshot_id": identity["database_snapshot_id"],
            }),
        }

        for composition in category_compositions:
            region = next(item for item in map_regions if composition["composition_id"] in item["composition_ids"])
            focus_ids = region["focusable_node_ids"]
            focus_labels = [vocabulary_by_id[item]["canonical_label"] for item in focus_ids]
            for focus_label in focus_labels:
                tree = build_tree(composition, focus_label, vocabulary_by_label, association_by_id)
                trees[f"{composition['composition_id']}|{term_to_id[focus_label]}"] = tree
                admitted_endpoints = {
                    endpoint
                    for association_id in composition["admitted_association_ids"]
                    for endpoint in association_by_id[association_id]["endpoint_vocabulary_ids"]
                }
                neighbour_ids = {
                    endpoint
                    for association_id in composition["admitted_association_ids"]
                    if term_to_id[focus_label] in association_by_id[association_id]["endpoint_vocabulary_ids"]
                    for endpoint in association_by_id[association_id]["endpoint_vocabulary_ids"]
                }
                for expanded in (False, True):
                    visible = sorted(admitted_endpoints if expanded else neighbour_ids | {term_to_id[focus_label]})
                    state_id = stable_id("TRSTATE", f"{map_id}|{composition['composition_id']}|{term_to_id[focus_label]}|{expanded}")
                    state = {
                        "schema_version": STATE_VERSION,
                        "exploration_state_id": state_id,
                        "category_id": category_id,
                        "map_id": map_id,
                        "current_region_id": region["region_id"],
                        "focused_node_id": term_to_id[focus_label],
                        "selected_composition_id": composition["composition_id"],
                        "expanded_node_ids": [term_to_id[focus_label]] if expanded else [],
                        "visible_node_ids": visible,
                        "visible_association_ids": sorted([
                            association_id for association_id in composition["admitted_association_ids"]
                            if set(association_by_id[association_id]["endpoint_vocabulary_ids"]) <= set(visible)
                        ]),
                        "available_actions": [
                            "SELECT_CATEGORY", "FOCUS_NODE", "EXPAND_NODE", "COLLAPSE_NODE",
                            "MOVE_FOCUS", "SELECT_COMPOSITION", "RESET_CATEGORY", "EXPORT_CURRENT_STATE",
                        ],
                        "semantic_hash": composition["semantic_hash"],
                        "presentation_hash": canonical_hash({
                            "projection_version": PROJECTION_VERSION,
                            "focused_node_id": term_to_id[focus_label],
                            "visible_node_ids": visible,
                            "expanded": expanded,
                        }),
                        "database_snapshot_id": identity["database_snapshot_id"],
                        "api_version": API_VERSION,
                        "state_hash": "",
                    }
                    state["state_hash"] = _state_hash(state)
                    states[state_id] = state
                    states_by_hash[state["state_hash"]] = state_id
                    state_variant_index[(map_id, composition["composition_id"], term_to_id[focus_label], expanded)] = state_id
        initial_id = state_variant_index[(map_id, comp_ids[0], category_compositions[0]["seed_node_ids"][0], True)]
        maps[map_id]["initial_state_id"] = initial_id

    for state_id, state in states.items():
        map_item = maps[state["map_id"]]
        composition = compositions[state["selected_composition_id"]]
        region = next(item for item in map_item["map_regions"] if item["region_id"] == state["current_region_id"])
        initial_id = map_item["initial_state_id"]
        def bind(action: str, target: str, target_state_id: str) -> None:
            transitions[f"{state['state_hash']}|{action}|{target}"] = target_state_id
        bind("RESET_CATEGORY", "", initial_id)
        bind("SELECT_CATEGORY", state["category_id"], initial_id)
        bind("EXPORT_CURRENT_STATE", "", state_id)
        for composition_id in map_item["composition_ids"]:
            target_comp = compositions[composition_id]
            target_focus = target_comp["seed_node_ids"][0]
            bind("SELECT_COMPOSITION", composition_id, state_variant_index[(state["map_id"], composition_id, target_focus, True)])
        for target in region["focusable_node_ids"]:
            bind("FOCUS_NODE", target, state_variant_index[(state["map_id"], composition["composition_id"], target, True)])
            bind("MOVE_FOCUS", target, state_variant_index[(state["map_id"], composition["composition_id"], target, True)])
            bind("EXPAND_NODE", target, state_variant_index[(state["map_id"], composition["composition_id"], target, True)])
            bind("COLLAPSE_NODE", target, state_variant_index[(state["map_id"], composition["composition_id"], target, False)])
        tree = trees[f"{composition['composition_id']}|{state['focused_node_id']}"]
        category = next(item for item in categories if item["category_id"] == state["category_id"])
        for theme in ("neutral-v1", "neutral-contrast-v1"):
            manifest = _export_manifest(state, tree, category, composition, theme, identity["database_snapshot_id"])
            export_manifests[f"{state['state_hash']}|{composition['composition_id']}|portrait_card|{theme}"] = manifest

    workflow_specs = [
        ("A", "region", "R16-COMP-REGION-01", "cultural negotiation"),
        ("B", "theme", "R16-COMP-THEME-01", "design diplomacy"),
        ("C", "medium", "R16-COMP-MEDIUM-01", "photography"),
        ("D", "movement", "R16-COMP-MOVEMENT-01", "craft"),
        ("E", "region", "R16-COMP-REGION-02", "supply chain"),
    ]
    workflows = []
    for name, category_id, composition_id, focus_label in workflow_specs:
        category = next(item for item in categories if item["category_id"] == category_id)
        state_id = state_variant_index[(category["map_id"], composition_id, term_to_id[focus_label], True)]
        state = states[state_id]
        key = f"{state['state_hash']}|{composition_id}|portrait_card|neutral-v1"
        workflows.append({
            "workflow_id": name,
            "name": {
                "A": "Regional contact-zone browse",
                "B": "Thematic exhibition browse",
                "C": "Medium photomontage browse",
                "D": "Movement-context Bauhaus browse",
                "E": "Real material-chain stress case",
            }[name],
            "category_id": category_id,
            "map_id": category["map_id"],
            "composition_id": composition_id,
            "focus_node_id": term_to_id[focus_label],
            "state_id": state_id,
            "state_hash": state["state_hash"],
            "export_manifest_key": key,
        })

    capabilities = {
        "schema_version": "trace-exploration-capabilities-v1",
        "api_version": API_VERSION,
        "supported_actions": [
            "SELECT_CATEGORY", "FOCUS_NODE", "EXPAND_NODE", "COLLAPSE_NODE",
            "MOVE_FOCUS", "SELECT_COMPOSITION", "RESET_CATEGORY", "EXPORT_CURRENT_STATE",
        ],
        "supported_export_presets": ["portrait_card"],
        "supported_theme_token_sets": ["neutral-v1", "neutral-contrast-v1"],
        "maximum_nodes": MAXIMUM_NODES,
        "maximum_expansion_depth": MAXIMUM_EXPANSION_DEPTH,
        "plain_text_formats": ["unicode", "ascii"],
        "current_database_snapshot": identity,
        "product_fixture_fallback": False,
        "typescript_is_normative_semantic_engine": False,
    }
    model = {
        "format": READ_MODEL_VERSION,
        "api_version": API_VERSION,
        "source_sha": SOURCE_SHA,
        "database": identity,
        "categories": categories,
        "maps": maps,
        "vocabulary": vocabulary,
        "associations": associations,
        "failed_associations_audit_only": failed_association_records,
        "compositions": compositions,
        "states": states,
        "states_by_hash": states_by_hash,
        "transitions": transitions,
        "trees": trees,
        "export_manifests": export_manifests,
        "workflows": workflows,
        "capabilities": capabilities,
        "source_inventory": {
            "database": DATABASE_PATH,
            "eligibility_ledger": ELIGIBILITY_LEDGER_PATH,
            "search_manifest": SEARCH_MANIFEST_PATH,
            "context_manifest": CONTEXT_MANIFEST_PATH,
            "spacetime_manifest": SPACETIME_MANIFEST_PATH,
            "round14_assessments": "scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json",
            "round14_evidence": "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv",
            "round15_engine": "scripts/trace-v49-exploration-composition-engine/model.py",
            "real_composition_registry": "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json",
            "scholarly_additions": "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv",
        },
    }
    model["read_model_sha256"] = canonical_hash({key: value for key, value in model.items() if key != "read_model_sha256"})
    return model


def initial_map_response(model: dict[str, Any], category_id: str, state_id: str | None = None) -> dict[str, Any]:
    category = next(item for item in model["categories"] if item["category_id"] == category_id)
    map_item = model["maps"][category["map_id"]]
    selected_state_id = state_id or map_item["initial_state_id"]
    state = model["states"][selected_state_id]
    composition = model["compositions"][state["selected_composition_id"]]
    tree = model["trees"][f"{composition['composition_id']}|{state['focused_node_id']}"]
    return {
        "api_version": API_VERSION,
        "database_snapshot_id": model["database"]["database_snapshot_id"],
        "map": map_item,
        "initial_state" if state_id is None else "state": state,
        "regions": map_item["map_regions"],
        "nodes": [item for item in model["vocabulary"] if item["vocabulary_id"] in map_item["node_ids"]],
        "associations": [item for item in model["associations"] if item["association_id"] in map_item["association_ids"]],
        "compositions": [model["compositions"][item] for item in map_item["composition_ids"]],
        "default_focus": map_item["default_focus"],
        "available_actions": state["available_actions"],
        "plain_text_tree": tree,
        "provenance_summary": {
            "archive_object_refs": map_item["archive_object_references"],
            "context_refs": map_item["context_references"],
            "spacetime_refs": map_item["spacetime_references"],
            "database_snapshot_id": model["database"]["database_snapshot_id"],
        },
        "semantic_hash": state["semantic_hash"],
        "state_hash": state["state_hash"],
    }
