import tempfile
import unittest
from pathlib import Path

from inspect_ai import eval

from factorio_benchmark.smelt_session import SmeltSessionRuntime
from factorio_orchestrator.task import smelt_one_iron_plate


class InspectSmokeTests(unittest.TestCase):
    def test_local_inspect_eval_records_benchmark_bundle_and_evaluator_score(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = SmeltSessionRuntime(*(Path(directory) / name for name in ("factorio", "python", "mod.zip", "client", "runs", "run")))
            def fake_runner(**kwargs):
                return {"eligible_for_scoring": True, "terminal_status": "completed_eligible", "score": {"score": 1.0}, "run_bundle_path": "/fake/run", "artifacts": {}}
            logs = eval(smelt_one_iron_plate(runtime=runtime, model_id="fake@sha256:" + "a" * 64,
                                              callback=lambda request: {"answer": "fake"}, session_runner=fake_runner))
            self.assertEqual(logs[0].samples[0].scores["evaluator_only_score"].value, 1.0)
            self.assertEqual(logs[0].samples[0].metadata["benchmark_run_bundle"], "/fake/run")
