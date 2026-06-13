"""
pdf_extractor.py
Extracts clean text from PDF files using pdfplumber.
Handles multi-column layouts common in patent documents.
"""

import pdfplumber
import re
from pathlib import Path


def extract_text(pdf_path: str) -> str:
    """
    Extract full text from a PDF file.
    Returns cleaned, concatenated text from all pages.
    """
    text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract text with layout preservation
            page_text = page.extract_text(layout=True)
            if page_text:
                text_parts.append(page_text)

    full_text = "\n".join(text_parts)
    return _clean_text(full_text)


def _clean_text(text: str) -> str:
    """
    Clean extracted PDF text:
    - Remove excessive whitespace
    - Fix hyphenated line breaks (common in patents)
    - Normalize line endings
    """
    # Fix hyphenated line breaks (e.g., "inven-\ntion" -> "invention")
    text = re.sub(r"-\n(\w)", r"\1", text)

    # Normalize multiple spaces to single space
    text = re.sub(r" {2,}", " ", text)

    # Normalize multiple newlines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_text_by_page(pdf_path: str) -> list[str]:
    """
    Extract text page by page. Useful for locating
    where claims appear in a patent document.
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True) or ""
            pages.append(_clean_text(page_text))
    return pages
