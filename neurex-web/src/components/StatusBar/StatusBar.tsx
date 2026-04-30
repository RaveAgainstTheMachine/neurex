import React from "react";
import { AlertCircle, AlertTriangle, GitGraph, Activity, Braces } from "lucide-react";
import { useStore } from "../../lib/store";
import "./StatusBar.css";

interface StatusBarProps {
  wsStatus: "connected" | "disconnected" | "connecting";
  setPaletteMode: (mode: "none" | "language" | "indent" | "encoding" | "global") => void;
  setSidebarTab: (tab: any) => void;
  isAIActive: boolean;
}

export function StatusBar({ wsStatus, setPaletteMode, setSidebarTab, isAIActive }: StatusBarProps) {
  const { 
    hiveStats, diagnostics, gitBranch, gitChanges, 
    cursorPosition, activeFileLanguage 
  } = useStore();

  return (
    <div className={`status-bar status-bar--${wsStatus}`}>
      <div className="status-bar__left">
        <button className="status-segment status-segment--interactive" onClick={() => setSidebarTab("git")}>
          <GitGraph size={12} />
          <span>{gitBranch}</span>
          {gitChanges.length > 0 && <span className="status-change-count">({gitChanges.length})</span>}
        </button>

        <button className="status-segment status-segment--interactive" onClick={() => {
          const event = new CustomEvent("neurex_show_problems");
          window.dispatchEvent(event);
        }}>
          <AlertCircle size={12} />
          <span>0</span>
          <AlertTriangle size={12} />
          <span>{diagnostics.length}</span>
        </button>
      </div>

      <div className="status-bar__center">
        {isAIActive && (
          <div className="status-segment status-ai-pulse">
            <Activity size={12} />
            <span>Neurex Composing...</span>
          </div>
        )}
      </div>

      <div className="status-bar__right">
        <div className="status-segments">
          <span className="status-segment" title="Cursor Position">Ln {cursorPosition.line}, Col {cursorPosition.ch}</span>
          <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("indent")}>Spaces: 2</button>
          <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("encoding")}>UTF-8</button>
          <button className="status-segment">LF</button>
          <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("language")}>
            <span>{(activeFileLanguage || "Plain Text").toUpperCase()}</span>
          </button>
          <div className="status-segment status-segment--mesh" title="Mesh Network Status">
             <Activity size={12} />
             <span>{hiveStats.total_nodes} NODES</span>
          </div>
        </div>
      </div>
    </div>
  );
}
