import React, { useMemo } from "react";
import { useStore } from "../../lib/store";
import { Sparkles, Check, X, FileText, AlertCircle, Trash2, Plus } from "lucide-react";
import toast from "react-hot-toast";
import "./SwarmDiffSidebar.css";

export function SwarmDiffSidebar() {
  const swarmDiffsObj = useStore((s) => s.swarmDiffs);
  const swarmDiffs = useMemo(() => Object.values(swarmDiffsObj), [swarmDiffsObj]);
  const activeFile = useStore((s) => s.activeFile);
  const openFile = useStore((s) => s.openFile);
  const setActiveFile = useStore((s) => s.setActiveFile);
  const setDiff = useStore((s) => s.setDiff);
  const acceptSwarmDiff = useStore((s) => s.acceptSwarmDiff);
  const discardSwarmDiff = useStore((s) => s.discardSwarmDiff);
  const clearSwarmDiffs = useStore((s) => s.clearSwarmDiffs);

  // Helper to determine change type (new, modified, deleted)
  const getChangeType = (original: string, modified: string) => {
    if (!original && modified) return { label: "NEW", color: "var(--text-green)", bg: "rgba(0,230,118,0.1)", icon: Plus };
    if (original && !modified) return { label: "DELETE", color: "var(--text-red)", bg: "rgba(255,23,68,0.1)", icon: Trash2 };
    return { label: "MODIFY", color: "var(--accent-glow)", bg: "rgba(0,184,212,0.1)", icon: FileText };
  };

  const handleFileClick = (path: string, original: string, modified: string) => {
    const s = useStore.getState();
    const isAlreadyOpen = s.openFiles.some((f) => f.path === path);
    if (!isAlreadyOpen) {
      s.openFile(path, original || "", "plaintext");
    }
    s.setDiff(path, original, modified);
    s.setActiveFile(path);
    toast.success(`Comparing: ${path.split("/").pop()}`, { id: "diff-toast" });
  };

  const handleAcceptFile = (e: React.MouseEvent, path: string) => {
    e.stopPropagation();
    acceptSwarmDiff(path);
    toast.success(`Accepted changes for ${path.split("/").pop()}`);
  };

  const handleDiscardFile = (e: React.MouseEvent, path: string) => {
    e.stopPropagation();
    discardSwarmDiff(path);
    toast.success(`Discarded changes for ${path.split("/").pop()}`);
  };

  const handleAcceptAll = () => {
    const s = useStore.getState();
    swarmDiffs.forEach((diff) => {
      if (diff.status === "pending") {
        s.acceptSwarmDiff(diff.path);
        // Also call original accept action if the file is in openFiles to clean up state
        s.acceptDiff(diff.path);
      }
    });
    toast.success("Accepted all swarm changes!");
  };

  const handleDiscardAll = () => {
    const s = useStore.getState();
    swarmDiffs.forEach((diff) => {
      if (diff.status === "pending") {
        s.discardSwarmDiff(diff.path);
        s.discardDiff(diff.path);
      }
    });
    toast.success("Discarded all swarm changes.");
  };

  const pendingDiffs = useMemo(() => swarmDiffs.filter(d => d.status === "pending"), [swarmDiffs]);

  return (
    <div className="swarm-diff-sidebar">
      <div className="swarm-diff-sidebar__header">
        <div className="title-wrapper">
          <Sparkles size={16} className="text-cyan animate-pulse" />
          <span>Swarm Changes</span>
        </div>
        {pendingDiffs.length > 0 && (
          <span className="swarm-badge">{pendingDiffs.length} pending</span>
        )}
      </div>

      {swarmDiffs.length > 0 ? (
        <div className="swarm-diff-sidebar__content">
          <div className="swarm-actions-header">
            <button 
              className="action-btn accept-all" 
              onClick={handleAcceptAll}
              disabled={pendingDiffs.length === 0}
            >
              <Check size={14} /> Accept All
            </button>
            <button 
              className="action-btn discard-all" 
              onClick={handleDiscardAll}
              disabled={pendingDiffs.length === 0}
            >
              <X size={14} /> Discard All
            </button>
          </div>

          <div className="swarm-file-list">
            {swarmDiffs.map((diff) => {
              const meta = getChangeType(diff.original, diff.modified);
              const isCurrent = activeFile === diff.path;
              const _Icon = meta.icon;

              return (
                <div 
                  key={diff.path}
                  className={`swarm-file-item ${isCurrent ? "current" : ""} ${diff.status}`}
                  onClick={() => handleFileClick(diff.path, diff.original, diff.modified)}
                >
                  <div className="file-item-header">
                    <div className="file-name-meta">
                      <span className="file-status-badge" style={{ color: meta.color, backgroundColor: meta.bg }}>
                        {meta.label}
                      </span>
                      <span className="file-item-path" title={diff.path}>
                        {diff.path.split("/").pop()}
                      </span>
                    </div>
                    {diff.status === "pending" ? (
                      <div className="file-item-actions">
                        <button 
                          className="item-btn btn-accept" 
                          onClick={(e) => handleAcceptFile(e, diff.path)}
                          title="Accept file"
                        >
                          <Check size={12} />
                        </button>
                        <button 
                          className="item-btn btn-discard" 
                          onClick={(e) => handleDiscardFile(e, diff.path)}
                          title="Discard file"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ) : (
                      <span className={`status-badge-final ${diff.status}`}>
                        {diff.status.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="file-item-sub">{diff.path}</div>
                </div>
              );
            })}
          </div>

          <div className="swarm-footer-actions">
            <button className="clear-swarm-btn" onClick={clearSwarmDiffs}>
              Clear Workspace
            </button>
          </div>
        </div>
      ) : (
        <div className="swarm-diff-sidebar__empty">
          <AlertCircle size={24} className="text-muted" />
          <p>No active swarm changes to review.</p>
          <span>Ask the AI to perform a multi-file refactoring to populate this workspace.</span>
        </div>
      )}
    </div>
  );
}
