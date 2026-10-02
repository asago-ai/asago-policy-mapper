"""Bounded checks for the API and inference backend of an LLM server."""

import instructor
from openai import APIConnectionError, OpenAI

from asago_policy_mapper.llm import SlimModel

PROBE_TIMEOUT_SECONDS = 60.0


class LLMHealthError(RuntimeError):
    """The server cannot supply the configured model or a structured completion."""


class LLMUnavailableError(LLMHealthError):
    """The API does not respond to the model request."""


class ProbeAnswer(SlimModel):
    answer: str


def probe_llm(base_url: str, model: str) -> None:
    """Make sure that the model API and structured inference both work."""
    with OpenAI(base_url=base_url, api_key="none", timeout=PROBE_TIMEOUT_SECONDS, max_retries=0) as probe:
        try:
            available = probe.models.list()
        except APIConnectionError as exc:
            raise LLMUnavailableError(f"LLM server not available at {base_url}: {exc}") from exc
        except Exception as exc:
            raise LLMHealthError(f"LLM model probe failed at {base_url}: {exc}") from exc

        available_ids = {m.id for m in available.data}
        if model not in available_ids:
            raise LLMHealthError(f"Model {model!r} not available on {base_url} (available: {sorted(available_ids)})")

        client = instructor.from_openai(probe, mode=instructor.Mode.JSON_SCHEMA)
        try:
            result = client.chat.completions.create(
                model=model,
                response_model=ProbeAnswer,
                messages=[{"role": "user", "content": "Reply with a short answer to say that you are ready."}],
                max_tokens=128,
                temperature=0.0,
                max_retries=0,
            )
            if not result.answer.strip():
                raise ValueError("The completion contains no answer.")
        except Exception as exc:
            raise LLMHealthError(f"LLM inference probe failed for {model!r} at {base_url}: {exc}") from exc
