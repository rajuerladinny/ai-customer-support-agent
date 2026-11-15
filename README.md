# Resolve AI — Customer Support Agent

A portfolio prototype for investigating customer support cases. It combines a customer conversation, a sample order lookup, evidence, a case timeline, and a human approval queue in one workspace.

**Current status: interactive prototype, not an AI-powered production service.** Chat replies use deterministic order lookup and simple keyword-based document excerpt matching. No language model, vector database, real orders, real customer data, payments, email, or external helpdesk is connected.

## Demo scenario

A fictional electronics store receives three sample cases: damaged headphones, a delayed delivery, and an unanswered question. A support person can inspect the case, view a relevant sample policy, and approve or reject a simulated replacement request.

## Features available today

- Three predefined support cases with a case investigation timeline.
- Server-side lookup of two fictional sample orders (`NS-1042`, `NS-1038`).
- Basic extractive search over two sample policy documents, with source names and an explicit no-match response.
- Upload up to five `.txt` files, each no larger than 15 KB, to search during the current browser session. Their content is sent to the server with each search request and is lost on refresh.
- Approve or reject a simulated replacement; approval decisions and chat messages are saved to a local JSON file across restarts.
- Backend tests and GitHub Actions checks.

The original private Sites demo uses the same underlying UI and backend. This independent GitHub project runs with the Node development server described below; it does not include the private Site identity, credentials or deployment automation.

## Run locally

Requires **Node.js 20 or newer**. No packages or API keys are required. The app persists demo messages and decisions in `data/state.json` on the machine running the server. This file is ignored by Git.

```bash
git clone https://github.com/rajuerladinny/ai-customer-support-agent.git
cd ai-customer-support-agent
npm start
```

Open <http://localhost:3000>. To use a different port, set `PORT` before running `npm start`. The local server binds to `127.0.0.1`.

To try the document workflow: open **Knowledge**, upload a small `.txt` file with fictional content, return to **Overview**, and ask a question containing relevant words. Search is keyword-based and may miss relevant text or return an irrelevant excerpt; it is not semantic retrieval or AI.

## Quality checks

```bash
npm run check
npm test
```

The CI workflow runs syntax checks and backend unit tests on push, pull request, or manual dispatch. These tests do not verify browser rendering, real AI quality, production security, integrations, or support resolution outcomes.

## Workflow

1. A customer submits a question or selects a sample case.
2. A sample order ID is retrieved from the backend, or the backend searches built-in policies and optional session documents.
3. The workspace shows a matching excerpt and its source, or reports that no match was found.
4. A support person reviews the simulated investigation and proposed action.
5. A simulated approval or rejection updates the local demo state. No real-world action occurs.

The predefined case timelines and dashboard counts are sample UI data; they do not yet update automatically from backend activity. See [Architecture and roadmap](docs/architecture.md) for the actual implementation and planned work.

## Project layout

| Path | Purpose |
| --- | --- |
| `worker/index.html` | Frontend, styling and simulated case workspace |
| `worker/backend.mjs` | Sample order lookup and extractive search API |
| `scripts/dev-server.mjs` | Local HTTP adapter and state API |
| `tests/backend.test.mjs` | Backend behaviour tests |
| `.github/workflows/ci.yml` | Syntax checks and tests |
| `docs/architecture.md` | Architecture, limitations and development roadmap |

## Important limitations

This is a prototype for fictional data only. It has no authentication, authorization, tenant isolation, rate limiting, privacy controls, or production monitoring. Local demo messages and approval decisions are stored unencrypted in `data/state.json`; use fictional data only. Uploaded text is sent to the server during queries; do not upload confidential or personal information. The demonstration must not be used to make real support, refund or replacement decisions.
