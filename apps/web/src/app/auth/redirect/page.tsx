import { redirect } from "next/navigation";
import { requireAccountProfile } from "@/lib/account-profile";

export default async function Page() {
  const profile = await requireAccountProfile();
  redirect(profile.onboarding_complete ? "/workspace" : "/onboarding");
}
