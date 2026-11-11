import { test, expect } from "bun:test";
test("robots + darabolt sitemap", async () => {
  const { __setTestDB } = await import("../lib/data_d1.js");
  const N = 23719;
  __setTestDB({ prepare: (sql) => ({
    first: async () => ({ n: N }),
    bind: (lim, off) => ({ all: async () => ({ results: Array.from({ length: Math.max(0, Math.min(lim, N - off)) }, (_, i) => ({ slug: `p${off + i}`, updated_at: "2026-11-08T02:00:00Z" })) }) }),
  }) });
  const robots = (await import("../app/robots.js")).default();
  expect(robots.sitemap).toBe("https://www.airsofthunter.com/sitemap.xml");
  expect(robots.rules[0].userAgent).toContain("Googlebot");
  expect(robots.rules[0].userAgent).not.toContain("Google-Extended");
  expect(robots.rules[1]).toEqual({ userAgent: "*", disallow: "/" });
  const idx = await (await (await import("../app/sitemap.xml/route.js")).GET()).text();
  expect(idx.includes("<sitemapindex")).toBe(true);
  expect((idx.match(/<loc>/g) || []).length).toBe(4);       // static + 3 termékfájl
  const part = await import("../app/sitemaps/[id]/route.js");
  const p2 = await (await part.GET(null, { params: Promise.resolve({ id: "p-2.xml" }) })).text();
  expect((p2.match(/<url>/g) || []).length).toBe(2 * (N - 20000));
  expect(p2.includes('hreflang="en" href="https://www.airsofthunter.com/en/p/p20000"')).toBe(true);
  const st = await (await part.GET(null, { params: Promise.resolve({ id: "static.xml" }) })).text();
  expect(st.includes("<loc>https://www.airsofthunter.com/hu</loc>")).toBe(true);
  expect((await part.GET(null, { params: Promise.resolve({ id: "p-9.xml" }) })).status).toBe(404);
  expect((await part.GET(null, { params: Promise.resolve({ id: "../x" }) })).status).toBe(404);
  const bot = await (await import("../app/bot/route.js")).GET();
  expect((await bot.text()).includes("AirsoftHunterBot")).toBe(true);
  __setTestDB(null);
});
