import json
import re
from copy import deepcopy

import yaml

from asago_policy_mapper.evals.eval import _load_risk_to_category_map
from asago_policy_mapper.extract import report_themes
from asago_policy_mapper.extract.report import build_risk_extraction_report


def test_saved_report_groups_cross_taxonomy_matches_without_changing_input(tmp_path):
    data = {
        "risks": [
            {"risk_id": "atlas-exposing-personal-information", "taxonomy": "ibm-risk-atlas"},
            {"risk_id": "mit-ai-risk-subdomain-2.1", "taxonomy": "mit-ai-risk-repository"},
            {"risk_id": "custom-privacy", "risk_name": "Privacy", "taxonomy": "custom"},
        ],
        "metadata": {"query_gen": True},
        "eval": {"matched": 3},
    }
    original = deepcopy(data)
    html = build_risk_extraction_report(data, tmp_path / "report.html").read_text()
    match = re.search(r"const DATA = (.*);</script>", html)
    assert match is not None
    enriched = json.loads(match.group(1))
    assert data == original
    assert enriched["metadata"] == data["metadata"]
    assert enriched["eval"] == data["eval"]
    assert len(enriched["risks"]) == 3
    ibm, mit, custom = enriched["risks"]
    assert ibm["theme_ids"] == mit["theme_ids"] == ["privacy"]
    assert any(link["category_label"] == "Sensitive information disclosure" for link in mit["theme_links"])
    assert custom["theme_ids"] == ["other"]
    assert custom["theme_links"] == []
    assert enriched["theme_catalog"][-1]["label"] == "Other / not yet grouped"


def test_only_supported_links_assign_themes_and_variants_stay_specific(tmp_path, monkeypatch):
    mapping_file = tmp_path / "mapping.tsv"
    mapping_file.write_text(
        "subject_id\tsubject_source\tpredicate_id\tobject_id\tobject_source\n"
        "both\tatlas\tskos:exactMatch\tnist-information-security\tnist-ai-rmf\n"
        "both\tatlas\tskos:closeMatch\tnist-data-privacy\tnist-ai-rmf\n"
        "both\tatlas\tskos:broadMatch\tllm022025-sensitive-information-disclosure\towasp-llm-2.0\n"
        "weak\tatlas\tskos:relatedMatch\tnist-data-privacy\tnist-ai-rmf\n"
        "future\tatlas\tskos:broadMatch\tnew-category\tnist-ai-rmf\n"
        "parent\tatlas\tskos:broadMatch\tnist-information-security\tnist-ai-rmf\n"
        "parent---private\tatlas\tskos:broadMatch\tnist-data-privacy\tnist-ai-rmf\n"
    )
    monkeypatch.setattr(report_themes, "_load_risk_to_category_map", lambda: _load_risk_to_category_map(mapping_file))
    ids = ["both", "weak", "future", "parent---private", "parent---unknown", "both Trailing Nexus name"]
    result = report_themes.enrich_report_themes({"risks": [{"risk_id": rid} for rid in ids]})
    both, weak, future, private, unknown, malformed = result["risks"]
    assert both["theme_ids"] == malformed["theme_ids"] == ["privacy", "security"]
    assert len(both["theme_links"]) == 3  # Multiple category links do not duplicate a theme.
    assert weak["theme_ids"] == future["theme_ids"] == unknown["theme_ids"] == ["other"]
    assert private["theme_ids"] == ["privacy"]  # Do not inherit the parent's security link.


def test_theme_vocabulary_covers_current_strong_categories_and_has_valid_references():
    definitions = yaml.safe_load(report_themes.THEMES_PATH.read_text())
    theme_ids = [theme["id"] for theme in definitions["themes"]]
    assert len(theme_ids) == len(set(theme_ids))
    assert "other" not in theme_ids
    categories = definitions["category_taxonomies"]
    for framework in categories.values():
        for category in framework["categories"].values():
            assert category["themes"]
            assert set(category["themes"]) <= set(theme_ids)
    for frameworks in _load_risk_to_category_map().values():
        for taxonomy, category_ids in frameworks.items():
            assert category_ids <= categories[taxonomy]["categories"].keys()


def test_empty_or_older_results_remain_usable():
    assert report_themes.enrich_report_themes({})["risks"] == []
    result = report_themes.enrich_report_themes({"risks": [{}, {"risk_id": None}]})
    assert all(risk["theme_ids"] == ["other"] for risk in result["risks"])
