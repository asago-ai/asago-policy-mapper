import re
from unittest.mock import MagicMock, patch

import httpx
import numpy as np
import pytest
from typer.testing import CliRunner

from asago_policy_mapper.cli import app
from asago_policy_mapper.extract.index import _load_cross_encoder, _RemoteCrossEncoder
from asago_policy_mapper.extract.models import RetrievalConfig

RERANK_URL = "http://reranker.example:8001/v1/rerank"

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _mock_client(mock_httpx_client_cls, payload):
    mock_client = MagicMock()
    mock_httpx_client_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_client.post.return_value = mock_response
    return mock_client, mock_response


@patch("httpx.Client")
def test_rerank_posts_to_rerank_endpoint(mock_httpx_client_cls):
    mock_client, _ = _mock_client(mock_httpx_client_cls, {"results": [{"index": 0, "relevance_score": 0.9}]})
    encoder = _RemoteCrossEncoder(RERANK_URL, api_type="rerank", model_name="qwen3-reranker-4b")

    encoder.predict([("risk desc", "chunk text")])

    mock_client.post.assert_called_once()
    assert mock_client.post.call_args.args[0] == "http://reranker.example:8001/v1/rerank"


@patch("httpx.Client")
def test_rerank_payload_uses_configured_model_name(mock_httpx_client_cls):
    mock_client, _ = _mock_client(
        mock_httpx_client_cls,
        {"results": [{"index": 1, "relevance_score": 0.8}, {"index": 0, "relevance_score": 0.1}]},
    )
    encoder = _RemoteCrossEncoder(RERANK_URL, api_type="rerank", model_name="qwen3-reranker-4b")

    encoder.predict([("risk A", "the chunk"), ("risk B", "the chunk")])

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload == {"model": "qwen3-reranker-4b", "query": "the chunk", "documents": ["risk A", "risk B"]}


@patch("httpx.Client")
def test_rerank_scores_follow_input_order(mock_httpx_client_cls):
    _mock_client(
        mock_httpx_client_cls,
        {
            "results": [
                {"index": 2, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.40},
                {"index": 1, "relevance_score": 0.01},
            ]
        },
    )
    encoder = _RemoteCrossEncoder(RERANK_URL, api_type="rerank", model_name="m")

    scores = encoder.predict([("a", "q"), ("b", "q"), ("c", "q")])

    np.testing.assert_allclose(scores, [0.40, 0.01, 0.95])


@patch("httpx.Client")
def test_rerank_http_error_raises(mock_httpx_client_cls):
    _, mock_response = _mock_client(mock_httpx_client_cls, {})
    request = httpx.Request("POST", RERANK_URL)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=request, response=httpx.Response(404, request=request)
    )
    encoder = _RemoteCrossEncoder(RERANK_URL, api_type="rerank", model_name="m")

    with pytest.raises(httpx.HTTPStatusError):
        encoder.predict([("a", "q"), ("b", "q")])


@patch("httpx.Client")
def test_rerank_incomplete_results_raise(mock_httpx_client_cls):
    _mock_client(mock_httpx_client_cls, {"results": [{"index": 0, "relevance_score": 0.5}]})
    encoder = _RemoteCrossEncoder(RERANK_URL, api_type="rerank", model_name="m")

    with pytest.raises(ValueError, match="rerank"):
        encoder.predict([("a", "q"), ("b", "q")])


@patch("httpx.Client")
def test_rerank_empty_pairs_make_no_request(mock_httpx_client_cls):
    mock_client = MagicMock()
    mock_httpx_client_cls.return_value = mock_client
    encoder = _RemoteCrossEncoder(RERANK_URL, api_type="rerank", model_name="m")

    assert encoder.predict([]).shape == (0,)
    mock_client.post.assert_not_called()


@patch("httpx.Client")
def test_score_type_derives_model_name_from_url_without_override(mock_httpx_client_cls):
    mock_client, _ = _mock_client(mock_httpx_client_cls, {"data": [{"index": 0, "score": 0.5}]})
    encoder = _RemoteCrossEncoder("https://gte-reranker-model-serving.apps.example.com/v1/score")

    encoder.predict([("a", "q")])

    assert mock_client.post.call_args.args[0] == "https://gte-reranker-model-serving.apps.example.com/v1/score"
    assert mock_client.post.call_args.kwargs["json"]["model"] == "gte-reranker"


@patch("httpx.Client")
def test_score_type_honours_model_name_override(mock_httpx_client_cls):
    mock_client, _ = _mock_client(mock_httpx_client_cls, {"data": [{"index": 0, "score": 0.5}]})
    encoder = _RemoteCrossEncoder("http://reranker.example:8001/v1/score", model_name="qwen3-reranker-4b")

    encoder.predict([("a", "q")])

    assert mock_client.post.call_args.kwargs["json"]["model"] == "qwen3-reranker-4b"


def test_unknown_api_type_rejected():
    with pytest.raises(ValueError, match="api_type"):
        _RemoteCrossEncoder(RERANK_URL, api_type="bogus")


@patch("httpx.Client")
def test_load_cross_encoder_builds_rerank_client_with_model_name(mock_httpx_client_cls):
    _mock_client(mock_httpx_client_cls, {"results": [{"index": 0, "relevance_score": 0.7}]})

    local, remote, apply_sigmoid, is_nli = _load_cross_encoder(
        RERANK_URL, "rerank", cross_encoder_model_name="qwen3-reranker-4b"
    )

    assert local is None
    assert isinstance(remote, _RemoteCrossEncoder)
    assert (apply_sigmoid, is_nli) == (False, False)
    remote.predict([("a", "q")])
    assert mock_httpx_client_cls.return_value.post.call_args.kwargs["json"]["model"] == "qwen3-reranker-4b"


def test_retrieval_config_records_cross_encoder_type_and_model_name():
    meta = RetrievalConfig(
        cross_encoder_model=RERANK_URL,
        cross_encoder_type="rerank",
        cross_encoder_model_name="qwen3-reranker-4b",
    ).to_metadata()

    assert meta["cross_encoder_type"] == "rerank"
    assert meta["cross_encoder_model_name"] == "qwen3-reranker-4b"


def test_retrieval_config_model_name_defaults_to_none():
    assert RetrievalConfig().to_metadata()["cross_encoder_model_name"] is None


def test_extract_help_lists_rerank_and_model_name_option():
    result = runner.invoke(app, ["extract", "--help"], env={"COLUMNS": "250", "LINES": "50"})

    assert result.exit_code == 0
    output = _strip_ansi(result.stdout)
    assert "--cross-encoder-model-name" in output
    assert "POLICY_MAPPER_CROSS_ENCODER_MODEL_NAME" in output
    assert "rerank" in output


def _invoke_extract_capturing_retrieval(tmp_path, extra_args=(), env=None):
    policy = tmp_path / "policy.txt"
    policy.write_text("test policy")
    captured: dict = {}

    def fake_run_extraction(**kwargs):
        captured["retrieval"] = kwargs["retrieval"]
        raise RuntimeError("stop after capture")

    nexus = MagicMock()
    nexus.return_value.get_all_risks.return_value = []
    with (
        patch("ai_atlas_nexus.AIAtlasNexus", nexus),
        patch("asago_policy_mapper.extract.pipeline.run_extraction", fake_run_extraction),
    ):
        runner.invoke(
            app,
            [
                "extract",
                str(policy),
                "-o",
                str(tmp_path / "out"),
                "--no-judge",
                "--no-grounding",
                "--no-expand-siblings",
                "--no-query-gen",
                "--cross-encoder-model",
                RERANK_URL,
                "--cross-encoder-type",
                "rerank",
                *extra_args,
            ],
            env=env or {},
        )
    return captured["retrieval"]


def test_cli_cross_encoder_model_name_flag_reaches_retrieval_config(tmp_path):
    retrieval = _invoke_extract_capturing_retrieval(
        tmp_path, extra_args=["--cross-encoder-model-name", "qwen3-reranker-4b"]
    )

    assert retrieval.cross_encoder_type == "rerank"
    assert retrieval.cross_encoder_model_name == "qwen3-reranker-4b"


def test_cli_cross_encoder_model_name_env_reaches_retrieval_config(tmp_path):
    retrieval = _invoke_extract_capturing_retrieval(
        tmp_path, env={"POLICY_MAPPER_CROSS_ENCODER_MODEL_NAME": "qwen3-reranker-4b"}
    )

    assert retrieval.cross_encoder_model_name == "qwen3-reranker-4b"


def test_cli_cross_encoder_model_name_defaults_to_none(tmp_path):
    assert _invoke_extract_capturing_retrieval(tmp_path).cross_encoder_model_name is None


def test_run_extraction_passes_cross_encoder_model_name_to_index(mock_config, tmp_path):
    from asago_policy_mapper.extract.pipeline import run_extraction

    doc = tmp_path / "test.txt"
    doc.write_text("AI systems must protect personal data.")
    risk = MagicMock(id="R-1", description="d", concern="")
    risk.name = "n"

    with patch("asago_policy_mapper.extract.pipeline.RiskIndex", side_effect=RuntimeError("stop")) as index_cls:
        with pytest.raises(RuntimeError, match="stop"):
            run_extraction(
                documents=[doc],
                client=MagicMock(),
                config=mock_config,
                risks=[risk],
                retrieval=RetrievalConfig(
                    cross_encoder_model=RERANK_URL,
                    cross_encoder_type="rerank",
                    cross_encoder_model_name="qwen3-reranker-4b",
                    query_gen=False,
                ),
                ocr=False,
            )

    assert index_cls.call_args.kwargs["cross_encoder_model_name"] == "qwen3-reranker-4b"
