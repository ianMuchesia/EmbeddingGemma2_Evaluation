"""Turn the benchmark results into charts (results/*.png).

    python -m eval.plots

Reads results/results.json (from eval.run) and, if present, results/memory.json
(from eval.memory). Writes:
    quality.png   answer quality per setup
    by_type.png   top-1 accuracy per question type, per setup
    speed.png     query latency per setup
    cost.png      disk, memory, indexing time and vector size per model
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write files, no window
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"

# One colour per model family (validated colour-blind-safe order). The three
# mixes of a model share its colour; the row label says which mix it is.
FAMILY_COLORS = {"keyword": "#2a78d6", "minilm": "#eb6834", "me5": "#1baf7a", "gemma": "#eda100", "ours": "#e87ba4"}
FAMILY_LABELS = {"keyword": "Keyword only (no model)", "minilm": "MiniLM (Typesense built-in)",
                 "me5": "Multilingual E5 (Typesense built-in)", "gemma": "EmbeddingGemma 2 (Python)"}
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CATALOG_SIZE_FOR_VECTORS = 10_000

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": TEXT, "axes.labelcolor": TEXT_2, "xtick.color": TEXT_2, "ytick.color": TEXT,
    "axes.edgecolor": GRID, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=RESULTS_DIR / "results.json")
    parser.add_argument("--memory", type=Path, default=RESULTS_DIR / "memory.json")
    args = parser.parse_args()

    report = json.loads(args.results.read_text())
    memory = json.loads(args.memory.read_text()) if args.memory.exists() else None
    out_dir = args.results.parent

    quality_chart(report, out_dir / "quality.png")
    type_heatmap(report, out_dir / "by_type.png")
    speed_chart(report, out_dir / "speed.png")
    cost_chart(report, memory, out_dir / "cost.png")


# ---------------------------------------------------------------- charts

def quality_chart(report, out):
    setups = report["setups"]
    summaries = [s["summary"] for s in setups]
    rows = [(s["label"], FAMILY_COLORS[s["family"]]) for s in setups]
    bar_panels(rows, [
        ("Top-1 accuracy", [m["top1"] for m in summaries], "{:.0%}", 1.15),
        ("Right product in top 3", [m["recall_at_3"] for m in summaries], "{:.0%}", 1.15),
        ("MRR@5", [m["mrr_at_5"] for m in summaries], "{:.2f}", 1.15),
        ("End-to-end (incl. 'not found')", [m["not_found"]["end_to_end_accuracy"] for m in summaries], "{:.0%}", 1.15),
    ], title="Search quality",
        subtitle=f"{report['n_products']} products · {report['n_questions']} questions · higher is better",
        out=out)


def speed_chart(report, out):
    setups = report["setups"]
    rows = [(s["label"], FAMILY_COLORS[s["family"]]) for s in setups]
    bar_panels(rows, [
        ("Query latency p50 (ms)", [s["summary"]["latency_ms"]["p50"] for s in setups], "{:.1f}", None),
        ("Query latency p95 (ms)", [s["summary"]["latency_ms"]["p95"] for s in setups], "{:.1f}", None),
    ], title="Search speed", subtitle=f"{machine(report)} · lower is better · includes embedding the question",
        out=out)


def cost_chart(report, memory, out):
    """One row per model: what it costs to run, whatever mix it is used with."""
    families = []
    for setup in report["setups"]:
        family = "gemma" if setup["family"] == "ours" else setup["family"]
        if family not in [f for f, _ in families]:
            families.append((family, setup))

    def memory_added(family):
        return (memory or {}).get("families", {}).get(family, {}).get("added_mb")

    def vectors_mb(setup):
        dim = setup["resources"]["model"].get("dim")
        return dim * 4 * CATALOG_SIZE_FOR_VECTORS / 1e6 if dim else None

    def index_s(setup):
        timings = setup["resources"]["index_timings_s"]
        return timings["embed_s"] + timings["import_s"]

    rows = [(FAMILY_LABELS[f], FAMILY_COLORS[f]) for f, _ in families]
    bar_panels(rows, [
        ("Model on disk (MB)", [s["resources"]["model"].get("disk_mb") for _, s in families], "{:,.0f}", None),
        ("Memory added (MB)", [memory_added(f) for f, _ in families], "{:,.0f}", None),
        (f"Index {report['n_products']} products (s)", [index_s(s) for _, s in families], "{:.1f}", None),
        (f"Vectors for {CATALOG_SIZE_FOR_VECTORS:,} products (MB)", [vectors_mb(s) for _, s in families],
         "{:.1f}", None),
    ], title="Cost per model",
        subtitle=f"{machine(report)} · lower is better · memory from eval.memory (n/a = not measured yet)",
        out=out)


def type_heatmap(report, out):
    """Top-1 accuracy per question type, plus how many 'we don't sell that' questions were rejected."""
    setups = report["setups"]
    types = sorted({t for s in setups for t in s["summary"]["by_type"]})
    first = setups[0]
    n_negative = sum(1 for q in first["questions"] if not q["expected"])
    column_labels = ([f"{t}\n(n={first['summary']['by_type'][t]['n']})" for t in types]
                     + [f"negative\nrejected (n={n_negative})"])
    grid = [[s["summary"]["by_type"].get(t, {}).get("top1") for t in types]
            + [s["summary"]["not_found"]["negatives_rejected"]] for s in setups]

    fig, ax = plt.subplots(figsize=(1.35 * len(column_labels) + 3.6, 0.5 * len(setups) + 2.2))
    cmap = LinearSegmentedColormap.from_list("sequential", SEQUENTIAL)
    ax.imshow([[v or 0 for v in row] for row in grid], cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i, row in enumerate(grid):
        for j, value in enumerate(row):
            ax.text(j, i, "n/a" if value is None else f"{value:.0%}", ha="center", va="center", fontsize=9,
                    color="#ffffff" if (value or 0) >= 0.55 else TEXT)

    ax.set_xticks(range(len(column_labels)), column_labels, fontsize=9)
    ax.set_yticks(range(len(setups)), [s["label"] for s in setups])
    ax.set_xticks([x - 0.5 for x in range(1, len(column_labels))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(setups))], minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    add_titles(fig, "Top-1 accuracy by question type",
               "last column: share of 'we don't sell that' questions answered 'not found' at each setup's best cutoff")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, out)


# --------------------------------------------------------------- helpers

def bar_panels(rows, panels, title, subtitle, out):
    """Small horizontal bar charts side by side: rows on the y-axis, the value printed on each bar.

    rows:   [(label, colour)]
    panels: [(title, values, number format, x-axis max or None)]
    """
    labels = [label for label, _ in rows]
    colors = [color for _, color in rows]
    fig, axes = plt.subplots(1, len(panels), figsize=(3.3 * len(panels) + 3.2, 0.42 * len(rows) + 1.9),
                             sharey=True, squeeze=False)
    y = list(range(len(rows)))[::-1]  # first row at the top
    for ax, (panel_title, values, fmt, xmax) in zip(axes[0], panels):
        shown = [v or 0 for v in values]
        top = xmax or (max(shown) * 1.3 if any(shown) else 1)
        ax.barh(y, shown, height=0.66, color=colors, edgecolor=SURFACE, linewidth=2)
        for yi, value in zip(y, values):
            ax.text((value or 0) + top * 0.02, yi, "n/a" if value is None else fmt.format(value),
                    va="center", fontsize=8.5, color=TEXT)
        ax.set_xlim(0, top)
        ax.set_title(panel_title, loc="left")
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
    axes[0][0].set_yticks(y, labels)

    add_titles(fig, title, subtitle)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, out)


def add_titles(fig, title, subtitle):
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.01, 0.905, subtitle, ha="left", fontsize=9, color=TEXT_2)


def machine(report):
    env = report["environment"]
    return f"{env['cpu']} · {env['cores']} cores · {'GPU' if env['cuda_available'] else 'CPU only'}"


def save(fig, out):
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
