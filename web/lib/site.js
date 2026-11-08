// Az oldal nyilvános címe (kanonikus URL-ek, sitemap, megosztási képek). Vercelen felülírható: SITE_URL
export const SITE_URL = (process.env.SITE_URL || "https://www.airsofthunter.com").replace(/\/$/, "");
export const SITE_NAME = "AirsoftHunter";

// ÜZEMELTETŐ ADATAI – az ÁSZF, az adatvédelmi tájékoztató és az impresszum ezekből készül.
// Töltsd ki a [szögletes zárójeles] értékeket (Jegyzettömbbel), majd git push.
// Magánszemélyként: név + értesítési cím + e-mail. Cégként/egyéni vállalkozóként: + adószám, nyilvántartási szám.
export const OPERATOR = {
  name: "[Üzemeltető neve]",
  address: "[Irányítószám, település, utca, házszám]",
  email: "[kapcsolat e-mail cím]",
  taxNumber: "",        // pl. "12345678-1-42" (ha van)
  registry: "",         // pl. "Cégjegyzékszám: 01-09-123456" vagy "EV nyilvántartási szám: 12345678" (ha van)
};

export const LEGAL_UPDATED = "2026-11-08";

// ─── Bevétel: Google AdSense + „Hívj meg egy kávéra” ──────────────────────────────
// Amíg ezek üresek, az oldalon SEMMI nem jelenik meg és semmi nem töltődik be.
// Kitölthető itt (Jegyzettömbbel, majd git push) VAGY Vercelen környezeti változóként
// (Settings → Environment Variables, utána Redeploy). A Vercel érték az erősebb.
// Ezek nem titkos adatok: a hirdetéskód minden AdSense-es oldal forrásában látszik.
const MONETIZE = {
  adsenseClient: "",      // pl. "ca-pub-1234567890123456"   (ADSENSE_CLIENT)
  adsenseSlotList: "",    // hirdetési egység azonosítója a terméklista alján, pl. "1234567890"   (ADSENSE_SLOT_LIST)
  adsenseSlotProduct: "", // hirdetési egység a termékoldal alján   (ADSENSE_SLOT_PRODUCT)
  coffeeUrl: "",          // pl. "https://ko-fi.com/airsofthunter" vagy "https://buymeacoffee.com/airsofthunter"   (COFFEE_URL)
};

const pick = (env, own) => String(process.env[env] || own || "").trim();
const client = pick("ADSENSE_CLIENT", MONETIZE.adsenseClient);
const slot = (v) => (/^\d{6,20}$/.test(v) ? v : "");
const coffee = pick("COFFEE_URL", MONETIZE.coffeeUrl);

export const ADS = {
  client: /^ca-pub-\d{10,20}$/.test(client) ? client : "",
  slots: {
    list: slot(pick("ADSENSE_SLOT_LIST", MONETIZE.adsenseSlotList)),
    product: slot(pick("ADSENSE_SLOT_PRODUCT", MONETIZE.adsenseSlotProduct)),
  },
};
export const COFFEE_URL = /^https:\/\/[\w.-]+\.[a-z]{2,}\/\S*$/i.test(coffee) ? coffee : "";
