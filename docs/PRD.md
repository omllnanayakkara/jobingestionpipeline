# Product Requirements Document (PRD)
## AI-Powered Job Tracking & Matching Agent

**Version:** 1.0 (MVP Scope)
**Status:** Draft — Ready for Architecture Phase

---

## 1. Overview

An autonomous AI agent system that helps job seekers — primarily in Sri Lanka, with secondary support for remote/foreign roles — discover relevant job postings without manually searching multiple sites. Users upload a CV (optional) and/or define role preferences; the system continuously ingests job listings from external sources, matches them against the user's profile, filters by recency, and proactively alerts the user, cutting out the repetitive manual searching that existing tools still require.

## 2. Problem Statement

Existing tools (e.g., LoopCV, AIApply) are largely **pull-based** — users must return to the platform to see new results — and are optimized for US/EU markets. Sri Lankan job seekers currently rely on manually checking multiple local and international job boards, with no reliable way to filter noise, verify listing legitimacy, or see company reputation alongside a job ad.

## 3. Goals

- Automatically surface **fresh, relevant** job postings matched to a user's CV and stated preferences
- Prioritize **Sri Lanka-based jobs**, with **remote/foreign jobs** as a secondary layer
- Deliver listings via **push-based alerts** rather than requiring manual searching
- Filter out likely **scam/fake listings**
- Enrich listings with **company reputation data** where available
- Keep the MVP scope lean by using a **third-party scraping service (Apify)** rather than building custom scrapers for LinkedIn/Glassdoor at launch

## 4. Non-Goals (MVP)

- Auto-applying to jobs on the user's behalf
- Building custom LinkedIn/Glassdoor scrapers (deferred — only revisit if Apify proves insufficient on cost, coverage, or reliability)
- Full application-cycle tracking (interview scheduling, offer management, etc.)

---

## 5. Target Users

- Job seekers based in Sri Lanka looking for local roles
- Sri Lankan job seekers open to remote roles with foreign companies
- English-fluent professionals (language/locale filtering is handled implicitly through parsing, not as a standalone preference)

---

## 6. Core Features (MVP)

### 6.1 CV Upload & Parsing
- User uploads CV (PDF/DOCX) — **optional**
- System extracts: skills, work experience, education, seniority level
- Extracted profile is editable by the user before being used for matching

### 6.2 User-Defined Preferences
- Desired role(s)/title(s)
- Experience level
- Preferred skills/technologies
- Location scope: Sri Lanka only / Remote / Foreign / Any
- Recency window: user-configurable (e.g., last 7 days, last 30 days)

### 6.3 Recency-Based Filtering
- Only listings within the user's chosen time window are shown
- Rolling window approach — **no need to track/store previously-shown listings** to avoid duplicates (simplifies system, deferred to Phase 2 if needed)

### 6.4 Job Data Ingestion (via Apify)
- Scheduled background jobs (e.g., hourly/every few hours) call Apify actors for:
  - LinkedIn job listings
  - Glassdoor company review/rating data
- Results are written into the system's **own database** (cache layer)
  - Avoids repeated per-user API calls (cost control)
  - Enables fast querying and consistent recency filtering
  - Custom scrapers to be built in-house for local sources: **topjobs.lk**, **rooster.jobs**, **itpro.lk**, **xpress.jobs** (no viable third-party scrapers found for these; ToS to be reviewed before implementation)

### 6.5 Matching Engine
- Compares parsed CV + preferences against ingested job listings
- Returns ranked/filtered matches per user

### 6.6 Push-Based Alerts
- Users are notified proactively (email/push/in-app) when new matching jobs are found within their recency window — no need to manually check the app

### 6.7 Scam / Fake Listing Detection
- Heuristic and/or ML-based flagging of suspicious postings before they reach the user (e.g., missing company info, unrealistic pay, known scam patterns) — **can be built as a future increment**

### 6.8 Company Reputation Enrichment
- Where available (via Apify's Glassdoor data), show company ratings/reviews alongside each job listing for context — **can be built as a future increment**

---

## 7. Phase 2 Features (Post-MVP)

| Feature | Description |
|---|---|
| Application Tracking | User marks jobs as "already applied" to suppress duplicate listings (not auto-apply) |
| Match Scoring & Feedback | Show % match score with breakdown of strengths and skill gaps |
| Custom Scraper Migration | Build in-house LinkedIn/Glassdoor scrapers if Apify becomes a bottleneck (cost, coverage, or reliability) |
| Database Duplicate Prevention | Avoid saving the same job posted on different platforms using similarity checking |

---

## 8. Data Sourcing Strategy

| Source | Method (MVP) | Notes |
|---|---|---|
| LinkedIn | Apify actor | Public job listing pages only; no login/session-cookie scraping (account ban + liability risk) |
| Glassdoor | Apify actor | Company reviews/ratings enrichment |
| topjobs.lk | Custom in-house scraper | Review ToS before building |
| rooster.jobs | Custom in-house scraper | Review ToS before building |
| itpro.lk | Custom in-house scraper | Review ToS before building |
| xpress.jobs | Custom in-house scraper | Review ToS before building |

**Note on scale-up path:** Apify is the MVP validation layer — it proves out the matching/alerting pipeline without upfront scraper investment. If cost, coverage, or reliability becomes a limiting factor at scale, migrate to a custom scraper (e.g., Playwright + Camoufox + residential proxies), following the architecture patterns studied from open-source references (e.g., RomanBaz/apify-linkedin-scraper).

---

## 9. High-Level System Flow

1. User signs in/up to the platform
2. User may upload CV → parsed into structured profile
3. User sets preferences (role, location scope, recency window)
4. Scheduled job (hourly/every few hours) pulls fresh listings via Apify → stores in internal DB
5. Custom scrapers pull other listings from topjobs.lk, rooster.jobs, itpro.lk, xpress.jobs on the same schedule
6. Scam-detection filter runs on newly ingested listings
7. Matching engine scores listings against each user's profile
8. New qualifying matches (within recency window) trigger a push alert
9. User views listing + company reputation data in-app

---

## 10. Open Questions / Risks

- **Legal/ToS risk**: Confirm topjobs.lk, rooster.jobs, itpro.lk, and xpress.jobs terms of service permit scraping before building — TBD
- **Scam detection accuracy**: Needs a defined ruleset or model — TBD in design phase
- **Apify cost at scale**: Needs projected usage volume vs. pricing tiers before committing long-term
- **Data freshness vs. cost tradeoff**: Polling frequency (hourly vs. every few hours) needs to be tuned against Apify usage costs

---

## 11. Success Metrics (suggested — to be finalized)

- % of alerted jobs marked relevant by users
- Time from job posting to user alert (freshness)
- Reduction in duplicate/stale listings shown
- User retention / repeat engagement with alerts
