"""Keyword-based Resume Match Analyzer.

NOTE: This is a simple keyword matcher, not an ML/NLP model. It looks for
known skills (SKILL_BANK plus a few aliases) in the job description and
compares them with the skills the user lists. It cannot understand context,
seniority, or synonyms beyond ALIASES.
"""
import re

SKILL_BANK = [
    "python", "sql", "pandas", "numpy", "streamlit", "flask", "django", "fastapi",
    "java", "javascript", "typescript", "react", "node.js", "html", "css",
    "c++", "c#", "git", "github", "docker", "kubernetes", "aws", "azure", "gcp",
    "mysql", "postgresql", "mongodb", "sqlite", "excel", "power bi", "tableau",
    "postman", "selenium", "jira", "rest api", "api testing", "manual testing",
    "test cases", "regression testing", "machine learning", "data analysis",
    "linux", "ci/cd", "agile", "scikit-learn", "tensorflow",
]
ALIASES = {
    "js": "javascript", "node": "node.js", "nodejs": "node.js", "postgres": "postgresql",
    "ml": "machine learning", "sklearn": "scikit-learn", "powerbi": "power bi",
    "k8s": "kubernetes", "restful api": "rest api",
}


def _present(term: str, text: str) -> bool:
    return re.search(rf"(?<![\w+#]){re.escape(term)}(?![\w+#])", text) is not None


def find_skills(text: str, bank=SKILL_BANK) -> list:
    """Return known skills (in SKILL_BANK order) mentioned in `text`."""
    text = text.lower()
    terms = {s: s for s in bank}
    terms.update({a: c for a, c in ALIASES.items() if c in bank})
    found = {canon for term, canon in terms.items() if _present(term, text)}
    return [s for s in bank if s in found]


def analyze(resume_skills: str, jd: str) -> dict:
    mine = {ALIASES.get(s.strip().lower(), s.strip().lower())
            for s in re.split(r"[,\n]", resume_skills) if s.strip()}
    required = find_skills(jd)
    matched = [s for s in required if s in mine]
    missing = [s for s in required if s not in mine]
    pct = round(100 * len(matched) / len(required)) if required else 0
    return {"matched": matched, "missing": missing, "score": pct,
            "percent": pct, "total": len(required)}
