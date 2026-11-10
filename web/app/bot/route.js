// A scraper User-Agentje erre az oldalra mutat: a boltok itt látják, ki és hogyan gyűjt adatot.
const HTML = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AirsoftHunterBot</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 20px;background:#f6f7f8;color:#14171a}a{color:#0b6e4f}</style></head>
<body><h1>AirsoftHunterBot</h1>
<p>AirsoftHunterBot collects publicly listed prices and stock status of airsoft products once a day for the price comparison site <a href="https://www.airsofthunter.com">airsofthunter.com</a>. Every listing links back to the shop.</p>
<ul><li>Respects <code>robots.txt</code>, including <code>Crawl-delay</code>.</li><li>One request at a time per shop, 2–3 seconds apart, at night (CET).</li>
<li>Reads only product name, price, currency, stock status, brand, product code and image URL (schema.org data).</li></ul>
<p>To block the bot, add <code>User-agent: AirsoftHunterBot</code> / <code>Disallow: /</code> to your robots.txt. Shops that prefer a product feed or want to be removed can contact us via the website.</p>
<hr><p lang="hu">Az AirsoftHunterBot naponta egyszer gyűjti az airsoft termékek nyilvános árát és készletét az airsofthunter.com árösszehasonlítóhoz. Betartja a robots.txt-t, boltonként egyszerre egy kérést küld, 2–3 másodperces szünetekkel.</p>
</body></html>`;

export function GET() {
  return new Response(HTML, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=86400" } });
}
