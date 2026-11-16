import colorsys
import random

import numpy as np

from bntx import Texture

TUNIC_COLORS = {
    "Kokiri Green": (0x1E, 0x69, 0x1B), "Goron Red": (0x64, 0x14, 0x00), "Zora Blue": (0x00, 0x3C, 0x64),
    "Black": (0x30, 0x30, 0x30), "White": (0xF0, 0xF0, 0xFF), "Azure Blue": (0x13, 0x9E, 0xD8),
    "Vivid Cyan": (0x13, 0xE9, 0xD8), "Light Red": (0xF8, 0x7C, 0x6D), "Fuchsia": (0xFF, 0x00, 0xFF),
    "Purple": (0x95, 0x30, 0x80), "Majora Purple": (0x40, 0x00, 0x40), "Twitch Purple": (0x64, 0x41, 0xA5),
    "Purple Heart": (0x8A, 0x2B, 0xE2), "Persian Rose": (0xFF, 0x14, 0x93), "Dirty Yellow": (0xE0, 0xD8, 0x60),
    "Blush Pink": (0xF8, 0x6C, 0xF8), "Hot Pink": (0xFF, 0x69, 0xB4), "Rose Pink": (0xFF, 0x90, 0xB3),
    "Orange": (0xE0, 0x79, 0x40), "Gray": (0xA0, 0xA0, 0xB0), "Gold": (0xD8, 0xB0, 0x60),
    "Silver": (0xD0, 0xF0, 0xFF), "Beige": (0xC0, 0xA0, 0xA0), "Teal": (0x30, 0xD0, 0xB0),
    "Blood Red": (0x83, 0x03, 0x03), "Blood Orange": (0xFE, 0x4B, 0x03), "Royal Blue": (0x40, 0x00, 0x90),
    "Sonic Blue": (0x50, 0x90, 0xE0), "NES Green": (0x00, 0xD0, 0x00), "Dark Green": (0x00, 0x25, 0x18),
    "Lumen": (0x50, 0x8C, 0xF0),
}

GAUNTLET_COLORS = {
    "Silver": (0xFF, 0xFF, 0xFF), "Gold": (0xFE, 0xCF, 0x0F), "Black": (0x00, 0x00, 0x06),
    "Green": (0x02, 0x59, 0x18), "Blue": (0x06, 0x02, 0x5A), "Bronze": (0x60, 0x06, 0x02),
    "Red": (0xFF, 0x13, 0x0F), "Sky Blue": (0x02, 0x5D, 0xB0), "Pink": (0xFA, 0x6A, 0x90),
    "Magenta": (0xE0, 0x10, 0x8A), "Orange": (0xDA, 0x38, 0x00), "Lime": (0x5B, 0xA8, 0x06),
    "Purple": (0x80, 0x00, 0x8C),
}

SLOTS = {
    "kokiri_tunic": {
        "label": "Kokiri Tunic", "palette": TUNIC_COLORS, "default": "Kokiri Green", "hue": (110, 58),
        "textures": ["Angin_Tile_A_Alb", "Angin_Tile_A_Dark_Alb", "Mt_Angin_Acs_Player_Adult_Alb",
                     "Mt_PantsParts_Player_Child_Alb"],
    },
    "kokiri_under": {
        "label": "Kokiri Trim & Under Layer", "palette": TUNIC_COLORS, "default": "Kokiri Green", "hue": (110, 58),
        "match": "kokiri_tunic",
        "textures": ["Mt_Vest_Player_Adult_Alb", "Mt_Vest_Player_Child_Alb", "Mt_Cloth_Parts_Player_Child_Alb"],
    },
    "goron_tunic": {
        "label": "Goron Tunic", "palette": TUNIC_COLORS, "default": "Goron Red", "hue": (0, 22),
        "textures": ["Mt_Angin_Armor_Adult_Goron_Alb", "Mt_Vest_Armor_Adult_Goron_Alb"],
    },
    "zora_tunic": {
        "label": "Zora Tunic", "palette": TUNIC_COLORS, "default": "Zora Blue", "hue": (215, 40),
        "textures": ["Mt_Angin_Acs_Armor_Adult_Zora_Alb", "Mt_Angin_Armor_Adult_Zora_Alb",
                     "Mt_Vest_Armor_Adult_Zora_Alb", "Mt_Parts_Armor_Adult_Zora_Alb"],
    },
    "silver_gauntlets": {
        "label": "Silver Gauntlets", "palette": GAUNTLET_COLORS, "default": "Silver", "hue": None,
        "textures": ["Mt_Silver_Armor_Adult_Gauntlet_Silver_Alb"],
    },
    "golden_gauntlets": {
        "label": "Golden Gauntlets", "palette": GAUNTLET_COLORS, "default": "Gold", "hue": (45, 25),
        "textures": ["Mt_Gold_Armor_Adult_Gauntlet_Gold_Alb"],
    },
}


def _rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    d = mx - mn
    safe = np.where(d == 0, 1, d)
    h = np.where(mx == r, ((g - b) / safe) % 6, np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60
    h = np.where(d == 0, 0, h)
    s = np.where(mx == 0, 0, d / np.where(mx == 0, 1, mx))
    return h, s, mx


def _hsv_to_rgb(h, s, v):
    c = v * s
    hp = (h % 360) / 60
    x = c * (1 - np.abs(hp % 2 - 1))
    z = np.zeros_like(h)
    i = np.floor(hp).astype(int) % 6
    r = np.choose(i, [c, x, z, z, x, c])
    g = np.choose(i, [x, c, c, x, z, z])
    b = np.choose(i, [z, z, x, c, c, x])
    m = v - c
    return np.stack([r + m, g + m, b + m], -1)


def _soft(x, knee=0.8):
    over = np.maximum(x - knee, 0)
    return np.where(x > knee, knee + (1 - knee) * (1 - np.exp(-over / (1 - knee))), x)


def _remap(value, ref, target):
    return _soft(target * value / max(ref, 1e-3))


def recolor_fn(slot, color):
    spec = SLOTS[slot]
    sh, ss, sv = colorsys.rgb_to_hsv(*(c / 255 for c in spec["palette"][spec["default"]]))
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in color))

    def fn(img):
        rgb = img[..., :3].astype(np.float32) / 255
        h, s, v = _rgb_to_hsv(rgb)
        if spec["hue"] is None:
            weight = np.clip((0.25 - s) / 0.1, 0, 1)
        else:
            center, width = spec["hue"]
            dist = np.abs((h - center + 180) % 360 - 180)
            weight = np.clip((width - dist) / 10, 0, 1) * np.clip((s - 0.12) / 0.08, 0, 1)
        core = weight > 0.5
        if not core.any():
            return img
        ref_s = float(np.median(s[core]))
        ref_v = float(np.median(v[core]))
        scale_v = ref_v / max(sv, 1e-3)
        scale_s = ref_s / ss if ss > 0.05 else 1.0
        nh = np.full_like(h, th * 360)
        ns = np.clip(s * min(1.0, ts * scale_s) / max(ref_s, 1e-3), 0, 1) if ts > 0.02 else np.zeros_like(s)
        nv = np.clip(_remap(v, ref_v, min(0.85, tv * scale_v)), 0, 1)
        new = _hsv_to_rgb(nh, ns, nv)
        out = rgb + (new - rgb) * weight[..., None]
        res = img.copy()
        res[..., :3] = np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)
        return res

    return fn


def parse_color(value, palette):
    if not value or value == "Default":
        return None
    if value in palette:
        return palette[value]
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
    raise ValueError(f"unknown color {value!r}")


def _contrast(color):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in color))
    if s < 0.15:
        r, g, b = colorsys.hsv_to_rgb(0.75, 0.55, 0.35 if v > 0.5 else 0.75)
    else:
        r, g, b = colorsys.hsv_to_rgb((h + 0.5) % 1.0, max(s, 0.5), min(1.0, max(0.3, v * 0.8)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def resolve(choices, rng=None):
    rng = rng or random.Random()
    out, picked = {}, {}
    for slot, spec in SLOTS.items():
        value = choices.get(slot, "Contrast" if spec.get("match") else "Default")
        if value == "Match Tunic":
            value = picked.get(spec.get("match"), "Default")
        elif value == "Contrast":
            base = picked.get(spec.get("match"), "Default")
            if base in (None, "Default", SLOTS[spec["match"]]["default"]):
                value = "Default"
            else:
                value = _contrast(parse_color(base, SLOTS[spec["match"]]["palette"]))
        if value == "Random Choice":
            value = rng.choice([k for k in spec["palette"] if k != spec["default"]])
        elif value == "Completely Random":
            value = "#%02X%02X%02X" % tuple(rng.randrange(256) for _ in range(3))
        picked[slot] = value
        if value in (None, "Default", spec["default"]):
            continue
        out[slot] = (value, parse_color(value, spec["palette"]))
    return out


GOLD_POT_TEXTURES = ["Rock_Pot_A_02_Alb"]


def _gild(img):
    rgb = img[..., :3].astype(np.float32) / 255
    _, _, v = _rgb_to_hsv(rgb)
    ref = max(float(np.median(v)), 1e-3)
    nv = np.clip(_soft(v / ref * 0.85, 0.85), 0, 1)
    ns = np.clip(0.82 + 0.15 * (1 - v / max(v.max(), 1e-3)), 0, 1)
    out = img.copy()
    out[..., :3] = np.clip(_hsv_to_rgb(np.full_like(v, 46.0), ns, nv) * 255 + 0.5, 0, 255).astype(np.uint8)
    return out


def gold_pots(game):
    files = {}
    for tex in GOLD_POT_TEXTURES:
        path = f"Tex/{tex}.bntx.zs"
        t = Texture(game.read(path))
        t.recolor(_gild)
        files[path] = t.dumps()
    return files


def build(game, choices, rng=None):
    files, summary = {}, {}
    for slot, (name, color) in resolve(choices, rng).items():
        fn = recolor_fn(slot, color)
        for tex in SLOTS[slot]["textures"]:
            path = f"Tex/{tex}.bntx.zs"
            t = Texture(game.read(path))
            t.recolor(fn)
            files[path] = t.dumps()
        summary[SLOTS[slot]["label"]] = name
    return files, summary
