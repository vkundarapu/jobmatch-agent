from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ParsedJD:
    title: str
    company: str
    location: str
    required_skills: List[str] = field(default_factory=list)
    nice_to_have_skills: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ParsedResume:
    name: str
    headline: str
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    projects: List[Dict] = field(default_factory=list)  # each: {title, description, tech, impact_metrics}
    experience: List[Dict] = field(default_factory=list) # each: {company, title, bullets, tech}
    raw_text: str = ""


def parse_jd(text: str) -> ParsedJD:
    """
    TODO: use an LLM later. For now, this is a stub so you can wire things up.
    """
    return ParsedJD(
        title="Unknown",
        company="Unknown",
        location="Unknown",
        required_skills=[],
        nice_to_have_skills=[],
        responsibilities=[],
        keywords=[],
        raw_text=text,
    )


def parse_resume(text: str) -> ParsedResume:
    """
    TODO: use an LLM later. For now, this is a stub so you can wire things up.
    """
    return ParsedResume(
        name="Unknown",
        headline="",
        skills=[],
        tools=[],
        projects=[],
        experience=[],
        raw_text=text,
    )
