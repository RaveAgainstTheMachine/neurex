// src/App.tsx
import { useState } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import {
  Files, MessageSquare, Settings, GitBranch, Search, Bot, Activity, Clock, Cpu, Shield, Puzzle
} from "lucide-react";
import { FileExplorer } from "./components/FileExplorer/FileExplorer";
import { ConversationList } from "./components/ConversationList/ConversationList";
import { InfraPanel } from "./components/InfraPanel/InfraPanel";
import { SystemLogsPanel } from "./components/SystemLogs/SystemLogs";
import { SearchPanel } from "./components/SearchPanel/SearchPanel";
import { EditorPane } from "./components/Editor/EditorPane";
import { AIPanel } from "./components/AIPanel/AIPanel";
import { Terminal } from "./components/Terminal/Terminal";
import { SkillsPanel } from "./components/SkillsPanel/SkillsPanel";
import { SettingsPanel } from "./components/SettingsPanel/SettingsPanel";
import { PresenceBar } from "./components/PresenceBar/PresenceBar";
import { useWebSocket } from "./hooks/useWebSocket";
import { useNotifications } from "./hooks/useNotifications";
import { useStore } from "./lib/store";
import { Toaster } from "react-hot-toast";
import "./App.css";

type SidebarTab = "explorer" | "search" | "git" | "agent" | "skills" | "history" | "infra" | "system";

export default function App() {
  useNotifications();
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("explorer");
  const [showAIPanel, setShowAIPanel] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const wsStatus = useStore((s) => s.wsStatus);
  const activeConversationId = useStore((s) => s.activeConversationId);

  const { send } = useWebSocket(activeConversationId);

  return (
    <div className="app">
      <Toaster position="top-right" toastOptions={{ 
        style: { background: '#1e1e24', color: '#e8e8f0', border: '1px solid var(--border)' } 
      }} />
      {/* Activity bar (left edge — VS Code style) */}
      <div className="activity-bar">
        <div className="activity-bar__top">
          <div className="activity-bar__logo">⬡</div>
          {(
            [
              { id: "explorer", icon: Files,          label: "Explorer" },
              { id: "search",   icon: Search,         label: "Search" },
              { id: "history",  icon: Clock,          label: "History" },
              { id: "infra",    icon: Cpu,            label: "AI Infrastructure" },
              { id: "system",   icon: Shield,         label: "System Logs" },
              { id: "git",      icon: GitBranch,      label: "Source Control" },
              { id: "skills",   icon: Puzzle,         label: "Skills & Extensions" },
              { id: "agent",    icon: Bot,            label: "Agents" },
            ] as { id: SidebarTab; icon: React.FC<any>; label: string }[]
          ).map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`activity-btn ${sidebarTab === id ? "activity-btn--active" : ""}`}
              onClick={() => setSidebarTab(id)}
              title={label}
            >
              <Icon size={20} />
            </button>
          ))}
        </div>
        <div className="activity-bar__bottom">
          <button
            className={`activity-btn ${showAIPanel ? "activity-btn--active" : ""}`}
            onClick={() => setShowAIPanel((v) => !v)}
            title="Toggle AI Panel"
          >
            <MessageSquare size={20} />
          </button>
          <button 
            className={`activity-btn ${showSettings ? "activity-btn--active" : ""}`} 
            title="Settings"
            onClick={() => setShowSettings((v) => !v)}
          >
            <Settings size={20} />
          </button>
        </div>
      </div>

      {/* Main layout */}
      <div className="app__body">
        <PanelGroup direction="horizontal" className="app__panels">
          {/* Sidebar */}
          <Panel defaultSize={16} minSize={10} maxSize={35} className="app__sidebar">
            {sidebarTab === "explorer" && <FileExplorer />}
            {sidebarTab === "history"  && <ConversationList />}
            {sidebarTab === "infra"    && <InfraPanel />}
            {sidebarTab === "system"   && <SystemLogsPanel />}
            {sidebarTab === "search"   && <SearchPanel />}
            {sidebarTab === "git"      && <PlaceholderPanel label="Source Control" />}
            {sidebarTab === "skills"   && <SkillsPanel />}
            {sidebarTab === "agent"    && <PlaceholderPanel label="Agent Logs" />}
          </Panel>

          <ResizeHandle />

          {/* Editor + bottom terminal */}
          <Panel minSize={30}>
            <PanelGroup direction="vertical">
              <Panel minSize={25} className="app__editor">
                <PresenceBar />
                {showSettings ? <SettingsPanel /> : <EditorPane />}
              </Panel>

              {/* Bottom: Terminal */}
              <ResizeHandle vertical />
              <Panel defaultSize={25} minSize={10} className="app__bottom">
                <BottomPanel send={send} />
              </Panel>
            </PanelGroup>
          </Panel>

          {/* AI Panel */}
          {showAIPanel && (
            <>
              <ResizeHandle />
              <Panel defaultSize={24} minSize={16} maxSize={45} className="app__ai">
                <AIPanel send={send} conversationId={activeConversationId} />
              </Panel>
            </>
          )}
        </PanelGroup>

        {/* Status bar */}
        <div className="status-bar">
          <div className="status-bar__left">
            <span className={`status-ws status-ws--${wsStatus}`}>
              <Activity size={10} />
              {wsStatus === "connected" ? "Neurex connected" : wsStatus}
            </span>
          </div>
          <div className="status-bar__right">
            <span>UTF-8</span>
            <span>Spaces: 2</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ResizeHandle({ vertical = false }: { vertical?: boolean }) {
  return (
    <PanelResizeHandle className={`resize-handle ${vertical ? "resize-handle--vertical" : "resize-handle--horizontal"}`}>
      <div className="resize-handle__inner" />
    </PanelResizeHandle>
  );
}

function PlaceholderPanel({ label }: { label: string }) {
  return (
    <div className="placeholder-panel">
      <div className="placeholder-panel__label">{label.toUpperCase()}</div>
      <div className="placeholder-panel__hint">Coming soon</div>
    </div>
  );
}

function BottomPanel({ send }: { send: (p: any) => void }) {
  const [tab, setTab] = useState<"terminal" | "output">("terminal");
  const tasks = useStore((s) => s.tasks);
  
  const lines = Object.values(tasks)
    .filter((t) => t.result || t.error)
    .flatMap((t) => {
      const out = [];
      if (t.result) out.push(`[${t.agent_type}/${t.title}] ${t.result}`);
      if (t.error)  out.push(`[ERROR] ${t.error}`);
      return out;
    });

  return (
    <div className="bottom-panel">
      <div className="bottom-panel__header">
        <div className="bottom-panel__tabs">
          <button className={`bottom-tab ${tab === "terminal" ? "active" : ""}`} onClick={() => setTab("terminal")}>TERMINAL</button>
          <button className={`bottom-tab ${tab === "output" ? "active" : ""}`} onClick={() => setTab("output")}>OUTPUT</button>
        </div>
      </div>
      <div className="bottom-panel__content">
        {tab === "terminal" ? (
          <Terminal 
            onInput={(data) => send({ type: "terminal_input", data })}
            onResize={(rows, cols) => send({ type: "terminal_resize", rows, cols })}
          />
        ) : (
          <div className="output-log">
            {lines.length === 0 ? (
              <span className="bottom-panel__empty">No output yet.</span>
            ) : (
              lines.map((l, i) => <div key={i} className="bottom-panel__line">{l}</div>)
            )}
          </div>
        )}
      </div>
    </div>
  );
}
