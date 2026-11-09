// Adatréteg: Cloudflare D1 (a lekérdezések: lib/data_d1.js). Szerveroldalon fut.
import * as d1 from "./data_d1";
import { PRICE_EDGES } from "./i18n";

export const PAGE_SIZE = 24;

/** Keresőkifejezés tisztítása (írásjelek ki, max. 60 karakter). */
export function cleanQuery(s) {
  return String(s || "").replace(/[(),*:"\\]/g, " ").replace(/\s+/g, " ").trim().slice(0, 60);
}

export const getProduct = (slug) => d1.getProductD1(slug);
export const getOffers = (productId) => d1.getOffersD1(productId);
export const getHistory = (productId) => d1.getHistoryD1(productId);
export const getRates = () => d1.getRatesD1();
export const getOfferTarget = (id) => d1.getOfferTargetD1(id);
export const getAllSlugs = (max = 45000) => d1.getAllSlugsD1(max);

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
  const res = await d1.catalogSearchD1({
    q: cleanQuery(params.q), cats: params.cats || [], plats: params.plats || [], brands: (params.brands || []).slice(0, 30),
    pmin: params.min > 0 ? Math.floor(params.min * r) : null, pmax: params.max > 0 ? Math.ceil(params.max * r) : null,
    inStock: !!params.stock, sort: params.sort || "popular", lim: PAGE_SIZE, off: (page - 1) * PAGE_SIZE,
    edges: edges.map((e) => Math.round(e * r)),
  });
  return { ...res, page, pages: Math.max(1, Math.ceil((res.total || 0) / PAGE_SIZE)), edges, edgeCurrency: cur };
}
