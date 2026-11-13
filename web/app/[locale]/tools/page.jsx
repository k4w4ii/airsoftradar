import { cookies } from "next/headers";
import Link from "next/link";
import { notFound } from "next/navigation";
import ToolIcon from "../../../components/tools/ToolIcon";
import { Shell } from "../../../components/ui";
import { altLanguages, CURRENCIES, DEFAULT_CURRENCY, isLocale } from "../../../lib/i18n";
import { breadcrumbJsonLd, ldJson } from "../../../lib/seo";
import { TOOLS, TOOLS_INDEX, toolPath, toolText } from "../../../lib/tools";

export async function generateMetadata({ params }) {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const T = TOOLS_INDEX[locale];
  return { title: `${T.title} | AirsoftHunter`, description: T.description,
           alternates: { canonical: toolPath(locale), languages: altLanguages((l) => toolPath(l)) } };
}

export default async function ToolsIndex({ params }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const jar = await cookies();
  const c = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(c) ? c : DEFAULT_CURRENCY[locale];
  const T = TOOLS_INDEX[locale];
  const crumbs = breadcrumbJsonLd([{ name: "AirsoftHunter", path: `/${locale}` }, { name: T.h1, path: toolPath(locale) }]);
  return (
    <Shell locale={locale} currency={currency} path={toolPath(locale)}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: ldJson(crumbs) }} />
      <article className="tools">
        <header className="tools-head">
          <h1>{T.h1}</h1>
          <p className="tools-intro">{T.intro}</p>
        </header>
        <ul className="tool-cards">
          {TOOLS.map((t) => {
            const x = toolText(t.slug, locale);
            return (
              <li key={t.slug}>
                <Link href={toolPath(locale, t.slug)} className="tool-card">
                  <span className="tool-ico"><ToolIcon name={t.icon} size={26} /></span>
                  <span className="tool-name">{x.name}</span>
                  <span className="tool-desc">{x.card}</span>
                  <span className="tool-open">{T.open} →</span>
                </Link>
              </li>
            );
          })}
        </ul>
        <p className="muted small tools-disc">{T.disclaimer}</p>
      </article>
    </Shell>
  );
}
