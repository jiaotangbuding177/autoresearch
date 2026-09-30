"""evolve_lab: a small harness comparing self-evolution strategies for code
generation agents, with real executable verification.
"""

from .backends import LLMBackend, MockBackend, OpenAIBackend, make_backend
from .runner import DEFAULT_STRATEGIES, format_report, run_experiment, run_strategy
from .sandbox import run_solution
from .strategies import STRATEGY_REGISTRY, Strategy, StrategyResult
from .tasks import TASKS, TASKS_BY_ID, BugVariant, Task

__all__ = [
    "LLMBackend",
    "MockBackend",
    "OpenAIBackend",
    "make_backend",
    "DEFAULT_STRATEGIES",
    "format_report",
    "run_experiment",
    "run_strategy",
    "run_solution",
    "STRATEGY_REGISTRY",
    "Strategy",
    "StrategyResult",
    "TASKS",
    "TASKS_BY_ID",
    "BugVariant",
    "Task",
]
