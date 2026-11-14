import { translateTitle } from "../lib/dictionary";
import { imgSrc, shopTarget } from "../lib/links";
import Link from "next/link";
import { dateFmt, money, shopMoney, shortDate, t } from "../lib/i18n";
import { historyStats, lastDays } from "../lib/seo";
import { Ad, Price, StockBadge } from "./ui";

/** Árdiagram SVG-ben (külső könyvtár nélkül), dátummal arányos időtengellyel: a hiányzó napok (pl. elfogyott) résként
 *  látszanak, nem csúsznak össze. points: [{ observed_on, min_huf }] */
export function PriceChart({ points, currency, rates, locale, days }) {
  const tr = t(locale);
  if (!points || points.length < 2) return <p className="muted chart-empty">{tr.historyEmpty}</p>;
  const W = 640, H = 180, PX = 8, PY = 18;
  const vals = points.map((p) => Number(p.min_huf));
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = hi - lo || hi * 0.05 || 1;
  const day = (d) => Date.parse(`${d}T00:00:00Z`) / 864e5;
  const t1 = day(points[points.length - 1].observed_on);
  const t0 = Math.min(day(points[0].observed_on), days ? t1 - days : Infinity);
  const x = (i) => PX + ((day(points[i].observed_on) - t0) / (t1 - t0 || 1)) * (W - 2 * PX);
  const y = (v) => PY + (1 - (v - lo) / span) * (H - 2 * PY);
  // 3 napnál nagyobb kihagyás = szakadás a vonalban (nem húzunk egyenest az ismeretlen időszakon át)
  const line = points.map((p, i) => {
    const gap = i && day(p.observed_on) - day(points[i - 1].observed_on) > 3;
    return `${!i || gap ? "M" : "L"}${x(i).toFixed(1)},${y(vals[i]).toFixed(1)}`;
  }).join(" ");
  const minI = vals.indexOf(lo);
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${tr.history}: ${money(lo, currency, rates, locale)} – ${money(hi, currency, rates, locale)}`}>
        <line x1={PX} x2={W - PX} y1={y(lo)} y2={y(lo)} className="chart-low" />
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

/** Ártörténet blokk: 30 / 90 napos váltó (JavaScript nélkül, rádiógombbal) + „valódi akció-e” ítélet. */
function History({ points, now, currency, rates, locale }) {
  const tr = t(locale);
  const st = historyStats(points, now);
  return (
    <section className="block history">
      <h2>{tr.history}</h2>
      <p className="muted small">{tr.historyNote}</p>
      {st ? (
        <p className={`verdict v-${st.verdict}`}>
          <b>{st.verdict === "low" ? tr.verdict.low : st.verdict === "near" ? tr.verdict.near : tr.verdict[st.verdict](st.diff)}</b>
          <span className="muted small"> {tr.low30}: {money(st.low, currency, rates, locale)} · {tr.avg30}: {money(st.avg, currency, rates, locale)}</span>
        </p>
      ) : null}
      <div className="range-tabs">
        <input type="radio" name="hr" id="hr30" defaultChecked />
        <label htmlFor="hr30">{tr.range(30)}</label>
        <input type="radio" name="hr" id="hr90" />
        <label htmlFor="hr90">{tr.range(90)}</label>
        <div className="r30"><PriceChart points={lastDays(points, 30)} days={30} currency={currency} rates={rates} locale={locale} /></div>
        <div className="r90"><PriceChart points={lastDays(points, 90)} days={90} currency={currency} rates={rates} locale={locale} /></div>
      </div>
    </section>
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
            {o.last_seen_at ? <span className="checked muted">{tr.checked}: {shortDate(o.last_seen_at, locale)}</span> : null}
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

export default function ProductView({ locale, currency, rates, product, offers: all, history, alert = null, related = null }) {
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
          {imgSrc(product.image_url) ? <img src={imgSrc(product.image_url)} alt={product.name} referrerPolicy="no-referrer" /> : null}
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
          {related}
        </div>
      </div>

      <section className="block">
        <h2>{tr.offers}</h2>
        <p className="muted">{tr.offersIntro(new Set(offers.map((o) => o.shop_slug)).size)}</p>
        <OfferLadder offers={offers} currency={currency} rates={rates} locale={locale} />
        {odd.length ? (
          <details className="odd-offers">
            <summary>{tr.oddOffers(odd.length)}</summary>
            <p className="muted small">{tr.oddOffersNote}</p>
            <OfferLadder offers={odd} currency={currency} rates={rates} locale={locale} odd scaleMax={scale} />
          </details>
        ) : null}
      </section>

      {alert}

      <History points={history} now={product.best_price_huf} currency={currency} rates={rates} locale={locale} />

      <Ad key={product.slug} place="product" locale={locale} />
    </article>
  );
}
