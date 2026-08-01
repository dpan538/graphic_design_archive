#!/usr/bin/env python3
"""Capture object-level LOC place evidence for v47's remaining unresolved rows."""
from __future__ import annotations
import csv, json, re, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; GENERATED=ROOT/'generated'
PARENT=GENERATED/'public_surfaces_prefreeze_candidate_v47.json'
RAW=DATA/'prefreeze_candidate_v48_loc_geo_repair_raw'; OUT=DATA/'prefreeze_candidate_v48_loc_geo_repairs.csv'
FIELDS=['surface_id','source_record_id','source_object_key','source_url','loc_item_url','loc_place_raw','normalized_place_text','country','evidence_field','evidence_text','status']
US={'Missouri','Massachusetts','Illinois','New Jersey','New York (State)','Ohio','United States'}

def norm(raw:str)->tuple[str,str]:
    parts=[x.strip() for x in raw.split('--') if x.strip()]
    if not parts or parts[0] not in US: raise ValueError(f'unsupported explicit LOC place: {raw}')
    if parts[0]=='United States': return 'United States','United States'
    first={'New York (State)':'New York',**{x:x for x in US}}[parts[0]]
    return 'United States — '+ ' — '.join([first,*parts[1:]]),'United States'

def main()->None:
    p=json.loads(PARENT.read_text(encoding='utf-8'))
    unresolved=[x for x in p['surfaces'] if x.get('placeText')=='Unresolved region']
    RAW.mkdir(parents=True,exist_ok=True); rows=[]
    for s in unresolved:
        key=str(s['sourceObjectKey']); url=f'https://www.loc.gov/pictures/item/{key}/?fo=json'
        req=urllib.request.Request(url,headers={'User-Agent':'ModernGDHistory/0.1 v48-loc-geo-repair'})
        with urllib.request.urlopen(req,timeout=45) as r: payload=json.loads(r.read().decode())
        (RAW/f'{key}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        item=payload.get('item') or {}; places=[str(x.get('title','')).strip() for x in item.get('place') or [] if str(x.get('title','')).strip()]
        if not places: raise SystemExit(f'missing item.place for {key}')
        # A record may have country plus city hierarchy; select the most specific
        # official place heading, never a title or repository location.
        raw=max(places,key=lambda x:(x.count('--'),len(x)))
        display,country=norm(raw)
        rows.append({'surface_id':s['surfaceId'],'source_record_id':s['sourceRecordId'],'source_object_key':key,'source_url':s['sourceUrl'],'loc_item_url':item.get('link') or s['sourceUrl'],'loc_place_raw':raw,'normalized_place_text':display,'country':country,'evidence_field':'item.place[].title','evidence_text':f'LOC item.place={raw}','status':'pass_explicit_object_place'})
        time.sleep(.2)
    if len(rows)!=18: raise SystemExit(f'expected 18 unresolved LOC rows, got {len(rows)}')
    with OUT.open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
    print(json.dumps({'repairs':len(rows),'countries':sorted({x['country'] for x in rows}),'raw_dir':str(RAW.relative_to(ROOT))}))
if __name__=='__main__': main()
