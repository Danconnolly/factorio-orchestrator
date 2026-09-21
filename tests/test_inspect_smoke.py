import tempfile
import unittest
import hashlib
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

    def test_failed_fake_session_records_terminal_bundle_and_manifest_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "failed-run"
            bundle.mkdir()
            manifest = bundle / "run-manifest.json"
            manifest.write_text('{"terminal_status":"runner_failed"}\n', encoding="utf-8")
            runtime = SmeltSessionRuntime(*(root / name for name in ("factorio", "python", "mod.zip", "client", "runs", "run")))

            def fake_runner(**kwargs):
                return {"eligible_for_scoring": False, "terminal_status": "runner_failed",
                        "score": {"score": 0.0}, "run_bundle_path": str(bundle)}

            logs = eval(smelt_one_iron_plate(runtime=runtime, model_id="fake@sha256:" + "a" * 64,
                                              callback=lambda request: {"answer": "fake"}, session_runner=fake_runner))
            metadata = logs[0].samples[0].metadata
            self.assertEqual(metadata["benchmark_run_bundle"], str(bundle.resolve()))
            self.assertEqual(metadata["benchmark_terminal_status"], "runner_failed")
            self.assertEqual(metadata["benchmark_run_manifest_sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
