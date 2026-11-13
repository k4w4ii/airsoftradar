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

// Kerekített darabszám a főoldalon („30 000+”): a Google a szöveget hetekig gyorsítótárazza, a pontos szám hamar elavulna,
// a lefelé kerekített „+” viszont igaz marad, ahogy a katalógus nő.
export const roundDown = (n) => (n >= 10000 ? Math.floor(n / 1000) * 1000 : n >= 1000 ? Math.floor(n / 100) * 100 : n);

const DICT = {
  hu: {
    title: "AirsoftHunter – airsoft árösszehasonlító",
    description: "Airsoft árösszehasonlító: replikák, alkatrészek és kiegészítők árai és készlete európai airsoft boltokból, minden éjjel frissítve. Vadászd le a legjobb árat!",
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
    welcomeSub: (n, s) => `${roundDown(n).toLocaleString("hu-HU")}+ termék ${s} európai boltból összehasonlítva, minden éjjel frissítve.`,
    browseCats: "Böngéssz kategóriák szerint",
    bestDeals: "Legnagyobb árkülönbségek",
    bestDealsNote: "Ugyanaz a termék ennyivel olcsóbb a legolcsóbb boltban, mint a legdrágábban.",
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
    offersIntro: (n) => `${n} boltban, a legolcsóbb elöl, az elfogyottak a lista végén. A sáv hossza az árral arányos.`,
    goToShop: "Megnézem a boltban",
    oddOffers: (n) => `Eltérő ár (${n})`,
    oddOffersNote: "Ezek az árak nagyon eltérnek a többi bolttól: valószínűleg alkatrész, tartozék vagy átépített (custom) változat. A legjobb árba nem számítanak bele.",
    original: "Bolti ár",
    history: "Ártörténet",
    historyEmpty: "Az árelőzmény a következő napokban épül fel: minden éjjel új adatpont kerül ide.",
    historyNote: "A legolcsóbb raktáron lévő EU-s ajánlat naponta (a nagyon eltérő árú ajánlatok nélkül).",
    range: (d) => `${d} nap`,
    low30: "30 napos legalacsonyabb ár",
    avg30: "30 napos átlag",
    verdict: {
      low: "Most van a legalacsonyabb áron az elmúlt 30 napban.",
      below: (p) => `${p}%-kal a 30 napos átlag alatt: valódi akciónak tűnik.`,
      near: "Az ára nagyjából a 30 napos átlagnak felel meg.",
      above: (p) => `${p}%-kal drágább a 30 napos átlagnál: érdemes lehet várni.`,
    },
    alertTitle: "Értesítés e-mailben",
    alertStock: "Szólj, ha újra raktáron lesz bármelyik EU-s boltban",
    alertPrice: "Szólj, ha az ára ez alá esik:",
    alertEmail: "E-mail cím",
    alertSubmit: "Kérem az értesítést",
    alertNote: "Regisztráció nélkül. Megerősítő e-mailt küldünk, és egy kattintással leiratkozhatsz.",
    alertPrivacy: "Adatvédelem",
    alertMsg: {
      sent: "Elküldtük a megerősítő e-mailt: kattints a benne lévő linkre (nézd meg a spam mappát is).",
      ok: "Megerősítve! Szólunk, amint teljesül a feltétel.",
      stopped: "Leiratkoztál erről az értesítésről.",
      stoppedAll: "Minden értesítésedet töröltük.",
      bad: "Hibás adat: ellenőrizd az e-mail címet és a célárat.",
      limit: "Túl sok kérés. Próbáld újra később.",
      off: "Az értesítő jelenleg nem elérhető.",
      expired: "Ez a link már nem érvényes.",
    },
    collectionTitle: (brand, cat) => `${brand} ${cat ? cat.toLowerCase() : "termékek"} – árak és készlet`,
    collectionIntro: (n, inStock, shops, low) =>
      `${n} termék, ebből ${inStock} raktáron, ${shops} európai boltból összehasonlítva. ${low ? `A legolcsóbb most ${low}-tól.` : ""} Az árak minden éjjel frissülnek.`,
    relatedBrand: (brand, cat) => `Összes ${brand} ${cat ? cat.toLowerCase() : "termék"}`,
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
    description: "Airsoft price comparison: prices and stock of replicas, parts and gear from European airsoft shops, updated every night. Hunt down the best price!",
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
    welcomeSub: (n, s) => `${roundDown(n).toLocaleString("en-GB")}+ products compared across ${s} European shops, updated every night.`,
    browseCats: "Browse by category",
    bestDeals: "Biggest price gaps",
    bestDealsNote: "The item is this much cheaper at the cheapest shop than at the most expensive one.",
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
    offersIntro: (n) => `${n} shops, cheapest first, out-of-stock offers last. Bar length is proportional to price.`,
    goToShop: "View in shop",
    oddOffers: (n) => `Unusual price (${n})`,
    oddOffersNote: "These prices differ greatly from the other shops: most likely a part, an accessory or a custom build. They are not counted in the best price.",
    original: "Shop price",
    history: "Price history",
    historyEmpty: "Price history builds up over the next days: a new data point is added every night.",
    historyNote: "The cheapest in-stock EU offer per day (offers with very different prices excluded).",
    range: (d) => `${d} days`,
    low30: "Lowest price in 30 days",
    avg30: "30-day average",
    verdict: {
      low: "This is the lowest price of the last 30 days.",
      below: (p) => `${p}% below the 30-day average: looks like a real deal.`,
      near: "The price is about the 30-day average.",
      above: (p) => `${p}% above the 30-day average: it may be worth waiting.`,
    },
    alertTitle: "Email alert",
    alertStock: "Tell me when it is back in stock in any EU shop",
    alertPrice: "Tell me when the price drops below:",
    alertEmail: "Email address",
    alertSubmit: "Notify me",
    alertNote: "No registration. We send a confirmation email, and you can unsubscribe with one click.",
    alertPrivacy: "Privacy",
    alertMsg: {
      sent: "We sent you a confirmation email: click the link in it (check your spam folder too).",
      ok: "Confirmed! We will let you know as soon as the condition is met.",
      stopped: "You unsubscribed from this alert.",
      stoppedAll: "All your alerts have been deleted.",
      bad: "Invalid data: check the email address and the target price.",
      limit: "Too many requests. Please try again later.",
      off: "Alerts are not available right now.",
      expired: "This link is no longer valid.",
    },
    collectionTitle: (brand, cat) => `${brand} ${cat ? cat.toLowerCase() : "products"} – prices and stock`,
    collectionIntro: (n, inStock, shops, low) =>
      `${n} products, ${inStock} in stock, compared across ${shops} European shops. ${low ? `Cheapest right now from ${low}.` : ""} Prices are updated every night.`,
    relatedBrand: (brand, cat) => `All ${brand} ${cat ? cat.toLowerCase() : "products"}`,
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
