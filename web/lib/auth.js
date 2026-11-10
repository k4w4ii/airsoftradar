// A scraper titkos végpontjának (/api/db) hitelesítése: Authorization: Bearer <INGEST_TOKEN>.
// Ha a Worker-titok nincs beállítva (vagy túl rövid), a végpontok nem léteznek (404).
export function ingestToken() {
  const token = String(process.env.INGEST_TOKEN || "").trim();
  return token.length >= 32 ? token : null;
}

export function sameSecret(a, b) {                 // időzítés-független összehasonlítás
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/** null = rendben; különben a visszaadandó válasz (404 / 401). */
export function checkIngest(req) {
  const token = ingestToken();
  if (!token) return new Response("Not found", { status: 404 });
  const auth = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!sameSecret(auth, token)) {
    return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401, headers: { "Content-Type": "application/json" } });
  }
  return null;
}
