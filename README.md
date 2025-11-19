# JobMatch Agent

An AI-powered tool that helps you tailor your resume to specific job postings.

You paste a **job description** and upload your **resume as a PDF**.  
The app uses OpenAI's model to:

- Parse the job description into structured requirements
- Extract skills and tools from your resume
- Compute a transparent **match score**
- Highlight **matched / missing skills**
- Generate **tailored advice & improved resume bullet points**

Backend: **FastAPI (Python)**  
Frontend: **React + Vite + TypeScript**  
LLM: **OpenAI `gpt-5.1`**

---

## Project structure

```text
jobmatch-agent/
├─ data/                 # (optional) example JDs / resumes
├─ frontend/             # React + Vite UI
├─ src/
│  ├─ api/
│  │  └─ main.py         # FastAPI app & /api/jobmatch endpoint
│  ├─ agent.py           # LLM calls, parsing, matching, advice
│  ├─ matching.py        # (optional) extra matching utilities
│  └─ parsing.py         # (optional) helpers
├─ .env                  # OPENAI_API_KEY (not committed; gitignored)
├─ requirements.txt      # Python deps
└─ README.md
