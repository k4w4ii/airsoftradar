import { brandSitemap, productSitemap, staticSitemap, xmlResponse } from "../../../lib/sitemap";

export const dynamic = "force-dynamic";

export async function GET(_req, { params }) {
  const { id } = await params;
  if (id === "static.xml") return xmlResponse(staticSitemap());
  if (id === "brands.xml") return xmlResponse(await brandSitemap().catch(() => "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"></urlset>"));
  const m = /^p-(\d{1,3})\.xml$/.exec(id);
  const body = m ? await productSitemap(Number(m[1])).catch(() => null) : null;
  return body ? xmlResponse(body) : new Response("Not found", { status: 404 });
}
