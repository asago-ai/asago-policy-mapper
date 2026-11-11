import copy
import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import openai
from openai import OpenAI
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Safety margin in token estimates for the JSON schema the structured-output
# layer adds to every request (see _response_format).
_SCHEMA_OVERHEAD_TOKENS = 500


def _strip_titles(obj: Any) -> Any:
    if isinstance(obj, dict):
        obj.pop("title", None)
        for v in obj.values():
            _strip_titles(v)
    elif isinstance(obj, list):
        for item in obj:
            _strip_titles(item)
    return obj


class SlimModel(BaseModel):
    @classmethod
    def model_json_schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
        schema = super().model_json_schema(*args, **kwargs)
        _strip_titles(schema)  # mutates in-place, and avoids no-any-return
        return schema


class StructuredOutputError(Exception):
    """Base class for the structured-output client's errors."""


class IncompleteOutputException(StructuredOutputError):
    """The completion stopped at the token limit before producing valid JSON."""

    def __init__(self, last_completion: Any = None):
        super().__init__("The output is incomplete due to a max_tokens length limit.")
        self.last_completion = last_completion


class ResponseParsingError(ValueError, StructuredOutputError):
    """The completion content is not JSON."""


class FailedAttempt:
    """One structured-output attempt that failed to parse or validate."""

    def __init__(self, attempt_number: int, exception: Exception, completion: Any = None):
        self.attempt_number = attempt_number
        self.exception = exception
        self.completion = completion


class ValidationRetryExhausted(StructuredOutputError):
    """Retries ran out because the completion kept failing to parse or validate.

    ``failed_attempts`` records one entry per parse or validation failure; a
    transport or API error raises the underlying ``openai`` exception directly
    instead, so a non-empty ``failed_attempts`` always means the model output,
    not the endpoint, was at fault.
    """

    def __init__(
        self,
        message: str,
        failed_attempts: list[FailedAttempt] | None = None,
    ):
        super().__init__(message)
        self.failed_attempts = failed_attempts or []


class StructuredOutputMode(Enum):
    """How the completion is constrained to the response model's JSON schema.

    JSON_SCHEMA sends the schema in the ``response_format`` parameter for
    server-side constrained decoding. JSON falls back to ``json_object`` and
    injects the schema into the system prompt for endpoints without schema
    support. JSON_SCHEMA_WITH_PROMPT also uses server-side constrained
    decoding, but additionally injects the schema into the system prompt in
    the block wording the instructor-wrapped client used, preserving the task
    framing the model saw before the instructor removal.
    """

    JSON_SCHEMA = "json_schema"
    JSON = "json"
    JSON_SCHEMA_WITH_PROMPT = "json_schema_with_prompt"


_INSTRUCTOR_SCHEMA_BLOCK = (
    "\n            As a genius expert, your task is to understand the content and provide\n"
    "            the parsed objects in json that match the following json_schema:\n"
    "\n"
    "\n"
    "            {schema}\n"
    "\n"
    "            Make sure to return an instance of the JSON, not the schema itself\n"
)


def _schema_block(schema: dict[str, Any]) -> str:
    """Render the schema-in-prompt block exactly as instructor Mode.JSON did.

    The odd 12-space indentation is verbatim from instructor's dedented
    template: the interpolated schema lines at column 0 break ``dedent``'s
    common-prefix removal, so the template lines keep their indentation.
    """
    return _INSTRUCTOR_SCHEMA_BLOCK.format(schema=json.dumps(schema, indent=2, ensure_ascii=False))


_SAFETY_MARGIN = 64
_MIN_OUTPUT_TOKENS = 256
_OUTPUT_TOKEN_PARAMETERS = ("max_tokens", "max_completion_tokens")


@dataclass
class LLMConfig:
    base_url: str
    model: str
    api_key: str = "none"
    temperature: float = 0.0
    top_p: float | None = None
    top_k: int | None = None
    max_retries: int = 3
    max_tokens: int = 8192
    output_token_parameter: str = "max_tokens"
    service_tier: str | None = None
    max_concurrent: int = 32
    max_context: int = 0

    def __post_init__(self):
        if self.output_token_parameter not in _OUTPUT_TOKEN_PARAMETERS:
            allowed = ", ".join(_OUTPUT_TOKEN_PARAMETERS)
            raise ValueError(f"output_token_parameter must be one of: {allowed}")
        if self.service_tier is not None:
            self.service_tier = self.service_tier.strip() or None
        if self.max_context > 0 and self.max_tokens >= self.max_context:
            self.max_tokens = self.max_context - _SAFETY_MARGIN - _SCHEMA_OVERHEAD_TOKENS


@dataclass
class TokenTracker:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    per_stage: dict[str, dict[str, int]] = field(default_factory=dict)
    incidents: list[dict] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _warned_no_usage: bool = field(default=False, repr=False)
    _current_stage: str | None = field(default=None, repr=False)
    _thread_local: threading.local = field(default_factory=threading.local, repr=False)

    @staticmethod
    def _usage_values(usage) -> tuple[int, int, int]:
        return (
            getattr(usage, "prompt_tokens", 0) or 0,
            getattr(usage, "completion_tokens", 0) or 0,
            getattr(usage, "total_tokens", 0) or 0,
        )

    def add(self, usage, stage: str | None = None) -> None:
        if usage is None:
            return
        pt, ct, tt = self._usage_values(usage)
        with self._lock:
            self.prompt_tokens += pt
            self.completion_tokens += ct
            self.total_tokens += tt
            self.calls += 1
            if stage:
                s = self.per_stage.setdefault(
                    stage, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}
                )
                s["prompt_tokens"] += pt
                s["completion_tokens"] += ct
                s["total_tokens"] += tt
                s["calls"] += 1

    def set_stage(self, stage: str | None) -> None:
        with self._lock:
            self._current_stage = stage

    def record_incident(self, kind: str, detail: str) -> None:
        with self._lock:
            incident: dict = {"kind": kind, "detail": detail}
            if self._current_stage:
                incident["stage"] = self._current_stage
            messages = getattr(self._thread_local, "current_messages", None)
            if messages:
                incident["messages"] = copy.deepcopy(messages)
            self.incidents.append(incident)

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
            "per_stage": dict(self.per_stage),
            "incidents": list(self.incidents),
        }


def estimate_tokens(text: str) -> int:
    return len(text) // 3


def estimate_message_tokens(messages: list[dict[str, str]]) -> int:
    total = 0
    for msg in messages:
        total += 4
        total += estimate_tokens(msg.get("content", ""))
    total += 2
    return total


def budget_max_tokens(
    messages: list[dict[str, str]],
    max_context: int,
    requested_max_tokens: int,
) -> int:
    if max_context <= 0:
        return requested_max_tokens

    estimated_input = estimate_message_tokens(messages) + _SCHEMA_OVERHEAD_TOKENS
    available = max_context - estimated_input - _SAFETY_MARGIN

    if available < _MIN_OUTPUT_TOKENS:
        logger.warning(
            "Token budget critically low: estimated_input=%d, max_context=%d, available_for_output=%d (min=%d)",
            estimated_input,
            max_context,
            available,
            _MIN_OUTPUT_TOKENS,
        )
        return _MIN_OUTPUT_TOKENS

    capped = min(requested_max_tokens, available)
    if capped < requested_max_tokens:
        logger.debug(
            "Budget: max_tokens %d -> %d (input~%d, context=%d)",
            requested_max_tokens,
            capped,
            estimated_input,
            max_context,
        )
    return capped


def create_client(
    config: LLMConfig,
    tracker: TokenTracker | None = None,
    mode: StructuredOutputMode | None = None,
) -> "_StructuredClient":
    """Build the tracked structured-output chat client used across the mapper.

    ``mode`` defaults to ``JSON_SCHEMA``; the ``POLICY_MAPPER_STRUCTURED_OUTPUT_MODE``
    environment variable overrides it (one of the ``StructuredOutputMode`` values,
    e.g. ``json_schema_with_prompt`` for battery comparisons).
    """
    if mode is None:
        env = os.environ.get("POLICY_MAPPER_STRUCTURED_OUTPUT_MODE")
        mode = StructuredOutputMode(env) if env else StructuredOutputMode.JSON_SCHEMA
    client = _StructuredClient(
        OpenAI(base_url=config.base_url, api_key=config.api_key),
        mode=mode,
    )
    _wrap_with_tracking(client, tracker if tracker is not None else TokenTracker(), config)
    return client


_CONTEXT_LENGTH_RE = re.compile(
    r"maximum context length is (\d+) tokens.*?(\d+) output tokens.*?(\d+) input tokens",
)


def _extract_reduced_max_tokens(exc: Exception) -> int | None:
    msg = str(exc)
    matches = list(_CONTEXT_LENGTH_RE.finditer(msg))
    if not matches:
        return None
    m = matches[-1]
    context_limit = int(m.group(1))
    input_tokens = int(m.group(3))
    new_max = context_limit - input_tokens - 32
    return new_max if new_max >= 256 else None


def _extract_response_content(completion: Any) -> str | None:
    try:
        content = completion.choices[0].message.content
        return content if isinstance(content, str) else None  # narrow from Any
    except (AttributeError, IndexError):
        return None


_TRUNCATION_FACTOR = 0.6
_MIN_USER_MESSAGE_CHARS = 500
_MAX_TRUNCATION_RETRIES = 3


def _truncate_messages(messages: list[dict[str, str]]) -> list[dict[str, str]] | None:
    longest_idx = -1
    longest_len = 0
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            content_len = len(msg.get("content", ""))
            if content_len > longest_len:
                longest_len = content_len
                longest_idx = i
    if longest_idx < 0 or longest_len <= _MIN_USER_MESSAGE_CHARS:
        return None
    truncated = copy.deepcopy(messages)
    new_len = max(int(longest_len * _TRUNCATION_FACTOR), _MIN_USER_MESSAGE_CHARS)
    truncated[longest_idx]["content"] = truncated[longest_idx]["content"][:new_len]
    return truncated


def _get_output_token_budget(kwargs: dict, config: LLMConfig) -> int:
    """Read an explicit output budget, accepting either wire-format parameter."""
    if config.output_token_parameter in kwargs:
        return int(kwargs[config.output_token_parameter])
    for parameter in _OUTPUT_TOKEN_PARAMETERS:
        if parameter in kwargs:
            return int(kwargs[parameter])
    return config.max_tokens


def _set_output_token_budget(kwargs: dict, config: LLMConfig, value: int) -> None:
    """Write the configured output budget while removing the alternate parameter."""
    for parameter in _OUTPUT_TOKEN_PARAMETERS:
        kwargs.pop(parameter, None)
    kwargs[config.output_token_parameter] = value


def _apply_budget(kwargs: dict, config: LLMConfig) -> None:
    requested = _get_output_token_budget(kwargs, config)
    if config.max_context > 0:
        messages = kwargs.get("messages", [])
        requested = budget_max_tokens(
            messages,
            config.max_context,
            requested,
        )
    _set_output_token_budget(kwargs, config, requested)


class _IncompleteOutput(Exception):
    """Signals that validation succeeded but output was truncated."""

    def __init__(self, cause):
        self.cause = cause


def _retry_with_validation(do_call, kwargs, config, tracker, original_messages, current_messages, max_retries):
    for val_attempt in range(max_retries + 1):
        try:
            return do_call(kwargs)
        except IncompleteOutputException as e:
            raise _IncompleteOutput(e) from e
        except openai.APIError as e:
            # Endpoints report context overflow as a 400; reduce the output
            # budget and retry. Every other API error propagates untouched.
            new_max = _extract_reduced_max_tokens(e)
            if new_max is None or val_attempt >= max_retries:
                raise
            old_max = _get_output_token_budget(kwargs, config)
            parameter = config.output_token_parameter
            logger.info("Context overflow, reducing %s %d -> %d and retrying", parameter, old_max, new_max)
            if tracker:
                tracker.record_incident(
                    "context_overflow", f"Context overflow, reducing {parameter} {old_max} -> {new_max}"
                )
            kwargs["messages"] = copy.deepcopy(original_messages)
            _set_output_token_budget(kwargs, config, new_max)
            _apply_budget(kwargs, config)
            continue
        except ValidationRetryExhausted as e:
            if val_attempt < max_retries:
                logger.info(
                    "Validation error (attempt %d/%d), retrying with fresh messages + error hint",
                    val_attempt + 1,
                    max_retries,
                )
                retry_messages = copy.deepcopy(current_messages)
                last_attempt = e.failed_attempts[-1] if e.failed_attempts else None
                if last_attempt and last_attempt.completion:
                    failed_content = _extract_response_content(last_attempt.completion)
                    if failed_content:
                        retry_messages.append({"role": "assistant", "content": failed_content})
                error_text = str(last_attempt.exception) if last_attempt else str(e)
                retry_messages.append(
                    {
                        "role": "user",
                        "content": f"Validation error: {error_text}\nCorrect your JSON response, fix the errors.",
                    }
                )
                kwargs["messages"] = retry_messages
                _apply_budget(kwargs, config)
                continue
            if tracker:
                tracker.record_incident("validation_exhausted", f"Validation retries exhausted: {e}")
            raise
    raise RuntimeError("_retry_with_validation exhausted retries without returning a completion")


def _call_with_retry(
    do_call,
    kwargs: dict,
    config: LLMConfig,
    tracker: TokenTracker | None = None,
) -> tuple:
    original_messages = copy.deepcopy(kwargs.get("messages", []))
    current_messages = kwargs.get("messages", [])
    max_validation_retries = kwargs.pop("max_retries", config.max_retries)

    for attempt in range(_MAX_TRUNCATION_RETRIES + 1):
        try:
            return _retry_with_validation(  # type: ignore[no-any-return]
                do_call,
                kwargs,
                config,
                tracker,
                original_messages,
                current_messages,
                max_validation_retries,
            )
        except _IncompleteOutput as e:
            shorter = _truncate_messages(current_messages)
            if shorter is None:
                if tracker:
                    tracker.record_incident(
                        "output_truncated", "Output truncated and prompt cannot be shortened further"
                    )
                raise e.cause
            logger.info(
                "Output truncated (attempt %d/%d), retrying with shorter prompt", attempt + 1, _MAX_TRUNCATION_RETRIES
            )
            if tracker:
                tracker.record_incident(
                    "output_truncated",
                    f"Output truncated (attempt {attempt + 1}/{_MAX_TRUNCATION_RETRIES}), retrying with shorter prompt",
                )
            current_messages = shorter
            kwargs["messages"] = shorter
            _apply_budget(kwargs, config)
    raise RuntimeError("_call_with_retry exhausted truncation retries without returning")


def _track_completion(tracker: TokenTracker, completion) -> None:
    usage = getattr(completion, "usage", None)
    if usage is None or (getattr(usage, "total_tokens", 0) or 0) == 0:
        if not tracker._warned_no_usage:
            logger.warning("LLM backend returned no token usage — cost tracking unavailable")
            tracker._warned_no_usage = True
    tracker.add(usage)


def _extract_json_span(content: str) -> str:
    """Return the last complete JSON object or array in ``content``.

    Models sometimes wrap their output in markdown fences or prepend prose.
    The model's own answer appears last, so the last complete span wins; an
    earlier span quoted from the prompt must not hijack the parse.
    """
    decoder = json.JSONDecoder()
    last_valid: str | None = None
    consumed = 0
    for index, char in enumerate(content):
        if index < consumed or char not in "{[":
            continue
        try:
            _, end = decoder.raw_decode(content, index)
        except json.JSONDecodeError:
            continue
        last_valid = content[index:end]
        consumed = end
    return last_valid if last_valid is not None else content


class _Completions:
    """``chat.completions`` facade over the plain OpenAI SDK."""

    def __init__(self, client: "_StructuredClient"):
        self._client = client

    def create(self, **kwargs: Any):
        """Return the validated response model for a structured completion."""
        result, _ = self._client.create_with_completion(**kwargs)
        return result


class _Chat:
    def __init__(self, client: "_StructuredClient"):
        self.completions = _Completions(client)


class _StructuredClient:
    """Structured-output chat client over a plain ``OpenAI`` instance.

    Call sites pass ``response_model=SomePydanticModel`` and receive the
    validated pydantic object from ``chat.completions.create``. The completion
    is constrained with the native ``json_schema`` ``response_format`` (or a
    ``json_object`` plus schema-in-prompt fallback via
    ``StructuredOutputMode.JSON``) and parsed locally. Parse and validation
    failures retry with error hints until ``max_retries`` is exhausted, then
    raise ``ValidationRetryExhausted``. API and transport errors from the
    OpenAI SDK propagate untouched. Streaming is not supported.
    """

    def __init__(self, openai_client: OpenAI, mode: StructuredOutputMode = StructuredOutputMode.JSON):
        self._openai = openai_client
        self.mode = mode
        self.chat = _Chat(self)

    def create_with_completion(self, **kwargs: Any) -> tuple[Any, Any]:
        """Return ``(validated_model, raw_completion)`` for a structured call.

        Without ``response_model`` the raw completion passes through for both
        elements, mirroring the previous client stack's seam.
        """
        response_model = kwargs.pop("response_model", None)
        # max_retries bounds this loop; the SDK's create() rejects the kwarg.
        max_attempts = max(int(kwargs.pop("max_retries", 0)), 0) + 1
        if response_model is None:
            completion = self._openai.chat.completions.create(**kwargs)
            return completion, completion

        request = dict(kwargs)
        messages = list(request.get("messages", []))
        request["messages"] = messages
        request["response_format"] = self._response_format(response_model, messages)

        failed_attempts: list[FailedAttempt] = []
        for attempt_number in range(1, max_attempts + 1):
            completion = self._openai.chat.completions.create(**request)
            try:
                return _parse_completion(completion, response_model), completion
            except (ValidationError, json.JSONDecodeError, ResponseParsingError) as e:
                failed_attempts.append(FailedAttempt(attempt_number, e, completion))
                if attempt_number >= max_attempts:
                    raise ValidationRetryExhausted(str(e), failed_attempts=failed_attempts) from e
                summary = str(e).splitlines()[0] if str(e) else type(e).__name__
                logger.warning(
                    "Structured output validation failed (attempt %d/%d), retrying with error hint: %s",
                    attempt_number,
                    max_attempts,
                    summary[:200],
                )
                _append_correction_messages(messages, completion, e)
        raise ValidationRetryExhausted("Structured output retries exhausted", failed_attempts=failed_attempts)

    def _response_format(self, response_model: type[BaseModel], messages: list[dict[str, Any]]) -> dict[str, Any]:
        schema = response_model.model_json_schema()
        if self.mode is StructuredOutputMode.JSON_SCHEMA:
            response_format: dict[str, Any] = {
                "type": "json_schema",
                "json_schema": {"name": response_model.__name__, "schema": schema},
            }
            if getattr(response_model, "__structured_strict__", False):
                response_format["json_schema"]["strict"] = True
            return response_format
        if self.mode is StructuredOutputMode.JSON_SCHEMA_WITH_PROMPT:
            _append_schema_block(messages, schema)
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": response_model.__name__, "schema": schema},
            }
            if getattr(response_model, "__structured_strict__", False):
                response_format["json_schema"]["strict"] = True
            return response_format
        # JSON fallback: json_object plus the schema appended to the system prompt.
        schema_text = (
            "Respond with a single JSON object that matches this JSON schema exactly:\n"
            f"{json.dumps(schema, indent=2, ensure_ascii=False)}"
        )
        if messages and messages[0].get("role") == "system":
            messages[0] = {**messages[0], "content": f"{messages[0].get('content', '')}\n\n{schema_text}"}
        else:
            messages.insert(0, {"role": "system", "content": schema_text})
        return {"type": "json_object"}


def _append_schema_block(messages: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    """Append the instructor-worded schema block to the first system message."""
    block = _schema_block(schema)
    if messages and messages[0].get("role") == "system":
        messages[0] = {**messages[0], "content": f"{messages[0].get('content', '')}{block}"}
    else:
        messages.insert(0, {"role": "system", "content": block.strip("\n")})


def _append_correction_messages(messages: list[dict[str, Any]], completion: Any, error: Exception) -> None:
    """Append the failed answer and an error hint so the model can correct itself."""
    failed_content = _extract_response_content(completion)
    if failed_content:
        messages.append({"role": "assistant", "content": failed_content})
    messages.append(
        {"role": "user", "content": f"Validation error: {error}\nCorrect your JSON response, fix the errors."}
    )


def _parse_completion(completion: Any, response_model: type[BaseModel]) -> Any:
    content = _extract_response_content(completion)
    if content is None:
        raise ResponseParsingError("The completion contains no text content.")
    if _finish_reason(completion) == "length":
        raise IncompleteOutputException(last_completion=completion)
    return response_model.model_validate_json(_extract_json_span(content))


def _finish_reason(completion: Any) -> str | None:
    try:
        reason = completion.choices[0].finish_reason
        return reason if isinstance(reason, str) else None  # narrow from Any
    except (AttributeError, IndexError):
        return None


def _wrap_with_tracking(client: _StructuredClient, tracker: TokenTracker, config: LLMConfig) -> None:
    def _do_call(kwargs):
        return client.create_with_completion(**kwargs)

    def tracked_create(**kwargs):
        kwargs.setdefault("temperature", config.temperature)
        if config.service_tier is not None:
            kwargs.setdefault("service_tier", config.service_tier)
        if config.top_p is not None:
            kwargs.setdefault("top_p", config.top_p)
        if config.top_k is not None:
            extra = kwargs.setdefault("extra_body", {})
            extra.setdefault("top_k", config.top_k)
        _apply_budget(kwargs, config)
        tracker._thread_local.current_messages = kwargs.get("messages")
        try:
            result, completion = _call_with_retry(_do_call, kwargs, config, tracker=tracker)
        finally:
            tracker._thread_local.current_messages = None
        _track_completion(tracker, completion)
        return result

    client.chat.completions.create = tracked_create  # type: ignore[method-assign,assignment]
