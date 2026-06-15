"""
embedder.py — lightweight version

Replaces sentence-transformers (heavy, ~500MB RAM) with
simple TF-IDF style keyword scoring for Railway's free tier.
For production, swap back to sentence-transformers.
"""

import re
import math
import numpy as np
from chunker import Chunk


def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    """
    Build a simple TF-IDF matrix instead of neural embeddings.
    Returns a 2D array of shape (n_chunks, vocab_size).
    """
    corpus = [chunk.text.lower() for chunk in chunks]
    vocab = _build_vocab(corpus)
    matrix = np.array([_tfidf_vector(doc, corpus, vocab) for doc in corpus])
    return matrix


def search(
    query: str,
    chunks: list[Chunk],
    chunk_embeddings: np.ndarray,
    top_k: int = 3
) -> list[tuple[Chunk, float]]:
    """
    Find top_k chunks most relevant to query using TF-IDF cosine similarity.
    """
    corpus = [chunk.text.lower() for chunk in chunks]
    vocab = _build_vocab(corpus)
    query_vec = _tfidf_vector(query.lower(), corpus, vocab)

    # Cosine similarity
    similarities = _cosine_similarity(query_vec, chunk_embeddings)
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [(chunks[i], float(similarities[i])) for i in top_indices]


def _build_vocab(corpus: list[str]) -> dict[str, int]:
    vocab = {}
    for doc in corpus:
        for word in _tokenize(doc):
            if word not in vocab:
                vocab[word] = len(vocab)
    return vocab


def _tokenize(text: str) -> list[str]:
    # Remove punctuation, split on whitespace, filter short words
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [w for w in text.split() if len(w) > 2]


def _tfidf_vector(doc: str, corpus: list[str], vocab: dict[str, int]) -> np.ndarray:
    vec = np.zeros(len(vocab))
    tokens = _tokenize(doc)
    if not tokens:
        return vec

    # TF
    tf = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    for token, count in tf.items():
        if token in vocab:
            # IDF
            doc_freq = sum(1 for d in corpus if token in d)
            idf = math.log((len(corpus) + 1) / (doc_freq + 1)) + 1
            vec[vocab[token]] = (count / len(tokens)) * idf

    # Normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    matrix_norm = matrix / norms
    return matrix_norm @ query_norm