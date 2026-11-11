// Partnersablon nélkül utm-jelölést kap (a bolt a saját statisztikájában lássa, honnan jött a vásárló).
// A Referer fejlécet nem küldjük (no-referrer): egyes boltok a külső Refererre hibás átirányítással válaszoltak.
export function withUtm(url) {
  try {
    const u = new URL(url);
    if (!u.searchParams.has("utm_source")) {
      u.searchParams.set("utm_source", "airsofthunter");
      u.searchParams.set("utm_medium", "referral");
    }
    return u.toString();
  } catch {
    return url;
  }
}

/** A bolti cél-URL: partnersablon ({url} helyére a termékoldal), különben utm-jelölés. Csak http(s) cél; egyébként null. */
export function shopTarget(url, template) {
  if (!url) return null;
  const target = template ? template.replace("{url}", encodeURIComponent(url)) : withUtm(url);
  return /^https?:\/\//i.test(target) ? target : null;
}

/** Külső képcím biztonságosan: csak http(s), a szóközök és egyéb tiltott karakterek kódolva (pl. atom-airsoft „a b,c.jpg”). */
export function imgSrc(url) {
  if (!url || typeof url !== "string") return null;
  try {
    const u = new URL(url.trim().replace(/ /g, "%20"));
    return u.protocol === "https:" || u.protocol === "http:" ? u.href : null;
  } catch {
    return null;
  }
}
