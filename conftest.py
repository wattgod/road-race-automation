"""Shared pytest fixtures for road-race-automation."""

import json
import pytest
from pathlib import Path


BASE_DIR = Path(__file__).parent


@pytest.fixture
def base_dir():
    return BASE_DIR


@pytest.fixture
def config():
    config_path = BASE_DIR / "config" / "dimensions.json"
    return json.loads(config_path.read_text())
