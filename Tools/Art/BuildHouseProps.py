"""Deterministic centimeter-scale, beveled game-prop source meshes; no dependencies."""
import math, os, json
from pathlib import Path
from collections import defaultdict

PROJECT = Path(os.environ.get('HOUSE_PROP_PROJECT',str(Path(__file__).resolve().parents[2])))
OUT = str(PROJECT / 'SourceArt' / 'Environment' / 'House' / 'Props')
os.makedirs(OUT, exist_ok=True)
PALETTE = {'Wood':(.25,.12,.05),'Fabric':(.10,.11,.09),'Tan':(.35,.27,.18),'Metal':(.16,.17,.18),'Rubber':(.018,.02,.022),'Yellow':(.48,.25,.035),'Ivory':(.72,.69,.61),'Stone':(.46,.44,.38),'Paper':(.75,.72,.64),'Ink':(.025,.03,.028),'Mirror':(.4,.45,.48),'Bulb':(1,.65,.25),'Leaf':(.07,.16,.035),'Soil':(.055,.026,.012),'Terracotta':(.25,.095,.045),'Burgundy':(.19,.045,.035)}

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a): return mul(a,1/max(1e-9,math.sqrt(dot(a,a))))
def rotate(p,yaw=0):
    a=math.radians(yaw); c,s=math.cos(a),math.sin(a)
    return (p[0]*c-p[1]*s,p[0]*s+p[1]*c,p[2])

class Mesh:
    def __init__(self,name): self.name=name; self.vertices=[]; self.faces=[]
    def vert(self,p,n,uv=(0,0)):
        self.vertices.append((p,n,uv)); return len(self.vertices)
    def tri(self,a,b,c,mat):
        p,q,r=[self.vertices[i-1][0] for i in (a,b,c)]
        n=self.vertices[a-1][1]
        area=cross(sub(q,p),sub(r,p))
        if dot(area,area)<1e-12: return
        if dot(area,n)<0: b,c=c,b
        self.faces.append((mat,(a,b,c)))
    def box(self,center,size,mat='Wood',bevel=1,yaw=0,roundness=2):
        h=[s/2 for s in size]; radius=min(bevel,min(h)*.8)
        for axis in range(3):
            u=(axis+1)%3; v=(axis+2)%3
            for sign in (-1,1):
                def steps(half):
                    if radius<=0: return [-half,half]
                    if roundness==1: return [-half,-half+radius,half-radius,half]
                    return [-half,-half+radius*.5,-half+radius,half-radius,half-radius*.5,half]
                us,vs=steps(h[u]),steps(h[v]); grid=[]
                for i,x in enumerate(us):
                    row=[]
                    for j,y in enumerate(vs):
                        raw=[0.,0.,0.]; raw[axis]=sign*h[axis]; raw[u]=x;raw[v]=y
                        inner=[max(-h[k]+radius,min(h[k]-radius,raw[k])) for k in range(3)]
                        delta=sub(raw,inner)
                        n=norm(delta) if radius>0 else tuple(sign if k==axis else 0 for k in range(3))
                        p=add(inner,mul(n,radius)) if radius>0 else raw
                        row.append(self.vert(add(rotate(p,yaw),center),rotate(n,yaw),(x/size[u]+.5,y/size[v]+.5)))
                    grid.append(row)
                for i in range(len(us)-1):
                    for j in range(len(vs)-1):
                        a,b,c,d=grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1]
                        self.tri(a,b,c,mat);self.tri(a,c,d,mat)
    def rod(self,a,b,r,mat='Metal',segments=12,r2=None):
        direction=norm(sub(b,a)); base=(0,0,1) if abs(direction[2])<.9 else (0,1,0)
        u=norm(cross(direction,base));v=cross(direction,u);rings=[]
        for center,radius in ((a,r),(b,r if r2 is None else r2)):
            ring=[]
            for i in range(segments+1):
                angle=2*math.pi*i/segments; n=add(mul(u,math.cos(angle)),mul(v,math.sin(angle)))
                ring.append(self.vert(add(center,mul(n,radius)),n,(i/segments,0 if center==a else 1)))
            rings.append(ring)
        for i in range(segments):
            j=i+1
            self.tri(rings[0][i],rings[1][i],rings[1][j],mat);self.tri(rings[0][i],rings[1][j],rings[0][j],mat)
        for center,normal,ring in ((a,mul(direction,-1),rings[0]),(b,direction,rings[1])):
            c=self.vert(center,normal,(.5,.5))
            rim=[self.vert(self.vertices[index-1][0],normal,(.5+.5*math.cos(2*math.pi*i/segments),.5+.5*math.sin(2*math.pi*i/segments))) for i,index in enumerate(ring)]
            for i in range(segments): self.tri(c,rim[i],rim[i+1],mat)
    def lathe(self,center,profile,mat='Metal',segments=24,aspect=1):
        rings=[]
        for k,(r,z) in enumerate(profile):
            prev=profile[max(0,k-1)];nxt=profile[min(len(profile)-1,k+1)]
            dr,dz=nxt[0]-prev[0],nxt[1]-prev[1]
            ring=[]
            for i in range(segments+1):
                a=2*math.pi*i/segments;c,s=math.cos(a),math.sin(a)
                p=add(center,(r*c,r*s*aspect,z)); n=norm((dz*c,dz*s/aspect,-dr))
                ring.append(self.vert(p,n,(i/segments,k/max(1,len(profile)-1))))
            rings.append(ring)
        for k in range(len(rings)-1):
            for i in range(segments):
                j=i+1;a,b,c,d=rings[k][i],rings[k+1][i],rings[k+1][j],rings[k][j]
                self.tri(a,b,c,mat);self.tri(a,c,d,mat)
    def write(self):
        path=os.path.join(OUT,self.name+'.obj');mtl=self.name+'.mtl'
        with open(path,'w') as f:
            f.write('# House props. Units: centimeters. Z up. Pivot at floor.\nmtllib '+mtl+'\no '+self.name+'\n')
            # OBJ is right handed; Unreal's OBJ importer reflects Y on import.
            for p,n,uv in self.vertices: f.write('v %.5f %.5f %.5f\n'%(p[0],-p[1],p[2]))
            for p,n,uv in self.vertices: f.write('vt %.5f %.5f\n'%uv)
            for p,n,uv in self.vertices: f.write('vn %.6f %.6f %.6f\n'%(n[0],-n[1],n[2]))
            groups=defaultdict(list)
            for mat,face in self.faces: groups[mat].append(face)
            for mat,faces in groups.items():
                f.write('usemtl '+mat+'\ns 1\n')
                for face in faces:f.write('f '+' '.join('%d/%d/%d'%(i,i,i) for i in (face[0],face[2],face[1]))+'\n')
        with open(os.path.join(OUT,mtl),'w') as f:
            for mat in groups:f.write('newmtl %s\nKd %.4f %.4f %.4f\nd 1\n'%(mat,*PALETTE[mat]))
        return {'name':self.name,'file':self.name+'.obj','triangles':len(self.faces),'vertices':len(self.vertices),'slots':list(groups)}

def legs(m,w,d,z=70,mat='Wood',r=3):
    for x in (-w/2+10,w/2-10):
        for y in (-d/2+10,d/2-10):m.rod((x,y,0),(x,y,z),r,mat)

def sofa(name,width,seats=3):
    m=Mesh(name);depth=100
    for x in (-width/2+18,width/2-18):
        for y in (-32,32):m.box((x,y,9),(9,9,18),'Wood',1)
    m.box((0,0,29),(width-12,depth-8,30),'Fabric',9)
    m.box((0,37,68),(width-24,24,65),'Fabric',9)
    for x in (-width/2+9,width/2-9):m.box((x,-2,57),(25,100,52),'Fabric',9)
    step=(width-51)/seats
    for i in range(seats):
        x=-width/2+26+step*(i+.5)
        m.box((x,-13,49),(step-2.2,70,20),'Fabric',6)
        m.box((x,23,77),(step-3,24,43),'Fabric',7)
    for x in (-width/2+45,width/2-45):m.box((x,-4,72),(32,16,30),'Tan',7,yaw=-15 if x<0 else 15)
    return m

def table(name,w,d,h):
    m=Mesh(name);legs(m,w,d,h-8,r=4)
    m.box((0,0,h-3),(w,d,6),'Wood',2)
    m.box((0,0,h-12),(w-15,d-15,12),'Wood',1,roundness=1)
    return m

def cup(m,x,y,z):
    m.lathe((x,y,z),[(0,0),(4,0),(4.7,7),(4.7,8),(3.7,8),(3.5,6)],'Ivory',16)
    m.rod((x,y,z+6.3),(x,y,z+6.5),3.6,'Ink',16)
    for a,b in (((x+4,y,z+2),(x+7,y,z+2)),((x+7,y,z+2),(x+7,y,z+6)),((x+7,y,z+6),(x+4,y,z+6))):m.rod(a,b,.7,'Ivory',6)

def paperwork(m,x,y,z,yaw=0):
    m.box((x,y,z+.2),(22,30,.4),'Paper',.05,yaw=yaw,roundness=1)
    for i in range(6):
        p=add(rotate((0,-9+i*3,0),yaw),(x,y,z+.45))
        m.box(p,(13 if i else 17,.45,.12),'Ink',0,yaw=yaw)

def flightcase(name,w=110,d=65,h=75,yellow=True):
    m=Mesh(name); shell='Yellow' if yellow else 'Rubber'
    for x in (-w/2+10,w/2-10):
        for y in (-d/2+10,d/2-10):
            m.rod((x-3,y,6),(x+3,y,6),6,'Rubber',12)
            m.box((x,y,12),(8,8,8),'Metal',1,roundness=1)
    m.box((0,0,(h+15)/2),(w-3,d-3,h-15),shell,2,roundness=1)
    for z in (18,h-14,h):
        for y in (-d/2,d/2):m.box((0,y,z),(w,2.2,3),'Metal',.4,roundness=1)
        for x in (-w/2,w/2):m.box((x,0,z),(2.2,d,3),'Metal',.4,roundness=1)
    for x in (-w/2,w/2):
        for y in (-d/2,d/2):m.box((x,y,(h+17)/2),(3.5,3.5,h-15),'Metal',.4,roundness=1)
    for x in (-w*.28,w*.28):
        m.box((x,-d/2-1,h-15),(8,2,13),'Metal',1,roundness=1)
        m.box((x,-d/2-2,h-15),(3,1,6),'Rubber',.2,roundness=1)
    m.box((0,-d/2-2,h*.52),(23,3,13),'Rubber',2)
    m.rod((-9,-d/2-5,h*.53),(9,-d/2-5,h*.53),1.7,'Metal',8)
    m.box((w*.25,-d/2-1,h*.4),(14,1,7),'Paper',0)
    m.box((0,0,h+1),(w*.24,d*.4,1.8),'Rubber',.6,roundness=1)
    return m

def cabinet(name,w=130,sink=False,stove=False):
    m=Mesh(name)
    m.box((0,3,7),(w-6,57,14),'Rubber',1,roundness=1)
    m.box((0,0,47),(w,64,78),'Wood',2,roundness=1)
    for x in (-w*.25,w*.25):
        m.box((x,-33,48),(w/2-3,3,70),'Wood',1,roundness=1)
        m.rod((x-12,-36,70),(x+12,-36,70),1,'Metal',8)
    m.box((0,0,88),(w+3,68,5),'Stone',1.5)
    if sink:
        m.box((0,-2,91),(70,43,1),'Metal',2)
        m.box((0,-2,91.6),(60,33,1),'Rubber',4)
        for a,b in (((0,22,91),(0,22,120)),((0,22,120),(0,5,125)),((0,5,125),(0,-3,118))):m.rod(a,b,1.5,'Metal',12)
        m.rod((-15,22,91),(-15,22,98),2,'Metal',10)
    if stove:
        m.box((0,0,91),(w-10,58,2),'Rubber',2)
        for x in (-w*.25,w*.25):
            for y in (-15,15):
                m.lathe((x,y,93),[(10,0),(11,1),(10,2),(8,2),(8,0)],'Metal',16)
                for dx,dy in ((0,0),):m.rod((x-12,y,95),(x+12,y,95),.7,'Rubber',6)
        m.box((0,-35,46),(w-20,2,45),'Rubber',2)
        m.box((0,-37,47),(w-30,1,30),'Mirror',1)
        m.rod((-w*.3,-39,69),(w*.3,-39,69),1.5,'Metal',10)
    return m

def build():
    result=[]
    def keep(m):result.append(m.write())
    if '--probe' in __import__('sys').argv:
        test=Mesh('SM_House_ImportProbe');test.box((0,0,40),(100,60,80),'Wood',3);keep(test)
        return result
    keep(sofa('SM_House_Sofa_ThreeSeat',320,3));keep(sofa('SM_House_Sofa_TwoSeat',220,2));keep(sofa('SM_House_Armchair',105,1))
    keep(table('SM_House_Table_Coffee',170,85,42));keep(table('SM_House_Table_Side',60,60,55))
    meeting=table('SM_House_Table_Meeting',450,190,78)
    for i,(x,y) in enumerate(((-150,-42),(-45,30),(60,-38),(150,30),(-160,44),(80,45))):paperwork(meeting,x,y,78,i*17-30)
    for x,y in ((-180,0),(-70,-60),(45,60),(155,-58)):cup(meeting,x,y,78)
    keep(meeting)
    chair=Mesh('SM_House_Chair_Dining');legs(chair,57,58,43,'Metal',2)
    chair.box((0,0,44),(57,58,10),'Fabric',5)
    chair.box((0,24,72),(57,12,52),'Fabric',6)
    for x in (-24,24):chair.rod((x,23,38),(x,23,83),2,'Metal',10)
    keep(chair)
    desk=table('SM_House_Desk_Office',220,95,78)
    desk.box((75,8,38),(55,73,68),'Wood',2)
    for z in (20,40,60):
        desk.box((75,-30,z),(50,3,17),'Wood',1)
        desk.rod((64,-33,z+2),(86,-33,z+2),1,'Metal',8)
    paperwork(desk,-25,-5,78,-12);cup(desk,65,25,78)
    keep(desk)
    console=table('SM_House_Console',175,48,80)
    console.box((0,10,36),(155,35,6),'Wood',1);keep(console)
    keep(flightcase('SM_House_FlightCase_Yellow'))
    keep(flightcase('SM_House_FlightCase_Black',85,60,110,False))
    rack=Mesh('SM_House_Rack_Equipment')
    for x in (-100,100):
        for y in (-32,32):rack.box((x,y,105),(5,5,210),'Metal',.5,roundness=1)
    for z in (12,75,140):
        rack.box((0,0,z),(205,70,4),'Metal',.5,roundness=1)
    for y in (-32,32):rack.box((0,y,205),(205,5,4),'Metal',.5,roundness=1)
    for z in (44,107,172):
        for x in (-53,52):
            rack.box((x,0,z),(95,60,51),'Yellow' if x<0 else 'Rubber',2,roundness=1)
            rack.box((x,-31,z),(89,2,43),'Yellow' if z<100 else 'Metal',1,roundness=1)
            rack.box((x,-33,z+4),(22,2,9),'Metal',1,roundness=1)
            for xx in (x-39,x+39):rack.box((xx,-33,z),(2,2,45),'Metal',0)
    keep(rack)
    keep(cabinet('SM_House_Kitchen_Cabinet'));keep(cabinet('SM_House_Kitchen_Sink',sink=True));keep(cabinet('SM_House_Kitchen_Cooker',stove=True))
    fridge=Mesh('SM_House_Kitchen_Refrigerator');fridge.box((0,0,100),(85,78,200),'Metal',4)
    for z,h in ((55,103),(152,85)):
        fridge.box((0,-40,z),(79,5,h),'Ivory',3)
        fridge.rod((28,-46,z-22),(28,-46,z+22),1.8,'Metal',12)
    keep(fridge)
    toilet=Mesh('SM_House_Bathroom_Toilet')
    toilet.lathe((0,-8,0),[(0,0),(15,0),(18,8),(13,22),(20,37),(25,40),(25,44),(20,45),(19,41),(12,32),(0,31)],'Ivory',28,1.3)
    toilet.box((0,25,58),(45,22,55),'Ivory',5)
    toilet.box((0,25,87),(48,25,5),'Ivory',2)
    toilet.rod((15,25,90),(15,25,91),2.5,'Metal',12);keep(toilet)
    basin=Mesh('SM_House_Bathroom_Basin');basin.box((0,7,43),(38,35,82),'Wood',2)
    basin.box((0,0,86),(65,47,8),'Ivory',5)
    basin.box((0,-2,90),(42,28,1),'Rubber',6)
    for a,b in (((0,16,90),(0,16,110)),((0,16,110),(0,0,110))):basin.rod(a,b,1.3,'Metal',12)
    keep(basin)
    vanity=table('SM_House_Vanity_Illuminated',280,65,78)
    vanity.box((0,27,141),(280,14,126),'Wood',3)
    vanity.box((0,18,141),(242,2,104),'Mirror',2)
    for x in (-131,131):
        for z in (99,121,143,165,187):vanity.lathe((x,13,z),[(0,-3),(4,-2),(5,0),(4,3),(0,5)],'Bulb',12)
    for x in (-100,100):vanity.box((x,0,39),(66,58,70),'Wood',2)
    cup(vanity,95,-12,78);keep(vanity)
    rail=Mesh('SM_House_ClothesRail')
    for x in (-100,100):
        rail.rod((x,0,4),(x,0,190),2.5,'Metal',12);rail.rod((x,-30,4),(x,30,4),3,'Metal',12)
    rail.rod((-100,0,190),(100,0,190),2.5,'Metal',12)
    for i in range(8):
        x=-78+i*22
        rail.rod((x,0,189),(x,0,179),.9,'Metal',6)
        rail.rod((x,0,179),(x,-18,167),.8,'Metal',6);rail.rod((x,-18,167),(x,18,167),.8,'Metal',6);rail.rod((x,18,167),(x,0,179),.8,'Metal',6)
        rail.box((x,0,132),(15,40,72),'Burgundy' if i%3==0 else 'Tan',5)
        rail.box((x,0,166),(17,62,16),'Burgundy' if i%3==0 else 'Tan',4)
    keep(rail)
    plant=Mesh('SM_House_Plant_Potted')
    plant.lathe((0,0,0),[(0,0),(18,0),(23,4),(28,38),(30,40),(30,44),(26,44),(25,38)],'Terracotta',24)
    plant.rod((0,0,39),(0,0,40),25,'Soil',24)
    for i in range(19):
        a=i*2.399963;h=75+(i%5)*12;r=35+(i%3)*9
        plant.rod((0,0,38),(math.cos(a)*r*.65,math.sin(a)*r*.65,h),.7,'Leaf',6)
        spine=[]
        for j in range(5):
            t=j/4;rr=r*(.25+t*.9);z=h+22*math.sin(t*math.pi)-12*t
            spine.append((rr*math.cos(a),rr*math.sin(a),z))
        sides=[]
        for j,p in enumerate(spine):
            half=max(.3,12*math.sin(j/4*math.pi))
            tangent=(-math.sin(a)*half,math.cos(a)*half,0)
            sides.append((plant.vert(sub(p,tangent),(0,0,1),(0,j/4)),plant.vert(add(p,(0,0,3*math.sin(j/4*math.pi))),(0,0,1),(.5,j/4)),plant.vert(add(p,tangent),(0,0,1),(1,j/4))))
        for j in range(4):
            for k in range(2):
                q=(sides[j][k],sides[j+1][k],sides[j+1][k+1],sides[j][k+1])
                plant.tri(q[0],q[1],q[2],'Leaf');plant.tri(q[0],q[2],q[3],'Leaf')
                # Duplicate the underside with opposite normals for an opaque one-sided material.
                underside=[plant.vert(plant.vertices[v-1][0],(0,0,-1),plant.vertices[v-1][2]) for v in q]
                plant.tri(underside[0],underside[1],underside[2],'Leaf');plant.tri(underside[0],underside[2],underside[3],'Leaf')
    keep(plant)
    lamp=Mesh('SM_House_Lamp_Floor')
    lamp.lathe((0,0,0),[(0,0),(23,0),(25,3),(22,7),(5,10)],'Metal',24)
    lamp.rod((0,0,8),(0,0,160),2.5,'Metal',16)
    lamp.lathe((0,0,0),[(28,137),(30,138),(18,172),(16,172),(26,138)],'Tan',24)
    lamp.lathe((0,0,149),[(0,-7),(6,-5),(8,0),(6,6),(0,8)],'Bulb',16);keep(lamp)
    desk_lamp=Mesh('SM_House_Lamp_Desk')
    desk_lamp.rod((0,0,0),(0,0,3),13,'Metal',20)
    desk_lamp.rod((0,0,3),(0,0,42),1.5,'Metal',12)
    desk_lamp.rod((0,0,42),(0,-15,50),1.5,'Metal',12)
    desk_lamp.lathe((0,-15,0),[(14,35),(15,37),(5,53),(0,55)],'Metal',20)
    desk_lamp.rod((0,-15,36),(0,-15,37),11,'Bulb',20);keep(desk_lamp)
    rug=Mesh('SM_House_Rug_Bordered');rug.box((0,0,.6),(280,420,1.2),'Tan',.4,roundness=1)
    for x in (-127,127):rug.box((x,0,1.25),(6,394,.15),'Burgundy',0)
    for y in (-197,197):rug.box((0,y,1.25),(260,6,.15),'Burgundy',0)
    keep(rug)
    mirror=Mesh('SM_House_Mirror_Wall')
    mirror.box((0,0,145),(70,8,95),'Wood',2)
    mirror.box((0,-4.5,145),(60,1,85),'Mirror',1)
    keep(mirror)
    tall=Mesh('SM_House_Cabinet_Tall')
    tall.box((0,0,7),(175,51,14),'Wood',2)
    for x in (-89,89):tall.box((x,0,111),(6,55,210),'Wood',1)
    tall.box((0,24,111),(180,5,210),'Wood',1)
    for z in (18,78,140,213):tall.box((0,0,z),(180,55,5),'Wood',1)
    for x in (-46,46):
        tall.box((x,-28,46),(86,4,52),'Wood',1)
        tall.rod((x-12,-32,57),(x+12,-32,57),1.2,'Metal',10)
    for i in range(14):
        tall.box((-76+i*11,4,104+(i%3)*4),(8,28,46+(i%3)*8),'Tan' if i%3 else 'Burgundy',.5,roundness=1)
    for x in (-45,45):tall.box((x,5,168),(65,38,40),'Rubber',2,roundness=1)
    keep(tall)
    with open(os.path.join(OUT,'HousePropsManifest.json'),'w') as f:json.dump(result,f,indent=2)
    return result

if __name__=='__main__':
    result=build();print(json.dumps({'meshes':len(result),'triangles':sum(x['triangles'] for x in result),'output':OUT}))
