import { test, expect } from "bun:test";
import { LOCALES, t, money, intl } from "../lib/i18n.js";
import { TL } from "../lib/toollabels.js";
import { TOOLS, TOOL_TEXT, TOOLS_INDEX } from "../lib/tools.js";
import { DOCS, DOC_TITLES, FOOTER_LABELS, docFromSlug, legalContent, switchLocale } from "../lib/legal.js";
import { FACETS, facetLabel, facetValue } from "../lib/catalog.js";
import { FACET_I18N } from "../lib/locales/facets.js";

// kulcsok rekurzívan (függvény = levél): minden nyelvnek pontosan ugyanazok a kulcsai legyenek
const keys = (o, p = "") => Object.entries(o).flatMap(([k, v]) =>
  v && typeof v === "object" && !Array.isArray(v) ? keys(v, `${p}${k}.`) : [`${p}${k}:${typeof v}`]).sort();

test("minden nyelv teljes: felület, kalkulátorok, jogi oldalak", () => {
  for (const l of LOCALES) {
    expect(keys(t(l))).toEqual(keys(t("en")));
    expect(keys(TL[l])).toEqual(keys(TL.en));
    expect(keys(TOOLS_INDEX[l])).toEqual(keys(TOOLS_INDEX.en));
    for (const tool of TOOLS) {
      const x = TOOL_TEXT[tool.slug][l];
      expect(keys(x)).toEqual(keys(TOOL_TEXT[tool.slug].en));
      expect(x.how.length).toBe(3);
      expect(x.faq.every((f) => f.length === 2 && f[0] && f[1])).toBe(true);
    }
    expect(Object.keys(DOC_TITLES[l]).sort()).toEqual(Object.keys(DOCS).sort());
    expect(Object.keys(FOOTER_LABELS[l]).sort()).toEqual(Object.keys(DOCS).sort());
    for (const d of Object.keys(DOCS)) {
      expect(docFromSlug(DOCS[d][l])).toBe(d);
      const c = legalContent(l, d);
      // ugyanannyi fejezet, mint a magyar változatban (a szerkezet nem csúszott el)
      expect(c.length).toBe(legalContent("hu", d).length);
      expect(c.every((s) => s.h || s.p || s.list)).toBe(true);
    }
  }
  // jogi oldalak címei nyelvenként egyediek
  const slugs = Object.values(DOCS).flatMap((d) => Object.values(d));
  expect(new Set(slugs).size).toBe(slugs.length);
});

test("szűrőfeliratok: ami angolul nem csak név/szám, az le van fordítva", () => {
  const plain = (s) => /^[\d.,\s–~+gV]+$/.test(s);
  for (const l of ["de", "pl", "cs"]) {
    for (const k of Object.keys(FACETS)) {
      expect(FACET_I18N[l].labels[k]).toBeTruthy();
      for (const [v, h, e] of FACETS[k].values) {
        // ha a magyar és az angol felirat eltér, az egy fordítandó szöveg (pl. „Rugós” / „Spring”), kivéve számok
        if (h !== e && !plain(e) && k !== "bbw" && k !== "volt") expect([k, v, Boolean(FACET_I18N[l].values[k]?.[v])]).toEqual([k, v, true]);
      }
    }
  }
  expect(facetValue("bbw", "0.25", "de")).toBe("0,25 g");
  expect(facetValue("volt", "7.4", "en")).toBe("7.4 V");
  expect(facetValue("pow", "aeg", "pl")).toBe("AEG (elektryczne)");
  expect(facetLabel("pow", "cs")).toBe("Pohon");
});

test("nyelvváltó bármelyik nyelvre, jogi oldal címével", () => {
  expect(switchLocale("/hu/adatvedelem", "hu", "de")).toBe("/de/datenschutz");
  expect(switchLocale("/pl/regulamin", "pl", "cs")).toBe("/cs/podminky-uziti");
  expect(switchLocale("/de?cat=rifle&brand=CYMA", "de", "pl")).toBe("/pl?cat=rifle&brand=CYMA");
  expect(switchLocale("/cs/p/cyma-cm048", "cs", "hu")).toBe("/hu/p/cyma-cm048");
});

test("többes szám és formázás", () => {
  expect(t("pl").items(1)).toBe("1 produkt");
  expect(t("pl").items(3)).toBe("3 produkty");
  expect(t("pl").items(12)).toBe("12 produktów");
  expect(t("pl").items(22)).toBe("22 produkty");
  expect(t("cs").items(4)).toBe("4 produkty");
  expect(t("cs").items(5)).toBe("5 produktů");
  expect(t("cs").range(30)).toBe("30 dní");
  expect(t("de").shops(1)).toBe("1 Shop");
  expect(intl("cs")).toBe("cs-CZ");
  expect(money(4000, "CZK", { CZK: 16 }, "cs").replace(/\s/g, " ")).toBe("250 Kč");
  expect(money(4000, "PLN", { PLN: 100 }, "pl").replace(/\s/g, " ")).toBe("40,00 zł");
});
