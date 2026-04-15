"""YAML 配置管理模块。"""

from pathlib import Path
from typing import Any

import yaml


class _Section:
    """支持属性访问的嵌套配置节。"""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        for key, value in (data or {}).items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

    def __repr__(self) -> str:
        return repr(self.__dict__)


class Config:
    """从 YAML 加载的应用配置。"""

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
