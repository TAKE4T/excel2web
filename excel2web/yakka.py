from __future__ import annotations

import re
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@dataclass(frozen=True)
class YakkaResult:
    drug_name: str
    price_text: str
    url: str


class YakkaClient:
    """Very small client for yakka-search.com.

    This implementation intentionally stays conservative:
    - Adds timeouts
    - Retries only for transient network errors
    - Performs a tiny delay between requests to reduce load

    Note: The HTML structure may change; extraction is best-effort.
    """

    def __init__(
        self,
        base_url: str = "https://yakka-search.com",
        timeout_seconds: float = 15.0,
        min_interval_seconds: float = 0.5,
        user_agent: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.min_interval_seconds = min_interval_seconds
        self._last_request_at = 0.0
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent
                or "excel2web/0.1 (+https://github.com/TAKE4T/excel2web)",
            }
        )

    def _sleep_if_needed(self) -> None:
        if self.min_interval_seconds <= 0:
            return
        now = time.time()
        delta = now - self._last_request_at
        if delta < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - delta)

    @retry(
        retry=retry_if_exception_type(
            (
                requests.Timeout,
                requests.ConnectionError,
                requests.HTTPError,
            )
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def search_price_text(self, drug_name: str) -> YakkaResult:
        self._sleep_if_needed()

        # 実サイトの検索URLは変わり得るので、まずはよくあるパターンで試す。
        # うまくいかない場合でも「Error」扱いではなく Not Found に寄せる。
        url = f"{self.base_url}/search"
        params = {"word": drug_name}

        resp = self.session.get(url, params=params, timeout=self.timeout_seconds)
        self._last_request_at = time.time()
        resp.raise_for_status()

        price_text = extract_price_text(resp.text)
        if not price_text:
            price_text = "Not Found"

        return YakkaResult(drug_name=drug_name, price_text=price_text, url=str(resp.url))


_PRICE_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)(?:\s*)?(円|点)")


def extract_price_text(html: str) -> str | None:
    """Try to extract a price-like text from search result HTML.

    Strategy:
    1) Prefer elements that look like price fields (class contains 'price' or 'yakka')
    2) Fallback to regex search for something like '123.4円' or '123円'

    Returns:
        str | None: extracted snippet, or None.
    """

    soup = BeautifulSoup(html, "lxml")

    # Heuristic 1: find any element with class/id containing price-ish keywords
    candidates: list[str] = []
    for el in soup.select("[class*='price' i], [class*='yakka' i], [id*='price' i], [id*='yakka' i]"):
        text = " ".join(el.get_text(" ", strip=True).split())
        if text:
            candidates.append(text)

    for text in candidates:
        m = _PRICE_RE.search(text)
        if m:
            return f"{m.group(1)}{m.group(2)}"

    # Fallback: search whole document text
    whole = " ".join(soup.get_text(" ", strip=True).split())
    m = _PRICE_RE.search(whole)
    if m:
        return f"{m.group(1)}{m.group(2)}"

    return None
