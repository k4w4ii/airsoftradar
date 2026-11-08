import { getOfferTarget } from "../../../lib/data";

// Kimenő link a boltba; ha a boltnak van affiliate sablonja ({url} helyére kerül a termék URL-je), azt használja.
export async function GET(_req, { params }) {
  const { id } = await params;
  const offer = await getOfferTarget(id).catch(() => null);
  if (!offer?.url) return new Response("Not found", { status: 404 });
  const tpl = offer.shops?.affiliate_template;
  const target = tpl ? tpl.replace("{url}", encodeURIComponent(offer.url)) : offer.url;
  return Response.redirect(target, 302);
}
