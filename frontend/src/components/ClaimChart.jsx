import { useState } from "react";

const styles = `
  .chart-header {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .chart-meta h2 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
    margin-bottom: 4px;
  }

  .chart-meta .vs {
    font-size: 13px;
    color: var(--text-2);
    font-style: italic;
  }

  .stats-row {
    display: flex;
    gap: 1.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--navy);
    font-family: var(--mono);
    line-height: 1;
  }

  .stat-label {
    font-size: 11px;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .chart-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
  }

  .btn-outline {
    padding: 9px 18px;
    border: 1.5px solid var(--border);
    background: var(--surface);
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    color: var(--text-2);
    transition: all 0.15s;
  }

  .btn-outline:hover { border-color: var(--accent); color: var(--accent); }

  .btn-export {
    padding: 9px 18px;
    border: none;
    background: var(--green);
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    color: #fff;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .btn-export:hover { background: #047857; }
  .btn-export:disabled { opacity: 0.5; cursor: not-allowed; }

  .warnings-box {
    background: var(--amber-bg);
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 1.5rem;
  }

  .warnings-box h4 {
    font-size: 12px;
    font-weight: 600;
    color: var(--amber);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
  }

  .warnings-box ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .warnings-box li {
    font-size: 12px;
    color: #92400e;
    display: flex;
    gap: 6px;
    align-items: flex-start;
  }

  .claim-block {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 1.5rem;
    overflow: hidden;
  }

  .claim-block-header {
    padding: 1rem 1.5rem;
    background: var(--navy);
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
  }

  .claim-number-badge {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .claim-badge {
    font-size: 11px;
    font-family: var(--mono);
    font-weight: 600;
    color: var(--navy);
    background: var(--accent);
    padding: 3px 10px;
    border-radius: 4px;
  }

  .claim-type {
    font-size: 12px;
    color: rgba(255,255,255,0.45);
    font-family: var(--mono);
  }

  .claim-chevron {
    color: rgba(255,255,255,0.4);
    font-size: 12px;
    transition: transform 0.2s;
  }

  .claim-chevron.open { transform: rotate(180deg); }

  .claim-text-preview {
    padding: 0.75rem 1.5rem;
    background: rgba(15,31,61,0.04);
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    color: var(--text-2);
    font-family: var(--mono);
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .elements-table {
    width: 100%;
    border-collapse: collapse;
  }

  .elements-table th {
    padding: 10px 16px;
    background: var(--surface-2);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-2);
    text-align: left;
    border-bottom: 1px solid var(--border);
  }

  .elements-table td {
    padding: 14px 16px;
    vertical-align: top;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    line-height: 1.55;
  }

  .elements-table tr:last-child td { border-bottom: none; }
  .elements-table tr:nth-child(even) td { background: var(--surface); }

  .col-element { width: 28%; color: var(--text); }
  .col-evidence { width: 50%; }
  .col-status { width: 22%; }

  .element-index {
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 600;
    color: var(--text-3);
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .element-text { color: var(--text); }

  .evidence-quote {
    background: var(--surface-2);
    border-left: 3px solid var(--accent);
    padding: 8px 12px;
    border-radius: 0 6px 6px 0;
    font-size: 12px;
    font-family: var(--mono);
    color: var(--text);
    line-height: 1.5;
    margin-bottom: 8px;
    word-break: break-word;
  }

  .evidence-explanation {
    font-size: 12px;
    color: var(--text-2);
    line-height: 1.5;
  }

  .no-evidence {
    color: var(--text-3);
    font-style: italic;
    font-size: 12px;
  }

  .confidence-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    font-family: var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .confidence-high { background: var(--green-bg); color: var(--green); }
  .confidence-medium { background: var(--amber-bg); color: var(--amber); }
  .confidence-low { background: var(--red-bg); color: var(--red); }
  .confidence-none { background: var(--surface-2); color: var(--text-3); }

  .mapped-status {
    font-size: 12px;
    margin-top: 6px;
  }

  .mapped-yes { color: var(--green); }
  .mapped-no { color: var(--red); }

  .legal-disclaimer {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 12px;
    color: var(--text-2);
    margin-top: 1.5rem;
    line-height: 1.6;
  }

  .legal-disclaimer strong { color: var(--text); }
`;

function ConfidencePill({ confidence, found }) {
  if (!found) return <span className="confidence-pill confidence-none">Not mapped</span>;
  const cls = `confidence-pill confidence-${confidence || "low"}`;
  const icon = confidence === "high" ? "●" : confidence === "medium" ? "◐" : "○";
  return <span className={cls}>{icon} {confidence || "low"}</span>;
}

function ClaimBlock({ claim }) {
  const [open, setOpen] = useState(true);
  const mappedCount = claim.elements.filter((e) => e.found_evidence).length;

  return (
    <div className="claim-block">
      <div className="claim-block-header" onClick={() => setOpen((o) => !o)}>
        <div className="claim-number-badge">
          <span className="claim-badge">Claim {claim.claim_number}</span>
          <span className="claim-type">
            {claim.is_independent ? "Independent" : "Dependent"} ·{" "}
            {mappedCount}/{claim.elements.length} elements mapped
          </span>
        </div>
        <span className={`claim-chevron ${open ? "open" : ""}`}>▼</span>
      </div>

      {open && (
        <>
          <div className="claim-text-preview">
            {claim.claim_text.length > 300
              ? claim.claim_text.slice(0, 300) + "…"
              : claim.claim_text}
          </div>
          <table className="elements-table">
            <thead>
              <tr>
                <th className="col-element">Claim Element</th>
                <th className="col-evidence">Evidence from Product Document</th>
                <th className="col-status">Status</th>
              </tr>
            </thead>
            <tbody>
              {claim.elements.map((elem) => (
                <tr key={elem.element_index}>
                  <td className="col-element">
                    <div className="element-index">
                      Element {elem.element_index + 1}
                    </div>
                    <div className="element-text">{elem.element_text}</div>
                  </td>
                  <td className="col-evidence">
                    {elem.found_evidence ? (
                      <>
                        <div className="evidence-quote">
                          "{elem.evidence_passage}"
                        </div>
                        <div className="evidence-explanation">
                          {elem.explanation}
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="no-evidence">
                          No clear evidence found in provided document.
                        </div>
                        {elem.explanation && (
                          <div className="evidence-explanation" style={{ marginTop: 6 }}>
                            {elem.explanation}
                          </div>
                        )}
                      </>
                    )}
                  </td>
                  <td className="col-status">
                    <ConfidencePill
                      confidence={elem.confidence}
                      found={elem.found_evidence}
                    />
                    <div className="mapped-status">
                      {elem.found_evidence ? (
                        <span className="mapped-yes">✓ Evidence found</span>
                      ) : (
                        <span className="mapped-no">✗ No evidence</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default function ClaimChart({ result, onReset }) {
  const [exporting, setExporting] = useState(false);

  const mappedPct = result.total_elements > 0
    ? Math.round((result.elements_mapped / result.total_elements) * 100)
    : 0;

  return (
    <>
      <style>{styles}</style>

      <div className="chart-header">
        <div className="chart-meta">
          <h2>{result.patent_title}</h2>
          <div className="vs">vs. {result.product_name}</div>
          <div className="stats-row">
            <div className="stat">
              <div className="stat-value">{result.claims.length}</div>
              <div className="stat-label">Claims charted</div>
            </div>
            <div className="stat">
              <div className="stat-value">{result.total_elements}</div>
              <div className="stat-label">Total elements</div>
            </div>
            <div className="stat">
              <div className="stat-value">{result.elements_mapped}</div>
              <div className="stat-label">Elements mapped</div>
            </div>
            <div className="stat">
              <div className="stat-value">{mappedPct}%</div>
              <div className="stat-label">Coverage</div>
            </div>
          </div>
        </div>

        <div className="chart-actions">
          <button className="btn-outline" onClick={onReset}>
            ← New chart
          </button>
          <button
            className="btn-export"
            disabled={exporting}
            onClick={() => alert("Export: re-submit form to /export endpoint with same files. See README.")}
          >
            {exporting ? "Exporting..." : "⬇ Export .docx"}
          </button>
        </div>
      </div>

      {result.warnings?.length > 0 && (
        <div className="warnings-box">
          <h4>⚠ Warnings ({result.warnings.length})</h4>
          <ul>
            {result.warnings.map((w, i) => (
              <li key={i}><span>→</span><span>{w}</span></li>
            ))}
          </ul>
        </div>
      )}

      {result.claims.map((claim) => (
        <ClaimBlock key={claim.claim_number} claim={claim} />
      ))}

      <div className="legal-disclaimer">
        <strong>Attorney review required.</strong> This claim chart was generated
        with AI assistance using semantic search and Claude. All evidence mappings
        are preliminary and must be verified by a qualified patent attorney before
        use in any legal or commercial proceeding. Evidence passages that could not
        be verified against source material have been excluded automatically.
      </div>
    </>
  );
}
