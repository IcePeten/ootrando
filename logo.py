import sys
from pathlib import Path

import numpy as np
import zstandard
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import bntx
from game import ROOT

TITLE_TEX = "UI/Layout2Archive/Title.Product.100.Nin_Ounce_NVN2.bntx.zs"
TEXTURE_FILES = [TITLE_TEX, "UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.bntx.zs"]
CACHE = ROOT / "cache" / "logo_v1"
LOGOS = ["Logo_USEU_00"]
TEXT = "RANDOMIZER"
FONTS = ["palab.ttf", "constanb.ttf", "georgiab.ttf", "timesbd.ttf"]
BUNDLED_FONT = ROOT / "fonts" / "texgyrepagella-bold.otf"
CENTER_X = 1123
TOP = 1000
CAP_HEIGHT = 84
MAX_WIDTH = 800
TRACKING = 0.12


def _font(size):
    for path in [Path("C:/Windows/Fonts") / name for name in FONTS] + [BUNDLED_FONT]:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _glyph_mask(width, height):
    size = int(CAP_HEIGHT / 0.7)
    while True:
        font = _font(size)
        advances = [font.getlength(c) for c in TEXT]
        track = size * TRACKING
        total = sum(advances) + track * (len(TEXT) - 1)
        if total <= MAX_WIDTH or size < 20:
            break
        size -= 2
    mask = Image.new("L", (width, height), 0)
    d = ImageDraw.Draw(mask)
    top = font.getbbox("R")[1]
    x = CENTER_X - total / 2
    for c, adv in zip(TEXT, advances):
        d.text((x, TOP - top), c, font=font, fill=255)
        x += adv + track
    return mask.filter(ImageFilter.MaxFilter(3))


def _roughen(mask, seed=7):
    rng = np.random.default_rng(seed)
    noise = Image.fromarray((rng.random((mask.height // 6 + 1, mask.width // 6 + 1)) * 255).astype(np.uint8))
    noise = np.asarray(noise.resize(mask.size, Image.BICUBIC), np.float32) / 255
    soft = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
    edge = np.clip((soft - 0.35 - (noise - 0.5) * 0.5) * 6, 0, 1)
    return edge


def _gold_leaf(text_layer, width, height):
    a = text_layer[..., 3].astype(np.int32)
    solid = (a >= 250).astype(np.int32)
    ii = np.pad(solid.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    best, size = None, 128
    while best is None and size >= 24:
        s = size
        area = ii[s:, s:] - ii[:-s, s:] - ii[s:, :-s] + ii[:-s, :-s]
        ys, xs = np.where(area == s * s)
        if len(ys):
            best = (ys[len(ys) // 2], xs[len(xs) // 2], s)
        size -= 8
    y, x, s = best
    patch = text_layer[y:y + s, x:x + s, :3]
    tile = np.concatenate([patch, patch[:, ::-1]], 1)
    tile = np.concatenate([tile, tile[::-1]], 0)
    reps = (height // tile.shape[0] + 1, width // tile.shape[1] + 1, 1)
    return np.tile(tile, reps)[:height, :width].astype(np.float32)


def compose(logo, text_layer):
    h, w = logo.shape[:2]
    mask = _glyph_mask(w, h)
    alpha = _roughen(mask)
    gold = _gold_leaf(text_layer, w, h)
    rows = np.linspace(1.08, 0.86, h)[:, None, None]
    gold = np.clip(gold * rows, 0, 255)
    shadow = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)),
                        np.float32) / 255 * 0.45

    base = logo.astype(np.float32) / 255
    out_a = base[..., 3]
    out_rgb = base[..., :3]

    def over(rgb, a, dst_rgb, dst_a):
        res_a = a + dst_a * (1 - a)
        safe = np.where(res_a == 0, 1, res_a)
        res_rgb = (rgb * a[..., None] + dst_rgb * (dst_a * (1 - a))[..., None]) / safe[..., None]
        return res_rgb, res_a

    out_rgb, out_a = over(np.zeros_like(out_rgb), shadow, out_rgb, out_a)
    out_rgb, out_a = over(gold / 255, alpha, out_rgb, out_a)
    out = np.dstack([out_rgb, out_a])
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def _patch(game, path):
    data, tex = bntx.textures(game.read(path))
    text_layer = tex["Logo_Text_USEU_00"].read_level(0)
    for name in LOGOS:
        t = tex[name]
        t.write_level(0, compose(t.read_level(0), text_layer))
    return bytes(data)


def build(game):
    out = {}
    for path in TEXTURE_FILES:
        cached = CACHE / path
        size_file = cached.with_name(cached.name + ".size")
        if not (cached.exists() and size_file.exists()):
            data = _patch(game, path)
            cached.parent.mkdir(parents=True, exist_ok=True)
            d = game.dictionary_for(path)
            threads = 0 if sys.platform == "emscripten" else -1
            comp = zstandard.ZstdCompressor(level=6, dict_data=d, threads=threads) if d else \
                zstandard.ZstdCompressor(level=6, threads=threads)
            tmp = cached.with_name(cached.name + ".tmp")
            tmp.write_bytes(comp.compress(data))
            size_file.write_text(str(len(data)))
            tmp.replace(cached)
        out[path] = (cached.read_bytes(), int(size_file.read_text()))
    return out
