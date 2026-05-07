import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vila INTEIA — Predição Política BR 2026",
  description: "PC-CRD cohort + Linzer ensemble. 94.16% acc 6-cycle backtest.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
