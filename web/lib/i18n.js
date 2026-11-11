export const LOCALES = ["hu", "en"];
export const CURRENCIES = ["HUF", "EUR", "PLN", "CZK", "GBP"];
export const DEFAULT_CURRENCY = { hu: "HUF", en: "EUR" };

// Árszűrő sávhatárai a választott pénznemben (kerek értékek); a lekérdezés HUF-ra váltja
export const PRICE_EDGES = {
  HUF: [30000, 60000, 100000, 200000],
  EUR: [75, 150, 250, 500],
  PLN: [300, 600, 1000, 2000],
  CZK: [2000, 4000, 6500, 13000],
  GBP: [65, 130, 220, 440],
};
export { CAT_GROUPS, LEAVES, PLATFORMS } from "./catalog";
export const WEAPON_CATS = ["rifle", "pistol", "smg", "sniper", "lmg", "shotgun", "grenade"];

export function isLocale(x) {
  return LOCALES.includes(x);
}

const DICT = {
  hu: {
    title: "AirsoftHunter – airsoft árösszehasonlító",
    description: "Airsoft replikák és kiegészítők árai európai boltokból, naponta frissítve. Vadászd le a legjobb árat.",
    searchPlaceholder: "Keresés: típus, gyártó vagy kód (pl. CM.522, Specna, EVOLT)",
    search: "Keresés",
    manufacturer: "Gyártó",
    allManufacturers: "Minden gyártó",
    inStockOnly: "Csak raktáron",
    sort: "Rendezés",
    sorts: { discount: "Kedvezmény szerint", popular: "Összes találat", price: "Ár szerint növekvő", price_desc: "Ár szerint csökkenő", name: "Név szerint" },
    view: "Nézet",
    views: { grid: "Csempe", list: "Lista" },
    allResultsFor: "Összes találat: „{q}”",
    welcomeTitle: "Vadászd le a legjobb airsoft árat",
    welcomeSub: (n, s) => `${n.toLocaleString("hu-HU")} termék ${s} európai boltból összehasonlítva, minden éjjel frissítve.`,
    browseCats: "Böngéssz kategóriák szerint",
    bestDeals: "Legnagyobb árkülönbségek",
    bestDealsNote: "Ugyanaz a fegyver, ennyivel olcsóbb a legjobb boltban, mint a legdrágábban.",
    seeAll: "Összes megtekintése",
    topBrands: "Népszerű gyártók",
    items: (n) => `${n} termék`,
    apply: "Szűrés",
    shops: (n) => `${n} bolt`,
    bestPrice: "Legjobb ár",
    from: "már",
    save: (p) => `${p}%-kal olcsóbb, mint a legdrágább bolt`,
    saveUpTo: (amount, p) => `Akár ${amount} megtakarítás (${p}%)`,
    saveUpToNote: "a legolcsóbb raktáron lévő ajánlat a legdrágább raktáron lévőhöz képest",
    noResults: "Nincs találat. Próbálj rövidebb keresést, vagy töröld a szűrőket.",
    clearFilters: "Szűrők törlése",
    results: (n) => `${n} termék`,
    prev: "Előző",
    next: "Következő",
    page: (a, b) => `${a}. oldal / ${b}`,
    stock: { in_stock: "Raktáron", out_of_stock: "Elfogyott", preorder: "Előrendelhető", unknown: "Készlet ismeretlen" },
    offers: "Ajánlatok",
    offersIntro: (n) => `${n} boltban, a legolcsóbb elöl. A sáv hossza az árral arányos.`,
    goToShop: "Megnézem a boltban",
    oddOffers: (n) => `Eltérő ár (${n})`,
    oddOffersNote: "Ezek az árak nagyon eltérnek a többi bolttól: valószínűleg alkatrész, tartozék vagy átépített (custom) változat. A legjobb árba nem számítanak bele.",
    original: "Bolti ár",
    history: "Legalacsonyabb ár naponta",
    historyEmpty: "Az árelőzmény a következő napokban épül fel: minden éjjel új adatpont kerül ide.",
    updated: "Frissítve",
    checked: "Ellenőrizve",
    back: "Vissza a listához",
    footer: "Az árak tájékoztató jellegűek, szállítási költség nélkül, a bolt pénznemében mért ár napi MNB-árfolyamon átszámítva. Vásárlás előtt mindig ellenőrizd a bolt oldalán.",
    otherLang: "English",
    currency: "Pénznem",
    notFound: "Ilyen termék nincs (vagy már egyik boltban sem kapható).",
    filters: "Szűrés",
    showResults: (n) => `${n} találat mutatása`,
    category: "Típus",
    cats: {
      all: "Minden termék", weapons: "Airsoft fegyverek", rifle: "Gépkarabélyok", pistol: "Pisztolyok",
      smg: "Géppisztolyok", sniper: "Mesterlövész, DMR", lmg: "Géppuskák", shotgun: "Sörétes puskák",
      grenade: "Gránátok, gránátvetők",
      parts: "Alkatrészek", part_internal: "Gearbox, belső alkatrészek", part_hopup: "Hop-up, belső cső",
      part_motor: "Motor, elektronika", part_external: "Külső alkatrészek",
      acc: "Kiegészítők", acc_mag: "Tárak", acc_power: "Akkumulátor, töltő", acc_optics: "Optika, lámpa, lézer",
      acc_ammo: "BB, gáz", acc_protect: "Védőfelszerelés", acc_gear: "Taktikai felszerelés, tokok", other: "Egyéb",
      custom: "Egyedi és tuningolt fegyverek", custom_rifle: "Egyedi puskák, gépkarabélyok", custom_pistol: "Egyedi pisztolyok",
      custom_sniper: "Egyedi mesterlövész puskák",
    },
    platform: "Mihez jó (platform)",
    plats: {
      m4: "M4 / AR-15", ak: "AK", g36: "G36", mp5: "MP5", aug: "AUG", scar: "SCAR", m14: "M14", p90: "P90",
      vsr: "VSR-10", l96: "L96 / AWP", glock: "Glock", hicapa: "Hi-Capa / 1911", m9: "M9 / Beretta 92",
      gb_v2: "Gearbox V2", gb_v3: "Gearbox V3",
    },
    price: "Ár",
    under: (v) => `${v} alatt`,
    over: (v) => `${v} felett`,
    customRange: "Egyedi ártartomány",
    min: "Min",
    max: "Max",
    ok: "OK",
    brands: "Gyártó",
    moreBrands: (n) => `Összes gyártó (${n})`,
    morePlatforms: (n) => `Összes platform (${n})`,
    availability: "Elérhetőség",
    activeFilters: "Aktív szűrők",
    remove: (x) => `${x} szűrő törlése`,
  },
  en: {
    title: "AirsoftHunter – airsoft price comparison",
    description: "Airsoft replica and gear prices from European shops, updated daily. Hunt down the best price.",
    searchPlaceholder: "Search by model, brand or code (e.g. CM.522, Specna, EVOLT)",
    search: "Search",
    manufacturer: "Brand",
    allManufacturers: "All brands",
    inStockOnly: "In stock only",
    sort: "Sort",
    sorts: { discount: "Biggest discount", popular: "All results", price: "Price: low to high", price_desc: "Price: high to low", name: "Name" },
    view: "View",
    views: { grid: "Grid", list: "List" },
    allResultsFor: "All results for “{q}”",
    welcomeTitle: "Hunt down the best airsoft price",
    welcomeSub: (n, s) => `${n.toLocaleString("en-GB")} products compared across ${s} European shops, updated every night.`,
    browseCats: "Browse by category",
    bestDeals: "Biggest price gaps",
    bestDealsNote: "The same gun, this much cheaper at the best shop than at the most expensive one.",
    seeAll: "See all",
    topBrands: "Popular brands",
    items: (n) => (n === 1 ? "1 product" : `${n} products`),
    apply: "Apply",
    shops: (n) => (n === 1 ? "1 shop" : `${n} shops`),
    bestPrice: "Best price",
    from: "from",
    save: (p) => `${p}% cheaper than the most expensive shop`,
    saveUpTo: (amount, p) => `Save up to ${amount} (${p}%)`,
    saveUpToNote: "cheapest in-stock offer compared with the most expensive in-stock one",
    noResults: "No results. Try a shorter search or clear the filters.",
    clearFilters: "Clear filters",
    results: (n) => (n === 1 ? "1 product" : `${n} products`),
    prev: "Previous",
    next: "Next",
    page: (a, b) => `Page ${a} of ${b}`,
    stock: { in_stock: "In stock", out_of_stock: "Out of stock", preorder: "Pre-order", unknown: "Stock unknown" },
    offers: "Offers",
    offersIntro: (n) => `${n} shops, cheapest first. Bar length is proportional to price.`,
    goToShop: "View in shop",
    oddOffers: (n) => `Unusual price (${n})`,
    oddOffersNote: "These prices differ greatly from the other shops: most likely a part, an accessory or a custom build. They are not counted in the best price.",
    original: "Shop price",
    history: "Lowest price per day",
    historyEmpty: "Price history builds up over the next days: a new data point is added every night.",
    updated: "Updated",
    checked: "Checked",
    back: "Back to the list",
    footer: "Prices are indicative, excluding shipping, converted from the shop's currency at the daily Hungarian central bank (MNB) rate. Always check the shop's page before buying.",
    otherLang: "Magyar",
    currency: "Currency",
    notFound: "No such product (or no shop sells it any more).",
    filters: "Filters",
    showResults: (n) => `Show ${n} results`,
    category: "Type",
    cats: {
      all: "All products", weapons: "Airsoft guns", rifle: "Assault rifles", pistol: "Pistols",
      smg: "SMGs", sniper: "Sniper rifles, DMR", lmg: "Machine guns", shotgun: "Shotguns",
      grenade: "Grenades, launchers",
      parts: "Parts", part_internal: "Gearbox & internals", part_hopup: "Hop-up & inner barrels",
      part_motor: "Motors & electronics", part_external: "External parts",
      acc: "Accessories", acc_mag: "Magazines", acc_power: "Batteries & chargers", acc_optics: "Optics, lights, lasers",
      acc_ammo: "BBs & gas", acc_protect: "Protective gear", acc_gear: "Tactical gear & holsters", other: "Other",
      custom: "Custom & tuned guns", custom_rifle: "Custom rifles", custom_pistol: "Custom pistols", custom_sniper: "Custom sniper rifles",
    },
    platform: "Fits (platform)",
    plats: {
      m4: "M4 / AR-15", ak: "AK", g36: "G36", mp5: "MP5", aug: "AUG", scar: "SCAR", m14: "M14", p90: "P90",
      vsr: "VSR-10", l96: "L96 / AWP", glock: "Glock", hicapa: "Hi-Capa / 1911", m9: "M9 / Beretta 92",
      gb_v2: "Gearbox V2", gb_v3: "Gearbox V3",
    },
    price: "Price",
    under: (v) => `Under ${v}`,
    over: (v) => `Over ${v}`,
    customRange: "Custom range",
    min: "Min",
    max: "Max",
    ok: "OK",
    brands: "Brand",
    moreBrands: (n) => `All brands (${n})`,
    morePlatforms: (n) => `All platforms (${n})`,
    availability: "Availability",
    activeFilters: "Active filters",
    remove: (x) => `Remove ${x}`,
  },
};

export function t(locale) {
  return DICT[isLocale(locale) ? locale : "en"];
}

/** HUF-ban tárolt összeg megjelenítése a választott pénznemben. rates: { EUR: 385.4, ... } (HUF / egység) */
export function money(amountHuf, currency, rates, locale) {
  if (amountHuf == null) return "–";
  const rate = currency === "HUF" ? 1 : rates?.[currency];
  if (!rate) return money(amountHuf, "HUF", rates, locale);
  const value = Number(amountHuf) / rate;
  return new Intl.NumberFormat(locale === "hu" ? "hu-HU" : "en-GB", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "HUF" || currency === "CZK" ? 0 : 2,
    minimumFractionDigits: currency === "HUF" || currency === "CZK" ? 0 : 2,
  }).format(value);
}

/** Bolti ár a bolt saját pénznemében */
export function shopMoney(amount, currency, locale) {
  return new Intl.NumberFormat(locale === "hu" ? "hu-HU" : "en-GB", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "HUF" ? 0 : 2,
  }).format(Number(amount));
}

export function dateFmt(iso, locale) {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale === "hu" ? "hu-HU" : "en-GB", {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Budapest",
  }).format(new Date(iso));
}

/** Rövid dátum a kártyákra / ajánlatsorokra: „nov. 11. 03:40” */
export function shortDate(iso, locale) {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale === "hu" ? "hu-HU" : "en-GB", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Budapest",
  }).format(new Date(iso));
}

/** Már a választott pénznemben lévő érték kiírása (pl. ársáv-határ) */
export function plainMoney(value, currency, locale) {
  return new Intl.NumberFormat(locale === "hu" ? "hu-HU" : "en-GB", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(value);
}
