import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path 

from dotenv import load_dotenv
from openai import OpenAI

# Load env vars and init OpenAI client
BASE_DIR = Path(__file__).resolve().parent.parent  
load_dotenv(BASE_DIR / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-5.1" 


# ---------- Data structures ----------

@dataclass
class JDInfo:
    title: str
    company: str
    location: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    responsibilities: List[str]
    keywords: List[str]


@dataclass
class ResumeInfo:
    name: str
    headline: str
    skills: List[str]
    tools: List[str]


# ---------- LLM helper functions ----------

def _call_llm_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Helper: call OpenAI and force a JSON object response that we can json.loads().
    """
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    return json.loads(content)


def _extract_jd_info(jd_text: str) -> JDInfo:
    system = (
        "You are an assistant that extracts structured information from job descriptions "
        "for software and data roles. Always respond with a single JSON object that can "
        "be parsed by json.loads in Python. No extra commentary."
    )

    user = f"""
    Extract the following fields from this job description:

    - title (string)
    - company (string or empty string if not obvious)
    - location (string or 'Remote' if clearly remote, otherwise empty string if unknown)
    - required_skills (list of core skills/technologies that seem REQUIRED)
    - nice_to_have_skills (list of skills labelled as preferred/plus/nice-to-have)
    - responsibilities (3-10 bullet-style strings summarizing duties)
    - keywords (8-20 important technical or domain keywords from the JD)

    Very important constraints:

    - Only extract skills that a candidate would realistically list on a resume or skills section.
      Do NOT treat soft phrases like "ability to work in a fast-paced environment", "strong work ethic",
      or "excellent communication skills" as separate skills unless they would actually appear as
      bullet points or items in a real resume.
    - For responsibilities / boilerplate text, ignore generic company marketing fluff and "About us"
      style paragraphs. Focus on the technical stack, core responsibilities, and core knowledge areas.
    - If the posting contains a long wall of text, be selective: focus on the sections that clearly list
      requirements, preferred qualifications, or responsibilities.

    Return JSON in this exact schema:

    {{
      "title": "",
      "company": "",
      "location": "",
      "required_skills": [],
      "nice_to_have_skills": [],
      "responsibilities": [],
      "keywords": []
    }}

    Job description:
    \"\"\"
    {jd_text}
    \"\"\"
    """

    data = _call_llm_json(system, user)

    return JDInfo(
        title=data.get("title", "").strip(),
        company=data.get("company", "").strip(),
        location=data.get("location", "").strip(),
        required_skills=[s.strip() for s in data.get("required_skills", [])],
        nice_to_have_skills=[s.strip() for s in data.get("nice_to_have_skills", [])],
        responsibilities=[s.strip() for s in data.get("responsibilities", [])],
        keywords=[s.strip() for s in data.get("keywords", [])],
    )


def _extract_resume_info(resume_text: str) -> ResumeInfo:
    system = (
        "You are an assistant that extracts structured information from a candidate's resume. "
        "Always respond with a single JSON object that can be parsed by json.loads in Python. "
        "No extra commentary."
        "Only put concrete technologies / skills / CS topics in skills and tools."
        "If you see vague traits like “hard-working”, “problem solver”, “fast-paced environment”, put those in a separate soft_traits list."
    )

    user = f"""
    From this resume text, extract:

    - name (best guess of the candidate's name; empty string if not obvious)
    - headline (1 short phrase like 'CS student', 'Software Engineer intern', etc.)
    - skills (list of skills/technologies the candidate claims)
    - tools (list of tools/platforms/frameworks they use)

    Return JSON in this exact schema:

    {{
      "name": "",
      "headline": "",
      "skills": [],
      "tools": []
    }}

    Resume text:
    \"\"\"
    {resume_text}
    \"\"\"
    """

    data = _call_llm_json(system, user)

    return ResumeInfo(
        name=data.get("name", "").strip(),
        headline=data.get("headline", "").strip(),
        skills=[s.strip() for s in data.get("skills", [])],
        tools=[s.strip() for s in data.get("tools", [])],
    )

# ---------- Matching logic ----------

def _compute_match(jd: JDInfo, resume: ResumeInfo) -> Dict[str, Any]:
    """
    Simple interpretable scoring: overlap between required/nice-to-have skills
    and candidate skills/tools.
    """
    resume_skillset = {s.lower() for s in (resume.skills + resume.tools)}
    required = {s.lower() for s in jd.required_skills}
    nice = {s.lower() for s in jd.nice_to_have_skills}

    matched_required = sorted(required & resume_skillset)
    missing_required = sorted(required - resume_skillset)
    matched_nice = sorted(nice & resume_skillset)
    missing_nice = sorted(nice - resume_skillset)

    # Weighted score: required = 70%, nice-to-have = 30%
    required_score = len(matched_required) / len(required) if required else 1.0
    nice_score = len(matched_nice) / len(nice) if nice else 1.0

    overall_score = round((required_score * 0.7 + nice_score * 0.3) * 100)

    return {
        "overall_score": overall_score,
        "required_match_fraction": round(required_score, 3),
        "nice_to_have_match_fraction": round(nice_score, 3),
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_nice_to_have": matched_nice,
        "missing_nice_to_have": missing_nice,
    }


def _generate_advice(jd: JDInfo, resume: ResumeInfo,
                     jd_text: str, resume_text: str) -> Dict[str, Any]:
    """
    Use the LLM as an expert recruiter / career coach to:
    - take a holistic view of the match (not just word overlap),
    - suggest rewritten bullets,
    - highlight strengths and growth areas.
    """
    system = (
        "You are an expert technical recruiter and career coach for early-career "
        "software engineers and data people. "
        "You evaluate candidates holistically: responsibilities, tech stack, "
        "soft skills, and trajectory. You ignore generic boilerplate like "
        "'About the company', benefits, EEO statements, and marketing fluff. "
        "Always respond with a single JSON object that can be parsed by json.loads()."
    )

    user = f"""
Job description (parsed struct):
{jd}

Resume (parsed struct):
{resume}

Full job description text (may contain extra fluff – IGNORE boilerplate):
\"\"\"{jd_text}\"\"\"

Full resume text:
\"\"\"{resume_text}\"\"\"

Using a holistic view (not just exact word matches), do ALL of the following:

1. Decide how strong a fit the candidate is for THIS SPECIFIC ROLE, on a scale 0–100.
   Consider responsibilities, required skills, level of experience

2. Write a brief, tailored summary that a recruiter could paste into a note,
   explaining why the candidate is or is not a strong fit.

3. Propose 2-4 improved resume bullet points that the candidate could use
   to better mirror the job description while staying truthful to the resume.

4. List skills/experiences that the candidate should emphasize more
   on their resume for THIS role.

5. List skills/experiences that the candidate should develop to be a stronger fit
   (can include soft skills or domain expertise).

Return JSON in this schema:

{{
  "tailored_summary": "string, 2–4 sentences",
  "rewritten_bullets": ["bullet 1", "bullet 2", "..."],
  "skills_to_highlight": ["skill 1", "skill 2", "..."],
  "skills_to_develop": ["skill 1", "skill 2", "..."]
}}
"""

    return _call_llm_json(system, user)


# ---------- Public entry point used by FastAPI ----------

def run_jobmatch_agent(jd_text: str, resume_text: str) -> Dict[str, Any]:
    """
    Main entry point called by FastAPI.

    1. Use LLM to parse JD into structured fields.
    2. Use LLM to parse resume into structured fields.
    3. Compute a transparent skill-overlap score in Python.
    4. Ask the LLM for holistic fit + tailored advice.
    """
    jd_info = _extract_jd_info(jd_text)
    resume_info = _extract_resume_info(resume_text)
    match_info = _compute_match(jd_info, resume_info)
    advice = _generate_advice(jd_info, resume_info, jd_text, resume_text)

    return {
        "jd": jd_info,
        "resume": resume_info,
        "match": match_info,
        "advice": advice,
    }
