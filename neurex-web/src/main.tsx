// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import { enableMapSet } from "immer";
import App from "./App";
import "./index.css";

enableMapSet();

// Register PWA Service Worker
registerSW({ immediate: false });

// Configure Monaco Environment for local workers
(window as any).MonacoEnvironment = {
  getWorker: function (_: any, label: string) {
    if (label === 'json') {
      return new Worker(new URL('monaco-editor/esm/vs/language/json/json.worker?worker', import.meta.url));
    }
    if (label === 'css' || label === 'scss' || label === 'less') {
      return new Worker(new URL('monaco-editor/esm/vs/language/css/css.worker?worker', import.meta.url));
    }
    if (label === 'html' || label === 'handlebars' || label === 'razor') {
      return new Worker(new URL('monaco-editor/esm/vs/language/html/html.worker?worker', import.meta.url));
    }
    if (label === 'typescript' || label === 'javascript') {
      return new Worker(new URL('monaco-editor/esm/vs/language/typescript/ts.worker?worker', import.meta.url));
    }
    return new Worker(new URL('monaco-editor/esm/vs/editor/editor.worker?worker', import.meta.url));
  }
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
