import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/react";
import "./globals.css";

const BASE_URL = "https://denmark-home-calculator-mikr30lsh-thorandlokes-projects.vercel.app";

export const metadata: Metadata = {
  title: {
    default: "BoligBeregner Danmark - Gratis Boligberegner i Danmark",
    template: "%s | BoligBeregner Danmark",
  },
  description:
    "Gratis boligberegner der viser alle omkostninger ved køb, salg og renovering af bolig i Danmark. Inkluderer skjulte gebyrer, agentgebyrer og energioptimering.",
  keywords: [
    "boligberegner",
    "boliglån",
    "køb hus Danmark",
    "salg bolig",
    "energiforbedring",
    "varmepumpe",
    "solceller",
    "isolering",
    "ejendomsskat",
    "tinglysningsafgift",
    "boligomkostninger",
    "realkreditlån",
    "danmark bolig",
    "huspris Danmark",
  ],
  authors: [{ name: "BoligBeregner Danmark" }],
  creator: "BoligBeregner Danmark",
  metadataBase: new URL(BASE_URL),
  alternates: {
    canonical: BASE_URL,
    languages: {
      "da-DK": "/",
      "en-US": "/en",
      "zh-CN": "/zh",
    },
  },
  openGraph: {
    type: "website",
    locale: "da_DK",
    url: BASE_URL,
    siteName: "BoligBeregner Danmark",
    title: "BoligBeregner Danmark - Gratis Boligberegner i Danmark",
    description:
      "Beregn alle omkostninger ved køb, salg og renovering af bolig i Danmark. Gratis værktøj til boligejere og købere.",
    images: [
      {
        url: "/og-image.svg",
        width: 1200,
        height: 630,
        alt: "BoligBeregner Danmark - Beregn dine boligomkostninger",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "BoligBeregner Danmark",
    description: "Gratis boligberegner for Danmark - køb, salg og renovering",
    images: ["/og-image.svg"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="da">
      <body className="antialiased">
        {children}
        <Analytics />
      </body>
    </html>
  );
}
