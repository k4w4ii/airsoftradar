"""Futtatás: cd scraper && python -m unittest -v"""
import re
import unittest
from decimal import Decimal
from unittest import mock

import crawl
import mnb_rates
import run_shop
from jsonld import ScrapedOffer, extract, map_stock, parse_price

WOO = """<html><head><link rel="canonical" href="https://airsoftplaza.hu/termek/ares-g36-ecu/">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"WebPage","name":"x"},
{"@type":"Product","name":"ARES G36 ECU fekete AR-078E","sku":"AR-078E","brand":{"@type":"Brand","name":"ARES"},
"image":["https://airsoftplaza.hu/img/g36.jpg"],
"offers":[{"@type":"Offer","price":"129990","priceCurrency":"HUF","availability":"http://schema.org/InStock"}]}]}
</script></head></html>"""

PRESTA_VARIANTS = """<script type="application/ld+json">
{"@context":"https://schema.org/","@type":"ProductGroup","name":"Specna Arms SA-E01 EDGE","brand":"Specna Arms",
 "hasVariant":[
  {"@type":"Product","sku":"SPE-01-018886","gtin13":"5901780000011","name":"Specna Arms SA-E01 EDGE Black",
   "offers":{"@type":"Offer","price":219.9,"priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/p/sa-e01?c=black"}},
  {"@type":"Product","sku":"SPE-01-018887","name":"Specna Arms SA-E01 EDGE Tan",
   "offers":{"@type":"Offer","price":"219,90","priceCurrency":"EUR","availability":"https://schema.org/PreOrder","url":"/p/sa-e01?c=tan"}}
 ]}</script>"""

AGGREGATE = """<script type='application/ld+json'>
{"@type":"Product","name":"CYMA CM.522","offers":{"@type":"AggregateOffer","lowPrice":"899.00","priceCurrency":"PLN",
"offers":[{"@type":"Offer","price":"899.00","priceCurrency":"PLN","availability":"OutOfStock"}]},}
</script>"""

OG_ONLY = """<meta property="og:title" content="Double Bell RK-10 AKMS" />
<meta property="product:price:amount" content="54 990" /><meta property="product:price:currency" content="HUF"/>
<meta property="product:availability" content="in stock"/>"""

MNB_SOAP = """<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>
<GetCurrentExchangeRatesResponse xmlns="http://www.mnb.hu/webservices/"><GetCurrentExchangeRatesResult>
&lt;MNBCurrentExchangeRates&gt;&lt;Day date="2026-11-06"&gt;&lt;Rate unit="1" curr="EUR"&gt;385,40&lt;/Rate&gt;
&lt;Rate unit="1" curr="PLN"&gt;90,1200&lt;/Rate&gt;&lt;Rate unit="100" curr="JPY"&gt;230,50&lt;/Rate&gt;&lt;/Day&gt;&lt;/MNBCurrentExchangeRates&gt;
</GetCurrentExchangeRatesResult></GetCurrentExchangeRatesResponse></s:Body></s:Envelope>"""


class TestJsonLd(unittest.TestCase):
    def test_woocommerce_graph(self):
        [o] = extract(WOO, "https://airsoftplaza.hu/termek/ares-g36-ecu/?ref=x")
        self.assertEqual((o.price, o.currency, o.stock, o.brand, o.sku), (Decimal("129990"), "HUF", "in_stock", "ARES", "AR-078E"))
        self.assertEqual(o.url, "https://airsoftplaza.hu/termek/ares-g36-ecu/")

    def test_product_group_variants(self):
        offers = extract(PRESTA_VARIANTS, "https://shop.eu/p/sa-e01")
        self.assertEqual(len(offers), 2)
        self.assertEqual([o.stock for o in offers], ["in_stock", "preorder"])
        self.assertEqual(offers[1].price, Decimal("219.90"))
        self.assertEqual(offers[0].brand, "Specna Arms")
        self.assertNotEqual(offers[0].external_id, offers[1].external_id)

    def test_aggregate_offer_and_trailing_comma(self):
        [o] = extract(AGGREGATE, "https://gunfire.com/x")
        self.assertEqual((o.price, o.currency, o.stock), (Decimal("899.00"), "PLN", "out_of_stock"))

    def test_opengraph_fallback(self):
        [o] = extract(OG_ONLY, "https://www.airsoftcentrum.hu/double-bell-rk-10-akms-ak47-7084")
        self.assertEqual((o.title, o.price, o.currency, o.stock), ("Double Bell RK-10 AKMS", Decimal("54990"), "HUF", "in_stock"))

    def test_clean_title(self):
        html = '<meta property="og:title" content="CM.522 Sport Line, GEN-2 [CYMA] | Taiwangun"><meta property="product:price:amount" content="68.73">'
        [o] = extract(html, "https://www.taiwangun.com/x")
        self.assertEqual(o.title, "CM.522 Sport Line, GEN-2 [CYMA]")

    def test_microdata_shoprenter(self):
        page = """<ol itemscope itemtype="https://schema.org/BreadcrumbList"><li itemprop="itemListElement" itemscope
        itemtype="https://schema.org/ListItem"><span itemprop="name">Kezdőlap</span></li></ol>
        <div itemscope itemtype="//schema.org/Product"><h1><span itemprop="name">Double Bell RK-10 AKMS AK47 Fém</span></h1>
        <span class="x" itemprop="brand">Double Bell</span><img itemprop="image" src="/img/rk10.jpg">
        <div itemprop="offers" itemscope itemtype="https://schema.org/Offer"><span>89.990 Ft</span>
        <meta itemprop="price" content="89990"/><meta itemprop="priceCurrency" content="HUF"/><meta itemprop="sku" content="00016582"/>
        <link itemprop="availability" href="http://schema.org/InStock"/></div></div>"""
        [o] = extract(page, "https://www.airsoftcentrum.hu/double-bell-rk-10-akms-ak47-7084")
        self.assertEqual((o.title, o.brand, o.price, o.currency, o.stock), ("Double Bell RK-10 AKMS AK47 Fém", "Double Bell", Decimal("89990"), "HUF", "in_stock"))
        self.assertEqual(o.image, "https://www.airsoftcentrum.hu/img/rk10.jpg")

    def test_microdata_nested_brand_not_title(self):
        page = """<div itemscope itemtype="https://schema.org/Product"><meta itemprop="name" content="Airsoftová zbraň AK47 Arsenal SLR105" />
        <span class="hidden" itemprop="brand" itemscope itemtype="https://schema.org/Thing"><meta itemprop="name" content="ASG" /></span>
        <meta itemprop="sku" content="7416" /><span itemprop="offers" itemscope itemtype="https://schema.org/Offer">
        <meta itemprop="price" content="1699" /><meta itemprop="priceCurrency" content="CZK" />
        <link itemprop="availability" href="https://schema.org/OutOfStock" /></span></div>"""
        [o] = extract(page, "https://airsoftpro.cz/x-detail")
        self.assertEqual((o.title, o.brand, o.stock), ("Airsoftová zbraň AK47 Arsenal SLR105", "ASG", "out_of_stock"))

    def test_no_data(self):
        self.assertEqual(extract("<html>kategória</html>", "https://x.hu"), [])

    def test_parse_price(self):
        cases = {"1.234,56": "1234.56", "1,234.56": "1234.56", "129 990 Ft": "129990", "219,90 €": "219.90",
                 "12,345": "12345", 99.5: "99.5", "0": None, "": None}
        for raw, exp in cases.items():
            self.assertEqual(parse_price(raw), Decimal(exp) if exp else None, raw)

    def test_stock_map(self):
        self.assertEqual(map_stock("https://schema.org/BackOrder"), "preorder")
        self.assertEqual(map_stock("valami"), "unknown")


class TestMnb(unittest.TestCase):
    def test_parse(self):
        rows = {r["currency"]: r for r in mnb_rates.parse(MNB_SOAP)}
        self.assertEqual(rows["EUR"]["huf_per_unit"], "385.4000")
        self.assertEqual(rows["JPY"]["huf_per_unit"], "2.3050")
        self.assertEqual(rows["PLN"]["rate_date"], "2026-11-06")


class FakeFetcher:
    def __init__(self, pages): self.pages, self.stats = pages, {}
    def get(self, url): return self.pages.get(url)


class TestCrawl(unittest.TestCase):
    def test_sitemap_index(self):
        f = FakeFetcher({
            "https://s.hu/sitemap.xml": "<sitemapindex><sitemap><loc>https://s.hu/p1.xml</loc></sitemap></sitemapindex>",
            "https://s.hu/p1.xml": "<urlset><url><loc>https://s.hu/termek/a/</loc></url><url><loc>https://s.hu/blog/b</loc></url></urlset>"})
        self.assertEqual(crawl.from_sitemap(f, "https://s.hu/sitemap.xml", r"/termek/"), ["https://s.hu/termek/a/"])

    def test_listing_pagination_stops(self):
        f = FakeFetcher({
            "https://s.eu/aeg": '<a href="/aeg/cm-522">x</a><a href="/aeg/cm-523?ref=1">y</a><a href="https://other.com/aeg/z">z</a>',
            "https://s.eu/aeg?page=2": '<a href="/aeg/sa-e01">x</a>',
            "https://s.eu/aeg?page=3": '<a href="/aeg/sa-e01">ugyanaz</a>'})
        urls, offers = crawl.from_listing(f, ["https://s.eu/aeg"], r"/aeg/[a-z0-9-]+$", "{url}?page={n}", extract_fn=extract)
        self.assertEqual(offers, [])
        self.assertEqual(urls, ["https://s.eu/aeg/cm-522", "https://s.eu/aeg/cm-523", "https://s.eu/aeg/sa-e01"])


    def test_listing_page_offers_gunfire_style(self):
        def page(names):
            items = ",".join('{"@type":"Product","name":"%s","sku":"%s","brand":{"name":"JG"},'
                             '"offers":{"@type":"Offer","price":"140.88","priceCurrency":"EUR","url":"/en/product-%s.html",'
                             '"availability":"https://schema.org/InStock"}}' % (n, n, n) for n in names)
            return '<script type="application/ld+json">{"@type":"ItemList","itemListElement":[%s]}</script>' % items
        f = FakeFetcher({"https://g.com/menu/aeg.html": page(["a1", "a2"]),
                         "https://g.com/menu/aeg.html?counter=1": page(["a3", "a4"]),
                         "https://g.com/menu/aeg.html?counter=2": page(["a3", "a4"])})
        urls, offers = crawl.from_listing(f, ["https://g.com/menu/aeg.html"], "/en/product", "{url}?counter={n0}", extract_fn=extract)
        self.assertEqual(urls, [])
        self.assertEqual([o.url for o in offers], [f"https://g.com/en/product-a{i}.html" for i in range(1, 5)])

    def test_listing_offers_without_own_url_ignored(self):
        html = '<script type="application/ld+json">[{"@type":"Product","name":"x","offers":{"price":"1","priceCurrency":"EUR"}},' \
               '{"@type":"Product","name":"y","sku":"2","offers":{"price":"2","priceCurrency":"EUR"}}]</script><a href="/aeg/x">x</a>'
        urls, offers = crawl.from_listing(FakeFetcher({"https://s.eu/aeg": html}), ["https://s.eu/aeg"], r"/aeg/x", extract_fn=extract)
        self.assertEqual((urls, offers), (["https://s.eu/aeg/x"], []))


# ---------------- pipeline teszt memóriabeli DB-vel ----------------
class FakeDB:
    DEFAULTS = {"offers": {"match_status": "pending", "product_id": None}, "products": {"name_lang": "en"}}

    def __init__(self):
        self.t = {k: [] for k in ["shops", "manufacturers", "manufacturer_aliases", "products", "product_codes",
                                  "offers", "price_history", "scrape_runs", "match_candidates"]}
        self.t["latest_rates"] = [{"currency": "EUR", "huf_per_unit": 385.4}, {"currency": "PLN", "huf_per_unit": 90.12}]
        self.seq = 0

    def _match(self, row, filters):
        for k, v in filters.items():
            if k == "select":
                continue
            op, val = v.split(".", 1)
            if op == "eq" and str(row.get(k)) != val or op == "lt" and not str(row.get(k)) < val:
                return False
            if op == "in" and str(row.get(k)) not in val.strip("()").split(","):     # PostgREST: id=in.(1,2,3)
                return False
        return True

    def select(self, table, **f): return [dict(r) for r in self.t[table] if self._match(r, f)]

    def insert(self, table, rows):
        out = []
        for r in rows:
            if table == "products" and any(p["manufacturer_id"] == r["manufacturer_id"] and p["model_code_norm"] == r["model_code_norm"] for p in self.t[table]):
                raise RuntimeError("409: 23505 duplicate")
            self.seq += 1
            row = {"id": self.seq, **self.DEFAULTS.get(table, {}), **r}
            self.t[table].append(row)
            out.append(dict(row))
        return out

    def upsert(self, table, rows, on_conflict, returning=True):
        keys, out = on_conflict.split(","), []
        for r in rows:
            ex = next((x for x in self.t[table] if all(str(x.get(k)) == str(r[k]) for k in keys)), None)
            if ex:
                ex.update(r)
                out.append(dict(ex))
            else:
                out += self.insert(table, [r])
        return out

    def update(self, table, values, **f):
        for r in self.t[table]:
            if self._match(r, f):
                r.update(values)

    def rpc(self, fn, args=None): pass


def _seed(db):
    db.t["shops"] = [{"id": 1, "slug": "taiwangun", "currency": "EUR", "lang": "en"},
                     {"id": 2, "slug": "airsoftplaza", "currency": "HUF", "lang": "hu"}]
    db.t["manufacturers"] = [{"id": 1, "slug": "cyma", "name": "CYMA"}]
    db.t["manufacturer_aliases"] = [{"alias_norm": "cyma", "manufacturer_id": 1}]


def _offer(title, price, ext):
    return ScrapedOffer(external_id=ext, url=f"https://x/{ext}", title=title, price=Decimal(price), currency=None, stock="in_stock")


class TestPipeline(unittest.TestCase):
    def test_two_shops_merge_into_one_product(self):
        db = FakeDB()
        _seed(db)
        with mock.patch("db.get_db", return_value=db):
            with mock.patch.object(run_shop, "scrape", return_value=([_offer("CYMA CM.522 AK fekete", "79990", "a1")], [], 3)):
                run_shop.run("airsoftplaza", None, False)
            with mock.patch.object(run_shop, "scrape", return_value=([_offer("CM.522 Sport Line Gen 2 (CYMA)", "189.90", "b1"),
                                                                      _offer("Unknown brand rifle", "50", "b2")], [], 3)):
                run_shop.run("taiwangun", None, False)

        self.assertEqual(len(db.t["products"]), 1)
        p = db.t["products"][0]
        self.assertEqual((p["model_code_norm"], p["name_lang"]), ("CM522", "en"))      # angol név felülírta
        self.assertEqual(p["name"], "CYMA CM.522 Sport Line Gen 2")    # egységes név, angol boltból
        matched = [o for o in db.t["offers"] if o["product_id"] == p["id"]]
        self.assertEqual({o["match_method"] for o in matched}, {"new", "code"})
        self.assertEqual(next(o for o in db.t["offers"] if o["external_id"] == "b2")["match_status"], "pending")
        h = {x["offer_id"]: x for x in db.t["price_history"]}
        eur_offer = next(o for o in db.t["offers"] if o["external_id"] == "b1")
        self.assertEqual(h[eur_offer["id"]]["price_huf"], "73187")
        self.assertEqual(h[eur_offer["id"]]["price_eur"], "189.90")
        self.assertTrue(all(r["status"] == "ok" for r in db.t["scrape_runs"]))
        self.assertEqual({c["code_norm"] for c in db.t["product_codes"]}, {"CM522"})


class TestFixUrl(unittest.TestCase):
    def test_double_scheme(self):
        from jsonld import extract, fix_url
        self.assertEqual(fix_url("https://gunfire.comhttps//gunfire.com/en/products/x-1.html"), "https://gunfire.com/en/products/x-1.html")
        self.assertEqual(fix_url("https://shop.cz/p?u=https://x"), "https://shop.cz/p?u=https://x")
        page = ('<script type="application/ld+json">{"@type":"Product","name":"AM-009 Carbine","offers":{"@type":"Offer",'
                '"price":"227.5","priceCurrency":"EUR","url":"https://gunfire.comhttps//gunfire.com/en/products/am-009-1.html"}}</script>')
        o = extract(page, "https://gunfire.com/en/menu/rifles.html")[0]
        self.assertEqual(o.url, "https://gunfire.com/en/products/am-009-1.html")


if __name__ == "__main__":
    unittest.main()


class TestRobotsSitemaps(unittest.TestCase):
    def test_sitemaps_from_robots(self):
        from fetcher import Fetcher
        f = Fetcher()
        with mock.patch.object(f, "_raw", return_value=(200, "User-agent: *\nDisallow: /cart\nSitemap: https://s.fr/1_en_0_sitemap.xml\n")):
            self.assertEqual(f.sitemaps("https://s.fr"), ["https://s.fr/1_en_0_sitemap.xml"])
            self.assertFalse(f.allowed("https://s.fr/cart"))

    def test_sitemaps_fallback(self):
        from fetcher import Fetcher
        f = Fetcher()
        with mock.patch.object(f, "_raw", return_value=(404, "")):
            self.assertEqual(f.sitemaps("https://s.hu/"), ["https://s.hu/sitemap.xml"])


class TestBudget(unittest.TestCase):
    def test_partial_run_does_not_deactivate(self):
        db = FakeDB()
        _seed(db)
        db.t["offers"].append({"id": 999, "shop_id": 1, "external_id": "old", "last_seen_at": "2000-01-01", "is_active": True,
                               "match_status": "auto", "product_id": None})
        with mock.patch("db.get_db", return_value=db):
            with mock.patch.object(run_shop, "scrape", return_value=([_offer("CYMA CM.522", "189.90", "n1")], [{"error": "időkorlát"}], None)):
                run_shop.run("taiwangun", None, False)
        self.assertTrue(next(o for o in db.t["offers"] if o["id"] == 999)["is_active"])
        self.assertEqual(db.t["scrape_runs"][-1]["status"], "partial")
        with mock.patch("db.get_db", return_value=db):
            with mock.patch.object(run_shop, "scrape", return_value=([_offer("CYMA CM.522", "189.90", "n1")], [], 3)):
                run_shop.run("taiwangun", None, False)
        self.assertFalse(next(o for o in db.t["offers"] if o["id"] == 999)["is_active"])

    def test_scrape_respects_budget(self):
        pages = {f"https://www.taiwangun.com/assault-rifle-aeg/p{i}": WOO for i in range(5)}
        listing = "".join(f'<a href="/assault-rifle-aeg/p{i}">x</a>' for i in range(5))
        pages["https://www.taiwangun.com/assault-rifle-aeg"] = listing
        fake = FakeFetcher(pages)
        cfg = {"source": "listing", "start_urls": ["https://www.taiwangun.com/assault-rifle-aeg"],
               "product_pattern": "^https://www\\.taiwangun\\.com/assault-rifle-aeg/[a-z0-9-]+$"}
        with mock.patch.object(run_shop, "Fetcher", return_value=fake), mock.patch.dict("os.environ", {"SCRAPE_BUDGET_MIN": "0"}), \
                mock.patch.dict(run_shop.CONFIG, {"taiwangun": cfg}):
            out, errors, stale = run_shop.scrape("taiwangun", None)
        self.assertIsNone(stale)
        self.assertIn("időkorlát", errors[-1]["error"])


class TestDiagnostics(unittest.TestCase):
    def test_403_everywhere_is_recorded(self):
        import urllib.error
        from fetcher import Fetcher
        f = Fetcher(retries=1, delay=0)
        def boom(url):
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        with mock.patch.object(f, "_raw", side_effect=boom), mock.patch.object(run_shop, "Fetcher", return_value=f):
            out, errors, stale = run_shop.scrape("powair6", None)
        self.assertEqual(out, [])
        self.assertIn("0 termék", errors[0]["error"])
        self.assertGreaterEqual(errors[0]["http"]["403"], 1)

    def test_wrong_pattern_shows_sample(self):
        f = FakeFetcher({"https://s.hu/sitemap.xml": "<urlset><url><loc>https://s.hu/p/abc-123</loc></url></urlset>"})
        diag = {}
        self.assertEqual(crawl.from_sitemap(f, "https://s.hu/sitemap.xml", r"/termek/", diag=diag), [])
        self.assertEqual(diag, {"locs": 1, "minta": ["https://s.hu/p/abc-123"]})


class TestRound3(unittest.TestCase):
    def test_cdata_sitemap_and_fr_to_en_rewrite(self):
        sm = ("<urlset><url><loc><![CDATA[https://www.powair6.com/fr/]]></loc></url>"
              "<url><loc><![CDATA[https://www.powair6.com/fr/aeg-assaut/96396-tokyo-marui-evolt.html]]></loc></url>"
              "<url><loc><![CDATA[https://www.powair6.com/fr/textile/1234-tshirt.html]]></loc></url></urlset>")
        en = "https://www.powair6.com/en/aeg-assaut/96396-tokyo-marui-evolt.html"
        fake = FakeFetcher({"https://www.powair6.com/1_index_sitemap.xml": sm, en: WOO})
        fake.sitemaps = lambda base: ["https://www.powair6.com/1_index_sitemap.xml"]
        with mock.patch.object(run_shop, "Fetcher", return_value=fake):
            out, errors, stale = run_shop.scrape("powair6", None)
        self.assertEqual(len(out), 1)              # csak a fegyverkategória, angol URL-en letöltve
        self.assertEqual(errors, [])

    def test_diag_prefers_product_like_urls(self):
        f = FakeFetcher({"https://s.fr/sm.xml": "<urlset>" + "".join(f"<url><loc>{u}</loc></url>" for u in
                         ["https://s.fr/fr/", "https://s.fr/fr/contact", "https://s.fr/fr/x/12-a.html"]) + "</urlset>"})
        diag = {}
        crawl.from_sitemap(f, "https://s.fr/sm.xml", r"/en/", diag=diag)
        self.assertEqual(diag["minta"], ["https://s.fr/fr/x/12-a.html"])

    def test_virtuemart_paging(self):
        def page(ids):
            return "".join(f'<a href="/cz/airsoftove-zbrane/airsoftove-zbrane-dlouhe/p{i}-detail">x</a>' for i in ids)
        base = "https://airsoftpro.cz/cz/airsoftove-zbrane/airsoftove-zbrane-dlouhe"
        f = FakeFetcher({base: page([1, 2]), base + "/results,25-24": page([3]), base + "/results,49-48": page([3])})
        cfg = run_shop.CONFIG["airsoftpro"]
        urls, _ = crawl.from_listing(f, [base], cfg["product_pattern"], cfg["page_tpl"], page_size=cfg["page_size"], extract_fn=extract)
        self.assertEqual([u.rsplit("/", 1)[1] for u in urls], ["p1-detail", "p2-detail", "p3-detail"])

    def test_evike_pattern(self):
        rx = re.compile(run_shop.CONFIG["evike-europe"]["product_pattern"])
        ok = ["https://evike-europe.com/11406.html", "https://evike-europe.com/we-gx01-bk.html", "https://evike-europe.com/27631-az.html"]
        bad = ["https://evike-europe.com/epic-deals.html", "https://evike-europe.com/airsoft-guns/assault-rifles/aeg-assault-rifles.html"]
        self.assertTrue(all(rx.search(u) for u in ok))
        self.assertFalse(any(rx.search(u) for u in bad))

    def test_airsoftcentrum_pattern(self):
        rx = re.compile(run_shop.CONFIG["airsoftcentrum"]["product_pattern"])
        self.assertTrue(rx.search("https://www.airsoftcentrum.hu/double-bell-rk-10-akms-ak47-7084"))
        self.assertFalse(rx.search("https://www.airsoftcentrum.hu/double-bell-m-151"))
        self.assertFalse(rx.search("https://www.airsoftcentrum.hu/adatvedelmi_nyilatkozat_3"))

    def test_rotating_window(self):
        urls = [f"https://www.airsoftcentrum.hu/p-{i:04d}" for i in range(10)]
        pages = {u: WOO for u in urls}
        sm = "<urlset>" + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"
        fake = FakeFetcher({"https://www.airsoftcentrum.hu/sitemap.xml": sm, **pages})
        fake.sitemaps = lambda base: ["https://www.airsoftcentrum.hu/sitemap.xml"]
        cfg = {**run_shop.CONFIG["airsoftcentrum"], "max_products": 4}
        with mock.patch.dict(run_shop.CONFIG, {"airsoftcentrum": cfg}), mock.patch.object(run_shop, "Fetcher", return_value=fake):
            out, errors, stale = run_shop.scrape("airsoftcentrum", None)
        self.assertEqual(stale, run_shop.STALE_DAYS + 3)   # 10 termék / 4 = 3 napos ciklus


class TestTitleProductPipeline(unittest.TestCase):
    def test_codeless_offers_from_two_shops_merge(self):
        db = FakeDB()
        _seed(db)
        with mock.patch("db.get_db", return_value=db):
            with mock.patch.object(run_shop, "scrape", return_value=([_offer("CYMA Platinum AKS-74U replica", "60000", "c1")], [], 3)):
                run_shop.run("airsoftplaza", None, False)
            with mock.patch.object(run_shop, "scrape", return_value=([_offer("CYMA Platinum AKS-74U replica - Black", "150", "c2")], [], 3)):
                run_shop.run("taiwangun", None, False)
        self.assertEqual(len(db.t["products"]), 1)
        p = db.t["products"][0]
        self.assertIsNone(p["model_code_norm"])
        self.assertEqual(db.t["product_codes"], [])
        self.assertEqual({o["match_method"] for o in db.t["offers"]}, {"new_title", "fuzzy"})


class TestRound4(unittest.TestCase):
    def test_single_offer_id_ignores_sku(self):
        page_a = '<script type="application/ld+json">{"@type":"Product","name":"X","sku":"A1","offers":{"price":"1","priceCurrency":"EUR"}}</script>'
        page_b = '<meta property="og:title" content="X"><meta property="product:price:amount" content="1">'
        a, = extract(page_a, "https://s.pl/x")
        b, = extract(page_b, "https://s.pl/x")
        self.assertEqual(a.external_id, b.external_id)       # JSON-LD vs meta: ugyanaz az ID

    def test_variants_keep_distinct_ids(self):
        offers = extract(PRESTA_VARIANTS.replace('"url":"/p/sa-e01?c=black"', '"url":"/p/sa-e01"').replace('"url":"/p/sa-e01?c=tan"', '"url":"/p/sa-e01"'), "https://shop.eu/p/sa-e01")
        self.assertEqual(len({o.external_id for o in offers}), 2)

    def test_shop_name_suffix_removed(self):
        db = FakeDB()
        _seed(db)
        db.t["shops"][1]["name"] = "AirsoftPlaza"
        db.t["shops"][0]["name"] = "Taiwangun"
        with mock.patch("db.get_db", return_value=db), mock.patch.object(run_shop, "scrape",
                return_value=([_offer("WE GLOCK 18 GEN.3 GÁZ GBB - FEKETE - Airsoftplaza", "53900", "g1")], [], 3)):
            run_shop.run("airsoftplaza", None, False)
        self.assertEqual(db.t["offers"][0]["title_raw"], "WE GLOCK 18 GEN.3 GÁZ GBB - FEKETE")


class TestNames(unittest.TestCase):
    A = {"cyma", "asg", "arsenal", "we", "jg", "jgworks", "emg", "aps", "doublebell", "ggarmament", "gg", "specnaarms"}

    def test_examples(self):
        from names import clean_name
        cases = [
            ("Airsoftová zbraň AK47 Arsenal SLR105", "ASG", "ASG AK47 Arsenal SLR105"),
            ("WE GLOCK 18 GEN.3 GREEN GÁZ GBB - FEKETE", "WE", "WE Glock 18 Gen.3 Green Gas GBB Black"),
            ("CM.513 Sport Line, GEN-2 - TAN [CYMA]", "CYMA", "CYMA CM.513 Sport Line GEN-2 Tan"),
            ("F-1 Firearms UDR-15 AEG - Black - EMG / APS", "EMG", "EMG F-1 Firearms UDR-15 AEG Black"),
            ("JG1011B EBB [J.G.WORKS]", "JG", "JG1011B EBB"),
            ("Replica of the RK-01-W carbine", "Double Bell", "Double Bell RK-01-W"),
            ("G&G CM16 Raider 2.0 Black", "G&G Armament", "G&G Armament CM16 Raider 2.0 Black"),
            # a weboldalon látott cseh címek
            ("Airsoftová zbraň M4 CQB Sportline (CM.506) - černá", "CYMA", "CYMA M4 CQB Sportline CM.506 Black"),
            ("Airsoftový samopal FN Herstal P90 (CM.060) - černá, licencované značení", "CYMA", "CYMA FN Herstal P90 CM.060 Black"),
            ("Airsoftový samopal Thompson M1A1 (CM.033) - celokov, licencované značení", "CYMA", "CYMA Thompson M1A1 CM.033 Full Metal"),
            # magyar / lengyel
            ("Cyma CM.042 AK47 airsoft elektromos gépkarabély fa markolattal, fekete", "CYMA", "CYMA CM.042 AK47 Wood Black"),
            ("Replika karabinka Specna Arms SA-E05 EDGE - czarna", "Specna Arms", "Specna Arms SA-E05 EDGE Black"),
            ("JG MP5 airsoft géppisztoly teljesen fém, licencelt jelölésekkel", "JG", "JG MP5 Full Metal"),
        ]
        for title, brand, exp in cases:
            got = clean_name(title, brand, self.A)
            self.assertEqual(got, exp, title)
            self.assertEqual(clean_name(got, brand, self.A), got, "idempotens: " + title)

    def test_existing_product_renamed_once(self):
        db = FakeDB()
        _seed(db)
        db.t["shops"][1]["name"] = "AirsoftPlaza"
        with mock.patch("db.get_db", return_value=db), mock.patch.object(run_shop, "scrape",
                return_value=([_offer("CYMA CM.522 AK fekete", "79990", "a1")], [], 3)):
            run_shop.run("airsoftplaza", None, False)
            name1 = db.t["products"][0]["name"]
            run_shop.run("airsoftplaza", None, False)
        self.assertEqual(name1, "CYMA CM.522 AK Black")
        self.assertEqual(db.t["products"][0]["name"], name1)        # második futás nem változtat


class TestCoverage(unittest.TestCase):
    def test_clothing_skipped_before_download(self):
        sm = "<urlset>" + "".join(f"<url><loc>{u}</loc></url>" for u in [
            "https://www.taiwangun.com/assault-rifle-aeg/cm-522-sport-line",
            "https://www.taiwangun.com/tactical-trousers/helikon-sfu-next",
            "https://www.taiwangun.com/025g-bbs-6mm/specna-bbs-025g",
            "https://www.taiwangun.com/pl/karabin-szturmowy-aeg/cm-522"]) + "</urlset>"
        fetched = []
        class F(FakeFetcher):
            def get(self, url):
                fetched.append(url)
                return super().get(url)
        fake = F({"https://www.taiwangun.com/sitemap/products_sitemap/": sm,
                  "https://www.taiwangun.com/assault-rifle-aeg/cm-522-sport-line": WOO,
                  "https://www.taiwangun.com/025g-bbs-6mm/specna-bbs-025g": WOO})
        with mock.patch.object(run_shop, "Fetcher", return_value=fake):
            out, errors, stale = run_shop.scrape("taiwangun", None)
        self.assertNotIn("https://www.taiwangun.com/tactical-trousers/helikon-sfu-next", fetched)
        self.assertNotIn("https://www.taiwangun.com/pl/karabin-szturmowy-aeg/cm-522", fetched)
        self.assertEqual(len(fetched), 3)          # sitemap + 2 termék

    def test_listing_offers_clothing_filtered(self):
        def item(n, title):
            return ('{"@type":"Product","name":"%s","sku":"%s","offers":{"price":"10","priceCurrency":"EUR",'
                    '"url":"/en/products/%s.html"}}' % (title, n, n))
        page = '<script type="application/ld+json">[%s]</script>' % ",".join(
            [item("a", "Specna Arms SA-E01"), item("b", "Combat shirt MCU"), item("c", "M4 magazine 120 BB")])
        fake = FakeFetcher({u: (page if i == 0 else "") for i, u in enumerate(run_shop.CONFIG["gunfire"]["start_urls"])})
        with mock.patch.object(run_shop, "Fetcher", return_value=fake):
            out, errors, stale = run_shop.scrape("gunfire", None)
        self.assertEqual(sorted(o.title for o in out), ["M4 magazine 120 BB", "Specna Arms SA-E01"])
