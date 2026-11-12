import type { Metadata } from "next";
import LegalPage from "@/components/legal-page";
export const metadata: Metadata = { title: "Privacy policy \u00b7 Alignn" };
export default function Page() {
  return (
    <LegalPage
      title="Privacy policy"
      intro="How Alignn handles your account, profile and opportunity activity."
      sections={[
        {
          title: "Information you provide",
          text: "Alignn stores account identifiers, name and email received through Clerk, the education, skills, interests, preferences and projects you add, saved opportunities, and application stages and private notes. A resume is optional. Avoid including information you do not want processed.",
        },
        {
          title: "How we use information",
          text: "We use profile information to operate your account, rank opportunities and explain profile fit. Saved listings and application history help you keep track of your own activity. Current matching uses confirmed profile data; uploading a resume does not currently extract its text or automatically add skills.",
        },
        {
          title: "Resumes and files",
          text: "Uploaded resumes are processed through the private file-storage and scanning workflow. They are not a public profile attachment. Do not upload another person’s resume without permission. Production storage, scanning and access arrangements must be verified before launch.",
        },
        {
          title: "Service providers and external sites",
          text: "Clerk handles authentication. Hosting, database, file-storage and email providers process information needed to operate their services; the final production provider and location list is pending. Applying opens the original opportunity platform, whose privacy practices apply there. Saving or tracking a listing does not send an application or your resume to that platform.",
        },
        {
          title: "Technical information",
          text: "Requests can generate operational and security records such as timestamps, request details and network information. Authentication uses necessary cookies. This app does not currently integrate optional advertising pixels or analytics scripts. See Cookie information for the current scope and browser controls.",
        },
        {
          title: "Your choices and requests",
          text: "You can edit your profile, remove saved listings and manage application records using the available controls. Email us to request access, correction or deletion of account-related data. Removing an authentication account alone must not be assumed to erase every Alignn record or backup. A complete self-service account-erasure workflow is not yet available.",
        },
        {
          title: "Retention and deletion",
          text: "There is no finalized published retention schedule yet for all profile, resume, application, security and backup records. Requests need review across the application and its providers; we do not promise immediate or automatic deletion. Exact retention periods and any justified exceptions must be established before public launch.",
        },
        {
          title: "Younger users",
          text: "The account flow does not currently implement verified parental consent. Before opening account registration to minors, Alignn must review applicable requirements under India’s DPDP Act and Rules and implement the necessary safeguards. This draft does not claim legal compliance.",
        },
        {
          title: "Changes to this policy",
          text: "We will update this page when the product or data practices change. The revision date identifies the current draft; material new uses of personal information require an appropriate notice and review before activation.",
        },
      ]}
    />
  );
}
