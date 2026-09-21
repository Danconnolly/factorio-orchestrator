from contextlib import contextmanager
import gc
import hashlib
from pathlib import Path
import tempfile
import unittest
import warnings

from inspect_ai import eval

from factorio_benchmark.smelt_session import SmeltSessionRuntime
from factorio_orchestrator.task import smelt_one_iron_plate


@contextmanager
def _fake_inspect_eval_cleanup():
    """Contain AnyIO's known unclosed receive-stream finalizer in fake evals.

    Inspect 0.3.266 leaves these third-party streams for finalization when its
    fake session runner exits. Keep the filter exact and collect before leaving
    the scope so real ResourceWarnings remain visible to the suite.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"^Unclosed <MemoryObjectReceiveStream at [0-9a-f]+>$",
            category=ResourceWarning,
            module=r"^anyio\.streams\.memory$",
        )
        yield
        gc.collect()


class InspectSmokeTests(unittest.TestCase):
    def test_fake_eval_cleanup_only_ignores_known_anyio_finalizer_warning(self) -> None:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            with _fake_inspect_eval_cleanup():
                warnings.warn_explicit(
                    "Unclosed <MemoryObjectReceiveStream at deadbeef>",
                    ResourceWarning,
                    filename="memory.py",
                    lineno=190,
                    module="anyio.streams.memory",
                )
                warnings.warn_explicit(
                    "Unclosed <MemoryObjectReceiveStream at deadbeef>",
                    ResourceWarning,
                    filename="other.py",
                    lineno=1,
                    module="anyio.streams.other",
                )
        self.assertEqual(len(captured), 1)

    @_fake_inspect_eval_cleanup()
    def test_local_inspect_eval_records_benchmark_bundle_and_evaluator_score(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = SmeltSessionRuntime(*(Path(directory) / name for name in ("factorio", "python", "mod.zip", "client", "runs", "run")))
            def fake_runner(**kwargs):
                return {"eligible_for_scoring": True, "terminal_status": "completed_eligible", "score": {"score": 1.0}, "run_bundle_path": "/fake/run", "artifacts": {}}
            logs = eval(smelt_one_iron_plate(runtime=runtime, model_id="fake@sha256:" + "a" * 64,
                                              callback=lambda request: {"answer": "fake"}, session_runner=fake_runner))
            self.assertEqual(logs[0].samples[0].scores["evaluator_only_score"].value, 1.0)
            self.assertEqual(logs[0].samples[0].metadata["benchmark_run_bundle"], "/fake/run")

    @_fake_inspect_eval_cleanup()
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
