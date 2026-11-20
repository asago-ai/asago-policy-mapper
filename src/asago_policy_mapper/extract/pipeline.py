from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from asago_policy_mapper.extract.attribute import (
    ground_and_extract_evidence,
    ground_risk_group,
    ground_variants,
    synthesize_causal_chain,
)
from asago_policy_mapper.extract.index import RiskIndex
from asago_policy_mapper.extract.merge import merge_matches
from asago_policy_mapper.extract.models import (
    ChunkSummary,
    EvidenceSpan,
    ExtractionResult,
    FilteredCandidate,
    LLMCallRecord,
    RetrievalConfig,
    RetrievalScores,
    RetrievalStats,
    RiskMatch,
    ScoredCandidate,
    _CausalChain,
)
from asago_policy_mapper.extract.parse import chunk_documents, parse_document
from asago_policy_mapper.extract.querygen import generate_queries, group_chunks
from asago_policy_mapper.extract.retrieve import (
    ChunkResult,
    build_chunk_contexts,
    judge_borderline,
    retrieve_chunk,
)
from asago_policy_mapper.llm import LLMConfig

logger = logging.getLogger(__name__)

_QUERY_GEN_MAX_CANDIDATES = 50


def _cap_accepted_candidates(chunk_results: list[ChunkResult], limit: int) -> None:
    """Keep the highest-RRF candidates when query-gen unions exceed the per-chunk cap."""
    for cr in chunk_results:
        if cr is None or len(cr.accepted) <= limit:
            continue
        cr.accepted = sorted(cr.accepted, key=lambda c: c.rrf_score, reverse=True)[:limit]
        cr.stats["auto_accepted"] = len(cr.accepted)
        cr.stats["candidates_retrieved"] = max(cr.stats.get("candidates_retrieved", 0), len(cr.accepted))


@contextmanager
def timed(timing, key):
    t0 = time.time()
    try:
        yield
    finally:
        timing[key] = (time.time() - t0) * 1000


_AGENTIC_PHRASES = {
    "agentic",
    "ai agent",
    "ai agents",
    "autonomous agent",
    "autonomous agents",
    "agent framework",
    "tool-calling",
    "tool calling",
    "function calling",
    "agentic ai",
    "agentic system",
    "agentic systems",
    "multi-agent",
    "multiagent",
}


def _document_discusses_agents(texts: list[str]) -> bool:
    combined = " ".join(texts).lower()
    return any(phrase in combined for phrase in _AGENTIC_PHRASES)


def _judge_one(
    i,
    cr,
    client,
    model,
    call_collector,
    judge_prompt="judge_risk",
    max_batch_size=0,
    context_text="",
):
    judged = judge_borderline(
        cr.borderline,
        context_text,
        client,
        model,
        call_collector=call_collector,
        chunk_index=i,
        prompt_name=judge_prompt,
        max_batch_size=max_batch_size,
    )
    return i, judged


def _ground_one(
    cr,
    chunks,
    client,
    model,
    call_collector,
    passes=1,
    max_batch_size=0,
    context_text="",
):
    chunk = chunks[cr.chunk_index]
    text = context_text if context_text else chunk.text
    merged: dict[str, tuple[list, str]] = {}
    for pass_num in range(1, passes + 1):
        grounded = ground_and_extract_evidence(
            chunk_text=text,
            candidates=cr.accepted,
            client=client,
            model=model,
            document=chunk.source,
            chunk_index=cr.chunk_index,
            page=chunk.page,
            section=chunk.section,
            call_collector=call_collector,
            max_batch_size=max_batch_size,
        )
        logger.info(
            "Grounding chunk %d/%d pass %d/%d: %d risks grounded",
            cr.chunk_index + 1,
            len(chunks),
            pass_num,
            passes,
            len(grounded),
        )
        for rid, val in grounded.items():
            if rid not in merged:
                merged[rid] = val
    return cr, merged


def determine_accepted_by(candidate, *, borderline_judged, use_cross_encoder, no_judge):
    if candidate in borderline_judged:
        return "auto_promoted" if no_judge else "llm_judge"
    return "threshold" if use_cross_encoder else "rrf"


def build_risk_match(
    candidate,
    *,
    taxonomy,
    accepted_by,
    grounding_confidence,
    evidence,
    use_cross_encoder=True,
    confidence_override=None,
    scores_override=None,
):
    confidence = (
        confidence_override
        if confidence_override is not None
        else (candidate.cross_encoder_score if use_cross_encoder else candidate.rrf_score)
    )
    scores = scores_override or RetrievalScores(
        bm25_rank=candidate.bm25_rank,
        embedding_distance=candidate.embedding_distance,
        cross_encoder_score=candidate.cross_encoder_score,
        rrf_score=candidate.rrf_score,
    )
    return RiskMatch(
        risk_id=candidate.risk_id,
        risk_name=candidate.risk_name,
        risk_description=candidate.risk_description,
        taxonomy=taxonomy,
        confidence=confidence,
        grounding_confidence=grounding_confidence,
        accepted_by=accepted_by,
        evidence=list(evidence),
        scores=scores,
    )


def _collect_ungrounded(chunk_results, index, retrieval):
    matches = []
    for cr in chunk_results:
        for candidate in cr.accepted:
            accepted_by = determine_accepted_by(
                candidate,
                borderline_judged=cr.borderline_judged,
                use_cross_encoder=retrieval.use_cross_encoder,
                no_judge=retrieval.no_judge,
            )
            matches.append(
                build_risk_match(
                    candidate,
                    taxonomy=index.get_taxonomy(candidate.risk_id),
                    accepted_by=accepted_by,
                    grounding_confidence="ungrounded",
                    evidence=[],
                    use_cross_encoder=retrieval.use_cross_encoder,
                )
            )
    return matches


def _run_grounding(
    chunk_results,
    chunks,
    client,
    config,
    retrieval,
    index,
    call_collector,
    grounding_passes=1,
    grounding_batch_size=0,
    chunk_contexts=None,
):
    all_matches = []
    all_filtered = []
    total_candidates = 0
    total_grounded = 0
    max_workers = config.max_concurrent

    ground_tasks = [cr for cr in chunk_results if cr.accepted]
    for cr in ground_tasks:
        total_candidates += len(cr.accepted)

    logger.info(
        "Grounding %d chunks with %d candidates (%d passes, batch_size=%d)",
        len(ground_tasks),
        total_candidates,
        grounding_passes,
        grounding_batch_size,
    )

    if ground_tasks:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    _ground_one,
                    cr,
                    chunks,
                    client,
                    config.model,
                    call_collector,
                    grounding_passes,
                    grounding_batch_size,
                    chunk_contexts[cr.chunk_index] if chunk_contexts else "",
                ): cr
                for cr in ground_tasks
            }
            for future in as_completed(futures):
                cr, grounded = future.result()
                total_grounded += len(grounded)
                grounded_ids = set(grounded.keys())
                for candidate in cr.accepted:
                    accepted_by = determine_accepted_by(
                        candidate,
                        borderline_judged=cr.borderline_judged,
                        use_cross_encoder=retrieval.use_cross_encoder,
                        no_judge=retrieval.no_judge,
                    )
                    rid = candidate.risk_id
                    if rid in grounded_ids:
                        evidence, confidence = grounded[rid]
                        all_matches.append(
                            build_risk_match(
                                candidate,
                                taxonomy=index.get_taxonomy(rid),
                                accepted_by=accepted_by,
                                grounding_confidence=confidence,
                                evidence=evidence,
                                use_cross_encoder=retrieval.use_cross_encoder,
                            )
                        )
                    else:
                        all_filtered.append(
                            FilteredCandidate(
                                risk_id=rid,
                                risk_name=candidate.risk_name,
                                taxonomy=index.get_taxonomy(rid),
                                cross_encoder_score=candidate.cross_encoder_score,
                                rrf_score=candidate.rrf_score,
                                bm25_rank=candidate.bm25_rank,
                                accepted_by=accepted_by,
                                chunk_index=cr.chunk_index,
                            )
                        )

    grounding_filtered = total_candidates - total_grounded
    return all_matches, all_filtered, grounding_filtered


def _ground_variants_one(
    parent_match,
    chunks,
    variant_map,
    client,
    model,
    call_collector,
    chunk_contexts=None,
):
    """Run variant-selective grounding for a single parent-level match."""
    parent_id = parent_match.risk_id
    variants = variant_map.get(parent_id, [])
    if not variants:
        return parent_match, {}

    evidence = parent_match.evidence
    if not evidence:
        return parent_match, {}

    best_ev = max(evidence, key=lambda e: e.cross_encoder_score, default=evidence[0])
    ci = best_ev.chunk_index
    text = chunk_contexts[ci] if chunk_contexts and ci < len(chunk_contexts) else chunks[ci].text
    chunk = chunks[ci]

    grounded = ground_variants(
        chunk_text=text,
        parent_id=parent_id,
        parent_name=parent_match.risk_name,
        parent_description=parent_match.risk_description,
        variants=variants,
        client=client,
        model=model,
        document=best_ev.document,
        chunk_index=ci,
        page=chunk.page if hasattr(chunk, "page") else None,
        section=chunk.section if hasattr(chunk, "section") else None,
        call_collector=call_collector,
    )
    return parent_match, grounded


def _run_variant_grounding(
    grounded_matches,
    chunks,
    variant_map,
    client,
    config,
    call_collector,
    chunk_contexts=None,
    max_workers=4,
):
    parent_matches = []
    non_parent_matches = []
    for m in grounded_matches:
        if m.risk_id in variant_map:
            parent_matches.append(m)
        else:
            non_parent_matches.append(m)

    if not parent_matches:
        return grounded_matches

    logger.info(
        "Variant grounding: %d parent matches (%d non-parent matches kept as-is)",
        len(parent_matches),
        len(non_parent_matches),
    )

    variant_matches: list[RiskMatch] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                _ground_variants_one,
                pm,
                chunks,
                variant_map,
                client,
                config.model,
                call_collector,
                chunk_contexts,
            ): pm
            for pm in parent_matches
        }
        for future in as_completed(futures):
            parent_match, grounded = future.result()
            for vid, (evidence, confidence) in grounded.items():
                vinfo = next(
                    (v for v in variant_map[parent_match.risk_id] if v["risk_id"] == vid),
                    None,
                )
                if not vinfo:
                    continue
                stub = ScoredCandidate(
                    risk_id=vid,
                    risk_name=vinfo["name"],
                    risk_description=vinfo["description"],
                    bm25_rank=parent_match.scores.bm25_rank,
                    embedding_distance=parent_match.scores.embedding_distance,
                    cross_encoder_score=parent_match.scores.cross_encoder_score,
                    rrf_score=parent_match.scores.rrf_score,
                )
                variant_matches.append(
                    build_risk_match(
                        stub,
                        taxonomy=vinfo.get("taxonomy", ""),
                        accepted_by=parent_match.accepted_by,
                        grounding_confidence=confidence,
                        evidence=evidence,
                    )
                )

    return non_parent_matches + variant_matches


def _run_judge(
    chunk_results,
    chunks,
    client,
    config,
    retrieval,
    call_collector,
    chunk_contexts=None,
):
    max_workers = config.max_concurrent
    judge_tasks = [(i, cr) for i, cr in enumerate(chunk_results) if cr.borderline]
    logger.info(
        "Judge: %d chunks with borderline candidates (no_judge=%s)",
        len(judge_tasks),
        retrieval.no_judge,
    )
    if retrieval.no_judge:
        for cr in chunk_results:
            if cr.borderline:
                cr.borderline_judged = list(cr.borderline)
                cr.accepted.extend(cr.borderline)
    elif retrieval.use_cross_encoder:
        if judge_tasks:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(
                        _judge_one,
                        i,
                        cr,
                        client,
                        config.model,
                        call_collector,
                        retrieval.judge_prompt,
                        retrieval.grounding_batch_size,
                        chunk_contexts[i] if chunk_contexts else "",
                    ): i
                    for i, cr in judge_tasks
                }
                for future in as_completed(futures):
                    idx, judged = future.result()
                    chunk_results[idx].borderline_judged = judged
                    chunk_results[idx].accepted.extend(judged)


def _build_chunk_risk_map(chunk_results, all_matches, no_grounding):
    chunk_risk_ids: dict[int, list[str]] = {}
    if no_grounding:
        for cr in chunk_results:
            for candidate in cr.accepted:
                chunk_risk_ids.setdefault(cr.chunk_index, []).append(candidate.risk_id)
    else:
        for m in all_matches:
            for ev in m.evidence:
                chunk_risk_ids.setdefault(ev.chunk_index, []).append(m.risk_id)
    return chunk_risk_ids


def _build_found_risk_chunks(merged, chunk_results) -> dict[str, set[int]]:
    """Map each found risk id to the chunks that show it.

    Sources are the accepted retrieval candidates and the merged grounding
    evidence; both tell the expansion grouper where a found risk lives.
    """
    found_risk_chunks: dict[str, set[int]] = {}
    for cr in chunk_results:
        for candidate in cr.accepted:
            cid = candidate.risk_id.split(" ")[0].strip()
            found_risk_chunks.setdefault(cid, set()).add(cr.chunk_index)
    for m in merged:
        for ev in m.evidence:
            found_risk_chunks.setdefault(m.risk_id, set()).add(ev.chunk_index)
    return found_risk_chunks


def _ground_expansion_group(group, chunks, documents, client, config, call_collector):
    """Ground one expansion group once against the group's chunk set."""
    return ground_risk_group(
        chunks=chunks,
        chunk_indices=group.chunk_indices,
        risks=list(group.risk_lookup.values()),
        client=client,
        model=config.model,
        document=str(documents[0]) if documents else "",
        call_collector=call_collector,
    )


def _ground_expansion_group_multi(group, chunks, documents, client, config, call_collector, passes):
    """Ground one group across several passes; the first pass wins per risk id.

    A risk grounded by an earlier pass keeps its evidence and confidence even
    when a later pass grounds it differently.
    """
    merged_results: dict[str, tuple[list[EvidenceSpan], str]] = {}
    for _ in range(passes):
        grounded = _ground_expansion_group(group, chunks, documents, client, config, call_collector)
        for rid, (evidence, confidence) in grounded.items():
            if rid not in merged_results:
                merged_results[rid] = (evidence, confidence)
    return merged_results


def _build_expansion_matches(grounded, index, risk_lookup) -> list[RiskMatch]:
    """Convert one group's grounded risks into expansion matches."""
    matches = []
    for rid, (evidence, confidence) in grounded.items():
        info = risk_lookup.get(rid, {})
        stub = ScoredCandidate(
            risk_id=rid,
            risk_name=info.get("name", ""),
            risk_description=info.get("description", ""),
        )
        matches.append(
            build_risk_match(
                stub,
                taxonomy=index.get_taxonomy(rid),
                accepted_by="expansion",
                grounding_confidence=confidence,
                evidence=evidence,
                confidence_override=0.0,
            )
        )
    return matches


def _ground_expansion_groups(
    groups, chunks, documents, index, client, config, max_workers, call_collector, expansion_passes, risk_lookup
) -> tuple[list[RiskMatch], int]:
    """Ground all expansion groups concurrently.

    With one pass each group grounds directly; with several, the per-group
    first-wins union runs inside the worker before any match is built.
    Returns the expansion matches and the grounded-risk count.
    """

    def _submit(pool, group):
        if expansion_passes > 1:
            return pool.submit(
                _ground_expansion_group_multi,
                group,
                chunks,
                documents,
                client,
                config,
                call_collector,
                expansion_passes,
            )
        return pool.submit(_ground_expansion_group, group, chunks, documents, client, config, call_collector)

    expansion_matches: list[RiskMatch] = []
    expanded_grounded = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {_submit(pool, g): g for g in groups}
        for future in as_completed(futures):
            grounded = future.result()
            expanded_grounded += len(grounded)
            expansion_matches.extend(_build_expansion_matches(grounded, index, risk_lookup))
    return expansion_matches, expanded_grounded


def _expand_siblings(risks, merged, chunk_results, chunks, stats) -> tuple:
    """Prepare sibling-expansion candidates and their grounding groups.

    Returns (expanded, groups, risk_lookup): the sibling candidates not yet
    found, their grounding groups (empty when there are no candidates), and
    the catalog lookup the matches are built from. Records the candidate and
    group counts in stats.
    """
    from asago_policy_mapper.extract.expand import (
        build_expansion_graph,
        expand_with_siblings,
        group_for_grounding,
    )

    risk_lookup = {r.id: {"name": r.name or "", "description": r.description or ""} for r in risks}
    risk_to_parent = {}
    for r in risks:
        parent = getattr(r, "isPartOf", "") or ""
        if parent:
            risk_to_parent[r.id] = parent

    expansion_graph = build_expansion_graph(risks)
    merged_ids = {m.risk_id for m in merged}
    expanded = expand_with_siblings(merged_ids, expansion_graph, risk_lookup)
    stats["expanded_candidates"] = len(expanded)
    if not expanded:
        return expanded, [], risk_lookup

    groups = group_for_grounding(
        expanded,
        _build_found_risk_chunks(merged, chunk_results),
        risk_to_parent,
        len(chunks),
    )
    stats["expansion_groups"] = len(groups)
    return expanded, groups, risk_lookup


def _run_expansion(
    risks,
    merged,
    chunk_results,
    chunks,
    documents,
    index,
    client,
    config,
    max_workers,
    call_collector,
    expansion_passes: int = 1,
    variant_map: dict | None = None,
    chunk_contexts=None,
) -> tuple[list[RiskMatch], dict]:
    stats = {"expanded_candidates": 0, "expanded_grounded": 0, "expansion_groups": 0}
    expanded, groups, risk_lookup = _expand_siblings(risks, merged, chunk_results, chunks, stats)
    if not expanded:
        return merged, stats

    logger.info(
        "Expansion: %d sibling candidates in %d groups (%d passes)",
        stats["expanded_candidates"],
        stats["expansion_groups"],
        expansion_passes,
    )

    expansion_matches, stats["expanded_grounded"] = _ground_expansion_groups(
        groups, chunks, documents, index, client, config, max_workers, call_collector, expansion_passes, risk_lookup
    )

    if expansion_matches and variant_map:
        expansion_matches = _run_variant_grounding(
            expansion_matches,
            chunks,
            variant_map,
            client,
            config,
            call_collector,
            chunk_contexts=chunk_contexts,
            max_workers=max_workers,
        )

    if expansion_matches:
        merged = merge_matches(merged + expansion_matches)

    return merged, stats


def _run_causal_synthesis(merged, chunks, client, config, max_workers, call_collector):
    chunk_texts = {i: chunks[i].text for i in range(len(chunks))}

    def _synthesize_one(risk_match):
        return risk_match.risk_id, synthesize_causal_chain(
            risk_match=risk_match,
            chunk_texts=chunk_texts,
            client=client,
            model=config.model,
            call_collector=call_collector,
        )

    results: dict[str, _CausalChain | None] = {}
    logger.info("Causal synthesis: %d risks", len(merged))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_synthesize_one, m): m for m in merged}
        for future in as_completed(futures):
            risk_id, chain = future.result()
            results[risk_id] = chain

    for m in merged:
        chain = results.get(m.risk_id)
        if chain:
            m.threat = chain.threat or None
            m.threat_source = chain.threat_source or None
            m.vulnerability = chain.vulnerability or None
            m.consequence = chain.consequence or None
            m.impact = chain.impact or None

    return merged


def _filter_agentic_risks(risks, parsed):
    """Drop agentic risks when no document mentions agent terminology."""
    if _document_discusses_agents([p.content for p in parsed]):
        return risks
    original_count = len(risks)
    risks = [r for r in risks if getattr(r, "risk_type", None) != "agentic"]
    filtered = original_count - len(risks)
    if filtered:
        logger.info(
            "Filtered %d agentic risks (no agent terminology in documents)",
            filtered,
        )
    return risks


def _build_risk_index(risks, retrieval) -> RiskIndex:
    """Build the retrieval index over the risk catalog with the configured encoders."""
    return RiskIndex(
        risks,
        bi_encoder_model=retrieval.bi_encoder_model,
        cross_encoder_model=retrieval.effective_cross_encoder_model,
        colbert_model=retrieval.colbert_model,
        query_instruction=retrieval.query_instruction,
        cross_encoder_type=retrieval.cross_encoder_type,
        bi_encoder_api_key=retrieval.bi_encoder_api_key,
        bi_encoder_model_name=retrieval.bi_encoder_model_name,
        cross_encoder_model_name=retrieval.cross_encoder_model_name,
    )


def _run_query_gen(chunks, client, config, call_collector, max_workers, timing) -> tuple[list, set[int]]:
    """Generate search queries per section group for query-gen retrieval.

    Returns the generated queries and the chunk indices that got no query
    and fall back to per-chunk retrieval.
    """
    with timed(timing, "query_gen_ms"):
        groups = group_chunks(chunks)
        qg_result = generate_queries(
            chunks,
            groups,
            client,
            config.model,
            call_collector=call_collector,
            max_workers=max_workers,
            return_fallbacks=True,
        )
        assert isinstance(qg_result, tuple)
        query_results, fallback_list = qg_result
        fallback_chunk_indices = set(fallback_list)
        logger.info(
            "Query generation: %d queries from %d groups, %d fallback chunks",
            len(query_results),
            len(groups),
            len(fallback_chunk_indices),
        )
    return query_results, fallback_chunk_indices


def _merge_query_candidates(chunk_results, chunks, qr, candidates):
    """Add a query's candidates to every chunk the query covers.

    The first occurrence of a risk id wins; later queries only append risks
    the chunk has not seen yet.
    """
    for ci in qr.chunk_indices:
        chunk = chunks[ci]
        if chunk_results[ci] is not None:
            existing_ids = {c.risk_id for c in chunk_results[ci].accepted}
            for c in candidates:
                if c.risk_id not in existing_ids:
                    chunk_results[ci].accepted.append(c)
                    existing_ids.add(c.risk_id)
        else:
            chunk_results[ci] = ChunkResult(
                chunk_index=ci,
                source=chunk.source,
                page=chunk.page,
                section=chunk.section,
                accepted=list(candidates),
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


def _retrieve_chunk_result(chunks, i, index, retrieval) -> ChunkResult:
    """Run per-chunk hybrid retrieval with the pipeline's retrieval settings."""
    return retrieve_chunk(
        chunks,
        i,
        index,
        top_n_accept=retrieval.top_n_accept,
        top_n_judge=retrieval.top_n_judge,
        min_score_floor=retrieval.min_score_floor,
        bm25_rescue_rank=retrieval.bm25_rescue_rank,
        use_cross_encoder=retrieval.use_cross_encoder,
        rrf_min_score=retrieval.effective_rrf_min_score,
        threshold_high=retrieval.threshold_high,
        threshold_low=retrieval.threshold_low,
    )


def _run_retrieval(chunks, index, retrieval, query_results, fallback_chunk_indices, timing) -> list[ChunkResult]:
    """Retrieve candidates per chunk: query-gen queries first, then per-chunk fallback.

    With query generation on, each query's candidates are unioned into every
    chunk the query covers (capped per chunk), and chunks without a query —
    plus fallback chunks — go through per-chunk retrieval. With query
    generation off, every chunk goes through per-chunk retrieval.
    """
    with timed(timing, "retrieve_ms"):
        chunk_results: list[ChunkResult] = [None] * len(chunks)  # type: ignore[list-item]

        if retrieval.query_gen:
            for qr in query_results:
                candidates = index.hybrid_search(
                    qr.query,
                    top_k=50,
                    bm25_rescue_rank=retrieval.bm25_rescue_rank,
                    rrf_min_score=retrieval.rrf_min_score or 0.015,
                )
                _merge_query_candidates(chunk_results, chunks, qr, candidates)

            _cap_accepted_candidates(chunk_results, _QUERY_GEN_MAX_CANDIDATES)

            retrieval_indices = fallback_chunk_indices | {i for i in range(len(chunks)) if chunk_results[i] is None}
            for i in sorted(retrieval_indices):
                chunk_results[i] = _retrieve_chunk_result(chunks, i, index, retrieval)
        else:
            for i in range(len(chunks)):
                chunk_results[i] = _retrieve_chunk_result(chunks, i, index, retrieval)

    return chunk_results


def _build_chunk_summaries(chunk_results, chunks) -> list[ChunkSummary]:
    """Summarize per-chunk retrieval counters for the ExtractionResult."""
    return [
        ChunkSummary(
            index=cr.chunk_index,
            source=cr.source,
            page=cr.page,
            section=cr.section,
            text_preview=chunks[cr.chunk_index].text[:200],
            candidates_retrieved=cr.stats.get("candidates_retrieved", 0),
            auto_accepted=cr.stats.get("auto_accepted", 0),
            borderline=cr.stats.get("borderline", 0),
            discarded=cr.stats.get("discarded", 0),
            bm25_rescued=cr.stats.get("bm25_rescued", 0),
        )
        for cr in chunk_results
    ]


def _run_matches_stage(
    chunk_results, chunks, client, config, retrieval, index, call_collector, chunk_contexts, timing
) -> tuple[list[RiskMatch], list[FilteredCandidate], int]:
    """Ground accepted candidates, or collect them ungrounded when grounding is disabled."""
    if retrieval.no_grounding:
        all_matches = _collect_ungrounded(chunk_results, index, retrieval)
        all_filtered: list[FilteredCandidate] = []
        timing["grounding_ms"] = 0.0
        grounding_filtered = 0
    else:
        with timed(timing, "grounding_ms"):
            all_matches, all_filtered, grounding_filtered = _run_grounding(
                chunk_results,
                chunks,
                client,
                config,
                retrieval,
                index,
                call_collector,
                grounding_passes=retrieval.grounding_passes,
                grounding_batch_size=retrieval.grounding_batch_size,
                chunk_contexts=chunk_contexts,
            )
    return all_matches, all_filtered, grounding_filtered


def _build_retrieval_stats(chunk_results, chunks, timing, grounding_filtered) -> RetrievalStats:
    """Aggregate per-chunk counters into the run's retrieval stats."""
    return RetrievalStats(
        total_chunks=len(chunks),
        total_candidates_retrieved=sum(cr.stats.get("candidates_retrieved", 0) for cr in chunk_results),
        auto_accepted=sum(cr.stats.get("auto_accepted", 0) for cr in chunk_results),
        llm_judged=sum(len(cr.borderline_judged) for cr in chunk_results),
        grounding_filtered=grounding_filtered,
        timing_ms=timing,
    )


def _build_result_metadata(config, retrieval, expansion_stats, query_results, fallback_chunk_indices) -> dict:
    """Assemble the run metadata recorded alongside the extraction result."""
    metadata = {
        "model": config.model,
        **({"service_tier": config.service_tier} if config.service_tier is not None else {}),
        **retrieval.to_metadata(),
        "expansion_stats": expansion_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if retrieval.query_gen:
        metadata["query_gen_queries"] = [
            {"query": qr.query, "chunk_indices": qr.chunk_indices, "section": qr.section} for qr in query_results
        ]
        metadata["query_gen_fallback_chunks"] = sorted(fallback_chunk_indices)
    return metadata


_EMPTY_EXPANSION_STATS = {"expanded_candidates": 0, "expanded_grounded": 0, "expansion_groups": 0}


def _run_variant_grounding_stage(
    all_matches, chunks, index, client, config, retrieval, call_collector, chunk_contexts, max_workers, timing
):
    """Variant-ground grounded matches when variants and a client are present."""
    if index.variant_map and not retrieval.no_grounding and client is not None:
        with timed(timing, "variant_grounding_ms"):
            return _run_variant_grounding(
                all_matches,
                chunks,
                index.variant_map,
                client,
                config,
                call_collector,
                chunk_contexts=chunk_contexts,
                max_workers=max_workers,
            )
    return all_matches


def _run_expansion_stage(
    merged,
    risks,
    chunk_results,
    chunks,
    documents,
    index,
    client,
    config,
    retrieval,
    call_collector,
    chunk_contexts,
    max_workers,
    timing,
) -> tuple[list, dict]:
    """Expand to sibling risks and ground them; grounded runs only.

    Returns the (possibly expanded) merged list and the expansion stats; the
    counters stay at zero when the stage is skipped.
    """
    if retrieval.expand_siblings and not retrieval.no_grounding and client is not None:
        with timed(timing, "expansion_ms"):
            merged, expansion_stats = _run_expansion(
                risks,
                merged,
                chunk_results,
                chunks,
                documents,
                index,
                client,
                config,
                max_workers,
                call_collector,
                expansion_passes=retrieval.expansion_passes,
                variant_map=index.variant_map if index.variant_map else None,
                chunk_contexts=chunk_contexts,
            )
            return merged, expansion_stats
    return merged, _EMPTY_EXPANSION_STATS.copy()


def _run_causal_synthesis_stage(merged, chunks, client, config, retrieval, call_collector, max_workers, timing):
    """Synthesize causal chains for each merged risk when a client is present."""
    if not retrieval.no_causal_synthesis and client is not None:
        with timed(timing, "causal_synthesis_ms"):
            return _run_causal_synthesis(
                merged,
                chunks,
                client,
                config,
                max_workers,
                call_collector,
            )
    return merged


def _expand_chunk_variants(chunk_results, index):
    """Expand collapsed parent candidates back to their variants in place.

    Ungrounded runs keep the variant granularity at match time, so the
    accepted and borderline lists are re-expanded per chunk.
    """
    for cr in chunk_results:
        cr.accepted = index.expand_variants(cr.accepted)
        cr.borderline = index.expand_variants(cr.borderline)


def _parse_and_chunk(documents, ocr, retrieval, timing) -> tuple | None:
    """Parse documents and chunk them; returns (parsed, chunks, contexts) or None.

    None means the run short-circuits: every document parsed empty or the
    documents produced no chunks. The parse and chunk stages are timed.
    """
    with timed(timing, "parse_ms"):
        parsed = [parse_document(doc, ocr=ocr) for doc in documents]
        parsed = [p for p in parsed if p.content.strip()]
        if not parsed:
            logger.warning("All documents are empty after parsing")
            return None

    with timed(timing, "chunk_ms"):
        chunks = chunk_documents(parsed, max_tokens=retrieval.chunk_max_tokens)
        if not chunks:
            return None
        chunk_contexts = build_chunk_contexts(chunks)
    logger.info("Chunked %d document(s) into %d chunks", len(parsed), len(chunks))
    return parsed, chunks, chunk_contexts


def run_extraction(
    documents: list[Path],
    client,
    config: LLMConfig,
    risks: list,
    retrieval: RetrievalConfig | None = None,
    *,
    ocr: bool = False,
) -> ExtractionResult:
    retrieval = retrieval or RetrievalConfig()
    timing: dict[str, float] = {}
    max_workers = config.max_concurrent

    prepared = _parse_and_chunk(documents, ocr, retrieval, timing)
    if prepared is None:
        return _empty_result(documents)
    parsed, chunks, chunk_contexts = prepared

    risks = _filter_agentic_risks(risks, parsed)

    with timed(timing, "index_ms"):
        if not risks:
            logger.error("No risks loaded from Nexus")
            return _empty_result(documents)
        index = _build_risk_index(risks, retrieval)

    call_collector: list[LLMCallRecord] = []
    fallback_chunk_indices: set[int] = set()
    query_results: list = []

    if retrieval.query_gen:
        query_results, fallback_chunk_indices = _run_query_gen(
            chunks, client, config, call_collector, max_workers, timing
        )

    chunk_results = _run_retrieval(chunks, index, retrieval, query_results, fallback_chunk_indices, timing)
    logger.info(
        "Retrieval complete: %d chunks, %d accepted candidates",
        len(chunks),
        sum(len(cr.accepted) for cr in chunk_results if cr is not None),
    )

    if index.variant_map and retrieval.no_grounding:
        _expand_chunk_variants(chunk_results, index)

    chunk_summaries = _build_chunk_summaries(chunk_results, chunks)

    with timed(timing, "judge_ms"):
        _run_judge(
            chunk_results,
            chunks,
            client,
            config,
            retrieval,
            call_collector,
            chunk_contexts=chunk_contexts,
        )

    all_matches, all_filtered, grounding_filtered = _run_matches_stage(
        chunk_results, chunks, client, config, retrieval, index, call_collector, chunk_contexts, timing
    )

    all_matches = _run_variant_grounding_stage(
        all_matches, chunks, index, client, config, retrieval, call_collector, chunk_contexts, max_workers, timing
    )

    chunk_risk_ids = _build_chunk_risk_map(chunk_results, all_matches, retrieval.no_grounding)
    for cs in chunk_summaries:
        cs.accepted_risk_ids = sorted(set(chunk_risk_ids.get(cs.index, [])))

    with timed(timing, "merge_ms"):
        merged = merge_matches(all_matches)

    merged, expansion_stats = _run_expansion_stage(
        merged,
        risks,
        chunk_results,
        chunks,
        documents,
        index,
        client,
        config,
        retrieval,
        call_collector,
        chunk_contexts,
        max_workers,
        timing,
    )

    merged = _run_causal_synthesis_stage(merged, chunks, client, config, retrieval, call_collector, max_workers, timing)

    total_stats = _build_retrieval_stats(chunk_results, chunks, timing, grounding_filtered)

    return ExtractionResult(
        risks=merged,
        source_documents=[str(d) for d in documents],
        retrieval_stats=total_stats,
        metadata=_build_result_metadata(config, retrieval, expansion_stats, query_results, fallback_chunk_indices),
        chunks=chunk_summaries,
        llm_calls=call_collector,
        grounding_filtered_candidates=all_filtered,
    )


def _empty_result(documents: list[Path]) -> ExtractionResult:
    return ExtractionResult(
        risks=[],
        source_documents=[str(d) for d in documents],
        retrieval_stats=RetrievalStats(
            total_chunks=0,
            total_candidates_retrieved=0,
            auto_accepted=0,
            llm_judged=0,
            grounding_filtered=0,
        ),
    )
