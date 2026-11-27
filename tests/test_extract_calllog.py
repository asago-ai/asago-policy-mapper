"""Tests for pipeline-stage call-record numbering.

Numbering happens in two lock-free steps. A worker numbers the records it
builds against its own records list (each list has one writer, the worker
thread). The coordinator then merges per-task lists into the run's collector
at fan-in, renumbering by the same counting predicate so ids stay unique and
follow task order, not completion order.
"""

import threading
import time

from asago_policy_mapper.extract.attribute import _record_grounding_call
from asago_policy_mapper.extract.calllog import merge_call_records, next_call_number
from asago_policy_mapper.extract.models import LLMCallRecord, _RiskEvidence


def _record(call_id: str, stage: str = "grounding", chunk_index: int = 0) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=call_id,
        stage=stage,  # type: ignore[arg-type]
        chunk_index=chunk_index,
        risk_ids=[],
        messages=[],
        response={},
        duration_ms=0.0,
        result_summary="",
    )


def test_next_call_number_counts_by_predicate():
    """Each site counts only its own stage; other stages leave numbering alone."""
    records = [
        _record("judge-001", stage="judge"),
        _record("ground-001", stage="grounding"),
        _record("ground-variant-001", stage="variant_grounding"),
    ]

    assert next_call_number(records, counts=lambda r: r.stage == "judge") == 2
    assert next_call_number(records, counts=lambda r: r.stage == "grounding") == 2
    assert next_call_number(records, counts=lambda r: r.stage == "variant_grounding") == 2
    assert next_call_number(records, counts=lambda r: "expand" in r.call_id) == 1
    assert next_call_number(records, counts=lambda r: r.stage == "causal_synthesis") == 1


def test_worker_side_numbering_is_sequential():
    """The production grounding site numbers a fresh list sequentially."""
    records: list[LLMCallRecord] = []
    for expected in ("ground-001", "ground-002", "ground-003"):
        _record_grounding_call(
            records,
            chunk_index=0,
            risk_ids=["R-001"],
            messages=[],
            verdicts=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"])],
            duration_ms=0.0,
            grounded_count=1,
            batch_size=1,
        )
        assert records[-1].call_id == expected
    assert [r.call_id for r in records] == ["ground-001", "ground-002", "ground-003"]


def test_record_ids_keep_legacy_counting():
    """An expansion record makes the next grounding id skip a number, as today.

    Exercises the production grounding predicate against the seeded record
    the expansion site builds, so a change to either site's counting
    predicate fails here.
    """
    verdicts = [
        _RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"]),
    ]
    records: list[LLMCallRecord] = [_record("ground-expand-001", stage="grounding")]

    _record_grounding_call(
        records,
        chunk_index=0,
        risk_ids=["R-001"],
        messages=[],
        verdicts=verdicts,
        duration_ms=0.0,
        grounded_count=1,
        batch_size=1,
    )

    assert [r.call_id for r in records] == ["ground-expand-001", "ground-002"]


def test_merge_renumbers_across_task_lists_in_task_order():
    """Two tasks' lists merge into one sequential run, in task order."""
    collector: list[LLMCallRecord] = []
    first = [_record("ground-001")]
    second = [_record("ground-001")]

    merge_call_records(collector, first, counts=lambda r: r.stage == "grounding")
    merge_call_records(collector, second, counts=lambda r: r.stage == "grounding")

    assert [r.call_id for r in collector] == ["ground-001", "ground-002"]


def test_merge_is_deterministic_under_reverse_completion():
    """32 tasks behind a barrier: merged ids follow task order, not completion.

    Each task fills its own list (one record, numbered 001 provisionally);
    later tasks are made to finish first. The merge still numbers by task
    order, which is the strongest uniqueness guarantee available: unique ids
    AND a deterministic order regardless of how the workers interleaved.
    """
    task_count = 32
    task_records: list[list[LLMCallRecord]] = [[] for _ in range(task_count)]
    barrier = threading.Barrier(task_count)

    def worker(index: int) -> None:
        barrier.wait()
        # Later tasks finish first: completion order is reverse task order.
        time.sleep((task_count - index) * 0.001)
        _record_grounding_call(
            task_records[index],
            chunk_index=index,
            risk_ids=["R-001"],
            messages=[],
            verdicts=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"])],
            duration_ms=0.0,
            grounded_count=1,
            batch_size=1,
        )

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(task_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    collector: list[LLMCallRecord] = []
    for records in task_records:
        merge_call_records(collector, records, counts=lambda r: r.stage == "grounding")

    assert len(collector) == task_count
    assert [r.call_id for r in collector] == [f"ground-{n:03d}" for n in range(1, task_count + 1)]
    assert [r.chunk_index for r in collector] == list(range(task_count))


class _ReverseGate:
    """Makes faked workers complete in reverse task order.

    Task k waits for task k+1 to have finished, so the last task finishes
    first; each fake registers its records list under its task index and
    records the completion order for the caller to assert.
    """

    def __init__(self, task_count: int):
        self.done = [threading.Event() for _ in range(task_count)]
        self.completion_order: list[int] = []
        self.task_count = task_count

    def enter(self, index: int) -> None:
        if index + 1 < self.task_count:
            assert self.done[index + 1].wait(timeout=10), f"task {index + 1} never finished"

    def finish(self, index: int) -> None:
        self.completion_order.append(index)
        self.done[index].set()


def test_merge_keeps_unnumbered_records_as_built():
    """Records without a counting predicate (query-gen) keep their call_id."""
    collector: list[LLMCallRecord] = []
    task = [_record("querygen-0", stage="query_gen")]

    merge_call_records(collector, task)

    assert [r.call_id for r in collector] == ["querygen-0"]


def test_merge_continues_numbering_past_the_collector():
    """A merge into a non-empty collector continues its numbering."""
    collector: list[LLMCallRecord] = [
        _record("judge-001", stage="judge"),
        _record("judge-002", stage="judge"),
    ]
    task = [_record("judge-001", stage="judge"), _record("judge-002", stage="judge")]

    merge_call_records(collector, task, counts=lambda r: r.stage == "judge")

    assert [r.call_id for r in collector] == ["judge-001", "judge-002", "judge-003", "judge-004"]


def test_merge_preserves_each_sites_prefix():
    """Expansion records keep their ground-expand prefix through a merge.

    The collector is seeded so the renumber must fire: a seeded expansion
    record bumps the count, forcing the task's records to new numbers while
    keeping the prefix.
    """
    collector: list[LLMCallRecord] = [_record("ground-expand-001")]
    task = [_record("ground-expand-001"), _record("ground-expand-002")]

    merge_call_records(collector, task, counts=lambda r: "expand" in r.call_id)

    assert [r.call_id for r in collector] == ["ground-expand-001", "ground-expand-002", "ground-expand-003"]


# ---------------------------------------------------------------------------
# Coordinator fan-in: task order, not completion order
# ---------------------------------------------------------------------------


def _grounding_chunk_results(count):
    """Build chunk results whose grounding fakes can number by chunk."""
    from asago_policy_mapper.extract.models import ScoredCandidate
    from asago_policy_mapper.extract.retrieve import ChunkResult

    return [
        ChunkResult(
            chunk_index=i,
            source="doc.md",
            page=None,
            section=None,
            accepted=[
                ScoredCandidate(risk_id=f"R-{i:03d}", risk_name="R", risk_description="d", cross_encoder_score=0.9)
            ],
            borderline=[],
            borderline_judged=[],
            stats={"auto_accepted": 1, "candidates_retrieved": 1},
        )
        for i in range(count)
    ]


def _pipeline():
    from asago_policy_mapper.extract import pipeline

    return pipeline


def _run_grounding_with_reverse_completion(monkeypatch, task_count):
    """Run _run_grounding with workers completing in reverse; return (gate, collector)."""
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()
    gate = _ReverseGate(task_count)

    def fake_ground_one(cr, chunks, client, model, records, passes, max_batch_size, context_text):
        index = cr.chunk_index
        gate.enter(index)
        _record_grounding_call(
            records,
            chunk_index=cr.chunk_index,
            risk_ids=[f"R-{cr.chunk_index:03d}"],
            messages=[],
            verdicts=[_RiskEvidence(risk_id=f"R-{cr.chunk_index:03d}", grounded=True, confidence="high", quotes=["t"])],
            duration_ms=0.0,
            grounded_count=1,
            batch_size=1,
        )
        gate.finish(index)
        return cr, {}

    monkeypatch.setattr(pipeline, "_ground_one", fake_ground_one)
    collector: list[LLMCallRecord] = []
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    retrieval = type("R", (), {"use_cross_encoder": True, "no_judge": False})()
    index = type("I", (), {"get_taxonomy": staticmethod(lambda rid: "t")})()
    chunks = [type("C", (), {"source": "doc.md"})() for _ in range(task_count)]

    pipeline._run_grounding(
        _grounding_chunk_results(task_count),
        chunks,
        None,
        config,
        retrieval,
        index,
        collector,
    )
    return gate, collector


def test_run_grounding_numbers_records_in_task_order(monkeypatch):
    """Workers complete in reverse; merged grounding ids follow chunk order."""
    task_count = 8
    gate, collector = _run_grounding_with_reverse_completion(monkeypatch, task_count)

    assert gate.completion_order == list(range(task_count - 1, -1, -1))
    assert [(r.call_id, r.chunk_index) for r in collector] == [
        (f"ground-{n:03d}", n - 1) for n in range(1, task_count + 1)
    ]


def test_run_grounding_without_collector_records_nothing(monkeypatch):
    """A None collector runs the stage and appends nothing."""
    task_count = 2
    pipeline = _pipeline()

    def fake_ground_one(cr, chunks, client, model, records, passes, max_batch_size, context_text):
        _record_grounding_call(
            records,
            chunk_index=cr.chunk_index,
            risk_ids=["R-001"],
            messages=[],
            verdicts=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["t"])],
            duration_ms=0.0,
            grounded_count=1,
            batch_size=1,
        )
        return cr, {}

    monkeypatch.setattr(pipeline, "_ground_one", fake_ground_one)
    from asago_policy_mapper.llm import LLMConfig

    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    retrieval = type("R", (), {"use_cross_encoder": True, "no_judge": False})()
    index = type("I", (), {"get_taxonomy": staticmethod(lambda rid: "t")})()
    chunks = [type("C", (), {"source": "doc.md"})() for _ in range(task_count)]

    matches, filtered, _ = pipeline._run_grounding(
        _grounding_chunk_results(task_count), chunks, None, config, retrieval, index, None
    )

    # The fake grounds nothing, so every candidate lands in filtered.
    assert matches == []
    assert len(filtered) == task_count


def test_run_judge_numbers_records_in_task_order(monkeypatch):
    """Workers complete in reverse; merged judge ids follow chunk order."""
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()
    task_count = 8
    gate = _ReverseGate(task_count)

    def fake_judge_one(i, cr, client, model, records, judge_prompt, max_batch_size, context_text):
        gate.enter(i)
        records.append(_record("judge-001", stage="judge", chunk_index=i))
        gate.finish(i)
        return i, []

    monkeypatch.setattr(pipeline, "_judge_one", fake_judge_one)
    collector: list[LLMCallRecord] = []
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    retrieval = type(
        "R", (), {"no_judge": False, "use_cross_encoder": True, "judge_prompt": "judge_risk", "grounding_batch_size": 0}
    )()
    chunk_results = _grounding_chunk_results(task_count)
    for cr in chunk_results:
        cr.borderline = list(cr.accepted)

    pipeline._run_judge(chunk_results, [], None, config, retrieval, collector)

    assert gate.completion_order == list(range(task_count - 1, -1, -1))
    assert [(r.call_id, r.chunk_index) for r in collector] == [
        (f"judge-{n:03d}", n - 1) for n in range(1, task_count + 1)
    ]


def test_run_judge_without_collector_records_nothing(monkeypatch):
    """A None collector runs the judge stage and appends nothing."""
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()

    def fake_judge_one(i, cr, client, model, records, judge_prompt, max_batch_size, context_text):
        records.append(_record("judge-001", stage="judge"))
        return i, []

    monkeypatch.setattr(pipeline, "_judge_one", fake_judge_one)
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    retrieval = type(
        "R", (), {"no_judge": False, "use_cross_encoder": True, "judge_prompt": "judge_risk", "grounding_batch_size": 0}
    )()
    chunk_results = _grounding_chunk_results(2)
    for cr in chunk_results:
        cr.borderline = list(cr.accepted)

    pipeline._run_judge(chunk_results, [], None, config, retrieval, None)


def test_run_variant_grounding_numbers_records_in_task_order(monkeypatch):
    """Workers complete in reverse; merged variant ids follow parent order."""
    from asago_policy_mapper.extract.models import EvidenceSpan, RetrievalScores, RiskMatch
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()
    task_count = 8
    gate = _ReverseGate(task_count)

    def fake_ground_variants_one(pm, chunks, variant_map, client, model, records, chunk_contexts):
        index = int(pm.risk_id.split("-")[1])
        gate.enter(index)
        records.append(_record("ground-variant-001", stage="variant_grounding", chunk_index=index))
        gate.finish(index)
        return pm, {}

    monkeypatch.setattr(pipeline, "_ground_variants_one", fake_ground_variants_one)
    collector: list[LLMCallRecord] = []

    def make_match(i):
        return RiskMatch(
            risk_id=f"P-{i:03d}",
            risk_name="Parent",
            risk_description="d",
            taxonomy="t",
            confidence=0.9,
            grounding_confidence="high",
            accepted_by="threshold",
            evidence=[EvidenceSpan(text="t", document="doc.md", chunk_index=i)],
            scores=RetrievalScores(bm25_rank=1, embedding_distance=0.1, cross_encoder_score=0.9, rrf_score=0.05),
        )

    matches = [make_match(i) for i in range(task_count)]
    variant_map = {
        f"P-{i:03d}": [{"risk_id": f"V-{i:03d}", "name": "V", "description": "d"}] for i in range(task_count)
    }
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)

    pipeline._run_variant_grounding(matches, [], variant_map, None, config, collector, max_workers=task_count)

    assert gate.completion_order == list(range(task_count - 1, -1, -1))
    assert [(r.call_id, r.chunk_index) for r in collector] == [
        (f"ground-variant-{n:03d}", n - 1) for n in range(1, task_count + 1)
    ]


def test_ground_expansion_groups_numbers_records_in_task_order(monkeypatch):
    """Workers complete in reverse; merged expansion ids follow group order."""
    from types import SimpleNamespace

    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()
    task_count = 8
    gate = _ReverseGate(task_count)

    def fake_ground_expansion_group(group, chunks, documents, client, config, records):
        index = group.chunk_indices[0]
        gate.enter(index)
        records.append(_record("ground-expand-001", chunk_index=index))
        gate.finish(index)
        return {}

    monkeypatch.setattr(pipeline, "_ground_expansion_group", fake_ground_expansion_group)
    collector: list[LLMCallRecord] = []

    groups = [SimpleNamespace(chunk_indices=[i], risk_lookup={f"R-{i:03d}": {}}) for i in range(task_count)]
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    risk_lookup = {}

    matches, grounded = pipeline._ground_expansion_groups(
        groups, [], [], None, None, config, task_count, collector, 1, risk_lookup
    )

    assert gate.completion_order == list(range(task_count - 1, -1, -1))
    assert [(r.call_id, r.chunk_index) for r in collector] == [
        (f"ground-expand-{n:03d}", n - 1) for n in range(1, task_count + 1)
    ]
    assert grounded == 0


def test_ground_expansion_groups_without_collector_records_nothing(monkeypatch):
    """A None collector runs the expansion stage and appends nothing."""
    from types import SimpleNamespace

    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()

    def fake_ground_expansion_group(group, chunks, documents, client, config, records):
        records.append(_record("ground-expand-001"))
        return {}

    monkeypatch.setattr(pipeline, "_ground_expansion_group", fake_ground_expansion_group)
    groups = [SimpleNamespace(chunk_indices=[0], risk_lookup={})]
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)

    pipeline._ground_expansion_groups(groups, [], [], None, None, config, 4, None, 1, {})


def test_run_causal_synthesis_numbers_records_in_task_order(monkeypatch):
    """Workers complete in reverse; merged causal ids follow merged order."""
    from asago_policy_mapper.extract.models import EvidenceSpan, RetrievalScores, RiskMatch
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()
    task_count = 8
    gate = _ReverseGate(task_count)

    def fake_synthesize_causal_chain(*, risk_match, chunk_texts, client, model, records):
        index = int(risk_match.risk_id.split("-")[1])
        gate.enter(index)
        records.append(_record("causal-001", stage="causal_synthesis", chunk_index=index))
        gate.finish(index)
        return None

    monkeypatch.setattr(pipeline, "synthesize_causal_chain", fake_synthesize_causal_chain)
    collector: list[LLMCallRecord] = []

    def make_match(i):
        return RiskMatch(
            risk_id=f"C-{i:03d}",
            risk_name="C",
            risk_description="d",
            taxonomy="t",
            confidence=0.9,
            grounding_confidence="high",
            accepted_by="threshold",
            evidence=[EvidenceSpan(text="t", document="doc.md", chunk_index=0)],
            scores=RetrievalScores(bm25_rank=1, embedding_distance=0.1, cross_encoder_score=0.9, rrf_score=0.05),
        )

    merged = [make_match(i) for i in range(task_count)]
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)

    pipeline._run_causal_synthesis(merged, [], None, config, task_count, collector)

    assert gate.completion_order == list(range(task_count - 1, -1, -1))
    assert [(r.call_id, r.chunk_index) for r in collector] == [
        (f"causal-{n:03d}", n - 1) for n in range(1, task_count + 1)
    ]


def test_run_causal_synthesis_without_collector_records_nothing(monkeypatch):
    """A None collector runs causal synthesis and appends nothing."""
    from asago_policy_mapper.extract.models import EvidenceSpan, RetrievalScores, RiskMatch
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()

    def fake_synthesize_causal_chain(*, risk_match, chunk_texts, client, model, records):
        records.append(_record("causal-001", stage="causal_synthesis"))
        return None

    monkeypatch.setattr(pipeline, "synthesize_causal_chain", fake_synthesize_causal_chain)

    def make_match(i):
        return RiskMatch(
            risk_id=f"C-{i:03d}",
            risk_name="C",
            risk_description="d",
            taxonomy="t",
            confidence=0.9,
            grounding_confidence="high",
            accepted_by="threshold",
            evidence=[EvidenceSpan(text="t", document="doc.md", chunk_index=0)],
            scores=RetrievalScores(bm25_rank=1, embedding_distance=0.1, cross_encoder_score=0.9, rrf_score=0.05),
        )

    merged = [make_match(0)]
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)

    pipeline._run_causal_synthesis(merged, [], None, config, 4, None)


def test_run_query_gen_without_collector_records_nothing(monkeypatch):
    """A None collector runs query generation and appends nothing."""
    from asago_policy_mapper.extract.parse import Chunk
    from asago_policy_mapper.llm import LLMConfig

    pipeline = _pipeline()

    def fake_generate_queries(chunks, groups, client, model, records=None, *, max_workers=32, return_fallbacks=False):
        if records is not None:
            records.append(_record("querygen-0", stage="query_gen"))
        return ([], []) if return_fallbacks else []

    monkeypatch.setattr(pipeline, "generate_queries", fake_generate_queries)
    chunks = [Chunk(text="text", source="doc.md", index=0, section=None)]
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    timing: dict[str, float] = {}

    query_results, fallback = pipeline._run_query_gen(chunks, None, config, None, 4, timing)

    assert query_results == []
    assert fallback == set()
