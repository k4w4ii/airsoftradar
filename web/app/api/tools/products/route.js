import { toolProductsD1 } from "../../../../lib/data_d1";
import { isLocale } from "../../../../lib/i18n";
import { toolFilter } from "../../../../lib/toolproducts";

// Kalkulátorok termékajánlója: GET /api/tools/products?kind=bb&lo=0.28&hi=0.30&locale=hu
export const dynamic = "force-dynamic";

export async function GET(req) {
  const u = new URL(req.url);
  const q = Object.fromEntries(u.searchParams);
  const locale = isLocale(q.locale) ? q.locale : "hu";
  const f = toolFilter(q.kind, q, locale);
  if (!f) return Response.json({ items: [], more: null }, { status: 400 });
  let items = [];
  try { items = await toolProductsD1(f.where, f.params); } catch { items = []; }
  return Response.json({ items, more: f.more }, { headers: { "Cache-Control": "public, max-age=600, s-maxage=3600" } });
}
