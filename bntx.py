import struct

import numpy as np

import texcodec

ASTC_BLOCKS = {0x2D: (4, 4), 0x2E: (5, 4), 0x2F: (5, 5), 0x30: (6, 5), 0x31: (6, 6), 0x32: (8, 5), 0x33: (8, 6),
               0x34: (8, 8), 0x35: (10, 5), 0x36: (10, 6), 0x37: (10, 8), 0x38: (10, 10), 0x39: (12, 10),
               0x3A: (12, 12)}
BC_FORMATS = {0x1A: ("bc1", 8), 0x1C: ("bc3", 16), 0x20: ("bc7", 16)}
TILES_WIDE = 256


def _div(a, b):
    return (a + b - 1) // b


def _addresses(width, height, bpp, block_height):
    gobs_wide = _div(width * bpp, 64)
    y, x = np.mgrid[0:height, 0:width]
    xb = x * bpp
    gob = ((y // (8 * block_height)) * 512 * block_height * gobs_wide
           + (xb // 64) * 512 * block_height
           + ((y % (8 * block_height)) // 8) * 512)
    xe = xb // 16
    inner = (y & 1) | (((y >> 1) & 1) << 1) | ((xe & 1) << 2) | (((y >> 2) & 1) << 3) | (((xe >> 1) & 1) << 4)
    return gob + inner * 16 + (xb % 16)


class Texture:
    def __init__(self, data, brti=None):
        self.data = data if isinstance(data, bytearray) else bytearray(data)
        b = self.brti = self.data.find(b"BRTI") if brti is None else brti
        self.mips = struct.unpack_from("<H", self.data, b + 0x16)[0]
        self.format = struct.unpack_from("<I", self.data, b + 0x1C)[0]
        self.width, self.height = struct.unpack_from("<II", self.data, b + 0x24)
        self.image_size = struct.unpack_from("<I", self.data, b + 0x50)[0]
        self.block_height_log2 = struct.unpack_from("<I", self.data, b + 0x34)[0] & 7
        ptrs = struct.unpack_from("<Q", self.data, b + 0x70)[0]
        self.offsets = list(struct.unpack_from(f"<{self.mips}Q", self.data, ptrs))
        kind = self.format >> 8
        self.srgb = (self.format & 0xFF) == 0x06
        if kind in ASTC_BLOCKS:
            self.codec, self.block_bytes = "astc", 16
            self.bw, self.bh = ASTC_BLOCKS[kind]
        elif kind in BC_FORMATS:
            self.codec, self.block_bytes = BC_FORMATS[kind]
            self.bw = self.bh = 4
        else:
            raise ValueError(f"unsupported texture format {self.format:#x}")

    def _decode(self, blocks, w, h):
        return texcodec.decode(self.codec, blocks, w, h, self.bw, self.bh, self.srgb)

    def _encode(self, rgba):
        return texcodec.encode(self.codec, rgba, self.bw, self.bh, self.srgb)

    def _layout(self, level):
        w, h = max(1, self.width >> level), max(1, self.height >> level)
        wb, hb = _div(w, self.bw), _div(h, self.bh)
        block_height = 1 << self.block_height_log2
        while block_height > 1 and hb <= (block_height * 8) // 2:
            block_height //= 2
        addr = self.offsets[level] + _addresses(wb, hb, self.block_bytes, block_height)
        return w, h, addr[..., None] + np.arange(self.block_bytes)

    def read_level(self, level=0):
        w, h, idx = self._layout(level)
        raw = np.frombuffer(self.data, np.uint8)
        return self._decode(raw[idx].reshape(-1).tobytes(), w, h)

    def write_level(self, level, rgba):
        w, h, idx = self._layout(level)
        enc = np.frombuffer(self._encode(np.ascontiguousarray(rgba)), np.uint8)
        raw = np.frombuffer(self.data, np.uint8).copy()
        raw[idx] = enc.reshape(idx.shape)
        self.data[:] = raw.tobytes()

    def recolor(self, fn):
        start = self.offsets[0]
        n = self.image_size // self.block_bytes
        cols = min(n, TILES_WIDE)
        rows = _div(n, cols)
        blob = bytes(self.data[start:start + n * self.block_bytes])
        blob += bytes(self.block_bytes * (cols * rows - n))
        out = fn(self._decode(blob, cols * self.bw, rows * self.bh))
        enc = np.frombuffer(self._encode(np.ascontiguousarray(out)), np.uint8)
        self.data[start:start + n * self.block_bytes] = enc[:n * self.block_bytes].tobytes()

    @property
    def name(self):
        off = struct.unpack_from("<Q", self.data, self.brti + 0x60)[0]
        n = struct.unpack_from("<H", self.data, off)[0]
        return self.data[off + 2:off + 2 + n].decode()

    def dumps(self):
        return bytes(self.data)


def textures(data):
    data = data if isinstance(data, bytearray) else bytearray(data)
    out, pos = {}, 0
    while (b := data.find(b"BRTI", pos)) >= 0:
        try:
            t = Texture(data, b)
            out[t.name] = t
        except ValueError:
            pass
        pos = b + 4
    return data, out
