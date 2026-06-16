import React, { useState, useEffect } from "react";
import { 
  X, Plus, Bot as BotIcon, Sparkles, 
  ChevronRight, ChevronDown, FileCode, AlertTriangle, Info
} from "lucide-react";
import { useStore } from "../../lib/store";
import { Terminal } from "../Terminal/Terminal";
import { TelemetryReplayCanvas } from "../TelemetryReplay/TelemetryReplayCanvas";
import { BenchmarkDashboard } from "../Benchmark/BenchmarkDashboard";
import toast from "react-hot-toast";
import "./BottomPanel.css";

interface BottomPanelProps {
  send: (p: any) => void;
}

export function BottomPanel({ send }: BottomPanelProps) {
  const [activeTab, setActiveTab] = useState<"terminal" | "output" | "flight" | "problems" | "benchmarks">("terminal");
  const { 
    terminalSessions, activeTerminalId, setActiveTerminalId, 
    addTerminalSession, closeTerminalSession, clearActiveTerminal, tasks, activeConversationId,
    diagnostics, sendMessage
  } = useStore();
  
  useEffect(() => {
    const handleShow = () => setActiveTab("problems");
    window.addEventListener("neurex_show_problems", handleShow);
    return () => window.removeEventListener("neurex_show_problems", handleShow);
  }, []);


  const lines = Object.values(tasks).filter((t: any) => t.result || t.error).flatMap((t: any) => {
    const out: string[] = [];
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
          <button className={`bottom-tab ${activeTab === "problems" ? "active" : ""}`} onClick={() => setActiveTab("problems")} title="Workspace Problems">
            PROBLEMS {diagnostics.length > 0 && <span className="tab-badge">{diagnostics.length}</span>}
          </button>
          <button className={`bottom-tab ${activeTab === "flight" ? "active" : ""}`} onClick={() => setActiveTab("flight")} title="AI Flight Recorder">FLIGHT LOG</button>
          <button className={`bottom-tab ${activeTab === "benchmarks" ? "active" : ""}`} onClick={() => setActiveTab("benchmarks")} title="Visual Benchmark Arena">BENCHMARK</button>
        </div>
        
        <div className="bottom-panel__actions">
          {activeTab === "terminal" && (
            <>
              <button 
                className="terminal-add-btn" 
                onClick={() => {
                  const active = useStore.getState().openFiles.find(f => f.path === useStore.getState().activeFile);
                  addTerminalSession(undefined, active?.root);
                }} 
                title="New Terminal"
              >
                <Plus size={14} />
              </button>
              <button className="terminal-add-btn" onClick={() => clearActiveTerminal()} title="Clear Terminal">
                <X size={14} />
              </button>
            </>
          )}
          <div className="bottom-panel__divider" />
          <button className="terminal-add-btn" onClick={() => {
            const panel = (window as any).neurexBottomPanel;
            if (panel) {
              const isMaximized = (panel.getSize()?.asPercentage ?? 0) > 80;
              panel.resize(isMaximized ? "25%" : "90%");
            }
          }} title="Toggle Maximize">
            <ChevronRight size={14} style={{ transform: "rotate(-90deg)" }} />
          </button>
          <button className="terminal-add-btn" onClick={() => {
            const panel = (window as any).neurexBottomPanel;
            if (panel) panel.collapse();
          }} title="Close Panel">
            <X size={14} />
          </button>
        </div>
      </div>
      <div className="bottom-panel__content">
        <div 
          className="bottom-panel__tab-content terminal-area" 
          style={{ display: activeTab === "terminal" ? "flex" : "none" }}
        >
          <div className="terminal-container">
            {terminalSessions.map((s) => (
              <div 
                key={s.id} 
                className="terminal-instance-wrapper"
                style={{ 
                  display: activeTerminalId === s.id ? "flex" : "none",
                  height: "100%",
                  width: "100%"
                }}
              >
                <Terminal 
                  sessionId={s.id}
                  isActive={activeTab === "terminal" && activeTerminalId === s.id}
                  onInput={(data) => send({ type: "terminal_input", sessionId: s.id, data })} 
                  onResize={(rows, cols) => send({ type: "terminal_resize", sessionId: s.id, rows, cols })} 
                />
              </div>
            ))}
          </div>
          <aside className="terminal-sidebar">
            <div className="terminal-list">
              {terminalSessions.map((s) => (
                <div 
                  key={s.id} 
                  className={`terminal-list-item ${activeTerminalId === s.id ? "active" : ""}`}
                  onClick={() => setActiveTerminalId(s.id)}
                >
                  <FileCode size={14} />
                  <span className="terminal-list-item__name">{s.name}</span>
                  {terminalSessions.length > 1 && (
                    <button 
                      className="terminal-list-item__close" 
                      onClick={(e) => { e.stopPropagation(); closeTerminalSession(s.id); }}
                    >
                      <X size={12} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </aside>
        </div>
        <div 
          className="bottom-panel__tab-content problems-view"
          style={{ display: activeTab === "problems" ? "block" : "none" }}
        >
          {diagnostics.length === 0 ? (
            <div className="empty-state">No problems detected in the workspace.</div>
          ) : (
              <div className="problems-list">
                <div className="problems-header">
                  <span>{diagnostics.length} items found</span>
                  <button className="btn btn--purple btn--sm" onClick={() => {
                    const context = diagnostics.map((d: any) => `File: ${d.path}\nLine ${d.line}: ${d.message}`).join("\n\n");
                    sendMessage(`I'm seeing several errors in the workspace. Can you help me fix them?\n\n${context}`);
                    toast.success("Diagnostics sent to Agent");
                  }}>
                    <BotIcon size={12} />
                    <span>Send All to Agent</span>
                  </button>
                </div>
                
                {Object.entries(
                  diagnostics.reduce((acc: Record<string, any[]>, d: any) => {
                    if (!acc[d.path]) acc[d.path] = [];
                    acc[d.path].push(d);
                    return acc;
                  }, {})
                ).map(([path, fileDiagnostics]) => (
                  <div key={path} className="problems-file-group">
                    <div className="problems-file-header">
                      <ChevronDown size={14} />
                      <FileCode size={14} className="text-muted" />
                      <span className="file-name">{path.split('/').pop()}</span>
                      <span className="problems-file-path">{path.substring(0, path.lastIndexOf('/'))}</span>
                      <span className="tab-badge">{fileDiagnostics.length}</span>
                    </div>
                    <div className="problems-file-items">
                      {fileDiagnostics.map((d: any, i: number) => (
                        <div key={i} className={`problem-item ${d.severity === 8 ? "error" : d.severity === 4 ? "warning" : "info"}`} onClick={async () => {
                          const { openFile, setActiveFile, setPendingJump } = useStore.getState();
                          const { api } = await import("../../lib/api");
                          try {
                            const data = await api.get<{ content: string }>(`/api/files/read?path=${encodeURIComponent(d.path)}`);
                            const ext = d.path.split('.').pop();
                            const lang = ext === 'ts' ? 'typescript' : ext === 'tsx' ? 'typescriptreact' : ext === 'js' ? 'javascript' : 'plaintext';
                            openFile(d.path, data.content ?? "", lang);
                            setPendingJump(d.path, d.line);
                            setActiveFile(d.path);
                          } catch {
                            toast.error("Could not open file");
                          }
                        }}>
                          <div style={{ width: 24 }} /> {/* Indent */}
                          {d.severity === 8 ? <AlertTriangle size={14} className="problem-icon" /> : <Info size={14} className="problem-icon" />}
                          <div className="problem-info">
                            <div className="problem-message">{d.message}</div>
                            <div className="problem-location">Line {d.line}, Column {d.column}</div>
                          </div>
                          <button className="problem-action" onClick={(e) => {
                            e.stopPropagation();
                            sendMessage(`Help me fix this error in ${d.path} at line ${d.line}: ${d.message}`);
                            toast.success("Problem sent to Agent");
                          }}>
                            <Sparkles size={12} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
          )}
        </div>
        <div 
          className="bottom-panel__tab-content output-log"
          style={{ display: activeTab === "output" ? "block" : "none" }}
        >
          {lines.map((l, i) => <div key={i} className="bottom-panel__line">{l}</div>)}
        </div>
        <div 
          className="bottom-panel__tab-content"
          style={{ display: activeTab === "flight" ? "block" : "none", height: "100%", overflow: "hidden" }}
        >
          <TelemetryReplayCanvas conversationId={activeConversationId} />
        </div>
        <div 
          className="bottom-panel__tab-content"
          style={{ display: activeTab === "benchmarks" ? "block" : "none", height: "100%", overflow: "hidden" }}
        >
          <BenchmarkDashboard />
        </div>
      </div>
    </div>
  );
}
