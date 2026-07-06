"""Deterministic 1-5 'how major is this story' heuristic.

Not LLM-based: asking the small local model to also self-rate importance
turned out unreliable (it would leak commentary like "I'd rate this a 4"
into the one-line summary itself). A keyword heuristic is more consistent
and keeps the summary text clean.
"""
import re

CATEGORY_BASE = {"news": 3, "research": 3, "community": 2}

HIGH_IMPACT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bfund(ing|ed|s)?\b", r"\bacqui(re|red|sition)\w*\b", r"\bbillion\b",
        r"\braises?\b", r"\blaunch(es|ed)?\b", r"\breleases?[sd]?\b", r"\blawsuit\b",
        r"\bban(s|ned)?\b", r"\bsafety\b", r"\bregulation\b", r"\bpolicy\b", r"\bipo\b",
        r"\blayoffs?\b", r"\bbreakthrough\b", r"\bpartnership\b", r"\bopen[- ]source\b",
    ]
]

MAJOR_ORGS = [
    "openai", "anthropic", "google", "deepmind", "meta", "microsoft", "mistral",
    "nvidia", "amazon", "apple", "xai", "hugging face", "alibaba", "samsung",
]


def score(title, description, category):
    text = f"{title} {description}".lower()
    value = CATEGORY_BASE.get(category, 3)
    if any(p.search(text) for p in HIGH_IMPACT_PATTERNS):
        value += 1
    if any(org in text for org in MAJOR_ORGS):
        value += 1
    return max(1, min(5, value))
