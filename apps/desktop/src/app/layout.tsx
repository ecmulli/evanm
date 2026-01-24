import type { Metadata } from "next";
import "./globals.css";
import { WindowProvider } from "@/context/WindowContext";

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
      <body>
        <WindowProvider>
          {children}
        </WindowProvider>
      </body>
    </html>
  );
}
