// Világos / sötét téma: sütibe menti, majd visszairányít (JavaScript nélkül is működik)
export async function GET(req) {
  const url = new URL(req.url);
  const t = url.searchParams.get("t");
  const back = url.searchParams.get("back") || "/";
  const safeBack = back.startsWith("/") && !back.startsWith("//") ? back : "/";
  const headers = new Headers({ Location: safeBack });
  if (t === "light" || t === "dark") {
    headers.append("Set-Cookie", `theme=${t}; Path=/; Max-Age=31536000; SameSite=Lax`);
  }
  return new Response(null, { status: 303, headers });
}
