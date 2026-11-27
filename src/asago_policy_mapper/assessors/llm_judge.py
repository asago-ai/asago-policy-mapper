"""The chat judge as an ``Assessor``, keeping the historical chat behaviour.

Renders the ``<prompt_name>`` prompt for the batch, makes exactly the
``client.chat.completions.create(model=..., response_model=_JudgeVerdicts,
messages=...)`` call the judge has always made, and maps each verdict to
``BooleanAnswer(relevant, justification)``. Duplicate verdicts for one id
stay as duplicate answers; the rule reduces them. The exchange payload
carries the verdicts dumped to plain JSON-able dicts at this boundary.
Transport and API exceptions propagate untouched.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from asago_policy_mapper.extract.models import _JudgeVerdicts
from asago_policy_mapper.extract.screening import Answer, AnswerBatch, BooleanAnswer, DecisionCase, Question
from asago_policy_mapper.llm import _shortenings_of
from asago_policy_mapper.prompts import render_prompt


class LlmJudgeAssessor:
    """The borderline-judge assessor over the structured chat client.

    ``assess`` routes its call through the client's ``for_stage``
    stage view, so the client must be the tracked client
    ``llm.create_client`` returns (``_StructuredClient``); a bare
    ``OpenAI`` client constructs (its host is readable for
    ``sends_offsite``) but fails at assess time, which names the
    missing ``for_stage`` attribute.
    """

    answer_types: frozenset[type] = frozenset({BooleanAnswer})

    def __init__(self, client, model: str, prompt_name: str):
        self.client = client
        self.model = model
        self.prompt_name = prompt_name
        self.assessor_id = f"llm-judge:{model}:{prompt_name}"
        self.sends_offsite = _offsite_base_url(_client_host(client))

    def assess(self, question: Question, context: str, cases: Sequence[DecisionCase]) -> AnswerBatch:
        """Answer ``question`` for ``cases`` against the ``context`` passage."""
        messages = render_prompt(
            self.prompt_name,
            {
                "chunk_text": context,
                "risks": [
                    {"risk_id": c.risk_id, "risk_name": c.name, "risk_description": c.description} for c in cases
                ],
            },
        )

        t0 = time.time()
        stage_client = self.client.for_stage("judge")
        verdicts_resp = stage_client.chat.completions.create(
            model=self.model,
            response_model=_JudgeVerdicts,
            messages=messages,
        )
        duration_ms = (time.time() - t0) * 1000
        return _batch_from_verdicts(verdicts_resp.items, cases, messages, duration_ms, _shortenings_of(verdicts_resp))


def _client_host(client) -> str | None:
    """Read the API host off a chat client, when it exposes one.

    This is host reading only, at construction time. The production
    stack wraps the ``OpenAI`` client inside ``_StructuredClient``
    (field ``_openai``), which has no ``base_url`` of its own; a bare
    ``OpenAI`` client carries ``base_url`` at the top level. Both paths
    are checked, so the host read works over either — but only the
    tracked client from ``create_client`` (``_StructuredClient``)
    exposes the ``for_stage`` view ``assess`` calls, so constructing
    over a bare client works while assessing over one raises.
    """
    for holder in (getattr(client, "_openai", None), client):
        base_url = getattr(holder, "base_url", None)
        host = getattr(base_url, "host", None)
        if host is not None:
            return str(host)
    return None


def _offsite_base_url(host: str | None) -> bool:
    """Tell whether an API host points off this machine.

    Missing host information counts as offsite (fail closed); localhost,
    the loopback address and the IPv6 loopback count as local.
    """
    if host is None:
        return True
    return host not in {"localhost", "127.0.0.1", "::1"}


def _batch_from_verdicts(
    verdicts,
    cases: Sequence[DecisionCase],
    messages: list[dict[str, str]],
    duration_ms: float,
    prompt_shortenings: list[dict] | None = None,
) -> AnswerBatch:
    """Collect raw answers from judge verdicts, keeping duplicates raw.

    Verdict ids outside the batch land in ``unmatched_ids`` and nowhere
    else, mirroring today's judge, which ignores them. The exchange
    payload carries the verdicts as plain dicts, dumped here at the
    assessor boundary: the assessor knows its response shape, so it
    serializes it, and no consumer of the batch needs model knowledge.
    The prompt shortenings the call made ride the same payload, so the
    record site reads them from the batch instead of a side channel.
    """
    answers: dict[str, tuple[Answer, ...]] = {}
    case_ids = {c.risk_id for c in cases}
    unmatched_ids: list[str] = []
    for v in verdicts:
        if v.risk_id in case_ids:
            entry = answers.get(v.risk_id, ())
            answers[v.risk_id] = entry + (BooleanAnswer(v.relevant, v.justification),)
        else:
            unmatched_ids.append(v.risk_id)

    exchange = {
        "messages": messages,
        "response": [v.model_dump() for v in verdicts],
        "prompt_shortenings": list(prompt_shortenings or []),
    }
    return AnswerBatch(
        answers=answers,
        unmatched_ids=tuple(unmatched_ids),
        latency_ms=duration_ms,
        exchange=exchange,
    )
