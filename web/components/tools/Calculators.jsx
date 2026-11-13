"use client";
// Airsoft kalkulátorok (kliensoldal): azonnali számítás gépelés közben, az eredmény alatt raktáron lévő termékajánló.
// A beállítások a címsorba kerülnek (?bb=0.28&speed=380…), így a link megosztható.
import { useEffect, useMemo, useRef, useState } from "react";
import { intl, money } from "../../lib/i18n";
import { imgSrc } from "../../lib/links";
import { tl } from "../../lib/toollabels";
import { BB_WEIGHTS, BORES, cylinderCalc, fpsCalc, GEAR_RATIOS, lipoCalc, springCalc, VOLTAGES } from "../../lib/toolcalc";

// rögzített tizedesjegyű szám a nyelv tizedesjelével (0,25 g; 6,03 mm; 7,4 V)
const dn = (v, locale, d) => Number(v).toLocaleString(intl(locale), { minimumFractionDigits: d, maximumFractionDigits: d });
const fmt = (v, locale, d = 0) => (v == null ? "–" : Number(v).toLocaleString(intl(locale), { maximumFractionDigits: d }));

function useQuerySync(state) {
  const first = useRef(true);
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    const sp = new URLSearchParams(Object.entries(state).filter(([, v]) => v !== "" && v != null).map(([k, v]) => [k, String(v)]));
    const t = setTimeout(() => window.history.replaceState(null, "", `${window.location.pathname}?${sp}`), 300);
    return () => clearTimeout(t);
  }, [JSON.stringify(state)]);   // eslint-disable-line react-hooks/exhaustive-deps
}

function Field({ label, value, onChange, unit, min, max, step = "any", id }) {
  return (
    <label className="tf" htmlFor={id}>
      <span className="tf-label">{label}</span>
      <span className="tf-input">
        <input id={id} type="number" inputMode="decimal" value={value} min={min} max={max} step={step}
               onChange={(e) => onChange(e.target.value)} />
        {unit ? <span className="tf-unit">{unit}</span> : null}
      </span>
    </label>
  );
}

function Seg({ label, value, options, onChange, name }) {
  return (
    <fieldset className="tseg">
      <legend className="tf-label">{label}</legend>
      <div className="tseg-opts" role="radiogroup">
        {options.map(([v, text]) => (
          <label key={v} className={String(v) === String(value) ? "on" : undefined}>
            <input type="radio" name={name} value={v} checked={String(v) === String(value)} onChange={() => onChange(String(v))} />
            {text}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function Out({ label, value, sub, big = false, tone }) {
  return (
    <div className={`tout${big ? " big" : ""}${tone ? ` ${tone}` : ""}`}>
      <span className="tout-label">{label}</span>
      <span className="tout-value">{value}</span>
      {sub ? <span className="tout-sub">{sub}</span> : null}
    </div>
  );
}

function Note({ children, tone = "info" }) {
  return <p className={`tnote ${tone}`}>{children}</p>;
}

/** Termékajánló: a kalkulátor eredményéhez illő, raktáron lévő termékek (késleltetett lekérés gépelés közben). */
function Products({ blocks, locale, currency, rates }) {
  const L = tl(locale);
  const key = JSON.stringify(blocks);
  const [data, setData] = useState({});
  useEffect(() => {
    let alive = true;
    const t = setTimeout(async () => {
      const out = {};
      await Promise.all(blocks.map(async (b) => {
        const sp = new URLSearchParams({ ...b.q, kind: b.kind, locale });
        try {
          const r = await fetch(`/api/tools/products?${sp}`);
          out[b.title] = r.ok ? await r.json() : { items: [] };
        } catch { out[b.title] = { items: [] }; }
      }));
      if (alive) setData(out);
    }, 450);
    return () => { alive = false; clearTimeout(t); };
  }, [key, locale]);   // eslint-disable-line react-hooks/exhaustive-deps
  if (!blocks.length) return null;
  return (
    <section className="tprod" aria-live="polite">
      <h2>{L.products}</h2>
      <p className="muted small">{L.productsNote}</p>
      {blocks.map((b) => {
        const d = data[b.title];
        return (
          <div key={b.title} className="tprod-block">
            <div className="tprod-head">
              <h3>{b.title}</h3>
              {d?.more ? <a href={d.more} className="see-all">{L.seeAll} →</a> : null}
            </div>
            {!d ? <p className="muted small">{L.loading}</p> : !d.items?.length ? <p className="muted small">{L.noProducts}</p> : (
              <ul className="tprod-list">
                {d.items.map((p) => (
                  <li key={p.id}>
                    <a href={`/${locale}/p/${p.slug}`} className="tprod-card">
                      <span className="tprod-img">{imgSrc(p.image_url) ? <img src={imgSrc(p.image_url)} alt="" loading="lazy" referrerPolicy="no-referrer" /> : null}</span>
                      <span className="tprod-name">{p.name}</span>
                      <span className="tprod-meta">
                        <span className="muted">{L.shops(p.offer_count)}</span>
                        <b>{p.offer_count > 1 ? `${L.from} ` : ""}{money(p.best_price_huf ?? p.min_price_any_huf, currency, rates, locale)}</b>
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </section>
  );
}

const pick = (v, list, d) => (list.map(String).includes(String(v)) ? String(v) : d);

export function FpsCalculator({ locale, currency, rates, initial = {} }) {
  const L = tl(locale);
  const [unit, setUnit] = useState(pick(initial.unit, ["fps", "ms"], "fps"));
  const [speed, setSpeed] = useState(initial.speed ?? "380");
  const [bb, setBb] = useState(pick(initial.bb, BB_WEIGHTS, "0.25"));
  useQuerySync({ unit, speed, bb });
  const r = useMemo(() => fpsCalc({ speed, unit, bb }), [speed, unit, bb]);
  const blocks = r ? [{ kind: "bb", q: { lo: r.bbRange[0], hi: r.bbRange[1] }, title: L.bbFor(r.bbRange[0], r.bbRange[1]) }] : [];
  return (
    <>
      <div className="tcard">
        <div className="tin">
          <Seg label={L.unit} name="unit" value={unit} onChange={setUnit} options={[["fps", L.unitFps], ["ms", L.unitMs]]} />
          <Field id="speed" label={L.speed} value={speed} onChange={setSpeed} unit={unit === "fps" ? "fps" : "m/s"} min={50} max={800} />
          <label className="tf" htmlFor="bb">
            <span className="tf-label">{L.bb}</span>
            <span className="tf-input">
              <select id="bb" value={bb} onChange={(e) => setBb(e.target.value)}>
                {BB_WEIGHTS.map((w) => <option key={w} value={w}>{dn(w, locale, 2)} g</option>)}
              </select>
            </span>
          </label>
        </div>
        <div className="tres single">
          {r ? (
            <>
              <Out big label={L.energy} value={`${fmt(r.joule, locale, 2)} J`} sub={`${fmt(r.fps, locale)} fps · ${fmt(r.ms, locale, 1)} m/s · ${fmt(bb, locale, 2)} g`} />
            </>
          ) : <p className="muted">–</p>}
        </div>
      </div>
      <Products blocks={blocks} locale={locale} currency={currency} rates={rates} />
    </>
  );
}

export function SpringCalculator({ locale, currency, rates, initial = {} }) {
  const L = tl(locale);
  const [unit, setUnit] = useState(pick(initial.unit, ["fps", "J"], "fps"));
  const [target, setTarget] = useState(initial.target ?? "380");
  const [barrel, setBarrel] = useState(initial.barrel ?? "363");
  const [ratio, setRatio] = useState(pick(initial.ratio, GEAR_RATIOS, "18"));
  useQuerySync({ unit, target, barrel, ratio });
  const r = useMemo(() => springCalc({ target, unit, barrel, ratio }), [target, unit, barrel, ratio]);
  const blocks = r ? [
    { kind: "spring", q: { m: r.m }, title: `${L.spring}: M${r.m}` },
    { kind: "motor", q: { t: r.motor }, title: `${L.motor}: ${L.motorName[r.motor]}` },
  ] : [];
  return (
    <>
      <div className="tcard">
        <div className="tin">
          <Seg label={L.unit} name="unit" value={unit} onChange={setUnit} options={[["fps", L.unitFps20], ["J", L.unitJ]]} />
          <Field id="target" label={L.target} value={target} onChange={setTarget} unit={unit === "J" ? "J" : "fps"} min={0} max={700} />
          <Field id="barrel" label={L.barrel} value={barrel} onChange={setBarrel} unit="mm" min={100} max={700} step={1} />
          <Seg label={L.ratio} name="ratio" value={ratio} onChange={setRatio} options={GEAR_RATIOS.map((g) => [g, `${g}:1`])} />
        </div>
        <div className="tres">
          {r ? (
            <>
              <Out big label={L.spring} value={`M${r.m}`} sub={`${L.estimate}: ≈ ${fmt(r.estFps, locale)} fps · ${fmt(r.estJoule, locale, 2)} J (${dn(0.2, locale, 2)} g) · ${L.efficiency} ${Math.round(r.eff * 100)}%`} />
              <Out label={L.motor} value={L.motorName[r.motor]} sub={L.motorNote[r.motor]} tone={r.motor === "hightorque" ? "warn" : undefined} />
              {r.highVolt ? <Note>{L.highVolt}</Note> : null}
              {r.outOfRange ? <Note tone="bad">{r.outOfRange === "low" ? L.rangeLow : L.rangeHigh}</Note> : null}
            </>
          ) : <p className="muted">–</p>}
        </div>
      </div>
      <Products blocks={blocks} locale={locale} currency={currency} rates={rates} />
    </>
  );
}

export function CylinderCalculator({ locale, currency, rates, initial = {} }) {
  const L = tl(locale);
  const [barrel, setBarrel] = useState(initial.barrel ?? "363");
  const [bore, setBore] = useState(pick(initial.bore, BORES, "6.03"));
  const [bb, setBb] = useState(pick(initial.bb, BB_WEIGHTS, "0.25"));
  useQuerySync({ barrel, bore, bb });
  const r = useMemo(() => cylinderCalc({ barrel, bore, bb }), [barrel, bore, bb]);
  const blocks = r ? [
    { kind: "cylinder", q: { type: r.type }, title: `${L.cylType}: ${L.typeName(r.type)}` },
    { kind: "barrel", q: { len: Math.round(Number(barrel)) }, title: `${L.barrel}: ${Math.round(Number(barrel))} mm` },
  ] : [];
  return (
    <>
      <div className="tcard">
        <div className="tin">
          <Field id="barrel" label={L.barrel} value={barrel} onChange={setBarrel} unit="mm" min={80} max={800} step={1} />
          <Seg label={L.bore} name="bore" value={bore} onChange={setBore} options={BORES.map((b) => [b, `${dn(b, locale, 2)} mm`])} />
          <label className="tf" htmlFor="bb">
            <span className="tf-label">{L.bb}</span>
            <span className="tf-input">
              <select id="bb" value={bb} onChange={(e) => setBb(e.target.value)}>
                {BB_WEIGHTS.map((w) => <option key={w} value={w}>{dn(w, locale, 2)} g</option>)}
              </select>
            </span>
          </label>
        </div>
        <div className="tres">
          {r ? (
            <>
              <Out big label={L.cylType} value={L.typeName(r.type)} sub={`${L.ratioRes}: ${fmt(r.ratio, locale, 2)} : 1 · ${L.ideal}: ${fmt(r.ideal, locale, 2)} : 1`} />
              <Out label={L.barrelVol} value={`${fmt(r.barrelVol, locale)} mm³`} />
              <Out label={L.cylVol} value={`${fmt(r.cylinderVol, locale)} mm³`} sub={`Type 0: ${fmt(r.ratioFull, locale, 2)} : 1`} />
              {r.warn ? <Note tone="warn">{r.warn === "long" ? L.cylWarnLong : L.cylWarnShort}</Note> : null}
            </>
          ) : <p className="muted">–</p>}
        </div>
      </div>
      <Products blocks={blocks} locale={locale} currency={currency} rates={rates} />
    </>
  );
}

export function LipoCalculator({ locale, currency, rates, initial = {} }) {
  const L = tl(locale);
  const [volt, setVolt] = useState(pick(initial.volt, VOLTAGES, "11.1"));
  const [mah, setMah] = useState(initial.mah ?? "1600");
  const [c, setC] = useState(initial.c ?? "25");
  const [rpm, setRpm] = useState(initial.rpm ?? "");
  const [ratio, setRatio] = useState(pick(initial.ratio, GEAR_RATIOS, "18"));
  useQuerySync({ volt, mah, c, rpm, ratio });
  const r = useMemo(() => lipoCalc({ volt, mah, c, rpm, ratio }), [volt, mah, c, rpm, ratio]);
  const blocks = r ? [{ kind: "battery", q: { v: volt }, title: `${volt} V LiPo / Li-Ion` }] : [];
  return (
    <>
      <div className="tcard">
        <div className="tin">
          <Seg label={L.volt} name="volt" value={volt} onChange={setVolt} options={VOLTAGES.map((v) => [v, `${dn(v, locale, 1)} V`])} />
          <Field id="mah" label={L.mah} value={mah} onChange={setMah} unit="mAh" min={300} max={10000} step={50} />
          <Field id="c" label={L.c} value={c} onChange={setC} unit="C" min={5} max={100} step={1} />
          <Field id="rpm" label={L.rpm} value={rpm} onChange={setRpm} unit="RPM" min={10000} max={80000} step={500} />
          <Seg label={L.ratio} name="ratio" value={ratio} onChange={setRatio} options={GEAR_RATIOS.map((g) => [g, `${g}:1`])} />
        </div>
        <div className="tres">
          {r ? (
            <>
              <Out big label={L.amps} value={`${fmt(r.amps, locale, 1)} A`} sub={`${fmt(Number(mah) / 1000, locale, 2)} Ah × ${fmt(c, locale)}C · ${L.energyWh}: ${fmt(r.wh, locale, 1)} Wh`}
                   tone={r.weak ? "warn" : undefined} />
              <Out label={L.shots} value={`${fmt(r.shots[0], locale)} – ${fmt(r.shots[1], locale)}`} />
              <Out label={L.rof} value={r.rof ? `≈ ${fmt(r.rof, locale, 1)} BB/s` : L.rofEmpty} />
              {r.weak ? <Note tone="warn">{L.weak}</Note> : null}
              {r.mosfet ? <Note>{L.mosfet}</Note> : null}
            </>
          ) : <p className="muted">–</p>}
        </div>
      </div>
      <Products blocks={blocks} locale={locale} currency={currency} rates={rates} />
    </>
  );
}

export default function Calculator({ slug, ...props }) {
  const C = { "fps-joule-calculator": FpsCalculator, "spring-motor-calculator": SpringCalculator,
              "cylinder-volume-ratio": CylinderCalculator, "lipo-rof-calculator": LipoCalculator }[slug];
  return C ? <C {...props} /> : null;
}
