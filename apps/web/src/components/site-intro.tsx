"use client";
import { useEffect } from "react";
import BrandLoader from "@/components/brand-loader";

// Runs before the page is painted, so repeat visits never flash the intro.
export const introScript = `try{if(!sessionStorage.getItem("alignn-intro-seen")){sessionStorage.setItem("alignn-intro-seen","1");document.documentElement.dataset.alignnIntro="true"}}catch{}`;

export default function SiteIntro() {
  useEffect(() => {
    const dismiss = () =>
      document.documentElement.removeAttribute("data-alignn-intro");
    const timer = window.setTimeout(dismiss, 1300);
    document.addEventListener("pointerdown", dismiss, { once: true });
    document.addEventListener("keydown", dismiss, { once: true });
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", dismiss);
      dismiss();
    };
  }, []);
  return (
    <div className="site-intro" aria-hidden="true">
      <div className="site-intro-lockup">
        <BrandLoader />
        <span className="site-intro-name">
          alignn<span className="intro-period">.</span>
        </span>
        <span className="site-intro-caption">
          A little direction. A world of possibility.
        </span>
      </div>
    </div>
  );
}
