"""
Retrieval system for Tutorly.

Workflow:
1. On startup, load all curriculum passages
2. Convert each to an embedding (numbers representing meaning)
3. Store them in a ChromaDB collection in memory
4. When asked, find the N most similar passages to a query
"""
from __future__ import annotations
import difflib
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


def _topic_match_score(query_topic: str, passage_topic: str) -> float:
    """
    Fuzzy 0..1 similarity between a requested topic and a curriculum
    passage's own topic label. These are two independently-authored
    vocabularies — admin/student topics are free-typed (e.g. "Kinematics"),
    while curriculum.py's topic labels are fixed strings written by hand
    (e.g. "Kinematics (Mechanics)") — so exact equality rarely holds even
    when the passage is exactly what's wanted. Substring containment covers
    the common case; SequenceMatcher covers everything else.
    """
    q = (query_topic or "").strip().lower()
    p = (passage_topic or "").strip().lower()
    if not q or not p:
        return 0.0
    if q == p:
        return 1.0
    if q in p or p in q:
        return 0.85
    return difflib.SequenceMatcher(None, q, p).ratio()


def search(query: str, top_k: int = 3, subject: str = None, topic: str = None) -> list[dict]:
    """Return the top_k most relevant passages for the query.

    Each result has: id, content, subject, grade, topic, distance.
    Lower distance = more similar.

    subject (optional): hard ChromaDB `where` filter — subject names are a
    small, controlled vocabulary shared with student_profile.py, so an
    exact match is reliable here.

    topic (optional): NOT a hard filter. Topic strings come from two
    independently-typed sources (admin-entered topics vs. curriculum.py's
    hand-written labels) and rarely match exactly, so hard-filtering on
    topic would silently exclude almost everything. Instead, this widens
    the semantic candidate pool and re-ranks it so passages whose topic
    label fuzzy-matches the requested topic are boosted toward the top —
    it can only reorder within the subject's results, never zero them out.
    """
    where = {"subject": subject} if subject else None

    # Widen the pool when re-ranking by topic, so a fuzzy topic match can
    # actually surface a passage that wasn't in the top_k on pure semantic
    # distance alone.
    pool_size = max(top_k * 5, 15) if topic else top_k

    query_embedding = EMBEDDER.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=pool_size,
        where=where,
    )

    candidates = []
    for i in range(len(results["ids"][0])):
        candidates.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "subject": results["metadatas"][0][i]["subject"],
            "grade": results["metadatas"][0][i]["grade"],
            "topic": results["metadatas"][0][i]["topic"],
            "distance": results["distances"][0][i],
        })

    if topic and candidates:
        # Blend semantic distance (lower = better) with a topic-match bonus
        # (higher = better), so a strong fuzzy topic match can outrank a
        # slightly-closer passage that's on a different topic within the
        # same subject.
        for c in candidates:
            c["_rank_score"] = c["distance"] - (_topic_match_score(topic, c["topic"]) * 0.5)
        candidates.sort(key=lambda c: c["_rank_score"])
        for c in candidates:
            del c["_rank_score"]

    return candidates[:top_k]


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