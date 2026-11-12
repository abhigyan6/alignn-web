import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/shell";

export const metadata: Metadata = {
  title: "Terms and conditions",
  description: "Terms for using the Alignn coming-soon website.",
  alternates: { canonical: "/terms" },
};

export default function TermsPage() {
  return (
    <MarketingShell>
      <section className="lp-doc-head">
        <div className="lp-wrap">
          <p className="lp-label">Legal</p>
          <h1>Terms and conditions</h1>
          <p className="lp-draft">
            Draft for the coming-soon site. Last updated 12 November 2026. Not
            yet reviewed by a lawyer.
          </p>
        </div>
      </section>
      <section className="lp-doc">
        <div className="lp-wrap lp-prose">
          <p>
            These terms cover your use of the Alignn coming-soon website. The
            Alignn product itself has not launched, and separate terms will
            apply when accounts and features open.
          </p>

          <h2>About this site</h2>
          <p>
            This site describes what Alignn plans to build. Features are shown
            as in development, planned or later, and may change or never be
            released. Anything marked “Example” is an illustration, not a real
            listing, match, result or statistic.
          </p>

          <h2>No offers or advice</h2>
          <p>
            Nothing on this site is an offer of employment, an admission
            decision, or career, legal or financial advice. Opportunities will
            link to their original organizers, who set their own rules and make
            their own decisions.
          </p>

          <h2>Using the site</h2>
          <ul>
            <li>Use it lawfully and do not try to disrupt or probe it.</li>
            <li>Do not scrape it at a volume that affects other visitors.</li>
          </ul>

          <h2>Intellectual property</h2>
          <p>
            The Alignn name, logo, design and text belong to Alignn unless
            stated otherwise. Third-party fonts are used under their open
            licences.
          </p>

          <h2>Availability and liability</h2>
          <p>
            The site is provided as is, without promises of uptime or accuracy.
            To the extent the law allows, Alignn is not liable for losses
            arising from your use of this coming-soon site.
          </p>

          <h2>Governing law and contact</h2>
          <p>
            The governing law and a contact address will be added here before
            launch. See also our <a href="/privacy">privacy policy</a>.
          </p>

          <h2>Changes</h2>
          <p>
            We may update these terms, and will change the date above when we
            do.
          </p>
        </div>
      </section>
    </MarketingShell>
  );
}
