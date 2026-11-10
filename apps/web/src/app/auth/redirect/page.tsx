import { redirect } from "next/navigation";
import AccountLoading from "@/components/account-loading";
import { requireAccountProfile } from "@/lib/account-profile";

export default async function Page() {
  const profile = await requireAccountProfile();
  redirect(profile.onboarding_complete ? "/workspace" : "/onboarding");
  return <AccountLoading />;
}
