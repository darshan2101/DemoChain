"""Task 3: RAG Module — product knowledge retrieval for NOVA support.

Provides a query() interface that takes a customer question and returns
relevant product info from the catalog using hybrid search (vector + BM25).

Usage:
    from rag_module import NovaRAG
    rag = NovaRAG()
    rag.build_index()  # one-time setup
    result = rag.query("What moisturizer is good for dry skin?")
"""

import json
import os
from pathlib import Path

# we'll handle missing dependencies gracefully for environments without them
try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

DB_PATH = Path(__file__).parent / "nova_mock_db.json"
CHROMA_DIR = Path(__file__).parent / "chroma_db"


class NovaRAG:
    """RAG pipeline for NOVA product catalog — hybrid search with re-ranking."""

    def __init__(self, chroma_dir=None):
        self.chroma_dir = str(chroma_dir or CHROMA_DIR)
        self.documents = []
        self.doc_metadata = []
        self.bm25 = None
        self.collection = None

    def _load_products(self):
        """Load products from mock DB and convert to searchable documents."""
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)

        docs = []
        meta = []
        for product in db["products"]:
            # build a rich text representation for each product
            text_parts = [
                f"Product: {product['name']}",
                f"Category: {product['category']}",
                f"Type: {product['type']}",
                f"Price: ${product['price']}",
                f"Rating: {product['rating']}/5 ({product['review_count']} reviews)",
                f"Description: {product['description']}",
            ]

            # add category-specific info
            if "ingredients" in product:
                text_parts.append(f"Ingredients: {', '.join(product['ingredients'])}")
            if "skin_types" in product:
                text_parts.append(f"Suitable for: {', '.join(product['skin_types'])} skin")
            if "hair_types" in product:
                text_parts.append(f"Hair types: {', '.join(product['hair_types'])}")
            if "concerns" in product:
                text_parts.append(f"Addresses: {', '.join(product['concerns'])}")
            if "available_sizes" in product:
                text_parts.append(f"Sizes: {', '.join(product['available_sizes'])}")
            if "material" in product:
                text_parts.append(f"Material: {product['material']}")
            if "shades" in product:
                text_parts.append(f"Shades: {', '.join(product['shades'])}")
            if "fit_note" in product:
                text_parts.append(f"Fit: {product['fit_note']}")

            doc_text = "\n".join(text_parts)
            docs.append(doc_text)
            meta.append({
                "sku": product["sku"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "in_stock": product.get("in_stock", True),
            })

        return docs, meta

    def build_index(self):
        """Build both vector and BM25 indexes from product catalog."""
        print("Loading product catalog...")
        self.documents, self.doc_metadata = self._load_products()
        print(f"Loaded {len(self.documents)} products")

        # build BM25 index for keyword search
        if HAS_BM25:
            tokenized = [doc.lower().split() for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized)
            print("BM25 keyword index built")

        # build ChromaDB vector index
        if HAS_CHROMA:
            client = chromadb.PersistentClient(path=self.chroma_dir)

            # use the default embedding function (all-MiniLM-L6-v2)
            ef = embedding_functions.DefaultEmbeddingFunction()

            # delete existing collection if rebuilding
            try:
                client.delete_collection("nova_products")
            except Exception:
                pass

            self.collection = client.create_collection(
                name="nova_products",
                embedding_function=ef,
                metadata={"description": "NOVA product catalog"}
            )

            # add documents in batches
            batch_size = 50
            for i in range(0, len(self.documents), batch_size):
                batch_docs = self.documents[i:i+batch_size]
                batch_ids = [f"prod_{j}" for j in range(i, i+len(batch_docs))]
                batch_meta = self.doc_metadata[i:i+batch_size]
                # chromadb metadata values must be str/int/float
                clean_meta = []
                for m in batch_meta:
                    clean_meta.append({
                        "sku": m["sku"],
                        "name": m["name"],
                        "category": m["category"],
                        "price": m["price"],
                        "in_stock": str(m["in_stock"]),
                    })
                self.collection.add(
                    documents=batch_docs,
                    ids=batch_ids,
                    metadatas=clean_meta,
                )

            print(f"ChromaDB vector index built ({self.collection.count()} docs)")
        else:
            print("ChromaDB not installed -- using BM25 only")

        print("Index ready.")

    def _vector_search(self, query, top_k=10):
        """Search using ChromaDB embeddings."""
        if not self.collection:
            return []
        results = self.collection.query(query_texts=[query], n_results=top_k)
        hits = []
        for i, doc_id in enumerate(results["ids"][0]):
            idx = int(doc_id.split("_")[1])
            hits.append({
                "index": idx,
                "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                "source": "vector",
            })
        return hits

    def _bm25_search(self, query, top_k=10):
        """Search using BM25 keyword matching."""
        if not self.bm25:
            return []
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            {"index": i, "score": float(scores[i]), "source": "bm25"}
            for i in top_indices if scores[i] > 0
        ]

    def _hybrid_merge(self, vector_hits, bm25_hits, top_k=5):
        """Merge vector and BM25 results using reciprocal rank fusion."""
        scores = {}
        k = 60  # RRF constant

        for rank, hit in enumerate(vector_hits):
            idx = hit["index"]
            scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)

        for rank, hit in enumerate(bm25_hits):
            idx = hit["index"]
            scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"index": idx, "rrf_score": score} for idx, score in ranked]

    def query(self, question, top_k=5):
        """Run hybrid search and return relevant products with context."""
        vector_hits = self._vector_search(question, top_k=10)
        bm25_hits = self._bm25_search(question, top_k=10)
        merged = self._hybrid_merge(vector_hits, bm25_hits, top_k=top_k)

        results = []
        for hit in merged:
            idx = hit["index"]
            results.append({
                "document": self.documents[idx],
                "metadata": self.doc_metadata[idx],
                "relevance_score": round(hit["rrf_score"], 4),
            })

        # build context string for the LLM
        context = "\n\n---\n\n".join([r["document"] for r in results])

        return {
            "question": question,
            "results": results,
            "context": context,
            "result_count": len(results),
        }

    def answer(self, question, top_k=5):
        """Full RAG: retrieve context then generate an answer using the LLM."""
        retrieval = self.query(question, top_k=top_k)

        from nova_llm import call_llm, load_prompt

        system = load_prompt("nova_system_prompt_v1.txt")
        system += "\n\n=== PRODUCT KNOWLEDGE ===\nUse the following product information to answer the customer's question. Only reference products that appear in this context.\n\n"
        system += retrieval["context"]

        answer = call_llm(system, question, temperature=0.3)

        return {
            "question": question,
            "answer": answer,
            "sources": [r["metadata"]["sku"] for r in retrieval["results"]],
            "result_count": retrieval["result_count"],
        }


def run_demo():
    """Quick demo of the RAG pipeline."""
    print("=" * 60)
    print("TASK 3: RAG PIPELINE DEMO")
    print("=" * 60)

    rag = NovaRAG()
    rag.build_index()

    test_queries = [
        "What moisturizer is good for dry sensitive skin?",
        "Does any product contain hyaluronic acid?",
        "What sizes are available for hoodies?",
        "I need something for frizzy curly hair",
        "Show me vegan leather bags under $50",
    ]

    for q in test_queries:
        print(f"\nQ: {q}")
        result = rag.query(q, top_k=3)
        print(f"Found {result['result_count']} results:")
        for r in result["results"]:
            m = r["metadata"]
            print(f"  - {m['name']} (${m['price']}, {m['category']}) score={r['relevance_score']}")

    print("\n" + "=" * 60)
    print("RAG pipeline demo complete")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
