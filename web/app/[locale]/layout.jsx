import { Barlow, Barlow_Condensed } from "next/font/google";
import "../globals.css";
import { SITE_URL } from "../../lib/site";

const body = Barlow({ subsets: ["latin", "latin-ext"], weight: ["400", "500", "600"], variable: "--font-body", display: "swap" });
const display = Barlow_Condensed({ subsets: ["latin", "latin-ext"], weight: ["500", "600", "700"], variable: "--font-display", display: "swap" });

export const metadata = {
  metadataBase: new URL(SITE_URL),
  applicationName: "AirsoftHunter",
  openGraph: { siteName: "AirsoftHunter", type: "website" },
  twitter: { card: "summary_large_image" },
};

export const viewport = { themeColor: "#1B2027", colorScheme: "dark" };

export default async function RootLayout({ children, params }) {
  const { locale } = await params;
  return (
    <html lang={locale === "hu" ? "hu" : "en"} className={`${body.variable} ${display.variable}`}>
      <body>{children}</body>
    </html>
  );
}
