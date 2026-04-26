"""
Retrieval system for Tutorly.

Workflow:
1. On startup, load all curriculum passages
2. Convert each to an embedding (numbers representing meaning)
3. Store them in a ChromaDB collection in memory
4. When asked, find the N most similar passages to a query
"""
from __future__ import annotations
import chromadb
from sentence_transformers import SentenceTransformer
from curriculum import CURRICULUM
from data.generated_curriculum import GENERATED_CURRICULUM

# This is an embedding model — small (~90MB), fast, works offline.
# First run downloads it; later runs use the cached copy.
print("Loading embedding model... (first time takes ~30 seconds)")
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model ready.")

# ChromaDB: in-memory vector database. Resets each time the server restarts,
# which is fine for now. We'll switch to persistent storage later.
_client = chromadb.Client()
_collection = _client.create_collection(name="curriculum")


def build_index() -> None:
    """Embed every curriculum passage and add it to the collection."""
    # Combine hand-written chunks with auto-generated syllabus chunks
    all_passages = list(CURRICULUM) + list(GENERATED_CURRICULUM)
    texts = [p["content"] for p in all_passages]
    ids = [p["id"] for p in all_passages]
    metadatas = [
        {
            "subject": p["subject"],
            "grade": p["grade"],
            "topic": p["topic"],
            # Generated chunks have extra metadata; hand-written ones don't
            "board": p.get("board", "manual"),
            "department": p.get("department", "Mixed"),
        }
        for p in all_passages
    ]
    print(f"Embedding {len(texts)} curriculum passages...")
    embeddings = EMBEDDER.encode(texts, show_progress_bar=False).tolist()

    _collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Curriculum index ready: {len(texts)} passages.")


def search(query: str, top_k: int = 3) -> list[dict]:
    """Return the top_k most relevant passages for the query.

    Each result has: id, content, subject, grade, topic, similarity_score.
    Lower distance = more similar.
    """
    query_embedding = EMBEDDER.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "subject": results["metadatas"][0][i]["subject"],
            "grade": results["metadatas"][0][i]["grade"],
            "topic": results["metadatas"][0][i]["topic"],
            "distance": results["distances"][0][i],
        })
    return hits


# Build the index as soon as this module is imported
build_index()


if __name__ == "__main__":
    # Quick test when you run `python rag.py` directly
    print("\n--- Testing retrieval ---\n")
    test_queries = [
        "How do plants make food?",
        "Explain Newton's laws",
        "What are acids?",
        "Solve quadratic equations",
    ]
    for q in test_queries:
        print(f"Query: {q}")
        for hit in search(q, top_k=2):
            print(f"  → {hit['topic']} ({hit['subject']}, {hit['grade']}) [dist={hit['distance']:.3f}]")
        print()