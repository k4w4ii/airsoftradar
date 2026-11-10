import { Chakra_Petch, Manrope, Montserrat } from "next/font/google";
import { cookies } from "next/headers";
import "../globals.css";
import { ADS, SITE_URL } from "../../lib/site";

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
    <html lang={locale === "hu" ? "hu" : "en"} data-theme={await theme()} className={`${body.variable} ${display.variable} ${brand.variable}`}>
      <head>
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
