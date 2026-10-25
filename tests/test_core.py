import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import urllib.error
from urllib.request import urlopen
import pytest
from gametest_ai.schema import validate_plan, fuzz_plan, lookup, compare
from gametest_ai.runner import invariants, write_reports
from gametest_ai.ai import generate_plan, EXAMPLE
from gametest_ai.server import game_url


def test_seeded_plan_repeatable():
    assert fuzz_plan(42, 30) == fuzz_plan(42, 30)
    assert fuzz_plan(42, 30) != fuzz_plan(43, 30)


@pytest.mark.parametrize(
    "step",
    [
        {"type": "eval", "code": "alert(1)"},
        {"type": "wait", "ms": 10001},
        {"type": "game", "action": {"code": "x"}, "dt": 1},
        {"type": "game", "action": {"tap": "yes"}, "dt": 1},
        {"type": "reset", "seed": -1},
        {"type": "click", "selector": ""},
    ],
)
def test_reject_unbounded_or_unsafe_steps(step):
    p = copy.deepcopy(EXAMPLE)
    p["scenarios"][0]["steps"] = [step]
    with pytest.raises(ValueError):
        validate_plan(p)


def test_unique_names_and_empty_plans():
    p = copy.deepcopy(EXAMPLE)
    p["scenarios"] *= 2
    with pytest.raises(ValueError):
        validate_plan(p)
    with pytest.raises(ValueError):
        validate_plan({"version": 1, "scenarios": []})


def test_assertions():
    assert lookup({"items": [{"x": 5}]}, "items.0.x") == 5
    compare(5, "gte", 5)
    compare("hello", "contains", "ell")
    with pytest.raises(AssertionError):
        compare(3, "gt", 4)
    with pytest.raises(AssertionError):
        lookup({"score": 1}, "missing")
    with pytest.raises(AssertionError):
        compare(True, "eq", 1)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), None, True, "3"])
def test_invariants_reject_bad_numbers(value):
    with pytest.raises(AssertionError):
        invariants({"score": value, "time": 1, "lives": 1, "status": "running"})


def test_report_html_escaping_and_junit(tmp_path):
    report = {
        "passed": 0,
        "failed": 1,
        "duration_seconds": 1,
        "scenarios": [
            {
                "name": "<script>x</script>",
                "status": "failed",
                "error": "a < b & c",
                "steps_completed": 0,
                "duration_seconds": 1,
            }
        ],
    }
    write_reports(report, tmp_path)
    assert "<script>" not in (tmp_path / "report.html").read_text()
    import xml.etree.ElementTree as ET

    root = ET.parse(tmp_path / "junit.xml").getroot()
    assert root.attrib["failures"] == "1"


def test_server_serves_only_game_root(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    (game / "index.html").write_text("Hello")
    (tmp_path / "secret.txt").write_text("private")
    with game_url(game) as url:
        assert urlopen(url).read() == b"Hello"
        base = url.split("/index.html")[0]
        with pytest.raises(urllib.error.HTTPError):
            urlopen(base + "/../secret.txt")
        try:
            (game / "linked.txt").symlink_to(tmp_path / "secret.txt")
        except OSError:
            return
        with pytest.raises(urllib.error.HTTPError):
            urlopen(base + "/linked.txt")


def test_ai_local_response_validation():
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            received.update(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            payload = json.dumps({"response": json.dumps(EXAMPLE)}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = generate_plan(
            "Tap game, adapter v1, target 10.", endpoint=f"http://127.0.0.1:{server.server_port}"
        )
        assert result == EXAMPLE and received["format"] == "json" and received["stream"] is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize(
    "url",
    ["https://example.com", "http://example.com", "http://user@localhost:11434", "file:///tmp/ai"],
)
def test_ai_rejects_nonlocal_endpoints(url):
    with pytest.raises(ValueError):
        generate_plan("game", endpoint=url)


@pytest.mark.gui
def test_gui_constructs():
    import tkinter as tk
    from gametest_ai.gui import TestApp

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("No graphical display available")
    try:
        app = TestApp(root)
        root.update()
        assert app.get_plan()["version"] == 1
    finally:
        root.destroy()


def test_server_blocks_symlink_index(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "index.html").write_text("public")
    secret = tmp_path / "secret.html"
    secret.write_text("private")
    nested = root / "nested"
    nested.mkdir()
    try:
        (nested / "index.html").symlink_to(secret)
    except OSError:
        pytest.skip("Symlinks not permitted on this platform")
    with game_url(root) as url:
        base = url.split("/index.html")[0]
        with pytest.raises(urllib.error.HTTPError):
            urlopen(base + "/nested/")


def test_ai_rejects_invalid_model_plan():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            bad = {
                "version": 1,
                "scenarios": [{"name": "bad", "steps": [{"type": "eval", "code": "x"}]}],
            }
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"response": json.dumps(bad)}).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with pytest.raises(ValueError):
            generate_plan("game", endpoint=f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
