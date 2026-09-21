"""The one-sample Inspect task backed by a benchmark-owned session."""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Mapping

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, scorer
from inspect_ai.solver import Solver, solver

from factorio_benchmark.smelt_session import SmeltSessionRuntime, run_smelt_callback_session
from factorio_benchmark.session import CallbackRequest

from .scoring import benchmark_score


@scorer(metrics=[])
def evaluator_only_score():
    async def score(state, target):
        value = benchmark_score(state.store.get("benchmark_result", {}))
        return Score(value=value, explanation="benchmark evaluator result") if value is not None else None
    return score


def benchmark_session_solver(*, runtime: SmeltSessionRuntime, model_id: str,
                             callback: Callable[[CallbackRequest], Mapping[str, Any]],
                             session_runner: Callable[..., Mapping[str, Any]] = run_smelt_callback_session) -> Solver:
    @solver
    def solve() -> Solver:
        async def run(state, generate):
            result = await asyncio.to_thread(
                session_runner, runtime=runtime, model_id=model_id, callback=callback,
            )
            state.store.set("benchmark_result", result)
            state.metadata["benchmark_run_bundle"] = result.get("run_bundle_path", str(runtime.runs_dir / runtime.run_name))
            state.metadata["benchmark_terminal_status"] = result.get("terminal_status")
            return state
        return run
    return solve()


@task
def smelt_one_iron_plate(*, runtime: SmeltSessionRuntime, model_id: str,
                          callback: Callable[[CallbackRequest], Mapping[str, Any]],
                          session_runner: Callable[..., Mapping[str, Any]] = run_smelt_callback_session) -> Task:
    """Inspect task whose score comes only from benchmark's evaluator."""
    return Task(
        dataset=[Sample(input="Run the benchmark-provided smelt-one-iron-plate prompt.", id="smelt-one-iron-plate")],
        solver=benchmark_session_solver(runtime=runtime, model_id=model_id, callback=callback, session_runner=session_runner),
        scorer=evaluator_only_score(), epochs=1,
        metadata={"scenario_id": "smelt-one-iron-plate", "model_id": model_id},
    )
