"""One-line summaries via a local Ollama model."""
import os

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("AIWIRE_MODEL", "llama3.2:3b")

PROMPT_TEMPLATE = """Summarize the following AI news article in exactly one clear, factual sentence (max 25 words), for a tech-savvy reader. Do not use quotes, preamble, or any commentary about the summary itself - respond with just the single sentence.

Title: {title}

Description: {description}

One-sentence summary:"""


class SummarizeError(RuntimeError):
    pass


def summarize(title, description, retries=2, timeout=60):
    prompt = PROMPT_TEMPLATE.format(title=title, description=description or title)

    last_exc = None
    for _ in range(retries + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
                timeout=timeout,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            text = text.strip('"').strip()
            text = " ".join(text.splitlines()).strip()
            if text:
                return text
        except Exception as exc:
            last_exc = exc

    raise SummarizeError(
        f"Could not reach Ollama at {OLLAMA_URL} with model '{MODEL}'. "
        f"Make sure `ollama serve` is running and the model is pulled. Last error: {last_exc}"
    )
