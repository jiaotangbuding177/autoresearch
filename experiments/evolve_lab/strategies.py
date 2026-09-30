"""Self-evolution strategies compared in the experiment.

All strategies share:
- the same attempt budget (max_attempts)
- the same real verifier (sandbox.run_solution)
- the same backend (mock or real)

They differ in WHAT they feed back into the next generation call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .backends import GenerationContext, LLMBackend
from .sandbox import run_solution
from .tasks import Task


@dataclass
class TaskOutcome:
    task_id: str
    success: bool
    first_attempt_success: bool
    attempts_used: int
    llm_calls: int


@dataclass
class StrategyResult:
    name: str
    outcomes: list[TaskOutcome] = field(default_factory=list)

    # aggregate helpers -----------------------------------------------------
    @property
    def success_rate(self) -> float:
        return _mean([o.success for o in self.outcomes])

    @property
    def first_attempt_rate(self) -> float:
        return _mean([o.first_attempt_success for o in self.outcomes])

    @property
    def avg_attempts(self) -> float:
        return _mean([o.attempts_used for o in self.outcomes])

    @property
    def total_calls(self) -> int:
        return sum(o.llm_calls for o in self.outcomes)

    def first_half_first_attempt_rate(self) -> float:
        half = max(1, len(self.outcomes) // 2)
        return _mean([o.first_attempt_success for o in self.outcomes[:half]])

    def second_half_first_attempt_rate(self) -> float:
        half = max(1, len(self.outcomes) // 2)
        return _mean([o.first_attempt_success for o in self.outcomes[half:]])


def _mean(values: list[bool]) -> float:
    return sum(values) / len(values) if values else 0.0


class Strategy:
    """Base class. Subclasses implement `solve`."""

    name = "base"
    uses_insights = False

    def __init__(self, backend: LLMBackend, max_attempts: int = 5) -> None:
        self.backend = backend
        self.max_attempts = max_attempts

    def solve(self, task: Task, insights: list[str]) -> TaskOutcome:
        raise NotImplementedError

    # shared helpers --------------------------------------------------------
    @staticmethod
    def _verify(task: Task, code: str) -> tuple[bool, str]:
        result = run_solution(task, code)
        return result.passed, result.output


class Direct(Strategy):
    """One shot. No feedback, no memory."""

    name = "direct"

    def solve(self, task: Task, insights: list[str]) -> TaskOutcome:
        context = GenerationContext(attempt=0, insights=insights)
        code = self.backend.generate(task, context)
        passed, _ = self._verify(task, code)
        return TaskOutcome(task.id, passed, passed, 1, 1)


class BestOfN(Strategy):
    """N independent samples; the first passing one wins."""

    name = "best_of_n"

    def __init__(self, backend: LLMBackend, max_attempts: int = 5, n: int = 5) -> None:
        super().__init__(backend, max_attempts)
        self.n = n

    def solve(self, task: Task, insights: list[str]) -> TaskOutcome:
        calls = 0
        first_passed = False
        for attempt in range(self.n):
            context = GenerationContext(attempt=attempt, insights=insights)
            code = self.backend.generate(task, context)
            calls += 1
            passed, _ = self._verify(task, code)
            if attempt == 0:
                first_passed = passed
            if passed:
                return TaskOutcome(task.id, True, first_passed, attempt + 1, calls)
        return TaskOutcome(task.id, False, first_passed, self.n, calls)


class SelfRefine(Strategy):
    """Iterate within one attempt using self-critique only (no test output)."""

    name = "self_refine"

    def __init__(self, backend: LLMBackend, max_attempts: int = 5, rounds: int = 4) -> None:
        super().__init__(backend, max_attempts)
        self.rounds = rounds

    def solve(self, task: Task, insights: list[str]) -> TaskOutcome:
        calls = 0
        context = GenerationContext(attempt=0, insights=insights)
        code = self.backend.generate(task, context)
        calls += 1
        passed, output = self._verify(task, code)
        first_passed = passed
        if passed:
            return TaskOutcome(task.id, True, first_passed, 1, calls)

        critiques: list[str] = []
        for round_index in range(self.rounds):
            critique = self.backend.critique(task, code, GenerationContext(attempt=round_index))
            calls += 1
            critiques.append(critique)
            context = GenerationContext(
                attempt=round_index + 1,
                reflections=critiques,
                insights=insights,
                code_so_far=code,
            )
            code = self.backend.generate(task, context)
            calls += 1
            passed, output = self._verify(task, code)
            if passed:
                return TaskOutcome(task.id, True, first_passed, round_index + 2, calls)
        return TaskOutcome(task.id, False, first_passed, 1 + self.rounds, calls)


class Reflexion(Strategy):
    """Sequential attempts; between attempts it reflects on REAL test output."""

    name = "reflexion"

    def solve(self, task: Task, insights: list[str]) -> TaskOutcome:
        calls = 0
        reflections: list[str] = []
        first_passed = False
        last_code = ""
        last_output = ""
        for attempt in range(self.max_attempts):
            context = GenerationContext(
                attempt=attempt, reflections=reflections, insights=insights
            )
            code = self.backend.generate(task, context)
            calls += 1
            passed, output = self._verify(task, code)
            if attempt == 0:
                first_passed = passed
            if passed:
                return TaskOutcome(task.id, True, first_passed, attempt + 1, calls)
            reflection = self.backend.reflect(task, code, output)
            calls += 1
            reflections.append(reflection)
            last_code, last_output = code, output
        # budget exhausted: record a final reflection for the trajectory log
        _ = self.backend.reflect(task, last_code, last_output)
        calls += 1
        return TaskOutcome(task.id, False, first_passed, self.max_attempts, calls)


class ReflexionPlusInsights(Reflexion):
    """Reflexion + ExpeL-style cross-task insight extraction and reuse."""

    name = "reflexion_insights"
    uses_insights = True

    def solve(self, task: Task, insights: list[str]) -> TaskOutcome:
        calls = 0
        reflections: list[str] = []
        trajectory: list[str] = []
        first_passed = False
        for attempt in range(self.max_attempts):
            context = GenerationContext(
                attempt=attempt, reflections=reflections, insights=insights
            )
            code = self.backend.generate(task, context)
            calls += 1
            passed, output = self._verify(task, code)
            if attempt == 0:
                first_passed = passed
            if passed:
                trajectory.append(f"attempt {attempt + 1}: PASSED")
                new_insights = self.backend.extract_insights(task, trajectory)
                calls += 1
                insights.extend(new_insights)
                return TaskOutcome(task.id, True, first_passed, attempt + 1, calls)
            reflection = self.backend.reflect(task, code, output)
            calls += 1
            reflections.append(reflection)
            trajectory.append(f"attempt {attempt + 1}: FAILED — {reflection}")
        new_insights = self.backend.extract_insights(task, trajectory)
        calls += 1
        insights.extend(new_insights)
        return TaskOutcome(task.id, False, first_passed, self.max_attempts, calls)


STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    Direct.name: Direct,
    BestOfN.name: BestOfN,
    SelfRefine.name: SelfRefine,
    Reflexion.name: Reflexion,
    ReflexionPlusInsights.name: ReflexionPlusInsights,
}
