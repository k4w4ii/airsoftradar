import Link from "next/link";
import { plainMoney, t, WEAPON_CATS } from "../lib/i18n";
import AutoSubmit from "./AutoSubmit";
import PriceSlider from "./PriceSlider";
import { Price, SpreadBar, StockBadge } from "./ui";

export const defaultCat = (q) => (q ? "all" : "weapons");

/** URL a jelenlegi szűrőkből, felülírásokkal. Lapozás minden szűrőváltozásnál az elejére ugrik. */
export function hrefFor(locale, params, over = {}) {
  const p = { ...params, page: 1, ...over };
  const sp = new URLSearchParams();
  if (p.q) sp.set("q", p.q);
  if (p.cat && p.cat !== defaultCat(p.q)) sp.set("cat", p.cat);
  for (const b of p.brands || []) sp.append("brand", b);
  if (p.min > 0) sp.set("min", String(p.min));
  if (p.max > 0) sp.set("max", String(p.max));
  if (p.stock) sp.set("stock", "1");
  if (p.sort && p.sort !== "popular") sp.set("sort", p.sort);
  if (p.page > 1) sp.set("page", String(p.page));
  const s = sp.toString();
  return `/${locale}${s ? `?${s}` : ""}`;
}

function niceStep(range) {
  const raw = range / 100;
  if (raw <= 1) return 1;
  const mag = 10 ** Math.floor(Math.log10(raw));
  return [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw);
}

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

function CategoryTree({ locale, params, counts }) {
  const tr = t(locale);
  const weapons = WEAPON_CATS.reduce((s, c) => s + (counts[c] || 0), 0);
  const all = weapons + (counts.other || 0);
  const item = (cat, n, cls = "") => (
    <li key={cat} className={cls}>
      <Link href={hrefFor(locale, params, { cat })} className={params.cat === cat ? "facet on" : n ? "facet" : "facet zero"}
            aria-current={params.cat === cat ? "true" : undefined}>
        <span>{tr.cats[cat]}</span><span className="n">{n}</span>
      </Link>
    </li>
  );
  return (
    <ul className="cat-tree">
      {item("all", all)}
      {item("weapons", weapons, "group")}
      <li>
        <ul className="sub">{WEAPON_CATS.map((c) => item(c, counts[c] || 0))}</ul>
      </li>
      {item("other", counts.other || 0)}
    </ul>
  );
}

function PriceFilter({ locale, params, facets, edges, edgeCurrency, currency, rates }) {
  const tr = t(locale);
  const cur = edgeCurrency;
  const rate = cur === "HUF" ? 1 : rates[cur];
  const fmt = (v) => plainMoney(v, cur, locale);
  const buckets = facets.buckets || {};
  const ranges = [
    { min: 0, max: edges[0], label: tr.under(fmt(edges[0])) },
    ...edges.slice(1).map((e, i) => ({ min: edges[i], max: e, label: `${fmt(edges[i])} – ${fmt(e)}` })),
    { min: edges[edges.length - 1], max: 0, label: tr.over(fmt(edges[edges.length - 1])) },
  ];
  const lo = facets.price?.min ? Math.floor(Number(facets.price.min) / rate) : 0;
  const hi = facets.price?.max ? Math.ceil(Number(facets.price.max) / rate) : 0;
  const step = niceStep(hi - lo);
  const loR = Math.floor(lo / step) * step;
  const hiR = Math.ceil(hi / step) * step;
  return (
    <>
      <ul className="facet-list">
        {ranges.map((r, i) => {
          const on = (params.min || 0) === r.min && (params.max || 0) === r.max;
          const n = buckets[String(i)] || 0;
          return (
            <li key={i}>
              <Link href={hrefFor(locale, params, on ? { min: 0, max: 0 } : { min: r.min, max: r.max })}
                    className={on ? "facet check on" : n ? "facet check" : "facet check zero"}
                    aria-current={on ? "true" : undefined}>
                <span className="box" aria-hidden="true" /><span>{r.label}</span><span className="n">{n}</span>
              </Link>
            </li>
          );
        })}
      </ul>
      <p className="facet-sub">{tr.customRange}</p>
      <PriceSlider key={`${loR}-${hiR}-${params.min}-${params.max}`} lo={loR} hi={hiR} step={step}
                   valueMin={params.min || null} valueMax={params.max || null}
                   labels={{ min: tr.min, max: tr.max, ok: tr.ok }} suffix={cur} />
    </>
  );
}

function BrandFilter({ locale, params, brands }) {
  const tr = t(locale);
  const selected = new Set(params.brands);
  const list = [...brands];
  for (const b of params.brands) if (!list.some((x) => x.name === b)) list.push({ name: b, n: 0 });
  const top = list.filter((b, i) => i < 10 || selected.has(b.name));
  const rest = list.filter((b, i) => i >= 10 && !selected.has(b.name));
  const box = (b) => (
    <li key={b.name}>
      <label className={b.n || selected.has(b.name) ? "facet check" : "facet check zero"}>
        <input type="checkbox" name="brand" value={b.name} defaultChecked={selected.has(b.name)} />
        <span className="box" aria-hidden="true" /><span>{b.name}</span><span className="n">{b.n}</span>
      </label>
    </li>
  );
  return (
    <>
      <ul className="facet-list">{top.map(box)}</ul>
      {rest.length ? (
        <details className="more">
          <summary>{tr.moreBrands(list.length)}</summary>
          <ul className="facet-list">{rest.map(box)}</ul>
        </details>
      ) : null}
    </>
  );
}

function Chips({ locale, params, currency }) {
  const tr = t(locale);
  const chips = [];
  if (params.q) chips.push({ label: `„${params.q}”`, href: hrefFor(locale, params, { q: "", cat: params.cat === "all" ? "weapons" : params.cat }) });
  if (params.cat !== defaultCat(params.q)) chips.push({ label: tr.cats[params.cat], href: hrefFor(locale, params, { cat: defaultCat(params.q) }) });
  for (const b of params.brands) chips.push({ label: b, href: hrefFor(locale, params, { brands: params.brands.filter((x) => x !== b) }) });
  if (params.min || params.max) {
    const lbl = `${params.min ? plainMoney(params.min, currency, locale) : "0"} – ${params.max ? plainMoney(params.max, currency, locale) : "∞"}`;
    chips.push({ label: lbl, href: hrefFor(locale, params, { min: 0, max: 0 }) });
  }
  if (params.stock) chips.push({ label: tr.inStockOnly, href: hrefFor(locale, params, { stock: false }) });
  if (!chips.length) return null;
  return (
    <div className="chips" aria-label={tr.activeFilters}>
      {chips.map((c) => (
        <Link key={c.label} href={c.href} className="chip" aria-label={tr.remove(c.label)}>{c.label}<span aria-hidden="true">×</span></Link>
      ))}
      {chips.length > 1 ? <Link href={`/${locale}`} className="chip-clear">{tr.clearFilters}</Link> : null}
    </div>
  );
}

export default function HomeView({ locale, currency, rates, stats, data, params }) {
  const tr = t(locale);
  const facets = data.facets || {};
  const heading = params.q ? `„${params.q}”` : params.cat === "weapons" && !params.brands.length ? tr.tagline(stats) : tr.cats[params.cat];

  return (
    <form id="filters" action={`/${locale}`} className="catalog">
      <AutoSubmit />
      {params.q ? <input type="hidden" name="q" value={params.q} /> : null}
      {params.cat !== defaultCat(params.q) ? <input type="hidden" name="cat" value={params.cat} /> : null}

      <input type="checkbox" id="ft" className="ft-toggle" />
      <label htmlFor="ft" className="ft-btn btn">{tr.filters}</label>

      <aside className="sidebar" aria-label={tr.filters}>
        <section className="fgroup">
          <h2>{tr.category}</h2>
          <CategoryTree locale={locale} params={params} counts={facets.categories || {}} />
        </section>
        <section className="fgroup">
          <h2>{tr.availability}</h2>
          <ul className="facet-list">
            <li>
              <label className="facet check">
                <input type="checkbox" name="stock" value="1" defaultChecked={params.stock} />
                <span className="box" aria-hidden="true" /><span>{tr.inStockOnly}</span><span className="n">{facets.in_stock ?? ""}</span>
              </label>
            </li>
          </ul>
        </section>
        <section className="fgroup">
          <h2>{tr.price}</h2>
          <PriceFilter locale={locale} params={params} facets={facets} edges={data.edges} edgeCurrency={data.edgeCurrency}
                       currency={currency} rates={rates} />
        </section>
        <section className="fgroup">
          <h2>{tr.brands}</h2>
          <BrandFilter locale={locale} params={params} brands={facets.brands || []} />
        </section>
        <button type="submit" className="btn apply-btn">{tr.showResults(data.total)}</button>
      </aside>

      <div className="results">
        <div className="results-head">
          <h1>{heading}</h1>
          <div className="results-bar">
            <span className="muted">{tr.results(data.total)}</span>
            <label className="sort">
              <span>{tr.sort}</span>
              <select name="sort" defaultValue={params.sort}>
                {Object.entries(tr.sorts).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
          </div>
          <Chips locale={locale} params={params} currency={data.edgeCurrency} />
        </div>

        {data.items.length ? (
          <ul className="rows">
            {data.items.map((p) => <ProductRow key={p.id} p={p} locale={locale} currency={currency} rates={rates} />)}
          </ul>
        ) : (
          <div className="empty">
            <p>{tr.noResults}</p>
            <Link href={`/${locale}`} className="btn">{tr.clearFilters}</Link>
          </div>
        )}

        {data.pages > 1 ? (
          <nav className="pager" aria-label="pagination">
            {data.page > 1 ? <Link href={hrefFor(locale, params, { page: data.page - 1 })} rel="prev">{tr.prev}</Link> : <span />}
            <span className="muted">{tr.page(data.page, data.pages)}</span>
            {data.page < data.pages ? <Link href={hrefFor(locale, params, { page: data.page + 1 })} rel="next">{tr.next}</Link> : <span />}
          </nav>
        ) : null}
      </div>
    </form>
  );
}
