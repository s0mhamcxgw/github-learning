import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "黔数 · 数据政策研究台",
  description: "聚焦贵州与全国的数据要素流通、数据交易、数据工厂、数据质量、高质量数据集和可信数据空间。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
