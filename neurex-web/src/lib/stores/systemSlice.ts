import { StoreSlice } from "./types";
import { api } from "../api";
import type { NeurexStore, Notification } from "../types";
import packageJson from "../../../package.json";

export const createSystemSlice: StoreSlice<NeurexStore> = (set, _get) => ({
  // ── App Lifecycle ────────────────────────────────────────────────

    isInitialized: false,
    isInitializing: false,
    lastLocalSave: 0,
    setIsInitialized: (val) => set((s) => { s.isInitialized = val; }),
    setIsInitializing: (val) => set((s) => { s.isInitializing = val; }),
    
      // ── Speech ────────────────────────────────────────────────

    speechLang: localStorage.getItem("neurex_speech_lang") || "en-US",
    setSpeechLang: (lang) => {
      localStorage.setItem("neurex_speech_lang", lang);
      set((s) => { s.speechLang = lang; });
    },

      // ── WS ────────────────────────────────────────────────

    wsStatus: "connecting",
    setWsStatus: (status) => set((s) => { s.wsStatus = status; }),
    presence: [],
    setPresence: (presence) => set((s) => { s.presence = presence; }),
    locks: {},
    setLocks: (locks) => set((s) => { s.locks = locks; }),
    autonomyLevel: localStorage.getItem("neurex_autonomy_level") || "limited",
    setAutonomyLevel: (level) => set((s) => {
      s.autonomyLevel = level;
      localStorage.setItem("neurex_autonomy_level", level);
      s.send({ type: "set_autonomy", level });
    }),

      // ── Search ────────────────────────────────────────────────

    search: (() => {
      const fallback = { query: "", results: [], includeGlob: "", excludeGlob: "", caseSensitive: false, useRegex: false, wholeWord: false };
      try {
        const val = localStorage.getItem("neurex_search");
        if (!val || val === "undefined") return fallback;
        const parsed = JSON.parse(val);
        return (parsed && typeof parsed === "object") ? { ...fallback, ...parsed } : fallback;
      } catch {
        return fallback;
      }
    })(),
    setSearch: (patch) => set((s) => { s.search = { ...s.search, ...patch }; localStorage.setItem("neurex_search", JSON.stringify(s.search)); }),
    clearSearch: () => set((s) => { s.search = { query: "", results: [], includeGlob: "", excludeGlob: "", caseSensitive: false, useRegex: false, wholeWord: false }; localStorage.removeItem("neurex_search"); }),

      // ── Modals & Hive ────────────────────────────────────────────────

    modalOpen: false,
    setModalOpen: (val) => set((s) => { s.modalOpen = typeof val === 'function' ? val(s.modalOpen) : val; }),
    hiveStats: { total_nodes: 0, memory_count: 0 },
    theme: (() => {
      const fallback = { accent_color: "#9c6fff", glow_color: "#9c6fff66", enable_glassmorphism: true, enable_animations: true, enable_swarm_glow: true, menu_mode: "horizontal", terminal_line_height: 1.4, terminal_font_size: 13, terminal_font_family: "'JetBrains Mono', 'Fira Code', monospace", terminal_cursor_style: "block" };
      try {
        const val = localStorage.getItem("neurex_theme");
        if (!val || val === "undefined") return fallback;
        const parsed = JSON.parse(val);
        return (parsed && typeof parsed === "object") ? { ...fallback, ...parsed } : fallback;
      } catch {
        return fallback;
      }
    })(),
    setTheme: (patch) => set((s) => { s.theme = { ...s.theme, ...patch }; localStorage.setItem("neurex_theme", JSON.stringify(s.theme)); }),
    refreshTheme: async () => {},
    settings: null,
    setSettings: (settings) => set((s) => { s.settings = settings; }),
    refreshSettings: async () => { 
      try { 
        const data = await api.get<any>("/api/settings/"); 
        set((s) => { 
          const fetched = data.settings || data;
          s.settings = fetched;
          // Sync theme settings from backend
          if (fetched.accent_color) {
            s.theme = {
              ...s.theme,
              accent_color: fetched.accent_color,
              glow_color: fetched.glow_color ?? s.theme.glow_color,
              enable_glassmorphism: fetched.enable_glassmorphism ?? s.theme.enable_glassmorphism,
              enable_animations: fetched.enable_animations ?? s.theme.enable_animations,
              enable_swarm_glow: fetched.enable_swarm_glow ?? s.theme.enable_swarm_glow,
              menu_mode: fetched.menu_mode ?? s.theme.menu_mode,
              terminal_line_height: fetched.terminal_line_height ?? s.theme.terminal_line_height,
              terminal_font_size: fetched.terminal_font_size ?? s.theme.terminal_font_size,
              terminal_font_family: fetched.terminal_font_family ?? s.theme.terminal_font_family,
              terminal_cursor_style: fetched.terminal_cursor_style ?? s.theme.terminal_cursor_style,
            };
            localStorage.setItem("neurex_theme", JSON.stringify(s.theme));
          }
        }); 
      } catch { /* intentional */ } 
    },
    refreshHiveStats: async () => { try { const stats = await api.get<any>("/api/memory/stats"); set((s) => { s.hiveStats = stats; }); } catch { /* intentional */ } },
    send: (payload) => { console.warn("[neurex] send() called before WebSocket connected", payload); },

      // ── UI Panels ────────────────────────────────────────────────

    sidebarTab: localStorage.getItem("neurex_sidebar_tab") || "explorer",
    setSidebarTab: (tab) => set((s) => { s.sidebarTab = tab; s.showSettings = false; localStorage.setItem("neurex_sidebar_tab", tab); }),
    sidebarOrder: (() => {
      const fallback = ["explorer", "search", "git", "history", "agent", "infra", "substrate", "skills", "system", "timeline"];
      try {
        const val = localStorage.getItem("neurex_sidebar_order");
        if (!val || val === "undefined") return fallback;
        const parsed = JSON.parse(val);
        return Array.isArray(parsed) ? parsed : fallback;
      } catch {
        return fallback;
      }
    })(),
    setSidebarOrder: (order) => set((s) => { s.sidebarOrder = order; localStorage.setItem("neurex_sidebar_order", JSON.stringify(order)); }),
    showAIPanel: localStorage.getItem("neurex_show_ai") !== "false",
    setShowAIPanel: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showAIPanel) : val; s.showAIPanel = next; localStorage.setItem("neurex_show_ai", String(next)); }),
    showSettings: false,
    setShowSettings: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showSettings) : val; s.showSettings = next; if (next) { s.showAbout = false; } }),
    showAbout: false,
    setShowAbout: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showAbout) : val; s.showAbout = next; if (next) { s.showSettings = false; } }),

    // Notifications Center
    notifications: [
      {
        id: "initial-sync",
        type: "success",
        title: "Substrate Active",
        description: `Secure Neurex v${packageJson.version} runtime is active.`,
        timestamp: new Date().toLocaleTimeString(),
        unread: true,
      }
    ],
    addNotification: (type, title, description) => set((s) => {
      s.notifications = [
        {
          id: Math.random().toString(36).substring(2, 9),
          type,
          title,
          description,
          timestamp: new Date().toLocaleTimeString(),
          unread: true,
        },
        ...s.notifications
      ];
    }),
    clearNotifications: () => set((s) => {
      s.notifications = [];
    }),
    markNotificationsAsRead: () => set((s) => {
      s.notifications = s.notifications.map(n => ({ ...n, unread: false }));
    }),
  } as unknown as NeurexStore);

