import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { BRAND } from "../lib/brand";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: `${BRAND.name} — ${BRAND.descriptor}`,
  description: BRAND.shortDescription,
  keywords: [
    "portfolio management",
    "SEBI RIA",
    "Indian equities",
    "Markowitz optimization",
    "portfolio diagnosis",
    "rebalancing engine",
    "wealth management",
  ],
  authors: [{ name: BRAND.legalName }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#F7F6F1] text-[#142A3B]">
        {children}
      </body>
    </html>
  );
}
