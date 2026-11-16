import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ASTCENC = Path(__file__).resolve().parent / "tools" / "astcenc" / "bin" / "astcenc-avx2.exe"
ASTC_FAST = 10.0

try:
    import etcpak
    import texture2ddecoder
    NATIVE = True
except ImportError:
    NATIVE = False


def decode(codec, blocks, w, h, bw, bh, srgb):
    if NATIVE:
        if codec == "astc":
            bgra = texture2ddecoder.decode_astc(blocks, w, h, bw, bh)
        else:
            bgra = getattr(texture2ddecoder, f"decode_{codec}")(blocks, w, h)
        return np.frombuffer(bgra, np.uint8).reshape(h, w, 4)[..., [2, 1, 0, 3]].copy()
    if codec == "astc":
        return _web_astc_decode(blocks, w, h, bw, bh, srgb)
    return _bc_decode(codec, blocks, w, h)


def encode(codec, rgba, bw, bh, srgb):
    rgba = np.ascontiguousarray(rgba)
    if codec == "astc":
        return _native_astc_encode(rgba, bw, bh, srgb) if NATIVE else _web_astc_encode(rgba, bw, bh, srgb)
    if NATIVE:
        return getattr(etcpak, f"compress_{codec}")(rgba.tobytes(), rgba.shape[1], rgba.shape[0])
    return _bc_encode(codec, rgba)


def _native_astc_encode(rgba, bw, bh, srgb):
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in.png")
        dst = os.path.join(tmp, "out.astc")
        Image.fromarray(rgba, "RGBA").save(src)
        subprocess.run([str(ASTCENC), "-cs" if srgb else "-cl", src, dst, f"{bw}x{bh}", "-fast", "-silent"],
                       check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return Path(dst).read_bytes()[16:]


def _blocks_count(w, h, bw, bh):
    return ((w + bw - 1) // bw) * ((h + bh - 1) // bh)


def _web_astc_decode(blocks, w, h, bw, bh, srgb):
    import js
    from pyodide.ffi import to_js
    out = js.astcDecode(to_js(memoryview(bytes(blocks))), w, h, bw, bh, bool(srgb))
    return np.frombuffer(out.to_bytes(), np.uint8).reshape(h, w, 4).copy()


def _web_astc_encode(rgba, bw, bh, srgb):
    import js
    from pyodide.ffi import to_js
    h, w = rgba.shape[:2]
    out = js.astcEncode(to_js(memoryview(rgba.tobytes())), w, h, bw, bh, bool(srgb), ASTC_FAST)
    return out.to_bytes()


def _to_blocks(img):
    h, w = img.shape[:2]
    return img.reshape(h // 4, 4, w // 4, 4, -1).swapaxes(1, 2).reshape(-1, 16, img.shape[2])


def _from_blocks(blocks, w, h):
    c = blocks.shape[-1]
    return blocks.reshape(h // 4, w // 4, 4, 4, c).swapaxes(1, 2).reshape(h, w, c)


def _unpack565(c):
    c = c.astype(np.uint32)
    r = (c >> 11) & 31
    g = (c >> 5) & 63
    b = c & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.int32)


def _pack565(rgb):
    rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint32)
    return ((rgb[..., 0] * 31 + 127) // 255 << 11) | ((rgb[..., 1] * 63 + 127) // 255 << 5) | \
        ((rgb[..., 2] * 31 + 127) // 255)


def _color_palette(c0, c1, four):
    e0, e1 = _unpack565(c0), _unpack565(c1)
    p2 = np.where(four[:, None], (2 * e0 + e1) // 3, (e0 + e1) // 2)
    p3 = np.where(four[:, None], (e0 + 2 * e1) // 3, 0)
    return np.stack([e0, e1, p2, p3], 1)


def _decode_color(raw, force_four=False):
    c0 = raw[:, 0].astype(np.uint16) | (raw[:, 1].astype(np.uint16) << 8)
    c1 = raw[:, 2].astype(np.uint16) | (raw[:, 3].astype(np.uint16) << 8)
    bits = raw[:, 4:8].astype(np.uint32)
    bits = bits[:, 0] | (bits[:, 1] << 8) | (bits[:, 2] << 16) | (bits[:, 3] << 24)
    idx = (bits[:, None] >> (2 * np.arange(16, dtype=np.uint32))) & 3
    four = np.ones(len(raw), bool) if force_four else c0 > c1
    pal = _color_palette(c0, c1, four)
    rgb = np.take_along_axis(pal, idx[..., None].astype(np.int64).repeat(3, -1), 1)
    alpha = np.where((~four[:, None]) & (idx == 3), 0, 255)
    return rgb, alpha


def _alpha_palette(a0, a1):
    a0 = a0.astype(np.int32)[:, None]
    a1 = a1.astype(np.int32)[:, None]
    i = np.arange(1, 7)
    eight = np.concatenate([a0, a1, ((7 - i) * a0 + i * a1) // 7], 1)
    i = np.arange(1, 5)
    six = np.concatenate([a0, a1, ((5 - i) * a0 + i * a1) // 5, np.zeros_like(a0), np.full_like(a0, 255)], 1)
    return np.where((a0 > a1), eight, six)


def _decode_alpha(raw):
    pal = _alpha_palette(raw[:, 0], raw[:, 1])
    bits = np.zeros(len(raw), np.uint64)
    for k in range(6):
        bits |= raw[:, 2 + k].astype(np.uint64) << np.uint64(8 * k)
    idx = (bits[:, None] >> (np.uint64(3) * np.arange(16, dtype=np.uint64))) & np.uint64(7)
    return np.take_along_axis(pal, idx.astype(np.int64), 1)


def _bc_decode(codec, blocks, w, h):
    pw, ph = (w + 3) // 4 * 4, (h + 3) // 4 * 4
    size = 8 if codec == "bc1" else 16
    raw = np.frombuffer(bytes(blocks), np.uint8)[:_blocks_count(w, h, 4, 4) * size].reshape(-1, size)
    if codec == "bc1":
        rgb, _ = _decode_color(raw)
        alpha = np.full(rgb.shape[:2], 255)
    elif codec == "bc3":
        rgb, _ = _decode_color(raw[:, 8:], force_four=True)
        alpha = _decode_alpha(raw[:, :8])
    else:
        raise ValueError(f"no browser decoder for {codec}")
    px = np.concatenate([rgb, alpha[..., None]], -1).astype(np.uint8)
    return _from_blocks(px, pw, ph)[:h, :w].copy()


def _principal_endpoints(rgb):
    mean = rgb.mean(1, keepdims=True)
    d = rgb - mean
    cov = np.einsum("nki,nkj->nij", d, d)
    axis = np.ones((len(rgb), 3), np.float32)
    for _ in range(8):
        axis = np.einsum("nij,nj->ni", cov, axis)
        norm = np.linalg.norm(axis, axis=1, keepdims=True)
        axis = np.where(norm > 1e-6, axis / np.maximum(norm, 1e-6), np.float32(0.57735))
    proj = np.einsum("nki,ni->nk", d, axis)
    lo = mean[:, 0] + proj.min(1)[:, None] * axis
    hi = mean[:, 0] + proj.max(1)[:, None] * axis
    return hi, lo


def _encode_color(rgb):
    hi, lo = _principal_endpoints(rgb.astype(np.float32))
    c0, c1 = _pack565(hi), _pack565(lo)
    swap = c0 < c1
    c0, c1 = np.where(swap, c1, c0), np.where(swap, c0, c1)
    pal = _color_palette(c0, c1, np.ones(len(rgb), bool)).astype(np.float32)
    dist = ((rgb[:, :, None, :].astype(np.float32) - pal[:, None, :, :]) ** 2).sum(-1)
    idx = dist.argmin(-1).astype(np.uint32)
    idx = np.where((c0 == c1)[:, None], 0, idx)
    bits = (idx << (2 * np.arange(16, dtype=np.uint32))).sum(1).astype(np.uint32)
    out = np.zeros((len(rgb), 8), np.uint8)
    out[:, 0], out[:, 1] = c0 & 0xFF, c0 >> 8
    out[:, 2], out[:, 3] = c1 & 0xFF, c1 >> 8
    for k in range(4):
        out[:, 4 + k] = (bits >> (8 * k)) & 0xFF
    return out


def _encode_alpha(a):
    a0 = a.max(1).astype(np.uint8)
    a1 = a.min(1).astype(np.uint8)
    pal = _alpha_palette(a0, a1)
    pal = np.where((a0 == a1)[:, None], a0[:, None].astype(np.int32), pal)
    idx = np.abs(a[:, :, None].astype(np.int32) - pal[:, None, :]).argmin(-1).astype(np.uint64)
    bits = (idx << (np.uint64(3) * np.arange(16, dtype=np.uint64))).sum(1, dtype=np.uint64)
    out = np.zeros((len(a), 8), np.uint8)
    out[:, 0], out[:, 1] = a0, a1
    for k in range(6):
        out[:, 2 + k] = ((bits >> np.uint64(8 * k)) & np.uint64(0xFF)).astype(np.uint8)
    return out


def _bc_encode(codec, rgba):
    h, w = rgba.shape[:2]
    pw, ph = (w + 3) // 4 * 4, (h + 3) // 4 * 4
    if (pw, ph) != (w, h):
        rgba = np.pad(rgba, ((0, ph - h), (0, pw - w), (0, 0)), mode="edge")
    blocks = _to_blocks(rgba)
    color = _encode_color(blocks[..., :3])
    if codec == "bc1":
        return color.tobytes()
    if codec == "bc3":
        return np.concatenate([_encode_alpha(blocks[..., 3]), color], 1).tobytes()
    raise ValueError(f"no browser encoder for {codec}")
