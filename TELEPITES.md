# AirsoftHunter – telepítési útmutató (kezdőknek)

Minden parancsot **PowerShellben**, az `E:\airsoftradar` mappában futtass (`cd E:\airsoftradar`).

## 1. Fájlok frissítése
Az `airsoftradar.zip` tartalmát csomagold ki az `E:\airsoftradar` mappába → „Fájlok cseréje” mindenre.

## 2. Git bemutatkozás (egyszer kell)
```powershell
git config --global user.name "A neved"
git config --global user.email "a-github-email-cimed@pelda.hu"
```

## 3. GitHub
1. Ha nincs fiókod: https://github.com → Sign up.
2. GitHub parancssori eszköz telepítése:
   ```powershell
   winget install --id GitHub.cli
   ```
3. **Zárd be a PowerShellt, nyiss újat**, majd `cd E:\airsoftradar`.
4. Bejelentkezés:
   ```powershell
   gh auth login
   ```
   Válaszok: `GitHub.com` → `HTTPS` → `Y` → `Login with a web browser` → a kiírt kódot írd be a megnyíló böngészőben.
5. Feltöltés publikus repóba:
   ```powershell
   git add .
   git commit -m "Első verzió"
   gh repo create airsoftradar --public --source . --push
   ```

## 4. Supabase (adatbázis)
1. https://supabase.com → **Start your project** → belépés GitHubbal.
2. **New project**: név `airsoftradar`, adatbázis-jelszó (mentsd el), Region: **Central EU (Frankfurt)**. Várj ~2 percet.
3. Bal menü **SQL Editor** → **New query**. Nyisd meg Jegyzettömbbel a `supabase\telepites_egyben.sql`-t, **Ctrl+A, Ctrl+C**, illeszd be az üres query-be, **Run**.
   - Ha felugrik egy „destructive operation” figyelmeztetés: **Run this query** (csak a saját árkereső-tábláinkat törli és hozza létre újra).
   - Várt eredmény alul egy sor: `boltok 20 | gyartok 81 | kategoriak 6`.
4. Ez a fájl az összes migrációt (0001–0013) helyes sorrendben tartalmazza. Újrafuttatható, de **minden összegyűjtött ajánlatot töröl** – csak új telepítéskor vagy végső esetben használd.
5. Bal lent **Project Settings** → **API Keys** → másold ki a **Secret key**-t (`sb_secret_...`).
   **Project Settings → Data API** (vagy a projekt főoldala) → másold ki a **Project URL**-t (`https://xxxx.supabase.co`).

## 5. Kulcsok a GitHubra (titkosan)
```powershell
gh secret set SUPABASE_URL
gh secret set SUPABASE_SERVICE_KEY
```
Mindkettő után illeszd be az értéket (jobb klikk) és Enter. A titkos kulcs **soha** ne kerüljön fájlba!

## 6. Első próbafutás
1. https://github.com → a repód → **Actions** fül → bal oldalt **daily-scrape** → **Run workflow** → `limit` mezőbe: `10` → **Run workflow**.
2. ~5–10 perc múlva zöld pipa = siker. Piros X esetén kattints rá, és küldd el a hibaüzenetet.
3. Supabase → **SQL Editor** → futtasd a `supabase\allapot.sql`-t: boltonként mutatja, hány ajánlat jött le, mennyi párosodott, és az első hibát.

## 7. Frissítés (amikor új fájlokat kapsz)
Zip kicsomagolása az `E:\airsoftradar` mappába (felülírás), majd:
```powershell
git add .
git commit -m "Frissítés"
git push
```

## 8. Weboldal (Vercel) – egyszer kell
1. **Supabase → SQL Editor → +**: futtasd a `supabase\migrations\0005_web_views.sql`-t (adatot nem töröl). Várt eredmény: `kész | <termékszám>`.
2. **Supabase → Project Settings → API Keys**: másold ki a **Publishable key**-t (`sb_publishable_...`). Ez nyilvános olvasókulcs, a weboldal ezzel olvas.
3. Új fájlok feltöltése (7. pont: kicsomagolás, `git add .`, `git commit`, `git push`).
4. **vercel.com → Add New… → Project** → GitHub összekötése (ha kéri) → az `airsoftradar` repó mellett **Import**.
5. A beállító oldalon:
   - **Root Directory** → **Edit** → válaszd a `web` mappát → **Continue**.
   - **Environment Variables** – két sor:
     - `SUPABASE_URL` = `https://xxxx.supabase.co`
     - `SUPABASE_PUBLISHABLE_KEY` = `sb_publishable_...`
   - **Deploy**.
6. 1–2 perc múlva kész: a kapott címen (pl. `airsoftradar.vercel.app`) él az oldal. Ezután minden `git push` után magától frissül.

## 9. Adatbázis-frissítés (amikor új `migrations/000N_...sql` fájlt kapsz)
Supabase → **SQL Editor** → **+** → az új fájl tartalma → **Run**. Ezek adatot nem törölnek. (A `telepites_egyben.sql`-t ilyenkor **ne** futtasd!)

## 10. Saját domain (Cloudflare → Vercel)
1. **Vercel → Project → Settings → Domains**: add hozzá az `airsofthunter.com`-ot (a `www` változat magától jön, a csupasz domain 308-cal a `www`-re irányít).
2. **Cloudflare → airsofthunter.com → DNS → Records**: töröld a meglévő `@` és `www` A/AAAA/CNAME rekordokat (ha vannak).
3. **Add record** kétszer (az értéket a Vercel mutatja, „View DNS configuration”):
   - Type `CNAME`, Name `@`, Target `<…>.vercel-dns-017.com`, **Proxy status: DNS only (szürke felhő)**
   - Type `CNAME`, Name `www`, Target ugyanaz (vagy amit a Vercel a www-hez ír), **DNS only**
4. Vercel → **Refresh**. Pár perc – néhány óra, amíg „Valid Configuration” lesz; az SSL-t a Vercel adja.

## 11. Üzemeltetői adatok (ÁSZF, adatvédelem, impresszum)
1. Nyisd meg Jegyzettömbbel: `web\lib\site.js`.
2. Az `OPERATOR` részben írd át a `[szögletes zárójeles]` értékeket: név, cím, e-mail (cég / egyéni vállalkozó esetén adószám és nyilvántartási szám is). Az idézőjelek maradjanak!
3. Mentés, majd `git add .` → `git commit -m "Uzemelteto adatai"` → `git push`. A jogi oldalak 1–2 perc múlva frissülnek.

## 12. Bevétel: Google AdSense és „Hívj meg egy kávéra” (később, ha kéred)
Alapból **minden ki van kapcsolva**, az oldalon semmi nem látszik. A beállítások a `web\lib\site.js` alján, a `MONETIZE` részben vannak (vagy Vercelen környezeti változóként, utána Redeploy).

**Kávé:** regisztrálj a ko-fi.com vagy a buymeacoffee.com oldalon, és a saját oldalad címét írd be a `coffeeUrl` mezőbe. A lábléc jobb alsó sarkában megjelenik egy halk link.

**AdSense, 1. lépés (jóváhagyás):**
1. Regisztrálj: adsense.google.com, webhelyként add meg az `airsofthunter.com`-ot.
2. A kapott `ca-pub-…` kódot írd be az `adsenseClient` mezőbe, majd push. Ettől betöltődik az ellenőrző kód, és elérhető lesz a `www.airsofthunter.com/ads.txt`. Hirdetés még nem jelenik meg.
3. Az AdSense felületén: **Hirdetések → Webhelyek szerint → Automatikus hirdetések: KI** (ez alapból be van kapcsolva, ezért kell kikapcsolni!). Az átfedő formátumokat (rögzített sáv, teljes képernyős „vignette”) is kapcsold ki.
4. **Adatvédelem és üzenetek → Európai szabályozás → üzenet létrehozása.** Ez a Google hitelesített hozzájárulás-kérő ablaka, az EU-ban kötelező. Nélküle az EU-s látogatóknak az AdSense nem vagy csak korlátozottan mutat hirdetést. Ez az egyetlen dolog, ami első látogatáskor felugrik, és ezt nem lehet kihagyni.
5. Várd meg a jóváhagyást (néhány nap – pár hét).

**AdSense, 2. lépés (hirdetések bekapcsolása):** Hirdetések → Hirdetési egység szerint → **Display hirdetés**, „vízszintes” formában. Két egység kell: egy a lista aljára, egy a termékoldal aljára. A kapott `data-ad-slot` számokat írd be az `adsenseSlotList` és az `adsenseSlotProduct` mezőbe, majd push.

Az adatvédelmi tájékoztató a beállításoktól függően automatikusan kiegészül (Google AdSense, hozzájárulás, kávé-szolgáltató).

## 13. Frissítés 2026-11-09: alkatrész-kategóriák, többes szűrés
1. Zip kicsomagolása, `git add .` → `git commit -m "Alkatresz kategoriak"` → `git push`.
2. **Supabase → SQL Editor → +**: futtasd a `supabase\migrations\0010_parts_platforms.sql`-t (adatot nem töröl). A végén kategóriánként kiírja a termékszámot (rifle, pistol, part_internal, acc_mag…).
   - Ha a 0007–0009 még nincs lefuttatva, előbb azokat, sorrendben.
3. A weboldal 1–2 perc múlva az új szűrőkkel jelenik meg. A tévesen fegyverhez kötött olcsó tárak/alkatrészek ajánlatai átmenetileg eltűnnek; a következő éjszakai futás a helyes termékhez párosítja őket.

## 14. Partnerprogramok (affiliate) bekötése
Ha egy bolt partnerlinket ad, a `/go/…` kimenő link automatikusan azt használja:
**Supabase → Table Editor → `shops`** → a bolt sorában az `affiliate_template` mezőbe írd a sablont, ahol `{url}` a termékoldal címe, pl. `https://partner.pelda.com/klikk?id=123&url={url}`. Mentés – azonnal él, push sem kell.

## 15. Frissítés 2026-11-09 (2): gyanús árak, custom változatok, biztonság
1. Zip kicsomagolása, `git add .` → `git commit -m "Gyanus arak, biztonsag"` → `git push`.
2. **Supabase → SQL Editor → +**: előbb a `0010_parts_platforms.sql` (ha még nem futott), utána a `0011_outliers_variants.sql`. A végén kiírja, hány „eltérő” ajánlatot talált, és hányat választott le újrapárosításra.
3. Biztonsági beállítások (egyszer, kézzel – kód nélkül):
   - **Kétlépcsős azonosítás (2FA)** mindenhol: GitHub (Settings → Password and authentication), Cloudflare (My Profile → Authentication), Vercel (Account Settings → Authentication), Supabase (Account → Security), Google.
   - **GitHub → a repó → Settings → Code security**: Dependabot alerts és Secret scanning: **Enable**.
   - **Cloudflare → airsofthunter.com → DNS → Settings → DNSSEC: Enable** (a Cloudflare-nél vett domainnél egy kattintás).

## 16. Frissítés 2026-11-09 (3): összekevert termékek szétbontása
1. Zip kicsomagolása, `git add .` → `git commit -m "Termekek szetbontasa"` → `git push`.
2. **Supabase → SQL Editor**, mindegyik új lapon, ebben a sorrendben (amelyik már lefutott, az kihagyható, de újrafuttatni sem baj): `0010_parts_platforms.sql` → `0011_outliers_variants.sql` → `0012_parts_multilang.sql`.
3. **GitHub → a repód → Actions → bal oldalt „rematch” → Run workflow.** Pár perc alatt újrapárosítja a leválasztott ajánlatokat, angolra egységesíti a termékneveket és frissíti az oldalt. (Ha épp fut az éjszakai letöltés, megvárja.)

## 17. Frissítés 2026-11-09 (4): gyors weboldal-frissítés
1. **Supabase → SQL Editor → +**: futtasd a `0013_fast_refresh.sql`-t (kb. fél–egy perc). A végén: `termekek | besorolatlan_ajanlat` – az utóbbi legyen 0.
2. Zip kicsomagolása, `git add .` → `git commit -m "Gyors frissites"` → `git push`.
Miért: a weboldal-frissítés túllépte a Supabase 8 mp-es időkorlátját („statement timeout”). Most a besorolás ajánlatonként egyszer fut, a frissítés kb. 1 mp.

## 18. Frissítés 2026-11-09 (5): BB-súlyok, gázok, akkuk, rugók szétválasztása
1. Zip kicsomagolása, `git add .` → `git commit -m "Jellemzo-or"` → `git push`.
2. **GitHub → Actions → rematch → Run workflow** (most egyszer kézzel; pár perc). A naplóban: `eltérő jellemző miatt leválasztva: N`, utána párosítás, átnevezés, frissítés.
3. Ezután minden éjjel automatikusan lefut a napi letöltés végén – kézzel nem kell.

## 19. Átköltözés a Cloudflare-re – 1. lépés: a weboldal (Vercel helyett Cloudflare Workers)
Az adat egyelőre a Supabase-ből jön; a 2. lépésben az adatbázis is átkerül (D1). Közben az oldal végig működik.

**A) Cloudflare fizetős csomag (havi 5 $):** Cloudflare → bal menü **Workers & Pages** → **Plans** (vagy „Upgrade”) → **Workers Paid** → fizetés megadása.

**B) Fájlok:** zip kicsomagolása, `git add .` → `git commit -m "Cloudflare Workers"` → `git push`. (A Vercel ettől még fut tovább, az átállásig az él.)

**C) Worker létrehozása a GitHub-repóból:**
1. **Workers & Pages → Create → Import a repository** → GitHub összekötése (ha kéri) → válaszd az `airsoftradar` repót.
2. **Project name:** `airsofthunter` (pontosan így – ez szerepel a `web/wrangler.jsonc`-ben).
3. **Build settings / Advanced:**
   - Root directory (Path): `web`
   - Build command: `npx opennextjs-cloudflare build`
   - Deploy command: `npx opennextjs-cloudflare deploy`
   - Build variables: `SUPABASE_URL` és `SUPABASE_PUBLISHABLE_KEY` (ugyanazok, mint a Vercelen)
4. **Create and deploy.** Az első fordítás 3–6 perc. Ha piros, küldd el a build naplót (Deployments → a sikertelen → View build log).

**D) Futásidejű változók:** a Worker oldalán **Settings → Variables and Secrets → Add**:
   - `SUPABASE_URL` – Type: **Secret** – érték: `https://xxxx.supabase.co`
   - `SUPABASE_PUBLISHABLE_KEY` – Type: **Secret** – érték: `sb_publishable_...`
   - **Deploy**. Ezután a `https://airsofthunter.<valami>.workers.dev` címen már működnie kell az oldalnak. Próbáld ki: lista, szűrők, termékoldal, ÁSZF, „Megnézem a boltban”.

**E) A domain átállítása (ha a D) pontban minden jó):**
1. **Cloudflare → airsofthunter.com → DNS → Records:** töröld a két `CNAME` rekordot, ami a `vercel-dns`-re mutat (`@` és `www`).
2. **Workers & Pages → airsofthunter → Settings → Domains & Routes → Add → Custom domain:** `www.airsofthunter.com` → Add. Majd ugyanígy: `airsofthunter.com`.
3. **Csupasz domain → www átirányítás:** airsofthunter.com → **Rules → Redirect Rules → Create rule**:
   - Ha: *Hostname* *equals* `airsofthunter.com`
   - Akkor: *Dynamic*, kifejezés: `concat("https://www.airsofthunter.com", http.request.uri.path)`, Status: **301**, *Preserve query string*: bepipálva → **Deploy**.
4. Pár perc múlva a `https://www.airsofthunter.com` már a Cloudflare-ről jön (a böngészőben semmi nem látszik másnak).

**F) Vercel megszüntetése (1–2 nap hibátlan működés után):** Vercel → a projekt → Settings → Advanced → **Delete Project**; GitHub → Settings → Applications → Vercel → Uninstall.

## Hibák
| Üzenet | Megoldás |
|---|---|
| `LF will be replaced by CRLF` | Csak figyelmeztetés, nem hiba. |
| `Author identity unknown` | 2. lépés kimaradt. |
| `gh is not recognized` | 3.2 után nem nyitottál új PowerShellt. |
| `null value in column "name_en"` | A migrációk rossz sorrendben futottak -> futtasd a `telepites_egyben.sql`-t. |
| PowerShell „nem áll le” probe közben | Még dolgozik (sok oldalt tölt le). A `[probe] ...` sorok mutatják, hol tart; a végén `[probe] KÉSZ`. Leállítás: **Ctrl+C**. |
| Vercel: „Hiányzik a SUPABASE_URL…” | A 8.5 környezeti változók hiányoznak; Vercel → Settings → Environment Variables, utána Deployments → Redeploy. |
| Vercel: „Supabase 404 … product_summary/v_product_offers” | A 8.1 lépés (`0005_web_views.sql`) kimaradt. |
| Vercel domain: „Invalid Configuration” | Cloudflare-ben a felhő narancssárga (proxy) → kattints rá, legyen szürke (DNS only); vagy még terjed a DNS (várj, majd Refresh). |
| `canceling statement due to statement timeout` | A 0013 (`0013_fast_refresh.sql`) még nem futott le. |
| Cloudflare build: „Your Worker exceeded the size limit” | A Workers Paid csomag nincs bekapcsolva (A pont). |
| Cloudflare oldal: „Hiányzik a SUPABASE_URL…” | A D pont változói hiányoznak (Settings → Variables and Secrets), utána Deploy. |
| `Invalid JWT` | Rossz kulcs: a **Secret key**-t (`sb_secret_...`) add meg, ne a publishable-t. |
