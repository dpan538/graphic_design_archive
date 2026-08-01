#!/usr/bin/env python3
"""Build progressive, read-only TRACE visualization assets from frozen v48."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import shutil
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "prefreeze_candidate_v48.sqlite"
CANDIDATE_JSON = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v48.json"
ADJUNCTS = ROOT / "generated" / "prefreeze_candidate_v47_aic_trace_adjuncts.json"
FRONTEND_PAYLOAD = ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json"
OUT = ROOT / "frontend" / "public" / "data" / "trace-v48"
NEIGHBORHOODS = OUT / "neighborhoods"
VERSION = "v48"
EXPECTED_ACTIVE = 15_923
EXPECTED_REVIEW = 4_425
EXPECTED_ADJUNCTS = 11
EXPECTED_DB_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
EXPECTED_CANDIDATE_JSON_SHA256 = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"

BUDGETS = {
    "atlas_bytes": 180_000,
    "atlas_gzip": 45_000,
    "catalog_bytes": 4_500_000,
    "catalog_gzip": 1_100_000,
    "review_bytes": 1_800_000,
    "review_gzip": 500_000,
    "auxiliary_bytes": 100_000,
    "shard_max_bytes": 600_000,
    "shard_p95_bytes": 250_000,
    "atlas_marks": 360,
}

PROVENANCE = {
    "documented_by", "created_by", "part_of_collection", "part_of_series",
    "captured_from_provider", "exposes_source_record", "documents_object",
    "contains_record", "documents", "issued_by", "publishes_collection",
    "maintains_collection", "maintains_collection_or_namespace",
}
TIME_PLACE = {
    "associated_with_place", "dated", "dated_to", "dated_approximately",
    "associated_with_year", "circulated_in", "context_mentions_place",
}


def clean(value: Any, limit: int | None = None) -> str:
    text = " ".join(str(value or "").split())
    if limit is not None and len(text) > limit:
        return text[: max(0, limit - 1)].rstrip() + "…"
    return text


def dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def shard_for(surface_id: str) -> str:
    # 576 stable hash buckets keep p95 local payloads below the mobile budget
    # without creating one file per object.
    value = int(hashlib.sha256(surface_id.encode("utf-8")).hexdigest()[:8], 16) % 576
    return f"{value:03x}"


def medium_group(value: str) -> str:
    text = value.casefold()
    if any(token in text for token in ("photograph", "gelatin silver", "photographic", "photo relief")):
        return "photography"
    if any(token in text for token in ("lithograph", "screenprint", "screen print", "woodcut", "linocut", "etching", "engraving", "print on paper")):
        return "printmaking"
    if "poster" in text:
        return "poster"
    if any(token in text for token in ("book", "magazine", "periodical", "catalog", "pamphlet", "brochure", "publication")):
        return "publication"
    if any(token in text for token in ("digital", "animation", "video", "web")):
        return "digital / moving image"
    if any(token in text for token in ("textile", "fabric", "cloth")):
        return "textile / material"
    return "graphic object / other"


def relation_family(label: str) -> str:
    if label == "influenced_by":
        return "historical_influence"
    if label in PROVENANCE:
        return "source_provenance"
    if label in TIME_PLACE:
        return "time_place"
    return "medium_context"


def href(value: str, fallback: str) -> str:
    value = clean(value)
    return value if value.startswith(("https://", "http://", "/")) else fallback


def percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    index = max(0, min(len(values) - 1, math.ceil(len(values) * ratio) - 1))
    return values[index]


def main() -> None:
    if not DB.is_file() or not CANDIDATE_JSON.is_file() or not ADJUNCTS.is_file() or not FRONTEND_PAYLOAD.is_file():
        raise SystemExit("Frozen v48, adjunct, or frontend route payload is missing")
    database_sha = sha256(DB)
    candidate_json_sha = sha256(CANDIDATE_JSON)
    if database_sha != EXPECTED_DB_SHA256 or candidate_json_sha != EXPECTED_CANDIDATE_JSON_SHA256:
        raise SystemExit(
            "Frozen v48 hash gate failed: "
            f"database={database_sha} candidate_json={candidate_json_sha}"
        )
    if OUT.exists():
        shutil.rmtree(OUT)
    NEIGHBORHOODS.mkdir(parents=True)

    frontend = json.loads(FRONTEND_PAYLOAD.read_text(encoding="utf-8"))
    archive_ids = {clean(row.get("surfaceId")) for row in frontend.get("surfaces") or []}
    adjunct_source = json.loads(ADJUNCTS.read_text(encoding="utf-8"))
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        integrity = clean(conn.execute("pragma integrity_check").fetchone()[0])
        objects = [dict(row) for row in conn.execute(
            """select surface_id,title,date_start,region,medium,source_name,source_url,
                      trace_tree_id,trace_object_node_id,trace_state,trace_tier,
                      authority_state,trace_evidence_url
               from objects where count_eligible=1 order by surface_id"""
        )]
        if integrity != "ok" or len(objects) != EXPECTED_ACTIVE:
            raise SystemExit(f"Frozen database gate failed: integrity={integrity} active={len(objects)}")

        object_by_id = {row["surface_id"]: row for row in objects}
        neighborhoods: dict[str, dict[str, Any]] = {}
        shard_payloads: dict[str, dict[str, Any]] = defaultdict(dict)
        catalog_rows: list[dict[str, Any]] = []
        decade_counts: Counter[int] = Counter()
        region_counts: Counter[str] = Counter()
        source_counts: Counter[str] = Counter()
        medium_counts: Counter[str] = Counter()
        tree_counts: Counter[str] = Counter()
        region_decades: Counter[tuple[str, int]] = Counter()
        tier_counts: Counter[str] = Counter()

        for row in objects:
            sid = clean(row["surface_id"])
            year = int(row["date_start"])
            decade = year // 10 * 10
            region = clean(row["region"])
            source = clean(row["source_name"])
            group = medium_group(clean(row["medium"]))
            archive_href = f"/surfaces/{sid}" if sid in archive_ids else ""
            root_href = archive_href or clean(row["source_url"])
            shard = shard_for(sid)
            catalog_rows.append({
                "id": sid,
                "title": clean(row["title"], 180),
                "year": year,
                "region": region,
                "source": source,
                "mediumGroup": group,
                "tier": clean(row["trace_tier"]),
                "tree": clean(row["trace_tree_id"]),
                "shard": shard,
                "href": root_href,
                "hrefKind": "object" if archive_href else "source",
            })
            neighborhoods[sid] = {
                "object": {
                    "id": sid,
                    "nodeId": clean(row["trace_object_node_id"]),
                    "title": clean(row["title"], 220),
                    "year": year,
                    "region": region,
                    "medium": clean(row["medium"], 200),
                    "mediumGroup": group,
                    "source": source,
                    "sourceUrl": clean(row["source_url"]),
                    "href": root_href,
                    "hrefKind": "object" if archive_href else "source",
                    "tree": clean(row["trace_tree_id"]),
                    "traceState": clean(row["trace_state"]),
                    "traceTier": clean(row["trace_tier"]),
                    "authorityState": clean(row["authority_state"]),
                    "evidenceReturnUrl": clean(row["trace_evidence_url"]),
                    "layer": "active",
                },
                "nodes": {},
                "edges": [],
            }
            decade_counts[decade] += 1
            region_counts[region] += 1
            source_counts[source] += 1
            medium_counts[group] += 1
            tree_counts[clean(row["trace_tree_id"])] += 1
            region_decades[(region, decade)] += 1
            tier_counts[clean(row["trace_tier"])] += 1

        edge_query = """
            select x.surface_id,
                   e.edge_id,e.tree_id,e.branch_id,e.subject_node_id,e.object_node_id,
                   e.edge_label,e.evidence_url,e.evidence_text,e.evidence_field,
                   e.confidence,e.review_state,e.prohibited_inference_check,
                   sn.node_type subject_type,sn.label subject_label,sn.region subject_region,
                   sn.source_url subject_url,sn.evidence_status subject_status,
                   obn.node_type object_type,obn.label object_label,obn.region object_region,
                   obn.source_url object_url,obn.evidence_status object_status
            from object_trace_edges x
            join objects o on o.surface_id=x.surface_id and o.count_eligible=1
            join trace_edges e on e.edge_id=x.edge_id
            left join trace_nodes sn on sn.node_id=e.subject_node_id
            left join trace_nodes obn on obn.node_id=e.object_node_id
            order by x.surface_id,e.edge_id
        """
        relation_counts: Counter[str] = Counter()
        for row in conn.execute(edge_query):
            graph = neighborhoods[clean(row["surface_id"])]
            root_id = graph["object"]["nodeId"]
            evidence_url = clean(row["evidence_url"])
            edge = {
                "id": clean(row["edge_id"]),
                "label": clean(row["edge_label"]),
                "family": relation_family(clean(row["edge_label"])),
                "subject": clean(row["subject_node_id"]),
                "object": clean(row["object_node_id"]),
                "direction": (
                    "outgoing" if clean(row["subject_node_id"]) == root_id
                    else "incoming" if clean(row["object_node_id"]) == root_id
                    else "associated"
                ),
                "branch": clean(row["branch_id"]),
                "evidenceUrl": evidence_url,
                "evidenceText": clean(row["evidence_text"], 200),
                "evidenceField": clean(row["evidence_field"], 100),
                "confidence": clean(row["confidence"]),
                "reviewState": clean(row["review_state"]),
                "inferenceCheck": clean(row["prohibited_inference_check"], 120),
            }
            graph["edges"].append(edge)
            relation_counts[edge["label"]] += 1
            for prefix, node_id in (("subject", edge["subject"]), ("object", edge["object"])):
                if node_id in graph["nodes"]:
                    continue
                is_root = node_id == root_id
                node_href = graph["object"]["href"] if is_root else href(clean(row[f"{prefix}_url"]), evidence_url or graph["object"]["sourceUrl"])
                graph["nodes"][node_id] = {
                    "id": node_id,
                    "type": "object" if is_root else clean(row[f"{prefix}_type"]) or "evidence",
                    "label": graph["object"]["title"] if is_root else clean(row[f"{prefix}_label"], 160) or edge["label"],
                    "region": graph["object"]["region"] if is_root else clean(row[f"{prefix}_region"]),
                    "href": node_href,
                    "evidenceStatus": "active_root" if is_root else clean(row[f"{prefix}_status"]) or edge["reviewState"],
                    "layer": "active",
                }

        for sid, graph in neighborhoods.items():
            graph["nodes"] = sorted(graph["nodes"].values(), key=lambda row: (row["type"], row["label"], row["id"]))
            graph["edges"].sort(key=lambda row: (row["family"], row["label"], row["id"]))
            shard_payloads[shard_for(sid)][sid] = graph

        review = [dict(row) for row in conn.execute(
            """select review_id,surface_id,title,date_start,region,source_name,source_url,
                      authority_state,trace_state,review_route,count_policy
               from authority_review_objects_current order by review_id"""
        )]
        if len(review) != EXPECTED_REVIEW:
            raise SystemExit(f"Expected {EXPECTED_REVIEW} review rows, got {len(review)}")
        review_rows = [{
            "id": clean(row["review_id"]),
            "surfaceId": clean(row["surface_id"]),
            "title": clean(row["title"], 180),
            "year": int(row["date_start"]) if row["date_start"] is not None else None,
            "region": clean(row["region"]),
            "source": clean(row["source_name"]),
            "href": clean(row["source_url"]),
            "authorityState": clean(row["authority_state"]),
            "traceState": clean(row["trace_state"]),
            "reviewRoute": clean(row["review_route"], 140),
            "countPolicy": clean(row["count_policy"], 120),
            "layer": "review",
        } for row in review]

        adjunct_items = adjunct_source.get("items") or []
        if len(adjunct_items) != EXPECTED_ADJUNCTS:
            raise SystemExit(f"Expected {EXPECTED_ADJUNCTS} adjuncts, got {len(adjunct_items)}")
        adjunct_nodes = {clean(row.get("node_id")): row for row in adjunct_source.get("traceNodes") or []}
        auxiliary = []
        for item in adjunct_items:
            trace = item.get("trace") or {}
            ids = set(trace.get("edgeIds") or [])
            edges = []
            nodes: dict[str, dict[str, Any]] = {}
            for raw_edge in adjunct_source.get("traceEdges") or []:
                if raw_edge.get("edge_id") not in ids:
                    continue
                label = clean(raw_edge.get("edge_label"))
                evidence_url = clean(raw_edge.get("evidence_url")) or clean(item.get("sourceUrl"))
                edge = {
                    "id": clean(raw_edge.get("edge_id")), "label": label,
                    "family": relation_family(label),
                    "subject": clean(raw_edge.get("subject_node_id")),
                    "object": clean(raw_edge.get("object_node_id")),
                    "direction": "outgoing",
                    "evidenceUrl": evidence_url,
                    "evidenceText": clean(raw_edge.get("evidence_text"), 240),
                    "evidenceField": clean(raw_edge.get("evidence_field"), 120),
                    "confidence": clean(raw_edge.get("confidence")),
                    "reviewState": clean(raw_edge.get("review_state")),
                    "inferenceCheck": clean(raw_edge.get("prohibited_inference_check"), 160),
                }
                edges.append(edge)
                for node_id in (edge["subject"], edge["object"]):
                    raw_node = adjunct_nodes.get(node_id) or {}
                    nodes[node_id] = {
                        "id": node_id,
                        "type": clean(raw_node.get("node_type")) or "evidence",
                        "label": clean(raw_node.get("label"), 180) or clean(item.get("title"), 180),
                        "region": clean(raw_node.get("region")),
                        "href": href(clean(raw_node.get("source_url")), evidence_url),
                        "evidenceStatus": clean(raw_node.get("evidence_status")) or "accepted_auxiliary",
                        "layer": "auxiliary",
                    }
            auxiliary.append({
                "object": {
                    "id": clean(item.get("adjunctId")),
                    "nodeId": clean(trace.get("objectNodeId")),
                    "title": clean(item.get("title"), 220),
                    "year": int(item.get("dateStart")),
                    "region": clean(item.get("placeText")),
                    "medium": clean(item.get("medium"), 240),
                    "mediumGroup": medium_group(clean(item.get("medium"))),
                    "source": clean(item.get("sourceName")),
                    "sourceUrl": clean(item.get("sourceUrl")),
                    "href": clean(item.get("sourceUrl")),
                    "hrefKind": "source",
                    "tree": clean(trace.get("treeId")),
                    "traceState": "accepted_auxiliary",
                    "traceTier": "auxiliary",
                    "authorityState": "mediated_known",
                    "evidenceReturnUrl": clean(item.get("sourceUrl")),
                    "layer": "auxiliary",
                    "countEligible": False,
                    "influenceState": clean(trace.get("influenceState")),
                },
                "nodes": sorted(nodes.values(), key=lambda row: (row["type"], row["label"])),
                "edges": sorted(edges, key=lambda row: (row["family"], row["label"])),
            })

        all_decades = sorted(decade_counts)
        top_regions = [name for name, _ in region_counts.most_common(14)]
        other_label = "Other regions"
        other_regions = sorted(name for name in region_counts if name not in top_regions)
        atlas_regions = top_regions + [other_label]
        matrix = []
        for region in atlas_regions:
            counts = []
            for decade in all_decades:
                value = (
                    region_decades[(region, decade)] if region != other_label
                    else sum(count for (name, year), count in region_decades.items() if year == decade and name not in top_regions)
                )
                counts.append(value)
            matrix.append({
                "region": region,
                "members": [region] if region != other_label else other_regions,
                "total": region_counts[region] if region != other_label else sum(count for name, count in region_counts.items() if name not in top_regions),
                "counts": counts,
            })

        trace_nodes = int(conn.execute("select count(*) from trace_nodes").fetchone()[0])
        trace_edges = int(conn.execute("select count(*) from trace_edges").fetchone()[0])
        influence = int(conn.execute("select count(*) from trace_edges where edge_label='influenced_by'").fetchone()[0])
        atlas_marks = len(matrix) * len(all_decades)
        atlas = {
            "version": VERSION,
            "status": "candidate_freeze_not_official_release",
            "generatedFrom": "data/prefreeze_candidate_v48.sqlite",
            "policy": {
                "activeDefault": True,
                "auxiliaryCountEligible": False,
                "reviewMixedWithActive": False,
                "influenceInferred": False,
                "mediumGroupsAreDisplayFiltersOnly": True,
            },
            "counts": {
                "activeObjects": len(objects), "traceNodes": trace_nodes,
                "traceEdges": trace_edges, "activeTrees": len(tree_counts),
                "sourceVerified": tier_counts["source_verified"],
                "metadataSupported": tier_counts["metadata_supported"],
                "reviewObjects": len(review_rows), "auxiliaryObjects": len(auxiliary),
                "influenceEdges": influence,
            },
            "decades": all_decades,
            "decadeTotals": [decade_counts[value] for value in all_decades],
            "regionMatrix": matrix,
            "atlasMarks": atlas_marks,
            "topSources": [{"name": name, "count": count} for name, count in source_counts.most_common(20)],
            "mediumGroups": [{"name": name, "count": count} for name, count in medium_counts.most_common()],
            "relationTypes": [{"label": label, "family": relation_family(label), "count": count} for label, count in relation_counts.most_common()],
            "treeCounts": [{"tree": name, "count": count} for name, count in tree_counts.most_common()],
            "assets": {
                "catalog": "/data/trace-v48/catalog.json",
                "review": "/data/trace-v48/review-catalog.json",
                "auxiliary": "/data/trace-v48/auxiliary.json",
                "neighborhoodBase": "/data/trace-v48/neighborhoods/",
            },
        }
    finally:
        conn.close()

    def compact(rows: list[dict[str, Any]], fields: list[str], dictionary_fields: list[str]) -> dict[str, Any]:
        dictionaries: dict[str, list[str]] = {}
        indexes: dict[str, dict[str, int]] = {}
        for field in dictionary_fields:
            values = sorted({clean(row.get(field)) for row in rows})
            dictionaries[field] = values
            indexes[field] = {value: index for index, value in enumerate(values)}
        items = []
        for row in rows:
            items.append([
                indexes[field][clean(row.get(field))] if field in indexes else row.get(field)
                for field in fields
            ])
        return {"schema": fields, "dictionaries": dictionaries, "items": items}

    catalog = compact(
        catalog_rows,
        ["id", "title", "year", "region", "source", "mediumGroup", "tier", "tree", "shard", "href", "hrefKind"],
        ["region", "source", "mediumGroup", "tier", "tree", "hrefKind"],
    )
    review_catalog = compact(
        review_rows,
        ["id", "surfaceId", "title", "year", "region", "source", "href", "authorityState", "traceState", "reviewRoute", "countPolicy", "layer"],
        ["region", "source", "authorityState", "traceState", "reviewRoute", "countPolicy", "layer"],
    )
    dump(OUT / "atlas.json", atlas)
    dump(OUT / "catalog.json", {"version": VERSION, "layer": "active", **catalog})
    dump(OUT / "review-catalog.json", {"version": VERSION, "layer": "review", **review_catalog})
    dump(OUT / "auxiliary.json", {"version": VERSION, "layer": "auxiliary", "countEligible": False, "items": auxiliary})
    for shard in (f"{value:03x}" for value in range(576)):
        dump(NEIGHBORHOODS / f"{shard}.json", {"version": VERSION, "shard": shard, "objects": shard_payloads.get(shard, {})})

    asset_paths = sorted(path for path in OUT.rglob("*.json") if path.name != "manifest.json")
    assets = []
    for path in asset_paths:
        raw = path.read_bytes()
        assets.append({
            "path": str(path.relative_to(OUT)),
            "bytes": len(raw),
            "gzipBytes": len(gzip.compress(raw, compresslevel=9)),
            "sha256": sha256(path),
        })
    by_path = {row["path"]: row for row in assets}
    shard_sizes = [row["bytes"] for row in assets if row["path"].startswith("neighborhoods/")]
    performance = {
        "atlasBytes": by_path["atlas.json"]["bytes"],
        "atlasGzipBytes": by_path["atlas.json"]["gzipBytes"],
        "catalogBytes": by_path["catalog.json"]["bytes"],
        "catalogGzipBytes": by_path["catalog.json"]["gzipBytes"],
        "reviewBytes": by_path["review-catalog.json"]["bytes"],
        "reviewGzipBytes": by_path["review-catalog.json"]["gzipBytes"],
        "auxiliaryBytes": by_path["auxiliary.json"]["bytes"],
        "neighborhoodShardMaxBytes": max(shard_sizes),
        "neighborhoodShardP95Bytes": percentile(shard_sizes, 0.95),
        "atlasMarks": atlas["atlasMarks"],
        "runtimeVisualizationDependenciesAdded": 0,
    }
    failures = []
    comparisons = {
        "atlasBytes": "atlas_bytes", "atlasGzipBytes": "atlas_gzip",
        "catalogBytes": "catalog_bytes", "catalogGzipBytes": "catalog_gzip",
        "reviewBytes": "review_bytes", "reviewGzipBytes": "review_gzip",
        "auxiliaryBytes": "auxiliary_bytes",
        "neighborhoodShardMaxBytes": "shard_max_bytes",
        "neighborhoodShardP95Bytes": "shard_p95_bytes", "atlasMarks": "atlas_marks",
    }
    for key, budget_key in comparisons.items():
        if performance[key] > BUDGETS[budget_key]:
            failures.append({"metric": key, "value": performance[key], "budget": BUDGETS[budget_key]})
    if influence != 0:
        failures.append({"metric": "influenceEdges", "value": influence, "budget": 0})
    manifest = {
        "version": VERSION,
        "sourceDatabaseSha256": database_sha,
        "sourceCandidateJsonSha256": candidate_json_sha,
        "frozenDataModified": False,
        "counts": atlas["counts"],
        "performance": performance,
        "budgets": BUDGETS,
        "gate": "PASS" if not failures else "HOLD",
        "failures": failures,
        "assets": assets,
    }
    dump(OUT / "manifest.json", manifest)
    print(json.dumps({"gate": manifest["gate"], "assets": len(assets) + 1, "performance": performance, "failures": failures}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
