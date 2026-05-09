import { StoreSlice } from "./types";
import { api } from "../api";
import toast from "react-hot-toast";
import { terminalRegistry } from "../../components/Terminal/Terminal";
import type { NeurexStore, TaskNode, Diagnostic, FileNode } from "../types";

export const createTaskSlice: StoreSlice<NeurexStore> = (set, get) => ({
  // ── Tasks ────────────────────────────────────────────────

    tasks: {},
    upsertTask: (task: TaskNode) => set((s) => { s.tasks[task.id] = task; }),
    clearTasks: () => set((s) => { s.tasks = {}; }),

    } as unknown as NeurexStore);
