import argparse
import json
from pathlib import Path
import sys
from .schema import load_plan, fuzz_plan


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Test browser mini-games with reproducible scenarios and optional local AI."
    )
    sub = p.add_subparsers(dest="command")
    sub.add_parser("gui")
    run = sub.add_parser("run")
    run.add_argument("target")
    run.add_argument("plan")
    run.add_argument("--output", required=True)
    run.add_argument("--headed", action="store_true")
    run.add_argument("--allow-external", action="store_true")
    run.add_argument("--timeout", type=int, default=5000)
    fuzz = sub.add_parser("fuzz")
    fuzz.add_argument("target")
    fuzz.add_argument("--output", required=True)
    fuzz.add_argument("--seed", type=int, default=42)
    fuzz.add_argument("--steps", type=int, default=300)
    fuzz.add_argument("--width", type=int, default=480)
    check = sub.add_parser("validate")
    check.add_argument("plan")
    ai = sub.add_parser("generate")
    ai.add_argument("description", help="UTF-8 game specification file")
    ai.add_argument("--output", required=True)
    ai.add_argument("--model", default="qwen2.5-coder:7b")
    ai.add_argument("--endpoint", default="http://127.0.0.1:11434")
    args = p.parse_args(argv)
    try:
        if args.command in (None, "gui"):
            from .gui import main as gui

            gui()
            return 0
        if args.command == "validate":
            plan = load_plan(args.plan)
            print(f"Valid: {len(plan['scenarios'])} scenarios")
            return 0
        if args.command == "generate":
            from .ai import generate_plan

            path = Path(args.output)
            if path.exists():
                raise FileExistsError("Output plan already exists")
            plan = generate_plan(
                Path(args.description).read_text(encoding="utf-8"), args.model, args.endpoint
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as f:
                f.write(json.dumps(plan, indent=2) + "\n")
            print(f"Generated {path}. Review it before running.")
            return 0
        from .runner import run_plan

        if args.command == "fuzz":
            result = run_plan(
                args.target, fuzz_plan(args.seed, args.steps, args.width), args.output
            )
        else:
            result = run_plan(
                args.target,
                load_plan(args.plan),
                args.output,
                not args.headed,
                args.timeout,
                args.allow_external,
            )
        print(
            f"{result['passed']} passed, {result['failed']} failed. Report: {Path(args.output) / 'report.html'}"
        )
        return 1 if result["failed"] else 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
