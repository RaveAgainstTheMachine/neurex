import { StoreSlice } from "./types";
import { api } from "../api";
import type { NeurexStore } from "../types";

export const createAuthSlice: StoreSlice<NeurexStore> = (set, _get) => ({
  // ── Auth ────────────────────────────────────────────────

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
      } catch { /* intentional */ }
    },

    } as unknown as NeurexStore);
