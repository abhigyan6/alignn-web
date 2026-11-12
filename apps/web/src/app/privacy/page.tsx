import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/shell";

export const metadata: Metadata = {
  title: "Privacy policy",
  description:
    "How Alignn handles information while the product is coming soon.",
  alternates: { canonical: "/privacy" },
};

export default function PrivacyPage() {
  return (
    <MarketingShell>
      <section className="lp-doc-head">
        <div className="lp-wrap">
          <p className="lp-label">Legal</p>
          <h1>Privacy policy</h1>
          <p className="lp-draft">
            Draft for the coming-soon site. Last updated 12 November 2026. Not
            yet reviewed by a lawyer.
          </p>
        </div>
      </section>
      <section className="lp-doc">
        <div className="lp-wrap lp-prose">
          <p>
            Alignn is not launched yet. This page describes what this
            coming-soon site does with information today, and it will be updated
            before any sign-up or account feature opens.
          </p>

          <h2>What we collect today</h2>
          <p>
            The sign-up form on this site is switched off. We are not collecting
            email addresses or any other personal details through it. Nothing
            you type into a disabled field is sent to us.
          </p>
          <p>
            Like most websites, our hosting provider may keep standard server
            logs, such as IP address, browser type and the pages requested, for
            security and reliability.
          </p>

          <h2>Cookies and tracking</h2>
          <p>
            This page does not add advertising or analytics trackers. If account
            sign-in is enabled on the site, our authentication provider may set
            cookies that are needed to keep you signed in securely.
          </p>

          <h2>Before sign-up opens</h2>
          <p>
            When we start collecting information, we will explain here what we
            collect (for example, an email address or profile details), why, who
            processes it on our behalf, how long we keep it, and how you can
            access, correct or delete it. Resumes, if you choose to upload one,
            are planned to be kept in private storage and not sent to AI
            features by default.
          </p>

          <h2>Your choices</h2>
          <p>
            Because we are not collecting personal details through this page,
            there is nothing to withdraw today. Once that changes, this policy
            will describe how to exercise your rights.
          </p>

          <h2>Contact</h2>
          <p>
            A privacy contact will be published here before launch. Until then,
            please reach the team through the details on our{" "}
            <a href="/team">team page</a> when they are available.
          </p>

          <h2>Changes</h2>
          <p>
            We will update this policy and its date when our practices change.
          </p>
        </div>
      </section>
    </MarketingShell>
  );
}
