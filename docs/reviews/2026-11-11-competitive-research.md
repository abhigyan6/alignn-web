# Alignn: competitor research and Indian opportunity sources

Reviewed 11 November 2026. Scope: representative competitors and public source feasibility, not an exhaustive audit of every similar site. This is a product research checkpoint; proposed features below are not implemented or measured merely because they appear here.

## Proposal interpretation

Read all 11 rendered pages of the supplied `ALIGNN Proposal.pdf`. Its technology section was excluded from architectural decisions as requested. Team contact and enrollment information was excluded from research artifacts and CLI prompts.

The product is a student career opportunity intelligence platform: discover external opportunities, personalize against education/interests/confirmed resume skills, explain eligibility uncertainty, track deadlines, prepare and record application progress. Initial relevance is LNCT/Bhopal/MP, expanding across India. Proposal features include internships, jobs, hackathons, fellowships, scholarships, research/open-source programs, a career calendar, readiness guidance and institutional services. Outcomes and revenue forecasts in the proposal are aspirations, not evidence of current results.

**Scope conflict:** the proposal mentions hackathon services among possible revenue streams. Later user instructions explicitly removed event hosting, team formation, registration, submissions and judging. Those remain excluded. External hackathon discovery and links are retained. The older November 3 system specification also includes hosting; the later product-completion checklist supersedes that scope.

## Evidence levels and competitor matrix

Only Unstop and Devfolio received current desktop visual inspection in Edge in this pass. Other entries are bounded by official public pages/help documentation or indexed official snippets. Authenticated onboarding, mobile flows and paid features were not comprehensively exercised. Takeaways are design recommendations, not claims that a competitor uses the exact proposed Alignn component.

| Reference | Evidence inspected | Useful pattern for Alignn | Proposed adaptation / boundary |
| --- | --- | --- | --- |
| [Unstop](https://unstop.com/) | Live Edge desktop homepage; public competition/hiring pages | Persistent search, category navigation, save affordance, visible format and application status | Compact discovery navigation and consistent opportunity cards. Retain Alignn branding; do not import hosting or promotional carousel clutter. |
| [Devfolio](https://devfolio.co/hackathons) | Live Edge desktop catalog, structured public page metadata and an event detail | Open/upcoming/past grouping, themes, event dates, obvious application CTA, personal event shortcut | Distinguish registration deadline from event start/end. Link to source; do not collect builder profiles or copy branding. |
| [Internshala](https://internshala.com/internships/) | Indexed official result snippets; direct fetch blocked by robots in research tool | Role, city/WFH, stipend, duration and start-date filtering | Prioritize known stipend/duration when sourced; show unknown values explicitly. Full live interface review remains unverified. |
| [LinkedIn job alerts](https://www.linkedin.com/help/linkedin/answer/a511279/job-alerts-on-linkedin?lang=en) | Official help documentation | Saved searches with delivery preferences | A future alert should record the actual query and cadence. No automatic applications or copied LinkedIn content. |
| [LinkedIn saved jobs](https://www.linkedin.com/help/linkedin/answer/a513247/managing-jobs-you-saved-on-linkedin?lang=en) | Official help documentation | Separate discovery from later follow-up | Preserve source URL and manual student-reported application history. |
| [Naukri](https://www.naukri.com/faq/job-seeker) | Candidate benchmark; direct FAQ retrieval failed | Fresher/experience and academic criteria deserve review | Do not claim a completed UI audit or enable an undocumented/private scraper. |
| [HackerEarth](https://booking.hackerearth.com/hackcellence.html) | Official challenge detail, including stages and dates | Preparation and stage timeline | Present externally published stages when sourced; no internal judging or coding assessment engine. Example inspected was already closed, so not an import candidate. |
| [Hack2skill](https://hack2skill.com/event/startupbuildathon2026) | Official Indian program detail and [Build with Gemini](https://hack2skill.com/event/buildwithgemini/) | Clear audience, phases, FAQs and absolute deadlines | A program may be India-based yet professionals-only. Country is separate from student eligibility. |
| [MLH season schedule](https://www.mlh.com/seasons/2027/events) | Official public schedule and embedded event data | Region/date grouping and clear upcoming/past separation | APAC or online does not prove India eligibility. This fetch did not establish an Indian event in its initial results. |
| [Devpost](https://devpost.com/hackathons) | Public shell/navigation; limited listing access | Dedicated hackathon browsing and personal activity | Detailed current card behavior and ingestion contract remain unverified. |
| [Wellfound search](https://help.wellfound.com/article/777-setting-up-a-search) | Official search help | Compensation and employment preferences | Apply only to metadata supplied by the source; do not invent salary or company verification. |
| [Simplify](https://help.simplify.jobs/help/articles/2415391-use-copilot-to-autofill-applications) | Official help describing user-triggered autofill and tracking | Reduce repeated work and connect applying with follow-up | Keep applications external and tracking manual for now. Extension/autofill is a separate feature decision. |
| [Teal tracker](https://www.tealhq.com/tool/job-tracker) | Candidate benchmark; direct retrieval failed | Career CRM is relevant to the proposal | Kanban and saved listing snapshots are proposals requiring a later verified teardown, not confirmed findings from this pass. |

## Design decisions to implement after the checkpoint

1. **Discovery first:** land returning students in personalized discovery. Keep profile completion and optional resume suggestions accessible without an obstructive promotional dashboard. Preserve the repaired authentication/onboarding flow.
2. **One card contract:** title, organizer/employer, category, location, known work mode, registration deadline or “not published”, provenance, last successful source check, save and detail actions. On mobile use a single column and a filter sheet. Wrap long titles and maintain a stable skeleton footprint.
3. **Separate time meanings:** registration cutoff, event dates and internship duration are different fields. Relative urgency must derive from an absolute sourced timestamp and include a readable timezone. Never turn an event end date into an application deadline.
4. **Fit explanation:** distinguish confirmed matching skills, inferred preferred skills and missing/unknown eligibility. “India-based” does not mean all Indian students qualify. Keep a direct original requirements link. Resume extraction suggestions require student confirmation before changing their profile.
5. **Details with a clear next action:** concise overview, sourced requirements, known dates, fit explanation and a single external application CTA. Mobile CTA can stay reachable without covering content. A save is not an application or a registration.
6. **Workspace follow-up:** reuse the existing manual tracker and application history before adding Kanban. Future reminders should distinguish saved deadlines from student-entered next actions, with deduplication and notification preferences.
7. **Career Radar later:** official announced windows and historical estimates must have distinct labels and evidence. Do not fabricate a calendar of future corporate drives or infer exact deadlines from last year.
8. **Consistent components:** reuse the current shared auth shell, tokens, accessible controls, loading states and motion rules. Add category-specific metadata through one card/detail system, not independently styled pages.

Recommended order: data reliability and source visibility -> discovery/filter/card polish -> confirmable resume extraction and fit explanations -> deadline follow-up/tracking -> evidence-backed Radar -> institutional features. This prioritization is a recommendation, not a new scope approval or completed implementation.

## Proposal-to-product gaps

| Proposal capability | Current evidence / next step |
| --- | --- |
| External discovery and matching | Existing Remotive ingestion and deterministic matching; new Indian-source changes are a local working-tree checkpoint. |
| India hackathon coverage | Live Devfolio crawl returned 14 explicit India events with open registration timestamps at fetch time. Results change over time; not a coverage guarantee. |
| India internships | Three public employer boards checked; Stripe exposed a Bengaluru Software Engineer, Intern role, confirmed on its [official careers page](https://stripe.com/careers/listing/software-engineer-intern/8031833). No qualifying internship found in the Razorpay/Figma snapshots. |
| Resume intelligence | Optional private upload exists; extraction and user-confirmed skill suggestions remain unfinished. |
| Eligibility explanation | Structured eligibility cannot be assumed from unstructured third-party descriptions. Current external-listing eligibility endpoint directs users to the original source. |
| Deadlines and tracker | Manual external tracking exists; proposal-level full notification/readiness journey requires implementation and end-to-end verification. |
| Fellowships, scholarships, research/open source | Need separate verified sources and appropriate category contracts. Not covered by the new hackathon/internship adapters. |
| Future career calendar / assistant | Keep as later, evidence-backed work; no synthetic predictions presented as announcements. |
| Institutional/corporate services | Later scope; no college or company integration established by research. |

## Source and open-source decisions

**Selected engine:** [Scrapy](https://github.com/scrapy/scrapy), BSD-3-Clause ([license](https://github.com/scrapy/scrapy/blob/master/LICENSE)). Installed version resolved to 2.20.0. It provides explicit robots handling, bounded requests, delays and structured extraction; an autonomous LLM browser agent is unnecessary for routine ingestion. [Official settings](https://docs.scrapy.org/en/latest/topics/settings.html) and [script execution documentation](https://docs.scrapy.org/en/latest/topics/practices.html#run-scrapy-from-a-script) informed the implementation.

| Source | Verified access and decision | Important limit |
| --- | --- | --- |
| Devfolio | Public catalog and per-event structured page data fetched; robots fetched. Implemented draft adapter uses explicit detail country `India`, official registration date and canonical Devfolio apply URL. | Public accessibility/robots allowance is not a content licence or legal assurance. Recheck terms and redistribution expectations before public rollout. Index is curated, so missing events must not be closed by absence. |
| Greenhouse | [Documented public GET API](https://docs.greenhouse.io/job-board.html); actual `stripe`, `figma`, `razorpaysoftwareprivatelimited` boards returned HTTP 200. Draft adapter imports only internships with explicit Indian city/country location evidence. | Read-only GET access does not confer employer endorsement or comprehensive India coverage. No invented deadline, stipend, eligibility or remote status. |
| Remotive | Existing adapter and attribution contract remain in place; see [API repository](https://github.com/remotive-com/remote-jobs-api). | Global remote roles are not automatically India-accessible. Existing feed restrictions and attribution still apply. |
| Hack2skill | Official program pages provide useful India/audience evidence. | No adapter enabled in this checkpoint; verify robots, dates and stable structured fields per program before adding. |
| MLH | Season page embeds structured events. | No adapter enabled; APAC/global remote results require actual country/eligibility validation. |
| Unstop, Internshala, Naukri, LinkedIn | Product references only in this implementation. | No private APIs, account scraping, CAPTCHA bypass, stealth fingerprints or logged-in scraping enabled. |
| Scholarships / government / GSoC | Candidate official source families identified. | No current application-feed contract or completeness established. Blog announcements are not automatically application listings. |

Inspected [0xarchit/hackathon-api](https://github.com/0xarchit/hackathon-api), commit `44aa8ee24d6138994bf457a2890bb8189617e9f1`, MIT license. Its Devfolio/HackerEarth adapters hardcode India; rejected that normalization. No code from that repository was copied or executed. Crawlee and Scrapling were considered but not adopted. JobSpy was suggested by Antigravity; it was not installed or enabled. No proprietary competitor components, logos or participant photos were copied.

## Antigravity CLI assistance and review disposition

Ran authorized read-only research with `agy --mode plan --sandbox --dangerously-skip-permissions --print-timeout 0`. It completed and produced a research report in `/tmp/alignn-competitive-source-research.md`. Only a sanitized product brief was supplied; no credentials or proposal team contact details were requested. Raw CLI output is research input, not approved product truth.

Accepted: separate source adapters; prefer documented employer APIs; explicit provenance; distinguish career estimates from official dates; preserve external discovery scope.

Corrected/rejected:

- “100% compliant” and “tamper-proof” claims have no support and are omitted.
- `ends_at` cannot map to `registration_closes_at`.
- `APAC` or digital format cannot establish India accessibility.
- HTTP 200 or an open GitHub repository does not establish redistribution rights or source completeness.
- Claimed internship dataset volumes and Indian accessibility were not independently validated and are excluded.
- “No API exists” and scraping-prohibition claims require specific evidence; unavailable retrieval alone cannot prove them.
- Employer board tokens were checked directly rather than adopting its proposed 30-company registry as verified.

The additional read-only CLI review completed after the pause. Its findings were assessed and dispositions recorded in `docs/implementation/2026-11-11-indian-source-checkpoint.md`; recommendations were not accepted automatically.

## Checkpoint and remaining questions

The user requested pausing implementation until their limit resets in approximately 3 hours 30 minutes. No deployment, cloud provisioning, DNS change, paid service or competitor account access was performed for this research.

Assumptions: India-first means evidence-based location relevance, not a nationality/eligibility promise; local ingestion is separate from deployment; inferred skills are preferences, not mandatory admissions rules; optional resume processing remains private and confirmation-based.

Open decisions for later: which additional employer boards to curate; whether global India-accessible opportunities should be a separate filter; what approved sources cover non-hackathon workshops/scholarships/fellowships; whether to add verified compensation/duration fields; which notification channels to launch. None blocks preserving this research checkpoint.
