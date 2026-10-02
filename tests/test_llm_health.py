import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import instructor
import pytest
import test_llm_integration as integration
from llm_health import (
    PROBE_TIMEOUT_SECONDS,
    LLMHealthError,
    LLMUnavailableError,
    ProbeAnswer,
    probe_llm,
)
from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI

BASE_URL = "http://localhost:11434/v1"
MODEL = "gemma3:1b"


@pytest.fixture
def mock_probe():
    with patch("llm_health.OpenAI") as factory, patch("llm_health.instructor.from_openai") as wrap:
        api = factory.return_value.__enter__.return_value
        api.models.list.return_value = SimpleNamespace(data=[SimpleNamespace(id=MODEL)])
        client = wrap.return_value
        client.chat.completions.create.return_value = ProbeAnswer(answer="Ready")
        yield factory, api, wrap, client


def _server_error():
    request = httpx.Request("POST", f"{BASE_URL}/chat/completions")
    response = httpx.Response(500, request=request)
    return InternalServerError(
        "llama-server process has terminated: signal: segmentation fault", response=response, body=None
    )


def test_probe_checks_structured_inference_with_bounded_requests(mock_probe):
    factory, api, wrap, client = mock_probe

    probe_llm(BASE_URL, MODEL)

    factory.assert_called_once_with(base_url=BASE_URL, api_key="none", timeout=PROBE_TIMEOUT_SECONDS, max_retries=0)
    api.models.list.assert_called_once_with()
    wrap.assert_called_once_with(api, mode=instructor.Mode.JSON_SCHEMA)
    call = client.chat.completions.create.call_args.kwargs
    assert call["model"] == MODEL
    assert call["response_model"] is ProbeAnswer
    assert call["max_tokens"] == 128
    assert call["temperature"] == 0.0
    assert call["max_retries"] == 0
    factory.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("error_type", [APIConnectionError, APITimeoutError])
def test_probe_reports_unavailable_api(mock_probe, error_type):
    factory, api, wrap, _ = mock_probe
    api.models.list.side_effect = error_type(request=httpx.Request("GET", f"{BASE_URL}/models"))

    with pytest.raises(LLMUnavailableError, match="LLM server not available"):
        probe_llm(BASE_URL, MODEL)

    wrap.assert_not_called()
    factory.return_value.__exit__.assert_called_once()


def test_probe_reports_api_server_error_as_failure(mock_probe):
    _, api, wrap, _ = mock_probe
    api.models.list.side_effect = _server_error()

    with pytest.raises(LLMHealthError, match="LLM model probe failed") as exc:
        probe_llm(BASE_URL, MODEL)

    assert not isinstance(exc.value, LLMUnavailableError)
    wrap.assert_not_called()


def test_probe_rejects_missing_model(mock_probe):
    _, api, wrap, _ = mock_probe
    api.models.list.return_value = SimpleNamespace(data=[SimpleNamespace(id="other-model")])

    with pytest.raises(LLMHealthError, match="Model 'gemma3:1b' not available"):
        probe_llm(BASE_URL, MODEL)

    wrap.assert_not_called()


def test_probe_reports_backend_crash_without_retry(mock_probe):
    factory, _, _, client = mock_probe
    client.chat.completions.create.side_effect = _server_error()

    with pytest.raises(LLMHealthError, match="LLM inference probe failed.*segmentation fault"):
        probe_llm(BASE_URL, MODEL)

    client.chat.completions.create.assert_called_once()
    factory.return_value.__exit__.assert_called_once()


def test_probe_reports_inference_timeout_as_failure(mock_probe):
    _, _, _, client = mock_probe
    client.chat.completions.create.side_effect = APITimeoutError(
        request=httpx.Request("POST", f"{BASE_URL}/chat/completions")
    )

    with pytest.raises(LLMHealthError, match="LLM inference probe failed") as exc:
        probe_llm(BASE_URL, MODEL)

    assert not isinstance(exc.value, LLMUnavailableError)
    client.chat.completions.create.assert_called_once()


@pytest.mark.parametrize("answer", ["", "  "])
def test_probe_rejects_empty_completion(mock_probe, answer):
    _, _, _, client = mock_probe
    client.chat.completions.create.return_value = ProbeAnswer(answer=answer)

    with pytest.raises(LLMHealthError, match="The completion contains no answer"):
        probe_llm(BASE_URL, MODEL)


@pytest.mark.parametrize(
    ("status_code", "content", "expected_error"),
    [
        (200, '{"answer":"Ready"}', None),
        (200, "not JSON", "LLM inference probe failed"),
        (500, "llama-server process has terminated: signal: segmentation fault", "segmentation fault"),
    ],
)
def test_probe_with_real_sdk_and_instructor(monkeypatch, status_code, content, expected_error):
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.path == "/v1/models":
            return httpx.Response(
                200,
                json={"object": "list", "data": [{"id": MODEL, "object": "model", "created": 0, "owned_by": "test"}]},
            )
        assert request.url.path == "/v1/chat/completions"
        if status_code != 200:
            return httpx.Response(status_code, json={"error": {"message": content, "type": "api_error"}})
        return httpx.Response(
            200,
            json={
                "id": "probe",
                "object": "chat.completion",
                "created": 0,
                "model": MODEL,
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}
                ],
            },
        )

    def create_probe(**kwargs):
        return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond)))

    monkeypatch.setattr("llm_health.OpenAI", create_probe)
    if expected_error is None:
        probe_llm(BASE_URL, MODEL)
    else:
        with pytest.raises(LLMHealthError, match=expected_error):
            probe_llm(BASE_URL, MODEL)

    assert len(requests) == 2
    body = json.loads(requests[1].content)
    assert body["response_format"]["type"] == "json_schema"
    assert body["max_tokens"] == 128


@pytest.fixture
def fixture_probe(monkeypatch):
    probe = MagicMock()
    monkeypatch.setattr(integration, "probe_llm", probe)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_REQUIRE_SERVER", raising=False)
    return probe


def test_llm_config_skips_unavailable_optional_server(fixture_probe):
    fixture_probe.side_effect = LLMUnavailableError("LLM server not available")

    with pytest.raises(pytest.skip.Exception, match="LLM server not available"):
        integration.llm_config.__wrapped__()


def test_llm_config_fails_unavailable_required_server(fixture_probe, monkeypatch):
    monkeypatch.setenv("LLM_REQUIRE_SERVER", "1")
    fixture_probe.side_effect = LLMUnavailableError("LLM server not available")

    with pytest.raises(pytest.fail.Exception, match="LLM server not available"):
        integration.llm_config.__wrapped__()


def test_llm_config_fails_unhealthy_inference(fixture_probe):
    fixture_probe.side_effect = LLMHealthError("LLM inference probe failed: segmentation fault")

    with pytest.raises(pytest.fail.Exception, match="segmentation fault"):
        integration.llm_config.__wrapped__()


def test_llm_config_probes_configured_endpoint(fixture_probe, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://custom-server/v1")
    monkeypatch.setenv("LLM_MODEL", "custom-model")

    config = integration.llm_config.__wrapped__()

    fixture_probe.assert_called_once_with("http://custom-server/v1", "custom-model")
    assert config.base_url == "http://custom-server/v1"
    assert config.model == "custom-model"
