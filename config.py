"""YAML configuration management module."""

from pathlib import Path
from typing import Any

import yaml


class _Section:
    """Nested configuration section with attribute access."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        for key, value in (data or {}).items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

    def __repr__(self) -> str:
        return repr(self.__dict__)


class Config:
    """Application configuration loaded from YAML."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        for key, value in data.items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

    def __repr__(self) -> str:
        return repr(self.__dict__)


cfg = Config()
