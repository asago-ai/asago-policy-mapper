import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add tests directory and project root to path for experiments imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from asago_policy_mapper.llm import LLMConfig


def pytest_addoption(parser):
    parser.addoption(
        "--test-llm", action="store_true", default=False, help="Run LLM integration tests (requires a live LLM server)"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--test-llm"):
        return
    skip_llm = pytest.mark.skip(reason="LLM tests disabled by default — pass --test-llm to enable")
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(skip_llm)


@pytest.fixture
def mock_config():
    return LLMConfig(base_url="http://localhost:8000/v1", model="test-model", max_context=0)


@pytest.fixture
def mock_client():
    client = MagicMock()
    return client
