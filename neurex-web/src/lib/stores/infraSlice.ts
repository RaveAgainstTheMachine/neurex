import { StoreSlice } from "./types";
import { api } from "../api";
import toast from "react-hot-toast";
import { terminalRegistry } from "../../components/Terminal/Terminal";
import type { NeurexStore, TaskNode, Diagnostic, FileNode } from "../types";

export const createInfraSlice: StoreSlice<NeurexStore> = (set, get) => ({
  // ── Infra ────────────────────────────────────────────────

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

    } as unknown as NeurexStore);
