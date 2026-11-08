# Airsoft árkereső – architektúra és fejlesztési terv (MVP)

## Stack
| Réteg | Választás |
|---|---|
| Frontend | Next.js (App Router, ISR) + Tailwind, dark-first |
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
- **Nyelv:** UI-szövegek Next.js-ben JSON szótárakkal (`messages/hu.json`, `en.json`), külső i18n könyvtár nélkül; `middleware` az `Accept-Language` alapján irányít. Kategóriák: `name_hu` / `name_en`. Terméknév: nyelvsemleges gyártói név; angol nyelvű bolt címe felülírja a magyart/csehet (`products.name_lang`).
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
`0001_init` séma · `0002_seed` boltok/gyártók/kategóriák · `0003_i18n_multicurrency` HU/EN, EUR, ships_to · `0004_more_manufacturers` +28 gyártó.
A törzsadat is migráció, mert a Supabase a `seed.sql`-t a migrációk UTÁN futtatná.

## Boltok állapota (2026-11-08, 3. kör – első éles futások után)
| Bolt | Forrás | Állapot |
|---|---|---|
| Gunfire | kategória-lapozás (`?counter=`) | ✓ élesben: 10/10 letöltve, 7 párosítva |
| Taiwangun | kategória-lapozás | ✓ élesben: 20 ajánlat, 12 párosítva (USD) |
| Evike Europe | 3 AEG kategória (`?p=N`) | ✓ élesben; minta szigorítva (termék-URL-ben mindig van szám) |
| Powair6 | robots.txt sitemap (12 223 URL, CDATA), csak `/en/aeg-*` | javítva: CDATA-kezelés |
| AirsoftPlaza | robots.txt sitemap | ✓ élesben |
| AirsoftCentrum | robots.txt sitemap, forgó napi ablak | kategóriaoldalon nincs terméklink (JS) -> sitemap; microdata ✓ |
| AirsoftPro | – | ⏸ letiltva: sitemap-részek időtúllépés GitHubról -> kategória-lapozás kell |
| Combat-Zone | – | ❌ letiltva: a kategórialista JS-ből tölt |

Nagy boltok: ha több termék van, mint `max_products` (2000), naponta forgó ablak; inaktiválás csak `STALE_DAYS + ciklushossz` nap után.
Hibakeresés: `supabase/allapot.sql` (összesítő), `supabase/diagnozis.sql` (http kódok, példa URL-ek).
Kinyerési sorrend: JSON-LD -> microdata (itemscope/itemprop) -> OpenGraph meta.
Időkorlát: boltonként 90 perc (`SCRAPE_BUDGET_MIN`) és max. 2000 termék; csonka futás után nincs inaktiválás.
Állapot-lekérdezés: `supabase/allapot.sql`.

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
6. Egyébként `pending`

Védőkorlátok: szomszédos kódok (CM522/CM523) sosem olvadnak össze; családnevek (AK47, M4, MP5) nem kódok; rövid gyártóaliasok (TM, WE, DB) a címben csak nagybetűvel számítanak.
Karbantartás: új regex a `STRONG_PATTERNS`-be = több automatikus párosítás.

## Fejlesztési terv
1. ✅ **Séma** – migrációk 0001–0004 (lásd fent).
2. ✅ **MNB árfolyam job** – `mnb_rates.py`, napi cron.
3. ✅ **Generikus scraper + pipeline** – JSON-LD, sitemap/lapozás, `run_shop.py`, GitHub Actions.
4. ⏳ **Bolt-konfigok élesítése** – 2. kör kész (fenti táblázat, microdata-támogatás). Hátra: első éles futás `allapot.sql` alapján, Combat-Zone.
5. ✅ **Párosítás bekötése** – `run_shop.py` hívja, `match_candidates` review-hoz.
6. **Frontend MVP (5–7 nap)** – `/[locale]` (hu, en), kereső (pg_trgm), kategórialista szűrőkkel (ár, készlet, gyártó, szállítási ország), termékoldal (ajánlatok választott devizában, eredeti ár tooltipben, árdiagram), `/go/[offerId]` átirányító affiliate taggel + kattintásszámlálás.
7. **Admin review oldal (1–2 nap)** – pending/review ajánlatok: „összevon X-szel” / „új termék” / „elutasít” (Supabase Auth, admin role).
8. **Üzemeltetés (1 nap)** – `scrape_runs` monitor, GitHub Actions hiba -> email; ajánlat `is_active=false`, ha 3 napig nem láttuk.
9. **2. fázis** – árriasztás (`price_alerts` kész), szállítási költség HU-ra boltonként, affiliate XML feedek.

## Scraping irányelvek
robots.txt és ÁSZF tiszteletben tartása, boltonként 1 kérés/1–3 mp, éjszakai futás, cache (`ETag`/`Last-Modified`). Ahol van affiliate program, **XML/CSV termékfeedet kérni** – az a legstabilabb, karbantartásmentes forrás.
