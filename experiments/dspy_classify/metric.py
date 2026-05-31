from __future__ import annotations

import dspy


def classify_metric(example, prediction, trace=None, pred_name=None, pred_trace=None):
    expected = {v["risk_id"]: v["applies"] for v in example.expected_verdicts}

    try:
        predicted_verdicts = prediction.verdicts
        if not predicted_verdicts:
            predicted = {}
        else:
            predicted = {}
            for v in predicted_verdicts:
                if hasattr(v, "risk_id"):
                    predicted[v.risk_id] = v.applies
                elif isinstance(v, dict):
                    predicted[v["risk_id"]] = v["applies"]
    except (AttributeError, TypeError):
        predicted = {}

    tp = sum(1 for rid in expected if expected[rid] and predicted.get(rid, False))
    fp = sum(1 for rid in predicted if predicted[rid] and not expected.get(rid, False))
    fn = sum(1 for rid in expected if expected[rid] and not predicted.get(rid, False))

    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

    if pred_name is None:
        return f1

    n_expected_pos = sum(1 for v in expected.values() if v)
    n_predicted_pos = sum(1 for v in predicted.values() if v)

    feedback = (
        f"F1={f1:.3f} P={precision:.3f} R={recall:.3f} "
        f"(TP={tp} FP={fp} FN={fn}) "
        f"expected_pos={n_expected_pos} predicted_pos={n_predicted_pos}"
    )

    return dspy.Prediction(score=f1, feedback=feedback)
