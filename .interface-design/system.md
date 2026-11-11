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

## Loading and interaction rules

- The brand reveal is decorative, lasts about 1.2 seconds, and runs once per browser tab using sessionStorage. Input dismisses it. Reduced-motion users skip the reveal entirely. Storage failures leave content available.
- Use the shared BrandLoader symbol for account preparation. Match skeleton structures to discovery cards or the onboarding form rather than swapping entire layouts for a spinner.
- Skeleton shapes are hidden from assistive technology, with one status announcement and an aria-busy container. Remove them when data or an error arrives.
- Use shared 140ms interaction and 240ms surface-transition tokens. Hover effects apply only on devices that support hover. Reduced motion disables moving loader/shimmer effects and press/lift transforms.
- Application pages show Discover and My workspace links with active-page semantics. The public coming-soon homepage stays focused on its existing content.

Verified in the November 11 loading pass: production build and formatting, 22 desktop/mobile browser checks for loading, reduced motion, sign-in guards and title wrapping, and separate delayed-results screenshot checks. Native Edge inspection confirmed the application navigation. These checks do not establish full signed-in onboarding acceptance.

## Shared opportunity surfaces (11 November repair)

- One `OpportunityCard` is shared by discovery and saved opportunities: source category, organizer/employer, a single wrapping title, location/work mode, up to three explicitly labeled inferred/listed skills and source/deadline footer. No generated poster repeats the title.
- Panels/cards use 16px radii, 20px card insets and 16px grid gaps. Discovery category controls are 44px pill buttons with pressed semantics. Existing Manrope and semantic green tokens remain authoritative.
- Source dates use Asia/Kolkata with an explicit IST label. The detail action preserves the published time; unknown deadlines and work modes remain unknown.
- Desktop detail content and actions use two columns. On narrow screens actions precede long descriptions in both DOM and visual order. Source application remains an external link; saving/tracking remain separate actions.
- Workspace and discovery share cards. Details use the same bordered white surfaces. Loading cards follow the shorter card structure. Mobile discovery hides the optional guide and explanatory sidebar.
- The public homepage retains its coming-soon title. Application routes inherit the product title rather than advertising the whole application as coming soon.
