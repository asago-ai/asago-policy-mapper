"""Characterization tests for the borderline judge.

The first six tests pin ``judge_borderline``'s behaviour across the
judge-seam refactor and must stay unedited afterwards: the seam keeps
every quirk they pin (candidate order, batch splitting, duplicate risk
ids, out-of-batch verdict ids ignored, one LLM call per batch, the judge
call record's shape and exchange messages).

They stub the LLM client at the ``chat.completions.create`` seam with
``MagicMock``, so no network or model is involved.
"""

import hashlib
import subprocess
import sys
from unittest.mock import MagicMock, patch

import httpx

from asago_policy_mapper.assessors.llm_judge import LlmJudgeAssessor
from asago_policy_mapper.extract.models import LLMCallRecord, ScoredCandidate, _JudgeVerdict, _JudgeVerdicts
from asago_policy_mapper.extract.retrieve import judge_borderline
from asago_policy_mapper.extract.screening import (
    RELEVANCE_QUESTION_V1,
    AnswerBatch,
    BooleanAnswer,
    Decision,
    DecisionCase,
    Keep,
    NoAnswer,
    ProbabilityAnswer,
    Question,
    answer_payloads,
)


def _candidates(*risk_ids: str) -> list[ScoredCandidate]:
    return [
        ScoredCandidate(
            risk_id=risk_id,
            risk_name=f"Risk {risk_id}",
            risk_description=f"Description for {risk_id}.",
            cross_encoder_score=0.5,
        )
        for risk_id in risk_ids
    ]


def _case(risk_id: str) -> DecisionCase:
    return DecisionCase(risk_id=risk_id, name=f"Risk {risk_id}", description=f"Description for {risk_id}.")


def _verdicts(*entries: tuple[str, bool]) -> _JudgeVerdicts:
    items = [
        _JudgeVerdict(risk_id=risk_id, relevant=relevant, justification="stubbed") for risk_id, relevant in entries
    ]
    return _JudgeVerdicts(items=items)


def _client(returning: _JudgeVerdicts) -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.return_value = returning
    client.for_stage = lambda stage: client
    return client


def test_judge_keeps_relevant_drops_irrelevant():
    """A verdict of relevant=True keeps the candidate; relevant=False drops it."""
    client = _client(_verdicts(("R-001", True), ("R-002", False)))
    candidates = _candidates("R-001", "R-002")

    accepted = judge_borderline(candidates, "Chunk text.", client, "test-model")

    assert [c.risk_id for c in accepted] == ["R-001"]


def test_judge_omitted_verdict_is_rejected():
    """A candidate with no verdict in the response is dropped, not kept."""
    client = _client(_verdicts(("R-001", True)))
    candidates = _candidates("R-001", "R-002")

    accepted = judge_borderline(candidates, "Chunk text.", client, "test-model")

    assert [c.risk_id for c in accepted] == ["R-001"]


def test_judge_duplicate_any_yes_wins():
    """Duplicate verdicts for one id: any relevant=True keeps the candidate.

    Both verdict orders must survive, so neither a first-wins nor a
    last-wins reduction passes.
    """
    for entries in (
        (("R-001", False), ("R-001", True)),
        (("R-001", True), ("R-001", False)),
    ):
        client = _client(_verdicts(*entries))
        accepted = judge_borderline(_candidates("R-001"), "Chunk text.", client, "test-model")
        assert [c.risk_id for c in accepted] == ["R-001"]
        client.chat.completions.create.assert_called_once()

    # Duplicate candidates sharing one risk id both survive, in input order,
    # and both stay in the record's risk_ids.
    client = _client(_verdicts(("R-001", True)))
    collector: list[LLMCallRecord] = []
    accepted = judge_borderline(
        _candidates("R-001", "R-001"),
        "Chunk text.",
        client,
        "test-model",
        records=collector,
    )
    assert [c.risk_id for c in accepted] == ["R-001", "R-001"]
    assert collector[0].risk_ids == ["R-001", "R-001"]


def test_judge_ignores_out_of_batch_ids():
    """A verdict id from another batch keeps nothing, in either batch.

    Batch 1's response carries a positive verdict for batch 2's id; that
    must not promote the batch-2 candidate, whose own verdict is negative.
    """
    client = MagicMock()
    client.for_stage = lambda stage: client
    client.chat.completions.create.side_effect = [
        _verdicts(("R-002", True), ("R-001", False)),
        _verdicts(("R-002", False)),
    ]

    accepted = judge_borderline(
        _candidates("R-001", "R-002"),
        "Chunk text.",
        client,
        "test-model",
        max_batch_size=1,
    )

    assert accepted == []
    assert client.chat.completions.create.call_count == 2


def test_judge_batches_at_max_batch_size():
    """31 candidates at batch size 15 make 3 calls, order preserved across batches."""
    n = 31
    risk_ids = [f"R-{i:03d}" for i in range(n)]
    candidates = _candidates(*risk_ids)

    responses = [_verdicts(*((rid, True) for rid in ids)) for ids in (risk_ids[0:15], risk_ids[15:30], risk_ids[30:31])]
    client = MagicMock()
    client.for_stage = lambda stage: client
    client.chat.completions.create.side_effect = responses

    accepted = judge_borderline(candidates, "Chunk text.", client, "test-model", max_batch_size=15)

    assert client.chat.completions.create.call_count == 3
    assert [c.risk_id for c in accepted] == risk_ids

    # Each call saw exactly its own batch's candidates, in order, in the prompt.
    calls = client.chat.completions.create.call_args_list
    for call, ids in zip(calls, (risk_ids[0:15], risk_ids[15:30], risk_ids[30:31])):
        user_message = call.kwargs["messages"][1]["content"]
        rendered_ids = [line.split("**")[1] for line in user_message.splitlines() if line.startswith("- **")]
        assert rendered_ids == ids

        # Today's wire shape: the structured response model and model name.
        assert call.kwargs["response_model"] is _JudgeVerdicts
        assert call.kwargs["model"] == "test-model"


def test_judge_record_shape():
    """The judge record carries today's LLMCallRecord fields and wire messages."""
    client = _client(_verdicts(("R-001", True)))
    collector: list[LLMCallRecord] = []

    judge_borderline(
        _candidates("R-001", "R-002"),
        "Chunk text.",
        client,
        "test-model",
        records=collector,
        chunk_index=7,
    )

    assert len(collector) == 1
    record = collector[0]
    assert isinstance(record, LLMCallRecord)
    assert record.call_id == "judge-001"
    assert record.stage == "judge"
    assert record.chunk_index == 7
    assert record.risk_ids == ["R-001", "R-002"]
    assert record.messages == client.chat.completions.create.call_args.kwargs["messages"]
    assert record.messages[0]["role"] == "system"
    assert "Chunk text." in record.messages[1]["content"]
    assert "R-001" in record.messages[1]["content"]
    assert "R-002" in record.messages[1]["content"]
    assert record.response == [{"risk_id": "R-001", "relevant": True, "justification": "stubbed"}]
    assert record.duration_ms >= 0
    assert record.result_summary == "1/2 accepted"


# --- tests for the judge seam (assessor + rule) ---


def test_judge_latency_covers_only_the_call():
    """latency_ms converts the wall time around the create call to milliseconds.

    A fake clock pins the arithmetic: a 0.25s call reports 250ms, so a
    unit confusion or a sign flip fails here.
    """
    client = _client(_verdicts(("R-001", True)))
    assessor = LlmJudgeAssessor(client, "test-model", "judge_risk")
    clock = iter([100.0, 100.25])

    with patch("asago_policy_mapper.assessors.llm_judge.time.time", side_effect=lambda: next(clock)):
        batch = assessor.assess(RELEVANCE_QUESTION_V1, "Chunk text.", [_case("R-001")])

    assert batch.latency_ms == 250.0


def test_judge_assessor_never_emits_probability():
    """The judge assessor emits only boolean answers, never a probability."""
    client = _client(_verdicts(("R-001", True), ("R-001", False), ("R-009", True)))
    assessor = LlmJudgeAssessor(client, "test-model", "judge_risk")
    cases = [_case("R-001"), _case("R-002")]

    batch = assessor.assess(RELEVANCE_QUESTION_V1, "Chunk text.", cases)

    assert assessor.answer_types == frozenset({BooleanAnswer})
    all_answers = [a for answers in batch.answers.values() for a in answers]
    assert all_answers
    assert all(isinstance(a, BooleanAnswer) for a in all_answers)
    assert not any(isinstance(a, (ProbabilityAnswer, NoAnswer)) for a in all_answers)
    # Duplicates stay raw; unmatched ids land in unmatched_ids only.
    assert batch.answers["R-001"] == (BooleanAnswer(True, "stubbed"), BooleanAnswer(False, "stubbed"))
    assert "R-002" not in batch.answers
    assert batch.unmatched_ids == ("R-009",)

    # The rendered prompt carries each case's name and description, and the
    # exchange payload is the messages that travelled plus the verdicts,
    # dumped to plain dicts at the assessor boundary.
    user_message = batch.exchange["messages"][1]["content"]
    assert "Risk R-001" in user_message
    assert "Description for R-001." in user_message
    assert batch.exchange["messages"][0]["role"] == "system"
    assert batch.latency_ms >= 0
    assert batch.exchange["response"] == [v.model_dump() for v in client.chat.completions.create.return_value.items]
    assert all(isinstance(entry, dict) for entry in batch.exchange["response"])


def test_judge_batch_passes_question_and_cases_to_the_assessor():
    """_judge_batch wires the real question, cases and exchange through the seam.

    Runs judge_borderline with a stubbed LlmJudgeAssessor.assess recording
    its inputs, so dropping a candidate field or the question from the
    wiring fails here.
    """
    from asago_policy_mapper.extract import retrieve

    seen: dict = {}

    def fake_assess(assessor_self, question, context, cases):
        seen["question"] = question
        seen["context"] = context
        seen["cases"] = list(cases)
        return AnswerBatch(
            answers={"R-001": (BooleanAnswer(True, "via stub"),)},
            unmatched_ids=(),
            latency_ms=5.0,
            exchange={
                "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
                "response": [],
            },
        )

    with patch.object(retrieve.LlmJudgeAssessor, "assess", autospec=True, side_effect=fake_assess):
        collector: list[LLMCallRecord] = []
        accepted = retrieve.judge_borderline(
            _candidates("R-001", "R-002"),
            "Chunk text.",
            MagicMock(),
            "test-model",
            records=collector,
        )

    assert seen["question"] is RELEVANCE_QUESTION_V1
    assert seen["context"] == "Chunk text."
    assert [(c.risk_id, c.name, c.description) for c in seen["cases"]] == [
        ("R-001", "Risk R-001", "Description for R-001."),
        ("R-002", "Risk R-002", "Description for R-002."),
    ]
    # The record carries the exchange messages and the decision log built
    # from the stub's answers.
    assert [c.risk_id for c in accepted] == ["R-001"]
    assert collector[0].messages == [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    assert collector[0].response == []
    log = collector[0].decision
    assert log is not None
    assert log.items[0].answers == [{"kind": "boolean", "holds": True, "rationale": "via stub"}]
    assert log.items[1].answers == []


def test_judge_batch_tolerates_exchange_free_assessor():
    """A batch with no exchange payload still reduces and records empty messages.

    Assessors that run in process report exchange=None; the seam must not
    require chat exchange fields.
    """
    from asago_policy_mapper.extract import retrieve

    def fake_assess(assessor_self, question, context, cases):
        return AnswerBatch(
            answers={"R-002": (BooleanAnswer(True, "exchange-free"),)},
            unmatched_ids=("R-009",),
            latency_ms=2.0,
            exchange=None,
        )

    with patch.object(retrieve.LlmJudgeAssessor, "assess", autospec=True, side_effect=fake_assess):
        collector: list[LLMCallRecord] = []
        accepted = retrieve.judge_borderline(
            _candidates("R-001", "R-002"),
            "Chunk text.",
            MagicMock(),
            "test-model",
            records=collector,
        )

    assert [c.risk_id for c in accepted] == ["R-002"]
    record = collector[0]
    assert record.messages == []
    assert record.response == []
    log = record.decision
    assert log is not None
    assert log.unmatched_ids == ["R-009"]
    assert log.items[1].answers == [{"kind": "boolean", "holds": True, "rationale": "exchange-free"}]


def test_keep_rule_reasons():
    """Keep reduces raw answers with the reasons the rule names.

    A kept case's reason is the bare word "yes": the rationale is already
    in the answers, so the reason does not repeat it.
    """
    rule = Keep()
    cases = [
        _case("R-001"),
        _case("R-002"),
        _case("R-003"),
        _case("R-004"),
        _case("R-005"),
        _case("R-006"),
        _case("R-007"),
        _case("R-008"),
        _case("R-009"),
        _case("R-010"),
    ]

    batch = AnswerBatch(
        answers={
            "R-001": (BooleanAnswer(True, "direct mention"),),
            "R-002": (BooleanAnswer(False, "too broad"),),
            "R-003": (BooleanAnswer(False, "first"), BooleanAnswer(True, "second")),
            "R-004": (),
            "R-005": (NoAnswer(reason="timeout", detail="504"),),
            "R-006": (ProbabilityAnswer(probability=0.3),),
            "R-007": (NoAnswer(reason="timeout"), BooleanAnswer(True, "after")),
            "R-008": (BooleanAnswer(True, "before"), NoAnswer(reason="timeout")),
            "R-009": (BooleanAnswer(True, None),),
            "R-010": (BooleanAnswer(False, None),),
        },
        unmatched_ids=("R-009",),
        latency_ms=1.0,
        exchange=None,
    )

    decisions = rule.decide(cases, batch)

    assert [(d.risk_id, d.keep) for d in decisions] == [
        ("R-001", True),
        ("R-002", False),
        ("R-003", True),
        ("R-004", False),
        ("R-005", False),
        ("R-006", False),
        ("R-007", True),
        ("R-008", True),
        ("R-009", True),
        ("R-010", False),
    ]
    assert decisions[0].reason == "yes"
    assert decisions[1].reason == "no"
    assert decisions[2].reason == "yes"
    assert decisions[3].reason == "missing"
    assert decisions[4].reason == "no_answer:timeout"
    assert decisions[5].reason == "probability:0.3"
    # A yes wins over a no-answer in the same case, in either order.
    assert decisions[6].reason == "yes"
    assert decisions[7].reason == "yes"
    # A rationale-less verdict keeps the bare reason word.
    assert decisions[8].reason == "yes"
    assert decisions[9].reason == "no"
    # A case the assessor never mentioned at all is also a "missing" drop.
    assert rule.decide([_case("R-011")], batch)[0].reason == "missing"
    # A near-threshold probability keeps its full repr, not a rounded form.
    near = rule._decide_case(_case("R-012"), (ProbabilityAnswer(probability=0.10000001),))
    assert near.reason == "probability:0.10000001"


def test_judge_assessor_offsite_follows_client_host():
    """sends_offsite derives from the client's base_url host, failing closed."""
    from openai import OpenAI

    local = LlmJudgeAssessor(OpenAI(base_url="http://localhost:11434/v1", api_key="x"), "m", "judge_risk")
    remote = LlmJudgeAssessor(OpenAI(base_url="https://api.example.com/v1", api_key="x"), "m", "judge_risk")
    mocked = LlmJudgeAssessor(MagicMock(), "m", "judge_risk")

    assert local.sends_offsite is False
    assert remote.sends_offsite is True
    # A client that exposes no base_url (test doubles) fails closed.
    assert mocked.sends_offsite is True
    assert local.assessor_id == "llm-judge:m:judge_risk"


def test_client_host_reads_the_wrapped_openai_client():
    """The production stack exposes the host only via the _openai indirection.

    _StructuredClient has no base_url of its own; it holds the OpenAI
    client in ``_openai``. A client shaped like that must yield its host,
    in both directions.
    """
    from asago_policy_mapper.assessors.llm_judge import _client_host

    class WrappedClient:
        def __init__(self, url: str):
            self._openai = OpenAIStub(url)

    class OpenAIStub:
        def __init__(self, url: str):
            self.base_url = httpx.URL(url)

    assert _client_host(WrappedClient("http://localhost:11434/v1")) == "localhost"
    assert _client_host(WrappedClient("https://api.example.com/v1")) == "api.example.com"
    local = LlmJudgeAssessor(WrappedClient("http://localhost:11434/v1"), "m", "judge_risk")
    remote = LlmJudgeAssessor(WrappedClient("https://api.example.com/v1"), "m", "judge_risk")
    assert local.sends_offsite is False
    assert remote.sends_offsite is True


def test_offsite_base_url_fails_closed_on_missing_host():
    """A host of None counts as offsite, and loopback variants count as local."""
    from asago_policy_mapper.assessors.llm_judge import _offsite_base_url

    # Fail closed: no host information means offsite.
    assert _offsite_base_url(None) is True
    # Every loopback spelling counts as local.
    assert _offsite_base_url("localhost") is False
    assert _offsite_base_url("127.0.0.1") is False
    assert _offsite_base_url("::1") is False
    assert _offsite_base_url("api.example.com") is True


def test_decision_log_on_judge_record():
    """The judge record stores the seam's decision log.

    The log identifies the question, prompt (hashed system template),
    assessor and rule, and carries one item per case, in batch order, with
    the raw answers, the keep flag and the rule's reason. Out-of-batch
    verdict ids land in unmatched_ids.
    """
    from asago_policy_mapper.prompts import render_prompt

    client = _client(_verdicts(("R-001", False), ("R-002", True), ("R-002", True), ("R-009", True)))
    collector: list[LLMCallRecord] = []

    judge_borderline(
        _candidates("R-001", "R-002"),
        "Chunk text.",
        client,
        "test-model",
        records=collector,
    )

    record = collector[0]
    log = record.decision
    assert log is not None
    assert log.question_id == "risk-relevance"
    assert log.question_version == "1"
    assert log.prompt_name == "judge_risk"
    system = render_prompt("judge_risk", {"chunk_text": "", "risks": []})[0]["content"]
    assert log.prompt_sha256 == hashlib.sha256(system.encode("utf-8")).hexdigest()
    assert log.assessor_id == "llm-judge:test-model:judge_risk"
    assert log.rule_id == "keep/1"
    assert log.unmatched_ids == ["R-009"]
    assert log.latency_ms >= 0

    # One item per case, in batch order; duplicates stay raw in answers.
    assert [item.risk_id for item in log.items] == ["R-001", "R-002"]
    r1, r2 = log.items
    assert r1.keep is False
    assert r1.reason == "no"
    assert r1.answers == [{"kind": "boolean", "holds": False, "rationale": "stubbed"}]
    assert r2.keep is True
    assert r2.reason == "yes"
    assert r2.answers == [
        {"kind": "boolean", "holds": True, "rationale": "stubbed"},
        {"kind": "boolean", "holds": True, "rationale": "stubbed"},
    ]

    # The log serializes into the record's JSON shape.
    dumped = record.model_dump()["decision"]
    assert dumped["items"][0]["risk_id"] == "R-001"


def test_decision_log_hashes_empty_when_no_system_template():
    """A messages list with no system message hashes the empty string.

    Every judge prompt ships a system template, so this pins the fallback
    for prompt sets without one.
    """
    from asago_policy_mapper.extract.retrieve import build_decision_log

    answers = AnswerBatch(
        answers={"R-001": (BooleanAnswer(True, "n"),)},
        unmatched_ids=(),
        latency_ms=1.0,
        exchange=None,
    )
    decisions = [Decision(risk_id="R-001", keep=True, reason="yes")]
    assessor = LlmJudgeAssessor(MagicMock(), "m", "judge_risk")

    log = build_decision_log(answers, decisions, assessor, Keep(), [{"role": "user", "content": "u"}])

    assert log.prompt_sha256 == hashlib.sha256(b"").hexdigest()


def test_decision_log_prompt_hash_tells_templates_apart():
    """An alternate judge prompt template hashes to a different prompt_sha256."""
    from asago_policy_mapper.prompts import render_prompt

    client = _client(_verdicts(("R-001", True)))
    collector: list[LLMCallRecord] = []

    judge_borderline(
        _candidates("R-001"),
        "Chunk text.",
        client,
        "test-model",
        records=collector,
        prompt_name="judge_risk_gepa",
    )

    log = collector[0].decision
    assert log is not None
    assert log.prompt_name == "judge_risk_gepa"
    assert log.assessor_id == "llm-judge:test-model:judge_risk_gepa"
    gepa_system = render_prompt("judge_risk_gepa", {"chunk_text": "", "risks": []})[0]["content"]
    risk_system = render_prompt("judge_risk", {"chunk_text": "", "risks": []})[0]["content"]
    assert log.prompt_sha256 == hashlib.sha256(gepa_system.encode("utf-8")).hexdigest()
    assert log.prompt_sha256 != hashlib.sha256(risk_system.encode("utf-8")).hexdigest()


def test_answer_payloads_pin_stable_serialized_kinds():
    """Each answer type serializes under an explicit, stable kind string.

    The kinds are part of the output JSON, so they must not drift with
    Python class names: "boolean" (holds/rationale), "probability"
    (probability), "no_answer" (reason/detail).
    """
    answers: tuple = (
        BooleanAnswer(True, "note"),
        ProbabilityAnswer(probability=0.25),
        NoAnswer(reason="timeout", detail="504"),
        BooleanAnswer(False, None),
    )

    assert answer_payloads(answers) == [
        {"kind": "boolean", "holds": True, "rationale": "note"},
        {"kind": "probability", "probability": 0.25},
        {"kind": "no_answer", "reason": "timeout", "detail": "504"},
        {"kind": "boolean", "holds": False, "rationale": None},
    ]


def test_judge_exchange_response_entries_are_plain_data():
    """The judge assessor dumps its verdicts to plain dicts at its boundary.

    ``AnswerBatch.exchange`` entries are JSON-able data, not model
    objects, so the record path never needs the response model. A verdict
    object appearing in the exchange would break every consumer that
    conforms to the documented contract without model knowledge.
    """
    client = _client(_verdicts(("R-001", True)))
    assessor = LlmJudgeAssessor(client, "test-model", "judge_risk")

    batch = assessor.assess(RELEVANCE_QUESTION_V1, "Chunk text.", [_case("R-001")])

    response = batch.exchange["response"]
    assert all(isinstance(entry, dict) for entry in response)
    assert response == [{"risk_id": "R-001", "relevant": True, "justification": "stubbed"}]


def test_judge_records_plain_dict_assessor_responses():
    """A conforming assessor returning plain dicts records without crashing.

    The judge record path must tolerate plain-dict exchange entries: the
    contract the ``AnswerBatch`` docstring states is JSON-able data, so a
    protocol-conforming assessor with no model objects cannot crash the
    record. A legacy entry carrying ``model_dump`` still records.
    """
    from asago_policy_mapper.extract import retrieve

    plain_verdict = {"risk_id": "R-001", "relevant": True, "justification": "via plain dict"}

    def fake_assess(assessor_self, question, context, cases):
        return AnswerBatch(
            answers={"R-001": (BooleanAnswer(True, "plain"),)},
            unmatched_ids=(),
            latency_ms=1.0,
            exchange={
                "messages": [{"role": "system", "content": "s"}],
                "response": [plain_verdict],
            },
        )

    with patch.object(retrieve.LlmJudgeAssessor, "assess", autospec=True, side_effect=fake_assess):
        collector: list[LLMCallRecord] = []
        accepted = retrieve.judge_borderline(
            _candidates("R-001"),
            "Chunk text.",
            MagicMock(),
            "test-model",
            records=collector,
        )

    assert [c.risk_id for c in accepted] == ["R-001"]
    assert collector[0].response == [plain_verdict]

    # A legacy entry that still carries model_dump records through the
    # same path, dumped rather than passed through.
    class _LegacyVerdict:
        def model_dump(self) -> dict:
            return {"risk_id": "R-002", "relevant": False, "justification": "legacy"}

    def legacy_assess(assessor_self, question, context, cases):
        return AnswerBatch(
            answers={"R-002": (BooleanAnswer(True, "legacy"),)},
            unmatched_ids=(),
            latency_ms=1.0,
            exchange={"messages": [], "response": [_LegacyVerdict()]},
        )

    with patch.object(retrieve.LlmJudgeAssessor, "assess", autospec=True, side_effect=legacy_assess):
        collector = []
        retrieve.judge_borderline(_candidates("R-002"), "Chunk text.", MagicMock(), "test-model", records=collector)

    assert collector[0].response == [{"risk_id": "R-002", "relevant": False, "justification": "legacy"}]


def test_assessors_import_without_extract_pipeline():
    """Importing an assessor module first does not fail on a fresh start.

    The ``extract`` package init is lazy (PEP 562) because assessors
    import ``extract.screening`` and an eager ``pipeline`` import there
    would be circular. This test fails the day someone adds an eager
    ``extract.pipeline``/``extract.retrieve`` import to
    ``extract/__init__.py``: importing an assessor would then try to
    import ``extract.retrieve``, which imports the assessor back while it
    is still initializing.
    """
    script = "import asago_policy_mapper.assessors.llm_judge; import asago_policy_mapper.extract"
    run = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, f"assessor-first import failed:\n{run.stderr}"


def test_build_decision_log_takes_the_question():
    """build_decision_log records the question it is given, not the judge's.

    The default stays the judge's relevance question, but a caller with
    its own question (the prefilter's) passes it instead of rebuilding
    this loop.
    """
    from asago_policy_mapper.extract.retrieve import build_decision_log

    answers = AnswerBatch(
        answers={"R-001": (BooleanAnswer(True, "n"),)},
        unmatched_ids=(),
        latency_ms=1.0,
        exchange=None,
    )
    decisions = [Decision(risk_id="R-001", keep=True, reason="yes")]
    assessor = LlmJudgeAssessor(MagicMock(), "m", "prefilter-prompt")

    other = Question(question_id="grounding-likelihood", version="1", criterion="any criterion")
    log = build_decision_log(answers, decisions, assessor, Keep(), [{"role": "user", "content": "u"}], question=other)

    assert log.question_id == "grounding-likelihood"
    assert log.question_version == "1"

    default_log = build_decision_log(answers, decisions, assessor, Keep(), [{"role": "user", "content": "u"}])
    assert default_log.question_id == RELEVANCE_QUESTION_V1.question_id
