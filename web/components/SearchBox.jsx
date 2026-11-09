"use client";
import { useEffect, useId, useRef, useState } from "react";

// Kereső javaslatokkal: gépelés közben (2+ karakter, 180 ms szünet után) termékeket, márkákat és kategóriákat ajánl.
// Billentyűzet: ↑/↓ választ, Enter megnyit (ha nincs kiválasztva: teljes keresés), Esc bezár.
// JavaScript nélkül sima keresőűrlap.
export default function SearchBox({ locale, defaultValue = "", placeholder, label, button, allText, className = "topsearch", big = false }) {
  const [q, setQ] = useState(defaultValue);
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const box = useRef(null);
  const ctrl = useRef(null);
  const id = useId();

  useEffect(() => {
    const term = q.trim();
    if (term.length < 2) { setData(null); return; }
    const timer = setTimeout(async () => {
      ctrl.current?.abort();
      const c = new AbortController();
      ctrl.current = c;
      try {
        const res = await fetch(`/api/suggest?l=${locale}&q=${encodeURIComponent(term)}`, { signal: c.signal });
        if (res.ok) { setData(await res.json()); setActive(-1); }
      } catch { /* megszakítva vagy hálózati hiba: nincs javaslat */ }
    }, 180);
    return () => clearTimeout(timer);
  }, [q, locale]);

  useEffect(() => {
    const close = (e) => { if (!box.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, []);

  const items = data ? [
    ...data.cats.map((x) => ({ ...x, kind: "cat" })),
    ...data.brands.map((x) => ({ ...x, kind: "brand" })),
    ...data.products.map((x) => ({ ...x, kind: "product" })),
  ] : [];
  const show = open && q.trim().length >= 2 && items.length > 0;
  const go = (href) => { window.location.href = href; };

  const onKey = (e) => {
    if (!show) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => (a + 1) % items.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => (a <= 0 ? items.length - 1 : a - 1)); }
    else if (e.key === "Escape") { setOpen(false); }
    else if (e.key === "Enter" && active >= 0) { e.preventDefault(); go(items[active].href); }
  };

  let idx = -1;
  const opt = (it, body) => {
    idx += 1;
    const i = idx;
    return (
      <li key={`${it.kind}-${it.href}`} id={`${id}-${i}`} role="option" aria-selected={i === active}
          onPointerEnter={() => setActive(i)}>
        <a href={it.href} className={i === active ? "sg-item on" : "sg-item"} tabIndex={-1}>{body}</a>
      </li>
    );
  };

  return (
    <form action={`/${locale}`} className={`${className}${big ? " big" : ""}`} role="search" ref={box}>
      <div className="sg-wrap">
        <input name="q" type="search" value={q} placeholder={placeholder} aria-label={label} autoComplete="off"
               role="combobox" aria-expanded={show} aria-controls={`${id}-list`} aria-autocomplete="list"
               aria-activedescendant={show && active >= 0 ? `${id}-${active}` : undefined}
               onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)} onKeyDown={onKey} />
        {show ? (
          <ul className="sg-list" id={`${id}-list`} role="listbox">
            {data.cats.map((c) => opt({ ...c, kind: "cat" }, <><span className="sg-tag">▸</span><span>{c.label}</span></>))}
            {data.brands.map((b) => opt({ ...b, kind: "brand" },
              <><span className="sg-tag">◎</span><span>{b.label}</span><span className="sg-n">{b.n}</span></>))}
            {data.products.map((p) => opt({ ...p, kind: "product" }, (
              <>
                <span className="sg-thumb">{p.image ? <img src={p.image} alt="" loading="lazy" referrerPolicy="no-referrer" /> : null}</span>
                <span className="sg-main"><span className="sg-mfr">{p.manufacturer}</span><span className="sg-name">{p.name}</span></span>
                <span className="sg-price">{p.price}<span className="sg-n">{p.shops}</span></span>
              </>
            )))}
            <li className="sg-all"><button type="submit">{allText.replace("{q}", q.trim())}</button></li>
          </ul>
        ) : null}
      </div>
      <button type="submit">{button}</button>
    </form>
  );
}
