import { test, expect, beforeAll, afterAll } from "bun:test";
import { Database } from "bun:sqlite";
import { readFileSync } from "fs";
import * as d1 from "../lib/data_d1.js";
import { breadcrumbJsonLd, brandSlug, catalogMeta, collectionPath, historyStats, lastDays, ldJson, productJsonLd } from "../lib/seo.js";
import { parseCatalog } from "../lib/catalog.js";
import { t } from "../lib/i18n.js";
import { __resetAlerts, act, confirmMail, subscribe, validEmail } from "../lib/alerts.js";
import { brandSitemap } from "../lib/sitemap.js";
import { mailEnabled, sendMail } from "../lib/mail.js";

function fakeD1(sq) {
  const stmt = (sql, args = []) => ({
    bind: (...a) => { if (a.length > 100) throw new Error("too many SQL variables"); return stmt(sql, a); },
    all: async () => ({ results: sq.query(sql).all(...args) }),
    first: async () => sq.query(sql).get(...args) ?? null,
    run: async () => { sq.query(sql).run(...args); return { success: true }; },
    _run: () => ({ results: sq.query(sql).all(...args) }),
  });
  return {
    prepare: (sql) => stmt(sql),
    batch: async (list) => { sq.exec("BEGIN"); try { const r = list.map((s) => s._run()); sq.exec("COMMIT"); return r; } catch (e) { sq.exec("ROLLBACK"); throw e; } },
  };
}

let sq;
beforeAll(() => {
  sq = new Database(":memory:");
  sq.exec(readFileSync(new URL("../../d1/schema.sql", import.meta.url).pathname, "utf8"));
  sq.exec(`
    INSERT INTO shops (id,slug,name,base_url,country,currency) VALUES (1,'a','ShopA','x','PL','EUR'),(2,'b','ShopB','x','HU','HUF');
    INSERT INTO exchange_rates (currency,rate_date,huf_per_unit) VALUES ('EUR','2026-11-09',400);
    INSERT INTO product_summary (id,slug,name,manufacturer,search_code,category,best_price_huf,offer_count,in_stock_count,stock,price) VALUES
      (1,'cyma-cm048','CYMA CM048','CYMA','x','rifle',80000,2,2,'in_stock',80000),
      (2,'cyma-cm030','CYMA CM030','CYMA','x','rifle',20000,1,1,'in_stock',20000),
      (3,'cyma-cm016','CYMA CM016','CYMA','x','rifle',NULL,1,0,'out_of_stock',30000),
      (4,'cyma-g18','CYMA G18','CYMA','x','pistol',9000,1,1,'in_stock',9000),
      (5,'specna-e20','Specna Arms SA-E20','Specna Arms','x','rifle',120000,1,1,'in_stock',120000);
    INSERT INTO offers (id,shop_id,external_id,url,title_raw,price,currency,stock,product_id,match_status,is_active) VALUES
      (10,1,'1','u1','t',200,'EUR','in_stock',1,'matched',1),(11,2,'2','u2','t',85000,'HUF','in_stock',1,'matched',1),
      (12,2,'3','u3','t',20000,'HUF','in_stock',2,'matched',1),(13,1,'4','u4','t',75,'EUR','out_of_stock',3,'matched',1);
  `);
  d1.__setTestDB(fakeD1(sq));
});
afterAll(() => { d1.__setTestDB(null); delete process.env.RESEND_API_KEY; });

const offers = [
  { id: 1, shop_name: "A", price_huf: 80000, stock: "in_stock", is_outlier: 0 },
  { id: 2, shop_name: "B", price_huf: 92000, stock: "in_stock", is_outlier: 0 },
  { id: 3, shop_name: "C", price_huf: 70000, stock: "out_of_stock", is_outlier: 0 },
  { id: 4, shop_name: "D", price_huf: 400000, stock: "in_stock", is_outlier: 1 },
];
const product = { slug: "cyma-cm048", name: "CYMA CM048 </script>", manufacturer: "CYMA", model_code: "CM048", image_url: "https://img/x.jpg" };

test("Product + AggregateOffer JSON-LD", () => {
  const hu = productJsonLd({ product, offers, locale: "hu", rates: { EUR: 400 } });
  expect(hu.offers).toEqual({ "@type": "AggregateOffer", priceCurrency: "HUF", lowPrice: 80000, highPrice: 92000, offerCount: 2,
                              availability: "https://schema.org/InStock", url: "https://www.airsofthunter.com/hu/p/cyma-cm048" });
  expect(hu.brand.name).toBe("CYMA");
  expect(hu.mpn).toBe("CM048");
  const en = productJsonLd({ product, offers, locale: "en", rates: { EUR: 400 } });
  expect([en.offers.priceCurrency, en.offers.lowPrice, en.offers.highPrice]).toEqual(["EUR", 200, 230]);
  const out = productJsonLd({ product, offers: offers.map((o) => ({ ...o, stock: "out_of_stock" })), locale: "hu", rates: {} });
  expect(out.offers.availability).toBe("https://schema.org/OutOfStock");
  expect(out.offers.lowPrice).toBe(70000);
  expect(productJsonLd({ product, offers: [], locale: "hu", rates: {} })).toBe(null);
  expect(ldJson(hu)).not.toContain("</script>");
  expect(breadcrumbJsonLd([{ name: "x", path: "/hu" }]).itemListElement[0].item).toBe("https://www.airsofthunter.com/hu");
});

test("árelőzmény: 30 napos legalacsonyabb, átlag, valódi akció-e", () => {
  const today = new Date("2026-11-30T12:00:00Z");
  const pts = (vals) => vals.map((v, i) => ({ observed_on: new Date(today - (vals.length - i) * 864e5).toISOString().slice(0, 10), min_huf: v }));
  expect(historyStats(pts([100, 100, 100, 100]), 90, today)).toBe(null);                  // kevés adat
  expect(historyStats(pts([100, 100, 100, 100, 100, 100]), 90, today).verdict).toBe("low");
  expect(historyStats(pts([100, 90, 100, 100, 100, 100]), 92, today)).toMatchObject({ verdict: "below", low: 90 });
  expect(historyStats(pts([100, 90, 100, 100, 100, 100]), 98, today).verdict).toBe("near");
  expect(historyStats(pts([100, 90, 100, 100, 100, 100]), 120, today)).toMatchObject({ verdict: "above", diff: 22 });
  expect(lastDays(pts([1, 2, 3, 4, 5]), 2, today).map((p) => p.min_huf)).toEqual([4, 5]);
});

test("kanonikus cím és noindex a szűrt listákra", () => {
  const tr = t("hu");
  const m = (q) => catalogMeta("hu", parseCatalog(q), tr);
  expect(m({ q: "cm048" }).robots).toEqual({ index: false, follow: true });
  expect(m({ cat: "rifle", sort: "price", view: "list" }).alternates.canonical).toBe("/hu?cat=rifle");
  expect(m({ cat: "rifle", page: "3" }).alternates.canonical).toBe("/hu?cat=rifle&page=3");
  expect(m({ cat: "rifle", brand: "Specna Arms" }).alternates.canonical).toBe("/hu/b/specna-arms/rifle");
  expect(m({ cat: "all", brand: "CYMA" }).alternates.canonical).toBe("/hu/b/cyma");
  expect(m({ cat: "rifle", brand: "CYMA", plat: "ak" }).alternates.canonical).toBe("/hu?cat=rifle");
  expect(m({ cat: ["rifle", "pistol"] }).alternates.canonical).toBe("/hu?cat=weapons");
  expect(brandSlug("E&L Airsoft")).toBe("e-l-airsoft");
  expect(brandSlug("Árpád")).toBe("arpad");
  expect(collectionPath("en", "Tokyo Marui", "pistol")).toBe("/en/b/tokyo-marui/pistol");
});

test("márka-gyűjtőoldalak sitemapje (legalább 3 termék)", async () => {
  const xml = await brandSitemap();
  expect(xml).toContain("https://www.airsofthunter.com/hu/b/cyma</loc>");
  expect(xml).toContain("https://www.airsofthunter.com/en/b/cyma/rifle</loc>");
  expect(xml).not.toContain("/b/cyma/pistol<");                   // 1 pisztoly: túl kevés
  expect(xml).not.toContain("/b/specna-arms");                     // 1 termék: túl kevés
  const s = await d1.collectionSummaryD1("CYMA", ["rifle"]);
  expect(s).toEqual({ n: 3, inStock: 2, low: 20000, shops: 2 });
});

test("értesítő: feliratkozás, dupla megerősítés, leiratkozás, korlátok", async () => {
  __resetAlerts();
  expect(validEmail("a@b.hu")).toBe(true);
  expect(validEmail("a@b")).toBe(false);
  expect(validEmail("<x>@b.hu")).toBe(false);
  const mails = [];
  const mailer = async (m) => { mails.push(m); return true; };
  const p = { id: 3, slug: "cyma-cm016", name: "CYMA CM016" };
  const base = { email: " A@B.hu ", product: p, kind: "stock", locale: "hu", ip: "1.2.3.4" };
  expect(await subscribe({ ...base, email: "rossz" }, mailer)).toBe("bad");
  expect(await subscribe({ ...base, kind: "price", targetHuf: 0 }, mailer)).toBe("bad");
  expect(await subscribe(base, mailer)).toBe("sent");
  expect(mails[0].to).toBe("a@b.hu");
  expect(mails[0].subject).toContain("CYMA CM016");
  const token = /a=confirm&t=([a-f0-9]{48})/.exec(mails[0].text)[1];
  expect(mails[0].headers["List-Unsubscribe"]).toContain(`a=stop&t=${token}`);
  let row = sq.query("SELECT * FROM alerts WHERE token = ?").get(token);
  expect(row.confirmed_at).toBe(null);
  expect(row.ip_hash).toHaveLength(16);
  expect(row.ip_hash).not.toContain("1.2.3.4");
  expect(await act("confirm", token)).toEqual({ result: "ok", slug: "cyma-cm016", locale: "hu" });
  expect(sq.query("SELECT confirmed_at FROM alerts WHERE token = ?").get(token).confirmed_at).toBeTruthy();
  // már megerősített: új levél nélkül csak frissül
  expect(await subscribe(base, mailer)).toBe("ok");
  expect(mails.length).toBe(1);
  expect(await act("stop", token)).toMatchObject({ result: "stopped" });
  expect(await act("confirm", token)).toMatchObject({ result: "expired" });
  expect(await act("confirm", "nem-token")).toMatchObject({ result: "expired" });
  // IP-korlát: óránként 10 új kérés
  const results = [];
  for (let i = 0; i < 11; i++) results.push(await subscribe({ ...base, email: `x${i}@b.hu`, ip: "9.9.9.9" }, mailer));
  expect(results.slice(0, 10).every((r) => r === "sent")).toBe(true);
  expect(results[10]).toBe("limit");
  // sikertelen küldés: a kérés nem marad meg
  expect(await subscribe({ ...base, email: "fail@b.hu", ip: "5.5.5.5" }, async () => false)).toBe("off");
  expect(sq.query("SELECT count(*) AS n FROM alerts WHERE email = 'fail@b.hu'").get().n).toBe(0);
  // mindről leiratkozás
  const tok2 = sq.query("SELECT token FROM alerts WHERE email = 'x1@b.hu'").get().token;
  expect(await act("stopall", tok2)).toMatchObject({ result: "stoppedAll" });
});

test("levél: célár szövege, HTML-escape, adatvédelmi link", () => {
  const m = confirmMail({ locale: "en", name: "<b>X</b>", kind: "price", targetText: "€150", token: "a".repeat(48) });
  expect(m.subject).toBe("Confirm your alert: <b>X</b>");
  expect(m.html).toContain("&lt;b&gt;X&lt;/b&gt;");
  expect(m.html).toContain("€150");
  expect(m.html).toContain("https://www.airsofthunter.com/en/privacy");
});

test("e-mail szolgáltató: kulcs nélkül ki, Resend formátum", async () => {
  delete process.env.RESEND_API_KEY;
  delete process.env.BREVO_API_KEY;
  expect(mailEnabled()).toBe(false);
  expect(await sendMail({ to: "a@b.hu", subject: "s", html: "h", text: "t" })).toBe(false);
  process.env.RESEND_API_KEY = "re_test";
  const calls = [];
  const ok = await sendMail({ to: "a@b.hu", subject: "s", html: "h", text: "t" }, async (url, init) => { calls.push([url, init]); return { ok: true }; });
  expect(ok).toBe(true);
  expect(calls[0][0]).toBe("https://api.resend.com/emails");
  expect(JSON.parse(calls[0][1].body).to).toEqual(["a@b.hu"]);
  expect(calls[0][1].headers.Authorization).toBe("Bearer re_test");
});

test("értesítő végpont: csapda-mező, kikapcsolt állapot, hibás link", async () => {
  const { POST, GET } = await import("../app/api/alert/route.js");
  const form = (o) => { const f = new FormData(); for (const [k, v] of Object.entries(o)) f.set(k, v); return f; };
  const post = (o) => POST(new Request("https://www.airsofthunter.com/api/alert", { method: "POST", body: form(o) }));
  delete process.env.RESEND_API_KEY;
  let r = await post({ slug: "cyma-cm016", locale: "hu", email: "a@b.hu", kind: "stock", website: "spam" });
  expect(r.status).toBe(303);
  expect(r.headers.get("location")).toBe("https://www.airsofthunter.com/hu/p/cyma-cm016?alert=sent#alert");
  r = await post({ slug: "cyma-cm016", locale: "en", email: "a@b.hu", kind: "stock" });
  expect(r.headers.get("location")).toContain("/en/p/cyma-cm016?alert=off");
  r = await GET(new Request("https://www.airsofthunter.com/api/alert?a=confirm&t=xyz"));
  expect(r.headers.get("location")).toBe("https://www.airsofthunter.com/hu?alert=expired#alert");
  expect((await GET(new Request("https://www.airsofthunter.com/api/alert?a=hack&t=x"))).status).toBe(404);
});

test("nyelvváltás: ugyanaz az oldal a másik nyelven", async () => {
  const { switchLocale } = await import("../lib/legal.js");
  expect(switchLocale("/hu?cat=rifle&brand=CYMA", "hu")).toBe("/en?cat=rifle&brand=CYMA");
  expect(switchLocale("/en/p/cyma-cm048", "en")).toBe("/hu/p/cyma-cm048");
  expect(switchLocale("/hu/b/cyma/rifle", "hu")).toBe("/en/b/cyma/rifle");
  expect(switchLocale("/hu/adatvedelem", "hu")).toBe("/en/privacy");
  expect(switchLocale("/en/terms", "en")).toBe("/hu/aszf");
  expect(switchLocale("/hu", "hu")).toBe("/en");
  expect(switchLocale("", "hu")).toBe("/en");
  expect(switchLocale("/hungary", "hu")).toBe("/en");
});

test("adatvédelem: a beállított e-mail szolgáltató szerepel", async () => {
  const { legalContent } = await import("../lib/legal.js");
  const text = (l) => JSON.stringify(legalContent(l, "privacy"));
  delete process.env.RESEND_API_KEY;
  process.env.BREVO_API_KEY = "x";
  expect(text("hu")).toContain("Brevo");
  expect(text("hu")).not.toContain("Resend");
  delete process.env.BREVO_API_KEY;
  process.env.RESEND_API_KEY = "x";
  expect(text("en")).toContain("Resend");
  expect(text("en")).toContain("Cloudflare and Resend are US companies");
  delete process.env.RESEND_API_KEY;
  expect(text("hu")).toContain("Brevo");                       // kulcs nélkül a site.js tartaléka (brevo)
});
