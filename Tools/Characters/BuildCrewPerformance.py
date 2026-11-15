"""Bake crew on one bind-axis convention while preserving each mesh's proportions."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_paths import ART_ROOT
OUT=ART_ROOT/'Crew';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ART_ROOT/'Maya/Original/Maya.fbx'))
source=next(o for o in bpy.data.objects if o.type=='ARMATURE');source_mesh=next(o for o in bpy.data.objects if o.type=='MESH')
actions={a.name.split('|')[-1].split('.')[0]:a for a in bpy.data.actions}
source.animation_data.action=None
for p in source.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()
source_rest={b.name:b.matrix_local.to_quaternion() for b in source.data.bones};source_pelvis=source.data.bones['pelvis'].head_local.copy();motion_scale=1.78/source_mesh.dimensions.z
cache={}
for name,base,count in [('Idle','idle',180),('Walk','walk',70),('Focused','idle',120)]:
 samples=[];source.animation_data.action=actions[base]
 for i in range(count+1):
  f=actions[base].frame_range.x+(actions[base].frame_range.y-actions[base].frame_range.x)*(i/count if name!='Focused' else 0)
  bpy.context.scene.frame_set(int(f),subframe=f-int(f))
  root_delta=source.pose.bones['root'].matrix.to_quaternion()@source_rest['root'].inverted()
  rotations={p.name:root_delta.inverted()@p.matrix.to_quaternion()@source_rest[p.name].inverted() for p in source.pose.bones}
  samples.append((rotations,(source.pose.bones['pelvis'].head.z-source_pelvis.z)*motion_scale))
 cache[name]=samples
common_axes=None;manifest=[]
for role in ['Utility','A','B']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(OUT/'Original'/(role+'.fbx')))
 s=bpy.context.scene;s.render.fps=30
 arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH')
 if arm.animation_data:arm.animation_data.action=None
 for p in arm.pose.bones:p.matrix_basis.identity()
 bpy.context.view_layer.update();factor=1.78/mesh.dimensions.z
 for v in mesh.data.vertices:v.co*=factor
 bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
 original={b.name:(b.head.copy(),b.tail.copy(),b.matrix.to_quaternion()) for b in arm.data.edit_bones}
 # Disconnect first: editing a connected parent's tail otherwise scales the child head twice.
 for b in arm.data.edit_bones:b.use_connect=False
 if common_axes is None:common_axes={name:data[2] for name,data in original.items()}
 for b in arm.data.edit_bones:
  head,tail,_=original[b.name];b.matrix=common_axes[b.name].to_matrix().to_4x4();b.head=head*factor;b.length=(tail-head).length*factor
 bpy.ops.object.mode_set(mode='OBJECT')
 rest={b.name:b.matrix_local.to_quaternion() for b in arm.data.bones}
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=arm
 mat=bpy.data.materials.new('Crew_'+role);mat.use_nodes=True
 texture=bpy.data.images.load(str(OUT/(role+'_BaseColor.png')))
 bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=texture
 mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.7
 mesh.data.materials.clear();mesh.data.materials.append(mat)
 kwargs=dict(use_selection=True,add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_scale_options='FBX_SCALE_ALL')
 bpy.ops.export_scene.fbx(filepath=str(OUT/('SK_Crew_'+role+'.fbx')),object_types={'ARMATURE','MESH'},bake_anim=False,**kwargs)
 if role=='Utility':
  for name,samples in cache.items():
   if not arm.animation_data:arm.animation_data_create()
   a=bpy.data.actions.new('A_Crew_'+name);arm.animation_data.action=a;a.use_fake_user=True
   for i,(rotations,bob) in enumerate(samples):
    desired={n:rotations[n]@rest[n] for n in rest}
    for p in arm.pose.bones:
     p.rotation_mode='QUATERNION';p.location=Vector((0,0,0));p.scale=Vector((1,1,1))
     parent=desired[p.parent.name]@rest[p.parent.name].inverted()@rest[p.name] if p.parent else rest[p.name]
     p.rotation_quaternion=parent.inverted()@desired[p.name]
     if p.name=='pelvis':p.location=rest[p.name].inverted()@Vector((0,0,bob))
    arm.pose.bones['root'].matrix_basis.identity()
    for p in arm.pose.bones:
     p.keyframe_insert('location',frame=i);p.keyframe_insert('rotation_quaternion',frame=i);p.keyframe_insert('scale',frame=i)
   for fc in a.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
   s.frame_start=0;s.frame_end=len(samples)-1;s.frame_set(0)
   bpy.ops.export_scene.fbx(filepath=str(OUT/('A_Crew_'+name+'.fbx')),object_types={'ARMATURE'},bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,**kwargs)
   manifest.append({'animation':name,'frames':len(samples)})
  arm.animation_data.action=bpy.data.actions['A_Crew_Idle'];s.frame_end=180;s.frame_set(0)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('Crew_'+role+'.blend')),compress=True)
(OUT/'AnimationManifest.json').write_text(json.dumps(manifest,indent=2))
print('CREW_EXPORT_COMPLETE')
