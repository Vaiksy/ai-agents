"""
Embedding Engine – v5.1 (DISABLED)

EMBEDDINGS ARE DISABLED - nomic-embed-text is not installed.
All functions will raise RuntimeError when called.

To enable embeddings: ollama pull nomic-embed-text
"""

import math


SEMANTIC_GAP_THRESHOLD = 0.35


def embed_text(text: str) -> list:
    """
    DISABLED - Embeddings not available.
    
    To enable: ollama pull nomic-embed-text
    """
    raise RuntimeError(
        "Embeddings are DISABLED. nomic-embed-text is not installed. "
        "To enable: ollama pull nomic-embed-text"
    )


def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Compute cosine similarity between two vectors.
    
    This function still works but won't be called since embeddings are disabled.
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vector length mismatch: {} vs {}".format(len(vec1), len(vec2)))

    dot = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot / (mag1 * mag2)


def check_embedding_available() -> bool:
    """
    Check if embedding model is available.
    
    ALWAYS returns False because embeddings are disabled.
    """
    return False


def embed_pages(research_data: list) -> list:
    """
    DISABLED - Embeddings not available.
    
    To enable: ollama pull nomic-embed-text
    """
    raise RuntimeError(
        "Embeddings are DISABLED. nomic-embed-text is not installed. "
        "To enable: ollama pull nomic-embed-text"
    )


def compute_gap_scores(page_embeddings: list, subdomain_texts: list) -> list:
    """
    DISABLED - Embeddings not available.
    
    To enable: ollama pull nomic-embed-text
    """
    raise RuntimeError(
        "Embeddings are DISABLED. nomic-embed-text is not installed. "
        "To enable: ollama pull nomic-embed-text"
    )
