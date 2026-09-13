import type { RunResult } from "../api";

interface Props {
  result: RunResult | null;
  previewHtml: string | null;
  onRun: () => void;
  busy: boolean;
}

export function PreviewPane({ result, previewHtml, onRun, busy }: Props) {
  return (
    <div className="bottom-pane">
      <div className="preview">
        <div className="panel-header">
          <span>Preview</span>
          <button type="button" className="btn" onClick={onRun} disabled={busy}>
            {busy ? "Running…" : "Run sandbox"}
          </button>
        </div>
        {previewHtml ? (
          <iframe className="preview-frame" title="preview" srcDoc={previewHtml} sandbox="" />
        ) : (
          <div style={{ padding: "0.85rem", color: "var(--muted)", fontSize: "0.85rem" }}>
            Run the sandbox to capture stdout. HTML responses render here.
          </div>
        )}
      </div>
      <div className="console">
        <div className="panel-header">
          <span>Sandbox output</span>
          <span>{result ? `${result.duration_ms}ms · exit ${result.exit_code}` : "idle"}</span>
        </div>
        <pre>
          {result
            ? `$ ${result.command}\n${result.stdout}${result.stderr ? `\n[stderr]\n${result.stderr}` : ""}`
            : "No runs yet."}
        </pre>
      </div>
    </div>
  );
}
