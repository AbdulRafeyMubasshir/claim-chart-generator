"""
chunker.py

Splits product/technical documents into meaningful chunks
for semantic search. Chunking strategy matters enormously —
naive splitting breaks sentences and loses context.

Strategy used here:
- Paragraph-aware splitting (respect natural breaks)
- Overlapping windows (so evidence spanning paragraph
  boundaries isn't missed)
- Minimum/maximum chunk size enforcement
"""

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk with its source location."""
    text: str
    index: int
    char_start: int
    char_end: int


def chunk_document(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80
) -> list[Chunk]:
    """
    Split document text into overlapping chunks.

    Args:
        text: Full document text
        chunk_size: Target characters per chunk
        overlap: Overlap between consecutive chunks
                 (catches evidence that spans boundaries)

    Returns:
        List of Chunk objects
    """
    # First split into paragraphs (respect natural structure)
    paragraphs = _split_paragraphs(text)

    # Then create overlapping chunks from paragraphs
    chunks = _create_overlapping_chunks(paragraphs, chunk_size, overlap)

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    """
    Split text into paragraphs, keeping meaningful breaks.
    Filters out very short fragments (headers, page numbers, etc.)
    """
    # Split on double newlines (paragraph breaks)
    raw_paragraphs = re.split(r"\n\s*\n", text)

    paragraphs = []
    for para in raw_paragraphs:
        cleaned = para.strip()
        # Filter out noise: page numbers, single words, headers
        if len(cleaned) > 50:
            paragraphs.append(cleaned)

    return paragraphs


def _create_overlapping_chunks(
    paragraphs: list[str],
    chunk_size: int,
    overlap: int
) -> list[Chunk]:
    """
    Create overlapping chunks from paragraphs.
    Tries to respect paragraph boundaries, but splits
    long paragraphs if needed.
    """
    # Join all paragraphs with separators, tracking positions
    full_text = "\n\n".join(paragraphs)

    chunks = []
    index = 0
    pos = 0

    while pos < len(full_text):
        end = min(pos + chunk_size, len(full_text))

        # Try to end at a sentence boundary
        if end < len(full_text):
            # Look for sentence end within last 100 chars
            sentence_end = _find_sentence_end(full_text, end - 100, end)
            if sentence_end:
                end = sentence_end

        chunk_text = full_text[pos:end].strip()

        if len(chunk_text) > 30:  # Filter noise
            chunks.append(Chunk(
                text=chunk_text,
                index=index,
                char_start=pos,
                char_end=end
            ))
            index += 1

        # Move forward with overlap
        pos = end - overlap if end < len(full_text) else len(full_text)

    return chunks


def _find_sentence_end(text: str, start: int, end: int) -> int | None:
    """
    Find the last sentence boundary (. ! ?) in a text range.
    Returns position after the punctuation, or None if not found.
    """
    search_area = text[start:end]
    # Find last sentence-ending punctuation
    matches = list(re.finditer(r"[.!?]\s", search_area))
    if matches:
        last_match = matches[-1]
        return start + last_match.end()
    return None
