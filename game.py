from functools import cached_property
from pathlib import Path

import zstandard

import sarc
from nup import Nup

ROOT = Path(__file__).resolve().parent
DEFAULT_NUP = next(ROOT.parent.glob("*Ocarina of Time*.nup"), None)
TITLE_ID = "0400486024DEC000"


class Game:
    def __init__(self, nup_path=DEFAULT_NUP, level=16, source=None):
        self.nup = source if source is not None else Nup.open(nup_path)
        self.files = self.nup.romfs()
        self.level = level

    @cached_property
    def dictionaries(self):
        packed = zstandard.ZstdDecompressor().decompressobj().decompress(
            self.nup.read(self.files["Pack/ZsDic.pack.zs"]))
        archive = sarc.Sarc(packed)
        return {f.name: zstandard.ZstdCompressionDict(bytes(f.data)) for f in archive.get_files()}

    def dictionary_for(self, path):
        if path.endswith(".rsizetable.zs"):
            return None
        if path.endswith(".bcett.byml.zs"):
            return self.dictionaries.get("bcett.byml.zsdic")
        if path.endswith(".pack.zs"):
            return self.dictionaries.get("pack.zsdic")
        return self.dictionaries.get("zs.zsdic")

    def raw(self, path):
        return self.nup.read(self.files[path])

    def read(self, path):
        data = self.raw(path)
        if path.endswith(".zs"):
            d = self.dictionary_for(path)
            dctx = zstandard.ZstdDecompressor(dict_data=d) if d else zstandard.ZstdDecompressor()
            data = dctx.decompressobj().decompress(data)
        return data

    def compress(self, path, data):
        d = self.dictionary_for(path)
        cctx = zstandard.ZstdCompressor(level=self.level, dict_data=d) if d else \
            zstandard.ZstdCompressor(level=self.level)
        return cctx.compress(data)

    def sarc(self, path):
        return sarc.Sarc(self.read(path))

    def glob(self, pattern):
        import fnmatch
        return sorted(p for p in self.files if fnmatch.fnmatch(p, pattern))
