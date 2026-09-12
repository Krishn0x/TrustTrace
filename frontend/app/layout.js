import "./globals.css";

export const metadata = {
  title: "TrustTrace",
  description: "Service dependency mapping and blast radius simulation",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
