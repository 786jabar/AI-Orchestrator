# ForgeLink — AI Orchestrator Platform

Web platform that routes software tasks across Claude, GPT, and Gemini into one shared Node.js workspace, with a separate sandbox service for execution.

## Architecture

```
apps/web                 React + TypeScript + Monaco
services/orchestrator    FastAPI — projects, VFS, task queue, AI routing
services/sandbox         FastAPI — isolated code execution (local subprocess; E2B when keyed)
data/                    SQLite metadata + on-disk project/sandbox trees
```

Orchestrator and sandbox are separate processes so either can be swapped or scaled independently.

## MVP build order covered

1. **Project workspace** — create projects, edit files (Monaco), persist to SQLite + disk VFS  
2. **AI integration** — Claude / GPT / Gemini clients with a consistent `send_prompt(task, context)` interface (mock fallback without keys)  
3. **Sandbox** — separate execution service; Node.js only for MVP  
4. **Routing** — category → model map with manual override  
5. **Pipeline UI** — live task handoffs in the sidebar  
6. **BYOK keys** — encrypted per-user API keys + routing table

## Quick start

```bash
# deps
python3 -m pip install -r services/orchestrator/requirements.txt -r services/sandbox/requirements.txt
cd apps/web && npm install && cd ../..

# optional keys
cp .env.example .env

# three terminals
./scripts/start-sandbox.sh
./scripts/start-orchestrator.sh
cd apps/web && npm run dev
```

Open http://127.0.0.1:5173

Without API keys, choose **Mock** or leave auto-routing — the mock provider still writes files so you can exercise save → route → sandbox.

## Default routing

| Category        | Provider |
|-----------------|----------|
| architecture    | Claude   |
| debugging       | Claude   |
| code_generation | GPT      |
| testing         | GPT      |
| ui_generation   | Gemini   |
| general         | Claude   |

## API sketch

- `POST /api/projects` — create workspace (seeds `index.js`, `package.json`, …)
- `GET/PUT /api/projects/:id/files` — shared VFS
- `POST /api/projects/:id/tasks` — classify, route, run one AI step
- `POST /api/projects/:id/orchestrate` — plan → code → UI → test pipeline
- `POST /api/projects/:id/run` — execute via sandbox service
- `PUT /api/users/:id/keys` — store encrypted BYOK keys

## Notes

- Cursor cannot be embedded; ForgeLink calls model APIs directly.
- Sandbox prefers E2B when `E2B_API_KEY` is set; otherwise uses a per-project local subprocess with timeout.
- Runtime scope for MVP: **Node.js only**.
