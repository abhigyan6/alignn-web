import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { SignUp } from "@clerk/nextjs";
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
      <main id="main" className="auth">
        <section>
          <h1>Sign-in is being connected.</h1>
          <p>
            Clerk development keys are not configured yet. Opportunity discovery
            is still available.
          </p>
          <Link className="button" href="/explore">
            Explore opportunities
          </Link>
        </section>
      </main>
    );
  return (
    <main id="main" className="auth">
      <section>
        <p className="brand-note">Find your people. Find your next step.</p>
        <h1>Make room for your next chapter.</h1>
        <Suspense fallback={<p role="status">Loading secure sign-in…</p>}>
          <SignUp
            routing="path"
            path="/signup"
            signInUrl="/login"
            fallbackRedirectUrl="/auth/redirect"
            forceRedirectUrl="/auth/redirect"
          />
        </Suspense>
      </section>
    </main>
  );
}
