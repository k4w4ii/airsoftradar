// Cloudflare D1 adatréteg (a Supabase PostgREST helyett). A lib/data.js hívja, ha DATA_SOURCE=d1.
// A product_summary táblát a scraper építi (scraper/summary.py); itt csak olvasunk.
// D1 korlát: legfeljebb 100 paraméter / lekérdezés – a szűrők ennél jóval kevesebbet használnak.
import { CAT_GROUPS, PLATFORMS } from "./catalog";

let testDB = null;
/** Teszthez: helyi SQLite a D1 helyett. */
export function __setTestDB(db) { testDB = db; }

export async function getDB() {
  if (testDB) return testDB;
  const { getCloudflareContext } = await import("@opennextjs/cloudflare");
  const { env } = await getCloudflareContext({ async: true });
  if (!env.DB) throw new Error("Hiányzik a D1 kötés (DB) – web/wrangler.jsonc: d1_databases.");
  return env.DB;
}

const all = async (stmt) => (await stmt.all()).results || [];

const GROUP_LEAVES = Object.fromEntries(CAT_GROUPS.map((g) => [g.id, g.leaves]));
const SORT_SQL = {
  popular: "offer_count DESC, price IS NULL, price ASC, id",
  price: "price IS NULL, price ASC, id",
  price_desc: "price IS NULL, price DESC, id",
  name: "name ASC, id",
};

/** Szűrő-darabok: mindegyik facet a SAJÁT szűrője nélkül számol (mint a catalog_search SQL). */
export function buildFilters({ q, cats = [], plats = [], brands = [], pmin, pmax, inStock }) {
  const f = {};
  const words = String(q || "").trim().split(/\s+/).filter(Boolean).slice(0, 5);
  if (words.length) {
    const parts = [], params = [];
    for (const w of words) {
      const code = w.toLowerCase().replace(/[^a-z0-9]/g, "");
      parts.push(`(name LIKE ? ESCAPE '\\' OR manufacturer LIKE ? ESCAPE '\\'${code ? " OR search_code LIKE ?" : ""})`);
      const like = `%${w.replace(/[\\%_]/g, (m) => "\\" + m)}%`;
      params.push(like, like, ...(code ? [`%${code}%`] : []));
    }
    f.q = { sql: parts.join(" AND "), params };
  }
  if (cats.length) {
    const leaves = [...new Set(cats.flatMap((c) => GROUP_LEAVES[c] || [c]))];
    f.cat = { sql: `category IN (${leaves.map(() => "?").join(",")})`, params: leaves };
  }
  if (plats.length) f.plat = { sql: `(${plats.map(() => "platforms LIKE ?").join(" OR ")})`, params: plats.map((p) => `%,${p},%`) };
  if (brands.length) f.brand = { sql: `manufacturer IN (${brands.map(() => "?").join(",")})`, params: brands };
  if (pmin != null || pmax != null) {
    const parts = [], params = [];
    if (pmin != null) { parts.push("price >= ?"); params.push(pmin); }
    if (pmax != null) { parts.push("price <= ?"); params.push(pmax); }
    f.price = { sql: parts.join(" AND "), params };
  }
  if (inStock) f.stock = { sql: "stock = 'in_stock'", params: [] };
  return f;
}

function whereExcept(f, except) {
  const keys = Object.keys(f).filter((k) => k !== except);
  return { sql: keys.length ? " WHERE " + keys.map((k) => f[k].sql).join(" AND ") : "", params: keys.flatMap((k) => f[k].params) };
}

/** A catalog_search RPC megfelelője: találatok + szűrő-darabszámok egy D1-kötegben. */
export async function catalogSearchD1({ q, cats, plats, brands, pmin, pmax, inStock, sort, lim, off, edges }) {
  const db = await getDB();
  const f = buildFilters({ q, cats, plats, brands, pmin, pmax, inStock });
  const w = whereExcept(f, null);
  const T = "FROM product_summary";
  const cols = "id, slug, name, manufacturer, image_url, category, best_price_huf, max_price_huf, min_price_any_huf, offer_count, stock";
  const wc = whereExcept(f, "cat"), wp = whereExcept(f, "plat"), wb = whereExcept(f, "brand"), wpr = whereExcept(f, "price"), ws = whereExcept(f, "stock");
  const platSums = PLATFORMS.map((p) => `SUM(platforms LIKE '%,${p},%') AS "${p}"`).join(", ");
  const bucketCase = edges && edges.length
    ? "CASE " + edges.map((e, i) => `WHEN price < ${Number(e)} THEN ${i}`).join(" ") + ` ELSE ${edges.length} END`
    : null;
  const stmts = [
    db.prepare(`SELECT ${cols} ${T}${w.sql} ORDER BY ${SORT_SQL[sort] || SORT_SQL.popular} LIMIT ? OFFSET ?`).bind(...w.params, lim, off),
    db.prepare(`SELECT count(*) AS n ${T}${w.sql}`).bind(...w.params),
    db.prepare(`SELECT category, count(*) AS n ${T}${wc.sql} GROUP BY category`).bind(...wc.params),
    db.prepare(`SELECT ${platSums} ${T}${wp.sql}`).bind(...wp.params),
    db.prepare(`SELECT manufacturer AS name, count(*) AS n ${T}${wb.sql} GROUP BY manufacturer ORDER BY n DESC, manufacturer`).bind(...wb.params),
    db.prepare(`SELECT min(price) AS min, max(price) AS max ${T}${wpr.sql}`).bind(...wpr.params),
    db.prepare(`SELECT count(*) AS n ${T}${ws.sql ? ws.sql + " AND" : " WHERE"} stock = 'in_stock'`).bind(...ws.params),
  ];
  if (bucketCase) {
    stmts.push(db.prepare(`SELECT ${bucketCase} AS bk, count(*) AS n ${T}${wpr.sql ? wpr.sql + " AND" : " WHERE"} price IS NOT NULL GROUP BY bk`).bind(...wpr.params));
  }
  const res = (await db.batch(stmts)).map((r) => r.results || []);
  const [items, total, catRows, platRow, brandRows, priceRow, stockRow, bucketRows] = res;
  return {
    total: total[0]?.n || 0,
    items,
    facets: {
      categories: Object.fromEntries(catRows.map((r) => [r.category, r.n])),
      platforms: Object.fromEntries(Object.entries(platRow[0] || {}).filter(([, n]) => n > 0)),
      brands: brandRows,
      price: priceRow[0] || { min: null, max: null },
      buckets: bucketRows ? Object.fromEntries(bucketRows.map((r) => [String(r.bk), r.n])) : null,
      in_stock: stockRow[0]?.n || 0,
    },
  };
}

export async function getProductD1(slug) {
  const db = await getDB();
  return (await db.prepare("SELECT * FROM product_summary WHERE slug = ?").bind(slug).first()) || null;
}

/** v_product_offers megfelelője: bolt+URL ismétlődés nélkül, HUF/EUR árral, bolt adataival, eltérő-ár jelzővel. */
export async function getOffersD1(productId) {
  const db = await getDB();
  return all(db.prepare(`
    WITH r AS (SELECT currency, huf_per_unit FROM latest_rates),
    eur AS (SELECT huf_per_unit AS e FROM r WHERE currency = 'EUR'),
    o AS (
      SELECT o.*, round(o.price * CASE WHEN o.currency = 'HUF' THEN 1 ELSE (SELECT huf_per_unit FROM r WHERE r.currency = o.currency) END) AS price_huf
      FROM offers o WHERE o.product_id = ? AND o.is_active = 1
    ),
    d AS (
      SELECT o.*, row_number() OVER (PARTITION BY shop_id, url ORDER BY substr(last_seen_at, 1, 10) DESC, stock = 'in_stock' DESC, price_huf ASC) AS rn
      FROM o WHERE price_huf IS NOT NULL
    )
    SELECT d.id, d.product_id, d.url, d.title_raw, d.price, d.currency, d.price_huf,
           round(d.price_huf / (SELECT e FROM eur), 2) AS price_eur, d.stock, d.last_seen_at, d.is_outlier,
           s.name AS shop_name, s.slug AS shop_slug, s.country AS shop_country
    FROM d JOIN shops s ON s.id = d.shop_id
    WHERE d.rn = 1 ORDER BY d.price_huf`).bind(Number(productId)));
}

export async function getHistoryD1(productId) {
  const db = await getDB();
  return all(db.prepare(`
    SELECT h.observed_on, min(h.price_huf) AS min_huf, min(h.price_eur) AS min_eur
    FROM price_history h JOIN offers o ON o.id = h.offer_id
    WHERE o.product_id = ? AND h.stock = 'in_stock' AND o.is_outlier = 0
    GROUP BY h.observed_on ORDER BY h.observed_on LIMIT 365`).bind(Number(productId)));
}

export async function getRatesD1() {
  const db = await getDB();
  const rows = await all(db.prepare("SELECT currency, huf_per_unit FROM latest_rates"));
  return Object.fromEntries(rows.map((r) => [String(r.currency).trim(), Number(r.huf_per_unit)]));
}

export async function getOfferTargetD1(id) {
  const db = await getDB();
  const row = await db.prepare("SELECT o.url, s.affiliate_template FROM offers o JOIN shops s ON s.id = o.shop_id WHERE o.id = ?")
    .bind(Number(id)).first();
  return row ? { url: row.url, shops: { affiliate_template: row.affiliate_template } } : null;
}

export async function getAllSlugsD1(max = 45000) {
  const db = await getDB();
  return all(db.prepare("SELECT slug, updated_at FROM product_summary ORDER BY id LIMIT ?").bind(max));
}
