import { useState } from "react";
import { 
  AlertCircle, AlertTriangle, GitGraph, Activity, 
  X, CheckCircle, Bell, BellOff, Info 
} from "lucide-react";
import { useStore } from "../../lib/store";
import "./StatusBar.css";

interface StatusBarProps {
  wsStatus: "connected" | "disconnected" | "connecting";
  setPaletteMode: (mode: "none" | "language" | "indent" | "encoding" | "global") => void;
  setSidebarTab: (tab: any) => void;
  isAIActive: boolean;
}

export function StatusBar({ wsStatus, setPaletteMode, setSidebarTab, isAIActive }: StatusBarProps) {
  // Phase 44.20: Strict State Selection (Prevent Status churn)
  const diagnostics = useStore(s => s.diagnostics);
  const gitBranch = useStore(s => s.gitBranch);
  const gitChanges = useStore(s => s.gitChanges);
  const cursorPosition = useStore(s => s.cursorPosition);
  const activeFileLanguage = useStore(s => s.activeFileLanguage);
  const settings = useStore(s => s.settings);
  const hiveStats = useStore(s => s.hiveStats);

  const notifications = useStore(s => s.notifications);
  const clearNotifications = useStore(s => s.clearNotifications);
  const markNotificationsAsRead = useStore(s => s.markNotificationsAsRead);
  const [showNotifications, setShowNotifications] = useState(false);
  const notificationCount = notifications.filter(n => n.unread).length;


  return (
    <div className={`status-bar status-bar--${wsStatus} ${settings?.enable_swarm_glow ? "status-bar--glow" : ""}`}>
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
          <div className="status-segment status-segment--mesh" title={`Mesh Network Status: ${hiveStats.total_nodes} node(s) online`}>
             <Activity size={12} />
             <span>MESH ACTIVE ({hiveStats.total_nodes})</span>
          </div>
          <div className="status-segment" title={`Swarm Collective Memory: ${hiveStats.memory_count} memories indexed`}>
             <span>MEM: {hiveStats.memory_count}</span>
          </div>
          <button 
            className={`status-segment status-segment--interactive status-segment--notification ${showNotifications ? "active" : ""}`}
            onClick={() => {
              const nextVal = !showNotifications;
              setShowNotifications(nextVal);
              if (nextVal) {
                markNotificationsAsRead();
              }
            }}
          >
            {notificationCount > 0 ? <Bell size={12} /> : <BellOff size={12} />}
            {notificationCount > 0 && <span className="notification-badge">{notificationCount}</span>}
          </button>
        </div>
 
        {showNotifications && (
          <div className="notifications-center">
            <div className="notifications-header">
              <span>NOTIFICATIONS</span>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                {notifications.length > 0 && (
                  <button 
                    className="notifications-clear-btn" 
                    onClick={clearNotifications}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--accent-color, #9c6fff)",
                      fontSize: "10px",
                      cursor: "pointer",
                      padding: "2px 6px",
                      borderRadius: "4px",
                    }}
                  >
                    Clear All
                  </button>
                )}
                <button className="icon-btn" onClick={() => setShowNotifications(false)}><X size={14} /></button>
              </div>
            </div>
            <div className="notifications-list">
              {notifications.length === 0 ? (
                <div className="notification-empty">No new notifications</div>
              ) : (
                notifications.map((n) => (
                  <div key={n.id} className="notification-item">
                    {n.type === "success" && <CheckCircle size={14} className="text-green" />}
                    {n.type === "error" && <AlertCircle size={14} className="text-red" />}
                    {n.type === "warning" && <AlertTriangle size={14} className="text-yellow" />}
                    {n.type === "info" && <Info size={14} className="text-blue" />}
                    <div className="notification-content">
                      <div className="notification-title">{n.title}</div>
                      <div className="notification-desc">{n.description}</div>
                      <div className="notification-time">{n.timestamp}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
