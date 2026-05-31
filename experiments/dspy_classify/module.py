from __future__ import annotations

import dspy

from experiments.dspy_classify.signature import ClassifyRiskTaxonomy


class RiskClassifier(dspy.Module):
    def __init__(self):
        self.classify = dspy.ChainOfThought(ClassifyRiskTaxonomy)

    def forward(self, extracted_risks: str, target_categories: str):
        return self.classify(
            extracted_risks=extracted_risks,
            target_categories=target_categories,
        )
