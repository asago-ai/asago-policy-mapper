import json
import logging
import re
import tempfile

import pytest
import typer
import yaml
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


# (option name, envvar) pairs documented in README/.env usage. A rename or an
# accidentally dropped envvar silently severs .env-based configuration: the
# option falls back to its default with no error, which is hard to notice.
_ENVVAR_OPTIONS = [
    ("base_url", "POLICY_MAPPER_BASE_URL"),
    ("nexus_base_dir", "NEXUS_BASE_DIR"),
    ("model", "POLICY_MAPPER_MODEL"),
    ("api_key", "POLICY_MAPPER_API_KEY"),
    ("max_tokens", "POLICY_MAPPER_MAX_OUTPUT_TOKENS"),
    ("output_token_parameter", "POLICY_MAPPER_OUTPUT_TOKEN_PARAMETER"),
    ("service_tier", "POLICY_MAPPER_SERVICE_TIER"),
    ("bi_encoder_model", "POLICY_MAPPER_BI_ENCODER_MODEL"),
    ("bi_encoder_api_key", "POLICY_MAPPER_BI_ENCODER_API_KEY"),
    ("bi_encoder_model_name", "POLICY_MAPPER_BI_ENCODER_MODEL_NAME"),
    ("cross_encoder_model", "POLICY_MAPPER_CROSS_ENCODER_MODEL"),
    ("cross_encoder_model_name", "POLICY_MAPPER_CROSS_ENCODER_MODEL_NAME"),
]


@pytest.mark.parametrize("option_name,envvar", _ENVVAR_OPTIONS)
def test_extract_envvar_attached_to_option(option_name, envvar):
    from typer.main import get_command

    command = get_command(app).commands["extract"]
    params = {p.name: p for p in command.params}
    assert option_name in params, f"option --{option_name} no longer exists"
    registered = params[option_name].envvar
    if isinstance(registered, str):
        registered = [registered]
    assert envvar in (registered or []), f"--{option_name} lost its envvar (expected {envvar})"


def test_cli_configures_logging():
    """The CLI attaches a root handler at INFO so stage logs are visible.

    Without this, the pipeline's logger.info calls are swallowed (Python's
    last-resort handler only prints WARNING+). basicConfig is a no-op when
    logging is already configured, so the test resets the root logger first
    and restores it afterwards.
    """
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    root.handlers = []
    root.setLevel(logging.WARNING)
    try:
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
            ],
        )
        assert result.exit_code != 0
        assert root.level == logging.INFO
        assert root.handlers, "CLI should have attached a root logging handler"
    finally:
        root.handlers = saved_handlers
        root.setLevel(saved_level)


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
    args = ["extract", str(policy), "-o", str(tmp_path / "out")]
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


def test_extract_env_values_reach_llm_config(monkeypatch, tmp_path):
    """Env-provided service tier, output budget and parameter name reach LLMConfig.

    Regression test for the 2026-11-11 incident: the service tier was believed
    configured through the environment but the wiring was never verified
    end-to-end, so a silent override went unnoticed across several runs. This
    exercises the real CLI path: envvar resolution -> option -> LLMConfig ->
    the config object the pipeline receives.
    """
    captured = {}

    class FakeNexus:
        def __init__(self, base_dir=None):
            pass

        def get_all_risks(self):
            return [
                Risk(id="r1", name="r1", description="A risk.", isDefinedByTaxonomy="test", type="Risk"),
            ]

    def stop(**kwargs):
        captured["config"] = kwargs["config"]
        raise _StopAfterRiskLoad

    monkeypatch.setattr("ai_atlas_nexus.AIAtlasNexus", FakeNexus)
    monkeypatch.setattr("asago_policy_mapper.extract.pipeline.run_extraction", stop)
    policy = tmp_path / "policy.txt"
    policy.write_text("test policy")
    result = runner.invoke(
        app,
        [
            "extract",
            str(policy),
            "-o",
            str(tmp_path / "out"),
            "--no-judge",
            "--no-grounding",
            "--no-expand-siblings",
        ],
        env={
            "POLICY_MAPPER_BASE_URL": "http://localhost:8000/v1",
            "POLICY_MAPPER_MODEL": "test-model",
            "POLICY_MAPPER_MAX_OUTPUT_TOKENS": "4096",
            "POLICY_MAPPER_OUTPUT_TOKEN_PARAMETER": "max_completion_tokens",
            "POLICY_MAPPER_SERVICE_TIER": "default",
        },
    )

    assert isinstance(result.exception, _StopAfterRiskLoad)
    config = captured["config"]
    assert config.service_tier == "default"
    assert config.max_tokens == 4096
    assert config.output_token_parameter == "max_completion_tokens"
    assert config.base_url == "http://localhost:8000/v1"
    assert config.model == "test-model"


def test_extract_blank_nexus_base_dir_behaves_like_unset(monkeypatch, tmp_path):
    """A blank --nexus-base-dir reaches the catalog and both mitigation loaders as None.

    Regression test for a normalization split: the CLI normalized '' for the
    catalog (``AIAtlasNexus(base_dir=None)``) but passed the raw '' to the
    mitigation loaders, which resolved relative ``src/ai_atlas_nexus/...``
    paths against the CWD — a package catalog with CWD-relative mitigation
    data. Blank must behave exactly like unset for every consumer. (The test
    drives the option, not the envvar: click treats an empty NEXUS_BASE_DIR
    envvar as unset, so the option is the path that carries '' into the body.)
    """
    from unittest.mock import MagicMock, patch

    import asago_policy_mapper.extract.mitigations as mitigations_module

    received: dict = {}

    class FakeNexus:
        def __init__(self, base_dir=None):
            received["catalog_base_dir"] = base_dir

        def get_all_risks(self):
            return [Risk(id="r1", name="r1", description="A risk.", isDefinedByTaxonomy="test", type="Risk")]

    def fake_build_action_descriptions(nexus_base_dir=None, data_dir=None):
        received["action_descs"] = nexus_base_dir
        return {}

    def fake_build_risk_crossmap(nexus_base_dir=None):
        received["crossmap"] = nexus_base_dir
        return {}

    def fake_enrich(risks, index, descriptions=None, risk_crossmap=None, risk_threats=None, risk_consequences=None):
        pass

    def fake_run_extraction(**kwargs):
        result = MagicMock()
        result.risks = []
        result.token_usage = {}
        result.model_dump = lambda: {"risks": [], "retrieval_stats": {}}
        return result

    monkeypatch.setattr(mitigations_module, "build_action_descriptions", fake_build_action_descriptions)
    monkeypatch.setattr(mitigations_module, "build_risk_crossmap", fake_build_risk_crossmap)
    monkeypatch.setattr(mitigations_module, "enrich_with_mitigations", fake_enrich)

    policy = tmp_path / "policy.txt"
    policy.write_text("test policy")
    args = [
        str(policy),
        "-o",
        str(tmp_path / "out"),
        "--no-judge",
        "--no-grounding",
        "--no-query-gen",
        "--no-expand-siblings",
    ]

    with (
        patch("ai_atlas_nexus.AIAtlasNexus", FakeNexus),
        patch("asago_policy_mapper.extract.pipeline.run_extraction", fake_run_extraction),
    ):
        # An explicit empty option reaches the command body as '' (click treats
        # an empty *envvar* as unset, so the option is the path that carries it).
        result = runner.invoke(app, ["extract", *args, "--nexus-base-dir", ""])

    assert result.exit_code == 0, result.exception
    assert received["catalog_base_dir"] is None
    assert received["action_descs"] is None
    assert received["crossmap"] is None


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


# --- _validate_extract_options unit tests ---


def _validate_kwargs(tmp_path, **overrides):
    policy = tmp_path / "policy.txt"
    policy.write_text("test policy")
    kwargs = dict(
        output_format="json",
        policy_files=[policy],
        base_url="http://localhost:8000/v1",
        model="test-model",
        no_judge=False,
        no_grounding=False,
        expand_siblings=True,
        query_gen=False,
    )
    kwargs.update(overrides)
    return kwargs


def test_validate_extract_options_rejects_bad_output_format(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    with pytest.raises(typer.Exit) as excinfo:
        _validate_extract_options(**_validate_kwargs(tmp_path, output_format="xml"))
    assert excinfo.value.exit_code == 1


def test_validate_extract_options_rejects_missing_policy_file(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    with pytest.raises(typer.Exit) as excinfo:
        _validate_extract_options(**_validate_kwargs(tmp_path, policy_files=[tmp_path / "nonexistent.pdf"]))
    assert excinfo.value.exit_code == 1


def test_validate_extract_options_requires_llm_endpoint_when_needed(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    # Grounding on, so the run needs an LLM: missing base_url/model is fatal.
    with pytest.raises(typer.Exit) as excinfo:
        _validate_extract_options(**_validate_kwargs(tmp_path, base_url=None, model=None))
    assert excinfo.value.exit_code == 1


def test_validate_extract_options_allows_missing_endpoint_for_ir_only(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    # Pure IR run: no endpoint needed, needs_llm is False.
    assert (
        _validate_extract_options(
            **_validate_kwargs(
                tmp_path, base_url=None, model=None, no_judge=True, no_grounding=True, expand_siblings=False
            )
        )
        is False
    )


def test_validate_extract_options_query_gen_forces_llm(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    # The options alone would make an IR-only run; query generation forces an LLM.
    assert (
        _validate_extract_options(
            **_validate_kwargs(tmp_path, query_gen=True, no_judge=True, no_grounding=True, expand_siblings=False)
        )
        is True
    )


def test_validate_extract_options_ignores_nexus_base_dir(tmp_path):
    """The nexus override is optional; the validator no longer requires it."""
    from asago_policy_mapper.cli import _validate_extract_options

    # No nexus_base_dir parameter at all: validation passes for a valid run.
    assert _validate_extract_options(**_validate_kwargs(tmp_path)) is True


def test_validate_extract_options_expand_siblings_forces_llm(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    # Judge and grounding off, but sibling expansion needs the LLM: the flag
    # combination needs an endpoint, so a missing one is fatal.
    with pytest.raises(typer.Exit) as excinfo:
        _validate_extract_options(
            **_validate_kwargs(
                tmp_path, no_judge=True, no_grounding=True, expand_siblings=True, base_url=None, model=None
            )
        )
    assert excinfo.value.exit_code == 1
    # With the endpoint present the same combination passes and reports the need.
    assert (
        _validate_extract_options(**_validate_kwargs(tmp_path, no_judge=True, no_grounding=True, expand_siblings=True))
        is True
    )


def test_validate_extract_options_valid_formats_accepted(tmp_path):
    from asago_policy_mapper.cli import _validate_extract_options

    # All three formats pass validation (with an LLM endpoint present).
    for fmt in ("json", "yaml", "both"):
        assert _validate_extract_options(**_validate_kwargs(tmp_path, output_format=fmt)) is True


# --- _load_risk_catalog unit tests ---


def test_load_risk_catalog_merges_custom_risks_and_counts(monkeypatch, tmp_path):
    from asago_policy_mapper.cli import _load_risk_catalog

    nexus_risks = [
        Risk(id="r1", name="r1", description="A risk.", isDefinedByTaxonomy="test", type="Risk"),
    ]
    custom = [
        Risk(id="c1", name="c1", description="Custom risk.", isDefinedByTaxonomy="custom", type="Risk"),
        Risk(id="r1", name="r1 duplicate", description="Collides.", isDefinedByTaxonomy="custom", type="Risk"),
    ]

    class FakeNexus:
        def __init__(self, base_dir=None):
            pass

        def get_all_risks(self):
            return nexus_risks

    monkeypatch.setattr("ai_atlas_nexus.AIAtlasNexus", FakeNexus)

    all_risks, custom_count = _load_risk_catalog(str(tmp_path), custom)

    ids = [r.id for r in all_risks]
    assert ids.count("r1") == 1  # the colliding custom risk is skipped
    # The survivor is the Nexus risk, not the custom duplicate.
    kept_r1 = next(r for r in all_risks if r.id == "r1")
    assert kept_r1.description == "A risk."
    assert "c1" in ids
    assert custom_count == 1


def test_load_risk_catalog_collision_warns_on_stderr(monkeypatch, tmp_path, capsys):
    from asago_policy_mapper.cli import _load_risk_catalog

    class FakeNexus:
        def __init__(self, base_dir=None):
            pass

        def get_all_risks(self):
            return [Risk(id="r1", name="r1", description="A risk.", isDefinedByTaxonomy="test", type="Risk")]

    monkeypatch.setattr("ai_atlas_nexus.AIAtlasNexus", FakeNexus)
    colliding = [Risk(id="r1", name="dup", description="Collides.", isDefinedByTaxonomy="custom", type="Risk")]

    _load_risk_catalog(str(tmp_path), colliding)

    err = capsys.readouterr().err
    assert "custom risk 'r1' collides with an existing risk - skipping" in err


def test_load_risk_catalog_excludes_excluded_taxonomies(monkeypatch, tmp_path):
    from asago_policy_mapper.cli import EXCLUDED_TAXONOMIES, _load_risk_catalog

    excluded_tax = sorted(EXCLUDED_TAXONOMIES)[0]
    nexus_risks = [
        Risk(id="keep", name="keep", description="Kept.", isDefinedByTaxonomy="test", type="Risk"),
        Risk(id="drop", name="drop", description="Dropped.", isDefinedByTaxonomy=excluded_tax, type="Risk"),
    ]

    class FakeNexus:
        def __init__(self, base_dir=None):
            pass

        def get_all_risks(self):
            return nexus_risks

    monkeypatch.setattr("ai_atlas_nexus.AIAtlasNexus", FakeNexus)

    all_risks, _ = _load_risk_catalog(str(tmp_path), [])

    assert [r.id for r in all_risks] == ["keep"]


def test_load_risk_catalog_without_custom_risks(monkeypatch, tmp_path):
    from asago_policy_mapper.cli import _load_risk_catalog

    class FakeNexus:
        def __init__(self, base_dir=None):
            pass

        def get_all_risks(self):
            return [Risk(id="r1", name="r1", description="A risk.", isDefinedByTaxonomy="test", type="Risk")]

    monkeypatch.setattr("ai_atlas_nexus.AIAtlasNexus", FakeNexus)

    all_risks, custom_count = _load_risk_catalog(str(tmp_path), [])

    assert len(all_risks) == 1
    assert custom_count == 0


# --- _write_extraction_outputs unit tests ---


def _extraction_result_with_stats(auto_accepted, llm_judged, grounding_filtered):
    from asago_policy_mapper.extract.models import ExtractionResult, RetrievalStats

    return ExtractionResult(
        risks=[],
        source_documents=["policy.txt"],
        retrieval_stats=RetrievalStats(
            total_chunks=2,
            total_candidates_retrieved=10,
            auto_accepted=auto_accepted,
            llm_judged=llm_judged,
            grounding_filtered=grounding_filtered,
        ),
    )


class _RecordingTracker:
    """TokenTracker stand-in with fixed counters."""

    prompt_tokens = 100
    completion_tokens = 50
    total_tokens = 150
    calls = 3


@pytest.mark.parametrize(
    "no_judge,no_grounding,no_cross_encoder,expected_summary",
    [
        (True, True, False, "  3 auto-accepted (IR-only, no LLM stages)"),
        (False, True, False, "  3 auto-accepted, 1 LLM-judged (no grounding)"),
        (False, False, True, "  3 RRF-accepted, 2 grounding-filtered (no cross-encoder)"),
        (False, False, False, "  3 auto-accepted, 1 LLM-judged, 2 grounding-filtered"),
    ],
)
def test_write_extraction_outputs_summary_lines(
    tmp_path, capsys, no_judge, no_grounding, no_cross_encoder, expected_summary
):
    from asago_policy_mapper.cli import _write_extraction_outputs

    result = _extraction_result_with_stats(auto_accepted=3, llm_judged=1, grounding_filtered=2)
    result_data = result.model_dump()

    _write_extraction_outputs(
        result,
        result_data,
        tmp_path,
        output_format="json",
        needs_llm=False,
        tracker=_RecordingTracker(),
        no_judge=no_judge,
        no_grounding=no_grounding,
        no_cross_encoder=no_cross_encoder,
    )

    written = json.loads((tmp_path / "risk-extraction.json").read_text())
    assert written == result_data
    assert not (tmp_path / "risk-extraction.yaml").exists()
    assert expected_summary in capsys.readouterr().out


def test_write_extraction_outputs_yaml_format(tmp_path):
    from asago_policy_mapper.cli import _write_extraction_outputs

    result = _extraction_result_with_stats(auto_accepted=1, llm_judged=0, grounding_filtered=0)
    result_data = result.model_dump()

    _write_extraction_outputs(
        result,
        result_data,
        tmp_path,
        output_format="yaml",
        needs_llm=False,
        tracker=_RecordingTracker(),
        no_judge=True,
        no_grounding=True,
        no_cross_encoder=False,
    )

    assert (tmp_path / "risk-extraction.yaml").exists()
    assert yaml.safe_load((tmp_path / "risk-extraction.yaml").read_text()) == result_data
    assert not (tmp_path / "risk-extraction.json").exists()


def test_write_extraction_outputs_both_formats(tmp_path):
    from asago_policy_mapper.cli import _write_extraction_outputs

    result = _extraction_result_with_stats(auto_accepted=1, llm_judged=0, grounding_filtered=0)
    result_data = result.model_dump()

    _write_extraction_outputs(
        result,
        result_data,
        tmp_path,
        output_format="both",
        needs_llm=False,
        tracker=_RecordingTracker(),
        no_judge=True,
        no_grounding=True,
        no_cross_encoder=False,
    )

    assert json.loads((tmp_path / "risk-extraction.json").read_text()) == result_data
    assert yaml.safe_load((tmp_path / "risk-extraction.yaml").read_text()) == result_data


def test_write_extraction_outputs_token_usage_only_when_llm_needed(tmp_path, capsys):
    from asago_policy_mapper.cli import _write_extraction_outputs

    result = _extraction_result_with_stats(auto_accepted=1, llm_judged=0, grounding_filtered=0)
    result_data = result.model_dump()

    _write_extraction_outputs(
        result,
        result_data,
        tmp_path,
        output_format="json",
        needs_llm=True,
        tracker=_RecordingTracker(),
        no_judge=False,
        no_grounding=True,
        no_cross_encoder=False,
    )

    out = capsys.readouterr().out
    assert "Token usage: 100 prompt + 50 completion = 150 total (3 calls)" in out

    _write_extraction_outputs(
        result,
        result_data,
        tmp_path,
        output_format="json",
        needs_llm=False,
        tracker=_RecordingTracker(),
        no_judge=True,
        no_grounding=True,
        no_cross_encoder=False,
    )

    out = capsys.readouterr().out
    assert "Token usage" not in out
