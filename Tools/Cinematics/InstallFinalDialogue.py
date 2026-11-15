"""Final pickup and confession captions from the v3 screenplay."""
import json
import unreal
t=unreal.load_asset('/Game/Game/Data/Dialogue/DT_Dialogue')
rows=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(t))
rows=[r for r in rows if not r['Name'].startswith('FINAL_')]
def add(key,speaker,line,duration=None):
 rows.append(dict(Name='FINAL_'+key,Speaker=speaker,SubtitleText=line,VoiceSound='None',
                  DialogueCategory='BEHIND_SCENES',SceneID='FINAL',
                  Duration=duration or max(2.5,len(line.split())*.47)))
pickup=[('SURYA','Everyone, back on set, please. One last pickup.'),('CREW A','Copy that.'),
 ('CREW B','All set, Director.'),('SURYA','Thank you, everyone. Nearly done.'),
 ('MAYA','Can I ask a favour?'),('SURYA','Go on.'),
 ('MAYA','Could we leave the camera running for a moment? I would like to try something for the ending.'),
 ('SURYA','An improvisation?'),('MAYA','Something like that.'),
 ('SURYA','Alright. Let us give her a moment.'),('CREW C','Camera ready.'),
 ('SURYA','And... action.'),('MAYA','Okay.'),('MAYA','I think I am ready.')]
confession=[('MAYA','There is something I have not told you.'),('MAYA','The woman who died here...'),
 ('MAYA','Her name was Evelyn.'),('MAYA','She was my sister.'),
 ('MAYA','They said it was an accident.'),
 ('MAYA','But there were four people in this house who knew what happened.'),
 ('MAYA','They made a film out of it.'),('MAYA','Then they made sure nobody would ever see it.'),
 ('MAYA','I thought I wanted them to tell the truth.'),('MAYA','I thought that would be enough.'),
 ('MAYA','It was not.')]
reveal=[('MAYA','There is one more thing.'),('MAYA','Remember what I said about the frame?'),
 ('MAYA (OFF CAMERA)','Now you have seen everything.')]
for section,lines in [('PICKUP',pickup),('CONFESSION',confession),('REVEAL',reveal)]:
 for i,(speaker,line) in enumerate(lines,1):add(f'{section}_{i:02d}',speaker,line)
assert unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(t,json.dumps(rows,ensure_ascii=False))
unreal.EditorAssetLibrary.save_loaded_asset(t,False)
print('FINAL_DIALOGUE_SAVED',len(rows))
