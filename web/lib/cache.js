// Lekérdezés-gyorsítótár a Cloudflare ingyenes Cache API-jával (caches.default).
// Miért: a D1 ingyenes kerete napi 5 millió BEOLVASOTT sor. Egy listaoldal ~10 teljes táblabejárás (szűrő-darabszámok),
// vagyis gyorsítótár nélkül pár tucat látogató / keresőrobot is kimerítené. Az adat naponta egyszer frissül,
// ezért az 1 órás tárolás nem látszik a látogatónak, a D1-terhelést viszont a töredékére csökkenti.
// Helyi futtatásnál és tesztben nincs caches.default -> közvetlen lekérdezés.
const HOST = "https://cache.airsofthunter.internal";

export async function cached(name, args, ttl, fn) {
  const store = globalThis.caches?.default;
  if (!store) return fn();
  let key;
  try {
    key = new Request(`${HOST}/${name}?k=${encodeURIComponent(JSON.stringify(args ?? null))}`);
    const hit = await store.match(key);
    if (hit) return await hit.json();
  } catch { /* a gyorsítótár hibája sosem törheti el az oldalt */ }
  const value = await fn();
  try {
    if (key && value != null) {
      await store.put(key, new Response(JSON.stringify(value), {
        headers: { "Content-Type": "application/json", "Cache-Control": `public, max-age=${ttl}` },
      }));
    }
  } catch { /* nem baj */ }
  return value;
}
