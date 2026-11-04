"use client";
import Link from "next/link";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
export default function Login() {
  const router = useRouter();
  const [signup, setSignup] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSuccess("");
    const data = new FormData(e.currentTarget);
    try {
      await api(signup ? "/auth/signup" : "/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: data.get("email"),
          password: data.get("password"),
          ...(signup ? { full_name: data.get("name") } : {}),
        }),
      });
      if (signup) {
        setSuccess(
          "Account created. Check your email for a verification link, then sign in.",
        );
      } else router.push("/workspace");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="auth">
      <section>
        <LinkMark />
        <h1>
          {signup
            ? "Make room for your next chapter."
            : "Your next step starts here."}
        </h1>
        <p>
          {signup
            ? "Create your Alignn participant account."
            : "Sign in to your Alignn workspace."}
        </p>
        <form onSubmit={submit}>
          {signup && (
            <label>
              Full name
              <input name="name" autoComplete="name" required minLength={2} />
            </label>
          )}
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete={signup ? "new-password" : "current-password"}
              minLength={signup ? 12 : 1}
              required
              aria-describedby="password-help"
            />
          </label>
          <p id="password-help">
            {signup
              ? "Use at least 12 characters."
              : "Use the password for your Alignn account."}
          </p>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          {success && <p role="status">{success}</p>}
          <button className="button" disabled={busy}>
            {busy ? "Please wait…" : signup ? "Create account" : "Sign in"}
          </button>
        </form>
        {!signup && (
          <p>
            <Link href="/forgot-password">Forgot your password?</Link>
          </p>
        )}
        <button
          className="text-button"
          onClick={() => {
            setSignup(!signup);
            setError("");
            setSuccess("");
          }}
        >
          {signup
            ? "Already have an account? Sign in"
            : "New here? Create an account"}
        </button>
      </section>
    </main>
  );
}
function LinkMark() {
  return <p className="brand-note">Find your people. Find your next step.</p>;
}
