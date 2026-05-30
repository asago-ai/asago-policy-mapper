from __future__ import annotations

import logging
import time

from pydantic import BaseModel

from concorde_policy_mapper.extract.models import (
    EvidenceSpan,
    LLMCallRecord,
    RetrievalScores,
    RiskMatch,
)
from concorde_policy_mapper.prompts import render_prompt

logger = logging.getLogger(__name__)


class _ClassifyVerdict(BaseModel):
    risk_id: str
    applies: bool
    source_risk_ids: list[str]


def classify_risks(
    extracted: list[RiskMatch],
    targets: list,
    client,
    model: str,
    *,
    call_collector: list[LLMCallRecord] | None = None,
) -> list[RiskMatch]:
    if not extracted or not targets:
        return []

    extracted_context = []
    for r in extracted:
        quote = ""
        if r.evidence:
            quote = r.evidence[0].text[:200]
        extracted_context.append({
            "risk_id": r.risk_id,
            "risk_name": r.risk_name,
            "evidence_quote": quote,
        })

    target_context = []
    target_lookup = {}
    for t in targets:
        tid = t.id
        target_context.append({
            "id": tid,
            "name": t.name or "",
            "description": t.description or "",
        })
        target_lookup[tid] = t

    messages = render_prompt(
        "classify_risks",
        {
            "extracted_risks": extracted_context,
            "target_risks": target_context,
        },
    )

    t0 = time.time()
    verdicts: list[_ClassifyVerdict] = client.chat.completions.create(
        model=model,
        response_model=list[_ClassifyVerdict],
        messages=messages,
        temperature=0.0,
    )
    duration_ms = (time.time() - t0) * 1000

    extracted_by_id = {r.risk_id: r for r in extracted}
    target_ids = set(target_lookup.keys())
    results: list[RiskMatch] = []

    for v in verdicts:
        if not v.applies or v.risk_id not in target_ids:
            continue

        valid_sources = [sid for sid in v.source_risk_ids if sid in extracted_by_id]
        if not valid_sources:
            continue

        t = target_lookup[v.risk_id]
        evidence = _collect_evidence(valid_sources, extracted_by_id)

        results.append(
            RiskMatch(
                risk_id=v.risk_id,
                risk_name=t.name or "",
                risk_description=t.description or "",
                taxonomy=getattr(t, "isDefinedByTaxonomy", ""),
                confidence=1.0,
                grounding_confidence="high",
                accepted_by="classification",
                evidence=evidence,
                scores=RetrievalScores(
                    bm25_rank=0,
                    embedding_distance=0.0,
                    cross_encoder_score=0.0,
                    rrf_score=0.0,
                ),
                source_risk_ids=valid_sources,
            )
        )

    if call_collector is not None:
        call_id = f"classify-{len([c for c in call_collector if c.stage == 'classify']) + 1:03d}"
        call_collector.append(
            LLMCallRecord(
                call_id=call_id,
                stage="classify",
                risk_ids=[v.risk_id for v in verdicts if v.applies],
                messages=messages,
                response=[v.model_dump() for v in verdicts],
                duration_ms=duration_ms,
                result_summary=f"{len(results)}/{len(targets)} classified",
            )
        )

    logger.info(
        "Taxonomy classification: %d/%d categories matched from %d extracted risks",
        len(results), len(targets), len(extracted),
    )

    return results


def _collect_evidence(
    source_ids: list[str],
    extracted_by_id: dict[str, RiskMatch],
) -> list[EvidenceSpan]:
    seen_texts: set[str] = set()
    evidence: list[EvidenceSpan] = []
    for sid in source_ids:
        source = extracted_by_id.get(sid)
        if not source:
            continue
        for ev in source.evidence:
            key = ev.text[:80].lower()
            if key not in seen_texts:
                seen_texts.add(key)
                evidence.append(ev)
            if len(evidence) >= 3:
                return evidence
    return evidence
