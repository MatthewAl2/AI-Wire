"""CLI entrypoint: fetch -> filter -> summarize (new items only) -> store -> build."""
from . import build as build_mod
from . import fetch, importance, store
from .dedupe import filter_associated
from .summarize import SummarizeError, summarize


def main():
    print("Fetching feeds...")
    fetched = fetch.fetch_all()

    current = store.load()
    before = len(fetched)
    anchor_titles = [it["title"] for it in current.values() if not it.get("requires_association")]
    fetched = filter_associated(fetched, extra_anchor_titles=anchor_titles)
    dropped = before - len(fetched)
    print(f"  {len(fetched)} recent entries found" + (f" ({dropped} unassociated arXiv papers skipped)" if dropped else ""))

    new_count = 0
    error_count = 0

    for item in fetched:
        if item["id"] in current and current[item["id"]].get("summary"):
            continue
        try:
            item["summary"] = summarize(item["title"], item["description"])
            item["importance"] = importance.score(item["title"], item["description"], item["category"])
        except SummarizeError as exc:
            print(f"  [summarize-error] {item['title'][:60]}: {exc}")
            error_count += 1
            continue
        current[item["id"]] = item
        new_count += 1
        print(f"  + {item['source']}: {item['summary']}")

    current = store.prune(current)
    store.save(current)

    total_rendered = build_mod.build(current)
    print(f"\nDone. {new_count} new summaries, {error_count} errors, {total_rendered} items on site.")
    print("Open docs/index.html in a browser, or run: python -m http.server --directory docs 8000")


if __name__ == "__main__":
    main()
