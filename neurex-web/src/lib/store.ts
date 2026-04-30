import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { subscribeWithSelector } from "zustand/middleware";
import toast from "react-hot-toast";
import { terminalRegistry } from "../components/Terminal/Terminal";
import type { NeurexStore, TaskNode, Diagnostic } from "./types";

import { API_BASE } from "./config";
import { api } from "./api";

export const useStore = create<NeurexStore>()(
  subscribeWithSelector(
    immer((set, get) => ({
    // ── App Lifecycle ────────────────────────────────────────────────
    isInitialized: false,
    isInitializing: false,
    lastLocalSave: 0,
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
      set((s) => { 
        s.token = null; 
        s.user = null; 
        s.isInitialized = false; 
        s.messages = [];
        s.tasks = {};
        s.infraEngines = [];
        s.infraMetrics = null;
        s.infraRegistry = [];
        s.infraSkills = [];
        s.infraPeers = [];
      });
      toast.error("Logged out");
    },
    refreshMe: async () => {
      if (!get().token) return;
      try {
        const user = await api.get<any>("/api/auth/me");
        localStorage.setItem("user", JSON.stringify(user));
        set((s) => { s.user = user; });
      } catch (err) {
        if (err instanceof Error && err.message.includes("401")) {
          get().logout();
        }
      }
    },

    // ── Infra ─────────────────────────────────────────────────────────
    infraEngines: [],
    infraMetrics: null,
    infraRegistry: [],
    infraSkills: [],
    infraPeers: [],
    hiveStats: { total_nodes: 0, memory_count: 0 },
    theme: (() => {
      const saved = localStorage.getItem("neurex_theme");
      const base = { 
        accent_color: "#9c6fff", 
        glow_color: "#9c6fff66",
        enable_glassmorphism: true,
        enable_animations: true,
        enable_swarm_glow: true,
        menu_mode: "horizontal",
        terminal_line_height: 1.2,
        terminal_font_size: 13,
        terminal_font_family: "'JetBrains Mono', 'Fira Code', monospace",
        terminal_cursor_style: "block"
      };
      try {
        return saved ? { ...base, ...JSON.parse(saved) } : base;
      } catch (e) { return base; }
    })(),
    settings: null,
    setSettings: (settings) => set((s) => { s.settings = settings; }),
    refreshSettings: async () => {
      if (!get().token) return;
      try {
        const data = await api.get<any>("/api/settings/");
        set((s) => { s.settings = data; });
        // Also sync theme
        get().setTheme({
          accent_color: data.accent_color,
          glow_color: data.glow_color,
          enable_glassmorphism: data.enable_glassmorphism,
          enable_animations: data.enable_animations,
          enable_swarm_glow: data.enable_swarm_glow,
          menu_mode: data.menu_mode || "horizontal",
          terminal_line_height: data.terminal_line_height || 1.2,
          terminal_font_size: data.terminal_font_size || 13,
          terminal_font_family: data.terminal_font_family || "'JetBrains Mono', 'Fira Code', monospace",
          terminal_cursor_style: data.terminal_cursor_style || "block"
        });
      } catch (err) {
        console.error("Settings sync failed", err);
      }
    },
    setTheme: (theme) => set((s) => { 
      s.theme = { ...s.theme, ...theme };
      localStorage.setItem("neurex_theme", JSON.stringify(s.theme));
      const root = document.documentElement;
      if (s.theme.accent_color) {
        root.style.setProperty('--accent-purple', s.theme.accent_color);
        root.style.setProperty('--purple-main', s.theme.accent_color);
        root.style.setProperty('--accent-primary', s.theme.accent_color);
      }
      if (s.theme.glow_color) {
        root.style.setProperty('--glow-purple', s.theme.glow_color);
        root.style.setProperty('--accent-primary-glow', s.theme.glow_color);
      }
    }),
    refreshTheme: async () => {
      // Logic moved into refreshSettings for efficiency
      await get().refreshSettings();
    },
    refreshInfra: async () => {
      if (!get().token) return;
      try {
        const [statusData, regData, skillsData, peersData, hiveData] = await Promise.all([
          api.get<any>("/api/infra/status"),
          api.get<any[]>("/api/infra/registry"),
          api.get<any[]>("/api/infra/skills"),
          api.get<any[]>("/api/infra/mesh/peers"),
          api.get<any>("/api/memory/stats")
        ]);

        set((s) => {
          s.infraEngines = Array.isArray(statusData.engines) ? statusData.engines : [];
          s.infraMetrics = statusData.metrics || null;
          s.infraRegistry = Array.isArray(regData) ? regData : [];
          s.infraSkills = Array.isArray(skillsData) ? skillsData : [];
          s.infraPeers = Array.isArray(peersData) ? peersData : [];
          s.hiveStats = hiveData;
        });
      } catch (e) {
        if (e instanceof Error && e.message.includes("401")) {
          get().logout();
        }
        console.error("Infra refresh failed", e);
      }
    },

    // ── Editor ────────────────────────────────────────────────────────
    openFiles: JSON.parse(localStorage.getItem("neurex_open_files") || "[]"),
    activeFile: localStorage.getItem("neurex_active_file"),
    editorPanes: [{ id: "pane-main", path: localStorage.getItem("neurex_active_file") }],
    setEditorPanes: (panes) => set((s) => { s.editorPanes = panes; }),
    splitEditor: (direction) => set((s) => {
      if (s.editorPanes.length < 2) {
        const id = `pane-${Math.random().toString(36).substring(7)}`;
        s.editorPanes.push({ id, path: s.activeFile });
      }
    }),
    closePane: (paneId) => set((s) => {
      if (s.editorPanes.length > 1) {
        s.editorPanes = s.editorPanes.filter(p => p.id !== paneId);
      }
    }),
    setPaneFile: (paneId, path) => set((s) => {
      const pane = s.editorPanes.find(p => p.id === paneId);
      if (pane) pane.path = path;
    }),
    cursorPosition: { line: 1, ch: 1 },
    setCursorPosition: (line, ch) => set((s) => { s.cursorPosition = { line, ch }; }),
    activeFileLanguage: "plaintext",
    setFileLanguage: (path, language) => set((s) => {
      const f = s.openFiles.find(x => x.path === path);
      if (f) f.language = language;
      if (s.activeFile === path) s.activeFileLanguage = language;
    }),

    // ── Speech ────────────────────────────────────────────────────────
    speechLang: localStorage.getItem("neurex_speech_lang") || "en-US",
    setSpeechLang: (lang) => {
      localStorage.setItem("neurex_speech_lang", lang);
      set((s) => { s.speechLang = lang; });
    },

    // ── File Tree ─────────────────────────────────────────────────────
    fileTree: [],
    diagnostics: [],
    workspaceDiagnostics: {} as Record<string, any[]>,
    setWorkspaceDiagnostics: (path: string, diagnostics: any[]) => {
      set((s) => {
        if (!diagnostics || diagnostics.length === 0) {
          delete s.workspaceDiagnostics[path];
        } else {
          s.workspaceDiagnostics[path] = diagnostics;
        }
        // Update the flat diagnostics list for the status bar/problems view
        s.diagnostics = Object.values(s.workspaceDiagnostics).flat() as Diagnostic[];
      });
    },
    setDiagnostics: (path: string, items: any[]) => set((s) => {
      const other = s.diagnostics.filter((d: any) => d.path !== path);
      s.diagnostics = [...other, ...items.map(i => ({ ...i, path }))];
    }),
    expandedFolders: new Set<string>(JSON.parse(localStorage.getItem("neurex_expanded_folders") || "[]")),
    collapsedFolders: new Set<string>(JSON.parse(localStorage.getItem("neurex_collapsed_folders") || "[]")),
    toggleFolder: (path, val) => set((s) => {
      const isExpanded = val !== undefined ? val : !s.expandedFolders.has(path);
      
      if (isExpanded) {
        s.expandedFolders.add(path);
        s.collapsedFolders.delete(path);
      } else {
        s.expandedFolders.delete(path);
        s.collapsedFolders.add(path);
      }
      
      localStorage.setItem("neurex_expanded_folders", JSON.stringify(Array.from(s.expandedFolders)));
      localStorage.setItem("neurex_collapsed_folders", JSON.stringify(Array.from(s.collapsedFolders)));
    }),
    collapseSignal: 0,
    collapseAllFolders: () => set((s) => { 
      s.collapseSignal += 1;
      s.expandedFolders.clear();
      s.collapsedFolders.clear();
      localStorage.setItem("neurex_expanded_folders", "[]");
      localStorage.setItem("neurex_collapsed_folders", "[]");
    }),
    gitBranch: "main",
    gitChanges: [],
    refreshGitStatus: async () => {
      try {
        const data = await api.get<any>("/api/git/status");
        set((s) => {
          s.gitBranch = data.branch;
          s.gitChanges = data.changes;
        });
      } catch (err) {}
    },
    setFileTree: (tree) => set((s) => { s.fileTree = tree; }),
    refreshFileTree: async () => {
      try {
        const data = await api.get<any>("/api/files/tree?depth=2");
        set((s) => { s.fileTree = Array.isArray(data) ? data : [data]; });
      } catch (err) {
        console.error("Failed to fetch file tree:", err);
      }
    },
    setWorkspace: async (path: string) => {
      try {
        await api.post("/api/files/workspace", { path });
        toast.success("Workspace Switched");
        set((s) => { 
          s.fileTree = []; 
          s.openFiles = []; 
          s.activeFile = null;
          s.editorPanes = [{ id: "pane-main", path: null }];
          s.expandedFolders = new Set();
          s.collapsedFolders = new Set();
        });
        localStorage.setItem("neurex_open_files", "[]");
        localStorage.setItem("neurex_active_file", "");
        localStorage.setItem("neurex_expanded_folders", "[]");
        localStorage.setItem("neurex_collapsed_folders", "[]");
        await get().refreshFileTree();
        await get().refreshGitStatus();
      } catch (err: any) {
        toast.error(err.message || "Switch failed");
      }
    },
    closeWorkspace: async () => {
      try {
        await api.post("/api/files/workspace", { path: "" });
        set((s) => {
          s.fileTree = [];
          s.openFiles = [];
          s.activeFile = null;
          s.editorPanes = [{ id: "pane-main", path: null }];
          s.expandedFolders = new Set();
          s.collapsedFolders = new Set();
        });
        localStorage.setItem("neurex_open_files", "[]");
        localStorage.setItem("neurex_active_file", "");
        localStorage.setItem("neurex_expanded_folders", "[]");
        localStorage.setItem("neurex_collapsed_folders", "[]");
        toast.success("Folder Closed");
      } catch (err: any) {
        toast.error("Failed to close folder");
      }
    },
    createFile: async (path: string) => {
      const tid = toast.loading(`Creating file: ${path}...`);
      try {
        await api.post("/api/files/save", { path, content: "" });
        toast.success(`File ${path} created`, { id: tid });
        get().refreshFileTree();
      } catch (err: any) {
        toast.error(err.message || "Creation failed", { id: tid });
      }
    },
    createFolder: async (path: string) => {
      const tid = toast.loading(`Creating folder: ${path}...`);
      try {
        await api.post(`/api/files/create-folder?path=${encodeURIComponent(path)}`);
        toast.success(`Folder ${path} created`, { id: tid });
        get().refreshFileTree();
      } catch (err: any) {
        toast.error(err.message || "Creation failed", { id: tid });
      }
    },
    fetchSubtree: async (path: string) => {
      try {
        const data = await api.get<any>(`/api/files/tree?path=${encodeURIComponent(path)}&depth=1`);
        set((s) => {
          const updateNode = (nodes: any[]) => {
            for (const node of nodes) {
              if (node.path === path) {
                node.children = data.children || data;
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
    send: (payload) => { /* placeholder set by App.tsx */ },
    sendMessage: (content) => {
      get().addMessage({ role: "user", content });
      get().send({ type: "message", content });
    },

    // ── Tasks ─────────────────────────────────────────────────────────
    tasks: {},
    upsertTask: (task: TaskNode) => set((s) => {
      s.tasks[task.id] = task;
    }),
    clearTasks: () => set((s) => { s.tasks = {}; }),

    // ── Editor Actions ───────────────────────────────────────────────
    openFile: (path, content, language, isPreview = false) => {
      if (!path) return;
      set((s) => {
        const existingIdx = s.openFiles.findIndex(f => f.path === path);
        if (existingIdx !== -1) {
          if (!isPreview) {
            s.openFiles[existingIdx].isPreview = false;
          }
          s.activeFile = path;
        } else {
          // If we are opening a preview, and there's already a preview file, replace it
          if (isPreview) {
            const previewIdx = s.openFiles.findIndex(f => f.isPreview);
            if (previewIdx !== -1) {
              s.openFiles[previewIdx] = { path, content, language, isDirty: false, isPreview: true };
            } else {
              s.openFiles.push({ path, content, language, isDirty: false, isPreview: true });
            }
          } else {
            s.openFiles.push({ path, content, language, isDirty: false, isPreview: false });
          }
          s.activeFile = path;
        }
        s.activeFileLanguage = language || "plaintext";
        localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
        localStorage.setItem("neurex_active_file", path);
      });
      setTimeout(() => (window as any).hideOverlays?.(), 0);
    },
    closeFile: (path) => set((s) => {
      const idx = s.openFiles.findIndex((f) => f.path === path);
      if (idx !== -1) {
        s.openFiles.splice(idx, 1);
      }
      
      if (s.activeFile === path) {
        s.activeFile = s.openFiles.length > 0 ? s.openFiles[s.openFiles.length - 1].path : null;
      }
      
      // Update panes
      s.editorPanes.forEach(p => {
        if (p.path === path) p.path = s.activeFile;
      });
      
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      localStorage.setItem("neurex_active_file", s.activeFile || "");
    }),
    closeOthers: (path) => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.path === path);
      s.activeFile = path;
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      localStorage.setItem("neurex_active_file", path);
    }),
    closeToRight: (path) => set((s) => {
      const idx = s.openFiles.findIndex(f => f.path === path);
      if (idx === -1) return;
      s.openFiles = s.openFiles.slice(0, idx + 1);
      if (!s.openFiles.find(f => f.path === s.activeFile)) {
        s.activeFile = path;
      }
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      localStorage.setItem("neurex_active_file", s.activeFile || "");
    }),
    closeSaved: () => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.isDirty);
      if (!s.openFiles.find(f => f.path === s.activeFile)) {
        s.activeFile = s.openFiles[0]?.path ?? null;
      }
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      localStorage.setItem("neurex_active_file", s.activeFile || "");
    }),
    closeAllFiles: () => set((s) => {
      s.openFiles = [];
      s.activeFile = null;
      localStorage.setItem("neurex_open_files", "[]");
      localStorage.setItem("neurex_active_file", "");
    }),
    setActiveFile: (path) => { 
      set((s) => { 
        s.activeFile = path; 
        const file = s.openFiles.find(f => f.path === path);
        s.activeFileLanguage = file?.language || "plaintext";
        localStorage.setItem("neurex_active_file", path || "");
      });
      setTimeout(() => (window as any).hideOverlays?.(), 0);
    },
    togglePin: (path) => set((s) => {
      const f = s.openFiles.find(x => x.path === path);
      if (f) {
        f.isPinned = !f.isPinned;
        localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      }
    }),
    setFileContent: (path, content) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { 
        f.content = content; 
        f.isDirty = true; 
        localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      }
    }),
    setDiff: (path, original, modified) => set((s) => {
      const ext = path.split('.').pop();
      const language = ext === 'ts' ? 'typescript' : ext === 'tsx' ? 'typescriptreact' : ext === 'js' ? 'javascript' : ext === 'py' ? 'python' : 'plaintext';
      
      const f = s.openFiles.find(f => f.path === path);
      if (f) {
        f.originalContent = original;
        f.content = modified;
        f.language = language;
      } else {
        s.openFiles.push({ path, content: modified, originalContent: original, language, isDirty: false });
      }
      s.activeFile = path;
    }),
    diffFile: async (path: string) => {
      try {
        const data = await api.get<any>(`/api/git/diff?path=${encodeURIComponent(path)}`);
        get().setDiff(path, data.original, data.modified);
      } catch (err: any) {
        toast.error(err.message || "Failed to load diff");
      }
    },
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
        await api.post("/api/files/save", { path, content: file.content });
        set((s) => {
          const f = s.openFiles.find((x) => x.path === path);
          if (f) f.isDirty = false;
          s.lastLocalSave = Date.now();
        });
        toast.success(`Saved ${path.split("/").pop()}`);
      } catch (err: any) {
        toast.error(err.message || `Failed to save ${path}`);
        console.error("Failed to save file:", err);
      }
    },
    renameFile: async (oldPath, newPath) => {
      try {
        await api.post("/api/files/rename", { old_path: oldPath, new_path: newPath });
        toast.success("File renamed");
        get().refreshFileTree();
        // Update open files if applicable
        set(s => {
          const f = s.openFiles.find(x => x.path === oldPath);
          if (f) f.path = newPath;
          if (s.activeFile === oldPath) s.activeFile = newPath;
        });
      } catch (err: any) {
        toast.error(err.message || "Rename failed");
      }
    },
    deleteFile: async (path) => {
      try {
        await api.delete(`/api/files/delete?path=${encodeURIComponent(path)}`);
        toast.success("File deleted");
        get().refreshFileTree();
        get().closeFile(path);
      } catch (err: any) {
        toast.error(err.message || "Delete failed");
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
    terminalSessions: JSON.parse(localStorage.getItem("neurex_terminal_sessions") || '[{"id":"default","name":"bash"}]'),
    activeTerminalId: localStorage.getItem("neurex_active_terminal") || "default",
    addTerminalSession: (name = "bash") => set((s) => {
      const id = Math.random().toString(36).substring(7);
      s.terminalSessions.push({ id, name });
      s.activeTerminalId = id;
      localStorage.setItem("neurex_terminal_sessions", JSON.stringify(s.terminalSessions));
      localStorage.setItem("neurex_active_terminal", id);
    }),
    closeTerminalSession: (id) => set((s) => {
      if (s.terminalSessions.length <= 1) return;
      s.terminalSessions = s.terminalSessions.filter(t => t.id !== id);
      if (s.activeTerminalId === id) {
        s.activeTerminalId = s.terminalSessions[s.terminalSessions.length - 1].id;
      }
      localStorage.setItem("neurex_terminal_sessions", JSON.stringify(s.terminalSessions));
      localStorage.setItem("neurex_active_terminal", s.activeTerminalId);
      
      const ws = (window as any).neurexWS;
      if (ws && ws.send) {
        ws.send({ type: "terminal_kill", sessionId: id });
      }
    }),
    setActiveTerminalId: (id) => set((s) => { 
      s.activeTerminalId = id;
      localStorage.setItem("neurex_active_terminal", id);
    }),
    clearActiveTerminal: () => {
      const id = get().activeTerminalId;
      const term = terminalRegistry.get(id);
      if (term) term.clear();
      const ws = (window as any).neurexWS;
      if (ws && ws.send) {
        ws.send({ type: "terminal_clear", sessionId: id });
        ws.send({ type: "terminal_input", sessionId: id, data: "\x0c" }); // Send Ctrl+L to clear backend buffer
      }
    },
    runActiveFile: () => {
      const file = get().activeFile;
      if (!file) {
        toast.error("No active file to run");
        return;
      }
      const id = get().activeTerminalId;
      const ws = (window as any).neurexWS;
      if (ws && ws.send) {
        let cmd = "";
        if (file.endsWith(".py")) cmd = `python ${file}\n`;
        else if (file.endsWith(".js")) cmd = `node ${file}\n`;
        else if (file.endsWith(".sh")) cmd = `bash ${file}\n`;
        
        if (cmd) {
          ws.send({ type: "terminal_input", sessionId: id, data: cmd });
          toast.success(`Running ${file.split("/").pop()}`);
        } else {
          toast.error("Language not supported for direct execution");
        }
      }
    },

    // ── Navigation ───────────────────────────────────────────────────
    pendingJump: null,
    setPendingJump: (path, line) => set((s) => {
      s.pendingJump = { path, line, timestamp: Date.now() };
    }),
    clearPendingJump: () => set((s) => { s.pendingJump = null; }),
    // ── Modals ───────────────────────────────────────────────────────
    modalOpen: false,
    setModalOpen: (val) => set((s) => { 
      s.modalOpen = typeof val === 'function' ? val(s.modalOpen) : val; 
    }),

    // ── UI State & Panel Management ───────────────────────────────────
    sidebarTab: localStorage.getItem("neurex_sidebar_tab") || "explorer",
    setSidebarTab: (tab) => set((s) => {
      s.sidebarTab = tab;
      s.showSettings = false;
      s.showHiveMind = false;
      localStorage.setItem("neurex_sidebar_tab", tab);
    }),
    sidebarOrder: JSON.parse(localStorage.getItem("neurex_sidebar_order") || '["explorer", "search", "git", "history", "agent", "infra", "skills", "system", "timeline"]'),
    setSidebarOrder: (order) => set((s) => {
      s.sidebarOrder = order;
      localStorage.setItem("neurex_sidebar_order", JSON.stringify(order));
    }),
    showAIPanel: localStorage.getItem("neurex_show_ai") !== "false",
    setShowAIPanel: (val) => set((s) => {
      const next = typeof val === 'function' ? val(s.showAIPanel) : val;
      s.showAIPanel = next;
      localStorage.setItem("neurex_show_ai", String(next));
    }),
    showSettings: false,
    setShowSettings: (val) => set((s) => { 
      const next = typeof val === 'function' ? val(s.showSettings) : val;
      s.showSettings = next; 
      if (next) s.showHiveMind = false;
    }),
    showHiveMind: false,
    setShowHiveMind: (val) => set((s) => { 
      const next = typeof val === 'function' ? val(s.showHiveMind) : val;
      s.showHiveMind = next; 
      if (next) s.showSettings = false;
    }),
  })))
);
