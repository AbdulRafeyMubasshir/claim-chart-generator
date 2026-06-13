"""
embedder.py

Embeds document chunks and performs semantic search
to find chunks most relevant to each claim element.

Uses sentence-transformers locally (free, no API cost).
Model: all-MiniLM-L6-v2 — fast, good quality for technical text.

No external vector DB needed — in-memory numpy cosine similarity
is sufficient for demo scale (thousands of chunks).
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from chunker import Chunk


# Load model once at module level (not per request)
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Loading embedding model (first time only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    """
    Embed all document chunks.
    Returns a 2D array of shape (n_chunks, embedding_dim).
    """
    model = get_model()
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings


def search(
    query: str,
    chunks: list[Chunk],
    chunk_embeddings: np.ndarray,
    top_k: int = 3
) -> list[tuple[Chunk, float]]:
    """
    Find the top_k most relevant chunks for a query string.

    Args:
        query: The claim element text to search for
        chunks: List of document chunks
        chunk_embeddings: Pre-computed embeddings for all chunks
        top_k: Number of top results to return

    Returns:
        List of (chunk, similarity_score) tuples, sorted by relevance
    """
    model = get_model()

    # Embed the query
    query_embedding = model.encode([query])[0]

    # Compute cosine similarities
    similarities = _cosine_similarity(query_embedding, chunk_embeddings)

    # Get top_k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = [
        (chunks[i], float(similarities[i]))
        for i in top_indices
    ]

    return results


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a query vector
    and a matrix of document vectors.
    """
    # Normalize query
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)

    # Normalize document vectors
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    matrix_norm = matrix / norms

    # Dot product = cosine similarity (since both are normalized)
    similarities = matrix_norm @ query_norm

    return similarities
