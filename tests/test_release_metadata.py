from pathlib import Path
import tomllib
import unittest


class ReleaseMetadataTests(unittest.TestCase):
    def test_paired_wheel_smoke_requires_the_0_2_0_release_pair(self) -> None:
        smoke = (Path(__file__).resolve().parents[1] / "scripts" / "smoke_wheel_metadata.py").read_text(encoding="utf-8")

        self.assertIn('("factorio-benchmark", "0.2.3")', smoke)
        self.assertIn('("factorio-orchestrator", "0.2.3")', smoke)
        self.assertIn('factorio-benchmark==0.2.3', smoke)

    def test_orchestrator_and_benchmark_are_released_as_the_0_2_0_pair(self) -> None:
        pyproject = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(pyproject["project"]["version"], "0.2.3")
        self.assertIn(
            "factorio-benchmark==0.2.3", pyproject["project"]["dependencies"]
        )
