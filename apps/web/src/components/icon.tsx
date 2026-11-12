import type { CSSProperties } from "react";

const paths = {
  search: "m21 21-4.5-4.5M18 10.5a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z",
  bookmark: "M6 4h12v17l-6-4-6 4V4Z",
  briefcase: "M8 7V4h8v3M3 8h18v12H3V8Zm0 5c5 3 13 3 18 0M10 13h4",
  code: "m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18",
  calendar:
    "M5 5h14a2 2 0 0 1 2 2v13H3V7a2 2 0 0 1 2-2Zm2-3v6m10-6v6M3 10h18m-14 4h2m3 0h2m3 0h1m-11 3h2m3 0h2",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  external: "M14 3h7v7m0-7L10 14m0-10H4v16h16v-6",
  chevron: "m9 5 7 7-7 7",
  check: "m5 12 4 4L19 6",
  location:
    "M19 10c0 6-7 11-7 11S5 16 5 10a7 7 0 1 1 14 0Zm-4 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z",
  globe:
    "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM3 12h18M12 3c4 5 4 13 0 18-4-5-4-13 0-18Z",
  filter: "M4 6h16M7 12h10m-7 6h4M7 3v6m10 0v6m-5 0v6",
  grid: "M3 3h7v7H3V3Zm11 0h7v7h-7V3ZM3 14h7v7H3v-7Zm11 0h7v7h-7v-7Z",
  close: "m6 6 12 12M6 18 18 6",
  user: "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-2a8 8 0 0 1 16 0v2",
  list: "M9 5h12M9 12h12M9 19h12M3 5h1m-1 7h1m-1 7h1",
  file: "M14 2H5v20h14V7l-5-5Zm0 0v5h5M8 12h8m-8 4h6",
  clock: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM12 7v5l3 2",
  refresh: "M20 7A9 9 0 1 0 21 15M20 2v6h-6",
  spark: "m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4L12 3Z",
  cap: "m2 9 10-5 10 5-10 5L2 9Zm4 3v5c4 3 8 3 12 0v-5m4-3v8",
} satisfies Record<string, string>;
export type IconName = keyof typeof paths;
export default function Icon({
  name,
  size = 20,
  className = "",
  style,
}: {
  name: IconName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      <path d={paths[name]} />
    </svg>
  );
}
export function BrandMark({ className = "" }: { className?: string }) {
  return (
    <svg className={className} aria-hidden="true" viewBox="0 0 48 48">
      <path
        d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
        fill="none"
        stroke="currentColor"
        strokeWidth="4.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
