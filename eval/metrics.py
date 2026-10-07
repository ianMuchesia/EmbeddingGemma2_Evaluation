"""Scoring: how good were a setup's answers?

Each question produces a row; `summarize` turns the rows into the numbers
shown in the charts.
"""
from statistics import mean, median


def score_question(question, result_ids, confidence, latency_ms):
    """One row of results for one question."""
    expected = question["expected"]
    rank = next((i for i, pid in enumerate(result_ids) if pid in expected), None)
    return {
        "q": question["q"],
        "type": question["type"],
        "expected": expected,
        "results": result_ids,
        "confidence": round(confidence, 4),
        "latency_ms": round(latency_ms, 2),
        "top1": rank == 0,
        "recall_at_3": rank is not None and rank < 3,
        "reciprocal_rank": 0.0 if rank is None else 1 / (rank + 1),
    }


def summarize(rows):
    answerable = [r for r in rows if r["expected"]]
    return {
        "top1": mean(r["top1"] for r in answerable),
        "recall_at_3": mean(r["recall_at_3"] for r in answerable),
        "mrr_at_5": mean(r["reciprocal_rank"] for r in answerable),
        "by_type": accuracy_by_type(answerable),
        "not_found": best_cutoff(rows),
        "latency_ms": latency_stats(rows),
    }


def accuracy_by_type(rows):
    by_type = {}
    for question_type in sorted({r["type"] for r in rows}):
        group = [r for r in rows if r["type"] == question_type]
        by_type[question_type] = {"n": len(group),
                                  "top1": mean(r["top1"] for r in group),
                                  "recall_at_3": mean(r["recall_at_3"] for r in group)}
    return by_type


def latency_stats(rows):
    times = sorted(r["latency_ms"] for r in rows)
    p95_index = min(len(times) - 1, round(0.95 * (len(times) - 1)))
    return {"p50": median(times), "p95": times[p95_index], "mean": mean(times)}


def best_cutoff(rows):
    """Find the confidence cutoff that handles the most questions correctly.

    Correct means: the question should match, the top result is right and
    confidence >= cutoff; or the question should match nothing and
    confidence < cutoff ("not found"). The cutoff is tuned on the same
    questions it is scored on, so the result is optimistic.
    """
    candidates = sorted({0.0, float("inf")} | {r["confidence"] for r in rows})
    scores = [correct_at_cutoff(rows, c) for c in candidates]
    best = scores.index(max(scores))

    # Put the cutoff halfway between the last rejected score and the first
    # accepted one: same result here, more margin for new questions.
    cutoff = candidates[best]
    if 0 < best and cutoff != float("inf"):
        cutoff = (candidates[best - 1] + cutoff) / 2

    answerable = [r for r in rows if r["expected"]]
    unanswerable = [r for r in rows if not r["expected"]]
    return {
        "cutoff": None if cutoff == float("inf") else round(cutoff, 4),
        "end_to_end_accuracy": scores[best] / len(rows),
        "negatives_rejected": (sum(r["confidence"] < cutoff for r in unanswerable) / len(unanswerable)
                               if unanswerable else None),
        "positives_answered_correctly": (sum(r["confidence"] >= cutoff and r["top1"] for r in answerable)
                                         / len(answerable)),
    }


def correct_at_cutoff(rows, cutoff):
    return sum((r["confidence"] >= cutoff and r["top1"]) if r["expected"] else r["confidence"] < cutoff
               for r in rows)
