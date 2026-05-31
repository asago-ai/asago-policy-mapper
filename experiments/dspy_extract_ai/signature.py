"""DSPy Signature for AI system extraction from policy documents."""

from __future__ import annotations

from typing import Literal

import dspy
from pydantic import BaseModel, field_validator


_VALID_DEPLOYMENT_STATUSES = {"deployed", "referenced", "generic"}


class AISystem(BaseModel):
    name: str
    description: str = ""
    capabilities: list[str] = []
    deployment_status: str = ""

    @field_validator("deployment_status")
    @classmethod
    def _normalize_deployment_status(cls, v: str) -> str:
        if not v:
            return ""
        normalized = v.strip().lower()
        if normalized in _VALID_DEPLOYMENT_STATUSES:
            return normalized
        return ""


class AIExtractionResult(BaseModel):
    systems: list[AISystem]


class ExtractAISystems(dspy.Signature):
    """Extract AI systems from this policy document. For each system, capture its name,
    description, capabilities, and deployment_status.

    Classify deployment_status as:
    - "deployed": the organization actively operates or deploys this system
    - "referenced": a named system mentioned but not deployed (prohibited, compared against, discussed)
    - "generic": a category of AI systems, not a specific named system

    Extract only AI systems the organization deploys, procures, evaluates, governs, or references.
    Do NOT extract generic AI concepts, technology categories, or glossary definitions.
    Do NOT extract the same generic AI concept multiple times under different names."""

    document_text: str = dspy.InputField(desc="Full policy document text")
    ontology_snippet: str = dspy.InputField(desc="AI system types and capability vocabulary from DPV ontology")
    extraction: AIExtractionResult = dspy.OutputField(desc="Extracted AI systems with names, descriptions, capabilities, and deployment status")
