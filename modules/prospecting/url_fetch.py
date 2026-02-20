from __future__ import annotations

import requests
from bs4 import BeautifulSoup


def fetch_award_text(url: str, timeout: int = 10) -> str:
    """Fetch a URL and return cleaned visible text stripped of HTML markup."""
    response = requests.get(url, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch '{url}': HTTP {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned
