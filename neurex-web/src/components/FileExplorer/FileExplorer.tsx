// src/components/FileExplorer/FileExplorer.tsx
import React, { useState, useEffect, useMemo, useRef } from "react";
import { 
  ChevronRight, ChevronDown, File, Folder, FolderOpen, RefreshCw, Loader2,
  FileJson, FileCode, FileText, Settings, GitGraph, 
  Database, Terminal as TerminalIcon, FilePlus, FolderPlus, FoldVertical, X,
  Braces, Square
} from "lucide-react";
import { useStore } from "../../lib/store";
import type { FileNode } from "../../lib/types";
import { ContextMenu } from "../ContextMenu/ContextMenu";
import { ConfirmModal } from "../ConfirmModal/ConfirmModal";
import { InputDialog } from "../Modals/InputDialog";
import { FolderBrowser } from "../Modals/FolderBrowser";
import { toast } from "react-hot-toast";
import "./FileExplorer.css";

import { api } from "../../lib/api";

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
    if (lowerName === ".github" || lowerName === ".git") return <GitGraph size={12} className="file-item__icon git" />;
    if (lowerName === "node_modules" || lowerName === "venv" || lowerName === ".venv") return <Database size={12} className="file-item__icon modules" />;
    if (lowerName === "src" || lowerName === "app" || lowerName === "lib") return <FolderOpen size={12} className="file-item__icon src" />;
    return expanded ? <FolderOpen size={12} className="file-item__icon dir" /> : <Folder size={12} className="file-item__icon dir" />;
  }

  const ext = name.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "ts": return <FileCode size={12} className="file-item__icon ts" />;
    case "tsx": return <FileCode size={12} className="file-item__icon react" />;
    case "js": return <FileCode size={12} className="file-item__icon js" />;
    case "jsx": return <FileCode size={12} className="file-item__icon react" />;
    case "py": return <FileCode size={12} className="file-item__icon py" />;
    case "css": return <FileText size={12} className="file-item__icon css" />;
    case "json": return <FileJson size={12} className="file-item__icon json" />;
    case "md": return <FileText size={12} className="file-item__icon md" />;
    case "sh": return <TerminalIcon size={12} className="file-item__icon sh" />;
    case "yml":
    case "yaml": return <Settings size={12} className="file-item__icon yml" />;
    default: return <File size={12} className="file-item__icon" />;
  }
}

const FileItem = React.memo(function FileItem({ node, depth }: { 
  node: FileNode; 
  depth: number;
}) {
  const { 
    openFile, setActiveFile, openFiles, activeFile, 
    fetchSubtree, expandedFolders, collapsedFolders, toggleFolder 
  } = useStore();
  const collapseSignal = useStore(s => s.collapseSignal);
  const expanded = useMemo(() => {
    if (node.type !== "dir") return false;
    if (node.path && collapsedFolders.has(node.path)) return false;
    if (node.path && expandedFolders.has(node.path)) return true;
    return depth < 1; 
  }, [node.path, node.type, depth, expandedFolders, collapsedFolders, collapseSignal]);

  const isDir = node.type === "dir";
  const [fetching, setFetching] = useState(false);
  const isActive = activeFile === node.path;

  useEffect(() => {
    if (expanded && isDir && node.path && (node.children === null || node.children === undefined)) {
      const delay = Math.random() * 500; 
      const timer = setTimeout(() => {
        if (expanded && isDir && node.path) {
          fetchSubtree(node.path);
        }
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [expanded, isDir, node.path, node.children, fetchSubtree]);

  const aggregate = useMemo(() => {
    const status = { 
      m: node.status === "M" || node.has_m || false, 
      u: node.status === "U" || node.has_u || false, 
      m_count: 0,
      u_count: 0,
      error: false, 
      dirty: false 
    };
    const walk = (n: FileNode) => {
      const isOpen = openFiles.find(f => f.path === n.path);
      if (isOpen?.isDirty) status.dirty = true;
      if ((n.errors || 0) > 0) status.error = true;
      if (n.children) n.children.forEach(walk);
    };
    if (isDir && node.children) node.children.forEach(walk);
    return status;
  }, [node, openFiles, isDir]);

  const handleDoubleClick = async (e: React.MouseEvent) => {
    if (isDir) return;
    e.stopPropagation();
    try {
      const data = await api.get<{ content: string }>(`/api/files/read?path=${encodeURIComponent(node.path!)}`);
      openFile(node.path!, data.content ?? "", getLanguage(node.path!), false);
    } catch (err) {}
  };

  const handleClick = async (e: React.MouseEvent) => {
    if (isDir) {
      if (!expanded && node.path && (!node.children || node.children.length === 0)) {
        setFetching(true);
        await fetchSubtree(node.path);
        setFetching(false);
      }
      if (node.path) toggleFolder(node.path);
    } else if (node.path) {
      const alreadyOpen = openFiles.find(f => f.path === node.path);
      if (alreadyOpen) { 
        setActiveFile(node.path); 
        return; 
      }

      try {
        const data = await api.get<{ content: string }>(`/api/files/read?path=${encodeURIComponent(node.path)}`);
        openFile(node.path, data.content ?? "", getLanguage(node.path), true);
      } catch (err) {}
    }
  };

  return (
    <div className="file-tree-node">
        <div
          className={`file-item ${isActive ? "file-item--active" : ""} status-${node.status || 'none'} ${(node.errors ?? 0) > 0 ? 'status-error' : ''} ${node.has_m ? 'has-m' : ''} ${node.has_u ? 'has-u' : ''}`}
          style={{ paddingLeft: 8 + depth * 12 }}
          onClick={handleClick}
          onDoubleClick={handleDoubleClick}
          data-path={node.path}
          data-type={node.type}
          data-name={node.name}
          data-depth={depth}
        >
          {Array.from({ length: depth }).map((_, i) => (
            <div 
              key={i} 
              className="indent-guide" 
              style={{ left: 12 + i * 12 }} 
            />
          ))}
      <div className="file-item__main">
        {isDir ? (
          <span className="file-item__arrow">
            {fetching ? <Loader2 size={10} className="animate-spin" /> : (expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />)}
          </span>
        ) : (
          <span className="file-item__spacer" />
        )}
        {getFileIcon(node.name, isDir, expanded)}
        <span className="file-item__name">{node.name}</span>
      </div>

      <div className="file-item__status">
        {!isDir && node.status === "M" && <span className="git-indicator git-indicator--modified" title={`Modified: ${node.path}`}>M</span>}
        {!isDir && node.status === "U" && <span className="git-indicator git-indicator--untracked" title={`Untracked: ${node.path}`}>U</span>}
        
        {aggregate.dirty && <span className="indicator-dot indicator-dot--dirty" title={`Unsaved changes in: ${node.path}`} />}
        {(node.errors ?? 0) > 0 && (
          <span className="problem-badge" title={`${node.errors} problems in: ${node.path}`}>
            {node.errors}
          </span>
        )}

        {isDir && (node.has_m || node.has_u) && (
          <div className="folder-indicators">
            {node.has_m && <div className="indicator-bubble indicator-bubble--modified" title={`Modified contents in: ${node.path}`}>M</div>}
            {node.has_u && <div className="indicator-bubble indicator-bubble--untracked" title={`Untracked contents in: ${node.path}`}>U</div>}
          </div>
        )}
      </div>

      </div>
    {isDir && expanded && node.children && (
      <div className="file-item__children">
        {node.children?.filter(child => child && child.name)
          .sort((a, b) => (a.type === "dir" ? -1 : 1) || (a.name || "").localeCompare(b.name || ""))
          .map((child) => (
            <FileItem 
              key={child.path || child.name} 
              node={child} 
              depth={depth + 1} 
            />
          ))}
      </div>
    )}
  </div>
  );
});

export function FileExplorer() {
  const fileTree = useStore(s => s.fileTree);
  const refreshFileTree = useStore(s => s.refreshFileTree);
  const setWorkspace = useStore(s => s.setWorkspace);
  const createFile = useStore(s => s.createFile);
  const createFolder = useStore(s => s.createFolder);
  const collapseAllFolders = useStore(s => s.collapseAllFolders);
  const deleteFile = useStore(s => s.deleteFile);
  const renameFile = useStore(s => s.renameFile);
  const addTerminalSession = useStore(s => s.addTerminalSession);
  const closeWorkspace = useStore(s => s.closeWorkspace);
  const activeFile = useStore(s => s.activeFile);
  const openFiles = useStore(s => s.openFiles);
  const toggleFolder = useStore(s => s.toggleFolder);
  const setPendingJump = useStore(s => s.setPendingJump);

  const [loading, setLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ path: string, name: string } | null>(null);
  const [inputDialog, setInputDialog] = useState<{ type: 'file' | 'folder', dir: string } | null>(null);
  const [folderBrowserOpen, setFolderBrowserOpen] = useState(false);
  const [sections, setSections] = useState({ open: true, workspace: true, outline: true });

  useEffect(() => {
    if (activeFile) {
      const parts = activeFile.split('/');
      let currentPath = "";
      for (let i = 0; i < parts.length - 1; i++) {
        currentPath += (currentPath ? "/" : "") + parts[i];
        toggleFolder(currentPath, true);
      }
    }
  }, [activeFile, toggleFolder]);

  const handleRefresh = async () => {
    setLoading(true);
    const tid = toast.loading("Refreshing workspace...");
    try {
      await refreshFileTree();
      toast.success("Explorer synchronized", { id: tid });
    } catch (err) {
      toast.error("Sync failed", { id: tid });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFolder = () => setFolderBrowserOpen(true);
  const handleCreateFile = (dir: string = "") => setInputDialog({ type: 'file', dir });
  const handleCreateFolder = (dir: string = "") => setInputDialog({ type: 'folder', dir });

  const activeContent = useMemo(() => {
    return openFiles.find(f => f.path === activeFile)?.content || "";
  }, [activeFile, openFiles]);

  const symbols = useMemo(() => {
    if (!activeContent) return [];
    const lines = activeContent.split("\n");
    const results: { name: string; line: number; type: "func" | "class" | "const" }[] = [];
    
    // Simple regex for TS/JS/Python
    const funcRegex = /^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)/;
    const arrowFuncRegex = /^(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>/;
    const classRegex = /^(?:export\s+)?class\s+([a-zA-Z0-9_]+)/;
    const pyDefRegex = /^\s*def\s+([a-zA-Z0-9_]+)\s*\(/;
    const pyClassRegex = /^\s*class\s+([a-zA-Z0-9_]+)\s*(?:\(|:)/;

    lines.forEach((line, i) => {
      let match;
      if ((match = line.match(funcRegex)) || (match = line.match(pyDefRegex))) {
        results.push({ name: match[1], line: i + 1, type: "func" });
      } else if ((match = line.match(classRegex)) || (match = line.match(pyClassRegex))) {
        results.push({ name: match[1], line: i + 1, type: "class" });
      } else if ((match = line.match(arrowFuncRegex))) {
        results.push({ name: match[1], line: i + 1, type: "func" });
      }
    });
    return results;
  }, [activeContent]);

  return (
    <div className="file-explorer">
      <div className="sidebar-section">
        <div className="sidebar-section__header" onClick={() => setSections(s => ({ ...s, open: !s.open }))}>
          {sections.open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span>OPEN EDITORS</span>
        </div>
        {sections.open && (
          <div className="sidebar-section__content open-editors-list">
            {openFiles.map(f => (
              <div 
                key={f.path} 
                className={`open-editor-item ${f.path === activeFile ? 'active' : ''}`}
                onClick={() => useStore.getState().setActiveFile(f.path)}
              >
                <FileCode size={12} className="text-muted" />
                <span>{f.path.split('/').pop()}</span>
                <X 
                  size={12} 
                  className="close-icon" 
                  onClick={(e) => { e.stopPropagation(); useStore.getState().closeFile(f.path); }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section__header explorer-header">
          <div className="sidebar-section__header-left" onClick={() => setSections(s => ({ ...s, workspace: !s.workspace }))}>
            {sections.workspace ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>NEUREX</span>
          </div>
          <div className="explorer-actions">
            <button className="icon-btn" onClick={(e) => { e.stopPropagation(); handleCreateFile(""); }} title="New File"><FilePlus size={14} /></button>
            <button className="icon-btn" onClick={(e) => { e.stopPropagation(); handleCreateFolder(""); }} title="New Folder"><FolderPlus size={14} /></button>
            <button className="icon-btn" onClick={(e) => { e.stopPropagation(); handleRefresh(); }} title="Refresh"><RefreshCw size={12} /></button>
            <button className="icon-btn" onClick={(e) => { e.stopPropagation(); collapseAllFolders(); }} title="Collapse All"><FoldVertical size={14} /></button>
          </div>
        </div>
        {sections.workspace && (
          <div className="sidebar-section__content">
            {fileTree.length > 0 ? (
              fileTree
                .filter(node => node && node.name)
                .sort((a, b) => (a.type === "dir" ? -1 : 1) || (a.name || "").localeCompare(b.name || ""))
                .map((node) => (
                  <FileItem 
                    key={node.path || node.name} 
                    node={node} 
                    depth={0} 
                  />
                ))
            ) : (
              <div className="explorer-empty-state">
                <button className="btn btn--purple btn--full" onClick={handleOpenFolder}>Open Folder</button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section__header" onClick={() => setSections(s => ({ ...s, outline: !s.outline }))}>
          {sections.outline ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span>OUTLINE</span>
        </div>
        {sections.outline && symbols.length > 0 && (
          <div className="sidebar-section__content outline-list">
            {symbols.map((sym, i) => (
              <div key={i} className="outline-item" onClick={() => setPendingJump(activeFile!, sym.line)}>
                {sym.type === "class" ? <Braces size={12} className="text-purple" /> : <Square size={10} className="text-cyan" />}
                <span>{sym.name}</span>
                <span className="outline-line">:{sym.line}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <FolderBrowser 
        isOpen={folderBrowserOpen}
        onClose={() => setFolderBrowserOpen(false)}
        onConfirm={(path) => {
          setWorkspace(path);
          setFolderBrowserOpen(false);
        }}
      />
      
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
          { type: 'separator' },
          { label: 'New File', action: (target) => {
            const path = target.getAttribute('data-path');
            const type = target.getAttribute('data-type');
            const dir = type === 'dir' ? path : path?.split('/').slice(0, -1).join('/') || "";
            if (path) handleCreateFile(dir || "");
          }},
          { label: 'New Folder', action: (target) => {
            const path = target.getAttribute('data-path');
            const type = target.getAttribute('data-type');
            const dir = type === 'dir' ? path : path?.split('/').slice(0, -1).join('/') || "";
            if (path) handleCreateFolder(dir || "");
          }},
          { type: 'separator' },
          { label: 'Delete', shortcut: 'Delete', danger: true, action: (target) => {
            const path = target.getAttribute('data-path');
            const name = target.getAttribute('data-name');
            if (path && name) {
              setConfirmDelete({ path, name });
            }
          }}
        ]}
      />
      <InputDialog
        isOpen={!!inputDialog}
        title={inputDialog?.type === 'file' ? 'New File' : 'New Folder'}
        placeholder={inputDialog?.type === 'file' ? 'filename.ext' : 'folder name'}
        onConfirm={(name) => {
          if (!inputDialog) return;
          const fullPath = inputDialog.dir ? `${inputDialog.dir}/${name}` : name;
          if (inputDialog.type === 'file') createFile(fullPath);
          else createFolder(fullPath);
        }}
        onClose={() => setInputDialog(null)}
      />
    </div>
  );
}
