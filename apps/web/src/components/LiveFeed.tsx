import type { LiveEvent } from "../api";

interface Props {
  events: LiveEvent[];
}

export function LiveFeed({ events }: Props) {
  const recent = [...events].slice(-12).reverse();
  return (
    <div className="live-feed">
      <div className="panel-header">
        <span>Live agent stream</span>
        <span>{events.length}</span>
      </div>
      <div className="live-list">
        {recent.length === 0 && <div className="pipe-sub">Waiting for agent events…</div>}
        {recent.map((ev, idx) => (
          <div className="live-row" key={`${ev.at}-${idx}`}>
            <span className="live-type">{ev.type}</span>
            <span className="pipe-sub">
              {Object.entries(ev.payload || {})
                .slice(0, 3)
                .map(([k, v]) => `${k}=${String(v)}`)
                .join(" · ")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
