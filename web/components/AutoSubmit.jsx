"use client";
import { useEffect, useRef } from "react";

// JavaScripttel: jelölőnégyzet / legördülő változásakor azonnal szűr. Nélküle a „Szűrés” gomb működik.
export default function AutoSubmit() {
  const ref = useRef(null);
  useEffect(() => {
    const form = ref.current?.closest("form");
    if (!form) return;
    const onChange = (e) => {
      if (e.target.matches('input[type="checkbox"][name], select[name]')) form.requestSubmit();
    };
    form.addEventListener("change", onChange);
    form.classList.add("js-auto");
    return () => form.removeEventListener("change", onChange);
  }, []);
  return <span ref={ref} hidden />;
}
