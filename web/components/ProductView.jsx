import Link from "next/link";
import { dateFmt, money, shopMoney, t } from "../lib/i18n";
import { Price, StockBadge } from "./ui";

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

function OfferLadder({ offers, currency, rates, locale }) {
  const tr = t(locale);
  const max = Math.max(...offers.map((o) => Number(o.price_huf)));
  return (
    <ol className="ladder">
      {offers.map((o, i) => (
        <li key={o.id} className={i === 0 && o.stock === "in_stock" ? "rung best" : "rung"}>
          <div className="rung-shop">
            <span className="shop-name">{o.shop_name}</span>
            <span className="cc">{o.shop_country}</span>
            <StockBadge stock={o.stock} locale={locale} />
          </div>
          <div className="rung-bar" aria-hidden="true">
            <div style={{ width: `${Math.max(4, (Number(o.price_huf) / max) * 100)}%` }} />
          </div>
          <div className="rung-price">
            <Price huf={o.price_huf} currency={currency} rates={rates} locale={locale} />
            {o.currency !== currency ? (
              <span className="orig muted" title={tr.original}>{shopMoney(o.price, o.currency, locale)}</span>
            ) : null}
          </div>
          <a className="btn go" href={`/go/${o.id}`} rel="nofollow sponsored noopener" target="_blank">{tr.goToShop}</a>
        </li>
      ))}
    </ol>
  );
}

export default function ProductView({ locale, currency, rates, product, offers, history }) {
  const tr = t(locale);
  const best = product.best_price_huf ?? product.min_price_any_huf;
  const pct = product.max_price_huf && best ? Math.round((1 - best / product.max_price_huf) * 100) : 0;
  return (
    <article className="product">
      <Link href={`/${locale}`} className="back">{tr.back}</Link>
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
          {pct >= 1 && offers.length > 1 ? <p className="saving">{tr.save(pct)}</p> : null}
          {product.updated_at ? <p className="muted small">{tr.updated}: {dateFmt(product.updated_at, locale)}</p> : null}
        </div>
      </div>

      <section className="block">
        <h2>{tr.offers}</h2>
        <p className="muted">{tr.offersIntro(offers.length)}</p>
        <OfferLadder offers={offers} currency={currency} rates={rates} locale={locale} />
      </section>

      <section className="block">
        <h2>{tr.history}</h2>
        <PriceChart points={history} currency={currency} rates={rates} locale={locale} />
      </section>
    </article>
  );
}
