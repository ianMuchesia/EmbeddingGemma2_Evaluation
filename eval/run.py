"""Benchmark the search setups on the same questions; write results/results.json.

    docker compose up -d                 # Typesense must be running
    python -m eval.run                   # all setups
    python -m eval.run --setups ts-keyword,py-gemma --repeats 1
    python -m eval.plots                 # charts from the results

For each setup it measures answer quality, "not found" handling, query speed,
indexing time and disk. Memory is measured separately: python -m eval.memory
"""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from shop.search import DATA_DIR, load_products
from eval import measure
from eval.metrics import score_question, summarize
from eval.setups import SETUP_NAMES, build_setups
from eval.typesense_client import Typesense

RESULTS_FILE = measure.ROOT / "results" / "results.json"
TOP_K = 5      # results kept per question
WARMUP = 3     # untimed questions before timing starts


def main():
    args = parse_args()
    products = load_products()
    questions = json.loads((DATA_DIR / "eval_questions.json").read_text())

    typesense = Typesense()
    if any(name.startswith("ts-") for name in args.setups):
        typesense.check_running()
    else:
        typesense = None

    report = start_report(args.out, products, questions, args.repeats, typesense)
    for setup in build_setups(args.setups, typesense):
        add_setup(report, run_setup(setup, products, questions, args.repeats, typesense))
        if typesense:
            report["typesense_disk"] = measure.typesense_disk_usage()
        save(report, args.out)  # after every setup, so a crash keeps the finished ones

    print(f"\nwrote {args.out}")
    print_table(report)


def start_report(path, products, questions, repeats, typesense):
    """A fresh report header that keeps earlier results for setups not re-run now.

    Earlier results are dropped if the products or questions have changed
    since, because they would not be comparable.
    """
    report = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": measure.environment(typesense),
        "dataset": dataset_fingerprint(products, questions),
        "n_products": len(products),
        "n_questions": len(questions),
        "top_k": TOP_K,
        "repeats": repeats,
        "setups": [],
    }
    if path.exists():
        previous = json.loads(path.read_text())
        if previous.get("dataset") == report["dataset"]:
            # Setups that no longer exist (renamed or removed) are dropped.
            report["setups"] = [s for s in previous.get("setups", []) if s["name"] in SETUP_NAMES]
            report["typesense_disk"] = previous.get("typesense_disk")
    return report


def dataset_fingerprint(products, questions):
    """Short hash of the catalog and questions, to tell whether old results still apply."""
    data = json.dumps([products, questions], sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()[:12]


def add_setup(report, result):
    """Add or replace one setup's results, keeping the standard setup order."""
    others = [s for s in report["setups"] if s["name"] != result["name"]]
    report["setups"] = sorted(others + [result], key=lambda s: SETUP_NAMES.index(s["name"]))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--setups", default=",".join(SETUP_NAMES),
                        help=f"comma-separated subset of: {', '.join(SETUP_NAMES)}")
    parser.add_argument("--repeats", type=int, default=3, help="timed runs per question; the median is kept")
    parser.add_argument("--out", type=Path, default=RESULTS_FILE)
    args = parser.parse_args()

    args.setups = args.setups.split(",")
    unknown = set(args.setups) - set(SETUP_NAMES)
    if unknown:
        parser.error(f"unknown setups {sorted(unknown)}; choose from {SETUP_NAMES}")
    return args


def run_setup(setup, products, questions, repeats, typesense):
    """Index the catalog with one setup, ask every question, and summarize."""
    print(f"\n== {setup.label} ==", flush=True)

    timings = setup.index(products)
    print("  indexed: " + ", ".join(f"{step} {secs:.1f}s" for step, secs in timings.items()), flush=True)

    rows = ask_all(setup, questions, repeats)
    summary = summarize(rows)
    print(f"  top-1 {summary['top1']:.0%} · top-3 {summary['recall_at_3']:.0%} · "
          f"end-to-end {summary['not_found']['end_to_end_accuracy']:.0%} · "
          f"p50 {summary['latency_ms']['p50']:.1f} ms", flush=True)

    return {
        "name": setup.name,
        "label": setup.label,
        "family": setup.spec.family,
        "meaning_weight": setup.spec.meaning_weight,
        "summary": summary,
        "resources": resources(setup, products, timings),
        "questions": rows,
    }


def ask_all(setup, questions, repeats):
    """Ask every question `repeats` times; keep the median latency."""
    for question in questions[:WARMUP]:  # first queries are slower (caches, lazy setup)
        setup.search(question["q"], TOP_K)

    rows = []
    for question in questions:
        latencies = []
        for _ in range(repeats):
            start = time.perf_counter()
            result_ids, confidence = setup.search(question["q"], TOP_K)
            latencies.append((time.perf_counter() - start) * 1000)
        rows.append(score_question(question, result_ids, confidence, median(latencies)))
    return rows


def resources(setup, products, timings):
    model = setup.model_info()
    info = {"index_timings_s": {step: round(secs, 3) for step, secs in timings.items()}, "model": model}
    if "dim" in model:
        info["raw_vectors_mb"] = measure.to_mb(len(products) * model["dim"] * 4)  # float32
    return info


def save(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")


def print_table(report):
    header = f"{'setup':<44} {'top-1':>6} {'top-3':>6} {'MRR':>5} {'e2e':>5} {'p50 ms':>7} {'index s':>8}"
    print("\n" + header + "\n" + "-" * len(header))
    for setup in report["setups"]:
        s = setup["summary"]
        t = setup["resources"]["index_timings_s"]
        print(f"{setup['label']:<44} {s['top1']:>6.0%} {s['recall_at_3']:>6.0%} {s['mrr_at_5']:>5.2f} "
              f"{s['not_found']['end_to_end_accuracy']:>5.0%} {s['latency_ms']['p50']:>7.1f} "
              f"{t['embed_s'] + t['import_s']:>8.1f}")


if __name__ == "__main__":
    main()
