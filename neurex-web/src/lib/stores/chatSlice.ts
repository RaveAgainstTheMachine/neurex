import { StoreSlice } from "./types";
import type { NeurexStore } from "../types";

export const createChatSlice: StoreSlice<NeurexStore> = (set, get) => ({
  // ── Chat ────────────────────────────────────────────────

    messages: [],
    activeConversationId: (() => {
      try {
        const folders = JSON.parse(localStorage.getItem("neurex_workspace_folders") || "[]");
        const root = folders.length > 0 ? folders[0] : "default";
        const map = JSON.parse(localStorage.getItem("neurex_workspace_chats") || "{}");
        if (map[root]) return map[root];
        
        // No chat for this workspace yet, generate a new one so we don't bleed chats across workspaces
        const newId = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
        map[root] = newId;
        localStorage.setItem("neurex_workspace_chats", JSON.stringify(map));
        return newId;
      } catch {}
      return typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
    })(),
    preferredModel: localStorage.getItem("neurex_model") || "qwen2.5-coder:14b",
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
        // Force array reference change so Zustand triggers React re-render
        s.messages = [...s.messages];
      } else {
        const id = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
        s.messages = [...s.messages, { id, role: "assistant", content: token, timestamp: new Date() }];
      }
    }),
    replaceTokens: (content) => set((s) => {
      const last = s.messages[s.messages.length - 1];
      if (last?.role === "assistant") {
        last.content = content;
        s.messages = [...s.messages];
      } else {
        const id = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2);
        s.messages = [...s.messages, { id, role: "assistant", content, timestamp: new Date() }];
      }
    }),
    setActiveConversation: (id) => set((s) => {
      s.activeConversationId = id;
      localStorage.setItem("neurex_conv_id", id);
      const root = s.workspaceFolders && s.workspaceFolders.length > 0 ? s.workspaceFolders[0] : "default";
      try {
        const map = JSON.parse(localStorage.getItem("neurex_workspace_chats") || "{}");
        map[root] = id;
        localStorage.setItem("neurex_workspace_chats", JSON.stringify(map));
      } catch {}
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
        localStorage.setItem("neurex_conv_id", id);
        const root = s.workspaceFolders && s.workspaceFolders.length > 0 ? s.workspaceFolders[0] : "default";
        try {
          const map = JSON.parse(localStorage.getItem("neurex_workspace_chats") || "{}");
          map[root] = id;
          localStorage.setItem("neurex_workspace_chats", JSON.stringify(map));
        } catch {}
      });
    },
    sendMessage: (content) => { get().addMessage({ role: "user", content }); get().send({ type: "message", content }); },

    } as unknown as NeurexStore);
