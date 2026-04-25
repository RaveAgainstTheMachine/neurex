import React, { useState, useEffect } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import {
  Files, MessageSquare, Settings, GitBranch, Search, Bot, Activity, Clock, Cpu, Shield, Puzzle, Layout, AlertTriangle
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
import { HiveMindPanel } from "./components/HiveMindPanel/HiveMindPanel";
import { PresenceBar } from "./components/PresenceBar/PresenceBar";
import { useWebSocket } from "./hooks/useWebSocket";
import { useNotifications } from "./hooks/useNotifications";
import { useStore } from "./lib/store";
import { Toaster } from "react-hot-toast";
import { BrainCircuit } from "lucide-react";
import { UpdateNotifier } from "./components/UpdateNotifier/UpdateNotifier";
import "./App.css";

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <AlertTriangle size={48} className="text-red mb-4" />
          <h1>System Failure</h1>
          <p>Neurex encountered a critical rendering error.</p>
          <button className="btn btn--purple mt-4" onClick={() => window.location.reload()}>Reboot System</button>
        </div>
      );
    }
    return this.props.children;
  }
}

type SidebarTab = "explorer" | "search" | "git" | "agent" | "skills" | "history" | "infra" | "system";
type MobileTab = "chat" | "editor" | "terminal" | "explorer";

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}

function AppContent() {
  useNotifications();
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("explorer");
  const [showAIPanel, setShowAIPanel] = useState(window.innerWidth > 768);
  const [mobileTab, setMobileTab] = useState<MobileTab>("chat");
  const [showSettings, setShowSettings] = useState(false);
  const [showHiveMind, setShowHiveMind] = useState(false);
  const wsStatus = useStore((s) => s.wsStatus);
  const activeConversationId = useStore((s) => s.activeConversationId);

  const { send } = useWebSocket(activeConversationId);

  // Handle window resizing
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) setShowAIPanel(true);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleSettings = () => {
    setShowSettings(v => !v);
    setShowHiveMind(false);
  };

  const toggleHiveMind = () => {
    setShowHiveMind(v => !v);
    setShowSettings(false);
  };

  // Global handle for store to close overlays
  useEffect(() => {
    (window as any).hideOverlays = () => {
      setShowSettings(false);
      setShowHiveMind(false);
    };
  }, []);

  return (
    <div className="app">
      <Toaster position="top-right" toastOptions={{ 
        style: { background: '#1e1e24', color: '#e8e8f0', border: '1px solid var(--border)' } 
      }} />
      
      {/* Activity bar (Hidden on mobile) */}
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
              onClick={() => { setSidebarTab(id); setShowSettings(false); setShowHiveMind(false); }}
              title={label}
            >
              <Icon size={20} />
            </button>
          ))}
        </div>
        <div className="activity-bar__bottom">
          <button
            className={`activity-btn ${showHiveMind ? "activity-btn--active" : ""}`}
            onClick={toggleHiveMind}
            title="Hive Mind (Collective Memory)"
          >
            <BrainCircuit size={20} className="text-cyan" />
          </button>
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
            onClick={toggleSettings}
          >
            <Settings size={20} />
          </button>
        </div>
      </div>

      {/* Main layout */}
      <div className="app__body">
        <PanelGroup direction="horizontal" className="app__panels">
          {/* Sidebar */}
          <Panel 
            defaultSize={16} minSize={10} maxSize={35} 
            className={`app__sidebar ${mobileTab === "explorer" ? "mobile-visible" : ""}`}
          >
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
          <Panel 
            minSize={30} 
            className={`app__main-panel ${mobileTab === "editor" || mobileTab === "terminal" ? "mobile-visible" : ""}`}
          >
            <PanelGroup direction="vertical">
              <Panel 
                minSize={25} 
                className={`app__editor ${mobileTab === "editor" ? "mobile-visible" : ""}`}
              >
                <PresenceBar />
                {showSettings ? <SettingsPanel /> : showHiveMind ? <HiveMindPanel /> : <EditorPane />}
              </Panel>

              {/* Bottom: Terminal */}
              <ResizeHandle vertical />
              <Panel 
                defaultSize={25} minSize={10} 
                className={`app__bottom ${mobileTab === "terminal" ? "mobile-visible" : ""}`}
              >
                <BottomPanel send={send} />
              </Panel>
            </PanelGroup>
          </Panel>

          {/* AI Panel */}
          {(showAIPanel || mobileTab === "chat") && (
            <>
              <ResizeHandle />
              <Panel 
                defaultSize={24} minSize={16} maxSize={45} 
                className={`app__ai ${mobileTab === "chat" ? "mobile-visible" : ""}`}
              >
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
              <span className="hide-mobile">{wsStatus === "connected" ? "Neurex connected" : wsStatus}</span>
            </span>
          </div>
          <div className="status-bar__right">
            <UpdateNotifier />
            <span className="hide-mobile">UTF-8</span>
            <span className="hide-mobile">Spaces: 2</span>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="mobile-nav">
          <button className={`mobile-nav-btn ${mobileTab === "chat" ? "active" : ""}`} onClick={() => setMobileTab("chat")}>
            <MessageSquare size={20} />
            <span>Chat</span>
          </button>
          <button className={`mobile-nav-btn ${mobileTab === "editor" ? "active" : ""}`} onClick={() => setMobileTab("editor")}>
            <Layout size={20} />
            <span>Code</span>
          </button>
          <button className={`mobile-nav-btn ${mobileTab === "terminal" ? "active" : ""}`} onClick={() => setMobileTab("terminal")}>
            <Activity size={20} />
            <span>Run</span>
          </button>
          <button className={`mobile-nav-btn ${mobileTab === "explorer" ? "active" : ""}`} onClick={() => setMobileTab("explorer")}>
            <Files size={20} />
            <span>Files</span>
          </button>
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
