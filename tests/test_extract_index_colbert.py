"""Stubbed-model tests for the ColBERT paths of RiskIndex.

search_colbert and _hybrid_search_colbert need a local ColBERT checkpoint,
which the suite never loads; until now the only ColBERT test asserted that
remote URLs are rejected. These tests stub SentenceTransformer with a
deterministic fake — the same transport-stubbing approach the LLM tests
use — so the real RiskIndex, _load_colbert and search code run end to end
without downloading a model.

The stub maps each word of a fixed vocabulary to one orthogonal unit vector
and drops every other word (a text with no vocabulary word keeps a single
out-of-vocabulary token). A query therefore scores a document exactly:
MaxSim is the fraction of query tokens whose vocabulary word the document
shares.
"""

from __future__ import annotations

import re
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from asago_policy_mapper.extract.index import RiskIndex
from asago_policy_mapper.extract.models import ScoredCandidate

_COLBERT_VOCAB = {
    "bias": np.array([1.0, 0.0, 0.0, 0.0, 0.0]),
    "data": np.array([0.0, 1.0, 0.0, 0.0, 0.0]),
    "privacy": np.array([0.0, 0.0, 1.0, 0.0, 0.0]),
    "safety": np.array([0.0, 0.0, 0.0, 1.0, 0.0]),
}
_COLBERT_OOV = np.array([0.0, 0.0, 0.0, 0.0, 1.0])

# The stub scales every vector it returns. The asserted scores stay exact
# only while search_colbert normalizes query tokens itself.
_COLBERT_SCALE = 2.0


def _colbert_token_vecs(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_COLBERT_VOCAB[w] for w in words if w in _COLBERT_VOCAB] or [_COLBERT_OOV]


class _StubColBERT:
    """Stands in for SentenceTransformer over the stub vocabulary."""

    SCALE = _COLBERT_SCALE

    def encode(self, texts, output_value="sentence_embeddings", show_progress_bar=None, batch_size=None):
        assert output_value == "token_embeddings", "ColBERT search needs token-level embeddings"
        if isinstance(texts, str):
            return [self.SCALE * v for v in _colbert_token_vecs(texts)]
        return [[self.SCALE * v for v in _colbert_token_vecs(t)] for t in texts]


class _TorchLikeTensor:
    """Mimics the torch tensor _load_colbert and search_colbert may receive."""

    def __init__(self, arr):
        self._arr = arr

    def cpu(self):
        return self

    def float(self):
        return self

    def numpy(self):
        return self._arr


class _TorchStubColBERT(_StubColBERT):
    """Returns torch-like tensors instead of numpy arrays."""

    def encode(self, texts, output_value="sentence_embeddings", show_progress_bar=None, batch_size=None):
        assert output_value == "token_embeddings"
        if isinstance(texts, str):
            return _TorchLikeTensor(np.array([self.SCALE * v for v in _colbert_token_vecs(texts)], dtype=np.float32))
        return [
            _TorchLikeTensor(np.array([self.SCALE * v for v in _colbert_token_vecs(t)], dtype=np.float32))
            for t in texts
        ]


def _make_risk(id, name, description):
    return SimpleNamespace(
        id=id,
        name=name,
        description=description,
        concern="",
        risk_type="",
        isDefinedByTaxonomy="test-taxonomy",
        isPartOf="",
    )


COLBERT_RISKS = [
    _make_risk("R-001", "Model Bias", "systematic bias in model outputs"),
    _make_risk("R-002", "Data Poisoning", "corrupt data in training sets"),
    _make_risk("R-003", "Privacy Violation", "unauthorized privacy data collection"),
    _make_risk("R-004", "Governance", "miscellaneous governance wording"),
]

# A fifth risk that BM25 reaches at rank 2 but ColBERT never scores, for the
# rescue-rank boundary in _hybrid_search_colbert.
RESCUE_RISKS = COLBERT_RISKS + [_make_risk("R-005", "Oversight", "regular oversight reviews and audits")]


def _colbert_index(risks, stub=_StubColBERT):
    with patch(
        "asago_policy_mapper.extract.index.SentenceTransformer",
        lambda model_name, model_kwargs=None: stub(),
    ):
        return RiskIndex(risks, colbert_model="stub-colbert")


# --- search_colbert tests ---


def test_search_colbert_ranks_by_token_overlap():
    index = _colbert_index(COLBERT_RISKS)

    # "data privacy" (two tokens) fully overlaps R-003 and halves on R-002;
    # R-001 and R-004 share no vocabulary word and are dropped at score 0.
    results = index.search_colbert("data privacy", top_k=10)
    assert [c.risk_id for c in results] == ["R-003", "R-002"]
    assert [c.cross_encoder_score for c in results] == pytest.approx([1.0, 0.5])
    assert all(c.embedding_distance == 0.0 for c in results)

    top = index.search_colbert("bias", top_k=10)
    assert [c.risk_id for c in top] == ["R-001"]
    assert top[0].cross_encoder_score == pytest.approx(1.0)


def test_search_colbert_carries_risk_metadata():
    index = _colbert_index(COLBERT_RISKS)

    results = index.search_colbert("bias", top_k=10)

    assert results[0].risk_name == "Model Bias"
    assert results[0].risk_description == "systematic bias in model outputs"


def test_search_colbert_respects_top_k():
    index = _colbert_index(COLBERT_RISKS)

    results = index.search_colbert("data privacy", top_k=1)

    assert [c.risk_id for c in results] == ["R-003"]


def test_search_colbert_no_overlap_returns_empty():
    index = _colbert_index(COLBERT_RISKS)

    # "safety" is stub vocabulary but no indexed risk contains it.
    assert index.search_colbert("safety", top_k=10) == []


def test_search_colbert_accepts_torch_tensors():
    index = _colbert_index(COLBERT_RISKS, stub=_TorchStubColBERT)

    results = index.search_colbert("data privacy", top_k=10)

    assert [c.risk_id for c in results] == ["R-003", "R-002"]
    assert [c.cross_encoder_score for c in results] == pytest.approx([1.0, 0.5])


def test_search_colbert_without_colbert_returns_empty():
    with (
        patch("asago_policy_mapper.extract.index._load_bi_encoder", return_value=(None, None, None)),
        patch("asago_policy_mapper.extract.index._load_cross_encoder", return_value=(None, None, False, False)),
    ):
        index = RiskIndex(COLBERT_RISKS)

    assert index.has_colbert is False
    assert index.search_colbert("bias", top_k=10) == []


# --- _hybrid_search_colbert tests (reached through hybrid_search) ---


def _stub_bm25(monkeypatch, index, risk_ids):
    """Fix the BM25 side of the fusion so only fusion logic is under test.

    _hybrid_search_colbert calls search_bm25 itself, so the stub replaces it
    on the index instance. Each candidate's bm25_rank matches its list
    position, as search_bm25 would set it; the rescue loop reads that field.
    """
    candidates = [
        ScoredCandidate(risk_id=rid, risk_name="x", risk_description="y", bm25_rank=rank)
        for rank, rid in enumerate(risk_ids, start=1)
    ]
    monkeypatch.setattr(index, "search_bm25", lambda text, top_k=100: list(candidates))


def test_hybrid_search_colbert_fuses_bm25_and_colbert(monkeypatch):
    index = _colbert_index(COLBERT_RISKS)
    # Only R-003 comes back from the BM25 side, at rank 1.
    _stub_bm25(monkeypatch, index, ["R-003"])

    results = index.hybrid_search("data privacy")
    assert [c.risk_id for c in results] == ["R-003", "R-002"]
    # R-003: rank 1 in both lists; R-002: rank 2 in the ColBERT list only.
    assert [c.rrf_score for c in results] == pytest.approx([2 / 61, 1 / 62])
    assert [c.cross_encoder_score for c in results] == pytest.approx([1.0, 0.5])
    assert [c.bm25_rank for c in results] == [1, 0]


def test_hybrid_search_colbert_respects_top_k(monkeypatch):
    index = _colbert_index(COLBERT_RISKS)
    _stub_bm25(monkeypatch, index, ["R-003"])

    results = index.hybrid_search("data privacy", top_k=1)

    assert [c.risk_id for c in results] == ["R-003"]


def test_hybrid_search_colbert_no_candidates_returns_empty():
    index = _colbert_index(COLBERT_RISKS)

    # Neither retriever finds "safety": the empty-both-lists early return.
    assert index.hybrid_search("safety") == []


def test_hybrid_search_colbert_bm25_rescue(monkeypatch):
    index = _colbert_index(RESCUE_RISKS)
    query = "bias governance oversight"

    # BM25 ranks the governance and oversight risks above the bias risk;
    # ColBERT matches only the bias token, so R-001 is the sole fused
    # candidate at top_k=1.
    _stub_bm25(monkeypatch, index, ["R-004", "R-005", "R-001"])

    without_rescue = index.hybrid_search(query, top_k=1, bm25_rescue_rank=0)
    assert [c.risk_id for c in without_rescue] == ["R-001"]
    assert without_rescue[0].rrf_score == pytest.approx(1 / 61 + 1 / 63)
    assert without_rescue[0].cross_encoder_score == pytest.approx(1.0)

    # rescue_rank 1 admits the BM25 rank-1 risk, rescue_rank 2 also the
    # rank-2 one; rescued candidates keep their BM25 rank, get the ColBERT
    # fallback score of 0.0 and their BM25-only RRF contribution.
    rescued_one = index.hybrid_search(query, top_k=1, bm25_rescue_rank=1)
    assert [c.risk_id for c in rescued_one] == ["R-001", "R-004"]
    assert rescued_one[1].rrf_score == pytest.approx(1 / 61)
    assert rescued_one[1].cross_encoder_score == 0.0
    assert rescued_one[1].bm25_rank == 1

    rescued_two = index.hybrid_search(query, top_k=1, bm25_rescue_rank=2)
    assert [c.risk_id for c in rescued_two] == ["R-001", "R-004", "R-005"]
    assert rescued_two[2].rrf_score == pytest.approx(1 / 62)
    assert rescued_two[2].cross_encoder_score == 0.0
    assert rescued_two[2].bm25_rank == 2
