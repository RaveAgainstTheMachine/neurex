"use client";
// src/components/Editor/CodeEditor.tsx
import { useEffect, useRef } from "react";
import Editor, { useMonaco } from "@monaco-editor/react";
import { useStore } from "@/lib/store";

function getLanguage(path: string): string {
  const ext = path.split(".").pop() ?? "";
  const map: Record<string, string> = {
    ts: "typescript", tsx: "typescriptreact",
    js: "javascript", jsx: "javascriptreact",
    py: "python", rs: "rust", go: "go",
    json: "json", yaml: "yaml", yml: "yaml",
    md: "markdown", toml: "toml", sh: "shell",
    css: "css", html: "html",
  };
  return map[ext] ?? "plaintext";
}

export function CodeEditor() {
  const openFile      = useStore((s) => s.openFile);
  const fileContents  = useStore((s) => s.fileContents);
  const setFileContent = useStore((s) => s.setFileContent);
  const monaco        = useMonaco();

  const content  = openFile ? (fileContents[openFile] ?? "") : "";
  const language = openFile ? getLanguage(openFile) : "plaintext";

  useEffect(() => {
    if (!monaco) return;
    // Configure dark theme to match Neurex palette
    monaco.editor.defineTheme("neurex-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment",  foreground: "4a5568", fontStyle: "italic" },
        { token: "keyword",  foreground: "a855f7" },
        { token: "string",   foreground: "22c55e" },
        { token: "number",   foreground: "f59e0b" },
        { token: "function", foreground: "3b82f6" },
      ],
      colors: {
        "editor.background":           "#0d0f12",
        "editor.foreground":           "#e2e8f0",
        "editorLineNumber.foreground": "#4a5568",
        "editorCursor.foreground":     "#3b82f6",
        "editor.selectionBackground":  "#3b82f630",
        "editor.lineHighlightBackground": "#13161b",
        "editorGutter.background":     "#0d0f12",
        "scrollbarSlider.background":  "#252a35",
      },
    });
    monaco.editor.setTheme("neurex-dark");
  }, [monaco]);

  if (!openFile) {
    return (
      <div style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--text-muted)",
        gap: 8,
      }}>
        <span style={{ fontSize: 32 }}>⌨️</span>
        <span style={{ fontSize: 13 }}>Select a file to open</span>
        <span style={{ fontSize: 11 }}>or ask an agent to create one</span>
      </div>
    );
  }

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "4px 16px",
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        fontSize: 12,
        color: "var(--text-secondary)",
      }}>
        <span style={{ color: "var(--accent-blue)" }}>●</span>
        <span className="mono">{openFile}</span>
      </div>

      <Editor
        height="calc(100% - 29px)"
        language={language}
        value={content}
        theme="neurex-dark"
        onChange={(value) => {
          if (openFile && value !== undefined) {
            setFileContent(openFile, value);
          }
        }}
        options={{
          fontSize: 13,
          fontFamily: "'JetBrains Mono', monospace",
          fontLigatures: true,
          lineHeight: 22,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          renderLineHighlight: "line",
          wordWrap: "on",
          padding: { top: 12, bottom: 12 },
          smoothScrolling: true,
          cursorBlinking: "phase",
          cursorSmoothCaretAnimation: "on",
          bracketPairColorization: { enabled: true },
        }}
      />
    </div>
  );
}
