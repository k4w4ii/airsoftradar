# Airsoft árkereső – architektúra és fejlesztési terv (MVP)

## Stack
| Réteg | Választás |
|---|---|
| Frontend | Next.js 16 (App Router) + sima CSS, dark-first, Vercel |
| DB / Auth | Supabase (Postgres, RLS, Auth) |
| Scraper + párosító | **Python, csak stdlib** (urllib, regex, json) – nincs `pip install`; Playwright csak JS/Cloudflare-es boltokra |
| Ütemezés | GitHub Actions cron (`.github/workflows/daily-scrape.yml`) |
| Nyelv | HU + EN (`/hu`, `/en` útvonalak, hreflang) |

## Adatfolyam (naponta 02:17 UTC)
```
mnb_rates.py ─> run_shop.py × 8 bolt (párhuzamosan, max 4) ─> run_shop.py --refresh
                 felderítés (sitemap / lapozás) -> JSON-LD -> offers upsert
                 -> matcher -> price_history (HUF + EUR) -> inaktiválás (3 nap)
```

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
| `probe.py` | új bolt felderítése: mit lát a scraper, milyen linkminták vannak |
| `mnb_rates.py` | MNB SOAP -> `exchange_rates` |
| `shops.json` | boltonkénti konfig (forrás, URL-minta, lapozás, extra fejlécek, `enabled`, `status`) |

## GitHub Actions (publikus repó)
- Publikus repó -> korlátlan ingyenes Actions perc.
- `keepalive.yml`: havonta automatikus commit, mert a GitHub 60 nap commit-inaktivitás után letiltja az ütemezett workflow-kat.
- Titkok csak GitHub Secrets-ben (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`); forkból indított PR nem kapja meg őket.

## Migrációk (`supabase/migrations`, `supabase db push` sorrendben)
`0001_init` séma · `0002_seed` boltok/gyártók/kategóriák · `0003_i18n_multicurrency` HU/EN, EUR, ships_to · `0004_more_manufacturers` +28 gyártó · `0005_web_views` weboldal-nézetek, olvasási jog · `0006_dedupe_search` ismétlődés-szűrés (bolt+URL), valódi boltszám, kódos keresés · `0007_categories_search` fegyvertípus-besorolás + `catalog_search()` RPC · `0008_eu_shops` +12 EU-s bolt · `0009_accessory_brands` +31 kiegészítő/alkatrész-gyártó, ruházat elrejtése.
A törzsadat is migráció, mert a Supabase a `seed.sql`-t a migrációk UTÁN futtatná.

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
| Airsoftmania | IT | Shopify sitemap `/products/` | ÚJ – ellenőrizendő |
| Gunshot | IT | sitemap, általános minta | ÚJ – ellenőrizendő |
| VSGUN | ES | sitemap, általános minta | ÚJ – ellenőrizendő |
| Airsoft Legends | NL | sitemap, csak `/en/` | ÚJ – ellenőrizendő |
| Bunker501 | NL | sitemap, általános minta | ÚJ – ellenőrizendő |
| Phenix Airsoft | FR | sitemap, általános minta | ÚJ – ellenőrizendő |
| Militaria.pl | PL | sitemap, általános minta | ÚJ – ellenőrizendő |
| Red Beret | PL | sitemap, általános minta | ÚJ – ellenőrizendő |
| Atom Airsoft | FI | Shopify sitemap `/products/` | ÚJ – ellenőrizendő |

Lefedettség (2026-11-08 óta): fegyverek + kiegészítők + alkatrészek + védő/taktikai felszerelés; **ruházat és lábbeli kizárva** (`scraper/filters.py`, URL-re letöltés előtt és címre). Boltonként 300 perc / 6000 termék naponta (forgó ablakkal a nagy katalógusok is körbeérnek), sitemapből max. 60 000 URL, a weboldal boltonként frissül. Párosítás: token-előszűrés (6000 termék/gyártó mellett is gyors). A workflow 6 boltot futtat párhuzamosan. Ismeretlen gyártójú termékek `pending` maradnak (nem jelennek meg).

Nagy boltok: ha több termék van, mint `max_products` (6000), naponta forgó ablak; inaktiválás csak `STALE_DAYS + ciklushossz` nap után.
Hibakeresés: `supabase/allapot.sql` (összesítő), `supabase/diagnozis.sql` (http kódok, példa URL-ek).
Kinyerési sorrend: JSON-LD -> microdata (itemscope/itemprop) -> OpenGraph meta.
Időkorlát: boltonként 300 perc (`SCRAPE_BUDGET_MIN`, job-timeout 330) és alapból 6000 termék; csonka futás után nincs inaktiválás.
Állapot-lekérdezés: `supabase/allapot.sql`.

## Weboldal (`web/`, Next.js 16, Vercel)
- Függőség csak `next`, `react`, `react-dom`; sima CSS (`app/globals.css`), JavaScript (nincs TS-típusellenőrzés, ami buildet törhetne).
- Adat: PostgREST `fetch`-csel (`lib/data.js`), **publishable** kulccsal (csak olvas), 30 perces cache. Env: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`.
- Útvonalak: `/` -> `/hu` vagy `/en` (Accept-Language, `next.config.mjs` redirect) · `/[locale]` lista + szűrők · `/[locale]/p/[slug]` termékoldal · `/go/[id]` kimenő link (affiliate sablon) · `/cur` pénznem-süti.
- Nézetek (0005–0007): `product_summary` (+max ár, `category`, `search_code`), `v_product_offers`, `v_price_daily`, `v_manufacturers`, `v_site_stats`.
- Katalógus: **egy RPC-hívás** (`catalog_search`) adja a találatokat és a szűrő-darabszámokat; minden szűrő darabszáma a többi szűrővel számol. Szűrők: típus-fa (`weapons` = minden fegyver; alapértelmezés kereséskor `all`), ársávok (pénznemenként kerek határok, `PRICE_EDGES`) + kétfogantyús csúszka + min/max, márkák (többes választás), raktáron. Mobilon CSS-only lenyitható panel; JS nélkül „Szűrés” gombbal működik.
- Kategória-besorolás (`airsoft_category()` SQL): név + bolti címek + bolti URL-ek kulcsszavai, kiegészítő-felismerés árküszöbbel (< 25 000 Ft). 30 valós címen tesztelve.
- Dizájn: palaszürke `#1B2027`, csontfehér `#E9E4D8`, sárgaréz `#C8A24E` (csak ár / legjobb ajánlat), olív = raktáron, tégla = elfogyott; Barlow Condensed + Barlow. Egyedi elem: árfolyosó (legolcsóbb vs. legdrágább bolt) és arányos ajánlat-létra.

## Séma – lényeg
- `products` = kanonikus termék, kulcs: **(manufacturer_id, model_code_norm)**.
- `offers` = bolti termékoldal (`shop_id, external_id` egyedi), nyers cím/brand/SKU/EAN megőrizve -> újrapárosítható.
- `product_codes` = EAN + alternatív kódok; a kézi összevonások ide kerülnek, így legközelebb automatikus.
- `price_history` napi 1 sor/ajánlat, HUF a napi árfolyamon rögzítve.
- `exchange_rates` + `latest_rates` nézet: hétvégén az utolsó MNB árfolyam él.
- `product_summary` materializált nézet: legjobb raktáron lévő HUF ár, ajánlatszám, összesített készlet.
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
1. ✅ **Séma** – migrációk 0001–0009 (lásd fent).
2. ✅ **MNB árfolyam job** – `mnb_rates.py`, napi cron.
3. ✅ **Generikus scraper + pipeline** – JSON-LD, sitemap/lapozás, `run_shop.py`, GitHub Actions.
4. ⏳ **Bolt-konfigok élesítése** – 2. kör kész (fenti táblázat, microdata-támogatás). Hátra: első éles futás `allapot.sql` alapján, Combat-Zone.
5. ✅ **Párosítás bekötése** – `run_shop.py` hívja, `match_candidates` review-hoz.
6. ✅ **Frontend MVP** – `web/` (lásd „Weboldal”). Élesben: https://airsoftradar.vercel.app (2026-11-08). Kész: kódos keresés (CM522 = CM.522). Kész: szűrősáv (típus, ár + csúszka, márka, készlet). Hátra: sitemap.xml, kattintásszámlálás, saját domain.
7. **Admin review oldal (1–2 nap)** – pending/review ajánlatok: „összevon X-szel” / „új termék” / „elutasít” (Supabase Auth, admin role).
8. **Üzemeltetés (1 nap)** – `scrape_runs` monitor, GitHub Actions hiba -> email; ajánlat `is_active=false`, ha 3 napig nem láttuk.
9. **2. fázis** – árriasztás (`price_alerts` kész), szállítási költség HU-ra boltonként, affiliate XML feedek.

## Scraping irányelvek
robots.txt és ÁSZF tiszteletben tartása, boltonként 1 kérés/1–3 mp, éjszakai futás, cache (`ETag`/`Last-Modified`). Ahol van affiliate program, **XML/CSV termékfeedet kérni** – az a legstabilabb, karbantartásmentes forrás.
