import Editor from "@monaco-editor/react";

interface Props {
  path: string | null;
  content: string;
  dirty: boolean;
  onChange: (value: string) => void;
  onSave: () => void;
  onRun?: () => void;
  runBusy?: boolean;
}

function languageFor(path: string | null): string {
  if (!path) return "plaintext";
  if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
  if (path.endsWith(".js") || path.endsWith(".jsx")) return "javascript";
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".md")) return "markdown";
  if (path.endsWith(".css")) return "css";
  if (path.endsWith(".html")) return "html";
  return "plaintext";
}

export function CodeEditor({
  path,
  content,
  dirty,
  onChange,
  onSave,
  onRun,
  runBusy,
}: Props) {
  return (
    <div className="editor-wrap">
      <div className="editor-toolbar">
        <span className="path">{path ?? "No file selected"}{dirty ? " •" : ""}</span>
        <button type="button" className="btn" onClick={onSave} disabled={!path || !dirty}>
          Save
        </button>
        {onRun ? (
          <button type="button" className="btn btn-primary" onClick={onRun} disabled={runBusy}>
            {runBusy ? "Running…" : "Run sandbox"}
          </button>
        ) : null}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <Editor
          height="100%"
          theme="vs-dark"
          path={path ?? "untitled"}
          language={languageFor(path)}
          value={content}
          onChange={(v) => onChange(v ?? "")}
          options={{
            fontFamily: "IBM Plex Mono, monospace",
            fontSize: 13,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 12 },
          }}
        />
      </div>
    </div>
  );
}
