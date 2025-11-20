"""Paper ranking service using semantic similarity with Sentence Transformers"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
from utils.text_utils import clean_text

# Load embedding model (reuse same model as RAG for consistency)
# Using a faster model for ranking
model = SentenceTransformer("all-MiniLM-L6-v2")


def rank_papers(query: str, papers: List[Dict], top_k: int = 10) -> List[Dict]:
    """Rank papers based on semantic similarity to the query"""
    # Clean query and abstracts
    query = clean_text(query)
    for paper in papers:
        paper["abstract"] = clean_text(paper["abstract"] or "")

    # Compute embeddings
    query_embedding = model.encode([query])
    paper_embeddings = model.encode([paper["abstract"] for paper in papers])

    # Compute cosine similarity
    similarities = cosine_similarity(query_embedding, paper_embeddings)[0]

    # Calculate scores with recency and keyword matching
    for i, paper in enumerate(papers):
        year = paper.get("year")
        recency_weight = 1 + (2025 - year) * 0.01 if year else 1
        keyword_match = sum(1 for word in query.split() if word.lower() in paper["abstract"].lower())
        paper["score"] = float(similarities[i]) * recency_weight + keyword_match * 0.1

    # Sort by score
    ranked_papers = sorted(papers, key=lambda x: x["score"], reverse=True)

    # Normalize scores
    max_score = max(paper["score"] for paper in ranked_papers) if ranked_papers else 1
    for paper in ranked_papers:
        paper["score"] = paper["score"] / max_score

    return ranked_papers[:top_k]

