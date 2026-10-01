"""LLM backends: a deterministic MockBackend for offline mechanics and an
OpenAIBackend for real experiments against any OpenAI-compatible endpoint.
"""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field

from .tasks import BugVariant, Task


@dataclass
class GenerationContext:
    """Everything the strategy wants the backend to condition on."""

    attempt: int = 0
    reflections: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    code_so_far: str | None = None  # used by refinement-style strategies


class LLMBackend:
    """Interface every backend implements. One call == one LLM invocation."""

    name = "base"

    def generate(self, task: Task, context: GenerationContext) -> str:
        raise NotImplementedError

    def critique(self, task: Task, code: str, context: GenerationContext) -> str:
        """Self-critique WITHOUT external feedback (self-refine style)."""
        raise NotImplementedError

    def reflect(self, task: Task, code: str, failure_output: str) -> str:
        """Reflection given a REAL failure output from executing the code."""
        raise NotImplementedError

    def extract_insights(self, task: Task, trajectory: list[str]) -> list[str]:
        """Cross-task transferable insights (ExpeL style)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mock backend
# ---------------------------------------------------------------------------

def _seeded_rng(*parts: object) -> random.Random:
    key = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


class MockBackend(LLMBackend):
    """Deterministic simulated model.

    Behaviour model (documented in logs/iteration-14):
    - fresh attempt succeeds with probability task.base_p
    - otherwise it samples one of the task's typical bug variants
    - bugs already named in stored reflections are avoided (Reflexion memory)
    - each stored cross-task insight nudges base_p up by 0.05 (ExpeL transfer)
    - self-critique (no external signal) spots a bug with p=0.5 per round
    """

    name = "mock"

    def __init__(self, seed: int = 7, critique_accuracy: float = 0.5) -> None:
        self.seed = seed
        self.critique_accuracy = critique_accuracy

    def _avoid_set(self, task: Task, context: GenerationContext) -> set[str]:
        avoid: set[str] = set()
        for reflection in context.reflections:
            for bug in task.buggy:
                if f"'{bug.id}'" in reflection:
                    avoid.add(bug.id)
        return avoid

    def generate(self, task: Task, context: GenerationContext) -> str:
        rng = _seeded_rng(self.seed, "generate", task.id, context.attempt, len(context.reflections))
        p = task.base_p + 0.05 * len(context.insights) + 0.02 * len(context.reflections)
        p = min(p, 0.97)
        if rng.random() < p:
            return task.correct
        avoid = self._avoid_set(task, context)
        pool = [b for b in task.buggy if b.id not in avoid]
        if not pool:
            return task.correct  # every known failure mode has been reflected upon
        return rng.choice(pool).code

    def critique(self, task: Task, code: str, context: GenerationContext) -> str:
        rng = _seeded_rng(self.seed, "critique", task.id, context.attempt, len(code))
        match = next((b for b in task.buggy if b.code == code), None)
        if match is not None and rng.random() < self.critique_accuracy:
            return (
                f"Self-critique: I notice a potential issue '{match.id}' — {match.cause}. "
                f"Suggested fix: {match.fix}."
            )
        return "Self-critique: reviewing my code against the spec, it looks correct to me."

    def reflect(self, task: Task, code: str, failure_output: str) -> str:
        hits = [b for b in task.buggy if b.signature in failure_output]
        if hits:
            parts = [
                f"Avoid failure mode '{b.id}': {b.cause}. Fix: {b.fix}." for b in hits
            ]
            return " ".join(parts)
        return (
            "The tests failed with an unrecognized error. Re-read the spec carefully "
            "and handle edge cases explicitly."
        )

    def extract_insights(self, task: Task, trajectory: list[str]) -> list[str]:
        lessons = ", ".join(sorted({b.cause for b in task.buggy}))
        return [f"insight from '{task.id}': validate edge cases — common pitfalls: {lessons}"]


# ---------------------------------------------------------------------------
# OpenAI-compatible backend
# ---------------------------------------------------------------------------

_GEN_PROMPT = """\
You are solving a small Python task. Reply with ONLY the function implementation code, no tests, no markdown fences.

Task: {description}

{memory}Write the solution now."""

_CRITIQUE_PROMPT = """\
Review the following Python solution against the task spec. Reply with a short critique; if you find an issue, name it and propose the fix.

Task: {description}

Code:
{code}
"""

_REFLECT_PROMPT = """\
A solution failed its real test suite. Diagnose the root cause and write one short, concrete lesson to remember for the next attempt.

Task: {description}

Code:
{code}

Test failure output:
{failure}

Write the lesson (plain text, 1-3 sentences)."""

_INSIGHT_PROMPT = """\
Extract one transferable engineering lesson from this coding trajectory that could help on OTHER tasks.

Task: {description}

Trajectory (attempts and outcomes):
{trajectory}

One plain-text sentence, starting with 'insight:'."""


def _memory_block(context: GenerationContext) -> str:
    parts: list[str] = []
    if context.reflections:
        parts.append("Lessons from previous failed attempts:\n" + "\n".join(f"- {r}" for r in context.reflections))
    if context.insights:
        parts.append("Transferable insights from earlier tasks:\n" + "\n".join(f"- {i}" for i in context.insights))
    if context.code_so_far:
        parts.append("Your previous version:\n" + context.code_so_far)
    if not parts:
        return ""
    return "\n\n".join(parts) + "\n\n"


class OpenAIBackend(LLMBackend):
    """Calls any OpenAI-compatible chat completions endpoint.

    Env: OPENAI_API_KEY (required), OPENAI_BASE_URL (optional; e.g. a DeepSeek,
    Zhipu or local vLLM endpoint).

    Retry policy (layered):
    - inner: openai client max_retries=5 (handles 429 + 5xx with exp. backoff)
    - outer: up to outer_retries additional calls on any exception, with jitter
    """

    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        outer_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        try:
            from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pip install openai to use the OpenAI backend") from exc
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        base_url = os.environ.get("OPENAI_BASE_URL") or None
        self._errors = (APIConnectionError, APITimeoutError, RateLimitError)
        self.client = OpenAI(api_key=api_key, base_url=base_url, max_retries=5)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.outer_retries = outer_retries
        self.base_delay = base_delay
        self._rng = random.Random()

    def _chat(self, prompt: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(self.outer_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return (response.choices[0].message.content or "").strip()
            except self._errors as exc:  # pragma: no cover - transient path
                last_exc = exc
                if attempt < self.outer_retries:
                    delay = self.base_delay * (2 ** attempt) + self._rng.uniform(0, 0.5)
                    import time as _t
                    _t.sleep(delay)
                    continue
                raise
        raise last_exc  # pragma: no cover

    def generate(self, task: Task, context: GenerationContext) -> str:
        prompt = _GEN_PROMPT.format(description=task.description, memory=_memory_block(context))
        return _strip_fences(self._chat(prompt))

    def critique(self, task: Task, code: str, context: GenerationContext) -> str:
        return self._chat(_CRITIQUE_PROMPT.format(description=task.description, code=code))

    def reflect(self, task: Task, code: str, failure_output: str) -> str:
        return self._chat(
            _REFLECT_PROMPT.format(
                description=task.description, code=code, failure=failure_output[-2000:]
            )
        )

    def extract_insights(self, task: Task, trajectory: list[str]) -> list[str]:
        text = self._chat(
            _INSIGHT_PROMPT.format(
                description=task.description, trajectory="\n".join(trajectory)[-2000:]
            )
        )
        return [text]


def _strip_fences(text: str) -> str:
    """Remove markdown code fences a model may add despite instructions."""
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines) + "\n"


def make_backend(name: str, **kwargs: object) -> LLMBackend:
    if name == "mock":
        return MockBackend(**kwargs)  # type: ignore[arg-type]
    if name == "openai":
        return OpenAIBackend(**kwargs)  # type: ignore[arg-type]
    raise ValueError(f"unknown backend: {name}")
