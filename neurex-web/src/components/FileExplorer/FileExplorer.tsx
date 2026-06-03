// src/components/FileExplorer/FileExplorer.tsx
import React, { useState, useEffect, useMemo, useRef } from "react";
import { 
  ChevronRight, ChevronDown, File, Folder, FolderOpen, RefreshCw, Loader2,
  FileJson, FileCode, FileText, Settings, GitGraph, 
  Database, Terminal as TerminalIcon, FilePlus, FolderPlus, FoldVertical, X,
  Braces, Square, PlusCircle
} from "lucide-react";
import { Panel, PanelGroup, PanelResizeHandle, ImperativePanelHandle } from "react-resizable-panels";
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

function SidebarResizeHandle() {
  return <PanelResizeHandle className="sidebar-resize-handle" />;
}

const FileItem = React.memo(function FileItem({ node, depth, rootPath }: { 
  node: FileNode; 
  depth: number;
  rootPath?: string;
}) {
  // Phase 44.16: Strict State Selection (Bypass store-wide re-renders)
  const openFile = useStore(s => s.openFile);
  const setActiveFile = useStore(s => s.setActiveFile);
  const activeFile = useStore(s => s.activeFile);
  const fetchSubtree = useStore(s => s.fetchSubtree);
  const expandedFolders = useStore(s => s.expandedFolders);
  const collapsedFolders = useStore(s => s.collapsedFolders);
  const toggleFolder = useStore(s => s.toggleFolder);
  const openFiles = useStore(s => s.openFiles);
  const workspaceDiagnostics = useStore(s => s.workspaceDiagnostics);
  const collapseSignal = useStore(s => s.collapseSignal);
  
  const currentRoot = depth === 0 ? node.path : rootPath;
  
  const expanded = useMemo(() => {
    if (node.type !== "dir") return false;
    if (node.path !== undefined && collapsedFolders.has(node.path)) return false;
    if (node.path !== undefined && expandedFolders.has(node.path)) return true;
    return depth < 1; 
  }, [node.path, node.type, depth, expandedFolders, collapsedFolders, collapseSignal]);

  const isDir = node.type === "dir";
  const [fetching, setFetching] = useState(false);
  const isActive = activeFile === node.path;

  useEffect(() => {
    if (expanded && isDir && node.path !== undefined && (node.children === null || node.children === undefined)) {
      const timer = setTimeout(() => {
        if (expanded && isDir && node.path !== undefined) fetchSubtree(node.path);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [expanded, isDir, node.path, node.children, fetchSubtree]);

  // Phase 44.16: Shallow Status Aggregation (Bypass recursive walks)
  const status = useMemo(() => {
    const hasDirty = openFiles.some(f => f.path.startsWith(node.path || "") && f.isDirty);
    const hasErrors = Object.keys(workspaceDiagnostics).some(p => p.startsWith(node.path || "") && workspaceDiagnostics[p].length > 0);
    return { dirty: hasDirty, error: hasErrors || (node.errors || 0) > 0 };
  }, [node.path, openFiles, workspaceDiagnostics, node.errors]);

  const handleClick = async () => {
    if (isDir) {
      if (!expanded && node.path !== undefined && (!node.children || node.children.length === 0)) {
        setFetching(true);
        await fetchSubtree(node.path);
        setFetching(false);
      }
      if (node.path !== undefined) toggleFolder(node.path);
    } else if (node.path) {
      const alreadyOpen = openFiles.find(f => f.path === node.path && f.root === currentRoot);
      if (alreadyOpen) { 
        setActiveFile(node.path); 
        return; 
      }
      try {
        const params = new URLSearchParams({ path: node.path });
        if (currentRoot) params.append("root_path", currentRoot);
        const data = await api.get<{ content: string }>(`/api/files/read?${params.toString()}`);
        openFile(node.path, data.content ?? "", getLanguage(node.path), true, currentRoot);
      } catch { /* intentional */ }
    }
  };

  return (
    <div className="file-tree-node">
      <div
        className={`file-item ${isActive ? "file-item--active" : ""} status-${node.status || 'none'} ${(node.errors ?? 0) > 0 ? 'status-error' : ''} ${depth === 0 ? 'file-item--root' : ''}`}
        style={{ paddingLeft: 8 + depth * 12 }}
        onClick={handleClick}
        data-path={node.path}
        data-type={node.type}
        data-name={node.name}
        data-depth={depth}
        data-root={currentRoot}
      >
        <div className="file-item__main">
          {isDir ? (
            <span className="file-item__arrow">
              {fetching ? <Loader2 size={10} className="animate-spin" /> : (expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />)}
            </span>
          ) : <span className="file-item__spacer" />}
          {getFileIcon(node.name, isDir, expanded)}
          <span className="file-item__name">{node.name}</span>
        </div>
        <div className="file-item__status">
          {status.dirty && <span className="indicator-dot indicator-dot--dirty" />}
          {(node.errors ?? 0) > 0 && <span className="problem-badge">{node.errors}</span>}
          {!isDir && node.status === "M" && <span className="git-indicator git-indicator--modified">M</span>}
          {!isDir && node.status === "U" && <span className="git-indicator git-indicator--untracked">U</span>}
        </div>
      </div>
      {isDir && expanded && node.children && (
        <div className="file-item__children">
          {node.children.filter(child => child && child.name)
            .sort((a, b) => (a.type === "dir" ? -1 : 1) || a.name.localeCompare(b.name))
            .map((child) => (
              <FileItem key={child.path || child.name} node={child} depth={depth + 1} rootPath={currentRoot} />
            ))}
        </div>
      )}
    </div>
  );
});

export function FileExplorer() {
  const { 
    fileTree, workspaceFolders, addWorkspaceFolder, removeWorkspaceFolder, 
    refreshFileTree, setWorkspace, createFile, createFolder, 
    collapseAllFolders, deleteFile, activeFile, openFiles, setPendingJump 
  } = useStore();

  const [__loading, setLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ path: string, name: string, root?: string } | null>(null);
  const [inputDialog, setInputDialog] = useState<{ type: 'file' | 'folder', dir: string, root?: string } | null>(null);
  const [folderBrowser, setFolderBrowser] = useState<{ open: boolean, mode: 'open' | 'add' }>({ open: false, mode: 'open' });
  const [sections, setSections] = useState({ open: true, workspace: true, outline: false });

  const openEditorsRef = useRef<ImperativePanelHandle>(null);
  const explorerRef = useRef<ImperativePanelHandle>(null);
  const outlineRef = useRef<ImperativePanelHandle>(null);

  const activeContent = useMemo(() => {
    return openFiles.find(f => f.path === activeFile)?.content || "";
  }, [activeFile, openFiles]);

  const symbols = useMemo(() => {
    if (!activeContent) return [];
    const lines = activeContent.split("\n");
    const results: { name: string; line: number; type: "func" | "class" | "interface" }[] = [];
    
    const funcRegex = /^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)/;
    const arrowFuncRegex = /^(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>/;
    const classRegex = /^(?:export\s+)?class\s+([a-zA-Z0-9_]+)/;
    const interfaceRegex = /^(?:export\s+)?interface\s+([a-zA-Z0-9_]+)/;
    const pyDefRegex = /^\s*def\s+([a-zA-Z0-9_]+)\s*\(/;
    const pyClassRegex = /^\s*class\s+([a-zA-Z0-9_]+)\s*(?:\(|:)/;

    lines.forEach((line, i) => {
      let match;
      if ((match = line.match(funcRegex)) || (match = line.match(pyDefRegex))) results.push({ name: match[1], line: i + 1, type: "func" });
      else if ((match = line.match(classRegex)) || (match = line.match(pyClassRegex))) results.push({ name: match[1], line: i + 1, type: "class" });
      else if ((match = line.match(interfaceRegex))) results.push({ name: match[1], line: i + 1, type: "interface" });
      else if ((match = line.match(arrowFuncRegex))) results.push({ name: match[1], line: i + 1, type: "func" });
    });
    return results;
  }, [activeContent]);

  const handleRefresh = async () => {
    setLoading(true);
    const tid = toast.loading("Refreshing workspace...");
    try {
      await refreshFileTree();
      toast.success("Explorer synchronized", { id: tid });
    } catch (_err) {
      toast.error("Sync failed", { id: tid });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFolder = () => setFolderBrowser({ open: true, mode: 'open' });
  const handleAddFolder = () => setFolderBrowser({ open: true, mode: 'add' });

  const toggleSection = (key: keyof typeof sections) => {
    const newVal = !sections[key];
    setSections(s => ({ ...s, [key]: newVal }));
    
    if (key === 'open' && openEditorsRef.current) {
      void (newVal ? openEditorsRef.current.resize(10) : openEditorsRef.current.resize(4));
    } else if (key === 'workspace' && explorerRef.current) {
      void (newVal ? explorerRef.current.resize(80) : explorerRef.current.resize(10));
    } else if (key === 'outline' && outlineRef.current) {
      if (newVal) {
        outlineRef.current.resize(20);
        // Shrink explorer to make room
        if (explorerRef.current) explorerRef.current.resize(70);
      } else {
        outlineRef.current.resize(4);
        if (explorerRef.current) explorerRef.current.resize(90);
      }
    }
  };

  return (
    <div className="file-explorer">
      <PanelGroup direction="vertical">
        {/* ── Open Editors ──────────────────────────────────────────────── */}
        <Panel 
          ref={openEditorsRef}
          defaultSize={6} 
          minSize={4} 
          className="sidebar-section"
        >
          <div className="sidebar-section__header" onClick={() => toggleSection('open')}>
            {sections.open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>OPEN EDITORS</span>
          </div>
          {sections.open && (
            <div className="sidebar-section__content open-editors-list">
              {openFiles.map(f => (
                <div key={f.path} className={`open-editor-item ${f.path === activeFile ? 'active' : ''}`} onClick={() => useStore.getState().setActiveFile(f.path)}>
                  <FileCode size={12} className="text-muted" />
                  <span>{f.path.split('/').pop()}</span>
                  <X size={12} className="close-icon" onClick={(e) => { e.stopPropagation(); useStore.getState().closeFile(f.path); }} />
                </div>
              ))}
            </div>
          )}
        </Panel>

        <SidebarResizeHandle />

        {/* ── Explorer ──────────────────────────────────────────────────── */}
        <Panel 
          ref={explorerRef}
          defaultSize={90} 
          minSize={10} 
          className="sidebar-section"
        >
          <div className="sidebar-section__header explorer-header" onClick={() => toggleSection('workspace')}>
            <div className="sidebar-section__header-left">
              {sections.workspace ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <span>{workspaceFolders.length > 1 ? "WORKSPACE" : "NEUREX"}</span>
            </div>
            <div className="explorer-actions">
              <button className="icon-btn" onClick={(e) => { e.stopPropagation(); setInputDialog({ type: 'file', dir: "" }); }} title="New File"><FilePlus size={14} /></button>
              <button className="icon-btn" onClick={(e) => { e.stopPropagation(); setInputDialog({ type: 'folder', dir: "" }); }} title="New Folder"><FolderPlus size={14} /></button>
              <button className="icon-btn" onClick={(e) => { e.stopPropagation(); handleRefresh(); }} title="Refresh"><RefreshCw size={12} /></button>
              <button className="icon-btn" onClick={(e) => { e.stopPropagation(); collapseAllFolders(); }} title="Collapse All"><FoldVertical size={14} /></button>
            </div>
          </div>
          {sections.workspace && (
            <div className="sidebar-section__content">
              {fileTree.length > 0 ? (
                fileTree.filter(node => node && node.name)
                  .sort((a, b) => (a.type === "dir" ? -1 : 1) || a.name.localeCompare(b.name))
                  .map((node) => <FileItem key={node.path || node.name} node={node} depth={0} />)
              ) : (
                <div className="explorer-empty-state">
                  <button className="btn btn--purple btn--full" onClick={handleOpenFolder}>Open Folder</button>
                </div>
              )}
            </div>
          )}
        </Panel>

        <SidebarResizeHandle />

        {/* ── Outline ───────────────────────────────────────────────────── */}
        <Panel 
          ref={outlineRef}
          defaultSize={4} 
          minSize={4} 
          collapsible={true}
          className="sidebar-section"
        >
          <div className="sidebar-section__header" onClick={() => toggleSection('outline')}>
            {sections.outline ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>OUTLINE</span>
          </div>
          {sections.outline && (
            <div className="sidebar-section__content outline-list">
              {symbols.length > 0 ? symbols.map((sym, i) => (
                <div key={i} className="outline-item" onClick={() => setPendingJump(activeFile!, sym.line)}>
                  {sym.type === "class" ? <Braces size={12} className="text-purple" /> : 
                   sym.type === "interface" ? <Database size={12} className="text-amber" /> :
                   <Square size={10} className="text-cyan" />}
                  <span>{sym.name}</span>
                  <span className="outline-line">:{sym.line}</span>
                </div>
              )) : <div className="outline-empty">No symbols found</div>}
            </div>
          )}
        </Panel>
      </PanelGroup>
      
      <FolderBrowser 
        isOpen={folderBrowser.open}
        onClose={() => setFolderBrowser(prev => ({ ...prev, open: false }))}
        onConfirm={(path) => {
          if (folderBrowser.mode === 'open') setWorkspace(path);
          else addWorkspaceFolder(path);
          setFolderBrowser(prev => ({ ...prev, open: false }));
        }}
      />
      
      <ConfirmModal 
        isOpen={!!confirmDelete}
        title="Permanently Delete?"
        message={`Are you sure you want to delete '${confirmDelete?.name}'?`}
        confirmLabel="Delete"
        danger={true}
        onClose={() => setConfirmDelete(null)}
        onConfirm={() => { if (confirmDelete) { deleteFile(confirmDelete.path, confirmDelete.root); setConfirmDelete(null); } }}
      />
      <InputDialog
        isOpen={!!inputDialog}
        title={inputDialog?.type === 'file' ? 'New File' : 'New Folder'}
        placeholder={inputDialog?.type === 'file' ? 'filename.ext' : 'folder name'}
        onConfirm={(name) => {
          if (!inputDialog) return;
          const fullPath = inputDialog.dir ? `${inputDialog.dir}/${name}` : name;
          if (inputDialog.type === 'file') createFile(fullPath, inputDialog.root);
          else createFolder(fullPath, inputDialog.root);
        }}
        onClose={() => setInputDialog(null)}
      />
      <ContextMenu 
        targetSelector=".file-item"
        items={[
          { label: 'New File', action: (target: any) => setInputDialog({ type: 'file', dir: target.getAttribute('data-type') === 'dir' ? target.getAttribute('data-path') : target.getAttribute('data-path').split('/').slice(0, -1).join('/'), root: target.getAttribute('data-root') }) },
          { label: 'New Folder', action: (target: any) => setInputDialog({ type: 'folder', dir: target.getAttribute('data-type') === 'dir' ? target.getAttribute('data-path') : target.getAttribute('data-path').split('/').slice(0, -1).join('/'), root: target.getAttribute('data-root') }) },
          { type: 'separator' },
          { label: 'Add Folder to Workspace...', icon: <PlusCircle size={14} />, action: handleAddFolder },
          { label: 'Delete', shortcut: 'Delete', danger: true, action: (target: any) => setConfirmDelete({ path: target.getAttribute('data-path'), name: target.getAttribute('data-name'), root: target.getAttribute('data-root') }) }
        ]}
      />
    </div>
  );
}
