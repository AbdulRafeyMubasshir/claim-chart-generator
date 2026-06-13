"""
patent_parser.py

Parses patent claims from extracted patent text.
Handles the specific structure of US patent claims:
- Independent claims (stand alone)
- Dependent claims (reference a parent claim)
- Claim elements / limitations (the individual requirements)
"""

import re
from dataclasses import dataclass, field


@dataclass
class ClaimElement:
    """A single limitation/element within a patent claim."""
    text: str
    index: int  # Position within the claim


@dataclass
class Claim:
    """A single patent claim with its elements."""
    number: int
    text: str
    is_independent: bool
    parent_claim: int | None  # For dependent claims
    elements: list[ClaimElement] = field(default_factory=list)
    preamble: str = ""


def parse_claims(patent_text: str) -> list[Claim]:
    """
    Extract and parse all claims from patent text.
    Returns a list of Claim objects with elements broken out.
    """
    # Find the claims section
    claims_text = _extract_claims_section(patent_text)
    if not claims_text:
        raise ValueError(
            "Could not find claims section in patent. "
            "Ensure the PDF contains the full patent text including claims."
        )

    # Split into individual claims
    raw_claims = _split_into_claims(claims_text)

    # Parse each claim
    claims = []
    for number, raw_text in raw_claims.items():
        claim = _parse_single_claim(number, raw_text)
        claims.append(claim)

    claims.sort(key=lambda c: c.number)
    return claims


def _extract_claims_section(text: str) -> str:
    """
    Find and extract just the claims section from a patent.
    Handles multiple formats including OCR-spaced text.
    """
    # First, create a de-spaced version for pattern matching
    # OCR patents often have "W h a t i s c l a i m e d" or "1 . A method"
    
    # Strategy 1: Standard header-bounded extraction
    header_patterns = [
        r"(?:^|\n)\s*CLAIMS\s*\n(.*?)(?=\n\s*(?:ABSTRACT|DRAWINGS|BRIEF DESCRIPTION|[-]{3,})\s*\n|\Z)",
        r"(?:^|\n)\s*Claims\s*\n(.*?)(?=\n\s*(?:Abstract|ABSTRACT)\s*\n|\Z)",
        r"(?:^|\n)\s*What is claimed is:?\s*\n(.*?)(?=\n\s*(?:ABSTRACT|DRAWINGS)\s*\n|\Z)",
        r"(?:^|\n)\s*What is claimed is:?\s+(.*?)(?=\n\s*(?:ABSTRACT|DRAWINGS)\s*\n|\Z)",
        r"(?:^|\n)\s*THE CLAIMS\s*\n(.*?)(?=\n\s*ABSTRACT\s*\n|\Z)",
        r"(?:^|\n)\s*C L A I M S\s*\n(.*?)(?=\n\s*(?:ABSTRACT|A B S T R A C T)\s*\n|\Z)",
    ]

    for pattern in header_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            section = match.group(1).strip()
            if re.search(r"1\s*[.)]\s+\w", section):
                return section

    # Strategy 2: "What is claimed is:" followed immediately by claim 1 on same line
    inline_match = re.search(
        r"What\s+is\s+claimed\s+is\s*:?\s*(1\s*[.)].+)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if inline_match:
        return inline_match.group(1).strip()

    # Strategy 3: Find claim 1 with OCR spacing like "1 . A method"
    # and take everything from there
    for pattern in [
        r"(?:^|\n)[ \t]*1\s*[.)]\s+(?:A |An |The )\w",
        r"(?:^|\n)[ \t]*1\s*[.)]\s+\w",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = text[match.start():].strip()
            # Verify claim 2 exists nearby
            if re.search(r"2\s*[.)]\s+\w", candidate):
                return candidate

    # Strategy 4: Line-by-line scan
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^1\s*[.)]\s+\w", stripped):
            lookahead = "\n".join(lines[i:i+40])
            if re.search(r"2\s*[.)]\s+", lookahead):
                return "\n".join(lines[i:]).strip()

    # Strategy 5: Handle fully inline text with no newlines between claims
    # e.g. "What is claimed is : 1 . A laser ... 2 . The system of claim 1"
    inline_all = re.search(
        r"(?:What\s+is\s+claimed\s+is|CLAIMS?)\s*:?\s*(1[\s.]+.+)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if inline_all:
        return inline_all.group(1).strip()

    return ""


def _split_into_claims(claims_text: str) -> dict[int, str]:
    """
    Split claims text into individual numbered claims.
    Handles OCR spacing like "1 . A method" and "12 . The system"
    """
    claim_pattern = re.compile(
        r"(?:^|\n)\s*(\d+)\s*[.)]\s+(.*?)(?=\n\s*\d+\s*[.)]\s+|\Z)",
        re.DOTALL
    )

    claims = {}
    for match in claim_pattern.finditer(claims_text):
        number = int(match.group(1))
        text = match.group(2).strip()
        if text and len(text) > 20:
            claims[number] = text

    # Fallback: if claims run together without newlines between them
    # try splitting on the pattern " 2 . " " 3 . " etc inline
    if len(claims) <= 1:
        inline_pattern = re.compile(r"(\d+)\s*[.)]\s+(.+?)(?=\s+\d+\s*[.)]\s+|\Z)", re.DOTALL)
        claims = {}
        for match in inline_pattern.finditer(claims_text):
            number = int(match.group(1))
            text = match.group(2).strip()
            if text and len(text) > 20:
                claims[number] = text

    return claims


def _parse_single_claim(number: int, text: str) -> Claim:
    """
    Parse a single claim's text into structured form.
    Extracts preamble, determines if independent/dependent,
    and breaks out individual claim elements.
    """
    # Check if dependent (references another claim)
    dependent_pattern = re.search(
        r"[Tt]he (?:method|system|device|apparatus|composition|process) of claim (\d+)",
        text
    )
    dependent_pattern2 = re.search(r"[Aa]ccording to claim (\d+)", text)
    dep_match = dependent_pattern or dependent_pattern2

    is_independent = dep_match is None
    parent_claim = int(dep_match.group(1)) if dep_match else None

    # Extract preamble (text before "comprising", "consisting", "wherein")
    preamble_match = re.match(
        r"^(.*?)(?=\bcomprising\b|\bconsisting\b|\bwherein\b|\bincluding\b)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    preamble = preamble_match.group(1).strip() if preamble_match else ""

    # Extract elements (split on semicolons, "wherein", bullet indicators)
    elements = _extract_elements(text)

    return Claim(
        number=number,
        text=text,
        is_independent=is_independent,
        parent_claim=parent_claim,
        preamble=preamble,
        elements=elements
    )


def _extract_elements(claim_text: str) -> list[ClaimElement]:
    """
    Break a claim into its individual elements/limitations.

    Patent claims list elements separated by:
    - Semicolons
    - "wherein" clauses
    - Line breaks with lowercase continuation
    """
    # Find the body (after comprising/consisting/including)
    body_match = re.search(
        r"(?:comprising|consisting of|including|wherein)[:\s]+(.*)",
        claim_text,
        re.IGNORECASE | re.DOTALL
    )

    if not body_match:
        # No clear structure, treat whole claim as one element
        return [ClaimElement(text=claim_text.strip(), index=0)]

    body = body_match.group(1).strip()

    # Split on semicolons (primary element separator in patents)
    raw_elements = re.split(r";\s*", body)

    elements = []
    for i, elem_text in enumerate(raw_elements):
        cleaned = elem_text.strip().rstrip(".")
        if cleaned and len(cleaned) > 10:  # Filter out noise
            elements.append(ClaimElement(text=cleaned, index=i))

    # If no elements found, fall back to whole body
    if not elements:
        elements = [ClaimElement(text=body.strip(), index=0)]

    return elements


def get_independent_claims(claims: list[Claim]) -> list[Claim]:
    """Return only independent claims (most important for claim charts)."""
    return [c for c in claims if c.is_independent]
