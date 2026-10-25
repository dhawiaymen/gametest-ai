"""Actual Chromium tests. Install the browser before running this suite."""

import json
from pathlib import Path
import pytest
from gametest_ai.runner import run_plan
from gametest_ai.schema import fuzz_plan

pytestmark = pytest.mark.browser


@pytest.fixture
def game():
    return Path(__file__).parent.parent / "examples/demo-game/index.html"


def test_real_browser_pass_and_fail(game, tmp_path):
    plan = {
        "version": 1,
        "scenarios": [
            {
                "name": "Win by tapping",
                "steps": [{"type": "reset", "seed": 42}]
                + [{"type": "game", "action": {"tap": True}, "dt": 0.1} for _ in range(5)]
                + [
                    {
                        "type": "assert",
                        "source": "snapshot",
                        "path": "status",
                        "op": "eq",
                        "value": "won",
                    }
                ],
            },
            {
                "name": "Deliberate failing assertion",
                "steps": [
                    {"type": "reset", "seed": 42},
                    {
                        "type": "assert",
                        "source": "snapshot",
                        "path": "score",
                        "op": "eq",
                        "value": 999,
                    },
                ],
            },
        ],
    }
    result = run_plan(game, plan, tmp_path / "report")
    assert result["passed"] == 1 and result["failed"] == 1
    assert "999" in result["scenarios"][1]["error"]
    assert (tmp_path / "report/scenario-002.png").stat().st_size > 100
    assert json.loads((tmp_path / "report/report.json").read_text())["failed"] == 1


def test_dom_interaction_and_reset(game, tmp_path):
    p = {
        "version": 1,
        "scenarios": [
            {
                "name": "Keyboard and restart",
                "steps": [
                    {"type": "click", "selector": "canvas"},
                    {"type": "press", "key": "Space"},
                    {
                        "type": "assert",
                        "source": "snapshot",
                        "path": "score",
                        "op": "eq",
                        "value": 2,
                    },
                    {"type": "click", "selector": "#restart"},
                    {
                        "type": "assert",
                        "source": "snapshot",
                        "path": "score",
                        "op": "eq",
                        "value": 0,
                    },
                    {
                        "type": "assert",
                        "source": "text",
                        "path": "#status",
                        "op": "contains",
                        "value": "running",
                    },
                ],
            }
        ],
    }
    r = run_plan(game, p, tmp_path / "report")
    assert r["failed"] == 0, r


def test_fuzz_is_executed_in_browser(game, tmp_path):
    r = run_plan(game, fuzz_plan(123, 80), tmp_path / "fuzz")
    assert r["failed"] == 0, r


def test_detects_javascript_error(tmp_path):
    target = tmp_path / "broken.html"
    target.write_text('<h1>Hello</h1><script>throw Error("BROKEN_GAME")</script>')
    p = {
        "version": 1,
        "scenarios": [{"name": "Catch runtime error", "steps": [{"type": "wait", "ms": 20}]}],
    }
    r = run_plan(target, p, tmp_path / "report")
    assert r["failed"] == 1
    assert "BROKEN_GAME" in r["scenarios"][0]["error"]


def test_missing_adapter_is_actionable(tmp_path):
    target = tmp_path / "plain.html"
    target.write_text("<h1>Plain DOM</h1>")
    r = run_plan(target, fuzz_plan(1, 1), tmp_path / "report")
    assert r["failed"] == 1 and "adapter v1 missing" in r["scenarios"][0]["error"]


def test_cli_failure_exit_code(game, tmp_path):
    from gametest_ai.cli import main

    plan = {
        "version": 1,
        "scenarios": [
            {
                "name": "Failure",
                "steps": [
                    {"type": "assert", "source": "text", "path": "h1", "op": "eq", "value": "WRONG"}
                ],
            }
        ],
    }
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    assert main(["run", str(game), str(path), "--output", str(tmp_path / "report")]) == 1


def test_preexisting_output_is_never_overwritten(game, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep").write_text("keep")
    with pytest.raises(FileExistsError):
        run_plan(game, fuzz_plan(1, 1), out)
    assert (out / "keep").read_text() == "keep"


@pytest.mark.gui
def test_gui_runs_browser_worker(game, tmp_path, tk_root):
    import time
    from gametest_ai.gui import TestApp
    app = TestApp(tk_root)
    app.target.set(str(game))
    app.output.set(str(tmp_path / "gui report"))
    app.set_plan(fuzz_plan(42, 5))
    app.run()
    deadline = time.monotonic() + 20
    while app.busy and time.monotonic() < deadline:
        tk_root.update()
        time.sleep(0.02)
    assert not app.busy
    assert app.report_path and Path(app.report_path).exists()
    assert "0 failed" in app.status.get()
