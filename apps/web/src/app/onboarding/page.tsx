import { redirect } from "next/navigation";
import { requireAccountProfile } from "@/lib/account-profile";
import AccountLoading from "@/components/account-loading";
import { Suspense } from "react";
import Screen from "@/components/onboarding";
type SearchParams = Promise<{ edit?: string | string[] }>;
async function ProtectedScreen({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const profile = await requireAccountProfile();
  const editing = (await searchParams).edit === "1";
  if (profile.onboarding_complete && !editing) redirect("/workspace");
  return <Screen initialProfile={profile} editing={editing} />;
}
export default function Page({ searchParams }: { searchParams: SearchParams }) {
  if (
    !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
    !process.env.CLERK_SECRET_KEY
  )
    redirect("/login");
  return (
    <Suspense fallback={<AccountLoading />}>
      <ProtectedScreen searchParams={searchParams} />
    </Suspense>
  );
}
