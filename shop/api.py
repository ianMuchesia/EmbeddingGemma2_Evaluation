"""HTTP API: the shop search, plus the setup comparison used by the compare page.

Run:  uvicorn shop.api:app --reload --port 8000
Try:  http://localhost:8000/api/search?q=how%20much%20is%20the%20iphone%2015
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from shop.compare import Comparer
from shop.search import ShopSearch, load_model, load_products

# Load EmbeddingGemma once; the shop search and the compare page share it.
model = load_model()
shop = ShopSearch(load_products(), model=model)
comparer = Comparer(shop.products, model)


@asynccontextmanager
async def lifespan(app):
    comparer.start()  # indexes the compare setups in a background thread; the shop search works meanwhile
    yield


app = FastAPI(title="Shop search", lifespan=lifespan)


@app.get("/api/search")
def search(q: str = Query(..., min_length=1, description="The customer's question")):
    return shop.search(q)


@app.get("/api/products")
def products():
    return shop.products


@app.get("/api/compare/info")
def compare_info():
    """Indexing status and the list of setups (with benchmark scores, if any)."""
    return comparer.info()


@app.get("/api/compare/questions")
def compare_questions():
    """The benchmark questions, used as suggestions on the compare page."""
    return comparer.questions


@app.get("/api/compare")
def compare(q: str = Query(..., min_length=1), setups: str = Query(..., description="comma-separated setup names")):
    return comparer.compare(q, setups.split(","))
