// src/components/Editor/EditorPane.tsx
import { useEffect, useRef, useState, useCallback } from "react";
import MonacoEditor, { Editor, DiffEditor } from "@monaco-editor/react";
import { useStore } from "../../lib/store";
import { 
  Files, ChevronDown, Save, FileCode, Check, AlertCircle, 
  Sparkles, X, CornerDownLeft, Loader2 
} from "lucide-react";
import "./EditorPane.css";

export function EditorPane() {
  const { 
    openFiles, activeFile, setFileContent, saveFile, 
    presence, pendingJump, clearPendingJump, setFileLanguage,
    setCursorPosition, upsertTask
  } = useStore();
  
  const editorRef = useRef<any>(null);
  const active = openFiles.find((f) => f.path === activeFile) ?? openFiles[0];
  
  // Inline AI Edit State
  const [inlinePrompt, setInlinePrompt] = useState("");
  const [isInlineVisible, setIsInlineVisible] = useState(false);
  const [inlineCoords, setInlineCoords] = useState({ top: 0, left: 0 });
  const [isProcessing, setIsProcessing] = useState(false);

  // Auto-Save / Debounced Sync
  useEffect(() => {
    if (!active) return;
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
    if (!inlinePrompt.trim() || isProcessing || !editorRef.current) return;
    
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
    return (
      <div className="editor-empty">
        <div className="editor-empty__content">
          <div className="editor-empty__logo">
            <Files size={64} />
          </div>
          <h1 className="editor-empty__title">Neurex Editor</h1>
          <p className="editor-empty__subtitle">Select a file from the explorer to start coding with AI-powered intelligence.</p>
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
              className={`editor-tab ${f.path === activeFile ? "active" : ""} ${f.isDirty ? "is-dirty" : ""}`}
              onClick={() => useStore.getState().setActiveFile(f.path)}
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
        </div>
        
        <div className="editor-controls">
          {active.isDirty && (
            <button className="editor-control-btn save-btn" onClick={() => saveFile(active.path)} title="Save Changes (Cmd+S)">
              <Save size={14} />
              <span>Save</span>
            </button>
          )}
        </div>
      </div>

      <div className="editor-monaco">
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
              const { sendPresence } = (window as any).neurexWS || {};
              
              editor.onDidChangeCursorPosition((e) => {
                setCursorPosition(e.position.lineNumber, e.position.column);
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
                  left: Math.min(coords.left, editor.getDomNode()?.clientWidth ?? 0 - 320) 
                });
                setIsInlineVisible(true);
              });

              editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
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
            }}
          />
        )}
      </div>
    </div>
  );
}
