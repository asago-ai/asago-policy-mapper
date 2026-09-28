"""Enrich saved results with curated report themes, without rerunning extraction."""

from pathlib import Path

import yaml

from asago_policy_mapper.evals.eval import _load_risk_to_category_map, _sanitise_risk_id

THEMES_PATH = Path(__file__).resolve().parents[1] / "data" / "report_themes.yaml"
UNGROUPED_THEME = {
    "id": "other",
    "label": "Other / not yet grouped",
    "description": "Matches without a supported theme mapping, including custom risks.",
}


def enrich_report_themes(data: dict) -> dict:
    """Return a report-only copy with themes and the category links behind them.

    Reuse evaluation's exact/close/broad mapping policy. Match full risk IDs:
    variant links stay specific and are never inferred from a synthetic parent.
    The saved extraction and its risk/evaluation counts are left intact.
    """
    definitions = yaml.safe_load(THEMES_PATH.read_text())
    themes = definitions["themes"]
    categories = definitions["category_taxonomies"]
    risk_to_category = _load_risk_to_category_map()
    risks = []
    for risk in data.get("risks") or []:
        links = []
        theme_ids: set[str] = set()
        risk_id = _sanitise_risk_id(risk.get("risk_id") or "")
        for taxonomy, category_ids in sorted(risk_to_category.get(risk_id, {}).items()):
            framework = categories.get(taxonomy, {})
            for category_id in sorted(category_ids):
                category = framework.get("categories", {}).get(category_id)
                if not category:
                    continue
                theme_ids.update(category["themes"])
                links.append(
                    {
                        "category_id": category_id,
                        "category_label": category["label"],
                        "taxonomy": taxonomy,
                        "taxonomy_label": framework["label"],
                        "theme_ids": list(category["themes"]),
                    }
                )
        risks.append(
            {
                **risk,
                "theme_ids": [theme["id"] for theme in themes if theme["id"] in theme_ids] or ["other"],
                "theme_links": links,
            }
        )
    return {
        **data,
        "risks": risks,
        "theme_catalog": [*themes, UNGROUPED_THEME],
        "theme_mapping_version": definitions["version"],
    }
