"""Catalog equivalence tests for the ai-atlas-nexus PyPI pin.

The migration from the git pin (commit c7a53040, declared as @main) to
ai-atlas-nexus==1.2.5 must not change the risk catalog the pipeline
consumes. These tests load the installed package's catalog with the
production EXCLUDED_TAXONOMIES filter and assert the known post-filter
population, so a future dependency bump that changes the catalog fails
loudly here instead of shifting retrieval results silently.
"""

import pytest

from asago_policy_mapper.cli import EXCLUDED_TAXONOMIES

# Filtered risk population of the pinned-commit catalog, verified identical
# for the 1.2.5 wheel during the pin migration (same 560 IDs, same names and
# descriptions). If a deliberate upgrade changes this number, update it here
# and re-run the battery smoke.
EXPECTED_FILTERED_RISKS = 560

_TAXONOMY_HISTOGRAM = {
    "ibm-risk-atlas": 99,
    "ai-risk-taxonomy": 314,
    "credo-ucf": 49,
    "eticas-ai-risk-taxonomy": 64,
    "mit-ai-risk-repository": 24,
    "owasp-ast10": 10,
}


def _filtered_risks(nexus):
    return [r for r in nexus.get_all_risks() if getattr(r, "isDefinedByTaxonomy", "") not in EXCLUDED_TAXONOMIES]


def test_installed_package_catalog_matches_pinned_population():
    """The installed ai-atlas-nexus catalog yields the pinned 560 filtered risks."""
    from ai_atlas_nexus import AIAtlasNexus

    risks = _filtered_risks(AIAtlasNexus())

    assert len(risks) == EXPECTED_FILTERED_RISKS


def test_installed_package_catalog_taxonomy_histogram():
    """The filtered risks keep the pinned per-taxonomy distribution."""
    from collections import Counter

    from ai_atlas_nexus import AIAtlasNexus

    risks = _filtered_risks(AIAtlasNexus())

    histogram = Counter(r.isDefinedByTaxonomy for r in risks)
    assert dict(histogram) == _TAXONOMY_HISTOGRAM


def test_installed_package_catalog_excludes_no_excluded_taxonomy():
    """No excluded taxonomy leaks into the filtered catalog."""
    from ai_atlas_nexus import AIAtlasNexus

    risks = _filtered_risks(AIAtlasNexus())

    assert all(r.isDefinedByTaxonomy not in EXCLUDED_TAXONOMIES for r in risks)


def test_installed_package_catalog_risk_ids_unique():
    """Risk IDs are unique after filtering (variant collapsing relies on distinct IDs)."""
    from ai_atlas_nexus import AIAtlasNexus

    risks = _filtered_risks(AIAtlasNexus())

    ids = [r.id for r in risks]
    assert len(ids) == len(set(ids))


@pytest.mark.slow
def test_pinned_commit_catalog_matches_installed_package():
    """Full equivalence check against the pinned git commit's catalog.

    Marked slow: it loads a second full catalog in a subprocess. Run it when
    the pin moves. Requires a checkout of the old pinned commit laid out as a
    source tree (``<dir>/src/ai_atlas_nexus/...``) in ``NEXUS_PIN_EQUIVALENCE_DIR``.

    The pinned tree is loaded with its own models in a subprocess, because the
    installed wheel's datamodel cannot validate the old pin's raw YAML (the pin
    sits commits ahead of the released tag and carries slot changes). Each
    catalog is therefore loaded by the library version it shipped with, which
    is also how production consumed the pin.
    """
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    tree = os.environ.get("NEXUS_PIN_EQUIVALENCE_DIR")
    if not tree:
        pytest.skip("no pinned-commit data tree available (set NEXUS_PIN_EQUIVALENCE_DIR to compare)")
    src_dir = Path(tree) / "src"
    assert (src_dir / "ai_atlas_nexus" / "data" / "knowledge_graph").exists(), f"pinned tree missing: {src_dir}"

    # Load the pinned tree with its own code in a subprocess.
    loader = (
        "import sys; sys.path.insert(0, {src!r});\n"
        "from ai_atlas_nexus import AIAtlasNexus;\n"
        "from asago_policy_mapper.cli import EXCLUDED_TAXONOMIES;\n"
        "n = AIAtlasNexus();\n"
        "catalog = {{r.id: [r.name, r.description] for r in n.get_all_risks()\n"
        "           if getattr(r, 'isDefinedByTaxonomy', '') not in EXCLUDED_TAXONOMIES}};\n"
        "print(json.dumps(catalog))"
    ).format(src=str(src_dir))
    proc = subprocess.run(
        [sys.executable, "-c", "import json;\n" + loader],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
    pinned = {k: tuple(v) for k, v in json.loads(proc.stdout).items()}

    from ai_atlas_nexus import AIAtlasNexus

    installed = {r.id: (r.name, r.description) for r in _filtered_risks(AIAtlasNexus())}

    assert pinned == installed
