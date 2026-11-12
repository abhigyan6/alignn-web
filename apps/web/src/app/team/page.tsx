import type { Metadata } from "next";
import { MarketingShell } from "@/components/marketing/shell";
import { teamMembers } from "@/lib/team";

export const metadata: Metadata = {
  title: "Meet our team",
  description: "The people building Alignn.",
  alternates: { canonical: "/team" },
};

export default function TeamPage() {
  return (
    <MarketingShell>
      <section className="lp-doc-head">
        <div className="lp-wrap">
          <p className="lp-label">Team</p>
          <h1>Meet our team</h1>
          <p className="lp-section-intro">
            The people building Alignn, the missing link to your future.
          </p>
        </div>
      </section>
      <section className="lp-doc">
        <div className="lp-wrap">
          {teamMembers.length > 0 ? (
            <ul className="lp-team-grid">
              {teamMembers.map((person) => (
                <li className="lp-person" key={person.name}>
                  <h2>{person.name}</h2>
                  <p>{person.role}</p>
                  {person.bio ? <p>{person.bio}</p> : null}
                </li>
              ))}
            </ul>
          ) : (
            <>
              <p className="lp-team-intro">
                We’re still putting this page together. Team members will be
                introduced here before launch.
              </p>
              <ul aria-label="Example team card" className="lp-team-grid">
                <li className="lp-person">
                  <span className="lp-example">Example</span>
                  <div aria-hidden="true" className="lp-person-photo" />
                  <h2>Name to come</h2>
                  <p>Role to come</p>
                </li>
              </ul>
            </>
          )}
        </div>
      </section>
    </MarketingShell>
  );
}
