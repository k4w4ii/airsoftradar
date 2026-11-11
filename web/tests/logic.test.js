import { test, expect } from "bun:test";
import { cleanQuery } from "../lib/data.js";
import { __setTestDB } from "../lib/data_d1.js";
import { money } from "../lib/i18n.js";
import { GET as cur } from "../app/cur/route.js";
import { GET as go } from "../app/go/[id]/route.js";

test("cleanQuery", () => {
  expect(cleanQuery('a,b(c)*"d')).toBe("a b c d");
  expect(cleanQuery("x".repeat(100)).length).toBe(60);
});

test("money", () => {
  const r = { EUR: 385.4, CZK: 15.3 };
  expect(money(73187, "HUF", r, "hu").replace(/\s/g, " ")).toBe("73 187 Ft");
  expect(money(73187, "EUR", r, "en")).toBe("€189.90");
  expect(money(null, "EUR", r, "en")).toBe("–");
  expect(money(1000, "GBP", r, "en")).toContain("1,000");   // nincs GBP árfolyam -> HUF
});

test("currency cookie route", async () => {
  const res = await cur(new Request("https://x.app/cur?c=EUR&back=%2Fhu%2Fp%2Fabc"));
  expect(res.status).toBe(303);
  expect(res.headers.get("location")).toBe("/hu/p/abc");
  expect(res.headers.get("set-cookie")).toContain("cur=EUR");
  const evil = await cur(new Request("https://x.app/cur?c=XXX&back=%2F%2Fevil.com"));
  expect(evil.headers.get("location")).toBe("/");
  expect(evil.headers.get("set-cookie")).toBeNull();
});

// egysoros D1-utánzat: a .first() a megadott sort adja
const fakeRow = (row) => ({ prepare: () => ({ bind: () => ({ first: async () => row }) }) });

test("go route with affiliate template", async () => {
  __setTestDB(fakeRow({ url: "https://shop.pl/p 1", affiliate_template: "https://aff.net/?u={url}&id=7" }));
  const res = await go(new Request("https://x.app/go/5"), { params: Promise.resolve({ id: "5" }) });
  expect(res.status).toBe(200);
  const body = await res.text();
  expect(body).toContain('location.replace("https://aff.net/?u=https%3A%2F%2Fshop.pl%2Fp%201&id=7")');
  expect(body).toContain('content="0;url=https://aff.net/?u=https%3A%2F%2Fshop.pl%2Fp%201&amp;id=7"');
  // támadó URL (javascript:) nem mehet át
  __setTestDB(fakeRow({ url: "javascript:alert(1)", affiliate_template: null }));
  expect((await go(new Request("https://x.app/go/6"), { params: Promise.resolve({ id: "6" }) })).status).toBe(404);
  __setTestDB(fakeRow(null));
  expect((await go(new Request("https://x.app/go/9"), { params: Promise.resolve({ id: "9" }) })).status).toBe(404);
  __setTestDB(null);
});

test("go route without template: utm + no-referrer", async () => {
  const { withUtm } = await import("../lib/links.js");
  expect(withUtm("https://gunfire.com/en/products/x-1.html")).toBe("https://gunfire.com/en/products/x-1.html?utm_source=airsofthunter&utm_medium=referral");
  expect(withUtm("https://shop.cz/p?id=5#top")).toBe("https://shop.cz/p?id=5&utm_source=airsofthunter&utm_medium=referral#top");
  __setTestDB(fakeRow({ url: "https://gunfire.com/en/products/x-1.html", affiliate_template: null }));
  const body = await (await go(new Request("https://x.app/go/1"), { params: Promise.resolve({ id: "1" }) })).text();
  expect(body).toContain('<meta name="referrer" content="no-referrer">');
  expect(body).toContain('location.replace("https://gunfire.com/en/products/x-1.html?utm_source=airsofthunter&utm_medium=referral")');
  __setTestDB(null);
});

test("shopTarget: közvetlen bolti link", async () => {
  const { shopTarget } = await import("../lib/links.js");
  expect(shopTarget("https://gunfire.com/en/products/am-009-1.html", null))
    .toBe("https://gunfire.com/en/products/am-009-1.html?utm_source=airsofthunter&utm_medium=referral");
  expect(shopTarget("https://shop.pl/p 1", "https://aff.net/?u={url}&id=7")).toBe("https://aff.net/?u=https%3A%2F%2Fshop.pl%2Fp%201&id=7");
  expect(shopTarget("javascript:alert(1)", null)).toBeNull();
  expect(shopTarget(null, null)).toBeNull();
});

test("képcím-normalizálás", async () => {
  const { imgSrc } = await import("../lib/links.js");
  expect(imgSrc("https://atom-airsoft.fi/img/a b,c.jpg")).toBe("https://atom-airsoft.fi/img/a%20b,c.jpg");
  expect(imgSrc("javascript:alert(1)")).toBe(null);
  expect(imgSrc("")).toBe(null);
  expect(imgSrc("nem url")).toBe(null);
});
