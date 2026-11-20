"""CLI tests for the annotate command.

The unit tests in test_annotate.py cover prepare_annotation_data and its
helpers, but the annotate command itself was untested: no test exercised
run-dir resolution, output echo, the ground-truth comparison path or the
error exit. These tests run the real Typer command through CliRunner with
plain-text documents, so docling and the embedding models never load.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from asago_policy_mapper.cli import app

runner = CliRunner()


def _write_policy(tmp_path: Path) -> Path:
    policy = tmp_path / "policy.txt"
    policy.write_text(
        "Section 1: Introduction\n\n"
        "AI systems must be transparent and accountable.\n"
        "Organizations should ensure fairness in all AI deployments.\n\n"
        "Section 2: Data Privacy\n\n"
        "Personal data must be protected according to regulations.\n"
    )
    return policy


def _extraction_data() -> dict:
    return {
        "risks": [
            {
                "risk_id": "risk-transparency",
                "risk_name": "Lack of Transparency",
                "risk_description": "AI systems not transparent",
                "taxonomy": "test-taxonomy",
                "confidence": 0.95,
                "grounding_confidence": "high",
                "evidence": [
                    {
                        "text": "AI systems must be transparent and accountable.",
                        "document": "policy.txt",
                        "chunk_index": 0,
                    }
                ],
            },
            {
                "risk_id": "risk-imagined",
                "risk_name": "Imagined Risk",
                "risk_description": "A risk with no support in the document",
                "taxonomy": "test-taxonomy",
                "confidence": 0.4,
                "grounding_confidence": "low",
                "evidence": [
                    {
                        "text": "This sentence appears nowhere in the policy document.",
                        "document": "policy.txt",
                        "chunk_index": 0,
                    }
                ],
            },
        ],
        "metadata": {"model": "test-model"},
    }


def _write_run_dir(tmp_path: Path, extraction_data: dict, suffix: str = ".json") -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    payload = json.dumps(extraction_data) if suffix == ".json" else yaml.safe_dump(extraction_data)
    (run_dir / f"risk-extraction{suffix}").write_text(payload)
    return run_dir


def test_annotate_json_run_writes_report_and_echoes_summary(tmp_path):
    policy = _write_policy(tmp_path)
    run_dir = _write_run_dir(tmp_path, _extraction_data())

    result = runner.invoke(app, ["annotate", str(run_dir), str(policy)])

    assert result.exit_code == 0
    assert "Annotation view: 2 risks, 2 evidence spans" in result.stdout
    assert "Matched: 1, Unmatched: 1" in result.stdout
    html = run_dir / "risk-annotation.html"
    assert html.exists()
    # The template placeholder is replaced by the serialized annotation data.
    content = html.read_text()
    assert "__REPORT_DATA__" not in content
    assert "risk-transparency" in content


def test_annotate_yaml_run_uses_yaml_loader(tmp_path):
    policy = _write_policy(tmp_path)
    run_dir = _write_run_dir(tmp_path, _extraction_data(), suffix=".yaml")

    result = runner.invoke(app, ["annotate", str(run_dir), str(policy)])

    assert result.exit_code == 0
    assert "Annotation view: 2 risks, 2 evidence spans" in result.stdout
    assert (run_dir / "risk-annotation.html").exists()


def test_annotate_prefers_json_over_yaml(tmp_path):
    policy = _write_policy(tmp_path)
    run_dir = _write_run_dir(tmp_path, _extraction_data())
    # A yaml file that would parse to different risk ids.
    other = _extraction_data()
    other["risks"] = [other["risks"][0]]
    (run_dir / "risk-extraction.yaml").write_text(yaml.safe_dump(other))

    result = runner.invoke(app, ["annotate", str(run_dir), str(policy)])

    assert result.exit_code == 0
    # The JSON file (2 risks) wins over the yaml file (1 risk).
    assert "Annotation view: 2 risks" in result.stdout


def test_annotate_ground_truth_echoes_metrics_and_creates_revised_dir(tmp_path):
    policy = _write_policy(tmp_path)
    run_dir = _write_run_dir(tmp_path, _extraction_data())
    gt = tmp_path / "gt.yaml"
    gt.write_text("risk_ids:\n  - risk-transparency\n  - risk-not-extracted\n")

    result = runner.invoke(app, ["annotate", str(run_dir), str(policy), "--ground-truth", str(gt)])

    assert result.exit_code == 0
    # 1 matched (risk-transparency), 1 spurious (risk-imagined), 1 missing.
    assert "GT: 1 matched, 1 spurious, 1 missing" in result.stdout
    assert "P=0.500 R=0.500 F1=0.500" in result.stdout
    assert f"Save revised GT to: {run_dir / 'revised_gt'}" in result.stdout
    assert (run_dir / "revised_gt").is_dir()


def test_annotate_missing_extraction_exits_with_error(tmp_path):
    policy = _write_policy(tmp_path)
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = runner.invoke(app, ["annotate", str(empty_dir), str(policy)])

    assert result.exit_code == 1
    assert "no risk-extraction.json or .yaml found" in result.stderr


def test_annotate_ocr_and_chunk_options_reach_annotation_data(tmp_path, monkeypatch):
    """--ocr and --chunk-max-tokens are forwarded to prepare_annotation_data.

    The command imports prepare_annotation_data inside its body, so the spy
    patches the module it resolves from, not the CLI namespace.
    """
    policy = _write_policy(tmp_path)
    run_dir = _write_run_dir(tmp_path, _extraction_data())
    captured = {}

    from asago_policy_mapper.extract.annotate import prepare_annotation_data as real_prepare

    def spy(extraction_data, source_document, **kwargs):
        captured.update(kwargs)
        return real_prepare(extraction_data, source_document, **kwargs)

    monkeypatch.setattr("asago_policy_mapper.extract.annotate.prepare_annotation_data", spy)

    result = runner.invoke(
        app,
        ["annotate", str(run_dir), str(policy), "--ocr", "--chunk-max-tokens", "256"],
    )

    assert result.exit_code == 0
    assert captured["ocr"] is True
    assert captured["chunk_max_tokens"] == 256
    assert (run_dir / "risk-annotation.html").exists()
