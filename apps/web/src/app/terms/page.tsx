import type { Metadata } from "next";
import LegalPage from "@/components/legal-page";
export const metadata: Metadata = { title: "Terms & conditions \u00b7 Alignn" };
export default function Page() {
  return (
    <LegalPage
      title="Terms & conditions"
      intro="The current scope of Alignn and the responsibilities that come with using it."
      sections={[
        {
          title: "What Alignn provides",
          text: "Alignn helps students discover externally listed internships, hackathons and events, build a profile, inspect profile-based relevance, save opportunities and manually track applications. Alignn does not run the listed events, select applicants or submit applications on your behalf.",
        },
        {
          title: "Accounts and your information",
          text: "Keep account access secure and provide information you are entitled to share. You remain responsible for reviewing profile details and application records. Do not impersonate someone else or upload another person’s private material without permission.",
        },
        {
          title: "Opportunity information and recommendations",
          text: "Listings come from external sources and can change or expire. Check the original platform for current deadlines, eligibility, fees and application instructions. A profile-fit score is informational and does not guarantee eligibility, admission, an interview or employment.",
        },
        {
          title: "Applying on external platforms",
          text: "An external Apply link takes you to a separate service with its own terms and privacy policy. Saving or tracking in Alignn does not complete an application. You decide whether to apply and what information to share with the original platform.",
        },
        {
          title: "Acceptable use",
          text: "Do not attempt unauthorized access, disrupt the service, distribute malware, abuse other users, bypass security controls or use Alignn to distribute unlawful material. Report suspicious listings or security concerns through the contact address below.",
        },
        {
          title: "Your content and third-party material",
          text: "You retain ownership of your profile and uploaded material. Providing it allows Alignn to process it for the requested service. Third-party names and listing content belong to their respective owners; appearing in Alignn does not imply endorsement. Rights holders can contact us about corrections or removal.",
        },
        {
          title: "Availability and changes",
          text: "The product is under development and features may change. These draft terms do not promise uninterrupted availability or specific outcomes. Operator identity, age eligibility, account closure, liability terms and any applicable dispute arrangements require review before final publication.",
        },
      ]}
    />
  );
}
