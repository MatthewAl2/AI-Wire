# AI Wire — daily AI news digest

Scrapes curated AI-news RSS feeds, reduces each article to a one-line summary
using a local open-source model (via [Ollama](https://ollama.com)), and
renders a static site (`docs/`) linking back to the original articles.

Four pages are generated, matching the original design's structure:
- **`index.html`** (Home) — the most important stories overall (ranked by a
  deterministic importance heuristic, see `aiwire/importance.py`), plus a
  3-story preview of each category below.
- **`newsletter.html`** — all "news" category stories (press coverage: TechCrunch, VentureBeat, The Verge, Ars Technica).
- **`research.html`** — all "research" category stories (lab blogs, Hugging Face, MarkTechPost).
- **`community.html`** — all "community" category stories (Hacker News, r/MachineLearning).

Within each category, stories about the same event from different outlets (e.g.
TechCrunch and The Verge both covering the same layoffs) are automatically merged
into a single card with an "Also covered by" link to the other source(s) — see
`aiwire/dedupe.py` for the title-similarity heuristic.

arXiv (`cs.AI`/`cs.CL`/`cs.LG`, ~30 latest papers/run) is a special "research"
source: raw papers are only kept if their title matches an article from another
source (i.e. some outlet actually covered that paper) — see
`filter_associated()` in `aiwire/dedupe.py`. This keeps the site from being
flooded with arXiv's daily volume; it's normal for 0 papers to qualify on a
given run if nothing overlapped with press/blog coverage.

Note: Reddit's `.rss` endpoints (r/MachineLearning, r/LocalLLaMA, r/artificial)
will occasionally 429 if hit too frequently in a short window (e.g. repeated
manual test runs) - the pipeline just skips that feed for the run rather than
failing. Not an issue for normal once- or twice-daily scheduled runs.

## One-time setup

1. Install [Ollama](https://ollama.com) (already done on this machine via
   `winget install Ollama.Ollama`) and make sure it's running:
   ```
   ollama serve
   ```
   (leave this running in its own terminal, or install as a background service)

2. Pull the summarization model:
   ```
   ollama pull llama3.2:3b
   ```

3. Create a virtualenv and install Python dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```

## Running the pipeline

```
.venv\Scripts\python -m aiwire.main
```

This will:
- fetch recent entries from the feeds in `sources.yaml`
- summarize any article not already in `data/news.json` (one Ollama call per new article — cheap to re-run, already-summarized items are skipped)
- rebuild `docs/index.html`, `docs/newsletter.html`, `docs/research.html`, `docs/community.html`, and `docs/style.css`

Preview locally:
```
.venv\Scripts\python -m http.server --directory docs 8000
```
then open http://localhost:8000

## Configuring sources

Edit `sources.yaml` — each entry is `{name, url, category}` where `category`
is `news`, `research`, or `community` (controls which page it lands on and
which color pill is shown). Feeds that fail to fetch are skipped with a
warning rather than failing the whole run.

## Configuring the model

Override via environment variables before running:
```
set AIWIRE_MODEL=qwen2.5:3b-instruct
set OLLAMA_URL=http://localhost:11434/api/generate
```

## Publishing to GitHub Pages

Already set up at https://github.com/MatthewAl2/AI-Wire — pushed to `main`.
In the repo's Settings → Pages, source is the `main` branch, `/docs` folder;
the site is live at `https://matthewal2.github.io/AI-Wire/`.

## Automatic daily refresh (GitHub Actions)

`.github/workflows/refresh.yml` runs the pipeline on a schedule (13:00 UTC
daily, adjustable via the cron line) and on manual trigger (Actions tab →
"Refresh AI Wire" → Run workflow). It installs Ollama and the model fresh on
each GitHub-hosted runner (cached between runs via `actions/cache` so it
doesn't re-download every time), runs `python -m aiwire.main`, and pushes the
regenerated `docs/` + `data/news.json` back to `main` if anything changed.

No secrets to configure — it uses the workflow's automatically-provided
`GITHUB_TOKEN` to push, since it's committing to the same repo.
