"""Small exterior prop library, centimeters, shared opaque materials."""
import os,importlib.util,json
from pathlib import Path
P=Path(os.environ.get('HOUSE_PROP_PROJECT',str(Path(__file__).resolve().parents[2])))
spec=importlib.util.spec_from_file_location('housemesh',str(P/'Tools/Art/BuildHouseProps.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
OUT=P/'SourceArt/Environment/House/Exterior';OUT.mkdir(parents=True,exist_ok=True);g.OUT=str(OUT);g.PALETTE.update({'LeafDark':(.03,.08,.035),'LeafSage':(.055,.11,.055),'Bark':(.065,.042,.023),'Stone':(.22,.23,.21),'Metal':(.04,.05,.05),'Bulb':(.8,.6,.3)})
entries=[]
m=g.Mesh('SM_House_Exterior_Shrub')
for x,y,z,r,mat in [(-26,0,0,1,'LeafDark'),(24,12,4,.85,'LeafSage'),(0,-23,12,.83,'LeafDark')]:
 m.lathe((x,y,z),[(0,2),(18*r,5),(37*r,20),(42*r,40),(32*r,63),(14*r,76),(0,80)],mat,12,aspect=.9)
entries.append(m.write())
m=g.Mesh('SM_House_Exterior_LampPost')
m.lathe((0,0,0),[(0,0),(24,0),(24,7),(16,11),(12,35),(7,42),(6,290)],'Metal',12)
m.box((0,0,314),(33,33,42),'Bulb',2,roundness=1)
for x in (-18,18):
 for y in (-18,18):m.rod((x,y,290),(x,y,339),1.5,'Metal',6)
for z in (290,339):m.box((0,0,z),(44,44,5),'Metal',1,roundness=1)
m.lathe((0,0,341),[(29,0),(20,9),(9,16),(0,22)],'Metal',12)
entries.append(m.write())
m=g.Mesh('SM_House_Exterior_WallLantern')
m.box((0,0,0),(20,5,33),'Metal',1,roundness=1);m.rod((0,0,10),(0,20,16),2,'Metal',8)
m.box((0,26,-3),(18,18,28),'Bulb',1,roundness=1)
for x in (-11,11):
 for y in (15,37):m.rod((x,y,-20),(x,y,17),1,'Metal',6)
for z in (-20,17):m.box((0,26,z),(26,26,3),'Metal',.5,roundness=1)
entries.append(m.write())
(OUT/'HouseExteriorManifest.json').write_text(json.dumps(entries,indent=2));print({'meshes':len(entries),'triangles':sum(e['triangles'] for e in entries)})
