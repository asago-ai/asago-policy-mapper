from __future__ import annotations

import logging

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from concorde_policy_mapper.extract.models import ScoredCandidate

logger = logging.getLogger(__name__)

_DEFAULT_BI_ENCODER = "all-mpnet-base-v2"
_DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-12-v2"

_SIGMOID_MODELS = {"cross-encoder/ms-marco-MiniLM-L-12-v2", "cross-encoder/ms-marco-electra-base"}


def _maxsim(query_tokens: np.ndarray, doc_tokens: np.ndarray) -> float:
    """ColBERT MaxSim: for each query token, find max cosine similarity with any doc token, then sum."""
    sim = np.dot(query_tokens, doc_tokens.T)
    return float(sim.max(axis=1).sum())


class RiskIndex:
    def __init__(
        self,
        risks: list,
        bi_encoder_model: str = _DEFAULT_BI_ENCODER,
        cross_encoder_model: str | None = _DEFAULT_CROSS_ENCODER,
        colbert_model: str | None = None,
    ):
        self._risk_ids: list[str] = []
        self._risk_meta: dict[str, dict] = {}
        self._bm25: BM25Okapi | None = None
        self._embeddings: np.ndarray | None = None
        self._colbert_doc_embeddings: list[np.ndarray] | None = None

        if not risks:
            self._bi_encoder = None
            self._cross_encoder = None
            self._colbert = None
            return

        for r in risks:
            rid = r.id
            self._risk_ids.append(rid)
            self._risk_meta[rid] = {
                "name": r.name or "",
                "description": r.description or "",
                "concern": getattr(r, "concern", "") or "",
                "taxonomy": getattr(r, "isDefinedByTaxonomy", "") or "",
            }

        bm25_corpus = []
        for r in risks:
            parts = [
                r.name or "",
                r.description or "",
                getattr(r, "concern", "") or "",
                getattr(r, "isPartOf", "") or "",
            ]
            bm25_corpus.append(" ".join(parts).lower().split())
        self._bm25 = BM25Okapi(bm25_corpus)

        if colbert_model:
            import torch
            self._colbert = SentenceTransformer(
                colbert_model,
                model_kwargs={"torch_dtype": torch.bfloat16},
            )
            descriptions = [f"{r.name or ''}: {r.description or ''}" for r in risks]
            raw = self._colbert.encode(
                descriptions, output_value="token_embeddings",
                show_progress_bar=False, batch_size=32,
            )
            self._colbert_doc_embeddings = []
            for emb in raw:
                arr = emb.cpu().float().numpy() if hasattr(emb, "cpu") else np.array(emb, dtype=np.float32)
                arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
                self._colbert_doc_embeddings.append(arr)
            self._bi_encoder = None
            self._cross_encoder = None
            self._apply_sigmoid = False
            logger.info("ColBERT index built: %d risks, %s", len(risks), colbert_model)
        else:
            self._colbert = None
            self._bi_encoder = SentenceTransformer(bi_encoder_model)
            descriptions = [f"{r.name or ''}: {r.description or ''}" for r in risks]
            self._embeddings = self._bi_encoder.encode(
                descriptions, normalize_embeddings=True, show_progress_bar=False
            )
            if cross_encoder_model:
                self._cross_encoder = CrossEncoder(cross_encoder_model)
                self._apply_sigmoid = cross_encoder_model in _SIGMOID_MODELS
            else:
                self._cross_encoder = None
                self._apply_sigmoid = False

    @property
    def risk_count(self) -> int:
        return len(self._risk_ids)

    @property
    def cross_encoder(self):
        return self._cross_encoder

    @property
    def has_colbert(self) -> bool:
        return self._colbert is not None

    def get_taxonomy(self, risk_id: str) -> str:
        return self._risk_meta.get(risk_id, {}).get("taxonomy", "")

    def search_bm25(self, text: str, top_k: int = 100) -> list[ScoredCandidate]:
        if not self._bm25:
            return []
        tokens = text.lower().split()
        scores = self._bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] <= 0:
                break
            rid = self._risk_ids[idx]
            meta = self._risk_meta[rid]
            results.append(
                ScoredCandidate(
                    risk_id=rid,
                    risk_name=meta["name"],
                    risk_description=meta["description"],
                    bm25_rank=rank + 1,
                )
            )
        return results

    def search_semantic(self, text: str, top_k: int = 100) -> list[ScoredCandidate]:
        if self._bi_encoder is None or self._embeddings is None:
            return []
        query_emb = self._bi_encoder.encode(text, normalize_embeddings=True)
        similarities = np.dot(self._embeddings, query_emb)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            rid = self._risk_ids[idx]
            meta = self._risk_meta[rid]
            results.append(
                ScoredCandidate(
                    risk_id=rid,
                    risk_name=meta["name"],
                    risk_description=meta["description"],
                    embedding_distance=float(1.0 - similarities[idx]),
                )
            )
        return results

    def search_colbert(self, text: str, top_k: int = 100) -> list[ScoredCandidate]:
        if self._colbert is None or self._colbert_doc_embeddings is None:
            return []
        query_emb = self._colbert.encode(text, output_value="token_embeddings")
        query_arr = query_emb.cpu().float().numpy() if hasattr(query_emb, "cpu") else np.array(query_emb, dtype=np.float32)
        query_arr = query_arr / np.linalg.norm(query_arr, axis=1, keepdims=True)
        n_query_tokens = query_arr.shape[0]

        scores = np.array([
            _maxsim(query_arr, doc_emb) / n_query_tokens
            for doc_emb in self._colbert_doc_embeddings
        ])
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                break
            rid = self._risk_ids[idx]
            meta = self._risk_meta[rid]
            results.append(
                ScoredCandidate(
                    risk_id=rid,
                    risk_name=meta["name"],
                    risk_description=meta["description"],
                    cross_encoder_score=float(scores[idx]),
                    embedding_distance=0.0,
                )
            )
        return results

    def rerank(
        self, text: str, candidates: list[ScoredCandidate], top_k: int = 50
    ) -> list[ScoredCandidate]:
        if not candidates or not self._cross_encoder:
            return []
        pairs = [(f"{c.risk_name}: {c.risk_description}", text) for c in candidates]
        raw_scores = self._cross_encoder.predict(pairs)
        if self._apply_sigmoid:
            scores = 1.0 / (1.0 + np.exp(-np.array(raw_scores)))
        else:
            scores = np.clip(np.array(raw_scores, dtype=np.float64), 0.0, 1.0)
        scored = sorted(
            zip(candidates, scores), key=lambda x: x[1], reverse=True
        )
        results = []
        for c, score in scored[:top_k]:
            s = float(score)
            if np.isnan(s) or np.isinf(s):
                logger.warning("Skipping candidate %s with invalid score", c.risk_id)
                continue
            results.append(c.model_copy(update={"cross_encoder_score": s}))
        return results

    def hybrid_search(
        self,
        text: str,
        top_k: int = 50,
        bm25_top_k: int = 100,
        semantic_top_k: int = 100,
        rrf_k: int = 60,
        bm25_rescue_rank: int = 0,
        rrf_min_score: float = 0.0,
    ) -> list[ScoredCandidate]:
        if self._colbert is not None:
            return self._hybrid_search_colbert(text, top_k, bm25_top_k, rrf_k, bm25_rescue_rank)

        bm25_results = self.search_bm25(text, top_k=bm25_top_k)
        semantic_results = self.search_semantic(text, top_k=semantic_top_k)

        if not bm25_results and not semantic_results:
            return []

        rrf_scores: dict[str, float] = {}
        candidate_data: dict[str, ScoredCandidate] = {}
        bm25_ranks: dict[str, int] = {}
        semantic_distances: dict[str, float] = {}

        for rank, c in enumerate(bm25_results, 1):
            rrf_scores[c.risk_id] = rrf_scores.get(c.risk_id, 0) + 1 / (rrf_k + rank)
            candidate_data[c.risk_id] = c
            bm25_ranks[c.risk_id] = rank

        for rank, c in enumerate(semantic_results, 1):
            rrf_scores[c.risk_id] = rrf_scores.get(c.risk_id, 0) + 1 / (rrf_k + rank)
            if c.risk_id not in candidate_data:
                candidate_data[c.risk_id] = c
            semantic_distances[c.risk_id] = c.embedding_distance

        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)
        rrf_candidates = []
        for rid in sorted_ids[: top_k * 2]:
            c = candidate_data[rid]
            rrf_candidates.append(
                c.model_copy(
                    update={
                        "rrf_score": rrf_scores[rid],
                        "bm25_rank": bm25_ranks.get(rid, 0),
                        "embedding_distance": semantic_distances.get(
                            rid, c.embedding_distance
                        ),
                    }
                )
            )

        if rrf_min_score > 0:
            return [
                c for c in rrf_candidates
                if c.rrf_score >= rrf_min_score
            ][:top_k]

        reranked = self.rerank(text, rrf_candidates, top_k=top_k)

        if bm25_rescue_rank > 0:
            reranked_ids = {c.risk_id for c in reranked}
            for c in rrf_candidates:
                if (
                    c.risk_id not in reranked_ids
                    and c.bm25_rank > 0
                    and c.bm25_rank <= bm25_rescue_rank
                ):
                    reranked.append(c)

        rrf_lookup = {c.risk_id: c for c in rrf_candidates}
        results = []
        for c in reranked:
            source = rrf_lookup.get(c.risk_id)
            if source:
                results.append(
                    c.model_copy(
                        update={
                            "rrf_score": source.rrf_score,
                            "bm25_rank": source.bm25_rank,
                            "embedding_distance": source.embedding_distance,
                        }
                    )
                )
            else:
                results.append(c)
        return results

    def _hybrid_search_colbert(
        self,
        text: str,
        top_k: int = 50,
        bm25_top_k: int = 100,
        rrf_k: int = 60,
        bm25_rescue_rank: int = 0,
    ) -> list[ScoredCandidate]:
        """Hybrid search using ColBERT MaxSim + BM25 with RRF fusion.

        ColBERT replaces both bi-encoder retrieval and cross-encoder reranking.
        MaxSim scores are stored in cross_encoder_score for threshold compatibility.
        """
        bm25_results = self.search_bm25(text, top_k=bm25_top_k)
        colbert_results = self.search_colbert(text, top_k=top_k * 2)

        if not bm25_results and not colbert_results:
            return []

        rrf_scores: dict[str, float] = {}
        candidate_data: dict[str, ScoredCandidate] = {}
        bm25_ranks: dict[str, int] = {}
        colbert_scores: dict[str, float] = {}

        for rank, c in enumerate(bm25_results, 1):
            rrf_scores[c.risk_id] = rrf_scores.get(c.risk_id, 0) + 1 / (rrf_k + rank)
            candidate_data[c.risk_id] = c
            bm25_ranks[c.risk_id] = rank

        for rank, c in enumerate(colbert_results, 1):
            rrf_scores[c.risk_id] = rrf_scores.get(c.risk_id, 0) + 1 / (rrf_k + rank)
            if c.risk_id not in candidate_data:
                candidate_data[c.risk_id] = c
            colbert_scores[c.risk_id] = c.cross_encoder_score

        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

        results = []
        for rid in sorted_ids:
            c = candidate_data[rid]
            results.append(
                c.model_copy(
                    update={
                        "rrf_score": rrf_scores[rid],
                        "bm25_rank": bm25_ranks.get(rid, 0),
                        "cross_encoder_score": colbert_scores.get(rid, 0.0),
                    }
                )
            )

        if bm25_rescue_rank > 0:
            result_ids = {c.risk_id for c in results}
            for c in bm25_results:
                if c.risk_id not in result_ids and c.bm25_rank <= bm25_rescue_rank:
                    results.append(
                        c.model_copy(
                            update={
                                "rrf_score": rrf_scores.get(c.risk_id, 0),
                                "cross_encoder_score": colbert_scores.get(c.risk_id, 0.0),
                            }
                        )
                    )

        return results
