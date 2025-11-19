import { useState, type FormEvent, type ChangeEvent } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

interface MatchInfo {
  overall_score: number;
  required_match_fraction: number;
  nice_to_have_match_fraction: number;
  matched_required_skills: string[];
  missing_required_skills: string[];
  matched_nice_to_have: string[];
  missing_nice_to_have: string[];
}

interface AdviceInfo {
  tailored_summary: string;
  rewritten_bullets: string[];
  skills_to_highlight: string[];
  skills_to_develop: string[];
}

interface ApiResponse {
  match: MatchInfo;
  jd: {
    title: string;
    company: string;
    location: string;
    required_skills: string[];
    nice_to_have_skills: string[];
    responsibilities: string[];
    keywords: string[];
  };
  resume: {
    name: string;
    headline: string;
    skills: string[];
    tools: string[];
  };
  advice?: AdviceInfo;
}

function App() {
  const [jdText, setJdText] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const [match, setMatch] = useState<MatchInfo | null>(null);
  const [advice, setAdvice] = useState<AdviceInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    if (file && file.type !== "application/pdf") {
      setError("Please upload a PDF file only.");
      setResumeFile(null);
      return;
    }
    setError(null);
    setResumeFile(file);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!jdText.trim()) {
      setError("Please paste a job description.");
      return;
    }
    if (!resumeFile) {
      setError("Please upload your resume as a PDF.");
      return;
    }

    const formData = new FormData();
    formData.append("jd_text", jdText);
    formData.append("resume_file", resumeFile);

    setIsLoading(true);
    setError(null);
    setMatch(null);
    setAdvice(null);

    try {
      const res = await fetch(`${API_BASE}/api/jobmatch_pdf`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server error ${res.status}: ${text}`);
      }

      const data: ApiResponse = await res.json();
      setMatch(data.match);
      setAdvice(data.advice ?? null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Something went wrong while analyzing.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="card">
        <h1>JobMatch Agent</h1>
        <p className="subtitle">
          Paste a job description, upload your resume PDF, and let the agent
          score your fit, highlight gaps, and rewrite bullets for you.
        </p>

        <form onSubmit={handleSubmit} className="form-grid">
          <div className="field">
            <label className="field-label">Job description</label>
            <textarea
              className="textarea"
              rows={7}
              placeholder="Paste the job description here..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </div>

          <div className="field">
            <label className="field-label">Resume PDF</label>
            <div className="file-row">
              <input
                id="resume-file"
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />
              <label htmlFor="resume-file" className="file-button">
                {resumeFile ? "Change PDF" : "Upload Resume PDF"}
              </label>
              <span className="file-name">
                {resumeFile ? resumeFile.name : "No file selected"}
              </span>
            </div>
            <p className="hint">Only .pdf files are accepted.</p>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <button
            className="primary-button"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner" />
                <span>Analyzing…</span>
              </>
            ) : (
              "Analyze fit"
            )}
          </button>
        </form>

        {match && (
          <div className="results">
            <h2>Match score</h2>
            <div className="score-row">
              <div className="score-circle">
                <span>{match.overall_score}</span>
              </div>
              <div className="score-details">
                <p>
                  <strong>Required skills match:</strong>{" "}
                  {(match.required_match_fraction * 100).toFixed(0)}%
                </p>
                <p>
                  <strong>Nice-to-have skills match:</strong>{" "}
                  {(match.nice_to_have_match_fraction * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            <div className="pill-groups">
              <div>
                <h3>Matched required skills</h3>
                <div className="pill-row">
                  {match.matched_required_skills.map((s) => (
                    <span key={s} className="pill pill-good">
                      {s}
                    </span>
                  ))}
                  {match.matched_required_skills.length === 0 && (
                    <span className="pill pill-muted">None detected</span>
                  )}
                </div>
              </div>

              <div>
                <h3>Missing required skills</h3>
                <div className="pill-row">
                  {match.missing_required_skills.map((s) => (
                    <span key={s} className="pill pill-bad">
                      {s}
                    </span>
                  ))}
                  {match.missing_required_skills.length === 0 && (
                    <span className="pill pill-muted">None detected</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {advice && (
          <div className="results">
            <h2>Tailored resume advice</h2>
            <p className="summary">{advice.tailored_summary}</p>

            {advice.rewritten_bullets.length > 0 && (
              <div>
                <h3>Suggested bullet rewrites</h3>
                <ul className="bullet-list">
                  {advice.rewritten_bullets.map((b, idx) => (
                    <li key={idx}>{b}</li>
                  ))}
                </ul>
              </div>
            )}

            {advice.skills_to_highlight.length > 0 && (
              <div>
                <h3>Skills to emphasize</h3>
                <div className="pill-row">
                  {advice.skills_to_highlight.map((s) => (
                    <span key={s} className="pill pill-good">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {advice.skills_to_develop.length > 0 && (
              <div>
                <h3>Skills to develop</h3>
                <div className="pill-row">
                  {advice.skills_to_develop.map((s) => (
                    <span key={s} className="pill pill-warning">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
