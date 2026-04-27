// src/components/FileExplorer/FileExplorer.tsx
import { useState, useEffect, useMemo } from "react";
import { 
  ChevronRight, ChevronDown, File, Folder, FolderOpen, RefreshCw,
  FileJson, FileCode, FileText, Settings, FileKey, GitGraph, 
  Container, Zap, Database, Terminal as TerminalIcon, Globe, Lock
} from "lucide-react";
import { useStore } from "../../lib/store";
import type { FileNode } from "../../lib/types";
import "./FileExplorer.css";

import { API_BASE } from "../../lib/config";

const LANG_MAP: Record<string, string> = {
  ts: "typescript", tsx: "typescriptreact", js: "javascript", jsx: "javascriptreact",
  py: "python", css: "css", json: "json", md: "markdown", sh: "shell",
  yml: "yaml", yaml: "yaml", html: "html", rs: "rust", go: "go",
};

function getLanguage(path: string) {
  return LANG_MAP[path.split(".").pop() ?? ""] ?? "plaintext";
}

function getFileIcon(name: string, isDir: boolean, expanded: boolean) {
  if (isDir) {
    const lowerName = name.toLowerCase();
    if (lowerName === ".github") return <GitGraph size={13} className="file-item__icon git" />;
    if (lowerName === "node_modules") return <Database size={13} className="file-item__icon modules" />;
    if (lowerName === "src") return <FolderOpen size={13} className="file-item__icon src" />;
    if (lowerName === "api" || lowerName === "core") return <Settings size={13} className="file-item__icon core" />;
    return expanded ? <FolderOpen size={13} className="file-item__icon dir" /> : <Folder size={13} className="file-item__icon dir" />;
  }

  const lowerName = name.toLowerCase();
  const ext = name.split(".").pop()?.toLowerCase();

  // Exact Match
  if (lowerName === "package.json") return <FileJson size={13} className="file-item__icon npm" />;
  if (lowerName === "tsconfig.json") return <Settings size={13} className="file-item__icon ts" />;
  if (lowerName.includes("vite.config")) return <Zap size={13} className="file-item__icon vite" />;
  if (lowerName.includes("dockerfile")) return <Container size={13} className="file-item__icon docker" />;
  if (lowerName.startsWith(".env")) return <FileKey size={13} className="file-item__icon env" />;
  if (lowerName.startsWith(".git")) return <GitGraph size={13} className="file-item__icon git" />;
  if (lowerName.includes("eslint")) return <Settings size={13} className="file-item__icon eslint" />;
  if (lowerName === "main.py") return <Zap size={13} className="file-item__icon py" />;

  // Extension Match
  switch (ext) {
    case "ts": return <FileCode size={13} className="file-item__icon ts" />;
    case "tsx": return <FileCode size={13} className="file-item__icon react" />;
    case "js": return <FileCode size={13} className="file-item__icon js" />;
    case "jsx": return <FileCode size={13} className="file-item__icon react" />;
    case "py": return <FileCode size={13} className="file-item__icon py" />;
    case "css": return <FileText size={13} className="file-item__icon css" />;
    case "json": return <FileJson size={13} className="file-item__icon json" />;
    case "md": return <FileText size={13} className="file-item__icon md" />;
    case "sh": return <TerminalIcon size={13} className="file-item__icon sh" />;
    case "yml":
    case "yaml": return <Settings size={13} className="file-item__icon yml" />;
    case "html": return <Globe size={13} className="file-item__icon html" />;
    case "sql": return <Database size={13} className="file-item__icon sql" />;
    case "rs": return <FileCode size={13} className="file-item__icon rust" />;
    case "go": return <FileCode size={13} className="file-item__icon go" />;
    default: return <File size={13} className="file-item__icon" />;
  }
}

function FileItem({ node, depth }: { node: FileNode; depth: number }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const openFile = useStore((s) => s.openFile);
  const setActiveFile = useStore((s) => s.setActiveFile);
  const openFiles = useStore((s) => s.openFiles);
  const activeFile = useStore((s) => s.activeFile);
  const locks = useStore((s) => s.locks);
  const fetchSubtree = useStore((s) => s.fetchSubtree);
  
  const isDir = node.type === "dir";
  const [fetching, setFetching] = useState(false);
  const isActive = activeFile === node.path;
  const lock = node.path ? locks[node.path] : null;
  
  // Aggregate status for collapsed folders
  const aggregate = useMemo(() => {
    const status = { 
      m: node.has_m || false, 
      u: node.has_u || false, 
      error: false, 
      dirty: false 
    };
    const walk = (n: FileNode) => {
      if (!n) return;
      if ((n.errors || 0) > 0) status.error = true;
      if (n.path && openFiles.some(f => f.path === n.path && f.isDirty)) status.dirty = true;
      if (n.children) n.children.forEach(walk);
    };
    if (isDir && node.children && node.children.length > 0) {
      node.children.forEach(walk);
    }
    return status;
  }, [node, openFiles, isDir]);

  const handleClick = async () => {
    if (isDir) {
      if (!expanded && node.path && (!node.children || node.children.length === 0)) {
        setFetching(true);
        await fetchSubtree(node.path);
        setFetching(false);
      }
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
        className={`file-item ${isActive ? "file-item--active" : ""} ${node.status ? `file-item--${node.status.toLowerCase()}` : ""} ${node.has_m ? 'file-item--m' : ''} ${node.has_u ? 'file-item--u' : ''}`}
        style={{ paddingLeft: 8 + depth * 12 }}
        onClick={handleClick}
      >
        {isDir ? (
          <span className="file-item__arrow">
            {fetching ? <Loader2 size={10} className="animate-spin" /> : (expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />)}
          </span>
        ) : (
          <span className="file-item__arrow" />
        )}
        
        {getFileIcon(node.name, isDir, expanded)}
        
        <span className="file-item__name">{node.name}</span>

        {node.status && (
          <span className={`file-status-tag tag--${node.status.toLowerCase()}`}>
            {node.status}
          </span>
        )}

        {lock && (
          <span className="file-lock-badge" title={`Locked by ${lock.locked_by}`}>
            <Lock size={10} />
          </span>
        )}

        {(node.errors ?? 0) > 0 && (
          <span className="file-error-badge">
            {node.errors}
          </span>
        )}

        {isDir && !expanded && (
          <div className="folder-indicators">
            {aggregate.error && <span className="indicator-dot indicator-dot--error" title="Errors inside" />}
            {aggregate.dirty && <span className="indicator-dot indicator-dot--dirty" title="Unsaved changes inside" />}
            {aggregate.m && <span className="indicator-dot indicator-dot--m" title="Modified files inside" />}
            {aggregate.u && <span className="indicator-dot indicator-dot--u" title="New files inside" />}
          </div>
        )}
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
  const fileTree = useStore((s) => s.fileTree);
  const refreshFileTree = useStore((s) => s.refreshFileTree);
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
