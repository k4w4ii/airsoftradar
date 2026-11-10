import Link from "next/link";
import CatImg from "./CatImg";
import { CAT_GROUPS, hrefFor } from "../lib/catalog";
import { t } from "../lib/i18n";
import { ProductTile } from "./HomeView";
import SearchBox from "./SearchBox";

const BASE = { q: "", cats: [], plats: [], brands: [], min: 0, max: 0, stock: false, sort: "discount", view: "grid", page: 1 };
// a kategória-csempék sorrendje: fegyverek, majd a leggyakrabban keresett alkatrész- és kiegészítő-csoportok
const TILES = [...CAT_GROUPS[0].leaves, "parts", "acc_mag", "acc_ammo", "acc_power", "acc_optics", "acc_protect", "acc_gear"];
const GROUP_LEAVES = Object.fromEntries(CAT_GROUPS.map((g) => [g.id, g.leaves]));

export default function Welcome({ locale, currency, rates, data }) {
  const tr = t(locale);
  const count = (c) => (GROUP_LEAVES[c] || [c]).reduce((x, l) => x + (data.counts[l] || 0), 0);
  const image = (c) => (GROUP_LEAVES[c] || [c]).flatMap((l) => [].concat(data.images[l] || [])).slice(0, 3);
  const tiles = TILES.filter((c) => count(c) > 0);
  return (
    <div className="welcome">
      <section className="hero">
        <h1>{tr.welcomeTitle}</h1>
        <p className="hero-sub">{tr.welcomeSub(data.total, data.shops)}</p>
        <SearchBox locale={locale} placeholder={tr.searchPlaceholder} label={tr.search} button={tr.search}
                   allText={tr.allResultsFor} className="topsearch" big />
      </section>

      <section className="wblock">
        <div className="wblock-head">
          <h2>{tr.browseCats}</h2>
          <Link href={hrefFor(locale, { ...BASE, cats: [] })} className="see-all">{tr.cats.all} →</Link>
        </div>
        <ul className="cat-tiles">
          {tiles.map((c) => (
            <li key={c}>
              <Link href={hrefFor(locale, { ...BASE, cats: [c] })} className="cat-tile">
                <span className="cat-img"><CatImg srcs={image(c)} /></span>
                <span className="cat-name">{tr.cats[c]}</span>
                <span className="cat-n">{tr.items(count(c))}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {data.deals.length ? (
        <section className="wblock">
          <div className="wblock-head">
            <div>
              <h2>{tr.bestDeals}</h2>
              <p className="muted small">{tr.bestDealsNote}</p>
            </div>
            <Link href={hrefFor(locale, { ...BASE, cats: ["weapons"] })} className="see-all">{tr.seeAll} →</Link>
          </div>
          <ul className="tiles">
            {data.deals.map((p) => <ProductTile key={p.id} p={p} locale={locale} currency={currency} rates={rates} />)}
          </ul>
        </section>
      ) : null}

      {data.brands.length ? (
        <section className="wblock">
          <h2>{tr.topBrands}</h2>
          <div className="chips brand-chips">
            {data.brands.map((b) => (
              <Link key={b.name} href={hrefFor(locale, { ...BASE, brands: [b.name] })} className="chip">
                {b.name}<span>{b.n}</span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
