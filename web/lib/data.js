// Supabase PostgREST elérés fetch-csel (nincs supabase-js függőség).
// Szerveroldalon fut; a publishable kulcs csak olvasni tud (RLS).
import { PRICE_EDGES } from "./i18n";

export const PAGE_SIZE = 24;
const REVALIDATE = 1800; // fél óra; az adatok éjjel frissülnek

const SORTS = {
  popular: "offer_count.desc,best_price_huf.asc.nullslast",
  price: "best_price_huf.asc.nullslast",
  price_desc: "best_price_huf.desc.nullslast",
  name: "name.asc",
};

async function q(path, { count = false } = {}) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error("Hiányzik a SUPABASE_URL vagy a SUPABASE_PUBLISHABLE_KEY környezeti változó (Vercel -> Settings -> Environment Variables).");
  }
  const res = await fetch(`${url.replace(/\/$/, "")}/rest/v1/${path}`, {
    headers: { apikey: key, ...(count ? { Prefer: "count=exact" } : {}) },
    next: { revalidate: REVALIDATE },
  });
  if (!res.ok) throw new Error(`Supabase ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const data = await res.json();
  if (!count) return data;
  const total = Number((res.headers.get("content-range") || "").split("/")[1]);
  return { data, total: Number.isFinite(total) ? total : data.length };
}

/** Keresőkifejezés tisztítása a PostgREST szintaxishoz (vessző, zárójel, csillag tilos). */
export function cleanQuery(s) {
  return String(s || "").replace(/[(),*:"\\]/g, " ").replace(/\s+/g, " ").trim().slice(0, 60);
}

export function buildListQuery({ q: query, mfr, stock, sort, page }) {
  const p = new URLSearchParams();
  p.set("select", "id,slug,name,manufacturer,image_url,best_price_huf,max_price_huf,min_price_any_huf,offer_count,in_stock_count,stock");
  const term = cleanQuery(query);
  if (term) {
    // minden szó szerepeljen a névben vagy a gyártóban
    const parts = term.split(" ").slice(0, 4).map((w) => {
      const code = w.toLowerCase().replace(/[^a-z0-9]/g, ""); // CM522 = CM.522 = cm-522
      return `or(name.ilike.*${w}*,manufacturer.ilike.*${w}*${code ? `,search_code.ilike.*${code}*` : ""})`;
    });
    p.set("and", `(${parts.join(",")})`);
  }
  if (mfr) p.set("manufacturer", `eq.${mfr}`);
  if (stock === "1") p.set("stock", "eq.in_stock");
  p.set("order", SORTS[sort] || SORTS.popular);
  const pg = Math.max(1, Number(page) || 1);
  p.set("limit", String(PAGE_SIZE));
  p.set("offset", String((pg - 1) * PAGE_SIZE));
  return { path: `product_summary?${p.toString()}`, page: pg };
}

export async function listProducts(params) {
  const { path, page } = buildListQuery(params);
  const { data, total } = await q(path, { count: true });
  return { items: data, total, page, pages: Math.max(1, Math.ceil(total / PAGE_SIZE)) };
}

export async function getProduct(slug) {
  const rows = await q(`product_summary?slug=eq.${encodeURIComponent(slug)}&limit=1`);
  return rows[0] || null;
}

export async function getOffers(productId) {
  return q(`v_product_offers?product_id=eq.${Number(productId)}&order=price_huf.asc`);
}

export async function getHistory(productId) {
  return q(`v_price_daily?product_id=eq.${Number(productId)}&order=observed_on.asc&limit=365`);
}

export async function getManufacturers() {
  return q("v_manufacturers?order=manufacturer.asc");
}

export async function getRates() {
  const rows = await q("latest_rates?select=currency,huf_per_unit");
  return Object.fromEntries(rows.map((r) => [r.currency, Number(r.huf_per_unit)]));
}

export async function getOfferTarget(id) {
  const rows = await q(`offers?id=eq.${Number(id)}&select=url,shops(affiliate_template)`);
  return rows[0] || null;
}

/** PostgreSQL tömb-literál: {"a","b"} (idézőjel és backslash escape-elve) */
export function pgArray(values) {
  return `{${values.map((v) => `"${String(v).replace(/["\\]/g, (m) => "\\" + m)}"`).join(",")}}`;
}

/**
 * Lista + szűrő-darabszámok egy hívásban (SQL: catalog_search).
 * params: { q, cats[], plats[], brands[], min, max (a választott pénznemben), stock, sort, page }
 */
export function buildSearchQuery(params, currency, rates) {
  const rate = currency === "HUF" ? 1 : rates?.[currency];
  const cur = rate ? currency : "HUF";
  const r = rate || 1;
  const p = new URLSearchParams();
  const term = cleanQuery(params.q);
  if (term) p.set("q", term);
  if (params.cats?.length) p.set("cats", pgArray(params.cats));
  if (params.plats?.length) p.set("plats", pgArray(params.plats));
  if (params.brands?.length) p.set("brands", pgArray(params.brands.slice(0, 30)));
  if (params.min > 0) p.set("pmin", String(Math.floor(params.min * r)));
  if (params.max > 0) p.set("pmax", String(Math.ceil(params.max * r)));
  if (params.stock) p.set("in_stock", "true");
  p.set("sort", params.sort || "popular");
  const page = Math.max(1, Number(params.page) || 1);
  p.set("lim", String(PAGE_SIZE));
  p.set("off", String((page - 1) * PAGE_SIZE));
  const edges = PRICE_EDGES[cur];
  p.set("edges", pgArray(edges.map((e) => Math.round(e * r))));
  // szóköz %20-ként (nem "+"), hogy a márkanevek biztosan helyesen érkezzenek
  return { path: `rpc/catalog_search?${p.toString().replace(/\+/g, "%20")}`, page, edges, currency: cur };
}

export async function catalogSearch(params, currency, rates) {
  const { path, page, edges, currency: cur } = buildSearchQuery(params, currency, rates);
  const res = await q(path);
  return { ...res, page, pages: Math.max(1, Math.ceil((res.total || 0) / PAGE_SIZE)), edges, edgeCurrency: cur };
}

/** Sitemaphez: minden termék slug-ja lapozva (a Supabase egyszerre max. 1000 sort ad) */
export async function getAllSlugs(max = 45000) {
  const out = [];
  for (let off = 0; off < max; off += 1000) {
    const rows = await q(`product_summary?select=slug,updated_at&order=id.asc&limit=1000&offset=${off}`);
    out.push(...rows);
    if (rows.length < 1000) break;
  }
  return out;
}
