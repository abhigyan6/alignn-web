import { AuthProvider, SessionBridge } from "@/components/auth-provider";
import { SiteChrome } from "@/components/site-chrome";
import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.PUBLIC_ORIGIN ?? "http://localhost:3000"),
  title: {
    default: "Alignn | The missing link to your future",
    template: "%s | Alignn",
  },
  description:
    "Alignn brings internships, jobs, hackathons and competitions into one place, matched to your profile. Coming soon.",
};

export const viewport: Viewport = {
  themeColor: "#0c3c29",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const configured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  const content = (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <SiteChrome>
        {configured ? <SessionBridge>{children}</SessionBridge> : children}
      </SiteChrome>
    </>
  );
  return (
    <html lang="en">
      <body>
        {configured ? <AuthProvider>{content}</AuthProvider> : content}
      </body>
    </html>
  );
}
