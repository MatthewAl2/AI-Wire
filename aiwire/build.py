"""Render the static site (home + 3 category pages) from the news store."""
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .dedupe import merge_duplicates

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "docs"
STYLE_SRC = ROOT / "style.css"

CATEGORY_META = {
    "news": {
        "label": "News", "avatar_color": "#e08a2c", "heading": "Newsletter & Journalism",
        "description": "Daily coverage from major outlets on product launches, industry moves, and policy.",
        "file": "newsletter.html", "nav_key": "newsletter", "grid_id": "grid-news",
    },
    "research": {
        "label": "Research", "avatar_color": "#7c4dff", "heading": "Research",
        "description": "Model releases, papers, and technical deep-dives from labs and the open-source ecosystem.",
        "file": "research.html", "nav_key": "research", "grid_id": "grid-research",
    },
    "community": {
        "label": "Community", "avatar_color": "#0fb3a3", "heading": "Community Pulse",
        "description": "What builders on Hacker News and Reddit are discussing about AI right now.",
        "file": "community.html", "nav_key": "community", "grid_id": "grid-community",
    },
}

EXTRA_CSS = """
/* ---------- generated content banners ---------- */
.node-banner{ display:flex; align-items:flex-end; padding:14px 16px; }
.banner-news{ background:linear-gradient(135deg,#e08a2c,#ffcf8f); }
.banner-research{ background:linear-gradient(135deg,#7c4dff,#c6b6ff); }
.banner-community{ background:linear-gradient(135deg,#0fb3a3,#8fe9df); }
.banner-source{
  font-family:'IBM Plex Mono', monospace; font-size:12px; font-weight:700;
  color:rgba(255,255,255,0.95); letter-spacing:0.05em; text-transform:uppercase;
  text-shadow:0 1px 2px rgba(0,0,0,0.15);
}
.card .meta{ justify-content:space-between; flex-wrap:wrap; row-gap:6px; }
.src-link{ color:var(--brand); font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:600; white-space:nowrap; }
.src-link:hover{ text-decoration:underline; }
.empty-state{ color:var(--ink-soft); padding:40px 0; text-align:center; }
.related-sources{
  font-family:'IBM Plex Mono', monospace; font-size:11.5px; color:var(--ink-soft);
  padding-top:10px; margin-top:2px; border-top:1px dashed var(--line);
}
.related-sources a{ color:var(--brand); font-weight:600; }
.related-sources a:hover{ text-decoration:underline; }

/* ---------- sort toggle ---------- */
.list-toolbar{ display:flex; justify-content:flex-end; margin-bottom:14px; }
.sort-toggle{
  display:inline-flex; background:var(--paper); border:1px solid var(--line);
  border-radius:100px; padding:3px; gap:2px;
}
.sort-btn{
  font-family:'IBM Plex Mono', monospace; font-size:11px; font-weight:600;
  letter-spacing:0.03em; text-transform:uppercase; color:var(--ink-soft);
  background:none; border:none; border-radius:100px; padding:7px 14px; cursor:pointer;
}
.sort-btn.active{ background:var(--card); color:var(--brand); box-shadow:var(--shadow); }
.sort-btn:hover:not(.active){ color:var(--ink); }
"""

SORT_JS = """(function(){
  function sortGrid(grid, mode){
    var cards = Array.prototype.slice.call(grid.children);
    cards.sort(function(a, b){
      if(mode === 'importance'){
        var d = parseInt(b.dataset.importance, 10) - parseInt(a.dataset.importance, 10);
        if(d !== 0) return d;
      }
      return parseInt(b.dataset.published, 10) - parseInt(a.dataset.published, 10);
    });
    cards.forEach(function(card){ grid.appendChild(card); });
  }

  document.querySelectorAll('.sort-toggle').forEach(function(toggle){
    var grid = document.getElementById(toggle.getAttribute('data-target'));
    if(!grid) return;
    var buttons = toggle.querySelectorAll('.sort-btn');
    buttons.forEach(function(btn){
      btn.addEventListener('click', function(){
        buttons.forEach(function(b){ b.classList.remove('active'); });
        btn.classList.add('active');
        sortGrid(grid, btn.getAttribute('data-sort'));
      });
    });
  });
})();
"""


def _relative_time(dt, now):
    seconds = (now - dt).total_seconds()
    if seconds < 60:
        return "just now"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)}h ago"
    days = hours / 24
    if days < 7:
        return f"{int(days)}d ago"
    return dt.strftime("%b %d, %Y")


def _initials(name):
    words = [w for w in name.split() if w]
    if not words:
        return "AI"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _prepare(item, now):
    published = datetime.fromisoformat(item["published"])
    meta = CATEGORY_META.get(item["category"], CATEGORY_META["news"])
    return {
        **item,
        "category_label": meta["label"],
        "avatar_color": meta["avatar_color"],
        "initials": _initials(item["source"]),
        "relative_time": _relative_time(published, now),
        "importance": item.get("importance", 3),
        "published_ts": int(published.timestamp()),
        "_published_dt": published,
    }


def build(store):
    """Render docs/index.html + docs/{newsletter,research,community}.html + docs/style.css + docs/sort.js.

    Returns the total number of summarized items rendered across all pages.
    """
    now = datetime.now(timezone.utc)

    prepared = [_prepare(it, now) for it in store.values() if it.get("summary")]

    by_category = {cat: [] for cat in CATEGORY_META}
    for item in prepared:
        by_category.setdefault(item["category"], by_category["news"]).append(item)

    for cat in by_category:
        by_category[cat] = merge_duplicates(by_category[cat])

    items = [item for cat_items in by_category.values() for item in cat_items]

    hero_items = sorted(items, key=lambda it: (it["importance"], it["_published_dt"]), reverse=True)[:3]

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = now.strftime("%Y-%m-%d %H:%M UTC")

    home_tpl = env.get_template("index.html.jinja")
    sections = [
        {
            "label": CATEGORY_META[cat]["heading"],
            "href": CATEGORY_META[cat]["file"],
            "grid_id": f"home-{CATEGORY_META[cat]['grid_id']}",
            "cards": by_category[cat][:3],
        }
        for cat in ("news", "research", "community")
    ]
    home_html = home_tpl.render(hero_items=hero_items, sections=sections, generated_at=generated_at)
    (DOCS_DIR / "index.html").write_text(home_html, encoding="utf-8")

    cat_tpl = env.get_template("category.html.jinja")
    for cat, meta in CATEGORY_META.items():
        html_out = cat_tpl.render(
            category=cat,
            category_label=meta["label"],
            heading=meta["heading"],
            description=meta["description"],
            active=meta["nav_key"],
            grid_id=meta["grid_id"],
            items=by_category[cat],
            generated_at=generated_at,
        )
        (DOCS_DIR / meta["file"]).write_text(html_out, encoding="utf-8")

    base_css = STYLE_SRC.read_text(encoding="utf-8")
    (DOCS_DIR / "style.css").write_text(base_css + "\n" + EXTRA_CSS, encoding="utf-8")
    (DOCS_DIR / "sort.js").write_text(SORT_JS, encoding="utf-8")

    return len(items)
