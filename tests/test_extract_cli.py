import logging
import re
import tempfile

import pytest
from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk
from typer.testing import CliRunner

from asago_policy_mapper.cli import app

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_extract_command_exists():
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    assert "Extract risks" in result.stdout or "extract" in result.stdout.lower()


def test_extract_missing_base_url():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("test policy")
        f.flush()
        result = runner.invoke(
            app,
            [
                "extract",
                f.name,
                "-o",
                "/tmp/test-output",
                "--nexus-base-dir",
                "/tmp/nexus",
            ],
            env={"POLICY_MAPPER_BASE_URL": "", "POLICY_MAPPER_MODEL": ""},
        )
    assert result.exit_code != 0


def test_extract_nonexistent_file():
    result = runner.invoke(
        app,
        [
            "extract",
            "/nonexistent/policy.pdf",
            "-o",
            "/tmp/test-output",
            "--base-url",
            "http://localhost:8000/v1",
            "--model",
            "test",
            "--nexus-base-dir",
            "/tmp/nexus",
        ],
    )
    assert result.exit_code != 0


def test_extract_custom_taxonomy_flag_in_help():
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    assert "--custom-taxonomy" in _strip_ansi(result.stdout)


def test_extract_output_token_parameter_flag_in_help():
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    output = _strip_ansi(result.stdout)
    # Typer's rich help renderer truncates long option names and values at the
    # default terminal width.
    assert "--output-token-pa" in output
    assert "max_completion_to" in output


def test_extract_service_tier_flag_in_help():
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    output = _strip_ansi(result.stdout)
    assert "--service-tier" in output


def test_extract_check_risk_text_flag_in_help():
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0
    assert "--check-risk-text" in _strip_ansi(result.stdout)


class _StopAfterRiskLoad(Exception):
    pass


@pytest.mark.parametrize("check_risk_text", [True, False])
def test_extract_check_risk_text_warnings_only_when_enabled(monkeypatch, tmp_path, caplog, check_risk_text):
    risks = [
        Risk(id="ok", name="ok", description="Complete sentence.", isDefinedByTaxonomy="test", type="Risk"),
        Risk(id="cut", name="cut", description="This sentence stops in the", isDefinedByTaxonomy="test", type="Risk"),
        # Truncated upstream text as shipped in the Nexus CREDO UCF catalog.
        Risk(
            id="credo-risk-018",
            name="AI deception",
            description="The AI system may misrepresent its own capabilities or limitations, "
            "potentially leading to misplaced trust or inappropriate",
            isDefinedByTaxonomy="credo-ucf",
            type="Risk",
        ),
    ]
    pipeline_risks: list[Risk] = []

    class FakeNexus:
        def __init__(self, base_dir=None):
            pass

        def get_all_risks(self):
            return risks

    def stop(**kwargs):
        pipeline_risks.extend(kwargs["risks"])
        raise _StopAfterRiskLoad

    monkeypatch.setattr("ai_atlas_nexus.AIAtlasNexus", FakeNexus)
    monkeypatch.setattr("asago_policy_mapper.extract.pipeline.run_extraction", stop)
    policy = tmp_path / "policy.txt"
    policy.write_text("test policy")
    args = ["extract", str(policy), "-o", str(tmp_path / "out"), "--nexus-base-dir", str(tmp_path)]
    args += ["--no-judge", "--no-grounding", "--no-query-gen", "--no-expand-siblings"]
    if check_risk_text:
        args.append("--check-risk-text")

    with caplog.at_level(logging.WARNING, logger="asago_policy_mapper.taxonomy"):
        result = runner.invoke(app, args)

    assert isinstance(result.exception, _StopAfterRiskLoad)
    # The restored CREDO text, not the truncated upstream one, reaches the pipeline.
    descriptions = {r.id: r.description for r in pipeline_risks}
    assert descriptions["credo-risk-018"] == (
        "The AI system may misrepresent its own capabilities or limitations, "
        "potentially leading to misplaced trust or inappropriate use."
    )
    if check_risk_text:
        assert "Risk 'cut' description lacks closing punctuation" in caplog.text
        assert "'ok'" not in caplog.text
        assert "credo-risk-018" not in caplog.text
        assert "Risk text check: 1 of 3 risk descriptions lack closing punctuation: cut" in result.output
    else:
        assert "lacks closing punctuation" not in caplog.text
        assert "Risk text check" not in result.output


def test_extract_invalid_custom_taxonomy():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("test policy")
        f.flush()
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as bad_yaml:
            bad_yaml.write("not_a_taxonomy: true\n")
            bad_yaml.flush()
            result = runner.invoke(
                app,
                [
                    "extract",
                    f.name,
                    "-o",
                    "/tmp/test-output",
                    "--base-url",
                    "http://localhost:8000/v1",
                    "--model",
                    "test",
                    "--nexus-base-dir",
                    "/tmp/nexus",
                    "--custom-taxonomy",
                    bad_yaml.name,
                    "--no-judge",
                    "--no-grounding",
                    "--no-expand-siblings",
                    "--no-query-gen",
                ],
                env={"POLICY_MAPPER_BASE_URL": "", "POLICY_MAPPER_MODEL": ""},
            )
    assert result.exit_code != 0
    output = _strip_ansi(result.stdout + (result.stderr or ""))
    assert "missing the 'taxonomy' block" in output


def test_eval_command_exists():
    result = runner.invoke(app, ["eval", "--help"])
    assert result.exit_code == 0
    assert "Evaluate" in result.stdout or "eval" in result.stdout.lower()
