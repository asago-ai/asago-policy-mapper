import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest
from unittest.mock import MagicMock
from concorde_policy_mapper.llm import LLMConfig


@pytest.fixture
def mock_config():
    return LLMConfig(base_url="http://localhost:8000/v1", model="test-model", max_context=0)


@pytest.fixture
def mock_client():
    client = MagicMock()
    return client
