import React, { useState, useEffect, useRef } from "react";
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
import { AgentPanel } from "./components/AgentPanel/AgentPanel";
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
          
          <div style={{ 
            textAlign: 'left', 
            fontSize: 11, 
            color: '#ff5555', 
            padding: 16, 
            background: 'rgba(255,0,0,0.05)', 
            border: '1px solid rgba(255,0,0,0.2)',
            borderRadius: 4,
            maxWidth: 600,
            fontFamily: 'var(--font-mono)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            maxHeight: 400,
            overflow: 'auto'
          }}>
            <strong style={{ display: 'block', marginBottom: 8, fontSize: 13 }}>Cause: {this.state.error?.name}</strong>
            {this.state.error?.message}
            <div style={{ marginTop: 12, opacity: 0.6, fontSize: 10 }}>
              {this.state.error?.stack}
            </div>
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

function SortableActivityItem(props: { id: string; active: boolean; onClick: () => void; icon: React.FC<any>; label: string }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: props.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : 1,
    cursor: 'grab'
  };

  const Icon = props.icon;

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <button
        className={`activity-btn ${props.active ? "activity-btn--active" : ""}`}
        onClick={props.onClick}
        title={props.label}
      >
        <Icon size={20} />
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
  const wsStatus = useStore(s => s.wsStatus);
  const refreshFileTree = useStore(s => s.refreshFileTree);
  const refreshInfra = useStore(s => s.refreshInfra);
  
  const [targetProgress, setTargetProgress] = useState(10);
  const [visualProgress, setVisualProgress] = useState(0);
  const [isInitialized, setIsInitialized] = useState(false);

  // Smooth visual progress catch-up
  useEffect(() => {
    if (visualProgress < targetProgress) {
      const timer = setTimeout(() => {
        setVisualProgress(prev => Math.min(prev + 1, targetProgress));
      }, 10);
      return () => clearTimeout(timer);
    }
  }, [visualProgress, targetProgress]);

  const [sidebarTab, setSidebarTab] = useState<SidebarTab>(
    (localStorage.getItem("neurex_sidebar_tab") as SidebarTab) || "explorer"
  );

  const updateSidebarTab = (tab: SidebarTab) => {
    setSidebarTab(tab);
    localStorage.setItem("neurex_sidebar_tab", tab);
    setShowSettings(false); 
    setShowHiveMind(false);
  };
  const [showAIPanel, setShowAIPanel] = useState(window.innerWidth > 768);
  const [mobileTab, setMobileTab] = useState<MobileTab>("chat");
  const [showSettings, setShowSettings] = useState(false);
  const [showHiveMind, setShowHiveMind] = useState(false);
  const activeConversationId = useStore((s) => s.activeConversationId);

  const { send } = useWebSocket(activeConversationId);

  const initializedRef = useRef(false);

  // Workspace Initialization
  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    const init = async () => {
      const state = useStore.getState();
      // Start a steady ramp towards 40% immediately
      const rampInterval = setInterval(() => {
        setTargetProgress(prev => prev < 40 ? prev + 2 : prev);
      }, 100);

      try {
        await Promise.all([
          state.refreshFileTree(),
          state.refreshInfra()
        ]);
        setTargetProgress(70);
        
        // Finalize
        setTimeout(() => {
          setTargetProgress(100);
        }, 300);
      } finally {
        clearInterval(rampInterval);
      }
    };
    init();
  }, []);

  // Finish initialization only when visual progress reaches 100
  useEffect(() => {
    if (visualProgress === 100 && !isInitialized) {
      const t = setTimeout(() => setIsInitialized(true), 400);
      return () => clearTimeout(t);
    }
  }, [visualProgress, isInitialized]);

  const toggleSettings = () => {
    setShowSettings(v => !v);
    setShowHiveMind(false);
  };

  const toggleHiveMind = () => {
    setShowHiveMind(v => !v);
    setShowSettings(false);
  };

  const sidebarRef = useRef<any>(null);

  const handleInfraExpand = React.useCallback((size: number) => {
    sidebarRef.current?.resize(size);
  }, []);

  useEffect(() => {
    (window as any).hideOverlays = () => {
      setShowSettings(false);
      setShowHiveMind(false);
    };
  }, []);

  try {

  return (
    <div className="app">
      {!isInitialized && <LoadingOverlay progress={visualProgress} />}
      <Toaster position="top-right" toastOptions={{ 
        style: { 
          background: '#1e1e24', 
          color: '#e8e8f0', 
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)'
        } 
      }} />
      
      {/* Activity bar (Hidden on mobile) */}
      <div className="activity-bar">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleSidebarDragEnd}>
          <div className="activity-bar__top">
            <div className="activity-bar__logo">⬡</div>
            <SortableContext items={sidebarOrder} strategy={verticalListSortingStrategy}>
              {sidebarOrder.map(id => {
                const item = SIDEBAR_ITEMS.find(i => i.id === id);
                if (!item) return null;
                return (
                  <SortableActivityItem
                    key={id}
                    id={id}
                    icon={item.icon}
                    label={item.label}
                    active={sidebarTab === id}
                    onClick={() => updateSidebarTab(id as SidebarTab)}
                  />
                );
              })}
            </SortableContext>
          </div>
        </DndContext>
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
            ref={sidebarRef}
            defaultSize={16} minSize={10} maxSize={45} 
            className={`app__sidebar ${mobileTab === "explorer" ? "mobile-visible" : ""}`}
          >
            {sidebarTab === "explorer" && <FileExplorer />}
            {sidebarTab === "history"  && <ConversationList />}
            {sidebarTab === "infra"    && (
              <InfraPanel 
                onExpand={handleInfraExpand} 
                currentSize={sidebarRef.current?.getSize() || 16}
              />
            )}
            {sidebarTab === "system"   && <SystemLogsPanel />}
            {sidebarTab === "search"   && <SearchPanel />}
            {sidebarTab === "git"      && <PlaceholderPanel label="Source Control" />}
            {sidebarTab === "skills"   && <SkillsPanel />}
            {sidebarTab === "agent"    && <AgentPanel />}
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
  } catch (err) {
    console.error("AppContent Render Error:", err);
    throw err;
  }
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
        <div className="bottom-panel__tab-content" hidden={tab !== "terminal"}>
          <Terminal 
            onInput={(data) => send({ type: "terminal_input", data })}
            onResize={(rows, cols) => send({ type: "terminal_resize", rows, cols })}
          />
        </div>
        <div className="bottom-panel__tab-content output-log" hidden={tab !== "output"}>
          {lines.length === 0 ? (
            <span className="bottom-panel__empty">No output yet.</span>
          ) : (
            lines.map((l, i) => <div key={i} className="bottom-panel__line">{l}</div>)
          )}
        </div>
      </div>
    </div>
  );
}
