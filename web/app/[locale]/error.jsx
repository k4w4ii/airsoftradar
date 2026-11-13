"use client";

export default function Error({ error, reset }) {
  return (
    <main className="page empty">
      <p>Az adatok most nem érhetők el. / Data is temporarily unavailable. / Daten vorübergehend nicht verfügbar. / Dane są chwilowo niedostępne. / Data jsou dočasně nedostupná.</p>
      <p className="muted small">{error?.message}</p>
      <button className="btn" onClick={() => reset()}>Újra / Retry / Erneut / Ponów / Znovu</button>
    </main>
  );
}
