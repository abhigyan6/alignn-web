import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { Suspense } from "react";
import Screen from "@/components/workspace";
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
        <main id="main" className="auth">
          <p role="status">Loading your account…</p>
        </main>
      }
    >
      <ProtectedScreen />
    </Suspense>
  );
}
