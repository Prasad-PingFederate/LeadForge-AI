# ⚡ LeadForge AI

> **Autonomous B2B Sales, Competitor Intelligence & Lead-Generation Agent Platform**  
> Given ANY product or app website URL, LeadForge AI autonomously discovers, verifies, and scores high-intent buyers, analyzes competitor vulnerabilities, and drafts hyper-personalized outreach sequences.

---

## 🎯 Primary Objective

Enter any SaaS, B2B tool, or product URL (e.g., `https://cal.com`, `https://posthog.com`, `https://supabase.com`). LeadForge AI autonomously executes a full multi-agent go-to-market pipeline:

```
[Target Product URL]
        │
        ▼
1. Profiler Agent ───────► Crawls landing page & builds structured Ideal Customer Profile (ICP)
        │
        ▼
2. Competitor Agent ─────► Live web search -> Extracts competitor weaknesses, battlecards & 3 GTM strategies
        │
        ▼
3. Lead Hunter Agent ────► Discovers REAL buyers via live social intent listening (Reddit, HN, Web Dorks)
        │
        ▼
4. Waterfall Enricher ───► Crawls company sites, verifies email (Regex + MX DNS + Provider check), 0–100 score
        │
        ▼
5. Outreach Agent ───────► Drafts 3-step Cold Email + LinkedIn DM + Social Reply in Human-Approval Queue
        │
        ▼
6. Self-Learning Loop ───► Reply classifier re-weights highest-converting GTM strategies & sources
```

---

## 🛡️ Strict Engineering Rules (Zero-Hallucination Invariant)

1. **ZERO HALLUCINATED LEADS:** Every lead stored in the database **must** originate from a real external connector response with its exact `intent_source_url`, `intent_snippet`, and `intent_platform` recorded. LLMs are used solely to extract, classify, score, and write copy—**never** to invent names, domains, or email addresses.
2. **Real-Time Streaming UI:** Server-Sent Events (SSE) stream LangGraph node step transitions directly to the browser with live visual logs.
3. **Built-in Deliverability & Compliance:** Global `suppression_list`, mandatory unsubscribe links, per-inbox daily send caps (default 50/day), randomized throttle intervals (45–180s), and strict `email_status == "verified"` gating before mail dispatch.

---

## 🏗️ Architecture & Tech Stack

- **Backend:** Python 3.11+, FastAPI, LangGraph (Multi-Agent StateGraph), SQLAlchemy 2.0 (async), Alembic, PostgreSQL (with `pgvector`) / SQLite aiosqlite for local dev, Redis + ARQ background workers, httpx, BeautifulSoup4, dnspython.
- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS, TanStack Table, Lucide Icons.
- **Connectors:**
  - `intent_social.py`: Reddit Public JSON search, Hacker News Algolia Search API, Google Dorks (`"looking for alternative to [competitor]"`, `"recommend a tool for [pain]"`).
  - `b2b_discovery.py`: Real target companies via Serper / Tavily / Brave / Google Places.
  - `website_auditor.py`: Async crawl of homepage/about/contact pages to extract verified public emails, social URLs, and tech signals.
  - `email_verifier.py`: Multi-stage verification (Format + Disposable domain blocklist + Live DNS MX lookup + API check).
- **LLM Abstraction:** Provider-agnostic engine supporting:
  - **Auto-Cascade & Free Tiers:** Google Gemini (`gemini-1.5-flash`), Groq (`llama-3.3-70b-versatile`), and OpenRouter Free models.
  - **Zero-Key Heuristic Mode:** Built-in deterministic heuristic engine with thread-safe TTL caching (`TTLCache`) so the entire platform runs 100% offline without any paid API keys.
  - **Commercial Providers:** OpenAI (`gpt-4o-mini`) and Anthropic Claude.
- **B2C Deal Promotion Mode (BharatBazaro & Amazon India):**
  - Instant ASIN extraction and canonical universal affiliate link formatting (`tag=dammaiprasad-21`, `linkCode=ll1`, `ascsubtag`).
  - Automated category commission calculation (Home & Kitchen 9%, Small Appliances 7%, Beauty 8%, 0% smartphone filter).
  - WhatsApp VIP Deal Broadcast & Telegram Markdown alert generation with 1-click Web dispatch buttons.

---

## 🚀 Quickstart

### 1. Using Docker Compose (One-Command Full Stack)

```bash
# Clone the repository
git clone https://github.com/Prasad-PingFederate/LeadForge-AI.git
cd LeadForge-AI

# Configure environment
cp .env.example .env

# Launch Postgres, Redis, Backend, Worker, and Frontend
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API & Swagger:** http://localhost:8000/docs
- **SSE Stream:** http://localhost:8000/api/campaigns/{id}/stream

### 2. Local Development (Lightweight, No Docker Required)

#### Backend:
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

#### Run Test Suite:
```bash
cd backend
pytest tests -v
```

---

## 📊 Clay-Style Lead Grid Preview

| Lead / Company | Role / Contact | Verified Email | Score | Live Intent Signal & Source Proof | Actions |
|---|---|---|---|---|---|
| **Linear App** | Head of Engineering | `eng@linear.app` 🟢 | **94/100** | *"Frustrated with Jira latency, looking for keyboard-first issue tracker"* [🔗 Reddit Proof](https://reddit.com) | [Review Sequence] |
| **Cal.com** | VP of Product | `product@cal.com` 🟢 | **88/100** | *"Seeking enterprise scheduling with self-hosted privacy"* [🔗 HN Proof](https://news.ycombinator.com) | [Review Sequence] |

---

## 📄 License
MIT License. Built for modern autonomous B2B revenue and sales teams.
