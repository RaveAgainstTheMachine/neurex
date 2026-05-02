// src/lib/store.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { subscribeWithSelector } from "zustand/middleware";
import toast from "react-hot-toast";
import { terminalRegistry } from "../components/Terminal/Terminal";
import type { NeurexStore, TaskNode, Diagnostic, FileNode } from "./types";

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
        if (age > 8 * 60 * 60 * 1000) { 
          localStorage.removeItem("token");
          localStorage.removeItem("token_timestamp");
          return null;
        }
        return t;
      }
      return null;
    })(),
    user: JSON.parse(localStorage.getItem("user") || "null"),
    setAuth: (token, user) => set((s) => {
      s.token = token;
      s.user = user;
      localStorage.setItem("token", token);
      localStorage.setItem("token_timestamp", Date.now().toString());
      localStorage.setItem("user", JSON.stringify(user));
    }),
    logout: () => set((s) => {
      s.token = null;
      s.user = null;
      localStorage.removeItem("token");
      localStorage.removeItem("token_timestamp");
      localStorage.removeItem("user");
      window.location.reload();
    }),
    refreshMe: async () => {
      try {
        const data = await api.get<any>("/api/auth/me");
        set((s) => { s.user = data; });
        localStorage.setItem("user", JSON.stringify(data));
      } catch (err) {}
    },

    // ── Infra ─────────────────────────────────────────────────────────
    infraEngines: [],
    infraMetrics: null,
    infraRegistry: [],
    infraSkills: [],
    infraPeers: [],
    refreshInfra: async () => {
      const results = await Promise.allSettled([
        api.get<any>("/api/infra/engines"),
        api.get<any>("/api/infra/metrics"),
        api.get<any>("/api/infra/registry"),
        api.get<any>("/api/skills/"),
        api.get<any>("/api/infra/peers")
      ]);
      
      set((s) => {
        if (results[0].status === "fulfilled") s.infraEngines = results[0].value;
        if (results[1].status === "fulfilled") s.infraMetrics = results[1].value;
        if (results[2].status === "fulfilled") s.infraRegistry = results[2].value;
        if (results[3].status === "fulfilled") s.infraSkills = results[3].value;
        if (results[4].status === "fulfilled") s.infraPeers = results[4].value;
      });
    },

    // ── Speech ────────────────────────────────────────────────────────
    speechLang: localStorage.getItem("neurex_speech_lang") || "en-US",
    setSpeechLang: (lang) => {
      localStorage.setItem("neurex_speech_lang", lang);
      set((s) => { s.speechLang = lang; });
    },

    // ── File Tree ─────────────────────────────────────────────────────
    fileTree: [],
    diagnostics: [],
    workspaceDiagnostics: {} as Record<string, Diagnostic[]>,
    workspaceFolders: JSON.parse(localStorage.getItem("neurex_workspace_folders") || "[]"),
    collapseSignal: 0,
    
    updateDiagnostics: (path: string, items: Diagnostic[]) => set((s) => {
      if (!items || items.length === 0) delete s.workspaceDiagnostics[path];
      else s.workspaceDiagnostics[path] = items;
      s.diagnostics = Object.values(s.workspaceDiagnostics).flat() as Diagnostic[];
    }),

    expandedFolders: new Set<string>(JSON.parse(localStorage.getItem("neurex_expanded_folders") || "[]")),
    collapsedFolders: new Set<string>(JSON.parse(localStorage.getItem("neurex_collapsed_folders") || "[]")),
    
    toggleFolder: (path, val) => set((s) => {
      const isExpanded = val !== undefined ? val : !s.expandedFolders.has(path);
      if (isExpanded) { s.expandedFolders.add(path); s.collapsedFolders.delete(path); }
      else { s.expandedFolders.delete(path); s.collapsedFolders.add(path); }
      localStorage.setItem("neurex_expanded_folders", JSON.stringify(Array.from(s.expandedFolders)));
      localStorage.setItem("neurex_collapsed_folders", JSON.stringify(Array.from(s.collapsedFolders)));
    }),

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
      const { workspaceFolders } = get();
      try {
        if (workspaceFolders.length === 0) {
          set((s) => { s.fileTree = []; });
          return;
        }
        const trees = await Promise.all(workspaceFolders.map(path => 
          api.get<any>(`/api/files/tree?depth=2&root_path=${encodeURIComponent(path)}`)
        ));
        set((s) => {
          s.fileTree = trees.map((t, i) => ({
            name: workspaceFolders[i].split("/").pop() || workspaceFolders[i],
            type: "dir",
            path: workspaceFolders[i],
            children: Array.isArray(t) ? t : t.children || [],
            isRoot: true
          })) as FileNode[];
        });
      } catch (err) {
        console.error("Failed to sync file tree:", err);
      }
    },

    addWorkspaceFolder: async (path: string) => {
      set((s) => {
        if (!s.workspaceFolders.includes(path)) {
          s.workspaceFolders.push(path);
          localStorage.setItem("neurex_workspace_folders", JSON.stringify(s.workspaceFolders));
        }
      });
      await get().refreshFileTree();
    },

    removeWorkspaceFolder: (path: string) => set((s) => {
      s.workspaceFolders = s.workspaceFolders.filter(p => p !== path);
      localStorage.setItem("neurex_workspace_folders", JSON.stringify(s.workspaceFolders));
      get().refreshFileTree();
    }),

    setWorkspace: async (path: string) => {
      try {
        await api.post("/api/files/workspace", { path });
        toast.success("Workspace Switched");
        set((s) => { 
          s.fileTree = []; 
          s.openFiles = []; 
          s.activeFile = null;
          s.workspaceFolders = [path];
          s.editorPanes = [{ id: "pane-main", path: null }];
          s.expandedFolders = new Set();
          s.collapsedFolders = new Set();
        });
        localStorage.setItem("neurex_workspace_folders", JSON.stringify([path]));
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
          s.workspaceFolders = [];
          s.editorPanes = [{ id: "pane-main", path: null }];
          s.expandedFolders = new Set();
          s.collapsedFolders = new Set();
        });
        localStorage.setItem("neurex_workspace_folders", "[]");
        localStorage.setItem("neurex_open_files", "[]");
        localStorage.setItem("neurex_active_file", "");
        localStorage.setItem("neurex_expanded_folders", "[]");
        localStorage.setItem("neurex_collapsed_folders", "[]");
        toast.success("Folder Closed");
      } catch (err: any) {
        toast.error("Failed to close folder");
      }
    },
    createFile: async (path: string, root_path?: string) => {
      const tid = toast.loading(`Creating file: ${path}...`);
      try {
        await api.post("/api/files/save", { path, content: "", root_path });
        toast.success(`File ${path} created`, { id: tid });
        get().refreshFileTree();
      } catch (err: any) {
        toast.error(err.message || "Creation failed", { id: tid });
      }
    },
    createFolder: async (path: string, root_path?: string) => {
      const tid = toast.loading(`Creating folder: ${path}...`);
      try {
        const params = new URLSearchParams({ path });
        if (root_path) params.append("root_path", root_path);
        await api.post(`/api/files/create-folder?${params.toString()}`);
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
      } catch (err) { console.error("Failed to fetch subtree:", err); }
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
      set((s) => { s.activeConversationId = id; s.messages = []; s.tasks = {}; });
      localStorage.setItem("neurex_conv_id", id);
    },
    sendMessage: (content) => { get().addMessage({ role: "user", content }); get().send({ type: "message", content }); },

    // ── Tasks ─────────────────────────────────────────────────────────
    tasks: {},
    upsertTask: (task: TaskNode) => set((s) => { s.tasks[task.id] = task; }),
    clearTasks: () => set((s) => { s.tasks = {}; }),

    // ── Editor Actions ───────────────────────────────────────────────
    cursorPosition: { line: 1, ch: 1 },
    setCursorPosition: (line, ch) => set((s) => { s.cursorPosition = { line, ch }; }),
    activeFileLanguage: "plaintext",
    setFileLanguage: (path, language) => set((s) => {
      const f = s.openFiles.find(x => x.path === path);
      if (f) f.language = language;
      if (s.activeFile === path) s.activeFileLanguage = language;
    }),
    openFiles: JSON.parse(localStorage.getItem("neurex_open_files") || "[]"),
    activeFile: localStorage.getItem("neurex_active_file") || null,
    editorPanes: [{ id: "pane-main", path: null }],
    pendingJump: null,

    openFile: (path, content, language, isPreview = false, root?: string) => {
      if (!path) return;
      set((s) => {
        const existingIdx = s.openFiles.findIndex(f => f.path === path && f.root === root);
        if (existingIdx !== -1) {
          if (!isPreview) s.openFiles[existingIdx].isPreview = false;
          s.activeFile = path;
        } else {
          if (isPreview) {
            const previewIdx = s.openFiles.findIndex(f => f.isPreview);
            if (previewIdx !== -1) s.openFiles[previewIdx] = { path, content, language, isDirty: false, isPreview: true, root };
            else s.openFiles.push({ path, content, language, isDirty: false, isPreview: true, root });
          } else {
            s.openFiles.push({ path, content, language, isDirty: false, isPreview: false, root });
          }
          s.activeFile = path;
        }
        s.activeFileLanguage = language || "plaintext";
        
        // Phase 50.1: Sync with active pane
        const mainPane = s.editorPanes.find(p => p.id === "pane-main");
        if (mainPane) mainPane.path = path;
        
        localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
        localStorage.setItem("neurex_active_file", path);
      });
      setTimeout(() => (window as any).hideOverlays?.(), 0);
    },
    closeFile: (path) => set((s) => {
      const idx = s.openFiles.findIndex((f) => f.path === path);
      if (idx !== -1) s.openFiles.splice(idx, 1);
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
    }),
    closeOthers: (path) => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.path === path || f.isPinned);
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
    }),
    closeToRight: (path) => set((s) => {
      const idx = s.openFiles.findIndex(f => f.path === path);
      if (idx !== -1) s.openFiles = s.openFiles.slice(0, idx + 1).concat(s.openFiles.slice(idx + 1).filter(f => f.isPinned));
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
    }),
    closeSaved: () => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.isDirty || f.isPinned);
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
    }),
    closeAllFiles: () => set((s) => {
      s.openFiles = s.openFiles.filter(f => f.isPinned);
      s.activeFile = s.openFiles[0]?.path || null;
      localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles));
      localStorage.setItem("neurex_active_file", s.activeFile || "");
    }),
    togglePin: (path) => set((s) => {
      const f = s.openFiles.find(x => x.path === path);
      if (f) { f.isPinned = !f.isPinned; localStorage.setItem("neurex_open_files", JSON.stringify(s.openFiles)); }
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
    setPaneFile: (paneId, path) => set((s) => {
      const pane = s.editorPanes.find(p => p.id === paneId);
      if (pane) pane.path = path;
    }),
    setEditorPanes: (panes) => set((s) => { s.editorPanes = panes; }),
    splitEditor: (direction) => set((s) => {
      const id = `pane-${Math.random().toString(36).substring(7)}`;
      s.editorPanes.push({ id, path: s.activeFile });
    }),
    closePane: (id) => set((s) => {
      if (s.editorPanes.length > 1) s.editorPanes = s.editorPanes.filter(p => p.id !== id);
    }),
    setFileContent: (path, content) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { f.content = content; f.isDirty = true; }
    }),
    setDiff: (path, original, modified) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { f.originalContent = original; f.content = modified; }
    }),
    acceptDiff: (path) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { delete f.originalContent; f.isDirty = true; }
    }),
    discardDiff: (path) => set((s) => {
      const f = s.openFiles.find(f => f.path === path);
      if (f) { f.content = f.originalContent!; delete f.originalContent; f.isDirty = false; }
    }),
    saveFile: async (path) => {
      const file = get().openFiles.find(f => f.path === path);
      if (!file) return;
      try {
        await api.post("/api/files/save", { 
          path, 
          content: file.content, 
          root_path: file.root 
        });
        set((s) => { 
          const f = s.openFiles.find(f => f.path === path);
          if (f) f.isDirty = false; 
        });
      } catch (err) { toast.error("Failed to save file"); }
    },
    diffFile: async (path) => { /* placeholder */ },
    renameFile: async (oldPath, newPath, root_path) => {
      try {
        await api.post("/api/files/rename", { old_path: oldPath, new_path: newPath, root_path });
        toast.success("Renamed");
        get().refreshFileTree();
      } catch (err) { toast.error("Rename failed"); }
    },
    deleteFile: async (path, root_path) => {
      try {
        const params = new URLSearchParams({ path });
        if (root_path) params.append("root_path", root_path);
        await api.delete(`/api/files/delete?${params.toString()}`);
        toast.success("Deleted");
        get().refreshFileTree();
      } catch (err) { toast.error("Delete failed"); }
    },
    setPendingJump: (path, line, root?: string) => set((s) => { s.pendingJump = { path, line, timestamp: Date.now(), root }; }),
    clearPendingJump: () => set((s) => { s.pendingJump = null; }),

    // ── WS ────────────────────────────────────────────────────────────
    wsStatus: "connecting",
    setWsStatus: (status) => set((s) => { s.wsStatus = status; }),
    presence: [],
    setPresence: (presence) => set((s) => { s.presence = presence; }),
    locks: {},
    setLocks: (locks) => set((s) => { s.locks = locks; }),

    // ── Search ────────────────────────────────────────────────────────
    search: JSON.parse(localStorage.getItem("neurex_search") || '{"query":"","results":[],"includeGlob":"","excludeGlob":"","caseSensitive":false,"useRegex":false,"wholeWord":false}'),
    setSearch: (patch) => set((s) => { s.search = { ...s.search, ...patch }; localStorage.setItem("neurex_search", JSON.stringify(s.search)); }),
    clearSearch: () => set((s) => { s.search = { query: "", results: [], includeGlob: "", excludeGlob: "", caseSensitive: false, useRegex: false, wholeWord: false }; localStorage.removeItem("neurex_search"); }),

    // ── Terminal ──────────────────────────────────────────────────────
    terminalSessions: JSON.parse(localStorage.getItem("neurex_terminal_sessions") || '[{"id":"default","name":"bash"}]'),
    activeTerminalId: localStorage.getItem("neurex_active_terminal") || "default",
    addTerminalSession: (name, cwd) => set((s) => {
      const id = Math.random().toString(36).substring(7);
      s.terminalSessions.push({ id, name: name || "bash", cwd }); 
      s.activeTerminalId = id;
      localStorage.setItem("neurex_terminal_sessions", JSON.stringify(s.terminalSessions));
      localStorage.setItem("neurex_active_terminal", id);
    }),
    closeTerminalSession: (id) => set((s) => {
      if (s.terminalSessions.length <= 1) return;
      s.terminalSessions = s.terminalSessions.filter(t => t.id !== id);
      if (s.activeTerminalId === id) s.activeTerminalId = s.terminalSessions[s.terminalSessions.length - 1].id;
      localStorage.setItem("neurex_terminal_sessions", JSON.stringify(s.terminalSessions));
      localStorage.setItem("neurex_active_terminal", s.activeTerminalId);
      if (s.send) s.send({ type: "terminal_kill", sessionId: id });
    }),
    setActiveTerminalId: (id) => set((s) => { s.activeTerminalId = id; localStorage.setItem("neurex_active_terminal", id); }),
    clearActiveTerminal: () => {
      const id = get().activeTerminalId; const term = terminalRegistry.get(id); if (term) term.clear();
      const send = get().send;
      if (send) { 
        send({ type: "terminal_clear", sessionId: id }); 
        send({ type: "terminal_input", sessionId: id, data: "\x0c" }); 
      }
    },
    runActiveFile: () => {
      const file = get().activeFile; if (!file) { toast.error("No active file to run"); return; }
      const id = get().activeTerminalId; const ws = (window as any).neurexWS;
      if (ws?.send) {
        let cmd = ""; if (file.endsWith(".py")) cmd = `python ${file}\n`; else if (file.endsWith(".js")) cmd = `node ${file}\n`; else if (file.endsWith(".sh")) cmd = `bash ${file}\n`;
        if (cmd) { ws.send({ type: "terminal_input", sessionId: id, data: cmd }); toast.success(`Running ${file.split("/").pop()}`); }
        else toast.error("Language not supported for direct execution");
      }
    },

    // ── Modals & Hive ─────────────────────────────────────────────────
    modalOpen: false,
    setModalOpen: (val) => set((s) => { s.modalOpen = typeof val === 'function' ? val(s.modalOpen) : val; }),
    hiveStats: { total_nodes: 0, memory_count: 0 },
    theme: JSON.parse(localStorage.getItem("neurex_theme") || '{"accent_color":"#9c6fff","glow_color":"#9c6fff66","enable_glassmorphism":true,"enable_animations":true,"enable_swarm_glow":true,"menu_mode":"horizontal","terminal_line_height":1.4,"terminal_font_size":13,"terminal_font_family":"\'JetBrains Mono\', \'Fira Code\', monospace","terminal_cursor_style":"block"}'),
    setTheme: (patch) => set((s) => { s.theme = { ...s.theme, ...patch }; localStorage.setItem("neurex_theme", JSON.stringify(s.theme)); }),
    refreshTheme: async () => {},
    settings: null,
    setSettings: (settings) => set((s) => { s.settings = settings; }),
    refreshSettings: async () => { try { const data = await api.get<any>("/api/settings/"); set((s) => { s.settings = data.settings || data; }); } catch (err) {} },
    send: (payload) => { /* placeholder */ },

    // ── UI Panels ─────────────────────────────────────────────────────
    sidebarTab: localStorage.getItem("neurex_sidebar_tab") || "explorer",
    setSidebarTab: (tab) => set((s) => { s.sidebarTab = tab; s.showSettings = false; s.showHiveMind = false; localStorage.setItem("neurex_sidebar_tab", tab); }),
    sidebarOrder: JSON.parse(localStorage.getItem("neurex_sidebar_order") || '["explorer", "search", "git", "history", "agent", "infra", "substrate", "skills", "system", "timeline"]'),
    setSidebarOrder: (order) => set((s) => { s.sidebarOrder = order; localStorage.setItem("neurex_sidebar_order", JSON.stringify(order)); }),
    showAIPanel: localStorage.getItem("neurex_show_ai") !== "false",
    setShowAIPanel: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showAIPanel) : val; s.showAIPanel = next; localStorage.setItem("neurex_show_ai", String(next)); }),
    showSettings: false,
    setShowSettings: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showSettings) : val; s.showSettings = next; if (next) s.showHiveMind = false; }),
    showHiveMind: false,
    setShowHiveMind: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showHiveMind) : val; s.showHiveMind = next; if (next) s.showSettings = false; }),
  })))
);
