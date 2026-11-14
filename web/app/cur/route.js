import { CURRENCIES } from "../../lib/i18n";

// Pénznemválasztó: sütibe menti, majd visszairányít (JavaScript nélkül is működik)
export async function GET(req) {
  const url = new URL(req.url);
  const c = url.searchParams.get("c");
  const back = url.searchParams.get("back") || "/";
  const safeBack = /^\/(?![\/\\])[^\\\r\n]*$/.test(back) ? back : "/";   // csak saját útvonal (//, /\\ és sortörés kizárva)
  const headers = new Headers({ Location: safeBack });
  if (CURRENCIES.includes(c)) {
    headers.append("Set-Cookie", `cur=${c}; Path=/; Max-Age=31536000; SameSite=Lax`);
  }
  return new Response(null, { status: 303, headers });
}
