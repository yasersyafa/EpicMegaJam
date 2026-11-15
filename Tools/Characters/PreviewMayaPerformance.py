import bpy,math,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_paths import ART_ROOT
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ART_ROOT/'Maya/Maya_Performance.blend'))
s=bpy.context.scene;units=1/s.unit_settings.scale_length;arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH')
s.world=bpy.data.worlds.new('PreviewWorld');s.world.color=(.35,.35,.35)
s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=480;s.render.resolution_y=600;s.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(2.6*units,-4*units,2.2*units));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.88*units))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.1*units;s.camera=cam
for loc,power in [((2,-3,4),650),((-3,-1,3),450)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(loc)*units);l=bpy.context.object;l.data.energy=power*units*units;l.data.size=4*units;l.rotation_euler=(Vector((0,0,.8*units))-l.location).to_track_quat('-Z','Y').to_euler()
out=ROOT/'Saved/CharacterPolish/Previews';out.mkdir(exist_ok=True)
report=[]
for name,t in [('Idle',.1),('Walk',.25),('LookAround',.3),('LookAtDirector',.5),('Hesitate',.4),('Inspect',.5),('Surprised',.3),('Waiting',.5),('ReadScript',.5),('WalkWithScript',.25)]:
 a=bpy.data.actions['A_Maya_'+name];arm.animation_data.action=a;s.frame_set(round(a.frame_range.y*t))
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 # Measure deformed bounds at every authored frame, catch collapsed/exploded poses.
 heights=[]
 for f in range(int(a.frame_range.y)+1):
  s.frame_set(f);ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());coords=[ev.matrix_world@Vector(c) for c in ev.bound_box];heights.append((max(v.z for v in coords)-min(v.z for v in coords))/units)
 report.append({'animation':name,'min_height':min(heights),'max_height':max(heights)})
(ROOT/'Saved/CharacterPolish/blender_validation.json').write_text(json.dumps(report,indent=2))
