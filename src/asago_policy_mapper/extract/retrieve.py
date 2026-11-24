from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from dataclasses import dataclass

import spacy

from asago_policy_mapper.assessors.llm_judge import LlmJudgeAssessor
from asago_policy_mapper.extract.calllog import next_call_number
from asago_policy_mapper.extract.models import DecisionItem, DecisionLog, LLMCallRecord, ScoredCandidate
from asago_policy_mapper.extract.parse import Chunk
from asago_policy_mapper.extract.screening import (
    RELEVANCE_QUESTION_V1,
    AnswerBatch,
    Assessor,
    Decision,
    DecisionCase,
    Keep,
    Question,
    Rule,
    answer_payloads,
)

logger = logging.getLogger(__name__)


def _counts_judge(record: LLMCallRecord) -> bool:
    """The ``judge-NNN`` predicate."""
    return record.stage == "judge"


_nlp = spacy.blank("en")
_nlp.add_pipe("sentencizer")


def _sent_tokenize(text: str) -> list[str]:
    if not text.strip():
        return []
    return [sent.text for sent in _nlp(text).sents]


def _try_expand_side(
    neighbor: Chunk,
    chunk_source: str,
    budget: int,
) -> tuple[bool, int]:
    """Tell whether one neighbor chunk fits the context budget.

    Returns (admitted, token_cost); a neighbor from another source or one
    that overflows the budget is not admitted (cost 0).
    """
    if neighbor.source != chunk_source:
        return False, 0
    t = len(neighbor.text.split())
    if t > budget:
        return False, 0
    return True, t


def _expand_neighbor_indices(
    chunks: list[Chunk],
    i: int,
    budget: int,
) -> tuple[list[int], list[int], int]:
    """Collect same-source neighbor indices around chunk i within the budget.

    Expands symmetrically (alternating before/after) until the token budget is
    spent or both sides hit a boundary (document edge, source change, or an
    over-budget neighbor). Returns (before_indices, after_indices, remaining
    budget); indices are ordered outward from i.
    """
    chunk = chunks[i]
    before_indices: list[int] = []
    after_indices: list[int] = []
    before_idx = i - 1
    after_idx = i + 1
    expand_before = True

    while budget > 0 and (before_idx >= 0 or after_idx < len(chunks)):
        if expand_before and before_idx >= 0:
            admitted, cost = _try_expand_side(chunks[before_idx], chunk.source, budget)
            if admitted:
                before_indices.insert(0, before_idx)
                budget -= cost
                before_idx -= 1
            else:
                before_idx = -1
        elif not expand_before and after_idx < len(chunks):
            admitted, cost = _try_expand_side(chunks[after_idx], chunk.source, budget)
            if admitted:
                after_indices.append(after_idx)
                budget -= cost
                after_idx += 1
            else:
                after_idx = len(chunks)
        expand_before = not expand_before

    return before_indices, after_indices, budget


def _join_context(chunks: list[Chunk], ordered: list[int]) -> str:
    """Join the chunk texts in order, inserting section headings at transitions."""
    parts: list[str] = []
    for pos, idx in enumerate(ordered):
        c = chunks[idx]
        if pos > 0:
            prev_c = chunks[ordered[pos - 1]]
            if c.section and c.section != prev_c.section:
                parts.append(f"## {c.section}")
        parts.append(c.text)
    return "\n\n".join(parts)


def build_chunk_contexts(
    chunks: list[Chunk],
    max_context_tokens: int = 1024,
) -> list[str]:
    """Build enriched context text for each chunk by expanding to neighbors.

    Expands symmetrically (alternating before/after) with adjacent chunks
    from the same source document until the token budget is reached. Inserts
    section headings at section transitions between included chunks.

    Returns a list parallel to chunks — one context string per chunk.
    """
    contexts: list[str] = []
    for i, chunk in enumerate(chunks):
        core_tokens = len(chunk.text.split())
        budget = max_context_tokens - core_tokens

        before_indices, after_indices, _ = _expand_neighbor_indices(chunks, i, budget)
        ordered = before_indices + [i] + after_indices
        contexts.append(_join_context(chunks, ordered))

    return contexts


def build_padded_text(
    chunks: list[Chunk],
    chunk_index: int,
    context_sentences: int = 2,
    max_context_tokens: int = 0,
) -> str:
    """Build padded text from a chunk and its neighbors.

    Deprecated: use build_chunk_contexts() instead for consistent context
    across judge and grounding stages.
    """
    if max_context_tokens > 0:
        contexts = build_chunk_contexts(chunks, max_context_tokens)
        return contexts[chunk_index]

    chunk = chunks[chunk_index]
    source = chunk.source
    parts = []

    if chunk_index > 0:
        prev = chunks[chunk_index - 1]
        if prev.source == source:
            prev_sents = _sent_tokenize(prev.text)
            parts.extend(prev_sents[-context_sentences:])

    parts.append(chunk.text)

    if chunk_index < len(chunks) - 1:
        nxt = chunks[chunk_index + 1]
        if nxt.source == source:
            next_sents = _sent_tokenize(nxt.text)
            parts.extend(next_sents[:context_sentences])

    return " ".join(parts)


def classify_by_threshold(
    candidates: list[ScoredCandidate],
    *,
    threshold_high: float,
    threshold_low: float = 0.15,
    bm25_rescue_rank: int = 0,
) -> tuple[list[ScoredCandidate], list[ScoredCandidate], list[ScoredCandidate]]:
    accepted = []
    borderline = []
    discarded = []
    for c in candidates:
        if c.cross_encoder_score >= threshold_high:
            accepted.append(c)
        elif c.cross_encoder_score >= threshold_low:
            borderline.append(c)
        elif bm25_rescue_rank > 0 and c.bm25_rank > 0 and c.bm25_rank <= bm25_rescue_rank:
            borderline.append(c)
        else:
            discarded.append(c)
    return accepted, borderline, discarded


def classify_by_rank(
    candidates: list[ScoredCandidate],
    *,
    top_n_accept: int = 5,
    top_n_judge: int = 5,
    min_score_floor: float = 0.0,
    bm25_rescue_rank: int = 0,
) -> tuple[list[ScoredCandidate], list[ScoredCandidate], list[ScoredCandidate]]:
    ranked = sorted(candidates, key=lambda c: c.cross_encoder_score, reverse=True)
    accepted = []
    borderline = []
    discarded = []
    for i, c in enumerate(ranked):
        if min_score_floor > 0 and c.cross_encoder_score < min_score_floor:
            if bm25_rescue_rank > 0 and c.bm25_rank > 0 and c.bm25_rank <= bm25_rescue_rank:
                borderline.append(c)
            else:
                discarded.append(c)
        elif i < top_n_accept:
            accepted.append(c)
        elif i < top_n_accept + top_n_judge:
            borderline.append(c)
        elif bm25_rescue_rank > 0 and c.bm25_rank > 0 and c.bm25_rank <= bm25_rescue_rank:
            borderline.append(c)
        else:
            discarded.append(c)
    return accepted, borderline, discarded


def classify_candidates(
    candidates: list[ScoredCandidate],
    *,
    top_n_accept: int = 5,
    top_n_judge: int = 5,
    min_score_floor: float = 0.0,
    bm25_rescue_rank: int = 0,
    threshold_high: float | None = None,
    threshold_low: float | None = None,
) -> tuple[list[ScoredCandidate], list[ScoredCandidate], list[ScoredCandidate]]:
    if threshold_high is not None:
        return classify_by_threshold(
            candidates,
            threshold_high=threshold_high,
            threshold_low=threshold_low if threshold_low is not None else 0.15,
            bm25_rescue_rank=bm25_rescue_rank,
        )
    return classify_by_rank(
        candidates,
        top_n_accept=top_n_accept,
        top_n_judge=top_n_judge,
        min_score_floor=min_score_floor,
        bm25_rescue_rank=bm25_rescue_rank,
    )


def _dump_entry(entry: object) -> object:
    """Return ``entry`` as plain data, if it is not already.

    ``AnswerBatch.exchange`` response entries are plain dicts, matching
    the call record's ``list[dict]`` response field: assessors serialize
    their responses at their own boundary. An assessor that still hands
    back an object with a ``model_dump`` records too; it is dumped here,
    so both shapes record.
    """
    dump = getattr(entry, "model_dump", None)
    if dump is None:
        return entry
    return dump()


def _record_judge_call(
    records: list[LLMCallRecord],
    *,
    chunk_index: int,
    risk_ids: list[str],
    messages,
    verdicts,
    duration_ms: float,
    batch_accepted: int,
    batch_size: int,
    prompt_shortenings: list[dict],
    decision_log: DecisionLog | None = None,
) -> None:
    number = next_call_number(records, counts=_counts_judge)
    records.append(
        LLMCallRecord(
            call_id=f"judge-{number:03d}",
            stage="judge",
            chunk_index=chunk_index,
            risk_ids=risk_ids,
            messages=messages,
            response=[_dump_entry(v) for v in verdicts],
            duration_ms=duration_ms,
            result_summary=f"{batch_accepted}/{batch_size} accepted",
            prompt_shortenings=prompt_shortenings,
            decision=decision_log,
        ),
    )


def _judge_batch(
    batch: list[ScoredCandidate],
    chunk_text: str,
    client,
    model: str,
    prompt_name: str,
) -> tuple[list[ScoredCandidate], list, list, float, list[dict], DecisionLog]:
    """Judge one batch through the assessor/rule seam.

    Returns (accepted candidates, messages, verdicts, duration_ms,
    shortenings, decision_log). The messages and verdicts come from the
    assessor's exchange payload, so the judge call record stays identical
    to the pre-seam one apart from the decision log; the shortenings ride
    the same payload, so a shortening made inside the assessor's call
    reaches the record the way the pre-seam judge's did.
    """
    cases = [DecisionCase(risk_id=c.risk_id, name=c.risk_name, description=c.risk_description) for c in batch]
    assessor = LlmJudgeAssessor(client, model, prompt_name)
    answers = assessor.assess(RELEVANCE_QUESTION_V1, chunk_text, cases)

    rule = Keep()
    decisions = rule.decide(cases, answers)
    kept_ids = {d.risk_id for d in decisions if d.keep}
    accepted = [c for c in batch if c.risk_id in kept_ids]

    # The chat judge always reports its exchange payload; its response
    # entries are plain dicts, dumped at the assessor boundary.
    exchange = answers.exchange or {}
    messages = exchange.get("messages", [])
    verdicts = list(exchange.get("response", []))
    shortenings = list(exchange.get("prompt_shortenings", []))

    decision_log = build_decision_log(answers, decisions, assessor, rule, messages)
    return accepted, messages, verdicts, answers.latency_ms, shortenings, decision_log


def build_decision_log(
    answers: AnswerBatch,
    decisions: Sequence[Decision],
    assessor: Assessor,
    rule: Rule,
    messages: list,
    question: Question | None = None,
) -> DecisionLog:
    """Assemble the seam's decision log for one assessed batch.

    ``question`` is the question the answers answer; it defaults to the
    judge's relevance question, so callers with their own question pass it
    rather than rebuilding this loop.
    """
    if question is None:
        question = RELEVANCE_QUESTION_V1
    items = [
        DecisionItem(
            risk_id=d.risk_id,
            answers=answer_payloads(answers.answers.get(d.risk_id, ())),
            keep=d.keep,
            reason=d.reason,
        )
        for d in decisions
    ]
    system = next((m["content"] for m in messages if m.get("role") == "system"), "")
    return DecisionLog(
        question_id=question.question_id,
        question_version=question.version,
        prompt_name=assessor.prompt_name,
        prompt_sha256=hashlib.sha256(system.encode()).hexdigest(),
        assessor_id=assessor.assessor_id,
        rule_id=rule.rule_id,
        latency_ms=answers.latency_ms,
        items=items,
        unmatched_ids=list(answers.unmatched_ids),
    )


def judge_borderline(
    candidates: list[ScoredCandidate],
    chunk_text: str,
    client,
    model: str,
    *,
    records: list[LLMCallRecord] | None = None,
    chunk_index: int = 0,
    prompt_name: str = "judge_risk",
    max_batch_size: int = 0,
) -> list[ScoredCandidate]:
    if not candidates:
        return []

    if max_batch_size > 0 and len(candidates) > max_batch_size:
        batches = [candidates[i : i + max_batch_size] for i in range(0, len(candidates), max_batch_size)]
    else:
        batches = [candidates]

    result: list[ScoredCandidate] = []

    for batch in batches:
        accepted, messages, verdicts, duration_ms, shortenings, decision_log = _judge_batch(
            batch, chunk_text, client, model, prompt_name
        )
        result.extend(accepted)

        if records is not None:
            _record_judge_call(
                records,
                chunk_index=chunk_index,
                risk_ids=[c.risk_id for c in batch],
                messages=messages,
                verdicts=verdicts,
                duration_ms=duration_ms,
                batch_accepted=len(accepted),
                batch_size=len(batch),
                prompt_shortenings=shortenings,
                decision_log=decision_log,
            )

    return result


@dataclass
class ChunkResult:
    chunk_index: int
    source: str
    page: int | None
    section: str | None
    accepted: list[ScoredCandidate]
    borderline: list[ScoredCandidate]
    borderline_judged: list[ScoredCandidate]
    stats: dict


def retrieve_chunk(
    chunks: list[Chunk],
    chunk_index: int,
    index,
    *,
    top_k: int = 50,
    top_n_accept: int = 5,
    top_n_judge: int = 5,
    min_score_floor: float = 0.0,
    context_sentences: int = 2,
    bm25_rescue_rank: int = 0,
    use_cross_encoder: bool = True,
    rrf_min_score: float = 0.0,
    threshold_high: float | None = None,
    threshold_low: float | None = None,
) -> ChunkResult:
    chunk = chunks[chunk_index]
    padded = build_padded_text(chunks, chunk_index, context_sentences)
    candidates = index.hybrid_search(
        padded,
        top_k=top_k,
        bm25_rescue_rank=bm25_rescue_rank,
        rrf_min_score=rrf_min_score,
    )

    if not use_cross_encoder:
        return ChunkResult(
            chunk_index=chunk_index,
            source=chunk.source,
            page=chunk.page,
            section=chunk.section,
            accepted=candidates,
            borderline=[],
            borderline_judged=[],
            stats={
                "candidates_retrieved": len(candidates),
                "auto_accepted": len(candidates),
                "borderline": 0,
                "discarded": 0,
                "bm25_rescued": 0,
            },
        )

    accepted, borderline, discarded = classify_candidates(
        candidates,
        top_n_accept=top_n_accept,
        top_n_judge=top_n_judge,
        min_score_floor=min_score_floor,
        bm25_rescue_rank=bm25_rescue_rank,
        threshold_high=threshold_high,
        threshold_low=threshold_low,
    )
    floor = threshold_low if threshold_low is not None else min_score_floor
    bm25_rescued = sum(
        1 for c in borderline if c.cross_encoder_score < floor and c.bm25_rank > 0 and c.bm25_rank <= bm25_rescue_rank
    )
    return ChunkResult(
        chunk_index=chunk_index,
        source=chunk.source,
        page=chunk.page,
        section=chunk.section,
        accepted=accepted,
        borderline=borderline,
        borderline_judged=[],
        stats={
            "candidates_retrieved": len(candidates),
            "auto_accepted": len(accepted),
            "borderline": len(borderline),
            "discarded": len(discarded),
            "bm25_rescued": bm25_rescued,
        },
    )
