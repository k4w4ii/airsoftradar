"use client";
import { useRef, useState } from "react";

/** Kétfogantyús árcsúszka + min/max mezők. Értékek a választott pénznemben. JS nélkül a mezők + OK gomb működnek. */
export default function PriceSlider({ lo, hi, step, valueMin, valueMax, labels, suffix }) {
  const [a, setA] = useState(valueMin ?? lo);
  const [b, setB] = useState(valueMax ?? hi);
  const ref = useRef(null);
  const span = Math.max(hi - lo, 1);
  const submit = () => setTimeout(() => ref.current?.closest("form")?.requestSubmit(), 0);
  const pct = (v) => ((Math.min(Math.max(v, lo), hi) - lo) / span) * 100;

  return (
    <div className="pslider" ref={ref}>
      {hi > lo ? (
        <div className="pslider-rail">
          <div className="pslider-fill" style={{ left: `${pct(a)}%`, right: `${100 - pct(b)}%` }} />
          <input type="range" min={lo} max={hi} step={step} value={a} aria-label={labels.min}
                 onChange={(e) => setA(Math.min(Number(e.target.value), b - step))}
                 onPointerUp={submit} onKeyUp={(e) => e.key.startsWith("Arrow") && submit()} />
          <input type="range" min={lo} max={hi} step={step} value={b} aria-label={labels.max}
                 onChange={(e) => setB(Math.max(Number(e.target.value), a + step))}
                 onPointerUp={submit} onKeyUp={(e) => e.key.startsWith("Arrow") && submit()} />
        </div>
      ) : null}
      <div className="pslider-inputs">
        <label>
          <span className="sr-only">{labels.min}</span>
          <input type="number" name="min" inputMode="numeric" min="0" placeholder={labels.min}
                 value={a > lo ? a : ""} onChange={(e) => setA(e.target.value === "" ? lo : Number(e.target.value))} />
        </label>
        <span aria-hidden="true">–</span>
        <label>
          <span className="sr-only">{labels.max}</span>
          <input type="number" name="max" inputMode="numeric" min="0" placeholder={labels.max}
                 value={b < hi ? b : ""} onChange={(e) => setB(e.target.value === "" ? hi : Number(e.target.value))} />
        </label>
        <span className="pslider-suffix muted">{suffix}</span>
        <button type="submit" className="btn small-btn">{labels.ok}</button>
      </div>
    </div>
  );
}
