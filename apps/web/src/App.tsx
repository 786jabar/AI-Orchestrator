import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type AiProvider,
  type FileNode,
  type Project,
  type RunResult,
  type Task,
} from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { CodeEditor } from "./components/CodeEditor";
import { FileExplorer } from "./components/FileExplorer";
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
  const [newName, setNewName] = useState("Demo App");
  const [newDesc, setNewDesc] = useState("Shared Node.js workspace for multi-AI collaboration");

  const dirty = content !== savedContent;
  const previewHtml = useMemo(
    () => (runResult ? extractHtml(runResult.stdout) : null),
    [runResult],
  );

  const refreshProjects = useCallback(async () => {
    setProjects(await api.listProjects());
  }, []);

  const refreshWorkspace = useCallback(async (id: number, preferPath?: string | null) => {
    const [fileList, taskList, proj] = await Promise.all([
      api.listFiles(id),
      api.listTasks(id),
      api.getProject(id),
    ]);
    setProject(proj);
    setFiles(fileList);
    setTasks(taskList);
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
  }, [activePath]);

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

  async function createProject() {
    setError("");
    try {
      const created = await api.createProject({ name: newName, description: newDesc });
      await refreshProjects();
      await refreshWorkspace(created.id, "index.js");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function openProject(id: number) {
    setError("");
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
      if (mode === "pipeline") {
        await api.orchestrate(project.id, prompt.trim());
      } else {
        await api.createTask(project.id, {
          prompt: prompt.trim(),
          provider_override: provider === "auto" ? null : provider,
          target_path: activePath ?? undefined,
        });
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
      if (dirty && activePath) {
        await saveFile();
      }
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
        <a className="brand" href="/" onClick={(e) => { e.preventDefault(); setProject(null); }}>
          <span className="brand-mark">ForgeLink</span>
          <span className="brand-sub">AI Orchestrator Platform</span>
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
            <div className="eyebrow">Multi-model software workspace</div>
            <h1>One shared project. Many AIs. Coordinated builds.</h1>
            <p>
              ForgeLink routes architecture, code, UI, and tests across Claude, GPT, and Gemini —
              then merges every edit into a single Node.js workspace you can run in an isolated
              sandbox.
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
                <button key={p.id} type="button" className="project-row" onClick={() => openProject(p.id)}>
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
        <main className="workspace">
          <FileExplorer files={files} activePath={activePath} onSelect={selectFile} />
          <CodeEditor
            path={activePath}
            content={content}
            dirty={dirty}
            onChange={setContent}
            onSave={saveFile}
          />
          <div className="side-stack">
            <ChatPanel
              tasks={tasks}
              prompt={prompt}
              provider={provider}
              busy={busy}
              onPromptChange={setPrompt}
              onProviderChange={setProvider}
              onSubmit={submitTask}
            />
            <PipelineView tasks={tasks} />
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
