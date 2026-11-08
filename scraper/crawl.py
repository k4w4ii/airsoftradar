"""Termék URL-ek felderítése: sitemap.xml (preferált) vagy kategória-lapozás."""
from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from fetcher import Fetcher

_LOC_RX = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.I | re.S)
_HREF_RX = re.compile(r"href=[\"']([^\"'#]+)[\"']", re.I)


def locs(body: str) -> list[str]:
    """<loc> értékek; kezeli a <![CDATA[...]]> csomagolást (pl. PrestaShop)."""
    out = []
    for x in _LOC_RX.findall(body):
        x = html.unescape(x.strip())
        if x.startswith("<![CDATA["):
            x = x[9:].removesuffix("]]>").strip()
        out.append(x)
    return out


def _clean(u: str) -> str:
    p = urlsplit(u)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))   # query/fragment le: duplikátumok ellen


def from_sitemap(f: Fetcher, url: str, pattern: str, limit: int = 60000, _depth: int = 0,
                 diag: dict | None = None) -> list[str]:
    """diag (opcionális): {'locs': összes látott URL, 'minta': pár nem illeszkedő URL} – hibakereséshez."""
    rx, out = re.compile(pattern), []
    diag = diag if diag is not None else {}
    body = f.get(url) or ""
    for loc in locs(body):
        if len(out) >= limit:
            break
        if "<sitemapindex" in body and _depth < 2:
            out += from_sitemap(f, loc, pattern, limit - len(out), _depth + 1, diag)
        else:
            diag["locs"] = diag.get("locs", 0) + 1
            if rx.search(loc):
                out.append(_clean(loc))
            else:
                m = diag.setdefault("minta", [])
                productish = bool(re.search(r"\d.*\.html$|-detail$|/termek/|/product", loc))
                if productish and not diag.get("_pp"):     # első termékszerű URL-ek kiszorítják a menüpontokat
                    m.clear()
                    diag["_pp"] = True
                if len(m) < 3 and (productish or not diag.get("_pp")):
                    m.append(loc)
    return list(dict.fromkeys(out))[:limit]


def links_in(page: str, base: str, rx: re.Pattern) -> list[str]:
    host = urlsplit(base).netloc
    out = []
    for href in _HREF_RX.findall(page):
        u = _clean(urljoin(base, html.unescape(href)))
        if urlsplit(u).netloc == host and rx.search(u):
            out.append(u)
    return list(dict.fromkeys(out))


def from_listing(f: Fetcher, start_urls: list[str], pattern: str, page_tpl: str | None = None,
                 max_pages: int = 50, extract_fn=None, diag: dict | None = None,
                 page_size: int = 24) -> tuple[list[str], list]:
    """page_tpl pl. '{url}?page={n}'. Változók: {n} 1-től, {n0} 0-tól, {off} = (n-1)*page_size, {off1} = off+1
    (VirtueMart: '{url}/results,{off1}-{off}').
    Ha extract_fn a kategóriaoldalból >=2 ajánlatot ad (pl. Gunfire JSON-LD lista), azokat közvetlenül
    visszaadja -> nem kell minden termékoldalt letölteni. Leáll, ha egy oldal semmi újat nem hoz."""
    rx, links, offers = re.compile(pattern), {}, {}
    for start in start_urls:
        for n in range(1, (max_pages if page_tpl else 1) + 1):
            url = start if n == 1 or not page_tpl else page_tpl.format(url=start, n=n, n0=n - 1,
                                                                     off=(n - 1) * page_size, off1=(n - 1) * page_size + 1)
            page = f.get(url)
            if not page:
                break
            if diag is not None and n == 1 and "minta" not in diag:
                same_host = links_in(page, url, re.compile("."))
                diag["linkek"] = len(same_host)
                diag["minta"] = [u for u in same_host if not rx.search(u)][:3]
            found = [o for o in (extract_fn(page, url) if extract_fn else []) if o.has_own_url]
            if len(found) >= 2:
                new = [o for o in found if o.external_id not in offers]
                offers.update((o.external_id, o) for o in new)
            else:
                new = [u for u in links_in(page, url, rx) if u not in links]
                links.update(dict.fromkeys(new))
            if not new:
                break
    return list(links), list(offers.values())
