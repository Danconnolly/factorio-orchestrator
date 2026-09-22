from pathlib import Path
import tomllib
import unittest


class ReleaseMetadataTests(unittest.TestCase):
    def test_orchestrator_and_benchmark_are_released_as_the_0_2_0_pair(self) -> None:
        pyproject = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(pyproject["project"]["version"], "0.2.0")
        self.assertIn(
            "factorio-benchmark==0.2.0", pyproject["project"]["dependencies"]
        )
