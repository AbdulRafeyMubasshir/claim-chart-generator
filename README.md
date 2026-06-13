# Claim Chart Generator

AI-powered tool that maps patent claim elements to evidence in product documents, generating structured claim charts for attorney review.

Built as a portfolio project demonstrating applied AI for IP workflows.

---

## What it does

Upload a patent PDF and a product/technical document PDF. The tool:

1. Extracts and parses patent claims (independent + dependent)
2. Breaks each claim into its individual limitations/elements
3. Chunks the product document with sentence-boundary-aware overlapping windows
4. Embeds all chunks using `sentence-transformers` (local, no API cost)
5. For each claim element, retrieves the top 3 candidate chunks via cosine similarity
6. Sends candidates to Claude with a structured prompt asking for precise evidence mapping
7. Validates Claude's output — quoted passages are verified against source material to prevent hallucination
8. Displays results in a claim chart UI with confidence scores
9. Exports a formatted `.docx` claim chart ready for attorney review

---

## Technical architecture

```
backend/
├── pdf_extractor.py   # pdfplumber text extraction with hyphenation fix
├── patent_parser.py   # Claim section detection, claim splitting, element extraction
├── chunker.py         # Paragraph-aware overlapping chunks (400 chars, 80 overlap)
├── embedder.py        # sentence-transformers + numpy cosine similarity (no vector DB)
├── mapper.py          # Claude API call + anti-hallucination validation
├── exporter.py        # python-docx claim chart generation
└── main.py            # FastAPI endpoints: /generate (JSON) + /export (.docx)

frontend/
└── src/
    ├── App.jsx              # Shell, pipeline visualisation
    ├── components/
    │   ├── UploadPanel.jsx  # File upload + config form
    │   └── ClaimChart.jsx   # Claim chart table display
```

---

## Key design decisions and why

### Chunking strategy
Naive fixed-size chunking (every N characters) breaks sentences mid-thought and loses context. This implementation uses paragraph-aware splitting followed by sentence-boundary detection when creating overlapping windows. The 80-character overlap ensures evidence spanning paragraph breaks isn't missed.

### Why local embeddings instead of OpenAI
`all-MiniLM-L6-v2` runs locally via `sentence-transformers` — zero API cost and no latency for the embedding step. For a demo with thousands of chunks, this is faster than making hundreds of API calls. Quality is sufficient for the retrieval step; the precision work is done by Claude.

### Two-stage retrieval + reasoning
Pure semantic search would send entire chunks to Claude and hope for the best. This pipeline does retrieval first (fast, cheap) then asks Claude to make a precise legal judgment on a small, pre-filtered candidate set. This is more reliable and far cheaper than embedding the entire product document in every prompt.

### Anti-hallucination check
After Claude returns a mapping, the quoted passage is verified against the source chunks before being accepted. If Claude invents text that doesn't appear in the candidates, the mapping is rejected and flagged for manual review. In patent work, fabricated evidence is a serious legal risk — the system must fail safe.

### Why Claude over GPT-4
Claude produces more consistent structured JSON output for legal/document tasks and follows formatting instructions more reliably. The system prompt asks for exact JSON with no preamble — Claude complies more consistently in testing.

---

## Where the AI struggles (honest assessment)

Tested across 10 patents and product documents from USPTO:

- **Claim parsing: 9/10** — dependent claim detection works well; occasional failures on non-standard formatting (e.g. claims presented as a single block without numbers)
- **Element extraction: 8/10** — semicolon-separated elements parse well; "wherein" clauses that modify multiple elements sometimes merge incorrectly
- **Evidence mapping: 7/10** — high-similarity matches are reliable; low-similarity cases (<0.25 cosine) often correctly return "no evidence" but occasionally miss edge cases
- **Failure mode**: Very technical domains (e.g. pharmaceutical chemistry) where claim language is highly abbreviated can produce low-quality embeddings and poor retrieval

---

## What I'd do with more time

1. **Fine-tune element extraction** — current regex-based approach misses complex nested claim structures; a small fine-tuned model would be more robust
2. **Multi-document product evidence** — allow uploading multiple product documents and merging evidence across them
3. **Prior art mode** — instead of a product doc, search against the USPTO full-text database for prior art mapping
4. **Export all claims** — current `.docx` export generates one claim at a time; proper implementation would generate a full multi-claim chart with cover page
5. **Confidence calibration** — Claude's self-reported confidence isn't well-calibrated; a second-pass verification prompt or human feedback loop would improve this

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

First run downloads the `all-MiniLM-L6-v2` model (~90MB). Subsequent runs use the cached version.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### Environment

You need an Anthropic API key: https://console.anthropic.com

Enter it in the UI — it's sent with each request and not stored server-side.

---

## Test documents

Good sources for testing:
- **Patents**: https://patents.google.com — search any technical topic, download full PDF
- **Product docs**: Company technical whitepapers, datasheets (search "[product] datasheet filetype:pdf")

Recommended first test: a software/networking patent + a product technical specification in the same domain.

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI + Python | Standard for AI/ML backends; async support |
| PDF extraction | pdfplumber | Better columnar layout handling than PyMuPDF |
| Embeddings | sentence-transformers | Local, free, fast for retrieval step |
| Vector search | numpy cosine similarity | No DB overhead for demo scale |
| LLM | Claude (claude-sonnet-4-20250514) | Better structured output for legal tasks |
| Word export | python-docx | Attorneys work in Word |
| Frontend | React + Vite | Fast iteration, no framework overhead |
