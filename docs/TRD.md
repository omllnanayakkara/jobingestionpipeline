# Technical Requirements Document (TRD)
## AI-Powered Job Tracking & Matching Agent

**Version:** 1.0 (MVP Scope)
**Status:** Draft — Aligned with PRD v1.0
**Companion doc:** `job-tracking-agent-PRD.md`

---

## 1. Architecture Overview

The system splits into two halves, connected by a database sync:

1. **Ingestion pipeline** (background, scheduled) — scrapes job sources, deduplicates, stores raw listings
2. **User-facing flow** (request-driven) — parses CVs, matches against listings, serves results, sends alerts

See accompanying architecture diagrams: `ingestion_dedup_pipeline` and `user_facing_matching_flow`.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend language/framework | Python (FastAPI recommended) | Async support matters for I/O-heavy work (scraping, model calls, embeddings) |
| Frontend | React | — |
| Scheduled jobs | Azure Functions (Timer Trigger) | Consider Durable Functions for fan-out/fan-in across multiple sources; watch execution time limits on Consumption plan |
| Primary database | PostgreSQL + `pgvector` extension | Single database for structured data and vector similarity — no separate vector DB needed at MVP scale |
| Caching layer | Redis (Upstash free tier, or Azure Cache for Redis Basic) | Replaces the earlier "search DB" design — caches computed match results with TTL aligned to the recency window |
| API design | REST | Better fit than GraphQL — resource-oriented endpoints (CV upload, preferences, matches, alerts), simpler caching, lower complexity |
| Authentication | Email + password, plus OAuth (Google, LinkedIn — identity only, not scraping) | — |
| Notifications | Azure Communication Services (email) | Does not cover push notifications — pair with Azure Notification Hubs or Firebase Cloud Messaging if in-app/mobile push is needed later |
| File storage (CVs) | Azure Blob Storage | Store raw uploaded files here, not in Postgres |
| Secrets management | Azure Key Vault | For Apify keys, DB credentials, etc. |
| Observability | Azure Application Insights | Prioritize monitoring the scraping pipeline specifically — most failure-prone part (site layout changes, Apify errors, rate limits) |

---

## 3. Data Sourcing & Ingestion

| Source | Method | Notes |
|---|---|---|
| LinkedIn | Apify actor | Public listings only, no login/session-cookie scraping |
| Glassdoor | Apify actor | Company reviews/ratings enrichment |
| topjobs.lk, rooster.jobs, itpro.lk, xpress.jobs | Custom in-house scrapers | ToS review required before building |

**Scale-up path:** Apify validates the pipeline at MVP stage. Migrate to custom scrapers (Playwright + Camoufox + residential proxies) only if cost, coverage, or reliability becomes a bottleneck at scale.

### Deduplication (two distinct checks, both retained in architecture)
1. **Cross-platform dedup** — same job posted across multiple sources (LinkedIn, topjobs.lk, etc.), identified via similarity checking on title/company/description. (Phase 2 per PRD — full similarity-based implementation deferred; MVP may ship a simplified/no-op version.)
2. **Re-scrape dedup** — same listing re-encountered on a later scrape run before it expires from the recency window. Identified via a unique key (source + external job ID, or URL hash). Required for MVP.

### Handling image-based job posts
Some sources (notably topjobs.lk) post listings as images rather than text. These are routed through the same model used for CV parsing (see Section 4) — Qwen2.5-VL in vision mode — to extract structured fields (title, company, location, salary) before entering the standard dedup/storage flow.

---

## 4. CV Parsing

Two-path extraction depending on file type, converging on a shared structuring step:

1. **Digital text CVs (common case):** extract raw text directly via `pdfplumber` (PDF) or `python-docx` (DOCX) — no vision model needed.
2. **Image-based/scanned CVs (fallback case):** when no text layer exists or extraction returns empty/garbled output, fall back to **Qwen2.5-VL** in vision mode.
3. **Structuring (shared by both paths):** raw text is passed to **Qwen2.5-VL** in text mode with a prompt to extract skills, work experience, education, and seniority level into structured JSON.
4. Structured profile is shown to the user as **editable** before being used for matching (per PRD 6.1).

Qwen2.5-VL serves double duty across CV parsing and image-based job ad OCR — one shared model service rather than separate systems.

**Model hosting:** Hugging Face Inference API (pay-per-use) recommended for MVP over self-hosting on a GPU VM — self-hosting is the single largest potential cost in this stack (~$150-400+/month) versus a much smaller pay-per-use cost at low volume.

---

## 5. Scam / Fake Listing Detection

**Model:** `AventIQ-AI/BERT-Spam-Job-Posting-Detection-Model` (Hugging Face) — a BERT-based binary classifier fine-tuned specifically for fake vs. real job posting detection. Free to run via `transformers`, no hosting cost beyond inference compute.

**Where it runs:** applied during ingestion, after dedup and before storage — flags suspicious listings rather than silently dropping them, so flagged items can be reviewed or surfaced to users with a warning rather than lost entirely.

**Known limitation — imbalanced training data:** the standard datasets this class of model trains on (e.g., Kaggle/EMSCAD) are heavily imbalanced (~5% fraudulent, ~95% legitimate). High headline accuracy can mask poor recall on the fraudulent class specifically — evaluate any candidate model on **fraud-class recall**, not overall accuracy, before relying on it.

**Known limitation — geographic transfer:** underlying training data is presumably US/global listings and may not transfer cleanly to scam patterns specific to the Sri Lankan market. Treat as a v1 baseline filter, not a solved problem — fine-tuning on local scam patterns is a candidate Phase 2 refinement once real flagged/reported data exists.

---

## 6. Matching Engine

**Approach: Hybrid (structured filtering + embedding similarity)**

1. **Hard constraint filtering (SQL):** location, recency window, employment type — cheap, unambiguous, filters the candidate pool first.
2. **Semantic ranking (embeddings):** remaining candidates ranked by cosine similarity between CV content and job description embeddings.

**Embedding model:** `all-MiniLM-L6-v2` (via `sentence-transformers`) for MVP — free, fast, CPU-runnable, sufficient to validate matching quality. Upgrade path to `BGE-M3` if ranking quality proves insufficient at real usage (drop-in swap, same interface).

**Storage:** vectors stored directly in Postgres via `pgvector` — no separate vector database (e.g., Qdrant) needed at MVP scale. Revisit only if query latency becomes a measured bottleneck at much higher listing volume (millions of vectors).

---

## 7. Hosting & Cost Summary

| Component | Approach | Est. monthly cost |
|---|---|---|
| PostgreSQL (B1MS, 32GB) | Azure Database for PostgreSQL Flexible Server | $0 for 12 months (free tier), ~$12-20/mo after |
| Scheduled scraping | Azure Functions | $0 (always-free tier, well within 1M executions/mo) |
| Cache | Upstash Redis (free tier) or Azure Cache Basic | $0-16/mo |
| Job scraping | Apify | ~$5-20/mo at low volume |
| Notifications | Azure Communication Services | $0-5/mo at low volume |
| File storage | Azure Blob Storage | ~$1-2/mo |
| CV/job ad parsing | Hugging Face Inference API (Qwen2.5-VL) | $0-30/mo depending on volume |
| **Estimated MVP total** | | **~$10-40/month** |

**Key cost risk:** self-hosting Qwen2.5-VL on a GPU VM instead of using a hosted inference API could increase total spend 5-10x. Start with the hosted API; revisit self-hosting only once volume justifies the fixed GPU cost.

**Note:** Azure has no automatic spend cap — configure budget alerts from day one.

---

## 8. Open Items Before Implementation

- Confirm ToS for topjobs.lk, rooster.jobs, itpro.lk, xpress.jobs permits scraping
- Evaluate `AventIQ-AI/BERT-Spam-Job-Posting-Detection-Model` on fraud-class recall (not just accuracy) before relying on it in production
- Finalize polling frequency (1hr vs 2hr) against Apify usage cost
- Decide on push notification provider if in-app/mobile alerts are added beyond email
- Define concrete REST API endpoint list (upload CV, set preferences, get matches, manage alerts)
- Confirm CI/CD approach for Functions, API, and React frontend