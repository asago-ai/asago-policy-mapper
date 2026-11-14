"""Tests for the SDK retry and timeout settings on LLMConfig.

The OpenAI SDK's transport-level retry count and timeout are now explicit
and configurable independently of the mapper's own validation retries:
``LLMConfig.sdk_max_retries`` and ``LLMConfig.sdk_timeout_s`` go to
``OpenAI(...)`` only, never into a completion request, and default from
``POLICY_MAPPER_SDK_MAX_RETRIES`` / ``POLICY_MAPPER_SDK_TIMEOUT_S`` when the
constructor leaves them unset.
"""

from unittest.mock import patch

import httpx
import openai
import pytest

from asago_policy_mapper.llm import LLMConfig, create_client


class _CapturedOpenAI:
    """Records the constructor kwargs create_client passes to OpenAI."""

    instances: list = []

    def __init__(self, **kwargs):
        self.kwargs = dict(kwargs)
        # A real client over a dead transport: create_client only constructs
        # it, no request is made in these tests.
        self._real = openai.OpenAI(**kwargs)
        self.chat = self._real.chat
        type(self).instances.append(self)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("POLICY_MAPPER_SDK_MAX_RETRIES", raising=False)
    monkeypatch.delenv("POLICY_MAPPER_SDK_TIMEOUT_S", raising=False)


@pytest.fixture
def captured():
    _CapturedOpenAI.instances = []
    with patch("asago_policy_mapper.llm.OpenAI", _CapturedOpenAI):
        yield _CapturedOpenAI


def _config(**kwargs) -> LLMConfig:
    return LLMConfig(base_url="http://localhost:8000/v1", model="test-model", **kwargs)


class TestCreateClientSdkSettings:
    def test_create_client_passes_explicit_sdk_retries_and_timeout(self, captured):
        create_client(_config(sdk_max_retries=5, sdk_timeout_s=12.5))
        (instance,) = captured.instances
        assert instance.kwargs["max_retries"] == 5
        assert instance.kwargs["timeout"] == 12.5

    def test_sdk_settings_independent_of_validation_retries(self, captured):
        """LLMConfig.max_retries (validation retries) never reaches OpenAI(...)."""
        create_client(_config(max_retries=7, sdk_max_retries=1, sdk_timeout_s=30.0))
        (instance,) = captured.instances
        assert instance.kwargs["max_retries"] == 1
        assert instance.kwargs["timeout"] == 30.0

        # The validation retries keep their meaning: the same kwargs reach
        # the retry loop's config, and the create call still accepts the
        # caller's max_retries kwarg without forwarding it to the SDK.
        config = _config(max_retries=7, sdk_max_retries=1, sdk_timeout_s=30.0)
        assert config.max_retries == 7
        assert config.sdk_max_retries == 1

    def test_unset_sdk_settings_pass_sdk_defaults(self, captured):
        """Unset values become the SDK's own defaults, explicitly."""
        create_client(_config())
        (instance,) = captured.instances
        assert instance.kwargs["max_retries"] == openai.DEFAULT_MAX_RETRIES
        assert instance.kwargs["timeout"] == openai.DEFAULT_TIMEOUT

    def test_sdk_settings_never_reach_the_completion_request(self):
        """Neither value is ever sent as a completion parameter."""
        requests = []

        def handler(request):
            requests.append(request.read().decode())
            body = {
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
            return httpx.Response(200, json=body)

        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(
                _config(sdk_max_retries=9, sdk_timeout_s=99.0, max_context=0, max_tokens=64),
            )
        client.chat.completions.create(
            model="test-model",
            messages=[{"role": "user", "content": "hi"}],
        )
        (wire,) = requests
        assert "max_retries" not in wire
        assert "timeout" not in wire


class TestSdkEnvDefaults:
    def test_sdk_env_defaults_and_constructor_override(self, captured, monkeypatch):
        """Env vars fill unset fields; a constructor value wins over the env."""
        monkeypatch.setenv("POLICY_MAPPER_SDK_MAX_RETRIES", "6")
        monkeypatch.setenv("POLICY_MAPPER_SDK_TIMEOUT_S", "42.5")

        create_client(_config())
        (from_env,) = captured.instances
        assert from_env.kwargs["max_retries"] == 6
        assert from_env.kwargs["timeout"] == 42.5

        create_client(_config(sdk_max_retries=2, sdk_timeout_s=8.0))
        override = captured.instances[-1]
        assert override.kwargs["max_retries"] == 2
        assert override.kwargs["timeout"] == 8.0

    def test_env_values_are_read_in_llm_config_fields(self, monkeypatch):
        """The env defaults land on the config, so callers can inspect them."""
        monkeypatch.setenv("POLICY_MAPPER_SDK_MAX_RETRIES", "4")
        monkeypatch.setenv("POLICY_MAPPER_SDK_TIMEOUT_S", "17.0")
        config = _config()
        assert config.sdk_max_retries == 4
        assert config.sdk_timeout_s == 17.0

        config = _config(sdk_max_retries=None, sdk_timeout_s=None)
        assert config.sdk_max_retries == 4
        assert config.sdk_timeout_s == 17.0

    def test_env_vars_do_not_override_validation_retries(self, monkeypatch):
        """POLICY_MAPPER_SDK_MAX_RETRIES leaves max_retries (validation) alone."""
        monkeypatch.setenv("POLICY_MAPPER_SDK_MAX_RETRIES", "6")
        config = _config()
        assert config.max_retries == 3


class TestInvalidSdkSettings:
    def test_invalid_sdk_settings_fail_before_client_creation(self, captured):
        """Validation rejects bad values without constructing OpenAI(...)."""
        with pytest.raises(ValueError, match="sdk_max_retries"):
            create_client(_config(sdk_max_retries=-1))
        with pytest.raises(ValueError, match="sdk_timeout_s"):
            create_client(_config(sdk_timeout_s=0.0))
        with pytest.raises(ValueError, match="sdk_timeout_s"):
            create_client(_config(sdk_timeout_s=-5.0))
        with pytest.raises(ValueError, match="sdk_timeout_s"):
            create_client(_config(sdk_timeout_s=float("inf")))
        with pytest.raises(ValueError, match="sdk_timeout_s"):
            create_client(_config(sdk_timeout_s=float("nan")))
        assert captured.instances == []

    def test_zero_sdk_retries_is_valid(self, captured):
        """Zero transport retries is a legal setting (retry count at least 0)."""
        create_client(_config(sdk_max_retries=0))
        (instance,) = captured.instances
        assert instance.kwargs["max_retries"] == 0

    def test_constructor_rejects_invalid_values_directly(self):
        """LLMConfig itself validates, so a bad value fails at construction."""
        with pytest.raises(ValueError, match="sdk_max_retries"):
            _config(sdk_max_retries=-2)
        with pytest.raises(ValueError, match="sdk_timeout_s"):
            _config(sdk_timeout_s=0.0)
