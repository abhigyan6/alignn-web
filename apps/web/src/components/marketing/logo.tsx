export function LogoMark({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} viewBox="0 0 48 48">
      <path
        d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
        fill="none"
        stroke="currentColor"
        strokeWidth="5"
        strokeLinecap="round"
      />
    </svg>
  );
}
