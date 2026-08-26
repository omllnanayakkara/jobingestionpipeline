# ADR-0003: Rolling recency window instead of tracking shown-listing history

**Status:** Accepted

**Context**
The system needs to avoid repeatedly surfacing the same or stale job listings to a user without building a persistent record of "what has this user already been shown."

**Options considered**
1. Store a history of previously-shown listings per user and filter those out on every query.
2. Use a rolling, user-configurable time window (e.g. last 7 or 30 days) and rely on age alone to exclude stale listings.

**Decision**
Use the rolling recency window. No per-user "already shown" history is stored.

**Consequences**
Significantly simpler system — no extra storage, no extra join, no growing table to prune. Old listings naturally age out. The trade-off: a listing can technically reappear if it's still within the window and the user simply didn't notice it before, since there's no permanent memory of "seen." This gap is partly addressed later by the Phase 2 application-tracking feature (ADR-0005), which lets a user mark something as already handled.

---

# ADR-0004: Scam detection and company reputation kept in MVP scope as core differentiators

**Status:** Accepted

**Context**
Existing tools (LoopCV, AIApply) don't offer scam/fake-listing filtering or company reputation context alongside listings. These were identified as genuine gaps in the market, particularly relevant given how common dubious postings are on local Sri Lankan job boards and Facebook groups.

**Options considered**
1. Ship MVP without either feature, add both later once the core matching loop is validated.
2. Build both into MVP scope as first-class differentiators, even though they add real implementation time to an already tight solo timeline.

**Decision**
Both are built as part of MVP (scam detection via a pretrained classifier, company reputation via Apify's Glassdoor data), not deferred to Phase 2.

**Consequences**
Meaningfully stronger differentiation from existing tools and better user trust from day one. The cost is real: additional model integration, an additional Apify data source, and additional evaluation work (see ADR-0016), all inside an already ambitious 4-6 week solo build.

---

# ADR-0005: Application tracking and match-percentage scoring deferred to Phase 2

**Status:** Accepted

**Context**
During feature brainstorming, both "let users mark a job as already applied" and "show a match percentage with strengths/gaps" came up as genuinely valuable additions.

**Options considered**
1. Build both into the MVP alongside the core matching and alerting loop.
2. Defer both to Phase 2, keep MVP scope focused on discovery and alerting.

**Decision**
Deferred to Phase 2. Neither is required to validate the core value proposition (getting relevant, fresh, trustworthy job alerts).

**Consequences**
Smaller, faster-to-ship MVP. The trade-off is that early users won't get duplicate-application suppression or match transparency, which could reduce trust or perceived usefulness of the ranking until these ship.

---

# ADR-0006: Apify (third-party) for LinkedIn and Glassdoor instead of custom scrapers

**Status:** Accepted

**Context**
LinkedIn and Glassdoor both actively defend against scraping (bot detection, no free public API, and a documented precedent of Apify itself suing another scraping company, Proxycurl, over LinkedIn data). Building and maintaining custom scrapers for these two sources specifically would require significant stealth/proxy infrastructure with ongoing maintenance as the sites change.

**Options considered**
1. Build custom scrapers with stealth tooling (Playwright + Camoufox + residential proxies).
2. Use Apify's existing pre-built actors for these sources as a paid, managed service.
3. Skip LinkedIn/Glassdoor entirely.

**Decision**
Use Apify for MVP. Explicitly scoped as a validation-stage choice, with a stated path to migrate to custom scraping only if cost, coverage, or reliability becomes a real bottleneck at scale.

**Consequences**
Avoids upfront investment in stealth/proxy infrastructure and the ongoing burden of chasing site layout changes; lower legal and account-ban risk. The cost is a recurring per-listing fee and dependency on a third-party vendor's actor availability and pricing.

---

# ADR-0007: Custom in-house scrapers for local job boards instead of Apify

**Status:** Accepted

**Context**
No Apify actors exist for topjobs.lk, rooster.jobs, itpro.lk, or xpress.jobs. These sites also appear less defended against scraping than LinkedIn/Glassdoor.

**Options considered**
1. Skip these local boards entirely.
2. Build custom in-house scrapers.
3. Wait for third-party scraper support to appear.

**Decision**
Build custom scrapers for all four boards.

**Consequences**
This is a core part of the product's actual differentiation — local market coverage that larger competitors don't have. Likely lower technical difficulty than LinkedIn/Glassdoor given weaker bot defenses. The full maintenance burden (site layout changes breaking the scraper) falls entirely on the solo developer, and each site's Terms of Service needs review before building, which is a real calendar-time risk independent of development hours.

---

# ADR-0008: Two separate deduplication checks instead of one unified check

**Status:** Accepted

**Context**
An early architecture sketch had a single generic "check and remove duplicates" step. On closer inspection, two genuinely different problems were being conflated: the same listing being re-scraped by the pipeline's own recurring schedule, versus the same underlying job being posted with different wording across multiple sites.

**Options considered**
1. One unified fuzzy-matching dedup step for everything.
2. Two distinct checks: an exact/hash-based check for re-scrape duplicates, and a similarity-based check for cross-platform duplicates.

**Decision**
Two separate checks, each solved with the technique suited to it — a unique key (source + external ID) for re-scrape dedup, embedding similarity for cross-platform dedup.

**Consequences**
The re-scrape check is cheap, exact, and fast. The genuinely hard problem (cross-platform matching) is isolated and can be simplified or deferred to Phase 2 without blocking MVP launch. The cost is a more complex ingestion pipeline — two distinct steps to build, test, and reason about instead of one.

---

# ADR-0009: Vision-language model (Qwen2.5-VL) instead of traditional OCR for image-based listings

**Status:** Accepted

**Context**
Some job ads, notably on topjobs.lk, are posted as images with graphic-design layouts (multiple columns, logos mixed with text) rather than plain scanned text.

**Options considered**
1. Traditional OCR (e.g. Tesseract) — mature, fast, but weak on layout understanding.
2. A vision-language model (Qwen2.5-VL) that understands structure, not just characters.
3. Skip image-based listings entirely.

**Decision**
Use Qwen2.5-VL, since it can distinguish "this is the title" from "this is the salary" even in a designed layout, and output structured fields directly rather than raw text requiring further parsing.

**Consequences**
Higher-quality structured extraction from complex, designed job ads, and the same model is reusable for CV parsing (ADR-0015). The trade-off: heavier and slower per call than plain OCR, and a generative model carries a real risk of hallucinating or slightly rewording text rather than transcribing it exactly — a risk plain character-recognition OCR doesn't have.

---

# ADR-0010: Redis cache instead of a second synced "search" database

**Status:** Accepted

**Context**
An early architecture sketch had two databases — a raw ingestion DB and a separate "search DB" — kept in sync via an explicit "sync recent jobs" step.

**Options considered**
1. Keep the dual-database design with a manual sync step.
2. Collapse to a single database plus a Redis cache layer in front of it, with TTL-based expiry.

**Decision**
Single Postgres database plus Redis cache. The sync step is eliminated entirely.

**Consequences**
Removes an entire class of consistency bugs (two datasets silently disagreeing). Redis's TTL naturally aligns with the product's existing recency-window concept, so cache expiry doesn't need separate logic. Cache key design and invalidation still need to be thought through deliberately, and Redis is one more piece of infrastructure to run, though a free tier is available at this scale.

---

# ADR-0011: pgvector instead of a separate vector database (Qdrant)

**Status:** Accepted

**Context**
The matching engine needs vector similarity search over job listing and CV embeddings. A dedicated vector database (Qdrant) was considered as an alternative to using Postgres's own vector extension.

**Options considered**
1. Qdrant — purpose-built, potentially faster at very large scale.
2. pgvector — a Postgres extension, keeping vectors in the same database as structured data.

**Decision**
pgvector, since the hybrid matching approach (ADR-0017) needs to combine structured SQL filtering with vector ranking in a single query path, and running two databases at MVP scale (thousands to tens of thousands of listings) adds operational overhead without a corresponding benefit yet.

**Consequences**
One database to run and reason about; hybrid queries (filter then rank) stay a single round trip instead of two systems coordinating. The explicit trade-off, and revisit trigger, is that pgvector may become a real bottleneck only once listing volume reaches into the millions with heavy concurrent load — not a concern at MVP scale.

---

# ADR-0012: Neon (free-tier managed Postgres) instead of Azure Database for PostgreSQL, for the MVP phase

**Status:** Accepted

**Context**
Azure Database for PostgreSQL Flexible Server has no genuine permanent free tier — its free allotment is a 12-month grant, after which it costs roughly $12-20/month. Neon and Supabase both offer indefinite free tiers with pgvector support.

**Options considered**
1. Use Azure Postgres from day one, for consolidated billing and infrastructure with the rest of the Azure-hosted stack.
2. Use Neon's free tier during MVP validation, with an explicit option to migrate to Azure later.

**Decision**
Neon for the MVP/validation phase.

**Consequences**
Zero database cost while validating the product concept. The trade-off is provider sprawl — compute lives on Azure, the database lives on Neon — and Postgres migration between providers, while a well-understood, contained task (pg_dump/restore), is still a deliberate future step rather than something to defer indefinitely if the project scales.

---

# ADR-0013: Free, self-hostable embedding model instead of a paid embedding API

**Status:** Accepted

**Context**
The matching engine needs to convert CV and job description text into vectors. Several paid options exist (OpenAI, Cohere, Voyage), alongside free open-source models available via Hugging Face.

**Options considered**
1. A paid embedding API.
2. `all-MiniLM-L6-v2` — a small, free, open-source model runnable on CPU.

**Decision**
`all-MiniLM-L6-v2` for MVP, with a named upgrade path (`BGE-M3`) if ranking quality proves insufficient once there's real usage data to evaluate against.

**Consequences**
Zero marginal cost per embedding, and fast enough to validate the entire matching concept without any infrastructure investment. The accepted trade-off: this model sits roughly 5-8% behind larger models on complex retrieval benchmarks — a known quality ceiling that's acceptable for validating the concept, not necessarily for a mature product.

---

# ADR-0014: Hugging Face Inference API instead of self-hosting models on a GPU

**Status:** Accepted

**Context**
Both Qwen2.5-VL (vision-language model) and the scam classifier need to run somewhere. Self-hosting either requires a GPU-capable VM.

**Options considered**
1. Self-host on a GPU VM.
2. Call Hugging Face's hosted Inference API on a pay-per-use basis.

**Decision**
Use the hosted Inference API for MVP.

**Consequences**
This avoids what was identified as the single largest potential cost in the entire stack — a GPU VM runs roughly $150-400+/month, versus an estimated $0-30/month on pay-per-use at MVP volume. No GPU infrastructure to provision or maintain. The trade-off is that cost scales with usage rather than being fixed, and the project takes on a dependency on Hugging Face's API availability and pricing. Self-hosting is explicitly deferred until volume actually justifies the fixed GPU cost.

---

# ADR-0015: Qwen2.5-VL reused for both job-ad OCR and CV parsing

**Status:** Accepted

**Context**
Extracting structured information from a graphically complex job-ad image and extracting structured information from a CV are, at a mechanical level, the same underlying task: turn messy input into structured JSON.

**Options considered**
1. Separate models or pipelines for each use case.
2. One shared model service, with input routed to vision or text mode depending on whether the source document already has an extractable text layer.

**Decision**
One shared Qwen2.5-VL service serving both use cases.

**Consequences**
One model to host, call, and prompt-engineer instead of two, which simplifies operations meaningfully. The trade-off is that this model now sits on the critical path for two different features — a failure or degradation affects both simultaneously — though the two use cases are similar enough that this shared-fate risk is considered low.

---

# ADR-0016: Pretrained free scam-detection classifier used as a v1 baseline

**Status:** Accepted

**Context**
Fake and scam job postings are a known problem in the target market, but building a custom classifier from scratch would require a labeled dataset the project doesn't have.

**Options considered**
1. Build a custom classifier, requiring dataset collection and labeling before any model work could start.
2. Use an existing pretrained model from Hugging Face (`AventIQ-AI/BERT-Spam-Job-Posting-Detection-Model`).
3. Skip scam detection for MVP entirely.

**Decision**
Use the pretrained model as a v1 baseline filter. Explicitly plan to evaluate it on fraud-class recall (not just overall accuracy) before trusting it in production, given that the datasets this class of model typically trains on are heavily imbalanced (~5% fraudulent, ~95% legitimate) — a condition under which high accuracy can mask poor detection of the fraudulent class specifically. Flagged listings are surfaced to users with a warning rather than hard-rejected.

**Consequences**
Zero training cost or time, ships inside the MVP timeline. The explicit, accepted limitation: the model's training data is presumably US/global, and may not transfer cleanly to scam patterns specific to the Sri Lankan market. This is treated as a known v1 limitation, not a solved problem, with fine-tuning on local data flagged as a Phase 2 candidate once real flagged/reported data exists.

---

# ADR-0017: Hybrid matching engine (SQL hard-constraint filtering + embedding similarity ranking)

**Status:** Accepted

**Context**
Pure keyword matching misses semantically similar but differently-worded skills or roles (e.g. "led a team of 5" vs. "people management experience"). Pure embedding-based matching can't cheaply or precisely express hard constraints like location, recency, or employment type.

**Options considered**
1. Keyword-only matching.
2. Embedding-only (pure semantic) matching.
3. A hybrid: hard constraints applied first via SQL, then the remaining candidates ranked by embedding similarity.

**Decision**
Hybrid — filter first, rank second.

**Consequences**
Fast, cheap SQL filtering narrows the candidate pool before the more expensive similarity computation runs on it, and the semantic ranking step captures nuance that keyword matching alone would miss. The trade-off is a genuinely more complex two-stage pipeline to build and tune correctly, compared to either approach alone.

---

# ADR-0018: REST instead of GraphQL for the API design

**Status:** Accepted

**Context**
Needed to choose an API style for the core app's public-facing endpoints.

**Options considered**
1. REST.
2. GraphQL.

**Decision**
REST. The data isn't deeply relational from the client's perspective — "get my matches," "update my preferences" are naturally resource-shaped requests, not a graph a client needs to traverse flexibly — and REST has simpler caching semantics and a lower learning curve for a solo developer.

**Consequences**
Simpler to build, debug, and cache, and better matched to the team size (one developer, no need for GraphQL's benefit of serving multiple heterogeneous client types from one flexible endpoint). The trade-off is less flexibility if future clients ever need very different data shapes from the same underlying resources — that would mean new endpoints or versioning rather than just a different query.

---

# ADR-0019: CV_profile kept as a separate entity from Search_profile

**Status:** Accepted

**Context**
CV upload is optional and structurally different from stated preferences — CVs hold multi-valued data (skills, experience entries) and a large embedding vector, while preferences are scalar fields (one role, one location scope, one recency window) that get edited directly and often.

**Options considered**
1. Merge CV-derived fields as attributes directly on Search_profile.
2. Keep CV_profile as its own entity, related 1:1 (later many:many) to User.

**Decision**
Keep them separate — a form of vertical partitioning appropriate for an optional, structurally different, independently-updated attribute group.

**Consequences**
Avoids repeating-group or JSON-blob awkwardness sitting next to otherwise clean scalar columns. Re-uploading a CV can never silently overwrite hand-edited preferences, since they're different rows entirely. The vector index only needs to account for rows that actually have an embedding. The cost: one additional join is needed whenever both are required together — mitigated by `Job_match` holding both foreign keys directly (ADR-0022).

---

# ADR-0020: CV data kept off the User entity as well

**Status:** Accepted

**Context**
After settling CV_profile as separate from Search_profile, the same question arose one level up: could CV-derived attributes (skills, experience) simply live on the User entity itself?

**Options considered**
1. Add skills/experience columns directly to User.
2. Keep CV data on its own entity; User remains identity/auth-only.

**Decision**
Keep separate. `User` is an identity/auth entity touched on every login; CV data is domain/matching data touched by the matching engine. Mixing them would bloat authentication queries with data they never need, and violates the same separation-of-concerns principle already applied to the Scraper and Repository interfaces.

**Consequences**
Lean, fast identity queries. Repositories stay single-purpose — `UserRepository` for auth concerns, a separate profile repository for CV data. No significant downside identified; this was a low-cost decision that reused reasoning already established elsewhere in the project.

---

# ADR-0021: Multiple CV profiles and multiple Search profiles allowed per user

**Status:** Accepted

**Context**
Users may realistically be job-hunting across multiple distinct tracks at once (e.g. backend vs. frontend roles), each warranting a different CV and different search criteria. This was originally scoped as strict 1:1 for MVP, with multi-profile support explicitly deferred to Phase 2.

**Options considered**
1. Keep strict 1:1 as originally planned, defer flexibility to Phase 2 as scoped.
2. Allow many CV profiles and many search profiles per user now, adding an explicit relationship between the two entities to disambiguate which pairs with which.

**Decision**
Allow multiple profiles of each type now. Once both sides can be many, a shared `user_id` alone can no longer answer "which CV goes with which search profile" — so an explicit optional foreign key (`Search_profile.cv_profile_id`) was added.

**Consequences**
More realistic support for multi-track job seekers, and the schema supports this without requiring a later migration. The trade-off: this pulls Phase 2 schema complexity earlier than planned, and adds real UI complexity (a profile switcher) even if the initial UI still ships as effectively single-profile at launch. It also directly required the decision in ADR-0023.

---

# ADR-0022: Job_match modeled as a real junction table, not a relationship-diamond

**Status:** Accepted

**Context**
An early ER diagram modeled matching as a "generates" relationship (a diamond) connecting `Search_profile` and `Job_listing`, which then separately "produced" a `Job_match` entity via another arrow. This didn't map cleanly onto any single physical table.

**Options considered**
1. Keep the diamond-and-arrow structure literally as drawn.
2. Collapse it into one table, `Job_match`, holding foreign keys to each participant plus its own attributes (`match_score`, `matched_at`).

**Decision**
Collapse into a single junction table — standard ER-to-relational mapping practice whenever a relationship needs attributes of its own.

**Consequences**
The diagram now matches what actually gets migrated into SQL, avoiding a mismatch discovered only when writing DDL. Normalization checks can be applied directly to a real table. The diagram loses a small amount of its original "this is a derived/computed thing" framing, though the underlying meaning is unchanged.

---

# ADR-0023: cv_profile_id kept as a snapshot on Job_match rather than derived via join

**Status:** Accepted

**Context**
Once `Search_profile` could point to different `CV_profile`s over time (per ADR-0021), a match's "which CV was this actually scored against" became ambiguous if derived live through `search_profile → cv_profile_id`, since that link is reassignable after the fact.

**Options considered**
1. Derive `cv_profile_id` via a join through `Search_profile` — fully normalized, no redundancy.
2. Store a copy of `cv_profile_id` directly on `Job_match` at the time the match was computed — denormalized, but historically accurate.

**Decision**
Store the snapshot. This is an intentional, documented denormalization for audit-trail correctness, not an oversight.

**Consequences**
Match history can never silently "rewrite itself" if a user later changes which CV a search profile points to. The trade-off is genuine redundancy in the schema — the join-derived value and the snapshot could, in principle, disagree if application logic has a bug — a risk accepted deliberately in exchange for historical accuracy, rather than defaulted into.

---

# ADR-0024: Job_alert modeled as its own weak entity instead of a boolean flag

**Status:** Accepted

**Context**
An early design considered a simple `notified` boolean on `Job_match` to track whether a user had been alerted about a match.

**Options considered**
1. A boolean flag on `Job_match`.
2. A separate `Job_alert` entity, weakly dependent on `Job_match`.

**Decision**
Separate entity.

**Consequences**
Supports genuine history — multiple send attempts, different channels, resend logic — instead of a single mutable bit that only reflects the current state and discards everything before it. The cost is one additional table and relationship to manage, versus a single column.

---

# ADR-0025: TDD adopted as the development approach

**Status:** Accepted

**Context**
An explicit project goal is building good engineering habits and decision-making skill, not just shipping working code, given the developer's junior/learning-focused stage.

**Options considered**
1. Write tests after implementation, or skip them under time pressure — common under a tight solo deadline.
2. Test-first development (Red-Green-Refactor) for all feature-shaped work.

**Decision**
TDD adopted project-wide, reflected directly in the WBS as reordered subtasks (tests written before implementation, not after) for every feature task.

**Consequences**
Forces interface-first thinking — code can't be tested against a contract that doesn't exist yet, which reinforces the Repository/DI patterns already being learned. Provides a real safety net for refactoring under time pressure. The explicit, accepted cost: this genuinely increases total estimated hours (233 → 288 hours when subtasks were first broken out this way) — a deliberate trade of raw speed for habit-building.

---

# ADR-0026: SOLID principles and specific design patterns adopted deliberately from Phase 0

**Status:** Accepted

**Context**
The project involves several interchangeable scraper implementations (LinkedIn, Glassdoor, four local boards), identified as a natural teaching opportunity for the Strategy pattern specifically. Combined with the explicit goal of learning software design decision-making, not just implementation.

**Options considered**
1. Let design patterns emerge organically while building features, as needs become apparent.
2. Define the core interfaces (Scraper, Repository, NotificationSender) and wire dependency injection upfront, as a dedicated Phase 0, before any feature code is written.

**Decision**
Dedicated Phase 0: Strategy pattern for scrapers, Repository pattern plus DI for data access, Adapter pattern for external model/API calls — all defined before Phase 1 feature work begins, each paired with a short ADR explaining the choice.

**Consequences**
Retrofitting these patterns after four or more scrapers already existed directly against Postgres would have cost far more than building on them from day one. Gives small, concrete artifacts (interfaces, ADRs) to practice the actual "why this pattern, what's the trade-off" reasoning on, rather than absorbing it passively. The cost: roughly 20 hours of upfront work before any user-visible feature exists — a real, accepted delay to first visible progress.

---

# ADR-0027: Two-service split (Python worker + .NET core app) instead of a single-language backend

**Status:** Accepted

**Context**
I have an existing .NET background and is new to Python. However, Python seems to be prominent for AI/ML related work and also the scapping tools like Apify SDK support are limited to python and nodejs.

**Options considered**
1. Single Python (FastAPI) backend for everything, including scraping.
2. Single .NET backend for everything, including scraping (technically possible via REST calls to Apify and custom .NET scraping libraries, but without first-class SDK support).
3. Split — Python owns scraping and the ML-heavy ingestion pipeline, .NET owns the core app (auth, matching, alerts, database).

**Decision**
Split. This lets the architecturally rich learning (SOLID, DI, Repository, TDD) happen entirely in the language already known fluently, while Python is picked up in a narrow, well-defined, low-stakes corner of the system (the ingestion worker) rather than fighting on two unfamiliar fronts simultaneously.

**Consequences**
Plays to existing strength for the harder, more valuable learning goal (design decisions), while still using Python's genuinely stronger scraping and Hugging Face ecosystem where it matters. The cost: two ecosystems to build, deploy, and monitor (NuGet and pip, xUnit and pytest, two CI pipelines), and a real new coordination surface — the inter-service boundary — that a single-service design simply wouldn't have (see ADR-0028, ADR-0029).

---

# ADR-0028: Single-writer principle — only the .NET core app writes to the database

**Status:** Accepted

**Context**
With two services potentially both needing database access, there was a real risk of two independent write paths (a Python repository implementation and a .NET one) drifting out of sync over time.

**Options considered**
1. Both services get their own repository implementation and write to Postgres directly.
2. Only the core app ever writes; the ingestion worker communicates results via an API call instead.

**Decision**
The core app is the sole writer. The Python worker produces clean, deduplicated, classified data and hands it off via one HTTP call — it never touches Postgres for writes. One deliberate, narrow exception: the worker retains read-only database access specifically for the re-scrape dedup existence check, since making that a network round trip per scraped item would be wasteful, and reads don't threaten write consistency the way a second write path would.

**Consequences**
Keeps "one Repository interface, one implementation" true in practice, not just on a diagram — there's no risk of the two languages' write logic silently diverging. The cost: the worker now depends on the core app being reachable in order to actually persist anything it finds, which required designing retry/backoff logic (ADR-0029) so a temporary outage doesn't silently lose an entire scrape cycle's results.

---

# ADR-0029: Plain HTTPS with a shared API key for inter-service communication — no message broker

**Status:** Accepted

**Context**
The two services need a way for the Python worker to hand scraped, processed data to the .NET core app. "Microservices" as a term can imply heavyweight tooling (a message broker, service mesh, API gateway) that would be disproportionate for two services owned entirely by one developer.

**Options considered**
1. A full message-broker or event-bus architecture (e.g. Kafka, RabbitMQ).
2. A plain REST call to an internal endpoint, authenticated with a shared secret, with basic client-side retry on failure.

**Decision**
Plain HTTPS POST to an internal ingestion endpoint, authenticated with a single shared API key stored in Key Vault, with a small number of retries and short backoff on the worker side if the call fails. Explicitly not OAuth, not mTLS, not a queue.

**Consequences**
Minimal new infrastructure to learn, operate, or debug — proportionate to two services one person owns and can redeploy easily. Easy to reason about: one call, one documented contract (task 0.6). The accepted limitation: there's no durability guarantee beyond the worker's own retry logic — if the core app is unreachable long enough to exhaust retries, that batch's results are lost until the next scheduled run. This is an accepted risk at MVP scale; a queue would be the fix if it but will be considered when the application grows. 

---

# ADR-0030: Job listing embeddings computed in the Python worker; CV embeddings computed in .NET

**Status:** Accepted

**Context**
Both job listings and CVs need embeddings from the same model (`all-MiniLM-L6-v2`) for the resulting vectors to be comparable in the matching engine. The two services have different natural reasons to need each: the worker already computes job-listing embeddings for cross-platform dedup (ADR-0008); CV embedding only happens on-demand at upload time, which is a live, user-triggered action naturally belonging to the request-driven core app.

**Options considered**
1. Centralize all embedding computation in one service, with the other calling it via an internal API for every embedding it needs.
2. Split the computation — each service computes the embeddings it already has the clearest reason to need, both calling the same underlying model.

**Decision**
Split. The worker includes the job listing's embedding (already computed for dedup) directly in its ingestion payload, so it's never computed twice. The core app computes CV embeddings itself, calling the Hugging Face Inference API's feature-extraction endpoint directly.

**Consequences**
No duplicate computation of the same embedding, and the core app never needs a local Python ML runtime just for this one purpose. The trade-off: both sides must stay disciplined about using the exact same model version, since any drift between them would silently make the two sets of vectors incomparable without either side necessarily noticing — worth stating explicitly in the task 0.6 ingestion contract rather than leaving implicit.

---

# ADR-0031: SQLAlchemy + Alembic instead of Prisma for the ingestion pipeline's ORM/migrations

**Status:** Accepted

**Context**
`prisma/schema.prisma` was drafted to model `JobListing`, `Company`, and `Run` for eventual persistence, but no Python code ever depended on the generated Prisma client — the ingestion pipeline is otherwise 100% Python (scrapers, `models/job_listing.py` dataclasses, `pipeline/*.py`), and this repo has no Node project scaffolding (no `package.json`). Running the Prisma CLI therefore meant `npx` re-fetching the whole toolchain on every invocation, which failed repeatedly in this environment — first with a network `ECONNRESET` during download, then with a corrupted npx cache (`ERR_MODULE_NOT_FOUND`) on retry — blocking schema validation entirely.

**Options considered**
1. Keep Prisma and fix the environment (clear the npx cache, retry the download, or properly bootstrap a local Node project with `prisma` as a real `devDependency` instead of relying on `npx` re-fetching it each time).
2. Switch to SQLAlchemy + Alembic — pure Python ORM and migration tooling with no Node dependency at all.

**Decision**
Switch to SQLAlchemy + Alembic. Since nothing depended on the Prisma client yet, there was no migration cost, and it removes an entire second-language toolchain from a repo that otherwise has zero Node footprint.

**Consequences**
One less language/toolchain to install, run, and debug in this repo — no more npx network flakiness blocking schema work, and `alembic revision --autogenerate` / `alembic upgrade head` ran successfully on the first real attempt. Prisma's `@map("value")` convention (aligning stored enum values with the Python enums' `.value` strings) is replicated via SQLAlchemy's `Enum(..., values_callable=...)`. The trade-off: no auto-generated typed client — model and session code (`db/models.py`, `db/session.py`) is hand-written instead of generated, and Alembic's autogenerate-diff workflow is less turnkey than a single `schema.prisma` file driving both migrations and a client.

---

# ADR-0032: `db.models` used only as a persistence-boundary conversion target, not as the pipeline's source of truth

**Status:** Accepted

**Context**
With SQLAlchemy models now in place (ADR-0031), the natural follow-up question was whether `db.models.JobListing`/`Company` should become the single shape used throughout the pipeline — scrapers, dedup, LLM extraction, and persistence all operating on the same ORM objects — instead of the existing `NormalizedListing`/`JobListing` dataclasses in `models/job_listing.py`.

**Options considered**
1. Make `db.models` the single source of truth: collector and LLM-extraction stages build/mutate `db.models.JobListing` directly.
2. Keep the existing dataclasses as the DB-agnostic shape for scraping and LLM I/O, and add a small boundary converter that builds `db.models.Company`/`JobListing` only at the point of persistence.

**Decision**
Option 2. A boundary converter (`db/converters.py`, functions `build_company_model` and `build_job_listing_model`) maps a finished `JobListing` dataclass instance onto `db.models.Company`/`JobListing`, used by the new persistence stage (`pipeline/store.py`). Scraping and LLM extraction never import `db.models`. This is also the only workable direction structurally: `db/models.py` already imports the shared enums (`JobCategory`, `JobType`, etc.) from `models/job_listing.py`, so having `models/job_listing.py` import back from `db/` would create a circular import — a converter has to live on the `db/` side of that boundary regardless.

**Consequences**
Scraping and LLM-extraction code stays free of any SQLAlchemy/Postgres dependency, so those stages remain testable and runnable without a database — the JSON-export path in `pipeline/base.py` is unaffected. Company resolution (`Company.name` is unique and non-nullable) and the get-or-create query against an existing row are left to the caller in `pipeline/store.py`, not baked into the converter itself. The trade-off: two parallel shapes for a job listing (dataclass and ORM model) instead of one, so a new field generally needs to be added in both `models/job_listing.py` and `db/models.py`, kept in sync by the converter functions.

---

# ADR-0033: `pipeline/store.py` persists via plain-dict Postgres upserts, not ORM object inserts

**Status:** Accepted

**Context**
The first version of `pipeline/store.py` built `db.models.Company`/`JobListing` ORM instances (via `db/converters.py`, per ADR-0032) and passed them straight into `session.execute(core_insert_stmt, list_of_orm_objects)`. Code review surfaced this doesn't work: SQLAlchemy Core's `execute(stmt, params)` executemany form expects plain column-name dicts, not ORM instances with relationship attributes (`company=company` is a relationship, not the `company_id` column, so it never actually bound). Two further issues came from the same code review: the Company upsert's `on_conflict_do_update` targeted `id` — which `build_company_model` generates fresh on every call, so it can never collide — instead of the real unique constraint (`Company.name`); and neither table had a de-duplication or re-run story (repeat company names within a batch produced multiple rows; a re-scraped `external_id` crashed the whole batch on a bare `insert()`).

**Options considered**
1. Keep building ORM instances in `db/converters.py` and switch `pipeline/store.py` to ORM-style persistence (`session.add_all(...)`), letting the unit-of-work resolve the `company` relationship into `company_id` on flush.
2. Keep Core-style `pg_insert(...).on_conflict_do_update(...)` upserts for both tables, but have `db/converters.py` return plain dicts instead of ORM instances, and resolve `company_id` explicitly via a `RETURNING id, name` on the Company upsert before building job rows.

**Decision**
Option 2. `build_company_model`/`build_job_listing_model` in `db/converters.py` now return plain dicts of column values instead of `Company`/`JobListing` instances. `pipeline/store.py` de-duplicates companies by `company_name` within a batch (one dict per distinct name), skips any listing with no `company_name` (required, unique, non-nullable), and runs a single `pg_insert(Company).on_conflict_do_update(index_elements=["name"], ...).returning(Company.id, Company.name)` to get the authoritative id for every company — whether freshly inserted or already existing — before building job-listing dicts with that resolved `company_id`. `JobListing` rows are also upserted (`on_conflict_do_update(index_elements=["external_id"], ...)`), refreshing the re-scrapable fields (title, description, salary, skills, etc. — see `JOB_LISTING_REFRESHABLE_COLUMNS`) while leaving identity/provenance columns (`id`, `external_id`, `source`, `source_url`, `run_id`) untouched on conflict.

**Consequences**
Both tables now handle re-running the pipeline safely: a listing seen before updates in place instead of crashing the batch on a duplicate-key error, and a company shared by several listings in one batch (or across runs) resolves to one row instead of many. Persistence code is Core-only end to end (`pg_insert` + explicit dicts), so there's no ORM/Core parameter-binding mismatch to reason about — the trade-off is that `db/converters.py` no longer returns typed `Company`/`JobListing` objects, just dicts, so a typo in a dict key (e.g. a renamed `db.models` column) won't be caught until the statement executes against Postgres rather than at construction time.

---

# ADR-0034: Bounded client-side retry (and eager model unload) around the local Ollama normalizer call, instead of relying on the Ollama service alone

**Status:** Accepted

**Context**
`llm_handlers/local_llm_handler.py` calls a local Ollama-served model (`numind/nuextract3:q4_k_m`, run via `--flash-attn`, an 8GB prompt-cache limit, and up to 32 context checkpoints) to normalize scraped job listings. During batch pipeline runs, the request failed with `httpx.RemoteProtocolError: Server disconnected without sending a response`. `journalctl -u ollama` showed the actual cause: the kernel OOM killer repeatedly killed the `llama-server` subprocess mid-request (`ollama.service: The kernel OOM killer killed some processes in this unit`, twice within ~10 minutes), which drops the client's TCP connection with no HTTP response rather than returning an error the client can parse. The pipeline processes up to `MAX_BATCH_SIZE` (20) listings per run, each a separate `ollama.chat()` call, so a single OOM-triggered restart previously failed the entire batch.

**Options considered**
1. Do nothing at the application layer — treat this purely as an Ollama/infra sizing problem (lower `-c`/context size or `--cache-ram` in the systemd service config) and let the pipeline crash on the rare OOM restart until that's fixed.
2. Add a bounded retry-with-backoff in `LocalLLMHandler.chat()` around the `ollama.chat()` call (catching `httpx.RemoteProtocolError`, `httpx.ConnectError`, `ollama.ResponseError`), and set `keep_alive=0` so the model unloads immediately after each response instead of staying resident in memory for a keep-alive window, reducing the standing memory pressure that batch processing puts on the service.

**Decision**
Option 2. `chat()` now retries up to `MAX_RETRIES` (3) times with linear backoff (`RETRY_BACKOFF_SECONDS * attempt`) on those specific exceptions, and `keep_alive` was changed from `"10m"` to `0`.

**Consequences**
A transient OOM-kill/restart of the local Ollama service no longer fails an entire batch run outright — the retry gives the service time to come back up and reprocess that single listing. Setting `keep_alive=0` trades per-call latency (the model has to reload rather than staying warm across the batch) for a smaller steady-state memory footprint during back-to-back calls, which was judged worth it given OOM kills were actively breaking runs. The underlying resource-sizing issue is not fixed by this change — if the model's context/cache configuration still doesn't fit available RAM, retries only mask repeated failures with added latency rather than eliminating them; lowering the Ollama service's context size or cache-RAM limit remains the real fix if OOM kills persist or worsen.