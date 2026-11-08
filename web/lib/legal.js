// Jogi oldalak tartalma (HU + EN). Az üzemeltetői adatok a lib/site.js OPERATOR objektumából jönnek.
import { ADS, COFFEE_URL, LEGAL_UPDATED, OPERATOR, SITE_NAME, SITE_URL } from "./site";

export const DOCS = {
  terms: { hu: "aszf", en: "terms" },
  privacy: { hu: "adatvedelem", en: "privacy" },
  imprint: { hu: "impresszum", en: "imprint" },
  shops: { hu: "boltoknak", en: "for-shops" },
};
export const DOC_TITLES = {
  hu: { terms: "Általános Szerződési Feltételek (ÁSZF)", privacy: "Adatvédelmi tájékoztató", imprint: "Impresszum", shops: "Boltoknak" },
  en: { terms: "Terms of Use", privacy: "Privacy Policy", imprint: "Imprint", shops: "For shops" },
};
export const FOOTER_LABELS = {
  hu: { terms: "ÁSZF", privacy: "Adatvédelem", imprint: "Impresszum", shops: "Boltoknak" },
  en: { terms: "Terms", privacy: "Privacy", imprint: "Imprint", shops: "For shops" },
};

export function docFromSlug(slug) {
  return Object.keys(DOCS).find((k) => DOCS[k].hu === slug || DOCS[k].en === slug) || null;
}

const O = OPERATOR;
const operatorLines = (hu) => [
  `${hu ? "Név" : "Name"}: ${O.name}`,
  ...(O.address ? [`${hu ? "Cím" : "Address"}: ${O.address}`] : []),
  `E-mail: ${O.email}`,
  ...(O.taxNumber ? [`${hu ? "Adószám" : "Tax number"}: ${O.taxNumber}`] : []),
  ...(O.registry ? [O.registry] : []),
];
const ADS_ON = Boolean(ADS.client);
const google = (hu) => `Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, ${hu ? "Írország" : "Ireland"} – policies.google.com (${hu ? "hirdetések: Google AdSense" : "advertising: Google AdSense"})`;
const hosts = (hu) => [
  `Vercel Inc., 440 N Barranca Ave #4133, Covina, CA 91723, USA – privacy@vercel.com (${hu ? "weboldal tárhely" : "website hosting"})`,
  `Supabase Pte. Ltd., 970 Toa Payoh North #07-04, Singapore 318992 – supabase.com (${hu ? "adatbázis; az adatok az EU-ban, Frankfurtban vannak" : "database; data stored in the EU, Frankfurt"})`,
  `Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA – cloudflare.com (${hu ? "domain és DNS" : "domain and DNS"})`,
  ...(ADS_ON ? [google(hu)] : []),
];

// Hirdetés és támogatás: csak akkor kerül a tájékoztatóba, ha be van kapcsolva (lib/site.js)
const adsSection = (hu) => !ADS_ON ? [] : [{
  h: hu ? "Hirdetések (Google AdSense)" : "Advertising (Google AdSense)",
  list: hu ? [
    "Az oldal fenntartását hirdetések segítik, amelyeket a Google AdSense jelenít meg. Felugró ablakot és automatikus hirdetést nem használunk; a hirdetések „Hirdetés” felirattal, a lista és a termékoldal alján jelennek meg.",
    "Az EU-ban a Google hozzájárulás-kezelő ablaka (Google által hitelesített, IAB TCF szerinti) első látogatáskor megkérdezi, engedélyezed-e a hirdetési sütiket és a személyre szabott hirdetéseket. Hozzájárulás nélkül csak nem személyre szabott vagy korlátozott hirdetések jelennek meg. Jogalap: hozzájárulás (GDPR 6. cikk (1) a)); a döntésed bármikor módosíthatod az oldal alján megjelenő adatvédelmi beállításokkal.",
    "A Google a hirdetések kiszolgálásához sütiket és eszközazonosítókat használhat, és az adatokat az EU–USA adatvédelmi keretrendszer alapján az USA-ba továbbíthatja. Részletek: policies.google.com/technologies/ads; a személyre szabott hirdetések kikapcsolása: adssettings.google.com.",
  ] : [
    "Advertising, served by Google AdSense, helps keep the site running. We use no pop-ups and no automatic ads; ads are labelled “Advertisement” and shown at the bottom of lists and product pages.",
    "In the EU, Google's consent dialog (Google-certified, IAB TCF) asks on your first visit whether you allow advertising cookies and personalised ads. Without consent, only non-personalised or limited ads are shown. Legal basis: consent (GDPR Art. 6(1)(a)); you can change your choice at any time via the privacy settings link at the bottom of the page.",
    "Google may use cookies and device identifiers to serve ads and may transfer data to the US under the EU–US Data Privacy Framework. Details: policies.google.com/technologies/ads; opt out of personalised ads: adssettings.google.com.",
  ],
}];
const coffeeSection = (hu) => !COFFEE_URL ? [] : [{
  h: hu ? "Támogatás („Hívj meg egy kávéra”)" : "Support (“Buy me a coffee”)",
  p: [hu
    ? `Az oldal alján lévő link egy külső támogatói oldalra (${new URL(COFFEE_URL).hostname}) visz. A támogatás önkéntes; a fizetést és az ehhez szükséges adatokat az a szolgáltató kezeli a saját adatvédelmi szabályai szerint. Tőle a támogató megadott nevét és üzenetét kaphatjuk meg.`
    : `The link at the bottom of the page leads to an external support page (${new URL(COFFEE_URL).hostname}). Support is voluntary; payment and the related data are handled by that provider under its own privacy policy. We may receive the supporter's chosen name and message.`],
}];

// Egy dokumentum: [{ h: "Cím", p: ["bekezdés", ...], list: ["pont", ...] }]
const CONTENT = {
  hu: {
    terms: [
      { p: [`Hatályos: ${LEGAL_UPDATED}. Ez a dokumentum a(z) ${SITE_NAME} (${SITE_URL}) weboldal használatának feltételeit tartalmazza. Az oldal használatával a felhasználó elfogadja ezeket a feltételeket.`] },
      { h: "1. Az üzemeltető", list: operatorLines(true) },
      { h: "2. A szolgáltatás", p: [
        `A(z) ${SITE_NAME} ingyenes, tájékoztató jellegű ár- és készlet-összehasonlító oldal airsoft termékekhez. Az oldal nem webáruház: terméket nem értékesít, megrendelést nem fogad, fizetést nem kezel.`,
        "A vásárlás a felhasználó és a kiválasztott bolt között jön létre, a bolt saját feltételei szerint. Az oldal ebben a jogviszonyban nem vesz részt, a boltok teljesítéséért (szállítás, garancia, elállás, panaszkezelés) nem felel.",
      ] },
      { h: "3. Árak és adatok pontossága", list: [
        "Az árakat, készletinformációt és termékadatokat a boltok nyilvános oldalairól automatikusan, naponta gyűjtjük, ezért eltérhetnek a bolt aktuális adataitól.",
        "A feltüntetett árak nem tartalmazzák a szállítási költséget. A más pénznemben (pl. EUR, PLN) megadott bolti árakat a Magyar Nemzeti Bank napi árfolyamán számoljuk át a választott pénznemre; a bolt végösszege ettől eltérhet.",
        "A termékek összepárosítása automatikus; előfordulhat, hogy eltérő változatok (szín, kivitel) egy terméknél jelennek meg.",
        "Vásárlás előtt mindig a bolt oldalán szereplő adat az irányadó.",
      ] },
      { h: "4. Kimenő linkek és partnerprogramok", p: [
        "A „Megnézem a boltban” gomb a bolt oldalára visz. Egyes linkek partnerprogram (affiliate) linkek lehetnek: ha a felhasználó ezeken keresztül vásárol, az üzemeltető jutalékot kaphat. Ez a felhasználó által fizetett árat nem befolyásolja, és a találatok sorrendjét sem: a lista ár, boltszám vagy név szerint rendeződik.",
      ] },
      { h: "5. Airsoft termékekre vonatkozó figyelmeztetés", list: [
        "Az airsoft replikák vásárlását, birtoklását és szállítását országonként eltérő jogszabályok szabályozzák (például korhatár, teljesítménykorlát, szállítási tilalom). Ezek betartása a felhasználó felelőssége.",
        "Airsoft replikát kiskorú csak a helyi jogszabályok és a bolt feltételei szerint vásárolhat; számos bolt csak 18 év felett szolgál ki.",
        "Játék során tartsd be a Magyar Airsoft Szabályzat (MASZ) biztonsági előírásait, különösen a szemvédelemre vonatkozókat.",
      ] },
      { h: "6. Szellemi tulajdon", p: [
        "A termék- és márkanevek, logók a jogosultjaik tulajdonát képezik; feltüntetésük kizárólag a termék azonosítását szolgálja. A termékképek a boltok, illetve a gyártók tulajdonai, azokat az oldal a bolt ajánlatának bemutatására jeleníti meg.",
        `Az oldal saját tartalma (kialakítás, szövegek, összesített adatok) az üzemeltető engedélye nélkül nem másolható tömegesen, és automatizált eszközzel nem gyűjthető.`,
      ] },
      { h: "7. Felelősség korlátozása", p: [
        "Az üzemeltető törekszik az oldal folyamatos és hibamentes működésére, de ezt nem garantálja. Az oldal adatainak felhasználásából, az oldal elérhetetlenségéből vagy a boltokkal létrejött jogviszonyból eredő károkért az üzemeltető – a jogszabály által megengedett mértékben – nem felel.",
      ] },
      { h: "8. Boltok és jogosultak", p: [
        `Ha egy bolt nem szeretne szerepelni az oldalon, vagy hibás adatot észlel, a(z) ${O.email} címen kérheti a javítást vagy az eltávolítást. Részletek a „Boltoknak” oldalon.`,
      ] },
      { h: "9. Záró rendelkezések", p: [
        "Az üzemeltető jogosult a feltételeket egyoldalúan módosítani; a módosítás az oldalon történő közzététellel lép hatályba. A jelen feltételekre a magyar jog az irányadó. Kérdés esetén írj a fenti e-mail címre.",
      ] },
    ],
    privacy: [
      { p: [`Hatályos: ${LEGAL_UPDATED}. Ez a tájékoztató az Európai Unió általános adatvédelmi rendelete (GDPR, 2016/679/EU) alapján ismerteti, hogyan kezeljük a(z) ${SITE_NAME} látogatóinak adatait.`] },
      { h: "1. Az adatkezelő", list: operatorLines(true) },
      { h: "2. Röviden", list: [
        "Az oldalon nincs regisztráció, és nem kérünk be személyes adatot.",
        ADS_ON ? "Analitikai sütit nem használunk. Hirdetési sütit csak a Google hirdetései használhatnak, és csak a hozzájárulásoddal (lásd alább)." : "Nem használunk analitikai, követő vagy hirdetési sütit.",
        ADS_ON ? "Saját sütink egyetlen van: a választott pénznem megjegyzésére." : "Egyetlen sütit használunk: a választott pénznem megjegyzésére.",
      ] },
      { h: "3. Milyen adatokat kezelünk", list: [
        "Technikai naplóadatok: az oldal megnyitásakor a tárhelyszolgáltató (Vercel) szervere automatikusan rögzíti az IP-címet, a böngésző típusát, a kért oldalt és az időpontot. Cél: az oldal biztonságos működése, hibakeresés, visszaélések kiszűrése. Jogalap: jogos érdek (GDPR 6. cikk (1) f)). Megőrzés: a tárhelyszolgáltató naplózási ideje szerint, legfeljebb néhány hét.",
        "Pénznem-süti („cur”): a felhasználó által választott pénznemet (pl. HUF, EUR) tárolja, 1 évig. Csak a kért funkcióhoz szükséges, személyes adatot nem tartalmaz, ezért nem igényel hozzájárulást.",
        "Kimenő linkek: a „Megnézem a boltban” gomb a /go/… címen keresztül irányít a boltba. Ennek során személyes adatot nem rögzítünk. A bolt oldalán a bolt saját adatkezelése érvényes.",
        "Kapcsolatfelvétel: ha e-mailt írsz nekünk, a nevedet, e-mail címedet és az üzenetet a megkeresés megválaszolásához használjuk, és az ügy lezárása után legfeljebb 1 évig őrizzük. Jogalap: jogos érdek.",
      ] },
      ...adsSection(true),
      ...coffeeSection(true),
      { h: "4. Adatfeldolgozók és szolgáltatók", list: hosts(true) },
      { p: [(ADS_ON ? "A Vercel, a Cloudflare és a Google amerikai (illetve amerikai anyavállalatú) cégek;" : "A Vercel és a Cloudflare amerikai cégek;") + " az adattovábbítás az EU–USA adatvédelmi keretrendszer, illetve általános szerződési feltételek alapján történik."] },
      { h: "5. Jogaid", p: [
        "Kérheted a rólad kezelt adatokhoz való hozzáférést, azok helyesbítését, törlését, kezelésük korlátozását, és tiltakozhatsz a jogos érdeken alapuló adatkezelés ellen. Kérésedet a fenti e-mail címre küldd; 30 napon belül válaszolunk.",
        "Panasszal fordulhatsz a Nemzeti Adatvédelmi és Információszabadság Hatósághoz (NAIH): 1055 Budapest, Falk Miksa utca 9–11., ugyfelszolgalat@naih.hu, www.naih.hu, vagy bírósághoz.",
      ] },
      { h: "6. Változások", p: ["A tájékoztatót módosíthatjuk; az aktuális változat mindig ezen az oldalon érhető el."] },
    ],
    imprint: [
      { h: "Üzemeltető", list: operatorLines(true) },
      { h: "Tárhelyszolgáltatók", list: hosts(true) },
      { h: "Az oldalról", p: [
        `A(z) ${SITE_NAME} független airsoft ár-összehasonlító. Nem áll kapcsolatban az oldalon szereplő boltokkal és gyártókkal, kivéve, ha egy linknél partnerprogram működik (lásd ÁSZF 4. pont).`,
      ] },
    ],
    shops: [
      { p: [`A(z) ${SITE_NAME} naponta egyszer gyűjti a boltok nyilvános termékoldalairól a nevet, az árat, a pénznemet, a készletet, a márkát, a termékkódot és a kép címét, és minden ajánlatnál a bolt saját oldalára linkel.`] },
      { h: "Hogyan gyűjtünk", list: [
        "A robotunk neve: AirsoftHunterBot (részletek: /bot).",
        "Betartjuk a robots.txt-t, beleértve a Crawl-delay értéket.",
        "Boltonként egyszerre egy kérést küldünk, 2–3 másodperces szünetekkel, éjszaka.",
        "Csak a schema.org szerinti, nyilvános termékadatokat olvassuk.",
      ] },
      { h: "Javítás, eltávolítás, együttműködés", list: [
        `Hibás adat vagy eltávolítás kérése: ${O.email}`,
        "A robot letiltása: User-agent: AirsoftHunterBot / Disallow: / a robots.txt-ben.",
        "Termékfeed (XML/CSV) vagy partnerprogram esetén szívesen áttérünk arra: így pontosabb és frissebb lesz az adat, a te szervered pedig kevésbé terhelt.",
      ] },
    ],
  },
  en: {
    terms: [
      { p: [`Effective: ${LEGAL_UPDATED}. These terms govern the use of ${SITE_NAME} (${SITE_URL}). By using the site you accept these terms.`] },
      { h: "1. Operator", list: operatorLines(false) },
      { h: "2. The service", p: [
        `${SITE_NAME} is a free, informational price and stock comparison site for airsoft products. It is not a shop: it does not sell products, take orders or handle payments.`,
        "Any purchase is a contract between you and the selected shop under the shop's own terms. We are not a party to it and are not responsible for the shop's performance (delivery, warranty, returns, complaints).",
      ] },
      { h: "3. Prices and data accuracy", list: [
        "Prices, stock and product data are collected automatically once a day from the shops' public pages and may differ from the shop's current data.",
        "Prices exclude shipping. Prices in other currencies are converted at the daily rate of the Hungarian central bank (MNB); the shop's final total may differ.",
        "Products are matched automatically; variants (colour, finish) may appear under one product.",
        "The information on the shop's website always prevails.",
      ] },
      { h: "4. Outbound links and affiliate programmes", p: [
        "The “View in shop” button takes you to the shop. Some links may be affiliate links: if you buy through them, the operator may receive a commission. This does not change the price you pay or the order of results, which are sorted by price, number of shops or name.",
      ] },
      { h: "5. Airsoft notice", list: [
        "Buying, owning and shipping airsoft replicas is regulated differently in each country (age limits, power limits, shipping bans). Complying with them is your responsibility.",
        "Minors may only buy airsoft replicas as permitted by local law and the shop's terms; many shops only sell to customers aged 18 or over.",
        "When playing, follow your local safety rules, especially on eye protection.",
      ] },
      { h: "6. Intellectual property", p: [
        "Product and brand names and logos belong to their owners and are shown only to identify products. Product images belong to the shops or manufacturers and are shown to present the shop's offer.",
        "The site's own content (design, texts, aggregated data) may not be copied in bulk or collected by automated means without the operator's permission.",
      ] },
      { h: "7. Limitation of liability", p: [
        "We aim to keep the site available and accurate but do not guarantee it. To the extent permitted by law, the operator is not liable for damages arising from the use of the site's data, its unavailability, or contracts with shops.",
      ] },
      { h: "8. Shops and rights holders", p: [`Shops that do not wish to be listed, or that spot incorrect data, can request a correction or removal at ${O.email}. See the “For shops” page.`] },
      { h: "9. Final provisions", p: ["The operator may amend these terms; changes take effect when published on this page. These terms are governed by Hungarian law. Questions: write to the e-mail address above."] },
    ],
    privacy: [
      { p: [`Effective: ${LEGAL_UPDATED}. This notice explains, under the EU General Data Protection Regulation (GDPR, 2016/679), how ${SITE_NAME} handles visitor data.`] },
      { h: "1. Controller", list: operatorLines(false) },
      { h: "2. In short", list: [
        "There is no registration and we do not ask for personal data.",
        ADS_ON ? "We use no analytics cookies. Advertising cookies may only be set by Google's ads, and only with your consent (see below)." : "We use no analytics, tracking or advertising cookies.",
        ADS_ON ? "Our own site sets a single cookie, to remember your chosen currency." : "We use a single cookie to remember your chosen currency.",
      ] },
      { h: "3. What we process", list: [
        "Technical logs: when you open a page, the hosting provider (Vercel) automatically logs the IP address, browser type, requested page and time. Purpose: security, troubleshooting, abuse prevention. Legal basis: legitimate interest (GDPR Art. 6(1)(f)). Retention: according to the host's log retention, at most a few weeks.",
        "Currency cookie (“cur”): stores the currency you chose (e.g. EUR, HUF) for 1 year. It is strictly needed for the feature you requested and contains no personal data, so no consent is required.",
        "Outbound links: the “View in shop” button redirects via /go/…; we do not record personal data. On the shop's site, the shop's own privacy policy applies.",
        "Contact: if you e-mail us, we use your name, e-mail address and message to reply and keep them for up to 1 year after the matter is closed. Legal basis: legitimate interest.",
      ] },
      ...adsSection(false),
      ...coffeeSection(false),
      { h: "4. Processors and providers", list: hosts(false) },
      { p: [(ADS_ON ? "Vercel, Cloudflare and Google are US companies or have US parents;" : "Vercel and Cloudflare are US companies;") + " transfers rely on the EU–US Data Privacy Framework or standard contractual clauses."] },
      { h: "5. Your rights", p: [
        "You may request access to, rectification or erasure of your data, restriction of processing, and object to processing based on legitimate interest. Send requests to the e-mail above; we reply within 30 days.",
        "You may lodge a complaint with the Hungarian data protection authority (NAIH, 1055 Budapest, Falk Miksa utca 9–11, www.naih.hu) or the authority of your country of residence.",
      ] },
      { h: "6. Changes", p: ["We may update this notice; the current version is always available on this page."] },
    ],
    imprint: [
      { h: "Operator", list: operatorLines(false) },
      { h: "Hosting providers", list: hosts(false) },
      { h: "About", p: [`${SITE_NAME} is an independent airsoft price comparison site, not affiliated with the listed shops or manufacturers except where a link is part of an affiliate programme (see Terms, section 4).`] },
    ],
    shops: [
      { p: [`${SITE_NAME} collects, once a day, the name, price, currency, stock status, brand, product code and image URL from shops' public product pages, and every offer links to the shop's own page.`] },
      { h: "How we collect", list: [
        "Our crawler: AirsoftHunterBot (details: /bot).",
        "We respect robots.txt, including Crawl-delay.",
        "One request at a time per shop, 2–3 seconds apart, at night (CET).",
        "We only read public schema.org product data.",
      ] },
      { h: "Corrections, removal, partnership", list: [
        `Incorrect data or removal: ${O.email}`,
        "To block the crawler: User-agent: AirsoftHunterBot / Disallow: / in robots.txt.",
        "If you offer a product feed (XML/CSV) or an affiliate programme, we are happy to switch to it: more accurate, fresher data and less load on your server.",
      ] },
    ],
  },
};

export function legalContent(locale, doc) {
  return CONTENT[locale === "hu" ? "hu" : "en"][doc];
}
