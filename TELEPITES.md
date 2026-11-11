# AirsoftHunter – telepítési és üzemeltetési útmutató (kezdőknek)

Minden parancsot **PowerShellben**, az `E:\airsoftradar` mappában futtass (`cd E:\airsoftradar`).
Felépítés: weboldal és adatbázis a **Cloudflare**-en (Workers + D1), a napi letöltés a **GitHub Actions**-ben fut.

## 1. Frissítés (amikor új zipet kapsz)
1. Az `airsoftradar.zip` tartalmát csomagold ki az `E:\airsoftradar` mappába → „Fájlok cseréje” mindenre.
2. Ellenőrizd a `web\wrangler.jsonc` végén a `database_id`-t. Ha ott `IDE_MASOLD_A_D1_DATABASE_ID-T` áll, írd vissza a saját D1 Database ID-det (3.3 pont).
3. Feltöltés:
   ```powershell
   git add -A
   git commit -m "Frissítés"
   git push
   ```
4. A Cloudflare magától újraépíti az oldalt (Workers & Pages → `airsofthunter` → Deployments, 3–6 perc, zöld = kész).

## 2. Git és GitHub (egyszer kell)
```powershell
git config --global user.name "A neved"
git config --global user.email "a-github-email-cimed@pelda.hu"
winget install --id GitHub.cli
```
Zárd be a PowerShellt, nyiss újat, `cd E:\airsoftradar`, majd `gh auth login` (GitHub.com → HTTPS → Y → Login with a web browser).
Első feltöltés: `git add .` → `git commit -m "Első verzió"` → `gh repo create airsoftradar --public --source . --push`.

## 3. Cloudflare (egyszer kell)
1. **Fizetős csomag (havi 5 $):** Workers & Pages → Plans → **Workers Paid**.
2. **Worker a GitHub-repóból:** Workers & Pages → Create → **Import a repository** → `airsoftradar`.
   - Project name: `airsofthunter`
   - Root directory (Path): `web`
   - Build command: `npx opennextjs-cloudflare build`
   - Deploy command: `npx opennextjs-cloudflare deploy`
3. **Adatbázis:** Storage & databases → D1 SQL database → **Create**.
   - Name: `airsofthunter`, Location: Eastern Europe (EEUR).
   - A **Database ID**-t írd be a `web\wrangler.jsonc`-be az `IDE_MASOLD_A_D1_DATABASE_ID-T` helyére, majd push (1. pont).
   - A táblákat: D1 → Console → a `d1\schema.sql` teljes tartalma → Run.
4. **Titkos kulcs:** PowerShellben generáld:
   ```powershell
   [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
   ```
   Worker → Settings → Variables and Secrets → Add: Type **Secret**, Name `INGEST_TOKEN`, Value: a kulcs → Deploy.
   A kulcsot ne küldd el senkinek, ne mentsd fájlba, és ne legyen rajta képernyőképen.
5. **Domain:** Worker → Settings → Domains & Routes → Add → Custom domain: `www.airsofthunter.com`, majd `airsofthunter.com`.
   Csupasz domain → www: airsofthunter.com → Rules → Redirect Rules → *Hostname equals* `airsofthunter.com` → Dynamic: `concat("https://www.airsofthunter.com", http.request.uri.path)`, 301, Preserve query string.
6. **Védelem:** a proxy és a DDoS-védelem a Custom domainnel automatikus.
   - Security → Settings → **Bot fight mode: On**.
   - Security → Security rules → Create rule ▾ → **Rate limiting rules**: URI Path starts with `/`, IP szerint, 100 kérés / 10 mp → Block 10 mp.
   - Az **AI Labyrinth** és a **Precursor** maradjon kikapcsolva.

## 3/b. Pontos éjszakai indítás (egyszer kell)
A GitHub saját ütemezője órákat késhet, ezért a napi letöltést a Cloudflare Worker indítja 02:17 UTC-kor (`web/custom-worker.js`). Ha ez valamiért elmarad, a GitHub 06:47 UTC-kor tartalékként indítja.
1. GitHub → jobb felül a profilképed → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
   - Token name: `airsofthunter-cron`. Expiration: a leghosszabb választható.
   - Repository access: **Only select repositories** → `airsoftradar`.
   - Permissions → Repository permissions → **Actions: Read and write**.
   - **Generate token** → másold ki (csak egyszer látszik).
2. Cloudflare → Worker → Settings → Variables and Secrets → Add: Type **Secret**, Name `GH_TOKEN`, Value: a token → Deploy.
3. Lejáratkor ugyanígy újat kell generálni (addig a tartalék indítás működik).

## 4. GitHub titkok és változók (egyszer kell)
Repó → Settings → Secrets and variables → Actions:
- **Secrets** fül → `D1_API_TOKEN` = ugyanaz a kulcs, mint a Worker `INGEST_TOKEN`-je.
- **Variables** fül → `D1_API_URL` = `https://airsofthunter.<fiókod>.workers.dev/api/db`.
  - A pontos cím: Worker → Settings → Domains & Routes → `workers.dev` sor; ha „Disabled”, kapcsold be.

## 5. Napi működés és ellenőrzés
- **daily-scrape** (minden éjjel 02:17 UTC):
  1. MNB-árfolyam.
  2. Boltok letöltése.
  3. Újrapárosítás és a weboldal frissítése.
  4. **Állapot-ellenőrzés**.
  
  Ha bármi hibás, a futás piros lesz, és a GitHub e-mailt küld.
- **Kézi ellenőrzés bármikor:** Actions → **health** → Run workflow (fél perc).
  - A futás **Summary** oldalán táblázat jelenik meg: ✅ rendben, ⚠️ figyelmeztetés (pl. egy bolt nem sikerült), ❌ hiba.
  - Ellenőrzi: adatbázis, termékszám, árfolyam frissessége, napi letöltés, boltok, főoldal, szűrés, termékoldal, bolti link, sitemap, jogi oldal, a titkos végpont védelme.
- **Kézi újrapárosítás:** Actions → **rematch** → Run workflow (pár perc).
- **Ismeretlen márkák listája:** Actions → **brands** → Run workflow → a futás oldalán alul az `ismeretlen-markak` csatolmány (CSV) letölthető.
- **SQL-fájl futtatása** (új márkák, boltok): Actions → **d1-sql** → Run workflow → fájlnév (pl. `d1/uj_markak_2026-11-09.sql`). Utána magától lefut a rematch is.
- **Boltonkénti állapot:** D1 → Console → a `d1\allapot.sql` tartalma → Run.
- **Miért ad egy bolt 0 terméket:** ugyanott a `d1\diagnozis.sql`.

## 5/b. Rendrakás (automatikus)
- A rematch (és a napi futás vége) leválasztja a rossz helyen lévő ajánlatokat: alkatrész egy fegyver alatt, egyedi/HPA/használt változat a gyári alatt (és fordítva), majd a helyes termékhez kerülnek.
- Az egyedi, tuningolt, HPA és használt fegyverek külön kategóriában vannak („Egyedi és tuningolt fegyverek”).
- **Idegen nyelvű címek:** ingyenes szótár fordítja angolra (`scraper/dict/*.txt`, kb. 3000 szó, nincs fizetős szolgáltatás). A terméknevek a rematch-nél lesznek angolok, a termékoldali bolti címek az oldal nyelvén jelennek meg (magyar oldalon a magyar szavak maradnak).
- **Új szó felvétele:** a megfelelő `scraper/dict/0X.txt` fájlba egy sor: `szó=angol` (üres jobb oldal = a szó törlődik). Utána a gépeden: `python scraper/dictionary.py` (frissíti a `web/lib/dictionary.json`-t), push, majd Actions → rematch. Az Actions → words workflow csak a még nem ismert szavakat listázza.

## 5/c. Minőség-őr (automatikus + kézi javítások)
- Minden éjjel és minden kézi rematch-nél fut (`scraper/quality.py`):
  - **automatikusan javít**, amit biztosan el lehet dönteni: a típusához túl olcsó „fegyvert”, és az alkatrész nevű „fegyvert” (pl. „Stock for CM.708”) átsorolja;
  - **listát készít** arról, amit érdemes megnézni: vegyes ajánlatok egy termék alatt, 2,5x-es árkülönbség a raktáron lévők között, drága „alkatrész”, idegen nyelvű név.
- **Hol látod:** Actions → a rematch (vagy a napi futás) → **Summary** oldal: „Minőség-őr” táblázat; lent **Artifacts → minoseg** → CSV (Excelben megnyitható).
- **Kézi javítás (mindörökre):** `scraper/javitasok.txt` – egy sor = egy javítás, a fájl elején példák:
  - `kategoria <termék-slug> = acc_gear` (a slug a termékoldal címének vége: `.../hu/p/<slug>`)
  - `elrejt <bolti URL>` (az ajánlat soha többé nem jelenik meg)
  - Mentés → push → Actions → rematch.

## 5/d. Védőhálók (automatikus, nem kell kézzel tesztelni)
1. **Tesztek minden feltöltésnél** (Actions → **tests**): több mint 100 valós bolti címmel ellenőrzi a besorolást, a párosítást, a szűrőket és a weboldalt. Ha piros, e-mailt kapsz.
2. **Tesztkapu:** az éjszakai frissítés, a rematch és a d1-sql csak akkor ír az adatbázisba, ha a tesztek zöldek – hibás kód soha nem rontja el az oldalt.
3. **Biztosíték:** ha változatlan kód mellett egy éjjel tömegesen (300 terméknél vagy 3%-nál több) változna a kategória, vagy sok termék tűnne el, a változás nem kerül ki, a régi állapot marad, és a health piros (e-mail). Ha a változás szándékos: Actions → rematch → Run workflow → pipáld be a **force**-t.
4. **Minőség-őr** a health-ben is: „Minőség-őr” sor (ellenőrizendő tételek száma).

## 6. Üzemeltetői adatok (ÁSZF, adatvédelem, impresszum)
`web\lib\site.js` → `OPERATOR` rész (név, e-mail; cím, adószám, nyilvántartási szám csak ha kitöltöd). Mentés → push.

## 7. Bevétel: Google AdSense és „Hívj meg egy kávéra” (alapból kikapcsolva)
A beállítások a `web\lib\site.js` alján, a `MONETIZE` részben vannak, vagy a Workeren változóként: `ADSENSE_CLIENT`, `ADSENSE_SLOT_LIST`, `ADSENSE_SLOT_PRODUCT`, `COFFEE_URL` → Deploy.

**Kávé:** ko-fi.com vagy buymeacoffee.com → a saját oldalad címe a `coffeeUrl` mezőbe. A láblécben halk link jelenik meg.

**AdSense:**
1. adsense.google.com → webhely: `airsofthunter.com`.
2. A `ca-pub-…` kód az `adsenseClient` mezőbe → push. Ekkor él az ellenőrző kód és a `/ads.txt`, hirdetés még nincs.
3. AdSense: Automatikus hirdetések **KI**, az átfedő formátumok is.
4. Adatvédelem és üzenetek → Európai szabályozás → üzenet létrehozása. Ez az EU-ban kötelező hozzájárulás-kérő, és ez az egyetlen dolog, ami első látogatáskor felugrik.
5. Jóváhagyás után két „Display” egység (lista alja, termékoldal alja), a `data-ad-slot` számok az `adsenseSlotList` és az `adsenseSlotProduct` mezőbe → push.

Az adatvédelmi tájékoztató magától kiegészül.

## 8. Partnerprogram (affiliate) bekötése
Ha egy bolt partnerlinket ad, a „Megnézem a boltban” gomb azt használja. D1 → Console:
```sql
UPDATE shops SET affiliate_template = 'https://partner.pelda.com/klikk?id=123&url={url}' WHERE slug = 'gunfire';
```
A `{url}` helyére kerül a termékoldal címe. Azonnal él (legfeljebb fél óra gyorsítótár).

## 9. Google Search Console (egyszer)
1. search.google.com/search-console → **Add property** → **Domain**: `airsofthunter.com` → Continue.
2. Ellenőrzés: ha felajánlja a **Cloudflare**-t („Start verification”), jelentkezz be és engedélyezd – a TXT rekordot magától felveszi. Különben másold ki a `google-site-verification=…` szöveget → Cloudflare → DNS → Records → Add record: Type `TXT`, Name `@`, Content: a szöveg → Save → vissza a Search Console-ba → **Verify**.
3. Bal menü **Sitemaps** → `sitemap.xml` → Submit. Ez egy index: a Google magától megtalálja a darabjait (`/sitemaps/static.xml`, `/sitemaps/p-0.xml` …). Állapot: „Success”; a „Felfedezett oldalak” száma pár nap alatt nő.
4. Gyorsítás: felül az **URL-vizsgálat** mezőbe `https://www.airsofthunter.com/hu` → **Indexelés kérése**; ugyanígy `/en` és 2–3 kategória (pl. `/hu?cat=weapons`). Naponta kb. 10 ilyen kérés engedélyezett.
5. Cloudflare: a **rate limiting** szabály (3.6) ne fogja meg a Google-t. Security → Security rules → a szabály → Edit: ha van **Verified Bot** mező, a kifejezés végére: `and not cf.client.bot`. Ha nincs ilyen mező, emeld a határt 300 kérés / 10 mp-re.
6. (Ajánlott) Bing: bing.com/webmasters → **Import from Google Search Console** – egy kattintás.
7. Az első indexelés napoktól hetekig tart; a **Pages** jelentésben az „Felfedezve – jelenleg nincs indexelve” új oldalnál normális.

## 10. Biztonság (egyszer, kézzel)
- **Kétlépcsős azonosítás (2FA):** GitHub, Cloudflare, Google.
- **GitHub → repó → Settings → Code security:** Dependabot alerts és Secret scanning: **Enable**.
- **Cloudflare → airsofthunter.com → DNS → Settings → DNSSEC: Enable.**
- A Workeren a titkok mindig **Secret** típusúak legyenek, ne „Variable”.

## Hibák
| Üzenet | Megoldás |
|---|---|
| `LF will be replaced by CRLF` | Csak figyelmeztetés, nem hiba. |
| `Author identity unknown` | A 2. pont `git config` sorai kimaradtak. |
| `gh is not recognized` | A `winget` után nem nyitottál új PowerShellt. |
| Push: „Everything up-to-date” | Nem változott fájl (a zip nem lett kibontva, vagy már fent van). |
| Cloudflare build piros: „database_id” / „D1 database not found” | A `web\wrangler.jsonc`-ben nem a saját Database ID áll (1.2 pont). |
| Cloudflare build: „Your Worker exceeded the size limit” | A Workers Paid csomag nincs bekapcsolva (3.1). |
| Oldal: „Az adatok most nem érhetők el” | Worker → **Observability** → a legfrissebb piros sor mutatja az okot. Gyakori: hiányzó D1 binding (Settings → Bindings: `DB` → `airsofthunter`). |
| Actions: `D1 401` | A GitHub `D1_API_TOKEN` és a Worker `INGEST_TOKEN` nem egyezik. Generálj újat, és mindkét helyre ugyanazt írd. |
| Actions: `D1 404` | A Workerben nincs `INGEST_TOKEN`, vagy a `D1_API_URL` rossz (a vége `/api/db`). |
| Actions: `unknown url type` | A `D1_API_URL` értéke hibás; helyesen: `https://airsofthunter.<fiókod>.workers.dev/api/db`. |
| health: ⚠️ „Saját domain … kihívást adott” | Normális: a botvédelem a GitHub gépét ellenőrizte. Nézd meg böngészőben, hogy az oldal megy-e. |
| health: ❌ „Napi letöltés” | Az éjszakai daily-scrape nem futott vagy elakadt: Actions → daily-scrape → a piros futás naplója. |
