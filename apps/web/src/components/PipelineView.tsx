import type { Task } from "../api";

interface Props {
  tasks: Task[];
}

export function PipelineView({ tasks }: Props) {
  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div className="panel-header">
        <span>Pipeline</span>
        <span>{tasks.length} steps</span>
      </div>
      <div className="pipeline">
        {tasks.length === 0 && <div className="pipe-sub">No tasks yet.</div>}
        {tasks.map((task) => (
          <div className="pipe-row" data-status={task.status} key={task.id}>
            <span className="pipe-dot" />
            <div>
              <div className="pipe-title">{task.title}</div>
              <div className="pipe-sub">
                {task.category.replaceAll("_", " ")} · {task.status}
                {task.manual_override ? " · override" : ""}
              </div>
            </div>
            <span className={`provider ${task.assigned_provider}`}>{task.assigned_provider}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
