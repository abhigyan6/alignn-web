"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AccountLoading from "@/components/account-loading";
import type { AccountProfile } from "@/lib/account-profile";
import { api } from "@/lib/api";
import styles from "./onboarding.module.css";

type Skill = { key: string; name: string };
type FileEntry = {
  id: string;
  filename: string;
  purpose: string;
  scan_status: string;
};
type FieldErrors = Record<string, string>;
const steps = ["Education", "Skills & interests", "Resume"];
const degrees = [
  ["btech", "B.Tech"],
  ["mtech", "M.Tech"],
  ["bca", "BCA"],
  ["mca", "MCA"],
  ["bsc", "B.Sc"],
  ["msc", "M.Sc"],
  ["bba", "BBA"],
  ["mba", "MBA"],
  ["bcom", "B.Com"],
  ["ba", "BA"],
  ["other", "Other"],
];
const branches = [
  ["cse", "Computer science"],
  ["it", "Information technology"],
  ["ece", "Electronics & communication"],
  ["eee", "Electrical & electronics"],
  ["mechanical", "Mechanical engineering"],
  ["civil", "Civil engineering"],
  ["design", "Design"],
  ["business", "Business"],
  ["science", "Science"],
  ["other", "Other"],
];
const workModes = [
  ["ANY", "Open to any format"],
  ["REMOTE", "Remote"],
  ["HYBRID", "Hybrid"],
  ["ONSITE", "In person"],
];
const interestSuggestions = [
  "Web development",
  "Design",
  "Data science",
  "AI & machine learning",
  "Product",
  "Cloud & DevOps",
];
const scanLabels: Record<string, string> = {
  PENDING: "Upload pending",
  UPLOADED: "Scan pending",
  CLEAN: "Scan complete",
  SCAN_ERROR: "Scan unavailable",
  REJECTED: "File not accepted",
};

function interestList(value: string) {
  return [
    ...new Set(
      value
        .split(",")
        .map((item) => item.trim().toLowerCase())
        .filter(Boolean),
    ),
  ];
}

function Field({
  id,
  label,
  help,
  error,
  children,
  wide = false,
}: {
  id: string;
  label: ReactNode;
  help?: string;
  error?: string;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className={`${styles.field} ${wide ? styles.wide : ""}`}>
      <label htmlFor={id}>{label}</label>
      {children}
      {(help || error) && (
        <p
          id={`${id}-hint`}
          className={error ? styles.fieldError : styles.help}
        >
          {error || help}
        </p>
      )}
    </div>
  );
}

export default function Onboarding({
  initialProfile,
  editing,
}: {
  initialProfile: AccountProfile;
  editing: boolean;
}) {
  const router = useRouter();
  const [loaded, setLoaded] = useState(false);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [skillQuery, setSkillQuery] = useState("");
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(
    !editing && initialProfile.degree_id && initialProfile.graduation_year
      ? 2
      : 1,
  );
  const [status, setStatus] = useState("");
  const [draft, setDraft] = useState({
    college: initialProfile.college ?? "",
    degree: initialProfile.degree_id ?? "",
    branch: initialProfile.branch_id ?? "",
    graduation: initialProfile.graduation_year?.toString() ?? "",
    location: initialProfile.location ?? "",
    interests: initialProfile.career_interests?.join(", ") ?? "",
    mode: initialProfile.preferred_work_mode ?? "ANY",
  });
  const heading = useRef<HTMLHeadingElement>(null);
  const errorSummary = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (loaded) heading.current?.focus({ preventScroll: true });
  }, [loaded, step]);
  useEffect(() => {
    if (loaded && error) errorSummary.current?.focus();
  }, [error, loaded]);
  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    setError("");
    Promise.all([
      api<Skill[]>("/skills", options),
      api<{ skill_id: string }[]>("/me/skills", options),
      api<{ items: FileEntry[] }>("/me/files", options),
    ])
      .then(([catalog, chosen, uploads]) => {
        if (controller.signal.aborted) return;
        setSkills(catalog);
        setSelected(chosen.map((skill) => skill.skill_id));
        setFiles(uploads.items);
        setLoaded(true);
      })
      .catch((failure: Error) => {
        if (!controller.signal.aborted) setError(failure.message);
      });
    return () => controller.abort();
  }, [loadAttempt]);

  function updateDraft(name: keyof typeof draft, value: string) {
    setDraft((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: "" }));
  }
  function goToStep(next: number) {
    setError("");
    setFieldErrors({});
    setStep(next);
  }
  function invalidFields(errors: FieldErrors) {
    setFieldErrors(errors);
    const first = Object.keys(errors)[0];
    if (!first) return false;
    requestAnimationFrame(() =>
      document.getElementById(`profile-${first}`)?.focus(),
    );
    return true;
  }
  async function academics(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const errors: FieldErrors = {};
    if (!draft.college.trim())
      errors.college = "Enter your college or university.";
    if (!draft.degree) errors.degree = "Select your degree.";
    if (!draft.branch) errors.branch = "Select your field of study.";
    if (
      !/^\d{4}$/.test(draft.graduation) ||
      +draft.graduation < 2000 ||
      +draft.graduation > 2100
    )
      errors.graduation = "Enter a graduation year between 2000 and 2100.";
    if (invalidFields(errors)) return;
    setBusy(true);
    try {
      await api<AccountProfile>("/me/profile", {
        method: "PUT",
        body: JSON.stringify({
          college: draft.college.trim(),
          degree_id: draft.degree,
          branch_id: draft.branch,
          graduation_year: Number(draft.graduation),
          location: draft.location.trim(),
        }),
      });
      goToStep(2);
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function preferences(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const interests = interestList(draft.interests);
    if (
      invalidFields(
        interests.length > 12
          ? { interests: "Choose up to 12 interests." }
          : interests.some((item) => item.length > 80)
            ? { interests: "Keep each interest to 80 characters or fewer." }
            : {},
      )
    )
      return;
    setBusy(true);
    try {
      await api("/me/skills", {
        method: "PUT",
        body: JSON.stringify({
          skills: selected.map((skill_id) => ({ skill_id, level: "beginner" })),
        }),
      });
      await api<AccountProfile>("/me/profile", {
        method: "PUT",
        body: JSON.stringify({
          career_interests: interests,
          preferred_work_mode: draft.mode,
        }),
      });
      goToStep(3);
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function finish() {
    setBusy(true);
    setError("");
    try {
      await api("/me/onboarding/complete", { method: "POST" });
      router.replace("/explore");
    } catch (failure) {
      setError((failure as Error).message);
      setBusy(false);
    }
  }
  async function upload(file: File) {
    if (
      !file.size ||
      file.size > 10 * 1024 * 1024 ||
      !/\.(pdf|docx)$/i.test(file.name)
    ) {
      setError(
        "Choose a PDF or DOCX resume up to 10 MB. The file cannot be empty.",
      );
      return;
    }
    setBusy(true);
    setError("");
    setStatus("Uploading your resume…");
    try {
      const ticket = await api<{
        id: string;
        upload_url: string;
        complete_required: boolean;
      }>("/me/files", {
        method: "POST",
        body: JSON.stringify({
          filename: file.name,
          size: file.size,
          purpose: "resume",
        }),
      });
      if (ticket.upload_url.startsWith("/api/v1/")) {
        await api(ticket.upload_url.slice("/api/v1".length), {
          method: "PUT",
          body: file,
          headers: { "Content-Type": "application/octet-stream" },
        });
      } else {
        const result = await fetch(ticket.upload_url, {
          method: "PUT",
          body: file,
          credentials: "omit",
        });
        if (!result.ok)
          throw new Error("Resume upload failed. Please try again.");
      }
      if (ticket.complete_required)
        await api(`/me/files/${ticket.id}/complete`, { method: "POST" });
      setFiles((await api<{ items: FileEntry[] }>("/me/files")).items);
      setStatus(
        "Resume uploaded and queued for a security scan. You can continue to your opportunities.",
      );
    } catch (failure) {
      setError((failure as Error).message);
      setStatus("");
    } finally {
      setBusy(false);
    }
  }
  function toggleInterest(value: string) {
    const current = interestList(draft.interests);
    const key = value.toLowerCase();
    updateDraft(
      "interests",
      (current.includes(key)
        ? current.filter((item) => item !== key)
        : [...current, value]
      ).join(", "),
    );
  }
  function fieldState(name: string) {
    return {
      "aria-invalid": Boolean(fieldErrors[name]) || undefined,
      "aria-describedby": fieldErrors[name]
        ? `profile-${name}-hint`
        : undefined,
    };
  }

  if (!loaded)
    return error ? (
      <main id="main" className={styles.loadError}>
        <h1>We couldn’t load your profile details.</h1>
        <p role="alert">{error}</p>
        <div className={styles.actions}>
          <button
            className="button"
            onClick={() => setLoadAttempt((value) => value + 1)}
          >
            Try again
          </button>
          <Link href="/explore">Browse opportunities</Link>
        </div>
      </main>
    ) : (
      <AccountLoading onboarding />
    );

  const resumeFiles = files.filter((file) => file.purpose === "resume");
  const matchingSkills = skills.filter((skill) =>
    skill.name.toLowerCase().includes(skillQuery.trim().toLowerCase()),
  );
  const interests = interestList(draft.interests);
  return (
    <main id="main" className={styles.page}>
      <aside className={styles.guide} aria-label="Profile setup">
        <h2>
          A few details.
          <br />A more relevant next step.
        </h2>
        <p>
          Your skills and interests help shape the opportunities you discover.
        </p>
        <ol className={styles.steps}>
          {steps.map((name, index) => (
            <li
              key={name}
              aria-current={step === index + 1 ? "step" : undefined}
              data-complete={step > index + 1}
            >
              <span className={styles.stepNumber} aria-hidden="true">
                {step > index + 1 ? (
                  <svg viewBox="0 0 20 20" fill="none">
                    <path d="m5 10 3.5 3.5L15 6.5" />
                  </svg>
                ) : (
                  index + 1
                )}
              </span>
              <span>
                <strong>{name}</strong>
                <small>
                  {
                    [
                      "Your academic background",
                      "What you want to work on",
                      "Optional, now or later",
                    ][index]
                  }
                </small>
              </span>
            </li>
          ))}
        </ol>
        <p className={styles.editNote}>You can update every detail later.</p>
        <Link className={styles.browseLink} href="/explore">
          Browse opportunities first
        </Link>
      </aside>
      <section className={styles.content} aria-labelledby="setup-heading">
        <div className={styles.progressRow}>
          <span>{editing ? "Edit your profile" : "Set up your profile"}</span>
          <span>Step {step} of 3</span>
        </div>
        <progress
          className={styles.progress}
          value={step}
          max={3}
          aria-label="Profile setup progress"
        />
        <div className={styles.heading}>
          <h1 id="setup-heading" tabIndex={-1} ref={heading}>
            {
              [
                "Start with your education",
                "What would you like to explore?",
                "Add a resume, if you like",
              ][step - 1]
            }
          </h1>
          <p>
            {
              [
                "Add the background you want to include in your profile.",
                "Choose the skills and interests that should shape your profile matches.",
                "Keep a private copy alongside your profile. This step is optional.",
              ][step - 1]
            }
          </p>
        </div>
        {error && (
          <div
            role="alert"
            ref={errorSummary}
            tabIndex={-1}
            className={styles.error}
          >
            {error}
          </div>
        )}
        {step === 1 ? (
          <form onSubmit={academics} noValidate className={styles.form}>
            <p className={styles.help}>
              Fields are required unless marked optional.
            </p>
            <fieldset disabled={busy} className={styles.educationFields}>
              <legend className="sr-only">Your education</legend>
              <Field
                id="profile-college"
                label="College or university"
                error={fieldErrors.college}
                wide
              >
                <input
                  id="profile-college"
                  name="college"
                  autoComplete="organization"
                  value={draft.college}
                  onChange={(e) => updateDraft("college", e.target.value)}
                  required
                  maxLength={180}
                  placeholder="Enter your college or university"
                  {...fieldState("college")}
                />
              </Field>
              <Field
                id="profile-degree"
                label="Degree"
                error={fieldErrors.degree}
              >
                <select
                  id="profile-degree"
                  name="degree"
                  value={draft.degree}
                  onChange={(e) => updateDraft("degree", e.target.value)}
                  required
                  {...fieldState("degree")}
                >
                  <option value="" disabled>
                    Select your degree
                  </option>
                  {degrees.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field
                id="profile-branch"
                label="Field of study"
                error={fieldErrors.branch}
              >
                <select
                  id="profile-branch"
                  name="branch"
                  value={draft.branch}
                  onChange={(e) => updateDraft("branch", e.target.value)}
                  required
                  {...fieldState("branch")}
                >
                  <option value="" disabled>
                    Select your field
                  </option>
                  {branches.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field
                id="profile-graduation"
                label="Graduation year"
                error={fieldErrors.graduation}
              >
                <input
                  id="profile-graduation"
                  name="graduation"
                  type="number"
                  inputMode="numeric"
                  min={2000}
                  max={2100}
                  value={draft.graduation}
                  onChange={(e) => updateDraft("graduation", e.target.value)}
                  required
                  placeholder="For example, 2027"
                  {...fieldState("graduation")}
                />
              </Field>
              <Field
                id="profile-location"
                label={
                  <>
                    Location <span className={styles.optional}>(optional)</span>
                  </>
                }
              >
                <input
                  id="profile-location"
                  name="location"
                  autoComplete="address-level2"
                  value={draft.location}
                  onChange={(e) => updateDraft("location", e.target.value)}
                  maxLength={160}
                  placeholder="City, state"
                />
              </Field>
            </fieldset>
            <div className={styles.actions}>
              <button className="button" disabled={busy}>
                {busy ? "Saving…" : "Continue to skills"}
              </button>
            </div>
          </form>
        ) : step === 2 ? (
          <form onSubmit={preferences} noValidate className={styles.form}>
            <fieldset className={styles.skillFieldset} disabled={busy}>
              <legend>
                Your skills <span className={styles.optional}>(optional)</span>
              </legend>
              <p className={styles.help}>
                Choose what you’re learning or already working with. Up to 40
                skills.
              </p>
              <label htmlFor="profile-skill-search" className="sr-only">
                Find a skill
              </label>
              <input
                id="profile-skill-search"
                type="search"
                placeholder="Find a skill, like Python or design"
                value={skillQuery}
                onChange={(e) => setSkillQuery(e.target.value)}
                className={styles.skillSearch}
              />
              <div className={styles.skillOptions}>
                {matchingSkills.map((skill) => (
                  <label
                    key={skill.key}
                    data-selected={selected.includes(skill.key)}
                  >
                    <input
                      type="checkbox"
                      checked={selected.includes(skill.key)}
                      disabled={
                        !selected.includes(skill.key) && selected.length >= 40
                      }
                      onChange={(e) =>
                        setSelected(
                          e.target.checked
                            ? [...selected, skill.key]
                            : selected.filter((key) => key !== skill.key),
                        )
                      }
                    />
                    <span>{skill.name}</span>
                  </label>
                ))}
              </div>
              {!matchingSkills.length && (
                <p className={styles.help}>
                  {skills.length
                    ? "No skills match that search. Try a different term."
                    : "No skills are available right now. You can continue and add them later."}
                </p>
              )}
              <p className={styles.selectionCount}>
                {selected.length} selected
              </p>
            </fieldset>
            <Field
              id="profile-interests"
              label="Career interests"
              error={fieldErrors.interests}
              help="Choose a starting point below, or add your own separated by commas. Up to 12 interests."
            >
              <input
                id="profile-interests"
                name="interests"
                value={draft.interests}
                onChange={(e) => updateDraft("interests", e.target.value)}
                placeholder="For example, web development, design"
                disabled={busy}
                aria-describedby="profile-interests-hint"
                aria-invalid={Boolean(fieldErrors.interests) || undefined}
              />
            </Field>
            <div
              className={styles.interestOptions}
              aria-label="Interest suggestions"
            >
              {interestSuggestions.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  disabled={
                    busy ||
                    (!interests.includes(interest.toLowerCase()) &&
                      interests.length >= 12)
                  }
                  aria-pressed={interests.includes(interest.toLowerCase())}
                  onClick={() => toggleInterest(interest)}
                >
                  {interest}
                </button>
              ))}
            </div>
            <Field id="profile-mode" label="Preferred work format">
              <select
                id="profile-mode"
                name="mode"
                disabled={busy}
                value={draft.mode}
                onChange={(e) =>
                  updateDraft("mode", e.target.value as typeof draft.mode)
                }
              >
                {workModes.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <div className={styles.actions}>
              <button
                type="button"
                className="button secondary"
                disabled={busy}
                onClick={() => goToStep(1)}
              >
                Back
              </button>
              <button className="button" disabled={busy}>
                {busy ? "Saving…" : "Continue to resume"}
              </button>
            </div>
          </form>
        ) : (
          <div className={styles.resumeStep}>
            <label className={styles.resumeInput} htmlFor="profile-resume">
              <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
                <path d="M19 4H8a2 2 0 0 0-2 2v20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V11L19 4Z" />
                <path d="M19 4v7h7M11 17h10m-10 5h7" />
              </svg>
              <strong>Choose your resume</strong>
              <span>PDF or DOCX, up to 10 MB</span>
              <input
                id="profile-resume"
                type="file"
                accept=".pdf,.docx"
                disabled={busy}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void upload(file);
                  e.target.value = "";
                }}
              />
            </label>
            <p className={styles.help}>
              Your resume stays private and is checked before use. Resume text
              extraction is not available yet; matching uses the skills and
              interests you choose.
            </p>
            {status && (
              <p className={styles.uploadStatus} role="status">
                {status}
              </p>
            )}
            {!!resumeFiles.length && (
              <ul className={styles.fileList} aria-label="Your resumes">
                {resumeFiles.map((file) => (
                  <li key={file.id}>
                    <strong>{file.filename}</strong>
                    <span>
                      {scanLabels[file.scan_status] ?? "Status unavailable"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <div className={styles.actions}>
              <button
                type="button"
                className="button secondary"
                disabled={busy}
                onClick={() => goToStep(2)}
              >
                Back
              </button>
              <button
                type="button"
                className="button"
                disabled={busy}
                onClick={finish}
              >
                {busy ? "Getting your opportunities…" : "Find opportunities"}
              </button>
            </div>
            {!resumeFiles.length && (
              <p className={styles.continueNote}>
                You can continue without uploading a resume.
              </p>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
