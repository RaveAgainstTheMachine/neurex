// src/components/Editor/EditorPane.tsx
import MonacoEditor from "@monaco-editor/react";
import { X } from "lucide-react";
import { useStore } from "../../lib/store";
import "./EditorPane.css";

export function EditorPane() {
  const { openFiles, activeFile, closeFile, setActiveFile, setFileContent } = useStore();

  if (openFiles.length === 0) {
    return (
      <div className="editor-empty">
        <div className="editor-empty__content">
          <div className="editor-empty__logo">⬡</div>
          <div className="editor-empty__title">Neurex IDE</div>
          <div className="editor-empty__subtitle">Open a file from the explorer, or ask the agent to build something.</div>
        </div>
      </div>
    );
  }

  const active = openFiles.find((f) => f.path === activeFile) ?? openFiles[0];

  return (
    <div className="editor-pane">
      <div className="editor-tabs">
        {openFiles.map((file) => {
          const name = file.path.split("/").pop() ?? file.path;
          return (
            <div
              key={file.path}
              className={`editor-tab ${file.path === activeFile ? "editor-tab--active" : ""}`}
              onClick={() => setActiveFile(file.path)}
            >
              <span className="editor-tab__name">{name}</span>
              {file.isDirty && <span className="editor-tab__dirty" />}
              <button
                className="editor-tab__close"
                onClick={(e) => { e.stopPropagation(); closeFile(file.path); }}
              >
                <X size={12} />
              </button>
            </div>
          );
        })}
      </div>

      <div className="editor-breadcrumb">
        {active.path.split("/").map((seg, i, arr) => (
          <span key={i}>
            <span className={i === arr.length - 1 ? "breadcrumb-active" : "breadcrumb-seg"}>{seg}</span>
            {i < arr.length - 1 && <span className="breadcrumb-sep"> › </span>}
          </span>
        ))}
      </div>

      <div className="editor-monaco">
        <MonacoEditor
          path={active.path}
          language={active.language}
          value={active.content}
          theme="neurex-dark"
          onChange={(val) => setFileContent(active.path, val ?? "")}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontLigatures: true,
            lineHeight: 22,
            minimap: { enabled: true, scale: 1 },
            scrollBeyondLastLine: false,
            renderLineHighlight: "line",
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            smoothScrolling: true,
            padding: { top: 12, bottom: 12 },
            tabSize: 2,
            wordWrap: "on",
          }}
          beforeMount={(monaco) => {
            monaco.editor.defineTheme("neurex-dark", {
              base: "vs-dark",
              inherit: true,
              rules: [
                { token: "comment", foreground: "55556a", fontStyle: "italic" },
                { token: "keyword", foreground: "9c6fff" },
                { token: "string", foreground: "3ddc84" },
                { token: "number", foreground: "ffc542" },
                { token: "type", foreground: "3ddcdc" },
              ],
              colors: {
                "editor.background": "#131316",
                "editor.foreground": "#e8e8f0",
                "editor.lineHighlightBackground": "#1a1a1f",
                "editor.selectionBackground": "#4c8eff33",
                "editorCursor.foreground": "#4c8eff",
                "editorLineNumber.foreground": "#2a2a35",
                "editorLineNumber.activeForeground": "#55556a",
              },
            });
          }}
        />
      </div>
    </div>
  );
}
