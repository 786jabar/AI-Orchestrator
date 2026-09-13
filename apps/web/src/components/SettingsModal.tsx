import { useEffect, useState } from "react";
import { api, type AiProvider, type ApiKeyOut, type User } from "../api";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PROVIDERS: AiProvider[] = ["claude", "gpt", "gemini"];

export function SettingsModal({ open, onClose }: Props) {
  const [user, setUser] = useState<User | null>(null);
  const [keys, setKeys] = useState<ApiKeyOut[]>([]);
  const [routing, setRouting] = useState<Record<string, string>>({});
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const u = await api.getOrCreateUser("demo@orchestrator.local");
        setUser(u);
        const [k, r] = await Promise.all([api.listKeys(u.id), api.getRouting()]);
        setKeys(k);
        setRouting(r);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
  }, [open]);

  if (!open) return null;

  async function save(provider: AiProvider) {
    if (!user) return;
    const value = drafts[provider]?.trim();
    if (!value) return;
    try {
      await api.upsertKey(user.id, provider, value);
      setKeys(await api.listKeys(user.id));
      setDrafts((d) => ({ ...d, [provider]: "" }));
      setMessage(`Saved ${provider} key`);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header" style={{ border: 0, padding: 0, marginBottom: "0.85rem" }}>
          <span>API keys & routing</span>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
          Bring your own keys. They are encrypted at rest. Without keys, ForgeLink uses the mock
          provider so the workspace loop still works.
        </p>
        {PROVIDERS.map((provider) => {
          const existing = keys.find((k) => k.provider === provider);
          return (
            <div className="field" key={provider}>
              <label>
                {provider.toUpperCase()} {existing ? `(${existing.masked_key})` : ""}
              </label>
              <div style={{ display: "flex", gap: "0.45rem" }}>
                <input
                  type="password"
                  placeholder={`Paste ${provider} API key`}
                  value={drafts[provider] ?? ""}
                  onChange={(e) => setDrafts((d) => ({ ...d, [provider]: e.target.value }))}
                />
                <button type="button" className="btn" onClick={() => save(provider)}>
                  Save
                </button>
              </div>
            </div>
          );
        })}
        <div className="field">
          <label>Default routing</label>
          <pre style={{ margin: 0, fontSize: "0.75rem", color: "var(--muted)" }}>
            {JSON.stringify(routing, null, 2)}
          </pre>
        </div>
        {message ? <div style={{ color: "var(--ok)", fontSize: "0.85rem" }}>{message}</div> : null}
        {error ? <div className="error">{error}</div> : null}
      </div>
    </div>
  );
}
