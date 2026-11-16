import json
import os
import shutil
import threading
import traceback
from pathlib import Path

import webview

import options as opts
import randomizer
from game import ROOT, Game
from mod import mods_dir

UI = ROOT / "ui" / "index.html"
SPOILERS = ROOT / "spoilers"


class Api:
    def __init__(self):
        self._game = None
        self._lock = threading.Lock()

    def game(self):
        if self._game is None:
            self._game = Game()
        return self._game

    def defaults(self):
        s = opts.defaults()
        s["installed"] = self.installed()
        return s

    def random_seed(self):
        return opts.random_seed()

    def installed(self):
        root = mods_dir()
        if not root.exists():
            return []
        return sorted(p.name for p in root.iterdir() if (p / "romfs").exists())

    def generate(self, options):
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "error": "A seed is already being generated."}
        try:
            settings = opts.settings_from(options)
            seed = settings.seed
            result = randomizer.generate(settings)
            target = randomizer.apply(self.game(), result)
            SPOILERS.mkdir(exist_ok=True)
            spoiler_path = SPOILERS / f"spoiler_{seed}.txt"
            spoiler_path.write_text(randomizer.spoiler(result))
            (SPOILERS / f"tracker_{seed}.json").write_text(json.dumps(randomizer.tracker(result, self.game())))
            out = opts.summary(result)
            out.update({"spoiler": str(spoiler_path), "mod": str(target), "installed": self.installed()})
            return out
        except Exception as e:
            traceback.print_exc()
            return {"ok": False, "error": str(e)}
        finally:
            self._lock.release()

    def tracker(self, seed=None):
        files = sorted(SPOILERS.glob("tracker_*.json"), key=lambda p: p.stat().st_mtime, reverse=True) \
            if SPOILERS.exists() else []
        if seed is not None:
            files = [p for p in files if p.stem == f"tracker_{seed}"]
        if not files:
            return None
        data = json.loads(files[0].read_text())
        state = SPOILERS / f"checked_{data['seed']}.json"
        data["checked"] = json.loads(state.read_text()) if state.exists() else []
        return data

    def set_checked(self, seed, checked):
        (SPOILERS / f"checked_{seed}.json").write_text(json.dumps(sorted(set(checked))))
        return True

    def open_path(self, path):
        if path and Path(path).exists():
            os.startfile(path)

    def open_mods(self):
        root = mods_dir()
        root.mkdir(parents=True, exist_ok=True)
        os.startfile(root)

    def remove(self, name):
        target = mods_dir() / name
        if target.exists() and target.parent == mods_dir():
            shutil.rmtree(target)
        return self.installed()


def main():
    webview.create_window("OoT Studio", str(UI), js_api=Api(), width=900, height=960, min_size=(620, 700),
                          background_color="#0d1411")
    webview.start()


if __name__ == "__main__":
    main()
