import json
import mimetypes
import re
import shutil
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import game
import randomizer
from mod import mods_dir
from studio import SPOILERS, Api

WEB = game.ROOT / "web"
LOGO = game.ROOT / "research" / "logo_preview.png"
DOWNLOADS = game.ROOT / "cache" / "downloads"
PORT = 8765
api = Api()


def game_info():
    nup = game.DEFAULT_NUP
    if not nup or not Path(nup).exists():
        return {"found": False}
    version = re.search(r"\[v(\d+)\]", Path(nup).name)
    return {"found": True, "name": "The Legend of Zelda: Ocarina of Time",
            "size_gb": round(Path(nup).stat().st_size / 1e9, 1), "title_id": game.TITLE_ID,
            "version": f"Version {version.group(1)}" if version else "Unknown version"}


def package(seed, mod_path):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    target = DOWNLOADS / f"OoT-Randomizer-{seed}"
    mod_path = Path(mod_path)
    shutil.make_archive(str(target), "zip", root_dir=mod_path.parent, base_dir=mod_path.name)
    return f"/api/download/{target.name}.zip"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, body, kind="application/json", status=200, headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path, kind=None, headers=None):
        if not path.exists() or not path.is_file():
            return self._send({"error": "not found"}, status=404)
        self._send(path.read_bytes(), kind or mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                   headers=headers)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/defaults":
            d = api.defaults()
            d["game"] = game_info()
            d["forest_modes"] = list(randomizer.FOREST_MODES)
            return self._send(d)
        if path == "/api/random_seed":
            return self._send({"seed": api.random_seed()})
        if path.startswith("/api/download/"):
            name = Path(path).name
            return self._file(DOWNLOADS / name, "application/zip",
                              {"Content-Disposition": f'attachment; filename="{name}"'})
        if path.startswith("/api/spoiler/"):
            seed = Path(path).name
            return self._file(SPOILERS / f"spoiler_{seed}.txt", "text/plain; charset=utf-8")
        if path == "/logo.png":
            return self._file(LOGO, "image/png")
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        target = (WEB / rel).resolve()
        if WEB.resolve() not in target.parents and target != WEB.resolve():
            return self._send({"error": "not found"}, status=404)
        self._file(target)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/generate":
            return self._send({"error": "not found"}, status=404)
        length = int(self.headers.get("Content-Length", 0))
        options = json.loads(self.rfile.read(length) or b"{}")
        result = api.generate(options)
        if result.get("ok"):
            result["download"] = package(result["seed"], result["mod"])
            result["spoiler_url"] = f"/api/spoiler/{result['seed']}"
            result["mods_dir"] = str(mods_dir())
        self._send(result)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}/"
    print(f"OoT Randomizer website running at {url}")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
