"""Exceptions in the shape the structured-output client raises in production.

The client raises ``ValidationRetryExhausted`` (with ``failed_attempts``)
chained ``from`` the original error when the model output fails parsing or
validation until retries run out. A transport or API error propagates as the
original ``openai`` exception, unwrapped, so it is not masked as a validation
exhaustion.
"""

import json

import httpx
import openai

from asago_policy_mapper.extract.models import _CausalChains
from asago_policy_mapper.llm import FailedAttempt, ValidationRetryExhausted

_REQUEST = httpx.Request("POST", "http://localhost:8000/v1/chat/completions")


def _wrap(cause: Exception, failed_attempts: list[FailedAttempt]) -> ValidationRetryExhausted:
    exc = ValidationRetryExhausted(str(cause), failed_attempts=failed_attempts)
    exc.__cause__ = cause
    return exc


def pydantic_validation_error() -> Exception:
    try:
        _CausalChains.model_validate({"items": "not a list"})
    except Exception as exc:
        return exc
    raise AssertionError("expected a validation error")


def json_decode_error() -> Exception:
    try:
        json.loads('{"items": [')
    except json.JSONDecodeError as exc:
        return exc
    raise AssertionError("expected a JSON decode error")


def validation_exhaustion(cause: Exception | None = None) -> ValidationRetryExhausted:
    """Retries exhausted because the model output failed parsing or validation."""
    cause = cause if cause is not None else pydantic_validation_error()
    return _wrap(cause, [FailedAttempt(attempt_number=1, exception=cause, completion=None)])


def connection_failure() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=_REQUEST)


def server_error(status_code: int = 503) -> openai.InternalServerError:
    response = httpx.Response(status_code, request=_REQUEST)
    return openai.InternalServerError("Service Unavailable", response=response, body=None)


def authentication_failure() -> openai.AuthenticationError:
    response = httpx.Response(401, request=_REQUEST)
    return openai.AuthenticationError("Unauthorized", response=response, body=None)
