import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_site

POLICY = build_site.CSP.replace("; upgrade-insecure-requests", "")


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Content-Security-Policy", POLICY)
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=str(build_site.OUT))
    ThreadingHTTPServer(("127.0.0.1", 8790), handler).serve_forever()
