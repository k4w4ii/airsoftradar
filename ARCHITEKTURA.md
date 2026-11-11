# AirsoftHunter – airsoft árkereső: architektúra és fejlesztési terv

## Stack
| Réteg | Választás |
|---|---|
| Frontend | Next.js 16 (App Router) + sima CSS, dark-first, **Cloudflare Workers** (OpenNext adapter) |
| Adatbázis | **Cloudflare D1** (SQLite), séma: `d1/schema.sql` |
| Scraper + párosító | **Python, csak stdlib** (urllib, regex, json) – nincs `pip install`; Playwright csak JS/Cloudflare-es boltokra |
| Ütemezés | GitHub Actions cron (`.github/workflows/daily-scrape.yml`) |
| Nyelv | HU + EN (`/hu`, `/en` útvonalak, hreflang) |

## Adatfolyam (naponta 02:17 UTC)
```
mnb_rates.py ─> run_shop.py × 20 bolt (párhuzamosan, max 6) ─> rematch.py ─> health_check.py
                 felderítés (sitemap / lapozás) -> JSON-LD -> offers upsert      (audit, párosítás, nevek,
                 -> matcher -> price_history (HUF + EUR) -> inaktiválás            summary.rebuild)
```
A scraper a D1-be a weboldal Workerének titkos végpontján (`/api/db`, Bearer token) ír.

## Európai kiterjesztés (0003 migráció)
- **Nyelv:** UI-szövegek Next.js-ben JSON szótárakkal (`web/lib/i18n.js`), külső i18n könyvtár nélkül; a `/` az `Accept-Language` alapján irányít (`next.config.mjs`). Kategóriák: `name_hu` / `name_en`. Terméknév: nyelvsemleges gyártói név; angol nyelvű bolt címe felülírja a magyart/csehet (`products.name_lang`).
- **Deviza:** belső bázis HUF (MNB, minden deviza). `v_offers` és `product_summary` HUF + EUR oszlopot ad; alapértelmezés `/hu` -> HUF, `/en` -> EUR; PLN/CZK/GBP stb. a frontend-en a `latest_rates`-ből (cookie-ban tárolt választás).
- **Szállítás:** `shops.ships_to` (ISO országkód-tömb) -> „csak az én országomba szállító boltok” szűrő. `product_summary.shop_countries` a boltok székhelye.

## Scraper modulok (`scraper/`)
| Fájl | Feladat |
|---|---|
| `fetcher.py` | robots.txt, hostonkénti 2–3 mp késleltetés, 429/5xx újrapróbálás, gzip |
| `crawl.py` | termék URL-ek sitemapből vagy kategória-lapozásból |
| `jsonld.py` | schema.org Product (JSON-LD, microdata) + OpenGraph tartalék |
| `matcher.py` | termékpárosítás (lásd lent) |
| `run_shop.py` | teljes futás egy boltra, `scrape_runs` napló |
| `rematch.py` | letöltés nélküli újrapárosítás + névegységesítés (Actions → rematch) |
| `probe.py` | új bolt felderítése: mit lát a scraper, milyen linkminták vannak |
| `mnb_rates.py` | MNB SOAP -> `exchange_rates` |
| `d1db.py` | D1-kliens (a `/api/db` végponton át; PostgREST-stílusú szűrők) |
| `classify.py`, `summary.py` | kategória/platform-besorolás; `product_summary` + kiugró árak újraépítése (csak a változások) |
| `dictionary.py`, `dict/` | ingyenes szótáras fordítás (cseh, lengyel, magyar, olasz, finn, holland, német → angol); a `names.clean_name` és a weboldal (`web/lib/dictionary.js` + `dictionary.json`) is ezt használja; `hu_words.lst`: magyar oldalon meghagyott szavak, `nem_forditando.lst`: átnézett márkák/angol szavak |
| `quality.py`, `javitasok.txt` | minőség-őr: a `summary` része; kézi javítások (kategória, ajánlat elrejtése), biztos automatikus javítások (túl olcsó / alkatrész nevű „fegyver”), ellenőrizendő lista (`minoseg.csv` artifact + futás-összesítő) |
| `health_check.py` | állapot-ellenőrzés: D1 + weboldal (Actions → health, és a napi futás vége) |
| `shops.json` | boltonkénti konfig (forrás, URL-minta, lapozás, extra fejlécek, `enabled`, `status`) |

## GitHub Actions (publikus repó)
- Publikus repó -> korlátlan ingyenes Actions perc.
- `keepalive.yml`: havonta automatikus commit, mert a GitHub 60 nap commit-inaktivitás után letiltja az ütemezett workflow-kat.
- Titok: `D1_API_TOKEN` (Secret), változó: `D1_API_URL` (a workers.dev cím + `/api/db`); forkból indított PR nem kapja meg őket.
- Workflow-k: `daily-scrape` (+ `refresh` és `health` job), `rematch`, `health`, `keepalive`; közös `concurrency` csoport (`airsofthunter-db`).

## Adatbázis-séma (`d1/schema.sql`)
2026-11-09-ig Supabase (Postgres, migrációk 0001–0013), azóta Cloudflare D1. A Postgres-logika (regex-besorolás, materializált nézet, triggerek, RPC) Pythonba került: `scraper/classify.py`, `scraper/summary.py`; a kereső a Workerben (`web/lib/data_d1.js`). Új bolt / gyártó: `INSERT` a D1 Console-ban (vagy a zipben kapott `d1/*.sql`).

## Boltok (20; csak EU, UK nélkül)
| Bolt | Ország | Forrás | Állapot |
|---|---|---|---|
| Gunfire | PL | 20 kategória JSON-LD lapozás (60/oldal): fegyverek, alkatrészek, kiegészítők, védő/taktikai | ✓ élesben |
| Taiwangun | PL | termék-sitemap (`/sitemap/products_sitemap/`), angol URL-ek | ✓ élesben (USD) |
| Evike Europe | FR | angol termék-sitemap (15 872 URL) | ✓ élesben |
| Powair6 | FR | sitemap (francia, CDATA) → minden termék, `/en/` | ✓ élesben |
| AirsoftPlaza | HU | sitemap | ✓ élesben |
| AirsoftCentrum | HU | sitemap, forgó ablak | ✓ élesben (microdata) |
| AirsoftPro | CZ | VirtueMart lapozás: fegyverek, tárak, BB/gáz, alkatrészek | ✓ élesben (microdata) |
| Combat-Zone | HU | – | ❌ letiltva (JS-lista) |
| Begadi | DE | sitemap, csak `airsoftwaffen` | ÚJ (2026-11-08) – ellenőrizendő |
| Airsoft Sports | DE | sitemap, általános minta | ÚJ – ellenőrizendő |
| AirsoftGuns.eu | CZ | sitemap, általános minta | ÚJ – ellenőrizendő |
| Airsoftmania | IT | – | ❌ letiltva (nincs sitemap, elutasítja a robotot) |
| Gunshot | IT | sitemap, általános minta | ÚJ – ellenőrizendő |
| VSGUN | ES | – | ❌ letiltva (bot-védelem) |
| Airsoft Legends | NL | sitemap, csak `/en/` | ÚJ – ellenőrizendő |
| Bunker501 | NL | sitemap, általános minta | ÚJ – ellenőrizendő |
| Phenix Airsoft | FR | – | ❌ letiltva 2026-11-10 (a GitHub-gépről 405, bot-védelem; feedet kérni) |
| Militaria.pl | PL | – | ❌ letiltva (nincs sitemap, JS-lista; később lapozós konfig) |
| Red Beret | PL | sitemap, általános minta | ÚJ – ellenőrizendő |
| Atom Airsoft | FI | Shopify sitemap `/products/` | ÚJ – ellenőrizendő |

Lefedettség (2026-11-08 óta): fegyverek + kiegészítők + alkatrészek + védő/taktikai felszerelés; **ruházat és lábbeli kizárva** (`scraper/filters.py`, URL-re letöltés előtt és címre). Boltonként 300 perc / 6000 termék naponta (forgó ablakkal a nagy katalógusok is körbeérnek), sitemapből max. 60 000 URL, a weboldal boltonként frissül. Párosítás: token-előszűrés (6000 termék/gyártó mellett is gyors). A workflow 6 boltot futtat párhuzamosan. Ismeretlen gyártójú termékek `pending` maradnak (nem jelennek meg).

Nagy boltok: ha több termék van, mint `max_products` (6000), naponta forgó ablak; inaktiválás csak `STALE_DAYS + ciklushossz` nap után.
Hibakeresés: `d1/allapot.sql` (összesítő), `d1/diagnozis.sql` (http kódok, példa URL-ek) – D1 Console.
Kinyerési sorrend: JSON-LD -> microdata (itemscope/itemprop) -> OpenGraph meta.
Időkorlát: boltonként 300 perc (`SCRAPE_BUDGET_MIN`, job-timeout 330) és alapból 6000 termék; csonka futás után nincs inaktiválás.
Állapot-lekérdezés: `d1/allapot.sql`, automatikus ellenőrzés: `scraper/health_check.py`.

## Márka
**AirsoftHunter** – „vadászd le a legjobb árat”. Logó: osztott szálkereszt (irányzék), sárgaréz középponttal (a találat = a legjobb ár). Domain: `www.airsofthunter.com` (az `airsofthunter.com` 308-cal ide irányít). Scraper User-Agent: `AirsoftHunterBot/1.0 (+https://www.airsofthunter.com/bot)`.

## Cloudflare-átállás (2026-11-09, kész)
- **1. lépés – weboldal:** `web/wrangler.jsonc` + `web/open-next.config.ts`; Workers Builds a GitHub-repóból (root `web`). Custom domain a Workeren, a csupasz domain Redirect Rule-lal a www-re; proxy + DDoS-védelem automatikus, Bot Fight Mode és rate limiting (100 kérés / 10 mp / IP) bekapcsolva.
- **2. lépés – adatbázis:** Supabase → D1 egyszeri migrációval; a Supabase és a Vercel megszüntetve, a kódból a Supabase-ág kivéve.

### D1 részletek
- `d1/schema.sql`: SQLite séma. A Postgres-logika (besorolás, kiugró árak, összesítő) Pythonban fut: `scraper/classify.py` (a 0010/0012 SQL-ből generálva) és `scraper/summary.py` (csak a megváltozott `product_summary` sorokat írja, sha1 „sig” alapján).
- Írás kívülről: `web/app/api/db/route.js`.
  - `POST {statements:[{sql,params}]}`, legfeljebb 100 utasítás, egy D1 batch = egy tranzakció.
  - Bearer `INGEST_TOKEN`, időzítés-független összehasonlítással. Token nélkül 404.
  - A scraper a workers.dev címet használja (a zóna botvédelme miatt).
- `scraper/d1db.py`: select / insert / upsert / update PostgREST-stílusú szűrőkkel (→ SQL), rowid-lapozás, 90 paraméteres IN-darabolás; `scraper/db.py: get_db()` ezt adja.
- `web/lib/data_d1.js`: a katalógus (találatok + minden szűrő darabszáma) egy 8 utasításos D1-batch-ben; `web/lib/data.js` csak továbbít.
- `scraper/d1db.py` a `D1_API_URL`-t kiegészíti (`https://`, `/api/db`), ha hiányos.
- Tesztek: `scraper/test_d1.py` (helyi sqlite3 a D1 helyett: szűrők, lapozás, teljes folyamat, állapot-ellenőrzés). A webes oldal bun:sqlite-tal tesztelve (katalógus, ajánlatok, előzmény, `/api/db`).

## Weboldal (`web/`, Next.js 16, Cloudflare Workers)
- Függőség csak `next`, `react`, `react-dom`; sima CSS (`app/globals.css`), JavaScript (nincs TS-típusellenőrzés, ami buildet törhetne).
- Adat: Cloudflare D1 binding (`DB`, `wrangler.jsonc`), `lib/data.js` → `lib/data_d1.js`. Titkos írási végpont: `app/api/db/route.js` (Worker-titok `INGEST_TOKEN`).
- Jogi oldalak (HU/EN, `app/[locale]/[doc]`, tartalom: `lib/legal.js`): ÁSZF `/hu/aszf` · `/en/terms`, adatvédelem `/hu/adatvedelem` · `/en/privacy`, impresszum `/hu/impresszum` · `/en/imprint`, boltoknak `/hu/boltoknak` · `/en/for-shops`. Üzemeltetői adatok egy helyen: `lib/site.js` → `OPERATOR` (kitöltendő). Lábléc: márka, felelősségkizárás, jogi linkek.
- Bevétel (alapból kikapcsolva, `lib/site.js` → `MONETIZE` vagy env `ADSENSE_CLIENT`, `ADSENSE_SLOT_LIST`, `ADSENSE_SLOT_PRODUCT`, `COFFEE_URL`): AdSense szkript + `google-adsense-account` meta csak kitöltött kódnál; `/ads.txt` route (különben 404); két kézi, „Hirdetés” feliratú egység (`components/AdSlot.jsx`, lista alja és termékoldal alja), kitöltetlen egység elrejtve (`:has([data-ad-status=unfilled])`); automatikus és átfedő hirdetések az AdSense-ben kikapcsolva; az EU-s hozzájárulást a Google CMP kezeli. Kávé-link a láblécben. Az adatvédelmi szöveg feltételesen bővül.
- SEO: `app/sitemap.js` (lista- és termékoldalak hu/en hreflang-gal, naponta), `app/robots.js` (csak a Google keresőrobotjai engedélyezettek, minden más robot – AI-tanítók, más keresők – tiltva; `/go/`, `/cur`, `/theme`, `/api/` a Google-nek is tiltva). Sitemap: `/sitemap.xml` index → `/sitemaps/static.xml`, `/sitemaps/p-N.xml` (10 000 termék / fájl), `metadataBase` = `SITE_URL` (`lib/site.js`).
- Útvonalak: `/` -> `/hu` vagy `/en` (Accept-Language, `next.config.mjs` redirect) · `/[locale]` paraméter nélkül **üdvözlő oldal** (kereső, kategória-csempék a legnépszerűbb termék képével, legnagyobb árkülönbségek, népszerű gyártók; `components/Welcome.jsx`), bármilyen katalógus-paraméterrel (`?cat=weapons` az alap) lista + szűrők · `/[locale]/p/[slug]` termékoldal · `/go/[id]` kimenő link (affiliate sablon) · `/cur` pénznem-süti.
- Táblák a weboldalnak: `product_summary` (a scraper építi: legjobb ár, max ár, `category`, `platforms` „,m4,ak,” formában, `search_code`), az ajánlatok és az ártörténet SQL-lel a `offers` / `price_history` táblából.
- Ütemezés: a Worker cron-triggere (`wrangler.jsonc` → `triggers.crons`, `web/custom-worker.js`) 02:17 UTC-kor a GitHub API-n át indítja a `daily-scrape`-et (`GH_TOKEN` Worker-titok); a GitHub-schedule 06:47 UTC-kor csak tartalék (a `gate` job kihagyja, ha 14 órán belül már indult).
- Rendrakás (`rematch.py: audit_kinds`): alkatrész a fegyver alatt / fegyver az alkatrész alatt (besoroló + árküszöb), egyedi változat a gyári alatt → leválasztás és újrapárosítás; a matcher (`same_kind` + `gun_kind`) nem engedi vissza. Kategóriák: `custom_rifle`, `custom_pistol`, `custom_sniper` (csoport: `custom`), ha a termék neve vagy ajánlatainak többsége egyedi/HPA/tuningolt/használt.
- Árkülönbség megjelenítése: „Akár X Ft megtakarítás (Y%)” – csak a raktáron lévő ajánlatok egymás közt (`max_price_huf` = a legdrágább raktáron lévő); ha sehol nincs raktáron, csak az utolsó legolcsóbb ár látszik, százalék nélkül (csempén, listában, termékoldalon), nem csak százalék.
- Kereső: gépelés közbeni javaslatok (`components/SearchBox.jsx` → `/api/suggest`: kategóriák, gyártók, 6 termék árral; 180 ms késleltetés, billentyűzettel kezelhető, JS nélkül sima űrlap).
- **Működés-szűrő** (`?pow=aeg|gbb|gas|co2|spring|hpa|aep`): `classify.powers()` a névből és a bolti címekből (alkatrésznél a „mihez jó”: „for GBB”, gearbox = AEG); `product_summary.powers` (a `summary` magától létrehozza az oszlopot). Az eltérő hajtású (AEG ≠ GBBR) és a Specna-sorozatú (CORE ≠ FLEX ≠ EDGE ≠ PRIME ≠ VAPOR) ajánlatok soha nem párosulnak (`filters.specs`: `power`, `line`).
- Rendezés: alap a **kedvezmény** (legolcsóbb vs. legdrágább bolt, %), továbbá „Összes találat” (legtöbb bolt), ár, név. Nézet: **csempe** (alap) vagy lista (`?view=list`).
- Besorolás árküszöbbel (`classify.py: _weapon_ok`): fegyverkategória csak a típusra jellemző minimális ár felett (pl. pisztoly 2500 Ft, puska 6000 Ft); ha csak modellnév szerepel (M4, AK, SCAR, 1911, SVD) fegyverszó nélkül, 15 000 Ft (pisztoly 8000 Ft) alatt alkatrész.
- Katalógus: **egy D1-batch** adja a találatokat és a szűrő-darabszámokat; minden szűrő darabszáma a többi szűrővel számol. Szűrők: típus-fa (`weapons` = minden fegyver; alapértelmezés kereséskor `all`), ársávok (pénznemenként kerek határok, `PRICE_EDGES`) + kétfogantyús csúszka + min/max, márkák (többes választás), raktáron. Mobilon CSS-only lenyitható panel; JS nélkül „Szűrés” gombbal működik.
- Kategóriák (0010): fegyverek (`rifle, pistol, smg, sniper, lmg, shotgun, grenade`), alkatrészek (`part_internal, part_hopup, part_motor, part_external`), kiegészítők (`acc_mag, acc_power, acc_optics, acc_ammo, acc_protect, acc_gear, other`). Csoportok: `weapons`, `parts`, `acc`. A szűrőben pipálható fa, több kategória egyszerre (`?cat=rifle&cat=sniper`); `?cat=all` = minden termék; kategória nélkül a fegyverek az alap (`lib/catalog.js`).
- Besorolás (`scraper/classify.py: category(cím, url, ár)`, eredetileg SQL): ajánlatonként a bolti címből; a termék kategóriája a boltok többségi szavazata (+ a terméknév fél szavazat). Csomag-részek („with battery”, „+ 2 mags”) levágva; alkatrészszó + fegyverszó + fegyverár (>= 30 000 Ft) = fegyver, kivéve „for X / X-hez” alakban. Az URL csak végső tartalék. 46 valós címen tesztelve.
- „Mihez jó” (`classify.platforms()`): M4/AR, AK, G36, MP5, AUG, SCAR, M14, P90, VSR-10, L96, Glock, Hi-Capa/1911, M9, Gearbox V2/V3 – a név és az azonos csoportba sorolt bolti címek alapján; szűrő: `?plat=m4`.
- Párosítás-védelem: alkatrész/kiegészítő ajánlat (`scraper/filters.py: is_part`) nem párosul modellkódra (a „Magazine for CM.041K” kódja a fegyveré), és fuzzy-val is csak alkatrész-termékhez.
- „Máshoz készült” szabály (`made_for_other`): „for / für / pour / para / -hoz / -hez” vagy kisbetűs „pro / do / per” + modellkód vagy platform = alkatrész/tartozék, akkor is, ha az alkatrészszót nem ismerjük („Upgrade set pro CYMA M24 CM.702”). A „VSR-10 Pro” terméknév nem számít (nagybetűs).
- Nevek: a cseh/magyar/lengyel/német/francia/olasz alkatrészszavak angolra fordítva (`names.py`: zásobník → Magazine, válec/henger → Cylinder, „M24-HEZ” → „for M24”, „na 20 ran” → „20 rounds”).
- Újrapárosítás: a napi futás a bolt korábban leválasztott (pending) ajánlatait is párosítja; kézzel: `scraper/rematch.py` (Actions → rematch, letöltés nélkül, percek alatt; közös `concurrency` csoport a napi futással).
- Jellemző-őr (`filters.py: specs / spec_conflict`): BB-súly, kiszerelés (g/kg, db), gázfajta és ml, akku V / mAh / csatlakozó / forma, rugó (M100…), belső cső átmérő és hossz, gumikeménység (°), tárkapacitás és -típus (hi/mid/low-cap), áttétel (18:1), motor tengely és típus, generáció, verzió (V2/V3), fps, csőhossz (″), csomagméret, bio/nyomjelző BB. Ha két cím ugyanabban a jellemzőben eltér, soha nem párosulnak (se kódra, se fuzzy-val); a termékhez került ajánlat jellemzőit a katalógus megjegyzi (`Catalog.learn`).
- Jellemző-audit (`rematch.py: audit_specs`): egy terméken belül az eltérő jellemzőjű ajánlatok leválnak (a név szerinti, ennek hiányában a leggyakoribb érték marad), majd újrapárosulnak. A napi futás utolsó lépése (`refresh` job → `rematch.py`), így az oldal minden éjjel magától rendbe jön.
- Egyedi változat (`is_variant`: custom, HPA, Wolverine/Polarstar, tuned, upgraded, használt…): csak ugyanilyen termékhez párosul; ha a kód az alap terméké, cím alapján új termék lesz (pl. „Evike Custom CYMA CM048 … HPA” ≠ „CYMA CM048”).
- Árkiugrás (`summary.py`, `offers.is_outlier`): >= 3 boltnál a medián 40%-a alatti / 250%-a feletti ajánlat, 2 boltnál a 2,5x olcsóbb „eltérő” (pl. alkatrész a fegyver mellett). Nem számít a legjobb árba, árfolyosóba, boltszámba, ártörténetbe; a termékoldalon lenyitható „Eltérő ár” blokkban látszik.
- Dizájn: palaszürke `#1B2027`, csontfehér `#E9E4D8`, sárgaréz `#C8A24E` (csak ár / legjobb ajánlat), olív = raktáron, tégla = elfogyott; Barlow Condensed + Barlow. Egyedi elem: árfolyosó (legolcsóbb vs. legdrágább bolt) és arányos ajánlat-létra.

## Teljesítmény
- A weboldal egy oldalbetöltésnél 1–2 D1-kérést küld (a katalógus egy batch); az összesítő tábla indexelt (`category`, `manufacturer`, népszerűség).
- A `summary.rebuild` csak a ténylegesen változott `product_summary` sorokat írja (sha1 „sig”), így a napi sorírás kicsi (D1: a sorírás a költség).

## Költségek
- Csak a Workers Paid csomag (5 $/hó); minden más ebben ingyenes (D1, cron trigger) vagy a GitHub/Cloudflare ingyenes része. Fizetős Cloudflare-szolgáltatást (pl. Workers AI) csak a tulajdonos kifejezett jóváhagyásával szabad bevezetni.

## Biztonság
- Titkok: Worker → `INGEST_TOKEN` (Secret), GitHub → `D1_API_TOKEN` (Secret). A repóban nincs kulcs. A böngésző soha nem kap kulcsot; a D1 csak a Workerből érhető el.
- Írási végpont (`/api/db`): token nélkül 404, rossz tokennel 401 (időzítés-független összehasonlítás); legfeljebb 100 utasítás / kérés, egy tranzakció; robots.txt tiltja.
- Weboldal: SQL csak paraméterezve (a kereső `LIKE ... ESCAPE`, nincs összefűzött felhasználói adat); biztonsági fejlécek (`next.config.mjs`: HSTS, nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, CSP frame-ancestors/form-action), `X-Powered-By` ki; `/go` csak DB-beli http(s) bolti URL-re irányít; `/cur` open-redirect-védett.
- Hálózat: Cloudflare proxy (DDoS automatikus), Bot Fight Mode, rate limiting (100 kérés / 10 mp / IP); a scraper a workers.dev címen ír (oda nem hat a zóna botvédelme).
- GitHub Actions: `permissions: contents: read`, a kézi `limit` env-ként és számként ellenőrizve; forkból nyitott PR nem kap titkot.
- Kód: a repó publikus (ingyenes Actions-percek miatt), `LICENSE` = minden jog fenntartva.

## Séma – lényeg
- `products` = kanonikus termék, kulcs: **(manufacturer_id, model_code_norm)**.
- `offers` = bolti termékoldal (`shop_id, external_id` egyedi), nyers cím/brand/SKU/EAN megőrizve -> újrapárosítható.
- `product_codes` = EAN + alternatív kódok; a kézi összevonások ide kerülnek, így legközelebb automatikus.
- `price_history` napi 1 sor/ajánlat, HUF a napi árfolyamon rögzítve.
- `exchange_rates` + `latest_rates` nézet: hétvégén az utolsó MNB árfolyam él.
- `product_summary` tábla (a scraper építi a napi futás végén): legjobb raktáron lévő HUF ár, ajánlatszám, összesített készlet.
- `match_status = 'manual'` sort az automatika soha nem írja felül.

## Párosítási kaszkád (`scraper/matcher.py`)
1. EAN egyezés -> auto
2. Gyártó + erős kód (gyártóspecifikus regex, pl. `CM.522` -> `CM522`) meglévő termékre -> auto
3. Erős kód, de nincs termék -> új kanonikus termék
4. Gyenge kód (betű+szám token) -> csak ha pontosan 1 meglévő termékre illik
5. Gyártón belüli fuzzy cím (difflib): ≥0.92 és 0.05-ös előny -> auto; ≥0.75 -> review sor
6. Ismert gyártó, nincs kód és nincs hasonló termék -> új termék cím alapján (`new_title`, `model_code_norm = null`); a többi bolt fuzzy-val párosul rá
7. Ismeretlen gyártó -> `pending`

Egységes név (`scraper/names.py`): „Márka + modell + típus + szín”, többnyelvű töltelékszavak (airsoftová zbraň, replika, puska…) törlése, színek angolul, csupa nagybetűs címek javítása. Idempotens; a meglévő termékeket az éjszakai futás nevezi át.

Védőkorlátok: szomszédos kódok (CM522/CM523) sosem olvadnak össze; családnevek (AK47, M4, MP5) nem kódok; rövid gyártóaliasok (TM, WE, DB) a címben csak nagybetűvel számítanak.
Karbantartás: új regex a `STRONG_PATTERNS`-be = több automatikus párosítás.

## Fejlesztési terv
1. ✅ **Séma** – `d1/schema.sql` (korábban Supabase-migrációk 0001–0013).
2. ✅ **MNB árfolyam job** – `mnb_rates.py`, napi cron.
3. ✅ **Generikus scraper + pipeline** – JSON-LD, sitemap/lapozás, `run_shop.py`, GitHub Actions.
4. ⏳ **Bolt-konfigok élesítése** – 2. kör kész (fenti táblázat, microdata-támogatás). Hátra: első éles futás `allapot.sql` alapján, Combat-Zone.
5. ✅ **Párosítás bekötése** – `run_shop.py` hívja, `match_candidates` review-hoz.
6. ✅ **Frontend MVP** – `web/` (lásd „Weboldal”). Élesben: https://www.airsofthunter.com (Cloudflare Workers + D1). Kész: kódos keresés (CM522 = CM.522). Kész: szűrősáv (típus, ár + csúszka, márka, készlet). Kész: sitemap.xml, robots.txt, /bot oldal, saját domain. Hátra: kattintásszámlálás.
7. **Admin review oldal (1–2 nap)** – pending/review ajánlatok: „összevon X-szel” / „új termék” / „elutasít” (Cloudflare Access-szel védett oldal).
8. ✅ **Üzemeltetés** – `health_check.py` (napi + kézi), GitHub Actions hiba -> e-mail; ajánlat `is_active=false`, ha napokig nem láttuk.
9. **2. fázis** – árriasztás (`price_alerts` kész), szállítási költség HU-ra boltonként, affiliate XML feedek.

## Scraping irányelvek
robots.txt és ÁSZF tiszteletben tartása, boltonként 1 kérés/1–3 mp, éjszakai futás, cache (`ETag`/`Last-Modified`). Ahol van affiliate program, **XML/CSV termékfeedet kérni** – az a legstabilabb, karbantartásmentes forrás.
