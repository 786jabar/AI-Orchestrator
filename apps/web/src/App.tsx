import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type AiProvider,
  type FileNode,
  type LiveEvent,
  type PendingChange,
  type Project,
  type RunResult,
  type Snapshot,
  type Task,
} from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { CodeEditor } from "./components/CodeEditor";
import { DiffAndSnapshotPanel } from "./components/DiffAndSnapshotPanel";
import { FileExplorer } from "./components/FileExplorer";
import { LiveFeed } from "./components/LiveFeed";
import { PipelineView } from "./components/PipelineView";
import { PreviewPane } from "./components/PreviewPane";
import { SettingsModal } from "./components/SettingsModal";

function extractHtml(stdout: string): string | null {
  const start = stdout.indexOf("<!doctype html>");
  const alt = stdout.indexOf("<html");
  const idx = start >= 0 ? start : alt;
  if (idx < 0) return null;
  return stdout.slice(idx);
}

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [activePath, setActivePath] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [savedContent, setSavedContent] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState<AiProvider | "auto">("auto");
  const [busy, setBusy] = useState(false);
  const [runBusy, setRunBusy] = useState(false);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [error, setError] = useState("");
  const [health, setHealth] = useState("checking");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [newName, setNewName] = useState("Advanced Demo");
  const [newDesc, setNewDesc] = useState(
    "Multi-agent workspace with tools, critic scoring, diffs, and snapshots",
  );
  const [requireApproval, setRequireApproval] = useState(false);
  const [autoImprove, setAutoImprove] = useState(true);
  const [useTools, setUseTools] = useState(true);
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [changes, setChanges] = useState<PendingChange[]>([]);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);

  const dirty = content !== savedContent;
  const previewHtml = useMemo(
    () => (runResult ? extractHtml(runResult.stdout) : null),
    [runResult],
  );

  const refreshProjects = useCallback(async () => {
    setProjects(await api.listProjects());
  }, []);

  const refreshAdvanced = useCallback(async (id: number) => {
    const [c, s] = await Promise.all([api.listChanges(id), api.listSnapshots(id)]);
    setChanges(c);
    setSnapshots(s);
  }, []);

  const refreshWorkspace = useCallback(
    async (id: number, preferPath?: string | null) => {
      const [fileList, taskList, proj] = await Promise.all([
        api.listFiles(id),
        api.listTasks(id),
        api.getProject(id),
      ]);
      setProject(proj);
      setFiles(fileList);
      setTasks(taskList);
      await refreshAdvanced(id);
      const nextPath =
        preferPath ??
        activePath ??
        fileList.find((f) => !f.is_directory && f.path === "index.js")?.path ??
        fileList.find((f) => !f.is_directory)?.path ??
        null;
      if (nextPath) {
        const file = await api.readFile(id, nextPath);
        setActivePath(nextPath);
        setContent(file.content);
        setSavedContent(file.content);
      }
    },
    [activePath, refreshAdvanced],
  );

  useEffect(() => {
    (async () => {
      try {
        const h = await api.health();
        const sandboxOk = (h.sandbox as { status?: string } | undefined)?.status === "ok";
        setHealth(h.status === "ok" && sandboxOk ? "ok" : "degraded");
        await refreshProjects();
      } catch {
        setHealth("down");
      }
    })();
  }, [refreshProjects]);

  // Live SSE telemetry
  useEffect(() => {
    if (!project) return;
    const es = new EventSource(api.eventsUrl(project.id));
    const onAny = (type: string) => (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data) as LiveEvent;
        setEvents((prev) => [...prev.slice(-80), { ...data, type: data.type || type }]);
        if (
          type === "task_completed" ||
          type === "diffs_pending" ||
          type === "diff_applied" ||
          type === "diff_rejected" ||
          type === "auto_improve"
        ) {
          void refreshWorkspace(project.id, activePath);
        }
      } catch {
        /* ignore malformed */
      }
    };
    const types = [
      "subscribed",
      "task_queued",
      "task_running",
      "agent_round",
      "task_completed",
      "task_failed",
      "critic_started",
      "critic_finished",
      "diffs_pending",
      "diff_applied",
      "diff_rejected",
      "auto_improve",
      "sandbox_verified",
    ];
    for (const t of types) es.addEventListener(t, onAny(t));
    es.onmessage = onAny("message");
    return () => es.close();
  }, [project, activePath, refreshWorkspace]);

  async function createProject() {
    setError("");
    try {
      const created = await api.createProject({ name: newName, description: newDesc });
      setEvents([]);
      await refreshProjects();
      await refreshWorkspace(created.id, "index.js");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function openProject(id: number) {
    setError("");
    setEvents([]);
    try {
      await refreshWorkspace(id, "index.js");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function selectFile(path: string) {
    if (!project) return;
    if (dirty && !confirm("Discard unsaved changes?")) return;
    const file = await api.readFile(project.id, path);
    setActivePath(path);
    setContent(file.content);
    setSavedContent(file.content);
  }

  async function saveFile() {
    if (!project || !activePath) return;
    const saved = await api.saveFile(project.id, activePath, content);
    setSavedContent(saved.content);
  }

  async function submitTask(mode: "single" | "pipeline") {
    if (!project || !prompt.trim()) return;
    setBusy(true);
    setError("");
    try {
      const body = {
        prompt: prompt.trim(),
        provider_override: provider === "auto" ? null : provider,
        target_path: activePath ?? undefined,
        require_approval: requireApproval,
        use_tools: useTools,
        auto_improve: autoImprove,
      };
      if (mode === "pipeline") {
        await api.orchestrate(project.id, body);
      } else {
        await api.createTask(project.id, body);
      }
      setPrompt("");
      await refreshWorkspace(project.id, activePath);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runSandbox() {
    if (!project) return;
    setRunBusy(true);
    setError("");
    try {
      if (dirty && activePath) await saveFile();
      const result = await api.runProject(project.id);
      setRunResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="/"
          onClick={(e) => {
            e.preventDefault();
            setProject(null);
          }}
        >
          <span className="brand-mark">ForgeLink</span>
          <span className="brand-sub">Advanced AI Orchestrator</span>
        </a>
        <div className="topbar-actions">
          <span className="status-pill">API {health}</span>
          {project ? (
            <button type="button" className="btn btn-ghost" onClick={() => setProject(null)}>
              Projects
            </button>
          ) : null}
          <button type="button" className="btn" onClick={() => setSettingsOpen(true)}>
            Keys
          </button>
        </div>
      </header>

      {!project ? (
        <main className="home">
          <section className="home-copy">
            <div className="eyebrow">Multi-model software factory</div>
            <h1>ForgeLink routes, critiques, and improves code across agents.</h1>
            <p>
              Tool loops, critic scoring, auto-improve, approval-gated diffs, project memory,
              snapshots, and live SSE telemetry — collaborating on one Node.js workspace.
            </p>
          </section>
          <section className="home-panel">
            <div className="field">
              <label htmlFor="name">New project</label>
              <input id="name" value={newName} onChange={(e) => setNewName(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="desc">Description</label>
              <textarea id="desc" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
            </div>
            <button type="button" className="btn btn-primary" onClick={createProject}>
              Create workspace
            </button>
            {error ? <p className="error">{error}</p> : null}
            <div className="project-list">
              {projects.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="project-row"
                  onClick={() => openProject(p.id)}
                >
                  <div>
                    <strong>{p.name}</strong>
                    <div style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{p.description}</div>
                  </div>
                  <span className="status-pill">{p.runtime}</span>
                </button>
              ))}
            </div>
          </section>
        </main>
      ) : (
        <main className="workspace workspace-advanced">
          <FileExplorer files={files} activePath={activePath} onSelect={selectFile} />
          <CodeEditor
            path={activePath}
            content={content}
            dirty={dirty}
            onChange={setContent}
            onSave={saveFile}
            onRun={runSandbox}
            runBusy={runBusy}
          />
          <div className="side-stack">
            <ChatPanel
              tasks={tasks}
              prompt={prompt}
              provider={provider}
              busy={busy}
              requireApproval={requireApproval}
              autoImprove={autoImprove}
              useTools={useTools}
              onPromptChange={setPrompt}
              onProviderChange={setProvider}
              onToggleApproval={setRequireApproval}
              onToggleImprove={setAutoImprove}
              onToggleTools={setUseTools}
              onSubmit={submitTask}
            />
            <PipelineView tasks={tasks} />
            <LiveFeed events={events} />
            <DiffAndSnapshotPanel
              changes={changes}
              snapshots={snapshots}
              onApply={async (id) => {
                await api.applyChange(project.id, id);
                await refreshWorkspace(project.id, activePath);
              }}
              onReject={async (id) => {
                await api.rejectChange(project.id, id);
                await refreshAdvanced(project.id);
              }}
              onSnapshot={async () => {
                await api.createSnapshot(project.id, `manual-${new Date().toISOString()}`);
                await refreshAdvanced(project.id);
              }}
              onRestore={async (id) => {
                if (!confirm("Restore snapshot? A safety snapshot of the current tree is saved first."))
                  return;
                await api.restoreSnapshot(project.id, id);
                await refreshWorkspace(project.id, activePath);
              }}
            />
          </div>
          <PreviewPane
            result={runResult}
            previewHtml={previewHtml}
            onRun={runSandbox}
            busy={runBusy}
          />
          {error ? (
            <div style={{ gridColumn: "1 / -1", padding: "0.5rem 1rem" }} className="error">
              {error}
            </div>
          ) : null}
        </main>
      )}

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
