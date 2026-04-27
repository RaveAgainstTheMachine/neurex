import { useEffect, useRef, useState } from "react";
import MonacoEditor, { Editor, DiffEditor } from "@monaco-editor/react";
import { useStore } from "../../lib/store";
import { Files, ChevronDown, Save, FileCode, Check, AlertCircle } from "lucide-react";
import "./EditorPane.css";

const LANGUAGES = [
  "typescript", "javascript", "python", "css", "json", "markdown", 
  "shell", "yaml", "html", "rust", "go", "sql", "plaintext"
];

export function EditorPane() {
  const { 
    openFiles, activeFile, setFileContent, saveFile, 
    presence, pendingJump, clearPendingJump, setFileLanguage 
  } = useStore();
  
  const editorRef = useRef<any>(null);
  const [showLangMenu, setShowLangMenu] = useState(false);

  const active = openFiles.find((f) => f.path === activeFile) ?? openFiles[0];

  // Handle line jumps (e.g. from search)
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

  // Sync presence with monaco decorations
  useEffect(() => {
    if (editorRef.current?._presenceObserver) {
      editorRef.current._presenceObserver();
    }
  }, [presence]);

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
        {active.originalContent !== undefined ? (
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
                colors: { "editor.background": "#0d0d0f" },
              });
            }}
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
                colors: { "editor.background": "#0d0d0f" },
              });
            }}
            onChange={(val) => setFileContent(active.path, val ?? "")}
            onMount={(editor, monaco) => {
              editorRef.current = editor;
              const { sendPresence } = (window as any).neurexWS || {};
              
              editor.onDidChangeCursorPosition((e) => {
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

      <div className="editor-status-bar">
        <div className="editor-status-left">
          <span className="status-item">
            {active.isDirty ? <AlertCircle size={12} className="text-orange" /> : <Check size={12} className="text-green" />}
            {active.isDirty ? "Unsaved Changes" : "Synchronized"}
          </span>
        </div>
        <div className="editor-status-right">
          <div className="language-selector">
            <button 
              className="lang-select-btn" 
              onClick={() => setShowLangMenu(!showLangMenu)}
            >
              <span>{active.language.toUpperCase()}</span>
              <ChevronDown size={12} />
            </button>
            
            {showLangMenu && (
              <div className="lang-menu animate-slide-up">
                {LANGUAGES.map(lang => (
                  <button 
                    key={lang} 
                    className={`lang-option ${active.language === lang ? "active" : ""}`}
                    onClick={() => {
                      setFileLanguage(active.path, lang);
                      setShowLangMenu(false);
                    }}
                  >
                    {lang.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </div>
          <span className="status-item">UTF-8</span>
          <span className="status-item">Ln {editorRef.current?.getPosition()?.lineNumber || 1}, Col {editorRef.current?.getPosition()?.column || 1}</span>
        </div>
      </div>
    </div>
  );
}
