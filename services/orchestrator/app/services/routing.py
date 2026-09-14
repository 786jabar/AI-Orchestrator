from ..models import AiProvider, TaskCategory

# Default routing map: category → preferred provider
ROUTING_TABLE: dict[TaskCategory, AiProvider] = {
    TaskCategory.architecture: AiProvider.claude,
    TaskCategory.code_generation: AiProvider.gpt,
    TaskCategory.debugging: AiProvider.claude,
    TaskCategory.ui_generation: AiProvider.gemini,
    TaskCategory.testing: AiProvider.gpt,
    TaskCategory.general: AiProvider.claude,
}


KEYWORD_HINTS: list[tuple[tuple[str, ...], TaskCategory]] = [
    (("architect", "design", "plan", "decompose", "spec"), TaskCategory.architecture),
    (("debug", "fix", "bug", "error", "stack trace"), TaskCategory.debugging),
    (("ui", "css", "layout", "frontend", "html", "style"), TaskCategory.ui_generation),
    (("test", "jest", "pytest", "coverage", "assert"), TaskCategory.testing),
    (("implement", "code", "write", "generate", "function", "api"), TaskCategory.code_generation),
]


def classify_task(prompt: str) -> TaskCategory:
    lower = prompt.lower()
    scores: dict[TaskCategory, int] = {c: 0 for c in TaskCategory}
    for keywords, category in KEYWORD_HINTS:
        for kw in keywords:
            if kw in lower:
                scores[category] += 1
    best = max(scores.items(), key=lambda item: item[1])
    if best[1] == 0:
        return TaskCategory.general
    return best[0]


def route_provider(category: TaskCategory, override: AiProvider | None = None) -> tuple[AiProvider, bool]:
    if override is not None:
        return override, True
    return ROUTING_TABLE.get(category, AiProvider.claude), False
