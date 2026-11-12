import { DOCS } from "../lib/legal";
import { t } from "../lib/i18n";

/** Ár- és készletfigyelő űrlap (JavaScript nélkül is működik: sima POST, a szerver visszairányít ide). */
export default function AlertBox({ product, locale, currency, rates, status }) {
  const tr = t(locale);
  const out = !(product.in_stock_count > 0);
  const rate = currency === "HUF" ? 1 : rates?.[currency] || null;
  const best = product.best_price_huf ?? product.min_price_any_huf;
  const step = currency === "HUF" || currency === "CZK" ? 100 : 1;
  const suggest = best && rate ? Math.max(step, Math.floor((best * 0.9) / rate / step) * step) : "";
  const msg = status && tr.alertMsg[status];
  return (
    <section className="block alert-box" id="alert">
      <h2>{tr.alertTitle}</h2>
      {msg ? <p className={`alert-msg ${["sent", "ok", "stopped", "stoppedAll"].includes(status) ? "good" : "bad"}`} role="status">{msg}</p> : null}
      <form method="post" action="/api/alert" className="alert-form">
        <input type="hidden" name="slug" value={product.slug} />
        <input type="hidden" name="locale" value={locale} />
        <input type="hidden" name="cur" value={currency} />
        <div className="hp" aria-hidden="true"><label>Website <input type="text" name="website" tabIndex={-1} autoComplete="off" /></label></div>
        {out ? (
          <label className="alert-kind">
            <input type="radio" name="kind" value="stock" defaultChecked /> <span>{tr.alertStock}</span>
          </label>
        ) : null}
        <label className="alert-kind">
          <input type="radio" name="kind" value="price" defaultChecked={!out} /> <span>{tr.alertPrice}</span>
          <span className="alert-target">
            <input type="number" name="target" min={step} step={step} defaultValue={suggest} inputMode="decimal" aria-label={tr.alertPrice} />
            <span className="muted">{currency}</span>
          </span>
        </label>
        <div className="alert-row">
          <input type="email" name="email" required maxLength={254} placeholder={tr.alertEmail} aria-label={tr.alertEmail} autoComplete="email" />
          <button type="submit" className="btn">{tr.alertSubmit}</button>
        </div>
        <p className="muted small">
          {tr.alertNote} <a href={`/${locale}/${DOCS.privacy[locale]}`}>{tr.alertPrivacy}</a>
        </p>
      </form>
    </section>
  );
}
