"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main id="main" className="workspace">
      <h1>We couldn’t load this page.</h1>
      <p>Please try again in a moment.</p>
      <button className="button" onClick={reset}>
        Try again
      </button>
      <a href="/">Back to Alignn</a>
    </main>
  );
}
