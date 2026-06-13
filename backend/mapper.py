"""
mapper.py

Uses Claude to map patent claim elements to evidence
in a product document.

This is the critical AI step. We don't just dump chunks
at Claude — we first narrow candidates via semantic search,
then ask Claude to make a precise legal judgment:
  1. Does this chunk actually evidence the claim element?
  2. If yes, what's the specific relevant passage?
  3. Why does it map?

We treat Claude's output as untrusted and validate it.
Hallucinated evidence in a claim chart is a serious legal risk.
"""

import anthropic
import json
import re
from dataclasses import dataclass

from patent_parser import ClaimElement, Claim
from chunker import Chunk


@dataclass
class MappingResult:
    """Result of mapping a single claim element to evidence."""
    claim_element: ClaimElement
    found_evidence: bool
    evidence_passage: str          # The specific quoted text
    evidence_chunk: Chunk | None   # Source chunk
    explanation: str               # Why this maps to the claim element
    confidence: str                # "high", "medium", "low"


def map_element_to_evidence(
    claim_element: ClaimElement,
    candidate_chunks: list[tuple[Chunk, float]],
    claim_context: str,
    api_key: str
) -> MappingResult:
    """
    Ask Claude to determine if any candidate chunk evidences
    the given claim element.

    Args:
        claim_element: The patent claim limitation to map
        candidate_chunks: Top chunks from semantic search
                         (chunk, similarity_score) pairs
        claim_context: Full claim text for context
        api_key: Anthropic API key

    Returns:
        MappingResult with evidence or explanation of no match
    """
    client = anthropic.Anthropic(api_key=api_key)

    # Format candidate chunks for the prompt
    candidates_text = _format_candidates(candidate_chunks)

    prompt = f"""You are a patent analyst helping to build a claim chart.

A claim chart maps each element of a patent claim to evidence of how a product or technology implements (or infringes) that element.

PATENT CLAIM CONTEXT:
{claim_context}

CLAIM ELEMENT TO MAP:
"{claim_element.text}"

CANDIDATE PASSAGES FROM PRODUCT DOCUMENT:
{candidates_text}

Your task:
1. Determine if any of these passages provides evidence that the product implements the claim element.
2. If yes, identify the SPECIFIC passage (quote it exactly as it appears) and explain the mapping.
3. If no passage clearly evidences this element, say so honestly. Do not fabricate or stretch evidence.

Legal accuracy matters. Only map where there is genuine correspondence.

Respond in this exact JSON format:
{{
  "found_evidence": true or false,
  "evidence_passage": "the exact quoted text from one of the passages, or empty string if not found",
  "source_chunk_index": the index number of the chunk (0, 1, or 2), or null if not found,
  "explanation": "why this passage evidences the claim element, or why no evidence was found",
  "confidence": "high", "medium", or "low"
}}

Return only the JSON object, no other text."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_output = response.content[0].text.strip()

    return _parse_and_validate_response(
        raw_output,
        claim_element,
        candidate_chunks
    )


def _format_candidates(
    candidate_chunks: list[tuple[Chunk, float]]
) -> str:
    """Format candidate chunks for inclusion in the prompt."""
    parts = []
    for i, (chunk, score) in enumerate(candidate_chunks):
        parts.append(
            f"[Passage {i}] (relevance: {score:.2f})\n{chunk.text}"
        )
    return "\n\n---\n\n".join(parts)


def _parse_and_validate_response(
    raw_output: str,
    claim_element: ClaimElement,
    candidate_chunks: list[tuple[Chunk, float]]
) -> MappingResult:
    """
    Parse Claude's JSON response and validate it.

    Key validation: if Claude claims evidence was found,
    verify the quoted passage actually appears in one of
    the candidate chunks (prevents hallucination).
    """
    try:
        # Strip any accidental markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw_output).strip()
        data = json.loads(clean)
    except json.JSONDecodeError:
        # Claude returned something unparseable — treat as no evidence
        return MappingResult(
            claim_element=claim_element,
            found_evidence=False,
            evidence_passage="",
            evidence_chunk=None,
            explanation="Failed to parse AI response. Manual review required.",
            confidence="low"
        )

    found = data.get("found_evidence", False)
    passage = data.get("evidence_passage", "").strip()
    chunk_index = data.get("source_chunk_index")
    explanation = data.get("explanation", "")
    confidence = data.get("confidence", "low")

    # VALIDATION: Verify quoted passage exists in source material
    # This is the anti-hallucination check
    if found and passage:
        passage_verified = _verify_passage_exists(passage, candidate_chunks)
        if not passage_verified:
            # Claude invented text that doesn't exist — reject it
            return MappingResult(
                claim_element=claim_element,
                found_evidence=False,
                evidence_passage="",
                evidence_chunk=None,
                explanation=(
                    "AI identified a potential mapping but the quoted "
                    "passage could not be verified in source document. "
                    "Manual review required."
                ),
                confidence="low"
            )

    # Get the source chunk if identified
    source_chunk = None
    if chunk_index is not None and 0 <= chunk_index < len(candidate_chunks):
        source_chunk = candidate_chunks[chunk_index][0]

    return MappingResult(
        claim_element=claim_element,
        found_evidence=found and bool(passage),
        evidence_passage=passage,
        evidence_chunk=source_chunk,
        explanation=explanation,
        confidence=confidence
    )


def _verify_passage_exists(
    passage: str,
    candidate_chunks: list[tuple[Chunk, float]]
) -> bool:
    """
    Check if a quoted passage actually appears in the source chunks.
    Uses fuzzy matching to allow for minor whitespace differences.
    """
    # Normalise for comparison
    normalised_passage = " ".join(passage.lower().split())

    for chunk, _ in candidate_chunks:
        normalised_chunk = " ".join(chunk.text.lower().split())
        # Check if the core of the passage exists in the chunk
        # Allow for the passage being a substring of the chunk
        passage_core = normalised_passage[:100]  # First 100 chars
        if passage_core in normalised_chunk:
            return True

    return False
