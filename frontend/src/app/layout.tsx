import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BharatQuery — Cross-Lingual Public Data Explorer",
  description:
    "Autonomous Multi-Agent Cross-Lingual Text-to-SQL Swarm for Indian Open Government Data (NDAP). Ask questions in your mother tongue and get verified answers.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col font-sans bg-slate-50 text-slate-900 selection:bg-ashoka-200">
        {children}
      </body>
    </html>
  );
}

