import { useState, useRef } from "react";
import { API_BASE } from "../api.js";

const styles = `
  .upload-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-top: 2rem;
  }

  @media (max-width: 700px) {
    .upload-panel { grid-template-columns: 1fr; }
  }

  .upload-card {
    background: #fff;
    border: 1.5px dashed var(--border);
    border-radius: 12px;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
  }

  .upload-card:hover, .upload-card.drag-over {
    border-color: var(--accent);
    background: var(--accent-glow);
  }

  .upload-card.has-file {
    border-style: solid;
    border-color: var(--green);
    background: var(--green-bg);
  }

  .upload-icon {
    font-size: 2rem;
    line-height: 1;
  }

  .upload-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }

  .upload-hint {
    font-size: 12px;
    color: var(--text-3);
    text-align: center;
  }

  .upload-filename {
    font-size: 12px;
    font-family: var(--mono);
    color: var(--green);
    font-weight: 500;
    text-align: center;
    word-break: break-all;
  }

  .form-section {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    grid-column: 1 / -1;
  }

  .form-section h3 {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-2);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 1rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  @media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }

  .form-group { display: flex; flex-direction: column; gap: 6px; }

  .form-group label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-2);
  }

  .form-input {
    padding: 9px 12px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    font-family: var(--sans);
    color: var(--text);
    outline: none;
    transition: border-color 0.15s;
  }

  .form-input:focus { border-color: var(--accent); }

  .form-input.api-key { font-family: var(--mono); font-size: 13px; }

  .claims-toggle {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .toggle-btn {
    padding: 7px 14px;
    border-radius: 6px;
    border: 1.5px solid var(--border);
    background: var(--surface);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    color: var(--text-2);
    transition: all 0.15s;
  }

  .toggle-btn.active {
    background: var(--navy);
    border-color: var(--navy);
    color: #fff;
  }

  .submit-row {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 1.5rem;
    grid-column: 1 / -1;
  }

  .btn-primary {
    padding: 11px 28px;
    background: var(--blue-light);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-primary:hover:not(:disabled) { background: var(--blue); }
  .btn-primary:active:not(:disabled) { transform: scale(0.98); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

  .error-banner {
    grid-column: 1 / -1;
    background: var(--red-bg);
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: var(--red);
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .progress-area {
    grid-column: 1 / -1;
    background: var(--navy);
    border-radius: 12px;
    padding: 2rem;
    color: #fff;
    text-align: center;
  }

  .progress-spinner {
    display: inline-block;
    width: 32px;
    height: 32px;
    border: 3px solid rgba(255,255,255,0.15);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .progress-message {
    font-size: 14px;
    color: rgba(255,255,255,0.7);
    font-family: var(--mono);
  }

  .progress-note {
    font-size: 12px;
    color: rgba(255,255,255,0.35);
    margin-top: 0.5rem;
  }
`;

const PROGRESS_MESSAGES = [
  "Extracting text from PDFs...",
  "Parsing patent claims...",
  "Chunking product document...",
  "Computing embeddings...",
  "Running semantic search...",
  "Mapping elements with Claude...",
  "Assembling claim chart...",
];

export default function UploadPanel({ onResult, onStepChange }) {
  const [patentFile, setPatentFile] = useState(null);
  const [productFile, setProductFile] = useState(null);
  const [apiKey, setApiKey] = useState("");
  const [patentTitle, setPatentTitle] = useState("");
  const [productName, setProductName] = useState("");
  const [claimsMode, setClaimsMode] = useState("independent");
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState("");
  const [error, setError] = useState("");

  const patentRef = useRef();
  const productRef = useRef();

  const handleDrop = (setter) => (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      setter(file);
    }
  };

  const canSubmit = patentFile && productFile && apiKey.trim().length > 10;

  const simulateProgress = () => {
    let step = 0;
    const interval = setInterval(() => {
      if (step < PROGRESS_MESSAGES.length) {
        setProgressMsg(PROGRESS_MESSAGES[step]);
        onStepChange(step);
        step++;
      } else {
        clearInterval(interval);
      }
    }, 2200);
    return interval;
  };

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    const interval = simulateProgress();

    try {
      const form = new FormData();
      form.append("patent_pdf", patentFile);
      form.append("product_pdf", productFile);
      form.append("api_key", apiKey.trim());
      form.append("patent_title", patentTitle);
      form.append("product_name", productName);
      form.append("claims_to_chart", claimsMode);

      const res = await fetch(`${API_BASE}generate`, { method: "POST", body: form });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      clearInterval(interval);
      onStepChange(5);
      onResult(data);
    } catch (err) {
      clearInterval(interval);
      setError(err.message);
      onStepChange(-1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className="upload-panel">

        {/* Patent upload */}
        <div
          className={`upload-card ${patentFile ? "has-file" : ""}`}
          onClick={() => patentRef.current.click()}
          onDrop={handleDrop(setPatentFile)}
          onDragOver={(e) => e.preventDefault()}
        >
          <input
            ref={patentRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => setPatentFile(e.target.files[0])}
          />
          <div className="upload-icon">{patentFile ? "✅" : "📄"}</div>
          <div className="upload-label">Patent Document</div>
          {patentFile ? (
            <div className="upload-filename">{patentFile.name}</div>
          ) : (
            <div className="upload-hint">
              Drop a patent PDF here or click to browse.<br />
              Full patent text including claims section required.
            </div>
          )}
        </div>

        {/* Product doc upload */}
        <div
          className={`upload-card ${productFile ? "has-file" : ""}`}
          onClick={() => productRef.current.click()}
          onDrop={handleDrop(setProductFile)}
          onDragOver={(e) => e.preventDefault()}
        >
          <input
            ref={productRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => setProductFile(e.target.files[0])}
          />
          <div className="upload-icon">{productFile ? "✅" : "📋"}</div>
          <div className="upload-label">Product / Technical Document</div>
          {productFile ? (
            <div className="upload-filename">{productFile.name}</div>
          ) : (
            <div className="upload-hint">
              Drop a product datasheet, spec, or whitepaper.<br />
              The AI will search this for claim evidence.
            </div>
          )}
        </div>

        {/* Settings */}
        <div className="form-section">
          <h3>Configuration</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Patent Title (optional)</label>
              <input
                className="form-input"
                placeholder="e.g. US10,123,456 — System for..."
                value={patentTitle}
                onChange={(e) => setPatentTitle(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Product / Document Name (optional)</label>
              <input
                className="form-input"
                placeholder="e.g. Acme Widget v2 Datasheet"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Anthropic API Key</label>
              <input
                className="form-input api-key"
                type="password"
                placeholder="sk-ant-..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Claims to chart</label>
              <div className="claims-toggle">
                {["independent", "all"].map((mode) => (
                  <button
                    key={mode}
                    className={`toggle-btn ${claimsMode === mode ? "active" : ""}`}
                    onClick={() => setClaimsMode(mode)}
                  >
                    {mode === "independent" ? "Independent claims only" : "All claims"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span><strong>Error:</strong> {error}</span>
          </div>
        )}

        {/* Progress */}
        {loading && (
          <div className="progress-area">
            <div className="progress-spinner" />
            <div className="progress-message">{progressMsg}</div>
            <div className="progress-note">
              This takes 30–90 seconds depending on document length
            </div>
          </div>
        )}

        {/* Submit */}
        {!loading && (
          <div className="submit-row">
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              Generate Claim Chart →
            </button>
          </div>
        )}
      </div>
    </>
  );
}
