"use client";
import { useState, FormEvent } from "react";
import { api } from "@/lib/api";
export default function Forgot() {
  const [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await api("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: data.get("email") }),
      });
      setMessage("If that account exists, a reset link will be sent.");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="auth">
      <h1>Let’s get you back in.</h1>
      <form onSubmit={submit}>
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <button className="button" disabled={busy}>
          {busy ? "Please wait…" : "Request reset link"}
        </button>
        <p role="status">{message}</p>
      </form>
    </main>
  );
}
