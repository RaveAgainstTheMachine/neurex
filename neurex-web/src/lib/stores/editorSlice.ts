import { StoreSlice } from "./types";
import { api } from "../api";
import toast from "react-hot-toast";
import { terminalRegistry } from "../../components/Terminal/Terminal";
import type { NeurexStore } from "../types";

export const createEditorSlice: StoreSlice<NeurexStore> = (set, get) => ({
  // ── Editor Actions ────────────────────────────────────────────────

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

    openFile: (_path, content, language, isPreview = false, root?: string) => {
      if (!path) return;
      set((s) => {
        const existingIdx = s.openFiles.findIndex(f => f.path === path && f.root === root);
        if (existingIdx !== -1) {
          if (!isPreview) s.openFiles[existingIdx].isPreview = false;
          s.activeFile = path;
        } else {
          if (isPreview) {
            const previewIdx = s.openFiles.findIndex(f => f.isPreview);
            if (previewIdx !== -1) s.openFiles[previewIdx] = { _path, content, language, isDirty: false, isPreview: true, root };
            else s.openFiles.push({ _path, content, language, isDirty: false, isPreview: true, root });
          } else {
            s.openFiles.push({ _path, content, language, isDirty: false, isPreview: false, root });
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
    splitEditor: (_direction) => set((s) => {
      const id = `pane-${Math.random().toString(36).substring(7)}`;
      s.editorPanes.push({ id, path: s.activeFile });
    }),
    closePane: (id) => set((s) => {
      if (s.editorPanes.length > 1) s.editorPanes = s.editorPanes.filter(p => p.id !== id);
    }),
    setFileContent: (_path, content) => set((s) => {
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
          _path, 
          content: file.content, 
          root_path: file.root 
        });
        set((s) => { 
          const f = s.openFiles.find(f => f.path === path);
          if (f) f.isDirty = false; 
        });
      } catch { toast.error("Failed to save file"); }
    },
    diffFile: async (path) => { /* placeholder */ },
    renameFile: async (oldPath, newPath, root_path) => {
      try {
        await api.post("/api/files/rename", { old_path: oldPath, new_path: newPath, root_path });
        toast.success("Renamed");
        get().refreshFileTree();
      } catch { toast.error("Rename failed"); }
    },
    deleteFile: async (path, root_path) => {
      try {
        const params = new URLSearchParams({ path });
        if (root_path) params.append("root_path", root_path);
        await api.delete(`/api/files/delete?${params.toString()}`);
        toast.success("Deleted");
        get().refreshFileTree();
      } catch { toast.error("Delete failed"); }
    },
    setPendingJump: (path, line, root?: string) => set((s) => { s.pendingJump = { path, line, timestamp: Date.now(), root }; }),
    clearPendingJump: () => set((s) => { s.pendingJump = null; }),

    swarmDiffs: {},
    setSwarmDiffs: (diffs) => set((s) => { s.swarmDiffs = diffs; }),
    acceptSwarmDiff: (path) => set((s) => {
      const diff = s.swarmDiffs[path];
      if (diff) {
        diff.status = "accepted";
        const f = s.openFiles.find(x => x.path === path);
        if (f) {
          delete f.originalContent;
          f.isDirty = true;
        }
      }
    }),
    discardSwarmDiff: (path) => set((s) => {
      const diff = s.swarmDiffs[path];
      if (diff) {
        diff.status = "discarded";
        const f = s.openFiles.find(x => x.path === path);
        if (f && f.originalContent !== undefined) {
          f.content = f.originalContent;
          delete f.originalContent;
          f.isDirty = false;
        }
      }
    }),
    clearSwarmDiffs: () => set((s) => { s.swarmDiffs = {}; }),

    debateMessages: [],
    addDebateMessage: (msg) => set((s) => {
      const idx = s.debateMessages.findIndex(x => x.id === msg.id);
      if (idx !== -1) {
        s.debateMessages[idx] = msg;
      } else {
        s.debateMessages.push(msg);
      }
    }),
    clearDebateMessages: () => set((s) => { s.debateMessages = []; }),

      // ── Terminal ────────────────────────────────────────────────

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

    } as unknown as NeurexStore);
