"""Exceptions in the shape the instructor-wrapped client raises in production.

instructor's ``retry_sync_v2`` catches every exception from the API call or the
response parser and re-raises it as ``InstructorRetryException`` chained
``from`` the original. ``failed_attempts`` holds only parse and validation
failures, so a transport error produces an empty list.
"""

import json

import httpx
import openai
from instructor.core import FailedAttempt, InstructorRetryException

from asago_policy_mapper.extract.models import _CausalChains

_REQUEST = httpx.Request("POST", "http://localhost:8000/v1/chat/completions")


def _wrap(cause: Exception, failed_attempts: list[FailedAttempt]) -> InstructorRetryException:
    exc = InstructorRetryException(
        str(cause),
        n_attempts=1,
        total_usage=0,
        failed_attempts=failed_attempts,
    )
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


def validation_exhaustion(cause: Exception | None = None) -> InstructorRetryException:
    """Retries exhausted because the model output failed parsing or validation."""
    cause = cause if cause is not None else pydantic_validation_error()
    return _wrap(cause, [FailedAttempt(attempt_number=1, exception=cause, completion=None)])


def connection_failure() -> InstructorRetryException:
    return _wrap(openai.APIConnectionError(request=_REQUEST), [])


def server_error(status_code: int = 503) -> InstructorRetryException:
    response = httpx.Response(status_code, request=_REQUEST)
    cause = openai.InternalServerError("Service Unavailable", response=response, body=None)
    return _wrap(cause, [])


def authentication_failure() -> InstructorRetryException:
    response = httpx.Response(401, request=_REQUEST)
    return _wrap(openai.AuthenticationError("Unauthorized", response=response, body=None), [])
