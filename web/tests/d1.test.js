import { test, expect, beforeAll, afterAll } from "bun:test";
import { Database } from "bun:sqlite";
import { readFileSync } from "fs";
import * as d1 from "../lib/data_d1.js";
import { catalogSearch, getOffers, getProduct, getHistory, getRates, getOfferTarget } from "../lib/data.js";
import { POST, GET } from "../app/api/db/route.js";

// a Cloudflare D1 felületét utánzó helyi SQLite
function fakeD1(sq) {
  const stmt = (sql, args = []) => ({
    bind: (...a) => { if (a.length > 100) throw new Error("D1: too many SQL variables (" + a.length + ")"); return stmt(sql, a); },
    all: async () => ({ results: sq.query(sql).all(...args), success: true }),
    first: async () => sq.query(sql).get(...args) ?? null,
    _run: () => { const q = sq.query(sql); const rows = q.all(...args); return { results: rows, meta: { changes: sq.query("SELECT changes() AS c").get().c } }; },
  });
  return {
    prepare: (sql) => stmt(sql),
    batch: async (list) => { sq.exec("BEGIN"); try { const r = list.map((s) => s._run()); sq.exec("COMMIT"); return r; } catch (e) { sq.exec("ROLLBACK"); throw e; } },
  };
}

let sq;
const ago = (d) => new Date(Date.now() - d * 864e5).toISOString().slice(0, 10);
const D1 = ago(4), D2 = ago(3), OLD = ago(120);
beforeAll(() => {
  sq = new Database(":memory:");
  sq.exec(readFileSync(new URL("../../d1/schema.sql", import.meta.url).pathname, "utf8"));
  sq.exec(`
    INSERT INTO shops (id,slug,name,base_url,country,currency,affiliate_template) VALUES (1,'a','ShopA','x','PL','EUR',NULL),(2,'b','ShopB','x','HU','HUF','{url}?ref=ah');
    INSERT INTO exchange_rates (currency,rate_date,huf_per_unit) VALUES ('EUR','2026-11-08',380),('EUR','2026-11-09',400);
    INSERT INTO product_summary (id,slug,name,manufacturer,search_code,category,platforms,best_price_huf,offer_count,in_stock_count,stock,price) VALUES
      (1,'cyma-cm048','CYMA CM048 AKM','CYMA','cm048','rifle',',ak,',80000,3,2,'in_stock',80000),
      (2,'specna-sa-e20','Specna Arms SA-E20','Specna Arms','sae20','rifle',',m4,',120000,2,1,'in_stock',120000),
      (3,'bb-020','Specna Arms BB 0.20g 1kg','Specna Arms','','bb','',6000,4,4,'in_stock',6000),
      (4,'cyma-mag','CYMA AK tár 100%_off','CYMA','','acc_mag',',ak,',3000,1,0,'out_of_stock',3000);
    INSERT INTO offers (id,shop_id,external_id,url,title_raw,price,currency,stock,product_id,match_status,is_outlier,last_seen_at) VALUES
      (10,1,'1','https://a/1','CM048',200,'EUR','in_stock',1,'matched',0,'2026-11-09T02:00:00+00:00'),
      (11,2,'2','https://b/2','CM048',85000,'HUF','in_stock',1,'matched',0,'2026-11-09T02:00:00+00:00'),
      (12,2,'3','https://b/2','CM048 régi',90000,'HUF','out_of_stock',1,'matched',0,'2026-11-01T02:00:00+00:00'),
      (13,1,'4','https://a/hpa','CM048 HPA',900,'EUR','in_stock',1,'matched',1,'2026-11-09T02:00:00+00:00');
    INSERT INTO price_history VALUES (10,'${D1}',200,'EUR',76000,200,'in_stock'),(13,'${D1}',900,'EUR',342000,900,'in_stock'),(11,'${D2}',85000,'HUF',85000,212.5,'in_stock'),(11,'${OLD}',99000,'HUF',99000,250,'in_stock');
  `);
  d1.__setTestDB(fakeD1(sq));
});

test("katalógus: szűrés, rendezés, darabszámok", async () => {
  const p = (o) => catalogSearch({ q: "", cats: [], plats: [], brands: [], min: 0, max: 0, stock: false, sort: "price", page: 1, ...o }, "HUF", { EUR: 400 });
  let r = await p({ cats: ["weapons"] });
  expect(r.items.map((x) => x.slug)).toEqual(["cyma-cm048", "specna-sa-e20"]);
  expect(r.total).toBe(2);
  expect(r.facets.categories).toEqual({ rifle: 2, bb: 1, acc_mag: 1 });   // a kategória-facet a saját szűrője nélkül számol
  r = await p({});
  expect(r.facets.categories).toEqual({ rifle: 2, bb: 1, acc_mag: 1 });
  expect(r.facets.platforms).toEqual({ ak: 2, m4: 1 });
  expect(r.facets.in_stock).toBe(3);
  r = await p({ plats: ["ak"], sort: "price_desc" });
  expect(r.items.map((x) => x.id)).toEqual([1, 4]);
  r = await p({ q: "cm-048" });                                            // kódkeresés írásjel nélkül
  expect(r.items.map((x) => x.id)).toEqual([1]);
  r = await p({ q: "100%" });                                              // a % nem joker
  expect(r.items.map((x) => x.id)).toEqual([4]);
  r = await p({ q: "%" });
  expect(r.items.map((x) => x.id)).toEqual([4]);
  r = await p({ brands: ["CYMA"], stock: true });
  expect(r.items.map((x) => x.id)).toEqual([1]);
  expect(r.facets.brands).toEqual([{ name: "CYMA", n: 1 }, { name: "Specna Arms", n: 2 }].sort((a, b) => b.n - a.n));
  r = await catalogSearch({ cats: [], plats: [], brands: [], min: 100, max: 250, sort: "price", page: 1 }, "EUR", { EUR: 400 });
  expect(r.items.map((x) => x.id)).toEqual([1]);                           // 100-250 EUR = 40000-100000 Ft
  expect(r.edgeCurrency).toBe("EUR");
  expect(r.pages).toBe(1);
  sq.exec("UPDATE product_summary SET powers = ',aeg,' WHERE id IN (1,2); UPDATE product_summary SET powers = ',gbb,' WHERE id = 4");
  r = await p({ cats: ["rifle", "acc_mag"], attrs: { pow: ["aeg"] } });
  expect(r.items.map((x) => x.id)).toEqual([1, 2]);
  expect(r.facets.attrs.pow).toEqual({ aeg: 2, gbb: 1 });                 // a saját szűrője nélkül számol
  r = await p({ cats: [], attrs: { pow: ["aeg"] } });                      // „minden termék”: nincs extra szűrő
  expect(r.total).toBe(4);
  sq.exec("INSERT INTO product_summary (id,slug,name,manufacturer,category,subtypes,offer_count,in_stock_count,stock,price) VALUES (5,'tb','Thunder B','X','grenade',',gt=sound,',1,1,'in_stock',9000),(6,'sm','Smoke','X','grenade',',gt=smoke,',1,1,'in_stock',3000)");
  r = await p({ cats: ["grenade"], attrs: { gt: ["smoke"] } });
  expect(r.items.map((x) => x.id)).toEqual([6]);
  expect(r.facets.attrs.gt).toEqual({ sound: 1, smoke: 1 });
  expect((await p({ cats: ["weapons"] })).facets.attrs.gt).toBeUndefined();
  sq.exec("DELETE FROM product_summary WHERE id IN (5,6)");
});

test("termék, ajánlatok (ismétlődés nélkül), előzmény, árfolyam, kattintás", async () => {
  expect((await getProduct("cyma-cm048")).name).toBe("CYMA CM048 AKM");
  expect(await getProduct("nincs")).toBeNull();
  const offers = await getOffers(1);
  expect(offers.map((o) => o.id)).toEqual([10, 11, 13]);                   // a 12 ugyanaz a bolt+URL, régebbi
  expect(offers[0].price_huf).toBe(80000);
  expect(offers[0].price_eur).toBe(200);
  expect(offers[2].is_outlier).toBe(1);
  const h = await getHistory(1);
  expect(h).toEqual([{ observed_on: D1, min_huf: 76000, min_eur: 200 }, { observed_on: D2, min_huf: 85000, min_eur: 212.5 }]);   // a 91 napnál régebbi kimarad
  expect((await getRates()).EUR).toBe(400);
  const t = await getOfferTarget(11);
  expect(t.shops.affiliate_template).toBe("{url}?ref=ah");
});

const TOKEN = "t".repeat(40);
const req = (body, auth) => new Request("https://x/api/db", { method: "POST", headers: auth ? { authorization: auth } : {}, body: JSON.stringify(body) });

test("api/db: token nélkül nincs, rossz tokennel 401, jóval fut (egy tranzakció)", async () => {
  delete process.env.INGEST_TOKEN;
  expect((await POST(req({ statements: [{ sql: "SELECT 1" }] }, "Bearer " + TOKEN))).status).toBe(404);
  process.env.INGEST_TOKEN = TOKEN;
  expect((await POST(req({ statements: [{ sql: "SELECT 1" }] }, "Bearer rossz"))).status).toBe(401);
  expect((await POST(req({ statements: [{ sql: "SELECT 1" }] }))).status).toBe(401);
  expect((await GET()).status).toBe(404);
  expect((await POST(req({ statements: [] }, "Bearer " + TOKEN))).status).toBe(400);
  expect((await POST(req({ statements: Array(101).fill({ sql: "SELECT 1" }) }, "Bearer " + TOKEN))).status).toBe(400);
  let r = await POST(req({ statements: [
    { sql: "INSERT INTO manufacturers (slug,name) VALUES (?,?) RETURNING id, slug", params: ["g&g", "G&G"] },
    { sql: "SELECT count(*) AS n FROM manufacturers" },
  ] }, "Bearer " + TOKEN));
  expect(r.status).toBe(200);
  const out = await r.json();
  expect(out[0].results[0].slug).toBe("g&g");
  expect(out[1].results[0].n).toBe(1);
  r = await POST(req({ statements: [                                       // hiba -> semmi nem íródik
    { sql: "INSERT INTO manufacturers (slug,name) VALUES ('x','X')" },
    { sql: "INSERT INTO manufacturers (slug,name) VALUES ('g&g','dupla')" },
  ] }, "Bearer " + TOKEN));
  expect(r.status).toBe(400);
  expect((await r.json()).error).toContain("UNIQUE");
  expect(sq.query("SELECT count(*) AS n FROM manufacturers").get().n).toBe(1);
});

afterAll(() => { delete process.env.INGEST_TOKEN; d1.__setTestDB(null); });

test("javaslatok, üdvözlő oldal, kedvezmény-rendezés", async () => {
  d1.__setTestDB(fakeD1(sq));
  const { getWelcomeD1, suggestD1 } = d1;
  const s1 = await suggestD1("cm-048");
  expect(s1.products.map((p) => p.slug)).toEqual(["cyma-cm048"]);
  const s2 = await suggestD1("spec");
  expect(s2.brands).toEqual([{ name: "Specna Arms", n: 2 }]);
  expect((await suggestD1("")).products).toEqual([]);
  const w = await getWelcomeD1();
  expect(w.total).toBe(4);
  expect(w.counts.rifle).toBe(2);
  expect(w.shops).toBe(0);
  const r = await catalogSearch({ cats: [], plats: [], brands: [], sort: "discount", page: 1 }, "HUF", { EUR: 400 });
  expect(r.items.length).toBe(4);
  const { GET } = await import("../app/api/suggest/route.js");
  const res = await GET(new Request("https://x/api/suggest?l=hu&q=cyma", { headers: { cookie: "cur=EUR" } }));
  const body = await res.json();
  expect(body.products[0].href).toBe("/hu/p/cyma-cm048");
  expect(body.products[0].price).toContain("200");
  expect(body.brands[0]).toMatchObject({ label: "CYMA", href: "/hu?cat=all&brand=CYMA" });
  const cats = await (await GET(new Request("https://x/api/suggest?l=hu&q=piszt"))).json();
  expect(cats.cats[0]).toMatchObject({ label: "Pisztolyok", href: "/hu?cat=pistol" });
});
