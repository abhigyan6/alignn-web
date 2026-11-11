export const metadata = { title: "Alignn · Coming soon" };
export default function Home() {
  return (
    <main id="main" className="coming-soon-page">
      <section className="coming-soon-card" aria-labelledby="coming-soon-title">
        <div className="coming-soon-mark" aria-hidden="true">
          <svg viewBox="0 0 48 48">
            <path
              d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
              fill="none"
              stroke="currentColor"
              strokeWidth="5"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <p className="eyebrow">Alignn</p>
        <h1 id="coming-soon-title">A clearer path is coming soon.</h1>
        <p className="coming-soon-copy">
          We&apos;re putting the finishing touches on a better way to discover
          opportunities and take your next step with confidence.
        </p>
        <p className="coming-soon-note">Stay tuned.</p>
      </section>
    </main>
  );
}
