#!/usr/bin/env python3
"""Run the document-to-risk extraction pipeline against a battery config.

Battery configs are YAML files that specify which policy files/directories
to run and with what model. Subdirectories are multi-document groups —
all files in the subdirectory are passed together as one run.

Uses the hybrid retrieval pipeline (BM25 + semantic + cross-encoder)
to extract Nexus risk IDs directly from documents.

Usage:
    python run_extract_battery.py ../batteries/simple.yaml --base-url http://localhost:8000/v1
    python run_extract_battery.py ../batteries/real.yaml --base-url http://localhost:8000/v1 --model override-model
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import yaml

from concorde_policy_mapper.evals.eval import evaluate_extraction

PACKAGE_DIR = Path(__file__).parent
ROOT = PACKAGE_DIR.parent
RUNS_DIR = PACKAGE_DIR / "extract-runs"
NEXUS_BASE_DIR = os.environ.get("NEXUS_BASE_DIR", "/Users/hjrnunes/workspace/redhat/ibm/ai-atlas-nexus")
GROUND_TRUTH_DIR = PACKAGE_DIR / "evals" / "ground_truth"

POLICY_EXTENSIONS = {".json", ".md", ".txt", ".pdf", ".docx", ".html", ".htm"}

_print_lock = threading.Lock()


def _locked_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)
        sys.stdout.flush()


def _is_policy_file(p: Path) -> bool:
    return p.is_file() and not p.name.startswith(".") and p.suffix.lower() in POLICY_EXTENSIONS


def _resolve_run(entry: str) -> tuple[str, list[Path]]:
    path = ROOT / entry.rstrip("/")
    if path.is_file():
        return path.stem, [path]
    if path.is_dir():
        files = sorted(p for p in path.iterdir() if _is_policy_file(p))
        if not files:
            _locked_print(f"  Warning: no policy files in {path}, skipping")
            return path.name, []
        return path.name, files
    _locked_print(f"  Warning: {path} does not exist, skipping")
    return Path(entry).stem, []


def _fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s:02d}s"


def _pad_name(name: str, width: int = 20) -> str:
    return name.ljust(width)[:width]


def run_one(
        policies: list[Path],
        name: str,
        base_url: str,
        model: str,
        runs_dir: Path,
        threshold_high: float = 0.7,
        threshold_low: float = 0.15,
        bi_encoder_model: str = "all-mpnet-base-v2",
        cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
        name_width: int = 20,
        no_cross_encoder: bool = False,
        rrf_min_score: float = 0.01,
        classify_taxonomies: str = "nist-ai-rmf,owasp-llm-2.0",
) -> tuple[str, bool, str, int, float]:
    out = runs_dir / name
    tag = _pad_name(name, name_width)

    files_desc = ", ".join(p.name for p in policies)
    _locked_print(f"  [{tag}] starting ({files_desc})")

    cmd = [
        "uv", "run", "concorde-policy-mapper", "extract",
        *[str(p) for p in policies],
        "-o", str(out),
        "--base-url", base_url,
        "--model", model,
        "--nexus-base-dir", NEXUS_BASE_DIR,
        "--threshold-high", str(threshold_high),
        "--threshold-low", str(threshold_low),
        "--bi-encoder-model", bi_encoder_model,
        "--cross-encoder-model", cross_encoder_model,
        "--classify-taxonomies", classify_taxonomies,
    ]
    if no_cross_encoder:
        cmd.extend(["--no-cross-encoder", "--rrf-min-score", str(rrf_min_score)])

    t0 = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    captured_lines: list[str] = []
    for line in proc.stdout:
        line = line.rstrip("\n")
        captured_lines.append(line)
        _locked_print(f"  [{tag}] {line}")
    proc.wait()

    elapsed = time.monotonic() - t0
    ok = proc.returncode == 0

    if ok:
        _locked_print(f"  [{tag}] done ({_fmt_elapsed(elapsed)})")
    else:
        _locked_print(f"  [{tag}] FAILED (exit {proc.returncode}, {_fmt_elapsed(elapsed)})")
        error_path = out / "error.json"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_data = {
            "error": True,
            "name": name,
            "exit_code": proc.returncode,
            "stderr_tail": captured_lines[-20:],
            "timestamp": datetime.now().isoformat(),
        }
        with open(error_path, "w") as f:
            json.dump(error_data, f, indent=2)

    return name, ok, "", proc.returncode, elapsed


def run_eval(name: str, runs_dir: Path, min_recall: float = 0.80, min_precision: float = 0.60) -> dict | None:
    gt_path = GROUND_TRUTH_DIR / f"{name}.yaml"
    if not gt_path.exists():
        return None
    extracted_path = runs_dir / name / "risk-extraction.json"
    if not extracted_path.exists():
        return None
    result = evaluate_extraction(gt_path, extracted_path, policy_name=name, min_recall=min_recall, min_precision=min_precision)
    eval_path = runs_dir / name / "eval.json"
    eval_path.write_text(json.dumps(result, indent=2))

    extraction_data = json.loads(extracted_path.read_text())
    extraction_data["eval"] = result
    extracted_path.write_text(json.dumps(extraction_data, indent=2))

    try:
        from concorde_policy_mapper.extract.report import build_risk_extraction_report
        build_risk_extraction_report(extraction_data, runs_dir / name / "risk-extraction.html")
    except Exception as e:
        _locked_print(f"  [{name}] Warning: could not generate HTML report: {e}")

    return result


def _build_battery_report(summary: dict, output_path: Path) -> None:
    eval_results = summary.get("eval_results", {})
    tax_agg = summary.get("taxonomy_aggregate", {})

    policies = sorted(eval_results.keys())
    all_taxonomies = set()
    for ev in eval_results.values():
        all_taxonomies.update(ev.get("per_taxonomy", {}).keys())
    taxonomies = sorted(all_taxonomies)

    def _cell_color(val: float | None) -> str:
        if val is None:
            return "background-color: #e5e7eb;"
        if val <= 0.5:
            r = 239
            g = int(68 + (val / 0.5) * (163 - 68))
            b = 68
        else:
            r = int(239 - ((val - 0.5) / 0.5) * (239 - 34))
            g = int(163 + ((val - 0.5) / 0.5) * (197 - 163))
            b = int(68 + ((val - 0.5) / 0.5) * (94 - 68))
        return f"background-color: rgb({r},{g},{b}); color: {'#fff' if val < 0.4 else '#000'};"

    def _heatmap_table(metric: str) -> str:
        rows = []
        for policy in policies:
            ev = eval_results[policy]
            per_tax = ev.get("per_taxonomy", {})
            cells = []
            for tax in taxonomies:
                td = per_tax.get(tax)
                if td and td["expected"] > 0:
                    val = td[metric]
                    style = _cell_color(val)
                    cells.append(f'<td style="{style} text-align:center; padding:4px 8px; font-size:13px;">{val:.2f}</td>')
                else:
                    cells.append(f'<td style="{_cell_color(None)} text-align:center; padding:4px 8px; font-size:13px;">—</td>')
            agg_val = ev.get(metric, 0)
            style = _cell_color(agg_val)
            rows.append(
                f'<tr><td style="padding:4px 8px; font-weight:500; white-space:nowrap;">{policy}</td>'
                + "".join(cells)
                + f'<td style="{style} text-align:center; padding:4px 8px; font-weight:600;">{agg_val:.3f}</td></tr>'
            )
        tax_headers = "".join(
            f'<th style="padding:4px 6px; text-align:center; font-size:12px; writing-mode:vertical-rl; transform:rotate(180deg); max-width:30px; white-space:nowrap;">{t}</th>'
            for t in taxonomies
        )
        return f"""
        <table style="border-collapse:collapse; margin:16px 0; font-family:system-ui,-apple-system,sans-serif; font-size:13px;">
          <thead><tr>
            <th style="padding:4px 8px; text-align:left;">Policy</th>
            {tax_headers}
            <th style="padding:4px 8px; text-align:center;">Overall</th>
          </tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>"""

    n_pass = sum(1 for ev in eval_results.values() if ev["pass"])
    macro_r = sum(ev["recall"] for ev in eval_results.values()) / len(eval_results) if eval_results else 0
    macro_p = sum(ev["precision"] for ev in eval_results.values()) / len(eval_results) if eval_results else 0
    macro_f = sum(ev["f1"] for ev in eval_results.values()) / len(eval_results) if eval_results else 0

    tax_rows = ""
    for tax in sorted(tax_agg):
        a = tax_agg[tax]
        m, e = a["matched"], a["expected"]
        x = a.get("extracted", m)
        spur = x - m
        p = m / (m + spur) if m + spur > 0 else 0.0
        r = m / e if e > 0 else 0.0
        f = 2 * p * r / (p + r) if p + r > 0 else 0.0
        tax_rows += f"<tr><td style='padding:4px 8px;'>{tax}</td><td style='text-align:right; padding:4px 8px;'>{e}</td><td style='text-align:right; padding:4px 8px;'>{m}</td><td style='text-align:right; padding:4px 8px;'>{p:.3f}</td><td style='text-align:right; padding:4px 8px;'>{r:.3f}</td><td style='text-align:right; padding:4px 8px;'>{f:.3f}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Battery Report — {summary.get('battery', '')} ({summary.get('timestamp', '')})</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 24px; background: #f9fafb; color: #111; }}
  h1 {{ font-size: 20px; margin-bottom: 4px; }}
  h2 {{ font-size: 16px; margin-top: 32px; border-bottom: 1px solid #d1d5db; padding-bottom: 4px; }}
  .summary {{ display: flex; gap: 24px; margin: 12px 0; }}
  .stat {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px 20px; }}
  .stat .label {{ font-size: 12px; color: #6b7280; }}
  .stat .value {{ font-size: 22px; font-weight: 600; }}
  table {{ border-collapse: collapse; }}
  th {{ background: #f3f4f6; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #d1d5db; }}
  td {{ border-bottom: 1px solid #e5e7eb; }}
</style>
</head>
<body>
<h1>Battery Report: {summary.get('battery', '')}</h1>
<p style="color:#6b7280; font-size:13px;">Model: {summary.get('model', '')} &middot; {summary.get('timestamp', '')}</p>

<div class="summary">
  <div class="stat"><div class="label">Evals</div><div class="value">{n_pass}/{len(eval_results)} pass</div></div>
  <div class="stat"><div class="label">Macro Recall</div><div class="value">{macro_r:.3f}</div></div>
  <div class="stat"><div class="label">Macro Precision</div><div class="value">{macro_p:.3f}</div></div>
  <div class="stat"><div class="label">Macro F1</div><div class="value">{macro_f:.3f}</div></div>
</div>

<h2>Per-Taxonomy Aggregate</h2>
<table style="font-size:13px;">
  <thead><tr><th style="padding:4px 8px; text-align:left;">Taxonomy</th><th style="padding:4px 8px; text-align:right;">Expected</th><th style="padding:4px 8px; text-align:right;">Matched</th><th style="padding:4px 8px; text-align:right;">Precision</th><th style="padding:4px 8px; text-align:right;">Recall</th><th style="padding:4px 8px; text-align:right;">F1</th></tr></thead>
  <tbody>{tax_rows}</tbody>
</table>

<h2>F1 Heatmap — Policy × Taxonomy</h2>
{_heatmap_table("f1")}

<h2>Recall Heatmap — Policy × Taxonomy</h2>
{_heatmap_table("recall")}

<h2>Precision Heatmap — Policy × Taxonomy</h2>
{_heatmap_table("precision")}

</body>
</html>"""

    output_path.write_text(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("battery", type=Path, help="Battery config YAML file (e.g. ../batteries/simple.yaml)")
    parser.add_argument("--base-url", required=True, help="LLM API base URL")
    parser.add_argument("--model", default=None, help="Override model from battery config")
    parser.add_argument("-j", "--jobs", type=int, default=6, help="Max parallel jobs (default: 6)")
    parser.add_argument("--threshold-high", type=float, default=0.7, help="Auto-accept threshold (default: 0.7)")
    parser.add_argument("--threshold-low", type=float, default=0.15, help="Discard threshold (default: 0.15)")
    parser.add_argument("--bi-encoder-model", default="all-mpnet-base-v2", help="Bi-encoder model (default: all-mpnet-base-v2)")
    parser.add_argument("--cross-encoder-model", default="cross-encoder/ms-marco-MiniLM-L-12-v2", help="Cross-encoder model (default: cross-encoder/ms-marco-MiniLM-L-12-v2)")
    parser.add_argument("--no-cross-encoder", action="store_true", help="Skip cross-encoder reranking and LLM judge; use RRF score floor instead")
    parser.add_argument("--rrf-min-score", type=float, default=0.01, help="Minimum RRF score for candidates (only used with --no-cross-encoder)")
    parser.add_argument("--classify-taxonomies", default="nist-ai-rmf", help="Taxonomies to classify post-retrieval (comma-separated, empty to disable)")
    args = parser.parse_args()

    battery_path = args.battery if args.battery.is_absolute() else PACKAGE_DIR / args.battery
    if not battery_path.exists():
        print(f"Battery config not found: {battery_path}")
        sys.exit(1)

    config = yaml.safe_load(battery_path.read_text())
    model = args.model or config.get("model")
    if not model:
        print("Error: model not specified (set in battery config or pass --model)")
        sys.exit(1)

    battery_name = battery_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = RUNS_DIR / f"{battery_name}_{timestamp}"
    runs_dir.mkdir(parents=True)

    runs: list[tuple[str, list[Path]]] = []
    for entry in config.get("runs", []):
        name, files = _resolve_run(entry)
        if files:
            runs.append((name, files))

    if not runs:
        print("No runs resolved from battery config")
        sys.exit(1)

    n_groups = sum(1 for _, files in runs if len(files) > 1)
    n_single = len(runs) - n_groups
    name_width = max(len(name) for name, _ in runs)
    print(f"Extract Battery: {battery_name}")
    print(f"  model:          {model}")
    print(f"  bi_encoder:     {args.bi_encoder_model}")
    print(f"  cross_encoder:  {'DISABLED' if args.no_cross_encoder else args.cross_encoder_model}")
    if args.no_cross_encoder:
        print(f"  rrf_min_score:  {args.rrf_min_score}")
    print(f"  threshold_high: {args.threshold_high}")
    print(f"  threshold_low:  {args.threshold_low}")
    print(f"  classify_tax:   {args.classify_taxonomies or 'DISABLED'}")
    print(f"  runs:           {len(runs)} ({n_single} single-doc, {n_groups} multi-doc)")
    print(f"  jobs:           {args.jobs}")
    print(f"  output:         {runs_dir}")
    print()

    t_battery = time.monotonic()
    failed = []
    timings: dict[str, float] = {}

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(
                run_one, files, name, args.base_url, model, runs_dir,
                args.threshold_high, args.threshold_low,
                args.bi_encoder_model, args.cross_encoder_model, name_width,
                args.no_cross_encoder, args.rrf_min_score,
                args.classify_taxonomies,
            ): name
            for name, files in runs
        }
        for future in as_completed(futures):
            name, ok, _, exit_code, elapsed = future.result()
            timings[name] = elapsed
            if not ok:
                failed.append(name)

    elapsed_total = time.monotonic() - t_battery

    # --- Eval ---
    eval_results: dict[str, dict] = {}
    for name, _ in runs:
        if name not in failed:
            ev = run_eval(name, runs_dir)
            if ev is not None:
                eval_results[name] = ev

    # Generate HTML reports for runs without eval
    for name, _ in runs:
        if name not in failed and name not in eval_results:
            extraction_path = runs_dir / name / "risk-extraction.json"
            if extraction_path.exists():
                try:
                    from concorde_policy_mapper.extract.report import build_risk_extraction_report
                    data = json.loads(extraction_path.read_text())
                    build_risk_extraction_report(data, runs_dir / name / "risk-extraction.html")
                except Exception as e:
                    _locked_print(f"  [{name}] Warning: could not generate HTML report: {e}")

    # --- Summary ---
    print(f"\n{'═' * 60}")
    print(f"Extract battery complete: {len(runs) - len(failed)}/{len(runs)} succeeded in {_fmt_elapsed(elapsed_total)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")

    succeeded = [name for name, _ in runs if name not in failed]
    if succeeded:
        has_evals = bool(eval_results)
        header = f"{'Name':<{name_width}}  {'Risks':>6}  {'Auto':>5}  {'Judge':>6}  {'Filter':>7}  {'Time':>8}"
        separator = f"{'─' * name_width}  {'─' * 6}  {'─' * 5}  {'─' * 6}  {'─' * 7}  {'─' * 8}"
        if has_evals:
            header += f"  {'Recall':>7}  {'Prec':>7}  {'Eval':>6}"
            separator += f"  {'─' * 7}  {'─' * 7}  {'─' * 6}"
        print(f"\n{header}")
        print(separator)
        for name in succeeded:
            result_path = runs_dir / name / "risk-extraction.json"
            if result_path.exists():
                data = json.loads(result_path.read_text())
                n_risks = len(data.get("risks", []))
                stats = data.get("retrieval_stats", {})
                auto = stats.get("auto_accepted", 0)
                judged = stats.get("llm_judged", 0)
                filtered = stats.get("grounding_filtered", 0)
                elapsed = timings.get(name, 0)
                row = f"{name:<{name_width}}  {n_risks:>6}  {auto:>5}  {judged:>6}  {filtered:>7}  {_fmt_elapsed(elapsed):>8}"
                if has_evals:
                    ev = eval_results.get(name)
                    if ev:
                        status = "PASS" if ev["pass"] else "FAIL"
                        row += f"  {ev['recall']:>7.3f}  {ev['precision']:>7.3f}  {status:>6}"
                    else:
                        row += f"  {'—':>7}  {'—':>7}  {'—':>6}"
                print(row)

    if eval_results:
        n_pass = sum(1 for ev in eval_results.values() if ev["pass"])
        print(f"\nEvals: {n_pass}/{len(eval_results)} passed")

        # Per-taxonomy aggregate
        tax_agg: dict[str, dict[str, int]] = {}
        for ev in eval_results.values():
            for tax, td in ev.get("per_taxonomy", {}).items():
                agg = tax_agg.setdefault(tax, {"expected": 0, "extracted": 0, "matched": 0})
                agg["expected"] += td["expected"]
                agg["extracted"] += td["extracted"]
                agg["matched"] += td["matched"]

        if tax_agg:
            tw = max(len(t) for t in tax_agg)
            tw = max(tw, 10)
            print(f"\n{'Taxonomy':<{tw}}  {'Expect':>6}  {'Match':>5}  {'Prec':>7}  {'Recall':>7}  {'F1':>7}")
            print(f"{'─' * tw}  {'─' * 6}  {'─' * 5}  {'─' * 7}  {'─' * 7}  {'─' * 7}")
            for tax in sorted(tax_agg):
                a = tax_agg[tax]
                m, e, x = a["matched"], a["expected"], a["extracted"]
                spur = x - m
                p = m / (m + spur) if m + spur > 0 else 0.0
                r = m / e if e > 0 else 0.0
                f = 2 * p * r / (p + r) if p + r > 0 else 0.0
                print(f"{tax:<{tw}}  {e:>6}  {m:>5}  {p:>7.3f}  {r:>7.3f}  {f:>7.3f}")

        battery_summary = {
            "battery": battery_name,
            "model": model,
            "timestamp": timestamp,
            "eval_results": {name: ev for name, ev in eval_results.items()},
            "taxonomy_aggregate": {
                tax: {
                    **a,
                    "precision": round(a["matched"] / (a["matched"] + a["extracted"] - a["matched"]) if a["matched"] + a["extracted"] - a["matched"] > 0 else 0.0, 3),
                    "recall": round(a["matched"] / a["expected"] if a["expected"] > 0 else 0.0, 3),
                }
                for tax, a in tax_agg.items()
            },
        }
        summary_path = runs_dir / "battery-summary.json"
        summary_path.write_text(json.dumps(battery_summary, indent=2))

        try:
            _build_battery_report(battery_summary, runs_dir / "battery-summary.html")
            print(f"Battery report: {runs_dir / 'battery-summary.html'}")
        except Exception as e:
            _locked_print(f"Warning: could not generate battery HTML report: {e}")

    print(f"\nOutput: {runs_dir}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
