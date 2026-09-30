"""Empirically verify the task suite's signature contract.

For every task:
1. the correct solution must PASS its tests
2. every buggy variant must FAIL its tests
3. the variant's signature must appear in its own real failure output
4. no signature may appear in the output of the correct solution, nor in the
   output of a DIFFERENT variant of the same task (uniqueness)

Run: python experiments/scripts/verify_tasks.py
Exit code 0 == all checks green.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evolve_lab.sandbox import run_solution  # noqa: E402
from evolve_lab.tasks import TASKS  # noqa: E402


def main() -> int:
    failures: list[str] = []
    for task in TASKS:
        result = run_solution(task, task.correct)
        if not result.passed:
            failures.append(f"{task.id}: correct solution FAILED its own tests")
            print(result.output)
    print("solutions: checked")

    for task in TASKS:
        correct_output = run_solution(task, task.correct).output
        variant_outputs: dict[str, str] = {}
        for bug in task.buggy:
            res = run_solution(task, bug.code)
            variant_outputs[bug.id] = res.output
            if res.passed:
                failures.append(f"{task.id}/{bug.id}: buggy variant PASSED tests (not buggy!)")
            if bug.signature not in res.output:
                failures.append(
                    f"{task.id}/{bug.id}: signature {bug.signature!r} NOT found in its own output"
                )
        for bug in task.buggy:
            if bug.signature in correct_output:
                failures.append(
                    f"{task.id}/{bug.id}: signature {bug.signature!r} leaks into CORRECT output"
                )
            for other_id, output in variant_outputs.items():
                if other_id != bug.id and bug.signature in output:
                    failures.append(
                        f"{task.id}/{bug.id}: signature {bug.signature!r} also appears in variant '{other_id}'"
                    )
    print("signatures: checked")

    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"\nAll checks green for {len(TASKS)} tasks "
          f"({sum(len(t.buggy) for t in TASKS)} buggy variants with unique signatures).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
