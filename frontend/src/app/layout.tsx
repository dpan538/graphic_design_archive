import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Archive Box — Modern Graphic Design History",
  description:
    "Rights-aware archive index for modern graphic design history. A reading and source-navigation prototype.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="archive">
      <body className="font-mono antialiased">{children}</body>
    </html>
  );
}
