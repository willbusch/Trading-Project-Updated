"""Loads config.yaml once and exposes it as a plain dict.

Every strategy threshold lives in config.yaml. Code should read values from
here, never hard-code a number that config.yaml already names.
"""
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

_config = None


def load_config() -> dict:
    global _config
    if _config is None:
        with open(_CONFIG_PATH, "r") as f:
            _config = yaml.safe_load(f)
    return _config
