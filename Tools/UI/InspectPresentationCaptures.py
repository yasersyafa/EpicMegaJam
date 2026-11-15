"""Inspect pixels from PNGs rendered in PIE; no Unreal editor-world tests."""
import json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/UIRefresh/Runtime'
report=json.loads((OUT/'report.json').read_text());checks=[];prompt_frames={}
for name in report['captures']:
 if not name.startswith(('opening_','intro_','take_')):continue
 path=OUT/(name+'.bmp');data=path.read_bytes();offset=struct.unpack_from('<I',data,10)[0];w,h,planes,bits=struct.unpack_from('<iiHH',data,18);assert planes==1 and bits in [24,32]
 stride=((w*bits+31)//32)*4;pixels=np.frombuffer(data,dtype=np.uint8,offset=offset,count=stride*abs(h)).reshape(abs(h),stride)[:,:w*(bits//8)].reshape(abs(h),w,bits//8)
 if h>0:pixels=pixels[::-1]
 if name in ['take_2560','take_cut_prompt_2560']:prompt_frames[name]=pixels[:,:,:3].copy()
 height=abs(h);mask=pixels[:,:,:3].max(axis=2)>60;ys,xs=np.where(mask);assert len(ys),name+' empty render'
 row_hits=np.where(mask.sum(axis=1)>=3)[0];groups=[]
 for y in row_hits:
  if not groups or y-groups[-1][-1]>5:groups.append([int(y)])
  else:groups[-1].append(int(y))
 # Actual painted glyphs, including hints, must all be inside the lower 160px strip.
 inside=int(ys.min())>=height-160 and int(ys.max())<height
 # Up to speaker + two dialogue lines + separate hint.
 lines_ok=len(groups)<=4
 checks.append({'capture':name,'size':[w,height],'painted_bounds':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],'painted_line_groups':len(groups),'inside_lower_border':bool(inside),'line_count_ok':lines_ok,'passed':bool(inside and lines_ok)})
base=prompt_frames['take_2560'];hint=prompt_frames['take_cut_prompt_2560'];added=(hint.astype(np.int16)-base.astype(np.int16)).max(axis=2)>30
hint_y=np.where(added)[0];body_y=np.where(base.max(axis=2)>60)[0];gap=int(hint_y.min()-body_y.max()-1)
row=next(c for c in checks if c['capture']=='take_cut_prompt_2560');row['dialogue_to_hint_gap_px']=gap;row['passed']=row['passed'] and gap>=8
r={'checks':checks,'passed':all(c['passed'] for c in checks)};(OUT/'pixel_bounds.json').write_text(json.dumps(r,indent=2));print({'pixel_checks':len(checks),'passed':r['passed']});assert r['passed']
