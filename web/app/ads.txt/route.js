import { ADS } from "../../lib/site";

// /ads.txt – az AdSense ebből ellenőrzi, hogy jogosult vagy hirdetést megjeleníteni az oldalon.
export function GET() {
  if (!ADS.client) return new Response("", { status: 404 });
  const pub = ADS.client.replace(/^ca-/, "");
  return new Response(`google.com, ${pub}, DIRECT, f08c47fec0942fa0\n`, {
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "public, max-age=86400" },
  });
}
