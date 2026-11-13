import json

import yaml
from typer.testing import CliRunner

from asago_policy_mapper.cli import app

runner = CliRunner()

SAMPLE_EXTRACTION = {
    "version": "0.2",
    "risks": [
        {
            "risk_id": "atlas-bias",
            "risk_name": "Bias",
            "risk_description": "",
            "confidence": 0.9,
            "grounding_confidence": "high",
            "accepted_by": "threshold",
            "evidence": [],
            "scores": {"bm25_rank": 1, "embedding_distance": 0.1, "cross_encoder_score": 0.9, "rrf_score": 0.5},
        },
        {
            "risk_id": "atlas-privacy",
            "risk_name": "Privacy",
            "risk_description": "",
            "confidence": 0.8,
            "grounding_confidence": "high",
            "accepted_by": "threshold",
            "evidence": [],
            "scores": {"bm25_rank": 2, "embedding_distance": 0.2, "cross_encoder_score": 0.8, "rrf_score": 0.4},
        },
    ],
    "source_documents": ["policy.md"],
    "retrieval_stats": {
        "total_chunks": 10,
        "total_candidates_retrieved": 50,
        "auto_accepted": 2,
        "llm_judged": 0,
        "grounding_filtered": 0,
    },
}


def test_eval_command_with_explicit_ground_truth(tmp_path):
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()
    (run_dir / "risk-extraction.json").write_text(json.dumps(SAMPLE_EXTRACTION))

    gt = tmp_path / "gt.yaml"
    gt.write_text("risk_ids:\n  - atlas-bias\n  - atlas-privacy\n")

    result = runner.invoke(app, ["eval", str(run_dir), "--ground-truth", str(gt)])
    assert result.exit_code == 0
    assert "precision" in result.stdout.lower()
    assert "recall" in result.stdout.lower()

    eval_json = run_dir / "eval.json"
    assert eval_json.exists()
    data = json.loads(eval_json.read_text())
    assert data["precision"] == 1.0
    assert data["recall"] == 1.0
    assert data["pass"] is True


def test_eval_command_missing_extraction(tmp_path):
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir()

    gt = tmp_path / "gt.yaml"
    gt.write_text("risk_ids:\n  - atlas-bias\n")

    result = runner.invoke(app, ["eval", str(run_dir), "--ground-truth", str(gt)])
    assert result.exit_code == 1


def test_eval_command_uses_yaml_when_json_missing(tmp_path):
    run_dir = tmp_path / "yaml-run"
    run_dir.mkdir()
    (run_dir / "risk-extraction.yaml").write_text(yaml.dump(SAMPLE_EXTRACTION))

    gt = tmp_path / "gt.yaml"
    gt.write_text("risk_ids:\n  - atlas-bias\n  - atlas-privacy\n")

    result = runner.invoke(app, ["eval", str(run_dir), "--ground-truth", str(gt)])
    # Pins the known yaml-only bug: evaluate_extraction json.loads the yaml
    # sidecar, so a yaml-only run directory fails with a decode error rather
    # than evaluating. The command exits 1 and writes no eval.json.
    assert result.exit_code == 1
    assert isinstance(result.exception, json.JSONDecodeError)
    assert not (run_dir / "eval.json").exists()


def test_eval_command_ground_truth_not_found(tmp_path):
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()
    (run_dir / "risk-extraction.json").write_text(json.dumps(SAMPLE_EXTRACTION))

    result = runner.invoke(app, ["eval", str(run_dir), "--ground-truth", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 1
    assert "ground truth not found" in result.output


def test_eval_command_reports_missing_and_spurious(tmp_path):
    run_dir = tmp_path / "partial-run"
    run_dir.mkdir()
    (run_dir / "risk-extraction.json").write_text(json.dumps(SAMPLE_EXTRACTION))

    gt = tmp_path / "gt.yaml"
    gt.write_text("risk_ids:\n  - atlas-bias\n  - atlas-safety\n")

    result = runner.invoke(app, ["eval", str(run_dir), "--ground-truth", str(gt)])
    assert result.exit_code == 0
    assert "FAIL" in result.stdout
    assert "Missing:   atlas-safety" in result.stdout
    assert "Spurious:  atlas-privacy" in result.stdout


def test_eval_command_json_and_yaml_both_updated(tmp_path):
    run_dir = tmp_path / "both-run"
    run_dir.mkdir()
    (run_dir / "risk-extraction.json").write_text(json.dumps(SAMPLE_EXTRACTION))
    (run_dir / "risk-extraction.yaml").write_text(yaml.dump(SAMPLE_EXTRACTION))

    gt = tmp_path / "gt.yaml"
    gt.write_text("risk_ids:\n  - atlas-bias\n  - atlas-privacy\n")

    result = runner.invoke(app, ["eval", str(run_dir), "--ground-truth", str(gt)])
    assert result.exit_code == 0
    updated_json = json.loads((run_dir / "risk-extraction.json").read_text())
    updated_yaml = yaml.safe_load((run_dir / "risk-extraction.yaml").read_text())
    assert updated_json["eval"]["pass"] is True
    assert updated_yaml["eval"]["pass"] is True
    assert (run_dir / "risk-extraction.html").exists()
