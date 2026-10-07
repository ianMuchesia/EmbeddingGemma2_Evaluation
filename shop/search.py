"""Answer shop questions by matching them to products, no LLM involved.

Usage:
    python -m shop.search                       # interactive
    python -m shop.search "how much is the iphone 15"
"""
import json
import re
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DEFAULT_MODEL = "google/embeddinggemma-2"
# Below this meaning score we say "not found". It depends on the model, so
# re-tune it when you change models. For embeddinggemma-2 we measured:
# real matches 0.69-0.73, "do you sell bicycles" 0.575 (on the old 10-product
# catalog; eval/run.py reports the best cutoff for the current one).
DEFAULT_THRESHOLD = 0.65
# How much an exact product-name match can add on top of the meaning score.
DEFAULT_NAME_BONUS = 0.10


def load_products(path=DATA_DIR / "products.json"):
    return json.loads(Path(path).read_text())


def product_text(p):
    """The text that gets embedded for a product (same for every search setup)."""
    return f"{p['name']}. {p['description']}"


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def name_match(query, name):
    """Fraction of the product name's words that appear in the question."""
    name_tokens = tokens(name)
    return len(name_tokens & tokens(query)) / len(name_tokens)


class ShopSearch:
    def __init__(self, products, model_name=DEFAULT_MODEL, model=None,
                 threshold=DEFAULT_THRESHOLD, name_bonus=DEFAULT_NAME_BONUS):
        """Pass `model` to reuse an already loaded SentenceTransformer."""
        self.products = products
        self.model_name = model_name
        self.threshold = threshold
        self.name_bonus = name_bonus
        self.model = model or SentenceTransformer(model_name)
        # Embed every product once, up front. A real site would save these to disk.
        self.product_vecs = self.model.encode_document([product_text(p) for p in products])

    def search(self, query):
        """Rank every product for the question and build a templated answer."""
        meaning = self.model.similarity(self.model.encode_query(query), self.product_vecs)[0]

        matches = []
        for p, m in zip(self.products, meaning.tolist()):
            nm = name_match(query, p["name"])
            matches.append({**p, "meaning": m, "name_match": nm, "final": m + self.name_bonus * nm})
        matches.sort(key=lambda r: r["final"], reverse=True)

        best = matches[0]
        found = best["meaning"] >= self.threshold
        if found:
            stock = f"{best['stock']} in stock" if best["stock"] else "currently out of stock"
            answer = f"{best['name']} costs KSh {best['price']:,} ({stock}). {best['description']}"
        else:
            answer = "Sorry, I couldn't find that in our shop."

        return {"query": query, "found": found, "answer": answer,
                "threshold": self.threshold, "matches": matches}


def print_result(result):
    print("  top matches (final / meaning):")
    for r in result["matches"][:3]:
        print(f"    {r['final']:.3f} / {r['meaning']:.3f}  {r['name']}")
    print(result["answer"])


if __name__ == "__main__":
    shop = ShopSearch(load_products())
    if len(sys.argv) > 1:
        print_result(shop.search(" ".join(sys.argv[1:])))
    else:
        while (q := input("\nAsk the shop (empty to quit): ").strip()):
            print_result(shop.search(q))
