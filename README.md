# 10-K Detective

A learning MVP: find a ticker, choose two **report years**, extract Business (Item 1) and Risk Factors (Item 1A), and display grounded paragraph differences. React + TypeScript handles the interface; FastAPI handles SEC requests and analysis. No AI, API keys, database, authentication, or investment scoring.

See [the real public-filing example](docs/public-filing-example.md) for verified Apple 2024/2025 SEC links and a guided manual comparison.

## Public GitHub Pages demo

The Pages deployment hosts the React interface with exported **synthetic DEMO data**, not a running FastAPI server. It supports the 2024/2025 example and source documents. Live ticker lookup and SEC downloads require the backend described below. The Pages workflow generates fixture responses, builds with `VITE_STATIC_DEMO=true`, and deploys after each push to main. Local development continues to use the real API routes.

## Repository map

```text
backend/
  app/main.py       HTTP endpoints and orchestration
  app/sec.py        ticker lookup, filing discovery, headers, cache, limiter
  app/extract.py    HTML section boundaries and paragraph comparison
  fixtures/        clearly labeled fictional 2024/2025 reports
  tests/           offline API, extraction, discovery, and HTTP tests
frontend/
  src/main.tsx     lookup, year selection, evidence viewer
  src/style.css    responsive presentation
  vite.config.ts   local /api proxy to FastAPI
```

## First runnable steps (Windows PowerShell)

Install Python 3.11+ and Node.js 20.19+ (or 22.12+). Open a terminal in this repository.

1. Create the backend environment. This isolates Python packages from other projects.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATA_MODE = 'mock'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

2. In a second terminal, start the frontend. Vite serves React and forwards `/api` requests to the backend.

```powershell
cd frontend
npm ci
npm run dev
```

3. Open http://localhost:5173. Look up **DEMO**, select 2024 → 2025, then compare. Expect one replacement group (supplier text) and one addition group (privacy text). Open the source links and expand the extracted sections to check the evidence yourself. API docs: http://127.0.0.1:8000/docs.

On macOS/Linux use `python3`, `.venv/bin/python`, and `export DATA_MODE=mock`.

## Learn the data path

1. Read `main.py`: the company endpoint returns company metadata and eligible annual reports. The comparison endpoint retrieves exactly the two selected documents.
2. Read `sec.py`: a ticker maps to a zero-padded CIK. Submissions contain parallel arrays of filing fields; historical submissions are followed too. Original `10-K` forms are eligible; `10-K/A` amendments are excluded. For multiple originals in one report year, the latest filing date wins. Years refer to the report period end, not the filing date.
3. Read `extract.py`: HTML becomes normalized lines. Recognized Item headings bound the sections. The largest complete candidate avoids short table-of-contents entries. Missing or implausibly short boundaries fail visibly.
4. Follow `compare`: Python's SequenceMatcher aligns normalized paragraphs. Insert/delete/replace groups retain exact extracted text and paragraph positions on each side. A reordered paragraph may appear removed and added. Paragraph numbers refer to extraction, not SEC page numbers.
5. Read `main.tsx`: state tracks discovery, year selection, pending requests, errors, and comparison results. React renders text safely and links each excerpt to its source document.

## Live SEC mode

## Hosted FastAPI backend (Render)

`render.yaml` defines one free Python web service, one worker, a health check, mock mode, and CORS for this GitHub Pages origin. Import this repository as a Render Blueprint. Free instances can sleep when idle, so the first request may be slow. The frontend supports `VITE_API_BASE_URL` for a hosted API; disable `VITE_STATIC_DEMO` when connecting it. Set a real SEC identity through Render environment settings before enabling live mode; never commit that value.

## Live SEC mode

Mock mode is the default and never contacts SEC. Do not mistake synthetic evidence for real disclosures. No SEC identity is supplied by default and live API access has **not** been established for this user's identity.

Set a real descriptive application/contact identity in the backend terminal and restart:

```powershell
$env:DATA_MODE = 'live'
$env:SEC_USER_AGENT = '10-K Detective Your Name your.actual.email@your-domain.com'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Then look up a real ticker, such as AAPL. A successful ticker lookup verifies the ticker endpoint; a successful comparison separately verifies submissions and archive access. SEC can block requests even with valid headers. Failures remain visible; live mode never silently substitutes mock evidence. `.env.example` documents the settings; `.env` files are **not automatically loaded**.

SEC guidance: https://www.sec.gov/about/developer-resources and https://www.sec.gov/search-filings/edgar-application-programming-interfaces. All SEC hosts share one lock with a 0.5-second minimum request interval (at most 2 requests/second) and one-hour in-memory response cache. Use **one backend worker/process**; the limiter is not distributed. Account for other SEC clients on your network. No automatic retries on rate blocks. Cache disappears on restart. Historical filing discovery can take time for issuers with many submission files.

## Checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
cd ../frontend
npm run build
```

Tests make no network requests. Fixtures exercise the full API flow; HTTP transport mocks verify identity headers and cache behavior. GitHub Actions runs the same checks.

## Known limits and next steps

Section extraction is heuristic: unusual headings, PDF-only reports, tables, incorporated-by-reference disclosures, and nonstandard markup may fail or yield imperfect boundaries. Inspect the complete extracted sections and source documents. Whitespace/case-only edits are ignored; formatting changes and paragraph splits can create apparent differences. No semantic claims about risk severity are generated. A fiscal year ending in January is labeled by its report-date calendar year.

Next learning milestone: collect a small legally accessible corpus of actual filing HTML and add boundary regression tests before broadening live support. Then improve matching of reordered paragraphs. Defer AI Q&A until source extraction and citations are reliable.
