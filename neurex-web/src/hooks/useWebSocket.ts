// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../lib/store";
import type { TaskNode } from "../lib/types";

const API_BASE = "http://127.0.0.1:8000";
const WS_TOKEN = "neurex-dev-token";
const userId = "User-" + Math.random().toString(36).substring(7);

export function useWebSocket(conversationId: string) {
  const ws = useRef<WebSocket | null>(null);
  const { setWsStatus, upsertTask, addMessage, appendToken, clearTasks, setPresence } = useStore();

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
    if (!conversationId || conversationId === "undefined") return;

    const url = `ws://127.0.0.1:8000/ws/${conversationId}?token=${WS_TOKEN}&user_id=${userId}`;
    const socket = new WebSocket(url);
    ws.current = socket;
    (window as any).neurexWS = { send, sendPresence };
    setWsStatus("connecting");

    socket.onopen = () => setWsStatus("connected");
    socket.onclose = () => setWsStatus("disconnected");
    socket.onerror = () => setWsStatus("disconnected");

    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const { event, data } = msg;

        switch (event) {
          case "presence_update":
            setPresence(data.filter((p: any) => p.user_id !== userId));
            break;
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
          case "terminal_output":
            window.dispatchEvent(new CustomEvent("terminal_write", { detail: data }));
            break;
          case "error":
            addMessage({ role: "assistant", content: `❌ Error: ${data}` });
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
      clearTasks();
    };
  }, [conversationId, setWsStatus, upsertTask, appendToken, addMessage, clearTasks, setPresence]);

  // Load history on mount or switch
  useEffect(() => {
    if (!conversationId) return;
    fetch(`${API_BASE}/api/chat/${conversationId}`)
      .then((r) => r.json())
      .then((data) => useStore.getState().setMessages(data))
      .catch(() => {});
  }, [conversationId]);

  // Load tasks on mount or switch
  useEffect(() => {
    // Load tasks for the current conversation
    fetch(`${API_BASE}/api/tasks/?graph_id=${conversationId}`)
      .then((r) => r.json())
      .then((data: TaskNode[]) => {
        data.forEach(upsertTask);
      })
      .catch(() => {});
  }, [conversationId, upsertTask]);

  return { send, sendPresence };
}
