"""Experiment orchestration: run strategies over the task suite, collect and
persist metrics.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .backends import LLMBackend, make_backend
from .strategies import STRATEGY_REGISTRY, Strategy, StrategyResult
from .tasks import TASKS, Task

DEFAULT_STRATEGIES = (
    "direct",
    "best_of_n",
    "self_refine",
    "reflexion",
    "reflexion_insights",
)


def run_strategy(
    strategy: Strategy,
    tasks: tuple[Task, ...] = TASKS,
    verbose: bool = True,
) -> StrategyResult:
    """Run one strategy over the task suite in a fixed order.

    Insights persist across tasks for strategies that extract them (shared
    list owned by the runner); other strategies pass an unused empty list.
    """
    result = StrategyResult(name=strategy.name)
    insights: list[str] = []  # cross-task memory lives here
    for task in tasks:
        started = time.perf_counter()
        outcome = strategy.solve(task, insights)
        elapsed = time.perf_counter() - started
        result.outcomes.append(outcome)
        if verbose:
            status = "PASS" if outcome.success else "FAIL"
            marker = "first-try" if outcome.first_attempt_success else f"{outcome.attempts_used} tries"
            print(
                f"  [{strategy.name:<18}] {status:<4} {task.id:<16} "
                f"({marker}, {outcome.llm_calls} calls, {elapsed:.2f}s)"
            )
    return result


def run_experiment(
    backend_name: str = "mock",
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    task_ids: tuple[str, ...] | None = None,
    max_attempts: int = 5,
    seeds: tuple[int, ...] = (7,),
    out_dir: Path | None = None,
    verbose: bool = True,
    backend_kwargs: dict | None = None,
) -> dict:
    """Run every strategy over the task suite (for each seed) and aggregate."""
    tasks = TASKS if task_ids is None else tuple(t for t in TASKS if t.id in task_ids)
    backend_kwargs = backend_kwargs or {}

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend": backend_name,
        "backend_kwargs": backend_kwargs,
        "max_attempts": max_attempts,
        "seeds": list(seeds),
        "tasks": [t.id for t in tasks],
        "runs": [],
    }

    for seed in seeds:
        for strategy_name in strategies:
            if verbose:
                print(f"[seed={seed}] strategy: {strategy_name}")
            kw = dict(backend_kwargs)
            if backend_name == "mock":
                kw.setdefault("seed", seed)
            backend: LLMBackend = make_backend(backend_name, **kw)
            strategy_cls = STRATEGY_REGISTRY[strategy_name]
            strategy = strategy_cls(backend, max_attempts=max_attempts)
            result = run_strategy(strategy, tasks, verbose=verbose)
            report["runs"].append(
                {
                    "seed": seed,
                    "strategy": strategy_name,
                    "outcomes": [asdict(o) for o in result.outcomes],
                    "summary": {
                        "success_rate": result.success_rate,
                        "first_attempt_rate": result.first_attempt_rate,
                        "avg_attempts": result.avg_attempts,
                        "total_llm_calls": result.total_calls,
                        "first_half_first_attempt_rate": result.first_half_first_attempt_rate(),
                        "second_half_first_attempt_rate": result.second_half_first_attempt_rate(),
                    },
                }
            )

    report["aggregate"] = _aggregate(report["runs"])

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
        path = out_dir / f"experiment-{backend_name}-{stamp}.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["_saved_to"] = str(path)
    return report


def _aggregate(runs: list[dict]) -> dict:
    """Average each strategy's summary across seeds."""
    by_strategy: dict[str, list[dict]] = {}
    for run in runs:
        by_strategy.setdefault(run["strategy"], []).append(run["summary"])
    aggregate: dict[str, dict] = {}
    for strategy, summaries in by_strategy.items():
        keys = summaries[0].keys()
        aggregate[strategy] = {
            key: round(sum(s[key] for s in summaries) / len(summaries), 4) for key in keys
        }
    return aggregate


def format_report(report: dict) -> str:
    """Human-readable summary table."""
    lines: list[str] = []
    header = f"{'strategy':<20} {'success':>8} {'first-try':>10} {'attempts':>9} {'calls':>7} {'1st-half':>9} {'2nd-half':>9}"
    lines.append(header)
    lines.append("-" * len(header))
    for strategy, summary in report["aggregate"].items():
        lines.append(
            f"{strategy:<20} {summary['success_rate']:>8.2f} {summary['first_attempt_rate']:>10.2f} "
            f"{summary['avg_attempts']:>9.2f} {summary['total_llm_calls']:>7.1f} "
            f"{summary['first_half_first_attempt_rate']:>9.2f} {summary['second_half_first_attempt_rate']:>9.2f}"
        )
    return "\n".join(lines)
