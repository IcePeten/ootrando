import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import formats
import options as opts
import randomizer
from folder import FolderSource
from game import TITLE_ID, Game

NEEDED_PATH = Path(__file__).resolve().parent / "data" / "romfs_needed.json"
OUT_ZIP = "/tmp/mod.zip"
OUT_SPOILER = "/tmp/spoiler.txt"

_game = None


class JsFile:
    def __init__(self, reader, size, name):
        self.reader = reader
        self.size = size
        self.name = name
        self.pos = 0

    def seek(self, pos, whence=0):
        self.pos = pos if whence == 0 else self.pos + pos if whence == 1 else self.size + pos
        return self.pos

    def tell(self):
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        data = self.reader(self.pos, n).to_bytes() if n else b""
        self.pos += len(data)
        return data


def defaults():
    return json.dumps(opts.defaults())


def random_seed():
    return opts.random_seed()


def open_game(reader, size, name):
    global _game
    _game = None
    f = JsFile(reader, size, name)
    if f.read(4) != b"NUP\x01":
        info = formats.describe(f, size, name)
        return json.dumps({"found": False, "unsupported": True, "format": info["format"],
                           "contents": formats.summary(info), "diagnostics": info})
    f.seek(0)
    try:
        game = Game(f, level=9)
    except Exception as e:
        raise ValueError("This file could not be read as a .nup game file. Make sure it is a complete, "
                         "unmodified .nup of Ocarina of Time.") from e
    base = game.nup.package("base")
    if base is None or f"{base.title_id:016X}" != TITLE_ID:
        raise ValueError("This file is not The Legend of Zelda: Ocarina of Time for Nintendo Switch 2.")
    update = game.nup.package("update")
    version = re.search(r"\[v(\d+)\]", name)
    label = f"Update v{update.version}" if update else (f"Update v{version.group(1)}" if version else "Base game")
    _game = game
    return json.dumps({"found": True, "name": "The Legend of Zelda: Ocarina of Time",
                       "size_gb": round(size / 1e9, 1), "title_id": TITLE_ID, "version": label})


def _needed():
    with open(NEEDED_PATH, encoding="utf-8") as f:
        return json.load(f)


def open_folder(sizes_json, reader):
    global _game
    _game = None
    sizes = json.loads(sizes_json)
    needed = _needed()
    missing = [p for p in needed["files"] if p not in sizes]
    if "Pack/ZsDic.pack.zs" not in sizes or len(missing) > len(needed["files"]) // 20:
        raise ValueError(f"This folder doesn't look like the RomFS of Ocarina of Time ({len(missing)} of "
                         f"{len(needed['files'])} needed files are missing). Choose the romfs folder you extracted "
                         f"from the game.")
    source = FolderSource(sizes, reader)
    game = Game(source=source, level=9)
    hashes = {}
    for path in needed["versions"]["probes"]:
        if path in sizes:
            hashes[path] = hashlib.sha256(source.read(source.entries[path])).hexdigest()
    label = next((name for name, known in needed["versions"]["known"].items()
                  if all(hashes.get(p) == h for p, h in known.items())), None)
    _game = game
    return json.dumps({"found": True, "name": "The Legend of Zelda: Ocarina of Time", "size_gb": None,
                       "source": "Extracted RomFS folder", "title_id": TITLE_ID,
                       "version": label or "Unknown version", "known_version": bool(label),
                       "missing": missing[:50], "hashes": hashes})


def generate(options_json, progress):
    if _game is None:
        raise ValueError("Choose your game file first.")
    settings = opts.settings_from(json.loads(options_json))
    progress("Shuffling items and checking that the seed can be beaten")
    result = randomizer.generate(settings)
    builder = randomizer.build_mod(_game, result, progress)
    progress("Packing the mod")
    files = builder.finish()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for path in sorted(files):
            z.writestr(f"{settings.mod_name}/romfs/{path}", files[path])
    with open(OUT_ZIP, "wb") as f:
        f.write(buf.getbuffer())
    with open(OUT_SPOILER, "w", encoding="utf-8") as f:
        f.write(randomizer.spoiler(result))
    return json.dumps(opts.summary(result))
