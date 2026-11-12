import { AuthProvider, SessionBridge } from "@/components/auth-provider";
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import AppNavigation from "@/components/app-navigation";
import { BrandMark } from "@/components/icon";
export const metadata: Metadata = {
  title: "Alignn · Find your next opportunity",
  description:
    "Discover Indian internships, hackathons and events. Build a student profile, save opportunities and track your next steps with Alignn.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  const configured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  const content = (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <Link className="brand" href="/">
          <BrandMark />
          alignn
        </Link>
        <AppNavigation authenticated={configured} />
      </header>
      {configured ? <SessionBridge>{children}</SessionBridge> : children}
      <footer className="site-footer">
        <Link className="footer-brand" href="/">
          alignn<span>Find your next opportunity.</span>
        </Link>
        <p>Built for students. Connected to the original source.</p>
        <Link href="/explore">Explore opportunities</Link>
      </footer>
    </>
  );
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {configured ? <AuthProvider>{content}</AuthProvider> : content}
      </body>
    </html>
  );
}
