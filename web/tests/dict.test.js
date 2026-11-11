import { expect, test } from "bun:test";
import { translateTitle } from "../lib/dictionary.js";
test("dictionary translate", () => {
  expect(translateTitle("Retro Arms Šroub pažbičky M4 2ks", "en")).toBe("Retro Arms Screw stock M4 2pcs");
  expect(translateTitle("CYMA M14 rugószett", "en")).toBe("CYMA M14 spring set");
  expect(translateTitle("CYMA M14 rugószett", "hu")).toBe("CYMA M14 rugószett");
  expect(translateTitle("VSR-10 Pro Sniper", "en")).toBe("VSR-10 Pro Sniper");
  expect(translateTitle("Emperor`s Children", "en")).toBe("Emperor`s Children");
  expect(translateTitle("", "en")).toBe("");
});
