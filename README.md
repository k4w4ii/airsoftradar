# Airsoft árkereső

Európai airsoft ár- és készletfigyelő (HU / EN). Részletek: [ARCHITEKTURA.md](ARCHITEKTURA.md).

## Beállítás

1. **Supabase:** új projekt, majd
   ```bash
   supabase link --project-ref <ref>
   supabase db push          # migrations/0001–0004
   ```
2. **GitHub repo secrets** (Settings → Secrets and variables → Actions):
   - `SUPABASE_URL` – pl. `https://xyz.supabase.co`
   - `SUPABASE_SERVICE_KEY` – Secret key (`sb_secret_...`, Settings → API Keys; **soha ne kerüljön a kódba**, publikus repó!)
3. **Actions:** `daily-scrape` naponta 02:17 UTC, `keepalive` havonta (60 napos letiltás ellen).
   Kézi teszt: Actions → daily-scrape → Run workflow → `limit: 10`.

## Helyi futtatás (Python 3.10+, nincs függőség)

```bash
cd scraper
python -m unittest -v                                  # tesztek
python probe.py --file pelda_urls.txt                  # mit lát a scraper
python probe.py --dump debug <url>                     # nyers HTML + JSON-LD mentése
python run_shop.py taiwangun --limit 5 --dry-run       # DB nélkül
SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python mnb_rates.py
```

## Új bolt hozzáadása

1. `probe.py <termékoldal> <kategória vagy sitemap>` – van-e JSON-LD, milyen a link-minta.
2. Sor a `shops` táblába (új migráció) + bejegyzés a `scraper/shops.json`-ba.
3. A shop slug hozzáadása a `daily-scrape.yml` matrixához.
