"""Merge near-duplicate stories (same event covered by multiple outlets) within a category."""
import re

STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "is", "are", "with", "its",
    "has", "have", "after", "over", "at", "by", "as", "that", "this", "from", "new",
    "says", "said", "will", "be", "amid", "how", "why", "what", "into", "out", "up",
    "down", "now", "than", "just", "more", "not", "but", "or", "it", "your", "you",
    "ai", "artificial", "intelligence",
}

WORD_RE = re.compile(r"[a-z0-9]+")

MIN_SHARED_TOKENS = 2
MIN_TOKENS = 3
OVERLAP_THRESHOLD = 0.6


def _tokens(title):
    words = WORD_RE.findall(title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _similar(a_tokens, b_tokens):
    # Overlap coefficient (intersection / smaller set), not Jaccard: two outlets
    # covering the same event often write titles of very different length/detail
    # (e.g. "Microsoft is laying off 4,800 employees" vs "Microsoft lays off nearly
    # 5,000 employees across Xbox, commercial sales") - Jaccard over-penalizes the
    # longer title's extra detail words, overlap coefficient does not.
    if len(a_tokens) < MIN_TOKENS or len(b_tokens) < MIN_TOKENS:
        return False
    intersection = a_tokens & b_tokens
    if len(intersection) < MIN_SHARED_TOKENS:
        return False
    smaller = min(len(a_tokens), len(b_tokens))
    return len(intersection) / smaller >= OVERLAP_THRESHOLD


def merge_duplicates(items):
    """items: list of prepared item dicts (must include 'title', 'importance', '_published_dt').

    Returns a new list where near-duplicate items (same headline topic, different
    outlets) are merged: the highest-importance (then most recent) item is kept,
    annotated with a 'related' list of the other outlets that covered the same story.
    """
    n = len(items)
    token_cache = [_tokens(it["title"]) for it in items]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for i in range(n):
        for j in range(i + 1, n):
            if _similar(token_cache[i], token_cache[j]):
                union(i, j)

    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(items[i])

    merged = []
    for group in clusters.values():
        group.sort(key=lambda it: (it["importance"], it["_published_dt"]), reverse=True)
        primary, *rest = group
        primary = {
            **primary,
            "related": [
                {"source": r["source"], "link": r["link"], "relative_time": r["relative_time"]}
                for r in rest
            ],
        }
        merged.append(primary)

    merged.sort(key=lambda it: it["_published_dt"], reverse=True)
    return merged


def filter_associated(items, extra_anchor_titles=None):
    """Drop any item flagged 'requires_association' (e.g. raw arXiv papers) unless
    its title matches an already-fetched non-flagged article, or one of
    extra_anchor_titles (titles of already-stored articles from prior runs).

    This keeps arXiv coverage limited to papers notable enough that some outlet
    has actually written about them, instead of dumping the full daily arXiv
    listing onto the site.
    """
    anchors = [it["title"] for it in items if not it.get("requires_association")]
    anchors.extend(extra_anchor_titles or [])
    anchor_tokens = [_tokens(t) for t in anchors]

    kept = []
    for it in items:
        if not it.get("requires_association"):
            kept.append(it)
            continue
        it_tokens = _tokens(it["title"])
        if any(_similar(it_tokens, at) for at in anchor_tokens):
            kept.append(it)
    return kept
