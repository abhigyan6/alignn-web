"use client";
import Link from "next/link";
import { useState, FormEvent } from "react";
import { api } from "@/lib/api";
export default function TokenForm({
  purpose,
}: {
  purpose: "verify-email" | "reset-password";
}) {
  const [message, setMessage] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [done, setDone] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const data = new FormData(e.currentTarget);
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      setError(
        "This link is missing its token. Open the complete link from your email.",
      );
      setBusy(false);
      return;
    }
    try {
      await api("/auth/" + purpose, {
        method: "POST",
        body: JSON.stringify({
          token,
          ...(purpose === "reset-password"
            ? { password: data.get("password") }
            : {}),
        }),
      });
      setMessage(
        purpose === "verify-email"
          ? "Email verified. Sign in to continue."
          : "Password reset. Sign in with your new password.",
      );
      setDone(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="auth">
      <h1>
        {purpose === "verify-email"
          ? "Verify your email."
          : "Choose a new password."}
      </h1>
      {done ? (
        <>
          <p role="status">{message}</p>
          <Link className="button" href="/login">
            Sign in
          </Link>
        </>
      ) : (
        <form onSubmit={submit}>
          {purpose === "reset-password" && (
            <label>
              New password
              <input
                name="password"
                type="password"
                autoComplete="new-password"
                minLength={12}
                required
                aria-describedby="password-rule"
              />
              <span id="password-rule">Use at least 12 characters.</span>
            </label>
          )}
          {error && <p role="alert">{error}</p>}
          <button className="button" disabled={busy}>
            {busy
              ? "Please wait…"
              : purpose === "verify-email"
                ? "Verify email"
                : "Reset password"}
          </button>
        </form>
      )}
    </main>
  );
}
