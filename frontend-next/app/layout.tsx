import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vila INTEIA - Previsões Políticas BR 2026",
  description: "Painel de previsões políticas em português claro, com chances, cenários e teste histórico.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
