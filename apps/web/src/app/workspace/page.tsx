import { redirect } from "next/navigation";
import { requireAccountProfile } from "@/lib/account-profile";
import AccountLoading from "@/components/account-loading";
import { Suspense } from "react";
import Screen from "@/components/workspace";
import { isClerkServerConfigured } from "@/lib/config/server";
async function ProtectedScreen() {
  const profile = await requireAccountProfile();
  if (!profile.onboarding_complete) redirect("/onboarding");
  return <Screen />;
}
export default function Page() {
  if (!isClerkServerConfigured) redirect("/login");
  return (
    <Suspense fallback={<AccountLoading />}>
      <ProtectedScreen />
    </Suspense>
  );
}
