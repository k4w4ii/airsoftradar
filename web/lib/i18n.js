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
export const WEAPON_CATS = ["rifle", "pistol", "smg", "sniper", "lmg", "shotgun", "grenade"];

export function isLocale(x) {
  return LOCALES.includes(x);
}

const DICT = {
  hu: {
    title: "AirsoftHunter – airsoft árösszehasonlító",
    description: "Airsoft replikák és kiegészítők árai európai boltokból, naponta frissítve. Vadászd le a legjobb árat.",
    tagline: (s) => `${s.products} replika ${s.shops} európai boltból, naponta frissítve`,
    searchPlaceholder: "Keresés: típus, gyártó vagy kód (pl. CM.522, Specna, EVOLT)",
    search: "Keresés",
    manufacturer: "Gyártó",
    allManufacturers: "Minden gyártó",
    inStockOnly: "Csak raktáron",
    sort: "Rendezés",
    sorts: { popular: "Legtöbb bolt", price: "Ár szerint növekvő", price_desc: "Ár szerint csökkenő", name: "Név szerint" },
    apply: "Szűrés",
    shops: (n) => `${n} bolt`,
    bestPrice: "Legjobb ár",
    from: "már",
    save: (p) => `${p}%-kal olcsóbb, mint a legdrágább bolt`,
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
    original: "Bolti ár",
    history: "Legalacsonyabb ár naponta",
    historyEmpty: "Az árelőzmény a következő napokban épül fel: minden éjjel új adatpont kerül ide.",
    updated: "Frissítve",
    back: "Vissza a listához",
    footer: "Az árak tájékoztató jellegűek, szállítási költség nélkül, a bolt pénznemében mért ár napi MNB-árfolyamon átszámítva. Vásárlás előtt mindig ellenőrizd a bolt oldalán.",
    otherLang: "English",
    currency: "Pénznem",
    notFound: "Ilyen termék nincs (vagy már egyik boltban sem kapható).",
    filters: "Szűrés",
    showResults: (n) => `${n} találat mutatása`,
    category: "Típus",
    cats: {
      all: "Minden termék", weapons: "Airsoft fegyverek", rifle: "Gépkarabélyok (AR, AK)", pistol: "Pisztolyok",
      smg: "Géppisztolyok", sniper: "Mesterlövész, DMR", lmg: "Géppuskák", shotgun: "Sörétes puskák",
      grenade: "Gránátok, gránátvetők", other: "Kiegészítők, egyéb",
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
    availability: "Elérhetőség",
    activeFilters: "Aktív szűrők",
    remove: (x) => `${x} szűrő törlése`,
  },
  en: {
    title: "AirsoftHunter – airsoft price comparison",
    description: "Airsoft replica and gear prices from European shops, updated daily. Hunt down the best price.",
    tagline: (s) => `${s.products} replicas from ${s.shops} European shops, updated daily`,
    searchPlaceholder: "Search by model, brand or code (e.g. CM.522, Specna, EVOLT)",
    search: "Search",
    manufacturer: "Brand",
    allManufacturers: "All brands",
    inStockOnly: "In stock only",
    sort: "Sort",
    sorts: { popular: "Most shops", price: "Price: low to high", price_desc: "Price: high to low", name: "Name" },
    apply: "Apply",
    shops: (n) => (n === 1 ? "1 shop" : `${n} shops`),
    bestPrice: "Best price",
    from: "from",
    save: (p) => `${p}% cheaper than the most expensive shop`,
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
    original: "Shop price",
    history: "Lowest price per day",
    historyEmpty: "Price history builds up over the next days: a new data point is added every night.",
    updated: "Updated",
    back: "Back to the list",
    footer: "Prices are indicative, excluding shipping, converted from the shop's currency at the daily Hungarian central bank (MNB) rate. Always check the shop's page before buying.",
    otherLang: "Magyar",
    currency: "Currency",
    notFound: "No such product (or no shop sells it any more).",
    filters: "Filters",
    showResults: (n) => `Show ${n} results`,
    category: "Type",
    cats: {
      all: "All products", weapons: "Airsoft guns", rifle: "Assault rifles (AR, AK)", pistol: "Pistols",
      smg: "SMGs", sniper: "Sniper rifles, DMR", lmg: "Machine guns", shotgun: "Shotguns",
      grenade: "Grenades, launchers", other: "Accessories, other",
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

/** Már a választott pénznemben lévő érték kiírása (pl. ársáv-határ) */
export function plainMoney(value, currency, locale) {
  return new Intl.NumberFormat(locale === "hu" ? "hu-HU" : "en-GB", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(value);
}
