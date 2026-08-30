import type { Metadata } from "next";
import localFont from "next/font/local";

import { Providers } from "@/app/providers";

import "./globals.css";

const estedad = localFont({
  src: "./fonts/Estedad-Variable.woff2",
  variable: "--font-estedad",
  weight: "100 900",
  style: "normal",
  display: "swap",
  fallback: ["Tahoma", "Arial", "sans-serif"],
});

export const metadata: Metadata = {
  title: "آواتو | ویس و عکس‌هات رو بده؛ ریلز آماده تحویل بگیر",
  description:
    "ساخت خودکار ویدیوی عمودی زیرنویس‌دار از ویس فارسی و عکس‌های شخصی، بدون نیاز به ادیت حرفه‌ای.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body className={estedad.variable}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
