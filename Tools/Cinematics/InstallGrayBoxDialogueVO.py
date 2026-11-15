"""Import cut voice lines and bind only previously silent production dialogue rows."""
import unreal,json,shutil
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/GrayBoxAudio';OUT.mkdir(exist_ok=True)
clips=json.loads((OUT/'PreparedDialogue.json').read_text())['clips']
table=unreal.load_asset('/Game/Game/Data/Dialogue/DT_Dialogue');assert table
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
backup=OUT/'Backup/DT_Dialogue_before_vo.uasset';backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():shutil.copy2(ROOT/'Content/Game/Data/Dialogue/DT_Dialogue.uasset',backup)
tasks=[]
for clip in clips:
 if unreal.EditorAssetLibrary.does_asset_exist(clip['asset']):continue
 task=unreal.AssetImportTask();task.filename=clip['wav'];task.destination_path='/Game/Game/Audio/VoiceOver';task.destination_name=clip['asset'].split('/')[-1];task.automated=True;task.replace_existing=True;task.save=True;tasks.append(task)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
assert all(x.imported_object_paths for x in tasks)
for clip in clips:
 sound=unreal.load_asset(clip['asset']);assert sound,clip['asset']
 assert sound.get_editor_property('duration')>.1,clip['asset']
rows=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
by={x['id']:x for x in clips}
changed=[]
for row in rows:
 key=row['Name'];clip=by.get(key)
 if not clip or key.startswith('INTRO_') or key.startswith('CUT_'):continue
 if row['VoiceSound']!='None':
  assert clip['asset'] in row['VoiceSound'],(key,row['VoiceSound'])
  continue
 row['VoiceSound']="/Script/Engine.SoundWave'"+clip['asset']+'.'+clip['asset'].split('/')[-1]+"'"
 row['Duration']=max(float(row['Duration']),clip['duration']+.15)
 changed.append(key)
assert len(changed) in (0,27),(len(changed),changed)
assert unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False))
assert unreal.EditorAssetLibrary.save_loaded_asset(table,False)
(OUT/'DialogueInstallation.json').write_text(json.dumps({'imported':len(clips),'rows':changed},indent=2))
print('DIALOGUE_VO_IMPORTED',len(clips),'ROWS',len(changed))
