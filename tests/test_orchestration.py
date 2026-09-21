import unittest

from factorio_orchestrator.config import OrchestrationConfig
from factorio_orchestrator.scoring import benchmark_score


class OrchestrationTests(unittest.TestCase):
    def test_config_requires_explicit_paths_and_pinned_model_identity(self) -> None:
        config = OrchestrationConfig.from_mapping({
            "model_id": "qwen@sha256:" + "a" * 64,
            "model_base_url": "http://model.test/v1",
            "runtime": {"factorio": "/opt/factorio", "control_python": "/opt/control/python", "mod_archive": "/opt/mod.zip", "client_template": "/opt/client", "runs_dir": "/tmp/runs"},
        })
        self.assertEqual(config.model_id[:4], "qwen")
        with self.assertRaisesRegex(ValueError, "pinned"):
            OrchestrationConfig.from_mapping({"model_id": "qwen:latest", "model_base_url": "http://x", "runtime": {}})
        for model_id in ("qwen@sha256:" + "A" * 64, "qwen@sha256:" + "a" * 63,
                         "qwen@sha256:" + "a" * 65, "@sha256:" + "a" * 64,
                         "qwen@sha256:" + "g" * 64, "not a name@sha256:" + "a" * 64):
            with self.subTest(model_id=model_id), self.assertRaisesRegex(ValueError, "pinned"):
                OrchestrationConfig.from_mapping({
                    "model_id": model_id, "model_base_url": "http://x",
                    "runtime": {"factorio": "/a", "control_python": "/b", "mod_archive": "/c", "client_template": "/d", "runs_dir": "/e"},
                })

    def test_score_is_only_the_evaluator_result_and_unscored_stays_unscored(self) -> None:
        self.assertEqual(benchmark_score({"score": {"score": 1.0}, "eligible_for_scoring": True}), 1.0)
        self.assertIsNone(benchmark_score({"score": {"score": 1.0}, "eligible_for_scoring": False}))
        self.assertIsNone(benchmark_score({"terminal_status": "agent_timeout"}))
