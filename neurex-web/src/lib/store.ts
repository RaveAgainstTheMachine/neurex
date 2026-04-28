// src/lib/store.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import toast from "react-hot-toast";
import type { NeurexStore, TaskNode } from "./types";

import { API_BASE } from "./config";

export const useStore = create<NeurexStore>()(
  immer((set, get) => ({
    // ── App Lifecycle ────────────────────────────────────────────────
    isInitialized: false,
    isInitializing: false,
    setIsInitialized: (val) => set((s) => { s.isInitialized = val; }),
    setIsInitializing: (val) => set((s) => { s.isInitializing = val; }),
    
    // ── Auth ──────────────────────────────────────────────────────────
    onboardingRequired: false,
    setOnboardingRequired: (val) => set((s) => { s.onboardingRequired = val; }),
    token: (() => {
      const t = localStorage.getItem("token");
      const ts = localStorage.getItem("token_timestamp");
      if (t && ts) {
        const age = Date.now() - parseInt(ts);
        if (age > 8 * 60 * 60 * 1000) { // 8 hours
          localStorage.removeItem("token");
          localStorage.removeItem("token_timestamp");
          localStorage.removeItem("user");
          return null;
        }
      }
      return t;
    })(),
    user: (() => {
      const u = localStorage.getItem("user");
      const t = localStorage.getItem("token");
      if (!t) {
        localStorage.removeItem("user");
        return null;
      }
      return JSON.parse(u || "null");
    })(),
    setAuth: (token, user) => {
      const now = Date.now().toString();
      localStorage.setItem("token", token);
      localStorage.setItem("token_timestamp", now);
      localStorage.setItem("user", JSON.stringify(user));
      set((s) => { 
        s.token = token; 
        s.user = user;
      });
      toast.success(`Welcome back, ${user.username}`);
    },
    logout: () => {
      localStorage.removeItem("token");
      localStorage.removeItem("token_timestamp");
      localStorage.removeItem("user");
      set((s) => { s.token = null; s.user = null; s.isInitialized = false; });
      toast.error("Logged out");
    },

    // ── Infra ─────────────────────────────────────────────────────────
    infraEngines: [],
    infraMetrics: null,
    infraRegistry: [],
    infraSkills: [],
    infraPeers: [],
    hiveStats: { total_nodes: 0, memory_count: 0 },
    theme: { 
      accent_color: "hsl(260, 90%, 70%)", 
      glow_color: "hsla(260, 90%, 70%, 0.4)",
      enable_glassmorphism: true,
      enable_animations: true,
      enable_swarm_glow: true
    },
    setTheme: (theme) => set((s) => { 
      s.theme = { ...s.theme, ...theme };
      const root = document.documentElement;
      if (theme.accent_color) root.style.setProperty('--accent-purple', theme.accent_color);
      if (theme.accent_color) root.style.setProperty('--purple-main', theme.accent_color);
      if (theme.glow_color) root.style.setProperty('--glow-purple', theme.glow_color);
    }),
    refreshTheme: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/settings/`);
        const data = await res.json();
        if (data.accent_color) {
          get().setTheme({
            accent_color: data.accent_color,
            glow_color: data.glow_color,
            enable_glassmorphism: data.enable_glassmorphism,
            enable_animations: data.enable_animations,
            enable_swarm_glow: data.enable_swarm_glow
          });
        }
      } catch (err) {
        console.error("Theme sync failed", err);
      }
    },
    refreshInfra: async () => {
      const token = get().token;
      if (!token) return;
      
      try {
        const statusProm = fetch(`${API_BASE}/api/infra/status`, { headers: { "Authorization": `Bearer ${token}` } }).then(r => r.json()).then(data => {
          set((s) => {
            s.infraEngines = Array.isArray(data.engines) ? data.engines : [];
            s.infraMetrics = data.metrics || null;
          });
        });
        
        const regProm = fetch(`${API_BASE}/api/infra/registry`, { headers: { "Authorization": `Bearer ${token}` } }).then(r => r.json()).then(data => {
          set((s) => { s.infraRegistry = Array.isArray(data) ? data : []; });
        });

        fetch(`${API_BASE}/api/infra/skills`, { headers: { "Authorization": `Bearer ${token}` } }).then(r => r.json()).then(data => {
          set((s) => { s.infraSkills = Array.isArray(data) ? data : []; });
        }).catch(e => console.warn("Skills fetch failed"));

        fetch(`${API_BASE}/api/infra/mesh/peers`, { headers: { "Authorization": `Bearer ${token}` } }).then(r => r.json()).then(data => {
          set((s) => { s.infraPeers = Array.isArray(data) ? data : []; });
        }).catch(e => console.warn("Peers fetch failed"));

        fetch(`${API_BASE}/api/memory/stats`).then(r => r.json()).then(data => {
          set((s) => { s.hiveStats = data; });
        }).catch(e => console.warn("Memory stats failed"));

        await Promise.all([statusProm, regProm]);
        get().refreshTheme();
      } catch (e) {
        console.error("Infra refresh failed", e);
      }
    },

    // ── Editor ────────────────────────────────────────────────────────
    openFiles: JSON.parse(localStorage.getItem("neurex_open_files") || "[]"),
    activeFile: localStorage.getItem("neurex_active_file"),
    cursorPosition: { line: 1, ch: 1 },
    setCursorPosition: (line, ch) => set((s) => { s.cursorPosition = { line, ch }; }),
    setFileLanguage: (path, language) => set((s) => {
      const f = s.openFiles.find(x => x.path === path);
      if (f) f.language = language;
    }),

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
        const token = get().token;
        if (!token) return;
        const r = await fetch(`${API_BASE}/api/files/tree?depth=2`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await r.json();
        set((s) => { s.fileTree = Array.isArray(data) ? data : [data]; });
      } catch (err) {
        console.error("Failed to fetch file tree:", err);
      }
    },
    fetchSubtree: async (path: string) => {
      try {
        const token = get().token;
        const r = await fetch(`${API_BASE}/api/files/tree?path=${encodeURIComponent(path)}&depth=1`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await r.json();
        set((s) => {
          const updateNode = (nodes: any[]) => {
            for (const node of nodes) {
              if (node.path === path) {
                node.children = data.children;
                return true;
              }
              if (node.children && updateNode(node.children)) return true;
            }
            return false;
          };
          updateNode(s.fileTree);
        });
      } catch (err) {
        console.error("Failed to fetch subtree:", err);
      }
    },
    // ── Chat ──────────────────────────────────────────────────────────
    messages: [],
    activeConversationId: (localStorage.getItem("neurex_conv_id") && localStorage.getItem("neurex_conv_id") !== "undefined") ? localStorage.getItem("neurex_conv_id")! : "default",
    preferredModel: localStorage.getItem("neurex_model") || "qwen2.5-coder:7b",
    conversations: [],
    setMessages: (msgs) => set((s) => { s.messages = msgs; }),
    addMessage: (msg) => set((s) => {
      const id = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
      s.messages.push({ ...msg, id, timestamp: new Date() });
    }),
    appendToken: (token) => set((s) => {
      const last = s.messages[s.messages.length - 1];
      if (last?.role === "assistant") {
        last.content += token;
      } else {
        const id = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
        s.messages.push({ id, role: "assistant", content: token, timestamp: new Date() });
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
      const id = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
      set((s) => {
        s.activeConversationId = id;
        s.messages = [];
        s.tasks = {};
      });
      localStorage.setItem("neurex_conv_id", id);
    },

    // ── Tasks ─────────────────────────────────────────────────────────
    tasks: {},
    upsertTask: (task: TaskNode) => set((s) => {
      s.tasks[task.id] = task;
    }),
    clearTasks: () => set((s) => { s.tasks = {}; }),

    // ── Editor Actions ───────────────────────────────────────────────
    openFile: (path, content, language) => {
      if (!path) return;
      set((s) => {
        const exists = s.openFiles.some(f => f.path === path);
        if (!exists) {
          s.openFiles.push({ path, content, language, isDirty: false });
        }
        s.activeFile = path;
        localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
        localStorage.setItem("neurex_active_file", path);
      });
      setTimeout(() => (window as any).hideOverlays?.(), 0);
    },
    closeFile: (path) => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.path !== path);
      if (s.activeFile === path) {
        s.activeFile = s.openFiles[s.openFiles.length - 1]?.path ?? null;
      }
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      localStorage.setItem("neurex_active_file", s.activeFile || "");
    }),
    setActiveFile: (path) => { 
      set((s) => { 
        s.activeFile = path; 
        localStorage.setItem("neurex_active_file", path || "");
      });
      setTimeout(() => (window as any).hideOverlays?.(), 0);
    },
    setFileContent: (path, content) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { 
        f.content = content; 
        f.isDirty = true; 
        localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      }
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
        const token = get().token;
        await fetch(`${API_BASE}/api/files/save`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
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
    locks: {},
    setLocks: (locks) => set((s) => { s.locks = locks; }),

    // ── Search ────────────────────────────────────────────────────────
    search: (() => {
      const saved = localStorage.getItem("neurex_search");
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch (e) {
          console.error("Failed to parse saved search", e);
        }
      }
      return {
        query: "",
        results: [],
        includeGlob: "",
        excludeGlob: "",
        caseSensitive: false,
        useRegex: false,
        wholeWord: false,
      };
    })(),
    setSearch: (patch) => set((s) => {
      s.search = { ...s.search, ...patch };
      localStorage.setItem("neurex_search", JSON.stringify(s.search));
    }),
    clearSearch: () => set((s) => {
      s.search = {
        query: "",
        results: [],
        includeGlob: "",
        excludeGlob: "",
        caseSensitive: false,
        useRegex: false,
        wholeWord: false,
      };
      localStorage.removeItem("neurex_search");
    }),

    // ── Terminal ──────────────────────────────────────────────────────
    terminalSessions: [{ id: "default", name: "bash" }],
    activeTerminalId: "default",
    addTerminalSession: (name = "bash") => set((s) => {
      const id = Math.random().toString(36).substring(7);
      s.terminalSessions.push({ id, name });
      s.activeTerminalId = id;
    }),
    closeTerminalSession: (id) => set((s) => {
      if (s.terminalSessions.length <= 1) return;
      s.terminalSessions = s.terminalSessions.filter(t => t.id !== id);
      if (s.activeTerminalId === id) {
        s.activeTerminalId = s.terminalSessions[s.terminalSessions.length - 1].id;
      }
    }),
    setActiveTerminalId: (id) => set((s) => { s.activeTerminalId = id; }),

    // ── Navigation ───────────────────────────────────────────────────
    pendingJump: null,
    setPendingJump: (path, line) => set((s) => {
      s.pendingJump = { path, line, timestamp: Date.now() };
    }),
    clearPendingJump: () => set((s) => { s.pendingJump = null; }),
    // ── Modals ───────────────────────────────────────────────────────
    modalOpen: false,
    setModalOpen: (val) => set((s) => { s.modalOpen = val; }),
  }))
);
