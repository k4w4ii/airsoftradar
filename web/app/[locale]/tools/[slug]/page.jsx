import { cookies } from "next/headers";
import Link from "next/link";
import { notFound } from "next/navigation";
import Calculator from "../../../../components/tools/Calculators";
import ToolIcon from "../../../../components/tools/ToolIcon";
import { Shell } from "../../../../components/ui";
import { getRates } from "../../../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale } from "../../../../lib/i18n";
import { breadcrumbJsonLd, ldJson } from "../../../../lib/seo";
import { TOOLS, TOOLS_INDEX, toolBySlug, toolPath, toolText } from "../../../../lib/tools";

export async function generateMetadata({ params }) {
  const { locale, slug } = await params;
  const x = isLocale(locale) && toolBySlug(slug) ? toolText(slug, locale) : null;
  if (!x) return {};
  return {
    title: `${x.title} | AirsoftHunter`,
    description: x.description,
    alternates: { canonical: toolPath(locale, slug), languages: { hu: toolPath("hu", slug), en: toolPath("en", slug) } },
  };
}

// a címsorban megosztott beállítások (csak egyszerű szám/szöveg értékek)
const clean = (sp) => Object.fromEntries(Object.entries(sp || {}).filter(([k, v]) => /^[a-z]{1,8}$/.test(k) && typeof v === "string"
                                                                       && /^[0-9a-zA-Z.]{0,10}$/.test(v)));

export default async function ToolPage({ params, searchParams }) {
  const { locale, slug } = await params;
  const tool = toolBySlug(slug);
  if (!isLocale(locale) || !tool) notFound();
  const x = toolText(slug, locale);
  const T = TOOLS_INDEX[locale];
  const jar = await cookies();
  const c = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(c) ? c : DEFAULT_CURRENCY[locale];
  const rates = await getRates().catch(() => ({}));
  const faqLd = { "@context": "https://schema.org", "@type": "FAQPage",
                  mainEntity: x.faq.map(([q, a]) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })) };
  const crumbs = breadcrumbJsonLd([{ name: "AirsoftHunter", path: `/${locale}` }, { name: T.h1, path: toolPath(locale) },
                                   { name: x.name, path: toolPath(locale, slug) }]);
  return (
    <Shell locale={locale} currency={currency} path={toolPath(locale, slug)}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: ldJson(faqLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: ldJson(crumbs) }} />
      <article className="tools tool-page">
        <nav className="crumbs" aria-label="breadcrumb">
          <Link href={toolPath(locale)}>{T.h1}</Link><span aria-hidden="true"> / </span><span>{x.name}</span>
        </nav>
        <header className="tools-head">
          <h1><span className="tool-ico"><ToolIcon name={tool.icon} size={28} /></span>{x.h1}</h1>
          <p className="tools-intro">{x.intro}</p>
        </header>

        <Calculator slug={slug} locale={locale} currency={currency} rates={rates} initial={clean(await searchParams)} />

        <section className="tool-text">
          <h2>{T.how}</h2>
          {x.how.map((p, i) => <p key={i}>{p}</p>)}
          <p className="muted small">{T.disclaimer}</p>
        </section>

        <section className="tool-faq">
          <h2>{T.faq}</h2>
          {x.faq.map(([q, a]) => (
            <details key={q}>
              <summary>{q}</summary>
              <p>{a}</p>
            </details>
          ))}
        </section>

        <section className="tool-more">
          <h2>{T.others}</h2>
          <ul className="tool-cards small">
            {TOOLS.filter((t) => t.slug !== slug).map((t) => (
              <li key={t.slug}>
                <Link href={toolPath(locale, t.slug)} className="tool-card">
                  <span className="tool-ico"><ToolIcon name={t.icon} /></span>
                  <span className="tool-name">{toolText(t.slug, locale).name}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </article>
    </Shell>
  );
}
