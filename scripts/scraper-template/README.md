# Alignn India-first opportunity collector

Private standalone export from `abhigyan6/alignn-web`. `EXPORT.json` records the exact source commit; it must say `dirty: false` for a published release. Update from the canonical app using `python3 scripts/export-scraper.py --output /path/to/alignn-scraper`; do not hand-edit exported collectors.

Run **Actions → Scrape Indian opportunities → Run workflow → all** (or one source). Each source runs fixture tests and a bounded public crawl; the report job combines validated partitions into the private `alignn-opportunities-v1` artifact, retained seven days. Failed/partial source counts are explicit. Running refreshes are not cancelled; repeated pending refreshes may coalesce. No database, AWS, Clerk, user information or resume credentials belong here.

The configured Alignn backend automatically polls trusted completed default-branch runs and imports the artifact to PostgreSQL. Collection success alone does not confirm import. A developer can validate a downloaded `opportunities.zip` with the app's `python -m alignn.domains.opportunities.import_scraped --file ... --dry-run`; manual import is recovery only.

Cron is present but jobs are **disabled** unless the repository variable `SCRAPER_SCHEDULE_ENABLED` equals `true`. Enable only after production backend access, worker supervision, account Actions allowance and source budgets are checked. GitHub scheduling can be delayed. No paid runner or billing setting is configured by this repository.

## Sources and limits

Enabled public metadata: HackIndia public hackathon/detail pages; Luma public Bengaluru/New Delhi/Mumbai city pages plus two reviewed India hackathon seeds; Devfolio public hackathon/detail pages; curated Greenhouse employer boards Stripe, Figma and Razorpay (Indian internships only).

Unstop is blocked by the currently observed JavaScript/cookie catalog. Hack2skill and KonfHub need a verified public extraction contract. They are not runnable placeholders. Coverage is bounded, not every event or every platform. Only explicit India location/country/audience evidence is accepted; timezone, currency or online format are insufficient.

Public page/robots review: 11 November 2026. HackIndia public pages allow discovery while its `/api`, teams and profile paths are excluded. Luma has no general-agent disallow in the reviewed robots response; only public city/event pages are used. Greenhouse uses its documented public GET Job Board API. These observations are access evidence, not a redistribution license or legal-compliance claim. Source owners can change terms/robots; the transport rechecks robots each run and preserves last good backend data on failure. Review permission/attribution before public launch; link each listing to its canonical source and avoid republishing more description than necessary.

No login, cookies, CAPTCHA bypass, attendee/guest APIs, proxy rotation or auto-applications. Whitelisted metadata only; no raw HTML/pages, participant objects, personal profiles or contact fields in output. Descriptions are plain text with email/direct-chat contacts omitted. Unknown dates remain null. Public descriptions may still contain personal information in prose; review and minimize public display before launch.

Limits: 100 records/source, 100 detail pages, one request per domain at a time, ≥1 second spacing, 15 second request timeout, 180 seconds/source; two MiB HTML/page (20 MiB for complete documented ATS JSON), one retry. Artifact schema 1 uses ≤1 MiB chunks and a manifest; total ≤80 MiB uncompressed, ZIP ≤85 MiB, ≤128 members. Critical eligibility/deadline facts are never truncated to fit. No title-based cross-platform merge.

## Local development

Python 3.12+, `python -m pip install --require-hashes -r requirements.lock`, then `PYTHONPATH=src python -m pytest -q` and `PYTHONPATH=src python -m alignn_scraper --source hackindia --output output/opportunities.zip`.

Dependencies are pinned with hashes. Workflow actions are pinned to reviewed release commits. This collector never imports the Alignn app, settings, SQLAlchemy or a database driver.
