"""
Ár- és készletfigyelő: a napi frissítés végén megnézi a megerősített értesítéseket, és e-mailt küld, ha
  - stock: a termék újra raktáron van bármelyik figyelt boltban (in_stock_count > 0);
  - price: a legjobb (raktáron lévő) ár a célár alá esett.
Egy értesítés egyszer szól (utána kész; a termékoldalon újra kérhető). Adattakarékosság: a meg nem erősített
kéréseket 7 nap, a teljesülteket 30 nap, a többit 1 év után törli.
A feliratkozás és a megerősítés a weboldalon fut (web/lib/alerts.js, web/app/api/alert/route.js).

Env: RESEND_API_KEY vagy BREVO_API_KEY (nélküle kihagyja magát), MAIL_FROM, ALERT_MAX_MAILS (alapból 90 / futás).
Futtatás: a daily-scrape végén magától; helyben: python scraper/alerts.py. Csak stdlib.
"""
from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

SITE = "https://www.airsofthunter.com"
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS alerts (
     id INTEGER PRIMARY KEY, email TEXT NOT NULL, product_id INTEGER NOT NULL, kind TEXT NOT NULL,
     target_huf REAL, target_amount REAL, currency TEXT, locale TEXT NOT NULL DEFAULT 'hu',
     token TEXT NOT NULL UNIQUE, ip_hash TEXT, created_at TEXT NOT NULL, confirmed_at TEXT, sent_at TEXT)""",
    "CREATE UNIQUE INDEX IF NOT EXISTS alerts_one ON alerts (email, product_id, kind)",
    "CREATE INDEX IF NOT EXISTS alerts_ip ON alerts (ip_hash, created_at)",
]

TXT = {
    "hu": {
        "stock_subject": "Újra raktáron: {name}",
        "stock_title": "Újra raktáron!",
        "stock_text": "A(z) „{name}” újra kapható: legjobb ár most {price}, {n} boltban raktáron.",
        "price_subject": "Árcsökkenés: {name} most {price}",
        "price_title": "Elérte a célárat!",
        "price_text": "A(z) „{name}” legjobb ára most {price} (a célárad: {target}).",
        "button": "Megnézem az ajánlatokat",
        "note": "Ez egyszeri értesítés volt. Ha újra figyelnéd, a termékoldalon kérhetsz újat. Az árak tájékoztató jellegűek: vásárlás előtt ellenőrizd a bolt oldalán.",
        "footer": 'Ezt a levelet azért kaptad, mert értesítést kértél az AirsoftHunteren. <a href="{stopall}">Leiratkozás az összes értesítésről</a>',
    },
    "en": {
        "stock_subject": "Back in stock: {name}",
        "stock_title": "Back in stock!",
        "stock_text": "“{name}” is available again: best price now {price}, in stock at {n} shop(s).",
        "price_subject": "Price drop: {name} now {price}",
        "price_title": "Your target price is reached!",
        "price_text": "The best price of “{name}” is now {price} (your target: {target}).",
        "button": "See the offers",
        "note": "This was a one-time alert. To keep watching, request a new one on the product page. Prices are indicative: check the shop's page before buying.",
        "footer": 'You received this email because you requested an alert on AirsoftHunter. <a href="{stopall}">Unsubscribe from all alerts</a>',
    },
}


def money(huf: float, currency: str, rates: dict, locale: str) -> str:
    rate = 1.0 if currency == "HUF" else rates.get(currency)
    if not rate:
        currency, rate = "HUF", 1.0
    v = huf / rate
    if currency in ("HUF", "CZK"):
        num = f"{round(v):,}".replace(",", " ")
    else:
        num = f"{v:,.2f}".replace(",", " ")
        if locale == "hu":
            num = num.replace(".", ",")
    sym = {"HUF": "Ft", "EUR": "€", "PLN": "zł", "CZK": "Kč", "GBP": "£"}.get(currency, currency)
    return f"£{num}" if currency == "GBP" else f"{num} {sym}"


def due(alert: dict) -> bool:
    """Teljesült-e a feltétel."""
    if alert.get("slug") is None:
        return False                                      # a termék (most) nincs az összesítőben
    if alert["kind"] == "stock":
        return (alert.get("in_stock_count") or 0) > 0
    best = alert.get("best_price_huf")
    return best is not None and alert.get("target_huf") is not None and best <= alert["target_huf"]


def build_mail(alert: dict, rates: dict) -> dict:
    loc = alert.get("locale") if alert.get("locale") in TXT else "en"
    T, cur = TXT[loc], alert.get("currency") or ("HUF" if loc == "hu" else "EUR")
    name = alert["name"]
    price = money(alert["best_price_huf"], cur, rates, loc) if alert.get("best_price_huf") is not None else "–"
    url = f"{SITE}/{loc}/p/{alert['slug']}"
    stop = f"{SITE}/api/alert?a=stop&t={alert['token']}"
    stopall = f"{SITE}/api/alert?a=stopall&t={alert['token']}"
    if alert["kind"] == "stock":
        subject, title = T["stock_subject"].format(name=name), T["stock_title"]
        text = T["stock_text"].format(name=name, price=price, n=alert.get("in_stock_count") or 1)
    else:
        target = money(alert["target_huf"], cur, rates, loc)
        subject, title = T["price_subject"].format(name=name, price=price), T["price_title"]
        text = T["price_text"].format(name=name, price=price, target=target)
    e = html.escape
    body = f"""<!doctype html><html><body style="margin:0;background:#f4f3ef;font-family:Arial,Helvetica,sans-serif;color:#1f1f1c">
<div style="max-width:560px;margin:0 auto;padding:24px">
<p style="font-weight:bold;font-size:18px;margin:0 0 16px">AIRSOFT<span style="color:#b38b3c">HUNTER</span></p>
<div style="background:#fff;border-radius:10px;padding:24px">
<h1 style="font-size:20px;margin:0 0 12px">{e(title)}</h1>
<p style="line-height:1.5;margin:0 0 12px">{e(text)}</p>
<p style="margin:20px 0"><a href="{e(url)}" style="background:#b38b3c;color:#fff;text-decoration:none;padding:12px 20px;border-radius:8px;display:inline-block;font-weight:bold">{e(T['button'])}</a></p>
<p style="line-height:1.5;margin:0;color:#77756d;font-size:13px">{e(T['note'])}</p>
</div>
<p style="font-size:12px;color:#77756d;line-height:1.5;margin:16px 0 0">{T['footer'].format(stopall=e(stopall))}</p>
</div></body></html>"""
    return {"to": alert["email"], "subject": subject[:180], "html": body, "text": f"{text}\n\n{url}\n\n{T['note']}\n{stopall}",
            "headers": {"List-Unsubscribe": f"<{stop}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}}


def send(mail: dict, opener=urllib.request.urlopen) -> bool:
    frm = os.environ.get("MAIL_FROM", "").strip() or "AirsoftHunter <ertesito@airsofthunter.com>"
    if os.environ.get("RESEND_API_KEY", "").strip():
        url, headers = "https://api.resend.com/emails", {"Authorization": f"Bearer {os.environ['RESEND_API_KEY'].strip()}"}
        payload = {"from": frm, "to": [mail["to"]], "subject": mail["subject"], "html": mail["html"], "text": mail["text"],
                   "headers": mail["headers"]}
    elif os.environ.get("BREVO_API_KEY", "").strip():
        name, _, addr = frm.rpartition("<")
        url, headers = "https://api.brevo.com/v3/smtp/email", {"api-key": os.environ["BREVO_API_KEY"].strip()}
        payload = {"sender": {"name": name.strip() or "AirsoftHunter", "email": addr.rstrip(">").strip() or frm},
                   "to": [{"email": mail["to"]}], "subject": mail["subject"], "htmlContent": mail["html"],
                   "textContent": mail["text"], "headers": mail["headers"]}
    else:
        return False
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={**headers, "Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "AirsoftHunter/1.0"})
    try:
        with opener(req, timeout=30) as r:
            return 200 <= r.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[alerts] küldési hiba: {e}", flush=True)
        return False


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def run(db, sender=send, now: datetime | None = None, max_mails: int = 90) -> dict:
    now = now or datetime.now(timezone.utc)
    db.execute([(s, []) for s in SCHEMA])
    db.execute([
        ("DELETE FROM alerts WHERE confirmed_at IS NULL AND created_at < ?", [_iso(now - timedelta(days=7))]),
        ("DELETE FROM alerts WHERE sent_at IS NOT NULL AND sent_at < ?", [_iso(now - timedelta(days=30))]),
        ("DELETE FROM alerts WHERE created_at < ?", [_iso(now - timedelta(days=365))]),
    ])
    rows = db.query("""SELECT a.id, a.email, a.kind, a.target_huf, a.currency, a.locale, a.token,
                              p.slug, p.name, p.best_price_huf, p.in_stock_count
                       FROM alerts a LEFT JOIN product_summary p ON p.id = a.product_id
                       WHERE a.confirmed_at IS NOT NULL AND a.sent_at IS NULL""")
    rates = {r["currency"].strip(): float(r["huf_per_unit"]) for r in db.query("SELECT currency, huf_per_unit FROM latest_rates")}
    todo = [a for a in rows if due(a)]
    sent, failed = [], 0
    for a in todo[:max_mails]:
        if sender(build_mail(a, rates)):
            sent.append(a["id"])
        else:
            failed += 1
    for i in range(0, len(sent), 80):
        part = sent[i:i + 80]
        db.execute([(f"UPDATE alerts SET sent_at = ? WHERE id IN ({','.join('?' * len(part))})", [_iso(now), *part])])
    return {"aktiv": len(rows), "teljesult": len(todo), "elkuldve": len(sent), "hiba": failed,
            "maradt": max(0, len(todo) - max_mails)}


def main() -> int:
    if not (os.environ.get("RESEND_API_KEY", "").strip() or os.environ.get("BREVO_API_KEY", "").strip()):
        print("[alerts] nincs e-mail kulcs (RESEND_API_KEY / BREVO_API_KEY) – kihagyva", flush=True)
        return 0
    from db import get_db
    stats = run(get_db(), max_mails=int(os.environ.get("ALERT_MAX_MAILS", "90")))
    line = f"Értesítők: {stats['aktiv']} aktív, {stats['teljesult']} teljesült, {stats['elkuldve']} elküldve, {stats['hiba']} hiba"
    print(f"[alerts] {stats}", flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(f"## Ár- és készletfigyelő\n\n{line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
