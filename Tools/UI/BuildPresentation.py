"""Repeatable background-only UI authoring. Does not start PIE or focus windows."""
import sys,json,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call,python
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/UIRefresh';OUT.mkdir(exist_ok=True)
def edit(code):
 result=OUT/'last_authoring.json'
 wrapper="import unreal,json,traceback\ntry:\n exec("+repr(code)+")\n json.dump({'ok':True},open("+repr(result.as_posix())+",'w'))\nexcept Exception:\n json.dump({'ok':False,'error':traceback.format_exc()},open("+repr(result.as_posix())+",'w'))\n"
 python('exec('+repr(wrapper)+')');r=json.loads(result.read_text());assert r['ok'],r
edit("import unreal,types,sys; m=types.ModuleType('ui_refresh');sys.modules['ui_refresh']=m;exec(open("+repr(str(ROOT/'Tools/UI/RefreshPresentation.py'))+").read(),m.__dict__)")
edit("""import unreal
from pathlib import Path
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
for weight in ['Regular','Bold']:
 p='/Game/Game/UI/Fonts/F_Arial'+weight
 if not unreal.EditorAssetLibrary.does_asset_exist(p):
  t=unreal.AssetImportTask();t.filename=str(root/'SourceArt/UI/Fonts'/('Arial'+weight+'.ttf'));t.destination_path='/Game/Game/UI/Fonts';t.destination_name='F_Arial'+weight;t.automated=True;t.save=True;t.factory=unreal.FontFileImportFactory();unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths
if not unreal.EditorAssetLibrary.does_asset_exist('/Game/Game/UI/Fonts/F_UI'):unreal.AssetToolsHelpers.get_asset_tools().create_asset('F_UI','/Game/Game/UI/Fonts',unreal.Font,unreal.FontFactory())
""")
value='(DefaultTypeface=(Fonts=((Name="Regular",Font=(FontFaceAsset=/Script/Engine.FontFace\'/Game/Game/UI/Fonts/F_ArialRegular.F_ArialRegular\')),(Name="Bold",Font=(FontFaceAsset=/Script/Engine.FontFace\'/Game/Game/UI/Fonts/F_ArialBold.F_ArialBold\')))))'
call('set_asset_property',path='/Game/Game/UI/Fonts/F_UI',property='CompositeFont',value=value);call('save_asset',path='/Game/Game/UI/Fonts/F_UI')
for path,parent in [('/Game/Game/UI/Cinematics/WBP_OpeningOverlay','CanvasPanel_0'),('/Game/Game/UI/Scene01/WBP_Scene01Objective','CanvasPanel_0'),('/Game/Game/UI/HUD/WBP_GameHUD','Root')]:
 widgets=call('list_widgets',path=path)['widgets']
 if not any(w['name']=='CinematicBand' for w in widgets):call('add_widget',path=path,widgetClass='Border',name='CinematicBand',parent=parent)
 call('set_widget_property',path=path,widget='CinematicBand',property='bIsVariable',value='true')
p='/Game/Game/Blueprints/UI/WBP_DirectorNotes';widgets=call('list_widgets',path=p)['widgets']
if not any(w['name']=='ClueScale' for w in widgets):call('add_widget',path=p,widgetClass='ScaleBox',name='ClueScale',parent='Content')
if not any(w['name']=='ClueImage' for w in widgets):call('add_widget',path=p,widgetClass='Image',name='ClueImage',parent='ClueScale')
call('set_widget_property',path=p,widget='ClueImage',property='bIsVariable',value='true')
for name in ['Objective','Controls']:call('set_widget_property',path='/Game/Game/UI/Scene01/WBP_Scene01Objective',widget=name,property='bIsVariable',value='true')
edit("import sys;sys.modules['ui_refresh'].layout()")
runpy.run_path(str(ROOT/'Tools/UI/PatchPresentation.py'),run_name='__main__')
print('UI_PRESENTATION_COMPLETE')
