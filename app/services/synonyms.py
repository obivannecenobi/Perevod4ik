"""Synonyms lookup service."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


def fetch_synonyms(word: str, lang: str = "en") -> list[str]:
    """Return a list of synonyms for *word*.

    The function uses the public Datamuse API. Network failures are
    silently ignored and an empty list is returned in such cases.
    """

    base = "https://api.datamuse.com/words"
    query = urllib.parse.urlencode({"rel_syn": word, "v": lang})
    url = f"{base}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    return [item["word"] for item in data if "word" in item]
