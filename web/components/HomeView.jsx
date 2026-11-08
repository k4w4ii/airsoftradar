import Link from "next/link";
import { t } from "../lib/i18n";
import { Price, SpreadBar, StockBadge } from "./ui";

function ProductRow({ p, locale, currency, rates }) {
  const tr = t(locale);
  const best = p.best_price_huf ?? p.min_price_any_huf;
  return (
    <li className="row">
      <Link href={`/${locale}/p/${p.slug}`} className="row-link">
        <div className="thumb">
          {p.image_url ? <img src={p.image_url} alt="" loading="lazy" referrerPolicy="no-referrer" /> : null}
        </div>
        <div className="row-main">
          <span className="row-mfr">{p.manufacturer}</span>
          <span className="row-name">{p.name}</span>
          <span className="row-meta">
            <StockBadge stock={p.stock} locale={locale} />
            <span className="muted">{tr.shops(p.offer_count)}</span>
          </span>
        </div>
        <div className="row-spread">
          {p.offer_count > 1 ? <SpreadBar min={best} max={p.max_price_huf} locale={locale} /> : null}
        </div>
        <div className="row-price">
          {p.offer_count > 1 ? <span className="from">{tr.from}</span> : null}
          <Price huf={best} currency={currency} rates={rates} locale={locale} />
        </div>
      </Link>
    </li>
  );
}

export default function HomeView({ locale, currency, rates, stats, list, manufacturers, params }) {
  const tr = t(locale);
  const { q = "", mfr = "", stock = "", sort = "popular" } = params;
  const filtered = Boolean(q || mfr || stock || (sort && sort !== "popular"));
  const pageHref = (n) => {
    const sp = new URLSearchParams();
    if (q) sp.set("q", q);
    if (mfr) sp.set("mfr", mfr);
    if (stock) sp.set("stock", stock);
    if (sort && sort !== "popular") sp.set("sort", sort);
    if (n > 1) sp.set("page", String(n));
    const s = sp.toString();
    return `/${locale}${s ? `?${s}` : ""}`;
  };

  return (
    <>
      <section className="intro">
        <h1>{q ? `„${q}”` : tr.tagline(stats)}</h1>
      </section>

      <form className="filters" action={`/${locale}`}>
        {q ? <input type="hidden" name="q" value={q} /> : null}
        <label className="field">
          <span>{tr.manufacturer}</span>
          <select name="mfr" defaultValue={mfr}>
            <option value="">{tr.allManufacturers}</option>
            {manufacturers.map((m) => (
              <option key={m.manufacturer} value={m.manufacturer}>{m.manufacturer} ({m.products})</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>{tr.sort}</span>
          <select name="sort" defaultValue={sort}>
            {Object.entries(tr.sorts).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" name="stock" value="1" defaultChecked={stock === "1"} />
          <span>{tr.inStockOnly}</span>
        </label>
        <button type="submit" className="btn">{tr.apply}</button>
        {filtered ? <Link href={`/${locale}`} className="clear">{tr.clearFilters}</Link> : null}
        <span className="count muted">{tr.results(list.total)}</span>
      </form>

      {list.items.length ? (
        <ul className="rows">
          {list.items.map((p) => <ProductRow key={p.id} p={p} locale={locale} currency={currency} rates={rates} />)}
        </ul>
      ) : (
        <div className="empty">
          <p>{tr.noResults}</p>
          <Link href={`/${locale}`} className="btn">{tr.clearFilters}</Link>
        </div>
      )}

      {list.pages > 1 ? (
        <nav className="pager" aria-label="pagination">
          {list.page > 1 ? <Link href={pageHref(list.page - 1)} rel="prev">{tr.prev}</Link> : <span />}
          <span className="muted">{tr.page(list.page, list.pages)}</span>
          {list.page < list.pages ? <Link href={pageHref(list.page + 1)} rel="next">{tr.next}</Link> : <span />}
        </nav>
      ) : null}
    </>
  );
}
