from __future__ import annotations

import json
import re
from collections import Counter


STOP = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "your",
    "have",
    "will",
    "please",
    "build",
    "make",
    "create",
    "a",
    "an",
    "to",
    "of",
    "in",
    "on",
}


def tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_./-]+", text.lower()) if t not in STOP and len(t) > 1}


def rank_files(prompt: str, files: dict[str, str], limit: int = 8) -> list[tuple[str, str, float]]:
    """Return the most relevant files for a prompt (path, content, score)."""
    query = tokenize(prompt)
    scored: list[tuple[str, str, float]] = []
    for path, content in files.items():
        path_tokens = tokenize(path.replace(".", " ").replace("/", " "))
        body_tokens = tokenize(content[:3000])
        overlap = len(query & (path_tokens | body_tokens))
        path_bonus = 2.0 if any(t in path.lower() for t in query) else 0.0
        size_penalty = min(len(content) / 20000.0, 1.0)
        score = overlap * 2.0 + path_bonus - size_penalty
        # Always keep entrypoints somewhat visible
        if path in {"index.js", "package.json", "README.md"}:
            score += 0.5
        scored.append((path, content, score))
    scored.sort(key=lambda x: x[2], reverse=True)
    if not scored:
        return []
    # Keep at least top N with score > 0, else top entrypoints
    positive = [s for s in scored if s[2] > 0]
    return (positive or scored)[:limit]


def build_smart_context(
    prompt: str,
    files: dict[str, str],
    memory: list[str],
    prior_results: list[str],
) -> str:
    ranked = rank_files(prompt, files)
    parts: list[str] = ["## Relevant project files"]
    for path, content, score in ranked:
        snippet = content if len(content) < 3500 else content[:3500] + "\n…(truncated)"
        parts.append(f"### {path} (relevance {score:.1f})\n```\n{snippet}\n```")

    omitted = sorted(set(files) - {p for p, _, _ in ranked})
    if omitted:
        parts.append("## Other files in workspace\n" + ", ".join(omitted))

    if memory:
        parts.append("## Project memory (recent conversation)")
        for idx, msg in enumerate(memory[-6:], start=1):
            parts.append(f"{idx}. {msg[:600]}")

    if prior_results:
        parts.append("## Prior AI outputs")
        for idx, result in enumerate(prior_results[-3:], start=1):
            parts.append(f"### Output {idx}\n{result[:1800]}")

    return "\n\n".join(parts)


def summarize_change_set(before: dict[str, str], after: dict[str, str]) -> list[dict]:
    changes = []
    for path in sorted(set(before) | set(after)):
        old = before.get(path)
        new = after.get(path)
        if old == new:
            continue
        if old is None:
            action = "create"
        elif new is None:
            action = "delete"
        else:
            action = "update"
        changes.append(
            {
                "path": path,
                "action": action,
                "before": old or "",
                "after": new or "",
                "before_lines": (old or "").count("\n") + (1 if old else 0),
                "after_lines": (new or "").count("\n") + (1 if new else 0),
            }
        )
    return changes


def unified_diff(path: str, before: str, after: str) -> str:
    import difflib

    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
    )
