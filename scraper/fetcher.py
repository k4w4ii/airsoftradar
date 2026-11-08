"""Udvarias HTTP letöltő: robots.txt, hostonkénti késleltetés, újrapróbálás, gzip. Csak stdlib."""
from __future__ import annotations

import gzip
import random
import time
import urllib.error
import urllib.request
import urllib.robotparser
import zlib
from urllib.parse import urlsplit

USER_AGENT = "AirsoftPriceBot/0.1 (+https://example.com/bot)"  # TODO: saját domain + bot info oldal


class Fetcher:
    def __init__(self, delay: float = 2.0, retries: int = 3, timeout: int = 30, user_agent: str = USER_AGENT,
                 extra_headers: dict | None = None):
        self.delay, self.retries, self.timeout, self.ua = delay, retries, timeout, user_agent
        self.extra = extra_headers or {}   # pl. {"Cookie": "currency=EUR"} boltonként a shops.json-ból
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        p = urlsplit(url)
        host = f"{p.scheme}://{p.netloc}"
        if host not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                status, text = self._raw(f"{host}/robots.txt")
                rp.parse(text.splitlines() if status == 200 else [])
            except Exception:
                rp.parse([])
            self._robots[host] = rp
            if (cd := rp.crawl_delay(self.ua)) and cd > self.delay:
                self.delay = float(cd)
        return self._robots[host].can_fetch(self.ua, url)

    def sitemaps(self, base_url: str) -> list[str]:
        """A robots.txt 'Sitemap:' sorai; ha nincs, a szokásos /sitemap.xml."""
        self.allowed(base_url)
        p = urlsplit(base_url)
        rp = self._robots.get(f"{p.scheme}://{p.netloc}")
        return list((rp and rp.site_maps()) or [f"{p.scheme}://{p.netloc}/sitemap.xml"])

    def get(self, url: str) -> str | None:
        """HTML szöveg, vagy None (robots tiltás / 404 / tartós hiba)."""
        if not self.allowed(url):
            return None
        for attempt in range(self.retries):
            self._throttle(url)
            try:
                status, text = self._raw(url)
                return text if status == 200 else None
            except urllib.error.HTTPError as e:
                if e.code in (404, 410):
                    return None
                if e.code not in (429, 500, 502, 503, 504):
                    raise
            except (urllib.error.URLError, TimeoutError):
                pass
            if attempt < self.retries - 1:
                time.sleep((2 ** attempt) * 5 + random.random() * 2)
        return None

    def _throttle(self, url: str) -> None:
        host = urlsplit(url).netloc
        wait = self._last.get(host, 0) + self.delay * random.uniform(1.0, 1.5) - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def _raw(self, url: str) -> tuple[int, str]:
        req = urllib.request.Request(url, headers={
            "User-Agent": self.ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,hu;q=0.8", "Accept-Encoding": "gzip, deflate", **self.extra})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            body = r.read()
            enc = r.headers.get("Content-Encoding", "")
            if enc == "gzip" or body[:2] == b"\x1f\x8b":      # .xml.gz sitemapek is
                body = gzip.decompress(body)
            elif enc == "deflate":
                body = zlib.decompress(body)
            charset = r.headers.get_content_charset() or "utf-8"
            return r.status, body.decode(charset, errors="replace")
