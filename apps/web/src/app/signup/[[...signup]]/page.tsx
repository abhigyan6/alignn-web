import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { SignUp } from "@clerk/nextjs";
import { Suspense } from "react";
import AuthShell, { authAppearance } from "@/components/auth-shell";

export default async function Page() {
  if (
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
    process.env.CLERK_SECRET_KEY
  ) {
    const { userId } = await auth();
    if (userId) redirect("/auth/redirect");
  }
  const configured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
    process.env.CLERK_SECRET_KEY,
  );
  return (
    <AuthShell
      title="Make room for your next chapter."
      description="Create your profile to find events, internships and opportunities that fit where you want to go."
    >
      {configured ? (
        <Suspense
          fallback={
            <p className="auth-loading" role="status">
              Loading secure signup…
            </p>
          }
        >
          <SignUp
            routing="path"
            path="/signup"
            signInUrl="/login"
            fallbackRedirectUrl="/auth/redirect"
            forceRedirectUrl="/auth/redirect"
            appearance={authAppearance}
          />
        </Suspense>
      ) : (
        <div className="auth-panel-heading">
          <h2>Create your Alignn account</h2>
          <p>
            Account access is being connected. You can explore opportunities in
            the meantime.
          </p>
        </div>
      )}
    </AuthShell>
  );
}
