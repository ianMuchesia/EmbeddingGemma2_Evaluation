"""The search setups being compared.

Every setup indexes the same catalog, then answers each question with its
top-k product ids plus a confidence score. The confidence is the best cosine
similarity it saw (or simply hits / no hits for keyword search); the metrics
use it to decide when to answer "not found".

Typesense hybrid search blends a keyword rank and a meaning (vector) rank.
Its default gives meaning 30% of the weight; each model is also tried at 70%
and with meaning only, so the models are compared fairly and not just
Typesense's default blend.
"""
import time
from dataclasses import dataclass

from shop.search import DEFAULT_MODEL, ShopSearch, load_model, product_text
from eval import measure

TEXT_FIELDS = "name,brand,category,description"
BASE_FIELDS = [
    {"name": "name", "type": "string"},
    {"name": "brand", "type": "string", "facet": True},
    {"name": "category", "type": "string", "facet": True},
    {"name": "description", "type": "string"},
    {"name": "price", "type": "float"},
    {"name": "stock", "type": "int32"},
]
# How many nearest neighbours the vector half of a search looks at.
VECTOR_K = 50
MEANING_ONLY = 1.0


# ------------------------------------------------------------ the setups

@dataclass(frozen=True)
class SetupSpec:
    name: str              # short id used in results.json and on the command line
    label: str             # readable name for charts and the UI
    family: str            # keyword | minilm | me5 | gemma | ours (one chart colour each)
    model: str = None      # embedding model, if any
    meaning_weight: float = None  # Typesense hybrid weight of the meaning rank; 1.0 = meaning only


EMBEDDING_MODELS = [
    # family, model, label
    ("minilm", "ts/all-MiniLM-L12-v2", "MiniLM"),
    ("me5", "ts/multilingual-e5-small", "Multilingual E5"),
    ("gemma", DEFAULT_MODEL, "EmbeddingGemma 2"),
]
MIXES = [
    # meaning weight, name suffix, label
    (0.3, "mix30", "30% meaning (default)"),
    (0.7, "mix70", "70% meaning"),
    (MEANING_ONLY, "meaning", "meaning only"),
]

SPECS = [SetupSpec("ts-keyword", "Keyword only", "keyword")]
for _family, _model, _model_label in EMBEDDING_MODELS:
    for _weight, _suffix, _mix_label in MIXES:
        SPECS.append(SetupSpec(f"ts-{_family}-{_suffix}", f"{_model_label} · {_mix_label}",
                               _family, _model, _weight))
SPECS.append(SetupSpec("py-gemma", "Our search · EmbeddingGemma 2", "ours", DEFAULT_MODEL))

SETUP_NAMES = [spec.name for spec in SPECS]
SPECS_BY_NAME = {spec.name: spec for spec in SPECS}


# ------------------------------------------------------------------ base

class Setup:
    uses_typesense = False

    def __init__(self, spec):
        self.spec = spec
        self.name = spec.name
        self.label = spec.label

    def index(self, products):
        """Index the catalog; return timings in seconds: create_s, embed_s, import_s."""
        raise NotImplementedError

    def search(self, query, k):
        """Return (top-k product ids, confidence)."""
        raise NotImplementedError

    def model_info(self):
        """What embedding model this setup uses and what it costs. Empty if none."""
        return {}


# ------------------------------------------------------------ Typesense

class TypesenseSetup(Setup):
    """Keyword search in its own Typesense collection. Subclasses add vectors."""

    uses_typesense = True

    def __init__(self, spec, typesense, prefix):
        super().__init__(spec)
        self.typesense = typesense
        self.collection = f"{prefix}_{spec.name.replace('-', '_')}"

    def index(self, products):
        self.typesense.drop_collection(self.collection)

        start = time.perf_counter()
        self.typesense.create_collection({"name": self.collection, "fields": BASE_FIELDS + self.vector_fields()})
        create_s = time.perf_counter() - start

        documents, embed_s = self.documents(products)  # embed_s may come from a cache

        start = time.perf_counter()
        self.typesense.import_documents(self.collection, documents)
        import_s = time.perf_counter() - start

        return {"create_s": create_s, "embed_s": embed_s, "import_s": import_s}

    def search(self, query, k):
        params = {"collection": self.collection, "q": query, "query_by": TEXT_FIELDS,
                  "per_page": k, "exclude_fields": "embedding", **self.vector_params(query)}
        hits = self.typesense.search(params)
        return [hit["document"]["id"] for hit in hits], self.confidence(hits)

    # Hooks for the vector setups below; plain keyword search uses none of them.
    def vector_fields(self):
        return []

    def documents(self, products):
        """Documents to import, and seconds spent computing embeddings for them."""
        return products, 0.0

    def vector_params(self, query):
        return {}

    def confidence(self, hits):
        return 1.0 if hits else 0.0


class TypesenseVectorSetup(TypesenseSetup):
    """Shared logic for setups that search by meaning as well as keywords."""

    @property
    def meaning_only(self):
        return self.spec.meaning_weight >= MEANING_ONLY

    def vector_query(self, vector=""):
        if self.meaning_only:
            return f"embedding:([{vector}], k:{VECTOR_K})"
        return f"embedding:([{vector}], k:{VECTOR_K}, alpha:{self.spec.meaning_weight})"

    def confidence(self, hits):
        return best_similarity(hits)


class TypesenseBuiltinModel(TypesenseVectorSetup):
    """Typesense embeds products and questions itself with a built-in model."""

    DIM = 384  # both built-in models used here produce 384 numbers per text

    def vector_fields(self):
        return [{"name": "embedding", "type": "float[]",
                 "embed": {"from": ["name", "description"], "model_config": {"model_name": self.spec.model}}}]

    def vector_params(self, query):
        query_by = "embedding" if self.meaning_only else TEXT_FIELDS + ",embedding"
        return {"query_by": query_by, "vector_query": self.vector_query()}

    def model_info(self):
        return {"model": self.spec.model, "runs_in": "typesense server", "dim": self.DIM,
                "disk_mb": measure.to_mb(measure.typesense_model_size(self.spec.model))}


class TypesenseOwnModel(TypesenseVectorSetup):
    """We compute the vectors ourselves (EmbeddingGemma) and Typesense searches them."""

    def __init__(self, spec, typesense, prefix, model):
        super().__init__(spec, typesense, prefix)
        self.model = model

    def vector_fields(self):
        return [{"name": "embedding", "type": "float[]", "num_dim": self.model.dim}]

    def documents(self, products):
        vectors, embed_s = self.model.encode_products(products)
        return [{**p, "embedding": v.tolist()} for p, v in zip(products, vectors)], embed_s

    def vector_params(self, query):
        vector = ",".join(f"{x:.6f}" for x in self.model.st.encode_query(query).tolist())
        params = {"vector_query": self.vector_query(vector)}
        if self.meaning_only:
            params["q"] = "*"  # no keyword part at all
        return params

    def model_info(self):
        return self.model.info()


def best_similarity(hits):
    """Typesense reports cosine distance (0 = identical); turn the best one into a similarity."""
    distances = [hit["vector_distance"] for hit in hits if "vector_distance" in hit]
    return 1 - min(distances) if distances else 0.0


# ----------------------------------------------------- our own Python search

class PythonShopSearch(Setup):
    """shop/search.py: brute-force similarity + name bonus, no Typesense."""

    def __init__(self, spec, model):
        super().__init__(spec)
        self.model = model

    def index(self, products):
        start = time.perf_counter()
        self.shop = ShopSearch(products, model=self.model.st)
        return {"create_s": 0.0, "embed_s": time.perf_counter() - start, "import_s": 0.0}

    def search(self, query, k):
        matches = self.shop.search(query)["matches"]
        return [m["id"] for m in matches[:k]], max(m["meaning"] for m in matches)

    def model_info(self):
        return self.model.info()


# ------------------------------------------------------------ shared model

class LoadedModel:
    """A SentenceTransformer loaded once and shared by setups.

    Product vectors are computed once and reused, so the three EmbeddingGemma
    Typesense setups don't each spend half a minute re-embedding the catalog.
    """

    def __init__(self, model_name, st=None):
        if st is None:
            print(f"loading {model_name} (text only) ...", flush=True)
            st = load_model(model_name)
        self.st = st
        self.name = model_name
        self.dim = st.get_embedding_dimension()
        self._product_vectors = None  # (product ids, vectors, seconds it took)

    def encode_products(self, products):
        """Product vectors and the seconds the first computation took."""
        ids = [p["id"] for p in products]
        if self._product_vectors is None or self._product_vectors[0] != ids:
            start = time.perf_counter()
            vectors = self.st.encode_document([product_text(p) for p in products])
            self._product_vectors = (ids, vectors, time.perf_counter() - start)
        _, vectors, seconds = self._product_vectors
        return vectors, seconds

    def info(self):
        return {"model": self.name, "runs_in": "python process", "dim": self.dim,
                "disk_mb": measure.to_mb(measure.huggingface_model_size(self.name))}


# ----------------------------------------------------------------- factory

def build_setups(names, typesense, prefix="bench", gemma=None):
    """Create the requested setups, loading EmbeddingGemma only if one needs it.

    `prefix` names the Typesense collections, so the benchmark ("bench") and the
    compare page in the app ("app") don't overwrite each other.
    """
    specs = [SPECS_BY_NAME[name] for name in names]
    if gemma is None and any(spec.model == DEFAULT_MODEL for spec in specs):
        gemma = LoadedModel(DEFAULT_MODEL)

    setups = []
    for spec in specs:
        if spec.family == "keyword":
            setups.append(TypesenseSetup(spec, typesense, prefix))
        elif spec.family == "ours":
            setups.append(PythonShopSearch(spec, gemma))
        elif spec.model == DEFAULT_MODEL:
            setups.append(TypesenseOwnModel(spec, typesense, prefix, gemma))
        else:
            setups.append(TypesenseBuiltinModel(spec, typesense, prefix))
    return setups
