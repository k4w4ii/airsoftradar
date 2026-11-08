import Link from "next/link";
import { CURRENCIES, money, t } from "../lib/i18n";

export function Logo() {
  // Irányzék: osztott szálkereszt, a középpont sárgaréz (a „találat” = a legjobb ár)
  return (
    <svg className="logo-mark" viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="12" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M16 1.5v8M16 22.5v8M1.5 16h8M22.5 16h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="16" r="2.6" fill="var(--brass)" />
    </svg>
  );
}

export function Shell({ locale, currency, path = "", children, query = "" }) {
  const tr = t(locale);
  const other = locale === "hu" ? "en" : "hu";
  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link href={`/${locale}`} className="brand">
            <Logo />
            <span>AirsoftHunter</span>
          </Link>
          <form action={`/${locale}`} className="topsearch" role="search">
            <input name="q" type="search" defaultValue={query} placeholder={tr.searchPlaceholder} aria-label={tr.search} />
            <button type="submit">{tr.search}</button>
          </form>
          <nav className="toolbar" aria-label={tr.currency}>
            <div className="seg" role="group" aria-label={tr.currency}>
              {CURRENCIES.map((c) => (
                <a key={c} href={`/cur?c=${c}&back=${encodeURIComponent(path || `/${locale}`)}`}
                   className={c === currency ? "on" : undefined} aria-current={c === currency ? "true" : undefined}>
                  {c}
                </a>
              ))}
            </div>
            <Link href={`/${other}`} className="lang" hrefLang={other} lang={other}>{tr.otherLang}</Link>
          </nav>
        </div>
      </header>
      <main className="page">{children}</main>
      <footer className="footer">
        <p>{tr.footer}</p>
      </footer>
    </div>
  );
}

export function StockBadge({ stock, locale }) {
  return <span className={`stock stock-${stock}`}>{t(locale).stock[stock] || stock}</span>;
}

/** Árfolyosó: a teljes sáv a legdrágább bolt ára, a sárgaréz rész a legolcsóbb. A maradék a megtakarítás. */
export function SpreadBar({ min, max, locale }) {
  if (!min || !max || max <= min) return null;
  const pct = Math.round((1 - min / max) * 100);
  if (pct < 1) return null;
  return (
    <div className="spread" title={t(locale).save(pct)}>
      <div className="spread-track">
        <div className="spread-fill" style={{ width: `${(min / max) * 100}%` }} />
      </div>
      <span className="spread-label">−{pct}%</span>
    </div>
  );
}

export function Price({ huf, currency, rates, locale, className = "price" }) {
  return <span className={className}>{money(huf, currency, rates, locale)}</span>;
}
