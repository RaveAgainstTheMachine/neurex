// neurex-web/src/components/Editor/EditorPane.tsx
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import MonacoEditor, { Editor, DiffEditor } from "@monaco-editor/react";
import { useStore } from "../../lib/store";
import { API_BASE } from "../../lib/config";
import { 
  Files, ChevronDown, Save, FileCode, Check, AlertCircle, 
  Sparkles, X, CornerDownLeft, Loader2, Activity, Cpu, Zap, Layout 
} from "lucide-react";
import toast from "react-hot-toast";
import { ContextMenu } from "../ContextMenu/ContextMenu";
import { lspManager } from "../../lib/lsp";
import "./EditorPane.css";

export function EditorPane() {
  const { 
    openFiles, activeFile, setFileContent, saveFile, 
    presence, pendingJump, clearPendingJump, 
    setCursorPosition, upsertTask, hiveStats, infraMetrics,
    acceptDiff, discardDiff, token
  } = useStore();

  const [supportedLangs, setSupportedLangs] = useState<string[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/languages/supported`)
      .then(r => r.json())
      .then(data => setSupportedLangs(data.languages))
      .catch(() => {});
  }, []);
  
  const editorRef = useRef<any>(null);
  const active = openFiles.find((f) => f.path === activeFile);
  
  // Inline AI Edit State
  const [installableLangs, setInstallableLangs] = useState<string[]>([]);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE}/api/languages/installable`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setInstallableLangs(data.languages))
      .catch(() => {});
  }, [token]);

  const handleInstall = async () => {
    if (!active || !token) return;
    setIsInstalling(true);
    const toastId = toast.loading(`Provisioning ${active.language} intelligence...`);
    try {
      const { installLanguageServer } = await import("../../lib/lsp");
      await installLanguageServer(active.language, token);
      toast.success(`${active.language} intelligence active!`, { id: toastId });
      // Refresh supported list in store
      refreshInfra();
    } catch (err: any) {
      toast.error(err.message, { id: toastId });
    } finally {
      setIsInstalling(false);
    }
  };

  const showAutopilot = active && !supportedLangs.includes(active.language) && installableLangs.includes(active.language);

  const [inlinePrompt, setInlinePrompt] = useState("");
  const [isInlineVisible, setIsInlineVisible] = useState(false);
  const [inlineCoords, setInlineCoords] = useState({ top: 0, left: 0 });
  const [isProcessing, setIsProcessing] = useState(false);

  // Auto-Save / Debounced Sync
  useEffect(() => {
    if (!active || active.originalContent !== undefined) return;
    const timer = setTimeout(() => {
      if (active.isDirty) {
        saveFile(active.path);
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [active?.content, active?.isDirty, active?.path, saveFile]);

  useEffect(() => {
    if (pendingJump && editorRef.current && pendingJump.path === activeFile) {
      const editor = editorRef.current;
      setTimeout(() => {
        editor.revealLineInCenter(pendingJump.line);
        editor.setPosition({ lineNumber: pendingJump.line, column: 1 });
        editor.focus();
        clearPendingJump();
      }, 50);
    }
  }, [pendingJump, activeFile, clearPendingJump]);

  useEffect(() => {
    if (editorRef.current?._presenceObserver) {
      editorRef.current._presenceObserver();
    }
  }, [presence]);

  const handleInlineSubmit = useCallback(async () => {
    if (!inlinePrompt.trim() || isProcessing || !editorRef.current || !active) return;
    
    setIsProcessing(true);
    const editor = editorRef.current;
    const selection = editor.getSelection();
    const selectedText = editor.getModel().getValueInRange(selection);
    
    try {
      const taskId = Math.random().toString(36).substring(7);
      upsertTask({
        id: taskId,
        graph_id: "inline-edit",
        parent_id: null,
        agent_type: "coder",
        title: "Inline AI Edit",
        description: inlinePrompt,
        status: "THINKING",
        result: null,
        error: null,
        iteration: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });

      const event = new CustomEvent("neurex_inline_edit", {
        detail: {
          path: active.path,
          prompt: inlinePrompt,
          selection: selectedText,
          range: selection,
          taskId
        }
      });
      window.dispatchEvent(event);
      
      setIsInlineVisible(false);
      setInlinePrompt("");
    } catch (err) {
      console.error("Inline edit failed", err);
    } finally {
      setIsProcessing(false);
    }
  }, [inlinePrompt, isProcessing, active, upsertTask]);

  if (!active) {
    const activeTasksCount = Object.values(useStore.getState().tasks).filter(t => ["THINKING", "WRITING"].includes(t.status)).length;

    return (
      <div className="editor-empty">
        <div className="editor-empty__content">
          <div className="editor-empty__logo animate-float">⬡</div>
          <h1 className="editor-empty__title">NEUREX SYSTEM ACTIVE</h1>
          <p className="editor-empty__subtitle">The Distributed Intelligence Mesh is synchronized and awaiting instructions.</p>
          
          <div className="dashboard-grid">
            <div className="dashboard-card glass">
              <div className="dashboard-card__header">
                <Activity size={14} className="text-cyan" />
                <span>SWARM STATUS</span>
              </div>
              <div className="dashboard-card__body">
                <div className="big-stat">{hiveStats.total_nodes}</div>
                <div className="stat-label">ACTIVE NODES</div>
              </div>
            </div>
            
            <div className="dashboard-card glass">
              <div className="dashboard-card__header">
                <Cpu size={14} className="text-purple" />
                <span>RESOURCE LOAD</span>
              </div>
              <div className="dashboard-card__body">
                <div className="big-stat">{infraMetrics?.vram_gb || 0}GB</div>
                <div className="stat-label">VRAM UTILIZED</div>
              </div>
            </div>

            <div className="dashboard-card glass">
              <div className="dashboard-card__header">
                <Zap size={14} className="text-amber" />
                <span>AGENT ACTIVITY</span>
              </div>
              <div className="dashboard-card__body">
                <div className="big-stat">{activeTasksCount}</div>
                <div className="stat-label">RUNNING TASKS</div>
              </div>
            </div>
          </div>

          <div className="quick-actions">
            <button className="btn btn--green" onClick={() => window.dispatchEvent(new CustomEvent('open_command_palette'))}>
              <Layout size={14} /> Open Command Palette
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="editor-pane">
      <div className="editor-pane__header">
        <div className="editor-tabs">
          {openFiles.map((f) => (
            <div
              key={f.path}
              className={`editor-tab ${f.path === activeFile ? "active" : ""} ${f.isDirty ? "is-dirty" : ""} ${f.originalContent !== undefined ? "is-diff" : ""}`}
              onClick={() => useStore.getState().setActiveFile(f.path)}
              data-path={f.path}
            >
              <FileCode size={13} className="editor-tab__icon" />
              <span className="editor-tab__name">{f.path.split("/").pop()}</span>
              {f.isDirty && <span className="dirty-dot" />}
              <button
                className="editor-tab__close"
                onClick={(e) => {
                  e.stopPropagation();
                  useStore.getState().closeFile(f.path);
                }}
              >
                ×
              </button>
            </div>
          ))}
          <ContextMenu 
            targetSelector=".editor-tab"
            items={[
              { label: 'Close', shortcut: 'Ctrl+W', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) useStore.getState().closeFile(path);
              }},
              { label: 'Close Others', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) useStore.getState().closeOthers(path);
              }},
              { label: 'Close to the Right', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) useStore.getState().closeToRight(path);
              }},
              { label: 'Close Saved', shortcut: 'Ctrl+K U', action: () => useStore.getState().closeSaved() },
              { label: 'Close All', shortcut: 'Ctrl+K W', action: () => useStore.getState().closeAllFiles() },
              { type: 'separator' },
              { label: 'Copy Path', shortcut: 'Ctrl+Alt+C', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) {
                  navigator.clipboard.writeText(path);
                  toast.success("Path copied to clipboard");
                }
              }},
              { label: 'Copy Relative Path', shortcut: 'Ctrl+Shift+Alt+C', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) {
                  const rel = path.replace(/^\/+/, '');
                  navigator.clipboard.writeText(rel);
                  toast.success("Relative path copied");
                }
              }},
              { type: 'separator' },
              { label: 'Reveal in Explorer', shortcut: 'Ctrl+Alt+R', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) {
                  // This is a UI-only reveal in our current setup
                  toast.success(`Revealing ${path.split('/').pop()}`);
                }
              }}
            ]}
          />
        </div>
        
        <div className="editor-controls">
          {active.originalContent !== undefined ? (
            <div className="diff-actions">
              <button className="btn btn--green btn--sm" onClick={() => acceptDiff(active.path)}>
                <Check size={14} /> Accept
              </button>
              <button className="btn btn--red btn--sm" onClick={() => discardDiff(active.path)}>
                <X size={14} /> Discard
              </button>
            </div>
          ) : active.isDirty && (
            <button className="editor-control-btn save-btn" onClick={() => saveFile(active.path)} title="Save Changes (Cmd+S)">
              <Save size={14} />
              <span>Save</span>
            </button>
          )}
        </div>
      </div>

      <div className="editor-monaco" data-path={active.path}>
        <ContextMenu 
          targetSelector=".editor-monaco"
          items={[
            { label: 'Go to Definition', shortcut: 'F12', action: () => editorRef.current?.trigger('any', 'editor.action.revealDefinition') },
            { label: 'Go to References', shortcut: 'Shift+F12', action: () => editorRef.current?.trigger('any', 'editor.action.goToReferences') },
            { type: 'separator' },
            { label: 'Find All References', shortcut: 'Alt+Shift+F12', action: () => editorRef.current?.trigger('any', 'references-view.findReferences') },
            { label: 'Rename Symbol', shortcut: 'F2', action: () => editorRef.current?.trigger('any', 'editor.action.rename') },
            { label: 'Change All Occurrences', shortcut: 'Ctrl+F2', action: () => editorRef.current?.trigger('any', 'editor.action.changeAll') },
            { type: 'separator' },
            { label: 'Format Document', shortcut: 'Alt+Shift+F', action: () => editorRef.current?.trigger('any', 'editor.action.formatDocument') },
            { label: 'Refactor...', shortcut: 'Ctrl+Shift+R', action: () => editorRef.current?.trigger('any', 'editor.action.quickFix') },
            { type: 'separator' },
            { label: 'Cut', shortcut: 'Ctrl+X', action: () => {
              editorRef.current?.focus();
              document.execCommand('cut');
            }},
            { label: 'Copy', shortcut: 'Ctrl+C', action: () => {
              editorRef.current?.focus();
              document.execCommand('copy');
            }},
            { label: 'Paste', shortcut: 'Ctrl+V', action: () => {
              editorRef.current?.focus();
              document.execCommand('paste');
            }},
            { type: 'separator' },
            { label: 'Run in Terminal', shortcut: 'F5', action: () => useStore.getState().runActiveFile() },
            { label: 'Command Palette...', shortcut: 'Ctrl+Shift+P', action: () => window.dispatchEvent(new CustomEvent('open_command_palette')) }
          ]}
        />
        {isInlineVisible && (
          <div 
            className="inline-ai-prompt animate-scale"
            style={{ top: inlineCoords.top, left: inlineCoords.left }}
          >
            <div className="inline-ai-prompt__header">
              <Sparkles size={12} className="text-cyan" />
              <span>Ask AI to edit...</span>
              <button className="close-btn" onClick={() => setIsInlineVisible(false)}><X size={12} /></button>
            </div>
            <div className="inline-ai-prompt__input-wrapper">
              <input 
                autoFocus
                placeholder="Fix bugs, add features, refactor..."
                value={inlinePrompt}
                onChange={(e) => setInlinePrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleInlineSubmit();
                  if (e.key === "Escape") setIsInlineVisible(false);
                }}
              />
              <button className="submit-btn" onClick={handleInlineSubmit}>
                {isProcessing ? <Loader2 size={14} className="animate-spin" /> : <CornerDownLeft size={14} />}
              </button>
            </div>
          </div>
        {showAutopilot && (
          <div className="autopilot-banner glass animate-slide-down">
            <div className="autopilot-banner__info">
              <BrainCircuit size={14} className="text-cyan animate-pulse" />
              <span>Autopilot detected missing {active.language} intelligence.</span>
            </div>
            <button 
              className="btn btn--cyan btn--small" 
              onClick={handleInstall}
              disabled={isInstalling}
            >
              {isInstalling ? <RefreshCw size={12} className="animate-spin" /> : "ENABLE AUTOPILOT"}
            </button>
          </div>
        )}

        {active.originalContent !== undefined ? (
          <DiffEditor
            height="100%"
            original={active.originalContent}
            modified={active.content}
            language={active.language}
            theme="neurex-dark"
            options={{
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              renderSideBySide: true,
              scrollBeyondLastLine: false,
              readOnly: false,
              automaticLayout: true,
              contextmenu: false,
            }}
          />
        ) : (
          <Editor
            height="100%"
            key={`${active.path}-${active.language}`}
            path={active.path}
            language={active.language}
            value={active.content}
            theme="neurex-dark"
            beforeMount={(monaco) => {
              monaco.editor.defineTheme("neurex-dark", {
                base: "vs-dark",
                inherit: true,
                rules: [],
                colors: { "editor.background": "#0a0a0c" },
              });
            }}
            onChange={(val) => setFileContent(active.path, val ?? "")}
            onMount={(editor, monaco) => {
              editorRef.current = editor;

              if (active && token && supportedLangs.includes(active.language)) {
                lspManager.connect(active.language, token);
              }

              const { sendPresence } = (window as any).neurexWS || {};
              
              // ── Neural Error Lens ──────────────────────────────────────
              let errorLensDecorations: string[] = [];
              const updateErrorLens = () => {
                const model = editor.getModel();
                if (!model) return;
                const markers = monaco.editor.getModelMarkers({ resource: model.uri });
                
                // Group by line to avoid overlapping messages
                const markersByLine: Record<number, any[]> = {};
                markers.forEach(m => {
                  if (!markersByLine[m.endLineNumber]) markersByLine[m.endLineNumber] = [];
                  markersByLine[m.endLineNumber].push(m);
                });

                const newDecorations = Object.entries(markersByLine).map(([line, lineMarkers]) => {
                  const worstMarker = lineMarkers.sort((a, b) => b.severity - a.severity)[0];
                  const messages = lineMarkers.map(m => m.message).join(' | ');
                  
                  return {
                    range: new monaco.Range(parseInt(line), 1, parseInt(line), 1),
                    options: {
                      isWholeLine: true,
                      after: {
                        content: `   ⬡ ${messages}`,
                        inlineClassName: `error-lens-msg error-lens-msg--${worstMarker.severity === 8 ? 'error' : 'warning'}`
                      }
                    }
                  };
                });
                errorLensDecorations = editor.deltaDecorations(errorLensDecorations, newDecorations);
              };

              monaco.editor.onDidChangeMarkers(() => updateErrorLens());

              // ── Neural GitLens Blame ───────────────────────────────────
              let blameDecorations: string[] = [];
              const updateBlame = async (lineNumber: number) => {
                if (!active || !token) return;
                try {
                  const res = await fetch(`${API_BASE}/api/git/blame?path=${active.path}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                  });
                  if (!res.ok) return;
                  const { blame } = await res.json();
                  const info = blame[lineNumber - 1];
                  if (!info) return;

                  const timeStr = new Date(info.time * 1000).toLocaleDateString();
                  const newDecorations = [{
                    range: new monaco.Range(lineNumber, 1, lineNumber, 1),
                    options: {
                      isWholeLine: true,
                      after: {
                        content: `   ${info.author} • ${info.summary} • ${timeStr}`,
                        inlineClassName: 'git-blame-ghost'
                      }
                    }
                  }];
                  blameDecorations = editor.deltaDecorations(blameDecorations, newDecorations);
                } catch (err) {}
              };

              let lastLine = -1;
              editor.onDidChangeCursorPosition((e) => {
                const currentLine = e.position.lineNumber;
                setCursorPosition(currentLine, e.position.column);
                
                if (currentLine !== lastLine) {
                  updateBlame(currentLine);
                  lastLine = currentLine;
                }
                
                if (sendPresence) {
                  sendPresence({
                    active_file: active.path,
                    cursor: { line: e.position.lineNumber, ch: e.position.column }
                  });
                }
              });

              let decorations: string[] = [];
              const renderRemoteCursors = () => {
                try {
                  const newDecorations: any[] = [];
                  presence.forEach((p) => {
                    if (p.active_file === active.path && p.cursor && typeof p.cursor.line === 'number') {
                      newDecorations.push({
                        range: new monaco.Range(p.cursor.line, p.cursor.ch, p.cursor.line, p.cursor.ch + 1),
                        options: {
                          className: `remote-cursor remote-cursor--${(p.user_id || '').toLowerCase().includes('agent') ? 'agent' : 'user'}`,
                          hoverMessage: { value: p.user_id || 'Unknown' }
                        }
                      });
                    }
                  });
                  decorations = editor.deltaDecorations(decorations, newDecorations);
                } catch (err) {}
              };

              (editor as any)._presenceObserver = renderRemoteCursors;

              editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyK, () => {
                const pos = editor.getPosition();
                if (!pos) return;
                const coords = editor.getScrolledVisiblePosition(pos);
                if (!coords) return;
                setInlineCoords({ 
                  top: coords.top + 30, 
                  left: Math.min(coords.left, (editor.getDomNode()?.clientWidth ?? 800) - 320) 
                });
                setIsInlineVisible(true);
              });

              editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, async () => {
                // Trigger formatting if available
                const formatAction = editor.getAction('editor.action.formatDocument');
                if (formatAction) {
                  await formatAction.run();
                }
                saveFile(active.path);
              });
            }}
            options={{
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              minimap: { enabled: true, scale: 0.75 },
              scrollBeyondLastLine: false,
              automaticLayout: true,
              padding: { top: 10, bottom: 10 },
              lineNumbers: "on",
              glyphMargin: true,
              folding: true,
              lineDecorationsWidth: 10,
              lineNumbersMinChars: 3,
              bracketPairColorization: { enabled: true },
              suggestOnTriggerCharacters: true,
              contextmenu: false,
            }}
          />
        )}
      </div>
    </div>
  );
}
