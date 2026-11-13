// Jogi oldalak tartalma (HU + EN itt, DE/PL/CS a lib/locales/legal.js-ben). Az üzemeltetői adatok a lib/site.js OPERATOR objektumából jönnek.
import { ADS, COFFEE_URL, LEGAL_UPDATED, MAIL_PROVIDER, OPERATOR, SITE_NAME, SITE_URL } from "./site";
import { mailProvider } from "./mail";
import { legalX } from "./locales/legal";

export const DOCS = {
  terms: { hu: "aszf", en: "terms", de: "nutzungsbedingungen", pl: "regulamin", cs: "podminky-uziti" },
  privacy: { hu: "adatvedelem", en: "privacy", de: "datenschutz", pl: "polityka-prywatnosci", cs: "ochrana-osobnich-udaju" },
  imprint: { hu: "impresszum", en: "imprint", de: "impressum", pl: "nota-prawna", cs: "provozovatel" },
  shops: { hu: "boltoknak", en: "for-shops", de: "fuer-haendler", pl: "dla-sklepow", cs: "pro-obchody" },
};
export const DOC_TITLES = {
  hu: { terms: "Általános Szerződési Feltételek (ÁSZF)", privacy: "Adatvédelmi tájékoztató", imprint: "Impresszum", shops: "Boltoknak" },
  en: { terms: "Terms of Use", privacy: "Privacy Policy", imprint: "Imprint", shops: "For shops" },
  de: { terms: "Nutzungsbedingungen", privacy: "Datenschutzerklärung", imprint: "Impressum", shops: "Für Händler" },
  pl: { terms: "Regulamin serwisu", privacy: "Polityka prywatności", imprint: "Nota prawna", shops: "Dla sklepów" },
  cs: { terms: "Podmínky užití", privacy: "Zásady ochrany osobních údajů", imprint: "Provozovatel", shops: "Pro obchody" },
};
export const FOOTER_LABELS = {
  hu: { terms: "ÁSZF", privacy: "Adatvédelem", imprint: "Impresszum", shops: "Boltoknak" },
  en: { terms: "Terms", privacy: "Privacy", imprint: "Imprint", shops: "For shops" },
  de: { terms: "Nutzungsbedingungen", privacy: "Datenschutz", imprint: "Impressum", shops: "Für Händler" },
  pl: { terms: "Regulamin", privacy: "Prywatność", imprint: "Nota prawna", shops: "Dla sklepów" },
  cs: { terms: "Podmínky užití", privacy: "Ochrana údajů", imprint: "Provozovatel", shops: "Pro obchody" },
};
const LANGS = Object.keys(DOC_TITLES);

/** Nyelvváltás: ugyanaz az oldal a másik nyelven (szűrők, termék, jogi oldal megmarad).
 *  „/hu?cat=rifle&brand=CYMA” -> „/en?cat=rifle&brand=CYMA”, „/hu/adatvedelem” -> „/de/datenschutz”.
 *  to: célnyelv (alapból hu <-> en). */
export function switchLocale(path, locale, to = locale === "hu" ? "en" : "hu") {
  const p = String(path || "");
  const ok = p === `/${locale}` || ["/", "?", "#"].some((c) => p.startsWith(`/${locale}${c}`));
  if (!ok) return `/${to}`;
  let rest = p.slice(locale.length + 1);
  const m = /^\/([^/?#]+)(.*)$/.exec(rest);
  if (m) {
    const doc = Object.keys(DOCS).find((k) => DOCS[k][locale] === m[1]);
    if (doc) rest = `/${DOCS[doc][to]}${m[2]}`;
  }
  return `/${to}${rest}`;
}

/** Jogi oldal azonosítója a címből (bármelyik nyelv címét felismeri). */
export function docFromSlug(slug) {
  return Object.keys(DOCS).find((k) => LANGS.some((l) => DOCS[k][l] === slug)) || null;
}

const O = OPERATOR;
const OP_LABELS = {
  hu: ["Név", "Cím", "Adószám"], en: ["Name", "Address", "Tax number"], de: ["Name", "Anschrift", "Steuernummer"],
  pl: ["Imię i nazwisko / nazwa", "Adres", "Numer podatkowy"], cs: ["Jméno / název", "Adresa", "Daňové číslo"],
};
const operatorLines = (L) => {
  const [name, addr, tax] = OP_LABELS[L];
  return [
    `${name}: ${O.name}`,
    ...(O.address ? [`${addr}: ${O.address}`] : []),
    `E-mail: ${O.email}`,
    ...(O.taxNumber ? [`${tax}: ${O.taxNumber}`] : []),
    ...(O.registry ? [O.registry] : []),
  ];
};
const ADS_ON = Boolean(ADS.client);
const W = {   // szolgáltatók leírásának nyelvi elemei
  ireland: { hu: "Írország", en: "Ireland", de: "Irland", pl: "Irlandia", cs: "Irsko" },
  adsense: { hu: "hirdetések: Google AdSense", en: "advertising: Google AdSense", de: "Werbung: Google AdSense",
             pl: "reklamy: Google AdSense", cs: "reklama: Google AdSense" },
  mails: { hu: "értesítő e-mailek küldése", en: "sending alert emails", de: "Versand der Benachrichtigungs-E-Mails",
           pl: "wysyłka e-maili z powiadomieniami", cs: "odesílání e-mailů s upozorněními" },
  paris: { hu: "Párizs, Franciaország", en: "Paris, France", de: "Paris, Frankreich", pl: "Paryż, Francja", cs: "Paříž, Francie" },
  hosting: { hu: "weboldal tárhely, adatbázis, domain és DNS", en: "website hosting, database, domain and DNS",
             de: "Webhosting, Datenbank, Domain und DNS", pl: "hosting strony, baza danych, domena i DNS",
             cs: "hosting webu, databáze, doména a DNS" },
};
const google = (L) => `Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, ${W.ireland[L]} – policies.google.com (${W.adsense[L]})`;
// a ténylegesen beállított szolgáltató (Worker-titok: BREVO_API_KEY / RESEND_API_KEY), ennek hiányában a site.js értéke
const provider = () => mailProvider() || MAIL_PROVIDER;
const MAILERS = {
  resend: (L) => `Resend, Inc., 2261 Market Street #5039, San Francisco, CA 94114, USA – resend.com (${W.mails[L]})`,
  brevo: (L) => `Sendinblue SAS (Brevo), 17 rue Salneuve, 75017 ${W.paris[L]} – brevo.com (${W.mails[L]})`,
};
const hosts = (L) => [
  `Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA – cloudflare.com (${W.hosting[L]})`,
  ...(ADS_ON ? [google(L)] : []),
  ...(MAILERS[provider()] ? [MAILERS[provider()](L)] : []),
];

const usNote = (L) => {
  const US = ["Cloudflare", ...(ADS_ON ? ["Google"] : []), ...(provider() === "resend" ? ["Resend"] : [])];
  const one = US.length === 1;
  const list = US.slice(0, -1).join(", "), last = US[US.length - 1];
  return {
    hu: one ? `A ${US[0]} amerikai cég;` : `A ${list} és a ${last} amerikai (illetve amerikai anyavállalatú) cégek;`,
    en: one ? `${US[0]} is a US company;` : `${list} and ${last} are US companies or have US parents;`,
    de: one ? `${US[0]} ist ein US-Unternehmen;` : `${list} und ${last} sind US-Unternehmen bzw. haben eine US-Muttergesellschaft;`,
    pl: one ? `${US[0]} jest firmą amerykańską;` : `${list} i ${last} są firmami amerykańskimi (lub mają amerykańską spółkę dominującą);`,
    cs: one ? `${US[0]} je americká společnost;` : `${list} a ${last} jsou americké společnosti (nebo mají americkou mateřskou společnost);`,
  }[L];
};
const US_BASIS = {
  hu: " az adattovábbítás az EU–USA adatvédelmi keretrendszer, illetve általános szerződési feltételek alapján történik.",
  en: " transfers rely on the EU–US Data Privacy Framework or standard contractual clauses.",
  de: " die Übermittlung erfolgt auf Grundlage des EU-US Data Privacy Framework bzw. von Standardvertragsklauseln.",
  pl: " przekazywanie danych odbywa się na podstawie ram ochrony danych UE–USA (EU–US Data Privacy Framework) lub standardowych klauzul umownych.",
  cs: " předávání údajů probíhá na základě rámce pro ochranu osobních údajů mezi EU a USA (EU–US Data Privacy Framework) nebo standardních smluvních doložek.",
};

// Ár- és készletfigyelő (e-mail értesítő)
const alertsSectionHuEn = (hu) => [{
  h: hu ? "Ár- és készletértesítő (e-mail)" : "Price and stock alerts (email)",
  list: hu ? [
    "Ha a termékoldalon értesítést kérsz, ezeket kezeljük: e-mail cím, a termék, az értesítés típusa (újra raktáron / célár), a célár és pénzneme, a kérés, a megerősítés és a kiküldés időpontja, valamint az IP-címed egyirányú, rövidített lenyomata (hash) a visszaélések (tömeges feliratkoztatás) kiszűrésére.",
    "Cél: a kért értesítés elküldése. Jogalap: hozzájárulás (GDPR 6. cikk (1) a)), amelyet a megerősítő e-mailben lévő linkre kattintva adsz meg (dupla megerősítés). Megerősítés nélkül semmilyen levelet nem küldünk.",
    "Hozzájárulásodat bármikor visszavonhatod a levelekben lévő leiratkozó linkkel (egy értesítésről vagy az összesről), vagy a fenti e-mail címen.",
    "Megőrzés: a meg nem erősített kérést 7 nap után, a teljesült (kiküldött) értesítést 30 nap után, minden más értesítést legkésőbb 1 év után automatikusan töröljük.",
    "Az adatokat nem adjuk el, hirdetésre és hírlevélre nem használjuk; csak a kért értesítést küldjük el. A leveleket az alább felsorolt e-mail szolgáltató kézbesíti.",
  ] : [
    "If you request an alert on a product page, we process: your email address, the product, the alert type (back in stock / target price), the target price and its currency, the time of the request, the confirmation and the sending, and a one-way, shortened hash of your IP address to prevent abuse (mass sign-ups).",
    "Purpose: sending the alert you requested. Legal basis: consent (GDPR Art. 6(1)(a)), given by clicking the link in the confirmation email (double opt-in). Without confirmation we send no email at all.",
    "You can withdraw your consent at any time via the unsubscribe link in our emails (for one alert or for all), or at the email address above.",
    "Retention: unconfirmed requests are deleted after 7 days, fulfilled (sent) alerts after 30 days, and every other alert after 1 year at the latest, automatically.",
    "We do not sell the data and do not use it for advertising or newsletters; we only send the alert you asked for. Emails are delivered by the email provider listed below.",
  ],
}];

// Hirdetés és támogatás: csak akkor kerül a tájékoztatóba, ha be van kapcsolva (lib/site.js)
const adsSectionHuEn = (hu) => !ADS_ON ? [] : [{
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
const coffeeSectionHuEn = (hu) => !COFFEE_URL ? [] : [{
  h: hu ? "Támogatás („Hívj meg egy kávéra”)" : "Support (“Buy me a coffee”)",
  p: [hu
    ? `Az oldal alján lévő link egy külső támogatói oldalra (${new URL(COFFEE_URL).hostname}) visz. A támogatás önkéntes; a fizetést és az ehhez szükséges adatokat az a szolgáltató kezeli a saját adatvédelmi szabályai szerint. Tőle a támogató megadott nevét és üzenetét kaphatjuk meg.`
    : `The link at the bottom of the page leads to an external support page (${new URL(COFFEE_URL).hostname}). Support is voluntary; payment and the related data are handled by that provider under its own privacy policy. We may receive the supporter's chosen name and message.`],
}];

const alertsSection = (L) => alertsSectionHuEn(L === "hu");
const adsSection = (L) => adsSectionHuEn(L === "hu");
const coffeeSection = (L) => coffeeSectionHuEn(L === "hu");
// a német, lengyel és cseh változat ugyanezekből az építőkockákból (lib/locales/legal.js)
const H = () => ({ operatorLines, hosts, usNote, US_BASIS, ADS_ON, COFFEE_URL, SITE_NAME, SITE_URL, LEGAL_UPDATED, O });

// Egy dokumentum: [{ h: "Cím", p: ["bekezdés", ...], list: ["pont", ...] }]
const buildContent = () => ({
  ...legalX(H()),
  hu: {
    terms: [
      { p: [`Hatályos: ${LEGAL_UPDATED}. Ez a dokumentum a(z) ${SITE_NAME} (${SITE_URL}) weboldal használatának feltételeit tartalmazza. Az oldal használatával a felhasználó elfogadja ezeket a feltételeket.`] },
      { h: "1. Az üzemeltető", list: operatorLines("hu") },
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
      { h: "1. Az adatkezelő", list: operatorLines("hu") },
      { h: "2. Röviden", list: [
        "Az oldalon nincs regisztráció. Személyes adatot (e-mail címet) csak akkor kérünk, ha ár- vagy készletértesítőt kérsz.",
        ADS_ON ? "Analitikai sütit nem használunk. Hirdetési sütit csak a Google hirdetései használhatnak, és csak a hozzájárulásoddal (lásd alább)." : "Nem használunk analitikai, követő vagy hirdetési sütit.",
        ADS_ON ? "Saját sütink egyetlen van: a választott pénznem megjegyzésére." : "Egyetlen sütit használunk: a választott pénznem megjegyzésére.",
      ] },
      { h: "3. Milyen adatokat kezelünk", list: [
        "Technikai naplóadatok: az oldal megnyitásakor a tárhelyszolgáltató (Cloudflare) szervere automatikusan rögzíti az IP-címet, a böngésző típusát, a kért oldalt és az időpontot. Cél: az oldal biztonságos működése, hibakeresés, visszaélések kiszűrése. Jogalap: jogos érdek (GDPR 6. cikk (1) f)). Megőrzés: a tárhelyszolgáltató naplózási ideje szerint, legfeljebb néhány hét.",
        "Pénznem-süti („cur”): a felhasználó által választott pénznemet (pl. HUF, EUR) tárolja, 1 évig. Csak a kért funkcióhoz szükséges, személyes adatot nem tartalmaz, ezért nem igényel hozzájárulást.",
        "Kimenő linkek: a „Megnézem a boltban” gomb a /go/… címen keresztül irányít a boltba. Ennek során személyes adatot nem rögzítünk. A bolt oldalán a bolt saját adatkezelése érvényes.",
        "Kapcsolatfelvétel: ha e-mailt írsz nekünk, a nevedet, e-mail címedet és az üzenetet a megkeresés megválaszolásához használjuk, és az ügy lezárása után legfeljebb 1 évig őrizzük. Jogalap: jogos érdek.",
      ] },
      ...alertsSection("hu"),
      ...adsSection("hu"),
      ...coffeeSection("hu"),
      { h: "4. Adatfeldolgozók és szolgáltatók", list: hosts("hu") },
      { p: [usNote("hu") + US_BASIS.hu] },
      { h: "5. Jogaid", p: [
        "Kérheted a rólad kezelt adatokhoz való hozzáférést, azok helyesbítését, törlését, kezelésük korlátozását, és tiltakozhatsz a jogos érdeken alapuló adatkezelés ellen. Kérésedet a fenti e-mail címre küldd; 30 napon belül válaszolunk.",
        "Panasszal fordulhatsz a Nemzeti Adatvédelmi és Információszabadság Hatósághoz (NAIH): 1055 Budapest, Falk Miksa utca 9–11., ugyfelszolgalat@naih.hu, www.naih.hu, vagy bírósághoz.",
      ] },
      { h: "6. Változások", p: ["A tájékoztatót módosíthatjuk; az aktuális változat mindig ezen az oldalon érhető el."] },
    ],
    imprint: [
      { h: "Üzemeltető", list: operatorLines("hu") },
      { h: "Tárhelyszolgáltatók", list: hosts("hu") },
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
      { h: "1. Operator", list: operatorLines("en") },
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
      { h: "1. Controller", list: operatorLines("en") },
      { h: "2. In short", list: [
        "There is no registration. We only ask for personal data (an email address) if you request a price or stock alert.",
        ADS_ON ? "We use no analytics cookies. Advertising cookies may only be set by Google's ads, and only with your consent (see below)." : "We use no analytics, tracking or advertising cookies.",
        ADS_ON ? "Our own site sets a single cookie, to remember your chosen currency." : "We use a single cookie to remember your chosen currency.",
      ] },
      { h: "3. What we process", list: [
        "Technical logs: when you open a page, the hosting provider (Cloudflare) automatically logs the IP address, browser type, requested page and time. Purpose: security, troubleshooting, abuse prevention. Legal basis: legitimate interest (GDPR Art. 6(1)(f)). Retention: according to the host's log retention, at most a few weeks.",
        "Currency cookie (“cur”): stores the currency you chose (e.g. EUR, HUF) for 1 year. It is strictly needed for the feature you requested and contains no personal data, so no consent is required.",
        "Outbound links: the “View in shop” button redirects via /go/…; we do not record personal data. On the shop's site, the shop's own privacy policy applies.",
        "Contact: if you e-mail us, we use your name, e-mail address and message to reply and keep them for up to 1 year after the matter is closed. Legal basis: legitimate interest.",
      ] },
      ...alertsSection("en"),
      ...adsSection("en"),
      ...coffeeSection("en"),
      { h: "4. Processors and providers", list: hosts("en") },
      { p: [usNote("en") + US_BASIS.en] },
      { h: "5. Your rights", p: [
        "You may request access to, rectification or erasure of your data, restriction of processing, and object to processing based on legitimate interest. Send requests to the e-mail above; we reply within 30 days.",
        "You may lodge a complaint with the Hungarian data protection authority (NAIH, 1055 Budapest, Falk Miksa utca 9–11, www.naih.hu) or the authority of your country of residence.",
      ] },
      { h: "6. Changes", p: ["We may update this notice; the current version is always available on this page."] },
    ],
    imprint: [
      { h: "Operator", list: operatorLines("en") },
      { h: "Hosting providers", list: hosts("en") },
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
});

export function legalContent(locale, doc) {
  return (buildContent()[locale] || buildContent().en)[doc];
}
