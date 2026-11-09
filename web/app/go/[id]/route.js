import { getOfferTarget } from "../../../lib/data";
import { withUtm } from "../../../lib/links";

// Kimenő link a boltba; ha a boltnak van affiliate sablonja ({url} helyére kerül a termék URL-je), azt használja.
// Nem HTTP-átirányítás (Location fejléc), hanem egy azonnal továbbugró mini oldal: a Cloudflare-es Next.js
// átalakító (OpenNext) a külső Location címet elrontotta („gunfire.comhttps//gunfire.com/...”).
const esc = (s) => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export async function GET(_req, { params }) {
  const { id } = await params;
  const offer = await getOfferTarget(id).catch(() => null);
  if (!offer?.url) return new Response("Not found", { status: 404 });
  const tpl = offer.shops?.affiliate_template;
  const target = tpl ? tpl.replace("{url}", encodeURIComponent(offer.url)) : withUtm(offer.url);
  if (!/^https?:\/\//i.test(target)) return new Response("Not found", { status: 404 });   // csak http(s) cél
  const js = JSON.stringify(target).replace(/</g, "\\u003c");
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer">
<meta http-equiv="refresh" content="0;url=${esc(target)}"><title>AirsoftHunter</title></head>
<body style="background:#1B2027;color:#E9E4D8;font-family:sans-serif"><script>location.replace(${js})</script>
<p><a style="color:#C8A24E" href="${esc(target)}" rel="nofollow sponsored noopener noreferrer">Tovább a boltba / Continue to the shop</a></p></body></html>`;
  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow" },
  });
}
