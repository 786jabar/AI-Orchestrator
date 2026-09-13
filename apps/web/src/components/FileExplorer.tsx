import type { FileNode } from "../api";

interface Props {
  files: FileNode[];
  activePath: string | null;
  onSelect: (path: string) => void;
}

export function FileExplorer({ files, activePath, onSelect }: Props) {
  const sorted = [...files].sort((a, b) => {
    if (a.is_directory !== b.is_directory) return a.is_directory ? -1 : 1;
    return a.path.localeCompare(b.path);
  });

  return (
    <div className="panel">
      <div className="panel-header">
        <span>Files</span>
        <span>{files.filter((f) => !f.is_directory).length}</span>
      </div>
      <div className="file-tree">
        {sorted.map((file) => (
          <button
            key={file.path}
            type="button"
            className={`file-item${file.is_directory ? " dir" : ""}${
              activePath === file.path ? " active" : ""
            }`}
            onClick={() => !file.is_directory && onSelect(file.path)}
            disabled={file.is_directory}
          >
            {file.is_directory ? "▸ " : ""}
            {file.path}
          </button>
        ))}
      </div>
    </div>
  );
}
