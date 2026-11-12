"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import styles from "./legal.module.css";
const key = "alignn-cookie-notice";
export default function CookieNotice() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    try {
      setVisible(localStorage.getItem(key) !== "v1");
    } catch {
      setVisible(true);
    }
  }, []);
  if (!visible) return null;
  return (
    <aside className={styles.cookieNotice} aria-label="Cookie information">
      <p>
        Alignn uses cookies for sign-in and security.{" "}
        <Link href="/cookies">Read about cookies and browser controls</Link>.
      </p>
      <button
        className="button secondary"
        onClick={() => {
          try {
            localStorage.setItem(key, "v1");
          } catch {
            /* The notice can still be dismissed for this visit. */
          }
          setVisible(false);
        }}
      >
        Dismiss notice
      </button>
    </aside>
  );
}
