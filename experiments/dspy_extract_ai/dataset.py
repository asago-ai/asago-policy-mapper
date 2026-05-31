"""Build DSPy dataset from human-reviewed ground truth TTL + policy documents."""

from __future__ import annotations

import json
from pathlib import Path

import dspy
from rdflib import Graph, Namespace, RDF

from experiments.dspy_extract_ai.signature import AISystem

_ROOT = Path(__file__).resolve().parent.parent.parent
_GT_DIR = _ROOT / "policy-extractor" / "evals" / "ground_truth"
_POLICY_DIR = _ROOT / "policy_examples"

AI = Namespace("https://w3id.org/dpv/ai#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DPV = Namespace("https://w3id.org/dpv#")
TECH = Namespace("https://w3id.org/dpv/tech#")

REVIEWED_POLICIES = [
    ("ars", "ars.md"),
    ("dhs-gov", "dhs-gov.md"),
    ("llvm", "llvm.md"),
]


def _load_ontology_snippet() -> str:
    from policy_extractor.graph.catalogue import load_curated_registry, render_curated_snippet
    registry = load_curated_registry()
    return render_curated_snippet(registry, ["ai_systems", "ai_capabilities"])


def _parse_gt_ai_systems(gt_path: Path) -> list[dict]:
    g = Graph()
    g.parse(str(gt_path), format="turtle")

    systems = []
    for s in g.subjects(RDF.type, AI.AISystem):
        name = g.value(s, SKOS.prefLabel)
        if not name:
            continue
        desc = g.value(s, DPV.hasDescription)
        caps = []
        for cap_node in g.objects(s, AI.hasCapability):
            cap_name = g.value(cap_node, SKOS.prefLabel)
            if cap_name:
                caps.append(str(cap_name))

        has_deployer = any(True for _ in g.objects(s, TECH.hasDeployer))
        deployment_status = "deployed" if has_deployer else ""

        systems.append({
            "name": str(name),
            "description": str(desc) if desc else "",
            "capabilities": caps,
            "deployment_status": deployment_status,
        })
    return systems


def load_dataset() -> tuple[list[dspy.Example], list[dspy.Example]]:
    snippet = _load_ontology_snippet()

    examples = []
    for gt_name, policy_file in REVIEWED_POLICIES:
        gt_path = _GT_DIR / f"{gt_name}.ttl"
        policy_path = _POLICY_DIR / policy_file

        if not gt_path.exists() or not policy_path.exists():
            raise FileNotFoundError(f"Missing files for {gt_name}: gt={gt_path.exists()}, policy={policy_path.exists()}")

        document_text = policy_path.read_text()
        gt_systems = _parse_gt_ai_systems(gt_path)

        example = dspy.Example(
            document_text=document_text,
            ontology_snippet=snippet,
            expected_systems=gt_systems,
        ).with_inputs("document_text", "ontology_snippet")

        examples.append(example)

    return examples, list(examples)
