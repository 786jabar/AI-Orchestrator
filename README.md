# ForgeLink — Advanced AI Orchestrator Platform

Web platform that routes software tasks across Claude, GPT, and Gemini into one shared Node.js workspace, with a separate sandbox service for execution.

## Architecture

```
apps/web                 React + TypeScript + Monaco
services/orchestrator    FastAPI — projects, VFS, task queue, AI routing, tools, critic
services/sandbox         FastAPI — isolated code execution (local subprocess; E2B when keyed)
data/                    SQLite metadata + on-disk project/sandbox trees
```

Orchestrator and sandbox are separate processes so either can be swapped or scaled independently.

## Advanced capabilities (v0.2)

- **Smart context packing** — ranks relevant files for each prompt
- **Tool-using agent loop** — `list_files`, `read_file`, `write_file`, `run_tests`
- **Critic scoring** — secondary reviewer assigns quality scores
- **Auto-improve** — low scores trigger a fix pass
- **Approval-gated diffs** — optional apply/reject before writes land
- **Project snapshots** — checkpoint & restore (with safety snapshot)
- **Project memory** — conversation history fed into later prompts
- **Live SSE stream** — real-time agent/pipeline telemetry in the UI
- **Full pipeline** — Plan → Code → UI → Tests → Verify (+ sandbox check)

## Quick start

```bash
python3 -m pip install -r services/orchestrator/requirements.txt -r services/sandbox/requirements.txt
cd apps/web && npm install && cd ../..
cp .env.example .env   # optional API keys

./scripts/start-sandbox.sh
./scripts/start-orchestrator.sh
cd apps/web && npm run dev
```

Open http://127.0.0.1:5173

Without API keys, Mock mode still exercises tools, critic, pipeline, sandbox, and diffs.

## Default routing

| Category        | Provider |
|-----------------|----------|
| architecture    | Claude   |
| debugging       | Claude   |
| code_generation | GPT      |
| testing         | GPT      |
| ui_generation   | Gemini   |
| general         | Claude   |

## Key APIs

- `POST /api/projects/:id/tasks` — single routed agent step (`use_tools`, `auto_improve`, `require_approval`)
- `POST /api/projects/:id/orchestrate` — multi-stage pipeline
- `GET  /api/projects/:id/events` — SSE live stream
- `GET/POST /api/projects/:id/snapshots` — checkpoint / restore
- `GET  /api/projects/:id/memory` — project conversation memory
- `GET/POST /api/projects/:id/changes/...` — pending diff apply/reject
- `POST /api/projects/:id/run` — sandbox execution

## Notes

- Cursor cannot be embedded; ForgeLink calls model APIs directly.
- Sandbox prefers E2B when `E2B_API_KEY` is set; otherwise local subprocess with timeout.
- Runtime scope: **Node.js only** for now.
