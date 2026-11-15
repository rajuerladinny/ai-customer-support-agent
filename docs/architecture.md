# Architecture, workflow and roadmap

## Current architecture

The browser renders the support workspace from `worker/index.html`. It keeps case selection in memory. Chat messages, uploaded text documents, human-review requests and approval decisions are persisted by the local server to a JSON file. The Node local server (`scripts/dev-server.mjs`) serves the page and forwards `/api/*` requests to the shared Fetch-style handler in `worker/backend.mjs`.

- `GET /api/order?id=NS-1042` looks up a fictional order from a hard-coded dataset; unknown orders return HTTP 404.
- `POST /api/answer` accepts a question, searches built-in and locally stored text documents, and selects a matching excerpt by overlapping keywords. It requires two matching terms for multi-term questions and otherwise returns a no-match message. Input is bounded; this is not a semantic model or evidence verification system.
- The private Sites demo uses a Worker adapter, while this repository's independent local adapter is Node. A cloud deployment target and its security configuration remain future work.

## Current support flow

1. Select one of three sample cases. Case details, initial conversations, investigation and action suggestions are predefined in the frontend.
2. Enter an order ID, or send a question. The server returns sample order data or a document excerpt.
3. Review the displayed source or no-match message. Matching may be incomplete or irrelevant; the result is not a reliable confidence score.
4. The first case offers an approval/rejection demonstration. The decision is persisted locally; it does not create an order, replacement or refund.
5. Optionally upload `.txt` policies to the local store. Files persist across restarts and can be removed in the Knowledge screen. Use only fictional data.

The three seeded case investigations are not dynamically recalculated from questions. The queue and metrics are demonstrative, not operational analytics. There is no multi-user collaboration or audit history.

## Planned milestones

### 1. AI and evidence

- Configure a server-side model provider and secret using a supported integration.
- Extend text ingestion with chunking and semantic retrieval; PDF support is planned, not implemented.
- Add a curated evaluation set for groundedness, refusal when evidence is missing, citations and prompt-injection resistance.
- Make model costs, data handling and failure behaviour explicit; never expose API secrets to the browser.

### 2. Cases and approvals

- Replace the local JSON prototype store with a transactional database and persist case and audit events.
- Add roles, authenticated access, an audit trail and explicit confirmation before any external side effect.
- Drive case timelines and metrics from actual events, and verify action outcomes.

### 3. Customer integrations

- Add a configurable support platform and order-system integration with least-privilege credentials and server-side authorization.
- Add retries, idempotency, error monitoring and rate limits. Keep mock connectors for safe demos.

### 4. Intelligence and operational insights

- Identify recurring issues and knowledge gaps, and suggest drafts for human review.
- Add support-team analytics based on genuine case events. Validate each feature against realistic test cases before describing it as reliable.

## Safety and privacy boundaries

Never upload real customer records or sensitive documents to this prototype. Its document matching and sample approval flow are not suitable for live operations. Production use requires access control, tenant isolation, retention rules, audit logs, secure integration credentials, redaction, model evaluation and explicit policy checks.

## Local persistence added

`GET /api/state` loads saved messages and the sample approval decision. `POST /api/messages` appends a validated message, `POST /api/approval` records a one-time decision, and `POST /api/reset` explicitly clears the demo state. Writes are serialized in one process and replaced atomically. This is local single-process storage, not a database, audit log, or multi-user solution. Up to five text documents are stored in the same local file; `/api/documents` and `/api/documents/delete` manage them. Reset clears them together with messages and approvals.

## Local human-review queue

`POST /api/escalations` creates a review containing the case ID, a customer message summary and timestamp. It rejects a second open review for the same case. `GET /api/escalations` lists local requests, and `POST /api/escalations/resolve` records a review timestamp. The queue does not notify anyone, connect to a helpdesk, verify resolution, or provide a complete audit trail. Reset clears it.
