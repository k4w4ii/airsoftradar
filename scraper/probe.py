"""
Bolt-felderítő: megmutatja, mit lát a scraper egy oldalon (robots, JSON-LD termékadat, linkminták, sitemap).

  python scraper/probe.py --file scraper/pelda_urls.txt
  python scraper/probe.py https://shop.hu/sitemap.xml
  python scraper/probe.py --dump debug https://shop.hu/termek/x   # nyers HTML + JSON-LD blokkok mentése
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from crawl import _LOC_RX, links_in
from fetcher import Fetcher
from jsonld import _load_blocks, extract


def _shape(path: str) -> str:
    return re.sub(r"\d+", r"\\d+", re.sub(r"[a-z0-9]+(?:-[a-z0-9]+){2,}", "<slug>", path.lower()))


def shapes(urls: list[str], top: int = 8) -> list[tuple[str, int, str]]:
    """URL-ek 'alakja' (számok -> \\d+, hosszú slugok -> <slug>), gyakoriság szerint – product_pattern-hez."""
    cnt, sample = Counter(), {}
    for u in urls:
        s = _shape(urlsplit(u).path)
        cnt[s] += 1
        sample.setdefault(s, u)
    return [(s, n, sample[s]) for s, n in cnt.most_common(top)]


def dump(directory: str, url: str, page: str) -> None:
    d = Path(directory)
    d.mkdir(exist_ok=True)
    name = re.sub(r"[^a-z0-9]+", "_", urlsplit(url).netloc + urlsplit(url).path.lower())[:80]
    (d / f"{name}.html").write_text(page, encoding="utf-8")
    (d / f"{name}.jsonld.json").write_text(json.dumps(_load_blocks(page), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  mentve: {d / name}.html (+ .jsonld.json)")


def probe(f: Fetcher, url: str, dump_dir: str | None = None) -> None:
    if urlsplit(url).path in ("", "/"):
        maps = f.sitemaps(url)
        print(f"\n=== {url}\n  robots.txt sitemapek: {maps}")
        for m in maps[:5]:
            probe(f, m)
        return
    print(f"\n=== {url}")
    if not f.allowed(url):
        print("  robots.txt TILTJA")
        return
    page = f.get(url)
    if not page:
        print("  nem tölthető le (blokk / 404 / JS-only?) -> Playwright adapter kellhet")
        return
    if dump_dir:
        dump(dump_dir, url, page)
    if "<urlset" in page or "<sitemapindex" in page:
        locs = _LOC_RX.findall(page)
        print(f"  {'sitemap INDEX' if '<sitemapindex' in page else 'sitemap'}: {len(locs)} URL")
        for s, n, sample in shapes(locs):
            print(f"    {n:5d}x  {s:55s} pl. {sample}")
        if "<sitemapindex" in page:          # al-sitemapek közül a termékesnek tűnőket is megnézzük
            for sub in [l for l in locs if re.search(r"product|termek|produkt|item", l, re.I)][:3] or locs[:2]:
                probe(f, sub)
        return
    offers = extract(page, url)
    if offers:
        for o in offers[:3]:
            print(f"  TERMÉK  {o.title[:60]!r}\n          ár={o.price} {o.currency}  készlet={o.stock}  "
                  f"brand={o.brand}  sku={o.sku}  mpn={o.mpn}  ean={o.ean}\n          url={o.url} "
                  f"{'' if o.has_own_url else '(NINCS saját URL!)'}")
        if len(offers) > 3:
            print(f"  ... +{len(offers) - 3} további")
    else:
        print("  nincs termékadat (kategóriaoldal, vagy nincs JSON-LD) – linkminták:")
        for s, n, sample in shapes(links_in(page, url, re.compile("."))):
            print(f"    {n:4d}x  {s:55s} pl. {sample}")


if __name__ == "__main__":
    args, dump_dir = sys.argv[1:], None
    if args[:1] == ["--dump"]:
        dump_dir, args = args[1], args[2:]
    if args[:1] == ["--file"]:
        urls = [l.strip() for l in open(args[1], encoding="utf-8") if l.strip().startswith("http")]
    else:
        urls = args
    f = Fetcher(delay=1.0)
    for u in urls:
        try:
            probe(f, u, dump_dir)
        except Exception as e:
            print(f"\n=== {u}\n  HIBA: {e!r}")
