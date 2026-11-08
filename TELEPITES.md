# Telepítési útmutató (kezdőknek)

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
   - Várt eredmény alul egy sor: `boltok 8 | gyartok 42 | kategoriak 6`.
4. Ez a fájl a 4 migrációt helyes sorrendben tartalmazza, és bármikor újrafuttatható (ha valami elromlik, csak futtasd újra).
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

## Hibák
| Üzenet | Megoldás |
|---|---|
| `LF will be replaced by CRLF` | Csak figyelmeztetés, nem hiba. |
| `Author identity unknown` | 2. lépés kimaradt. |
| `gh is not recognized` | 3.2 után nem nyitottál új PowerShellt. |
| `null value in column "name_en"` | A migrációk rossz sorrendben futottak -> futtasd a `telepites_egyben.sql`-t. |
| PowerShell „nem áll le” probe közben | Még dolgozik (sok oldalt tölt le). A `[probe] ...` sorok mutatják, hol tart; a végén `[probe] KÉSZ`. Leállítás: **Ctrl+C**. |
| `Invalid JWT` | Rossz kulcs: a **Secret key**-t (`sb_secret_...`) add meg, ne a publishable-t. |
