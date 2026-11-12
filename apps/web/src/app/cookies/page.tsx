import type { Metadata } from "next";
import LegalPage from "@/components/legal-page";
export const metadata: Metadata = { title: "Cookie information \u00b7 Alignn" };
export default function Page() {
  return (
    <LegalPage
      title="Cookie information"
      intro="What browser storage supports Alignn and how to manage it."
      sections={[
        {
          title: "Sign-in and security cookies",
          text: "Clerk uses cookies to maintain authentication and session state. Its documentation identifies cookies such as __session and __client_uat. Actual cookie names, domains and lifetimes depend on the configured Clerk instance and session settings; this is not a production cookie inventory. Blocking necessary sign-in cookies can prevent authentication.",
        },
        {
          title: "Notice preference",
          text: "When you dismiss our cookie notice, Alignn stores alignn-cookie-notice in local storage on that browser. It only remembers that the notice was dismissed; it is not agreement to optional tracking. It remains until site storage is cleared or the notice version changes.",
        },
        {
          title: "Optional tracking",
          text: "The current application source does not integrate optional advertising or analytics scripts. There are no optional tracking categories to enable in this version. Before adding them, their purposes, providers and retention must be disclosed and any required consent controls must prevent loading them until a choice is made.",
        },
        {
          title: "Your controls",
          text: "Use your browser’s site-data settings to inspect or clear cookies and local storage. Clearing site data can sign you out and show this notice again. Authentication cookie settings are managed by Clerk; dismissing this notice does not disable them.",
        },
        {
          title: "External platforms",
          text: "When you follow an opportunity link or use an external sign-in provider, that service can use its own cookies under its own policies. Review those policies on the destination site.",
        },
      ]}
    />
  );
}
