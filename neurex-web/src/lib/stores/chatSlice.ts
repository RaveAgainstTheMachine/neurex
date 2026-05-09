import { StoreSlice } from "./types";
import { api } from "../api";
import toast from "react-hot-toast";
import { terminalRegistry } from "../../components/Terminal/Terminal";
import type { NeurexStore, TaskNode, Diagnostic, FileNode } from "../types";

export const createChatSlice: StoreSlice<NeurexStore> = (set, get) => ({
  // ── Chat ────────────────────────────────────────────────

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

    } as unknown as NeurexStore);
