# CopilotKit Frontend

Next.js UI for interacting with local A2A agents and CopilotKit. Provides two entry points:

- `AgentExplorer` lists agent cards and lets operators send direct messages via the backend BFF
- `CopilotChat` embeds a CopilotKit conversation UI configured via environment variables

## Prerequisites

- Node 20+
- Backend running at `http://localhost:8100` (see `../backend`)
- Copy `.env.example` to `.env` and update runtime URLs or API keys as needed

## Getting Started

```bash
npm install
npm run dev
```

Navigate to [http://localhost:3000](http://localhost:3000) to access the control center UI. Update agent addresses using the backend `.env` file to surface additional services.
