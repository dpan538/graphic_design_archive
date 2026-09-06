import { projectJsonLd, safeJsonLd } from "@/features/machine-reading/project";
import type { Metadata, Viewport } from "next";
import { Baskervville, Instrument_Sans, Inter } from "next/font/google";
import "./globals.css";

/* Display / large headings — transitional serif, size-driven hierarchy. */
const baskervville = Baskervville({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--font-baskervville",
  display: "swap",
});

/* Body — humanist grotesque, minimum 16px. */
const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-instrument",
  display: "swap",
});

/* Numerals only — weights 200 / 300 / 400. */
const inter = Inter({
  subsets: ["latin"],
  weight: ["200", "300", "400"],
  variable: "--font-inter",
  display: "swap",
});

export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover" };

export const metadata: Metadata = {
  metadataBase: new URL("https://mgdarchive.com"),
  title: {
    default: "Modern Graphic Design Archive",
    template: "%s — Modern Graphic Design Archive",
  },
  description:
    "A verified, extensible platform for reading, locating, and exploring modern graphic design history — for design researchers, learners, and AI research tools.",
};

export default function RootLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  /* Parallel slot for navigations intercepted as overlays (Search), so the
     page they were opened from stays mounted underneath. */
  modal: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${baskervville.variable} ${instrumentSans.variable} ${inter.variable}`}
    >
      <head><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(projectJsonLd) }} /></head>
      <body>
        {children}
        {modal}
      </body>
    </html>
  );
}
