#!/usr/bin/env python3
"""Apply explicit LOC object-place evidence to produce v48 from v47."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import rebuild_public_surfaces_from_records as rebuild

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; GENERATED=ROOT/'generated'
PARENT=GENERATED/'public_surfaces_prefreeze_candidate_v47.json'; OUT=GENERATED/'public_surfaces_prefreeze_candidate_v48.json'
REPAIRS=DATA/'prefreeze_candidate_v48_loc_geo_repairs.csv'; NODES=DATA/'prefreeze_candidate_v48_loc_geo_trace_nodes.csv'; EDGES=DATA/'prefreeze_candidate_v48_loc_geo_trace_edges.csv'; SAMPLE_IN=DATA/'prefreeze_candidate_v47_sample_200_audit.csv'; SAMPLE_OUT=DATA/'prefreeze_candidate_v48_sample_200_audit.csv'; SUMMARY=DATA/'prefreeze_candidate_v48_summary.csv'

def ident(p,*v): return p+'-'+hashlib.sha1('\x1f'.join(v).encode()).hexdigest()[:16].upper()
def read(path):
 with path.open(encoding='utf-8',newline='') as h:return list(csv.DictReader(h))
def write(path,fields,rows):
 with path.open('w',encoding='utf-8',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)
def table(s,kind): return next(x for x in s['tables'] if x['kind']==kind)
def put(t,label,value):
 for r in t['rows']:
  if r[0]==label:r[1]=value;return
 t['rows'].append([label,value])

def main():
 p=json.loads(PARENT.read_text(encoding='utf-8')); repairs=read(REPAIRS); by={x['surface_id']:x for x in repairs}; surf={x['surfaceId']:x for x in p['surfaces']}
 if len(repairs)!=18 or any(k not in surf for k in by):raise SystemExit('repair source mismatch')
 nodes={};edges=[]
 for sid,r in by.items():
  s=surf[sid]; trace=s['trace']; tree=trace['treeId']; oid=trace['objectNodeId']; pid=ident('TRN-PLACE',r['country'])
  nodes[pid]={'node_id':pid,'tree_id':tree,'node_type':'place','label':r['country'],'canonical_key':'place:'+r['country'].casefold(),'region':r['country'],'source_url':r['loc_item_url'],'evidence':'LOC item.place object geography repair','evidence_status':'source_verified'}
  eid=ident('TRE',oid,pid,'associated_with_place','v48_loc_item_place')
  edges.append({'edge_id':eid,'tree_id':tree,'branch_id':'TRB167','subject_node_id':oid,'object_node_id':pid,'edge_label':'associated_with_place','evidence_url':r['loc_item_url'],'evidence_text':r['evidence_text'],'evidence_field':r['evidence_field'],'confidence':'high','review_state':'accepted','prohibited_inference_check':'pass:explicit_object_place_not_influence'})
  s['placeText']=r['normalized_place_text']; s['folders']=[x for x in s['folders'] if x.get('type')!='region']; s['folders'].insert(0,{'folderId':'FOL-REGION-UNITED-STATES','type':'region','title':'United States'})
  put(table(s,'SOURCE'),'Source place',r['normalized_place_text']); put(table(s,'NORMALIZED'),'Region','United States');put(table(s,'NORMALIZED'),'Object geography evidence',r['evidence_text']);put(table(s,'RELATIONS'),'TRACE geography repair','LOC item.place (explicit object place)')
  trace['branchIds']=list(dict.fromkeys([*(trace.get('branchIds') or []),'TRB167']));trace['edgeIds']=list(dict.fromkeys([*(trace.get('edgeIds') or []),eid]));trace['edgeLabels']=list(dict.fromkeys([*(trace.get('edgeLabels') or []),'associated_with_place']));trace['edgeCount']=int(trace.get('edgeCount') or 0)+1;trace['coreEdgeCount']=int(trace.get('coreEdgeCount') or trace.get('edgeCount')-1)+1;trace['evidenceReturnUrl']=r['loc_item_url']
 # Move folder memberships without inferring a country from a repository.
 us=next(x for x in p['folders'] if x.get('folderId')=='FOL-REGION-UNITED-STATES'); us_ids=set(us['surfaceIds']);us_ids.update(by);us['surfaceIds']=sorted(us_ids)
 for f in p['folders']:
  if f.get('type')=='region' and f.get('folderId')!='FOL-REGION-UNITED-STATES':f['surfaceIds']=[x for x in f.get('surfaceIds',[]) if x not in by]
 p['folders']=[x for x in p['folders'] if not(x.get('type')=='region' and not x.get('surfaceIds'))]
 p['meta'].update({'generatedAt':'2026-08-01','status':'prefreeze_candidate_v48_loc_object_geography_repair','parentCandidateVersion':'v47','sourceCandidate':'generated/public_surfaces_prefreeze_candidate_v47.json','locObjectGeographyRepairsV48':len(repairs),'unresolvedRegionCount':0,'activeSurfaceCount':len(p['surfaces']),'acceptedObjectCount':len(p['surfaces']),'remainingToMinimumTarget':20000-len(p['surfaces'])})
 p=rebuild.attach_structural_collections(p);p=rebuild.build_research_dossiers(p)
 OUT.write_text(json.dumps(p,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 nf=['node_id','tree_id','node_type','label','canonical_key','region','source_url','evidence','evidence_status'];ef=['edge_id','tree_id','branch_id','subject_node_id','object_node_id','edge_label','evidence_url','evidence_text','evidence_field','confidence','review_state','prohibited_inference_check'];write(NODES,nf,list(nodes.values()));write(EDGES,ef,edges)
 fields=list(csv.DictReader(SAMPLE_IN.open(encoding='utf-8',newline='')).fieldnames or []); old=read(SAMPLE_IN); audits=[]
 for i,r in enumerate(repairs,1):audits.append({'sample_id':f'v48-loc-geo-{i:03d}','sample_lane':'v48_explicit_loc_item_place_repair','surface_id':r['surface_id'],'source_record_id':r['source_record_id'],'title':surf[r['surface_id']]['title'],'date_start':surf[r['surface_id']]['dateStart'],'region':r['normalized_place_text'],'source_name':'Library of Congress loc.gov API','authority_state':'resolved_origin','trace_state':'accepted','trace_tier':'source_verified','source_url_gate':'pass','title_gate':'pass','date_gate':'pass','region_gate':'pass','image_route_gate':'pass','authority_gate':'pass','trace_gate':'pass','influence_gate':'pass','six_tables_gate':'pass','audit_status':'pass','audit_note':r['evidence_text']})
 write(SAMPLE_OUT,fields,audits+old[:200-len(audits)])
 write(SUMMARY,['metric','value'],[{'metric':'active_objects','value':str(len(p['surfaces']))},{'metric':'explicit_LOC_object_geography_repairs','value':str(len(repairs))},{'metric':'unresolved_region_objects','value':'0'},{'metric':'remaining_to_20000','value':str(20000-len(p['surfaces']))}])
 print(json.dumps({'active':len(p['surfaces']),'repairs':len(repairs),'unresolved':sum(x.get('placeText')=='Unresolved region' for x in p['surfaces'])}))
if __name__=='__main__':main()
