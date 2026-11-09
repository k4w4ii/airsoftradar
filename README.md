# AirsoftHunter – airsoft árkereső

**Minden jog fenntartva – lásd [LICENSE](LICENSE). A kód nem szabadon felhasználható.**

Európai airsoft ár- és készletfigyelő (HU / EN). Részletek: [ARCHITEKTURA.md](ARCHITEKTURA.md), telepítés: [TELEPITES.md](TELEPITES.md).

## Felépítés
- **Weboldal:** Next.js 16 a Cloudflare Workersen (`web/`, OpenNext), adatbázis: **Cloudflare D1** (`d1/schema.sql`).
- **Scraper:** Python, csak stdlib (`scraper/`), GitHub Actions-ben fut, és a weboldal titkos `/api/db` végpontján át ír a D1-be.
- **Titkok:** Worker → `INGEST_TOKEN` (Secret); GitHub → `D1_API_TOKEN` (Secret, ugyanaz) és `D1_API_URL` (Variable). A repóban nincs kulcs.

## Actions
`daily-scrape` naponta 02:17 UTC (árfolyam → boltok → újrapárosítás → állapot-ellenőrzés) · `rematch` kézi újrapárosítás · `health` kézi állapot-ellenőrzés · `keepalive` havonta (60 napos letiltás ellen).

## Helyi futtatás (Python 3.10+, nincs függőség)
```bash
cd scraper
python -m unittest -v                                  # tesztek (a D1-et helyi SQLite helyettesíti)
python probe.py --file pelda_urls.txt                  # mit lát a scraper
python run_shop.py taiwangun --limit 5 --dry-run       # adatbázis nélkül
D1_API_URL=... D1_API_TOKEN=... python health_check.py
```

## Új bolt hozzáadása
1. `probe.py <termékoldal> <kategória vagy sitemap>` – van-e JSON-LD, milyen a link-minta.
2. Sor a `shops` táblába (D1 Console, `INSERT INTO shops ...`) + bejegyzés a `scraper/shops.json`-ba.
3. A bolt slug-ja a `daily-scrape.yml` matrixába.
