import { act, subscribe } from "../../../lib/alerts";
import { getProduct, getRates } from "../../../lib/data";
import { CURRENCIES, isLocale, plainMoney } from "../../../lib/i18n";
import { mailEnabled } from "../../../lib/mail";

// Ár- és készletfigyelő. POST = feliratkozás a termékoldal űrlapjáról (JavaScript nélkül is működik: visszairányít).
// GET ?a=confirm|stop|stopall&t=<token> = a levélben lévő linkek. POST ?a=stop&t=… = egykattintásos leiratkozás (RFC 8058).
export const dynamic = "force-dynamic";

const back = (req, locale, slug, result) => {
  const base = new URL(req.url).origin;
  const path = slug ? `/${locale}/p/${encodeURIComponent(slug)}` : `/${locale}`;
  return new Response(null, { status: 303, headers: { Location: `${base}${path}?alert=${result}#alert`, "Cache-Control": "no-store" } });
};

export async function GET(req) {
  const u = new URL(req.url);
  const action = u.searchParams.get("a");
  if (!["confirm", "stop", "stopall"].includes(action)) return new Response("Not found", { status: 404 });
  const r = await act(action, u.searchParams.get("t"));
  return back(req, r.locale, r.slug, r.result);
}

export async function POST(req) {
  const u = new URL(req.url);
  if (u.searchParams.get("a") === "stop" && u.searchParams.get("t")) {           // egykattintásos leiratkozás a levelezőből
    await act("stop", u.searchParams.get("t"));
    return new Response("ok", { headers: { "Cache-Control": "no-store" } });
  }
  let f;
  try { f = await req.formData(); } catch { return new Response("Bad request", { status: 400 }); }
  const get = (k) => String(f.get(k) || "").trim();
  const locale = isLocale(get("locale")) ? get("locale") : "hu";
  const slug = get("slug").slice(0, 200);
  if (get("website")) return back(req, locale, slug, "sent");                  // csapda-mező: robot (úgy teszünk, mintha rendben lenne)
  if (!mailEnabled()) return back(req, locale, slug, "off");
  const product = slug ? await getProduct(slug) : null;
  if (!product) return back(req, locale, null, "bad");
  const kind = get("kind") === "price" ? "price" : "stock";
  const currency = CURRENCIES.includes(get("cur")) ? get("cur") : "HUF";
  let targetHuf = null, targetAmount = null, targetText = "";
  if (kind === "price") {
    targetAmount = Number(get("target").replace(/\s/g, "").replace(",", "."));
    const rates = await getRates();
    const rate = currency === "HUF" ? 1 : rates[currency];
    if (!(targetAmount > 0) || !rate || targetAmount > 1e7) return back(req, locale, slug, "bad");
    targetHuf = Math.round(targetAmount * rate);
    targetText = plainMoney(targetAmount, currency, locale);
  }
  const ip = req.headers.get("cf-connecting-ip") || req.headers.get("x-forwarded-for") || "";
  const result = await subscribe({ email: get("email"), product, kind, targetHuf, targetAmount, currency, locale, ip, targetText });
  return back(req, locale, slug, result);
}
