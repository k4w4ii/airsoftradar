import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { Shell } from "../../../components/ui";
import { DOC_TITLES, DOCS, docFromSlug, legalContent } from "../../../lib/legal";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale } from "../../../lib/i18n";
import { OPERATOR } from "../../../lib/site";

export async function generateMetadata({ params }) {
  const { locale, doc: slug } = await params;
  const doc = docFromSlug(slug);
  if (!doc || !isLocale(locale)) return {};
  return {
    title: `${DOC_TITLES[locale][doc]} | AirsoftHunter`,
    alternates: { canonical: `/${locale}/${DOCS[doc][locale]}`, languages: { hu: `/hu/${DOCS[doc].hu}`, en: `/en/${DOCS[doc].en}` } },
  };
}

export default async function LegalPage({ params }) {
  const { locale, doc: slug } = await params;
  const doc = docFromSlug(slug);
  if (!isLocale(locale) || !doc) notFound();
  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];
  const sections = legalContent(locale, doc);
  const missing = OPERATOR.name.startsWith("[");
  return (
    <Shell locale={locale} currency={currency} path={`/${locale}/${DOCS[doc][locale]}`}>
      <article className="legal">
        <h1>{DOC_TITLES[locale][doc]}</h1>
        {missing ? <p className="legal-todo">{locale === "hu" ? "Az üzemeltetői adatok kitöltése folyamatban." : "Operator details are being completed."}</p> : null}
        {sections.map((s, i) => (
          <section key={i}>
            {s.h ? <h2>{s.h}</h2> : null}
            {(s.p || []).map((t, j) => <p key={j}>{t}</p>)}
            {s.list ? <ul>{s.list.map((t, j) => <li key={j}>{t}</li>)}</ul> : null}
          </section>
        ))}
      </article>
    </Shell>
  );
}
