import React, { useState, useEffect, useRef, useMemo } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import {
  Files, MessageSquare, Settings, GitBranch, Search, Bot, Activity, Clock, Cpu, Shield, Puzzle, Layout, AlertTriangle, BrainCircuit, Braces, Terminal as TerminalIcon, Plus, RefreshCw, LogOut, Moon, Sun, Save, X
} from "lucide-react";
import { FileExplorer } from "./components/FileExplorer/FileExplorer";
import { ConversationList } from "./components/ConversationList/ConversationList";
import { InfraPanel } from "./components/InfraPanel/InfraPanel";
import { SystemLogsPanel } from "./components/SystemLogs/SystemLogs";
import { SearchPanel } from "./components/SearchPanel/SearchPanel";
import { SourceControlPanel } from "./components/SourceControlPanel/SourceControlPanel";
import { EditorPane } from "./components/Editor/EditorPane";
import { AIPanel } from "./components/AIPanel/AIPanel";
import { AgentPanel } from "./components/AgentPanel/AgentPanel";
import { Terminal } from "./components/Terminal/Terminal";
import { SkillsPanel } from "./components/SkillsPanel/SkillsPanel";
import { SettingsPanel } from "./components/SettingsPanel/SettingsPanel";
import { HiveMindPanel } from "./components/HiveMindPanel/HiveMindPanel";
import { PresenceBar } from "./components/PresenceBar/PresenceBar";
import { AuthOverlay } from "./components/AuthOverlay/AuthOverlay";
import { MenuBar } from "./components/MenuBar/MenuBar";
import { CommandPalette } from "./components/CommandPalette/CommandPalette";
import { API_BASE } from "./lib/config";
import { useWebSocket } from "./hooks/useWebSocket";
import { useNotifications } from "./hooks/useNotifications";
import { useStore } from "./lib/store";
import { Toaster, toast } from "react-hot-toast";
import { UpdateNotifier } from "./components/UpdateNotifier/UpdateNotifier";
import { FlightRecorder } from "./components/FlightRecorder/FlightRecorder";
import { LoadingOverlay } from "./components/LoadingOverlay/LoadingOverlay";
import { ContextMenu } from "./components/ContextMenu/ContextMenu";
import { 
  DndContext, 
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import "./App.css";

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean, error: Error | null }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }
  componentDidCatch(error: Error, errorInfo: any) {
    console.error("Critical Failure:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <AlertTriangle size={48} className="text-red mb-4" />
          <h1 style={{ marginBottom: 4 }}>System Failure</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: 20 }}>Neurex encountered a critical rendering error.</p>
          <div style={{ textAlign: 'left', fontSize: 11, color: '#ff5555', padding: 16, background: 'rgba(255,0,0,0.05)', border: '1px solid rgba(255,0,0,0.2)', borderRadius: 4, maxWidth: 600, fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 400, overflow: 'auto' }}>
            <strong style={{ display: 'block', marginBottom: 8, fontSize: 13 }}>Cause: {this.state.error?.name}</strong>
            {this.state.error?.message}
          </div>
          <button className="btn btn--purple mt-4" onClick={() => window.location.reload()}>Reboot System</button>
        </div>
      );
    }
    return this.props.children;
  }
}

type SidebarTab = "explorer" | "search" | "git" | "agent" | "skills" | "history" | "infra" | "system";

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}

const SIDEBAR_ITEMS: { id: SidebarTab; icon: React.FC<any>; label: string }[] = [
  { id: "explorer", icon: Files,          label: "Explorer" },
  { id: "search",   icon: Search,         label: "Search" },
  { id: "git",      icon: GitBranch,      label: "Source Control" },
  { id: "history",  icon: Clock,          label: "History" },
  { id: "infra",    icon: Cpu,            label: "AI Infrastructure" },
  { id: "system",   icon: Shield,         label: "System Logs" },
  { id: "skills",   icon: Puzzle,         label: "Skills & Extensions" },
  { id: "agent",    icon: Bot,            label: "Agents" },
];

function SortableActivityItem({ id, active, onClick, icon: Icon, label, badge }: { id: string; active: boolean; onClick: () => void; icon: React.FC<any>; label: string; badge?: number | string }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="activity-item-wrapper">
      <button className={`activity-btn ${active ? "active" : ""}`} onClick={onClick} title={label}>
        <Icon size={20} />
        {badge && <span className="activity-badge animate-scale">{badge}</span>}
        {active && <div className="activity-indicator" />}
      </button>
    </div>
  );
}

function AppContent() {
  const [sidebarOrder, setSidebarOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem("neurex_sidebar_order");
    return saved ? JSON.parse(saved) : SIDEBAR_ITEMS.map(i => i.id);
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleSidebarDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setSidebarOrder((items) => {
        const oldIndex = items.indexOf(active.id as string);
        const newIndex = items.indexOf(over.id as string);
        const next = arrayMove(items, oldIndex, newIndex);
        localStorage.setItem("neurex_sidebar_order", JSON.stringify(next));
        return next;
      });
    }
  };

  useNotifications();
  const { 
    wsStatus, isInitialized, setIsInitialized, onboardingRequired, 
    token, activeConversationId, modalOpen, tasks, hiveStats, 
    theme, cursorPosition, openFiles, activeFile, setFileLanguage, logout, saveFile
  } = useStore();
  
  const [visualProgress, setVisualProgress] = useState(25);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>((localStorage.getItem("neurex_sidebar_tab") as SidebarTab) || "explorer");
  const [showAIPanel, setShowAIPanel] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showHiveMind, setShowHiveMind] = useState(false);
  const { send } = useWebSocket(activeConversationId);
  const sidebarRef = useRef<any>(null);

  // Command Palette States
  const [paletteMode, setPaletteMode] = useState<"none" | "language" | "indent" | "encoding" | "global">("none");

  useEffect(() => {
    const handleGlobalKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "P") {
        e.preventDefault();
        setPaletteMode("global");
      }
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "F") {
        e.preventDefault();
        updateSidebarTab("search");
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        if (activeFile) {
          saveFile(activeFile);
          toast.success("File Saved");
        }
      }
    };
    window.addEventListener("keydown", handleGlobalKey);
    return () => window.removeEventListener("keydown", handleGlobalKey);
  }, [activeFile, saveFile]);

  // ── Event Listeners (Bypass) ──
  useEffect(() => {
    const handleForce = () => setIsInitialized(true);
    window.addEventListener('neurex-force-start', handleForce);
    return () => window.removeEventListener('neurex-force-start', handleForce);
  }, [setIsInitialized]);

  // ── Onboarding / Auth Initialization ──
  useEffect(() => {
    const checkStatus = async () => {
      const state = useStore.getState();
      try {
        // 1. Always check onboarding status first
        const res = await fetch(`${API_BASE}/api/auth/onboarding/status`);
        const data = await res.json();
        state.setOnboardingRequired(data.onboarding_required);
        
        // 2. If we don't have a token, we are done with "loading" — show Auth/Onboarding
        if (!state.token || data.onboarding_required) {
          setVisualProgress(100);
          setIsInitialized(true);
          if ((window as any).hidePreloader) (window as any).hidePreloader();
          return;
        }

        // 3. If we DO have a token, proceed with full workspace initialization
        if (!isInitialized && !state.isInitializing) {
          state.setIsInitializing(true);
          const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error("Init Timeout")), 5000));
          try {
            await Promise.race([
              Promise.all([state.refreshFileTree(), state.refreshInfra()]),
              timeout
            ]);
          } catch (err) {
            console.warn("Workspace init timed out/failed", err);
          } finally {
            setVisualProgress(100);
            setIsInitialized(true);
            state.setIsInitializing(false);
            if ((window as any).hidePreloader) (window as any).hidePreloader();
          }
        }
      } catch (e) {
        console.error("System status check failed", e);
        setIsInitialized(true); // Fallback
      }
    };

    checkStatus();
  }, [token, onboardingRequired, isInitialized, setIsInitialized]);

  useEffect(() => {
    // Bounce back to 18% when switching tabs or clearing search
    if (sidebarTab !== "search" && sidebarTab !== "infra") {
      sidebarRef.current?.resize(18);
    }
  }, [sidebarTab]);

  const updateSidebarTab = (tab: SidebarTab) => {
    setSidebarTab(tab);
    localStorage.setItem("neurex_sidebar_tab", tab);
    setShowSettings(false); 
    setShowHiveMind(false);
  };

  const activeTaskCount = Object.values(tasks).filter(t => t.status === "THINKING" || t.status === "WRITING" || t.status === "TESTING").length;
  const activeFileLanguage = openFiles.find(f => f.path === activeFile)?.language || "plaintext";
  const isAIActive = Object.values(tasks).some(t => t.status === "THINKING" || t.status === "WRITING");

  const languageItems = useMemo(() => [
    "typescript", "javascript", "python", "css", "json", "markdown", "yaml", "html", "rust", "go"
  ].map(l => ({ id: l, label: l.toUpperCase(), action: () => activeFile && setFileLanguage(activeFile, l) })), [activeFile, setFileLanguage]);

  const globalCommands = [
    { id: "new-file", label: "File: New File", category: "General", action: () => {} },
    { id: "save-file", label: "File: Save", category: "General", action: () => activeFile && saveFile(activeFile) },
    { id: "view-explorer", label: "View: Show Explorer", category: "Navigation", action: () => updateSidebarTab("explorer") },
    { id: "view-git", label: "View: Show Source Control", category: "Navigation", action: () => updateSidebarTab("git") },
    { id: "view-search", label: "View: Show Search", category: "Navigation", action: () => updateSidebarTab("search") },
    { id: "toggle-ai", label: "View: Toggle AI Assistant", category: "View", action: () => setShowAIPanel(!showAIPanel) },
    { id: "toggle-settings", label: "View: Toggle Settings", category: "View", action: () => setShowSettings(!showSettings) },
    { id: "reload", label: "Developer: Reload Window", category: "Developer", action: () => window.location.reload() },
    { id: "logout", label: "Account: Logout", category: "Account", action: logout }
  ];

  try {
    return (
      <div className={`app ${modalOpen ? "modal-open" : ""}`}>
        {(!token || onboardingRequired) && <AuthOverlay />}
        {!isInitialized && <LoadingOverlay progress={visualProgress} />}
        
        <ContextMenu 
          targetSelector=".file-explorer-item"
          items={[
            { label: 'Open File', action: () => {} },
            { label: 'Reveal in Explorer', action: () => {} },
            { label: 'Copy Path', action: () => {} },
            { label: 'Delete File', action: () => {}, danger: true }
          ]}
        />

        <ContextMenu 
          targetSelector=".editor-pane"
          items={[
            { label: 'Format Document', action: () => {} },
            { label: 'Peek Definition', action: () => {} },
            { label: 'Refactor with AI', action: () => {} },
            { label: 'Stage Changes', action: () => {} }
          ]}
        />
        <CommandPalette 
          isOpen={paletteMode === "global"} 
          onClose={() => setPaletteMode("none")} 
          title="Global Commands"
          items={globalCommands}
          placeholder="Type a command to execute..."
        />
        <CommandPalette 
          isOpen={paletteMode === "language"} 
          onClose={() => setPaletteMode("none")} 
          title="Select Language Mode"
          items={languageItems}
        />

        <Toaster position="top-right" />
        
        <div className="app__root">
          <div className="app__main-layout">
            <div className="activity-bar">
              <div className="activity-bar__top">
                <MenuBar />
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleSidebarDragEnd}>
                  <SortableContext items={sidebarOrder} strategy={verticalListSortingStrategy}>
                    {sidebarOrder.map(id => {
                      const item = SIDEBAR_ITEMS.find(i => i.id === id);
                      if (!item) return null;
                      let badge = undefined;
                      if (id === "agent" && activeTaskCount > 0) badge = activeTaskCount;
                      return (
                        <SortableActivityItem
                          key={id} id={id} icon={item.icon} label={item.label}
                          active={sidebarTab === id && !showSettings && !showHiveMind}
                          onClick={() => updateSidebarTab(id as SidebarTab)}
                          badge={badge}
                        />
                      );
                    })}
                  </SortableContext>
                </DndContext>
              </div>
              <div className="activity-bar__bottom">
                <button className={`activity-btn ${showHiveMind ? "active" : ""}`} onClick={() => { setShowHiveMind(!showHiveMind); setShowSettings(false); }} title="Hive Mind (Knowledge Base)">
                  <BrainCircuit size={20} className="text-cyan" />
                  {showHiveMind && <div className="activity-indicator" />}
                </button>
                <button className={`activity-btn ${showAIPanel ? "active" : ""}`} onClick={() => setShowAIPanel(!showAIPanel)} title="Toggle AI Assistant (Cmd+L)">
                  <MessageSquare size={20} />
                </button>
                <button className={`activity-btn ${showSettings ? "active" : ""}`} onClick={() => { setShowSettings(!showSettings); setShowHiveMind(false); }} title="IDE Settings">
                  <Settings size={20} />
                  {showSettings && <div className="activity-indicator" />}
                </button>
              </div>
            </div>

            <div className="app__body">
              <PanelGroup direction="horizontal" className="app__panels">
                <Panel ref={sidebarRef} defaultSize={18} minSize={10} maxSize={40} className="app__sidebar">
                  {sidebarTab === "explorer" && <FileExplorer />}
                  {sidebarTab === "history"  && <ConversationList />}
                  {sidebarTab === "infra"    && <InfraPanel onExpand={(s) => sidebarRef.current?.resize(s)} currentSize={sidebarRef.current?.getSize() || 18} />}
                  {sidebarTab === "system"   && <SystemLogsPanel />}
                  {sidebarTab === "search"   && <SearchPanel onExpand={(s) => sidebarRef.current?.resize(s)} />}
                  {sidebarTab === "git"      && <SourceControlPanel />}
                  {sidebarTab === "skills"   && <SkillsPanel />}
                  {sidebarTab === "agent"    && <AgentPanel />}
                </Panel>
                <ResizeHandle />
                <Panel minSize={30} className="app__main-content">
                  <PanelGroup direction="vertical" className="app__v-panels">
                    <Panel minSize={20} className="app__editor-wrapper">
                      <PresenceBar />
                      {showSettings ? <SettingsPanel /> : showHiveMind ? <HiveMindPanel /> : <EditorPane />}
                    </Panel>
                    <ResizeHandle vertical />
                    <Panel defaultSize={25} minSize={5} className="app__bottom-wrapper">
                      <BottomPanel send={send} />
                    </Panel>
                  </PanelGroup>
                </Panel>
                {showAIPanel && (
                  <>
                    <ResizeHandle />
                    <Panel defaultSize={25} minSize={15} maxSize={45} className="app__ai-wrapper">
                      <AIPanel send={send} conversationId={activeConversationId} isActive={showAIPanel} />
                    </Panel>
                  </>
                )}
              </PanelGroup>

              <div className="status-bar">
                <div className="status-bar__left">
                  <span className="status-ws status-ws--connected" title="Mesh Network: Connected">
                    <Activity size={10} />
                    <span>NEUREX MESH ACTIVE</span>
                  </span>
                  <div className="status-intel" title="Hive Statistics">
                    <div className="swarm-pulse swarm-pulse--active" />
                    <span>{hiveStats.total_nodes} NODES ACTIVE</span>
                  </div>
                </div>
                <div className="status-bar__right">
                  <div className="status-segments">
                    <span className="status-segment" title="Cursor Position">Ln {cursorPosition.line}, Col {cursorPosition.ch}</span>
                    <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("indent")} title="Select Indentation">Spaces: 2</button>
                    <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("encoding")} title="Select Encoding">UTF-8</button>
                    <button className="status-segment" title="End of Line Sequence">LF</button>
                    <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("language")} title="Select Language Mode">
                      <Braces size={10} />
                      <span>{activeFileLanguage.toUpperCase()}</span>
                    </button>
                    {isAIActive && (
                      <button className="status-segment animate-pulse" title="Neurex is composing...">
                        <Activity size={10} className="text-cyan" />
                        <span>Compose</span>
                      </button>
                    )}
                  </div>
                  <UpdateNotifier />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  } catch (err) {
    console.error("AppContent Error:", err);
    throw err;
  }
}

function ResizeHandle({ vertical = false }: { vertical?: boolean }) {
  return (
    <PanelResizeHandle className={`resize-handle ${vertical ? "resize-handle--vertical" : "resize-handle--horizontal"}`}>
      <div className="resize-handle__highlight" />
    </PanelResizeHandle>
  );
}

function BottomPanel({ send }: { send: (p: any) => void }) {
  const [activeTab, setActiveTab] = useState<"terminal" | "output" | "flight">("terminal");
  const { terminalSessions, activeTerminalId, setActiveTerminalId, addTerminalSession, closeTerminalSession, tasks } = useStore();
  
  const lines = Object.values(tasks).filter((t) => t.result || t.error).flatMap((t) => {
    const out = [];
    if (t.result) out.push(`[${t.agent_type}] ${t.result}`);
    if (t.error)  out.push(`[ERROR] ${t.error}`);
    return out;
  });

  return (
    <div className="bottom-panel">
      <div className="bottom-panel__header">
        <div className="bottom-panel__tabs">
          <button className={`bottom-tab ${activeTab === "terminal" ? "active" : ""}`} onClick={() => setActiveTab("terminal")} title="Integrated Terminal">TERMINAL</button>
          <button className={`bottom-tab ${activeTab === "output" ? "active" : ""}`} onClick={() => setActiveTab("output")} title="Build & Task Output">OUTPUT</button>
          <button className={`bottom-tab ${activeTab === "flight" ? "active" : ""}`} onClick={() => setActiveTab("flight")} title="AI Flight Recorder">FLIGHT LOG</button>
        </div>
        
        {activeTab === "terminal" && (
          <div className="terminal-session-switcher">
            {terminalSessions.map((s) => (
              <div key={s.id} className={`terminal-tab ${activeTerminalId === s.id ? "active" : ""}`} onClick={() => setActiveTerminalId(s.id)}>
                <span className="terminal-tab__name">{s.name}</span>
                {terminalSessions.length > 1 && (
                  <button className="terminal-tab__close" onClick={(e) => { e.stopPropagation(); closeTerminalSession(s.id); }}><X size={10} /></button>
                )}
              </div>
            ))}
            <button className="terminal-add-btn" onClick={() => addTerminalSession()} title="New Terminal"><Plus size={14} /></button>
          </div>
        )}
      </div>
      <div className="bottom-panel__content">
        <div className="bottom-panel__tab-content" hidden={activeTab !== "terminal"}>
          <Terminal 
            sessionId={activeTerminalId}
            onInput={(data) => send({ type: "terminal_input", sessionId: activeTerminalId, data })} 
            onResize={(rows, cols) => send({ type: "terminal_resize", sessionId: activeTerminalId, rows, cols })} 
          />
        </div>
        <div className="bottom-panel__tab-content output-log" hidden={activeTab !== "output"}>
          {lines.map((l, i) => <div key={i} className="bottom-panel__line">{l}</div>)}
        </div>
      </div>
    </div>
  );
}
