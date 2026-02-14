import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "B&B RAG — Dashboard",
  description: "Plataforma SaaS de agentes SDR",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
