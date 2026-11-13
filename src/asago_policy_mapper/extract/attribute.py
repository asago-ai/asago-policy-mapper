from __future__ import annotations

import logging
import time

from asago_policy_mapper.extract.models import (
    EvidenceSpan,
    LLMCallRecord,
    RiskMatch,
    ScoredCandidate,
    _CausalChain,
    _CausalChains,
    _RiskEvidenceList,
)
from asago_policy_mapper.llm import _OUTPUT_VALIDATION_ERRORS, ValidationRetryExhausted
from asago_policy_mapper.prompts import render_prompt

logger = logging.getLogger(__name__)


def _verdicts_to_result(
    verdicts,
    batch_ids: set[str],
    document: str,
    chunk_index: int,
    page: int | None,
    section: str | None,
) -> dict[str, tuple[list[EvidenceSpan], str]]:
    """Filter grounded verdicts to their risk ids and quote evidence spans."""
    result: dict[str, tuple[list[EvidenceSpan], str]] = {}
    for v in verdicts:
        if not v.grounded or v.risk_id not in batch_ids:
            continue
        spans = [
            EvidenceSpan(
                text=quote,
                document=document,
                page=page,
                section=section,
                chunk_index=chunk_index,
            )
            for quote in v.quotes
            if quote.strip()
        ]
        if spans:
            result[v.risk_id] = (spans, v.confidence)
    return result


def _record_grounding_call(
    call_collector: list[LLMCallRecord],
    *,
    chunk_index: int,
    risk_ids: list[str],
    messages,
    verdicts,
    duration_ms: float,
    grounded_count: int,
    batch_size: int,
) -> None:
    call_id = f"ground-{len([c for c in call_collector if c.stage == 'grounding']) + 1:03d}"
    call_collector.append(
        LLMCallRecord(
            call_id=call_id,
            stage="grounding",
            chunk_index=chunk_index,
            risk_ids=risk_ids,
            messages=messages,
            response=[v.model_dump() for v in verdicts],
            duration_ms=duration_ms,
            result_summary=f"{grounded_count}/{batch_size} grounded",
        )
    )


def ground_and_extract_evidence(
    chunk_text: str,
    candidates: list[ScoredCandidate],
    client,
    model: str,
    document: str,
    chunk_index: int,
    page: int | None = None,
    section: str | None = None,
    *,
    call_collector: list[LLMCallRecord] | None = None,
    max_batch_size: int = 0,
) -> dict[str, tuple[list[EvidenceSpan], str]]:
    if not candidates:
        return {}

    if max_batch_size > 0 and len(candidates) > max_batch_size:
        batches = [candidates[i : i + max_batch_size] for i in range(0, len(candidates), max_batch_size)]
    else:
        batches = [candidates]

    result: dict[str, tuple[list[EvidenceSpan], str]] = {}

    for batch in batches:
        messages = render_prompt(
            "ground_evidence",
            {
                "chunk_text": chunk_text,
                "risks": [
                    {
                        "risk_id": c.risk_id,
                        "risk_name": c.risk_name,
                        "risk_description": c.risk_description,
                    }
                    for c in batch
                ],
            },
        )

        t0 = time.time()
        verdicts_resp = client.chat.completions.create(
            model=model,
            response_model=_RiskEvidenceList,
            messages=messages,
        )
        verdicts = verdicts_resp.items
        duration_ms = (time.time() - t0) * 1000

        batch_ids = {c.risk_id for c in batch}
        result.update(_verdicts_to_result(verdicts, batch_ids, document, chunk_index, page, section))

        if call_collector is not None:
            _record_grounding_call(
                call_collector,
                chunk_index=chunk_index,
                risk_ids=[c.risk_id for c in batch],
                messages=messages,
                verdicts=verdicts,
                duration_ms=duration_ms,
                grounded_count=sum(v.grounded and v.risk_id in batch_ids for v in verdicts),
                batch_size=len(batch),
            )

    return result


def ground_variants(
    chunk_text: str,
    parent_id: str,
    parent_name: str,
    parent_description: str,
    variants: list[dict],
    client,
    model: str,
    document: str,
    chunk_index: int,
    page: int | None = None,
    section: str | None = None,
    *,
    call_collector: list[LLMCallRecord] | None = None,
) -> dict[str, tuple[list[EvidenceSpan], str]]:
    """Ground individual variants after parent-level grounding confirms relevance."""
    if not variants:
        return {}

    messages = render_prompt(
        "ground_variants",
        {
            "chunk_text": chunk_text,
            "parent_id": parent_id,
            "parent_name": parent_name,
            "parent_description": parent_description,
            "variants": variants,
        },
    )

    t0 = time.time()
    verdicts_resp = client.chat.completions.create(
        model=model,
        response_model=_RiskEvidenceList,
        messages=messages,
    )
    verdicts = verdicts_resp.items
    duration_ms = (time.time() - t0) * 1000

    variant_ids = {v["risk_id"] for v in variants}
    result: dict[str, tuple[list[EvidenceSpan], str]] = {}

    for v in verdicts:
        if not v.grounded or v.risk_id not in variant_ids:
            continue
        spans = [
            EvidenceSpan(
                text=quote,
                document=document,
                page=page,
                section=section,
                chunk_index=chunk_index,
            )
            for quote in v.quotes
            if quote.strip()
        ]
        if spans:
            result[v.risk_id] = (spans, v.confidence)

    if call_collector is not None:
        call_id = f"ground-variant-{len([c for c in call_collector if c.stage == 'variant_grounding']) + 1:03d}"
        call_collector.append(
            LLMCallRecord(
                call_id=call_id,
                stage="variant_grounding",
                chunk_index=chunk_index,
                risk_ids=[v["risk_id"] for v in variants],
                messages=messages,
                response=[v.model_dump() for v in verdicts],
                duration_ms=duration_ms,
                result_summary=(f"{len(result)}/{len(variants)} variants grounded (parent: {parent_id})"),
            )
        )

    return result


def _group_verdicts_to_result(
    verdicts,
    risk_ids: set[str],
    document: str,
    find_chunk_for_quote,
) -> dict[str, tuple[list[EvidenceSpan], str]]:
    """Filter grounded group verdicts, placing each quote in its chunk."""
    result: dict[str, tuple[list[EvidenceSpan], str]] = {}
    for v in verdicts:
        if not v.grounded or v.risk_id not in risk_ids:
            continue
        spans = [
            EvidenceSpan(
                text=quote,
                document=document,
                chunk_index=find_chunk_for_quote(quote),
            )
            for quote in v.quotes
            if quote.strip()
        ]
        if spans:
            result[v.risk_id] = (spans, v.confidence)
    return result


def _record_group_call(
    call_collector: list[LLMCallRecord],
    *,
    chunk_indices: list[int],
    risk_ids: list[str],
    messages,
    verdicts,
    duration_ms: float,
    grounded_count: int,
    risk_count: int,
) -> None:
    call_id = f"ground-expand-{len([c for c in call_collector if 'expand' in c.call_id]) + 1:03d}"
    call_collector.append(
        LLMCallRecord(
            call_id=call_id,
            stage="grounding",
            chunk_index=chunk_indices[0] if chunk_indices else -1,
            risk_ids=risk_ids,
            messages=messages,
            response=[v.model_dump() for v in verdicts],
            duration_ms=duration_ms,
            result_summary=f"{grounded_count}/{risk_count} grounded (expansion)",
        )
    )


def ground_risk_group(
    chunks: list,
    chunk_indices: list[int],
    risks: list[dict],
    client,
    model: str,
    document: str,
    *,
    call_collector: list[LLMCallRecord] | None = None,
) -> dict[str, tuple[list[EvidenceSpan], str]]:
    """Ground a group of related risks against multiple document chunks."""
    if not risks or not chunk_indices:
        return {}

    passages = []
    for idx in chunk_indices:
        if idx < len(chunks):
            passages.append({"index": idx, "text": chunks[idx].text})

    if not passages:
        return {}

    messages = render_prompt(
        "ground_group",
        {
            "passages": passages,
            "risks": risks,
        },
    )

    t0 = time.time()
    verdicts_resp = client.chat.completions.create(
        model=model,
        response_model=_RiskEvidenceList,
        messages=messages,
    )
    verdicts = verdicts_resp.items
    duration_ms = (time.time() - t0) * 1000

    risk_ids = {r["risk_id"] for r in risks}

    passage_texts = {idx: chunks[idx].text for idx in chunk_indices if idx < len(chunks)}

    def _find_chunk_for_quote(quote: str) -> int:
        for idx, text in passage_texts.items():
            if quote in text:
                return idx
        return chunk_indices[0] if chunk_indices else 0

    result = _group_verdicts_to_result(verdicts, risk_ids, document, _find_chunk_for_quote)

    if call_collector is not None:
        _record_group_call(
            call_collector,
            chunk_indices=chunk_indices,
            risk_ids=[r["risk_id"] for r in risks],
            messages=messages,
            verdicts=verdicts,
            duration_ms=duration_ms,
            grounded_count=len(result),
            risk_count=len(risks),
        )

    return result


def _is_output_validation_exhaustion(exc: ValidationRetryExhausted) -> bool:
    """Tell whether the model output, not the endpoint, caused the exhaustion.

    The structured-output client records the failed attempt in
    ``failed_attempts`` and chains its error as ``__cause__``, so a non-empty
    list with a parse/validation cause means the retries ran out on
    unfixable model output. Anything else is not a validation exhaustion.
    """
    return bool(exc.failed_attempts) and isinstance(exc.__cause__, _OUTPUT_VALIDATION_ERRORS)


def _evidence_chunk_texts(risk_match: RiskMatch, chunk_texts: dict[int, str]) -> list[str]:
    """Collect the distinct chunk texts the risk's evidence points at, in order."""
    evidence_chunks = []
    for ev in risk_match.evidence:
        if ev.chunk_index in chunk_texts and chunk_texts[ev.chunk_index] not in evidence_chunks:
            evidence_chunks.append(chunk_texts[ev.chunk_index])
    return evidence_chunks


def _request_causal_chain(
    risk_match: RiskMatch, combined_text: str, client, model: str
) -> tuple[list[dict[str, str]], list, bool, float]:
    """Render the prompt and call the causal-synthesis endpoint.

    Returns (messages, results, retry_exhausted, duration_ms). A validation
    exhaustion caused by unfixable model output downgrades to an empty result
    with retry_exhausted set; anything else propagates.
    """
    messages = render_prompt(
        "causal_synthesis",
        {
            "risk_id": risk_match.risk_id,
            "risk_name": risk_match.risk_name,
            "risk_description": risk_match.risk_description,
            "chunk_texts": combined_text,
        },
    )
    t0 = time.time()
    retry_exhausted = False
    try:
        results_resp = client.chat.completions.create(
            model=model,
            response_model=_CausalChains,
            messages=messages,
        )
        results = results_resp.items
    except ValidationRetryExhausted as exc:
        if not _is_output_validation_exhaustion(exc):
            raise
        logger.warning(
            "Causal synthesis exhausted retries for %s (%s); no causal chain",
            risk_match.risk_id,
            type(exc.__cause__).__name__,
        )
        results = []
        retry_exhausted = True
    duration_ms = (time.time() - t0) * 1000
    return messages, results, retry_exhausted, duration_ms


def synthesize_causal_chain(
    risk_match: RiskMatch,
    chunk_texts: dict[int, str],
    client,
    model: str,
    *,
    call_collector: list[LLMCallRecord] | None = None,
) -> _CausalChain | None:
    evidence_chunks = _evidence_chunk_texts(risk_match, chunk_texts)

    if not evidence_chunks:
        return None

    combined_text = "\n\n---\n\n".join(evidence_chunks)

    messages, results, retry_exhausted, duration_ms = _request_causal_chain(risk_match, combined_text, client, model)

    chain = results[0] if results else None

    if chain and all(
        not v for v in (chain.threat, chain.threat_source, chain.vulnerability, chain.consequence, chain.impact)
    ):
        logger.warning("Causal synthesis returned all-empty fields for %s", risk_match.risk_id)
        chain = None

    if call_collector is not None:
        call_id = f"causal-{len([c for c in call_collector if c.stage == 'causal_synthesis']) + 1:03d}"
        first_chunk = risk_match.evidence[0].chunk_index if risk_match.evidence else -1
        call_collector.append(
            LLMCallRecord(
                call_id=call_id,
                stage="causal_synthesis",
                chunk_index=first_chunk,
                risk_ids=[risk_match.risk_id],
                messages=messages,
                response=chain.model_dump() if chain else {},
                duration_ms=duration_ms,
                result_summary="synthesized" if chain else "retry_exhausted" if retry_exhausted else "empty",
            )
        )

    return chain
