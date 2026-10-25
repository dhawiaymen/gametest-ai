"""Temporary loopback-only server for local games. Never lists directories."""

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from urllib.parse import urlparse, quote


class GameHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None

    def send_head(self):
        resolved = Path(self.translate_path(self.path)).resolve()
        root = Path(self.directory).resolve()
        candidates = [resolved]
        if resolved.is_dir():
            candidates += [resolved / name for name in ("index.html", "index.htm")]
        if any(not candidate.resolve().is_relative_to(root) for candidate in candidates):
            self.send_error(403, "Path is outside the game directory")
            return None
        return super().send_head()


@contextmanager
def game_url(target, manual=True):
    parsed = urlparse(str(target))
    if parsed.scheme in ("http", "https"):
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Use an HTTP URL without credentials")
        # Remote games control their own test mode; URLs are not silently rewritten.
        yield str(target)
        return
    p = Path(target).resolve()
    if p.is_dir():
        p = p / "index.html"
    if not p.is_file() or p.suffix.lower() not in (".html", ".htm"):
        raise ValueError("Target must be an HTML file, game folder, or HTTP(S) URL")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(GameHandler, directory=str(p.parent)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/{quote(p.name)}" + (
            "?test=1" if manual else ""
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
