"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Word-by-word reveal driven by scroll position. Server output contains every
 * word as plain text; words are dimmed by CSS and lit up as the paragraph
 * scrolls through the viewport. Reduced-motion users (and no-JS) see all words
 * at full contrast immediately.
 */
export function RevealText({ text }: { text: string }) {
  const words = text.split(" ");
  const ref = useRef<HTMLParagraphElement>(null);
  const [lit, setLit] = useState(0);
  const [instant, setInstant] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const el = ref.current;
    if (!el) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      if (query.matches) {
        setInstant(true);
        return;
      }
      setInstant(false);
      const rect = el.getBoundingClientRect();
      const vh = window.innerHeight;
      // 0 when the paragraph top reaches 85% of the viewport, 1 when its
      // bottom reaches 45%.
      const start = vh * 0.85;
      const end = vh * 0.45;
      const progress = (start - rect.top) / (start - end + rect.height);
      const clamped = Math.min(1, Math.max(0, progress));
      setLit(Math.round(clamped * words.length));
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    query.addEventListener("change", schedule);
    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      query.removeEventListener("change", schedule);
    };
  }, [words.length]);

  return (
    <p className="lp-manifesto" data-instant={instant || undefined} ref={ref}>
      {words.map((word, index) => (
        <span
          className="lp-word"
          data-lit={instant || index < lit ? "true" : undefined}
          key={`${word}-${index}`}
        >
          {word}{" "}
        </span>
      ))}
    </p>
  );
}
