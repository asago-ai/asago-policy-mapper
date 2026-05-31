"""DSPy Module for AI system extraction."""

from __future__ import annotations

import dspy

from experiments.dspy_extract_ai.signature import ExtractAISystems


class AIExtractor(dspy.Module):
    def __init__(self):
        self.extract = dspy.ChainOfThought(ExtractAISystems)

    def forward(self, document_text: str, ontology_snippet: str):
        return self.extract(document_text=document_text, ontology_snippet=ontology_snippet)
