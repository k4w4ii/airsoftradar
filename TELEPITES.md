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
3. Bal menü **Sitemaps** → `https://www.airsofthunter.com/sitemap.xml` → Submit. Állapot: „Success” (az első indexelés napoktól hetekig tart).
4. (Ajánlott) Bing: bing.com/webmasters → **Import from Google Search Console** – egy kattintás.

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
