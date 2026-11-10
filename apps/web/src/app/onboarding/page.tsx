import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { Suspense } from "react";
import Screen from "@/components/onboarding";
async function ProtectedScreen() {
  await auth.protect();
  return <Screen />;
}
export default function Page() {
  if (
    !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
    !process.env.CLERK_SECRET_KEY
  )
    redirect("/login");
  return (
    <Suspense
      fallback={
        <main id="main" className="workspace">
          <p role="status">Loading your workspace…</p>
        </main>
      }
    >
      <ProtectedScreen />
    </Suspense>
  );
}
