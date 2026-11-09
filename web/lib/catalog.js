// Katalógus-szűrők: kategóriafa, platformok, URL <-> szűrőállapot. Tiszta függvények (szerveren és tesztben is).

export const CAT_GROUPS = [
  { id: "weapons", leaves: ["rifle", "pistol", "smg", "sniper", "lmg", "shotgun", "grenade"] },
  { id: "parts", leaves: ["part_internal", "part_hopup", "part_motor", "part_external"] },
  { id: "acc", leaves: ["acc_mag", "acc_power", "acc_optics", "acc_ammo", "acc_protect", "acc_gear", "other"] },
];
export const GROUP_IDS = CAT_GROUPS.map((g) => g.id);
export const LEAVES = CAT_GROUPS.flatMap((g) => g.leaves);
export const groupOf = (leaf) => CAT_GROUPS.find((g) => g.leaves.includes(leaf))?.id;

// „Mihez jó”: sorrend a szűrőben (SQL: airsoft_platforms)
export const PLATFORMS = ["m4", "ak", "g36", "mp5", "aug", "scar", "m14", "p90", "vsr", "l96", "glock", "hicapa", "m9", "gb_v2", "gb_v3"];

export const SORTS = ["discount", "popular", "price", "price_desc", "name"];
export const DEFAULT_SORT = "discount";          // legnagyobb árkülönbség (legolcsóbb vs. legdrágább bolt)
export const VIEWS = ["grid", "list"];           // csempe az alap

/** Üres cím (/hu, /en) = üdvözlő oldal; bármilyen paraméter = katalógus. */
const CATALOG_KEYS = ["q", "cat", "plat", "brand", "min", "max", "stock", "sort", "view", "page"];
export const isWelcome = (sp) => !CATALOG_KEYS.some((k) => sp?.[k] !== undefined && sp[k] !== "");   // utm_*, gclid stb. nem számít

/** Keresés nélkül a fegyverek az alap, kereséskor minden termék. */
export const defaultCats = (q) => (q ? [] : ["weapons"]);

/** Ismeretlen értékek ki; ha egy csoport minden eleme be van jelölve, a csoport marad; a csoport elnyeli a saját elemeit. */
export function normalizeCats(tokens) {
  const set = new Set(tokens.filter((t) => GROUP_IDS.includes(t) || LEAVES.includes(t)));
  for (const g of CAT_GROUPS) {
    if (g.leaves.every((l) => set.has(l))) set.add(g.id);
    if (set.has(g.id)) g.leaves.forEach((l) => set.delete(l));
  }
  return [...GROUP_IDS, ...LEAVES].filter((t) => set.has(t));     // stabil sorrend -> stabil URL
}

const list = (v) => [].concat(v ?? []).filter((x) => typeof x === "string").flatMap((x) => x.split(",")).map((x) => x.trim()).filter(Boolean);
const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

/** searchParams -> szűrőállapot. A „cat=all” (vagy üres cat) = minden termék; ha a cat hiányzik, az alapértelmezés. */
export function parseCatalog(sp) {
  const one = (k) => (typeof sp[k] === "string" ? sp[k] : Array.isArray(sp[k]) ? sp[k][0] ?? "" : "");
  const q = one("q").trim().slice(0, 60);
  const rawCats = list(sp.cat);
  const cats = sp.cat === undefined ? defaultCats(q) : normalizeCats(rawCats);
  const plats = PLATFORMS.filter((p) => list(sp.plat).includes(p));
  const brands = [].concat(sp.brand || []).filter((b) => typeof b === "string" && b).slice(0, 30);
  const num = (k) => Math.max(0, Math.round(Number(one(k)) || 0));
  let [min, max] = [num("min"), num("max")];
  if (min && max && min > max) [min, max] = [max, min];
  return { q, cats, plats, brands, min, max, stock: one("stock") === "1",
           sort: SORTS.includes(one("sort")) ? one("sort") : DEFAULT_SORT,
           view: VIEWS.includes(one("view")) ? one("view") : "grid", page: Math.max(1, num("page")) };
}

/** Szűrőállapot -> URL. Lapozás minden szűrőváltozásnál az elejére ugrik. */
export function hrefFor(locale, params, over = {}) {
  const p = { ...params, page: 1, ...over };
  const sp = new URLSearchParams();
  if (p.q) sp.set("q", p.q);
  const cats = normalizeCats(p.cats || []);
  if (!same(cats, defaultCats(p.q))) {
    if (cats.length) cats.forEach((c) => sp.append("cat", c));
    else sp.set("cat", "all");
  }
  for (const pl of p.plats || []) sp.append("plat", pl);
  for (const b of p.brands || []) sp.append("brand", b);
  if (p.min > 0) sp.set("min", String(p.min));
  if (p.max > 0) sp.set("max", String(p.max));
  if (p.stock) sp.set("stock", "1");
  if (p.sort && p.sort !== DEFAULT_SORT) sp.set("sort", p.sort);
  if (p.view && p.view !== "grid") sp.set("view", p.view);
  if (p.page > 1) sp.set("page", String(p.page));
  const s = sp.toString();
  // a paraméter nélküli cím az üdvözlő oldal -> az alap katalógus (fegyverek) kifejezett kategóriát kap
  return `/${locale}?${s || "cat=weapons"}`;
}

/** Egy kategória-jelölés kivétele (chiphez): csoportból kivéve a többi elem marad. */
export function withoutCat(cats, token) {
  if (GROUP_IDS.includes(token)) return cats.filter((c) => c !== token);
  const g = groupOf(token);
  if (cats.includes(g)) return normalizeCats([...cats.filter((c) => c !== g), ...CAT_GROUPS.find((x) => x.id === g).leaves.filter((l) => l !== token)]);
  return cats.filter((c) => c !== token);
}
