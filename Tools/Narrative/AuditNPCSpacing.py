import json,math,itertools
from pathlib import Path
P=str(Path(__file__).resolve().parents[2])+'/';r=json.load(open(P+'Saved/NarrativeBuildReport.json'));d=json.load(open(P+'Tools/Narrative/NarrativeFlow.json'));out=[]
for beat in [4,6,11,19]:
 paths=[p for p in r['routes'] if p['beat']==beat];mind={}
 def at(p,t):
  pts=p['points'];ds=[math.dist(x,y) for x,y in zip(pts,pts[1:])];total=sum(ds);f=max(0,min(1,(t-p['start'])/(p['end']-p['start'])))*total
  for a,b,dist in zip(pts,pts[1:],ds):
   if f<=dist:return [a[i]+(b[i]-a[i])*f/max(dist,.01) for i in range(3)]
   f-=dist
  return pts[-1]
 for n in range(int(d['blocks'][beat]['duration']*20)):
  t=n/20
  for a,b in itertools.combinations(paths,2):
   dist=math.dist(at(a,t),at(b,t));key=(a['actor'],b['actor'])
   if key not in mind or dist<mind[key]['distance']:mind[key]={'beat':beat,'actors':key,'distance':round(dist,2),'time':t}
 out+=list(mind.values())
json.dump({'minimum_pair_distances':out,'issues':[x for x in out if x['distance']<85]},open(P+'Saved/NarrativeNPCSpacing.json','w'),indent=2)
print([x for x in out if x['distance']<85])
