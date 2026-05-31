from __future__ import annotations

import dspy

from experiments.dspy_judge.signature import JudgeRiskRelevance


class RiskJudge(dspy.Module):
    def __init__(self):
        self.judge = dspy.ChainOfThought(JudgeRiskRelevance)

    def forward(self, chunk_text: str, candidate_risks: str):
        return self.judge(
            chunk_text=chunk_text, candidate_risks=candidate_risks
        )
