import type { Metadata } from "next";
import "./globals.css";
import { WindowProvider } from "@/context/WindowContext";

export const metadata: Metadata = {
  title: "Retro Desktop",
  description: "A retro Mac OS inspired personal website",
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
