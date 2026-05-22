import React, { useState, useEffect, useRef, useMemo } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { DynamicRenderer, UIBlueprint } from './components/DynamicUI/DynamicRenderer';
import { StatusBar } from "./components/StatusBar/StatusBar";
import { BottomPanel } from "./components/BottomPanel/BottomPanel";
import { FileExplorer } from "./components/FileExplorer/FileExplorer";
import { ActivityBar } from "./components/ActivityBar/ActivityBar";
import { ConversationList } from "./components/ConversationList/ConversationList";
import { InfraPanel } from "./components/InfraPanel/InfraPanel";
import { SystemLogsPanel } from "./components/SystemLogs/SystemLogs";
import { SearchPanel } from "./components/SearchPanel/SearchPanel";
import { SourceControlPanel } from "./components/SourceControlPanel/SourceControlPanel";
import { EditorPane } from "./components/Editor/EditorPane";
import { AIPanel } from "./components/AIPanel/AIPanel";
import { AgentPanel } from "./components/AgentPanel/AgentPanel";
import { SkillsPanel } from "./components/SkillsPanel/SkillsPanel";
import { GitTimeline } from "./components/GitTimeline/GitTimeline";
import { SettingsPanel } from "./components/SettingsPanel/SettingsPanel";
import { AboutPanel } from "./components/AboutPanel/AboutPanel";
import { PresenceBar } from "./components/PresenceBar/PresenceBar";
import { AuthOverlay } from "./components/AuthOverlay/AuthOverlay";
import { TitleBar } from "./components/TitleBar/TitleBar";
import { CommandPalette } from "./components/CommandPalette/CommandPalette";
import { API_BASE } from "./lib/config";
import { useWebSocket } from "./hooks/useWebSocket";
import { useNotifications } from "./hooks/useNotifications";
import { useGlobalShortcuts } from "./hooks/useGlobalShortcuts";
import { useStore } from "./lib/store";
import { Toaster } from "react-hot-toast";
import { LoadingOverlay } from "./components/LoadingOverlay/LoadingOverlay";
import { MobileView } from "./components/MobileView/MobileView";
import { ContextMenu } from "./components/ContextMenu/ContextMenu";
import { SwarmDiffSidebar } from "./components/SwarmDiff/SwarmDiffSidebar";
import { DebateArena } from "./components/DebateArena/DebateArena";
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

type SidebarTab = "explorer" | "search" | "git" | "agent" | "skills" | "history" | "timeline" | "infra" | "system" | "swarm" | "debate";

export default function App() {
  const [blueprint, setBlueprint] = useState<UIBlueprint | null>(null);
  
  // Listen for Dynamic UI updates
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'UI_BLUEPRINT') {
          setBlueprint(data.payload);
        }
      } catch (e) {}
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  return (
    <ErrorBoundary>
      <div className="h-screen w-screen bg-obsidian text-white overflow-hidden flex flex-col font-inter">
        {/* Dynamic UI Overlay (Phase 42) */}
        {blueprint && (
          <div className="fixed inset-0 z-50 bg-obsidian/80 backdrop-blur-xl flex items-center justify-center p-12">
            <div className="max-w-4xl w-full bg-void border border-white/5 rounded-3xl shadow-2xl overflow-y-auto max-h-[80vh]">
              <button 
                className="absolute top-6 right-6 text-white/20 hover:text-white"
                onClick={() => setBlueprint(null)}
              >
                [ CLOSE ]
              </button>
              <DynamicRenderer blueprint={blueprint} />
            </div>
          </div>
        )}
        <AppContent />
      </div>
    </ErrorBoundary>
  );
}

function AppContent() {
  useNotifications();

  // Phase 44.21: Architectural State Decoupling (Stabilize Root Layout)
  const wsStatus = useStore(s => s.wsStatus);
  const isInitialized = useStore(s => s.isInitialized);
  const setIsInitialized = useStore(s => s.setIsInitialized);
  const onboardingRequired = useStore(s => s.onboardingRequired);
  const token = useStore(s => s.token);
  const activeConversationId = useStore(s => s.activeConversationId);
  const theme = useStore(s => s.theme);
  const refreshFileTree = useStore(s => s.refreshFileTree);
  const refreshGitStatus = useStore(s => s.refreshGitStatus);
  const sidebarTab = useStore(s => s.sidebarTab);
  const setSidebarTab = useStore(s => s.setSidebarTab);
  const showAIPanel = useStore(s => s.showAIPanel);
  const setShowAIPanel = useStore(s => s.setShowAIPanel);
  const showSettings = useStore(s => s.showSettings);
  const setShowSettings = useStore(s => s.setShowSettings);
  const showAbout = useStore(s => s.showAbout);
  const setShowAbout = useStore(s => s.setShowAbout);
  const settings = useStore(s => s.settings);
  const tasks = useStore(s => s.tasks);
  const activeFile = useStore(s => s.activeFile);
  const setFileLanguage = useStore(s => s.setFileLanguage);
  const saveFile = useStore(s => s.saveFile);
  const modalOpen = useStore(s => s.modalOpen);
  const setModalOpen = useStore(s => s.setModalOpen);
  const addTerminalSession = useStore(s => s.addTerminalSession);
  const clearActiveTerminal = useStore(s => s.clearActiveTerminal);
  const closeTerminalSession = useStore(s => s.closeTerminalSession);
  const activeTerminalId = useStore(s => s.activeTerminalId);
  const runActiveFile = useStore(s => s.runActiveFile);
  const logout = useStore(s => s.logout);
  const editorPanes = useStore(s => s.editorPanes);
  
  // ── Poll Git Status ──
  useEffect(() => {
    if (token) {
      refreshGitStatus();
      const timer = setInterval(refreshGitStatus, 30000); // 30s
      return () => clearInterval(timer);
    }
  }, [token, refreshGitStatus]);

  const [visualProgress, setVisualProgress] = useState(25);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  
  const { send } = useWebSocket(activeConversationId);
  useEffect(() => {
    useStore.setState({ send });
  }, [send]);

  const sidebarRef = useRef<any>(null);
  const handleSidebarResize = React.useCallback((size: number) => {
    sidebarRef.current?.resize(size);
  }, []);

  useEffect(() => {
    if (theme) {
      document.documentElement.style.setProperty('--accent-primary', theme.accent_color);
      document.documentElement.style.setProperty('--accent-primary-glow', theme.glow_color);
      document.documentElement.style.setProperty('--accent-purple', theme.accent_color);
      document.documentElement.style.setProperty('--glow-purple', theme.glow_color);
    }
  }, [theme]);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Command Palette States
  const [paletteMode, setPaletteMode] = useState<"none" | "language" | "indent" | "encoding" | "global">("none");

  useGlobalShortcuts({ setPaletteMode, setSidebarTab, setShowAIPanel });

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
          
          // Refresh user profile to ensure roles are correct
          state.refreshMe();
          
          // Use a race to ensure we don't hang forever
          const initPromise = Promise.all([
            state.refreshFileTree(), 
            state.refreshInfra(),
            state.refreshSettings()
          ]);

          const timeoutPromise = new Promise((resolve) => {
            setTimeout(() => {
              console.warn("Workspace init timed out, forcing entry...");
              resolve("timeout");
            }, 5000); // 5 second hard limit for pre-auth init
          });

          try {
            await Promise.race([initPromise, timeoutPromise]);
          } catch (err) {
            console.warn("Workspace init failed", err);
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
  }, [token, onboardingRequired]);

  useEffect(() => {
    // Bounce back to 18% when switching tabs or clearing search
    if (sidebarTab !== "search" && sidebarTab !== "infra") {
      sidebarRef.current?.resize(18);
    }
  }, [sidebarTab]);


  const activeTaskCount = Object.values(tasks).filter((t: any) => t.status === "THINKING" || t.status === "WRITING" || t.status === "TESTING").length;
  const isAIActive = Object.values(tasks).some((t: any) => t.status === "THINKING" || t.status === "WRITING");

  const languageItems = useMemo(() => [
    "typescript", "javascript", "python", "css", "json", "markdown", "yaml", "html", "rust", "go"
  ].map(l => ({ id: l, label: l.toUpperCase(), action: () => activeFile && setFileLanguage(activeFile, l) })), [activeFile, setFileLanguage]);

  const globalCommands = [
    { id: "new-file", label: "File: New File", category: "General", action: () => {} },
    { id: "save-file", label: "File: Save", category: "General", action: () => activeFile && saveFile(activeFile) },
    { id: "refresh-explorer", label: "File: Refresh Explorer", category: "General", action: refreshFileTree },
    { id: "view-explorer", label: "View: Show Explorer", category: "Navigation", action: () => setSidebarTab("explorer") },
    { id: "view-git", label: "View: Show Source Control", category: "Navigation", action: () => setSidebarTab("git") },
    { id: "view-search", label: "View: Show Search", category: "Navigation", action: () => setSidebarTab("search") },
    { id: "toggle-ai", label: "View: Toggle AI Assistant", category: "View", action: () => setShowAIPanel(!showAIPanel) },
    { id: "toggle-settings", label: "View: Toggle Settings", category: "View", action: () => setModalOpen(!modalOpen) },
    { id: "new-terminal", label: "Terminal: New Terminal", category: "Terminal", action: () => {
      const active = useStore.getState().openFiles.find(f => f.path === useStore.getState().activeFile);
      addTerminalSession(undefined, active?.root);
    } },
    { id: "clear-terminal", label: "Terminal: Clear Terminal", category: "Terminal", action: clearActiveTerminal },
    { id: "kill-terminal", label: "Terminal: Kill Active Session", category: "Terminal", action: () => closeTerminalSession(activeTerminalId) },
    { id: "run-file", label: "Terminal: Run Active File", category: "Terminal", action: runActiveFile },
    { id: "reload", label: "Developer: Reload Window", category: "Developer", action: () => window.location.reload() },
    { id: "logout", label: "Account: Logout", category: "Account", action: logout }
  ];

  return (
    <div className={`app ${modalOpen ? "modal-open" : ""}`}>
      {(!token || onboardingRequired) && <AuthOverlay />}
      {!isInitialized && <LoadingOverlay progress={visualProgress} />}
      
      <AnimatePresence>
        {showAbout && <AboutPanel />}
      </AnimatePresence>
      
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
      
      <div className={`app__root ${settings?.menu_mode === 'horizontal' ? 'with-horizontal-menu' : ''}`}>
          {settings?.menu_mode === 'horizontal' && <TitleBar />}
          {isMobile ? (
            <MobileView send={send} />
          ) : (
            <div className="app__main-layout">
                <ActivityBar />

              <div className="app__body">
                <PanelGroup direction="horizontal" className="app__panels" storage={localStorage} autoSaveId="neurex-main-layout">
                  <Panel ref={sidebarRef} defaultSize={18} minSize={10} maxSize={40} className="app__sidebar">
                    {sidebarTab === "explorer" && <FileExplorer />}
                    {sidebarTab === "history"  && <ConversationList />}
                    {sidebarTab === "infra"    && <InfraPanel onExpand={handleSidebarResize} currentSize={sidebarRef.current?.getSize() || 18} />}
                    {sidebarTab === "system"   && <SystemLogsPanel />}
                    {sidebarTab === "search"   && <SearchPanel onExpand={handleSidebarResize} />}
                    {sidebarTab === "git"      && <SourceControlPanel />}
                    {sidebarTab === "timeline" && <GitTimeline />}
                    {sidebarTab === "skills"   && <SkillsPanel />}
                    {sidebarTab === "agent"    && <AgentPanel />}
                    {sidebarTab === "swarm"    && <SwarmDiffSidebar />}
                    {sidebarTab === "debate"   && <DebateArena />}
                  </Panel>
                  <ResizeHandle />
                  <Panel minSize={30} className="app__main-content">
                    <PanelGroup direction="vertical" className="app__v-panels" storage={localStorage} autoSaveId="neurex-v-layout">
                      <Panel minSize={20} className="app__editor-wrapper">
                        <PresenceBar />
                        {showSettings ? <SettingsPanel /> : (
                          <PanelGroup direction="horizontal" storage={localStorage} autoSaveId="neurex-h-layout">
                            {editorPanes.map((pane: any, idx: number) => (
                              <React.Fragment key={pane.id}>
                                {idx > 0 && <ResizeHandle />}
                                <Panel minSize={20}>
                                  <EditorPane paneId={pane.id} />
                                </Panel>
                              </React.Fragment>
                            ))}
                          </PanelGroup>
                        )}
                      </Panel>
                      <ResizeHandle vertical />
                      <Panel 
                        defaultSize={25} 
                        minSize={0} 
                        collapsible={true}
                        onCollapse={() => console.log("Panel Collapsed")}
                        ref={(ref) => { (window as any).neurexBottomPanel = ref; }}
                        className="app__bottom-wrapper"
                      >
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

                <StatusBar 
                  wsStatus={wsStatus} 
                  setPaletteMode={setPaletteMode}
                  setSidebarTab={setSidebarTab}
                  isAIActive={isAIActive}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
}
function ResizeHandle({ vertical = false }: { vertical?: boolean }) {
  return (
    <PanelResizeHandle className={`resize-handle ${vertical ? "resize-handle--vertical" : "resize-handle--horizontal"}`}>
      <div className="resize-handle__highlight" />
    </PanelResizeHandle>
  );
}

