"""The decision seam: a versioned question, an assessor, and rules.

The borderline judge and the pre-grounding filter both put a question
about each candidate risk to a decision model and reduce the answers to a
keep-or-drop decision. A ``Question`` states the question put to an
assessor. An ``Assessor`` (see ``assessors/``) answers it for a batch of
``DecisionCase`` objects, returning raw answers per risk id. A rule
reduces those answers to ``Decision`` objects: ``Keep`` keeps a case when
any answer is a yes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class Question:
    """The question an assessor answers, with an id and version for logging."""

    question_id: str
    version: str
    criterion: str


RELEVANCE_QUESTION_V1 = Question(
    question_id="risk-relevance",
    version="1",
    criterion=(
        "A risk is relevant to a policy passage when the passage directly names "
        "the risk or its specific technical concept, describes its mitigation, "
        "management or oversight, or establishes a governance framework that "
        "inherently covers it."
    ),
)
"""The borderline-judge question, mirroring templates/prompts/judge_risk_system.j2.

The template counts three routes to relevance: direct mention of the risk or
its technical concept, description of its mitigation/oversight, and
governance that only implies coverage of the risk. ``version`` stays at "1"
while those semantics hold; a template that changes them bumps the version.
"""


@dataclass(frozen=True)
class DecisionCase:
    """One risk put to an assessor, decoupled from the retrieval candidate.

    ``is_variant_parent`` is set exactly when the risk id names a collapsed
    variant parent (an id containing ``---``), so assessors can treat
    synthetic parent entries differently from real risks.
    """

    risk_id: str
    name: str
    description: str
    is_variant_parent: bool = False


@dataclass(frozen=True)
class BooleanAnswer:
    """A yes/no answer with an optional rationale (the judge justification)."""

    holds: bool
    rationale: str | None = None


@dataclass(frozen=True)
class ProbabilityAnswer:
    """A probability answer for the yes/no question."""

    probability: float


@dataclass(frozen=True)
class NoAnswer:
    """The assessor could not answer; ``detail`` says why."""

    reason: Literal["missing", "invalid", "timeout", "error"]
    detail: str = ""


Answer = BooleanAnswer | ProbabilityAnswer | NoAnswer
"""One raw answer for one risk id, before a rule reduces it."""


@dataclass(frozen=True)
class AnswerBatch:
    """An assessor's raw answers for one batch of ``DecisionCase`` objects.

    ``answers`` stays raw: an absent key or an empty tuple means the
    assessor omitted the risk, and more than one entry means duplicate
    answers (the rule reduces them). ``unmatched_ids`` carries returned ids
    that were not in the batch, which the pipeline ignores. ``latency_ms``
    measures the invocation, never multiplied per candidate. ``exchange``
    holds the raw requests and responses the assessor sent and received
    (``{"messages", "response"}`` for the chat judge).

    The batch is a single-owner value. It is frozen, but ``answers`` and
    ``exchange`` are plain dict fields, so the freeze is shallow: the
    assessor redacts everything it must redact while building them (at
    its boundary, where it knows its credential), and every consumer
    after construction treats both fields as read-only. Consumers that
    record the same payload twice build their own copies; the frozen
    dataclass gives per-assessment identity, not nested immutability.

    ``exchange`` carries plain JSON-able data, not model objects: an
    assessor that talks to a structured client serializes its responses
    at its own boundary, where it knows the response shape, so no
    consumer of the batch needs that model knowledge. The judge's
    ``response`` entries are plain dicts, matching the call record's
    ``response`` field (``list[dict]``); keys beyond
    ``messages``/``response`` are assessor-specific (the HTTP probability
    assessor records ``requests``/``responses``).
    """

    answers: dict[str, tuple[Answer, ...]]
    unmatched_ids: tuple[str, ...]
    latency_ms: float
    exchange: dict | None


class Assessor(Protocol):
    """An assessor that answers a ``Question`` for a batch of cases.

    ``answer_types`` declares the answer types the assessor can produce, so
    a rule can reject an assessor whose answers it cannot reduce.
    ``sends_offsite`` states whether answers leave the machine, for runs
    that must stay local. ``prompt_name`` names the prompt the answers came
    from, so the decision log can tell prompt variants apart. An assessor
    serializes its raw responses to plain data itself, so its batch's
    ``exchange`` never carries model objects.
    """

    assessor_id: str
    answer_types: frozenset[type]
    sends_offsite: bool
    prompt_name: str

    def assess(self, question: Question, context: str, cases: Sequence[DecisionCase]) -> AnswerBatch: ...


class Rule(Protocol):
    """A rule that reduces a batch of answers to decisions.

    ``rule_id`` versions the reduction, so a decision log names the exact
    rule semantics that produced each decision.
    """

    rule_id: str

    def decide(self, cases: Sequence[DecisionCase], batch: AnswerBatch) -> list[Decision]: ...


@dataclass(frozen=True)
class Decision:
    """The keep or drop verdict for one risk id, with the rule's reason."""

    risk_id: str
    keep: bool
    reason: str


class Keep:
    """Keep/drop rule "keep/1": keep when any answer is a yes.

    A case is kept when any of its answers is a ``BooleanAnswer`` that
    holds, regardless of what the other answers are. An empty answer tuple
    (the assessor omitted the risk) drops with reason "missing". Otherwise
    the drop reason names the first answer: "no" for a ``BooleanAnswer``
    that does not hold, "no_answer:<reason>" for a ``NoAnswer``,
    "probability:<p>" for a ``ProbabilityAnswer``.
    """

    rule_id = "keep/1"

    def decide(self, cases: Sequence[DecisionCase], batch: AnswerBatch) -> list[Decision]:
        decisions: list[Decision] = []
        for case in cases:
            decisions.append(self._decide_case(case, batch.answers.get(case.risk_id, ())))
        return decisions

    def _decide_case(self, case: DecisionCase, answers: tuple[Answer, ...]) -> Decision:
        if any(isinstance(a, BooleanAnswer) and a.holds for a in answers):
            return Decision(case.risk_id, True, "yes")
        if not answers:
            return Decision(case.risk_id, False, "missing")
        return Decision(case.risk_id, False, self._drop_reason(answers[0]))

    @staticmethod
    def _drop_reason(answer: Answer) -> str:
        if isinstance(answer, BooleanAnswer):
            return "no"
        if isinstance(answer, NoAnswer):
            return f"no_answer:{answer.reason}"
        return f"probability:{answer.probability!r}"


def answer_payloads(answers: Sequence[Answer]) -> list[dict]:
    """Serialize answers for a ``DecisionItem``, keeping duplicates raw.

    Each answer carries an explicit stable ``kind`` ("boolean",
    "probability" or "no_answer"), so the output JSON does not depend on
    the Python class names.
    """
    return [{"kind": _answer_kind(a), **_answer_fields(a)} for a in answers]


def _answer_kind(answer: Answer) -> str:
    if isinstance(answer, BooleanAnswer):
        return "boolean"
    if isinstance(answer, ProbabilityAnswer):
        return "probability"
    return "no_answer"


def _answer_fields(answer: Answer) -> dict:
    if isinstance(answer, BooleanAnswer):
        return {"holds": answer.holds, "rationale": answer.rationale}
    if isinstance(answer, ProbabilityAnswer):
        return {"probability": answer.probability}
    return {"reason": answer.reason, "detail": answer.detail}
