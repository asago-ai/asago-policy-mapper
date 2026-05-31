from __future__ import annotations

from typing import Literal

import dspy
from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    risk_id: str
    relevant: bool
    justification: str


class JudgeRiskRelevance(dspy.Signature):
    """Given a text passage from a policy document and a list of candidate AI
    risks, determine which risks are actually relevant to the text.

    A risk is relevant if the text describes, implies, or directly addresses
    the risk concept — even if different terminology is used.

    Respond with a verdict for EACH candidate risk."""

    chunk_text: str = dspy.InputField(
        desc="Text passage from an AI policy document"
    )
    candidate_risks: str = dspy.InputField(
        desc="Candidate AI risks to evaluate, each with ID, name, and description"
    )
    verdicts: list[JudgeVerdict] = dspy.OutputField(
        desc="Relevance verdict for each candidate risk"
    )
