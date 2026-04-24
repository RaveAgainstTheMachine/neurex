// src/lib/store.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import type { NeurexStore, TaskNode } from "./types";

export const useStore = create<NeurexStore>()(
  immer((set) => ({
    // ── Chat ──────────────────────────────────────────────────────────
    messages: [],
    setMessages: (msgs) => set((s) => { s.messages = msgs; }),
    addMessage: (msg) => set((s) => {
      s.messages.push({ ...msg, id: crypto.randomUUID(), timestamp: new Date() });
    }),
    appendToken: (token) => set((s) => {
      const last = s.messages[s.messages.length - 1];
      if (last?.role === "assistant") {
        last.content += token;
      } else {
        s.messages.push({ id: crypto.randomUUID(), role: "assistant", content: token, timestamp: new Date() });
      }
    }),

    // ── Tasks ─────────────────────────────────────────────────────────
    tasks: {},
    upsertTask: (task: TaskNode) => set((s) => {
      s.tasks[task.id] = task;
    }),
    clearTasks: () => set((s) => { s.tasks = {}; }),

    // ── Editor ────────────────────────────────────────────────────────
    openFiles: [],
    activeFile: null,
    openFile: (path, content, language) => set((s) => {
      const exists = s.openFiles.some(f => f.path === path);
      if (!exists) {
        s.openFiles.push({ path, content, language, isDirty: false });
      }
      s.activeFile = path;
    }),
    closeFile: (path) => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.path !== path);
      if (s.activeFile === path) {
        s.activeFile = s.openFiles[s.openFiles.length - 1]?.path ?? null;
      }
    }),
    setActiveFile: (path) => set((s) => { s.activeFile = path; }),
    setFileContent: (path, content) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { f.content = content; f.isDirty = true; }
    }),

    // ── WS ────────────────────────────────────────────────────────────
    wsStatus: "connecting",
    setWsStatus: (status) => set((s) => { s.wsStatus = status; }),
  }))
);
