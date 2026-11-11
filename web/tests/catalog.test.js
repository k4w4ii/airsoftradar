import { test, expect } from "bun:test";
import { hrefFor, normalizeCats, parseCatalog, withoutCat } from "../lib/catalog.js";

const base = { q: "", cats: ["weapons"], plats: [], brands: [], min: 0, max: 0, stock: false, sort: "discount", view: "grid", page: 3 };

test("parseCatalog: alapértelmezés, több kategória, minden termék", () => {
  expect(parseCatalog({}).cats).toEqual(["weapons"]);
  expect(parseCatalog({ q: "glock" }).cats).toEqual([]);
  expect(parseCatalog({ cat: ["all", "rifle", "sniper"] }).cats).toEqual(["rifle", "sniper"]);   // űrlap: rejtett all + pipák
  expect(parseCatalog({ cat: "all" }).cats).toEqual([]);
  expect(parseCatalog({ cat: "rifle,bogus" }).cats).toEqual(["rifle"]);
  expect(parseCatalog({ cat: ["weapons", "rifle", "acc_mag"] }).cats).toEqual(["weapons", "acc_mag"]);  // csoport elnyeli az elemét
  expect(parseCatalog({ plat: ["ak", "m4", "x"] }).plats).toEqual(["m4", "ak"]);
});

test("normalizeCats: teljes csoport -> csoport", () => {
  expect(normalizeCats(["part_internal", "part_hopup", "part_motor", "part_external"])).toEqual(["parts"]);
});

test("hrefFor", () => {
  expect(hrefFor("hu", base)).toBe("/hu?cat=weapons");                     // a /hu az üdvözlő oldal
  expect(hrefFor("hu", base, { sort: "popular", view: "list" })).toBe("/hu?sort=popular&view=list");
  expect(hrefFor("hu", base, { cats: ["rifle", "sniper"] })).toBe("/hu?cat=rifle&cat=sniper");
  expect(hrefFor("hu", base, { cats: [] })).toBe("/hu?cat=all");
  expect(hrefFor("hu", { ...base, cats: ["parts"], plats: ["m4"], brands: ["CYMA"], min: 3000, stock: true }, { page: 2 }))
    .toBe("/hu?cat=parts&plat=m4&brand=CYMA&min=3000&stock=1&page=2");
  expect(hrefFor("en", { ...base, q: "glock", cats: [] })).toBe("/en?q=glock");
});

test("withoutCat: csoportból egy elem kivétele", () => {
  expect(withoutCat(["weapons"], "pistol")).toEqual(["rifle", "smg", "sniper", "lmg", "shotgun", "grenade"]);
  expect(withoutCat(["rifle", "sniper"], "rifle")).toEqual(["sniper"]);
});


test("isWelcome + alapértelmezések", async () => {
  const { isWelcome } = await import("../lib/catalog.js");
  expect(isWelcome({})).toBe(true);
  expect(isWelcome({ utm_source: "x", gclid: "y" })).toBe(true);
  expect(isWelcome({ q: "" })).toBe(true);
  expect(isWelcome({ cat: "weapons" })).toBe(false);
  expect(parseCatalog({ cat: "weapons" })).toMatchObject({ cats: ["weapons"], sort: "discount", view: "grid" });
  expect(parseCatalog({ view: "list", sort: "bogus" })).toMatchObject({ view: "list", sort: "discount" });
});

test("extra szűrők (pow, gt…) és láthatóság", async () => {
  const { parseCatalog, hrefFor, isWelcome, visibleDims, showPlatforms } = await import("../lib/catalog.js");
  const p = parseCatalog({ cat: "weapons", pow: ["gbb", "xyz", "aeg"], bbw: "0.25" });
  expect(p.attrs).toEqual({ pow: ["aeg", "gbb"], bbw: ["0.25"] });
  expect(hrefFor("hu", { ...p, attrs: { pow: p.attrs.pow } })).toBe("/hu?pow=aeg&pow=gbb");
  expect(isWelcome({ pow: "aeg" })).toBe(false);
  expect(visibleDims(["weapons"])).toEqual(["pow", "mdl"]);          // 6/7 fegyverkategória: működés + modell, a gránát nem
  expect(visibleDims(["grenade", "rifle"])).toEqual(["pow", "mdl", "gt"]);   // 2 kategória: mindkettőé
  expect(visibleDims(["lmg"])).toEqual(["pow", "mdl"]);
  expect(showPlatforms(["lmg"])).toBe(false);                         // fegyvernél „Modell”, nem „Mihez jó”
  expect(showPlatforms(["weapons"])).toBe(false);
  expect(showPlatforms(["part_external"])).toBe(true);
  expect(showPlatforms([])).toBe(true);
  expect(parseCatalog({ cat: "lmg", mdl: ["m249", "nincs"] }).attrs).toEqual({ mdl: ["m249"] });
  expect(visibleDims(["acc_ammo"])).toEqual(["bbw", "bbt", "bbq", "gas", "gml"]);
  expect(visibleDims(["acc"])).toEqual([]);                           // az egész „Kiegészítők”: nincs zsúfolt extra szűrő
  expect(visibleDims([])).toEqual([]);
});
