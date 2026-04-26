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
  const openFile = useStore((s) => s.openFile);
  const setActiveFile = useStore((s) => s.setActiveFile);
  const openFiles = useStore((s) => s.openFiles);
  const activeFile = useStore((s) => s.activeFile);
  
  const isDir = node.type === "dir";
  const isActive = activeFile === node.path;

  const handleClick = async () => {
    if (isDir) {
      setExpanded((v) => !v);
    } else if (node.path) {
      const alreadyOpen = openFiles.find(f => f.path === node.path);
      if (alreadyOpen) {
        setActiveFile(node.path);
        return;
      }

      try {
        const r = await fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(node.path)}`);
        if (!r.ok) throw new Error("Failed to read");
        const data = await r.json();
        openFile(node.path, data.content ?? "", getLanguage(node.path));
      } catch (err) {
        openFile(node.path, "// Error loading file", getLanguage(node.path));
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
      {isDir && expanded && node.children && (
        <div className="file-item__children">
          {(node.children || [])
            .filter(child => child && child.name)
            .sort((a, b) => (a.type === "dir" ? -1 : 1) || (a.name || "").localeCompare(b.name || ""))
            .map((child) => (
              <FileItem key={child.path || child.name} node={child} depth={depth + 1} />
            ))}
        </div>
      )}
    </div>
  );
}

export function FileExplorer() {
  const { fileTree, refreshFileTree } = useStore();
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    await refreshFileTree();
    setLoading(false);
  };

  useEffect(() => {
    if (fileTree.length === 0) {
      handleRefresh();
    }
  }, []);

  return (
    <div className="file-explorer">
      <div className="file-explorer__header">
        <span>EXPLORER</span>
        <button className="icon-btn" onClick={handleRefresh} title="Refresh" disabled={loading}>
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
      <div className="file-explorer__tree">
        {(fileTree || [])
          .filter(node => node && node.name)
          .sort((a, b) => (a.type === "dir" ? -1 : 1) || (a.name || "").localeCompare(b.name || ""))
          .map((node) => (
            <FileItem key={node.path || node.name} node={node} depth={0} />
          ))}
      </div>
    </div>
  );
}
