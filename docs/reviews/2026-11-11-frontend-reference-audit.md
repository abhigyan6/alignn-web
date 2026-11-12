# Alignn frontend reference audit

11 November 2026. Product/interface research for the authorized redesign, not an exhaustive competitor audit, usability study or visual-quality certification.

## Product the UI must explain

Alignn helps Indian students discover external internships, hackathons and technical/career events relevant to their education, interests and confirmed skills; understand the fit and missing information; save a shortlist; apply on the original platform; and record progress.

Account → short profile setup → optional private résumé → personalized discovery → details → original-source application → manual tracking. Returning students should reach discovery directly. Saving, opening an external link and submitting an application are different actions.

**Current truth:** profile/skill matching, discovery, saves, manual tracking and private upload exist. Résumé extraction and confirmation of extracted suggestions are unfinished. Upload must not be portrayed as working résumé intelligence. External eligibility is generally unstructured. Event hosting, registrations, teams, submissions and judging remain excluded.

## Evidence boundaries

I inspected the current frontend source and existing product/research documents. This pass retrieved official public rendered text and help documentation. It did not perform new visual screenshot inspection, competitor sign-in, authenticated onboarding, paid-feature or mobile competitor testing. The older research records its own limited dated Edge evidence.

The primary Unstop catalog returned a JavaScript shell to the text tool; indexed Unstop-owned public HTML supplied listing metadata. Internshala returned readable public structure, but the web index snapshot was seven months old: verify current visuals, do not reuse its listing counts. Teal's singular `/tool/job-tracker` failed; its current plural `/tools/job-tracker` and official help were available.

## Reference decisions

| Platform / primary evidence | Observed or documented pattern | Adopt in Alignn | Exclude |
|---|---|---|---|
| [Unstop catalog](https://unstop.com/hackathons/), [Unstop-owned listing HTML](https://api.unstop.com/hackathons/) | Categories and organizer/audience/deadline cues; participation metadata. Exact current card geometry unverified here. | Recognizable categories and compact decision facts; visible source. | Hosting, business tooling, unrelated assessments, promotional clutter, fabricated popularity. |
| [Internshala internships](https://internshala.com/internships/) | Role/profile, location/WFH, stipend and duration controls; fact-first employer listings. Snapshot-age caveat applies. | Persistent search/filter region, scannable metadata and editable preferences. | Unsupported pay/duration filters and sign-up countdown promotions. |
| [Devfolio catalog](https://devfolio.co/hackathons), [discovery guide](https://guide.devfolio.co/docs/guide/introduction) | Open/Upcoming/Past grouping, format/themes and distinct event start timing; mode/theme/location discovery. | Event-specific date hierarchy and a clear available next action. | Participant avatars, leaderboards, submissions/judging and organizer tooling. |
| [Wellfound search help](https://help.wellfound.com/article/777-setting-up-a-search) | Role/location/preferences plus keywords; compensation filtering explicitly handles missing salary data. | Explain personalized ordering versus manual browsing; preserve unknown facts. | Equity/funding/recruiter filters or invented compensation. |
| [Simplify dashboard](https://help.simplify.jobs/en/help/articles/6390631-navigate-your-dashboard), [tracker](https://help.simplify.jobs/help/articles/2140179-use-the-job-tracker) | Recommendations, search, preferences, tracker and profile are separate tasks. A saved/manual record does not submit an employer application. | Clear destinations and explicit post-apply tracking. | Autofill/autonomous applications, email access, streaks, paid AI widgets or recruiter-attention claims. |
| [Teal tracker help](https://help.tealhq.com/en/articles/14435727-how-to-track-your-job-applications), [product](https://www.tealhq.com/tools/job-tracker) | Compact records keep stage and notes together; bookmarked and applied are different; closed records leave active work. | Scannable Applications view, stage, expandable history/notes and retained closed records. | Contacts CRM, email templates, reminders, analytics and unimplemented statuses. |

These are interaction principles, not permission to copy proprietary code, text, logos, screenshots, icons or media. Use Alignn's mark and original components.

## Current source-level problems

1. `app/page.tsx` still says Coming Soon, without explaining or entering the usable local product.
2. `app/explore/page.tsx` pushes results below broad motivational content and repeats guidance in two sidebars. Profile-based relevance is not made concrete.
3. `components/app-navigation.tsx` offers Discover and My workspace. “Workspace” conceals two distinct jobs, Saved and Applications; profile editing is another buried link.
4. `components/onboarding.tsx` completes to `/workspace`, although the promised setup payoff is a relevant feed.
5. `components/opportunity-card.tsx` is an all-card link with no separate Save, event-date range or visible closed treatment. Inferred skills are not a personalized explanation.
6. Detail correctly separates source application, fit and eligibility, but raw numeric factors read like implementation output. External eligibility uncertainty must remain visible.
7. Workspace mixes greeting, verification, profile editing, saved cards, tracker and sign-out into one long page.
8. The tracker already supports real manual stages, notes and history. Improve those controls rather than substituting a decorative static Kanban board.

These are inspected-code findings, not measured user outcomes.

## Recommended information architecture

Use **Discover · Saved · Applications · Profile** as task vocabulary. Initially these can be workspace tabs/anchors backed by existing endpoints. Put account/sign-out in the account menu; opportunity categories belong inside Discover.

- **Public home:** explain finding relevant Indian opportunities in one concrete sentence; offer discovery and profile creation; show real available content/categories. Avoid invented user counts, partnerships, selection rates and AI claims.
- **Discover:** short title, query, categories, real “For you / Latest / Closing soon” sorts, active-filter state, results and one compact preferences entry. Returning students should see opportunities in the first viewport.
- **Saved:** shortlist with Open/Closed distinction; closed items remain readable, with remove/save state and a discovery route. Saved does not mean applied.
- **Applications:** compact stage-oriented records and inline update/history. Use only existing Saved, Applied, Interview, Offer, Rejected and Withdrawn statuses. Notes remain private.
- **Profile:** education, skills/interests/preferences and private documents in separate sections. Onboarding is their short first-use version, not the only editing route.

## Component and copy contracts

### Listings

Prioritize title → published organizer/employer → location/known work mode → category-specific dates → source and separate Save. Use a restrained category accent and original icon/initial, not an invented employer logo. Do not nest Save inside an all-card link.

A known cutoff can show an absolute IST date and derived urgency. Unknown cutoff gets “Check deadline at source.” Show event start/end separately. Closed saved cards need explicit historical status; a published collected row alone does not justify a source-verified “Open” claim.

**Data constraints:** the opportunity-list response has no per-card fit score. Do not invent “95% match” badges; use the actual ranking state and detail fit endpoint. Search currently exposes query, kind, sort, cursor and limit. Do not make new location/pay/duration controls appear functional without their backend contract. A category control must not promise data coverage merely because the enum exists.

### Detail

Order identity/source, important timing/location, fit/requirements summary, then description. Make the external application link primary and Save separate. “Track application” should explain that the student records an action completed elsewhere; opening a source link never means Applied. Translate real fit factors into understandable evidence, retaining the distinction between fit and eligibility. Source presence does not establish organizer verification.

A mobile action region must leave space for content, keyboard and browser controls. On desktop, keep the action panel adjacent to the description. Do not introduce sticky elements that cover the final paragraph or focused control.

### Onboarding/auth

Use Education → Skills and preferences → Optional résumé, explaining why each field helps. Preserve values, save deliberately and focus the next heading. Finish with “Show my opportunities” and the discovery destination.

Treat upload, scanning and extraction separately. Current success can report receipt/scan state; it cannot say “We found your skills” or show fake parsing progress. Provide a clear skip/continue. Preserve the repaired Clerk redirect/onboarding logic; visual redesign does not require recreating authentication.

### Feedback/motion

Keep results spatially stable during updates. Skeletons should resemble the final cards/rows with one accessible status; avoid full-app blanking while rankings refresh. Short save feedback can confirm a real result. Frequent filters, text input and navigation should stay fast; respect keyboard/reduced-motion use. A decorative welcome must not delay the task.

## Build order and acceptance

1. Clarify entry/home, navigation vocabulary and setup payoff.
2. Recompose discovery around search, categories, results and one compact preferences area; wire only real filters.
3. Share the card/detail decision hierarchy across discovery and saved records.
4. Separate Saved and Applications; polish the existing tracker/history.
5. Normalize auth/setup/profile controls, typography and loading states.
6. Verify rendered phone, tablet and desktop states: long titles, loading, empty results, errors/retry, signed-out Save, closed saved detail, repeated filters, keyboard and reduced motion.

This proposes frontend work only. It does not add sources, reminders, auto-application, AI extraction or backend features. Final appearance requires current rendered screenshots and the main agent's design work; research alone cannot certify visual quality.
