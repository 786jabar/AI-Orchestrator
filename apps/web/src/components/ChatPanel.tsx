import type { AiProvider, Task } from "../api";

interface Props {
  tasks: Task[];
  prompt: string;
  provider: AiProvider | "auto";
  busy: boolean;
  onPromptChange: (v: string) => void;
  onProviderChange: (v: AiProvider | "auto") => void;
  onSubmit: (mode: "single" | "pipeline") => void;
}

export function ChatPanel({
  tasks,
  prompt,
  provider,
  busy,
  onPromptChange,
  onProviderChange,
  onSubmit,
}: Props) {
  const recent = [...tasks].reverse().slice(0, 8);

  return (
    <div className="chat">
      <div className="panel-header">
        <span>Task</span>
        <span>{busy ? "running…" : "ready"}</span>
      </div>
      <div className="chat-log">
        {recent.length === 0 && (
          <div className="bubble">
            <div className="meta">ForgeLink</div>
            <pre>
              Describe what to build. Tasks are classified and routed to Claude, GPT, or Gemini.
              Without API keys, a mock provider still exercises the full loop.
            </pre>
          </div>
        )}
        {recent.map((task) => (
          <div className="bubble" key={task.id}>
            <div className="meta">
              <span className={`provider ${task.assigned_provider}`}>{task.assigned_provider}</span>
              <span>{task.category.replace("_", " ")}</span>
              <span>{task.status}</span>
            </div>
            <pre>{task.result || task.prompt}</pre>
            {task.error ? <pre className="error">{task.error}</pre> : null}
          </div>
        ))}
      </div>
      <div className="chat-compose">
        <textarea
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          placeholder="Build a tiny HTTP status page with a refresh button…"
        />
        <div className="chat-actions">
          <select
            value={provider}
            onChange={(e) => onProviderChange(e.target.value as AiProvider | "auto")}
            aria-label="AI provider"
          >
            <option value="auto">Auto route</option>
            <option value="claude">Claude</option>
            <option value="gpt">GPT</option>
            <option value="gemini">Gemini</option>
            <option value="mock">Mock</option>
          </select>
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy || !prompt.trim()}
            onClick={() => onSubmit("single")}
          >
            Run task
          </button>
          <button
            type="button"
            className="btn"
            disabled={busy || !prompt.trim()}
            onClick={() => onSubmit("pipeline")}
          >
            Full pipeline
          </button>
        </div>
      </div>
    </div>
  );
}
