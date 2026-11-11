# Alignn interface system

Alignn helps students identify opportunities that fit their education, interests and confirmed skills. Discovery should make relevance and the next action clear. Profile setup should feel like a short, understandable sequence.

## Existing direction consolidated

- Use Manrope throughout the product. Body text starts at 16px with 1.55 line height. Keep input text at least 16px on mobile.
- Use the existing forest green accent (#123e2f), pale green canvas (#f5f6f0), white surfaces, deep green ink (#1d3027), muted text (#53685b) and quiet border (#d4ded5).
- Shared CSS tokens in globals.css own these values. Auth-provider appearance values must match the same accent. Avoid new per-page accent overrides.
- Reserve category colors for opportunity categories. Do not make category colors alternative primary actions.
- Retain the 4px spacing base. Existing shared controls use 10px/14px inset spacing, and primary actions have a 48px minimum height.
- Use subtle borders and white cards to group content. Maintain existing corner-radius choices while consolidating reusable components in the next pass.
- Long source titles and employer names must wrap. Card clipping must not hide their content.
- Discovery uses a two-column desktop card grid and one column on narrow phones. Scrollable category controls must stay within the viewport.
- Keep keyboard focus visible and expose loading, error, empty and retry states. Honor reduced motion.

## Verification status

Discovery was inspected at 360, 390, 768 and 1440px using explicit synthetic browser fixtures. Long-title clipping was reproduced and fixed. Shared palette consolidation has started. Full auth, onboarding, details, workspace and tracking visual acceptance remains pending.
