export type AiProvider = "claude" | "gpt" | "gemini" | "mock";
export type TaskCategory =
  | "architecture"
  | "code_generation"
  | "debugging"
  | "ui_generation"
  | "testing"
  | "general";
export type TaskStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface Project {
  id: number;
  name: string;
  description: string;
  runtime: string;
  entrypoint: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface FileNode {
  path: string;
  is_directory: boolean;
  updated_at?: string;
}

export interface FileContent {
  path: string;
  content: string;
  is_directory: boolean;
  updated_at?: string;
}

export interface Task {
  id: number;
  project_id: number;
  parent_id: number | null;
  title: string;
  prompt: string;
  category: TaskCategory;
  status: TaskStatus;
  assigned_provider: AiProvider;
  manual_override: boolean;
  result: string;
  error: string;
  target_path: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface RunResult {
  exit_code: number;
  stdout: string;
  stderr: string;
  command: string;
  duration_ms: number;
}

export interface ApiKeyOut {
  id: number;
  provider: AiProvider;
  label: string;
  masked_key: string;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  display_name: string;
}

const API = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (body: { name: string; description?: string }) =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify(body) }),
  getProject: (id: number) => request<Project>(`/api/projects/${id}`),
  listFiles: (id: number) => request<FileNode[]>(`/api/projects/${id}/files`),
  readFile: (id: number, path: string) =>
    request<FileContent>(`/api/projects/${id}/files/content?path=${encodeURIComponent(path)}`),
  saveFile: (id: number, path: string, content: string) =>
    request<FileContent>(`/api/projects/${id}/files`, {
      method: "PUT",
      body: JSON.stringify({ path, content }),
    }),
  listTasks: (id: number) => request<Task[]>(`/api/projects/${id}/tasks`),
  createTask: (
    id: number,
    body: {
      prompt: string;
      provider_override?: AiProvider | null;
      category?: TaskCategory;
      target_path?: string;
    },
  ) =>
    request<Task>(`/api/projects/${id}/tasks`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  orchestrate: (id: number, prompt: string) =>
    request<Task[]>(`/api/projects/${id}/orchestrate`, {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
  runProject: (id: number, command?: string) =>
    request<RunResult>(`/api/projects/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ command }),
    }),
  getRouting: () => request<Record<string, string>>("/api/routing"),
  getOrCreateUser: (email: string) =>
    request<User>(`/api/users/by-email?email=${encodeURIComponent(email)}`),
  listKeys: (userId: number) => request<ApiKeyOut[]>(`/api/users/${userId}/keys`),
  upsertKey: (userId: number, provider: AiProvider, api_key: string) =>
    request<ApiKeyOut>(`/api/users/${userId}/keys`, {
      method: "PUT",
      body: JSON.stringify({ provider, api_key }),
    }),
  health: () => request<{ status: string; sandbox: { status: string } }>("/health"),
};
