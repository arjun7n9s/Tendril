# SignalGraph: Autonomous GTM Change Intelligence

**Hackathon Track:** Track 1 - GTM Intelligence  
**Core Thesis:** Revenue teams do not need more static lead lists. They need a live, evidence-backed system that notices meaningful account and champion changes, understands why they matter, and turns them into reviewable next actions.

## 1. Product Positioning

SignalGraph is an AI GTM intelligence agent for B2B sales and revenue operations. It continuously monitors public web signals around target accounts, past champions, competitors, hiring plans, funding, product launches, and vendor migration clues. It stores those signals in a durable knowledge graph, scores them against the company's ideal customer profile, and drafts human-safe outreach or account briefs with citations.

The practical wedge is not "scrape LinkedIn and spam people." The wedge is:

> "Give sales teams a daily queue of account changes that are current, explainable, and safe to act on."

## 2. Why This Wins The Track

Track 1 asks for systems that monitor competitors, buying signals, and market movements in real time, enrich accounts into GTM workflows, replace manual research, and give AI agents live web context. SignalGraph maps directly to that.

Bright Data is not decorative here. It is the live web layer that can retrieve SERP results, public pages, dynamic pages, and structured web data reliably. Cognee is not decorative either. It is the persistent memory layer that turns one-off scraped facts into a timeline and relationship graph.

## 3. Refined Problem

Current GTM teams have four painful gaps:

1. Static data vendors are late. They often notice role changes, hiring shifts, product launches, and vendor clues after the buying window has already opened.
2. Sales reps still manually research accounts across Google, LinkedIn, GitHub, job boards, news, company sites, and review pages.
3. AI assistants forget context. They can summarize today's page but cannot reliably remember that a person was a prior champion, their old company used your product, and their new company is now hiring for the same technical stack.
4. Outreach automation creates trust risk. Hyper-personalized copy can become creepy, unverifiable, or non-compliant unless every claim is grounded and filtered.

## 4. The Engineered Solution

SignalGraph has three loops.

### Loop A: Account Watchtower

Input:
- Target accounts or market segment.
- Competitors to monitor.
- ICP rules such as company size, industry, geography, tech stack, role seniority, and pain indicators.

Signals collected:
- New job posts that imply initiatives or tool adoption.
- Company blog/news/product announcements.
- Pricing, positioning, and competitor messaging changes.
- Funding, expansion, layoffs, leadership changes, and office openings.
- Public GitHub activity for developer-tool products.
- SERP-visible mentions of relevant keywords.

Output:
- Account brief.
- Change timeline.
- Buying-signal score.
- Recommended next action.
- Citations for every fact.

### Loop B: Champion Mobility

Input:
- CRM export of prior champions or power users.
- Public identifiers such as name, prior company, role, GitHub URL, personal site, or public profile URL.

Practical implementation:
- Use public, allowed sources first: GitHub, personal sites, company team pages, conference bios, author pages, public articles, SERP results, and official company pages.
- Use Bright Data's structured APIs where available instead of fragile custom scraping.
- Treat LinkedIn as optional enrichment only if available through approved Bright Data Web Scraper API usage and hackathon terms.

Output:
- "Former champion appears to be at new company" event.
- Evidence bundle with confidence score.
- Suggested rep action, usually a warm reactivation note.

### Loop C: Lookalike Discovery

Input:
- Best existing customers/users.
- Outcome metadata: activation, retention, expansion, support burden, product usage, and deal size.

Cognee graph:
- Person -> role -> company -> industry -> tech stack -> pains -> outcomes.
- Company -> job posts -> initiatives -> competitor mentions -> buying signals.
- Champion -> previous product usage -> new company -> relevant trigger.

Output:
- Net-new accounts and contacts that resemble high-retention customers.
- Ranking by fit, timing, and evidence quality.
- Explainable "why now" field.

## 5. Partner Tool Usage

### Bright Data

Use Bright Data as the live web acquisition layer.

Recommended tools:
- **Bright Data MCP Server:** fastest hackathon integration for agentic search, `scrape_as_markdown`, structured extraction, and browser automation.
- **Search/SERP API:** discover relevant public pages and monitor account/competitor keywords.
- **Unlocker API / Web Unlocker:** retrieve public pages that block bots, manage IP/session/CAPTCHA issues, and return reliable content.
- **Browser API / Scraping Browser:** handle JavaScript-heavy pages when static retrieval fails.
- **Web Scraper API:** use pre-built structured scrapers where available, especially for commonly supported platforms.

Bright Data should power these demo actions:
- Search: "Company X hiring data engineer Kafka Snowflake" or "Company X competitor migration".
- Scrape: official careers page, blog post, press release, docs page, GitHub repo, or review page.
- Extract: structured JSON with signal type, date, account, evidence URL, confidence, and suggested action.

### Cognee

Use Cognee as the graph memory and retrieval layer.

Recommended usage:
- Ingest CRM seed records, scraped public documents, and extracted signal JSON into named datasets.
- Use permanent memory for account/champion history.
- Use session memory for live demo conversations.
- Query the graph for relationships such as:
  - "Which accounts now match our best-customer pattern?"
  - "Which former champions have a credible new-company signal?"
  - "Which competitor accounts show current migration or dissatisfaction signals?"

Cognee's value in the pitch:
- It converts web snippets into durable GTM memory.
- It lets the agent reason over change over time, not just summarize a page.
- It makes every recommendation explainable through relationships and evidence.

### AI/ML API

Use AI/ML API as the model gateway.

Recommended usage:
- One model for extraction into strict JSON.
- One stronger reasoning model for account briefs.
- One cheaper/faster model for email draft variants.

Why it helps:
- It gives model flexibility through an OpenAI-compatible interface.
- It reduces vendor lock-in and lets the demo show model routing as a product feature.

### Triggerware.ai

Use Triggerware as the automation layer if access is available.

Recommended workflow:
- Schedule daily account scans.
- Trigger graph updates when a new signal is found.
- Trigger rep notifications when score crosses a threshold.
- Trigger human approval before CRM writeback or email export.

If access is limited, implement the same abstraction locally with cron/background jobs and present Triggerware as the intended event workflow partner.

### Speechmatics

Optional, but there is a clean use case:
- Sales rep records a short voice note after a call.
- Speechmatics transcribes it.
- SignalGraph adds the note to Cognee as account memory.
- Future outreach drafts include call context without forcing reps to type notes.

This is a nice extra, not required for the core demo.

## 6. MVP Scope For The Hackathon

Build only the sharpest demo path:

1. Import a seed CRM CSV with 5 accounts, 3 prior champions, and 2 best-customer examples.
2. Run a Bright Data-powered scan for one selected account.
3. Collect 5-10 public sources: company page, careers page, blog/news, SERP results, GitHub/docs if relevant.
4. Extract structured signals:
   - signal_type
   - account
   - person if applicable
   - evidence_url
   - observed_at
   - confidence
   - why_it_matters
   - recommended_action
5. Store seed data and signals in Cognee.
6. Query Cognee for account fit and champion relationships.
7. Render a dashboard:
   - Live scan progress.
   - Signal cards with citations.
   - Knowledge graph/timeline.
   - AI-generated account brief.
   - Outreach draft with "safe mode" guardrails.
8. Require human approval before exporting any outreach.

## 7. Demo Story

Demo company:
- Use a fictional vendor: "VectorLake", a developer data platform.
- Seed best customers: fintech data teams using Snowflake, Kafka, dbt, and compliance-heavy workflows.
- Seed champion: "Maya Chen", formerly at a mock customer, now publicly listed on a new company's engineering blog or team page.

Live demo:
1. The rep opens SignalGraph and selects a target account.
2. The agent uses Bright Data to search and scrape public web evidence.
3. It finds that the account is hiring for data platform roles, recently published a migration blog, and has a public GitHub repo mentioning relevant tooling.
4. Cognee connects those facts to the ICP graph and the champion history.
5. The dashboard shows:
   - "Why now: hiring + migration + champion proximity."
   - "Evidence confidence: high/medium/low."
   - "Recommended action: send warm research note, not a hard pitch."
6. The outreach draft is grounded, non-creepy, and citation-backed.

## 8. Ethical Guardrails

SignalGraph should feel like responsible GTM intelligence, not surveillance.

Rules:
- Use public web data and approved APIs.
- Do not claim private knowledge.
- Do not mention sensitive personal inferences.
- Do not auto-send messages.
- Require citations for factual claims.
- Label confidence.
- Prefer account-level triggers over personal-life triggers.
- Use "human approval required" before CRM writeback or outreach export.

Outreach style:

Bad:
> "I saw you changed jobs and your new company is using competitor Y."

Good:
> "Congrats on the new role at Acme. I noticed the team is hiring around data platform reliability, and it reminded me of the work your previous team did around observability. Happy to share a short playbook if useful."

## 9. Architecture

Frontend:
- Next.js dashboard.
- Signal cards, graph/timeline view, account brief panel, approval drawer.

Backend:
- FastAPI or Next.js API routes.
- Job runner for scans.
- Postgres/Supabase for app state.
- Cognee for memory/graph.

Pipeline:

1. `seed_importer`
   - Reads CRM CSV.
   - Normalizes accounts, people, usage history, ICP examples.
   - Inserts into app DB and Cognee.

2. `source_discovery_agent`
   - Uses Bright Data MCP or SERP API.
   - Produces candidate URLs.

3. `scrape_extract_agent`
   - Uses Bright Data `scrape_as_markdown`, Unlocker, Browser API, or Web Scraper API.
   - Extracts structured facts with AI/ML API.

4. `graph_update_agent`
   - Writes extracted signals into Cognee.
   - Links accounts, people, companies, products, competitors, and events.

5. `scoring_agent`
   - Scores fit, timing, confidence, and actionability.

6. `briefing_agent`
   - Generates account brief, evidence summary, and outreach draft.

7. `approval_workflow`
   - Human reviews.
   - Optional CRM export/webhook.

## 10. Scoring Model

Total score: 100

- Fit score: 30
  - Industry, size, geography, role match, tech stack.
- Timing score: 30
  - Recent job posts, launches, funding, migrations, leadership changes.
- Relationship score: 20
  - Prior champion, known customer pattern, shared ecosystem.
- Evidence score: 20
  - Source quality, recency, number of corroborating sources, extraction confidence.

Only show a lead as "sales-ready" above 70 and with at least two independent evidence points.

## 11. What To Avoid

- Do not build a generic lead scraper.
- Do not make LinkedIn the only source of truth.
- Do not promise instant detection for every job change.
- Do not auto-send emails.
- Do not overbuild the lookalike engine before the live signal loop works.
- Do not rely on ungrounded LLM claims.

## 12. Submission Narrative

Short description:

> SignalGraph is a live GTM intelligence agent that uses Bright Data to monitor public web changes, Cognee to remember account and champion relationships, and AI models to turn verified signals into explainable sales actions.

Long description:

> Revenue teams lose deals because the buying moment happens before static lead databases update. SignalGraph continuously scans the public web for account changes, hiring signals, product launches, competitor movement, and champion mobility. Bright Data unlocks reliable live web access across search, public pages, and dynamic sites. Cognee stores those signals as graph memory so the agent can reason over people, companies, past product usage, and market events over time. The result is a daily queue of evidence-backed account briefs and human-approved outreach drafts, designed to be useful without being creepy.

## 13. Build Priority

Day 1:
- CSV seed import.
- Bright Data MCP/SERP scrape path.
- Basic extraction schema.
- Dashboard skeleton.

Day 2:
- Cognee ingestion and graph queries.
- Scoring model.
- Evidence cards.
- Account brief generation.

Day 3:
- Champion mobility demo with controlled public sources.
- Safe outreach guardrails.
- Presentation polish.
- Record demo video.

## 14. Source Notes From Research

- Bright Data Web Access APIs cover unblocking, crawling, dynamic content, SERP data, proxy rotation, and CAPTCHA solving: https://docs.brightdata.com/scraping-automation/introduction
- Bright Data MCP Server exposes search, scraping, extraction, structured platform data, and browser automation tools: https://docs.brightdata.com/ai/mcp-server/tools
- Cognee `remember()` can store data in permanent graph memory, with entity/relationship extraction and embeddings: https://docs.cognee.ai/core-concepts/main-operations/remember
- AI/ML API supports OpenAI-compatible SDK usage for chat, embeddings, audio, and related features: https://docs.aimlapi.com/quickstart/supported-sdks
- Speechmatics supports real-time transcription, batch transcription, TTS, and voice agent workflows: https://docs.speechmatics.com/

