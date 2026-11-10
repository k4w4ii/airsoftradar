import Link from "next/link";
import { CAT_GROUPS, defaultCats, hrefFor, PLATFORMS, withoutCat } from "../lib/catalog";
import { money, plainMoney, t } from "../lib/i18n";
import AutoSubmit from "./AutoSubmit";
import PriceSlider from "./PriceSlider";
import { Ad, Price, SpreadBar, StockBadge } from "./ui";

export { hrefFor } from "../lib/catalog";

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
          {p.offer_count > 1 ? <SpreadBar min={best} max={p.max_price_huf} locale={locale} currency={currency} rates={rates} /> : null}
        </div>
        <div className="row-price">
          {p.offer_count > 1 ? <span className="from">{tr.from}</span> : null}
          <Price huf={best} currency={currency} rates={rates} locale={locale} />
        </div>
      </Link>
    </li>
  );
}

/** Csempe-nézet kártyája: kép, árkülönbség-jelvény, márka, név, készlet, „már X Ft”. */
export function ProductTile({ p, locale, currency, rates }) {
  const tr = t(locale);
  const best = p.best_price_huf ?? p.min_price_any_huf;
  const pct = p.offer_count > 1 && p.max_price_huf > best ? Math.round((1 - best / p.max_price_huf) * 100) : 0;
  return (
    <li className="tile">
      <Link href={`/${locale}/p/${p.slug}`} className="tile-link">
        <div className="tile-img">
          {p.image_url ? <img src={p.image_url} alt="" loading="lazy" referrerPolicy="no-referrer" /> : null}
        </div>
        <div className="tile-body">
          <span className="row-mfr">{p.manufacturer}</span>
          <span className="tile-name">{p.name}</span>
          <span className="row-meta">
            <StockBadge stock={p.stock} locale={locale} />
            <span className="muted">{tr.shops(p.offer_count)}</span>
          </span>
          <span className="tile-price">
            {p.offer_count > 1 ? <span className="from">{tr.from}</span> : null}
            <Price huf={best} currency={currency} rates={rates} locale={locale} />
          </span>
          {pct >= 1 ? (
            <span className="tile-save" title={tr.saveUpToNote}>
              {tr.saveUpTo(money(p.max_price_huf - best, currency, rates, locale), pct)}
            </span>
          ) : null}
        </div>
      </Link>
    </li>
  );
}

function ViewToggle({ locale, params }) {
  const tr = t(locale);
  const icon = { grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z", list: "M3 4h18v3H3zM3 10.5h18v3H3zM3 17h18v3H3z" };
  return (
    <div className="views seg" role="group" aria-label={tr.view}>
      {["grid", "list"].map((v) => (
        <Link key={v} href={hrefFor(locale, params, { view: v, page: params.page })} className={params.view === v ? "on" : undefined}
              aria-current={params.view === v ? "true" : undefined} title={tr.views[v]} aria-label={tr.views[v]}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d={icon[v]} fill="currentColor" /></svg>
        </Link>
      ))}
    </div>
  );
}

function CategoryTree({ locale, params, counts }) {
  const tr = t(locale);
  const sel = new Set(params.cats);
  const total = Object.values(counts).reduce((x, y) => x + y, 0);
  const box = (name, value, label, n, on, data) => (
    <label className={n || on ? "facet check" : "facet check zero"}>
      <input type="checkbox" name={name} value={value} defaultChecked={on} {...data} />
      <span className="box" aria-hidden="true" /><span>{label}</span><span className="n">{n}</span>
    </label>
  );
  return (
    <ul className="cat-tree">
      <li>
        <Link href={hrefFor(locale, params, { cats: [] })} className={params.cats.length ? "facet" : "facet on"}
              aria-current={params.cats.length ? undefined : "true"}>
          <span>{tr.cats.all}</span><span className="n">{total}</span>
        </Link>
      </li>
      {CAT_GROUPS.map((g) => {
        const n = g.leaves.reduce((x, l) => x + (counts[l] || 0), 0);
        const gOn = sel.has(g.id);
        const open = gOn || g.leaves.some((l) => sel.has(l)) || (g.id === "weapons" && !params.cats.length);
        return (
          <li key={g.id} className={open ? "group open" : "group"}>
            <div className="group-row">
              {box("cat", g.id, tr.cats[g.id], n, gOn, { "data-group": g.id })}
              <button type="button" className="twisty" data-twisty aria-expanded={open ? "true" : "false"}
                      aria-label={tr.cats[g.id]} />
            </div>
            <ul className="sub">
              {g.leaves.map((l) => (
                <li key={l}>{box("cat", l, tr.cats[l], counts[l] || 0, gOn || sel.has(l), { "data-parent": g.id })}</li>
              ))}
            </ul>
          </li>
        );
      })}
    </ul>
  );
}

function PlatformFilter({ locale, params, counts }) {
  const tr = t(locale);
  const sel = new Set(params.plats);
  const items = PLATFORMS.filter((p) => counts[p] || sel.has(p)).sort((a, b) => (counts[b] || 0) - (counts[a] || 0));
  if (!items.length) return null;
  const top = items.filter((p, i) => i < 6 || sel.has(p));
  const rest = items.filter((p, i) => i >= 6 && !sel.has(p));
  const box = (p) => (
    <li key={p}>
      <label className={counts[p] || sel.has(p) ? "facet check" : "facet check zero"}>
        <input type="checkbox" name="plat" value={p} defaultChecked={sel.has(p)} />
        <span className="box" aria-hidden="true" /><span>{tr.plats[p]}</span><span className="n">{counts[p] || 0}</span>
      </label>
    </li>
  );
  return (
    <section className="fgroup">
      <h2>{tr.platform}</h2>
      <ul className="facet-list">{top.map(box)}</ul>
      {rest.length ? (
        <details className="more">
          <summary>{tr.morePlatforms(items.length)}</summary>
          <ul className="facet-list">{rest.map(box)}</ul>
        </details>
      ) : null}
    </section>
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
  if (params.q) chips.push({ label: `„${params.q}”`, href: hrefFor(locale, params, { q: "", cats: params.cats.length ? params.cats : defaultCats("") }) });
  const isDefault = params.cats.join() === defaultCats(params.q).join();
  if (!isDefault) for (const c of params.cats) chips.push({ label: tr.cats[c], href: hrefFor(locale, params, { cats: withoutCat(params.cats, c) }) });
  for (const p of params.plats) chips.push({ label: tr.plats[p], href: hrefFor(locale, params, { plats: params.plats.filter((x) => x !== p) }) });
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
      {chips.length > 1 ? <Link href={`/${locale}?cat=weapons`} className="chip-clear">{tr.clearFilters}</Link> : null}
    </div>
  );
}

export default function HomeView({ locale, currency, rates, data, params }) {
  const tr = t(locale);
  const facets = data.facets || {};
  const names = params.cats.map((c) => tr.cats[c]);
  const heading = params.q ? `„${params.q}”` : !names.length ? tr.cats.all
    : names.length > 2 ? `${names.slice(0, 2).join(", ")} +${names.length - 2}` : names.join(", ");

  return (
    <form id="filters" action={`/${locale}`} className="catalog">
      <AutoSubmit />
      {params.q ? <input type="hidden" name="q" value={params.q} /> : null}
      {params.view !== "grid" ? <input type="hidden" name="view" value={params.view} /> : null}
      {/* ha minden kategória-pipa üres: „minden termék” (nem az alapértelmezés) */}
      <input type="hidden" name="cat" value="all" />

      <input type="checkbox" id="ft" className="ft-toggle" />
      <label htmlFor="ft" className="ft-btn btn">{tr.filters}</label>

      <aside className="sidebar" aria-label={tr.filters}>
        <section className="fgroup">
          <h2>{tr.category}</h2>
          <CategoryTree locale={locale} params={params} counts={facets.categories || {}} />
        </section>
        <PlatformFilter locale={locale} params={params} counts={facets.platforms || {}} />
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
            <div className="bar-right">
            <ViewToggle locale={locale} params={params} />
            <label className="sort">
              <span>{tr.sort}</span>
              <select name="sort" defaultValue={params.sort}>
                {Object.entries(tr.sorts).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            </div>
          </div>
          <Chips locale={locale} params={params} currency={data.edgeCurrency} />
        </div>

        {data.items.length ? (
          params.view === "list" ? (
            <ul className="rows">
              {data.items.map((p) => <ProductRow key={p.id} p={p} locale={locale} currency={currency} rates={rates} />)}
            </ul>
          ) : (
            <ul className="tiles">
              {data.items.map((p) => <ProductTile key={p.id} p={p} locale={locale} currency={currency} rates={rates} />)}
            </ul>
          )
        ) : (
          <div className="empty">
            <p>{tr.noResults}</p>
            <Link href={`/${locale}?cat=weapons`} className="btn">{tr.clearFilters}</Link>
          </div>
        )}

        {data.items.length ? <Ad place="list" locale={locale} /> : null}

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
