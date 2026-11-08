// Supabase PostgREST elérés fetch-csel (nincs supabase-js függőség).
// Szerveroldalon fut; a publishable kulcs csak olvasni tud (RLS).
const PAGE_SIZE = 24;
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
    const parts = term.split(" ").slice(0, 4).map((w) => `or(name.ilike.*${w}*,manufacturer.ilike.*${w}*)`);
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

export async function getStats() {
  const rows = await q("v_site_stats");
  return rows[0] || { products: 0, offers: 0, shops: 0 };
}

export async function getRates() {
  const rows = await q("latest_rates?select=currency,huf_per_unit");
  return Object.fromEntries(rows.map((r) => [r.currency, Number(r.huf_per_unit)]));
}

export async function getOfferTarget(id) {
  const rows = await q(`offers?id=eq.${Number(id)}&select=url,shops(affiliate_template)`);
  return rows[0] || null;
}
