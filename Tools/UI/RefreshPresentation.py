"""Editor authoring only: shared UI font, cinematic text layout, and illustrated held notes."""
import unreal,json,shutil,hashlib
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()));OUT=ROOT/'Saved/UIRefresh';OUT.mkdir(exist_ok=True)
UI=['/Game/Game/UI/Cinematics/WBP_OpeningOverlay','/Game/Game/UI/Scene01/WBP_Scene01Objective','/Game/Game/UI/HUD/WBP_GameHUD','/Game/Game/Blueprints/UI/WBP_DirectorNotes','/Game/Game/UI/Menus/WBP_MainMenu','/Game/Game/UI/Menus/WBP_PauseMenu','/Game/Game/UI/Menus/WBP_Credits']
OWNED=UI+['/Game/Game/Blueprints/UI/BP_InteractionHUD','/Game/Game/Blueprints/Film/BP_FilmSceneManager','/Game/Game/Data/Scenes/DA_SceneConfig_L01','/Game/Game/Data/Scenes/DA_SceneConfig_L02']
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
for path in OWNED:
 src=ROOT/'Content'/Path(path.removeprefix('/Game/')).with_suffix('.uasset');dest=OUT/'Backup'/src.relative_to(ROOT/'Content');dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():shutil.copy2(src,dest)
protected=OUT/'protected.json'
if not protected.exists():
 files=list((ROOT/'Content/Game/Cinematics').rglob('*.uasset'))+[ROOT/'Content/Game/Levels/SB_GrayBox.umap',ROOT/'Content/Game/Blueprints/Player/BP_PlayerCharacter.uasset']
 protected.write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
for i in [1,2]:
 task=unreal.AssetImportTask();task.filename=str(ROOT/f'SourceArt/UI/DirectorNotes/Storyboard_L0{i}.png');task.destination_path='/Game/Game/UI/Notes/Textures';task.destination_name=f'T_Storyboard_L0{i}';task.automated=True;task.replace_existing=True;task.save=True
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
 tex=unreal.load_asset(task.imported_object_paths[0]);tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON);tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS);unreal.EditorAssetLibrary.save_loaded_asset(tex,False)
 da=unreal.load_asset(f'/Game/Game/Data/Scenes/DA_SceneConfig_L0{i}');da.set_editor_property('ReferenceImage',tex);da.set_editor_property('DirectorNotesText','Entrance  /  Odd wall' if i==1 else 'Floor plan  /  Sealed wall');unreal.EditorAssetLibrary.save_loaded_asset(da,False)
def widgets(bp):return {w.get_name():w for w in unreal.ObjectIterator(unreal.Widget) if w.get_outer() and w.get_outer().get_outer()==bp}
def anchored(w,left,top,right,bottom,minimum=(0,1),maximum=(1,1),alignment=(0,0),z=10):
 slot=w.get_editor_property('slot');assert isinstance(slot,unreal.CanvasPanelSlot),w.get_name()
 slot.set_anchors(unreal.Anchors(minimum=unreal.Vector2D(*minimum),maximum=unreal.Vector2D(*maximum)));slot.set_alignment(unreal.Vector2D(*alignment));slot.set_offsets(unreal.Margin(left=left,top=top,right=right,bottom=bottom));slot.set_z_order(z)
def font(w,size=None,bold=None):
 info=w.get_editor_property('font');info.set_editor_property('font_object',unreal.load_asset('/Game/Game/UI/Fonts/F_UI'));weight=('Bold' in str(info.get_editor_property('typeface_font_name'))) if bold is None else bold
 info.set_editor_property('typeface_font_name','Bold' if weight else 'Regular')
 if size is not None:info.set_editor_property('size',size)
 w.set_font(info)
def layout():
 for path in UI:
  bp=unreal.load_asset(path);ww=widgets(bp)
  for w in ww.values():
   if isinstance(w,unreal.TextBlock):font(w)
  if 'CinematicBand' in ww:
   band=ww['CinematicBand'];band.set_brush_color(unreal.LinearColor(0,0,0,1));band.set_visibility(unreal.SlateVisibility.HIT_TEST_INVISIBLE);anchored(band,0,-160,0,160,z=1)
  if path.endswith('WBP_OpeningOverlay'):
   caption=ww['Caption'];anchored(caption,120,-144,120,106);caption.set_editor_property('justification', unreal.TextJustify.CENTER);caption.set_auto_wrap_text(True);font(caption,26,False)
   anchored(ww['SkipHint'],0,-34,1000,24,minimum=(.5,1),maximum=(.5,1),alignment=(.5,0));font(ww['SkipHint'],14,False)
  if path.endswith('WBP_Scene01Objective'):
   caption=ww['DialogueCaption'];anchored(caption,120,-144,120,106);caption.set_editor_property('justification', unreal.TextJustify.CENTER);caption.set_auto_wrap_text(True);font(caption,26,False)
  if path.endswith('WBP_GameHUD'):
   anchored(ww['SubtitleBox'],120,-152,120,106);ww['SpeakerText'].set_editor_property('justification', unreal.TextJustify.CENTER);ww['LineText'].set_editor_property('justification', unreal.TextJustify.CENTER);ww['LineText'].set_auto_wrap_text(True);font(ww['SpeakerText'],17,True);font(ww['LineText'],26,False)
   anchored(ww['CutHintText'],0,-34,1000,24,minimum=(.5,1),maximum=(.5,1),alignment=(.5,0));font(ww['CutHintText'],14,False)
   anchored(ww['SceneCompleteText'],0,-34,1000,24,minimum=(.5,1),maximum=(.5,1),alignment=(.5,0));font(ww['SceneCompleteText'],14,True)
  if path.endswith('WBP_DirectorNotes'):
   content=ww['Content'];content.clear_children()
   order=['Header','SceneTitle','Rule','ClueScale','Objective','Todo1','Todo2','Todo3','Footer']
   for name in order:
    w=ww[name];slot=content.add_child_to_vertical_box(w);slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
    if name=='ClueScale':slot.set_size(unreal.SlateChildSize(value=1,size_rule=unreal.SlateSizeRule.FILL));slot.set_padding(unreal.Margin(top=10,bottom=10))
   ww['Paper'].set_padding(unreal.Margin(left=20,top=24,right=20,bottom=20));ww['Paper'].set_brush_color(unreal.LinearColor(.90,.85,.74,1))
   ww['Header'].set_text("DIRECTOR'S NOTES");font(ww['Header'],20,True)
   ww['SceneTitle'].set_text('SCENE 01 / THE ARRIVAL');font(ww['SceneTitle'],17,True)
   ww['ClueScale'].set_stretch(unreal.Stretch.SCALE_TO_FIT);ww['ClueImage'].set_brush_from_texture(unreal.load_asset('/Game/Game/UI/Notes/Textures/T_Storyboard_L01'),True)
   ww['Objective'].set_text('Entrance  /  Odd wall');font(ww['Objective'],16,False);ww['Objective'].set_editor_property('justification', unreal.TextJustify.CENTER);ww['Objective'].set_auto_wrap_text(True)
   for name in ['Todo1','Todo2','Todo3']:ww[name].set_visibility(unreal.SlateVisibility.COLLAPSED)
   ww['Footer'].set_text('TAB');font(ww['Footer'],11,False)
  unreal.BlueprintEditorLibrary.compile_blueprint(bp);unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
 print('UI_FONT_AND_LAYOUT_SAVED')

