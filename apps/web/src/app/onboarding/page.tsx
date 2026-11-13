import { redirect } from "next/navigation";
import { requireAccountProfile } from "@/lib/account-profile";
import AccountLoading from "@/components/account-loading";
import { Suspense } from "react";
import Screen from "@/components/onboarding";
import { isClerkServerConfigured } from "@/lib/config";
type SearchParams = Promise<{ edit?: string | string[] }>;
async function ProtectedScreen({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const profile = await requireAccountProfile();
  const editing = (await searchParams).edit === "1";
  if (profile.onboarding_complete && !editing) redirect("/explore");
  return <Screen initialProfile={profile} editing={editing} />;
}
export default function Page({ searchParams }: { searchParams: SearchParams }) {
  if (!isClerkServerConfigured) redirect("/login");
  return (
    <Suspense fallback={<AccountLoading onboarding />}>
      <ProtectedScreen searchParams={searchParams} />
    </Suspense>
  );
}
