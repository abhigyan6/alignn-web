# Alignn product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Students in India finding internships, hackathons and career/technical events that relate to their education, skills and interests. Initial context includes Bhopal/LNCT; the product is India-first.

## Product Purpose

Help students find relevant external opportunities, understand the information available, save a shortlist and keep track of applications. Confirmed directly by the user on 11 November 2026 after they rejected a frontend that obscured this purpose.

## Operating Context

Browse opportunities before signing in. Sign up/sign in through Clerk; a new/incomplete profile enters short profile setup with education, interests, skills and an optional private resume upload. Completed profiles enter Discover. Students can view opportunity details, inspect profile-fit evidence, save listings, apply on the original platform and manually track application progress. A save or an external click never means an application was submitted.

## Capabilities and Constraints

The API remains authoritative for profile data, saves, matching and application history. Existing architecture is Next.js/React/TypeScript, custom CSS, FastAPI, PostgreSQL and separate Python workers. Public external opportunity data is collected from verified sources; missing metadata stays unknown. Current nonempty sources include Devfolio, HackIndia, Luma and one curated employer careers board. No invented stipends, deadlines, eligibility checks or match percentages.

Resume upload/private scanning exists. Resume text extraction and user-confirmed skill suggestions are not implemented; the interface must not claim the uploaded file already generated recommendations. Current matching uses confirmed profile/skills/projects. No event hosting, teams, registrations, judging or auto-applications.

## Brand Commitments

Name: Alignn, wordmark alignn. Preserve the original connecting-loop symbol and readable Manrope family. Colors and page composition may change: user explicitly requested a fresh consistent design inspired by comparable platforms. Product actions use a clear, warm student-facing voice with concrete labels.

## Evidence on Hand

Existing local API and database; actual opportunities available in development. The user supplied an original project archive, proposal and brand kit. The scraper checkpoint documents dated source counts and verification. No customer/placement/selection metrics, company endorsements, user testimonials or production availability proof should be fabricated.

## Product Principles

- Put real opportunities and useful facts ahead of motivational copy.
- Explain what a profile changes and distinguish unknown eligibility from fit.
- Keep saved opportunities and application progress distinct and easy to reach.
- Preserve authentication/session behavior while replacing the interface.
- Work on small mobile screens, keyboard navigation and reduced motion.
