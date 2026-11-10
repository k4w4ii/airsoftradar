import { translateTitle } from "../lib/dictionary";
import { shopTarget } from "../lib/links";
import Link from "next/link";
import { dateFmt, money, shopMoney, t } from "../lib/i18n";
import { Ad, Price, StockBadge } from "./ui";

/** Árdiagram SVG-ben (külső könyvtár nélkül). points: [{ observed_on, min_huf }] */
export function PriceChart({ points, currency, rates, locale }) {
  const tr = t(locale);
  if (!points || points.length < 2) return <p className="muted chart-empty">{tr.historyEmpty}</p>;
  const W = 640, H = 180, PX = 8, PY = 18;
  const vals = points.map((p) => Number(p.min_huf));
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = hi - lo || hi * 0.05 || 1;
  const x = (i) => PX + (i * (W - 2 * PX)) / (points.length - 1);
  const y = (v) => PY + (1 - (v - lo) / span) * (H - 2 * PY);
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(vals[i]).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1).toFixed(1)},${H} L${x(0).toFixed(1)},${H} Z`;
  const minI = vals.indexOf(lo);
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${tr.history}: ${money(lo, currency, rates, locale)} – ${money(hi, currency, rates, locale)}`}>
        <path d={area} className="chart-area" />
        <path d={line} className="chart-line" />
        <circle cx={x(minI)} cy={y(lo)} r="4" className="chart-dot" />
      </svg>
      <figcaption>
        <span>{points[0].observed_on}</span>
        <span className="chart-range">
          <span>min <b>{money(lo, currency, rates, locale)}</b></span>
          <span>max <b>{money(hi, currency, rates, locale)}</b></span>
        </span>
        <span>{points[points.length - 1].observed_on}</span>
      </figcaption>
    </figure>
  );
}

function OfferLadder({ offers, currency, rates, locale, odd = false, scaleMax }) {
  const tr = t(locale);
  const max = scaleMax || Math.max(...offers.map((o) => Number(o.price_huf)));
  const perShop = offers.reduce((m, o) => ({ ...m, [o.shop_name]: (m[o.shop_name] || 0) + 1 }), {});
  return (
    <ol className="ladder">
      {offers.map((o, i) => (
        <li key={o.id} className={odd ? "rung odd" : i === 0 && o.stock === "in_stock" ? "rung best" : "rung"}>
          <div className="rung-shop">
            <span className="shop-name">{o.shop_name}</span>
            <span className="cc">{o.shop_country}</span>
            <StockBadge stock={o.stock} locale={locale} />
            {perShop[o.shop_name] > 1 || odd ? <span className="variant muted">{translateTitle(o.title_raw, locale)}</span> : null}
          </div>
          <div className="rung-bar" aria-hidden="true">
            <div style={{ width: `${Math.min(100, Math.max(4, (Number(o.price_huf) / max) * 100))}%` }} />
          </div>
          <div className="rung-price">
            <Price huf={o.price_huf} currency={currency} rates={rates} locale={locale} />
            {o.currency !== currency ? (
              <span className="orig muted" title={tr.original}>{shopMoney(o.price, o.currency, locale)}</span>
            ) : null}
          </div>
          {/* közvetlen bolti link (nincs köztes átirányítás); Referer nélkül, utm-jelöléssel vagy partnersablonnal */}
          <a className="btn go" href={shopTarget(o.url, o.affiliate_template) || `/go/${o.id}`}
             rel="nofollow sponsored noopener noreferrer" referrerPolicy="no-referrer" target="_blank">{tr.goToShop}</a>
        </li>
      ))}
    </ol>
  );
}

export default function ProductView({ locale, currency, rates, product, offers: all, history }) {
  const tr = t(locale);
  // gyanús ár (alkatrész vagy átépített változat): külön, a legjobb árba nem számít bele
  const offers = all.filter((o) => !o.is_outlier);
  const odd = all.filter((o) => o.is_outlier);
  const scale = Math.max(1, ...offers.map((o) => Number(o.price_huf)));
  const best = product.best_price_huf ?? product.min_price_any_huf;
  const pct = product.max_price_huf && best ? Math.round((1 - best / product.max_price_huf) * 100) : 0;
  return (
    <article className="product">
      <Link href={`/${locale}?cat=weapons`} className="back">{tr.back}</Link>
      <div className="product-head">
        <div className="product-img">
          {product.image_url ? <img src={product.image_url} alt={product.name} referrerPolicy="no-referrer" /> : null}
        </div>
        <div className="product-info">
          <span className="row-mfr">{product.manufacturer}</span>
          <h1>{product.name}</h1>
          <div className="best">
            <span className="muted">{tr.bestPrice}</span>
            <Price huf={best} currency={currency} rates={rates} locale={locale} className="price big" />
            <StockBadge stock={product.stock} locale={locale} />
          </div>
          {pct >= 1 && offers.length > 1 ? (
            <p className="saving">
              {tr.saveUpTo(money(product.max_price_huf - best, currency, rates, locale), pct)}
              <span className="muted small"> – {tr.saveUpToNote}</span>
            </p>
          ) : null}
          {product.updated_at ? <p className="muted small">{tr.updated}: {dateFmt(product.updated_at, locale)}</p> : null}
        </div>
      </div>

      <section className="block">
        <h2>{tr.offers}</h2>
        <p className="muted">{tr.offersIntro(offers.length)}</p>
        <OfferLadder offers={offers} currency={currency} rates={rates} locale={locale} />
        {odd.length ? (
          <details className="odd-offers">
            <summary>{tr.oddOffers(odd.length)}</summary>
            <p className="muted small">{tr.oddOffersNote}</p>
            <OfferLadder offers={odd} currency={currency} rates={rates} locale={locale} odd scaleMax={scale} />
          </details>
        ) : null}
      </section>

      <section className="block">
        <h2>{tr.history}</h2>
        <PriceChart points={history} currency={currency} rates={rates} locale={locale} />
      </section>

      <Ad key={product.slug} place="product" locale={locale} />
    </article>
  );
}
