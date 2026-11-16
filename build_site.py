import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import evfl

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
EXTRA = ROOT / "web_build"
OUT = ROOT.parent / "ootrando-site"

ENGINE_MODULES = ["game", "nup", "sarc", "byml", "msbt", "bntx", "texcodec", "cosmetics", "hints", "logic", "logo",
                  "maps", "mod", "npcs", "pickups", "places", "randomizer", "songs", "starting", "options",
                  "webentry", "folder", "formats", "keys", "skips", "models", "bfres"]
ENGINE_DATA = ["data/isget.json", "data/locations.json", "data/places.json", "data/landmarks.json",
               "data/romfs_needed.json",
               "fonts/texgyrepagella-bold.otf", "fonts/GUST-FONT-LICENSE.txt"]
FOLDER_DIRS = ["Event/EventFlow", "Pack/Actor"]

WORDMARK = """<div class="wordmark" role="img" aria-label="Ocarina of Time Randomizer">
    <span class="top">Ocarina of Time</span>
    <span class="main">Randomizer</span>
    <span class="rule"></span>
  </div>"""

CSP = ("default-src 'self'; "
       "script-src 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval' 'unsafe-eval'; "
       "connect-src 'self' https://cdn.jsdelivr.net blob: data:; "
       "img-src 'self' data: blob:; "
       "style-src 'self' 'unsafe-inline'; "
       "font-src 'self'; "
       "worker-src 'self' blob:; "
       "object-src 'none'; "
       "base-uri 'self'; "
       "form-action 'self'; "
       "frame-ancestors 'none'; "
       "upgrade-insecure-requests")

HTTPS_RULES = """<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{HTTPS} !=on
  RewriteCond %{HTTP:X-Forwarded-Proto} !https
  RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</IfModule>

"""

HSTS = '  Header always set Strict-Transport-Security "max-age=31536000"\n'

HTACCESS = """Options -Indexes
DirectoryIndex index.html
ServerSignature Off

<FilesMatch "^\\.(?!htaccess$)|\\.(env|py|bak|log|ini|sql|md)$">
  Require all denied
</FilesMatch>

<IfModule mod_mime.c>
  AddType application/javascript .js
  AddType application/zip .zip
  AddType application/wasm .wasm
  AddType image/svg+xml .svg
  AddType image/webp .webp
</IfModule>

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json text/plain
</IfModule>

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-Frame-Options "DENY"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()"
  Header always set Cross-Origin-Opener-Policy "same-origin"
  Header always set Content-Security-Policy "{csp}"
{hsts}  <FilesMatch "\\.(html|zip)$">
    Header set Cache-Control "no-cache"
  </FilesMatch>
  <FilesMatch "\\.(js|css|otf|webp)$">
    Header set Cache-Control "public, max-age=604800"
  </FilesMatch>
</IfModule>
"""


def engine_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in ENGINE_MODULES:
            z.write(ROOT / f"{name}.py", f"{name}.py")
        for rel in ENGINE_DATA:
            z.write(ROOT / rel, rel)
        package = Path(evfl.__file__).parent
        for path in sorted(package.rglob("*.py")):
            rel = path.relative_to(package.parent)
            if "tests" not in rel.parts:
                z.write(path, rel.as_posix())
    return buf.getvalue()


def stamp(data):
    return hashlib.sha1(data).hexdigest()[:10]


def index_html(versions):
    html = (WEB / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'<img class="logo"[^>]*>', WORDMARK, html, count=1)
    html = html.replace("<title>Ocarina of Time Randomizer</title>",
                        "<title>Ocarina of Time Randomizer for Nintendo Switch 2</title>\n"
                        '<meta name="description" content="Make an item randomizer mod for The Legend of Zelda: '
                        'Ocarina of Time on Nintendo Switch 2. Runs in your browser from your own copy of the game.">')
    html = html.replace('href="style.css"', f'href="style.css?v={versions["style.css"]}"')
    html = html.replace('<script src="app.js"></script>',
                        f'<script src="engine.js?v={versions["engine.js"]}"></script>\n'
                        f'<script src="app.js?v={versions["app.js"]}"></script>')
    return html


def htaccess(force_https):
    text = HTACCESS.replace("{csp}", CSP).replace("{hsts}", HSTS if force_https else "")
    return (HTTPS_RULES + text) if force_https else text


def main(force_https=False):
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.iterdir():
        shutil.rmtree(old) if old.is_dir() else old.unlink()
    files = {
        "style.css": (WEB / "style.css").read_bytes(),
        "app.js": (WEB / "app.js").read_bytes(),
        "favicon.svg": (WEB / "favicon.svg").read_bytes(),
        "feedback.php": (WEB / "feedback.php").read_bytes(),
        "log.php": (WEB / "log.php").read_bytes(),
        "engine.js": (EXTRA / "site" / "engine.js").read_bytes(),
        "worker.js": (EXTRA / "site" / "worker.js").read_bytes(),
        "astcenc.js": (EXTRA / "astcenc.js").read_bytes(),
        "engine.zip": engine_zip(),
    }
    needed = json.loads((ROOT / "data" / "romfs_needed.json").read_text())
    files["romfs-files.json"] = json.dumps({"files": needed["files"], "dirs": FOLDER_DIRS}).encode()
    for shot in sorted(WEB.glob("shot-*.webp")):
        files[shot.name] = shot.read_bytes()
    versions = {k: stamp(v) for k, v in files.items()}
    files["worker.js"] = files["worker.js"].replace(
        b'importScripts(PYODIDE + "pyodide.js", "astcenc.js");',
        f'importScripts(PYODIDE + "pyodide.js", "astcenc.js?v={versions["astcenc.js"]}");'.encode())
    files["worker.js"] = files["worker.js"].replace(b'fetch("engine.zip"', f'fetch("engine.zip?v={versions["engine.zip"]}"'.encode())
    files["engine.js"] = files["engine.js"].replace(b'new Worker("worker.js")',
                                                    f'new Worker("worker.js?v={stamp(files["worker.js"])}")'.encode())
    versions["engine.js"] = stamp(files["engine.js"])
    files["index.html"] = index_html(versions).encode()
    files[".htaccess"] = htaccess(force_https).encode()
    for name, data in files.items():
        (OUT / name).write_bytes(data)
    total = sum(len(v) for v in files.values())
    print(f"site written to {OUT} ({len(files)} files, {total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
