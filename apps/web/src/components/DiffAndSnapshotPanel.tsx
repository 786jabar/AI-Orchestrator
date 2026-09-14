import type { PendingChange, Snapshot } from "../api";

interface Props {
  changes: PendingChange[];
  snapshots: Snapshot[];
  onApply: (id: number) => void;
  onReject: (id: number) => void;
  onSnapshot: () => void;
  onRestore: (id: number) => void;
}

export function DiffAndSnapshotPanel({
  changes,
  snapshots,
  onApply,
  onReject,
  onSnapshot,
  onRestore,
}: Props) {
  return (
    <div className="adv-panel">
      <div className="panel-header">
        <span>Diffs & snapshots</span>
        <button type="button" className="btn" onClick={onSnapshot}>
          Snapshot
        </button>
      </div>
      <div className="adv-body">
        <div className="adv-section-title">Pending diffs</div>
        {changes.length === 0 && <div className="pipe-sub">No approval-gated changes.</div>}
        {changes.map((c) => (
          <div className="diff-card" key={c.id}>
            <div className="pipe-title">
              {c.action} · {c.path}
            </div>
            <pre className="diff-pre">{c.diff_text || "(binary/empty diff)"}</pre>
            <div className="chat-actions">
              <button type="button" className="btn btn-primary" onClick={() => onApply(c.id)}>
                Apply
              </button>
              <button type="button" className="btn" onClick={() => onReject(c.id)}>
                Reject
              </button>
            </div>
          </div>
        ))}

        <div className="adv-section-title" style={{ marginTop: "0.85rem" }}>
          Snapshots
        </div>
        {snapshots.slice(0, 6).map((s) => (
          <div className="snap-row" key={s.id}>
            <div>
              <div className="pipe-title">{s.label}</div>
              <div className="pipe-sub">
                {s.source} · {s.file_count} files
              </div>
            </div>
            <button type="button" className="btn" onClick={() => onRestore(s.id)}>
              Restore
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
