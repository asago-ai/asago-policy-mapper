"""Rewrite ai-risk-taxonomy descriptions for better cross-encoder retrieval.

Reads airt_risks.json, rewrites each description via LLM, and outputs
a mapping file (risk_id -> rewritten_description) that can be loaded
by the pipeline at runtime without modifying Nexus.

Usage:
    uv run python risk-landscaper/scripts/rewrite_descriptions.py \
        --base-url https://your-endpoint/v1 \
        --model gemma-4-26b-a4b-it \
        [--batch-size 10] \
        [--output risk-landscaper/data/description_overrides.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import openai

SCRIPT_DIR = Path(__file__).resolve().parent

SYSTEM_PROMPT = """\
You are rewriting risk descriptions for an AI risk taxonomy. These descriptions \
will be used to match risks against organizational AI policy documents using a \
text retrieval model (ms-marco cross-encoder).

The retrieval model scores highest when descriptions:
- Explicitly mention "AI systems", "AI tools", or "AI" as the actor
- Use short, direct, active-voice statements
- Use concrete verbs (process, store, expose, disclose, generate) not nominalizations (leakage, de-anonymization)
- Read like something a policy author would write about

Write each rewritten description as a single direct statement, 1 sentence, under 30 words."""

USER_TEMPLATE = """\
Rewrite each risk description below. Follow these rules strictly:

1. NEVER start with the risk name or "is defined as"
2. ALWAYS mention "AI systems", "AI tools", or "AI" explicitly as the subject or agent
3. Use SHORT, DIRECT statements with ACTIVE VERBS: "may expose", "might generate", \
"could disclose", "may produce" — NOT nominalizations like "leakage", "de-anonymization", \
"amplification", "exacerbation"
4. Keep each to ONE sentence, under 30 words
5. Describe what can go wrong concretely, not abstractly

GOOD examples (these score 0.90+ with the retrieval model):
- "AI tools may process, store, or expose personal data without adequate safeguards or consent."
- "Unauthorized disclosure of personal data and sensitive information through AI systems."
- "AI-generated content might not be clearly disclosed or labeled as machine-produced."
- "AI systems might produce biased or discriminatory outputs affecting certain groups."
- "Personal information might be included as a part of the prompt that is sent to the model."

BAD examples (these score near 0.00 — AVOID this style):
- "Impacts due to leakage and unauthorized use, disclosure, or de-anonymization of personally identifiable information." (abstract, no AI actor, nominalizations)
- "Amplification and exacerbation of historical, societal, and systemic biases." (abstract, no AI actor, nominalizations)
- "Arrangements of or interactions between a human and an AI system which can result in..." (overly complex framing)
- "Non-transparent or untraceable integration of upstream third-party components." (jargon, no concrete harm)

Respond with ONLY a JSON array of objects, each with "risk_id" and "description" fields. \
No markdown, no explanation.

Risks to rewrite:
{risks_json}"""


def rewrite_batch(
    client: openai.OpenAI,
    model: str,
    risks: list[dict],
) -> list[dict]:
    risks_json = json.dumps(
        [{"risk_id": r["risk_id"], "name": r["name"], "description": r["original_description"]}
         for r in risks],
        indent=2,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(risks_json=risks_json)},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]

    return json.loads(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", default="gemma-4-26b-a4b-it")
    parser.add_argument("--api-key", default="none")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--input", type=Path, default=SCRIPT_DIR / "airt_risks.json")
    parser.add_argument("--output", type=Path, default=Path("risk-landscaper/data/description_overrides.json"))
    args = parser.parse_args()

    with open(args.input) as f:
        risks = json.load(f)

    print(f"Loaded {len(risks)} risks to rewrite")
    print(f"Model: {args.model}")
    print(f"Batch size: {args.batch_size}")

    client = openai.OpenAI(base_url=args.base_url, api_key=args.api_key)

    overrides = {}
    total = len(risks)
    errors = 0

    for i in range(0, total, args.batch_size):
        batch = risks[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (total + args.batch_size - 1) // args.batch_size

        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} risks)...", end=" ", flush=True)

        try:
            results = rewrite_batch(client, args.model, batch)
            for r in results:
                rid = r["risk_id"]
                desc = r["description"].strip()
                if desc:
                    overrides[rid] = desc
            print(f"OK ({len(results)} rewritten)")
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1
            for r in batch:
                overrides[r["risk_id"]] = r["original_description"]

    args.output.parent.mkdir(parents=True, exist_ok=True)

    output_data = {}
    for r in risks:
        rid = r["risk_id"]
        output_data[rid] = {
            "taxonomy": r["taxonomy"],
            "name": r["name"],
            "description": overrides.get(rid, r["original_description"]),
        }

    args.output.write_text(json.dumps(output_data, indent=2))
    print(f"\nDone: {len(overrides)}/{total} rewritten, {errors} batch errors")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
