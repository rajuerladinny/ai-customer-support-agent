# Resolve AI — Customer Support Agent

A portfolio prototype for investigating customer support cases. It combines a customer conversation, a sample order lookup, evidence, a case timeline, and a human approval queue in one workspace.

**Current status: interactive prototype, not an AI-powered production service.** Chat replies use deterministic order lookup and simple keyword-based document excerpt matching. No language model, vector database, real orders, real customer data, payments, email, or external helpdesk is connected.

## Demo scenario

A fictional electronics store receives three sample cases: damaged headphones, a delayed delivery, and an unanswered question. A support person can inspect the case, view a relevant sample policy, and approve or reject a simulated replacement request.

## Features available today

- Three predefined support cases with a case investigation timeline.
- Server-side lookup of two fictional sample orders (`NS-1042`, `NS-1038`).
- Basic extractive search over two sample policy documents, with source names and an explicit no-match response.
- Upload up to five `.txt` files, each no larger than 15 KB, to search locally. Documents are saved in the same local JSON file and can be removed in the Knowledge screen.
- Approve or reject a simulated replacement; approval decisions and chat messages are saved to a local JSON file across restarts.
- Create and resolve a local human-review request for a sample case, retaining the customer summary and timestamps. No message is sent externally.
- Backend tests and GitHub Actions checks.

The GitHub Pages demo runs entirely in the browser, using fictional data and browser-local storage. It does not call a real AI model or a support backend. The private Sites demo is an earlier version and does not contain these features.

## Browser-only demo

Run `npm run build:demo` to build `dist/demo`. The **Deploy demo** GitHub Actions workflow tests and publishes that directory to GitHub Pages on a push to `main` or manual dispatch. GitHub Pages must be enabled in repository Settings → Pages with Source set to GitHub Actions. Pages serves static files only: all support API calls are handled in the browser using the same search and validation logic as the local app. Changes stay in browser local storage; use fictional information and Reset demo to clear it. No server, model, email, helpdesk or live action is connected. A successful deployment is required before a demo URL can be claimed.

## Run locally

Requires **Node.js 20 or newer**. No packages or API keys are required. The app persists demo messages, decisions, review requests and uploaded documents in `data/state.json` on the machine running the server. This file is ignored by Git and is cleared by Reset demo.

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
2. A sample order ID is retrieved from the backend, or the backend searches built-in policies and locally saved documents.
3. The workspace shows a matching excerpt and its source, or reports that no match was found.
4. A support person reviews the simulated investigation and proposed action.
5. A simulated approval or rejection updates the local demo state. No real-world action occurs.
6. Request human review from the case workspace; the local queue shows its summary and status until marked reviewed. This does not notify a real person.

The predefined case timelines and dashboard counts are sample UI data; they do not yet update automatically from backend activity. See [Architecture and roadmap](docs/architecture.md) for the actual implementation and planned work.

## Project layout

| Path | Purpose |
| --- | --- |
| `worker/index.html` | Frontend, styling and simulated case workspace |
| `worker/backend.mjs` | Sample order lookup and extractive search API |
| `scripts/dev-server.mjs` | Local HTTP adapter and state API |
| `tests/backend.test.mjs` | Backend behaviour tests |
| `demo/` | Browser-only API adapter for the static demo |
| `.github/workflows/demo.yml` | Build and deploy demo to GitHub Pages |
| `.github/workflows/ci.yml` | Syntax checks and tests |
| `docs/architecture.md` | Architecture, limitations and development roadmap |

## Important limitations

This is a prototype for fictional data only. It has no authentication, authorization, tenant isolation, rate limiting, privacy controls, or production monitoring. Local demo messages, documents, review requests and approval decisions are stored unencrypted in `data/state.json`; use fictional data only. Uploaded text is stored by the local server; do not upload confidential or personal information. The demonstration must not be used to make real support, refund or replacement decisions.
