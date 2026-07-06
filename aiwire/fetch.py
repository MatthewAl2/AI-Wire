"""Pull curated AI-news RSS feeds and normalize entries."""
import hashlib
import html
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = ROOT / "sources.yaml"

USER_AGENT = "AIWireBot/0.1 (+https://github.com/; personal news digest)"
TAG_RE = re.compile(r"<[^>]+>")


def load_sources():
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def _clean_text(raw):
    if not raw:
        return ""
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _entry_published(entry):
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch_all(max_age_days=7):
    """Return a list of normalized article dicts from all configured sources."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    items = []

    for i, source in enumerate(load_sources()):
        name = source["name"]
        url = source["url"]
        category = source.get("category", "news")
        requires_association = source.get("requires_association", False)
        if i > 0:
            # reddit.com in particular will 429 several back-to-back feed
            # requests from the same client - a bigger gap avoids that.
            time.sleep(6 if "reddit.com" in url else 1.5)
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception as exc:
            print(f"  [skip] {name}: {exc}")
            continue

        for entry in parsed.entries[:30]:
            link = (entry.get("link") or "").strip()
            title = _clean_text(entry.get("title", ""))
            if not link or not title:
                continue

            published = _entry_published(entry)
            if published and published < cutoff:
                continue

            description = _clean_text(entry.get("summary") or entry.get("description") or "")
            item_id = hashlib.sha1(link.encode("utf-8")).hexdigest()

            items.append({
                "id": item_id,
                "title": title,
                "description": description[:1500],
                "link": link,
                "source": name,
                "category": category,
                "published": (published or datetime.now(timezone.utc)).isoformat(),
                "requires_association": requires_association,
            })

    return items
