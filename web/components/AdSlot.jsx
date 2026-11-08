"use client";
import { useEffect, useRef } from "react";

/** Egyetlen, kézzel elhelyezett AdSense-egység. Nincs popup, nincs automatikus hirdetés.
 *  Ha a Google nem tölti ki (data-ad-status="unfilled"), a doboz a CSS-sel eltűnik. */
export default function AdSlot({ client, slot, label }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || el.getAttribute("data-adsbygoogle-status")) return;
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      /* hirdetésblokkoló vagy még nem töltött be a szkript: csendben kihagyjuk */
    }
  }, [slot]);
  return (
    <aside className="ad" aria-label={label}>
      <span className="ad-label">{label}</span>
      <ins ref={ref} className="adsbygoogle" style={{ display: "block" }}
           data-ad-client={client} data-ad-slot={slot}
           data-ad-format="horizontal" data-full-width-responsive="true" />
    </aside>
  );
}
