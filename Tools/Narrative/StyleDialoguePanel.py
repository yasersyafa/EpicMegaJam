"""Apply the film's dialogue styling to its shared UMG panel, in the editor."""
import binascii
import struct
import zlib
from pathlib import Path

import unreal


PANEL = "/Game/Game/UI/Narrative/WBP_DialoguePanel"
ART = "/Game/Game/UI/Narrative/Textures/T_Dialogue_Vignette"
ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))


def template(asset, name):
    path = f"{asset}.{asset.rsplit('/', 1)[-1]}:WidgetTree.{name}"
    return unreal.load_object(None, path)


def make_gradient():
    """Small original screen-space alpha ramp. The image always fills the width."""
    source = ROOT / "SourceArt/UI/T_Dialogue_Vignette.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    width, height = 64, 256
    stops = [(0, 0), (.15, .08), (.30, .32), (.46, .65),
             (.62, .80), (.80, .86), (1, .91)]
    rows = bytearray()
    for y in range(height):
        t = y / (height - 1)
        low, high = next((a, b) for a, b in zip(stops, stops[1:]) if t <= b[0])
        fraction = (t - low[0]) / (high[0] - low[0])
        alpha = low[1] + fraction * (high[1] - low[1])
        rows.append(0)
        for x in range(width):
            edge = abs(2 * x / (width - 1) - 1) ** 2
            rows.extend((12, 14, 18, round(255 * min(1, alpha * (1 + .055 * edge)))))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", binascii.crc32(tag + data))

    source.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                       + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path, task.destination_name = ART.rsplit("/", 1)
    task.automated = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(ART)
    assert texture
    texture.set_editor_properties({
        "compression_settings": unreal.TextureCompressionSettings.TC_EDITOR_ICON,
        "lod_group": unreal.TextureGroup.TEXTUREGROUP_UI,
        "mip_gen_settings": unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS,
        "address_x": unreal.TextureAddress.TA_CLAMP, "address_y": unreal.TextureAddress.TA_CLAMP,
    })
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def anchor(widget, minimum, maximum, offsets=(0, 0, 0, 0)):
    lo = unreal.Vector2D(*minimum)
    hi = unreal.Vector2D(*maximum)
    widget.slot.set_anchors(unreal.Anchors(minimum=lo, maximum=hi))
    widget.slot.set_alignment(unreal.Vector2D(0, 0))
    widget.slot.set_offsets(unreal.Margin(*offsets))


def style():
    # Set instance fields on the widget-tree templates. Properties written to the
    # generated class instead of these objects are lost on the next Blueprint compile.
    bp = unreal.load_asset(PANEL)
    bp.modify()
    image = template(PANEL, "Vignette")
    image.modify()
    image.set_brush_from_texture(make_gradient(), False)
    anchor(image, (0, .57), (1, 1))
    column = template(PANEL, "DialogueColumn")
    column.modify()
    anchor(column, (.12, .748), (.88, .99))
    for name, size, face, rgba, tracking in [
        ("Speaker", 24, "Bold", (.98, .735, .365, 1), 35),
        ("LineBody", 30, "Regular", (.973, .958, .925, 1), 0),
    ]:
        widget = template(PANEL, name)
        widget.modify()
        font = widget.get_editor_property("font")
        font.set_editor_properties({"size": size, "typeface_font_name": face, "letter_spacing": tracking})
        widget.set_font(font)
        widget.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(*rgba)))
        widget.set_editor_property("justification", unreal.TextJustify.CENTER)
        widget.set_auto_wrap_text(True)
        widget.set_shadow_offset(unreal.Vector2D(0, 1.25))
        widget.set_shadow_color_and_opacity(unreal.LinearColor(0, 0, 0, .72))
        widget.set_text("")
        widget.slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
    divider = template(PANEL, "Divider")
    divider.modify()
    divider.set_desired_size_override(unreal.Vector2D(1, 1))
    divider.set_color_and_opacity(unreal.LinearColor(.71, .60, .42, .35))
    divider.slot.set_padding(unreal.Margin(0, 5, 0, 8))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, False)

    for path, raw in [
        ("/Game/Game/UI/Scene01/WBP_Scene01Objective", "DialogueCaption"),
        ("/Game/Game/UI/Cinematics/WBP_OpeningOverlay", "Caption"),
    ]:
        parent = unreal.load_asset(path)
        child = template(path, "DialoguePanel")
        if child:
            parent.modify()
            child.modify()
            anchor(child, (0, 0), (1, 1))
            child.set_visibility(unreal.SlateVisibility.COLLAPSED)
            old = template(path, raw)
            old.modify()
            old.set_visibility(unreal.SlateVisibility.COLLAPSED)
            unreal.BlueprintEditorLibrary.compile_blueprint(parent)
            unreal.EditorAssetLibrary.save_loaded_asset(parent, False)


style()
