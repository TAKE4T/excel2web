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

        # NOTE: 2025-12 時点でトップページのフォームは /index.php に GET で
        #   s=<keyword>&stype=1
        # を投げている。
        url = f"{self.base_url}/index.php"
        params = {"s": drug_name, "stype": "1"}

        resp = self.session.get(url, params=params, timeout=self.timeout_seconds)
        self._last_request_at = time.time()
        resp.raise_for_status()

        price_text = extract_price_text(resp.text)
        if not price_text:
            price_text = "Not Found"

        return YakkaResult(drug_name=drug_name, price_text=price_text, url=str(resp.url))


_PRICE_RE = re.compile(r"\b(\d+(?:\.\d+)?)\b")


def extract_price_text(html: str) -> str | None:
    """Try to extract a price-like text from search result HTML.

    Strategy:
    1) Prefer elements that look like price fields (class contains 'price' or 'yakka')
    2) Fallback to regex search for something like '123.4円' or '123円'

    Returns:
        str | None: extracted snippet, or None.
    """

    soup = BeautifulSoup(html, "lxml")

    # Heuristic 1: table header contains "薬価" (mojibake-safe: search in bytes also later)
    table = soup.select_one("table")
    if table:
        headers = [th.get_text(" ", strip=True) for th in table.select("tr th")]
        # Find column index that contains the Japanese word '薬価' after best-effort decode.
        idx = None
        for i, h in enumerate(headers):
            if "薬価" in h:
                idx = i
                break

        if idx is not None:
            first_row = table.select_one("tr:nth-of-type(2)")
            if first_row:
                tds = [td.get_text(" ", strip=True) for td in first_row.select("td")]
                # th includes the leading blank column while td includes it as well, so align by idx.
                if 0 <= idx < len(tds):
                    cell = tds[idx]
                    m = _PRICE_RE.search(cell)
                    if m:
                        return m.group(1)

        # If header text is mojibake, fallback by searching for the known pattern:
        # '薬価 (' appears as garbled bytes in some environments. We'll instead
        # pick the first numeric cell in 5th/6th columns which are typically prices.
        first_row = table.select_one("tr:nth-of-type(2)")
        if first_row:
            tds = [td.get_text(" ", strip=True) for td in first_row.select("td")]
            for col in (4, 5, 3):
                if 0 <= col < len(tds):
                    m = _PRICE_RE.search(tds[col])
                    if m:
                        return m.group(1)

    # Fallback 2: search any element with class/id containing price-ish keywords
    candidates: list[str] = []
    for el in soup.select("[class*='price' i], [class*='yakka' i], [id*='price' i], [id*='yakka' i]"):
        text = " ".join(el.get_text(" ", strip=True).split())
        if text:
            candidates.append(text)

    for text in candidates:
        m = _PRICE_RE.search(text)
        if m:
            return m.group(1)

    # Fallback 3: search whole document
    whole = " ".join(soup.get_text(" ", strip=True).split())
    m = _PRICE_RE.search(whole)
    if m:
        return m.group(1)

    return None
