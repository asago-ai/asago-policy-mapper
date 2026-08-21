from __future__ import annotations

import logging
from pathlib import Path

import yaml
from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk

from asago_policy_mapper.evals.eval import _TAXONOMY_PREFIXES

logger = logging.getLogger(__name__)

_BUILTIN_PREFIXES = tuple(prefix for prefix, _ in _TAXONOMY_PREFIXES)


def load_custom_taxonomy(path: Path) -> list[Risk]:
    """Load and validate a custom taxonomy YAML file.

    Returns a list of Risk objects ready to be passed to run_extraction().
    Raises ValueError with actionable messages on validation failure.
    """
    path = Path(path)
    if not path.exists():
        raise ValueError(f"Custom taxonomy file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ValueError(f"Custom taxonomy file must be a YAML mapping, got {type(raw).__name__} in {path}")

    _validate_taxonomy_block(raw, path)
    taxonomy_id = raw["taxonomy"]["id"]
    taxonomy_name = raw["taxonomy"]["name"]

    if "risks" not in raw:
        raise ValueError(f"Custom taxonomy {path} is missing the 'risks' key")
    if not isinstance(raw["risks"], list) or len(raw["risks"]) == 0:
        raise ValueError(f"Custom taxonomy {path} has an empty or invalid 'risks' list - at least one risk is required")

    risks: list[Risk] = []
    seen_ids: set[str] = set()

    for i, entry in enumerate(raw["risks"]):
        _validate_risk_entry(entry, i, path)

        rid = entry["id"]
        if rid in seen_ids:
            raise ValueError(f"Duplicate risk ID '{rid}' in {path}")
        seen_ids.add(rid)

        for prefix in _BUILTIN_PREFIXES:
            if rid.startswith(prefix):
                logger.warning(
                    "Risk '%s' in %s uses built-in prefix '%s' - this may collide with Nexus risks",
                    rid,
                    path,
                    prefix,
                )
                break

        desc = entry["description"]
        if len(desc.strip()) < 10:
            logger.warning(
                "Risk '%s' in %s has a very short description (%d chars) - retrieval quality may be poor",
                rid,
                path,
                len(desc.strip()),
            )

        risks.append(
            Risk(
                id=rid,
                name=entry["name"],
                description=desc,
                isDefinedByTaxonomy=taxonomy_id,
                concern=entry.get("concern", ""),
                risk_type=entry.get("risk_type"),
                type="Risk",
            )
        )

    logger.info(
        "Loaded %d custom risks from taxonomy '%s' (%s)",
        len(risks),
        taxonomy_name,
        path,
    )
    return risks


def _validate_taxonomy_block(raw: dict, path: Path) -> None:
    if "taxonomy" not in raw:
        raise ValueError(f"Custom taxonomy {path} is missing the 'taxonomy' block")

    tax = raw["taxonomy"]
    if not isinstance(tax, dict):
        raise ValueError(f"'taxonomy' in {path} must be a mapping, got {type(tax).__name__}")

    for field in ("id", "name"):
        if field not in tax or not isinstance(tax[field], str) or not tax[field].strip():
            raise ValueError(f"'taxonomy.{field}' is missing or empty in {path}")


def _validate_risk_entry(entry: dict, index: int, path: Path) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"Risk at index {index} in {path} must be a mapping, got {type(entry).__name__}")

    for field in ("id", "name", "description"):
        if field not in entry:
            raise ValueError(f"Risk at index {index} in {path} is missing required field '{field}'")
        val = entry[field]
        if not isinstance(val, str) or not val.strip():
            raise ValueError(
                f"Risk '{entry.get('id', f'index {index}')}' in {path} has an empty or non-string '{field}'"
            )
