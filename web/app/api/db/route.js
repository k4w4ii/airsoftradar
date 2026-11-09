import { getDB } from "../../../lib/data_d1";

// A scraper (GitHub Actions) ezen a titkos végponton át ír a D1-be (scraper/d1db.py).
// Hitelesítés: Authorization: Bearer <INGEST_TOKEN> (Worker-titok). Ha nincs beállítva token, a végpont nem létezik.
// Egy kérés = legfeljebb 100 utasítás, egy tranzakcióban (D1 batch: hiba esetén semmi nem íródik).
export const dynamic = "force-dynamic";

function sameSecret(a, b) {                 // időzítés-független összehasonlítás
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

export async function POST(req) {
  const token = String(process.env.INGEST_TOKEN || "").trim();
  if (token.length < 32) return new Response("Not found", { status: 404 });
  const auth = req.headers.get("authorization") || "";
  if (!sameSecret(auth.replace(/^Bearer\s+/i, ""), token)) return json({ error: "unauthorized" }, 401);

  let body;
  try { body = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const list = Array.isArray(body?.statements) ? body.statements : null;
  if (!list || !list.length || list.length > 100) return json({ error: "1-100 statements" }, 400);
  if (list.some((s) => typeof s?.sql !== "string" || (s.params && !Array.isArray(s.params)))) return json({ error: "bad statement" }, 400);

  try {
    const db = await getDB();
    const res = await db.batch(list.map((s) => db.prepare(s.sql).bind(...(s.params || []))));
    return json(res.map((r) => ({ results: r.results || [], meta: { changes: r.meta?.changes, rows_written: r.meta?.rows_written } })));
  } catch (e) {
    return json({ error: String(e?.message || e).slice(0, 500) }, 400);
  }
}

export function GET() {
  return new Response("Not found", { status: 404 });
}
