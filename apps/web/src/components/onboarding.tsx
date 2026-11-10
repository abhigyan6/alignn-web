"use client";
import { useEffect, useRef, useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import type { components } from "../../../../packages/api-client/src/schema";
type Profile = components["schemas"]["ProfileOut"];
type Skill = { key: string; name: string };
type FileEntry = {
  id: string;
  filename: string;
  purpose: string;
  scan_status: string;
};
export default function Page() {
  return (
    <Suspense
      fallback={
        <main id="main" className="auth">
          <p role="status">Loading your profile…</p>
        </main>
      }
    >
      <Onboarding />
    </Suspense>
  );
}
function Onboarding() {
  const router = useRouter(),
    search = useSearchParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]),
    [selected, setSelected] = useState<string[]>([]);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [step, setStep] = useState(1);
  const [status, setStatus] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (step > 1) heading.current?.focus();
  }, [step]);
  useEffect(() => {
    Promise.all([
      api<Profile>("/me/profile"),
      api<Skill[]>("/skills"),
      api<{ skill_id: string }[]>("/me/skills"),
      api<{ items: FileEntry[] }>("/me/files"),
    ])
      .then(([p, catalog, chosen, uploads]) => {
        if (p.degree_id && p.graduation_year && search.get("edit") !== "1") {
          router.replace("/workspace");
          return;
        }
        setProfile(p);
        setSkills(catalog);
        setSelected(chosen.map((s) => s.skill_id));
        setFiles(uploads.items);
      })
      .catch((e) => setError(e.message));
  }, [router, search]);
  async function academics(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const p = await api<Profile>("/me/profile", {
        method: "PUT",
        body: JSON.stringify({
          college: data.get("college"),
          degree_id: data.get("degree"),
          branch_id: data.get("branch"),
          graduation_year: Number(data.get("graduation")),
          location: data.get("location"),
        }),
      });
      setProfile(p);
      setStep(2);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function preferences(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      await api("/me/skills", {
        method: "PUT",
        body: JSON.stringify({
          skills: selected.map((skill_id) => ({ skill_id, level: "beginner" })),
        }),
      });
      const updated = await api<Profile>("/me/profile", {
        method: "PUT",
        body: JSON.stringify({
          career_interests: String(data.get("interests"))
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          preferred_work_mode: data.get("mode"),
        }),
      });
      setProfile(updated);
      setStep(3);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(file: File) {
    if (file.size > 10 * 1024 * 1024 || !/\.(pdf|docx)$/i.test(file.name)) {
      setError("Choose a PDF or DOCX resume up to 10 MB.");
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
        "Resume uploaded and queued for a security scan. Resume parsing is not connected yet; your confirmed profile and skills drive matching.",
      );
    } catch (e) {
      setError((e as Error).message);
      setStatus("");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="onboarding">
      <aside className="onboarding-guide" aria-label="Setup progress">
        <h1>Make Alignn yours.</h1>
        <p>A little about you. A clearer path to your next opportunity.</p>
        <ol className="onboarding-steps" aria-label="Profile setup">
          {["Education", "Skills & interests", "Resume"].map((name, i) => (
            <li
              key={name}
              aria-current={step === i + 1 ? "step" : undefined}
              data-complete={step > i + 1}
            >
              <span className="step-number" aria-hidden="true">
                {i + 1}
              </span>
              <span>
                {name}
                <small>
                  {
                    [
                      "Your academic background",
                      "What you enjoy working on",
                      "Optional · add it anytime",
                    ][i]
                  }
                </small>
              </span>
            </li>
          ))}
        </ol>
        <p className="onboarding-guide-note">
          Your profile can evolve with you. You can edit these details later.
        </p>
        <Link href="/explore" className="onboarding-explore">
          Explore opportunities first
        </Link>
      </aside>
      <section className="onboarding-content" aria-labelledby="setup-heading">
        <div className="setup-progress" aria-label={`Step ${step} of 3`}>
          <span>Profile setup</span>
          <span>Step {step} of 3</span>
        </div>
        <div className="setup-heading">
          <h2 id="setup-heading" tabIndex={-1} ref={heading}>
            {
              [
                "Start with your education",
                "What are you interested in?",
                "Add your resume, if you like",
              ][step - 1]
            }
          </h2>
          <p>
            {
              [
                "Help us understand your background and the opportunities you may be eligible for.",
                "Choose your skills and interests to give your profile more direction.",
                "Keep your resume alongside your profile. You can also add it later.",
              ][step - 1]
            }
          </p>
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {!profile ? (
          <p role="status">
            {error
              ? "Refresh this page to try again."
              : "Loading your profile…"}
          </p>
        ) : step === 1 ? (
          <form onSubmit={academics}>
            <p className="form-note">
              All fields are required unless marked optional.
            </p>
            <div className="education-fields">
              <label className="field-wide">
                College
                <input
                  name="college"
                  defaultValue={profile.college ?? ""}
                  required
                  maxLength={180}
                  placeholder="Your college or university"
                  autoComplete="organization"
                />
              </label>
              <label>
                Degree
                <select
                  name="degree"
                  defaultValue={profile.degree_id ?? ""}
                  required
                >
                  <option value="" disabled>
                    Select your degree
                  </option>
                  {[
                    "btech",
                    "mtech",
                    "bca",
                    "mca",
                    "bsc",
                    "msc",
                    "bba",
                    "mba",
                    "bcom",
                    "ba",
                    "other",
                  ].map((d) => (
                    <option key={d} value={d}>
                      {d.toUpperCase()}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Field of study
                <select
                  name="branch"
                  defaultValue={profile.branch_id ?? ""}
                  required
                >
                  <option value="" disabled>
                    Select your field
                  </option>
                  {[
                    "cse",
                    "it",
                    "ece",
                    "eee",
                    "mechanical",
                    "civil",
                    "design",
                    "business",
                    "science",
                    "other",
                  ].map((d) => (
                    <option key={d} value={d}>
                      {d.toUpperCase()}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Graduation year
                <input
                  name="graduation"
                  type="number"
                  min={2000}
                  max={2100}
                  defaultValue={profile.graduation_year ?? ""}
                  required
                  placeholder="e.g. 2027"
                />
              </label>
              <label>
                <span>
                  Location <small>(optional)</small>
                </span>
                <input
                  name="location"
                  defaultValue={profile.location ?? ""}
                  maxLength={160}
                  placeholder="City, state"
                  autoComplete="address-level2"
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="button" disabled={busy}>
                {busy ? "Saving…" : "Continue to skills"}
              </button>
            </div>
          </form>
        ) : step === 2 ? (
          <form onSubmit={preferences}>
            <fieldset>
              <legend>Your skills</legend>
              <p>
                Choose the skills you’re starting with. You can update them
                later.
              </p>
              <div className="skill-options">
                {skills.map((s) => (
                  <label key={s.key}>
                    <input
                      type="checkbox"
                      checked={selected.includes(s.key)}
                      onChange={(e) =>
                        setSelected(
                          e.target.checked
                            ? [...selected, s.key]
                            : selected.filter((k) => k !== s.key),
                        )
                      }
                    />
                    {s.name}
                  </label>
                ))}
              </div>
              <small>{selected.length} selected</small>
            </fieldset>
            <label>
              Career interests
              <input
                name="interests"
                defaultValue={profile.career_interests?.join(", ") ?? ""}
                placeholder="Web development, design, data science"
              />
              <small>Separate interests with commas; up to 12.</small>
            </label>
            <label>
              Preferred work mode
              <select
                name="mode"
                defaultValue={profile.preferred_work_mode ?? "ANY"}
              >
                {["ANY", "REMOTE", "HYBRID", "ONSITE"].map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-actions">
              <button type="button" onClick={() => setStep(1)} disabled={busy}>
                Back
              </button>
              <button className="button" disabled={busy}>
                {busy ? "Saving…" : "Continue to resume"}
              </button>
            </div>
          </form>
        ) : (
          <div>
            <p>
              Your resume stays private. Upload a PDF or DOCX up to 10 MB, or
              add it later.
            </p>
            <label className="resume-input">
              <strong>Choose your resume</strong>
              <span>PDF or DOCX · up to 10 MB</span>
              <input
                type="file"
                accept=".pdf,.docx"
                disabled={busy}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void upload(f);
                  e.target.value = "";
                }}
              />
            </label>
            <p className="form-note">
              Resume text extraction is not available yet. Add your skills and
              interests above to complete your profile.
            </p>
            {status && <p role="status">{status}</p>}
            {files
              .filter((f) => f.purpose === "resume")
              .map((f) => (
                <p key={f.id}>
                  {f.filename} · {f.scan_status.toLowerCase()}
                </p>
              ))}
            <div className="form-actions">
              <button disabled={busy} onClick={() => setStep(2)}>
                Back
              </button>
              <button
                className="button"
                disabled={busy}
                onClick={() => router.replace("/workspace")}
              >
                Go to my workspace
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
