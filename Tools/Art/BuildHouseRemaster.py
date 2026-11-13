"""Build centimeter-scale old-house mouldings and shared fixtures from saved room bounds."""
import importlib.util,json,math,os
from pathlib import Path
PROJECT=Path(os.environ.get('HOUSE_PROP_PROJECT',str(Path(__file__).resolve().parents[2])))
spec=importlib.util.spec_from_file_location('house_mesh',str(PROJECT/'Tools/Art/BuildHouseProps.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
OUT=PROJECT/'SourceArt/Environment/House/Remaster';OUT.mkdir(parents=True,exist_ok=True);g.OUT=str(OUT)
g.PALETTE.update({'AgedIvory':(.48,.44,.34),'Ceiling':(.48,.46,.39),'Brass':(.22,.15,.065),'Glass':(.85,.69,.4),'Roof':(.05,.065,.062),'PanelInset':(.32,.31,.24),'Sage':(.17,.225,.2)})
input_path=PROJECT/'Saved/HouseRemasterInspection.json'
if not input_path.exists():input_path=OUT/'HouseRemasterInput.json'
data=json.loads(input_path.read_text());(OUT/'HouseRemasterInput.json').write_text(json.dumps(data,indent=2))
floors=[a for a in data['actors'] if a['label'].startswith('GB_Floor_')];walls=[a for a in data['actors'] if a['label'].startswith('GB_Wall_')];lintels=[a for a in data['actors'] if a['label'].startswith('GB_Lintel_')]
# Infer clear door intervals from neighbouring solid walls, not oversized lintel bounds.
doors=[]
for a in lintels:
 x,y,_=a['bounds_origin'];wx,wy,_=a['bounds_extent'];axis=0 if wx>wy else 1;perp=1-axis;c=a['bounds_origin'][axis]
 same=[w for w in walls if (w['bounds_extent'][0]>w['bounds_extent'][1])==(axis==0) and abs(w['bounds_origin'][perp]-a['bounds_origin'][perp])<.1]
 left=[w['bounds_origin'][axis]+w['bounds_extent'][axis] for w in same if w['bounds_origin'][axis]+w['bounds_extent'][axis]<c]
 right=[w['bounds_origin'][axis]-w['bounds_extent'][axis] for w in same if w['bounds_origin'][axis]-w['bounds_extent'][axis]>c]
 if not left or not right:raise RuntimeError('Cannot resolve door '+a['label'])
 lo,hi=max(left),min(right)
 if hi-lo<90 or hi-lo>2*a['bounds_extent'][axis]+1:raise RuntimeError('Invalid door interval '+a['label'])
 doors.append(dict(label=a['label'],axis=axis,plane=a['bounds_origin'][perp],lo=lo,hi=hi))
manifest=[];audit={'doors':doors,'casings':[],'panels':[],'cornice_runs':[]}
for floor in floors:
 room=floor['label'].removeprefix('GB_Floor_');cx,cy,_=floor['bounds_origin'];ex,ey,_=floor['bounds_extent'];m=g.Mesh('SM_House_Architecture_'+room);cornices={}
 def box(x,y,z,sx,sy,sz,mat='AgedIvory'):m.box((x-cx,y-cy,z),(sx,sy,sz),mat,0,roundness=1)
 for a in walls+lintels:
  x,y,_=a['bounds_origin'];wx,wy,_=a['bounds_extent'];along_x=wx>wy;axis=0 if along_x else 1;wallplane=y if along_x else x
  if along_x:
   if abs(abs(y-cy)-ey)>25:continue
   lo=max(x-wx,cx-ex+13);hi=min(x+wx,cx+ex-13);plane=y+(wy+1)*(1 if cy>y else -1)
  else:
   if abs(abs(x-cx)-ex)>25:continue
   lo=max(y-wy,cy-ey+13);hi=min(y+wy,cy+ey-13);plane=x+(wx+1)*(1 if cx>x else -1)
  if hi-lo<8:continue
  cornices.setdefault((axis,plane),[]).append((lo,hi))
  def strip(mid,z,ln,depth,height,mat='AgedIvory'):
   if along_x:box(mid,plane,z,ln,depth,height,mat)
   else:box(plane,mid,z,depth,ln,height,mat)
  if a in lintels:
   door=next(d for d in doors if d['label']==a['label']);dl,dh=door['lo'],door['hi']
   # Casings stand on the solid jambs; their inner edges coincide with the clear opening.
   for mid in (dl-4,dh+4):strip(mid,120,8,10,240)
   strip((dl+dh)/2,245,dh-dl+16,10,10)
   strip((dl+dh)/2,252,dh-dl+24,12,4)
   audit['casings'].append(dict(room=room,door=door['label'],opening=[dl,dh],jamb_inner_edges=[dl,dh]))
   continue
  # Stop all low rails/backing/frames against the OUTSIDE of each casing.
  for d in doors:
   if d['axis']!=axis or abs(d['plane']-wallplane)>.1:continue
   if abs(hi-d['lo'])<.1:hi-=8.1
   if abs(lo-d['hi'])<.1:lo+=8.1
  if hi-lo<8:continue
  audit['panels'].append(dict(room=room,axis=axis,wallplane=wallplane,lo=lo,hi=hi))
  strip((lo+hi)/2,60,hi-lo,2.5,108,'PanelInset')
  for z,depth,height in [(7,5,14),(108,4,7),(115,6,4)]:strip((lo+hi)/2,z,hi-lo,depth,height)
  n=max(1,round((hi-lo)/90));step=(hi-lo)/n
  for i in range(n):
   l=lo+i*step+6;r=lo+(i+1)*step-6
   for mid in (l,r):strip(mid,61,3,8.5,72)
   for z in (25,97):strip((l+r)/2,z,max(2,r-l),8.5,3)
 # Union lintel and wall spans before creating cornices, removing double/coplanar overlaps.
 for (axis,plane),spans in cornices.items():
  merged=[]
  for lo,hi in sorted(spans):
   if merged and lo<=merged[-1][1]+.01:merged[-1][1]=max(hi,merged[-1][1])
   else:merged.append([lo,hi])
  for lo,hi in merged:
   audit['cornice_runs'].append(dict(room=room,axis=axis,plane=plane,lo=lo,hi=hi))
   for z,depth,height in [(333,7,10),(325,5,4),(318,3,3)]:
    if axis==0:box((lo+hi)/2,plane,z,hi-lo,depth,height)
    else:box(plane,(lo+hi)/2,z,depth,hi-lo,height)
 e=m.write();e.update(location=[cx,cy,0],room=room,category='Architecture');manifest.append(e)
# Focused geometry gate: no low panel may intersect a clear opening or its casing footprint.
for panel in audit['panels']:
 for door in doors:
  if panel['axis']==door['axis'] and abs(panel['wallplane']-door['plane'])<.1:
   assert min(panel['hi'],door['hi']+8)-max(panel['lo'],door['lo']-8)<=.01,(panel,door)
audit['passed']=True
(OUT/'HouseTrimFitAudit.json').write_text(json.dumps(audit,indent=2))
# Shared hanging light. A few solid frosted bulbs, no translucency/alpha overdraw.
m=g.Mesh('SM_House_Fixture_Chandelier')
m.rod((0,0,-3),(0,0,0),18,'Brass',16);m.rod((0,0,-30),(0,0,-3),1.5,'Brass',8)
m.lathe((0,0,-28),[(0,0),(11,-2),(13,-5),(9,-8),(0,-8)],'Brass',16)
for i in range(4):
 a=i*math.pi/2;x,y=31*math.cos(a),31*math.sin(a)
 m.rod((0,0,-31),(x,y,-37),1.2,'Brass',8)
 m.lathe((x,y,-40),[(0,-10),(6,-8),(8,-3),(8,3),(5,8),(0,10)],'Glass',12)
e=m.write();e.update(category='Fixture');manifest.append(e)
# A broad shallow ceiling rose, reused in every furnished room.
m=g.Mesh('SM_House_Fixture_CeilingRose')
m.lathe((0,0,0),[(0,0),(38,0),(38,-1),(34,-3),(23,-3),(21,-5),(15,-5),(12,-3),(0,-3)],'AgedIvory',32)
e=m.write();e.update(category='Fixture');manifest.append(e)
# Solid pentagonal gable ends: exact sloping silhouette, no stepped gaps.
m=g.Mesh('SM_House_Roof_Gable');profile=[(-1595,340),(1595,340),(1595,448),(0,660),(-1595,448)]
for y,normal in [(-13,(0,-1,0)),(13,(0,1,0))]:
 ids=[m.vert((x,y,z),normal,((x+1595)/3190,(z-340)/320)) for x,z in profile]
 for i in range(1,4):m.tri(ids[0],ids[i],ids[i+1],'Sage')
for i in range(5):
 a=profile[i];b=profile[(i+1)%5];n=g.norm((b[1]-a[1],0,a[0]-b[0]))
 ids=[m.vert(v,n,uv) for v,uv in [((a[0],-13,a[1]),(0,0)),((b[0],-13,b[1]),(1,0)),((b[0],13,b[1]),(1,1)),((a[0],13,a[1]),(0,1))]]
 m.tri(ids[0],ids[1],ids[2],'Sage');m.tri(ids[0],ids[2],ids[3],'Sage')
e=m.write();e.update(category='Roof');manifest.append(e)
(OUT/'HouseRemasterManifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'meshes':len(manifest),'triangles':sum(x['triangles'] for x in manifest)}))

