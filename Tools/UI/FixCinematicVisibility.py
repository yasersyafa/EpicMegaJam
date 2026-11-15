"""Own subtitle visibility in presentation; preserve dialogue text and timing."""
import sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call, python
from BuildGameplaySystems import Graph

TARGETS = [
    ('/Game/Game/UI/HUD/WBP_GameHUD', 'SubtitleBox', 'LineText', [('ObjectiveText', 'Visible')]),
    ('/Game/Game/UI/Scene01/WBP_Scene01Objective', 'DialogueCaption', 'DialogueCaption', [('Objective', 'Collapsed'), ('Controls', 'Collapsed')]),
    ('/Game/Game/UI/Cinematics/WBP_OpeningOverlay', 'Caption', 'Caption', []),
]

def visible(g, name, previous, state, ref):
    g.fn(ref, 'Widget', 'SetVisibility', previous, InVisibility=state)
    g.wire(g.get(name), ref+'.self')
    return ref+'.then'

def apply():
    backup = Path('Saved/UIRefresh/VisibilityBackup')
    for path, caption, text, objectives in TARGETS:
        src = Path('Content') / (path.removeprefix('/Game/')+'.uasset')
        dst = backup / src.relative_to('Content')
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists(): shutil.copy2(src, dst)
        try:
            summary = call('read_blueprint_graph_summary', path=path, graphName='RefreshCinematicPresentation')
        except RuntimeError:
            call('create_function', path=path, functionName='RefreshCinematicPresentation', inputs=[])
            summary = call('read_blueprint_graph_summary', path=path, graphName='RefreshCinematicPresentation')
        entry = next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
        for node in summary['nodes']:
            if node['id'] != entry:
                call('remove_node', path=path, graphName='RefreshCinematicPresentation', nodeId=node['id'])
        g = Graph(path, 'RefreshCinematicPresentation', entry+'.then')
        g.fn('controller', 'GameplayStatics', 'GetPlayerController')
        g.fn('view', 'PlayerController', 'GetViewTarget'); g.wire('controller.ReturnValue', 'view.self')
        # Only a camera view counts: another actor or missing pawn is not a cutscene.
        g.fn('viewClass', 'GameplayStatics', 'GetObjectClass'); g.wire('view.ReturnValue', 'viewClass.Object')
        g.fn('cinematic', 'KismetMathLibrary', 'ClassIsChildOf', ParentClass='/Script/Engine.CameraActor')
        g.wire('viewClass.ReturnValue', 'cinematic.TestClass')
        g.fn('text', 'TextBlock', 'GetText'); g.wire(g.get(text), 'text.self')
        g.fn('empty', 'KismetTextLibrary', 'TextIsEmpty'); g.wire('text.ReturnValue', 'empty.InText')
        g.fn('nonempty', 'KismetMathLibrary', 'Not_PreBool'); g.wire('empty.ReturnValue', 'nonempty.A')
        g.fn('showCaption', 'KismetMathLibrary', 'BooleanAND')
        g.wire('cinematic.ReturnValue', 'showCaption.A'); g.wire('nonempty.ReturnValue', 'showCaption.B')
        band = 'showCaption.ReturnValue'
        if caption == 'SubtitleBox':
            content = 'nonempty.ReturnValue'
            for i, hint in enumerate(['CutHintText', 'SceneCompleteText']):
                g.fn('hint'+str(i), 'Widget', 'IsVisible'); g.wire(g.get(hint), 'hint'+str(i)+'.self')
                g.fn('content'+str(i), 'KismetMathLibrary', 'BooleanOR')
                g.wire(content, 'content'+str(i)+'.A'); g.wire('hint'+str(i)+'.ReturnValue', 'content'+str(i)+'.B')
                content = 'content'+str(i)+'.ReturnValue'
            g.fn('showBand', 'KismetMathLibrary', 'BooleanAND')
            g.wire('cinematic.ReturnValue', 'showBand.A'); g.wire(content, 'showBand.B')
            band = 'showBand.ReturnValue'
        elif caption == 'Caption':
            band = 'cinematic.ReturnValue'
        g.node('parallel', 'Sequence'); g.wire(g.entry, 'parallel.execute')
        a, b = g.branch(band, 'parallel.then_0')
        visible(g, 'CinematicBand', a, 'HitTestInvisible', 'bandVisible')
        visible(g, 'CinematicBand', b, 'Collapsed', 'hideBand')
        g.node('details', 'Sequence'); g.wire('parallel.then_1', 'details.execute')
        yes, no = g.branch('cinematic.ReturnValue', 'details.then_0')
        for i, (name, state) in enumerate(objectives):
            yes = visible(g, name, yes, 'Collapsed', 'hideObjective'+str(i))
            no = visible(g, name, no, state, 'restoreObjective'+str(i))
        caption_condition = 'showCaption.ReturnValue' if caption == 'Caption' else 'nonempty.ReturnValue'
        a, b = g.branch(caption_condition, 'details.then_1')
        visible(g, caption, a, 'HitTestInvisible', 'showText')
        visible(g, caption, b, 'Collapsed', 'hideText')
        g.build()
        event = call('read_blueprint_graph_summary', path=path, graphName='EventGraph')
        if not any(n['title']=='RefreshCinematicPresentation' for n in event['nodes']):
            tick = next((n for n in event['nodes'] if n['title']=='Event Tick'), None)
            g = Graph(path, 'EventGraph')
            if tick:
                previous = tick['id']+'.then'
                links = next((p['linkedTo'] for p in tick.get('connectedPins', []) if p['pin']=='then'), [])
            else:
                g.node('tick', 'Event', eventName='ReceiveTick'); previous='tick.then'; links=[]
            g.fn('refresh', path.split('/')[-1]+'_C', 'RefreshCinematicPresentation', previous)
            for link in links: g.wire('refresh.then', link['node']+'.'+link['pin'])
            g.build()
        result = call('compile_blueprint', path=path)
        assert result.get('errorCount')==0, result
        call('save_blueprint', path=path)
        print('VISIBILITY_FIXED', path, result, flush=True)
    # Initial templates must not paint a band before the first presentation tick.
    python("exec("+repr("import unreal\nfor p in "+repr([t[0] for t in TARGETS])+":\n bp=unreal.load_asset(p)\n for w in unreal.ObjectIterator(unreal.Widget):\n  if w.get_name()=='CinematicBand' and w.get_outer() and w.get_outer().get_outer()==bp:w.set_visibility(unreal.SlateVisibility.COLLAPSED)\n unreal.BlueprintEditorLibrary.compile_blueprint(bp)\n unreal.EditorAssetLibrary.save_loaded_asset(bp,False)\n")+")")

if __name__ == '__main__': apply()
