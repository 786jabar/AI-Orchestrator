import type { AiProvider, Task } from "../api";

interface Props {
  tasks: Task[];
  prompt: string;
  provider: AiProvider | "auto";
  busy: boolean;
  requireApproval: boolean;
  autoImprove: boolean;
  useTools: boolean;
  onPromptChange: (v: string) => void;
  onProviderChange: (v: AiProvider | "auto") => void;
  onToggleApproval: (v: boolean) => void;
  onToggleImprove: (v: boolean) => void;
  onToggleTools: (v: boolean) => void;
  onSubmit: (mode: "single" | "pipeline") => void;
}

export function ChatPanel({
  tasks,
  prompt,
  provider,
  busy,
  requireApproval,
  autoImprove,
  useTools,
  onPromptChange,
  onProviderChange,
  onToggleApproval,
  onToggleImprove,
  onToggleTools,
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
            <div className="meta">ForgeLink Advanced</div>
            <pre>
              Tool-using agents, critic scoring, auto-improve, approval-gated diffs, snapshots, and
              live SSE telemetry — all on one shared workspace.
            </pre>
          </div>
        )}
        {recent.map((task) => (
          <div className="bubble" key={task.id}>
            <div className="meta">
              <span className={`provider ${task.assigned_provider}`}>{task.assigned_provider}</span>
              <span>{task.category.replace("_", " ")}</span>
              <span>{task.status}</span>
              {typeof task.quality_score === "number" && task.quality_score > 0 ? (
                <span>score {task.quality_score.toFixed(2)}</span>
              ) : null}
            </div>
            <pre>{task.result || task.prompt}</pre>
            {task.tool_trace ? (
              <pre className="tool-trace">{task.tool_trace.slice(0, 1200)}</pre>
            ) : null}
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
        <div className="toggle-row">
          <label>
            <input
              type="checkbox"
              checked={useTools}
              onChange={(e) => onToggleTools(e.target.checked)}
            />
            Tools
          </label>
          <label>
            <input
              type="checkbox"
              checked={autoImprove}
              onChange={(e) => onToggleImprove(e.target.checked)}
            />
            Auto-improve
          </label>
          <label>
            <input
              type="checkbox"
              checked={requireApproval}
              onChange={(e) => onToggleApproval(e.target.checked)}
            />
            Approve diffs
          </label>
        </div>
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
