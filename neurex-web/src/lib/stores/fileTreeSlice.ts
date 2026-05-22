import { StoreSlice } from "./types";
import { api } from "../api";
import toast from "react-hot-toast";
import type { NeurexStore, Diagnostic, FileNode } from "../types";

export const createFiletreeSlice: StoreSlice<NeurexStore> = (set, get) => ({
  // ── File Tree ────────────────────────────────────────────────

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
      } catch { /* intentional */ }
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
      } catch {
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

    removeWorkspaceFolder: async (path: string) => {
      set((s) => {
        s.workspaceFolders = s.workspaceFolders.filter(p => p !== path);
        localStorage.setItem("neurex_workspace_folders", JSON.stringify(s.workspaceFolders));
      });
      await get().refreshFileTree();
    },

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
      } catch {
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
      } catch {
        toast.error("Failed to close folder");
      }
    },
    createFile: async (path: string, root_path?: string) => {
      const tid = toast.loading(`Creating file: ${path}...`);
      try {
        await api.post("/api/files/save", { path, content: "", root_path });
        toast.success(`File ${path} created`, { id: tid });
        get().refreshFileTree();
      } catch {
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
      } catch {
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
      } catch { console.error("Failed to fetch subtree:", err); }
    },

    } as unknown as NeurexStore);
