import { StoreSlice } from "./types";
import { api } from "../api";
import type { NeurexStore } from "../types";

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

      // ── Search ────────────────────────────────────────────────

    search: JSON.parse(localStorage.getItem("neurex_search") || '{"query":"","results":[],"includeGlob":"","excludeGlob":"","caseSensitive":false,"useRegex":false,"wholeWord":false}'),
    setSearch: (patch) => set((s) => { s.search = { ...s.search, ...patch }; localStorage.setItem("neurex_search", JSON.stringify(s.search)); }),
    clearSearch: () => set((s) => { s.search = { query: "", results: [], includeGlob: "", excludeGlob: "", caseSensitive: false, useRegex: false, wholeWord: false }; localStorage.removeItem("neurex_search"); }),

      // ── Modals & Hive ────────────────────────────────────────────────

    modalOpen: false,
    setModalOpen: (val) => set((s) => { s.modalOpen = typeof val === 'function' ? val(s.modalOpen) : val; }),
    hiveStats: { total_nodes: 0, memory_count: 0 },
    theme: JSON.parse(localStorage.getItem("neurex_theme") || '{"accent_color":"#9c6fff","glow_color":"#9c6fff66","enable_glassmorphism":true,"enable_animations":true,"enable_swarm_glow":true,"menu_mode":"horizontal","terminal_line_height":1.4,"terminal_font_size":13,"terminal_font_family":"\'JetBrains Mono\', \'Fira Code\', monospace","terminal_cursor_style":"block"}'),
    setTheme: (patch) => set((s) => { s.theme = { ...s.theme, ...patch }; localStorage.setItem("neurex_theme", JSON.stringify(s.theme)); }),
    refreshTheme: async () => {},
    settings: null,
    setSettings: (settings) => set((s) => { s.settings = settings; }),
    refreshSettings: async () => { try { const data = await api.get<any>("/api/settings/"); set((s) => { s.settings = data.settings || data; }); } catch { /* intentional */ } },
    send: (_payload) => { /* placeholder */ },

      // ── UI Panels ────────────────────────────────────────────────

    sidebarTab: localStorage.getItem("neurex_sidebar_tab") || "explorer",
    setSidebarTab: (tab) => set((s) => { s.sidebarTab = tab; s.showSettings = false; localStorage.setItem("neurex_sidebar_tab", tab); }),
    sidebarOrder: JSON.parse(localStorage.getItem("neurex_sidebar_order") || '["explorer", "search", "git", "history", "agent", "infra", "substrate", "skills", "system", "timeline"]'),
    setSidebarOrder: (order) => set((s) => { s.sidebarOrder = order; localStorage.setItem("neurex_sidebar_order", JSON.stringify(order)); }),
    showAIPanel: localStorage.getItem("neurex_show_ai") !== "false",
    setShowAIPanel: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showAIPanel) : val; s.showAIPanel = next; localStorage.setItem("neurex_show_ai", String(next)); }),
    showSettings: false,
    setShowSettings: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showSettings) : val; s.showSettings = next; if (next) { s.showAbout = false; } }),
    showAbout: false,
    setShowAbout: (val) => set((s) => { const next = typeof val === 'function' ? val(s.showAbout) : val; s.showAbout = next; if (next) { s.showSettings = false; } }),
  } as unknown as NeurexStore);
