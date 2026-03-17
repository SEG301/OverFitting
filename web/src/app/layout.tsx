import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "vietnamese"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "OverFitting | Vietnamese Enterprise Search",
  description: "Advanced Hybrid Search Engine powered by BM25, FAISS, and Cross-Encoder.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className={`${inter.variable} font-sans antialiased text-gray-800`}>
        {children}
      </body>
    </html>
  );
}
