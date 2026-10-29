from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

import yaml
from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk

from asago_policy_mapper.evals.eval import _TAXONOMY_PREFIXES

logger = logging.getLogger(__name__)

_BUILTIN_PREFIXES = tuple(prefix for prefix, _ in _TAXONOMY_PREFIXES)

# Sentence-ending punctuation, optionally followed by closing quotes or brackets.
_CLOSING_PUNCTUATION_RE = re.compile(r"[.!?][\"'\u201d\u2019)\]}]*$")
# A trailing ellipsis ("..." or U+2026) marks elided text, so it does not count as an ending.
_TRAILING_ELLIPSIS_RE = re.compile(r"(?:\.\.\.|\u2026)[\"'\u201d\u2019)\]}]*$")

# Upstream Nexus descriptions known to be cut mid-sentence, keyed by risk ID.
# Each entry maps the exact truncated text Nexus ships to the full text from the
# source publication. The override applies only while the loaded description still
# equals the truncated text, so a fixed upstream catalog is never overwritten.
#
# Source for the CREDO UCF entries: Eisenberg et al., "The Unified Control Framework:
# Establishing a Common Foundation for Enterprise AI Governance, Risk Management and
# Regulatory Compliance", arXiv:2503.05937v1, Appendix A "Risk taxonomy" table.
# credo-risk-045 ("Competitive dynamics") is not listed: the paper's own text is cut
# after "The AI system's rapid development", so no complete wording exists to restore.
_DESCRIPTION_OVERRIDES: dict[str, tuple[str, str]] = {
    # "Stereotype perpetuation", PDF page 21. Nexus appends a cut copy of the
    # credo-risk-011 text; the paper's description is the first sentence alone
    # (the paper typesets the apostrophe as U+2019; the catalog's ASCII ' is kept).
    "credo-risk-010": (
        "The AI system's outputs may explicitly reflect or reinforce harmful stereotypes, prejudices, "
        "or biased characterizations of specific groups. The AI system may exhibit unjustified or "
        "harmful differences in accuracy, quality, or outcomes across demographic groups, potentially "
        "leading to unfair treatment and discrimination. This includes both disparate error rates that "
        "affect opportunity and",
        "The AI system's outputs may explicitly reflect or reinforce harmful stereotypes, prejudices, "
        "or biased characterizations of specific groups.",
    ),
    # "AI deception", PDF page 22.
    "credo-risk-018": (
        "The AI system may misrepresent its own capabilities or limitations, potentially leading to "
        "misplaced trust or inappropriate",
        "The AI system may misrepresent its own capabilities or limitations, potentially leading to "
        "misplaced trust or inappropriate use.",
    ),
}


def apply_description_overrides(risks: Iterable[Risk]) -> list[Risk]:
    """Return the risks with known upstream-truncated descriptions restored.

    A risk listed in ``_DESCRIPTION_OVERRIDES`` is replaced by a copy carrying the
    full description only when its loaded description (ignoring surrounding
    whitespace) still equals the known truncated text; every other risk is
    returned unchanged.
    """
    patched: list[Risk] = []
    for risk in risks:
        override = _DESCRIPTION_OVERRIDES.get(risk.id)
        if override and (getattr(risk, "description", None) or "").strip() == override[0]:
            logger.debug("Restoring truncated description of risk '%s'", risk.id)
            risk = risk.model_copy(update={"description": override[1]})
        patched.append(risk)
    return patched


def find_unterminated_descriptions(risks: Iterable[Risk]) -> list[Risk]:
    """Return the risks whose non-empty description lacks closing punctuation.

    A description that does not end in ``.``, ``!`` or ``?`` (optionally followed
    by closing quotes or brackets) may have been cut mid-sentence upstream. A
    trailing ellipsis is flagged too, since it marks elided text. Empty and
    whitespace-only descriptions are not flagged: there is no text to be cut.
    """
    flagged: list[Risk] = []
    for risk in risks:
        desc = (getattr(risk, "description", None) or "").strip()
        if desc and (not _CLOSING_PUNCTUATION_RE.search(desc) or _TRAILING_ELLIPSIS_RE.search(desc)):
            flagged.append(risk)
    return flagged


def warn_unterminated_descriptions(risks: Iterable[Risk]) -> list[str]:
    """Log a warning for each risk whose description lacks closing punctuation.

    Opt-in check (``extract --check-risk-text``); returns the flagged risk IDs.
    """
    flagged = find_unterminated_descriptions(risks)
    for risk in flagged:
        logger.warning(
            "Risk '%s' description lacks closing punctuation - text may be truncated: ...%s",
            risk.id,
            risk.description.strip()[-60:],
        )
    return [risk.id for risk in flagged]


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
