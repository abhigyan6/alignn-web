import Link from "next/link";
import type { ReactNode } from "react";
import { LogoMark } from "./logo";
import "./marketing.css";

const navLinks = [
  { href: "/#coming", label: "What’s coming" },
  { href: "/#how", label: "How it works" },
  { href: "/#preview", label: "Preview" },
  { href: "/#faq", label: "FAQ" },
];

export function SiteNav() {
  return (
    <header className="lp-nav">
      <div className="lp-nav-inner">
        <div className="lp-nav-brand">
          <Link className="lp-logo" href="/" aria-label="Alignn home">
            <LogoMark className="lp-logo-mark" />
            <span>alignn</span>
          </Link>
          <span className="lp-pill">Coming soon</span>
        </div>
        <nav aria-label="Primary" className="lp-nav-links">
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="lp-footer">
      <div className="lp-wrap lp-footer-top">
        <p className="lp-footer-tag">The missing link to your future.</p>
        <nav aria-label="Footer" className="lp-footer-links">
          <Link href="/team">Meet our team</Link>
          <Link href="/privacy">Privacy policy</Link>
          <Link href="/terms">Terms and conditions</Link>
        </nav>
      </div>
      <p aria-hidden="true" className="lp-wordmark">
        alignn
      </p>
      <p className="lp-wrap lp-footer-legal">
        Coming soon. Launch date to be announced.
      </p>
    </footer>
  );
}

/** Nav + footer wrapper shared by the landing page and the legal/team pages. */
export function MarketingShell({
  children,
  mainClassName = "",
}: {
  children: ReactNode;
  mainClassName?: string;
}) {
  return (
    <div className="lp">
      <SiteNav />
      <main id="main" className={`lp-main ${mainClassName}`.trim()}>
        {children}
      </main>
      <SiteFooter />
    </div>
  );
}
