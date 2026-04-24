// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../lib/store";
import type { TaskNode } from "../lib/types";

const API_BASE = "http://localhost:8000";
const WS_TOKEN = "neurex-dev-token";

export function useWebSocket(conversationId: string) {
  const ws = useRef<WebSocket | null>(null);
  const { setWsStatus, upsertTask, addMessage, appendToken, clearTasks } = useStore();

  const send = useCallback((payload: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(payload));
    }
  }, []);

  useEffect(() => {
    if (!conversationId || conversationId === "undefined") return;

    const url = `ws://localhost:8000/ws/${conversationId}?token=${WS_TOKEN}`;
    const socket = new WebSocket(url);
    ws.current = socket;
    setWsStatus("connecting");

    socket.onopen = () => setWsStatus("connected");
    socket.onclose = () => setWsStatus("disconnected");
    socket.onerror = () => setWsStatus("disconnected");

    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const { event, data } = msg;

        switch (event) {
          case "task_created":
          case "task_updated":
            upsertTask(data as TaskNode);
            break;
          case "plan_ready":
            (data.tasks as TaskNode[]).forEach(upsertTask);
            break;
          case "token":
            appendToken(data as string);
            break;
          case "done":
            (data.tasks as TaskNode[]).forEach(upsertTask);
            break;
          case "error":
            addMessage({ role: "assistant", content: `❌ Error: ${data}` });
            break;
        }
      } catch {}
    };

    return () => {
      socket.close();
    };
  }, [conversationId]);

  // Load history on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/chat/${conversationId}`)
      .then((r) => r.json())
      .then((data) => useStore.getState().setMessages(data))
      .catch(() => {});
  }, [conversationId]);

  // Load tasks on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/tasks/`)
      .then((r) => r.json())
      .then((data: TaskNode[]) => data.forEach(upsertTask))
      .catch(() => {});
  }, []);

  return { send };
}
