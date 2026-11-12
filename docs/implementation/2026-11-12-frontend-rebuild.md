# Frontend rebuild checkpoint — 12 November 2026

Rebuilt home, discovery, opportunity cards/details, navigation, sign-in/sign-up shells, onboarding, Saved and Applications around the user-confirmed India-first external opportunity journey. Product truth is in `apps/web/PRODUCT.md`; shared design rules are in `.interface-design/system.md` and `apps/web/DESIGN.md`. Existing session guards and backend contracts remain; completed profiles enter Discover.

Removed the artificial splash, retained useful cards during ranking refresh, added complete skeleton states, qualified unknown organizer attribution, and fixed stale pagination and nearby mobile fit-error recovery. Closed records preserve history without active Apply/Track actions. Optional resume copy distinguishes upload/scanning from unfinished extraction.

Verification: optimized production build, TypeScript and Prettier checks passed. Full desktop/mobile Playwright suite passed 50 tests. After the user requested a browser change, 10 focused auth/layout/product-flow tests passed in Brave. Local test configuration now selects installed Brave on macOS, supports `PLAYWRIGHT_EXECUTABLE_PATH`, and otherwise uses Playwright's installed Chromium. No browser was installed. The in-app browser also verified real discovery, internship filtering and source details.

A deliberately inverted closed-detail condition made its regression test fail as expected; source bytes were restored immediately in `finally`. Temporary synthetic account scenarios passed at 390px and 1440px, intercepting every application API call with no real writes. The review route was deleted. Detailed evidence and limits are in the accompanying motion/loading audit.

These checks do not establish a real signed-in Clerk journey, production deployment, performance targets or accessibility/legal compliance. Resume extraction and confirmed skill suggestions remain unfinished; matching currently uses confirmed profile data. No backend/scraper or infrastructure changes were made in this rebuild.

Three scoped agents contributed research/workspace, auth/onboarding, and loading/motion plus account-component verification. Selected starred skill instructions informed the work; no proprietary assets, candidate hooks or new app dependencies were added. No competitor animation was measured or transplanted. `docs/tech-stack.md` explains the current stack and cites competitor disclosures with their historical limits.
