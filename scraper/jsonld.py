"""Generikus termékadat-kinyerés: schema.org Product JSON-LD, tartalékként OpenGraph/microdata meta. Csak stdlib."""
from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

_LD_RX = re.compile(r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.S | re.I)
_META_RX = re.compile(r"<meta\s+[^>]*?(?:property|name|itemprop)=[\"']([^\"']+)[\"'][^>]*?content=[\"']([^\"']*)[\"']", re.I)
_META_RX_REV = re.compile(r"<meta\s+[^>]*?content=[\"']([^\"']*)[\"'][^>]*?(?:property|name|itemprop)=[\"']([^\"']+)[\"']", re.I)
_CANON_RX = re.compile(r"<link[^>]+rel=[\"']canonical[\"'][^>]*href=[\"']([^\"']+)[\"']", re.I)

STOCK_MAP = {
    "instock": "in_stock", "limitedavailability": "in_stock", "onlineonly": "in_stock", "instoreonly": "in_stock",
    "outofstock": "out_of_stock", "soldout": "out_of_stock", "discontinued": "out_of_stock",
    "preorder": "preorder", "presale": "preorder", "backorder": "preorder",
    # OpenGraph product:availability értékek
    "in stock": "in_stock", "out of stock": "out_of_stock", "available for order": "preorder", "pending": "preorder",
}


@dataclass
class ScrapedOffer:
    external_id: str
    url: str
    title: str
    price: Decimal
    currency: str | None
    stock: str = "unknown"
    brand: str | None = None
    sku: str | None = None
    mpn: str | None = None
    ean: str | None = None
    image: str | None = None
    has_own_url: bool = True        # False: a JSON-LD nem adott termék-URL-t (az oldal URL-je lett)


def parse_price(v) -> Decimal | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if not s:
        return None
    if "," in s and "." in s:                      # 1.234,56 vagy 1,234.56
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:                                 # 1234,56 vagy 12,345 (ezres)
        s = s.replace(",", ".") if len(s.split(",")[-1]) <= 2 else s.replace(",", "")
    try:
        d = Decimal(s)
        return d if d > 0 else None
    except InvalidOperation:
        return None


def clean_title(t: str | None) -> str | None:
    """'CM.522 Sport Line | Taiwangun' -> 'CM.522 Sport Line' (csak '|' utáni rövid boltnév-farok)."""
    if not t:
        return t
    return re.sub(r"\s+\|\s+[^|]{2,30}$", "", re.sub(r"\s+", " ", t)).strip()


def map_stock(v) -> str:
    if not v:
        return "unknown"
    key = str(v).rstrip("/").rsplit("/", 1)[-1].strip().lower()
    return STOCK_MAP.get(key, "unknown")


def _types(node: dict) -> set[str]:
    t = node.get("@type", [])
    return {x.rsplit("/", 1)[-1] for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)}


def _walk(obj):
    if isinstance(obj, list):
        for x in obj:
            yield from _walk(x)
    elif isinstance(obj, dict):
        yield obj
        for k in ("@graph", "mainEntity", "itemListElement", "item"):
            if k in obj:
                yield from _walk(obj[k])


def _text(v) -> str | None:
    if isinstance(v, list):
        v = v[0] if v else None
    if isinstance(v, dict):
        v = v.get("name") or v.get("url") or v.get("@id")
    if v in (None, ""):
        return None
    s = str(v)
    for _ in range(3):                       # néhány bolt kétszer kódolja: „G&amp;amp;G”
        u = html.unescape(s)
        if u == s:
            break
        s = u
    return s.strip()


def _load_blocks(page: str) -> list:
    out = []
    for raw in _LD_RX.findall(page):
        raw = raw.strip().removeprefix("<!--").removesuffix("-->").strip()
        for candidate in (raw, html.unescape(raw), re.sub(r",\s*([}\]])", r"\1", raw)):
            try:
                out.append(json.loads(candidate, strict=False))
                break
            except json.JSONDecodeError:
                continue
    return out


def _offer_nodes(product: dict) -> list[dict]:
    offers = product.get("offers")
    nodes = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []
    flat = []
    for n in nodes:
        if "AggregateOffer" in _types(n) and n.get("offers"):
            sub = n["offers"]
            flat += sub if isinstance(sub, list) else [sub]
        else:
            flat.append(n)
    return [n for n in flat if isinstance(n, dict)]


def _ext_id(url: str, variant: str | None) -> str:
    p = urlsplit(url)
    return hashlib.sha1(f"{p.netloc}{p.path}#{variant or ''}".encode()).hexdigest()[:20]


def _from_product(p: dict, page_url: str, parent: dict | None = None) -> list[ScrapedOffer]:
    base = parent or {}
    title = clean_title(_text(p.get("name")) or _text(base.get("name")))
    brand = _text(p.get("brand")) or _text(base.get("brand")) or _text(p.get("manufacturer"))
    sku, mpn = _text(p.get("sku")), _text(p.get("mpn")) or _text(base.get("mpn"))
    ean = next((_text(p.get(k)) for k in ("gtin13", "gtin", "gtin12", "gtin14", "gtin8", "ean") if p.get(k)), None)
    image = _text(p.get("image")) or _text(base.get("image"))
    out = []
    for o in _offer_nodes(p):
        price = parse_price(o.get("price") or o.get("lowPrice") or (o.get("priceSpecification") or {}).get("price"))
        if not (title and price):
            continue
        own = _text(o.get("url")) or _text(p.get("url"))
        url = urljoin(page_url, own or page_url)
        variant = _text(o.get("sku")) or sku
        out.append(ScrapedOffer(
            external_id=_ext_id(url, variant), url=url, title=title, price=price,
            currency=(_text(o.get("priceCurrency")) or "").upper() or None, stock=map_stock(o.get("availability")),
            brand=brand, sku=variant, mpn=mpn, ean=ean, image=urljoin(page_url, image) if image else None,
            has_own_url=bool(own)))
    return out


def extract(page: str, page_url: str) -> list[ScrapedOffer]:
    """Egy termékoldal ajánlatai (variánsonként külön, ha a bolt variánsonként ad árat)."""
    if m := _CANON_RX.search(page):
        page_url = urljoin(page_url, html.unescape(m.group(1)))
    results: list[ScrapedOffer] = []
    for block in _load_blocks(page):
        for node in _walk(block):
            types = _types(node)
            if "ProductGroup" in types and node.get("hasVariant"):
                for v in node["hasVariant"] if isinstance(node["hasVariant"], list) else [node["hasVariant"]]:
                    results += _from_product(v, page_url, parent=node)
            elif "Product" in types:
                results += _from_product(node, page_url)
    if not results:                                   # 2. microdata (itemscope/itemprop), pl. Shoprenter, VirtueMart
        for node in microdata_items(page):
            if "Product" in _types(node):
                results += _from_product(node, page_url)
    if results:
        seen, uniq = set(), []
        for r in results:
            if r.external_id not in seen:
                seen.add(r.external_id)
                uniq.append(r)
        page_key = lambda u: urlsplit(u).netloc + urlsplit(u).path      # ugyanaz, amiből az ID készül
        per_page: dict[str, int] = {}
        for r in uniq:
            per_page[page_key(r.url)] = per_page.get(page_key(r.url), 0) + 1
        for r in uniq:                       # stabil ID: az SKU csak akkor számít, ha egy oldalon több változat van
            if per_page[page_key(r.url)] == 1:
                r.external_id = _ext_id(r.url, None)
        return uniq
    return _from_meta(page, page_url)


def _from_meta(page: str, page_url: str) -> list[ScrapedOffer]:
    meta = {k.lower(): html.unescape(v) for k, v in _META_RX.findall(page)}
    meta.update({k.lower(): html.unescape(v) for v, k in _META_RX_REV.findall(page)})
    price = parse_price(meta.get("product:price:amount") or meta.get("og:price:amount") or meta.get("price"))
    title = clean_title(meta.get("og:title") or meta.get("name"))
    if not (price and title):
        return []
    return [ScrapedOffer(
        external_id=_ext_id(page_url, None), url=page_url, title=title, price=price,
        currency=(meta.get("product:price:currency") or meta.get("og:price:currency") or meta.get("pricecurrency") or "").upper() or None,
        stock=map_stock(meta.get("product:availability") or meta.get("og:availability") or meta.get("availability")),
        brand=meta.get("product:brand"), image=meta.get("og:image"))]


# ---------------------------------------------------------------- microdata
_VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "param", "track", "wbr"}


class _Microdata(HTMLParser):
    """schema.org microdata -> JSON-LD-szerű dict-ek ({'@type': ..., prop: érték | dict | [..]})."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[dict] = []      # gyökér itemek
        self.scopes: list[dict] = []     # aktív itemscope-ok
        self.stack: list[tuple] = []     # (tag, scope_pushed, capture)

    def _add(self, prop: str, value) -> None:
        if self.scopes and value not in (None, ""):
            for name in prop.split():
                self.scopes[-1].setdefault(name, []).append(value)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        prop, pushed, capture = a.get("itemprop"), False, None
        if "itemscope" in a:
            itype = (a.get("itemtype") or "").split()
            item = {"@type": itype[0].rsplit("/", 1)[-1] if itype else ""}
            if prop and self.scopes:
                self._add(prop, item)
            elif not prop:
                self.items.append(item)
            self.scopes.append(item)
            pushed = True
        elif prop:
            val = a.get("content")
            if val is None:
                val = a.get("href") if tag in ("a", "link") else a.get("src") if tag in ("img", "source") else None
            if val is not None or tag in _VOID:
                self._add(prop, val)
            else:
                capture = [prop, self.scopes[-1] if self.scopes else None, []]
        if tag not in _VOID:
            self.stack.append((tag, pushed, capture))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        for _, _, cap in self.stack:
            if cap:
                cap[2].append(data)

    def handle_endtag(self, tag):
        if not any(t == tag for t, _, _ in self.stack):
            return
        while self.stack:
            t, pushed, cap = self.stack.pop()
            if cap and cap[1] is not None:
                text = re.sub(r"\s+", " ", "".join(cap[2])).strip()
                if text:
                    for name in cap[0].split():
                        cap[1].setdefault(name, []).append(text)
            if pushed and self.scopes:
                self.scopes.pop()
            if t == tag:
                break


def _flatten(item: dict) -> dict:
    """Listás értékek -> első érték (offers kivétel: lista marad), beágyazott itemek rekurzívan."""
    out = {"@type": item.get("@type") or ""}
    for k, vals in item.items():
        if k == "@type":
            continue
        vals = [_flatten(v) if isinstance(v, dict) else v for v in vals]
        out[k] = vals if k == "offers" else vals[0]
    return out


def microdata_items(page: str) -> list[dict]:
    p = _Microdata()
    try:
        p.feed(page)
        p.close()
    except Exception:
        pass
    return [_flatten(i) for i in p.items]
