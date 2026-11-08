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
3. Bal menü **SQL Editor** → **New query**. Nyisd meg Jegyzettömbbel a `supabase\migrations\0001_init.sql`-t, másold be az egészet, **Run**. Várt eredmény: „Success. No rows returned”.
4. Ugyanígy sorban: `0002_seed.sql`, `0003_i18n_multicurrency.sql`, `0004_more_manufacturers.sql`. Mindegyik új query-ben.
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
3. Supabase → **Table Editor** → `offers` táblában látszanak a letöltött ajánlatok.

## Hibák
| Üzenet | Megoldás |
|---|---|
| `LF will be replaced by CRLF` | Csak figyelmeztetés, nem hiba. |
| `Author identity unknown` | 2. lépés kimaradt. |
| `gh is not recognized` | 3.2 után nem nyitottál új PowerShellt. |
| `Invalid JWT` | Rossz kulcs: a **Secret key**-t (`sb_secret_...`) add meg, ne a publishable-t. |
