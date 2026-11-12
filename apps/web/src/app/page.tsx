import type { Metadata } from "next";
import Link from "next/link";
import { LogoMark } from "@/components/marketing/logo";
import { RevealText } from "@/components/marketing/reveal-text";
import { MarketingShell } from "@/components/marketing/shell";
import { SignupForm } from "@/components/marketing/signup-form";

const title = "Alignn | The missing link to your future";
const description =
  "Alignn brings internships, jobs, hackathons and competitions into one place, matched to your profile. Coming soon.";

export const metadata: Metadata = {
  title: { absolute: title },
  description,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "Alignn",
    title,
    description,
    url: "/",
  },
  twitter: { card: "summary", title, description },
};

const bandItems = ["Internships", "Jobs", "Hackathons", "Competitions"];

const manifesto =
  "Opportunities are scattered. Deadlines arrive quietly. Eligibility is a guess. Alignn gathers it all in one place, shows you why you fit, and reminds you in time.";

const notes = [
  {
    title: "Real listings only",
    body: "No mock data. The feed stays empty until published records exist.",
  },
  {
    title: "AI explains, never decides",
    body: "Eligibility comes from the rules each opportunity publishes.",
  },
  {
    title: "Apply at the source",
    body: "Every opportunity links to its original organizer.",
  },
];

const steps = [
  {
    title: "Create your profile",
    body: "Degree, skills, projects and interests. A resume upload is optional and stays private.",
  },
  {
    title: "See what fits, and why",
    body: "Browse opportunities ordered by fit. Each says which requirements you meet and which you don’t.",
  },
  {
    title: "Apply and keep track",
    body: "Apply through the original organizer, then follow each stage and next action from your workspace.",
  },
];

const feed = [
  { kind: "Internship", lines: ["m", "s"] },
  { kind: "Hackathon", lines: ["s", "m"] },
  { kind: "Job", lines: ["m", "s"] },
  { kind: "Competition", lines: ["s", "m"] },
];

const faqs = [
  {
    q: "When does Alignn launch?",
    a: "We haven’t set a launch date. This page will change when we have one.",
  },
  {
    q: "Who is Alignn for?",
    a: "Students and early-career candidates looking for internships, jobs, hackathons and competitions.",
  },
  {
    q: "Will AI decide whether I’m eligible?",
    a: "No. Eligibility comes from the rules each opportunity publishes. AI may help explain a result in simple words, but it never makes the decision.",
  },
  {
    q: "Where will the opportunities come from?",
    a: "Alignn links to the original organizer, so you always apply at the source. The catalog stays empty until real, published records exist.",
  },
  {
    q: "What happens to my resume?",
    a: "Uploading one is optional. Resumes are kept in private storage and are not sent to AI features by default.",
  },
];

function BandGroup({ hidden = false }: { hidden?: boolean }) {
  return (
    <ul
      aria-hidden={hidden || undefined}
      className="lp-band-group"
      aria-label={hidden ? undefined : "Opportunity types"}
    >
      {bandItems.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default function Home() {
  return (
    <MarketingShell>
      <section aria-labelledby="hero-title" className="lp-hero">
        <LogoMark className="lp-hero-loop" />
        <div className="lp-wrap lp-hero-content">
          <div className="lp-hero-meta">
            <span className="lp-hero-tag">Coming soon</span>
            <span className="lp-hero-date">Launch date to be announced</span>
          </div>
          <h1 id="hero-title">
            The missing link to your <em>future.</em>
          </h1>
          <p className="lp-lead">
            Internships, jobs, hackathons and competitions in one place, matched
            to your profile, with the reason you qualify spelled out, before the
            deadline.
          </p>
          <div className="lp-actions">
            <Link className="lp-btn lp-btn-primary" href="#coming">
              See what’s coming
            </Link>
            <Link className="lp-btn lp-btn-ghost" href="#how">
              How it will work
            </Link>
          </div>
        </div>
        <div className="lp-band">
          <div className="lp-band-track">
            <BandGroup />
            <BandGroup hidden />
          </div>
        </div>
      </section>

      <section aria-labelledby="why-title" className="lp-section" id="why">
        <div className="lp-wrap">
          <p className="lp-label">
            <b>(01)</b> Why Alignn
          </p>
          <h2 className="lp-sr" id="why-title">
            Why Alignn
          </h2>
          <RevealText text={manifesto} />
          <ul className="lp-notes">
            {notes.map((note) => (
              <li key={note.title}>
                <h3>{note.title}</h3>
                <p>{note.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section
        aria-labelledby="coming-title"
        className="lp-section lp-building"
        id="coming"
      >
        <div className="lp-wrap">
          <p className="lp-label">
            <b>(02)</b> What’s coming
          </p>
          <div className="lp-head-row">
            <h2 className="lp-section-title" id="coming-title">
              What we’re building.
            </h2>
            <p className="lp-head-note">
              Each part says where it really stands: in development, planned, or
              later.
            </p>
          </div>

          <div className="lp-bento">
            <div className="lp-bento-row">
              <article className="lp-tile lp-tile-dark">
                <div className="lp-tile-top">
                  <span className="lp-status">In development</span>
                  <h3>Discovery built around your profile</h3>
                  <p>
                    Add your skills, projects and interests once. Alignn orders
                    internships, jobs, hackathons and competitions by how well
                    they fit you.
                  </p>
                </div>
                <ul aria-label="Example match rows" className="lp-mock-rows">
                  {[
                    "You meet 4 of 5",
                    "You meet 5 of 5",
                    "You meet 3 of 5",
                  ].map((chip) => (
                    <li className="lp-mock-row" key={chip}>
                      <span aria-hidden="true" className="lp-mock-lines">
                        <i />
                        <i />
                      </span>
                      <span
                        className="lp-chip"
                        data-hot={chip.includes("5 of 5") || undefined}
                      >
                        {chip}
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="lp-tile-caption">
                  Example. Illustration only, not real matches.
                </p>
              </article>

              <article className="lp-tile lp-tile-amber">
                <div className="lp-tile-top">
                  <span className="lp-status">In development</span>
                  <h3>Saved opportunities, deadlines in full</h3>
                </div>
                <div>
                  <p className="lp-bigdate">Jan 18</p>
                  <p className="lp-date-sub">11:59 PM IST. Closes in 6 days.</p>
                  <p className="lp-tile-caption">
                    Example. We always show the exact date, time zone and
                    urgency.
                  </p>
                </div>
              </article>
            </div>

            <div className="lp-bento-row">
              <article className="lp-tile lp-tile-sm lp-tile-surface">
                <div className="lp-tile-top">
                  <span className="lp-status">In development</span>
                  <h3>Eligibility in plain words</h3>
                  <p>Clear rules decide. AI explains, never decides.</p>
                </div>
                <ul className="lp-checks">
                  <li>Degree</li>
                  <li>Branch</li>
                  <li>Graduation year</li>
                  <li data-fail="true">
                    <span className="lp-sr">Not met: </span>CGPA: below the
                    minimum
                  </li>
                </ul>
                <p className="lp-tile-caption">Example. Not a real result.</p>
              </article>

              <article className="lp-tile lp-tile-sm lp-tile-tint">
                <div className="lp-tile-top">
                  <span className="lp-status">In development</span>
                  <h3>Application tracker</h3>
                  <p>Apply on the organizer’s site. Track every stage here.</p>
                </div>
                <ol aria-label="Example stages" className="lp-stages">
                  <li>Saved</li>
                  <li>Applied</li>
                  <li data-todo="true">Interview</li>
                  <li data-todo="true">Offer</li>
                </ol>
                <p className="lp-tile-caption">
                  Example. Stages are illustrative.
                </p>
              </article>

              <article className="lp-tile lp-tile-sm lp-tile-dashed">
                <div className="lp-tile-top">
                  <span className="lp-status" data-status="planned">
                    Planned
                  </span>
                  <h3>Skill-gap planning</h3>
                  <p>
                    A short weekly focus list from the opportunities you saved.
                  </p>
                </div>
                <hr className="lp-rule" />
                <div className="lp-tile-top">
                  <span className="lp-status" data-status="later">
                    Later
                  </span>
                  <h3>Career Radar</h3>
                  <p>
                    Predicted hiring windows, always labelled as predictions.
                  </p>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section
        aria-labelledby="how-title"
        className="lp-section lp-how"
        id="how"
      >
        <div className="lp-wrap">
          <p className="lp-label">
            <b>(03)</b> How it will work
          </p>
          <h2 className="lp-section-title" id="how-title">
            Three steps from blank to applied.
          </h2>
          <ol className="lp-how-list">
            {steps.map((step, index) => (
              <li className="lp-how-row" key={step.title}>
                <span aria-hidden="true" className="lp-numeral">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section
        aria-labelledby="preview-title"
        className="lp-section lp-preview"
        id="preview"
      >
        <div className="lp-wrap">
          <p className="lp-label">
            <b>(04)</b> Preview
          </p>
          <h2 className="lp-section-title" id="preview-title">
            Your feed will live here.
          </h2>
          <div className="lp-window-wrap">
            <p className="lp-sticker">Coming soon</p>
            <div className="lp-window">
              <div className="lp-window-bar">
                <span aria-hidden="true" className="lp-dots">
                  <i />
                  <i />
                  <i />
                </span>
                <span className="lp-window-title">Opportunity feed</span>
                <span className="lp-example">Example</span>
              </div>
              <div className="lp-window-body">
                <div aria-hidden="true" className="lp-side">
                  <span className="lp-bar" style={{ width: "90%" }} />
                  <span className="lp-bar" style={{ width: "60%" }} />
                  <span className="lp-bar" style={{ width: "80%" }} />
                  <span className="lp-bar" style={{ width: "50%" }} />
                  <span className="lp-bar" style={{ width: "70%" }} />
                </div>
                <ul aria-label="Example feed rows" className="lp-feed">
                  <li aria-hidden="true" className="lp-search" />
                  {feed.map((row) => (
                    <li className="lp-feed-row" key={row.kind}>
                      <span className="lp-kind">{row.kind}</span>
                      <span aria-hidden="true" className="lp-feed-lines">
                        <span className="lp-bar" data-w={row.lines[0]} />
                        <span className="lp-bar" data-w={row.lines[1]} />
                      </span>
                      <span aria-hidden="true" className="lp-feed-action" />
                      <span className="lp-example">Example</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          <p className="lp-preview-note">
            Example only. There are no listings yet; the feed stays empty until
            real, published records exist.
          </p>
        </div>
      </section>

      <section
        aria-labelledby="faq-title"
        className="lp-section lp-faq"
        id="faq"
      >
        <div className="lp-wrap">
          <p className="lp-label">Questions</p>
          <h2 className="lp-section-title" id="faq-title">
            Before we launch
          </h2>
          <div className="lp-faq-list">
            {faqs.map((item) => (
              <details key={item.q} name="faq">
                <summary>{item.q}</summary>
                <p>{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="join-title" className="lp-join" id="join">
        <span aria-hidden="true" className="lp-join-arc" data-a="" />
        <span aria-hidden="true" className="lp-join-arc" data-b="" />
        <span aria-hidden="true" className="lp-join-arc" data-c="" />
        <div className="lp-wrap">
          <h2 id="join-title">A clearer path is on its way.</h2>
          <p className="lp-lead">
            Early-access sign-up isn’t open yet. When it opens, you’ll join
            right here.
          </p>
          <SignupForm />
        </div>
      </section>
    </MarketingShell>
  );
}
