"""
eval/run_evals.py
Minimal eval harness for Neurex. Runs a fixed set of coding tasks against
the live API and scores the results.

Usage:
  python eval/run_evals.py
  python eval/run_evals.py --model qwen2.5-coder:7b
  python eval/run_evals.py --only smoke

Output: JSON report to eval/results/<timestamp>.json
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

API_BASE   = os.getenv("EVAL_API_URL", "http://localhost:8000")
API_TOKEN  = os.getenv("API_TOKEN", "neurex-dev-token")
WS_BASE    = os.getenv("EVAL_WS_URL", "ws://localhost:8000")
RESULTS_DIR = Path(__file__).parent / "results"

# ── Test cases ────────────────────────────────────────────────────────────────
# Each entry: { id, tag, prompt, checks: list of strings that must appear in
# any written file or agent output }

EVAL_CASES = [
    # Smoke tests — fast, no real coding
    {
        "id": "smoke-hello",
        "tag": "smoke",
        "prompt": "Create a file called hello.py that prints 'Hello, Neurex!'",
        "checks": ["hello.py", "Hello, Neurex"],
    },
    {
        "id": "smoke-readme",
        "tag": "smoke",
        "prompt": "Create a README.md with a one-sentence description of the project.",
        "checks": ["README.md"],
    },

    # Python coding
    {
        "id": "py-fibonacci",
        "tag": "python",
        "prompt": "Write a Python function fibonacci(n) that returns the nth Fibonacci number. Add a docstring and type hints. Save to fibonacci.py.",
        "checks": ["fibonacci.py", "def fibonacci", "-> int", '"""'],
    },
    {
        "id": "py-class",
        "tag": "python",
        "prompt": "Create a Python dataclass BankAccount with fields: owner (str), balance (float). Add deposit() and withdraw() methods that raise ValueError if balance goes negative. Save to bank.py.",
        "checks": ["bank.py", "dataclass", "def deposit", "def withdraw", "ValueError"],
    },
    {
        "id": "py-async",
        "tag": "python",
        "prompt": "Write an async Python function fetch_json(url: str) -> dict that uses httpx to GET a URL and return parsed JSON. Handle HTTPError. Save to fetcher.py.",
        "checks": ["fetcher.py", "async def fetch_json", "httpx", "HTTPError"],
    },
    {
        "id": "py-tests",
        "tag": "python",
        "prompt": "Write pytest tests for a function add(a, b) that returns a+b. Include at least 3 test cases including an edge case. Save to test_add.py.",
        "checks": ["test_add.py", "def test_", "assert"],
    },

    # TypeScript coding
    {
        "id": "ts-interface",
        "tag": "typescript",
        "prompt": "Create a TypeScript interface User with id, name, email fields. Export it from types.ts.",
        "checks": ["types.ts", "interface User", "export"],
    },
    {
        "id": "ts-function",
        "tag": "typescript",
        "prompt": "Write a TypeScript function groupBy<T>(arr: T[], key: keyof T): Record<string, T[]>. Add JSDoc. Save to utils.ts.",
        "checks": ["utils.ts", "groupBy", "keyof T", "Record"],
    },

    # Multi-file
    {
        "id": "multi-module",
        "tag": "multi",
        "prompt": "Create a Python package called mathlib/ with an __init__.py that exports two modules: geometry.py (area_circle, area_rect) and stats.py (mean, median). Include type hints throughout.",
        "checks": ["mathlib/", "__init__.py", "def area_circle", "def mean", "-> float"],
    },
    {
        "id": "multi-api",
        "tag": "multi",
        "prompt": "Create a minimal FastAPI app in app.py with a GET /health endpoint returning {status: ok} and a POST /echo endpoint that returns the request body.",
        "checks": ["app.py", "FastAPI", "/health", "/echo", "@app.post"],
    },

    # Refactoring
    {
        "id": "refactor-extract",
        "tag": "refactor",
        "prompt": "Read the file refactor_input.py (if it exists, create a placeholder with a 60-line function). Extract the function into 3 smaller functions with clear names and docstrings.",
        "checks": ["def ", '"""'],
    },

    # Rules adherence
    {
        "id": "rules-no-wildcard",
        "tag": "rules",
        "prompt": "Write a Python module config.py that imports os, sys, and pathlib. Make sure to use explicit imports only, no wildcards.",
        "checks": ["config.py", "import os", "import sys"],
        "negative_checks": ["import *"],
    },
    {
        "id": "rules-type-hints",
        "tag": "rules",
        "prompt": "Write a Python function parse_config(path: str) -> dict that reads a JSON file and returns a dict. All arguments and return values must have type hints.",
        "checks": ["def parse_config", "str", "-> dict"],
    },

    # Research
    {
        "id": "research-library",
        "tag": "research",
        "prompt": "Research how to use the 'duckduckgo-search' Python library to get news results. Provide a code example.",
        "checks": ["DDGS", "ddgs.news", "duckduckgo-search"],
    },
]



# ── Runner ────────────────────────────────────────────────────────────────────

async def run_case(case: dict, model: str | None) -> dict:
    import websockets

    ws_url = f"{WS_BASE}/ws/eval-{case['id']}?token={API_TOKEN}"
    result = {
        "id":      case["id"],
        "tag":     case["tag"],
        "prompt":  case["prompt"],
        "passed":  False,
        "details": "",
        "duration_s": 0.0,
        "output":  "",
    }

    start = time.monotonic()
    try:
        async with websockets.connect(ws_url, open_timeout=10) as ws:
            await ws.send(json.dumps({"type": "message", "content": case["prompt"]}))

            output_tokens = []
            written_files: dict[str, str] = {}

            async for raw in ws:
                event = json.loads(raw)
                if event["event"] == "token":
                    output_tokens.append(event["data"])
                elif event["event"] == "done":
                    break
                elif event["event"] == "error":
                    result["details"] = f"WS error: {event['data']}"
                    return result

        full_output = "".join(output_tokens)
        result["output"] = full_output[:2000]

        # Read written files from workspace for checking
        async with httpx.AsyncClient() as client:
            tree_r = await client.get(f"{API_BASE}/api/files/tree")
            if tree_r.is_success:
                tree = tree_r.json()
                written_files = _flatten_tree(tree)

        # Score
        corpus = full_output + "\n" + "\n".join(written_files.keys()) + "\n" + "\n".join(written_files.values())

        failed_checks = [c for c in case.get("checks", []) if c.lower() not in corpus.lower()]
        failed_neg    = [c for c in case.get("negative_checks", []) if c.lower() in corpus.lower()]

        if not failed_checks and not failed_neg:
            result["passed"] = True
        else:
            parts = []
            if failed_checks:
                parts.append(f"Missing: {failed_checks}")
            if failed_neg:
                parts.append(f"Should not contain: {failed_neg}")
            result["details"] = "; ".join(parts)

    except Exception as e:
        result["details"] = f"Exception: {e}"

    result["duration_s"] = round(time.monotonic() - start, 2)
    return result


def _flatten_tree(node: dict, acc: dict | None = None) -> dict[str, str]:
    if acc is None:
        acc = {}
    if node.get("type") == "file":
        acc[node.get("path", "")] = ""  # content fetching omitted for speed
    for child in node.get("children", []):
        _flatten_tree(child, acc)
    return acc


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  default=None, help="Override model name")
    parser.add_argument("--only",   default=None, help="Filter by tag (smoke|python|typescript|multi|refactor|rules)")
    parser.add_argument("--case",   default=None, help="Run a single case by ID")
    args = parser.parse_args()

    cases = EVAL_CASES
    if args.only:
        cases = [c for c in cases if c["tag"] == args.only]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]

    if not cases:
        print("No matching cases.")
        sys.exit(1)

    print(f"\n🧪 Neurex Eval — running {len(cases)} cases\n{'─'*50}")

    results = []
    for case in cases:
        print(f"  {case['id']:<35}", end="", flush=True)
        result = await run_case(case, args.model)
        status = "✅ PASS" if result["passed"] else f"❌ FAIL  ({result['details']})"
        print(f"{status}  ({result['duration_s']}s)")
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    total  = len(results)
    print(f"\n{'─'*50}")
    print(f"  Score: {passed}/{total}  ({100*passed//total}%)")

    # Write report
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = RESULTS_DIR / f"eval_{ts}.json"
    report_path.write_text(json.dumps({
        "timestamp": ts,
        "model":     args.model or "default",
        "score":     f"{passed}/{total}",
        "results":   results,
    }, indent=2))
    print(f"  Report: {report_path}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
