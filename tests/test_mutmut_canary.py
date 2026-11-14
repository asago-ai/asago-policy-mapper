"""Sandbox-isolation canary for the local mutmut workflow.

mutmut's sandbox (``mutants/``) is only trustworthy if the test workers import
the trampolined copies from ``mutants/src`` rather than the editable-installed
original tree. A run that silently imports the original reports every mutant
as survived. This guard runs one known-killable mutant through the real mutmut
machinery and asserts it dies, so a broken sandbox fails loudly instead of
producing false scores.

See "Mutation testing" in CLAUDE.md for the workflow this protects.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# A mutant that must die: `if not matches:` -> `if matches:` in merge_matches
# inverts the early return, so non-empty inputs come back empty — the
# non-empty merge tests (test_merge_same_risk_across_chunks and siblings) pin
# the opposite and kill it. When the canary needs to change (e.g. the mutant
# renumbers after edits to merge.py), re-run
# `mutmut run "asago_policy_mapper.extract.merge*"` and pick a killed mutant
# whose diff inverts a directly asserted behavior.
_CANARY_MUTANT = "asago_policy_mapper.extract.merge.x_merge_matches__mutmut_2"

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_mutmut_sandbox_kills_canary_mutant(tmp_path):
    """The mutmut sandbox must import mutated code: the canary mutant dies.

    Runs the real `mutmut run` on a single known-killable mutant in a copy of
    the checkout and asserts the recorded verdict is "killed". A sandbox that
    imports the editable-installed original tree instead of ``mutants/src``
    reports the canary as survived, failing this test.
    """
    try:
        import mutmut  # noqa: F401
    except ImportError:
        pytest.skip("mutmut is not installed; install it with `UV_NO_CONFIG=1 uv pip install mutmut`")

    # Run in a scratch copy so the repo's own mutants/ cache and stats stay
    # untouched; a read-only checkout would break mutmut's sandbox generation.
    repo = tmp_path / "repo"
    repo.mkdir()
    for name in ("src", "tests", "pyproject.toml", "uv.lock"):
        source = _REPO_ROOT / name
        target = repo / name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

    run = subprocess.run(
        [sys.executable, "-m", "mutmut", "run", _CANARY_MUTANT, "--max-children", "2"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert run.returncode == 0, f"mutmut run failed:\n{run.stdout}\n{run.stderr}"

    meta = json.loads((repo / "mutants" / "src" / "asago_policy_mapper" / "extract" / "merge.py.meta").read_text())
    verdict = meta["exit_code_by_key"].get(_CANARY_MUTANT)
    # exit code 1 means pytest failed under the mutant: the kill is real.
    # exit code 0 means the tests passed with the mutant active, which for this
    # canary means the workers ran the unmutated original.
    assert verdict == 1, (
        f"canary mutant {_CANARY_MUTANT} was not killed (verdict={verdict!r}). "
        "The mutmut sandbox probably imported the editable-installed original "
        "tree instead of mutants/src; every mutation score from such a run is false."
    )
