import Link from "next/link";
import { CURRENCIES, money, t } from "../lib/i18n";
import { DOCS, FOOTER_LABELS } from "../lib/legal";
import { ADS, COFFEE_URL } from "../lib/site";
import AdSlot from "./AdSlot";
import SearchBox from "./SearchBox";

export function Logo() {
  // Irányzék + sas (public/logo-mark.png maszkként: a szín a témából jön, világos és sötét módban is)
  return <span className="logo-mark" aria-hidden="true" />;
}

// Szóvédjegy: AIRSOFT / HUNTER.com két sorban
export function Wordmark() {
  return (
    <span className="wordmark">
      <span className="wm-top">AIRSOFT</span>
      <span className="wm-bottom">HUNTER<span className="wm-dot">.com</span></span>
    </span>
  );
}

// Világos/sötét váltó: két link, a CSS mindig csak a másik témára váltót mutatja (JS nélkül is működik)
function ThemeToggle({ locale, back }) {
  const href = (t) => `/theme?t=${t}&back=${encodeURIComponent(back)}`;
  const hu = locale === "hu";
  return (
    <>
      <a href={href("dark")} className="theme-btn to-dark" rel="nofollow" title={hu ? "Sötét mód" : "Dark mode"} aria-label={hu ? "Sötét mód" : "Dark mode"}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" />
        </svg>
      </a>
      <a href={href("light")} className="theme-btn to-light" rel="nofollow" title={hu ? "Világos mód" : "Light mode"} aria-label={hu ? "Világos mód" : "Light mode"}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      </a>
    </>
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
            <Wordmark />
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
            <ThemeToggle locale={locale} back={path || `/${locale}`} />
            <Link href={`/${other}`} className="lang" hrefLang={other} lang={other}>{tr.otherLang}</Link>
          </nav>
        </div>
      </header>
      <main className="page">{children}</main>
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Link href={`/${locale}`} className="brand small-brand" aria-label="AirsoftHunter"><Logo /><Wordmark /></Link>
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
export function SpreadBar({ min, max, locale, currency, rates }) {
  if (!min || !max || max <= min) return null;
  const pct = Math.round((1 - min / max) * 100);
  if (pct < 1) return null;
  const tr = t(locale);
  return (
    <div className="spread" title={tr.saveUpToNote}>
      <div className="spread-track">
        <div className="spread-fill" style={{ width: `${(min / max) * 100}%` }} />
      </div>
      <span className="spread-label">{tr.saveUpTo(money(max - min, currency, rates, locale), pct)}</span>
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
