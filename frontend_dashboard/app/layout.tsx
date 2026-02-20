import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "B&B RAG — Dashboard",
  description: "Plataforma SaaS de agentes SDR",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className="w-full overflow-x-hidden">
      <body className="w-full min-w-0 max-w-full overflow-x-hidden">{children}</body>
    </html>
  );
}
