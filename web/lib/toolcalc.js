// Airsoft kalkulátorok számításai (tiszta függvények: böngészőben, szerveren és tesztben is futnak).
// A képletek fizikai alapúak (energia, térfogat, áram); a rugó-, motor- és hengerajánlás tapasztalati közelítés.

export const FPS_PER_MS = 3.28084;
export const BB_WEIGHTS = ["0.20", "0.23", "0.25", "0.28", "0.30", "0.32", "0.36", "0.40", "0.43", "0.45", "0.48"];
export const GEAR_RATIOS = [13, 16, 18, 22, 32];
export const BORES = ["6.01", "6.02", "6.03", "6.05", "6.08"];
export const VOLTAGES = ["7.4", "11.1"];

const r1 = (x) => Math.round(x * 10) / 10;
const r2 = (x) => Math.round(x * 100) / 100;
const num = (x, d = 0) => (Number.isFinite(Number(x)) ? Number(x) : d);

/** Torkolati energia (J) – m: g, v: m/s. */
export const joule = (g, ms) => 0.5 * (g / 1000) * ms * ms;
/** Sebesség (m/s) adott energiához és BB-súlyhoz. */
export const speedFor = (j, g) => Math.sqrt((2 * j) / (g / 1000));

// Magyar Airsoft Szabályzat (MASZ 2015) kategóriái: kézifegyver ≤ 1,5 J, félautomata mesterlövész ≤ 2,2 J,
// ismétlő mesterlövész ≤ 3,3 J (a két mesterlövész-kategóriában 20 m minimális lőtáv).
export const MASZ = [
  { id: "hand", max: 1.5, fps: 400 },
  { id: "dmr", max: 2.2, fps: 500 },
  { id: "bolt", max: 3.3, fps: 600 },
];

/** Ajánlott BB-súly tartomány az energia szerint (tapasztalati sávok: nagyobb energiához nehezebb BB stabilabb). */
export function bbRangeFor(j) {
  if (j <= 0.9) return ["0.20", "0.25"];
  if (j <= 1.2) return ["0.25", "0.28"];
  if (j <= 1.5) return ["0.28", "0.30"];
  if (j <= 2.0) return ["0.30", "0.36"];
  if (j <= 2.6) return ["0.36", "0.40"];
  return ["0.40", "0.48"];
}

/** 1. FPS / Joule / BB súly. */
export function fpsCalc({ speed, unit = "fps", bb = 0.2 }) {
  const g = num(bb, 0.2);
  const s = num(speed);
  const ms = unit === "ms" ? s : s / FPS_PER_MS;
  if (!(ms > 0) || !(g > 0)) return null;
  const j = joule(g, ms);
  const ms20 = speedFor(j, 0.2);
  // a szabályzat táblázata kerekít (400 fps ≈ 1,5 J, 600 fps ≈ 3,3 J): a 0,20 g-os fps-határ is számít
  const masz = MASZ.find((c) => j <= c.max + 1e-9 || ms20 * FPS_PER_MS <= c.fps + 0.5)?.id || "over";
  return { ms: r1(ms), fps: Math.round(ms * FPS_PER_MS), joule: r2(j), fps20: Math.round(ms20 * FPS_PER_MS), ms20: r1(ms20),
           masz, bbRange: bbRangeFor(j) };
}

// Csőhossz-hatásfok (363 mm = 1,0): rövid csőben a levegő egy része „elfogy”, mielőtt a BB kiér; hosszú csőnél kis többlet.
const EFF = [[150, 0.88], [200, 0.9], [250, 0.94], [300, 0.97], [363, 1.0], [455, 1.02], [510, 1.03], [700, 1.03]];
export function barrelEfficiency(mm) {
  const L = Math.min(700, Math.max(150, num(mm, 363)));
  for (let i = 1; i < EFF.length; i++) {
    const [x0, y0] = EFF[i - 1], [x1, y1] = EFF[i];
    if (L <= x1) return y0 + ((L - x0) / (x1 - x0)) * (y1 - y0);
  }
  return 1.03;
}

// Rugó: M100 ≈ 330 fps (0,20 g, 363 mm-es cső, jó légzárás), M10-enként ≈ 30 fps.
const springFps = (m) => 330 + (m - 100) * 3;

/** 2. Rugó- és motorválasztó. */
export function springCalc({ target, unit = "fps", barrel = 363, ratio = 18 }) {
  const t = num(target);
  const fps20 = unit === "J" ? speedFor(t, 0.2) * FPS_PER_MS : t;
  if (!(fps20 > 150)) return null;
  const eff = barrelEfficiency(barrel);
  const raw = 100 + (fps20 / eff - 330) / 3;
  const m = Math.min(150, Math.max(90, Math.round(raw / 5) * 5));
  const rt = num(ratio, 18);
  const load = m * (18 / rt);                       // rövidebb áttétel (13:1) = nagyobb terhelés a motoron
  const motor = load <= 115 ? "balanced" : load <= 135 ? "torque" : "hightorque";
  const est = springFps(m) * eff;
  return { m, fps20: Math.round(fps20), joule20: r2(joule(0.2, fps20 / FPS_PER_MS)), eff: r2(eff), estFps: Math.round(est),
           estJoule: r2(joule(0.2, est / FPS_PER_MS)), motor, load: Math.round(load),
           highVolt: rt <= 16 || m >= 130, outOfRange: raw < 87.5 ? "low" : raw > 152.5 ? "high" : null };
}

// Teljes (furatolatlan) AEG henger: Ø 24 mm × 49 mm löket ≈ 22 170 mm³. A furatolt típusok hasznos térfogata ennek része.
export const CYLINDER_FULL = Math.PI * 12 * 12 * 49;
export const CYLINDER_TYPES = [[0, 1.0], [1, 0.88], [2, 0.75], [3, 0.58], [4, 0.45]];

/** Ideális henger:cső térfogatarány a BB súlya szerint (nehezebb BB-hez több levegő kell). */
export const idealRatio = (g) => 1.4 + (num(g, 0.25) - 0.2) * 3;

/** 3. Henger–belső cső térfogatarány. */
export function cylinderCalc({ barrel, bore = 6.03, bb = 0.25 }) {
  const L = num(barrel), d = num(bore, 6.03);
  if (!(L >= 80 && L <= 800) || !(d > 5.9 && d < 6.2)) return null;
  const vb = Math.PI * (d / 2) ** 2 * L;
  const ideal = idealRatio(bb);
  const need = (vb * ideal) / CYLINDER_FULL;
  const [type, frac] = CYLINDER_TYPES.reduce((best, cur) => (Math.abs(cur[1] - need) < Math.abs(best[1] - need) ? cur : best));
  return { barrelVol: Math.round(vb), cylinderVol: Math.round(CYLINDER_FULL * frac), ratio: r2((CYLINDER_FULL * frac) / vb),
           ratioFull: r2(CYLINDER_FULL / vb), ideal: r2(ideal), type, fill: Math.round(need * 100),
           warn: need > 1.08 ? "long" : need < 0.42 ? "short" : null };
}

/** 4. LiPo / Li-Ion akku és tűzgyorsaság. rpm: a motor névleges fordulatszáma 11,1 V-on (opcionális). */
export function lipoCalc({ volt = 11.1, mah, c, rpm, ratio = 18 }) {
  const V = num(volt, 11.1), cap = num(mah), C = num(c);
  if (!(cap > 0) || !(C > 0)) return null;
  const amps = (cap / 1000) * C;
  const R = num(rpm), rt = num(ratio, 18);
  // terhelés alatt a motor ~25%-kal lassabb a névlegesnél; 1 lövés = 1 szektorkerék-fordulat = „áttétel” motorfordulat
  const rof = R > 0 && rt > 0 ? r1(((R * (V / 11.1)) * 0.75) / rt / 60) : null;
  return { amps: r1(amps), shots: [Math.round(cap * 1.5), Math.round(cap * 2)], rof, wh: r1((V * cap) / 1000),
           weak: amps < 20, mosfet: V >= 11.1 || (rof || 0) > 25 };
}
