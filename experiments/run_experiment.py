"""CLI entry point for the self-evolution strategy experiment.

Examples:
    python experiments/run_experiment.py
    python experiments/run_experiment.py --strategies direct,reflexion
    python experiments/run_experiment.py --backend openai --model gpt-4o-mini
    python experiments/run_experiment.py --seeds 1,2,3 --out experiments/results
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evolve_lab.runner import DEFAULT_STRATEGIES, format_report, run_experiment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backend", default="mock", choices=["mock", "openai"])
    parser.add_argument("--model", default="gpt-4o-mini", help="model name for the openai backend")
    parser.add_argument(
        "--strategies",
        default=",".join(DEFAULT_STRATEGIES),
        help=f"comma-separated; available: {','.join(DEFAULT_STRATEGIES)}",
    )
    parser.add_argument("--tasks", default="", help="comma-separated task ids (default: all)")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument(
        "--critique-accuracy",
        type=float,
        default=0.5,
        help="mock-only: probability a self-critique round spots the current bug",
    )
    parser.add_argument("--seeds", default="7", help="comma-separated seeds, e.g. 1,2,3")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "results"))
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    args = parser.parse_args()

    strategies = tuple(s.strip() for s in args.strategies.split(",") if s.strip())
    task_ids = tuple(t.strip() for t in args.tasks.split(",") if t.strip()) or None
    seeds = tuple(int(s.strip()) for s in args.seeds.split(",") if s.strip())

    backend_kwargs: dict = {"model": args.model} if args.backend == "openai" else {}
    if args.backend == "mock":
        backend_kwargs["critique_accuracy"] = args.critique_accuracy
    report = run_experiment(
        backend_name=args.backend,
        strategies=strategies,
        task_ids=task_ids,
        max_attempts=args.max_attempts,
        seeds=seeds,
        out_dir=Path(args.out),
        verbose=not args.quiet,
        backend_kwargs=backend_kwargs,
    )

    print("\n=== Aggregate (mean over seeds) ===")
    print(format_report(report))
    print(f"\nsaved: {report.get('_saved_to')}")
    if args.json:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
