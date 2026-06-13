import { useState } from "react";
import UploadPanel from "./components/UploadPanel.jsx";
import ClaimChart from "./components/ClaimChart.jsx";

const styles = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --navy: #0f1f3d;
    --navy-mid: #1a3260;
    --blue: #1e4db7;
    --blue-light: #2563eb;
    --accent: #3b82f6;
    --accent-glow: rgba(59,130,246,0.15);
    --green: #059669;
    --green-bg: #ecfdf5;
    --amber: #d97706;
    --amber-bg: #fffbeb;
    --red: #dc2626;
    --red-bg: #fef2f2;
    --surface: #f8fafc;
    --surface-2: #f1f5f9;
    --border: #e2e8f0;
    --text: #0f172a;
    --text-2: #475569;
    --text-3: #94a3b8;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'Inter', system-ui, sans-serif;
  }

  body {
    font-family: var(--sans);
    background: var(--navy);
    color: var(--text);
    min-height: 100vh;
  }

  #root { min-height: 100vh; display: flex; flex-direction: column; }

  .app-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .app-header {
    background: var(--navy);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding: 0 2rem;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    background: var(--blue-light);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }

  .logo-text {
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.01em;
  }

  .logo-sub {
    font-size: 11px;
    color: var(--text-3);
    font-weight: 400;
  }

  .header-badge {
    font-size: 11px;
    font-family: var(--mono);
    color: var(--text-3);
    background: rgba(255,255,255,0.06);
    padding: 4px 10px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
  }

  .app-main {
    flex: 1;
    background: var(--surface);
  }

  .hero {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-mid) 100%);
    padding: 3.5rem 2rem 3rem;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }

  .hero-eyebrow {
    font-size: 11px;
    font-family: var(--mono);
    letter-spacing: 0.12em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 1rem;
  }

  .hero-title {
    font-size: clamp(1.8rem, 3vw, 2.6rem);
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 0.85rem;
  }

  .hero-title span {
    color: var(--accent);
  }

  .hero-sub {
    font-size: 1rem;
    color: rgba(255,255,255,0.55);
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.6;
  }

  .pipeline-steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin-top: 2.5rem;
    flex-wrap: wrap;
    gap: 2px;
  }

  .pipeline-step {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 4px;
    font-size: 11px;
    font-family: var(--mono);
    color: rgba(255,255,255,0.5);
  }

  .pipeline-step.active {
    background: var(--accent-glow);
    border-color: var(--accent);
    color: var(--accent);
  }

  .pipeline-arrow {
    color: rgba(255,255,255,0.2);
    font-size: 12px;
    padding: 0 2px;
  }

  .content-area {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem;
  }
`;

const PIPELINE_STEPS = [
  "Extract PDF text",
  "Parse claims",
  "Chunk product doc",
  "Embed + search",
  "Map with Claude",
  "Generate chart",
];

export default function App() {
  const [result, setResult] = useState(null);
  const [activeStep, setActiveStep] = useState(-1);

  return (
    <>
      <style>{styles}</style>
      <div className="app-shell">
        <header className="app-header">
          <div className="logo">
            <div className="logo-icon">⚖️</div>
            <div>
              <div className="logo-text">ClaimChart AI</div>
              <div className="logo-sub">Patent analysis tool</div>
            </div>
          </div>
          <div className="header-badge">RAG + Claude · Built for IP teams</div>
        </header>

        <main className="app-main">
          <div className="hero">
            <div className="hero-eyebrow">AI-Powered Patent Analysis</div>
            <h1 className="hero-title">
              Map patent claims to<br />
              <span>product evidence</span> automatically
            </h1>
            <p className="hero-sub">
              Upload a patent and a product document. The AI extracts claims,
              finds supporting evidence using semantic search, and generates
              a formatted claim chart ready for attorney review.
            </p>

            <div className="pipeline-steps">
              {PIPELINE_STEPS.map((step, i) => (
                <>
                  <div
                    key={step}
                    className={`pipeline-step ${i <= activeStep ? "active" : ""}`}
                  >
                    {step}
                  </div>
                  {i < PIPELINE_STEPS.length - 1 && (
                    <span key={`arrow-${i}`} className="pipeline-arrow">→</span>
                  )}
                </>
              ))}
            </div>
          </div>

          <div className="content-area">
            {!result ? (
              <UploadPanel
                onResult={setResult}
                onStepChange={setActiveStep}
              />
            ) : (
              <ClaimChart
                result={result}
                onReset={() => { setResult(null); setActiveStep(-1); }}
              />
            )}
          </div>
        </main>
      </div>
    </>
  );
}
