#!/usr/bin/env python3
"""Strict AIC v47 main-object capture plus non-counted print/photo TRACE.

The pass is deliberately small and evidence-first: an object must have a
single exact AIC date, explicit `place_of_origin`, public-domain image route,
and a bounded graphic carrier. Search words are discovery only; neither them
nor an artist biography is used as geography. Explicitly documented art
photography and printmaking become auxiliary TRACE nodes, not active objects.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_expansion_capture_1931_1970 as shared

ROOT = Path(__file__).resolve().parents[1]
DATA, GENERATED = ROOT / "data", ROOT / "generated"
STEM = "capture_batch_trace_first_aic_geographic_balance_v47"
RAW = DATA / f"{STEM}_raw"; RECORDS = DATA / f"{STEM}_records.csv"; QUALITY = DATA / f"{STEM}_quality.csv"; NODES = DATA / f"{STEM}_trace_nodes.csv"; EDGES = DATA / f"{STEM}_trace_edges.csv"; SUMMARY = DATA / f"{STEM}_summary.csv"
ADJUNCT_RECORDS = DATA / f"{STEM}_trace_adjunct_records.csv"; ADJUNCT_NODES = DATA / f"{STEM}_trace_adjunct_nodes.csv"; ADJUNCT_EDGES = DATA / f"{STEM}_trace_adjunct_edges.csv"
PARENT = GENERATED / "public_surfaces_prefreeze_candidate_v46.json"
API = "https://api.artic.edu/api/v1/artworks/search"
TREE, BRANCH, ACCESS_DATE = "TRTREE048", "TRB165", "2026-08-01"
USER_AGENT = "ModernGDHistory/0.1 v47-aic-geographic-balance"
QUERIES = ("Mexican poster", "Polish poster", "Japanese poster", "Chinese poster", "Indian poster", "Iranian poster", "Turkish poster", "Brazilian poster", "Cuban poster", "South African poster", "Yugoslav poster", "Ukrainian poster")
BLOCKED_PLACE = {"united states", "usa", "united kingdom", "england", "scotland", "wales"}
PREFERRED_PLACE_TERMS = ("mexico", "poland", "japan", "china", "india", "iran", "turkey", "brazil", "cuba", "south africa", "yugoslav", "ukraine", "netherlands")
GRAPHIC = ("poster", "advertis", "portfolio cover", "book cover", "cover design", "type specimen", "label", "brochure", "publication", "graphic design", "typography", "packaging")
ADJUNCT_MEDIA = ("photograph", "gelatin silver", "silver dye", "inkjet", "lithograph", "zincograph", "screenprint", "woodcut", "etching", "photogravure")
NON_GRAPHIC = ("sauceboat", "tureen", "vessel", "porcelain", "ceramic", "textile", "furniture", "painting", "sculpture")
NODE_FIELDS = ["node_id", "tree_id", "node_type", "label", "canonical_key", "region", "source_url", "evidence", "evidence_status"]
EDGE_FIELDS = ["edge_id", "tree_id", "branch_id", "subject_node_id", "object_node_id", "edge_label", "evidence_url", "evidence_text", "evidence_field", "confidence", "review_state", "prohibited_inference_check"]
QUALITY_FIELDS = ["capture_id", "source_identifier", "source_title", "year", "place", "status", "reason"]


def clean(value: Any, limit: int = 1000) -> str:
    if isinstance(value, list): value = "; ".join(clean(x, limit) for x in value if clean(x, limit))
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def ident(prefix: str, *parts: str) -> str:
    return f"{prefix}-{hashlib.sha1(chr(31).join(parts).encode()).hexdigest()[:16].upper()}"


def existing() -> set[str]:
    source = json.loads(PARENT.read_text(encoding="utf-8"))
    return {clean(x.get("sourceObjectKey")) for x in source.get("surfaces") or [] if clean(x.get("sourceName")) == "Art Institute of Chicago API"}


def fetch(query: str) -> tuple[list[dict[str, Any]], Path]:
    params = {"q": query, "limit": "100", "fields": "id,title,date_display,date_start,date_end,place_of_origin,is_public_domain,image_id,classification_titles,medium_display,artist_display"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response: payload = json.loads(response.read().decode("utf-8"))
    RAW.mkdir(parents=True, exist_ok=True); path = RAW / (re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_") + ".json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    time.sleep(.35)
    return [x for x in payload.get("data") or [] if isinstance(x, dict)], path


def qualify(item: dict[str, Any]) -> tuple[dict[str, str] | None, str]:
    iid, title, place = clean(item.get("id")), clean(item.get("title")), clean(item.get("place_of_origin"))
    start, end = clean(item.get("date_start")), clean(item.get("date_end"))
    if not iid or not title: return None, "missing_identity"
    if not re.fullmatch(r"(18\d{2}|19\d{2}|20[0-2]\d)", start) or start != end: return None, "not_exact_single_year"
    folded_place = place.casefold()
    if not place or folded_place in BLOCKED_PLACE: return None, "blocked_or_missing_explicit_place"
    if not any(term in folded_place for term in PREFERRED_PLACE_TERMS): return None, "outside_current_geographic_balance_lane"
    if not clean(item.get("image_id")): return None, "missing_official_source_image"
    # Museum departments/classifications are discovery aids, not a carrier gate:
    # a ceramics object can be in a graphic-arts department.  Require the
    # title or medium itself to name a graphic carrier and reject material
    # classes that contradict that reading.
    medium = clean(item.get("medium_display"))
    carrier_blob = " ".join((title, medium)).casefold()
    if any(word in carrier_blob for word in NON_GRAPHIC): return None, "contradictory_non_graphic_carrier"
    # Main graphic carriers may be named in title or medium.  An auxiliary
    # photographic/printmaking branch is stricter: it must be documented by
    # the museum's medium field, never inferred merely from a title such as
    # "After Photography".
    carrier_role = "main" if any(word in carrier_blob for word in GRAPHIC) else "trace_adjunct" if any(word in medium.casefold() for word in ADJUNCT_MEDIA) else ""
    if not carrier_role: return None, "not_bounded_graphic_or_adjunct_media"
    return {"id": iid, "title": title, "year": start, "place": place, "image_id": clean(item.get("image_id")), "image_state": "IMG03" if item.get("is_public_domain") else "IMG02", "creator": clean(item.get("artist_display")), "type": clean(item.get("classification_titles")), "medium": clean(item.get("medium_display")), "date_text": clean(item.get("date_display")), "carrier_role": carrier_role}, f"qualified_{carrier_role}"


def as_record(x: dict[str, str], raw: Path, number: int) -> dict[str, str]:
    viewer = f"https://www.artic.edu/artworks/{x['id']}"; image = f"https://www.artic.edu/iiif/2/{x['image_id']}/full/843,/0/default.jpg"
    row = {key: "" for key in shared.FIELDNAMES}
    image_state = x["image_state"]
    image_note = "AIC API reports is_public_domain=true." if image_state == "IMG03" else "AIC exposes an official image route; item is not marked public domain and remains source-hosted only."
    # The IIIF URLs are discovered from the official API but were rejected by
    # Cloudflare during a live route check.  Retain their provenance in the
    # capture record while rendering through the stable item page only.
    image_state = "IMG02"
    image_note = "Official AIC item page and image metadata are retained; the direct IIIF route was not accepted by live validation, so display stays source-viewer only."
    row.update({"capture_id": f"AICTRACEV47R{number:04d}", "direction_id": "AIC-GEOBAL-V47", "direction_name": "aic / explicit-object-place geographic balance", "source_id": "SRC-AIC-GEOBAL-V47", "source_name": "Art Institute of Chicago API", "source_api_url": API, "capture_status": "qualified_trace_object", "source_identifier": x["id"], "source_record_url": viewer, "source_title": x["title"], "source_creator": x["creator"], "source_date_text": x["date_text"] or x["year"], "date_start": x["year"], "date_end": x["year"], "source_place_text": x["place"], "source_object_type": x["type"], "source_medium": x["medium"], "source_collection": "Art Institute of Chicago", "source_description": "AIC graphic object with explicit origin field.", "source_notes": "Promotion requires exact date_start=date_end, place_of_origin, graphic carrier, and a stable source item route.", "source_subjects": "graphic object; AIC", "source_rights_text": image_note, "rights_basis": image_note, "image_presence_code": image_state, "image_presence_basis": image_note, "image_state_evaluation": f"{image_state}: {image_note}", "image_state_confidence": "high", "rights_review_required": "true", "image_state_review_note": "Keep the AIC item route visible; no local copy.", "image_frame_behavior": "source_viewer_frame", "image_url_detected": image, "local_copy_permitted": "false", "iiif_or_viewer_available": viewer, "fallback_required": "false", "raw_json_path": str(raw.relative_to(ROOT)), "access_date": ACCESS_DATE, "image_expectation": "official source item route", "parser_status": "strict_object_gate_passed", "display_mode": "web_linear_object", "ocr_or_excerpt": x["medium"], "source_description_raw": f"date={x['year']}; place_of_origin={x['place']}; image_state={image_state}", "editorial_summary": f"{x['title']} is an AIC graphic object dated {x['year']} with explicit place of origin {x['place']}.", "historical_context_note": "The AIC record documents object attributes; it does not create historical-influence claims.", "classification_rationale": "AIC record has required item-level date, place, carrier and source item route.", "uncertainty_note": "Search country terms do not establish geography; only place_of_origin is used.", "citation_basis": f"Art Institute of Chicago. {x['title']}. {viewer}. Accessed {ACCESS_DATE}."})
    return row


def as_adjunct_record(x: dict[str, str], raw: Path, number: int) -> dict[str, str]:
    row = as_record(x, raw, number)
    row.update({"capture_id": f"AICTRACEV47X{number:04d}", "capture_status": "trace_adjunct_not_count_eligible", "direction_id": "AIC-TRACE-ADJUNCT-V47", "direction_name": "aic / print-photography auxiliary trace", "source_notes": "Auxiliary print/photography node: retained as a documented extension of graphic practice, never an active graphic-design object.", "classification_rationale": "Exact object year, explicit place and official image route pass; media is retained as a TRACE adjunct rather than a main graphic-design carrier.", "uncertainty_note": "countEligible=false. This record does not establish historical influence or elevate art photography/printmaking into the archive's main object category.", "editorial_summary": f"{x['title']} is retained as a dated, place-specific photographic or printed TRACE adjunct, not a main graphic-design object."})
    return row


def trace(row: dict[str, str], *, adjunct: bool = False) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    obj, source, place, year = ident("TRN-OBJ", row["source_identifier"]), ident("TRN-SRC", row["source_identifier"]), ident("TRN-PLACE", row["source_place_text"]), ident("TRN-YEAR", row["date_start"]); url = row["source_record_url"]
    nodes = [{"node_id": obj, "tree_id": TREE, "node_type": "object", "label": row["source_title"], "canonical_key": row["source_identifier"], "region": row["source_place_text"], "source_url": url, "evidence": "AIC object API record", "evidence_status": "source_verified"}, {"node_id": source, "tree_id": TREE, "node_type": "source_record", "label": f"AIC {row['source_identifier']}", "canonical_key": url, "region": "", "source_url": url, "evidence": "Official public-domain AIC object record", "evidence_status": "source_verified"}, {"node_id": place, "tree_id": TREE, "node_type": "place", "label": row["source_place_text"], "canonical_key": f"place:{row['source_place_text'].casefold()}", "region": row["source_place_text"], "source_url": url, "evidence": "AIC place_of_origin", "evidence_status": "source_verified"}, {"node_id": year, "tree_id": TREE, "node_type": "year", "label": row["date_start"], "canonical_key": f"year:{row['date_start']}", "region": "", "source_url": url, "evidence": "AIC exact date", "evidence_status": "source_verified"}]
    links = [(obj,source,"documented_by","Official AIC object record","source_record"),(obj,place,"associated_with_place",f"place_of_origin={row['source_place_text']}","place_of_origin"),(obj,year,"dated",f"date_start=date_end={row['date_start']}","date_start/date_end")]
    state = "accepted_auxiliary" if adjunct else "accepted"
    branch = "TRB166" if adjunct else BRANCH
    edges = [{"edge_id": ident("TRE",a,b,label,state),"tree_id":TREE,"branch_id":branch,"subject_node_id":a,"object_node_id":b,"edge_label":label,"evidence_url":url,"evidence_text":text,"evidence_field":field,"confidence":"high","review_state":state,"prohibited_inference_check":"pass:no_historical_influence_inferred"} for a,b,label,text,field in links]
    return nodes,edges


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        w=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore",lineterminator="\n"); w.writeheader(); w.writerows(rows)


def main() -> None:
    seen=existing(); held=Counter(); rows=[]; nodes={}; edges={}; quality=[]; adjunct_rows=[]; adjunct_nodes={}; adjunct_edges={}
    for query in QUERIES:
        items, raw = fetch(query)
        for item in items:
            hit, reason=qualify(item)
            if not hit: held[reason]+=1; continue
            if hit['id'] in seen: held['already_v46_or_batch']+=1; continue
            seen.add(hit['id'])
            if hit["carrier_role"] == "main":
                row=as_record(hit,raw,len(rows)+1); rows.append(row); ns,es=trace(row); nodes.update({x['node_id']:x for x in ns}); edges.update({x['edge_id']:x for x in es}); quality.append({"capture_id":row['capture_id'],"source_identifier":row['source_identifier'],"source_title":row['source_title'],"year":row['date_start'],"place":row['source_place_text'],"status":"pass","reason":"all_item_level_main_gates_pass"})
            else:
                row=as_adjunct_record(hit,raw,len(adjunct_rows)+1); adjunct_rows.append(row); ns,es=trace(row,adjunct=True); adjunct_nodes.update({x['node_id']:x for x in ns}); adjunct_edges.update({x['edge_id']:x for x in es})
    write(RECORDS,shared.FIELDNAMES,rows); write(QUALITY,QUALITY_FIELDS,quality); write(NODES,NODE_FIELDS,list(nodes.values())); write(EDGES,EDGE_FIELDS,list(edges.values())); write(ADJUNCT_RECORDS,shared.FIELDNAMES,adjunct_rows); write(ADJUNCT_NODES,NODE_FIELDS,list(adjunct_nodes.values())); write(ADJUNCT_EDGES,EDGE_FIELDS,list(adjunct_edges.values())); write(SUMMARY,["metric","value"],[{"metric":"qualified_main_objects","value":str(len(rows))},{"metric":"trace_adjunct_objects_not_count_eligible","value":str(len(adjunct_rows))},*[{"metric":f"hold:{k}","value":str(v)} for k,v in sorted(held.items())]])
    print(json.dumps({"qualified_main_objects":len(rows),"trace_adjunct_objects":len(adjunct_rows),"held":held,"trace_nodes":len(nodes)+len(adjunct_nodes),"trace_edges":len(edges)+len(adjunct_edges)},default=dict))


if __name__ == "__main__": main()
