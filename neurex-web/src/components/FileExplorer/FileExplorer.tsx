// src/components/FileExplorer/FileExplorer.tsx
import { useState, useEffect } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, RefreshCw } from "lucide-react";
import { useStore } from "../../lib/store";
import type { FileNode } from "../../lib/types";
import "./FileExplorer.css";

const API_BASE = "http://localhost:8000";

const LANG_MAP: Record<string, string> = {
  ts: "typescript", tsx: "typescriptreact", js: "javascript", jsx: "javascriptreact",
  py: "python", css: "css", json: "json", md: "markdown", sh: "shell",
  yml: "yaml", yaml: "yaml", html: "html", rs: "rust", go: "go",
};

function getLanguage(path: string) {
  return LANG_MAP[path.split(".").pop() ?? ""] ?? "plaintext";
}

function FileItem({ node, depth }: { node: FileNode; depth: number }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const { openFile, activeFile } = useStore();
  const isDir = node.type === "dir";
  const isActive = activeFile === node.path;

  const handleClick = async () => {
    if (isDir) {
      setExpanded((v) => !v);
      } else if (node.path) {
      try {
        const r = await fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(node.path)}`);
        const data = await r.json();
        openFile(node.path, data.content ?? "", getLanguage(node.path));
      } catch {

        openFile(node.path, "// Could not load file", getLanguage(node.path));
      }
    }
  };

  return (
    <div>
      <div
        className={`file-item ${isActive ? "file-item--active" : ""}`}
        style={{ paddingLeft: 8 + depth * 12 }}
        onClick={handleClick}
      >
        {isDir ? (
          <>
            <span className="file-item__arrow">
              {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </span>
            {expanded ? <FolderOpen size={13} className="file-item__icon dir" /> : <Folder size={13} className="file-item__icon dir" />}
          </>
        ) : (
          <>
            <span className="file-item__arrow" />
            <File size={13} className="file-item__icon" />
          </>
        )}
        <span className="file-item__name">{node.name}</span>
      </div>
      {isDir && expanded && node.children?.map((child) => (
        <FileItem key={child.path ?? child.name} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export function FileExplorer() {
  const [tree, setTree] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTree = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/files/tree`);
      const data = await r.json();
      setTree(Array.isArray(data) ? data : [data]);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { loadTree(); }, []);

  return (
    <div className="file-explorer">
      <div className="file-explorer__header">
        <span>EXPLORER</span>
        <button className="icon-btn" onClick={loadTree} title="Refresh">
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
      <div className="file-explorer__tree">
        {tree.map((node) => (
          <FileItem key={node.path ?? node.name} node={node} depth={0} />
        ))}
      </div>
    </div>
  );
}
