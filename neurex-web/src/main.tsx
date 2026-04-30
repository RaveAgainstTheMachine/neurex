// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import { enableMapSet } from "immer";
import App from "./App";
import "./index.css";

// Import workers using Vite's ?worker syntax
import JsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import CssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import HtmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import TsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';

enableMapSet();

// Register PWA Service Worker
registerSW({ immediate: false });

// Configure Monaco Environment for local workers
(window as any).MonacoEnvironment = {
  getWorker: function (_: any, label: string) {
    if (label === 'json') {
      return new JsonWorker();
    }
    if (label === 'css' || label === 'scss' || label === 'less') {
      return new CssWorker();
    }
    if (label === 'html' || label === 'handlebars' || label === 'razor') {
      return new HtmlWorker();
    }
    if (label === 'typescript' || label === 'javascript') {
      return new TsWorker();
    }
    return new EditorWorker();
  }
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
