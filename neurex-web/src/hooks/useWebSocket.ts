// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../lib/store";
import type { TaskNode } from "../lib/types";

import { API_BASE } from "../lib/config";
export function useWebSocket(conversationId: string) {
  const ws = useRef<WebSocket | null>(null);
  const token = useStore(s => s.token);
  const user = useStore(s => s.user);
  const userId = user?.username || "anonymous";
  
  const setWsStatus = useStore(s => s.setWsStatus);
  const upsertTask = useStore(s => s.upsertTask);
  const addMessage = useStore(s => s.addMessage);
  const appendToken = useStore(s => s.appendToken);
  const clearTasks = useStore(s => s.clearTasks);
  const setPresence = useStore(s => s.setPresence);

  const send = useCallback((payload: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const preferredModel = useStore.getState().preferredModel;
      ws.current.send(JSON.stringify({ ...payload, model: preferredModel }));
    }
  }, []);

  const sendPresence = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "presence_update", data }));
    }
  }, []);

  useEffect(() => {
    if (!conversationId || conversationId === "undefined" || !token) return;
    const state = useStore.getState();

    const wsBase = API_BASE.replace(/^http/, "ws");
    const url = `${wsBase}/ws/${conversationId}?token=${token}&user_id=${userId}`;
    const socket = new WebSocket(url);
    ws.current = socket;
    (window as any).neurexWS = { send, sendPresence };
    state.setWsStatus("connecting");

    socket.onopen = () => state.setWsStatus("connected");
    socket.onclose = () => state.setWsStatus("disconnected");
    socket.onerror = () => state.setWsStatus("disconnected");

    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const { event, data } = msg;
        const s = useStore.getState();

        switch (event) {
          case "presence_update":
            s.setPresence(data.filter((p: any) => p.user_id !== userId));
            break;
          case "task_created":
          case "task_updated":
            s.upsertTask(data as TaskNode);
            break;
          case "plan_ready":
            (data.tasks as TaskNode[]).forEach(s.upsertTask);
            break;
          case "token":
            s.appendToken(data as string);
            break;
          case "done":
            (data.tasks as TaskNode[]).forEach(s.upsertTask);
            break;
          case "terminal_output":
            window.dispatchEvent(new CustomEvent("terminal_write", { detail: data }));
            break;
          case "lock_update":
            s.setLocks({ ...s.locks, [data.path]: data });
            break;
          case "lock_release":
            const nextLocks = { ...s.locks };
            delete nextLocks[data.path];
            s.setLocks(nextLocks);
            break;
          case "error":
            s.addMessage({ role: "assistant", content: `❌ Error: ${data}` });
            break;
        }
      } catch {}
    };

    const heartbeat = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ping" }));
      }
    }, 15000);

    return () => {
      clearInterval(heartbeat);
      socket.close();
      state.clearTasks();
    };
  }, [conversationId, send, sendPresence, token, userId]);

  // Load history on mount or switch
  useEffect(() => {
    if (!conversationId || !token) return;
    fetch(`${API_BASE}/api/chat/${conversationId}`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then((r) => r.json())
      .then((data) => useStore.getState().setMessages(data))
      .catch(() => {});
  }, [conversationId, token]);

  // Load tasks on mount or switch
  useEffect(() => {
    if (!conversationId || !token) return;
    fetch(`${API_BASE}/api/tasks/?graph_id=${conversationId}`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then((r) => r.json())
      .then((data: TaskNode[]) => {
        data.forEach(upsertTask);
      })
      .catch(() => {});
  }, [conversationId, upsertTask, token]);

  return { send, sendPresence };
}
