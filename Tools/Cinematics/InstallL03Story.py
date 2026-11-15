"""Scene 03 rules and screenplay lines for the main graybox director."""
import json
import unreal

root='/Game/Game'
src=root+'/Data/Scenes/DA_SceneConfig_L02'
dst=root+'/Data/Scenes/DA_SceneConfig_L03'
da=unreal.load_asset(dst) or unreal.EditorAssetLibrary.duplicate_asset(src,dst)
assert da
def put(obj,key,value):obj.set_editor_property(key,value)
put(da,'SceneID',unreal.Name('L03'))
put(da,'DisplayName','THE LAST SCENE')
put(da,'NextSceneID',unreal.Name('FINAL'))
put(da,'ObjectiveText','SCENE 3 - THE LAST SCENE: match the chair and lamp to Evelyn\'s reference photo. [F] ACTION')
put(da,'DirectorNotesText','HIDDEN ROOM  /  Study the photograph\nMatch the chair and light before ACTION.')
put(da,'OpeningSequence',unreal.load_asset(root+'/Cinematics/L03/LS_L03_Opening'))
put(da,'IntroDialogueIDs',[unreal.Name('L03_APPROACH_01'),unreal.Name('L03_APPROACH_02')])
put(da,'SuccessDialogueIDs',[unreal.Name('L03_AFTER_0'+str(i)) for i in range(1,7)])
put(da,'InterludeDialogueIDs',[unreal.Name('L03_INTERLUDE_0'+str(i)) for i in range(1,6)])
put(da,'TransitionDialogueIDs',[])
put(da,'EarlyCutDialogueID',unreal.Name('L03_CUT_EARLY'))
flagname='FlagName_2_031A26F5454CA0E1000B4A8F1CA56A1D'
ruletype='RuleType_4_083AF5F44D144509CDBBBEA7E2EB8B70'
placements='Placements_6_290FA8AD4F48E680E74615A51740CD4F'
propid='PropID_2_B7CDC8FF45EED9FE3D7F27A626E9174E'
areaid='AreaID_4_2FB0AFF24B5BA70844DCC78B960FD16D'
rules=list(da.get_editor_property('FlagRules'));require=rules[2].get_editor_property(ruletype)
for r,name,prop,area in [(rules[0],'bChairMatched','WoodenChair','L03_ChairReference'),
                         (rules[1],'bPhotoLit','StandingLamp','L03_LampReference')]:
 p=list(rules[2].get_editor_property(placements))[0]
 p.set_editor_property(propid,unreal.Name(prop));p.set_editor_property(areaid,unreal.Name(area))
 r.set_editor_property(flagname,unreal.Name(name));r.set_editor_property(ruletype,require)
 r.set_editor_property(placements,[p])
put(da,'FlagRules',rules[:2])
outid='OutcomeID_2_079AF04F458E1F5CA991BE82A7C10B98'
trigger='TriggerIfAnyFalse_6_AAFFCD26476C4432B51AB1A43EC7E060'
seqkey='OutcomeSequence_8_26AFF9494070F390915316BEFABD599B'
performance='PerformanceDialogueIDs_12_AF91D8264EDA9817080D1C9B7D0F358D'
hints='HintDialogueIDs_14_D4A9418A4D1320C6F13AACB1C9CE42F1'
cut='CutDialogueID_16_229A41E64C80FDB34C5E868253150649'
out=list(da.get_editor_property('OutcomeRules'))
for r,name,flag,seq,lines,hint,cutid in [
 (out[0],'CHAIR','bChairMatched','LS_L03_ChairWrong',['L03_FAIL_CHAIR'],['L03_HINT_CHAIR'],'L03_CUT_CHAIR'),
 (out[1],'DARK','bPhotoLit','LS_L03_LampWrong',['L03_FAIL_LAMP'],['L03_HINT_LAMP'],'L03_CUT_LAMP'),
 (out[2],'PERFECT',None,'LS_L03_Perfect',[f'L03_LARAS_0{i}' for i in range(1,6)],[], '')]:
 r.set_editor_property(outid,unreal.Name(name))
 r.set_editor_property(trigger,[unreal.Name(flag)] if flag else [])
 r.set_editor_property(seqkey,unreal.load_asset(root+'/Cinematics/L03/'+seq))
 r.set_editor_property(performance,[unreal.Name(x) for x in lines])
 r.set_editor_property(hints,[unreal.Name(x) for x in hint])
 r.set_editor_property(cut,unreal.Name(cutid))
put(da,'OutcomeRules',out)
unreal.EditorAssetLibrary.save_loaded_asset(da,False)

table=unreal.load_asset(root+'/Data/Dialogue/DT_Dialogue')
rows=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
rows=[r for r in rows if not r['Name'].startswith(('L03_','FINAL_'))]
def add(id,speaker,line,category='BEHIND_SCENES',duration=None):
 rows.append(dict(Name=id,Speaker=speaker,SubtitleText=line,VoiceSound='None',
                  DialogueCategory=category,SceneID='L03',Duration=duration or max(2.6,len(line.split())*.43)))
for i,s,l in [(1,'CREW A','This is the last set, sir.'),(2,'MAYA','The photograph is our reference?')]:add(f'L03_APPROACH_0{i}',s,l)
for i,l in enumerate(['So this is where it leads.','This room...','It\'s exactly the same.',
                      'Someone was here.','What happened to them?'],1):add(f'L03_LARAS_0{i}','MAYA (as LARAS)',l,'IN_FILM')
for id,s,l in [('L03_FAIL_CHAIR','MAYA','Sorry, this does not quite match the reference.'),
 ('L03_HINT_CHAIR','SURYA (THOUGHT)','The continuity is off. I should check the chair placement.'),
 ('L03_CUT_CHAIR','SURYA','CUT! Let us put the chair where it was in the photograph.'),
 ('L03_FAIL_LAMP','MAYA','Could we get a little more light here?'),
 ('L03_HINT_LAMP','SURYA (THOUGHT)','The reveal needs to read properly. I should adjust the lamp.'),
 ('L03_CUT_LAMP','SURYA','CUT! Bring the lamp closer to the photograph.'),
 ('L03_CUT_EARLY','SURYA','CUT! Hold on, I need to tidy up the scene.')]:add(id,s,l)
for i,s,l in [(1,'SURYA','CUT! Beautiful. That is our last scene.'),(2,'MAYA','Really? We are finished?'),
 (3,'SURYA','Nearly. Just a final pickup.'),(4,'MAYA','What do you need?'),
 (5,'SURYA','One final shot to close the film.'),(6,'MAYA','Of course.')]:add(f'L03_AFTER_0{i}',s,l)
for i,l in enumerate(['I suppose that is why endings matter so much.',
 'They make you look at everything that came before...', '...a little differently.',
 'Sometimes all it takes is one last shot.','Just one.'],1):add(f'L03_INTERLUDE_0{i}','MAYA',l,'RECORDING')
assert unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False))
unreal.EditorAssetLibrary.save_loaded_asset(table,False)
print('L03_CONFIG_DIALOGUE_SAVED',len(rows))
