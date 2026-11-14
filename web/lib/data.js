import { visibleDims } from "./catalog";
// Adatréteg: Cloudflare D1 (a lekérdezések: lib/data_d1.js). Szerveroldalon fut.
import * as d1 from "./data_d1";
import { cached } from "./cache";
import { PRICE_EDGES } from "./i18n";

export const PAGE_SIZE = 24;

/** Keresőkifejezés tisztítása (írásjelek ki, max. 60 karakter). */
export function cleanQuery(s) {
  return String(s || "").replace(/[(),*:"\\]/g, " ").replace(/\s+/g, " ").trim().slice(0, 60);
}

const HOUR = 3600;
export const getProduct = (slug) => d1.getProductD1(slug);                    // indexelt, olcsó: mindig friss
export const getOffers = (productId) => d1.getOffersD1(productId);
export const getHistory = (productId) => cached("history", productId, HOUR, () => d1.getHistoryD1(productId));
export const getRates = () => cached("rates", null, HOUR, () => d1.getRatesD1());
export const getOfferTarget = (id) => d1.getOfferTargetD1(id);
export const getAllSlugs = (max = 45000, offset = 0) => cached("slugs", [max, offset], 6 * HOUR, () => d1.getAllSlugsD1(max, offset));
export const countProducts = () => cached("count", null, 6 * HOUR, () => d1.countProductsD1());
export const getWelcome = () => cached("welcome", null, HOUR, () => d1.getWelcomeD1());
export const suggest = (q) => { const c = cleanQuery(q).toLowerCase(); return cached("suggest", c, HOUR, () => d1.suggestD1(c)); };
export const brandStats = () => cached("brandstats", null, 6 * HOUR, () => d1.brandStatsD1());
export const collectionSummary = (brand, leaves) => cached("collection", [brand, leaves], 6 * HOUR, () => d1.collectionSummaryD1(brand, leaves));

/**
 * Lista + szűrő-darabszámok egy D1-kötegben.
 * params: { q, cats[], plats[], brands[], min, max (a választott pénznemben), stock, sort, page }
 */
export async function catalogSearch(params, currency, rates) {
  const rate = currency === "HUF" ? 1 : rates?.[currency];
  const cur = rate ? currency : "HUF";
  const r = rate || 1;
  const page = Math.max(1, Number(params.page) || 1);
  const edges = PRICE_EDGES[cur];
  // csak a kiválasztott kategóriához tartozó extra szűrők számítanak (kategóriaváltáskor a régiek nem maradnak „láthatatlanul”)
  const dims = visibleDims(params.cats || []);
  const attrs = Object.fromEntries(Object.entries(params.attrs || {}).filter(([k]) => dims.includes(k)));
  const args = {
    q: cleanQuery(params.q), cats: params.cats || [], attrs, dims, plats: params.plats || [], brands: (params.brands || []).slice(0, 30),
    pmin: params.min > 0 ? Math.floor(params.min * r) : null, pmax: params.max > 0 ? Math.ceil(params.max * r) : null,
    inStock: !!params.stock, sort: params.sort || "discount", lim: PAGE_SIZE, off: (page - 1) * PAGE_SIZE,
    edges: edges.map((e) => Math.round(e * r)),
  };
  const res = await cached("catalog", args, HOUR, () => d1.catalogSearchD1(args));
  return { ...res, page, pages: Math.max(1, Math.ceil((res.total || 0) / PAGE_SIZE)), edges, edgeCurrency: cur };
}
