"""Persist summarized items across runs so we don't re-summarize old news."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "news.json"

KEEP_DAYS = 14


def load():
    if not DATA_PATH.exists():
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(store):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def prune(store, keep_days=KEEP_DAYS):
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    kept = {}
    for item_id, item in store.items():
        try:
            published = datetime.fromisoformat(item["published"])
        except Exception:
            kept[item_id] = item
            continue
        if published >= cutoff:
            kept[item_id] = item
    return kept
