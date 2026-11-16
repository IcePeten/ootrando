import json

from PIL import Image

import bntx
import byml
from game import ROOT

OUT = ROOT / "ui" / "maps"
CAPTURE = "Game/MapCaptureInfo/MapCaptureInfo.game__MapCaptureInfo.bgyml"
MENU = "Game/MapMenuInfo/MapMenuInfo.game__ui__MapMenuInfo.bgyml"
MAX_SIDE = 1024
PAD = 12


def _texture_path(game, name, dungeon):
    if dungeon:
        path = f"UI/CustomTex/Map/Dungeon/{name}_All.bntx.zs"
    else:
        path = f"UI/CustomTex/Map/Field/{name}.bntx.zs"
    return path if path in game.files else None


def _decode(game, path):
    tex = bntx.Texture(game.read(path))
    img = Image.fromarray(tex.read_level(0), "RGBA")
    scale = MAX_SIDE / max(img.size)
    if scale < 1:
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    return img


def export(game, force=False):
    index = OUT / "maps.json"
    if index.exists() and not force:
        return json.loads(index.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    captures = byml.loads(game.read(CAPTURE))[0]["MapCaptureParamArray"]
    menus = byml.loads(game.read(MENU))[0]["MapMenuParamArray"]
    out = {}
    for menu, cap in zip(menus, captures):
        area = menu["LocationName"]
        if "CameraPos" not in cap or "Height" not in cap:
            continue
        dungeon = bool(cap.get("IsDungeon"))
        for age, name in zip(("Child", "Adult"), menu.get("TextureName", [])):
            path = name and _texture_path(game, name, dungeon)
            if not path:
                continue
            file = f"{name}.png"
            img = _decode(game, path)
            full_w, full_h = img.size
            box = img.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox() or (0, 0, full_w, full_h)
            box = (max(0, box[0] - PAD), max(0, box[1] - PAD), min(full_w, box[2] + PAD), min(full_h, box[3] + PAD))
            img = img.crop(box)
            img.save(OUT / file)
            out.setdefault(area, {})[age] = {
                "image": f"maps/{file}", "cx": cap["CameraPos"]["X"], "cz": cap["CameraPos"]["Z"],
                "span": cap["Height"], "full_w": full_w, "full_h": full_h,
                "x0": box[0], "y0": box[1], "w": img.width, "h": img.height,
            }
    index.write_text(json.dumps(out, indent=1))
    return out
