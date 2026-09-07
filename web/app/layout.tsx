import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ChatDev 像素公司 — 官方算法交互复现",
  description: "进入像素风虚拟软件公司，交互学习 Chat Chain、角色分工、沟通式去幻觉与测试反馈。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: {
    title: "ChatDev Lab — 官方算法交互复现",
    description: "从需求到可执行软件：交互学习 Chat Chain 与沟通式去幻觉。",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "ChatDev Lab 算法工作流" }],
  },
  twitter: { card: "summary_large_image", images: ["/og.png"] },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
