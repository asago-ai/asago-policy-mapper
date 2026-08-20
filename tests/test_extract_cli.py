import re
import tempfile

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
