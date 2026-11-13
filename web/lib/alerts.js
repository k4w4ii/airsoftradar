// Ár- és készletfigyelő: feliratkozás (dupla megerősítéssel), megerősítés, leiratkozás. Az ellenőrzés és a riasztó e-mail
// a napi frissítés végén fut (scraper/alerts.py). Regisztráció nincs: egy riasztás = e-mail + termék + típus (+ célár).
import { getDB } from "./data_d1";
import { esc, mailHtml, sendMail } from "./mail";
import { DOCS } from "./legal";
import { SITE_URL } from "./site";

export const KINDS = ["stock", "price"];
export const LIMITS = { perIpHour: 10, perEmail: 50 };
const EMAIL = /^[^\s@<>()",;:]{1,64}@[a-z0-9.-]{1,180}\.[a-z]{2,24}$/i;

export const validEmail = (e) => EMAIL.test(String(e || "").trim()) && String(e).length <= 254;

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS alerts (
     id INTEGER PRIMARY KEY, email TEXT NOT NULL, product_id INTEGER NOT NULL, kind TEXT NOT NULL,
     target_huf REAL, target_amount REAL, currency TEXT, locale TEXT NOT NULL DEFAULT 'hu',
     token TEXT NOT NULL UNIQUE, ip_hash TEXT, created_at TEXT NOT NULL, confirmed_at TEXT, sent_at TEXT)`,
  "CREATE UNIQUE INDEX IF NOT EXISTS alerts_one ON alerts (email, product_id, kind)",
  "CREATE INDEX IF NOT EXISTS alerts_ip ON alerts (ip_hash, created_at)",
];
let ready = false;
export async function ensureAlerts(db) {
  if (ready) return;
  await db.batch(SCHEMA.map((s) => db.prepare(s)));
  ready = true;
}
export function __resetAlerts() { ready = false; }

export function newToken() {
  const b = new Uint8Array(24);
  crypto.getRandomValues(b);
  return [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

export async function hashIp(ip) {
  const data = new TextEncoder().encode(`airsofthunter:${ip || "?"}`);
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", data));
  return [...h.slice(0, 8)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

const now = () => new Date().toISOString().slice(0, 19) + "Z";
export const alertLink = (action, token) => `${SITE_URL}/api/alert?a=${action}&t=${token}`;

const TXT = {
  hu: {
    subject: (name) => `Erősítsd meg az értesítést: ${name}`,
    title: "Erősítsd meg az értesítést",
    stock: (name) => `Szólunk, ha a(z) „${name}” újra raktáron lesz bármelyik általunk figyelt EU-s boltban.`,
    price: (name, target) => `Szólunk, ha a(z) „${name}” legjobb ára ${target} alá esik.`,
    confirm: "Megerősítem",
    ignore: "Ha nem te kérted, hagyd figyelmen kívül ezt a levelet: megerősítés nélkül nem küldünk semmit, és 7 nap múlva töröljük a címed.",
    footer: (stop, privacy) => `Ezt a levelet azért kaptad, mert valaki ezzel a címmel értesítést kért az AirsoftHunteren. <a href="${stop}">Leiratkozás</a> · <a href="${privacy}">Adatvédelem</a>`,
  },
  en: {
    subject: (name) => `Confirm your alert: ${name}`,
    title: "Confirm your alert",
    stock: (name) => `We will let you know when “${name}” is back in stock in any EU shop we track.`,
    price: (name, target) => `We will let you know when the best price of “${name}” drops below ${target}.`,
    confirm: "Confirm",
    ignore: "If you did not request this, ignore this email: we send nothing without confirmation, and we delete your address after 7 days.",
    footer: (stop, privacy) => `You received this email because someone requested an alert with this address on AirsoftHunter. <a href="${stop}">Unsubscribe</a> · <a href="${privacy}">Privacy</a>`,
  },
  de: {
    subject: (name) => `Bestätige deine Benachrichtigung: ${name}`,
    title: "Bestätige deine Benachrichtigung",
    stock: (name) => `Wir melden uns, sobald „${name}“ in einem der von uns beobachteten EU-Shops wieder auf Lager ist.`,
    price: (name, target) => `Wir melden uns, sobald der beste Preis für „${name}“ unter ${target} fällt.`,
    confirm: "Bestätigen",
    ignore: "Falls du das nicht angefordert hast, ignoriere diese E-Mail einfach: Ohne Bestätigung senden wir nichts, und deine Adresse wird nach 7 Tagen gelöscht.",
    footer: (stop, privacy) => `Du erhältst diese E-Mail, weil jemand mit dieser Adresse auf AirsoftHunter eine Benachrichtigung angefordert hat. <a href="${stop}">Abbestellen</a> · <a href="${privacy}">Datenschutz</a>`,
  },
  pl: {
    subject: (name) => `Potwierdź powiadomienie: ${name}`,
    title: "Potwierdź powiadomienie",
    stock: (name) => `Damy znać, gdy „${name}” znów będzie dostępny w którymkolwiek z obserwowanych przez nas sklepów w UE.`,
    price: (name, target) => `Damy znać, gdy najlepsza cena produktu „${name}” spadnie poniżej ${target}.`,
    confirm: "Potwierdzam",
    ignore: "Jeśli to nie ty, po prostu zignoruj tę wiadomość: bez potwierdzenia niczego nie wyślemy, a twój adres usuniemy po 7 dniach.",
    footer: (stop, privacy) => `Otrzymujesz tę wiadomość, ponieważ ktoś zamówił powiadomienie na ten adres w serwisie AirsoftHunter. <a href="${stop}">Wypisz się</a> · <a href="${privacy}">Prywatność</a>`,
  },
  cs: {
    subject: (name) => `Potvrď upozornění: ${name}`,
    title: "Potvrď upozornění",
    stock: (name) => `Dáme ti vědět, až bude „${name}“ znovu skladem v kterémkoli z obchodů v EU, které sledujeme.`,
    price: (name, target) => `Dáme ti vědět, až nejlepší cena produktu „${name}“ klesne pod ${target}.`,
    confirm: "Potvrdit",
    ignore: "Pokud jsi o to nežádal(a), tento e-mail ignoruj: bez potvrzení nic neposíláme a tvou adresu po 7 dnech smažeme.",
    footer: (stop, privacy) => `Tento e-mail ti přišel, protože si někdo na AirsoftHunteru objednal upozornění na tuto adresu. <a href="${stop}">Odhlásit</a> · <a href="${privacy}">Ochrana osobních údajů</a>`,
  },
};

export function confirmMail({ locale, name, kind, targetText, token }) {
  const T = TXT[locale] || TXT.en;
  const stop = alertLink("stop", token);
  const privacy = `${SITE_URL}/${locale}/${DOCS.privacy[locale] || DOCS.privacy.en}`;
  const intro = kind === "price" ? T.price(name, targetText) : T.stock(name);
  return {
    subject: T.subject(name),
    html: mailHtml({ title: T.title, paragraphs: [intro, T.ignore], button: { href: alertLink("confirm", token), label: T.confirm },
                     footer: T.footer(esc(stop), esc(privacy)) }),
    text: `${intro}\n\n${T.confirm}: ${alertLink("confirm", token)}\n\n${T.ignore}\n${stop}`,
    headers: { "List-Unsubscribe": `<${stop}>`, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click" },
  };
}

/** Feliratkozás. Visszaad: "sent" | "ok" (már megerősített, csak a célár frissült) | "limit" | "off" | "bad". */
export async function subscribe({ email, product, kind, targetHuf, targetAmount, currency, locale, ip, targetText }, mailer = sendMail) {
  email = String(email || "").trim().toLowerCase();
  if (!validEmail(email) || !KINDS.includes(kind) || !product) return "bad";
  if (kind === "price" && !(targetHuf > 0)) return "bad";
  const db = await getDB();
  await ensureAlerts(db);
  const ipHash = await hashIp(ip);
  const hourAgo = new Date(Date.now() - 3600e3).toISOString().slice(0, 19) + "Z";
  const [byIp, byEmail, existing] = (await db.batch([
    db.prepare("SELECT count(*) AS n FROM alerts WHERE ip_hash = ? AND created_at >= ?").bind(ipHash, hourAgo),
    db.prepare("SELECT count(*) AS n FROM alerts WHERE email = ?").bind(email),
    db.prepare("SELECT id, confirmed_at, token FROM alerts WHERE email = ? AND product_id = ? AND kind = ?").bind(email, product.id, kind),
  ])).map((r) => r.results || []);
  const row = existing[0];
  if (row?.confirmed_at) {                                   // már él: csak a célár frissül, nem küldünk új levelet
    await db.prepare("UPDATE alerts SET target_huf = ?, target_amount = ?, currency = ?, sent_at = NULL WHERE id = ?")
      .bind(targetHuf ?? null, targetAmount ?? null, currency || null, row.id).run();
    return "ok";
  }
  if ((byIp[0]?.n || 0) >= LIMITS.perIpHour || (!row && (byEmail[0]?.n || 0) >= LIMITS.perEmail)) return "limit";
  const token = newToken();
  await db.prepare(`INSERT INTO alerts (email, product_id, kind, target_huf, target_amount, currency, locale, token, ip_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (email, product_id, kind) DO UPDATE SET target_huf = excluded.target_huf,
                      target_amount = excluded.target_amount, currency = excluded.currency, locale = excluded.locale,
                      token = excluded.token, ip_hash = excluded.ip_hash, created_at = excluded.created_at`)
    .bind(email, product.id, kind, targetHuf ?? null, targetAmount ?? null, currency || null, locale, token, ipHash, now()).run();
  const ok = await mailer({ to: email, ...confirmMail({ locale, name: product.name, kind, targetText, token }) });
  if (!ok) {
    await db.prepare("DELETE FROM alerts WHERE token = ?").bind(token).run();
    return "off";
  }
  return "sent";
}

/** Megerősítés / leiratkozás a levélben lévő linkkel. Visszaad: { result, slug, locale } (slug null, ha nincs ilyen). */
export async function act(action, token) {
  if (!/^[a-f0-9]{48}$/.test(String(token || ""))) return { result: "expired", slug: null, locale: "hu" };
  const db = await getDB();
  await ensureAlerts(db);
  const row = await db.prepare(`SELECT a.id, a.email, a.locale, a.confirmed_at, p.slug FROM alerts a
                                LEFT JOIN product_summary p ON p.id = a.product_id WHERE a.token = ?`).bind(token).first();
  if (!row) return { result: "expired", slug: null, locale: "hu" };
  const base = { slug: row.slug || null, locale: row.locale || "hu" };
  if (action === "confirm") {
    if (!row.confirmed_at) await db.prepare("UPDATE alerts SET confirmed_at = ? WHERE id = ?").bind(now(), row.id).run();
    return { result: "ok", ...base };
  }
  if (action === "stopall") {
    await db.prepare("DELETE FROM alerts WHERE email = ?").bind(row.email).run();
    return { result: "stoppedAll", ...base };
  }
  await db.prepare("DELETE FROM alerts WHERE id = ?").bind(row.id).run();
  return { result: "stopped", ...base };
}
