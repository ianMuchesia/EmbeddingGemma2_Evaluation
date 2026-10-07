"""Minimal Typesense REST client: only what the benchmark needs."""
import json
import os

import requests

TYPESENSE_URL = os.environ.get("TYPESENSE_URL", "http://localhost:8108")
TYPESENSE_KEY = os.environ.get("TYPESENSE_API_KEY", "benchmark-local-key")


class Typesense:
    def __init__(self, url=TYPESENSE_URL, key=TYPESENSE_KEY):
        self.url = url
        self.http = requests.Session()
        self.http.headers["X-TYPESENSE-API-KEY"] = key

    def request(self, method, path, ok=(200, 201), timeout=60, **kwargs):
        response = self.http.request(method, self.url + path, timeout=timeout, **kwargs)
        if response.status_code not in ok:
            raise RuntimeError(f"Typesense {method} {path} -> {response.status_code}: {response.text[:500]}")
        return response

    def check_running(self):
        try:
            self.request("GET", "/health")
        except requests.ConnectionError:
            raise SystemExit(f"Typesense is not running at {self.url}. Start it with: docker compose up -d")

    def version(self):
        return self.request("GET", "/debug").json().get("version")

    def collection_names(self):
        return [c["name"] for c in self.request("GET", "/collections").json()]

    def drop_collection(self, name):
        self.request("DELETE", f"/collections/{name}", ok=(200, 404))

    def create_collection(self, schema):
        # With a built-in model this also downloads and loads the model, so allow a long timeout.
        self.request("POST", "/collections", json=schema, timeout=1800)

    def import_documents(self, collection, documents):
        body = "\n".join(json.dumps(d) for d in documents)
        response = self.request("POST", f"/collections/{collection}/documents/import?action=create",
                                data=body.encode(), timeout=1800)
        failed = [line for line in response.text.splitlines() if not json.loads(line).get("success")]
        if failed:
            raise RuntimeError(f"{len(failed)} documents failed to import into {collection}: {failed[0]}")

    def search(self, params):
        # multi_search is a POST, so long vectors fit in the body instead of the URL.
        result = self.request("POST", "/multi_search", json={"searches": [params]}).json()["results"][0]
        if "error" in result:
            raise RuntimeError(f"Typesense search error: {result['error']}")
        return result["hits"]
