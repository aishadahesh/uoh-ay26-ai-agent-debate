"""Minimal web-search tool used to provide debate evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import quote_plus


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str


class WebSearchTool:
    """Searches the web through a lightweight HTML endpoint with timeouts."""

    def __init__(self, enabled: bool, timeout: float, max_results: int) -> None:
        self.enabled = enabled
        self.timeout = timeout
        self.max_results = max_results

    def search(self, query: str) -> list[SearchResult]:
        """Return best-effort search result links; failures degrade gracefully."""

        if not self.enabled:
            return []
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            import requests

            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "agent-debate"},
            )
            response.raise_for_status()
        except Exception:
            return []
        pattern = re.compile(r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>')
        results: list[SearchResult] = []
        for link, title in pattern.findall(response.text):
            clean_title = re.sub("<.*?>", "", unescape(title))
            results.append(SearchResult(title=clean_title, url=unescape(link)))
            if len(results) >= self.max_results:
                break
        return results
