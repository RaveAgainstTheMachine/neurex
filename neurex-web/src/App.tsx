import React, { useState, useEffect, useRef, useMemo } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import {
  Files, MessageSquare, Settings, GitBranch, Search, Bot, Activity, Clock, Cpu, Shield, Puzzle, Layout, AlertTriangle, BrainCircuit, Braces
} from "lucide-react";
import { FileExplorer } from "./components/FileExplorer/FileExplorer";
import { ConversationList } from "./components/ConversationList/ConversationList";
import { InfraPanel } from "./components/InfraPanel/InfraPanel";
import { SystemLogsPanel } from "./components/SystemLogs/SystemLogs";
import { SearchPanel } from "./components/SearchPanel/SearchPanel";
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
import { useWebSocket } from "./hooks/useWebSocket";
import { useNotifications } from "./hooks/useNotifications";
import { useStore } from "./lib/store";
import { Toaster } from "react-hot-toast";
import { UpdateNotifier } from "./components/UpdateNotifier/UpdateNotifier";
import { FlightRecorder } from "./components/FlightRecorder/FlightRecorder";
import { LoadingOverlay } from "./components/LoadingOverlay/LoadingOverlay";
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
type MobileTab = "chat" | "editor" | "terminal" | "explorer";

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
  { id: "history",  icon: Clock,          label: "History" },
  { id: "infra",    icon: Cpu,            label: "AI Infrastructure" },
  { id: "system",   icon: Shield,         label: "System Logs" },
  { id: "git",      icon: GitBranch,      label: "Source Control" },
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
    infraMetrics, theme, cursorPosition, openFiles, activeFile, setFileLanguage 
  } = useStore();
  
  const [visualProgress, setVisualProgress] = useState(25);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>((localStorage.getItem("neurex_sidebar_tab") as SidebarTab) || "explorer");
  const [showAIPanel, setShowAIPanel] = useState(window.innerWidth > 768);
  const [mobileTab, setMobileTab] = useState<MobileTab>("chat");
  const [showSettings, setShowSettings] = useState(false);
  const [showHiveMind, setShowHiveMind] = useState(false);
  const { send } = useWebSocket(activeConversationId);
  const sidebarRef = useRef<any>(null);

  // Command Palette States
  const [paletteMode, setPaletteMode] = useState<"none" | "language" | "indent" | "encoding">("none");

  useEffect(() => {
    if (!token || onboardingRequired || isInitialized || useStore.getState().isInitializing) return;
    const init = async () => {
      const state = useStore.getState();
      state.setIsInitializing(true);
      try {
        await Promise.all([state.refreshFileTree(), state.refreshInfra()]);
        setVisualProgress(100);
        setIsInitialized(true);
        if ((window as any).hidePreloader) (window as any).hidePreloader();
      } catch (err) {
        setVisualProgress(100);
        setIsInitialized(true);
      } finally {
        state.setIsInitializing(false);
      }
    };
    init();
  }, [token, onboardingRequired, isInitialized, setIsInitialized]);

  useEffect(() => {
    if (!token || onboardingRequired) {
      if ((window as any).hidePreloader) (window as any).hidePreloader();
    }
  }, [token, onboardingRequired]);

  const updateSidebarTab = (tab: SidebarTab) => {
    setSidebarTab(tab);
    localStorage.setItem("neurex_sidebar_tab", tab);
    setShowSettings(false); 
    setShowHiveMind(false);
  };

  const activeTaskCount = Object.values(tasks).filter(t => t.status === "THINKING" || t.status === "WRITING" || t.status === "TESTING").length;
  const activeFileLanguage = openFiles.find(f => f.path === activeFile)?.language || "plaintext";

  const languageItems = useMemo(() => [
    "typescript", "javascript", "python", "css", "json", "markdown", "yaml", "html", "rust", "go"
  ].map(l => ({ id: l, label: l.toUpperCase(), action: () => activeFile && setFileLanguage(activeFile, l) })), [activeFile, setFileLanguage]);

  const indentItems = [
    { id: "2", label: "Spaces: 2", action: () => {} },
    { id: "4", label: "Spaces: 4", action: () => {} },
    { id: "tabs", label: "Tabs", action: () => {} }
  ];

  const encodingItems = [
    { id: "utf8", label: "UTF-8", action: () => {} },
    { id: "ascii", label: "ASCII", action: () => {} }
  ];

  try {
    return (
      <div className={`app ${modalOpen ? "modal-open" : ""}`}>
        {(!token || onboardingRequired) && <AuthOverlay />}
        {!isInitialized && <LoadingOverlay progress={visualProgress} />}
        
        <CommandPalette 
          isOpen={paletteMode === "language"} 
          onClose={() => setPaletteMode("none")} 
          title="Select Language Mode"
          items={languageItems}
        />
        <CommandPalette 
          isOpen={paletteMode === "indent"} 
          onClose={() => setPaletteMode("none")} 
          title="Select Indentation"
          items={indentItems}
        />
        <CommandPalette 
          isOpen={paletteMode === "encoding"} 
          onClose={() => setPaletteMode("none")} 
          title="Select Encoding"
          items={encodingItems}
        />

        <Toaster position="top-right" toastOptions={{ style: { background: '#1e1e24', color: '#e8e8f0', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' } }} />
        
        <div className="app__root">
          <div className="app__main-layout">
            <div className="activity-bar">
              <div className="activity-bar__top">
                <MenuBar />
                <div className="activity-bar__logo" onClick={() => window.location.reload()}>⬡</div>
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
                <button className={`activity-btn ${showHiveMind ? "active" : ""}`} onClick={() => { setShowHiveMind(!showHiveMind); setShowSettings(false); }} title="Hive Mind">
                  <BrainCircuit size={20} className="text-cyan" />
                  {showHiveMind && <div className="activity-indicator" />}
                </button>
                <button className={`activity-btn ${showAIPanel ? "active" : ""}`} onClick={() => setShowAIPanel(!showAIPanel)} title="Toggle AI Panel">
                  <MessageSquare size={20} />
                </button>
                <button className={`activity-btn ${showSettings ? "active" : ""}`} onClick={() => { setShowSettings(!showSettings); setShowHiveMind(false); }} title="Settings">
                  <Settings size={20} />
                  {showSettings && <div className="activity-indicator" />}
                </button>
              </div>
            </div>

            <div className="app__body">
              <PanelGroup autoSaveId="neurex-main-layout-h" direction="horizontal" className="app__panels">
                <Panel ref={sidebarRef} defaultSize={16} minSize={10} maxSize={45} className={`app__sidebar ${mobileTab === "explorer" ? "mobile-visible" : ""}`}>
                  {sidebarTab === "explorer" && <FileExplorer />}
                  {sidebarTab === "history"  && <ConversationList />}
                  {sidebarTab === "infra"    && <InfraPanel onExpand={(s) => sidebarRef.current?.resize(s)} currentSize={sidebarRef.current?.getSize() || 16} />}
                  {sidebarTab === "system"   && <SystemLogsPanel />}
                  {sidebarTab === "search"   && <SearchPanel />}
                  {sidebarTab === "skills"   && <SkillsPanel />}
                  {sidebarTab === "agent"    && <AgentPanel />}
                </Panel>
                <ResizeHandle />
                <Panel minSize={30} className="app__main-content">
                  <PanelGroup autoSaveId="neurex-main-layout-v" direction="vertical" className="app__v-panels">
                    <Panel minSize={25} className="app__editor-wrapper">
                      <PresenceBar />
                      {showSettings ? <SettingsPanel /> : showHiveMind ? <HiveMindPanel /> : <EditorPane />}
                    </Panel>
                    <ResizeHandle vertical />
                    <Panel defaultSize={25} minSize={10} className="app__bottom-wrapper">
                      <BottomPanel send={send} />
                    </Panel>
                  </PanelGroup>
                </Panel>
                {showAIPanel && (
                  <>
                    <ResizeHandle />
                    <Panel defaultSize={24} minSize={16} maxSize={45} className="app__ai-wrapper">
                      <AIPanel send={send} conversationId={activeConversationId} isActive={showAIPanel} />
                    </Panel>
                  </>
                )}
              </PanelGroup>

              <div className="status-bar">
                <div className="status-bar__left">
                  <span className={`status-ws status-ws--${wsStatus}`} title={`WebSocket: ${wsStatus}`}>
                    <Activity size={10} />
                    <span className="hide-mobile">{wsStatus === "connected" ? "NEUREX MESH ACTIVE" : wsStatus.toUpperCase()}</span>
                  </span>
                  <div className="status-intel">
                    <div className={`swarm-pulse ${hiveStats.total_nodes > 0 && theme.enable_swarm_glow ? 'swarm-pulse--active' : ''}`} />
                    <span className="hide-mobile">{hiveStats.total_nodes} NODES</span>
                  </div>
                </div>
                <div className="status-bar__right">
                  <div className="status-segments">
                    <span className="status-segment">Ln {cursorPosition.line}, Col {cursorPosition.ch}</span>
                    <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("indent")}>Spaces: 2</button>
                    <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("encoding")}>UTF-8</button>
                    <button className="status-segment">LF</button>
                    <button className="status-segment status-segment--interactive" onClick={() => setPaletteMode("language")}>
                      <Braces size={10} />
                      <span>{activeFileLanguage.toUpperCase()}</span>
                    </button>
                    <button className="status-segment">
                      <Activity size={10} className="text-cyan" />
                      <span>Compose</span>
                    </button>
                  </div>
                  <UpdateNotifier />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mobile-nav">
          <button className={`mobile-nav-btn ${mobileTab === "chat" ? "active" : ""}`} onClick={() => setMobileTab("chat")}><MessageSquare size={20} /><span>Chat</span></button>
          <button className={`mobile-nav-btn ${mobileTab === "editor" ? "active" : ""}`} onClick={() => setMobileTab("editor")}><Layout size={20} /><span>Code</span></button>
          <button className={`mobile-nav-btn ${mobileTab === "terminal" ? "active" : ""}`} onClick={() => setMobileTab("terminal")}><Activity size={20} /><span>Run</span></button>
          <button className={`mobile-nav-btn ${mobileTab === "explorer" ? "active" : ""}`} onClick={() => setMobileTab("explorer")}><Files size={20} /><span>Files</span></button>
        </div>
      </div>
    );
  } catch (err) {
    console.error("AppContent Render Error:", err);
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
  const [tab, setTab] = useState<"terminal" | "output" | "flight">("terminal");
  const activeConversationId = useStore(s => s.activeConversationId);
  const tasks = useStore((s) => s.tasks);
  const lines = Object.values(tasks).filter((t) => t.result || t.error).flatMap((t) => {
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
          <button className={`bottom-tab ${tab === "flight" ? "active" : ""}`} onClick={() => setTab("flight")}>FLIGHT LOG</button>
        </div>
      </div>
      <div className="bottom-panel__content">
        <div className="bottom-panel__tab-content" hidden={tab !== "terminal"}><Terminal onInput={(data) => send({ type: "terminal_input", data })} onResize={(rows, cols) => send({ type: "terminal_resize", rows, cols })} /></div>
        <div className="bottom-panel__tab-content output-log" hidden={tab !== "output"}>{lines.length === 0 ? <span className="bottom-panel__empty">No output yet.</span> : lines.map((l, i) => <div key={i} className="bottom-panel__line">{l}</div>)}</div>
        <div className="bottom-panel__tab-content" hidden={tab !== "flight"}>{activeConversationId ? <FlightRecorder conversationId={activeConversationId} isActive={tab === "flight"} /> : <div className="flight-empty">Select a conversation to view reasoning traces.</div>}</div>
      </div>
    </div>
  );
}
