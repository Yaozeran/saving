import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Saving · Sepolia savings",
  description: "A transparent, wallet-connected Sepolia savings vault.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
