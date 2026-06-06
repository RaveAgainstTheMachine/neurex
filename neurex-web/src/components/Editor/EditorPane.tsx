// neurex-web/src/components/Editor/EditorPane.tsx
"use client";

import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { Editor, DiffEditor } from "@monaco-editor/react";
import { useStore } from "../../lib/store";
import { 
  ChevronRight, FileCode, Check, 
  Sparkles, X, CornerDownLeft, Loader2, Layout, Folder, Pin
} from "lucide-react";
import toast from "react-hot-toast";
import { ContextMenu } from "../ContextMenu/ContextMenu";
import { api } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import "./EditorPane.css";

export function EditorPane({ paneId = "pane-main" }: { paneId?: string }) {
  // Phase 44.17: Strict State Selection (Prevent Editor churn)
  const openFiles = useStore(s => s.openFiles);
  const setFileContent = useStore(s => s.setFileContent);
  const saveFile = useStore(s => s.saveFile);
  const presence = useStore(s => s.presence);
  const pendingJump = useStore(s => s.pendingJump);
  const clearPendingJump = useStore(s => s.clearPendingJump);
  const setCursorPosition = useStore(s => s.setCursorPosition);
  const token = useStore(s => s.token);
  const refreshInfra = useStore(s => s.refreshInfra);
  const editorPanes = useStore(s => s.editorPanes);
  const activeFile = useStore(s => s.activeFile);
  const setActiveFile = useStore(s => s.setActiveFile);
  const splitEditor = useStore(s => s.splitEditor);
  const closePane = useStore(s => s.closePane);
  const updateDiagnostics = useStore(s => s.updateDiagnostics);
  const togglePin = useStore(s => s.togglePin);
  const upsertTask = useStore(s => s.upsertTask);
  const setPaneFile = useStore(s => s.setPaneFile);
  const acceptDiff = useStore(s => s.acceptDiff);
  const discardDiff = useStore(s => s.discardDiff);

  const [supportedLangs, setSupportedLangs] = useState<string[]>([]);

  const activePath = editorPanes.find(p => p.id === paneId)?.path || activeFile;
  const active = openFiles.find((f) => f.path === activePath);

  const fetchSupportedLangs = useCallback(() => {
    api.get<any>("/api/languages/supported")
      .then((data: any) => setSupportedLangs(data?.languages || []))
      .catch(() => setSupportedLangs([]));
  }, []);

  useEffect(() => {
    fetchSupportedLangs();
  }, [fetchSupportedLangs]);
  
  const editorRef = useRef<any>(null);
  
  // Inline AI Edit State
  const [installableLangs, setInstallableLangs] = useState<string[]>([]);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.get<any>("/api/languages/installable")
      .then((data: any) => setInstallableLangs(data.languages))
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
      fetchSupportedLangs(); // Refresh the list so the loop stops
      refreshInfra();
    } catch (err: any) {
      toast.error(err.message, { id: toastId });
    } finally {
      setIsInstalling(false);
    }
  };

  const [inlinePrompt, setInlinePrompt] = useState("");
  const [isInlineVisible, setIsInlineVisible] = useState(false);
  const [inlineCoords, setInlineCoords] = useState({ top: 0, left: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [breadcrumbMenu, setBreadcrumbMenu] = useState<{ index: number; items: string[] } | null>(null);

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
    if (!active || !token) return;
    
    const isSupported = supportedLangs?.includes(active.language);
    const isInstallable = installableLangs?.includes(active.language);

    if (isSupported) {
      import("../../lib/lsp").then(m => m.lspManager.connect(active.language, token));
    } else if (isInstallable && !isInstalling) {
      handleInstall();
    }
  }, [active?.language, token, supportedLangs, installableLangs, isInstalling, handleInstall]);

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

  const triggerAstAction = async (actionType: 'refactor' | 'document' | 'test') => {
    if (!active || !editorRef.current) return;
    const editor = editorRef.current;
    const pos = editor.getPosition();
    if (!pos) return;

    const toastId = toast.loading("Analyzing AST structure...");
    try {
      const res = await api.get<any>(`/api/intelligence/ast-bounds?path=${encodeURIComponent(active.path)}&line=${pos.lineNumber}&column=${pos.column}`);
      toast.dismiss(toastId);
      
      const { start_line, end_line } = res;
      if (start_line !== undefined && end_line !== undefined) {
        editor.setSelection({
          startLineNumber: start_line,
          startColumn: 1,
          endLineNumber: end_line,
          endColumn: editor.getModel().getLineMaxColumn(end_line)
        });

        if (actionType === 'refactor') {
          const coords = editor.getScrolledVisiblePosition({ lineNumber: start_line, column: 1 });
          if (coords) {
            setInlineCoords({ 
              top: coords.top + 30, 
              left: Math.min(coords.left, (editor.getDomNode()?.clientWidth ?? 800) - 320) 
            });
            setIsInlineVisible(true);
          }
        } else {
          const prompt = actionType === 'document' 
            ? "Write rich, complete docstrings/documentation for this method. Return the updated method."
            : "Generate complete unit tests for this method/class.";
          
          setIsProcessing(true);
          const selection = editor.getSelection();
          const selectedText = editor.getModel().getValueInRange(selection);
          
          const taskId = Math.random().toString(36).substring(7);
          upsertTask({
            id: taskId,
            graph_id: "inline-edit",
            parent_id: null,
            agent_type: "coder",
            title: actionType === 'document' ? "AST Auto-Document" : "AST Test Generator",
            description: prompt,
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
              prompt,
              selection: selectedText,
              range: selection,
              taskId
            }
          });
          window.dispatchEvent(event);
          setIsProcessing(false);
          toast.success(actionType === 'document' ? "Documentation generation queued" : "Unit tests generation queued");
        }
      } else {
        toast.error("Could not resolve AST bounds for the current cursor position.");
      }
    } catch (err: any) {
      toast.dismiss(toastId);
      toast.error("AST query failed: " + (err.message || "Unknown error"));
    }
  };

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

  const sortedTabs = useMemo(() => {
    return [...openFiles].sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return 0;
    });
  }, [openFiles]);

  const renderBreadcrumbs = () => {
    if (!active) return null;
    const parts = active.path.split("/").filter(Boolean);
    const rootName = active.root ? active.root.split("/").pop() : null;
    
    return (
      <div className="editor-breadcrumbs">
        {rootName && (
          <React.Fragment>
            <div className="breadcrumb-item root" title={active.root}>
              <Folder size={12} className="text-muted" />
              <span>{rootName}</span>
            </div>
            <span className="breadcrumb-separator"><ChevronRight size={10} /></span>
          </React.Fragment>
        )}
        {parts.map((part, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span className="breadcrumb-separator"><ChevronRight size={10} /></span>}
            <div 
              className={`breadcrumb-item ${i === parts.length - 1 ? 'file' : ''}`}
              onClick={() => {
                setBreadcrumbMenu(breadcrumbMenu?.index === i ? null : { index: i, items: [part, "other_file.ts", "sibling_dir"] });
              }}
            >
              {i === parts.length - 1 ? <FileCode size={12} className="text-muted" /> : <Folder size={12} className="text-muted" />}
              <span>{part}</span>
              {breadcrumbMenu?.index === i && (
                <div className="breadcrumb-picker">
                  {breadcrumbMenu.items.map(item => (
                    <div key={item} className="breadcrumb-picker-item">
                      {item.includes('.') ? <FileCode size={12} /> : <Folder size={12} />}
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </React.Fragment>
        ))}
      </div>
    );
  };

  if (!active) {
    return (
      <div className="editor-empty">
        <div className="editor-watermark">
          <div className="watermark-item">
            <span className="watermark-label">Show All Commands</span>
            <span className="watermark-shortcut">Ctrl+Shift+P</span>
          </div>
          <div className="watermark-item">
            <span className="watermark-label">Go to File</span>
            <span className="watermark-shortcut">Ctrl+P</span>
          </div>
          <div className="watermark-item">
            <span className="watermark-label">Find in Files</span>
            <span className="watermark-shortcut">Ctrl+Shift+F</span>
          </div>
          <div className="watermark-item">
            <span className="watermark-label">Show AI Assistant</span>
            <span className="watermark-shortcut">Ctrl+L</span>
          </div>
          <div className="watermark-item">
            <span className="watermark-label">Toggle Terminal</span>
            <span className="watermark-shortcut">Ctrl+`</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="editor-pane">
      <div className="editor-pane__header">
        <div className="editor-tabs">
          {sortedTabs.map((f) => (
            <div
              key={`${f.root}:${f.path}`}
              className={`editor-tab ${f.path === activePath ? "active" : ""} ${f.isDirty ? "is-dirty" : ""} ${f.originalContent !== undefined ? "is-diff" : ""} ${f.isPreview ? "is-preview" : ""} ${f.isPinned ? "pinned" : ""}`}
              onClick={() => {
                setPaneFile(paneId, f.path);
                setActiveFile(f.path);
              }}
              onDoubleClick={() => {
                useStore.getState().openFile(f.path, f.content, f.language, false, f.root);
              }}
              data-path={f.path}
              data-root={f.root}
            >
              <FileCode size={13} className="editor-tab__icon" />
              <div className="editor-tab__label">
                <span className="editor-tab__name">{f.path.split("/").pop()}</span>
                {f.root && <span className="editor-tab__root">{f.root.split("/").pop()}</span>}
              </div>
              {f.isPinned && <Pin size={10} className="pin-icon" />}
              {f.isDirty && !f.isPinned && <span className="dirty-dot" />}
              {!f.isPinned && (
                <button
                  className="editor-tab__close"
                  onClick={(e) => {
                    e.stopPropagation();
                    useStore.getState().closeFile(f.path);
                  }}
                >
                  <X size={14} />
                </button>
              )}
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
              { type: 'separator' },
              { label: active.isPinned ? 'Unpin' : 'Pin', action: (target) => {
                const path = target.getAttribute('data-path');
                if (path) togglePin(path);
              }},
              { type: 'separator' },
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
                  const parts = path.split('/');
                  let currentPath = "";
                  for (let i = 0; i < parts.length - 1; i++) {
                    currentPath += (currentPath ? "/" : "") + parts[i];
                    useStore.getState().toggleFolder(currentPath, true);
                  }
                  toast.success(`Revealed ${path.split('/').pop()}`);
                }
              }}
            ]}
          />
        </div>
        
        <div className="editor-controls">
          {active.originalContent !== undefined && (
            <div className="diff-actions">
              <button className="btn btn--green btn--sm" onClick={() => acceptDiff(active.path)}>
                <Check size={14} /> Accept
              </button>
              <button className="btn btn--red btn--sm" onClick={() => discardDiff(active.path)}>
                <X size={14} /> Discard
              </button>
            </div>
          )}
          <div className="editor-group-actions">
            <button className="editor-control-btn" onClick={() => splitEditor("horizontal")} title="Split Editor Right">
              <Layout size={14} className="rotate-90" />
            </button>
            {editorPanes.length > 1 && (
              <button className="editor-control-btn text-red" onClick={() => closePane(paneId)} title="Close Pane">
                <X size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
      {renderBreadcrumbs()}

      <div className="editor-monaco" data-path={active.path}>
        <ContextMenu 
          targetSelector=".editor-monaco"
          items={[
            { label: '✨ Neurex: Refactor Symbol / Block', shortcut: 'Ctrl+K', action: () => triggerAstAction('refactor') },
            { label: '📝 Neurex: Document Method', action: () => triggerAstAction('document') },
            { label: '🧪 Neurex: Generate Unit Tests', action: () => triggerAstAction('test') },
            { type: 'separator' },
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
        )}

        {active.isPreview && active.language === "markdown" ? (
          <div className="editor-markdown-preview message__content" style={{ padding: '24px', height: '100%', overflowY: 'auto' }}>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {active.content}
            </ReactMarkdown>
          </div>
        ) : active.originalContent !== undefined ? (
          <DiffEditor
            height="100%"
            original={active.originalContent}
            modified={active.content}
            language={active.language}
            theme="neurex-dark"
            beforeMount={(monaco) => {
              monaco.editor.defineTheme("neurex-dark", {
                base: "vs-dark",
                inherit: true,
                rules: [],
                colors: { "editor.background": "#0a0a0c" },
              });
            }}
            options={{
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              renderSideBySide: true,
              scrollBeyondLastLine: false,
              readOnly: false,
              automaticLayout: true,
              contextmenu: false,
              wordWrap: (active?.path?.includes('.neurex/plans/') || active?.path?.includes('.neurex/replays/')) ? "on" : "off",
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

              if (active && token && supportedLangs?.includes(active.language)) {
                import("../../lib/lsp").then(m => m.lspManager.connect(active.language, token));
              }

              const { sendPresence } = (window as any).neurexWS || {};
              
              // ── Neural Error Lens ──────────────────────────────────────
              let errorLensDecorations: string[] = [];
              const updateErrorLens = () => {
                const model = editor.getModel();
                if (!model) return;
                const markers = monaco.editor.getModelMarkers({ resource: model.uri });
                
                // Sync with global store
                updateDiagnostics(active.path, markers.map((m: any) => ({
                  message: m.message,
                  severity: m.severity,
                  line: m.startLineNumber,
                  column: m.startColumn,
                  source: m.source || "LSP"
                })));
                
                // Group by line to avoid overlapping messages
                const markersByLine: Record<number, any[]> = {};
                markers.forEach((m: any) => {
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
                  const data = await api.get<any>(`/api/git/blame?path=${active.path}`);
                  const { blame } = data;
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
                } catch { /* intentional */ }
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
                          className: `remote-cursor remote-cursor--${(p.user_id || '').toLowerCase().match(/agent|coder|neurex/) ? 'agent' : 'user'}`,
                          hoverMessage: { value: p.user_id || 'Unknown' }
                        }
                      });
                    }
                  });
                  decorations = editor.deltaDecorations(decorations, newDecorations);
                } catch { /* intentional */ }
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
              wordWrap: (active?.path?.includes('.neurex/plans/') || active?.path?.includes('.neurex/replays/')) ? "on" : "off",
              renderWhitespace: "selection",
              guides: {
                indentation: true,
                bracketPairs: true,
              },
              smoothScrolling: true,
              cursorBlinking: "blink",
              cursorSmoothCaretAnimation: "on",
              mouseWheelZoom: true,
              links: true,
            }}
          />
        )}
      </div>
    </div>
  );
}
