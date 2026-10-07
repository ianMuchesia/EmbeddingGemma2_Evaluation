"""Live side-by-side comparison of the benchmark setups, for the compare page.

The setups are indexed in a background thread when the API starts, so the shop
page works immediately; the compare page shows progress until they are ready.
Typesense collections use the "app" prefix so they don't clash with the
benchmark's ("bench").
"""
import json
import threading
import time

from eval.run import RESULTS_FILE
from eval.setups import SETUP_NAMES, SPECS, LoadedModel, build_setups
from eval.typesense_client import Typesense
from shop.search import DATA_DIR, DEFAULT_MODEL

TOP_K = 5


class Comparer:
    def __init__(self, products, gemma_model):
        self.products = products
        self.products_by_id = {p["id"]: p for p in products}
        self.gemma = LoadedModel(DEFAULT_MODEL, st=gemma_model)
        self.questions = json.loads((DATA_DIR / "eval_questions.json").read_text())
        self.expected_by_question = {q["q"].lower(): q["expected"] for q in self.questions}
        self.benchmark = load_benchmark()

        self.status = "starting"   # starting -> indexing -> ready | error
        self.message = ""
        self.ready = {}            # setup name -> indexed setup

    def start(self):
        threading.Thread(target=self._index_all, daemon=True).start()

    def _index_all(self):
        typesense = Typesense()
        try:
            typesense.request("GET", "/health")
            names = SETUP_NAMES
        except Exception:
            self.message = "Typesense is not running (docker compose up -d), so only our search is available."
            names = [n for n in SETUP_NAMES if not n.startswith("ts-")]

        self.status = "indexing"
        try:
            for setup in build_setups(names, typesense, prefix="app", gemma=self.gemma):
                setup.index(self.products)
                self.ready[setup.name] = setup
            self.status = "ready"
        except Exception as error:
            self.status = "error"
            self.message = f"Indexing failed: {error}"

    def info(self):
        """Status plus every setup, with its benchmark scores if a benchmark has been run."""
        setups = []
        for spec in SPECS:
            scores = self.benchmark.get(spec.name, {})
            setups.append({"name": spec.name, "label": spec.label, "family": spec.family,
                           "ready": spec.name in self.ready, **scores})
        return {"status": self.status, "message": self.message, "ready": len(self.ready),
                "total": len(SPECS), "setups": setups, "defaults": default_selection(setups)}

    def compare(self, query, names):
        expected = self.expected_by_question.get(query.strip().lower())
        results = []
        for name in names:
            setup = self.ready.get(name)
            if setup is None:
                continue
            card = {"name": name, "label": setup.label, "family": setup.spec.family}
            start = time.perf_counter()
            try:
                ids, confidence = setup.search(query, TOP_K)
            except Exception as error:
                # e.g. Typesense restarting, or its collections deleted by eval.memory
                results.append({**card, "error": f"{error}. Restart the API to re-index."})
                continue
            latency_ms = (time.perf_counter() - start) * 1000
            cutoff = self.benchmark.get(name, {}).get("cutoff")
            results.append({
                **card,
                "latency_ms": round(latency_ms, 1),
                "confidence": round(confidence, 4),
                "cutoff": cutoff,
                "found": None if cutoff is None else confidence >= cutoff,
                "products": [{**self.products_by_id[pid], "correct": None if expected is None else pid in expected}
                             for pid in ids],
            })
        return {"query": query, "expected": expected, "results": results}


def load_benchmark():
    """Per setup: best 'not found' cutoff and headline scores from results/results.json."""
    if not RESULTS_FILE.exists():
        return {}
    report = json.loads(RESULTS_FILE.read_text())
    return {s["name"]: {"cutoff": s["summary"]["not_found"]["cutoff"],
                        "top1": s["summary"]["top1"],
                        "end_to_end": s["summary"]["not_found"]["end_to_end_accuracy"]}
            for s in report["setups"]}


def default_selection(setups):
    """Keyword search, our search, and each model's best mix by end-to-end score (or its default mix)."""
    best = {}
    for setup in setups:
        family = setup["family"]
        score = setup.get("end_to_end", -1)
        if family not in best or score > best[family][0]:
            best[family] = (score, setup["name"])
    if all(score < 0 for score, _ in best.values()):  # no benchmark yet: use Typesense's default mix
        return [s["name"] for s in setups if s["family"] in ("keyword", "ours") or s["name"].endswith("-mix30")]
    return [name for _, name in best.values()]
