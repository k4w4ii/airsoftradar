import Link from "next/link";
import { LOCALE_NAMES, LOCALES } from "../../lib/i18n";

export default function NotFound() {
  return (
    <main className="page empty">
      <p>Ilyen oldal nincs. / This page does not exist. / Diese Seite gibt es nicht. / Ta strona nie istnieje. / Tato stránka neexistuje.</p>
      <p>{LOCALES.map((l) => <Link key={l} href={`/${l}`} className="btn" hrefLang={l} lang={l}>{LOCALE_NAMES[l]}</Link>)}</p>
    </main>
  );
}
