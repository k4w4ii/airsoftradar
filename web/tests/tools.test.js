import { test, expect } from "bun:test";
import { barrelEfficiency, cylinderCalc, fpsCalc, lipoCalc, springCalc } from "../lib/toolcalc.js";
import { toolFilter } from "../lib/toolproducts.js";
import { TOOLS, TOOL_TEXT, toolText } from "../lib/tools.js";
import { TL } from "../lib/toollabels.js";

test("FPS / Joule / BB súly", () => {
  const r = fpsCalc({ speed: 400, unit: "fps", bb: 0.2 });
  expect(r.joule).toBe(1.49);
  expect(r.fps20).toBe(400);
  expect(r.masz).toBe("hand");
  const h = fpsCalc({ speed: 110, unit: "ms", bb: 0.25 });
  expect(h.joule).toBe(1.51);
  expect(h.fps20).toBe(403);                 // 0,20 g-os egyenérték: ugyanaz az energia gyorsabb könnyebb BB-vel
  expect(h.masz).toBe("dmr");
  expect(fpsCalc({ speed: 600, bb: 0.2 }).masz).toBe("bolt");
  expect(fpsCalc({ speed: 700, bb: 0.2 }).masz).toBe("over");
  expect(fpsCalc({ speed: 380, bb: 0.25 }).bbRange).toEqual(["0.30", "0.36"]);   // 1,68 J
  expect(fpsCalc({ speed: "", bb: 0.2 })).toBe(null);
});

test("rugó- és motorválasztó", () => {
  expect(springCalc({ target: 330, barrel: 363, ratio: 18 }).m).toBe(100);
  expect(springCalc({ target: 400, barrel: 363, ratio: 18 }).m).toBe(125);
  expect(springCalc({ target: 1.5, unit: "J", barrel: 363, ratio: 18 }).m).toBe(125);
  const short = springCalc({ target: 350, barrel: 200, ratio: 18 });
  expect(short.m).toBeGreaterThan(springCalc({ target: 350, barrel: 363, ratio: 18 }).m);   // rövid cső: erősebb rugó
  expect(springCalc({ target: 350, ratio: 18 }).motor).toBe("balanced");
  expect(springCalc({ target: 400, ratio: 13 }).motor).toBe("hightorque");
  expect(springCalc({ target: 400, ratio: 13 }).highVolt).toBe(true);
  expect(springCalc({ target: 200, ratio: 18 }).outOfRange).toBe("low");
  expect(springCalc({ target: 650, ratio: 18 })).toMatchObject({ m: 150, outOfRange: "high" });
  expect(barrelEfficiency(363)).toBe(1);
  expect(barrelEfficiency(50)).toBe(0.88);
});

test("henger–cső térfogatarány", () => {
  const r = cylinderCalc({ barrel: 363, bore: 6.03, bb: 0.25 });
  expect(r.type).toBe(2);
  expect(r.barrelVol).toBe(10366);
  expect(cylinderCalc({ barrel: 500, bore: 6.03, bb: 0.25 }).type).toBe(0);
  expect(cylinderCalc({ barrel: 430, bore: 6.03, bb: 0.25 }).type).toBe(1);
  expect(cylinderCalc({ barrel: 275, bore: 6.03, bb: 0.25 }).type).toBe(3);
  expect(cylinderCalc({ barrel: 229, bore: 6.03, bb: 0.25 }).type).toBe(4);
  expect(cylinderCalc({ barrel: 363, bore: 6.03, bb: 0.36 }).type).toBeLessThan(2);    // nehezebb BB: több levegő
  expect(cylinderCalc({ barrel: 650, bore: 6.03, bb: 0.4 }).warn).toBe("long");
  expect(cylinderCalc({ barrel: 20, bore: 6.03 })).toBe(null);
});

test("LiPo és tűzgyorsaság", () => {
  const r = lipoCalc({ volt: 11.1, mah: 1600, c: 25, rpm: 35000, ratio: 18 });
  expect(r.amps).toBe(40);
  expect(r.shots).toEqual([2400, 3200]);
  expect(r.rof).toBe(24.3);
  expect(lipoCalc({ volt: 7.4, mah: 1600, c: 25, rpm: 35000, ratio: 18 }).rof).toBe(16.2);
  expect(lipoCalc({ volt: 7.4, mah: 1000, c: 15 }).weak).toBe(true);
  expect(lipoCalc({ volt: 7.4, mah: 1600, c: 25 }).rof).toBe(null);
});

test("termékajánló szűrők: csak paraméteres SQL, katalógus-link", () => {
  const bb = toolFilter("bb", { lo: "0.28", hi: "0.30" }, "hu");
  expect(bb.params).toEqual(["%,bbw=0.28,%", "%,bbw=0.30,%"]);
  expect(bb.more).toContain("bbw=0.28");
  expect(bb.more).toContain("stock=1");
  expect(toolFilter("spring", { m: "120" }).params).toEqual(["%M120%", "%M 120%", "%SP120%"]);
  expect(toolFilter("spring", { m: "1; DROP" })).toBe(null);
  expect(toolFilter("battery", { v: "11.1" }).params).toEqual(["%,volt=11.1,%"]);
  expect(toolFilter("battery", { v: "99" })).toBe(null);
  expect(toolFilter("cylinder", { type: "2" }).where).toContain("cylinder");
  expect(toolFilter("hack", {})).toBe(null);
  for (const k of ["bb", "spring", "motor", "cylinder", "barrel", "battery"]) {
    const f = toolFilter(k, { lo: "0.2", hi: "0.25", m: "110", t: "torque", type: "1", len: "363", v: "7.4" });
    expect(f.where).not.toMatch(/'%[^']*\d/);           // értékek csak paraméterként
  }
});

test("minden kalkulátorhoz van magyar és angol SEO-szöveg és felirat", () => {
  for (const t of TOOLS) for (const l of ["hu", "en"]) {
    const x = toolText(t.slug, l);
    expect(x.title.length).toBeGreaterThan(20);
    expect(x.description.length).toBeGreaterThan(80);
    expect(x.description.length).toBeLessThan(200);
    expect(x.faq.length).toBeGreaterThanOrEqual(3);
    expect(x.how.length).toBeGreaterThanOrEqual(3);
  }
  expect(Object.keys(TL.hu).sort()).toEqual(Object.keys(TL.en).sort());
  expect(Object.keys(TOOL_TEXT).length).toBe(4);
});
