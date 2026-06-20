import type { Metadata } from "next";
import { Inter, Hanken_Grotesk, JetBrains_Mono } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const hankenGrotesk = Hanken_Grotesk({
  variable: "--font-hanken-grotesk",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TradeGPT India",
  description: "Financial Intelligence Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${hankenGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-full bg-canvas text-text-primary font-body antialiased overflow-x-hidden">
        <div className="flex h-full w-full">
          {/* Persistent Left Sidebar */}
          <Sidebar />

          {/* Right Main Container */}
          <div className="flex-1 flex flex-col min-h-screen pl-[260px]">
            {/* Dynamic Header */}
            <Header />

            {/* Page Workspace Wrapper */}
            <main className="flex-1 pt-14 flex flex-col bg-canvas">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
