"""Playwright execution, browser diagnostics, invariant checks, and portable reports."""

from datetime import datetime, timezone
import html
import json
import math
import os
import re
from pathlib import Path
import time
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from .schema import validate_plan, lookup, compare
from .server import game_url


class DiagnosticLog(list):
    """Bound noisy games without hiding the fact that diagnostics occurred."""
    def append(self, message):
        if len(self) < 200:
            super().append(str(message)[:2000])
        elif len(self) == 200:
            super().append("Further diagnostics omitted (200-message limit).")


def adapter_call(page, method, argument, timeout):
    return page.evaluate("""async ({method, argument, timeout}) => {
      const adapter = window.gameTest;
      if (!adapter || adapter.version !== 1 || typeof adapter[method] !== 'function')
        throw Error('GameTest adapter v1 missing or method unavailable: ' + method);
      let timer;
      try {
        return await Promise.race([
          Promise.resolve().then(() => method === 'step' ?
            adapter.step(argument.action, argument.dt) :
            method === 'reset' ? adapter.reset(argument) : adapter.snapshot()),
          new Promise((_, reject) => {timer = setTimeout(() => reject(Error('Adapter timed out')), timeout);})
        ]);
      } finally {clearTimeout(timer);}
    }""", {"method": method, "argument": argument, "timeout": timeout})


def invariants(snapshot):
    if not isinstance(snapshot, dict):
        raise AssertionError("Adapter snapshot must be an object")
    for field in ("score", "time", "lives"):
        value = snapshot.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise AssertionError(f"{field} is missing or non-finite")
    if snapshot["time"] < 0 or snapshot["lives"] < 0:
        raise AssertionError("Time and lives must be nonnegative")
    if snapshot.get("status") not in ("running", "won", "lost"):
        raise AssertionError("Invalid game status")


def execute_step(page, step, timeout):
    kind = step["type"]
    if kind == "click":
        page.locator(step["selector"]).click(timeout=timeout)
    elif kind == "press":
        page.keyboard.press(step["key"])
    elif kind == "wait":
        page.wait_for_timeout(step["ms"])
    elif kind in ("reset", "game"):
        if kind == "reset":
            snapshot = adapter_call(page, "reset", step["seed"], timeout)
        else:
            snapshot = adapter_call(page, "step", step, timeout)
        invariants(snapshot)
    elif kind == "assert":
        if step["source"] == "text":
            actual = page.locator(step["path"]).inner_text(timeout=timeout)
        else:
            snapshot = adapter_call(page, "snapshot", None, timeout)
            invariants(snapshot)
            actual = lookup(snapshot, step["path"])
        compare(actual, step["op"], step["value"])


def write_reports(report, folder):
    folder = Path(folder)
    (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    suite = ET.Element(
        "testsuite",
        name="GameTest AI",
        tests=str(len(report["scenarios"])),
        failures=str(report["failed"]),
        time=str(report["duration_seconds"]),
    )
    rows = []
    for result in report["scenarios"]:
        def xml_text(value):
            return re.sub(r"[^\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]", "\ufffd", value)

        case = ET.SubElement(suite, "testcase", name=xml_text(result["name"]), time=str(result["duration_seconds"]))
        if result["status"] == "failed":
            error = xml_text(result["error"])
            ET.SubElement(case, "failure", message=error).text = error
        shot = result.get("screenshot")
        link = f'<a href="{html.escape(shot, quote=True)}">Screenshot</a>' if shot else ""
        rows.append(
            f"<tr><td>{html.escape(result['name'])}</td><td>{result['status']}</td><td>{result['steps_completed']}</td><td><pre>{html.escape(result.get('error', ''))}</pre>{link}</td></tr>"
        )
    ET.ElementTree(suite).write(folder / "junit.xml", encoding="utf-8", xml_declaration=True)
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><title>GameTest AI report</title>
<style>body{font:16px system-ui;background:#111c30;color:#ecf2ff;margin:40px}table{border-collapse:collapse;width:100%}th,td{padding:14px;border:1px solid #3d5072;text-align:left}a{color:#66e2ba}pre{white-space:pre-wrap;max-width:700px}h1{color:#66e2ba}</style>"""
    page += f"<h1>GameTest AI</h1><p>{report['passed']} passed · {report['failed']} failed · {report['duration_seconds']:.2f}s</p>"
    page += (
        "<table><tr><th>Scenario</th><th>Result</th><th>Completed steps</th><th>Details</th></tr>"
        + "".join(rows)
        + "</table></html>"
    )
    (folder / "report.html").write_text(page, encoding="utf-8")


def run_plan(
    target,
    plan,
    output,
    headless=True,
    timeout=5000,
    allow_external=False,
    progress=None,
    cancel=None,
):
    from playwright.sync_api import sync_playwright

    plan = validate_plan(plan)
    if not isinstance(timeout, int) or not 100 <= timeout <= 60000:
        raise ValueError("Timeout must be 100–60000 ms")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("Reports require a new output folder")
    report = {
        "version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "target": str(target),
        "scenarios": [],
        "passed": 0,
        "failed": 0,
        "duration_seconds": 0,
    }
    started = time.monotonic()
    with game_url(target) as url, sync_playwright() as pw:
        launch = {"headless": headless}
        if os.environ.get("GAMETEST_BROWSER_PATH"):
            launch["executable_path"] = os.environ["GAMETEST_BROWSER_PATH"]
        browser = pw.chromium.launch(**launch)
        output.mkdir(parents=True, exist_ok=False)
        (output / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
        try:
            for i, scenario in enumerate(plan["scenarios"]):
                begin = time.monotonic()
                logs = DiagnosticLog()
                result = {
                    "name": scenario["name"],
                    "status": "passed",
                    "steps_completed": 0,
                    "error": "",
                    "logs": logs,
                }
                context = browser.new_context(
                    viewport={"width": 1000, "height": 900}, service_workers="block"
                )
                if not allow_external:
                    origin = urlparse(url)

                    def route_request(route):
                        u = urlparse(route.request.url)
                        if u.scheme in ("data", "blob") or (u.scheme, u.netloc) == (
                            origin.scheme,
                            origin.netloc,
                        ):
                            route.continue_()
                        else:
                            route.abort()

                    context.route("**/*", route_request)
                    def block_socket(socket):
                        logs.append("WebSocket blocked: " + socket.url)
                        # An intercepted socket has no upstream connection unless
                        # connect_to_server() is called. Keep it inert until context cleanup.
                    context.route_web_socket("**/*", block_socket)
                page = context.new_page()
                page.set_default_timeout(timeout)
                page.on("pageerror", lambda e: logs.append("JavaScript: " + str(e)))
                page.on(
                    "console",
                    lambda msg: (
                        logs.append("Console: " + msg.text) if msg.type == "error" else None
                    ),
                )
                page.on("requestfailed", lambda req: logs.append("Request failed: " + req.url))
                page.on("response", lambda res: logs.append(f"HTTP {res.status}: {res.url}") if res.status >= 400 else None)
                try:
                    if cancel and cancel.is_set():
                        raise RuntimeError("Cancelled")
                    response = page.goto(url, wait_until="load", timeout=timeout)
                    if response and response.status >= 400:
                        raise AssertionError(f"Navigation HTTP {response.status}")
                    for step in scenario["steps"]:
                        if cancel and cancel.is_set():
                            raise RuntimeError("Cancelled")
                        if time.monotonic() - begin > 120:
                            raise TimeoutError("Scenario exceeded 120 seconds")
                        execute_step(page, step, timeout)
                        result["steps_completed"] += 1
                    page.wait_for_timeout(80)
                    if logs:
                        raise AssertionError("\n".join(logs[:20]))
                except Exception as exc:
                    result["status"] = "failed"
                    result["error"] = f"{type(exc).__name__}: {exc}"
                finally:
                    try:
                        filename = f"scenario-{i + 1:03}.png"
                        page.screenshot(path=str(output / filename), timeout=timeout)
                        result["screenshot"] = filename
                    except Exception as exc:
                        logs.append("Screenshot unavailable: " + str(exc))
                    context.close()
                result["duration_seconds"] = round(time.monotonic() - begin, 4)
                report["scenarios"].append(result)
                report[result["status"]] += 1
                report["duration_seconds"] = round(time.monotonic() - started, 4)
                write_reports(report, output)
                if progress:
                    progress(i + 1, len(plan["scenarios"]), result["name"], result["status"])
                if cancel and cancel.is_set():
                    report["cancelled"] = True
                    write_reports(report, output)
                    break
        finally:
            browser.close()
    return report
