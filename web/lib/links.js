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
