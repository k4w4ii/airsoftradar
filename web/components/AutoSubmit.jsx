"use client";
import { useEffect, useRef } from "react";

// JavaScripttel: jelölőnégyzet / legördülő változásakor azonnal szűr. Nélküle a „Szűrés” gomb működik.
// Kategóriacsoportok: a főpipa az összes alpipát állítja; ha minden alpipa be van jelölve, a főpipa is.
// Küldéskor a bejelölt csoport alpipái nem mennek az URL-be (elég a csoport: ?cat=weapons).
export default function AutoSubmit() {
  const ref = useRef(null);
  useEffect(() => {
    const form = ref.current?.closest("form");
    if (!form) return;
    const kids = (g) => [...form.querySelectorAll(`input[data-parent="${g}"]`)];
    const parent = (g) => form.querySelector(`input[data-group="${g}"]`);
    const sync = (g) => {
      const p = parent(g), k = kids(g);
      if (!p || !k.length) return;
      const n = k.filter((x) => x.checked).length;
      p.checked = n === k.length;
      p.indeterminate = n > 0 && n < k.length;
    };
    const groups = [...form.querySelectorAll("input[data-group]")].map((x) => x.dataset.group);
    groups.forEach(sync);

    const onChange = (e) => {
      const el = e.target;
      if (el.dataset.group) kids(el.dataset.group).forEach((k) => { k.checked = el.checked; });
      if (el.dataset.parent) sync(el.dataset.parent);
      if (el.matches('input[type="checkbox"][name], select[name]')) form.requestSubmit();
    };
    const onSubmit = () => {
      for (const g of groups) if (parent(g)?.checked) kids(g).forEach((k) => { k.disabled = true; });
    };
    const onClick = (e) => {
      const btn = e.target.closest("[data-twisty]");
      if (!btn) return;
      const li = btn.closest("li");
      btn.setAttribute("aria-expanded", String(li.classList.toggle("open")));
    };
    // vissza gombnál a böngésző a letiltott állapotot is visszahozhatja
    const onShow = () => form.querySelectorAll("input[data-parent]").forEach((k) => { k.disabled = false; });

    form.addEventListener("change", onChange);
    form.addEventListener("submit", onSubmit);
    form.addEventListener("click", onClick);
    window.addEventListener("pageshow", onShow);
    form.classList.add("js-auto");
    return () => {
      form.removeEventListener("change", onChange);
      form.removeEventListener("submit", onSubmit);
      form.removeEventListener("click", onClick);
      window.removeEventListener("pageshow", onShow);
    };
  }, []);
  return <span ref={ref} hidden />;
}
