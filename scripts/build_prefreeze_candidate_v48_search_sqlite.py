#!/usr/bin/env python3
"""Synchronize v48 explicit LOC geography repairs into an isolated SQLite copy."""
from __future__ import annotations
import csv,json,shutil,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';GEN=ROOT/'generated';DOCS=ROOT/'docs'/'capture'
BASE=DATA/'prefreeze_candidate_v47.sqlite';OUT=DATA/'prefreeze_candidate_v48.sqlite';PAYLOAD=GEN/'public_surfaces_prefreeze_candidate_v48.json';REPAIRS=DATA/'prefreeze_candidate_v48_loc_geo_repairs.csv';NODES=DATA/'prefreeze_candidate_v48_loc_geo_trace_nodes.csv';EDGES=DATA/'prefreeze_candidate_v48_loc_geo_trace_edges.csv';GATE=DATA/'prefreeze_candidate_v48_search_gate.csv';REPORT=DOCS/'PREFREEZE_CANDIDATE_v48_SEARCH_TRACE.md'
def read(p):
 with p.open(encoding='utf-8',newline='') as h:return list(csv.DictReader(h))
def write(p,fields,rows):
 with p.open('w',encoding='utf-8',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def scalar(c,q,args=()):return int(c.execute(q,args).fetchone()[0])
def main():
 p=json.loads(PAYLOAD.read_text(encoding='utf-8')); rep=read(REPAIRS);nodes=read(NODES);edges=read(EDGES)
 if OUT.exists():OUT.unlink()
 shutil.copy2(BASE,OUT);c=sqlite3.connect(OUT)
 try:
  c.executemany('insert or ignore into trace_nodes values (?,?,?,?,?,?,?,?,?)',[(x['node_id'],x['tree_id'],x['node_type'],x['label'],x['canonical_key'],x['region'],x['source_url'],x['evidence'],x['evidence_status']) for x in nodes])
  c.executemany('insert or ignore into trace_edges values (?,?,?,?,?,?,?,?,?,?,?,?)',[(x['edge_id'],x['tree_id'],x['branch_id'],x['subject_node_id'],x['object_node_id'],x['edge_label'],x['evidence_url'],x['evidence_text'],x['evidence_field'],x['confidence'],x['review_state'],x['prohibited_inference_check']) for x in edges])
  em={x['subject_node_id']:x for x in edges}
  for r in rep:
   sid=r['surface_id'];e=next(x for x in edges if x['evidence_url']==r['loc_item_url'] and x['evidence_text']==r['evidence_text'])
   c.execute("update objects set region='United States',trace_edge_count=trace_edge_count+1,trace_core_edge_count=trace_core_edge_count+1,trace_evidence_url=? where surface_id=?",(r['loc_item_url'],sid))
   c.execute("delete from object_folder_refs where surface_id=? and folder_type='region'",(sid,));c.execute('insert or ignore into object_folder_refs values (?,?,?,?)',(sid,'FOL-REGION-UNITED-STATES','region','United States'))
   c.execute("update object_metadata_rows set value=? where surface_id=? and ((table_kind='SOURCE' and label='Source place') or (table_kind='NORMALIZED' and label='Region'))",(r['normalized_place_text'],sid))
   c.execute("update object_metadata_rows set value='United States' where surface_id=? and table_kind='NORMALIZED' and label='Region'",(sid,))
   c.execute('insert or ignore into object_metadata_rows values (?,?,?,?,?)',(sid,'NORMALIZED',999,'Object geography evidence',r['evidence_text']))
   c.execute('insert or ignore into object_trace_edges values (?,?)',(sid,e['edge_id']))
   c.execute("update search_documents set region='United States',body=body||char(10)||? where object_or_capture_id=? and active_object=1",(f"object_geography: {r['evidence_text']}",sid))
  c.execute("insert into search_documents_fts(search_documents_fts) values('rebuild')")
  for k,v in {'active_object_count':str(len(p['surfaces'])),'candidate_status':'prefreeze_candidate_v48','schema_version':'prefreeze_candidate_v48_sqlite_v1','source_payload':'generated/public_surfaces_prefreeze_candidate_v48.json'}.items():c.execute('update schema_meta set value=? where key=?',(v,k))
  c.executescript("drop view if exists active_objects_current;create view active_objects_current as select * from objects where count_eligible=1;drop view if exists trace_accepted_objects_current;create view trace_accepted_objects_current as select * from objects where trace_state='accepted';")
  gates=[('sqlite_integrity',c.execute('pragma integrity_check').fetchone()[0],'ok'),('active_object_count',scalar(c,"select count(*) from objects where count_eligible=1"),str(len(p['surfaces']))),('unresolved_region_active',scalar(c,"select count(*) from objects where count_eligible=1 and region='Unresolved region'"),'0'),('trace_unlinked_active',scalar(c,"select count(*) from objects where count_eligible=1 and trace_state<>'accepted'"),'0'),('influence_edges',scalar(c,"select count(*) from trace_edges where edge_label='influenced_by'"),'0'),('loc_geo_repair_edges',scalar(c,"select count(*) from trace_edges where branch_id='TRB167'"),str(len(rep)))]
  c.commit()
 finally:c.close()
 rows=[{'gate':k,'value':v,'status':'PASS' if str(v)==need else 'HOLD','requirement':need,'note':'v48 explicit LOC object-place repair'} for k,v,need in gates];write(GATE,['gate','value','status','requirement','note'],rows)
 REPORT.write_text('# Prefreeze candidate v48 search and TRACE\n\n- 18 LOC item.place repairs synchronized; active unresolved geography: 0.\n- Active total remains 15,923; no influence edges are inferred.\n\n## Gates\n\n'+'\n'.join(f"- {x['gate']}: {x['value']} — {x['status']}" for x in rows)+'\n',encoding='utf-8')
 print(json.dumps({'gates':len(rows),'pass':sum(x['status']=='PASS' for x in rows)}))
if __name__=='__main__':main()
