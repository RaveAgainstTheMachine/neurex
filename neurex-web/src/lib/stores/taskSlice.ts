import { StoreSlice } from "./types";
import { api } from "../api";
import toast from "react-hot-toast";
import type { NeurexStore, TaskNode } from "../types";

export const createTaskSlice: StoreSlice<NeurexStore> = (set, _get) => ({
  tasks: {},
  upsertTask: (task: TaskNode) => set((s) => { s.tasks[task.id] = task; }),
  clearTasks: () => set((s) => { s.tasks = {}; }),

  mutateGraph: async (graphId, payload) => {
    try {
      const res = await api.post<any>(`/api/tasks/${graphId}/mutate`, payload);
      if (res.error) {
        toast.error(res.error);
        return res;
      }
      // Reload all tasks in the graph to ensure everything is in sync
      const allTasks = await api.get<TaskNode[]>(`/api/tasks/?graph_id=${graphId}`);
      set((s) => {
        s.tasks = {};
        allTasks.forEach((t) => {
          s.tasks[t.id] = t;
        });
      });
      toast.success(`Task graph updated: ${payload.action}`);
      return res;
    } catch (err: any) {
      toast.error(err.message || "Failed to mutate task graph");
      throw err;
    }
  },

  toggleBreakpoint: async (taskId) => {
    try {
      const res = await api.post<any>(`/api/tasks/${taskId}/toggle_breakpoint`);
      if (res.error) {
        toast.error(res.error);
        return;
      }
      set((s) => {
        if (s.tasks[taskId]) {
          s.tasks[taskId].is_checkpoint = res.is_checkpoint;
        }
      });
      toast.success(res.is_checkpoint ? "Breakpoint enabled" : "Breakpoint disabled");
    } catch (err: any) {
      toast.error(err.message || "Failed to toggle breakpoint");
    }
  },

  approveTask: async (taskId) => {
    try {
      const res = await api.post<any>(`/api/tasks/${taskId}/approve`);
      if (res.error) {
        toast.error(res.error);
        return;
      }
      set((s) => {
        if (s.tasks[taskId]) {
          s.tasks[taskId].status = res.status;
          s.tasks[taskId].is_checkpoint = false;
        }
      });
      toast.success("Task approved and resumed");
    } catch (err: any) {
      toast.error(err.message || "Failed to approve task");
    }
  }
} as unknown as NeurexStore);
