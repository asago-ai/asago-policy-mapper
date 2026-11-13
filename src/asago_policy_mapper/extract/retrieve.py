from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import spacy

from asago_policy_mapper.extract.models import LLMCallRecord, ScoredCandidate, _JudgeVerdicts
from asago_policy_mapper.extract.parse import Chunk
from asago_policy_mapper.prompts import render_prompt

logger = logging.getLogger(__name__)

_nlp = spacy.blank("en")
_nlp.add_pipe("sentencizer")


def _sent_tokenize(text: str) -> list[str]:
    if not text.strip():
        return []
    return [sent.text for sent in _nlp(text).sents]


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
            prev = chunks[before_idx]
            if prev.source != chunk.source:
                before_idx = -1
            else:
                t = len(prev.text.split())
                if t <= budget:
                    before_indices.insert(0, before_idx)
                    budget -= t
                    before_idx -= 1
                else:
                    before_idx = -1
        elif not expand_before and after_idx < len(chunks):
            nxt = chunks[after_idx]
            if nxt.source != chunk.source:
                after_idx = len(chunks)
            else:
                t = len(nxt.text.split())
                if t <= budget:
                    after_indices.append(after_idx)
                    budget -= t
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


def _record_judge_call(
    call_collector: list[LLMCallRecord],
    *,
    chunk_index: int,
    risk_ids: list[str],
    messages,
    verdicts,
    duration_ms: float,
    batch_accepted: int,
    batch_size: int,
) -> None:
    call_id = f"judge-{len([c for c in call_collector if c.stage == 'judge']) + 1:03d}"
    call_collector.append(
        LLMCallRecord(
            call_id=call_id,
            stage="judge",
            chunk_index=chunk_index,
            risk_ids=risk_ids,
            messages=messages,
            response=[v.model_dump() for v in verdicts],
            duration_ms=duration_ms,
            result_summary=f"{batch_accepted}/{batch_size} accepted",
        )
    )


def _judge_batch(
    batch: list[ScoredCandidate],
    chunk_text: str,
    client,
    model: str,
    prompt_name: str,
) -> tuple[list[ScoredCandidate], list, list, float]:
    """Judge one batch; return (accepted candidates, messages, verdicts, duration_ms)."""
    messages = render_prompt(
        prompt_name,
        {
            "chunk_text": chunk_text,
            "risks": [
                {"risk_id": c.risk_id, "risk_name": c.risk_name, "risk_description": c.risk_description} for c in batch
            ],
        },
    )

    t0 = time.time()
    verdicts_resp = client.chat.completions.create(
        model=model,
        response_model=_JudgeVerdicts,
        messages=messages,
    )
    verdicts = verdicts_resp.items
    duration_ms = (time.time() - t0) * 1000

    batch_ids = {c.risk_id for c in batch}
    accepted_ids = {v.risk_id for v in verdicts if v.relevant and v.risk_id in batch_ids}
    accepted = [c for c in batch if c.risk_id in accepted_ids]
    return accepted, messages, verdicts, duration_ms


def judge_borderline(
    candidates: list[ScoredCandidate],
    chunk_text: str,
    client,
    model: str,
    *,
    call_collector: list[LLMCallRecord] | None = None,
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
        accepted, messages, verdicts, duration_ms = _judge_batch(batch, chunk_text, client, model, prompt_name)
        result.extend(accepted)

        if call_collector is not None:
            _record_judge_call(
                call_collector,
                chunk_index=chunk_index,
                risk_ids=[c.risk_id for c in batch],
                messages=messages,
                verdicts=verdicts,
                duration_ms=duration_ms,
                batch_accepted=len(accepted),
                batch_size=len(batch),
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
