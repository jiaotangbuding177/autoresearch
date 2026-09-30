"""Real code execution: run a candidate solution against the task's tests
in a separate Python process with a timeout. No simulation here.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .tasks import Task

RUN_TIMEOUT_SECONDS = 20


@dataclass
class RunResult:
    passed: bool
    output: str


def run_solution(task: Task, code: str) -> RunResult:
    """Execute `code` against `task.tests` in a subprocess. Returns real output."""
    with tempfile.TemporaryDirectory(prefix="evolve-lab-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "solution.py").write_text(code, encoding="utf-8")
        (tmp_path / "test_solution.py").write_text(task.tests, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "test_solution", "-v"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            output = (exc.stderr or "") + "\n[TIMEOUT]"
            if isinstance(output, bytes):  # pragma: no cover - defensive
                output = output.decode("utf-8", "replace")
            return RunResult(passed=False, output=output)
    output = (proc.stdout or "") + (proc.stderr or "")
    return RunResult(passed=proc.returncode == 0, output=output)
