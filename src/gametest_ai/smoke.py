"""Exercise the packaged app on a real Windows runner, including Tk startup."""
import json
import platform
from pathlib import Path
import tempfile
import traceback
import tkinter as tk


def run(result_path):
    result = {"status": "failed", "platform": platform.platform(), "checks": []}
    root = None
    try:
        with tempfile.TemporaryDirectory(prefix="portable smoke ") as temporary:
            work = Path(temporary)
            import os
            from importlib.resources import files
            from .runner import run_plan
            from .gui import TestApp
            if getattr(__import__("sys"), "frozen", False):
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
                os.environ.pop("GAMETEST_BROWSER_PATH", None)
            source = work / "demo"
            source.mkdir()
            resource = files("gametest_ai").joinpath("templates")
            for name in ("index.html", "game.js", "project.json", "LICENSE"):
                (source / name).write_bytes(resource.joinpath(name).read_bytes())
            plan = json.loads(resource.joinpath("tap-win.json").read_text(encoding="utf-8"))
            report = run_plan(source, plan, work / "report")
            assert report["passed"] == len(plan["scenarios"]) and report["failed"] == 0, report
            assert (work / "report/junit.xml").is_file()
            result["checks"] += ["bundled Chromium launch", "demo browser assertions", "HTML JSON JUnit reports"]
            root = tk.Tk()
            app = TestApp(root)
            root.update()
            app.load_demo()
            assert Path(app.target.get()).is_file()
            result["checks"].append("native Tk workbench and bundled demo")
            root.destroy()
            root = None
        result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        if root is not None:
            root.destroy()
        Path(result_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["status"] == "passed" else 1
