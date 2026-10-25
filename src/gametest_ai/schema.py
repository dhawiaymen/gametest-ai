"""Bounded, data-only browser test plans; no arbitrary JavaScript or shell actions."""

import copy
import json
import math
import re
from pathlib import Path

OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "contains")


def finite(value, lo, hi, label, integer=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not lo <= value <= hi
        or (integer and int(value) != value)
    ):
        raise ValueError(
            f"{label} must be a finite {'integer' if integer else 'number'} in [{lo},{hi}]"
        )


def text(value, label, limit=500):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"Invalid {label}")


def validate_plan(plan):
    if (
        not isinstance(plan, dict)
        or set(plan) != {"version", "scenarios"}
        or type(plan["version"]) is not int
        or plan["version"] != 1
    ):
        raise ValueError("Plan must contain version:1 and scenarios")
    if not isinstance(plan["scenarios"], list) or not 1 <= len(plan["scenarios"]) <= 100:
        raise ValueError("Use 1–100 scenarios")
    names = set()
    for scenario in plan["scenarios"]:
        if not isinstance(scenario, dict) or set(scenario) != {"name", "steps"}:
            raise ValueError("Scenario requires name and steps")
        text(scenario["name"], "scenario name", 120)
        if scenario["name"] in names:
            raise ValueError("Scenario names must be unique")
        names.add(scenario["name"])
        if not isinstance(scenario["steps"], list) or not 1 <= len(scenario["steps"]) <= 5000:
            raise ValueError("Use 1–5000 steps per scenario")
        for step in scenario["steps"]:
            if not isinstance(step, dict):
                raise ValueError("Each step must be an object")
            kind = step.get("type")
            fields = {
                "click": {"type", "selector"},
                "press": {"type", "key"},
                "wait": {"type", "ms"},
                "reset": {"type", "seed"},
                "game": {"type", "action", "dt"},
                "assert": {"type", "source", "path", "op", "value"},
            }.get(kind)
            if fields is None or set(step) != fields:
                raise ValueError(f"Invalid step fields: {kind}")
            if kind == "click":
                text(step["selector"], "selector")
            elif kind == "press":
                text(step["key"], "key", 80)
            elif kind == "wait":
                finite(step["ms"], 0, 10000, "wait", True)
            elif kind == "reset":
                finite(step["seed"], 0, 4294967295, "seed", True)
            elif kind == "game":
                finite(step["dt"], 0, 10, "dt")
                a = step["action"]
                if not isinstance(a, dict) or set(a) - {"tap", "x"}:
                    raise ValueError("Game action supports only tap and x")
                if "tap" in a and type(a["tap"]) is not bool:
                    raise ValueError("tap must be boolean")
                if "x" in a:
                    finite(a["x"], -10000, 10000, "x")
            else:
                if step["source"] not in ("snapshot", "text"):
                    raise ValueError("Assertion source must be snapshot or text")
                text(step["path"], "assertion path")
                if step["source"] == "snapshot" and not re.fullmatch(
                    r"[A-Za-z_][A-Za-z_0-9]*(\.[A-Za-z_0-9]+)*", step["path"]
                ):
                    raise ValueError("Snapshot path must be dotted identifiers")
                if step["op"] not in OPS:
                    raise ValueError("Unknown assertion operator")
                if isinstance(step["value"], (list, dict)) or step["value"] is None:
                    raise ValueError("Assertion value must be a string, number, or boolean")
                if isinstance(step["value"], float) and not math.isfinite(step["value"]):
                    raise ValueError("Non-finite assertion value")
    if sum(len(s["steps"]) for s in plan["scenarios"]) > 20000:
        raise ValueError("Plan exceeds 20,000 total steps")
    return copy.deepcopy(plan)


def load_plan(path):
    p = Path(path)
    if p.stat().st_size > 5_000_000:
        raise ValueError("Plan exceeds 5 MB")
    return validate_plan(json.loads(p.read_text(encoding="utf-8")))


def lookup(snapshot, path):
    value = snapshot
    for key in path.split("."):
        if isinstance(value, list) and key.isdigit():
            value = value[int(key)]
        elif isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise AssertionError(f"Missing snapshot path: {path}")
    return value


def compare(actual, op, expected):
    try:
        if op == "eq":
            ok = (
                type(actual) is type(expected)
                and actual == expected
                or (
                    type(actual) in (int, float)
                    and type(expected) in (int, float)
                    and actual == expected
                )
            )
        elif op == "ne":
            ok = actual != expected
        elif op == "gt":
            ok = actual > expected
        elif op == "gte":
            ok = actual >= expected
        elif op == "lt":
            ok = actual < expected
        elif op == "lte":
            ok = actual <= expected
        elif op == "contains":
            ok = expected in actual
        else:
            raise ValueError("Unknown assertion operator")
    except TypeError:
        ok = False
    if not ok:
        raise AssertionError(f"Expected {actual!r} {op} {expected!r}")


def fuzz_plan(seed=42, steps=300, width=480):
    import random

    finite(seed, 0, 4294967295, "seed", True)
    finite(steps, 1, 4999, "steps", True)
    finite(width, 1, 10000, "width", True)
    rng = random.Random(seed)
    actions = [{"type": "reset", "seed": seed}]
    for _ in range(steps):
        actions.append(
            {
                "type": "game",
                "action": {"x": rng.randint(0, width), "tap": rng.random() < 0.15},
                "dt": 0.1,
            }
        )
    return validate_plan(
        {"version": 1, "scenarios": [{"name": f"Seeded exploration {seed}", "steps": actions}]}
    )
