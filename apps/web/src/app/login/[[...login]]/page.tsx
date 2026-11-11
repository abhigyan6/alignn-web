import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { SignIn } from "@clerk/nextjs";
import { Suspense } from "react";
import Link from "next/link";
export default async function Page() {
  if (
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
    process.env.CLERK_SECRET_KEY
  ) {
    const { userId } = await auth();
    if (userId) redirect("/auth/redirect");
  }
  if (
    !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
    !process.env.CLERK_SECRET_KEY
  )
    return (
      <main id="main" className="auth auth-page">
        <section className="auth-shell" aria-labelledby="auth-title">
          <div className="auth-story">
            <Link
              className="auth-mark"
              href="/explore"
              aria-label="Alignn home"
            >
              <svg aria-hidden="true" viewBox="0 0 48 48">
                <path
                  d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="5"
                  strokeLinecap="round"
                />
              </svg>
              <span>alignn</span>
            </Link>
            <div className="auth-story-copy">
              <h1 id="auth-title">
                Find the opportunity that fits your next chapter.
              </h1>
              <p>
                Sign in to keep your events, internships and competitions in one
                considered workspace.
              </p>
            </div>
            <div className="auth-signal" aria-hidden="true">
              <span>Discover</span>
              <span>Align</span>
              <span>Move forward</span>
            </div>
          </div>
          <div className="auth-panel">
            <div className="auth-panel-heading">
              <p className="auth-kicker">Welcome back</p>
              <h2>Sign in to Alignn</h2>
              <p>Pick up where your next step begins.</p>
            </div>
            <Link className="button auth-ghost-link" href="/explore">
              Continue browsing first
            </Link>
          </div>
        </section>
      </main>
    );
  return (
    <main id="main" className="auth auth-page">
      <section className="auth-shell" aria-labelledby="auth-title">
        <div className="auth-story">
          <Link className="auth-mark" href="/explore" aria-label="Alignn home">
            <svg aria-hidden="true" viewBox="0 0 48 48">
              <path
                d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
                fill="none"
                stroke="currentColor"
                strokeWidth="5"
                strokeLinecap="round"
              />
            </svg>
            <span>alignn</span>
          </Link>
          <div className="auth-story-copy">
            <h1 id="auth-title">
              Find the opportunity that fits your next chapter.
            </h1>
            <p>
              Sign in to keep your events, internships and competitions in one
              considered workspace.
            </p>
          </div>
          <div className="auth-signal" aria-hidden="true">
            <span>Discover</span>
            <span>Align</span>
            <span>Move forward</span>
          </div>
        </div>
        <div className="auth-panel">
          <Suspense
            fallback={
              <p className="auth-loading" role="status">
                Loading secure sign-in…
              </p>
            }
          >
            <SignIn
              routing="path"
              path="/login"
              signUpUrl="/signup"
              fallbackRedirectUrl="/auth/redirect"
              forceRedirectUrl="/auth/redirect"
              appearance={{
                variables: {
                  colorPrimary: "#123e2f",
                  colorBackground: "#f4f2e9",
                  borderRadius: "12px",
                  fontFamily: "Manrope, sans-serif",
                },
                elements: {
                  rootBox: "auth-clerk-root",
                  cardBox: "auth-clerk-box",
                  card: "auth-clerk-card",
                  footer: "auth-clerk-footer",
                  headerTitle: "auth-clerk-title",
                  headerSubtitle: "auth-clerk-subtitle",
                  socialButtonsBlockButton: "auth-clerk-social",
                  formButtonPrimary: "auth-clerk-primary",
                  formFieldInput: "auth-clerk-input",
                  footerActionLink: "auth-clerk-link",
                  identityPreviewEditButton: "auth-clerk-link",
                },
              }}
            />
          </Suspense>
          <Link className="auth-ghost-link" href="/explore">
            Continue browsing first
          </Link>
        </div>
      </section>
    </main>
  );
}
