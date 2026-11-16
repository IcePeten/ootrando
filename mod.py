import os
import shutil
import struct
import zlib
from pathlib import Path

import byml
from game import TITLE_ID

RESTBL_PATH = "System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs"


def mods_dir():
    return Path(os.environ["APPDATA"]) / "lichii" / "load" / TITLE_ID


class ResourceSizeTable:
    def __init__(self, data):
        self.magic, self.version, self.str_size, crc_count, name_count = struct.unpack_from("<6sIIII", data)
        pos = 22
        self.crcs = {}
        for _ in range(crc_count):
            crc, size = struct.unpack_from("<II", data, pos)
            self.crcs[crc] = size
            pos += 8
        self.names = {}
        for _ in range(name_count):
            name = data[pos:pos + self.str_size].split(b"\0")[0].decode()
            self.names[name] = struct.unpack_from("<I", data, pos + self.str_size)[0]
            pos += self.str_size + 4

    def get(self, path):
        return self.names.get(path, self.crcs.get(zlib.crc32(path.encode())))

    def set(self, path, size):
        if path in self.names:
            self.names[path] = size
        else:
            self.crcs[zlib.crc32(path.encode())] = size

    def dumps(self):
        out = bytearray(struct.pack("<6sIIII", self.magic, self.version, self.str_size,
                                    len(self.crcs), len(self.names)))
        for crc in sorted(self.crcs):
            out += struct.pack("<II", crc, self.crcs[crc])
        for name in sorted(self.names):
            out += name.encode().ljust(self.str_size, b"\0") + struct.pack("<I", self.names[name])
        return bytes(out)


class ModBuilder:
    """Collects edited game files and writes them as a LayeredFS mod."""

    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.files = {}
        self.restbl = ResourceSizeTable(game.read(RESTBL_PATH))
        self.loaded = {}
        self.plain = {}

    def placement(self, path):
        if path not in self.loaded:
            root, version, endian = byml.loads(self.game.read(path))
            self.loaded[path] = (root, version, endian)
        return self.loaded[path][0]

    def _store(self, path, data):
        original = len(self.game.read(path))
        key = path[:-3] if path.endswith(".zs") else path
        entry = self.restbl.get(key)
        if entry is not None:
            need = len(data) * 3 // 2 if ".bfevfl" in path else len(data)
            self.restbl.set(key, max(entry, need + max(0, entry - original)))
        self.files[path] = self.game.compress(path, data) if path.endswith(".zs") else data
        self.plain[path] = data

    def put(self, path, data):
        self._store(path, data)

    def current(self, path):
        return self.plain.get(path) or self.game.read(path)

    def put_new(self, path, data, template):
        key = path[:-3] if path.endswith(".zs") else path
        tkey = template[:-3] if template.endswith(".zs") else template
        overhead = max(0, (self.restbl.get(tkey) or 0) - len(self.game.read(template)))
        self.restbl.set(key, len(data) + overhead)
        self.files[path] = self.game.compress(path, data) if path.endswith(".zs") else data

    def put_compressed(self, path, compressed, size):
        original = len(self.game.read(path))
        key = path[:-3]
        entry = self.restbl.get(key)
        if entry is not None:
            self.restbl.set(key, max(entry, size + max(0, entry - original)))
        self.files[path] = compressed

    def finish(self):
        for path, (root, version, endian) in self.loaded.items():
            self._store(path, byml.dumps(root, version, endian))
        self.loaded = {}
        self.files[RESTBL_PATH] = self.game.compress(RESTBL_PATH, self.restbl.dumps())
        return self.files

    def write(self):
        self.finish()
        target = mods_dir() / self.name
        if target.exists():
            shutil.rmtree(target)
        for path, data in self.files.items():
            out = target / "romfs" / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
        return target
