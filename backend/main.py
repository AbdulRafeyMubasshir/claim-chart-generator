"""
main.py

FastAPI backend for the Claim Chart Generator.
Exposes two endpoints:
  POST /generate  — runs the full pipeline, returns JSON claim chart
  POST /export    — generates and returns a .docx file
"""

import os
import tempfile
import asyncio
from pathlib import Path
import re as _re

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from pdf_extractor import extract_text
from patent_parser import parse_claims, get_independent_claims, Claim
from chunker import chunk_document
from embedder import embed_chunks, search
from mapper import map_element_to_evidence, MappingResult
from exporter import generate_claim_chart

app = FastAPI(title="Claim Chart Generator API")

# CORS for local React dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://claim-chart-generator.vercel.app",
        "https://*.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Response models ──────────────────────────────────────────────────────────

class ClaimElementResult(BaseModel):
    element_index: int
    element_text: str
    found_evidence: bool
    evidence_passage: str
    explanation: str
    confidence: str


class ClaimResult(BaseModel):
    claim_number: int
    claim_text: str
    is_independent: bool
    elements: list[ClaimElementResult]


class GenerateResponse(BaseModel):
    patent_title: str
    product_name: str
    claims: list[ClaimResult]
    total_elements: int
    elements_mapped: int
    warnings: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/generate", response_model=GenerateResponse)
async def generate(
    patent_pdf: UploadFile = File(...),
    product_pdf: UploadFile = File(...),
    api_key: str = Form(...),
    patent_title: str = Form(default=""),
    product_name: str = Form(default=""),
    claims_to_chart: str = Form(default="independent"),  # "independent" or "all"
):
    """
    Run the full claim chart pipeline.
    Returns structured JSON with all mappings.
    """
    warnings = []

    # Save uploads to temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        patent_path = Path(tmpdir) / "patent.pdf"
        product_path = Path(tmpdir) / "product.pdf"

        patent_path.write_bytes(await patent_pdf.read())
        product_path.write_bytes(await product_pdf.read())

        # Step 1: Extract text
        try:
            patent_text = extract_text(str(patent_path))
            product_text = extract_text(str(product_path))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")

        # Step 2: Parse claims
        try:
            all_claims = parse_claims(patent_text)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not all_claims:
            raise HTTPException(
                status_code=400,
                detail="No claims found in patent. Ensure you uploaded a patent document with a claims section."
            )

        # Select which claims to chart
        if claims_to_chart == "independent":
            claims_to_process = get_independent_claims(all_claims)
            if not claims_to_process:
                warnings.append("No independent claims found — charting all claims instead.")
                claims_to_process = all_claims
        else:
            claims_to_process = all_claims

        # Step 3: Chunk and embed product document
        chunks = chunk_document(product_text)
        if len(chunks) < 3:
            raise HTTPException(
                status_code=400,
                detail="Product document too short or could not be parsed."
            )

        chunk_embeddings = embed_chunks(chunks)

        # Step 4: Map each claim element to evidence
        claim_results = []

        for claim in claims_to_process:
            element_results = []

            for element in claim.elements:
                # Semantic search for candidate chunks
                candidates = search(
                    query=element.text,
                    chunks=chunks,
                    chunk_embeddings=chunk_embeddings,
                    top_k=3
                )

                # Low similarity warning
                if candidates and candidates[0][1] < 0.2:
                    warnings.append(
                        f"Claim {claim.number}, Element {element.index + 1}: "
                        f"Low semantic similarity ({candidates[0][1]:.2f}) — "
                        f"evidence quality may be poor."
                    )

                # Claude mapping
                mapping = map_element_to_evidence(
                    claim_element=element,
                    candidate_chunks=candidates,
                    claim_context=claim.text,
                    api_key=api_key
                )

                element_results.append(ClaimElementResult(
                    element_index=element.index,
                    element_text=element.text,
                    found_evidence=mapping.found_evidence,
                    evidence_passage=mapping.evidence_passage,
                    explanation=mapping.explanation,
                    confidence=mapping.confidence
                ))

            claim_results.append(ClaimResult(
                claim_number=claim.number,
                claim_text=claim.text,
                is_independent=claim.is_independent,
                elements=element_results
            ))

        # Stats
        total_elements = sum(len(c.elements) for c in claim_results)
        elements_mapped = sum(
            sum(1 for e in c.elements if e.found_evidence)
            for c in claim_results
        )

        return GenerateResponse(
            patent_title=patent_title or patent_pdf.filename or "Unknown Patent",
            product_name=product_name or product_pdf.filename or "Unknown Product",
            claims=claim_results,
            total_elements=total_elements,
            elements_mapped=elements_mapped,
            warnings=warnings
        )


@app.post("/export")
async def export_docx(
    patent_pdf: UploadFile = File(...),
    product_pdf: UploadFile = File(...),
    api_key: str = Form(...),
    patent_title: str = Form(default=""),
    product_name: str = Form(default=""),
):
    """
    Run pipeline and return a .docx claim chart file.
    """
    # Reuse the generate endpoint logic
    result = await generate(
        patent_pdf=patent_pdf,
        product_pdf=product_pdf,
        api_key=api_key,
        patent_title=patent_title,
        product_name=product_name,
    )

    # Generate Word doc for first claim
    if not result.claims:
        raise HTTPException(status_code=400, detail="No claims to export.")

    # For export, generate for all claims
    # Build MappingResult objects from response
    from patent_parser import ClaimElement, Claim as PatentClaim
    from mapper import MappingResult

    all_docs = []
    for claim_result in result.claims:
        mappings = []
        for elem in claim_result.elements:
            mappings.append(MappingResult(
                claim_element=ClaimElement(
                    text=elem.element_text,
                    index=elem.element_index
                ),
                found_evidence=elem.found_evidence,
                evidence_passage=elem.evidence_passage,
                evidence_chunk=None,
                explanation=elem.explanation,
                confidence=elem.confidence
            ))

        claim_obj = PatentClaim(
            number=claim_result.claim_number,
            text=claim_result.claim_text,
            is_independent=claim_result.is_independent,
            parent_claim=None,
            elements=[]
        )

        doc_bytes = generate_claim_chart(
            claim=claim_obj,
            mappings=mappings,
            patent_title=result.patent_title,
            product_name=result.product_name
        )
        all_docs.append(doc_bytes)

    # Return the first claim's doc (simplification for demo)
    return Response(
        content=all_docs[0],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="claim_chart.docx"'
        }
    )


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/debug-pdf")
async def debug_pdf(pdf: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "file.pdf"
        path.write_bytes(await pdf.read())
        text = extract_text(str(path))
    return {
        "total_chars": len(text),
        "first_2000": text[:2000],
        "last_3000": text[-3000:],
        "contains_claims": "claims" in text.lower(),
        "has_claim_1": bool(_re.search(r"\n\s*1\s*[.)]\s+\w", text)),
    }