// neurex-web/src/components/SourceControlPanel/SourceControlPanel.tsx
"use client";

import { useState, useEffect } from "react";
import { 
  GitBranch, GitCommit, GitPullRequest, RotateCw, Plus, Minus, 
  Check, MoreHorizontal, ChevronDown, ChevronRight, FileText, 
  AlertCircle, History, Sparkles, Wand2 
} from "lucide-react";
import { useStore } from "../../lib/store";
import toast from "react-hot-toast";
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
            {expanded.staged && stagedChanges.map(change => (
              <ChangeItem 
                key={change.path} 
                change={change} 
                onToggle={() => toggleStage(change.path, true)}
                onClick={() => diffFile(change.path)}
              />
            ))}
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
          {expanded.unstaged && unstagedChanges.map(change => (
            <ChangeItem 
              key={change.path} 
              change={change} 
              onToggle={() => toggleStage(change.path, false)}
              onClick={() => diffFile(change.path)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function ChangeItem({ change, onToggle, onClick }: { change: GitChange; onToggle: () => void; onClick: () => void }) {
  const { activeFile } = useStore();
  const isActive = activeFile === change.path;

  const statusChar = {
    modified: "M",
    added: "A",
    deleted: "D",
    renamed: "R",
    untracked: "U"
  }[change.status];

  return (
    <div className={`change-item ${isActive ? "active" : ""}`} onClick={onClick}>
      <div className="change-item__main">
        <FileText size={14} className="change-icon" />
        <div className="change-info">
          <span className="change-name">{change.path.split("/").pop()}</span>
          <span className="change-path">{change.path.substring(0, change.path.lastIndexOf("/"))}</span>
        </div>
      </div>
      <div className="change-item__actions">
        <span className={`status-badge status--${change.status}`}>{statusChar}</span>
        <button 
          className="stage-btn" 
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          title={change.staged ? "Unstage" : "Stage"}
        >
          {change.staged ? <Minus size={14} /> : <Plus size={14} />}
        </button>
      </div>
    </div>
  );
}
