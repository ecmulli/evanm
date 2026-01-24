import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { WindowProvider } from "@/context/WindowContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "evanm.xyz",
  description: "A retro Mac OS inspired personal website",
  icons: {
    icon: [
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
      { url: "/pfp.svg", type: "image/svg+xml" },
    ],
    shortcut: "/favicon-32x32.png",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <WindowProvider>
          {children}
        </WindowProvider>
      </body>
    </html>
  );
}
