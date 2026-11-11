// Ingyenes szótáras fordítás a bolti címekhez (ugyanaz, mint a scraper/dictionary.py; a dictionary.json-t az készíti).
// Angol oldalon minden ismert idegen szót angolra cserél, magyar oldalon a magyar szavakat meghagyja.
import DICT from "./dictionary.json";

const WORDS = DICT.words;
const AMBIGUOUS = new Set(DICT.ambiguous);
const HU = new Set(DICT.hu);
const WORD = /[\p{L}]+(?:['’-][\p{L}]+)*/gu;

function sameCase(src, dst, allCaps) {
  if (!dst) return dst;
  if (allCaps || (src.length > 1 && src === src.toUpperCase())) return dst.toUpperCase();
  if (src[0] !== src[0].toLowerCase()) return dst[0].toUpperCase() + dst.slice(1);
  return dst;
}

export function translateTitle(text, locale = "en") {
  if (!text) return text;
  const letters = [...text].filter((c) => c.toLowerCase() !== c.toUpperCase());
  const allCaps = letters.length > 0 && letters.filter((c) => c === c.toUpperCase()).length / letters.length > 0.8;
  const spaced = (at, len) => (at === 0 || /\s/.test(text[at - 1])) && (at + len === text.length || /\s/.test(text[at + len]));
  const out = text.replace(WORD, (w, at) => {
    const key = w.toLowerCase();
    if (!Object.prototype.hasOwnProperty.call(WORDS, key)) return w;
    if (locale === "hu" && HU.has(key)) return w;
    if (AMBIGUOUS.has(key) && !(w === key || allCaps)) return w;
    if (AMBIGUOUS.has(key) && key.length <= 2 && !spaced(at, w.length)) return w; // „z”, „s”: csak önálló szóként
    return sameCase(w, WORDS[key], allCaps);
  });
  return out
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([,.;:)])(?=\s|$)/g, "$1")
    .replace(/(\(|^)\s+/g, "$1")
    .replace(/^[\s\-–,]+|[\s\-–,]+$/g, "");
}
