// src/components/FileExplorer/FileExplorer.tsx
import { useState, useEffect, useMemo } from "react";
import { 
  ChevronRight, ChevronDown, File, Folder, FolderOpen, RefreshCw, Loader2,
  FileJson, FileCode, FileText, Settings, FileKey, GitGraph, 
  Container, Zap, Database, Terminal as TerminalIcon, Globe, Lock,
  MoreVertical, Plus
} from "lucide-react";
import { useStore } from "../../lib/store";
import type { FileNode } from "../../lib/types";
import { ContextMenu } from "../ContextMenu/ContextMenu";
import { ConfirmModal } from "../ConfirmModal/ConfirmModal";
import { toast } from "react-hot-toast";
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
    if (lowerName === ".github" || lowerName === ".git") return <GitGraph size={14} className="file-item__icon git" />;
    if (lowerName === "node_modules" || lowerName === "venv" || lowerName === ".venv") return <Database size={14} className="file-item__icon modules" />;
    if (lowerName === "src" || lowerName === "app" || lowerName === "lib") return <FolderOpen size={14} className="file-item__icon src" />;
    return expanded ? <FolderOpen size={14} className="file-item__icon dir" /> : <Folder size={14} className="file-item__icon dir" />;
  }

  const ext = name.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "ts": return <FileCode size={14} className="file-item__icon ts" />;
    case "tsx": return <FileCode size={14} className="file-item__icon react" />;
    case "js": return <FileCode size={14} className="file-item__icon js" />;
    case "jsx": return <FileCode size={14} className="file-item__icon react" />;
    case "py": return <FileCode size={14} className="file-item__icon py" />;
    case "css": return <FileText size={14} className="file-item__icon css" />;
    case "json": return <FileJson size={14} className="file-item__icon json" />;
    case "md": return <FileText size={14} className="file-item__icon md" />;
    case "sh": return <TerminalIcon size={14} className="file-item__icon sh" />;
    case "yml":
    case "yaml": return <Settings size={14} className="file-item__icon yml" />;
    default: return <File size={14} className="file-item__icon" />;
  }
}

function FileItem({ node, depth }: { node: FileNode; depth: number }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const { openFile, setActiveFile, openFiles, activeFile, locks, fetchSubtree } = useStore();
  
  const isDir = node.type === "dir";
  const [fetching, setFetching] = useState(false);
  const isActive = activeFile === node.path;
  
  const aggregate = useMemo(() => {
    const status = { m: node.has_m || false, u: node.has_u || false, error: false, dirty: false };
    const walk = (n: FileNode) => {
      if (!n) return;
      if ((n.errors || 0) > 0) status.error = true;
      if (n.path && openFiles.some(f => f.path === n.path && f.isDirty)) status.dirty = true;
      if (n.children) n.children.forEach(walk);
    };
    if (isDir && node.children) node.children.forEach(walk);
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
      if (alreadyOpen) { setActiveFile(node.path); return; }

      try {
        const r = await fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(node.path)}`);
        const data = await r.json();
        openFile(node.path, data.content ?? "", getLanguage(node.path));
      } catch (err) {}
    }
  };

  return (
    <div className="file-tree-node">
      <div
        className={`file-item ${isActive ? "file-item--active" : ""}`}
        style={{ paddingLeft: 8 + depth * 12 }}
        onClick={handleClick}
        data-path={node.path}
        data-type={node.type}
        data-name={node.name}
      >
        <div className="file-item__main">
          {isDir ? (
            <span className="file-item__arrow">
              {fetching ? <Loader2 size={10} className="animate-spin" /> : (expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)}
            </span>
          ) : (
            <span className="file-item__spacer" />
          )}
          {getFileIcon(node.name, isDir, expanded)}
          <span className="file-item__name">{node.name}</span>
        </div>

        <div className="file-item__actions">
          {isDir && !expanded && (
            <div className="folder-indicators">
              {aggregate.error && <span className="indicator-dot indicator-dot--error" />}
              {aggregate.dirty && <span className="indicator-dot indicator-dot--dirty" />}
            </div>
          )}
          <button className="file-item__menu-btn" onClick={(e) => e.stopPropagation()}><MoreVertical size={12} /></button>
        </div>
      </div>
      {isDir && expanded && node.children && (
        <div className="file-item__children">
          {node.children
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
  const { fileTree, refreshFileTree, renameFile, deleteFile, addTerminalSession } = useStore();
  const [loading, setLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ path: string, name: string } | null>(null);

  const handleRefresh = async () => {
    setLoading(true);
    await refreshFileTree();
    setLoading(false);
  };

  useEffect(() => {
    if (fileTree.length === 0) handleRefresh();
  }, []);

  return (
    <div className="file-explorer">
      <div className="file-explorer__header">
        <span className="explorer-title">EXPLORER</span>
        <div className="explorer-actions">
          <button className="icon-btn"><Plus size={14} /></button>
          <button className="icon-btn" onClick={handleRefresh} title="Refresh" disabled={loading}>
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>
      <div className="file-explorer__tree">
        {fileTree
          .filter(node => node && node.name)
          .sort((a, b) => (a.type === "dir" ? -1 : 1) || (a.name || "").localeCompare(b.name || ""))
          .map((node) => (
            <FileItem key={node.path || node.name} node={node} depth={0} />
          ))}
      </div>
      
      <ConfirmModal 
        isOpen={!!confirmDelete}
        title="Permanently Delete?"
        message={`Are you sure you want to delete '${confirmDelete?.name}'? This action cannot be undone.`}
        confirmLabel="Delete"
        danger={true}
        onClose={() => setConfirmDelete(null)}
        onConfirm={() => {
          if (confirmDelete) {
            deleteFile(confirmDelete.path);
            setConfirmDelete(null);
          }
        }}
      />

      <ContextMenu 
        targetSelector=".file-item"
        items={[
          { label: 'Open', shortcut: 'Enter', action: (target) => target.click() },
          { label: 'Open to the Side', shortcut: 'Ctrl+Enter', action: (target) => target.click() },
          { label: 'Open in Integrated Terminal', action: (target) => {
            const path = target.getAttribute('data-path');
            const type = target.getAttribute('data-type');
            if (path) {
              const dir = type === 'dir' ? path : path.split('/').slice(0, -1).join('/');
              addTerminalSession(dir);
            }
          }},
          { type: 'separator' },
          { label: 'Copy Path', shortcut: 'Ctrl+Alt+C', action: (target) => {
            const path = target.getAttribute('data-path');
            if (path) {
              navigator.clipboard.writeText(path);
              toast.success("Path copied");
            }
          }},
          { label: 'Copy Relative Path', shortcut: 'Ctrl+Shift+Alt+C', action: (target) => {
            const path = target.getAttribute('data-path');
            if (path) {
              navigator.clipboard.writeText(path.replace(/^\/+/, ''));
              toast.success("Relative path copied");
            }
          }},
          { type: 'separator' },
          { label: 'Rename...', shortcut: 'F2', action: (target) => {
            const path = target.getAttribute('data-path');
            const name = target.getAttribute('data-name');
            if (path) {
              const newName = prompt("Rename to:", name || "");
              if (newName && newName !== name) {
                const newPath = path.split('/').slice(0, -1).concat(newName).join('/');
                renameFile(path, newPath);
              }
            }
          }},
          { label: 'Delete', shortcut: 'Delete', danger: true, action: (target) => {
            const path = target.getAttribute('data-path');
            const name = target.getAttribute('data-name');
            if (path && name) {
              setConfirmDelete({ path, name });
            }
          }}
        ]}
      />
    </div>
  );
}
