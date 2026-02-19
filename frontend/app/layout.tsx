import type { Metadata, Viewport } from "next";
import { Montserrat } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
  weight: ["100", "300", "400", "500", "700", "900"],
});

export const metadata: Metadata = {
  title: "Ultron Mark II",
  description: "Timekeeper Prototype",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#06b6d4",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${montserrat.variable} font-sans antialiased bg-white dark:bg-[#0a0f1a] text-slate-900 dark:text-slate-100 selection:bg-cyan-400 selection:text-white transition-colors`}
      >
        <div className="fixed top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400 z-50"></div>
        
        <Navbar />
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative">
          {/* Decorative background elements */}
          <div className="fixed top-32 right-8 w-64 h-64 border border-slate-100 dark:border-cyan-900/30 rounded-full opacity-20 pointer-events-none -z-10"></div>
          <div className="fixed bottom-12 left-12 w-px h-32 bg-gradient-to-b from-transparent via-cyan-200 dark:via-cyan-600 to-transparent opacity-50 pointer-events-none -z-10"></div>
          
          {children}
        </main>
      </body>
    </html>
  );
}
