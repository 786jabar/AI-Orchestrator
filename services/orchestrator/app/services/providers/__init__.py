from __future__ import annotations

import json
import re

import httpx

from .base import AiProviderClient, AiResponse


class MockProvider(AiProviderClient):
    name = "mock"

    async def send_prompt(self, task: str, context: str) -> AiResponse:
        lower = task.lower()
        if "score the solution" in lower or "strict code reviewer" in lower:
            return AiResponse(
                content=(
                    "SCORE: 0.82\n"
                    "- Structure is clear and runnable\n"
                    "- Add stronger input validation next\n"
                    "- Consider extracting HTML into a template helper"
                ),
                provider=self.name,
                model="mock-critic-v1",
            )

        if "continue after tool results" in lower:
            pass
        elif "verify the project" in lower or ("use tools if needed" in lower):
            if "<tool name=\"list_files\"" not in task and "tool results" not in lower:
                return AiResponse(
                    content='Inspecting workspace.\n<tool name="list_files" />\n',
                    provider=self.name,
                    model="mock-tools-v1",
                )

        target = "index.js"
        if "test.js" in lower or "test script" in lower:
            target = "test.js"
            content = f"""I'll add `{target}`.

```{target}
const test = require('node:test');
const assert = require('node:assert/strict');

test('forge link smoke', () => {{
  assert.equal(1 + 1, 2);
  assert.ok(true, {json.dumps(task[:80])});
}});
```
"""
            return AiResponse(content=content, provider=self.name, model="mock-v2")

        # Rich demo app: PulseBoard / team status board
        if any(k in lower for k in ("pulseboard", "team status", "teammates", "live team", "status board")):
            content = """I'll implement a complete PulseBoard team status app in `index.js`.

```index.js
const http = require("http");

const PORT = process.env.PORT || 3000;

const TEAM = [
  { name: "Ava Chen", role: "Product", status: "online" },
  { name: "Jordan Lee", role: "Engineering", status: "busy" },
  { name: "Sam Ortiz", role: "Design", status: "away" },
  { name: "Riley Kim", role: "Support", status: "online" },
];

const STATUSES = ["online", "busy", "away"];

function render(team) {
  const cards = team
    .map(
      (m) => `
      <article class="card">
        <div class="avatar">${m.name.split(" ").map((p) => p[0]).join("")}</div>
        <div class="meta">
          <h2>${m.name}</h2>
          <p>${m.role}</p>
        </div>
        <span class="pill ${m.status}">${m.status}</span>
      </article>`
    )
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PulseBoard</title>
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0; min-height: 100vh; font-family: "Segoe UI", Georgia, serif;
      background:
        radial-gradient(900px 400px at 10% -10%, rgba(61,214,198,.18), transparent 55%),
        linear-gradient(160deg, #071216, #0b1c22 50%, #10262e);
      color: #e8f2f0;
    }
    main { max-width: 880px; margin: 0 auto; padding: 2.5rem 1.25rem 3rem; }
    header h1 { margin: 0; font-size: 2.4rem; letter-spacing: -0.03em; color: #3dd6c6; }
    header p { margin: .45rem 0 1.5rem; color: #8aa3a8; }
    .actions { display: flex; gap: .6rem; margin-bottom: 1.25rem; }
    button {
      border: 0; border-radius: 10px; padding: .7rem 1rem; font-weight: 650; cursor: pointer;
      background: linear-gradient(135deg, #2bbbad, #3dd6c6); color: #042026;
    }
    .grid { display: grid; gap: .85rem; }
    .card {
      display: grid; grid-template-columns: 52px 1fr auto; gap: .85rem; align-items: center;
      padding: 1rem 1.1rem; border-radius: 14px; border: 1px solid rgba(125,211,198,.18);
      background: rgba(12, 28, 34, .82);
    }
    .avatar {
      width: 52px; height: 52px; border-radius: 12px; display: grid; place-items: center;
      background: #18333d; color: #3dd6c6; font-weight: 700;
    }
    .meta h2 { margin: 0; font-size: 1.05rem; }
    .meta p { margin: .2rem 0 0; color: #8aa3a8; font-size: .9rem; }
    .pill {
      text-transform: uppercase; letter-spacing: .06em; font-size: .68rem; font-weight: 700;
      padding: .35rem .65rem; border-radius: 999px;
    }
    .pill.online { background: rgba(90,214,125,.18); color: #5ad67d; }
    .pill.busy { background: rgba(240,180,41,.18); color: #f0b429; }
    .pill.away { background: rgba(160,174,192,.18); color: #a0aec0; }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>PulseBoard</h1>
      <p>Live team pulse</p>
    </header>
    <div class="actions">
      <button id="refresh" type="button">Refresh statuses</button>
    </div>
    <section class="grid" id="board">${cards}</section>
  </main>
  <script>
    const statuses = ${JSON.stringify(STATUSES)};
    const board = document.getElementById("board");
    function shuffle() {
      const pills = [...board.querySelectorAll(".pill")];
      pills.forEach((el) => {
        const next = statuses[Math.floor(Math.random() * statuses.length)];
        el.className = "pill " + next;
        el.textContent = next;
      });
    }
    document.getElementById("refresh").addEventListener("click", shuffle);
  </script>
</body>
</html>`;
}

const html = render(TEAM);

if (process.env.FORGELINK_ONCE === "1") {
  process.stdout.write(html);
  process.exit(0);
}

const server = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(html);
});

server.listen(PORT, () => console.log(`PulseBoard listening on ${PORT}`));
```

Explanation: Complete PulseBoard app with teammate cards, status pills, and client-side refresh.
"""
            return AiResponse(content=content, provider=self.name, model="mock-pulseboard-v1")

        match = re.search(r"file[:\s]+([\\w./-]+)", task, re.I)
        if match:
            target = match.group(1)

        content = f"""I'll update `{target}` based on your request.

```{target}
// Generated by Mock AI (advanced agent loop)
// Task: {task[:180].replace(chr(96), "'")}

const http = require("http");
const port = process.env.PORT || 3000;
const html = `<!doctype html><html><body style="font-family:Georgia,serif;padding:2rem;background:#0f172a;color:#e2e8f0">
  <h1 style="color:#38bdf8">ForgeLink Advanced Build</h1>
  <p>{task.replace('`', "'")[:240]}</p>
  <button onclick="location.reload()" style="margin-top:1rem;padding:.6rem 1rem;border:0;border-radius:8px;background:#3dd6c6;color:#042026;font-weight:600">Refresh</button>
</body></html>`;

if (process.env.FORGELINK_ONCE === "1") {{
  process.stdout.write(html);
  process.exit(0);
}}

const server = http.createServer((req, res) => {{
  res.writeHead(200, {{ "Content-Type": "text/html; charset=utf-8" }});
  res.end(html);
}});

server.listen(port, () => console.log(`listening on ${{port}}`));
```

Explanation: Advanced mock agent simulates tool-aware coding with critic-ready output.
"""
        return AiResponse(content=content, provider=self.name, model="mock-v2")


class ClaudeProvider(AiProviderClient):
    name = "claude"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    async def send_prompt(self, task: str, context: str) -> AiResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": (
                "You are a senior software engineer collaborating in a shared Node.js workspace. "
                "When proposing file changes, wrap each file in a fenced code block whose language "
                "tag is the exact file path (example: ```index.js). Keep responses concise."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": f"## Shared project context\n{context}\n\n## Task\n{task}",
                }
            ],
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        return AiResponse(content=text, provider=self.name, model=self.model, raw=data)


class OpenAIProvider(AiProviderClient):
    name = "gpt"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def send_prompt(self, task: str, context: str) -> AiResponse:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a coding agent in a shared Node.js workspace. "
                        "Propose file edits using fenced blocks tagged with the file path."
                    ),
                },
                {"role": "user", "content": f"## Shared project context\n{context}\n\n## Task\n{task}"},
            ],
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return AiResponse(content=text, provider=self.name, model=self.model, raw=data)


class GeminiProvider(AiProviderClient):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def send_prompt(self, task: str, context: str) -> AiResponse:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are a UI-focused coding agent in a shared Node.js workspace. "
                                "Propose file edits using fenced blocks tagged with the file path.\n\n"
                                f"## Shared project context\n{context}\n\n## Task\n{task}"
                            )
                        }
                    ]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return AiResponse(content=text, provider=self.name, model=self.model, raw=data)


def parse_file_blocks(markdown: str) -> dict[str, str]:
    """Extract ```path ... ``` code blocks from model output."""
    pattern = re.compile(r"```([^\n`]+)\n(.*?)```", re.DOTALL)
    files: dict[str, str] = {}
    for lang, body in pattern.findall(markdown):
        path = lang.strip().split()[0]
        # Skip plain language tags without path separators or extensions
        if "/" in path or "." in path:
            files[path.lstrip("./")] = body.strip("\n") + ("\n" if body.strip() else "")
    return files
