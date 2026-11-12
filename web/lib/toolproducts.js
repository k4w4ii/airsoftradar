// Kalkulátorok termékajánlója: a kalkulátor eredményéből szűrő (SQL + katalógus-link). Csak paraméteres SQL.
import { hrefFor } from "./catalog";
import { BB_WEIGHTS, VOLTAGES } from "./toolcalc";

const BASE = { q: "", cats: [], attrs: {}, plats: [], brands: [], min: 0, max: 0, stock: true, sort: "price", view: "grid", page: 1 };
const like = (col, v) => ({ sql: `${col} LIKE ?`, p: [v] });
const any = (parts) => ({ sql: `(${parts.map((x) => x.sql).join(" OR ")})`, p: parts.flatMap((x) => x.p) });

/** kind + paraméterek -> { where, params, more } vagy null. */
export function toolFilter(kind, q, locale = "hu") {
  if (kind === "bb") {
    const lo = Number(q.lo), hi = Number(q.hi);
    const ws = BB_WEIGHTS.filter((w) => Number(w) >= lo - 1e-9 && Number(w) <= hi + 1e-9);
    if (!ws.length) return null;
    const f = any(ws.map((w) => like("subtypes", `%,bbw=${w},%`)));
    return { where: `category = 'acc_ammo' AND ${f.sql}`, params: f.p,
             more: hrefFor(locale, { ...BASE, cats: ["acc_ammo"], attrs: { bbw: ws } }) };
  }
  if (kind === "spring") {
    const m = Math.round(Number(q.m));
    if (!(m >= 70 && m <= 200)) return null;
    const f = any([like("name", `%M${m}%`), like("name", `%M ${m}%`), like("name", `%SP${m}%`)]);
    return { where: `category = 'part_internal' AND subtypes LIKE '%,pt=spring,%' AND ${f.sql}`, params: f.p,
             more: hrefFor(locale, { ...BASE, q: `M${m}`, cats: ["part_internal"] }) };
  }
  if (kind === "motor") {
    const words = { hightorque: ["%high torque%", "%torque%", "%ht %"], torque: ["%torque%", "%balance%"], balanced: ["%balance%", "%speed%", "%hs %"] }[q.t];
    if (!words) return null;
    const f = any(words.map((w) => like("lower(name)", w)));
    return { where: `category = 'part_motor' AND subtypes LIKE '%,pt=motor,%' AND ${f.sql}`, params: f.p,
             more: hrefFor(locale, { ...BASE, cats: ["part_motor"], attrs: { pt: ["motor"] } }) };
  }
  if (kind === "cylinder") {
    const t = Math.round(Number(q.type));
    if (!(t >= 0 && t <= 4)) return null;
    const names = [`%type ${t}%`, `%type-${t}%`, `%typ ${t}%`, `%tipo ${t}%`, ...(t === 0 ? ["%full%"] : [`%t${t} %`])];
    const f = any(names.map((n) => like("lower(name)", n)));
    return { where: `category = 'part_internal' AND (lower(name) LIKE '%cylinder%' OR lower(name) LIKE '%henger%' OR lower(name) LIKE '%zylinder%') AND ${f.sql}`,
             params: f.p, more: hrefFor(locale, { ...BASE, q: "cylinder", cats: ["part_internal"] }) };
  }
  if (kind === "barrel") {
    const L = Math.round(Number(q.len));
    if (!(L >= 80 && L <= 800)) return null;
    return { where: "category = 'part_hopup' AND subtypes LIKE '%,pt=barrel,%' AND (name LIKE ? OR name LIKE ?)",
             params: [`%${L}mm%`, `%${L} mm%`], more: hrefFor(locale, { ...BASE, q: `${L}mm`, cats: ["part_hopup"] }) };
  }
  if (kind === "battery") {
    const v = VOLTAGES.includes(String(q.v)) ? String(q.v) : null;
    if (!v) return null;
    return { where: "category = 'acc_power' AND subtypes LIKE '%,pk=battery,%' AND subtypes LIKE ?", params: [`%,volt=${v},%`],
             more: hrefFor(locale, { ...BASE, cats: ["acc_power"], attrs: { pk: ["battery"], volt: [v] } }) };
  }
  return null;
}
