"""Measure how much memory each embedding model needs, one model at a time.

    python -m eval.memory          # writes results/memory.json

Typesense (keyword only, MiniLM, multilingual E5): start a brand-new, empty
Typesense container for each model (port 8109, data in memory, the already
downloaded models mounted read-only), then compare the Typesense process's
memory (RSS, read from /proc) before and after indexing the catalog with that
model and running a few searches. The container is removed afterwards.

A fresh server matters: a restarted one replays its history (creating and
dropping earlier collections, loading their models), which inflates the
"before" reading. `docker stats` isn't used either: it includes the OS file
cache. Your main Typesense (port 8108) and the API are not touched.

EmbeddingGemma: load it in a fresh Python process and record that process's
peak memory after embedding the catalog and a few questions.
"""
import argparse
import json
import re
import resource
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from shop.search import DATA_DIR, DEFAULT_MODEL, load_products
from eval import measure
from eval.setups import SPECS_BY_NAME, build_setups
from eval.typesense_client import TYPESENSE_KEY, Typesense

MEMORY_FILE = measure.ROOT / "results" / "memory.json"
QUESTIONS_TO_ASK = 10
# One representative setup per Typesense family; the mix doesn't change memory.
TYPESENSE_FAMILIES = {"keyword": "ts-keyword", "minilm": "ts-minilm-mix30", "me5": "ts-me5-mix30"}
TEST_CONTAINER = "embeddinggemma-memtest"
TEST_PORT = 8109


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--child", help=argparse.SUPPRESS)  # internal: measure this model in-process
    args = parser.parse_args()
    if args.child:
        print(json.dumps(measure_in_this_process(args.child)))
        return

    products = load_products()
    questions = json.loads((DATA_DIR / "eval_questions.json").read_text())[:QUESTIONS_TO_ASK]

    families = {}
    for family, setup_name in TYPESENSE_FAMILIES.items():
        print(f"\n== Typesense: {SPECS_BY_NAME[setup_name].label} ==", flush=True)
        families[family] = measure_typesense(setup_name, products, questions)
        print(f"  added {families[family]['added_mb']:.0f} MB "
              f"(peak +{families[family]['peak_added_mb']:.0f} MB)", flush=True)

    print(f"\n== Python process: {DEFAULT_MODEL} ==", flush=True)
    families["gemma"] = measure_in_fresh_process(DEFAULT_MODEL)
    print(f"  added {families['gemma']['added_mb']:.0f} MB (peak)", flush=True)

    report = {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "environment": measure.environment(), "families": families}
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {MEMORY_FILE}")


# ------------------------------------------------------------- Typesense

def measure_typesense(setup_name, products, questions):
    with fresh_typesense() as typesense:
        before, _ = typesense_process_memory_mb()

        [setup] = build_setups([setup_name], typesense, prefix="mem")
        setup.index(products)
        for question in questions:
            setup.search(question["q"], 5)
        time.sleep(2)  # let memory settle
        after, peak = typesense_process_memory_mb()

    return {"where": "typesense server", "model": SPECS_BY_NAME[setup_name].model,
            "before_mb": before, "after_mb": after, "peak_mb": peak,
            "added_mb": round(after - before, 1), "peak_added_mb": round(peak - before, 1)}


@contextmanager
def fresh_typesense(timeout_s=120):
    """An empty Typesense in a throwaway container, removed on exit."""
    docker = ["docker"]
    subprocess.run(docker + ["rm", "-f", TEST_CONTAINER], capture_output=True)  # leftover from a crash
    subprocess.run(docker + [
        "run", "-d", "--rm", "--name", TEST_CONTAINER, "-p", f"{TEST_PORT}:8108",
        "--tmpfs", "/data",
        "-v", f"{measure.TYPESENSE_DATA / 'models'}:/data/models:ro",
        typesense_image(), "--data-dir", "/data", f"--api-key={TYPESENSE_KEY}",
    ], check=True, capture_output=True)
    try:
        typesense = Typesense(url=f"http://localhost:{TEST_PORT}")
        wait_until_healthy(typesense, timeout_s)
        yield typesense
    finally:
        subprocess.run(docker + ["rm", "-f", TEST_CONTAINER], capture_output=True)


def typesense_image():
    """The same image as docker-compose.yml, so the measurement matches the benchmark."""
    compose = (measure.ROOT / "docker-compose.yml").read_text()
    return re.search(r"image:\s*(\S+)", compose).group(1)


def wait_until_healthy(typesense, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            typesense.request("GET", "/health")
            time.sleep(2)  # let startup allocations settle
            return
        except Exception:
            time.sleep(0.5)
    raise SystemExit(f"test Typesense did not start; check: docker logs {TEST_CONTAINER}")


def typesense_process_memory_mb():
    """(current, peak) resident memory of the test Typesense process, in MB, read from /proc."""
    pid = subprocess.run(["docker", "inspect", "-f", "{{.State.Pid}}", TEST_CONTAINER],
                         check=True, capture_output=True, text=True).stdout.strip()
    fields = dict(line.split(":", 1) for line in open(f"/proc/{pid}/status") if ":" in line)

    def kib_to_mb(field):
        return round(int(fields[field].split()[0]) * 1024 / 1e6, 1)

    return kib_to_mb("VmRSS"), kib_to_mb("VmHWM")


# ---------------------------------------------------------- Python model

def measure_in_fresh_process(model_name):
    """Run this file again as a child process so nothing else is in its memory."""
    result = subprocess.run([sys.executable, "-m", "eval.memory", "--child", model_name],
                            cwd=measure.ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout.strip().splitlines()[-1])


def measure_in_this_process(model_name):
    import torch  # noqa: F401  (imported before the baseline, like in the app)
    from sentence_transformers import SentenceTransformer

    from shop.search import product_text

    baseline = measure.process_memory()
    model = SentenceTransformer(model_name)
    after_load = measure.process_memory()

    model.encode_document([product_text(p) for p in load_products()])
    questions = json.loads((DATA_DIR / "eval_questions.json").read_text())[:QUESTIONS_TO_ASK]
    for question in questions:
        model.encode_query(question["q"])
    after_use = measure.process_memory()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # Linux reports KiB

    return {"where": "python process", "model": model_name,
            "before_mb": measure.to_mb(baseline), "after_load_mb": measure.to_mb(after_load),
            "after_use_mb": measure.to_mb(after_use), "peak_mb": measure.to_mb(peak),
            "added_mb": measure.to_mb(peak - baseline)}


if __name__ == "__main__":
    main()
