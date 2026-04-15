"""YAML + 环境变量 配置管理模块。"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()


class _Section:
    """支持属性访问的嵌套配置节。"""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        for key, value in (data or {}).items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

    def __repr__(self) -> str:
        return repr(self.__dict__)


# 环境变量到配置键的映射（支持嵌套键，用下划线分隔层级）
_ENV_OVERRIDES = {
    "DATABASE_URL": ("database", "url"),
    "API_KEY": ("auth", "api_key"),
    "SERVER_HOST": ("server", "host"),
    "SERVER_PORT": ("server", "port"),
    "LOG_LEVEL": ("logging", "level"),
}


class Config:
    """从 YAML 加载应用配置，环境变量可覆盖。"""

    def __init__(self, config_path: str = "config.yaml") -> None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        # 应用环境变量覆盖
        for env_key, (section, field) in _ENV_OVERRIDES.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                if section not in data:
                    data[section] = {}
                data[section][field] = env_value

        for key, value in data.items():
            setattr(self, key, _Section(value) if isinstance(value, dict) else value)

    def __repr__(self) -> str:
        return repr(self.__dict__)


cfg = Config()
