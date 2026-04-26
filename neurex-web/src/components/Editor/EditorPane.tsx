import { useEffect, useRef } from "react";
import MonacoEditor, { Editor, DiffEditor } from "@monaco-editor/react";
import { useStore } from "../../lib/store";
import { Files } from "lucide-react";
import "./EditorPane.css";

export function EditorPane() {
  const { openFiles, activeFile, setFileContent, saveFile, presence } = useStore();
  const editorRef = useRef<any>(null);

  const active = openFiles.find((f) => f.path === activeFile) ?? openFiles[0];

  // Sync presence with monaco decorations
  useEffect(() => {
    if (editorRef.current?._presenceObserver) {
      editorRef.current._presenceObserver();
    }
  }, [presence]);

  if (!active) {
    return (
      <div className="editor-empty">
        <div className="editor-empty__inner">
          <Files size={48} />
          <p>Select a file to start coding</p>
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
              className={`editor-tab ${f.path === activeFile ? "active" : ""}`}
              onClick={() => useStore.getState().setActiveFile(f.path)}
            >
              <span className="editor-tab__name">{f.path.split("/").pop()}</span>
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
                colors: {
                  "editor.background": "#0d0d0f",
                },
              });
            }}
            options={{
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              renderSideBySide: true,
              scrollBeyondLastLine: false,
              readOnly: false,
            }}
          />
        ) : (
          <Editor
            height="100%"
            key={active.path}
            path={active.path}
            language={active.language}
            value={active.content}
            theme="neurex-dark"
            beforeMount={(monaco) => {
              monaco.editor.defineTheme("neurex-dark", {
                base: "vs-dark",
                inherit: true,
                rules: [],
                colors: {
                  "editor.background": "#0d0d0f",
                },
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
                    try {
                      if (p.active_file === active.path && p.cursor && typeof p.cursor.line === 'number' && p.user_id) {
                        newDecorations.push({
                          range: new monaco.Range(p.cursor.line, p.cursor.ch, p.cursor.line, p.cursor.ch + 1),
                          options: {
                            className: `remote-cursor remote-cursor--${(p.user_id || '').toLowerCase().includes('agent') ? 'agent' : 'user'}`,
                            hoverMessage: { value: p.user_id || 'Unknown' }
                          }
                        });
                      }
                    } catch (innerErr) {}
                  });
                  decorations = editor.deltaDecorations(decorations, newDecorations);
                } catch (err) {}
              };

              (editor as any)._presenceObserver = renderRemoteCursors;
              
              editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
                saveFile(active.path);
              });

              return () => {
                (editor as any)._presenceObserver = null;
                editorRef.current = null;
              };
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
            }}
          />
        )}
      </div>
    </div>
  );
}
