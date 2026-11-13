import { Chakra_Petch, Manrope, Montserrat } from "next/font/google";
import { cookies } from "next/headers";
import "../globals.css";
import { ADS, SITE_URL } from "../../lib/site";
import { isLocale } from "../../lib/i18n";

const body = Manrope({ subsets: ["latin", "latin-ext"], weight: ["400", "500", "600", "700"], variable: "--font-body", display: "swap" });
const brand = Montserrat({ subsets: ["latin"], weight: ["700", "800"], variable: "--font-brand", display: "swap" });
const display = Chakra_Petch({ subsets: ["latin", "latin-ext"], weight: ["500", "600", "700"], variable: "--font-display", display: "swap" });

export const metadata = {
  metadataBase: new URL(SITE_URL),
  applicationName: "AirsoftHunter",
  openGraph: { siteName: "AirsoftHunter", type: "website" },
  twitter: { card: "summary_large_image" },
  // AdSense webhely-ellenőrzés (csak ha be van állítva a hirdetéskód)
  ...(ADS.client ? { other: { "google-adsense-account": ADS.client } } : {}),
};

async function theme() {
  const jar = await cookies();
  return jar.get("theme")?.value === "dark" ? "dark" : "light";   // alapértelmezés: világos
}

export async function generateViewport() {
  const dark = (await theme()) === "dark";
  return { themeColor: dark ? "#1F1E1D" : "#FFFFFF", colorScheme: dark ? "dark" : "light" };
}

export default async function RootLayout({ children, params }) {
  const { locale } = await params;
  return (
    <html lang={isLocale(locale) ? locale : "en"} data-theme={await theme()} className={`${body.variable} ${display.variable} ${brand.variable}`}>
      <head>
        {/* betöltetlen (törölt / hotlink-tiltott) boltkép: nem a nyers alt-szöveg látszik, hanem egy halvány logó */}
        <script dangerouslySetInnerHTML={{ __html: "document.addEventListener('error',function(e){var t=e.target;if(t&&t.tagName==='IMG'&&!t.closest('.cat-tile')){t.style.visibility='hidden';t.parentNode&&t.parentNode.classList.add('noimg')}},true)" }} />
        {/* AdSense: csak akkor töltődik be, ha a hirdetéskód ki van töltve (lib/site.js). Automatikus hirdetések: az AdSense felületén KIKAPCSOLVA. */}
        {ADS.client ? (
          <script async crossOrigin="anonymous"
                  src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADS.client}`} />
        ) : null}
      </head>
      <body>{children}</body>
    </html>
  );
}
