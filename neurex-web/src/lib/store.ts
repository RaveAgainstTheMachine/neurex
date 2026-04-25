// src/lib/store.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import toast from "react-hot-toast";
import type { NeurexStore, TaskNode } from "./types";

const API_BASE = "http://localhost:8000";

export const useStore = create<NeurexStore>()(
  immer((set, get) => ({
    // ── Speech ────────────────────────────────────────────────────────
    speechLang: localStorage.getItem("neurex_speech_lang") || "en-US",
    setSpeechLang: (lang) => {
      localStorage.setItem("neurex_speech_lang", lang);
      set((s) => { s.speechLang = lang; });
    },

    // ── File Tree ─────────────────────────────────────────────────────
    fileTree: [],
    setFileTree: (tree) => set((s) => { s.fileTree = tree; }),
    refreshFileTree: async () => {
      try {
        const r = await fetch(`${API_BASE}/api/files/tree`);
        const data = await r.json();
        set((s) => { s.fileTree = Array.isArray(data) ? data : [data]; });
      } catch (err) {
        console.error("Failed to fetch file tree:", err);
      }
    },

    // ── Chat ──────────────────────────────────────────────────────────
    messages: [],
    activeConversationId: localStorage.getItem("neurex_conv_id") || "default",
    preferredModel: localStorage.getItem("neurex_model") || "qwen2.5-coder:7b",
    conversations: [],
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
    setActiveConversation: (id) => set((s) => {
      s.activeConversationId = id;
      localStorage.setItem("neurex_conv_id", id);
      s.messages = [];
      s.tasks = {};
    }),
    setConversations: (convs) => set((s) => { s.conversations = convs; }),
    setPreferredModel: (model) => set((s) => {
      s.preferredModel = model;
      localStorage.setItem("neurex_model", model);
    }),
    newConversation: () => {
      const id = crypto.randomUUID();
      set((s) => {
        s.activeConversationId = id;
        localStorage.setItem("neurex_conv_id", id);
        s.messages = [];
        s.tasks = {};
      });
    },

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
      if (!path) return;
      const exists = s.openFiles.some(f => f.path === path);
      if (!exists) {
        s.openFiles.push({ path, content, language, isDirty: false });
      }
      s.activeFile = path;
      // Force editor visibility
      (window as any).hideOverlays?.();
    }),
    closeFile: (path) => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.path !== path);
      if (s.activeFile === path) {
        s.activeFile = s.openFiles[s.openFiles.length - 1]?.path ?? null;
      }
    }),
    setActiveFile: (path) => set((s) => { 
      s.activeFile = path; 
      (window as any).hideOverlays?.();
    }),
    setFileContent: (path, content) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { f.content = content; f.isDirty = true; }
    }),
    setDiff: (path, original, modified) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) {
        f.originalContent = original;
        f.content = modified;
      }
    }),
    acceptDiff: (path) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) {
        delete f.originalContent;
        f.isDirty = true;
        toast.success("Changes merged");
      }
    }),
    discardDiff: (path) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f && f.originalContent !== undefined) {
        f.content = f.originalContent;
        delete f.originalContent;
        toast.error("Changes discarded", { icon: "🗑️" });
      }
    }),
    saveFile: async (path) => {
      const file = get().openFiles.find((f) => f.path === path);
      if (!file) return;

      try {
        await fetch(`${API_BASE}/api/files/save`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path, content: file.content }),
        });
        set((s) => {
          const f = s.openFiles.find((x) => x.path === path);
          if (f) f.isDirty = false;
        });
        toast.success(`Saved ${path.split("/").pop()}`);
      } catch (err) {
        toast.error(`Failed to save ${path}`);
        console.error("Failed to save file:", err);
      }
    },

    // ── WS ────────────────────────────────────────────────────────────
    wsStatus: "connecting",
    setWsStatus: (status) => set((s) => { s.wsStatus = status; }),
    presence: [],
    setPresence: (presence) => set((s) => { s.presence = presence; }),
  }))
);
