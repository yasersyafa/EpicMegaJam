"""Apply focused subtitle and Maya performance fixes in the isolated editor."""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call, python
from BuildGameplaySystems import Graph

HUD = '/Game/Game/UI/HUD/WBP_GameHUD'
INTRO = '/Game/Game/UI/Scene01/WBP_Scene01Objective'
MANAGER = '/Game/Game/Blueprints/Film/BP_FilmSceneManager'


def backup(path):
    source = Path('Content') / (path.removeprefix('/Game/') + '.uasset')
    target = Path('Saved/QA/FeedbackFixBackup') / source.relative_to('Content')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)


def fix_hide():
    summary = call('read_blueprint_graph_summary', path=HUD, graphName='HideSubtitle')
    visibility = next(n for n in summary['nodes'] if n['title'] == 'Set Visibility')
    graph = Graph(HUD, 'HideSubtitle')
    previous = visibility['id'] + '.then'
    for widget in ('LineText', 'SpeakerText'):
        ref = 'clear' + widget
        graph.fn(ref, 'TextBlock', 'SetText', previous, InText='')
        graph.wire(graph.get(widget), ref + '.self')
        previous = ref + '.then'
    graph.build()
    result = call('compile_blueprint', path=HUD)
    assert result.get('errorCount') == 0, result
    call('save_blueprint', path=HUD)


def fix_assets():
    code = r'''
import unreal
from pathlib import Path
for path in ['/Game/Game/UI/HUD/WBP_GameHUD','/Game/Game/UI/Scene01/WBP_Scene01Objective']:
 bp=unreal.load_asset(path)
 for w in unreal.ObjectIterator(unreal.Widget):
  if not w.get_outer() or w.get_outer().get_outer()!=bp: continue
  if w.get_name() in ('LineText','SpeakerText','DialogueCaption'):
   w.set_text('')
   if w.get_name() in ('LineText','DialogueCaption'):
    font=w.get_editor_property('font');font.size=23;w.set_editor_property('font',font)
  if w.get_name()=='SubtitleBox':
   slot=w.get_editor_property('slot');slot.set_auto_size(False);slot.set_offsets(unreal.Margin(90,-150,90,90))
  if w.get_name() in ('LineText','SpeakerText'):
   w.get_editor_property('slot').set_editor_property('horizontal_alignment',unreal.HorizontalAlignment.H_ALIGN_FILL)
   if w.get_name()=='LineText':w.set_editor_property('wrap_text_at',0.0)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
for folder in ('L01','L02'):
 for path in unreal.EditorAssetLibrary.list_assets('/Game/Game/Cinematics/'+folder,False,False):
  seq=unreal.load_asset(path)
  if not isinstance(seq,unreal.LevelSequence):continue
  changed=False
  for binding in seq.get_bindings():
   if binding.get_name()!='MAYA_Take':continue
   for track in binding.get_tracks():
    if not isinstance(track,unreal.MovieSceneSkeletalAnimationTrack):continue
    for section in track.get_sections():
     params=section.get_editor_property('params');anim=params.get_editor_property('animation')
     if not anim or anim.get_name() not in ('A_Maya_Hesitate','A_Maya_LookAtDirector','A_Maya_LookAround','A_Maya_Inspect'):continue
     rate=params.get_editor_property('play_rate')
     old=rate.to_fixed_play_rate()
     if old<=1.25:continue
     rate.set_fixed_play_rate(1.0);params.set_editor_property('play_rate',rate);section.set_editor_property('params',params)
     print('NORMALIZED_ANIMATION',seq.get_name(),anim.get_name(),old)
     changed=True
  if changed:unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
'''
    python('exec(' + repr(code) + ')')


def fix_action_order():
    # Opening sequence must own the first ACTION frame before dialogue begins.
    backup(MANAGER)
    call('remove_node', path=MANAGER, graphName='EventGraph', nodeId='2947A5C1')
    graph = Graph(MANAGER, 'EventGraph')
    graph.wire('98AD7EF8.then', 'E0C03F82.execute')
    graph.fn('introAfterCamera', 'BP_FilmSceneManager_C', 'PlayDialogueList', '35DDBEE3.else')
    graph.wire('CA8BDC37.IntroDialogueIDs', 'introAfterCamera.IDs')
    graph.build()
    result = call('compile_blueprint', path=MANAGER)
    assert result.get('errorCount') == 0, result
    call('save_blueprint', path=MANAGER)


if __name__ == '__main__':
    for path in (HUD, INTRO): backup(path)
    if '--assets-only' not in sys.argv: fix_hide()
    fix_assets()
    if '--action-only' in sys.argv: fix_action_order()
