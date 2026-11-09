import Link from "next/link";
import { CURRENCIES, money, t } from "../lib/i18n";
import { DOCS, FOOTER_LABELS } from "../lib/legal";
import { ADS, COFFEE_URL } from "../lib/site";
import AdSlot from "./AdSlot";
import SearchBox from "./SearchBox";

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

export function Shell({ locale, currency, path = "", children, query = "", hideSearch = false }) {
  const tr = t(locale);
  const other = locale === "hu" ? "en" : "hu";
  const curHref = (c) => `/cur?c=${c}&back=${encodeURIComponent(path || `/${locale}`)}`;
  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link href={`/${locale}`} className="brand">
            <Logo />
            <span>AirsoftHunter</span>
          </Link>
          {hideSearch ? <span className="topsearch-gap" /> : (
            <SearchBox locale={locale} defaultValue={query} placeholder={tr.searchPlaceholder} label={tr.search}
                       button={tr.search} allText={tr.allResultsFor} />
          )}
          <nav className="toolbar" aria-label={tr.currency}>
            <div className="seg" role="group" aria-label={tr.currency}>
              {CURRENCIES.map((c) => (
                <a key={c} href={curHref(c)}
                   className={c === currency ? "on" : undefined} aria-current={c === currency ? "true" : undefined}>
                  {c}
                </a>
              ))}
            </div>
            {/* mobilon a pénznem lenyíló menü, hogy a logó mellett elférjen az oldal neve */}
            <details className="cur-menu">
              <summary aria-label={tr.currency}>{currency}</summary>
              <div className="cur-pop">
                {CURRENCIES.map((c) => (
                  <a key={c} href={curHref(c)} className={c === currency ? "on" : undefined}>{c}</a>
                ))}
              </div>
            </details>
            <Link href={`/${other}`} className="lang" hrefLang={other} lang={other}>{tr.otherLang}</Link>
          </nav>
        </div>
      </header>
      <main className="page">{children}</main>
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Link href={`/${locale}`} className="brand small-brand"><Logo /><span>AirsoftHunter</span></Link>
            <p>{tr.footer}</p>
          </div>
          <nav className="footer-links" aria-label={locale === "hu" ? "Jogi információk" : "Legal"}>
            {Object.keys(DOCS).map((d) => (
              <Link key={d} href={`/${locale}/${DOCS[d][locale]}`}>{FOOTER_LABELS[locale === "hu" ? "hu" : "en"][d]}</Link>
            ))}
          </nav>
        </div>
        <div className="footer-copy">
          <span>© {new Date().getFullYear()} AirsoftHunter</span>
          {COFFEE_URL ? (
            <a className="coffee" href={COFFEE_URL} target="_blank" rel="noopener">
              <CoffeeIcon />
              {locale === "hu" ? "Hasznos az oldal? Hívj meg egy kávéra" : "Find it useful? Buy me a coffee"}
            </a>
          ) : null}
        </div>
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

function CoffeeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="coffee-icon">
      <path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V9Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M16 11h1.5a2.5 2.5 0 0 1 0 5H16" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 3.5c0 1 1 1.5 1 2.5M12 3.5c0 1 1 1.5 1 2.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

/** Hirdetési hely. Ha nincs beállítva hirdetéskód vagy egység-azonosító, semmit nem renderel. */
export function Ad({ place, locale }) {
  const slot = ADS.slots[place];
  if (!ADS.client || !slot) return null;
  return <AdSlot client={ADS.client} slot={slot} label={locale === "hu" ? "Hirdetés" : "Advertisement"} />;
}
