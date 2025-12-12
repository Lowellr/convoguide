import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ConvoGuide - Adaptive Voice AI",
  description: "An adaptive conversational AI that responds to your mood and style",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
