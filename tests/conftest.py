"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def test_config_dir(project_root):
    """Return the test config directory"""
    return project_root / "config"

