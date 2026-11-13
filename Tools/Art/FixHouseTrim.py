import unreal,os,json
src=open(os.path.join(unreal.Paths.project_dir(),'Tools/Art/StageHouseRemaster.py')).read().split('\ntry:\n')[0]
src=src.replace("out={};slotmap=", "entries=[e for e in entries if e['category']=='Architecture'];out={};slotmap=")
exec(compile(src,'StageHouseRemaster-import-only','exec'))
S.clear_actor_selection_set()
folder=ROOT+'/Materials/Instances/'
palette={
 'Timber_AgedIvory':load(folder+'Remaster/MI_House_Timber_AgedIvory'),
 'Timber_PanelInset':load(folder+'Remaster/MI_House_Timber_PanelInset'),
 'Plaster_Sage':load(folder+'Remaster/MI_House_Plaster_Sage'),
 'Brass':load(folder+'Props/MI_House_Prop_Shelf_Gunmetal'),
 'Glass':load(folder+'Props/MI_House_Prop_Bulb')}
os.environ['HOUSE_REMASTER_REIMPORT']='1'
try:
 meshes,entries=import_meshes(palette)
 R['success']=True;R['reimported_rooms']=[e['room'] for e in entries]
finally:os.environ.pop('HOUSE_REMASTER_REIMPORT',None)
R['saved']=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
with open(os.path.join(P,'Saved/HouseTrimFixReport.json'),'w') as f:json.dump(R,f,indent=2)
unreal.log('CODEX_TRIM_FIX '+str(R['success']))
