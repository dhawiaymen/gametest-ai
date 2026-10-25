import copy
import json
import xml.etree.ElementTree as ET
import pytest
from gametest_ai.schema import validate_plan, compare, lookup, fuzz_plan
from gametest_ai.ai import EXAMPLE
from gametest_ai.runner import run_plan, DiagnosticLog, write_reports


@pytest.mark.parametrize("kind", [[], {}, 7, None])
def test_malformed_type_is_validation_error(kind):
    plan = copy.deepcopy(EXAMPLE)
    plan["scenarios"][0]["steps"] = [{"type": kind}]
    with pytest.raises(ValueError, match="type must be a string"):
        validate_plan(plan)


def test_bool_and_number_equality_are_consistent():
    compare(True, "ne", 1)
    with pytest.raises(AssertionError):
        compare(1, "ne", 1.0)
    with pytest.raises(AssertionError, match="Missing snapshot path"):
        lookup({"items": []}, "items.0.x")


def test_huge_numbers_fail_cleanly():
    with pytest.raises(ValueError):
        fuzz_plan(10 ** 1000)
    assert fuzz_plan(42.0, 3.0, 480.0) == fuzz_plan(42, 3, 480)


def test_noisy_game_logs_are_bounded():
    log = DiagnosticLog()
    for _ in range(10000):
        log.append("x" * 5000)
    assert len(log) == 201
    assert len(log[0]) == 2000
    assert "omitted" in log[-1]


def test_junit_remains_parseable_with_control_characters(tmp_path):
    report = {"passed": 0, "failed": 1, "duration_seconds": 0,
              "scenarios": [{"name": "bad\x00name", "status": "failed", "error": "error\x01", "steps_completed": 0, "duration_seconds": 0}]}
    write_reports(report, tmp_path)
    assert ET.parse(tmp_path / "junit.xml").getroot().attrib["failures"] == "1"
    assert json.loads((tmp_path / "report.json").read_text())["failed"] == 1


@pytest.mark.browser
def test_async_adapter_timeout_is_reported(tmp_path):
    game = tmp_path / "index.html"
    game.write_text("<script>window.gameTest={version:1,reset:()=>new Promise(()=>{})}</script>")
    plan = {"version": 1, "scenarios": [{"name": "Promise timeout", "steps": [{"type": "reset", "seed": 1}]}]}
    report = run_plan(game, plan, tmp_path / "report", timeout=150)
    assert report["failed"] == 1
    assert "Adapter timed out" in report["scenarios"][0]["error"]


@pytest.mark.browser
def test_websocket_is_blocked_by_default(tmp_path):
    game = tmp_path / "index.html"
    game.write_text('<script>new WebSocket("ws://127.0.0.1:9/");</script>')
    plan = {"version": 1, "scenarios": [{"name": "Network guard", "steps": [{"type": "wait", "ms": 150}]}]}
    report = run_plan(game, plan, tmp_path / "report")
    assert report["failed"] == 1
    assert any("WebSocket blocked" in x for x in report["scenarios"][0]["logs"])


@pytest.mark.gui
def test_bundled_demo_can_be_loaded(tk_root):
    import tkinter as tk
    import weakref
    from pathlib import Path
    from gametest_ai.gui import TestApp
    app = TestApp(tk_root)
    app.load_demo()
    assert Path(app.target.get()).exists()
    assert app.get_plan()["scenarios"]
    temporary = Path(app.demo_directory.name)
    variables = [weakref.ref(value) for value in vars(app).values() if isinstance(value, tk.Variable)]
    assert variables
    app.destroy()
    assert not temporary.exists()
    assert all(reference() is None for reference in variables)
