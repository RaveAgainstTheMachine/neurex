// src/lib/store.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { v4 as uuid } from "crypto";
import type { NeurexStore, ChatMessage, TaskNode } from "./types";

export const useStore = create<NeurexStore>()(
  immer((set) => ({
    // ── Chat ──────────────────────────────────────────────────────────────
    messages: [],

    addMessage: (msg) =>
      set((s) => {
        s.messages.push({
          ...msg,
          id: Math.random().toString(36).slice(2),
          timestamp: new Date(),
        });
      }),

    appendToken: (token) =>
      set((s) => {
        const last = s.messages[s.messages.length - 1];
        if (last && last.role === "assistant") {
          last.content += token;
        } else {
          s.messages.push({
            id: Math.random().toString(36).slice(2),
            role: "assistant",
            content: token,
            timestamp: new Date(),
          });
        }
      }),

    // ── Tasks ─────────────────────────────────────────────────────────────
    tasks: {},

    upsertTask: (task) =>
      set((s) => {
        s.tasks[task.id] = task;
      }),

    // ── Editor ────────────────────────────────────────────────────────────
    openFile: null,
    setOpenFile: (path) => set((s) => { s.openFile = path; }),

    fileContents: {},
    setFileContent: (path, content) =>
      set((s) => { s.fileContents[path] = content; }),

    // ── Scratchpad ────────────────────────────────────────────────────────
    scratchpad: "",
    setScratchpad: (text) => set((s) => { s.scratchpad = text; }),

    // ── WebSocket ─────────────────────────────────────────────────────────
    wsStatus: "disconnected",
    setWsStatus: (status) => set((s) => { s.wsStatus = status; }),
  }))
);
