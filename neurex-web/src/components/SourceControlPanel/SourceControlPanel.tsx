// neurex-web/src/components/SourceControlPanel/SourceControlPanel.tsx
"use client";

import { useState, useEffect } from "react";
import { 
  GitBranch, RotateCw, Plus, Minus, 
  Check, MoreHorizontal, ChevronDown, ChevronRight, FileText, 
  History, Sparkles, List, Share2, Folder
} from "lucide-react";
import { useStore } from "../../lib/store";
import toast from "react-hot-toast";
import React from "react";
import "./SourceControlPanel.css";

import { API_BASE } from "../../lib/config";

interface GitChange {
  path: string;
  status: "modified" | "added" | "deleted" | "renamed" | "untracked";
  staged: boolean;
}

export function SourceControlPanel() {
  const { token, refreshFileTree, diffFile } = useStore();
  const [branch, setBranch] = useState("main");
  const [changes, setChanges] = useState<GitChange[]>([]);
  const [commitMessage, setCommitMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [expanded, setExpanded] = useState({ staged: true, unstaged: true });
  const [viewMode, setViewMode] = useState<'tree' | 'flat'>(() => {
    return (localStorage.getItem("neurex_sc_view_mode") as 'tree' | 'flat') || 'tree';
  });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const toggleViewMode = () => {
    const next = viewMode === 'tree' ? 'flat' : 'tree';
    setViewMode(next);
    localStorage.setItem("neurex_sc_view_mode", next);
  };

  const toggleNode = (path: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const fetchGitStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/git/status`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setBranch(data.branch || "unknown");
      setChanges(data.changes || []);
    } catch (err) {
      console.error("Git status failed", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGitStatus();
  }, []);

  const handleGenerateCommit = async () => {
    if (isGenerating) return;
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/git/generate_commit_msg`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.message) {
        setCommitMessage(data.message);
        toast.success("Semantic message generated");
      }
    } catch (err) {
      toast.error("Failed to generate message");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCommit = async () => {
    if (!commitMessage.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/git/commit`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ message: commitMessage })
      });
      if (res.ok) {
        setCommitMessage("");
        fetchGitStatus();
        refreshFileTree();
        toast.success("Changes committed to " + branch);
      }
    } catch (err) {
      toast.error("Commit failed");
    } finally {
      setLoading(false);
    }
  };

  const toggleStage = async (path: string, staged: boolean) => {
    try {
      await fetch(`${API_BASE}/api/git/${staged ? "unstage" : "stage"}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ path })
      });
      fetchGitStatus();
    } catch (err) {}
  };

  const stagedChanges = changes.filter(c => c.staged);
  const unstagedChanges = changes.filter(c => !c.staged);

  return (
    <div className="source-control">
      <div className="source-control__header">
        <div className="source-control__title">SOURCE CONTROL</div>
        <div className="source-control__actions">
          <button 
            className={`view-toggle-btn ${viewMode === 'tree' ? 'active' : ''}`}
            onClick={toggleViewMode}
            title={viewMode === 'tree' ? "Switch to Flat View" : "Switch to Tree View"}
          >
            {viewMode === 'tree' ? <Share2 size={14} /> : <List size={14} />}
          </button>
          <button onClick={fetchGitStatus} title="Refresh" className={`icon-btn ${loading ? "animate-spin" : ""}`}>
            <RotateCw size={14} />
          </button>
          <button title="View History" className="icon-btn"><History size={14} /></button>
          <button title="More Actions" className="icon-btn"><MoreHorizontal size={14} /></button>
        </div>
      </div>

      <div className="source-control__branch">
        <GitBranch size={14} className="text-purple" />
        <span className="branch-name">{branch}</span>
      </div>

      <div className="source-control__commit-box">
        <div className="commit-textarea-wrapper">
          <textarea 
            placeholder="Commit message..."
            value={commitMessage}
            onChange={(e) => setCommitMessage(e.target.value)}
            onKeyDown={(e) => (e.metaKey || e.ctrlKey) && e.key === "Enter" && handleCommit()}
          />
          <button 
            className={`ai-generate-btn ${isGenerating ? 'loading' : ''}`} 
            onClick={handleGenerateCommit}
            title="Generate AI Commit Message"
            disabled={isGenerating || stagedChanges.length === 0}
          >
            {isGenerating ? <RotateCw size={12} className="animate-spin" /> : <Sparkles size={12} />}
          </button>
        </div>
        <button 
          className="btn btn--purple commit-btn" 
          disabled={loading || !commitMessage.trim() || stagedChanges.length === 0}
          onClick={handleCommit}
        >
          {loading ? <RotateCw size={14} className="animate-spin" /> : <Check size={14} />}
          <span>Commit changes</span>
        </button>
      </div>

      <div className="source-control__lists">
        {stagedChanges.length > 0 && (
          <div className="change-list">
            <div className="change-list__header" onClick={() => setExpanded(v => ({ ...v, staged: !v.staged }))}>
              {expanded.staged ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <span>STAGED</span>
              <span className="count-badge">{stagedChanges.length}</span>
            </div>
            {expanded.staged && (
              viewMode === 'flat' ? (
                stagedChanges.map(change => (
                  <ChangeItem 
                    key={change.path} 
                    change={change} 
                    onToggle={() => toggleStage(change.path, true)}
                    onClick={() => diffFile(change.path)}
                  />
                ))
              ) : (
                <GitTree 
                  changes={stagedChanges} 
                  onToggle={(path) => toggleStage(path, true)} 
                  onSelect={diffFile}
                  expandedNodes={expandedNodes}
                  onToggleNode={toggleNode}
                />
              )
            )}
          </div>
        )}

        <div className="change-list">
          <div className="change-list__header" onClick={() => setExpanded(v => ({ ...v, unstaged: !v.unstaged }))}>
            {expanded.unstaged ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>CHANGES</span>
            <span className="count-badge">{unstagedChanges.length}</span>
          </div>
          {expanded.unstaged && unstagedChanges.length === 0 && (
            <div className="change-list__empty">No pending changes</div>
          )}
          {expanded.unstaged && (
            viewMode === 'flat' ? (
              unstagedChanges.map(change => (
                <ChangeItem 
                  key={change.path} 
                  change={change} 
                  onToggle={() => toggleStage(change.path, false)}
                  onClick={() => diffFile(change.path)}
                />
              ))
            ) : (
              <GitTree 
                changes={unstagedChanges} 
                onToggle={(path) => toggleStage(path, false)} 
                onSelect={diffFile}
                expandedNodes={expandedNodes}
                onToggleNode={toggleNode}
              />
            )
          )}
        </div>
      </div>
    </div>
  );
}

interface ChangeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children: Record<string, ChangeNode>;
  change?: GitChange;
}

function GitTree({ changes, onToggle, onSelect, expandedNodes, onToggleNode }: { 
  changes: GitChange[], 
  onToggle: (p: string) => void, 
  onSelect: (p: string) => void,
  expandedNodes: Set<string>,
  onToggleNode: (p: string) => void
}) {
  const buildTree = (changes: GitChange[]) => {
    const root: Record<string, ChangeNode> = {};
    
    changes.forEach(change => {
      const parts = change.path.split('/');
      let current = root;
      let fullPath = "";
      
      parts.forEach((part, i) => {
        fullPath += (fullPath ? "/" : "") + part;
        const isLast = i === parts.length - 1;
        
        if (!current[part]) {
          current[part] = {
            name: part,
            path: fullPath,
            type: isLast ? 'file' : 'folder',
            children: {},
            change: isLast ? change : undefined
          };
        }
        current = current[part].children;
      });
    });
    return root;
  };

  const tree = buildTree(changes);

  const renderNodes = (nodes: Record<string, ChangeNode>, depth = 0) => {
    return Object.values(nodes)
      .sort((a, b) => {
        if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
        return a.name.localeCompare(b.name);
      })
      .map(node => {
        const isExpanded = expandedNodes.has(node.path);
        const hasChildren = Object.keys(node.children).length > 0;

        return (
          <React.Fragment key={node.path}>
            <ChangeItem 
              change={node.change || { path: node.path, status: 'modified', staged: false } as any}
              isFolder={node.type === 'folder'}
              depth={depth}
              isExpanded={isExpanded}
              onToggle={() => node.type === 'file' ? onToggle(node.path) : onToggleNode(node.path)}
              onClick={() => node.type === 'file' ? onSelect(node.path) : onToggleNode(node.path)}
            />
            {node.type === 'folder' && isExpanded && (
              <div className="change-item__children">
                {renderNodes(node.children, depth + 1)}
              </div>
            )}
          </React.Fragment>
        );
      });
  };

  return <div className="git-tree">{renderNodes(tree)}</div>;
}

function ChangeItem({ 
  change, onToggle, onClick, isFolder, depth = 0, isExpanded 
}: { 
  change: GitChange; 
  onToggle: () => void; 
  onClick: () => void;
  isFolder?: boolean;
  depth?: number;
  isExpanded?: boolean;
}) {
  const { activeFile } = useStore();
  const isActive = activeFile === change.path;

  const statusChar = isFolder ? null : {
    modified: "M",
    added: "A",
    deleted: "D",
    renamed: "R",
    untracked: "U"
  }[change.status];

  return (
    <div 
      className={`change-item ${isActive ? "active" : ""} ${isFolder ? "change-item--folder" : `status--${change.status}`}`} 
      onClick={onClick}
      style={{ paddingLeft: 8 + depth * 12 }}
    >
      {/* Indent Guides */}
      {Array.from({ length: depth }).map((_, i) => (
        <div 
          key={i} 
          className="change-item__indent-guide" 
          style={{ left: 12 + i * 12 }} 
        />
      ))}

      <div className="change-item__main">
        {isFolder ? (
          <div className="change-item__arrow">
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </div>
        ) : null}
        
        {isFolder ? <Folder size={14} className="change-icon" /> : <FileText size={14} className="change-icon" />}
        
        <div className="change-info">
          <span className="change-name">{change.path.split("/").pop()}</span>
        </div>
        {!isFolder && depth === 0 && (
          <span className="change-path">{change.path.substring(0, change.path.lastIndexOf("/"))}</span>
        )}
      </div>
      
      {!isFolder && (
        <div className="change-item__actions">
          <span className="status-badge">{statusChar}</span>
          <button 
            className="stage-btn" 
            onClick={(e) => { e.stopPropagation(); onToggle(); }}
            title={change.staged ? "Unstage" : "Stage"}
          >
            {change.staged ? <Minus size={14} /> : <Plus size={14} />}
          </button>
        </div>
      )}
    </div>
  );
}
