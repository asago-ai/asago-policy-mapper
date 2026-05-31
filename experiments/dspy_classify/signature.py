from __future__ import annotations

import dspy
from pydantic import BaseModel


class ClassifyVerdict(BaseModel):
    risk_id: str
    applies: bool
    source_risk_ids: list[str]


class ClassifyRiskTaxonomy(dspy.Signature):
    """Given specific AI risks already identified in a policy document (with
    supporting evidence), determine which high-level risk framework categories
    apply.

    A target category applies ONLY if at least one extracted risk clearly and
    directly falls within its scope, supported by the evidence. Do not classify
    based on thematic overlap alone.

    Respond with a verdict for EACH target category."""

    extracted_risks: str = dspy.InputField(
        desc="Specific AI risks already identified in this document, with evidence quotes"
    )
    target_categories: str = dspy.InputField(
        desc="Target risk framework categories to classify into, with descriptions"
    )
    verdicts: list[ClassifyVerdict] = dspy.OutputField(
        desc="Classification verdict for each target category"
    )
