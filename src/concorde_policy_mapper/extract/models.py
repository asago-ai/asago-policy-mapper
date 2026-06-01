from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ScoredCandidate(BaseModel):
    risk_id: str
    risk_name: str
    risk_description: str
    bm25_rank: int = 0
    embedding_distance: float = 0.0
    cross_encoder_score: float = 0.0
    rrf_score: float = 0.0


class EvidenceSpan(BaseModel):
    text: str
    document: str
    page: int | None = None
    section: str | None = None
    chunk_index: int
    sentence_index: int = 0
    cross_encoder_score: float = 0.0


class RetrievalScores(BaseModel):
    bm25_rank: int
    embedding_distance: float
    cross_encoder_score: float
    rrf_score: float


class RiskMatch(BaseModel):
    risk_id: str
    risk_name: str
    risk_description: str
    taxonomy: str = ""
    confidence: float
    grounding_confidence: str
    accepted_by: str
    evidence: list[EvidenceSpan]
    scores: RetrievalScores


class RetrievalStats(BaseModel):
    total_chunks: int
    total_candidates_retrieved: int
    auto_accepted: int
    llm_judged: int
    grounding_filtered: int
    timing_ms: dict[str, float] = {}


class ChunkSummary(BaseModel):
    index: int
    source: str
    page: int | None = None
    section: str | None = None
    text_preview: str
    candidates_retrieved: int
    auto_accepted: int
    borderline: int
    discarded: int
    bm25_rescued: int = 0
    accepted_risk_ids: list[str] = []


class LLMCallRecord(BaseModel):
    call_id: str
    stage: Literal["judge", "grounding"]
    chunk_index: int = -1
    risk_ids: list[str]
    messages: list[dict]
    response: dict | str | list[dict]
    duration_ms: float
    result_summary: str


class FilteredCandidate(BaseModel):
    risk_id: str
    risk_name: str
    taxonomy: str = ""
    cross_encoder_score: float
    rrf_score: float = 0.0
    bm25_rank: int = 0
    accepted_by: str
    chunk_index: int


class ExtractionResult(BaseModel):
    version: str = "0.3"
    risks: list[RiskMatch]
    source_documents: list[str]
    token_usage: dict = {}
    retrieval_stats: RetrievalStats
    metadata: dict = {}
    chunks: list[ChunkSummary] = []
    llm_calls: list[LLMCallRecord] = []
    grounding_filtered_candidates: list[FilteredCandidate] = []
    eval: dict | None = None


class _JudgeVerdict(BaseModel):
    risk_id: str
    relevant: bool
    justification: str


class _GroundingVerdict(BaseModel):
    risk_id: str
    grounded: bool
    confidence: Literal["high", "medium", "low"]


class _RiskEvidence(BaseModel):
    risk_id: str
    grounded: bool
    confidence: Literal["high", "medium", "low"]
    quotes: list[str]
