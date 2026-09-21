"""Portable, explicit orchestration configuration."""
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimePaths:
    factorio: Path
    control_python: Path
    mod_archive: Path
    client_template: Path
    runs_dir: Path


@dataclass(frozen=True)
class OrchestrationConfig:
    model_id: str
    model_base_url: str
    runtime: RuntimePaths

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "OrchestrationConfig":
        model_id = value.get("model_id")
        if not isinstance(model_id, str) or not re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", model_id):
            raise ValueError("model_id must be a pinned digest identity")
        base_url = value.get("model_base_url")
        if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
            raise ValueError("model_base_url must be an explicit HTTP URL")
        runtime = value.get("runtime")
        if not isinstance(runtime, Mapping):
            raise ValueError("runtime paths are required")
        names = ("factorio", "control_python", "mod_archive", "client_template", "runs_dir")
        if any(not isinstance(runtime.get(name), str) or not runtime[name] for name in names):
            raise ValueError("all explicit runtime paths are required")
        return cls(model_id=model_id, model_base_url=base_url,
                   runtime=RuntimePaths(**{name: Path(runtime[name]) for name in names}))
